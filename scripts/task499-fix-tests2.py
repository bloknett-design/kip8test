#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 499 (kip8test), фикс-итерация 2 — ДОП: окна sw.js (продолжение).

Первый прогон скрипта task499-fix-tests.py записал правки 371/372/494 и
упал на якоре 471 (порядок строк). Этот скрипт применяет ОСТАВШИЕСЯ
правки окон: 471, 472 (×2), 496, 497. Замеры от 'kipia-test-v723':
  471@11207 (окно 11200 — за границей на 7) → 12000;
  472@10658 (окно 10300) → 11200; контекст 471 (в 472) → 12000;
  496@1292 от const-строки (окно 900) → 1600; 497@1043 (окно 900) → 1300.
"""
import io

T = '/home/z/my-project/kip8test/tests/'


def apply(path, edits):
    s = io.open(path, encoding='utf-8').read()
    for name, old, new in edits:
        n = s.count(old)
        assert n == 1, 'ЯКОРЬ %s (%s): вхождений %d (ожидалось 1)' % (name, path, n)
        s = s.replace(old, new)
        print('  OK %s' % name)
    io.open(path, 'w', encoding='utf-8').write(s)


# ------------------------------ test-task471.js -----------------------
apply(T + 'test-task471.js', [
    ('471: окно 11200 → 12000',
     """        const ctx = SW_SRC.slice(Math.max(0, i - 11200), i);
        // Task 478: окно 2700 → 3400 — комментарий ППР-индикации""",
     """        // Task 499: окно 11200 → 12000 — комментарий плейсхолдеров
        // диапазонов (~430 симв.) отодвинул Task 471 до ~11207.
        const ctx = SW_SRC.slice(Math.max(0, i - 12000), i);
        // Task 478: окно 2700 → 3400 — комментарий ППР-индикации"""),
])

# ------------------------------ test-task472.js -----------------------
apply(T + 'test-task472.js', [
    ('472: окно комментария 10300 → 11200',
     """        // Task 497: комментарий избранного расходомеров (~200 симв.)
        // — якорь 472@9939 — окно 9900 → 10300 (запас 361).
        const ctx = SW_SRC.slice(Math.max(0, i - 10300), i);""",
     """        // Task 497: комментарий избранного расходомеров (~200 симв.)
        // — якорь 472@9939 — окно 9900 → 10300 (запас 361).
        // Task 499: комментарий плейсхолдеров диапазонов (~430 симв.)
        // — якорь 472@10658 — окно 10300 → 11200 (запас 542).
        const ctx = SW_SRC.slice(Math.max(0, i - 11200), i);"""),
    ('472: контекст 471 — окно 11200 → 12000',
     """        // Task 474 в шапке sw.js отодвинул начало комментария Task 471
        // (~1157 символов).
        const ctx = SW_SRC.slice(Math.max(0, i - 11200), i);""",
     """        // Task 474 в шапке sw.js отодвинул начало комментария Task 471
        // (~1157 символов).
        // Task 499: комментарий плейсхолдеров (~430 симв.) — якорь
        // 471@11207 — окно 11200 → 12000.
        const ctx = SW_SRC.slice(Math.max(0, i - 12000), i);"""),
])

# ------------------------------ test-task496.js -----------------------
apply(T + 'test-task496.js', [
    ('496: окно 900 → 1600',
     """        const i = SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v723';");
        const ctx = SW_SRC.slice(Math.max(0, i - 900), i);
        assertTrue(ctx.indexOf('Task 496') !== -1, 'маркер задачи');""",
     """        const i = SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v723';");
        // Task 499: комментарий плейсхолдеров диапазонов (~430 симв.)
        // отодвинул Task 496 до ~1292 — окно 900 → 1600.
        const ctx = SW_SRC.slice(Math.max(0, i - 1600), i);
        assertTrue(ctx.indexOf('Task 496') !== -1, 'маркер задачи');"""),
])

# ------------------------------ test-task497.js -----------------------
apply(T + 'test-task497.js', [
    ('497: окно 900 → 1300',
     """        const i = SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v723';");
        const ctx = SW_SRC.slice(Math.max(0, i - 900), i);
        assertTrue(ctx.indexOf('Task 497') !== -1, 'маркер задачи');""",
     """        const i = SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v723';");
        // Task 499: комментарий плейсхолдеров диапазонов (~430 симв.)
        // отодвинул Task 497 до ~1043 — окно 900 → 1300.
        const ctx = SW_SRC.slice(Math.max(0, i - 1300), i);
        assertTrue(ctx.indexOf('Task 497') !== -1, 'маркер задачи');"""),
])

print('Task 499 фикс-итерация 2 (доп): применена.')
