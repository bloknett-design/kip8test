#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 497: бамп версии SW в тестах kip8test.

sw.js: kipia-test-v720 → kipia-test-v721 (Task 497: расходомеры —
избранное показывается из кэша до ответа сервера, заглушка «Нет
избранных» не появляется в loading/error при наличии избранного).

Порядок важен: СНАЧАЛА гарды v721→v722 (проверки «следующей»
версии), затем ассерты v720→v721 — иначе двойная замена.

Внимание: tests/test-task497.js уже написан под v721 (ассерт) и
v722 (гард) — файл ИСКЛЮЧЁН из замен (урок Task 495: бамп-скрипт
бампает НОВЫЙ тест, потом версии приходится восстанавливать).

Ожидания по счётчикам (замер до запуска):
  v720 в старых тестах: 622 (618 ассертов после Task 496 + 4 в
    test-task496.js: ассерт в коде/имени теста/сообщении + шапка)
  v721 в старых тестах: 150 (149 гардов после Task 496 + 1 гард
    test-task496.js)
"""
import io
import glob

T = '/home/z/my-project/kip8test/tests'
SKIP = T + '/test-task497.js'  # новый тест уже под v721/v722

files = sorted(glob.glob(T + '/test-*.js')) + [T + '/run-all.js']
files = [f for f in files if f != SKIP]

OLD_ASSERT = 'kipia-test-v720'
NEW_ASSERT = 'kipia-test-v721'
OLD_GUARD = 'kipia-test-v721'
NEW_GUARD = 'kipia-test-v722'

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
        print('%-52s guards v721→v722 x%d, asserts v720→v721 x%d' %
              (f.split('/')[-1], n_guard, n_assert))

print('---')
print('Файлов изменено: %d' % touched)
print('Гардов v721→v722: %d' % total_guard)
print('Ассертов v720→v721: %d' % total_assert)
assert total_guard == 150, 'гардов %d ≠ 150' % total_guard
assert total_assert == 622, 'ассертов %d ≠ 622' % total_assert

# Контроль: в старых тестах не осталось v720; новый тест не тронут
left_v720 = 0
for f in files:
    s = io.open(f, encoding='utf-8').read()
    left_v720 += s.count('kipia-test-v720')
assert left_v720 == 0, 'остались ассерты v720: %d' % left_v720

new = io.open(SKIP, encoding='utf-8').read()
assert new.count("'kipia-test-v721';") >= 1, 'ассерт v721 в новом тесте жив'
assert new.count('kipia-test-v722') == 1, 'гард v722 в новом тесте жив'
print('Контроль: v720 в старых тестах нет; test-task497.js не тронут '
      '(v721 ассерт / v722 гард). Всё ок.')
