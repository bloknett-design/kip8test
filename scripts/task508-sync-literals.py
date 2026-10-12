#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 508 — каскад синхро-литералов окон истории (task508-windows.py
расширил окна 461/471 → мета-тесты, пинящие ЛИТЕРАЛЫ чужих окон,
должны увидеть новые значения; прецедент task506-sync-literals.py):
  test-task475.js:  461 'i - 16300' → 'i - 17000'; 471 'i - 13700' → 'i - 14400'
  test-task481.js:  461 'i - 16300' → 'i - 17000'; 471 'i - 13700' → 'i - 14400'
  test-task486.js:  каскад 475 "'i - 16300'" → "'i - 17000'"
Окно test-task472 (13700) НЕ менялось — его литералы остаются.
"""
import io
import sys

ROOT = '/home/z/my-project/kip8test'

FIXES = [
    ('tests/test-task475.js',
     "        assertTrue(s.indexOf('i - 16300') !== -1, 'окно 14000 (Task 498; Task 505: +700)');",
     "        assertTrue(s.indexOf('i - 17000') !== -1, 'окно 14000 (Task 498; Task 505: +700; Task 508: +700)');"),
    ('tests/test-task475.js',
     "        assertTrue(s1.indexOf('i - 13700') !== -1, 'test-task471: 13000 (Task 501)');",
     "        assertTrue(s1.indexOf('i - 14400') !== -1, 'test-task471: 13000 (Task 501; Task 508: +700)');"),
    ('tests/test-task481.js',
     "        assertTrue(s461.indexOf('i - 16300') !== -1, 'test-task461: окно 13200 (Task 495; Task 505: +700)');",
     "        assertTrue(s461.indexOf('i - 17000') !== -1, 'test-task461: окно 13200 (Task 495; Task 505: +700; Task 508: +700)');"),
    ('tests/test-task481.js',
     "        assertTrue(s471.indexOf('i - 13700') !== -1, 'test-task471: окно 13000 (Task 501)');",
     "        assertTrue(s471.indexOf('i - 14400') !== -1, 'test-task471: окно 13000 (Task 501; Task 508: +700)');"),
    ('tests/test-task486.js',
     "        assertTrue(s475.indexOf(\"'i - 16300'\") !== -1, 'каскад 475: 461 → 14000 (Task 498; Task 505: +700)');",
     "        assertTrue(s475.indexOf(\"'i - 17000'\") !== -1, 'каскад 475: 461 → 14000 (Task 498; Task 505: +700; Task 508: +700)');"),
]

fails = []
for rel, old, new in FIXES:
    p = ROOT + '/' + rel
    src = io.open(p, encoding='utf-8').read()
    if src.count(old) != 1:
        fails.append('%s: ×%d — %s' % (rel, src.count(old), old[:60]))
        continue
    src = src.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('OK   %s: %s' % (rel, new[60:110]))

if fails:
    for f in fails:
        print('FAIL ' + f)
    sys.exit(1)
print('СИНХРО-ЛИТЕРАЛЫ ОБНОВЛЕНЫ')
