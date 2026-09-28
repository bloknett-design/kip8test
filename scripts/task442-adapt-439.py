#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: адаптация tests/test-task439.js — блок кодов удалён
# (HTML ряд снят, PDF зоны сняты, Excel колонка D снята); «Мероприятия»
# на всю ширину. Хосты — без _printCodesData, +_wsTabelStyleMap.
import io

P = 'tests/test-task439.js'
s = io.open(P, encoding='utf-8').read()
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


# --- 1. CSS .wsp-bottom: ряд снят (Task 442) ---
rep("""    test('CSS: .wsp-bottom — flex-ряд с зазором 10px (Task 440)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r.indexOf('display: flex') !== -1, 'обёртка — гибкий ряд');
        assertTrue(r.indexOf('align-items: flex-start') !== -1,
            'блоки прижаты к общей верхней линии');
        // Task 440 (заявка: «на расстоянии друг от друга 10px»)
        assertTrue(r.indexOf('gap: 10px') !== -1,
            'зазор между блоками — ровно 10px');
        assertTrue(r.indexOf('gap: 6mm') === -1,
            'прежний зазор 6mm убран');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ секции от таблицы жив (Task 364)');
    });

    test('CSS: .wsp-mev — левая часть ряда, .wsp-legend — правая 92mm', () => {
        const mev = ruleBlock('#wsPrintSheet .wsp-mev {');
        // Task 440: flex-grow снят (было 1 1 auto) — коды за текстом
        assertTrue(mev.indexOf('flex: 0 1 auto') !== -1,
            'мероприятия НЕ растягиваются — коды за текстом (Task 440)');
        assertTrue(mev.indexOf('min-width: 0') !== -1, 'усадка для переносов текста');
        const leg = ruleBlock('#wsPrintSheet .wsp-legend {');
        assertTrue(leg.indexOf('flex: 0 0 92mm') !== -1,
            'блок кодов — фиксированная ширина 92mm (справа)');
        assertTrue(leg.indexOf('margin-top: 0') !== -1,
            'отступ сверху снят — общая верхняя линия с мероприятиями');
    });

    test('DOM: порядок секций — мероприятия, затем коды, внутри обёртки', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iCols = b.indexOf('<div class="wsp-legend-cols">');
        assertTrue(iOpen !== -1 && iMev !== -1 && iLegend !== -1,
            'обёртка и секции строятся');
        assertTrue(iOpen < iMev && iMev < iLegend && iLegend < iCols,
            'порядок: обёртка → мероприятия → коды (+сетка 2 колонки Task 434)');
    });
""",
    """    test('CSS: .wsp-bottom — ОДНА колонка (Task 442: кодов нет)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r.indexOf('display: flex') === -1,
            'flex-ряд снят — блока кодов справа больше нет (Task 442)');
        assertTrue(r.indexOf('gap') === -1,
            'зазора между блоками нет (снят вместе с блоком кодов)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ секции от таблицы жив (Task 364)');
    });

    test('CSS: .wsp-mev — вся ширина, .wsp-legend удалён (Task 442)', () => {
        const mev = ruleBlock('#wsPrintSheet .wsp-mev {');
        assertTrue(mev.indexOf('flex:') === -1 && mev.indexOf('min-width') === -1,
            'мероприятия не ограничены — столбик на всю ширину листа');
        assertTrue(ruleBlock('#wsPrintSheet .wsp-legend {') === '' &&
                   INDEX_SRC.indexOf('#wsPrintSheet .wsp-legend {') === -1,
            'правило .wsp-legend удалено вместе с блоком кодов');
    });

    test('DOM: в обёртке — только мероприятия (Task 442)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        assertTrue(iOpen !== -1 && iMev !== -1,
            'обёртка и секция мероприятий строятся');
        assertTrue(iOpen < iMev, 'обёртка → мероприятия');
        assertTrue(b.indexOf('wsp-legend') === -1,
            'секции кодов в разметке нет (столбец удалён, Task 442)');
    });
""", 'css-bottom-mev')

# --- 2. VM печатный лист: без кодов ---
rep("""    test('VM: мероприятия и коды — в одной обёртке, коды следом', () => {
        const html = sheetHost({ entries: { '2026-09-02|017': { 'статус': 'ОТ' } } })
            ._buildPrintHtml(EMPS, AGG);
        const iOpen = html.indexOf('<div class="wsp-bottom">');
        const iMev = html.indexOf('<div class="wsp-mev">');
        const iLegend = html.indexOf('<div class="wsp-legend">');
        const iClose = html.indexOf('</div></div>', iLegend);
        assertTrue(iOpen !== -1 && iMev !== -1 && iLegend !== -1,
            'секции строятся');
        assertTrue(iOpen < iMev && iMev < iLegend,
            'мероприятия слева (первый в DOM), коды — справа (второй)');
        const row = html.slice(iOpen, iClose);
        assertTrue(row.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий в ряду');
        assertTrue(row.indexOf('Коды:') !== -1, 'заголовок кодов в ряду');
        assertTrue(row.indexOf('ОТ — отпуск') !== -1,
            'код месяца в блоке кодов');
    });

    test('VM: пустой месяц мероприятий — заглушка слева, коды справа', () => {
        const html = sheetHost({ trainings: [],
                                 entries: { '2026-09-02|017': { 'статус': 'ОТ' } } })
            ._buildPrintHtml(EMPS, AGG);
        const iOpen = html.indexOf('<div class="wsp-bottom">');
        const row = html.slice(iOpen, html.indexOf('</div></div>', iOpen));
        assertTrue(row.indexOf('нет мероприятий в этом месяце') !== -1,
            'заглушка мероприятий на месте');
        assertTrue(row.indexOf('Коды:') !== -1, 'блок кодов строится');
    });
""",
    """    test('VM: в обёртке — только мероприятия (Task 442)', () => {
        const html = sheetHost({ entries: { '2026-09-02|017': { 'статус': 'ОТ' } } })
            ._buildPrintHtml(EMPS, AGG);
        const iOpen = html.indexOf('<div class="wsp-bottom">');
        const iMev = html.indexOf('<div class="wsp-mev">');
        assertTrue(iOpen !== -1 && iMev !== -1,
            'обёртка и секция мероприятий строятся');
        assertTrue(iOpen < iMev, 'мероприятия — первая (и единственная) секция');
        const row = html.slice(iOpen, html.indexOf('</div></div>', iOpen));
        assertTrue(row.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий на месте');
        assertTrue(row.indexOf('Коды:') === -1,
            'заголовка кодов нет (столбец удалён, Task 442)');
        assertTrue(row.indexOf('ОТ — отпуск') === -1,
            'расшифровок кодов нет');
    });

    test('VM: пустой месяц мероприятий — заглушка, кодов нет', () => {
        const html = sheetHost({ trainings: [],
                                 entries: { '2026-09-02|017': { 'статус': 'ОТ' } } })
            ._buildPrintHtml(EMPS, AGG);
        const iOpen = html.indexOf('<div class="wsp-bottom">');
        const row = html.slice(iOpen, html.indexOf('</div></div>', iOpen));
        assertTrue(row.indexOf('нет мероприятий в этом месяце') !== -1,
            'заглушка мероприятий на месте');
        assertTrue(row.indexOf('Коды:') === -1, 'блока кодов нет (Task 442)');
    });
""", 'vm-sheet-codes')

# --- 3. Хост _printModel: без _printCodesData ---
rep("            methodText(WS_CLIENT, '_printEventsData') + ',' +\n"
    "            methodText(WS_CLIENT, '_printCodesData') + ',' +\n"
    "            '_year: 2026, _month: 9, _view: ' + JSON.stringify(opts.view || 'full') + ',' +",
    "            methodText(WS_CLIENT, '_printEventsData') + ',' +\n"
    "            '_year: 2026, _month: 9, _view: ' + JSON.stringify(opts.view || 'full') + ',' +",
    'host-model')

# --- 4. Хост Excel: _printCodesData → _wsTabelStyleMap ---
rep("            methodText(WS_CLIENT, '_printCodesData') + ',' +\n"
    "            methodText(WS_CLIENT, '_wsTabelStylesXml') + ',' +",
    "            methodText(WS_CLIENT, '_wsTabelStyleMap') + ',' +\n"
    "            methodText(WS_CLIENT, '_wsTabelStylesXml') + ',' +",
    'host-tabel')

# --- 5. VM раскладка PDF: без кодов ---
rep("""    test('VM: компактный месяц — ОДНА страница: таблица + события + коды', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(10, 3, 4));
        assertEqual(lay.pages.length, 1, 'всё на одной странице');
        const p = lay.pages[0];
        assertEqual(p.events.length, 3, 'события на ней же');
        assertEqual(p.codes.length, 4, 'коды на ней же (справа от событий)');
    });

    test('VM: ГРАНИЧНЫЙ случай — пара (max) влезает, сумма не влезала бы', () => {
        // A4-альбом: contentH = 595 − 2×23 = 549. Первая страница:
        // шапка 34 + gap 8 + лента 24 → 21 строка. При 22 строках
        // вторая страница: used = 24 + 22 + 8 = 54. 33 события:
        // evH = 18 + 33×13 = 447; cdH (4 кода, ОДИН столбец
        // Task 441) = 74. Прежняя сумма (447 + 8 + 74 = 529;
        // 54 + 529 = 583 > 549) не влезала — теперь пара =
        // max(447, 74) = 447; 54 + 447 = 501 ≤ 549:
        // события И коды — на последней странице таблицы
        const lay = layoutHost()._printPdfLayout(fakeModel(22, 33, 4));
        assertEqual(lay.pages.length, 2, '2 страницы (прежде было бы 3)');
        const last = lay.pages[1];
        assertEqual(last.rows.length, 1, 'вторая страница — последняя строка');
        assertEqual(last.events.length, 33, 'все события на ней');
        assertTrue(!!last.codes, 'коды РЯДОМ с событиями (Task 439: max, не сумма)');
    });

    test('VM: много событий — режутся, коды — с последним куском', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(60, 200, 4));
        const evPages = lay.pages.filter(p => p.events && p.rows.length === 0);
        assertTrue(evPages.length >= 2, '200 событий — несколько страниц');
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.codes, 'коды размещены (рядом с последним куском событий)');
        let evTotal = 0;
        for (const p of evPages) evTotal += p.events.length;
        assertEqual(evTotal, 200, 'все события распределены без потерь');
    });

    test('VM: тесная страница — коды отдельной страницей (не теряются)', () => {
        // низкая «страница» (H=300): пара событий+кодов не влезает —
        // коды уходят на собственную страницу
        const lay = layoutHost()._printPdfLayout(fakeModel(0, 100, 40), { H: 300 });
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.codes, 'коды — на последней странице');
        assertEqual(last.codes.length, 40, 'все 40 кодов (одной страницей)');
    });

    test('VM: раскладка несёт геометрию зон (codeW/colGap/evW)', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(2, 1, 2));
        assertEqual(lay.codeW, 235, 'ширина правой зоны кодов');
        // Task 440: зазор 10px = 7.5pt (1px = 0.75pt)
        assertEqual(lay.colGap, 7.5, 'зазор между мероприятиями и кодами — 7.5pt (= 10px)');
        assertEqual(lay.evW, lay.W - 2 * lay.M - 235 - 7.5,
            'левая зона мероприятий = остаток ширины');
        // переопределение зон через opts
        const lay2 = layoutHost()._printPdfLayout(fakeModel(2, 1, 2),
                                                  { codeW: 300, colGap: 20 });
        assertEqual(lay2.codeW, 300, 'codeW переопределяется opts');
        assertEqual(lay2.colGap, 20, 'colGap переопределяется opts');
    });

    test('VM: пустой месяц (0 строк, 0 событий) — заглушка + коды рядом', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(0, 0, 2));
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.events, 'события-заглушка размещены');
        assertTrue(!!last.codes, 'коды размещены');
    });
""",
    """    test('VM: компактный месяц — ОДНА страница: таблица + события', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(10, 3, 4));
        assertEqual(lay.pages.length, 1, 'всё на одной странице');
        const p = lay.pages[0];
        assertEqual(p.events.length, 3, 'события на ней же');
        assertTrue(!p.codes, 'кодов нет (Task 442: столбец удалён)');
    });

    test('VM: ГРАНИЧНЫЙ случай — события влезают под таблицей', () => {
        // A4-альбом: contentH = 595 − 2×23 = 549. Первая страница:
        // шапка 34 + gap 8 + лента 24 → 21 строка. При 22 строках
        // вторая страница: used = 24 + 22 + 8 = 54. 33 события:
        // evH = 18 + 33×13 = 447; 54 + 447 = 501 ≤ 549 — события
        // на последней странице таблицы (кодов больше нет, Task 442)
        const lay = layoutHost()._printPdfLayout(fakeModel(22, 33, 4));
        assertEqual(lay.pages.length, 2, '2 страницы');
        const last = lay.pages[1];
        assertEqual(last.rows.length, 1, 'вторая страница — последняя строка');
        assertEqual(last.events.length, 33, 'все события на ней');
        assertTrue(!last.codes, 'кодов нет (Task 442)');
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
        assertEqual(evTotal, 200, 'все события распределены без потерь');
    });

    test('VM: тесная страница — события режутся, ничего не теряется', () => {
        // низкая «страница» (H=300): события не влезают под лентой —
        // уходят отдельными страницами (кодов больше нет, Task 442)
        const lay = layoutHost()._printPdfLayout(fakeModel(0, 100, 40), { H: 300 });
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.events, 'последняя страница — мероприятия');
        let evTotal = 0;
        for (const p of lay.pages) {
            if (p.events) evTotal += p.events.length;
        }
        assertEqual(evTotal, 100, 'все 100 событий распределены');
    });

    test('VM: раскладка — мероприятия на ВСЮ ширину (evW)', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(2, 1, 2));
        assertTrue(!('codeW' in lay), 'зоны кодов нет (Task 442)');
        assertTrue(!('colGap' in lay), 'зазора мероприятий↔коды нет');
        assertEqual(lay.evW, lay.W - 2 * lay.M,
            'зона мероприятий = вся ширина листа (без вычета кодов)');
    });

    test('VM: пустой месяц (0 строк, 0 событий) — заглушка', () => {
        const lay = layoutHost()._printPdfLayout(fakeModel(0, 0, 2));
        const last = lay.pages[lay.pages.length - 1];
        assertTrue(!!last.events, 'события-заглушка размещены');
        assertTrue(!last.codes, 'кодов нет (Task 442)');
    });
""", 'vm-layout')

# --- 6. SRC отрисовка PDF: зоны кодов нет ---
rep("""    test('SRC: коды — ПРАВАЯ зона (codeX), мероприятия — левая с переносом', () => {
        const b = stripComments(methodText(WS_CLIENT, '_printPdfPaintPage'));
        // Task 440: codeX — за фактическим краем текста мероприятий
        // (evRightMax + colGap, ограничен правым краем листа);
        // край листа остаётся ОГРАНИЧЕНИЕМ (x0 + CW - codeW в min)
        assertTrue(b.indexOf('codeX = Math.min(evRightMax + colGap,') !== -1 &&
                   b.indexOf('x0 + CW - codeW)') !== -1,
            'зона кодов: за текстом мероприятий, не правее края листа');
        assertTrue(b.indexOf("ctx.fillText('Коды:', codeX, y + 8)") !== -1,
            'заголовок «Коды:» рисуется в правой зоне');
        assertTrue(b.indexOf('var botY = y;') !== -1 &&
                   b.indexOf('y = botY;') !== -1,
            'общая верхняя линия блоков (botY)');
        assertTrue(b.indexOf('evMaxW') !== -1 && b.indexOf('evWords') !== -1,
            'текст мероприятий переносится по словам в левой зоне');
    });
""",
    """    test('SRC: зоны кодов нет, мероприятия — вся ширина (Task 442)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_printPdfPaintPage'));
        assertTrue(b.indexOf('codeX') === -1 && b.indexOf('evZoneW') === -1,
            'геометрии зон кодов (Task 439/440) нет — столбец удалён');
        assertTrue(b.indexOf("'Коды:'") === -1,
            'заголовка «Коды:» в PDF нет');
        assertTrue(b.indexOf('botY') === -1,
            'общей верхней линии пары блоков нет');
        assertTrue(b.indexOf('var evMaxW = x0 + CW - ex;') !== -1 &&
                   b.indexOf('evWords') !== -1,
            'текст мероприятий переносится по словам до края ЛИСТА');
    });
""", 'src-paint')

# --- 7. Excel: колонки C/D нет ---
rep("""    test('VM: коды — в колонке D на тех же строках, что мероприятия', () => {
        const host = tabelHost();
        const rows = host._wsTabelRows(host._printModel(EMPS, AGG), {});
        // строка-заголовок блока: A = «Мероприятия · …», D = «Коды:»
        let hdr = null;
        for (const r of rows) {
            if (r[0] && String(r[0].v).indexOf('Мероприятия · ') === 0) {
                hdr = r; break;
            }
        }
        assertTrue(hdr !== null, 'заголовок блока мероприятий найден');
        assertEqual(hdr.length, 4, 'строка заголовка: A + зазор C + D');
        assertEqual(hdr[3].v, 'Коды:', '«Коды:» — в колонке D (справа)');
        assertEqual(hdr[1], null, 'B в заголовке пуст (дата мероприятия ниже)');
        // первая строка данных блока: A = дата, B = текст, D = код
        const idx = rows.indexOf(hdr);
        const first = rows[idx + 1];
        assertEqual(first[0].v, '02.09', 'дата мероприятия в A');
        assertTrue(String(first[1].v).indexOf('И · Повторный инструктаж') === 0,
            'текст мероприятия в B');
        assertTrue(String(first[3].v).indexOf(' — ') !== -1 ||
                   String(first[3].v).length > 0,
            'код месяца — в колонке D той же строки');
    });

    test('VM: пустой месяц — заглушка в A, «Коды:» всё равно в D', () => {
        const host = tabelHost();
        host._TRAININGS = [];
        const rows = host._wsTabelRows(host._printModel(EMPS, AGG), {});
        let hdr = null;
        for (const r of rows) {
            if (r[0] && String(r[0].v).indexOf('Мероприятия · ') === 0) {
                hdr = r; break;
            }
        }
        const first = rows[rows.indexOf(hdr) + 1];
        assertEqual(first[0].v, 'нет мероприятий в этом месяце',
            'заглушка мероприятий в колонке A');
        assertEqual(hdr[3].v, 'Коды:', 'заголовок кодов — в D');
    });
""",
    """    test('VM: блок — только A/B, колонок C/D нет (Task 442)', () => {
        const host = tabelHost();
        const rows = host._wsTabelRows(host._printModel(EMPS, AGG), {});
        // строка-заголовок блока: A = «Мероприятия · …» (одна ячейка)
        let hdr = null;
        for (const r of rows) {
            if (r[0] && String(r[0].v).indexOf('Мероприятия · ') === 0) {
                hdr = r; break;
            }
        }
        assertTrue(hdr !== null, 'заголовок блока мероприятий найден');
        assertEqual(hdr.length, 1, 'заголовок — ОДНА ячейка (без «Коды:»)');
        // первая строка данных блока: A = дата, B = текст — и всё
        const idx = rows.indexOf(hdr);
        const first = rows[idx + 1];
        assertEqual(first[0].v, '02.09', 'дата мероприятия в A');
        assertTrue(String(first[1].v).indexOf('И · Повторный инструктаж') === 0,
            'текст мероприятия в B');
        assertTrue(first.length <= 2, 'правее B ячеек нет (Task 442)');
    });

    test('VM: пустой месяц — заглушка в A, кодов нет', () => {
        const host = tabelHost();
        host._TRAININGS = [];
        const rows = host._wsTabelRows(host._printModel(EMPS, AGG), {});
        let hdr = null;
        for (const r of rows) {
            if (r[0] && String(r[0].v).indexOf('Мероприятия · ') === 0) {
                hdr = r; break;
            }
        }
        const first = rows[rows.indexOf(hdr) + 1];
        assertEqual(first[0].v, 'нет мероприятий в этом месяце',
            'заглушка мероприятий в колонке A');
        assertEqual(hdr.length, 1, 'заголовка «Коды:» нет (Task 442)');
    });
""", 'vm-xlsx-block')

# --- 8. Excel: «Коды:» в D листа — удалено ---
rep("""    test('VM: «Коды:» в колонке D листа (заголовок справа от мероприятий)', () => {
        const wb = tabelHost()._buildTabelWorkbook(EMPS, AGG);
        const z = parseZip(wb.bytes);
        const sheet = Buffer.from(
            z.files.filter(f => f.name === 'xl/worksheets/sheet1.xml')[0].data)
            .toString('utf8');
        // Task 440: «Коды:» — стиль 8 (шапка + indent 1 — зазор
        // ~7px от текста мероприятий, Excel-эквивалент 10px)
        assertTrue(/<c r="D\\d+" t="inlineStr" s="8"><is><t>Коды:<\\/t><\\/is><\\/c>/
            .test(sheet), '«Коды:» — колонка D со стилем шапки и отступом');
        assertTrue(sheet.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий — колонка A той же строки');
    });
""",
    """    test('VM: «Коды:» в книге НЕТ (Task 442), мероприятия живы', () => {
        const wb = tabelHost()._buildTabelWorkbook(EMPS, AGG);
        const z = parseZip(wb.bytes);
        const sheet = Buffer.from(
            z.files.filter(f => f.name === 'xl/worksheets/sheet1.xml')[0].data)
            .toString('utf8');
        assertTrue(sheet.indexOf('>Коды:<') === -1,
            'секции «Коды:» в листе нет (столбец удалён, Task 442)');
        assertTrue(sheet.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий — колонка A');
    });
""", 'vm-xlsx-codeshdr')

io.open(P, 'w', encoding='utf-8').write(s)
print()
print('=== ИТОГ task442-adapt-439 ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ГОТОВО')
