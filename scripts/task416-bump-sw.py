#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 416 — SW-бамп kipia-test-v642 → kipia-test-v643 (механика 409-415).

Guard-файлы определяются по git HEAD (HEAD = daf573d, Task 415):
  1) guard'ы (HEAD: kipia-test-v643 — ассерты «следующая версия не
     должна появиться» из Task 415 и ранее): на диске v643 → v644;
  2) основная версия: kipia-test-v642 → v643 (sw.js + tests/*.js;
     test-task416.js — новый, v642 не содержит, не тронется).
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
    guard_rel = head_grep('kipia-test-v643')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 76, 'ожидалось 76 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v642' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v643', 'kipia-test-v644')  # вперёд
    m = bump(main_targets, 'kipia-test-v642', 'kipia-test-v643')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 76, 'guard-файлов ожидалось 76, обработано %d' % g
    # 104 = 103 файла Task 415 (102 tests + sw.js) + test-task415.js
    # + test-task416.js (упоминание v642 в ассерте «не осталась»);
    # после бампа ассерт test-task416.js вручную возвращён на v642
    assert m == 104, 'main-файлов ожидалось 104, обработано %d' % m
    print('OK — SW v643')


if __name__ == '__main__':
    main()
