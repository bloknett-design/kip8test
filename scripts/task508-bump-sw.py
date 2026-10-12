#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 508 — бамп SW-версий в тестах kip8test (v729→v730) + регистрация
нового теста:
  1) ГАРДЫ 'kipia-test-v730' → 'kipia-test-v731' — ВО ВСЕХ файлах,
     КРОМЕ нового test-task508.js (его v730 — актуальный ассерт,
     v731 — его собственный гард);
  2) АССЕРТЫ 'kipia-test-v729' → 'kipia-test-v730' — во всех старых
     файлах;
  3) регистрация test-task508.js в tests/run-all.js ПОСЛЕ бампа
     (урок Task 481).
"""
import io
import os
import sys

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task508.js']

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

print('Шаг 1 — ГАРДЫ v730 → v731 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v730', 'kipia-test-v731', 'гард')

print('Шаг 2 — АССЕРТЫ v729 → v730:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v729', 'kipia-test-v730', 'ассерт')

print('Шаг 3 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task508.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task506.js');" in src:
    anchor = "require('./test-task506.js');\n"
    add = ("// Task 508: «Кабельный журнал» — архив правок/удалений:\n"
           "// сервер помечает удалённые записи («Удалён», кем, когда;\n"
           "// последний редактор), клиент: печать/PDF без архива,\n"
           "// Excel — с блоком «Архив». SW v730.\n"
           "require('./test-task508.js');\n")
    src = src.replace(anchor, anchor + add, 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  зарегистрирован после test-task506.js')
else:
    fails.append('run-all.js: якорь test-task506 не найден')

# санитарная сверка: в sw.js нет v731, в тестах нет v729 (кроме истории)
sw = io.open(os.path.join(ROOT, 'sw.js'), encoding='utf-8').read()
if 'kipia-test-v731' in sw:
    fails.append('sw.js содержит v731 (двойной бамп)')

print()
print('Итого замен: %d в %d файлах' % (sum(changed.values()), len(changed)))
if fails:
    print('ПРОВАЛЕНО: %d' % len(fails))
    for f in fails:
        print(' - ' + f)
    sys.exit(1)
print('БУМП ЗАВЕРШЁН')
