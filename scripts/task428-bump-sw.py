#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 428 — SW-бамп kipia-test-v654 → kipia-test-v655 (механика 409-427).

Порядок (как в task427-bump-sw.py):
  1) guard'ы: kipia-test-v655 → v656 (88 файлов = 87 прежних
     guard'ов Task 427 + собственный guard-ассерт test-task427.js;
     НОВЫЙ test-task428.js НЕ трогаем — его основной ассерт уже
     v655, guard у него свой v656);
  2) основная версия: kipia-test-v654 → v655 (115 файлов =
     113 тестов + sw.js + test-task427.js — его собственный
     основной ассерт v654 раунда 427).
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
    guard_targets = [p for p in files_with('kipia-test-v655')
                     if not p.endswith('test-task428.js')]
    print('guard-файлов:', len(guard_targets))
    assert len(guard_targets) == 88, \
        'ожидалось 88 guard-файлов, найдено %d' % len(guard_targets)

    g = bump(guard_targets, 'kipia-test-v655', 'kipia-test-v656')  # вперёд
    main_targets = files_with('kipia-test-v654',
                              extra=[os.path.join(ROOT, 'sw.js')])
    m = bump(main_targets, 'kipia-test-v654', 'kipia-test-v655')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert m == 115, 'main-файлов ожидалось 115 (113 тестов + sw.js + test-task427.js с собственным v654-ассертом), обработано %d' % m
    print('OK — SW v655')


if __name__ == '__main__':
    main()
