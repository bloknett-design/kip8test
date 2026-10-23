#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 546 — бамп SW-версии в kip8test (v756→v757), по образцу
task539-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГВАРДЫ 'kipia-test-v757' → 'kipia-test-v758' — во всех файлах,
     КРОМЕ НОВОГО test-task546.js (сразу написан под v757 с
     гвардом v758);
  2) АССЕРТЫ 'kipia-test-v756' → 'kipia-test-v757' — во всех
     старых файлах (test-task546.js исключён);
  3) sw.js: CACHE_VERSION v756 → v757 (index.html менялся: Task 546
     — анимация переворота клетки сапёра с бликом/вибрацией +
     блок «Архив партий»).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task546.js']

changed = {}


def bump(path, old, new, label):
    src = io.open(path, encoding='utf-8').read()
    n = src.count(old)
    if n == 0:
        return
    src = src.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(src)
    changed[os.path.basename(path)] = changed.get(
        os.path.basename(path), 0) + n
    print('  %s: %s ×%d' % (os.path.basename(path), label, n))


tests_dir = os.path.join(ROOT, 'tests')
files = sorted(f for f in os.listdir(tests_dir) if f.endswith('.js'))

print('Шаг 1 — ГВАРДЫ v757 → v758 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v757', 'kipia-test-v758', 'гард')

print('Шаг 2 — АССЕРТЫ v756 → v757:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v756', 'kipia-test-v757', 'ассерт')

print('Шаг 3 — sw.js CACHE_VERSION:')
sw = os.path.join(ROOT, 'sw.js')
src = io.open(sw, encoding='utf-8').read()
n = src.count("const CACHE_VERSION = 'kipia-test-v756'")
if n != 1:
    print('  FAIL: CACHE_VERSION v756 найден %d раз' % n)
    raise SystemExit(1)
src = src.replace("const CACHE_VERSION = 'kipia-test-v756'",
                  "const CACHE_VERSION = 'kipia-test-v757'")
io.open(sw, 'w', encoding='utf-8').write(src)
print('  sw.js: CACHE_VERSION → kipia-test-v757')

total = sum(changed.values()) + 1
print('ИТОГО замен: %d в %d файлах' % (total, len(changed) + 1))
