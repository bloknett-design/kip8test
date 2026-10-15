#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 531 — бамп SW-версий в тестах kip8test (v743→v744), по образцу
task530-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГАРДЫ 'kipia-test-v744' → 'kipia-test-v745' — во всех файлах,
     КРОМЕ test-task531.js и test-task530.js (в них v744 — ТЕКУЩАЯ
     версия Task 531);
  2) АССЕРТЫ 'kipia-test-v743' → 'kipia-test-v744' — во всех старых
     файлах (кроме test-task531.js/530.js — уже переписаны вручную);
  3) sw.js: CACHE_VERSION v743 → v744 (менялся index.html — Task 531).
test-task531.js в run-all.js уже зарегистрирован вручную.
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task531.js', 'test-task530.js']

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

print('Шаг 1 — ГАРДЫ v744 → v745 (кроме НОВОГО/адаптированного):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v744', 'kipia-test-v745', 'гард')

print('Шаг 2 — АССЕРТЫ v743 → v744:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v743', 'kipia-test-v744', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v743 → v744:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v743') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v743'",
                    "const CACHE_VERSION = 'kipia-test-v744'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v744')
else:
    print('  ВНИМАНИЕ: kipia-test-v743 в sw.js встречается %d раз — не тронуто'
          % sw.count('kipia-test-v743'))

total = sum(changed.values())
print('Итого замен в тестах: %d (файлов: %d)' % (total, len(changed)))
