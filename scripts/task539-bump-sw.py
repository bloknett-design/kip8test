#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 539 — бамп SW-версий в тестах kip8test (v750→v751), по образцу
task536-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГВАРДЫ 'kipia-test-v751' → 'kipia-test-v752' — во всех файлах;
  2) АССЕРТЫ 'kipia-test-v750' → 'kipia-test-v751' — во всех старых
     файлах (test-task539.js исключён: пишется сразу под v751
     с гвардом v752);
  3) sw.js: CACHE_VERSION v750 → v751 (менялся index.html — Task 539:
     табы «Все / Избранное» телефонного справочника: мобильный нижний
     бар #pbBottomBar + десктопные табы #pbDesktopTabs).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task539.js']

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

print('Шаг 1 — ГВАРДЫ v751 → v752 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v751', 'kipia-test-v752', 'гард')

print('Шаг 2 — АССЕРТЫ v750 → v751:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v750', 'kipia-test-v751', 'ассерт')

print('Шаг 3 — sw.js CACHE_VERSION:')
sw = os.path.join(ROOT, 'sw.js')
src = io.open(sw, encoding='utf-8').read()
n = src.count("const CACHE_VERSION = 'kipia-test-v750'")
if n != 1:
    print('  FAIL: CACHE_VERSION v750 найден %d раз' % n)
    raise SystemExit(1)
src = src.replace("const CACHE_VERSION = 'kipia-test-v750'",
                  "const CACHE_VERSION = 'kipia-test-v751'")
io.open(sw, 'w', encoding='utf-8').write(src)
print('  sw.js: CACHE_VERSION v750 → v751')

total = sum(changed.values())
print()
print('Итого: файлов изменено %d, замен %d + sw.js' % (len(changed), total))
