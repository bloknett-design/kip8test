#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 405: SW-бамп kipia-test-v631 → v632 (index.html менялся —
# разделение таблицы инструктажей: блок «Мероприятия» = новая
# таблица, новый блок «Повторные инструктажи и периодическая
# проверка знаний», колонка сводки).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v632 → v633 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v633;
#   ЗАТЕМ v631 → v632 — ассерты «присутствует» едут на текущую.
# tests/test-task405.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v632 + guard v633).
import glob

OWN = 'tests/test-task405.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v631'"
new = "CACHE_VERSION = 'kipia-test-v632'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v631'
assert 'kipia-test-v632' not in sw, 'sw.js: v632 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v631 -> kipia-test-v632')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v632 отсутствует» → «v633 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v632')
    s = s.replace('kipia-test-v632', 'kipia-test-v633')
    # 2) ассерты «v631 присутствует» → «v632 присутствует»
    n_assert = s.count('kipia-test-v631')
    s = s.replace('kipia-test-v631', 'kipia-test-v632')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v631->v632: %d, guard v632->v633: %d)' % (f, a, g))
