#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: адаптация tests/test-task440.js — зазор 10px/indent-стили
# существовали для ПАРЫ мероприятий↔коды; блок кодов удалён —
# соответствующие SRC/VM тесты переработаны (Excel: база цветных 7,
# контуры выходных + regDate); хост +_wsTabelStyleMap.
import io

P = 'tests/test-task440.js'
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


# --- 1. SRC блок «зазор 10px» → снят вместе с блоком кодов ---
rep("""    test('HTML: .wsp-bottom — gap: 10px, прежнего 6mm нет', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-bottom');
        assertTrue(r !== '', 'правило обёртки есть');
        assertTrue(r.indexOf('gap: 10px') !== -1,
            'зазор между блоками ряда — ровно 10px');
        assertTrue(r.indexOf('gap: 6mm') === -1,
            'прежний зазор 6mm (Task 439) убран');
    });

    test('HTML: .wsp-mev — flex 0 1 auto (коды за ТЕКСТОМ, не у края)', () => {
        // Task 431 → 440: «сейчас между ними очень большое
        // расстояние» — flex-grow снят, блок кодов в 10px от правого
        // края текста мероприятий; длинные тексты переносятся
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        assertTrue(r !== '', 'правило мероприятий есть');
        assertTrue(r.indexOf('flex: 0 1 auto') !== -1,
            'мероприятия НЕ растягиваются (Task 440, было 1 1 auto)');
        assertTrue(r.indexOf('flex: 1 1 auto') === -1,
            'растяжение на остаток ширины убрано');
        assertTrue(r.indexOf('min-width: 0') !== -1,
            'усадка для переносов текста жива (Task 439)');
    });

    test('PDF: _printPdfLayout — colGap по умолчанию 7.5pt (= 10px)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_printPdfLayout'));
        assertTrue(fn.indexOf('var colGap = opts.colGap || 7.5;') !== -1,
            '10 CSS-px = 7.5pt (1px = 0.75pt)');
        assertTrue(fn.indexOf('|| 12') === -1, 'прежний зазор 12pt убран');
    });

    test('PDF: _printPdfPaintPage — фолбэк colGap 7.5pt + коды за текстом', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_printPdfPaintPage'));
        assertTrue(fn.indexOf('var colGap = lay.colGap || 7.5;') !== -1,
            'зазор зон отрисовки — 7.5pt');
        // Task 440: блок кодов — за ФАКТИЧЕСКИМ правым краем строк
        // мероприятий (evRightMax + colGap), не прижат к правому
        // краю листа; ограничение — край листа; без мероприятий —
        // от левого края (+colGap)
        assertTrue(fn.indexOf('var evRightMax = 0;') !== -1,
            'край строк мероприятий отслеживается');
        assertTrue(fn.indexOf('codeX = Math.min(evRightMax + colGap,') !== -1,
            'кодX = min(край текста + 7.5pt, правый край листа)');
        assertTrue(fn.indexOf('var codeX = x0 + colGap;') !== -1,
            'страницы без мероприятий — коды от левого края (+colGap)');
    });

    test('Excel: стили — ДВА новых xf с indent="1" (код-строка + «Коды:»)', () => {
        const st = methodText(INDEX_SRC, '_wsTabelStylesXml');
        const code = st.indexOf('<alignment horizontal="left" indent="1"/></xf>');
        const head = st.indexOf('<alignment horizontal="left" indent="1"/></xf>', code + 1);
        assertTrue(code !== -1, 'стиль код-строки (базовый шрифт + indent)');
        assertTrue(head !== -1, 'стиль заголовка «Коды:» (шапка + indent)');
        // стиль «Коды:» — как s=1 (bold/заливка) ПЛЮС отступ
        const headXf = st.slice(st.lastIndexOf('<xf', head), head + 31);
        assertTrue(headXf.indexOf('fontId="1"') !== -1 &&
                   headXf.indexOf('fillId="2"') !== -1,
            'шапка «Коды:» — тот же вид, что «Мероприятия», + отступ');
        assertTrue(st.indexOf('(9 + colors.length)') !== -1,
            'cellXfs count = 9 + colors (было 7 + colors)');
    });

    test('Excel: строки — «Коды:» s:8, код-строки s:7, сетка 9+idx', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_wsTabelRows'));
        assertTrue(fn.indexOf("{ v: 'Коды:', s: 8 }") !== -1,
            'заголовок «Коды:» — стиль 8 (шапка + indent)');
        assertTrue(fn.indexOf('{ v: codeLines[b], s: 7 }') !== -1,
            'строки кодов — стиль 7 (indent, зазор от мероприятий)');
        assertTrue(fn.indexOf('st = 9 + colorIdx[col];') !== -1,
            'цветные ячейки сетки — стили 9+idx (7/8 заняты кодами)');
        assertFalse(fn.indexOf('st = 7 + colorIdx[col];') !== -1,
            'прежняя база цветных стилей 7 убрана');
    });
""",
    """    test('HTML: .wsp-bottom — БЕЗ ряда/зазора (Task 442: кодов нет)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-bottom');
        assertTrue(r !== '', 'правило обёртки есть');
        assertTrue(r.indexOf('gap') === -1,
            'зазора нет — блок кодов удалён (Task 442), ряда больше нет');
        assertTrue(r.indexOf('display: flex') === -1,
            'flex-ряд снят вместе с блоком кодов');
    });

    test('HTML: .wsp-mev — вся ширина листа (Task 442)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        assertTrue(r !== '', 'правило мероприятий есть');
        assertTrue(r.indexOf('flex:') === -1,
            'ограничений зоны нет — кодов справа больше нет');
        assertTrue(r.indexOf('min-width') === -1,
            'усадка зоны снята (зоны больше нет)');
    });

    test('PDF: _printPdfLayout — зоны кодов НЕТ (Task 442)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_printPdfLayout'));
        assertTrue(fn.indexOf('colGap') === -1,
            'зазора мероприятий↔коды нет — пара блоков не существует');
        assertTrue(fn.indexOf('codeW') === -1,
            'ширины зоны кодов нет');
        assertTrue(fn.indexOf('var evW = W - 2 * M;') !== -1,
            'мероприятия — вся ширина листа');
    });

    test('PDF: _printPdfPaintPage — зон кодов НЕТ (Task 442)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_printPdfPaintPage'));
        assertTrue(fn.indexOf('colGap') === -1 && fn.indexOf('codeX') === -1,
            'геометрии пары блоков нет');
        assertTrue(fn.indexOf('evRightMax') === -1,
            'край текста мероприятий больше не трекается (кодов нет)');
        assertTrue(fn.indexOf('var evMaxW = x0 + CW - ex;') !== -1,
            'перенос текста — до правого края ЛИСТА');
    });

    test('Excel: стили — indent-стили кодов УДАЛЕНЫ (Task 442)', () => {
        const st = methodText(INDEX_SRC, '_wsTabelStylesXml');
        assertTrue(st.indexOf('indent="1"') === -1,
            'indent-стилей нет — столбца кодов больше нет');
        assertTrue(st.indexOf('(st.regDate + 1)') !== -1,
            'cellXfs count = regDate + 1 (карта _wsTabelStyleMap)');
        assertTrue(st.indexOf('count="13"') !== -1,
            '13 границ: thin + 11 medium-комбинаций контура выходных');
        assertTrue(st.indexOf('count="\\'' + 7 + '\''"') !== -1 ||
                   st.indexOf("count=\"' + 7 + '\"") !== -1,
            '7 шрифтов (+ НЕ жирные белые числа дат)');
    });

    test('Excel: строки — кодов нет, сетка 7+idx (Task 442)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_wsTabelRows'));
        assertTrue(fn.indexOf("'Коды:'") === -1,
            'заголовка «Коды:» нет');
        assertTrue(fn.indexOf('codeLines') === -1,
            'строк кодов нет');
        assertTrue(fn.indexOf('stMap.coloredBase + colorIdx[col]') !== -1,
            'цветные ячейки сетки — база 7 (indent-стили сняты)');
    });
""", 'src-gap-block')

# --- 2. VM Excel: хост + карта стилей; тесты без кодов ---
rep("""    function xlsHost() {
        return new Function('return ({' +
            methodText(INDEX_SRC, '_wsTabelStylesXml') + ',' +
            methodText(INDEX_SRC, '_wsTabelRows') +
            '});')();
    }
""",
    """    function xlsHost() {
        return new Function('return ({' +
            methodText(INDEX_SRC, '_wsTabelStyleMap') + ',' +
            methodText(INDEX_SRC, '_wsTabelStylesXml') + ',' +
            methodText(INDEX_SRC, '_wsTabelRows') +
            '});')();
    }
""", 'vm-xls-host')

rep("""    test('styles.xml: indent="1" ×2, cellXfs 9 + colors', () => {
        const xml = xlsHost()._wsTabelStylesXml(['FFE082']);
        assertEqual(xml.split('indent="1"').length - 1, 2,
            'ровно ДВА стиля с отступом (код-строка и «Коды:»)');
        assertTrue(xml.indexOf('<cellXfs count="10">') !== -1,
            '9 базовых + 1 цвет = 10 стилей (было 8)');
    });

    test('строки: сетка s9, «Коды:» s8, код-строка s7', () => {
        const rows = xlsHost()._wsTabelRows(MODEL, { FFE082: 0 });
        let grid = null, hdr = null, block = null;
        for (const r of rows) {
            if (r[0] && String(r[0].v).indexOf('Иванов') === 0) grid = r;
            if (r[0] && String(r[0].v).indexOf('Мероприятия · ') === 0) hdr = r;
        }
        const hi = rows.indexOf(hdr);
        block = rows[hi + 1];
        assertTrue(grid !== null && hdr !== null && block !== null,
            'строки найдены');
        assertEqual(9, grid[1].s, 'цветная ячейка сетки — стиль 9 (база сдвинута)');
        assertEqual(4, grid[2].s, 'пустая ячейка сетки — стиль 4 (без цвета)');
        assertEqual(8, hdr[3].s, '«Коды:» — стиль 8 (шапка + indent)');
        assertEqual('Коды:', hdr[3].v, 'заголовок кодов в D');
        assertEqual(7, block[3].s, 'строка кода — стиль 7 (indent)');
        assertEqual('Д — День', block[3].v, 'код месяца в D');
    });
""",
    """    test('styles.xml: БЕЗ indent, контуры выходных + regDate (Task 442)', () => {
        const xml = xlsHost()._wsTabelStylesXml(['FFE082']);
        assertEqual(xml.split('indent="1"').length - 1, 0,
            'indent-стилей НЕТ — столбца кодов больше нет');
        // карта: 7 + C + 4 + 3 + 7 + 7C + 1 = 22 + 8C; C=1 → 30
        assertTrue(xml.indexOf('<cellXfs count="30">') !== -1,
            'cellXfs count = 30 (база 0–6 + цветной + контуры + regDate)');
        assertTrue(xml.split('style="medium"').length - 1 > 20,
            'medium-границы контуров выходных построены');
        assertTrue(xml.indexOf('<fonts count="7">') !== -1,
            '7 шрифтов (+ НЕ жирные белые числа дат)');
        assertTrue(xml.indexOf('<borders count="13">') !== -1,
            '13 границ (thin + 11 комбинаций контура)');
    });

    test('строки: сетка s7, блока кодов нет (Task 442)', () => {
        const rows = xlsHost()._wsTabelRows(MODEL, { FFE082: 0 });
        let grid = null, hdr = null, block = null;
        for (const r of rows) {
            if (r[0] && String(r[0].v).indexOf('Иванов') === 0) grid = r;
            if (r[0] && String(r[0].v).indexOf('Мероприятия · ') === 0) hdr = r;
        }
        const hi = rows.indexOf(hdr);
        block = rows[hi + 1];
        assertTrue(grid !== null && hdr !== null && block !== null,
            'строки найдены');
        assertEqual(7, grid[1].s,
            'цветная ячейка сетки — стиль 7 (база цветных, Task 442)');
        assertEqual(4, grid[2].s, 'пустая ячейка сетки — стиль 4 (без цвета)');
        assertEqual(1, hdr.length, 'заголовок блока — одна ячейка A (без «Коды:»)');
        assertEqual(block.length, 2, 'строка блока — A (дата) + B (текст)');
        assertEqual('01.09', block[0].v, 'дата мероприятия в A');
        assertEqual('Плановое обслуживание', block[1].v, 'текст мероприятия в B');
    });
""", 'vm-xlsx-tests')

io.open(P, 'w', encoding='utf-8').write(s)
print()
print('=== ИТОГ task442-adapt-440 ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ГОТОВО')
