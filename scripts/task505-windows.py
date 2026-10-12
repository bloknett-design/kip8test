#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 505: ОКНА ИСТОРИИ версий sw.js — комментарий Task 505 (~615
# симв.) перед CACHE_VERSION отодвинул все исторические якоря;
# окна в тестах расширены на +700 (запас). Две формы:
#   SW_SRC.slice(Math.max(0, i - N), i)  → N + 700
#   (i - iNNN) < N                       → N + 700
# Заголовки тестов («окно 1700» и т.п.) — ИСТОРИЧЕСКИЕ, не меняются
# (прецедент task483-windows.py / task484-windows.py).
# Запуск из корня репо kip8test.
import re

FILES = [
    'tests/test-task461.js', 'tests/test-task472.js',
    'tests/test-task473.js', 'tests/test-task474.js',
    'tests/test-task476.js', 'tests/test-task477.js',
    'tests/test-task478.js', 'tests/test-task479.js',
    'tests/test-task480.js', 'tests/test-task481.js',
    'tests/test-task482.js', 'tests/test-task483.js',
    'tests/test-task484.js', 'tests/test-task485.js',
    'tests/test-task486.js', 'tests/test-task488.js',
    'tests/test-task493.js', 'tests/test-task494.js',
    'tests/test-task495.js', 'tests/test-task496.js',
    'tests/test-task497.js', 'tests/test-task501.js',
]

SHIFT = 700
# окно-вырезка назад от якоря версии: Math.max(0, i - N), i)
RE_SLICE = re.compile(r'(SW_SRC\.slice\(Math\.max\(0, i - )(\d+)(\), i\))')
# дистанция до исторического якоря: (i - iNNN) < N
RE_DIST = re.compile(r'(\(i - i\d+\) < )(\d+)')

total = 0
for f in FILES:
    s = open(f, encoding='utf-8').read()
    orig = s
    n1 = [0]

    def bump_slice(m):
        n1[0] += 1
        return m.group(1) + str(int(m.group(2)) + SHIFT) + m.group(3)

    s = RE_SLICE.sub(bump_slice, s)
    n2 = [0]

    def bump_dist(m):
        n2[0] += 1
        return m.group(1) + str(int(m.group(2)) + SHIFT)

    s = RE_DIST.sub(bump_dist, s)
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        total += n1[0] + n2[0]
        print('%s: slice +%d, dist +%d' % (f, n1[0], n2[0]))
print('итого расширено окон: %d' % total)
