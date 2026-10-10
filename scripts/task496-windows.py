#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 496 — kip8test: окна истории sw.js в тестах.

Комментарий Task 496 (4 строки, ~254 симв. перед CACHE_VERSION)
отодвинул якоря (замер node -e: i = позиция CACHE_VERSION v720):

  Task 474 9239 (окно 9000 — ВЫЛЕТЕЛО, было впритык: запас 10)
  | Task 481 6859 (окно 6800 — ВЫЛЕТЕЛО; «золотистого для ТО»@6683,
                    «ГОД»@6792 — окно должно накрыть ВЕСЬ коммент)
  | Task 480 7103 < w700 7500 ✓ | 479 7117 / 478 7697 < w1400 8100 ✓
  | LIMITS: 474 9239<9600 ✓ | 472 9612<10000 ✓ | 471 10161<10600 ✓
  | 461 12723<13200 ✓ | Task 495 504, Task 496 246.

Расширения (запас ~460/~640):
  474:  собств. окно 9000 → 9700
  481:  собств. окно 6800 → 7500 (w700 7500 / w1400 8100 живы)

КАСКАДЫ (тесты читают литералы окон ДРУГИХ тестов):
  test-task475.js:389 'i - 9000' → 'i - 9700' (окно Task 474);
  test-task481.js:548 'i - 9000' → 'i - 9700' (s474);
  test-task486.js:586 "'i - 9000'" → "'i - 9700'" (s481-каскад);
  test-task482.js:698 'i - 6800' → 'i - 7500' (s481 собств. + 8100 жив).
"""
import io

T = '/home/z/my-project/kip8test/tests'
OK = True


def rep(fname, pairs):
    global OK
    p = T + '/' + fname
    src = io.open(p, encoding='utf-8').read()
    for old, new, cnt in pairs:
        n = src.count(old)
        if n != cnt:
            OK = False
            print('  X %s: %r найдено %d (ожидалось %d)' % (fname, old, n, cnt))
            continue
        src = src.replace(old, new)
        print('  + %s: %r → %r' % (fname, old, new))
    io.open(p, 'w', encoding='utf-8').write(src)


# 1. Собственное окно Task 474: 9000 → 9700 (+ комментарий)
rep('test-task474.js', [
    ("        const ctx = SW_SRC.slice(Math.max(0, i - 9000), i);",
     "        // Task 496: комментарий ППР-клавиатуры (~254 симв.) — якорь\n"
     "        // 474@9239 — окно 9000 → 9700 (запас 461).\n"
     "        const ctx = SW_SRC.slice(Math.max(0, i - 9700), i);", 1),
])

# 2. Собственное окно Task 481: 6800 → 7500 (+ комментарий)
rep('test-task481.js', [
    ("        // Task 493: комментарий переименования кнопки Табель (~173 симв.)\n"
     "        // — якорь 481@6153 — окно 6000 → 6800 (запас 647)\n"
     "        const ctx = SW_SRC.slice(Math.max(0, i - 6800), i);",
     "        // Task 493: комментарий переименования кнопки Табель (~173 симв.)\n"
     "        // — якорь 481@6153 — окно 6000 → 6800 (запас 647)\n"
     "        // Task 496: комментарий ППР-клавиатуры (~254 симв.) — якорь\n"
     "        // 481@6859 — окно 6800 → 7500 (запас 641)\n"
     "        const ctx = SW_SRC.slice(Math.max(0, i - 7500), i);", 1),
])

# 3. Каскады
rep('test-task475.js', [
    ("        assertTrue(s.indexOf('i - 9000') !== -1, 'окно Task 474: 5300');",
     "        assertTrue(s.indexOf('i - 9700') !== -1, 'окно Task 474: 5300 (Task 496)');", 1),
])
rep('test-task481.js', [
    ("        assertTrue(s474.indexOf('i - 9000') !== -1, 'test-task474: окно 5300');",
     "        assertTrue(s474.indexOf('i - 9700') !== -1, 'test-task474: окно 5300 (Task 496)');", 1),
])
rep('test-task486.js', [
    ("        assertTrue(s481.indexOf(\"'i - 9000'\") !== -1, 'каскад 481: 471 → 6500');",
     "        assertTrue(s481.indexOf(\"'i - 9700'\") !== -1, 'каскад 481: 471 → 6500 (Task 496)');", 1),
])
rep('test-task482.js', [
    ("        assertTrue(s481.indexOf('i - 6800') !== -1 &&\n"
     "                   s481.indexOf('i - 8100') !== -1,\n"
     "            'test-task481: окна 6800 (Task 493: собств. + w700)/7300');",
     "        assertTrue(s481.indexOf('i - 7500') !== -1 &&\n"
     "                   s481.indexOf('i - 8100') !== -1,\n"
     "            'test-task481: окна 7500 (Task 496: собств. + w700)/8100');", 1),
])

print('---')
print('ВСЁ ОК' if OK else 'ЕСТЬ ОШИБКИ')
raise SystemExit(0 if OK else 1)
