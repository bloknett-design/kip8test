#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 410 — адаптация тестов под режимы шторки «+ Инструктаж…»:
instr (select всех пунктов «Список_И_и_ПЗ», без поля «Тип») и
мероприятие (типы обучение/прогул/примечание). Поведение по заявке
изменилось — ассерты приведены к новой семантике."""
import io

BASE = '/home/z/my-project/kip8test/tests/'


def patch(fname, edits):
    p = BASE + fname
    with io.open(p, encoding='utf-8') as f:
        s = f.read()
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            raise SystemExit('%s: ЯКОРЬ n=%d: %r' % (fname, n, old[:100]))
        s = s.replace(old, new)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: %d правок' % (fname, len(edits)))


# ---------------------------------------------------------------- 306
patch('test-task306.js', [
    ("""    test('HTML: форма «Новое мероприятие» — 5 опций типа', () => {
        const sel = INDEX_SRC.match(/<select id="wsTrType"[\\s\\S]*?<\\/select>/);
        assertTrue(!!sel, 'селект типа найден');
        ['инструктаж', 'обучение', 'проверка_знаний', 'прогул', 'примечание']
            .forEach(v => {
                assertTrue(sel[0].indexOf('value="' + v + '"') !== -1,
                    'опция «' + v + '» есть');
            });
    });""",
     """    test('HTML: форма «Новое мероприятие» — 3 опции типа (Task 410)', () => {
        const sel = INDEX_SRC.match(/<select id="wsTrType"[\\s\\S]*?<\\/select>/);
        assertTrue(!!sel, 'селект типа найден');
        ['обучение', 'прогул', 'примечание']
            .forEach(v => {
                assertTrue(sel[0].indexOf('value="' + v + '"') !== -1,
                    'опция «' + v + '» есть');
            });
        // Task 410: инструктаж/проверка знаний — только через блок
        // инструктажей (select «Список_И_и_ПЗ»), в типах их нет
        ['инструктаж', 'проверка_знаний'].forEach(v => {
            assertTrue(sel[0].indexOf('value="' + v + '"') === -1,
                'опция «' + v + '» убрана из мероприятий');
        });
    });"""),
])

# ---------------------------------------------------------------- 405
patch('test-task405.js', [
    ("""    test('форма: prefillType — тип по умолчанию из кнопки входа', () => {
        const fn = stripComments(methodText(INDEX_SRC, 'openTrainingForm'));
        assertTrue(fn.indexOf('editTraining, prefillType') !== -1,
            '4-й аргумент prefillType');
        assertTrue(fn.indexOf("preTip === 'инструктаж'") !== -1 &&
                   fn.indexOf("preTip === 'обучение'") !== -1,
            'валидация переданного типа (фолбэк — инструктаж)');""",
     """    test('форма: prefillType — режим/тип по умолчанию из кнопки входа', () => {
        const fn = stripComments(methodText(INDEX_SRC, 'openTrainingForm'));
        assertTrue(fn.indexOf('editTraining, prefillType') !== -1,
            '4-й аргумент prefillType');
        // Task 410: instr-типы → instr-режим (select «Список_И_и_ПЗ»),
        // мероприятие — обучение/прогул/примечание, фолбэк «обучение»
        assertTrue(fn.indexOf('this._trInstrMode = this._isInstrType(preTip);') !== -1,
            'instr-режим из prefillType (Task 410)');
        assertTrue(fn.indexOf("preTip === 'обучение'") !== -1,
            'валидация переданного типа мероприятия');"""),
])

# ---------------------------------------------------------------- 408
patch('test-task408.js', [
    ("""        assertTrue(sf.indexOf('var useSel = this._isInstrType(tip) &&') !== -1 &&
                   sf.indexOf('(this._INSTR_LIST || []).length > 0;') !== -1,
            'select только для инструктажа/ПЗ с шаблоном');""",
     """        assertTrue(sf.indexOf('var useSel = !!this._trInstrMode &&') !== -1 &&
                   sf.indexOf('(this._INSTR_LIST || []).length > 0;') !== -1,
            'select только в instr-режиме с шаблоном (Task 410)');"""),
    ("""        assertTrue(sm.indexOf('var tema = (this._isInstrType(tip) && trSel && !trSel.hidden)') !== -1,
            'submit читает тему из select');""",
     """        assertTrue(sm.indexOf('var tema = (this._trInstrMode && trSel && !trSel.hidden)') !== -1,
            'submit читает тему из select');"""),
    ("""describe('Task 408 — VM: форма (select по типу)', () => {""",
     """describe('Task 408 — VM: форма (select «Список_И_и_ПЗ»)', () => {"""),
    # formHost: явный режим (Task 410)
    ("""    function formHost(tip, tpl) {
        const els = {
            wsTrType: { value: tip },""",
     """    // Task 410: режим формы задаётся явно (instr = select всех
    // пунктов «Список_И_и_ПЗ»; tip больше не влияет)
    function formHost(tip, tpl, mode) {
        const els = {
            wsTrType: { value: tip },"""),
    ("""            '_plural: function(n, f) { return f[2]; },' +
            '_INSTR_LIST: ' + JSON.stringify(tpl === undefined ? TPL : tpl) +
            '});')(mockDoc(els));
        return { host: host, els: els };
    }

    test('инструктаж: select показан, ввод скрыт, пункты вида', () => {
        const c = formHost('инструктаж');
        c.host._syncTrTitleField();
        assertTrue(c.els.wsTrTitleSel.hidden === false, 'select виден');
        assertTrue(c.els.wsTrTitle.hidden === true, 'текстовый ввод скрыт');
        const h = c.els.wsTrTitleSel.innerHTML;
        assertTrue(h.indexOf('value="">— выберите из списка —') !== -1,
            'пустой пункт');
        assertTrue(h.indexOf('value="Охрана труда"') !== -1 &&
                   h.indexOf('value="Пожарная безопасность"') !== -1,
            'пункты вида «инструктаж»');
        assertTrue(h.indexOf('Электробезопасность') === -1,
            'ПЗ-пункт не предлагается');
        assertEqual('', c.els.wsTrTitleSel.value, 'по умолчанию — не выбрано');
    });

    test('проверка знаний (пробел в типе): только ПЗ-пункты', () => {
        const c = formHost('проверка знаний');
        c.host._syncTrTitleField();
        const h = c.els.wsTrTitleSel.innerHTML;
        assertTrue(h.indexOf('value="Электробезопасность"') !== -1,
            'ПЗ-пункт предложен');
        assertTrue(h.indexOf('Охрана труда') === -1 &&
                   h.indexOf('Пожарная безопасность') === -1,
            'инструктажные пункты не предложены');
    });

    test('обучение: свободный ввод (select скрыт, datalist жив)', () => {
        const c = formHost('обучение');""",
     """            '_plural: function(n, f) { return f[2]; },' +
            '_trInstrMode: ' + (mode === false ? 'false' : 'true') + ',' +
            '_INSTR_LIST: ' + JSON.stringify(tpl === undefined ? TPL : tpl) +
            '});')(mockDoc(els));
        return { host: host, els: els };
    }

    test('instr-режим: select показан, ВСЕ пункты шаблона с группами', () => {
        const c = formHost(null);
        c.host._syncTrTitleField();
        assertTrue(c.els.wsTrTitleSel.hidden === false, 'select виден');
        assertTrue(c.els.wsTrTitle.hidden === true, 'текстовый ввод скрыт');
        const h = c.els.wsTrTitleSel.innerHTML;
        assertTrue(h.indexOf('value="">— выберите из списка —') !== -1,
            'пустой пункт');
        assertTrue(h.indexOf('<optgroup label="Инструктажи">') !== -1 &&
                   h.indexOf('<optgroup label="Проверка знаний">') !== -1,
            'группы по виду (Task 410)');
        assertTrue(h.indexOf('value="Охрана труда"') !== -1 &&
                   h.indexOf('value="Пожарная безопасность"') !== -1 &&
                   h.indexOf('value="Электробезопасность"') !== -1,
            'ВСЕ пункты шаблона — инструктажи и ПЗ одним списком');
        assertEqual('', c.els.wsTrTitleSel.value, 'по умолчанию — не выбрано');
    });

    test('группы: инструктажи и ПЗ разделены по видам', () => {
        const c = formHost(null);
        c.host._syncTrTitleField();
        const h = c.els.wsTrTitleSel.innerHTML;
        const gi = h.indexOf('<optgroup label="Инструктажи">');
        const gp = h.indexOf('<optgroup label="Проверка знаний">');
        assertTrue(gi !== -1 && gp !== -1 && gi < gp, 'обе группы по порядку');
        const segI = h.slice(gi, gp);
        assertTrue(segI.indexOf('value="Охрана труда"') !== -1 &&
                   segI.indexOf('value="Пожарная безопасность"') !== -1,
            'инструктажи — в своей группе');
        assertTrue(segI.indexOf('Электробезопасность') === -1,
            'ПЗ-пункт не в группе инструктажей');
        assertTrue(h.slice(gp).indexOf('value="Электробезопасность"') !== -1,
            'ПЗ-пункт — в своей группе');
    });

    test('event-режим: свободный ввод (select скрыт, datalist жив)', () => {
        const c = formHost('обучение', undefined, false);"""),
    ("""    test('шаблона нет — деградация в свободный ввод', () => {
        const c = formHost('инструктаж', []);""",
     """    test('шаблона нет — деградация в свободный ввод', () => {
        const c = formHost(null, []);"""),
    ("""    test('правка: тема совпала (регистр/пробелы) — пункт выбран', () => {
        const c = formHost('инструктаж');""",
     """    test('правка: тема совпала (регистр/пробелы) — пункт выбран', () => {
        const c = formHost(null);"""),
    ("""    test('правка: тема «вне списка» — отдельный пункт, значение сохранено', () => {
        const c = formHost('инструктаж');""",
     """    test('правка: тема «вне списка» — отдельный пункт, значение сохранено', () => {
        const c = formHost(null);"""),
    ("""    test('подсказка пункта: периодичность + основание', () => {
        const c = formHost('инструктаж');""",
     """    test('подсказка пункта: периодичность + основание', () => {
        const c = formHost(null);"""),
    ("""    test('подсказка: разовый пункт без основания — строка скрыта', () => {
        const c = formHost('инструктаж');""",
     """    test('подсказка: разовый пункт без основания — строка скрыта', () => {
        const c = formHost(null);"""),
])

# ---------------------------------------------------------------- 409
patch('test-task409.js', [
    ("""            '_INSTR_LIST: ' + JSON.stringify(FIVE) +
            '});')(mockDoc(els));""",
     """            '_trInstrMode: true,' +
            '_INSTR_LIST: ' + JSON.stringify(FIVE) +
            '});')(mockDoc(els));"""),
    ("""    test('инструктаж: select предлагает только 2 пункта вида', () => {
        const c = formHost('инструктаж');
        c.host._syncTrTitleField();
        const h = c.els.wsTrTitleSel.innerHTML;
        assertEqual(2, (h.match(/<option value="/g) || []).length - 1,
            '2 пункта вида (+ пустой)');
        assertTrue(h.indexOf('Повторный инструктаж по рабочим инструкциям ОТ') !== -1 &&
                   h.indexOf('Повторный инструктаж по инструкции № 9-ОГЭ') !== -1,
            'оба инструктажа');
        assertTrue(h.indexOf('Периодическая проверка знаний') === -1,
            'проверки знаний не предложены');
    });

    test('проверка знаний: select предлагает 3 пункта вида', () => {
        const c = formHost('проверка_знаний');
        c.host._syncTrTitleField();
        const h = c.els.wsTrTitleSel.innerHTML;
        assertEqual(3, (h.match(/<option value="/g) || []).length - 1,
            '3 пункта вида (+ пустой)');
        assertTrue(h.indexOf('при выполнении работ на высоте') !== -1,
            'высота предложена');
        assertTrue(h.indexOf('Повторный инструктаж') === -1,
            'инструктажи не предложены');
    });""",
     """    test('select предлагает ВСЕ 5 пунктов эталона с группами', () => {
        const c = formHost(null);
        c.host._syncTrTitleField();
        const h = c.els.wsTrTitleSel.innerHTML;
        assertEqual(5, (h.match(/<option value="/g) || []).length - 1,
            '5 пунктов эталона (+ пустой)');
        assertTrue(h.indexOf('Повторный инструктаж по рабочим инструкциям ОТ') !== -1 &&
                   h.indexOf('Повторный инструктаж по инструкции № 9-ОГЭ') !== -1 &&
                   h.indexOf('Периодическая проверка знаний на допуск к самостоятельной работе') !== -1,
            'пункты заявки 409');
        assertTrue(h.indexOf('<optgroup label="Инструктажи">') !== -1 &&
                   h.indexOf('<optgroup label="Проверка знаний">') !== -1,
            'группы по виду (Task 410)');
    });

    test('группа «Проверка знаний» — 3 пункта эталона', () => {
        const c = formHost(null);
        c.host._syncTrTitleField();
        const h = c.els.wsTrTitleSel.innerHTML;
        const gp = h.indexOf('<optgroup label="Проверка знаний">');
        assertTrue(gp !== -1, 'группа ПЗ есть');
        assertEqual(3, (h.slice(gp).match(/<option value="/g) || []).length,
            '3 ПЗ-пункта в своей группе');
        assertTrue(h.slice(gp).indexOf('при выполнении работ на высоте') !== -1,
            'высота предложена');
    });"""),
])

# ---------------------------------------------------------------- 309
patch('test-task309.js', [
    ("""        assertTrue(otf.indexOf("sheetTitle.textContent = 'Правка мероприятия'") !== -1,
            'заголовок в режиме правки');""",
     """        assertTrue(otf.indexOf(": 'Правка мероприятия'") !== -1,
            'заголовок в режиме правки (мероприятие; Task 410 — тернарник)');"""),
    ("""        assertTrue(otf.indexOf("sheetTitle.textContent = 'Новое мероприятие'") !== -1,
            'заголовок в режиме создания');""",
     """        assertTrue(otf.indexOf("sheetTitle.textContent = this._trInstrMode") !== -1 &&
                   otf.indexOf("'Новое мероприятие'") !== -1,
            'заголовок в режиме создания (Task 410 — режимы шторки)');"""),
])

# --------------------------------------------------------- work-events
patch('test-work-events.js', [
    ("""        assertTrue(INDEX_SRC.indexOf("sheetTitle.textContent = 'Правка мероприятия'") !== -1,
            'режим правки меняет заголовок шторки');""",
     """        assertTrue(INDEX_SRC.indexOf("sheetTitle.textContent = this._trInstrMode") !== -1 &&
                   INDEX_SRC.indexOf("'Правка мероприятия'") !== -1,
            'режим правки меняет заголовок шторки (Task 410 — тернарник)');"""),
])

# ------------------------------------------------------- work-schedule
patch('test-work-schedule.js', [
    ("""        assertTrue(pop.indexOf('this.openTrainingForm(tabNo, date);') !== -1,
            '«+ Мероприятие…» попапа открывает шторку с префиллом');""",
     """        assertTrue(pop.indexOf("this.openTrainingForm(tabNo, date, null, 'обучение');") !== -1,
            '«+ Мероприятие…» попапа открывает шторку с префиллом (Task 410: дефолт «обучение»)');"""),
])

print('OK')
