// Загружает docs/version.json и подставляет в элементы [data-version="..."].
// Плюс обновляет <title>, если там есть паттерн vX.Y(.Z).
fetch('version.json')
  .then(r => {
    if (!r.ok) throw new Error('version.json HTTP ' + r.status);
    return r.json();
  })
  .then(v => {
    window.APP_VERSION = v;
    document.querySelectorAll('[data-version]').forEach(el => {
      const key = el.dataset.version;
      if (v[key]) el.textContent = v[key];
    });
    if (v.app) {
      document.title = document.title.replace(/v\d+(\.\d+)+[-\w.]*/, 'v' + v.app);
    }
  })
  .catch(err => console.warn('[version] не загрузился version.json:', err));
