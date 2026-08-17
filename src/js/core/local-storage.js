/**
 * @module core/local-storage
 * @description localStorage isolation — wraps getItem/setItem/removeItem
 * with 'kip8test:' prefix so that settings from this test repository
 * don't collide with the main kip8 repository on the same origin.
 *
 * Original source: src/index.html lines 8521–8534.
 *
 * This module is self-executing on import: simply importing it
 * is enough to activate the prefix isolation.
 */

// ===== ТЕСТОВЫЙ РЕПОЗИТОРИЙ kip8test: изоляция localStorage =====
// localStorage общий для всего origin (bloknett-design.github.io).
// Чтобы настройки (тема, метод калибровки буя) из тестового репозитория
// не влияли на основной репозиторий kip8, добавляем префикс ко всем ключам.
// В основном репозитории kip8 этот блок ОТСУТСТВУЕТ — там ключи без префикса.

const PREFIX = 'kip8test:';
const origGetItem = localStorage.getItem.bind(localStorage);
const origSetItem = localStorage.setItem.bind(localStorage);
const origRemoveItem = localStorage.removeItem.bind(localStorage);

localStorage.getItem = function(key) { return origGetItem(PREFIX + key); };
localStorage.setItem = function(key, value) { return origSetItem(PREFIX + key, value); };
localStorage.removeItem = function(key) { return origRemoveItem(PREFIX + key); };
