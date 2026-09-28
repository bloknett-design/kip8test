#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: адаптация tests/test-task360/361/362/364/375/387/388 —
# бейджи печати удалены, серая заливка выходных снята, легенда
# кодов удалена (usedCodes/legacy/wsp-lg/«Коды:» не существуют).
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
# test-task360.js
# ============================================================
adapt('tests/test-task360.js', [
    ("""    test('SRC: порядок секций — таблица → обёртка(мероприятия→коды)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iTable = b.indexOf("'</tbody></table>'");
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iTable !== -1 && iMev !== -1 && iLegend !== -1,
            'все секции на месте');
        assertTrue(iFoot === -1, 'сноски wsp-foot нет (Task 438)');
        assertTrue(iTable < iMev, 'мероприятия ПОД графиком');
        // Task 433 (заявка: «расположение кодов в печати верни
        // обратно»): нижняя секция снова ВЕРТИКАЛЬНАЯ — список
        // мероприятий ПЕРВЫМ, коды — строкой-абзацем ПОД ним
        // (флоат Task 432 строил коды первыми в DOM)
        assertTrue(iMev < iLegend, 'перечень кодов — ПОД списком мероприятий'
            + ' (Task 433: вертикальная секция, флоат снят)');
        // Task 438: сноски после кодов больше нет — лист заканчивается
        // перечнем кодов
    });
""",
     """    test('SRC: порядок секций — таблица → обёртка(мероприятия)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iTable = b.indexOf("'</tbody></table>'");
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iTable !== -1 && iMev !== -1,
            'таблица и секция мероприятий на месте');
        assertTrue(iFoot === -1, 'сноски wsp-foot нет (Task 438)');
        assertTrue(iTable < iMev, 'мероприятия ПОД графиком');
        // Task 442: перечень кодов УДАЛЁН — секция одна, лист
        // заканчивается списком мероприятий
        assertTrue(b.indexOf('wsp-legend') === -1,
            'легенды кодов нет (Task 442: столбец удалён)');
    });
""", 'порядок-секций'),

    ("""    test('SRC: usedCodes собирается по эффективным записям строк', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('var usedCodes = {}') !== -1,
            'карта кодов месяца');
        assertTrue(b.indexOf("usedCodes[effEntry['статус']]") !== -1,
            'код отмечается по эффективной записи ячейки');
    });

    test('SRC: легенда фильтруется по usedCodes, порядок — справочник', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iFilter = b.indexOf('if (!usedCodes[codes[ci].code])');
        const iWykh = b.indexOf("!(codes[ci].code === '' && usedCodes['.'])");
        const iLoop = b.indexOf('for (var ci = 0; ci < codes.length; ci++)');
        assertTrue(iFilter !== -1, 'коды вне месяца пропускаются');
        assertTrue(iWykh !== -1, 'Task 387: легаси-«.» раскрывается строкой «Выходного»');
        assertTrue(iLoop !== -1 && iFilter > iLoop,
            'фильтр внутри цикла справочника (порядок = справочник)');
    });

    test('SRC: легаси-код вне справочника — в конце, без цвета/имени', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('var legacy = [];') !== -1,
            'список легаси-кодов');
        assertTrue(b.indexOf('legacy.sort()') !== -1,
            'легаси сортируются');
        const iLegacy = b.indexOf('var legacy = [];');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        assertTrue(iLegacy > iLegend, 'легаси добавляются ПОСЛЕ кодов справочника');
    });
""",
     """    test('SRC: usedCodes и легенда УДАЛЕНЫ (Task 442)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('var usedCodes = {}') === -1,
            'карты кодов месяца нет — перечню некуда собираться');
        assertTrue(b.indexOf('var legacy = [];') === -1,
            'легаси-кодов нет');
        assertTrue(b.indexOf('wsp-lg') === -1,
            'записей легенды нет');
    });
""", 'usedcodes-легенда'),

    ("""    test('SRC: .wsp-lg — коды в ДВЕ КОЛОНКИ (Task 434: под названием «Коды:»)', () => {
        const block = printCss();
        const i = block.indexOf('#wsPrintSheet .wsp-lg {');
        assertTrue(i !== -1, 'правило .wsp-lg есть');
        const rule = block.slice(i, block.indexOf('}', i) + 1);
        // Task 434 (заявка: «коды на печати сделать в две колонки
        // под названием "Коды:"»): заголовок «Коды:» — отдельной
        // строкой СВЕРХУ, под ним сетка-ДВЕ-КОЛОНКИ .wsp-legend-cols
        // (grid 1fr 1fr) на всю ширину листа; каждая запись-код —
        // своя строка колонки, длинное наименование переносится
        // ВНУТРИ своей колонки (строка Task 433 и столбик Task 360–431
        // сняты)
        const t = block.indexOf('#wsPrintSheet .wsp-legend-t {');
        assertTrue(t !== -1, 'правило заголовка .wsp-legend-t есть');
        const tRule = block.slice(t, block.indexOf('}', t) + 1);
        assertTrue(tRule.indexOf('display: block') !== -1,
            'заголовок «Коды:» — отдельной строкой сверху');
        const c = block.indexOf('#wsPrintSheet .wsp-legend-cols {');
        assertTrue(c !== -1, 'правило сетки .wsp-legend-cols есть');
        const cRule = block.slice(c, block.indexOf('}', c) + 1);
        assertTrue(cRule.indexOf('display: grid') !== -1 &&
                   cRule.indexOf('grid-template-columns: 1fr') !== -1,
            'одна колонка на всю ширину блока кодов (Task 441)');
        assertTrue(rule.indexOf('display: block') !== -1,
            'каждый код — своя строка колонки (не инлайн)');
        assertTrue(rule.indexOf('white-space: normal') !== -1,
            'длинное наименование переносится ВНУТРИ колонки');
        assertTrue(rule.indexOf('break-inside: avoid') !== -1,
            'запись кода не рвётся между колонками/страницами');
    });
""",
     """    test('SRC: правила легенды .wsp-lg/.wsp-legend-* УДАЛЕНЫ (Task 442)', () => {
        const block = printCss();
        assertTrue(block.indexOf('#wsPrintSheet .wsp-lg {') === -1,
            'правила .wsp-lg нет (столбец кодов удалён)');
        assertTrue(block.indexOf('#wsPrintSheet .wsp-legend-t {') === -1,
            'правила заголовка «Коды:» нет');
        assertTrue(block.indexOf('#wsPrintSheet .wsp-legend-cols {') === -1,
            'правила сетки кодов нет');
    });
""", 'wsp-lg-css'),

    ("""    function legendSection(html) {
        var i = html.indexOf('<div class="wsp-legend">');
        return html.slice(i, html.indexOf('</div>', i));
    }

    test('VM: только коды месяца — Д есть, Н/ОТ НЕ используются', () => {
        var entries = {
            '2026-09-02|017': { 'статус': 'Д' },
            '2026-09-03|031': { 'статус': 'Д' },
            '2026-09-04|017': { 'статус': '.' }
        };
        var html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('Д — День (12-час)') !== -1, 'код Д месяца');
        assertTrue(lg.indexOf('. — Плановый выходной') !== -1, 'код «.» месяца');
        assertTrue(lg.indexOf('Н — Ночь') === -1, 'неиспользуемый Н НЕ печатается');
        assertTrue(lg.indexOf('ОТ — Отпуск') === -1, 'неиспользуемый ОТ НЕ печатается');
    });
""",
     """    // Task 442: легенда кодов удалена — legendSection больше не
    // нужна; проверяем ОТСУТСТВИЕ перечня на листе
    test('VM: перечень кодов на листе НЕТ (Task 442)', () => {
        var entries = {
            '2026-09-02|017': { 'статус': 'Д' },
            '2026-09-03|031': { 'статус': 'Д' },
            '2026-09-04|017': { 'статус': '.' }
        };
        var html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('wsp-legend') === -1,
            'легенды кодов нет (столбец удалён, Task 442)');
        assertTrue(html.indexOf('Д — День (12-час)') === -1,
            'расшифровки кода Д нет');
        assertTrue(html.indexOf('Коды:') === -1, 'заголовка «Коды:» нет');
        assertTrue(html.indexOf('Мероприятия · ') !== -1,
            'список мероприятий жив (Task 360)');
    });
""", 'vm-только-коды'),

    ("""    test('VM: порядок кодов — как в справочнике', () => {
        var entries = {
            '2026-09-02|017': { 'статус': 'ОТ' },
            '2026-09-03|017': { 'статус': 'Н' },
            '2026-09-04|017': { 'статус': 'Д' }
        };
        var html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        var lg = legendSection(html);
        var iD = lg.indexOf('Д —');
        var iN = lg.indexOf('Н —');
        var iO = lg.indexOf('ОТ —');
        assertTrue(iD !== -1 && iN !== -1 && iO !== -1, 'все три кода месяца');
        assertTrue(iD < iN && iN < iO, 'порядок справочника: Д, Н, ОТ');
    });

    test('VM: локальная правка добавляет код, __delete убирает', () => {
        var entries = { '2026-09-02|017': { 'статус': 'Д' } };
        // правка 03.09 → ОТ (код появляется), удаление 02.09 (код Д исчезает)
        var pending = {
            '2026-09-03|017': { 'статус': 'ОТ' },
            '2026-09-02|017': { '__delete': true }
        };
        var html = sheetHost({ entries: entries, pending: pending })
            ._buildPrintHtml(EMPS, AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('ОТ — Отпуск') !== -1,
            'код локальной правки попадает в перечень');
        assertTrue(lg.indexOf('Д —') === -1,
            'удалённая запись исключает код Д');
    });

    test('VM: легаси-код вне справочника — в конце, только код', () => {
        var entries = {
            '2026-09-02|017': { 'статус': 'Д' },
            '2026-09-03|017': { 'статус': 'ZZ' }
        };
        var html = sheetHost({ entries: entries })._buildPrintHtml(EMPS, AGG);
        var lg = legendSection(html);
        var iD = lg.indexOf('Д —');
        var iZ = lg.indexOf('>ZZ<');
        assertTrue(iZ !== -1, 'легаси-код печатается');
        assertTrue(lg.indexOf('ZZ —') === -1, 'без имени (нет в справочнике)');
        assertTrue(iD !== -1 && iZ > iD, 'легаси-код ПОСЛЕ кодов справочника');
    });

    test('VM: записей нет — «Коды:» без строк (структура жива, регресс 343)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('Коды:') !== -1, 'заголовок перечня жив');
        assertTrue(lg.indexOf('wsp-lg') === -1 || lg.indexOf('<i') === -1,
            'строк кодов нет (все статусы месяца отсутствуют)');
    });

    test('VM: печатаемые строки определяют коды (вид — не все сотрудники)', () => {
        // только Иванов печатается — его коды в перечне, код
        // Сидорова (единственный Н) НЕ попадает
        var entries = {
            '2026-09-02|017': { 'статус': 'Д' },
            '2026-09-03|031': { 'статус': 'Н' }
        };
        var html = sheetHost({ entries: entries })
            ._buildPrintHtml([EMPS[0]], AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('Д — День (12-час)') !== -1, 'код печатаемой строки');
        assertTrue(lg.indexOf('Н —') === -1,
            'код НЕпечатаемой строки в перечень не попадает');
    });
""",
     """    test('VM: пустой месяц записей — легенды нет, лист валиден', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('wsp-legend') === -1,
            'легенды нет и без записей (Task 442)');
        assertTrue(html.indexOf('нет мероприятий в этом месяце') !== -1,
            'заглушка мероприятий жива (Task 360)');
    });

    test('VM: печатаемые строки больше не влияют на перечень (его нет)', () => {
        var entries = {
            '2026-09-02|017': { 'статус': 'Д' },
            '2026-09-03|031': { 'статус': 'Н' }
        };
        var html = sheetHost({ entries: entries })
            ._buildPrintHtml([EMPS[0]], AGG);
        assertTrue(html.indexOf('wsp-legend') === -1,
            'легенды нет при любых записях (Task 442)');
        assertTrue(html.indexOf('Н —') === -1 && html.indexOf('Д — День') === -1,
            'расшифровок кодов на листе нет');
    });
""", 'vm-легенда-остальное'),
])

# ============================================================
# test-task361.js
# ============================================================
adapt('tests/test-task361.js', [
    ("""    test('SRC: строки ПОД таблицей крупнее', () => {
        assertTrue(ruleOf('#wsPrintSheet .wsp-mev {').indexOf('font-size: 11px') !== -1,
            'список мероприятий 11px (был 8px)');
        assertTrue(ruleOf('#wsPrintSheet .wsp-legend {').indexOf('font-size: 11px') !== -1,
            'перечень кодов 11px (был 8px)');
        assertTrue(INDEX_SRC.indexOf('#wsPrintSheet .wsp-foot {') === -1,
            'сноска удалена — правило .wsp-foot убрано (Task 438)');
        const i = ruleOf('#wsPrintSheet .wsp-mev-item i {');
        assertTrue(i.indexOf('width: 9px') !== -1, 'точка цвета 9px (была 7px)');
        const lg = ruleOf('#wsPrintSheet .wsp-lg i {');
        assertTrue(lg.indexOf('width: 9px') !== -1, 'точка кода 9px (была 7px)');
    });
""",
     """    test('SRC: строки ПОД таблицей крупнее (легенды нет — Task 442)', () => {
        assertTrue(ruleOf('#wsPrintSheet .wsp-mev {').indexOf('font-size: 11px') !== -1,
            'список мероприятий 11px (был 8px)');
        assertTrue(INDEX_SRC.indexOf('#wsPrintSheet .wsp-legend {') === -1,
            'правило .wsp-legend удалено вместе с перечнем (Task 442)');
        assertTrue(INDEX_SRC.indexOf('#wsPrintSheet .wsp-foot {') === -1,
            'сноска удалена — правило .wsp-foot убрано (Task 438)');
        const i = ruleOf('#wsPrintSheet .wsp-mev-item i {');
        assertTrue(i.indexOf('width: 9px') !== -1, 'точка цвета 9px (была 7px)');
    });
""", 'под-таблицей'),

    ("""    test('SRC: CSS .wsp-ev-wrap/.wsp-ev/.wsp-ev-plan в @media print', () => {
        const block = printCss();
        const wrap = block.indexOf('#wsPrintSheet .wsp-ev-wrap {');
        assertTrue(wrap !== -1, 'правило .wsp-ev-wrap есть');
        const wrapRule = block.slice(wrap, block.indexOf('}', wrap) + 1);
        assertTrue(wrapRule.indexOf('position: absolute') !== -1,
            'позиционирование в углу ячейки');
        assertTrue(wrapRule.indexOf('bottom:') !== -1 && wrapRule.indexOf('right:') !== -1,
            'правый НИЖНИЙ угол (точка переработки — верхний)');
        const ev = block.indexOf('#wsPrintSheet .wsp-ev {');
        const evRule = block.slice(ev, block.indexOf('}', ev) + 1);
        assertTrue(evRule.indexOf('print-color-adjust: exact') !== -1,
            'цвет бейджа печатается принудительно');
        assertFalse(block.indexOf('wsp-ev-plan') !== -1,
            'пунктирного бейджа-план нет (Task 388: заливка всегда)');
    });

    test('SRC: _printCell — события дня, виртуальный бейдж, solid/plan', () => {
        const c = stripComments(methodText(WS_CLIENT, '_printCell'));
        assertTrue(c.indexOf('_eventsAt') !== -1, 'источник — _eventsAt');
        assertTrue(c.indexOf('events.concat') !== -1,
            'виртуальный бейдж статус-мероприятия без строки в «Инструктажах»');
        // Task 388: бейдж печати ВСЕГДА сплошной с цветом кода
        assertFalse(c.indexOf('wsp-ev-plan') !== -1,
            'пунктирных бейджей нет (Task 388)');
        assertTrue(c.indexOf("evMeta.color ? ' style=\\"background:' + evMeta.color") !== -1,
            'inline-цвет кода из справочника');
        assertTrue(c.indexOf("content + evHtml + '</td>'") !== -1,
            'бейджи добавляются в ячейку после кода');
    });
""",
     """    test('SRC: CSS бейджей .wsp-ev* УДАЛЕНЫ (Task 442)', () => {
        const block = printCss();
        assertTrue(block.indexOf('#wsPrintSheet .wsp-ev-wrap {') === -1,
            'правила .wsp-ev-wrap нет (значки удалены)');
        assertTrue(block.indexOf('#wsPrintSheet .wsp-ev {') === -1,
            'правила .wsp-ev нет');
        assertTrue(block.indexOf('wsp-ev-plan') === -1,
            'и пунктирного плана нет (сняты вместе со значками)');
    });

    test('SRC: _printCell — бейджей НЕТ (Task 442)', () => {
        const c = stripComments(methodText(WS_CLIENT, '_printCell'));
        assertTrue(c.indexOf('_eventsAt') === -1,
            'события дня печатной ячейкой не запрашиваются');
        assertTrue(c.indexOf('events.concat') === -1,
            'виртуального бейджа нет');
        assertTrue(c.indexOf('wsp-ev') === -1,
            'разметки бейджей в ячейке нет (Task 442)');
        assertTrue(c.indexOf("content + '</td>'") !== -1,
            'ячейка закрывается сразу после кода/точки');
    });
""", 'src-бейджи-361'),

    ("""    test('VM: смена Д + событие И — код в центре + сплошной бейдж с цветом', () => {
        var td = cellHost({ meta: { code: 'Д', color: '#FFE082' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(2, '2026-09-02', EMP, { 'статус': 'Д' });
        assertTrue(td.indexOf('background:#FFE082;">Д<') !== -1,
            'код смены Д в центре ячейки (регресс 341)');
        assertTrue(td.indexOf('class="wsp-ev"') !== -1, 'бейдж сплошной (день сформирован)');
        assertTrue(td.indexOf('>И</span>') !== -1, 'код мероприятия в бейдже');
        assertTrue(td.indexOf('wsp-ev-plan') === -1, 'пунктирного нет');
    });

    test('VM: пустая ячейка + 2 события — два СПЛОШНЫХ бейджа с заливкой (Task 388)', () => {
        var td = cellHost({ events: [{ code: 'И', training: 1 },
                                      { code: 'ПР', training: 2 }] })
            ._printCell(6, '2026-09-06', EMP, null);
        var n = (td.match(/class="wsp-ev"/g) || []).length;
        assertEqual(n, 2, 'два сплошных бейджа');
        assertTrue(td.indexOf('background:') !== -1,
            'с заливкой цветом кода (Task 388)');
    });

    test('VM: статус-мероприятие И покрыто событием — один бейдж (без дубля)', () => {
        var td = cellHost({ meta: { code: 'И', color: '#B3E5FC' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(5, '2026-09-05', EMP, { 'статус': 'И' });
        var n = (td.match(/class="wsp-ev"/g) || []).length;
        assertEqual(n, 1, 'виртуальный бейдж НЕ дублирует запись «Инструктажей»');
    });

    test('VM: статус-мероприятие ОБ БЕЗ записи — виртуальный бейдж строится', () => {
        var td = cellHost({ meta: { code: 'ОБ', color: '#D1C4E9' } })
            ._printCell(7, '2026-09-07', EMP, { 'статус': 'ОБ' });
        assertTrue(td.indexOf('>ОБ</span>') !== -1, 'виртуальный бейдж');
        assertTrue(td.indexOf('background:#D1C4E9') !== -1, 'с цветом справочника');
    });

    test('VM: переработка + событие — точка сверху, бейдж снизу (без конфликтов)', () => {
        var td = cellHost({ events: [{ code: 'И', training: 7 }] })
            ._printCell(3, '2026-09-03', EMP,
                        { 'статус': 'д', 'переработка': 1 });
        assertTrue(td.indexOf('wsp-over') !== -1, 'красная точка переработки');
        assertTrue(td.indexOf('wsp-ev-wrap') !== -1, 'бейдж мероприятия');
    });
""",
     """    test('VM: смена Д + событие И — только код в центре, бейджа НЕТ (Task 442)', () => {
        var td = cellHost({ meta: { code: 'Д', color: '#FFE082' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(2, '2026-09-02', EMP, { 'статус': 'Д' });
        assertTrue(td.indexOf('background:#FFE082;">Д<') !== -1,
            'код смены Д в центре ячейки (регресс 341)');
        assertTrue(td.indexOf('wsp-ev') === -1,
            'бейджа НЕТ (Task 442: мини-значки удалены)');
    });

    test('VM: пустая ячейка + 2 события — бейджей НЕТ (Task 442)', () => {
        var td = cellHost({ events: [{ code: 'И', training: 1 },
                                      { code: 'ПР', training: 2 }] })
            ._printCell(6, '2026-09-06', EMP, null);
        assertTrue(td.indexOf('wsp-ev') === -1, 'бейджей нет вовсе');
        assertTrue(td.indexOf('background:') === -1, 'заливки нет');
    });

    test('VM: статус-мероприятие И — ПУСТАЯ ячейка (Task 442)', () => {
        var td = cellHost({ meta: { code: 'И', color: '#B3E5FC' },
                            events: [{ code: 'И', training: 7 }] })
            ._printCell(5, '2026-09-05', EMP, { 'статус': 'И' });
        assertTrue(td.indexOf('>И<') === -1, 'кода нет');
        assertTrue(td.indexOf('wsp-ev') === -1, 'бейджа нет');
        assertTrue(td.indexOf('background:') === -1, 'фона нет');
    });

    test('VM: статус-мероприятие ОБ БЕЗ записи — ПУСТАЯ ячейка (Task 442)', () => {
        var td = cellHost({ meta: { code: 'ОБ', color: '#D1C4E9' } })
            ._printCell(7, '2026-09-07', EMP, { 'статус': 'ОБ' });
        assertTrue(td.indexOf('>ОБ<') === -1, 'кода нет');
        assertTrue(td.indexOf('wsp-ev') === -1, 'бейджа нет');
    });

    test('VM: переработка + событие — точка есть, бейджа нет (Task 442)', () => {
        var td = cellHost({ events: [{ code: 'И', training: 7 }] })
            ._printCell(3, '2026-09-03', EMP,
                        { 'статус': 'д', 'переработка': 1 });
        assertTrue(td.indexOf('wsp-over') !== -1, 'красная точка переработки');
        assertTrue(td.indexOf('wsp-ev') === -1, 'бейджа нет (Task 442)');
    });
""", 'vm-бейджи-361'),

    ("""        assertTrue(html.indexOf('<div class="wsp-mev">') !== -1, 'секция мероприятий (Task 360)');
        assertTrue(html.indexOf('<div class="wsp-legend">') !== -1, 'перечень кодов (Task 360)');
""",
     """        assertTrue(html.indexOf('<div class="wsp-mev">') !== -1, 'секция мероприятий (Task 360)');
        assertTrue(html.indexOf('<div class="wsp-legend">') === -1,
            'перечня кодов НЕТ (Task 442: столбец удалён)');
""", 'vm-структура-361'),
])

# ============================================================
# test-task362.js
# ============================================================
adapt('tests/test-task362.js', [
    ("""    test('SRC: коды мероприятий месяца попадают в usedCodes', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('_trainingCodeOf(evList[eci][\\'тип\\'])') !== -1,
            'код типа записи «Инструктажей»');
        assertTrue(b.indexOf('usedCodes[evCd] = true') !== -1,
            'код мероприятия помечается в usedCodes');
        // пустой код (неизвестный тип) не помечается
        assertTrue(b.indexOf('if (evCd) usedCodes[evCd] = true;') !== -1,
            'только непустой код');
    });
""",
     """    test('SRC: пометка кодов мероприятий в usedCodes УДАЛЕНА (Task 442)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('usedCodes[evCd] = true') === -1,
            'сбора usedCodes нет — перечня кодов больше нет');
        // код типа по-прежнему читается для ТЕКСТА строки списка
        assertTrue(b.indexOf('_trainingCodeOf(ev[\\'тип\\'])') !== -1,
            'код типа живёт в тексте мероприятий (список ниже таблицы)');
    });
""", 'src-usedcodes-362'),

    ("""    test('VM: дневной вид — «ПЗ — Проверка знаний» печатается (баг заявки)', () => {
        var html = sheetHost({ view: 'day', trainings: TRAININGS, entries: ENTRIES })
            ._buildPrintHtml([EMPS[1]], AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('ПЗ — Проверка знаний') !== -1,
            'наименование кода ПЗ из списка мероприятий (записи сетки нет)');
        assertTrue(lg.indexOf('ОБ — Обучение') !== -1,
            'код ОБ мероприятия тоже объяснён');
        assertTrue(lg.indexOf('Д8 — День 8-час') !== -1,
            'код сетки дневного на месте');
    });

    test('VM: дневной вид — коды сменного НЕ печатаются', () => {
        var html = sheetHost({ view: 'day', trainings: TRAININGS, entries: ENTRIES })
            ._buildPrintHtml([EMPS[1]], AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('И — Инструктаж') === -1,
            'код И сменного не в дневном виде');
        assertTrue(lg.indexOf('Н — Ночь') === -1,
            'код Н сменного не в дневном виде');
        assertTrue(lg.indexOf('Д — День (12-час)') === -1,
            'код Д сменного не в дневном виде');
    });

    test('VM: сменный вид — код И из мероприятия, ПЗ/ОБ нет', () => {
        var html = sheetHost({ view: 'shift', trainings: TRAININGS, entries: ENTRIES })
            ._buildPrintHtml([EMPS[0]], AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('И — Инструктаж') !== -1,
            'код И мероприятия сменного объяснён');
        assertTrue(lg.indexOf('Д — День (12-час)') !== -1 &&
                   lg.indexOf('Н — Ночь (12-час)') !== -1,
            'коды сетки сменного на месте');
        assertTrue(lg.indexOf('ПЗ —') === -1 && lg.indexOf('ОБ —') === -1,
            'коды дневного в сменном виде НЕ печатаются');
    });

    test('VM: полный вид — коды всех мероприятий месяца', () => {
        var html = sheetHost({ view: 'full', trainings: TRAININGS, entries: ENTRIES })
            ._buildPrintHtml(EMPS, AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('И — Инструктаж') !== -1 &&
                   lg.indexOf('ОБ — Обучение') !== -1 &&
                   lg.indexOf('ПЗ — Проверка знаний') !== -1,
            'полный вид: И/ОБ/ПЗ объяснены');
    });

    test('VM: мероприятие вне месяца код в перечень НЕ даёт', () => {
        var trs = [
            { 'таб_номер': '017', 'тип': 'инструктаж',
              'дата_начала': '2026-10-05', 'тема': 'Октябрь' }];
        var html = sheetHost({ view: 'shift', trainings: trs, entries: ENTRIES })
            ._buildPrintHtml([EMPS[0]], AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('И — Инструктаж') === -1,
            'код И октября в сентябрьском перечне отсутствует');
        assertTrue(lg.indexOf('Д — День (12-час)') !== -1,
            'коды сетки сентября живы');
    });
""",
     """    test('VM: перечень кодов месяца УДАЛЁН (Task 442)', () => {
        // прежде: коды мероприятий/сетки попадали в перечень;
        // теперь перечня нет вовсе — при любых записях
        var html = sheetHost({ view: 'day', trainings: TRAININGS, entries: ENTRIES })
            ._buildPrintHtml([EMPS[1]], AGG);
        assertTrue(html.indexOf('wsp-legend') === -1,
            'легенды кодов нет (Task 442: столбец удалён)');
        assertTrue(html.indexOf('ПЗ — Проверка знаний') === -1,
            'расшифровки ПЗ нет');
        assertTrue(html.indexOf('Д8 — День 8-час') === -1,
            'расшифровки Д8 нет');
        // список мероприятий при этом жив и несёт коди в тексте
        var sec = mevSection(html);
        assertTrue(sec.indexOf('ПЗ · Проверка знаний промбезопасности') !== -1,
            'мероприятие ПЗ — в списке под таблицей');
    });

    test('VM: сменный вид — легенды нет, мероприятия живы (Task 442)', () => {
        var html = sheetHost({ view: 'shift', trainings: TRAININGS, entries: ENTRIES })
            ._buildPrintHtml([EMPS[0]], AGG);
        assertTrue(html.indexOf('wsp-legend') === -1, 'легенды нет');
        var sec = mevSection(html);
        assertTrue(sec.indexOf('И · Повторный инструктаж') !== -1,
            'мероприятие сменного на месте');
    });

    test('VM: полный вид — легенды нет (Task 442)', () => {
        var html = sheetHost({ view: 'full', trainings: TRAININGS, entries: ENTRIES })
            ._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('wsp-legend') === -1,
            'полный вид: перечня кодов тоже нет');
        assertTrue(html.indexOf('Коды:') === -1, 'заголовка нет');
    });
""", 'vm-перечень-362'),

    ("""    test('VM: неизвестный тип мероприятия — строка без кода, перечень не растёт', () => {
        var trs = [
            { 'таб_номер': '023', 'тип': 'иное',
              'дата_начала': '2026-09-12', 'тема': 'Встреча' }];
        var html = sheetHost({ view: 'day', trainings: trs, entries: ENTRIES })
            ._buildPrintHtml([EMPS[1]], AGG);
        var sec = mevSection(html);
        assertTrue(sec.indexOf('Встреча · Петров Пётр Петрович') !== -1,
            'строка без кода печатается (тема · ФИО)');
        var lg = legendSection(html);
        assertTrue(lg.indexOf('wsp-lg') === -1 || lg.indexOf('Д8 —') !== -1,
            'перечень не упал');
        assertTrue(lg.indexOf('И —') === -1 && lg.indexOf('ПЗ —') === -1 &&
                   lg.indexOf('ОБ —') === -1,
            'пустой код типа ничего не добавил');
    });

    test('VM: статус-мероприятие сетки по-прежнему даёт код (без «Инструктажей»)', () => {
        // запись сетки И у дневного БЕЗ строки в «Инструктажах» —
        // код обязан попасть в перечень из цикла строк (Task 360)
        var entries = { '2026-09-10|023': { 'статус': 'ПЗ' } };
        var html = sheetHost({ view: 'day', trainings: [], entries: entries })
            ._buildPrintHtml([EMPS[1]], AGG);
        var lg = legendSection(html);
        assertTrue(lg.indexOf('ПЗ — Проверка знаний') !== -1,
            'код статус-мероприятия сетки объяснён');
    });
""",
     """    test('VM: неизвестный тип мероприятия — строка без кода (Task 442)', () => {
        var trs = [
            { 'таб_номер': '023', 'тип': 'иное',
              'дата_начала': '2026-09-12', 'тема': 'Встреча' }];
        var html = sheetHost({ view: 'day', trainings: trs, entries: ENTRIES })
            ._buildPrintHtml([EMPS[1]], AGG);
        var sec = mevSection(html);
        assertTrue(sec.indexOf('Встреча · Петров Пётр Петрович') !== -1,
            'строка без кода печатается (тема · ФИО)');
        assertTrue(html.indexOf('wsp-legend') === -1,
            'легенды нет — «добавлять» код некуда (Task 442)');
    });

    test('VM: статус-мероприятие сетки — пустая ячейка без бейджа (Task 442)', () => {
        // запись сетки И у дневного БЕЗ строки в «Инструктажах» —
        // ячейка пустая: ни кода, ни значка (Task 442)
        var entries = { '2026-09-10|023': { 'статус': 'ПЗ' } };
        var html = sheetHost({ view: 'day', trainings: [], entries: entries })
            ._buildPrintHtml([EMPS[1]], AGG);
        assertTrue(html.indexOf('wsp-ev') === -1,
            'бейджей в печати нет (Task 442)');
        assertTrue(html.indexOf('wsp-legend') === -1,
            'перечня кодов нет');
    });
""", 'vm-хвост-362'),

    ("""        assertTrue(html.indexOf('<div class="wsp-mev">') !== -1,
            'секция мероприятий (Task 360)');
        assertTrue(html.indexOf('<div class="wsp-legend">') !== -1,
            'перечень кодов (Task 360)');
""",
     """        assertTrue(html.indexOf('<div class="wsp-mev">') !== -1,
            'секция мероприятий (Task 360)');
        assertTrue(html.indexOf('<div class="wsp-legend">') === -1,
            'перечня кодов НЕТ (Task 442)');
""", 'vm-структура-362'),
])

# ============================================================
# test-task364.js
# ============================================================
adapt('tests/test-task364.js', [
    ("""        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): нижняя секция — ГИБКИЙ РЯД (флоат Task 432
        // не вернулся): список мероприятий слева, коды справа
        assertTrue(r.indexOf('display: flex') !== -1,
            'обёртка — flex-ряд (Task 439)');
        assertTrue(r.indexOf('align-items: flex-start') !== -1,
            'блоки выровнены по верхней линии');
        // Task 440 (заявка: «на расстоянии друг от друга 10px»):
        // зазор ряда — ровно 10px (прежде 6mm Task 439)
        assertTrue(r.indexOf('gap: 10px') !== -1, 'зазор между блоками — 10px (Task 440)');
        assertTrue(r.indexOf('flow-root') === -1,
            'флоат-обёртки Task 432 не вернулась');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы на обёртке жив');
    });
""",
     """        // Task 442: ряд Task 439/440 снят — блока кодов справа
        // больше нет; обёртка — простой блок с отступом от таблицы
        assertTrue(r.indexOf('display: flex') === -1,
            'flex-ряда НЕТ (Task 442: кодов справа больше нет)');
        assertTrue(r.indexOf('gap') === -1,
            'зазора между блоками нет (снят с рядом)');
        assertTrue(r.indexOf('flow-root') === -1,
            'флоат-обёртки Task 432 не вернулась');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы на обёртке жив');
    });
""", 'wsp-bottom-364'),

    ("""    test('SRC: CSS .wsp-mev — ЛЕВАЯ часть ряда (без растяжения, Task 440)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        // Task 439: мероприятия — левая часть flex-ряда обёртки
        // (коды — справа). Task 440: flex-grow СНЯТ — коды встают в
        // 10px от текста мероприятий (семантика Task 431), длинные
        // тексты переносятся (flex-shrink + min-width: 0)
        assertTrue(r.indexOf('flex: 0 1 auto') !== -1,
            'блок мероприятий НЕ растягивается — коды за текстом (Task 440)');
        assertTrue(r.indexOf('min-width: 0') !== -1,
            'усадка для переносов текста');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
""",
     """    test('SRC: CSS .wsp-mev — НЕ ограничен, вся ширина (Task 442)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        // Task 442: кодов справа нет — столбик мероприятий занимает
        // всю ширину листа (ограничения зоны Tasks 439/440 сняты)
        assertTrue(r.indexOf('flex:') === -1,
            'flex-ограничений нет (кодов справа больше нет)');
        assertTrue(r.indexOf('min-width') === -1,
            'усадка зоны снята');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
""", 'wsp-mev-364'),

    ("""    test('SRC: CSS .wsp-legend — ПРАВЫЙ блок ряда (Task 439)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        // Task 439: коды — ПРАВАЯ часть flex-ряда (справа от
        // мероприятий), фиксированная ширина блока
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'блок кодов — фикс. ширина 92mm справа (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'верхняя линия общая с мероприятиями');
        assertTrue(r.indexOf('float:') === -1,
            'флоат Task 432 не вернулся');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });

    test('SRC: JS — обёртка открывается ДО секции мероприятий', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom строится');
        assertTrue(iOpen < iMev, 'открытие обёртки до мероприятий');
        // Task 433: секция ВЕРТИКАЛЬНАЯ — список мероприятий
        // ПЕРВЫМ, коды — строкой-абзацем ПОД ним (флоат Task 432
        // строил коды первыми в DOM)
        assertTrue(iMev < iLegend, 'коды — ПОД списком мероприятий (Task 433)');
        assertTrue(iFoot === -1, 'сноски нет (Task 438)');
    });

    test('SRC: JS — обёртка закрывается ПОСЛЕ кодов (двойной div)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        // Task 433: порядок — мероприятия → коды → закрытие обёртки:
        // закрытие кодов и обёртки — ДВА последовательных оператора
        const iClose1 = b.indexOf("html += '</div>';", iLegend);
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iClose1 !== -1 && iClose2 !== -1,
            'двойное закрытие legend + обёртки');
        assertTrue(iClose1 > iLegend, 'закрытие после перечня кодов');
        assertTrue(iClose2 - iClose1 < 200,
            'операторы закрытия — подряд');
    });
""",
     """    test('SRC: CSS .wsp-legend — правило УДАЛЕНО (Task 442)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        assertTrue(r === '',
            'правила .wsp-legend нет — блок кодов удалён (Task 442)');
    });

    test('SRC: JS — обёртка содержит только мероприятия (Task 442)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iOpen = b.indexOf('<div class="wsp-bottom">');
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom строится');
        assertTrue(iOpen < iMev, 'открытие обёртки до мероприятий');
        assertTrue(b.indexOf('wsp-legend') === -1,
            'секции кодов нет (Task 442)');
        assertTrue(iFoot === -1, 'сноски нет (Task 438)');
    });

    test('SRC: JS — закрытие обёртки ПОСЛЕ мероприятий (Task 442)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iMev = b.indexOf('<div class="wsp-mev">');
        // Task 442: секция одна — после её закрытия обёртка
        // закрывается тем же оператором ряда
        const iClose1 = b.indexOf("html += '</div>';", iMev);
        assertTrue(iClose1 !== -1, 'закрытие после мероприятий есть');
        assertTrue(iClose1 > iMev, 'закрытие после секции');
    });
""", 'src-хвост-364'),

    ("""    test('VM: лист содержит обёртку, внутри — мероприятия и коды', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iMev = html.indexOf('<div class="wsp-mev">');
        var iLegend = html.indexOf('<div class="wsp-legend">');
        var iClose = html.indexOf('</div></div>', iLegend);
        var iFoot = html.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom в листе');
        // Task 433: секция вертикальная — мероприятия ПЕРВЫМИ,
        // коды — ПОД списком (флоат Task 432 строил коды первыми)
        assertTrue(iOpen < iMev && iMev < iLegend,
            'мероприятия, за ними коды — внутри обёртки (Task 433)');
        assertTrue(iClose !== -1 && iClose > iLegend, 'обёртка закрыта после кодов');
        assertTrue(iFoot === -1, 'сноски нет (Task 438)');
    });

    test('VM: у мероприятий и кодов НЕТ личных обёрток-посредников', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        // структура CSS проверена в SRC; здесь — что оба блока
        // в одном родителе: между закрытием mev и открытием legend
        // (Task 433: мероприятия строятся первыми) нет посредников
        var iMev = html.indexOf('<div class="wsp-mev">');
        var iLegend = html.indexOf('<div class="wsp-legend">');
        var iMevEnd = html.indexOf('</div>', iMev);
        var between = html.slice(iMevEnd + 6, iLegend);
        assertEqual(between.replace(/\\s+/g, ''), '',
            'legend — непосредственный сосед mev в обёртке');
    });

    test('VM: регресс 362 — ПЗ печатается в перечне кодов (в обёртке)', () => {
        var html = sheetHost({ view: 'day' })._buildPrintHtml([EMPS[1]], AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iClose = html.indexOf('</div></div>', iOpen);
        var row = html.slice(iOpen, iClose);
        assertTrue(row.indexOf('ПЗ — Проверка знаний') !== -1,
            'наименование ПЗ в перечне кодов внутри ряда');
        assertTrue(row.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий в ряду (вид: дневной)');
    });

    test('VM: пустой месяц — заглушка в левой колонке, коды справа', () => {
        var html = sheetHost({ trainings: [] })._buildPrintHtml(EMPS, AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iClose = html.indexOf('</div></div>', iOpen);
        var row = html.slice(iOpen, iClose);
        assertTrue(row.indexOf('нет мероприятий в этом месяце') !== -1,
            'заглушка мероприятий на месте');
        assertTrue(row.indexOf('Коды:') !== -1, 'заголовок кодов в ряду');
    });
""",
     """    test('VM: обёртка содержит только мероприятия (Task 442)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iMev = html.indexOf('<div class="wsp-mev">');
        var iClose = html.indexOf('</div></div>', iOpen);
        var iFoot = html.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom в листе');
        assertTrue(iOpen < iMev, 'мероприятия внутри обёртки');
        assertTrue(iClose !== -1 && iClose > iMev, 'обёртка закрыта после мероприятий');
        assertTrue(html.indexOf('wsp-legend') === -1,
            'секции кодов НЕТ (Task 442)');
        assertTrue(iFoot === -1, 'сноски нет (Task 438)');
    });

    test('VM: регресс 362 — ПЗ в списке мероприятий (без перечня)', () => {
        var html = sheetHost({ view: 'day' })._buildPrintHtml([EMPS[1]], AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iClose = html.indexOf('</div></div>', iOpen);
        var row = html.slice(iOpen, iClose);
        assertTrue(row.indexOf('ПЗ · Проверка знаний промбезопасности') !== -1,
            'мероприятие ПЗ — в списке (без расшифровки-перечня)');
        assertTrue(row.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'заголовок мероприятий (вид: дневной)');
    });

    test('VM: пустой месяц — заглушка, кодов нет (Task 442)', () => {
        var html = sheetHost({ trainings: [] })._buildPrintHtml(EMPS, AGG);
        var iOpen = html.indexOf('<div class="wsp-bottom">');
        var iClose = html.indexOf('</div></div>', iOpen);
        var row = html.slice(iOpen, iClose);
        assertTrue(row.indexOf('нет мероприятий в этом месяце') !== -1,
            'заглушка мероприятий на месте');
        assertTrue(row.indexOf('Коды:') === -1, 'заголовка кодов нет (Task 442)');
    });
""", 'vm-хвост-364'),
])

# ============================================================
# test-task375.js
# ============================================================
adapt('tests/test-task375.js', [
    ("""        // Task 440 (заявка: «коды справа от мероприятий на
        // расстоянии друг от друга 10px»): ряд Task 439 — зазор
        // между блоками СНОВА ровно 10px (как в Task 375)
        assertTrue(r.indexOf('gap: 10px') !== -1,
            'зазор между блоками ряда — ровно 10px (Task 440)');
        const leg = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        assertTrue(leg.indexOf('float:') === -1,
            'коды — не плавающий столбик (Task 439: правый блок ряда)');
        assertTrue(leg.indexOf('margin-top: 0') !== -1,
            'отступ строки кодов снят (Task 439: общая верхняя линия с мероприятиями)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы на обёртке не тронут');
    });
""",
     """        // Task 442: блок кодов удалён — зазора между блоками и
        // самого ряда больше нет (зазор 10px Tasks 375/440 снят
        // вместе с правым блоком)
        assertTrue(r.indexOf('gap') === -1,
            'зазора между блоками нет — блока кодов больше нет (Task 442)');
        const leg = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        assertTrue(leg === '',
            'правила .wsp-legend нет (столбец кодов удалён, Task 442)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы на обёртке не тронут');
    });
""", 'зазор-375'),
])

# ============================================================
# test-task387.js
# ============================================================
adapt('tests/test-task387.js', [
    ("""    test('печать: «.» раскрывается строкой «Выходного» без кода', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        assertTrue(b.indexOf("!(codes[ci].code === '' && usedCodes['.'])") !== -1,
            'фильтр: usedCodes[„."]» раскрывает слот «Выходного»');
        assertTrue(b.indexOf("this._esc(codes[ci].name || 'Выходной')") !== -1,
            'строка «Выходного» — имя без кода-символа');
    });
""",
     """    test('печать: слот «Выходного» удалён вместе с легендой (Task 442)', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        assertTrue(b.indexOf("usedCodes['.'])") === -1,
            'фильтра-раскрытия «.» нет — перечня кодов больше нет (Task 442)');
        assertTrue(b.indexOf("codes[ci].name || 'Выходной'") === -1,
            'строки «Выходного» в печати нет');
    });
""", 'слот-387'),
])

# ============================================================
# test-task388.js
# ============================================================
adapt('tests/test-task388.js', [
    ("""    test('печать: _printCell — бейдж всегда сплошной', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_printCell'));
        assertFalse(fn.indexOf('wsp-ev-plan') !== -1,
            'пунктирных бейджей-план в печати нет');
        assertTrue(fn.indexOf("evMeta.color ? ' style=\\"background:' + evMeta.color") !== -1,
            'inline-цвет кода — безусловно');
        assertFalse(INDEX_SRC.indexOf('.wsp-ev.wsp-ev-plan { border-style: dashed; }') !== -1,
            'CSS-правило пунктирного бейджа печати удалено');
    });
""",
     """    test('печать: _printCell — бейджей НЕТ (Task 442)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_printCell'));
        assertTrue(fn.indexOf('wsp-ev') === -1,
            'бейджей в печати нет вовсе (мини-значки удалены, Task 442)');
        assertTrue(fn.indexOf('evMeta') === -1,
            'цветов бейджей в печатной ячейке нет');
        assertFalse(INDEX_SRC.indexOf('.wsp-ev.wsp-ev-plan { border-style: dashed; }') !== -1,
            'CSS-правило пунктирного бейджа печати удалено');
    });
""", 'бейдж-387-печать'),

    ("""    // --- _printCell: бейдж печати на пустой ячейке — сплошной ---
    test('VM: печать — «*» на пустой ячейке со заливкой цветом кода', () => {
        const host = new Function('return ({' +
            methodText(INDEX_SRC, '_printCell') + ',\\n' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_statusMeta: function(code) { return { code: code, color: "#FFAB91" }; },' +
            '_calDayOff: function() { return false; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { return [{ code: "*", training: 1 }]; },' +
            '_esc: function(s) { return String(s); }' +
            '});')();
        const td = host._printCell(6, '2026-09-06',
            { 'таб_номер': '017' }, null);
        assertFalse(td.indexOf('wsp-ev-plan') !== -1, 'пунктирного бейджа нет');
        assertTrue(/class="wsp-ev"/.test(td), 'бейдж один вида (сплошной)');
        assertTrue(td.indexOf('background:#FFAB91') !== -1,
            'заливка цветом «*» — и на печати');
    });
""",
     """    // --- _printCell: бейджей печати больше нет (Task 442) ---
    test('VM: печать — «*» в ячейке НЕ отображается (Task 442)', () => {
        const host = new Function('return ({' +
            methodText(INDEX_SRC, '_printCell') + ',\\n' +
            '_EVENT_CODES: ["И","ОБ","ПЗ","ПР","*"],' +
            '_statusMeta: function(code) { return { code: code, color: "#FFAB91" }; },' +
            '_calDayOff: function() { return false; },' +
            '_vacationAt: function() { return null; },' +
            '_eventsAt: function() { return [{ code: "*", training: 1 }]; },' +
            '_esc: function(s) { return String(s); }' +
            '});')();
        const td = host._printCell(6, '2026-09-06',
            { 'таб_номер': '017' }, null);
        assertTrue(td.indexOf('wsp-ev') === -1,
            'бейджа НЕТ (мини-значки удалены, Task 442)');
        assertTrue(td.indexOf('background:#FFAB91') === -1,
            'заливки цвета «*» в печати нет');
    });
""", 'vm-звезда-388'),
])

print()
print('=== ИТОГ adapt-360-388 ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ГОТОВО')
