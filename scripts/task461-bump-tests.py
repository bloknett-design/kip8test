#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 461: массовая замена версий SW в тестах kip8test.
# Порядок СТРОГО сверху вниз (иначе двойной сдвиг):
#   1) kipia-test-v685 → kipia-test-v686  (защитный no-op, v685 в тестах до бампа нет)
#   2) kipia-test-v684 → kipia-test-v685  (ассерты текущей версии)
# test-task461.js исключён (пишется ПОСЛЕ бампа с ассертом v685).
import glob
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = [
    ('kipia-test-v685', 'kipia-test-v686'),
    ('kipia-test-v684', 'kipia-test-v685'),
]
EXCLUDE = {'test-task461.js'}

files = sorted(glob.glob(os.path.join(ROOT, 'tests', 'test-*.js')))
changed_files = 0
total_repl = 0
for path in files:
    if os.path.basename(path) in EXCLUDE:
        continue
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    orig = src
    n = 0
    for a, b in ORDER:
        n += src.count(a)
        src = src.replace(a, b)
    if src != orig:
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(src)
        changed_files += 1
        total_repl += n
print('изменено файлов: %d, замен: %d' % (changed_files, total_repl))
