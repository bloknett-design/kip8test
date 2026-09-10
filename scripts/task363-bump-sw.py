#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 363: SW-бамп kipia-test-v591 → v592 (index.html менялся —
# шахматка: фон выходных как пустые, красная рамка-группа вокруг
# столбцов выходных, розовый + фон даты — праздники).
# Порядок замен в tests/ ВАЖЕН (урок Task 361): СНАЧАЛА guard-ы
# «v592 не существует» → v593, ЗАТЕМ ассерты v591 → v592.
# Сообщения guard-ов подчищаются под новую цель (v593).
# Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v591'"
new = "CACHE_VERSION = 'kipia-test-v592'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v591'
assert 'kipia-test-v592' not in sw, 'sw.js: v592 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v591 -> kipia-test-v592')

# 2. tests/*.js — guard v592→v593, затем ассерты v591→v592
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v592')
    s = s.replace('kipia-test-v592', 'kipia-test-v593')
    n_assert = s.count('kipia-test-v591')
    s = s.replace('kipia-test-v591', 'kipia-test-v592')
    # сообщения guard-ов — под новую цель v593 (косметика)
    s = s.replace('v592 ещё не существует', 'v593 ещё не существует')
    s = s.replace('v591 ещё не существует', 'v593 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v591→v592: %d, guard v592→v593: %d)' % (f, a, g))

# 3. контроль: v592 в sw.js ровно один
assert sw.count('kipia-test-v592') == 1
print('OK: единственный kipia-test-v592 в sw.js')
