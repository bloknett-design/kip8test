#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 464: бамп версий в тестах kip8test (SW kipia-test-v687 → v688).
# Два прохода (порядок КРИТИЧЕН — иначе guards перезапишут ассерты):
#   1) kipia-test-v688 → kipia-test-v689  (guards «версии ещё нет»)
#   2) kipia-test-v687 → kipia-test-v688  (ассерты текущей версии)
# Сначала guards: v688 в тестах сейчас ТОЛЬКО негативные («версии v688
# быть не должно»), их поднимаем до v689; затем позитивные ассерты v687
# становятся v688. sw.js правится отдельно (task464-patch).
import io
import os

TDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests')
MAP = [
    ('kipia-test-v688', 'kipia-test-v689'),
    ('kipia-test-v687', 'kipia-test-v688'),
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
