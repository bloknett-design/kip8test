#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 438: SW-бамп kipia-test-v661 → v662 (index.html менялся —
# печать табеля: шапка из двух строк, без сноски, без «Часов»,
# «Перераб.» — только дни, коды сокращённые; диалог предпросмотра:
# «Сохранить PDF» + «Сохранить Excel» вместо HTML-файла).
# Порядок замен в tests/ ВАЖЕН: СНАЧАЛА guard-ы v662 → v663
# (чтобы старые «ложный инкремент»-guards смотрели на новую
# несуществующую версию), ЗАТЕМ ассерты v661 → v662.
# НОВЫЙ test-task438.js ещё не создан (пишется после бампа с
# ассертами v662 сразу). Исторические записи (worklog.md,
# DEPLOY-*.md, scripts/*.py) не переписываются.
import glob

# 1. sw.js — CACHE_VERSION + комментарий Task 438
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v661'"
new = "CACHE_VERSION = 'kipia-test-v662'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v661'
assert 'kipia-test-v662' not in sw, 'sw.js: v662 уже был (двойной бамп?)'
sw = sw.replace(old, new)
marker = "// текст шапки/значений по центру; нижние бордюры шторки и сетки"
assert marker in sw, 'sw.js: не найдена точка вставки комментария'
sw = sw.replace(marker, marker +
    "\n// Task 438: печать табеля — шапка из двух строк («График работы» +"
    "\n// месяц/год · вид), сноска внизу и колонка «Часы» убраны, «Перераб.» —"
    "\n// только дни, перечень кодов — сокращённый (short); диалог"
    "\n// предпросмотра: «Сохранить PDF» (canvas→JPEG→PDF) и «Сохранить"
    "\n// Excel» (xlsx-писатель с цветными ячейками) вместо HTML-файла.")
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v661 -> kipia-test-v662 + комментарий')

# 2. tests/*.js — guard v662→v663, затем ассерты v661→v662
SKIP = {'tests/test-task438.js'}
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') in SKIP:
        print('  SKIP (новый тест уже на v662): %s' % f)
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v662')
    s = s.replace('kipia-test-v662', 'kipia-test-v663')
    n_assert = s.count('kipia-test-v661')
    s = s.replace('kipia-test-v661', 'kipia-test-v662')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v661→v662: %d, guard v662→v663: %d)' % (f, a, g))
