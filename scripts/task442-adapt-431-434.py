#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: адаптация tests/test-task431/432/433/434 — легенда кодов
# и flex-ряд нижней секции печати удалены (Task 442); мероприятия —
# единственная секция на всю ширину.
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
# test-task431.js
# ============================================================
adapt('tests/test-task431.js', [
    ("""    test('.wsp-mev: ЛЕВАЯ часть ряда — flex 0 1 auto (Task 431 → 440)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-mev {');
        assertTrue(i !== -1, 'правило .wsp-mev есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        // Task 440 (заявка: «коды справа от мероприятий на
        // расстоянии друг от друга 10px» — как в 431 «сейчас между
        // ними очень большое расстояние»): flex-grow СНЯТ (Task 439
        // временно вернул 1 1 auto) — коды встают в 10px от ПРАВОГО
        // КРАЯ ТЕКСТА мероприятий; перенос длинных текстов жив
        // (flex-shrink + min-width: 0)
        assertTrue(r.indexOf('flex: 0 1 auto') !== -1,
            'мероприятия НЕ растягиваются — коды за текстом (Task 440)');
        assertTrue(r.indexOf('min-width: 0') !== -1,
            'min-width — усадка для переносов текста');
    });

    test('.wsp-legend: коды — ПРАВЫЙ блок ряда (Task 439)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-legend {');
        assertTrue(i !== -1, 'правило кодов есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): коды — ПРАВАЯ часть flex-ряда фикс. ширины
        assertTrue(r.indexOf('float:') === -1,
            'флоат не вернулся (коды — не плавающий столбик)');
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'фиксированная ширина блока кодов (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'отступ строки кодов от списка мероприятий сверху');
    });

    test('wsp-foot удалена; закрытия секций — три оператора подряд (Task 438)', () => {
        // Task 438 (заявка: «нижний текст убери»): сноска wsp-foot
        // УДАЛЕНА — но структура секций не изменилась
        const f = INDEX_SRC.indexOf("html += '<div class=\\"wsp-foot\\">");
        assertTrue(f === -1, 'сноска wsp-foot не строится (Task 438)');
        const iLegend = INDEX_SRC.indexOf("html += '<div class=\\"wsp-legend\\">");
        assertTrue(iLegend !== -1, 'легенда кодов строится');
        // Task 434 жив: закрытия сетки-колонок, легенды и обёртки —
        // ТРИ последовательных оператора (сноска шла после них)
        const close1 = INDEX_SRC.indexOf("html += '</div>';", iLegend);
        const close2 = INDEX_SRC.indexOf("html += '</div>';", close1 + 1);
        const close3 = INDEX_SRC.indexOf("html += '</div>';", close2 + 1);
        assertTrue(close1 !== -1 && close2 !== -1 && close3 !== -1 &&
                   close2 - close1 < 200 && close3 - close2 < 200,
            'закрытия сетки/легенды/обёртки — подряд (Task 434 жив)');
        const open = INDEX_SRC.lastIndexOf("html += '<div class=\\"wsp-bottom\\">'", iLegend);
        assertTrue(open !== -1 && open < iLegend,
            'обёртка wsp-bottom открывается раньше секций');
        // внутри обёртки — ОБА блока: мероприятия + коды
        const wrap = INDEX_SRC.slice(open, close3);
        assertTrue(wrap.indexOf('wsp-mev') !== -1 && wrap.indexOf('wsp-legend') !== -1,
            'в обёртке — список мероприятий и перечень кодов');
    });
""",
     """    test('.wsp-mev: без ограничений — вся ширина листа (Task 442)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-mev {');
        assertTrue(i !== -1, 'правило .wsp-mev есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        // Task 442: столбца кодов справа больше нет — ограничения
        // зоны мероприятий (flex/min-width из Tasks 439/440) сняты
        assertTrue(r.indexOf('flex:') === -1,
            'flex-ограничений нет (кодов справа больше нет, Task 442)');
        assertTrue(r.indexOf('min-width') === -1,
            'усадки зоны нет (зоны больше нет)');
    });

    test('.wsp-legend: правило УДАЛЕНО (Task 442)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-legend {');
        assertTrue(i === -1,
            'правила .wsp-legend нет — блок кодов удалён (Task 442)');
        assertTrue(INDEX_SRC.indexOf('#wsPrintSheet .wsp-lg {') === -1,
            'правила .wsp-lg тоже нет');
    });

    test('wsp-foot удалена; секция одна — мероприятия (Task 442)', () => {
        // Task 438 (заявка: «нижний текст убери»): сноска wsp-foot
        // УДАЛЕНА; Task 442: легенда кодов удалена — в обёртке
        // осталась единственная секция мероприятий
        const f = INDEX_SRC.indexOf("html += '<div class=\\"wsp-foot\\">");
        assertTrue(f === -1, 'сноска wsp-foot не строится (Task 438)');
        const iLegend = INDEX_SRC.indexOf("html += '<div class=\\"wsp-legend\\">");
        assertTrue(iLegend === -1,
            'легенда кодов НЕ строится (Task 442)');
        const iMev = INDEX_SRC.indexOf("html += '<div class=\\"wsp-mev\\">");
        assertTrue(iMev !== -1, 'секция мероприятий строится');
        const open = INDEX_SRC.lastIndexOf("html += '<div class=\\"wsp-bottom\\">'", iMev);
        assertTrue(open !== -1 && open < iMev,
            'обёртка wsp-bottom открывается раньше секции');
        // закрытие секции и обёртки — два последовательных оператора
        const close1 = INDEX_SRC.indexOf("html += '</div>';", iMev);
        const close2 = INDEX_SRC.indexOf("html += '</div>';", close1 + 1);
        assertTrue(close1 !== -1 && close2 !== -1 && close2 - close1 < 200,
            'закрытия секции/обёртки — подряд');
        const wrap = INDEX_SRC.slice(open, close2);
        assertTrue(wrap.indexOf('wsp-mev') !== -1 && wrap.indexOf('wsp-legend') === -1,
            'в обёртке — только список мероприятий (Task 442)');
    });
""", 'print-431'),
])

# ============================================================
# test-task432.js
# ============================================================
adapt('tests/test-task432.js', [
    ("""    test('.wsp-legend — ПРАВЫЙ блок ряда, БЕЗ флоата (Task 439)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend {');
        assertTrue(r !== '', 'правило кодов есть');
        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): коды — ПРАВАЯ часть flex-ряда (заявка
        // Task 433 «под списком» снята); Task 434: заголовок
        // «Коды:» + сетка-две-колонки
        assertTrue(r.indexOf('float:') === -1,
            'флоат Task 432 не вернулся (коды — не плавающий столбик)');
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'блок кодов — фикс. ширина 92mm справа (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'верхняя линия общая с мероприятиями (Task 439)');
        assertTrue(r.indexOf('max-width') === -1,
            'кап ширины Task 364 не вернулся');
        // Task 434: две колонки; Task 441 — ОДНА колонка
        const c = ruleBlock('#wsPrintSheet .wsp-legend-cols {');
        assertTrue(c.indexOf('display: grid') !== -1 &&
                   c.indexOf('grid-template-columns: 1fr') !== -1,
            'Task 441: сетка-ОДНА-КОЛОНКА (прежде ДВЕ, Task 434)');
        const lg = ruleBlock('#wsPrintSheet .wsp-lg {');
        assertTrue(lg.indexOf('display: block') !== -1,
            'Task 434: каждый код — своя строка колонки');
        assertTrue(lg.indexOf('white-space: normal') !== -1,
            'Task 434: длинное наименование переносится внутри колонки');
    });

    test('.wsp-mev — ЛЕВАЯ часть ряда (flex 0 1 auto, Task 440)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-mev {');
        assertTrue(r !== '', 'правило мероприятий есть');
        // Task 440: flex-grow снят — коды в 10px от ТЕКСТА
        // мероприятий (семантика Task 431), не у правого края листа
        assertTrue(r.indexOf('flex: 0 1 auto') !== -1,
            'мероприятия НЕ растягиваются (Task 440)');
        assertTrue(r.indexOf('min-width: 0') !== -1,
            'min-width — усадка для переносов текста (Task 439)');
    });
""",
     """    test('.wsp-legend — правило УДАЛЕНО (Task 442)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend {');
        assertTrue(r === '',
            'правила .wsp-legend нет — блок кодов удалён (Task 442)');
        assertTrue(ruleBlock('#wsPrintSheet .wsp-legend-cols {') === '' &&
                   ruleBlock('#wsPrintSheet .wsp-lg {') === '',
            'правил сетки/записей кодов нет (Task 442)');
    });

    test('.wsp-mev — без ограничений зоны (Task 442)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-mev {');
        assertTrue(r !== '', 'правило мероприятий есть');
        // Task 442: кодов справа нет — мероприятия на всю ширину
        assertTrue(r.indexOf('flex:') === -1,
            'flex-ограничений нет (зона снята, Task 442)');
        assertTrue(r.indexOf('min-width') === -1,
            'усадка зоны снята');
    });
""", 'print-432-css'),

    ("""    test('JS: мероприятия ПЕРВЫМИ, коды — ПОД ними (Task 433)', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        assertTrue(iOpen !== -1 && iLegend !== -1 && iMev !== -1,
            'обёртка, мероприятия и коды строятся');
        // Task 433: флоат снят — порядок DOM прямой: мероприятия,
        // за ними коды (в Task 432 коды строились первыми)
        assertTrue(iOpen < iMev && iMev < iLegend,
            'порядок: обёртка → мероприятия → коды (вертикальная секция)');
    });

    test('JS: закрытие кодов и обёртки — два оператора (сноски нет)', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        const iClose1 = b.indexOf("html += '</div>';", b.indexOf('<div class="wsp-legend">'));
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
        assertTrue(iClose1 !== -1 && iClose2 !== -1,
            'закрытия кодов и обёртки строятся');
        assertTrue(iClose2 - iClose1 < 200,
            'два последовательных оператора закрытия (legend + обёртка)');
    });
""",
     """    test('JS: секция одна — мероприятия (Task 442)', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        assertTrue(iOpen !== -1 && iMev !== -1,
            'обёртка и секция мероприятий строятся');
        // Task 442: флоат/ряд/абзац — история; легенды больше нет
        assertTrue(iOpen < iMev, 'порядок: обёртка → мероприятия');
        assertTrue(iLegend === -1, 'секции кодов НЕТ (Task 442)');
    });

    test('JS: закрытие секции и обёртки — два оператора (Task 442)', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        const iClose1 = b.indexOf("html += '</div>';", b.indexOf('<div class="wsp-mev">'));
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
        assertTrue(iClose1 !== -1 && iClose2 !== -1,
            'закрытия секции и обёртки строятся');
        assertTrue(iClose2 - iClose1 < 200,
            'два последовательных оператора закрытия (mev + обёртка)');
    });
""", 'print-432-js'),
])

# ============================================================
# test-task433.js
# ============================================================
adapt('tests/test-task433.js', [
    ("""    test('.wsp-legend — ПРАВЫЙ блок ряда (Task 439: справа от мероприятий)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend {');
        assertTrue(r !== '', 'правило кодов есть');
        assertTrue(r.indexOf('float') === -1,
            'флоат Task 432 не вернулся');
        assertTrue(r.indexOf('max-width') === -1,
            'кап ширины Task 364 не вернулся');
        // Task 439: коды — СПРАВА от мероприятий (фикс. ширина,
        // общая верхняя линия), прежний отступ «под списком» снят
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'фиксированная ширина блока кодов (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'верхняя линия общая с мероприятиями (Task 439)');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) жив');
    });

    test('.wsp-lg — коды в ДВЕ КОЛОНКИ под заголовком (Task 434)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-lg {');
        assertTrue(r !== '', 'правило кода есть');
        // Task 434 (заявка: «коды на печати сделать в две колонки
        // под названием "Коды:"»): строка-абзац Task 433 и столбик
        // Task 360–431 сняты — сетка-две-колонки .wsp-legend-cols
        assertTrue(r.indexOf('display: block') !== -1,
            'каждый код — своя строка колонки');
        assertTrue(r.indexOf('white-space: normal') !== -1,
            'длинное наименование переносится ВНУТРИ колонки');
        assertTrue(r.indexOf('break-inside: avoid') !== -1,
            'запись кода не рвётся между колонками/страницами');
        const t = ruleBlock('#wsPrintSheet .wsp-legend-t {');
        assertTrue(t.indexOf('display: block') !== -1,
            'заголовок «Коды:» — отдельной строкой СВЕРХУ сетки');
        const c = ruleBlock('#wsPrintSheet .wsp-legend-cols {');
        assertTrue(c.indexOf('grid-template-columns: 1fr') !== -1,
            'одна колонка на всю ширину блока кодов (Task 441)');
        assertFalse(r.indexOf('display: inline') !== -1,
            'инлайн-строка Task 433 снята');
    });

    test('JS: порядок секции — мероприятия, ЗА НИМИ коды (Task 434: + сетка)', () => {
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1 && iMev !== -1 && iLegend !== -1,
            'все секции строятся');
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
        assertTrue(iOpen < iMev && iMev < iLegend,
            'порядок: обёртка → МЕРОПРИЯТИЯ → КОДЫ (Task 433)');
        // Task 434: заголовок «Коды:» и СЕТКА-ДВЕ-КОЛОНКИ открываются
        // сразу за легендой
        const iCols = b.indexOf('<div class="wsp-legend-cols">');
        assertTrue(iCols !== -1 && iLegend < iCols,
            'Task 434: сетка .wsp-legend-cols внутри легенды');
        const iClose1 = b.indexOf("html += '</div>';", iLegend);
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        const iClose3 = b.indexOf("html += '</div>';", iClose2 + 1);
        assertTrue(iClose1 !== -1 && iClose2 !== -1 && iClose3 !== -1 &&
                   iClose2 - iClose1 < 200 && iClose3 - iClose2 < 200,
            'Task 434: закрытия сетки, легенды и обёртки — три последовательных оператора');
    });
""",
     """    test('.wsp-legend/.wsp-lg — правила УДАЛЕНЫ (Task 442)', () => {
        assertTrue(ruleBlock('#wsPrintSheet .wsp-legend {') === '',
            'правила .wsp-legend нет (Task 442: столбец кодов удалён)');
        assertTrue(ruleBlock('#wsPrintSheet .wsp-lg {') === '' &&
                   ruleBlock('#wsPrintSheet .wsp-legend-t {') === '' &&
                   ruleBlock('#wsPrintSheet .wsp-legend-cols {') === '',
            'правил заголовка/сетки/записей кодов нет');
    });

    test('JS: секция одна — мероприятия (Task 442)', () => {
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1 && iMev !== -1,
            'обёртка и секция мероприятий строятся');
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
        assertTrue(iOpen < iMev, 'порядок: обёртка → МЕРОПРИЯТИЯ');
        assertTrue(b.indexOf('wsp-legend') === -1,
            'секции кодов нет (Task 442)');
    });
""", 'print-433'),
])

# ============================================================
# test-task434.js
# ============================================================
adapt('tests/test-task434.js', [
    ("""    test('.wsp-legend-t — заголовок «Коды:» отдельной строкой', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend-t {');
        assertTrue(r !== '', 'правило заголовка есть');
        assertTrue(r.indexOf('display: block') !== -1,
            'заголовок — своя строка СВЕРХУ сетки кодов');
        assertTrue(r.indexOf('font-weight: 700') !== -1,
            'заголовок жирный (как прежде)');
        assertTrue(r.indexOf('margin-bottom') !== -1,
            'отступ заголовка от сетки кодов');
    });

    test('.wsp-legend-cols — сетка ОДНА колонка (Task 441)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend-cols {');
        assertTrue(r !== '', 'правило сетки есть');
        assertTrue(r.indexOf('display: grid') !== -1,
            'контейнер — grid');
        // Task 441 (заявка: «коды сделай в один столбец»):
        // ОДНА колонка — прежде ДВЕ равные (Task 434)
        assertTrue(r.indexOf('grid-template-columns: 1fr') !== -1,
            'ОДНА колонка на всю ширину блока кодов');
        assertFalse(r.indexOf('grid-template-columns: 1fr 1fr') !== -1,
            'две равные колонки Task 434 сняты (Task 441)');
        assertFalse(r.indexOf('column-gap') !== -1,
            'column-gap снят — колонок больше нет (Task 441)');
        assertTrue(r.indexOf('row-gap') !== -1,
            'вертикальный зазор между записями');
    });

    test('.wsp-lg — запись кода своей строкой колонки', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-lg {');
        assertTrue(r !== '', 'правило записи есть');
        assertTrue(r.indexOf('display: block') !== -1,
            'каждый код — своя строка колонки');
        assertTrue(r.indexOf('white-space: normal') !== -1,
            'длинное наименование переносится ВНУТРИ колонки');
        assertTrue(r.indexOf('break-inside: avoid') !== -1 &&
                   r.indexOf('page-break-inside: avoid') !== -1,
            'запись не рвётся между колонками и страницами');
        assertTrue(r.indexOf('min-width: 0') !== -1,
            'усадка при переполнении разрешена');
        assertFalse(r.indexOf('white-space: nowrap') !== -1,
            'nowrap Task 433 снят (строка-абзац больше не нужна)');
        assertFalse(r.indexOf('display: inline') !== -1,
            'инлайн-строка Task 433 снята');
    });

    test('.wsp-legend — без флоата и капа (регресс 432/433)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-legend {');
        assertTrue(r !== '', 'правило легенды есть');
        assertTrue(r.indexOf('float') === -1,
            'флоат Task 432 не вернулся');
        assertTrue(r.indexOf('max-width') === -1,
            'кап ширины Task 364 не вернулся');
        // Task 439: коды — ПРАВЫЙ блок ряда (справа от
        // мероприятий), верхняя линия общая — отступа сверху нет
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'фиксированная ширина блока кодов (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'верхняя линия общая с мероприятиями (Task 439)');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) жив');
    });
""",
     """    test('правила легенды кодов УДАЛЕНЫ (Task 442)', () => {
        // Task 442 (заявка: «убери … столбец с кодами»): вся
        // легенда (заголовок, сетка, записи) снята из печати
        assertTrue(ruleBlock('#wsPrintSheet .wsp-legend-t {') === '',
            'правила .wsp-legend-t нет');
        assertTrue(ruleBlock('#wsPrintSheet .wsp-legend-cols {') === '',
            'правила .wsp-legend-cols нет');
        assertTrue(ruleBlock('#wsPrintSheet .wsp-lg {') === '',
            'правила .wsp-lg нет');
        assertTrue(ruleBlock('#wsPrintSheet .wsp-legend {') === '',
            'правила .wsp-legend нет');
    });
""", 'print-434-css'),

    ("""    test('JS: «Коды:» + сетка в DOM, три последовательных закрытия', () => {
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iTitle = b.indexOf('<span class="wsp-legend-t">Коды:</span>');
        const iCols = b.indexOf('<div class="wsp-legend-cols">');
        assertTrue(iLegend !== -1 && iTitle !== -1 && iCols !== -1,
            'легенда, заголовок «Коды:» и сетка строятся');
        assertTrue(iLegend < iTitle && iTitle < iCols,
            'порядок: легенда → заголовок «Коды:» → сетка-колонки');
        const iClose1 = b.indexOf("html += '</div>';", iCols);
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        const iClose3 = b.indexOf("html += '</div>';", iClose2 + 1);
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iClose1 !== -1 && iClose2 !== -1 && iClose3 !== -1 &&
                   iClose2 - iClose1 < 200 && iClose3 - iClose2 < 200,
            'закрытия сетки, легенды и обёртки — три последовательных оператора');
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
    });
""",
     """    test('JS: легенды в DOM НЕТ — секция мероприятий одна (Task 442)', () => {
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        assertTrue(b.indexOf('<div class="wsp-legend">') === -1,
            'легенда не строится (Task 442)');
        assertTrue(b.indexOf('Коды:') === -1,
            'заголовка «Коды:» нет');
        assertTrue(b.indexOf('wsp-legend-cols') === -1,
            'сетки колонок нет');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
        // закрытие секции мероприятий + обёртки — два оператора
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iClose1 = b.indexOf("html += '</div>';", iMev);
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iClose1 !== -1 && iClose2 !== -1 && iClose2 - iClose1 < 200,
            'закрытия секции/обёртки — подряд');
    });
""", 'print-434-js'),
])

print()
print('=== ИТОГ adapt-431-434 ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ГОТОВО')
