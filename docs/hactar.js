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
 *
 * Связка поиска и грейда: работают ВМЕСТЕ, а не по очереди. Введён
 * «Магний» + выбран грейд «D» -> остаётся только Магний (у него грейд D).
 *
 * Чего здесь НЕТ сознательно: расчёта доз и сравнения — это следующие
 * шаги Project Hactar. Логика графа не трогается.
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
  /* H-4: пустое состояние и заглушка — по одному на каждый таб. */
  var emptyStates = document.querySelectorAll('.hactar-empty-state');
  var stubs = document.querySelectorAll('.hactar-stub');
  var emptyBtns = document.querySelectorAll('.hactar-empty-btn');

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
    for (var i = 0; i < items.length; i++) html += cardHtml(items[i]);
    listEl.innerHTML = html;
    listEl.setAttribute('aria-busy', 'false');
    rows = Array.prototype.slice.call(listEl.querySelectorAll('.hactar-row'));
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

  /* H-4: пустое состояние против заглушки.
     Пока не выбрана ни одна добавка — показываем иллюстрацию с подсказкой
     и кнопкой «Выбрать добавки». Как только что-то выбрано — вместо этого
     показываем заглушку «Здесь будет <режим>. Выбрано добавок: N»
     (сам контент таба ещё не реализован).
     Состояние живёт в атрибуте hidden, а не в классе: [hidden] — это
     единственный способ спрятать блок, о котором не знает CSS. */
  function updateEmptyState(n) {
    var i;
    var label;
    var empty = (n === 0);
    for (i = 0; i < emptyStates.length; i++) {
      emptyStates[i].hidden = !empty;
    }
    for (i = 0; i < stubs.length; i++) {
      stubs[i].hidden = empty;
      label = stubs[i].getAttribute('data-stub-label') || '';
      stubs[i].textContent = 'Здесь будет ' + label + '. Выбрано добавок: ' + n;
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

  /* ──────────────────────────── старт ──────────────────────────── */

  showSkeleton();

  loadData()
    .then(function (items) {
      all = items;
      loaded = true;
      if (totalEl) totalEl.textContent = String(items.length);
      renderList(items);
      /* Выбор из памяти браузера — после рендера, иначе нечего ставить. */
      restoreSaved();
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
    clearSelection: function () {
      setSelection([]);
      writeSavedIds([]);
      updateCount();
    }
  };
})();
