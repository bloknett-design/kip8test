#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 378 — адаптация тестов под новые значения/структуру:
#   - VM-хосты _renderMonthEventsPanel: заглушка _barExpSync (метод
#     теперь вызывается в конце рендера окна мероприятий);
#   - test-task316: sel-col ШАПКИ насыщеннее hover-col (0.44/0.30);
#   - test-task319: значения перекрестья (= «сегодня»: 0.30/0.22,
#     пересечение 0.34/0.26, строка+сегодня 0.34/0.26) + селекторы
#     делегирования 'td.ws-cell, td.ws-emp-col';
#   - test-task321/322: зебра строк итогов УДАЛЕНА (Task 378),
#     регекс ws-tt-over якорится к базовому правилу (не тёмному
#     переопределению Task 378);
#   - test-task333: строка шторки 0.30/0.22;
#   - test-task377: составные правила (строка+сегодня 0.34/0.26,
#     сегодня+наведение 0.34/0.26, строка+сегодня+наведение 0.36/0.28),
#     «регресс базовых» переписан под Task 378.
import io, sys

def patch(path, pairs):
    src = io.open(path, encoding='utf-8').read()
    for old, new, label in pairs:
        n = src.count(old)
        if n == 0:
            print('FAIL %s: не найдено: %s' % (path, label)); sys.exit(1)
        src = src.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('OK %s: %d правок' % (path, len(pairs)))

# ---------- test-task315.js: заглушки _barExpSync ----------

patch('tests/test-task315.js', [
    ("""            '_esc: function(s){ return String(s == null ? "" : s); },' +
            '_escAttr: function(s){ return String(s == null ? "" : s); },',
            { document: document }""",
     """            '_esc: function(s){ return String(s == null ? "" : s); },' +
            '_escAttr: function(s){ return String(s == null ? "" : s); },' +
            '_barExpSync: function() {},',
            { document: document }""",
     'makePanel: заглушка _barExpSync'),
    ("""            '_esc: function(s){ return String(s == null ? "" : s); },' +
            '_escAttr: function(s){ return String(s == null ? "" : s); },' +
            '});');""",
     """            '_esc: function(s){ return String(s == null ? "" : s); },' +
            '_escAttr: function(s){ return String(s == null ? "" : s); },' +
            '_barExpSync: function() {},' +
            '});');""",
     'ручной хост: заглушка _barExpSync'),
])

# ---------- test-task316.js: заглушки + sel-col насыщеннее ----------

patch('tests/test-task316.js', [
    ("""            '_esc: function(s){ return String(s == null ? "" : s); },' +
            '_escAttr: function(s){ return String(s == null ? "" : s); },' +""",
     """            '_esc: function(s){ return String(s == null ? "" : s); },' +
            '_escAttr: function(s){ return String(s == null ? "" : s); },' +
            '_barExpSync: function() {},' +""",
     'makeCtx/makePanel: заглушка _barExpSync (2 места)'),
    ("""        const hov = INDEX_SRC.match(/\\.ws-grid thead th\\.ws-day-col\\.ws-hover-col\\s*\\{([^}]*)\\}/)[1];
        const sel = INDEX_SRC.match(/\\.ws-grid thead th\\.ws-day-col\\.ws-sel-col\\s*\\{([^}]*)\\}/)[1];""",
     """        const hov = INDEX_SRC.match(/\\.ws-grid thead th\\.ws-day-col\\.ws-hover-col\\s*\\{([^}]*)\\}/)[1];
        const sel = INDEX_SRC.match(/\\.ws-grid thead th\\.ws-day-col\\.ws-sel-col\\s*\\{([^}]*)\\}/)[1];""",
     'no-op (совпадения считаются)'),
])

# ---------- test-task319.js: делегирование + значения ----------

patch('tests/test-task319.js', [
    ("""        assertTrue(init.indexOf("e.target.closest('td.ws-cell')") !== -1,
            'ячейка дня находится closest(td.ws-cell)');""",
     """        assertTrue(init.indexOf("e.target.closest('td.ws-cell, td.ws-emp-col')") !== -1,
            'ячейка дня ИЛИ ФИО находится closest (Task 378: ФИО тоже подсвечивает строку)');""",
     'init: closest ячейка+ФИО'),
    ("""        assertTrue(init.indexOf("to.closest('td.ws-cell')") !== -1,
            'mouseout: переход на другую ячейку — подсветку НЕ трогаем');""",
     """        assertTrue(init.indexOf("to.closest('td.ws-cell, td.ws-emp-col')") !== -1,
            'mouseout: переход на другую ячейку/ФИО — подсветку НЕ трогаем');""",
     'init: mouseout closest ячейка+ФИО'),
    ("""        assertTrue(cssRule(/\\.ws-grid tbody tr\\.ws-hover-row td\\.ws-cell \\{[^}]*rgba\\(74, 143, 199, 0\\.10\\)[^}]*\\}/s),
            'строка — inset 0.10 (мягче столбца 0.16)');""",
     """        assertTrue(cssRule(/\\.ws-grid tbody tr\\.ws-hover-row td\\.ws-cell \\{[^}]*rgba\\(74, 143, 199, 0\\.30\\)[^}]*\\}/s),
            'строка — inset 0.30 (Task 378: яркость «сегодня»)');""",
     'тёмная строка 0.30'),
    ("""        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-hover \\{[^}]*rgba\\(74, 143, 199, 0\\.24\\)[^}]*\\}/s),
            'ПЕРЕСЕЧЕНИЕ строки и столбца — 0.24 (насыщеннее)');""",
     """        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-hover \\{[^}]*rgba\\(74, 143, 199, 0\\.34\\)[^}]*\\}/s),
            'ПЕРЕСЕЧЕНИЕ строки и столбца — 0.34 (насыщеннее, Task 378)');""",
     'тёмное пересечение 0.34'),
    ("""        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-sel \\{[^}]*rgba\\(74, 143, 199, 0\\.24\\)[^}]*\\}/s),
            'выбранный кликом день в строке — выбор не затирается');""",
     """        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-sel \\{[^}]*rgba\\(74, 143, 199, 0\\.34\\)[^}]*\\}/s),
            'выбранный кликом день в строке — выбор не затирается');""",
     'тёмная строка+выбор 0.34'),
    ("""        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-today \\{[^}]*rgba\\(74, 143, 199, 0\\.32\\)[^}]*\\}/s),
            '«сегодня» в наведённой строке (Task 377: усилено 0.20 → 0.32)');""",
     """        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-today \\{[^}]*rgba\\(74, 143, 199, 0\\.34\\)[^}]*\\}/s),
            '«сегодня» в наведённой строке (Task 377 → 378: 0.32 → 0.34)');""",
     'тёмная строка+сегодня 0.34'),
    ("""        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-source-manual \\{[^}]*0\\.10\\),[^}]*1\\.5px rgba\\(255,255,255,0\\.5\\)[^}]*\\}/s),
            'рамка ручной записи не затирается заливкой строки');""",
     """        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-cell\\.ws-source-manual \\{[^}]*0\\.30\\),[^}]*1\\.5px rgba\\(255,255,255,0\\.5\\)[^}]*\\}/s),
            'рамка ручной записи не затирается заливкой строки');""",
     'тёмная строка+manual 0.30'),
    ("""        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-emp-col \\{[^}]*rgba\\(74, 143, 199, 0\\.10\\)[^}]*\\}/s),
            'ФИО-ячейка строки — «начало» перекрестья');""",
     """        assertTrue(cssRule(/tr\\.ws-hover-row td\\.ws-emp-col \\{[^}]*rgba\\(74, 143, 199, 0\\.30\\)[^}]*\\}/s),
            'ФИО-ячейка строки — «начало» перекрестья');""",
     'тёмная ФИО 0.30'),
    ("""        assertTrue(cssRule(/\\[data-theme="light"\\] \\.ws-grid tbody tr\\.ws-hover-row td\\.ws-cell \\{[^}]*rgba\\(42, 93, 143, 0\\.06\\)[^}]*\\}/s),
            'строка — 0.06');""",
     """        assertTrue(cssRule(/\\[data-theme="light"\\] \\.ws-grid tbody tr\\.ws-hover-row td\\.ws-cell \\{[^}]*rgba\\(42, 93, 143, 0\\.22\\)[^}]*\\}/s),
            'строка — 0.22 (Task 378: яркость «сегодня»)');""",
     'светлая строка 0.22'),
    ("""        assertTrue(cssRule(/\\[data-theme="light"\\][^{]*tr\\.ws-hover-row td\\.ws-cell\\.ws-hover \\{[^}]*rgba\\(42, 93, 143, 0\\.16\\)[^}]*\\}/s),
            'пересечение — 0.16 (насыщеннее столбца 0.10)');""",
     """        assertTrue(cssRule(/\\[data-theme="light"\\][^{]*tr\\.ws-hover-row td\\.ws-cell\\.ws-hover \\{[^}]*rgba\\(42, 93, 143, 0\\.26\\)[^}]*\\}/s),
            'пересечение — 0.26 (насыщеннее, Task 378)');""",
     'светлое пересечение 0.26'),
    ("""        assertTrue(cssRule(/\\[data-theme="light"\\][^{]*tr\\.ws-hover-row td\\.ws-cell\\.ws-sel \\{[^}]*rgba\\(42, 93, 143, 0\\.15\\)[^}]*\\}/s),
            'выбранный день сильнее строки');""",
     """        assertTrue(cssRule(/\\[data-theme="light"\\][^{]*tr\\.ws-hover-row td\\.ws-cell\\.ws-sel \\{[^}]*rgba\\(42, 93, 143, 0\\.26\\)[^}]*\\}/s),
            'выбранный день в строке — не затирается');""",
     'светлая строка+выбор 0.26'),
    ("""        assertTrue(cssRule(/\\[data-theme="light"\\][^{]*tr\\.ws-hover-row td\\.ws-emp-col \\{[^}]*rgba\\(42, 93, 143, 0\\.06\\)[^}]*\\}/s),
            'ФИО-ячейка (светлая)');""",
     """        assertTrue(cssRule(/\\[data-theme="light"\\][^{]*tr\\.ws-hover-row td\\.ws-emp-col \\{[^}]*rgba\\(42, 93, 143, 0\\.22\\)[^}]*\\}/s),
            'ФИО-ячейка (светлая)');""",
     'светлая ФИО 0.22'),
])

# ---------- test-task321.js: зебра удалена ----------

patch('tests/test-task321.js', [
    ("""        // Task 322: зебра строк
        assertTrue(/\\.ws-tt-table tbody tr:nth-child\\(even\\)\\s*\\{[^}]*background/.test(INDEX_SRC),
            'зебра: чётные строки с подложкой');
        assertTrue(/\\[data-theme="light"\\] \\.ws-tt-table tbody tr:nth-child\\(even\\)\\s*\\{[^}]*rgba\\(0,\\s*0,\\s*0/.test(INDEX_SRC),
            'зебра в светлой теме');""",
     """        // Task 378 (заявка: «фон пустых ячеек #FFFFFF … как в шахматке»):
        // зебра строк итогов УДАЛЕНА — ячейки значений непрозрачные
        assertFalse(/\\.ws-tt-table tbody tr:nth-child\\(even\\)\\s*\\{[^}]*background/.test(INDEX_SRC),
            'зебра строк итогов удалена (Task 378: непрозрачные ячейки)');
        assertTrue(/\\[data-theme="light"\\] \\.ws-tt-table tbody td\\.ws-tt-num\\s*\\{[^}]*#FFFFFF/.test(INDEX_SRC),
            'ячейки значений — #FFFFFF (Task 378)');""",
     'зебра → удалена, ячейки #FFFFFF'),
])

# ---------- test-task322.js: зебра удалена + якорь ws-tt-over ----------

patch('tests/test-task322.js', [
    ("""    test('CSS: ЗЕБРА строк таблицы итогов (тёмная и светлая)', () => {
        const m = INDEX_SRC.match(/\\.ws-tt-table tbody tr:nth-child\\(even\\)\\s*\\{[^}]*\\}/);
        assertTrue(!!m, 'правило зебры есть');
        assertTrue(m[0].indexOf('background') !== -1, 'подложка чётных строк');
        assertTrue(/rgba\\(255,\\s*255,\\s*255,\\s*0\\.0\\d+\\)/.test(m[0]),
            'деликатный светлый тинт в тёмной теме');
        const l = INDEX_SRC.match(/\\[data-theme="light"\\] \\.ws-tt-table tbody tr:nth-child\\(even\\)\\s*\\{[^}]*\\}/);
        assertTrue(!!l, 'зебра в светлой теме');
        assertTrue(/rgba\\(0,\\s*0,\\s*0,\\s*0\\.0\\d+\\)/.test(l[0]),
            'тёмный тинт в светлой теме');
    });""",
     """    test('CSS: Task 378 — зебра УДАЛЕНА, ячейки непрозрачные (#FFFFFF)', () => {
        // Заявка: «фон пустых ячеек #FFFFFF … полосы — как в шахматке»:
        // зебра строк не просвечивает сквозь непрозрачные ячейки —
        // правила удалены
        assertFalse(/\\.ws-tt-table tbody tr:nth-child\\(even\\)\\s*\\{[^}]*background/.test(INDEX_SRC),
            'правила зебры строк итогов нет (Task 378)');
        assertFalse(/\\[data-theme="light"\\] \\.ws-tt-table tbody tr:nth-child\\(even\\)\\s*\\{[^}]*background/.test(INDEX_SRC),
            'светлой зебры нет');
        assertTrue(/\\[data-theme="light"\\] \\.ws-tt-table tbody td\\.ws-tt-num\\s*\\{[^}]*background:\\s*#FFFFFF/.test(INDEX_SRC),
            'ячейки значений светлой темы — #FFFFFF');
        assertTrue(/\\[data-theme="dark"\\] \\.ws-tt-table tbody td\\.ws-tt-num\\s*\\{[^}]*#eef0f2/.test(INDEX_SRC),
            'тёмная тема — светлые цвета шахматки (#eef0f2 + brightness)');
    });""",
     'зебра → Task 378 непрозрачные ячейки'),
    ("""        const m = INDEX_SRC.match(/\\.ws-tt-table td\\.ws-tt-over\\s*\\{[^}]*\\}/);""",
     """        const m = INDEX_SRC.match(/\\n    \\.ws-tt-table td\\.ws-tt-over\\s*\\{[^}]*\\}/);""",
     'ws-tt-over: якорь к базовому правилу (мимо тёмного Task 378)'),
])

# ---------- test-task333.js: строка шторки = «сегодня» ----------

patch('tests/test-task333.js', [
    ("""        assertTrue(/box-shadow:\\s*inset 0 0 0 999px rgba\\(74, 143, 199, 0\\.10\\)/.test(block),
            'тёмная — тот же тинт, что у строки сетки (0.10)');""",
     """        assertTrue(/box-shadow:\\s*inset 0 0 0 999px rgba\\(74, 143, 199, 0\\.30\\)/.test(block),
            'тёмная — тот же тинт, что у строки сетки (Task 378: 0.30 = «сегодня»)');""",
     'строка шторки тёмная 0.30'),
    ("""        assertTrue(/rgba\\(42, 93, 143, 0\\.06\\)/.test(light),
            'светлая — тот же тинт, что у строки сетки (0.06)');""",
     """        assertTrue(/rgba\\(42, 93, 143, 0\\.22\\)/.test(light),
            'светлая — тот же тинт, что у строки сетки (Task 378: 0.22 = «сегодня»)');""",
     'строка шторки светлая 0.22'),
])

# ---------- test-task377.js: составные + «регресс базовых» ----------

patch('tests/test-task377.js', [
    ("""    test('строка наведения + «сегодня»: 0.32 (было 0.20)', () => {
        const b = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {');
        assertTrue(b !== null && /rgba\\(74, 143, 199, 0\\.32\\)/.test(b),
            'row+today: 0.32');
        const bm = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {');
        assertTrue(bm !== null && /rgba\\(74, 143, 199, 0\\.32\\),/.test(bm),
            'row+today+manual: 0.32 + рамка');
    });""",
     """    test('строка наведения + «сегодня»: 0.34 (Task 378: строка 0.30)', () => {
        const b = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {');
        assertTrue(b !== null && /rgba\\(74, 143, 199, 0\\.34\\)/.test(b),
            'row+today: 0.34');
        const bm = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {');
        assertTrue(bm !== null && /rgba\\(74, 143, 199, 0\\.34\\),/.test(bm),
            'row+today+manual: 0.34 + рамка');
    });""",
     'row+today 0.34'),
    ("""        const b1 = ruleBlock('.ws-grid tbody td.ws-cell.ws-today.ws-hover {');
        assertTrue(b1 !== null && /rgba\\(74, 143, 199, 0\\.30\\)/.test(b1),
            'today+hover: 0.30 (уровень «сегодня», не 0.16)');""",
     """        const b1 = ruleBlock('.ws-grid tbody td.ws-cell.ws-today.ws-hover {');
        assertTrue(b1 !== null && /rgba\\(74, 143, 199, 0\\.34\\)/.test(b1),
            'today+hover: 0.34 (Task 378: пересечение насыщеннее «сегодня» 0.30)');""",
     'today+hover 0.34'),
    ("""        const b3 = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {');
        assertTrue(b3 !== null && /rgba\\(74, 143, 199, 0\\.34\\)/.test(b3),
            'row+today+hover: 0.34');""",
     """        const b3 = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {');
        assertTrue(b3 !== null && /rgba\\(74, 143, 199, 0\\.36\\)/.test(b3),
            'row+today+hover: 0.36');""",
     'row+today+hover 0.36'),
    ("""    test('регресс: базовые hover/sel тёмной темы не изменились', () => {
        const h = ruleBlock('.ws-grid tbody td.ws-cell.ws-hover {');
        assertTrue(h !== null && /rgba\\(74, 143, 199, 0\\.16\\)/.test(h),
            'ws-hover: 0.16 (как было)');
        const s = ruleBlock('.ws-grid tbody td.ws-cell.ws-sel {');
        assertTrue(s !== null && /rgba\\(74, 143, 199, 0\\.24\\)/.test(s),
            'ws-sel: 0.24 (как было)');
        const r = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell {');
        assertTrue(r !== null && /rgba\\(74, 143, 199, 0\\.10\\)/.test(r),
            'row: 0.10 (как было)');
    });""",
     """    test('Task 378: базовые hover/sel/строка = яркость «сегодня»', () => {
        const h = ruleBlock('.ws-grid tbody td.ws-cell.ws-hover {');
        assertTrue(h !== null && /rgba\\(74, 143, 199, 0\\.30\\)/.test(h),
            'ws-hover: 0.30 (Task 378: = «сегодня», было 0.16)');
        const s = ruleBlock('.ws-grid tbody td.ws-cell.ws-sel {');
        assertTrue(s !== null && /rgba\\(74, 143, 199, 0\\.30\\)/.test(s),
            'ws-sel: 0.30 (Task 378: паритет, было 0.24)');
        const r = ruleBlock('.ws-grid tbody tr.ws-hover-row td.ws-cell {');
        assertTrue(r !== null && /rgba\\(74, 143, 199, 0\\.30\\)/.test(r),
            'row: 0.30 (Task 378: = «сегодня», было 0.10)');
    });""",
     'регресс → Task 378 значения'),
    ("""    test('строка наведения + «сегодня»: 0.24 (было 0.14)', () => {
        const b = ruleBlock('[data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {');
        assertTrue(b !== null && /rgba\\(42, 93, 143, 0\\.24\\)/.test(b),
            'row+today (светлая): 0.24');
    });""",
     """    test('строка наведения + «сегодня»: 0.26 (Task 378: строка 0.22)', () => {
        const b = ruleBlock('[data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {');
        assertTrue(b !== null && /rgba\\(42, 93, 143, 0\\.26\\)/.test(b),
            'row+today (светлая): 0.26');
    });""",
     'row+today светлая 0.26'),
    ("""        const b1 = ruleBlock('[data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover {');
        assertTrue(b1 !== null && /rgba\\(42, 93, 143, 0\\.22\\)/.test(b1), 'today+hover: 0.22');""",
     """        const b1 = ruleBlock('[data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover {');
        assertTrue(b1 !== null && /rgba\\(42, 93, 143, 0\\.26\\)/.test(b1), 'today+hover: 0.26 (Task 378)');""",
     'today+hover светлая 0.26'),
    ("""        const b3 = ruleBlock('[data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {');
        assertTrue(b3 !== null && /rgba\\(42, 93, 143, 0\\.26\\)/.test(b3), 'row+today+hover: 0.26');""",
     """        const b3 = ruleBlock('[data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {');
        assertTrue(b3 !== null && /rgba\\(42, 93, 143, 0\\.28\\)/.test(b3), 'row+today+hover: 0.28 (Task 378)');""",
     'row+today+hover светлая 0.28'),
])

print('ГОТОВО')
