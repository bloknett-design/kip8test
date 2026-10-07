#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 482: SW-бамп kipia-test-v705 → v706 (табель: окна бара —
# раскрытие КАПАЕТСЯ по низу экрана (_barExpMaxH), длинный список
# листается внутри (колесо/свайп/↑↓); бейджи И/ПЗ ячеек — рамка
# зелёная (выполнение отмечено) / красная (не отмечено + дата
# прошла); галочка отметки выполнения — в окне «Мероприятия в этот
# день» рядом с ✎/✕, уровень edit). sw.js логики SW не менял —
# только версия + комментарий Task 482 (~375 симв.).
# Сам sw.js уже поправлен вручную (версия + комментарий) — скрипт
# сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478/479/480/481):
#   СНАЧАЛА v706 → v707 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v707;
#   ЗАТЕМ v705 → v706 — ассерты «присутствует» едут на текущую.
# tests/test-task482.js — ИСКЛЮЧЁН (OWN): его SW-тесты уже в
# канонической пост-бамп форме (assert v706 + guard v707 + v705
# отсутствует).
# ОКНА ИСТОРИИ sw.js: комментарий Task 482 (~375 симв.) выдавил
# якоря — окна расширены ЗАРАНЕЕ scripts/task482-windows.py
# (прецедент Task 478/480/481):
#   Task 478: ~1096 → ~1474 (окно 1400 → 1700 в 478/479/481)
#   Task 479: ~880  → ~894  (в окне 1700)
#   Task 480: ~430  → ~880  (окно 700 → 1100 в 480/481)
#   Task 474 ~3016 < 3100; 472 ~3389 < 3600; 471 ~3938 < 4200;
#   461 ~6500 < 6800 — расширения НЕ нужны
# Скрипт это СВЕРЯЕТ (ассерты ниже), не патчит.
# УРОК Task 481: в task481-bump-sw.py оказалась битая строка
# (ctx = swax(0, ...) — срез окна) — здесь все срезы вынесены в
# отдельную функцию и скрипт прогнан через py_compile ДО запуска.
import glob

OWN = 'tests/test-task482.js'


def window_slice(sw, i, size):
    """Окно истории: size символов ДО индекса версии (без выхода
    за начало файла)."""
    start = i - size
    if start < 0:
        start = 0
    return sw[start:i]


# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v706';" in sw, \
    'sw.js: CACHE_VERSION не v706 (ручная правка не применена?)'
assert 'kipia-test-v705' not in sw, 'sw.js: v705 ещё остался'
assert 'Task 482' in sw, 'sw.js: нет комментария Task 482'
assert '_barExpMaxH' in sw, 'sw.js: нет упоминания капа в комментарии'
assert 'kipia-images-test-v3' in sw and 'kipia-data-test-v1' in sw, \
    'sw.js: персистентные кэши сбиты?!'
print('sw.js: проверка OK — v706 + Task 482 (кап окон/рамки И-ПЗ/галочка)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v706 отсутствует» → «v707 отсутствует»
    n_guard = s.count('kipia-test-v706')
    s = s.replace('kipia-test-v706', 'kipia-test-v707')
    # (б) ассерты «v705 присутствует» → «v706 присутствует»
    n_assert = s.count('kipia-test-v705')
    s = s.replace('kipia-test-v705', 'kipia-test-v706')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v705->v706: %d, guards v706->v707: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Сверка: v705 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v705 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v705' in s:
        leftover.append(f)
assert not leftover, 'v705 остался в: %r' % leftover

# --- 3) Окна истории версий sw.js: СВЕРКА (без правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v706';")
for name, window in [('Task 474', 3100), ('Task 472', 3600),
                     ('Task 471', 4200), ('Task 461', 6800)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d) — окно НЕ менялось' % (name, dist, window, window - dist))

# --- 4) Комментарии Task 481/480/479/478 не вытеснены (окна 1100/1700) ---
w1100 = window_slice(sw, i, 1100)
for marker in ['Task 482', '_barExpMaxH', 'Task 481', 'Task 480',
               'Перечень КИП ИОС рабочий']:
    assert marker in w1100, 'маркер %r вытеснен из окна 1100 шапки sw.js' % marker
w1700 = window_slice(sw, i, 1700)
for marker in ['Task 479', 'оранжево-золотистый', 'Task 478',
               'Период ремонта', 'ЗЕЛЁНЫЙ', 'КРАСНЫЙ']:
    assert marker in w1700, 'маркер %r вытеснен из окна 1700 шапки sw.js' % marker
print('окна 1100/1700: маркеры Task 482 + 481 + 480 + 479 + 478 рядом с версией — OK')

# --- 5) Сверка литералов ЧУЖИХ окон (синхронизированы windows-скриптом) ---
for fname, lits in [
    ('tests/test-task478.js', ['i - 1700']),
    ('tests/test-task479.js', ['i - 1700']),
    ('tests/test-task480.js', ['i - 1100']),
    ('tests/test-task481.js', ['i - 1100', 'i - 1700']),
    ('tests/test-task475.js', ['i - 6800', 'i - 4200', 'i - 3600', 'i - 3100'])
]:
    s = open(fname, encoding='utf-8').read()
    for lit in lits:
        assert lit in s, '%s: литерал %r не найден' % (fname, lit)
print('литералы окон 478/479/480/481 (1100/1700) + 475 (6800/4200/3600/3100) — синхронизированы')

print('OK: бамп v705→v706 выполнен; окна истории расширены заранее (task482-windows.py)')
