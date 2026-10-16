#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 534 — бамп SW-версий в тестах kip8test (v746→v747), по образцу
task533-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов):
  1) ГАРДЫ 'kipia-test-v747' → 'kipia-test-v748' — во всех файлах
     (в Task 533 гварды v747 уже расставлены);
  2) АССЕРТЫ 'kipia-test-v746' → 'kipia-test-v747' — во всех старых
     файлах (test-task534.js ещё НЕ существует — пишется после бампа
     сразу с ассертами v747 и гвардом v748);
  3) sw.js: CACHE_VERSION v746 → v747 (менялись index.html — Task 534:
     второй прямой канал погоды wttr.in + подсказка authorizeWeather
     при «нет разрешения UrlFetchApp»; календарь: год/месяц по левому
     краю, подписи убраны, шрифт месяца мельче; WorkSchedule.gs —
     authorizeWeather + diag 90).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
# тесты, которые уже переписаны вручную под v747 (пока нет таких)
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

print('Шаг 1 — ГАРДЫ v747 → v748 (кроме НОВОГО/адаптированного):')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v747', 'kipia-test-v748', 'гард')

print('Шаг 2 — АССЕРТЫ v746 → v747:')
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), 'kipia-test-v746', 'kipia-test-v747', 'ассерт')

print('Шаг 3 — sw.js: CACHE_VERSION v746 → v747:')
sw_path = os.path.join(ROOT, 'sw.js')
sw = io.open(sw_path, encoding='utf-8').read()
if sw.count('kipia-test-v746') == 1:
    sw = sw.replace("const CACHE_VERSION = 'kipia-test-v746'",
                    "const CACHE_VERSION = 'kipia-test-v747'")
    io.open(sw_path, 'w', encoding='utf-8').write(sw)
    print('  sw.js: CACHE_VERSION = kipia-test-v747')
else:
    print('  ВНИМАНИЕ: kipia-test-v746 в sw.js встречается %d раз — не тронуто'
          % sw.count('kipia-test-v746'))

total = sum(changed.values())
print('Итого замен в тестах: %d (файлов: %d)' % (total, len(changed)))
