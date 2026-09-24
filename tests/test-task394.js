// ============================================================
// Task 394 — заявка (3 части):
//  (1) «В десктопном представлении, блок отпусков переместить
//      справа от блока профиля, а блок СИЗ разместить под ним,
//      все четыре блока разместить равномерно по горизонтали на
//      весь экран» — сетка 2×2 (обёртка .ws-wgrid2, ≥1024px),
//      кап ширины 1020px снят;
//  (2) «В картах работников мероприятия указывать на весь год» —
//      _loadTrainings без month (сервер отдаёт ГОД), блок 3
//      карточки — «Мероприятия · ГОД», колонка «Общей» вкладки —
//      тоже год;
//  (3) «В табеле учёта рабочего времени, в окне мероприятий на
//      текущий месяц так же указывать информацию по СИЗ на текущий
//      месяц, и по отпускам (если отпуск попадает частично на два
//      месяца, то информация по нему должна отображаться в окне
//      мероприятий обоих месяцев)» — секции «Отпуска» (пересечение
//      с месяцем) и «СИЗ» (дата_окончания в месяце) в
//      _renderMonthEventsPanel.
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
    return m ? String(m) : '';
}

function stripComments(s) {
    return String(s).replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
}

function ruleBlock(sel) {
    const i = INDEX_SRC.indexOf(sel);
    if (i === -1) return null;
    const end = INDEX_SRC.indexOf('\n    }', i);
    return end === -1 ? null : INDEX_SRC.slice(i, end + 7);
}

function mockDoc(els) {
    return { getElementById: function(id) { return els[id] || null; } };
}

function mkEl() {
    return {
        style: {}, attrs: {}, hidden: false, innerHTML: '',
        value: '', textContent: '',
        classList: { add: function() {}, remove: function() {},
                     contains: function() { return false; },
                     toggle: function() {} },
        setAttribute: function(k, v) { this.attrs[k] = v; },
        getBoundingClientRect: function() { return { width: 0, height: 0,
                                                     left: 0, right: 0,
                                                     top: 0, bottom: 0 }; },
        querySelector: function() { return null; },
        querySelectorAll: function() { return []; },
        addEventListener: function() {},
        focus: function() {},
        appendChild: function() {},
    };
}

// ============================================================
// 1. SRC — загрузка года, карточка, «Общая», обёртка сетки
// ============================================================
describe('Task 394 — SRC: мероприятия на весь год', () => {

    test('_loadTrainings — ГОД без month (сервер отдаёт год)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_loadTrainings'));
        assertTrue(fn.indexOf("listTrainings', { year: this._year }") !== -1,
            'payload только год');
        assertFalse(fn.indexOf('month: this._month') !== -1,
            'месяц из запроса убран');
    });

    test('карточка: блок 3 — «Мероприятия · ГОД», пустое — «за год»', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCard'));
        assertTrue(fn.indexOf("Мероприятия · ' +\n                     this._year + '</div>'") !== -1,
            'заголовок блока — год');
        assertTrue(fn.indexOf('нет мероприятий за год') !== -1,
            'пустое состояние — «нет мероприятий за год»');
        assertFalse(fn.indexOf('monthNames') !== -1,
            'monthNames карточке больше не нужен');
        // защита от смешанных данных: сверка пересечения с годом
        assertTrue(fn.indexOf("trYStart = this._year + '-01-01'") !== -1 &&
                   fn.indexOf("trYEnd = this._year + '-12-31'") !== -1,
            'границы года для фильтра записей');
        assertTrue(fn.indexOf('if (tE < trYStart || tS > trYEnd) continue;') !== -1,
            'записи вне года не показываются');
    });

    test('«Общая» вкладка — колонка «Мероприятия · ГОД»', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersGeneral'));
        assertTrue(fn.indexOf("'<th>Мероприятия · ' + this._year + '</th>'") !== -1,
            'заголовок колонки — год');
        assertFalse(fn.indexOf('monthNames') !== -1,
            'monthNames сводке больше не нужен');
    });

    test('_renderWorkersPage — обёртка .ws-wgrid2 вокруг панелей', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersPage'));
        assertTrue(fn.indexOf("contentHtml = '<div class=\"ws-wgrid2\">' +") !== -1,
            'панели блоков — в обёртке сетки');
        assertTrue(fn.indexOf('this._renderWorkerCardPanels(empTabNo, withEdit)') !== -1,
            'вызов панелей жив (Task 393)');
        // «Общая» — без сетки
        const gi = fn.indexOf("'<div class=\"ws-wgen\">'");
        const wi = fn.indexOf("'<div class=\"ws-wgrid2\">'");
        assertTrue(gi !== -1 && wi !== -1, 'обе ветки рендера живы');
    });
});

// ============================================================
// 2. SRC — CSS: сетка 2×2, весь экран, плашки/точки секций
// ============================================================
describe('Task 394 — SRC: CSS сетки и окна мероприятий', () => {

    test('десктоп ≥1024px — .ws-wgrid2: ДВЕ колонки flex (Task 395)', () => {
        const re = /@media \(min-width: 1024px\) \{\s*\.ws-wgrid2 \{[^}]*?display: flex;[^}]*?gap: 12px;[^}]*?align-items: flex-start;\s*\}\s*\.ws-wgrid2 \.ws-wcol \{[^}]*?flex: 1 1 0;[^}]*?min-width: 0;[^}]*?margin-bottom: 0;\s*\}/;
        assertTrue(re.test(INDEX_SRC),
            'Task 395: две равные flex-колонки; правая (СИЗ) сверху — не тянется');
    });

    test('мобильный стек жив: зазор margin-bottom у панелей', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-wtab-body .ws-wcard { margin-bottom: 12px; }') !== -1,
            'базовый зазор стека (≤1023px) сохранён');
        assertTrue(INDEX_SRC.indexOf('.ws-wtab-body .ws-wcard:last-child { margin-bottom: 0; }') !== -1,
            'последнее окно без зазора');
    });

    test('страница «Работники» — НА ВЕСЬ ЭКРАН (кап 1020px снят)', () => {
        const r = ruleBlock('.ws-workers-body {');
        assertTrue(r !== null, 'правило живо');
        assertFalse(r.indexOf('max-width: 1020px') !== -1,
            'кап 1020px (Task 388) снят — блоки на весь экран');
    });

    test('окно мероприятий: плашки секций «Отпуска»/«СИЗ» и точки', () => {
        const vac = ruleBlock('.ws-ep-cap-vac {');
        const ppe = ruleBlock('.ws-ep-cap-ppe {');
        assertTrue(vac !== null && ppe !== null, 'плашки секций живы');
        assertTrue(INDEX_SRC.indexOf('.ws-ep-dot-vac { background: #90a4ae; }') !== -1,
            'точка отпуска — читаемый тон обеих тем');
        assertTrue(INDEX_SRC.indexOf('.ws-ep-dot-ppe { background: #f0a830; }') !== -1,
            'точка СИЗ — янтарная');
        const re = /\[data-theme="light"\] \.ws-ep-cap-vac,\s*\n\s*\[data-theme="light"\] \.ws-ep-cap-ppe \{[^}]*?color: #000;[^}]*?\}/;
        assertTrue(re.test(INDEX_SRC),
            'светлая тема: текст плашек — чёрный (Task 330)');
    });

    test('_renderMonthEventsPanel — секции отпусков и СИЗ', () => {
        const m = methodText(INDEX_SRC, '_renderMonthEventsPanel');
        assertTrue(m.indexOf('this._VACATIONS || []') !== -1,
            'защитный доступ к отпускам (харнессы без поля)');
        assertTrue(m.indexOf('this._PPE || []') !== -1,
            'защитный доступ к СИЗ');
        assertTrue(m.indexOf('vE < mStart || vS > mEnd') !== -1,
            'отпуск попадает при ПЕРЕСЕЧЕНИИ месяца (как мероприятия)');
        assertTrue(m.indexOf('pExpIso < mStart || pExpIso > mEnd') !== -1,
            'СИЗ — дата_окончания ВНУТРИ месяца');
        assertTrue(m.indexOf("pExpIso === 'До износа'") !== -1,
            '«До износа» — без даты, не показывается');
        assertTrue(m.indexOf('Отпуска · ') !== -1 && m.indexOf('СИЗ · ') !== -1,
            'заголовки секций');
        assertTrue(m.indexOf('ws-ep-dot-vac') !== -1 && m.indexOf('ws-ep-dot-ppe') !== -1,
            'точки секций');
        assertTrue(m.indexOf("'Отпуск · ' + vFio") !== -1 &&
                   m.indexOf("'СИЗ · ' + String(ppz['наименование']") !== -1,
            'тексты строк секций');
        assertTrue(m.indexOf('pExpIso !== selIso') !== -1,
            'режим выбранного дня: СИЗ — истекающие ровно в день');
        assertTrue(m.indexOf('vacList.length') !== -1 && m.indexOf('ppeList.length') !== -1,
            'счётчики секций');
    });
});

// ============================================================
// 3. VM — карточка: мероприятия за год
// ============================================================
function cardHost(trainings, vacs) {
    const EMP = [
        { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
          'смена': '', 'должность': 'Мастер КИПиА', 'комментарий': '',
          'дата_приёма': '2007-03-06' },
        { 'таб_номер': '0377', 'ФИО': 'Первов С. А.', 'тип': 'сменный',
          'смена': 1, 'должность': 'Слесарь КИПиА', 'комментарий': '',
          'дата_приёма': '2025-01-20' },
    ];
    const host = new Function('document', 'return ({' +
        methodText(INDEX_SRC, '_renderWorkerCard') + ',\n' +
        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\n' +
        '_canEdit: true,' +
        '_year: 2026, _month: 9,' +
        '_EMPLOYEES: ' + JSON.stringify(EMP) + ',' +
        '_VACATIONS: ' + JSON.stringify(vacs || []) + ',' +
        '_TRAININGS: ' + JSON.stringify(trainings || []) + ',' +
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
    return host;
}

describe('Task 394 — VM: карточка — мероприятия за весь год', () => {

    const TRS = [
        { id: 41, 'таб_номер': '2706', 'тип': 'инструктаж', 'тема': 'Февральский',
          'дата_начала': '2026-02-03', 'дата_окончания': '2026-02-05' },
        { id: 42, 'таб_номер': '2706', 'тип': 'обучение', 'тема': 'Июньское',
          'дата_начала': '2026-06-15', 'дата_окончания': '2026-06-15' },
        { id: 43, 'таб_номер': '2706', 'тип': 'инструктаж', 'тема': 'Сентябрьское',
          'дата_начала': '2026-09-07', 'дата_окончания': '2026-09-07' },
        // вне года шахматки — НЕ показывается
        { id: 44, 'таб_номер': '2706', 'тип': 'инструктаж', 'тема': 'Прошлый год',
          'дата_начала': '2025-09-07', 'дата_окончания': '2025-09-07' },
        // чужой работник — НЕ показывается
        { id: 45, 'таб_номер': '0377', 'тип': 'инструктаж', 'тема': 'Чужое',
          'дата_начала': '2026-09-08', 'дата_окончания': '2026-09-08' },
        // пересекает границу года (конец в 2026) — показывается
        { id: 46, 'таб_номер': '2706', 'тип': 'инструктаж', 'тема': 'Через Новый год',
          'дата_начала': '2025-12-30', 'дата_окончания': '2026-01-03' },
    ];

    test('блок 3 — «Мероприятия · 2026»: записи ВСЕХ месяцев года', () => {
        const host = cardHost(TRS);
        const b = host._renderWorkerCard('2706', true, true)[2];
        assertTrue(b.indexOf('Мероприятия · 2026') !== -1,
            'заголовок — год (не месяц)');
        ['Февральский', 'Июньское', 'Сентябрьское', 'Через Новый год']
            .forEach(t => assertTrue(b.indexOf(t) !== -1,
                'мероприятие года показано: ' + t));
        assertFalse(b.indexOf('Прошлый год') !== -1,
            'запись вне года не показывается');
        assertFalse(b.indexOf('Чужое') !== -1,
            'чужой работник не показывается');
        assertFalse(b.indexOf('нет мероприятий за год') !== -1,
            'пустого состояния нет');
    });

    test('порядок записей года — по дате начала', () => {
        const host = cardHost(TRS);
        const b = host._renderWorkerCard('2706', true, true)[2];
        const i1 = b.indexOf('Через Новый год');
        const i2 = b.indexOf('Февральский');
        const i3 = b.indexOf('Июньское');
        const i4 = b.indexOf('Сентябрьское');
        assertTrue(i1 < i2 && i2 < i3 && i3 < i4,
            'хронология года: декабрь→февраль→июнь→сентябрь');
    });

    test('пустой год — «нет мероприятий за год»', () => {
        const host = cardHost([]);
        const b = host._renderWorkerCard('2706', true, true)[2];
        assertTrue(b.indexOf('Мероприятия · 2026') !== -1, 'заголовок года');
        assertTrue(b.indexOf('нет мероприятий за год') !== -1, 'пустое состояние');
    });

    test('попап шахматки — та же секция года (склеенная строка)', () => {
        const host = cardHost(TRS);
        const html = host._renderWorkerCard('2706', false);
        assertEqual(typeof html, 'string', 'попап — строка');
        assertTrue(html.indexOf('Мероприятия · 2026') !== -1,
            'секция года и в попапе');
        assertTrue(html.indexOf('Февральский') !== -1 &&
                   html.indexOf('Сентябрьское') !== -1,
            'записи разных месяцев года в попапе');
    });
});

// ============================================================
// 4. VM — страница «Работники»: обёртка сетки + «Общая» (год)
// ============================================================
function pageHost(trainings) {
    const els = { wsWorkersBody: mkEl() };
    const EMPLOYEES = [
        { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
          'смена': '', 'должность': 'Мастер КИПиА', 'комментарий': '',
          'дата_приёма': '2007-03-06' },
        { 'таб_номер': '0377', 'ФИО': 'Первов С. А.', 'тип': 'сменный',
          'смена': 1, 'должность': 'Слесарь КИПиА', 'комментарий': '',
          'дата_приёма': '2025-01-20' },
    ];
    const host = new Function('document', 'return ({' +
        methodText(INDEX_SRC, '_renderWorkersPage') + ',\n' +
        methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\n' +
        methodText(INDEX_SRC, 'selectWorkersTab') + ',\n' +
        methodText(INDEX_SRC, '_isMasterKipia') + ',\n' +
        methodText(INDEX_SRC, '_renderWorkerCard') + ',\n' +
        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\n' +
        '_workersTab: "general",' +
        '_canEdit: true,' +
        '_year: 2026, _month: 9,' +
        '_EMPLOYEES: ' + JSON.stringify(EMPLOYEES) + ',' +
        '_VACATIONS: [],' +
        '_TRAININGS: ' + JSON.stringify(trainings || []) + ',' +
        '_PPE: [],' +
        '_fmtDateRu: function(d) { d = String(d);' +
        '  var p = d.split("-"); return p.length === 3 ?' +
        '  p[2] + "." + p[1] + "." + p[0] : d; },' +
        '_esc: function(s) { return String(s); },' +
        '_escAttr: function(s) { return String(s); },' +
        '_trainingCodeOf: function(t) { return "И"; },' +
        '_statusMeta: function(c) { return {}; },' +
        '_vacDaysInYear: function(v, y) { return 0; },' +
        '_vacNetDaysInYear: function(v, y) { return 0; },' +
        '_plural: function(n, f) { return f[2]; }' +
        '});')(mockDoc(els));
    return { host: host, els: els };
}

describe('Task 394 — VM: страница «Работники» — сетка и сводка', () => {

    test('вкладка работника — обёртка .ws-wgrid2 с 4 панелями', () => {
        const t = pageHost([]);
        t.host._renderWorkersPage();
        t.host.selectWorkersTab('2706');
        const body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('<div class="ws-wgrid2">') !== -1,
            'панели — в обёртке сетки 2×2');
        assertEqual((body.match(/class="ws-wcard"/g) || []).length, 4,
            'в обёртке — ровно четыре блока-окна');
        // порядок блоков в DOM: профиль → отпуска → мероприятия → СИЗ
        const i1 = body.indexOf('Галкин Д. Н.');
        const i2 = body.indexOf('Отпуска · 2026');
        const i3 = body.indexOf('Мероприятия · 2026');
        const i4 = body.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(i1 < i2 && i2 < i3 && i3 < i4,
            'DOM-порядок = раскладка сетки: профиль|отпуска / мероприятия|СИЗ');
    });

    test('«Общая» вкладка — БЕЗ обёртки сетки, колонка «Мероприятия · год»', () => {
        const trs = [
            { id: 41, 'таб_номер': '2706', 'тип': 'инструктаж', 'тема': 'А',
              'дата_начала': '2026-02-03', 'дата_окончания': '2026-02-03' },
            { id: 42, 'таб_номер': '2706', 'тип': 'обучение', 'тема': 'Б',
              'дата_начала': '2026-06-15', 'дата_окончания': '2026-06-15' },
            { id: 43, 'таб_номер': '2706', 'тип': 'инструктаж', 'тема': 'В',
              'дата_начала': '2026-09-07', 'дата_окончания': '2026-09-07' },
            { id: 44, 'таб_номер': '0377', 'тип': 'инструктаж', 'тема': 'Г',
              'дата_начала': '2026-09-08', 'дата_окончания': '2026-09-08' },
        ];
        const t = pageHost(trs);
        t.host._renderWorkersPage();
        const body = t.els.wsWorkersBody.innerHTML;
        assertFalse(body.indexOf('ws-wgrid2') !== -1,
            '«Общая» — без сетки карточки');
        assertTrue(body.indexOf('<th>Мероприятия · 2026</th>') !== -1,
            'колонка сводки — «Мероприятия · 2026» (год)');
        // счётчик в ячейке — годовой: у 2706 три записи года
        const re = /<tr><td>2706<\/td>[\s\S]*?<td>3<\/td><\/tr>/;
        assertTrue(re.test(body), 'ячейка Галкина — 3 мероприятия года');
    });
});

// ============================================================
// 5. VM — окно мероприятий месяца: отпуска + СИЗ
// ============================================================
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
        '_selDay: ' + (opts.selDay === undefined ? 'null' : opts.selDay) + ',' +
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

describe('Task 394 — VM: окно мероприятий — ОТПУСКА', () => {

    // отпуск ЧАСТИЧНО на два месяца: 29.09–02.10
    const VAC2M = [
        { id: 21, 'таб_номер': '0871', 'часть': 1,
          'дата_начала': '2026-09-29', 'дата_окончания': '2026-10-02',
          'комментарий': '' },
    ];

    test('отпуск через границу — в окне СЕНТЯБРЯ', () => {
        const el = panelHost({ month: 9, vacations: VAC2M });
        assertTrue(el.innerHTML.indexOf('Отпуска · сентябрь 2026 · 1') !== -1,
            'секция «Отпуска» с месяцем и счётчиком');
        assertTrue(el.innerHTML.indexOf('29.09–02.10') !== -1,
            'диапазон через границу месяцев');
        assertTrue(el.innerHTML.indexOf('Отпуск · Иванов Иван Иванович') !== -1,
            'текст строки: Отпуск · ФИО');
        assertTrue(el.innerHTML.indexOf('ws-ep-dot-vac') !== -1,
            'точка отпуска');
    });

    test('тот же отпуск — в окне ОКТЯБРЯ (заявка: обоих месяцев)', () => {
        const el = panelHost({ month: 10, vacations: VAC2M });
        assertTrue(el.innerHTML.indexOf('Отпуска · октябрь 2026 · 1') !== -1,
            'секция «Отпуска» есть и в следующем месяце');
        assertTrue(el.innerHTML.indexOf('29.09–02.10') !== -1,
            'тот же период виден в октябре');
    });

    test('месяц БЕЗ отпусков — секции «Отпуска» нет (скрыта)', () => {
        const el = panelHost({ month: 11, vacations: VAC2M });
        assertFalse(el.innerHTML.indexOf('Отпуска · ') !== -1,
            'ноябрь — отпуск не показывается');
        assertFalse(el.innerHTML.indexOf('· 0') !== -1,
            'нулевого счётчика нет');
    });

    test('без данных об отпусках — секции нет (харнесс без _VACATIONS)', () => {
        const el = panelHost({ month: 9, vacations: [] });
        assertFalse(el.innerHTML.indexOf('Отпуска · ') !== -1,
            'пустой список — секция скрыта');
    });

    test('выбранный день — только НАКРЫВАЮЩИЙ отпуск', () => {
        const vac = [
            { id: 22, 'таб_номер': '0871', 'часть': 1,
              'дата_начала': '2026-09-02', 'дата_окончания': '2026-09-05',
              'комментарий': '' },
        ];
        const el3 = panelHost({ month: 9, selDay: 3, vacations: vac });
        assertTrue(el3.innerHTML.indexOf('Отпуска · 03.09 · 1') !== -1,
            'день 3 накрыт отпуском 02–05.09');
        const el10 = panelHost({ month: 9, selDay: 10, vacations: vac });
        assertFalse(el10.innerHTML.indexOf('Отпуска · ') !== -1,
            'день 10 не накрыт — секция скрыта');
    });
});

describe('Task 394 — VM: окно мероприятий — СИЗ', () => {

    const PPE = [
        { id: 1, 'таб_номер': '0871', 'наименование': 'Каска защитная',
          'дата_выдачи': '2025-09-17', 'срок_годности': '1 год',
          'дата_окончания': '2026-09-17', 'примечание': '' },
        { id: 2, 'таб_номер': '0871', 'наименование': 'Очки закрытые',
          'дата_выдачи': '', 'срок_годности': 'До износа',
          'дата_окончания': 'До износа', 'примечание': '' },
        { id: 3, 'таб_номер': '0871', 'наименование': 'Ботинки',
          'дата_выдачи': '2024-10-05', 'срок_годности': '2 года',
          'дата_окончания': '2026-10-05', 'примечание': '' },
    ];

    test('СИЗ с датой окончания в месяце — секция «СИЗ»', () => {
        const el = panelHost({ month: 9, ppe: PPE });
        assertTrue(el.innerHTML.indexOf('СИЗ · сентябрь 2026 · 1') !== -1,
            'секция «СИЗ» с месяцем и счётчиком');
        assertTrue(el.innerHTML.indexOf('до 17.09') !== -1,
            'дата окончания строкой «до 17.09»');
        assertTrue(el.innerHTML.indexOf('СИЗ · Каска защитная · Иванов Иван Иванович') !== -1,
            'текст: СИЗ · наименование · ФИО');
        assertTrue(el.innerHTML.indexOf('ws-ep-dot-ppe') !== -1,
            'точка СИЗ');
    });

    test('«До износа» и чужой месяц — не показываются', () => {
        const el = panelHost({ month: 9, ppe: PPE });
        assertFalse(el.innerHTML.indexOf('Очки закрытые') !== -1,
            '«До износа» — без даты окончания, скрыто');
        assertFalse(el.innerHTML.indexOf('Ботинки') !== -1,
            'окончание в октябре — в сентябре скрыто');
        const el10 = panelHost({ month: 10, ppe: PPE });
        assertTrue(el10.innerHTML.indexOf('СИЗ · октябрь 2026 · 1') !== -1,
            'октябрь — ботинки видны');
        assertTrue(el10.innerHTML.indexOf('до 05.10') !== -1,
            'дата окончания октября');
    });

    test('выбранный день — СИЗ, истекающие РОВНО в день', () => {
        const el5 = panelHost({ month: 9, selDay: 17, ppe: PPE });
        assertTrue(el5.innerHTML.indexOf('СИЗ · 17.09 · 1') !== -1,
            'день 17 = дата окончания каски');
        const el6 = panelHost({ month: 9, selDay: 18, ppe: PPE });
        assertFalse(el6.innerHTML.indexOf('СИЗ · ') !== -1,
            'другой день — секция СИЗ скрыта');
    });

    test('прошедшие — класс ws-ep-past (динамические даты)', () => {
        // инвариант при любой дате запуска (приём Task 380):
        // «весь месяц» не прошедший; «первый день» — прошедший
        // iff 1-е число < сегодня
        const NOW = new Date();
        const Y = NOW.getFullYear(), M = NOW.getMonth() + 1;
        const pad = function(n) { return (n < 10 ? '0' : '') + n; };
        const iso = function(y, m, d) { return y + '-' + pad(m) + '-' + pad(d); };
        const DIM = new Date(Y, M, 0).getDate();
        const vac = [
            { 'таб_номер': '0871', 'дата_начала': iso(Y, M, 1),
              'дата_окончания': iso(Y, M, DIM) },
            { 'таб_номер': '0871', 'дата_начала': iso(Y, M, 1),
              'дата_окончания': iso(Y, M, 1) },
        ];
        const ppe = [
            { 'таб_номер': '0871', 'наименование': 'Каска',
              'дата_окончания': iso(Y, M, DIM) },
            { 'таб_номер': '0871', 'наименование': 'Ботинки',
              'дата_окончания': iso(Y, M, 1) },
        ];
        const el = panelHost({ year: Y, month: M, vacations: vac, ppe: ppe });
        // «1-е число» — прошедшее iff 1-е < сегодня (в этом же месяце)
        const expPast = iso(Y, M, 1) < iso(Y, M, NOW.getDate());
        // строк отпуска — 2, СИЗ — 2; прошедшие из них: оба «1-го числа»
        // (отпуск + СИЗ) iff 1-е < сегодня
        const nPast = (el.innerHTML.match(/ws-ep-past/g) || []).length;
        assertEqual(nPast, expPast ? 2 : 0,
            'классов ws-ep-past столько, сколько строк с прошедшей датой');
        assertEqual((el.innerHTML.match(/<span class="ws-ep-item/g) || []).length, 4,
            'строки: 2 отпуска + 2 СИЗ');
    });
});

describe('Task 394 — VM: окно мероприятий — порядок секций', () => {

    test('порядок: Мероприятия → Отпуска → СИЗ', () => {
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
        const iEv = el.innerHTML.indexOf('Мероприятия · сентябрь 2026');
        const iVac = el.innerHTML.indexOf('Отпуска · сентябрь 2026');
        const iPpe = el.innerHTML.indexOf('СИЗ · сентябрь 2026');
        assertTrue(iEv !== -1 && iVac !== -1 && iPpe !== -1, 'все три секции');
        assertTrue(iEv < iVac && iVac < iPpe, 'порядок: мероприятия → отпуска → СИЗ');
    });

    test('мероприятия месяца — прежний вид (заголовок/счётчик)', () => {
        const el = panelHost({
            month: 9,
            trainings: [{ 'таб_номер': '0871', 'тип': 'инструктаж',
                          'тема': 'Повторный', 'дата_начала': '2026-09-05',
                          'дата_окончания': '2026-09-05' }],
        });
        assertTrue(el.innerHTML.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий не изменился (Task 315)');
        assertFalse(el.innerHTML.indexOf('Отпуска · ') !== -1,
            'отпусков нет — секция скрыта');
        assertFalse(el.innerHTML.indexOf('СИЗ · ') !== -1,
            'СИЗ нет — секция скрыта');
    });
});

// ============================================================
// 6. SW — версия поднята
// ============================================================
describe('Task 394 — SW', () => {

    test('SW: kipia-test-v630', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v630'") !== -1,
            'SWVersion bumped');
        assertTrue(SW_SRC.indexOf('kipia-test-v631') === -1,
            'двойного бампа не было');
    });
});
