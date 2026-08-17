/**
 * @module catalogs/projects
 * @description Projects catalog — list view, detail view, group navigation,
 * entry button on KIP IOS dashboard.  Data source: projects.json.
 * Lines ~6609–7238 of the original index.html.
 */

// ===== ПРОЕКТЫ (зеркало регуляторов/клапанов/блокировок) =====
// Поля соответствуют листу "Проекты" Google Sheets
// https://docs.google.com/spreadsheets/d/1IQq8S4-Qao1eJKli3zgMvTpA2exkGYg0/edit
// (файл «Перечень проектов КИП пр-ва ИОС»)
// Реальная структура полей определяется на этапе парсинга sync-projects.py.
// Если в данных есть колонки, не указанные в PROJECT_FIELDS — они не будут показаны.
const PROJECT_FIELDS = [
    { key: 'Наименование проекта', label: 'Наименование проекта', group: 1, hiddenInCard: true },
    { key: '№ проекта',            label: '№ проекта',            group: 1 },
    { key: 'Отделение',            label: 'Отделение',            group: 1 },
    { key: 'Статус проекта',       label: 'Статус проекта',       group: 2 },
    { key: 'Данные статуса',       label: 'Данные статуса',       group: 2 },
    { key: 'Дата утв.',            label: 'Дата утв.',            group: 3 },
    // «Файл проекта» скрыт в карточке — вместо отдельной строки
    // № проекта делается кликабельной ссылкой, если в «Файл проекта»
    // есть рабочая ссылка (http:// или https://). См. projectRenderDetail.
    { key: 'Файл проекта',         label: 'Файл проекта',         group: 3, hiddenInCard: true },
    { key: 'Примечание',           label: 'Примечание',           group: 4 },
    { key: 'Жёлтым отмечены приоритетные проекты', label: 'Приоритетный', group: 4 },
];
let projectData = null;
let projectLoaded = false;
let projectGroupExpanded = {};

function projectEsc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function projectNorm(s) {
    if (s == null) return '';
    return String(s).toLowerCase().replace(/[ё]/g, 'е').replace(/[^a-zа-я0-9]/gi, '');
}
function projectMark(text, query) {
    if (!query) return projectEsc(text);
    const t = String(text);
    const q = projectNorm(query);
    if (!q) return projectEsc(t);
    const idx = projectNorm(t).indexOf(q);
    if (idx === -1) return projectEsc(t);
    const before = t.substring(0, idx);
    const match = t.substring(idx, idx + q.length);
    const after = t.substring(idx + q.length);
    return projectEsc(before) + '<mark>' + projectEsc(match) + '</mark>' + projectMark(after, query);
}
// Рабочая ссылка на файл проекта — это URL (http:// или https://),
// извлечённый из гиперссылки Excel sync-projects.py.
// Локальные пути «Проекты_Files\...» не считаются рабочими ссылками.
// Возвращает '' если ссылки нет или она нерабочая.
function getProjectFileUrl(item) {
    const raw = String(item && item['Файл проекта'] || '').trim();
    return (raw.startsWith('http://') || raw.startsWith('https://')) ? raw : '';
}
// Сгенерировать HTML-строку для № проекта в предварительной карточке.
// Если есть рабочая ссылка на файл проекта — рендерится как кликабельная <a>
// с классом .kip-project-link (синий цвет, открытие в новой вкладке, stopPropagation).
// Иначе — обычный текст «№ {num}».
// query — текущий поисковый запрос для подсветки совпадений (через projectMark).
function projectRenderCardNumber(num, item, query) {
    if (!num) return '';
    const url = getProjectFileUrl(item);
    if (url) {
        // Подсветка не применяется внутри <a> (projectMark возвращает HTML,
        // который может сломать структуру тегов). Поэтому для кликабельного
        // № подсветку отключаем — простой экранированный текст.
        return '<a class="kip-project-link project-card-num-link" href="' + projectEsc(url) + '" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">'
            + '<span>№ ' + projectEsc(num) + '</span>'
            + '<span class="kip-project-link-arrow">↗</span>'
            + '</a>';
    }
    // Без ссылки — обычный текст с подсветкой.
    return projectMark('№ ' + num, query);
}
function projectPlural(n, forms) {
    const m = n % 100;
    const m1 = m % 10;
    if (m >= 5 && m <= 20) return forms[2];
    if (m1 === 1) return forms[0];
    if (m1 >= 2 && m1 <= 4) return forms[1];
    return forms[2];
}
function projectFormatDate(dateVal) {
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
function projectGetLastUpdateDate() {
    try {
        const raw = localStorage.getItem('projectsLastUpdate');
        if (!raw) return '';
        const d = new Date(raw);
        if (isNaN(d.getTime())) return '';
        return String(d.getDate()).padStart(2, '0') + '.' + String(d.getMonth() + 1).padStart(2, '0') + '.' + d.getFullYear();
    } catch (e) { return ''; }
}
function projectStatusClass(status) {
    const s = String(status || '').toLowerCase().trim();
    if (s === 'выполнен')   return 'project-card-status-done';
    if (s === 'новый')      return 'project-card-status-new';
    if (s === 'остановлен') return 'project-card-status-stopped';
    if (s === 'отменен' || s === 'отменён') return 'project-card-status-cancel';
    return '';
}

// Возвращает timestamp для сортировки по «Дате утв.».
// Поддерживаемые форматы:
//   • ISO:      'YYYY-MM-DD' (например '1994-05-16')
//   • Russian:  'DD.MM.YYYY' (например '16.05.1994')
//   • Excel serial: число > 30000 (дней с 30.12.1899)
//   • '00.00.00' / пусто / нераспознанное → Infinity (в конец списка).
// Это позволяет единообразно сортировать проекты от старых к новым,
// отправляя проекты без даты в конец каждой группы.
function projectDateSortValue(dateVal) {
    if (dateVal === null || dateVal === undefined) return Infinity;
    // Excel serial date
    const num = parseFloat(dateVal);
    if (!isNaN(num) && num > 30000) {
        const epoch = Date.UTC(1899, 11, 30);
        const t = epoch + num * 86400000;
        return isNaN(t) ? Infinity : t;
    }
    const str = String(dateVal).trim();
    if (!str) return Infinity;
    // ISO YYYY-MM-DD
    let m = str.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m) {
        const t = Date.UTC(+m[1], +m[2] - 1, +m[3]);
        return isNaN(t) ? Infinity : t;
    }
    // DD.MM.YYYY (включая невалидные '00.00.00' → Infinity)
    m = str.match(/^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$/);
    if (m) {
        let year = +m[3];
        if (year < 100) year += 2000;
        const day = +m[1];
        const month = +m[2];
        if (day === 0 || month === 0 || year === 0) return Infinity;
        const t = Date.UTC(year, month - 1, day);
        return isNaN(t) ? Infinity : t;
    }
    // Последняя попытка — через Date.parse
    const t = Date.parse(str);
    return isNaN(t) ? Infinity : t;
}

// Возвращает ключ года для группировки по «Дате утв.».
// Валидная дата → строка года ('2024'); невалидная / '00.00.00' / пусто → 'Без даты'.
// Используется для группировки списков проектов в подгруппы по годам.
function projectYearKey(dateVal) {
    const t = projectDateSortValue(dateVal);
    if (t === Infinity) return 'Без даты';
    const d = new Date(t);
    return String(d.getUTCFullYear());
}

async function projectInitSorted(mode) {
    if (!projectLoaded || !projectData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/projects.json' + bust, { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            projectData = await resp.json();
            projectLoaded = true;
            localStorage.setItem('projectsLastUpdate', new Date().toISOString());
        } catch (e) {
            console.error('projectInitSorted error:', e);
            const ids = { prod: 'projectProdList' };
            const el = document.getElementById(ids[mode]);
            if (el) el.innerHTML = '<div class="pb-empty">Ошибка загрузки.<br>Проверьте соединение.</div>';
            return;
        }
    }
    projectsRenderSorted(mode);
}

function projectsForceRefresh(mode) {
    projectData = null;
    projectLoaded = false;
    projectInitSorted(mode);
    if (navigator.vibrate) navigator.vibrate(40);
}

// Alias used in other modules
function projectForceRefresh(mode) {
    projectsForceRefresh(mode);
}

function projectsRenderSorted(mode) {
    const ids = {
        prod: { list: 'projectProdList', info: 'projectProdInfo', search: 'projectProdSearchInput', page: 'page-projects-prod' },
    };
    const id = ids[mode];
    if (!id) return;
    const list = document.getElementById(id.list);
    const info = document.getElementById(id.info);
    if (!list || !info) return;

    if (!projectLoaded || !projectData) {
        list.innerHTML = '';
        info.textContent = 'Загрузка…';
        return;
    }

    const query = projectNorm((document.getElementById(id.search)?.value || '').trim());
    let filtered = projectData.projects || [];

    // Сортировка: по «Отделению», внутри отделения — по «Дате утв.» (старые → новые).
    const sortKey = 'Отделение';
    filtered.sort((a, b) => {
        const va = (a[sortKey] || '').toString().toLowerCase();
        const vb = (b[sortKey] || '').toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        // Внутри отделения — по дате утверждения (от старых к новым).
        const da = projectDateSortValue(a['Дата утв.']);
        const db = projectDateSortValue(b['Дата утв.']);
        if (da < db) return -1;
        if (da > db) return 1;
        // Совпадающие даты (в т.ч. обе Infinity) — добиваем по наименованию.
        const na = (a['Наименование проекта'] || '').toString().toLowerCase();
        const nb = (b['Наименование проекта'] || '').toString().toLowerCase();
        if (na < nb) return -1;
        if (na > nb) return 1;
        return 0;
    });

    if (query) {
        filtered = filtered.filter(d =>
            PROJECT_FIELDS.some(f => projectNorm(d[f.key] || '').includes(query))
        );
    }

    // Группировка верхнего уровня — по «Отделению».
    const groups = {};
    const groupOrder = [];
    for (const d of filtered) {
        const g = d[sortKey] || '(без отделения)';
        if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
        groups[g].push(d);
    }

    // Сортировка самих подгрупп (отделений) по «Дате утв.» —
    // подгруппа с самым старым проектом идёт первой; подгруппы, где все даты
    // пустые/невалидные ('00.00.00'), уходят в конец. При совпадении «минимальной»
    // даты добиваем по алфавиту (имя отделения).
    groupOrder.sort((a, b) => {
        const itemsA = groups[a];
        const itemsB = groups[b];
        let minA = Infinity, minB = Infinity;
        for (const it of itemsA) {
            const v = projectDateSortValue(it['Дата утв.']);
            if (v < minA) minA = v;
        }
        for (const it of itemsB) {
            const v = projectDateSortValue(it['Дата утв.']);
            if (v < minB) minB = v;
        }
        if (minA < minB) return -1;
        if (minA > minB) return 1;
        const va = a.toString().toLowerCase();
        const vb = b.toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    info.textContent = '';

    if (filtered.length === 0) {
        list.innerHTML = '<div class="pb-empty">Ничего не найдено.<br>Попробуйте изменить запрос.</div>';
        return;
    }

    let html = '<div class="project-sorted-list' + (query ? ' searching' : '') + '">';
    for (const g of groupOrder) {
        const items = groups[g];
        const groupKey = mode + '|' + g;
        const isGroupExpanded = query ? true : (projectGroupExpanded[groupKey] === true);

        html += '<div class="pb-section project-group' + (isGroupExpanded ? ' expanded' : '') + '" data-group="' + projectEsc(g) + '" data-mode="' + mode + '">';
        html += '<div class="pb-section-title project-group-title" onclick="projectsToggleGroup(this)">';
        html += '<span class="pb-section-title-text">' + projectMark(g, query) + '</span>';
        html += '<span class="pb-section-title-count">' + items.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';

        for (const item of items) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Наименование проекта'] || '(без названия)';
            const num  = item['№ проекта'] || '';
            const status = item['Статус проекта'] || '';
            const statusCls = projectStatusClass(status);

            html += '<div class="project-card" data-project-id="' + projectEsc(itemId) + '" data-mode="' + mode + '">';
            html += '<div class="project-card-header" onclick="projectOpenDetail(\'' + projectEsc(itemId) + '\')">';
            html += '<div class="project-card-header-inner">';
            html += '<div class="project-card-text">';
            html += '<div class="project-card-title">' + projectMark(name, query) + '</div>';
            // № проекта — кликабельная ссылка (синяя, со стрелкой ↗), если есть
            // рабочая ссылка на файл проекта. Иначе — обычный текст «№ {num}».
            const numHtml = projectRenderCardNumber(num, item, query);
            if (numHtml) html += '<div class="project-card-subtitle">' + numHtml + '</div>';
            if (status) html += '<div class="project-card-status ' + statusCls + '">' + projectMark(status, query) + '</div>';
            html += '</div>';
            html += '</div>';
            html += window.KipFav._cardFavBtnHtml(itemId, 'proj');
            html += window.KipFav._cardFavToggleHtml(itemId, 'proj');
            html += '</div>';
            html += '</div>';
        }
        html += '</div>';
        html += '</div>';
    }
    html += '</div>';
    list.innerHTML = html;
    // Добавить кликабельность значка избранного на карточках проектов
    if (typeof window.KipFav !== 'undefined') window.KipFav.wrapKipCardsForFavSwipe('.project-card', 'proj', 'data-project-id');
}

function projectsToggleGroup(titleEl) {
    const section = titleEl.closest('.pb-section');
    if (!section) return;
    const mode = section.getAttribute('data-mode') || 'prod';
    const group = section.getAttribute('data-group');
    if (!group) return;
    if (navigator.vibrate) navigator.vibrate(25);
    window._projectGroupCtx = { mode: mode, group: group };
    window.navigateTo('project-group');
}

function projectsRenderGroup() {
    const ctx = window._projectGroupCtx || {};
    const mode = ctx.mode || 'prod';
    const group = ctx.group || '';
    const list = document.getElementById('projectGroupList');
    const titleEl = document.getElementById('projectGroupTitle');
    if (!list) return;
    if (titleEl) titleEl.textContent = group || 'Проекты';
    // На десктопе: заменить заголовок на полные хлебные крошки
    if (window.isDesktop()) window.updateDesktopBreadcrumb(null, group || 'Проекты');

    if (!projectLoaded || !projectData) {
        list.innerHTML = '<div class="pb-empty">Загрузка…</div>';
        return;
    }

    // Фильтр по отделению (как было раньше).
    const sortKey = 'Отделение';
    let items = (projectData.projects || []).filter(d => {
        const g = d[sortKey] || '(без отделения)';
        return g === group;
    });
    // Сортировка по «Дате утв.» (от старых к новым).
    // Проекты без даты ('00.00.00' / пусто) уходят в конец списка.
    items.sort((a, b) => {
        const da = projectDateSortValue(a['Дата утв.']);
        const db = projectDateSortValue(b['Дата утв.']);
        if (da < db) return -1;
        if (da > db) return 1;
        // Совпадающие даты (в т.ч. обе Infinity) — добиваем по наименованию.
        const na = (a['Наименование проекта'] || '').toString().toLowerCase();
        const nb = (b['Наименование проекта'] || '').toString().toLowerCase();
        if (na < nb) return -1;
        if (na > nb) return 1;
        return 0;
    });

    if (items.length === 0) {
        list.innerHTML = '<div class="pb-empty">В группе нет проектов.</div>';
        return;
    }

    // Внутри отделения — подгруппы по ГОДУ из «Даты утв.» (без свёртывания).
    // Используется класс .pb-section.static — тело всегда раскрыто,
    // заголовок без кликабельного chevron. 'Без даты' идёт ПЕРВОЙ.
    const yearGroups = {};
    const yearOrder = [];
    for (const item of items) {
        const yk = projectYearKey(item['Дата утв.']);
        if (!yearGroups[yk]) { yearGroups[yk] = []; yearOrder.push(yk); }
        yearGroups[yk].push(item);
    }
    yearOrder.sort((a, b) => {
        if (a === 'Без даты' && b === 'Без даты') return 0;
        if (a === 'Без даты') return -1;
        if (b === 'Без даты') return 1;
        const na = parseInt(a, 10);
        const nb = parseInt(b, 10);
        if (na < nb) return -1;
        if (na > nb) return 1;
        return 0;
    });

    let html = '<div class="project-sorted-list">';
    for (const yk of yearOrder) {
        const yItems = yearGroups[yk];
        // Подгруппа-год — всегда раскрытая (static), без onclick.
        html += '<div class="pb-section project-group project-subgroup static">';
        html += '<div class="pb-section-title">';
        html += '<span class="pb-section-title-text">' + projectEsc(yk) + '</span>';
        html += '<span class="pb-section-title-count">' + yItems.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';
        for (const item of yItems) {
            const itemId = String(item['ID'] ?? '');
            const name = item['Наименование проекта'] || '(без названия)';
            const num  = item['№ проекта'] || '';
            const status = item['Статус проекта'] || '';
            const statusCls = projectStatusClass(status);

            html += '<div class="project-card" data-project-id="' + projectEsc(itemId) + '" data-mode="' + mode + '">';
            html += '<div class="project-card-header" onclick="projectOpenDetail(\'' + projectEsc(itemId) + '\')">';
            html += '<div class="project-card-header-inner">';
            html += '<div class="project-card-text">';
            html += '<div class="project-card-title">' + projectEsc(name) + '</div>';
            // № проекта — кликабельная ссылка (синяя, со стрелкой ↗), если есть
            // рабочая ссылка на файл проекта. Иначе — обычный текст «№ {num}».
            // В режиме группы (без поиска) query не передаётся — подсветка не нужна.
            const numHtml = projectRenderCardNumber(num, item, '');
            if (numHtml) html += '<div class="project-card-subtitle">' + numHtml + '</div>';
            if (status) html += '<div class="project-card-status ' + statusCls + '">' + projectEsc(status) + '</div>';
            html += '</div>';
            html += '</div>';
            html += window.KipFav._cardFavBtnHtml(itemId, 'proj');
            html += window.KipFav._cardFavToggleHtml(itemId, 'proj');
            html += '</div>';
            html += '</div>';
        }
        html += '</div>'; // pb-section-body
        html += '</div>'; // pb-section
    }
    html += '</div>';
    list.innerHTML = html;
    // Добавить кликабельность значка избранного на карточках проектов
    if (typeof window.KipFav !== 'undefined') window.KipFav.wrapKipCardsForFavSwipe('.project-card', 'proj', 'data-project-id');
}

function projectsScrollToGroup(el) {
    if (!el) return;
    const mode = el.getAttribute('data-mode') || 'prod';
    const ph = document.querySelector('#page-projects-' + mode + ' .page-inline-header');
    const stickyHeight = ph ? ph.offsetHeight : 56;
    const rect = el.getBoundingClientRect();
    const targetY = window.scrollY + rect.top - stickyHeight - 8;
    window.scrollTo({ top: Math.max(0, targetY), behavior: 'auto' });
}

// ===== Открытие карточки проекта (отдельная страница) =====
function projectOpenDetail(projectId) {
    if (!projectId) return;
    if (navigator.vibrate) navigator.vibrate(15);
    window._projectDetailId = projectId;
    if (window.isDesktop()) {
        window.projectRenderDetailInPanel();
    } else {
        window.navigateTo('project-detail');
    }
}

// ===== Открытие карточки проекта по внешнему «№ проекта» =====
// Используется для перекрёстных ссылок из других разделов КИП ИОС
// (приборы / блокировки / клапаны / регуляторы / кабельный журнал).
// Если projects.json ещё не загружен — догружаем, затем ищем проект
// по точному совпадению поля «№ проекта» (с нормализацией регистра/пробелов),
// в fallback — по частичному совпадению. Если ничего не найдено — alert.
async function projectOpenByProjectNo(projectNo) {
    if (projectNo == null) return;
    const raw = String(projectNo).trim();
    if (!raw) return;
    // Защита: явно пустые значения («Нет данных», «-», «н/д») не обрабатываем
    if (window.kipIsEmptyProjectNo(raw)) {
        if (navigator.vibrate) navigator.vibrate(10);
        alert('№ проекта не указан.');
        return;
    }
    if (navigator.vibrate) navigator.vibrate(15);

    // Догрузить projects.json, если ещё не загружен
    if (!projectLoaded || !projectData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/projects.json' + bust, { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            projectData = await resp.json();
            projectLoaded = true;
            localStorage.setItem('projectsLastUpdate', new Date().toISOString());
        } catch (e) {
            console.error('projectOpenByProjectNo: ошибка загрузки projects.json:', e);
            alert('Не удалось загрузить данные проектов. Проверьте соединение.');
            return;
        }
    }

    // Нормализация: нижний регистр, ё→е, обрезка пробелов по краям.
    // Внутренние пробелы оставляем (номера проектов могут содержать их),
    // но схлопываем подряд идущие.
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');

    const items = projectData.projects || [];
    const r = norm(raw);

    // 1) Точное совпадение по «№ проекта»
    const exact = items.find(d => norm(d['№ проекта']) === r);
    if (exact && exact['ID'] != null && exact['ID'] !== '') {
        projectOpenDetail(exact['ID']);
        return;
    }

    // 2) Не найдено точное совпадение — показать сообщение.
    //    Частичное совпадение отключено: разные проекты могут содержать
    //    одинаковые подстроки (например, 551-114-363-ТХ и 551-114-363-ТХ-2 —
    //    это РАЗНЫЕ проекты), поэтому соответствие определяется только
    //    по полному совпадению номеров.
    alert('Проект с № «' + raw + '» не найден в базе проектов.');
}

// Вспомогательная функция: считается ли значение «№ проекта» пустым/
// незаполненным. Для таких значений ссылка не рендерится в RenderDetail,
// а в projectOpenByProjectNo показывается короткое сообщение вместо поиска.
// Возвращает true для: пусто, «Нет данных», «нет», «-», «—», «–», «н/д», «n/a».
function kipIsEmptyProjectNo(val) {
    if (val == null) return true;
    const s = String(val).trim().toLowerCase().replace(/[ё]/g, 'е');
    if (!s) return true;
    const empties = ['нет данных', 'нет', '-', '—', '–', '—', 'н/д', 'n/a', 'na', 'null', 'undefined', 'нет сведений'];
    return empties.indexOf(s) !== -1;
}

// ===== Разделение multi-value полей «№ проекта» / «№ СБС» / «№ САР» / «№ САРиРУ» =====
// В исходных данных одно поле может содержать несколько значений, разделённых
// запятой или точкой с запятой. Например:
//   «551-114-363-ТХ; 551-114-677-ТХ» — два разных проекта через ';'
//   «551-114-231-ТХ, 551-114-487-АТХ» — два разных проекта через ','
//   «109, 126» — два разных СБС
//   «513/1,2,3» — ОДИН составной СБС (запятая внутри /-группы — НЕ разделитель)
//   «551-114-487-АТХ-2,3,6» — ОДИН проект (запятая внутри списка подпроектов)
//
// Эти функции корректно разделяют такие значения, чтобы каждое значение
// стало отдельной кликабельной ссылкой в карточке.

// Разделить «№ проекта» на отдельные значения.
// Правила:
//   1. Точкака с запятой ';' ВСЕГДА разделяет разные проекты.
//   2. Запятая ',' разделяет ТОЛЬКО если КАЖДЫЙ полученный фрагмент
//      начинается с полного кода проекта (NNN-NNN-NNN...). Это защищает
//      «551-114-487-АТХ-2,3,6» (один проект) от разбиения на части.
// Возвращает массив непустых строк. Для одиночного значения — [value].
function kipSplitProjectValues(raw) {
    if (raw == null) return [];
    const s = String(raw).trim();
    if (!s) return [];
    const parts = s.split(';').map(p => p.trim()).filter(Boolean);
    let result = [];
    for (const p of parts) {
        if (p.indexOf(',') === -1) {
            result.push(p);
            continue;
        }
        const commaParts = p.split(',').map(x => x.trim()).filter(Boolean);
        const allFull = commaParts.length > 1 &&
            commaParts.every(x => /^\d{3}-\d{3}-\d{3}/.test(x));
        if (allFull) {
            result = result.concat(commaParts);
        } else {
            result.push(p);
        }
    }
    return result;
}

// Разделить «№ СБС» / «№ САР» / «№ САРиРУ» на отдельные значения.
// Это поля с чисто числовыми ID (иногда с суффиксами -1, /1,2,3 и т.п.).
// Правила:
//   1. Запятая ',' и точка с запятой ';' разделяют разные ID.
//   2. Запятые ВНУТРИ /-групп (например «513/1,2,3») НЕ разделяют —
//      это под-ID одного составного номера.
//   3. Удаляются trailing-точки и лишние пробелы.
// Возвращает массив непустых строк.
function kipSplitIdValues(raw) {
    if (raw == null) return [];
    const s = String(raw).trim();
    if (!s) return [];
    // Защитить запятые внутри /-групп: заменить их на placeholder \u0001.
    // /-группа начинается с '/' и содержит ТОЛЬКО цифры и запятые (без пробелов!),
    // заканчивается цифрой. Это позволяет отличить «513/1,2,3» (один составной ID,
    // запятые внутри не разделяют) от «513/1, 2, 3» (три разных ID через запятую).
    const protectedStr = s.replace(/\/\d[\d,]*\d|\/\d/g, function(m) {
        return m.replace(/,/g, '\u0001');
    });
    const parts = protectedStr.split(/[,;]/)
        .map(p => p.trim().replace(/\u0001/g, ',').replace(/\.+$/,'').trim())
        .filter(Boolean);
    return parts;
}

// Сгенерировать HTML-строку с одной или несколькими кликабельными ссылками
// для поля «№ проекта» / «№ СБС» / «№ САР» / «№ САРиРУ».
// parts — уже разделённый массив значений (из kipSplitProjectValues / kipSplitIdValues).
// kind — 'project' | 'sbs' | 'sar' (определяет CSS-класс и data-атрибут).
// escFn — функция экранирования для текущего раздела (devEsc / lockEsc / ...).
// Возвращает HTML-строку (без обёртки <div> — обёртку добавляет вызывающий код).
function kipRenderMultiLinks(parts, kind, escFn) {
    if (!parts || parts.length === 0) return '';
    const cls = kind === 'project' ? 'kip-project-link' :
                kind === 'sbs'     ? 'kip-sbs-link'     :
                kind === 'sar'     ? 'kip-sar-link'     : '';
    const arrowCls = cls + '-arrow';
    const dataAttr = kind === 'project' ? 'data-project-link' :
                     kind === 'sbs'     ? 'data-sbs-link'     :
                     kind === 'sar'     ? 'data-sar-link'     : '';
    const sep = kind === 'project' ? '; ' : ', ';
    let html = '';
    for (let i = 0; i < parts.length; i++) {
        if (i > 0) html += '<span class="kip-link-sep">' + sep + '</span>';
        html += '<span class="' + cls + '" ' + dataAttr + '="' + escFn(parts[i]) + '">';
        html += escFn(parts[i]) + '<span class="' + arrowCls + '">›</span>';
        html += '</span>';
    }
    return html;
}

// ===== projectRenderDetail (called from project-detail page) =====
function projectRenderDetail() {
    const projectId = window._projectDetailId;
    if (!projectId || !projectLoaded || !projectData) return;
    const item = projectData.projects.find(d => String(d['ID'] ?? '') === String(projectId));
    if (!item) return;
    const titleEl = document.getElementById('projectDetailTitle');
    const content = document.getElementById('projectDetailContent');
    if (!titleEl || !content) return;
    const name = item['Наименование проекта'] || '(без названия)';
    titleEl.textContent = name;

    // Рабочая ссылка на файл проекта — это URL (http:// или https://),
    // извлечённый из гиперссылки Excel sync-projects.py.
    // Локальные пути «Проекты_Files\...» не считаются рабочими ссылками.
    // Используется общий helper getProjectFileUrl (см. выше).
    const projectFileUrl = getProjectFileUrl(item);

    let html = '<div class="project-detail-card">';
    // Значок избранного в правом верхнем углу (виден только на десктопе)
    html += '<button type="button" class="dev-detail-fav-btn" onclick="KipFav.toggleFromDetailByType(\'proj\')" aria-label="Избранное" title="Добавить/убрать из избранного"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button>';
    html += '<div class="project-detail-rows">';
    for (const f of PROJECT_FIELDS) {
        if (f.hiddenInCard) continue;
        let val = item[f.key];
        if (val === undefined || val === null || val === '') continue;
        if (f.key === 'Дата утв.') val = projectFormatDate(val);
        // «Приоритетный» — переформулировать как Да/Нет
        if (f.key === 'Жёлтым отмечены приоритетные проекты') {
            const v = String(val).toLowerCase().trim();
            if (v === 'да' || v === 'yes' || v === '1' || v === 'true') val = 'Да';
            else continue;
        }
        const grpCls = f.group ? ' project-row-group-' + f.group : '';
        html += '<div class="project-detail-row' + grpCls + '">';
        html += '<div class="project-detail-label">' + projectEsc(f.label) + '</div>';
        // № проекта — кликабельная ссылка, если есть рабочая ссылка на файл проекта.
        // Используем тот же стиль, что и .kip-project-link (синяя ссылка со стрелкой),
        // чтобы визуально отличать от обычного текста.
        if (f.key === '№ проекта' && projectFileUrl) {
            html += '<div class="project-detail-value">';
            html += '<a class="kip-project-link" href="' + projectEsc(projectFileUrl) + '" target="_blank" rel="noopener noreferrer">';
            html += '<span>' + projectEsc(String(val)) + '</span>';
            html += '<span class="kip-project-link-arrow">↗</span>';
            html += '</a>';
            html += '</div>';
        } else {
            html += '<div class="project-detail-value">' + projectEsc(String(val)) + '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    // Блок «Связанные записи» — обратные ссылки на приборы/блокировки/клапаны/регуляторы/кабели
    const projectNo = item['№ проекта'];
    if (projectNo && !window.kipIsEmptyProjectNo(projectNo)) {
        html += window.kipRenderRelatedBlock(String(projectNo));
    }
    content.innerHTML = html;
    // Запустить фоновую загрузку данных разделов и обновить счётчики
    if (projectNo && !window.kipIsEmptyProjectNo(projectNo)) {
        window.kipLoadAndUpdateRelated(String(projectNo));
    }
    // Обновить значок избранного в заголовке
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

// ===== Кнопка Проекты на странице КИП И ОС =====
function projectsInitEntryButton() {
    const btn = document.getElementById('projectsEntryBtn');
    if (!btn || btn.dataset.initialized) return;
    btn.dataset.initialized = '1';
    btn.addEventListener('click', function() {
        if (navigator.vibrate) navigator.vibrate(15);
        window.navigateTo('projects-prod');
    });
    // Обновить sublabel количеством проектов
    projectsUpdateEntrySublabel();
}
async function projectsUpdateEntrySublabel() {
    const btn = document.getElementById('projectsEntryBtn');
    if (!btn) return;
    const sublabel = btn.querySelector('.menu-btn-sublabel');
    if (!sublabel) return;
    if (!projectLoaded || !projectData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/projects.json' + bust, { cache: 'no-store' });
            if (!resp.ok) return;
            projectData = await resp.json();
            projectLoaded = true;
            localStorage.setItem('projectsLastUpdate', new Date().toISOString());
        } catch (e) { return; }
    }
    const count = (projectData.projects || []).length;
    sublabel.textContent = count + ' ' + projectPlural(count, ['проект', 'проекта', 'проектов']) + ' КИП ИОС';
}

// ===== Exports =====
export {
    PROJECT_FIELDS,
    projectData,
    projectLoaded,
    projectGroupExpanded,
    // Public API (as specified in task)
    projectsInitEntryButton,
    projectsUpdateEntrySublabel,
    projectInitSorted,
    projectForceRefresh,
    projectsForceRefresh,
    projectsRenderSorted,
    projectOpenDetail,
    projectOpenByProjectNo,
    projectRenderDetail,
    projectsToggleGroup,
    projectsRenderGroup,
    projectsScrollToGroup,
    projectRenderCardNumber,
    projectEsc,
    projectNorm,
    projectMark,
    projectPlural,
    projectFormatDate,
    projectGetLastUpdateDate,
    projectStatusClass,
    projectDateSortValue,
    projectYearKey,
    getProjectFileUrl,
    kipIsEmptyProjectNo,
    kipSplitProjectValues,
    kipSplitIdValues,
    kipRenderMultiLinks,
};
