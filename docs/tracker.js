/* === v2.7 Part A: ТРЕКЕР ПРИЁМА (tracker.js) === */
/* Изолирован: не трогает script.js / style.css / index.html (кроме строки подключения) */
(function () {
  'use strict';

  var TRACKER_VERSION = '2.7-a';
  var STORAGE_KEY = 'myCourse';
  var DEFAULT_DAYS = 30;
  var _supplementsCache = null;

  function fetchSupplements() {
    if (_supplementsCache) return Promise.resolve(_supplementsCache);
    return fetch('data.json?ts=' + Date.now())
      .then(function (r) { return r.json(); })
      .then(function (d) { _supplementsCache = d; return d; })
      .catch(function () { return []; });
  }

  function findSup(id) {
    if (!_supplementsCache) return null;
    return _supplementsCache.find(function (s) { return s.id === id; }) || null;
  }

  function findSupByName(name) {
    if (!_supplementsCache) return null;
    return _supplementsCache.find(function (s) { return s.name === name; }) || null;
  }

  /* ================================================================
     A1. localStorage-схема myCourse + гард (как у favs)
     myCourse[id] = { start: ISO, days: int, taken: [ISO], note: str }
     ================================================================ */
  function getMyCourses() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return {};
      var parsed = JSON.parse(raw);
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        console.warn('[tracker] myCourse: невалидная структура, сброс');
        localStorage.removeItem(STORAGE_KEY);
        return {};
      }
      var cleaned = {};
      for (var id in parsed) {
        var c = parsed[id];
        if (!c || typeof c !== 'object' || Array.isArray(c)) {
          console.warn('[tracker] myCourse[' + id + ']: невалидный объект, пропуск');
          continue;
        }
        if (typeof c.start !== 'string' || isNaN(Date.parse(c.start))) {
          console.warn('[tracker] myCourse[' + id + ']: невалидный start, пропуск');
          continue;
        }
        if (typeof c.days !== 'number' || c.days < 1) {
          console.warn('[tracker] myCourse[' + id + ']: невалидные days, пропуск');
          continue;
        }
        if (!Array.isArray(c.taken)) c.taken = [];
        if (typeof c.note !== 'string') c.note = '';
        cleaned[id] = c;
      }
      if (Object.keys(cleaned).length !== Object.keys(parsed).length) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(cleaned));
      }
      return cleaned;
    } catch (e) {
      console.warn('[tracker] myCourse: ошибка чтения, сброс', e);
      localStorage.removeItem(STORAGE_KEY);
      return {};
    }
  }

  function saveMyCourses(obj) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(obj));
  }

  function isCourseActive(course) {
    if (!course) return false;
    return course.taken.length < course.days;
  }

  function isCourseDone(course) {
    return course && course.taken.length >= course.days;
  }

  /* ================================================================
     A2. Кнопка «📅 В мой курс» в модалке — MutationObserver
     Не трогает script.js. Реагирует на смену style.display у #modalOverlay.
     ================================================================ */
  function injectCourseButton() {
    var modalBody = document.getElementById('modalBody');
    if (!modalBody || !modalBody.innerHTML) return;

    // Уже есть кнопка — не дублируем
    if (modalBody.querySelector('[data-tracker-btn]')) return;

    // Определяем id добавки из хэша URL (openModal ставит #sup=<id>)
    var hash = decodeURIComponent((location.hash || '').replace('#sup=', ''));
    if (!hash) return;
    var sup = findSup(hash);
    if (!sup) return;

    // Кнопка «📅 В мой курс»
    var btn = document.createElement('button');
    btn.className = 'favFilter';
    btn.dataset.trackerBtn = sup.id;
    btn.style.marginTop = '0.5rem';
    btn.style.marginRight = '0.5rem';

    var courses = getMyCourses();
    var existing = courses[sup.id];
    if (existing && isCourseActive(existing)) {
      btn.textContent = '📅 В курсе (' + existing.taken.length + '/' + existing.days + ')';
      btn.disabled = false;
    } else if (existing && isCourseDone(existing)) {
      btn.textContent = '✅ Курс завершён';
      btn.disabled = true;
    } else {
      btn.textContent = '📅 В мой курс';
      btn.disabled = false;
    }

    btn.addEventListener('click', function () {
      var courses = getMyCourses();
      var dosage = sup.dosage || '';
      var course = courses[sup.id];
      if (!course) {
        course = {
          start: new Date().toISOString(),
          days: DEFAULT_DAYS,
          taken: [],
          note: dosage ? 'Доза: ' + dosage : ''
        };
        courses[sup.id] = course;
      }
      course.taken.push(new Date().toISOString());
      saveMyCourses(courses);
      btn.textContent = '📅 В курсе (' + course.taken.length + '/' + course.days + ')';
      window.dispatchEvent(new Event('courseUpdated'));
    });

    // Приватность-пометка
    var privacy = document.createElement('div');
    privacy.style.fontSize = '0.75rem';
    privacy.style.opacity = '0.6';
    privacy.style.marginTop = '0.25rem';
    privacy.textContent = '\u{1F512} Данные хранятся только в вашем браузере, никуда не отправляются';

    // Вставляем перед ссылкой «Нашли неточность?» или в конец
    var issueLink = modalBody.querySelector('a[href*="issues/new"]');
    if (issueLink && issueLink.parentElement) {
      issueLink.parentElement.insertBefore(btn, issueLink);
      issueLink.parentElement.insertBefore(privacy, issueLink);
    } else {
      modalBody.appendChild(btn);
      modalBody.appendChild(privacy);
    }
  }

  function setupModalObserver() {
    var overlay = document.getElementById('modalOverlay');
    if (!overlay) return;
    var observer = new MutationObserver(function () {
      if (overlay.style.display === 'flex') {
        setTimeout(injectCourseButton, 100);
      }
    });
    observer.observe(overlay, { attributes: true, attributeFilter: ['style'] });
  }

  /* ================================================================
     A3. Секция «Мои добавки» на главной — DOM-контейнер из JS
     ================================================================ */
  function createMyCoursesSection() {
    var section = document.createElement('section');
    section.id = 'myCoursesSection';
    section.style.cssText = 'background:var(--card-bg);padding:1.2rem 1.5rem;border-radius:12px;border:1px solid var(--border);display:none;';
    return section;
  }

  function renderMyCourses() {
    var courses = getMyCourses();
    var ids = Object.keys(courses);
    var section = document.getElementById('myCoursesSection');
    if (!section) return;

    if (ids.length === 0) {
      section.style.display = 'none';
      return;
    }

    section.style.display = '';

    var html = '<h2>\u{1F4C5} Мои добавки</h2>';
    ids.forEach(function (id) {
      var c = courses[id];
      var sup = findSup(id);
      var name = sup ? sup.name : id;
      var pct = Math.min(100, Math.round((c.taken.length / c.days) * 100));
      var done = isCourseDone(c);
      var statusColor = done ? '#2ecc71' : '#3498db';

      html += '<div class="card" style="margin-bottom:0.8rem;padding:1rem;border-left:4px solid ' + statusColor + '">';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem">';
      html += '<div>';
      html += '<b>' + name + '</b>';
      if (c.note) html += ' <span style="font-size:.8rem;opacity:.7">(' + c.note + ')</span>';
      html += ' <span style="font-size:.8rem;opacity:.6">с ' + c.start.slice(0, 10) + '</span>';
      html += '</div>';
      html += '<div style="display:flex;gap:0.4rem;flex-wrap:wrap">';

      if (!done) {
        html += '<button class="favFilter tracker-take" data-tracker-take="' + id + '">+ Принял</button>';
      }
      html += '<button class="favFilter tracker-remove" data-tracker-remove="' + id + '">убрать</button>';
      html += '</div></div>';

      // Прогресс-бар
      html += '<div style="background:rgba(128,128,128,.2);border-radius:6px;height:8px;margin-top:0.5rem;overflow:hidden">';
      html += '<div style="width:' + pct + '%;height:100%;background:' + statusColor + ';border-radius:6px;transition:width .3s"></div>';
      html += '</div>';
      html += '<div style="font-size:.8rem;margin-top:0.3rem;opacity:.8">' + c.taken.length + '/' + c.days +
        (done ? ' — курс завершён \u2705' : ' (' + pct + '%)') + '</div>';

      html += '</div>';
    });

    section.innerHTML = html;

    // Обработчики кнопок
    section.querySelectorAll('[data-tracker-take]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var courses = getMyCourses();
        var id = btn.dataset.trackerTake;
        var c = courses[id];
        if (!c) return;
        c.taken.push(new Date().toISOString());
        saveMyCourses(courses);
        renderMyCourses();
        window.dispatchEvent(new Event('courseUpdated'));
      });
    });

    section.querySelectorAll('[data-tracker-remove]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var courses = getMyCourses();
        var id = btn.dataset.trackerRemove;
        delete courses[id];
        saveMyCourses(courses);
        renderMyCourses();
        window.dispatchEvent(new Event('courseUpdated'));
      });
    });
  }

  function injectMyCoursesSection() {
    if (document.getElementById('myCoursesSection')) {
      renderMyCourses();
      return;
    }
    var section = createMyCoursesSection();
    var chartSection = document.getElementById('chartSection');
    if (chartSection && chartSection.parentElement) {
      chartSection.parentElement.insertBefore(section, chartSection);
    } else {
      var footer = document.querySelector('footer');
      if (footer) {
        footer.parentElement.insertBefore(section, footer);
      } else {
        document.body.appendChild(section);
      }
    }
    renderMyCourses();
  }

  /* ================================================================
     A4. Инициализация — загружаем data.json, рендерим, вешаем observer
     ================================================================ */
  function init() {
    injectMyCoursesSection();
    setupModalObserver();
    window.addEventListener('courseUpdated', function () {
      renderMyCourses();
    });
  }

  function boot() {
    fetchSupplements().then(function () { init(); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
