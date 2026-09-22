#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 391: SW-бамп kipia-test-v618 → v619 (index.html менялся —
# «Общая» вкладка «Работников»: формулировки строк в скобках,
# шрифт крупнее/ярче, кнопка «Добавить работника» акцентная в
# стиле сайта).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v619 → v620 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v620;
#   ЗАТЕМ v618 → v619 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v618'"
new = "CACHE_VERSION = 'kipia-test-v619'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v618'
assert 'kipia-test-v619' not in sw, 'sw.js: v619 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v618 -> kipia-test-v619')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v619 отсутствует» → «v620 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v619')
    s = s.replace('kipia-test-v619', 'kipia-test-v620')
    # 2) ассерты «v618 присутствует» → «v619 присутствует»
    n_assert = s.count('kipia-test-v618')
    s = s.replace('kipia-test-v618', 'kipia-test-v619')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v618→v619: %d, guard v619→v620: %d)' % (f, a, g))
