#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: адаптация tests/test-task438.js — легенда кодов удалена
# из печати (HTML/PDF/Excel): хосты без _printCodesData (+ карта
# стилей), ассерты «кодов» переработаны под отсутствие.
import io

P = 'tests/test-task438.js'
s = io.open(P, encoding='utf-8').read()
orig = s
fail = []


def rep(old, new, tag, cnt=1):
    global s
    n = s.count(old)
    if n != cnt:
        fail.append('[%s] вхождений %d, ожидалось %d' % (tag, n, cnt))
        print('FAIL [%s]: %d (ожидалось %d)' % (tag, n, cnt))
        return
    s = s.replace(old, new)
    print('OK [%s]' % tag)


# --- 1. Хосты: _printCodesData → _wsTabelStyleMap (2 места) ---
rep("            methodText(WS_CLIENT, '_printCodesData') + ',' +\n"
    "            methodText(WS_CLIENT, '_wsTabelStylesXml') + ',' +",
    "            methodText(WS_CLIENT, '_wsTabelStyleMap') + ',' +\n"
    "            methodText(WS_CLIENT, '_wsTabelStylesXml') + ',',",
    'host-stylemap', 2)
rep("            methodText(WS_CLIENT, '_printEventsData') + ',' +\n"
    "            methodText(WS_CLIENT, '_printCodesData') + ',' +",
    "            methodText(WS_CLIENT, '_printEventsData') + ',' +",
    'host-model-stylemap')

# --- 2. SRC: перечень кодов — теперь УДАЛЁН ---
rep("""    test('SRC: перечень кодов — сокращённый вид (short)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const i = b.indexOf('var lgShort =');
        assertTrue(i !== -1, 'выбор сокращения в цикле легенды');
        const tail = b.slice(i, i + 200);
        assertTrue(tail.indexOf('codes[ci].short || codes[ci].name') !== -1,
            'short с фолбэком name (коды вне канона без short)');
        assertTrue(tail.indexOf('lgShort') !== -1,
            'сокращение печатается после кода');
    });
""",
    """    test('SRC: перечень кодов — УДАЛЁН из печати (Task 442)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('var lgShort =') === -1,
            'цикла легенды (lgShort) больше нет — столбец кодов удалён');
        assertTrue(b.indexOf('wsp-legend') === -1,
            'блока кодов в разметке нет');
        assertTrue(b.indexOf('wsp-lg') === -1,
            'записей кодов нет');
    });
""", 'src-codes-removed')

# --- 3. SRC: список методов — без _printCodesData ---
rep("""        for (const m of ['_printModel', '_printEventsData', '_printCodesData',
                         '_printPdfLayout', '_buildPdfDocument',""",
    """        assertTrue(extractMethod(WS_CLIENT, '_printCodesData') === null,
            'Task 442: метод _printCodesData удалён (столбца кодов нет)');
        for (const m of ['_printModel', '_printEventsData',
                         '_printPdfLayout', '_buildPdfDocument',""",
    'src-methods-list')

# --- 4. VM: коды в HTML — сокращений больше нет ---
rep("""    test('VM: коды — сокращённый вид (short), фолбэк name', () => {
        const entries = {
            '2026-09-02|017': { 'статус': 'ОТ' },
            '2026-09-03|031': { 'статус': 'Д' }
        };
        const html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('ОТ — отпуск') !== -1,
            'код месяца ОТ — с сокращением (short)');
        assertTrue(html.indexOf('Отпуск, ежегодный основной оплачиваемый отпуск') === -1,
            'полное наименование ОТ больше не печатается');
        assertTrue(html.indexOf('Д — день 12ч') !== -1,
            'код Д — с сокращением');
        // фолбэк: код вне канона без short печатает name
        const customCodes = [
            { code: 'ОТ', name: 'Отпуск, ежегодный основной оплачиваемый отпуск', color: '#ECEFF1' },
            { code: 'XX', name: 'Особый случай', color: '#FFCCBC' }
        ];
        const html2 = sheetHost({ entries: entries, codes: customCodes })
            ._buildPrintHtml(EMPS, AGG);
        assertTrue(html2.indexOf('ОТ — Отпуск, ежегодный основной оплачиваемый отпуск') !== -1,
            'нет short — печатается name (фолбэк)');
    });
""",
    """    test('VM: перечень кодов в HTML — УДАЛЁН (Task 442)', () => {
        const entries = {
            '2026-09-02|017': { 'статус': 'ОТ' },
            '2026-09-03|031': { 'статус': 'Д' }
        };
        const html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('ОТ — отпуск') === -1,
            'строк легенды кодов нет (столбец удалён)');
        assertTrue(html.indexOf('Д — день 12ч') === -1,
            'код Д не расшифровывается на листе');
        assertTrue(html.indexOf('wsp-legend') === -1 &&
                   html.indexOf('wsp-lg') === -1,
            'разметки легенды нет вовсе');
        // ячейки шахматки по-прежнему несут коды с цветами
        assertTrue(html.indexOf('background:#FFE082') !== -1,
            'цвет кода Д в ячейках жив (цвета из справочника)');
    });
""", 'vm-html-codes')

# --- 5. VM: usedCodes в модели больше нет ---
rep("""    test('VM: usedCodes — только эффективные коды месяца', () => {
        const m = modelHost({ entries: ENTRIES, pending: PENDING })
            ._printModel(EMPS, AGG);
        assertTrue(m.usedCodes['ОТ'] === true, 'правка ОТ учтена');
        assertTrue(m.usedCodes['.'] === true, '«.» учтён (слот Выходной)');
        assertTrue(m.usedCodes['Д'] === undefined,
            'перекрытый Д не попадает (правка важнее)');
        assertTrue(m.usedCodes['Н'] === undefined,
            'удалённая запись Н не попадает');
    });
""",
    """    test('VM: usedCodes — поле УДАЛЕНО из модели (Task 442)', () => {
        const m = modelHost({ entries: ENTRIES, pending: PENDING })
            ._printModel(EMPS, AGG);
        assertTrue(!('usedCodes' in m),
            'модель печати не собирает коды — столбца кодов нет');
    });
""", 'vm-usedcodes')

# --- 6. VM: codes в модели больше нет ---
rep("""    test('VM: коды — сокращённый вид, порядок справочника, легаси', () => {
        const m = modelHost({ entries: ENTRIES, pending: PENDING })
            ._printModel(EMPS, AGG);
        // порядок — как в справочнике фикстуры: ОТ (используется),
        // затем слот «» (Выходной, по «.»); легаси вне справочника
        // (И, ОБ — коды мероприятий) — в конец; «.» НЕ дублируется
        assertEqual(m.codes.length, 4, 'ОТ + Выходной + легаси И/ОБ');
        assertEqual(m.codes[0].code, 'ОТ', 'ОТ — в порядке справочника');
        assertEqual(m.codes[0].label, 'отпуск', 'сокращение ОТ (short)');
        assertEqual(m.codes[1].code, '', 'слот «Выходной» (по «.»)');
        assertEqual(m.codes[1].label, 'выходной', 'метка Выходного');
        assertEqual(m.codes[2].code, 'И', 'легаси И (код мероприятия)');
        assertEqual(m.codes[3].code, 'ОБ', 'легаси ОБ');
        assertEqual(m.codes[2].label, '', 'у легаси-кода нет расшифровки');
        // Task 438: голая «.» НЕ дублируется — точка раскрыта слотом
        // «Выходной» (пустой код) первым элементом списка
        let hasDot = false;
        for (const c of m.codes) { if (c.code === '.') hasDot = true; }
        assertFalse(hasDot, '«.» в перечне не дублируется (Task 438)');
    });
""",
    """    test('VM: codes — поле УДАЛЕНО из модели (Task 442)', () => {
        const m = modelHost({ entries: ENTRIES, pending: PENDING })
            ._printModel(EMPS, AGG);
        assertTrue(!('codes' in m),
            'перечень кодов не строится — столбца кодов нет');
    });
""", 'vm-model-codes')

rep("""    test('VM: события без «Инструктажей» — пустой массив, не падает', () => {
        const m = modelHost({ trainings: [] })._printModel(EMPS, AGG);
        assertEqual(m.events.length, 0, 'событий нет');
        assertEqual(m.codes.length, 0, 'кодов месяца нет (нет и «.»)');
    });
""",
    """    test('VM: события без «Инструктажей» — пустой массив, не падает', () => {
        const m = modelHost({ trainings: [] })._printModel(EMPS, AGG);
        assertEqual(m.events.length, 0, 'событий нет');
        assertTrue(!('codes' in m), 'кодов месяца нет (поле удалено)');
    });
""", 'vm-events-empty')

# --- 7. VM: раскладка — страницы без кодов ---
rep("""    test('VM: компактный месяц — ОДНА страница со всем', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(10, 3, 4));
        assertEqual(lay.pages.length, 1, '10 строк + события + коды — одна страница');
        const p = lay.pages[0];
        assertTrue(p.first === true, 'первая страница помечена');
        assertEqual(p.rows.length, 10, 'все строки на ней');
        assertEqual(p.events.length, 3, 'события на ней же');
        assertEqual(p.codes.length, 4, 'коды на ней же');
        assertEqual(lay.W, 842, 'A4 альбомная — ширина 842 pt');
        assertEqual(lay.H, 595, 'высота 595 pt');
    });
""",
    """    test('VM: компактный месяц — ОДНА страница со всем', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(10, 3, 4));
        assertEqual(lay.pages.length, 1, '10 строк + события — одна страница');
        const p = lay.pages[0];
        assertTrue(p.first === true, 'первая страница помечена');
        assertEqual(p.rows.length, 10, 'все строки на ней');
        assertEqual(p.events.length, 3, 'события на ней же');
        assertTrue(!p.codes, 'кодов на странице нет (Task 442)');
        assertEqual(lay.W, 842, 'A4 альбомная — ширина 842 pt');
        assertEqual(lay.H, 595, 'высота 595 pt');
    });
""", 'vm-layout-compact')

rep("""        // последняя страница несёт события/коды (или они отдельными)
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.codes, 'коды — на последней странице');
    });

    test('VM: много событий — режутся по страницам, коды в конце', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(60, 200, 4));
        const evPages = lay.pages.filter(p => p.events && p.rows.length === 0);
        assertTrue(evPages.length >= 2, '200 событий — несколько страниц');
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.codes, 'коды — на самой последней странице');
        let evTotal = 0;
        for (const p of evPages) evTotal += p.events.length;
        assertEqual(evTotal, 200, 'все события распределены');
    });

    test('VM: пустой месяц (0 строк) — не падает, события/коды живут', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(0, 0, 2));
        assertTrue(lay.pages.length >= 1, 'страницы есть');
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.codes, 'коды размещены');
        assertTrue(!!last.events, 'события (пустой список) размещены');
    });
""",
    """        // последняя страница несёт события (или они отдельными)
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.events, 'события — на последней странице');
    });

    test('VM: много событий — режутся по страницам', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(60, 200, 4));
        const evPages = lay.pages.filter(p => p.events && p.rows.length === 0);
        assertTrue(evPages.length >= 2, '200 событий — несколько страниц');
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.events, 'последняя страница — мероприятия');
        assertTrue(!last.codes, 'кодов нет (Task 442)');
        let evTotal = 0;
        for (const p of evPages) evTotal += p.events.length;
        assertEqual(evTotal, 200, 'все события распределены');
    });

    test('VM: пустой месяц (0 строк) — не падает, события живут', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(0, 0, 2));
        assertTrue(lay.pages.length >= 1, 'страницы есть');
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.events, 'события (пустой список) размещены');
    });
""", 'vm-layout-tail')

# --- 8. VM: Excel — секция кодов удалена ---
rep("""        assertTrue(sheet.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'секция мероприятий с счётчиком');
        assertTrue(sheet.indexOf('02.09') !== -1, 'дата мероприятия');
        assertTrue(sheet.indexOf('И · Повторный инструктаж · Иванов Иван Иванович') !== -1,
            'текст события: код · сокращение · ФИО');
        assertTrue(sheet.indexOf('>Коды:<') !== -1, 'секция «Коды:»');
        assertTrue(sheet.indexOf('Д — день 12ч') !== -1, 'код Д — сокращённо');
        assertTrue(sheet.indexOf('ОТ — отпуск') !== -1, 'код ОТ — сокращённо');
        assertTrue(sheet.indexOf('Отпуск, ежегодный основной оплачиваемый отпуск') === -1,
            'полные наименования кодов не выгружаются');
    });
""",
    """        assertTrue(sheet.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'секция мероприятий с счётчиком');
        assertTrue(sheet.indexOf('02.09') !== -1, 'дата мероприятия');
        assertTrue(sheet.indexOf('И · Повторный инструктаж · Иванов Иван Иванович') !== -1,
            'текст события: код · сокращение · ФИО');
        // Task 442: столбец кодов удалён — секция «Коды:» НЕ выгружается
        assertTrue(sheet.indexOf('>Коды:<') === -1, 'секции «Коды:» нет');
        assertTrue(sheet.indexOf('Д — день 12ч') === -1,
            'расшифровок кодов в книге нет');
        assertTrue(sheet.indexOf('ОТ — отпуск') === -1,
            'расшифровки ОТ нет');
    });
""", 'vm-xlsx-codes')

io.open(P, 'w', encoding='utf-8').write(s)
print()
print('=== ИТОГ task442-adapt-438 ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ГОТОВО: %d замен' % (len([1]) if s == orig else 1))
