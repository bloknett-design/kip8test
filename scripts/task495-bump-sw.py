#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 495: бамп версии SW в тестах kip8test.

sw.js: kipia-test-v718 → kipia-test-v719 (Task 495: блок ввода данных
расчёта таблицы — без поля типа датчика, панель ts-calc-inset).

Порядок важен: СНАЧАЛА гарды v719→v720 (проверки «следующей» версии),
затем ассерты v718→v719 — иначе двойная замена.

Внимание: tests/test-task495.js уже написан под v719 (ассерт) и v720
(гард) — замен его не касается (v718 в нём нет, а строка v719 в нём —
ассерт, не гард: гарды ищут v720).
"""
import io
import glob

OLD_ASSERT = 'kipia-test-v718'
NEW_ASSERT = 'kipia-test-v719'
OLD_GUARD = 'kipia-test-v719'
NEW_GUARD = 'kipia-test-v720'

files = sorted(glob.glob('/home/z/my-project/kip8test/tests/test-*.js'))
files += ['/home/z/my-project/kip8test/tests/run-all.js']

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
        print('%-52s guards v719→v720 x%d, asserts v718→v719 x%d' %
              (f.split('/')[-1], n_guard, n_assert))

print('---')
print('Файлов изменено: %d' % touched)
print('Гардов v719→v720: %d' % total_guard)
print('Ассертов v718→v719: %d' % total_assert)

# Контроль: в тестах не осталось старой версии ассертов
left_v718 = left_v719 = 0
for f in files:
    s = io.open(f, encoding='utf-8').read()
    left_v718 += s.count(OLD_ASSERT)
    left_v719 += s.count("'kipia-test-v719'") + s.count('"kipia-test-v719"')
assert left_v718 == 0, 'остались ассерты v718: %d' % left_v718
print('Контроль: v718 в тестах больше нет; v719 (текущая) = %d вхождений' %
      left_v719)
