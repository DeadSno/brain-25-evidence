// Форсируем активацию новой версии сразу
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

/* v73 (2026-10-03, v5.1.5-fix): снята Яндекс.Метрика с index.html — счётчик
   tag.js и пиксель <noscript>; удалён мёртвый tracker.js; в форму обратной
   связи добавлен обязательный чекбокс согласия на обработку email.
   Изменились docs/index.html и docs/feedback.html — оба входят в
   STATIC_ASSETS, отдаются cacheFirstForStatic, поэтому бамп обязателен.
   style.css НЕ менялся, поэтому ?v= в страницах оставлен как был (v407).
   Запись вынесена сюда отдельно от длинного changelog-комментария,
   чтобы не править чужой блок по границам регулярки. */
/* v74 (2026-10-04, v5.1.6 cross-browser): в style.css добавлено
   .tabs #search{flex-basis:100%} в @media(max-width:480px). Правка чинит
   измеренное расхождение: поле поиска на interactions@412 было 344.81px в
   Chromium и 293.41px в WebKit, потому что flex-basis:250px из #search
   выигрывал у мобильного width:100%!important. Изменился style.css, поэтому
   ?v= в 17 страницах поднят с 407 на 408. HTML по содержимому не менялся,
   но бамп CACHE_VERSION всё равно нужен: style.css входит в STATIC_ASSETS
   и отдаётся cacheFirstForStatic, а ?v= браузер при кэшировании через SW
   не различает. */
/* v75 (2026-10-04, v5.4.0 Inter): шрифт перенесён из Google Fonts в
   репозиторий. Удалены preconnect на fonts.googleapis.com и fonts.gstatic.com
   и <link> на css2?family=Inter из docs/index.html; вместо них в style.css
   добавлено пять @font-face на статические начертания в docs/fonts/
   (Inter 4.1: Regular, Medium, SemiBold, Bold, ExtraBold — 561 КБ).
   Вариативный InterVariable.woff2 был отвергнут после замера: оба движка
   грузят его одинаково и рапортуют status 'loaded', но ширины кириллицы
   расходятся на всех пяти весах (400: 328.84 против 354.78) — ось веса они
   инстанцируют по-разному. У статики оси нет, и ширины сошлись.
   Причина переноса не в размере: fonts.googleapis.com отдавал шрифт
   с IP посетителя, то есть третья сторона получала данные о визите —
   та же причина, по которой снята Метрика.

   Побочный эффект: Inter теперь применяется на всех 18 страницах, а не на
   одной. До этого 17 страниц шли системным шрифтом, и Chromium с WebKit
   выбирали разный — расхождение 2-11% пикселей между движками.

   Файл добавлен в STATIC_ASSETS, иначе офлайн-PWA остался бы без шрифта.
   Изменились style.css и index.html, поэтому ?v= в 17 страницах поднят
   с 408 на 409. Бамп CACHE_VERSION обязателен: style.css, index.html и
   сам шрифт входят в STATIC_ASSETS и отдаются cacheFirstForStatic. */
/* v76 (2026-10-04, v5.4.0 dark-first): тёмная тема стала состоянием
   по умолчанию. Палитра переехала из html.dark,body.dark в :root, светлая
   — в html.light; класс .dark убран из разметки и из JS полностью.

   Что переписано: style.css (палитра и 35 селекторов), 17 страниц
   (предзагрузка в <head> и переключатели), script.js (initTheme/setLight),
   trends.html (своя setTheme), interactions.html (своя палитра),
   atlas/calculator/map (--apanel/--aborder/--atext/--amut) и inline
   <style> в calculator, feedback, graph, map, trends.

   Почему селекторы стали html:not(.light), а не голыми X: расчёт
   специфичности показал, что у html:not(.light) ровно (0,1,1) — столько же,
   сколько у body.dark. Голое X дало бы (0,1,0) и сломало бы 4 правила:
   #modal a, .trustChips .chip, h1 a и .top .site-title a — каждое
   перебивается более поздним правилом с меньшей специфичностью.

   Проверка: снапшоты 73 passed, 1 skipped, и картинки совпали с эталонами,
   снятыми ДО переворота. Значит инверсия визуально нейтральна.

   Изменились style.css и 17 страниц, поэтому ?v= поднят с 409 на 410. */
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
   кладёт './style.css' без версии, а страницы просят 'style.css?v=NNN'.

   v79 (2026-10-05, v5.6.0 этап 1.5): под текстом бейджа «Грейд A-D» на
   sup/*.html шёл ряд точек. Замерено в DevTools, а не найдено на глаз:
   у .grade-badge text-decoration: none, у вложенного <abbr> —
   underline dotted, то есть браузерное умолчание для abbr с title.
   Других элементов с dotted на странице нет, списков и псевдоэлементов
   бейджа нет. Добавлено .sup-wrap .grade-badge abbr{text-decoration:none} —
   точечно, вне бейджа dotted-подчёркивание у abbr осталось.

   Изменился style.css, поэтому ?v= в 17 страницах поднят с 412 на 413,
   а CACHE_VERSION — с v78 на v79: style.css входит в STATIC_ASSETS и
   отдаётся cacheFirstForStatic, а ?v= при кэшировании через SW не
   различается. Без обоих бампов фикс не дошёл бы до пользователей. */
/* v81 (2026-10-06, v5.6.1): в STATIC_ASSETS добавлен './sup/index.html' —
   каталог 130 страниц sup/*.html. До этого в прекеше лежали пять отдельных
   страниц (kreatin, magniy, omega-3, paba, vitamin-d): по прямой ссылке
   извне они открывались офлайн, но сам каталог — точка входа, из которой
   на них переходят, — не открывался вообще.

   Путь записан как './sup/index.html' — с './' и без ведущего слэша, как у
   остальных записей списка. cache.add() разрешает относительный URL по
   scope регистрации worker'а, поэтому ключом кэша становится
   http://<host>/sup/index.html — ровно тот адрес, которым приходит
   навигация, и точное совпадение в cacheFirstForStatic срабатывает без
   ignoreSearch. С ведущим слэшем ключ уехал бы в /sup/... от корня
   сервера, и на GitHub Pages (сайт лежит в /brain-25-evidence/) совпадение
   сломалось бы молча.

   Чего это НЕ даёт: каталог ссылается на 130 страниц, в прекеше их пять.
   Офлайн остальные 125 ссылок попадают в ветку навигации и получают
   offline.html — честное «нет соединения», а не чужая страница (блок про
   FALLBACK_HTML выше). Полный офлайн-каталог — это 130 файлов в кэше;
   решение за владельцем, здесь оно не принято.

   ?v= нигде не поднят: sup/index.html — HTML, а версионируются в страницах
   только CSS и скрипты (style.css?v=414). Бамп CACHE_VERSION v80 -> v81
   обязателен по правилу из шапки файла: install кладёт STATIC_ASSETS в кэш
   с именем CACHE_VERSION, а activate удаляет все кэши, кроме двух текущих,
   то есть новый кэш собирается с нуля. Без бампа новый список лёг бы в
   старый v80-static, где удалённые из STATIC_ASSETS файлы остались бы
   навсегда: чистит их только activate, а он без смены имени не чистит
   ничего. */

/* Бамп CACHE_VERSION v83 -> v84 обязателен по правилу из шапки файла
   (то же, что для v80 -> v81 на строке выше и v82 -> v83 ниже): install
   кладёт STATIC_ASSETS в кэш с именем CACHE_VERSION, а activate удаляет всё,
   кроме двух текущих. Без бампа новый список лёг бы в старый v83-static.

   Причина этого бампа — правки style.css в v5.6.2: тач-таргеты ссылок
   подвала и <summary>, плюс замок прокрутки body.modal-open. В ссылках на
   style.css ?v поднят с 414 на 415 в 143 файлах (12 страниц и 131 в sup/ —
   130 карточек плюс sup/index.html, не 130, как считал план). Обновлённый CSS
   пришёл бы в кэш только по новому ключу запроса, но activate всё равно
   нужен: иначе старый v83-static живёт вечно и cache.add() не перезапишет
   ключ, для которого файл не изменился. */

/* Бамп CACHE_VERSION v84 -> v85 обязателен по правилу из шапки файла
   (то же, что для v80 -> v81 и v82 -> v83): install кладёт STATIC_ASSETS в
   кэш с именем CACHE_VERSION, а activate удаляет всё, кроме двух текущих.

   Причина — правки style.css в v5.6.2: компактная шапка на мобильном
   (T1, #96), тач-таргет селектов (#94). В ссылках на style.css ?v поднят
   с 415 на 416 в тех же 143 файлах (12 страниц и 131 в sup/ — 130 карточек
   плюс sup/index.html). Без бампа activate не почистит старый v84-static,
   и удалённые из STATIC_ASSETS файлы остались бы в кэше навсегда. */

var CACHE_VERSION = 'v88';
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

/* sup/*.html, кроме sup/index.html. Каталог и пять прекешенных страниц
   (kreatin, magniy, omega-3, paba, vitamin-d) остаются в STATIC_ASSETS и
   идут через cacheFirstForStatic. Остальные 125 страниц — stale-while-revalidate:
   при первом визите кэш пуст, запрос идёт в сеть и кэшируется; при повторном
   кэш отдаётся сразу, а свежая копия догружается в фоне. */
var SUP_HTML_RE = /\/sup\/[^\/]+\.html$/;

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
  './feed.xml',
  './pwa.js',
  './version.js',
  './script.js',
  './style.css',
  './effect_tags.json',
  './effect_labels.json',
  './sup/index.html',
  './sup/kreatin.html',
  './sup/magniy.html',
  './sup/omega-3.html',
  './sup/paba.html',
  './sup/vitamin-d.html',
  './icons/192.png',
  './icons/512.png',
  './fonts/inter-regular.woff2',
  './fonts/inter-medium.woff2',
  './fonts/inter-semibold.woff2',
  './fonts/inter-bold.woff2',
  './fonts/inter-extrabold.woff2',
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

/* Stale-while-revalidate для sup/*.html (кроме sup/index.html).
   При первом визите страницы нет в кэше — запрос идёт в сеть, ответ
   кэшируется. При повторном визите кэш отдаётся сразу (без задержки),
   а в фоне догружается свежая копия и заменяет кэш. Так правки страниц
   доходят до пользователей при следующей загрузке, а не после сброса
   кэша или бампа CACHE_VERSION. */
async function staleWhileRevalidateForSup(req) {
  var cache = await caches.open(CACHE_STATIC);
  var key = staticCacheKey(req);
  var cached = await cache.match(key);

  /* Фоновая загрузка свежей копии. Запускается всегда, но результат
     используется только при первом визите (в кэше пусто). При повторном
     визите ошибка фоновой загрузки не страшна: кэш уже отдан пользователю. */
  var fetchPromise = fetch(req).then(function (resp) {
    if (resp && resp.ok) cache.put(key, resp.clone());
    return resp;
  }).catch(function () {
    /* Фон не смог обновить кэш — молча, пользователь уже видит кэш. */
  });

  if (cached) {
    /* Повторный визит: отдаём кэш сразу, свежесть — при следующей загрузке. */
    return cached;
  }

  /* Первый визит: в кэше пусто, ждём сеть. Офлайн — честный offline.html. */
  try {
    var resp = await fetchPromise;
    if (resp && resp.ok) return resp;
    throw new Error('sup not 200');
  } catch (err) {
    notifyOffline();
    var loose = await cache.match(req, { ignoreSearch: true });
    if (loose) return loose;
    return cache.match(OFFLINE_URL);
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
  } else if (SUP_HTML_RE.test(url.pathname) && url.pathname.indexOf('/sup/index.html') === -1) {
    event.respondWith(staleWhileRevalidateForSup(req));
  } else {
    event.respondWith(cacheFirstForStatic(req));
  }
});

/* v82 (2026-10-06, v5.6.1): sup/*.html (кроме sup/index.html) переведены
   на stale-while-revalidate. До этого все HTML страницы шли через
   cacheFirstForStatic: при повторном визите отдавалась копия с момента
   первого посещения, и правки страниц не доходили до пользователей,
   пока они сами не сбрасывали кэш. Это приемлемо для корневых страниц и
   пяти прекешенных sup (kreatin, magniy, omega-3, paba, vitamin-d) — они
   меняются редко, а их кэш чистит бамп CACHE_VERSION. Остальные 125 страниц
   каталога менялись чаще (правки текстов, ссылок, данных), и каждый бамп
   CACHE_VERSION из-за правки одной страницы — это пересборка кэша у всех
   пользователей.

   Стратегия stale-while-revalidate: при первом визите страницы нет в
   кэше, запрос идёт в сеть, ответ кэшируется; при повторном визите
   отдаётся кэш сразу (без задержки), а в фоне идёт загрузка свежей копии,
   которая заменяет кэш. Пользователь всегда получает страницу мгновенно,
   а правки доходят до него при следующей загрузке.

   sup/index.html не тронут: он в прекеше STATIC_ASSETS и остаётся
   cacheFirstForStatic. Каталог — точка входа, и его офлайн-доступность
   важнее свежести. Пять прекешенных страниц тоже не тронуты: их кэш
   чистится бампом CACHE_VERSION, и SWR не нужен.

   Бамп CACHE_VERSION v81 -> v82 обязателен: без него существующие
   пользователи не получат новый sw.js, потому что браузер проверяет
   файл на изменение, а sw.js уже у них в кэше под старой версией. */

/* v83 (2026-10-07, v5.6.1): в STATIC_ASSETS добавлен './feed.xml' —
   RSS-фид из scripts/build_feed.py (131 запись: каталог + 130 карточек).

   Зачем: фид не входил в precache, поэтому офлайн отдавал по нему
   offline.html — подписчик, у которого пропал интернет, получал вместо
   ленты страницу «нет соединения». Для автоопределения фида браузеру
   достаточно <link rel="alternate"> в head (он есть на всех 143
   страницах), но кеша за этой ссылкой не было.

   Стратегия: feed.xml не подпадает ни под DATA_RE, ни под SUP_HTML_RE,
   поэтому уходит в общую ветку cacheFirstForStatic. Для статического
   файла, меняющегося раз в месяц, это правильный выбор: stale-while-
   revalidate как у 125 карточек тут не нужен, а свежесть и так
   обеспечивается бампом CACHE_VERSION ниже.

   Путь записан как './feed.xml' — с './' и без ведущего слэша, по той же
   причине, что и у './sup/index.html' (см. запись v81): cache.add()
   разрешает относительный URL по scope worker'а, поэтому ключом кэша
   становится http://<host>/feed.xml — ровно тот адрес, которым приходит
   запрос. На GitHub Pages (сайт лежит в /brain-25-evidence/) это
   единственная форма, при которой точное совпадение в cacheFirstForStatic
   срабатывает без ignoreSearch.

   Бамп CACHE_VERSION v82 -> v83 обязателен по правилу из шапки файла:
   install кладёт STATIC_ASSETS в кэш с именем CACHE_VERSION, а activate
   удаляет всё, кроме двух текущих. Без бампа новый список лёг бы в старый
   v82-static и офлайн-фид так и не появился бы: cache.add() не перезаписывает
   уже закешированный ключ, если файл не менялся. */
