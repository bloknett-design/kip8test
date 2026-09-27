#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 426 — SW-бамп kipia-test-v652 → kipia-test-v653 (механика 409-425).

Порядок (как в task425-bump-sw.py):
  1) guard'ы: kipia-test-v653 → v654 (86 файлов = 85 прежних +
     test-task425.js с guard-строкой) — ассерты «следующая версия
     не должна появиться»;
  2) основная версия: kipia-test-v652 → v653 (113 файла =
     112 тестов + sw.js).
Исторические .md (worklog, DEPLOY-*) НЕ трогаем.
test-task426.js пишется ПОСЛЕ бампа с собственными v653/v654.
"""
import io
import glob
import os

ROOT = '/home/z/my-project/kip8test'


def files_with(pattern, extra=None):
    targets = sorted(glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    if extra:
        targets = extra + targets
    return [p for p in targets
            if pattern in io.open(p, encoding='utf-8').read()]


def bump(files, old, new):
    total = 0
    touched = 0
    for p in files:
        with io.open(p, encoding='utf-8') as f:
            s = f.read()
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            with io.open(p, 'w', encoding='utf-8') as f:
                f.write(s)
            total += n
            touched += 1
    print('%s → %s: %d вхождений в %d файлах' % (old, new, total, touched))
    return touched


def main():
    guard_targets = files_with('kipia-test-v653')
    print('guard-файлов:', len(guard_targets))
    assert len(guard_targets) == 86, \
        'ожидалось 86 guard-файлов, найдено %d' % len(guard_targets)

    g = bump(guard_targets, 'kipia-test-v653', 'kipia-test-v654')  # вперёд
    main_targets = files_with('kipia-test-v652', extra=[os.path.join(ROOT, 'sw.js')])
    m = bump(main_targets, 'kipia-test-v652', 'kipia-test-v653')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 86, 'guard-файлов ожидалось 86, обработано %d' % g
    assert m == 113, 'main-файлов ожидалось 113 (112 тестов + sw.js), обработано %d' % m
    print('OK — SW v653')


if __name__ == '__main__':
    main()
