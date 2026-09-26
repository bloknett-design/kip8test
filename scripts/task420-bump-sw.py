#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 420 — SW-бамп kipia-test-v646 → kipia-test-v647 (механика 409-419).

Guard-файлы по git HEAD (HEAD = 4ea1f71, Task 419):
  1) guard'ы (HEAD: kipia-test-v647 — ассерты «следующая версия не
     должна появиться»): v647 → v648;
  2) основная версия: kipia-test-v646 → v647 (sw.js + tests/*.js).
test-task420.js содержит v647/v648 и НЕ содержит v646 — ни в один
набор не попадает (в HEAD его нет, main ищет v646).
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
    guard_rel = head_grep('kipia-test-v647')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 80, 'ожидалось 80 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v646' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v647', 'kipia-test-v648')  # вперёд
    m = bump(main_targets, 'kipia-test-v646', 'kipia-test-v647')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 80, 'guard-файлов ожидалось 80, обработано %d' % g
    # main = 106 тестов с v646 (HEAD) + sw.js; test-task420.js v646 не содержит
    assert m == 107, 'main-файлов ожидалось 107, обработано %d' % m
    print('OK — SW v647')


if __name__ == '__main__':
    main()
