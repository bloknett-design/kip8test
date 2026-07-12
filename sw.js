// ============================================================
// Service Worker для КИПиА — ТЕСТОВЫЙ РЕПОЗИТОРИЙ kip8test
// ============================================================
// ВНИМАНИЕ: это тестовая версия SW для репозитория kip8test.
// Имена кэшей содержат суффикс '-test' чтобы избежать конфликтов
// с основным репозиторием kip8 на том же origin (github.io).
//
// КАК ОБНОВИТЬ САЙТ: увеличьте CACHE_VERSION ниже.
//   'kipia-test-v1' → 'kipia-test-v2' → 'kipia-test-v3' и т.д.
// При смене версии SW удалит ВСЕ старые кэши и закэширует
// свежие версии файлов из ASSETS.
// ============================================================

const CACHE_VERSION = 'kipia-test-v45';
const CACHE_NAME = CACHE_VERSION;

// Отдельный кэш для картинок Google Drive (превью + полные).
// ВАЖНО: эта версия НЕ зависит от CACHE_VERSION. При обновлении приложения
// (инкременте CACHE_VERSION) кэш картинок сохраняется — пользователю не нужно
// заново скачивать все 26 картинок после каждого релиза.
// Инкрементируйте IMAGE_CACHE_VERSION только если нужно принудительно сбросить
// кэш картинок (например, если в Google Drive заменили файлы с тем же ID).
const IMAGE_CACHE_VERSION = 'kipia-images-test-v1';
const IMAGE_CACHE_NAME = IMAGE_CACHE_VERSION;

// Файлы для пред-кэширования при установке SW.
// Эти ресурсы будут доступны в офлайне сразу после первой загрузки.
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './images/icon-192.png',
  './images/icon-512.png',
  './images/icon-192-maskable.png',
  './images/icon-512-maskable.png',
  './images/icon.png',
  './images/1000\u0412.png',
  './images/4\u0440.png',
  './images/5\u0440.png',
  './images/6\u0440.png',
  './data/exam-tickets.json'
];

// App Shell — главный HTML-файл, который обслуживает все навигационные
// запросы в офлайне. PWA «КИПиА» — SPA, поэтому любой navigation-запрос
// должен вернуть index.html (один и тот же HTML для всех маршрутов).
const APP_SHELL_URL = './index.html';

// Теги фоновой синхронизации
const SYNC_TAG_ANALYTICS = 'kipia-sync-analytics';
const SYNC_TAG_DATA_REFRESH = 'kipia-sync-data';

// ============================================================
// Утилита: получить "чистый" ключ кэша (URL без query-параметров)
// ============================================================
// ВАЖНО: index.html использует cache-busting для data/exam-tickets.json
// через ?v=t<timestamp>. Это создаёт новый URL при каждой перезагрузке
// страницы. Если использовать event.request как ключ кэша напрямую,
// Cache Storage будет расти бесконечно, а в офлайне запрос с новым
// timestamp не найдёт закэшированную версию.
//
// Решение: для локальных GET-запросов ключом кэша служит URL БЕЗ query.
//   fetch(event.request)              ← оригинальный запрос (с ?v=t123, для сервера)
//   cache.put(cacheKey, response)     ← ключ без query (для стабильности кэша)
//   caches.match(cacheKey)            ← поиск по ключу без query
function makeCacheKey(request) {
  const url = new URL(request.url);
  // Для локальных запросов отбрасываем search (всё после '?')
  if (url.origin === self.location.origin) {
    // Новый Request с тем же методом, но URL без query.
    // headers не копируются — для кэша они не нужны.
    return new Request(url.pathname, { method: request.method });
  }
  // Для внешних ресурсов (шрифты, CDN) — ключом служит полный URL,
  // потому что query часто содержит аутентификационные токены или
  // версии, которые являются частью идентичности ресурса.
  return request;
}

// ============================================================
// Install — пред-кэширование основных файлов
// ============================================================
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
  // Немедленно активировать новый SW, не дожидаясь закрытия старых вкладок
  self.skipWaiting();
});

// ============================================================
// Activate — удалить старые кэши + очистить «осиротевшие» записи
// ============================================================
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => {
        // 1. Удалить все кэши с другими именами, КРОМЕ IMAGE_CACHE_NAME.
        //    Кэш картинок переживает обновления CACHE_VERSION — иначе пользователю
        //    пришлось бы заново скачивать все 26 картинок после каждого релиза.
        const deleteOldCaches = Promise.all(
          keys.filter(k => k !== CACHE_NAME && k !== IMAGE_CACHE_NAME).map(k => caches.delete(k))
        );
        return deleteOldCaches.then(() => {
          // 2. В текущем кэше удалить записи, которых больше нет в ASSETS
          //    (например, устаревшие ?v=t1234567890 от предыдущей версии SW)
          return caches.open(CACHE_NAME).then(cache => {
            return cache.keys().then(requests => {
              return Promise.all(requests.map(req => {
                // Нормализуем текущий ключ так же, как makeCacheKey
                const normalizedKey = makeCacheKey(req);
                const normalizedUrl = new URL(normalizedKey.url);
                // Список допустимых путей из ASSETS (без './' префикса и query)
                const validPaths = ASSETS.map(a => a.replace(/^\.\//, '/'));
                // Если запись не входит в ASSETS — удаляем
                const matches = validPaths.some(p => normalizedUrl.pathname === p);
                if (!matches) {
                  return cache.delete(req);
                }
                return Promise.resolve();
              }));
            });
          });
        });
      })
      .then(() => self.clients.claim())  // Захватить контроль над всеми вкладками
  );
});

// ============================================================
// Fetch — стратегия NETWORK-FIRST + App Shell для навигации
// ============================================================
// Логика:
//   1. Навигационные запросы (mode === 'navigate') — это запросы HTML-страниц.
//      Для SPA возвращаем index.html (App Shell), который сам разберётся с
//      маршрутизацией. Сначала пытаемся обновить кэш из сети, при ошибке —
//      отдаём закэшированный index.html. Это гарантирует, что любой URL
//      внутри приложения (например, /kip8/#tickets-1000v) откроется в офлайне.
//
//   2. Локальные файлы (CSS, JS, JSON, images):
//      - Идём в сеть с оригинальным запросом (включая cache-busting query).
//      - При успехе — обновляем кэш по нормализованному ключу (без query).
//      - При ошибке сети — отдаём из кэша по нормализованному ключу.
//
//   3. Внешние ресурсы (шрифты Google, CDN):
//      - Идём в сеть с оригинальным запросом.
//      - При успехе — кэшируем по полному URL (query сохраняется).
//      - При ошибке — отдаём из кэша по полному URL.
self.addEventListener('fetch', event => {
  const request = event.request;

  // Только GET-запросы кэшируем
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  const isLocal = url.origin === self.location.origin;

  // ===== 1. Навигационные запросы (App Shell pattern) =====
  // Это запросы HTML-страниц (location reload, переход по ссылке и т.д.)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) {
            // Обновляем кэш свежим index.html
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(APP_SHELL_URL, clone));
          }
          return response;
        })
        .catch(() => {
          // Нет сети — отдаём закэшированный App Shell
          return caches.match(APP_SHELL_URL).then(cached => {
            return cached || new Response(
              '<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">' +
              '<title>КИПиА — офлайн</title></head><body style="font-family:sans-serif;' +
              'background:#1a2233;color:#e0e0e0;padding:40px;text-align:center;">' +
              '<h1>Нет подключения к интернету</h1>' +
              '<p>Приложение КИПиА требует первого запуска с интернетом.</p>' +
              '<p>После первой загрузки оно будет работать офлайн.</p>' +
              '</body></html>',
              {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'text/html; charset=utf-8' }
              }
            );
          });
        })
    );
    return;
  }

  // ===== 2. Внешние ресурсы (шрифты Google, CDN, картинки Google Drive) =====
  // Для картинок билетов (drive.google.com/thumbnail, lh3.googleusercontent.com)
  // запросы от <img> идут с mode:'no-cors' → response.type === 'opaque' (status 0).
  // Opaque responses тоже кэшируем — в офлайне <img> сможет их отрендерить.
  //
  // Стратегия для Google Drive картинок — STALE-WHILE-REVALIDATE:
  //   - Сразу отдаём из кэша (мгновенный рендер <img>)
  //   - Фоном идём в сеть и обновляем кэш (пользователь видит старую версию, следующая загрузка — свежую)
  //   - Если кэша нет — идём в сеть (первая загрузка)
  //   - Если сети нет и кэша нет — ошибка (картинка не отрендерится, сработает fallback)
  //
  // Стратегия для прочих внешних ресурсов (шрифты) — NETWORK-FIRST:
  //   - Идём в сеть, при успехе кэшируем, при ошибке — отдаём из кэша.
  if (!isLocal) {
    const isGoogleDriveImage = url.hostname === 'drive.google.com' ||
                                url.hostname === 'lh3.googleusercontent.com';

    if (isGoogleDriveImage) {
      // Stale-while-revalidate через отдельный IMAGE_CACHE_NAME (переживает обновления версии)
      event.respondWith(
        caches.open(IMAGE_CACHE_NAME).then(cache => {
          return cache.match(request).then(cached => {
            // Фоновое обновление в сети (не блокирует ответ)
            const fetchPromise = fetch(request).then(response => {
              if (response.ok || response.type === 'opaque') {
                cache.put(request, response.clone());
              }
              return response;
            }).catch(() => null); // ошибка сети — тихо игнорируем (у нас уже есть cached или вернём ошибку)
            // Если есть кэш — отдаём сразу; сеть обновит кэш для следующего раза.
            // Если кэша нет — ждём сеть.
            return cached || fetchPromise;
          });
        })
      );
      return;
    }

    // Прочие внешние ресурсы (шрифты Google, CDN) — network-first
    event.respondWith(
      fetch(request)
        .then(response => {
          // Кэшируем успешные ответы И opaque (no-cors) ответы.
          // response.ok === false для opaque (status 0), но cache.put() их принимает.
          if (response.ok || response.type === 'opaque') {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // ===== 3. Локальные файлы (CSS-in-HTML, JS-in-HTML, JSON, images) =====
  const cacheKey = makeCacheKey(request);

  event.respondWith(
    fetch(request)
      .then(response => {
        if (response.ok) {
          // Обновляем кэш по нормализованному ключу (без ?v=...)
          // Важно: response.clone() нужен, т.к. сам response пойдёт в браузер.
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(cacheKey, clone));
        }
        return response;
      })
      .catch(() => {
        // Нет сети — отдаём из кэша по нормализованному ключу
        return caches.match(cacheKey).then(cached => {
          if (cached) return cached;
          // Если кэша нет — пытаемся найти по полному URL (на случай,
          // если какая-то старая запись осталась без нормализации)
          return caches.match(request).then(fallback => {
            return fallback || new Response('Offline', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: { 'Content-Type': 'text/plain; charset=utf-8' }
            });
          });
        });
      })
  );
});

// ============================================================
// Background Sync — фоновая синхронизация
// ============================================================
// Регистрируется через navigator.serviceWorker.ready.then(reg =>
//   reg.sync.register('kipia-sync-data'))
//
// Срабатывает, когда:
//   - Пользователь зарегистрировал sync и есть подключение к сети
//   - Браузер сам решает, когда выполнить (обычно сразу при появлении сети)
//
// Используются два тега:
//   - kipia-sync-analytics — отправка накопившейся аналитики (заглушка)
//   - kipia-sync-data-refresh — обновление exam-tickets.json в фоне
self.addEventListener('sync', event => {
  if (event.tag === SYNC_TAG_ANALYTICS) {
    event.waitUntil(sendPendingAnalytics());
  } else if (event.tag === SYNC_TAG_DATA_REFRESH) {
    event.waitUntil(refreshTicketsData());
  }
});

// Заглушка для отправки аналитики.
// В будущем здесь можно отправлять накопленные события на сервер.
async function sendPendingAnalytics() {
  // TODO: реализовать отправку накопленной аналитики, когда будет endpoint.
  // Пока просто логируем, что sync сработал — это поможет при отладке.
  try {
    const allClients = await self.clients.matchAll({ includeUncontrolled: true });
    allClients.forEach(client => {
      client.postMessage({ type: 'SYNC_ANALYTICS_DONE', tag: SYNC_TAG_ANALYTICS });
    });
  } catch (e) {
    // Тихая ошибка — sync не должен падать
  }
}

// Обновление exam-tickets.json в фоне.
// Используется тот же cache-busting подход, что и в index.html.
async function refreshTicketsData() {
  try {
    const cache = await caches.open(CACHE_NAME);
    // Используем cache-busting query, как и в основном коде
    const url = './data/exam-tickets.json?v=sync' + Date.now();
    const response = await fetch(url);
    if (response.ok) {
      // Кэшируем по нормализованному ключу (без query) —
      // это гарантирует, что в офлайне запрос найдёт свежую версию
      const cacheKey = new Request('./data/exam-tickets.json', { method: 'GET' });
      await cache.put(cacheKey, response.clone());
      // Уведомляем все открытые вкладки, что данные обновились
      const allClients = await self.clients.matchAll({ includeUncontrolled: true });
      allClients.forEach(client => {
        client.postMessage({ type: 'DATA_REFRESHED', tag: SYNC_TAG_DATA_REFRESH });
      });
    }
  } catch (e) {
    // Тихая ошибка — sync не должен падать, повторится при следующей возможности
  }
}

// ============================================================
// Message handler — коммуникация с главным потоком
// ============================================================
self.addEventListener('message', event => {
  if (!event.data) return;

  switch (event.data.type) {
    case 'SKIP_WAITING':
      // Принудительно активировать новый SW (альтернатива self.skipWaiting())
      self.skipWaiting();
      break;

    case 'REGISTER_SYNC':
      // Регистрация фоновой синхронизации из главного потока
      if (event.data.tag && 'sync' in self.registration) {
        self.registration.sync.register(event.data.tag).catch(() => {
          // sync API может быть недоступен (Safari, Firefox) — тихо игнорируем
        });
      }
      break;

    case 'FORCE_REFRESH_DATA':
      // Принудительное обновление данных по запросу пользователя
      event.waitUntil(refreshTicketsData());
      break;
  }
});
