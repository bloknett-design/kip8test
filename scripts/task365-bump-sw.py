#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 365: SW-бамп kipia-test-v593 → v594 (index.html менялся —
# нормализация периода №12 «Ежедневно» (_normalizeMeters в 3 точках
# данных) + поправка заявки в комментариях; data/flowmeters.json —
# №12 «Ежедневно», файл в кэш-листе SW).
# Порядок замен в tests/ ВАЖЕН (урок Task 361): СНАЧАЛА guard-ы
# «v594 не существует» → v595, ЗАТЕМ ассерты v593 → v594.
# Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v593'"
new = "CACHE_VERSION = 'kipia-test-v594'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v593'
assert 'kipia-test-v594' not in sw, 'sw.js: v594 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v593 -> kipia-test-v594')

# 2. tests/*.js — guard v594→v595, затем ассерты v593→v594
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v594')
    s = s.replace('kipia-test-v594', 'kipia-test-v595')
    n_assert = s.count('kipia-test-v593')
    s = s.replace('kipia-test-v593', 'kipia-test-v594')
    # сообщения guard-ов — под новую цель v595 (косметика)
    s = s.replace('v594 ещё не существует', 'v595 ещё не существует')
    s = s.replace('v593 ещё не существует', 'v595 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v593→v594: %d, guard v594→v595: %d)' % (f, a, g))

# 3. контроль: v594 в sw.js ровно один
assert sw.count('kipia-test-v594') == 1
print('OK: единственный kipia-test-v594 в sw.js')
