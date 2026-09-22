#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 394: SW-бамп kipia-test-v621 → v622 (index.html менялся —
# сетка 2×2 карточки работника на весь экран, мероприятия за год
# в карточках, секции «Отпуска»/«СИЗ» в окне мероприятий месяца).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v622 → v623 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v623;
#   ЗАТЕМ v621 → v622 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v621'"
new = "CACHE_VERSION = 'kipia-test-v622'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v621'
assert 'kipia-test-v622' not in sw, 'sw.js: v622 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v621 -> kipia-test-v622')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v622 отсутствует» → «v623 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v622')
    s = s.replace('kipia-test-v622', 'kipia-test-v623')
    # 2) ассерты «v621 присутствует» → «v622 присутствует»
    n_assert = s.count('kipia-test-v621')
    s = s.replace('kipia-test-v621', 'kipia-test-v622')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v621->v622: %d, guard v622->v623: %d)' % (f, a, g))
