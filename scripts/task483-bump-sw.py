#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 483: SW-бамп kipia-test-v706 → v707 (Графики КИП ИОС →
# «Приборы»: таблица «Вид обслуживания × месяцы I–XII» + сгруппиро-
# ванная диаграмма «как в Excel» (выровнена по колонкам таблицы);
# данные ppr_chart считаются sync-devices.py по листу «Приборы»
# с фильтром «Наличие в ППР» = «Есть»; заШитые счётчики _PPR_DEVICES
# удалены). sw.js логики SW не менял — только версия + комментарий
# Task 483 (~378 симв.).
# Сам sw.js уже поправлен вручную (версия + комментарий) — скрипт
# сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478-482):
#   СНАЧАЛА v707 → v708 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v708;
#   ЗАТЕМ v706 → v707 — ассерты «присутствует» едут на текущую.
# tests/test-task483.js — ИСКЛЮЧЁН (OWN): его SW-тесты в
# канонической пост-бамп форме (assert v707 + guard v708 + v706
# отсутствует).
# ОКНА ИСТОРИИ sw.js: комментарий Task 483 (~378 симв.) выдавил
# якоря — окна расширены ЗАРАНЕЕ scripts/task483-windows.py
# (прецедент Task 478/480/481/482):
#   Task 478: ~1421 → ~1799 (окно 1700 → 2100 в 478/479/481/482)
#   Task 480: ~827  → ~1205 (окно 1100 → 1500 в 480/481/482)
#   Task 481: ~583  → ~961  (собственное окно 700 → 1100 + w700
#                            1100 → 1500; w1400 1700 → 2100)
#   Task 474 ~3341 → окно 3100 → 3500; 472 ~3714 → 3600 → 4000;
#   471 ~4263 → 4200 → 4600; 461 ~6825 → 6800 → 7200
#   (+ синхрон литералов test-task475 §9 и каскада test-task482)
# Скрипт это СВЕРЯЕТ (ассерты ниже), не патчит.
# УРОК Task 481 (повтор): все срезы окон — в отдельной функции,
# py_compile ДО запуска.
import glob

OWN = 'tests/test-task483.js'


def window_slice(sw, i, size):
    """Окно истории: size символов ДО индекса версии (без выхода
    за начало файла)."""
    start = i - size
    if start < 0:
        start = 0
    return sw[start:i]


# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v707';" in sw, \
    'sw.js: CACHE_VERSION не v707 (ручная правка не применена?)'
assert 'kipia-test-v706' not in sw, 'sw.js: v706 ещё остался'
assert 'Task 483' in sw, 'sw.js: нет комментария Task 483'
assert 'ppr_chart' in sw, 'sw.js: нет упоминания ppr_chart в комментарии'
assert 'Графики КИП ИОС' in sw, 'sw.js: нет упоминания раздела'
assert 'kipia-images-test-v3' in sw and 'kipia-data-test-v1' in sw, \
    'sw.js: персистентные кэши сбиты?!'
print('sw.js: проверка OK — v707 + Task 483 (таблица+диаграмма ППР приборов)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v707 отсутствует» → «v708 отсутствует»
    n_guard = s.count('kipia-test-v707')
    s = s.replace('kipia-test-v707', 'kipia-test-v708')
    # (б) ассерты «v706 присутствует» → «v707 присутствует»
    n_assert = s.count('kipia-test-v706')
    s = s.replace('kipia-test-v706', 'kipia-test-v707')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v706->v707: %d, guards v707->v708: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v706 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v706 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v706' in s:
        leftover.append(f)
assert not leftover, 'v706 остался в: %r' % leftover

# --- 3) Окна истории версий sw.js: СВЕРКА (без правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v707';")
for name, window in [('Task 474', 3500), ('Task 472', 4000),
                     ('Task 471', 4600), ('Task 461', 7200)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d) — окно НЕ менялось' % (name, dist, window, window - dist))

# --- 4) Комментарии Task 482-478 не вытеснены (окна 1500/2100) ---
w1500 = window_slice(sw, i, 1500)
for marker in ['Task 483', 'ppr_chart', 'Task 482', '_barExpMaxH',
               'Task 481', 'Task 480', 'Перечень КИП ИОС рабочий']:
    assert marker in w1500, 'маркер %r вытеснен из окна 1500 шапки sw.js' % marker
w2100 = window_slice(sw, i, 2100)
for marker in ['Task 479', 'оранжево-золотистый', 'Task 478',
               'Период ремонта', 'ЗЕЛЁНЫЙ', 'КРАСНЫЙ']:
    assert marker in w2100, 'маркер %r вытеснен из окна 2100 шапки sw.js' % marker
print('окна 1500/2100: маркеры Task 483 + 482 + 481 + 480 + 479 + 478 рядом с версией — OK')

# --- 5) Сверка литералов ЧУЖИХ окон (синхронизированы windows-скриптом) ---
for fname, lits in [
    ('tests/test-task478.js', ['i - 2100']),
    ('tests/test-task479.js', ['i - 2100']),
    ('tests/test-task480.js', ['i - 1500']),
    ('tests/test-task481.js', ['i - 1100', 'i - 1500', 'i - 2100']),
    ('tests/test-task482.js', ['i - 1500', 'i - 2100']),
    ('tests/test-task475.js', ['i - 7200', 'i - 4600', 'i - 4000', 'i - 3500'])
]:
    s = open(fname, encoding='utf-8').read()
    for lit in lits:
        assert lit in s, '%s: литерал %r не найден' % (fname, lit)
print('литералы окон 478/479/480/481/482 (2100/1500) + 475 (7200/4600/4000/3500) — синхронизированы')

print('OK: бамп v706→v707 выполнен; окна истории расширены заранее (task483-windows.py)')
