#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 488: SW-бамп kipia-test-v711 → v712 (заявка из 2 частей:
# (1) «кнопка отметки осталась» — из окна «Мероприятия в этот день»
# удалён read-only маркер ws-done-chk (зелёный квадрат ✓ выглядел
# кнопкой; окно — чисто текстовая справка, состояние выполнения
# несут рамка бейджа сетки и галочка карточки работника);
# (2) «все сохранения Excel — простой редактируемый xlsx» — числа
# ЧИСЛАМИ (дни 1–31 шапки табеля прежде были текстом), docProps
# core/app + bookViews, [Content_Types].xml первым в zip архива,
# вырезание XML-запрещённых управляющих символов, xml:space при
# краевом пробеле). sw.js логики не менял — только версия +
# комментарий. Сам sw.js уже поправлен вручную — скрипт сверяет
# и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478):
#   СНАЧАЛА v712 → v713 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v713;
#   ЗАТЕМ v711 → v712 — ассерты «присутствует» едут на текущую.
# tests/test-task488.js — ИСКЛЮЧЁН: его SW-тесты в канонической
# пост-бамп форме (assert v712 + guard v711 отсутствует).
import glob

OWN = 'tests/test-task488.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v712';" in sw, \
    'sw.js: CACHE_VERSION не v712 (ручная правка не применена?)'
assert 'kipia-test-v711' not in sw, 'sw.js: v711 ещё остался'
assert 'Task 488' in sw, 'sw.js: нет комментария Task 488'
assert 'маркер' in sw, 'sw.js: нет «маркер» (часть 1 заявки)'
assert 'xlsx' in sw, 'sw.js: нет «xlsx» (часть 2 заявки)'
assert 'docProps' in sw, 'sw.js: нет «docProps» (часть 2 заявки)'
print('sw.js: проверка OK — v712 + Task 488 (маркер убран + простой xlsx)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v712 отсутствует» → «v713 отсутствует»
    n_guard = s.count('kipia-test-v712')
    s = s.replace('kipia-test-v712', 'kipia-test-v713')
    # (б) ассерты «v711 присутствует» → «v712 присутствует»
    n_assert = s.count('kipia-test-v711')
    s = s.replace('kipia-test-v711', 'kipia-test-v712')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v711->v712: %d, guards v712->v713: %d)'
      % (len(changed), sum(a for _, a, _ in changed),
         sum(g for _, _, g in changed)))

# --- 2) Сверка: v711 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v711 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v711' in s:
        leftover.append(f)
assert not leftover, 'v711 остался в: ' + ', '.join(leftover)
print('tests: v711 не осталось (кроме OWN-негативов) — бамп чист')
