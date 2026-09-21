#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 385: SW-бамп kipia-test-v612 → v613 (index.html менялся —
# шторка «Легенда» сокращений, переименование «сотрудник»→«работник»,
# страница «Работники» с полными карточками, карточка шахматки
# read-only).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v613 → v614 — ВСЕ guard-ы «отсутствует» (assertFalse/
#   assertTrue/имена тестов/сообщения) переезжают на новую
#   несуществующую v614;
#   ЗАТЕМ v612 → v613 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v612'"
new = "CACHE_VERSION = 'kipia-test-v613'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v612'
assert 'kipia-test-v613' not in sw, 'sw.js: v613 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v612 -> kipia-test-v613')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v613 отсутствует» → «v614 отсутствует» (все формы:
    #    assertFalse/assertTrue/имена тестов/тексты сообщений)
    n_guard = s.count('kipia-test-v613')
    s = s.replace('kipia-test-v613', 'kipia-test-v614')
    # 2) ассерты «v612 присутствует» → «v613 присутствует»
    n_assert = s.count('kipia-test-v612')
    s = s.replace('kipia-test-v612', 'kipia-test-v613')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v612→v613: %d, guard v613→v614: %d)' % (f, a, g))
