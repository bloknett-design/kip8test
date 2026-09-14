#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 367: SW-бамп kipia-test-v595 → v596 (index.html менялся —
# баннер недоставленных показаний убран, вместо него жёлто-оранжевый
# цвет значений карточек .flow-summary-val-pending; _isOverdue —
# регэкспы распознавания периодов; перерендеры после _outboxAdd и
# в finish() флаша). Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v596 не существует» → v597, ЗАТЕМ ассерты
# v595 → v596. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v595'"
new = "CACHE_VERSION = 'kipia-test-v596'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v595'
assert 'kipia-test-v596' not in sw, 'sw.js: v596 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v595 -> kipia-test-v596')

# 2. tests/*.js — guard v596→v597, затем ассерты v595→v596
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v596')
    s = s.replace('kipia-test-v596', 'kipia-test-v597')
    n_assert = s.count('kipia-test-v595')
    s = s.replace('kipia-test-v595', 'kipia-test-v596')
    # сообщения guard-ов — под новую цель v597 (косметика)
    s = s.replace('v596 ещё не существует', 'v597 ещё не существует')
    s = s.replace('v595 ещё не существует', 'v597 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v595→v596: %d, guard v596→v597: %d)' % (f, a, g))

# 3. контроль: v596 в sw.js ровно один
assert sw.count('kipia-test-v596') == 1
print('OK: единственный kipia-test-v596 в sw.js')
