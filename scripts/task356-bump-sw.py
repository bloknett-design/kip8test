#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 356: SW-бамп kipia-test-v584 → v585 (index.html менялся —
# шахматка табеля: точка «·» убрана и в ПУСТЫХ ячейках БЕЗ кодов
# событий на рабочих днях — пустая/«.»/статус-мероприятие показывают
# чистый центр, как выходные после Task 355; бейджи мероприятий,
# коды смен/неявок и планы «ОТ» — прежний вид).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v585 → v586
# (чтобы старые guards смотрели на новую несуществующую версию),
# ЗАТЕМ ассерты v584 → v585.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
# NOTE: test-task356.js пишется ПОСЛЕ этого скрипта (guard v586 в нём
# уже актуален), поэтому скрипт его не тронет.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v584'"
new = "CACHE_VERSION = 'kipia-test-v585'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v584'
assert 'kipia-test-v585' not in sw, 'sw.js: v585 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v584 -> kipia-test-v585')

# 2. tests/*.js — guard v585→v586, затем ассерты v584→v585
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v585')
    s = s.replace('kipia-test-v585', 'kipia-test-v586')
    n_assert = s.count('kipia-test-v584')
    s = s.replace('kipia-test-v584', 'kipia-test-v585')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v584→v585: %d, guard v585→v586: %d)' % (f, a, g))
