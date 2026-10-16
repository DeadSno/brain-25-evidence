/* Кнопка «Поделиться» на страницах без собственной логики шеринга.

   Контекст. На atlas.html и calculator.html кнопка «скопировать ссылку» была
   всегда и живёт в их собственном <script>. На остальных 16 страницах её не
   было вовсе — при том, что ссылка на конкретную карточку (#sup=<id>) или на
   отфильтрованный набор и есть то, чем тут стоит делиться.

   Почему отдельный файл, а не строка в pwa.js: pwa.js подключается на всех
   страницах, но он про регистрацию service worker и бейдж офлайна. Смешивать
   с ним UI шеринга — значит потом искать этот код в неочевидном месте.
   Почему не инлайн в каждый футер: та же логика 16 раз — ровно то дублирование,
   которое мы только что убрали из футеров в батче E3.

   Подключается и из корня (./share.js), и со страниц /sup/*.html (../share.js).

   Поведение: если браузер умеет navigator.share (обычно мобильные) — отдаём
   системный лист; если нет или пользователь отказался — копируем location.href
   в буфер и честно сообщаем об этом текстом на кнопке. Никаких «успешно»,
   которые ничего не скопировали. */
(function () {
  /* 13A1 (I18N-P2-01): пользовательские строки — в словаре; см. docs/script.js. */
  var I18N = { ru: {
    "share.label": "🔗 Поделиться",
    "share.copied": "✓ Скопировано",
    "share.fail": "Не удалось скопировать"
  } };
  function t(key, params) {
    var lang = (document.documentElement.lang || 'ru').slice(0, 2);
    var dict = I18N[lang] || I18N.ru;
    var s = dict[key] != null ? dict[key] : (I18N.ru[key] != null ? I18N.ru[key] : key);
    if (params) s = s.replace(/\{(\w+)\}/g, function (m, k) { return (k in params) ? params[k] : m; });
    return s;
  }
  var LABEL = t("share.label");
  var OK = t("share.copied");
  var FAIL = t("share.fail");

  function mark(btn, text, isError) {
    var old = btn.textContent;
    btn.textContent = text;
    /* aria-live на самой кнопке: сообщение считывается скринридером, но
       не перехватывает фокус и не мешает клику. */
    btn.setAttribute('aria-live', 'polite');
    if (isError) btn.classList.add('is-share-error');
    window.setTimeout(function () {
      btn.textContent = old || LABEL;
      if (isError) btn.classList.remove('is-share-error');
    }, 2200);
  }

  function copyFallback(btn, url) {
    /* navigator.clipboard требует https и бывает недоступен. Поэтому
       сперва пробуем его, а при отказе — старый execCommand, который
       работает на http://localhost и в старых браузерах. */
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () {
        mark(btn, OK, false);
      }, function () {
        /* Ровно одна попытка legacy-копирования: звать legacyCopy дважды
           означало бы скопировать один и тот же URL дважды. */
        var ok = legacyCopy(btn, url);
        mark(btn, ok ? OK : FAIL, !ok);
      });
      return;
    }
    var done = legacyCopy(btn, url);
    mark(btn, done ? OK : FAIL, !done);
  }

  /* Вызывать только из catch/fallback-ветки: здесь true означает «готово». */
  function legacyCopy(btn, url) {
    try {
      var ta = document.createElement('textarea');
      ta.value = url;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch (e) {
      return false;
    }
  }

  function wire(btn) {
    var url = location.href;
    btn.addEventListener('click', function () {
      if (navigator.share) {
        navigator.share({ title: document.title, url: url })
          .then(function () { /* системный лист закрыт, ничего не сообщаем */ })
          .catch(function (err) {
            /* Пользователь закрыл лист — это не ошибка, сообщать не о чем.
               Остальное (AbortError не приходит, но прочие — да) → копируем. */
            if (err && err.name === 'AbortError') return;
            copyFallback(btn, url);
          });
        return;
      }
      copyFallback(btn, url);
    });
  }

  function init() {
    var btns = document.querySelectorAll('.share-page');
    for (var i = 0; i < btns.length; i++) wire(btns[i]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();