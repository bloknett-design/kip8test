#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 377: SW-бамп kipia-test-v605 → v606 (index.html менялся — усиление
# «сегодня» + полосы светлой темы). Порядок замен в tests/ ВАЖЕН:
# СНАЧАЛА guard-ы v606 → v607 (guards смотрят на новую несуществующую),
# ЗАТЕМ ассерты v605 → v606. test-task377.js пишется ПОСЛЕ запуска
# (его ассерты v606/guard v607 уже актуальны).
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v605'"
new = "CACHE_VERSION = 'kipia-test-v606'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v605'
assert 'kipia-test-v606' not in sw, 'sw.js: v606 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v605 -> kipia-test-v606')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v606')
    s = s.replace('kipia-test-v606', 'kipia-test-v607')
    n_assert = s.count('kipia-test-v605')
    s = s.replace('kipia-test-v605', 'kipia-test-v606')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v605→v606: %d, guard v606→v607: %d)' % (f, a, g))
