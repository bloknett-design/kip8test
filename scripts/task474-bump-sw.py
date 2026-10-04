#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 474: SW-бамп kipia-test-v697 → v698 (index.html менялся —
# подробная карточка прибора в разделе КИП ИОС: текст типа прибора
# на картинке в ПОЛТОРА раза крупнее (12px → 18px) + тексты
# «№ прибора» и «Место установки» смещены немного ниже от верхней
# границы карточки (padding-top 2px → 12px у .dev-detail-meta)).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v698 → v699 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v699;
#   ЗАТЕМ v697 → v698 — ассерты «присутствует» едут на текущую.
# tests/test-task474.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v698 + guard v699 + v697 отсутствует).
# ПЛЮС адаптация окон истории версий sw.js (прецедент Task 471/473):
#   test-task461.js 3600 → 3800 (комментарий Task 474 отодвинул
#   Task 461 до ~3719 символов);
#   test-task471.js и test-task472.js (контекст Task 471)
#   1020 → 1300 (Task 471 теперь ~1157 символов).
import glob

OWN = 'tests/test-task474.js'

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v697'"
new = "CACHE_VERSION = 'kipia-test-v698'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v697'
assert 'kipia-test-v698' not in sw, 'sw.js: v698 уже был (двойной бамп?)'
sw = sw.replace(old, new)

# Комментарий Task 474 в шапке (перед строкой-якорём после Task 473)
anchor = '// ВСЕГДА на одном уровне (обе колонки: скролл-зона + 5px + 12px).'
task474 = ('// Task 474: карточка прибора (КИП ИОС) — текст Типа на картинке\n'
           '// в полтора раза крупнее (12→18px); «№ прибора»/«Место установки»\n'
           '// ниже от верха карточки.\n')
assert anchor in sw, 'sw.js: не найден якорь вставки комментария'
assert 'Task 474' not in sw, 'sw.js: комментарий Task 474 уже есть'
sw = sw.replace(anchor, task474 + anchor, 1)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v697 -> kipia-test-v698 + комментарий Task 474')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v698 отсутствует» → «v699 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v698')
    s = s.replace('kipia-test-v698', 'kipia-test-v699')
    # 2) ассерты «v697 присутствует» → «v698 присутствует»
    n_assert = s.count('kipia-test-v697')
    s = s.replace('kipia-test-v697', 'kipia-test-v698')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed[:5]:
    print('  %s (ассерты v697->v698: %d, guard v698->v699: %d)' % (f, a, g))
print('  ... и ещё %d файлов' % max(0, len(changed) - 5))

# ============================================================
# Адаптация окон истории версий sw.js (после бампа — текст уже
# содержит v698 в ассертах, окна не зависят от версий)
# ============================================================
def patch(path, old, new):
    s = open(path, encoding='utf-8').read()
    assert s.count(old) == 1, '%s: якорь окна найден (%d)' % (path, s.count(old))
    s = s.replace(old, new)
    open(path, 'w', encoding='utf-8').write(s)
    print('%s: окно обновлено' % path)

# test-task461.js: 3600 → 3800
patch('tests/test-task461.js',
      "        // Task 471: окно 3050 → 3600 — комментарий Task 471 (9 строк о\n"
      "        // кнопке годов и работах месяца) снова отодвинул комментарий\n"
      "        // Task 461 (расстояние ~3200 символов)\n"
      "        const above = SW_SRC.slice(Math.max(0, i - 3600), i);",
      "        // Task 471: окно 3050 → 3600 — комментарий Task 471 (9 строк о\n"
      "        // кнопке годов и работах месяца) снова отодвинул комментарий\n"
      "        // Task 461 (расстояние ~3200 символов)\n"
      "        // Task 474: окно 3600 → 3800 — комментарий Task 474 (3 строки\n"
      "        // о карточке прибора) снова отодвинул Task 461 (~3719 симв.)\n"
      "        const above = SW_SRC.slice(Math.max(0, i - 3800), i);")

# test-task471.js: 1020 → 1300
patch('tests/test-task471.js',
      "        // Task 473: окно 900 → 1020 — комментарий Task 473 (2 строки о\n"
      "        // графике ППР «Приборы») отодвинул начало комментария Task 471\n"
      "        // (расстояние ~986 символов).\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 1020), i);",
      "        // Task 473: окно 900 → 1020; Task 474: 1020 → 1300 —\n"
      "        // комментарий Task 474 (3 строки о карточке прибора) отодвинул\n"
      "        // начало комментария Task 471 (~1157 символов).\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 1300), i);")

# test-task472.js: контекст Task 471 — 1020 → 1300
patch('tests/test-task472.js',
      "    test('контекст Task 471 не вытеснен (окно 1020 символов)', () => {",
      "    test('контекст Task 471 не вытеснен (окно 1300 символов)', () => {")
patch('tests/test-task472.js',
      "        // Task 473: окно 900 → 1020 — комментарий Task 473 в шапке sw.js\n"
      "        // отодвинул начало комментария Task 471 (~986 символов).\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 1020), i);",
      "        // Task 473: окно 900 → 1020; Task 474: 1020 → 1300 — комментарий\n"
      "        // Task 474 в шапке sw.js отодвинул начало комментария Task 471\n"
      "        // (~1157 символов).\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 1300), i);")

# run-all.js: + require test-task474 после 473
ra = 'tests/run-all.js'
s = open(ra, encoding='utf-8').read()
A = "require('./test-task473.js');\n"
B = "require('./test-task473.js');\nrequire('./test-task474.js');\n"
assert s.count(A) == 1, 'run-all.js: якорь test-task473 найден (%d)' % s.count(A)
assert 'test-task474' not in s, 'run-all.js: 474 уже подключён'
s = s.replace(A, B)
open(ra, 'w', encoding='utf-8').write(s)
print('run-all.js: test-task474 подключён')
