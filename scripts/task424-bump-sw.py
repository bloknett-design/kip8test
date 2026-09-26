#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 424 — SW-бамп kipia-test-v650 → kipia-test-v651 (механика 409-423).

Guard-файлы по git HEAD (HEAD = 1585139, Task 423):
  1) guard'ы (HEAD: kipia-test-v651 — ассерты «следующая версия не
     должна появиться»): v651 → v652 (84 файла = 83 прежних +
     test-task423.js с guard-строкой);
  2) основная версия: kipia-test-v650 → v651 (111 файлов = 110
     тестов + sw.js; test-task424.js НЕ содержит v650 — его
     собственные v651/v652 уже верны).
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
    guard_rel = head_grep('kipia-test-v651')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 84, 'ожидалось 84 guard-файла, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v650' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v651', 'kipia-test-v652')  # вперёд
    m = bump(main_targets, 'kipia-test-v650', 'kipia-test-v651')    # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 84, 'guard-файлов ожидалось 84, обработано %d' % g
    # main = 110 тестов с v650 (вкл. test-task423.js) + sw.js;
    # test-task424.js (новый, v651/v652) в bump не попадает
    assert m == 111, 'main-файлов ожидалось 111, обработано %d' % m
    print('OK — SW v651')


if __name__ == '__main__':
    main()
