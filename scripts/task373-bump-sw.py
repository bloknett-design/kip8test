#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 373: SW-бамп kipia-test-v601 → v602 (index.html менялся — датчики
# температуры: мобильные карточки столбиком, избранное TempFav, бейджи
# ТС/ТП убраны, ТХК (L), панель расчёта над формой).
# Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v602 не существует» → v603, ЗАТЕМ ассерты
# v601 → v602. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v601'"
new = "CACHE_VERSION = 'kipia-test-v602'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v601'
assert 'kipia-test-v602' not in sw, 'sw.js: v602 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v601 -> kipia-test-v602')

# 2. tests/*.js — guard v602→v603, затем ассерты v601→v602
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v602')
    s = s.replace('kipia-test-v602', 'kipia-test-v603')
    n_assert = s.count('kipia-test-v601')
    s = s.replace('kipia-test-v601', 'kipia-test-v602')
    # сообщения guard-ов — под новую цель v603 (косметика)
    s = s.replace('v602 ещё не существует', 'v603 ещё не существует')
    s = s.replace('v601 ещё не существует', 'v603 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v601→v602: %d, guard v602→v603: %d)' % (f, a, g))

# 3. контроль: v602 в sw.js ровно один
assert sw.count('kipia-test-v602') == 1
print('OK: единственный kipia-test-v602 в sw.js')
