#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 487: расширение ОКОН ИСТОРИИ sw.js в тестах.
# Комментарий Task 487 (~569 симв.) отодвинул якоря задач в шапке
# sw.js; дистанции от CACHE_VERSION ('kipia-test-v711'):
#   474 ~5592 (окно 5300 — ПРОВАЛ); 472 ~5965 (5900 — ПРОВАЛ);
#   471 ~6514 (6500 — ПРОВАЛ); 461 ~9076 (9100 — проходит, НО запас
#   всего 24 симв. против регламентных 100+ — расширяем превентивно).
# Новые значения (запасы ~400/500/500/700):
#   Task 474: 5300 → 6000; Task 472: 5900 → 6500;
#   Task 471: 6500 → 7000; Task 461: 9100 → 9800.
# Собственные окна задачи: 473 5600 → 6200 (якорь ~5704);
# 474 (двойное) — срез 5300 → 6000 (второе окно 471/461 —
# distance-форма); 471/472 срезы 6500 → 7000 / 5900 → 6500.
# Мета-ассерты (литералы 'i - N' в кавычках) синхронизированы:
#   test-task475.js §адаптация (461/471/472/474),
#   test-task481.js §мета (те же четыре),
#   test-task486.js §мета (каскад 475: 9100→9800; 481: 6500→7000).
# ПОРЯДОК ЗАМЕН ВАЖЕН: сначала 6500 → 7000 (иначе новые 6500 от
# 5900→6500 попадут под повторную замену); B-формы (срезы) — до
# C-форм (мета) в каждом файле.
# Прецедент: scripts/task482-windows.py (каскадная синхронизация).
import glob

OWN = 'tests/test-task487.js'

sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v711';" in sw
assert 'Task 487' in sw

# --- 1) A-форма: distance-ассерты (i - iNNN) < W ---
A = [
    ('(i - i471) < 6500', '(i - i471) < 7000'),
    ('(i - i472) < 5900', '(i - i472) < 6500'),
    ('(i - i474) < 5300', '(i - i474) < 6000'),
    ('(i - i461) < 9100', '(i - i461) < 9800'),
]
# --- 2) B-форма: срезы SW_SRC.slice(Math.max(0, i - N), i) ---
B = [
    ('Math.max(0, i - 6500)', 'Math.max(0, i - 7000)'),
    ('Math.max(0, i - 5900)', 'Math.max(0, i - 6500)'),
    ('Math.max(0, i - 5300)', 'Math.max(0, i - 6000)'),
    ('Math.max(0, i - 9100)', 'Math.max(0, i - 9800)'),
    ('Math.max(0, i - 5600)', 'Math.max(0, i - 6200)'),
]
stats = {}
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    for old, new in A + B:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            stats.setdefault(old + ' → ' + new, []).append((f, n))
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
for k, v in sorted(stats.items()):
    total = sum(n for _, n in v)
    print('%s: %d мест в %d файлах' % (k, total, len(v)))

# --- 3) C-форма: мета-ассерты (литералы в кавычках) ---
C = [
    # 475 и 481: одни и те же четыре литерала; 486: двойные кавычки
    ('tests/test-task475.js', [
        ("s1.indexOf('i - 6500')", "s1.indexOf('i - 7000')"),
        ("s2.indexOf('i - 6500')", "s2.indexOf('i - 7000')"),
        ("s.indexOf('i - 5900')", "s.indexOf('i - 6500')"),
        ("s.indexOf('i - 5300')", "s.indexOf('i - 6000')"),
        ("s.indexOf('i - 9100')", "s.indexOf('i - 9800')"),
    ]),
    ('tests/test-task481.js', [
        ("s471.indexOf('i - 6500')", "s471.indexOf('i - 7000')"),
        ("s472.indexOf('i - 5900')", "s472.indexOf('i - 6500')"),
        ("s474.indexOf('i - 5300')", "s474.indexOf('i - 6000')"),
        ("s461.indexOf('i - 9100')", "s461.indexOf('i - 9800')"),
    ]),
    ('tests/test-task486.js', [
        ('s475.indexOf("\'i - 9100\'")', 's475.indexOf("\'i - 9800\'")'),
        ('s481.indexOf("\'i - 6500\'")', 's481.indexOf("\'i - 7000\'")'),
    ]),
]
for f, rules in C:
    s = open(f, encoding='utf-8').read()
    for old, new in rules:
        if old in s:
            s = s.replace(old, new)
            print('%s: %s → %s' % (f, old, new))
    open(f, 'w', encoding='utf-8').write(s)

# --- 4) Сверка: старых литералов (вне OWN) не осталось ---
for pat in ['(i - i474) < 5300', '(i - i472) < 5900', '(i - i471) < 6500',
            '(i - i461) < 9100', 'Math.max(0, i - 5900)',
            'Math.max(0, i - 5300)', 'Math.max(0, i - 5600)']:
    leftover = [f for f in glob.glob('tests/*.js')
                if f.replace('\\', '/') != OWN and pat in open(f, encoding='utf-8').read()]
    assert not leftover, 'паттерн %r остался в: %r' % (pat, leftover)
print('tests: старые окна вычистились полностью')

# --- 5) Итоговые дистанции ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v711';")
for name in ['Task 474', 'Task 473', 'Task 472', 'Task 471', 'Task 461']:
    k = sw.rindex(name, 0, i)
    print('  %s: %d' % (name, i - k))
