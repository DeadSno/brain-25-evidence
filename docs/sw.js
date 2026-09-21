/* v29 PWA: cache-first для статики, network-first для data.json.
   Install через поштучный cache.add().catch() — один missing файл
   не валит всю установку. Бамп CACHE_VERSION при изменении STATIC_ASSETS. */
var CACHE_VERSION = 'v33';
var CACHE_STATIC = CACHE_VERSION + '-static';
var CACHE_DATA = CACHE_VERSION + '-data';
var DATA_PATH = '/data.json';
var FALLBACK_HTML = './index.html';

var STATIC_ASSETS = [
  './index.html',
  './map.html',
  './interactions.html',
  './atlas.html',
  './manifest.webmanifest',
  './pwa.js',
  './version.js',
  './script.js',
  './style.css',
  './effect_tags.json',
  './effect_labels.json',
  './icons/192.png',
  './icons/512.png'
];

function notifyOffline() {
  self.clients.matchAll().then(function (clients) {
    clients.forEach(function (c) { c.postMessage({ type: 'offline' }); });
  });
}

async function networkFirstForData(req) {
  var cache = await caches.open(CACHE_DATA);
  var dataKey = new URL(DATA_PATH, self.location.origin).toString();
  try {
    var resp = await fetch(req, { cache: 'no-store' });
    if (resp && resp.ok) {
      cache.put(dataKey, resp.clone());
      return resp;
    }
    throw new Error('data.json not 200');
  } catch (err) {
    notifyOffline();
    var cached = await cache.match(dataKey);
    if (cached) return cached;
    return new Response('[]', {
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'x-fallback': '1' }
    });
  }
}

async function cacheFirstForStatic(req) {
  var cache = await caches.open(CACHE_STATIC);
  var cached = await cache.match(req, { ignoreSearch: true });
  if (cached) return cached;
  try {
    var resp = await fetch(req);
    if (resp && resp.ok) {
      cache.put(req, resp.clone());
      return resp;
    }
    throw new Error('static not 200');
  } catch (err) {
    notifyOffline();
    var fallback = await cache.match(FALLBACK_HTML);
    if (fallback) return fallback;
    return new Response('offline', { status: 503 });
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

  if (url.pathname === DATA_PATH) {
    event.respondWith(networkFirstForData(req));
  } else {
    event.respondWith(cacheFirstForStatic(req));
  }
});