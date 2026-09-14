#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 370: SW-бамп kipia-test-v598 → v599 (index.html менялся — цвет
# недоставленных показаний ярче и ближе к жёлтому: #ffc400 тёмная /
# #cc9900 светлая, было #f5a623 / #c96e00; заявка пользователя внести
# сразу и в тестовый, и в боевой проекты).
# Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v599 не существует» → v600, ЗАТЕМ ассерты
# v598 → v599. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v598'"
new = "CACHE_VERSION = 'kipia-test-v599'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v598'
assert 'kipia-test-v599' not in sw, 'sw.js: v599 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v598 -> kipia-test-v599')

# 2. tests/*.js — guard v599→v600, затем ассерты v598→v599
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v599')
    s = s.replace('kipia-test-v599', 'kipia-test-v600')
    n_assert = s.count('kipia-test-v598')
    s = s.replace('kipia-test-v598', 'kipia-test-v599')
    # сообщения guard-ов — под новую цель v600 (косметика)
    s = s.replace('v599 ещё не существует', 'v600 ещё не существует')
    s = s.replace('v598 ещё не существует', 'v600 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v598→v599: %d, guard v599→v600: %d)' % (f, a, g))

# 3. контроль: v599 в sw.js ровно один
assert sw.count('kipia-test-v599') == 1
print('OK: единственный kipia-test-v599 в sw.js')
