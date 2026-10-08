/* v5.6.2: cookie-баннер согласия на Яндекс.Метрику (счётчик 112465667).
 *
 * Правило владельца: до нажатия «Принять» НИ ОДНОГО запроса к mc.yandex.ru.
 * Сам tag.js инжектируется только внутри loadMetrika() (docs/metrika.js),
 * поэтому загрузка этого файла сетевую активность не создаёт.
 *
 * Состояние согласия — localStorage['cookie-consent']:
 *   'accepted' → Метрика грузится сразу, баннер не показывается;
 *   'rejected' → баннер не показывается, Метрика не грузится никогда;
 *   отсутствует → показывается баннер, выбора ещё не сделано.
 *
 * Разметка баннера (#cookieBanner) лежит в конце <body> каждой страницы
 * (144 шт., кроме offline.html — она сознательно без внешних скриптов).
 */
function initCookieBanner() {
  var consent = null;
  try { consent = localStorage.getItem('cookie-consent'); } catch (e) {}

  if (consent === 'accepted') {
    // typeof-guard: если metrika.js не загрузился, страница не должна
    // упасть с ReferenceError на каждом просмотре.
    if (typeof loadMetrika === 'function') loadMetrika();
    return;
  }
  if (consent === 'rejected') return;

  var banner = document.getElementById('cookieBanner');
  if (!banner) return;
  banner.hidden = false;

  var accept = document.getElementById('cookieAccept');
  var reject = document.getElementById('cookieReject');
  if (!accept || !reject) return;

  accept.addEventListener('click', function () {
    try { localStorage.setItem('cookie-consent', 'accepted'); } catch (e) {}
    banner.hidden = true;
    if (typeof loadMetrika === 'function') loadMetrika();
  });

  reject.addEventListener('click', function () {
    try { localStorage.setItem('cookie-consent', 'rejected'); } catch (e) {}
    banner.hidden = true;
  });
}
