#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 422 — SW-бамп kipia-test-v648 → kipia-test-v649 (механика 409-421).

Guard-файлы по git HEAD (HEAD = 7d0a7f4, Task 421):
  1) guard'ы (HEAD: kipia-test-v649 — ассерты «следующая версия не
     должна появиться»): v649 → v650 (82 файла = 81 прежних +
     test-task421.js с guard-строкой);
  2) основная версия: kipia-test-v648 → v649 (109 файлов = 108
     тестов + sw.js; test-task422.js НЕ содержит v648 и в HEAD
     отсутствует — его собственные v649/v650 уже верны).
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
    guard_rel = head_grep('kipia-test-v649')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 82, 'ожидалось 82 guard-файла, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v648' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v649', 'kipia-test-v650')  # вперёд
    m = bump(main_targets, 'kipia-test-v648', 'kipia-test-v649')    # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 82, 'guard-файлов ожидалось 82, обработано %d' % g
    # main = 108 тестов с v648 (вкл. test-task419/420/421) + sw.js
    assert m == 109, 'main-файлов ожидалось 109, обработано %d' % m
    print('OK — SW v649')


if __name__ == '__main__':
    main()
