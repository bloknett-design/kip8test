#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 523 — бамп SW-версий в тестах kip8test (v735→v736) + регистрация
нового теста (по образцу task522-bump-sw.py):
  1) ГАРДЫ 'kipia-test-v736' → 'kipia-test-v737' — во всех файлах,
     КРОМЕ нового test-task523.js (гварды «двойного бампа нет» в
     старых файлах смотрят на одну версию ВПЕРЁД — двигаются ПЕРВЫМИ,
     до АССЕРТОВ, иначе ассерты уже-bumped попадут под гвард);
  2) АССЕРТЫ 'kipia-test-v735' → 'kipia-test-v736' — во всех старых
     файлах;
  3) sw.js: CACHE_VERSION v735 → v736 (менялся index.html);
  4) регистрация test-task523.js в tests/run-all.js.
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task523.js']

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

print('Шаг 1 — ГАРДЫ v736 → v737 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v736', 'kipia-test-v737', 'гард')

print('Шаг 2 — АССЕРТЫ v735 → v736:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v735', 'kipia-test-v736', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v735 → v736:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v735') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v735'",
                    "const CACHE_VERSION = 'kipia-test-v736'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v736')
elif sw.count('kipia-test-v736') == 1:
    print('  sw.js: уже kipia-test-v736 (пропуск)')
else:
    raise SystemExit('sw.js: неожиданное состояние версий')

print('Шаг 4 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task523.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task522.js');" in src:
    anchor = "require('./test-task522.js');\n"
    add = ("// Task 523: Табель — времена начала/окончания работ д/н дневного\n"
           "// персонала СОХРАНЯЮТСЯ в колонках L/M «Записи_графика» (K — часы\n"
           "// пересчитываются из пары на сервере); префилл формы — точной парой;\n"
           "// попап: «Время работы: 07:30–15:30 · 7,2 ч»; «н» = «д». SW v736.\n")
    src = src.replace(anchor, anchor + add +
                      "require('./test-task523.js');\n", 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  зарегистрирован после test-task522.js')
else:
    raise SystemExit('run-all.js: якорь test-task522 не найден')

total = sum(changed.values())
print('ИТОГО замен в тестах: %d' % total)
