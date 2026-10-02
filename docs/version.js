// Загружает version.json, подставляет в [data-version] и <title>.
// После подгрузки дёргает applyFilters (если есть) — чтобы карточки
// перерисовались с актуальной APP_VERSION.data.

// v51: адрес version.json считается ОТ САМОГО СКРИПТА, а не от документа.
// Раньше был fetch('version.json?...') — относительный URL, который браузер
// резолвит от документа. На 12 страницах корень документа совпадает с
// папкой скрипта, и всё работало; на 5 страницах sup/*.html документ в /sup/,
// а скрипт подключён как ../version.js — запрос уходил на /sup/version.json
// и получал 404, который молча уходил в catch(). Версия в <title> и
// [data-version] на этих страницах не подставлялась вообще.
//
// document.currentScript доступен на верхнем уровне классического скрипта
// (defer не мешает) и равен null только в модулях и внутри колбэков —
// на этот случай есть запасной document.baseURI (старое поведение).
var VERSION_JSON_URL = (function () {
  var scriptEl = document.currentScript;
  var base = (scriptEl && scriptEl.src) ? scriptEl.src : document.baseURI;
  // 'version.json' рядом с 'version.js' в корне сайта: query у src отбрасывается,
  // так что ?v=NNN на подключении ничего не ломает.
  return new URL('version.json', base).href;
})();

fetch(VERSION_JSON_URL + '?ts=' + Date.now())
  .then(function (r) {
    if (!r.ok) throw new Error('version.json HTTP ' + r.status);
    return r.json();
  })
  .then(function (v) {
    window.APP_VERSION = v;
    document.querySelectorAll('[data-version]').forEach(function (el) {
      var key = el.dataset.version;
      if (v[key] != null) el.textContent = v[key];
    });
    if (v.app) {
      document.title = document.title.replace(/v\d+(\.\d+)+[-\w.]*/, 'v' + v.app);
    }
    // Перерисовать карточки с новой датой
    if (typeof applyFilters === 'function' && window.supplements && supplements.length) {
      try { applyFilters(); } catch (e) { console.warn('[version] applyFilters:', e); }
    }
  })
  .catch(function (err) {
    console.warn('[version] не загрузился version.json:', err);
  });