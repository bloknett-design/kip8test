#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 483: расширение окон истории sw.js в тестах.

Комментарий Task 483 в шапке sw.js (~378 симв., вставлен ПЕРЕД
const CACHE_VERSION) отодвинул все предыдущие якоря комментариев:
  Task 482 ~700 (было ~322); Task 481 ~961 (было ~583 — вылетело из
  СОБСТВЕННОГО окна 700!); Task 480 ~1205 (окно 1100); Task 479
  ~1460; Task 478 ~1799 (окно 1700); якоря 474/472/471/461:
  3341/3714/4263/6825 против окон 3100/3600/4200/6800.

Расширения (запас 159+):
  478/479/482: окно комментария 1700 → 2100; 480/482/481(w700):
  1100 → 1500; 481 (собств. окно) 700 → 1100; 481 w1400 1700 → 2100;
  якорные окна 3100 → 3500, 3600 → 4000, 4200 → 4600, 6800 → 7200
  (в 478/479/481/482); литералы test-task475 §9 и каскадные проверки
  test-task482 §каскад синхронизированы (прецедент task481-windows.py).

Окна INDEX_SRC (index.html) НЕ трогаются — они про другой файл.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
T = ROOT / 'tests'


def rep(fname, pairs):
    p = T / fname
    src = p.read_text(encoding='utf-8')
    for old, new in pairs:
        n = src.count(old)
        assert n >= 1, f'{fname}: не найдено {old!r}'
        src = src.replace(old, new)
        print(f'  {fname}: {old!r} x{n} -> {new!r}')
    p.write_text(src, encoding='utf-8')


# --- 1. Окна комментариев своих задач (SW_SRC) ---
rep('test-task481.js', [
    # собственное окно комментария Task 481 (было 700, якорь ушёл на ~961)
    ("const ctx = SW_SRC.slice(Math.max(0, i - 700), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 1100), i);"),
])
rep('test-task481.js', [
    # w700 (окно «700»): Task 480 ушёл на ~1205
    ("const w700 = SW_SRC.slice(Math.max(0, i - 1100), i);",
     "const w700 = SW_SRC.slice(Math.max(0, i - 1500), i);"),
    # w1400: Task 478 ушёл на ~1799
    ("const w1400 = SW_SRC.slice(Math.max(0, i - 1700), i);",
     "const w1400 = SW_SRC.slice(Math.max(0, i - 2100), i);"),
])
rep('test-task478.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1700), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);"),
])
rep('test-task479.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1700), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);"),
])
rep('test-task480.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1100), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 1500), i);"),
])
rep('test-task482.js', [
    # ×2 (окна 1100: комментарий Task 482 + не-вытеснение 481/480)
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1100), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 1500), i);"),
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1700), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);"),
])

# --- 2. Окна якорей 474/472/471/461 (478/479/481/482) ---
ANCH = [
    ("(i - i474) < 3100", "(i - i474) < 3500"),
    ("(i - i472) < 3600", "(i - i472) < 4000"),
    ("(i - i471) < 4200", "(i - i471) < 4600"),
    ("(i - i461) < 6800", "(i - i461) < 7200"),
    ("'Task 474 в окне 3100'", "'Task 474 в окне 3500'"),
    ("'Task 472 в окне 3600'", "'Task 472 в окне 4000'"),
    ("'Task 471 в окне 4200'", "'Task 471 в окне 4600'"),
    ("'Task 461 в окне 6800'", "'Task 461 в окне 7200'"),
    # 478 называет якорь 474 «Task 478 в окне 3100» — историческое имя
    ("'Task 478 в окне 3100'", "'Task 478 в окне 3500'"),
]
for f in ('test-task478.js', 'test-task479.js', 'test-task481.js', 'test-task482.js'):
    rep(f, [p for p in ANCH if p[0] in (T / f).read_text(encoding='utf-8')])

# --- 3. Окна своих якорей в 461/471/472/474 ---
rep('test-task461.js', [
    ("const above = SW_SRC.slice(Math.max(0, i - 6800), i);",
     "const above = SW_SRC.slice(Math.max(0, i - 7200), i);"),
])
rep('test-task471.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 4200), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 4600), i);"),
])
rep('test-task472.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 3600), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 4000), i);"),
    ("const ctx = SW_SRC.slice(Math.max(0, i - 4200), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 4600), i);"),
])
rep('test-task474.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 3100), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 3500), i);"),
])

# --- 4. Каскад: test-task475 §9 (литералы чужих окон) ---
rep('test-task475.js', [
    ("s.indexOf('i - 6800') !== -1, 'окно расширено до 6800'",
     "s.indexOf('i - 7200') !== -1, 'окно расширено до 7200'"),
    ("s1.indexOf('i - 4200') !== -1, 'test-task471: 4200'",
     "s1.indexOf('i - 4600') !== -1, 'test-task471: 4600'"),
    ("s2.indexOf('i - 4200') !== -1, 'test-task472: 4200'",
     "s2.indexOf('i - 4600') !== -1, 'test-task472: 4600'"),
    ("s.indexOf('i - 3600') !== -1, 'окно Task 472: 3600'",
     "s.indexOf('i - 4000') !== -1, 'окно Task 472: 4000'"),
    ("s.indexOf('i - 3100') !== -1, 'окно Task 474: 3100'",
     "s.indexOf('i - 3500') !== -1, 'окно Task 474: 3500'"),
])

# --- 5. Каскад: test-task482 §каскад (литералы окон 478-481) ---
rep('test-task482.js', [
    ("s478.indexOf('i - 1700') !== -1, 'test-task478: окно 1700'",
     "s478.indexOf('i - 2100') !== -1, 'test-task478: окно 2100'"),
    ("s479.indexOf('i - 1700') !== -1, 'test-task479: окно 1700'",
     "s479.indexOf('i - 2100') !== -1, 'test-task479: окно 2100'"),
    ("s480.indexOf('i - 1100') !== -1, 'test-task480: окно 1100'",
     "s480.indexOf('i - 1500') !== -1, 'test-task480: окно 1500'"),
    ("s481.indexOf('i - 1100') !== -1 &&\n                   s481.indexOf('i - 1700') !== -1,\n            'test-task481: окна 1100/1700'",
     "s481.indexOf('i - 1100') !== -1 &&\n                   s481.indexOf('i - 1500') !== -1 &&\n                   s481.indexOf('i - 2100') !== -1,\n            'test-task481: окна 1100/1500/2100'"),
])

# --- 6. Комментарий у окна 480 (история расширений) ---
rep('test-task480.js', [
    ("test('комментарий Task 480 в шапке версий (окно 700)', () => {",
     "test('комментарий Task 480 в шапке версий (окно 1100 → 1500, Task 483)', () => {"),
])

# --- 7. ДОПОЛНЕНИЕ после первого прогона тестов: якорные окна в
#     test-task476.js §«окна истории» и test-task477.js §«границы и
#     окна» (те же якоря 474/472/471/461, литералы 3100/3600/4200/
#     6800) — применено ТЕ ЖЕ замены 3500/4000/4600/7200 (правки
#     внесены напрямую; этот блок — документация для воспроизведения) ---
#  test-task476.js: '(i - i474) < 3100' → '< 3500'; '(i - i472) < 3600'
#    → '< 4000'; '(i - i471) < 4200' → '< 4600'; '(i - i461) < 6800'
#    → '< 7200' + комментарий Task 483 у блока.
#  test-task477.js: те же четыре замены + заголовок теста и числа ~
#    в сообщениях ассертов.

print('\nOK: окна истории расширены (Task 483)')
