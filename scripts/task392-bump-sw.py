#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 392: SW-бамп kipia-test-v619 → v620 (index.html менялся —
# строка текущего момента без скобок вокруг числа + раздел «СИЗ»:
# лист «СИЗ» табель_КИП_ИОС, секция в карточке работника, шторка
# формы, сервер listPpe/addPpe/updatePpe/deletePpe).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v620 → v621 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v621;
#   ЗАТЕМ v619 → v620 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v619'"
new = "CACHE_VERSION = 'kipia-test-v620'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v619'
assert 'kipia-test-v620' not in sw, 'sw.js: v620 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v619 -> kipia-test-v620')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v620 отсутствует» → «v621 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v620')
    s = s.replace('kipia-test-v620', 'kipia-test-v621')
    # 2) ассерты «v619 присутствует» → «v620 присутствует»
    n_assert = s.count('kipia-test-v619')
    s = s.replace('kipia-test-v619', 'kipia-test-v620')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v619→v620: %d, guard v620→v621: %d)' % (f, a, g))
