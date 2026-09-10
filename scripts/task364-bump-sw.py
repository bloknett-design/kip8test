#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 364: SW-бамп kipia-test-v592 → v593 (index.html менялся —
# рамка-группа выходных 2px #e57373; печать: коды — правая колонка
# ряда мероприятий, обёртка wsp-bottom).
# Порядок замен в tests/ ВАЖЕН (урок Task 361): СНАЧАЛА guard-ы
# «v593 не существует» → v594, ЗАТЕМ ассерты v592 → v593.
# Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v592'"
new = "CACHE_VERSION = 'kipia-test-v593'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v592'
assert 'kipia-test-v593' not in sw, 'sw.js: v593 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v592 -> kipia-test-v593')

# 2. tests/*.js — guard v593→v594, затем ассерты v592→v593
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v593')
    s = s.replace('kipia-test-v593', 'kipia-test-v594')
    n_assert = s.count('kipia-test-v592')
    s = s.replace('kipia-test-v592', 'kipia-test-v593')
    # сообщения guard-ов — под новую цель v594 (косметика)
    s = s.replace('v593 ещё не существует', 'v594 ещё не существует')
    s = s.replace('v592 ещё не существует', 'v594 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v592→v593: %d, guard v593→v594: %d)' % (f, a, g))

# 3. контроль: v593 в sw.js ровно один
assert sw.count('kipia-test-v593') == 1
print('OK: единственный kipia-test-v593 в sw.js')
