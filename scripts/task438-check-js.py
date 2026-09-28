#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Проверка синтаксиса всех inline <script>-блоков index.html
# (node --check по каждому блоку). Запуск из корня репо.
import re, subprocess, tempfile, os, sys

src = open('index.html', encoding='utf-8').read()
# блоки <script> без src= и без type=module/JSON
blocks = []
pos = 0
# настоящие теги — только с начала строки (без отступа-кода);
# упоминания <script> внутри JS-комментариев пропускаем
for m in re.finditer(r'^[ \t]*<script(\b[^>]*)>', src, re.M):
    attrs = m.group(1)
    if re.search(r'\bsrc\s*=', attrs):
        continue
    end = src.find('</script>', m.end())
    if end == -1:
        continue
    blocks.append(src[m.end():end])

print('найдено inline-блоков: %d' % len(blocks))
fails = 0
for i, b in enumerate(blocks):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                     encoding='utf-8') as f:
        f.write(b)
        tmp = f.name
    r = subprocess.run(['node', '--check', tmp],
                       capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode != 0:
        fails += 1
        print('=== БЛОК %d: ОШИБКА ===' % i)
        print(r.stderr[:2000])
print('итог: %d ошибок' % fails)
sys.exit(1 if fails else 0)
