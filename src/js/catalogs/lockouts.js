/**
 * @module catalogs/lockouts
 * @description Lockouts (Блокировки) catalog — data loading, rendering, search,
 * sorted/grouped views, detail card, and entry button.
 *
 * External dependencies (accessed via `window.*`):
 *   navigateTo, showToast, KipFav, isDesktop, parseLocaleNumber, formatNumber,
 *   lockRenderDetailInPanel, openDetailPanel, closeDetailPanel,
 *   kipIsEmptyProjectNo, kipSplitProjectValues, kipRenderMultiLinks,
 *   kipIsEmptySbsNo,
 *   kipIsProjectLinkFilterActive, kipClearProjectLinkFilter, kipMatchesProjectFilter,
 *   kipRenderFilterBadge, kipBindFilterBadge,
 *   kipProjectLinkFilter,
 *   kipRenderSbsRelatedBlock, kipLoadAndUpdateSbsRelated,
 *   projectOpenByProjectNo,
 *   updateDesktopBreadcrumb
 */

// ===== БЛОКИРОВКИ =====
// Поля соответствуют листу "Блокировки_app" таблицы Google Sheets
// https://docs.google.com/spreadsheets/d/1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy/edit (тот же файл, что и для приборов)
const LOCK_FIELDS = [
    { key: 'Параметр', label: 'Параметр', group: 1, hiddenInCard: true },
    { key: 'Производство', label: 'Производство', group: 1 },
    { key: 'Назначение', label: 'Назначение', group: 2 },
    { key: 'Расположение', label: 'Расположение', group: 2 },
    { key: 'Уставка', label: 'Уставка', group: 3 },
    { key: 'Значение сигнала', label: 'Значение сигнала', group: 3 },
    { key: '№ СБС', label: '№ СБС', group: 3 },
    { key: '№ проекта', label: '№ проекта', group: 4 },
    { key: 'Дата проверки', label: 'Дата проверки', group: 4 },
    { key: 'В перечне', label: 'В перечне', group: 4 },
    { key: 'Примечания', label: 'Примечания', group: 5 },
    { key: 'Замечания', label: 'Замечания', group: 5 },
];
let lockData = null;
let lockLoaded = false;
let lockGroupExpanded = {};

function lockEsc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function lockNorm(s) {
    if (s == null) return '';
    return String(s).toLowerCase().replace(/[ё]/g, 'е').replace(/[^a-zа-я0-9]/gi, '');
}
function lockMark(text, query) {
    if (!query) return lockEsc(text);
    const t = String(text);
    const q = lockNorm(query);
    if (!q) return lockEsc(t);
    const idx = lockNorm(t).indexOf(q);
    if (idx === -1) return lockEsc(t);
    const before = t.substring(0, idx);
    const match = t.substring(idx, idx + q.length);
    const after = t.substring(idx + q.length);
    return lockEsc(before) + '<mark>' + lockEsc(match) + '</mark>' + lockMark(after, query);
}
function lockPlural(n, forms) {
    const m = n % 100;
    const m1 = m % 10;
    if (m >= 5 && m <= 20) return forms[2];
    if (m1 === 1) return forms[0];
    if (m1 >= 2 && m1 <= 4) return forms[1];
    return forms[2];
}
function lockFormatDate(dateVal) {
    if (!dateVal) return '';
    const num = parseFloat(dateVal);
    if (!isNaN(num) && num > 30000) {
        const epoch = new Date(1899, 11, 30);
        const d = new Date(epoch.getTime() + num * 86400000);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        return day + '.' + month + '.' + year;
    }
    const str = String(dateVal).trim();
    const m = str.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m) return m[3] + '.' + m[2] + '.' + m[1];
    if (/^\d{2}\.\d{2}\.\d{4}$/.test(str)) return str;
    return str;
}
function lockGetLastUpdateDate() {
    try {
        const raw = localStorage.getItem('lockoutsLastUpdate');
        if (!raw) return '';
        const d = new Date(raw);
        if (isNaN(d.getTime())) return '';
        return String(d.getDate()).padStart(2, '0') + '.' + String(d.getMonth() + 1).padStart(2, '0') + '.' + d.getFullYear();
    } catch (e) { return ''; }
}

async function lockInitSorted(mode) {
    if (!lockLoaded || !lockData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/lockouts.json' + bust, { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            lockData = await resp.json();
            lockLoaded = true;
            localStorage.setItem('lockoutsLastUpdate', new Date().toISOString());
        } catch (e) {
            console.error('lockInitSorted error:', e);
            const ids = { type: 'lockTypeList', name: 'lockNameList', prod: 'lockProdList' };
            const el = document.getElementById(ids[mode]);
            if (el) el.innerHTML = '<div class="pb-empty">Ошибка загрузки.<br>Проверьте соединение.</div>';
            return;
        }
    }
    lockRenderSorted(mode);
}

function lockForceRefresh(mode) {
    lockData = null;
    lockLoaded = false;
    lockInitSorted(mode);
    if (navigator.vibrate) navigator.vibrate(40);
}

function lockRenderSorted(mode) {
    const ids = {
        type: { list: 'lockTypeList', info: 'lockTypeInfo', search: 'lockTypeSearchInput', page: 'page-lockouts-type' },
        name: { list: 'lockNameList', info: 'lockNameInfo', search: 'lockNameSearchInput', page: 'page-lockouts-name' },
        prod: { list: 'lockProdList', info: 'lockProdInfo', search: 'lockProdSearchInput', page: 'page-lockouts-prod' },
    };
    const id = ids[mode];
    if (!id) return;
    const list = document.getElementById(id.list);
    const info = document.getElementById(id.info);
    if (!list || !info) return;

    if (!lockLoaded || !lockData) {
        list.innerHTML = '';
        info.textContent = 'Загрузка…';
        return;
    }

    const query = lockNorm((document.getElementById(id.search)?.value || '').trim());
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по проекту
    if (query && window.kipIsProjectLinkFilterActive('lockouts')) {
        window.kipClearProjectLinkFilter('lockouts');
    }
    let filtered = lockData.lockouts || [];

    const sortKey = mode === 'type' ? 'Тип' : mode === 'name' ? 'Наименование' : 'Производство';
    filtered.sort((a, b) => {
        const va = (a[sortKey] || '').toString().toLowerCase();
        const vb = (b[sortKey] || '').toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    // Фильтр по «№ проекта» (из карточки проекта)
    if (window.kipIsProjectLinkFilterActive('lockouts')) {
        filtered = filtered.filter(d => window.kipMatchesProjectFilter(d, 'lockouts'));
    }

    if (query) {
        filtered = filtered.filter(d =>
            LOCK_FIELDS.some(f => lockNorm(d[f.key] || '').includes(query))
        );
    }

    const groups = {};
    const groupOrder = [];
    for (const d of filtered) {
        const g = d[sortKey] || '(без группы)';
        if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
        groups[g].push(d);
    }
    // Сортируем основные группы по алфавиту
    groupOrder.sort((a, b) => {
        const va = a.toString().toLowerCase();
        const vb = b.toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    info.textContent = '';

    if (filtered.length === 0) {
        let emptyHtml = '';
        if (window.kipIsProjectLinkFilterActive('lockouts')) {
            emptyHtml += window.kipRenderFilterBadge('lockouts');
            emptyHtml += '<div class="pb-empty">По проекту №«' + lockEsc(window.kipProjectLinkFilter.projectNo) + '» блокировок не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">Ничего не найдено.<br>Попробуйте изменить запрос.</div>';
        }
        list.innerHTML = emptyHtml;
        window.kipBindFilterBadge(list, 'lockouts', lockRenderSorted);
        return;
    }

    let html = '';
    // Бейдж активного фильтра по проекту (вверху списка)
    if (window.kipIsProjectLinkFilterActive('lockouts')) {
        html += window.kipRenderFilterBadge('lockouts');
    }
    html += '<div class="lock-sorted-list' + (query ? ' searching' : '') + '">';
    for (const g of groupOrder) {
        const items = groups[g];
        const groupKey = mode + '|' + g;
        const isGroupExpanded = query ? true : (lockGroupExpanded[groupKey] === true);

        html += '<div class="pb-section lock-group' + (isGroupExpanded ? ' expanded' : '') + '" data-group="' + lockEsc(g) + '" data-mode="' + mode + '">';
        html += '<div class="pb-section-title lock-group-title" onclick="lockToggleGroup(this)">';
        html += '<span class="pb-section-title-text">' + lockMark(g, query) + '</span>';
        html += '<span class="pb-section-title-count">' + items.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';

        for (const item of items) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Параметр'] || '(без названия)';
            const type = item['Уставка'] || '';
            const place = item['Расположение'] || '';

            html += '<div class="lock-card" data-lock-id="' + lockEsc(itemId) + '" data-mode="' + mode + '">';
            html += window.KipFav._cardFavBtnHtml(itemId, 'lock');
            html += '<div class="lock-card-header" onclick="lockOpenDetail(\'' + lockEsc(itemId) + '\')">';
            html += '<div class="lock-card-header-inner">';
            html += '<div class="lock-card-text">';
            html += '<div class="lock-card-title">' + lockMark(name, query) + '</div>';
            let subtitle = '';
            if (type) subtitle += type;
            if (place) subtitle += (subtitle ? ' · ' : '') + place;
            if (subtitle) html += '<div class="lock-card-subtitle">' + lockMark(subtitle, query) + '</div>';
            html += '</div>'; // .lock-card-text
            html += '</div>'; // .lock-card-header-inner
            html += '</div>'; // .lock-card-header
            html += '</div>'; // .lock-card
        }
        html += '</div>';
        html += '</div>';
    }
    html += '</div>';
    list.innerHTML = html;
    // Привязка обработчика к кнопке ✕ в бейдже фильтра
    window.kipBindFilterBadge(list, 'lockouts', lockRenderSorted);
    // Свайп для добавления в избранное
    if (typeof window.KipFav !== 'undefined') window.KipFav.wrapKipCardsForFavSwipe('.lock-card', 'lock', 'data-lock-id');
}

function lockToggleGroup(titleEl) {
    const section = titleEl.closest('.pb-section');
    if (!section) return;
    const mode = section.getAttribute('data-mode') || 'type';
    const group = section.getAttribute('data-group');
    if (!group) return;
    if (navigator.vibrate) navigator.vibrate(25);
    window._lockGroupCtx = { mode: mode, group: group };
    window.navigateTo('lock-group');
}

function lockRenderGroup() {
    const ctx = window._lockGroupCtx || {};
    const mode = ctx.mode || 'type';
    const group = ctx.group || '';
    const list = document.getElementById('lockGroupList');
    const titleEl = document.getElementById('lockGroupTitle');
    if (!list) return;
    if (titleEl) titleEl.textContent = group || 'Блокировки';
    // На десктопе: заменить заголовок на полные хлебные крошки
    if (window.isDesktop()) window.updateDesktopBreadcrumb(null, group || 'Блокировки');

    if (!lockLoaded || !lockData) {
        list.innerHTML = '<div class="pb-empty">Загрузка…</div>';
        return;
    }

    const sortKey = mode === 'type' ? 'Тип' : mode === 'name' ? 'Наименование' : 'Производство';
    let items = (lockData.lockouts || []).filter(d => {
        const g = d[sortKey] || '(без группы)';
        return g === group;
    });
    // Применить активный фильтр по «№ проекта», если он установлен.
    // Без этого при клике на группу из отфильтрованного списка будет показан
    // весь список блокировок этой группы, а не только относящиеся к проекту.
    if (window.kipIsProjectLinkFilterActive('lockouts')) {
        items = items.filter(d => window.kipMatchesProjectFilter(d, 'lockouts'));
    }
    items.sort((a, b) => {
        const va = (a['Параметр'] || '').toString().toLowerCase();
        const vb = (b['Параметр'] || '').toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    if (items.length === 0) {
        let emptyHtml = '';
        if (window.kipIsProjectLinkFilterActive('lockouts')) {
            emptyHtml += window.kipRenderFilterBadge('lockouts');
            emptyHtml += '<div class="pb-empty">В группе «' + lockEsc(group) + '» по проекту №«' + lockEsc(window.kipProjectLinkFilter.projectNo) + '» блокировок не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">В группе нет блокировок.</div>';
        }
        list.innerHTML = emptyHtml;
        window.kipBindFilterBadge(list, 'lockouts', function() { lockRenderGroup(); });
        return;
    }

    // Сгруппировать блокировки по «Производству» — раскрытая группа без сворачивания.
    const groups = {};
    const groupOrder = [];
    for (const item of items) {
        const g = item['Производство'] || '(без производства)';
        if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
        groups[g].push(item);
    }
    // Алфавитный порядок групп
    groupOrder.sort((a, b) => {
        const va = a.toString().toLowerCase();
        const vb = b.toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    let html = '';
    // Бейдж активного фильтра по «№ проекта» вверху страницы группы
    if (window.kipIsProjectLinkFilterActive('lockouts')) {
        html += window.kipRenderFilterBadge('lockouts');
    }
    html += '<div class="lock-sorted-list">';
    for (const g of groupOrder) {
        const gItems = groups[g];
        html += '<div class="pb-section lock-group lock-subgroup static">';
        html += '<div class="pb-section-title">';
        html += '<span class="pb-section-title-text">' + lockEsc(g) + '</span>';
        html += '<span class="pb-section-title-count">' + gItems.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';
        for (const item of gItems) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Параметр'] || '(без названия)';
            const type = item['Уставка'] || '';
            const place = item['Расположение'] || '';

            html += '<div class="lock-card" data-lock-id="' + lockEsc(itemId) + '" data-mode="' + mode + '">';
            html += window.KipFav._cardFavBtnHtml(itemId, 'lock');
            html += '<div class="lock-card-header" onclick="lockOpenDetail(\'' + lockEsc(itemId) + '\')">';
            html += '<div class="lock-card-header-inner">';
            html += '<div class="lock-card-text">';
            html += '<div class="lock-card-title">' + lockEsc(name) + '</div>';
            let subtitle = '';
            if (type) subtitle += type;
            if (place) subtitle += (subtitle ? ' · ' : '') + place;
            if (subtitle) html += '<div class="lock-card-subtitle">' + lockEsc(subtitle) + '</div>';
            html += '</div>';
            html += '</div>';
            html += '</div>';
            html += '</div>';
        }
        html += '</div>'; // pb-section-body
        html += '</div>'; // pb-section
    }
    html += '</div>';
    list.innerHTML = html;
    // Привязка обработчика к кнопке ✕ в бейдже фильтра
    window.kipBindFilterBadge(list, 'lockouts', function() { lockRenderGroup(); });
    // Свайп для добавления в избранное
    if (typeof window.KipFav !== 'undefined') window.KipFav.wrapKipCardsForFavSwipe('.lock-card', 'lock', 'data-lock-id');
}

function lockScrollToGroup(el) {
    if (!el) return;
    const mode = el.getAttribute('data-mode') || 'type';
    const ph = document.querySelector('#page-lockouts-' + mode + ' .page-inline-header');
    const stickyHeight = ph ? ph.offsetHeight : 56;
    const rect = el.getBoundingClientRect();
    const targetY = window.scrollY + rect.top - stickyHeight - 8;
    window.scrollTo({ top: Math.max(0, targetY), behavior: 'auto' });
}

// ===== Открытие карточки блокировки (отдельная страница, как у приборов) =====
function lockOpenDetail(lockId) {
    if (!lockId) return;
    if (navigator.vibrate) navigator.vibrate(15);
    window._lockDetailId = lockId;
    if (window.isDesktop()) {
        window.lockRenderDetailInPanel();
    } else {
        window.navigateTo('lockout-detail');
    }
}

function lockRenderDetail() {
    const lockId = window._lockDetailId;
    if (!lockId || !lockLoaded || !lockData) return;
    const item = lockData.lockouts.find(d => String(d['ID'] ?? '') === String(lockId));
    if (!item) return;
    const titleEl = document.getElementById('lockoutDetailTitle');
    const content = document.getElementById('lockoutDetailContent');
    if (!titleEl || !content) return;
    const name = item['Параметр'] || '(без названия)';
    titleEl.textContent = name;

    let html = '<div class="lock-detail-card">';
    // Значок избранного в правом верхнем углу (виден только на десктопе)
    html += '<button type="button" class="dev-detail-fav-btn" onclick="KipFav.toggleFromDetailByType(\'lock\')" aria-label="Избранное" title="Добавить/убрать из избранного"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button>';
    html += '<div class="lock-detail-rows">';
    for (const f of LOCK_FIELDS) {
        if (f.hiddenInCard) continue;
        let val = item[f.key];
        if (val === undefined || val === null || val === '') continue;
        if (f.key === 'Дата проверки') val = lockFormatDate(val);
        const grpCls = f.group ? ' lock-row-group-' + f.group : '';
        html += '<div class="lock-detail-row' + grpCls + '">';
        html += '<div class="lock-detail-label">' + lockEsc(f.label) + '</div>';
        // Для поля «№ проекта» — кликабельная ссылка в карточку проекта
        // (только если значение не пустое/«Нет данных»).
        // Если значение содержит несколько номеров (через ',' или ';'),
        // каждое число становится отдельной кликабельной ссылкой.
        if (f.key === '№ проекта' && !window.kipIsEmptyProjectNo(val)) {
            const parts = window.kipSplitProjectValues(val);
            html += '<div class="lock-detail-value kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'project', lockEsc);
            html += '</div>';
        } else {
            html += '<div class="lock-detail-value">' + lockEsc(String(val)) + '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    // Блок «Связанные записи» — обратные ссылки на приборы/клапаны/регуляторы
    // по полю «№ СБС» (если оно заполнено в карточке блокировки).
    const sbsNo = item['№ СБС'];
    if (sbsNo && !window.kipIsEmptySbsNo(sbsNo)) {
        html += window.kipRenderSbsRelatedBlock(String(sbsNo));
    }
    content.innerHTML = html;
    // Обновить состояние кнопки избранного в карточке
    window.KipFav.updateDetailFavBtnByType('lock', lockId);
    // Привязка кликов по ссылкам «№ проекта» (безопасно: через data-атрибут)
    content.querySelectorAll('[data-project-link]').forEach(function(el) {
        el.addEventListener('click', function() {
            window.projectOpenByProjectNo(this.getAttribute('data-project-link'));
        });
    });
    // Запустить фоновую загрузку данных разделов и обновить счётчики по «№ СБС»
    if (sbsNo && !window.kipIsEmptySbsNo(sbsNo)) {
        window.kipLoadAndUpdateSbsRelated(String(sbsNo));
    }
    // Обновить значок избранного в заголовке (мобильный)
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

// ===== Кнопка Блокировки на странице КИП И ОС: только tap =====
function lockInitEntryButton() {
    const btn = document.getElementById('lockoutsEntryBtn');
    if (!btn || btn.dataset.initialized) return;
    btn.dataset.initialized = '1';
    btn.addEventListener('click', function() {
        if (navigator.vibrate) navigator.vibrate(15);
        window.navigateTo('lockouts-prod');
    });
    // Обновить sublabel количеством блокировок
    lockUpdateEntrySublabel();
}
async function lockUpdateEntrySublabel() {
    const btn = document.getElementById('lockoutsEntryBtn');
    if (!btn) return;
    const sublabel = btn.querySelector('.menu-btn-sublabel');
    if (!sublabel) return;
    if (!lockLoaded || !lockData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/lockouts.json' + bust, { cache: 'no-store' });
            if (!resp.ok) return;
            lockData = await resp.json();
            lockLoaded = true;
            localStorage.setItem('lockoutsLastUpdate', new Date().toISOString());
        } catch (e) { return; }
    }
    const count = (lockData.lockouts || []).length;
    sublabel.textContent = count + ' ' + lockPlural(count, ['блокировка', 'блокировки', 'блокировок']) + ' КИП ИОС';
}

// ===== Exports =====
export {
    lockData,
    lockLoaded,
    lockInitEntryButton,
    lockInitSorted,
    lockForceRefresh,
    lockRenderSorted,
    lockOpenDetail,
    lockRenderDetail,
    lockToggleGroup,
    lockRenderGroup
};
