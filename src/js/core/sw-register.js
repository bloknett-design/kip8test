/**
 * @module core/sw-register
 * @description Service Worker registration and lifecycle handling.
 * Extracted from the separate `<script>` block in src/index.html (lines 20960–20999).
 *
 * This module is self-executing on import: simply importing it
 * is enough to register the service worker.
 */

if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('./sw.js').then(function(reg) {
            // Проверять обновления SW каждые 30 минут
            setInterval(function() { reg.update(); }, 30 * 60 * 1000);

            // Регистрация фоновой синхронизации для обновления данных
            // (exam-tickets.json). Сработает при появлении сети, если
            // браузер поддерживает Background Sync API. Safari/Firefox
            // не поддерживают — тихо игнорируется.
            if ('SyncManager' in window) {
                reg.sync.register('kipia-sync-data').catch(function() {
                    // Sync API недоступен или заблокирован — не критично
                });
            }

            // Слушаем сообщения от SW (например, "данные обновились")
            navigator.serviceWorker.addEventListener('message', function(event) {
                if (!event.data) return;
                if (event.data.type === 'DATA_REFRESHED') {
                    // SW обновил exam-tickets.json в фоне — сбросим
                    // in-memory кэш, чтобы при следующем открытии билетов
                    // загрузилась свежая версия
                    if (typeof _ticketsData !== 'undefined') {
                        _ticketsData = null;
                    }
                }
            });
        }).catch(function(err) {
            // Ошибка регистрации SW — приложение работает без офлайна
        });

        // Автообновление страницы при активации нового Service Worker
        navigator.serviceWorker.addEventListener('controllerchange', function() {
            // Новый SW взял контроль — перезагружаем для загрузки свежих файлов
            window.location.reload();
        });
    });
}
