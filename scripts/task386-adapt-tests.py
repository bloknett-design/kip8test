#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 386: адаптация тестов под новую реальность (заявка):
#   • кнопка «Легенда» → «Обозначения»; шторка — ДВА вида (узкий
#     190px без наименований / широкий min(400px,45vw) с шевроном
#     #wsLgChv); мобильного оверлея нет — страница #page-ws-legend;
#     класс ws-legend-open удалён; ширины явные (_legendWidthPx);
#   • заголовок шапки сетки — ПРОСТО надпись «Работники» (класс
#     ws-emp-head-add/onclick/плюсик и их CSS-правила удалены);
#   • кнопка страницы «Работники»: «+» → «Добавить работника».
# Файлы: test-task385.js (крупная адаптация), test-task311.js,
# test-task318.js, test-task330.js, test-task335.js, test-task337.js,
# test-task338.js, test-work-schedule.js, test-task334.js, run-all.js.

import io


def patch(path, repls):
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: применено правок: %d' % (path, len(repls)))


# ============================================================
# test-task385.js
# ============================================================
patch('tests/test-task385.js', [
    # 1. Кнопка ряда 2: «Легенда» → «Обозначения»
    ('кнопка «Обозначения»', '''    test('HTML: кнопка «Легенда» в ряду 2 (после вкладки «Год»)', () => {
        const iYear = INDEX_SRC.indexOf('id="wsTtTabYear"');
        const iLeg = INDEX_SRC.indexOf('id="wsLegendBtn"');
        assertTrue(iYear !== -1 && iLeg !== -1 && iYear < iLeg,
            'кнопка «Легенда» после вкладок итогов');
        const chunk = INDEX_SRC.slice(iLeg - 200, iLeg + 300);
        assertTrue(chunk.indexOf('WorkSchedule.toggleLegend()') !== -1,
            'onclick → toggleLegend');
        assertTrue(chunk.indexOf('aria-pressed="false"') !== -1,
            'кнопка-переключатель (aria-pressed)');
        assertTrue(chunk.indexOf('>Легенда</button>') !== -1,
            'текст «Легенда»');
    });
''', '''    test('HTML: кнопка «Обозначения» в ряду 2 (после вкладки «Год»)', () => {
        const iYear = INDEX_SRC.indexOf('id="wsTtTabYear"');
        const iLeg = INDEX_SRC.indexOf('id="wsLegendBtn"');
        assertTrue(iYear !== -1 && iLeg !== -1 && iYear < iLeg,
            'кнопка «Обозначения» после вкладок итогов');
        const chunk = INDEX_SRC.slice(iLeg - 200, iLeg + 400);
        assertTrue(chunk.indexOf('WorkSchedule.toggleLegend()') !== -1,
            'onclick → toggleLegend');
        assertTrue(chunk.indexOf('aria-pressed="false"') !== -1,
            'кнопка-переключатель (aria-pressed)');
        assertTrue(chunk.indexOf('>Обозначения</button>') !== -1,
            'текст «Обозначения» (Task 386: «словом попроще»)');
    });
''', 1),

    # 2. Шторка: заголовок «Обозначения» + шеврон wsLgChv
    ('шторка — заголовок + шеврон', '''    test('HTML: шторка «Легенда» — структура (в #wsWsBody после итогов)', () => {
        const iDrawer = INDEX_SRC.indexOf('id="wsTotalsDrawer"');
        const iLegend = INDEX_SRC.indexOf('id="wsLegendDrawer"');
        assertTrue(iDrawer !== -1 && iLegend !== -1 && iDrawer < iLegend,
            'шторка легенды рядом с итогами (общая рабочая область)');
        const chunk = INDEX_SRC.slice(iLegend - 100, iLegend + 700);
        assertTrue(chunk.indexOf('ws-legend-drawer') !== -1, 'класс ws-legend-drawer');
        assertTrue(chunk.indexOf('ws-legend-inner') !== -1, 'внутренняя панель');
        assertTrue(chunk.indexOf('id="wsLegendBody"') !== -1, 'тело контента #wsLegendBody');
        assertTrue(chunk.indexOf('ws-lg-edge') !== -1, 'левый бортик');
        assertTrue(chunk.indexOf('Сокращения в шахматке') !== -1, 'заголовок шторки');
    });
''', '''    test('HTML: шторка «Обозначения» — структура + шеврон (Task 386)', () => {
        const iDrawer = INDEX_SRC.indexOf('id="wsTotalsDrawer"');
        const iLegend = INDEX_SRC.indexOf('id="wsLegendDrawer"');
        assertTrue(iDrawer !== -1 && iLegend !== -1 && iDrawer < iLegend,
            'шторка легенды рядом с итогами (общая рабочая область)');
        const chunk = INDEX_SRC.slice(iLegend - 100, iLegend + 900);
        assertTrue(chunk.indexOf('ws-legend-drawer') !== -1, 'класс ws-legend-drawer');
        assertTrue(chunk.indexOf('ws-legend-inner') !== -1, 'внутренняя панель');
        assertTrue(chunk.indexOf('id="wsLegendBody"') !== -1, 'тело контента #wsLegendBody');
        assertTrue(chunk.indexOf('ws-lg-edge') !== -1, 'левый бортик');
        assertTrue(chunk.indexOf('>Обозначения</div>') !== -1,
            'заголовок шторки «Обозначения» (Task 386)');
        assertTrue(chunk.indexOf('id="wsLgChv"') !== -1 &&
                   chunk.indexOf('toggleLegendWide()') !== -1,
            'значок-шеврон на левом крае — разворот шире (Task 386)');
        assertTrue(chunk.indexOf('aria-label="Показать подробные наименования кодов"') !== -1,
            'aria-подпись шеврона');
    });
''', 1),

    # 3. CSS: десктоп margin+width, мобайл — display:none (оверлей удалён)
    ('CSS: margin+width, мобайл display:none', '''    test('HTML: CSS шторки легенды — десктоп margin + мобайл fixed', () => {
        const iCss = INDEX_SRC.indexOf('.ws-legend-drawer {');
        assertTrue(iCss !== -1, 'CSS-блок .ws-legend-drawer есть');
        const chunk = INDEX_SRC.slice(iCss, iCss + 700);
        assertTrue(chunk.indexOf('transition: margin-right 0.28s ease') !== -1,
            'десктоп: margin-анимация (как у итогов)');
        const iMob = INDEX_SRC.indexOf('#page-work-schedule.ws-legend-open .ws-legend-drawer { transform: none; }');
        assertTrue(iMob !== -1, 'мобайл: transform-оверлей, класс ws-legend-open');
    });
''', '''    test('HTML: CSS шторки — десктоп margin+width; мобайл — страница', () => {
        const iCss = INDEX_SRC.indexOf('.ws-legend-drawer {');
        assertTrue(iCss !== -1, 'CSS-блок .ws-legend-drawer есть');
        const chunk = INDEX_SRC.slice(iCss, iCss + 700);
        assertTrue(chunk.indexOf('transition: margin-right 0.28s ease, width 0.28s ease') !== -1,
            'десктоп: margin + width-анимация (Task 386: два вида)');
        assertTrue(INDEX_SRC.indexOf('.ws-legend-drawer { display: none; }') !== -1,
            'мобайл: шторка гасится (Task 386 — отдельная страница ws-legend)');
        assertTrue(INDEX_SRC.indexOf('ws-legend-open') === -1,
            'класс ws-legend-open удалён (мобильного оверлея нет)');
        assertTrue(INDEX_SRC.indexOf('.ws-lg-page-body') !== -1,
            'CSS тела мобильной страницы «Обозначения»');
    });
''', 1),

    # 4. Страница «Работники»: кнопка «Добавить работника»
    ('страница — кнопка «Добавить работника»', '''        assertTrue(chunk.indexOf('id="wsWorkersAddBtn"') !== -1, 'кнопка «+» в шапке');
        assertTrue(chunk.indexOf('WorkSchedule.openEmployeeForm()') !== -1,
            '«+» → шторка создания (openEmployeeForm)');
        assertTrue(chunk.indexOf('id="wsWorkersBody"') !== -1, 'тело #wsWorkersBody');
        assertTrue(chunk.indexOf('aria-label="Добавить работника"') !== -1,
            'aria-подпись кнопки');
''', '''        assertTrue(chunk.indexOf('id="wsWorkersAddBtn"') !== -1, 'кнопка добавления в шапке');
        assertTrue(chunk.indexOf('WorkSchedule.openEmployeeForm()') !== -1,
            'кнопка → шторка создания (openEmployeeForm)');
        assertTrue(chunk.indexOf('>Добавить работника</button>') !== -1,
            'текст «Добавить работника» (Task 386: прежде значок «+»)');
        assertTrue(chunk.indexOf('id="wsWorkersBody"') !== -1, 'тело #wsWorkersBody');
        assertTrue(chunk.indexOf('aria-label="Добавить работника"') !== -1,
            'aria-подпись кнопки');
''', 1),

    # 5. Шапки: сетка «Работники» (1) + итоги «Работник» (3)
    ('шапки — сетка «Работники» + итоги «Работник»', '''        assertEqual((INDEX_SRC.match(/data-full="Работник" data-s4="Рабо"/g) || []).length, 4,
            '4 шапки: сетка + итоги месяц/год/архив');
''', '''        assertEqual((INDEX_SRC.match(/data-full="Работник" data-s4="Рабо"/g) || []).length, 3,
            '3 шапки итогов: месяц/год/архив');
        assertEqual((INDEX_SRC.match(/data-full="Работники" data-s4="Рабо"/g) || []).length, 1,
            'шапка СЕТКИ — «Работники» (Task 386: «Работник +» → надпись)');
''', 1),

    # 6. Шапка сетки — надпись
    ('шапка сетки — надпись «Работники»', '''    test('шапка сетки — «Работник +» ведёт на страницу', () => {
        const grid = INDEX_SRC.slice(INDEX_SRC.indexOf('_renderGrid: function'),
                                      INDEX_SRC.indexOf('_fitGrid: function'));
        assertTrue(grid.indexOf('data-full="Работник" data-s4="Рабо">Работник</span>') !== -1,
            'заголовок «Работник» (сужение — «Рабо»)');
        assertTrue(grid.indexOf('onclick="WorkSchedule.openWorkersPage()"') !== -1,
            'клик заголовка → openWorkersPage (не openEmployeeForm)');
    });
''', '''    test('шапка сетки — «Работники»: ПРОСТО надпись (Task 386)', () => {
        const grid = INDEX_SRC.slice(INDEX_SRC.indexOf('_renderGrid: function'),
                                      INDEX_SRC.indexOf('_fitGrid: function'));
        assertTrue(grid.indexOf('data-full="Работники" data-s4="Рабо">Работники</span>') !== -1,
            'заголовок «Работники» (сужение — «Рабо»)');
        assertTrue(grid.indexOf('onclick="WorkSchedule.openWorkersPage()"') === -1,
            'функции кнопки у заголовка НЕТ — переход только кнопкой в баре');
        assertTrue(grid.indexOf('ws-emp-head-add') === -1 &&
                   grid.indexOf('ws-emp-head-plus') === -1,
            'класс кнопки и плюсик-индикатор удалены');
    });
''', 1),

    # 7. _WORK_SCHEDULE_PAGES + ws-legend
    ('_WORK_SCHEDULE_PAGES + ws-legend', '''        assertTrue(INDEX_SRC.indexOf("_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers']") !== -1,
            '_WORK_SCHEDULE_PAGES + ws-workers (права наследует табель)');
''', '''        assertTrue(INDEX_SRC.indexOf(
            "_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers', 'ws-legend']") !== -1,
            '_WORK_SCHEDULE_PAGES + ws-workers + ws-legend (права наследует табель)');
''', 1),

    # 8. _setLegend SRC: явные ширины, без ws-legend-open/замера inner
    ('_setLegend SRC — новые механики', '''    test('_setLegend — aria/класс/маржа (десктоп и мобайл)', () => {
        const fn = methodText(INDEX_SRC, '_setLegend');
        assertTrue(fn.indexOf("aria-pressed") !== -1, 'aria-pressed кнопки');
        assertTrue(fn.indexOf("ws-legend-open") !== -1, 'класс ws-legend-open на странице');
        assertTrue(fn.indexOf("matchMedia('(min-width: 1024px)')") !== -1,
            'десктоп/мобайл ветвление (как toggleTotals)');
        assertTrue(fn.indexOf('marginRight') !== -1, 'margin-механика выезда (как итоги)');
        assertTrue(fn.indexOf('.ws-legend-inner') !== -1,
            'замер фикс-ширины внутренностей');
        assertTrue(fn.indexOf('void drawer.offsetWidth') !== -1,
            'синхронный reflow перед анимацией (как итоги)');
        assertTrue(fn.indexOf('this._fitGrid()') !== -1, 'сетка перегоняется под шторку');
    });
''', '''    test('_setLegend — aria/маржа/явная ширина (десктоп и мобайл)', () => {
        const fn = methodText(INDEX_SRC, '_setLegend');
        assertTrue(fn.indexOf("aria-pressed") !== -1, 'aria-pressed кнопки');
        assertTrue(fn.indexOf("matchMedia('(min-width: 1024px)')") !== -1,
            'десктоп/мобайл ветвление (как toggleTotals)');
        assertTrue(fn.indexOf('marginRight') !== -1, 'margin-механика выезда (как итоги)');
        assertTrue(fn.indexOf('_legendWidthPx()') !== -1,
            'ширина слота — ЯВНАЯ (flex-сжатие inner больше не ловится)');
        assertTrue(fn.indexOf('_applyLegendWide()') !== -1,
            'вид (узкий/широкий) применяется при открытии');
        assertTrue(fn.indexOf('ws-legend-open') === -1,
            'класс ws-legend-open удалён (Task 386: мобайл — страница)');
        assertTrue(fn.indexOf('void drawer.offsetWidth') !== -1,
            'синхронный reflow перед анимацией (как итоги)');
        assertTrue(fn.indexOf('this._fitGrid()') !== -1, 'сетка перегоняется под шторку');
    });
''', 1),

    # 9. Контент — метод _legendHtml (+ notesec)
    ('контент — _legendHtml', '''    test('_renderLegendSheet — секции и динамические коды', () => {
        const fn = methodText(INDEX_SRC, '_renderLegendSheet');
        assertTrue(fn.indexOf('Коды дней (Т-12/Т-13)') !== -1, 'секция кодов дней');
        assertTrue(fn.indexOf('Коды мероприятий') !== -1, 'секция кодов мероприятий');
        assertTrue(fn.indexOf('Обозначения в шахматке') !== -1, 'секция обозначений');
''', '''    test('_legendHtml — секции и динамические коды', () => {
        // Task 386: контент вынесен в _legendHtml (шторка и мобильная
        // страница рендерят одно и то же)
        const fn = methodText(INDEX_SRC, '_legendHtml');
        assertTrue(fn.indexOf('Коды дней (Т-12/Т-13)') !== -1, 'секция кодов дней');
        assertTrue(fn.indexOf('Коды мероприятий') !== -1, 'секция кодов мероприятий');
        assertTrue(fn.indexOf('Обозначения в шахматке') !== -1, 'секция обозначений');
        assertTrue(fn.indexOf('ws-lg-notesec') !== -1,
            'пояснения — в свёртываемом блоке .ws-lg-notesec (Task 386)');
''', 1),

    # 10. VM HOST_METHODS: новые методы
    ('VM: HOST_METHODS + новые методы', '''    const HOST_METHODS = [
        '_renderEmpPopup', '_renderWorkerCard', '_renderWorkersPage',
        '_renderWorkersIfOpen', 'openWorkersPage', 'onWorkersPageOpen',
        '_setLegend', 'toggleLegend', '_renderLegendSheet',
''', '''    const HOST_METHODS = [
        '_renderEmpPopup', '_renderWorkerCard', '_renderWorkersPage',
        '_renderWorkersIfOpen', 'openWorkersPage', 'onWorkersPageOpen',
        '_setLegend', 'toggleLegend', '_renderLegendSheet',
        // Task 386: два вида шторки + мобильная страница
        '_legendHtml', 'onLegendPageOpen', '_legendWidthPx',
        'toggleLegendWide', '_applyLegendWide',
''', 1),

    # 11. VM toggleLegend: десктоп-хост (мобайл теперь уходит на страницу)
    ('VM: toggleLegend — десктоп-хост', '''    test('VM: toggleLegend — взаимоисключение с итогами', () => {
        const h = makeHost();
        h.WSM._totalsOpen = true;
''', '''    test('VM: toggleLegend — взаимоисключение с итогами', () => {
        // Task 386: десктоп-хост — на «мобайле» toggleLegend уходит
        // на страницу ws-legend (не тогглит шторку)
        const h = makeHost(true);
        h.WSM._totalsOpen = true;
''', 1),

    # 12. VM _setLegend десктоп: ширины/шеврон, без класса страницы
    ('VM: _setLegend — новые ассерты', '''    test('VM: _setLegend — класс/aria/маржа (десктоп)', () => {
        const h = makeHost(true);   // десктоп
        // предсоздаём моки (getElementById в методе создаст их же,
        // но нам нужны расширенные поведение/свойства)
        const drawn = { calls: [] };
        const page = { style: {}, classList: { _c: {}, add(c) { this._c[c] = 1; },
                                               remove(c) { delete this._c[c]; },
                                               contains(c) { return !!this._c[c]; } } };
        const btn = mkEl();
        btn.setAttribute = (k, v) => { drawn.calls.push([k, v]); };
        const drawer = mkEl();
        drawer.querySelector = () => ({ getBoundingClientRect: () => ({ width: 400 }) });
        h.els()['page-work-schedule'] = page;
        h.els().wsLegendBtn = btn;
        h.els().wsLegendDrawer = drawer;
        h.WSM._setLegend(true);
        assertEqual(h.WSM._legendOpen, true, 'флаг');
        assertTrue(page.classList.contains('ws-legend-open'), 'класс ws-legend-open');
        assertEqual(drawn.calls[0][0], 'aria-pressed', 'aria-pressed ставится');
        assertEqual(drawn.calls[0][1], 'true', 'aria-pressed=true');
        assertEqual(drawer.style.marginRight, '0px', 'маржа 0 (панель выехала)');
        h.WSM._setLegend(false);
        assertFalse(page.classList.contains('ws-legend-open'), 'класс снят');
        assertEqual(drawer.style.marginRight, '-400px', 'уехала за край (−ширина inner)');
    });
''', '''    test('VM: _setLegend — aria/маржа/ширина/шеврон (десктоп)', () => {
        const h = makeHost(true);   // десктоп
        const drawn = { calls: [] };
        const btn = mkEl();
        btn.setAttribute = (k, v) => { drawn.calls.push([k, v]); };
        const drawer = mkEl();
        const chv = mkEl();
        h.els().wsLegendBtn = btn;
        h.els().wsLegendDrawer = drawer;
        h.els().wsLgChv = chv;
        h.WSM._setLegend(true);
        assertEqual(h.WSM._legendOpen, true, 'флаг');
        assertEqual(drawn.calls[0][0], 'aria-pressed', 'aria-pressed ставится');
        assertEqual(drawn.calls[0][1], 'true', 'aria-pressed=true');
        assertEqual(chv.hidden, false, 'шеврон показан вместе со шторкой');
        assertEqual(drawer.style.width, '190px', 'слот — узкий вид (190px)');
        assertEqual(drawer.style.marginRight, '0px', 'маржа 0 (панель выехала)');
        h.WSM._setLegend(false);
        assertEqual(drawer.style.marginRight, '-190px', 'уехала за край (−ширина вида)');
        assertEqual(chv.hidden, true, 'шеврон скрыт при закрытии');
    });
''', 1),
])

# ============================================================
# test-task311.js — заголовок-надпись
# ============================================================
patch('tests/test-task311.js', [
    ('JS: заголовок — надпись', '''    test('JS: _renderGrid — заголовок «Работник» становится кнопкой (редакторам)', () => {
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
            'openWorkersPage проверяет право записи (зритель — мимо)');
    });
''', '''    test('JS: _renderGrid — заголовок «Работники» — ПРОСТО надпись (Task 386)', () => {
        const gridPart = INDEX_SRC.slice(
            INDEX_SRC.indexOf('_renderGrid: function'),
            INDEX_SRC.indexOf('_fitGrid: function'));
        assertTrue(gridPart.indexOf('data-full="Работники" data-s4="Рабо">Работники</span>') !== -1,
            'текст «Работники» (Task 386: «Работник +» → надпись)');
        assertTrue(gridPart.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") === -1,
            'класс кнопки НЕ вешается (функция кнопки снята по заявке)');
        assertTrue(gridPart.indexOf('onclick="WorkSchedule.openWorkersPage()"') === -1,
            'клика у заголовка нет — переход только кнопкой «Работники» в баре');
        assertTrue(gridPart.indexOf('<i class="ws-emp-head-plus">+</i>') === -1,
            'плюсик-индикатор удалён');
        // двойная защита: openWorkersPage сам проверяет право записи
        const owp = fnBody(INDEX_SRC, 'openWorkersPage: function');
        assertTrue(owp.indexOf('if (!this._canEdit) return;') !== -1,
            'openWorkersPage проверяет право записи (зритель — мимо)');
    });
''', 1),

    ('CSS: правила кнопки удалены', '''    test('CSS: ws-emp-head-add — курсор-палец, подсветка, плюсик', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-grid thead th.ws-emp-col.ws-emp-head-add { cursor: pointer; }') !== -1,
            'курсор-палец на заголовке-кнопке');
        assertTrue(INDEX_SRC.indexOf('.ws-grid thead th.ws-emp-col.ws-emp-head-add:hover {') !== -1,
            'подсветка при наведении');
        assertTrue(INDEX_SRC.indexOf('.ws-grid thead th.ws-emp-col .ws-emp-head-plus {') !== -1,
            'стиль плюсика-индикатора');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ws-grid thead th.ws-emp-col.ws-emp-head-add:hover {') !== -1,
            'светлая тема подсветки');
    });
''', '''    test('CSS: ws-emp-head-add — правила УДАЛЕНЫ (Task 386: надпись)', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-grid thead th.ws-emp-col.ws-emp-head-add') === -1,
            'курсор/hover-правила кнопки заголовка удалены');
        assertTrue(INDEX_SRC.indexOf('.ws-grid thead th.ws-emp-col .ws-emp-head-plus {') === -1,
            'стиль плюсика-индикатора удалён');
    });
''', 1),
])

# ============================================================
# test-task318.js — hover-правила заголовка удалены
# ============================================================
patch('tests/test-task318.js', [
    ('CSS: hover удалён (тёмная)', '''    test('CSS: hover — СПЛОШНОЙ #2a3a4c (Task 330: светлее сине-серой шапки)', () => {
        const m = INDEX_SRC.match(/th\\.ws-emp-col\\.ws-emp-head-add:hover \\{\\s*([^}]*)\\}/);
        assertTrue(!!m, 'правило hover живо');
        // Task 330: шапка стала сине-серой #1e293b — hover #2a3a4c
        // (прежде #15202f был светлее старого фона #0e1621 — логика
        // «hover светлее фона» сохранена на новом цвете)
        assertTrue(m[1].indexOf('background: #2a3a4c') !== -1,
            'фон — сплошной #2a3a4c (светлее шапки #1e293b, Task 330)');
        assertFalse(/rgba\\(/.test(m[1]),
            'полупрозрачного rgba в hover больше нет — фон НЕ прозрачный');
    });
''', '''    test('CSS: hover-правило заголовка УДАЛЕНО (Task 386: надпись)', () => {
        // Task 386: заголовок «Работники» — просто надпись; hover
        // #2a3a4c (Task 330) жил в правиле ws-emp-head-add:hover —
        // удалено вместе с кнопкой
        const m = INDEX_SRC.match(/th\\.ws-emp-col\\.ws-emp-head-add:hover \\{\\s*([^}]*)\\}/);
        assertTrue(!m, 'правило hover удалено (заголовок больше не кнопка)');
    });
''', 1),

    ('CSS: hover удалён (светлая)', '''    test('CSS: светлая тема hover — СПЛОШНОЙ #e2e8ef', () => {
        const m = INDEX_SRC.match(/\\[data-theme="light"\\] th\\.ws-emp-col\\.ws-emp-head-add:hover \\{\\s*([^}]*)\\}/) ||
                  INDEX_SRC.match(/\\[data-theme="light"\\] \\.ws-grid thead th\\.ws-emp-col\\.ws-emp-head-add:hover \\{\\s*([^}]*)\\}/);
        assertTrue(!!m, 'правило светлой темы живо');
        assertTrue(m[1].indexOf('background: #e2e8ef') !== -1,
            'светлая — сплошной #e2e8ef (как td.ws-emp-col:hover)');
        assertFalse(/rgba\\(/.test(m[1]), 'светлая: rgba убран');
    });
''', '''    test('CSS: светлая тема hover — правило УДАЛЕНО (Task 386)', () => {
        const m = INDEX_SRC.match(/\\[data-theme="light"\\][^{}]*ws-emp-head-add:hover\\s*\\{[^}]*\\}/);
        assertTrue(!m, 'правило светлой темы удалено вместе с кнопкой');
    });
''', 1),
])

# ============================================================
# test-task330.js — hover-правило удалено
# ============================================================
patch('tests/test-task330.js', [
    ('CSS: hover #2a3a4c → правило удалено', '''    test('тёмная тема: hover «Сотрудник +» — #2a3a4c (светлее шапки)', () => {
        const block = ruleBlock('.ws-grid thead th.ws-emp-col.ws-emp-head-add:hover {');
        assertTrue(block.length > 0, 'правило hover найдено');
        assertTrue(/background:\\s*#2a3a4c/.test(block),
            'hover — #2a3a4c, светлее новой шапки #1e293b');
        assertFalse(/background:\\s*#15202f/.test(block),
            'прежний hover #15202f (темнее новой шапки) заменён');
    });
''', '''    test('тёмная тема: hover-правило заголовка удалено (Task 386)', () => {
        // Task 386: заголовок — надпись; hover #2a3a4c из Task 330
        // удалён вместе с кнопкой
        const block = ruleBlock('.ws-grid thead th.ws-emp-col.ws-emp-head-add:hover {');
        assertEqual(block.length, 0, 'правило hover удалено (заголовок-надпись)');
    });
''', 1),
])

# ============================================================
# test-task335.js — плюсик narrow удалён; шапка «Работники»
# ============================================================
patch('tests/test-task335.js', [
    ('CSS: narrow плюсик удалён', '''    test('CSS: плюсик шапки скрыт в суженном виде', () => {
        const b = ruleBlock('.ws-grid.ws-narrow thead th.ws-emp-col .ws-emp-head-plus {');
        assertTrue(b.length > 0, 'правило найдено');
        assertTrue(/display:\\s*none/.test(b), 'display: none');
    });
''', '''    test('CSS: правило плюсика в суженном виде удалено (Task 386)', () => {
        // Task 386: заголовок — надпись, плюсика нет — правило
        // (.ws-narrow .ws-emp-head-plus) удалено
        const b = ruleBlock('.ws-grid.ws-narrow thead th.ws-emp-col .ws-emp-head-plus {');
        assertEqual(b.length, 0, 'правило удалено (плюсика больше нет)');
    });
''', 1),

    ('РЕНДЕР: шапка «Работники»', '''    test('РЕНДЕР: шапка сетки — span «Работник» ⇄ «Рабо»', () => {
        const i = INDEX_SRC.indexOf('class="ws-emp-head-txt"');
        assertTrue(i !== -1, 'span.ws-emp-head-txt в разметке шапки сетки');
        const chunk = INDEX_SRC.slice(i - 80, i + 160);
        assertTrue(chunk.indexOf('data-full="Работник"') !== -1, 'data-full (Task 385: работник)');
        assertTrue(chunk.indexOf('data-s4="Рабо"') !== -1, 'data-s4 «Рабо»');
    });
''', '''    test('РЕНДЕР: шапка сетки — span «Работники» ⇄ «Рабо»', () => {
        const i = INDEX_SRC.indexOf('class="ws-emp-head-txt"');
        assertTrue(i !== -1, 'span.ws-emp-head-txt в разметке шапки сетки');
        const chunk = INDEX_SRC.slice(i - 80, i + 160);
        assertTrue(chunk.indexOf('data-full="Работники"') !== -1,
            'data-full «Работники» (Task 386: надпись, не кнопка)');
        assertTrue(chunk.indexOf('data-s4="Рабо"') !== -1, 'data-s4 «Рабо»');
    });
''', 1),
])

# ============================================================
# test-task337.js / test-task338.js — гейт заголовка снят
# ============================================================
patch('tests/test-task337.js', [
    ('SRC: заголовок — надпись', '''    test('SRC: «+» заголовка сотрудников — только редакторам', () => {
        assertTrue(INDEX_SRC.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") !== -1,
            'класс/клик заголовка — по праву записи');
    });
''', '''    test('SRC: заголовок шапки — надпись (гейт снят, Task 386)', () => {
        assertTrue(INDEX_SRC.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") === -1,
            'кнопки-заголовка нет; право решает кнопка «Работники» в баре');
    });
''', 1),
])

patch('tests/test-task338.js', [
    ('SRC: заголовок — надпись (регресс)', '''    test('SRC: «+» заголовка «Сотрудник» — прежний гейт (регресс)', () => {
        assertTrue(INDEX_SRC.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") !== -1,
            'заголовок «Сотрудник +» — только редакторам (Task 311/319)');
    });
''', '''    test('SRC: заголовок «Работники» — надпись (Task 386: гейт снят)', () => {
        assertTrue(INDEX_SRC.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") === -1,
            'заголовок-кнопки нет — правит кнопка «Работники» в баре (Task 386)');
    });
''', 1),
])

# ============================================================
# test-work-schedule.js — литерал карт + заголовок-надпись
# ============================================================
patch('tests/test-work-schedule.js', [
    ('литерал карт (SUBSECTIONS)', '''        assertTrue(html.indexOf("_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers']") !== -1,
                'work-schedule в _WORK_SCHEDULE_PAGES (доступ Админу через *; Task 334: + итоги; Task 385: + «Работники»)');
''', '''        assertTrue(html.indexOf(
            "_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers', 'ws-legend']") !== -1,
                'work-schedule в _WORK_SCHEDULE_PAGES (доступ Админу через *; Task 334: + итоги; Task 385: + «Работники»; Task 386: + «Обозначения»)');
''', 1),

    ('заголовок — надпись (3078)', '''    test('HTML: Task 311 — кнопка «+ Сотрудник» УДАЛЕНА; заголовок «Работник» — триггер', () => {
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
            'клик заголовка → openWorkersPage (Task 385: страница «Работники»)');
        assertTrue(grid.indexOf('ws-emp-head-plus') !== -1,
            'плюсик-индикатор у заголовка (редакторам)');
        assertTrue(grid.indexOf("this._canEdit ? ' ws-emp-head-add' : ''") !== -1,
            'класс/клик вешаются по праву записи (_canEdit)');
    });
''', '''    test('HTML: Task 311 — кнопка «+ Сотрудник» УДАЛЕНА; заголовок — надпись', () => {
        // Task 311: кнопка из тулбара удалена; Task 385: заголовок
        // вёл на СТРАНИЦУ «Работники»; Task 386 (заявка): заголовок
        // «Работники» — ПРОСТО надпись, без функции кнопки — переход
        // выполняет только кнопка «Работники» в баре (ряд 1)
        assertTrue(html.indexOf('id="wsEmpBtn"') === -1,
            'кнопка #wsEmpBtn удалена из тулбара');
        // рендер шапки: заголовок — надпись (Task 386)
        const grid = html.slice(html.indexOf('_renderGrid: function'),
                                html.indexOf('_fitGrid: function'));
        assertTrue(grid.indexOf('data-full="Работники" data-s4="Рабо">Работники</span>') !== -1,
            'заголовок «Работники» (Task 386)');
        assertTrue(grid.indexOf('ws-emp-head-add') === -1,
            'класс кнопки у заголовка снят (Task 386)');
        assertTrue(grid.indexOf('onclick="WorkSchedule.openWorkersPage()"') === -1,
            'клика у заголовка нет — переход только кнопкой в баре');
        assertTrue(grid.indexOf('ws-emp-head-plus') === -1,
            'плюсик-индикатор удалён (Task 386)');
    });
''', 1),

    ('литерал карт (3148)', '''        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals', 'ws-workers'",
            'в карте ролей модуля — шахматка, итоги (Task 334) и «Работники» (Task 385)');
    });

    test('HTML: bottom-sheet формы работника жив (без изменений)', () => {
''', '''        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals', 'ws-workers', 'ws-legend'",
            'в карте ролей модуля — шахматка, итоги (Task 334), «Работники» (Task 385), «Обозначения» (Task 386)');
    });

    test('HTML: bottom-sheet формы работника жив (без изменений)', () => {
''', 1),

    ('литерал карт (3381)', '''        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals', 'ws-workers'",
            'в карте ролей модуля — шахматка, итоги (Task 334) и «Работники» (Task 385)');
    });

    test('HTML: bottom-sheet «Новый отпуск» жив (без изменений)', () => {
''', '''        assertEqual(m[1].trim(), "'work-schedule', 'ws-totals', 'ws-workers', 'ws-legend'",
            'в карте ролей модуля — шахматка, итоги (Task 334), «Работники» (Task 385), «Обозначения» (Task 386)');
    });

    test('HTML: bottom-sheet «Новый отпуск» жив (без изменений)', () => {
''', 1),
])

# ============================================================
# test-task334.js — литерал карт
# ============================================================
patch('tests/test-task334.js', [
    ('литерал карт (334)', '''        assertTrue(INDEX_SRC.indexOf(
            "_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers']") !== -1,
            '_WORK_SCHEDULE_PAGES: страницы модуля (+ «Работники» — Task 385)');
''', '''        assertTrue(INDEX_SRC.indexOf(
            "_WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers', 'ws-legend']") !== -1,
            '_WORK_SCHEDULE_PAGES: страницы модуля (+ «Работники» — Task 385; + «Обозначения» — Task 386)');
''', 1),
])

# ============================================================
# run-all.js — подключение test-task386.js
# ============================================================
patch('tests/run-all.js', [
    ('run-all + task386', '''require('./test-task385.js');
require('./test-deploy-url.js');
''', '''require('./test-task385.js');
// Task 386: «Обозначения» (кнопка/два вида шторки/мобильная
// страница), шапка «Работники» (надпись), «Добавить работника»
require('./test-task386.js');
require('./test-deploy-url.js');
''', 1),
])

print('Task 386: тесты адаптированы (9 файлов + run-all)')
