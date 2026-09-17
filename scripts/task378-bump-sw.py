#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 378: SW-бамп kipia-test-v606 → v607 (index.html менялся — итоги
# учёта #FFFFFF/нули/линии, перекрестье = «сегодня», окна бара без
# полосы + значок раскрытия). Порядок замен в tests/ ВАЖЕН:
# СНАЧАЛА guard-ы v607 → v608 (guards смотрят на новую несуществующую),
# ЗАТЕМ ассерты v606 → v607. test-task378.js пишется ПОСЛЕ запуска
# (его ассерты v607/guard v608 уже актуальны).
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v606'"
new = "CACHE_VERSION = 'kipia-test-v607'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v606'
assert 'kipia-test-v607' not in sw, 'sw.js: v607 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v606 -> kipia-test-v607')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v607')
    s = s.replace('kipia-test-v607', 'kipia-test-v608')
    n_assert = s.count('kipia-test-v606')
    s = s.replace('kipia-test-v606', 'kipia-test-v607')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v606→v607: %d, guard v607→v608: %d)' % (f, a, g))
