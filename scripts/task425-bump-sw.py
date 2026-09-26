#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 425 — SW-бамп kipia-test-v651 → kipia-test-v652 (механика 409-424).

Guard-файлы по git HEAD (HEAD = d2fd43c, Task 424):
  1) guard'ы (HEAD: kipia-test-v652 — ассерты «следующая версия не
     должна появиться»): v652 → v653 (85 файлов = 84 прежних +
     test-task424.js с guard-строкой);
  2) основная версия: kipia-test-v651 → v652 (112 файлов = 111
     прежних + test-task424.js; sw.js + тесты; test-task425.js НЕ
     содержит v651 — его собственные v652/v653 уже верны).
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
    guard_rel = head_grep('kipia-test-v652')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 85, 'ожидалось 85 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v651' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v652', 'kipia-test-v653')  # вперёд
    m = bump(main_targets, 'kipia-test-v651', 'kipia-test-v652')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 85, 'guard-файлов ожидалось 85, обработано %d' % g
    # main = 111 файлов с v651 (вкл. test-task424.js) + sw.js
    assert m == 112, 'main-файлов ожидалось 112, обработано %d' % m
    print('OK — SW v652')


if __name__ == '__main__':
    main()
