#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 489 — адаптация существующих тестов под новую структуру
«Сотрудники» (ФИО → фамилия/имя/отчество + дата_рождения).

Правки:
1. test-task403.js — в mkHost (listEmployees/updateEmployee/addEmployee)
   добавляются _employeesColMap + _wsShortFio/_wsNameInitial/_wsFullFio.
2. test-task384.js — серверные методы + клиентские поля формы
   (wsEmpFio → wsEmpFam/wsEmpName/wsEmpPatr/wsEmpBirth) + payload.
3. test-task392.js / test-task443.js — серверные методы (PPE-хосты
   читают лист «Сотрудники» через _ppeLookupEmployee → _employeesColMap).
4. test-work-schedule.js — список id полей формы.
"""
import io
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def patch(path, replacements, marker='Task 489'):
    p = ROOT / path
    src = io.open(p, encoding='utf-8').read()
    if marker + '-adapt' in src:
        print('  [skip] %s (уже адаптирован)' % path)
        return
    n = 0
    for old, new in replacements:
        if old not in src:
            print('  [ MISS ] %s: не найдено: %r' % (path, old[:70]))
            continue
        src = src.replace(old, new, 1)
        n += 1
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  [ ok ] %s: %d/%d замен' % (path, n, len(replacements)))


SRV_METHODS = ("'_employeesColMap', '_wsShortFio', '_wsNameInitial', "
               "'_wsFullFio',\n                     ")
SRV_METHODS_392 = ("'_employeesColMap', '_wsShortFio', '_wsNameInitial', "
                    "'_wsFullFio',\n                     ")

# 1) test-task403.js — три mkHost: вставка после _headerColIndex
patch('tests/test-task403.js', [
    (
        "            methodText(WS_GS_SRC, 'listEmployees') + ',' +\n"
        "            methodText(WS_GS_SRC, '_accessGroupColIndex') + ',' +\n"
        "            methodText(WS_GS_SRC, '_headerColIndex') + ',' +",
        "            methodText(WS_GS_SRC, 'listEmployees') + ',' +\n"
        "            methodText(WS_GS_SRC, '_accessGroupColIndex') + ',' +\n"
        "            methodText(WS_GS_SRC, '_headerColIndex') + ',' +\n"
        "            // Task 489-adapt: карта столбцов + композиция ФИО\n"
        "            methodText(WS_GS_SRC, '_employeesColMap') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsShortFio') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsNameInitial') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsFullFio') + ',' +"
    ),
    (
        "            methodText(WS_GS_SRC, 'updateEmployee') + ',' +\n"
        "            methodText(WS_GS_SRC, '_accessGroupColIndex') + ',' +\n"
        "            methodText(WS_GS_SRC, '_headerColIndex') + ',' +",
        "            methodText(WS_GS_SRC, 'updateEmployee') + ',' +\n"
        "            methodText(WS_GS_SRC, '_accessGroupColIndex') + ',' +\n"
        "            methodText(WS_GS_SRC, '_headerColIndex') + ',' +\n"
        "            // Task 489-adapt: карта столбцов + композиция ФИО\n"
        "            methodText(WS_GS_SRC, '_employeesColMap') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsShortFio') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsNameInitial') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsFullFio') + ',' +"
    ),
    (
        "            methodText(WS_GS_SRC, 'addEmployee') + ',' +\n"
        "            methodText(WS_GS_SRC, '_accessGroupColIndex') + ',' +\n"
        "            methodText(WS_GS_SRC, '_headerColIndex') + ',' +",
        "            methodText(WS_GS_SRC, 'addEmployee') + ',' +\n"
        "            methodText(WS_GS_SRC, '_accessGroupColIndex') + ',' +\n"
        "            methodText(WS_GS_SRC, '_headerColIndex') + ',' +\n"
        "            // Task 489-adapt: карта столбцов + композиция ФИО\n"
        "            methodText(WS_GS_SRC, '_employeesColMap') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsShortFio') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsNameInitial') + ',' +\n"
        "            methodText(WS_GS_SRC, '_wsFullFio') + ',' +"
    ),
])

# 2) test-task384.js
patch('tests/test-task384.js', [
    # серверные методы
    (
        "    const methods = ['_parseIsoDate', '_parseSheetDate', "
        "'_safeDate', '_toIsoDate',\n"
        "                     '_accessGroupColIndex', '_headerColIndex',\n"
        "                     'updateEmployee', 'updateVacation'];",
        "    const methods = ['_parseIsoDate', '_parseSheetDate', "
        "'_safeDate', '_toIsoDate',\n"
        "                     '_accessGroupColIndex', '_headerColIndex',\n"
        "                     '_employeesColMap', '_wsShortFio', "
        "'_wsNameInitial', '_wsFullFio',\n"
        "                     'updateEmployee', 'updateVacation'];"
    ),
    # клиентские методы (нужен _wsShortFio для submitEmployeeForm)
    (
        "        '_esc', '_escAttr', '_apiErrText', '_isoDate', "
        "'_fmtDateRu',\n"
        "        '_parseIsoLocal', '_vacIsHoliday', '_vacSplitDays',",
        "        '_esc', '_escAttr', '_apiErrText', '_isoDate', "
        "'_fmtDateRu',\n"
        "        // Task 489-adapt: композиция краткого ФИО из частей\n"
        "        '_wsShortFio', '_wsNameInitial', '_wsFullFio',\n"
        "        '_parseIsoLocal', '_vacIsHoliday', '_vacSplitDays',"
    ),
    # префилл: три поля вместо одного
    (
        "        assertEqual(els.wsEmpFio.value, 'Иванов И. И.', 'ФИО');",
        "        // Task 489-adapt: ТРИ поля имени (легаси-запись без "
        "частей —\n"
        "        // раскладка краткого ФИО по словам)\n"
        "        assertEqual(els.wsEmpFam.value, 'Иванов', 'фамилия');\n"
        "        assertEqual(els.wsEmpName.value, 'И.', 'имя (инициал)');\n"
        "        assertEqual(els.wsEmpPatr.value, 'И.', "
        "'отчество (инициал)');\n"
        "        assertEqual(els.wsEmpBirth.value, '', "
        "'дата рождения (нет в записи)');"
    ),
    # submit: установка полей
    (
        "        els.wsEmpFio.value = 'Иванов И. И. (ст.)';",
        "        els.wsEmpFam.value = 'Иванов';\n"
        "        els.wsEmpName.value = 'Иван';\n"
        "        els.wsEmpPatr.value = 'Иванович';"
    ),
    # submit: payload-проверки
    (
        "        assertEqual(upd[0].payload['ФИО'], "
        "'Иванов И. И. (ст.)', 'новое ФИО');",
        "        assertEqual(upd[0].payload['ФИО'], 'Иванов И. И.',\n"
        "            'ФИО (краткая композиция — легаси-поле, Task 489)');\n"
        "        assertEqual(upd[0].payload['фамилия'], 'Иванов',\n"
        "            'фамилия (Task 489)');\n"
        "        assertEqual(upd[0].payload['имя'], 'Иван',\n"
        "            'имя (Task 489)');\n"
        "        assertEqual(upd[0].payload['отчество'], 'Иванович',\n"
        "            'отчество (Task 489)');\n"
        "        assertEqual(upd[0].payload['дата_рождения'], null,\n"
        "            'дата рождения (пусто → null, Task 489)');"
    ),
])

# 3) test-task392.js — серверный PPE-хост
patch('tests/test-task392.js', [
    (
        "    const methods = ['_parseIsoDate', '_parseSheetDate', "
        "'_safeDate', '_toIsoDate',\n"
        "                     '_appendRowKeepText', 'listPpe', 'addPpe', "
        "'updatePpe',\n"
        "                     'deletePpe', '_ppeLookupEmployee', "
        "'_ppeTermMonths',\n"
        "                     '_ppeExpiry', '_ppeHasManufactureCol'];",
        "    const methods = ['_parseIsoDate', '_parseSheetDate', "
        "'_safeDate', '_toIsoDate',\n"
        "                     '_appendRowKeepText', 'listPpe', 'addPpe', "
        "'updatePpe',\n"
        "                     'deletePpe', '_ppeLookupEmployee', "
        "'_ppeTermMonths',\n"
        "                     '_ppeExpiry', '_ppeHasManufactureCol',\n"
        "                     // Task 489-adapt: _ppeLookupEmployee идёт "
        "через карту\n"
        "                     '_employeesColMap', '_wsShortFio', "
        "'_wsNameInitial', '_wsFullFio'];"
    ),
])

# 4) test-task443.js — серверный PPE-хост
patch('tests/test-task443.js', [
    (
        "    const methods = ['_parseIsoDate', '_parseSheetDate', "
        "'_safeDate', '_toIsoDate',\n"
        "                     '_appendRowKeepText', 'listPpe', 'addPpe', "
        "'updatePpe',\n"
        "                     'deletePpe', '_ppeLookupEmployee', "
        "'_ppeTermMonths',\n"
        "                     '_ppeExpiry', '_ppeHasManufactureCol'];",
        "    const methods = ['_parseIsoDate', '_parseSheetDate', "
        "'_safeDate', '_toIsoDate',\n"
        "                     '_appendRowKeepText', 'listPpe', 'addPpe', "
        "'updatePpe',\n"
        "                     'deletePpe', '_ppeLookupEmployee', "
        "'_ppeTermMonths',\n"
        "                     '_ppeExpiry', '_ppeHasManufactureCol',\n"
        "                     // Task 489-adapt: _ppeLookupEmployee идёт "
        "через карту\n"
        "                     '_employeesColMap', '_wsShortFio', "
        "'_wsNameInitial', '_wsFullFio'];"
    ),
])

# 5) test-work-schedule.js — список id полей формы
patch('tests/test-work-schedule.js', [
    (
        "        ['wsEmpOverlay', 'wsEmpSheet', 'wsEmpTabNo', "
        "'wsEmpFio', 'wsEmpType',",
        "        // Task 489-adapt: wsEmpFio → wsEmpFam/wsEmpName/"
        "wsEmpPatr (+wsEmpBirth)\n"
        "        ['wsEmpOverlay', 'wsEmpSheet', 'wsEmpTabNo', "
        "'wsEmpFam', 'wsEmpName', 'wsEmpPatr', 'wsEmpBirth', "
        "'wsEmpType',",
    ),
])

print('Готово.')

# ============================================================
# Часть 2: окна + SRC-литералы карты столбцов (после прогона)
# ============================================================
patch('tests/test-task340.js', [
    (
        "// Task 465: окно 500000 → 560000 — блок печати списка "
        "мероприятий\n"
        "// (~36 КБ) сдвинул _renderEmpPopup/_renderWorkerCard за "
        "старую\n"
        "// границу; негативные ассерты (методы УДАЛЕНЫ) безопасны — "
        "их нет\n"
        "// во всём файле\n"
        "const WS_CLIENT = INDEX_SRC.slice(WS_START, WS_START "
        "+ 560000);",
        "// Task 465: окно 500000 → 560000 — блок печати списка "
        "мероприятий\n"
        "// (~36 КБ) сдвинул _renderEmpPopup/_renderWorkerCard за "
        "старую\n"
        "// границу; негативные ассерты (методы УДАЛЕНЫ) безопасны — "
        "их нет\n"
        "// во всём файле\n"
        "// Task 489-adapt: окно 560000 → 600000 — хелперы имени "
        "(~1,6 КБ\n"
        "// перед карточкой) сдвинули хвост _renderWorkerCard "
        "(~36 КБ);\n"
        "// карточка теперь ЦЕЛИКОМ в окне (конец ~586,6 КБ)\n"
        "const WS_CLIENT = INDEX_SRC.slice(WS_START, WS_START "
        "+ 600000);"
    ),
])

patch('tests/test-task384.js', [
    (
        "        assertTrue(fn.indexOf('sheet.getRange(row, posCol + 1).setValue(position);') !== -1 &&\n"
        "                   fn.indexOf('sheet.getRange(row, comCol + 1).setValue(comment);') !== -1,\n"
        "            'должность/комментарий — отдельные setValue по заголовкам');",
        "        // Task 489-adapt: столбцы — из карты _employeesColMap\n"
        "        assertTrue(fn.indexOf(\"sheet.getRange(row, cols['должность'] + 1).setValue(position);\") !== -1 &&\n"
        "                   fn.indexOf(\"sheet.getRange(row, cols['комментарий'] + 1).setValue(comment);\") !== -1,\n"
        "            'должность/комментарий — отдельные setValue по заголовкам (карта)');"
    ),
])

patch('tests/test-task402.js', [
    (
        "        const fn = stripComments(methodText(WS_GS_SRC, 'listEmployees'));\n"
        "        assertTrue(fn.indexOf('var groupCol = this._accessGroupColIndex(sheet);') !== -1,\n"
        "            'столбец ищется по заголовку');",
        "        const fn = stripComments(methodText(WS_GS_SRC, 'listEmployees'));\n"
        "        // Task 489-adapt: группа/должность/комментарий — в карте\n"
        "        // _employeesColMap (по заголовкам строки 1)\n"
        "        assertTrue(fn.indexOf('var cols = this._employeesColMap(sheet);') !== -1,\n"
        "            'столбцы ищутся по заголовкам (карта, Task 489)');"
    ),
    (
        "        assertTrue(fn.indexOf('var readWidth = 11;') !== -1 &&\n"
        "                   fn.indexOf('groupCol + 1 > readWidth') !== -1,\n"
        "            'чтение расширено до самого правого найденного столбца');\n"
        "        assertTrue(fn.indexOf('группа_допуска:') !== -1 &&\n"
        "                   fn.indexOf('(groupCol !== null)') !== -1,\n"
        "            'поле в ответе; нет столбца — пустая строка');",
        "        assertTrue(fn.indexOf('cols.width') !== -1 &&\n"
        "                   fn.indexOf('r[cols[') !== -1,\n"
        "            'чтение до самого правого столбца карты');\n"
        "        assertTrue(fn.indexOf('группа_допуска:') !== -1 &&\n"
        "                   fn.indexOf(\"(cols['группа_допуска'] !== null)\") !== -1,\n"
        "            'поле в ответе; нет столбца — пустая строка');"
    ),
    (
        "        assertTrue(fn.indexOf('sheet.getRange(row, groupCol + 1).setValue(accessGroup);') !== -1,\n"
        "            'запись в столбец по заголовку');",
        "        assertTrue(fn.indexOf(\"sheet.getRange(row, cols['группа_допуска'] + 1).setValue(accessGroup);\") !== -1,\n"
        "            'запись в столбец по заголовку (карта, Task 489-adapt)');"
    ),
    (
        "        assertTrue(fn.indexOf('rowVals[posCol] = position;') !== -1 &&\n"
        "                   fn.indexOf('rowVals[comCol] = comment;') !== -1,\n"
        "            'должность и комментарий — каждый в свой столбец');\n"
        "        assertTrue(fn.indexOf('rowVals[groupCol] = accessGroup;') !== -1,\n"
        "            'группа записана в найденный столбец');",
        "        assertTrue(fn.indexOf(\"rowVals[cols['должность']] = position;\") !== -1 &&\n"
        "                   fn.indexOf(\"rowVals[cols['комментарий']] = comment;\") !== -1,\n"
        "            'должность и комментарий — каждый в свой столбец (карта)');\n"
        "        assertTrue(fn.indexOf(\"rowVals[cols['группа_допуска']] = accessGroup;\") !== -1,\n"
        "            'группа записана в найденный столбец (карта)');"
    ),
])

print('Часть 2 готова.')
