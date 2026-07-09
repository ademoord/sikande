/* Sikande service worker — shell caching + offline fallback */
const CACHE_VERSION = 'v1';
const PRECACHE = 'sikande-precache-' + CACHE_VERSION;
const RUNTIME = 'sikande-runtime-' + CACHE_VERSION;

const PRECACHE_URLS = [
  '/offline',
  '/static/css/style.css',
  '/static/js/pwa.js',
  '/static/js/sikandeScript.js',
  '/static/js/dashboard.js',
  '/static/images/logo-S-big-transparent.png',
  '/static/images/logo-S-big-transparent.ico',
  '/static/images/kabah-sikande.jpg',
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(PRECACHE).then(function (cache) {
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (key) {
          return key.indexOf('sikande-') === 0 && key !== PRECACHE && key !== RUNTIME;
        }).map(function (key) {
          return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') {
    return;
  }

  var url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    return;
  }

  if (url.pathname.indexOf('/api/') === 0) {
    return;
  }

  if (url.pathname.indexOf('/static/') === 0) {
    event.respondWith(cacheFirst(request));
    return;
  }

  if (request.mode === 'navigate' || (request.headers.get('accept') || '').indexOf('text/html') !== -1) {
    event.respondWith(networkFirst(request));
  }
});

function cacheFirst(request) {
  return caches.match(request).then(function (cached) {
    if (cached) {
      return cached;
    }
    return fetch(request).then(function (response) {
      if (response && response.status === 200) {
        var copy = response.clone();
        caches.open(RUNTIME).then(function (cache) {
          cache.put(request, copy);
        });
      }
      return response;
    });
  });
}

function networkFirst(request) {
  return fetch(request).catch(function () {
    return caches.match(request).then(function (cached) {
      return cached || caches.match('/offline');
    });
  });
}
