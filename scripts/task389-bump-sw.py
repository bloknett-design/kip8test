#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 389: SW-бамп kipia-test-v616 → v617 (index.html менялся —
# окно «Мероприятия»: прошедшие — общий фон окна; страница
# «Работники»: кнопка «Добавить работника» на «Общей» вкладке,
# численность (текущая — автоподсчёт, по штату — константа),
# сплошные фоны ярлыков/окон вкладок, блок с левого края).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v617 → v618 — ВСЕ guard-ы «отсутствует» (assertFalse/
#   assertTrue/имена тестов/сообщения) переезжают на новую
#   несуществующую v618;
#   ЗАТЕМ v616 → v617 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v616'"
new = "CACHE_VERSION = 'kipia-test-v617'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v616'
assert 'kipia-test-v617' not in sw, 'sw.js: v617 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v616 -> kipia-test-v617')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v617 отсутствует» → «v618 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v617')
    s = s.replace('kipia-test-v617', 'kipia-test-v618')
    # 2) ассерты «v616 присутствует» → «v617 присутствует»
    n_assert = s.count('kipia-test-v616')
    s = s.replace('kipia-test-v616', 'kipia-test-v617')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v616→v617: %d, guard v617→v618: %d)' % (f, a, g))
