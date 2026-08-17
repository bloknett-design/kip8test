/**
 * @module core/navigation
 * @description Central navigation, page hierarchy, breadcrumbs, desktop layout utilities.
 * Extracted from the monolithic src/index.html (lines 9218–10002).
 */

// ============================================================
// ДЕСКТОПНЫЙ ЛЕЙАУТ: утилиты и master-detail
// ============================================================

/** Страницы, которые на десктопе открывают detail-panel вместо перехода */
const DESKTOP_DETAIL_PAGES = new Set([
    'device-detail', 'lockout-detail', 'valve-detail',
    'regulator-detail', 'project-detail', 'cable-journal-view',
    'flowmeter-detail'
]);

/** Страницы-списки (master), при клике в которых открывается detail */
const DESKTOP_MASTER_PAGES = new Set([
    'devices-prod', 'devices-type', 'devices-name',
    'dev-group',
    'lockouts-prod', 'lock-group',
    'valves-prod', 'valves-type', 'valves-name',
    'valve-group',
    'regulators-prod', 'regulator-group',
    'projects-prod', 'project-group',
    'cable-journal-edit',
    'tickets-1000v', 'tickets-4', 'tickets-5', 'tickets-6',
    'flowmeter-data'
]);

/** Открывает detail-panel с содержимым */
function openDetailPanel(title, contentHtml) {
    if (!window.isDesktop()) return;
    const panel = document.getElementById('detailPanel');
    const bodyEl = document.getElementById('detailPanelBody');
    if (!panel || !bodyEl) return;
    bodyEl.innerHTML = contentHtml || '';
    panel.classList.add('active');
    // Показываем полноэкранную строку breadcrumbs
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');
    // Подсветка активной карточки в списке
    document.querySelectorAll('.dev-card.detail-highlight, .lock-card.detail-highlight, .valve-card.detail-highlight, .regulator-card.detail-highlight, .project-card.detail-highlight, .ticket-list-item.detail-highlight, .flow-card.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
}

/** Закрывает detail-panel */
function closeDetailPanel() {
    const panel = document.getElementById('detailPanel');
    if (!panel) return;
    panel.classList.remove('active');
    document.getElementById('detailPanelBody').innerHTML = '';
    const footer = document.getElementById('detailPanelFooter');
    if (footer) footer.innerHTML = '';
    // Скрыть значок избранного в хедере десктоп-панели
    const favBtn = document.getElementById('detailPanelFavBtn');
    if (favBtn) favBtn.style.display = 'none';
    // Скрываем полноэкранную строку breadcrumbs
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) {
        bcBar.classList.remove('active');
        const bcContent = document.getElementById('detailBreadcrumbContent');
        if (bcContent) bcContent.innerHTML = '';
    }
    document.querySelectorAll('.dev-card.detail-highlight, .lock-card.detail-highlight, .valve-card.detail-highlight, .regulator-card.detail-highlight, .project-card.detail-highlight, .ticket-list-item.detail-highlight, .flow-card.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
    // Восстанавливаем breadcrumbs без виртуальной detail-страницы
    updateDesktopBreadcrumb();
}

/** Поменять местами левую и правую панели на десктопе. */
function swapDetailPanels() {
    const contentArea = document.getElementById('contentArea');
    if (!contentArea) return;
    contentArea.classList.toggle('panels-swapped');
    // Сохраняем состояние в localStorage
    try {
        if (contentArea.classList.contains('panels-swapped')) {
            localStorage.setItem('kip8_panels_swapped', '1');
        } else {
            localStorage.removeItem('kip8_panels_swapped');
        }
    } catch(e) {}
}

/** Восстановить сохранённое состояние панелей при загрузке. */
function restorePanelsSwapState() {
    try {
        if (localStorage.getItem('kip8_panels_swapped') === '1') {
            const contentArea = document.getElementById('contentArea');
            if (contentArea) contentArea.classList.add('panels-swapped');
        }
    } catch(e) {}
}

// Слушатель изменения размера окна — полная очистка при переходе между режимами
window.matchMedia('(min-width: 1024px)').addEventListener('change', function(e) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const ci = document.getElementById('connectionIndicator');
    const mainApp = document.getElementById('mainApp');
    const contentArea = document.getElementById('contentArea');

    if (!e.matches) {
        // === Переход на мобильный: полная очистка десктопного состояния ===
        closeDetailPanel();
        if (typeof _ticketSelectedIndex !== 'undefined') _ticketSelectedIndex = -1;
        // Снять swap-режим панелей
        if (contentArea) contentArea.classList.remove('panels-swapped');

        // Убрать десктопные классы sidebar
        if (sidebar) {
            sidebar.classList.remove('desktop-open');
            sidebar.classList.remove('active'); // на всякий случай
        }
        if (overlay) {
            overlay.classList.remove('desktop-active');
            overlay.classList.remove('active');
        }

        // Вернуть connection indicator в body (мобильная позиция — fixed)
        if (ci && ci.parentElement && ci.parentElement.classList.contains('desktop-top-bar-right')) {
            document.body.appendChild(ci);
            // Восстановить мобильные стили connection indicator
            ci.style.position = '';
            ci.style.top = '';
            ci.style.right = '';
            ci.style.zIndex = '';
        }

        // Очистить инлайн-стили, которые могли быть установлены десктопным JS
        if (mainApp) {
            mainApp.style.display = '';
            mainApp.style.height = '';
            mainApp.style.overflow = '';
        }
        if (contentArea) {
            contentArea.style.display = '';
            contentArea.style.overflow = '';
            contentArea.style.flex = '';
        }
        // Восстановить прокрутку body
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';
        document.body.style.height = '';
        document.documentElement.style.height = '';
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        // Снять блокировку прокрутки от билетов
        if (document.body.classList.contains('ticket-open')) {
            document.body.classList.remove('ticket-open');
            document.body.style.top = '';
            requestAnimationFrame(function() { window.scrollTo(0, (typeof _savedScrollY !== 'undefined' ? _savedScrollY : 0) || 0); });
        }
        if (document.body.classList.contains('ticket-img-viewing')) {
            document.body.classList.remove('ticket-img-viewing');
        }
        document.querySelectorAll('.ticket-item.open').forEach(item => item.classList.remove('open'));

    } else {
        // === Переход на десктоп: убрать мобильные классы, инициализировать ===
        if (sidebar) sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        if (typeof window.initDesktopSidebar === 'function') initDesktopSidebar();
    }
});


// ============================================================
// Навигация
// ============================================================
let pageHistory = [];
let isNavigating = false;

function navigateTo(page, addToHistory=true) {
    // Проверка доступа (если KipAuth инициализирован).
    if (typeof window.KipAuth !== 'undefined' && window.KipAuth._cachedRole && !window.KipAuth.canAccess(page)) {
        window.KipAuth._showNoAccess(page);
        return;
    }
    if (page === 'library') { navigateTo('library-internal'); return; }
    // Раздел "Кабельный журнал" объединён с редакторской версией:
    // единая страница — cable-journal-edit (роль с правом записи видит
    // UI редактирования, остальные — только просмотр).
    // Доступ к кабельному журналу (страницы cable-journal-*) —
    // всем ролям с доступом к КИП ИОС (просмотр).
    // Право записи (canEdit) — только КИП ИОС pro, ИТР ИОС и Админ
    // (определяется сервером в cableJournal.getColumns).
    // Любой переход на устаревший идентификатор 'cables' или 'cables-prod'
    // перенаправляется туда же.
    if (page === 'cables' || page === 'cables-prod') { navigateTo('cable-journal-edit'); return; }
    // Сброс активного фильтра «№ проекта» при уходе со страницы соответствующего раздела.
    // Карта: страница → раздел, к которому относится фильтр.
    // Если пользователь уходит не на «свою» страницу раздела и не на детальную —
    // фильтр считаем «зависшим» и сбрасываем.
    if (typeof window.kipProjectLinkFilter !== 'undefined' && window.kipProjectLinkFilter) {
        const sec = window.kipProjectLinkFilter.section;
        // Для devices разрешаем все 3 вкладки сортировки — фильтр должен
        // сохраняться при переключении между По типу / По наименованию / По производствам.
        const allowedPages = {
            devices:    ['devices-prod', 'devices-type', 'devices-name', 'device-detail', 'dev-group'],
            lockouts:   ['lockouts-prod', 'lockout-detail', 'lock-group'],
            valves:     ['valves-prod', 'valve-detail', 'valve-group'],
            regulators: ['regulators-prod', 'regulator-detail', 'regulator-group'],
        }[sec] || [];
        if (allowedPages.indexOf(page) === -1) {
            window.kipClearProjectLinkFilter(sec);
        }
    }
    // Сброс активного фильтра «№ СБС» при уходе со страницы соответствующего раздела.
    if (typeof window.kipSbsLinkFilter !== 'undefined' && window.kipSbsLinkFilter) {
        const sec = window.kipSbsLinkFilter.section;
        const allowedPages = {
            devices:    ['devices-prod', 'devices-type', 'devices-name', 'device-detail', 'dev-group'],
            valves:     ['valves-prod', 'valve-detail', 'valve-group'],
            regulators: ['regulators-prod', 'regulator-detail', 'regulator-group'],
        }[sec] || [];
        if (allowedPages.indexOf(page) === -1) {
            window.kipClearSbsLinkFilter(sec);
        }
    }
    // Сброс активного фильтра «№ САР» при уходе со страницы соответствующего раздела.
    if (typeof window.kipSarLinkFilter !== 'undefined' && window.kipSarLinkFilter) {
        const sec = window.kipSarLinkFilter.section;
        const allowedPages = {
            devices:    ['devices-prod', 'devices-type', 'devices-name', 'device-detail', 'dev-group'],
            valves:     ['valves-prod', 'valve-detail', 'valve-group'],
        }[sec] || [];
        if (allowedPages.indexOf(page) === -1) {
            window.kipClearSarLinkFilter(sec);
        }
    }
    if (page === 'minesweeper') { setTimeout(() => { if (typeof window.msInit === 'function') window.msInit(); }, 50); }
    if (page === 'phonebook') { setTimeout(() => { if (typeof window.pbInit === 'function') window.pbInit(); }, 30); }
    if (page === 'devices') { setTimeout(() => { if (typeof window.devInit === 'function') window.devInit(); }, 30); }
    if (page === 'devices-type') { setTimeout(() => { if (typeof window.devInitSorted === 'function') window.devInitSorted('type'); }, 30); }
    if (page === 'devices-name') { setTimeout(() => { if (typeof window.devInitSorted === 'function') window.devInitSorted('name'); }, 30); }
    if (page === 'devices-prod') { setTimeout(() => { if (typeof window.devInitSorted === 'function') window.devInitSorted('prod'); }, 30); }
    if (page === 'device-detail') { setTimeout(() => { if (typeof window.devRenderDetail === 'function') window.devRenderDetail(); }, 30); }
    if (page === 'lockouts-prod') { setTimeout(() => { if (typeof window.lockInitSorted === 'function') window.lockInitSorted('prod'); }, 30); }
    if (page === 'lockout-detail') { setTimeout(() => { if (typeof window.lockRenderDetail === 'function') window.lockRenderDetail(); }, 30); }
    if (page === 'valves-prod') { setTimeout(() => { if (typeof window.valveInitSorted === 'function') window.valveInitSorted('prod'); }, 30); }
    if (page === 'valves-type') { setTimeout(() => { if (typeof window.valveInitSorted === 'function') window.valveInitSorted('type'); }, 30); }
    if (page === 'valves-name') { setTimeout(() => { if (typeof window.valveInitSorted === 'function') window.valveInitSorted('name'); }, 30); }
    if (page === 'valve-detail') { setTimeout(() => { if (typeof window.valveRenderDetail === 'function') window.valveRenderDetail(); }, 30); }
    if (page === 'regulators-prod') { setTimeout(() => { if (typeof window.regulatorInitSorted === 'function') window.regulatorInitSorted('prod'); }, 30); }
    if (page === 'regulator-detail') { setTimeout(() => { if (typeof window.regulatorRenderDetail === 'function') window.regulatorRenderDetail(); }, 30); }
    if (page === 'dev-group') { setTimeout(() => { if (typeof window.devRenderGroup === 'function') window.devRenderGroup(); }, 30); }
    if (page === 'lock-group') { setTimeout(() => { if (typeof window.lockRenderGroup === 'function') window.lockRenderGroup(); }, 30); }
    if (page === 'valve-group') { setTimeout(() => { if (typeof window.valveRenderGroup === 'function') window.valveRenderGroup(); }, 30); }
    if (page === 'regulator-group') { setTimeout(() => { if (typeof window.regulatorRenderGroup === 'function') window.regulatorRenderGroup(); }, 30); }
    if (page === 'projects-prod') { setTimeout(() => { if (typeof window.projectInitSorted === 'function') window.projectInitSorted('prod'); }, 30); }
    if (page === 'project-detail') { setTimeout(() => { if (typeof window.projectRenderDetail === 'function') window.projectRenderDetail(); }, 30); }
    if (page === 'project-group') { setTimeout(() => { if (typeof window.projectsRenderGroup === 'function') window.projectsRenderGroup(); }, 30); }
    if (page === 'cable-journal-edit') { setTimeout(() => { if (typeof window.KipCableJournal !== 'undefined') window.KipCableJournal.init(); }, 30); }
    if (page === 'cable-journal-add')  { setTimeout(() => { if (typeof window.KipCableJournal !== 'undefined') window.KipCableJournal.initAddPage(); }, 30); }
    if (page === 'device-favorites') { setTimeout(() => { if (typeof window.KipFav !== 'undefined') window.KipFav.initFavoritesPage(); }, 30); }
    if (page === 'cable-journal-view') {
        if (window.isDesktop()) {
            // На десктопе: рендерим в detail-panel вместо перехода
            if (typeof window.cableRenderDetailInPanel === 'function') window.cableRenderDetailInPanel();
        } else {
            setTimeout(() => { if (typeof window.KipCableJournal !== 'undefined') window.KipCableJournal.initViewPage(); }, 30);
        }
    }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.devInitEntryButton === 'function') window.devInitEntryButton(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.kipIOSUpdateLastChange === 'function') window.kipIOSUpdateLastChange(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.lockInitEntryButton === 'function') window.lockInitEntryButton(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.valveInitEntryButton === 'function') window.valveInitEntryButton(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.regulatorInitEntryButton === 'function') window.regulatorInitEntryButton(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.projectsInitEntryButton === 'function') window.projectsInitEntryButton(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.cablesInitEntryButton === 'function') window.cablesInitEntryButton(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.plan114InitEntryButton === 'function') window.plan114InitEntryButton(); }, 30); }
    if (page === 'kip-ios') { setTimeout(() => { if (typeof window.KipCharts !== 'undefined') window.KipCharts.initEntryButton(); }, 30); }
    if (page === 'flowmeter-data') { setTimeout(() => { if (typeof window.FlowmeterData !== 'undefined') window.FlowmeterData.init(); }, 30); }
    if (page === 'plan-114') { setTimeout(() => { if (typeof window.plan114RenderList === 'function') window.plan114RenderList(); }, 30); }
    if (page === 'charts') { setTimeout(() => { if (typeof window.KipCharts !== 'undefined') window.KipCharts.onPageOpen(); }, 30); }
    if (typeof window.TICKET_IDS !== 'undefined' && window.TICKET_IDS.includes(page)) { setTimeout(() => window.initTicketsPage(page), 30); }
    if (page === 'exam-tickets') { setTimeout(() => { if (typeof window.loadTicketsData === 'function') window.loadTicketsData(); }, 30); }
    // ============================================================
    // Админ-панель: автоматическая загрузка данных при заходе на раздел.
    // ============================================================
    if (page === 'admin-users')    { setTimeout(() => { if (typeof window.KipAdmin !== 'undefined') window.KipAdmin.loadUsers();    }, 30); }
    if (page === 'admin-sessions') { setTimeout(() => { if (typeof window.KipAdmin !== 'undefined') window.KipAdmin.loadSessions(); }, 30); }
    if (page === 'admin-logs')     { setTimeout(() => { if (typeof window.KipAdmin !== 'undefined') window.KipAdmin.loadLogs();     }, 30); }
    if (page === 'admin-stats')    { setTimeout(() => { if (typeof window.KipAdmin !== 'undefined') window.KipAdmin.loadStats();    }, 30); }
    // Снять блокировку прокрутки и закрыть открытые билеты при уходе со страницы
    if (document.body.classList.contains('ticket-open')) {
        document.body.classList.remove('ticket-open');
        document.body.style.top = '';
        document.body.style.position = '';
        document.body.style.width = '';
        requestAnimationFrame(function() { window.scrollTo(0, (typeof _savedScrollY !== 'undefined' ? _savedScrollY : 0) || 0); });
    }
    // Закрыть overlay картинки билета, если открыт
    if (document.body.classList.contains('ticket-img-viewing')) {
        if (typeof window.closeTicketImage === 'function') window.closeTicketImage();
    }
    // Полная очистка инлайн-стилей, блокирующих прокрутку на мобильном
    // (могут остаться от десктопного режима при resize или от iOS scroll-lock)
    if (!window.isDesktop()) {
        if (document.body.style.overflow === 'hidden') document.body.style.overflow = '';
        if (document.documentElement.style.overflow === 'hidden') document.documentElement.style.overflow = '';
        if (document.body.style.position === 'fixed') { document.body.style.position = ''; document.body.style.top = ''; document.body.style.width = ''; }
        var _bh = document.body.style.height; if (_bh === '100%' || _bh === '100vh') document.body.style.height = '';
        var _dh = document.documentElement.style.height; if (_dh === '100%' || _dh === '100vh') document.documentElement.style.height = '';
    }
    // Закрыть все открытые билеты при навигации на другую страницу
    document.querySelectorAll('.ticket-item.open').forEach(item => {
        item.classList.remove('open');
        const body = item.querySelector('.ticket-item-body');
        if (body) body.scrollTop = 0;
    });
    // Очистить нижний бар кабельного журнала при уходе со страницы
    if (page !== 'cable-journal-view') {
        const cjBar = document.getElementById('cjViewBottomBar');
        if (cjBar) cjBar.innerHTML = '';
    }
    if (page !== 'cable-journal-add') {
        const cjAddBar = document.getElementById('cjAddBottomBar');
        if (cjAddBar) cjAddBar.innerHTML = '';
    }
    let active = document.querySelector('.page-content.active');
    let currentPageId = active ? active.id.replace('page-', '') : 'dashboard';
    if (active && addToHistory) { if (currentPageId !== page) pageHistory.push(currentPageId); }
    // === Десктоп: detail-страницы -> detail-panel вместо перехода ===
    if (window.isDesktop() && DESKTOP_DETAIL_PAGES.has(page)) {
        // На десктопе: не переключаем страницу, а рендерим в detail-panel
        // Вызываем соответствующий InPanel-рендерер
        if (page === 'device-detail') { setTimeout(() => { if (typeof window.devRenderDetailInPanel === 'function') window.devRenderDetailInPanel(); }, 30); }
        else if (page === 'lockout-detail') { setTimeout(() => { if (typeof window.lockRenderDetailInPanel === 'function') window.lockRenderDetailInPanel(); }, 30); }
        else if (page === 'valve-detail') { setTimeout(() => { if (typeof window.valveRenderDetailInPanel === 'function') window.valveRenderDetailInPanel(); }, 30); }
        else if (page === 'regulator-detail') { setTimeout(() => { if (typeof window.regulatorRenderDetailInPanel === 'function') window.regulatorRenderDetailInPanel(); }, 30); }
        else if (page === 'project-detail') { setTimeout(() => { if (typeof window.projectRenderDetailInPanel === 'function') window.projectRenderDetailInPanel(); }, 30); }
        else if (page === 'cable-journal-view') { setTimeout(() => { if (typeof window.cableRenderDetailInPanel === 'function') window.cableRenderDetailInPanel(); }, 30); }
        else if (page === 'flowmeter-detail') { setTimeout(() => { if (typeof window.flowmeterRenderDetailInPanel === 'function') window.flowmeterRenderDetailInPanel(); }, 30); }
        else {
            // Для неизвестных detail-страниц — просто открываем пустую панель
            const panel = document.getElementById('detailPanel');
            if (panel) panel.classList.add('active');
            const bcBar = document.getElementById('detailBreadcrumbBar');
            if (bcBar) bcBar.classList.add('active');
        }
        // Обновляем breadcrumbs с виртуальной detail-страницей в конце пути
        updateDesktopBreadcrumb(page);
        return;
    }
    document.querySelectorAll('.page-content').forEach(el => { el.classList.remove('active', 'visible'); });
    // На десктопе: при навигации на обычную страницу закрыть detail-панель
    if (window.isDesktop()) closeDetailPanel();
    // Сбросить состояние прокрутки при переходе на новую страницу
    document.querySelectorAll('.page-content.scrolled').forEach(el => el.classList.remove('scrolled'));
    let target = document.getElementById('page-' + page);
    if (target) { target.classList.add('active'); requestAnimationFrame(() => { requestAnimationFrame(() => target.classList.add('visible')); }); }
    // Обновить активную вкладку в десктопном верхнем баре
    if (typeof window.updateDesktopTopBarTabs === 'function') window.updateDesktopTopBarTabs();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (page === 'buoy-calc') { if (typeof window.updateBuoyCalcTitle === 'function') window.updateBuoyCalcTitle(); if (typeof window.setCalibMethodOnForm === 'function') window.setCalibMethodOnForm(); }
    // Обернуть карточки подразделов для swipe-to-add на страницах меню подразделов
    if (page === 'calculators' || page === 'calc-kipa' || page === 'calc-electro' || page === 'calc-geometry' || page === 'docs' || page === 'kip-ios' || page === 'docs-ios' || page === 'flowmeter-data') {
        if (typeof window.wrapSubsectionItems === 'function') window.wrapSubsectionItems('page-' + page);
    }
    updateBottomNavActive(page);
    // Toggle global app-header visibility
    let appHeader = document.querySelector('.app-header');
    if (appHeader) appHeader.style.display = (page === 'dashboard') ? 'block' : 'none';
    // Sync browser history
    if (addToHistory && !isNavigating) {
        history.pushState({ page: page }, '', '#' + page);
    }
    // При переходе на главную — очистить внутреннюю историю навигации,
    // чтобы шеврон на дочерних страницах показывал корректное число стрелок
    // после возврата на главную (двойной тап по шеврону или popstate).
    if (page === 'dashboard') {
        pageHistory = [];
    }
    // Обновить количество стрелок шеврона в заголовке активной страницы
    updateChevronArrows();
    // Обновить хлебные крошки в десктопной версии
    updateDesktopBreadcrumb();
    // Адаптивная подгонка заголовка активной страницы (уменьшение шрифта
    // или увеличение высоты бара, если текст не помещается).
    if (typeof window.fitPageHeaderTitle === 'function') {
        // Сразу после активации page-content, чтобы измерения были корректны.
        window.fitPageHeaderTitle();
        // Повтор через 2 RAF — layout успевает досчитаться полностью.
        requestAnimationFrame(function() {
            requestAnimationFrame(window.fitPageHeaderTitle);
        });
        // И финальный пересчёт после завершения плавного скролла наверх.
        setTimeout(window.fitPageHeaderTitle, 350);
    }
    isNavigating = false;
}

function updateBottomNavActive(page) {
    let map = {'converter':0,'scale-signal':1,'error-select':2,'buoy-select':3,'library':4};
    let idx = map[page];
    document.querySelectorAll('.bottom-nav-item').forEach((el, i) => { el.classList.toggle('active', i === idx); });
}

function goBack() {
    let active = document.querySelector('.page-content.active');
    let currentPageId = active ? active.id.replace('page-', '') : 'dashboard';
    if (currentPageId === 'dashboard') {
        // На главной — выйти из сайта
        if (pageHistory.length) { pageHistory = []; }
        window.close();
        // window.close() работает только для окон, открытых скриптом.
        // Для обычных вкладок — пытаемся перейти назад в браузере
        history.back();
        return;
    }
    // Только history.back() — навигацию выполнит обработчик popstate
    history.back();
}

// ===== Шевроны в заголовке: 1 тап = назад, 2 тапа = на главную =====
let chevronTapCount = 0;
let chevronTapTimer = null;
const CHEVRON_DOUBLE_TAP_DELAY = 300; // мс

function chevronTap() {
    chevronTapCount++;
    if (navigator.vibrate) navigator.vibrate(10);
    clearTimeout(chevronTapTimer);
    if (chevronTapCount === 1) {
        // Ждём — может быть второй тап
        chevronTapTimer = setTimeout(() => {
            // Одиночный тап — назад
            goBack();
            chevronTapCount = 0;
        }, CHEVRON_DOUBLE_TAP_DELAY);
    } else if (chevronTapCount === 2) {
        // Двойной тап — на главную
        clearTimeout(chevronTapTimer);
        chevronTapCount = 0;
        if (navigator.vibrate) navigator.vibrate([10, 30, 10]);
        navigateTo('dashboard');
    }
}

// ===== Просмотр PDF из Google Drive (раздел «Библиотека») =====
// Внутренний просмотрщик удалён (Task 67) — все PDF-карточки в разделах
// «Библиотека КИП и А» / «Электробезопасность» теперь открываются прямыми
// ссылками <a href="https://drive.google.com/file/d/FILE_ID/view" target="_blank">
// в новой вкладке браузера. Эта функция оставлена как заглушка-редирект —
// на случай, если где-то остался вызов openLibraryViewer() (например, в
// закэшированной старой версии страницы). При вызове открывает файл
// напрямую в новой вкладке.
function openLibraryViewer(fileId, title) {
    if (!fileId) return;
    if (navigator.vibrate) navigator.vibrate(10);
    const url = 'https://drive.google.com/file/d/' + encodeURIComponent(fileId) + '/view';
    window.open(url, '_blank', 'noopener');
}

// ===== Динамическое количество стрелок шеврона "Назад" =====
// Глубина навигации = pageHistory.length (число переходов назад до главной).
// На странице с глубиной 1 — одна стрелка, 2 — две, 3 — три, 4+ — четыре (кап).
// SVG-разметка та же, что использовалась в захардкоженных шевронах.
// Стрелки очень компактные (14×14px) и плотно сгруппированы (margin-left:-8px),
// чтобы визуально занимать минимум места в углу бара поверх заголовка.
function updateChevronArrows() {
    try {
        const active = document.querySelector('.page-content.active');
        if (!active) return;
        const chevron = active.querySelector('.page-inline-header-chevron');
        if (!chevron) return;
        const n = Math.min(Math.max(pageHistory.length, 0), 4);
        // Сгенерировать n SVG-стрелок. Первая — без margin, остальные с margin-left:-8px.
        let html = '';
        for (let i = 0; i < n; i++) {
            const style = (i === 0) ? '' : ' style="margin-left:-8px;"';
            html += '<svg viewBox="0 0 24 24"' + style + '><polyline points="15 18 9 12 15 6"/></svg>';
        }
        // Если n === 0 (например, мы на главной, но там нет chevron — этот случай не наступит),
        // оставляем пусто.
        chevron.innerHTML = html;
    } catch (e) {
        // Тихо игнорируем — обновление шеврона не должно ломать навигацию.
    }
}

// ============================================================
// ХЛЕБНЫЕ КРОШКИ (breadcrumb) — десктопная версия
// ============================================================
// Иерархическая навигация: каждая страница знает своего родителя.
// Путь строится снизу вверх: текущая → родитель → ... → корень.
// При переходе в другой раздел автоматически начинается новая ветка.

// Карта: страница → её родитель в иерархии
const PAGE_PARENTS = {
    // Верхний уровень (корневые разделы)
    'calculators':      'dashboard',
    'docs':             'dashboard',
    'phonebook':        'dashboard',
    'admin':            'dashboard',
    // Инженерные калькуляторы
    'calc-kipa':        'calculators',
    'calc-electro':     'calculators',
    'calc-geometry':    'calculators',
    'minesweeper':      'calculators',
    // КИП и А — подразделы
    'converter':        'calc-kipa',
    'scale-signal':     'calc-kipa',
    'error-select':     'calc-kipa',
    'buoy-select':      'calc-kipa',
    'temp-sensors':     'calc-kipa',
    'orifice-select':   'calc-kipa',
    // Конвертер единиц — категории
    'conv-pressure':    'converter',
    'conv-flow':        'converter',
    'conv-mass':        'converter',
    'conv-temp':        'converter',
    'conv-length':      'converter',
    'conv-density':     'converter',
    'conv-time':        'converter',
    'conv-volume':      'converter',
    // Расчёт погрешности — подразделы
    'error-pressure':       'error-select',
    'error-temp-rtd':       'error-select',
    'error-temp-tc':        'error-select',
    'error-flow':           'error-select',
    'error-level':          'error-select',
    'error-scale':          'error-select',
    'error-generic':        'error-select',
    'error-kit':            'error-select',
    // Погрешность по классу точности
    'error-generic-number':     'error-generic',
    'error-generic-underline':  'error-generic',
    'error-generic-circle':     'error-generic',
    'error-generic-fraction':   'error-generic',
    // Буйковый уровнемер
    'buoy-calc':            'buoy-select',
    // Сужающее устройство
    'orifice-quick':        'orifice-select',
    'orifice-dp':           'orifice-select',
    'orifice-flow':         'orifice-select',
    'orifice-diameter':     'orifice-select',
    // Электротехника
    'circuit-breaker':      'calc-electro',
    // Геометрия
    'geo-circle':       'calc-geometry',
    'geo-ring':         'calc-geometry',
    'geo-cylinder':     'calc-geometry',
    'geo-horiz':        'calc-geometry',
    'geo-sphere':       'calc-geometry',
    'geo-cone':         'calc-geometry',
    // Документация — подразделы
    'exam-tickets':     'docs',
    'library':          'docs',
    'library-internal': 'docs',
    'library-electro':  'library-internal',
    'kip-ios':          'docs',
    'docs-ios':         'docs',
    'flowmeter-data':   'docs-ios',
    'flowmeter-detail': 'flowmeter-data',
    // Экзаменационные билеты
    'tickets-1000v':    'exam-tickets',
    'tickets-4':        'exam-tickets',
    'tickets-5':        'exam-tickets',
    'tickets-6':        'exam-tickets',
    // КИП ИОС — подразделы
    'devices-type':     'kip-ios',
    'devices-name':     'kip-ios',
    'devices-prod':     'kip-ios',
    'devices':          'kip-ios',
    'device-detail':    'devices-prod',
    'device-favorites': 'dashboard',
    'dev-group':        'devices-prod',
    'lockouts-prod':    'kip-ios',
    'lockout-detail':   'lockouts-prod',
    'lock-group':       'lockouts-prod',
    'valves-type':      'kip-ios',
    'valves-name':      'kip-ios',
    'valves-prod':      'kip-ios',
    'valve-detail':     'valves-prod',
    'valve-group':      'valves-prod',
    'regulators-prod':  'kip-ios',
    'regulator-detail': 'regulators-prod',
    'regulator-group':  'regulators-prod',
    'projects-prod':    'kip-ios',
    'project-detail':   'projects-prod',
    'project-group':    'projects-prod',
    'cable-journal-edit':   'kip-ios',
    'cable-journal-add':    'cable-journal-edit',
    'cable-journal-view':   'cable-journal-edit',
    'plan-114':         'kip-ios',
    'plan-114-view':    'plan-114',
    'charts':           'kip-ios',
    // Админ-панель
    'admin-users':      'admin',
    'admin-sessions':   'admin',
    'admin-logs':       'admin',
    'admin-stats':      'admin'
};

// Карта: идентификатор → читаемое название для breadcrumbs
const PAGE_LABELS = {
    'dashboard':        'Главная',
    'calculators':      'Инженерные калькуляторы',
    'docs':             'Документация',
    'calc-kipa':        'КИП и А',
    'calc-electro':     'Электротехника',
    'calc-geometry':    'Геометрия',
    'kip-ios':          'КИП ИОС',
    'docs-ios':         'Документация ИОС',
    'flowmeter-data':   'Расходомеры хозрасчётные',
    'flowmeter-detail': 'Расходомер',
    'exam-tickets':     'Экзаменационные билеты',
    'tickets-1000v':    'Билеты до 1000 В',
    'tickets-4':        'Билеты на 4 разряд',
    'tickets-5':        'Билеты на 5 разряд',
    'tickets-6':        'Билеты на 6 разряд',
    'library':          'Библиотека КИП и А',
    'library-internal': 'Библиотека КИП и А',
    'library-electro':  'Электробезопасность',
    'devices':          'Приборы',
    'devices-type':     'Приборы по типу',
    'devices-name':     'Приборы по наименованию',
    'devices-prod':     'Приборы по производствам',
    'device-detail':    'Прибор',
    'device-favorites': 'Избранное',
    'dev-group':        'Группа приборов',
    'lockouts-prod':    'Блокировки',
    'lockout-detail':   'Блокировка',
    'lock-group':       'Группа блокировок',
    'valves-type':      'Клапана по типу',
    'valves-name':      'Клапана по DN',
    'valves-prod':      'Клапана по производствам',
    'valve-detail':     'Клапан',
    'valve-group':      'Группа клапанов',
    'regulators-prod':  'Регуляторы',
    'regulator-detail': 'Регулятор',
    'regulator-group':  'Группа регуляторов',
    'projects-prod':    'Проекты',
    'project-detail':   'Проект',
    'project-group':    'Группа проектов',
    'cable-journal-edit':   'Кабельный журнал',
    'cable-journal-add':    'Новая запись',
    'cable-journal-view':   'Запись',
    'plan-114':         'План корпуса 114',
    'plan-114-view':    'План',
    'charts':           'Графики КИП ИОС',
    'converter':        'Конвертер единиц',
    'conv-pressure':    'Давление',
    'conv-flow':        'Расход',
    'conv-mass':        'Вес и масса',
    'conv-temp':        'Температура',
    'conv-length':      'Длина и расстояние',
    'conv-density':     'Плотность',
    'conv-time':        'Время',
    'conv-volume':      'Объём',
    'scale-signal':     'Шкала-сигнал',
    'circuit-breaker':  'Автоматический выключатель',
    'geo-circle':       'Круг',
    'geo-ring':         'Кольцо',
    'geo-cylinder':     'Цилиндр вертикальный',
    'geo-horiz':        'Цилиндр горизонтальный',
    'geo-sphere':       'Сфера',
    'geo-cone':         'Конус',
    'orifice-select':   'Сужающее устройство',
    'whats-new':        'Что нового',
    'orifice-quick':    'Быстрый расчёт диафрагмы',
    'orifice-dp':       'Перепад давления Δp',
    'orifice-flow':     'Расход среды Q',
    'orifice-diameter': 'Сужающее устройство',
    'error-select':     'Расчёт погрешности',
    'error-pressure':   'Датчики давления',
    'error-temp-rtd':   'Термопреобразователи',
    'error-temp-tc':    'Термопары',
    'error-flow':       'Расходомеры',
    'error-level':      'Уровнемеры',
    'error-scale':      'Весы',
    'error-generic':    'По классу точности',
    'error-generic-number':    'Приведённая γ — число',
    'error-generic-underline': 'Приведённая γ — число с подчёркиванием',
    'error-generic-circle':    'Относительная δ — число в кружке',
    'error-generic-fraction':  'Относительная δ — дробь c/d',
    'error-kit':        'Комплект приборов',
    'buoy-select':      'Буйковый уровнемер',
    'buoy-calc':        'Буйковый уровнемер',
    'temp-sensors':     'Датчики температуры',
    'minesweeper':      'Сапёр',
    'phonebook':        'Телефонный справочник',
    'admin':            'Админ-панель',
    'admin-users':      'Пользователи',
    'admin-sessions':   'Активные сессии',
    'admin-logs':       'Журнал событий',
    'admin-stats':      'Статистика'
};

// Строит иерархический путь от корня до текущей страницы.
// Использует PAGE_PARENTS: поднимается от текущей страницы до корня,
// затем разворачивает путь сверху вниз.
// Формат: «Главная / Инженерные калькуляторы / КИП и А / Конвертер единиц»
function buildBreadcrumbPath(pageId) {
    if (pageId === 'dashboard') return [];

    const path = [];
    let current = pageId;
    const visited = new Set(); // защита от циклов

    while (current && current !== 'dashboard' && !visited.has(current)) {
        visited.add(current);
        path.unshift(current); // добавляем в начало
        current = PAGE_PARENTS[current] || null;
    }

    return path; // порядок: от корневого раздела до текущей страницы
}

// Обновляет хлебные крошки в заголовке страницы (только десктоп).
// Каждый сегмент, кроме последнего, кликабелен и ведёт на соответствующую страницу.
// Параметр virtualPage — виртуальная страница (например, 'device-detail'),
// добавляемая в конец пути, если detail-панель открыта поверх текущей страницы.
// customCurrentLabel — если задана, заменяет метку последнего сегмента
//   (например, реальное название группы вместо «Группа приборов»).
function updateDesktopBreadcrumb(virtualPage, customCurrentLabel) {
    if (!window.matchMedia('(min-width: 1024px)').matches) return;

    const active = document.querySelector('.page-content.active');
    if (!active) return;

    const currentPage = active.id.replace('page-', '');
    if (currentPage === 'dashboard' && !virtualPage) return; // на главной крошки не нужны

    const titleEl = active.querySelector('.page-inline-header-title');
    if (!titleEl) return;

    // Сохраняем подзаголовок (если есть — например, у «Библиотека КИП и А»)
    const subEl = titleEl.querySelector('.page-inline-header-subtitle');
    const subHtml = subEl ? subEl.outerHTML : '';

    // Строим иерархический путь по дереву PAGE_PARENTS
    // Если есть виртуальная страница (detail-панель) — строим путь до неё
    const targetPage = virtualPage || currentPage;
    const path = buildBreadcrumbPath(targetPage);

    // Если текущая страница — dashboard и есть virtualPage,
    // путь уже содержит полный маршрут от корня
    const startLabel = (currentPage === 'dashboard' && virtualPage) ? '' :
        '<span class="breadcrumb-link" onclick="navigateTo(\'dashboard\', false)">Главная</span>';

    // Строим HTML крошек: «Главная / Раздел / ... / Текущая»
    let html = startLabel;

    for (let i = 0; i < path.length; i++) {
        const pageId = path[i];
        // Последний сегмент: используем customCurrentLabel если задана
        const isLast = (i === path.length - 1);
        const label = (isLast && customCurrentLabel) ? customCurrentLabel : (PAGE_LABELS[pageId] || pageId);
        html += '<span class="breadcrumb-sep"> / </span>';

        if (!isLast) {
            // Кликабельный сегмент — ведёт на страницу
            html += '<span class="breadcrumb-link" onclick="navigateTo(\'' + pageId + '\', false)">' + label + '</span>';
        } else {
            // Текущая страница — не кликабельна, жирный шрифт
            html += '<span class="breadcrumb-current">' + label + '</span>';
        }
    }

    // Если есть подзаголовок — сохраняем его
    if (subHtml) {
        html += subHtml;
    }

    titleEl.innerHTML = html;
}

// ============================================================
// SUBSECTIONS registry — used by pinned.js and pin-sheet.js
// ============================================================
const SUBSECTIONS = {
    // ===== Главные разделы =====
    'calculators':   { label: 'Инженерные калькуляторы', sublabel: 'Конвертеры, погрешности, геометрия',             target: 'calculators',    category: 'calculators' },
    'docs':          { label: 'Документация',            sublabel: 'Билеты, библиотека, КИП ИОС',                    target: 'docs',           category: 'docs' },
    // ===== Калькуляторы — разделы (страница page-calculators) =====
    'calc-kipa':     { label: 'КИП и А',                  sublabel: 'Конвертеры, погрешности, датчики, диафрагмы',   target: 'calc-kipa',      category: 'calculators' },
    'calc-electro':  { label: 'Электротехника',           sublabel: 'Автоматический выключатель',                     target: 'calc-electro',   category: 'calculators' },
    'calc-geometry': { label: 'Геометрия',                sublabel: 'Площади, объёмы, сечения',                       target: 'calc-geometry',  category: 'calculators' },
    // ===== КИП и А — подразделы (страница page-calc-kipa) =====
    'converter':      { label: 'Конвертер единиц',          sublabel: 'Давление, расход, температура и др.',           target: 'converter',      category: 'calculators' },
    'scale-signal':   { label: 'Шкала-сигнал',              sublabel: 'Расчёт диапазонов шкалы и сигнала',             target: 'scale-signal',   category: 'calculators' },
    'error-select':   { label: 'Расчёт погрешности',        sublabel: 'ГОСТ 8.401-80, ГОСТ OIML R 76-1-2011, ТС, ТП',  target: 'error-select',   category: 'calculators' },
    'buoy-select':    { label: 'Буйковый уровнемер',        sublabel: 'Калибровка, выталкивающая сила',                target: 'buoy-select',    category: 'calculators' },
    'temp-sensors':   { label: 'Датчики температуры',       sublabel: 'Расчёт R и мВ по температуре (°C)',             target: 'temp-sensors',   category: 'calculators' },
    'orifice-select': { label: 'Сужающее устройство',       sublabel: 'Расчёт диафрагмы по расходу и перепаду',        target: 'orifice-select', category: 'calculators' },
    // ===== Электротехника — подразделы (страница page-calc-electro) =====
    'circuit-breaker':{ label: 'Автоматический выключатель', sublabel: 'Расчёт по мощности, току, сечению кабеля',     target: 'circuit-breaker',category: 'calculators' },
    // ===== Геометрия — подразделы (страница page-calc-geometry) =====
    'geo-circle':    { label: 'Круг',                    sublabel: 'Площадь, периметр, радиус',                     target: 'geo-circle',    category: 'calculators' },
    'geo-ring':      { label: 'Кольцо',                  sublabel: 'Площадь сечения, эквивалентный диаметр',        target: 'geo-ring',      category: 'calculators' },
    'geo-cylinder':  { label: 'Цилиндр вертикальный',    sublabel: 'Объём, площадь поверхности',                    target: 'geo-cylinder',  category: 'calculators' },
    'geo-horiz':     { label: 'Цилиндр горизонтальный',  sublabel: 'Объём жидкости при частичном заполнении',       target: 'geo-horiz',     category: 'calculators' },
    'geo-sphere':    { label: 'Сфера',                   sublabel: 'Объём, площадь поверхности',                    target: 'geo-sphere',    category: 'calculators' },
    'geo-cone':      { label: 'Конус',                   sublabel: 'Объём, образующая, площадь',                    target: 'geo-cone',      category: 'calculators' },
    // ===== Документация — разделы (страница page-docs) =====
    'exam-tickets':  { label: 'Экзаменационные билеты',  sublabel: '4, 5, 6 разряд, до 1000 В',                      target: 'exam-tickets',  category: 'docs' },
    'library':       { label: 'Библиотека КИП и А',      sublabel: 'Документация, схемы, инструкции',                target: 'library',       category: 'docs' },
    'kip-ios':       { label: 'КИП ИОС',                  sublabel: 'Перечень приборов, документация',               target: 'kip-ios',       category: 'docs' },
    'docs-ios':      { label: 'Документация ИОС',         sublabel: 'Документация и оперативные данные',              target: 'docs-ios',      category: 'docs' },
    // ===== Документация ИОС — подразделы (страница page-docs-ios) =====
    'flowmeter-data': { label: 'Расходомеры хозрасчётные', sublabel: 'Накопительные расходы и показания',             target: 'flowmeter-data',category: 'docs' },
    // ===== КИП ИОС — подразделы (страница page-kip-ios) =====
    'devices':       { label: 'Приборы',                  sublabel: 'Перечень КИП ИОС — 1312 приборов',              target: 'devices',       category: 'docs' },
    'lockouts':      { label: 'Блокировки',               sublabel: 'По производствам',                               target: 'lockouts-prod', category: 'docs' },
    'valves':        { label: 'Клапана',                  sublabel: 'По производствам',                               target: 'valves-prod',   category: 'docs' },
    'regulators':    { label: 'Регуляторы',               sublabel: 'По производствам',                               target: 'regulators-prod',category: 'docs' },
    'projects':      { label: 'Проекты',                  sublabel: 'Перечень проектов КИП пр-ва ИОС',               target: 'projects',      category: 'docs' },
    'cables':        { label: 'Кабельный журнал',        sublabel: 'Кабельный журнал КИП пр-ва ИОС',                 target: 'cable-journal-edit', category: 'docs' },
    'plan-114':      { label: 'План корпуса 114',        sublabel: '6 планов помещений',                             target: 'plan-114',      category: 'docs' },
    'charts':        { label: 'Графики',                  sublabel: 'Статистика КИП ИОС',                             target: 'charts',        category: 'docs' },
    'favorites':     { label: 'Избранное',                sublabel: 'Закладки и заметки',                             target: 'device-favorites', category: 'docs' }
};

// ============================================================
// Exports
// ============================================================
export {
    DESKTOP_DETAIL_PAGES,
    DESKTOP_MASTER_PAGES,
    CHEVRON_DOUBLE_TAP_DELAY,
    PAGE_PARENTS,
    PAGE_LABELS,
    SUBSECTIONS,
    pageHistory,
    isNavigating,
    chevronTapCount,
    chevronTapTimer,
    navigateTo,
    goBack,
    chevronTap,
    openDetailPanel,
    closeDetailPanel,
    swapDetailPanels,
    restorePanelsSwapState,
    openLibraryViewer,
    updateChevronArrows,
    buildBreadcrumbPath,
    updateDesktopBreadcrumb,
    updateBottomNavActive
};
