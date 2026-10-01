#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 459: адаптация test-task445.js / test-task446.js — харнессы
# _workersArchiveData/_buildArchiveWorkbook получают НОВЫЙ метод
# _ppePosNoGrade (должность СИЗ без разрядов), комментарии про
# «сортировку по таб. №» переписаны на сортировку по фамилиям.
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def patch(path, pairs):
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    for old, new, label in pairs:
        n = s.count(old)
        assert n == 1, '%s: ЯКОРЬ %d РАЗ (ожидался 1): %s' % (
            os.path.basename(path), n, label)
        s = s.replace(old, new)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: %d замен' % (os.path.basename(path), len(pairs)))

# ---------------- test-task445.js ----------------
patch(os.path.join(ROOT, 'tests', 'test-task445.js'), [
    # харнесс dataHost: новый метод рядом с _workersArchiveData
    ("""            methodText(INDEX_SRC, '_workersArchiveData') + ',\\n' +
            "_isInstrType: function(t) { return t === 'инструктаж' || t === 'проверка_знаний'; }," +
""",
     """            methodText(INDEX_SRC, '_workersArchiveData') + ',\\n' +
            methodText(INDEX_SRC, '_ppePosNoGrade') + ',\\n' +
            "_isInstrType: function(t) { return t === 'инструктаж' || t === 'проверка_знаний'; }," +
""", 'dataHost: + _ppePosNoGrade'),
    # комментарий и подписи ассертов СИЗ: фамилии вместо таб. №
    ("""        // сортировка по таб. №: 017 (очки) → 031 (каска)
        assertEqual(d.ppe[1][2], 'Очки закрытые', 'первый — таб 017');
        assertEqual(d.ppe[2][2], 'Каска защитная', 'второй — таб 031');""",
     """        // Task 459: сортировка по ФАМИЛИЯМ — Иванов (очки) →
        // Сидоров (каска); таб. № больше не первичный ключ
        assertEqual(d.ppe[1][2], 'Очки закрытые',
            'первый — Иванов (по фамилии, Task 459)');
        assertEqual(d.ppe[2][2], 'Каска защитная',
            'второй — Сидоров (по фамилии)');""", 'СИЗ: подписи по фамилиям'),
])

# ---------------- test-task446.js ----------------
patch(os.path.join(ROOT, 'tests', 'test-task446.js'), [
    # харнесс dataHost: + _ppePosNoGrade
    ("""            methodText(INDEX_SRC, '_workersArchiveData') + ',\\n' +
            "_isInstrType: function(t) { return t === 'инструктаж' || t === 'проверка_знаний'; }," +
""",
     """            methodText(INDEX_SRC, '_workersArchiveData') + ',\\n' +
            methodText(INDEX_SRC, '_ppePosNoGrade') + ',\\n' +
            "_isInstrType: function(t) { return t === 'инструктаж' || t === 'проверка_знаний'; }," +
""", 'dataHost: + _ppePosNoGrade'),
    # харнесс wbHost: + _ppePosNoGrade (после _buildArchiveWorkbook)
    ("""            methodText(INDEX_SRC, '_workersArchiveData') + ',\\n' +
            methodText(INDEX_SRC, '_buildArchiveWorkbook') + ',\\n' +
""",
     """            methodText(INDEX_SRC, '_workersArchiveData') + ',\\n' +
            methodText(INDEX_SRC, '_buildArchiveWorkbook') + ',\\n' +
            methodText(INDEX_SRC, '_ppePosNoGrade') + ',\\n' +
""", 'wbHost: + _ppePosNoGrade'),
    # название теста + подписи: СИЗ теперь по фамилиям (Task 459)
    ("""    test('отпуска/СИЗ/мероприятия: сортировки прежние, данные на местах', () => {""",
     """    test('отпуска/СИЗ/мероприятия: сортировки на местах (СИЗ — Task 459 по фамилиям)', () => {""",
     'название теста'),
    ("""        // СИЗ: сортировка по таб. № (017 → 031) — прежняя
        assertEqual(d.ppe[1][0], 'Иванов И. И.', 'СИЗ: первый — таб 017');
        assertEqual(d.ppe[1][4], '01.06.' + (NOWY - 1), 'СИЗ: изготовление [4]');
        assertEqual(d.ppe[2][0], 'Сидоров С. С.', 'СИЗ: второй — таб 031 (фолбэк ФИО)');""",
     """        // СИЗ: сортировка по ФАМИЛИЯМ (Task 459): Иванов → Сидоров
        assertEqual(d.ppe[1][0], 'Иванов И. И.',
            'СИЗ: первый — Иванов (по фамилии, Task 459)');
        assertEqual(d.ppe[1][4], '01.06.' + (NOWY - 1), 'СИЗ: изготовление [4]');
        assertEqual(d.ppe[2][0], 'Сидоров С. С.',
            'СИЗ: второй — Сидоров (фолбэк ФИО)');""", 'СИЗ: подписи по фамилиям'),
    # комментарий зебры листа 4 (zip-тест)
    ("""        // сортировка по таб.: 017 Иванов (строка 2) → 031 Сидоров (строка 3)""",
     """        // Task 459: сортировка по фамилиям — Иванов (строка 2) → Сидоров (строка 3)""",
     'zip-тест: комментарий'),
])

print('OK: адаптация 445/446 завершена')
