#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 386: SW-бамп kipia-test-v613 → v614 (index.html менялся —
# кнопка «Обозначения» (два вида шторки + мобильная страница),
# шапка сетки «Работники» (просто надпись), кнопка «Добавить
# работника» на странице «Работники»).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v614 → v615 — ВСЕ guard-ы «отсутствует» (assertFalse/
#   assertTrue/имена тестов/сообщения) переезжают на новую
#   несуществующую v615;
#   ЗАТЕМ v613 → v614 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v613'"
new = "CACHE_VERSION = 'kipia-test-v614'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v613'
assert 'kipia-test-v614' not in sw, 'sw.js: v614 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v613 -> kipia-test-v614')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v614 отсутствует» → «v615 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v614')
    s = s.replace('kipia-test-v614', 'kipia-test-v615')
    # 2) ассерты «v613 присутствует» → «v614 присутствует»
    n_assert = s.count('kipia-test-v613')
    s = s.replace('kipia-test-v613', 'kipia-test-v614')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v613→v614: %d, guard v614→v615: %d)' % (f, a, g))
