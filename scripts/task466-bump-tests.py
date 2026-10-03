#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 466: бамп версий в тестах kip8test (SW kipia-test-v689 → v690).
# Два прохода (порядок КРИТИЧЕН — иначе guards перезапишут ассерты):
#   1) kipia-test-v690 → kipia-test-v691  (guards «версии ещё нет»)
#   2) kipia-test-v689 → kipia-test-v690  (ассерты текущей версии)
# Сначала guards: v690 в тестах сейчас ТОЛЬКО негативные («версии v690
# быть не должно»), их поднимаем до v691; затем позитивные ассерты v689
# становятся v690. sw.js уже поправлен вручную (CACHE_VERSION v690).
# test-task466.js пишется ПОСЛЕ этого скрипта — сразу с финальным v690.
import io
import os

TDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests')
MAP = [
    ('kipia-test-v690', 'kipia-test-v691'),
    ('kipia-test-v689', 'kipia-test-v690'),
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
