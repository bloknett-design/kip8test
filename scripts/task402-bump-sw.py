#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 402: SW-бамп kipia-test-v628 → v629 (index.html и WorkSchedule.gs
# менялись — строка типа работника третьей строкой ячейки сетки;
# «группа_допуска» в ячейке/карточке/сводной/шторке правки работника;
# GAS: столбец по заголовку листа).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v629 → v630 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v630;
#   ЗАТЕМ v628 → v629 — ассерты «присутствует» едут на текущую.
# tests/test-task402.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v629 + guard v630).
import glob

OWN = 'tests/test-task402.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v628'"
new = "CACHE_VERSION = 'kipia-test-v629'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v628'
assert 'kipia-test-v629' not in sw, 'sw.js: v629 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v628 -> kipia-test-v629')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v629 отсутствует» → «v630 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v629')
    s = s.replace('kipia-test-v629', 'kipia-test-v630')
    # 2) ассерты «v628 присутствует» → «v629 присутствует»
    n_assert = s.count('kipia-test-v628')
    s = s.replace('kipia-test-v628', 'kipia-test-v629')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v628->v629: %d, guard v629->v630: %d)' % (f, a, g))
