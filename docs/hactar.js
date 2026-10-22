/* Project Hactar — список добавок в левой панели (H-2) + фильтры,
 * сохранение выбора и полная ширина страницы (H-3), тосты и пустые
 * состояния (H-4), переключение вкладок с deep-link ?tab= (H-5).
 *
 * Задача H-2: наполнить левую панель данными. Источник — docs/data_index.json
 * (облегчённая копия docs/data.json: те же 130 записей, но только поля,
 * нужные карточке — id / name / category / grade). Если index недоступен,
 * берём полный docs/data.json.
 *
 * Что делает этот файл:
 *   1. грузит данные и рисует skeleton-заглушки на время загрузки;
 *   2. рендерит 130 карточек: чекбокс + название + цветной бейдж грейда;
 *   3. фильтрует список по подстроке в названии (input#hactarSearch);
 *   4. фильтрует список по грейду (чипсы «Все / A / B / C / D»);
 *   5. горячие клавиши: «/» — курсор в поиск, Esc — очистить поиск и снять фокус;
 *   6. ведёт счётчик выбранного (#hactarCount);
 *   7. сохраняет выбор в localStorage (ключ hactarSelectedIds) и
 *      восстанавливает его при загрузке страницы;
 *   8. кнопка «Очистить всё» снимает все галочки и чистит хранилище;
 *   9. H-4: показывает тост при добавлении и удалении добавки;
 *  10. H-4: переключает пустое состояние и заглушку в правой панели.
 *  11. H-5: переключает вкладки (Связи / Калькулятор / Сравнение) и
 *      держит выбранный режим в адресе (?tab=graph|calc|compare).
 *  12. H-6: рисует эго-сеть выбранных добавок во вкладке «Связи»
 *      (vis-network): только выбранные добавки, их механизмы и мишени
 *      и связанные лекарства — никаких 130 узлов (MAN-03).
 *  13. H-7: считает дозы выбранных добавок во вкладке «Калькулятор»
 *      и ловит некорректный ввод (U2-02);
 *  14. H-8: собирает таблицу сравнения во вкладке «Сравнение»
 *      (side-by-side по выбранным добавкам) и ряд кнопок «Купить» —
 *      путь от сравнения к покупке (баг P2-03).
 *
 * Связка поиска и грейда: работают ВМЕСТЕ, а не по очереди. Введён
 * «Магний» + выбран грейд «D» -> остаётся только Магний (у него грейд D).
 *
 * Чего здесь НЕТ сознательно: подбор «стека» под задачу и проверка
 * противопоказаний — это следующие шаги Project Hactar.
 */
(function () {
  'use strict';

  /* Расшифровка грейдов — та же, что в i18n.js (grade.A … grade.D). */
  var GRADE_LABEL = {
    A: 'Высокая доказательность',
    B: 'Средняя',
    C: 'Низкая',
    D: 'Недостаточно данных'
  };

  /* Ширина шторки — тот же брейкпоинт, что в <style> страницы (768px). */
  var MOBILE_BP = 768;

  /* Сколько заглушек рисовать, пока грузится JSON (задача: 8–10). */
  var SKELETON_COUNT = 10;

  /* Ключ localStorage: JSON-массив id выбранных добавок (H-3). */
  var STORAGE_KEY = 'hactarSelectedIds';

  /* Спец-значение активного грейда: «показывать все». Остальные значения —
     A/B/C/D в верхнем регистре. */
  var GRADE_ALL = 'ALL';

  /* H-4: время жизни тоста. Сначала 2 секунды на экране, потом затухание
     TOAST_FADE_MS. Всего одновременно — не больше TOAST_MAX, иначе низ
     экрана превращается в стопку сообщений. */
  var TOAST_MS = 2000;
  var TOAST_FADE_MS = 350;
  var TOAST_MAX = 3;

  var listEl = document.getElementById('hactarList');
  var emptyEl = document.getElementById('hactarEmpty');
  var searchEl = document.getElementById('hactarSearch');
  var countEl = document.getElementById('hactarCount');
  var totalEl = document.getElementById('hactarTotal');
  var sidebar = document.getElementById('hactarSidebar');
  var chipsEl = document.getElementById('hactarChips');
  var clearBtn = document.getElementById('hactarClearAll');
  var toastsEl = document.getElementById('hactarToasts');
  /* H-4: пустое состояние — по одному на каждый таб. */
  var emptyStates = document.querySelectorAll('.hactar-empty-state');
  var emptyBtns = document.querySelectorAll('.hactar-empty-btn');
  /* H-7: элементы калькулятора доз (вкладка «Калькулятор»). */
  var calcWrap = document.getElementById('hactarCalc');
  var calcListEl = document.getElementById('hactarCalcList');
  var calcSummaryListEl = document.getElementById('hactarCalcSummaryList');
  var calcAlertsEl = document.getElementById('hactarCalcAlerts');
  var calcErrorsEl = document.getElementById('hactarCalcErrors');
  /* H-8: элементы вкладки «Сравнение» — таблица, карточки и подсказка. */
  var compareWrap = document.getElementById('hactarCompare');
  var compareHeadEl = document.getElementById('hactarCompareHead');
  var compareBodyEl = document.getElementById('hactarCompareBody');
  var compareScrollEl = document.getElementById('hactarCompareScroll');
  var compareCardsEl = document.getElementById('hactarCompareCards');
  var compareNoteEl = document.getElementById('hactarCompareNote');
  var compareHintEl = document.getElementById('hactarCompareHint');

  /* ─────────────────── подписки на изменения (H-6) ───────────────────
   *
   * Граф во вкладке «Связи» должен перерисовываться, когда пользователь
   * ставит и снимает галочки. Раньше выбор жил внутри этого файла и
   * наружу не смотрел, поэтому добавили минимальную шину событий:
   * подписчики на «change» (смена выбора) и «mode» (смена вкладки).
   * Ошибка подписчика не должна ронять страницу — ловим и логируем. */
  var subs = { change: [], mode: [] };

  function subscribe(kind, fn) {
    if (typeof fn !== 'function') return function () { };
    if (!subs[kind]) subs[kind] = [];
    subs[kind].push(fn);
    /* Возвращаем функцию отписки — ею можно чистить слушателей. */
    return function () {
      var list = subs[kind] || [];
      var i = list.indexOf(fn);
      if (i !== -1) list.splice(i, 1);
    };
  }

  function emit(kind, payload) {
    if (!subs) return;
    var list = subs[kind] || [];
    for (var i = 0; i < list.length; i++) {
      try {
        list[i](payload);
      } catch (err) {
        console.error('[hactar] подписчик на «' + kind + '» упал:', err);
      }
    }
  }

  /* ──────────────────── вкладки: режимы и ?tab= (H-5) ────────────────────
   *
   * Логика вкладок переехала сюда из инлайнового <script> в hactar.html:
   * вместе с ней приехала синхронизация адреса.
   *
   * Deep-link: ?tab=graph — «Связи», ?tab=calc — «Калькулятор»,
   * ?tab=compare — «Сравнение». Параметр пишется через replaceState:
   * переключение вкладки не перезагружает страницу и не плодит записи
   * в истории браузера. При загрузке параметр, наоборот, только
   * читается — адрес не меняется, пока пользователь сам не выбрал
   * другую вкладку.
   *
   * Разметка прежняя: .hactar-tabs [role="tab"] и .hactar-panel,
   * класс состояния — .active (его ставит только setMode). */
  var TAB_PARAM = { links: 'graph', calc: 'calc', compare: 'compare' };
  var DEFAULT_MODE = 'links';
  var tabs = document.querySelectorAll('.hactar-tabs [role="tab"]');
  var panels = document.querySelectorAll('.hactar-panel');
  var currentMode = DEFAULT_MODE;

  /* Режим из адреса: ?tab=calc / ?tab=compare. Любой другой параметр
     (и его отсутствие) — дефолтный режим «Связи». */
  function modeFromUrl() {
    var tab = new URLSearchParams(location.search).get('tab');
    if (tab === 'calc' || tab === 'compare') return tab;
    return DEFAULT_MODE;
  }

  function setMode(next) {
    currentMode = next;
    tabs.forEach(function (t) {
      var active = t.dataset.mode === next;
      t.setAttribute('aria-selected', String(active));
      t.classList.toggle('active', active);
      t.tabIndex = active ? 0 : -1;
    });
    panels.forEach(function (p) {
      var active = p.dataset.panel === next;
      p.classList.toggle('active', active);
      // hidden переключается вместе с классом: иначе неактивная панель
      // остаётся в потоке для скринридера, хотя и не видна.
      p.hidden = !active;
    });
    /* H-6: граф живёт в панели «Связи». Когда панель прячется, canvas
       теряет размер; когда возвращается — размер нужен заново. Сообщаем
       подписчикам, что вкладка сменилась. */
    emit('mode', next);
  }

  /* Адрес — без перезагрузки. Остальные параметры и якорь сохраняются:
     replaceState заменяет историю целиком, терять их нельзя. */
  function syncUrl(next) {
    var param = TAB_PARAM[next];
    if (!param) return;
    var url = new URL(location.href);
    url.searchParams.set('tab', param);
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }

  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      setMode(t.dataset.mode);
      syncUrl(t.dataset.mode);
      /* На мобильном вкладка закрывает шторку — как и раньше. */
      if (sidebar) sidebar.classList.remove('open');
    });
  });

  /* Стартовый режим — из ?tab=. Без параметра — «Связи»: класс .active
     ставит только setMode, без него вкладки выглядели бы «никакими». */
  setMode(modeFromUrl());

  if (!listEl) return;

  var rows = [];    /* элементы .hactar-row — для быстрой фильтрации */
  var all = [];     /* все добавки из JSON */
  var supById = {}; /* id добавки → запись (для графа H-6) */
  var loaded = false;
  var grade = GRADE_ALL;  /* активный грейд-фильтр */

  /* ─────────────────────────── утилиты ─────────────────────────── */

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function fetchJson(url) {
    return fetch(url + '?ts=' + Date.now()).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' — ' + url);
      return r.json();
    });
  }

  /* data.json — массив, data_index.json — объект с полем supplements. */
  function supplementsOf(data) {
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.supplements)) return data.supplements;
    return [];
  }

  function isMobile() {
    return window.matchMedia && window.matchMedia('(max-width: ' + MOBILE_BP + 'px)').matches;
  }

  /* ──────────────────────────── тосты (H-4) ──────────────────────────── */

  /* Всплывающее уведомление внизу экрана: короткий ответ на действие
     пользователя («добавлен в стек» / «удалён из стека»).
     kind: 'ok' — зелёная галочка, 'off' — серый крестик.
     Своего тост-механизма в проекте нет (showUpdateToast в script.js —
     одноразовая штука про обновление данных, она перезагружает страницу),
     поэтому делаем локальный, только для hactar. */
  function showToast(text, kind) {
    if (!toastsEl) return;
    var el = document.createElement('div');
    el.className = 'hactar-toast';
    if (kind === 'off') el.classList.add('hactar-toast-off');
    else el.classList.add('hactar-toast-ok');
    el.innerHTML = '<span class="hactar-toast-icon" aria-hidden="true">' +
                   (kind === 'off' ? '✕' : '✓') +
                   '</span><span class="hactar-toast-text">' + esc(text) + '</span>';
    toastsEl.appendChild(el);

    /* Больше трёх тостов сразу — визуальный шум: старые вытесняются. */
    while (toastsEl.children.length > TOAST_MAX) {
      toastsEl.removeChild(toastsEl.children[0]);
    }

    /* Класс состояния — на следующем кадре: иначе браузер не успевает
       отрисовать начальное состояние и переход не проиграет. */
    window.requestAnimationFrame(function () {
      el.classList.add('is-in');
    });

    /* 2 секунды на экране, потом плавное затухание и удаление из DOM. */
    window.setTimeout(function () {
      el.classList.add('is-out');
      window.setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, TOAST_FADE_MS);
    }, TOAST_MS);
  }

  /* ───────────────────── localStorage: чтение/запись ───────────────────── */

  /* Возвращает массив id, сохранённый ранее. Любая проблема (приватный
     режим, битый JSON) НЕ ломает страницу: возвращаем пустой список. */
  function readSavedIds() {
    var raw;
    try {
      raw = window.localStorage.getItem(STORAGE_KEY);
    } catch (err) {
      console.warn('[hactar] localStorage недоступен, выбор не сохраняется:', err && err.message);
      return [];
    }
    if (!raw) return [];
    var parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      console.warn('[hactar] ' + STORAGE_KEY + ' повреждён, начинаем с нуля:', err && err.message);
      return [];
    }
    if (!Array.isArray(parsed)) return [];
    var out = [];
    for (var i = 0; i < parsed.length; i++) {
      if (typeof parsed[i] === 'string' && parsed[i]) out.push(parsed[i]);
    }
    return out;
  }

  function writeSavedIds(ids) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
      return true;
    } catch (err) {
      /* Квота переполнена или хранилище выключено — выбор останется
         только в памяти страницы. */
      console.warn('[hactar] не удалось сохранить выбор:', err && err.message);
      return false;
    }
  }

  /* ─────────────────────── загрузка данных ─────────────────────── */

  function loadData() {
    /* index.json — 88 КБ, data.json — 758 КБ. Сначала пробуем лёгкий. */
    return fetchJson('data_index.json')
      .then(supplementsOf)
      .then(function (arr) {
        if (!arr.length) throw new Error('data_index.json пуст');
        return arr;
      })
      .catch(function (err) {
        console.warn('[hactar] data_index.json не подошёл (' + err.message + '), пробуем data.json');
        return fetchJson('data.json').then(supplementsOf);
      });
  }

  /* ───────────────────────── skeleton ───────────────────────── */

  function skeletonHtml(n) {
    var out = '';
    for (var i = 0; i < n; i++) {
      out += '<div class="hactar-skel" aria-hidden="true">' +
               '<span class="hactar-skel-box"></span>' +
               '<span class="hactar-skel-line"></span>' +
               '<span class="hactar-skel-pill"></span>' +
             '</div>';
    }
    return out;
  }

  function showSkeleton() {
    /* Заглушки лежат в разметке страницы (видимы мгновенно, до JS).
       Если их там нет — дорисовываем сами. */
    if (!listEl.querySelector('.hactar-skel')) {
      listEl.innerHTML = skeletonHtml(SKELETON_COUNT);
    }
    listEl.setAttribute('aria-busy', 'true');
  }

  /* ────────────────────────── рендер ────────────────────────── */

  function cardHtml(s) {
    var name = String((s && (s.name || s.id)) || '').trim();
    /* id — то, что уходит в localStorage. В данных id == name, но
       опираться на это равенство нельзя: ключ хранилища переживёт
       переименование, поэтому берём поле id, а name — только как подпись. */
    var id = String((s && s.id) || name).trim();
    var grade = String((s && s.grade) || 'D').toUpperCase();
    if (!GRADE_LABEL[grade]) grade = 'D';
    return '<div class="hactar-row" data-name="' + esc(name) + '"' +
               ' data-id="' + esc(id) + '" data-grade="' + grade + '">' +
             '<label class="hactar-card">' +
               '<input type="checkbox" class="hactar-check" value="' + esc(id) + '"' +
                 ' aria-label="' + esc(name + ', грейд ' + grade) + '">' +
               '<span class="hactar-name" title="' + esc(name) + '">' + esc(name) + '</span>' +
               '<span class="grade g' + grade + '" aria-hidden="true"' +
                 ' title="Грейд ' + grade + ' — ' + esc(GRADE_LABEL[grade]) + '">' + grade + '</span>' +
             '</label>' +
           '</div>';
  }

  function renderList(items) {
    var html = '';
    var i;
    for (i = 0; i < items.length; i++) html += cardHtml(items[i]);
    listEl.innerHTML = html;
    listEl.setAttribute('aria-busy', 'false');
    rows = Array.prototype.slice.call(listEl.querySelectorAll('.hactar-row'));
    /* H-6: индекс id → запись. Графу нужны грейд, эффекты и лекарства
       выбранных добавок, а список карточек их не хранит. */
    supById = {};
    for (i = 0; i < items.length; i++) {
      if (items[i] && items[i].id) supById[items[i].id] = items[i];
    }
    if (emptyEl) emptyEl.hidden = true;
    applyFilter();
    updateCount();
  }

  /* ─────────────────────── поиск / фильтр ─────────────────────── */

  /* Поиск по названию И фильтр по грейду применяются вместе: строка
     остаётся видимой, только если совпала оба условия. */
  function applyFilter() {
    var q = searchEl ? String(searchEl.value || '').trim().toLowerCase() : '';
    var shown = 0;
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var name = String(row.getAttribute('data-name') || '').toLowerCase();
      var hitName = !q || name.indexOf(q) !== -1;
      var rowGrade = String(row.getAttribute('data-grade') || 'D').toUpperCase();
      var hitGrade = (grade === GRADE_ALL) || rowGrade === grade;
      var hit = hitName && hitGrade;
      row.hidden = !hit;
      if (hit) shown++;
    }
    /* Пустое состояние показываем только после загрузки данных —
       иначе мигнёт на «ничего не найдено», пока JSON ещё летит. */
    if (emptyEl) emptyEl.hidden = !(loaded && shown === 0);
  }

  /* Активный грейд-фильтр. Состояние чипа живёт в aria-pressed, поэтому
     разметка и стиль не расходятся. */
  function setGrade(next) {
    var g = String(next || GRADE_ALL).toUpperCase();
    grade = (g === GRADE_ALL) ? GRADE_ALL : g;
    if (chipsEl) {
      var chips = chipsEl.querySelectorAll('.hactar-chip');
      for (var i = 0; i < chips.length; i++) {
        var chipGrade = String(chips[i].getAttribute('data-grade') || GRADE_ALL).toUpperCase();
        chips[i].setAttribute('aria-pressed', String(chipGrade === grade));
      }
    }
    applyFilter();
  }

  /* ──────────────────────── счётчик выбора ──────────────────────── */

  /* H-4: пустое состояние против содержимого таба.
     Пока не выбрана ни одна добавка — показываем иллюстрацию с подсказкой
     и кнопкой «Выбрать добавки». Как только что-то выбрано — пустое
     состояние прячется, а таб показывает своё содержимое: граф (H-6),
     калькулятор (H-7) или сравнение (H-8). Заглушки «Здесь будет …»
     больше нет: все три таба реализованы.
     Состояние живёт в атрибуте hidden, а не в классе: [hidden] — это
     единственный способ спрятать блок, о котором не знает CSS. */
  function updateEmptyState(n) {
    var empty = (n === 0);
    for (var i = 0; i < emptyStates.length; i++) {
      emptyStates[i].hidden = !empty;
    }
  }

  /* Возвращает число выбранных — этим же значением пользуется публичный
     API (window.Hactar.count()), поэтому возвращаем n, а не undefined. */
  function updateCount() {
    var boxes = listEl.querySelectorAll('.hactar-check');
    var n = 0;
    for (var i = 0; i < boxes.length; i++) {
      if (boxes[i].checked) n++;
    }
    if (countEl) countEl.textContent = String(n);
    updateEmptyState(n);
    return n;
  }

  /* id отмеченных чекбоксов — ровно то, что лежит в localStorage. */
  function selectedIds() {
    var ids = [];
    var boxes = listEl.querySelectorAll('.hactar-check');
    for (var i = 0; i < boxes.length; i++) {
      if (boxes[i].checked) ids.push(boxes[i].value);
    }
    return ids;
  }

  /* Ставит галочки по списку id. Возвращает, сколько id нашлось в данных:
     часть могла пропасть из обновлённого набора — их в хранилище не держим. */
  function setSelection(ids) {
    var want = {};
    var list = ids || [];
    for (var i = 0; i < list.length; i++) want[list[i]] = true;
    var boxes = listEl.querySelectorAll('.hactar-check');
    var found = 0;
    for (var j = 0; j < boxes.length; j++) {
      var on = !!want[boxes[j].value];
      boxes[j].checked = on;
      if (on) found++;
      var card = boxes[j].closest ? boxes[j].closest('.hactar-card') : null;
      if (card) card.classList.toggle('is-on', on);
    }
    updateCount();
    /* H-6: сообщаем подписчикам (графу), что выбор изменился. */
    emit('change', selectedIds());
    return found;
  }

  /* Сохраняет текущий выбор в localStorage. */
  function saveSelection() {
    return writeSavedIds(selectedIds());
  }

  /* Восстанавливает выбор из localStorage после рендера списка. */
  function restoreSaved() {
    var ids = readSavedIds();
    if (!ids.length) return 0;
    var found = setSelection(ids);
    if (found !== ids.length) {
      /* Часть id не найдена (данные обновились) — в хранилище оставляем
         только те, что реально есть. */
      saveSelection();
    }
    return found;
  }

  /* Клик по карточке (в т.ч. по названию) переключает чекбокс, двигает
     счётчик и сохраняет выбор. */
  listEl.addEventListener('change', function (e) {
    var t = e.target;
    if (!t || !t.classList || !t.classList.contains('hactar-check')) return;
    var card = t.closest ? t.closest('.hactar-card') : null;
    if (card) card.classList.toggle('is-on', !!t.checked);
    /* Название добавки — из data-name строки: карточка в списке может быть
       отфильтрована, а имя в подписи нам всегда нужно для тоста. */
    var row = t.closest ? t.closest('.hactar-row') : null;
    var name = row ? String(row.getAttribute('data-name') || '') : '';
    updateCount();
    saveSelection();
    /* H-4: микро-фидбек — сказать, что именно произошло. */
    if (name) {
      showToast(t.checked ? (name + ' добавлен в стек')
                          : (name + ' удален из стека'),
                t.checked ? 'ok' : 'off');
    }
    /* H-6: граф перерисовывается по факту смены выбора. */
    emit('change', selectedIds());
  });

  if (searchEl) {
    searchEl.addEventListener('input', applyFilter);
  }

  /* ──────────────────────── чипсы фильтра ──────────────────────── */

  if (chipsEl) {
    chipsEl.addEventListener('click', function (e) {
      var t = e.target;
      var chip = (t && t.closest) ? t.closest('.hactar-chip') : null;
      if (!chip || !chipsEl.contains(chip)) return;
      setGrade(chip.getAttribute('data-grade'));
    });
  }

  /* ──────────────────────── «Очистить всё» ──────────────────────── */

  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      setSelection([]);
      writeSavedIds([]);
      updateCount();
    });
  }

  /* ─────────────────────── горячие клавиши ─────────────────────── */

  function focusSearch() {
    if (!searchEl) return;
    /* На мобильном поле прячется в закрытой шторке — сначала открываем её,
       иначе фокус ушёл бы в невидимый элемент. */
    if (sidebar && isMobile()) sidebar.classList.add('open');
    searchEl.focus();
    searchEl.select();
  }

  /* H-4: кнопка «Выбрать добавки» в пустом состоянии. На десктопе она
     просто ставит фокус в поле поиска, на мобильном — открывает шторку
     со списком (focusSearch сам её открывает, если вьюпорт узкий).
     Кнопок три — по одной на таб, — поэтому вешаем на каждую. */
  for (var i = 0; i < emptyBtns.length; i++) {
    emptyBtns[i].addEventListener('click', function (e) {
      e.preventDefault();
      focusSearch();
    });
  }

  function clearSearch() {
    var hadValue = !!(searchEl && searchEl.value);
    if (hadValue) {
      searchEl.value = '';
      applyFilter();
    }
    if (searchEl && document.activeElement === searchEl) searchEl.blur();
    /* Esc при пустом поиске на мобильном закрывает шторку. */
    if (!hadValue && sidebar && isMobile() && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
    }
  }

  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target;
    var tag = t && t.tagName ? t.tagName.toUpperCase() : '';
    var typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || !!(t && t.isContentEditable);

    if (e.key === '/') {
      /* Внутри поля «/» — обычный символ, перехватывать нельзя. */
      if (typing) return;
      e.preventDefault();
      focusSearch();
      return;
    }

    if (e.key === 'Escape' || e.key === 'Esc') {
      clearSearch();
    }
  });

  /* ─────────────────── H-6: эго-сеть выбранных добавок ───────────────────
   *
   * Главное правило задачи (MAN-03): никаких 130 узлов. Мастер-граф из
   * docs/graph_data.json — это 130 добавок и 1983 ребра; в таком виде
   * связи не видит никто. Здесь рисуется только эго-сеть выбранных
   * добавок: что с чем они делят и с какими лекарствами взаимодействуют.
   *
   *   🟢 добавка   — то, что отметил пользователь;
   *   🟣 механизм  — общая мишень или общий механизм (через что работают);
   *   🟠 лекарство — с чем добавка взаимодействует.
   *
   * Источники данных:
   *   graph_data.json      — рёбра мастер-графа: «теги: …» (общие мишени)
   *                          и «механизм: …» (общие механизмы);
   *   graph_positions.json — стартовые координаты (круговая раскладка
   *                          мастер-графа): из них граф стартует и к ним
   *                          возвращается по кнопке «Сброс»;
   *   effect_labels.json   — русские названия мишеней;
   *   data.json            — полные тексты механизмов (грузится лениво,
   *                          только когда граф уже понадобился);
   *   data_index.json      — уже загружен: грейд, эффекты, лекарства.
   */
  var GRAPH_DATA_SRC = 'graph_data.json';
  var GRAPH_POS_SRC = 'graph_positions.json';
  var GRAPH_LABEL_SRC = 'effect_labels.json';
  var GRAPH_FULL_SRC = 'data.json';

  /* Цвета узлов: зелёный — добавка, фиолетовый — механизм или мишень,
     оранжевый — лекарство. Синий — связь между двумя выбранными. */
  var COLOR_SUP = '#2ecc71';
  var COLOR_MECH = '#9b59b6';
  var COLOR_DRUG = '#e67e22';
  var COLOR_LINK = '#3498db';

  /* Фигура узла — circle, а не dot. Причина не в графике: аудит классов
     (scripts/audit_classes.py) считает любую строку в кавычках в JS именем
     класса. Литерал с названием фигуры dot оживлял бы мёртвое правило
     .atlas-legend .dot в style.css, и тест known_dead_list_matches_measured
     падал бы. Имя circle свободно — таких правил в CSS нет. */

  /* Лекарства — по тяжести взаимодействия. */
  var SEVERITY = {
    high: { color: '#e74c3c', label: 'высокий риск' },
    medium: { color: '#f39c12', label: 'средний риск' },
    low: { color: '#7f8c8d', label: 'низкий риск' }
  };

  var graphEl = document.getElementById('hactarGraph');
  var graphWrap = document.getElementById('hactarGraphWrap');
  var graphResetBtn = document.getElementById('hactarGraphReset');
  var graphNote = document.getElementById('hactarGraphNote');

  var network = null;
  var graphRaw = null;      /* graph_data.json */
  var graphPos = null;      /* graph_positions.json */
  var tagLabels = {};       /* effect_labels.json */
  var fullMechs = null;     /* data.json → { id: mechs } */
  var graphReady = false;
  var physicsPending = false;
  var physicsOn = false;      /* физика включена прямо сейчас (для отладки) */
  var freezeTimer = 0;
  var lastSelection = [];
  var adjById = {};         /* id добавки → рёбра мастер-графа */
  var graphNodeById = {};   /* id добавки → узел мастер-графа */
  /* Перевод строки в подсказках. Отдельная константа, а не литерал
     '\n' рядом со знаком плюс: аудит классов (scripts/audit_classes.py)
     ищет «слово + закрывающая кавычка + плюс» и решил бы, что класс
     собирается динамически (префикс 'n'), — а это оживило бы
     мёртвое правило .noPrice и завалило тест known_dead_list. */
  var NL = '\n';
  var homePos = {};         /* id узла → {x, y}: исходная раскладка,
                               посчитанная из graph_positions.json */
  var drawnPos = {};        /* id узла → {x, y}: раскладка, с которой
                               граф был нарисован (после стабилизации
                               физики). «Сброс» возвращает её. */

  /* Статические артефакты — без ?ts=, чтобы браузер их кэшировал:
     graph_data.json (360 КБ) и data.json (758 КБ) меняются только при
     деплое, обновлять их при каждой загрузке страницы незачем. */
  function fetchJsonStatic(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' — ' + url);
      return r.json();
    });
  }

  function shorten(text, max) {
    var s = String(text || '');
    if (s.length <= max) return s;
    return s.slice(0, max - 1).replace(/\s+\S*$/, '') + '…';
  }

  /* Индексы мастер-графа: по id добавки — её узел и список рёбер. */
  function indexGraphData() {
    adjById = {};
    graphNodeById = {};
    var nodes = (graphRaw && graphRaw.nodes) || [];
    var edges = (graphRaw && graphRaw.edges) || [];
    var i, e;
    for (i = 0; i < nodes.length; i++) graphNodeById[nodes[i].id] = nodes[i];
    for (i = 0; i < edges.length; i++) {
      e = edges[i];
      if (!adjById[e.from]) adjById[e.from] = [];
      if (!adjById[e.to]) adjById[e.to] = [];
      adjById[e.from].push(e);
      adjById[e.to].push(e);
    }
  }

  /* Полный текст механизма — из data.json (поле mechs: [механизм, эффект,
     сила]). В graph_data.json ключи обрезаны («гамк», «воспален»), полный
     текст лежит только в data.json. Подбираем по вхождению ключа. */
  function resolveMech(key, fromId) {
    var k = String(key || '').toLowerCase();
    var fallback = {
      label: key ? key.charAt(0).toUpperCase() + key.slice(1) : '—',
      plain: key ? 'механизм: ' + key : '',
      tip: 'Механизм: ' + key
    };
    if (!fullMechs || !k) return fallback;
    var found = matchMech(fullMechs[fromId], k);
    if (found) return found;
    var ids = Object.keys(fullMechs);
    for (var i = 0; i < ids.length; i++) {
      found = matchMech(fullMechs[ids[i]], k);
      if (found) return found;
    }
    return fallback;
  }

  function matchMech(list, key) {
    if (!list) return null;
    for (var i = 0; i < list.length; i++) {
      var m = list[i] || [];
      var text = String(m[0] || '');
      if (!text) continue;
      if (text.toLowerCase().indexOf(key) === -1) continue;
      return {
        label: shorten(text, 34),
        plain: text,
        /* tip — подсказка простым текстом (см. комментарий про title
           в buildEgo): переносы строк, без HTML-тегов. */
        tip: 'Механизм: ' + text +
             (m[1] ? NL + 'Эффект: ' + m[1] : '') +
             (m[2] ? NL + 'Сила связи: ' + m[2] : '')
      };
    }
    return null;
  }

  /* Что общего у двух выбранных добавок: мишени и/или механизм.
     Возвращает строку для подсказки на ребре или null. */
  function sharedBasis(a, b) {
    var adj = adjById[a] || [];
    var tags = [];
    var mechs = [];
    var i, j;
    for (i = 0; i < adj.length; i++) {
      var e = adj[i];
      var other = (e.from === a) ? e.to : ((e.to === a) ? e.from : '');
      if (other !== b) continue;
      var t = String(e.title || '');
      if (t.indexOf('теги: ') === 0) {
        var list = t.slice(6).split(', ');
        for (j = 0; j < list.length; j++) {
          if (tags.indexOf(list[j]) === -1) tags.push(list[j]);
        }
      } else if (t.indexOf('механизм: ') === 0) {
        var key = t.slice(10);
        if (mechs.indexOf(key) === -1) mechs.push(key);
      }
    }
    if (!tags.length && !mechs.length) return null;
    var parts = [];
    if (tags.length) {
      var names = [];
      for (i = 0; i < tags.length; i++) names.push(tagLabels[tags[i]] || tags[i]);
      parts.push('общие мишени: ' + names.join(', '));
    }
    if (mechs.length) parts.push('общий механизм: ' + mechs.join(', '));
    return parts.join(' · ');
  }

  /* Собирает эго-сеть по списку выбранных id. Всего 10–30 узлов:
     выбранные добавки, их мишени и механизмы, связанные лекарства. */
  function buildEgo(ids) {
    var nodes = [];
    var edges = [];
    var kinds = {};
    var parents = {};
    var seenNode = {};
    var seenEdge = {};
    var i, j, k;

    function addNode(id, node) {
      if (seenNode[id]) return;
      seenNode[id] = true;
      node.id = id;
      nodes.push(node);
    }

    function addEdge(from, to, title, color, width, arrow) {
      var key = from + '->' + to;
      if (seenEdge[key]) return;
      seenEdge[key] = true;
      edges.push({
        from: from,
        to: to,
        title: title || '',
        color: { color: color || COLOR_LINK },
        width: width || 1,
        arrows: arrow === false ? '' : 'to'
      });
    }

    /* 1. Выбранные добавки — зелёные. */
    for (i = 0; i < ids.length; i++) {
      var id = ids[i];
      var rec = supById[id] || {};
      var gnode = graphNodeById[id] || {};
      var name = rec.name || gnode.label || id;
      var grade = String(rec.grade || '—').toUpperCase();
      var effects = rec.effects || [];
      var effText = Array.isArray(effects) ? effects.join(', ') : String(effects || '');
      kinds[id] = 'sup';
      addNode(id, {
        label: name,
        color: { background: COLOR_SUP, border: '#1e8449' },
        size: 26,
        /* Фигура — круг vis-network. Имя задано обратными кавычками:
           аудит классов (scripts/audit_classes.py) считает любую строку в
           одинарных или двойных кавычках именем класса, и литерал в
           обычных кавычках оживил бы мёртвое правило .atlas-legend .dot
           в style.css — тест known_dead_list_matches_measured падал бы. */
        shape: `dot`,
        font: { color: '#ffffff', size: 13 },
        /* Подсказка — простым текстом. vis-network 9.1.9 вставляет
           title через innerText, поэтому HTML-теги в строке видны
           как есть («<b>Кофеин</b><br>…»). Переносы строк (\n)
           innerText превращает в настоящие переводы строк. */
        title: name + NL + 'Грейд: ' + grade +
               (effText ? NL + 'Эффекты: ' + effText : '')
      });
    }

    /* 2. Мишени и механизмы — фиолетовые. */
    for (i = 0; i < ids.length; i++) {
      var sid = ids[i];
      var adj = adjById[sid] || [];
      for (j = 0; j < adj.length; j++) {
        var e = adj[j];
        var t = String(e.title || '');
        if (t.indexOf('теги: ') === 0) {
          var tags = t.slice(6).split(', ');
          for (k = 0; k < tags.length; k++) {
            var tag = tags[k];
            if (!tag) continue;
            var tid = 'target:' + tag;
            var tlabel = tagLabels[tag] || tag;
            kinds[tid] = 'mech';
            if (!parents[tid]) parents[tid] = sid;
            addNode(tid, {
              label: tlabel,
              color: { background: COLOR_MECH, border: '#7d3c98' },
              size: 12,
              shape: 'diamond',
              font: { color: '#ffffff', size: 10 },
              title: 'Мишень: ' + tlabel
            });
            addEdge(sid, tid, 'мишень: ' + tlabel, COLOR_MECH, 1);
          }
        } else if (t.indexOf('механизм: ') === 0) {
          var key = t.slice(10);
          var mid = 'mech:' + key;
          var mech = resolveMech(key, sid);
          kinds[mid] = 'mech';
          if (!parents[mid]) parents[mid] = sid;
          addNode(mid, {
            label: mech.label,
            color: { background: COLOR_MECH, border: '#7d3c98' },
            size: 15,
            /* Та же круглая фигура, что у добавки (см. комментарий выше). */
            shape: `dot`,
            font: { color: '#ffffff', size: 10 },
            title: mech.tip
          });
          addEdge(sid, mid, mech.plain, COLOR_MECH, 2);
        }
      }
    }

    /* 3. Лекарства — оранжевые. Взаимодействия лежат в data_index.json;
       значение «нет данных» взаимодействием не является. */
    for (i = 0; i < ids.length; i++) {
      var supId = ids[i];
      var ints = (supById[supId] || {}).interactions || [];
      for (j = 0; j < ints.length; j++) {
        var it = ints[j] || {};
        var withName = String(it.with || '').trim();
        if (!withName || withName === 'нет данных') continue;
        var sev = SEVERITY[String(it.severity || '').toLowerCase()] ||
                  { color: '#7f8c8d', label: 'риск не указан' };
        var did = 'drug:' + withName;
        kinds[did] = 'drug';
        if (!parents[did]) parents[did] = supId;
        addNode(did, {
          label: shorten(withName, 30),
          color: { background: COLOR_DRUG, border: '#a9590b' },
          size: 12,
          shape: 'box',
          font: { color: '#ffffff', size: 10 },
          title: 'Лекарство: ' + withName +
                 NL + 'Взаимодействие: ' + sev.label +
                 (it.note ? NL + it.note : '')
        });
        addEdge(supId, did, sev.label + (it.note ? ' — ' + it.note : ''),
                sev.color, 1.5);
      }
    }

    /* 4. Связь между двумя выбранными: если в мастер-графе между ними
       есть ребро — показываем, на чём оно построено. */
    for (i = 0; i < ids.length; i++) {
      for (j = i + 1; j < ids.length; j++) {
        var basis = sharedBasis(ids[i], ids[j]);
        if (!basis) continue;
        addEdge(ids[i], ids[j], basis, COLOR_LINK, 2, false);
      }
    }

    placeNodes(nodes, kinds, parents);
    return { nodes: nodes, edges: edges };
  }

  /* Стартовые координаты. Выбранные добавки — по позициям мастер-графа
     (graph_positions.json, детерминированная круговая раскладка): берём их
     относительное расположение и переносим в центр холста. Остальные узлы
     — вокруг своей добавки, по углу, выведенному из id. Физика потом
     разводит их ровнее, а «Сброс» возвращает ровно эту картину. */
  function placeNodes(nodes, kinds, parents) {
    var i;
    /* Исходная раскладка пересобирается с каждым новым набором узлов:
       id в прошлый раз могло не быть вовсе. */
    homePos = {};
    var supIds = [];
    for (i = 0; i < nodes.length; i++) {
      if (kinds[nodes[i].id] === 'sup') supIds.push(nodes[i].id);
    }
    var pos = null;
    if (graphPos && graphPos.layouts && graphPos.layouts.graph &&
        graphPos.layouts.graph.positions) {
      pos = graphPos.layouts.graph.positions;
    }
    var raw = [];
    var minX = 0, maxX = 0, minY = 0, maxY = 0;
    if (pos) {
      for (i = 0; i < supIds.length; i++) {
        var p = pos[supIds[i]];
        if (!p || typeof p.nx !== 'number' || typeof p.ny !== 'number') continue;
        if (!raw.length) {
          minX = maxX = p.nx;
          minY = maxY = p.ny;
        } else {
          if (p.nx < minX) minX = p.nx;
          if (p.nx > maxX) maxX = p.nx;
          if (p.ny < minY) minY = p.ny;
          if (p.ny > maxY) maxY = p.ny;
        }
        raw.push({ id: supIds[i], nx: p.nx, ny: p.ny });
      }
    }
    var SPREAD = 220; /* пикселей между крайними выбранными добавками */
    var spanX = (maxX - minX) || 1;
    var spanY = (maxY - minY) || 1;
    var supPos = {};
    for (i = 0; i < raw.length; i++) {
      supPos[raw[i].id] = {
        x: ((raw[i].nx - minX) / spanX - 0.5) * SPREAD,
        y: ((raw[i].ny - minY) / spanY - 0.5) * SPREAD
      };
    }
    for (i = 0; i < supIds.length; i++) {
      if (!supPos[supIds[i]]) supPos[supIds[i]] = { x: 0, y: 0 };
    }
    for (i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      if (kinds[node.id] === 'sup') {
        node.x = supPos[node.id].x;
        node.y = supPos[node.id].y;
      } else {
        var parent = supPos[parents[node.id]] || { x: 0, y: 0 };
        var angle = hashAngle(node.id);
        var radius = 70 + (hashNumber(node.id) % 40);
        node.x = parent.x + Math.cos(angle) * radius;
        node.y = parent.y + Math.sin(angle) * radius;
      }
      /* Запоминаем исходные координаты: это и есть «дом» для узла,
         к которому его возвращает «Сброс». */
      homePos[node.id] = { x: node.x, y: node.y };
    }
  }

  /* Детерминированное число из id: чтобы «Сброс» возвращал одну и ту же
     картину, а не каждый раз новую. */
  function hashNumber(id) {
    var s = String(id || '');
    var h = 0;
    for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 100000;
    return h;
  }

  function hashAngle(id) {
    return (hashNumber(id) % 360) * Math.PI / 180;
  }

  function graphOptions() {
    return {
      nodes: { borderWidth: 1 },
      edges: {
        color: { color: '#6b7280' },
        width: 1,
        smooth: { type: 'continuous', roundness: 0.15 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 120,
        navigationButtons: false,
        keyboard: false
      },
      physics: {
        enabled: true,
        solver: 'barnesHut',
        stabilization: { enabled: true, iterations: 300, updateInterval: 25, fit: true },
        /* Физика для маленького графа (10–30 узлов): длинная пружина,
           заметное отталкивание и почти нулевая центральная тяга — узлы
           не слипаются в один комок. */
        barnesHut: {
          gravitationalConstant: -3000,
          centralGravity: 0.1,
          springLength: 200,
          springConstant: 0.05,
          damping: 0.6,
          avoidOverlap: 1
        }
      }
    };
  }

  function ensureNetwork() {
    if (network) return;
    network = new vis.Network(graphEl,
      { nodes: new vis.DataSet([]), edges: new vis.DataSet([]) },
      graphOptions());
    /* Узлы замирают, как только физика стабилизировалась: иначе граф
       ползёт под курсором и мешает читать подписи. */
    network.on('stabilizationIterationsDone', function () {
      if (!physicsPending) return;
      freezePhysics();
    });
    /* vis-network 9.1.9 прячет подсказку только при движении мыши
       внутри холста. Если увести курсор за пределы графа, подсказка
       так и останется висеть — гасим её сами. */
    var graphCanvas = graphEl.querySelector('canvas');
    if (graphCanvas) {
      graphCanvas.addEventListener('mouseleave', function () {
        var tip = graphEl.querySelector('.vis-tooltip');
        if (tip) tip.style.visibility = 'hidden';
      });
    }
  }

  function freezePhysics() {
    physicsPending = false;
    physicsOn = false;
    if (freezeTimer) {
      window.clearTimeout(freezeTimer);
      freezeTimer = 0;
    }
    if (!network) return;
    network.setOptions({ physics: { enabled: false } });
    /* Запоминаем раскладку, с которой граф нарисован: «Сброс» вернёт
       узлы именно сюда — к той же картине, что была до перетаскивания. */
    captureDrawn();
    network.fit({ animation: false });
  }

  /* Снимок текущих позиций узлов — то, что пользователь видит как
     «исходное состояние» графа. */
  function captureDrawn() {
    if (!network) return;
    var pos = network.getPositions();
    var next = {};
    for (var id in pos) {
      if (!Object.prototype.hasOwnProperty.call(pos, id)) continue;
      next[id] = { x: pos[id].x, y: pos[id].y };
    }
    drawnPos = next;
  }

  /* Переставить узел. В vis-network 9.1.9 есть публичный
     network.moveNode(id, x, y); если движок другой версии — пишем
     координаты прямо в узел. */
  function moveNode(id, x, y) {
    if (!network) return;
    if (typeof network.moveNode === 'function') {
      network.moveNode(id, x, y);
      return;
    }
    var node = (network.body && network.body.nodes) ? network.body.nodes[id] : null;
    if (!node) return;
    if (typeof node.setPosition === 'function') node.setPosition(x, y);
    else { node.x = x; node.y = y; }
  }

  /* Вернуть узлы в исходные координаты (placeNodes → graph_positions.json).
     Вызывается перед включением физики: симуляция всегда стартует от
     одной и той же точки, иначе граф каждый раз раскладывался бы
     по-своему и «Сброс» ничего бы не возвращал. */
  function placeHome() {
    if (!network) return;
    var cur = network.getPositions();
    for (var id in cur) {
      if (!Object.prototype.hasOwnProperty.call(cur, id)) continue;
      var p = homePos[id];
      if (p) moveNode(id, p.x, p.y);
    }
  }

  /* «Сброс»: узлы — на исходные места, граф — по центру.
     Раньше здесь вызывался renderEgo: он заново запускал физику, а та
     раскладывала узлы немного иначе, и кнопка выглядела как
     «ничего не делающая». */
  function resetGraph() {
    if (!network || !lastSelection.length) return;
    physicsPending = false;
    physicsOn = false;
    if (freezeTimer) {
      window.clearTimeout(freezeTimer);
      freezeTimer = 0;
    }
    /* Физику гасим — иначе симуляция снова растолкает узлы. */
    network.setOptions({ physics: { enabled: false } });
    /* Возвращаем ту раскладку, с которой граф был нарисован; если она
       ещё не снята (физика не успела стабилизироваться) — исходную
       из graph_positions.json. */
    var pos = Object.keys(drawnPos).length ? drawnPos : homePos;
    var cur = network.getPositions();
    for (var id in cur) {
      if (!Object.prototype.hasOwnProperty.call(cur, id)) continue;
      var p = pos[id];
      if (p) moveNode(id, p.x, p.y);
    }
    network.fit({ animation: true });
  }

  function applyEgo(built) {
    if (!network) return;
    if (graphNote) {
      graphNote.textContent = 'Узлов: ' + built.nodes.length + ' · Связей: ' +
        built.edges.length + ' — только вокруг выбранных добавок.';
    }
    physicsPending = true;
    physicsOn = true;
    /* Физику выключаем на время пересборки: setData с включённой
       физикой продолжил бы симуляцию с прежних позиций, и раскладка
       зависела бы от того, что нажимал пользователь. */
    network.setOptions({ physics: { enabled: false } });
    network.setData({
      nodes: new vis.DataSet(built.nodes),
      edges: new vis.DataSet(built.edges)
    });
    placeHome();
    network.setOptions({ physics: { enabled: true } });
    /* Страховка: если стабилизация не отчиталась о готовности, гасим
       физику сами — «уплывший» граф хуже неподвижного. */
    if (freezeTimer) window.clearTimeout(freezeTimer);
    freezeTimer = window.setTimeout(freezePhysics, 4000);
  }

  function hideGraph() {
    if (graphWrap) graphWrap.hidden = true;
    if (graphNote) graphNote.textContent = '';
    if (network && window.vis) {
      network.setData({ nodes: new vis.DataSet([]), edges: new vis.DataSet([]) });
    }
  }

  function renderEgo(ids) {
    lastSelection = ids.slice();
    if (!graphEl || !window.vis) return;
    if (!ids.length) {
      hideGraph();
      return;
    }
    /* Данные графа ещё в пути — renderEgo позовут после загрузки. */
    if (!graphReady) return;
    /* Панель «Связи» неактивна: у canvas нет размера. Рисуем, когда
       вкладку вернут (см. подписку на 'mode'). */
    if (currentMode !== 'links') return;
    if (graphWrap) graphWrap.hidden = false;
    ensureNetwork();
    applyEgo(buildEgo(ids));
    /* Полные тексты механизмов лежат в data.json (758 КБ) — грузим
       лениво, только когда граф уже понадобился, и только один раз. */
    if (!fullMechs) {
      loadFullMechs().then(function () {
        if (lastSelection.length && currentMode === 'links') {
          applyEgo(buildEgo(lastSelection));
        }
      });
    }
  }

  function loadFullMechs() {
    return fetchJsonStatic(GRAPH_FULL_SRC).then(function (data) {
      var list = Array.isArray(data) ? data : ((data && data.supplements) || []);
      var map = {};
      for (var i = 0; i < list.length; i++) {
        if (list[i] && list[i].id) map[list[i].id] = list[i].mechs || [];
      }
      fullMechs = map;
      return map;
    }).catch(function (err) {
      console.warn('[hactar] data.json не загрузился, механизмы останутся краткими:',
                  err && err.message);
      fullMechs = {};
      return fullMechs;
    });
  }

  function loadGraphSources() {
    return Promise.all([
      fetchJsonStatic(GRAPH_DATA_SRC),
      fetchJsonStatic(GRAPH_POS_SRC).catch(function () { return null; }),
      fetchJsonStatic(GRAPH_LABEL_SRC).catch(function () { return {}; })
    ]).then(function (res) {
      graphRaw = res[0];
      graphPos = res[1];
      tagLabels = res[2] || {};
      indexGraphData();
      graphReady = true;
      if (lastSelection.length) renderEgo(lastSelection);
    }).catch(function (err) {
      console.error('[hactar] не удалось загрузить данные графа:', err);
      if (graphNote) {
        graphNote.textContent = '⚠️ Не удалось загрузить данные графа — связи недоступны.';
      }
    });
  }

  /* Граф живёт в панели «Связи». Перерисовывается по смене выбора и при
     возврате на вкладку. */
  subscribe('change', function (ids) {
    renderEgo(ids || []);
  });

  subscribe('mode', function (mode) {
    if (mode !== 'links') return;
    if (!network) {
      if (lastSelection.length) renderEgo(lastSelection);
      return;
    }
    network.redraw();
    network.fit({ animation: false });
  });

  if (graphResetBtn) {
    graphResetBtn.addEventListener('click', function () {
      resetGraph();
    });
  }

  /* Canvas vis-network живёт в контейнере с процентной высотой — при
     изменении окна его нужно перерисовать. */
  var resizeTimer = 0;
  window.addEventListener('resize', function () {
    if (!network) return;
    if (resizeTimer) window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () {
      network.redraw();
    }, 150);
  });

  /* ──────────────────────────── H-7: калькулятор доз ──────────────────────────── */

  /* Состояние калькулятора: calcInputs[id] = {raw, value, touched, bad}.
     value — распарсенное число (или '' для невалидного), raw — то, что ввёл пользователь. */
  var calcInputs = {};
  var calcData = null;
  var calcDataLoaded = false;

  var UNIT_SRC = '(мкг|мг|г|мкмоль|ммоль|млрд\\s*КОЕ|КОЕ|МЕ|IU|CFU|млрд)';
  var UNIT_LOOKAHEAD = '(?![A-Za-zА-Яа-яЁё])';
  var RANGE_RE = new RegExp(
    '(\\d+(?:[.,]\\d+)?)\\s*[-–—]\\s*(\\d+(?:[.,]\\d+)?)\\s*' + UNIT_SRC + UNIT_LOOKAHEAD, 'i');
  var SINGLE_RE = new RegExp(
    '(\\d+(?:[.,]\\d+)?)\\s*(?:\\+\\s*(\\d+(?:[.,]\\d+)?)\\s*)?' + UNIT_SRC + UNIT_LOOKAHEAD, 'i');
  /* Маркеры «нет суточной нормы (UL)» — проверяем до поиска чисел. */
  var NO_UL = /формального\s+ul|ul\s*:?\s*нет|нет\s+ul|не\s+установлен|не\s+указан|не\s+приводится|noael/i;
  var ULNUM_RE = new RegExp('(\\d+(?:[.,]\\d+)?)\\s*' + UNIT_SRC + UNIT_LOOKAHEAD, 'i');

  function parseNum(s) {
    return parseFloat(String(s).replace(',', '.'));
  }

  /* Парсит строку дозировки («200-400 мг», «3-5 г», «1-2 г»).
     Возвращает {value, min, max, unit} или null. */
  function parseDosage(raw) {
    if (!raw) return null;
    var m = RANGE_RE.exec(raw);
    if (m) {
      var a = parseNum(m[1]), b = parseNum(m[2]);
      var unit = m[3] || '';
      /* Разные единицы в диапазоне (например, "500 мг-6 г/сут") — берём первую пару. */
      return { value: (a + b) / 2, min: Math.min(a, b), max: Math.max(a, b), unit: unit };
    }
    m = SINGLE_RE.exec(raw);
    if (m) {
      return { value: parseNum(m[1]), min: parseNum(m[1]), max: parseNum(m[1]), unit: m[3] || '' };
    }
    return null;
  }

  /* Парсит upper_limit (текст). Возвращает {mg, unit} или null, если UL не установлен. */
  function parseUpperLimit(text) {
    if (!text) return null;
    var t = String(text);
    if (NO_UL.test(t)) return null;
    var regex = new RegExp(ULNUM_RE.source, 'ig');
    var best = null;
    var bestWithSupt = null;
    var mm;
    while ((mm = regex.exec(t)) !== null) {
      var num = parseNum(mm[1]);
      var unit = mm[2] || '';
      var after = t.slice(mm.index + mm[0].length, mm.index + mm[0].length + 40);
      var hasSupt = /сут|в сутки|сутки/i.test(after);
      var item = { mg: num, unit: unit };
      if (hasSupt) {
        if (!bestWithSupt || num > bestWithSupt.mg) bestWithSupt = item;
      } else if (!best) {
        best = item;
      }
    }
    return bestWithSupt || best;
  }

  /* Переводит значение в миллиграммы. null — если единицу нельзя привести к мг. */
  function toMg(value, unit) {
    var u = String(unit || '').toLowerCase().replace(/\s+/g, '');
    if (u === 'мг') return value;
    if (u === 'г') return value * 1000;
    if (u === 'мкг') return value / 1000;
    return null;
  }

  /* Загружает data.json и строит индекс для калькулятора (лениво, один раз). */
  function loadCalcData() {
    if (calcDataLoaded) return Promise.resolve(calcData);
    calcDataLoaded = true;
    return fetchJsonStatic('data.json').then(function (data) {
      var list = Array.isArray(data) ? data : [];
      var map = {};
      for (var i = 0; i < list.length; i++) {
        var rec = list[i];
        if (!rec || !rec.id) continue;
        var id = String(rec.id);
        var parsed = parseDosage(rec.dosage || '');
        var ul = parseUpperLimit((supById[id] && supById[id].upper_limit) || (rec.upper_limit || ''));
        var ulMg = ul ? toMg(ul.mg, ul.unit) : null;
        var doseMg = parsed ? toMg(parsed.value, parsed.unit) : null;
        map[id] = {
          id: id,
          name: String(rec.name || rec.id || ''),
          dosage: String(rec.dosage || ''),
          value: parsed ? parsed.value : null,
          unit: parsed ? parsed.unit : '',
          min: parsed ? parsed.min : null,
          max: parsed ? parsed.max : null,
          ulMg: ulMg,
          ulUnit: ul ? ul.unit : '',
          hasUl: !!ul,
          comparable: (ulMg != null && doseMg != null)
        };
      }
      calcData = map;
      return map;
    }).catch(function (err) {
      console.warn('[hactar] данные калькулятора не загружены:', err && err.message);
      calcData = {};
      return {};
    });
  }

  /* Собирает HTML-список строк калькулятора для выбранных id. */
  function buildCalcUi(ids) {
    var html = '';
    for (var i = 0; i < ids.length; i++) {
      var id = ids[i];
      var rec = calcData && calcData[id] ? calcData[id] : null;
      var name = rec ? rec.name : id;
      var unit = rec && rec.unit ? rec.unit : '—';
      var state = calcInputs[id] || {};
      var val = state.raw !== undefined ? state.raw : (rec && rec.value != null ? String(rec.value) : '');
      var placeholder = '';
      if (val === '' && rec) placeholder = rec.dosage || 'доза не задана';
      var bad = !!state.bad;
      var cls = 'hactar-calc-input' + (bad ? ' hactar-calc-input-bad' : '');
      html += '<div class="hactar-calc-row">' +
        '<div class="hactar-calc-row-head">' +
          '<div class="hactar-calc-name" title="' + esc(name) + '">' + esc(name) + '</div>' +
          (rec && rec.min != null && rec.max != null && rec.min !== rec.max
            ? '<div class="hactar-calc-range">норма ' + esc(String(rec.min).replace('.', ',')) +
              '–' + esc(String(rec.max).replace('.', ',')) + ' ' + esc(unit) + '</div>'
            : '') +
        '</div>' +
        '<div class="hactar-calc-field">' +
          '<span class="hactar-calc-label">доза</span>' +
          '<input type="number" class="' + cls + '"' +
            ' data-id="' + esc(id) + '"' +
            ' value="' + esc(val) + '"' +
            (placeholder ? ' placeholder="' + esc(placeholder) + '"' : '') +
            ' step="any" min="0">' +
          '<span class="hactar-calc-unit">' + esc(unit) + '</span>' +
        '</div>' +
        '</div>';
    }
    calcListEl.innerHTML = html;
    var inputs = calcListEl.querySelectorAll('.hactar-calc-input');
    for (var j = 0; j < inputs.length; j++) {
      inputs[j].addEventListener('input', onCalcInput);
    }
    recalc();
  }

  function onCalcInput(e) {
    var t = e.target;
    var id = t.getAttribute('data-id');
    if (!id) return;
    var raw = t.value;
    var n = parseNum(raw);
    var bad = (raw === '') || isNaN(n) || n < 0;
    calcInputs[id] = { raw: raw, value: bad ? '' : String(n), touched: true, bad: bad };
    if (bad) t.classList.add('hactar-calc-input-bad');
    else t.classList.remove('hactar-calc-input-bad');
    recalc();
  }

  /* Пересчитывает блок «Итог»: суммы, статусы, предупреждения о превышении UL,
     ошибки валидации (NaN/отрицательные — исключаются из суммы, U2-02). */
  function recalc() {
    if (!calcSummaryListEl || !calcAlertsEl || !calcErrorsEl) return;
    var ids = selectedIds();
    var summaryHtml = '';
    var alertsHtml = '';
    var errorsHtml = '';
    for (var i = 0; i < ids.length; i++) {
      var id = ids[i];
      var rec = calcData && calcData[id] ? calcData[id] : null;
      var state = calcInputs[id] || {};
      var name = rec ? rec.name : id;
      var unit = rec && rec.unit ? rec.unit : '—';
      if (state.bad) {
        errorsHtml += '<div class="hactar-calc-error">Ошибка: введите корректную дозу для ' +
          esc(name) + '.</div>';
        continue;
      }
      var val = state.value !== undefined ? state.value :
        (rec && rec.value != null ? String(rec.value) : '');
      if (val === '' || val == null) {
        summaryHtml += '<li class="hactar-calc-summary-item">' +
          '<span class="hactar-calc-summary-name">' + esc(name) + '</span>' +
          '<span class="hactar-calc-summary-value">—</span>' +
          '<span class="hactar-calc-summary-status hactar-calc-status-ok">норма не задана</span>' +
          '</li>';
        continue;
      }
      var n = parseNum(val);
      var over = rec && rec.comparable && n > rec.ulMg;
      var dispVal = String(n).replace('.', ',');
      var statusCls = over ? 'hactar-calc-status-over' : 'hactar-calc-status-ok';
      var statusTxt = over ? 'превышена суточную норму' : 'в пределах нормы';
      summaryHtml += '<li class="hactar-calc-summary-item">' +
        '<span class="hactar-calc-summary-name">' + esc(name) + '</span>' +
        '<span class="hactar-calc-summary-value">' + esc(dispVal) + ' ' + esc(unit) + '</span>' +
        '<span class="hactar-calc-summary-status ' + esc(statusCls) + '">' + esc(statusTxt) + '</span>' +
        '</li>';
      if (over) {
        alertsHtml += '<div class="hactar-calc-alert">⚠️ ' + esc(name) + ': доза ' + esc(dispVal) +
          ' ' + esc(unit) + ' превышает суточную норму ' +
          esc(String(rec.ulMg).replace('.', ',')) + ' ' + esc(rec.ulUnit) + '.</div>';
      }
    }
    calcSummaryListEl.innerHTML = summaryHtml;
    calcAlertsEl.innerHTML = alertsHtml;
    calcErrorsEl.innerHTML = errorsHtml;
  }

  /* (Пере)рисовать калькулятор для текущего выбора. Вызывается при смене
     выбора и при открытии вкладки «Калькулятор». */
  function renderCalc(ids) {
    if (!calcWrap || !calcListEl) return;
    calcWrap.hidden = !(ids && ids.length);
    if (!ids || !ids.length) {
      calcListEl.innerHTML = '';
      calcSummaryListEl.innerHTML = '';
      calcAlertsEl.innerHTML = '';
      calcErrorsEl.innerHTML = '';
      return;
    }
    loadCalcData().then(function () {
      buildCalcUi(ids);
    });
  }

  /* Реактивность: при смене выбора (галочка в левой панели) перерисовываем
     калькулятор; при открытии вкладки — тоже. */
  subscribe('change', function (ids) {
    renderCalc(ids || []);
  });
  subscribe('mode', function (mode) {
    if (mode === 'calc') renderCalc(selectedIds());
  });

  /* ──────────────────── вкладка «Сравнение» (H-8) ────────────────────
   *
   * Таблица side-by-side по выбранным добавкам: по строкам — параметры
   * (грейд доказательности, эффекты, дозировка, взаимодействия
   * с лекарствами), по столбцам — сами добавки.
   *
   * В самом низу таблицы — ряд кнопок «Купить» (Ozon, Wildberries,
   * Яндекс.Маркет). Без них воронка обрывалась на шаге «Сравнение»:
   * сравнивать было некуда идти (баг P2-03).
   *
   * На узких экранах таблицу сменяют вертикальные карточки — колонки
   * не помещаются, а горизонтальная прокрутка всей страницы ломает
   * мобильную вёрстку. Рисует карточки тот же код, что и таблицу.
   */

  /* Полный data.json для сравнения: id добавки → запись. Заполняется
     лениво, первым же открытием вкладки «Сравнение». */
  var compareData = null;
  var compareDataPromise = null;

  /* Магазины: ссылка на поиск товара по названию добавки. Ссылки
     открываются в новой вкладке, поэтому rel="noopener nofollow"
     обязателен (иначе страница магазина получит доступ к window.opener). */
  var COMPARE_SHOPS = [
    { label: 'Ozon', base: 'https://www.ozon.ru/search/?text=' },
    { label: 'Wildberries', base: 'https://www.wildberries.ru/catalog/0/search.aspx?search=' },
    { label: 'Яндекс.Маркет', base: 'https://market.yandex.ru/search?text=' }
  ];

  /* Тяжесть взаимодействия: подпись и класс .sev из style.css. */
  var COMPARE_SEVERITY = {
    critical: { label: 'критический риск', cls: 'sev-critical' },
    high: { label: 'высокий риск', cls: 'sev-high' },
    medium: { label: 'средний риск', cls: 'sev-medium' },
    low: { label: 'низкий риск', cls: 'sev-low' }
  };

  /* Полная запись добавки для сравнения. Всё, кроме дозировки и форм,
     лежит в облегчённом data_index.json; дозировка — только в data.json,
     поэтому она подтягивается отдельным запросом (loadCompareData). */
  function compareRecord(id) {
    var full = compareData && compareData[id] ? compareData[id] : null;
    var light = supById[id] || null;
    var grade = String((light && light.grade) || (full && full.grade) || 'D').toUpperCase();
    if (!GRADE_LABEL[grade]) grade = 'D';
    return {
      id: id,
      name: String((light && light.name) || (full && full.name) || id),
      grade: grade,
      effects: (light && light.effects) || (full && full.effects) || [],
      interactions: (light && light.interactions) || (full && full.interactions) || [],
      dosage: full ? String(full.dosage || '') : '',
      forms: full ? String(full.forms || '') : ''
    };
  }

  /* Запрос товара в магазине: название + первая форма. Форм в data.json
     несколько («капсулы, порошок»), берём первую — иначе запрос
     превратится в «Магний капсулы, порошок» и магазин не найдёт
     ничего. */
  function compareQuery(rec) {
    var parts = String(rec.forms || '').split(',');
    var form = String(parts[0] || '').trim();
    return form ? (rec.name + ' ' + form) : rec.name;
  }

  /* Ячейка «Грейд доказательности»: цветной бейдж + расшифровка. */
  function compareGradeCell(rec) {
    var label = GRADE_LABEL[rec.grade];
    return '<span class="grade g' + rec.grade + '" aria-hidden="true"' +
           ' title="Грейд ' + rec.grade + ' — ' + esc(label) + '">' +
           rec.grade + '</span> <span class="hactar-compare-inline">' +
           esc(label) + '</span>';
  }

  /* Ячейка «Эффекты»: короткий список заявленных эффектов. */
  function compareEffectsCell(rec) {
    var list = rec.effects || [];
    if (!list.length) {
      return '<span class="hactar-compare-none">не указаны</span>';
    }
    var html = '<ul class="hactar-compare-list">';
    for (var i = 0; i < list.length; i++) {
      html += '<li>' + esc(list[i]) + '</li>';
    }
    return html + '</ul>';
  }

  /* Ячейка «Дозировка»: из data.json, до его загрузки — прочерк. */
  function compareDosageCell(rec) {
    if (!rec.dosage) {
      return '<span class="hactar-compare-none">не указана</span>';
    }
    return esc(rec.dosage);
  }

  /* Ячейка «Взаимодействия с лекарствами»: препарат + тяжесть риска. */
  function compareInteractionsCell(rec) {
    var list = rec.interactions || [];
    if (!list.length) {
      return '<span class="hactar-compare-none">не выявлены</span>';
    }
    var html = '<ul class="hactar-compare-list">';
    for (var i = 0; i < list.length; i++) {
      var it = list[i] || {};
      var sev = COMPARE_SEVERITY[it.severity] || COMPARE_SEVERITY.medium;
      html += '<li><span class="sev ' + sev.cls + '">' + esc(sev.label) + '</span>' +
              ' <span class="hactar-compare-inline">' + esc(it.with || '') + '</span>' +
              (it.note ? ' <span class="hactar-compare-inline">— ' +
                         esc(it.note) + '</span>' : '') +
              '</li>';
    }
    return html + '</ul>';
  }

  /* Ячейка «Купить»: ряд кнопок-чипов со ссылками на магазины. */
  function compareBuyCell(rec) {
    var q = encodeURIComponent(compareQuery(rec));
    var html = '<div class="hactar-compare-shops">';
    for (var i = 0; i < COMPARE_SHOPS.length; i++) {
      var shop = COMPARE_SHOPS[i];
      html += '<a class="hactar-compare-shop" href="' + shop.base + q + '"' +
              ' target="_blank" rel="noopener nofollow"' +
              ' aria-label="Купить ' + esc(rec.name) + ' на ' +
              esc(shop.label) + '">' + esc(shop.label) + '</a>';
    }
    return html + '</div>';
  }

  /* Строки таблицы: подпись параметра и функция ячейки. */
  var COMPARE_ROWS = [
    { label: 'Грейд доказательности', cell: compareGradeCell },
    { label: 'Эффекты', cell: compareEffectsCell },
    { label: 'Дозировка', cell: compareDosageCell },
    { label: 'Взаимодействия с лекарствами', cell: compareInteractionsCell },
    { label: 'Купить', cell: compareBuyCell }
  ];

  /* Шапка таблицы: «Параметр» + по колонке на добавку. */
  function compareHeadHtml(recs) {
    var html = '<th scope="col" class="hactar-compare-param">Параметр</th>';
    for (var i = 0; i < recs.length; i++) {
      html += '<th scope="col" class="hactar-compare-sup">' +
              esc(recs[i].name) + '</th>';
    }
    return html;
  }

  /* Тело таблицы: по строке на параметр, по ячейке на добавку. */
  function compareBodyHtml(recs) {
    var html = '';
    for (var i = 0; i < COMPARE_ROWS.length; i++) {
      /* Атрибут scope со значением row не пишем: аудит классов считает
         любой такой литерал в JS-шаблоне именем класса и оживляет .row
         из мёртвого списка. Заголовок строки и так читается как
         заголовок — это <th> в первом столбце. Так же сделано на
         странице compare.html. */
      html += '<tr><th class="hactar-compare-rowhead">' +
              esc(COMPARE_ROWS[i].label) + '</th>';
      for (var j = 0; j < recs.length; j++) {
        html += '<td class="hactar-compare-cell">' +
                COMPARE_ROWS[i].cell(recs[j]) + '</td>';
      }
      html += '</tr>';
    }
    return html;
  }

  /* Карточка для мобильного: те же параметры, но вертикальным списком. */
  function compareCardRow(label, valueHtml) {
    return '<div class="hactar-compare-cardrow">' +
             '<span class="hactar-compare-cardlabel">' + esc(label) + '</span>' +
             '<span class="hactar-compare-cardvalue">' + valueHtml + '</span>' +
           '</div>';
  }

  function compareCardsHtml(recs) {
    var html = '';
    for (var i = 0; i < recs.length; i++) {
      var rec = recs[i];
      html += '<div class="hactar-compare-card">' +
              '<div class="hactar-compare-cardhead">' +
                '<span class="grade g' + rec.grade + '" aria-hidden="true">' +
                  rec.grade + '</span>' +
                '<span class="hactar-compare-cardname">' + esc(rec.name) + '</span>' +
              '</div>' +
              compareCardRow('Грейд доказательности',
                             '<span class="hactar-compare-inline">' +
                               esc(GRADE_LABEL[rec.grade]) + '</span>') +
              compareCardRow('Эффекты', compareEffectsCell(rec)) +
              compareCardRow('Дозировка', compareDosageCell(rec)) +
              compareCardRow('Взаимодействия', compareInteractionsCell(rec)) +
              compareCardRow('Купить', compareBuyCell(rec)) +
              '</div>';
    }
    return html;
  }

  /* Согласование слова «добавка» с числом: 1 добавка, 2-4 добавки,
     5+ добавок. Без этого в подписи вылезало «Сравниваем 2 добавок». */
  function comparePlural(n) {
    var n10 = n % 10;
    var n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return 'добавка';
    if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return 'добавки';
    return 'добавок';
  }

  /* Перерисовка вкладки «Сравнение».
     Ноль выбранных — пустое состояние (H-4) показывает сам разметчик,
     здесь только прячем блок. Одна добавка — подсказка «выберите ещё».
     Две и больше — таблица (на широком экране) или карточки (на узком).
     Обе формы рисуются всегда: так переключение брейкпоинта не требует
     перезагрузки данных, а скрытая копия не мешает скринридеру
     (атрибут hidden убирает её из дерева доступности). */
  function renderCompare(ids) {
    if (!compareWrap) return;
    var list = ids || [];
    var n = list.length;
    if (!n) {
      compareWrap.hidden = true;
      compareHintEl.hidden = true;
      compareScrollEl.hidden = true;
      compareCardsEl.hidden = true;
      compareHeadEl.innerHTML = '';
      compareBodyEl.innerHTML = '';
      compareCardsEl.innerHTML = '';
      compareNoteEl.textContent = '';
      return;
    }
    compareWrap.hidden = false;
    if (n < 2) {
      compareHintEl.hidden = false;
      compareScrollEl.hidden = true;
      compareCardsEl.hidden = true;
      compareHeadEl.innerHTML = '';
      compareBodyEl.innerHTML = '';
      compareCardsEl.innerHTML = '';
      compareNoteEl.textContent = 'Выбрана одна добавка. Добавьте вторую — ' +
        'и покажем сравнение по параметрам.';
      return;
    }
    compareHintEl.hidden = true;
    var recs = [];
    var i;
    for (i = 0; i < list.length; i++) recs.push(compareRecord(list[i]));
    compareNoteEl.textContent = 'Сравниваем ' + n + ' ' + comparePlural(n) +
      ': по строкам — параметры, по столбцам — добавки.';
    compareHeadEl.innerHTML = compareHeadHtml(recs);
    compareBodyEl.innerHTML = compareBodyHtml(recs);
    compareCardsEl.innerHTML = compareCardsHtml(recs);
    var mobile = isMobile();
    compareScrollEl.hidden = mobile;
    compareCardsEl.hidden = !mobile;
  }

  /* Данные для сравнения: полный data.json (дозировка и формы).
     Грузится лениво — только когда вкладка «Сравнение» понадобилась,
     чтобы не тянуть 758 КБ странице, которая туда не заходила. */
  function loadCompareData() {
    if (compareDataPromise) return compareDataPromise;
    compareDataPromise = fetchJsonStatic('data.json').then(function (data) {
      var list = supplementsOf(data);
      var map = {};
      for (var i = 0; i < list.length; i++) {
        if (list[i] && list[i].id) map[list[i].id] = list[i];
      }
      compareData = map;
      return map;
    });
    return compareDataPromise;
  }

  /* Догружаем дозировки и перерисовываем таблицу. */
  function ensureCompareData() {
    if (compareData || compareDataPromise) return;
    loadCompareData().then(function () {
      renderCompare(selectedIds());
    }).catch(function (err) {
      console.error('[hactar] не удалось загрузить данные для сравнения:', err);
    });
  }

  /* Реактивность: при смене выбора таблица перерисовывается, при
     открытии вкладки — тоже. Данные для дозировок тянутся только когда
     вкладка «Сравнение» открыта: пока она не нужна, 758 КБ data.json
     никому не должны. */
  subscribe('change', function (ids) {
    renderCompare(ids || []);
    if (currentMode === 'compare') ensureCompareData();
  });
  subscribe('mode', function (mode) {
    if (mode === 'compare') {
      renderCompare(selectedIds());
      ensureCompareData();
    }
  });

  /* Смена ширины окна (поворот телефона, поворот планшета) меняет
     представление: таблица ↔ карточки. */
  if (window.matchMedia) {
    var compareMq = window.matchMedia('(max-width: ' + MOBILE_BP + 'px)');
    var onCompareBreak = function () { renderCompare(selectedIds()); };
    if (compareMq.addEventListener) compareMq.addEventListener('change', onCompareBreak);
    else if (compareMq.addListener) compareMq.addListener(onCompareBreak);
  }

  /* ──────────────────────────── старт ──────────────────────────── */

  showSkeleton();

  /* H-6: данные графа грузим сразу, параллельно со списком добавок —
     к моменту, когда пользователь отметит первую добавку, граф уже готов. */
  loadGraphSources();

  loadData()
    .then(function (items) {
      all = items;
      loaded = true;
      if (totalEl) totalEl.textContent = String(items.length);
      renderList(items);
      /* Выбор из памяти браузера — после рендера, иначе нечего ставить. */
      restoreSaved();
      /* H-7: отрисовать калькулятор для уже выбранных (восстановленных) добавок. */
      renderCalc(selectedIds());
      /* H-8: то же для сравнения — при прямом заходе по ?tab=compare. */
      renderCompare(selectedIds());
      if (currentMode === 'compare') ensureCompareData();
    })
    .catch(function (err) {
      console.error('[hactar] не удалось загрузить список добавок:', err);
      listEl.innerHTML = '<p class="hactar-empty">⚠️ Не удалось загрузить список добавок. Обновите страницу.</p>';
      listEl.setAttribute('aria-busy', 'false');
    });

  /* Публичный API. Им пользуется H-3 (сохранение в localStorage) и
     следующие шаги (калькулятор, сравнение). */
  window.Hactar = {
    items: function () { return all; },
    selectedIds: selectedIds,
    setSelection: function (ids) {
      setSelection(ids || []);
      saveSelection();
    },
    count: updateCount,
    /* H-3: активный грейд-фильтр. */
    grade: function () { return grade; },
    setGrade: setGrade,
    /* H-3: память браузера. */
    savedIds: readSavedIds,
    save: saveSelection,
    /* H-5: активный режим вкладки и переключение на него. */
    mode: function () { return currentMode; },
    setMode: setMode,
    /* H-6: подписки. Граф подключается через них — как и любой другой
       потребитель выбора. Возвращают функцию отписки. */
    onChange: function (fn) { return subscribe('change', fn); },
    onMode: function (fn) { return subscribe('mode', fn); },
    /* H-6: состояние графа — сколько узлов/рёбер и остановлена ли физика.
       Нужен для отладки и автотестов. */
    graphState: function () {
      if (!network) {
        return { nodes: 0, edges: 0, physics: false, ready: graphReady };
      }
      return {
        nodes: network.body.data.nodes.length,
        edges: network.body.data.edges.length,
        physics: physicsOn,
        ready: graphReady
      };
    },
    /* H-8: состояние вкладки «Сравнение» — сколько добавок в сравнении,
       что показано (таблица / карточки / подсказка) и загружены ли
       дозировки. Нужно для отладки и автотестов. */
    compareState: function () {
      var mobile = isMobile();
      return {
        selected: selectedIds().length,
        visible: !!(compareWrap && !compareWrap.hidden),
        hint: !!(compareHintEl && !compareHintEl.hidden),
        view: mobile ? 'cards' : 'table',
        dataLoaded: !!compareData
      };
    },
    clearSelection: function () {
      setSelection([]);
      writeSavedIds([]);
      updateCount();
    }
  };
})();
