#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 508: проверка синтаксиса inline-скриптов index.html (паттерн
tmp/task504-syntax*.js: вырезаем <script> без src → node --check)."""
import io
import re
import subprocess
import sys

ROOT = '/home/z/my-project/kip8test'
src = io.open(ROOT + '/index.html', encoding='utf-8').read()

# вырезать script-блоки без src
blocks = []
for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',
                     src, re.S | re.I):
    body = m.group(1)
    if body.strip():
        blocks.append(body)
print('script-блоков: %d' % len(blocks))

js = '\n;\n'.join(blocks)
out = ROOT + '/tmp/task508-syntax.js'
io.open(out, 'w', encoding='utf-8').write(js)
r = subprocess.run(['node', '--check', out], capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[:3000])
    sys.exit(1)
print('SYNTAX OK')
