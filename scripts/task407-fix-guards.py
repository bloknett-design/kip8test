#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ФИКС бампа Task 407: бамп-скрипт заменил v633→v634 ВЕЗДЕ, но
# guard-ассерты «v634 отсутствует» (guard следующей несуществующей
# версии) должны уехать на v635. Правило: строка с v634 — guard,
# если это assertTrue(... === -1) или assertFalse(... !== -1).
# Ассерты присутствия (assertTrue ... !== -1) остаются на v634.
import glob
import re

guard_re_absent = re.compile(r"indexOf\((['\"])kipia-test-v634\1\)\s*===\s*-1")
guard_re_false = re.compile(r"assertFalse\([^)]*indexOf\((['\"])kipia-test-v634\1\)\s*!==\s*-1")

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == 'tests/test-task407.js':
        continue  # наш SW-тест уже в пост-бамп форме (v634 присутствует)
    lines = open(f, encoding='utf-8').read().split('\n')
    n = 0
    for i, line in enumerate(lines):
        if 'kipia-test-v634' not in line:
            continue
        is_guard = False
        if guard_re_absent.search(line) and 'assertFalse' not in line:
            is_guard = True
        if guard_re_false.search(line):
            is_guard = True
        if is_guard:
            lines[i] = line.replace('kipia-test-v634', 'kipia-test-v635')
            n += 1
    if n:
        open(f, 'w', encoding='utf-8').write('\n'.join(lines))
        changed.append((f, n))

print('guard-фикс: файлов %d' % len(changed))
for f, n in changed:
    print('  %s: %d' % (f, n))

# контроль: после фикса ни одной guard-строки с v634 не осталось
bad = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == 'tests/test-task407.js':
        continue
    for i, line in enumerate(open(f, encoding='utf-8').read().split('\n')):
        if 'kipia-test-v634' not in line:
            continue
        if (guard_re_absent.search(line) and 'assertFalse' not in line) or \
           guard_re_false.search(line):
            bad.append('%s:%d' % (f, i + 1))
print('остаточные guard-ы с v634: %d' % len(bad))
for b in bad[:10]:
    print('  ' + b)
