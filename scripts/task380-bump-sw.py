#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 380: SW-бамп kipia-test-v608 → v609 (index.html менялся —
# окно «Мероприятия»: фон строк по сроку; мобайл: запрет выделения
# текста в шахматке/итогах). Порядок замен в tests/ ВАЖЕН: СНАЧАЛА
# guard-ы v609 → v610 (guards смотрят на новую несуществующую),
# ЗАТЕМ ассерты v608 → v609. test-task380.js пишется ПОСЛЕ запуска
# (его ассерты v609/guard v610 уже актуальны).
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v608'"
new = "CACHE_VERSION = 'kipia-test-v609'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v608'
assert 'kipia-test-v609' not in sw, 'sw.js: v609 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v608 -> kipia-test-v609')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v609')
    s = s.replace('kipia-test-v609', 'kipia-test-v610')
    n_assert = s.count('kipia-test-v608')
    s = s.replace('kipia-test-v608', 'kipia-test-v609')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v608→v609: %d, guard v609→v610: %d)' % (f, a, g))
