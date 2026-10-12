#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 506: ОКНА ИСТОРИИ версий sw.js — комментарий Task 506 (~520
# симв.) перед CACHE_VERSION отодвинул исторические якоря; запас
# +700 от Task 505 исчерпан (его комментарий был ~615 симв.).
# Окна расширены на +600 в файлах, где тесты падали. Формы (как
# task505-windows.py):
#   SW_SRC.slice(Math.max(0, i - N), i)  → N + 600
#   (i - iNNN) < N                       → N + 600
# Заголовки тестов — ИСТОРИЧЕСКИЕ, не меняются.
import re

FILES = [
    'tests/test-task461.js', 'tests/test-task471.js',
    'tests/test-task472.js', 'tests/test-task473.js',
    'tests/test-task474.js', 'tests/test-task476.js',
    'tests/test-task477.js', 'tests/test-task478.js',
    'tests/test-task479.js', 'tests/test-task480.js',
    'tests/test-task481.js', 'tests/test-task482.js',
    'tests/test-task484.js', 'tests/test-task485.js',
    'tests/test-task486.js', 'tests/test-task488.js',
    'tests/test-task493.js', 'tests/test-task494.js',
    'tests/test-task495.js', 'tests/test-task496.js',
    'tests/test-task497.js', 'tests/test-task500.js',
    'tests/test-task501.js',
]

SHIFT = 600
RE_SLICE = re.compile(r'(SW_SRC\.slice\(Math\.max\(0, i - )(\d+)(\), i\))')
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
print('итого расширено окон: %d (+%d каждое)' % (total, SHIFT))
