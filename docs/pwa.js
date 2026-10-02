/* v2.8 PWA: регистрация SW + бейдж «офлайн-режим». */
(function () {
  var badge = null;

  /* v2.8: pwa.js подключается и из корня (./pwa.js), и со страниц /sup/*.html
     (../pwa.js). Регистрировать надо sw.js рядом со скриптом, а не
     относительно страницы: на /sup/kreatin.html './sw.js' резолвился
     в /sup/sw.js → 404, и офлайн-режим на этих страницах не работал.
     URL запоминаем сразу на верхнем уровне: document.currentScript валиден
     только во время синхронного выполнения скрипта, а в обработчике 'load'
     он уже равен null. */
  var PWA_BASE = (document.currentScript && document.currentScript.src) || location.href;

  function showBadge() {
    if (badge) return;
    badge = document.createElement('div');
    badge.id = 'pwaOfflineBadge';
    badge.setAttribute('role', 'status');
    badge.setAttribute('aria-live', 'polite');
    badge.textContent = '📴 Офлайн-режим: данные могут быть устаревшими';
    var st = badge.style;
    st.position = 'fixed';
    /* v49: bottom считается от safe-area. На iPhone с home indicator плашка
       bottom:16px наезжала бы на индикатор жестов — ровно то, что мы уже
       починили для футера и модалки. */
    st.bottom = 'calc(16px + env(safe-area-inset-bottom, 0px))';
    st.left = 'calc(16px + env(safe-area-inset-left, 0px))';
    st.right = '16px';
    st.zIndex = '2000';
    st.background = '#1c1c1e';
    st.color = '#f5f5f7';
    st.border = '1px solid #f1c40f';
    st.padding = '8px 14px';
    st.borderRadius = '999px';
    st.fontSize = '.82rem';
    st.fontWeight = '600';
    st.boxShadow = '0 4px 14px rgba(0,0,0,.35)';
    st.maxWidth = 'calc(100% - 32px)';
    st.webkitTapHighlightColor = 'transparent';
    document.body.appendChild(badge);
  }

  function hideBadge() {
    if (badge) {
      badge.remove();
      badge = null;
    }
  }

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register(new URL('sw.js', PWA_BASE).href).catch(function (err) {
        console.warn('[pwa] service worker не зарегистрирован:', err.message || err);
      });
    });
    navigator.serviceWorker.addEventListener('message', function (event) {
      if (event.data && event.data.type === 'offline') showBadge();
    });
  }

  window.addEventListener('offline', showBadge);
  window.addEventListener('online', hideBadge);
  if (!navigator.onLine) showBadge();
})();