#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 418 — SW-бамп kipia-test-v644 → kipia-test-v645 (механика 409-417).

Guard-файлы определяются по git HEAD (HEAD = 2c0f5ea, Task 417):
  1) guard'ы (HEAD: kipia-test-v645 — ассерты «следующая версия не
     должна появиться» из Task 417 и ранее): на диске v645 → v646;
  2) основная версия: kipia-test-v644 → v645 (sw.js + tests/*.js;
     новый test-task418.js уже несёт ассерт v645, v644 не содержит).
test-task418.js упоминает v645 ДО бампа — в main-набор не попадает
(main ищет v644), но guard-замена v645 → v646 его НЕ тронет: файл
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
    guard_rel = head_grep('kipia-test-v645')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 78, 'ожидалось 78 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel]
    main_targets = [p for p in all_targets
                    if 'kipia-test-v644' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v645', 'kipia-test-v646')  # вперёд
    m = bump(main_targets, 'kipia-test-v644', 'kipia-test-v645')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 78, 'guard-файлов ожидалось 78, обработано %d' % g
    # main = 104 tests с v644 (HEAD) + sw.js; test-task418.js v644 не содержит
    assert m == 105, 'main-файлов ожидалось 105, обработано %d' % m
    print('OK — SW v645')


if __name__ == '__main__':
    main()
