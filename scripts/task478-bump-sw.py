#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 478: SW-бамп kipia-test-v701 → v702 (карточка прибора КИП ИОС —
# строка «Период ремонта» цветная по состоянию ППР: в гр. ППР + вид
# ТО/К/П + срок не просрочен — ЗЕЛЁНЫЙ; просрочен — КРАСНЫЙ; остальные
# — обычный цвет. devPprStatusClass + CSS dev-ppr-ok/bad в index.html.
# sw.js логики не менял — только версия + комментарий).
# Сам sw.js уже поправлен вручную (версия + комментарий Task 478) —
# скрипт сверяет состояние и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v702 → v703 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v703;
#   ЗАТЕМ v701 → v702 — ассерты «присутствует» едут на текущую.
# tests/test-task478.js — ИСКЛЮЧЁН: его SW-тесты уже в канонической
# пост-бамп форме (assert v702 + guard v703 + v701 отсутствует).
# ПЛЮС адаптация окон истории версий sw.js (прецедент Task 475/476):
#   комментарий Task 478 (~340 симв., 6 строк) отодвинул якоря:
#   test-task461.js  5300 → 6000 (Task 461 теперь ~5362 симв.);
#   test-task471.js  2700 → 3400 (Task 471 теперь ~2800);
#   test-task472.js  2100 → 2900 (Task 472 ~2251) и
#                     2700 → 3400 (Task 471 в контексте 472);
#   test-task474.js  1700 → 2500 (Task 474 ~1878) + дистанции
#                     2700 → 3400 (Task 471) и 5300 → 6000 (Task 461);
#   test-task475.js  литералы проверки чужих окон (5300/2700/2100/
#                     1700 → 6000/3400/2900/2500);
#   test-task476.js  дистанции 1700/2100/2700/5300 → 2500/2900/3400/6000;
#   test-task477.js  дистанции 1700/2100/2700/5300 → 2500/2900/3400/6000.
import glob

OWN = 'tests/test-task478.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v702';" in sw, \
    'sw.js: CACHE_VERSION не v702 (ручная правка не применена?)'
assert 'kipia-test-v701' not in sw, 'sw.js: v701 ещё остался'
assert 'Task 478' in sw, 'sw.js: нет комментария Task 478'
assert 'Период ремонта' in sw, 'sw.js: нет упоминания строки Период ремонта'
print('sw.js: проверка OK — v702 + Task 478 (ППР-индикация)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v702 отсутствует» → «v703 отсутствует»
    n_guard = s.count('kipia-test-v702')
    s = s.replace('kipia-test-v702', 'kipia-test-v703')
    # (б) ассерты «v701 присутствует» → «v702 присутствует»
    n_assert = s.count('kipia-test-v701')
    s = s.replace('kipia-test-v701', 'kipia-test-v702')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v701->v702: %d, guards v702->v703: %d)'
      % (len(changed), sum(a for _, a, _ in changed), sum(g for _, _, g in changed)))

# --- 2) Окна истории версий sw.js ---
def patch(fname, old, new, note):
    s = open(fname, encoding='utf-8').read()
    assert old in s, '%s: не найдено окно %r' % (fname, old)
    assert new not in s, '%s: окно %r уже стоит (повторный прогон?)' % (fname, new)
    s = s.replace(old, new, 1)
    open(fname, 'w', encoding='utf-8').write(s)
    print('%s: окно %r → %r (%s)' % (fname, old, new, note))

# test-task461.js — окно Task 461
patch('tests/test-task461.js',
      'const above = SW_SRC.slice(Math.max(0, i - 5300), i);',
      'const above = SW_SRC.slice(Math.max(0, i - 6000), i);',
      'Task 478 (~340 симв.) отодвинул Task 461 до ~5362')

# test-task471.js — окно Task 471
patch('tests/test-task471.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2700), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 3400), i);',
      'Task 471 теперь ~2800')

# test-task472.js — ДВА окна: контекст Task 471 (2700) и Task 472 (2100)
patch('tests/test-task472.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2700), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 3400), i);',
      'Task 471 (контекст 472) теперь ~2800')
patch('tests/test-task472.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2100), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2900), i);',
      'Task 472 теперь ~2251')

# test-task474.js — окно Task 474 + дистанции 471/461
patch('tests/test-task474.js',
      'const ctx = SW_SRC.slice(Math.max(0, i - 1700), i);',
      'const ctx = SW_SRC.slice(Math.max(0, i - 2500), i);',
      'Task 474 теперь ~1878')
patch('tests/test-task474.js',
      'assertTrue(i471 !== -1 && (i - i471) < 2700,',
      'assertTrue(i471 !== -1 && (i - i471) < 3400,',
      'дистанция Task 471 ~2800')
patch('tests/test-task474.js',
      'assertTrue(i461 !== -1 && (i - i461) < 5300,',
      'assertTrue(i461 !== -1 && (i - i461) < 6000,',
      'дистанция Task 461 ~5362')

# test-task475.js — литералы проверки ЧУЖИХ окон (section 9)
patch('tests/test-task475.js',
      "assertTrue(s.indexOf('i - 5300') !== -1, 'окно расширено до 5300');",
      "assertTrue(s.indexOf('i - 6000') !== -1, 'окно расширено до 6000');",
      'test-task461 теперь с окном 6000')
patch('tests/test-task475.js',
      "assertTrue(s1.indexOf('i - 2700') !== -1, 'test-task471: 2700');",
      "assertTrue(s1.indexOf('i - 3400') !== -1, 'test-task471: 3400');",
      'test-task471 теперь 3400')
patch('tests/test-task475.js',
      "assertTrue(s2.indexOf('i - 2700') !== -1, 'test-task472: 2700');",
      "assertTrue(s2.indexOf('i - 3400') !== -1, 'test-task472: 3400');",
      'контекст Task 471 в 472 теперь 3400')
patch('tests/test-task475.js',
      "assertTrue(s.indexOf('i - 2100') !== -1, 'окно Task 472: 2100');",
      "assertTrue(s.indexOf('i - 2900') !== -1, 'окно Task 472: 2900');",
      'test-task472 теперь 2900')
patch('tests/test-task475.js',
      "assertTrue(s.indexOf('i - 1700') !== -1, 'окно Task 474: 1700');",
      "assertTrue(s.indexOf('i - 2500') !== -1, 'окно Task 474: 2500');",
      'test-task474 теперь 2500')

# test-task476.js — дистанции (section 10)
patch('tests/test-task476.js',
      "assertTrue(i474 !== -1 && (i - i474) < 1700, 'якорь Task 474 виден');",
      "assertTrue(i474 !== -1 && (i - i474) < 2500, 'якорь Task 474 виден');",
      'Task 474 теперь ~1878')
patch('tests/test-task476.js',
      "assertTrue(i472 !== -1 && (i - i472) < 2100, 'якорь Task 472 виден');",
      "assertTrue(i472 !== -1 && (i - i472) < 2900, 'якорь Task 472 виден');",
      'Task 472 теперь ~2251')
patch('tests/test-task476.js',
      "assertTrue(i471 !== -1 && (i - i471) < 2700, 'якорь Task 471 виден');",
      "assertTrue(i471 !== -1 && (i - i471) < 3400, 'якорь Task 471 виден');",
      'Task 471 теперь ~2800')
patch('tests/test-task476.js',
      "assertTrue(i461 !== -1 && (i - i461) < 5300, 'якорь Task 461 виден');",
      "assertTrue(i461 !== -1 && (i - i461) < 6000, 'якорь Task 461 виден');",
      'Task 461 теперь ~5362')

# test-task477.js — дистанции (section 6)
patch('tests/test-task477.js',
      "assertTrue(i474 !== -1 && (i - i474) < 1700, 'Task 474 (~1539) в окне 1700');",
      "assertTrue(i474 !== -1 && (i - i474) < 2500, 'Task 474 (~1878) в окне 2500');",
      'Task 478 отодвинул Task 474')
patch('tests/test-task477.js',
      "assertTrue(i472 !== -1 && (i - i472) < 2100, 'Task 472 (~1912) в окне 2100');",
      "assertTrue(i472 !== -1 && (i - i472) < 2900, 'Task 472 (~2251) в окне 2900');",
      'Task 478 отодвинул Task 472')
patch('tests/test-task477.js',
      "assertTrue(i471 !== -1 && (i - i471) < 2700, 'Task 471 (~2461) в окне 2700');",
      "assertTrue(i471 !== -1 && (i - i471) < 3400, 'Task 471 (~2800) в окне 3400');",
      'Task 478 отодвинул Task 471')
patch('tests/test-task477.js',
      "assertTrue(i461 !== -1 && (i - i461) < 5300, 'Task 461 (~5023) в окне 5300');",
      "assertTrue(i461 !== -1 && (i - i461) < 6000, 'Task 461 (~5362) в окне 6000');",
      'Task 478 отодвинул Task 461')

# --- 3) Комментарии к окнам (после правки чисел) ---
def add_note(fname, anchor, note):
    s = open(fname, encoding='utf-8').read()
    assert anchor in s, '%s: якорь комментария не найден' % fname
    if note in s:
        return
    s = s.replace(anchor, anchor + '\n' + note, 1)
    open(fname, 'w', encoding='utf-8').write(s)
    print('%s: добавлен комментарий окна' % fname)

add_note('tests/test-task461.js',
         'const above = SW_SRC.slice(Math.max(0, i - 6000), i);',
         '        // Task 478: окно 5300 → 6000 — комментарий ППР-индикации\n'
         '        // (~340 симв.) отодвинул Task 461 до ~5362.')
add_note('tests/test-task471.js',
         'const ctx = SW_SRC.slice(Math.max(0, i - 3400), i);',
         '        // Task 478: окно 2700 → 3400 — комментарий ППР-индикации\n'
         '        // (~340 симв.) отодвинул Task 471 до ~2800.')
add_note('tests/test-task472.js',
         'const ctx = SW_SRC.slice(Math.max(0, i - 2900), i);',
         '        // Task 478: окна 2100 → 2900 (Task 472 ~2251) и\n'
         '        // 2700 → 3400 (Task 471 ~2800) — комментарий ППР-индикации.')
add_note('tests/test-task474.js',
         'const ctx = SW_SRC.slice(Math.max(0, i - 2500), i);',
         '        // Task 478: окна 1700 → 2500 (Task 474 ~1878), 2700 → 3400\n'
         '        // (Task 471 ~2800), 5300 → 6000 (Task 461 ~5362) — комментарий\n'
         '        // ППР-индикации карточки прибора (~340 симв.).')
add_note('tests/test-task477.js',
         "assertTrue(i474 !== -1 && (i - i474) < 2500, 'Task 474 (~1878) в окне 2500');",
         '        // Task 478: окна расширены (комментарий ~340 симв.):\n'
         '        // 474 1700→2500, 472 2100→2900, 471 2700→3400, 461 5300→6000.')

# --- 4) Сверка дистанций якорей (после всех правок) ---
i = sw.index("const CACHE_VERSION = 'kipia-test-v702';")
for name, window in [('Task 474', 2500), ('Task 472', 2900),
                     ('Task 471', 3400), ('Task 461', 6000)]:
    j = sw.rindex(name, 0, i)
    dist = i - j
    assert dist < window, \
        '%s: дистанция %d вылезла за окно %d — расширить!' % (name, dist, window)
    print('%s: дистанция %d < окна %d (запас %d)' % (name, dist, window, window - dist))

print('OK: бамп v701→v702 + окна истории адаптированы (6000/3400/2900/2500)')
