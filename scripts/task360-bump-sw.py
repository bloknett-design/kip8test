#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 360: SW-бамп kipia-test-v588 → v589 (index.html менялся —
# печатная форма: под шахматкой список мероприятий месяца и
# перечень кодов этого месяца, оба в один столбик).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v589 → v590
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v588 → v589.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v588'"
new = "CACHE_VERSION = 'kipia-test-v589'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v588'
assert 'kipia-test-v589' not in sw, 'sw.js: v589 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v588 -> kipia-test-v589')

# 2. tests/*.js — guard v589→v590, затем ассерты v588→v589
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v589')
    s = s.replace('kipia-test-v589', 'kipia-test-v590')
    n_assert = s.count('kipia-test-v588')
    s = s.replace('kipia-test-v588', 'kipia-test-v589')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v588→v589: %d, guard v589→v590: %d)' % (f, a, g))
