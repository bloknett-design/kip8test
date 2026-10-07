#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 481: SW-бамп kipia-test-v704 → v705 (ППР-индикация, вид «ТО» —
# только ГОД даты ремонта: текущий год → зелёный, другой год →
# красный; период/месяц НЕ учитываются, warn для ТО невозможен —
# ветка в devPprStatusClass до разбора периода; карточка + столбец
# «Дата» таблицы одной функцией). sw.js логики SW не менял — только
# версия + компактный комментарий ~258 симв.
# Сам sw.js уже поправлен вручную (версия + комментарий Task 481) —
# скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478/479/480):
#   СНАЧАЛА v705 → v706 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v706;
#   ЗАТЕМ v704 → v705 — ассерты «присутствует» едут на текущую.
# tests/test-task481.js — ИСКЛЮЧЁН (OWN): его SW-тесты уже в
# канонической пост-бамп форме (assert v705 + guard v706 + v704
# отсутствует).
# ОКНА ИСТОРИИ sw.js: комментарий Task 481 (~258 симв.) выдавил
# якоря — окна расширены ЗАРАНЕЕ scripts/task481-windows.py
# (прецедент Task 478/475/476):
#   Task 474: ~2377 → ~2638 (окно 2500 → 3100)
#   Task 472: ~2750 → ~3011 (окно 2900 → 3600)
#   Task 471: ~3299 → ~3560 (окно 3400 → 4200)
#   Task 461: ~5861 → ~6122 (окно 6000 → 6800)
#   комментарий Task 478 в шапке: ~835 → ~1096 (окно 1100 → 1400 в
#   test-task478.js и test-task479.js — запас был 4 симв.!)
# Скрипт это СВЕРЯЕТ (ассерты ниже), не патчит.
import glob

OWN = 'tests/test-task481.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v705';" in sw, \
    'sw.js: CACHE_VERSION не v705 (ручная правка не применена?)'
assert 'kipia-test-v704' not in sw, 'sw.js: v704 ещё остался'
assert 'Task 481' in sw, 'sw.js: нет комментария Task 481'
assert 'ГОД' in sw, 'sw.js: нет правила года в комментарии'
assert 'kipia-images-test-v3' in sw and 'kipia-data-test-v1' in sw, \
    'sw.js: персистентные кэши сбиты?!'
print('sw.js: проверка OK — v705 + Task 481 (ТО = только год)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v705 отсутствует» → «v706 отсутствует»
    n_guard = s.count('kipia-test-v705')
    s = s.replace('kipia-test-v705', 'kipia-test-v706')
    # (б) ассерты «v704 присутствует» → «v705 присутствует»
    n_assert = s.count('kipia-test-v704')
    s = s.replace('kipia-test-v704', 'kipia-test-v705')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v704->v705: %d, guards v705->v706: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v704 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v704 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v704' in s:
        leftover.append(f)
assert not leftover, 'v704 остался в: %r' % leftover

# --- 3) Окна истории версий sw.js: СВЕРКА (без правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v705';")
for name, window in [('Task 474', 3100), ('Task 472', 3600),
                     ('Task 471', 4200), ('Task 461', 6800)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d) — окно НЕ менялось' % (name, dist, window, window - dist))

# --- 4) Комментарии Task 480/479/478 не вытеснены (окна 700/1400) ---
for window, markers in [
    (700, ['Task 481', 'ГОД', 'Task 480', 'Перечень КИП ИОС рабочий']),
    (1400, ['Task 479', 'оранжево-золотистый', 'Task 478',
            'Период ремонта', 'ЗЕЛЁНЫЙ', 'КРАСНЫЙ'])
]:
    ctx = sw[max(0, i - window):i]
    for marker in markers:
        assert marker in ctx, 'маркер %r вытеснен из окна %d шапки sw.js' % (marker, window)
print('окна 700/1400: маркеры Task 481 + 480 + 479 + 478 рядом с версией — OK')

# --- 5) Сверка литералов ЧУЖИХ окон (test-task475 §9 синхронизирован) ---
s475 = open('tests/test-task475.js', encoding='utf-8').read()
for lit in ['i - 6800', 'i - 4200', 'i - 3600', 'i - 3100']:
    assert lit in s475, 'test-task475: литерал %r не найден' % lit
assert 'i - 6000' not in s475 and 'i - 3400' not in s475 \
    and 'i - 2900' not in s475 and 'i - 2500' not in s475, \
    'test-task475: остались СТАРЫЕ литералы окон'
print('test-task475 §9: литералы окон 6800/4200/3600/3100 синхронизированы')

print('OK: бамп v704→v705 выполнен; окна истории расширены заранее (task481-windows.py)')
