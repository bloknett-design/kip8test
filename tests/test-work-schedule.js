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

    // ============================================================
    // Task 249: хлебные крошки страниц Графика работы.
    // До фикса: у work-schedule*-страниц не было записей ни в PAGE_PARENTS,
    // ни в PAGE_LABELS → крошки показывали raw id: «Главная / work-schedule».
    // После фикса: «Главная / График работы» (и полные пути у подразделов).
    // Task 267: work-schedule стал подразделом «Документации ИОС» —
    // цепочка стала ПОЛНОЙ: «Главная / Документация / Документация ИОС /
    // График работы» (см. тесты ниже и describe Task 267).
    // ============================================================
    describe('Task 249: крошки «Главная / График работы» вместо raw id', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');
        // Извлекаем блок PAGE_LABELS (regex по всему html цепляет и PAGE_PARENTS,
        // где 'work-schedule': 'dashboard' стоит выше по файлу)
        const labelsMatch = html.match(/const PAGE_LABELS = \{([\s\S]*?)\n    \};/);
        const labels = labelsMatch ? labelsMatch[1] : '';

        test('PAGE_LABELS: метка «График работы» для work-schedule', () => {
            const m = labels.match(/'work-schedule':\s+'([^']+)'/);
            assertTrue(!!m, 'PAGE_LABELS должен содержать запись для work-schedule');
            assertEqual(m[1], 'График работы',
                'Метка work-schedule должна быть «График работы» (не raw id)');
        });

        test('PAGE_LABELS: метки для подразделов (сотрудники/инструктажи)', () => {
            const mEmp = labels.match(/'work-schedule-employees':\s+'([^']+)'/);
            const mTr = labels.match(/'work-schedule-trainings':\s+'([^']+)'/);
            assertTrue(!!mEmp, 'PAGE_LABELS должен содержать запись для work-schedule-employees');
            assertTrue(!!mTr, 'PAGE_LABELS должен содержать запись для work-schedule-trainings');
            assertEqual(mEmp[1], 'Сотрудники',
                'Метка work-schedule-employees должна совпадать с заголовком страницы');
            assertEqual(mTr[1], 'Инструктажи и обучения',
                'Метка work-schedule-trainings должна совпадать с заголовком страницы');
        });

        test('PAGE_LABELS: метки не дублируются (единственная запись на страницу)', () => {
            const countMain = (labels.match(/'work-schedule':\s+'/g) || []).length;
            const countEmp = (labels.match(/'work-schedule-employees':\s+'/g) || []).length;
            const countTr = (labels.match(/'work-schedule-trainings':\s+'/g) || []).length;
            assertEqual(countMain, 1, 'Ровно одна запись work-schedule в PAGE_LABELS');
            assertEqual(countEmp, 1, 'Ровно одна запись work-schedule-employees в PAGE_LABELS');
            assertEqual(countTr, 1, 'Ровно одна запись work-schedule-trainings в PAGE_LABELS');
        });

        test('PAGE_PARENTS: work-schedule — подраздел «Документации ИОС» (Task 267)', () => {
            // Task 249: был корневым ('dashboard'). Task 267: полная цепочка
            // крошек — «Главная / Документация / Документация ИОС / График
            // работы» (кнопка раздела живёт на page-docs-ios, рядом с
            // «Расходомерами хозрасчётными» — их цепочка построена так же)
            const re = /'work-schedule':\s+'docs-ios'/;
            assertTrue(re.test(html),
                'PAGE_PARENTS должен содержать work-schedule → docs-ios (полная цепочка крошек, Task 267)');
        });

        test('PAGE_PARENTS: подразделы с родителем work-schedule', () => {
            const reEmp = /'work-schedule-employees':\s+'work-schedule'/;
            const reTr = /'work-schedule-trainings':\s+'work-schedule'/;
            assertTrue(reEmp.test(html),
                'PAGE_PARENTS: work-schedule-employees → work-schedule (путь «Главная / График работы / Сотрудники»)');
            assertTrue(reTr.test(html),
                'PAGE_PARENTS: work-schedule-trainings → work-schedule (путь «Главная / График работы / Инструктажи и обучения»)');
        });

        test('buildBreadcrumbPath: путь work-schedule = [docs, docs-ios, work-schedule] (Task 267)', () => {
            // Симуляция buildBreadcrumbPath с PAGE_PARENTS из index.html:
            // извлекаем карту и поднимаемся от work-schedule до dashboard.
            const mapMatch = html.match(/const PAGE_PARENTS = \{([\s\S]*?)\n    \};/);
            assertTrue(!!mapMatch, 'PAGE_PARENTS должен существовать в index.html');
            const entries = {};
            const re = /'([a-z0-9-]+)':\s+'([a-z0-9-]+)'/g;
            let mm;
            while ((mm = re.exec(mapMatch[1])) !== null) {
                if (!(mm[1] in entries)) entries[mm[1]] = mm[2]; // первая запись приоритетна
            }
            // Путь от work-schedule вверх
            const path = [];
            let cur = 'work-schedule';
            const visited = new Set();
            while (cur && cur !== 'dashboard' && !visited.has(cur)) {
                visited.add(cur);
                path.unshift(cur);
                cur = entries[cur] || null;
            }
            // Task 267: полная цепочка — Документация → Документация ИОС → График работы
            assertEqual(path.length, 3,
                'Путь work-schedule — три сегмента (полная цепочка, Task 267)');
            assertEqual(path[0], 'docs');
            assertEqual(path[1], 'docs-ios');
            assertEqual(path[2], 'work-schedule');
        });

        test('buildBreadcrumbPath: путь work-schedule-employees = [docs, docs-ios, work-schedule, work-schedule-employees] (Task 267)', () => {
            const mapMatch = html.match(/const PAGE_PARENTS = \{([\s\S]*?)\n    \};/);
            assertTrue(!!mapMatch, 'PAGE_PARENTS должен существовать в index.html');
            const entries = {};
            const re = /'([a-z0-9-]+)':\s+'([a-z0-9-]+)'/g;
            let mm;
            while ((mm = re.exec(mapMatch[1])) !== null) {
                if (!(mm[1] in entries)) entries[mm[1]] = mm[2];
            }
            const path = [];
            let cur = 'work-schedule-employees';
            const visited = new Set();
            while (cur && cur !== 'dashboard' && !visited.has(cur)) {
                visited.add(cur);
                path.unshift(cur);
                cur = entries[cur] || null;
            }
            // Task 267: четыре сегмента — Главная / Документация /
            // Документация ИОС / График работы / Сотрудники
            assertEqual(path.length, 4,
                'Путь work-schedule-employees — четыре сегмента через docs → docs-ios → work-schedule');
            assertEqual(path[0], 'docs');
            assertEqual(path[1], 'docs-ios');
            assertEqual(path[2], 'work-schedule');
            assertEqual(path[3], 'work-schedule-employees');
        });

        test('Метки совпадают с заголовками страниц (page-inline-header-title)', () => {
            // Заголовок страницы — источник истины для метки крошек
            assertTrue(html.indexOf('<div class="page-inline-header-title">График работы</div>') !== -1,
                'Заголовок страницы work-schedule — «График работы»');
            assertTrue(html.indexOf('<div class="page-inline-header-title">Сотрудники</div>') !== -1,
                'Заголовок страницы work-schedule-employees — «Сотрудники»');
            assertTrue(html.indexOf('<div class="page-inline-header-title">Инструктажи и обучения</div>') !== -1,
                'Заголовок страницы work-schedule-trainings — «Инструктажи и обучения»');
        });

        // Task 249: SW-тест версии v508 удалён — версия v509 введена в
        // Task 250 (см. describe ниже). Историческая заметка.
    });

    // ============================================================
    // Task 250: десктопная версия «Графика работы»:
    //   1) коды статусов убраны (из ячеек и легенды);
    //   2) фон ячеек шахматки непрозрачный (было transparent у пустых);
    //   3) дашборд автоматически подгоняется по ширине экрана
    //      приложения, без горизонтальной прокрутки.
    // ============================================================
    describe('Task 250: коды статусов убраны из ячеек и легенды', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        // Task 252: тесты «код не выводится в ячейке» и «легенда без
        // кодов» удалены — Task 252 вернул коды в ячейки и убрал легенду
        // целиком (см. describe Task 252 ниже). Историческая заметка.

        test('JS: tooltip показывает название статуса, а не код', () => {
            assertTrue(html.indexOf("var statusName = status;") !== -1,
                'Должна быть переменная statusName (поиск названия по коду)');
            assertTrue(html.indexOf("titleParts.push('статус: ' + (statusName || '—'));") !== -1,
                'Tooltip: «статус: <название>» вместо кода');
        });

        test('JS: переработка — класс ws-overtime (маркер-точка вместо underline)', () => {
            assertTrue(html.indexOf("if (isOvertime) classes.push('ws-overtime');") !== -1,
                'Переработка должна добавлять класс ws-overtime');
            assertTrue(html.indexOf("text-decoration:underline;") === -1,
                'Прежний underline текста кода должен быть удалён (текста в ячейке нет)');
        });
    });

    describe('Task 250: фон ячеек шахматки непрозрачный', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('JS: inline-фон «transparent» убран из _renderCell', () => {
            assertTrue(html.indexOf(": 'transparent'") === -1,
                'Пустые ячейки не должны получать inline transparent-фон');
            // Статусные ячейки — inline цвет; пустые — CSS-фон
            assertTrue(html.indexOf("if (status) style += 'background:' + color + ';';") !== -1,
                'Inline-фон задаётся только статусным ячейкам (цвет справочника)');
        });

        test('CSS: сплошной фон ячеек (.ws-grid tbody td.ws-cell)', () => {
            const re = /\.ws-grid tbody td\.ws-cell \{[^}]*background:\s*var\(--bg-primary, #1a2233\);[^}]*\}/;
            assertTrue(re.test(html),
                'Ячейки должны иметь сплошной (непрозрачный) CSS-фон в тёмной теме');
        });

        test('CSS: сплошной фон ячеек в светлой теме', () => {
            const re = /\[data-theme="light"\] \.ws-grid tbody td\.ws-cell \{[^}]*background:\s*#eef0f2;[^}]*\}/;
            assertTrue(re.test(html),
                'Светлая тема: сплошной фон пустых ячеек (#eef0f2)');
        });

        test('CSS: маркер переработки — точка ::after в углу ячейки', () => {
            const re = /\.ws-grid tbody td\.ws-cell\.ws-overtime::after \{[^}]*border-radius:\s*50%;[^}]*\}/;
            assertTrue(re.test(html),
                'ws-overtime::after — круглая точка (маркер переработки)');
        });
    });

    describe('Task 250: десктоп — вся ширина экрана, без прокрутки', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: table-layout: fixed + width: 100% для шахматки (≥1024px)', () => {
            assertTrue(html.indexOf('#page-work-schedule .ws-grid {\n            width: 100%;') !== -1,
                'Таблица должна занимать 100% ширины контейнера');
            assertTrue(html.indexOf('table-layout: fixed;') !== -1,
                'table-layout: fixed — колонки дней делят ширину поровну');
        });

        test('CSS: горизонтальная прокрутка отключена на десктопе', () => {
            const re = /@media \(min-width: 1024px\) \{[^@]*?#page-work-schedule \.ws-grid-wrap \{\s*\n\s*overflow-x: hidden;/;
            assertTrue(re.test(html),
                '.ws-grid-wrap на десктопе — overflow-x: hidden (без прокрутки)');
        });

        test('CSS: колонка сотрудников фиксирована, дни делят остаток', () => {
            assertTrue(html.indexOf('#page-work-schedule .ws-grid thead th.ws-emp-col {\n            width: 200px;') !== -1,
                'Колонка сотрудников — фиксированная ширина (200px)');
            const reDay = /#page-work-schedule \.ws-grid thead th\.ws-day-col \{[^}]*width:\s*auto;[^}]*min-width:\s*0;/;
            assertTrue(reDay.test(html),
                'Колонки дней: width auto + min-width 0 (делят остаток ширины)');
        });

        test('CSS: ФИО — эллипсис в фиксированной колонке', () => {
            const re = /#page-work-schedule \.ws-grid tbody td\.ws-emp-col \{[^}]*overflow:\s*hidden;[^}]*text-overflow:\s*ellipsis;/;
            assertTrue(re.test(html),
                'Длинные ФИО обрезаются эллипсисом, не растягивая таблицу');
        });

        // Task 250: SW-тест версии v509 удалён — версия v510 введена в
        // Task 251 (см. describe ниже). Историческая заметка.
    });

    // ============================================================
    // Task 251: переделанный ввод статусов в шахматке:
    //   1) клик по ячейке → попап-табличка «код — название» рядом с ячейкой;
    //   2) выбор статуса отображается в ячейке ЛОКАЛЬНО (накопление в
    //      _PENDING), мгновенной передачи на сервер НЕТ;
    //   3) кнопка «Сохранить» — пакетная отправка всех изменений на сервер
    //      (setManualEntry/deleteEntry) с последующей синхронизацией
    //      (loadGrid перечитывает данные из БД).
    // ============================================================
    describe('Task 251: попап выбора статуса рядом с ячейкой', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('HTML: элементы попапа (#wsCellPopup + #wsPopupCloser) существуют', () => {
            assertTrue(html.indexOf('id="wsCellPopup"') !== -1,
                'Должен быть контейнер попапа #wsCellPopup');
            assertTrue(html.indexOf('id="wsPopupCloser"') !== -1,
                'Должен быть прозрачный клик-ловец #wsPopupCloser (закрытие по клику мимо)');
        });

        test('JS: клик по ячейке вызывает onCellClick (не openCellForm)', () => {
            // В HTML onclick собирается в JS-строке: onCellClick(event, \'...\')
            assertTrue(html.indexOf("WorkSchedule.onCellClick(event, \\\''") !== -1,
                'onclick ячейки должен открывать попап: onCellClick(event, ...)');
            // Старый мгновенно-сохраняющий обработчик в ячейках удалён
            assertTrue(html.indexOf("WorkSchedule.openCellForm(\\'") === -1,
                'openCellForm не должен вызываться напрямую из onclick ячейки');
        });

        test('JS: попап рендерит строки «код + название» столбиком', () => {
            assertTrue(html.indexOf("WorkSchedule.onPopupStatus(\\'") !== -1,
                'Строки попапа: клик → onPopupStatus(код)');
            assertTrue(html.indexOf('<span class="ws-popup-code">') !== -1,
                'Код статуса в попапе (.ws-popup-code)');
            assertTrue(html.indexOf('<span class="ws-popup-name">') !== -1,
                'Название статуса в попапе (.ws-popup-name)');
            assertTrue(html.indexOf('>выходной</span>') !== -1,
                'Строка «— выходной —» для очистки ячейки');
        });

        test('JS: строка «Дополнительно…» открывает sheet расширенной правки', () => {
            assertTrue(html.indexOf('onclick="WorkSchedule.onPopupMore()">Дополнительно…') !== -1,
                'Попап должен содержать «Дополнительно…» → onPopupMore → openCellForm');
        });

        test('CSS: попап — фиксированное позиционирование + строки столбиком', () => {
            const reFixed = /\.ws-cell-popup \{[^}]*position:\s*fixed;/;
            assertTrue(reFixed.test(html),
                '.ws-cell-popup — position: fixed (позиция у ячейки через JS)');
            const reRow = /\.ws-popup-row \{[^}]*display:\s*flex;/;
            assertTrue(reRow.test(html),
                '.ws-popup-row — flex-строки (табличка код—название столбиком)');
        });
    });

    describe('Task 251: накопление правок без мгновенной отправки', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('JS: буфер _PENDING в состоянии модуля', () => {
            assertTrue(html.indexOf('_PENDING: {},') !== -1,
                'Модуль должен содержать _PENDING — буфер локальных правок');
        });

        test('JS: onPopupStatus применяет статус ЛОКАЛЬНО (без _api)', () => {
            // Извлекаем метод onPopupStatus и проверяем: _applyCellStatus +
            // _renderGrid, и НЕТ вызова _api (мгновенной отправки нет)
            const m = html.match(/onPopupStatus: function\(code\) \{[\s\S]*?\n        \},/);
            assertTrue(!!m, 'Метод onPopupStatus должен существовать');
            const body = m[0];
            assertTrue(body.indexOf('this._applyCellStatus(') !== -1,
                'onPopupStatus должен применять статус через _applyCellStatus');
            assertTrue(body.indexOf('this._renderGrid();') !== -1,
                'onPopupStatus должен перерисовывать сетку (статус сразу в ячейке)');
            assertTrue(body.indexOf('_api(') === -1,
                'onPopupStatus НЕ должен вызывать _api — мгновенной отправки быть не должно');
        });

        test('JS: _applyCellStatus не обращается к серверу', () => {
            const m = html.match(/_applyCellStatus: function\(isoDate, tabNo, code\) \{[\s\S]*?\n        \},/);
            assertTrue(!!m, 'Метод _applyCellStatus должен существовать');
            assertTrue(m[0].indexOf('_api(') === -1,
                '_applyCellStatus — только локальный _PENDING, без сервера');
            assertTrue(m[0].indexOf('__delete: true') !== -1,
                '_applyCellStatus должен уметь планировать удаление (__delete)');
        });

        test('JS: «выходной» на ручной записи → __delete; на авто — тост', () => {
            const m = html.match(/_applyCellStatus: function\(isoDate, tabNo, code\) \{[\s\S]*?\n        \},/);
            const body = m[0];
            assertTrue(body.indexOf("server.источник === 'руч') {") !== -1 &&
                       body.indexOf('__delete: true') !== -1,
                'Очистка ручной записи → __delete (удаление при сохранении)');
            assertTrue(body.indexOf('Нельзя очистить авто-запись') !== -1,
                'Очистка авто-записи → тост-отказ (сервер запрещает deleteEntry для авто)');
        });

        test('JS: submitCellForm накапливает локально (без setManualEntry)', () => {
            const m = html.match(/submitCellForm: function\(\) \{[\s\S]*?\n        \},/);
            assertTrue(!!m, 'Метод submitCellForm должен существовать');
            assertTrue(m[0].indexOf('_setPendingCell(') !== -1,
                'submitCellForm должен писать в _PENDING (локально)');
            assertTrue(m[0].indexOf('setManualEntry') === -1,
                'submitCellForm НЕ должен вызывать setManualEntry напрямую');
        });

        test('JS: рендер ячейки учитывает pending (класс ws-pending)', () => {
            assertTrue(html.indexOf("if (isPending) classes.push('ws-pending');") !== -1,
                'Ячейка с несохранённой правкой — класс ws-pending');
            const re = /\.ws-grid tbody td\.ws-cell\.ws-pending \{[^}]*outline:\s*2px dashed/;
            assertTrue(re.test(html),
                'CSS: ws-pending — пунктирная рамка (маркер несохранённой ячейки)');
            assertTrue(html.indexOf("if (isPending) titleParts.push('не сохранено');") !== -1,
                'Tooltip несохранённой ячейки — «не сохранено»');
        });

        test('JS: _renderGrid накладывает _PENDING на серверные данные', () => {
            const re = /var pending = this\._PENDING\[key\] \|\| null;/;
            assertTrue(re.test(html),
                '_renderGrid должен читать _PENDING для каждой ячейки');
            assertTrue(html.indexOf('Object.assign({}, entry || {}, pending,') !== -1,
                'Слияние: pending перекрывает серверную запись (эффективное состояние)');
        });
    });

    describe('Task 251: кнопка «Сохранить» — пакетная отправка и синхронизация', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('HTML: кнопка #wsSaveBtn в тулбаре', () => {
            const re = /<button type="button" id="wsSaveBtn" class="ws-save-btn" onclick="WorkSchedule\.saveAll\(\)" hidden>Сохранить<\/button>/;
            assertTrue(re.test(html),
                'Кнопка «Сохранить» (saveAll) должна быть в тулбаре, скрыта по умолчанию');
        });

        test('JS: _updateSaveBtn — счётчик правок и скрытие при нуле', () => {
            const m = html.match(/_updateSaveBtn: function\(\) \{[\s\S]*?\n        \},/);
            assertTrue(!!m, 'Метод _updateSaveBtn должен существовать');
            assertTrue(m[0].indexOf('btn.hidden = !this._canEdit || n === 0;') !== -1,
                'Кнопка скрыта без прав или без правок');
            assertTrue(m[0].indexOf("'Сохранить (' + n + ')'") !== -1,
                'Текст кнопки — со счётчиком правок');
        });

        test('JS: saveAll отправляет setManualEntry и deleteEntry', () => {
            const m = html.match(/saveAll: function\(\) \{[\s\S]*?\n        \},/);
            assertTrue(!!m, 'Метод saveAll должен существовать');
            assertTrue(m[0].indexOf("self._api('workSchedule.deleteEntry', payload)") !== -1,
                'saveAll: pending __delete → deleteEntry');
            assertTrue(m[0].indexOf("self._api('workSchedule.setManualEntry', payload)") !== -1,
                'saveAll: правка статуса → setManualEntry');
        });

        test('JS: saveAll синхронизируется — loadGrid после отправки', () => {
            const m = html.match(/saveAll: function\(\) \{[\s\S]*?\n        \},/);
            assertTrue(m[0].indexOf('self.loadGrid();') !== -1,
                'После пакетной отправки — loadGrid (перечитать данные из БД)');
        });

        test('JS: успешные правки удаляются из _PENDING, ошибки остаются', () => {
            const m = html.match(/saveAll: function\(\) \{[\s\S]*?\n        \},/);
            assertTrue(m[0].indexOf('delete self._PENDING[key];') !== -1,
                'Успешная отправка — правка удаляется из _PENDING');
            assertTrue(m[0].indexOf('failCount++;') !== -1,
                'Ошибка отправки — правка остаётся в _PENDING (можно повторить)');
        });

        test('JS: защита от повторного запуска (_saving)', () => {
            const m = html.match(/saveAll: function\(\) \{[\s\S]*?\n        \},/);
            assertTrue(m[0].indexOf('if (this._saving) return;') !== -1,
                'saveAll должен игнорировать повторный клик во время сохранения');
        });

        test('JS: Esc закрывает попап, beforeunload предупреждает о правках', () => {
            assertTrue(html.indexOf("if (ev.key === 'Escape') selfOnce.closeCellPopup();") !== -1,
                'Esc должен закрывать попап');
            assertTrue(html.indexOf("Object.keys(selfOnce._PENDING).length > 0") !== -1,
                'beforeunload должен предупреждать при несохранённых правках');
        });

        // Task 252: SW-тест версии v510 удалён — версия v511 введена в
        // Task 252 (см. describe ниже). Историческая заметка.
    });

    // ============================================================
    // Task 252: «График работы» — чистка десктопного дашборда:
    //   1) легенды под шахматкой убраны совсем (HTML/CSS/JS);
    //   2) шахматка растянута до самого низа окна (десктоп ≥1024px):
    //      страница — flex-колонка, ws-grid-wrap flex:1 + скролл,
    //      таблица height:100% — строки делят свободную высоту;
    //   3) тулбар с кнопками — на всю ширину, ровно между баром
    //      хлебных крошек (page-inline-header) и графиком;
    //   4) коды статусов ВЕРНУТЫ в ячейки шахматки (цвет + код,
    //      как до Task 250; непрозрачный фон Task 250 сохранён).
    // ============================================================
    describe('Task 252: легенда под шахматкой полностью убрана', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('HTML: элемент #wsLegend удалён со страницы', () => {
            assertTrue(html.indexOf('id="wsLegend"') === -1,
                'Контейнер легенды #wsLegend не должен существовать');
            assertTrue(html.indexOf('class="ws-legend"') === -1,
                'Элемент .ws-legend не должен существовать');
        });

        test('JS: метод _renderLegend удалён из модуля WorkSchedule', () => {
            assertTrue(html.indexOf('_renderLegend') === -1,
                'Ни метод, ни вызов _renderLegend не должны остаться в коде');
        });

        test('CSS: правила .ws-legend / .ws-legend-item / .ws-legend-swatch удалены', () => {
            const reItem = /\.ws-legend-item\s*\{/;
            const reSwatch = /\.ws-legend-swatch\s*\{/;
            const reBlock = /\.ws-legend\s*\{/;
            assertTrue(!reBlock.test(html) && !reItem.test(html) && !reSwatch.test(html),
                'CSS-правила легенды должны быть удалены (вместо них — комментарий Task 252)');
        });
    });

    describe('Task 252: коды статусов возвращены в ячейки', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('JS: в ячейке выводится код статуса (status || «·»)', () => {
            // Реверс Task 250: снова (status || '·') — код буквой в ячейке
            assertTrue(html.indexOf("(status || '·')") !== -1,
                'Код статуса должен выводиться в ячейке (паттерн (status || \'·\'))');
            assertTrue(html.indexOf("(status ? '' : '·')") === -1,
                'Паттерн Task 250 «статусная ячейка без текста» должен быть удалён');
        });

        test('JS: непрозрачный фон Task 250 сохранён (CSS-фон + inline для статусных)', () => {
            const re = /\.ws-grid tbody td\.ws-cell \{[^}]*background:\s*var\(--bg-primary, #1a2233\);/;
            assertTrue(re.test(html),
                'Сплошной CSS-фон пустых ячеек должен остаться');
            assertTrue(html.indexOf("if (status) style += 'background:' + color + ';';") !== -1,
                'Inline-фон задаётся только статусным ячейкам');
        });

        test('JS: tooltip и маркеры Task 250/251 не тронуты', () => {
            assertTrue(html.indexOf("titleParts.push('статус: ' + (statusName || '—'));") !== -1,
                'Tooltip: «статус: <название>» (Task 250) — на месте');
            assertTrue(html.indexOf("if (isOvertime) classes.push('ws-overtime');") !== -1,
                'Маркер переработки ws-overtime (Task 250) — на месте');
            assertTrue(html.indexOf("if (isPending) classes.push('ws-pending');") !== -1,
                'Маркер несохранённой правки ws-pending (Task 251) — на месте');
        });
    });

    describe('Task 252: десктоп — график до самого низа, тулбар между крошками и графиком', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: страница — flex-колонка на всю высоту (≥1024px)', () => {
            const re = /#contentArea > #page-work-schedule\.active \{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;[^}]*\}/;
            assertTrue(re.test(html),
                '#page-work-schedule.active — flex-колонка (крошки → тулбар → шахматка)');
            const rePad = /#contentArea > #page-work-schedule\.active \{[^}]*padding-bottom:\s*0;/;
            assertTrue(rePad.test(html),
                'Мобильный нижний отступ ~70px убран на десктопе');
        });

        test('CSS: бары (крошки + тулбар) не сжимаются — тулбар во всю ширину между ними', () => {
            const re = /#page-work-schedule \.page-inline-header,\s*\n\s*#page-work-schedule \.ws-toolbar \{[^}]*flex-shrink:\s*0;/;
            assertTrue(re.test(html),
                'page-inline-header и ws-toolbar — flex-shrink: 0 (бары фиксированной высоты, тулбар между крошками и графиком)');
        });

        test('CSS: шахматка занимает остаток высоты и скроллится сама', () => {
            const re = /#page-work-schedule \.ws-grid-wrap \{[^}]*flex:\s*1;[^}]*min-height:\s*0;[^}]*overflow-y:\s*auto;[^}]*\}/;
            assertTrue(re.test(html),
                '.ws-grid-wrap: flex:1 + min-height:0 + overflow-y:auto — график занимает всё место до низа');
        });

        test('CSS: график до низа окна — Task 256: целые высоты строк вместо height:100%', () => {
            // Task 252 растягивал таблицу height:100% — браузер раздавал
            // строкам ДРОБНЫЕ высоты (60.2px), из-за чего 1px границы
            // «растворялись» антиалиасингом (Task 256). Теперь высоты
            // строк задаёт _fitGrid целыми пикселями, таблица по-прежнему
            // до нижнего края (сумма строк = высота области).
            const re = /#page-work-schedule \.ws-grid \{[^}]*height:\s*auto;[^}]*\}/;
            const reVar = /#page-work-schedule \.ws-grid tbody td \{[^}]*height:\s*var\(--ws-row-h,\s*32px\);[^}]*\}/;
            assertTrue(re.test(html) && reVar.test(html),
                '.ws-grid: height:auto + --ws-row-h (целые высоты строк, до низа окна)');
        });

        test('CSS: шапка таблицы компактная (не тянется вместе со строками)', () => {
            const re = /#page-work-schedule \.ws-grid thead th \{[^}]*height:\s*32px;/;
            assertTrue(re.test(html),
                'thead th: height 32px — шапка не растягивается пропорционально строкам');
        });

        // Task 252: SW-тест версии v511 удалён — версия v512 введена в
        // Task 254 (см. describe ниже). Историческая заметка.
    });

    // ============================================================
    // Task 254: визуальная разметка шахматки:
    //   1) пустые ячейки выходных (Сб/Вс) — слабый пастельно-розовый фон;
    //   2) красные линии-границы между колонками выходных и рабочих
    //      дней (слева от субботы, справа от воскресенья) — непрерывные,
    //      от шапки до последней строки;
    //   3) под ФИО сотрудника — строка с должностью
    //      («Слесарь КИПиА дневной» / «Слесарь КИПиА смена №1»);
    //   4) тулбар с кнопками — непрозрачный фон, кнопки без скруглений.
    // ============================================================
    describe('Task 254: розовый фон пустых ячеек выходных дней', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: .ws-weekend.ws-status-empty — розовый фон (тёмная тема)', () => {
            const re = /\.ws-grid tbody td\.ws-cell\.ws-weekend\.ws-status-empty \{[^}]*background:\s*#6e4250;[^}]*\}/;
            assertTrue(re.test(html),
                'Пустые ячейки выходных — сплошной пыльно-розовый фон (#6e4250)');
        });

        test('CSS: светлая тема — слабый пастельный розовый (#f7d9e3)', () => {
            const re = /\[data-theme="light"\] \.ws-grid tbody td\.ws-cell\.ws-weekend\.ws-status-empty \{[^}]*background:\s*#f7d9e3;/;
            assertTrue(re.test(html),
                'Светлая тема: пастельно-розовый фон пустых ячеек выходных');
        });

        test('JS: _renderCell помечает нерабочие дни классом ws-weekend', () => {
            // Task 260: выходные определяются по производственному
            // календарю (Сб/Вс + праздники + переносы, без рабочих суббот)
            assertTrue(html.indexOf("if (dayOff) classes.push('ws-weekend');") !== -1,
                'Нерабочие дни (Сб/Вс + праздники + переносы) — класс ws-weekend');
        });

        test('CSS: розовый ТОЛЬКО у пустых ячеек (комбинация с ws-status-empty)', () => {
            // Селектор требует ОБА класса: у статусных ячеек выходного
            // (Д/Н/Б…) цвета справочника остаются
            assertTrue(html.indexOf('.ws-grid tbody td.ws-cell.ws-weekend.ws-status-empty {') !== -1,
                'Селектор розового фона — строго .ws-weekend.ws-status-empty');
            assertTrue(html.indexOf("if (status) style += 'background:' + color + ';';") !== -1,
                'Inline-фон статусных ячеек сохранён (Task 250/252)');
        });
    });

    describe('Task 254 + Task 255: линии-границы выходных и рабочих дней', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: границы 1px приглушённые (#cc6e73) — только в tbody', () => {
            // Task 255: тоньше (1px вместо 2px), приглушённее (#cc6e73
            // вместо яркого #e53935), из шапки (thead) убраны.
            const reL = /\.ws-grid tbody td\.ws-cell\.ws-boundary-left,\s*\n\s*\.ws-grid tbody td\.ws-cell\.ws-boundary-before \{ border-left: 1px solid #cc6e73; \}/;
            const reR = /\.ws-grid tbody td\.ws-cell\.ws-boundary-right,\s*\n\s*\.ws-grid tbody td\.ws-cell\.ws-boundary-after \{ border-right: 1px solid #cc6e73; \}/;
            assertTrue(reL.test(html) && reR.test(html),
                'Линии — 1px #cc6e73, парные классы left/before + right/after (tbody)');
            const oldBright = /\.ws-grid[^{]*\{[^}]*#e53935/;
            assertTrue(!oldBright.test(html),
                'Яркий #e53935 больше не используется для линий-границ');
        });

        test('CSS: специфичность границ выше светлой темы (не перекрасится)', () => {
            // Светлая тема задаёт [data-theme="light"] .ws-grid tbody td
            // { border-color } со специфичностью (0,2,2) НИЖЕ по файлу.
            // Граничные селекторы обязаны быть сильнее: + .ws-cell → (0,3,2).
            const re = /\.ws-grid tbody td\.ws-cell\.ws-boundary-after \{ border-right: 1px solid #cc6e73; \}/;
            assertTrue(re.test(html),
                'Селектор td.ws-cell.ws-boundary-after — красная граница переживает светлую тему');
            const weak = /\.ws-grid tbody td\.ws-boundary-\w+ \{/;
            assertTrue(!weak.test(html),
                'Слабый селектор (без .ws-cell) удалён — иначе светлая тема перекрасит границу');
        });

        test('CSS: в шапке (thead) граничных селекторов больше нет', () => {
            // Task 255: линии убраны из шапки графика — только тело таблицы.
            const thBoundary = /\.ws-grid thead th[^{]*ws-boundary/;
            assertTrue(!thBoundary.test(html),
                'Граничные селекторы не должны затрагивать thead (шапка без линий)');
        });

        test('JS: обе стороны стыка — по производственному календарю', () => {
            // Task 260 (развитие Tasks 254/255): стык определяется между
            // соседними рабочим и нерабочим днём ПО КАЛЕНДАРЮ, а не по
            // дню недели (праздники в будни тоже дают красную границу).
            // При 1px в border-collapse цвет общей грани равных границ
            // браузер может взять у соседа — красной делается ОБЕ стороны.
            assertTrue(html.indexOf("var dayOff = this._calDayOff(day);") !== -1,
                '_renderCell определяет нерабочий день через _calDayOff');
            assertTrue(html.indexOf("if (dayOff && day > 1 && !this._calDayOff(day - 1)) classes.push('ws-boundary-left');") !== -1,
                'Первый нерабочий день блока — ws-boundary-left');
            assertTrue(html.indexOf("if (dayOff && day < lastDay && !this._calDayOff(day + 1)) classes.push('ws-boundary-right');") !== -1,
                'Последний нерабочий день блока — ws-boundary-right');
            assertTrue(html.indexOf("if (!dayOff && day < lastDay && this._calDayOff(day + 1)) classes.push('ws-boundary-after');") !== -1,
                'Последний рабочий день перед блоком — ws-boundary-after');
            assertTrue(html.indexOf("if (!dayOff && day > 1 && this._calDayOff(day - 1)) classes.push('ws-boundary-before');") !== -1,
                'Первый рабочий день после блока — ws-boundary-before');
            const reLast = /var lastDay = new Date\(this\._year, this\._month, 0\)\.getDate\(\);/;
            assertTrue(reLast.test(html),
                'lastDay вычисляется один раз для обеих проверок');
        });

        test('JS: шапка таблицы — граничные классы НЕ ставятся', () => {
            // Task 255: из шапки линии убраны — thCls больше не получает
            // ws-boundary-*, остаются ws-day-col + ws-holiday (+ ws-feast
            // Task 260 — праздник по производственному календарю).
            assertTrue(html.indexOf("thCls += ' ws-boundary-left'") === -1 &&
                       html.indexOf("thCls += ' ws-boundary-right'") === -1,
                'Шапка: граничные классы удалены из рендера th');
            const reTh = /var thCls = 'ws-day-col' \+ \(isOff \? ' ws-holiday' : ''\) \+/;
            assertTrue(reTh.test(html),
                'Шапка: thCls формируется из ws-day-col + ws-holiday (+ ws-feast)');
        });
    });

    describe('Task 254 + Task 255: должность и режим занятости под ФИО', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('JS: _posLabel — должность + тип (столбец C) + смена №N (столбец D)', () => {
            // Данные таблицы «Сотрудники» файла табель_КИП_ИОС: столбец C —
            // тип (сменный/дневной), столбец D — номер смены. Формирование:
            // «Слесарь КИПиА смена №1» / «Слесарь КИПиА дневной».
            const re = /_posLabel: function\(emp\) \{[\s\S]*?if \(tip === 'сменный'\) \{[\s\S]*?' смена №' \+ smena[\s\S]*?\} else if \(tip === 'дневной'\) \{[\s\S]*?' дневной';[\s\S]*?\}/;
            assertTrue(re.test(html),
                'Хелпер _posLabel формирует «… смена №N» / «… дневной»');
            const reRange = /smena >= 1 && smena <= 5/;
            assertTrue(reRange.test(html),
                'Смена выводится только при корректном номере 1..5');
        });

        test('JS: колонка сотрудника — ws-emp-pos с подписью _posLabel', () => {
            assertTrue(html.indexOf("var empPosLabel = this._posLabel(emp);") !== -1 &&
                       html.indexOf("'<div class=\"ws-emp-pos\">' + this._esc(empPosLabel) + '</div>'") !== -1,
                'Подпись в .ws-emp-pos формируется через _posLabel (должность + режим)');
            assertTrue(html.indexOf('<div class="ws-emp-name">') !== -1,
                'ФИО переносится в блок .ws-emp-name (две строки в колонке)');
        });

        test('JS: пустая подпись — строка не рендерится', () => {
            const re = /var empPosLabel = this\._posLabel\(emp\);\s*\n\s*var empPos = empPosLabel\s*\n\s*\? '<div class="ws-emp-pos">'/;
            assertTrue(re.test(html),
                'Тернарник: без должности И типа нет пустого блока .ws-emp-pos');
        });

        test('JS: справочник «Сотрудники» — смена в подписи должности (единый формат)', () => {
            // Task 255: в карточках справочника фрагмент «· смена N» убран,
            // смена (столбец D) входит в подпись должности справа от неё.
            assertTrue(html.indexOf("var posLabel = this._posLabel(e);") !== -1 &&
                       html.indexOf("(posLabel ? ' · ' + this._esc(posLabel) : '')") !== -1,
                'Карточка: подпись _posLabel справа от тега типа');
            assertTrue(html.indexOf("· смена ' + e.смена") === -1 &&
                       html.indexOf('· смена не задана') === -1,
                'Дублирующий отдельный фрагмент смены удалён');
        });

        test('CSS: .ws-emp-pos — мелкий приглушённый текст с эллипсисом', () => {
            const re = /\.ws-grid tbody td\.ws-emp-col \.ws-emp-pos \{[^}]*text-overflow:\s*ellipsis;[^}]*font-size:\s*10px;[^}]*font-weight:\s*400;/;
            assertTrue(re.test(html),
                'Должность: эллипсис при переполнении, 10px/400, цвет secondary');
        });

        test('CSS: светлая тема — должность темнее (#666)', () => {
            const re = /\[data-theme="light"\] \.ws-grid tbody td\.ws-emp-col \.ws-emp-pos \{[^}]*color:\s*#666;/;
            assertTrue(re.test(html),
                'Светлая тема: читаемая должность под ФИО');
        });
    });

    describe('Task 255: селекты месяца/года без скруглений', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: .ws-month-sel/.ws-year-sel — border-radius: 0', () => {
            const re = /\.ws-month-sel, \.ws-year-sel \{[^}]*border-radius:\s*0;/;
            assertTrue(re.test(html),
                'Селекты месяца и года — прямые углы (как кнопки тулбара)');
        });
    });

    describe('Task 254: непрозрачный тулбар, кнопки без скруглений', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: .ws-toolbar — сплошной фон (#17212b, без var(--card-bg))', () => {
            const re = /\.ws-toolbar \{[^}]*background:\s*#17212b;/;
            assertTrue(re.test(html),
                'Тулбар непрозрачный: сплошной аналог --header-bg тёмной темы');
            // именно ОБЪЯВЛЕНИЕ фона, не упоминание в комментарии
            // (комментарий внутри .ws-toolbar описывает, что было раньше)
            const reVar = /\.ws-toolbar \{[^}]*background:\s*var\(--card-bg\)/;
            assertTrue(!reVar.test(html),
                'Полупрозрачный var(--card-bg) больше не задаёт фон тулбара');
        });

        test('CSS: светлая тема — тулбар сплошной #f0eee6', () => {
            const re = /\[data-theme="light"\] \.ws-toolbar \{ background: #f0eee6; \}/;
            assertTrue(re.test(html),
                'Светлая тема: непрозрачный тулбар (аналог --header-bg светлой)');
        });

        test('CSS: кнопки «Сформировать» и «Сохранить» — без скруглений', () => {
            const reGen = /\.ws-generate-btn \{[^}]*border-radius:\s*0;/;
            const reSave = /\.ws-save-btn \{[^}]*border-radius:\s*0;/;
            assertTrue(reGen.test(html) && reSave.test(html),
                'Обе кнопки тулбара — border-radius: 0 (прямые углы)');
        });
    });

    describe('Task 256: авто-подгонка шахматки под окно (целые высоты строк)', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: шапка — целочисленные межстрочные интервалы (было 36.5px)', () => {
            const reTh = /\.ws-grid thead th \{[^}]*line-height:\s*14px;/s;
            const reDow = /\.ws-grid thead th\.ws-day-col \.ws-dow \{[^}]*line-height:\s*11px;/s;
            assertTrue(reTh.test(html) && reDow.test(html),
                'Числа дней lh=14px + дни недели lh=11px: шапка ровно 37.5px, ' +
                'границы строк — на целых пикселях (антиалиасинг не стирает линии)');
        });

        test('CSS: колонка ФИО — целые интервалы (.ws-emp-name/.ws-emp-pos)', () => {
            const reName = /\.ws-grid tbody td\.ws-emp-col \.ws-emp-name \{[^}]*line-height:\s*14px;/s;
            const rePos = /\.ws-grid tbody td\.ws-emp-col \.ws-emp-pos \{[^}]*line-height:\s*12px;/s;
            assertTrue(reName.test(html) && rePos.test(html),
                'ФИО lh=14px + должность lh=12px: природная высота строки целая');
        });

        test('CSS: высота ячеек тела — var(--ws-row-h) (задаёт _fitGrid)', () => {
            const re = /#page-work-schedule \.ws-grid tbody td \{\s*\n\s*height:\s*var\(--ws-row-h,\s*32px\);/s;
            assertTrue(re.test(html),
                'Высота строк через CSS-переменную, без JS — прежние 32px');
        });

        test('CSS: растяжение height:100% убрано (дробные высоты стирали границы)', () => {
            const reBad = /#page-work-schedule \.ws-grid \{\s*\n\s*height:\s*100%;/;
            const reOk = /#page-work-schedule \.ws-grid \{\s*\n\s*height:\s*auto;/;
            assertTrue(!reBad.test(html) && reOk.test(html),
                'height:100% заменён на auto: высоты строк задаёт _fitGrid целыми px');
        });

        test('CSS: компактные режимы ws-compact / ws-tight', () => {
            const reCompact = /\.ws-grid-wrap\.ws-compact \.ws-grid tbody td\.ws-emp-col \{[^}]*padding:\s*3px 10px;/s;
            const reTight = /\.ws-grid-wrap\.ws-tight \.ws-grid tbody td\.ws-emp-col \{[^}]*padding:\s*1px 8px;/s;
            const reTightPos = /\.ws-grid-wrap\.ws-tight \.ws-grid tbody td\.ws-emp-col \.ws-emp-pos \{[^}]*font-size:\s*9px;[^}]*margin-top:\s*0;/s;
            assertTrue(reCompact.test(html) && reTight.test(html) && reTightPos.test(html),
                'Два яруса уплотнения колонки ФИО при нехватке высоты окна');
        });

        test('JS: _fitGrid — целочисленные высоты + остаток по +1px первым строкам', () => {
            const hasFloor = html.indexOf('Math.floor(budget / n)') !== -1;
            const hasRem = html.indexOf('h + (i < rem ? 1 : 0)') !== -1;
            assertTrue(hasFloor && hasRem,
                'floor((область-шапка)/строки) и раздача остатка пикселей');
        });

        test('JS: _fitGrid — подбор яруса по ЗАМЕРУ природной высоты строки', () => {
            const reMeasure = /var measureNatural = function\(\) \{[\s\S]*?getBoundingClientRect\(\)\.height;/;
            const hasTiers = html.indexOf("wrap.classList.add('ws-compact');") !== -1 &&
                             html.indexOf("wrap.classList.add('ws-tight');") !== -1;
            assertTrue(reMeasure.test(html) && hasTiers,
                'Пороги компактности не по формуле, а по фактическому рендеру ' +
                '(box-sizing + collapsed-границы дают +1px к расчётной высоте)');
        });

        test('JS: _fitGrid — мобильная вёрстка (<1024px) не подгоняется', () => {
            const re = /window\.matchMedia\s*\n?\s*&&\s*window\.matchMedia\('\(min-width: 1024px\)'\)\.matches;/;
            const hasClear = html.indexOf("wrap.classList.remove('ws-compact', 'ws-tight');") !== -1;
            assertTrue(re.test(html) && hasClear,
                'На мобильной — природные высоты (очистка классов и переменной)');
        });

        test('JS: _renderGrid вызывает _fitGrid после сборки таблицы', () => {
            const re = /wrap\.innerHTML = html;\s*\n\s*\/\/ Task 256[\s\S]*?\n\s*this\._fitGrid\(\);/;
            assertTrue(re.test(html),
                'После каждого рендера шахматки — пересчёт высот строк');
        });

        test('JS: _attachFitResize — ResizeObserver + брейкпоинт 1024px', () => {
            const hasRO = html.indexOf('new ResizeObserver(function() {') !== -1 ||
                          html.indexOf('new ResizeObserver(') !== -1;
            const hasMq = html.indexOf("window.matchMedia('(min-width: 1024px)')") !== -1;
            assertTrue(hasRO && hasMq,
                'Пересчёт при изменении окна/показе страницы и переходе мобильная/десктоп');
        });

        test('JS: init навешивает _attachFitResize один раз', () => {
            const re = /this\._attachFitResize\(\);/;
            const hasGuard = html.indexOf('if (this._fitAttached) return;') !== -1;
            assertTrue(re.test(html) && hasGuard,
                'Наблюдатель размера вешается однократно при инициализации модуля');
        });
    });

    describe('Task 256: SW версия v514 (история)', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');

        test('v514 заменена актуальной версией', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'Актуальная версия — kipia-test-v526 (Task 272)');
        });
        test('Старая версия v514 убрана', () => {
            assertTrue(sw.indexOf("kipia-test-v514") === -1,
                'Старая v514 не должна остаться в sw.js');
        });
    });

    describe('Task 257: завершающая полоса внизу таблицы + скрытие скроллбара', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: .ws-grid-foot — полоса-бордюрчик 5px внизу таблицы (Task 259: непрозрачная, с эффектом выступа)', () => {
            const re = /\.ws-grid-foot \{[^}]*height:\s*5px;[^}]*box-sizing:\s*border-box;[^}]*background:\s*#35648f;[^}]*border-top:\s*1px solid #85b7dc;[^}]*border-bottom:\s*1px solid #0f1b26;[^}]*\}/s;
            assertTrue(re.test(html),
                'Бордюрчик 5px: сплошной стальной фон #35648f + верхняя грань ' +
                '#85b7dc (блик) и нижняя #0f1b26 (тень) — эффект выступа');
        });

        test('CSS: .ws-grid-foot — светлая тема (Task 259)', () => {
            const re = /\[data-theme="light"\] \.ws-grid-foot \{[^}]*background:\s*#b3c2ce;[^}]*border-top:\s*1px solid #ffffff;[^}]*border-bottom:\s*1px solid #84929e;[^}]*\}/s;
            assertTrue(re.test(html), 'Светлая тема: сплошной фон + белый блик сверху, тень снизу');
        });

        test('CSS: полосы прокрутки шахматки скрыты (все движки)', () => {
            const reWrap = /\.ws-grid-wrap \{[^}]*scrollbar-width:\s*none;[^}]*-ms-overflow-style:\s*none;[^}]*\}/s;
            const reWebkit = /\.ws-grid-wrap::-webkit-scrollbar \{[^}]*display:\s*none;[^}]*\}/s;
            assertTrue(reWrap.test(html) && reWebkit.test(html),
                'scrollbar-width:none (Firefox) + ::-webkit-scrollbar display:none ' +
                '(Chrome/Edge PWA) — полосы прокрутки справа от таблицы больше нет, ' +
                'прокрутка колесом/свайпом остаётся');
        });

        test('JS: _renderGrid добавляет .ws-grid-foot сразу после таблицы', () => {
            const re = /html \+= '<\/tbody><\/table>';[\s\S]*?html \+= '<div class="ws-grid-foot" aria-hidden="true"><\/div>';[\s\S]*?wrap\.innerHTML = html;/;
            assertTrue(re.test(html),
                'Полоса-бордюрчик рендерится под последней строкой каждой шахматки');
        });

        test('JS: _fitGrid резервирует высоту полосы в бюджете строк', () => {
            const reFoot = /var foot = wrap\.querySelector\('\.ws-grid-foot'\);[\s\S]*?var footH = foot \? Math\.round\(foot\.getBoundingClientRect\(\)\.height\) : 0;[\s\S]*?var budget = avail - headH - footH;/;
            assertTrue(reFoot.test(html),
                'budget = область - шапка - полоса: таблица с полосой всегда до низа');
        });

        test('JS: _fitGrid — реальная высота области вместо clientHeight', () => {
            const re = /var avail = Math\.floor\(wrap\.getBoundingClientRect\(\)\.height \+ 0\.25\);/;
            assertTrue(re.test(html),
                'floor(факт+0.25): при дробном масштабе окна (Windows 125%/150%) ' +
                'clientHeight округлялся ВВЕРХ и таблица переливалась на долю px — ' +
                'появлялась полоса прокрутки справа');
        });
    });

    describe('Task 258: SW версия v516 (история)', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');

        test('v516 заменена актуальной версией', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'Актуальная версия — kipia-test-v526 (Task 272)');
        });
    });

    describe('Task 257: SW версия v515 (история)', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');

        test('v515 заменена актуальной версией', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'Актуальная версия — kipia-test-v526 (Task 272)');
        });
    });

    describe('Task 255: SW версия v513 (история)', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');
        test('v513 заменена актуальной версией', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'Актуальная версия — kipia-test-v526');
        });
    });

    // ============================================================
    // Task 259: бордюрчик непрозрачный с эффектом выступа;
    // группировка/сортировка сотрудников (сменные 1-5 → дневные
    // по алфавиту); разделитель групп сменного/дневного персонала
    // ============================================================

    describe('Task 259: бордюрчик под графиком — непрозрачный, с эффектом выступа', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: полоса непрозрачная — сплошной фон без rgba-альфы', () => {
            const reSolid = /\.ws-grid-foot \{[^}]*background:\s*#35648f;[^}]*\}/s;
            const reLightSolid = /\[data-theme="light"\] \.ws-grid-foot \{[^}]*background:\s*#b3c2ce;[^}]*\}/s;
            assertTrue(reSolid.test(html) && reLightSolid.test(html),
                'Фон полосы — сплошные цвета в обеих темах (было rgba с альфой)');
            const reOldAlpha = /\.ws-grid-foot \{[^}]*rgba\(/s;
            assertFalse(reOldAlpha.test(html),
                'В тёмной теме больше нет полупрозрачного rgba-фона полосы');
        });

        test('CSS: эффект выступа — верхняя грань светлее фона, нижняя темнее', () => {
            const reDark = /\.ws-grid-foot \{[^}]*border-top:\s*1px solid #85b7dc;[^}]*border-bottom:\s*1px solid #0f1b26;[^}]*\}/s;
            assertTrue(reDark.test(html),
                'Блик #85b7dc сверху + тень #0f1b26 снизу на стальном фоне — bevel');
            const reLight = /\[data-theme="light"\] \.ws-grid-foot \{[^}]*border-top:\s*1px solid #ffffff;[^}]*border-bottom:\s*1px solid #84929e;[^}]*\}/s;
            assertTrue(reLight.test(html), 'Светлая тема: белый блик + серо-синяя тень');
        });

        test('CSS: высота полосы остаётся 5px (box-sizing: border-box)', () => {
            const re = /\.ws-grid-foot \{[^}]*height:\s*5px;[^}]*box-sizing:\s*border-box;[^}]*\}/s;
            assertTrue(re.test(html),
                '1px блик + 3px фон + 1px тень = 5px, _fitGrid читает реальную ' +
                'геометрию — подгонка строк не меняется');
        });
    });

    describe('Task 259: группировка и сортировка сотрудников', () => {
        const fs = require('fs');
        const path = require('path');
        const vm = require('vm');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        // Извлечение метода _sortEmployees из объекта WorkSchedule
        // (поиск по имени + балансировка фигурных скобок)
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

        let _sortEmployees = null;
        try {
            const src = extractMethod(html, '_sortEmployees');
            if (src) {
                const ctx = {};
                vm.createContext(ctx);
                vm.runInContext('var WSMixin = { ' + src + ' };', ctx);
                _sortEmployees = ctx.WSMixin._sortEmployees;
            }
        } catch (e) { /* метод не извлёкся — тесты ниже упадут с понятной причиной */ }

        test('JS: _sortEmployees определён и подключён в _loadEmployees', () => {
            assertTrue(html.indexOf('_sortEmployees: function(list)') !== -1,
                'Метод _sortEmployees определён в модуле WorkSchedule');
            const re = /self\._EMPLOYEES = self\._sortEmployees\(data\.employees \|\| \[\]\);/;
            assertTrue(re.test(html),
                '_loadEmployees применяет сортировку — единый порядок для ' +
                'шахматки, справочника и селектов');
        });

        test('Функционально: сменные по сменам 1..5, затем дневные по алфавиту', () => {
            assertTrue(typeof _sortEmployees === 'function',
                '_sortEmployees извлечён из index.html');
            const src = [
                { 'ФИО': 'Ягодкин Н.Н.', 'тип': 'дневной' },
                { 'ФИО': 'Иванов А.А.',  'тип': 'сменный', 'смена': 3 },
                { 'ФИО': 'Сидоров К.К.', 'тип': 'сменный', 'смена': 1 },
                { 'ФИО': 'Абрамов В.В.', 'тип': 'сменный', 'смена': 1 },
                { 'ФИО': 'Петров Б.Б.',  'тип': 'сменный', 'смена': 2 },
                { 'ФИО': 'Козлов Д.Д.',  'тип': 'дневной' }
            ];
            const out = _sortEmployees(src).map(e => e['ФИО']);
            assertEqual(JSON.stringify(out),
                JSON.stringify(['Абрамов В.В.', 'Сидоров К.К.', 'Петров Б.Б.',
                                'Иванов А.А.', 'Козлов Д.Д.', 'Ягодкин Н.Н.']),
                'Смена №1 (алфавит), смена №2, смена №3, затем дневные (алфавит)');
        });

        test('Функционально: внутри одной смены — алфавит фамилий', () => {
            const src = [
                { 'ФИО': 'Юдин С.С.', 'тип': 'сменный', 'смена': 2 },
                { 'ФИО': 'Белов Р.Р.', 'тип': 'сменный', 'смена': 2 },
                { 'ФИО': 'Мишин Л.Л.', 'тип': 'сменный', 'смена': 2 }
            ];
            const out = _sortEmployees(src).map(e => e['ФИО']);
            assertEqual(JSON.stringify(out),
                JSON.stringify(['Белов Р.Р.', 'Мишин Л.Л.', 'Юдин С.С.']),
                'Внутри смены №2 сортировка по фамилиям');
        });

        test('Функционально: все 5 смен по порядку, сменный без номера — после них', () => {
            const src = [
                { 'ФИО': 'Фёдоров Ф.Ф.', 'тип': 'сменный' },          // без номера
                { 'ФИО': 'Бобров Б.Б.', 'тип': 'сменный', 'смена': 5 },
                { 'ФИО': 'Агафов А.А.', 'тип': 'сменный', 'смена': 4 },
                { 'ФИО': 'Васин В.В.',  'тип': 'сменный', 'смена': 1 },
                { 'ФИО': 'Гусев Г.Г.',  'тип': 'сменный', 'смена': 2 },
                { 'ФИО': 'Дёмин Д.Д.',  'тип': 'сменный', 'смена': 3 },
                { 'ФИО': 'Яшин Я.Я.',   'тип': 'дневной' }
            ];
            const out = _sortEmployees(src).map(e => e['смена'] || '—');
            assertEqual(JSON.stringify(out),
                JSON.stringify([1, 2, 3, 4, 5, '—', '—']),
                'Смены 1-5 по порядку, сменный без номера перед дневными, дневной в конце');
        });

        test('Функционально: без типа — в конце; исходный массив не мутируется', () => {
            const src = [
                { 'ФИО': 'Иванов И.И.' },                        // без типа
                { 'ФИО': 'Смирнов С.С.', 'тип': 'дневной' },
                { 'ФИО': 'Кузнецов К.К.', 'тип': 'сменный', 'смена': 1 }
            ];
            const snapshot = JSON.stringify(src);
            const out = _sortEmployees(src);
            assertEqual(JSON.stringify(out.map(e => e['ФИО'])),
                JSON.stringify(['Кузнецов К.К.', 'Смирнов С.С.', 'Иванов И.И.']),
                'Сменный → дневной → без типа');
            assertEqual(JSON.stringify(src), snapshot,
                '_sortEmployees возвращает новый массив, не мутируя вход');
        });
    });

    describe('Task 259: разделитель групп сменного и дневного персонала', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: усиленная верхняя граница у строки ws-group-first', () => {
            const reDark = /\.ws-grid tbody tr\.ws-group-first td \{[^}]*border-top:\s*2px solid #4a8fc7;[^}]*\}/s;
            assertTrue(reDark.test(html),
                'Разделитель 2px стальной синий на первой строке дневной группы');
            const reLight = /\[data-theme="light"\] \.ws-grid tbody tr\.ws-group-first td \{[^}]*border-top:\s*2px solid #6e8ba4;[^}]*\}/s;
            assertTrue(reLight.test(html), 'Светлая тема — свой цвет разделителя');
        });

        test('JS: _renderGrid ставит ws-group-first на стыке сменных и дневных', () => {
            const re = /var trCls = \(empTier === 1 && prevTier === 0\)[\s\S]*?' class="ws-group-first"' : '';[\s\S]*?html \+= '<tr' \+ trCls \+ '>';/;
            assertTrue(re.test(html),
                'Класс ставится только когда дневной идёт сразу после сменного');
            const reTier = /var empTier = \(empTip === 'сменный'\) \? 0\s*: \(empTip === 'дневной'\) \? 1 : 2;/;
            assertTrue(reTier.test(html), 'Тир сотрудника: сменный 0, дневной 1, без типа 2');
        });

        test('JS: prevTier обновляется по каждой строке (стык отслеживается)', () => {
            const re = /var prevTier = -1;[\s\S]*?prevTier = empTier;/;
            assertTrue(re.test(html),
                'Группа предыдущей строки отслеживается до конца списка');
        });

        test('Инвариант: без сменных ИЛИ без дневных разделитель не ставится', () => {
            // условие empTier === 1 && prevTier === 0 не срабатывает:
            //  - все дневные: первая строка имеет prevTier = -1
            //  - только сменные: empTier === 1 не встречается
            const re = /var trCls = \(empTier === 1 && prevTier === 0\)/;
            assertTrue(re.test(html),
                'Строгая проверка стыка — лишних разделителей нет');
        });
    });

    describe('Task 259: SW версия v517 (история)', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');

        test('v517 заменена актуальной версией', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'Актуальная версия — kipia-test-v526 (Task 272)');
        });
        test('Старая версия v517 убрана', () => {
            assertTrue(sw.indexOf("kipia-test-v517") === -1,
                'Старая v517 не должна остаться в sw.js');
        });
    });

    describe('Task 260: SW версия v518', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');

        test('CACHE_VERSION = kipia-test-v526', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'CACHE_VERSION должен быть kipia-test-v526 (Task 272)');
        });
        test('Старая версия v517 убрана', () => {
            assertTrue(sw.indexOf("kipia-test-v517") === -1,
                'Старая v517 не должна остаться в sw.js');
        });
    });

    // ============================================================
    // Task 265: «Сформировать» — только через диалог подтверждения.
    // kipConfirm усилен: заголовок/надписи кнопок (title/okText/
    // cancelText), клавиатура (Escape — отмена, Enter — OK, если
    // фокус не на кнопке), защита от двойного срабатывания.
    // ============================================================
    describe('Task 265: подтверждение «Сформировать»', () => {
        const vm = require('vm');
        const html = require('fs').readFileSync(
            require('path').resolve(__dirname, '..', 'index.html'), 'utf8');

        // Извлечение function NAME(...) {...} из index.html
        function extractFn(src, name) {
            const start = src.indexOf('function ' + name + '(');
            if (start === -1) return null;
            const braceStart = src.indexOf('{', start);
            let depth = 0;
            for (let i = braceStart; i < src.length; i++) {
                if (src[i] === '{') depth++;
                else if (src[i] === '}') { depth--; if (depth === 0) return src.slice(start, i + 1); }
            }
            return null;
        }
        const dialogSrc = ['_kipDialogOverlay', '_kipDialogClose', '_kipDialogEsc', 'kipConfirm']
            .map(n => extractFn(html, n)).join('\n');
        if (!dialogSrc || dialogSrc.length < 100) {
            throw new Error('Task 265: функции диалога не извлеклись');
        }

        // Мок DOM + песочница с 4 функциями диалога
        function makeDialogSandbox() {
            const buttons = {
                cancel: { className: 'kip-dialog-btn kip-dialog-cancel', textContent: '', onclick: null,
                          closest: function () { return this; } },
                ok:     { className: 'kip-dialog-btn kip-dialog-ok', textContent: '', onclick: null,
                          closest: function () { return this; } }
            };
            const overlay = {
                id: '', className: '',
                _html: '',
                set innerHTML(v) { this._html = String(v || ''); },
                get innerHTML() { return this._html; },
                classList: (() => {
                    const set = new Set();
                    return { add: c => set.add(c), remove: c => set.delete(c), contains: c => set.has(c) };
                })(),
                querySelector: sel =>
                    sel === '.kip-dialog-cancel' ? buttons.cancel :
                    sel === '.kip-dialog-ok' ? buttons.ok : null
            };
            const listeners = {};
            const documentMock = {
                getElementById: id => (id === 'kipDialogOverlay' ? overlay : null),
                createElement: () => overlay,
                body: { appendChild: () => {} },
                addEventListener: (type, fn) => { (listeners[type] = listeners[type] || []).push(fn); },
                removeEventListener: (type, fn) => {
                    const arr = listeners[type] || [];
                    const i = arr.indexOf(fn);
                    if (i !== -1) arr.splice(i, 1);
                }
            };
            const sandbox = {
                document: documentMock,
                requestAnimationFrame: fn => { fn(); return 0; },
                setTimeout: () => 0,
                clearTimeout: () => {},
                Promise
            };
            vm.createContext(sandbox);
            vm.runInContext(dialogSrc, sandbox);
            return { sandbox, overlay, buttons, listeners };
        }
        const fireKey = (sb, key, target) => {
            (sb.listeners.keydown || []).forEach(fn => fn({ key, target: target || null }));
        };

        test('HTML: generateYear — kipConfirm с заголовком «Формирование шахматки» и кнопкой «Сформировать»', () => {
            assertTrue(html.indexOf("{ title: 'Формирование шахматки', okText: 'Сформировать' }") !== -1,
                'опции диалога: title + okText');
            assertTrue(/kipConfirm\('Сформировать шахматку на ' \+ this\._year \+ ' год \\(все 12 месяцев\\\?\\)'/.test(html) ||
                       html.indexOf("'Сформировать шахматку на ' + this._year + ' год (все 12 месяцев)?\\n'") !== -1,
                'текст вопроса с ГОДОМ (все 12 месяцев)');
            assertTrue(html.indexOf('Существующие ручные правки будут сохранены') !== -1,
                'пояснение о сохранении ручных правок');
            assertTrue(html.indexOf('if (!ok) return;') !== -1,
                'генерация только после подтверждения (ok === true)');
        });

        test('HTML: кнопка «Сформировать» с подсказкой о диалоге (год)', () => {
            const m = html.match(/id="wsGenerateBtn"[^>]*title="([^"]*)"/);
            assertTrue(m && m[1].indexOf('диалог подтверждения') !== -1,
                'title кнопки упоминает диалог подтверждения');
            assertTrue(m && m[1].indexOf('весь выбранный год') !== -1,
                'title кнопки упоминает весь год (Task 272)');
        });

        test('kipConfirm: дефолтные заголовок и кнопки', async () => {
            const sb = makeDialogSandbox();
            const p = sb.sandbox.kipConfirm('Удалить?', {});
            await Promise.resolve();
            assertTrue(sb.overlay.innerHTML.indexOf('Подтвердите действие') !== -1,
                'заголовок по умолчанию');
            assertTrue(sb.overlay.innerHTML.indexOf('>OK<') !== -1, 'кнопка OK');
            assertTrue(sb.overlay.innerHTML.indexOf('>Отмена<') !== -1, 'кнопка Отмена');
            assertTrue(sb.overlay.classList.contains('active'), 'оверлей активируется');
            sb.buttons.ok.onclick();
            assertEqual(await p, true, 'OK → true');
        });

        test('kipConfirm: кастомные title/okText/cancelText', async () => {
            const sb = makeDialogSandbox();
            const p = sb.sandbox.kipConfirm('Текст', { title: 'Формирование шахматки', okText: 'Сформировать', cancelText: 'Не сейчас' });
            await Promise.resolve();
            assertTrue(sb.overlay.innerHTML.indexOf('Формирование шахматки') !== -1,
                'свой заголовок');
            assertTrue(sb.overlay.innerHTML.indexOf('>Сформировать<') !== -1,
                'своя кнопка подтверждения');
            assertTrue(sb.overlay.innerHTML.indexOf('>Не сейчас<') !== -1,
                'своя кнопка отмены');
            sb.buttons.cancel.onclick();
            assertEqual(await p, false, 'отмена → false');
        });

        test('kipConfirm: danger — красная кнопка OK', () => {
            const sb = makeDialogSandbox();
            sb.sandbox.kipConfirm('Удалить всё?', { danger: true });
            assertTrue(sb.overlay.innerHTML.indexOf('kip-dialog-ok danger') !== -1,
                'класс danger у кнопки подтверждения');
        });

        test('kipConfirm: Escape — отмена, слушатель снимается', async () => {
            const sb = makeDialogSandbox();
            const p = sb.sandbox.kipConfirm('Вопрос?');
            await Promise.resolve();
            assertTrue((sb.listeners.keydown || []).length === 1, 'keydown-слушатель добавлен');
            fireKey(sb, 'Escape');
            assertEqual(await p, false, 'Escape → false');
            assertEqual((sb.listeners.keydown || []).length, 0, 'слушатель снят после закрытия');
        });

        test('kipConfirm: Enter — подтверждение (фокус не на кнопке)', async () => {
            const sb = makeDialogSandbox();
            const p = sb.sandbox.kipConfirm('Вопрос?');
            await Promise.resolve();
            fireKey(sb, 'Enter');
            assertEqual(await p, true, 'Enter → true');
        });

        test('kipConfirm: Enter при фокусе на кнопке диалога — обрабатывает кнопка', async () => {
            const sb = makeDialogSandbox();
            let settled = null;
            const p = sb.sandbox.kipConfirm('Вопрос?');
            p.then(v => { settled = v; });
            await Promise.resolve();
            fireKey(sb, 'Enter', sb.buttons.cancel);   // фокус на «Отмена»
            await new Promise(r => setTimeout(r, 5));
            assertEqual(settled, null, 'глобальный Enter не сработал');
            sb.buttons.cancel.onclick();
            assertEqual(await p, false, 'кнопка отменила');
        });

        test('kipConfirm: двойной клик не ломает результат', async () => {
            const sb = makeDialogSandbox();
            const p = sb.sandbox.kipConfirm('Вопрос?');
            await Promise.resolve();
            sb.buttons.ok.onclick();
            sb.buttons.ok.onclick();
            sb.buttons.cancel.onclick();
            assertEqual(await p, true, 'первое срабатывание побеждает');
            assertEqual((sb.listeners.keydown || []).length, 0, 'слушатель снят один раз');
        });

        test('kipConfirm: экранирование заголовка и надписей', () => {
            const sb = makeDialogSandbox();
            sb.sandbox.kipConfirm('?', { title: '<b>Опасно</b>', okText: 'OK<x>' });
            assertTrue(sb.overlay.innerHTML.indexOf('&lt;b&gt;Опасно&lt;/b&gt;') !== -1,
                'заголовок экранируется');
            assertTrue(sb.overlay.innerHTML.indexOf('OK&lt;x&gt;') !== -1,
                'надпись кнопки экранируется');
        });
    });

    // ============================================================
    // Task 267 (по заявке пользователя), 4 пункта:
    //   1) анимация точек «Загрузка…» при загрузке графика —
    //      по примеру «Расходомеров хозрасчётных» (.flow-loading-dots);
    //   2) Документация ИОС — автоматическое размещение кнопок
    //      (обе в одном .menu-btn-row, как на странице «Библиотека»);
    //   3) «График работы» можно закрепить на главной (SUBSECTIONS);
    //   4) хлебные крошки «Графика работы» — полная цепочка
    //      «Главная / Документация / Документация ИОС / График работы».
    // ============================================================
    describe('Task 267: анимация точек «Загрузка…» в Графике работы', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: переиспользуются классы расходомеров .flow-loading-dots + keyframes', () => {
            assertTrue(html.indexOf('.flow-loading-dots {') !== -1,
                'CSS .flow-loading-dots определён (общий для расходомеров и графика)');
            assertTrue(html.indexOf('@keyframes flowLoadingDot') !== -1,
                'keyframes flowLoadingDot определён');
            assertTrue(html.indexOf('.flow-loading-dots span {') !== -1,
                'анимация на точках-спанах');
            // Задержки чередуются — «бегущие» точки
            const re1 = /\.flow-loading-dots span:nth-child\(1\) \{ animation-delay: 0s; \}/;
            const re3 = /\.flow-loading-dots span:nth-child\(3\) \{ animation-delay: 0\.4s; \}/;
            assertTrue(re1.test(html) && re3.test(html),
                'задержки 0s/0.2s/0.4s — точки бегут по очереди');
        });

        test('HTML: статический #wsEmpty — «Загрузка» + три анимированные точки', () => {
            // Task 269: та же разметка, но на классах расходомеров
            // .flow-loading + .flow-loading-text (шрифт как у расходомеров)
            const re = /<div class="flow-loading" id="wsEmpty"><div class="flow-loading-text">Загрузка<span class="flow-loading-dots"><span>\.<\/span><span>\.<\/span><span>\.<\/span><\/span><\/div><\/div>/;
            assertTrue(re.test(html),
                'плейсхолдер сетки содержит span.flow-loading-dots с тремя точками');
        });

        test('JS: loadGrid() ставит ту же разметку с точками', () => {
            const re = /wrapEl\.innerHTML = '<div class="flow-loading" id="wsEmpty"><div class="flow-loading-text">Загрузка<span class="flow-loading-dots"><span>\.<\/span><span>\.<\/span><span>\.<\/span><\/span><\/div><\/div>';/;
            assertTrue(re.test(html),
                'loadGrid показывает «Загрузка…» с анимированными точками при каждой смене месяца');
        });

        test('CSS-комментарий фиксирует переиспользование классов (Task 267)', () => {
            assertTrue(html.indexOf('Task 267: классы .flow-loading-dots / @keyframes flowLoadingDot') !== -1,
                'комментарий в CSS о совместном использовании классов');
        });
    });

    describe('Task 267: Документация ИОС — автоматическое размещение кнопок', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        // Блок страницы Документация ИОС (от заголовка до следующей страницы)
        const pageStart = html.indexOf('id="page-docs-ios"');
        const pageEnd = html.indexOf('id="page-flowmeter-data"');
        assertTrue(pageStart !== -1 && pageEnd !== -1 && pageStart < pageEnd,
            'страница page-docs-ios найдена');
        const pageBlock = html.slice(pageStart, pageEnd);

        test('HTML: обе кнопки в ОДНОМ .menu-btn-row (как в Библиотеке)', () => {
            const rows = pageBlock.match(/<div class="menu-btn-row">/g) || [];
            assertEqual(rows.length, 1,
                'на странице Документация ИОС ровно один .menu-btn-row (было два)');
            assertTrue(pageBlock.indexOf('id="flowmeterMenuBtn"') !== -1,
                'кнопка «Расходомеры хозрасчётные» на месте');
            assertTrue(pageBlock.indexOf('id="workScheduleMenuBtn"') !== -1,
                'кнопка «График работы» на месте');
            // Порядок: расходомеры раньше графика в разметке
            const iFlow = pageBlock.indexOf('id="flowmeterMenuBtn"');
            const iWs = pageBlock.indexOf('id="workScheduleMenuBtn"');
            assertTrue(iFlow !== -1 && iWs !== -1 && iFlow < iWs,
                'порядок кнопок: Расходомеры → График работы');
        });

        test('CSS: grid-auto-rows 1fr — равная высота кнопок, как у Библиотеки', () => {
            const re = /#page-library-internal \.menu-btn-row,\s*\n\s*#page-library-electro \.menu-btn-row,\s*\n\s*#page-docs-ios \.kip-ios-block \.menu-btn-row \{ grid-auto-rows: 1fr; \}/;
            assertTrue(re.test(html),
                'правило grid-auto-rows: 1fr включает #page-docs-ios .kip-ios-block .menu-btn-row');
        });

        test('CSS: десктоп — 3 колонки для page-docs-ios (авто-размещение сеткой)', () => {
            const re = /#page-docs-ios \.kip-ios-block \.menu-btn-row,[\s\S]{0,200}?grid-template-columns: repeat\(3, 1fr\);/;
            assertTrue(re.test(html),
                'десктопное правило 3 колонок покрывает .kip-ios-block страницы Документация ИОС');
        });

        test('Роль-фильтр: скрытие .kip-ios-block при всех скрытых кнопках не сломано', () => {
            assertTrue(html.indexOf("flowmeterBtn.closest('.kip-ios-block')") !== -1,
                'проверка kip-ios-block осталась (кнопки в одном ряду — closest работает)');
        });
    });

    describe('Task 267: кнопка «График работы» — закрепление на главной', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        // Извлечение реестра SUBSECTIONS (как в test-role-access.js)
        const m = html.match(/const\s+SUBSECTIONS\s*=\s*\{/);
        assertTrue(!!m, 'SUBSECTIONS найден');
        // Запись work-schedule в реестре (регекс по строке реестра)
        test('SUBSECTIONS: запись work-schedule — label/sublabel/target/category', () => {
            const re = /'work-schedule':\s*\{ label: 'График работы',\s*sublabel: 'Шахматка сменного и дневного персонала',\s*target: 'work-schedule',\s*category: 'docs' \}/;
            assertTrue(re.test(html),
                'реестр содержит work-schedule (метка как у кнопки на странице, категория docs — золотистый стиль)');
        });

        test('SUBSECTIONS: work-schedule доступен для закрепления (валидный target)', () => {
            // target = 'work-schedule' — страница существует и входит в _WORK_SCHEDULE_PAGES
            assertTrue(html.indexOf('id="page-work-schedule"') !== -1,
                'страница page-work-schedule существует');
            assertTrue(html.indexOf("_WORK_SCHEDULE_PAGES: ['work-schedule',") !== -1,
                'work-schedule в _WORK_SCHEDULE_PAGES (доступ Админу через *)');
        });

        test('wrapSubsectionItems: ключ кнопки «График работы» теперь в реестре → свайп работает', () => {
            // Кнопка на page-docs-ios имеет onclick navigateTo('work-schedule');
            // wrapSubsectionItems оборачивает только кнопки с ключом в SUBSECTIONS
            const reBtn = /id="workScheduleMenuBtn"[^>]*onclick="navigateTo\('work-schedule'\)"/;
            assertTrue(reBtn.test(html),
                'кнопка workScheduleMenuBtn ведёт на work-schedule');
            assertTrue(html.indexOf("if (!SUBSECTIONS[key]) return;") !== -1,
                'фильтр по реестру в wrapSubsectionItems');
        });

        test('Закреплённый ярлык: рендер как у «Расходомеров» (docs-категория)', () => {
            // renderPinnedItems красит docs-категорию золотистым — как flowmeter-data
            assertTrue(html.indexOf("const isDocs = s.category === 'docs';") !== -1,
                'стилизация docs-категории в renderPinnedItems');
        });
    });

    describe('Task 267: полная цепочка хлебных крошек Графика работы', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('PAGE_PARENTS: work-schedule больше НЕ корневой (dashboard убран)', () => {
            const re = /'work-schedule':\s+'dashboard'/;
            assertTrue(!re.test(html),
                'записи work-schedule → dashboard быть не должно (Task 267 заменил на docs-ios)');
        });

        test('PAGE_PARENTS: цепочка как у «Расходомеров хозрасчётных»', () => {
            const reWs = /'work-schedule':\s+'docs-ios'/;
            const reFlow = /'flowmeter-data':\s+'docs-ios'/;
            assertTrue(reWs.test(html) && reFlow.test(html),
                'work-schedule и flowmeter-data — оба подразделы docs-ios (единая цепочка)');
        });

        test('PAGE_LABELS: метки цепочки существуют (Документация / Документация ИОС / График работы)', () => {
            const labelsMatch = html.match(/const PAGE_LABELS = \{([\s\S]*?)\n    \};/);
            assertTrue(!!labelsMatch, 'PAGE_LABELS найден');
            const labels = labelsMatch[1];
            assertTrue(/'docs':\s+'Документация'/.test(labels), 'метка Документация');
            assertTrue(/'docs-ios':\s+'Документация ИОС'/.test(labels), 'метка Документация ИОС');
            assertTrue(/'work-schedule':\s+'График работы'/.test(labels), 'метка График работы');
        });
    });

    describe('Task 269: SW версия v524', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');

        test('CACHE_VERSION = kipia-test-v526', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'CACHE_VERSION должен быть kipia-test-v526 (Task 272)');
        });
        test('Старая версия v523 убрана', () => {
            assertTrue(sw.indexOf("kipia-test-v523") === -1,
                'Старая v523 не должна остаться в sw.js');
        });
    });

    // ============================================================
    // Task 269 (по заявке пользователя), 5 пунктов — бар кнопок
    // «Графика работы» и «Загрузка…»:
    //   1) столбик норм окна календаря разделён на ДВА столбика
    //      (счётчики дней слева, нормы часов справа от них);
    //   2) само окно стало УЖЕ — ширина по тексту (fit-content);
    //   3) высота кнопок бара ВЫРАВНЕНА (34px у всех элементов);
    //   4) кнопки — в ЛЕВОЙ НИЖНЕЙ части бара, окно с данными —
    //      в ПРАВОЙ (десктоп ≥1024px);
    //   5) шрифт «Загрузка…» — как у «Расходомеров хозрасчётных»
    //      (.flow-loading + .flow-loading-text: 16px / 600).
    // ============================================================
    describe('Task 269: нормы двумя столбиками (.ws-cp-group/.ws-cp-cols)', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: группа норм — колонка с заголовком (.ws-cp-group)', () => {
            assertTrue(/\.ws-cp-group \{[^}]*flex-direction:\s*column/.test(html),
                'группа норм — вертикальная: заголовок сверху, столбики под ним');
            assertTrue(/\.ws-cp-group \{[^}]*flex-shrink:\s*0/.test(html),
                'группа не сжимается — переносится при нехватке ширины');
        });

        test('CSS: ДВА подстолбика норм в ряд (.ws-cp-cols)', () => {
            assertTrue(/\.ws-cp-cols \{[^}]*display:\s*flex/.test(html),
                '.ws-cp-cols — строка из двух подстолбиков');
            assertTrue(/\.ws-cp-cols \{[^}]*column-gap:\s*16px/.test(html),
                'зазор между подстолбиками (второй — справа от первого)');
            assertTrue(/\.ws-cp-cols \{[^}]*flex-wrap:\s*wrap/.test(html),
                'на узких экранах подстолбик часов переносится под дни');
        });

        test('JS: renderPanel — дни и часы в РАЗНЫХ подстолбиках', () => {
            // заголовок «Норма, …» живёт в группе, под ней .ws-cp-cols
            const groupRe = /'<div class="ws-cp-group ws-cp-norms"[^>]*>'\s*\+[^;]*?'<span class="ws-cp-cap">Норма, '/;
            assertTrue(groupRe.test(html),
                'группа норм с заголовком «Норма, {месяц}» (тултип официальности — на группе)');
            assertTrue(html.indexOf("'<div class=\"ws-cp-cols\">'") !== -1,
                'контейнер двух подстолбиков .ws-cp-cols');
            // первый подстолбик — счётчики дней, второй — нормы часов:
            // «Рабочих» и «40-час» в разных .ws-cp-col внутри .ws-cp-cols
            const colsStart = html.indexOf("'<div class=\"ws-cp-cols\">'");
            const colsEnd = html.indexOf("'</div>' +\n                    '</div>';");
            assertTrue(colsStart !== -1 && colsEnd > colsStart, 'блок .ws-cp-cols найден');
            const colsBlock = html.slice(colsStart, colsEnd);
            const iDays = colsBlock.indexOf('Рабочих: <b>');
            const iFirstColEnd = colsBlock.indexOf("'</div>' +", iDays);
            const iHours = colsBlock.indexOf('40-час: <b>');
            assertTrue(iDays !== -1 && iHours !== -1 && iFirstColEnd !== -1,
                'и дни, и часы есть в блоке .ws-cp-cols');
            assertTrue(iDays < iFirstColEnd && iHours > iFirstColEnd,
                '«Рабочих» — в первом подстолбике, «40-час» — во втором (справа)');
        });
    });

    describe('Task 269: окно уже — ширина по тексту; Task 270: высота под 5 строк', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: базовое правило — width: fit-content', () => {
            assertTrue(/\.ws-cal-panel \{[^}]*width:\s*fit-content/.test(html),
                'окно не растягивается — ширина по тексту столбиков');
            assertTrue(/\.ws-cal-panel \{[^}]*max-width:\s*100%/.test(html),
                'окно не шире бара');
        });

        test('CSS: статическая высота 95px — ПОД ПЯТЬ СТРОК (Task 270)', () => {
            assertTrue(/\.ws-cal-panel \{[^}]*height:\s*95px/.test(html),
                'высота окна — 95px в базовом правиле (плашка + 4 строки часов)');
            const re = /@media \(min-width: 1024px\) \{[\s\S]*?\.ws-cal-panel \{[^}]*height:\s*95px/s;
            assertTrue(re.test(html), 'высота окна на десктопе — те же 95px');
            assertFalse(/\.ws-cal-panel \{[^}]*height:\s*120px/.test(html),
                'старая высота 120px (Task 269) заменена');
        });
    });

    describe('Task 269: кнопки слева внизу / окно справа + высота кнопок', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: единая высота всех элементов ряда кнопок (34px)', () => {
            const re = /\.ws-month-sel, \.ws-year-sel, \.ws-cal-chip, \.ws-generate-btn, \.ws-save-btn \{[^}]*height:\s*34px[^}]*box-sizing:\s*border-box/;
            assertTrue(re.test(html),
                'селекты, чип «Календарь», «Сформировать» и «Сохранить» — одного роста');
        });

        test('CSS: десктоп — кнопки в ЛЕВОМ ВЕРХНЕМ углу бара (Task 272)', () => {
            assertTrue(/\.ws-toolbar-main \{[^}]*order:\s*0/.test(html),
                'ряд кнопок — левая часть бара (order: 0)');
            assertTrue(/\.ws-toolbar-main \{[^}]*align-self:\s*flex-start/.test(html),
                'кнопки прижаты к верхней кромке бара (Task 272 — левый верхний угол)');
            assertTrue(/\.ws-toolbar-main \{[^}]*margin-right:\s*auto/.test(html),
                'окно уходит в правую часть бара');
        });

        test('CSS: десктоп — окно с данными в ПРАВОЙ части бара', () => {
            assertTrue(/\.ws-cal-panel \{[^}]*order:\s*1/.test(html),
                'окно календаря — правая часть бара (order: 1)');
            assertTrue(/\.ws-cal-panel \{[^}]*flex:\s*0 1 auto/.test(html),
                'окно не растягивается на свободную ширину');
            assertFalse(/\.ws-cal-panel \{[^}]*flex:\s*1 1 auto/.test(html),
                'старое растягивание (flex: 1 1 auto) удалено');
        });

        test('CSS: старое размещение Task 266 удалено', () => {
            assertFalse(/\.ws-toolbar-main \{[^}]*margin-left:\s*auto/.test(html),
                'кнопки больше не прижаты вправо');
            assertFalse(/\.ws-cal-panel \{[^}]*min-width:\s*0/.test(html),
                'min-width: 0 из старого правила удалён');
        });
    });

    describe('Task 269: шрифт «Загрузка…» — как у расходомеров', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: .flow-loading-text — 16px / 600 / text-primary', () => {
            assertTrue(/\.flow-loading-text \{[^}]*font-size:\s*16px/.test(html),
                'размер шрифта «Загрузка…» — 16px (как у расходомеров)');
            assertTrue(/\.flow-loading-text \{[^}]*font-weight:\s*600/.test(html),
                'жирность — 600');
            assertTrue(/\.flow-loading-text \{[^}]*color:\s*var\(--text-primary\)/.test(html),
                'цвет — основной текст, а не приглушённый admin-empty');
        });

        test('HTML: статический #wsEmpty — .flow-loading + .flow-loading-text', () => {
            const re = /<div class="flow-loading" id="wsEmpty"><div class="flow-loading-text">Загрузка<span class="flow-loading-dots"><span>\.<\/span><span>\.<\/span><span>\.<\/span><\/span><\/div><\/div>/;
            assertTrue(re.test(html),
                'плейсхолдер сетки использует классы расходомеров (шрифт 16px/600) с тремя точками');
        });

        test('JS: loadGrid() ставит ту же разметку с классами расходомеров', () => {
            const re = /wrapEl\.innerHTML = '<div class="flow-loading" id="wsEmpty"><div class="flow-loading-text">Загрузка<span class="flow-loading-dots"><span>\.<\/span><span>\.<\/span><span>\.<\/span><\/span><\/div><\/div>';/;
            assertTrue(re.test(html),
                'loadGrid показывает «Загрузка…» шрифтом расходомеров при каждой смене месяца');
        });

        test('HTML: #wsEmpty больше не использует admin-empty', () => {
            assertFalse(/<div class="admin-empty" id="wsEmpty"/.test(html),
                'старая разметка admin-empty (14px, приглушённый цвет) удалена');
        });
    });

    // ============================================================
    // Task 270: окошко календаря — высота под 5 строк, светлый фон
    // темнее, плашки-заголовки столбцов с цветным фоном и ярким
    // текстом, узкий бар с отступами 5px
    // ============================================================

    describe('Task 270: заголовки столбцов — плашки с цветным фоном, текст ярче', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: .ws-cp-cap — плашка (inline-block + padding, обнимает текст)', () => {
            assertTrue(/\.ws-cp-cap \{[^}]*display:\s*inline-block/.test(html),
                'заголовок — inline-block плашка, а не растянутая строка');
            assertTrue(/\.ws-cp-cap \{[^}]*padding:\s*1px 7px/.test(html),
                'плашка с внутренними отступами 1px 7px');
            assertTrue(/\.ws-cp-cap \{[^}]*align-self:\s*flex-start/.test(html),
                'плашка не тянется на ширину столбика (align-self: flex-start)');
            assertTrue(/\.ws-cp-cap \{[^}]*border-radius:\s*2px/.test(html),
                'скругление 2px — как у чипов дней');
        });

        test('CSS: плашка «Норма» — синий фон, яркий текст', () => {
            const re = /\.ws-cp-norms > \.ws-cp-cap \{[^}]*background:\s*rgba\(74, 143, 199, 0\.22\);[^}]*color:\s*#93c1ea;/s;
            assertTrue(re.test(html),
                'цветовое разграничение: заголовок норм — синяя плашка, текст яркий #93c1ea');
        });

        test('CSS: плашка «Праздники» — красный фон, яркий текст', () => {
            const re = /\.ws-cp-days > \.ws-cp-cap \{[^}]*background:\s*rgba\(255, 107, 107, 0\.20\);[^}]*color:\s*#ff9c9c;/s;
            assertTrue(re.test(html),
                'заголовок праздников — красная плашка, текст яркий #ff9c9c');
        });

        test('CSS: плашки РАЗНЫЕ — синий ≠ красный (цветовое разграничение)', () => {
            const norms = html.match(/\.ws-cp-norms > \.ws-cp-cap \{[^}]*\}/s);
            const days = html.match(/\.ws-cp-days > \.ws-cp-cap \{[^}]*\}/s);
            assertTrue(norms && days && norms[0] !== days[0],
                'у заголовков норм и праздников — разные цвета фона');
        });

        test('CSS: светлая тема — плашки сохраняют смысловые цвета, текст ярче', () => {
            const reN = /\[data-theme="light"\] \.ws-cp-norms > \.ws-cp-cap \{[^}]*background:\s*rgba\(74, 143, 199, 0\.16\);[^}]*color:\s*#1d5f96;/s;
            assertTrue(reN.test(html),
                'светлая тема: норм — синяя плашка, насыщенный текст #1d5f96 (ярче серого #999)');
            const reD = /\[data-theme="light"\] \.ws-cp-days > \.ws-cp-cap \{[^}]*background:\s*rgba\(255, 107, 107, 0\.15\);[^}]*color:\s*#b02c2c;/s;
            assertTrue(reD.test(html),
                'светлая тема: праздники — красная плашка, насыщенный текст #b02c2c');
        });

        test('CSS: светлая тема — .ws-cp-cap больше НЕ перекрашивается в серый', () => {
            assertFalse(/\[data-theme="light"\] \.ws-cp-cap,/.test(html),
                'старое правило серого заголовка в светлой теме удалено');
        });
    });

    describe('Task 270: светлая тема — окно темнее, бар узкий с отступами 5px', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('CSS: светлая тема — фон окна #e9e7de (темнее белого и тулбара)', () => {
            const re = /\[data-theme="light"\] \.ws-cal-panel \{[^}]*background:\s*#e9e7de;/s;
            assertTrue(re.test(html),
                'окно в светлой теме — на тон темнее (#e9e7de вместо #fff): ' +
                'углублённый блок данных, не выбеливается на баре #f0eee6');
            assertFalse(/\[data-theme="light"\] \.ws-cal-panel \{[^}]*background:\s*#fff;/s.test(html),
                'белый фон окна в светлой теме убран');
        });

        test('CSS: отступы бара — 5px со всех сторон (базовое правило)', () => {
            assertTrue(/\.ws-toolbar \{[^}]*padding:\s*5px;/.test(html),
                'внутренние отступы тулбара — 5px (было 8px 12px)');
        });

        test('CSS: десктоп — зазор между рядом кнопок и окном 5px', () => {
            const re = /@media \(min-width: 1024px\) \{[\s\S]*?\.ws-toolbar \{[^}]*gap:\s*5px;/s;
            assertTrue(re.test(html), 'десктопный зазор в баре — 5px (было 12px)');
        });

        test('CSS: бар узкий — высота задаётся окном 95px, без лишних мин-высот', () => {
            // окно 95px + 2×5px отступа + рамка 1px = 106px: бар обнимает окно
            assertTrue(/\.ws-cal-panel \{[^}]*height:\s*95px/.test(html),
                'высота окна — 95px: бар сужается по высоте окошка');
            assertFalse(/\.ws-toolbar \{[^}]*min-height/.test(html),
                'у тулбара нет независимой мин-высоты — бар по содержимому');
            assertFalse(/\.ws-toolbar \{[^}]*padding:\s*8px 12px/.test(html),
                'старые отступы 8px 12px убраны');
        });
    });

    // ============================================================
    // Task 272 (по заявке пользователя):
    //   1) кнопка «Календарь» переделана в «Обновить» — клик
    //      открывает диалог с источником (calendar.legalic.ru,
    //      федеральный, официальные нормы) и кнопкой подтверждения;
    //   2) шторка настроек УДАЛЕНА: выбор регионов, поле ввода
    //      токена production-calendar.ru и прочее убраны — регион
    //      один (42 — Кемеровская область - Кузбасс);
    //   3) «Сформировать» строит шахматку на ВЕСЬ ГОД (12 месяцев
    //      последовательными вызовами workSchedule.generateMonth);
    //   4) обе кнопки («Обновить» + «Сформировать») — в ЛЕВОМ
    //      ВЕРХНЕМ углу бара.
    // ============================================================
    describe('Task 272: кнопка «Обновить» вместо «Календарь»', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('HTML: кнопка wsCalChip — надпись «Обновить» и confirmRefresh', () => {
            const m = html.match(/<button[^>]*id="wsCalChip"[^>]*>/);
            assertTrue(!!m, 'кнопка wsCalChip в тулбаре');
            assertTrue(m[0].indexOf('onclick="ProdCalendar.confirmRefresh()"') !== -1,
                'onclick — ProdCalendar.confirmRefresh()');
            assertTrue(html.indexOf('<span id="wsCalChipText">Обновить</span>') !== -1,
                'надпись — «Обновить»');
            assertTrue(html.indexOf('<span id="wsCalChipText">Календарь</span>') === -1,
                'старая надпись «Календарь» удалена');
        });

        test('JS: _updateCalChip ставит «Обновить» и новый тултип', () => {
            assertTrue(html.indexOf("textEl.textContent = 'Обновить';") !== -1,
                'текст кнопки — «Обновить»');
            assertTrue(html.indexOf("textEl.textContent = 'Календарь';") === -1,
                'старый текст удалён');
            assertTrue(html.indexOf('calendar.legalic.ru, федеральный') !== -1,
                'тултип упоминает источник legalic');
        });

        test('HTML: шторка настроек и токен полностью удалены', () => {
            assertTrue(html.indexOf('id="wsCalSheet"') === -1, 'шторка удалена');
            assertTrue(html.indexOf('id="wsCalOverlay"') === -1, 'оверлей шторки удалён');
            assertTrue(html.indexOf('wsCalToken') === -1, 'поле токена удалено');
            assertTrue(html.indexOf('wsCalRegionSel') === -1, 'селект региона удалён');
            assertTrue(html.indexOf('Обновить сейчас') === -1,
                'кнопка «Обновить сейчас» из шторки удалена');
            assertTrue(html.indexOf('Расширенный источник') === -1,
                'блок расширенного источника удалён');
        });
    });

    describe('Task 272: «Сформировать» — шахматка на весь год', () => {
        const fs = require('fs');
        const path = require('path');
        const indexPath = path.resolve(__dirname, '..', 'index.html');
        const html = fs.readFileSync(indexPath, 'utf8');

        test('HTML: кнопка вызывает WorkSchedule.generateYear()', () => {
            const m = html.match(/<button[^>]*id="wsGenerateBtn"[^>]*>/);
            assertTrue(!!m, 'кнопка wsGenerateBtn в тулбаре');
            assertTrue(m[0].indexOf('onclick="WorkSchedule.generateYear()"') !== -1,
                'onclick — WorkSchedule.generateYear()');
        });

        test('JS: generateYear определён, generateMonth (клиент) удалён', () => {
            assertTrue(html.indexOf('generateYear: function') !== -1,
                'метод generateYear определён');
            assertTrue(html.indexOf('_doGenerateYear: function') !== -1,
                'метод _doGenerateYear определён (цикл по месяцам)');
            assertFalse(/generateMonth: function/.test(html),
                'старый клиентский generateMonth: function удалён');
        });

        test('JS: _doGenerateYear — цикл 1..12 по workSchedule.generateMonth', () => {
            assertTrue(html.indexOf('nextMonth = function(month)') !== -1,
                'рекурсивный обход месяцев');
            assertTrue(html.indexOf('if (month > 12)') !== -1,
                'условие завершения после 12-го месяца');
            const apiCalls = (html.match(/workSchedule\.generateMonth'/g) || []).length;
            assertTrue(apiCalls >= 1,
                'серверный эндпоинт workSchedule.generateMonth вызывается из цикла');
            assertTrue(html.indexOf("'Формируется… ' + month + '/12'") !== -1,
                'прогресс на кнопке — «Формируется… N/12»');
        });

        test('JS: итоговый тост — суммы за весь год', () => {
            assertTrue(html.indexOf("'Год ' + self._year + ': сформировано '") !== -1,
                'тост с суммой сформированных записей за год');
            assertTrue(html.indexOf('totalGenerated') !== -1 &&
                       html.indexOf('totalUpdated') !== -1,
                'счётчики суммируются по всем месяцам');
        });

        test('JS: диалог подтверждения — год, а не месяц', () => {
            assertTrue(html.indexOf("'Сформировать шахматку на ' + this._year + ' год (все 12 месяцев)?\\n'") !== -1,
                'вопрос диалога — на весь год (все 12 месяцев)');
            assertTrue(/monthName\[this\._month\] \+ ' ' \+ this\._year/.test(html) === false,
                'старый текст с названием месяца удалён');
        });
    });

    describe('Task 272: SW версия v526', () => {
        const fs = require('fs');
        const path = require('path');
        const swPath = path.resolve(__dirname, '..', 'sw.js');
        const sw = fs.readFileSync(swPath, 'utf8');

        test('CACHE_VERSION = kipia-test-v526', () => {
            assertTrue(sw.indexOf("kipia-test-v526") !== -1,
                'CACHE_VERSION должен быть kipia-test-v526 (Task 272)');
        });
        test('Старая версия v525 убрана', () => {
            assertTrue(sw.indexOf("kipia-test-v525") === -1,
                'Старая v525 не должна остаться в sw.js');
        });
    });
});
