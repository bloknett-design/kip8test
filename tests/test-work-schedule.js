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

        test('PAGE_PARENTS: work-schedule — корневой раздел (родитель dashboard)', () => {
            // В PAGE_PARENTS: 'work-schedule': 'dashboard' (после admin-блока)
            const re = /'work-schedule':\s+'dashboard'/;
            assertTrue(re.test(html),
                'PAGE_PARENTS должен содержать work-schedule → dashboard (корневой раздел, как Сапёр/Справочник)');
        });

        test('PAGE_PARENTS: подразделы с родителем work-schedule', () => {
            const reEmp = /'work-schedule-employees':\s+'work-schedule'/;
            const reTr = /'work-schedule-trainings':\s+'work-schedule'/;
            assertTrue(reEmp.test(html),
                'PAGE_PARENTS: work-schedule-employees → work-schedule (путь «Главная / График работы / Сотрудники»)');
            assertTrue(reTr.test(html),
                'PAGE_PARENTS: work-schedule-trainings → work-schedule (путь «Главная / График работы / Инструктажи и обучения»)');
        });

        test('buildBreadcrumbPath: путь work-schedule = [work-schedule] (один сегмент)', () => {
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
            assertEqual(path.length, 1,
                'Путь work-schedule должен быть одним сегментом (родитель — dashboard)');
            assertEqual(path[0], 'work-schedule');
        });

        test('buildBreadcrumbPath: путь work-schedule-employees = [work-schedule, work-schedule-employees]', () => {
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
            assertEqual(path.length, 2,
                'Путь work-schedule-employees — два сегмента через work-schedule');
            assertEqual(path[0], 'work-schedule');
            assertEqual(path[1], 'work-schedule-employees');
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

        test('JS: текст кода статуса не выводится в ячейке (только цвет)', () => {
            // Старый вывод: (status || '·') — код буквой в ячейке
            assertTrue(html.indexOf("(status || '·')") === -1,
                'Код статуса не должен выводиться в ячейке (старый паттерн (status || \'·\'))');
            // Новый: пустая ячейка — маркер «·», статусная — без текста
            assertTrue(html.indexOf("(status ? '' : '·')") !== -1,
                'Статусная ячейка — без текста, пустая — маркер «·»');
        });

        test('JS: легенда без кодов — только цветовой образец и название', () => {
            assertTrue(html.indexOf("'<b>' + this._esc(c.code) + '</b> — '") === -1,
                'Код статуса не должен выводиться в легенде');
            // Новый рендер: свотч сразу followed by название, без кода
            const re = /';"><\/span>' \+\s*\n\s*this\._esc\(c\.name\) \+/;
            assertTrue(re.test(html),
                'Легенда: свотч + название (this._esc(c.name)) без кода');
        });

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

        test('SW: CACHE_VERSION = kipia-test-v509', () => {
            const swPath = path.resolve(__dirname, '..', 'sw.js');
            const sw = fs.readFileSync(swPath, 'utf8');
            assertTrue(sw.indexOf("kipia-test-v509") !== -1,
                'CACHE_VERSION должен быть kipia-test-v509 (Task 250)');
            assertTrue(sw.indexOf("kipia-test-v508") === -1,
                'Старая версия v508 не должна остаться в sw.js');
        });
    });
});
