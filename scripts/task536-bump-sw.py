#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 536 — бамп SW-версий в тестах kip8test (v748→v749), по образцу
task535-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГВАРДЫ 'kipia-test-v749' → 'kipia-test-v750' — во всех файлах;
  2) АССЕРТЫ 'kipia-test-v748' → 'kipia-test-v749' — во всех старых
     файлах (test-task536.js исключён: написан сразу с ассертами v749
     и гвардом v750);
  3) sw.js: CACHE_VERSION v748 → v749 (менялся index.html — Task 536:
     серверная погода УДАЛЕНА: WorkSchedule.gs без
     getWeather/_parseMeteoinfo/_parseOpenMeteo/authorizeWeather,
     Code.gs без роутинга; клиент — двухканальная цепочка
     open-meteo → wttr.in без серверного резерва).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
# тесты, которые уже написаны вручную под v749 (гвард v750 внутри)
OWN = ['test-task536.js']

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

print('Шаг 1 — ГВАРДЫ v749 → v750 (кроме НОВОГО):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v749', 'kipia-test-v750', 'гард')

print('Шаг 2 — АССЕРТЫ v748 → v749:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v748', 'kipia-test-v749', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v748 → v749:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v748') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v748'",
                    "const CACHE_VERSION = 'kipia-test-v749'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v749')
else:
    print('  ВНИМАНИЕ: kipia-test-v748 в sw.js встречается %d раз — не тронуто'
          % sw.count('kipia-test-v748'))

total = sum(changed.values())
print('Итого замен в тестах: %d (файлов: %d)' % (total, len(changed)))
