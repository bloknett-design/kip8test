#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 390: SW-бамп kipia-test-v617 → v618 (index.html менялся —
# «Общая» вкладка «Работников»: строки штата/текущего момента по
# категориям, выделенная шапка, примыкание ярлыков к окну, светлые
# тёплые ярлыки в тёмной теме).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v618 → v619 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v619;
#   ЗАТЕМ v617 → v618 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v617'"
new = "CACHE_VERSION = 'kipia-test-v618'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v617'
assert 'kipia-test-v618' not in sw, 'sw.js: v618 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v617 -> kipia-test-v618')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v618 отсутствует» → «v619 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v618')
    s = s.replace('kipia-test-v618', 'kipia-test-v619')
    # 2) ассерты «v617 присутствует» → «v618 присутствует»
    n_assert = s.count('kipia-test-v617')
    s = s.replace('kipia-test-v617', 'kipia-test-v618')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v617→v618: %d, guard v618→v619: %d)' % (f, a, g))
