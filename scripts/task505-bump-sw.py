#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 505: SW-бамп kipia-test-v727 → v728 (kipia-test-v728).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v728 → v729
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v727 → v728.
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Новый test-task505.js уже под v728 — его тоже не
# трогаем (guard v729 там нет, ассерт v727 нет).
# Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION (УЖЕ поднят вручную вместе с комментарием
#    Task 505; скрипт проверяет состояние и не делает двойной бамп)
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
assert "CACHE_VERSION = 'kipia-test-v728'" in sw, \
    'sw.js: CACHE_VERSION должен быть kipia-test-v728'
assert 'kipia-test-v729' not in sw, 'sw.js: v729 уже есть (двойной бамп?)'
print('sw.js: CACHE_VERSION kipia-test-v727 -> kipia-test-v728 (уже поднят)')

# 2. tests/*.js — guard v728→v729, затем ассерты v727→v728
#    test-task505.js исключён: его ассерты уже под v728
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/').endswith('tests/test-task505.js'):
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v728')
    s = s.replace('kipia-test-v728', 'kipia-test-v729')
    n_assert = s.count('kipia-test-v727')
    s = s.replace('kipia-test-v727', 'kipia-test-v728')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
total_a = 0
total_g = 0
for f, a, g in changed:
    total_a += a
    total_g += g
    print('  %s (ассерты v727→v728: %d, guard v728→v729: %d)' % (f, a, g))
print('итого: ассерты %d, guards %d' % (total_a, total_g))
