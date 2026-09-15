#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 374: SW-бамп kipia-test-v602 → v603 (index.html менялся — датчики
# температуры: кнопка «Копировать» над таблицами значений убрана).
# Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v603 не существует» → v604, ЗАТЕМ ассерты
# v602 → v603. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v602'"
new = "CACHE_VERSION = 'kipia-test-v603'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v602'
assert 'kipia-test-v603' not in sw, 'sw.js: v603 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v602 -> kipia-test-v603')

# 2. tests/*.js — guard v603→v604, затем ассерты v602→v603
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v603')
    s = s.replace('kipia-test-v603', 'kipia-test-v604')
    n_assert = s.count('kipia-test-v602')
    s = s.replace('kipia-test-v602', 'kipia-test-v603')
    # сообщения guard-ов — под новую цель v604 (косметика)
    s = s.replace('v603 ещё не существует', 'v604 ещё не существует')
    s = s.replace('v602 ещё не существует', 'v604 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v602→v603: %d, guard v603→v604: %d)' % (f, a, g))

# 3. контроль: v603 в sw.js ровно один
assert sw.count('kipia-test-v603') == 1
print('OK: единственный kipia-test-v603 в sw.js')
