#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 371: SW-бамп kipia-test-v599 → v600 (index.html менялся — блок
# «Расчёт произвольных значений» на странице «Датчики температуры»,
# под таблицей значений, по примеру раздела «Шкала-сигнал»).
# Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v600 не существует» → v601, ЗАТЕМ ассерты
# v599 → v600. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v599'"
new = "CACHE_VERSION = 'kipia-test-v600'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v599'
assert 'kipia-test-v600' not in sw, 'sw.js: v600 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v599 -> kipia-test-v600')

# 2. tests/*.js — guard v600→v601, затем ассерты v599→v600
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v600')
    s = s.replace('kipia-test-v600', 'kipia-test-v601')
    n_assert = s.count('kipia-test-v599')
    s = s.replace('kipia-test-v599', 'kipia-test-v600')
    # сообщения guard-ов — под новую цель v601 (косметика)
    s = s.replace('v600 ещё не существует', 'v601 ещё не существует')
    s = s.replace('v599 ещё не существует', 'v601 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v599→v600: %d, guard v600→v601: %d)' % (f, a, g))

# 3. контроль: v600 в sw.js ровно один
assert sw.count('kipia-test-v600') == 1
print('OK: единственный kipia-test-v600 в sw.js')
