#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 495 — kip8test: окна истории sw.js в тестах.

Комментарий Task 495 (~287 симв. перед CACHE_VERSION) отодвинул якори
(замер scripts/task495-windows-diag.js, i = позиция CACHE_VERSION
23443; для 471/472 — v-строка 23466):

  461 12474 (12400 — вылетело) | 471 9912/9935 (9800) | 472 9363/9386
  (9300) | 473 9102 (9000) | 474 8990 (8800 — в якорях-блоках) |
  478 7448 (7300) | 479 6868 ✓ (но нужен 478@7448 в том же окне) |
  480 6854 (6800) | 481 6610 ✓ (собств. окно живо) | 482 3829 +
  _barExpMaxH 6259 (6100) | 483 5551 (5400) | 484 5646 (5500) |
  485 5256 (5100) | 486 4558 (4400) | 488 3395 (3200).

Расширения (запас 570-730):
  461: 12400 → 13200 | 471: 9800 → 10600 | 472: 9300 → 9900,
  ctx471 9800 → 10600 | 473: 9000 → 9700 | 478/479: 7300 → 8100 |
  480: 6800 → 7500 | 481: w700 6800 → 7500, w1400 7300 → 8100
  (собств. 6800 жив — якорь 6610) | 482: 6100 → 6900, 6800 → 7500,
  7300 → 8100 | 483: 5400 → 6200 | 484: 5500 → 6300 | 485: 5100 →
  5900 | 486: 4400 → 5200 | 488: 3200 → 4000.

ЯКОРЯ-БЛОКИ «474/472/471/461» (LIMITS) в 7 тестах: 474 8800→9600,
  472 9400→10000 (запас), 471 9800→10600, 461 12400→13200.

КАСКАДЫ (тесты читают литералы окон ДРУГИХ тестов):
  475: s461 'i - 12400' → 'i - 13200'; s471/s472-ctx 'i - 9800' →
       'i - 10600'; s472 'i - 9300' → 'i - 9900';
  481: s461/s471/s472 — те же значения;
  482: s478/s479 'i - 7300' → 'i - 8100'; s480 'i - 6800' →
       'i - 7500'; s481 w1400 'i - 7300' → 'i - 8100' (s481
       'i - 6800' жив — собств. окно 481 не менялось);
  486: s475 "'i - 12400'" → "'i - 13200'"; s482 "'i - 7300'" →
       "'i - 8100'"; s484 'i - 5500' → 'i - 6300'.
"""
import io
import sys

T = '/home/z/my-project/kip8test/tests'
OK = True


def rep(fname, pairs):
    global OK
    p = T + '/' + fname
    src = io.open(p, encoding='utf-8').read()
    for old, new, cnt in pairs:
        n = src.count(old)
        if n != cnt:
            print('FAIL %s: %r найдено %d (ожидалось %d)' %
                  (fname, old[:56], n, cnt))
            OK = False
            continue
        src = src.replace(old, new)
        print('  %-18s %r x%d' % (fname, old[:48], n))
    io.open(p, 'w', encoding='utf-8').write(src)


LIMITS = [
    ('(i - i474) < 8800', '(i - i474) < 9600', 1),
    ('(i - i472) < 9400', '(i - i472) < 10000', 1),
    ('(i - i471) < 9800', '(i - i471) < 10600', 1),
    ('(i - i461) < 12400', '(i - i461) < 13200', 1),
]

# --- Собственные окна -----------------------------------------------
rep('test-task461.js', [
    ('SW_SRC.slice(Math.max(0, i - 12400), i)',
     'SW_SRC.slice(Math.max(0, i - 13200), i)', 1),
])
rep('test-task471.js', [
    ('SW_SRC.slice(Math.max(0, i - 9800), i)',
     'SW_SRC.slice(Math.max(0, i - 10600), i)', 1),
])
rep('test-task472.js', [
    ('SW_SRC.slice(Math.max(0, i - 9300), i)',
     'SW_SRC.slice(Math.max(0, i - 9900), i)', 1),
    ('SW_SRC.slice(Math.max(0, i - 9800), i)',
     'SW_SRC.slice(Math.max(0, i - 10600), i)', 1),
])
rep('test-task473.js', [
    ('SW_SRC.slice(Math.max(0, i - 9000), i)',
     'SW_SRC.slice(Math.max(0, i - 9700), i)', 1),
])
rep('test-task474.js', LIMITS)
rep('test-task476.js', LIMITS)
rep('test-task477.js', LIMITS)
rep('test-task478.js', [
    ('SW_SRC.slice(Math.max(0, i - 7300), i)',
     'SW_SRC.slice(Math.max(0, i - 8100), i)', 1),
] + LIMITS)
rep('test-task479.js', [
    ('SW_SRC.slice(Math.max(0, i - 7300), i)',
     'SW_SRC.slice(Math.max(0, i - 8100), i)', 1),
] + LIMITS)
rep('test-task480.js', [
    ('SW_SRC.slice(Math.max(0, i - 6800), i)',
     'SW_SRC.slice(Math.max(0, i - 7500), i)', 1),
])
rep('test-task481.js', [
    # w700 (якорь 480@6854); собств. окно 6800 (якорь 481@6610) НЕ трогаем
    ('const w700 = SW_SRC.slice(Math.max(0, i - 6800), i);',
     'const w700 = SW_SRC.slice(Math.max(0, i - 7500), i);', 1),
    ('const w1400 = SW_SRC.slice(Math.max(0, i - 7300), i);',
     'const w1400 = SW_SRC.slice(Math.max(0, i - 8100), i);', 1),
] + LIMITS)
rep('test-task482.js', [
    ('SW_SRC.slice(Math.max(0, i - 6100), i)',
     'SW_SRC.slice(Math.max(0, i - 6900), i)', 1),
    ('SW_SRC.slice(Math.max(0, i - 6800), i)',
     'SW_SRC.slice(Math.max(0, i - 7500), i)', 1),
    ('SW_SRC.slice(Math.max(0, i - 7300), i)',
     'SW_SRC.slice(Math.max(0, i - 8100), i)', 1),
] + LIMITS)
rep('test-task483.js', [
    ('SW_SRC.slice(Math.max(0, i - 5400), i)',
     'SW_SRC.slice(Math.max(0, i - 6200), i)', 1),
])
rep('test-task484.js', [
    ('SW_SRC.slice(Math.max(0, i - 5500), i)',
     'SW_SRC.slice(Math.max(0, i - 6300), i)', 1),
])
rep('test-task485.js', [
    ('SW_SRC.slice(Math.max(0, i - 5100), i)',
     'SW_SRC.slice(Math.max(0, i - 5900), i)', 1),
])
rep('test-task486.js', [
    ('SW_SRC.slice(Math.max(0, i - 4400), i)',
     'SW_SRC.slice(Math.max(0, i - 5200), i)', 1),
])
rep('test-task488.js', [
    ('SW_SRC.slice(Math.max(0, i - 3200), i)',
     'SW_SRC.slice(Math.max(0, i - 4000), i)', 1),
])

# --- Каскады: литералы окон ДРУГИХ тестов ----------------------------
rep('test-task475.js', [
    ("assertTrue(s.indexOf('i - 12400') !== -1, 'окно 12400 (Task 492)');",
     "assertTrue(s.indexOf('i - 13200') !== -1, 'окно 13200 (Task 495)');", 1),
    ("assertTrue(s1.indexOf('i - 9800') !== -1, 'test-task471: 9800 (Task 491)');",
     "assertTrue(s1.indexOf('i - 10600') !== -1, 'test-task471: 10600 (Task 495)');", 1),
    ("assertTrue(s2.indexOf('i - 9800') !== -1, 'test-task472: 9800 (Task 491)');",
     "assertTrue(s2.indexOf('i - 10600') !== -1, 'test-task472: 10600 (Task 495)');", 1),
    ("assertTrue(s.indexOf('i - 9300') !== -1, 'окно Task 472: 9300 (Task 492)');",
     "assertTrue(s.indexOf('i - 9900') !== -1, 'окно Task 472: 9900 (Task 495)');", 1),
])
rep('test-task481.js', [
    ("assertTrue(s461.indexOf('i - 12400') !== -1, 'test-task461: окно 12400 (Task 492)');",
     "assertTrue(s461.indexOf('i - 13200') !== -1, 'test-task461: окно 13200 (Task 495)');", 1),
    ("assertTrue(s471.indexOf('i - 9800') !== -1, 'test-task471: окно 9800 (Task 491)');",
     "assertTrue(s471.indexOf('i - 10600') !== -1, 'test-task471: окно 10600 (Task 495)');", 1),
    ("assertTrue(s472.indexOf('i - 9300') !== -1, 'test-task472: окно 9300 (Task 492)');",
     "assertTrue(s472.indexOf('i - 9900') !== -1, 'test-task472: окно 9900 (Task 495)');", 1),
])
rep('test-task482.js', [
    ("assertTrue(s478.indexOf('i - 7300') !== -1, 'test-task478: окно 7300 (Task 491)');",
     "assertTrue(s478.indexOf('i - 8100') !== -1, 'test-task478: окно 8100 (Task 495)');", 1),
    ("assertTrue(s479.indexOf('i - 7300') !== -1, 'test-task479: окно 7300 (Task 491)');",
     "assertTrue(s479.indexOf('i - 8100') !== -1, 'test-task479: окно 8100 (Task 495)');", 1),
    ("assertTrue(s480.indexOf('i - 6800') !== -1, 'test-task480: окно 6800 (Task 492)');",
     "assertTrue(s480.indexOf('i - 7500') !== -1, 'test-task480: окно 7500 (Task 495)');", 1),
    ("                   s481.indexOf('i - 7300') !== -1,",
     "                   s481.indexOf('i - 8100') !== -1,", 1),
])
rep('test-task486.js', [
    ("assertTrue(s475.indexOf(\"'i - 12400'\") !== -1, 'каскад 475: 461 → 12400 (Task 492)');",
     "assertTrue(s475.indexOf(\"'i - 13200'\") !== -1, 'каскад 475: 461 → 13200 (Task 495)');", 1),
    ("assertTrue(s482.indexOf(\"'i - 7300'\") !== -1, 'каскад 482: 478/479 → 7300 (Task 491)');",
     "assertTrue(s482.indexOf(\"'i - 8100'\") !== -1, 'каскад 482: 478/479 → 8100 (Task 495)');", 1),
    ("assertTrue(s484.indexOf('i - 5500') !== -1, '484: собственное окно (Task 487/490/491)');",
     "assertTrue(s484.indexOf('i - 6300') !== -1, '484: собственное окно (Task 487/490/491/495)');", 1),
])

print('RESULT: %s' % ('OK' if OK else 'FAIL'))
sys.exit(0 if OK else 1)
