#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 440: SW-бамп kipia-test-v663 → v664 (index.html менялся —
# печать табеля: зазор 10px между мероприятиями и кодами во всех
# трёх представлениях; карточки: › по записям следующего года
# (_wtabYearMax), блок «Отпуска» — своя навигация ‹год› по пулу
# годов отпусков). Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы
# v664 → v665 (чтобы старые «ложный инкремент»-guards смотрели на
# новую несуществующую версию), ЗАТЕМ ассерты v663 → v664.
# НОВЫЙ test-task440.js ещё не в прогонах — SKIP (он пишется сразу
# с ассертами v664 / guard v665).
import glob

# 1. sw.js — CACHE_VERSION + комментарий Task 440
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v663'"
new = "CACHE_VERSION = 'kipia-test-v664'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v663'
assert 'kipia-test-v664' not in sw, 'sw.js: v664 уже был (двойной бамп?)'
sw = sw.replace(old, new)
marker = ("// легаси-код «.» («Выходной, плановый выходной день») скрыт при"
          "\n// каноническом слоте «Выходной» (пустой код).")
assert marker in sw, 'sw.js: не найден комментарий Task 439 (точка вставки)'
sw = sw.replace(marker, marker +
    "\n// Task 440: печать табеля — зазор между мероприятиями и кодами"
    "\n// РОВНО 10px во всех трёх представлениях (HTML gap 10px, PDF"
    "\n// 7.5pt, Excel indent 1 у кодов); карточка работника — кнопка"
    "\n// «следующий год» активна по записям раздела (_wtabYearMax),"
    "\n// блок «Отпуска» — своя навигация ‹год› (пул _VAC_YEARS, лениво"
    "\n// listVacations по соседним годам).")
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v663 -> kipia-test-v664 + комментарий')

# 2. tests/*.js — guard v664→v665, затем ассерты v663→v664
SKIP = {'tests/test-task440.js'}
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') in SKIP:
        print('  SKIP (новый тест уже на v664): %s' % f)
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v664')
    s = s.replace('kipia-test-v664', 'kipia-test-v665')
    n_assert = s.count('kipia-test-v663')
    s = s.replace('kipia-test-v663', 'kipia-test-v664')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v663→v664: %d, guard v664→v665: %d)' % (f, a, g))
