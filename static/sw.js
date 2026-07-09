const CACHE_VERSION = "sikande-pwa-v2";

const PRECACHE_URLS = [
  "/static/css/style.css",
  "/static/js/pwa.js",
  "/static/js/sikandeScript.js",
  "/static/js/dashboard.js",
  "/static/images/logo-S-big-transparent.png",
  "/static/images/logo-S-big-transparent.ico",
  "/static/images/kabah-sikande.jpg",
  "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) {
    return;
  }

  if (!url.pathname.startsWith("/static/") && url.pathname !== "/manifest.webmanifest") {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }

      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || response.type === "opaque") {
          return response;
        }

        const copy = response.clone();
        caches.open(CACHE_VERSION).then((cache) => cache.put(event.request, copy));
        return response;
      });
    })
  );
});
