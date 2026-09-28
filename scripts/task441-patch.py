#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 441: печать табеля — коды в ОДИН столбец во всех трёх
# представлениях (заявка: «Во всех трёх представлениях печати
# коды сделай в один столбец»):
#   HTML  — сетка .wsp-legend-cols: grid 1fr 1fr → 1fr (одна
#           колонка), column-gap снят (колонок нет);
#   PDF   — _printPdfLayout: codeRows = длина кодов (без / 2);
#           _printPdfPaintPage: colW2/perCol УДАЛЕНЫ, lx = codeX
#           (без сдвига), ly = y + lc * codeRowH (сквозной столбец);
#   Excel — коды и так один столбец D (строка на код) — комментарий;
#   тесты — адаптация 434/432/360/433 (ассерты «1fr 1fr» → «1fr»),
#           439 (комментарий cdH 46→74), run-all + test-task441.
import io

def patch(path, frags):
    s = io.open(path, encoding='utf-8').read()
    for old, new in frags:
        n = s.count(old)
        assert n == 1, '%s: фрагмент найден %d раз (ожидался 1):\n%r' % (path, n, old[:90])
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: %d фрагментов заменено' % (path, len(frags)))

# ----------------------------------------------------------------
# 1. index.html — CSS, генерация HTML, PDF-раскладка/отрисовка, Excel
# ----------------------------------------------------------------
patch('index.html', [
    # (1a) большой комментарий print-CSS: ДВЕ-КОЛОНКИ → ОДНА-КОЛОНКА
    ('ДВЕ-КОЛОНКИ .wsp-legend-cols (grid 1fr 1fr) до\n'
     '           конца листа, ПОД списком мероприятий; сноска',
     'ОДНА-КОЛОНКА .wsp-legend-cols (grid 1fr; Task 441) до\n'
     '           конца листа, ПОД списком мероприятий; сноска'),
    # (1b) комментарий легенды: сетка — ОДНА колонка
    ('ОТДЕЛЬНОЙ строкой СВЕРХУ, под ним сетка-ДВЕ-КОЛОНКИ\n'
     '           .wsp-legend-cols (grid 1fr 1fr) на всю ширину листа\n'
     '           ДО КОНЦА; каждая запись-код — своя строка колонки\n'
     '           (длинное наименование переносится ВНУТРИ колонки,\n'
     '           запись не рвётся между колонками/страницами) */',
     'ОТДЕЛЬНОЙ строкой СВЕРХУ, под ним сетка .wsp-legend-cols;\n'
     '           Task 441 (заявка: «коды сделай в один столбец»):\n'
     '           ОДНА колонка (grid 1fr; прежде ДВЕ равные, Task 434)\n'
     '           на всю ширину блока кодов ДО КОНЦА; каждая запись-код\n'
     '           — своя строка (длинное наименование переносится\n'
     '           ВНУТРИ колонки, запись не рвётся между страницами) */'),
    # (1c) ПРАВИЛО: одна колонка, column-gap снят
    ('#wsPrintSheet .wsp-legend-cols {\n'
     '            display: grid;\n'
     '            grid-template-columns: 1fr 1fr;\n'
     '            column-gap: 6mm;\n'
     '            row-gap: 0.8mm;\n'
     '            align-items: start;\n'
     '        }',
     '#wsPrintSheet .wsp-legend-cols {\n'
     '            display: grid;\n'
     '            /* Task 441 (заявка: «коды сделай в один столбец»):\n'
     '               ОДНА колонка — прежде ДВЕ равные (Task 434);\n'
     '               межколоночный зазор снят — колонок больше нет */\n'
     '            grid-template-columns: 1fr;\n'
     '            row-gap: 0.8mm;\n'
     '            align-items: start;\n'
     '        }'),
    # (1d) генерация HTML: комментарий + прежнее поведение
    ('ОТДЕЛЬНОЙ строкой, под ним ДВЕ КОЛОНКИ\n'
     '            // (.wsp-legend-cols, grid 1fr 1fr) на всю ширину листа:\n'
     '            // каждый код — своя строка колонки, длинное название\n'
     '            // переносится ВНУТРИ своей колонки (запись не рвётся)',
     'ОТДЕЛЬНОЙ строкой, под ним колонка кодов; Task 441 (заявка:\n'
     '            // «коды сделай в один столбец»): ОДНА колонка\n'
     '            // (.wsp-legend-cols, grid 1fr) на всю ширину блока:\n'
     '            // каждый код — своя строка, длинное название\n'
     '            // переносится ВНУТРИ колонки (запись не рвётся)'),
    # (1e) PDF-раскладка: codeRows без деления пополам
    ('var codeRows = Math.max(1,\n'
     '                Math.ceil((model.codes || []).length / 2));',
     '// Task 441 (заявка: «коды сделай в один столбец»):\n'
     '            // ОДНА колонка — строк на код не делим (прежде\n'
     '            // ДВЕ колонки: ceil(n/2) строк, Task 434/439)\n'
     '            var codeRows = Math.max(1,\n'
     '                (model.codes || []).length);'),
    # (1f) PDF-отрисовка: комментарий зоны кодов
    ('// коды — ПРАВАЯ зона, две колонки (как в печати,\n'
     '            // Task 434); общая верхняя линия с мероприятиями',
     '// коды — ПРАВАЯ зона, ОДНА колонка (Task 441: «коды\n'
     '            // сделай в один столбец»; прежде две — Task 434);\n'
     '            // общая верхняя линия с мероприятиями'),
    # (1g) PDF-отрисовка: цикл кодов — сквозной столбец
    ('y += lay.secH;\n'
     '                var colW2 = codeW / 2;\n'
     '                var perCol = Math.max(1,\n'
     '                    Math.ceil(page.codes.length / 2));\n'
     '                for (var lc = 0; lc < page.codes.length; lc++) {\n'
     '                    var lx = codeX + (lc < perCol ? 0 : colW2);\n'
     '                    var ly = y + (lc % perCol) * lay.codeRowH;',
     'y += lay.secH;\n'
     '                // Task 441: ОДИН столбец — все коды друг под\n'
     '                // другом от codeX (прежде: две колонки со\n'
     '                // сдвигом colW2 и разбивкой perCol)\n'
     '                for (var lc = 0; lc < page.codes.length; lc++) {\n'
     '                    var lx = codeX;\n'
     '                    var ly = y + lc * lay.codeRowH;'),
    # (1h) Excel: комментарий — один столбец D сохранён
    ('// заголовки «Мероприятия · …» и «Коды:» на одной строке;\n'
     '            // пустой месяц — заглушка в A (как в печати)',
     '// заголовки «Мероприятия · …» и «Коды:» на одной строке;\n'
     '            // пустой месяц — заглушка в A (как в печати).\n'
     '            // Task 441 (заявка: «коды сделай в один столбец»):\n'
     '            // коды — ОДИН столбец D (строка на код; двух\n'
     '            // колонок в Excel и не было — семантика сохранена)'),
])

# ----------------------------------------------------------------
# 2. tests/test-task434.js — сетка теперь ОДНА колонка
# ----------------------------------------------------------------
patch('tests/test-task434.js', [
    ("test('.wsp-legend-cols — сетка ДВЕ равные колонки', () => {\n"
     "        const r = ruleBlock('#wsPrintSheet .wsp-legend-cols {');\n"
     "        assertTrue(r !== '', 'правило сетки есть');\n"
     "        assertTrue(r.indexOf('display: grid') !== -1,\n"
     "            'контейнер — grid');\n"
     "        assertTrue(r.indexOf('grid-template-columns: 1fr 1fr') !== -1,\n"
     "            'ДВЕ равные колонки на всю ширину листа до конца');\n"
     "        assertTrue(r.indexOf('column-gap') !== -1,\n"
     "            'горизонтальный зазор между колонками');\n"
     "        assertTrue(r.indexOf('row-gap') !== -1,\n"
     "            'вертикальный зазор между записями');\n"
     "    });",
     "test('.wsp-legend-cols — сетка ОДНА колонка (Task 441)', () => {\n"
     "        const r = ruleBlock('#wsPrintSheet .wsp-legend-cols {');\n"
     "        assertTrue(r !== '', 'правило сетки есть');\n"
     "        assertTrue(r.indexOf('display: grid') !== -1,\n"
     "            'контейнер — grid');\n"
     "        // Task 441 (заявка: «коды сделай в один столбец»):\n"
     "        // ОДНА колонка — прежде ДВЕ равные (Task 434)\n"
     "        assertTrue(r.indexOf('grid-template-columns: 1fr') !== -1,\n"
     "            'ОДНА колонка на всю ширину блока кодов');\n"
     "        assertFalse(r.indexOf('grid-template-columns: 1fr 1fr') !== -1,\n"
     "            'две равные колонки Task 434 сняты (Task 441)');\n"
     "        assertFalse(r.indexOf('column-gap') !== -1,\n"
     "            'column-gap снят — колонок больше нет (Task 441)');\n"
     "        assertTrue(r.indexOf('row-gap') !== -1,\n"
     "            'вертикальный зазор между записями');\n"
     "    });"),
])

# ----------------------------------------------------------------
# 3. tests/test-task432.js — сетка одна колонка
# ----------------------------------------------------------------
patch('tests/test-task432.js', [
    ("// Task 434: ДВЕ КОЛОНКИ под названием «Коды:» (заявка)\n"
     "        const c = ruleBlock('#wsPrintSheet .wsp-legend-cols {');\n"
     "        assertTrue(c.indexOf('display: grid') !== -1 &&\n"
     "                   c.indexOf('grid-template-columns: 1fr 1fr') !== -1,\n"
     "            'Task 434: сетка-ДВЕ-КОЛОНКИ на всю ширину листа');",
     "// Task 434: две колонки; Task 441 — ОДНА колонка\n"
     "        const c = ruleBlock('#wsPrintSheet .wsp-legend-cols {');\n"
     "        assertTrue(c.indexOf('display: grid') !== -1 &&\n"
     "                   c.indexOf('grid-template-columns: 1fr') !== -1,\n"
     "            'Task 441: сетка-ОДНА-КОЛОНКА (прежде ДВЕ, Task 434)');"),
])

# ----------------------------------------------------------------
# 4. tests/test-task360.js — сетка одна колонка
# ----------------------------------------------------------------
patch('tests/test-task360.js', [
    ("assertTrue(cRule.indexOf('display: grid') !== -1 &&\n"
     "                   cRule.indexOf('grid-template-columns: 1fr 1fr') !== -1,\n"
     "            'две равные колонки на всю ширину листа');",
     "assertTrue(cRule.indexOf('display: grid') !== -1 &&\n"
     "                   cRule.indexOf('grid-template-columns: 1fr') !== -1,\n"
     "            'одна колонка на всю ширину блока кодов (Task 441)');"),
])

# ----------------------------------------------------------------
# 5. tests/test-task433.js — сетка одна колонка
# ----------------------------------------------------------------
patch('tests/test-task433.js', [
    ("const c = ruleBlock('#wsPrintSheet .wsp-legend-cols {');\n"
     "        assertTrue(c.indexOf('grid-template-columns: 1fr 1fr') !== -1,\n"
     "            'две равные колонки на всю ширину листа');",
     "const c = ruleBlock('#wsPrintSheet .wsp-legend-cols {');\n"
     "        assertTrue(c.indexOf('grid-template-columns: 1fr') !== -1,\n"
     "            'одна колонка на всю ширину блока кодов (Task 441)');"),
])

# ----------------------------------------------------------------
# 6. tests/test-task439.js — комментарий cdH: один столбец
# ----------------------------------------------------------------
patch('tests/test-task439.js', [
    ("// evH = 18 + 33×13 = 447; cdH (4 кода) = 46. Прежняя сумма\n"
     "        // (447 + 8 + 46 = 501; 54 + 501 = 555 > 549) не влезала —\n"
     "        // теперь пара = max(447, 46) = 447; 54 + 447 = 501 ≤ 549:",
     "// evH = 18 + 33×13 = 447; cdH (4 кода, ОДИН столбец\n"
     "        // Task 441) = 74. Прежняя сумма (447 + 8 + 74 = 529;\n"
     "        // 54 + 529 = 583 > 549) не влезала — теперь пара =\n"
     "        // max(447, 74) = 447; 54 + 447 = 501 ≤ 549:"),
])

# ----------------------------------------------------------------
# 7. tests/run-all.js — подключение test-task441.js
# ----------------------------------------------------------------
patch('tests/run-all.js', [
    ("require('./test-task440.js');\nrequire('./test-deploy-url.js');",
     "require('./test-task440.js');\n"
     "// Task 441 (заявка: «Во всех трёх представлениях печати коды\n"
     "// сделай в один столбец»): сетка кодов — ОДНА колонка в\n"
     "// HTML-печати (grid 1fr), PDF (codeRows без деления, lx без\n"
     "// сдвига colW2) и Excel (колонка D — строка на код)\n"
     "require('./test-task441.js');\nrequire('./test-deploy-url.js');"),
])

print('OK: Task 441 — патчи применены')
