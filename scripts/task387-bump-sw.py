#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 387: SW-бамп kipia-test-v614 → v615 (index.html менялся —
# панель «Обозначения» до 500px, канон/нормализация справочника
# кодов в списках выбора, пояснения легенды, «Выходной» без
# кода-точки).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v615 → v616 — ВСЕ guard-ы «отсутствует» (assertFalse/
#   assertTrue/имена тестов/сообщения) переезжают на новую
#   несуществующую v616;
#   ЗАТЕМ v614 → v615 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v614'"
new = "CACHE_VERSION = 'kipia-test-v615'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v614'
assert 'kipia-test-v615' not in sw, 'sw.js: v615 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v614 -> kipia-test-v615')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v615 отсутствует» → «v616 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v615')
    s = s.replace('kipia-test-v615', 'kipia-test-v616')
    # 2) ассерты «v614 присутствует» → «v615 присутствует»
    n_assert = s.count('kipia-test-v614')
    s = s.replace('kipia-test-v614', 'kipia-test-v615')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v614→v615: %d, guard v615→v616: %d)' % (f, a, g))
