#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 532 — перенос тестов из kip8test в kip8 + бамп SW (v541→v542):
  1) test-task532.js: kip8test-версия с заменой SW-секций
     (kipia-test-v745 → kipia-v542; гвард v746 → v543);
  2) ГАРДЫ 'kipia-v542' → 'kipia-v543' — во всех старых файлах kip8;
  3) АССЕРТЫ 'kipia-v541' → 'kipia-v542' — во всех старых файлах kip8;
  4) sw.js: CACHE_VERSION v541 → v542;
  5) регистрация test-task532.js в kip8 tests/run-all.js;
  6) task532-browser-check-kip8.py (порт 8996, localStorage без префикса).
"""
import io
import os
import re

SRC = '/home/z/my-project/kip8test'
DST = '/home/z/my-project/kip8'

fails = []


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


# --- 1. test-task532.js ---
t = rd(os.path.join(SRC, 'tests', 'test-task532.js'))
n1 = t.count('kipia-test-v745')
n2 = t.count('kipia-test-v746')
t = t.replace('kipia-test-v746', 'kipia-v543')
t = t.replace('kipia-test-v745', 'kipia-v542')
# шапка: пометка зеркала
t = t.replace('// tests/test-task532.js\n',
              '// tests/test-task532.js  (зеркало kip8test; SW kipia-v542)\n')
wr(os.path.join(DST, 'tests', 'test-task532.js'), t)
print('test-task532.js: v745→v542 ×%d, гварды v746→v543 ×%d' % (n1, n2))

tests_dir = os.path.join(DST, 'tests')
files = sorted(f for f in os.listdir(tests_dir) if f.endswith('.js'))

# --- 2. ГАРДЫ v542 → v543 (кроме НОВОГО) ---
g = 0
for f in files:
    if f == 'test-task532.js':
        continue
    p = os.path.join(tests_dir, f)
    s = rd(p)
    if 'kipia-v542' in s:
        g += s.count('kipia-v542')
        wr(p, s.replace('kipia-v542', 'kipia-v543'))
print('гарды v542→v543: ×%d' % g)

# --- 3. АССЕРТЫ v541 → v542 ---
a = 0
for f in files:
    if f == 'test-task532.js':
        continue
    p = os.path.join(tests_dir, f)
    s = rd(p)
    if 'kipia-v541' in s:
        a += s.count('kipia-v541')
        wr(p, s.replace('kipia-v541', 'kipia-v542'))
print('ассерты v541→v542: ×%d' % a)

# --- 4. sw.js ---
swp = os.path.join(DST, 'sw.js')
sw = rd(swp)
if sw.count('kipia-v541') != 1:
    fails.append('sw.js: kipia-v541 ×%d (ожидалось 1)' % sw.count('kipia-v541'))
else:
    wr(swp, sw.replace("const CACHE_VERSION = 'kipia-v541'",
                       "const CACHE_VERSION = 'kipia-v542'"))
    print('sw.js: CACHE_VERSION = kipia-v542')

# --- 5. регистрация в run-all.js ---
rap = os.path.join(tests_dir, 'run-all.js')
ra = rd(rap)
if "require('./test-task532.js');" in ra:
    print('уже зарегистрирован')
elif "require('./test-task531.js');" in ra:
    anchor = "require('./test-task531.js');\n"
    add = ("// Task 532: LCD-информер — шестерёнка с настройками (клик по окну —\n"
           "// только календарь), выбор года, диагностика погоды + резервный\n"
           "// источник open-meteo, аудит кириллицы FONT5.\n")
    wr(rap, ra.replace(anchor, anchor + add + "require('./test-task532.js');\n"))
    print('test-task532.js зарегистрирован')
else:
    fails.append('run-all.js: якорь test-task531.js не найден')

# --- 6. браузер-скрипт kip8-вариант ---
b = rd(os.path.join(SRC, 'scripts', 'task532-browser-check.py'))
b = b.replace('PORT = 8999', 'PORT = 8996')
b = b.replace("REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
              "REPO = '/home/z/my-project/kip8'")
b = b.replace("'download', 'kip8test-task532'", "'download', 'kip8-task532'")
b = b.replace("'kip8test:kip8_session_token'", "'kip8_session_token'")
b = b.replace("'kip8test:app-theme'", "'app-theme'")
b = b.replace('bc-t532', 'bc-t532k8')
wr(os.path.join(DST, 'scripts', 'task532-browser-check-kip8.py'), b)
print('task532-browser-check-kip8.py записан')

if fails:
    print('ОШИБКИ:')
    for f in fails:
        print('  ! ' + f)
    raise SystemExit(1)
print('OK')
