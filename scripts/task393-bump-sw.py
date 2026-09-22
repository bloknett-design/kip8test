#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 393: SW-бамп kipia-test-v620 → v621 (index.html менялся —
# карточка работника страницы «Работники»: ЧЕТЫРЕ блока-окна
# .ws-wcard + шрифт крупнее; попап шахматки — прежний вид).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v621 → v622 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v622;
#   ЗАТЕМ v620 → v621 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v620'"
new = "CACHE_VERSION = 'kipia-test-v621'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v620'
assert 'kipia-test-v621' not in sw, 'sw.js: v621 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v620 -> kipia-test-v621')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v621 отсутствует» → «v622 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v621')
    s = s.replace('kipia-test-v621', 'kipia-test-v622')
    # 2) ассерты «v620 присутствует» → «v621 присутствует»
    n_assert = s.count('kipia-test-v620')
    s = s.replace('kipia-test-v620', 'kipia-test-v621')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v620->v621: %d, guard v621->v622: %d)' % (f, a, g))
