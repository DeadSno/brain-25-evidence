/* v2.7 PWA: cache-first для статики, network-first для data.json, бейдж офлайн. */
var CACHE_STATIC = 'v27-static';
var CACHE_DATA = 'v27-data';
var DATA_KEY = './data.json';
var FALLBACK_HTML = './index.html';

var STATIC_ASSETS = [
  './index.html',
  './map.html',
  './manifest.webmanifest',
  './pwa.js',
  './script.js',
  './style.css',
  './icons/192.png',
  './icons/512.png'
];

function notifyOffline() {
  self.clients.matchAll().then(function (clients) {
    clients.forEach(function (c) {
      c.postMessage({ type: 'offline' });
    });
  });
}

async function networkFirstForData(req) {
  var cache = await caches.open(CACHE_DATA);
  try {
    var resp = await fetch(req);
    if (resp && resp.ok) {
      cache.put(DATA_KEY, resp.clone());
      return resp;
    }
    throw new Error('data.json не 200');
  } catch (err) {
    notifyOffline();
    var cached = await cache.match(DATA_KEY);
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
      cache.put(req.clone(), resp.clone());
      return resp;
    }
    throw new Error('static не 200');
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
      return cache.addAll(STATIC_ASSETS);
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
  if (url.pathname.endsWith('/data.json')) {
    event.respondWith(networkFirstForData(req));
    return;
  }
  event.respondWith(cacheFirstForStatic(req));
});