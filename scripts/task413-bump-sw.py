#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 413 — SW-бамп kipia-test-v639 → kipia-test-v640 (механика 409-412).

Guard-файлы определяются по git HEAD (HEAD = 1da57de, Task 412):
  1) guard'ы (HEAD: kipia-test-v640 — ассерты «следующая версия не
     должна появиться» из Task 412): на диске v640 → v641;
  2) основная версия: kipia-test-v639 → v640 (sw.js + tests/*.js;
     test-task413.js — новый, v639 не содержит, не тронется).
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
    guard_rel = head_grep('kipia-test-v640')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 73, 'ожидалось 73 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v639' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v640', 'kipia-test-v641')  # вперёд
    m = bump(main_targets, 'kipia-test-v639', 'kipia-test-v640')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 73, 'guard-файлов ожидалось 73, обработано %d' % g
    # 100 = 99 файлов tests/ (main-бамп Task 412 + test-task412.js) +
    # sw.js; test-task413.js — новый, v639 не содержит
    assert m == 100, 'main-файлов ожидалось 100, обработано %d' % m
    print('OK — SW v640')


if __name__ == '__main__':
    main()
