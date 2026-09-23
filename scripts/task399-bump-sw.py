#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 399: SW-бамп kipia-test-v626 → v627 (index.html менялся —
# окно мероприятий табеля у уровня «min» больше не показывает
# записи мастеров «Мастер КИПиА»: мероприятия/отпуска/СИЗ
# фильтруются признаком _isMasterKipia, как строки сетки Task 340).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v627 → v628 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v628;
#   ЗАТЕМ v626 → v627 — ассерты «присутствует» едут на текущую.
# tests/test-task399.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v627 + guard v628).
import glob

OWN = 'tests/test-task399.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v626'"
new = "CACHE_VERSION = 'kipia-test-v627'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v626'
assert 'kipia-test-v627' not in sw, 'sw.js: v627 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v626 -> kipia-test-v627')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v627 отсутствует» → «v628 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v627')
    s = s.replace('kipia-test-v627', 'kipia-test-v628')
    # 2) ассерты «v626 присутствует» → «v627 присутствует»
    n_assert = s.count('kipia-test-v626')
    s = s.replace('kipia-test-v626', 'kipia-test-v627')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v626->v627: %d, guard v627->v628: %d)' % (f, a, g))
