#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408: SW-бамп kipia-test-v634 → v635 (index.html менялся —
# строгий select «Темы», тултипы бейджей, годовые архивы, eventsAll).
# Конвенция прежних бампов (урок Task 407):
#   ШАГ 1: v634 → v635 ВЕЗДЕ (sw.js + ассерты присутствия в тестах);
#   ШАГ 2: guard-ассерты «v635 отсутствует» (поехали с v634 при
#          замене) переносим на v636 — иначе 40+ падений.
# tests/test-task408.js — УЖЕ в пост-бамп форме (assert v635).
import glob
import re

OWN = 'tests/test-task408.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v634'"
new = "CACHE_VERSION = 'kipia-test-v635'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v634'
assert 'kipia-test-v635' not in sw, 'sw.js: v635 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v634 -> kipia-test-v635')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v634' not in s:
        continue
    orig = s
    s = s.replace('kipia-test-v634', 'kipia-test-v635')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append(f)
print('ШАГ 1 (замена v634→v635): файлов %d' % len(changed))

# ШАГ 2: guard-ы «v635 отсутствует» → «v636 отсутствует»
guard_re_absent = re.compile(r"indexOf\((['\"])kipia-test-v635\1\)\s*===\s*-1")
guard_re_false = re.compile(r"assertFalse\([^)]*indexOf\((['\"])kipia-test-v635\1\)\s*!==\s*-1")

fixed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    lines = open(f, encoding='utf-8').read().split('\n')
    n = 0
    for i, line in enumerate(lines):
        if 'kipia-test-v635' not in line:
            continue
        is_guard = False
        if guard_re_absent.search(line) and 'assertFalse' not in line:
            is_guard = True
        if guard_re_false.search(line):
            is_guard = True
        if is_guard:
            lines[i] = line.replace('kipia-test-v635', 'kipia-test-v636')
            n += 1
    if n:
        open(f, 'w', encoding='utf-8').write('\n'.join(lines))
        fixed.append((f, n))
print('ШАГ 2 (guard-ы → v636): файлов %d' % len(fixed))
for f, n in fixed[:10]:
    print('  %s: %d' % (f, n))

# контроль: guard-ов с v635 не осталось
bad = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    for i, line in enumerate(open(f, encoding='utf-8').read().split('\n')):
        if 'kipia-test-v635' not in line:
            continue
        if (guard_re_absent.search(line) and 'assertFalse' not in line) or \
           guard_re_false.search(line):
            bad.append('%s:%d' % (f, i + 1))
print('остаточные guard-ы с v635: %d' % len(bad))
for b in bad[:10]:
    print('  ' + b)
