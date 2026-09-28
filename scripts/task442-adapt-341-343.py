#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: адаптация tests/test-task341.js и test-task343.js —
# бейджи мероприятий в печати УДАЛЕНЫ, серая заливка выходных снята
# (контур вместо), легенда кодов удалена.
import io

fail = []


def adapt(path, reps):
    s = io.open(path, encoding='utf-8').read()
    ok = 0
    for old, new, tag in reps:
        n = s.count(old)
        if n != 1:
            fail.append('[%s/%s] вхождений %d' % (path, tag, n))
            print('FAIL [%s %s]: %d' % (path, tag, n))
            continue
        s = s.replace(old, new)
        ok += 1
        print('OK [%s %s]' % (path, tag))
    io.open(path, 'w', encoding='utf-8').write(s)
    return ok


# ============================================================
# test-task341.js
# ============================================================
T341 = 'tests/test-task341.js'
adapt(T341, [
    ("""    test('VM: статус-мероприятие (И) — ПУСТАЯ ячейка + бейдж в углу (Task 361)', () => {
        var td = cellHost({ meta: { code: 'И', color: '#B3E5FC' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(5, '2026-09-05', EMP, { 'статус': 'И' });
        assertTrue(td.indexOf('>И</td>') === -1, 'большого кода нет');
        assertTrue(td.indexOf('wsp-ev-wrap') !== -1,
            'бейдж мероприятия в печати есть (Task 361 вернул)');
        assertTrue(td.indexOf('background:#B3E5FC') !== -1,
            'сплошной бейдж с цветом кода (день сформирован)');
    });

    test('VM: событие в ПУСТОЙ ячейке — пунктирный бейдж-план (Task 361)', () => {
        var td = cellHost({ events: [{ code: 'И', training: 7 }] })
            ._printCell(6, '2026-09-06', EMP, null);
        assertFalse(td.indexOf('wsp-ev-plan') !== -1,
            'пунктирного бейджа нет (Task 388)');
        assertTrue(td.indexOf('background:') !== -1,
            'заливка цветом кода — и у несформированного дня (Task 388)');
    });

    test('VM: статус-мероприятие БЕЗ строки в «Инструктажах» — ВИРТУАЛЬНЫЙ бейдж (Task 361)', () => {
        var td = cellHost({ meta: { code: 'ОБ', color: '#D1C4E9' } })
            ._printCell(7, '2026-09-07', EMP, { 'статус': 'ОБ' });
        assertTrue(td.indexOf('wsp-ev') !== -1 && td.indexOf('>ОБ</span>') !== -1,
            'виртуальный бейдж строится — день не теряет мероприятие');
        assertTrue(td.indexOf('background:#D1C4E9') !== -1,
            'цвет кода из справочника');
    });
""",
     """    test('VM: статус-мероприятие (И) — ПУСТАЯ ячейка БЕЗ бейджа (Task 442)', () => {
        var td = cellHost({ meta: { code: 'И', color: '#B3E5FC' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(5, '2026-09-05', EMP, { 'статус': 'И' });
        assertTrue(td.indexOf('>И</td>') === -1, 'большого кода нет');
        assertTrue(td.indexOf('wsp-ev') === -1,
            'бейджа мероприятия НЕТ (Task 442 удалил мини-значки)');
        assertTrue(td.indexOf('background:') === -1,
            'фона нет — ячейка пустая (событие — в списке под таблицей)');
    });

    test('VM: событие в ПУСТОЙ ячейке — бейджей нет (Task 442)', () => {
        var td = cellHost({ events: [{ code: 'И', training: 7 }] })
            ._printCell(6, '2026-09-06', EMP, null);
        assertTrue(td.indexOf('wsp-ev') === -1,
            'бейджей нет — мини-значки удалены (Task 442)');
        assertTrue(td.indexOf('background:') === -1,
            'заливки нет (пустой день без статуса)');
    });

    test('VM: статус-мероприятие БЕЗ строки в «Инструктажах» — ячейка пустая (Task 442)', () => {
        var td = cellHost({ meta: { code: 'ОБ', color: '#D1C4E9' } })
            ._printCell(7, '2026-09-07', EMP, { 'статус': 'ОБ' });
        assertTrue(td.indexOf('wsp-ev') === -1,
            'виртуального бейджа нет (Task 442 удалил значки)');
        assertTrue(td.indexOf('>ОБ<') === -1,
            'код мероприятия в ячейке не печатается');
        assertTrue(td.indexOf('background:') === -1,
            'фона нет — мероприятие раскрывается списком ниже');
    });
""", 'printcell-badges'),

    ("""    test('VM: нерабочий день — серая заливка ТОЛЬКО пустой ячейки', () => {
        var empty = cellHost({ dayOff: true })
            ._printCell(12, '2026-09-12', EMP, null);
        assertTrue(empty.indexOf('wsp-cell-off') !== -1,
            'пустая нерабочая — заливка');
        var coded = cellHost({ dayOff: true })
            ._printCell(13, '2026-09-13', EMP, { 'статус': 'Н' });
        assertTrue(coded.indexOf('wsp-cell-off') === -1,
            'статусная нерабочая — свой цвет');
        var vac = cellHost({ dayOff: true, vac: {} })
            ._printCell(14, '2026-09-14', EMP, null);
        assertTrue(vac.indexOf('wsp-cell-off') === -1,
            'план отпуска — без серой заливки');
    });
""",
     """    test('VM: нерабочий день — БЕЗ заливки, маркер контура (Task 442)', () => {
        var empty = cellHost({ dayOff: true })
            ._printCell(12, '2026-09-12', EMP, null);
        assertTrue(empty.indexOf('wsp-cell-off') !== -1,
            'пустая нерабочая — маркер полосы выходных');
        assertTrue(empty.indexOf('background:') === -1,
            'заливки НЕТ (Task 442: фоном не выделяем)');
        var coded = cellHost({ dayOff: true })
            ._printCell(13, '2026-09-13', EMP, { 'статус': 'Н' });
        assertTrue(coded.indexOf('wsp-cell-off') !== -1,
            'статусная нерабочая — тоже в полосе контура (Task 442)');
        var vac = cellHost({ dayOff: true, vac: {} })
            ._printCell(14, '2026-09-14', EMP, null);
        assertTrue(vac.indexOf('wsp-cell-off') !== -1,
            'план отпуска в выходной — тоже в полосе (Task 442)');
    });
""", 'printcell-off'),

    ("""        var html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('wsp-sum') === -1, 'строки «Итого» нет (Task 343)');
        assertTrue(html.indexOf('>40</td>') === -1, 'итога дней нет (grand 40)');
        assertTrue(html.indexOf('>288</td>') === -1, 'итога часов нет (grand 288)');
        assertTrue(html.indexOf('wsp-legend') !== -1, 'легенда кодов');
        assertTrue(html.indexOf('Д — День (12-час)') !== -1,
            'код месяца Д с расшифровкой из справочника');
        assertTrue(html.indexOf('Н — Ночь (12-час)') !== -1,
            'код месяца Н с расшифровкой');
        assertTrue(html.indexOf('wsp-foot') === -1,
            'пояснения внизу удалены (Task 438)');
    });
""",
     """        var html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('wsp-sum') === -1, 'строки «Итого» нет (Task 343)');
        assertTrue(html.indexOf('>40</td>') === -1, 'итога дней нет (grand 40)');
        assertTrue(html.indexOf('>288</td>') === -1, 'итога часов нет (grand 288)');
        // Task 442: легенда кодов УДАЛЕНА — расшифровок на листе нет
        assertTrue(html.indexOf('wsp-legend') === -1,
            'легенды кодов нет (Task 442: столбец удалён)');
        assertTrue(html.indexOf('Д — День (12-час)') === -1,
            'расшифровки кода Д нет');
        assertTrue(html.indexOf('Н — Ночь (12-час)') === -1,
            'расшифровки кода Н нет');
        assertTrue(html.indexOf('wsp-foot') === -1,
            'пояснения внизу удалены (Task 438)');
    });
""", 'legend-removed'),
])

# ============================================================
# test-task343.js
# ============================================================
T343 = 'tests/test-task343.js'
adapt(T343, [
    ("""    test('SRC: _printCell строит wsp-ev и вызывает _eventsAt (Task 361)', () => {
        const c = stripComments(methodText(WS_CLIENT, '_printCell'));
        assertTrue(c.length > 0, 'метод найден');
        assertTrue(c.indexOf('wsp-ev') !== -1, 'бейджи wsp-ev строятся');
        assertTrue(c.indexOf('_eventsAt') !== -1, '_eventsAt вызывается');
        assertFalse(c.indexOf('wsp-ev-plan') !== -1,
            'пунктирных бейджей-план больше нет (Task 388: заливка всегда)');
    });

    test('SRC: CSS-правила бейджей .wsp-ev* в @media print (Task 361)', () => {
        const i = INDEX_SRC.indexOf('@media print');
        const block = stripComments(INDEX_SRC.slice(i, i + 9000));
        assertTrue(block.indexOf('#wsPrintSheet .wsp-ev') !== -1,
            'правило .wsp-ev есть');
        assertTrue(block.indexOf('wsp-ev-wrap') !== -1,
            'правило .wsp-ev-wrap есть');
        assertFalse(block.indexOf('wsp-ev-plan') !== -1,
            'правила .wsp-ev-plan нет (Task 388: пунктирные удалены)');
    });
""",
     """    test('SRC: _printCell — бейджей НЕТ, _eventsAt НЕ зовётся (Task 442)', () => {
        const c = stripComments(methodText(WS_CLIENT, '_printCell'));
        assertTrue(c.length > 0, 'метод найден');
        assertTrue(c.indexOf('wsp-ev') === -1,
            'бейджи wsp-ev удалены из печати (Task 442: «убери мини значки»)');
        assertTrue(c.indexOf('_eventsAt') === -1,
            '_eventsAt из печатной ячейки не вызывается (значков нет)');
    });

    test('SRC: CSS-правила бейджей .wsp-ev* УДАЛЕНЫ (Task 442)', () => {
        const i = INDEX_SRC.indexOf('@media print');
        const block = stripComments(INDEX_SRC.slice(i, i + 9000));
        assertTrue(block.indexOf('#wsPrintSheet .wsp-ev') === -1,
            'правила .wsp-ev нет (удалено вместе со значками)');
        assertTrue(block.indexOf('wsp-ev-wrap') === -1,
            'правила .wsp-ev-wrap нет');
    });
""", 'src-badges'),

    ("""    test('VM: статус-мероприятие «И» — ПУСТАЯ ячейка + сплошной бейдж (Task 361)', () => {
        var td = cellHost({ meta: { code: 'И', color: '#B3E5FC' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(10, '2026-09-10', EMP, { 'статус': 'И' });
        assertTrue(td.indexOf('>И</td>') === -1, 'большого кода нет');
        assertTrue(td.indexOf('wsp-ev') !== -1, 'бейдж есть');
        assertTrue(td.indexOf('background:#B3E5FC') !== -1,
            'бейдж с цветом кода (день сформирован — сплошной)');
    });

    test('VM: события дня в ПУСТОЙ ячейке — пунктирные бейджи-план (Task 361)', () => {
        var td = cellHost({ events: [{ code: 'ОБ', training: 8 },
                                      { code: 'ПР', training: 9 }] })
            ._printCell(11, '2026-09-11', EMP, null);
        assertTrue(td.indexOf('wsp-ev') !== -1, 'бейджи есть');
        assertFalse(td.indexOf('wsp-ev-plan') !== -1,
            'пунктирных нет (Task 388: заливка всегда)');
        assertTrue(td.indexOf('>ОБ<') !== -1 && td.indexOf('>ПР<') !== -1,
            'коды мероприятий в бейджах');
        assertTrue(td.indexOf('background:') !== -1,
            'с заливкой цветом кода (Task 388)');
    });
""",
     """    test('VM: статус-мероприятие «И» — ПУСТАЯ ячейка без бейджа (Task 442)', () => {
        var td = cellHost({ meta: { code: 'И', color: '#B3E5FC' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(10, '2026-09-10', EMP, { 'статус': 'И' });
        assertTrue(td.indexOf('>И</td>') === -1, 'большого кода нет');
        assertTrue(td.indexOf('wsp-ev') === -1,
            'бейджа НЕТ (Task 442: мини-значки удалены)');
        assertTrue(td.indexOf('background:') === -1,
            'фона нет — событие раскрывается списком мероприятий');
    });

    test('VM: события дня в ПУСТОЙ ячейке — бейджей НЕТ (Task 442)', () => {
        var td = cellHost({ events: [{ code: 'ОБ', training: 8 },
                                      { code: 'ПР', training: 9 }] })
            ._printCell(11, '2026-09-11', EMP, null);
        assertTrue(td.indexOf('wsp-ev') === -1,
            'бейджей нет (Task 442)');
        assertTrue(td.indexOf('>ОБ<') === -1 && td.indexOf('>ПР<') === -1,
            'коды мероприятий в ячейке не печатаются');
        assertTrue(td.indexOf('background:') === -1, 'заливки нет');
    });
""", 'vm-badges'),

    ("""    test('VM: _eventsAt в моке вызывается из _printCell (Task 361)', () => {
        // счётчик — на global: тело new Function видит только
        // глобальную область видимости
        global.__t343evCalls = 0;
        var host = new Function('return ({' +
            methodText(WS_CLIENT, '_printCell') + '\\n' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_statusMeta: function() { return {}; },' +
            '_calDayOff: function() { return false; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { global.__t343evCalls++; return []; },' +
            '_esc: ' + mockEsc.toString() + ',' +
            '});')();
        host._printCell(5, '2026-09-05', EMP, { 'статус': 'И' });
        host._printCell(6, '2026-09-06', EMP, null);
        assertEqual(global.__t343evCalls, 2, '_eventsAt вызывается для каждой ячейки');
    });
""",
     """    test('VM: _eventsAt из _printCell НЕ вызывается (Task 442)', () => {
        // счётчик — на global: тело new Function видит только
        // глобальную область видимости. Task 442: значков в печати
        // нет — печатная ячейка больше не спрашивает события дня
        global.__t343evCalls = 0;
        var host = new Function('return ({' +
            methodText(WS_CLIENT, '_printCell') + '\\n' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_statusMeta: function() { return {}; },' +
            '_calDayOff: function() { return false; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { global.__t343evCalls++; return []; },' +
            '_esc: ' + mockEsc.toString() + ',' +
            '});')();
        host._printCell(5, '2026-09-05', EMP, { 'статус': 'И' });
        host._printCell(6, '2026-09-06', EMP, null);
        assertEqual(global.__t343evCalls, 0,
            '_eventsAt НЕ вызывается — бейджей в печати нет (Task 442)');
    });
""", 'vm-eventsat'),

    ("""    test('VM: структура — шапка, строки, легенда; после строк таблица закрывается', () => {
        var agg = { byTab: {}, grand: null };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        var iClose = html.indexOf('</tbody></table>');
        assertTrue(iClose !== -1, 'таблица закрыта');
        assertTrue(html.indexOf('wsp-legend') !== -1, 'легенда после таблицы');
        assertTrue(html.indexOf('wsp-foot') === -1, 'сноски нет (Task 438)');
        assertTrue(html.indexOf('<tr class="') === -1 ||
                   html.indexOf('wsp-sum') === -1, 'служебных строк нет');
    });

    test('VM: сноски нет — лист заканчивается перечнем кодов (Task 438)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, { byTab: {}, grand: null });
        assertTrue(html.indexOf('wsp-foot') === -1, 'сноски нет (Task 438)');
        assertTrue(html.indexOf('сокращённый предпраздничный') === -1,
            'текста сноски нет');
    });
""",
     """    test('VM: структура — шапка, строки, мероприятия; легенды НЕТ (Task 442)', () => {
        var agg = { byTab: {}, grand: null };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        var iClose = html.indexOf('</tbody></table>');
        assertTrue(iClose !== -1, 'таблица закрыта');
        assertTrue(html.indexOf('wsp-mev') !== -1,
            'секция мероприятий после таблицы');
        assertTrue(html.indexOf('wsp-legend') === -1,
            'легенды кодов НЕТ (Task 442: столбец удалён)');
        assertTrue(html.indexOf('wsp-foot') === -1, 'сноски нет (Task 438)');
        assertTrue(html.indexOf('<tr class="') === -1 ||
                   html.indexOf('wsp-sum') === -1, 'служебных строк нет');
    });

    test('VM: сноски нет — лист заканчивается списком мероприятий (Task 442)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, { byTab: {}, grand: null });
        assertTrue(html.indexOf('wsp-foot') === -1, 'сноски нет (Task 438)');
        assertTrue(html.indexOf('сокращённый предпраздничный') === -1,
            'текста сноски нет');
    });
""", 'vm-structure'),
])

print()
print('=== ИТОГ adapt-341-343 ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ГОТОВО')
