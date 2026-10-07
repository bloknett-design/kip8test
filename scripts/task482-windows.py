#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 482: расширение ОКОН ИСТОРИИ sw.js в тестах — комментарий
# Task 482 (~375 симв., вставлен ПОСЛЕ комментария Task 481, ПЕРЕД
# const CACHE_VERSION) отодвинул якори:
#   Task 481 ~636   (481-тест: w700 «Task 480 в окне» → 880 — ВЫЛЕЗЛО)
#   Task 480 ~880   (480-тест: окно 700 → ВЫЛЕЗЛО)
#   Task 479 ~894   (влезает, но едет вместе с 478-окном)
#   Task 478 ~1474  (478/479-тесты: окно 1400 → ВЫЛЕЗЛО)
#   474 ~3016 < 3100; 472 ~3389 < 3600; 471 ~3938 < 4200;
#   461 ~6500 < 6800 — расширения НЕ нужны
# Правки (идемпотентные замены с проверкой «до/после»):
#   test-task478.js:  i - 1400 → i - 1700 (комментарий окна)
#   test-task479.js:  i - 1400 → i - 1700
#   test-task480.js:  i - 700  → i - 1100
#   test-task481.js:  i - 700  → i - 1100 (w700 «Task 480»)
#                     i - 1400 → i - 1700 (w1400 «Task 479/478»)
# Прецедент: scripts/task481-windows.py (Task 478/475/476).
import io

FILES = [
    # (файл, старое, новое, сколько раз ожидается)
    ('tests/test-task478.js', 'i - 1400', 'i - 1700', 1),
    ('tests/test-task479.js', 'i - 1400', 'i - 1700', 1),
    ('tests/test-task480.js', 'i - 700', 'i - 1100', 1),
    # test-task481: ДВА контекста «i - 700» — окно комментария
    # Task 481 (строка ~490, дистанция ~636 — ВЛЕЗАЕТ, НЕ трогаем) и
    # w700 «Task 480 в окне» (~880 — расширяем); w1400 «Task 479/478»
    # (~894/~1474 — расширяем). Заменяем ПО ЛИТЕРАЛАМ с именами const:
    ('tests/test-task481.js', 'const w700 = SW_SRC.slice(Math.max(0, i - 700), i);',
     'const w700 = SW_SRC.slice(Math.max(0, i - 1100), i);', 1),
    ('tests/test-task481.js', 'const w1400 = SW_SRC.slice(Math.max(0, i - 1400), i);',
     'const w1400 = SW_SRC.slice(Math.max(0, i - 1700), i);', 1),
]

# Сверка дистанций в sw.js ДО правок (комментарий уже вставлен)
sw = open('sw.js', encoding='utf-8').read()
i = sw.index("const CACHE_VERSION = 'kipia-test-v706';")
for name, window in [('Task 481', 1100), ('Task 480', 1100),
                     ('Task 479', 1700), ('Task 478', 1700),
                     ('Task 474', 3100), ('Task 472', 3600),
                     ('Task 471', 4200), ('Task 461', 6800)]:
    j = sw.rfind(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d)' % (name, dist, window, window - dist))

# Точечные замены
for fname, old, new, expect in FILES:
    s = io.open(fname, encoding='utf-8').read()
    n = s.count(old)
    if n == 0:
        # уже применено (идемпотентность)
        assert s.count(new) >= expect, \
            '%s: ни %r ни %r не найдены' % (fname, old, new)
        print('%s: уже применено (%s ×%d)' % (fname, new, s.count(new)))
        continue
    assert n == expect, \
        '%s: %r найдено %d раз (ожидалось %d)' % (fname, old, n, expect)
    s = s.replace(old, new, expect)
    io.open(fname, 'w', encoding='utf-8').write(s)
    print('%s: %s → %s (×%d)' % (fname, old, new, expect))

# Комментарии к окнам дополняем пометкой Task 482 (по желанию — не
# критично), сверяем итог
for fname, lit in [('tests/test-task478.js', 'i - 1700'),
                   ('tests/test-task479.js', 'i - 1700'),
                   ('tests/test-task480.js', 'i - 1100'),
                   ('tests/test-task481.js', 'i - 1100')]:
    s = io.open(fname, encoding='utf-8').read()
    assert lit in s, '%s: литерал %r не найден после правки' % (fname, lit)
s481 = io.open('tests/test-task481.js', encoding='utf-8').read()
assert 'i - 1700' in s481, 'test-task481: окно w1400 → 1700 не применено'

print('OK: окна истории 478/479/480/481 расширены под комментарий Task 482')
