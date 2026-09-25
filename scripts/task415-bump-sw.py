#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 415 — SW-бамп kipia-test-v641 → kipia-test-v642 (механика 409-414).

Guard-файлы определяются по git HEAD (HEAD = 513466c, Task 414):
  1) guard'ы (HEAD: kipia-test-v642 — ассерты «следующая версия не
     должна появиться» из Task 414 и ранее): на диске v642 → v643;
  2) основная версия: kipia-test-v641 → v642 (sw.js + tests/*.js;
     test-task415.js — новый, v641 не содержит, не тронется).
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
    guard_rel = head_grep('kipia-test-v642')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 75, 'ожидалось 75 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v641' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v642', 'kipia-test-v643')  # вперёд
    m = bump(main_targets, 'kipia-test-v641', 'kipia-test-v642')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 75, 'guard-файлов ожидалось 75, обработано %d' % g
    # 102 = 101 файл tests/ (main-бамп Task 414: 100 + test-task414.js
    # с v641-ассертом) + sw.js; test-task415.js — новый, v641 не содержит
    assert m == 102, 'main-файлов ожидалось 102, обработано %d' % m
    print('OK — SW v642')


if __name__ == '__main__':
    main()
