// tests/test-flow-period-input.js
// Task 286: ввод «расход за неделю/месяц» для Хозрасчёта №1.
// Task 287 (историческая заметка): счётчик переданных показаний
//   переделан — календарная неделя (пн–вс), предыдущий месяц
//   с откатом назад, непрозрачный фон.
// Task 288: блок «Передано показаний (контроль)» УДАЛЁН вместе с
//   логикой счёта (flowCountStats, flowPluralRecords, FLOW_MONTHS_RU,
//   _buildStatsHtml, CSS .flow-stats-*). Формы ввода за сутки /
//   за неделю / за месяц и запись значений за неделю/месяц в архив —
//   без изменений (суточная логика не тронута).
//
// ЗАДАЧА (по заявке пользователя и уточнениям):
//   • В детальной карточке Хозрасчёта №1 — выбор периода ввода:
//     «За сутки» (прежний режим Тэкон-19) / «За неделю» / «За месяц».
//     Значения — РАСХОД за период (агрегат), периоды — ПРОШЕДШИЕ
//     (неделя пн–вс, календарный месяц). Записи — ТОЛЬКО в архив
//     (meters-строка не меняется, «Последние показания» остаются
//     суточными).
//   • Task 288: счётчик пользователю не нужен — значения за неделю
//     и за месяц заносятся в архив, и на этом всё.
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   A. Standalone-хелперы (песочница extract-functions):
//      flowPrevWeekRange / flowPrevMonthRange — границы прошедших
//      периодов (пн–вс, календарный месяц, включая январь);
//      flowDateToInputVal / flowDateToMdy — конвертация дат;
//      flowEntryTypeAcc — винительный падеж («за неделю»).
//   B. Клиент (index.html, статика): chips периода, поля дат,
//      ветка submitInput, отдельный маршрут updatePeriodReading
//      (защита от старого сервера — «Unknown action», meters-строка
//      не портится), Task 288 — счётчик удалён (функции, CSS, рендер),
//      бейджи «нед»/«мес» в хронологии, график — только суточные
//      записи, CSS (тёмная/светлая), SW v534.
//   C. Серверные справочные копии (.gs): ветка entryType в
//      updateReading, _writePeriodEntry (только архив, prev=0,
//      hard-проверки), колонка R (entryType) в архиве,
//      самовосстановление заголовка R1, чтение 18 колонок,
//      пропуск агрегатов в getRecentAllMeters, маршрут в Code.gs,
//      node --check всех трёх файлов. Task 287 сервер НЕ менял.

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { test, describe, assertEqual, assertTrue, assertFalse } = require('./test-helpers.js');
const { extractFunctions } = require('./extract-functions.js');

const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');
const FLOWMETER_GS = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'Flowmeter.gs'), 'utf8');
const ARCHIVE_GS = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'FlowmeterArchive.gs'), 'utf8');
const CODE_GS = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'Code.gs'), 'utf8');

const fns = extractFunctions();

// ============================================================
// A. Standalone-хелперы (вычисления)
// ============================================================

describe('Task 286 — flowPrevWeekRange: границы прошедшей недели (пн–вс)', () => {

    test('Вторник 01.09.2026 → пн 24.08.2026 – вс 30.08.2026', () => {
        const r = fns.flowPrevWeekRange(new Date(2026, 8, 1));  // вт
        assertEqual(fns.flowDateToMdy(r.start), '8/24/2026', 'start = понедельник прошлой недели');
        assertEqual(fns.flowDateToMdy(r.end), '8/30/2026', 'end = воскресенье прошлой недели');
    });

    test('Понедельник 31.08.2026 → пн 24.08 – вс 30.08 (завершившаяся накануне неделя)', () => {
        const r = fns.flowPrevWeekRange(new Date(2026, 7, 31));  // пн
        assertEqual(fns.flowDateToMdy(r.start), '8/24/2026', 'start = пн прошлой недели (закрылась вчера, в вс)');
        assertEqual(fns.flowDateToMdy(r.end), '8/30/2026', 'end = вс прошлой недели');
    });

    test('Воскресенье 30.08.2026 (последний день недели 24–30.08) → пн 17.08 – вс 23.08', () => {
        const r = fns.flowPrevWeekRange(new Date(2026, 7, 30));  // вс
        assertEqual(fns.flowDateToMdy(r.start), '8/17/2026', 'текущая неделя ещё не закрыта — берём предыдущую');
        assertEqual(fns.flowDateToMdy(r.end), '8/23/2026', 'end = вс позапрошлой... прошлой полностью завершённой недели');
    });

    test('Суббота 29.08.2026 → та же прошедшая неделя 17.08–23.08, что и в вс', () => {
        const r = fns.flowPrevWeekRange(new Date(2026, 7, 29));  // сб
        assertEqual(fns.flowDateToMdy(r.start), '8/17/2026', 'сб и вс одной недели дают один результат');
        assertEqual(fns.flowDateToMdy(r.end), '8/23/2026', 'end = вс прошлой недели');
    });

    test('Диапазон всегда ровно 7 дней (пн–вс)', () => {
        const checks = [new Date(2026, 8, 1), new Date(2026, 11, 31), new Date(2027, 0, 13)];
        for (const now of checks) {
            const r = fns.flowPrevWeekRange(now);
            const days = Math.round((r.end - r.start) / 86400000);
            assertEqual(days, 6, 'разница start→end = 6 дней (7 дней включительно)');
            assertEqual(r.start.getDay(), 1, 'start — понедельник');
            assertEqual(r.end.getDay(), 0, 'end — воскресенье');
        }
    });

    test('Начало недели через границу года: вс 03.01.2027 → пн 21.12 – вс 27.12.2026', () => {
        const r = fns.flowPrevWeekRange(new Date(2027, 0, 3));  // вс
        assertEqual(fns.flowDateToMdy(r.start), '12/21/2026', 'start в прошлом году');
        assertEqual(fns.flowDateToMdy(r.end), '12/27/2026', 'end в прошлом году');
    });
});

describe('Task 286 — flowPrevMonthRange: границы прошедшего месяца', () => {

    test('01.09.2026 → 01.08.2026 – 31.08.2026', () => {
        const r = fns.flowPrevMonthRange(new Date(2026, 8, 1));
        assertEqual(fns.flowDateToMdy(r.start), '8/1/2026', 'start = 1-е число прошлого месяца');
        assertEqual(fns.flowDateToMdy(r.end), '8/31/2026', 'end = последнее число (31.08)');
    });

    test('15.02.2027 → 01.01.2027 – 31.01.2027 (январь — 31 день)', () => {
        const r = fns.flowPrevMonthRange(new Date(2027, 1, 15));
        assertEqual(fns.flowDateToMdy(r.start), '1/1/2027', 'start = 1 января');
        assertEqual(fns.flowDateToMdy(r.end), '1/31/2027', 'end = 31 января');
    });

    test('Январь 2027 → декабрь 2026 (переход через год): 01.12.2026 – 31.12.2026', () => {
        const r = fns.flowPrevMonthRange(new Date(2027, 0, 20));
        assertEqual(fns.flowDateToMdy(r.start), '12/1/2026', 'start = 1 декабря прошлого года');
        assertEqual(fns.flowDateToMdy(r.end), '12/31/2026', 'end = 31 декабря прошлого года');
    });

    test('Март невисокосного 2027 → февраль: 01.02 – 28.02', () => {
        const r = fns.flowPrevMonthRange(new Date(2027, 2, 5));
        assertEqual(fns.flowDateToMdy(r.end), '2/28/2027', 'end = 28 февраля (невисокосный)');
    });

    test('Июль 2028 → июнь, 30 дней', () => {
        const r = fns.flowPrevMonthRange(new Date(2028, 6, 10));
        assertEqual(fns.flowDateToMdy(r.end), '6/30/2028', 'end = 30 июня');
    });
});

describe('Task 286 — flowDateToInputVal / flowDateToMdy: конвертация дат', () => {

    test('flowDateToInputVal: паддинг нулями (01.09.2026 → 2026-09-01)', () => {
        assertEqual(fns.flowDateToInputVal(new Date(2026, 8, 1)), '2026-09-01', 'YYYY-MM-DD');
    });

    test('flowDateToInputVal: 25.12.2026 → 2026-12-25', () => {
        assertEqual(fns.flowDateToInputVal(new Date(2026, 11, 25)), '2026-12-25', 'YYYY-MM-DD');
    });

    test('flowDateToInputVal: невалидная дата → пустая строка', () => {
        assertEqual(fns.flowDateToInputVal(null), '', 'null → ""');
        assertEqual(fns.flowDateToInputVal(new Date(NaN)), '', 'Invalid Date → ""');
    });

    test('flowDateToMdy: 01.09.2026 → 9/1/2026 (внутренний формат)', () => {
        assertEqual(fns.flowDateToMdy(new Date(2026, 8, 1)), '9/1/2026', 'M/D/YYYY');
        assertEqual(fns.flowDateToMdy(new Date(2026, 11, 25)), '12/25/2026', 'M/D/YYYY');
    });

    test('flowDateToMdy: невалидная дата → пустая строка', () => {
        assertEqual(fns.flowDateToMdy(null), '', 'null → ""');
    });
});

describe('Task 286 — flowEntryTypeAcc: винительный падеж («за …»)', () => {

    test('за сутки / за неделю / за месяц', () => {
        assertEqual(fns.flowEntryTypeAcc('сутки'), 'сутки', '«за сутки»');
        assertEqual(fns.flowEntryTypeAcc('неделя'), 'неделю', '«за неделю» (не «за неделя»!)');
        assertEqual(fns.flowEntryTypeAcc('месяц'), 'месяц', '«за месяц»');
    });

    test('неизвестный тип → сутки (безопасный дефолт)', () => {
        assertEqual(fns.flowEntryTypeAcc(''), 'сутки', 'пусто → сутки');
        assertEqual(fns.flowEntryTypeAcc('день'), 'сутки', 'мусор → сутки');
    });
});

// B. Клиент (index.html — статические проверки)
// ============================================================

describe('Task 286 — клиент: UI шита ввода (chips + поля дат)', () => {

    test('Ряд chips периода присутствует и скрыт по умолчанию', () => {
        assertTrue(INDEX_SRC.indexOf('id="flowInputPeriodRow"') !== -1,
            'ряд #flowInputPeriodRow есть в HTML');
        const m = INDEX_SRC.match(/id="flowInputPeriodRow" style="display:none;"/);
        assertTrue(m !== null, 'по умолчанию скрыт (показывается только для №1)');
    });

    test('Три chips: За сутки / За неделю / За месяц → setEntryType', () => {
        assertTrue(INDEX_SRC.indexOf("id=\"flowChipDay\" onclick=\"FlowmeterData.setEntryType('сутки')\"") !== -1,
            'chip «За сутки»');
        assertTrue(INDEX_SRC.indexOf("id=\"flowChipWeek\" onclick=\"FlowmeterData.setEntryType('неделя')\"") !== -1,
            'chip «За неделю»');
        assertTrue(INDEX_SRC.indexOf("id=\"flowChipMonth\" onclick=\"FlowmeterData.setEntryType('месяц')\"") !== -1,
            'chip «За месяц»');
    });

    test('Второе поле даты «по» + динамические подписи лейблов', () => {
        assertTrue(INDEX_SRC.indexOf('id="flowInputDateEndGroup"') !== -1,
            'группа конца периода есть');
        assertTrue(INDEX_SRC.indexOf('id="flowInputDateEnd"') !== -1,
            'input #flowInputDateEnd есть');
        assertTrue(INDEX_SRC.indexOf('id="flowInputDateLabel"') !== -1,
            'лейбл начала даты получает id (для смены подписи)');
        assertTrue(INDEX_SRC.indexOf('id="flowInputDateEndLabel"') !== -1,
            'лейбл конца периода есть');
    });

    test('Заголовок шита — винительный падеж («за неделю», не «за неделя»)', () => {
        assertTrue(INDEX_SRC.indexOf("m.hoz + ' — внести расход за ' + flowEntryTypeAcc(type)") !== -1,
            'заголовок через flowEntryTypeAcc');
        assertTrue(INDEX_SRC.indexOf("KipToast.show('Расход за ' + flowEntryTypeAcc(type) + ' сохранён')") !== -1,
            'тост через flowEntryTypeAcc');
    });

    test('Chips видны только для №1 при новом вводе (openInput)', () => {
        const m = INDEX_SRC.match(/periodRow\.style\.display = \(dailyMode && !isEdit\) \? '' : 'none';/);
        assertTrue(m !== null, 'условие dailyMode && !isEdit');
    });

    test('setEntryType: только №1 + валидация типа', () => {
        assertTrue(INDEX_SRC.indexOf('setEntryType: function(type)') !== -1,
            'метод setEntryType определён');
        assertTrue(INDEX_SRC.indexOf("if (!m || !this._isDailyMode(m)) return;  // только №1") !== -1,
            'guard: только Хозрасчёт №1');
        assertTrue(INDEX_SRC.indexOf("if (type !== 'сутки' && type !== 'неделя' && type !== 'месяц') return;") !== -1,
            'guard: допустимые типы');
    });

    test('_applyEntryTypeFields: подписи «Период с» / «по» и даты по умолчанию', () => {
        assertTrue(INDEX_SRC.indexOf("_applyEntryTypeFields: function(m, isEdit)") !== -1,
            'метод определён');
        assertTrue(INDEX_SRC.indexOf("dateLabel.textContent = 'Период с'") !== -1,
            'лейбл «Период с»');
        assertTrue(INDEX_SRC.indexOf("dateEndLabel.textContent = 'по'") !== -1,
            'лейбл «по»');
        assertTrue(INDEX_SRC.indexOf("dateLabel.textContent = 'Дата за предыдущие сутки'") !== -1,
            'возврат подписи для суточного режима');
        assertTrue(INDEX_SRC.indexOf('flowPrevWeekRange(now)') !== -1,
            'даты недели по умолчанию — flowPrevWeekRange');
        assertTrue(INDEX_SRC.indexOf('flowPrevMonthRange(now)') !== -1,
            'даты месяца по умолчанию — flowPrevMonthRange');
    });

    test('closeInput снимает фокус с нового поля даты', () => {
        const m = INDEX_SRC.match(/dateEndField\.blur\(\);/);
        assertTrue(m !== null, 'blur для #flowInputDateEnd');
    });
});

describe('Task 286 — клиент: submitInput ветка «за период»', () => {

    test('submitInput уходит в _submitPeriodEntry для недели/месяца', () => {
        assertTrue(INDEX_SRC.indexOf("if (this._inputEntryType === 'неделя' || this._inputEntryType === 'месяц') {") !== -1,
            'ветка на выбранный тип');
        assertTrue(INDEX_SRC.indexOf('this._submitPeriodEntry(num, gcalVal);') !== -1,
            'вызов _submitPeriodEntry');
    });

    test('_submitPeriodEntry: отдельный маршрут flowmeter.updatePeriodReading', () => {
        assertTrue(INDEX_SRC.indexOf("this._api('flowmeter.updatePeriodReading', apiPayload)") !== -1,
            'маршрут updatePeriodReading (не updateReading!)');
    });

    test('_submitPeriodEntry: payload с entryType и prev=0', () => {
        assertTrue(INDEX_SRC.indexOf('entryType: type,') !== -1, 'entryType в payload');
        const m = INDEX_SRC.match(/prev: 0,\s*\/\/ расход за период → consumption = введённое значение/);
        assertTrue(m !== null, 'prev=0 — consumption = расход');
    });

    test('Защита от старого сервера: «Unknown action» → подсказка DEPLOY', () => {
        const m = INDEX_SRC.match(/msg\.indexOf\('Unknown action'\) !== -1[\s\S]{0,400}?обновите Apps Script \(DEPLOY-Task286\)/);
        assertTrue(m !== null, 'ветка Unknown action с подсказкой обновить сервер');
    });

    test('Клиентская hard-проверка: дата конца раньше начала → тост, без отправки', () => {
        const m = INDEX_SRC.match(/Дата конца периода раньше даты начала/);
        assertTrue(m !== null, 'сообщение о неверных датах периода');
    });

    test('Эхо entryType проверяется (подстраховка ветки сервера)', () => {
        const m = INDEX_SRC.match(/etEcho !== type/);
        assertTrue(m !== null, 'сравнение ответа сервера с отправленным типом');
    });

    test('После успеха — load() (перезагрузка архива), без optimistic-обновления meters', () => {
        const m = INDEX_SRC.match(/_submitPeriodEntry[\s\S]{0,2500}?self\.load\(\)/);
        assertTrue(m !== null, 'load() после сохранения периода');
        // Оптимистичное обновление meter.curr осталось только в суточной ветке:
        const submitBody = INDEX_SRC.slice(
            INDEX_SRC.indexOf('submitInput: function()'),
            INDEX_SRC.indexOf('_submitPeriodEntry: function(num, gcalVal)'));
        assertTrue(submitBody.indexOf('meter.curr = num;') !== -1,
            'суточная ветка: оптимистичное обновление как прежде');
    });
});

describe('Task 288 — счётчик «Передано показаний (контроль)» удалён', () => {

    test('Метод _buildStatsHtml и заголовок блока удалены', () => {
        assertFalse(INDEX_SRC.indexOf('_buildStatsHtml') !== -1,
            'метода _buildStatsHtml нет');
        assertFalse(INDEX_SRC.indexOf('Передано показаний') !== -1,
            'заголовка «Передано показаний» нет');
    });

    test('Логика счёта удалена: flowCountStats / flowPluralRecords / FLOW_MONTHS_RU', () => {
        assertFalse(INDEX_SRC.indexOf('flowCountStats') !== -1,
            'функции счёта нет');
        assertFalse(INDEX_SRC.indexOf('flowPluralRecords') !== -1,
            'склонения «N записей» нет');
        assertFalse(INDEX_SRC.indexOf('FLOW_MONTHS_RU') !== -1,
            'массива названий месяцев нет');
    });

    test('CSS блока .flow-stats-* удалён (тёмная и светлая темы)', () => {
        assertFalse(INDEX_SRC.indexOf('.flow-stats-section') !== -1, 'контейнера нет');
        assertFalse(INDEX_SRC.indexOf('.flow-stats-row') !== -1, 'строк нет');
        assertFalse(INDEX_SRC.indexOf('.flow-stats-title') !== -1, 'заголовка нет');
        assertFalse(INDEX_SRC.indexOf('.flow-stats-value') !== -1, 'значений нет');
    });

    test('Пустой архив: карточка рендерит только «Записей ещё нет», без блока', () => {
        const m = INDEX_SRC.match(/_buildArchiveHtml: function\(records, meter\) \{\s*if \(!records \|\| records\.length === 0\) \{\s*return '<div class="flow-archive-section">' \+/);
        assertTrue(m !== null, 'пустой архив → сразу хронология, без statsHtml');
        assertFalse(INDEX_SRC.indexOf('statsHtml') !== -1,
            'переменной statsHtml нет');
    });

    test('Хронология не начинается со вставки счётчика', () => {
        const m = INDEX_SRC.match(/var html = '';\s*html \+= '<div class="flow-archive-section">';/);
        assertTrue(m !== null, 'html начинается напрямую с flow-archive-section');
    });

    test('Удалённые хелперы не извлекаются песочницей (flowEntryTypeAcc остаётся)', () => {
        const EXTRACT_SRC = fs.readFileSync(path.join(__dirname, 'extract-functions.js'), 'utf8');
        assertFalse(EXTRACT_SRC.indexOf("'flowCountStats'") !== -1,
            'flowCountStats не извлекается');
        assertFalse(EXTRACT_SRC.indexOf("'flowPluralRecords'") !== -1,
            'flowPluralRecords не извлекается');
        assertTrue(EXTRACT_SRC.indexOf("'flowEntryTypeAcc'") !== -1,
            'flowEntryTypeAcc остаётся (форма ввода)');
    });

    test('Форма ввода не тронута: chips и flowEntryTypeAcc на месте', () => {
        assertTrue(INDEX_SRC.indexOf('id="flowChipDay"') !== -1, 'chip «За сутки»');
        assertTrue(INDEX_SRC.indexOf('id="flowChipWeek"') !== -1, 'chip «За неделю»');
        assertTrue(INDEX_SRC.indexOf('id="flowChipMonth"') !== -1, 'chip «За месяц»');
        assertTrue(INDEX_SRC.indexOf("m.hoz + ' — внести расход за ' + flowEntryTypeAcc(type)") !== -1,
            'заголовок шита через flowEntryTypeAcc');
    });

    test('Маршрут периода и запись в архив не тронуты', () => {
        assertTrue(INDEX_SRC.indexOf("this._api('flowmeter.updatePeriodReading', apiPayload)") !== -1,
            'маршрут updatePeriodReading на месте');
        assertTrue(INDEX_SRC.indexOf('_submitPeriodEntry: function(num, gcalVal)') !== -1,
            'метод _submitPeriodEntry на месте');
    });
});


describe('Task 286 — клиент: хронология (бейджи + график)', () => {

    test('Записи недели/месяца: диапазон дат + бейдж «нед»/«мес»', () => {
        assertTrue(INDEX_SRC.indexOf('flow-arch-period-badge') !== -1, 'CSS-класс бейджа');
        assertTrue(INDEX_SRC.indexOf("(rEt === 'неделя') ? 'нед' : 'мес'") !== -1,
            'текст бейджа нед/мес');
        assertTrue(INDEX_SRC.indexOf('_fmtDateShort(r.datePrev)') !== -1,
            'диапазон: datePrev–dateCurr');
    });

    test('График — только суточные записи (агрегаты исключены)', () => {
        assertTrue(INDEX_SRC.indexOf('dayRecords = records.filter') !== -1,
            'фильтрация dayRecords');
        assertTrue(INDEX_SRC.indexOf('this._buildArchiveChart(dayRecords, meter)') !== -1,
            'график строится из dayRecords');
    });

    test('Таблица хронологии показывает ВСЕ записи (включая агрегаты)', () => {
        // displayRecords (последние 31 любых) идут в таблицу:
        const m = INDEX_SRC.match(/displayRecords = records\.length > recLimit \? records\.slice\(0, recLimit\) : records;/);
        assertTrue(m !== null, 'таблица — все типы записей');
    });
});

describe('Task 286 — клиент: CSS и SW', () => {

    test('CSS: chips (тёмная + светлая темы)', () => {
        assertTrue(INDEX_SRC.indexOf('.flow-period-chip {') !== -1, 'базовый стиль');
        assertTrue(INDEX_SRC.indexOf('.flow-period-chip.active {') !== -1, 'активный chip');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .flow-period-chip.active {') !== -1,
            'светлая тема');
    });

    test('CSS: бейдж периода (тёмная + светлая)', () => {
        assertTrue(INDEX_SRC.indexOf('.flow-arch-period-badge {') !== -1, 'бейдж');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .flow-arch-period-badge {') !== -1,
            'светлая тема');
    });

    test('SW-кэш поднят до v534 (Task 288 — фронтенд менялся)', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v534'") !== -1,
            'CACHE_VERSION = kipia-test-v534');
        assertFalse(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v533'") !== -1,
            'старой версии v533 нет');
    });

    test('Регрессия: WEB_APP_URL не тронут (AKfycbyt…, Task 284)', () => {
        const m = INDEX_SRC.match(/WEB_APP_URL:\s*'(https:\/\/script\.google\.com\/macros\/s\/AKfycbyt[^(]+\/exec)'/);
        assertTrue(m !== null, 'URL развёртывания прежний');
    });
});

// ============================================================
// C. Серверные справочные копии (.gs)
// ============================================================

describe('Task 286 — сервер: Flowmeter.gs (ветка entryType)', () => {

    test('updateReading нормализует entryType (сутки по умолчанию)', () => {
        assertTrue(FLOWMETER_GS.indexOf("var entryType = String(payload.entryType || 'сутки').trim().toLowerCase();") !== -1,
            'нормализация с дефолтом «сутки»');
        assertTrue(FLOWMETER_GS.indexOf("if (entryType !== 'неделя' && entryType !== 'месяц') entryType = 'сутки';") !== -1,
            'неизвестные значения → сутки');
    });

    test('Ветка «за период» уходит в _writePeriodEntry ДО meters-записи', () => {
        const branch = FLOWMETER_GS.indexOf("if (entryType === 'неделя' || entryType === 'месяц') {");
        assertTrue(branch !== -1, 'ветка есть');
        // Ветка до блока Task 205 (id===1) — до записи в meters:
        const task205 = FLOWMETER_GS.indexOf('if (id === 1) {');
        assertTrue(branch < task205, 'ветка периода раньше суточной логики');
    });

    test('_writePeriodEntry: метод определён, prev=0 (consumption = расход)', () => {
        assertTrue(FLOWMETER_GS.indexOf('_writePeriodEntry: function(payload, user, id, entryType)') !== -1,
            'метод определён');
        assertTrue(FLOWMETER_GS.indexOf('0, currVal,   // prev=0 → consumption (E) = введённый расход за период') !== -1,
            'prev=0 при записи в архив');
    });

    test('_writePeriodEntry: НЕ пишет в meters-строку', () => {
        // Вырезаем тело метода и проверяем отсутствие setValue в колонки meters
        const start = FLOWMETER_GS.indexOf('_writePeriodEntry: function');
        const end = FLOWMETER_GS.indexOf('setComment: function');
        const body = FLOWMETER_GS.slice(start, end);
        // setValue в _writePeriodEntry допустим только в архиве (через appendToArchive);
        // прямых getRange(rowNum, N).setValue (запись в meters) быть не должно:
        const metersWrites = body.match(/getRange\(rowNum, \d+\)\.setValue\(/g) || [];
        assertEqual(metersWrites.length, 0, 'нет прямых записей в meters-строку: ' + metersWrites.length);
        // Чтение (getValue) колонок 2/8/11 — допустимо (hoz/unit/period):
        assertTrue(body.indexOf('sheet.getRange(rowNum, 2).getValue()') !== -1,
            'чтение hoz (только getValue)');
    });

    test('_writePeriodEntry: hard-проверки (отрицательное значение, даты навыворот)', () => {
        const start = FLOWMETER_GS.indexOf('_writePeriodEntry: function');
        const end = FLOWMETER_GS.indexOf('setComment: function');
        const body = FLOWMETER_GS.slice(start, end);
        assertTrue(body.indexOf("error: 'sign_neg'") !== -1, 'проверка отрицательного значения');
        assertTrue(body.indexOf("error: 'date_inconsistent'") !== -1, 'проверка порядка дат');
    });

    test('Soft-валидация пропускается для периодов (правила суточные)', () => {
        const start = FLOWMETER_GS.indexOf('_writePeriodEntry: function');
        const end = FLOWMETER_GS.indexOf('setComment: function');
        const body = FLOWMETER_GS.slice(start, end);
        assertFalse(body.indexOf('ValidationRules.compute') !== -1,
            'ValidationRules.compute не вызывается для недели/месяца');
        assertFalse(body.indexOf('_requireEdit') !== -1,
            'авторизация уже выполнена в updateReading (нет повторного _requireEdit)');
    });

    test('Ошибка записи в архив — неуспех (архив — единственное хранилище)', () => {
        const start = FLOWMETER_GS.indexOf('_writePeriodEntry: function');
        const end = FLOWMETER_GS.indexOf('setComment: function');
        const body = FLOWMETER_GS.slice(start, end);
        assertTrue(body.indexOf("return { ok: false, error: 'Ошибка записи в архив: '") !== -1,
            'ok:false при сбое архива');
    });

    test('Суточный путь помечает запись «сутки» (R=18)', () => {
        assertTrue(FLOWMETER_GS.indexOf("'сутки'  // Task 286: тип записи (R=18)") !== -1,
            'суточные записи помечены явно');
    });

    test('node --check: Flowmeter.gs синтаксически валиден', () => {
        const tmp = '/tmp/task286-flowmeter-check.js';
        fs.writeFileSync(tmp, FLOWMETER_GS);
        execSync('node --check ' + tmp);
        fs.unlinkSync(tmp);
        assertTrue(true, 'синтаксис валиден');
    });
});

describe('Task 286 — сервер: FlowmeterArchive.gs (колонка R)', () => {

    test('appendToArchive: параметр entryType (15-й)', () => {
        const m = ARCHIVE_GS.match(/appendToArchive: function\(meterId, hoz, prev, curr, datePrev, dateCurr, temp, gcal, unit, period, role, name, comment, anomaly, entryType\)/);
        assertTrue(m !== null, 'подпись с entryType');
    });

    test('appendRow пишет 18 значений (R = entryType)', () => {
        const m = ARCHIVE_GS.match(/String\(entryType \|\| ''\)\s+\/\/ R: entryType \(Task 286\)/);
        assertTrue(m !== null, 'R-колонка в appendRow');
    });

    test('Самовосстановление заголовка R1 (идемпотентно)', () => {
        const m = ARCHIVE_GS.match(/sheet\.getRange\(1, 18\)\.setValue\('entryType'\)/);
        assertTrue(m !== null, 'setValue заголовка при пустой ячейке R1');
    });

    test('listArchive читает 18 колонок и возвращает entryType', () => {
        assertTrue(ARCHIVE_GS.indexOf('lastRow - this.DATA_START_ROW + 1, 18);') !== -1,
            'getRange …18 колонок');
        assertTrue(ARCHIVE_GS.indexOf('entryType:   entryType                       // R=18 — Task 286') !== -1,
            'поле entryType в record');
        assertTrue(ARCHIVE_GS.indexOf("(entryTypeRaw === 'неделя' || entryTypeRaw === 'месяц') ? entryTypeRaw : 'сутки'") !== -1,
            'нормализация: пусто = сутки (legacy)');
    });

    test('getRecentAllMeters: 18 колонок + пропуск агрегатов', () => {
        const m = ARCHIVE_GS.match(/if \(etRaw === 'неделя' \|\| etRaw === 'месяц'\) continue;/);
        assertTrue(m !== null, 'агрегаты не участвуют в WRONG_METER');
    });

    test('flowmeterInitArchive: заголовок entryType (R=18)', () => {
        const m = ARCHIVE_GS.match(/'entryType'\s+\/\/ R=18 — Task 286/);
        assertTrue(m !== null, 'заголовок в init-функции');
    });

    test('node --check: FlowmeterArchive.gs синтаксически валиден', () => {
        const tmp = '/tmp/task286-archive-check.js';
        fs.writeFileSync(tmp, ARCHIVE_GS);
        execSync('node --check ' + tmp);
        fs.unlinkSync(tmp);
        assertTrue(true, 'синтаксис валиден');
    });
});

describe('Task 286 — сервер: Code.gs (маршрут updatePeriodReading)', () => {

    test("case 'flowmeter.updatePeriodReading' маршрутизируется в updateReading", () => {
        const m = CODE_GS.match(/case 'flowmeter\.updatePeriodReading':\s*\n\s*return _json\(Flowmeter\.updateReading\(payload\)\);/);
        assertTrue(m !== null, 'маршрут определён');
    });

    test('Маршрут distinct от суточного updateReading (защита от старого сервера)', () => {
        // Комментарий-обоснование в Code.gs (многострочный):
        const m = CODE_GS.match(/СТАРЫЙ[\s\S]{0,200}сервер без/);
        assertTrue(m !== null, 'комментарий о защите старого сервера');
        // Оба маршрута на месте:
        assertTrue(CODE_GS.indexOf("case 'flowmeter.updateReading':") !== -1,
            'суточный маршрут на месте');
        // Ровно один маршрут updatePeriodReading (нет дублей):
        const routes = CODE_GS.match(/case 'flowmeter\.updatePeriodReading':/g) || [];
        assertEqual(routes.length, 1, 'единственный маршрут updatePeriodReading');
    });

    test('node --check: Code.gs синтаксически валиден', () => {
        const tmp = '/tmp/task286-code-check.js';
        fs.writeFileSync(tmp, CODE_GS);
        execSync('node --check ' + tmp);
        fs.unlinkSync(tmp);
        assertTrue(true, 'синтаксис валиден');
    });
});
