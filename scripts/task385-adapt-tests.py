#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 385: адаптация старых тестов под новую архитектуру табеля:
#   1) «сотрудник» → «работник» в UI-ассертах (шапки сетки/итогов,
#      шторки, тосты, печать, span-обмен «Сотр»→«Рабо»);
#   2) карточка шахматки — read-only: ассерты тела карточки
#      переключены с _renderEmpPopup (теперь 2-строчная обёртка)
#      на _renderWorkerCard; гейты _canEdit → withEdit;
#   3) заголовок сетки — клик openWorkersPage (страница «Работники»);
#   4) _WORK_SCHEDULE_PAGES + 'ws-workers' (карты/крошки/доступ);
#   5) могильник Task 252 (старая легенда) — точные формы
#      «_renderLegend: function»/«this._renderLegend()» (новая
#      легенда Task 385 зовётся _renderLegendSheet);
#   6) Esc-окно test-task316 300→700 (строки закрытия легенды).

REPLS = {
    # ===== test-work-schedule.js =====
    'tests/test-work-schedule.js': [
        (
            'могильник легенды Task 252 — точные формы',
            """        test('JS: метод _renderLegend удалён из модуля WorkSchedule', () => {
            assertTrue(html.indexOf('_renderLegend') === -1,
                'Ни метод, ни вызов _renderLegend не должны остаться в коде');""",
            """        test('JS: метод _renderLegend удалён из модуля WorkSchedule', () => {
            // Task 385: новая легенда зовётся _renderLegendSheet (шторка
            // «Легенда» тулбара) — могильник проверяет ТОЧНЫЕ формы
            // старого метода (объявление и вызов)
            assertTrue(html.indexOf('_renderLegend: function') === -1 &&
                       html.indexOf('this._renderLegend()') === -1,
                'Ни метод, ни вызов _renderLegend не должны остаться в коде');""",
            1,
        ),
        (
            'SUBSECTIONS — ws-workers в карте',
            """        assertTrue(html.indexOf("_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals']") !== -1,
                'work-schedule в _WORK_SCHEDULE_PAGES (доступ Админу через *; Task 334: + страница итогов)');""",
            """        assertTrue(html.indexOf("_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers']") !== -1,
                'work-schedule в _WORK_SCHEDULE_PAGES (доступ Админу через *; Task 334: + итоги; Task 385: + «Работники»)');""",
            1,
        ),
        (
            'Task 311 HTML — заголовок «Работник» + openWorkersPage',
            """    test('HTML: Task 311 — кнопка «+ Сотрудник» УДАЛЕНА; заголовок «Сотрудник» — триггер', () => {
        // Task 311: кнопка из тулбара удалена — добавление сотрудника
        // выполняет заголовок колонки «Сотрудник» в шапке сетки
        // (класс ws-emp-head-add + onclick openEmployeeForm в _renderGrid)
        assertTrue(html.indexOf('id="wsEmpBtn"') === -1,
            'кнопка #wsEmpBtn удалена из тулбара');
        // рендер шапки: заголовок получает класс/onclick/плюсик
        const grid = html.slice(html.indexOf('_renderGrid: function'),
                                html.indexOf('_fitGrid: function'));
        assertTrue(grid.indexOf('ws-emp-head-add') !== -1,
            'заголовок «Сотрудник» несёт класс ws-emp-head-add (редакторам)');
        assertTrue(grid.indexOf('onclick="WorkSchedule.openEmployeeForm()"') !== -1,
            'клик заголовка → openEmployeeForm (прежний bottom-sheet)');""",
            """    test('HTML: Task 311 — кнопка «+ Сотрудник» УДАЛЕНА; заголовок «Работник» — триггер', () => {
        // Task 311: кнопка из тулбара удалена — добавление выполнял
        // заголовок колонки в шапке сетки; Task 385: заголовок
        // «Работник» ведёт на СТРАНИЦУ «Работники» (кнопки правки
        // переехали туда из карточки — класс ws-emp-head-add +
        // onclick openWorkersPage в _renderGrid)
        assertTrue(html.indexOf('id="wsEmpBtn"') === -1,
            'кнопка #wsEmpBtn удалена из тулбара');
        // рендер шапки: заголовок получает класс/onclick/плюсик
        const grid = html.slice(html.indexOf('_renderGrid: function'),
                                html.indexOf('_fitGrid: function'));
        assertTrue(grid.indexOf('ws-emp-head-add') !== -1,
            'заголовок «Работник» несёт класс ws-emp-head-add (редакторам)');
        assertTrue(grid.indexOf('onclick="WorkSchedule.openWorkersPage()"') !== -1,
            'клик заголовка → openWorkersPage (Task 385: страница «Работники»)');""",
            1,
        ),
        (
            'карты без сотрудников — + ws-workers',
            """        // Task 334: + мобильная страница итогов учёта (те же права)
        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals'",
            'в карте ролей модуля — шахматка и страница итогов (Task 334)');
    });

    test('HTML: bottom-sheet формы сотрудника жив (без изменений)', () => {""",
            """        // Task 334: + мобильная страница итогов учёта (те же права);
        // Task 385: + страница «Работники» (полные карточки)
        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals', 'ws-workers'",
            'в карте ролей модуля — шахматка, итоги (Task 334) и «Работники» (Task 385)');
    });

    test('HTML: bottom-sheet формы работника жив (без изменений)', () => {""",
            1,
        ),
        (
            'карты без trainings/vacations — + ws-workers',
            """        const m = html.match(/_WORK_SCHEDULE_PAGES:\\s*\\[([^\\]]+)\\]/);
        assertTrue(!!m, '_WORK_SCHEDULE_PAGES найден');
        // Task 334: + мобильная страница итогов учёта (те же права)
        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals'",
            'в карте ролей модуля — шахматка и страница итогов (Task 334)');
    });

    test('HTML: bottom-sheet «Новый отпуск» жив (без изменений)', () => {""",
            """        const m = html.match(/_WORK_SCHEDULE_PAGES:\\s*\\[([^\\]]+)\\]/);
        assertTrue(!!m, '_WORK_SCHEDULE_PAGES найден');
        // Task 334: + мобильная страница итогов учёта (те же права);
        // Task 385: + страница «Работники» (полные карточки)
        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals', 'ws-workers'",
            'в карте ролей модуля — шахматка, итоги (Task 334) и «Работники» (Task 385)');
    });

    test('HTML: bottom-sheet «Новый отпуск» жив (без изменений)', () => {""",
            1,
        ),
    ],

    # ===== test-task309.js =====
    'tests/test-task309.js': [
        (
            'блоки данных — _renderWorkerCard',
            """    test('JS: _renderEmpPopup — блоки данных из убранных вкладок', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: _renderEmpPopup — блоки данных из убранных вкладок', () => {
        // Task 385: тело карточки — в _renderWorkerCard (обёртка
        // _renderEmpPopup = чтение; withEdit=false/true)
        const rp = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
        (
            'отпуска в карточке — _renderWorkerCard',
            """    test('JS: отпуска в карточке — фильтр по году, чистые дни, БЕЗ итога года', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: отпуска в карточке — фильтр по году, чистые дни, БЕЗ итога года', () => {
        const rp = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
        (
            'мероприятия — _renderWorkerCard + withEdit',
            """    test('JS: мероприятия в карточке — сортировка по дате, кнопки только редакторам', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');
        assertTrue(rp.indexOf('WorkSchedule.editTraining(') !== -1,
            'кнопка правки ✎ в карточке');
        assertTrue(rp.indexOf('WorkSchedule.deleteTraining(') !== -1,
            'кнопка удаления ✕ в карточке');
        assertTrue(rp.indexOf('if (this._canEdit && trId)') !== -1,
            'кнопки — только ролям с правом записи');""",
            """    test('JS: мероприятия в карточке — сортировка по дате, кнопки только редакторам', () => {
        const rp = fnBody(INDEX_SRC, '_renderWorkerCard: function');
        assertTrue(rp.indexOf('WorkSchedule.editTraining(') !== -1,
            'кнопка правки ✎ в карточке (Task 385: страница «Работники»)');
        assertTrue(rp.indexOf('WorkSchedule.deleteTraining(') !== -1,
            'кнопка удаления ✕ в карточке (Task 385: страница «Работники»)');
        assertTrue(rp.indexOf('if (withEdit && trId)') !== -1,
            'кнопки — только с withEdit (Task 385: страница «Работники», редакторам)');""",
            1,
        ),
    ],

    # ===== test-task310.js =====
    'tests/test-task310.js': [
        (
            '«Старт цикла» — _renderWorkerCard',
            """    test('JS: _renderEmpPopup без «Старт цикла» и старт_цикла', () => {
        const rep = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: _renderEmpPopup без «Старт цикла» и старт_цикла', () => {
        const rep = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
        (
            'чистые дни — _renderWorkerCard',
            """    test('JS: дни периодов чистые (_vacNetDaysInYear), пометка праздников; итог года УБРАН', () => {
        const rep = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: дни периодов чистые (_vacNetDaysInYear), пометка праздников; итог года УБРАН', () => {
        const rep = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
    ],

    # ===== test-task311.js =====
    'tests/test-task311.js': [
        (
            'без строки «Сотрудник» — _renderWorkerCard',
            """    test('JS: _renderEmpPopup — без строки-заголовка «Сотрудник»', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: _renderEmpPopup — без строки-заголовка «Сотрудник»', () => {
        const rp = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
        (
            'без итога года — _renderWorkerCard',
            """    test('JS: _renderEmpPopup — без итога года отпусков', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: _renderEmpPopup — без итога года отпусков', () => {
        const rp = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
        (
            'заголовок-кнопка — openWorkersPage',
            """    test('JS: _renderGrid — заголовок «Сотрудник» становится кнопкой (редакторам)', () => {
        const gridPart = INDEX_SRC.slice(
            INDEX_SRC.indexOf('_renderGrid: function'),
            INDEX_SRC.indexOf('_fitGrid: function'));
        assertTrue(gridPart.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") !== -1,
            'класс ws-emp-head-add — только ролям с правом правки');
        assertTrue(gridPart.indexOf('onclick="WorkSchedule.openEmployeeForm()"') !== -1,
            'клик заголовка → openEmployeeForm');
        assertTrue(gridPart.indexOf('<i class="ws-emp-head-plus">+</i>') !== -1,
            'плюсик-индикатор у заголовка (редакторам)');
        // двойная защита: openEmployeeForm сам проверяет право записи
        const oef = fnBody(INDEX_SRC, 'openEmployeeForm: function');
        assertTrue(oef.indexOf('if (!this._canEdit) return;') !== -1,
            'openEmployeeForm проверяет право записи (зритель — мимо)');""",
            """    test('JS: _renderGrid — заголовок «Работник» становится кнопкой (редакторам)', () => {
        const gridPart = INDEX_SRC.slice(
            INDEX_SRC.indexOf('_renderGrid: function'),
            INDEX_SRC.indexOf('_fitGrid: function'));
        assertTrue(gridPart.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") !== -1,
            'класс ws-emp-head-add — только ролям с правом правки');
        assertTrue(gridPart.indexOf('onclick="WorkSchedule.openWorkersPage()"') !== -1,
            'клик заголовка → openWorkersPage (Task 385: страница «Работники»)');
        assertTrue(gridPart.indexOf('<i class="ws-emp-head-plus">+</i>') !== -1,
            'плюсик-индикатор у заголовка (редакторам)');
        // двойная защита: openWorkersPage сам проверяет право записи
        const owp = fnBody(INDEX_SRC, 'openWorkersPage: function');
        assertTrue(owp.indexOf('if (!this._canEdit) return;') !== -1,
            'openWorkersPage проверяет право записи (зритель — мимо)');""",
            1,
        ),
    ],

    # ===== test-task312.js =====
    'tests/test-task312.js': [
        (
            '«+ Отпуск…» — _renderWorkerCard + withEdit',
            """    test('JS: _renderEmpPopup — строка «+ Отпуск…» в блоке отпусков', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: _renderEmpPopup — строка «+ Отпуск…» в блоке отпусков', () => {
        // Task 385: тело — в _renderWorkerCard (страница «Работники»)
        const rp = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
        (
            'гейт withEdit у «+ Отпуск…»',
            """        // только редакторам
        assertTrue(rp.indexOf('if (this._canEdit) {') !== -1,
            'рендер строки обёрнут проверкой _canEdit');""",
            """        // только редакторам (Task 385: гейт withEdit — страница
        // «Работники»; попап шахматки зовёт с false)
        assertTrue(rp.indexOf('if (withEdit) {') !== -1,
            'рендер строки обёрнут гейтом withEdit');""",
            1,
        ),
        (
            'клик строки — _renderWorkerCard',
            """    test('JS: клик строки → onEmpAddVacation(таб. №) с экранированием', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');""",
            """    test('JS: клик строки → onEmpAddVacation(таб. №) с экранированием', () => {
        const rp = fnBody(INDEX_SRC, '_renderWorkerCard: function');""",
            1,
        ),
    ],

    # ===== test-task316.js =====
    'tests/test-task316.js': [
        (
            'Esc-окно 300 → 700 (строки легенды Task 385)',
            """        assertTrue(/ev\\.key === 'Escape'[\\s\\S]{0,300}selfOnce\\._daySelect\\(null\\);/.test(init),
            'Escape → _daySelect(null) рядом с закрытием попапов');""",
            """        // Task 385: между closeEmpPopup и _daySelect добавлено
        // закрытие шторки «Легенда» — окно расширено 300 → 700
        assertTrue(/ev\\.key === 'Escape'[\\s\\S]{0,700}selfOnce\\._daySelect\\(null\\);/.test(init),
            'Escape → _daySelect(null) рядом с закрытием попапов (+легенда Task 385)');""",
            1,
        ),
    ],

    # ===== test-task318.js =====
    'tests/test-task318.js': [
        (
            'HTML шторки — «работник»',
            """        assertTrue(sheet.indexOf('Увольнение сотрудника') !== -1, 'заголовок');
        assertTrue(sheet.indexOf('onclick="WorkSchedule.submitDismissForm()"') !== -1,
            'кнопка «Уволить» → submitDismissForm');
        assertTrue(sheet.indexOf('onclick="WorkSchedule.closeDismissForm()"') !== -1,
            'кнопка «Отмена» → closeDismissForm');
        assertTrue(sheet.indexOf('архиве справочника «Сотрудники»') !== -1,
            'пояснение: строка остаётся в архиве');""",
            """        assertTrue(sheet.indexOf('Увольнение работника') !== -1, 'заголовок (Task 385: работник)');
        assertTrue(sheet.indexOf('onclick="WorkSchedule.submitDismissForm()"') !== -1,
            'кнопка «Уволить» → submitDismissForm');
        assertTrue(sheet.indexOf('onclick="WorkSchedule.closeDismissForm()"') !== -1,
            'кнопка «Отмена» → closeDismissForm');
        assertTrue(sheet.indexOf('архиве справочника') !== -1,
            'пояснение: строка остаётся в архиве');""",
            1,
        ),
        (
            'подпись «Режим работы» — _renderWorkerCard',
            """    test('JS: _renderEmpPopup — подпись «Режим работы» (было «Тип»)', () => {
        const rp = methodText(INDEX_SRC, '_renderEmpPopup');""",
            """    test('JS: _renderEmpPopup — подпись «Режим работы» (было «Тип»)', () => {
        const rp = methodText(INDEX_SRC, '_renderWorkerCard');""",
            1,
        ),
        (
            '«Уволить…» — _renderWorkerCard + withEdit',
            """    test('JS: _renderEmpPopup — строка «Уволить…» (только редакторам)', () => {
        const rp = methodText(INDEX_SRC, '_renderEmpPopup');
        const i = rp.indexOf('ws-emp-dismiss');
        assertTrue(i !== -1, 'строка «Уволить…» в карточке');
        const seg = rp.slice(Math.max(0, i - 400), i + 400);
        assertTrue(seg.indexOf('this._canEdit') !== -1,
            'только ролям с правом записи');""",
            """    test('JS: _renderEmpPopup — строка «Уволить…» (только редакторам)', () => {
        const rp = methodText(INDEX_SRC, '_renderWorkerCard');
        const i = rp.indexOf('ws-emp-dismiss');
        assertTrue(i !== -1, 'строка «Уволить…» в карточке (Task 385: страница «Работники»)');
        const seg = rp.slice(Math.max(0, i - 400), i + 400);
        assertTrue(seg.indexOf('withEdit') !== -1,
            'только с withEdit (Task 385: страница «Работники», редакторам)');""",
            1,
        ),
        (
            'openDismissForm — «Работник не найден»',
            """        assertTrue(m.indexOf("'Сотрудник не найден'") !== -1, 'не найден — тост');""",
            """        assertTrue(m.indexOf("'Работник не найден'") !== -1, 'не найден — тост (Task 385: работник)');""",
            1,
        ),
    ],

    # ===== test-task321.js =====
    'tests/test-task321.js': [
        (
            'пустое состояние месяца — работники',
            """        assertTrue(t.els.wsTtBody.innerHTML.indexOf('Нет активных сотрудников') !== -1,
            'пустое состояние');""",
            """        assertTrue(t.els.wsTtBody.innerHTML.indexOf('Нет активных работников') !== -1,
            'пустое состояние (Task 385: работники)');""",
            1,
        ),
        (
            'годовая таблица — «Работник»',
            """        assertTrue(h.indexOf('<th class="ws-tt-emp"><span class="ws-tt-emp-head"') !== -1 &&
            h.indexOf('data-full="Сотрудник"') !== -1,
            'главная таблица: шапка с «Сотрудником» (Task 333, мобайл)');""",
            """        assertTrue(h.indexOf('<th class="ws-tt-emp"><span class="ws-tt-emp-head"') !== -1 &&
            h.indexOf('data-full="Работник"') !== -1,
            'главная таблица: шапка с «Работником» (Task 333, мобайл; Task 385: работник)');""",
            1,
        ),
    ],

    # ===== test-task323.js =====
    'tests/test-task323.js': [
        (
            'колонка «Работник» рендерится',
            """        assertTrue(h.indexOf('<th class="ws-tt-emp"><span class="ws-tt-emp-head"') !== -1 &&
            h.indexOf('data-full="Сотрудник"') !== -1,
            'заголовок колонки в разметке (мобайл/год)');""",
            """        assertTrue(h.indexOf('<th class="ws-tt-emp"><span class="ws-tt-emp-head"') !== -1 &&
            h.indexOf('data-full="Работник"') !== -1,
            'заголовок колонки в разметке (мобайл/год; Task 385: работник)');""",
            1,
        ),
    ],

    # ===== test-task327.js =====
    'tests/test-task327.js': [
        (
            'свёрнуто — «Работник»',
            """        assertEqual(JSON.stringify(names),
            JSON.stringify(['Сотрудник', 'Явки (дни)', 'Часы', 'Переработка (дни)']),
            'заголовки: Сотрудник + основные в порядке заявки (Task 331: подписи в днях)');""",
            """        assertEqual(JSON.stringify(names),
            JSON.stringify(['Работник', 'Явки (дни)', 'Часы', 'Переработка (дни)']),
            'заголовки: Работник (Task 385) + основные в порядке заявки (Task 331: подписи в днях)');""",
            1,
        ),
        (
            '«Ещё» — «Работник»',
            """        assertEqual(JSON.stringify(names), JSON.stringify([
            'Сотрудник', 'Явки (дни)', 'Часы', 'Переработка (дни)',
            'Отгул (ОВ)', 'Больничный (Б)', 'Отпуск (ОТ)', 'Уч. отпуск (У)',
            'Прогул (ПР)', 'День (Д)', 'Ночь (Н)', 'Прочие'
        ]), 'порядок заявки: основные (Task 331 — подписи в днях) + Отгул, Больничный, Отпуск, Уч. отпуск, Прогул, День, Ночь, Прочие');""",
            """        assertEqual(JSON.stringify(names), JSON.stringify([
            'Работник', 'Явки (дни)', 'Часы', 'Переработка (дни)',
            'Отгул (ОВ)', 'Больничный (Б)', 'Отпуск (ОТ)', 'Уч. отпуск (У)',
            'Прогул (ПР)', 'День (Д)', 'Ночь (Н)', 'Прочие'
        ]), 'порядок заявки: Работник (Task 385) + основные (Task 331) + Отгул, Больничный, Отпуск, Уч. отпуск, Прогул, День, Ночь, Прочие');""",
            1,
        ),
    ],

    # ===== test-task333.js =====
    'tests/test-task333.js': [
        (
            'пусто — «Нет работников»',
            """        assertTrue(t2.els.wsTtBody.innerHTML.indexOf('Нет сотрудников') !== -1,
            'нет ни активных, ни архива — пустое состояние');""",
            """        assertTrue(t2.els.wsTtBody.innerHTML.indexOf('Нет работников') !== -1,
            'нет ни активных, ни архива — пустое состояние (Task 385: работники)');""",
            1,
        ),
    ],

    # ===== test-task334.js =====
    'tests/test-task334.js': [
        (
            'карты — ws-workers',
            """        assertTrue(INDEX_SRC.indexOf(
            "_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals']") !== -1,
            '_WORK_SCHEDULE_PAGES: обе страницы модуля');""",
            """        assertTrue(INDEX_SRC.indexOf(
            "_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers']") !== -1,
            '_WORK_SCHEDULE_PAGES: страницы модуля (+ «Работники» — Task 385)');""",
            1,
        ),
    ],

    # ===== test-task335.js =====
    'tests/test-task335.js': [
        (
            'шапка сетки — Работник/Рабо',
            """    test('РЕНДЕР: шапка сетки — span «Сотрудник» ⇄ «Сотр»', () => {
        const i = INDEX_SRC.indexOf('class="ws-emp-head-txt"');
        assertTrue(i !== -1, 'span.ws-emp-head-txt в разметке шапки сетки');
        const chunk = INDEX_SRC.slice(i - 80, i + 160);
        assertTrue(chunk.indexOf('data-full="Сотрудник"') !== -1, 'data-full');
        assertTrue(chunk.indexOf('data-s4="Сотр"') !== -1, 'data-s4 «Сотр»');""",
            """    test('РЕНДЕР: шапка сетки — span «Работник» ⇄ «Рабо»', () => {
        const i = INDEX_SRC.indexOf('class="ws-emp-head-txt"');
        assertTrue(i !== -1, 'span.ws-emp-head-txt в разметке шапки сетки');
        const chunk = INDEX_SRC.slice(i - 80, i + 160);
        assertTrue(chunk.indexOf('data-full="Работник"') !== -1, 'data-full (Task 385: работник)');
        assertTrue(chunk.indexOf('data-s4="Рабо"') !== -1, 'data-s4 «Рабо»');""",
            1,
        ),
        (
            'шапки итогов — Работник/Рабо',
            """    test('РЕНДЕР: шапки итогов (месяц + год + архив) — span «Сотрудник» ⇄ «Сотр»', () => {
        const n = (INDEX_SRC.match(/class="ws-tt-emp-head"/g) || []).length;
        assertEqual(n, 3, 'три таблицы: месяц, годовая, архивная');
        const chunk = INDEX_SRC.slice(
            INDEX_SRC.indexOf('class="ws-tt-emp-head"') - 40,
            INDEX_SRC.indexOf('class="ws-tt-emp-head"') + 120);
        assertTrue(chunk.indexOf('data-full="Сотрудник"') !== -1, 'data-full');
        assertTrue(chunk.indexOf('data-s4="Сотр"') !== -1, 'data-s4 «Сотр»');""",
            """    test('РЕНДЕР: шапки итогов (месяц + год + архив) — span «Работник» ⇄ «Рабо»', () => {
        const n = (INDEX_SRC.match(/class="ws-tt-emp-head"/g) || []).length;
        assertEqual(n, 3, 'три таблицы: месяц, годовая, архивная');
        const chunk = INDEX_SRC.slice(
            INDEX_SRC.indexOf('class="ws-tt-emp-head"') - 40,
            INDEX_SRC.indexOf('class="ws-tt-emp-head"') + 120);
        assertTrue(chunk.indexOf('data-full="Работник"') !== -1, 'data-full (Task 385: работник)');
        assertTrue(chunk.indexOf('data-s4="Рабо"') !== -1, 'data-s4 «Рабо»');""",
            1,
        ),
    ],

    # ===== test-task340.js =====
    'tests/test-task340.js': [
        (
            'карточка read-only — новая архитектура',
            """    test('SRC: карточка read-only — элементы правки гейтятся _canEdit', () => {
        const fn = methodText(WS_CLIENT, '_renderEmpPopup');
        // «Уволить…», «+ Отпуск…», ✎/✕ — только редакторам: у «view»
        // карточка открывается БЕЗ правки
        const cnt = fn.split('if (this._canEdit').length - 1;
        assertTrue(cnt >= 3, 'все элементы правки гейтятся _canEdit (найдено ' + cnt + ')');
        assertTrue(fn.indexOf('ws-emp-dismiss') !== -1 &&
                   fn.indexOf('ws-emp-addvac') !== -1,
            '«Уволить…»/«+ Отпуск…» рендерятся по праву записи');
    });""",
            """    test('SRC: карточка read-only — элементы правки гейтятся withEdit', () => {
        // Task 385: карточка шахматки — ТОЛЬКО ЧТЕНИЕ для ВСЕХ уровней
        // (обёртка _renderEmpPopup → _renderWorkerCard(tabNo, false));
        // элементы правки живут в _renderWorkerCard с гейтом withEdit
        // и рендерятся на странице «Работники» (_renderWorkersPage,
        // только редакторам — двойная защита openWorkersPage)
        const wrap = methodText(WS_CLIENT, '_renderEmpPopup');
        assertTrue(wrap.indexOf('_renderWorkerCard(tabNo, false)') !== -1,
            'обёртка зовёт _renderWorkerCard с withEdit=false (Task 385)');
        const fn = methodText(WS_CLIENT, '_renderWorkerCard');
        const cnt = fn.split('if (withEdit').length - 1;
        assertTrue(cnt >= 4, 'все элементы правки гейтятся withEdit (найдено ' + cnt + ')');
        assertTrue(fn.indexOf('ws-emp-dismiss') !== -1 &&
                   fn.indexOf('ws-emp-addvac') !== -1,
            '«Уволить…»/«+ Отпуск…» рендерятся по withEdit (страница «Работники»)');
    });""",
            1,
        ),
    ],

    # ===== test-task341.js =====
    'tests/test-task341.js': [
        (
            'печать — «Работник»',
            """        assertTrue(html.indexOf('">Сотрудник</th>') !== -1,
            'заголовок колонки сотрудника');""",
            """        assertTrue(html.indexOf('">Работник</th>') !== -1,
            'заголовок колонки работника (Task 385)');""",
            1,
        ),
    ],

    # ===== test-task361.js =====
    'tests/test-task361.js': [
        (
            'SRC — inline ширина «Работник»',
            """        assertTrue(b.indexOf("empWmm + 'mm\\">Сотрудник</th>'") !== -1,
            'inline ширина на th .wsp-emp');""",
            """        assertTrue(b.indexOf("empWmm + 'mm\\">Работник</th>'") !== -1,
            'inline ширина на th .wsp-emp (Task 385: работник)');""",
            1,
        ),
        (
            'VM — empWidth regex «Работник»',
            """    function empWidth(html) {
        var m = html.match(/<th class="wsp-emp" style="width:(\\d+(?:\\.\\d+)?)mm">Сотрудник<\\/th>/);
        return m ? parseFloat(m[1]) : null;
    }""",
            """    function empWidth(html) {
        var m = html.match(/<th class="wsp-emp" style="width:(\\d+(?:\\.\\d+)?)mm">Работник<\\/th>/);
        return m ? parseFloat(m[1]) : null;
    }""",
            1,
        ),
    ],

    # ===== test-task384.js =====
    'tests/test-task384.js': [
        (
            'HTML — «Новый работник»',
            """    test('id заголовка и кнопки шторки сотрудника', () => {
        assertTrue(INDEX_SRC.indexOf('id="wsEmpSheetTitle">Новый сотрудник<') !== -1,
            'заголовок #wsEmpSheetTitle');""",
            """    test('id заголовка и кнопки шторки работника', () => {
        assertTrue(INDEX_SRC.indexOf('id="wsEmpSheetTitle">Новый работник<') !== -1,
            'заголовок #wsEmpSheetTitle (Task 385: работник)');""",
            1,
        ),
        (
            'комментарий карточки — Task 385',
            """    test('комментарий карточки: центр правки Task 384', () => {
        // HTML-комментарий попапа (CSS-комментарий Task 309 выше по
        // файлу — не тот маркер)
        const i = INDEX_SRC.indexOf('<!-- Task 309: карточка сотрудника — попап у колонки ФИО');
        assertTrue(i !== -1, 'HTML-комментарий карточки найден');
        const chunk = INDEX_SRC.slice(i, i + 1400);
        assertTrue(chunk.indexOf('Task 384: карточка — ЦЕНТР ПРАВКИ') !== -1,
            'комментарий описывает Task 384');
        assertTrue(chunk.indexOf('updateVacation/deleteVacation') !== -1,
            'упомянуты серверные вызовы правки');
    });""",
            """    test('комментарий карточки: read-only по Task 385', () => {
        // HTML-комментарий попапа (CSS-комментарий Task 309 выше по
        // файлу — не тот маркер). Task 385: карточка — только чтение,
        // правки переехали на страницу «Работники»
        const i = INDEX_SRC.indexOf('<!-- Task 309: карточка работника — попап у колонки ФИО');
        assertTrue(i !== -1, 'HTML-комментарий карточки найден');
        const chunk = INDEX_SRC.slice(i, i + 1600);
        assertTrue(chunk.indexOf('Task 385: карточка — ТОЛЬКО ЧТЕНИЕ') !== -1,
            'комментарий описывает Task 385 (read-only)');
        assertTrue(chunk.indexOf('страницу «Работники»') !== -1,
            'правки переехали на страницу «Работники»');
    });""",
            1,
        ),
        (
            'профиль «Правка данных…» — _renderWorkerCard',
            """    test('профиль: строка «Правка данных…» (редакторам)', () => {
        const fn = methodText(INDEX_SRC, '_renderEmpPopup');""",
            """    test('профиль: строка «Правка данных…» (редакторам)', () => {
        // Task 385: тело карточки — _renderWorkerCard (страница
        // «Работники», withEdit=true; попап шахматки — false)
        const fn = methodText(INDEX_SRC, '_renderWorkerCard');""",
            1,
        ),
        (
            'отпуска ✎/✕ — _renderWorkerCard + withEdit',
            """    test('отпуска: ✎/✕ у периодов (редакторам, только с id)', () => {
        const fn = methodText(INDEX_SRC, '_renderEmpPopup');
        assertTrue(fn.indexOf('WorkSchedule.editVacation(') !== -1, '✎ → editVacation(id)');
        assertTrue(fn.indexOf('WorkSchedule.deleteVacation(') !== -1, '✕ → deleteVacation(id)');
        assertTrue(fn.indexOf('if (this._canEdit && vId)') !== -1,
            'кнопки только редакторам и записям с id');""",
            """    test('отпуска: ✎/✕ у периодов (редакторам, только с id)', () => {
        const fn = methodText(INDEX_SRC, '_renderWorkerCard');
        assertTrue(fn.indexOf('WorkSchedule.editVacation(') !== -1, '✎ → editVacation(id)');
        assertTrue(fn.indexOf('WorkSchedule.deleteVacation(') !== -1, '✕ → deleteVacation(id)');
        assertTrue(fn.indexOf('if (withEdit && vId)') !== -1,
            'кнопки только с withEdit (страница «Работники») и записям с id');""",
            1,
        ),
        (
            'мероприятия «+ Мероприятие…» — _renderWorkerCard',
            """    test('мероприятия: строка «+ Мероприятие…» (редакторам)', () => {
        const fn = methodText(INDEX_SRC, '_renderEmpPopup');""",
            """    test('мероприятия: строка «+ Мероприятие…» (редакторам)', () => {
        const fn = methodText(INDEX_SRC, '_renderWorkerCard');""",
            1,
        ),
        (
            'openEmpEditForm — «Правка работника»',
            """        assertTrue(fn.indexOf("'Правка сотрудника'") !== -1, 'заголовок режима правки');""",
            """        assertTrue(fn.indexOf("'Правка работника'") !== -1, 'заголовок режима правки (Task 385: работник)');""",
            1,
        ),
        (
            'openEmployeeForm — «Новый работник»',
            """        assertTrue(fn.indexOf("'Новый сотрудник'") !== -1, 'заголовок создания');""",
            """        assertTrue(fn.indexOf("'Новый работник'") !== -1, 'заголовок создания (Task 385: работник)');""",
            1,
        ),
        (
            'submitEmployeeForm — «Данные работника обновлены»',
            """        assertTrue(fn.indexOf("'Данные сотрудника обновлены'") !== -1, 'тост успеха');""",
            """        assertTrue(fn.indexOf("'Данные работника обновлены'") !== -1, 'тост успеха (Task 385: работник)');""",
            1,
        ),
        (
            'VM: openEmpEditForm — «Правка работника»',
            """        assertEqual(els.wsEmpSheetTitle.textContent, 'Правка сотрудника', 'заголовок');""",
            """        assertEqual(els.wsEmpSheetTitle.textContent, 'Правка работника', 'заголовок (Task 385)');""",
            1,
        ),
        (
            'VM: openEmployeeForm — «Новый работник»',
            """        assertEqual(els.wsEmpSheetTitle.textContent, 'Новый сотрудник', 'заголовок');""",
            """        assertEqual(els.wsEmpSheetTitle.textContent, 'Новый работник', 'заголовок (Task 385)');""",
            1,
        ),
        (
            'VM: submit — тост «Данные работника»',
            """        assertTrue(api.toasts().indexOf('Данные сотрудника обновлены') !== -1,
            'тост успеха');""",
            """        assertTrue(api.toasts().indexOf('Данные работника обновлены') !== -1,
            'тост успеха (Task 385: работник)');""",
            1,
        ),
    ],
}

for path, repls in REPLS.items():
    s = open(path, encoding='utf-8').read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, '%s: [%s] найдено %d (ожидалось %d)' % (path, name, found, cnt)
        s = s.replace(old, new)
    open(path, 'w', encoding='utf-8').write(s)
    print('%s: адаптировано правок: %d' % (path, len(repls)))
print('Task 385: адаптация тестов завершена')
