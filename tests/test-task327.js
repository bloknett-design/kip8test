// tests/test-task327.js
// Task 327 — ИТОГИ УЧЁТА: заявка пользователя:
//   «В шторке итогов учёта убери строку общего количества, в таблице
//    оставь основные столбцы в такой последовательности Явки, Часы,
//    Переработка, и дополнительные скрытые столбцы Отгул, Больничный,
//    Отпуск, Уч. отпуск, Прогул, День, Ночь, Прочие, столбец Всего
//    убери. Столбцы в шторке итогов выравни по ширине, текст
//    заголовков сделай в две строки для компактности, при
//    необходимости. Внизу шторки сделай такой же бордюрчик как в
//    шахматке табеля. Кнопки "Месяц" и "Год" должны появляться при
//    открытии шторки итогов учёта.»
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   HTML: вкладки «Месяц»/«Год» скрыты (hidden) до открытия шторки;
//     кнопка «Ещё» (#wsTtMore) в шапке шторки — скрытые доп. столбцы
//     месяца; БОРДЮРЧИК .ws-tt-foot внизу панели (после #wsTtBody).
//   CSS: .ws-tt-tab[hidden]; .ws-tt-more (стили/активная/[hidden]);
//     .ws-tt-foot = .ws-grid-foot (5px стальной bevel, обе темы);
//     месячная таблица — table-layout fixed (равные столбцы),
//     год — прежняя авто-раскладка; заголовки th — normal+
//     break-word (2 строки при необходимости), год — nowrap;
//     .ws-tt-emp месяца — width 42% + эллипсис; tfoot-правил
//     .ws-tt-total больше нет.
//   JS/VM: _totalsExtra состояние; toggleTotalsExtra;
//     _updateTtTabsVisible (вкладки при открытии); _updateTtMoreBtn
//     (только месяц, «Ещё»/«Меньше»); _updateTtHead учитывает «Ещё»;
//     _renderTotalsMonth — порядок основных столбцов (Явки→Часы→
//     Переработка), доп. скрыты/показаны по _totalsExtra (порядок
//     заявки: Отгул, Больничный, Отпуск, Уч. отпуск, Прогул, День,
//     Ночь, Прочие), НЕТ tfoot/«Итого»/«Всего», min-width при «Ещё»;
//     _renderTotalsYearTable — НЕТ tfoot; _fitGrid — бюджет без
//     резерва итоговой строки; toggleTotals/setTotalsTab зовут новые
//     методы.
//   SW: kipia-test-v566.
//
// Запуск: через tests/run-all.js (require './test-task327.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
const WS_CLIENT = INDEX_SRC;

function methodText(src, name) {
    const sig = '\n        ' + name + ': function';
    const i = src.indexOf(sig);
    if (i === -1) return '';
    const rest = src.slice(i + 1);
    const m = rest.match(/\n        [a-zA-Z_]+: function|\n    \};/);
    const end = m ? m.index : rest.length;
    return rest.slice(0, end);
}

function methodFn(src, name) {
    const txt = methodText(src, name);
    assertTrue(txt.length > 0, 'метод найден: ' + name);
    const obj = new Function('return ({' + txt + '\n});')();
    return obj[name];
}

function mockDoc(els) {
    return { getElementById: function(id) { return els[id] || null; } };
}

// ============================================================
// 1. HTML: вкладки при открытии, «Ещё», бордюрчик
// ============================================================
describe('Task 327 — HTML: шторка и тулбар', () => {

    const ws = INDEX_SRC.slice(INDEX_SRC.indexOf('id="page-work-schedule"'),
                                INDEX_SRC.indexOf('id="wsGridWrap"'));

    test('HTML: вкладки «Месяц»/«Год» СКРЫТЫ до открытия шторки (заявка)', () => {
        const iM = ws.indexOf('id="wsTtTabMonth"');
        const iY = ws.indexOf('id="wsTtTabYear"');
        assertTrue(iM !== -1 && iY !== -1, 'вкладки есть в ряду 2');
        const btnM = ws.slice(iM, ws.indexOf('</button>', iM));
        const btnY = ws.slice(iY, ws.indexOf('</button>', iY));
        assertTrue(/\shidden\b/.test(btnM), '«Месяц» скрыта по умолчанию');
        assertTrue(/\shidden\b/.test(btnY), '«Год» скрыта по умолчанию');
        // Task 327: JS показывает/прячет вкладки вместе со шторкой
        assertTrue(INDEX_SRC.indexOf('_updateTtTabsVisible: function') !== -1,
            'метод _updateTtTabsVisible (видимость вкладок = шторка)');
    });

    test('HTML: кнопка «Ещё» в шапке шторки (#wsTtMore)', () => {
        const iPanel = INDEX_SRC.indexOf('id="wsTotalsPanel"');
        const chunk = INDEX_SRC.slice(iPanel, iPanel + 2600);
        const iMore = chunk.indexOf('id="wsTtMore"');
        assertTrue(iMore !== -1, 'кнопка «Ещё» есть');
        assertTrue(chunk.indexOf('toggleTotalsExtra()') !== -1,
            'onclick → WorkSchedule.toggleTotalsExtra()');
        const btn = chunk.slice(iMore, chunk.indexOf('</button>', iMore));
        assertTrue(/\shidden\b/.test(btn), 'скрыта по умолчанию (только месяц + открытая шторка)');
        assertTrue(btn.indexOf('Ещё') !== -1, 'текст «Ещё»');
    });

    test('HTML: БОРДЮРЧИК .ws-tt-foot внизу шторки (заявка)', () => {
        const iBody = INDEX_SRC.indexOf('id="wsTtBody"');
        const iFoot = INDEX_SRC.indexOf('class="ws-tt-foot"');
        assertTrue(iFoot !== -1, 'полоса .ws-tt-foot есть');
        assertTrue(iBody !== -1 && iBody < iFoot,
            'полоса ПОСЛЕ тела таблиц (закрывает шторку снизу)');
        // строка общего количества не рендерится (заявка): в КОДЕ
        // рендера нет tfoot/подписи Итого/столбца Всего (упоминания
        // в комментариях — история заявки, не разметка)
        const m = methodText(WS_CLIENT, '_renderTotalsMonth');
        assertFalse(m.indexOf("'</tbody><tfoot>") !== -1, 'месяц: tfoot не рендерится');
        assertFalse(m.indexOf('Итого по подразделению') !== -1, 'месяц: подписи Итого нет');
        assertFalse(m.indexOf("name: 'Всего'") !== -1, 'месяц: столбца «Всего» нет');
    });
});

// ============================================================
// 2. CSS: полоса, «Ещё», равные столбцы, заголовки в 2 строки
// ============================================================
describe('Task 327 — CSS: бордюрчик, «Ещё», равные столбцы', () => {

    test('CSS: вкладки — [hidden] гасит кнопку', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-tt-tab[hidden] { display: none; }') !== -1,
            'правило .ws-tt-tab[hidden]');
    });

    test('CSS: .ws-tt-more — кнопка «Ещё» + активная + [hidden]', () => {
        const m = INDEX_SRC.match(/\.ws-tt-more\s*\{[^}]*\}/);
        assertTrue(!!m, 'стиль кнопки');
        assertTrue(!!m && m[0].indexOf('cursor: pointer') !== -1, 'кликабельна');
        assertTrue(/\.ws-tt-more\.on\s*\{[^}]*rgba\(74,\s*143,\s*199/.test(INDEX_SRC),
            'активное состояние (доп. столбцы включены)');
        assertTrue(INDEX_SRC.indexOf('.ws-tt-more[hidden] { display: none; }') !== -1,
            'скрытие [hidden]');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ws-tt-more') !== -1,
            'светлая тема');
    });

    test('CSS: БОРДЮРЧИК = .ws-grid-foot шахматки (5px стальной bevel)', () => {
        const m = INDEX_SRC.match(/\.ws-tt-foot\s*\{[^}]*\}/);
        assertTrue(!!m, 'правило .ws-tt-foot');
        assertTrue(!!m && m[0].indexOf('height: 5px') !== -1, 'высота 5px (как Task 258)');
        assertTrue(!!m && m[0].indexOf('#35648f') !== -1, 'стальной фон (тот же, что сетка)');
        assertTrue(!!m && m[0].indexOf('border-top: 1px solid #85b7dc') !== -1,
            'блик сверху (bevel)');
        const l = INDEX_SRC.match(/\[data-theme="light"\] \.ws-tt-foot\s*\{[^}]*\}/);
        assertTrue(!!l && l[0].indexOf('#b3c2ce') !== -1, 'светлая тема полосы');
    });

    test('CSS: месячная таблица — РАВНЫЕ столбцы (заявка)', () => {
        assertTrue(/\.ws-tt-table:not\(\.ws-tt-year\)\s*\{[^}]*table-layout:\s*fixed/.test(INDEX_SRC),
            'table-layout: fixed — столбцы делят ширину поровну');
        // годовая — прежняя авто-раскладка (правило не задаёт fixed)
        const y = INDEX_SRC.match(/\.ws-tt-table\.ws-tt-year\s*\{[^}]*\}/);
        assertFalse(!!y && y[0].indexOf('table-layout') !== -1,
            'год: авто-раскладка сохранена');
        // месяц: колонка ФИО — доля, данные — равные остатки
        const mm = INDEX_SRC.match(/\.ws-tt-table:not\(\.ws-tt-year\) th\.ws-tt-emp,\n\s*\.ws-tt-table:not\(\.ws-tt-year\) td\.ws-tt-emp\s*\{[^}]*\}/);
        assertTrue(!!mm && mm[0].indexOf('width: 42%') !== -1,
            'месяц: ФИО 42% (мобайл), данные — равные доли остатка');
    });

    test('CSS: заголовки — в ДВЕ строки при необходимости (заявка)', () => {
        const th = INDEX_SRC.match(/\.ws-tt-table th\s*\{[^}]*\}/);
        assertTrue(!!th && th[0].indexOf('white-space: normal') !== -1,
            'перенос включён');
        assertTrue(!!th && th[0].indexOf('overflow-wrap: break-word') !== -1,
            'разрыв длинных слов');
        assertTrue(!!th && th[0].indexOf('hyphens: auto') !== -1, 'авто-переносы');
        assertTrue(!!th && th[0].indexOf('text-align: center') !== -1,
            'по центру равного столбца');
        const thY = INDEX_SRC.match(/\.ws-tt-table\.ws-tt-year th\s*\{[^}]*\}/);
        assertTrue(!!thY && thY[0].indexOf('white-space: nowrap') !== -1,
            'год: заголовки-месяцы одной строкой');
    });

    test('CSS: итоговая строка — стили УДАЛЕНЫ (заявка)', () => {
        assertFalse(/\.ws-tt-total\s*(td|tr)?\s*\{/.test(INDEX_SRC),
            'CSS-правила .ws-tt-total удалены');
        assertFalse(/tfoot tr\.ws-tt-total/.test(INDEX_SRC),
            'прилипающий tfoot удалён');
    });
});

// ============================================================
// 3. VM: _totalsExtra, toggleTotalsExtra, вкладки при открытии
// ============================================================
describe('Task 327 — VM: состояние и кнопки', () => {

    test('VM: поле _totalsExtra в состоянии', () => {
        assertTrue(INDEX_SRC.indexOf('_totalsExtra: false') !== -1,
            'начальное состояние — доп. столбцы скрыты');
    });

    test('VM: _updateTtTabsVisible — вкладки = шторка (заявка)', () => {
        const fn = methodFn(WS_CLIENT, '_updateTtTabsVisible');
        const mBtn = { hidden: false };
        const yBtn = { hidden: false };
        global.document = mockDoc({ wsTtTabMonth: mBtn, wsTtTabYear: yBtn });
        const host = { _totalsOpen: false };
        try {
        fn.call(host);
        assertEqual(mBtn.hidden, true, 'закрыта — вкладки скрыты');
        assertEqual(yBtn.hidden, true, 'закрыта — «Год» скрыта');
        host._totalsOpen = true;
        fn.call(host);
        assertEqual(mBtn.hidden, false, 'открыта — вкладки ПОЯВИЛИСЬ');
        assertEqual(yBtn.hidden, false, 'открыта — «Год» появилась');
        } finally { delete global.document; }
    });

    test('VM: _updateTtMoreBtn — только месяц, «Ещё»/«Меньше»', () => {
        const fn = methodFn(WS_CLIENT, '_updateTtMoreBtn');
        const b = { hidden: false, textContent: '', classList: {
            state: {}, toggle: function(c, o) { this.state[c] = o; } } };
        global.document = mockDoc({ wsTtMore: b });
        try {
            const host = { _totalsOpen: true, _totalsTab: 'year', _totalsExtra: true };
            fn.call(host);
            assertEqual(b.hidden, true, 'год: кнопки «Ещё» нет');
            host._totalsTab = 'month';
            host._totalsExtra = false;
            fn.call(host);
            assertEqual(b.hidden, false, 'месяц: кнопка видна');
            assertEqual(b.textContent, 'Ещё', 'текст «Ещё» (доп. скрыты)');
            assertEqual(b.classList.state['on'], false, 'не активна');
            host._totalsExtra = true;
            fn.call(host);
            assertEqual(b.textContent, 'Меньше', 'текст «Меньше» (доп. показаны)');
            assertEqual(b.classList.state['on'], true, 'активна');
            host._totalsOpen = false;
            fn.call(host);
            assertEqual(b.hidden, true, 'закрытая шторка: кнопка скрыта');
        } finally {
            delete global.document;
        }
    });

    test('VM: toggleTotalsExtra — переключение + перерисовка месяца', () => {
        const fn = methodFn(WS_CLIENT, 'toggleTotalsExtra');
        const calls = { render: 0, more: 0 };
        const host = {
            _totalsExtra: false,
            _updateTtMoreBtn: function() { calls.more++; },
            _renderTotalsMonth: function() { calls.render++; }
        };
        fn.call(host);
        assertEqual(host._totalsExtra, true, 'включены');
        assertEqual(calls.more, 1, 'кнопка обновлена');
        assertEqual(calls.render, 1, 'таблица перерисована');
        fn.call(host);
        assertEqual(host._totalsExtra, false, 'выключены');
    });

    test('VM: _updateTtHead — «Ещё» удерживает шапку (не empty)', () => {
        const fn = methodFn(WS_CLIENT, '_updateTtHead');
        const head = { classList: { state: {}, toggle: function(c, o) { this.state[c] = o; } } };
        const panel = { querySelector: function() { return head; } };
        global.document = mockDoc({
            wsTotalsPanel: panel,
            wsTtWarn: { hidden: true },
            wsTtRefresh: { hidden: true },
            wsTtMore: { hidden: false }
        });
        try {
            fn.call({});
            assertEqual(head.classList.state['ws-tt-head-empty'], false,
                'шапка не сжимается — «Ещё» видна');
            // «Ещё» скрыта (год), ⚠/Обновить тоже — шапка пустая
            global.document = mockDoc({
                wsTotalsPanel: panel,
                wsTtWarn: { hidden: true },
                wsTtRefresh: { hidden: true },
                wsTtMore: { hidden: true }
            });
            fn.call({});
            assertEqual(head.classList.state['ws-tt-head-empty'], true,
                '«Ещё» скрыта — шапка сжата (год без ⚠/Обновить)');
        } finally {
            delete global.document;
        }
    });

    test('JS: toggleTotals зовёт видимость вкладок и «Ещё»', () => {
        const txt = methodText(WS_CLIENT, 'toggleTotals');
        assertTrue(txt.indexOf('this._updateTtTabsVisible();') !== -1,
            'вкладки появляются/убираются со шторкой');
        assertTrue(txt.indexOf('this._updateTtMoreBtn();') !== -1,
            'кнопка «Ещё» синхронна шторке');
    });

    test('JS: setTotalsTab обновляет «Ещё» (год — скрыта)', () => {
        const txt = methodText(WS_CLIENT, 'setTotalsTab');
        assertTrue(txt.indexOf('this._updateTtMoreBtn();') !== -1,
            'setTotalsTab → _updateTtMoreBtn');
    });
});

// ============================================================
// 4. VM: _renderTotalsMonth — столбцы по заявке
// ============================================================
describe('Task 327 — VM: таблица месяца', () => {

    const MONTH_METHODS = ['_codeHours', '_totalsZero', '_totalsAgg', '_statusMeta',
                           '_empTypeMap', '_overHours', '_totalsEffectiveEntries',
                           '_fmtTotalsNum', '_esc', '_setTtWarn', '_renderTotalsMonth'];

    function makeHost(extra) {
        const els = {
            wsTtBody: { innerHTML: '', minWidth: null,
                        querySelector: function() {
                            return { style: { minWidth: '' } };
                        } },
            wsTtWarn: { textContent: '', hidden: true, attrs: {},
                        setAttribute: function(k, v) { this.attrs[k] = v; } }
        };
        const host = new Function('document', 'return ({' +
            MONTH_METHODS.map(function(n) {
                return methodText(WS_CLIENT, n);
            }).join('\n') + '\n' +
            '_totalsExtra: false,' +
            '_year: 2026, _month: 9,' +
            '_applyTtHeadVar: function() { return false; },' +
            '_fitGrid: function() {},' +
            '_syncTotalsRows: function() {},' +
            '_EMPLOYEES: [' +
            "  { 'таб_номер': '0871', 'ФИО': 'Иванов И.И.', 'тип': 'сменный' }," +
            "  { 'таб_номер': '023', 'ФИО': 'Петров П.П.', 'тип': 'дневной' }" +
            '],' +
            '_ENTRIES: [' +
            "  { 'дата': '2026-09-01', 'таб_номер': '0871', 'статус': 'Д' }," +
            "  { 'дата': '2026-09-02', 'таб_номер': '0871', 'статус': 'Н' }," +
            "  { 'дата': '2026-09-03', 'таб_номер': '023', 'статус': 'Д8' }" +
            '],' +
            '_PENDING: {},' +
            '_STATUS_CODES: [' +
            "  { code: 'Д', name: 'День (12-час)', color: '#FFE082' }," +
            "  { code: 'Д8', name: 'День 8-час', color: '#FFF9C4' }," +
            "  { code: 'Н', name: 'Ночь (12-час)', color: '#B0BEC5' }" +
            '] });')(mockDoc(els));
        Object.assign(host, extra || {});
        return { host: host, els: els };
    }

    test('месяц (свёрнуто): ТОЛЬКО Явки, Часы, Переработка — ПОРЯДОК (заявка)', () => {
        const t = makeHost();
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        const ths = h.match(/<th[^>]*>[^<]*<\/th>/g) || [];
        const names = ths.map(function(x) { return x.replace(/<[^>]*>/g, ''); });
        assertEqual(JSON.stringify(names),
            JSON.stringify(['Сотрудник', 'Явки', 'Часы', 'Переработка']),
            'заголовки: Сотрудник + основные в порядке заявки');
        assertFalse(h.indexOf('<th>Всего</th>') !== -1, 'столбца «Всего» нет');
        assertFalse(h.indexOf('<tfoot>') !== -1, 'tfoot (общее количество) нет');
    });

    test('месяц (свёрнуто): доп. столбцы НЕ рендерятся', () => {
        const t = makeHost();
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        for (const name of ['Отгул (ОВ)', 'Больничный (Б)', 'Отпуск (ОТ)',
                            'Уч. отпуск (У)', 'Прогул (ПР)', 'День (Д)',
                            'Ночь (Н)', 'Прочие']) {
            assertFalse(h.indexOf('<th>' + name + '</th>') !== -1,
                '«' + name + '» скрыт до «Ещё»');
        }
    });

    test('месяц («Ещё»): все 8 доп. столбцов в порядке ЗАЯВКИ', () => {
        const t = makeHost({ _totalsExtra: true });
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        const ths = h.match(/<th[^>]*>[^<]*<\/th>/g) || [];
        const names = ths.map(function(x) { return x.replace(/<[^>]*>/g, ''); });
        assertEqual(JSON.stringify(names), JSON.stringify([
            'Сотрудник', 'Явки', 'Часы', 'Переработка',
            'Отгул (ОВ)', 'Больничный (Б)', 'Отпуск (ОТ)', 'Уч. отпуск (У)',
            'Прогул (ПР)', 'День (Д)', 'Ночь (Н)', 'Прочие'
        ]), 'порядок заявки: основные + Отгул, Больничный, Отпуск, Уч. отпуск, Прогул, День, Ночь, Прочие');
        assertFalse(h.indexOf('<th>Всего</th>') !== -1, 'столбца «Всего» нет даже при «Ещё»');
    });

    test('месяц: значения строк — без итоговой строки', () => {
        const t = makeHost();
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('Иванов И.И.') !== -1, 'строка Иванова');
        assertTrue(h.indexOf('>24</td>') !== -1, 'часы Иванова 12+12');
        assertTrue(h.indexOf('>8</td>') !== -1, 'часы Петрова 8');
        const body = h.match(/<tbody>[\s\S]*?<\/tbody>/);
        const rows = body ? (body[0].match(/<tr>/g) || []).length : 0;
        assertEqual(rows, 2, 'ровно 2 строки сотрудников в tbody (без Итого)');
    });

    test('JS: min-width при «Ещё» — прокрутка широких столбцов', () => {
        const txt = methodText(WS_CLIENT, '_renderTotalsMonth');
        assertTrue(txt.indexOf('minWidth') !== -1 &&
                   txt.indexOf("cols.length * 64") !== -1,
            'разворот: таблица шире панели (≥64px на столбец)');
    });

    test('JS: год — tfoot «Итого» не рендерится (заявка)', () => {
        const txt = methodText(WS_CLIENT, '_renderTotalsYearTable');
        assertFalse(txt.indexOf('<tfoot>') !== -1, 'год: tfoot не рендерится');
        assertFalse(txt.indexOf('Итого по подразделению') !== -1, 'год: подписи Итого нет');
    });

    test('JS: _fitGrid — бюджет БЕЗ резерва итоговой строки', () => {
        const txt = methodText(WS_CLIENT, '_fitGrid');
        assertFalse(txt.indexOf("querySelector('#wsTtBody .ws-tt-total')") !== -1,
            'высота tfoot не читается (строки Итого нет)');
        assertTrue(txt.indexOf('var ttFootH = 0;') !== -1,
            'резерв = 0 (константа)');
        assertTrue(txt.indexOf('var budget = avail - headH - footH - ttFootH;') !== -1,
            'формула бюджета сохранена');
    });
});

// ============================================================
// 5. Service Worker
// ============================================================
describe('Task 327 — Service Worker', () => {
    test('SW: версия кэша kipia-test-v566', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v566'") !== -1,
            'CACHE_VERSION = kipia-test-v566 (Task 327 — только фронтенд)');
        assertFalse(SW_SRC.indexOf('kipia-test-v567') !== -1,
            'лишний инкремент не делался');
    });
});
