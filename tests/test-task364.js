// tests/test-task364.js
// Task 364 — заявка пользователя: «Красные линии вокруг ГРУППЫ
// ячеек выходных сделай 2px и по меньше яркости. Коды под
// графиком на печати размести в столбик справа от столбика
// мероприятий»:
//   • РАМКА-ГРУППА выходных (Task 363): 3px #e53935 → 2px #e57373
//     — та же рамка вокруг столбцов группы (верх-тень/бока/низ),
//     тоньше и бледнее; кнопка увольнения .ws-dismiss-submit
//     (#e53935) НЕ тронута;
//   • ПЕЧАТЬ: мероприятия и коды — ДВЕ КОЛОНКИ одного ряда под
//     таблицей (обёртка .wsp-bottom, flex: мероприятия слева,
//     коды справа, max-width 44%), сноска wsp-foot — ниже
//     обёртки на всю ширину; каждая запись/код — отдельной
//     строкой своего столбика (как в Task 360).
//
// SW: kipia-test-v593.
//
// Запуск: через tests/run-all.js (require './test-task364.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

const WS_START = INDEX_SRC.indexOf('var WorkSchedule = {');
const WS_CLIENT = INDEX_SRC.slice(WS_START, WS_START + 520000);

function methodText(src, name) {
    const sig = '\n        ' + name + ': function';
    const i = src.indexOf(sig);
    if (i === -1) return '';
    const rest = src.slice(i + 1);
    const m = rest.match(/\n        [a-zA-Z_]+: function|\n    \};/);
    const end = m ? m.index : rest.length;
    return rest.slice(0, end);
}

function stripComments(src) {
    return String(src)
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^[ \t]*\/\/.*$/gm, '');
}

function mockEsc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function cssRule(src, selector) {
    const i = src.indexOf(selector + ' {');
    if (i === -1) return '';
    return src.slice(i, src.indexOf('}', i) + 1);
}

// ============================================================
// 1. SRC — рамка-группа 2px #e57373 (Task 364)
// ============================================================
describe('Task 364 — SRC: рамка выходных 2px #e57373', () => {

    function wgrpBlock() {
        const i = INDEX_SRC.indexOf('.ws-grid thead th.ws-day-col.ws-wgrp {');
        const j = INDEX_SRC.indexOf('/* === Task 260', i);
        return INDEX_SRC.slice(i, j);
    }

    test('SRC: в правилах wgrp нет 3px и яркого #e53935', () => {
        const b = wgrpBlock();
        assertEqual(b.indexOf('3px'), -1, 'толщина 3px убрана из рамки');
        assertEqual(b.indexOf('#e53935'), -1, 'яркий красный убран из рамки');
        assertTrue(b.indexOf('2px') !== -1, 'толщина 2px в правилах');
        assertTrue(b.indexOf('#e57373') !== -1, 'спокойный красный #e57373');
    });

    test('SRC: все 6 линий рамки — 2px #e57373', () => {
        const b = wgrpBlock();
        assertEqual(b.split('2px solid #e57373').length - 1, 5,
            '5 сплошных границ (бока th/td + низ) по 2px #e57373');
        assertTrue(b.indexOf('inset 0 2px 0 0 #e57373') !== -1,
            'верх — внутренняя тень 2px #e57373');
    });

    test('SRC: кнопка увольнения .ws-dismiss-submit сохраняет #e53935', () => {
        const r = cssRule(INDEX_SRC, '.ws-dismiss-submit');
        assertTrue(r.indexOf('#e53935') !== -1,
            'кнопка увольнения НЕ перекрашена (регресс)');
    });
});

// ============================================================
// 2. SRC — печать: обёртка wsp-bottom (коды справа)
// ============================================================
describe('Task 364 — SRC: wsp-bottom на печати', () => {

    test('SRC: CSS .wsp-bottom — flex-ряд с зазором', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-bottom');
        assertTrue(r !== '', 'правило обёртки есть');
        assertTrue(r.indexOf('display: flex') !== -1, 'flex-раскладка');
        assertTrue(r.indexOf('flex-direction: row') !== -1,
            'колонки в один ряд (мероприятия слева, коды справа)');
        assertTrue(r.indexOf('align-items: flex-start') !== -1,
            'колонки от общего верха');
        assertTrue(r.indexOf('gap: 5mm') !== -1, 'зазор между столбиками 5mm');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы перенесён на обёртку');
    });

    test('SRC: CSS .wsp-mev — тянется на свободную ширину слева', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        assertTrue(r.indexOf('flex: 1 1 auto') !== -1,
            'мероприятия занимают остаток ряда');
        assertTrue(r.indexOf('min-width: 0') !== -1, 'перенос длинных строк');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'личный отступ сверху снят (отступ — на обёртке)');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });

    test('SRC: CSS .wsp-legend — правая колонка без растяжения', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        assertTrue(r.indexOf('flex: 0 0 auto') !== -1,
            'кодам НЕ растягиваться на остаток (правый столбик)');
        assertTrue(r.indexOf('max-width: 44%') !== -1,
            'не шире 44% листа');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'личный отступ сверху снят');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });

    test('SRC: JS — обёртка открывается ДО секции мероприятий', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom строится');
        assertTrue(iOpen < iMev, 'открытие обёртки до мероприятий');
        assertTrue(iMev < iLegend, 'мероприятия раньше кодов в ряду');
        assertTrue(iLegend < iFoot, 'сноска — после ряда');
    });

    test('SRC: JS — обёртка закрывается ПОСЛЕ перечня кодов (двойной div)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iClose = b.indexOf("html += '</div></div>';");
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iClose !== -1, 'двойное закрытие legend + обёртки');
        assertTrue(iClose > iLegend, 'закрытие после перечня кодов');
        assertTrue(iClose < iFoot, 'сноска строится после закрытия обёртки');
    });
});

// ============================================================
// 3. VM — печатный лист: структура ряда мероприятий|кодов
// ============================================================
// Хост из Task 362 (вид + «Инструктажи»), проверяем только
// структуру обёртки
function sheetHost(opts) {
    opts = opts || {};
    return new Function('ProdCalendar', 'return ({' +
        methodText(WS_CLIENT, '_buildPrintHtml') + '\n' +
        '_year: 2026, _month: 9, ' +
        '_view: ' + JSON.stringify(opts.view || 'full') + ',' +
        '_isoDate: function(dt) { return dt.getFullYear() + "-" + ' +
            '(dt.getMonth() < 9 ? "0" : "") + (dt.getMonth() + 1) + "-" + ' +
            '(dt.getDate() < 10 ? "0" : "") + dt.getDate(); },' +
        '_buildEntryIndex: function() { return ' + JSON.stringify(opts.entries || {}) + '; },' +
        '_PENDING: {},' +
        '_posLabel: function() { return "Слесарь КИПиА"; },' +
        '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
        '_STATUS_CODES: ' + JSON.stringify([
            { code: 'Д', name: 'День (12-час)', color: '#FFE082' },
            { code: 'И', name: 'Инструктаж', color: '#B3E5FC' },
            { code: 'ПЗ', name: 'Проверка знаний', color: '#FFCDD2' }]) + ',' +
        '_calDayOff: function(day) { return day % 7 === 0 || day % 7 === 6; },' +
        '_vacationAt: function() { return null; },' +
        '_TRAININGS: ' + JSON.stringify(opts.trainings || [
            { 'таб_номер': '017', 'тип': 'инструктаж',
              'дата_начала': '2026-09-07', 'тема': 'Повторный инструктаж' },
            { 'таб_номер': '023', 'тип': 'проверка_знаний',
              'дата_начала': '2026-09-15', 'дата_окончания': '2026-09-16',
              'тема': 'Проверка знаний промбезопасности' }]) + ',' +
        '_EMPLOYEES: ' + JSON.stringify([
            { 'ФИО': 'Иванов Иван Иванович', 'таб_номер': '017' },
            { 'ФИО': 'Петров Пётр Петрович', 'таб_номер': '023' }]) + ',' +
        '_trainingCodeOf: function(t) { ' +
            'return t === "инструктаж" ? "И" : (t === "проверка_знаний" ? "ПЗ" : ""); },' +
        '_statusMeta: function(code) { ' +
            'var m = { "Д": { code: "Д", color: "#FFE082", name: "День (12-час)" }, ' +
            '"И": { code: "И", color: "#B3E5FC", name: "Инструктаж" }, ' +
            '"ПЗ": { code: "ПЗ", color: "#FFCDD2", name: "Проверка знаний" } }; ' +
            'return m[code] || null; },' +
        '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
        '_printCell: function() { return "<td></td>"; },' +
        '_esc: ' + mockEsc.toString() + ',' +
        '});')();
}

var EMPS = [
    { 'ФИО': 'Иванов Иван Иванович', 'таб_номер': '017' },
    { 'ФИО': 'Петров Пётр Петрович', 'таб_номер': '023' }
];
var AGG = { byTab: {}, grand: null };

describe('Task 364 — VM: ряд мероприятий|кодов в печати', () => {

    test('VM: лист содержит обёртку, внутри — мероприятия и коды', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iMev = html.indexOf('<div class="wsp-mev">');
        var iLegend = html.indexOf('<div class="wsp-legend">');
        var iClose = html.indexOf('</div></div>', iLegend);
        var iFoot = html.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom в листе');
        assertTrue(iOpen < iMev && iMev < iLegend, 'мероприятия и коды внутри обёртки');
        assertTrue(iClose !== -1 && iClose > iLegend, 'обёртка закрыта после кодов');
        assertTrue(iFoot > iClose, 'сноска — ПОД обёрткой, на всю ширину');
    });

    test('VM: у мероприятий и кодов НЕТ личных отступов сверху (единый ряд)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        // структура CSS проверена в SRC; здесь — что оба блока
        // в одном родителе: между закрытием mev и открытием legend
        // нет обёрток-посредников с отступами
        var iMevEnd = html.indexOf('</div>', html.indexOf('<div class="wsp-mev">'));
        var iLegend = html.indexOf('<div class="wsp-legend">');
        var between = html.slice(iMevEnd + 6, iLegend);
        assertEqual(between.replace(/\s+/g, ''), '',
            'legend — непосредственный сосед mev в обёртке');
    });

    test('VM: регресс 362 — ПЗ печатается в перечне кодов (в обёртке)', () => {
        var html = sheetHost({ view: 'day' })._buildPrintHtml([EMPS[1]], AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iClose = html.indexOf('</div></div>', iOpen);
        var row = html.slice(iOpen, iClose);
        assertTrue(row.indexOf('ПЗ — Проверка знаний') !== -1,
            'наименование ПЗ в перечне кодов внутри ряда');
        assertTrue(row.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий в ряду (вид: дневной)');
    });

    test('VM: пустой месяц — заглушка в левой колонке, коды справа', () => {
        var html = sheetHost({ trainings: [] })._buildPrintHtml(EMPS, AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iClose = html.indexOf('</div></div>', iOpen);
        var row = html.slice(iOpen, iClose);
        assertTrue(row.indexOf('нет мероприятий в этом месяце') !== -1,
            'заглушка мероприятий на месте');
        assertTrue(row.indexOf('Коды:') !== -1, 'заголовок кодов в ряду');
    });
});

// ============================================================
// 4. SW — версия кеша
// ============================================================
describe('Task 364 — SW: версия кеша', () => {
    test('SW: CACHE_VERSION = kipia-test-v593', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v593'") !== -1,
            'SW поднят до v593 (рамка 2px + коды справа от мероприятий)');
    });
});
