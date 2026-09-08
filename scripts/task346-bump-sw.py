#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 346: SW-бамп kipia-test-v581 → v582 (index.html менялся —
# device в verifyOTP, тост evicted, бейдж админ-панели).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v582 → v583
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v581 → v582.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v581'"
new = "CACHE_VERSION = 'kipia-test-v582'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v581'
assert 'kipia-test-v582' not in sw, 'sw.js: v582 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v581 -> kipia-test-v582')

# 2. tests/*.js — guard v582→v583, затем ассерты v581→v582
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v582')
    s = s.replace('kipia-test-v582', 'kipia-test-v583')
    n_assert = s.count('kipia-test-v581')
    s = s.replace('kipia-test-v581', 'kipia-test-v582')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v581→v582: %d, guard v582→v583: %d)' % (f, a, g))
