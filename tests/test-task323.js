// tests/test-task323.js
// Task 323 — по заявке пользователя: «Перенеси бар итоги учёта в
// правую часть экрана сбоку и текст названия в баре расположи по
// вертикали, при открытии он должен выдвигаться справа налево на
// половину рабочей области, а внизу шахматки графика при этом
// появляется ползунок для перемещения шахматки по горизонтали —
// для удобства контроля по шахматке расчётов итога. С этим учётом
// строки итогов будут располагаться ровно по строкам работников в
// шахматке, и поэтому список работников в панели итога учёта
// можно убрать».
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   HTML: рабочая область #wsWsBody (сетка слева + шторка
//   #wsTotalsDrawer справа); вертикальный бар #wsTotalsBar
//   (класс ws-totals-vbar, текст «Итоги учёта» / «дни и часы»
//   вертикально, шеврон ◂/▸); панель внутри шторки.
//   CSS: вертикальный текст (writing-mode: vertical-rl); шторка
//   50% с отрицательным margin-right (свёрнута — торчит бар) и
//   анимацией; ws-tt-open → margin 0; широкий режим сетки
//   (ws-tt-gridwide): max-content + ВИДИМЫЙ ползунок (12px,
//   webkit + Firefox), шапка по --ws-tt-head-h, ФИО sticky-left;
//   мобильная шторка fixed 86vw/transform, тап-зона 44px;
//   tfoot итоговой строки sticky-bottom; колонка «Сотрудник»
//   скрыта на десктопе в месяце (не в году); скроллбар панели
//   скрыт (синхронный скролл).
//   VM: toggleTotals (панель/aria/шеврон/классы ws-tt-open +
//   ws-tt-gridwide, рендер→var→fit→sync; закрытие — панель
//   сразу hidden, gridwide держится, таймер → _ttCloseCleanup);
//   _ttCloseCleanup (gridwide снят, переменная удалена, fitGrid);
//   _ttIsWide (класс + ≥1024px); _applyTtHeadVar (tabs+thead →
//   --ws-tt-head-h, повторно без изменения); _syncTotalsRows
//   (высоты строк сетки копируются в панель, лишние строки
//   очищаются, scrollTop панели = сетке, эхо-флаг);
//   _attachTotalsSync (слушатели scroll сетки и панели, эхо);
//   _fitGrid: бюджет − tfoot панели (широкий режим), avail по
//   clientHeight (ползунок), syncTT в конце; рендеры: tfoot
//   «Итого», БЕЗ .ws-tt-scroll, ws-tt-year (год), год: активные
//   по порядку сетки + архив ниже; инфо в title.
//   SW: kipia-test-v563.
//
// Запуск: через tests/run-all.js (require './test-task323.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');
const WS_CLIENT = INDEX_SRC.slice(INDEX_SRC.indexOf('var WorkSchedule = {'));

function methodText(src, name) {
    const sig = '\n        ' + name + ': function';
    const i = src.indexOf(sig);
    if (i === -1) return '';
    const rest = src.slice(i + 1);
    const m = rest.match(/\n        \},|\n    \};/);
    const end = m ? m.index + m[0].length : rest.length;
    let text = rest.slice(0, end);
    text = text.replace(/\n\s{4}\};\s*$/, '');
    return text;
}
function methodFn(src, name, document) {
    const text = methodText(src, name).replace(/,\s*$/, '');
    const body = text.replace(new RegExp('^ {8}' + name + ': '), '');
    return new Function('document', 'return (' + body + ')')(document || null);
}
function wsHost(methodNames, extra, document) {
    const host = Object.assign({}, extra);
    methodNames.forEach(function(n) {
        host[n] = methodFn(WS_CLIENT, n, document || null);
    });
    return host;
}
function mockDoc(els) {
    return { getElementById: function(id) { return els[id] || null; } };
}

// ============================================================
// 1. HTML: рабочая область + шторка + вертикальный бар
// ============================================================
describe('Task 323 — HTML: боковая шторка и вертикальный бар', () => {
    test('HTML: #wsWsBody — рабочая область (сетка + шторка)', () => {
        const iBody = INDEX_SRC.indexOf('id="wsWsBody"');
        assertTrue(iBody !== -1, 'контейнер рабочей области есть');
        const iGrid = INDEX_SRC.indexOf('id="wsGridWrap"');
        const iDrawer = INDEX_SRC.indexOf('id="wsTotalsDrawer"');
        assertTrue(iGrid !== -1 && iDrawer !== -1, 'сетка и шторка есть');
        assertTrue(iBody < iGrid && iGrid < iDrawer,
            'сетка слева, шторка справа — внутри рабочей области');
    });

    test('HTML: Task 324 — шторка = панель (бар-ручка УДАЛЁН)', () => {
        const iDrawer = INDEX_SRC.indexOf('id="wsTotalsDrawer"');
        const iPanel = INDEX_SRC.indexOf('id="wsTotalsPanel"');
        assertTrue(iDrawer !== -1, 'шторка есть');
        assertTrue(iDrawer < iPanel,
            'панель — содержимое шторки (ручки-бара больше нет, Task 324)');
        const chunk = INDEX_SRC.slice(iDrawer, iDrawer + 1800);
        assertTrue(chunk.indexOf('class="ws-tt-drawer"') !== -1, 'класс шторки');
        // Task 324: вертикальный бар-ручка удалён — открывает кнопка тулбара
        assertFalse(chunk.indexOf('class="ws-totals-vbar"') !== -1,
            'вертикальный бар удалён из шторки (заявка Task 324)');
        assertFalse(chunk.indexOf('ws-tt-vwrap') !== -1,
            'обёртка вертикальных надписей удалена');
    });

    test('HTML: Task 324 — открытие кнопкой тулбара, закрытие ✕ шапки', () => {
        const i = INDEX_SRC.indexOf('id="wsTotalsBtn"');
        const chunk = INDEX_SRC.slice(i, i + 900);
        assertTrue(chunk.indexOf('WorkSchedule.toggleTotals()') !== -1,
            'кнопка «Итоги учёта» — toggleTotals');
        assertTrue(chunk.indexOf('aria-pressed') !== -1,
            'кнопка — переключатель (aria-pressed)');
        const x = INDEX_SRC.indexOf('id="wsTtClose"');
        const xChunk = INDEX_SRC.slice(x, x + 400);
        assertTrue(xChunk.indexOf('WorkSchedule.toggleTotals()') !== -1,
            '✕ шапки закрывает шторку');
        assertFalse(INDEX_SRC.indexOf('id="wsTotalsChev"') !== -1,
            'шеврон ручки удалён');
        assertFalse(INDEX_SRC.indexOf('◂') !== -1,
            'глиф ручки удалён');
    });
});

// ============================================================
// 2. CSS: вертикальный текст, шторка, ползунок, мобильная
// ============================================================
describe('Task 323 — CSS: шторка, шапка, ползунок', () => {
    test('CSS: Task 324 — шапка шторки (.ws-tt-head) вместо строки вкладок', () => {
        const head = INDEX_SRC.match(/\.ws-tt-head\s*\{[^}]*min-height:\s*28px[^}]*\}/);
        assertTrue(!!head, 'правило шапки шторки (базовая зона 28px)');
        const close = INDEX_SRC.match(/\.ws-tt-close\s*\{[^}]*display:\s*inline-flex[^}]*\}/);
        assertTrue(!!close && close[0].indexOf('cursor: pointer') !== -1,
            'кнопка ✕ — стиль есть (базовое правило)');
        assertFalse(INDEX_SRC.indexOf('ws-totals-bar-cap') !== -1,
            'вертикальные надписи ручки удалены');
        assertFalse(INDEX_SRC.indexOf('writing-mode: vertical-rl') !== -1,
            'вертикальный текст ручки удалён (ручки больше нет)');
    });

    test('CSS: шторка выдвигается справа налево на ПОЛОВИНУ области', () => {
        const d = INDEX_SRC.match(/@media \(min-width: 1024px\)\s*\{[\s\S]*?\.ws-tt-drawer\s*\{[^}]*\}/);
        assertTrue(!!d, 'десктопное правило шторки');
        assertTrue(d[0].indexOf('width: 50%') !== -1, 'ширина — половина рабочей области');
        assertTrue(d[0].indexOf('margin-right: -50%') !== -1,
            'Task 324: свёрнута — ПОЛНОСТЬЮ за правым краем (ручки нет)');
        assertTrue(d[0].indexOf('transition: margin-right 0.28s ease') !== -1,
            'анимация выдвижения справа налево');
        const open = INDEX_SRC.match(/#page-work-schedule\.ws-tt-open \.ws-tt-drawer\s*\{[^}]*\}/);
        assertTrue(!!open && open[0].indexOf('margin-right: 0') !== -1,
            'открыта: margin 0 — шторка на левой половине экрана');
    });

    test('CSS: сетка НЕ скрывается, рабочая область — строка', () => {
        assertFalse(/#page-work-schedule\.ws-tt-open \.ws-grid-wrap\s*\{[^}]*display:\s*none/.test(INDEX_SRC),
            'шахматка остаётся видимой рядом с шторкой');
        const row = INDEX_SRC.match(/\.ws-body\s*\{[^}]*flex-direction:\s*row[^}]*\}/);
        assertTrue(!!row, 'рабочая область — flex-строка (сетка|шторка)');
        assertTrue(row[0].indexOf('overflow: hidden') !== -1,
            'хвост свёрнутой шторки обрезается');
    });

    test('CSS: ПОЛЗУНОК внизу шахматки — видимый, окрашенный', () => {
        const sb = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid-wrap::-webkit-scrollbar\s*\{[^}]*\}/);
        assertTrue(!!sb, 'правило ползунка есть');
        assertTrue(sb[0].indexOf('height: 12px') !== -1, 'высота 12px');
        assertTrue(sb[0].indexOf('display: block') !== -1, 'ползунок ВИДИМ (не display:none)');
        const thumb = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid-wrap::-webkit-scrollbar-thumb\s*\{[^}]*\}/);
        assertTrue(!!thumb && thumb[0].indexOf('background') !== -1, 'бегунок окрашен');
        assertTrue(!!thumb && thumb[0].indexOf('border-radius') !== -1, 'бегунок скруглён');
        const track = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid-wrap::-webkit-scrollbar-track\s*\{[^}]*\}/);
        assertTrue(!!track, 'дорожка стилизована');
        const ff = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid-wrap\s*\{[^}]*\}/);
        assertTrue(!!ff && ff[0].indexOf('scrollbar-width: thin') !== -1,
            'Firefox: ползунок виден (scrollbar-width)');
        assertTrue(!!ff && ff[0].indexOf('overflow-x: auto') !== -1,
            'горизонтальная прокрутка включена');
        const light = INDEX_SRC.match(/\[data-theme="light"\] #page-work-schedule\.ws-tt-gridwide \.ws-grid-wrap::-webkit-scrollbar-thumb\s*\{[^}]*\}/);
        assertTrue(!!light, 'ползунок в светлой теме');
    });

    test('CSS: сетка в широком режиме — природная ширина, ФИО sticky', () => {
        const g = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid\s*\{[^}]*\}/);
        assertTrue(!!g && g[0].indexOf('width: max-content') !== -1,
            'таблица природной ширины (31 день не сжимается в пол-экрана)');
        assertTrue(!!g && g[0].indexOf('table-layout: auto') !== -1,
            'авто-раскладка колонок');
        const day = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid thead th\.ws-day-col\s*\{[^}]*\}/);
        assertTrue(!!day && day[0].indexOf('min-width: 30px') !== -1,
            'минимальная ширина дня (читаемые ячейки)');
        const emp = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid tbody td\.ws-emp-col\s*\{[^}]*\}/);
        assertTrue(!!emp && emp[0].indexOf('position: sticky') !== -1 &&
            emp[0].indexOf('left: 0') !== -1,
            'колонка ФИО прилипла к левому краю (видна при прокрутке)');
        assertTrue(!!emp && emp[0].indexOf('background') !== -1,
            'ФИО — непрозрачный фон (не просвечивает прокрутка)');
        const th = INDEX_SRC.match(/#page-work-schedule\.ws-tt-gridwide \.ws-grid thead th\s*\{[^}]*\}/);
        assertTrue(!!th && th[0].indexOf('var(--ws-tt-head-h, 56px)') !== -1,
            'шапка сетки — высота заголовочной зоны панели (выравнивание строк)');
        assertTrue(!!th && th[0].indexOf('vertical-align: middle') !== -1,
            'даты центрированы в высокой шапке');
    });

    test('CSS: Task 324 — панель: ВИДИМЫЙ нижний ползунок + tfoot у низа', () => {
        const b = INDEX_SRC.match(/\.ws-tt-body\s*\{[^}]*\}/);
        assertTrue(!!b && b[0].indexOf('overflow: auto') !== -1, 'скролл-контейнер');
        // Task 324 (заявка): горизонтальная полоса ВНИЗУ ШТОРКИ — видимая
        assertTrue(b[0].indexOf('scrollbar-width: thin') !== -1,
            'Firefox: тонкие полосы');
        const sb = INDEX_SRC.match(/\.ws-tt-body::-webkit-scrollbar\s*\{[^}]*\}/);
        assertTrue(!!sb && sb[0].indexOf('height: 12px') !== -1,
            'webkit: горизонтальная полоса ВИДИМАЯ (12px)');
        assertTrue(!!sb && sb[0].indexOf('width: 0') !== -1,
            'webkit: вертикальная скрыта (скролл синхронный с сеткой)');
        const thumb = INDEX_SRC.match(/\.ws-tt-body::-webkit-scrollbar-thumb\s*\{[^}]*\}/);
        assertTrue(!!thumb && thumb[0].indexOf('background') !== -1,
            'бегунок шторки окрашен');
        // Task 324 (заявка): оглавления — ОДНОЙ СТРОКОЙ (без переноса)
        const th = INDEX_SRC.match(/\.ws-tt-table th\s*\{[^}]*\}/);
        assertTrue(!!th && th[0].indexOf('white-space: nowrap') !== -1,
            'оглавления одной строкой (заявка)');
        assertFalse(th[0].indexOf('white-space: normal;') !== -1,
            'объявление переноса слов шапки удалено (упоминание в комментарии — история)');
        const tf = INDEX_SRC.match(/\.ws-tt-table tfoot tr\.ws-tt-total td\s*\{[^}]*\}/);
        assertTrue(!!tf && tf[0].indexOf('position: sticky') !== -1 &&
            tf[0].indexOf('bottom: 0') !== -1, 'итоговая строка прилипла к низу панели');
        assertTrue(!!tf && tf[0].indexOf('background') !== -1,
            'итоговая строка непрозрачна (зебра не просвечивает)');
    });

    test('CSS: колонка «Сотрудник» — месяц скрыт на десктопе, год/мобайл видны', () => {
        const m = INDEX_SRC.match(/@media \(min-width: 1024px\)\s*\{[\s\S]*?\.ws-tt-table:not\(\.ws-tt-year\) th\.ws-tt-emp,\s*\.ws-tt-table:not\(\.ws-tt-year\) td\.ws-tt-emp\s*\{[^}]*display:\s*none[^}]*\}/);
        assertTrue(!!m, 'месяц на десктопе: колонка скрыта — строки по строкам сетки');
        // мобайл: колонка остаётся — мобильный блок таблицы итогов
        // (компактные ячейки + max-width колонки, БЕЗ display:none)
        const mob = INDEX_SRC.match(/\.ws-tt-table th, \.ws-tt-table td \{ padding: 5px 8px; \}\s*\.ws-tt-table td\.ws-tt-emp,\s*\.ws-tt-table th\.ws-tt-emp\s*\{[^}]*\}/);
        assertTrue(!!mob, 'мобильные правила таблицы итогов есть');
        assertTrue(mob[0].indexOf('max-width: 150px') !== -1,
            'мобайл: колонка сотрудника осталась (узкая)');
        assertFalse(mob[0].indexOf('display: none') !== -1,
            'мобайл: список сотрудников НЕ скрыт (строки не совпадают с сеткой)');
    });

    test('CSS: мобильная шторка — fixed, 86vw, transform, ✕ 44px (Task 324)', () => {
        const m = INDEX_SRC.match(/\.ws-tt-drawer\s*\{[^}]*position:\s*fixed[^}]*\}/);
        assertTrue(!!m, 'мобильное правило шторки (fixed-оверлей)');
        assertTrue(m[0].indexOf('min(86vw, 560px)') !== -1, 'ширина ~86vw');
        assertTrue(m[0].indexOf('transform: translateX(100%)') !== -1,
            'Task 324: свёрнута — ПОЛНОСТЬЮ за экраном (ручки нет)');
        assertTrue(m[0].indexOf('z-index: 75') !== -1, 'под окнами/барами приложения');
        const w = INDEX_SRC.match(/\.ws-tt-close\s*\{[^}]*width:\s*44px/);
        assertTrue(!!w, 'тап-зона ✕ шапки 44px');
        const open = INDEX_SRC.match(/#page-work-schedule\.ws-tt-open \.ws-tt-drawer\s*\{[^}]*transform:\s*none/);
        assertTrue(!!open, 'мобайл: открыта — без сдвига');
    });
});

// ============================================================
// 3. VM: toggleTotals / _ttCloseCleanup / _ttIsWide
// ============================================================
describe('Task 323 — VM: переключение шторки', () => {
    function makeHost() {
        const calls = { render: 0, fit: 0, sync: 0, cleanup: 0, varSet: 0 };
        // Task 324: переключатель — КНОПКА ТУЛБАРА (aria-pressed)
        const btn = {
            attrs: {},
            setAttribute: function(k, v) { this.attrs[k] = v; }
        };
        const panel = { hidden: true };
        const page = {
            classList: {
                state: {},
                toggle: function(c, o) { this.state[c] = o; },
                add: function() { for (var i = 0; i < arguments.length; i++) this.state[arguments[i]] = true; },
                remove: function() { for (var i = 0; i < arguments.length; i++) this.state[arguments[i]] = false; },
                contains: function(c) { return !!this.state[c]; }
            },
            style: {
                props: {},
                setProperty: function(k, v) { this.props[k] = v; },
                getPropertyValue: function(k) { return this.props[k] || ''; },
                removeProperty: function(k) { delete this.props[k]; }
            }
        };
        const host = wsHost(['toggleTotals', '_ttCloseCleanup', '_ttIsWide'],
            { _totalsOpen: false },
            mockDoc({ wsTotalsBtn: btn, wsTotalsPanel: panel,
                      'page-work-schedule': page }));
        host._renderTotals = function() { calls.render++; };
        host._fitGrid = function() { calls.fit++; };
        host._applyTtHeadVar = function() { calls.varSet++; return false; };
        host._syncTotalsRows = function() { calls.sync++; };
        return { host: host, btn: btn, panel: panel, page: page, calls: calls };
    }

    test('toggleTotals: открыть — панель, aria-pressed, ДВА класса, рендер', () => {
        const t = makeHost();
        t.host.toggleTotals();
        assertEqual(t.panel.hidden, false, 'панель показана');
        assertEqual(t.btn.attrs['aria-pressed'], 'true',
            'кнопка тулбара «нажата» (aria-pressed)');
        assertEqual(t.page.classList.state['ws-tt-open'], true, 'ws-tt-open');
        assertEqual(t.page.classList.state['ws-tt-gridwide'], true,
            'ws-tt-gridwide — сетка в широком режиме (ползунок)');
        assertEqual(t.calls.render, 1, 'итоги отрисованы');
        assertEqual(t.calls.varSet, 1, 'высота заголовочной зоны применена');
        assertEqual(t.calls.fit, 1, 'строки пересчитаны');
        assertEqual(t.calls.sync, 1, 'строки итогов синхронизированы');
    });

    test('toggleTotals: закрыть — панель сразу скрыта, gridwide держится', () => {
        const t = makeHost();
        t.host.toggleTotals();
        t.host.toggleTotals();
        assertEqual(t.panel.hidden, true, 'панель скрыта (шторка уезжает пустой)');
        assertEqual(t.btn.attrs['aria-pressed'], 'false', 'кнопка «отпущена»');
        assertEqual(t.page.classList.state['ws-tt-open'], false, 'шторка свёрнута');
        assertEqual(t.page.classList.state['ws-tt-gridwide'], true,
            'широкий режим держится до конца анимации (320 мс)');
        assertEqual(t.calls.fit >= 2, true, 'fitGrid при закрытии');
    });

    test('_ttCloseCleanup: снимает gridwide, чистит переменную, пересчёт', () => {
        const t = makeHost();
        t.host.toggleTotals();
        t.host.toggleTotals();
        const fits = t.calls.fit;
        t.host._ttCloseCleanup();
        assertEqual(t.page.classList.state['ws-tt-gridwide'], false,
            'широкий режим снят');
        assertEqual(t.page.style.props['--ws-tt-head-h'], undefined,
            'переменная высоты шапки удалена');
        assertEqual(t.calls.fit, fits + 1, 'строки пересчитаны после уборки');
        // повторная уборка безопасна (после таймера)
        t.host._ttCloseCleanup();
        assertEqual(t.calls.fit, fits + 2, 'повторная уборка тоже пересчитывает');
    });

    test('_ttCloseCleanup: при открытой шторке — ничего не делает', () => {
        const t = makeHost();
        t.host.toggleTotals();
        t.host._ttCloseCleanup();
        assertEqual(t.page.classList.state['ws-tt-gridwide'], true,
            'открытая шторка — режим не снят');
        assertEqual(t.calls.fit, 1, 'лишнего пересчёта нет');
    });

    test('_ttIsWide: класс gridwide + десктоп (matchMedia)', () => {
        const t = makeHost();
        assertEqual(t.host._ttIsWide(), false, 'класса нет — false');
        t.page.classList.state['ws-tt-gridwide'] = true;
        // мок window: десктоп — true, мобильный — false
        const savedWindow = global.window;
        global.window = { matchMedia: function(q) { return { matches: true }; } };
        assertEqual(t.host._ttIsWide(), true, 'десктоп + класс — true');
        global.window = { matchMedia: function(q) { return { matches: false }; } };
        assertEqual(t.host._ttIsWide(), false, 'мобильный вид — false');
        global.window = {};   // без matchMedia
        assertEqual(t.host._ttIsWide(), false, 'без matchMedia — false');
        if (savedWindow === undefined) delete global.window;
        else global.window = savedWindow;
    });
});

// ============================================================
// 4. VM: _applyTtHeadVar — высота заголовочной зоны
// ============================================================
describe('Task 323 — VM: _applyTtHeadVar', () => {
    function makeHost(tabsH, theadH, curVar) {
        const page = {
            style: {
                props: curVar ? { '--ws-tt-head-h': curVar } : {},
                setProperty: function(k, v) { this.props[k] = v; },
                getPropertyValue: function(k) { return this.props[k] || ''; },
                removeProperty: function(k) { delete this.props[k]; }
            }
        };
        const panel = {
            getBoundingClientRect: function() { return { height: 300 }; },
            querySelector: function(sel) {
                if (sel === '.ws-tt-head') {
                    return { getBoundingClientRect: function() { return { height: tabsH }; } };
                }
                if (sel === '.ws-tt-table thead') {
                    return { getBoundingClientRect: function() { return { height: theadH }; } };
                }
                return null;
            }
        };
        const host = wsHost(['_applyTtHeadVar'], { _totalsOpen: true },
            mockDoc({ 'page-work-schedule': page, wsTotalsPanel: panel }));
        return { host: host, page: page };
    }

    test('зона = вкладки + шапка таблицы → переменная целым числом', () => {
        const t = makeHost(26.4, 31.2, '');
        const changed = t.host._applyTtHeadVar();
        assertEqual(changed, true, 'первое применение — изменено');
        assertEqual(t.page.style.props['--ws-tt-head-h'], '58px',
            'ceil(26,4 + 31,2) = 58px');
    });

    test('та же высота — НЕ изменилось (без лишнего пересчёта)', () => {
        const t = makeHost(26, 32, '58px');
        assertEqual(t.host._applyTtHeadVar(), false, 'высота та же');
    });

    test('закрытая шторка / нет таблицы — без изменения', () => {
        const t = makeHost(26, 32, '');
        t.host._totalsOpen = false;
        assertEqual(t.host._applyTtHeadVar(), false, 'закрыто — нет');
        const panel = { querySelector: function() { return null; } };
        const host2 = wsHost(['_applyTtHeadVar'], { _totalsOpen: true },
            mockDoc({ wsTotalsPanel: panel, 'page-work-schedule': t.page }));
        assertEqual(host2._applyTtHeadVar(), false, 'нет шапки — нет');
    });
});

// ============================================================
// 5. VM: _syncTotalsRows — строки итогов по строкам сетки
// ============================================================
describe('Task 323 — VM: _syncTotalsRows', () => {
    function makeDom(gHeights, tCount) {
        const gRows = gHeights.map(function(h) {
            return { getBoundingClientRect: function() { return { height: h }; }, style: {} };
        });
        const tRows = [];
        for (var i = 0; i < tCount; i++) tRows.push({ style: { height: 'не трогать ' + i } });
        const gridTable = { querySelectorAll: function(sel) { return sel === 'tbody tr' ? gRows : []; } };
        const ttTable = { querySelectorAll: function(sel) { return sel === 'tbody tr' ? tRows : []; } };
        const gridWrap = { scrollTop: 33, querySelector: function() { return gridTable; } };
        const body = { scrollTop: 0, querySelector: function() { return ttTable; } };
        return { gridWrap: gridWrap, body: body, gRows: gRows, tRows: tRows };
    }

    test('высоты строк сетки копируются в строки итогов (ceil)', () => {
        const d = makeDom([40.2, 39.8, 41], 3);
        const host = wsHost(['_syncTotalsRows'], { _totalsOpen: true, _ttEchoP: false },
            mockDoc({ wsGridWrap: d.gridWrap, wsTtBody: d.body }));
        host._ttEchoG = false;
        host._syncTotalsRows();
        assertEqual(d.tRows[0].style.height, '41px', 'ceil(40,2) = 41');
        assertEqual(d.tRows[1].style.height, '40px', 'ceil(39,8) = 40');
        assertEqual(d.tRows[2].style.height, '41px', '41 без изменения');
        assertEqual(d.body.scrollTop, 33, 'скролл панели = скроллу сетки');
    });

    test('лишние строки панели (год: архив) — высота сброшена', () => {
        const d = makeDom([40], 3);
        const host = wsHost(['_syncTotalsRows'], { _totalsOpen: true, _ttEchoP: false },
            mockDoc({ wsGridWrap: d.gridWrap, wsTtBody: d.body }));
        host._ttEchoG = false;
        host._syncTotalsRows();
        assertEqual(d.tRows[0].style.height, '40px', 'первая строка — по сетке');
        assertEqual(d.tRows[1].style.height, '', 'вторая (без пары) — природная');
        assertEqual(d.tRows[2].style.height, '', 'третья (без пары) — природная');
    });

    test('нулевая высота (скрытая страница) — высота не ставится', () => {
        const d = makeDom([0], 1);
        const host = wsHost(['_syncTotalsRows'], { _totalsOpen: true, _ttEchoP: false },
            mockDoc({ wsGridWrap: d.gridWrap, wsTtBody: d.body }));
        host._ttEchoG = false;
        host._syncTotalsRows();
        assertEqual(d.tRows[0].style.height, '', '0px — высота очищена');
    });

    test('эхо-флаг панели — сетку не дёргаем (панель ведёт)', () => {
        const d = makeDom([40], 1);
        const host = wsHost(['_syncTotalsRows'], { _totalsOpen: true, _ttEchoP: true },
            mockDoc({ wsGridWrap: d.gridWrap, wsTtBody: d.body }));
        host._syncTotalsRows();
        assertEqual(d.tRows[0].style.height, '40px', 'высоты всё равно скопированы');
        assertEqual(d.body.scrollTop, 0, 'скролл НЕ навязан (эхо)');
    });

    test('закрытая шторка / нет таблиц — выход без ошибок', () => {
        const d = makeDom([40], 1);
        const host = wsHost(['_syncTotalsRows'], { _totalsOpen: false },
            mockDoc({ wsGridWrap: d.gridWrap, wsTtBody: d.body }));
        host._syncTotalsRows();
        assertEqual(d.tRows[0].style.height, 'не трогать 0', 'ничего не менялось');
        const host2 = wsHost(['_syncTotalsRows'], { _totalsOpen: true },
            mockDoc({ wsGridWrap: null, wsTtBody: null }));
        host2._syncTotalsRows();   // не падает
    });
});

// ============================================================
// 6. VM: _attachTotalsSync — синхронизация скролла
// ============================================================
describe('Task 323 — VM: синхронизация скролла сетка ⇄ панель', () => {
    function makeScrollPair() {
        const events = { grid: [], panel: [] };
        const gridWrap = {
            scrollTop: 0,
            addEventListener: function(type, fn) { events.grid.push(fn); }
        };
        const body = {
            scrollTop: 0,
            addEventListener: function(type, fn) { events.panel.push(fn); }
        };
        const host = wsHost(['_attachTotalsSync'], { _totalsOpen: true },
            mockDoc({ wsGridWrap: gridWrap, wsTtBody: body }));
        host._attachTotalsSync();
        host._attachTotalsSync();   // второй вызов — один набор слушателей
        return { host: host, gridWrap: gridWrap, body: body, events: events };
    }

    test('слушатели на оба контейнера, ровно по одному', () => {
        const t = makeScrollPair();
        assertEqual(t.events.grid.length, 1, 'один слушатель сетки');
        assertEqual(t.events.panel.length, 1, 'один слушатель панели');
    });

    test('скролл сетки тянет панель (эхо глушится)', () => {
        const t = makeScrollPair();
        t.gridWrap.scrollTop = 50;
        t.events.grid[0]();
        assertEqual(t.body.scrollTop, 50, 'панель подвинулась к сетке');
        // событие панели (эхо нашего присвоения) НЕ тянет сетку
        t.events.panel[0]();
        assertEqual(t.gridWrap.scrollTop, 50, 'сетка не изменилась (эхо)');
    });

    test('скролл панели тянет сетку (обратная синхронизация)', () => {
        const t = makeScrollPair();
        t.body.scrollTop = 77;
        t.events.panel[0]();
        assertEqual(t.gridWrap.scrollTop, 77, 'сетка подвинулась к панели');
        t.events.grid[0]();
        assertEqual(t.body.scrollTop, 77, 'панель не изменилась (эхо)');
    });

    test('закрытая шторка — скроллы не синхронизируются', () => {
        const t = makeScrollPair();
        t.host._totalsOpen = false;
        t.gridWrap.scrollTop = 90;
        t.events.grid[0]();
        assertEqual(t.body.scrollTop, 0, 'панель не тронута');
    });
});

// ============================================================
// 7. VM: _fitGrid — бюджет с итоговой строкой и ползунком
// ============================================================
describe('Task 323 — VM: _fitGrid учитывает шторку', () => {
    test('JS: бюджет = область − шапка − полоса − итоговая строка', () => {
        const txt = methodText(WS_CLIENT, '_fitGrid');
        assertTrue(txt.indexOf('var budget = avail - headH - footH - ttFootH;') !== -1,
            'в бюджете вычитается итоговая строка панели');
        assertTrue(txt.indexOf("querySelector('#wsTtBody .ws-tt-total')") !== -1,
            'высота берётся из реального tfoot панели');
    });

    test('JS: avail — по МЕНЬШЕМУ из rect и clientHeight (ползунок)', () => {
        const txt = methodText(WS_CLIENT, '_fitGrid');
        assertTrue(txt.indexOf('var chH = wrap.clientHeight;') !== -1,
            'высота контента (без ползунка) читается');
        assertTrue(txt.indexOf('if (chH && chH < avail) avail = chH;') !== -1,
            'clientHeight (минус ползунок) ограничивает бюджет');
    });

    test('JS: подгонка завершается синхронизацией строк итогов', () => {
        const txt = methodText(WS_CLIENT, '_fitGrid');
        assertTrue(txt.indexOf('syncTT();') !== -1, 'syncTT вызывается');
        assertTrue(txt.indexOf('_syncTotalsRows') !== -1, 'строки копируются');
        assertTrue(txt.indexOf('_ttIsWide') !== -1, 'только в широком режиме');
    });
});

// ============================================================
// 8. VM: рендеры — tfoot, без обёртки, класс года, порядок строк
// ============================================================
describe('Task 323 — VM: структура таблиц итогов', () => {
    const RENDER_STUBS = {
        _applyTtHeadVar: function() { return false; },
        _fitGrid: function() {},
        _syncTotalsRows: function() {}
    };

    function makeMonthHost() {
        // Task 324: инфо-строка удалена — ⚠ шапки (пустая на месяце)
        const els = { wsTtBody: { innerHTML: '' },
                      wsTtWarn: { textContent: '', hidden: true, attrs: {},
                                  setAttribute: function(k, v) { this.attrs[k] = v; } } };
        const host = wsHost(['_codeHours', '_totalsZero', '_totalsAgg', '_statusMeta',
                             '_empTypeMap', '_overHours', '_totalsEffectiveEntries',
                             '_fmtTotalsNum', '_esc', '_setTtWarn', '_renderTotalsMonth'],
            Object.assign({
                _year: 2026, _month: 9,
                _EMPLOYEES: [
                    { 'таб_номер': '0871', 'ФИО': 'Иванов И.И.', 'тип': 'сменный' }
                ],
                _ENTRIES: [
                    { 'дата': '2026-09-01', 'таб_номер': '0871', 'статус': 'Д' }
                ],
                _PENDING: {},
                _STATUS_CODES: [ { code: 'Д', name: 'День (12-час)' } ]
            }, RENDER_STUBS), mockDoc(els));
        return { host: host, els: els };
    }

    test('месяц: БЕЗ обёртки .ws-tt-scroll, таблица прямо в #wsTtBody', () => {
        const t = makeMonthHost();
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('<table class="ws-tt-table">') !== -1, 'таблица без обёртки');
        assertFalse(h.indexOf('ws-tt-scroll') !== -1, 'обёртка .ws-tt-scroll удалена');
    });

    test('месяц: итоговая строка — в tfoot (прилипшая к низу)', () => {
        const t = makeMonthHost();
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('</tbody><tfoot><tr class="ws-tt-total">') !== -1,
            'tfoot после tbody');
        assertTrue(h.indexOf('Итого по подразделению') !== -1, 'подпись итога');
        assertTrue(h.indexOf('</tr></tfoot></table>') !== -1, 'закрытие tfoot');
    });

    test('месяц: колонка «Сотрудник» рендерится (скрывает CSS на десктопе)', () => {
        const t = makeMonthHost();
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('<th class="ws-tt-emp">Сотрудник</th>') !== -1,
            'заголовок колонки в разметке (мобайл/год)');
        assertTrue(h.indexOf('Иванов И.И.') !== -1, 'ФИО в строке (мобайл)');
    });

    test('месяц: Task 324 — инфо-строка удалена, ⚠ пуст', () => {
        const t = makeMonthHost();
        t.host._renderTotalsMonth();
        assertEqual(t.els.wsTtWarn.textContent, '', '⚠ пуст (инфо удалена по заявке)');
        assertEqual(t.els.wsTtWarn.hidden, true, '⚠ скрыта');
        const txt = methodText(WS_CLIENT, '_renderTotalsMonth');
        assertTrue(txt.indexOf("_setTtWarn('')") !== -1,
            'рендер месяца гасит ⚠ (аварий на месяце нет)');
        assertFalse(txt.indexOf('wsTtInfo') !== -1,
            'инфо-строка больше не пишется');
    });

    test('год: таблица с классом ws-tt-year (колонка сотрудника видна)', () => {
        const els = { wsTtBody: { innerHTML: '' },
                      wsTtWarn: { textContent: '', hidden: true, attrs: {},
                                  setAttribute: function(k, v) { this.attrs[k] = v; } } };
        const md = {
            year: 2026, ts: Date.now(), failed: 0,
            months: { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [],
                      9: [ { 'дата': '2026-09-01', 'таб_номер': '0871', 'статус': 'Д' } ],
                      10: [], 11: [], 12: [] },
            employees: [ { 'таб_номер': '0871', 'ФИО': 'Иванов И.И.' } ]
        };
        const host = wsHost(['_codeHours', '_totalsZero', '_totalsAgg', '_statusMeta',
                             '_empTypeMap', '_overHours', '_fmtTotalsNum', '_esc',
                             '_sortEmployees', '_setTtWarn', '_renderTotalsYearTable'],
            Object.assign({ _year: 2026, _month: 9,
                _EMPLOYEES: [ { 'таб_номер': '0871', 'ФИО': 'Иванов И.И.' } ],
                _STATUS_CODES: [ { code: 'Д', name: 'День (12-час)' } ],
                _YEAR_DATA: md }, RENDER_STUBS), mockDoc(els));
        host._renderTotalsYearTable();
        const h = els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('<table class="ws-tt-table ws-tt-year">') !== -1,
            'класс ws-tt-year — колонка сотрудника на десктопе видна');
        assertTrue(h.indexOf('</tbody><tfoot><tr class="ws-tt-total">') !== -1,
            'год: итоговая строка в tfoot');
    });

    test('год: АКТИВНЫЕ по порядку сетки сверху, архив — ниже (Task 323)', () => {
        const els = { wsTtBody: { innerHTML: '' },
                      wsTtWarn: { textContent: '', hidden: true, attrs: {},
                                  setAttribute: function(k, v) { this.attrs[k] = v; } } };
        const md = {
            year: 2026, ts: Date.now(), failed: 0,
            months: { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [],
                      9: [], 10: [], 11: [], 12: [] },
            employees: [
                { 'таб_номер': '099', 'ФИО': 'Сидоров С.С.', 'в_архиве': 1 },
                { 'таб_номер': '023', 'ФИО': 'Петров П.П.' }
            ]
        };
        const host = wsHost(['_codeHours', '_totalsZero', '_totalsAgg', '_statusMeta',
                             '_empTypeMap', '_overHours', '_fmtTotalsNum', '_esc',
                             '_sortEmployees', '_setTtWarn', '_renderTotalsYearTable'],
            Object.assign({ _year: 2026, _month: 9,
                // сетка: Петров (023) — первая строка
                _EMPLOYEES: [ { 'таб_номер': '023', 'ФИО': 'Петров П.П.' } ],
                _STATUS_CODES: [], _YEAR_DATA: md }, RENDER_STUBS), mockDoc(els));
        host._renderTotalsYearTable();
        const h = els.wsTtBody.innerHTML;
        const iP = h.indexOf('Петров П.П.');
        const iS = h.indexOf('Сидоров С.С.');
        assertTrue(iP !== -1 && iS !== -1, 'оба в таблице');
        assertTrue(iP < iS, 'активный (по строке сетки) — ВЫШЕ архивного');
    });
});

// ============================================================
// 9. Инициализация и интеграция
// ============================================================
describe('Task 323 — интеграция', () => {
    test('JS: init вешает синхронизацию скролла', () => {
        const txt = methodText(WS_CLIENT, 'init');
        assertTrue(txt.indexOf('this._attachTotalsSync();') !== -1,
            'слушатели скролла вешаются при старте');
    });

    test('JS: рендер сетки ведёт к пересчёту и синхронизации (fitGrid)', () => {
        const rg = methodText(WS_CLIENT, '_renderGrid');
        assertTrue(rg.indexOf('this._fitGrid();') !== -1, 'сетка подгоняется');
        assertTrue(rg.indexOf('this._renderTotalsIfOpen();') !== -1,
            'итоги перерисовываются вместе с сеткой');
    });

    test('JS: оба рендера итогов завершаются var+fit+sync', () => {
        const m = methodText(WS_CLIENT, '_renderTotalsMonth');
        assertTrue(m.indexOf('if (this._applyTtHeadVar()) this._fitGrid();') !== -1,
            'месяц: изменилась высота зоны — пересчёт');
        assertTrue(m.indexOf('this._syncTotalsRows();') !== -1, 'месяц: синхронизация');
        const y = methodText(WS_CLIENT, '_renderTotalsYearTable');
        assertTrue(y.indexOf('if (this._applyTtHeadVar()) this._fitGrid();') !== -1,
            'год: пересчёт при изменении зоны');
        assertTrue(y.indexOf('this._syncTotalsRows();') !== -1, 'год: синхронизация');
    });

    test('JS: бочка с таймером чистится при повторном открытии', () => {
        const txt = methodText(WS_CLIENT, 'toggleTotals');
        assertTrue(txt.indexOf('clearTimeout(this._ttWideTimer)') !== -1,
            'таймер уборки сбрасывается при новом открытии');
    });
});

// ============================================================
// 10. SW: версия кэша
// ============================================================
describe('Task 323 — SW: версия кэша', () => {
    test('SW: кэш поднят до kipia-test-v563 (Task 323)', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v563'") !== -1,
            'CACHE_VERSION = kipia-test-v563');
        assertFalse(SW_SRC.indexOf('kipia-test-v564') !== -1,
            'v563 не существует (один инкремент на Task 323)');
    });
});
