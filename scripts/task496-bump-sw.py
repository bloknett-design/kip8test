#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 496: бамп версии SW в тестах kip8test.

sw.js: kipia-test-v719 → kipia-test-v720 (Task 496: ППР — Enter
закрывает клавиатуру: enterkeyhint done + tempQueryEnterBlur).

Порядок важен: СНАЧАЛА гарды v720→v721 (проверки «следующей»
версии), затем ассерты v719→v720 — иначе двойная замена.

Внимание: tests/test-task496.js уже написан под v720 (ассерт) и
v721 (гард) — файл ИСКЛЮЧЁН из замен (урок Task 495: бамп-скрипт
бампает НОВЫЙ тест, потом версии приходится восстанавливать).

Ожидания по счётчикам (замер до запуска):
  v719 всего 619 (из них 1 — негатив-чек НОВОГО теста) → 618 ассертов
  v720: rg -c 153 СТРОКИ (4 строки — новый тест) → 149 гардов
"""
import io
import glob

T = '/home/z/my-project/kip8test/tests'
SKIP = T + '/test-task496.js'  # новый тест уже под v720/v721

files = sorted(glob.glob(T + '/test-*.js')) + [T + '/run-all.js']
files = [f for f in files if f != SKIP]

OLD_ASSERT = 'kipia-test-v719'
NEW_ASSERT = 'kipia-test-v720'
OLD_GUARD = 'kipia-test-v720'
NEW_GUARD = 'kipia-test-v721'

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
        print('%-52s guards v720→v721 x%d, asserts v719→v720 x%d' %
              (f.split('/')[-1], n_guard, n_assert))

print('---')
print('Файлов изменено: %d' % touched)
print('Гардов v720→v721: %d (ожидалось 149 (rg -c считал строки: 153 − 4 строки нового теста))' % total_guard)
print('Ассертов v719→v720: %d (ожидалось 618)' % total_assert)
assert total_guard == 149, 'гардов %d ≠ 149' % total_guard
assert total_assert == 618, 'ассертов %d ≠ 618' % total_assert

# Контроль: в старых тестах не осталось v719; новый тест не тронут
left_v719 = 0
for f in files:
    s = io.open(f, encoding='utf-8').read()
    left_v719 += s.count('kipia-test-v719')
assert left_v719 == 0, 'остались ассерты v719: %d' % left_v719

new = io.open(SKIP, encoding='utf-8').read()
assert new.count("'kipia-test-v720';") >= 1, 'ассерт v720 в новом тесте жив'
assert new.count('kipia-test-v721') == 1, 'гард v721 в новом тесте жив'
assert new.count('kipia-test-v719') == 1, 'негатив-чек v719 в новом тесте жив'
print('Контроль: v719 в старых тестах нет; test-task496.js не тронут '
      '(v720 ассерт / v721 гард / v719 негатив). Всё ок.')
