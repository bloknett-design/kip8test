#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 435 + 436: SW-бамп kipia-test-v660 → v661 (index.html
# менялся — карточки: РАЗДЕЛЬНЫЕ годы блоков «Мероприятия» и
# «Повторные инструктажи…» (fam 0/1, _wtabYear/_wtabYearInstr);
# график расходомеров: шкала двух групп 0–80/80–100).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v661 → v662
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v660 → v661.
# НОВЫЕ test-task435.js / test-task436.js уже ассертят v661 —
# они ИСКЛЮЧЕНЫ из замен (иначе guard-шаг их испортит).
# Исторические записи (worklog.md, DEPLOY-*.md, scripts/*.py) не
# переписываются. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v660'"
new = "CACHE_VERSION = 'kipia-test-v661'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v660'
assert 'kipia-test-v661' not in sw, 'sw.js: v661 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v660 -> kipia-test-v661')

# 2. tests/*.js — guard v661→v662, затем ассерты v660→v661
SKIP = {'tests/test-task435.js', 'tests/test-task436.js'}
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') in SKIP:
        print('  SKIP (новый тест уже на v661): %s' % f)
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v661')
    s = s.replace('kipia-test-v661', 'kipia-test-v662')
    n_assert = s.count('kipia-test-v660')
    s = s.replace('kipia-test-v660', 'kipia-test-v661')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v660→v661: %d, guard v661→v662: %d)' % (f, a, g))
