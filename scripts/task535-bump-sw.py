#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 535 — бамп SW-версий в тестах kip8test (v747→v748), по образцу
task534-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГАРДЫ 'kipia-test-v748' → 'kipia-test-v749' — во всех файлах;
  2) АССЕРТЫ 'kipia-test-v747' → 'kipia-test-v748' — во всех старых
     файлах (test-task535.js ещё НЕ существует — пишется после бампа
     сразу с ассертами v748 и гвардом v749);
  3) sw.js: CACHE_VERSION v747 → v748 (менялся index.html — Task 535:
     глиф «Я» с левой ножкой; день недели/блок погоды смещены правее
     (зазор дата→погода 2→7 колонок при короткой температуре);
     календарь: селекты по высоте кнопок (30px), светлая тема —
     яркие стрелки/«Сегодня»; WorkSchedule.gs — authorizeWeather
     с полным URL разрешения + подсказка appsscript.json).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
# тесты, которые уже переписаны вручную под v748 (пока нет таких)
OWN = []

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

print('Шаг 1 — ГАРДЫ v748 → v749 (кроме НОВОГО/адаптированного):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v748', 'kipia-test-v749', 'гард')

print('Шаг 2 — АССЕРТЫ v747 → v748:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v747', 'kipia-test-v748', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v747 → v748:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v747') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v747'",
                    "const CACHE_VERSION = 'kipia-test-v748'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v748')
else:
    print('  ВНИМАНИЕ: kipia-test-v747 в sw.js встречается %d раз — не тронуто'
          % sw.count('kipia-test-v747'))

total = sum(changed.values())
print('Итого замен в тестах: %d (файлов: %d)' % (total, len(changed)))
