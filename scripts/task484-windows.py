#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 484: расширение окон истории sw.js в тестах.

Комментарий Task 484 в шапке sw.js (~390 симв., вставлен ПЕРЕД
const CACHE_VERSION) отодвинул все предыдущие якоря комментариев:
  Task 483 ~292 (окно 700 — влезает); Task 482 ~1090 (окно 1500 —
  влезает, но окно «не-вытеснения 481/480» ловит Task 480 ~1595);
  Task 481 ~1351 (СОБСТВЕННОЕ окно 1100 — ВЫЛЕТЕЛО); Task 480
  ~1595 (окно 1500 — вылетело); Task 479 ~1609 (окно 2100 — ок);
  Task 478 ~2189 (окно 2100 — вылетело); якоря 474/472/471/461:
  ~3731/~4104/~4653/~7215 против окон 3500/4000/4600/7200.

Расширения (запас 164+):
  478: окно комментария 2100 → 2500; 480: 1500 → 2100;
  481: собственное 1100 → 1500, w700 (Task 480) 1500 → 2100,
       w1400 (Task 478) 2100 → 2500;
  482: окна 1500 → 2100 (×2: собственное + не-вытеснение) и
       2100 → 2500 (Task 478);
  якорные окна 3500 → 4000, 4000 → 4500, 4600 → 5000, 7200 → 7600
  (в 478/479/481/482/476/477);
  литералы test-task475 §9, каскады test-task481/test-task482
  синхронизированы (прецедент task483-windows.py).

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
        if n == 0 and new in src:
            print(f'  {fname}: УЖЕ применено {old[:44]!r}')
            continue
        assert n >= 1, f'{fname}: не найдено {old!r}'
        src = src.replace(old, new)
        print(f'  {fname}: {old[:58]!r} x{n}')
    p.write_text(src, encoding='utf-8')


# --- 1. Собственные окна комментариев своих задач (SW_SRC) ---
rep('test-task481.js', [
    # собственное окно комментария Task 481 (было 1100, якорь ~1351)
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1100), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 1500), i);"),
    # w700 (окно «Task 480 не вытеснен»): Task 480 ушёл на ~1595
    ("const w700 = SW_SRC.slice(Math.max(0, i - 1500), i);",
     "const w700 = SW_SRC.slice(Math.max(0, i - 2100), i);"),
    # w1400 (Task 478 не вытеснен): ушёл на ~2189
    ("const w1400 = SW_SRC.slice(Math.max(0, i - 2100), i);",
     "const w1400 = SW_SRC.slice(Math.max(0, i - 2500), i);"),
])
rep('test-task478.js', [
    # комментарий Task 478 ушёл на ~2189
    ("const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 2500), i);"),
])
rep('test-task479.js', [
    # УРОК прогона: окно 479 проверяет и «Task 478 не вытеснен» —
    # его комментарий на ~2189 ВЫЛЕТЕЛ из 2100; расширяем до 2500
    ("const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 2500), i);"),
])
# каскад: литерал s479 в test-task482 синхронизирован на 2500
rep('test-task480.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1500), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);"),
    ("test('комментарий Task 480 в шапке версий (окно 1100 → 1500, Task 483)', () => {",
     "test('комментарий Task 480 в шапке версий (окно 1500 → 2100, Task 484)', () => {"),
])
rep('test-task482.js', [
    # ВАЖНО: якорь окна Task 479/478 — с ЗАГОЛОВКОМ теста (литерал
    # 'i - 2100' общий для трёх окон; замена без контекстного якоря
    # в одном прогоне перехватывает литералы, созданные парой ниже —
    # урок этого прогона: 634/647 пришлось возвращать вручную).
    # Версия в якоре — v708 ПОСЛЕ бампа (скрипт запускается и после;
    # пары идемпотентны через гвард «УЖЕ применено»)
    ("test('комментарии Task 479/478 не вытеснены (окно 1700)', () => {\n        const i = SW_SRC.indexOf(\"const CACHE_VERSION = 'kipia-test-v708';\");\n        const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);",
     "test('комментарии Task 479/478 не вытеснены (окно 2500)', () => {\n        const i = SW_SRC.indexOf(\"const CACHE_VERSION = 'kipia-test-v708';\");\n        const ctx = SW_SRC.slice(Math.max(0, i - 2500), i);"),
    # ×2: собственное окно (Task 482 ~1090, было 1500) + окно
    # «не-вытеснение 481/480» (Task 480 ~1595 > 1500)
    ("const ctx = SW_SRC.slice(Math.max(0, i - 1500), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);"),
])

# --- 2. Якорные окна 474/472/471/461 (478/479/481/482/476/477) ---
ANCH_MSG = [
    ("(i - i474) < 3500", "(i - i474) < 4000"),
    ("(i - i472) < 4000", "(i - i472) < 4500"),
    ("(i - i471) < 4600", "(i - i471) < 5000"),
    ("(i - i461) < 7200", "(i - i461) < 7600"),
]
ANCH_MSG_TXT = [
    ("'Task 474 в окне 3500'", "'Task 474 в окне 4000'"),
    ("'Task 472 в окне 4000'", "'Task 472 в окне 4500'"),
    ("'Task 471 в окне 4600'", "'Task 471 в окне 5000'"),
    ("'Task 461 в окне 7200'", "'Task 461 в окне 7600'"),
    # 478 называет якорь 474 «Task 478 в окне …» — историческое имя
    ("'Task 478 в окне 3500'", "'Task 478 в окне 4000'"),
]
for f in ('test-task478.js', 'test-task479.js', 'test-task481.js', 'test-task482.js'):
    src = (T / f).read_text(encoding='utf-8')
    pairs = [p for p in ANCH_MSG + ANCH_MSG_TXT if p[0] in src]
    rep(f, pairs)

rep('test-task476.js', [
    ("assertTrue(i474 !== -1 && (i - i474) < 3500, 'якорь Task 474 виден');",
     "assertTrue(i474 !== -1 && (i - i474) < 4000, 'якорь Task 474 виден');"),
    ("assertTrue(i472 !== -1 && (i - i472) < 4000, 'якорь Task 472 виден');",
     "assertTrue(i472 !== -1 && (i - i472) < 4500, 'якорь Task 472 виден');"),
    ("assertTrue(i471 !== -1 && (i - i471) < 4600, 'якорь Task 471 виден');",
     "assertTrue(i471 !== -1 && (i - i471) < 5000, 'якорь Task 471 виден');"),
    ("assertTrue(i461 !== -1 && (i - i461) < 7200, 'якорь Task 461 виден');",
     "assertTrue(i461 !== -1 && (i - i461) < 7600, 'якорь Task 461 виден');"),
    ("    // расширены scripts/task483-windows.py (3100→3500/3600→4000/\n    // 4200→4600/6800→7200), заголовки тестов исторические.",
     "    // расширены scripts/task483-windows.py (3100→3500/3600→4000/\n    // 4200→4600/6800→7200) и task484-windows.py (3500→4000/\n    // 4000→4500/4600→5000/7200→7600), заголовки исторические."),
])
rep('test-task477.js', [
    ("assertTrue(i474 !== -1 && (i - i474) < 3500, 'Task 474 (~3341) в окне 3500');",
     "assertTrue(i474 !== -1 && (i - i474) < 4000, 'Task 474 (~3731) в окне 4000');"),
    ("assertTrue(i472 !== -1 && (i - i472) < 4000, 'Task 472 (~3714) в окне 4000');",
     "assertTrue(i472 !== -1 && (i - i472) < 4500, 'Task 472 (~4104) в окне 4500');"),
    ("assertTrue(i471 !== -1 && (i - i471) < 4600, 'Task 471 (~4263) в окне 4600');",
     "assertTrue(i471 !== -1 && (i - i471) < 5000, 'Task 471 (~4653) в окне 5000');"),
    ("assertTrue(i461 !== -1 && (i - i461) < 7200, 'Task 461 (~6825) в окне 7200');",
     "assertTrue(i461 !== -1 && (i - i461) < 7600, 'Task 461 (~7215) в окне 7600');"),
    ("        // Task 483: комментарий ~378 симв. — 3100→3500/3600→4000/\n        // 4200→4600/6800→7200 (scripts/task483-windows.py).",
     "        // Task 483: ~378 симв. — 3100→3500/3600→4000/4200→4600/\n        // 6800→7200; Task 484: ~390 симв. — 3500→4000/4000→4500/\n        // 4600→5000/7200→7600 (windows-скрипты задач)."),
])

# --- 3. Окна своих якорей в 461/471/472/474 ---
rep('test-task461.js', [
    ("const above = SW_SRC.slice(Math.max(0, i - 7200), i);",
     "const above = SW_SRC.slice(Math.max(0, i - 7600), i);"),
])
rep('test-task471.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 4600), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 5000), i);"),
])
rep('test-task472.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 4000), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 4500), i);"),
    ("const ctx = SW_SRC.slice(Math.max(0, i - 4600), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 5000), i);"),
])
rep('test-task474.js', [
    ("const ctx = SW_SRC.slice(Math.max(0, i - 3500), i);",
     "const ctx = SW_SRC.slice(Math.max(0, i - 4000), i);"),
])

# --- 4. Каскад: test-task475 §9 (литералы чужих окон) ---
rep('test-task475.js', [
    ("s.indexOf('i - 7200') !== -1, 'окно расширено до 7200'",
     "s.indexOf('i - 7600') !== -1, 'окно расширено до 7600'"),
    ("s1.indexOf('i - 4600') !== -1, 'test-task471: 4600'",
     "s1.indexOf('i - 5000') !== -1, 'test-task471: 5000'"),
    ("s2.indexOf('i - 4600') !== -1, 'test-task472: 4600'",
     "s2.indexOf('i - 5000') !== -1, 'test-task472: 5000'"),
    ("s.indexOf('i - 4000') !== -1, 'окно Task 472: 4000'",
     "s.indexOf('i - 4500') !== -1, 'окно Task 472: 4500'"),
    ("s.indexOf('i - 3500') !== -1, 'окно Task 474: 3500'",
     "s.indexOf('i - 4000') !== -1, 'окно Task 474: 4000'"),
])

# --- 5. Каскад: test-task481 §синхронизация (литералы 461/471/472/474) ---
rep('test-task481.js', [
    ("s461.indexOf('i - 7200') !== -1, 'test-task461: окно 7200'",
     "s461.indexOf('i - 7600') !== -1, 'test-task461: окно 7600'"),
    ("s471.indexOf('i - 4600') !== -1, 'test-task471: окно 4600'",
     "s471.indexOf('i - 5000') !== -1, 'test-task471: окно 5000'"),
    ("s472.indexOf('i - 4000') !== -1, 'test-task472: окно 4000'",
     "s472.indexOf('i - 4500') !== -1, 'test-task472: окно 4500'"),
    ("s474.indexOf('i - 3500') !== -1, 'test-task474: окно 3500'",
     "s474.indexOf('i - 4000') !== -1, 'test-task474: окно 4000'"),
])

# --- 6. Каскад: test-task482 §каскад (литералы окон 478-481) ---
rep('test-task482.js', [
    ("s478.indexOf('i - 2100') !== -1, 'test-task478: окно 2100'",
     "s478.indexOf('i - 2500') !== -1, 'test-task478: окно 2500'"),
    ("s479.indexOf('i - 2100') !== -1, 'test-task479: окно 2100'",
     "s479.indexOf('i - 2500') !== -1, 'test-task479: окно 2500'"),
    ("s480.indexOf('i - 1500') !== -1, 'test-task480: окно 1500'",
     "s480.indexOf('i - 2100') !== -1, 'test-task480: окно 2100'"),
    ("s481.indexOf('i - 1100') !== -1 &&\n                   s481.indexOf('i - 1500') !== -1 &&\n                   s481.indexOf('i - 2100') !== -1,\n            'test-task481: окна 1100/1500/2100'",
     "s481.indexOf('i - 1500') !== -1 &&\n                   s481.indexOf('i - 2100') !== -1 &&\n                   s481.indexOf('i - 2500') !== -1,\n            'test-task481: окна 1500/2100/2500'"),
    ("        // scripts/task482-windows.py: 478/479 1400→1700; 480 700→1100;\n        // 481 w700→1100 + w1400→1700",
     "        // windows-скрипты 482/483/484: 478 2100→2500; 479 2100 (без изм.);\n        // 480 1500→2100; 481: 1500/2100/2500"),
])

print('\nOK: окна истории расширены (Task 484)')
