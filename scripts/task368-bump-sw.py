#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 368: SW-бамп kipia-test-v596 → v597 (index.html менялся —
# форма показаний за период двух дат для №3/№11/№9, семантика
# красного/зелёного по ЗАКРЫТЫМ календарным неделям/месяцам,
# подписи-диапазоны на карточках и в хронологии). Порядок замен в
# tests/ ВАЖЕН (урок Task 361): СНАЧАЛА guard-ы «v597 не существует»
# → v598, ЗАТЕМ ассерты v596 → v597. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v596'"
new = "CACHE_VERSION = 'kipia-test-v597'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v596'
assert 'kipia-test-v597' not in sw, 'sw.js: v597 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v596 -> kipia-test-v597')

# 2. tests/*.js — guard v597→v598, затем ассерты v596→v597
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v597')
    s = s.replace('kipia-test-v597', 'kipia-test-v598')
    n_assert = s.count('kipia-test-v596')
    s = s.replace('kipia-test-v596', 'kipia-test-v597')
    # сообщения guard-ов — под новую цель v598 (косметика)
    s = s.replace('v597 ещё не существует', 'v598 ещё не существует')
    s = s.replace('v596 ещё не существует', 'v598 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v596→v597: %d, guard v597→v598: %d)' % (f, a, g))
