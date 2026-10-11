#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 498: бамп версии SW в тестах kip8test.

sw.js: kipia-test-v721 → kipia-test-v722 (Task 498: пределы НСХ
в полях ППР, заголовок — только тип датчика крупнее, формула pt1391
ниже 0 °C по таблице А.2 ГОСТ 6651-2009).

Порядок важен: СНАЧАЛА гарды v722→v723 (проверки «следующей»
версии), затем ассерты v721→v722 — иначе двойная замена.

Внимание: tests/test-task498.js ещё НЕ создан на момент запуска —
бамп идёт по текущим файлам (урок Task 495: новый тест пишется под
v722/v723 ПОСЛЕ бампа и бампом не трогается).

Ожидания (замер до запуска):
  v721 в тестах: 626 (622 ассерта старых тестов + 4 в test-task497.js)
  v722 в тестах: 151 (150 гардов старых тестов + 1 гард test-task497.js)
"""
import io
import glob

T = '/home/z/my-project/kip8test/tests'

files = sorted(glob.glob(T + '/test-*.js')) + [T + '/run-all.js']

OLD_ASSERT = 'kipia-test-v721'
NEW_ASSERT = 'kipia-test-v722'
OLD_GUARD = 'kipia-test-v722'
NEW_GUARD = 'kipia-test-v723'

total_guard = 0
total_assert = 0
touched = 0
for f in files:
    s = io.open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count(OLD_GUARD)
    if n_guard:
        s = s.replace(OLD_GUARD, NEW_GUARD)
        total_guard += n_guard
    n_assert = s.count(OLD_ASSERT)
    if n_assert:
        s = s.replace(OLD_ASSERT, NEW_ASSERT)
        total_assert += n_assert
    if s != orig:
        io.open(f, 'w', encoding='utf-8').write(s)
        touched += 1

print('Файлов изменено: %d' % touched)
print('Гардов v722→v723: %d' % total_guard)
print('Ассертов v721→v722: %d' % total_assert)
assert total_guard == 151, 'гардов %d ≠ 151' % total_guard
assert total_assert == 626, 'ассертов %d ≠ 626' % total_assert

# Контроль: живых v721 не осталось
left = 0
for f in files:
    left += io.open(f, encoding='utf-8').read().count('kipia-test-v721')
assert left == 0, 'остались ассерты v721: %d' % left
print('Контроль: v721 в тестах нет. Бамп Task 498 ок.')
