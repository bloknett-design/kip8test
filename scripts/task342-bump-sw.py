#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 342: SW-бамп kipia-test-v579 → v580 (kipia-test-v580).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v580 → v581
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v579 → v580.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v579'"
new = "CACHE_VERSION = 'kipia-test-v580'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v579'
assert 'kipia-test-v580' not in sw, 'sw.js: v580 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v579 -> kipia-test-v580')

# 2. tests/*.js — guard v580→v581, затем ассерты v579→v580
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v580')
    s = s.replace('kipia-test-v580', 'kipia-test-v581')
    n_assert = s.count('kipia-test-v579')
    s = s.replace('kipia-test-v579', 'kipia-test-v580')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v579→v580: %d, guard v580→v581: %d)' % (f, a, g))
