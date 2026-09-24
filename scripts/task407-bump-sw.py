#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 407: SW-бамп kipia-test-v633 → v634 (index.html менялся — блок
# инструктажей по шаблону «Список_И_и_ПЗ»: группы, «след. срок»,
# «вне списка», datalist «Темы»; GAS — instrList/instrAll).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v633 → v634 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v634;
#   ЗАТЕМ v632-следы не ждём — ассерты «присутствует» едут на текущую.
# tests/test-task407.js — УЖЕ в пост-бамп форме (assert v634).
import glob

OWN = 'tests/test-task407.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v633'"
new = "CACHE_VERSION = 'kipia-test-v634'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v633'
assert 'kipia-test-v634' not in sw, 'sw.js: v634 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v633 -> kipia-test-v634')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v633 отсутствует» → «v634 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v633')
    s = s.replace('kipia-test-v633', 'kipia-test-v634')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, n in changed:
    print('  %s: %d guard-замен' % (f, n))
