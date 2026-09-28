#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 440 — адаптация исторических тестов kip8test:
1) 19 файлов с VM-хостами годов (методы извлекаются из index.html):
   в каждый хост с _wtabYearMin добавить извлечения НОВЫХ методов
   _wtabYearMax + _vacYearRange (их теперь зовут _wtabYearShift/
   _wtabYearNav/_renderWorkerCard);
2) зазор печати: ассерты gap: 6mm → gap: 10px (test-task364/432/433/
   439), инверсия «10px больше не нужен» в test-task375 (Task 440
   вернул 10px);
3) test-task439: colGap 12 → 7.5 (в т.ч. формула evW);
4) test-task435: новые строки выбора хранилища (fam 2) и famArg.
"""
import io

BASE = '/home/z/my-project/kip8test/'

def rd(p):
    return io.open(BASE + p, encoding='utf-8').read()

def wr(p, s):
    io.open(BASE + p, 'w', encoding='utf-8').write(s)

def rep(path, old, new, what, cnt=None):
    s = rd(path)
    c = s.count(old)
    assert (cnt is None and c >= 1) or c == cnt, \
        'FAIL [%s / %s]: найдено %d (ожидалось %s)' % (path, what, c, cnt)
    s = s.replace(old, new)
    wr(path, s)
    print('OK  %s: %s (%d замен)' % (path, what, c))

# ----------------------------------------------------------------------
# 1. VM-хосты: +_wtabYearMax +_vacYearRange (после _wtabYearMin)
# ----------------------------------------------------------------------
HOST_FILES = ['392', '393', '394', '395', '396', '403', '404', '405',
               '406', '407', '408', '414', '416', '417', '431', '432',
               '433', '434', '435']
INJ_OLD = "methodText(INDEX_SRC, '_wtabYearMin') + ',\\n' +"
INJ_NEW = ("methodText(INDEX_SRC, '_wtabYearMin') + ',\\n' +\n"
           "        methodText(INDEX_SRC, '_wtabYearMax') + ',\\n' +\n"
           "        methodText(INDEX_SRC, '_vacYearRange') + ',\\n' +")
total = 0
for f in HOST_FILES:
    p = 'tests/test-task%s.js' % f
    s = rd(p)
    c = s.count(INJ_OLD)
    assert c >= 1, 'FAIL [%s]: строка _wtabYearMin-хоста не найдена' % p
    s = s.replace(INJ_OLD, INJ_NEW)
    wr(p, s)
    total += c
    print('OK  %s: хосты +%d (макс/диапазон отпусков)' % (p, c))
print('хостов адаптировано: %d' % total)

# ----------------------------------------------------------------------
# 2. Зазор печати: 6mm → 10px
# ----------------------------------------------------------------------
rep('tests/test-task364.js',
    "        assertTrue(r.indexOf('gap: 6mm') !== -1, 'зазор между блоками');",
    "        // Task 440 (заявка: «на расстоянии друг от друга 10px»):\n"
    "        // зазор ряда — ровно 10px (прежде 6mm Task 439)\n"
    "        assertTrue(r.indexOf('gap: 10px') !== -1, 'зазор между блоками — 10px (Task 440)');",
    'gap 6mm → 10px')

rep('tests/test-task433.js',
    """        assertTrue(r.indexOf('gap: 6mm') !== -1,
            'зазор между мероприятиями и кодами (Task 439)');""",
    """        // Task 440: зазор ряда — ровно 10px (прежде 6mm)
        assertTrue(r.indexOf('gap: 10px') !== -1,
            'зазор между мероприятиями и кодами — 10px (Task 440)');""",
    'gap 6mm → 10px')

rep('tests/test-task432.js',
    """        assertTrue(r.indexOf('gap: 6mm') !== -1,
            'зазор между блоками ряда (Task 439)');""",
    """        // Task 440: зазор ряда — ровно 10px (прежде 6mm)
        assertTrue(r.indexOf('gap: 10px') !== -1,
            'зазор между блоками ряда — 10px (Task 440)');""",
    'gap 6mm → 10px')

rep('tests/test-task439.js',
    """    test('CSS: .wsp-bottom — flex-ряд с зазором 6mm', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r.indexOf('display: flex') !== -1, 'обёртка — гибкий ряд');
        assertTrue(r.indexOf('align-items: flex-start') !== -1,
            'блоки прижаты к общей верхней линии');
        assertTrue(r.indexOf('gap: 6mm') !== -1, 'зазор между блоками 6mm');""",
    """    test('CSS: .wsp-bottom — flex-ряд с зазором 10px (Task 440)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r.indexOf('display: flex') !== -1, 'обёртка — гибкий ряд');
        assertTrue(r.indexOf('align-items: flex-start') !== -1,
            'блоки прижаты к общей верхней линии');
        // Task 440 (заявка: «на расстоянии друг от друга 10px»)
        assertTrue(r.indexOf('gap: 10px') !== -1,
            'зазор между блоками — ровно 10px');
        assertTrue(r.indexOf('gap: 6mm') === -1,
            'прежний зазор 6mm убран');""",
    'gap 6mm → 10px (+негативный ассерт)')

rep('tests/test-task375.js',
    """        assertTrue(r.indexOf('gap: 10px') === -1,
            'зазор 10px между столбиками больше не нужен (столбиков нет)');""",
    """        // Task 440 (заявка: «коды справа от мероприятий на
        // расстоянии друг от друга 10px»): ряд Task 439 — зазор
        // между блоками СНОВА ровно 10px (как в Task 375)
        assertTrue(r.indexOf('gap: 10px') !== -1,
            'зазор между блоками ряда — ровно 10px (Task 440)');""",
    'инверсия: 10px снова нужен (Task 440)')

# ----------------------------------------------------------------------
# 3. test-task439: colGap 12 → 7.5 (10 CSS-px = 7.5 pt)
# ----------------------------------------------------------------------
rep('tests/test-task439.js',
    """        assertEqual(lay.colGap, 12, 'зазор между мероприятиями и кодами');
        assertEqual(lay.evW, lay.W - 2 * lay.M - 235 - 12,
            'левая зона мероприятий = остаток ширины');""",
    """        // Task 440: зазор 10px = 7.5pt (1px = 0.75pt)
        assertEqual(lay.colGap, 7.5, 'зазор между мероприятиями и кодами — 7.5pt (= 10px)');
        assertEqual(lay.evW, lay.W - 2 * lay.M - 235 - 7.5,
            'левая зона мероприятий = остаток ширины');""",
    'colGap 12 → 7.5')

# ----------------------------------------------------------------------
# 4. test-task435: fam 2 (строки выбора хранилища и famArg)
# ----------------------------------------------------------------------
rep('tests/test-task435.js',
    """        assertTrue(fn.indexOf("var store = (fam === 1) ? this._wtabYearInstr : this._wtabYear;") !== -1,
            'fam 1 — хранилище инструктажей, fam 0/не задан — мероприятий');""",
    """        assertTrue(fn.indexOf("var store = (fam === 1) ? this._wtabYearInstr") !== -1 &&
                   fn.indexOf("(fam === 2) ? this._wtabYearVac : this._wtabYear;") !== -1,
            'fam 1 — инструктажи, fam 2 — отпуска (Task 440), fam 0/не задан — мероприятия');""",
    '_wtabYearOf: fam 2 в ассерте')

rep('tests/test-task435.js',
    """        assertTrue(fn.indexOf("var store = (fam === 1) ? '_wtabYearInstr' : '_wtabYear';") !== -1,
            'смена года пишет ТОЛЬКО в своё хранилище');""",
    """        assertTrue(fn.indexOf("var store = (fam === 1) ? '_wtabYearInstr'") !== -1 &&
                   fn.indexOf("(fam === 2) ? '_wtabYearVac' : '_wtabYear';") !== -1,
            'смена года пишет ТОЛЬКО в своё хранилище (fam 2 — отпуска, Task 440)');""",
    '_wtabYearShift: fam 2 в ассерте')

rep('tests/test-task435.js',
    """        assertTrue(fn.indexOf("var famArg = (fam === 1) ? ', 1' : '';") !== -1,
            'третий аргумент — только у навигатора инструктажей');""",
    """        assertTrue(fn.indexOf("var famArg = (fam === 1 || fam === 2) ? ', ' + fam : '';") !== -1,
            'третий аргумент — у навигаторов инструктажей (1) и отпусков (2, Task 440)');""",
    'famArg fam 2 в ассерте')

print('\nАдаптация завершена')
