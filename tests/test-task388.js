// ============================================================
// Task 388 — 5 частей заявки:
//   1) миниатюры мероприятий ВСЕГДА сплошные с фоном ЦВЕТА КОДА
//      (сетка + печать; пунктирные ws-ev-pending/wsp-ev-plan
//      удалены; сноска печати без «день ещё не сформирован»);
//   2) панель «Обозначения» в КРАТКОМ виде — КРАТКИЕ обозначения
//      кодов по порядку заявки (canon.short, .ws-lg-short, 230px);
//   3) итоги учёта доступны в видах «только сменный» и «только
//      дневной» (гейт только уровня «min»; строки таблиц — по
//      работникам текущего вида);
//   4) значок раскрытия окон «Мероприятия»/«Нормы» — правый
//      ВЕРХНИЙ угол, без последующего смещения;
//   5) страница «Работники» — вкладки-ярлыки СТОЛБИКОМ СЛЕВА:
//      «Общая» + работники ПО ФАМИЛЬНО ПО АЛФАВИТУ.
//
// Заявка: «Миниатюрный значок примечания *, установленный в
// установленном дополнительно выходном дне, отображается прозрачным
// фоном вместо красного, как должно быть, это касается всех
// миниатюр (цвет фона миниатюр всегда должен соответствовать
// установленному). В панели "Обозначения" в кратком виде укажи
// краткое обозначение кодов, по порядру: [список]. В видах шахматки
// только сменный и только дневной сделай возможность показывать
// данные итогов учёта. В окнах мероприятий и норм перемести значок
// раскрытия окон в верхний правый угол… и без последующего смещения
// этого значка. В разделе Табель учёта рабочего времени / Работники
// измени представление данных, сделай по примеру как организованны
// вкладки страниц открытых сайтов в классических интернет браузерах,
// только размести ярлыки вкладок сбоку слева столбиком, первая с
// верху общая вкладка с общей информацией по всем работникам, а
// дальше под ней работники по фамильно по алфавиту.»
// ============================================================

const fs = require('fs');
const path = require('path');
const vm = require('vm');
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

function mockDoc(els) {
    return { getElementById: function(id) { return els[id] || null; } };
}

function mkEl() {
    return {
        style: {}, attrs: {}, hidden: false, innerHTML: '',
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
    };
}

// Канон справочника из index.html (скобочный баланс массива)
function canonCodes() {
    const i = INDEX_SRC.indexOf('_STATUS_CODES_CANON: [');
    if (i === -1) return null;
    const open = INDEX_SRC.indexOf('[', i);
    let depth = 0;
    for (let k = open; k < INDEX_SRC.length; k++) {
        if (INDEX_SRC[k] === '[') depth++;
        else if (INDEX_SRC[k] === ']') {
            depth--;
            if (!depth) return eval(INDEX_SRC.slice(open, k + 1));
        }
    }
    return null;
}

const CANON = canonCodes() || [];

// ============================================================
// 1. SRC — миниатюры: фон ВСЕГДА цвет установленного кода
// ============================================================
describe('Task 388 — SRC: миниатюры всегда сплошные с цветом кода', () => {

    test('класс/правила ws-ev-pending полностью удалены', () => {
        assertFalse(INDEX_SRC.indexOf('ws-ev-pending') !== -1,
            'ни класса, ни правил, ни упоминаний ws-ev-pending');
        assertFalse(INDEX_SRC.indexOf('var solidBadges') !== -1,
            'признак сформированности дня больше не делит бейджи');
    });

    test('_renderCell: бейдж — безусловная заливка цветом кода', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderCell'));
        assertTrue(fn.indexOf("evMeta.color ? ' style=\"background:' + evMeta.color") !== -1,
            'inline-фон из справочника — БЕЗ условия solidBadges');
        assertTrue(fn.indexOf("'<span class=\"ws-ev-badge\"'") !== -1,
            'бейдж рендерится одним видом (без пунктирного класса)');
    });

    test('печать: _printCell — бейдж всегда сплошной', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_printCell'));
        assertFalse(fn.indexOf('wsp-ev-plan') !== -1,
            'пунктирных бейджей-план в печати нет');
        assertTrue(fn.indexOf("evMeta.color ? ' style=\"background:' + evMeta.color") !== -1,
            'inline-цвет кода — безусловно');
        assertFalse(INDEX_SRC.indexOf('.wsp-ev.wsp-ev-plan { border-style: dashed; }') !== -1,
            'CSS-правило пунктирного бейджа печати удалено');
    });

    test('печать: сноска без «день ещё не сформирован»', () => {
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        assertFalse(b.indexOf('день ещё не сформирован') !== -1,
            'пояснение пунктирного значка удалено');
        assertTrue(b.indexOf('значок в углу ячейки') !== -1,
            'пояснение значка мероприятия живо (регресс 361)');
    });
});

// ============================================================
// 2. SRC — краткие обозначения в кратком виде «Обозначений»
// ============================================================
describe('Task 388 — SRC: краткие обозначения кодов (canon.short)', () => {

    test('канон: все 16 кодов имеют short по списку заявки', () => {
        const want = {
            'Д8': 'день 8ч', 'Д7,2': 'день 7,2ч', 'Д': 'день 12ч',
            'Н': 'ночь 12ч', 'д': 'день в выходной', 'н': 'ночь в выходной',
            'ОТ': 'отпуск', 'У': 'ученический', 'ОВ': 'отгул',
            'Б': 'больничный', '': 'выходной', 'ПР': 'прогул',
            'И': 'инструктаж', 'ОБ': 'обучение', 'ПЗ': 'проверка знаний',
            '*': 'не плановый'
        };
        assertEqual(CANON.length, 16, '16 кодов канона');
        let bad = [];
        CANON.forEach(c => {
            if (String(c.short || '') !== want[String(c.code)]) bad.push(c.code || '«»');
        });
        assertEqual(JSON.stringify(bad), '[]', 'short всех кодов = списку заявки: ' + bad.join(','));
    });

    test('_normalizeStatusCodes переносит short из канона', () => {
        const fn = methodText(INDEX_SRC, '_normalizeStatusCodes');
        assertTrue(fn.indexOf('short: canon[ci].short') !== -1,
            'short канонического кода переносится в нормализованный список');
    });

    test('_legendHtml рендерит .ws-lg-short', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_legendHtml'));
        assertTrue(fn.indexOf('ws-lg-short') !== -1,
            'строка кода получает краткое обозначение');
        assertTrue(fn.indexOf("'<span class=\"ws-lg-short\">— '") !== -1,
            'формат «код — краткое обозначение» (тире заявки)');
    });

    test('CSS: краткий вид показывает short, развёрнутый/страница — полные имена', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-lg-short { font-size: 12px;') !== -1,
            'правило .ws-lg-short есть');
        assertTrue(INDEX_SRC.indexOf('.ws-legend-drawer.ws-lg-wide .ws-lg-short { display: none; }') !== -1,
            'развёрнутый вид прячет краткие обозначения');
        assertTrue(INDEX_SRC.indexOf('.ws-lg-page-body .ws-lg-short { display: none; }') !== -1,
            'мобильная страница — полные наименования');
    });

    test('ширина краткого вида — 230px (краткие обозначения влезают)', () => {
        const i = INDEX_SRC.indexOf('.ws-legend-inner {');
        const chunk = INDEX_SRC.slice(i, i + 400);
        assertTrue(chunk.indexOf('width: 230px') !== -1,
            'CSS inner — 230px (было 190)');
        const fn = methodText(INDEX_SRC, '_legendWidthPx');
        assertTrue(fn.indexOf(': 230;') !== -1, 'JS-ширина краткого вида — 230');
        assertTrue(fn.indexOf('Math.max(230') !== -1, 'широкий не уже 230');
    });
});

// ============================================================
// 3. SRC — итоги учёта в видах «сменный»/«дневной»
// ============================================================
describe('Task 388 — SRC: итоги учёта доступны в любом виде', () => {

    test('_applyView: кнопка итогов видна во всех видах (кроме min)', () => {
        const fn = methodText(INDEX_SRC, '_applyView');
        assertTrue(fn.indexOf('totalsBtn.hidden = minNoTotals;') !== -1,
            'гейт — только уровень «min»');
        assertFalse(fn.indexOf('!full || minNoTotals') !== -1,
            'гейта вида больше нет');
    });

    test('_applyView: смена вида НЕ закрывает открытую шторку', () => {
        const fn = methodText(INDEX_SRC, '_applyView');
        assertFalse(fn.indexOf('(!full || minNoTotals) && this._totalsOpen') !== -1,
            'принудительное закрытие при сменном/дневном виде удалено');
        assertTrue(fn.indexOf('minNoTotals && this._totalsOpen') !== -1,
            'закрытие — только у уровня min');
    });

    test('toggleTotals: гейт только уровня «min»', () => {
        const fn = stripComments(methodText(INDEX_SRC, 'toggleTotals'));
        assertTrue(fn.indexOf("if (this._viewLevel === 'min' &&") !== -1,
            'десктоп: гейт только уровнем');
        assertTrue(fn.indexOf("if (this._viewLevel === 'min') return;") !== -1,
            'мобильная страница: гейт только уровнем');
        assertFalse(fn.indexOf("vGate !== 'full'") !== -1,
            'гейта вида нет');
    });

    test('onTotalsPageOpen: гейт только уровня «min»', () => {
        const fn = stripComments(methodText(INDEX_SRC, 'onTotalsPageOpen'));
        assertFalse(fn.indexOf("vGate !== 'full'") !== -1,
            'гейта вида нет');
        assertTrue(fn.indexOf("this._viewLevel === 'min'") !== -1,
            'гейт уровня жив');
    });

    test('месяц/год: строки итогов — по работникам текущего вида', () => {
        const fm = stripComments(methodText(INDEX_SRC, '_renderTotalsMonth'));
        assertTrue(fm.indexOf('this._viewEmployees()') !== -1,
            'месячная таблица берёт _viewEmployees()');
        assertTrue(fm.indexOf('i < viewList.length') !== -1,
            'цикл строк — по viewList');
        assertTrue(fm.indexOf('Нет работников в текущем виде.') !== -1,
            'пустое состояние вида');
        const fy = stripComments(methodText(INDEX_SRC, '_renderTotalsYearTable'));
        assertTrue(fy.indexOf('this._viewEmployees()') !== -1,
            'годовая таблица берёт _viewEmployees()');
    });

    test('подсказка «Вид» и тосты: итоги в любом виде', () => {
        const tip = methodText(INDEX_SRC, '_showViewTip');
        assertTrue(tip.indexOf('Итоги учёта доступны в любом виде') !== -1,
            'динамическая подсказка переозвучена');
        assertTrue(INDEX_SRC.indexOf('Итоги учёта доступны в любом виде — строки по работникам текущего вида') !== -1,
            'статичный HTML wsViewTipDesc');
        const cv = methodText(INDEX_SRC, 'cycleView');
        assertTrue(cv.indexOf('Сменный вид — только сменные работники, итоги учёта доступны') !== -1 &&
                   cv.indexOf('Дневной вид — только дневные работники, итоги учёта доступны') !== -1,
            'тосты сменного/дневного вида обещают итоги');
    });

    test('SW: кэш поднят до kipia-test-v617', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v617'") !== -1,
            'CACHE_VERSION = kipia-test-v617 (Task 388 — фронтенд менялся)');
        assertFalse(SW_SRC.indexOf('kipia-test-v618') !== -1,
            'v617 ещё не существует (guard)');
    });
});

// ============================================================
// 4. SRC — значок раскрытия окон «Мероприятия»/«Нормы»
// ============================================================
describe('Task 388 — SRC: значок раскрытия окон — правый ВЕРХНИЙ угол', () => {

    test('CSS .ws-bar-exp: top:5px (не bottom)', () => {
        const i = INDEX_SRC.indexOf('.ws-bar-exp {');
        const rule = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
        assertTrue(/top:\s*5px/.test(rule), 'верхний край');
        assertFalse(/bottom:\s*5px/.test(rule), 'нижнего упора больше нет');
    });

    test('заголовки окон не прячутся под значком (правый паддинг)', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-events-panel .ws-ep-cap,\n    .ws-cal-panel .ws-cp-cap { padding-right: 26px; }') !== -1,
            'плашки-заголовки окон получили правый добор паддинга');
    });

    test('компенсация прокрутки жива (значок приколот к видимой грани)', () => {
        const fn = methodText(INDEX_SRC, '_barExpSync');
        assertTrue(fn.indexOf("'translateY(' + el.scrollTop + 'px)'") !== -1,
            'translateY(scrollTop) — прикол к видимой верхней грани');
    });
});

// ============================================================
// 5. SRC — страница «Работники»: вкладки-ярлыки столбиком слева
// ============================================================
describe('Task 388 — SRC: страница «Работники» — вкладки', () => {

    test('_renderWorkersPage: раскладка вкладок + фамильный алфавит', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersPage'));
        assertTrue(fn.indexOf('ws-workers-layout') !== -1, 'раскладка вкладки+тело');
        assertTrue(fn.indexOf('ws-wtabs') !== -1, 'колонка ярлыков');
        assertTrue(fn.indexOf('ws-wtab-general') !== -1, 'ярлык «Общая»');
        assertTrue(fn.indexOf("localeCompare(") !== -1 &&
                   fn.indexOf("'ru'") !== -1,
            'сортировка по ФИО (фамильно по алфавиту)');
        assertTrue(fn.indexOf('selectWorkersTab') !== -1, 'клики по ярлыкам');
        assertTrue(fn.indexOf('_renderWorkersGeneral(list)') !== -1,
            'тело «Общей» вкладки — сводная таблица');
        assertTrue(fn.indexOf('_renderWorkerCard(empTabNo, withEdit)') !== -1,
            'тело вкладки работника — полная карточка');
    });

    test('selectWorkersTab/_workersTab — состояние вкладки', () => {
        assertTrue(INDEX_SRC.indexOf("_workersTab: 'general',") !== -1,
            'выбранная вкладка — свойство (по умолчанию «Общая»)');
        const fn = methodText(INDEX_SRC, 'selectWorkersTab');
        assertTrue(fn.indexOf('this._workersTab = String(') !== -1 &&
                   fn.indexOf('this._renderWorkersPage();') !== -1,
            'клик — выбор вкладки + перерисовка');
    });

    test('«Общая» вкладка — сводная таблица по всем работникам', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersGeneral'));
        assertTrue(fn.indexOf('ws-wgen-table') !== -1, 'таблица сводки');
        ['Таб. №', 'ФИО', 'Режим работы', 'Должность', 'Дата приёма',
         'Отпуск', 'Мероприятия'].forEach(h =>
            assertTrue(fn.indexOf(h) !== -1, 'колонка «' + h + '»'));
        assertTrue(fn.indexOf('_vacNetDaysInYear') !== -1,
            'отпуск года — «чистые» дни (ст. 120)');
    });

    test('CSS: вкладки столбиком слева + мобайл горизонтальной лентой', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-workers-layout {') !== -1 &&
                   INDEX_SRC.indexOf('display: flex;') !== -1,
            'раскладка flex');
        const i = INDEX_SRC.indexOf('.ws-wtabs {');
        const chunk = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
        assertTrue(chunk.indexOf('flex-direction: column') !== -1 &&
                   chunk.indexOf('width: 236px') !== -1,
            'ярлыки — вертикальная колонка слева');
        assertTrue(INDEX_SRC.indexOf('.ws-wtab.active {') !== -1,
            'активный ярлык подсвечен');
        const m = INDEX_SRC.indexOf('@media (max-width: 1023px)', INDEX_SRC.indexOf('.ws-wtabs {'));
        const mblock = INDEX_SRC.slice(m, m + 1400);
        assertTrue(mblock.indexOf('flex-direction: row') !== -1 &&
                   mblock.indexOf('overflow-x: auto') !== -1,
            'мобайл: ярлыки горизонтальной лентой со скроллом');
    });

    test('HTML: кнопка «Добавить работника» жива (регресс 386; Task 389 — на «Общей» вкладке)', () => {
        assertTrue(INDEX_SRC.indexOf('id="wsWorkersAddBtn"') !== -1 &&
                   INDEX_SRC.indexOf('>Добавить работника</button>') !== -1,
            'кнопка добавления на месте (рендер _renderWorkersGeneral)');
    });
});

// ============================================================
// 6. VM — функциональные проверки
// ============================================================
describe('Task 388 — VM: миниатюры/легенда', () => {

    // --- _renderCell: бейдж на пустой ячейке («Выходной») — СПЛОШНОЙ ---
    function renderCellHost() {
        const CODES = [
            { code: 'Д', name: 'День', color: '#FFE082' },
            { code: 'И', name: 'Инструктаж', color: '#B3E5FC' },
            { code: '*', name: 'Примечание', color: '#FFAB91' }
        ];
        return new Function('return ({' +
            methodText(INDEX_SRC, '_renderCell') + ',\n' +
            '_year: 2026, _month: 9, _todayIso: null,' +
            '_STATUS_CODES: ' + JSON.stringify(CODES) + ',' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_VAC_CODES: ["ОТ","У"],' +
            '_eventsAt: function() { return [{ code: "*", training: { id: 9 } }]; },' +
            '_vacationAt: function() { return null; },' +
            '_plannedShiftAt: function() { return null; },' +
            '_statusMeta: function(code) {' +
            '  for (var i = 0; i < this._STATUS_CODES.length; i++)' +
            '    if (this._STATUS_CODES[i].code === code) return this._STATUS_CODES[i];' +
            '  return null; },' +
            '_calDayOff: function() { return false; },' +
            '_calDayFeast: function() { return false; },' +
            '_calWend: function() { return false; },' +
            '_esc: function(s) { return String(s); }' +
            '});')();
    }

    test('VM: «*» на дополнительно установленном выходном — КРАСНЫЙ фон (#FFAB91)', () => {
        // заявка: «отображается прозрачным фоном вместо красного» —
        // статус '' (Выходной = пустая ячейка), мероприятие «*»
        const host = renderCellHost();
        const td = host._renderCell(10, '2026-09-10',
            { 'таб_номер': '017', 'ФИО': 'Иванов', 'тип': 'сменный' },
            null, false);
        assertTrue(td.indexOf('ws-ev-badge') !== -1, 'бейдж «*» рендерится');
        assertFalse(td.indexOf('ws-ev-pending') !== -1,
            'пунктирного/прозрачного вида НЕТ (Task 388)');
        assertTrue(/style="background:#FFAB91;"/.test(td),
            'фон бейджа — ЦВЕТ КОДА «*» из справочника (не прозрачный)');
    });

    test('VM: легаси-«.»-выходной — тот же сплошной бейдж', () => {
        const host = renderCellHost();
        const td = host._renderCell(11, '2026-09-11',
            { 'таб_номер': '017', 'ФИО': 'Иванов', 'тип': 'сменный' },
            { 'статус': '.', 'источник': 'руч', 'переработка': 0 }, false);
        assertTrue(/style="background:#FFAB91;"/.test(td),
            'бейдж «*» сплошной и на легаси-«.»-ячейке');
    });

    // --- _printCell: бейдж печати на пустой ячейке — сплошной ---
    test('VM: печать — «*» на пустой ячейке со заливкой цветом кода', () => {
        const host = new Function('return ({' +
            methodText(INDEX_SRC, '_printCell') + ',\n' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_statusMeta: function(code) { return { code: code, color: "#FFAB91" }; },' +
            '_calDayOff: function() { return false; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { return [{ code: "*", training: 1 }]; },' +
            '_esc: function(s) { return String(s); }' +
            '});')();
        const td = host._printCell(6, '2026-09-06',
            { 'таб_номер': '017' }, null);
        assertFalse(td.indexOf('wsp-ev-plan') !== -1, 'пунктирного бейджа нет');
        assertTrue(/class="wsp-ev"/.test(td), 'бейдж один вида (сплошной)');
        assertTrue(td.indexOf('background:#FFAB91') !== -1,
            'заливка цветом «*» — и на печати');
    });

    // --- _legendHtml: краткие обозначения в строках ---
    test('VM: _legendHtml — «Д8 — день 8ч», «* — не плановый»', () => {
        const host = new Function('return ({' +
            methodText(INDEX_SRC, '_legendHtml') + ',\n' +
            '_STATUS_CODES: ' + JSON.stringify(CANON) + ',' +
            '_EVENT_CODES: ["ПР","И","ОБ","ПЗ","*"],' +
            '_esc: function(s) { return String(s); }' +
            '});')();
        const html = host._legendHtml();
        assertTrue(html.indexOf('ws-lg-short') !== -1, 'краткие обозначения рендерятся');
        // порядок заявки: первый — Д8 с кратким «день 8ч»
        const first = html.indexOf('Д8');
        assertTrue(first !== -1 && html.indexOf('>— день 8ч<') > first,
            '«Д8 — день 8ч»');
        ['— день 7,2ч<', '— день 12ч<', '— ночь 12ч<', '— день в выходной<',
         '— ночь в выходной<', '— отпуск<', '— ученический<', '— отгул<',
         '— больничный<', '— выходной<', '— прогул<', '— инструктаж<',
         '— обучение<', '— проверка знаний<', '— не плановый<'].forEach(s =>
            assertTrue(html.indexOf(s) !== -1, 'краткое обозначение «' + s.slice(2) + '» есть'));
        // полные имена тоже в строке (показывает развёрнутый вид)
        assertTrue(html.indexOf('ws-lg-name') !== -1, 'полные наименования рядом');
    });

    test('VM: _legendHtml — «Выходной» с кратким «выходной» и БЕЗ кода', () => {
        const host = new Function('return ({' +
            methodText(INDEX_SRC, '_legendHtml') + ',\n' +
            '_STATUS_CODES: ' + JSON.stringify(CANON) + ',' +
            '_EVENT_CODES: ["ПР","И","ОБ","ПЗ","*"],' +
            '_esc: function(s) { return String(s); }' +
            '});')();
        const html = host._legendHtml();
        const dotRow = html.indexOf('ws-lg-swatch-dot');
        assertTrue(dotRow !== -1, 'свотч пустой ячейки жив (Task 387)');
        const rowEnd = html.indexOf('</div>', dotRow);
        const row = html.slice(dotRow, rowEnd);
        assertTrue(row.indexOf('>— выходной<') !== -1,
            'краткое обозначение «выходной» у строки без кода');
    });

    // --- _normalizeStatusCodes: short переносится из канона ---
    test('VM: нормализация листа БЕЗ short — short из канона', () => {
        const live = [
            { code: 'Д8', name: 'Листовое имя', color: '#123456' },
            { code: '*', name: 'Листовое имя *', color: '#FFAB91' }
        ];
        const host = new Function('return ({' +
            '_STATUS_CODES_CANON: ' + JSON.stringify(CANON) + ',' +
            methodText(INDEX_SRC, '_normalizeStatusCodes') + '});')();
        const out = host._normalizeStatusCodes(live);
        const d8 = out.filter(function(c) { return c.code === 'Д8'; })[0];
        assertEqual(d8.short, 'день 8ч', 'short — канонический');
        assertEqual(d8.name, 'День, плановая дневная 8-часовая смена (с 7:30 до 16:30), в пятницу (предпраздничный день) на час короче',
            'имя — каноническое (Task 387 жив)');
        assertEqual(d8.color, '#123456', 'цвет — живой из листа (Task 387 жив)');
        const star = out.filter(function(c) { return c.code === '*'; })[0];
        assertEqual(star.short, 'не плановый', 'short «*» — не плановый');
        // слот «Выходного» добавляется всегда — с short
        const vyh = out.filter(function(c) { return c.code === ''; })[0];
        assertEqual(vyh && vyh.short, 'выходной', 'слот «Выходного» — short из канона');
    });
});

describe('Task 388 — VM: итоги в сменном/дневном виде', () => {

    test('toggleTotals: вид shift + уровень view — шторка ОТКРЫВАЕТСЯ', () => {
        const els = { wsTotalsBtn: mkEl(), wsTotalsPanel: mkEl(),
                      pageWorkSchedule: null, wsTotalsDrawer: mkEl() };
        els.pageWorkSchedule = mkEl();
        const host = new Function('document', 'window', 'navigateTo', 'return ({' +
            methodText(INDEX_SRC, 'toggleTotals') + ',\n' +
            "_view: 'shift', _viewLevel: 'view'," +
            '_totalsOpen: false, _ttPage: false, _legendOpen: false,' +
            '_setLegend: function() {},' +
            '_updateTtTabsVisible: function() { this.tabs = true; },' +
            '_updateTtChv: function() {},' +
            '_renderTotals: function() { this.rendered = true; },' +
            '_applyTtHeadVar: function() { return false; },' +
            '_fitGrid: function() {},' +
            '_syncTotalsRows: function() {},' +
            '_hbarSyncAll: function() {}' +
            '});')(mockDoc(els), { matchMedia: function() { return { matches: true }; } },
                  function() { throw new Error('navigateTo on desktop'); });
        host.toggleTotals();
        assertEqual(host._totalsOpen, true, 'шторка открылась в СМЕННОМ виде (Task 388)');
        assertEqual(host.rendered, true, 'таблицы отрисованы');
        assertEqual(host.tabs, true, 'вкладки Месяц/Год показаны');
    });

    // --- строки месячной таблицы — по работникам текущего вида ---
    function totalsMonthHost(view) {
        const els = {
            wsTtBody: { innerHTML: '',
                        querySelector: function() { return null; } },
            wsTtWarn: { textContent: '', hidden: true, attrs: {},
                        setAttribute: function(k, v) { this.attrs[k] = v; } }
        };
        const MONTH_METHODS = ['_codeHours', '_totalsZero', '_totalsAgg', '_statusMeta',
                               '_empTypeMap', '_overHours', '_totalsEffectiveEntries',
                               '_fmtTotalsNum', '_esc', '_setTtWarn',
                               '_viewEmployees', '_renderTotalsMonth'];
        const host = new Function('document', 'return ({' +
            MONTH_METHODS.map(function(n) { return methodText(INDEX_SRC, n); }).join(',\n') +
            ',\n' +
            '_view: ' + JSON.stringify(view) + ',' +
            '_totalsExtra: false,' +
            '_year: 2026, _month: 9,' +
            '_applyTtHeadVar: function() { return false; },' +
            '_fitGrid: function() {},' +
            '_syncTotalsRows: function() {},' +
            '_hoverRow: null,' +
            '_EMPLOYEES: [' +
            "  { 'таб_номер': '0871', 'ФИО': 'Иванов И.И.', 'тип': 'сменный' }," +
            "  { 'таб_номер': '023', 'ФИО': 'Петров П.П.', 'тип': 'дневной' }," +
            "  { 'таб_номер': '045', 'ФИО': 'Сидоров С.С.', 'тип': 'сменный' }" +
            '],' +
            '_ENTRIES: [],' +
            '_PENDING: {},' +
            '_STATUS_CODES: [] });')(mockDoc(els));
        return { host: host, els: els };
    }

    test('VM: сменный вид — в таблице только сменные работники', () => {
        const t = totalsMonthHost('shift');
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('Иванов И.И.') !== -1 &&
                   h.indexOf('Сидоров С.С.') !== -1,
            'сменные — в таблице');
        assertFalse(h.indexOf('Петров П.П.') !== -1,
            'дневной НЕ показан в сменном виде');
    });

    test('VM: дневной вид — в таблице только дневные работники', () => {
        const t = totalsMonthHost('day');
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('Петров П.П.') !== -1, 'дневной — в таблице');
        assertFalse(h.indexOf('Иванов И.И.') !== -1 &&
                    h.indexOf('Сидоров С.С.') !== -1,
            'сменные НЕ показаны в дневном виде');
    });

    test('VM: полный вид — все работники (регресс)', () => {
        const t = totalsMonthHost('full');
        t.host._renderTotalsMonth();
        const h = t.els.wsTtBody.innerHTML;
        assertTrue(h.indexOf('Иванов И.И.') !== -1 &&
                   h.indexOf('Петров П.П.') !== -1 &&
                   h.indexOf('Сидоров С.С.') !== -1,
            'полный вид — все трое');
    });

    // --- годовая таблица: активные строки — по виду ---
    test('VM: год в сменном виде — активные строки только сменные', () => {
        const md = {
            year: 2026, ts: 1, failed: 0,
            months: { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [],
                      9: [], 10: [], 11: [], 12: [] },
            employees: [
                { 'таб_номер': '0871', 'ФИО': 'Иванов И.И.', 'тип': 'сменный' },
                { 'таб_номер': '023', 'ФИО': 'Петров П.П.', 'тип': 'дневной' },
                { 'таб_номер': '900', 'ФИО': 'Архивный А.А.', 'в_архиве': 1 }
            ]
        };
        const els = {
            wsTtBody: { innerHTML: '', querySelector: function() { return null; } },
            wsTtWarn: { textContent: '', hidden: true, attrs: {},
                        setAttribute: function(k, v) { this.attrs[k] = v; } }
        };
        const YEAR_METHODS = ['_codeHours', '_totalsZero', '_totalsAgg', '_statusMeta',
                              '_empTypeMap', '_overHours', '_fmtTotalsNum', '_esc',
                              '_sortEmployees', '_setTtWarn',
                              '_viewEmployees', '_renderTotalsYearTable'];
        const host = new Function('document', 'return ({' +
            YEAR_METHODS.map(function(n) { return methodText(INDEX_SRC, n); }).join(',\n') +
            ',\n' +
            "_view: 'shift'," +
            '_year: 2026, _month: 9,' +
            '_applyTtHeadVar: function() { return false; },' +
            '_fitGrid: function() {},' +
            '_syncTotalsRows: function() {},' +
            '_hoverRow: null,' +
            '_STATUS_CODES: [],' +
            '_EMPLOYEES: [' +
            "  { 'таб_номер': '0871', 'ФИО': 'Иванов И.И.', 'тип': 'сменный' }," +
            "  { 'таб_номер': '023', 'ФИО': 'Петров П.П.', 'тип': 'дневной' }" +
            '],' +
            '_YEAR_DATA: ' + JSON.stringify(md) + ' });')(mockDoc(els));
        host._renderTotalsYearTable();
        const h = els.wsTtBody.innerHTML;
        const main = h.slice(0, h.indexOf('ws-tt-arch-cap') === -1
                              ? h.length : h.indexOf('ws-tt-arch-cap'));
        assertTrue(main.indexOf('Иванов И.И.') !== -1, 'сменный — в основной таблице');
        assertFalse(main.indexOf('Петров П.П.') !== -1,
            'дневной НЕ в основной таблице сменного вида');
        assertTrue(h.indexOf('Архивный А.А.') !== -1,
            'архив — весь (не фильтруется видом)');
    });
});

describe('Task 388 — VM: страница «Работники» — вкладки', () => {

    function workersHost(canEdit) {
        const els = { wsWorkersBody: mkEl() };
        const EMPLOYEES = [
            { 'таб_номер': '0955', 'ФИО': 'Петров П. П.', 'тип': 'дневной',
              'смена': null, 'должность': 'Инженер', 'комментарий': '',
              'дата_приёма': '2025-09-01' },
            { 'таб_номер': '0871', 'ФИО': 'Иванов И. И.', 'тип': 'сменный',
              'смена': 2, 'должность': 'Слесарь КИПиА', 'комментарий': 'осн.',
              'дата_приёма': '2024-05-01' },
            { 'таб_номер': '0300', 'ФИО': 'Аистов А. А.', 'тип': 'сменный',
              'смена': 1, 'должность': 'Электрик', 'комментарий': '',
              'дата_приёма': '2023-02-11' }
        ];
        const host = new Function('document', 'return ({' +
            methodText(INDEX_SRC, '_renderWorkersPage') + ',\n' +
            methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\n' +
            methodText(INDEX_SRC, 'selectWorkersTab') + ',\n' +
            '_workersTab: "general",' +
            '_canEdit: ' + JSON.stringify(!!canEdit) + ',' +
            '_year: 2026, _month: 6,' +
            '_EMPLOYEES: ' + JSON.stringify(EMPLOYEES) + ',' +
            '_VACATIONS: [' +
            "  { id: 21, 'таб_номер': '0871', 'часть': 1," +
            "    'дата_начала': '2026-06-01', 'дата_окончания': '2026-06-10' }" +
            '],' +
            '_TRAININGS: [' +
            "  { id: 31, 'таб_номер': '0871', 'тип': 'инструктаж'," +
            "    'тема': 'ОТ', 'дата_начала': '2026-06-05', 'дата_окончания': '2026-06-05' }" +
            '],' +
            '_renderWorkerCard: function(tabNo, withEdit) {' +
            '  return "CARD:" + tabNo + ":" + (withEdit ? "edit" : "view"); },' +
            '_vacNetDaysInYear: function(v, y) { return 10; },' +
            '_plural: function(n, forms) { return forms[0]; },' +
            '_fmtDateRu: function(d) { return String(d); },' +
            '_esc: function(s) { return String(s); },' +
            '_escAttr: function(s) { return String(s); }' +
            '});')(mockDoc(els));
        return { host: host, els: els };
    }

    test('VM: по умолчанию — «Общая» вкладка со сводной таблицей', () => {
        const t = workersHost(true);
        t.host._renderWorkersPage();
        const body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('ws-workers-layout') !== -1, 'раскладка вкладок');
        assertTrue(body.indexOf('ws-wtab-general active') !== -1, '«Общая» активна');
        assertTrue(body.indexOf('>Общая</button>') !== -1, 'ярлык «Общая» первый');
        assertTrue(body.indexOf('ws-wgen-table') !== -1, 'сводная таблица');
        assertTrue(body.indexOf('CARD:') === -1, 'карточки НЕ рендерятся на «Общей»');
        // сводка: счётчик + ФИО всех
        assertTrue(body.indexOf('3 ') !== -1, 'трое работников в счётчике');
        ['Иванов И. И.', 'Петров П. П.', 'Аистов А. А.'].forEach(n =>
            assertTrue(body.indexOf(n) !== -1, 'в сводке есть «' + n + '»'));
    });

    test('VM: ярлыки — по фамильно по алфавиту (Аистов → Иванов → Петров)', () => {
        const t = workersHost(true);
        t.host._renderWorkersPage();
        const body = t.els.wsWorkersBody.innerHTML;
        const a = body.indexOf('Аистов А. А.');
        const i = body.indexOf('Иванов И. И.');
        const p = body.indexOf('Петров П. П.');
        assertTrue(a !== -1 && i !== -1 && p !== -1, 'все ярлыки есть');
        assertTrue(a < i && i < p, 'фамильный алфавит (НЕ по сменам/типам)');
        assertEqual((body.match(/role="tab"/g) || []).length, 4,
            'четыре ярлыка: Общая + трое');
    });

    test('VM: клик по ярлыку — карточка работника; выбор переживает перерисовку', () => {
        const t = workersHost(true);
        t.host._renderWorkersPage();
        t.host.selectWorkersTab('0871');
        let body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('CARD:0871:edit') !== -1,
            'карточка Иванова (withEdit у редактора)');
        assertEqual((body.match(/ws-wcard/g) || []).length, 1, 'одна карточка');
        // перерисовка (обновление данных с сеткой) — вкладка та же
        t.host._renderWorkersPage();
        body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('CARD:0871:edit') !== -1,
            'выбранная вкладка пережила перерисовку');
    });

    test('VM: зритель — карточка без правки; «Общая» доступна', () => {
        const t = workersHost(false);
        t.host.selectWorkersTab('0955');
        const body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('CARD:0955:view') !== -1,
            'карточка Петрова в режиме просмотра');
        t.host.selectWorkersTab('general');
        assertTrue(t.els.wsWorkersBody.innerHTML.indexOf('ws-wgen-table') !== -1,
            '«Общая» вкладка доступна и зрителю');
    });

    test('VM: несуществующая вкладка — сброс на «Общую»', () => {
        const t = workersHost(true);
        t.host.selectWorkersTab('9999');
        // работник «уволен» — валидация возвращает «Общую»
        t.host._EMPLOYEES = t.host._EMPLOYEES.filter(function(e) {
            return String(e['таб_номер']) !== '0871';
        });
        t.host.selectWorkersTab('0871');
        const body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('ws-wtab-general active') !== -1,
            'несуществующая вкладка сброшена на «Общую»');
        assertTrue(body.indexOf('ws-wgen-table') !== -1, 'сводка показана');
    });

    test('VM: сводная таблица — отпуск и мероприятия посчитаны', () => {
        const t = workersHost(true);
        const html = t.host._renderWorkersGeneral(
            t.host._EMPLOYEES.slice().sort(function(a, b) {
                return String(a['ФИО']).localeCompare(String(b['ФИО']), 'ru');
            }));
        // Иванов: отпуск 10 (мок _vacNetDaysInYear), 1 мероприятие
        const ivanovRow = html.slice(html.indexOf('Иванов И. И.'),
                                     html.indexOf('</tr>', html.indexOf('Иванов И. И.')));
        assertTrue(ivanovRow.indexOf('>10 день<') !== -1 ||
                   ivanovRow.indexOf('10 день') !== -1,
            'отпуск Иванова — 10 (дней)');
        assertTrue(ivanovRow.indexOf('>1<') !== -1, 'мероприятие Иванова — 1');
        // Петров: без отпуска/мероприятий — прочерки
        const petrovRow = html.slice(html.indexOf('Петров П. П.'),
                                     html.indexOf('</tr>', html.indexOf('Петров П. П.')));
        assertTrue(petrovRow.indexOf('—') !== -1, 'прочерки у Петрова');
        // смена Иванова — в режиме работы
        assertTrue(ivanovRow.indexOf('сменный, смена №2') !== -1,
            'режим работы со сменой');
        // примечание со счётчиком типов
        assertTrue(html.indexOf('сменных — 2') !== -1 &&
                   html.indexOf('дневных — 1') !== -1,
            'примечание: сменных 2, дневных 1');
    });
});
