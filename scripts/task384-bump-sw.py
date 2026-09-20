#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 384: SW-бамп kipia-test-v611 → v612 (index.html менялся —
# карточка сотрудника стала центром правки: «Правка данных…»,
# ✎/✕ у отпусков, «+ Мероприятие…»; шторки в режимах правки;
# серверные справочники updateEmployee/updateVacation).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v612 → v613 — ВСЕ guard-ы «отсутствует» (assertFalse/
#   assertTrue/имена тестов/сообщения) переезжают на новую
#   несуществующую v613;
#   ЗАТЕМ v611 → v612 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v611'"
new = "CACHE_VERSION = 'kipia-test-v612'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v611'
assert 'kipia-test-v612' not in sw, 'sw.js: v612 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v611 -> kipia-test-v612')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v612 отсутствует» → «v613 отсутствует» (все формы:
    #    assertFalse/assertTrue/имена тестов/тексты сообщений)
    n_guard = s.count('kipia-test-v612')
    s = s.replace('kipia-test-v612', 'kipia-test-v613')
    # 2) ассерты «v611 присутствует» → «v612 присутствует»
    n_assert = s.count('kipia-test-v611')
    s = s.replace('kipia-test-v611', 'kipia-test-v612')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v611→v612: %d, guard v612→v613: %d)' % (f, a, g))
