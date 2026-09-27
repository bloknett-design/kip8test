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
// SW: kipia-test-v659.
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

    test('SRC: CSS .wsp-bottom — обёртка вертикальной секции (Task 433)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-bottom');
        assertTrue(r !== '', 'правило обёртки есть');
        // Task 433 (заявка: «расположение кодов в печати верни
        // обратно…»): флоат Task 432 и flex-ряд Task 364–431
        // СНЯТЫ — нижняя секция ВЕРТИКАЛЬНАЯ: список мероприятий
        // на всю ширину, коды — строкой-абзацем ПОД ним
        assertTrue(r.indexOf('display: flex') === -1,
            'flex-ряда нет (Task 433: вертикальная секция)');
        assertTrue(r.indexOf('flow-root') === -1,
            'флоат-обёртки Task 432 больше нет');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы перенесён на обёртку');
    });

    test('SRC: CSS .wsp-mev — строки на всю ширину листа (Task 432)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        // Task 432: flex снят — блок мероприятий на всю ширину, строки
        // ТЕКУТ вокруг плавающих кодов (рядом — до кромки кодов минус
        // 10px, ниже — до конца листа), переносятся ТОЛЬКО когда
        // места не хватает (прежде 0 1 auto Task 431 сжимал колонку
        // по тексту — правая часть листа пустовала)
        assertTrue(r.indexOf('flex:') === -1,
            'мероприятия НЕ в flex-колонке (Task 432: обтекание)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'личный отступ сверху снят (отступ — на обёртке)');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });

    test('SRC: CSS .wsp-legend — строка-абзац ПОД списком (Task 433)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        // Task 433 (заявка: «расположение кодов в печати верни
        // обратно»): ВЕРНУЛИ исходную форму «в одну строку» —
        // флоат и max-width сняты, блок — обычный абзац ПОД
        // списком мероприятий, растянутый до конца листа
        assertTrue(r.indexOf('float:') === -1,
            'флоат Task 432 снят (коды — не плавающий столбик)');
        assertTrue(r.indexOf('max-width') === -1,
            'кап ширины Task 364 снят');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от списка мероприятий сверху');
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
        // Task 433: секция ВЕРТИКАЛЬНАЯ — список мероприятий
        // ПЕРВЫМ, коды — строкой-абзацем ПОД ним (флоат Task 432
        // строил коды первыми в DOM)
        assertTrue(iMev < iLegend, 'коды — ПОД списком мероприятий (Task 433)');
        assertTrue(iLegend < iFoot, 'сноска — после кодов');
    });

    test('SRC: JS — обёртка закрывается ПОСЛЕ кодов (двойной div)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        // Task 433: порядок — мероприятия → коды → закрытие обёртки:
        // закрытие кодов и обёртки — ДВА последовательных оператора
        const iClose1 = b.indexOf("html += '</div>';", iLegend);
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iClose1 !== -1 && iClose2 !== -1,
            'двойное закрытие legend + обёртки');
        assertTrue(iClose1 > iLegend, 'закрытие после перечня кодов');
        assertTrue(iClose2 - iClose1 < 200,
            'операторы закрытия — подряд');
        assertTrue(iClose2 < iFoot, 'сноска строится после закрытия обёртки');
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
        methodText(WS_CLIENT, '_instrShortOf') + '\n' +
            methodText(WS_CLIENT, '_normInstrKey') + '\n' +
            methodText(WS_CLIENT, '_instrShortOf') + '\n' +
            methodText(WS_CLIENT, '_normInstrKey') + '\n' +
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
        // Task 433: секция вертикальная — мероприятия ПЕРВЫМИ,
        // коды — ПОД списком (флоат Task 432 строил коды первыми)
        assertTrue(iOpen < iMev && iMev < iLegend,
            'мероприятия, за ними коды — внутри обёртки (Task 433)');
        assertTrue(iClose !== -1 && iClose > iLegend, 'обёртка закрыта после кодов');
        assertTrue(iFoot > iClose, 'сноска — ПОД обёрткой, на всю ширину');
    });

    test('VM: у мероприятий и кодов НЕТ личных обёрток-посредников', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        // структура CSS проверена в SRC; здесь — что оба блока
        // в одном родителе: между закрытием mev и открытием legend
        // (Task 433: мероприятия строятся первыми) нет посредников
        var iMev = html.indexOf('<div class="wsp-mev">');
        var iLegend = html.indexOf('<div class="wsp-legend">');
        var iMevEnd = html.indexOf('</div>', iMev);
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
    test('SW: CACHE_VERSION = kipia-test-v659', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v659'") !== -1,
            'SW поднят до v659 (рамка 2px + коды строкой под мероприятиями — Task 433)');
    });
});
