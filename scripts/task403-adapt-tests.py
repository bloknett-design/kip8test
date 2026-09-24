#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 403: адаптация существующих тестов под изменения заявки
#   - test-task402.js: _empPosLine (без группы, «р.»), gridHost
#     +_shortGrade; SRC listEmployees/addEmployee — новые маркеры
#   - test-task392.js: СИЗ-тесты — asBlocks blocks[3] (страница
#     «Работники»; попап больше СИЗ не показывает)
#   - test-task396.js: легаси-вызов без asBlocks — 4 действия (не 5),
#     попап — БЕЗ секции СИЗ
#   - test-task395.js: колонки — левая (профиль+отпуска), правая
#     (мероприятия НАД СИЗ)
#   - test-work-schedule.js: формулировки сообщений _empPosLine
#   - test-task388.js: ширина ярлыков через var(--ws-wtabs-w, 236px)
#   - run-all.js: +test-task403.js

import io


def patch(path, edits):
    src = io.open(path, encoding='utf-8').read()
    for i, (old, new) in enumerate(edits):
        n = src.count(old)
        assert n == 1, '%s PATCH %d: вхождений %d: %r' % (path, i, n, old[:70])
        src = src.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('%s: правок %d' % (path, len(edits)))


# ============================================================
# test-task402.js
# ============================================================
patch('tests/test-task402.js', [

    # gridHost: + _shortGrade (нужен _empPosLine после Task 403)
    (
        """function gridHost() {
    return new Function('return ({' +
        methodText(INDEX_SRC, '_empPosLine') + ',' +
        methodText(INDEX_SRC, '_empTipLine') +
        '});')();
}""",
        """function gridHost() {
    return new Function('return ({' +
        methodText(INDEX_SRC, '_empPosLine') + ',' +
        methodText(INDEX_SRC, '_shortGrade') + ',' +
        methodText(INDEX_SRC, '_empTipLine') +
        '});')();
}""",
    ),

    # SRC: сообщение (должность без группы — Task 403)
    (
        """        assertTrue(fn.indexOf("var empPosLabel = this._empPosLine(emp);") !== -1,
            'строка должности (с группой) — _empPosLine');""",
        """        assertTrue(fn.indexOf("var empPosLabel = this._empPosLine(emp);") !== -1,
            'строка должности — _empPosLine (Task 403: без группы, «разряд» → «р.»)');""",
    ),

    # VM: _empPosLine — новое поведение (Task 403)
    (
        """    test('_empPosLine: должность · группа (данные группы ПОСЛЕ должности)', () => {
        const h = gridHost();
        assertEqual(h._empPosLine({ 'должность': 'Слесарь КИПиА', 'группа_допуска': 'IV' }),
            'Слесарь КИПиА · IV', 'должность + группа через «·»');
        assertEqual(h._empPosLine({ 'должность': 'Слесарь КИПиА' }), 'Слесарь КИПиА',
            'без группы — только должность');
        assertEqual(h._empPosLine({ 'группа_допуска': 'IV' }), 'IV',
            'без должности — только группа');
        assertEqual(h._empPosLine({}), '', 'пусто — строка не рендерится');
    });""",
        """    test('_empPosLine: только должность; «разряд» → «р.» (Task 403)', () => {
        const h = gridHost();
        assertEqual(h._empPosLine({ 'должность': 'Слесарь КИПиА', 'группа_допуска': 'IV' }),
            'Слесарь КИПиА', 'группа допуска из столбца ФИО убрана (Task 403)');
        assertEqual(h._empPosLine({ 'должность': 'Слесарь КИПиА' }), 'Слесарь КИПиА',
            'без группы — должность');
        assertEqual(h._empPosLine({ 'группа_допуска': 'IV' }), '',
            'без должности — пусто (группа не показывается)');
        assertEqual(h._empPosLine({}), '', 'пусто — строка не рендерится');
        assertEqual(h._empPosLine({ 'должность': 'Слесарь КИПиА 5 разряд' }),
            'Слесарь КИПиА 5 р.', '«разряд» сокращён до «р.» (Task 403)');
    });""",
    ),

    # SRC GAS: listEmployees — новые маркеры (заголовки всех столбцов)
    (
        """    test('listEmployees: поле группа_допуска + расширенное чтение', () => {
        const fn = stripComments(methodText(WS_GS_SRC, 'listEmployees'));
        assertTrue(fn.indexOf('var groupCol = this._accessGroupColIndex(sheet);') !== -1,
            'столбец ищется по заголовку');
        assertTrue(fn.indexOf('groupCol + 1 > 11') !== -1,
            'чтение расширено до найденного столбца (не уже A..K)');
        assertTrue(fn.indexOf('группа_допуска:') !== -1 &&
                   fn.indexOf('(groupCol !== null)') !== -1,
            'поле в ответе; нет столбца — пустая строка');
    });""",
        """    test('listEmployees: поле группа_допуска + расширенное чтение', () => {
        const fn = stripComments(methodText(WS_GS_SRC, 'listEmployees'));
        assertTrue(fn.indexOf('var groupCol = this._accessGroupColIndex(sheet);') !== -1,
            'столбец ищется по заголовку');
        // Task 403: должность/комментарий — тоже по заголовкам
        assertTrue(fn.indexOf("this._headerColIndex(sheet, ['должность'])") !== -1 &&
                   fn.indexOf("this._headerColIndex(sheet, ['комментарий'])") !== -1,
            'должность/комментарий — по заголовкам строки 1 (баг комментария)');
        assertTrue(fn.indexOf('var readWidth = 11;') !== -1 &&
                   fn.indexOf('groupCol + 1 > readWidth') !== -1,
            'чтение расширено до самого правого найденного столбца');
        assertTrue(fn.indexOf('группа_допуска:') !== -1 &&
                   fn.indexOf('(groupCol !== null)') !== -1,
            'поле в ответе; нет столбца — пустая строка');
    });""",
    ),

    # SRC GAS: addEmployee — новые маркеры сборки строки
    (
        """    test('addEmployee: группа в новой строке листа', () => {
        const fn = stripComments(methodText(WS_GS_SRC, 'addEmployee'));
        assertTrue(fn.indexOf('while (rowVals.length <= groupCol) rowVals.push(\\'\\');') !== -1,
            'строка дополнена пустыми до столбца группы');
        assertTrue(fn.indexOf('rowVals[groupCol] = accessGroup;') !== -1,
            'группа записана в найденный столбец');
    });""",
        """    test('addEmployee: группа в новой строке листа', () => {
        const fn = stripComments(methodText(WS_GS_SRC, 'addEmployee'));
        // Task 403: строка — до самого правого столбца, реквизиты —
        // каждый в свой (прежде фикс J..K затирал комментарий группой)
        assertTrue(fn.indexOf('while (rowVals.length < rowWidth) rowVals.push(\\'\\');') !== -1,
            'строка дополнена пустыми до самого правого столбца');
        assertTrue(fn.indexOf('rowVals[posCol] = position;') !== -1 &&
                   fn.indexOf('rowVals[comCol] = comment;') !== -1,
            'должность и комментарий — каждый в свой столбец');
        assertTrue(fn.indexOf('rowVals[groupCol] = accessGroup;') !== -1,
            'группа записана в найденный столбец');
    });""",
    ),
])

# ============================================================
# test-task392.js — СИЗ-тесты: asBlocks blocks[3] (страница)
# ============================================================
patch('tests/test-task392.js', [

    (
        """    test('записи работника с мета-строкой (выдано/срок/до)', () => {
        const host = cardHost(true, PPE);
        const html = host._renderWorkerCard('2706', true);
        assertTrue(html.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'заголовок секции');""",
        """    test('записи работника с мета-строкой (выдано/срок/до)', () => {
        const host = cardHost(true, PPE);
        // Task 403: СИЗ — только страница «Работники» (asBlocks)
        const html = host._renderWorkerCard('2706', true, true)[3];
        assertTrue(html.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'заголовок секции');""",
    ),

    (
        """    test('не выдано / До износа / примечание', () => {
        const host = cardHost(true, PPE);
        const html = host._renderWorkerCard('2706', true);
        assertTrue(html.indexOf('не выдано') !== -1, 'без даты выдачи — «не выдано»');""",
        """    test('не выдано / До износа / примечание', () => {
        const host = cardHost(true, PPE);
        const html = host._renderWorkerCard('2706', true, true)[3];
        assertTrue(html.indexOf('не выдано') !== -1, 'без даты выдачи — «не выдано»');""",
    ),

    (
        """    test('кнопки ✎/✕ у записей с id — только редакторам', () => {
        const host = cardHost(true, PPE);
        const html = host._renderWorkerCard('2706', true);
        assertTrue(html.indexOf('WorkSchedule.editPpe(1)') !== -1, '✎ запись 1');""",
        """    test('кнопки ✎/✕ у записей с id — только редакторам', () => {
        const host = cardHost(true, PPE);
        const html = host._renderWorkerCard('2706', true, true)[3];
        assertTrue(html.indexOf('WorkSchedule.editPpe(1)') !== -1, '✎ запись 1');""",
    ),

    (
        """    test('зритель — без кнопок, записи видны', () => {
        const host = cardHost(true, PPE);
        const html = host._renderWorkerCard('2706', false);
        assertTrue(html.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'секция видна зрителю');""",
        """    test('зритель — без кнопок, записи видны', () => {
        const host = cardHost(true, PPE);
        const html = host._renderWorkerCard('2706', false, true)[3];
        assertTrue(html.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'секция видна зрителю');""",
    ),

    (
        """    test('пустой список СИЗ — «нет выданных СИЗ»', () => {
        const host = cardHost(true, []);
        const html = host._renderWorkerCard('2706', true);
        assertTrue(html.indexOf('нет выданных СИЗ') !== -1, 'пустое состояние');""",
        """    test('пустой список СИЗ — «нет выданных СИЗ»', () => {
        const host = cardHost(true, []);
        const html = host._renderWorkerCard('2706', true, true)[3];
        assertTrue(html.indexOf('нет выданных СИЗ') !== -1, 'пустое состояние');""",
    ),

    (
        """    test('запись БЕЗ id (ручная строка листа) — без кнопок', () => {
        const host = cardHost(true, [
            { id: null, 'таб_номер': '2706', наименование: 'Перчатки',
              дата_выдачи: '', срок_годности: '', дата_окончания: '', примечание: '' },
        ]);
        const html = host._renderWorkerCard('2706', true);
        assertTrue(html.indexOf('Перчатки') !== -1, 'запись видна');""",
        """    test('запись БЕЗ id (ручная строка листа) — без кнопок', () => {
        const host = cardHost(true, [
            { id: null, 'таб_номер': '2706', наименование: 'Перчатки',
              дата_выдачи: '', срок_годности: '', дата_окончания: '', примечание: '' },
        ]);
        const html = host._renderWorkerCard('2706', true, true)[3];
        assertTrue(html.indexOf('Перчатки') !== -1, 'запись видна');""",
    ),
])

# ============================================================
# test-task396.js — легаси-вызов и попап: БЕЗ СИЗ (Task 403)
# ============================================================
patch('tests/test-task396.js', [

    (
        """    test('легаси-вызов (без asBlocks): прежние строки внизу, БЕЗ whead/зебры', () => {
        const h = cardHost(true);
        const html = h._renderWorkerCard('2706', true);
        assertTrue(html.indexOf('ws-popup-row ws-popup-more ws-emp-editdata') !== -1 &&
                   html.indexOf('ws-popup-row ws-popup-more ws-emp-dismiss') !== -1 &&
                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addvac') !== -1 &&
                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addtr') !== -1 &&
                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addppe') !== -1,
            'пять строк-действий — прежний вид (попап-совместимость)');
        assertTrue(html.indexOf('ws-whead') === -1 &&
                   html.indexOf('ws-wbtn') === -1 &&
                   html.indexOf('ws-row-alt') === -1,
            'без asBlocks — НЕТ шапок-полос/кнопок/зебры');
        assertTrue(html.indexOf('Правка данных…</div>') !== -1,
            'легаси-текст строки (div, не button)');
    });""",
        """    test('легаси-вызов (без asBlocks): прежние строки внизу, БЕЗ whead/зебры', () => {
        const h = cardHost(true);
        const html = h._renderWorkerCard('2706', true);
        // Task 403: «+ СИЗ…» из попапа убран — действий четыре
        assertTrue(html.indexOf('ws-popup-row ws-popup-more ws-emp-editdata') !== -1 &&
                   html.indexOf('ws-popup-row ws-popup-more ws-emp-dismiss') !== -1 &&
                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addvac') !== -1 &&
                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addtr') !== -1,
            'четыре строки-действия — прежний вид (попап-совместимость)');
        assertTrue(html.indexOf('ws-emp-addppe') === -1,
            '«+ СИЗ…» в попапе НЕТ (Task 403 — СИЗ только на странице)');
        assertTrue(html.indexOf('ws-whead') === -1 &&
                   html.indexOf('ws-wbtn') === -1 &&
                   html.indexOf('ws-row-alt') === -1,
            'без asBlocks — НЕТ шапок-полос/кнопок/зебры');
        assertTrue(html.indexOf('Правка данных…</div>') !== -1,
            'легаси-текст строки (div, не button)');
    });""",
    ),

    (
        """    test('попап шахматки (withEdit=false, без asBlocks) — прежний вид', () => {
        const h = cardHost(false);
        const html = h._renderWorkerCard('2706', false);
        assertTrue(html.indexOf('<div class="ws-popup-title">Галкин Д. Н.') !== -1,
            'шапка ФИО — прежний .ws-popup-title');
        assertTrue(html.indexOf('<div class="ws-popup-sec">Отпуска · 2026') !== -1 &&
                   html.indexOf('<div class="ws-popup-sec">СИЗ · средства индивидуальной защиты') !== -1,
            'секции — прежние .ws-popup-sec');
        assertTrue(html.indexOf('ws-whead') === -1 && html.indexOf('ws-row-alt') === -1,
            'попап — БЕЗ зебры и шапок-полос (компактная типографика)');
    });""",
        """    test('попап шахматки (withEdit=false, без asBlocks) — прежний вид', () => {
        const h = cardHost(false);
        const html = h._renderWorkerCard('2706', false);
        assertTrue(html.indexOf('<div class="ws-popup-title">Галкин Д. Н.') !== -1,
            'шапка ФИО — прежний .ws-popup-title');
        assertTrue(html.indexOf('<div class="ws-popup-sec">Отпуска · 2026') !== -1,
            'секции отпусков/мероприятий — прежние .ws-popup-sec');
        // Task 403 (заявка): данные СИЗ из попапа УБРАНЫ
        assertTrue(html.indexOf('СИЗ') === -1,
            'секции СИЗ в попапе НЕТ (только на странице «Работники»)');
        assertTrue(html.indexOf('ws-whead') === -1 && html.indexOf('ws-row-alt') === -1,
            'попап — БЕЗ зебры и шапок-полос (компактная типографика)');
    });""",
    ),
])

# ============================================================
# test-task395.js — колонки: мероприятия НАД СИЗ (Task 403)
# ============================================================
patch('tests/test-task395.js', [

    (
        """    test('_renderWorkerCardPanels — левая колонка (1–3) + правая СИЗ', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf("if (bi < 3) left += panel; else right += panel;") !== -1,
            'блоки 1–3 (профиль/отпуска/мероприятия) — в ЛЕВУЮ, 4 (СИЗ) — в ПРАВУЮ');""",
        """    test('_renderWorkerCardPanels — левая (профиль/отпуска) + правая (мероприятия/СИЗ)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        // Task 403: мероприятия — в верх ПРАВОЙ колонки (между
        // профилем и СИЗ); было bi < 3 (все три слева)
        assertTrue(fn.indexOf("if (bi < 2) left += panel; else right += panel;") !== -1,
            'блоки 1–2 (профиль/отпуска) — в ЛЕВУЮ, 3–4 (мероприятия/СИЗ) — в ПРАВУЮ');""",
    ),

    (
        """    test('левая колонка: профиль → отпуска → мероприятия; правая: СИЗ', () => {
        const t = pageHost({ canEdit: true });
        const html = t.host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iR = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        assertTrue(iL !== -1 && iR !== -1 && iL < iR,
            'две колонки: левая, затем правая (СИЗ)');
        // СИЗ — В ПРАВОЙ колонке (после её открытия)
        const rightPart = html.slice(iR);
        assertTrue(rightPart.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'СИЗ — в правой колонке');
        assertTrue(rightPart.indexOf('Каска защитная') !== -1,
            'запись СИЗ — в правой колонке');
        // левая — три блока
        const leftPart = html.slice(iL, iR);
        assertTrue((leftPart.match(/class="ws-wcard"/g) || []).length === 3,
            'в левой колонке — 3 окна (профиль/отпуска/мероприятия)');
        assertTrue((rightPart.match(/class="ws-wcard"/g) || []).length === 1,
            'в правой колонке — 1 окно (СИЗ)');
        const i1 = leftPart.indexOf('Галкин Д. Н.');
        const i2 = leftPart.indexOf('Отпуска · 2026');
        const i3 = leftPart.indexOf('Мероприятия · 2026');
        assertTrue(i1 !== -1 && i2 !== -1 && i3 !== -1 && i1 < i2 && i2 < i3,
            'порядок левой колонки: профиль → отпуска → мероприятия');
    });""",
        """    test('левая: профиль → отпуска; правая: мероприятия → СИЗ (Task 403)', () => {
        const t = pageHost({ canEdit: true });
        const html = t.host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iR = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        assertTrue(iL !== -1 && iR !== -1 && iL < iR,
            'две колонки: левая, затем правая');
        // Task 403: правая — мероприятия (верх) + СИЗ (низ)
        const rightPart = html.slice(iR);
        const iTr = rightPart.indexOf('Мероприятия · 2026');
        const iPz = rightPart.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(iTr !== -1 && iPz !== -1 && iTr < iPz,
            'мероприятия — ВВЕРХУ правой колонки, НАД СИЗ');
        assertTrue(rightPart.indexOf('Каска защитная') !== -1,
            'запись СИЗ — в правой колонке');
        // левая — два блока
        const leftPart = html.slice(iL, iR);
        assertTrue((leftPart.match(/class="ws-wcard"/g) || []).length === 2,
            'в левой колонке — 2 окна (профиль/отпуска)');
        assertTrue((rightPart.match(/class="ws-wcard"/g) || []).length === 2,
            'в правой колонке — 2 окна (мероприятия/СИЗ)');
        const i1 = leftPart.indexOf('Галкин Д. Н.');
        const i2 = leftPart.indexOf('Отпуска · 2026');
        assertTrue(i1 !== -1 && i2 !== -1 && i1 < i2,
            'порядок левой колонки: профиль → отпуска');
        // мероприятия — МЕЖДУ блоками профиля и СИЗ (по DOM правой)
        const iProf = html.indexOf('Галкин Д. Н.');
        assertTrue(iProf < iTr && iTr < iPz,
            'визуальный порядок: профиль → мероприятия → СИЗ');
    });""",
    ),

    # Сообщение теста страницы (правая колонка = мероприятия+СИЗ)
    (
        """        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-ppe">') !== -1,
            'правая колонка СИЗ — на странице');""",
        """        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-ppe">') !== -1,
            'правая колонка (мероприятия + СИЗ) — на странице');""",
    ),
])

# ============================================================
# test-work-schedule.js — формулировки _empPosLine (Task 403)
# ============================================================
patch('tests/test-work-schedule.js', [

    (
        """                'Подпись в .ws-emp-pos формируется через _empPosLine (должность + группа)');""",
        """                'Подпись в .ws-emp-pos формируется через _empPosLine (Task 403: должность, без группы)');""",
    ),

    (
        """                'Тернарник: без должности И группы нет пустого блока .ws-emp-pos');""",
        """                'Тернарник: без должности нет пустого блока .ws-emp-pos');""",
    ),

    (
        """            // в ШАХМАТКЕ тип работника — ТРЕТЬЯ строка (_empTipLine),
            // строка должности — _empPosLine (должность · группа);""",
        """            // в ШАХМАТКЕ тип работника — ТРЕТЬЯ строка (_empTipLine),
            // строка должности — _empPosLine (Task 403: только
            // должность, «разряд» → «р.», без группы допуска);""",
    ),
])

# ============================================================
# test-task388.js — ширина ярлыков через переменную (Task 403)
# ============================================================
patch('tests/test-task388.js', [

    (
        """        assertTrue(chunk.indexOf('flex-direction: column') !== -1 &&
                   chunk.indexOf('width: 236px') !== -1,
            'ярлыки — вертикальная колонка слева');""",
        """        assertTrue(chunk.indexOf('flex-direction: column') !== -1 &&
                   chunk.indexOf('width: var(--ws-wtabs-w, 236px)') !== -1,
            'ярлыки — вертикальная колонка слева (Task 403: ширина по самому длинному тексту, 236px — фолбэк)');""",
    ),
])

# ============================================================
# run-all.js — подключение test-task403.js
# ============================================================
patch('tests/run-all.js', [

    (
        """// Task 402 — тип работника третьей строкой ячейки сетки; «группа_допуска»
// (ячейка/карточка/сводная/шторка правки; GAS — столбец по заголовку)
require('./test-task402.js');
require('./test-deploy-url.js');""",
        """// Task 402 — тип работника третьей строкой ячейки сетки; «группа_допуска»
// (ячейка/карточка/сводная/шторка правки; GAS — столбец по заголовку)
require('./test-task402.js');
// Task 403 — «разряд» → «р.» и БЕЗ группы допуска в столбце ФИО; попап
// без СИЗ; GAS-фикс бага комментария (столбцы по заголовкам); ярлыки
// «Работников» по самому длинному тексту; мероприятия над СИЗ
require('./test-task403.js');
require('./test-deploy-url.js');""",
    ),
])

print('OK: все тест-файлы адаптированы')
