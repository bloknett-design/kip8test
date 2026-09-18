#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 382: SW-бамп kipia-test-v610 → v611 (index.html менялся —
# мобильная страница итогов, вкладка «Месяц»: ИЗНАЧАЛЬНАЯ ширина
# столбца с фамилиями — ПО ШИРИНЕ ТЕКСТА в ячейках, как на вкладке
# «Год»; переменная --ws-tt-emp-w, мерит _measureTtEmpFullW).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v611 → v612 (guards
# смотрят на новую несуществующую), ЗАТЕМ ассерты v610 → v611.
# Адаптации тестов 325/327/329 (width 42%) и test-task382.js
# делаются ДО/ПОСЛЕ запуска независимо от этого скрипта.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v610'"
new = "CACHE_VERSION = 'kipia-test-v611'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v610'
assert 'kipia-test-v611' not in sw, 'sw.js: v611 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v610 -> kipia-test-v611')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v611')
    s = s.replace('kipia-test-v611', 'kipia-test-v612')
    n_assert = s.count('kipia-test-v610')
    s = s.replace('kipia-test-v610', 'kipia-test-v611')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v610→v611: %d, guard v611→v612: %d)' % (f, a, g))
