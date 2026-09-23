#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 402: адаптация тестов к новой структуре.
#   1) tests/test-work-schedule.js — сетка перешла с _posLabel
#      (должность+тип одной строкой; формат остался ТОЛЬКО в печатной
#      форме) на _empPosLine (должность·группа) + _empTipLine (тип —
#      ТРЕТЬЯ строка ячейки): 3 ассерта со старой жёсткой привязкой
#      «var empPosLabel = this._posLabel(emp);» в РЕНДЕРЕ СЕТКИ.
#   2) tests/test-task384.js — клиентский VM-хост шторки: + методы
#      _fillGroupSelect/_fillGroupOptions (openEmployeeForm/
#      openEmpEditForm теперь их зовут); серверный VM-хост:
#      + метод _accessGroupColIndex (updateEmployee ищет столбец
#      «группа_допуска» по заголовку; мок-лист без getLastColumn —
#      try/catch хелпера возвращает null, записи группы нет).
#   3) tests/test-task396.js — карточка: профиль стал 4 полями
#      (Task 402: + «Группа допуска» после «Должности»); зебра
#      профиля — 2 alt-строки; мок работника 2706 получает группу IV.
# Скрипт идемпотентен: правка, чей якорь уже применён, пропускается.
import sys

def apply_file(path, repls):
    src = open(path, encoding='utf-8').read()
    n = 0
    for i, (old, new, what) in enumerate(repls, 1):
        if old in src:
            if src.count(old) != 1:
                print('FAIL [%s #%d]: якорь не уникален — %s'
                      % (path, i, what))
                sys.exit(1)
            src = src.replace(old, new)
            n += 1
            print('  [%s #%d] OK — %s' % (path, i, what))
        elif new in src:
            print('  [%s #%d] уже применена — %s' % (path, i, what))
        else:
            print('FAIL [%s #%d]: якорь не найден — %s' % (path, i, what))
            sys.exit(1)
    open(path, 'w', encoding='utf-8').write(src)
    return n

# ============================================================
# 1. tests/test-work-schedule.js
# ============================================================
WS_REPLS = [

(
"""        test('JS: колонка сотрудника — ws-emp-pos с подписью _posLabel', () => {
            assertTrue(html.indexOf("var empPosLabel = this._posLabel(emp);") !== -1 &&
                       html.indexOf("'<div class=\\"ws-emp-pos\\">' + this._esc(empPosLabel) + '</div>'") !== -1,
                'Подпись в .ws-emp-pos формируется через _posLabel (должность + режим)');
""",
"""        test('JS: колонка сотрудника — ws-emp-pos с подписью _empPosLine (Task 402)', () => {
            assertTrue(html.indexOf("var empPosLabel = this._empPosLine(emp);") !== -1 &&
                       html.indexOf("'<div class=\\"ws-emp-pos\\">' + this._esc(empPosLabel) + '</div>'") !== -1,
                'Подпись в .ws-emp-pos формируется через _empPosLine (должность + группа)');
""",
'ассерт рендера: _empPosLine (должность + группа)'),
]

# ============================================================
# 2. tests/test-task384.js
# ============================================================
T384_REPLS = [

(
"""        'openEmployeeForm', 'closeEmployeeForm', 'openEmpEditForm',
        'submitEmployeeForm', 'onEmpTypeChange',
        '_fillPositionSelect', '_fillPositionOptions',
""",
"""        'openEmployeeForm', 'closeEmployeeForm', 'openEmpEditForm',
        'submitEmployeeForm', 'onEmpTypeChange',
        '_fillPositionSelect', '_fillPositionOptions',
        '_fillGroupSelect', '_fillGroupOptions',
""",
'VM-хост клиента: + _fillGroupSelect/_fillGroupOptions (Task 402)'),

(
"""    const methods = ['_parseIsoDate', '_parseSheetDate', '_safeDate', '_toIsoDate',
                     'updateEmployee', 'updateVacation'];
""",
"""    const methods = ['_parseIsoDate', '_parseSheetDate', '_safeDate', '_toIsoDate',
                     '_accessGroupColIndex',
                     'updateEmployee', 'updateVacation'];
""",
'VM-хост сервера: + _accessGroupColIndex (Task 402)'),
]

# ============================================================
# 3. tests/test-task396.js
# ============================================================
T396_REPLS = [

(
"""    const EMP = [
        { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
          'смена': '', 'должность': 'Мастер КИПиА', 'комментарий': '',
          'дата_приёма': '2024-03-15' },
""",
"""    const EMP = [
        { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
          'смена': '', 'должность': 'Мастер КИПиА', 'комментарий': '',
          'группа_допуска': 'IV', 'дата_приёма': '2024-03-15' },
""",
'мок работника 2706 (cardHost): + группа_допуска IV (Task 402)'),

(
"""    const EMPLOYEES = [
        { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
          'смена': '', 'должность': 'Мастер КИПиА', 'комментарий': '',
          'дата_приёма': '2024-03-15' },
""",
"""    const EMPLOYEES = [
        { 'таб_номер': '2706', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной',
          'смена': '', 'должность': 'Мастер КИПиА', 'комментарий': '',
          'группа_допуска': 'IV', 'дата_приёма': '2024-03-15' },
""",
'мок работника 2706 (pageHost): + группа_допуска IV (Task 402)'),

(
"""        // b1: 3 поля (Режим/Должность/Дата приёма; Комментарий пуст — скрыт)
        assertEqual((blocks[0].match(/class="ws-emp-field/g) || []).length, 3,
            'поля профиля: 3 строки');
        assertEqual((blocks[0].match(/ws-emp-field ws-row-alt/g) || []).length, 1,
            'вторая строка (Должность) — с чередующимся фоном');
        assertTrue(blocks[0].indexOf('"ws-emp-k">Режим работы') !== -1 &&
                   blocks[0].indexOf('ws-emp-field ws-row-alt"><span class="ws-emp-k">Должность') !== -1,
            'именно ВТОРАЯ строка — Должность');
""",
"""        // b1: 4 поля (Режим/Должность/Группа допуска/Дата приёма —
        // Task 402 добавил «Группу допуска» после «Должности»;
        // Комментарий пуст — скрыт)
        assertEqual((blocks[0].match(/class="ws-emp-field/g) || []).length, 4,
            'поля профиля: 4 строки (Task 402: + Группа допуска)');
        assertEqual((blocks[0].match(/ws-emp-field ws-row-alt/g) || []).length, 2,
            'чередование: Должность (2-я) и Дата приёма (4-я) — alt');
        assertTrue(blocks[0].indexOf('"ws-emp-k">Режим работы') !== -1 &&
                   blocks[0].indexOf('ws-emp-field ws-row-alt"><span class="ws-emp-k">Должность') !== -1,
            'именно ВТОРАЯ строка — Должность');
        assertTrue(blocks[0].indexOf('"ws-emp-k">Группа допуска') !== -1 &&
                   blocks[0].indexOf('ws-emp-v">IV') !== -1,
            'Task 402: строка «Группа допуска» со значением IV');
        assertTrue(blocks[0].indexOf('"ws-emp-k">Должность') <
                   blocks[0].indexOf('"ws-emp-k">Группа допуска') &&
                   blocks[0].indexOf('"ws-emp-k">Группа допуска') <
                   blocks[0].indexOf('"ws-emp-k">Дата приёма'),
            'Task 402: Группа допуска — ПОСЛЕ Должности (до Даты приёма)');
""",
'зебра профиля: 4 поля, 2 alt, Группа допуска после Должности'),
]

n = 0
n += apply_file('tests/test-work-schedule.js', WS_REPLS)
n += apply_file('tests/test-task384.js', T384_REPLS)
n += apply_file('tests/test-task396.js', T396_REPLS)
print('OK: адаптация завершена (применено правок: %d)' % n)
