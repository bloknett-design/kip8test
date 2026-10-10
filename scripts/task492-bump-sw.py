#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 492: SW-бамп kipia-test-v715 → v716 (заявка: в разделе «Датчики
# температуры» кнопки «Все/Избранные» сместить ВНИЗ и оформить как в
# расходомерах; оформление кнопок вернуть как прежде, но крупный шрифт
# оставить и сделать его у всех кнопок; featured-оформление (эффект
# выступа) — у кнопок, добавленных в избранное). sw.js логики не менял —
# только версия + комментарий. Сам sw.js уже поправлен вручную — скрипт
# сверяет и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478):
#   СНАЧАЛА v716 → v717 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v717;
#   ЗАТЕМ v715 → v716 — ассерты «присутствует» едут на текущую.
# tests/test-task492.js — ИСКЛЮЧЁН: его SW-тесты в канонической
# пост-бамп форме (assert v716 + guard v715 отсутствует в sw.js).
import glob

OWN = 'tests/test-task492.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v716';" in sw, \
    'sw.js: CACHE_VERSION не v716 (ручная правка не применена?)'
assert 'kipia-test-v715' not in sw, 'sw.js: v715 ещё остался'
assert 'Task 492' in sw, 'sw.js: нет комментария Task 492'
assert 'ts-bottom-bar' in sw, 'sw.js: нет «ts-bottom-bar»'
assert 'В ИЗБРАННОМ' in sw, 'sw.js: нет «В ИЗБРАННОМ»'
print('sw.js: проверка OK — v716 + Task 492 (нижний бар, шрифт у всех, feat=избранное)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v716 отсутствует» → «v717 отсутствует»
    n_guard = s.count('kipia-test-v716')
    s = s.replace('kipia-test-v716', 'kipia-test-v717')
    # (б) ассерты «v715 присутствует» → «v716 присутствует»
    n_assert = s.count('kipia-test-v715')
    s = s.replace('kipia-test-v715', 'kipia-test-v716')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v715->v716: %d, guards v716->v717: %d)'
      % (len(changed), sum(a for _, a, _ in changed),
         sum(g for _, _, g in changed)))

# --- 2) Сверка: v715 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v715 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v715' in s:
        leftover.append(f)
assert not leftover, 'tests: v715 остался в %r' % leftover
print('tests: v715 полностью замещён (guard v717)')

# --- 3) Окно истории Task 491 в sw.js не вытеснено комментарием 492 ---
#     Комментарий 492 (~290 симв.) вставлен МЕЖДУ комментарием 491 и
#     CACHE_VERSION — якорь «Task 491» отодвинулся от CACHE_VERSION на
#     ~290 симв. Тест test-task491.js проверяет комментарий по вхождению
#     (не по окну), но test-task488.js держит окно 3200 от CACHE_VERSION —
#     сверим, что маркеры 488/491 не вытеснены.
i = sw.index("const CACHE_VERSION = 'kipia-test-v716';")
ctx = sw[max(0, i - 3200):i]
for marker in ['Task 488', 'Task 491', 'кнопк', 'xlsx', 'docProps']:
    assert marker in ctx, 'окно 3200: маркер %r вытеснен' % marker
print('sw.js: окно истории 3200 (Task 488/491) сохранено')

# --- 4) Итог ---
print('БАМП ЗАВЕРШЁН: v715 → v716, guard v717.')
