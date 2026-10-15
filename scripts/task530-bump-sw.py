#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 530 — бамп SW-версий в тестах kip8test (v742→v743) + регистрация
нового теста (по образцу task523-bump-sw.py, урок Task 529 — гварды
«следующей версии нет» двигаются ПЕРВЫМИ, до ассертов):
  1) ГАРДЫ 'kipia-test-v743' → 'kipia-test-v744' — во всех файлах,
     КРОМЕ test-task530.js и test-task529.js (в них v743 — ТЕКУЩАЯ
     версия, ассерты Task 530; гварды «двойного бампа нет» в старых
     файлах смотрят на одну версию ВПЕРЁД);
  2) АССЕРТЫ 'kipia-test-v742' → 'kipia-test-v743' — во всех старых
     файлах (529 исключён: там проверка «старой версии нет» умышленно
     ссылается на v742);
  3) sw.js: CACHE_VERSION v742 → v743 (менялся index.html — Task 530);
  4) регистрация test-task530.js в tests/run-all.js.
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task530.js', 'test-task529.js']

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

print('Шаг 1 — ГАРДЫ v743 → v744 (кроме НОВОГО/адаптированного):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v743', 'kipia-test-v744', 'гард')

print('Шаг 2 — АССЕРТЫ v742 → v743:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v742', 'kipia-test-v743', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v742 → v743:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v742') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v742'",
                    "const CACHE_VERSION = 'kipia-test-v743'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v743')
elif sw.count('kipia-test-v743') == 1:
    print('  sw.js: уже kipia-test-v743 (пропуск)')
else:
    raise SystemExit('sw.js: неожиданное состояние версий')

print('Шаг 4 — регистрация НОВОГО теста в run-all.js:')
run_all = os.path.join(tests_dir, 'run-all.js')
src = io.open(run_all, encoding='utf-8').read()
if "require('./test-task530.js');" in src:
    print('  уже зарегистрирован')
elif "require('./test-task529.js');" in src:
    anchor = "require('./test-task529.js');\n"
    src = src.replace(anchor, anchor + "require('./test-task530.js');\n", 1)
    io.open(run_all, 'w', encoding='utf-8').write(src)
    print('  test-task530.js зарегистрирован после test-task529.js')
else:
    raise SystemExit('run-all.js: якорь test-task529.js не найден')

print('Итого файлов изменено:', len(changed))
print('Итого замен:', sum(changed.values()))
