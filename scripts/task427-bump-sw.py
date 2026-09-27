#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 427 — SW-бамп kipia-test-v653 → kipia-test-v654 (механика 409-426).

Порядок (как в task426-bump-sw.py):
  1) guard'ы: kipia-test-v654 → v655 (87 файлов = 86 прежних +
     test-task425.js; НОВЫЙ test-task427.js НЕ трогаем — его
     основной ассерт уже v654, guard у него свой v655);
  2) основная версия: kipia-test-v653 → v654 (114 файла =
     113 тестов + sw.js).
Исторические .md (worklog, DEPLOY-*) НЕ трогаем.
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
    guard_targets = [p for p in files_with('kipia-test-v654')
                     if not p.endswith('test-task427.js')]
    print('guard-файлов:', len(guard_targets))
    assert len(guard_targets) == 87, \
        'ожидалось 87 guard-файлов, найдено %d' % len(guard_targets)

    g = bump(guard_targets, 'kipia-test-v654', 'kipia-test-v655')  # вперёд
    main_targets = files_with('kipia-test-v653',
                               extra=[os.path.join(ROOT, 'sw.js')])
    m = bump(main_targets, 'kipia-test-v653', 'kipia-test-v654')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert m == 114, 'main-файлов ожидалось 114 (113 тестов + sw.js), обработано %d' % m
    print('OK — SW v654')


if __name__ == '__main__':
    main()
