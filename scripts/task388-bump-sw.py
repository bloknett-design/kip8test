#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 388: SW-бамп kipia-test-v615 → v616 (index.html менялся —
# миниатюры мероприятий всегда сплошные с цветом кода; краткие
# обозначения кодов в кратком виде панели «Обозначения»; итоги
# учёта в видах сменный/дневной; значок раскрытия окон бара в
# правом верхнем углу; страница «Работники» — вкладки-ярлыки).
# Порядок замен в tests/ ВАЖЕН (конвенция прежних бампов):
#   СНАЧАЛА v616 → v617 — ВСЕ guard-ы «отсутствует» (assertFalse/
#   assertTrue/имена тестов/сообщения) переезжают на новую
#   несуществующую v617;
#   ЗАТЕМ v615 → v616 — ассерты «присутствует» едут на текущую.
import glob

sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v615'"
new = "CACHE_VERSION = 'kipia-test-v616'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v615'
assert 'kipia-test-v616' not in sw, 'sw.js: v616 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v615 -> kipia-test-v616')

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    # 1) guards «v616 отсутствует» → «v617 отсутствует» (все формы)
    n_guard = s.count('kipia-test-v616')
    s = s.replace('kipia-test-v616', 'kipia-test-v617')
    # 2) ассерты «v615 присутствует» → «v616 присутствует»
    n_assert = s.count('kipia-test-v615')
    s = s.replace('kipia-test-v615', 'kipia-test-v616')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v615→v616: %d, guard v616→v617: %d)' % (f, a, g))
