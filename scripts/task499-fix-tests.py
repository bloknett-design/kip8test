#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 499 (kip8test), фикс-итерация 2: тесты + окна sw.js.

Первый прогон (после бампа) — 13 падений, все объяснимы:
  (1) тесты 371/372/494 — значения/окна под новую геометрию:
      - 371: тост t=250 теперь «-180 … 200» (диапазон 50М расширен);
      - 372: диапазон каталога cu50_1428 = {"min":-180,"max":200};
      - 494: openTempSensor вырос (~900 симв. блок 499) — срез
        fn = slice(i, i+3000) не достаёт до плейсхолдер-кода (позиции
        fmtI499@3301 / fmtM499@3606) → 3000 → 4500;
  (2) окна sw.js (комментарий Task 499 ~430 симв. перед CACHE_VERSION
      отодвинул маркеры; замеры от 'kipia-test-v723'):
      - 471: 'Task 471'@11207 (окно 11200, за границей на 7!) → 12000;
      - 472: 'Task 472'@10658 (окно 10300) → 11200;
      - «контекст 471» (в 472): то же окно 11200 → 12000;
      - 496: 'Task 496'@1292 от const-строки (окно 900) → 1600;
      - 497: 'Task 497'@1043 (окно 900) → 1300.
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


# ------------------------------ test-task371.js -----------------------
apply(T + 'test-task371.js', [
    ('371: тост t=250 — границы −180',
     """        assertTrue(vmw.toasts.length === 1 &&
            vmw.toasts[0].indexOf('Температура вне диапазона НСХ') !== -1 &&
            vmw.toasts[0].indexOf('-50') !== -1 && vmw.toasts[0].indexOf('200') !== -1,
            'тост с границами: ' + (vmw.toasts[0] || '—'));""",
     """        // Task 499: диапазон Cu 0,00428 расширен — тост «-180 … 200»
        assertTrue(vmw.toasts.length === 1 &&
            vmw.toasts[0].indexOf('Температура вне диапазона НСХ') !== -1 &&
            vmw.toasts[0].indexOf('-180') !== -1 && vmw.toasts[0].indexOf('200') !== -1,
            'тост с границами: ' + (vmw.toasts[0] || '—'));"""),
])

# ------------------------------ test-task372.js -----------------------
apply(T + 'test-task372.js', [
    ('372: диапазон cu50_1428 = −180…200',
     """        assertEqual(JSON.stringify(byKey['cu50_1428'].range), '{"min":-50,"max":200}', 'Cu50');
        assertEqual(JSON.stringify(byKey['pt100_1385'].range), '{"min":-200,"max":850}', 'Pt100');""",
     """        // Task 499: Cu α = 0,00428 — −180…+200 (ГОСТ 6651-2009, А.3/5.2.3)
        assertEqual(JSON.stringify(byKey['cu50_1428'].range), '{"min":-180,"max":200}', 'Cu50 0,00428');
        assertEqual(JSON.stringify(byKey['cu50_1426'].range), '{"min":-50,"max":200}', 'Cu50 0,00426');
        assertEqual(JSON.stringify(byKey['pt100_1385'].range), '{"min":-200,"max":850}', 'Pt100');"""),
])

# ------------------------------ test-task494.js -----------------------
apply(T + 'test-task494.js', [
    ('494: срез openTempSensor 3000 → 4500',
     """        const i = INDEX_SRC.indexOf('function openTempSensor(');
        assertTrue(i !== -1, 'функция openTempSensor есть');
        const fn = INDEX_SRC.slice(i, i + 3000);""",
     """        const i = INDEX_SRC.indexOf('function openTempSensor(');
        assertTrue(i !== -1, 'функция openTempSensor есть');
        // Task 499: блок плейсхолдеров диапазонов (~3300-3600 от начала
        // функции) — срез расширен 3000 → 4500
        const fn = INDEX_SRC.slice(i, i + 4500);"""),
])

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
        const ctx = SW_SRC.slice(Math.max(0, i - 11200), i);
        assertTrue(ctx.indexOf('Task 471') !== -1,
            'комментарий Task 471 остаётся в окне версий');""",
     """        // Task 474 в шапке sw.js отодвинул начало комментария Task 471
        // (~1157 символов).
        // Task 499: комментарий плейсхолдеров (~430 симв.) — якорь
        // 471@11207 — окно 11200 → 12000.
        const ctx = SW_SRC.slice(Math.max(0, i - 12000), i);
        assertTrue(ctx.indexOf('Task 471') !== -1,
            'комментарий Task 471 остаётся в окне версий');"""),
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

print('Task 499 фикс-итерация 2: применена.')
