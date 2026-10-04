#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 475 (этап 1 оптимизации): SW-бамп kipia-test-v698 → v699
# (STALE-WHILE-REVALIDATE: навигация + data/*.json в персистентном
# DATA_CACHE_NAME + локальные ассеты; логотипы 2048→256px в ASSETS;
# офлайн-ветка входа в index.html — гостевой режим + автоповтор).
# Сам sw.js уже поправлен вручную (версия + комментарий Task 475 +
# DATA-кэш + SWR-ветки) — скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v699 → v700 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v700;
#   ЗАТЕМ v698 → v699 — ассерты «присутствует» едут на текущую.
# tests/test-task475.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v699 + guard v700 + v698 отсутствует).
# ПЛЮС адаптация окон истории версий sw.js (прецедент Task 471/473/474,
# комментарий Task 475 ~9 строк отодвинул все якоря):
#   test-task461.js  3800 → 4600 (Task 461 теперь ~4300 симв.);
#   test-task471.js  1300 → 2100 (Task 471 теперь ~1738);
#   test-task472.js  1300 → 2100 (Task 471) и 900 → 1500 (Task 472 ~1189);
#   test-task474.js   600 → 1100 (Task 474 теперь ~816).
import glob

OWN = 'tests/test-task475.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v699';" in sw, \
    'sw.js: CACHE_VERSION не v699 (ручная правка не применена?)'
assert 'kipia-test-v698' not in sw, 'sw.js: v698 ещё остался'
assert 'Task 475' in sw, 'sw.js: нет комментария Task 475'
assert "const DATA_CACHE_VERSION = 'kipia-data-test-v1';" in sw, \
    'sw.js: нет DATA_CACHE_VERSION'
assert "'./images/logo.png'," in sw, 'sw.js: logo.png не в ASSETS'
print('sw.js: проверка OK — v699 + Task 475 + DATA-кэш + SWR')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v699 отсутствует» → «v700 отсутствует»
    n_guard = s.count('kipia-test-v699')
    s = s.replace('kipia-test-v699', 'kipia-test-v700')
    # (б) ассерты «v698 присутствует» → «v699 присутствует»
    n_assert = s.count('kipia-test-v698')
    s = s.replace('kipia-test-v698', 'kipia-test-v699')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v698->v699: %d, guards v699->v700: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Окна истории версий sw.js ---
def patch(fname, old, new, note):
    s = open(fname, encoding='utf-8').read()
    assert old in s, '%s: не найдено окно %s' % (fname, old)
    assert new not in s, '%s: окно %s уже стоит (повторный прогон?)' % (fname, new)
    s = s.replace(old, new, 1)
    open(fname, 'w', encoding='utf-8').write(s)
    print('%s: окно %s → %s (%s)' % (fname, old, new, note))

patch('tests/test-task461.js',
      'const above = SW_SRC.slice(Math.max(0, i - 3800), i);',
      'const above = SW_SRC.slice(Math.max(0, i - 4600), i);',
      'Task 475 ~9 строк отодвинул Task 461 до ~4300')

patch('tests/test-task471.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1300), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);',
      'Task 471 теперь ~1738')

patch('tests/test-task472.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1300), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);',
      'Task 471 теперь ~1738')

patch('tests/test-task472.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 900), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1500), i);',
      'Task 472 теперь ~1189')

patch('tests/test-task474.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 600), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1100), i);',
      'Task 474 теперь ~816')

# --- 3) Комментарии к окнам (после правки чисел, чтобы не ломать анкеры выше) ---
def add_note(fname, anchor, note):
    s = open(fname, encoding='utf-8').read()
    assert anchor in s, '%s: якорь комментария не найден' % fname
    if note in s:
        return
    s = s.replace(anchor, anchor + '\n' + note, 1)
    open(fname, 'w', encoding='utf-8').write(s)
    print('%s: добавлен комментарий окна' % fname)

add_note('tests/test-task461.js',
         '// Task 474: окно 3600 → 3800 — комментарий Task 474 (3 строки',
         '        // Task 475: окно 3800 → 4600 — комментарий Task 475 (~9 строк\n'
         '        // этапа 1 оптимизации: SWR + персистентный DATA-кэш) отодвинул\n'
         '        // Task 461 до ~4300 символов.')
add_note('tests/test-task471.js',
         'const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);',
         '        // Task 475: окно 1300 → 2100 — комментарий этапа 1 оптимизации\n'
         '        // (~9 строк) отодвинул начало комментария Task 471 (~1738 симв.).')
add_note('tests/test-task472.js',
         '// Task 473: окно 900 → 1020; Task 474: 1020 → 1300 — комментарий',
         '        // Task 475: окно 1300 → 2100 — комментарий этапа 1 оптимизации\n'
         '        // отодвинул Task 471 до ~1738; окно Task 472 900 → 1500 (~1189).')

print('OK: бамп v698→v699 + окна истории адаптированы')
