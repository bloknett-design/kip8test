#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 443: SW-бамп kipia-test-v666 → v667 (index.html + серверные
# скрипты СИЗ менялись: столбец G «дата_изготовления», приоритет
# расчёта даты окончания). Порядок замен в tests/ ВАЖЕН: СНАЧАЛА
# guard-ы v667 → v668 (ложный инкремент смотрит на новую
# несуществующую), ЗАТЕМ ассерты v666 → v667.
# SKIP: tests/test-task443.js (новый, сразу с v667).
import glob
import io

# 1. sw.js — CACHE_VERSION + комментарий Task 443
sw_path = 'sw.js'
sw = io.open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v666'"
new = "CACHE_VERSION = 'kipia-test-v667'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v666'
assert 'kipia-test-v667' not in sw, 'sw.js: v667 уже был (двойной бамп?)'
sw = sw.replace(old, new)
marker = ("\n// Task 442: печать табеля — мини-значки мероприятий в шахматке и"
          "\n// столбец кодов УДАЛЕНЫ во всех трёх представлениях; полосы"
          "\n// выходных календарных дней — ТОЛСТЫЙ внешний контур БЕЗ заливки"
          "\n// (HTML 2px края/верх/низ, PDF strokeRect ×2.8, Excel medium-"
          "\n// границы), даты выходных — ЖИРНЫЕ (HTML/PDF), будни в Excel —"
          "\n// НЕ жирные (новый стиль regDate).")
assert marker in sw, 'sw.js: не найден комментарий Task 442 (точка вставки)'
sw = sw.replace(marker, marker +
    "\n// Task 443: СИЗ — столбец G «дата_изготовления» (справа от"
    "\n// «дата_выдачи»; срок/окончание/примечание сместились в H/I/J):"
    "\n// дата окончания = дата ИЗГОТОВЛЕНИЯ + срок (приоритет),"
    "\n// иначе дата выдачи + срок; поле в шторке СИЗ, «изгот.» в"
    "\n// карточке; миграция ppeMigrateManufacture() в PPEInit.gs.")
io.open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v666 -> kipia-test-v667 + комментарий')

# 2. tests/*.js — guard v667→v668, затем ассерты v666→v667
SKIP = {'tests/test-task443.js'}
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') in SKIP:
        print('  SKIP (новый, уже v667): %s' % f)
        continue
    s = io.open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v667')
    s = s.replace('kipia-test-v667', 'kipia-test-v668')
    n_assert = s.count('kipia-test-v666')
    s = s.replace('kipia-test-v666', 'kipia-test-v667')
    if s != orig:
        io.open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v666→v667: %d, guard v667→v668: %d)' % (f, a, g))

# 3. run-all.js — подключить test-task443 после 442
RA = 'tests/run-all.js'
s = io.open(RA, encoding='utf-8').read()
A = "require('./test-task442.js');\n"
B = "require('./test-task442.js');\nrequire('./test-task443.js');\n"
assert s.count(A) == 1, 'run-all.js: якорь 442 не найден'
assert 'test-task443' not in s, 'run-all.js: 443 уже подключён'
s = s.replace(A, B)
io.open(RA, 'w', encoding='utf-8').write(s)
print('run-all.js: test-task443 подключён после 442')
