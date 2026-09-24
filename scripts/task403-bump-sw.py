#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 403: SW-бамп kipia-test-v629 → v630 (index.html и WorkSchedule.gs
# менялись — строка должности столбца ФИО без группы + «разряд» → «р.»;
# попап без СИЗ; ярлыки «Работников» по самому длинному тексту;
# мероприятия над СИЗ; GAS-фикс бага комментария).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v630 → v631 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v631;
#   ЗАТЕМ v629 → v630 — ассерты «присутствует» едут на текущую.
# tests/test-task403.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v630 + guard v631).
import glob

OWN = 'tests/test-task403.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v629'"
new = "CACHE_VERSION = 'kipia-test-v630'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v629'
assert 'kipia-test-v630' not in sw, 'sw.js: v630 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v629 -> kipia-test-v630')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v630 отсутствует» → «v631 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v630')
    s = s.replace('kipia-test-v630', 'kipia-test-v631')
    # 2) ассерты «v629 присутствует» → «v630 присутствует»
    n_assert = s.count('kipia-test-v629')
    s = s.replace('kipia-test-v629', 'kipia-test-v630')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v629->v630: %d, guard v630->v631: %d)' % (f, a, g))
