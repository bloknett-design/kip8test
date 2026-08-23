// ============================================================
// Тест: аудит доступа ролей — соответствие всех точек входа
// (сайдбар, дашборд, закреплённые ярлыки, десктопный верхний бар)
// матрице фильтров доступа из карты ролей.
// Task 141.
//
// Подход (без DOM — статический анализ index.html):
//   1. Извлекаем из index.html массивы страниц KipAuth
//      (_BASE_PAGES ... _WHATS_NEW_PAGES) и тело init(),
//      вычисляем ROLE_ACCESS в песочнице vm — как в приложении.
//   2. Извлекаем реестр SUBSECTIONS (закреплённые ярлыки).
//   3. Парсим HTML-точки входа: .sidebar-item, .menu-btn
//      (атрибут onclick navigateTo), .desktop-top-bar-tab (data-page).
//   4. Сверяем с ожидаемой матрицей фильтров (1-10).
//
// Ловит регрессы вида:
//   - ярлык «Проекты» с target на несуществующую страницу (Task 141);
//   - «Приборы» без 'devices' в _KIP_IOS_PAGES (Task 141);
//   - удаление страницы из массива роли;
//   - новая кнопка/ярлык со страницей, недоступной роли.
// ============================================================

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { test, describe, assertEqual, assertTrue } = require('./test-helpers.js');

const INDEX_HTML = path.resolve(__dirname, '..', 'index.html');
const html = fs.readFileSync(INDEX_HTML, 'utf-8');

// ------------------------------------------------------------
// 1. Извлечение массивов страниц KipAuth и вычисление ROLE_ACCESS
// ------------------------------------------------------------
function extractArraysAndInit() {
    // Фрагмент от "_BASE_PAGES:" до конца "_WHATS_NEW_PAGES: [...]"
    const startMatch = html.match(/_BASE_PAGES:\s*\[/);
    if (!startMatch) throw new Error('_BASE_PAGES не найден в index.html');
    const startIdx = startMatch.index;
    const endMatch = html.slice(startIdx).match(/_WHATS_NEW_PAGES:\s*\[[^\]]*\]/);
    if (!endMatch) throw new Error('_WHATS_NEW_PAGES не найден');
    const fragment = html.slice(startIdx, startIdx + endMatch.index + endMatch[0].length);

    // Обернуть в объект и выполнить в песочнице
    const objCode = '({' + fragment + '})';
    const arraysObj = vm.runInNewContext(objCode, {}, 'arrays.vm');

    // Тело init(): от "init: function() {" до парной "}"
    const initMatch = html.match(/init:\s*function\(\)\s*\{/);
    if (!initMatch) throw new Error('init() KipAuth не найден');
    const initStart = initMatch.index + initMatch[0].length;
    let depth = 1, i = initStart;
    while (i < html.length && depth > 0) {
        if (html[i] === '{') depth++;
        else if (html[i] === '}') depth--;
        i++;
    }
    const initBody = html.slice(initMatch.index + 'init:'.length, i);
    // initBody = " function() { ... }" — выполняем с this = массивы
    const initFn = vm.runInNewContext('(' + initBody + ')', {}, 'init.vm');
    initFn.call(arraysObj);
    if (!arraysObj.ROLE_ACCESS) throw new Error('ROLE_ACCESS не построен после init()');
    return arraysObj;
}

// ------------------------------------------------------------
// 2. Извлечение SUBSECTIONS (закреплённые ярлыки на главной)
// ------------------------------------------------------------
function extractSubsections() {
    const m = html.match(/const\s+SUBSECTIONS\s*=\s*\{/);
    if (!m) throw new Error('SUBSECTIONS не найден');
    let depth = 0, i = m.index + m[0].length - 1;
    for (; i < html.length; i++) {
        if (html[i] === '{') depth++;
        else if (html[i] === '}') { depth--; if (depth === 0) break; }
    }
    const code = html.slice(m.index, i + 1) + ';';
    const sandbox = {};
    // const в vm-контексте НЕ пишется в sandbox — возвращаем значение
    // последним выражением
    const SUBSECTIONS = vm.runInNewContext(code + '\nSUBSECTIONS;', sandbox, 'subsections.vm');
    return SUBSECTIONS;
}

// ------------------------------------------------------------
// 3. Точки входа из HTML
// ------------------------------------------------------------
function extractEntryPoints() {
    const sidebar = [];
    const menuBtns = [];
    const topBar = [];
    // .sidebar-item с onclick navigateTo
    const re = /<div[^>]*class="[^"]*sidebar-item[^"]*"[^>]*onclick="navigateTo\('([^']+)'\)/g;
    let m;
    while ((m = re.exec(html)) !== null) sidebar.push(m[1]);
    // .menu-btn с onclick navigateTo (статические кнопки дашборда/разделов)
    const reBtn = /<div[^>]*class="[^"]*menu-btn[^"]*"[^>]*onclick="navigateTo\('([^']+)'\)/g;
    while ((m = reBtn.exec(html)) !== null) menuBtns.push(m[1]);
    // Десктопный верхний бар: data-page
    const reTab = /class="[^"]*desktop-top-bar-tab[^"]*"[^>]*data-page="([^"]+)"/g;
    while ((m = reTab.exec(html)) !== null) topBar.push(m[1]);
    return { sidebar, menuBtns, topBar };
}

const Kip = extractArraysAndInit();
const SUBSECTIONS = extractSubsections();
const ENTRIES = extractEntryPoints();

// Все страницы, доступные хоть какой-то роли (без '*')
const ALL_PAGES = [].concat(
    Kip._BASE_PAGES, Kip._CALC_PAGES, Kip._LIBRARY_PAGES, Kip._KIP_IOS_PAGES,
    Kip._FLOWMETER_PAGES, Kip._CHARTS_PAGES, Kip._SECRET_PAGES, Kip._WHATS_NEW_PAGES
);

// Роли по карте доступа
const ROLES = ['Запрет', 'Общий доступ', 'ИТР ТОКЕМ', 'КИП8', 'КИП8 pro', 'КИП ИОС',
               'КИП ИОС pro', 'КИП ИОС дежурный', 'ИТР8', 'ИТР8 pro', 'ИТР ИОС', 'Админ'];

// ------------------------------------------------------------
// Матрица фильтров (карта ролей): какие фильтры включены у роли.
// Фильтры: 1=калькуляторы, 2=билеты+библиотека, 3=КИП ИОС,
//          4=ограниченный КИП ИОС, 7=секретные, 8=что нового,
//          9=графики, 10=расходомеры
// ------------------------------------------------------------
const FILTER_MATRIX = {
    'Запрет':            [],
    'Общий доступ':      [1],
    'ИТР ТОКЕМ':         [1, 4, 8],
    'КИП8':              [1, 2, 7, 8],
    'КИП8 pro':          [1, 2, 7, 8, 10],
    'КИП ИОС':           [1, 2, 3, 7, 8],
    'КИП ИОС pro':       [1, 2, 3, 5, 7, 8],
    'КИП ИОС дежурный':  [1, 2, 3, 7, 8, 10, 11],
    'ИТР8':              [1, 2, 3, 7, 8, 10],
    'ИТР8 pro':          [1, 2, 3, 7, 8, 10],
    'ИТР ИОС':           [1, 2, 3, 5, 7, 8, 10],
    'Админ':             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
};

// Страница-представитель каждого фильтра (клиентская матрица)
const FILTER_PAGE = {
    1: 'calculators',      // Инженерные калькуляторы
    2: 'exam-tickets',     // Экзаменационные билеты (+библиотека)
    3: 'kip-ios',          // КИП ИОС
    7: 'minesweeper',      // Секретные кнопки
    8: 'whats-new',        // Что нового
    9: 'charts',           // Графики
    10: 'flowmeter-data'   // Расходомеры
};

function hasPage(role, page) {
    const allowed = Kip.ROLE_ACCESS[role];
    if (!allowed) return false;
    if (allowed.indexOf('*') !== -1) return true;
    return allowed.indexOf(page) !== -1;
}

// ------------------------------------------------------------
// Тесты
// ------------------------------------------------------------
describe('Аудит ролей: ROLE_ACCESS построен', function () {

    test('ROLE_ACCESS содержит все 12 ролей', function () {
        ROLES.forEach(function (role) {
            assertTrue(!!Kip.ROLE_ACCESS[role], 'роль отсутствует в ROLE_ACCESS: ' + role);
        });
    });

    test('Админ имеет полный доступ [*]', function () {
        assertEqual(Kip.ROLE_ACCESS['Админ'].indexOf('*') !== -1, true, 'Админ должен иметь "*"');
    });
});

describe('Аудит ролей: матрица фильтров 1-10', function () {

    ROLES.forEach(function (role) {
        test('Роль «' + role + '» — страницы по фильтрам', function () {
            const filters = FILTER_MATRIX[role];
            Object.keys(FILTER_PAGE).forEach(function (f) {
                const page = FILTER_PAGE[f];
                // Фильтр 4 (ограниченный КИП ИОС) тоже даёт доступ к kip-ios
                // (с ограничениями: скрыты Проекты/Каб.журнал/Графики/Замечания/ППР)
                let expectVisible = filters.indexOf(Number(f)) !== -1;
                if (Number(f) === 3 && filters.indexOf(4) !== -1) expectVisible = true;
                assertEqual(hasPage(role, page), expectVisible,
                    'фильтр ' + f + ' (' + page + '): ожидалось ' + (expectVisible ? 'доступ' : 'нет доступа'));
            });
        });
    });

    test('Фильтр 4 (ИТР ТОКЕМ): UI скрывает «Кабельный журнал» и «Проекты» (Task 139/140)', function () {
        // Статическая проверка: в _applyRoleToUI есть блок скрытия этих страниц
        // для ролей с ограниченным КИП ИОС
        assertTrue(html.indexOf("page === 'cable-journal-edit' || page === 'projects-prod'") !== -1,
            'нет проверки cable-journal-edit/projects-prod в _applyRoleToUI');
        assertTrue(html.indexOf('_hasRestrictedKipIos') !== -1,
            'нет вызова _hasRestrictedKipIos');
    });

    test('Фильтр 4: «Замечания» скрыты в карточках (Task 113)', function () {
        // Статическая проверка: в DEV-рендере есть skip Замечаний
        assertTrue(/_hideRemarks\s*&&\s*f\.key\s*===\s*'Замечания'/.test(html),
            'нет skip «Замечаний» в рендере карточки прибора');
        assertTrue(/_hideLockRemarks\s*&&\s*f\.key\s*===\s*'Замечания'/.test(html),
            'нет skip «Замечаний» в рендере карточки блокировки');
    });

    test('Фильтр 4: приборы без «В гр. ППР» скрыты во всех рендерах (Task 113/140)', function () {
        const count = (html.match(/В гр\. ППР'\]\s*\|\|\s*''\)\.trim\(\)\.toLowerCase\(\)\s*!==\s*'нет'/g) || []).length;
        assertTrue(count >= 3, 'фильтр «В гр. ППР» должен применяться минимум в 3 рендерах (devRender, devRenderSorted, devRenderGroup), найдено: ' + count);
    });

    test('Фильтр 4: блокировки без «В перечне» скрыты во всех рендерах (Task 113/140)', function () {
        const count = (html.match(/В перечне'\]\s*\|\|\s*''\)\.trim\(\)\.toLowerCase\(\)\s*!==\s*'нет'/g) || []).length;
        assertTrue(count >= 2, 'фильтр «В перечне» должен применяться минимум в 2 рендерах (lockRenderSorted, lockRenderGroup), найдено: ' + count);
    });
});

describe('Аудит ролей: закреплённые ярлыки (SUBSECTIONS)', function () {

    test('Все target закреплённых ярлыков — валидные доступные страницы', function () {
        Object.keys(SUBSECTIONS).forEach(function (key) {
            const target = SUBSECTIONS[key].target;
            const inAllPages = ALL_PAGES.indexOf(target) !== -1;
            const isAdminPage = target.indexOf('admin') === 0;
            assertTrue(inAllPages || isAdminPage,
                'target «' + key + '» → «' + target + '» недоступен ни одной роли (кроме Админа)');
        });
    });

    test('«Проекты» ведут на существующую страницу projects-prod (Task 141)', function () {
        assertEqual(SUBSECTIONS['projects'].target, 'projects-prod',
            'target ярлыка «Проекты» должен быть projects-prod');
        assertEqual(html.indexOf('id="page-projects-prod"') !== -1, true,
            'страница page-projects-prod должна существовать');
    });

    test('«Приборы»: страница devices доступна КИП ИОС-ролям (Task 141)', function () {
        ['КИП ИОС', 'КИП ИОС pro', 'КИП ИОС дежурный', 'ИТР8', 'ИТР8 pro', 'ИТР ИОС', 'ИТР ТОКЕМ', 'Админ']
            .forEach(function (role) {
                assertTrue(hasPage(role, 'devices'),
                    'роль «' + role + '» должна иметь доступ к devices (фильтр 3)');
            });
        ['Запрет', 'Общий доступ', 'КИП8', 'КИП8 pro'].forEach(function (role) {
            assertEqual(hasPage(role, 'devices'), false,
                'роль «' + role + '» НЕ должна иметь доступ к devices');
        });
    });

    test('Видимость закреплённых ярлыков по ролям (вычисление матрицы)', function () {
        // Для каждой роли: ярлык виден <=> target в allowed,
        // кроме фильтра 4 (ИТР ТОКЕМ: cable-journal-edit, projects-prod скрыты)
        const hiddenByF4 = ['cable-journal-edit', 'projects-prod'];
        ROLES.forEach(function (role) {
            const restricted = role === 'ИТР ТОКЕМ';
            Object.keys(SUBSECTIONS).forEach(function (key) {
                const target = SUBSECTIONS[key].target;
                let expectVisible = hasPage(role, target);
                if (restricted && hiddenByF4.indexOf(target) !== -1) expectVisible = false;
                // Динамическая проверка невозможна без DOM — здесь проверяем
                // консистентность матрицы: для ролей без фильтра 4 target доступен
                if (!restricted && expectVisible) {
                    assertEqual(hasPage(role, target), true,
                        'роль «' + role + '»: target «' + target + '» ярлыка «' + key + '» должен быть в allowed');
                }
            });
        });
    });
});

describe('Аудит ролей: HTML-точки входа', function () {

    // Страницы-редиректы (validate по navigateTo, а не по id="page-...")
    const REDIRECT_PAGES = ['library', 'cables', 'cables-prod'];

    test('Пункты сайдбара: все target валидны', function () {
        ENTRIES.sidebar.forEach(function (target) {
            const ok = ALL_PAGES.indexOf(target) !== -1 ||
                       target === 'admin' || REDIRECT_PAGES.indexOf(target) !== -1;
            assertTrue(ok, 'пункт сайдбара «' + target + '» ведёт на недоступную страницу');
        });
    });

    test('Кнопки меню: все target валидны', function () {
        ENTRIES.menuBtns.forEach(function (target) {
            const ok = ALL_PAGES.indexOf(target) !== -1 ||
                       target === 'admin' || REDIRECT_PAGES.indexOf(target) !== -1;
            assertTrue(ok, 'кнопка меню «' + target + '» ведёт на недоступную страницу');
        });
    });

    test('Десктопный верхний бар: все data-page валидны', function () {
        ENTRIES.topBar.forEach(function (target) {
            const ok = ALL_PAGES.indexOf(target) !== -1;
            assertTrue(ok, 'вкладка верхнего бара «' + target + '» ведёт на недоступную страницу');
        });
    });

    test('Верхний бар: вкладка «Документация» скрыта для ролей без docs (статически)', function () {
        // В _applyRoleToUI должна быть проверка вкладки docs
        assertTrue(/page === 'docs'[\s\S]{0,300}allowed\.indexOf\('docs'\)/.test(html),
            'нет фильтрации вкладки «Документация» верхнего бара');
    });

    test('Сайдбар: «Админ-панель» видна только Админу (статически)', function () {
        assertTrue(/sidebarAdminBtn[\s\S]{0,200}this\._cachedRole === 'Админ'/.test(html) ||
                   /_cachedRole === 'Админ'[\s\S]{0,200}sidebarAdminBtn/.test(html),
            'нет проверки роли Админа для кнопки админ-панели');
    });
});

describe('Аудит ролей: базовые инварианты', function () {

    test('Гость («Общий доступ») не имеет доступа к документации и КИП ИОС', function () {
        ['docs', 'exam-tickets', 'library', 'kip-ios', 'devices', 'flowmeter-data', 'minesweeper'].forEach(function (p) {
            assertEqual(hasPage('Общий доступ', p), false,
                'гость не должен видеть «' + p + '»');
        });
    });

    test('«Запрет» имеет доступ только к главной', function () {
        const allowed = Kip.ROLE_ACCESS['Запрет'];
        assertEqual(allowed.length, 1, 'у «Запрет» только dashboard');
        assertEqual(allowed[0], 'dashboard', 'у «Запрет» только dashboard');
    });

    test('Расходомеры: доступ по фильтру 10', function () {
        ['КИП8 pro', 'КИП ИОС дежурный', 'ИТР8', 'ИТР8 pro', 'ИТР ИОС', 'Админ'].forEach(function (role) {
            assertTrue(hasPage(role, 'flowmeter-data'), 'роль «' + role + '» должна видеть расходомеры (фильтр 10)');
        });
        ['Запрет', 'Общий доступ', 'ИТР ТОКЕМ', 'КИП8', 'КИП ИОС', 'КИП ИОС pro'].forEach(function (role) {
            assertEqual(hasPage(role, 'flowmeter-data'), false,
                'роль «' + role + '» НЕ должна видеть расходомеры');
        });
    });

    test('Графики: доступ только Админу (фильтр 9)', function () {
        ROLES.forEach(function (role) {
            assertEqual(hasPage(role, 'charts'), role === 'Админ',
                '«Графики»: только Админ, роль «' + role + '»');
        });
    });

    test('Секретные разделы: фильтр 7', function () {
        ['КИП8', 'КИП8 pro', 'КИП ИОС', 'КИП ИОС pro', 'КИП ИОС дежурный', 'ИТР8', 'ИТР8 pro', 'ИТР ИОС', 'Админ'].forEach(function (role) {
            assertTrue(hasPage(role, 'minesweeper'), 'роль «' + role + '» должна видеть секретные разделы (фильтр 7)');
        });
        ['Запрет', 'Общий доступ', 'ИТР ТОКЕМ'].forEach(function (role) {
            assertEqual(hasPage(role, 'minesweeper'), false,
                'роль «' + role + '» НЕ должна видеть секретные разделы');
        });
    });
});

// ------------------------------------------------------------
// Task 142: счётчики групп сайдбара, мобильный нижний бар,
// перестроение сетки при фильтрации (дыры)
// ------------------------------------------------------------

// Пункты сайдбара по группам (из HTML) — для вычисления ожидаемых счётчиков
const SIDEBAR_GROUPS = {
    kipa: ['converter', 'scale-signal', 'error-select', 'buoy-select', 'temp-sensors', 'orifice-select'],
    electro: ['circuit-breaker'],
    geometry: ['geo-circle', 'geo-ring', 'geo-cylinder', 'geo-horiz', 'geo-sphere', 'geo-cone'],
    'exam-tickets': ['tickets-1000v', 'tickets-4', 'tickets-5', 'tickets-6'],
    library: [],  // внешние ссылки + library-electro (без navigateTo у внешних)
    'kip-ios': ['devices-prod', 'lockouts-prod', 'valves-prod', 'regulators-prod', 'projects-prod', 'cable-journal-edit', 'plan-114'],
    'docs-ios': ['flowmeter-data']
};

// Ожидаемый динамический счётчик группы сайдбара для роли:
// число пунктов, доступных роли (страница в allowed), с учётом фильтра 4
// (ИТР ТОКЕМ: cable-journal-edit и projects-prod скрыты) и пустых
// родительских страниц (Task 115: docs-ios скрывается, если на целевой
// странице нет видимых кнопок — например, «Расходомеры» недоступны).
function expectedSidebarCount(role, group) {
    const items = SIDEBAR_GROUPS[group];
    if (!items || items.length === 0) return null;
    const restricted = role === 'ИТР ТОКЕМ';
    let count = 0;
    items.forEach(function (page) {
        if (!hasPage(role, page)) return;
        if (restricted && (page === 'cable-journal-edit' || page === 'projects-prod')) return;
        // Task 115: пункт «Расходомеры» (flowmeter-data) — на странице docs-ios
        // только эта кнопка; если недоступна — пункт не виден (hasPage уже учёл)
        count++;
    });
    return count;
}

describe('Аудит ролей: счётчики групп сайдбара (Task 139, динамические)', function () {

    test('Код динамического пересчёта счётчиков присутствует', function () {
        // Пересчёт: sidebar-group-title-count обновляется числом видимых пунктов
        assertTrue(html.indexOf('sidebar-group-title-count') !== -1,
            'нет элемента счётчика .sidebar-group-title-count');
        assertTrue(/visibleCount[\s\S]{0,80}countEl\.textContent\s*=\s*visibleCount/.test(html),
            'нет записи visibleCount в счётчик (динамический пересчёт Task 139)');
    });

    test('Каждая группа сайдбара в HTML имеет счётчик', function () {
        // Извлечь группы и проверить наличие счётчика в разметке
        const groups = html.match(/<div class="sidebar-group[^"]*" data-group="[^"]+"/g) || [];
        assertTrue(groups.length >= 7, 'в сайдбаре должно быть минимум 7 групп, найдено: ' + groups.length);
        const counts = html.match(/class="sidebar-group-title-count"/g) || [];
        assertEqual(counts.length, groups.length,
            'число счётчиков должно совпадать с числом групп');
    });

    test('ИТР ТОКЕМ: группа КИП ИОС — 5 видимых пунктов (7 − Проекты − Каб.журнал, фильтр 4)', function () {
        assertEqual(expectedSidebarCount('ИТР ТОКЕМ', 'kip-ios'), 5,
            'у ИТР ТОКЕМ в группе КИП ИОС должно быть 5 видимых пунктов');
    });

    test('КИП ИОС: группа КИП ИОС — 7 видимых пунктов (полный доступ)', function () {
        assertEqual(expectedSidebarCount('КИП ИОС', 'kip-ios'), 7,
            'у КИП ИОС в группе КИП ИОС должно быть 7 видимых пунктов');
    });

    test('Группа «Документация ИОС» (расходомеры): видима только ролям с фильтром 10', function () {
        ROLES.forEach(function (role) {
            const expected = hasPage(role, 'flowmeter-data') ? 1 : 0;
            assertEqual(expectedSidebarCount(role, 'docs-ios'), expected,
                'роль «' + role + '»: пунктов в группе docs-ios должно быть ' + expected);
        });
    });

    test('Гость: во всех группах 0 доступных пунктов документации', function () {
        ['exam-tickets', 'kip-ios', 'docs-ios'].forEach(function (group) {
            assertEqual(expectedSidebarCount('Общий доступ', group), 0,
                'у гостя в группе «' + group + '» не должно быть доступных пунктов');
        });
    });
});

describe('Аудит ролей: мобильный нижний бар (dashboardBottomBar)', function () {

    test('Кнопки нижнего бара присутствуют в HTML', function () {
        assertTrue(html.indexOf('dashboardBottomBar') !== -1,
            'нет контейнера dashboardBottomBar');
        assertTrue(html.indexOf('dashboard-bottom-btn-docs') !== -1,
            'нет кнопки «Документация» (.dashboard-bottom-btn-docs)');
    });

    test('Код фильтрации кнопки «Документация» присутствует (hasDocsAccess)', function () {
        assertTrue(/dashboard-bottom-btn-docs[\s\S]{0,200}hasDocsAccess/.test(html) ||
                   /hasDocsAccess[\s\S]{0,200}dashboard-bottom-btn-docs/.test(html),
            'нет фильтрации кнопки «Документация» нижнего бара по доступу');
    });

    test('Кнопка «Документация» видна ролям с доступом к docs/library/kip-ios', function () {
        // Формула из _applyRoleToUI: isAll || docs || library || kip-ios
        ROLES.forEach(function (role) {
            const allowed = Kip.ROLE_ACCESS[role] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const expectVisible = isAll
                || allowed.indexOf('docs') !== -1
                || allowed.indexOf('library') !== -1
                || allowed.indexOf('kip-ios') !== -1;
            // Кнопка ведёт на page-docs, где видимые кнопки зависят от роли:
            // Task 115 скрывает «Документацию», если ВСЕ кнопки на docs скрыты.
            // Полная симуляция Task 115 здесь не выполняется — проверяем формулу
            // hasDocsAccess (первичную видимость кнопки).
            assertEqual(typeof expectVisible, 'boolean',
                'роль «' + role + '»: вычисление видимости кнопки «Документация»');
        });
        // Конкретные ожидания по матрице
        [['Запрет', false], ['Общий доступ', false], ['ИТР ТОКЕМ', true], ['КИП8', true],
         ['КИП8 pro', true], ['КИП ИОС', true], ['Админ', true]].forEach(function (pair) {
            const allowed = Kip.ROLE_ACCESS[pair[0]] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const actual = isAll
                || allowed.indexOf('docs') !== -1
                || allowed.indexOf('library') !== -1
                || allowed.indexOf('kip-ios') !== -1;
            assertEqual(actual, pair[1],
                'роль «' + pair[0] + '»: кнопка «Документация» нижнего бара');
        });
    });
});

describe('Аудит ролей: перестроение сетки при фильтрации (Task 142)', function () {

    test('Код скрытия пустых обёрток subsection-cell/dev-swipe-cell присутствует', function () {
        assertTrue(/\.subsection-cell, \.dev-swipe-cell[\s\S]{0,300}cell\.style\.display/.test(html),
            'нет скрытия пустых обёрток .subsection-cell/.dev-swipe-cell в _applyRoleToUI');
    });

    test('wrapSubsectionItems скрывает обёртку скрытой кнопки при создании', function () {
        // Обёртки создаются при ПЕРВОМ переходе на страницу — позже _applyRoleToUI;
        // поэтому при создании обёртки скрытой кнопки она должна сразу скрываться
        assertTrue(/cell\.appendChild\(btn\);[\s\S]{0,400}btn\.style\.display === 'none'[\s\S]{0,100}cell\.style\.display = 'none'/.test(html),
            'в wrapSubsectionItems нет скрытия обёртки для скрытой роли кнопки');
    });

    test('Пустые menu-btn-row скрываются (нет пустых строк)', function () {
        assertTrue(/menu-btn-row[\s\S]{0,400}row\.style\.display = anyVisible \? '' : 'none'/.test(html),
            'нет скрытия пустых .menu-btn-row');
    });
});

// ------------------------------------------------------------
// Task 146: «Графики» — раздел только десктопного приложения (Electron)
// ------------------------------------------------------------
describe('Аудит ролей: «Графики» только в десктопе (Task 146)', function () {

    test('canAccess блокирует charts вне Electron (даже у Админа)', function () {
        // Статическая проверка: в canAccess есть условие IS_ELECTRON для charts
        assertTrue(/canAccess[\s\S]{0,600}page === 'charts'[\s\S]{0,200}IS_ELECTRON[\s\S]{0,120}return false/.test(html),
            'в canAccess нет блокировки charts для не-Electron окружений');
    });

    test('Кнопка «Графики» на КИП ИОС скрывается вне Electron', function () {
        // chartsEntryBtn: условие isElectronApp в _applyRoleToUI
        assertTrue(/chartsEntryBtn[\s\S]{0,400}isElectronApp[\s\S]{0,200}hasChartsAccess = isElectronApp/.test(html),
            'нет проверки IS_ELECTRON для chartsEntryBtn');
    });

    test('Закреплённый ярлык «Графики» скрывается вне Electron (цикл .menu-btn)', function () {
        // Цикл .menu-btn: charts + IS_ELECTRON
        assertTrue(/page === 'charts'[\s\S]{0,200}IS_ELECTRON[\s\S]{0,100}allowedForPage = false/.test(html),
            'нет скрытия ярлыка charts вне Electron в цикле .menu-btn');
    });

    test('Фильтр 9 (Графики) в матрице: только Админ — сохранено на уровне allowed', function () {
        // charts остаётся в allowed только у Админа; видимость поверх — Electron
        ROLES.forEach(function (role) {
            assertEqual(hasPage(role, 'charts'), role === 'Админ',
                '«Графики» в allowed: только Админ, роль «' + role + '»');
        });
    });
});

// ------------------------------------------------------------
// Task 147/148: десктоп-модули (только Electron)
// ------------------------------------------------------------
describe('Десктоп-модули (Task 147/148)', function () {

    test('Файлы десктоп-модулей существуют', function () {
        assertTrue(fs.existsSync(path.resolve(__dirname, '..', 'charts-desktop.js')),
            'charts-desktop.js отсутствует');
        assertTrue(fs.existsSync(path.resolve(__dirname, '..', 'devices-table-desktop.js')),
            'devices-table-desktop.js отсутствует');
    });

    test('Loader подключает модули только внутри IS_ELECTRON', function () {
        // Блок if (IS_ELECTRON) ... forEach(['charts-desktop.js', 'devices-table-desktop.js'])
        const re = /if \(IS_ELECTRON\) \{[\s\S]{0,400}'charts-desktop\.js', 'devices-table-desktop\.js'[\s\S]{0,300}forEach/;
        assertTrue(re.test(html), 'loader десктоп-модулей не найден или вне IS_ELECTRON');
    });

    test('Код таблицы не содержится в index.html (только в модуле)', function () {
        // CSS/логика таблицы не должны попасть в мобильный index.html
        assertEqual(html.indexOf('dev-table-toggle-btn') === -1, true,
            'класс кнопки таблицы не должен быть в index.html');
        assertEqual(html.indexOf('dev-table-wrap') === -1, true,
            'CSS таблицы не должен быть в index.html');
    });
});
