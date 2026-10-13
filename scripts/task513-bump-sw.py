#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 513 — бамп SW-версий в тестах kip8test (v730→v731) + регистрация
нового теста (по образцу task508-bump-sw.py):
  1) ГАРДЫ 'kipia-test-v731' → 'kipia-test-v732' — во всех файлах,
     КРОМЕ нового test-task513.js (его v731 — актуальный ассерт,
     v732 — его собственный гард);
  2) АССЕРТЫ 'kipia-test-v730' → 'kipia-test-v731' — во всех старых
     файлах;
  3) sw.js: CACHE_VERSION v730 → v731 (менялся index.html);
  4) регистрация test-task513.js в tests/run-all.js ПОСЛЕ бампа.
"""
import io
import os
import sys

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task513.js']

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

print('Шаг 1 — ГАРДЫ v731 → v732 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v731', 'kipia-test-v732', 'гард')

print('Шаг 2 — АССЕРТЫ v730 → v731:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v730', 'kipia-test-v731', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v730 → v731:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v730') != 1:
    fails.append('sw.js: упоминаний v730 = %d (ожидалось 1)' % sw.count('kipia-test-v730'))
else:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v730'",
                    "const CACHE_VERSION = 'kipia-test-v731'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v731')

print('Шаг 4 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task513.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task508.js');" in src:
    anchor = "require('./test-task508.js');\n"
    add = ("// Task 513: уборка мёртвого кода (аудит Task 512):\n"
           "// удалены остатки удалённых фич, опасный GAS-дубликат\n"
           "// setupTriggers из Utils.gs и 8 мёртвых backend-функций.\n"
           "// SW v731.\n"
           "require('./test-task513.js');\n")
    src = src.replace(anchor, anchor + add, 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  зарегистрирован после test-task508.js')
else:
    fails.append('run-all.js: якорь test-task508 не найден')

# санитарная сверка
sw = io.open(sw_path, encoding='utf-8').read()
if 'kipia-test-v732' in sw:
    fails.append('sw.js содержит v732 (двойной бамп)')
if 'kipia-test-v730' in sw:
    fails.append('sw.js содержит v730 после бампа')

print()
print('Итого замен в тестах: %d в %d файлах' % (sum(changed.values()), len(changed)))
if fails:
    print('ПРОВАЛЕНО: %d' % len(fails))
    for f in fails:
        print(' - ' + f)
    sys.exit(1)
print('БУМП ЗАВЕРШЁН')
