#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 410 — SW-бамп kipia-test-v636 → kipia-test-v637 (механика 409).

Guard-файлы определяются по git HEAD (assertFalse «следующая версия не
должна появиться»), а не по текущему диску — test-task410.js (новый,
не в HEAD) содержит v637 как MAIN-ассерт новой версии и guard'ом НЕ
является:
  1) guard'ы (HEAD: kipia-test-v637): на диске v637 → v638;
  2) основная версия: kipia-test-v636 → v637 (sw.js + tests/*.js).
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
    guard_rel = head_grep('kipia-test-v637')
    print('guard-файлов в HEAD:', len(guard_rel))
    assert len(guard_rel) == 73, 'ожидалось 73 guard-файлов, найдено %d' % len(guard_rel)

    all_targets = [os.path.join(ROOT, 'sw.js')] + sorted(
        glob.glob(os.path.join(ROOT, 'tests', '*.js')))
    # guard'ы: только файлы, где v637 был guard'ом В HEAD; test-task410.js
    # не входит (его v637 — main-ассерт новой версии, файла нет в HEAD)
    guard_targets = [p for p in all_targets
                     if os.path.relpath(p, ROOT) in guard_rel
                     and os.path.basename(p) != 'test-task410.js']
    main_targets = [p for p in all_targets
                    if 'kipia-test-v636' in io.open(p, encoding='utf-8').read()]

    g = bump(guard_targets, 'kipia-test-v637', 'kipia-test-v638')  # вперёд
    m = bump(main_targets, 'kipia-test-v636', 'kipia-test-v637')   # затем main
    print('Итого файлов: guard %d, main %d' % (g, m))
    assert g == 73, 'guard-файлов ожидалось 73, обработано %d' % g
    assert m == 97, 'main-файлов ожидалось 97, обработано %d' % m
    print('OK — SW v637')


if __name__ == '__main__':
    main()
