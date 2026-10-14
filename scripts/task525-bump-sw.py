#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 525 — бамп SW-версий в тестах kip8test (v737→v738) + регистрация
нового теста (по образцу task524-bump-sw.py):
  1) ГАРДЫ 'kipia-test-v738' → 'kipia-test-v739' — во всех файлах,
     КРОМЕ нового test-task525.js (гварды «двойного бампа нет» в
     старых файлах смотрят на одну версию ВПЕРЁД — двигаются ПЕРВЫМИ,
     до АССЕРТОВ, иначе ассерты уже-bumped попадут под гвард);
  2) АССЕРТЫ 'kipia-test-v737' → 'kipia-test-v738' — во всех старых
     файлах;
  3) sw.js: CACHE_VERSION v737 → v738 (менялся index.html — кнопка
     инструкции СО 153-34.03.603-2003 в Библиотеке/Электробезопасности);
  4) регистрация test-task525.js в tests/run-all.js.
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task525.js']

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

print('Шаг 1 — ГАРДЫ v738 → v739 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v738', 'kipia-test-v739', 'гард')

print('Шаг 2 — АССЕРТЫ v737 → v738:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v737', 'kipia-test-v738', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v737 → v738:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v737') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v737'",
                    "const CACHE_VERSION = 'kipia-test-v738'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v738')
elif sw.count('kipia-test-v738') == 1:
    print('  sw.js: уже kipia-test-v738 (пропуск)')
else:
    raise SystemExit('sw.js: неожиданное состояние версий')

print('Шаг 4 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task525.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task524.js');" in src:
    anchor = "require('./test-task524.js');\n"
    add = ("// Task 525: Библиотека/Электробезопасность — на кнопке\n"
           "// инструкции СО 153-34.03.603-2003 строка статуса\n"
           "// «Отменена — приказ Минэнерго России от 01.12.2023\n"
           "// № 1105» (красная, обе темы; ссылка Drive сохранена).\n"
           "// SW v738.\n")
    src = src.replace(anchor, anchor + add +
                      "require('./test-task525.js');\n", 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  зарегистрирован после test-task524.js')
else:
    raise SystemExit('run-all.js: якорь test-task524 не найден')

total = sum(changed.values())
print('ИТОГО замен в тестах: %d' % total)
