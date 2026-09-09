// tests/test-task343.js
// Task 343 — заявка пользователя: «из печати убери строку итогов
// и миниатюры иконок мероприятий» (правка печатной формы графика
// работ — Tasks 341/342). Печатный лист #wsPrintSheet:
//   • ИТОГОВАЯ СТРОКА «Итого» по подразделению (wsp-sum) УБРАНА —
//     agg.grand больше не используется в _buildPrintHtml; grand-
//     итоги остаются в приложении (вкладка «Месяц» «Итогов
//     учёта»); построчные колонки «Дни»/«Часы»/«Перераб.» живы;
//   • БЕЙДЖИ МЕРОПРИЯТИЙ в ячейках (wsp-ev/wsp-ev-plan —
//     «миниатюры иконок»: инструктажи/обучение/проверки) УБРАНЫ:
//     _printCell не вызывает _eventsAt и не строит виртуальный
//     бейдж статус-мероприятия; день с мероприятием печатается
//     ПУСТОЙ ячейкой (как в экранной сетке — без большого кода);
//   • CSS: правила .wsp-sum/.wsp-ev-* удалены из @media print;
//     сноска wsp-foot больше не упоминает бейдж мероприятий;
//   • НЕ тронуты: красная точка переработки, пунктирный план
//     отпуска, серая заливка пустых нерабочих, легенда кодов,
//     экранная сетка (бейджи мероприятий на экране остаются —
//     классы ws-ev-badge/ws-ev-wrap, Task 314).
//
// SW: kipia-test-v583.
//
// Запуск: через tests/run-all.js (require './test-task343.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

// Срез исходника от начала объекта WorkSchedule (имена методов
// НЕуникальны в файле — извлекаем только из модуля «График работы»)
const WS_START = INDEX_SRC.indexOf('var WorkSchedule = {');
const WS_CLIENT = INDEX_SRC.slice(WS_START, WS_START + 500000);

function methodText(src, name) {
    const sig = '\n        ' + name + ': function';
    const i = src.indexOf(sig);
    if (i === -1) return '';
    const rest = src.slice(i + 1);
    const m = rest.match(/\n        [a-zA-Z_]+: function|\n    \};/);
    const end = m ? m.index : rest.length;
    return rest.slice(0, end);
}

// Убирает комментарии (/* */ и //) — ассерты SRC проверяют КОД,
// а комментарии Task 343 в методах объясняют удаление и упоминают
// старые имена (wsp-ev/agg.grand/_eventsAt) как УДАЛЁННЫЕ
function stripComments(src) {
    return String(src)
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^[ \t]*\/\/.*$/gm, '');
}

// Простейший эскейп для моков (поведение = WorkSchedule._esc)
function mockEsc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ============================================================
// 1. SRC — итоговая строка убрана
// ============================================================
describe('Task 343 — итоговая строка убрана из печати', () => {

    test('SRC: _buildPrintHtml не строит wsp-sum, agg.grand не используется', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.length > 0, 'метод найден');
        assertTrue(b.indexOf('wsp-sum') === -1, 'разметки wsp-sum нет');
        assertTrue(b.indexOf('agg.grand') === -1, 'agg.grand не используется');
        assertTrue(b.indexOf("'</tbody></table>'") !== -1,
            'таблица закрывается сразу после строк сотрудников');
    });

    test('SRC: колонки построчных итогов живы (регресс 342)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('<th class="wsp-tot">Дни</th>') !== -1, 'колонка «Дни»');
        assertTrue(b.indexOf('<th class="wsp-tot">Часы</th>') !== -1, 'колонка «Часы»');
        assertTrue(b.indexOf('wsp-tot-over">Перераб.<span>дни/ч</span></th>') !== -1,
            'колонка «Перераб.» (Task 342)');
        assertTrue(b.indexOf('agg.byTab') !== -1, 'построчные итоги из agg.byTab');
    });

    test('SRC: CSS-правило .wsp-sum удалено из @media print', () => {
        const i = INDEX_SRC.indexOf('@media print');
        assertTrue(i !== -1, 'блок @media print есть');
        const block = stripComments(INDEX_SRC.slice(i, i + 6000));
        assertTrue(block.indexOf('#wsPrintSheet .wsp-sum') === -1,
            'правило .wsp-sum удалено');
    });
});

// ============================================================
// 2. SRC — бейджи мероприятий убраны из печати
// ============================================================
describe('Task 343 — бейджи мероприятий убраны из печати', () => {

    test('SRC: _printCell не строит wsp-ev и не вызывает _eventsAt', () => {
        const c = stripComments(methodText(WS_CLIENT, '_printCell'));
        assertTrue(c.length > 0, 'метод найден');
        assertTrue(c.indexOf('wsp-ev') === -1, 'бейджей wsp-ev нет');
        assertTrue(c.indexOf('_eventsAt') === -1, '_eventsAt не вызывается');
        assertTrue(c.indexOf('evHtml') === -1, 'переменной evHtml нет');
    });

    test('SRC: CSS-правила бейджей .wsp-ev* удалены из @media print', () => {
        const i = INDEX_SRC.indexOf('@media print');
        const block = stripComments(INDEX_SRC.slice(i, i + 6000));
        assertTrue(block.indexOf('#wsPrintSheet .wsp-ev') === -1,
            'правило .wsp-ev удалено');
        assertTrue(block.indexOf('wsp-ev-wrap') === -1,
            'правило .wsp-ev-wrap удалено');
        assertTrue(block.indexOf('wsp-ev-plan') === -1,
            'правило .wsp-ev-plan удалено');
    });

    test('SRC: сноска wsp-foot не упоминает бейдж мероприятий', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('бейдж в углу ячейки') === -1,
            'упоминание бейджа мероприятия удалено');
        assertTrue(b.indexOf('пунктирная рамка ячейки — плановый отпуск') !== -1,
            'пояснение плана отпуска живо (регресс 341)');
        assertTrue(b.indexOf('красная точка — переработка') !== -1,
            'пояснение переработки живо (регресс 341/342)');
    });

    test('SRC: ЭКРАННАЯ сетка не тронута — бейджи на экране живут (Task 314)', () => {
        const rc = methodText(WS_CLIENT, '_renderCell');
        assertTrue(rc.indexOf('ws-ev-badge') !== -1,
            'экранные бейджи ws-ev-badge на месте');
        assertTrue(rc.indexOf('ws-ev-wrap') !== -1, 'обёртка ws-ev-wrap на месте');
        assertTrue(rc.indexOf('_eventsAt') !== -1,
            'экранный рендер по-прежнему вызывает _eventsAt');
    });

    test('SRC: метод _eventsAt жив (экран/попап мероприятий)', () => {
        const ev = methodText(WS_CLIENT, '_eventsAt');
        assertTrue(ev.length > 0, '_eventsAt определён (для экранной сетки)');
    });
});

// ============================================================
// 3. VM — _printCell: пустые ячейки мероприятий
// ============================================================
describe('Task 343 — _printCell (VM)', () => {

    function cellHost(over) {
        over = over || {};
        return new Function('return ({' +
            methodText(WS_CLIENT, '_printCell') + '\n' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_statusMeta: function(code) { return ' + JSON.stringify(over.meta || { code: 'Д', color: '#FFE082' }) + '; },' +
            '_calDayOff: function(day) { return ' + JSON.stringify(over.dayOff === undefined ? false : over.dayOff) + '; },' +
            '_vacationAt: function(iso, tab) { return ' + JSON.stringify(over.vac || null) + '; },' +
            '_eventsAt: function(iso, tab) { return ' + JSON.stringify(over.events || []) + '; },' +
            '_esc: ' + mockEsc.toString() + ',' +
            '});')();
    }

    var EMP = { 'таб_номер': '017' };

    test('VM: статус-мероприятие «И» — ПУСТАЯ ячейка (кода и бейджа нет)', () => {
        var td = cellHost({ meta: { code: 'И', color: '#B3E5FC' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(10, '2026-09-10', EMP, { 'статус': 'И' });
        assertTrue(td.indexOf('>И<') === -1, 'ни кода, ни текста бейджа');
        assertTrue(td.indexOf('wsp-ev') === -1, 'бейджа нет');
        assertTrue(td.indexOf('background:') === -1, 'фона нет (ячейка пустая)');
    });

    test('VM: события дня в ПУСТОЙ ячейке — НЕ печатаются', () => {
        var td = cellHost({ events: [{ code: 'ОБ', training: 8 },
                                      { code: 'ПР', training: 9 }] })
            ._printCell(11, '2026-09-11', EMP, null);
        assertTrue(td.indexOf('wsp-ev') === -1, 'бейджей нет');
        assertTrue(td.indexOf('ОБ') === -1 && td.indexOf('ПР') === -1,
            'коды мероприятий не выводятся');
        assertTrue(/<td class="wsp-cell"><\/td>/.test(td) ||
                   /<td class="wsp-cell"[^>]*><\/td>/.test(td),
            'пустая ячейка');
    });

    test('VM: регресс — код с фоном, точка переработки, план отпуска живы', () => {
        var td = cellHost()._printCell(2, '2026-09-02', EMP,
                                       { 'статус': 'Д' });
        assertTrue(td.indexOf('>Д</td>') !== -1 && td.indexOf('background:#FFE082') !== -1,
            'код с inline-фоном');
        var ov = cellHost()._printCell(3, '2026-09-03', EMP,
                                       { 'статус': 'д', 'переработка': 1 });
        assertTrue(ov.indexOf('wsp-over') !== -1, 'красная точка переработки');
        var vac = cellHost({ vac: { 'дата_начала': '2026-09-01' } })
            ._printCell(4, '2026-09-04', EMP, null);
        assertTrue(vac.indexOf('wsp-vac') !== -1, 'пунктирный план отпуска');
    });

    test('VM: _eventsAt в моке НЕ вызывается из _printCell', () => {
        var calls = 0;
        var host = new Function('return ({' +
            methodText(WS_CLIENT, '_printCell') + '\n' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_statusMeta: function() { return {}; },' +
            '_calDayOff: function() { return false; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { calls++; return []; },' +
            '_esc: ' + mockEsc.toString() + ',' +
            '});')();
        host._printCell(5, '2026-09-05', EMP, { 'статус': 'И' });
        host._printCell(6, '2026-09-06', EMP, null);
        assertEqual(calls, 0, '_eventsAt не вызывается ни разу');
    });
});

// ============================================================
// 4. VM — _buildPrintHtml: лист без итоговой строки
// ============================================================
describe('Task 343 — _buildPrintHtml (VM)', () => {

    function sheetHost(opts) {
        opts = opts || {};
        return new Function('ProdCalendar', 'return ({' +
            methodText(WS_CLIENT, '_buildPrintHtml') + '\n' +
            '_year: 2026, _month: 9, _view: ' + JSON.stringify(opts.view || 'full') + ',' +
            '_isoDate: function(dt) { return dt.getFullYear() + "-" + ' +
                '(dt.getMonth() < 9 ? "0" : "") + (dt.getMonth() + 1) + "-" + ' +
                '(dt.getDate() < 10 ? "0" : "") + dt.getDate(); },' +
            '_buildEntryIndex: function() { return ' + JSON.stringify(opts.entries || {}) + '; },' +
            '_PENDING: ' + JSON.stringify(opts.pending || {}) + ',' +
            '_posLabel: function() { return "Слесарь КИПиА, смена 1"; },' +
            '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
            '_STATUS_CODES: ' + JSON.stringify(opts.codes || [
                { code: 'Д', name: 'День (12-час)', color: '#FFE082' },
                { code: 'д', name: 'Переработка (день)', color: '#FFCCBC' }]) + ',' +
            '_calDayOff: function(day) { return day % 7 === 0 || day % 7 === 6; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { return []; },' +
            '_statusMeta: function(code) { return { code: code, color: "#FFE082" }; },' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_printCell: function(day, iso, emp, entry) { return "<td>[" + (entry ? entry.статус : "-") + "]</td>"; },' +
            '_esc: ' + mockEsc.toString() + ',' +
            '});')(opts.pcal);
    }

    var EMPS = [
        { 'ФИО': 'Иванов Иван Иванович', 'таб_номер': '017' },
        { 'ФИО': 'Сидоров Сидор Сидорович', 'таб_номер': '031' }
    ];

    test('VM: agg С grand — итоговой строки НЕТ в листе', () => {
        var agg = {
            byTab: { '017': { work: 21, hours: 151.2, over: 12, overDays: 1 } },
            grand: { work: 21, hours: 151.2, over: 12, overDays: 1 }
        };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        assertTrue(html.indexOf('wsp-sum') === -1, 'wsp-sum нет');
        assertTrue(html.indexOf('Итого') === -1, 'слова «Итого» нет');
        // построчные итоги при этом на месте
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">1/12</td>') !== -1,
            'колонка «Перераб.» сотрудника жива (регресс 342)');
    });

    test('VM: agg БЕЗ grand (null) — лист строится, не падает', () => {
        var agg = { byTab: { '017': { work: 21, hours: 151.2 } }, grand: null };
        var html = sheetHost()._buildPrintHtml([EMPS[0]], agg);
        assertTrue(html.indexOf('wsp-title') !== -1, 'лист построен');
        assertTrue(html.indexOf('>21</td>') !== -1, 'построчные дни на месте');
    });

    test('VM: структура — шапка, строки, легенда, сноска; после строк таблица закрывается', () => {
        var agg = { byTab: {}, grand: null };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        var iClose = html.indexOf('</tbody></table>');
        assertTrue(iClose !== -1, 'таблица закрыта');
        assertTrue(html.indexOf('wsp-legend') !== -1, 'легенда после таблицы');
        assertTrue(html.indexOf('wsp-foot') !== -1, 'сноска жива');
        assertTrue(html.indexOf('<tr class="') === -1 ||
                   html.indexOf('wsp-sum') === -1, 'служебных строк нет');
    });

    test('VM: сноска — пояснения живы, упоминания мероприятий НЕТ', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, { byTab: {}, grand: null });
        var foot = html.slice(html.indexOf('wsp-foot'));
        assertTrue(foot.indexOf('мероприятие') === -1, 'мероприятия не упоминаются');
        assertTrue(foot.indexOf('«Перераб.» — дни/часы переработки') !== -1,
            'пояснение колонки (регресс 342)');
        assertTrue(foot.indexOf('пунктирная рамка') !== -1, 'план отпуска пояснён');
    });
});

// ============================================================
// 5. Service Worker
// ============================================================
describe('Task 343 — Service Worker', () => {

    test('SW: кэш поднят до kipia-test-v583', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v583'") !== -1,
            'CACHE_VERSION = kipia-test-v583 (Task 343 — фронтенд)');
        assertFalse(SW_SRC.indexOf('kipia-test-v584') !== -1,
            'лишний инкремент (v582) не сделан');
    });

    test('SW: в index.html нет захардкоженной версии кэша', () => {
        assertFalse(INDEX_SRC.indexOf('kipia-test-v58') !== -1,
            'клиент не знает номер кэша (версией управляет sw.js)');
    });
});
