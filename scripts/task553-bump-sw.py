#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 553 — бамп SW-версии в kip8test (v761→v762), по образцу
task550-bump-sw.py (урок Task 529: гварды «следующей версии нет»
двигаются ПЕРВЫМИ, до ассертов — иначе v762 окажется и в гвардах,
и в ассертах, и разделить их будет нельзя):
  1) ГВАРДЫ 'kipia-test-v762' → 'kipia-test-v763' — во всех
     тестах, КРОМЕ НОВОГО test-task553.js (его позитивный ассерт
     v762 — целевая версия, двигать нельзя);
  2) АССЕРТЫ 'kipia-test-v761' → 'kipia-test-v762' — во всех
     тестах, кроме нового (в нём v761 нет);
  3) sw.js: CACHE_VERSION v761 → v762 (index.html менялся:
     Task 553 — блок «Повторные инструктажи и периодическая
     проверка знаний»: отображение примечания записи — поле
     «комментарий» листа «Инструктажи», столбец H).
"""
import io
import os

ROOT = '/home/z/my-project/kip8test'
OWN = ['test-task553.js']
CUR = 'kipia-test-v761'    # текущая версия (до бампа)
NEW = 'kipia-test-v762'    # целевая версия Task 553
NXT = 'kipia-test-v763'    # следующая (гварды)

changed = {}

# Шаг 0 — ГВАРДЫ от повторного применения / кривого состояния
sw_path = os.path.join(ROOT, 'sw.js')
sw_src = io.open(sw_path, encoding='utf-8').read()
if sw_src.count("const CACHE_VERSION = '" + NEW + "'") != 0:
    print('  FAIL: %s уже в sw.js — скрипт уже применялся' % NEW)
    raise SystemExit(1)
if sw_src.count("const CACHE_VERSION = '" + CUR + "'") != 1:
    print('  FAIL: CACHE_VERSION %s найден %d раз' %
          (CUR, sw_src.count("const CACHE_VERSION = '" + CUR + "'")))
    raise SystemExit(1)


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

print('Шаг 1 — ГВАРДЫ %s → %s (кроме НОВОГО %s):' % (NEW, NXT, OWN))
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), NEW, NXT, 'гард')

print('Шаг 2 — АССЕРТЫ %s → %s (кроме НОВОГО):' % (CUR, NEW))
for f in files:
    if f in OWN:
        continue
    bump(os.path.join(tests_dir, f), CUR, NEW, 'ассерт')

print('Шаг 3 — sw.js CACHE_VERSION:')
n = sw_src.count(CUR)
sw_src = sw_src.replace(CUR, NEW)
io.open(sw_path, 'w', encoding='utf-8').write(sw_src)
changed['sw.js'] = changed.get('sw.js', 0) + n
print('  sw.js: v761 → v762 ×%d' % n)

print('\nИтого замен: %d в %d файлах' %
      (sum(changed.values()), len(changed)))
