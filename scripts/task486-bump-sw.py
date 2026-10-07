#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 486: SW-бамп kipia-test-v709 → v710 (Табель — ТИХОЕ обновление
# данных при открытии приложения: WorkSchedule.silentRefresh из
# KipAuth._schedulePreload — 7 read-only экшенов, копия в ОБА слоя
# (localStorage + KipDB), тихая перерисовка открытого раздела,
# троттлинг 5 мин, сбой — console.warn, KipPreload._preloadWs —
# ретрай-фолбэк). sw.js логики SW не менял — только версия +
# комментарий Task 486 (~510 симв.).
# Сам sw.js уже поправлен вручную (версия + комментарий) — скрипт
# сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478-485):
#   СНАЧАЛА v710 → v711 — ВСЕ guard-ы «отсутствует» (лишний инкремент
#   не сделан) переезжают на новую несуществующую v711;
#   ЗАТЕМ v709 → v710 — ассерты «присутствует» едут на текущую.
# tests/test-task486.js — ИСКЛЮЧЁН (OWN): его SW-тесты в
# канонической пост-бамп форме (assert v710 + guard v709 + v711
# отсутствует).
# ОКНА ИСТОРИИ sw.js: комментарий Task 486 (~510 симв.) выдавил
# якоря — окна расширены ЗАРАНЕЕ scripts/task486-windows.py
# (прецедент task482/484-windows.py). Скрипт это СВЕРЯЕТ
# (ассерты ниже), не патчит.
# УРОК Task 481 (повтор): все срезы окон — в отдельной функции,
# py_compile ДО запуска.
import glob

OWN = 'tests/test-task486.js'


def window_slice(sw, i, size):
    """Окно истории: size символов ДО индекса версии (без выхода
    за начало файла)."""
    start = i - size
    if start < 0:
        start = 0
    return sw[start:i]


# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v710';" in sw, \
    'sw.js: CACHE_VERSION не v710 (ручная правка не применена?)'
assert 'kipia-test-v709' not in sw, 'sw.js: v709 ещё остался'
assert 'Task 486' in sw, 'sw.js: нет комментария Task 486'
assert 'silentRefresh' in sw, 'sw.js: нет упоминания silentRefresh'
assert 'ТИХОЕ обновление' in sw, 'sw.js: нет сущности заявки'
assert 'Табель' in sw, 'sw.js: нет упоминания раздела'
assert 'kipia-images-test-v3' in sw and 'kipia-data-test-v1' in sw, \
    'sw.js: персистентные кэши сбиты?!'
print('sw.js: проверка OK — v710 + Task 486 (тихое обновление табеля при открытии)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v710 отсутствует» → «v711 отсутствует»
    n_guard = s.count('kipia-test-v710')
    s = s.replace('kipia-test-v710', 'kipia-test-v711')
    # (б) ассерты «v709 присутствует» → «v710 присутствует»
    n_assert = s.count('kipia-test-v709')
    s = s.replace('kipia-test-v709', 'kipia-test-v710')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v709->v710: %d, guards v710->v711: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v709 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v709 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v709' in s:
        leftover.append(f)
assert not leftover, 'v709 остался в: %r' % leftover

# --- 3) Окна истории версий sw.js: СВЕРКА (без правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v710';")
for name, window in [('Task 474', 5300), ('Task 472', 5900),
                     ('Task 471', 6500), ('Task 461', 9100)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d) — окно НЕ менялось' % (name, dist, window, window - dist))

# --- 4) Комментарии Task 485-478 не вытеснены (окна после расширения) ---
w2100 = window_slice(sw, i, 2100)
for marker in ['Task 486', 'silentRefresh', 'Task 485', 'Клапана']:
    assert marker in w2100, 'маркер %r вытеснен из окна 2100 шапки sw.js' % marker
w2600 = window_slice(sw, i, 2600)
for marker in ['Task 484', 'ppr_chart', 'Task 483']:
    assert marker in w2600, 'маркер %r вытеснен из окна 2600 шапки sw.js' % marker
w3200 = window_slice(sw, i, 3200)
for marker in ['Task 482', 'Task 481', 'Task 480', 'Task 479']:
    assert marker in w3200, 'маркер %r вытеснен из окна 3200 шапки sw.js' % marker
w4100 = window_slice(sw, i, 4100)
for marker in ['Task 478', 'Перечень КИП ИОС рабочий']:
    assert marker in w4100, 'маркер %r вытеснен из окна 4100 шапки sw.js' % marker
print('окна 2100/2600/3200/4100: маркеры Task 486 + 485 + 484 + 483 + 482 + 481 + 480 + 479 + 478 рядом с версией — OK')

print('OK: бамп v709→v710 выполнен; окна истории расширены заранее (task486-windows.py)')
