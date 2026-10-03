// Форсируем активацию новой версии сразу
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

/* PWA: cache-first для статики, network-first для data*.json.
   Install через поштучный cache.add().catch() — один missing файл
   не валит всю установку. Бамп CACHE_VERSION при изменении STATIC_ASSETS.

   v45: тач-таргеты 44px, шрифт полей 16px.
   v46: регресс звезды (.cat), viewport-fit=cover, safe-area, tap-highlight.
   v69: Шаг 7 — токены радиусов и теней в style.css (--radius-*,
        --shadow-*). Пиксели не сменились: токен объявлен значением того же
        литерала, который заменил.
   v70: Шаг 9 — токены межстрочного (--lh-tight/normal/loose).
        Покрытие 19 из 46 вхождений; значения вне шкалы оставлены
        литералами, потому что округление сдвинуло бы высоту строки.
   v71: Шаг 8 (этап 2) — токены --border-hover и --accent-hover.
        Пиксели не сменились: первый объявлен одним значением для
        обеих тем, второй заменил литерал на тождественный. Токены
        --info, --warn, --error НЕ применены: литералы лежат в
        правилах без указания темы, а значение токена различается
        по веткам, и подстановка меняла картинку в тёмной теме.
   v72: Шаг 8 завершён. Применено 3 токена из 5: --border-hover,
        --accent-hover, --accent-2 (тёмная ветка, #8ecbff).
        --info, --warn, --error отложены в v5.1.7: литералы лежат
        в правилах без указания темы, а ветки токена различаются.
   v47: safe-area для #modal, массовые тап-таргеты 44px, иконки atlas, theme-color.
   v48: порог 44px только для интерактивных .chip (+min-width по WCAG 2.5.5).
   v49: офлайн без подмены контента + 3 страницы в precache + data_index.json.
   v50: cache.match без ignoreSearch — ?v=NNN bust-ит кэш. ignoreSearch остался
        только как офлайн-страховка в ветке catch.
   v51: version.js считает адрес version.json от URL скрипта, а не от
        документа — на sup/*.html больше не 404 (было 5 страниц).
   v51: version.js считает адрес version.json от URL скрипта, а не от
        документа — на sup/*.html больше не 404 (было 5 страниц).

   v63: 33 правила sup/* вынесены из локальных <style> пяти страниц
        в style.css. Селекторы .verdict/.tag/.grade-badge ограничены
        .sup-wrap, чтобы не задеть trends/map/calculator.

   С v50 query-версия в <link href="style.css?v=NNN"> bust-ит кэш: точный
   cache.match идёт ПЕРВЫМ. ignoreSearch остался только офлайн-страховкой
   (cacheFirstForStatic, ветка catch) — там он нужен, потому что precache
   кладёт './style.css' без версии, а страницы просят 'style.css?v=NNN'. */

var CACHE_VERSION = 'v72';
var CACHE_STATIC = CACHE_VERSION + '-static';
var CACHE_DATA = CACHE_VERSION + '-data';

/* GitHub Pages кладёт сайт в /brain-25-evidence/, поэтому сравниваем по хвосту
   пути, а не по имени файла. data_index.json тоже идёт сюда: раньше он уходил в
   cacheFirstForStatic и при отказе получал HTML вместо JSON, r.json() падал, и
   boot показывал «не загрузились данные» даже когда файл был на диске.
   Именно /^data(_index)?\.json$/ — data_ma_timeline.json и data_price_history.json
   под это НЕ подходят (там после /data идёт _ma_timeline / _price_history) и
   остаются в статике, как и раньше. */
var DATA_RE = /\/data(_index)?\.json$/;

/* Главная — единственный допустимый fallback для навигации на корень.
   Раньше FALLBACK_HTML подставлялся ЛЮБОМУ упавшему GET, из-за чего офлайн
   на graph.html показывал главную страницу по URL graph.html со статусом 200. */
var INDEX_URL = './index.html';
var OFFLINE_URL = './offline.html';

var STATIC_ASSETS = [
  './index.html',
  './calculator.html',
  './map.html',
  './interactions.html',
  './atlas.html',
  './trends.html',
  './methodology.html',
  './faq.html',
  './glossary.html',
  './feedback.html',
  './graph.html',
  './support.html',
  './offline.html',
  './manifest.webmanifest',
  './pwa.js',
  './version.js',
  './script.js',
  './style.css',
  './effect_tags.json',
  './effect_labels.json',
  './sup/kreatin.html',
  './sup/magniy.html',
  './sup/omega-3.html',
  './sup/paba.html',
  './sup/vitamin-d.html',
  './icons/192.png',
  './icons/512.png',
  './share.js?v=1'];

function notifyOffline() {
  self.clients.matchAll().then(function (clients) {
    clients.forEach(function (c) { c.postMessage({ type: 'offline' }); });
  });
}

/* Ключ кэша данных: путь без query. Скрипты грузят данные как
   data_index.json?ts=<Date.now()>, поэтому search надо срезать, иначе каждый
   вызов создавал бы новую запись кэша. */
function dataCacheKey(req) {
  var u = new URL(req.url);
  u.search = '';
  return u.href;
}

async function networkFirstForData(req) {
  var cache = await caches.open(CACHE_DATA);
  /* v49: ключ берётся из САМОГО запроса. Раньше здесь жёстко стояло
     './data.json' и для cache.put, и для cache.match — и как только в эту
     ветку начали бы попадать и data.json, и data_index.json, второй запрос
     перезаписал бы кэш data.json содержимым data_index.json. */
  var key = dataCacheKey(req);
  try {
    var resp = await fetch(req, { cache: 'no-store' });
    if (resp && resp.ok) {
      cache.put(key, resp.clone());
      return resp;
    }
    throw new Error('data not 200');
  } catch (err) {
    notifyOffline();
    var cached = await cache.match(key);
    if (cached) return cached;
    /* Оба файла — JSON-массивы, поэтому пустой массив остаётся валидным ответом
       для обоих: index.html на [] показывает честное пустое состояние
       («ничего не найдено» + сброс фильтров), а не падает.

       Статус здесь ИМЕННО 200, и это не опечатка. script.js:180 делает
       `if (!r.ok) throw`, поэтому 503 приводил бы к тому, что тело `[]` вообще
       не парсится, d.status === 'rejected' и пользователь видит «Не удалось
       загрузить данные» — то есть ХУЖЕ, чем было до v49. Пустой результат —
       валидный ответ, а не ошибка; observability даёт заголовок x-fallback. */
    return new Response('[]', {
      status: 200,
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'x-fallback': 'empty' }
    });
  }
}

/* Ключ кэша для статики. Различаем два вида query-строки:

   ?v=NNN  — номер версии файла. Значимый: style.css?v=392 и style.css?v=391 —
             разные файлы, и бамп ?v= должен bust-ить кэш (иначе правки CSS
             не доходят до пользователей, и приходится вручную бампить
             CACHE_VERSION — три раунда подряд так и вышло).

   ?ts=<Date.now()> / ?_=<Date.now()> — АНТИХЕШ-метка времени, добавляется
             скриптами при каждой загрузке (script.js: fetch(url + '?ts=' +
             Date.now()), version.js: '?_='). Содержимого не меняет. Если
             оставить её в ключе, каждая загрузка страницы создаёт НОВУЮ
             запись кэша: 5 открытий дали 6 копий version.json?ts=..., и кэш
             рос бы бесконечно. Поэтому ts/_ отбрасываем.

   Итог: версия значима, метка времени — нет. */
var IGNORABLE_PARAMS = ['ts', '_', 't'];

function staticCacheKey(req) {
  var u = new URL(req.url);
  if (!u.search) return u.href;
  var changed = false;
  IGNORABLE_PARAMS.forEach(function (p) {
    if (u.searchParams.has(p)) { u.searchParams.delete(p); changed = true; }
  });
  // остались только значимые параметры (например v) — версия различает версии
  return changed ? u.href : new URL(req.url).href;
}

async function cacheFirstForStatic(req) {
  var cache = await caches.open(CACHE_STATIC);

  /* v50: сначала ТОЧНОЕ совпадение (по ключу staticCacheKey), БЕЗ
     ignoreSearch на входе. Раньше здесь стоял ignoreSearch:true, и из-за
     этого query-версия <link href="style.css?v=NNN"> не bust-ила кэш.

     ignoreSearch НЕ удалён из проекта целиком, а перенесён ниже в ветку
     офлайна: там он остаётся страховкой (см. комментарий после catch). */
  var key = staticCacheKey(req);
  var cached = await cache.match(key);
  if (cached) return cached;

  try {
    var resp = await fetch(req);
    if (resp && resp.ok) {
      cache.put(key, resp.clone());
      return resp;
    }
    throw new Error('static not 200');
  } catch (err) {
    notifyOffline();

    /* Офлайн-страховка. Точное совпадение не нашлось (или сеть упала), но
       ресурс мог лежать в кэше под ДРУГИМ query —precache кладёт './style.css'
       без версии, а страницы просят 'style.css?v=NNN'. Раньше это закрывал
       ignoreSearch в самом начале функции; теперь — здесь, чтобы офлайн не
       потерял стили, а онлайн при этом честно уважал ?v=. */
    var loose = await cache.match(req, { ignoreSearch: true });
    if (loose) return loose;

    /* Навигация. Отдаём СВОЮ страницу, а не подменяем главной:
       - корень сайта -> index.html (это его штатный адрес);
       - любой другой URL -> offline.html с честным «нет соединения».
       Никогда не отдаём контент другой страницы: пользователь должен видеть,
       что запрошенной страницы нет офлайн, а не читать чужую. */
    if (req.mode === 'navigate') {
      var isRoot = new URL(req.url).pathname === new URL(INDEX_URL, self.registration.scope).pathname;
      var page = await cache.match(isRoot ? INDEX_URL : OFFLINE_URL);
      if (page) return page;
      return new Response('offline', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
    }

    /* Подресурс (CSS/JS/JSON/иконка). Response.error() даёт настоящую сетевую
       ошибку, а не 200 с чужим телом: так срабатывают обработчики страницы
       (например, catch в script.js покажет «не загрузились данные»). 
   v64: 29 правил interactions.html вынесены в style.css (.sb-*,
        .legend*, .severityFilter*) с сохранением @media-контекста.
        Локальными остались :root/--fg, body/header/footer, .btn/.tab,
        vis-network - эти селекторы заняты другими страницами.

   v65: #sidebar переименован в #atl-sidebar (atlas) и #int-sidebar
        (interactions) - под одним id жили два разных сайдбара.
        Обновлено 12 обращений из JS (9 getElementById + 3 $) и
        29 CSS-правил; снято 2 мёртвых правила на index и map.
        id оставлен id: перевод в класс уронил бы специфичность
        (1,0,0) -> (0,1,0) и ширину сайдбара перестала бы выигрывать.

   v66: 29 правил сайдбара вынесены из локальных <style> atlas и
        interactions в style.css (#atl-sidebar, #int-sidebar).
        Стало возможно после переименования id на Шаге 3: под общим
        #sidebar жили два разных сайдбара. @media(640px) и
        @supports(safe-area-inset-bottom) сохранены как были.
        Перед переносом проверено: ни один токен этих селекторов не
        встречается в style.css, и ни одно оставшееся локальное правило
        страницы не делит с переносимыми ни одного свойства.

   v67: шкала отступов объявлена в :root (11 токенов) и применена
        к 324 литералам, которые УЖЕ равны ступени. Пиксели не
        изменились: 0 различий на 13 ширинах x 18 страницах.
        ВАЖНО: имена токенов с ДЕФИСОМ, не с точкой. Имя кастомного
        свойства не может содержать '.', браузер выбрасывает такое
        объявление молча, а var() от него проваливает всё правило -
        измерено, это уронило 23 снапшота из 37.
        offline.html исключён: он намеренно не подключает style.css,
        и var() там сломал бы отступы без ошибки в консоли.
*/
    return Response.error();
  }
}

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_STATIC).then(function (cache) {
      return Promise.all(
        STATIC_ASSETS.map(function (url) {
          return cache.add(url).catch(function (err) {
            console.warn('[sw] skip ' + url + ':', err.message || err);
          });
        })
      );
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) {
          return k !== CACHE_STATIC && k !== CACHE_DATA;
        }).map(function (k) { return caches.delete(k); })
      );
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (DATA_RE.test(url.pathname)) {
    event.respondWith(networkFirstForData(req));
  } else {
    event.respondWith(cacheFirstForStatic(req));
  }
});
