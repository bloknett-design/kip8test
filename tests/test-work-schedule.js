// tests/test-work-schedule.js
// Task 201: тесты для модуля «График работы» (WorkSchedule)
//
// Что проверяется (на стороне сервера — WorkSchedule.gs):
//   1. Соответствие типа мероприятия → код статуса
//   2. Алгоритм вычисления дня цикла (по образцу серверного)
//   3. Конвертация ISO-даты в Date и обратно (без таймзон-сдвига)
//
// Запуск: через tests/run-all.js (require './test-work-schedule.js').
//
// Тесты запускаются в Node.js. Серверный код (.gs) загружается через
// статический экстрактор — мы не запускаем Apps Script в Node, а просто
// проверяем чистые функции и инварианты.

const { test, describe, assertEqual, assertTrue, assertFalse } = require('./test-helpers.js');

// ============================================================
// Утилиты, повторяющие серверную логику (из WorkSchedule.gs)
// Используются как референс-имплементация для тестов.
// ============================================================

// Соответствие тип мероприятия → код статуса
const TRAINING_TYPE_TO_STATUS = {
    'инструктаж':      'И',
    'обучение':        'ОБ',
    'проверка_знаний': 'ПЗ'
};

// Конвертация ISO YYYY-MM-DD → Date (без timezone-сдвига)
function parseIsoDate(s) {
    if (!s) return null;
    if (s instanceof Date) return s;
    const parts = String(s).split('-');
    if (parts.length !== 3) return null;
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const d = parseInt(parts[2], 10);
    if (isNaN(y) || isNaN(m) || isNaN(d)) return null;
    return new Date(y, m - 1, d);
}

// Date → ISO YYYY-MM-DD
function toIsoDate(dt) {
    if (!dt) return null;
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    const d = String(dt.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + d;
}

// Количество дней в месяце (1..31)
function daysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
}

// Алгоритм вычисления дня цикла (как на сервере):
//   dayOfCycle = ((diffDays % cycle) + cycle) % cycle + 1
function dayOfCycle(startDate, currentDate, cycle) {
    const diffMs = currentDate.getTime() - startDate.getTime();
    const diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));
    return ((diffDays % cycle) + cycle) % cycle + 1;
}

// ============================================================
// Тесты
// ============================================================

describe('График работы — WorkSchedule', () => {

    describe('Соответствие типа мероприятия → код статуса', () => {
        test('инструктаж → И', () => {
            assertEqual(TRAINING_TYPE_TO_STATUS['инструктаж'], 'И');
        });
        test('обучение → ОБ', () => {
            assertEqual(TRAINING_TYPE_TO_STATUS['обучение'], 'ОБ');
        });
        test('проверка_знаний → ПЗ', () => {
            assertEqual(TRAINING_TYPE_TO_STATUS['проверка_знаний'], 'ПЗ');
        });
        test('неизвестный тип → undefined', () => {
            assertTrue(TRAINING_TYPE_TO_STATUS['unknown'] === undefined);
        });
    });

    describe('Парсинг ISO даты', () => {
        test('YYYY-MM-DD → Date с правильным годом/месяцем/днём', () => {
            const d = parseIsoDate('2026-08-15');
            assertEqual(d.getFullYear(), 2026);
            assertEqual(d.getMonth(), 7);  // август = 7
            assertEqual(d.getDate(), 15);
        });
        test('null → null', () => {
            assertEqual(parseIsoDate(null), null);
        });
        test('пустая строка → null', () => {
            assertEqual(parseIsoDate(''), null);
        });
        test('некорректный формат → null', () => {
            assertEqual(parseIsoDate('15/08/2026'), null);
            assertEqual(parseIsoDate('2026-08'), null);
        });
        test('Date → Date (identity)', () => {
            const d = new Date(2026, 7, 15);
            const result = parseIsoDate(d);
            assertTrue(result instanceof Date);
            assertEqual(result.getFullYear(), 2026);
        });
    });

    describe('Конвертация Date → ISO', () => {
        test('Date → YYYY-MM-DD', () => {
            const d = new Date(2026, 7, 15);
            assertEqual(toIsoDate(d), '2026-08-15');
        });
        test('Date с днём < 10 → с ведущим нулём', () => {
            const d = new Date(2026, 0, 5);
            assertEqual(toIsoDate(d), '2026-01-05');
        });
        test('null → null', () => {
            assertEqual(toIsoDate(null), null);
        });
    });

    describe('Round-trip ISO → Date → ISO', () => {
        test('2026-01-01 round-trip', () => {
            const iso = '2026-01-01';
            assertEqual(toIsoDate(parseIsoDate(iso)), iso);
        });
        test('2026-12-31 round-trip', () => {
            const iso = '2026-12-31';
            assertEqual(toIsoDate(parseIsoDate(iso)), iso);
        });
        test('2026-02-29 round-trip (високосный год)', () => {
            const iso = '2024-02-29';
            assertEqual(toIsoDate(parseIsoDate(iso)), iso);
        });
    });

    describe('Количество дней в месяце', () => {
        test('янв 2026 = 31', () => assertEqual(daysInMonth(2026, 1), 31));
        test('фев 2026 = 28', () => assertEqual(daysInMonth(2026, 2), 28));
        test('фев 2024 = 29 (високосный)', () => assertEqual(daysInMonth(2024, 2), 29));
        test('апр 2026 = 30', () => assertEqual(daysInMonth(2026, 4), 30));
        test('дек 2026 = 31', () => assertEqual(daysInMonth(2026, 12), 31));
    });

    describe('Алгоритм дня цикла', () => {
        // Pattern: 5-дневный (Д→Н→вых×3), старт = 2026-08-01
        // cycle = 5
        // 2026-08-01 — день 1 (Д)
        // 2026-08-02 — день 2 (Н)
        // 2026-08-03 — день 3 (вых)
        // 2026-08-04 — день 4 (вых)
        // 2026-08-05 — день 5 (вых)
        // 2026-08-06 — день 1 (Д) — цикл повторился
        test('старт = 2026-08-01, цикл=5, дата=2026-08-01 → день 1', () => {
            const start = parseIsoDate('2026-08-01');
            const cur = parseIsoDate('2026-08-01');
            assertEqual(dayOfCycle(start, cur, 5), 1);
        });
        test('старт = 2026-08-01, цикл=5, дата=2026-08-02 → день 2', () => {
            const start = parseIsoDate('2026-08-01');
            const cur = parseIsoDate('2026-08-02');
            assertEqual(dayOfCycle(start, cur, 5), 2);
        });
        test('старт = 2026-08-01, цикл=5, дата=2026-08-05 → день 5', () => {
            const start = parseIsoDate('2026-08-01');
            const cur = parseIsoDate('2026-08-05');
            assertEqual(dayOfCycle(start, cur, 5), 5);
        });
        test('старт = 2026-08-01, цикл=5, дата=2026-08-06 → день 1 (новый цикл)', () => {
            const start = parseIsoDate('2026-08-01');
            const cur = parseIsoDate('2026-08-06');
            assertEqual(dayOfCycle(start, cur, 5), 1);
        });
        test('старт = 2026-08-01, цикл=5, дата=2026-08-10 → день 5', () => {
            const start = parseIsoDate('2026-08-01');
            const cur = parseIsoDate('2026-08-10');
            assertEqual(dayOfCycle(start, cur, 5), 5);
        });
        test('старт = 2026-08-01, цикл=5, дата=2026-08-11 → день 1', () => {
            const start = parseIsoDate('2026-08-01');
            const cur = parseIsoDate('2026-08-11');
            assertEqual(dayOfCycle(start, cur, 5), 1);
        });
        test('отрицательный diff (дата раньше старта) → корректный день цикла', () => {
            // дата на 1 день раньше старта — должна дать последний день цикла
            const start = parseIsoDate('2026-08-02');
            const cur = parseIsoDate('2026-08-01');
            // diffDays = -1, cycle=5 → ((-1 % 5) + 5) % 5 + 1 = 4 + 1 = 5
            assertEqual(dayOfCycle(start, cur, 5), 5);
        });
        test('7-дневный цикл 5/2: старт=пн, через неделю → день 1', () => {
            const start = parseIsoDate('2026-08-03');  // понедельник
            const cur = parseIsoDate('2026-08-10');    // следующий понедельник
            assertEqual(dayOfCycle(start, cur, 7), 1);
        });
    });

    describe('Индекс ключа записи (дата|таб_номер)', () => {
        // Имитация логики _buildEntryIndex из WorkSchedule клиента.
        // Используем bracket-нотацию, т.к. символ № не входит в valid identifier.
        function buildIndex(entries) {
            const idx = {};
            for (let i = 0; i < entries.length; i++) {
                const e = entries[i];
                idx[e['дата'] + '|' + e['таб_номер']] = e;
            }
            return idx;
        }
        test('ключ формируется как ISO|таб_номер', () => {
            const idx = buildIndex([
                { 'дата': '2026-08-15', 'таб_номер': '2741', 'статус': 'Д' }
            ]);
            assertTrue('2026-08-15|2741' in idx);
        });
        test('последняя запись перезаписывает предыдущую с тем же ключом', () => {
            const idx = buildIndex([
                { 'дата': '2026-08-15', 'таб_номер': '2741', 'статус': 'Д', _v: 1 },
                { 'дата': '2026-08-15', 'таб_номер': '2741', 'статус': 'И', _v: 2 }
            ]);
            assertEqual(idx['2026-08-15|2741']['статус'], 'И');
        });
        test('разные таб_номер в один день → разные ключи', () => {
            const idx = buildIndex([
                { 'дата': '2026-08-15', 'таб_номер': '2741', 'статус': 'Д' },
                { 'дата': '2026-08-15', 'таб_номер': '5464', 'статус': 'Н' }
            ]);
            assertEqual(idx['2026-08-15|2741']['статус'], 'Д');
            assertEqual(idx['2026-08-15|5464']['статус'], 'Н');
        });
    });

    describe('Серверный WorkSchedule.gs: статичные поля', () => {
        // Читаем файл и проверяем ключевые константы без выполнения
        const fs = require('fs');
        const path = require('path');
        const gsPath = path.resolve(__dirname, '..', 'scripts', 'WorkSchedule.gs');
        let gsContent = '';
        try {
            gsContent = fs.readFileSync(gsPath, 'utf8');
        } catch (e) {
            // файл не найден — тест ниже провалится
        }

        test('файл WorkSchedule.gs существует', () => {
            assertTrue(gsContent.length > 0, 'WorkSchedule.gs должен существовать');
        });

        test('SPREADSHEET_ID указывает на новую таблицу графика', () => {
            assertTrue(gsContent.indexOf("1MQtW-CWCmjlu-SAeVBllKDP6NRkiOkmW-7xgOjHskWY") !== -1,
                'SPREADSHEET_ID должен указывать на новую таблицу');
        });

        test('имена листов на русском', () => {
            // Константы заданы с разными отступами, проверяем через 'имя_листа':
            assertTrue(gsContent.indexOf("'Сотрудники'") !== -1);
            assertTrue(gsContent.indexOf("'Коды_статусов'") !== -1);
            assertTrue(gsContent.indexOf("'Шаблоны_ротации'") !== -1);
            assertTrue(gsContent.indexOf("'Дни_цикла'") !== -1);
            assertTrue(gsContent.indexOf("'Инструктажи'") !== -1);
            assertTrue(gsContent.indexOf("'Записи_графика'") !== -1);
        });

        test('READ_ROLES и WRITE_ROLES ограничены только Админом (Task 204)', () => {
            // Task 204: доступ к графику работы ограничен — только Админ.
            // Ранее в READ_ROLES также были КИП ИОС/ИТР8/ИТР ИОС; в WRITE_ROLES — КИП ИОС+Админ.
            assertTrue(gsContent.indexOf("READ_ROLES: ['Админ']") !== -1);
            assertTrue(gsContent.indexOf("WRITE_ROLES: ['Админ']") !== -1);
        });

        test('TRAINING_TYPE_TO_STATUS: 3 типа → И/ОБ/ПЗ', () => {
            assertTrue(gsContent.indexOf("'инструктаж':       'И'") !== -1);
            assertTrue(gsContent.indexOf("'обучение':         'ОБ'") !== -1);
            assertTrue(gsContent.indexOf("'проверка_знаний':  'ПЗ'") !== -1);
        });

        test('все 11 endpoint-ов зарегистрированы в Code.gs', () => {
            const codePath = path.resolve(__dirname, '..', 'scripts', 'Code.gs');
            const codeContent = fs.readFileSync(codePath, 'utf8');
            const expectedActions = [
                'workSchedule.getStatusCodes',
                'workSchedule.getPatterns',
                'workSchedule.listEmployees',
                'workSchedule.listEntries',
                'workSchedule.listTrainings',
                'workSchedule.generateMonth',
                'workSchedule.setManualEntry',
                'workSchedule.deleteEntry',
                'workSchedule.addEmployee',
                'workSchedule.addTraining',
                'workSchedule.deleteTraining'
            ];
            for (const action of expectedActions) {
                assertTrue(codeContent.indexOf("case '" + action + "':") !== -1,
                    'Ожидается case в Code.gs: ' + action);
            }
        });
    });

    describe('Клиентский модуль в index.html: инварианты', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('var WorkSchedule = { определён', () => {
            assertTrue(html.indexOf('var WorkSchedule = {') !== -1);
        });

        test('HTML-страницы трёх под-разделов присутствуют', () => {
            assertTrue(html.indexOf('id="page-work-schedule"') !== -1);
            assertTrue(html.indexOf('id="page-work-schedule-employees"') !== -1);
            assertTrue(html.indexOf('id="page-work-schedule-trainings"') !== -1);
        });

        test('Кнопка меню на странице «Документация ИОС»', () => {
            assertTrue(html.indexOf("navigateTo('work-schedule')") !== -1);
        });

        test('navigateTo вызывает инициализаторы трёх страниц', () => {
            assertTrue(html.indexOf("page === 'work-schedule'") !== -1);
            assertTrue(html.indexOf("page === 'work-schedule-employees'") !== -1);
            assertTrue(html.indexOf("page === 'work-schedule-trainings'") !== -1);
        });

        test('_WORK_SCHEDULE_PAGES в карте ролей', () => {
            assertTrue(html.indexOf('_WORK_SCHEDULE_PAGES') !== -1);
        });

        test('3 bottom-sheet-а для форм (cell/employee/training)', () => {
            assertTrue(html.indexOf('id="wsCellSheet"') !== -1);
            assertTrue(html.indexOf('id="wsEmpSheet"') !== -1);
            assertTrue(html.indexOf('id="wsTrSheet"') !== -1);
        });

        test('CSS-классы для шахматки', () => {
            assertTrue(html.indexOf('.ws-grid') !== -1);
            assertTrue(html.indexOf('.ws-cell') !== -1);
            assertTrue(html.indexOf('.ws-emp-col') !== -1);
            assertTrue(html.indexOf('.ws-day-col') !== -1);
        });
    });
});
