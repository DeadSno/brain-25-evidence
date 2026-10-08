/* v5.6.2: Яндекс.Метрика, счётчик 112465667.
 *
 * ЕДИНСТВЕННАЯ точка загрузки tag.js. Вызывается только из
 * docs/cookie-banner.js после нажатия «Принять» (или при ранее данном
 * согласии) — сама по себе загрузка этого файла сетевых запросов
 * не делает.
 *
 * Включено по решению владельца: вебвизор (webvisor), карта кликов
 * (clickmap), отслеживание ссылок (trackLinks), точный показатель отказов
 * (accurateTrackBounce).
 *
 * Чего здесь сознательно НЕТ: <noscript><img src="https://mc.yandex.ru/
 * watch/112465667">. Пиксель в noscript загружается браузером без JS и
 * до всякого согласия — это ровно то, что запрещено правилом приватности.
 * Пользователи без JS просто не попадают в статистику.
 */
function loadMetrika() {
  // Счётчик уже инициализирован tag.js — повторный init не нужен.
  if (window.yaCounter112465667) return;
  // Загружается прямо сейчас (медленная сеть, двойной вызов) — второй раз
  // тег не цепляем.
  if (window.__metrikaLoading) return;
  window.__metrikaLoading = true;

  // Стаб ym: копит вызовы, пока tag.js не загрузится и не переопределит его.
  window.ym = window.ym || function () {
    (window.ym.a = window.ym.a || []).push(arguments);
  };
  window.ym.l = 1 * new Date();

  var s = document.createElement('script');
  s.src = 'https://mc.yandex.ru/metrika/tag.js';
  s.async = true;
  document.head.appendChild(s);

  ym(112465667, 'init', {
    clickmap: true,           // карта кликов
    trackLinks: true,         // переходы по внешним ссылкам
    accurateTrackBounce: true,
    webvisor: true            // вебвизор (+ карта скроллов)
  });
}
