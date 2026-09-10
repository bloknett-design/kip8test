#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 361: SW-бамп kipia-test-v589 → v590 (index.html менялся —
# печатная форма: колонка «Сотрудник» по ширине текста, крупнее
# таблица и шрифты, бейджи мероприятий в ячейках печати).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v590 → v591
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v589 → v590.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v589'"
new = "CACHE_VERSION = 'kipia-test-v590'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v589'
assert 'kipia-test-v590' not in sw, 'sw.js: v590 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v589 -> kipia-test-v590')

# 2. tests/*.js — guard v590→v591, затем ассерты v589→v590
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v590')
    s = s.replace('kipia-test-v590', 'kipia-test-v591')
    n_assert = s.count('kipia-test-v589')
    s = s.replace('kipia-test-v589', 'kipia-test-v590')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v589→v590: %d, guard v590→v591: %d)' % (f, a, g))

# 3. контроль: двойных v591-упоминаний вне guards не появилось
assert sw.count('kipia-test-v590') == 1
print('OK: единственный kipia-test-v590 в sw.js')
