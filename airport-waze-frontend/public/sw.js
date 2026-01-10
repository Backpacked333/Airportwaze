// AirportWaze Service Worker
// Handles offline caching, background sync, and push notifications

const CACHE_VERSION = 'airportwaze-v1';
const CACHE_STATIC = `${CACHE_VERSION}-static`;
const CACHE_DYNAMIC = `${CACHE_VERSION}-dynamic`;
const CACHE_API = `${CACHE_VERSION}-api`;

// Files to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// API endpoints to cache (with short TTL)
const API_ENDPOINTS = [
  '/api/airports',
  '/api/healthz'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(CACHE_STATIC)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Service worker installed');
        return self.skipWaiting(); // Activate immediately
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name.startsWith('airportwaze-') && name !== CACHE_VERSION)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service worker activated');
        return self.clients.claim(); // Take control immediately
      })
  );
});

// Fetch event - network-first strategy for API, cache-first for static
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin && !url.pathname.startsWith('/api/')) {
    return;
  }

  // API requests: Network-first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response for caching
          const responseClone = response.clone();

          // Cache successful GET requests
          if (request.method === 'GET' && response.status === 200) {
            caches.open(CACHE_API).then((cache) => {
              cache.put(request, responseClone);
            });
          }

          return response;
        })
        .catch(() => {
          // Network failed, try cache
          return caches.match(request);
        })
    );
    return;
  }

  // Static assets: Cache-first with network fallback
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          // Return cached version and update in background
          fetch(request).then((response) => {
            if (response.status === 200) {
              caches.open(CACHE_DYNAMIC).then((cache) => {
                cache.put(request, response);
              });
            }
          });
          return cachedResponse;
        }

        // Not in cache, fetch from network
        return fetch(request)
          .then((response) => {
            // Cache successful responses
            if (response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_DYNAMIC).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return response;
          });
      })
  );
});

// Background Sync - upload telemetry when connection restored
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync event:', event.tag);

  if (event.tag === 'upload-telemetry') {
    event.waitUntil(uploadPendingTelemetry());
  }
});

// Push notifications - notify user of wait time changes
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  let data = {};
  if (event.data) {
    data = event.data.json();
  }

  const title = data.title || 'AirportWaze';
  const options = {
    body: data.body || 'Airport wait time update',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-96x96.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: [
      {
        action: 'view',
        title: 'View Details'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Helper: Upload pending telemetry data
async function uploadPendingTelemetry() {
  try {
    // Get pending telemetry from IndexedDB
    const db = await openTelemetryDB();
    const tx = db.transaction('pending', 'readonly');
    const store = tx.objectStore('pending');
    const pending = await store.getAll();

    console.log(`[SW] Uploading ${pending.length} pending telemetry batches`);

    // Upload each batch
    for (const batch of pending) {
      try {
        const response = await fetch('/api/telemetry/upload', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(batch.data)
        });

        if (response.ok) {
          // Remove from pending queue
          const deleteTx = db.transaction('pending', 'readwrite');
          const deleteStore = deleteTx.objectStore('pending');
          await deleteStore.delete(batch.id);
          console.log('[SW] Uploaded batch:', batch.id);
        }
      } catch (error) {
        console.error('[SW] Failed to upload batch:', error);
      }
    }

    db.close();
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

// Helper: Open IndexedDB for telemetry storage
function openTelemetryDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AirportWazeTelemetry', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Create object stores
      if (!db.objectStoreNames.contains('pending')) {
        const pendingStore = db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
        pendingStore.createIndex('timestamp', 'timestamp', { unique: false });
      }

      if (!db.objectStoreNames.contains('sessions')) {
        const sessionsStore = db.createObjectStore('sessions', { keyPath: 'sessionId' });
        sessionsStore.createIndex('airportCode', 'airportCode', { unique: false });
      }
    };
  });
}

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((name) => caches.delete(name))
        );
      })
    );
  }
});

console.log('[SW] Service worker loaded');
