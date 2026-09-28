#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: SW-бамп kipia-test-v665 → v666 (index.html менялся —
# печать: мини-значки мероприятий и столбец кодов удалены, полосы
# выходных — толстый внешний контур без заливки, даты выходных
# жирнее; Excel — medium-контуры и НЕ жирные будни). Порядок замен
# в tests/ ВАЖЕН: СНАЧАЛА guard-ы v666 → v667 (ложный инкремент
# смотрит на новую несуществующую), ЗАТЕМ ассерты v665 → v666.
# SKIP: test-task441.js (переписан под удаление кодов — уже v666)
# и test-task442.js (новый, сразу с v666).
import glob
import io

# 1. sw.js — CACHE_VERSION + комментарий Task 442
sw_path = 'sw.js'
sw = io.open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v665'"
new = "CACHE_VERSION = 'kipia-test-v666'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v665'
assert 'kipia-test-v666' not in sw, 'sw.js: v666 уже был (двойной бамп?)'
sw = sw.replace(old, new)
marker = ("\n// Task 441: печать табеля — коды ОДНИМ столбцом во всех трёх"
          "\n// представлениях (HTML: grid 1fr вместо двух колонок; PDF:"
          "\n// codeRows = длина кодов, отрисовка сквозным столбцом от codeX;"
          "\n// Excel: столбец D — строка на код, как и было).")
assert marker in sw, 'sw.js: не найден комментарий Task 441 (точка вставки)'
sw = sw.replace(marker, marker +
    "\n// Task 442: печать табеля — мини-значки мероприятий в шахматке и"
    "\n// столбец кодов УДАЛЕНЫ во всех трёх представлениях; полосы"
    "\n// выходных календарных дней — ТОЛСТЫЙ внешний контур БЕЗ заливки"
    "\n// (HTML 2px края/верх/низ, PDF strokeRect ×2.8, Excel medium-"
    "\n// границы), даты выходных — ЖИРНЫЕ (HTML/PDF), будни в Excel —"
    "\n// НЕ жирные (новый стиль regDate).")
io.open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v665 -> kipia-test-v666 + комментарий')

# 2. tests/*.js — guard v666→v667, затем ассерты v665→v666
SKIP = {'tests/test-task441.js', 'tests/test-task442.js'}
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') in SKIP:
        print('  SKIP (уже на v666): %s' % f)
        continue
    s = io.open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v666')
    s = s.replace('kipia-test-v666', 'kipia-test-v667')
    n_assert = s.count('kipia-test-v665')
    s = s.replace('kipia-test-v665', 'kipia-test-v666')
    if s != orig:
        io.open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v665→v666: %d, guard v666→v667: %d)' % (f, a, g))

# 3. run-all.js — подключить test-task442 после 441
RA = 'tests/run-all.js'
s = io.open(RA, encoding='utf-8').read()
A = "require('./test-task441.js');\n"
B = "require('./test-task441.js');\nrequire('./test-task442.js');\n"
assert s.count(A) == 1, 'run-all.js: якорь 441 не найден'
assert 'test-task442' not in s, 'run-all.js: 442 уже подключён'
s = s.replace(A, B)
io.open(RA, 'w', encoding='utf-8').write(s)
print('run-all.js: test-task442 подключён после 441')
