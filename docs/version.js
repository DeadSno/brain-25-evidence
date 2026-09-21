// Загружает version.json, подставляет в [data-version] и <title>.
// После подгрузки дёргает applyFilters (если есть) — чтобы карточки
// перерисовались с актуальной APP_VERSION.data.
fetch('version.json?ts=' + Date.now())
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