#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 401: SW-бамп kipia-test-v627 → v628 (index.html менялся —
# десктопная шторка итогов «Год» раскрывается НА ВСЮ ШИРИНУ правее
# колонки ФИО (полностью закрывает шахматку); в шапке годовой таблицы
# — подстрока-пояснение «дней/часов»; три итоговых столбца — фон
# другого оттенка + разделитель 2px как левый край окна итогов).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v628 → v629 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v629;
#   ЗАТЕМ v627 → v628 — ассерты «присутствует» едут на текущую.
# tests/test-task401.js — ИСКЛЮЧЁН: его SW-тест уже в канонической
# пост-бамп форме (assert v628 + guard v629).
import glob

OWN = 'tests/test-task401.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v627'"
new = "CACHE_VERSION = 'kipia-test-v628'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v627'
assert 'kipia-test-v628' not in sw, 'sw.js: v628 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v627 -> kipia-test-v628')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v628 отсутствует» → «v629 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v628')
    s = s.replace('kipia-test-v628', 'kipia-test-v629')
    # 2) ассерты «v627 присутствует» → «v628 присутствует»
    n_assert = s.count('kipia-test-v627')
    s = s.replace('kipia-test-v627', 'kipia-test-v628')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v627->v628: %d, guard v628->v629: %d)' % (f, a, g))
