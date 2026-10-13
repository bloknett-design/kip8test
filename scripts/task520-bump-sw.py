#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 520 — бамп SW-версий в тестах kip8test (v732→v733) + регистрация
нового теста (по образцу task518-bump-sw.py):
  1) ГАРДЫ 'kipia-test-v733' → 'kipia-test-v734' — во всех файлах,
     КРОМЕ нового test-task520.js (его v733 — актуальный ассерт,
     v734 — его собственный гвард);
  2) АССЕРТЫ 'kipia-test-v732' → 'kipia-test-v733' — во всех старых
     файлах;
  3) sw.js: CACHE_VERSION v732 → v733 (менялся index.html);
  4) регистрация test-task520.js в tests/run-all.js ПОСЛЕ бампа.
"""
import io
import os
import sys

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task520.js']

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

print('Шаг 1 — ГАРДЫ v733 → v734 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v733', 'kipia-test-v734', 'гард')

print('Шаг 2 — АССЕРТЫ v732 → v733:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v732', 'kipia-test-v733', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v732 → v733:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v732') != 1:
    fails.append('sw.js: упоминаний v732 = %d (ожидалось 1)' % sw.count('kipia-test-v732'))
else:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v732'",
                    "const CACHE_VERSION = 'kipia-test-v733'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v733')

print('Шаг 4 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task520.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task518.js');" in src:
    anchor = "require('./test-task518.js');\n"
    add = ("// Task 520: окно мероприятий Табеля — формат строки СИЗ\n"
           "// месяца упрощён (наименование · ФИО, без «до дд.мм» и «СИЗ · »)\n"
           "// + НОВАЯ группа «Просроченная выдача СИЗ за всё время»\n"
           "// (мм.гггг красным, сортировка по фамилиям). SW v733.\n"
           "require('./test-task520.js');\n")
    src = src.replace(anchor, anchor + add, 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  зарегистрирован после test-task518.js')
else:
    fails.append('run-all.js: якорь test-task518 не найден')

# санитарная сверка
sw = io.open(sw_path, encoding='utf-8').read()
if 'kipia-test-v734' in sw:
    fails.append('sw.js содержит v734 (двойной бамп)')
if 'kipia-test-v732' in sw:
    fails.append('sw.js содержит v732 после бампа')

print()
print('Итого замен в тестах: %d в %d файлах' % (sum(changed.values()), len(changed)))
if fails:
    print('ПРОВАЛЕНО: %d' % len(fails))
    for f in fails:
        print(' - ' + f)
    sys.exit(1)
print('БУМП ЗАВЕРШЁН')
