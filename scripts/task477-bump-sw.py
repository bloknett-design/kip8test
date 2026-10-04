#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 477 (этап 3 оптимизации): SW-бамп kipia-test-v700 → v701
# (KipPreload в index.html — фоновая предзагрузка всех данных ПО
# ПРАВАМ РОЛИ после входа: idle-очередь по одному, паузы ≥1.5 с;
# статика через SWR + серверные копии в KipDB; saveData/2g —
# пропуск; logout — стоп. sw.js логики не менял — только версия).
# Сам sw.js уже поправлен вручную (версия + компактный комментарий
# Task 477 ~300 симв.) — скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v701 → v702 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v702;
#   ЗАТЕМ v700 → v701 — ассерты «присутствует» едут на текущую.
# tests/test-task477.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v701 + guard v702 + v700 отсутствует).
# ОКНА ИСТОРИИ НЕ МЕНЯЛИСЬ: комментарий Task 477 компактный
# (~300 симв.), дистанции якорей остались в прежних окнах
# (474 ~1539 < 1700; 472 ~1912 < 2100; 471 ~2461 < 2700;
# 461 ~5023 < 5300) — прецедент: экономия площади шапки версий.
import glob

OWN = 'tests/test-task477.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v701';" in sw, \
    'sw.js: CACHE_VERSION не v701 (ручная правка не применена?)'
assert 'kipia-test-v700' not in sw, 'sw.js: v700 ещё остался'
assert 'Task 477 (этап 3 оптимизации): KipPreload' in sw, \
    'sw.js: нет комментария Task 477'
print('sw.js: проверка OK — v701 + Task 477 (KipPreload)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v701 отсутствует» → «v702 отсутствует»
    n_guard = s.count('kipia-test-v701')
    s = s.replace('kipia-test-v701', 'kipia-test-v702')
    # (б) ассерты «v700 присутствует» → «v701 присутствует»
    n_assert = s.count('kipia-test-v700')
    s = s.replace('kipia-test-v700', 'kipia-test-v701')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v700->v701: %d, guards v701->v702: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка дистанций якорей (окна НЕ расширяем — только убеждаемся) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v701';")
for name, window in [('Task 474', 1700), ('Task 472', 2100),
                     ('Task 471', 2700), ('Task 461', 5300)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — нужно расширить окна!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d)' % (name, dist, window, window - dist))

print('OK: бамп v700→v701, окна истории без изменений (компактный комментарий)')
