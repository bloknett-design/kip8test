#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 381: SW-бамп kipia-test-v609 → v610 (index.html менялся —
# итоги: фон как до белого + зебра; значки раскрытия приколоты при
# прокрутке; мероприятия — общий фон окна вместо плашек). Порядок
# замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v610 → v611 (guards смотрят
# на новую несуществующую), ЗАТЕМ ассерты v609 → v610. Адаптации
# тестов 378/379/322/321/380 и test-task381.js делаются ПОСЛЕ запуска.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v609'"
new = "CACHE_VERSION = 'kipia-test-v610'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v609'
assert 'kipia-test-v610' not in sw, 'sw.js: v610 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v609 -> kipia-test-v610')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v610')
    s = s.replace('kipia-test-v610', 'kipia-test-v611')
    n_assert = s.count('kipia-test-v609')
    s = s.replace('kipia-test-v609', 'kipia-test-v610')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v609→v610: %d, guard v610→v611: %d)' % (f, a, g))
