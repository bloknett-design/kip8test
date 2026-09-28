#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 441: SW-бамп kipia-test-v664 → v665 (index.html менялся —
# печать табеля: коды — ОДИН столбец во всех трёх представлениях:
# HTML grid 1fr, PDF codeRows без деления и lx без сдвига,
# Excel — столбец D). Порядок замен в tests/ ВАЖЕН: СНАЧАЛА
# guard-ы v665 → v666 (чтобы старые «ложный инкремент»-guards
# смотрели на новую несуществующую версию), ЗАТЕМ ассерты
# v664 → v665. НОВЫЙ test-task441.js ещё не в прогонах — SKIP
# (он пишется сразу с ассертами v665).
import glob

# 1. sw.js — CACHE_VERSION + комментарий Task 441
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v664'"
new = "CACHE_VERSION = 'kipia-test-v665'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v664'
assert 'kipia-test-v665' not in sw, 'sw.js: v665 уже был (двойной бамп?)'
sw = sw.replace(old, new)
marker = ("\n// Task 440: печать табеля — зазор между мероприятиями и кодами"
          "\n// РОВНО 10px во всех трёх представлениях (HTML gap 10px, PDF"
          "\n// 7.5pt, Excel indent 1 у кодов); карточка работника — кнопка"
          "\n// «следующий год» активна по записям раздела (_wtabYearMax),"
          "\n// блок «Отпуска» — своя навигация ‹год› (пул _VAC_YEARS, лениво"
          "\n// listVacations по соседним годам).")
assert marker in sw, 'sw.js: не найден комментарий Task 440 (точка вставки)'
sw = sw.replace(marker, marker +
    "\n// Task 441: печать табеля — коды ОДНИМ столбцом во всех трёх"
    "\n// представлениях (HTML: grid 1fr вместо двух колонок; PDF:"
    "\n// codeRows = длина кодов, отрисовка сквозным столбцом от codeX;"
    "\n// Excel: столбец D — строка на код, как и было).")
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v664 -> kipia-test-v665 + комментарий')

# 2. tests/*.js — guard v665→v666, затем ассерты v664→v665
SKIP = {'tests/test-task441.js'}
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') in SKIP:
        print('  SKIP (новый тест уже на v665): %s' % f)
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v665')
    s = s.replace('kipia-test-v665', 'kipia-test-v666')
    n_assert = s.count('kipia-test-v664')
    s = s.replace('kipia-test-v664', 'kipia-test-v665')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v664→v665: %d, guard v665→v666: %d)' % (f, a, g))
