#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 384: адаптация старых тестов под новую функциональность
# карточки сотрудника (правка данных/отпусков/мероприятий).
#   1) заголовки шторок получили id (wsVacSheetTitle) — ассерты
#      «flow-input-sheet-title">Новый отпуск<» уточнены (test-work-
#      schedule ×2);
#   2) openVacationForm — сигнатура (tabNo, editVacation): Task 384
#      режим правки (test-work-schedule, test-task312);
#   3) submitEmployeeForm — окно блока 2200 → 4200 (ветка правки
#      Task 384 вставлена ДО addEmployee, loadGrid уехал дальше);
#   4) test-task314: loadGrid(true) 13 → 15 (две новые мутации —
#      updateEmployee/updateVacation в режимах правки).

REPLS = {
    'tests/test-work-schedule.js': [
        (
            'заголовок шторки отпуска (274)',
            '''            assertTrue(html.indexOf('flow-input-sheet-title">Новый отпуск<') !== -1,
                'заголовок формы');
            assertTrue((html.match(/<option value="[123]">[123] — /g) || []).length === 3,
                'части 1–3 в селекте');
        });

        test('HTML: подсказка про деление на части и ст. 125 ТК РФ', () => {''',
            '''            // Task 384: у заголовка появился id (режим «Правка отпуска»)
            assertTrue(html.indexOf('flow-input-sheet-title" id="wsVacSheetTitle">Новый отпуск<') !== -1,
                'заголовок формы (id wsVacSheetTitle — Task 384)');
            assertTrue((html.match(/<option value="[123]">[123] — /g) || []).length === 3,
                'части 1–3 в селекте');
        });

        test('HTML: подсказка про деление на части и ст. 125 ТК РФ', () => {''',
            1,
        ),
        (
            'submitEmployeeForm окно',
            '''        const block = html.slice(i, i + 2200);
        // Task 314: loadGrid(true) — свежие данные с сервера
        assertTrue(block.indexOf('self.loadGrid(true);') !== -1,
            'после добавления — loadGrid(true) (новая строка сотрудника в сетке)');''',
            '''        // Task 384: окно расширено — ветка правки updateEmployee
        // вставлена ДО addEmployee, loadGrid(true) уехал дальше
        const block = html.slice(i, i + 4200);
        // Task 314: loadGrid(true) — свежие данные с сервера
        assertTrue(block.indexOf('self.loadGrid(true);') !== -1,
            'после добавления — loadGrid(true) (новая строка сотрудника в сетке)');''',
            1,
        ),
        (
            'openVacationForm сигнатура (312-видимость)',
            '''        const openFn = html.slice(html.indexOf('openVacationForm: function'),
                                  html.indexOf('closeVacationForm: function'));
        assertTrue(openFn.indexOf('openVacationForm: function(tabNo)') !== -1 &&
                   openFn.indexOf('empSel.value = String(tabNo);') !== -1,
            'openVacationForm(tabNo) выбирает сотрудника в списке');''',
            '''        const openFn = html.slice(html.indexOf('openVacationForm: function'),
                                  html.indexOf('closeVacationForm: function'));
        // Task 384: 2-й аргумент editVacation — режим правки периода
        assertTrue(openFn.indexOf('openVacationForm: function(tabNo, editVacation)') !== -1 &&
                   openFn.indexOf('empSel.value = String(tabNo);') !== -1,
            'openVacationForm(tabNo, editVacation) выбирает сотрудника в списке');''',
            1,
        ),
        (
            'заголовок шторки отпуска (308)',
            '''        assertTrue(html.indexOf('flow-input-sheet-title">Новый отпуск<') !== -1,
            'заголовок формы');
        assertTrue((html.match(/<option value="[123]">[123] — /g) || []).length === 3,
            'части 1–3 в селекте');
    });

    test('CSS: Task 312 — .ws-addvac-btn удалён (стиль мёртв)', () => {''',
            '''        // Task 384: у заголовка появился id (режим «Правка отпуска»)
        assertTrue(html.indexOf('flow-input-sheet-title" id="wsVacSheetTitle">Новый отпуск<') !== -1,
            'заголовок формы (id wsVacSheetTitle — Task 384)');
        assertTrue((html.match(/<option value="[123]">[123] — /g) || []).length === 3,
            'части 1–3 в селекте');
    });

    test('CSS: Task 312 — .ws-addvac-btn удалён (стиль мёртв)', () => {''',
            1,
        ),
    ],
    'tests/test-task312.js': [
        (
            'openVacationForm сигнатура',
            '''        const fn = fnBody(INDEX_SRC, 'openVacationForm: function');
        assertTrue(INDEX_SRC.indexOf('openVacationForm: function(tabNo)') !== -1,
            'сигнатура принимает необязательный таб. №');''',
            '''        const fn = fnBody(INDEX_SRC, 'openVacationForm: function');
        // Task 384: 2-й аргумент editVacation — режим правки периода
        assertTrue(INDEX_SRC.indexOf('openVacationForm: function(tabNo, editVacation)') !== -1,
            'сигнатура принимает необязательный таб. № (и запись правки — Task 384)');''',
            1,
        ),
    ],
    'tests/test-task314.js': [
        (
            'счётчик loadGrid(true)',
            '''        // saveAll, генерация ×3, сотрудник, мероприятие ×5, отпуск ×2,
        // увольнение (Task 318) — правки обязаны перечитывать сервер,
        // кэш не подменяет свежее
        const n = (INDEX_SRC.match(/self\\.loadGrid\\(true\\);/g) || []).length;
        assertEqual(n, 13, '12 мутаций + 1 в refreshData = 13 вызовов loadGrid(true)');''',
            '''        // saveAll, генерация ×3, сотрудник, мероприятие ×5, отпуск ×2,
        // увольнение (Task 318) — правки обязаны перечитывать сервер,
        // кэш не подменяет свежее
        // Task 384: +2 — правка данных сотрудника (updateEmployee) и
        // правка периода отпуска (updateVacation) из карточки
        const n = (INDEX_SRC.match(/self\\.loadGrid\\(true\\);/g) || []).length;
        assertEqual(n, 15, '14 мутаций + 1 в refreshData = 15 вызовов loadGrid(true)');''',
            1,
        ),
    ],
}

for path, repls in REPLS.items():
    s = open(path, encoding='utf-8').read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, '%s: [%s] найдено %d (ожидалось %d)' % (path, name, found, cnt)
        s = s.replace(old, new)
    open(path, 'w', encoding='utf-8').write(s)
    print('%s: адаптировано правок: %d' % (path, len(repls)))
print('Task 384: адаптация тестов завершена')
