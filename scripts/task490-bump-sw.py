#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 490: SW-бамп kipia-test-v713 → v714 (заявка: в мобильной
# версии раздела «Датчики температуры» кнопки с градуировками — по
# две в одной строке, с одинаковой градуировкой рядом; на кнопках
# термометров только градуировка и температурный коэффициент, у
# термопар — градуировку и наименование; ТХА (K) и ТХК (L) вместе;
# остальные пары по усмотрению). sw.js логики не менял — только
# версия + комментарий. Сам sw.js уже поправлен вручную — скрипт
# сверяет и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478):
#   СНАЧАЛА v714 → v715 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v715;
#   ЗАТЕМ v713 → v714 — ассерты «присутствует» едут на текущую.
# tests/test-task490.js — ИСКЛЮЧЁН: его SW-тесты в канонической
# пост-бамп форме (assert v714 + guard v713 отсутствует).
import glob

OWN = 'tests/test-task490.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v714';" in sw, \
    'sw.js: CACHE_VERSION не v714 (ручная правка не применена?)'
assert 'kipia-test-v713' not in sw, 'sw.js: v713 ещё остался'
assert 'Task 490' in sw, 'sw.js: нет комментария Task 490'
assert 'по ДВЕ в строке' in sw, 'sw.js: нет «по ДВЕ в строке»'
assert 'ТХК (L) вместе' in sw, 'sw.js: нет «ТХК (L) вместе»'
assert 'градуировк' in sw, 'sw.js: нет «градуировк»'
print('sw.js: проверка OK — v714 + Task 490 (кнопки по две, пары градуировок)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v714 отсутствует» → «v715 отсутствует»
    n_guard = s.count('kipia-test-v714')
    s = s.replace('kipia-test-v714', 'kipia-test-v715')
    # (б) ассерты «v713 присутствует» → «v714 присутствует»
    n_assert = s.count('kipia-test-v713')
    s = s.replace('kipia-test-v713', 'kipia-test-v714')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v713->v714: %d, guards v714->v715: %d)'
      % (len(changed), sum(a for _, a, _ in changed),
         sum(g for _, _, g in changed)))

# --- 2) Сверка: v713 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v713 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v713' in s:
        leftover.append(f)
assert not leftover, 'tests: v713 остался в %r' % leftover
print('tests: v713 полностью замещён (guard v715)')

# --- 3) Окно истории Task 488 в sw.js не вытеснено комментарием 490 ---
#     (окно расширено 1800 → 2200 в самом тесте — Task 490 адаптация,
#     комментарий 490 в sw.js ~480 символов сместил маркеры 488)
#     ВАЖНО: скрипт ОДНОРАЗОВЫЙ — повторный запуск после применения
#     замен (шаг 1) недопустим (v714-ассерты уедут в v715).
i = sw.index("const CACHE_VERSION = 'kipia-test-v714';")
ctx = sw[max(0, i - 2200):i]
for marker in ['Task 488', 'кнопк', 'xlsx', 'docProps', 'ЧИСЛА']:
    assert marker in ctx, 'окно 2200: маркер %r вытеснен' % marker
print('sw.js: окно истории Task 488 (2200) сохранено')

# --- 4) Итог ---
print('БАМП ЗАВЕРШЁН: v713 → v714, guard v715.')
