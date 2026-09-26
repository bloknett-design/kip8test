#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 423 — SW-бамп kipia-test-v649 → kipia-test-v650 (механика 409-422).

Guard-файлы по git HEAD (HEAD = 4b97be6, Task 422):
  1) guard'ы (HEAD: kipia-test-v650 — ассерты «следующая версия не
     должна появиться»): v650 → v651 (83 файла = 82 прежних +
     test-task422.js с guard-строкой);
  2) основная версия: kipia-test-v649 → v650 (110 файлов = 109
     тестов + sw.js; test-task423.js НЕ содержит v649 — его
     собственные v650/v651 уже верны).
Исторические .md (worklog, DEPLOY-*) НЕ трогаем.
"""
import io
import glob
import os
import subprocess

ROOT = '/home/z/my-project/kip8test'


def head_grep(pattern):
    out = subprocess.run(
        ['git', 'grep', '-l', pattern, 'HEAD', '--', 'tests/'],
        cwd=ROOT, capture_output=True, text=True).stdout
    return set(l.split(':', 1)[1] for l in out.splitlines() if l)


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
    guard_rel = head_grep('kipia-test-v650')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 83, 'ожидалось 83 guard-файла, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v649' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v650', 'kipia-test-v651')  # вперёд
    m = bump(main_targets, 'kipia-test-v649', 'kipia-test-v650')    # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 83, 'guard-файлов ожидалось 83, обработано %d' % g
    # main = 109 тестов с v649 (вкл. test-task419/420/421/422) + sw.js
    assert m == 110, 'main-файлов ожидалось 110, обработано %d' % m
    print('OK — SW v650')


if __name__ == '__main__':
    main()
