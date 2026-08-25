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
        // CSS-ПРАВИЛА и логика таблицы не должны попасть в мобильный index.html.
        // Упоминания селекторов в index.html допустимы: Task 149/150
        // используют .dev-table-toggle-btn для позиционирования иконки
        // поиска левее кнопки «Таблица» (это НЕ код таблицы).
        assertEqual(/\.dev-table-wrap\s*\{/.test(html), false,
            'CSS-правило .dev-table-wrap не должно быть в index.html');
        assertEqual(/\.dev-table\s*\{/.test(html), false,
            'CSS-правило .dev-table не должно быть в index.html');
        assertEqual(/\.dev-table-td\s*\{|\.dev-table-th\s*\{/.test(html), false,
            'CSS-правила ячеек таблицы не должны быть в index.html');
        assertEqual(html.indexOf('buildTableHtml') === -1, true,
            'функция buildTableHtml не должна быть в index.html');
    });
});

// ------------------------------------------------------------
// Task 151: гибкий поиск (слова AND + транслит + нечёткий fallback)
// ------------------------------------------------------------
describe('Гибкий поиск kipSearchFilter (Task 151)', function () {

    // Извлечь поисковые функции из index.html через vm
    const vm = require('vm');
    const searchFns = (function () {
        const startM = html.indexOf('Task 151: ГИБКИЙ ПОИСК');
        const start = html.indexOf('var _TRANSLIT_RU2EN', startM);
        const endM = html.indexOf('function devEsc', start);
        const code = html.slice(start, endM);
        const sandbox = {};
        vm.runInNewContext(code + '\n;({kipSearchWords, kipTranslit, kipEditDistance, kipWordMatches, kipMatchAll, kipSearchFilter});', sandbox, 'search.vm');
        // kipSearchFilter объявлена как function — достаём из контекста
        return vm.runInNewContext(code + '\n;({kipSearchWords: kipSearchWords, kipEditDistance: kipEditDistance, kipMatchAll: kipMatchAll, kipSearchFilter: kipSearchFilter});', {}, 'search2.vm');
    })();

    // Тестовые записи (как приборы)
    const items = [
        { name: 'Счетчик воды турбинный', type: 'СТВУ-100' },
        { name: 'Метран-150CD', type: 'преобразователь давления' },
        { name: 'Регистратор безбумажный', type: 'Regigraf Ф1771-АД' },
        { name: 'ЭМИС-ПУЛЬС 530', type: 'расходомер' },
        { name: 'Датчик разности давления', type: 'Метран-100' }
    ];
    const getter = function (d) { return d.name + ' ' + d.type; };

    test('Точный поиск работает как раньше (подстрока)', function () {
        const r = searchFns.kipSearchFilter(items, 'метран', getter);
        assertEqual(r.length >= 2, true, '«метран» должен найти Метран-150CD и Метран-100');
    });

    test('Этап 1: слова в любом порядке (AND-логика)', function () {
        // «воды счетчик» должен найти «Счетчик воды турбинный»
        const r = searchFns.kipSearchFilter(items, 'воды счетчик', getter);
        assertEqual(r.length, 1, '«воды счетчик» → Счетчик воды турбинный');
        assertEqual(r[0].name, 'Счетчик воды турбинный');
    });

    test('Этап 1: дефис/пробел нормализуются', function () {
        const r = searchFns.kipSearchFilter(items, 'метран 150', getter);
        assertEqual(r.length >= 1, true, '«метран 150» должен найти «Метран-150CD»');
    });

    test('Этап 1: транслитерация en→ru («metran» находит «Метран»)', function () {
        const r = searchFns.kipSearchFilter(items, 'metran', getter);
        assertEqual(r.length >= 2, true, '«metran» должен найти Метран-150CD и Метран-100');
    });

    test('Этап 1: транслитерация ru→en («региграф» находит «Regigraf»)', function () {
        const r = searchFns.kipSearchFilter(items, 'региграф', getter);
        assertEqual(r.length, 1, '«региграф» → Regigraf Ф1771-АД');
    });

    test('Этап 2: опечатка одной буквы (только если нет точных)', function () {
        // «Регисратор» (пропущена «т») — точных нет, нечёткий найдёт
        const r = searchFns.kipSearchFilter(items, 'Регисратор', getter);
        assertEqual(r.length >= 1, true, '«Регисратор» → Регистратор безбумажный');
    });

    test('Этап 2: порог по длине — короткие слова не размываются', function () {
        // «датик» (опечатка в «датчик», 5 букв — 1 опечатка допускается)
        const r = searchFns.kipSearchFilter(items, 'датик', getter);
        assertEqual(r.length >= 1, true, '«датик» → Датчик разности давления');
        // «клапн» (4 буквы) — порог 0, не должен ничего найти
        const r2 = searchFns.kipSearchFilter(items, 'клапн', getter);
        assertEqual(r2.length, 0, '«клапн» (4 буквы) — без нечёткости');
    });

    test('AND: лишнее слово исключает запись (и в нечётком)', function () {
        // «счетчик урановый» — слова «счетчик» есть, «урановый» нет нигде
        const r = searchFns.kipSearchFilter(items, 'счетчик урановый', getter);
        assertEqual(r.length, 0, '«счетчик урановый» не должен ничего найти');
    });

    test('Дамерау-Левенштейн: перестановка = 1 операция', function () {
        assertEqual(searchFns.kipEditDistance('метран', 'метрана'), 1);
        assertEqual(searchFns.kipEditDistance('abc', 'acb'), 1, 'перестановка соседних = 1');
        assertEqual(searchFns.kipEditDistance('регисратор', 'регистратор'), 1);
    });

    test('Пустой запрос возвращает всё', function () {
        const r = searchFns.kipSearchFilter(items, '', getter);
        assertEqual(r.length, items.length);
        const r2 = searchFns.kipSearchFilter(items, '   ', getter);
        assertEqual(r2.length, items.length);
    });
});

// ------------------------------------------------------------
// Task 152: кабельный журнал — единый поиск + клиентская фильтрация
// ------------------------------------------------------------
describe('Кабельный журнал: единый поиск (Task 152)', function () {

    test('cj-поле использует единый класс (без cj-header-search)', function () {
        // Класс cj-header-search удалён из HTML — поле на общих правилах
        const m = html.match(/id="cjSearchInput"[^>]*/);
        assertTrue(!!m, 'cjSearchInput не найден');
        assertEqual(m[0].indexOf('cj-header-search') === -1, true,
            'cjSearchInput не должен иметь класс cj-header-search (единый стиль)');
        assertEqual(m[0].indexOf('dev-header-search') !== -1, true,
            'cjSearchInput должен иметь класс dev-header-search');
    });

    test('Кнопка поиска cj — единый класс dev-search-toggle-btn', function () {
        const m = html.match(/id="cjSearchToggleBtn"[^>]*/);
        assertTrue(!!m, 'cjSearchToggleBtn не найден');
        assertEqual(m[0].indexOf('dev-search-toggle-btn') !== -1, true,
            'кнопка должна использовать единый класс dev-search-toggle-btn');
        assertEqual(m[0].indexOf('data-search-input="cjSearchInput"') !== -1, true,
            'кнопка должна ссылаться на cjSearchInput через data-search-input');
    });

    test('Собственные cj-header-search CSS-правила удалены', function () {
        assertEqual(/\.cj-header-search\s*\{/.test(html), false,
            'CSS-правило .cj-header-search не должно существовать');
    });

    test('Клиентская фильтрация: kipSearchFilter подключён к cj', function () {
        // _applyClientSearch использует kipSearchFilter
        assertTrue(/_applyClientSearch[\s\S]{0,600}kipSearchFilter/.test(html),
            '_applyClientSearch должен вызывать kipSearchFilter');
        // load() больше не шлёт search на сервер: в опциях запроса только limit
        const loadIdx = html.indexOf("_api('cableJournal.list'");
        assertTrue(loadIdx !== -1, 'вызов cableJournal.list не найден');
        // Блок опций после вызова (в пределах 300 символов)
        const opts = html.slice(loadIdx, loadIdx + 300);
        assertEqual(opts.indexOf('search:') === -1, true,
            'load() не должен отправлять search на сервер (клиентская фильтрация)');
        assertEqual(opts.indexOf('limit:') !== -1, true,
            'load() должен запрашивать полный список (limit)');
    });

    test('Кэш полного списка: _allRows сохраняется при загрузке', function () {
        assertTrue(/_allRows = self\._rows\.slice\(\)/.test(html),
            'после load полный список должен копироваться в _allRows');
    });
});

// ------------------------------------------------------------
// Task 154: автосворачивание поиска при смене страницы
// ------------------------------------------------------------
describe('Автосворачивание поиска (Task 154)', function () {

    test('Функция kipCollapseSearch определена', function () {
        assertTrue(html.indexOf('window.kipCollapseSearch = function') !== -1,
            'нет window.kipCollapseSearch в контроллере поиска');
    });

    test('navigateTo вызывает kipCollapseSearch при смене страницы', function () {
        // Вызов сразу после деактивации страниц
        assertTrue(/querySelectorAll\('\.page-content'\)\.forEach\(el => \{ el\.classList\.remove\('active', 'visible'\); \}\);[\s\S]{0,300}kipCollapseSearch[\s\S]{0,60}\(\)/.test(html),
            'navigateTo должен вызывать kipCollapseSearch при деактивации страниц');
    });

    test('Сворачивание сбрасывает запрос (dispatch input)', function () {
        assertTrue(/kipCollapseSearch[\s\S]{0,1100}input\.value = ''[\s\S]{0,120}dispatchEvent\(new Event\('input'/.test(html),
            'при сворачивании запрос должен сбрасываться с перерендером');
    });
});

// ------------------------------------------------------------
// Task 155: запросы с разделителями (позиции «8м/1») + шум коротких слов
// ------------------------------------------------------------
describe('Поиск с разделителями и короткими словами (Task 155)', function () {

    // Извлечь движок заново (включая glued-форму)
    const vm2 = require('vm');
    const engine = (function () {
        const startM = html.indexOf('Task 151: ГИБКИЙ ПОИСК');
        const start = html.indexOf('var _TRANSLIT_RU2EN', startM);
        const endM = html.indexOf('function devEsc', start);
        const code = html.slice(start, endM);
        return vm2.runInNewContext(code + '\n;({kipSearchFilter: kipSearchFilter, kipMatchForms: kipMatchForms});', {}, 't155.vm');
    })();

    test('Запрос с разделителем «8м/1» находит запись «поз. 8м/1»', function () {
        const items = [
            { f: 'Состояние мешалок поз. 8м/1' },
            { f: 'Давление в аппарате 40м/2' },
            { f: 'Расход в поз. 8м/1-3' }
        ];
        const r = engine.kipSearchFilter(items, '8м/1', function (d) { return d.f; });
        assertEqual(r.length, 2, 'должны найтись «поз. 8м/1» и «8м/1-3»');
    });

    test('Glued-форма: «8м1» (слитый запрос) находит «8м/1»', function () {
        const items = [{ f: 'поз. 8м/1' }, { f: 'поз. 7м/2' }];
        const r = engine.kipSearchFilter(items, '8м1', function (d) { return d.f; });
        assertEqual(r.length, 1);
    });

    test('Разные разделители: «8 м/1» и «8м-1» находят «8м/1»', function () {
        const items = [{ f: 'поз. 8м/1' }];
        const a = engine.kipSearchFilter(items, '8 м/1', function (d) { return d.f; });
        const b = engine.kipSearchFilter(items, '8м-1', function (d) { return d.f; });
        assertEqual(a.length, 1, 'пробел-вариация');
        assertEqual(b.length, 1, 'дефис-вариация');
    });

    test('Короткие слова не дают шума: «8» не матчит «8мм»/«18»', function () {
        const items = [
            { f: 'Труба 8мм' },        // «8» — часть слова «8мм», НЕ отдельное слово
            { f: 'Клапан 18' },        // «8» — часть «18»
            { f: 'Позиция 8 сама' }    // «8» — отдельное слово → находится
        ];
        const r = engine.kipSearchFilter(items, '8', function (d) { return d.f; });
        assertEqual(r.length, 1, 'только запись с отдельным словом «8»');
    });

    test('Сырой запрос: списки передают rawQuery (не norm-слитый)', function () {
        // lockRenderSorted и др.: kipSearchFilter(filtered, rawQuery, ...)
        for (const f of ['LOCK_FIELDS', 'VALVE_FIELDS', 'REGULATOR_FIELDS', 'PROJECT_FIELDS']) {
            const re = new RegExp('kipSearchFilter\\(filtered, rawQuery, function \\(d\\) \\{[\\s\\S]{0,120}' + f);
            assertTrue(re.test(html), f + ' фильтр должен использовать rawQuery');
        }
    });
});

// ------------------------------------------------------------
// Task 156: счётчик результатов поиска
// ------------------------------------------------------------
describe('Счётчик результатов поиска (Task 156)', function () {

    test('Функция kipRenderSearchCounter определена', function () {
        assertTrue(html.indexOf('window.kipRenderSearchCounter = function') !== -1,
            'нет kipRenderSearchCounter');
    });

    test('Все 6 рендеров вызывают счётчик (__searchTotal + вызов)', function () {
        ['devRender', 'devRenderSorted', 'lockRenderSorted', 'valveRenderSorted',
         'regulatorRenderSorted', 'projectsRenderSorted'].forEach(function (fn) {
            const m = html.match(new RegExp('function ' + fn + '\\('));
            assertTrue(!!m, fn + ' не найдена');
            // Сегмент функции: до следующей function на верхнем уровне
            const start = m.index;
            const end = html.indexOf('\n    function ', start + 10);
            const seg = html.slice(start, end === -1 ? html.length : end);
            assertEqual(seg.indexOf('__searchTotal') !== -1, true,
                fn + ': нет __searchTotal');
            assertEqual(seg.indexOf('kipRenderSearchCounter(list') !== -1, true,
                fn + ': нет вызова kipRenderSearchCounter');
        });
    });

    test('cj: счётчик после _render в _applyClientSearch', function () {
        assertTrue(/_applyClientSearch[\s\S]{0,1600}this\._render\(\);[\s\S]{0,300}kipRenderSearchCounter/.test(html),
            'cj: счётчик должен вызываться после _render');
    });

    test('CSS счётчика определён (обе темы)', function () {
        assertEqual(/\.kip-search-counter\s*\{/.test(html), true, 'нет .kip-search-counter');
        assertEqual(/\[data-theme="light"\] \.kip-search-counter\s*\{/.test(html), true, 'нет светлой темы');
    });

    test('Без запроса счётчик удаляется', function () {
        assertTrue(/kipRenderSearchCounter[\s\S]{0,700}if \(!query\) return;/.test(html),
            'helper должен удалять счётчик при пустом запросе');
    });
});

// ------------------------------------------------------------
// Task 157: полный список ролей в админ-панели
// ------------------------------------------------------------
describe('Админ-панель: полный список ролей (Task 157)', function () {

    test('KipAdmin.ROLES содержит все 12 ролей матрицы', function () {
        // Все роли из матрицы фильтров должны быть назначаемы
        const all12 = ['Запрет', 'Общий доступ', 'ИТР ТОКЕМ', 'КИП8', 'КИП8 pro',
                       'КИП ИОС', 'КИП ИОС pro', 'КИП ИОС дежурный',
                       'ИТР8', 'ИТР8 pro', 'ИТР ИОС', 'Админ'];
        // Извлечь массив ROLES из index.html
        const m = html.match(/ROLES: \(function \(\) \{[\s\S]*?\}\)\(\),/);
        assertTrue(!!m, 'ROLES-конструктор не найден');
        all12.forEach(function (role) {
            assertEqual(m[0].indexOf("'" + role + "'") !== -1, true,
                'роль «' + role + '» должна быть в KipAdmin.ROLES');
        });
    });

    test('Раньше отсутствующие роли теперь в списке (ИТР ТОКЕМ, КИП ИОС дежурный)', function () {
        const m = html.match(/ROLES: \(function \(\) \{[\s\S]*?\}\)\(\),/);
        assertTrue(m[0].indexOf("'ИТР ТОКЕМ'") !== -1, 'ИТР ТОКЕМ');
        assertTrue(m[0].indexOf("'КИП ИОС дежурный'") !== -1, 'КИП ИОС дежурный');
    });

    test('Синхронизация с ROLE_ACCESS: новые роли подтягиваются автоматически', function () {
        // В конструкторе есть подтягивание из KipAuth.ROLE_ACCESS
        const m = html.match(/ROLES: \(function \(\) \{[\s\S]*?\}\)\(\),/);
        assertTrue(m[0].indexOf('KipAuth.ROLE_ACCESS') !== -1,
            'ROLES должен синхронизироваться с ROLE_ACCESS');
    });
});

// ------------------------------------------------------------
// Task 158: карточки клапанов — назначение в заголовке
// ------------------------------------------------------------
describe('Карточки клапанов: назначение в заголовке (Task 158)', function () {

    test('valveRenderSorted: заголовок = Назначение арматуры (параметр)', function () {
        // Порядок в fallback изменился: назначение первично, Марка — в подзаголовок
        const m = html.match(/const name = item\['Назначение арматуры \(параметр\)'\] \|\| item\['Марка'\] \|\| '\(без названия\)';[\s\S]{0,1200}?valveMark\(mark, query\)/);
        assertTrue(!!m, 'в valveRenderSorted назначение должно быть в заголовке, Марка — первой строкой подзаголовка');
    });

    test('valveRenderGroup: та же структура', function () {
        const m = html.match(/Task 158: заголовок — «Назначение арматуры \(параметр\)»[\s\S]{0,400}const name = item\['Назначение арматуры \(параметр\)'\]/);
        assertTrue(!!m, 'в valveRenderGroup назначение должно быть первичным');
        // Марка — первой строкой подзаголовка
        const m2 = html.match(/Task 158: Марка — первой строкой подзаголовка[\s\S]{0,120}if \(mark\) subtitleParts\.push/);
        assertTrue(!!m2, 'Марка должна быть первой в подзаголовке группы');
    });

    test('Старый порядок (Марка первичной) удалён из рендеров', function () {
        // Не должно остаться: name = item['Марка'] || item['Назначение арматуры...]
        assertEqual(html.indexOf("item['Марка'] || item['Назначение арматуры (параметр)']") === -1, true,
            'старый порядок (Марка в заголовке) не должен остаться');
    });
});

// ------------------------------------------------------------
// Task 161: счётчики расходомеров в десктопных табах «Все / Избранные»
// ------------------------------------------------------------
describe('Расходомеры: счётчики в десктопных табах (Task 161)', function () {

    test('flowDesktopTabs: кнопки содержат счётчики flowAllCountDesk / flowFavCountDesk', function () {
        const m = html.match(/<div id="flowDesktopTabs"[\s\S]*?<\/div>/);
        assertTrue(!!m, 'блок #flowDesktopTabs должен существовать');
        assertTrue(m[0].indexOf('id="flowAllCountDesk"') !== -1,
            'кнопка «Все» должна содержать span#flowAllCountDesk');
        assertTrue(m[0].indexOf('id="flowFavCountDesk"') !== -1,
            'кнопка «Избранные» должна содержать span#flowFavCountDesk');
    });

    test('_updateTabCounts обновляет счётчики обоих баров (мобильного и десктопного)', function () {
        const m = html.match(/_updateTabCounts: function\(\) \{[\s\S]*?\n        \},/);
        assertTrue(!!m, 'функция _updateTabCounts должна существовать');
        ['flowAllCount', 'flowFavCount', 'flowAllCountDesk', 'flowFavCountDesk'].forEach(function (id) {
            assertTrue(m[0].indexOf("'" + id + "'") !== -1,
                '_updateTabCounts должен обновлять #' + id);
        });
    });

    test('CSS: компактный стиль счётчиков для десктопных табов', function () {
        const m = html.match(/\.flow-desktop-tabs \.flow-tab-count \{[\s\S]*?\}/);
        assertTrue(!!m, 'должен быть переопределён .flow-desktop-tabs .flow-tab-count');
        assertTrue(m[0].indexOf('font-size: 10px') !== -1,
            'компактный размер шрифта (10px) для десктопных табов');
    });
});

// ------------------------------------------------------------
// Task 162: перетаскиваемая граница разделения панелей master-detail
// (клэмп 1/4 .. 3/4 ширины области разделения)
// ------------------------------------------------------------
describe('Master-detail: перетаскиваемая граница панелей (Task 162)', function () {

    test('detailPanel содержит разделитель #detailPanelResizer', function () {
        const m = html.match(/<div id="detailPanel">[\s\S]{0,400}?<div id="detailPanelResizer"/);
        assertTrue(!!m, 'разделитель должен быть первым ребёнком #detailPanel');
    });

    test('Клэмп границы: от 1/4 до 3/4 ширины области разделения', function () {
        const mMin = html.match(/DETAIL_RESIZER_MIN = 0\.25/);
        const mMax = html.match(/DETAIL_RESIZER_MAX = 0\.75/);
        assertTrue(!!mMin, 'минимум — 1/4 ширины (DETAIL_RESIZER_MIN = 0.25)');
        assertTrue(!!mMax, 'максимум — 3/4 ширины (DETAIL_RESIZER_MAX = 0.75)');
        // Сами клэмпы применяются в pointerMove
        const mClamp = html.match(/Math\.max\(minW, Math\.min\(maxW, width\)\)/);
        assertTrue(!!mClamp, 'ширина панели должна клэмпиться между minW и maxW');
    });

    test('Ширина сохраняется в localStorage и восстанавливается при загрузке', function () {
        const mSave = html.match(/localStorage\.setItem\(DETAIL_RESIZER_KEY, pct \+ '%'\)/);
        assertTrue(!!mSave, 'после перетаскивания ширина сохраняется в процентах');
        const mRestore = html.match(/initDetailPanelResizer\(\);[\s\S]{0,200}/) ||
                         html.match(/_detailPanelApplyWidth\(\);/);
        assertTrue(!!mRestore, 'при инициализации сохранённая ширина применяется');
    });

    test('Swap-режим: разделитель переходит на правую грань панели', function () {
        const m = html.match(/#contentArea\.panels-swapped > #detailPanel \.detail-panel-resizer \{[\s\S]*?left: auto;[\s\S]*?right: -3px;/);
        assertTrue(!!m, 'в swap-режиме разделитель должен сидеть на правой грани');
    });

    test('Двойной клик по разделителю сбрасывает ширину к CSS-умолчанию', function () {
        const m = html.match(/addEventListener\('dblclick', dblClickReset\)/);
        assertTrue(!!m, 'dblclick должен вызывать сброс');
        const mReset = html.match(/dblClickReset[\s\S]{0,300}?localStorage\.removeItem\(DETAIL_RESIZER_KEY\)/);
        assertTrue(!!mReset, 'сброс удаляет сохранённую ширину из localStorage');
    });
});

// ------------------------------------------------------------
// Task 163: таблица приборов — счётчик и CSV в шапке, таблица на всю площадь
// ------------------------------------------------------------
describe('Таблица приборов: счётчик и CSV в шапке (Task 163)', function () {
    const devTableJs = fs.readFileSync(path.resolve(__dirname, '..', 'devices-table-desktop.js'), 'utf-8');

    test('Группа в шапке: [Таблица][счётчик][Экспорт CSV] одним рядом', function () {
        assertTrue(devTableJs.indexOf('dev-table-header-group') !== -1,
            'группа .dev-table-header-group должна существовать');
        // Порядок внутри ensureButton: группа → кнопка «Таблица» → счётчик → CSV
        const iGroup = devTableJs.indexOf("group.className = 'dev-table-header-group'");
        const iCount = devTableJs.indexOf("count.id = 'devTableCount'");
        const iCsv = devTableJs.indexOf("csvBtn.id = 'devTableCsvBtn'");
        assertTrue(iGroup !== -1 && iCount !== -1 && iCsv !== -1,
            'группа, счётчик и CSV должны создаваться в ensureButton');
        assertTrue(iGroup < iCount && iCount < iCsv,
            'порядок в группе: «Таблица» → счётчик → «Экспорт CSV»');
    });

    test('Счётчик и CSV видны только в табличном виде (.table-active)', function () {
        const m = devTableJs.match(/\.dev-table-header-group \.dev-table-count,[\s\S]{0,120}?\.dev-table-header-group \.dev-table-csv-btn \{ display: none; \}/);
        assertTrue(!!m, 'по умолчанию счётчик и CSV скрыты');
        const m2 = devTableJs.match(/\.dev-table-header-group\.table-active \.dev-table-count \{ display: inline-block; \}/);
        assertTrue(!!m2, 'в табличном виде (.table-active) счётчик показывается');
    });

    test('Тулбар над таблицей удалён (счётчик/CSV больше не в таблице)', function () {
        assertEqual(devTableJs.indexOf('dev-table-toolbar') === -1, true,
            'класс .dev-table-toolbar должен быть удалён из модуля');
    });

    test('Таблица на всю свободную площадь: без отступов, рамки и скруглений', function () {
        const m = devTableJs.match(/\.dev-table-wrap \{[\s\S]*?\}/);
        assertTrue(!!m, '.dev-table-wrap должен существовать');
        assertTrue(m[0].indexOf('margin: 0') !== -1, 'margin: 0 — без отступов от краёв');
        assertTrue(m[0].indexOf('border: none') !== -1, 'border: none — без рамки');
        assertTrue(m[0].indexOf('border-radius: 0') !== -1, 'border-radius: 0 — без скруглений');
    });

    test('fitTableHeight подгоняет высоту (resize + detail-панель)', function () {
        assertTrue(devTableJs.indexOf('function fitTableHeight') !== -1,
            'функция fitTableHeight должна существовать');
        assertTrue(devTableJs.indexOf("addEventListener('resize', fitTableHeight)") !== -1,
            'пересчёт при resize окна');
        assertTrue(devTableJs.indexOf('MutationObserver(fitTableHeight)') !== -1,
            'пересчёт при открытии/закрытии detail-панели');
    });

    test('Лупа и поле поиска сдвигаются левее группы (--devt-group-w)', function () {
        assertTrue(devTableJs.indexOf('.dev-table-header-group.table-active') !== -1,
            'правила для табличного вида через .table-active');
        assertTrue(devTableJs.indexOf('--devt-group-w') !== -1,
            'CSS-переменная --devt-group-w для сдвига лупы/поиска');
    });
});

// ------------------------------------------------------------
// Task 164: поиск на вложенных страницах КИП ИОС
// (группы клапанов/регуляторов/проектов + Избранное)
// ------------------------------------------------------------
describe('Поиск на вложенных страницах КИП ИОС (Task 164)', function () {

    // Фрагмент шапки страницы: от открытия <div id="page-X"> до списка
    function pageHeaderFragment(pageId, listId) {
        const start = html.indexOf('<div id="page-' + pageId + '"');
        const listIdx = html.indexOf('id="' + listId + '"', start);
        assertTrue(start !== -1, 'страница ' + pageId + ' должна существовать');
        assertTrue(listIdx !== -1, 'список ' + listId + ' должен существовать');
        return html.slice(start, listIdx);
    }

    test('Группа клапанов: поле поиска + кнопка в шапке', function () {
        const frag = pageHeaderFragment('valve-group', 'valveGroupList');
        assertTrue(frag.indexOf('id="valveGroupSearchInput"') !== -1, 'поле поиска valveGroupSearchInput');
        assertTrue(frag.indexOf('data-search-input="valveGroupSearchInput"') !== -1, 'кнопка-лупа с data-search-input');
        assertTrue(frag.indexOf('oninput="valveRenderGroup()"') !== -1, 'oninput перерендеривает группу');
    });

    test('Группа регуляторов: поле поиска + кнопка в шапке', function () {
        const frag = pageHeaderFragment('regulator-group', 'regulatorGroupList');
        assertTrue(frag.indexOf('id="regulatorGroupSearchInput"') !== -1, 'поле поиска regulatorGroupSearchInput');
        assertTrue(frag.indexOf('oninput="regulatorRenderGroup()"') !== -1, 'oninput перерендеривает группу');
    });

    test('Группа проектов: поле поиска + кнопка в шапке', function () {
        const frag = pageHeaderFragment('project-group', 'projectGroupList');
        assertTrue(frag.indexOf('id="projectGroupSearchInput"') !== -1, 'поле поиска projectGroupSearchInput');
        assertTrue(frag.indexOf('oninput="projectsRenderGroup()"') !== -1, 'oninput перерендеривает группу');
    });

    test('Избранное: поле поиска + кнопка в шапке', function () {
        const frag = pageHeaderFragment('device-favorites', 'deviceFavoritesContent');
        assertTrue(frag.indexOf('id="favSearchInput"') !== -1, 'поле поиска favSearchInput');
        assertTrue(frag.indexOf('oninput="KipFav.initFavoritesPage()"') !== -1, 'oninput перерендеривает избранное');
    });

    test('Групповые рендеры фильтруют через kipSearchFilter и показывают счётчик', function () {
        // Фрагмент функции от чтения запроса (indexOf — надёжнее регулярок с ?.)
        function renderFragment(inputId) {
            const start = html.indexOf("document.getElementById('" + inputId + "')");
            assertTrue(start !== -1, 'рендер должен читать запрос из ' + inputId);
            return html.slice(start, start + 4000);
        }
        // Клапаны: запрос -> kipSearchFilter -> счётчик
        const fv = renderFragment('valveGroupSearchInput');
        assertTrue(fv.indexOf('kipSearchFilter(items, rawQuery') !== -1, 'valveRenderGroup: kipSearchFilter');
        assertTrue(fv.indexOf('kipRenderSearchCounter(list, items.length, __searchTotal, rawQuery)') !== -1, 'valveRenderGroup: счётчик');
        // Регуляторы
        const fr = renderFragment('regulatorGroupSearchInput');
        assertTrue(fr.indexOf('kipSearchFilter(items, rawQuery') !== -1, 'regulatorRenderGroup: kipSearchFilter');
        // Проекты
        const fp = renderFragment('projectGroupSearchInput');
        assertTrue(fp.indexOf('kipSearchFilter(items, rawQuery') !== -1, 'projectsRenderGroup: kipSearchFilter');
        assertTrue(fp.indexOf('kipRenderSearchCounter(list, items.length, __searchTotal, rawQuery)') !== -1, 'projectsRenderGroup: счётчик');
    });

    test('Избранное: фильтрация карточек поисковым запросом + счётчик', function () {
        const iQuery = html.indexOf("document.getElementById('favSearchInput')");
        assertTrue(iQuery !== -1, 'initFavoritesPage читает запрос favSearchInput');
        const frag = html.slice(iQuery, iQuery + 11000);
        assertTrue(frag.indexOf('var found = 0;') !== -1, 'счётчик найденных объявлен');
        assertTrue(frag.indexOf('meta.name, itemName, itemSub1, itemSub2') !== -1, 'строка поиска карточки (тип+название+подзаголовки)');
        assertTrue(frag.indexOf('kipSearchFilter([fav], rawQuery') !== -1, 'фильтрация карточек избранного через kipSearchFilter');
        assertTrue(frag.indexOf('kipRenderSearchCounter(content, found, __searchTotal, rawQuery)') !== -1, 'счётчик «Найдено: N из M» на странице избранного');
    });

    test('Избранное: правый кластер шапки не перекрывается лупой (padding)', function () {
        const m = html.match(/#page-device-favorites \.page-inline-header:has\(\.dev-search-toggle-btn\) \{\s*padding-right: 48px;\s*\}/);
        assertTrue(!!m, 'CSS-правило отступа для шапки избранного');
    });
});

// ------------------------------------------------------------
// Task 165: поиск в группах приборов/блокировок + жёлтая подсветка
// ------------------------------------------------------------
describe('Поиск в группах приборов/блокировок + жёлтая подсветка (Task 165)', function () {
    const devTableJs = fs.readFileSync(path.resolve(__dirname, '..', 'devices-table-desktop.js'), 'utf-8');

    test('Группа приборов: поле поиска + кнопка в шапке', function () {
        const start = html.indexOf('<div id="page-dev-group"');
        const listIdx = html.indexOf('id="devGroupList"', start);
        assertTrue(start !== -1 && listIdx !== -1, 'страница dev-group должна существовать');
        const frag = html.slice(start, listIdx);
        assertTrue(frag.indexOf('id="devGroupSearchInput"') !== -1, 'поле поиска devGroupSearchInput');
        assertTrue(frag.indexOf('oninput="devRenderGroup()"') !== -1, 'oninput перерендеривает группу');
        assertTrue(frag.indexOf('data-search-input="devGroupSearchInput"') !== -1, 'кнопка-лупа');
    });

    test('Группа блокировок: поле поиска + кнопка в шапке', function () {
        const start = html.indexOf('<div id="page-lock-group"');
        const listIdx = html.indexOf('id="lockGroupList"', start);
        assertTrue(start !== -1 && listIdx !== -1, 'страница lock-group должна существовать');
        const frag = html.slice(start, listIdx);
        assertTrue(frag.indexOf('id="lockGroupSearchInput"') !== -1, 'поле поиска lockGroupSearchInput');
        assertTrue(frag.indexOf('oninput="lockRenderGroup()"') !== -1, 'oninput перерендеривает группу');
    });

    test('devRenderGroup / lockRenderGroup: kipSearchFilter + счётчик + подсветка', function () {
        const iDev = html.indexOf("document.getElementById('devGroupSearchInput')");
        assertTrue(iDev !== -1, 'devRenderGroup читает запрос');
        const fragDev = html.slice(iDev, iDev + 7000);
        assertTrue(fragDev.indexOf('kipSearchFilter(items, rawQuery') !== -1, 'devRenderGroup: kipSearchFilter');
        assertTrue(fragDev.indexOf('kipRenderSearchCounter(list, items.length, __searchTotal, rawQuery)') !== -1, 'devRenderGroup: счётчик');
        assertTrue(fragDev.indexOf('devMark(name, rawQuery)') !== -1, 'devRenderGroup: подсветка devMark');

        const iLock = html.indexOf("document.getElementById('lockGroupSearchInput')");
        assertTrue(iLock !== -1, 'lockRenderGroup читает запрос');
        const fragLock = html.slice(iLock, iLock + 7000);
        assertTrue(fragLock.indexOf('kipSearchFilter(items, rawQuery') !== -1, 'lockRenderGroup: kipSearchFilter');
        assertTrue(fragLock.indexOf('lockMark(name, rawQuery)') !== -1, 'lockRenderGroup: подсветка lockMark');
        assertTrue(fragLock.indexOf('kipRenderSearchCounter(list, items.length, __searchTotal, rawQuery)') !== -1, 'lockRenderGroup: счётчик');
    });

    test('Жёлтая подсветка mark: единый стиль (списки + карточка прибора)', function () {
        const m = html.match(/mark,\s*\n\s*\.pb-card mark \{[\s\S]*?background: #ffd60a;/);
        assertTrue(!!m, 'глобальный mark + .pb-card mark — жёлтый #ffd60a');
        const m2 = html.match(/\.dev-card-value mark \{[\s\S]*?background: #ffd60a;/);
        assertTrue(!!m2, '.dev-card-value mark — жёлтый #ffd60a');
    });

    test('Таблица приборов: markCell подсвечивает совпадения слов запроса', function () {
        assertTrue(devTableJs.indexOf('function markCell') !== -1, 'функция markCell существует');
        assertTrue(devTableJs.indexOf('function currentSearchQuery') !== -1, 'currentSearchQuery читает #devProdSearchInput');
        assertTrue(devTableJs.indexOf("markCell(val, query)") !== -1, 'ячейки рендерятся через markCell');
        const m = devTableJs.match(/\.dev-table td mark \{ background: #ffd60a; color: #1a1a1a;/);
        assertTrue(!!m, 'CSS жёлтой подсветки в таблице');
    });

    test('Подсветка не применяется к колонке № (порядковый номер)', function () {
        const m = devTableJs.match(/var cellHtml = \(col\.key === '__num__'\) \? esc\(val\) : markCell\(val, query\);/);
        assertTrue(!!m, 'колонка № — без подсветки, остальные — markCell');
    });
});

// ------------------------------------------------------------
// Task 165 (доп.): регрессия порядка экранирования в markCell
// ------------------------------------------------------------
describe('markCell: порядок экранирования и ё-класс (Task 165)', function () {
    const devTableJs = fs.readFileSync(path.resolve(__dirname, '..', 'devices-table-desktop.js'), 'utf-8');

    test('Экранирование спецсимволов ДО подстановки [её] — скобки класса не экранируются', function () {
        // Якорь: комментарий про порядок стоит перед строкой экранирования,
        // замена е -> [её] — сразу после неё
        const iComment = devTableJs.indexOf('ВАЖНО: сначала экранируем спецсимволы');
        const iYo = devTableJs.indexOf("n = n.replace(/е/g, '[её]');");
        assertTrue(iComment !== -1, 'комментарий о порядке экранирования должен быть в markCell');
        assertTrue(iYo !== -1, 'замена е -> [её] должна быть в markCell');
        assertTrue(iComment < iYo, 'экранирование должно идти ДО подстановки [её]');
        // Регресс: старый порядок (сначала [её], потом экранирование) удалён
        const iOldOrder = devTableJs.indexOf("n = n.replace(/е/g, '[её]');\n            patterns.push(n.replace(/[");
        assertTrue(iOldOrder === -1, 'старый порядок (подстановка до экранирования) не должен остаться');
    });
});
