/**
 * @module whats-new
 * @description What's New tracking (unread updates badge) and About Modal.
 * Extracted from src/index.html (lines ~21289-21337, 3rd script block).
 *
 * External dependencies (temporary window bridges):
 *   - navigateTo  (will be imported from core/navigation once available)
 */

// ============================================================
// ABOUT MODAL
// ============================================================
function showAboutModal() {
    document.getElementById('aboutModalOverlay').classList.add('active');
}

function closeAboutModal() {
    document.getElementById('aboutModalOverlay').classList.remove('active');
}

// ============================================================
// «ЧТО НОВОГО» — отслеживание прочитанных обновлений
// ============================================================
// Текущая версия приложения (при обновлении — увеличить, чтобы значок стал красным)
const WHATS_NEW_VERSION = '3.1.0';
const WHATS_NEW_READ_KEY = 'kip8_whats_new_read_v';

/** Пометить текущую версию как прочитанную */
function whatsNewMarkRead() {
    try {
        localStorage.setItem(WHATS_NEW_READ_KEY + WHATS_NEW_VERSION, '1');
    } catch (e) {}
    whatsNewUpdateBtnState();
}

/** Проверить, есть ли непрочитанные обновления */
function whatsNewHasUnread() {
    try {
        return !localStorage.getItem(WHATS_NEW_READ_KEY + WHATS_NEW_VERSION);
    } catch (e) { return true; }
}

/** Обновить состояние кнопки-значка (красная анимация при непрочитанных) */
function whatsNewUpdateBtnState() {
    const hasUnread = whatsNewHasUnread();
    const btns = document.querySelectorAll('.whats-new-btn');
    btns.forEach(function(btn) {
        btn.classList.toggle('has-unread', hasUnread);
    });
}

// При загрузке страницы — обновить состояние кнопки
whatsNewUpdateBtnState();

// ========================
// Public exports
// ========================
export {
    showAboutModal,
    closeAboutModal,
    whatsNewMarkRead,
    whatsNewHasUnread,
    whatsNewUpdateBtnState,
    WHATS_NEW_VERSION,
    WHATS_NEW_READ_KEY
};
