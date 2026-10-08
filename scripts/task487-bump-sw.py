#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 487: SW-бамп kipia-test-v710 → v711 (табель: окно «Мероприятия
# в этот день» у ячеек стало справочным — убраны все три кнопки
# (✓ Task 482, ✎/✕ Task 309), правка/отметка — только из карточки
# работника; ДЕСКТОП-ховер по ячейке с мероприятием открывает окно
# без клика). sw.js логики не менял — только версия + комментарий.
# Сам sw.js уже поправлен вручную (версия + комментарий Task 487) —
# скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478):
#   СНАЧАЛА v711 → v712 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v712;
#   ЗАТЕМ v710 → v711 — ассерты «присутствует» едут на текущую.
# tests/test-task487.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v711 + guard v710 отсутствует).
# ОКНА ИСТОРИИ sw.js: комментарий Task 487 ~569 симв. отодвинул
# якорь Task 481 за окно 3200 (2643 → 3212) — окно теста 481
# расширено 3200 → 4000 тем же паттерном, что task482-windows.py
# (прецедент расширения окон при длинном комментарии). Окна 478/479
# (4100/5300) — с запасом, не тронуты. Скрипт это СВЕРЯЕТ.
import glob

OWN = 'tests/test-task487.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v711';" in sw, \
    'sw.js: CACHE_VERSION не v711 (ручная правка не применена?)'
assert 'kipia-test-v710' not in sw, 'sw.js: v710 ещё остался'
assert 'Task 487' in sw, 'sw.js: нет комментария Task 487'
assert 'СПРАВОЧНОЕ' in sw, 'sw.js: нет «СПРАВОЧНОЕ» (часть 1 заявки)'
assert 'ховер' in sw, 'sw.js: нет «ховер» (часть 2 заявки)'
assert 'карточк' in sw, 'sw.js: нет карточки работника'
print('sw.js: проверка OK — v711 + Task 487 (справочное окно + ховер)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v711 отсутствует» → «v712 отсутствует»
    n_guard = s.count('kipia-test-v711')
    s = s.replace('kipia-test-v711', 'kipia-test-v712')
    # (б) ассерты «v710 присутствует» → «v711 присутствует»
    n_assert = s.count('kipia-test-v710')
    s = s.replace('kipia-test-v710', 'kipia-test-v711')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v710->v711: %d, guards v711->v712: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v710 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v710 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v710' in s:
        leftover.append(f)
assert not leftover, 'v710 остался в: %r' % leftover
print('tests: v710 вычистился полностью (кроме канонического OWN)')

# --- 3) Окна истории sw.js: комментарий Task 487 (~569 симв.)
#     отодвинул якоря — расширение по прецеденту task482-windows.py:
#     test-task485: 1500 → 2100 (якорь 1858);
#     test-task484: 2100 → 2500 (якорь 2248);
#     test-task483: 2100 → 2500 (якорь 2153);
#     test-task481: 3200 → 4000 (якорь 3212, оба окна);
#     test-task480: 3200 → 4000 (якорь 3456);
#     test-task482: 3200 → 4000 (окна Task 481/480 в его тесте);
#     Окна 478/479/461/471-474 — с запасом, не тронуты.
windows = [
    ('tests/test-task485.js', 'i - 1500', 'i - 2100'),
    ('tests/test-task484.js', 'i - 2100', 'i - 2500'),
    ('tests/test-task483.js', 'i - 2100', 'i - 2500'),
    ('tests/test-task481.js', 'i - 3200', 'i - 4000'),
    ('tests/test-task480.js', 'i - 3200', 'i - 4000'),
    ('tests/test-task482.js', 'i - 3200', 'i - 4000'),
]
for f, old, new in windows:
    s = open(f, encoding='utf-8').read()
    n = s.count(old)
    assert n > 0, '%s: окно %r не найдено' % (f, old)
    open(f, 'w', encoding='utf-8').write(s.replace(old, new))
    print('%s: окно %s → %s (%d мест)' % (f, old, new, n))

# --- 4) Дистанции якорей — итоговая сводка (сверка глазами) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v711';")
for name in ['Task 486', 'Task 485', 'Task 484', 'Task 483', 'Task 482',
             'Task 481', 'Task 480', 'Task 479', 'Task 478']:
    k = sw.rindex(name, 0, i)
    print('  %s: дистанция %d' % (name, i - k))
