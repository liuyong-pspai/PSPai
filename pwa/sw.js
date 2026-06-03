const CACHE = 'xlr-v1';
const ASSETS = [
  './mobile.html',
  './config.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './img_longyuan.jpg',
  './img_chiyu.jpg',
  './img_ling.jpg',
  './img_qingmo.jpg',
  './img_shuanghua.jpg',
  './img_yeying.jpg',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
