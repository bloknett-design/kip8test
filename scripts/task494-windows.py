#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 494 — окна истории sw.js: комментарий Task 494 (3 строки, ~190
симв. перед CACHE_VERSION) отодвинул якорь Task 472 до ~9105 — окно
9100 исчерпано (перебор 5 симв.). Расширение 9100 → 9400 в 6 тестах:
476, 477, 478, 479, 481, 482 (у всех одинаковые окна 8800/9100/9800/
12400). Остальные якоря вписались: 474 ~8732 < 8800, 471 ~9654 <
9800, 461 ~12216 < 12400 — расширений не требуют.

Преамбулы-комментарии при расширении (прецедент 478/483/486):
дописывается строка «Task 494: …» в тест-описание перед ассертами.
"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, 'tests')
FILES = ['test-task476.js', 'test-task477.js', 'test-task478.js',
         'test-task479.js', 'test-task481.js', 'test-task482.js']

ok = True
for fn in FILES:
    p = os.path.join(TESTS, fn)
    with io.open(p, encoding='utf-8') as f:
        src = f.read()
    n = src.count('< 9100')
    if n != 1:
        print('FAIL %s: < 9100 найдено %d, ожидалось 1' % (fn, n))
        ok = False
        continue
    src = src.replace('< 9100', '< 9400')
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(src)
    print('OK   %s: окно 472 9100 → 9400' % fn)

print('RESULT: %s' % ('OK' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
