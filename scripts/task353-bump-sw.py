#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 353: SW-бамп kipia-test-v582 → v583 (index.html менялся —
# кнопка «Удалить» + модалка подтверждения в админ-панели, опция
# фильтра журнала ADMIN_DELETE_USER).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v583 → v584
# (чтобы старые guards смотрели на новую несуществующую версию),
# ЗАТЕМ ассерты v582 → v583.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
# NOTE: test-task353.js пишется ПОСЛЕ этого скрипта (guard v584 в нём
# уже актуален), поэтому скрипт его не тронет: v583 в нём — ассерт,
# и он появляется ПОСЛЕ замен этого скрипта.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v582'"
new = "CACHE_VERSION = 'kipia-test-v583'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v582'
assert 'kipia-test-v583' not in sw, 'sw.js: v583 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v582 -> kipia-test-v583')

# 2. tests/*.js — guard v583→v584, затем ассерты v582→v583
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v583')
    s = s.replace('kipia-test-v583', 'kipia-test-v584')
    n_assert = s.count('kipia-test-v582')
    s = s.replace('kipia-test-v582', 'kipia-test-v583')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v582→v583: %d, guard v583→v584: %d)' % (f, a, g))
