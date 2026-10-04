#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 476 (этап 2 оптимизации): SW-бамп kipia-test-v699 → v700
# (KipDB — IndexedDB-слой кэша СЕРВЕРНЫХ данных в index.html:
# табель/каб. журнал/расходомеры/отметки мероприятий — надёжная
# ёмкая копия рядом с localStorage; storage.persist() после входа;
# чистка копий при logout. sw.js логики не менял — только версия).
# Сам sw.js уже поправлен вручную (версия + комментарий Task 476) —
# скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v700 → v701 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v701;
#   ЗАТЕМ v699 → v700 — ассерты «присутствует» едут на текущую.
# tests/test-task476.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v700 + guard v701 + v699 отсутствует).
# ПЛЮС адаптация окон истории версий sw.js (прецедент Task 475):
#   комментарий Task 476 (~7 строк, ~490 симв.) отодвинул якоря:
#   test-task461.js  4600 → 5300 (Task 461 теперь ~4732 симв.);
#   test-task471.js  2100 → 2700 (Task 471 теперь ~2170);
#   test-task472.js  1500 → 2100 (Task 472 ~1621) и
#                     2100 → 2700 (Task 471 в контексте 472);
#   test-task474.js  1100 → 1700 (Task 474 ~1248) + окна в проверке
#                     дистанций 2100 → 2700 (Task 471) и
#                     4600 → 5300 (Task 461).
import glob

OWN = 'tests/test-task476.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v700';" in sw, \
    'sw.js: CACHE_VERSION не v700 (ручная правка не применена?)'
assert 'kipia-test-v699' not in sw, 'sw.js: v699 ещё остался'
assert 'Task 476' in sw, 'sw.js: нет комментария Task 476'
assert 'KipDB (IndexedDB)' in sw, 'sw.js: нет упоминания KipDB'
print('sw.js: проверка OK — v700 + Task 476 + KipDB')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v700 отсутствует» → «v701 отсутствует»
    n_guard = s.count('kipia-test-v700')
    s = s.replace('kipia-test-v700', 'kipia-test-v701')
    # (б) ассерты «v699 присутствует» → «v700 присутствует»
    n_assert = s.count('kipia-test-v699')
    s = s.replace('kipia-test-v699', 'kipia-test-v700')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v699->v700: %d, guards v700->v701: %d)'
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
      'const above = SW_SRC.slice(Math.max(0, i - 4600), i);',
      'const above = SW_SRC.slice(Math.max(0, i - 5300), i);',
      'Task 476 (~490 симв.) отодвинул Task 461 до ~4732')

patch('tests/test-task471.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2700), i);',
      'Task 471 теперь ~2170')

patch('tests/test-task472.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2700), i);',
      'Task 471 (контекст 472) теперь ~2170; ПЕРВЫМ — пока i-1500 не стал i-2100')

patch('tests/test-task472.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1500), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);',
      'Task 472 теперь ~1621')

patch('tests/test-task474.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1100), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1700), i);',
      'Task 474 теперь ~1248')

patch('tests/test-task474.js',
      'assertTrue(i471 !== -1 && (i - i471) < 2100,',
      'assertTrue(i471 !== -1 && (i - i471) < 2700,',
      'дистанция Task 471 ~2170')

patch('tests/test-task474.js',
      'assertTrue(i461 !== -1 && (i - i461) < 4600,',
      'assertTrue(i461 !== -1 && (i - i461) < 5300,',
      'дистанция Task 461 ~4732')

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
         '// Task 475: окно 3800 → 4600 — комментарий Task 475 (~9 строк',
         '        // Task 476: окно 4600 → 5300 — комментарий этапа 2\n'
         '        // (KipDB, ~490 симв.) отодвинул Task 461 до ~4732.')
add_note('tests/test-task471.js',
         'const ctx = SW_SRC.slice(Math.max(0, i - 2700), i);',
         '        // Task 476: окно 2100 → 2700 — комментарий этапа 2\n'
         '        // (KipDB, ~490 симв.) отодвинул Task 471 до ~2170.')
add_note('tests/test-task472.js',
         '// Task 475: окно 1300 → 2100 — комментарий этапа 1 оптимизации',
         '        // Task 476: окна 1500 → 2100 (Task 472 ~1621) и\n'
         '        // 2100 → 2700 (Task 471 ~2170) — комментарий этапа 2.')
add_note('tests/test-task474.js',
         '        // оптимизации (~9 строк) отодвинул якоря (Task 471 ~1738,',
         '        // Task 476: окна расширены (+~490 симв. этапа 2):\n'
         '        // Task 471 2100 → 2700 (~2170), Task 461 4600 → 5300 (~4732).')

print('OK: бамп v699→v700 + окна истории адаптированы')
