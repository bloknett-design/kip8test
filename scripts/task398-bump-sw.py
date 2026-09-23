#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 398: SW-бамп kipia-test-v625 → v626 (index.html менялся —
# универсальное правило [hidden]{display:none!important}: атрибут
# hidden вновь сильнее авторских display-правил; заявка — кнопка
# «Работники» в табеле видна роли КИП ИОС при уровне min).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v626 → v627 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v627;
#   ЗАТЕМ v625 → v626 — ассерты «присутствует» едут на текущую.
# tests/test-task398.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v626 + guard v627).
import glob

OWN = 'tests/test-task398.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v625'"
new = "CACHE_VERSION = 'kipia-test-v626'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v625'
assert 'kipia-test-v626' not in sw, 'sw.js: v626 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v625 -> kipia-test-v626')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v626 отсутствует» → «v627 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v626')
    s = s.replace('kipia-test-v626', 'kipia-test-v627')
    # 2) ассерты «v625 присутствует» → «v626 присутствует»
    n_assert = s.count('kipia-test-v625')
    s = s.replace('kipia-test-v625', 'kipia-test-v626')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v625->v626: %d, guard v626->v627: %d)' % (f, a, g))
