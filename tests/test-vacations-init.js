// tests/test-vacations-init.js
// Task 275: статические проверки скрипта инициализации листа
// «Отпуска» (scripts/VacationsInit.gs) на соответствие серверной
// части WorkSchedule.gs (Task 274). Apps Script в Node не запускаем —
// проверяем инварианты по исходнику (как test-work-schedule.js
// проверяет чистые функции и инварианты серверного кода).
//
// Что проверяется:
//   1. Файл scripts/VacationsInit.gs существует
//   2. SHEET_NAME инициализатора = VACATIONS_SHEET WorkSchedule.gs
//   3. SPREADSHEET_ID инициализатора = SPREADSHEET_ID WorkSchedule.gs
//   4. Заголовки A–F: ровно 6, порядок как читает listVacations
//   5. Даты демо — Date objects (WorkSchedule.gs требует instanceof
//      Date, строки игнорирует)
//   6. Математика демо-периодов: 017 = 14 + 10 + 4 = 28 дн., 023 = 14
//   7. Идемпотентность: force — очистка; без force — данные не
//      трогаются; данные в строке 1 сдвигаются вниз (insertRowBefore)
//   8. Валидация «часть» — requireNumberBetween(1, 3)
//   9. Список таб_номер — requireValueInRange из «Сотрудники»
//  10. Запись демо — appendRow из 6 полей, id от max id + 1
//      (та же логика, что addVacation)
//  11. Подсветка пересечений периодов одного сотрудника

const fs = require('fs');
const path = require('path');
const { test, describe, assertEqual, assertTrue, assertFalse } = require('./test-helpers.js');

const gsPath = path.resolve(__dirname, '..', 'scripts', 'VacationsInit.gs');
const wsPath = path.resolve(__dirname, '..', 'scripts', 'WorkSchedule.gs');

// Вытащить строковую константу из .gs: NAME: 'value' или var NAME = 'value'
function extractConst(src, name) {
    const re = new RegExp(name + "\\s*[:=]\\s*'([^']+)'");
    const m = src.match(re);
    return m ? m[1] : null;
}

describe('Task 275: VacationsInit.gs — инициализация листа «Отпуска»', () => {

    test('файл scripts/VacationsInit.gs существует', () => {
        assertTrue(fs.existsSync(gsPath), 'VacationsInit.gs не найден');
    });

    test('файл scripts/WorkSchedule.gs существует (эталон)', () => {
        assertTrue(fs.existsSync(wsPath), 'WorkSchedule.gs не найден');
    });

    test('SHEET_NAME инициализатора = VACATIONS_SHEET WorkSchedule.gs', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        const ws = fs.readFileSync(wsPath, 'utf8');
        const sheetName = extractConst(gs, 'SHEET_NAME');
        const vacSheet = extractConst(ws, 'VACATIONS_SHEET');
        assertEqual(sheetName, 'Отпуска', 'SHEET_NAME должен быть «Отпуска»');
        assertEqual(sheetName, vacSheet, 'имя листа разошлось с VACATIONS_SHEET сервера');
    });

    test('SPREADSHEET_ID инициализатора = SPREADSHEET_ID WorkSchedule.gs', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        const ws = fs.readFileSync(wsPath, 'utf8');
        const idInit = extractConst(gs, 'SPREADSHEET_ID');
        const idSrv = extractConst(ws, 'SPREADSHEET_ID');
        assertTrue(!!idInit && !!idSrv, 'SPREADSHEET_ID не извлечён');
        assertEqual(idInit, idSrv, 'инициализатор пишет не в ту таблицу');
    });

    test('заголовки A–F: ровно 6, порядок как читает listVacations', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        const m = gs.match(/HEADERS = \[([^\]]+)\]/);
        assertTrue(!!m, 'массив HEADERS не найден');
        const headers = m[1].split(',').map(s => s.trim().replace(/^'|'$/g, ''));
        assertEqual(headers.length, 6, 'должно быть 6 столбцов A–F');
        assertEqual(headers[0], 'id', 'A1');
        assertEqual(headers[1], 'таб_номер', 'B1');
        assertEqual(headers[2], 'часть', 'C1');
        assertEqual(headers[3], 'дата_начала', 'D1');
        assertEqual(headers[4], 'дата_окончания', 'E1');
        assertEqual(headers[5], 'комментарий', 'F1');
    });

    test('WorkSchedule.gs читает те же столбцы (комментарий listVacations)', () => {
        const ws = fs.readFileSync(wsPath, 'utf8');
        // Порядок чтения в listVacations: id (A), таб_номер (B), часть (C),
        // дата_начала (D), дата_окончания (E), комментарий (F)
        assertTrue(ws.indexOf('Читаем id (A), таб_номер (B), часть (C), дата_начала (D),') !== -1,
            'комментарий порядка столбцов listVacations не найден');
    });

    test('даты демо — Date objects, не строки (сервер требует instanceof Date)', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        // WorkSchedule.gs: if (!(startDate instanceof Date)) continue;
        const ws = fs.readFileSync(wsPath, 'utf8');
        assertTrue(ws.indexOf('instanceof Date') !== -1,
            'WorkSchedule.gs больше не проверяет instanceof Date — тест устарел');
        const dates = gs.match(/new Date\(2026, \d+, \d+\)/g);
        assertTrue(!!dates, 'new Date(...) в демо не найдены');
        assertEqual(dates.length, 8, '4 периода × 2 даты = 8 Date objects');
    });

    test('математика демо-периодов: 017 = 14 + 10 + 4 = 28 дн., 023 = 14 дн.', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        const re = /new Date\((\d+), (\d+), (\d+)\)/g;
        const pts = [];
        let m;
        while ((m = re.exec(gs)) !== null) {
            pts.push([+m[1], +m[2], +m[3]]);
        }
        assertEqual(pts.length, 8, 'ожидались 8 дат');
        const days = [];
        for (let i = 0; i < 8; i += 2) {
            const start = new Date(pts[i][0], pts[i][1], pts[i][2]);
            const end = new Date(pts[i + 1][0], pts[i + 1][1], pts[i + 1][2]);
            const d = Math.round((end - start) / 86400000) + 1;
            days.push(d);
        }
        assertEqual(days.join(','), '14,10,4,14', 'длительности периодов');
        assertEqual(days[0] + days[1] + days[2], 28, '017: 3 части = 28 дн.');
    });

    test('демо: 4 строки, таб_номера 017/017/017/023, части 1/2/3/1', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        const tabs = [...gs.matchAll(/tab: '(\d+)'/g)].map(x => x[1]);
        const parts = [...gs.matchAll(/part: (\d)/g)].map(x => +x[1]);
        assertEqual(tabs.join(','), '017,017,017,023', 'таб_номера демо');
        assertEqual(parts.join(','), '1,2,3,1', 'номера частей демо');
    });

    test('идемпотентность: функция с параметром force, clear только при force', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        assertTrue(/function vacationsInitSheet\(force\)/.test(gs),
            'сигнатура vacationsInitSheet(force) не найдена');
        assertTrue(gs.indexOf('sheet.clear()') !== -1, 'force-очистка отсутствует');
        // clear() вызывается только внутри ветки if (force)
        const forceBlock = gs.match(/if \(force\) \{[\s\S]{0,400}?sheet\.clear\(\)/);
        assertTrue(!!forceBlock, 'sheet.clear() должен вызываться только в ветке force');
    });

    test('без force: шапка чинится, данные в строке 1 сдвигаются вниз', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        assertTrue(gs.indexOf('insertRowBefore(1)') !== -1,
            'insertRowBefore(1) — данные строки 1 не сдвигаются');
        // Сдвиг выполняется только когда A1 не пуст и не «id»
        const cond = gs.indexOf("a1 !== '' && a1 !== HEADERS[0]") !== -1;
        assertTrue(cond, 'защитное условие сдвига строки 1 не найдено');
    });

    test('валидация «часть» — целое 1..3 (requireNumberBetween)', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        assertTrue(gs.indexOf('requireNumberBetween(1, 3)') !== -1,
            'requireNumberBetween(1, 3) не найден');
    });

    test('список таб_номер — из листа «Сотрудники» (requireValueInRange)', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        assertTrue(gs.indexOf('requireValueInRange(empRange, true)') !== -1,
            'requireValueInRange не найден');
        assertTrue(gs.indexOf("getSheetByName('Сотрудники')") !== -1,
            'источник списка — лист «Сотрудники»');
    });

    test('запись демо — appendRow из 6 полей (формат addVacation)', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        const ws = fs.readFileSync(wsPath, 'utf8');
        const appendInit = 'appendRow([maxId, row.tab, row.part, row.start, row.end, row.comment])';
        assertTrue(gs.indexOf(appendInit) !== -1, 'appendRow демо не в формате 6 полей');
        // Сервер пишет так же: appendRow([newId, tabNo, part, startDate, endDate, comment])
        assertTrue(ws.indexOf('appendRow([newId, tabNo, part, startDate, endDate, comment])') !== -1,
            'addVacation сменил формат записи — тест устарел');
    });

    test('демо: id продолжается от max id (как addVacation)', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        assertTrue(gs.indexOf('maxId++') !== -1, 'инкремент id не найден');
        const ws = fs.readFileSync(wsPath, 'utf8');
        assertTrue(ws.indexOf('var newId = maxId + 1;') !== -1,
            'addVacation сменил логику max id — тест устарел');
    });

    test('подсветка пересечений периодов одного сотрудника (COUNTIFS)', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        assertTrue(gs.indexOf('COUNTIFS($B$2:$B,$B2') !== -1,
            'COUNTIFS-формула пересечения не найдена');
        assertTrue(gs.indexOf('whenFormulaSatisfied') !== -1,
            'условное форматирование не настроено');
        // Формула пересечения: s1 <= e2 И e1 >= s2
        assertTrue(gs.indexOf('$D$2:$D,"<="&$E2') !== -1 && gs.indexOf('$E$2:$E,">="&$D2') !== -1,
            'условие пересечения интервалов неполное');
    });

    test('инициализатор не пишет данные при повторном запуске (без force)', () => {
        const gs = fs.readFileSync(gsPath, 'utf8');
        // appendRow в VacationsInit.gs — только в vacationsSeedDemo
        const seedStart = gs.indexOf('function vacationsSeedDemo');
        const appendPos = gs.indexOf('sheet.appendRow(');
        assertTrue(seedStart !== -1 && appendPos !== -1 && appendPos > seedStart,
            'appendRow должен использоваться только в vacationsSeedDemo');
    });
});
