// ============================================================
// Task 432 — заявка (kip8test): «в печати графика работы, строки
// столбика мероприятий должны растягиваться вправо до конца
// листа, и если места не хватит, только тогда переноситься на
// следующую строку. В блоке инструктажей, кнопку редактировать
// размести справа от кнопки удалить, строго на одном уровне.
// Так же в блоках карт работников убери фон зебры строк в виде
// рамки, и размести строки на всю ширину в блоке, зеброй без
// рамок и отступов, так же расстояние между текстами и
// кнопками, по вертикали, в этих блоках сделай 5px».
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   КЛИЕНТ (SRC):
//   1) печать — ОБТЕКАНИЕ вместо flex-ряда: .wsp-bottom —
//      display: flow-root (сноска ниже флоата), .wsp-legend —
//      float: right + margin 0 0 5px 10px (зазор строк→коды
//      10px Task 431/375 жив у флоата), .wsp-mev — БЕЗ flex:
//      строки занимают всю ширину листа (рядом с кодами — до их
//      кромки минус 10px, ниже кодов — до конца листа);
//   2) печать — ПОРЯДОК DOM: столбик кодов строится ПЕРВЫМ в
//      обёртке wsp-bottom (флоат обязан предшествовать
//      обтекаемому тексту), мероприятия — вторым, сноска
//      wsp-foot — после закрытия обёртки;
//   3) кнопки строки инструктажа: .ws-act-row — горизонтальный
//      ряд «✕ ✎» ВНУТРИ колонки .ws-act-col (✎ СПРАВА от ✕,
//      строго на одном уровне; порядок в разметке: iActDel +
//      iActEdit), галочка — НАД рядом (iChk первым); зазоры
//      колонки и ряда — 5px; попап ячейки — прежний порядок
//      ✎/✕ (iActEdit + iActDel, без колонки);
//   4) блоки карт: строки-зебры — ВО ВСЮ ширину окна (margin:
//      0 -16px гасит боковой паддинг панели) у трёх типов строк
//      (.ws-popup-row / .ws-emp-field / .ws-ppe-item),
//      скругление «пилюли» СНЯТО (border-radius: 0), вертикаль-
//      ный паддинг 5px, боковой 16px (текст — на линии паддинга
//      панели); пустые сообщения .ws-emp-empty — 5px 0; попап
//      шахматки (#wsCellPopup / базовый .ws-popup-row) НЕ тронут;
//   VM (клиент):
//   5) _renderWorkerCard asBlocks: в строке инструктажа ✎ ПОСЛЕ
//      ✕ (внутри .ws-act-row), ряд — внутри колонки, галочка —
//      выше ряда; зритель — колонка с одной галочкой состояния;
//      запись без id — без колонки; попап — без галочки/колонки.
//   SW: kipia-test-v658 (главный), v659 — прежней нет.
// ============================================================

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

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

function ruleBlock(sel) {
    const i = INDEX_SRC.indexOf(sel);
    if (i === -1) return '';
    return INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
}

function mockDoc(els) {
    return { getElementById: function(id) { return els[id] || null; } };
}

// ============================================================
// 1. SRC — печать: обтекание (строки до конца листа)
// ============================================================
describe('Task 432 — SRC: печать (обтекание кодов, строки до конца листа)', () => {

    test('.wsp-bottom — flow-root: флоат contained, сноска ниже кодов', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r !== '', 'правило обёртки есть');
        assertTrue(r.indexOf('display: flow-root') !== -1,
            'flow-root — обёртка содержит флоат (сноска wsp-foot ниже кодов)');
        assertFalse(r.indexOf('display: flex') !== -1,
            'flex-ряда больше нет (Task 432: обтекание)');
        assertFalse(r.indexOf('gap:') !== -1,
            'gap снят — зазор теперь у флоата (margin-left)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы не тронут (Task 364)');
    });

    test('.wsp-legend — float: right у правого верхнего угла ряда', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend {');
        assertTrue(r !== '', 'правило кодов есть');
        assertTrue(r.indexOf('float: right') !== -1,
            'столбик кодов ПЛАВАЕТ у правого края листа');
        assertTrue(r.indexOf('margin: 0 0 5px 10px') !== -1,
            'зазор от строк мероприятий 10px (Task 431/375) + 5px снизу');
        assertTrue(r.indexOf('flex: 0 0 auto') === -1,
            'flex-колонка снята (Task 432: флоат)');
        assertTrue(r.indexOf('max-width: 44%') !== -1,
            'кап ширины кодов сохранён (Task 364)');
    });

    test('.wsp-mev — БЕЗ flex: строки на всю ширину листа', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-mev {');
        assertTrue(r !== '', 'правило мероприятий есть');
        assertFalse(r.indexOf('flex:') !== -1,
            'flex снят: блок на всю ширину, строки ТЕКУТ вокруг кодов ' +
            'и ниже их растягиваются до конца листа');
        assertFalse(r.indexOf('min-width: 0') !== -1,
            'min-width снят (был нужен flex-усадке Task 431)');
    });

    test('JS: столбик кодов — ПЕРВЫМ в DOM обёртки (флоат)', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        assertTrue(iOpen !== -1 && iLegend !== -1 && iMev !== -1,
            'обёртка, коды и мероприятия строятся');
        assertTrue(iOpen < iLegend && iLegend < iMev,
            'порядок: обёртка → КОДЫ (флоат обязан предшествовать ' +
            'обтекаемому тексту) → мероприятия');
    });

    test('JS: закрытие mev и обёртки — два оператора перед сноской', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        const iClose1 = b.indexOf("html += '</div>';", b.indexOf('<div class="wsp-mev">'));
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iFoot !== -1 && iClose1 !== -1 && iClose2 !== -1,
            'закрытия мероприятий и обёртки строятся');
        assertTrue(iClose2 - iClose1 < 200,
            'два последовательных оператора закрытия (mev + обёртка)');
        assertTrue(iClose2 < iFoot, 'сноска — ПОСЛЕ закрытия обёртки');
    });
});

// ============================================================
// 2. SRC — кнопки: ✎ справа от ✕, строго на одном уровне
// ============================================================
describe('Task 432 — SRC: ✎ справа от ✕ (блок инструктажей)', () => {

    test('.ws-act-col — колонка: галочка НАД, зазор 5px', () => {
        const r = ruleBlock('.ws-act-col {');
        assertTrue(r !== '', 'правило колонки есть');
        assertTrue(r.indexOf('flex-direction: column') !== -1,
            'вертикальная колонка (галочка над рядом кнопок)');
        assertTrue(r.indexOf('align-items: flex-start') !== -1,
            'галочка — точно НАД ✕ (не над серединой пары ✕✎)');
        assertTrue(r.indexOf('gap: 5px') !== -1,
            'вертикальный зазор галочка↔ряд — 5px (заявка)');
    });

    test('.ws-act-row — горизонтальный ряд «✕ ✎», 5px', () => {
        const r = ruleBlock('.ws-act-row {');
        assertTrue(r !== '', 'правило ряда есть');
        assertTrue(r.indexOf('display: inline-flex') !== -1,
            '✕ и ✎ — в одном горизонтальном ряду');
        assertTrue(r.indexOf('align-items: center') !== -1,
            '✎ и ✕ — СТРОГО на одном уровне (общий центр)');
        assertTrue(r.indexOf('gap: 5px') !== -1, 'зазор между ✕ и ✎ — 5px');
        const m = ruleBlock('.ws-act-col .ws-popup-act {');
        assertTrue(m.indexOf('margin-left: 0') !== -1,
            'авто-сдвиг кнопок внутри колонки снят');
    });

    test('разметка b5: ряд ✕✎ внутри колонки, галочка — первой', () => {
        const start = INDEX_SRC.indexOf('нет инструктажей и проверок знаний за год');
        const end = INDEX_SRC.indexOf('ws-emp-addins', start);
        const FLAT = INDEX_SRC.slice(start, end);
        assertTrue(FLAT.indexOf(
            "'<span class=\"ws-act-row\">' + iActDel + iActEdit + '</span>'") !== -1,
            'ряд .ws-act-row: ✕ ПЕРВЫМ, ✎ ПОСЛЕ (✎ — справа от ✕)');
        assertTrue(FLAT.indexOf(
            "'<span class=\"ws-act-col\">' + iChk + iActRow + '</span>'") !== -1,
            'колонка: галочка ПЕРВОЙ (НАД), ряд ✕✎ — ПОД ней');
        assertTrue(FLAT.indexOf('iRowEnd = iActEdit + iActDel;') !== -1,
            'попап (!asBlocks) — прежний порядок ✎/✕, без колонки');
        assertTrue(FLAT.indexOf('iLateTag + iRowEnd') !== -1,
            'порядок строки: бейдж → колонка кнопок в конце');
    });
});

// ============================================================
// 3. SRC — зебра блоков карт: во всю ширину, без рамок, 5px
// ============================================================
describe('Task 432 — SRC: зебра карт во всю ширину + 5px', () => {

    test('.ws-popup-row карты — во всю ширину окна, паддинг 5px', () => {
        const r = ruleBlock('.ws-wcard .ws-popup-row {');
        assertTrue(r !== '', 'правило строк карты есть');
        assertTrue(r.indexOf('margin: 0 -16px') !== -1,
            'отрицательные поля гасят паддинг панели — полоса зебры ' +
            'ОТ КРАЯ ДО КРАЯ окна');
        assertTrue(r.indexOf('padding: 5px 16px') !== -1,
            'вертикальный ритм 5px (заявка), боковой — на линии панели');
    });

    test('.ws-emp-field и .ws-ppe-item — те же поля/паддинги', () => {
        const f = ruleBlock('.ws-wcard .ws-emp-field {');
        assertTrue(f.indexOf('margin: 0 -16px') !== -1 &&
                   f.indexOf('padding: 5px 16px') !== -1,
            'поля профиля — во всю ширину, 5px');
        const p = ruleBlock('.ws-wcard .ws-ppe-item {');
        assertTrue(p.indexOf('margin: 0 -16px') !== -1 &&
                   p.indexOf('padding: 5px 16px') !== -1,
            'СИЗ — во всю ширину, 5px');
    });

    test('скругление «пилюли» СНЯТО — зебра без рамок', () => {
        const i = INDEX_SRC.indexOf('.ws-wcard .ws-emp-field,\n' +
            '    .ws-wcard .ws-popup-row,');
        assertTrue(i !== -1, 'блок трёх селекторов есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        assertTrue(r.indexOf('border-radius: 0') !== -1,
            'border-radius: 0 — полоса без скругления (не «рамка»)');
    });

    test('пустые сообщения — вровень с текстом строк (5px 0)', () => {
        const r = ruleBlock('.ws-wcard .ws-emp-empty {');
        assertTrue(r.indexOf('padding: 5px 0') !== -1,
            'отступ 5px 0 — текст на линии паддинга панели');
    });

    test('попап шахматки НЕ тронут (пилюли и паддинги живы)', () => {
        const base = ruleBlock('.ws-popup-row {');
        assertTrue(base.indexOf('padding: 7px 10px') !== -1,
            'базовый паддинг строк попапа жив');
        assertTrue(base.indexOf('border-radius: 6px') !== -1,
            'скругление строк попапа живо (зебра снята ТОЛЬКО в картах)');
    });
});

// ============================================================
// 4. VM — рендер строки инструктажа: порядок кнопок
// ============================================================
describe('Task 432 — VM: строка инструктажа (✎ справа от ✕)', () => {

    const YEAR = new Date().getFullYear();

    function d(day) {
        return YEAR + '-09-' + (day < 10 ? '0' + day : day);
    }

    const EMP = [
      { 'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
        'должность': 'Слесарь КИПиА', 'группа_допуска': 'IV',
        'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0 }
    ];
    const INS = [
      { id: 51, 'таб_номер': '017', 'тип': 'инструктаж',
        'тема': 'Повторный инструктаж по ОТ', 'дата_начала': d(2),
        'дата_окончания': d(2), 'длительность_дней': 1,
        'выполнение': 0, 'просрочен': 0 },
      { id: 52, 'таб_номер': '017', 'тип': 'проверка_знаний',
        'тема': 'Электроустановки до 1000 В', 'дата_начала': d(10),
        'дата_окончания': d(10), 'длительность_дней': 1,
        'выполнение': 0, 'просрочен': 0 }
    ];

    function cardHost(opts) {
        return new Function('document', 'return ({' +
            methodText(INDEX_SRC, '_renderWorkerCard') + ',\n' +
            methodText(INDEX_SRC, '_wtabYearOf') + ',\n' +
            methodText(INDEX_SRC, '_wtabYearMin') + ',\n' +
            methodText(INDEX_SRC, '_wtabYearNav') + ',\n' +
            methodText(INDEX_SRC, '_wtabYearRecords') + ',\n' +
            methodText(INDEX_SRC, '_renderInstrSection') + ',\n' +
            methodText(INDEX_SRC, '_normInstrKey') + ',\n' +
            methodText(INDEX_SRC, '_normInstrKind') + ',\n' +
            methodText(INDEX_SRC, '_addMonthsIso') + ',\n' +
            methodText(INDEX_SRC, '_isoDate') + ',\n' +
            methodText(INDEX_SRC, '_fmtPeriodRu') + ',\n' +
            methodText(INDEX_SRC, '_isInstrType') + ',\n' +
            methodText(INDEX_SRC, '_instrShortOf') + ',\n' +
            '_canEdit: ' + (opts.edit ? 'true' : 'false') + ',' +
            '_year: ' + YEAR + ', _month: 9,' +
            '_EMPLOYEES: ' + JSON.stringify(EMP) + ',' +
            '_VACATIONS: [],' +
            '_TRAININGS: [],' +
            '_PPE: [],' +
            '_INSTR_LIST: [],' +
            '_INSTR_ALL: ' + JSON.stringify(opts.instrAll || INS) + ',' +
            '_fmtDateRu: function(x) { var p = String(x).split("-");' +
            '  return p.length === 3 ? p[2] + "." + p[1] + "." + p[0] : String(x); },' +
            '_esc: function(s) { return String(s); },' +
            '_escAttr: function(s) { return String(s); },' +
            '_vacDaysInYear: function(v, y) { return 0; },' +
            '_vacNetDaysInYear: function(v, y) { return 0; },' +
            '_plural: function(n, f) { return f[2]; },' +
            '_trainingCodeOf: function(t) { return t === "проверка_знаний" ? "ПЗ" : "И"; },' +
            '_statusMeta: function(c) { return { code: c, color: "#123456", name: c }; }' +
            '});')(mockDoc({}));
    }

    function rowOf(html, topic) {
        const i = html.indexOf(topic);
        if (i === -1) return null;
        const start = html.lastIndexOf('<div class="ws-popup-row', i);
        return html.slice(start, html.indexOf('</div>', i) + 6);
    }

    test('редактор: ✎ — ВНУТРИ .ws-act-row, ПОСЛЕ ✕ (справа)', () => {
        const host = cardHost({ edit: true });
        const html = host._renderWorkerCard('017', true, true).join('');
        const row = rowOf(html, 'Повторный инструктаж по ОТ');
        assertTrue(row !== null, 'строка записи найдена');
        const iCol = row.indexOf('<span class="ws-act-col">');
        const iRow = row.indexOf('<span class="ws-act-row">');
        assertTrue(iCol !== -1, 'колонка .ws-act-col в строке');
        assertTrue(iRow !== -1 && iRow > iCol, 'ряд .ws-act-row ВНУТРИ колонки');
        const iChk = row.indexOf('ws-done-chk', iCol);
        assertTrue(iChk !== -1 && iChk < iRow,
            'галочка — ПЕРВОЙ в колонке (НАД рядом ✕✎)');
        const iDel = row.indexOf('ws-popup-act-del', iRow);
        const iEdit = row.indexOf('ws-popup-act"', iRow);
        assertTrue(iDel !== -1 && iEdit !== -1 && iDel < iEdit,
            'в ряду ✕ ПЕРВЫМ, ✎ ПОСЛЕ — ✎ справа от ✕');
        // колонка замыкает строку: ДО неё кнопок нет (✎ больше
        // не ведёт строку горизонтально слева от колонки)
        assertTrue(row.slice(0, iCol).indexOf('ws-popup-act') === -1,
            'кнопок до колонки нет — колонка с ✕✎ в КОНЦЕ строки');
    });

    test('редактор: вторая запись — тот же порядок кнопок', () => {
        const host = cardHost({ edit: true });
        const html = host._renderWorkerCard('017', true, true).join('');
        const row = rowOf(html, 'Электроустановки до 1000 В');
        const iRow = row.indexOf('<span class="ws-act-row">');
        const iDel = row.indexOf('ws-popup-act-del', iRow);
        const iEdit = row.indexOf('ws-popup-act"', iRow);
        assertTrue(iRow !== -1 && iDel !== -1 && iEdit !== -1 && iDel < iEdit,
            'у каждой записи: ряд ✕✎, ✎ — справа');
    });

    test('зритель: колонка с одной галочкой состояния (выполнено)', () => {
        const done = JSON.parse(JSON.stringify(INS));
        done[0]['выполнение'] = 1;
        const host = cardHost({ edit: false, instrAll: done });
        const html = host._renderWorkerCard('017', false, true).join('');
        const row = rowOf(html, 'Повторный инструктаж по ОТ');
        const col = row.indexOf('<span class="ws-act-col">');
        assertTrue(col !== -1, 'колонка есть и у зрителя');
        const colEnd = row.indexOf('</span>', row.indexOf('✓', col));
        const colText = row.slice(col, colEnd);
        assertTrue(colText.indexOf('ws-done-on') !== -1 &&
                   colText.indexOf('ws-done-ro') !== -1,
            'некликабельная галочка состояния внутри колонки');
        assertTrue(colText.indexOf('ws-act-row') === -1,
            'ряда кнопок у зрителя нет (нет прав)');
    });

    test('запись без id — без колонки (нет кнопок)', () => {
        const noId = JSON.parse(JSON.stringify(INS));
        delete noId[0].id;
        const host = cardHost({ edit: true, instrAll: noId });
        const html = host._renderWorkerCard('017', true, true).join('');
        const row = rowOf(html, 'Повторный инструктаж по ОТ');
        assertTrue(row !== null, 'строка без id рендерится');
        assertTrue(row.indexOf('ws-act-col') === -1,
            'колонки нет — нет ни галочки, ни кнопок');
    });

    test('попап (!asBlocks): прежний вид — БЕЗ галочки, ряда и колонки', () => {
        const host = cardHost({ edit: true });
        const html = host._renderWorkerCard('017', true, false);
        assertTrue(html.indexOf('ws-done-chk') === -1,
            'галочка — только в карточке (Task 418, регресс)');
        assertTrue(html.indexOf('ws-act-col') === -1 &&
                   html.indexOf('ws-act-row') === -1,
            'колонка и ряд — только в карточке');
        assertTrue(html.indexOf('ws-popup-act') !== -1,
            'кнопки ✎/✕ в попапе живы (горизонтальный порядок)');
    });
});

// ============================================================
// 5. SW — версия
// ============================================================
describe('Task 432 — SW версия', () => {
    test('v658 (главный), v659 — прежней нет', () => {
        assertTrue(SW_SRC.indexOf('kipia-test-v658') !== -1,
            'SW кэш kipia-test-v658');
        assertFalse(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v659'") !== -1,
            'v659 ещё не существует (guard следующего бампа)');
    });
});
