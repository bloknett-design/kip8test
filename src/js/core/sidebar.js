/**
 * @module core/sidebar
 * @description Sidebar toggle, desktop sidebar, sidebar group accordion.
 * Extracted from the monolithic src/index.html (lines 11968–12203).
 */

function toggleSidebar() {
    let sidebar = document.getElementById('sidebar');
    let overlay = document.getElementById('sidebarOverlay');
    if (window.isDesktop()) {
        // На десктопе: закрываем sidebar (toggle)
        if (sidebar.classList.contains('desktop-open')) {
            sidebar.classList.remove('desktop-open');
            if (overlay) overlay.classList.remove('desktop-active');
        } else {
            sidebar.classList.add('desktop-open');
            if (overlay) overlay.classList.add('desktop-active');
        }
    } else {
        // На мобильном: стандартное поведение
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}

/** Десктоп: сворачивание/разворачивание sidebar */
function toggleDesktopSidebar() {
    if (!window.isDesktop()) return;
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!sidebar) return;
    const isOpen = sidebar.classList.contains('desktop-open');
    if (isOpen) {
        sidebar.classList.remove('desktop-open');
        if (overlay) overlay.classList.remove('desktop-active');
    } else {
        sidebar.classList.add('desktop-open');
        if (overlay) overlay.classList.add('desktop-active');
    }
    // Закрытие sidebar при клике на overlay
    if (!isOpen && overlay) {
        overlay.onclick = function() {
            sidebar.classList.remove('desktop-open');
            overlay.classList.remove('desktop-active');
        };
    }
}

/** Инициализация десктопного sidebar — по умолчанию скрыт */
function initDesktopSidebar() {
    if (!window.isDesktop()) return;
    // Sidebar скрыт по умолчанию — ничего не делаем
    // Обновляем активную вкладку в top bar
    if (typeof window.updateDesktopTopBarTabs === 'function') window.updateDesktopTopBarTabs();
    // Переместить connection indicator в десктопный бар
    const ci = document.getElementById('connectionIndicator');
    const barRight = document.querySelector('.desktop-top-bar-right');
    if (ci && barRight && !barRight.contains(ci)) {
        barRight.appendChild(ci);
    }
    // Клик по рабочей области (contentArea) закрывает sidebar
    const contentArea = document.getElementById('contentArea');
    if (contentArea && !contentArea._desktopSidebarCloseHandler) {
        contentArea._desktopSidebarCloseHandler = true;
        contentArea.addEventListener('click', function(e) {
            const sidebar = document.getElementById('sidebar');
            if (sidebar && sidebar.classList.contains('desktop-open')) {
                sidebar.classList.remove('desktop-open');
                const overlay = document.getElementById('sidebarOverlay');
                if (overlay) overlay.classList.remove('desktop-active');
            }
        });
    }
}

/** Обновление активной вкладки в десктопном верхнем баре */
function updateDesktopTopBarTabs() {
    const activePage = document.querySelector('.page-content.active');
    const currentPage = activePage ? activePage.id.replace('page-', '') : '';
    document.querySelectorAll('.desktop-top-bar-tab').forEach(tab => {
        const tabPage = tab.getAttribute('data-page');
        let isActive = false;
        if (tabPage === 'calculators') {
            isActive = ['calculators', 'calc-kipa', 'calc-electro', 'calc-geometry',
                'converter', 'scale-signal', 'error-select', 'buoy-select',
                'temp-sensors', 'orifice-select', 'circuit-breaker',
                'geo-circle', 'geo-ring', 'geo-cylinder', 'geo-horiz',
                'geo-sphere', 'geo-cone'].includes(currentPage);
        } else if (tabPage === 'docs') {
            isActive = ['docs', 'devices-prod', 'devices-type', 'devices-name',
                'device-detail', 'dev-group', 'lockouts-prod', 'lockout-detail',
                'lock-group', 'valves-prod', 'valve-detail', 'valve-group',
                'regulators-prod', 'regulator-detail', 'regulator-group',
                'projects-prod', 'project-detail', 'project-group',
                'cable-journal-edit', 'cable-journal-add', 'cable-journal-view',
                'kip-ios', 'library-internal', 'library-electro',
                'plan-114', 'exam-tickets', 'admin-users', 'admin-sessions',
                'admin-logs', 'admin-stats'].includes(currentPage);
        }
        tab.classList.toggle('active', isActive);
    });
}

// Аккордеон в боковом меню: при разворачивании группы — сворачиваем ранее раскрытую.
function toggleSidebarGroup(groupEl) {
    if (!groupEl) return;
    const isExpanded = groupEl.classList.contains('expanded');
    document.querySelectorAll('.sidebar-group.expanded').forEach(el => {
        if (el !== groupEl) {
            el.classList.remove('expanded');
        }
    });
    groupEl.classList.toggle('expanded', !isExpanded);
    if (navigator.vibrate) navigator.vibrate(15);
}

// Close sidebar when clicking outside
document.addEventListener('click', function(e) {
    let sidebar = document.getElementById('sidebar');
    let overlay = document.getElementById('sidebarOverlay');
    let menuBtn = document.getElementById('menuBtn');
    if (!sidebar || !overlay) return;
    if (sidebar.classList.contains('active')) {
        let clickedSidebar = sidebar.contains(e.target);
        let clickedMenuBtn = menuBtn && menuBtn.contains(e.target);
        if (!clickedSidebar && !clickedMenuBtn) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        }
    }
});

export {
    toggleSidebar,
    toggleDesktopSidebar,
    initDesktopSidebar,
    toggleSidebarGroup,
    updateDesktopTopBarTabs
};
