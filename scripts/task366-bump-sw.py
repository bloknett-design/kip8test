#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 366: SW-бамп kipia-test-v594 → v595 (index.html менялся —
# баннер недоставленных показаний с номерами расходомеров без иконки
# + server_busy как повторяемая ошибка outbox). FlowmeterArchive.gs —
# сервер Apps Script, в кэш PWA не входит.
# Порядок замен в tests/ ВАЖЕН (урок Task 361): СНАЧАЛА guard-ы
# «v595 не существует» → v596, ЗАТЕМ ассерты v594 → v595.
# Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v594'"
new = "CACHE_VERSION = 'kipia-test-v595'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v594'
assert 'kipia-test-v595' not in sw, 'sw.js: v595 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v594 -> kipia-test-v595')

# 2. tests/*.js — guard v595→v596, затем ассерты v594→v595
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v595')
    s = s.replace('kipia-test-v595', 'kipia-test-v596')
    n_assert = s.count('kipia-test-v594')
    s = s.replace('kipia-test-v594', 'kipia-test-v595')
    # сообщения guard-ов — под новую цель v596 (косметика)
    s = s.replace('v595 ещё не существует', 'v596 ещё не существует')
    s = s.replace('v594 ещё не существует', 'v596 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v594→v595: %d, guard v595→v596: %d)' % (f, a, g))

# 3. контроль: v595 в sw.js ровно один
assert sw.count('kipia-test-v595') == 1
print('OK: единственный kipia-test-v595 в sw.js')
