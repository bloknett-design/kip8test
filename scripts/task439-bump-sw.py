#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 439: SW-бамп kipia-test-v662 → v663 (index.html менялся —
# печать табеля: коды справа от мероприятий, колонка работника
# ФИО+Тип; мобильная шахматка: дедуп легаси-«.» в выборе кодов).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v663 → v664
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v662 → v663.
# НОВЫЙ test-task439.js ещё не в прогонах на старой версии —
# он уже написан с ассертами v663 / guard v664 → SKIP.
import glob

# 1. sw.js — CACHE_VERSION + комментарий Task 439
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v662'"
new = "CACHE_VERSION = 'kipia-test-v663'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v662'
assert 'kipia-test-v663' not in sw, 'sw.js: v663 уже был (двойной бамп?)'
sw = sw.replace(old, new)
marker = ("// предпросмотра: «Сохранить PDF» (canvas→JPEG→PDF) и «Сохранить"
          "\n// Excel» (xlsx-писатель с цветными ячейками) вместо HTML-файла.")
assert marker in sw, 'sw.js: не найден комментарий Task 438 (точка вставки)'
sw = sw.replace(marker, marker +
    "\n// Task 439: печать табеля — блок кодов СПРАВА от мероприятий"
    "\n// (HTML/PDF/Excel), в колонке работников только ФИО и Тип"
    "\n// (ширина — по самому большому тексту); попап ячеек шахматки —"
    "\n// легаси-код «.» («Выходной, плановый выходной день») скрыт при"
    "\n// каноническом слоте «Выходной» (пустой код).")
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v662 -> kipia-test-v663 + комментарий')

# 2. tests/*.js — guard v663→v664, затем ассерты v662→v663
SKIP = {'tests/test-task439.js'}
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') in SKIP:
        print('  SKIP (новый тест уже на v663): %s' % f)
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v663')
    s = s.replace('kipia-test-v663', 'kipia-test-v664')
    n_assert = s.count('kipia-test-v662')
    s = s.replace('kipia-test-v662', 'kipia-test-v663')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v662→v663: %d, guard v663→v664: %d)' % (f, a, g))
