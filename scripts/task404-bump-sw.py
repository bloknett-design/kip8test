#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 404: SW-бамп kipia-test-v630 → v631 (index.html менялся — три
# колонки карточки (СИЗ слева от мероприятий), кнопки ✎/✕ рядом,
# окно мероприятий без отпусков).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v631 → v632 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v632;
#   ЗАТЕМ v630 → v631 — ассерты «присутствует» едут на текущую.
# tests/test-task404.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v631 + guard v632).
import glob

OWN = 'tests/test-task404.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v630'"
new = "CACHE_VERSION = 'kipia-test-v631'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v630'
assert 'kipia-test-v631' not in sw, 'sw.js: v631 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v630 -> kipia-test-v631')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v631 отсутствует» → «v632 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v631')
    s = s.replace('kipia-test-v631', 'kipia-test-v632')
    # 2) ассерты «v630 присутствует» → «v631 присутствует»
    n_assert = s.count('kipia-test-v630')
    s = s.replace('kipia-test-v630', 'kipia-test-v631')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v630->v631: %d, guard v631->v632: %d)' % (f, a, g))
