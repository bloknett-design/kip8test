// ============================================================
// Task 441 — заявка (kip8test):
//   «Во всех трёх представлениях печати коды сделай в один
//    столбец. Переноси все изменения в боевой репозиторий kip8».
//   (Перенос партии 438–441 в kip8 — см. worklog/DEPLOY репо kip8;
//    здесь проверяется только клиентская часть kip8test.)
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   HTML-ПЕЧАТЬ (SRC):
//   1) сетка .wsp-legend-cols — ОДНА колонка (grid 1fr; прежде
//      ДВЕ равные 1fr 1fr — Task 434); column-gap снят (колонок
//      нет), row-gap жив; разметка <div class="wsp-legend-cols">
//      сохранена (класс не переименован — история задач жива);
//   2) записи .wsp-lg — прежние: строка, перенос внутри, не
//      рвётся (регресс Task 434);
//   PDF (SRC+VM):
//   3) _printPdfLayout: codeRows = ЧИСЛО кодов (без деления
//      ceil(n/2) пополам) — высота блока кодов по ОДНОЙ колонке;
//   4) _printPdfPaintPage: colW2/perCol УДАЛЕНЫ; lx = codeX (без
//      сдвига), ly = y + lc * codeRowH (сквозной столбец);
//   5) VM-раскладка: 18 кодов на низкой странице (H=300) — коды
//      уходят на СВОЮ страницу (при двух колонках Task 434/439
//      ехали бы с последним куском событий: cdH 144 ≤ 254, а в
//      одну колонку 270 > 254); коды не теряются (все 18);
//   6) VM-раскладка: обычный месяц — одна страница, все коды
//      рядом с мероприятиями (паритет max(evH, cdH) Task 439);
//   EXCEL (SRC+VM):
//   7) коды — по-прежнему ОДИН столбец D (строка на код),
//      ячеек правее D в строках блока нет;
//   SW: kipia-test-v665 (главный), v664 — прежней нет.
// ============================================================

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

const WS_START = INDEX_SRC.indexOf('var WorkSchedule = {');
const WS_CLIENT = INDEX_SRC.slice(WS_START, WS_START + 800000);

function extractMethod(src, name) {
    const start = src.indexOf(name + ': function(');
    if (start === -1) return null;
    const braceStart = src.indexOf('{', start);
    let depth = 0;
    for (let i = braceStart; i < src.length; i++) {
        if (src[i] === '{') depth++;
        else if (src[i] === '}') {
            depth--;
            if (depth === 0) return src.slice(start, i + 1);
        }
    }
    return null;
}

function methodText(src, name) {
    const m = extractMethod(src, name);
    if (m === null) throw new Error('метод не найден: ' + name);
    return m;
}

function stripComments(src) {
    return String(src)
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^[ \t]*\/\/.*$/gm, '');
}

function ruleBlock(sel) {
    const i = INDEX_SRC.indexOf(sel);
    if (i === -1) return '';
    return INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
}

// ============================================================
// 1. SRC — HTML-печать: сетка кодов ОДНА колонка
// ============================================================
describe('Task 441 — SRC: печать HTML (коды одним столбцом)', () => {

    test('CSS: .wsp-legend-cols — ОДНА колонка (grid 1fr)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend-cols {');
        assertTrue(r !== '', 'правило сетки есть');
        assertTrue(r.indexOf('display: grid') !== -1,
            'контейнер — grid (как в Task 434)');
        assertTrue(r.indexOf('grid-template-columns: 1fr;') !== -1,
            'ОДНА колонка на всю ширину блока кодов (Task 441)');
        assertFalse(r.indexOf('grid-template-columns: 1fr 1fr') !== -1,
            'ДВЕ равные колонки Task 434 сняты');
        assertFalse(r.indexOf('column-gap') !== -1,
            'column-gap снят — колонок больше нет (Task 441)');
        assertTrue(r.indexOf('row-gap') !== -1,
            'вертикальный зазор между записями жив');
        assertTrue(r.indexOf('align-items: start') !== -1,
            'выравнивание записей по верху живо');
    });

    test('CSS: .wsp-lg — запись кода своей строкой (регресс 434)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-lg {');
        assertTrue(r !== '', 'правило записи есть');
        assertTrue(r.indexOf('display: block') !== -1,
            'каждый код — своя строка столбца');
        assertTrue(r.indexOf('white-space: normal') !== -1,
            'длинное наименование переносится ВНУТРИ столбца');
        assertTrue(r.indexOf('break-inside: avoid') !== -1,
            'запись не рвётся между страницами');
    });

    test('JS: разметка сетки сохранена (класс wsp-legend-cols)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('<div class="wsp-legend-cols">') !== -1,
            'сетка .wsp-legend-cols строится (одна колонка — CSS)');
        assertTrue(b.indexOf('<span class="wsp-legend-t">Коды:</span>') !== -1,
            'заголовок «Коды:» — отдельно сверху');
        // двух колонок в разметке нет: каждый код — один span
        // .wsp-lg подряд (сетку колонок делает CSS)
        assertTrue(b.indexOf('<span class="wsp-lg">') !== -1,
            'записи кодов — span.wsp-lg');
    });
});

// ============================================================
// 2. SRC — PDF: раскладка и отрисовка одним столбцом
// ============================================================
describe('Task 441 — SRC: PDF (коды одним столбцом)', () => {

    test('_printPdfLayout: codeRows = число кодов (без деления)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_printPdfLayout'));
        assertTrue(b.indexOf('(model.codes || []).length') !== -1,
            'codeRows считается по полной длине кодов');
        assertFalse(b.indexOf('Math.ceil((model.codes || []).length / 2)') !== -1,
            'деление пополам (две колонки Task 434/439) снято');
        assertFalse(b.indexOf('/ 2') !== -1,
            'никаких делений пополам в раскладке кодов');
    });

    test('_printPdfPaintPage: colW2/perCol удалены, сквозной столбец', () => {
        const b = stripComments(methodText(WS_CLIENT, '_printPdfPaintPage'));
        assertFalse(b.indexOf('colW2') !== -1,
            'сдвиг второй колонки (colW2) удалён');
        assertFalse(b.indexOf('perCol') !== -1,
            'разбивка по колонкам (perCol) удалена');
        assertTrue(b.indexOf('var lx = codeX;') !== -1,
            'все коды — от codeX, без сдвига (ОДИН столбец)');
        assertTrue(b.indexOf('var ly = y + lc * lay.codeRowH;') !== -1,
            'строки — подряд: y + lc * codeRowH (сквозной столбец)');
    });

    test('SRC: геометрия зоны кодов не тронута (регресс 439/440)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_printPdfPaintPage'));
        assertTrue(b.indexOf('x0 + CW - codeW)') !== -1,
            'codeX ограничен правым краем листа минус codeW (Task 440)');
        assertTrue(b.indexOf('var codeW = lay.codeW || 235;') !== -1,
            'ширина зоны кодов — 235pt (Task 439)');
        const l = stripComments(methodText(WS_CLIENT, '_printPdfLayout'));
        assertTrue(l.indexOf('var colGap = opts.colGap || 7.5;') !== -1,
            'зазор 7.5pt = 10px (Task 440) жив');
    });
});

// ============================================================
// 3. VM — раскладка PDF: высота блока по ОДНОЙ колонке
// ============================================================
describe('Task 441 — VM: раскладка PDF (один столбец кодов)', () => {

    function fakeModel(nRows, nEvents, nCodes) {
        const days = [];
        for (let d = 1; d <= 30; d++) {
            days.push({ d: d, dow: 'Пн', off: false, feast: false, short: false });
        }
        const rows = [];
        for (let r = 0; r < nRows; r++) {
            rows.push({ fio: 'Работник №' + (r + 1), tip: '', tab: String(r),
                        cells: [], inAgg: true, work: 21, overDays: 0 });
        }
        const events = [];
        for (let e = 0; e < nEvents; e++) {
            events.push({ range: '0' + ((e % 9) + 1) + '.09',
                          text: 'Событие ' + (e + 1), code: 'И', color: '#B3E5FC' });
        }
        const codes = [];
        for (let c = 0; c < nCodes; c++) {
            codes.push({ code: 'К' + c, label: 'код ' + c, color: '#EEEEEE' });
        }
        return { year: 2026, month: 9, view: 'full',
                 days: days, rows: rows, events: events, codes: codes };
    }

    function layoutHost() {
        return new Function('return ({' +
            methodText(WS_CLIENT, '_printPdfLayout') +
            '});')();
    }

    test('VM: 18 кодов на низкой странице — коды СВОЯ страница', () => {
        // H=300: contentH = 254; evCap = 18 → 40 событий = 3 куска
        // (18+18+4). cdH одним столбцом = 18 + 18×14 = 270 > 254 —
        // коды НЕ едут с последним куском (при двух колонках
        // cdH = 18 + 9×14 = 144 ≤ 254 — ехали бы): страница кодов
        // отдельная, все 18 кодов на ней
        const lay = layoutHost()._printPdfLayout(fakeModel(0, 40, 18), { H: 300 });
        assertEqual(lay.pages.length, 4,
            '3 страницы событий + СВОЯ страница кодов (прежде 3 всего)');
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.codes, 'последняя страница — коды');
        assertTrue(!last.events, 'коды — БЕЗ мероприятий (отдельной страницей)');
        assertEqual(last.codes.length, 18, 'все 18 кодов (не теряются)');
        const prev = lay.pages[lay.pages.length - 2];
        assertTrue(!!prev.events && !prev.codes,
            'последний кусок событий — без кодов (не влезли одним столбцом)');
    });

    test('VM: обычный месяц — одна страница, все коды рядом', () => {
        // botH = max(18 + 3×13, 18 + 13×14) = max(57, 200) = 200;
        // 252 + 200 = 452 ≤ 549 — таблица + события + коды вместе
        const lay = layoutHost()._printPdfLayout(fakeModel(10, 3, 13));
        assertEqual(lay.pages.length, 1, 'всё на одной странице');
        assertEqual(lay.pages[0].codes.length, 13,
            'все 13 кодов — на странице (одним столбцом)');
        assertEqual(lay.pages[0].events.length, 3, 'события рядом (Task 439)');
    });

    test('VM: пара блоков — по-прежнему max, не сумма (регресс 439)', () => {
        // 22 строки → 2 страницы; 33 события: evH = 447;
        // cdH (4 кода, один столбец) = 74; пара = 447; влезает
        const lay = layoutHost()._printPdfLayout(fakeModel(22, 33, 4));
        assertEqual(lay.pages.length, 2, '2 страницы (пара = max)');
        const last = lay.pages[1];
        assertTrue(!!last.codes && !!last.events,
            'коды РЯДОМ с событиями на последней странице');
    });
});

// ============================================================
// 4. VM — Excel: коды одним столбцом D
// ============================================================
describe('Task 441 — VM: Excel (код — строка в колонке D)', () => {

    function tabelHost() {
        return new Function('ProdCalendar', 'return ({' +
            methodText(WS_CLIENT, '_printModel') + ',' +
            methodText(WS_CLIENT, '_printEventsData') + ',' +
            methodText(WS_CLIENT, '_printCodesData') + ',' +
            methodText(WS_CLIENT, '_wsTabelStylesXml') + ',' +
            methodText(WS_CLIENT, '_wsTabelRows') + ',' +
            methodText(WS_CLIENT, '_wsTabelSheetXml') + ',' +
            methodText(WS_CLIENT, '_buildTabelWorkbook') + ',' +
            methodText(WS_CLIENT, '_wsXlsZip') + ',' +
            methodText(WS_CLIENT, '_wsXlsBytes') + ',' +
            methodText(WS_CLIENT, '_wsXlsCrc32') + ',' +
            methodText(WS_CLIENT, '_wsXlsColName') + ',' +
            methodText(WS_CLIENT, '_wsXlsEsc') + ',' +
            '_year: 2026, _month: 9, _view: "full",' +
            '_isoDate: function(dt) { return dt.getFullYear() + "-" + ' +
                '(dt.getMonth() < 9 ? "0" : "") + (dt.getMonth() + 1) + "-" + ' +
                '(dt.getDate() < 10 ? "0" : "") + dt.getDate(); },' +
            '_buildEntryIndex: function() { return ' + JSON.stringify({
                '2026-09-02|017': { 'статус': 'ОТ' },
                '2026-09-03|031': { 'статус': 'Д' },
                '2026-09-04|017': { 'статус': '.' }
            }) + '; },' +
            '_PENDING: {},' +
            '_empTipLine: function(emp) { return emp && emp["таб_номер"] === "031" ? "дневной" : "смена №1"; },' +
            '_STATUS_CODES: ' + JSON.stringify([
                { code: 'Д', short: 'день 12ч', name: 'День, плановая 12-часовая смена', color: '#FFE082' },
                { code: 'ОТ', short: 'отпуск', name: 'Отпуск, ежегодный основной оплачиваемый отпуск', color: '#ECEFF1' },
                { code: '', short: 'выходной', name: 'Выходной, плановый выходной день', color: '#EEF0F2' }]) + ',' +
            '_TRAININGS: [{ "тип": "инструктаж", "тема": "Повторный инструктаж по охране труда",' +
            '  "дата_начала": "2026-09-02", "дата_окончания": "2026-09-02", "таб_номер": "017" }],' +
            '_EMPLOYEES: [{ "ФИО": "Иванов Иван Иванович", "таб_номер": "017" },' +
                        '{ "ФИО": "Сидоров Сидор Сидорович", "таб_номер": "031" }],' +
            '_trainingCodeOf: function(t) { return t === "инструктаж" ? "И" : ""; },' +
            '_instrShortOf: function(t) { return "Повторный инструктаж"; },' +
            '_calDayOff: function(day) { return day % 7 === 0 || day % 7 === 6; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { return []; },' +
            '_statusMeta: function(code) {' +
            '    var m = { "Д": { code: "Д", color: "#FFE082" },' +
            '              "ОТ": { code: "ОТ", color: "#ECEFF1" },' +
            '              "И": { code: "И", color: "#B3E5FC" } };' +
            '    return m[code] || {};' +
            '},' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '});')({ dayInfo: function() { return null; } });
    }

    const EMPS = [
        { 'ФИО': 'Иванов Иван Иванович', 'таб_номер': '017' },
        { 'ФИО': 'Сидоров Сидор Сидорович', 'таб_номер': '031' }
    ];
    const AGG = { byTab: { '017': { work: 21, overDays: 3 },
                           '031': { work: 19, overDays: 0 } } };

    test('VM: каждый код — ОДНА ячейка в D, правее D пусто', () => {
        const host = tabelHost();
        const m = host._printModel(EMPS, AGG);
        const rows = host._wsTabelRows(m, {});
        let hdrIdx = -1;
        for (let i = 0; i < rows.length; i++) {
            if (rows[i][0] && String(rows[i][0].v).indexOf('Мероприятия · ') === 0) {
                hdrIdx = i; break;
            }
        }
        assertTrue(hdrIdx !== -1, 'заголовок блока найден');
        let codeCells = 0;
        for (let i = hdrIdx + 1; i < rows.length; i++) {
            const r = rows[i];
            assertTrue(r.length <= 4,
                'строка блока — не шире 4 колонок (A–D), было: ' + r.length);
            for (let c = 4; c < r.length; c++) {
                assertTrue(!r[c], 'правее D (колонка ' + (c + 1) + ') ячеек нет');
            }
            if (r[3] && r[3].v) codeCells++;
        }
        assertEqual(codeCells, m.codes.length,
            'по одной строке на КАЖДЫЙ код — один столбец D (' +
            m.codes.length + ' кодов)');
    });

    test('SRC: _wsTabelRows — коды только в D (индекс 3)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_wsTabelRows'));
        assertTrue(b.indexOf('{ v: codeLines[b], s: 7 }') !== -1,
            'строка кода — одна ячейка (style 7) в колонке D');
        assertTrue(b.indexOf('Коды:') !== -1,
            'заголовок «Коды:» — в D (Task 439)');
    });
});

// ============================================================
// 5. SW — версия кэша
// ============================================================
describe('Task 441 — SW: версия kipia-test-v665', () => {
    test('CACHE_VERSION = kipia-test-v665, прежней v664 нет', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v665'") !== -1,
            'CACHE_VERSION = kipia-test-v665');
        assertFalse(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v664'") !== -1,
            'v664 как активная версия больше не существует');
    });
});
