#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 389 — заявка пользователя (4 части):
#   1) «В окне мероприятий, цвет общего фона за мероприятиями с
#      прошедшими датами сделай как раньше был общий фон (как сейчас
#      общий фон выше за оглавлением окна)» → строки ПРОШЕДШИХ
#      мероприятий — ПРОЗРАЧНЫЕ (background: transparent в обеих
#      темах): сквозь них виден ОБЩИЙ ФОН ОКНА var(--bg-tertiary) —
#      тот же, что выше заголовка .ws-ep-cap («как раньше», до
#      Task 380); «светлее окна» Task 380/381 для прошедших ОТМЕНЕНО;
#      текущие/будущие — ТЕМНЕЕ окна как прежде (не тронуты);
#   2) «На странице "Работники", кнопку "Добавить работника"
#      перенеси с бара на общую вкладку работников» → кнопка
#      УДАЛЕНА из шапки страницы (#page-ws-workers), рендерится в
#      шапке сводки «Общей» вкладки (_renderWorkersGeneral; id
#      wsWorkersAddBtn СОХРАНЁН; только у редакторов _canEdit);
#      пустой список больше НЕ прерывает рендер — «Общая» вкладка с
#      кнопкой показывается и без работников;
#   3) «в общей вкладке допиши информацию что, на текущий момент 12
#      работников (автоматический подсчёт), по штату 14 из которых
#      2 мастера, 5 сменных и 7 дневных» → шапка сводки: «На текущий
#      момент: N …» (N — АВТОПОДСЧЁТ по живому списку, склонение
#      _plural) + «По штату: 14, из которых 2 мастера, 5 сменных и
#      7 дневных.» (штат — константа);
#   4) «Фон ярлыков и окон вкладок сделай не прозрачным, и
#      расположи их с левого края» → ярлыки .ws-wtab — СПЛОШНОЙ фон
#      (было rgba-тинты — сетка-«миллиметровка» страницы
#      просвечивала): неактивный var(--bg-primary)/#E4E0D3 (тёмная/
#      светлая), hover — сплошной светлее; ОКНО «Общей» вкладки —
#      панель .ws-wgen (сплошной var(--bg-tertiary), как .ws-wcard —
#      окно вкладки работника уже сплошное); блок вкладок — с ЛЕВОГО
#      КРАЯ (.ws-workers-body margin: 0 auto → 0).
#
# Все правки — КЛИЕНТСКИЕ (index.html); серверных шагов НЕТ.
# SW-бамп отдельным скриптом: task389-bump-sw.py (v616 → v617).

import sys

INDEX = 'index.html'


def patch(path, repls):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: применено правок: %d' % (path, len(repls)))


REPLS = []

# ============================================================
# 1. ОКНО «МЕРОПРИЯТИЯ»: прошедшие — общий фон окна (прозрачные)
# ============================================================
REPLS.append(('ep-past: комментарий + правила → transparent', """
       Окно «Нормы» (.ws-cal-panel) НЕ тронута — там свой gap */
    .ws-ep-item {
        padding: 3px 10px;
        margin: 0 -10px;
        background: rgba(0, 0, 0, 0.45);
    }
    .ws-ep-item.ws-ep-past {
        background: rgba(255, 255, 255, 0.12);
    }
    [data-theme="light"] .ws-ep-item {
        background: rgba(0, 0, 0, 0.12);
    }
    [data-theme="light"] .ws-ep-item.ws-ep-past {
        background: rgba(255, 255, 255, 0.55);
    }
""", """
       Окно «Нормы» (.ws-cal-panel) НЕ тронута — там свой gap.
       Task 389 (заявка: «в окне мероприятий, цвет общего фона за
       мероприятиями с прошедшими датами сделай как раньше был
       общий фон (как сейчас общий фон выше за оглавлением окна)»):
       строки ПРОШЕДШИХ мероприятий — ПРОЗРАЧНЫЕ (background:
       transparent, обе темы) — сквозь них виден ОБЩИЙ ФОН ОКНА
       var(--bg-tertiary), тот же, что выше заголовка .ws-ep-cap
       («как раньше», до Task 380); «светлее окна» Task 380/381 для
       прошедших ОТМЕНЕНО. Текущие/будущие — ТЕМНЕЕ окна как прежде
       (rgba-тинты не тронуты); класс .ws-ep-past, каскад
       специфичностей (0,1,0 → 0,2,0 → 0,2,0 → 0,3,0) и склейка
       строк сохранены — видимый край цвета остаётся только на
       СТЫКЕ прошедших (общий фон) и идущих-будущих (тёмная зона) */
    .ws-ep-item {
        padding: 3px 10px;
        margin: 0 -10px;
        background: rgba(0, 0, 0, 0.45);
    }
    .ws-ep-item.ws-ep-past {
        background: transparent;
    }
    [data-theme="light"] .ws-ep-item {
        background: rgba(0, 0, 0, 0.12);
    }
    [data-theme="light"] .ws-ep-item.ws-ep-past {
        background: transparent;
    }
""", 1))

# ============================================================
# 2. СТРАНИЦА «РАБОТНИКИ»: CSS — сплошные фоны, левый край,
#    панель «Общей» вкладки, шапка сводки (инфо + кнопка)
# ============================================================
REPLS.append(('css-комментарий секции: кнопка на «Общей» вкладке', """
       тех же классов); кнопка «Добавить работника» в шапке страницы
       (Task 386: прежде значок «+») — шторка создания #wsEmpSheet
       (openEmployeeForm). Task 388 (заявка): представление — ВКЛАДКИ,
""", """
       тех же классов); кнопка «Добавить работника» — на «Общей»
       вкладке (Task 389: перенесена из шапки страницы; Task 386:
       прежде значок «+» в шапке) — шторка создания #wsEmpSheet
       (openEmployeeForm). Task 388 (заявка): представление — ВКЛАДКИ,
""", 1))

REPLS.append(('ws-workers-body: с левого края (margin: 0)', """
    .ws-workers-body {
        padding: 10px 12px 24px;
        max-width: 1020px;   /* Task 388: вкладки слева + карточка справа */
        margin: 0 auto;
    }
""", """
    .ws-workers-body {
        padding: 10px 12px 24px;
        max-width: 1020px;   /* Task 388: вкладки слева + карточка справа */
        /* Task 389 (заявка): ярлыки и окна вкладок — с ЛЕВОГО КРАЯ
           (было авто-центрирование — блок стоял по центру на
           широких экранах) */
        margin: 0;
    }
""", 1))

REPLS.append(('ws-workers-count: margin 0 (живёт в шапке сводки)', """
    .ws-workers-count {
        font-size: 12px;
        opacity: 0.75;
        margin: 2px 2px 10px;
    }
""", """
    .ws-workers-count {
        font-size: 12px;
        opacity: 0.75;
        /* Task 389: строка живёт в шапке сводки .ws-wgen-head —
           внешние отступы ушли контейнеру */
        margin: 0;
    }
""", 1))

REPLS.append(('вкладки: комментарий — сплошные фоны Task 389', """
    /* Task 388 (заявка): ярлыки-вкладки СТОЛБИКОМ СЛЕВА (браузерный
       вид): активный ярлык подсвечен и «пристыкован» к телу
       (margin-right:-1px, правая рамка прозрачна); тело — карточка
       выбранного работника / сводная таблица «Общей» вкладки */
    .ws-workers-layout {
""", """
    /* Task 388 (заявка): ярлыки-вкладки СТОЛБИКОМ СЛЕВА (браузерный
       вид): активный ярлык подсвечен и «пристыкован» к телу
       (margin-right:-1px, правая рамка прозрачна); тело — карточка
       выбранного работника / сводная таблица «Общей» вкладки.
       Task 389 (заявка: «фон ярлыков и окон вкладок сделай не
       прозрачным»): ярлыки — СПЛОШНОЙ цвет (были rgba-тинты —
       фоновая сетка-«миллиметровка» страницы просвечивала):
       неактивный — var(--bg-primary) / #E4E0D3 (тёмная/светлая),
       hover — сплошной светлее; активный — как ОКНО вкладки
       (var(--bg-tertiary), «пристыкован»). Окна вкладок: «Общая» —
       панель .ws-wgen (сплошной var(--bg-tertiary)), работник —
       .ws-wcard (уже сплошной) */
    .ws-workers-layout {
""", 1))

REPLS.append(('ws-wtab: сплошной фон неактивного (тёмная)', """
        border-radius: 8px 0 0 8px;
        background: rgba(255, 255, 255, 0.04);
        color: var(--text-secondary, rgba(255,255,255,0.65));
""", """
        border-radius: 8px 0 0 8px;
        background: var(--bg-primary, #1a2233);   /* Task 389: сплошной */
        color: var(--text-secondary, rgba(255,255,255,0.65));
""", 1))

REPLS.append(('ws-wtab:hover: сплошной светлее (тёмная)', """
    .ws-wtab:hover {
        background: rgba(255, 255, 255, 0.09);
        color: var(--text-primary, #e0e0e0);
    }
""", """
    .ws-wtab:hover {
        /* Task 389: сплошной, светлее неактивного var(--bg-primary) */
        background: #243048;
        color: var(--text-primary, #e0e0e0);
    }
""", 1))

REPLS.append(('светлая тема: ws-wtab сплошные', """
    [data-theme="light"] .ws-wtab {
        border-color: rgba(0, 0, 0, 0.12);
        background: rgba(0, 0, 0, 0.04);
        color: #444;
    }
    [data-theme="light"] .ws-wtab:hover { background: rgba(0, 0, 0, 0.08); color: #111; }
""", """
    [data-theme="light"] .ws-wtab {
        border-color: rgba(0, 0, 0, 0.12);
        background: #E4E0D3;   /* Task 389: сплошной */
        color: #444;
    }
    [data-theme="light"] .ws-wtab:hover { background: #DBD6C8; color: #111; }
""", 1))

REPLS.append(('ws-wgen: панель-окно «Общей» вкладки + шапка сводки', """
    /* Task 388: «Общая» вкладка — сводная таблица по ВСЕМ работникам */
    .ws-wgen-head { margin: 2px 2px 10px; }
""", """
    /* Task 388: «Общая» вкладка — сводная таблица по ВСЕМ
       работникам. Task 389 (заявка): ОКНО «Общей» вкладки — панель
       .ws-wgen со СПЛОШНЫМ фоном (как карточка .ws-wcard —
       сетка-«миллиметровка» страницы не просвечивает); шапка
       сводки — flex: численность (текущая — автоматический подсчёт,
       по штату — константа) слева, кнопка «Добавить работника»
       (перенос из шапки страницы) справа */
    .ws-wgen {
        background: var(--bg-tertiary, #0e1621);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 12px 14px 10px;
    }
    [data-theme="light"] .ws-wgen {
        background: var(--bg-tertiary, #e9e7de);
        border-color: rgba(0,0,0,0.1);
    }
    .ws-wtab-body .ws-wgen { margin-bottom: 0; }
    .ws-wgen-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 6px 12px;
        margin: 2px 2px 10px;
    }
    .ws-wgen-info {
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 3px;
    }
    .ws-wgen-staff {
        font-size: 12px;
        opacity: 0.75;
    }
""", 1))

# ============================================================
# 3. СТРАНИЦА «РАБОТНИКИ»: HTML — кнопка из шапки → «Общая» вкладка
# ============================================================
REPLS.append(('тулбар: комментарий Task 311 — кнопка на «Общей»', """
                         (Task 307 приносил её сюда со страницы
                         «Сотрудники»). Task 386: добавление работника —
                         кнопкой «Добавить работника» в шапке страницы
                         «Работники» (заголовок шапки сетки — просто
                         надпись, функции кнопки больше не несёт). -->
""", """
                         (Task 307 приносил её сюда со страницы
                         «Сотрудники»). Task 386: добавление работника —
                         кнопкой «Добавить работника» (Task 389: на
                         «Общей» вкладке страницы «Работники»; Task 386:
                         была в шапке страницы — заголовок шапки сетки
                         просто надпись, функции кнопки не несёт). -->
""", 1))

REPLS.append(('страница: кнопка удалена из шапки', """
             данные обновляются вместе с сеткой (loadGrid(true) →
             _renderGrid → _renderWorkersIfOpen); «Добавить
             работника» в шапке (Task 386: прежде значок «+») —
             шторка создания (openEmployeeForm) -->
        <div id="page-ws-workers" class="page-content">
            <div class="page-inline-header">
                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Работники</div>
                <!-- Task 386 (заявка): текстовая кнопка «Добавить
                     работника» (прежде — значок «+») -->
                <button type="button" id="wsWorkersAddBtn" class="ws-workers-add" onclick="WorkSchedule.openEmployeeForm()" aria-label="Добавить работника">Добавить работника</button>
            </div>
            <div id="wsWorkersBody" class="ws-workers-body"></div>
        </div>
""", """
             данные обновляются вместе с сеткой (loadGrid(true) →
             _renderGrid → _renderWorkersIfOpen); «Добавить
             работника» — на «Общей» вкладке (Task 389: перенесена
             из шапки страницы; Task 386: прежде значок «+» в шапке)
             — шторка создания (openEmployeeForm) -->
        <div id="page-ws-workers" class="page-content">
            <div class="page-inline-header">
                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Работники</div>
                <!-- Task 389 (заявка): кнопка «Добавить работника»
                     ПЕРЕНЕСЕНА из шапки страницы на «Общую» вкладку
                     — рендерит _renderWorkersGeneral (id сохранён) -->
            </div>
            <div id="wsWorkersBody" class="ws-workers-body"></div>
        </div>
""", 1))

# ============================================================
# 4. JS: _renderWorkersPage — без раннего выхода; .ws-wgen-панель
# ============================================================
REPLS.append(('renderWorkersPage: ранний выход удалён', """
        _renderWorkersPage: function() {
            var body = document.getElementById('wsWorkersBody');
            if (!body) return;
            if (!this._EMPLOYEES || !this._EMPLOYEES.length) {
                body.innerHTML = '<div class="ws-tt-empty">Нет активных работников. ' +
                                 'Добавьте первого кнопкой «Добавить работника» в шапке страницы.</div>';
                return;
            }
            var withEdit = !!this._canEdit;
            // ПО ФАМИЛЬНО ПО АЛФАВИТУ: сортировка по ФИО (фамилия —
            // первое слово ФИО) — порядок ярлыков вкладок
            var list = this._EMPLOYEES.slice().sort(function(a, b) {
""", """
        _renderWorkersPage: function() {
            var body = document.getElementById('wsWorkersBody');
            if (!body) return;
            var withEdit = !!this._canEdit;
            // ПО ФАМИЛЬНО ПО АЛФАВИТУ: сортировка по ФИО (фамилия —
            // первое слово ФИО) — порядок ярлыков вкладок.
            // Task 389: пустой список НЕ прерывает рендер — «Общая»
            // вкладка (кнопка «Добавить работника», численность)
            // показывается и без работников
            var list = (this._EMPLOYEES || []).slice().sort(function(a, b) {
""", 1))

REPLS.append(('renderWorkersPage: «Общая» — панель .ws-wgen', """
            // тело вкладки: «Общая» — сводная таблица всех
            // работников; работник — полная карточка (withEdit)
            var contentHtml = '';
            if (tab === 'general') {
                contentHtml = this._renderWorkersGeneral(list);
            } else {
""", """
            // тело вкладки: «Общая» — сводная таблица всех
            // работников (Task 389: ОКНО-панель .ws-wgen со сплошным
            // фоном — как карточка работника); работник — полная
            // карточка (withEdit)
            var contentHtml = '';
            if (tab === 'general') {
                contentHtml = '<div class="ws-wgen">' +
                    this._renderWorkersGeneral(list) + '</div>';
            } else {
""", 1))

# ============================================================
# 5. JS: _renderWorkersGeneral — численность + кнопка «Добавить»
# ============================================================
REPLS.append(('renderWorkersGeneral: шапка сводки (автоподсчёт + штат + кнопка)', """
        // Task 388: ОБЩАЯ вкладка — сводная информация по ВСЕМ
        // работникам (по фамильно по алфавиту): таб. №, ФИО, режим
        // работы (тип/смена), должность, дата приёма, отпуск года
        // («чистые» дни — праздники ст. 120 ТК РФ вычтены) и число
        // мероприятий месяца шахматки
        _renderWorkersGeneral: function(list) {
            var monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                              'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
            var shiftN = 0, dayN = 0;
            var html = '<div class="ws-wgen-head"><span class="ws-workers-count">' +
                       list.length + ' ' +
                       this._plural(list.length, ['работник', 'работника', 'работников']) +
                       '</span></div>';
            html += '<table class="ws-wgen-table"><thead><tr>' +
""", """
        // Task 388: ОБЩАЯ вкладка — сводная информация по ВСЕМ
        // работникам (по фамильно по алфавиту): таб. №, ФИО, режим
        // работы (тип/смена), должность, дата приёма, отпуск года
        // («чистые» дни — праздники ст. 120 ТК РФ вычтены) и число
        // мероприятий месяца шахматки.
        // Task 389 (заявка): в шапке сводки — ЧИСЛЕННОСТЬ: «на
        // текущий момент N …» (N — АВТОМАТИЧЕСКИЙ ПОДСЧЁТ по живому
        // списку, склонение _plural) и «по штату 14, из которых
        // 2 мастера, 5 сменных и 7 дневных» (штат — константа);
        // кнопка «Добавить работника» ПЕРЕНЕСЕНА сюда из шапки
        // страницы (id wsWorkersAddBtn сохранён; только у
        // редакторов — _canEdit)
        _renderWorkersGeneral: function(list) {
            var monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                              'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
            var shiftN = 0, dayN = 0;
            var addBtn = this._canEdit
                ? '<button type="button" id="wsWorkersAddBtn" class="ws-workers-add" onclick="WorkSchedule.openEmployeeForm()" aria-label="Добавить работника">Добавить работника</button>'
                : '';
            var html = '<div class="ws-wgen-head"><div class="ws-wgen-info">' +
                       '<span class="ws-workers-count">На текущий момент: ' +
                       list.length + ' ' +
                       this._plural(list.length, ['работник', 'работника', 'работников']) +
                       ' (автоматический подсчёт).</span>' +
                       '<span class="ws-wgen-staff">По штату: 14, из которых ' +
                       '2 мастера, 5 сменных и 7 дневных.</span>' +
                       '</div>' + addBtn + '</div>';
            if (!list.length) {
                html += '<div class="ws-tt-empty">Нет активных работников — добавьте первого кнопкой «Добавить работника».</div>';
                return html;
            }
            html += '<table class="ws-wgen-table"><thead><tr>' +
""", 1))

if __name__ == '__main__':
    if '--dry-run' in sys.argv:
        with open(INDEX, encoding='utf-8') as f:
            s = f.read()
        bad = 0
        for name, old, new, cnt in REPLS:
            found = s.count(old)
            status = 'OK' if found == cnt else '!!!'
            if found != cnt:
                bad += 1
            print('[%s] %s: найдено %d (ожидалось %d)' % (status, name, found, cnt))
        print('dry-run итог: несовпадений %d из %d' % (bad, len(REPLS)))
        sys.exit(1 if bad else 0)
    patch(INDEX, REPLS)
    print('Task 389: все правки применены.')
