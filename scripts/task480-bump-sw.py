#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 480: SW-бамп kipia-test-v703 → v704 (новый ID Google-таблицы
# «Перечень КИП ИОС рабочий.xlsx» — 1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee
# вместо 1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy — в sync-скриптах,
# workflows, data/*.json, index.html-комментариях, README и промте;
# данные и структура листов те же: 1291/531/320/268). sw.js логики
# не менял — только версия + компактный комментарий ~250 симв.)
# Сам sw.js уже поправлен вручную (версия + комментарий Task 480) —
# скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478/479):
#   СНАЧАЛА v704 → v705 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v705;
#   ЗАТЕМ v703 → v704 — ассерты «присутствует» едут на текущую.
# tests/test-task480.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v704 + guard v705 + v703 отсутствует).
# ОКНА ИСТОРИИ sw.js: комментарий Task 480 (~250 симв.) выдавил
# комментарий Task 478 за окно 700 (стало ~835) — окна 700→1100 в
# test-task478.js и test-task479.js УЖЕ расширены вручную (прецедент
# Task 463/475/479). Якоря 461/471/472/474 — в прежних окнах:
#   Task 461 ~5861 < 6000; Task 471 ~3299 < 3400;
#   Task 472 ~2750 < 2900; Task 474 ~2377 < 2500.
# Скрипт это СВЕРЯЕТ (ассерты ниже), не патчит.
import glob

OWN = 'tests/test-task480.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v704';" in sw, \
    'sw.js: CACHE_VERSION не v704 (ручная правка не применена?)'
assert 'kipia-test-v703' not in sw, 'sw.js: v703 ещё остался'
assert 'Task 480' in sw, 'sw.js: нет комментария Task 480'
assert '1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee' in sw, 'sw.js: нет нового ID'
assert '«Перечень КИП ИОС рабочий.xlsx»' in sw, 'sw.js: нет имени файла'
assert '1291/531/320/268' in sw, 'sw.js: нет сверки totals'
assert 'kipia-images-test-v3' in sw and 'kipia-data-test-v1' in sw, \
    'sw.js: персистентные кэши сбиты?!'
print('sw.js: проверка OK — v704 + Task 480 (новый ID таблицы)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v704 отсутствует» → «v705 отсутствует»
    n_guard = s.count('kipia-test-v704')
    s = s.replace('kipia-test-v704', 'kipia-test-v705')
    # (б) ассерты «v703 присутствует» → «v704 присутствует»
    n_assert = s.count('kipia-test-v703')
    s = s.replace('kipia-test-v703', 'kipia-test-v704')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v703->v704: %d, guards v704->v705: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v703 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v703 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v703' in s:
        leftover.append(f)
assert not leftover, 'v703 остался в: %r' % leftover

# --- 3) Окна истории версий sw.js: СВЕРКА (без правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v704';")
for name, window in [('Task 474', 2500), ('Task 472', 2900),
                     ('Task 471', 3400), ('Task 461', 6000)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d) — окно НЕ менялось' % (name, dist, window, window - dist))

# --- 4) Комментарии Task 478/479 не вытеснены (окна расширены до 1100) ---
for window, markers in [
    (700, ['Task 480', 'Перечень КИП ИОС рабочий', '1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee']),
    (1100, ['Task 479', 'оранжево-золотистый', 'Task 478', 'Период ремонта', 'ЗЕЛЁНЫЙ', 'КРАСНЫЙ'])
]:
    ctx = sw[max(0, i - window):i]
    for marker in markers:
        assert marker in ctx, 'маркер %r вытеснен из окна %d шапки sw.js' % (marker, window)
print('окна 700/1100: маркеры Task 480 + Task 479 + Task 478 рядом с версией — OK')

# --- 5) Сверка: старый ID таблицы отсутствует в рабочих файлах ---
CHECK = [
    'index.html', 'README.md', 'Системный_промт_для_приложения_КИПиА.md',
    'scripts/sync-devices.py', 'scripts/sync-lockouts.py',
    'scripts/sync-valves.py', 'scripts/sync-regulators.py',
    'data/devices.json', 'data/lockouts.json', 'data/valves.json',
    'data/regulators.json',
    '.github/workflows/sync-devices.yml', '.github/workflows/sync-lockouts.yml',
    '.github/workflows/sync-valves.yml', '.github/workflows/sync-regulators.yml',
]
dirty = [f for f in CHECK if '1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy' in open(f, encoding='utf-8').read()]
assert not dirty, 'старый ID остался в: %r' % dirty
print('старый ID 1eUUwwul… отсутствует во всех %d рабочих файлах — OK' % len(CHECK))

print('OK: бамп v703→v704 выполнен; окна 700→1100 (Task 478/479) применены заранее')
