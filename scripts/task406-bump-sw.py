#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 406: SW-бамп kipia-test-v632 → v633 (index.html менялся —
# раскладка карточки: мероприятия — под отпусками, СИЗ ↔ инструктажи).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v633 → v634 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v634;
#   ЗАТЕМ v632 → v633 — ассерты «присутствует» едут на текущую.
# tests/test-task406.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v633 + guard v634).
import glob

OWN = 'tests/test-task406.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v632'"
new = "CACHE_VERSION = 'kipia-test-v633'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v632'
assert 'kipia-test-v633' not in sw, 'sw.js: v633 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v632 -> kipia-test-v633')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v633 отсутствует» → «v634 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v633')
    s = s.replace('kipia-test-v633', 'kipia-test-v634')
    # 2) ассерты «v632 присутствует» → «v633 присутствует»
    n_assert = s.count('kipia-test-v632')
    s = s.replace('kipia-test-v632', 'kipia-test-v633')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v632->v633: %d, guard v633->v634: %d)' % (f, a, g))
