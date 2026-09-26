#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 421 — SW-бамп kipia-test-v647 → kipia-test-v648 (механика 409-420).

Guard-файлы по git HEAD (HEAD = e5bda8f, Task 420):
  1) guard'ы (HEAD: kipia-test-v648 — ассерты «следующая версия не
     должна появиться»): v648 → v649;
  2) основная версия: kipia-test-v647 → v648 (sw.js + tests/*.js).
test-task420.js в HEAD содержит и v647 (main), и v648 (guard) —
попадает в ОБА набора: после бампа v648 (current) + v649 (guard).
test-task421.js в HEAD отсутствует и v647 не содержит — ни в один
набор не попадает (его собственные v648/v649 уже верны).
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
    guard_rel = head_grep('kipia-test-v648')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 81, 'ожидалось 81 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v647' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v648', 'kipia-test-v649')  # вперёд
    m = bump(main_targets, 'kipia-test-v647', 'kipia-test-v648')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 81, 'guard-файлов ожидалось 81, обработано %d' % g
    # main = 107 тестов с v647 (HEAD, вкл. test-task420.js) + sw.js
    assert m == 108, 'main-файлов ожидалось 108, обработано %d' % m
    print('OK — SW v648')


if __name__ == '__main__':
    main()
