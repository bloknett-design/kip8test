#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 484: SW-бамп kipia-test-v707 → v708 (Графики КИП ИОС →
# «Блокировки»: тот же вид «как в Excel», что «Приборы» — таблица +
# диаграмма из ppr_chart в data/lockouts.json; sync-lockouts.py
# считает счётчики по исходному листу «Блокировки» с фильтром
# «Наличие в перечне и в ППР» = «Есть»; старый рендерер
# _renderPPRChart и заШитые _PPR_LOCKOUTS удалены). sw.js логики
# SW не менял — только версия + комментарий Task 484 (~390 симв.).
# Сам sw.js уже поправлен вручную (версия + комментарий) — скрипт
# сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478-483):
#   СНАЧАЛА v708 → v709 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v709;
#   ЗАТЕМ v707 → v708 — ассерты «присутствует» едут на текущую.
# tests/test-task484.js — ИСКЛЮЧЁН (OWN): его SW-тесты в
# канонической пост-бамп форме (assert v708 + guard v709 + v707
# отсутствует).
# ОКНА ИСТОРИИ sw.js: комментарий Task 484 (~390 симв.) выдавил
# якоря — окна расширены ЗАРАНЕЕ scripts/task484-windows.py
# (прецедент Task 478-483):
#   Task 481: собственное 1100 → 1500; w700 (Task 480) 1500 → 2100;
#   w1400 (Task 478) 2100 → 2500; Task 478: 2100 → 2500;
#   Task 480: 1500 → 2100; Task 482: 1500 → 2100 (×2), 2100 → 2500;
#   якорные 474/472/471/461: 3500 → 4000, 4000 → 4500, 4600 → 5000,
#   6800... 7200 → 7600 (+ синхрон литералов test-task475 §9 и
#   каскадов test-task481/test-task482)
# Скрипт это СВЕРЯЕТ (ассерты ниже), не патчит.
# УРОК Task 481 (повтор): все срезы окон — в отдельной функции,
# py_compile ДО запуска.
import glob

OWN = 'tests/test-task484.js'


def window_slice(sw, i, size):
    """Окно истории: size символов ДО индекса версии (без выхода
    за начало файла)."""
    start = i - size
    if start < 0:
        start = 0
    return sw[start:i]


# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v708';" in sw, \
    'sw.js: CACHE_VERSION не v708 (ручная правка не применена?)'
assert 'kipia-test-v707' not in sw, 'sw.js: v707 ещё остался'
assert 'Task 484' in sw, 'sw.js: нет комментария Task 484'
assert 'ppr_chart' in sw, 'sw.js: нет упоминания ppr_chart в комментарии'
assert 'Блокировки' in sw, 'sw.js: нет упоминания вкладки'
assert 'kipia-images-test-v3' in sw and 'kipia-data-test-v1' in sw, \
    'sw.js: персистентные кэши сбиты?!'
print('sw.js: проверка OK — v708 + Task 484 (таблица+диаграмма ППР блокировок)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v708 отсутствует» → «v709 отсутствует»
    n_guard = s.count('kipia-test-v708')
    s = s.replace('kipia-test-v708', 'kipia-test-v709')
    # (б) ассерты «v707 присутствует» → «v708 присутствует»
    n_assert = s.count('kipia-test-v707')
    s = s.replace('kipia-test-v707', 'kipia-test-v708')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v707->v708: %d, guards v708->v709: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v707 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v707 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v707' in s:
        leftover.append(f)
assert not leftover, 'v707 остался в: %r' % leftover

# --- 3) Окна истории версий sw.js: СВЕРКА (без правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v708';")
for name, window in [('Task 474', 4000), ('Task 472', 4500),
                     ('Task 471', 5000), ('Task 461', 7600)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d) — окно НЕ менялось' % (name, dist, window, window - dist))

# --- 4) Комментарии Task 483-478 не вытеснены (окна 1500/2100/2500) ---
w1500 = window_slice(sw, i, 1500)
for marker in ['Task 484', 'ppr_chart', 'Task 483', 'Графики КИП ИОС']:
    assert marker in w1500, 'маркер %r вытеснен из окна 1500 шапки sw.js' % marker
w2100 = window_slice(sw, i, 2100)
for marker in ['Task 482', '_barExpMaxH', 'Task 481', 'Task 480',
               'Перечень КИП ИОС рабочий']:
    assert marker in w2100, 'маркер %r вытеснен из окна 2100 шапки sw.js' % marker
w2500 = window_slice(sw, i, 2500)
for marker in ['Task 479', 'оранжево-золотистый', 'Task 478',
               'Период ремонта']:
    assert marker in w2500, 'маркер %r вытеснен из окна 2500 шапки sw.js' % marker
print('окна 1500/2100/2500: маркеры Task 484 + 483 + 482 + 481 + 480 + 479 + 478 рядом с версией — OK')

# --- 5) Сверка литералов ЧУЖИХ окон (синхронизированы windows-скриптом) ---
for fname, lits in [
    ('tests/test-task478.js', ['i - 2500']),
    ('tests/test-task479.js', ['i - 2500']),
    ('tests/test-task480.js', ['i - 2100']),
    ('tests/test-task481.js', ['i - 1500', 'i - 2100', 'i - 2500']),
    ('tests/test-task482.js', ['i - 2100', 'i - 2500']),
    ('tests/test-task475.js', ['i - 7600', 'i - 5000', 'i - 4500', 'i - 4000'])
]:
    s = open(fname, encoding='utf-8').read()
    for lit in lits:
        assert lit in s, '%s: литерал %r не найден' % (fname, lit)
print('литералы окон 478 (2500) / 479 (2100) / 480 (2100) / 481 (1500/2100/2500) / '
      '482 (2100/2500) + 475 (7600/5000/4500/4000) — синхронизированы')

print('OK: бамп v707→v708 выполнен; окна истории расширены заранее (task484-windows.py)')
