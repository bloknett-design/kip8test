#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 479: SW-бамп kipia-test-v702 → v703 (ППР-индикация — третий
# цвет: срок просрочен, НО месяц срока = ТЕКУЩИЙ календарный месяц —
# оранжево-золотистый dev-ppr-warn; месяц срока раньше — красный.
# Те же цвета — в столбце «Дата» табличного вида приборов (десктоп,
# devices-table-desktop.js). sw.js логики не менял — только версия
# + комментарий).
# Сам sw.js уже поправлен вручную (версия + комментарий Task 479) —
# скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478):
#   СНАЧАЛА v703 → v704 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v704;
#   ЗАТЕМ v702 → v703 — ассерты «присутствует» едут на текущую.
# tests/test-task479.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v703 + guard v704 + v702 отсутствует).
# ОКНА ИСТОРИИ sw.js в этот раз НЕ расширяются: комментарий Task 479
# компактен (~285 симв., прецедент экономии площади — Task 477), все
# якоря в прежних окнах с запасом 345+:
#   Task 461 ~5617 < 6000; Task 471 ~3055 < 3400;
#   Task 472 ~2506 < 2900; Task 474 ~2133 < 2500.
# Скрипт это СВЕРЯЕТ (ассерты ниже), не патчит.
import glob

OWN = 'tests/test-task479.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v703';" in sw, \
    'sw.js: CACHE_VERSION не v703 (ручная правка не применена?)'
assert 'kipia-test-v702' not in sw, 'sw.js: v702 ещё остался'
assert 'Task 479' in sw, 'sw.js: нет комментария Task 479'
assert 'dev-ppr-warn' in sw, 'sw.js: нет упоминания dev-ppr-warn'
assert 'столбце «Дата»' in sw, 'sw.js: нет упоминания столбца «Дата»'
print('sw.js: проверка OK — v703 + Task 479 (третий цвет + таблица)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v703 отсутствует» → «v704 отсутствует»
    n_guard = s.count('kipia-test-v703')
    s = s.replace('kipia-test-v703', 'kipia-test-v704')
    # (б) ассерты «v702 присутствует» → «v703 присутствует»
    n_assert = s.count('kipia-test-v702')
    s = s.replace('kipia-test-v702', 'kipia-test-v703')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v702->v703: %d, guards v703->v704: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v702 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v702 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v702' in s:
        leftover.append(f)
assert not leftover, 'v702 остался в: %r' % leftover

# --- 3) Окна истории версий sw.js: СВЕРКА (без правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v703';")
for name, window in [('Task 474', 2500), ('Task 472', 2900),
                     ('Task 471', 3400), ('Task 461', 6000)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d) — окно НЕ менялось' % (name, dist, window, window - dist))

# --- 4) Комментарий Task 478 не вытеснен из окна 700 (тест 478 жив) ---
ctx = sw[max(0, i - 700):i]
for marker in ('Task 478', 'Период ремонта', 'ЗЕЛЁНЫЙ', 'КРАСНЫЙ', 'Task 479'):
    assert marker in ctx, 'маркер %r вытеснен из окна 700 шапки sw.js' % marker
print('окно 700: маркеры Task 478 + Task 479 рядом с версией — OK')

print('OK: бамп v702→v703 выполнен, окна истории без изменений (6000/3400/2900/2500)')
