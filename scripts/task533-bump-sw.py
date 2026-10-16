#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 533 — бамп SW-версий в тестах kip8test (v745→v746), по образцу
task531-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГАРДЫ 'kipia-test-v746' → 'kipia-test-v747' — во всех файлах
     (в Task 532 гварды v746 уже расставлены);
  2) АССЕРТЫ 'kipia-test-v745' → 'kipia-test-v746' — во всех старых
     файлах;
  3) sw.js: CACHE_VERSION v745 → v746 (менялся index.html — Task 533:
     погода напрямую из браузера, шестерёнка внутри информера,
     календарь год/месяц).
test-task533.js в run-all.js регистрируется вручную ПОСЛЕ бампа
(пишется сразу с ассертами v746 и гвардом v747).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
# тесты, которые уже переписаны вручную под v746 (пока нет таких)
OWN = []

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

print('Шаг 1 — ГАРДЫ v746 → v747 (кроме НОВОГО/адаптированного):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v746', 'kipia-test-v747', 'гард')

print('Шаг 2 — АССЕРТЫ v745 → v746:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v745', 'kipia-test-v746', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v745 → v746:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v745') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v745'",
                    "const CACHE_VERSION = 'kipia-test-v746'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v746')
else:
    print('  ВНИМАНИЕ: kipia-test-v745 в sw.js встречается %d раз — не тронуто'
          % sw.count('kipia-test-v745'))

total = sum(changed.values())
print('Итого замен в тестах: %d (файлов: %d)' % (total, len(changed)))
