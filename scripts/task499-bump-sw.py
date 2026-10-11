#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 499: бамп версии SW в тестах kip8test.

sw.js: kipia-test-v722 → kipia-test-v723 (Task 499: подсказки
диапазонов НСХ — плейсхолдеры полей ППР; диапазон Cu α = 0,00428
расширен до −180…+200; НСХ меди ниже 0 °C по ф. 5.2.3 ГОСТ).

Порядок важен: СНАЧАЛА гарды v723→v724 (проверки «следующей»
версии), затем ассерты v722→v723 — иначе двойная замена.

Внимание: tests/test-task499.js ещё НЕ создан на момент запуска —
бамп идёт по текущим файлам (урок Task 495: новый тест пишется под
v723/v724 ПОСЛЕ бампа и бампом не трогается).

Ожидания (замер до запуска):
  v722 в тестах: 632 (все ассерты текущей версии)
  v723 в тестах: 153 (гарды следующей версии)
"""
import io
import glob

T = '/home/z/my-project/kip8test/tests'

files = sorted(glob.glob(T + '/test-*.js')) + [T + '/run-all.js']

OLD_ASSERT = 'kipia-test-v722'
NEW_ASSERT = 'kipia-test-v723'
OLD_GUARD = 'kipia-test-v723'
NEW_GUARD = 'kipia-test-v724'

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
print('Гардов v723→v724: %d' % total_guard)
print('Ассертов v722→v723: %d' % total_assert)
assert total_guard == 153, 'гардов %d ≠ 153' % total_guard
assert total_assert == 632, 'ассертов %d ≠ 632' % total_assert

# Контроль: живых v722 не осталось
left = 0
for f in files:
    left += io.open(f, encoding='utf-8').read().count('kipia-test-v722')
assert left == 0, 'остались ассерты v722: %d' % left
print('Контроль: v722 в тестах нет. Бамп Task 499 ок.')
