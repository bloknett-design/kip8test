#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 417 — SW-бамп kipia-test-v643 → kipia-test-v644 (механика 409-416).

Guard-файлы определяются по git HEAD (HEAD = 1fc80d9, Task 416):
  1) guard'ы (HEAD: kipia-test-v644 — ассерты «следующая версия не
     должна появиться» из Task 416 и ранее): на диске v644 → v645;
  2) основная версия: kipia-test-v643 → v644 (sw.js + tests/*.js;
     новый test-task417.js уже несёт ассерт v644, v643 не содержит).
test-task417.js упоминает v644 ДО бампа — в main-набор не попадает
(main ищет v643), но guard-замена v644→v645 его НЕ тронет: файл
не в HEAD (guard-набор только из HEAD).
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
    guard_rel = head_grep('kipia-test-v644')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 77, 'ожидалось 77 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v643' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v644', 'kipia-test-v645')  # вперёд
    m = bump(main_targets, 'kipia-test-v643', 'kipia-test-v644')    # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 77, 'guard-файлов ожидалось 77, обработано %d' % g
    # main = 103 tests с v643 + sw.js; test-task417.js v643 не содержит
    assert m == 104, 'main-файлов ожидалось 104, обработано %d' % m
    print('OK — SW v644')


if __name__ == '__main__':
    main()
