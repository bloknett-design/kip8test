#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 469: бамп версий в тестах kip8test (SW kipia-test-v692 → v693).
# Два прохода (порядок КРИТИЧЕН — иначе guards перезапишут ассерты):
#   1) kipia-test-v693 → kipia-test-v694  (guards «версии ещё нет»)
#   2) kipia-test-v692 → kipia-test-v693  (ассерты текущей версии)
# Сначала guards: v693 в тестах сейчас ТОЛЬКО негативные («версии v693
# быть не должно»), их поднимаем до v694; затем позитивные ассерты v692
# становятся v693. sw.js уже поправлен вручную (CACHE_VERSION v693).
# test-task469.js пишется ПОСЛЕ этого скрипта — сразу с финальным v693.
import io
import os

TDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests')
MAP = [
    ('kipia-test-v693', 'kipia-test-v694'),
    ('kipia-test-v692', 'kipia-test-v693'),
]

tot = {}
files_changed = 0
for name in sorted(os.listdir(TDIR)):
    if not name.startswith('test-') or not name.endswith('.js'):
        continue
    p = os.path.join(TDIR, name)
    with io.open(p, encoding='utf-8') as f:
        s = f.read()
    orig = s
    for old, new in MAP:
        if old in s:
            tot[old] = tot.get(old, 0) + s.count(old)
            s = s.replace(old, new)
    if s != orig:
        with io.open(p, 'w', encoding='utf-8') as f:
            f.write(s)
        files_changed += 1

print('изменено файлов: %d' % files_changed)
for old, new in MAP:
    print('%s → %s: %d замен' % (old, new, tot.get(old, 0)))
