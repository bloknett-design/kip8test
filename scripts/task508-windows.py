#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 508 — окна истории sw.js: комментарий Task 508 (~160 симв. перед
CACHE_VERSION) отодвинул четыре якоря за границы прежних окон
(замер от '// Task N:' до строки версии):
  461: 16317 > 16300  → 17000
  471: 13755 > 13700  → 14400
  483:  9814 >  9300  → 10500
  500:  2568 >  2200  →  2800
Прецедент: Task 480/499/502 — расширение с пояснительной записью.
"""
import io
import sys

ROOT = '/home/z/my-project/kip8test'

FIXES = [
    ('tests/test-task461.js',
     'const above = SW_SRC.slice(Math.max(0, i - 16300), i);',
     'const above = SW_SRC.slice(Math.max(0, i - 17000), i);',
     '        // Task 508: окно 16300 → 17000 — комментарий архива\n'
     '        // Кабельного журнала (~160 симв.) отодвинул Task 461.\n'),
    ('tests/test-task471.js',
     'const ctx = SW_SRC.slice(Math.max(0, i - 13700), i);',
     'const ctx = SW_SRC.slice(Math.max(0, i - 14400), i);',
     '        // Task 508: окно 13700 → 14400 — комментарий архива\n'
     '        // Кабельного журнала (~160 симв.) отодвинул Task 471.\n'),
    ('tests/test-task483.js',
     'const ctx = SW_SRC.slice(Math.max(0, i - 9300), i);',
     'const ctx = SW_SRC.slice(Math.max(0, i - 10500), i);',
     '        // Task 508: окно 9300 → 10500 — комментарий архива\n'
     '        // Кабельного журнала (~160 симв.) отодвинул Task 483.\n'),
    ('tests/test-task500.js',
     'const ctx = SW_SRC.slice(Math.max(0, i - 2200), i);',
     'const ctx = SW_SRC.slice(Math.max(0, i - 2800), i);',
     '        // Task 508: окно 2200 → 2800 — комментарий архива\n'
     '        // Кабельного журнала отодвинул Task 500 до ~2568.\n'),
]

fails = []
for rel, old, new, note in FIXES:
    p = ROOT + '/' + rel
    src = io.open(p, encoding='utf-8').read()
    if src.count(old) != 1:
        fails.append('%s: окно ×%d' % (rel, src.count(old)))
        continue
    src = src.replace(old, note + new, 1)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('OK   %s: окно расширено' % rel)

if fails:
    for f in fails:
        print('FAIL ' + f)
    sys.exit(1)
print('ОКНА ИСТОРИИ РАСШИРЕНЫ')
