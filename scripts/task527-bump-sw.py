#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 527 — бамп SW-версий в тестах kip8test (v739→v740) + регистрация
нового теста (по образцу task526-bump-sw.py):
  1) ГАРДЫ 'kipia-test-v740' → 'kipia-test-v741' — во всех файлах,
     КРОМЕ нового test-task527.js (гварды «двойного бампа нет» в
     старых файлах смотрят на одну версию ВПЕРЁД — двигаются ПЕРВЫМИ,
     до АССЕРТОВ, иначе ассерты уже-bumped попадают под гвард);
  2) АССЕРТЫ 'kipia-test-v739' → 'kipia-test-v740' — во всех старых
     файлах (включая адаптированный test-task526.js);
  3) sw.js: CACHE_VERSION v739 → v740 (менялся index.html — подписи
     размеров выведены из фигур, данные расчёта — в картинке под
     фигурой, рамка 350px);
  4) регистрация test-task527.js в tests/run-all.js.
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task527.js']

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

print('Шаг 1 — ГАРДЫ v740 → v741 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v740', 'kipia-test-v741', 'гард')

print('Шаг 2 — АССЕРТЫ v739 → v740:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v739', 'kipia-test-v740', 'ассерт')

print('Шаг 3 — sw.js CACHE_VERSION v739 → v740:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
n = sw.count("const CACHE_VERSION = 'kipia-test-v739'")
if n != 1:
    raise SystemExit('ОШИБКА: CACHE_VERSION v739 найден %d раз (ожидается 1)' % n)
sw = sw.replace("const CACHE_VERSION = 'kipia-test-v739'",
                "const CACHE_VERSION = 'kipia-test-v740'")
io.open(sw_path, 'w', encoding='utf-8').write(sw)
changed['sw.js'] = changed.get('sw.js', 0) + 1
print('  sw.js: CACHE_VERSION v740')

print('Шаг 4 — регистрация test-task527.js в run-all.js:')
ra_path = os.path.join(tests_dir, 'run-all.js')
ra = io.open(ra_path, encoding='utf-8').read()
if "require('./test-task527.js')" in ra:
    print('  уже зарегистрирован')
else:
    anchor = "require('./test-task526.js');"
    n = ra.count(anchor)
    if n != 1:
        raise SystemExit('ОШИБКА: якорь run-all найден %d раз' % n)
    ra = ra.replace(anchor, anchor + "\n// Task 527: подписи размеров вне фигур, данные расчёта —\n"
                                   "// в картинке под фигурой, рамка 350px. SW v740.\n"
                                   "require('./test-task527.js');")
    io.open(ra_path, 'w', encoding='utf-8').write(ra)
    changed['run-all.js'] = changed.get('run-all.js', 0) + 1
    print('  зарегистрирован после test-task526.js')

print('')
print('Итого файлов изменено: %d' % len(changed))
total = sum(changed.values())
print('Итого замен: %d' % total)
