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

  /* v5.6.1: баннер показывается ТОЛЬКО при реальном офлайне.
     Раньше pwa.js реагировал и на сообщение service worker'а
     ({type:'offline'}), и sw.js слал его из двух мест — при упавшем
     fetch данных (строка 206) и при упавшем запросе статики (строка 274).
     Но эти catch срабатывают не только без сети: тот же путь даёт любой
     сетевой сбой одного запроса — 404 постороннего файла, таймаут
     опроса data.json с cache:'no-store', отказ CORS. Плашка «Офлайн-режим:
     данные могут быть устаревшими» появлялась при полностью рабочей сети,
     а по навигации online её никто не гасил, если браузер не послал
     событие online.

     Теперь признак один и проверяемый: navigator.onLine === false.
     События online/offline остались — они и меняют состояние, но решает
     не сообщение, а факт. Автоскрытия через 5 секунд нет намеренно:
     офлайн не проходит сам, и плашка, исчезнувшая без причины, вводила
     бы в заблуждение сильнее, чем её отсутствие. */
  function isReallyOffline() {
    return navigator.onLine === false;
  }

  function showBadge() {
    if (badge) return;
    if (!isReallyOffline()) return;      // ложное срабатывание от sw.js
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

  /* События остались, но теперь решает navigator.onLine, а не факт
     события: событие offline может прийти при сбое одного запроса,
     и тогда navigator.onLine по-прежнему true. */
  window.addEventListener('offline', function () {
    if (isReallyOffline()) showBadge();
  });
  window.addEventListener('online', function () {
    // Гасим по факту, а не по факту события: событие online может не прийти,
    // если вкладка была свёрнута, тогда как navigator.onLine уже true.
    if (!isReallyOffline()) hideBadge();
  });
  if (isReallyOffline()) showBadge();
})();