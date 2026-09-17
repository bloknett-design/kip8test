#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 379: SW-бамп kipia-test-v607 → v608 (index.html менялся —
# шахматка: пустые ячейки светлой темы #FFFFFF; окна бара:
# раскрытие = оверлей вниз поверх бара, габарит бара неизменен).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v608 → v609 (guards
# смотрят на новую несуществующую), ЗАТЕМ ассерты v607 → v608.
# test-task379.js пишется ПОСЛЕ запуска (его ассерты v608/guard
# v609 уже актуальны).
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v607'"
new = "CACHE_VERSION = 'kipia-test-v608'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v607'
assert 'kipia-test-v608' not in sw, 'sw.js: v608 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v607 -> kipia-test-v608')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v608')
    s = s.replace('kipia-test-v608', 'kipia-test-v609')
    n_assert = s.count('kipia-test-v607')
    s = s.replace('kipia-test-v607', 'kipia-test-v608')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v607→v608: %d, guard v608→v609: %d)' % (f, a, g))
