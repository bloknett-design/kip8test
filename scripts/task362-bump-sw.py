#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 362: SW-бамп kipia-test-v590 → v591 (index.html менялся —
# печатная форма: мероприятия только печатаемого вида, коды
# мероприятий в перечне кодов).
# Порядок замен в tests/ ВАЖЕН (урок Task 361): СНАЧАЛА guard-ы
# «v591 не существует» → v592 (32 файла: 315…361 и flow-period),
# ЗАТЕМ ассерты v590 → v591. Сообщения guard-ов подчищаются под
# новую цель (v592). Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v590'"
new = "CACHE_VERSION = 'kipia-test-v591'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v590'
assert 'kipia-test-v591' not in sw, 'sw.js: v591 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v590 -> kipia-test-v591')

# 2. tests/*.js — guard v591→v592, затем ассерты v590→v591
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v591')
    s = s.replace('kipia-test-v591', 'kipia-test-v592')
    n_assert = s.count('kipia-test-v590')
    s = s.replace('kipia-test-v590', 'kipia-test-v591')
    # сообщения guard-ов — под новую цель v592 (косметика)
    s = s.replace('v591 ещё не существует', 'v592 ещё не существует')
    s = s.replace('v590 ещё не существует', 'v592 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v590→v591: %d, guard v591→v592: %d)' % (f, a, g))

# 3. контроль: v592 не существует нигде кроме guard-целей
assert sw.count('kipia-test-v591') == 1
print('OK: единственный kipia-test-v591 в sw.js')
