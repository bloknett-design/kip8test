/**
 * @module catalogs/valves
 * @description Valves (Клапаны) catalog — data loading, rendering, search, grouping, swipe navigation.
 * Extracted from inline <script> in index.html (lines ~5262-6088).
 *
 * External dependencies (accessed via window.*):
 *   navigateTo, KipFav, isDesktop,
 *   kipIsProjectLinkFilterActive, kipClearProjectLinkFilter,
 *   kipIsSbsLinkFilterActive, kipClearSbsLinkFilter,
 *   kipIsSarLinkFilterActive, kipClearSarLinkFilter,
 *   kipProjectLinkFilter, kipSbsLinkFilter, kipSarLinkFilter,
 *   kipMatchesProjectFilter, kipMatchesSbsFilter, kipMatchesSarFilter,
 *   kipRenderFilterBadge, kipRenderSbsFilterBadge, kipRenderSarFilterBadge,
 *   kipBindFilterBadge, kipBindSbsFilterBadge, kipBindSarFilterBadge,
 *   kipIsEmptyProjectNo, kipSplitProjectValues,
 *   kipIsEmptySbsNo, kipIsEmptySarNo, kipSplitIdValues,
 *   kipRenderMultiLinks,
 *   updateDesktopBreadcrumb,
 *   projectOpenByProjectNo, lockOpenBySbsNo, regulatorOpenBySarNo,
 *   valveRenderDetailInPanel
 */

// ===== КЛАПАНЫ (зеркало блокировок) =====
// Поля соответствуют листу "Клапана_app" таблицы Google Sheets
// https://docs.google.com/spreadsheets/d/1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy/edit (тот же файл, что и для приборов/блокировок)
// Реальная структура полей определяется на этапе парсинга sync-valves.py,
// здесь заданы только предполагаемые группы для типичного набора колонок.
// Если в данных есть колонки, не указанные в VALVE_FIELDS — они не будут показаны.
// Поля соответствуют листу "Клапаны_app" файла Excel.
// Все 22 ключа взяты из реальных столбцов valves.json (sync-valves.py).
const VALVE_FIELDS = [
    // group 1 -- идентификация и технические характеристики клапана
    { key: 'Марка', label: 'Марка', group: 1, hiddenInCard: true },
    { key: 'Тип, пропускная характеристика', label: 'Тип, пропускная характеристика', group: 1 },
    { key: 'Действие', label: 'Действие', group: 1 },
    { key: 'DN (мм)', label: 'DN (мм)', group: 1 },
    { key: 'PN (кгс/ см2)', label: 'PN (кгс/см2)', group: 1 },
    { key: 'Kvy (м3/ч)', label: 'Kvy (м3/ч)', group: 1 },
    { key: 't рабочей среды (°С)', label: 't рабочей среды (°C)', group: 1 },
    { key: 'Тип запорной части. Материал затвора/ корпуса', label: 'Тип запорной части. Материал затвора/корпуса', group: 1 },
    { key: 'Тип присоединения', label: 'Тип присоединения', group: 1 },
    { key: 'Размер строительный (мм)', label: 'Размер строительный (мм)', group: 1 },
    { key: 'Межосевое расстояние отверстий под крепёж (мм)/ резьба', label: 'Межосевое расстояние (мм)/резьба', group: 1 },
    { key: 'Позиционер (усилитель сигнала)', label: 'Позиционер (усилитель сигнала)', group: 1 },
    { key: 'Год выпуска клапана', label: 'Год выпуска клапана', group: 1 },
    // group 2 -- расположение и назначение
    { key: 'Производство', label: 'Производство', group: 2 },
    { key: 'Технологическое оборудование', label: 'Технологическое оборудование', group: 2 },
    { key: 'Назначение арматуры (параметр)', label: 'Назначение арматуры (параметр)', group: 2 },
    { key: 'Место расположения', label: 'Место расположения', group: 2 },
    // group 3 -- идентификаторы и привязки (с гиперссылками)
    { key: '№ арматуры/ привода', label: '№ арматуры/привода', group: 3 },
    { key: 'Позиция по проекту (регламенту)', label: 'Позиция по проекту (регламенту)', group: 3 },
    { key: '№ проекта', label: '№ проекта', group: 3 },
    { key: '№ СБС', label: '№ СБС', group: 3 },
    { key: '№ САРиРУ', label: '№ САРиРУ', group: 3 },
    // group 4 -- примечание
    { key: 'Примечание', label: 'Примечание', group: 4 },
];
let valveData = null;
let valveLoaded = false;
let valveGroupExpanded = {};

function valveEsc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function valveNorm(s) {
    if (s == null) return '';
    return String(s).toLowerCase().replace(/[ё]/g, 'е').replace(/[^a-zа-я0-9]/gi, '');
}
function valveMark(text, query) {
    if (!query) return valveEsc(text);
    const t = String(text);
    const q = valveNorm(query);
    if (!q) return valveEsc(t);
    const idx = valveNorm(t).indexOf(q);
    if (idx === -1) return valveEsc(t);
    const before = t.substring(0, idx);
    const match = t.substring(idx, idx + q.length);
    const after = t.substring(idx + q.length);
    return valveEsc(before) + '<mark>' + valveEsc(match) + '</mark>' + valveMark(after, query);
}
function valvePlural(n, forms) {
    const m = n % 100;
    const m1 = m % 10;
    if (m >= 5 && m <= 20) return forms[2];
    if (m1 === 1) return forms[0];
    if (m1 >= 2 && m1 <= 4) return forms[1];
    return forms[2];
}
function valveFormatDate(dateVal) {
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
function valveGetLastUpdateDate() {
    try {
        const raw = localStorage.getItem('valvesLastUpdate');
        if (!raw) return '';
        const d = new Date(raw);
        if (isNaN(d.getTime())) return '';
        return String(d.getDate()).padStart(2, '0') + '.' + String(d.getMonth() + 1).padStart(2, '0') + '.' + d.getFullYear();
    } catch (e) { return ''; }
}

async function valveInitSorted(mode) {
    if (!valveLoaded || !valveData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/valves.json' + bust, { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            valveData = await resp.json();
            valveLoaded = true;
            localStorage.setItem('valvesLastUpdate', new Date().toISOString());
        } catch (e) {
            console.error('valveInitSorted error:', e);
            const ids = { type: 'valveTypeList', name: 'valveNameList', prod: 'valveProdList' };
            const el = document.getElementById(ids[mode]);
            if (el) el.innerHTML = '<div class="pb-empty">Ошибка загрузки.<br>Проверьте соединение.</div>';
            return;
        }
    }
    valveRenderSorted(mode);
}

function valveForceRefresh(mode) {
    valveData = null;
    valveLoaded = false;
    valveInitSorted(mode);
    if (navigator.vibrate) navigator.vibrate(40);
}

function valveRenderSorted(mode) {
    const kipIsProjectLinkFilterActive = window.kipIsProjectLinkFilterActive;
    const kipClearProjectLinkFilter = window.kipClearProjectLinkFilter;
    const kipIsSbsLinkFilterActive = window.kipIsSbsLinkFilterActive;
    const kipClearSbsLinkFilter = window.kipClearSbsLinkFilter;
    const kipIsSarLinkFilterActive = window.kipIsSarLinkFilterActive;
    const kipClearSarLinkFilter = window.kipClearSarLinkFilter;
    const kipMatchesProjectFilter = window.kipMatchesProjectFilter;
    const kipMatchesSbsFilter = window.kipMatchesSbsFilter;
    const kipMatchesSarFilter = window.kipMatchesSarFilter;
    const kipRenderFilterBadge = window.kipRenderFilterBadge;
    const kipRenderSbsFilterBadge = window.kipRenderSbsFilterBadge;
    const kipRenderSarFilterBadge = window.kipRenderSarFilterBadge;
    const kipBindFilterBadge = window.kipBindFilterBadge;
    const kipBindSbsFilterBadge = window.kipBindSbsFilterBadge;
    const kipBindSarFilterBadge = window.kipBindSarFilterBadge;
    const KipFav = window.KipFav;

    const ids = {
        type: { list: 'valveTypeList', info: 'valveTypeInfo', search: 'valveTypeSearchInput', page: 'page-valves-type' },
        name: { list: 'valveNameList', info: 'valveNameInfo', search: 'valveNameSearchInput', page: 'page-valves-name' },
        prod: { list: 'valveProdList', info: 'valveProdInfo', search: 'valveProdSearchInput', page: 'page-valves-prod' },
    };
    const id = ids[mode];
    if (!id) return;
    const list = document.getElementById(id.list);
    const info = document.getElementById(id.info);
    if (!list || !info) return;

    if (!valveLoaded || !valveData) {
        list.innerHTML = '';
        info.textContent = 'Загрузка…';
        return;
    }

    const query = valveNorm((document.getElementById(id.search)?.value || '').trim());
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по проекту
    if (query && kipIsProjectLinkFilterActive('valves')) {
        kipClearProjectLinkFilter('valves');
    }
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по «№ СБС»
    if (query && kipIsSbsLinkFilterActive('valves')) {
        kipClearSbsLinkFilter('valves');
    }
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по «№ САР»
    if (query && kipIsSarLinkFilterActive('valves')) {
        kipClearSarLinkFilter('valves');
    }
    let filtered = valveData.valves || [];

    // sortKey — поле, по которому СОРТИРУЮТСЯ элементы внутри группы.
    // groupKey — поле, по которому ГРУППИРУЮТСЯ элементы (заголовки секций).
    // numericGroup = true → числовая сортировка самих групп (для DN).
    //
    // По уточнению пользователя:
    //   • свайп → (слева направо, mode='name')  → группировка по «DN (мм)»
    //   • свайп ← (справа налево, mode='type')  → группировка по «Тип, пропускная характеристика»
    //   • сортировка внутри групп (для обоих режимов) — по «Тип запорной части. Материал затвора/ корпуса»
    //   • режим prod (тап) — группировка и сортировка по производствам.
    let sortKey, groupKey, numericGroup = false;
    if (mode === 'type') {
        groupKey = 'Тип, пропускная характеристика';
        sortKey = 'Тип запорной части. Материал затвора/ корпуса';
    } else if (mode === 'name') {
        groupKey = 'DN (мм)';
        sortKey = 'Тип запорной части. Материал затвора/ корпуса';
        numericGroup = true;
    } else {
        sortKey = 'Производство';
        groupKey = 'Производство';
    }
    filtered.sort((a, b) => {
        // Внутри группы сортировка идёт по sortKey (для обоих режимов —
        // это «Тип запорной части. Материал затвора/ корпуса», текстовое поле).
        const va = (a[sortKey] || '').toString();
        const vb = (b[sortKey] || '').toString();
        const la = va.toLowerCase(), lb = vb.toLowerCase();
        if (la < lb) return -1;
        if (la > lb) return 1;
        // При равном sortKey — вторичная сортировка по марке
        const ma = (a['Марка'] || '').toString().toLowerCase();
        const mb = (b['Марка'] || '').toString().toLowerCase();
        return ma.localeCompare(mb);
    });

    // Фильтр по «№ проекта» (из карточки проекта)
    if (kipIsProjectLinkFilterActive('valves')) {
        filtered = filtered.filter(d => kipMatchesProjectFilter(d, 'valves'));
    }
    // Фильтр по «№ СБС» (из карточки блокировки)
    if (kipIsSbsLinkFilterActive('valves')) {
        filtered = filtered.filter(d => kipMatchesSbsFilter(d, 'valves'));
    }
    // Фильтр по «№ САР» (из карточки регулятора)
    if (kipIsSarLinkFilterActive('valves')) {
        filtered = filtered.filter(d => kipMatchesSarFilter(d, 'valves'));
    }

    if (query) {
        filtered = filtered.filter(d =>
            VALVE_FIELDS.some(f => valveNorm(d[f.key] || '').includes(query))
        );
    }

    // Группировка по groupKey. Порядок групп по умолчанию — порядок первого
    // вхождения после сортировки по sortKey. Для режима name (DN) дополнительно
    // пересортируем группы численно (DN 50, DN 100, DN 200 …), чтобы не было
    // алфавитного порядка (DN 100, DN 200, DN 50).
    const groups = {};
    const groupOrder = [];
    for (const d of filtered) {
        const g = d[groupKey] || '(без группы)';
        if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
        groups[g].push(d);
    }
    if (numericGroup) {
        groupOrder.sort((a, b) => {
            if (a === '(без группы)' && b === '(без группы)') return 0;
            if (a === '(без группы)') return 1;
            if (b === '(без группы)') return -1;
            const na = parseFloat(a.replace(',', '.'));
            const nb = parseFloat(b.replace(',', '.'));
            if (isNaN(na) && isNaN(nb)) return a.toLowerCase().localeCompare(b.toLowerCase());
            if (isNaN(na)) return 1;
            if (isNaN(nb)) return -1;
            if (na !== nb) return na - nb;
            return 0;
        });
    }

    info.textContent = '';

    if (filtered.length === 0) {
        let emptyHtml = '';
        if (kipIsProjectLinkFilterActive('valves')) {
            emptyHtml += kipRenderFilterBadge('valves');
            emptyHtml += '<div class="pb-empty">По проекту №«' + valveEsc(window.kipProjectLinkFilter.projectNo) + '» клапанов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (kipIsSbsLinkFilterActive('valves')) {
            emptyHtml += kipRenderSbsFilterBadge('valves');
            emptyHtml += '<div class="pb-empty">По СБС №«' + valveEsc(window.kipSbsLinkFilter.sbsNo) + '» клапанов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (kipIsSarLinkFilterActive('valves')) {
            emptyHtml += kipRenderSarFilterBadge('valves');
            emptyHtml += '<div class="pb-empty">По САР №«' + valveEsc(window.kipSarLinkFilter.sarNo) + '» клапанов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">Ничего не найдено.<br>Попробуйте изменить запрос.</div>';
        }
        list.innerHTML = emptyHtml;
        kipBindFilterBadge(list, 'valves', valveRenderSorted);
        kipBindSbsFilterBadge(list, 'valves', valveRenderSorted);
        kipBindSarFilterBadge(list, 'valves', valveRenderSorted);
        // Свайп для добавления в избранное
        if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.valve-card', 'valve', 'data-valve-id');
        return;
    }

    let html = '';
    // Бейдж активного фильтра по проекту (вверху списка)
    if (kipIsProjectLinkFilterActive('valves')) {
        html += kipRenderFilterBadge('valves');
    }
    // Бейдж активного фильтра по «№ СБС» (вверху списка)
    if (kipIsSbsLinkFilterActive('valves')) {
        html += kipRenderSbsFilterBadge('valves');
    }
    // Бейдж активного фильтра по «№ САР» (вверху списка)
    if (kipIsSarLinkFilterActive('valves')) {
        html += kipRenderSarFilterBadge('valves');
    }
    html += '<div class="valve-sorted-list' + (query ? ' searching' : '') + '">';
    for (const g of groupOrder) {
        const items = groups[g];
        const gKey = mode + '|' + g;
        const isGroupExpanded = query ? true : (valveGroupExpanded[gKey] === true);

        html += '<div class="pb-section valve-group' + (isGroupExpanded ? ' expanded' : '') + '" data-group="' + valveEsc(g) + '" data-mode="' + mode + '">';
        html += '<div class="pb-section-title valve-group-title" onclick="valveToggleGroup(this)">';
        html += '<span class="pb-section-title-text">' + valveMark(g, query) + '</span>';
        html += '<span class="pb-section-title-count">' + items.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';

        for (const item of items) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Марка'] || item['Назначение арматуры (параметр)'] || '(без названия)';
            const type = item['Тип, пропускная характеристика'] || '';
            const place = item['Место расположения'] || '';

            html += '<div class="valve-card" data-valve-id="' + valveEsc(itemId) + '" data-mode="' + mode + '">';
            html += KipFav._cardFavBtnHtml(itemId, 'valve');
            html += '<div class="valve-card-header" onclick="valveOpenDetail(\'' + valveEsc(itemId) + '\')">';
            html += '<div class="valve-card-header-inner">';
            html += '<div class="valve-card-text">';
            html += '<div class="valve-card-title">' + valveMark(name, query) + '</div>';
            let subtitle = '';
            if (type) subtitle += type;
            if (place) subtitle += (subtitle ? ' · ' : '') + place;
            if (subtitle) html += '<div class="valve-card-subtitle">' + valveMark(subtitle, query) + '</div>';
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
    kipBindFilterBadge(list, 'valves', valveRenderSorted);
    kipBindSbsFilterBadge(list, 'valves', valveRenderSorted);
    kipBindSarFilterBadge(list, 'valves', valveRenderSorted);
    // Свайп для добавления в избранное
    if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.valve-card', 'valve', 'data-valve-id');
}

function valveToggleGroup(titleEl) {
    const section = titleEl.closest('.pb-section');
    if (!section) return;
    const mode = section.getAttribute('data-mode') || 'type';
    const group = section.getAttribute('data-group');
    if (!group) return;
    if (navigator.vibrate) navigator.vibrate(25);
    window._valveGroupCtx = { mode: mode, group: group };
    window.navigateTo('valve-group');
}

function valveRenderGroup() {
    const kipIsProjectLinkFilterActive = window.kipIsProjectLinkFilterActive;
    const kipIsSbsLinkFilterActive = window.kipIsSbsLinkFilterActive;
    const kipIsSarLinkFilterActive = window.kipIsSarLinkFilterActive;
    const kipMatchesProjectFilter = window.kipMatchesProjectFilter;
    const kipMatchesSbsFilter = window.kipMatchesSbsFilter;
    const kipMatchesSarFilter = window.kipMatchesSarFilter;
    const kipRenderFilterBadge = window.kipRenderFilterBadge;
    const kipRenderSbsFilterBadge = window.kipRenderSbsFilterBadge;
    const kipRenderSarFilterBadge = window.kipRenderSarFilterBadge;
    const kipBindFilterBadge = window.kipBindFilterBadge;
    const kipBindSbsFilterBadge = window.kipBindSbsFilterBadge;
    const kipBindSarFilterBadge = window.kipBindSarFilterBadge;
    const KipFav = window.KipFav;

    const ctx = window._valveGroupCtx || {};
    const mode = ctx.mode || 'type';
    const group = ctx.group || '';
    const list = document.getElementById('valveGroupList');
    const titleEl = document.getElementById('valveGroupTitle');
    if (!list) return;
    // Динамический заголовок страницы группы:
    //   • mode='name' (DN): «DN {значение} (мм)» — например «DN 50 (мм)»
    //   • mode='type': название типа (группы) — например «Отс.»
    //   • mode='prod': название производства
    let pageTitle;
    if (mode === 'name') {
        pageTitle = group ? ('DN ' + group + ' (мм)') : 'Клапана';
    } else {
        pageTitle = group || 'Клапана';
    }
    if (titleEl) titleEl.textContent = pageTitle;
    // На десктопе: заменить заголовок на полные хлебные крошки
    if (window.isDesktop()) window.updateDesktopBreadcrumb(null, pageTitle);

    if (!valveLoaded || !valveData) {
        list.innerHTML = '<div class="pb-empty">Загрузка…</div>';
        return;
    }

    // groupKey — поле, по которому была выполнена группировка на родительской
    // странице. Нужно для отбора клапанов в выбранную группу.
    // subgroupKey — поле подгруппировки (всегда раскрытые подгруппы).
    // sortKey — поле сортировки внутри подгрупп.
    //
    // По уточнению пользователя:
    //   • mode='type' (свайп ←): группировка по «Тип, пропускная характеристика»,
    //     подгруппы внутри — по «Тип запорной части. Материал затвора/ корпуса».
    //   • mode='name' (свайп →): группировка по «DN (мм)»,
    //     подгруппы внутри — по «Тип запорной части. Материал затвора/ корпуса».
    //   • mode='prod' (тап): группировка по производствам,
    //     подгруппы внутри — по «DN (мм)» (численно, по возрастанию).
    let groupKey, subgroupKey, sortKey, numericSubgroups = false;
    if (mode === 'type') {
        groupKey = 'Тип, пропускная характеристика';
        subgroupKey = 'Тип запорной части. Материал затвора/ корпуса';
        sortKey = 'Тип запорной части. Материал затвора/ корпуса';
    } else if (mode === 'name') {
        groupKey = 'DN (мм)';
        subgroupKey = 'Тип запорной части. Материал затвора/ корпуса';
        sortKey = 'Тип запорной части. Материал затвора/ корпуса';
    } else {
        // mode === 'prod'
        groupKey = 'Производство';
        subgroupKey = 'DN (мм)';
        sortKey = 'Тип запорной части. Материал затвора/ корпуса';
        numericSubgroups = true;
    }
    let items = (valveData.valves || []).filter(d => {
        const g = d[groupKey] || '(без группы)';
        return g === group;
    });
    // Применить активный фильтр (проект / СБС / САР), если он установлен.
    // Без этого при клике на группу из отфильтрованного списка будет показан
    // весь список клапанов этой группы, а не только относящиеся к проекту.
    const hasValveFilter = kipIsProjectLinkFilterActive('valves')
        || kipIsSbsLinkFilterActive('valves')
        || kipIsSarLinkFilterActive('valves');
    if (hasValveFilter) {
        items = items.filter(d =>
            kipMatchesProjectFilter(d, 'valves')
            && kipMatchesSbsFilter(d, 'valves')
            && kipMatchesSarFilter(d, 'valves')
        );
    }
    items.sort((a, b) => {
        // Сортировка по subgroupKey (первичный ключ — чтобы подгруппы шли по порядку),
        // затем по sortKey (внутри подгруппы), затем по марке.
        const sa = (a[subgroupKey] || '').toString();
        const sb = (b[subgroupKey] || '').toString();
        if (numericSubgroups) {
            const na = parseFloat(sa.replace(',', '.'));
            const nb = parseFloat(sb.replace(',', '.'));
            if (!isNaN(na) && !isNaN(nb)) {
                if (na !== nb) return na - nb;
            } else if (isNaN(na) && !isNaN(nb)) {
                return 1;
            } else if (!isNaN(na) && isNaN(nb)) {
                return -1;
            }
        } else {
            const la = sa.toLowerCase(), lb = sb.toLowerCase();
            if (la < lb) return -1;
            if (la > lb) return 1;
        }
        // Внутри подгруппы — по sortKey
        const va = (a[sortKey] || '').toString();
        const vb = (b[sortKey] || '').toString();
        const lva = va.toLowerCase(), lvb = vb.toLowerCase();
        if (lva < lvb) return -1;
        if (lva > lvb) return 1;
        // При равном sortKey — по марке
        const ma = (a['Марка'] || '').toString().toLowerCase();
        const mb = (b['Марка'] || '').toString().toLowerCase();
        return ma.localeCompare(mb);
    });

    if (items.length === 0) {
        let emptyHtml = '';
        if (kipIsProjectLinkFilterActive('valves')) {
            emptyHtml += kipRenderFilterBadge('valves');
            emptyHtml += '<div class="pb-empty">В группе «' + valveEsc(pageTitle) + '» по проекту №«' + valveEsc(window.kipProjectLinkFilter.projectNo) + '» клапанов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (kipIsSbsLinkFilterActive('valves')) {
            emptyHtml += kipRenderSbsFilterBadge('valves');
            emptyHtml += '<div class="pb-empty">В группе «' + valveEsc(pageTitle) + '» по СБС №«' + valveEsc(window.kipSbsLinkFilter.sbsNo) + '» клапанов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (kipIsSarLinkFilterActive('valves')) {
            emptyHtml += kipRenderSarFilterBadge('valves');
            emptyHtml += '<div class="pb-empty">В группе «' + valveEsc(pageTitle) + '» по САР №«' + valveEsc(window.kipSarLinkFilter.sarNo) + '» клапанов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">В группе нет клапанов.</div>';
        }
        list.innerHTML = emptyHtml;
        kipBindFilterBadge(list, 'valves', function() { valveRenderGroup(); });
        kipBindSbsFilterBadge(list, 'valves', function() { valveRenderGroup(); });
        kipBindSarFilterBadge(list, 'valves', function() { valveRenderGroup(); });
        // Свайп для добавления в избранное
        if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.valve-card', 'valve', 'data-valve-id');
        return;
    }

    // Подгруппировка по subgroupKey.
    //   • mode='type' / 'name' — по «Тип запорной части. Материал затвора/ корпуса»
    //   • mode='prod' — по «DN (мм)» (численно, по возрастанию)
    // Подгруппы всегда раскрыты (статичные, без сворачивания) — класс .static.
    // Порядок подгрупп — по первому вхождению после сортировки выше.
    const subgroups = {};
    const subgroupOrder = [];
    for (const item of items) {
        const sgRaw = item[subgroupKey] || '(без подгруппы)';
        // Для числовых подгрупп (DN) — нормализуем ключ, чтобы «50» и «50,0»
        // не создавали разные подгруппы. Заголовок будет «DN {значение}».
        let sgKey = sgRaw;
        if (numericSubgroups && sgRaw !== '(без подгруппы)') {
            const num = parseFloat(String(sgRaw).replace(',', '.'));
            if (!isNaN(num)) {
                sgKey = Number.isInteger(num) ? String(num) : String(num).replace('.', ',');
            }
        }
        if (!subgroups[sgKey]) { subgroups[sgKey] = []; subgroupOrder.push(sgKey); }
        subgroups[sgKey].push(item);
    }
    // Сортируем подгруппы по алфавиту (или численно для DN)
    if (numericSubgroups) {
        subgroupOrder.sort((a, b) => {
            const na = parseFloat(String(a).replace(',', '.'));
            const nb = parseFloat(String(b).replace(',', '.'));
            if (!isNaN(na) && !isNaN(nb)) return na - nb;
            return a.toString().toLowerCase().localeCompare(b.toString().toLowerCase());
        });
    } else {
        subgroupOrder.sort((a, b) => {
            const va = a.toString().toLowerCase();
            const vb = b.toString().toLowerCase();
            if (va < vb) return -1;
            if (va > vb) return 1;
            return 0;
        });
    }

    let html = '';
    // Бейдж активного фильтра (проект / СБС / САР) вверху страницы группы
    if (kipIsProjectLinkFilterActive('valves')) {
        html += kipRenderFilterBadge('valves');
    } else if (kipIsSbsLinkFilterActive('valves')) {
        html += kipRenderSbsFilterBadge('valves');
    } else if (kipIsSarLinkFilterActive('valves')) {
        html += kipRenderSarFilterBadge('valves');
    }
    html += '<div class="valve-sorted-list">';
    for (const sg of subgroupOrder) {
        const sgItems = subgroups[sg];
        // Заголовок подгруппы:
        //   • numericSubgroups → «DN {значение}» (например «DN 50»)
        //   • иначе → само значение поля (например «Односедельный, плунжерный»)
        const sgLabel = (numericSubgroups && sg !== '(без подгруппы)')
            ? 'DN ' + sg
            : sg;
        // Статичная (всегда раскрытая) подгруппа
        html += '<div class="pb-section valve-group valve-subgroup static">';
        html += '<div class="pb-section-title">';
        html += '<span class="pb-section-title-text">' + valveEsc(sgLabel) + '</span>';
        html += '<span class="pb-section-title-count">' + sgItems.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';
        for (const item of sgItems) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Марка'] || item['Назначение арматуры (параметр)'] || '(без названия)';
            const type = item['Тип, пропускная характеристика'] || '';
            const place = item['Место расположения'] || '';
            const dn = item['DN (мм)'] || '';
            const shutOff = item['Тип запорной части. Материал затвора/ корпуса'] || '';

            html += '<div class="valve-card" data-valve-id="' + valveEsc(itemId) + '" data-mode="' + mode + '">';
            html += KipFav._cardFavBtnHtml(itemId, 'valve');
            html += '<div class="valve-card-header" onclick="valveOpenDetail(\'' + valveEsc(itemId) + '\')">';
            html += '<div class="valve-card-header-inner">';
            html += '<div class="valve-card-text">';
            html += '<div class="valve-card-title">' + valveEsc(name) + '</div>';
            // Подзаголовок зависит от режима:
            //   • mode='prod' — DN в заголовке подгруппы, поэтому в подзаголовке
            //     показываем «Тип запорной части» + «Тип, пропускная характеристика» + место
            //   • mode='name' / 'type' — «Тип запорной части» в заголовке подгруппы,
            //     поэтому в подзаголовке показываем DN + «Тип, пропускная характеристика» + место
            let subtitleParts = [];
            if (mode === 'prod') {
                if (shutOff) subtitleParts.push(shutOff);
            } else {
                if (dn) subtitleParts.push('DN ' + valveEsc(dn));
            }
            if (type) subtitleParts.push(type);
            if (place) subtitleParts.push(place);
            if (subtitleParts.length) {
                html += '<div class="valve-card-subtitle">' + valveEsc(subtitleParts.join(' · ')) + '</div>';
            }
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
    kipBindFilterBadge(list, 'valves', function() { valveRenderGroup(); });
    kipBindSbsFilterBadge(list, 'valves', function() { valveRenderGroup(); });
    kipBindSarFilterBadge(list, 'valves', function() { valveRenderGroup(); });
    // Свайп для добавления в избранное
    if (typeof KipFav !== 'undefined') KipFav.wrapKipCardsForFavSwipe('.valve-card', 'valve', 'data-valve-id');
}

function valveScrollToGroup(el) {
    if (!el) return;
    const mode = el.getAttribute('data-mode') || 'type';
    const ph = document.querySelector('#page-valves-' + mode + ' .page-inline-header');
    const stickyHeight = ph ? ph.offsetHeight : 56;
    const rect = el.getBoundingClientRect();
    const targetY = window.scrollY + rect.top - stickyHeight - 8;
    window.scrollTo({ top: Math.max(0, targetY), behavior: 'auto' });
}

// ===== Открытие карточки клапана (отдельная страница, как у приборов/блокировок) =====
function valveOpenDetail(valveId) {
    if (!valveId) return;
    if (navigator.vibrate) navigator.vibrate(15);
    window._valveDetailId = valveId;
    if (window.isDesktop()) {
        window.valveRenderDetailInPanel();
    } else {
        window.navigateTo('valve-detail');
    }
}

function valveRenderDetail() {
    const valveId = window._valveDetailId;
    if (!valveId || !valveLoaded || !valveData) return;
    const item = valveData.valves.find(d => String(d['ID'] ?? '') === String(valveId));
    if (!item) return;
    const titleEl = document.getElementById('valveDetailTitle');
    const content = document.getElementById('valveDetailContent');
    if (!titleEl || !content) return;
    const name = item['Марка'] || item['Назначение арматуры (параметр)'] || '(без названия)';
    titleEl.textContent = name;

    let html = '<div class="valve-detail-card">';
    // Значок избранного в правом верхнем углу (виден только на десктопе)
    html += '<button type="button" class="dev-detail-fav-btn" onclick="KipFav.toggleFromDetailByType(\'valve\')" aria-label="Избранное" title="Добавить/убрать из избранного"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button>';
    html += '<div class="valve-detail-rows">';
    for (const f of VALVE_FIELDS) {
        if (f.hiddenInCard) continue;
        let val = item[f.key];
        if (val === undefined || val === null || val === '') continue;
        if (f.key === 'Дата проверки') val = valveFormatDate(val);
        const grpCls = f.group ? ' valve-row-group-' + f.group : '';
        html += '<div class="valve-detail-row' + grpCls + '">';
        html += '<div class="valve-detail-label">' + valveEsc(f.label) + '</div>';
        // Для поля «№ проекта» — кликабельная ссылка в карточку проекта
        // (только если значение не пустое/«Нет данных»).
        // Если значение содержит несколько номеров (через ',' или ';'),
        // каждое число становится отдельной кликабельной ссылкой.
        if (f.key === '№ проекта' && !window.kipIsEmptyProjectNo(val)) {
            const parts = window.kipSplitProjectValues(val);
            html += '<div class="valve-detail-value kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'project', valveEsc);
            html += '</div>';
        } else if (f.key === '№ СБС' && !window.kipIsEmptySbsNo(val)) {
            const parts = window.kipSplitIdValues(val);
            html += '<div class="valve-detail-value kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'sbs', valveEsc);
            html += '</div>';
        } else if (f.key === '№ САРиРУ' && !window.kipIsEmptySarNo(val)) {
            const parts = window.kipSplitIdValues(val);
            html += '<div class="valve-detail-value kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'sar', valveEsc);
            html += '</div>';
        } else {
            html += '<div class="valve-detail-value">' + valveEsc(String(val)) + '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    content.innerHTML = html;
    // Обновить состояние кнопки избранного в карточке
    window.KipFav.updateDetailFavBtnByType('valve', valveId);
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
    // Привязка кликов по ссылкам «№ САРиРУ» → карточка регулятора
    content.querySelectorAll('[data-sar-link]').forEach(function(el) {
        el.addEventListener('click', function() {
            window.regulatorOpenBySarNo(this.getAttribute('data-sar-link'));
        });
    });
    // Обновить значок избранного в заголовке (мобильный)
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

// ===== Кнопка «Клапана» на странице КИП И ОС: tap + свайпы =====
// Логика идентична кнопке «Приборы» (см. devInitEntryButton), но с другими
// целевыми страницами и цветом подложки.
// tap → по производствам (valves-prod)
// swipe ← (влево, справа налево) → по типу (valves-type)
// swipe → (вправо, слева направо) → по DN (valves-name, переиспользуем id типа 'name' для совместимости со старым роутингом)
const VALVE_SWIPE_THRESHOLD = 12;    // px до определения направления
const VALVE_SWIPE_NAV_RATIO = 0.3;   // доля ширины для перехода
let valveSwipeState = null;
let valveSwipeMoved = false;

function valveInitEntryButton() {
    const btn = document.getElementById('valvesEntryBtn');
    if (!btn || btn.dataset.initialized) return;
    btn.dataset.initialized = '1';

    btn.addEventListener('pointerdown', onValveSwipePointerDown);
    // Тап без свайпа → по производствам
    btn.addEventListener('click', function() {
        if (valveSwipeMoved) return;
        if (navigator.vibrate) navigator.vibrate(15);
        window.navigateTo('valves-prod');
    });
    // Обновить sublabel количеством клапанов
    valveUpdateEntrySublabel();
}

function onValveSwipePointerDown(e) {
    if (e.button !== undefined && e.button !== 0) return;
    const el = e.currentTarget;
    const cell = document.getElementById('valveSwipeCell');
    if (!el || !cell) return;
    const rect = el.getBoundingClientRect();
    valveSwipeState = {
        el: el,
        cell: cell,
        startX: e.clientX,
        startY: e.clientY,
        width: rect.width,
        currentDx: 0,
        active: false,
        moved: false
    };
    window.addEventListener('pointermove', onValveSwipePointerMove);
    window.addEventListener('pointerup', onValveSwipePointerUp);
    window.addEventListener('pointercancel', onValveSwipePointerUp);
}

function onValveSwipePointerMove(e) {
    if (!valveSwipeState) return;
    const st = valveSwipeState;
    const dx = e.clientX - st.startX;
    const dy = e.clientY - st.startY;
    if (!st.active) {
        if (Math.abs(dx) > VALVE_SWIPE_THRESHOLD || Math.abs(dy) > VALVE_SWIPE_THRESHOLD) {
            if (Math.abs(dx) > Math.abs(dy) * 1.5) {
                st.active = true;
                st.el.classList.add('swipe-active');
                st.el.style.pointerEvents = 'none';
                if (navigator.vibrate) navigator.vibrate(10);
            } else {
                // Вертикальное — скролл, отменяем
                cleanupValveSwipe();
                return;
            }
        } else {
            return;
        }
    }
    e.preventDefault();
    let effectiveDx = dx;
    if (Math.abs(dx) > st.width) {
        const overshoot = Math.abs(dx) - st.width;
        effectiveDx = Math.sign(dx) * (st.width + overshoot * 0.3);
    }
    st.currentDx = effectiveDx;
    st.el.style.transform = 'translateX(' + effectiveDx + 'px)';
    st.cell.classList.toggle('swiping-left',  effectiveDx < 0);
    st.cell.classList.toggle('swiping-right', effectiveDx > 0);
}

function onValveSwipePointerUp(e) {
    if (!valveSwipeState) return;
    const st = valveSwipeState;
    const threshold = st.width * VALVE_SWIPE_NAV_RATIO;
    const shouldNav = st.active && Math.abs(st.currentDx) > threshold;
    const isLeft = st.currentDx < 0;

    if (shouldNav) {
        if (navigator.vibrate) navigator.vibrate(20);
        st.el.classList.remove('swipe-active');
        st.el.style.transition = 'transform 0.2s ease-out, opacity 0.2s ease-out';
        st.el.style.transform = 'translateX(' + (isLeft ? '-100%' : '100%') + ')';
        st.el.style.opacity = '0';
        // swipe влево (dx < 0) → valves-type (по типу, пропускная характеристика)
        // swipe вправо (dx > 0) → valves-name (по DN, мм)
        const targetPage = isLeft ? 'valves-type' : 'valves-name';
        setTimeout(function() {
            window.navigateTo(targetPage);
            setTimeout(function() {
                st.el.style.transition = '';
                st.el.style.opacity = '';
                st.el.style.transform = '';
                st.el.style.pointerEvents = '';
                st.cell.classList.remove('swiping-left', 'swiping-right');
            }, 100);
        }, 200);
        valveSwipeState = null;
        window.removeEventListener('pointermove', onValveSwipePointerMove);
        window.removeEventListener('pointerup', onValveSwipePointerUp);
        window.removeEventListener('pointercancel', onValveSwipePointerUp);
    } else {
        st.el.classList.remove('swipe-active');
        st.el.style.transform = '';
        st.el.style.pointerEvents = '';
        st.cell.classList.remove('swiping-left', 'swiping-right');
        st.moved = st.active;
        cleanupValveSwipe();
    }
}

function cleanupValveSwipe() {
    if (!valveSwipeState) return;
    const st = valveSwipeState;
    st.el.classList.remove('swipe-active');
    st.el.style.pointerEvents = '';
    st.el.style.transform = '';
    if (st.cell) {
        st.cell.classList.remove('swiping-left', 'swiping-right');
    }
    if (st.active) {
        valveSwipeMoved = true;
        setTimeout(function() { valveSwipeMoved = false; }, 300);
    }
    valveSwipeState = null;
    window.removeEventListener('pointermove', onValveSwipePointerMove);
    window.removeEventListener('pointerup', onValveSwipePointerUp);
    window.removeEventListener('pointercancel', onValveSwipePointerUp);
}

async function valveUpdateEntrySublabel() {
    const btn = document.getElementById('valvesEntryBtn');
    if (!btn) return;
    const sublabel = btn.querySelector('.menu-btn-sublabel');
    if (!sublabel) return;
    if (!valveLoaded || !valveData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/valves.json' + bust, { cache: 'no-store' });
            if (!resp.ok) return;
            valveData = await resp.json();
            valveLoaded = true;
            localStorage.setItem('valvesLastUpdate', new Date().toISOString());
        } catch (e) { return; }
    }
    const count = (valveData.valves || []).length;
    sublabel.textContent = count + ' ' + valvePlural(count, ['клапан', 'клапана', 'клапанов']) + ' КИП ИОС';
}

// ===== Exports =====
export {
    VALVE_FIELDS,
    VALVE_SWIPE_THRESHOLD,
    VALVE_SWIPE_NAV_RATIO,
    valveData,
    valveLoaded,
    valveGroupExpanded,
    valveSwipeState,
    valveSwipeMoved,
    valveEsc,
    valveNorm,
    valveMark,
    valvePlural,
    valveFormatDate,
    valveGetLastUpdateDate,
    valveInitSorted,
    valveForceRefresh,
    valveRenderSorted,
    valveToggleGroup,
    valveRenderGroup,
    valveScrollToGroup,
    valveOpenDetail,
    valveRenderDetail,
    valveInitEntryButton,
    valveUpdateEntrySublabel,
    onValveSwipePointerDown,
    onValveSwipePointerMove,
    onValveSwipePointerUp,
    cleanupValveSwipe,
};
