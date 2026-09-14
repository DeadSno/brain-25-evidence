/* v2.7 PWA: регистрация SW + бейдж «офлайн-режим». */
(function () {
  var badge = null;

  function showBadge() {
    if (badge) return;
    badge = document.createElement('div');
    badge.id = 'pwaOfflineBadge';
    badge.setAttribute('role', 'status');
    badge.textContent = '📴 Офлайн-режим: показываем данные из кэша';
    var st = badge.style;
    st.position = 'fixed';
    st.bottom = '16px';
    st.left = '16px';
    st.zIndex = '2000';
    st.background = '#1c1c1e';
    st.color = '#f5f5f7';
    st.border = '1px solid #f1c40f';
    st.padding = '8px 14px';
    st.borderRadius = '999px';
    st.fontSize = '.82rem';
    st.fontWeight = '600';
    st.boxShadow = '0 4px 14px rgba(0,0,0,.35)';
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
      navigator.serviceWorker.register('./sw.js').catch(function (err) {
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