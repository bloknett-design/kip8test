// tests/test-task306.js
// Task 306 — три изменения по заявке пользователя:
//   1. Бейдж плановой смены (Task 305) — ТОЛЬКО у работников типа
//      «сменный» (дневные Д8/Д7,2 бейдж больше не показывают).
//   2. К кодам мероприятий И/ОБ/ПЗ добавлены ПР (прогул) и *
//      (примечание) — новые типы в форме «Новое мероприятие»,
//      серверная карта TRAINING_TYPE_TO_STATUS и _isEventStatusCode.
//   3. Кнопки «Обновить» (календарь) и «Сформировать» объединены в
//      одну кнопку «Сформировать»: подтверждённое формирование ТИХО
//      обновляет производственный календарь
//      (_refreshProdCalendarQuiet → ProdCalendar.refreshNow(true)).
//
// ЧТО ПРОВЕРЯЕТСЯ (двумя слоями):
//   Слой 1 — СИМУЛЯЦИЯ сервера (как test-work-events.js):
//     A. прогул на дне без смены → авто-строка «ПР» + FK
//     B. примечание на дне без смены → авто-строка «*» + FK
//     C. прогул на сменном дне → смена НЕ затёрта, FK проставлен
//     D. удаление прогул-мероприятия → авто-«ПР» снята (шаг 4.6)
//     E. РУЧНАЯ «ПР» (прогул через попап ячейки) сверков НЕ тронута
//     F. идемпотентность: повторная генерация с ПР/* без правок
//     G. addTraining принимает типы «прогул»/«примечание»;
//        неизвестный тип отклоняется (invalid_тип)
//   Слой 2 — статические инварианты клиента:
//     — _EVENT_CODES 5 кодов; _trainingCodeOf: прогул→ПР, примечание→*
//       (функционально, извлечением из index.html)
//     — форма «Новое мероприятие»: опции прогул/примечание
//     — _renderTrainings: единая карта + CSS .ws-type-ПР / .ws-type-\*
//     — бейдж плановой смены: фильтр empIsShift === 'сменный'
//     — кнопки: wsCalChip/confirmRefresh УДАЛЕНЫ, wsGenerateBtn есть,
//       _refreshProdCalendarQuiet зовётся из обоих _doGenerate*,
//       refreshNow(silent) без тостов
//     — SW v545
//
// Запуск: через tests/run-all.js (require './test-task306.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertEqual, assertTrue, assertFalse } = require('./test-helpers.js');

const WS_SRC = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'WorkSchedule.gs'), 'utf8');
const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');

// ============================================================
// Мок-инфраструктура Apps Script (как в test-work-events.js)
// ============================================================
class MockSheet {
    constructor(rows) {
        this.rows = rows || [];
        this.fmtCalls = [];
    }
    getLastRow() { return this.rows.length; }
    getRange(row, col, numRows, numCols) {
        numRows = numRows || 1; numCols = numCols || 1;
        const self = this;
        return {
            getValues() {
                const out = [];
                for (let r = row; r < row + numRows; r++) {
                    const line = [];
                    for (let c = col; c < col + numCols; c++) {
                        const rr = self.rows[r - 1];
                        line.push(rr ? (rr[c - 1] === undefined ? '' : rr[c - 1]) : '');
                    }
                    out.push(line);
                }
                return out;
            },
            setValues(vals) {
                for (let i = 0; i < vals.length; i++) {
                    const r = row + i;
                    while (self.rows.length < r) self.rows.push([]);
                    for (let c = 0; c < vals[i].length; c++) {
                        self.rows[r - 1][col - 1 + c] = vals[i][c];
                    }
                }
            },
            setValue(v) {
                while (self.rows.length < row) self.rows.push([]);
                self.rows[row - 1][col - 1] = v;
            },
            setNumberFormat(fmt) {
                self.fmtCalls.push({ row: row, col: col,
                                     numRows: numRows, numCols: numCols, fmt: fmt });
            }
        };
    }
    deleteRow(r) { this.rows.splice(r - 1, 1); }
    appendRow(arr) { this.rows.push(arr.slice()); }
}

const MOCK_UTILS = {
    findSessionByToken: () => ({ user_id: 1 }),
    findUserById: () => ({ role: 'Админ', email: 'test@example.com' }),
    audit: () => {}
};

function loadWS(sheets) {
    const ss = { getSheetByName: (n) => sheets[n] || null };
    const SpreadsheetApp = { openById: () => ss };
    const factory = new Function('SpreadsheetApp', 'Utils', WS_SRC + '\nreturn WorkSchedule;');
    return factory(SpreadsheetApp, MOCK_UTILS);
}

// Стенд: 017, шаблон cycle 4 (Д/Н/—/—), старт 01.01.2026.
// Август 2026: 10.08 — плановая «Н», 11.08 — выходной по циклу.
function baseSheets() {
    return {
        'Сотрудники': new MockSheet([
            ['таб_номер', 'ФИО', 'тип', 'смена', 'шаблон', 'старт_цикла', 'приём', 'увольнение', 'архив', 'должность', 'комментарий'],
            ['017', 'Иванов И.И.', 'сменный', '', 1, new Date(2026, 0, 1), '', '', 0, '', '']
        ]),
        'Шаблоны_ротации': new MockSheet([
            ['id', 'name', 'cycle', 'desc'],
            [1, 'Сутки через двое', 4, '']
        ]),
        'Дни_цикла': new MockSheet([
            ['pattern_id', 'day', 'status'],
            [1, 1, 'Д'], [1, 2, 'Н'], [1, 3, ''], [1, 4, '']
        ]),
        'Инструктажи': new MockSheet([
            ['id', 'таб', 'тип', 'тема', 'начало', 'конец', 'дней', 'комментарий']
        ]),
        'Записи_графика': new MockSheet([
            ['дата', 'таб', 'статус', 'переработка', 'праздник', 'источник', 'обновлён', 'замещает', 'инструкция', 'комментарий']
        ]),
        'Отпуска': new MockSheet([
            ['id', 'таб_номер', 'часть', 'дата_начала', 'дата_окончания', 'комментарий']
        ])
    };
}

function entryAt(sheet, tabNo, dateIso) {
    for (let i = 1; i < sheet.rows.length; i++) {
        const r = sheet.rows[i];
        if (iso(r[0]) === dateIso && String(r[1]).trim() === tabNo) {
            return { s: r[2], instr: r[8], src: r[5] };
        }
    }
    return null;
}
function iso(dt) {
    return dt.getFullYear() + '-' + String(dt.getMonth() + 1).padStart(2, '0') + '-' +
           String(dt.getDate()).padStart(2, '0');
}

// ============================================================
// Слой 1: симуляция generateMonth — ПР и * как коды мероприятий
// ============================================================
describe('Task 306 — симуляция: ПР и * — коды мероприятий', () => {

    test('A: прогул на дне БЕЗ смены — авто-строка «ПР»', () => {
        const sheets = baseSheets();
        sheets['Инструктажи'].rows.push(
            [11, '017', 'прогул', 'Не явился на смену, акт №3',
             new Date(2026, 7, 11), new Date(2026, 7, 11), 1, '']);

        const WS = loadWS(sheets);
        const res = WS.generateMonth({ token: 't', year: 2026, month: 8 });
        assertTrue(res.ok, 'generateMonth ok');

        const cell = entryAt(sheets['Записи_графика'], '017', '2026-08-11');
        assertTrue(!!cell, 'строка 11.08 вставлена');
        assertEqual(cell.s, 'ПР', 'код прогул-мероприятия — ПР (день без смены)');
        assertEqual(cell.instr, 11, 'связка инструкция=11');
        assertEqual(cell.src, 'авто', 'источник — авто');
        assertEqual(res.data.eventGenerated, 1, 'eventGenerated=1');
    });

    test('B: примечание на дне БЕЗ смены — авто-строка «*»', () => {
        const sheets = baseSheets();
        sheets['Инструктажи'].rows.push(
            [12, '017', 'примечание', 'Смена по приказу №145 перенесена',
             new Date(2026, 7, 11), new Date(2026, 7, 11), 1, 'по приказу']);

        const res = loadWS(sheets).generateMonth({ token: 't', year: 2026, month: 8 });
        assertTrue(res.ok);

        const cell = entryAt(sheets['Записи_графика'], '017', '2026-08-11');
        assertTrue(!!cell, 'строка 11.08 вставлена');
        assertEqual(cell.s, '*', 'код примечания — *');
        assertEqual(cell.instr, 12, 'связка инструкция=12');
    });

    test('C: прогул на СМЕННОМ дне — смена НЕ затёрта', () => {
        const sheets = baseSheets();
        sheets['Инструктажи'].rows.push(
            [13, '017', 'прогул', 'Прогул на смене',
             new Date(2026, 7, 10), new Date(2026, 7, 10), 1, '']);

        const res = loadWS(sheets).generateMonth({ token: 't', year: 2026, month: 8 });
        assertTrue(res.ok);

        const cell = entryAt(sheets['Записи_графика'], '017', '2026-08-10');
        assertEqual(cell.s, 'Н', 'плановая смена «Н» сохранена — прогул бейджем (Task 303)');
        assertEqual(cell.instr, 13, 'связка инструкция=13');
        assertEqual(res.data.eventGenerated, 0, 'строк ПР не вставлялось (сменный день)');
    });

    test('D: удаление прогул-мероприятия — авто-«ПР» снята (4.6)', () => {
        const sheets = baseSheets();
        sheets['Инструктажи'].rows.push(
            [11, '017', 'прогул', 'Не явился',
             new Date(2026, 7, 11), new Date(2026, 7, 11), 1, '']);
        loadWS(sheets).generateMonth({ token: 't', year: 2026, month: 8 });
        assertEqual(entryAt(sheets['Записи_графика'], '017', '2026-08-11').s, 'ПР',
            'первая генерация вставила ПР');

        sheets['Инструктажи'].rows.pop();   // мероприятие удалено
        const res = loadWS(sheets).generateMonth({ token: 't', year: 2026, month: 8 });
        assertEqual(entryAt(sheets['Записи_графика'], '017', '2026-08-11'), null,
            'шаг 4.6: устаревшая авто-«ПР» удалена');
        assertEqual(res.data.eventRemoved, 1, 'eventRemoved=1');
    });

    test('E: РУЧНАЯ «ПР» (прогул через попап) — НЕ тронута', () => {
        const sheets = baseSheets();
        // ручная запись-прогул (setManualEntry), НЕ мероприятие
        sheets['Записи_графика'].rows.push(
            [new Date(2026, 7, 10), '017', 'ПР', 0, 0, 'руч', new Date(), '', null, 'акт №7']);

        const res = loadWS(sheets).generateMonth({ token: 't', year: 2026, month: 8 });

        const cell = entryAt(sheets['Записи_графика'], '017', '2026-08-10');
        assertEqual(cell.s, 'ПР', 'ручная «ПР» сохранена (приоритет ручной правки)');
        assertEqual(cell.src, 'руч', 'источник — руч');
        assertEqual(res.data.eventRestored, 0, 'восстановлений нет');
        assertEqual(res.data.eventRemoved, 0, 'удалений нет');
    });

    test('F: идемпотентность — повторный прогон с ПР/* без правок', () => {
        const sheets = baseSheets();
        sheets['Инструктажи'].rows.push(
            [11, '017', 'прогул', 'Не явился', new Date(2026, 7, 11), new Date(2026, 7, 11), 1, ''],
            [12, '017', 'примечание', 'Примечание', new Date(2026, 7, 10), new Date(2026, 7, 10), 1, '']);
        loadWS(sheets).generateMonth({ token: 't', year: 2026, month: 8 });

        const snapshot = JSON.stringify(sheets['Записи_графика'].rows.slice(1).map(
            r => [iso(r[0]), r[1], r[2], r[8]]));
        const res2 = loadWS(sheets).generateMonth({ token: 't', year: 2026, month: 8 });
        const snapshot2 = JSON.stringify(sheets['Записи_графика'].rows.slice(1).map(
            r => [iso(r[0]), r[1], r[2], r[8]]));
        assertEqual(snapshot, snapshot2, 'данные не изменились');
        assertEqual(res2.data.eventGenerated, 0, 'вставок нет');
        assertEqual(res2.data.eventRemoved, 0, 'удалений нет');
    });

    test('G: addTraining принимает «прогул»/«примечание», rejects unknown', () => {
        const sheets = baseSheets();
        const WS = loadWS(sheets);

        const r1 = WS.addTraining({ token: 't', 'таб_номер': '017', тип: 'прогул',
                                    тема: 'Не явился', дата_начала: '2026-08-20',
                                    дата_окончания: '2026-08-20', длительность_дней: 1,
                                    комментарий: '' });
        assertTrue(r1.ok, 'addTraining: тип «прогул» принят');
        const last = sheets['Инструктажи'].rows[sheets['Инструктажи'].rows.length - 1];
        assertEqual(last[2], 'прогул', 'тип записан в лист «Инструктажи»');

        const r2 = WS.addTraining({ token: 't', 'таб_номер': '017', тип: 'примечание',
                                    тема: 'Перенос по приказу', дата_начала: '2026-08-21' });
        assertTrue(r2.ok, 'addTraining: тип «примечание» принят');

        const r3 = WS.addTraining({ token: 't', 'таб_номер': '017', тип: 'стажировка',
                                    тема: '???', дата_начала: '2026-08-22' });
        assertFalse(r3.ok, 'неизвестный тип отклонён');
        assertEqual(r3.error, 'invalid_тип', 'код ошибки invalid_тип');
    });
});

// ============================================================
// Слой 2: клиент — ПР и * в слое мероприятий
// ============================================================
describe('Task 306 — клиент: новые коды мероприятий', () => {

    test('JS: _trainingCodeOf — прогул→ПР, примечание→* (функционально)', () => {
        const m = INDEX_SRC.match(/_trainingCodeOf: function\(тип\) \{([\s\S]*?)\n        \},/);
        assertTrue(!!m, 'функция _trainingCodeOf найдена');
        const fn = new Function('тип', m[1]);
        assertEqual(fn('инструктаж'), 'И', 'инструктаж → И');
        assertEqual(fn('обучение'), 'ОБ', 'обучение → ОБ');
        assertEqual(fn('проверка_знаний'), 'ПЗ', 'проверка_знаний → ПЗ');
        assertEqual(fn('прогул'), 'ПР', 'прогул → ПР (Task 306)');
        assertEqual(fn('примечание'), '*', 'примечание → * (Task 306)');
        assertEqual(fn('чего-угодно'), '', 'неизвестный тип → пусто');
    });

    test('HTML: форма «Новое мероприятие» — 5 опций типа', () => {
        const sel = INDEX_SRC.match(/<select id="wsTrType"[\s\S]*?<\/select>/);
        assertTrue(!!sel, 'селект типа найден');
        ['инструктаж', 'обучение', 'проверка_знаний', 'прогул', 'примечание']
            .forEach(v => {
                assertTrue(sel[0].indexOf('value="' + v + '"') !== -1,
                    'опция «' + v + '» есть');
            });
    });

    test('JS: _renderTrainings — единая карта кодов', () => {
        assertTrue(INDEX_SRC.indexOf(
            "var code = this._trainingCodeOf(t.тип) || '?';") !== -1,
            'код карточки — из _trainingCodeOf (была inline-тернарка)');
    });

    test('CSS: цветные плашки типов ПР и * (справочные цвета)', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-tr-card .ws-tr-type.ws-type-ПР { background: #EF5350;') !== -1,
            'ПР — красный справочника');
        assertTrue(INDEX_SRC.indexOf('.ws-tr-card .ws-tr-type.ws-type-\\* { background: #FFAB91;') !== -1,
            '* — оранжевый справочника (селектор с escape)');
    });
});

// ============================================================
// Слой 2: бейдж плановой смены — только «сменный»
// ============================================================
describe('Task 306 — клиент: бейдж смены только у «сменный»', () => {

    test('JS: фильтр empIsShift в условии vacMain', () => {
        assertTrue(INDEX_SRC.indexOf(
            "var empIsShift = String(emp['тип'] || '').trim() === 'сменный';") !== -1,
            'тип сотрудника читается из справочника (как _sortEmployees/_posLabel)');
        assertTrue(INDEX_SRC.indexOf('var vacMain = empIsShift &&') !== -1,
            'vacMain начинается с фильтра типа');
    });

    test('JS: _plannedShiftAt — расчёт НЕ фильтруется по типу (паритет)', () => {
        const m = INDEX_SRC.match(/_plannedShiftAt: function\(isoDate, emp\) \{([\s\S]*?)\n        \},/);
        assertTrue(!!m);
        assertFalse(m[1].indexOf("тип") !== -1,
            'в чистом расчёте цикла тип не участвует — фильтр только в рендере');
    });
});

// ============================================================
// Слой 2: кнопки «Обновить» + «Сформировать» объединены
// ============================================================
describe('Task 306 — клиент: одна кнопка «Сформировать»', () => {

    test('HTML: wsCalChip удалён, wsGenerateBtn — единственная кнопка действия', () => {
        assertTrue(INDEX_SRC.indexOf('id="wsCalChip"') === -1,
            'кнопки «Обновить» нет в разметке');
        assertTrue(INDEX_SRC.indexOf('ProdCalendar.confirmRefresh()') === -1,
            'вызов confirmRefresh не остался');
        const btn = INDEX_SRC.match(/<button[^>]*id="wsGenerateBtn"[^>]*>/);
        assertTrue(!!btn, 'кнопка «Сформировать» есть');
        assertTrue(btn[0].indexOf('календарь обновится автоматически') !== -1,
            'title упоминает обновление календаря');
    });

    test('JS: confirmRefresh удалён; refreshNow(silent) без тостов', () => {
        assertTrue(INDEX_SRC.indexOf('confirmRefresh: function') === -1,
            'метод диалога обновления удалён');
        assertTrue(INDEX_SRC.indexOf('refreshNow: function(silent)') !== -1,
            'тихий режим обновления');
        assertTrue(INDEX_SRC.indexOf(
            "if (!silent && typeof KipToast !== 'undefined'") !== -1,
            'тосты — только в НЕтихом режиме');
    });

    test('JS: _refreshProdCalendarQuiet зовётся из обоих генераторов', () => {
        const m = INDEX_SRC.match(/_refreshProdCalendarQuiet: function\(\) \{([\s\S]*?)\n        \},/);
        assertTrue(!!m, 'хелпер определён');
        assertTrue(INDEX_SRC.indexOf('ProdCalendar.refreshNow(true);') !== -1,
            'вызов refreshNow в тихом режиме');
        const calls = (INDEX_SRC.match(/this\._refreshProdCalendarQuiet\(\);/g) || []).length;
        assertEqual(calls, 2, 'ровно 2 вызова: _doGenerateMonth + _doGenerateYear');
    });

    test('JS: _updateCalChip — только renderPanel (кнопки больше нет)', () => {
        const m = INDEX_SRC.match(/_updateCalChip: function\(\) \{([\s\S]*?)\n        \},/);
        assertTrue(!!m);
        assertTrue(m[1].indexOf('ProdCalendar.renderPanel()') !== -1,
            'перерисовка окошка норм осталась');
        assertTrue(m[1].indexOf('getElementById') === -1,
            'обращений к удалённой кнопке нет');
    });

    test('CSS: мёртвые стили .ws-cal-chip удалены', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-cal-chip {') === -1,
            'основной блок стилей кнопки удалён');
        assertTrue(INDEX_SRC.indexOf('.ws-cal-chip:disabled') === -1,
            'стиль disabled удалён');
        assertTrue(INDEX_SRC.indexOf('.ws-cal-panel {') !== -1,
            'окошко календаря (нормы) осталось');
    });

    test('SW: версия кэша kipia-test-v545 (Task 306 — клиент менялся)', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v545'") !== -1,
            'CACHE_VERSION = kipia-test-v545');
    });
});
