// QRMenu Service Worker
'use strict';

const CACHE_NAME = 'qrmenu-v1';
const STATIC_ASSETS = [
  '/static/css/main.css',
  '/static/css/themes.css',
  '/static/js/cart.js',
  '/static/js/dashboard.js',
  '/static/js/kitchen.js',
  '/static/js/notifications.js',
  '/static/manifest.json',
  '/static/offline.html'
];

// Install: cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: cache-first for static, network-first for API/navigation
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // API calls: Network-first, no cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request).catch(() => new Response('{}', { headers: { 'Content-Type': 'application/json' } })));
    return;
  }

  // Static assets: Cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request).then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return res;
      }))
    );
    return;
  }

  // Navigation: Network-first with offline fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.match('/static/offline.html').then(r => r || new Response('غير متصل بالإنترنت', { headers: { 'Content-Type': 'text/html;charset=utf-8' } }))
      )
    );
    return;
  }

  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});

// Push notifications
self.addEventListener('push', event => {
  let data = { title: 'QRMenu', body: 'لديك إشعار جديد', url: '/' };
  try {
    data = { ...data, ...event.data.json() };
  } catch (e) {}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/static/icons/icon-192.png',
      badge: '/static/icons/icon-192.png',
      dir: 'rtl',
      lang: 'ar',
      data: { url: data.url }
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
      const existing = cs.find(c => c.url === url);
      if (existing) return existing.focus();
      return clients.openWindow(url);
    })
  );
});
