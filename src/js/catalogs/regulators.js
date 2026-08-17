/**
 * @module catalogs/regulators
 * @description Regulators (Регуляторы) catalog — data loading, rendering, search, grouping.
 * Extracted from inline <script> in index.html (lines ~6089-6607).
 *
 * External dependencies (accessed via window.*):
 *   navigateTo, KipFav, isDesktop,
 *   kipIsProjectLinkFilterActive, kipClearProjectLinkFilter,
 *   kipIsSbsLinkFilterActive, kipClearSbsLinkFilter,
 *   kipProjectLinkFilter, kipSbsLinkFilter,
 *   kipMatchesProjectFilter, kipMatchesSbsFilter,
 *   kipRenderFilterBadge, kipRenderSbsFilterBadge,
 *   kipBindFilterBadge, kipBindSbsFilterBadge,
 *   kipIsEmptyProjectNo, kipSplitProjectValues,
 *   kipIsEmptySbsNo, kipIsEmptySarNo, kipSplitIdValues,
 *   kipRenderMultiLinks,
 *   kipRenderSarRelatedBlock, kipLoadAndUpdateSarRelated,
 *   updateDesktopBreadcrumb,
 *   projectOpenByProjectNo, lockOpenBySbsNo,
 *   regulatorRenderDetailInPanel
 */

// ===== РЕГУЛЯТОРЫ (зеркало клапанов/блокировок) =====
// Поля соответствуют листу "Регуляторы_app" таблицы Google Sheets
// https://docs.google.com/spreadsheets/d/1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy/edit (тот же файл, что и для приборов/блокировок/клапанов)
// Реальная структура полей определяется на этапе парсинга sync-regulators.py,
// здесь заданы только предполагаемые группы для типичного набора колонок.
// Если в данных есть колонки, не указанные в REGULATOR_FIELDS — они не будут показаны.
// Поля соответствуют листу "Регуляторы_app" файла Excel.
// Все 10 ключей взяты из реальных столбцов regulators.json (sync-regulators.py).
const REGULATOR_FIELDS = [
    // group 1 -- идентификация и наладка регулятора
    { key: 'Параметр', label: 'Параметр', group: 1, hiddenInCard: true },
    { key: 'Уставка', label: 'Уставка', group: 1 },
    { key: 'Кп', label: 'Кп', group: 1 },
    { key: 'Ти', label: 'Ти', group: 1 },
    { key: 'Тд', label: 'Тд', group: 1 },
    { key: 'Устроиство регулятора или ручного управления', label: 'Устройство регулятора или ручного управления', group: 1 },
    // group 2 -- расположение
    { key: 'Производство', label: 'Производство', group: 2 },
    // group 3 -- идентификаторы и привязки (с гиперссылками)
    { key: '№ САРиРУ', label: '№ САРиРУ', group: 3 },
    { key: '№ проекта', label: '№ проекта', group: 3 },
    // group 4 -- примечания
    { key: 'Примечание', label: 'Примечание', group: 4 },
    { key: 'Замечание', label: 'Замечание', group: 4 },
];
let regulatorData = null;
let regulatorLoaded = false;
let regulatorGroupExpanded = {};

function regulatorEsc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function regulatorNorm(s) {
    if (s == null) return '';
    return String(s).toLowerCase().replace(/[ё]/g, 'е').replace(/[^a-zа-я0-9]/gi, '');
}
function regulatorMark(text, query) {
    if (!query) return regulatorEsc(text);
    const t = String(text);
    const q = regulatorNorm(query);
    if (!q) return regulatorEsc(t);
    const idx = regulatorNorm(t).indexOf(q);
    if (idx === -1) return regulatorEsc(t);
    const before = t.substring(0, idx);
    const match = t.substring(idx, idx + q.length);
    const after = t.substring(idx + q.length);
    return regulatorEsc(before) + '<mark>' + regulatorEsc(match) + '</mark>' + regulatorMark(after, query);
}
function regulatorPlural(n, forms) {
    const m = n % 100;
    const m1 = m % 10;
    if (m >= 5 && m <= 20) return forms[2];
    if (m1 === 1) return forms[0];
    if (m1 >= 2 && m1 <= 4) return forms[1];
    return forms[2];
}
function regulatorFormatDate(dateVal) {
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
function regulatorGetLastUpdateDate() {
    try {
        const raw = localStorage.getItem('regulatorsLastUpdate');
        if (!raw) return '';
        const d = new Date(raw);
        if (isNaN(d.getTime())) return '';
        return String(d.getDate()).padStart(2, '0') + '.' + String(d.getMonth() + 1).padStart(2, '0') + '.' + d.getFullYear();
    } catch (e) { return ''; }
}

async function regulatorInitSorted(mode) {
    if (!regulatorLoaded || !regulatorData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/regulators.json' + bust, { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            regulatorData = await resp.json();
            regulatorLoaded = true;
            localStorage.setItem('regulatorsLastUpdate', new Date().toISOString());
        } catch (e) {
            console.error('regulatorInitSorted error:', e);
            const ids = { type: 'regulatorTypeList', name: 'regulatorNameList', prod: 'regulatorProdList' };
            const el = document.getElementById(ids[mode]);
            if (el) el.innerHTML = '<div class="pb-empty">Ошибка загрузки.<br>Проверьте соединение.</div>';
            return;
        }
    }
    regulatorRenderSorted(mode);
}

function regulatorForceRefresh(mode) {
    regulatorData = null;
    regulatorLoaded = false;
    regulatorInitSorted(mode);
    if (navigator.vibrate) navigator.vibrate(40);
}

function regulatorRenderSorted(mode) {
    const kipIsProjectLinkFilterActive = window.kipIsProjectLinkFilterActive;
    const kipClearProjectLinkFilter = window.kipClearProjectLinkFilter;
    const kipIsSbsLinkFilterActive = window.kipIsSbsLinkFilterActive;
    const kipClearSbsLinkFilter = window.kipClearSbsLinkFilter;
    const kipMatchesProjectFilter = window.kipMatchesProjectFilter;
    const kipMatchesSbsFilter = window.kipMatchesSbsFilter;
    const kipRenderFilterBadge = window.kipRenderFilterBadge;
    const kipRenderSbsFilterBadge = window.kipRenderSbsFilterBadge;
    const kipBindFilterBadge = window.kipBindFilterBadge;
    const kipBindSbsFilterBadge = window.kipBindSbsFilterBadge;
    const KipFav = window.KipFav;

    const ids = {
        type: { list: 'regulatorTypeList', info: 'regulatorTypeInfo', search: 'regulatorTypeSearchInput', page: 'page-regulators-type' },
        name: { list: 'regulatorNameList', info: 'regulatorNameInfo', search: 'regulatorNameSearchInput', page: 'page-regulators-name' },
        prod: { list: 'regulatorProdList', info: 'regulatorProdInfo', search: 'regulatorProdSearchInput', page: 'page-regulators-prod' },
    };
    const id = ids[mode];
    if (!id) return;
    const list = document.getElementById(id.list);
    const info = document.getElementById(id.info);
    if (!list || !info) return;

    if (!regulatorLoaded || !regulatorData) {
        list.innerHTML = '';
        info.textContent = 'Загрузка…';
        return;
    }

    const query = regulatorNorm((document.getElementById(id.search)?.value || '').trim());
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по проекту
    if (query && kipIsProjectLinkFilterActive('regulators')) {
        kipClearProjectLinkFilter('regulators');
    }
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по «№ СБС»
    if (query && kipIsSbsLinkFilterActive('regulators')) {
        kipClearSbsLinkFilter('regulators');
    }
    let filtered = regulatorData.regulators || [];

    const sortKey = mode === 'type' ? 'Устроиство регулятора или ручного управления' : mode === 'name' ? 'Параметр' : 'Производство';
    filtered.sort((a, b) => {
        const va = (a[sortKey] || '').toString().toLowerCase();
        const vb = (b[sortKey] || '').toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    // Фильтр по «№ проекта» (из карточки проекта)
    if (kipIsProjectLinkFilterActive('regulators')) {
        filtered = filtered.filter(d => kipMatchesProjectFilter(d, 'regulators'));
    }
    // Фильтр по «№ СБС» (из карточки блокировки)
    if (kipIsSbsLinkFilterActive('regulators')) {
        filtered = filtered.filter(d => kipMatchesSbsFilter(d, 'regulators'));
    }

    if (query) {
        filtered = filtered.filter(d =>
            REGULATOR_FIELDS.some(f => regulatorNorm(d[f.key] || '').includes(query))
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
        if (kipIsProjectLinkFilterActive('regulators')) {
            emptyHtml += kipRenderFilterBadge('regulators');
            emptyHtml += '<div class="pb-empty">По проекту №«' + regulatorEsc(window.kipProjectLinkFilter.projectNo) + '» регуляторов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (kipIsSbsLinkFilterActive('regulators')) {
            emptyHtml += kipRenderSbsFilterBadge('regulators');
            emptyHtml += '<div class="pb-empty">По СБС №«' + regulatorEsc(window.kipSbsLinkFilter.sbsNo) + '» регуляторов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">Ничего не найдено.<br>Попробуйте изменить запрос.</div>';
        }
        list.innerHTML = emptyHtml;
        kipBindFilterBadge(list, 'regulators', regulatorRenderSorted);
        kipBindSbsFilterBadge(list, 'regulators', regulatorRenderSorted);
        // Свайп для добавления в избранное
        if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.regulator-card', 'reg', 'data-regulator-id');
        return;
    }

    let html = '';
    // Бейдж активного фильтра по проекту (вверху списка)
    if (kipIsProjectLinkFilterActive('regulators')) {
        html += kipRenderFilterBadge('regulators');
    }
    // Бейдж активного фильтра по «№ СБС» (вверху списка)
    if (kipIsSbsLinkFilterActive('regulators')) {
        html += kipRenderSbsFilterBadge('regulators');
    }
    html += '<div class="regulator-sorted-list' + (query ? ' searching' : '') + '">';
    for (const g of groupOrder) {
        const items = groups[g];
        const groupKey = mode + '|' + g;
        const isGroupExpanded = query ? true : (regulatorGroupExpanded[groupKey] === true);

        html += '<div class="pb-section regulator-group' + (isGroupExpanded ? ' expanded' : '') + '" data-group="' + regulatorEsc(g) + '" data-mode="' + mode + '">';
        html += '<div class="pb-section-title regulator-group-title" onclick="regulatorToggleGroup(this)">';
        html += '<span class="pb-section-title-text">' + regulatorMark(g, query) + '</span>';
        html += '<span class="pb-section-title-count">' + items.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';

        for (const item of items) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Параметр'] || '(без названия)';
            const type = item['Устроиство регулятора или ручного управления'] || '';
            const place = item['Производство'] || '';

            html += '<div class="regulator-card" data-regulator-id="' + regulatorEsc(itemId) + '" data-mode="' + mode + '">';
            html += KipFav._cardFavBtnHtml(itemId, 'reg');
            html += '<div class="regulator-card-header" onclick="regulatorOpenDetail(\'' + regulatorEsc(itemId) + '\')">';
            html += '<div class="regulator-card-header-inner">';
            html += '<div class="regulator-card-text">';
            html += '<div class="regulator-card-title">' + regulatorMark(name, query) + '</div>';
            let subtitle = '';
            if (type) subtitle += type;
            if (place) subtitle += (subtitle ? ' · ' : '') + place;
            if (subtitle) html += '<div class="regulator-card-subtitle">' + regulatorMark(subtitle, query) + '</div>';
            html += '</div>';
            html += '</div>';
            html += '</div>';
            html += '</div>';
        }
        html += '</div>';
        html += '</div>';
    }
    html += '</div>';
    list.innerHTML = html;
    // Привязка обработчика к кнопке ✕ в бейдже фильтра
    kipBindFilterBadge(list, 'regulators', regulatorRenderSorted);
    kipBindSbsFilterBadge(list, 'regulators', regulatorRenderSorted);
    // Свайп для добавления в избранное
    if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.regulator-card', 'reg', 'data-regulator-id');
}

function regulatorToggleGroup(titleEl) {
    const section = titleEl.closest('.pb-section');
    if (!section) return;
    const mode = section.getAttribute('data-mode') || 'type';
    const group = section.getAttribute('data-group');
    if (!group) return;
    if (navigator.vibrate) navigator.vibrate(25);
    window._regulatorGroupCtx = { mode: mode, group: group };
    window.navigateTo('regulator-group');
}

function regulatorRenderGroup() {
    const kipIsProjectLinkFilterActive = window.kipIsProjectLinkFilterActive;
    const kipIsSbsLinkFilterActive = window.kipIsSbsLinkFilterActive;
    const kipMatchesProjectFilter = window.kipMatchesProjectFilter;
    const kipMatchesSbsFilter = window.kipMatchesSbsFilter;
    const kipRenderFilterBadge = window.kipRenderFilterBadge;
    const kipRenderSbsFilterBadge = window.kipRenderSbsFilterBadge;
    const kipBindFilterBadge = window.kipBindFilterBadge;
    const kipBindSbsFilterBadge = window.kipBindSbsFilterBadge;
    const KipFav = window.KipFav;

    const ctx = window._regulatorGroupCtx || {};
    const mode = ctx.mode || 'type';
    const group = ctx.group || '';
    const list = document.getElementById('regulatorGroupList');
    const titleEl = document.getElementById('regulatorGroupTitle');
    if (!list) return;
    if (titleEl) titleEl.textContent = group || 'Регуляторы';
    // На десктопе: заменить заголовок на полные хлебные крошки
    if (window.isDesktop()) window.updateDesktopBreadcrumb(null, group || 'Регуляторы');

    if (!regulatorLoaded || !regulatorData) {
        list.innerHTML = '<div class="pb-empty">Загрузка…</div>';
        return;
    }

    const sortKey = mode === 'type' ? 'Устроиство регулятора или ручного управления' : mode === 'name' ? 'Параметр' : 'Производство';
    let items = (regulatorData.regulators || []).filter(d => {
        const g = d[sortKey] || '(без группы)';
        return g === group;
    });
    // Применить активный фильтр (проект / СБС), если он установлен.
    // Без этого при клике на группу из отфильтрованного списка будет показан
    // весь список регуляторов этой группы, а не только относящиеся к проекту.
    const hasRegFilter = kipIsProjectLinkFilterActive('regulators')
        || kipIsSbsLinkFilterActive('regulators');
    if (hasRegFilter) {
        items = items.filter(d =>
            kipMatchesProjectFilter(d, 'regulators')
            && kipMatchesSbsFilter(d, 'regulators')
        );
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
        if (kipIsProjectLinkFilterActive('regulators')) {
            emptyHtml += kipRenderFilterBadge('regulators');
            emptyHtml += '<div class="pb-empty">В группе «' + regulatorEsc(group) + '» по проекту №«' + regulatorEsc(window.kipProjectLinkFilter.projectNo) + '» регуляторов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (kipIsSbsLinkFilterActive('regulators')) {
            emptyHtml += kipRenderSbsFilterBadge('regulators');
            emptyHtml += '<div class="pb-empty">В группе «' + regulatorEsc(group) + '» по СБС №«' + regulatorEsc(window.kipSbsLinkFilter.sbsNo) + '» регуляторов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">В группе нет регуляторов.</div>';
        }
        list.innerHTML = emptyHtml;
        kipBindFilterBadge(list, 'regulators', function() { regulatorRenderGroup(); });
        kipBindSbsFilterBadge(list, 'regulators', function() { regulatorRenderGroup(); });
        // Свайп для добавления в избранное
        if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.regulator-card', 'reg', 'data-regulator-id');
        return;
    }

    // Сгруппировать регуляторы по «Производству» — раскрытая группа без сворачивания.
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
    // Бейдж активного фильтра (проект / СБС) вверху страницы группы
    if (kipIsProjectLinkFilterActive('regulators')) {
        html += kipRenderFilterBadge('regulators');
    } else if (kipIsSbsLinkFilterActive('regulators')) {
        html += kipRenderSbsFilterBadge('regulators');
    }
    html += '<div class="regulator-sorted-list">';
    for (const g of groupOrder) {
        const gItems = groups[g];
        html += '<div class="pb-section regulator-group regulator-subgroup static">';
        html += '<div class="pb-section-title">';
        html += '<span class="pb-section-title-text">' + regulatorEsc(g) + '</span>';
        html += '<span class="pb-section-title-count">' + gItems.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';
        for (const item of gItems) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Параметр'] || '(без названия)';
            const type = item['Устроиство регулятора или ручного управления'] || '';
            const place = item['Производство'] || '';

            html += '<div class="regulator-card" data-regulator-id="' + regulatorEsc(itemId) + '" data-mode="' + mode + '">';
            html += KipFav._cardFavBtnHtml(itemId, 'reg');
            html += '<div class="regulator-card-header" onclick="regulatorOpenDetail(\'' + regulatorEsc(itemId) + '\')">';
            html += '<div class="regulator-card-header-inner">';
            html += '<div class="regulator-card-text">';
            html += '<div class="regulator-card-title">' + regulatorEsc(name) + '</div>';
            let subtitle = '';
            if (type) subtitle += type;
            if (place) subtitle += (subtitle ? ' · ' : '') + place;
            if (subtitle) html += '<div class="regulator-card-subtitle">' + regulatorEsc(subtitle) + '</div>';
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
    // Привязка обработчиков к кнопкам ✕ в бейджах фильтра
    kipBindFilterBadge(list, 'regulators', function() { regulatorRenderGroup(); });
    kipBindSbsFilterBadge(list, 'regulators', function() { regulatorRenderGroup(); });
    // Свайп для добавления в избранное
    if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.regulator-card', 'reg', 'data-regulator-id');
}

function regulatorScrollToGroup(el) {
    if (!el) return;
    const mode = el.getAttribute('data-mode') || 'type';
    const ph = document.querySelector('#page-regulators-' + mode + ' .page-inline-header');
    const stickyHeight = ph ? ph.offsetHeight : 56;
    const rect = el.getBoundingClientRect();
    const targetY = window.scrollY + rect.top - stickyHeight - 8;
    window.scrollTo({ top: Math.max(0, targetY), behavior: 'auto' });
}

// ===== Открытие карточки регулятора (отдельная страница, как у приборов/блокировок/клапанов) =====
function regulatorOpenDetail(regulatorId) {
    if (!regulatorId) return;
    if (navigator.vibrate) navigator.vibrate(15);
    window._regulatorDetailId = regulatorId;
    if (window.isDesktop()) {
        window.regulatorRenderDetailInPanel();
    } else {
        window.navigateTo('regulator-detail');
    }
}

function regulatorRenderDetail() {
    const regulatorId = window._regulatorDetailId;
    if (!regulatorId || !regulatorLoaded || !regulatorData) return;
    const item = regulatorData.regulators.find(d => String(d['ID'] ?? '') === String(regulatorId));
    if (!item) return;
    const titleEl = document.getElementById('regulatorDetailTitle');
    const content = document.getElementById('regulatorDetailContent');
    if (!titleEl || !content) return;
    const name = item['Параметр'] || '(без названия)';
    titleEl.textContent = name;

    let html = '<div class="regulator-detail-card">';
    // Значок избранного в правом верхнем углу (виден только на десктопе)
    html += '<button type="button" class="dev-detail-fav-btn" onclick="KipFav.toggleFromDetailByType(\'reg\')" aria-label="Избранное" title="Добавить/убрать из избранного"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button>';
    html += '<div class="regulator-detail-rows">';
    for (const f of REGULATOR_FIELDS) {
        if (f.hiddenInCard) continue;
        let val = item[f.key];
        if (val === undefined || val === null || val === '') continue;
        if (f.key === 'Дата проверки') val = regulatorFormatDate(val);
        const grpCls = f.group ? ' regulator-row-group-' + f.group : '';
        html += '<div class="regulator-detail-row' + grpCls + '">';
        html += '<div class="regulator-detail-label">' + regulatorEsc(f.label) + '</div>';
        // Для поля «№ проекта» — кликабельная ссылка в карточку проекта
        // (только если значение не пустое/«Нет данных»).
        // Если значение содержит несколько номеров (через ',' или ';'),
        // каждое число становится отдельной кликабельной ссылкой.
        if (f.key === '№ проекта' && !window.kipIsEmptyProjectNo(val)) {
            const parts = window.kipSplitProjectValues(val);
            html += '<div class="regulator-detail-value kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'project', regulatorEsc);
            html += '</div>';
        } else if (f.key === '№ СБС' && !window.kipIsEmptySbsNo(val)) {
            const parts = window.kipSplitIdValues(val);
            html += '<div class="regulator-detail-value kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'sbs', regulatorEsc);
            html += '</div>';
        } else {
            html += '<div class="regulator-detail-value">' + regulatorEsc(String(val)) + '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    // Блок «Связанные записи» — обратные ссылки на приборы/клапаны
    // по полю «№ САРиРУ» (если оно заполнено в карточке регулятора).
    const sarNo = item['№ САРиРУ'];
    if (sarNo && !window.kipIsEmptySarNo(sarNo)) {
        html += window.kipRenderSarRelatedBlock(String(sarNo));
    }
    content.innerHTML = html;
    // Обновить состояние кнопки избранного в карточке
    window.KipFav.updateDetailFavBtnByType('reg', regulatorId);
    // Привязка кликов по ссылкам «№ проекта» (безопасно: через data-атрибут)
    content.querySelectorAll('[data-project-link]').forEach(function(el) {
        el.addEventListener('click', function() {
            window.projectOpenByProjectNo(this.getAttribute('data-project-link'));
        });
    });
    // Привязка кликов по ссылкам «№ СБС» → карточка блокировки
    content.querySelectorAll('[data-sbs-link]').forEach(function(el) {
        el.addEventListener('click', function() {
            window.lockOpenBySbsNo(this.getAttribute('data-sbs-link'));
        });
    });
    // Запустить фоновую загрузку данных разделов и обновить счётчики по «№ САРиРУ»
    if (sarNo && !window.kipIsEmptySarNo(sarNo)) {
        window.kipLoadAndUpdateSarRelated(String(sarNo));
    }
    // Обновить значок избранного в заголовке (мобильный)
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

// ===== Кнопка Регуляторы на странице КИП И ОС: только tap =====
function regulatorInitEntryButton() {
    const btn = document.getElementById('regulatorsEntryBtn');
    if (!btn || btn.dataset.initialized) return;
    btn.dataset.initialized = '1';
    btn.addEventListener('click', function() {
        if (navigator.vibrate) navigator.vibrate(15);
        window.navigateTo('regulators-prod');
    });
    // Обновить sublabel количеством регуляторов
    regulatorUpdateEntrySublabel();
}
async function regulatorUpdateEntrySublabel() {
    const btn = document.getElementById('regulatorsEntryBtn');
    if (!btn) return;
    const sublabel = btn.querySelector('.menu-btn-sublabel');
    if (!sublabel) return;
    if (!regulatorLoaded || !regulatorData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/regulators.json' + bust, { cache: 'no-store' });
            if (!resp.ok) return;
            regulatorData = await resp.json();
            regulatorLoaded = true;
            localStorage.setItem('regulatorsLastUpdate', new Date().toISOString());
        } catch (e) { return; }
    }
    const count = (regulatorData.regulators || []).length;
    sublabel.textContent = count + ' ' + regulatorPlural(count, ['регулятор', 'регулятора', 'регуляторов']) + ' КИП ИОС';
}

// ===== Exports =====
export {
    REGULATOR_FIELDS,
    regulatorData,
    regulatorLoaded,
    regulatorGroupExpanded,
    regulatorEsc,
    regulatorNorm,
    regulatorMark,
    regulatorPlural,
    regulatorFormatDate,
    regulatorGetLastUpdateDate,
    regulatorInitSorted,
    regulatorForceRefresh,
    regulatorRenderSorted,
    regulatorToggleGroup,
    regulatorRenderGroup,
    regulatorScrollToGroup,
    regulatorOpenDetail,
    regulatorRenderDetail,
    regulatorInitEntryButton,
    regulatorUpdateEntrySublabel,
};
