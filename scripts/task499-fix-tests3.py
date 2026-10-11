#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 499 (kip8test), фикс-итерация 3: мета-тесты синхронизации окон.

Task 499 расширил окна (471: 11200 → 12000; 472: 10300 → 11200) —
мета-тесты в 475/481 сверяют ЛИТЕРАЛЫ окон чужих файлов, обновляем:
  475: s1(471) 'i - 11200' → 'i - 12000'; s(472) 'i - 10300' → 'i - 11200'
  481: s471 'i - 11200' → 'i - 12000'; s472 'i - 10300' → 'i - 11200'
"""
import io

T = '/home/z/my-project/kip8test/tests/'


def apply(path, edits):
    s = io.open(path, encoding='utf-8').read()
    for name, old, new in edits:
        n = s.count(old)
        assert n == 1, 'ЯКОРЬ %s (%s): вхождений %d (ожидалось 1)' % (name, path, n)
        s = s.replace(old, new)
        print('  OK %s' % name)
    io.open(path, 'w', encoding='utf-8').write(s)


apply(T + 'test-task475.js', [
    ('475: s1(471) окно 12000',
     "        assertTrue(s1.indexOf('i - 11200') !== -1, 'test-task471: 11200 (Task 498)');",
     "        assertTrue(s1.indexOf('i - 12000') !== -1, 'test-task471: 12000 (Task 499)');"),
    ('475: s(472) окно 11200',
     "        assertTrue(s.indexOf('i - 10300') !== -1, 'окно Task 472: 10300 (Task 497)');",
     "        assertTrue(s.indexOf('i - 11200') !== -1, 'окно Task 472: 11200 (Task 499)');"),
])

apply(T + 'test-task481.js', [
    ('481: s471 окно 12000',
     "        assertTrue(s471.indexOf('i - 11200') !== -1, 'test-task471: окно 10600 (Task 495)');",
     "        assertTrue(s471.indexOf('i - 12000') !== -1, 'test-task471: окно 12000 (Task 499)');"),
    ('481: s472 окно 11200',
     "        assertTrue(s472.indexOf('i - 10300') !== -1, 'test-task472: окно 10300 (Task 497)');",
     "        assertTrue(s472.indexOf('i - 11200') !== -1, 'test-task472: окно 11200 (Task 499)');"),
])

print('Task 499 фикс-итерация 3: применена.')
