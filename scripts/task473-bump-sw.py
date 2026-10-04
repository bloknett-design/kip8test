#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 473: SW-бамп kipia-test-v696 → v697 (charts-desktop.js менялся —
# график ППР «Приборы» (Графики КИП ИОС → Приборы): КОРНЕВОЙ ФИКС
# зрительной невидимости столбцов (align-items:flex-end → stretch —
# height:% столбца схлопывался в min-height:2px) + значение над
# КАЖДЫМ столбцом каждого месяца («0» пустых месяцев у основания) +
# ВСПОМОГАТЕЛЬНАЯ ПРАВАЯ ОСЬ для малых серий К/П при ТО 320–500).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v697 → v698 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v698;
#   ЗАТЕМ v696 → v697 — ассерты «присутствует» едут на текущую.
# tests/test-task473.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v697 + guard v698 + v696 отсутствует).
import glob

OWN = 'tests/test-task473.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v696'"
new = "CACHE_VERSION = 'kipia-test-v697'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v696'
assert 'kipia-test-v697' not in sw, 'sw.js: v697 уже был (двойной бамп?)'
sw = sw.replace(old, new)

# Комментарий Task 473 в шапке (перед строкой-якорём после Task 472)
anchor = '// ВСЕГДА на одном уровне (обе колонки: скролл-зона + 5px + 12px).'
task473 = ('// Task 473: график ППР «Приборы» (только десктоп) — столбцы были\n'
           '// зрительно НЕвидимы (2px, схлопывание height:%); фикс + значение над\n'
           '// каждым столбцом каждого месяца (включая «0») + правая ось для К/П.\n')
assert anchor in sw, 'sw.js: не найден якорь вставки комментария'
assert 'Task 473' not in sw, 'sw.js: комментарий Task 473 уже есть'
sw = sw.replace(anchor, task473 + anchor, 1)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v696 -> kipia-test-v697 + комментарий Task 473')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v697 отсутствует» → «v698 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v697')
    s = s.replace('kipia-test-v697', 'kipia-test-v698')
    # 2) ассерты «v696 присутствует» → «v697 присутствует»
    n_assert = s.count('kipia-test-v696')
    s = s.replace('kipia-test-v696', 'kipia-test-v697')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed[:5]:
    print('  %s (ассерты v696->v697: %d, guard v697->v698: %d)' % (f, a, g))
print('  ... и ещё %d файлов' % max(0, len(changed) - 5))
