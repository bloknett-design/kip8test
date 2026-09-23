#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 396: SW-бамп kipia-test-v623 → v624 (index.html менялся —
# зебра строк блоков карточки, компактные кнопки действий в
# верхнем правом углу шапок блоков, оглавления блоков крупнее/
# ярче + выделены другим фоном).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v624 → v625 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v625;
#   ЗАТЕМ v623 → v624 — ассерты «присутствует» едут на текущую.
# tests/test-task396.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v624 + guard v625).
import glob

OWN = 'tests/test-task396.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v623'"
new = "CACHE_VERSION = 'kipia-test-v624'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v623'
assert 'kipia-test-v624' not in sw, 'sw.js: v624 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v623 -> kipia-test-v624')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v624 отсутствует» → «v625 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v624')
    s = s.replace('kipia-test-v624', 'kipia-test-v625')
    # 2) ассерты «v623 присутствует» → «v624 присутствует»
    n_assert = s.count('kipia-test-v623')
    s = s.replace('kipia-test-v623', 'kipia-test-v624')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v623->v624: %d, guard v624->v625: %d)' % (f, a, g))
