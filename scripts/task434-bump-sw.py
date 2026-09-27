#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 434: SW-бамп kipia-test-v659 → v660 (index.html менялся —
# печать: коды в ДВЕ КОЛОНКИ под названием «Коды:»; профиль:
# дата последней выполненной проверки знаний до 1000 В после
# знака группы; окна мероприятий ячеек — дата дд.мм.гггг).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v660 → v661
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v659 → v660.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v659'"
new = "CACHE_VERSION = 'kipia-test-v660'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v659'
assert 'kipia-test-v660' not in sw, 'sw.js: v660 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v659 -> kipia-test-v660')

# 2. tests/*.js — guard v660→v661, затем ассерты v659→v660
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v660')
    s = s.replace('kipia-test-v660', 'kipia-test-v661')
    n_assert = s.count('kipia-test-v659')
    s = s.replace('kipia-test-v659', 'kipia-test-v660')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v659→v660: %d, guard v660→v661: %d)' % (f, a, g))
