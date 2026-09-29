#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 443 — адаптация tests/test-task392.js под новую структуру
# листа «СИЗ» (G «дата_изготовления», H срок, I окончание, J
# примечание) и приоритет даты изготовления в _ppeExpiry/base.
# Семантика Task 392 сохранена: записи без даты изготовления
# считаются от даты выдачи, как и раньше.
import io

P = 'tests/test-task392.js'
s = io.open(P, encoding='utf-8').read()
n0 = s

def rep(old, new, tag):
    global s
    assert old in s, 'НЕ НАЙДЕНО (%s): %r' % (tag, old[:100])
    assert s.count(old) == 1, 'НЕ УНИКАЛЬНО (%s): %d вхождений' % (tag, s.count(old))
    s = s.replace(old, new)
    print('OK  %s' % tag)

# --- 1. SRC: _ppeExpiry — baseDate (Task 443 переименовал параметр) -----
rep(
"""    test('WorkSchedule.gs: дата окончания АВТО (выдача + срок, кламп дня)', () => {
        const fn = methodText(WS_GS_SRC, '_ppeExpiry');
        assertTrue(fn.indexOf("_ppeTermMonths(term)") !== -1, 'срок → месяцы');
        assertTrue(fn.indexOf("issueDate.getMonth() + months") !== -1,
            'месяцы прибавляются к дате выдачи');
        assertTrue(fn.indexOf("new Date(y, mo + 1, 0).getDate()") !== -1,
            'кламп дня к длине целевого месяца');
        assertTrue(fn.indexOf("return 'До износа';") !== -1, '«До износа» — строкой');
        const add = stripComments(methodText(WS_GS_SRC, 'addPpe'));
        assertTrue(add.indexOf('this._ppeExpiry(issued, term)') !== -1,
            'addPpe считает дату окончания автоматически');
        const upd = stripComments(methodText(WS_GS_SRC, 'updatePpe'));
        assertTrue(upd.indexOf('this._ppeExpiry(issued, term)') !== -1,
            'updatePpe пересчитывает дату окончания');
    });""",
"""    test('WorkSchedule.gs: дата окончания АВТО (базовая дата + срок, кламп дня; Task 443 — приоритет изготовления)', () => {
        const fn = methodText(WS_GS_SRC, '_ppeExpiry');
        assertTrue(fn.indexOf("_ppeTermMonths(term)") !== -1, 'срок → месяцы');
        assertTrue(fn.indexOf("baseDate.getMonth() + months") !== -1,
            'месяцы прибавляются к базовой дате (Task 443: изготовление в приоритете, иначе выдача)');
        assertTrue(fn.indexOf("new Date(y, mo + 1, 0).getDate()") !== -1,
            'кламп дня к длине целевого месяца');
        assertTrue(fn.indexOf("return 'До износа';") !== -1, '«До износа» — строкой');
        const add = stripComments(methodText(WS_GS_SRC, 'addPpe'));
        assertTrue(add.indexOf('var base = manufactured || issued;') !== -1 &&
                   add.indexOf('this._ppeExpiry(base, term)') !== -1,
            'addPpe считает дату окончания автоматически (база — изготовление/выдача)');
        const upd = stripComments(methodText(WS_GS_SRC, 'updatePpe'));
        assertTrue(upd.indexOf('var base = manufactured || issued;') !== -1 &&
                   upd.indexOf('this._ppeExpiry(base, term)') !== -1,
            'updatePpe пересчитывает дату окончания (база — изготовление/выдача)');
    });""",
'1. SRC _ppeExpiry/addPpe/updatePpe — base')

# --- 2. VM listPpe: фикстура 10 столбцов + ассерты даты изготовления ----
rep(
"""    function ppeSheet() {
        return [
            ['id', 'таб_номер', 'работник', 'должность', 'наименование_СИЗ',
             'дата_выдачи', 'срок_годности', 'дата_окончания', 'примечание'],
            [1, '2706', 'Галкин Д. Н.', 'Мастер КИПиА',
             'Костюм для защиты от растворов кислот и щелочей',
             new Date(2026, 7, 17), '1 год', new Date(2027, 7, 17), ''],
            [2, '2706', 'Галкин Д. Н.', 'Мастер КИПиА', 'Очки закрытые',
             '', 'До износа', 'До износа', ''],
            [3, '0377', 'Первов С. А.', 'Слесарь КИПиА', 'Ботинки',
             '2026-08-17', '1,5 года', '2028-02-17', ''],
            ['', '', '', '', '', '', '', '', ''],  // пустой стилевой хвост
        ];
    }

    test('чтение: ISO-даты, текстовые даты, «До износа» строкой, пропуск пустых', () => {
        const api = makePpeServer();
        api.setSheet('СИЗ', ppeSheet());
        const res = api.WSS.listPpe({ token: 't' });
        assertEqual(res.ok, true, 'успех');
        const ppe = res.data.ppe;
        assertEqual(ppe.length, 3, '3 записи (пустая строка пропущена)');
        assertEqual(ppe[0].дата_выдачи, '2026-08-17', 'Date → ISO');
        assertEqual(ppe[0].дата_окончания, '2027-08-17', 'окончание Date → ISO');
        assertEqual(ppe[1].дата_окончания, 'До износа', '«До износа» строкой');
        assertEqual(ppe[2].дата_выдачи, '2026-08-17', 'текстовая дата распарсена');
        assertEqual(ppe[2].дата_окончания, '2028-02-17', 'текстовое окончание');
        assertEqual(ppe[0].наименование, 'Костюм для защиты от растворов кислот и щелочей',
            'наименование');
    });""",
"""    function ppeSheet() {
        // Task 443: столбец G «дата_изготовления» (10 столбцов)
        return [
            ['id', 'таб_номер', 'работник', 'должность', 'наименование_СИЗ',
             'дата_выдачи', 'дата_изготовления', 'срок_годности',
             'дата_окончания', 'примечание'],
            [1, '2706', 'Галкин Д. Н.', 'Мастер КИПиА',
             'Костюм для защиты от растворов кислот и щелочей',
             new Date(2026, 7, 17), '', '1 год', new Date(2027, 7, 17), ''],
            [2, '2706', 'Галкин Д. Н.', 'Мастер КИПиА', 'Очки закрытые',
             '', '', 'До износа', 'До износа', ''],
            [3, '0377', 'Первов С. А.', 'Слесарь КИПиА', 'Ботинки',
             '2026-08-17', '2025-02-15', '1,5 года', '2028-02-17', ''],
            ['', '', '', '', '', '', '', '', '', ''],  // пустой стилевой хвост
        ];
    }

    test('чтение: ISO-даты, текстовые даты, «До износа» строкой, пропуск пустых', () => {
        const api = makePpeServer();
        api.setSheet('СИЗ', ppeSheet());
        const res = api.WSS.listPpe({ token: 't' });
        assertEqual(res.ok, true, 'успех');
        const ppe = res.data.ppe;
        assertEqual(ppe.length, 3, '3 записи (пустая строка пропущена)');
        assertEqual(ppe[0].дата_выдачи, '2026-08-17', 'Date → ISO');
        assertEqual(ppe[0].дата_окончания, '2027-08-17', 'окончание Date → ISO');
        assertEqual(ppe[1].дата_окончания, 'До износа', '«До износа» строкой');
        assertEqual(ppe[2].дата_выдачи, '2026-08-17', 'текстовая дата распарсена');
        assertEqual(ppe[2].дата_окончания, '2028-02-17', 'текстовое окончание');
        // Task 443: дата изготовления читается (текстовая — парсится,
        // пустая — пустая строка)
        assertEqual(ppe[2].дата_изготовления, '2025-02-15', 'дата изготовления (текст → ISO)');
        assertEqual(ppe[0].дата_изготовления, '', 'без даты изготовления — пусто');
        assertEqual(ppe[0].наименование, 'Костюм для защиты от растворов кислот и щелочей',
            'наименование');
    });""",
'2. VM listPpe — фикстура 10 столбцов')

# --- 3. makePpeServer: +_ppeHasManufactureCol ---------------------------
rep(
"""    const methods = ['_parseIsoDate', '_parseSheetDate', '_safeDate', '_toIsoDate',
                     '_appendRowKeepText', 'listPpe', 'addPpe', 'updatePpe',
                     'deletePpe', '_ppeLookupEmployee', '_ppeTermMonths',
                     '_ppeExpiry'];""",
"""    const methods = ['_parseIsoDate', '_parseSheetDate', '_safeDate', '_toIsoDate',
                     '_appendRowKeepText', 'listPpe', 'addPpe', 'updatePpe',
                     'deletePpe', '_ppeLookupEmployee', '_ppeTermMonths',
                     '_ppeExpiry', '_ppeHasManufactureCol'];""",
'3. makePpeServer — +_ppeHasManufactureCol')

# --- 4. addPpe VM: ppeEmpty 10 столбцов + сдвиг ассертов ---------------
rep(
"""    function ppeEmpty() {
        return [['id', 'таб_номер', 'работник', 'должность', 'наименование_СИЗ',
                 'дата_выдачи', 'срок_годности', 'дата_окончания', 'примечание']];
    }

    test('happy-path: id, копии C/D, авто-дата окончания, текстовый B', () => {
        const api = makePpeServer();
        const emp = api.setSheet('Сотрудники', empSheet());
        const sheet = api.setSheet('СИЗ', ppeEmpty());
        const res = api.WSS.addPpe({
            token: 't', 'таб_номер': '2706',
            наименование: 'Костюм для защиты от растворов кислот и щелочей',
            дата_выдачи: '2026-08-17', срок_годности: '1 год', примечание: '',
        });
        assertEqual(res.ok, true, 'успех');
        assertEqual(res.data.id, 1, 'id = max+1');
        const row = sheet._data[1];
        assertEqual(row[1], '2706', 'B: таб_№');
        assertEqual(row[2], 'Галкин Д. Н.', 'C: работник (копия из справочника)');
        assertEqual(row[3], 'Мастер КИПиА', 'D: должность (копия)');
        assertEqual(row[4], 'Костюм для защиты от растворов кислот и щелочей', 'E: наименование');
        assertEqual(row[5].getTime(), new Date(2026, 7, 17).getTime(), 'F: дата выдачи');
        assertEqual(row[6], '1 год', 'G: срок');
        assertEqual(row[7].getTime(), new Date(2027, 7, 17).getTime(),
            'H: АВТО-дата окончания = выдача + 1 год');
        assertTrue(sheet._formats.some(f => f.col === 2 && f.f === '@'),
            'B — текстовый формат (Task 304)');
        assertTrue(api.audits().indexOf('WORKSCHEDULE_ADD_PPE') !== -1, 'аудит');
    });

    test('«До износа» → дата окончания строкой; без даты — пусто', () => {
        const api = makePpeServer();
        api.setSheet('Сотрудники', empSheet());
        const sheet = api.setSheet('СИЗ', ppeEmpty());
        api.WSS.addPpe({ token: 't', 'таб_номер': '2706',
            наименование: 'Очки закрытые', срок_годности: 'До износа' });
        assertEqual(sheet._data[1][7], 'До износа', 'H = «До износа» (текст)');
        api.WSS.addPpe({ token: 't', 'таб_номер': '2706',
            наименование: 'Ботинки', срок_годности: '1,5 года' });
        assertTrue(sheet._data[2][5] === null || sheet._data[2][5] === '',
            'F: не выдано — пусто');
        assertTrue(sheet._data[2][7] === null || sheet._data[2][7] === '',
            'H: без даты — пусто');
        assertEqual(sheet._data[2][0], 2, 'id инкрементится');
    });""",
"""    function ppeEmpty() {
        // Task 443: шапка новой структуры (G — дата изготовления)
        return [['id', 'таб_номер', 'работник', 'должность', 'наименование_СИЗ',
                 'дата_выдачи', 'дата_изготовления', 'срок_годности',
                 'дата_окончания', 'примечание']];
    }

    test('happy-path: id, копии C/D, авто-дата окончания, текстовый B', () => {
        const api = makePpeServer();
        const emp = api.setSheet('Сотрудники', empSheet());
        const sheet = api.setSheet('СИЗ', ppeEmpty());
        const res = api.WSS.addPpe({
            token: 't', 'таб_номер': '2706',
            наименование: 'Костюм для защиты от растворов кислот и щелочей',
            дата_выдачи: '2026-08-17', срок_годности: '1 год', примечание: '',
        });
        assertEqual(res.ok, true, 'успех');
        assertEqual(res.data.id, 1, 'id = max+1');
        const row = sheet._data[1];
        assertEqual(row[1], '2706', 'B: таб_№');
        assertEqual(row[2], 'Галкин Д. Н.', 'C: работник (копия из справочника)');
        assertEqual(row[3], 'Мастер КИПиА', 'D: должность (копия)');
        assertEqual(row[4], 'Костюм для защиты от растворов кислот и щелочей', 'E: наименование');
        assertEqual(row[5].getTime(), new Date(2026, 7, 17).getTime(), 'F: дата выдачи');
        assertTrue(row[6] === null || row[6] === '',
            'G: без даты изготовления — пусто (Task 443)');
        assertEqual(row[7], '1 год', 'H: срок (Task 443: сместился из G)');
        assertEqual(row[8].getTime(), new Date(2027, 7, 17).getTime(),
            'I: АВТО-дата окончания = выдача + 1 год (без изготовления)');
        assertEqual(row[9], '', 'J: примечание (Task 443: сместилось из I)');
        assertTrue(sheet._formats.some(f => f.col === 2 && f.f === '@'),
            'B — текстовый формат (Task 304)');
        assertTrue(api.audits().indexOf('WORKSCHEDULE_ADD_PPE') !== -1, 'аудит');
    });

    test('«До износа» → дата окончания строкой; без даты — пусто', () => {
        const api = makePpeServer();
        api.setSheet('Сотрудники', empSheet());
        const sheet = api.setSheet('СИЗ', ppeEmpty());
        api.WSS.addPpe({ token: 't', 'таб_номер': '2706',
            наименование: 'Очки закрытые', срок_годности: 'До износа' });
        assertEqual(sheet._data[1][8], 'До износа', 'I = «До износа» (текст; Task 443)');
        api.WSS.addPpe({ token: 't', 'таб_номер': '2706',
            наименование: 'Ботинки', срок_годности: '1,5 года' });
        assertTrue(sheet._data[2][5] === null || sheet._data[2][5] === '',
            'F: не выдано — пусто');
        assertTrue(sheet._data[2][8] === null || sheet._data[2][8] === '',
            'I: без даты — пусто');
        assertEqual(sheet._data[2][0], 2, 'id инкрементится');
    });""",
'4. addPpe VM — сдвиг столбцов')

# --- 5. updatePpe VM: фикстура 10 столбцов + сдвиг ассертов ------------
rep(
"""    function ppeSheet() {
        return [
            ['id', 'таб_номер', 'работник', 'должность', 'наименование_СИЗ',
             'дата_выдачи', 'срок_годности', 'дата_окончания', 'примечание'],
            [5, '2706', 'Галкин Д. Н.', 'Мастер КИПиА (стар.)', 'Каска защитная',
             new Date(2025, 0, 10), '2 года', new Date(2027, 0, 10), 'До износа'],
            [6, '2706', 'Галкин Д. Н.', 'Мастер КИПиА', 'Подшлемник',
             '', '', '', ''],
        ];
    }

    test('updatePpe: B..I по id, копии освежены, дата пересчитана', () => {
        const api = makePpeServer();
        api.setSheet('Сотрудники', empSheet());
        const sheet = api.setSheet('СИЗ', ppeSheet());
        const res = api.WSS.updatePpe({
            token: 't', id: 5, 'таб_номер': '2706',
            наименование: 'Каска защитная',
            дата_выдачи: '2026-09-01', срок_годности: '1 год',
            примечание: 'новая выдача',
        });
        assertEqual(res.ok, true, 'успех');
        const row = sheet._data[1];
        assertEqual(row[0], 5, 'A: id не меняется');
        assertEqual(row[3], 'Мастер КИПиА', 'D: должность освежена из справочника');
        assertEqual(row[5].getTime(), new Date(2026, 8, 1).getTime(), 'F: новая дата выдачи');
        assertEqual(row[6], '1 год', 'G: новый срок');
        assertEqual(row[7].getTime(), new Date(2027, 8, 1).getTime(),
            'H: АВТО-дата пересчитана');
        assertEqual(row[8], 'новая выдача', 'I: примечание');
        assertEqual(sheet._data[2][4], 'Подшлемник', 'чужая строка не тронута');
        assertTrue(sheet._formats.some(f => f.row === 2 && f.col === 2 && f.f === '@'),
            'B — текстовый формат при правке');
        assertTrue(api.audits().indexOf('WORKSCHEDULE_UPDATE_PPE') !== -1, 'аудит');
    });""",
"""    function ppeSheet() {
        // Task 443: шапка новой структуры (G — дата изготовления)
        return [
            ['id', 'таб_номер', 'работник', 'должность', 'наименование_СИЗ',
             'дата_выдачи', 'дата_изготовления', 'срок_годности',
             'дата_окончания', 'примечание'],
            [5, '2706', 'Галкин Д. Н.', 'Мастер КИПиА (стар.)', 'Каска защитная',
             new Date(2025, 0, 10), '', '2 года', new Date(2027, 0, 10), 'До износа'],
            [6, '2706', 'Галкин Д. Н.', 'Мастер КИПиА', 'Подшлемник',
             '', '', '', '', ''],
        ];
    }

    test('updatePpe: B..J по id, копии освежены, дата пересчитана', () => {
        const api = makePpeServer();
        api.setSheet('Сотрудники', empSheet());
        const sheet = api.setSheet('СИЗ', ppeSheet());
        const res = api.WSS.updatePpe({
            token: 't', id: 5, 'таб_номер': '2706',
            наименование: 'Каска защитная',
            дата_выдачи: '2026-09-01', срок_годности: '1 год',
            примечание: 'новая выдача',
        });
        assertEqual(res.ok, true, 'успех');
        const row = sheet._data[1];
        assertEqual(row[0], 5, 'A: id не меняется');
        assertEqual(row[3], 'Мастер КИПиА', 'D: должность освежена из справочника');
        assertEqual(row[5].getTime(), new Date(2026, 8, 1).getTime(), 'F: новая дата выдачи');
        assertTrue(row[6] === null || row[6] === '',
            'G: дата изготовления пустая (Task 443)');
        assertEqual(row[7], '1 год', 'H: новый срок (Task 443: сместился из G)');
        assertEqual(row[8].getTime(), new Date(2027, 8, 1).getTime(),
            'I: АВТО-дата пересчитана (Task 443: сместилась из H)');
        assertEqual(row[9], 'новая выдача', 'J: примечание (Task 443: сместилось из I)');
        assertEqual(sheet._data[2][4], 'Подшлемник', 'чужая строка не тронута');
        assertTrue(sheet._formats.some(f => f.row === 2 && f.col === 2 && f.f === '@'),
            'B — текстовый формат при правке');
        assertTrue(api.audits().indexOf('WORKSCHEDULE_UPDATE_PPE') !== -1, 'аудит');
    });""",
'5. updatePpe VM — сдвиг столбцов')

io.open(P, 'w', encoding='utf-8').write(s)
print('\ntest-task392.js: файл записан (%d -> %d байт)' % (len(n0), len(s)))
