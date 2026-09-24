// ============================================================
// Task 404 — заявка: «В картах работников блок СИЗ размести слева
// от блока мероприятия. По итогу в верхней части должно быть три
// блока, слева на право, блок профиля (под ним блок отпуска),
// блок СИЗ и блок мероприятия, то есть нужно подогнать размеры
// блоков, что бы они поместились в одной линии. И кнопки
// "редактировать" в блоках отпуска и мероприятия выравнить
// разместить рядом с кнопками "удалить", по примеру как в блоке
// СИЗ. В разделе Табель учёта рабочего времени, в окне мероприятий
// убери информацию по отпускам».
//
// 1) КАРТОЧКА (страница «Работники»): ТРИ колонки — 1-я: профиль
//    (+отпуска под ним), 2-я: СИЗ, 3-я: мероприятия; три верхних
//    блока в ОДНУ ЛИНИЮ (равные доли flex: 1 1 0); мобайл — стек
//    профиль → отпуска → СИЗ → мероприятия.
// 2) КНОПКИ ✎/✕: в блоках отпуска и мероприятия — РЯДОМ, у правого
//    края (как в блоке СИЗ): контент строки растянут (flex: 1 —
//    .ws-emp-v / .ws-popup-name, как .ws-ppe-body), auto-маржины
//    кнопок больше не делят свободное место.
// 3) ОКНО МЕРОПРИЯТИЙ (тулбар): секция «Отпуска» УДАЛЕНА (сборка +
//    рендер + CSS-плашка/точка) — остались «Мероприятия» и «СИЗ».
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

function stripComments(s) {
    return String(s).replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
}

function mockDoc(els) {
    return { getElementById: function(id) { return els[id] || null; } };
}

function ruleBlock(name) {
    const i = INDEX_SRC.indexOf(name);
    if (i === -1) return null;
    return INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
}

// ============================================================
// 1. SRC — раскладка: ТРИ колонки
// ============================================================
describe('Task 404 — SRC: карточка — три блока в одну линию', () => {

    test('_renderWorkerCardPanels: СИЗ — вторая колонка, мероприятия — третья', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf('var colMain = \'\', colPpe = \'\', colTr = \'\';') !== -1,
            'три сборщика колонок: colMain / colPpe / colTr');
        assertTrue(fn.indexOf('if (bi < 2) colMain += panel;') !== -1,
            'блоки 1–2 (профиль + отпуска) — в ПЕРВУЮ колонку');
        assertTrue(fn.indexOf('else if (bi === 3) colPpe += panel;') !== -1,
            'блок 4 (СИЗ) — во ВТОРУЮ колонку (СЛЕВА от мероприятий)');
        assertTrue(fn.indexOf('else colTr += panel;') !== -1,
            'блок 3 (мероприятия) — в ТРЕТЬЮ колонку');
        assertTrue(fn.indexOf("'<div class=\"ws-wcol\">' + colMain + '</div>' +") !== -1 &&
                   fn.indexOf("'<div class=\"ws-wcol ws-wcol-ppe\">' + colPpe + '</div>' +") !== -1 &&
                   fn.indexOf("'<div class=\"ws-wcol ws-wcol-tr\">' + colTr + '</div>'") !== -1,
            'возврат: main → СИЗ (.ws-wcol-ppe) → мероприятия (.ws-wcol-tr)');
    });

    test('CSS: три РАВНЫЕ колонки — блоки помещаются в одной линии', () => {
        const m = INDEX_SRC.match(/@media \(min-width: 1024px\) \{\s*\.ws-wgrid2 \{[^}]*?\}\s*\.ws-wgrid2 \.ws-wcol \{[^}]*?\}\s*\}/);
        assertTrue(m !== null, 'блок медиаправил жив');
        assertTrue(m[0].indexOf('display: flex;') !== -1 &&
                   m[0].indexOf('flex-wrap: nowrap;') !== -1,
            'flex БЕЗ переноса — колонки строго в одну линию');
        assertTrue(m[0].indexOf('flex: 1 1 0;') !== -1,
            'равные доли 1 1 0 — три блока гарантированно помещаются');
        assertTrue(m[0].indexOf('gap: 12px;') !== -1,
            'зазор между колонками 12px');
        assertTrue(m[0].indexOf('align-items: flex-start;') !== -1,
            'колонки не тянутся по высоте друг друга');
    });

    test('мобайл ≤1023px — стек колонок без раскладки', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-wgrid2 .ws-wcol { margin-bottom: 12px; }') !== -1,
            'зазор между колонками в стеке жив');
        assertTrue(INDEX_SRC.indexOf('.ws-wgrid2 .ws-wcol:last-child { margin-bottom: 0; }') !== -1,
            'последняя колонка без зазора');
    });
});

// ============================================================
// 2. SRC — кнопки ✎/✕ рядом (контент строк растянут)
// ============================================================
describe('Task 404 — SRC: кнопки ✎/✕ рядом (как в блоке СИЗ)', () => {

    test('.ws-emp-v растянут — кнопки отпусков прижаты вправо', () => {
        const r = ruleBlock('.ws-emp-field .ws-emp-v {');
        assertTrue(r !== null, 'правило живо');
        assertTrue(r.indexOf('flex: 1;') !== -1 && r.indexOf('min-width: 0;') !== -1,
            'значение строки растянуто (как тело строки СИЗ .ws-ppe-body)');
        assertTrue(r.indexOf('text-overflow: ellipsis;') !== -1,
            'эллипсис длинных значений сохранён');
    });

    test('.ws-popup-name растянут — кнопки мероприятий прижаты вправо', () => {
        const r = ruleBlock('.ws-popup-name {');
        assertTrue(r !== null, 'правило живо');
        assertTrue(r.indexOf('flex: 1;') !== -1 && r.indexOf('min-width: 0;') !== -1,
            'имя строки растянуто — auto-маржины кнопок не разнесены');
    });

    test('образец СИЗ жив: .ws-ppe-body flex: 1 (тело строки СИЗ)', () => {
        const r = ruleBlock('.ws-ppe-item .ws-ppe-body {');
        assertTrue(r !== null && r.indexOf('flex: 1;') !== -1,
            'тело строки СИЗ растянуто — тот же приём у отпусков/мероприятий');
    });
});

// ============================================================
// 3. SRC — окно мероприятий: отпуска УДАЛЕНЫ
// ============================================================
describe('Task 404 — SRC: окно мероприятий — без информации по отпускам', () => {

    test('_renderMonthEventsPanel: сборки и секции отпусков НЕТ', () => {
        const m = methodText(INDEX_SRC, '_renderMonthEventsPanel');
        assertFalse(m.indexOf('vacList') !== -1,
            'список отпусков не собирается');
        assertFalse(m.indexOf('Отпуска · ') !== -1,
            'заголовка секции «Отпуска» нет');
        assertFalse(m.indexOf("'Отпуск · '") !== -1,
            'строк отпусков нет');
        assertFalse(m.indexOf('ws-ep-dot-vac') !== -1,
            'точек отпусков нет');
        assertTrue(m.indexOf('ppeList') !== -1 && m.indexOf('СИЗ · ') !== -1,
            'секция СИЗ жива');
        assertTrue(m.indexOf('Мероприятия · ') !== -1,
            'секция «Мероприятия» жива');
    });

    test('CSS: плашка/точка отпусков удалены, СИЗ — живы', () => {
        assertTrue(ruleBlock('.ws-ep-cap-vac {') === null,
            'плашка «Отпуска» удалена');
        assertFalse(INDEX_SRC.indexOf('.ws-ep-dot-vac') !== -1,
            'точка отпусков удалена (класс-житель исчез)');
        assertTrue(ruleBlock('.ws-ep-cap-ppe {') !== null,
            'плашка «СИЗ» жива');
        assertTrue(INDEX_SRC.indexOf('.ws-ep-dot-ppe { background: #f0a830; }') !== -1,
            'точка СИЗ — янтарная');
    });
});

// ============================================================
// 4. VM — панели: три колонки; кнопки в блоках
// ============================================================
describe('Task 404 — VM: панели и кнопки карточки', () => {

    function cardHost() {
        const EMP = [
            { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
              'смена': '', 'должность': 'Слесарь КИПиА 5 разряд', 'комментарий': '',
              'группа_допуска': 'IV', 'дата_приёма': '2024-03-15' },
        ];
        return new Function('document', 'return ({' +
            methodText(INDEX_SRC, '_renderWorkerCard') + ',\n' +
            methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\n' +
            '_canEdit: true, _year: 2026, _month: 8,' +
            '_EMPLOYEES: ' + JSON.stringify(EMP) + ',' +
            '_VACATIONS: ' + JSON.stringify([{
                id: 7, 'таб_номер': '2706', 'часть': 1,
                'дата_начала': '2026-07-01', 'дата_окончания': '2026-07-14',
                'комментарий': '' }]) + ',' +
            '_TRAININGS: ' + JSON.stringify([{
                id: 5, 'таб_номер': '2706', 'тип': 'Инструктаж', 'тема': 'ОТ',
                'дата_начала': '2026-02-10', 'дата_окончания': '2026-02-10' }]) + ',' +
            '_PPE: ' + JSON.stringify([{
                id: 3, 'таб_номер': '2706', наименование: 'Каска защитная',
                дата_выдачи: '2026-09-17', срок_годности: '1 год',
                дата_окончания: '2027-09-17', примечание: '' }]) + ',' +
            '_fmtDateRu: function(d) { d = String(d);' +
            '  var p = d.split("-"); return p.length === 3 ?' +
            '  p[2] + "." + p[1] + "." + p[0] : d; },' +
            '_esc: function(s) { return String(s); },' +
            '_escAttr: function(s) { return String(s); },' +
            '_trainingCodeOf: function(t) { return "И"; },' +
            '_statusMeta: function(c) { return {}; },' +
            '_vacDaysInYear: function(v, y) { return 14; },' +
            '_vacNetDaysInYear: function(v, y) { return 14; },' +
            '_plural: function(n, f) { return f[2]; }' +
            '});')(mockDoc({}));
    }

    test('три колонки: 2 окна | 1 (СИЗ) | 1 (мероприятия); порядок DOM', () => {
        const host = cardHost();
        const html = host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iP = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        const iT = html.indexOf('<div class="ws-wcol ws-wcol-tr">');
        assertTrue(iL !== -1 && iP !== -1 && iT !== -1 && iL < iP && iP < iT,
            'ТРИ колонки: main → СИЗ → мероприятия');
        const mainPart = html.slice(iL, iP);
        const ppePart = html.slice(iP, iT);
        const trPart = html.slice(iT);
        assertEqual((mainPart.match(/class="ws-wcard"/g) || []).length, 2,
            'колонка 1 — профиль + отпуска');
        assertEqual((ppePart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 2 — СИЗ');
        assertEqual((trPart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 3 — мероприятия');
        // порядок DOM = «слева на право» из заявки
        const iProf = mainPart.indexOf('Галкин Д. Н.');
        const iVac = mainPart.indexOf('Отпуска · 2026');
        const iPz = ppePart.indexOf('СИЗ · средства индивидуальной защиты');
        const iTr = trPart.indexOf('Мероприятия · 2026');
        assertTrue(iProf !== -1 && iVac !== -1 && iPz !== -1 && iTr !== -1,
            'все блоки на месте');
        assertTrue(iProf < iVac, 'под профилем — отпуска (внутри 1-й колонки)');
        assertTrue(iL + iProf < iP + iPz && iP + iPz < iT + iTr,
            'визуальный порядок: профиль → СИЗ → мероприятия');
    });

    test('кнопки ✎ и ✕ — в каждом блоке с записями (отпуска/мероприятия/СИЗ)', () => {
        const host = cardHost();
        const blocks = host._renderWorkerCard('2706', true, true);
        assertEqual(blocks.length, 4, 'четыре блока');
        // отпуска: ✎ перед ✕, оба в блоке
        const iEv = blocks[1].indexOf('WorkSchedule.editVacation(7)');
        const iDel = blocks[1].indexOf('WorkSchedule.deleteVacation(7)');
        assertTrue(iEv !== -1 && iDel !== -1 && iEv < iDel,
            'отпуск: ✎ (правка) и ✕ (удаление) — оба, ✎ первым');
        // мероприятия
        const iEt = blocks[2].indexOf('WorkSchedule.editTraining(5)');
        const iDt = blocks[2].indexOf('WorkSchedule.deleteTraining(5)');
        assertTrue(iEt !== -1 && iDt !== -1 && iEt < iDt,
            'мероприятие: ✎ и ✕ — оба, ✎ первым');
        // СИЗ — образец
        const iEp = blocks[3].indexOf('WorkSchedule.editPpe(3)');
        const iDp = blocks[3].indexOf('WorkSchedule.deletePpe(3)');
        assertTrue(iEp !== -1 && iDp !== -1 && iEp < iDp,
            'СИЗ: ✎ и ✕ — оба (образец)');
    });

    test('зритель (withEdit=false) — кнопок правки нет ни в одном блоке', () => {
        const EMP = [
            { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
              'смена': '', 'должность': 'Слесарь КИПиА', 'комментарий': '' },
        ];
        const host = new Function('document', 'return ({' +
            methodText(INDEX_SRC, '_renderWorkerCard') + ',\n' +
            '_canEdit: false, _year: 2026, _month: 8,' +
            '_EMPLOYEES: ' + JSON.stringify(EMP) + ',' +
            '_VACATIONS: ' + JSON.stringify([{
                id: 7, 'таб_номер': '2706', 'часть': 1,
                'дата_начала': '2026-07-01', 'дата_окончания': '2026-07-14' }]) + ',' +
            '_TRAININGS: ' + JSON.stringify([{
                id: 5, 'таб_номер': '2706', 'тип': 'Инструктаж', 'тема': 'ОТ',
                'дата_начала': '2026-02-10', 'дата_окончания': '2026-02-10' }]) + ',' +
            '_PPE: [],' +
            '_fmtDateRu: function(d) { d = String(d);' +
            '  var p = d.split("-"); return p.length === 3 ?' +
            '  p[2] + "." + p[1] + "." + p[0] : d; },' +
            '_esc: function(s) { return String(s); },' +
            '_escAttr: function(s) { return String(s); },' +
            '_trainingCodeOf: function(t) { return "И"; },' +
            '_statusMeta: function(c) { return {}; },' +
            '_vacDaysInYear: function(v, y) { return 14; },' +
            '_vacNetDaysInYear: function(v, y) { return 14; },' +
            '_plural: function(n, f) { return f[2]; }' +
            '});')(mockDoc({}));
        const blocks = host._renderWorkerCard('2706', false, true);
        blocks.forEach(function(b) {
            assertTrue(b.indexOf('ws-popup-act') === -1,
                'у зрителя кнопок ✎/✕ нет');
        });
    });
});

// ============================================================
// 5. VM — окно мероприятий: отпуска НЕ показываются
// ============================================================
describe('Task 404 — VM: окно мероприятий — отпуска не показываются', () => {

    function panelHost(opts) {
        const el = { innerHTML: '', hidden: true };
        const document = { getElementById: function(id) {
            return id === 'wsEventsPanel' ? el : null;
        }};
        const texts = ['_renderMonthEventsPanel', '_trainingCodeOf', '_statusMeta']
            .map(n => methodText(INDEX_SRC, n));
        const make = new Function('localStorage', 'document', 'confirm',
                                  'KipToast', 'kipConfirm',
            'return ({' + texts.join(',\n') + ',\n' +
            '_year: ' + (opts.year || 2026) + ', _month: ' + (opts.month || 9) + ',' +
            '_selDay: null,' +
            '_TRAININGS: ' + JSON.stringify(opts.trainings || []) + ',' +
            '_VACATIONS: ' + JSON.stringify(opts.vacations || []) + ',' +
            '_PPE: ' + JSON.stringify(opts.ppe || []) + ',' +
            '_EMPLOYEES: ' + JSON.stringify(opts.employees || [
                { 'таб_номер': '0871', 'ФИО': 'Иванов Иван Иванович' }]) + ',' +
            '_STATUS_CODES: [],' +
            '_esc: function(s){ return String(s == null ? "" : s); },' +
            '_escAttr: function(s){ return String(s == null ? "" : s); },' +
            '_isoDate: function(dt){ var m=(""+(dt.getMonth()+1)).padStart(2,"0"); var d=(""+dt.getDate()).padStart(2,"0"); return dt.getFullYear()+"-"+m+"-"+d; }, _barExpSync: function() {},' +
            '});');
        const ctx = make(null, document, null, null, null);
        ctx._renderMonthEventsPanel();
        return el;
    }

    test('данные отпусков есть — секции «Отпуска» НЕТ; СИЗ и мероприятия живы', () => {
        const el = panelHost({
            month: 9,
            trainings: [{ 'таб_номер': '0871', 'тип': 'инструктаж',
                          'тема': 'Повторный', 'дата_начала': '2026-09-05',
                          'дата_окончания': '2026-09-05' }],
            vacations: [{ 'таб_номер': '0871', 'дата_начала': '2026-09-10',
                          'дата_окончания': '2026-09-20' }],
            ppe: [{ 'таб_номер': '0871', 'наименование': 'Каска защитная',
                    'дата_окончания': '2026-09-25' }],
        });
        const html = el.innerHTML;
        assertFalse(html.indexOf('Отпуска · ') !== -1,
            'секции «Отпуска» нет (заявка Task 404)');
        assertFalse(html.indexOf('Отпуск · ') !== -1,
            'строк отпусков нет');
        assertFalse(html.indexOf('ws-ep-dot-vac') !== -1,
            'точек отпусков нет');
        assertTrue(html.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'секция «Мероприятия» жива');
        assertTrue(html.indexOf('СИЗ · сентябрь 2026 · 1') !== -1,
            'секция «СИЗ» жива');
        assertTrue(html.indexOf('Повторный') !== -1 &&
                   html.indexOf('Каска защитная') !== -1,
            'записи мероприятий и СИЗ показываются');
    });

    test('только отпуска — окно пустое (нет ни одной секции)', () => {
        const el = panelHost({
            month: 9,
            vacations: [{ 'таб_номер': '0871', 'дата_начала': '2026-09-10',
                          'дата_окончания': '2026-09-20' }],
        });
        assertTrue(el.innerHTML.indexOf('нет мероприятий в этом месяце') !== -1,
            'пустое состояние месяца');
        assertFalse(el.innerHTML.indexOf('Отпуска · ') !== -1,
            'секции отпусков нет');
        assertFalse(el.innerHTML.indexOf('СИЗ · ') !== -1,
            'секции СИЗ нет');
    });
});

// ============================================================
// 6. SW — версия кэша
// ============================================================
describe('Task 404 — SW: версия кэша', () => {
    test('CACHE_VERSION = kipia-test-v631 (Task 404)', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v631'") !== -1,
            'фронтенд менялся — кэш поднят до v631');
    });
    test('guard: v632 отсутствует (следующий бамп)', () => {
        assertTrue(SW_SRC.indexOf('kipia-test-v632') === -1,
            'v632 ещё не существует (guard следующего бампа)');
    });
});
