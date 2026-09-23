#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Проверка JS-синтаксиса всех inline <script>-блоков index.html
# (Task 401: санити после правок _fitTtDrawer/_renderTotalsYearTable).
import re, subprocess, sys

src = open('index.html', encoding='utf-8').read()
blocks = re.findall(r'<script>(.*?)</script>', src, re.S)
print('inline <script>-блоков: %d' % len(blocks))
ok = True
for i, b in enumerate(blocks):
    if not b.strip():
        continue
    p = '/tmp/t401_block_%d.js' % i
    open(p, 'w', encoding='utf-8').write(b)
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False
        print('БЛОК %d: ОШИБКА СИНТАКСИСА' % i)
        print(r.stderr[:1500])
    else:
        print('блок %d: OK (%d строк)' % (i, b.count('\n') + 1))
sys.exit(0 if ok else 1)
