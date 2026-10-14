#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 522 — бамп SW-версий в тестах kip8test (v734→v735) + регистрация
нового теста (по образцу task521-bump-sw.py):
  1) ГАРДЫ 'kipia-test-v735' → 'kipia-test-v736' — во всех файлах,
     КРОМЕ нового test-task522.js (его v735 — актуальный ассерт,
     v736 — его собственный гвард);
  2) АССЕРТЫ 'kipia-test-v734' → 'kipia-test-v735' — во всех старых
     файлах;
  3) sw.js: CACHE_VERSION v734 → v735 (менялся index.html);
  4) регистрация test-task522.js в tests/run-all.js ПОСЛЕ бампа.
"""
import io
import os
import sys

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task522.js']

fails = []
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

print('Шаг 1 — ГАРДЫ v735 → v736 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v735', 'kipia-test-v736', 'гард')

print('Шаг 2 — АССЕРТЫ v734 → v735:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v734', 'kipia-test-v735', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v734 → v735:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v734') != 1:
    fails.append('sw.js: упоминаний v734 = %d (ожидалось 1)' % sw.count('kipia-test-v734'))
else:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v734'",
                    "const CACHE_VERSION = 'kipia-test-v735'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v735')

print('Шаг 4 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task522.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task521.js');" in src:
    anchor = "require('./test-task521.js');\n"
    add = ("// Task 522: Табель — окно ячейки: секция «Статус дня» — справка\n"
           "// по коду «д»/«н» дневного персонала + «Время работы: N ч» из\n"
           "// колонки K; ховер открывает окно и без мероприятий. SW v735.\n"
           "require('./test-task522.js');\n")
    src = src.replace(anchor, anchor + add, 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  зарегистрирован после test-task521.js')
else:
    fails.append('run-all.js: якорь test-task521 не найден')

# санитарная сверка
sw = io.open(sw_path, encoding='utf-8').read()
if 'kipia-test-v736' in sw:
    fails.append('sw.js содержит v736 (двойной бамп)')
if 'kipia-test-v734' in sw:
    fails.append('sw.js содержит v734 после бампа')

print()
print('Итого замен в тестах: %d в %d файлах' % (sum(changed.values()), len(changed)))
if fails:
    print('ПРОВАЛЕНО: %d' % len(fails))
    for f in fails:
        print(' - ' + f)
    sys.exit(1)
print('БУМП ЗАВЕРШЁН')
