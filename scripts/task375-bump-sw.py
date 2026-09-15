#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 375: SW-бамп kipia-test-v603 → v604 (index.html менялся — печать
# табеля gap 10px + анти-дубли расходомеров).
# Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v604 не существует» → v605, ЗАТЕМ ассерты
# v603 → v604. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v603'"
new = "CACHE_VERSION = 'kipia-test-v604'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v603'
assert 'kipia-test-v604' not in sw, 'sw.js: v604 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v603 -> kipia-test-v604')

# 2. tests/*.js — guard v604→v605, затем ассерты v603→v604
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v604')
    s = s.replace('kipia-test-v604', 'kipia-test-v605')
    n_assert = s.count('kipia-test-v603')
    s = s.replace('kipia-test-v603', 'kipia-test-v604')
    # сообщения guard-ов — под новую цель v605 (косметика)
    s = s.replace('v604 ещё не существует', 'v605 ещё не существует')
    s = s.replace('v603 ещё не существует', 'v605 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v603→v604: %d, guard v604→v605: %d)' % (f, a, g))

# 3. контроль: v604 в sw.js ровно один
assert sw.count('kipia-test-v604') == 1
print('OK: единственный kipia-test-v604 в sw.js')
