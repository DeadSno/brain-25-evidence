/* Project Hactar — список добавок в левой панели (H-2) + фильтры,
 * сохранение выбора и полная ширина страницы (H-3).
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
 *   8. кнопка «Очистить всё» снимает все галочки и чистит хранилище.
 *
 * Связка поиска и грейда: работают ВМЕСТЕ, а не по очереди. Введён
 * «Магний» + выбран грейд «D» -> остаётся только Магний (у него грейд D).
 *
 * Чего здесь НЕТ сознательно: логика табов и калькулятора не трогается,
 * расчёта доз и сравнения тоже — это следующие шаги Project Hactar.
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

  var listEl = document.getElementById('hactarList');
  var emptyEl = document.getElementById('hactarEmpty');
  var searchEl = document.getElementById('hactarSearch');
  var countEl = document.getElementById('hactarCount');
  var totalEl = document.getElementById('hactarTotal');
  var sidebar = document.getElementById('hactarSidebar');
  var chipsEl = document.getElementById('hactarChips');
  var clearBtn = document.getElementById('hactarClearAll');

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

  /* Возвращает число выбранных — этим же значением пользуется публичный
     API (window.Hactar.count()), поэтому возвращаем n, а не undefined. */
  function updateCount() {
    var boxes = listEl.querySelectorAll('.hactar-check');
    var n = 0;
    for (var i = 0; i < boxes.length; i++) {
      if (boxes[i].checked) n++;
    }
    if (countEl) countEl.textContent = String(n);
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
    updateCount();
    saveSelection();
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
    clearSelection: function () {
      setSelection([]);
      writeSavedIds([]);
      updateCount();
    }
  };
})();
