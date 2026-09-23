#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 397: SW-бамп kipia-test-v624 → v625 (index.html менялся —
# ОБЩЕЕ ПРАВИЛО: кнопка раздела без доступа не отображается;
# универсальный проход + калькуляторы нижнего бара + композит docs).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v625 → v626 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v626;
#   ЗАТЕМ v624 → v625 — ассерты «присутствует» едут на текущую.
# tests/test-task397.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v625 + guard v626).
import glob

OWN = 'tests/test-task397.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v624'"
new = "CACHE_VERSION = 'kipia-test-v625'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v624'
assert 'kipia-test-v625' not in sw, 'sw.js: v625 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v624 -> kipia-test-v625')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v625 отсутствует» → «v626 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v625')
    s = s.replace('kipia-test-v625', 'kipia-test-v626')
    # 2) ассерты «v624 присутствует» → «v625 присутствует»
    n_assert = s.count('kipia-test-v624')
    s = s.replace('kipia-test-v624', 'kipia-test-v625')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v624->v625: %d, guard v625->v626: %d)' % (f, a, g))
