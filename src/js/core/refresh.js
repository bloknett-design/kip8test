/**
 * @module core/refresh
 * @description Refresh, connection indicator, and periodic connection check.
 * Extracted from the monolithic src/index.html (2nd post-main script block, lines 21003–21252).
 */

// Таймер для авто-скрытия зелёного облака через 5 секунд
let _cloudHideTimer = null;

// Показать зелёное облако на 5 секунд, затем скрыть.
function showCloudBriefly() {
    const el = document.getElementById('connectionIndicator');
    if (!el) return;
    if (el.classList.contains('offline')) return;
    el.classList.add('cloud-visible');
    if (_cloudHideTimer) clearTimeout(_cloudHideTimer);
    _cloudHideTimer = setTimeout(() => {
        el.classList.remove('cloud-visible');
        _cloudHideTimer = null;
    }, 5000);
}

// Утилита обновления визуального состояния кнопки обновления.
function updateConnectionIndicator() {
    const el = document.getElementById('connectionIndicator');
    if (!el) return;
    const isOnline = navigator.onLine;
    if (isOnline) {
        el.classList.remove('offline');
        el.title = 'Обновить данные приложения';
        el.setAttribute('aria-label', 'Обновить данные приложения');
    } else {
        el.classList.add('offline');
        el.classList.remove('refreshing');
        el.classList.remove('cloud-visible');
        el.title = 'Офлайн — обновление недоступно';
        el.setAttribute('aria-label', 'Офлайн — обновление недоступно');
    }
}

// Главная функция обновления данных приложения.
async function refreshAppData() {
    const el = document.getElementById('connectionIndicator');
    if (!el) return;

    // Десктоп (Electron): принудительное обновление
    if (typeof process !== 'undefined' && process.type === 'renderer') {
        forceDesktopRefresh();
        return;
    }

    if (window.matchMedia('(min-width: 1024px)').matches && window.__isElectron) {
        forceDesktopRefresh();
        return;
    }

    if (!navigator.onLine) {
        window.showToast('Нет подключения к интернету');
        return;
    }

    if (el.classList.contains('refreshing')) return;

    el.classList.add('refreshing');
    el.classList.remove('cloud-visible');
    el.title = 'Обновление…';
    const startTime = Date.now();
    const MIN_ANIMATION_MS = 800;

    try {
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.ready.then(reg => reg.update()).catch(() => {});
        }

        if (typeof window._ticketsData !== 'undefined') {
            window._ticketsData = null;
        }
        if (typeof window.loadTicketsData === 'function') {
            await window.loadTicketsData(true);
        }

        if (typeof window.renderTickets === 'function') {
            const activePage = document.querySelector('.page-content.active');
            if (activePage) {
                const pageId = activePage.id.replace('page-', '');
                if (pageId && pageId.indexOf('tickets-') === 0) {
                    window.renderTickets(pageId, '');
                }
            }
        }

        if (typeof window.KipFav !== 'undefined') window.KipFav.updateDashboardButton();

        window.showToast('Данные обновлены');
    } catch (e) {
        window.showToast('Ошибка обновления: ' + (e.message || e));
    } finally {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, MIN_ANIMATION_MS - elapsed);
        setTimeout(() => {
            el.classList.remove('refreshing');
            updateConnectionIndicator();
            showCloudBriefly();
        }, remaining);
    }
}

// Полное обновление приложения (из бокового меню).
async function forceFullRefresh() {
    window.showToast('Обновление…');

    try {
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            await Promise.all(cacheNames.map(name => caches.delete(name)));
        }

        if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            await Promise.all(registrations.map(reg => reg.unregister()));
        }

        if (window.__electronClearCache) {
            await window.__electronClearCache();
        }
    } catch (e) {
        console.log('[forceFullRefresh] Ошибка очистки кэша:', e);
    }

    setTimeout(() => {
        const url = new URL(window.location.href);
        url.searchParams.set('_nocache', Date.now());
        window.location.replace(url.toString());
    }, 400);
}

// Принудительное обновление десктопного приложения.
async function forceDesktopRefresh() {
    const el = document.getElementById('connectionIndicator');
    if (el) {
        el.classList.add('refreshing');
        el.title = 'Принудительное обновление…';
    }
    window.showToast('Принудительное обновление…');

    try {
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            await Promise.all(cacheNames.map(name => caches.delete(name)));
            console.log('[forceDesktopRefresh] Cache Storage очищен:', cacheNames);
        }

        if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            await Promise.all(registrations.map(reg => reg.unregister()));
            console.log('[forceDesktopRefresh] Service Worker unregister:', registrations.length);
        }

        if (window.__electronClearCache) {
            await window.__electronClearCache();
            console.log('[forceDesktopRefresh] HTTP-кэш Chromium очищен');
        }
    } catch (e) {
        console.log('[forceDesktopRefresh] Ошибка очистки кэша:', e);
    }

    setTimeout(() => {
        const url = new URL(window.location.href);
        url.searchParams.set('_nocache', Date.now());
        window.location.replace(url.toString());
    }, 400);
}

// Слушаем события online/offline
window.addEventListener('online', function() {
    updateConnectionIndicator();
    showCloudBriefly();
});
window.addEventListener('offline', updateConnectionIndicator);

// Более надёжная проверка подключения через HEAD-запрос.
async function checkRealConnection() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        const response = await fetch('manifest.json?v=check' + Date.now(), {
            method: 'HEAD',
            cache: 'no-cache',
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response.ok;
    } catch (e) {
        return false;
    }
}

// Периодическое обновление статуса подключения.
async function periodicConnectionCheck() {
    const el = document.getElementById('connectionIndicator');
    if (!el) return;
    if (el.classList.contains('refreshing')) return;
    const isReallyOnline = await checkRealConnection();
    const elCurrentlyOffline = el.classList.contains('offline');
    if (isReallyOnline && elCurrentlyOffline) {
        el.classList.remove('offline');
        el.title = 'Обновить данные приложения';
        showCloudBriefly();
    } else if (!isReallyOnline && !elCurrentlyOffline) {
        el.classList.add('offline');
        el.classList.remove('cloud-visible');
        el.title = 'Офлайн — обновление недоступно';
    }
}

// При загрузке страницы устанавливаем начальный статус + запускаем периодическую проверку
document.addEventListener('DOMContentLoaded', updateConnectionIndicator);
window.addEventListener('load', function() {
    updateConnectionIndicator();
    setInterval(periodicConnectionCheck, 15000);
    setTimeout(periodicConnectionCheck, 3000);
});

export {
    refreshAppData,
    forceFullRefresh,
    forceDesktopRefresh,
    updateConnectionIndicator,
    showCloudBriefly,
    checkRealConnection,
    periodicConnectionCheck
};
