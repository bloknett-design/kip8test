#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 489: расширение ОКОН ИСТОРИИ sw.js в тестах.
# Комментарий Task 489 (12 строк, ~752 симв.) отодвинул якоря задач
# в шапке sw.js; дистанции от литерала версии ('kipia-test-v713',
# indexOf-позиция — на 23 симв. правее const):
#   461 ~10601 (окно 10600 — ПРОВАЛ, запас −1);
#   471 ~8039 (8000 — ПРОВАЛ); 472 ~7490 (7500 — запас 10, тонко);
#   473 ~7229 (7200 — ПРОВАЛ); 474 ~7117 (7000 — ПРОВАЛ);
#   478 ~5575 (5600 — запас 25, тонко).
# Новые значения (запасы ~800-1000):
#   461: 10600 → 11600; 471: 8000 → 9000; 472: 7500 → 8500;
#   473: 7200 → 8200; 474: 7000 → 8000; 478/479: 5600 → 6500.
# ПОРЯДОК ЗАМЕН ВАЖЕН (уроки 482/486/487/488): СНАЧАЛА БОЛЬШИЕ
# исходные числа УБЫВАНИЕМ: 8000 → 9000 ДО 7000 → 8000 (иначе
# новые 8000 попадут под повторную замену); C-формы (мета-
# литералы в кавычках — тесты 475/481/482/486 сверяют ОКНА ДРУГИХ
# файлов) — тем же убывающим порядком ПОСЛЕ B-форм.
import glob

OWN = 'tests/test-task489.js'

sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v713';" in sw
assert 'Task 489' in sw
print('sw.js: v713 + Task 489 — OK')

# --- B-форма: срезы и дистанции (реальные окна) ---
B = [
    # ПОРЯДОК: убывание исходного значения!
    ('(i - i461) < 10600', '(i - i461) < 11600'),
    ('Math.max(0, i - 10600)', 'Math.max(0, i - 11600)'),
    ('(i - i471) < 8000', '(i - i471) < 9000'),
    ('Math.max(0, i - 8000)', 'Math.max(0, i - 9000)'),
    ('(i - i472) < 7500', '(i - i472) < 8500'),
    ('Math.max(0, i - 7500)', 'Math.max(0, i - 8500)'),
    ('Math.max(0, i - 7200)', 'Math.max(0, i - 8200)'),
    ('(i - i474) < 7000', '(i - i474) < 8000'),
    ('Math.max(0, i - 7000)', 'Math.max(0, i - 8000)'),
    ('Math.max(0, i - 5600)', 'Math.max(0, i - 6500)'),
]

stats = {}
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    for old, new in B:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            stats.setdefault(old + ' → ' + new, []).append((f, n))
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
total_b = 0
for k, v in sorted(stats.items()):
    t = sum(n for _, n in v)
    total_b += t
    print('B: %s: %d мест в %d файлах' % (k, t, len(v)))
print('B-форм всего: %d' % total_b)

# --- C-форма: мета-литералы (в кавычках) — окна ДРУГИХ файлов ---
C = [
    # тот же убывающий порядок!
    ("'i - 10600'", "'i - 11600'"),
    ('"i - 10600"', '"i - 11600"'),
    ("'i - 8000'", "'i - 9000'"),
    ('"i - 8000"', '"i - 9000"'),
    ("'i - 7500'", "'i - 8500'"),
    ('"i - 7500"', '"i - 8500"'),
    ("'i - 7200'", "'i - 8200'"),
    ('"i - 7200"', '"i - 8200"'),
    ("'i - 7000'", "'i - 8000'"),
    ('"i - 7000"', '"i - 8000"'),
    ("'i - 5600'", "'i - 6500'"),
    ('"i - 5600"', '"i - 6500"'),
]

stats_c = {}
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    for old, new in C:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            stats_c.setdefault(old + ' → ' + new, []).append((f, n))
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
total_c = 0
for k, v in sorted(stats_c.items()):
    t = sum(n for _, n in v)
    total_c += t
    print('C: %s: %d мест в %d файлах' % (k, t, len(v)))
print('C-форм всего: %d' % total_c)

# --- Сверка: старых окон не осталось (кроме OWN; НОВОЕ окно 474
#     равно 8000 — не путать со старым окном 471, которое уехало
#     в 9000 первой же заменой убывающего порядка) ---
left = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    for old in ['(i - i461) < 10600', 'Math.max(0, i - 10600)',
                '(i - i471) < 8000',
                'Math.max(0, i - 7500)', '(i - i472) < 7500',
                'Math.max(0, i - 7200)', '(i - i474) < 7000',
                'Math.max(0, i - 7000)', 'Math.max(0, i - 5600)']:
        if old in s:
            left.append((f, old))
assert not left, 'остались старые окна: %r' % left[:5]
print('ОКНА Подняты: 461→11600, 471→9000, 472→8500, 473→8200, '
      '474→8000, 478/479→6500.')

# --- Дозамена (после прогона): 485/486/488 — собственные окна ---
# 485 ~3383 (3100 — ПРОВАЛ); 486 ~2685 (2400 — ПРОВАЛ);
# 488 ~1522, его тело (docProps ~1071) за окном 900 — ПРОВАЛ
B2 = [
    ('Math.max(0, i - 3100)', 'Math.max(0, i - 4100)'),
    ('Math.max(0, i - 2400)', 'Math.max(0, i - 3400)'),
    ('Math.max(0, i - 900)', 'Math.max(0, i - 1800)'),
]
C2 = [
    ("'i - 3100'", "'i - 4100'"),
    ("'i - 2400'", "'i - 3400'"),
    ("'i - 900'", "'i - 1800'"),
]
n2 = 0
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    for old, new in B2 + C2:
        n2 += s.count(old)
        s = s.replace(old, new)
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
print('Дозамена 485/486/488: %d мест' % n2)
print('ОКНА-2: 485→4100, 486→3400, 488→1800.')
