#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 521 — бамп SW-версий в тестах kip8test (v733→v734) + регистрация
нового теста (по образцу task520-bump-sw.py):
  1) ГАРДЫ 'kipia-test-v734' → 'kipia-test-v735' — во всех файлах,
     КРОМЕ нового test-task521.js (его v734 — актуальный ассерт,
     v735 — его собственный гвард);
  2) АССЕРТЫ 'kipia-test-v733' → 'kipia-test-v734' — во всех старых
     файлах;
  3) sw.js: CACHE_VERSION v733 → v734 (менялся index.html);
  4) регистрация test-task521.js в tests/run-all.js ПОСЛЕ бампа.
"""
import io
import os
import sys

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task521.js']

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

print('Шаг 1 — ГАРДЫ v734 → v735 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v734', 'kipia-test-v735', 'гард')

print('Шаг 2 — АССЕРТЫ v733 → v734:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v733', 'kipia-test-v734', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v733 → v734:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v733') != 1:
    fails.append('sw.js: упоминаний v733 = %d (ожидалось 1)' % sw.count('kipia-test-v733'))
else:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v733'",
                    "const CACHE_VERSION = 'kipia-test-v734'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v734')

print('Шаг 4 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task521.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task520.js');" in src:
    anchor = "require('./test-task520.js');\n"
    add = ("// Task 521: малая форма д/н Табеля — поля «Время начала/"
           "окончания работ» (type=time) вместо ручного ввода часов;\n"
           "// часы переработки считаются автоматически (полночь +24 ч,"
           " живая строка расчёта). SW v734.\n"
           "require('./test-task521.js');\n")
    src = src.replace(anchor, anchor + add, 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  зарегистрирован после test-task520.js')
else:
    fails.append('run-all.js: якорь test-task520 не найден')

# санитарная сверка
sw = io.open(sw_path, encoding='utf-8').read()
if 'kipia-test-v735' in sw:
    fails.append('sw.js содержит v735 (двойной бамп)')
if 'kipia-test-v733' in sw:
    fails.append('sw.js содержит v733 после бампа')

print()
print('Итого замен в тестах: %d в %d файлах' % (sum(changed.values()), len(changed)))
if fails:
    print('ПРОВАЛЕНО: %d' % len(fails))
    for f in fails:
        print(' - ' + f)
    sys.exit(1)
print('БУМП ЗАВЕРШЁН')
