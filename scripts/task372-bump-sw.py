#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 372: SW-бамп kipia-test-v600 → v601 (index.html менялся — раздел
# «Датчики температуры» переделан на страницу карточек + страницу датчика).
# Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v601 не существует» → v602, ЗАТЕМ ассерты
# v600 → v601. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v600'"
new = "CACHE_VERSION = 'kipia-test-v601'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v600'
assert 'kipia-test-v601' not in sw, 'sw.js: v601 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v600 -> kipia-test-v601')

# 2. tests/*.js — guard v601→v602, затем ассерты v600→v601
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v601')
    s = s.replace('kipia-test-v601', 'kipia-test-v602')
    n_assert = s.count('kipia-test-v600')
    s = s.replace('kipia-test-v600', 'kipia-test-v601')
    # сообщения guard-ов — под новую цель v602 (косметика)
    s = s.replace('v601 ещё не существует', 'v602 ещё не существует')
    s = s.replace('v600 ещё не существует', 'v602 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v600→v601: %d, guard v601→v602: %d)' % (f, a, g))

# 3. контроль: v601 в sw.js ровно один
assert sw.count('kipia-test-v601') == 1
print('OK: единственный kipia-test-v601 в sw.js')
