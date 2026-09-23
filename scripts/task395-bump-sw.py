#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 395: SW-бамп kipia-test-v622 → v623 (index.html менялся —
# кнопка «Работники» по матрице доступа, фон/рамки блоков карточек,
# десктоп-колонки: отпуска под профилем, мероприятия под отпусками,
# СИЗ в верхней правой части).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v623 → v624 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v624;
#   ЗАТЕМ v622 → v623 — ассерты «присутствует» едут на текущую.
# tests/test-task395.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v623 + guard v624).
import glob

OWN = 'tests/test-task395.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v622'"
new = "CACHE_VERSION = 'kipia-test-v623'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v622'
assert 'kipia-test-v623' not in sw, 'sw.js: v623 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v622 -> kipia-test-v623')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v623 отсутствует» → «v624 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v623')
    s = s.replace('kipia-test-v623', 'kipia-test-v624')
    # 2) ассерты «v622 присутствует» → «v623 присутствует»
    n_assert = s.count('kipia-test-v622')
    s = s.replace('kipia-test-v622', 'kipia-test-v623')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v622->v623: %d, guard v623->v624: %d)' % (f, a, g))
