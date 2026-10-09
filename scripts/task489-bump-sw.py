#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 489: SW-бамп kipia-test-v712 → v713 (заявка: в файле
# табель_КИП_ИОС столбец «ФИО» таблицы «Сотрудники» разделён на
# три столбца — фамилия/имя/отчество (полные данные), добавлен
# столбец «дата_рождения» перед «комментарием»; полное ФИО —
# только в карте работника (блок профиля) и на листе «Работники»
# Excel-архива, в других местах — как прежде кратко; дата
# рождения — в конце списка профиля; код читает/пишет столбцы по
# ЗАГОЛОВКАМ строки 1 — столбцы сместились). sw.js логики не
# менял — только версия + комментарий. Сам sw.js уже поправлен
# вручную — скрипт сверяет и бампит ТЕСТЫ.
# Порядок замен в tests/ ВАЖЕН (конвенция Task 478):
#   СНАЧАЛА v713 → v714 — ВСЕ guard-ы «отсутствует» переезжают на
#   новую несуществующую v714;
#   ЗАТЕМ v712 → v713 — ассерты «присутствует» едут на текущую.
# tests/test-task489.js — ИСКЛЮЧЁН: его SW-тесты в канонической
# пост-бамп форме (assert v713 + guard v712 отсутствует).
import glob

OWN = 'tests/test-task489.js'

# --- 0) Сверка sw.js: уже в целевом состоянии ---
sw = open('sw.js', encoding='utf-8').read()
assert "const CACHE_VERSION = 'kipia-test-v713';" in sw, \
    'sw.js: CACHE_VERSION не v713 (ручная правка не применена?)'
assert 'kipia-test-v712' not in sw, 'sw.js: v712 ещё остался'
assert 'Task 489' in sw, 'sw.js: нет комментария Task 489'
assert 'фамилия' in sw, 'sw.js: нет «фамилия»'
assert 'дата_рождения' in sw, 'sw.js: нет «дата_рождения»'
assert 'employeesSplitInit' in sw, 'sw.js: нет «employeesSplitInit»'
print('sw.js: проверка OK — v713 + Task 489 (ФИО → части + дата рождения)')

# --- 1) Бамп версий в тестах ---
changed = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    orig = s
    # (а) guards «v713 отсутствует» → «v714 отсутствует»
    n_guard = s.count('kipia-test-v713')
    s = s.replace('kipia-test-v713', 'kipia-test-v714')
    # (б) ассерты «v712 присутствует» → «v713 присутствует»
    n_assert = s.count('kipia-test-v712')
    s = s.replace('kipia-test-v712', 'kipia-test-v713')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests: изменено файлов %d (ассерты v712->v713: %d, guards v713->v714: %d)'
      % (len(changed), sum(a for _, a, _ in changed),
         sum(g for _, _, g in changed)))

# --- 2) Сверка: v712 не осталось НИГДЕ в tests/ (кроме OWN, где это
#     осознанный негативный ассерт «v712 отсутствует в sw.js») ---
leftover = []
for f in sorted(glob.glob('tests/*.js')):
    if f.replace('\\', '/') == OWN:
        continue
    s = open(f, encoding='utf-8').read()
    if 'kipia-test-v712' in s:
        leftover.append(f)
assert not leftover, 'tests: v712 остался в %r' % leftover
print('tests: v712 полностью замещён (guard v714)')

# --- 3) Итог ---
print('БАМП ЗАВЕРШЁН: v712 → v713, guard v714.')
