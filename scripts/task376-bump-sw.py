#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 376: SW-бамп kipia-test-v604 → v605 (index.html и .gs менялись —
# честный ответ archive_write_failed + дедуп флаша по архиву).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v605 → v606
# (чтобы старые guards смотрели на новую несуществующую версию),
# ЗАТЕМ ассерты v604 → v605.
# NOTE: test-task376.js пишется ДО этого скрипта? — нет, ПОСЛЕ:
# его guard v606 должен остаться актуальным, а ассерты v605 — появиться.
# Поэтому скрипт запускается ДО записи финального test-task376.js…
# на практике: test-task376.js уже содержит v605/v606 — замены ниже его
# НЕ тронут (v605 как ассерт уже есть, guard v606 уже стоит).
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v604'"
new = "CACHE_VERSION = 'kipia-test-v605'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v604'
assert 'kipia-test-v605' not in sw, 'sw.js: v605 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v604 -> kipia-test-v605')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v605')
    s = s.replace('kipia-test-v605', 'kipia-test-v606')
    n_assert = s.count('kipia-test-v604')
    s = s.replace('kipia-test-v604', 'kipia-test-v605')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v604→v605: %d, guard v605→v606: %d)' % (f, a, g))
