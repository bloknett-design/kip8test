#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 494 — бамп SW-версий в тестах kip8test.

Порядок (по прецеденту task493-bump-sw.py):
  1) guards: kipia-test-v718 → kipia-test-v719 (assertFalse «следующей нет»)
  2) asserts: kipia-test-v717 → kipia-test-v718 (assertTrue «текущая»)
Порядок важен: сначала v718→v719, потом v717→v718 — иначе v718-ассерты
попали бы под первый проход повторно.

OWN (tests/test-task494.js) исключён — написан сразу под финальные
v718-ассерты / v719-guard.
"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, 'tests')
OWN = 'test-task494.js'

def replace_in(path, old, new):
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    n = src.count(old)
    if n == 0:
        return True
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(src.replace(old, new))
    print('OK   %s: %d × %s → %s' % (os.path.basename(path), n, old, new))
    return True

ok = True
total_g, total_a = 0, 0
files = sorted(f for f in os.listdir(TESTS)
               if f.endswith('.js') and f != OWN)
# --- 1) guards v718 → v719 ---
for fn in files:
    p = os.path.join(TESTS, fn)
    with io.open(p, encoding='utf-8') as f:
        src = f.read()
    g = src.count('kipia-test-v718')
    total_g += g
    if g:
        replace_in(p, 'kipia-test-v718', 'kipia-test-v719')
# --- 2) asserts v717 → v718 ---
for fn in files:
    p = os.path.join(TESTS, fn)
    with io.open(p, encoding='utf-8') as f:
        src = f.read()
    a = src.count('kipia-test-v717')
    total_a += a
    if a:
        replace_in(p, 'kipia-test-v717', 'kipia-test-v718')
print('GUARDS v718→v719: %d, ASSERTS v717→v718: %d (OWN %s исключён)'
      % (total_g, total_a, OWN))
sys.exit(0)
