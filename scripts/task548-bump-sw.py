#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 548 — бамп SW-версии в kip8test (v758→v759), по образцу
task547-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГВАРДЫ 'kipia-test-v759' → 'kipia-test-v760' — во всех файлах,
     КРОМЕ НОВОГО test-task548.js (SW-ассертов в нём нет —
     PWA-специфика не проверяется, тест репо-агностичен);
  2) АССЕРТЫ 'kipia-test-v758' → 'kipia-test-v759' — во всех
     старых файлах (test-task548.js исключён);
  3) sw.js: CACHE_VERSION v758 → v759 (index.html менялся: Task 548
     — табель: кнопка «Очистить правки» — сброс ручных правок
     месяца к авто-состоянию, подмены расставляются заново).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task548.js']

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

print('Шаг 1 — ГВАРДЫ v759 → v760 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v759', 'kipia-test-v760', 'гард')

print('Шаг 2 — АССЕРТЫ v758 → v759:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v758', 'kipia-test-v759', 'ассерт')

print('Шаг 3 — sw.js CACHE_VERSION:')
sw = os.path.join(ROOT, 'sw.js')
src = io.open(sw, encoding='utf-8').read()
n = src.count("const CACHE_VERSION = 'kipia-test-v758'")
if n != 1:
    print('  FAIL: CACHE_VERSION v758 найден %d раз' % n)
    raise SystemExit(1)
src = src.replace("const CACHE_VERSION = 'kipia-test-v758'",
                  "const CACHE_VERSION = 'kipia-test-v759'")
io.open(sw, 'w', encoding='utf-8').write(src)
print('  sw.js: CACHE_VERSION → kipia-test-v759')

total = sum(changed.values()) + 1
print('ИТОГО замен: %d в %d файлах' % (total, len(changed) + 1))
