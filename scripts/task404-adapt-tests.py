#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 404: адаптация существующих тестов под изменения заявки
#   - test-task394.js: окно мероприятий — отпуска УДАЛЕНЫ (плашки/точки/
#     сборка/VM-секции/порядок/прошедшие); DOM-порядок панели страницы
#   - test-task399.js: фильтр мастеров — двухсекционный (мероприятия/СИЗ)
#   - test-task393.js: порядок панелей (СИЗ — 2-я колонка, мероприятия — 3-я)
#   - test-task395.js: ТРИ колонки (main/СИЗ/мероприятия)
#   - test-task403.js: панели — три колонки (СИЗ слева от мероприятий)
#   - run-all.js: +test-task404.js

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
# test-task394.js — окно мероприятий: отпуска УДАЛЕНЫ (Task 404)
# ============================================================
patch('tests/test-task394.js', [

    # 1) плашки секций — только СИЗ
    (
        """    test('окно мероприятий: плашки секций «Отпуска»/«СИЗ» и точки', () => {
        const vac = ruleBlock('.ws-ep-cap-vac {');
        const ppe = ruleBlock('.ws-ep-cap-ppe {');
        assertTrue(vac !== null && ppe !== null, 'плашки секций живы');
        assertTrue(INDEX_SRC.indexOf('.ws-ep-dot-vac { background: #90a4ae; }') !== -1,
            'точка отпуска — читаемый тон обеих тем');
        assertTrue(INDEX_SRC.indexOf('.ws-ep-dot-ppe { background: #f0a830; }') !== -1,
            'точка СИЗ — янтарная');
        const re = /\\[data-theme="light"\\] \\.ws-ep-cap-vac,\\s*\\n\\s*\\[data-theme="light"\\] \\.ws-ep-cap-ppe \\{[^}]*?color: #000;[^}]*?\\}/;
        assertTrue(re.test(INDEX_SRC),
            'светлая тема: текст плашек — чёрный (Task 330)');
    });""",
        """    test('окно мероприятий: плашка секции «СИЗ» (отпуска убраны — Task 404)', () => {
        const ppe = ruleBlock('.ws-ep-cap-ppe {');
        assertTrue(ppe !== null, 'плашка секции СИЗ жива');
        assertTrue(ruleBlock('.ws-ep-cap-vac {') === null,
            'плашка секции «Отпуска» УДАЛЕНА (Task 404)');
        assertFalse(INDEX_SRC.indexOf('.ws-ep-dot-vac') !== -1,
            'точки отпуска больше нет');
        assertTrue(INDEX_SRC.indexOf('.ws-ep-dot-ppe { background: #f0a830; }') !== -1,
            'точка СИЗ — янтарная');
        const re = /\\[data-theme="light"\\] \\.ws-ep-cap-ppe \\{[^}]*?color: #000;[^}]*?\\}/;
        assertTrue(re.test(INDEX_SRC),
            'светлая тема: текст плашки — чёрный (Task 330)');
    });""",
    ),

    # 2) _renderMonthEventsPanel — секции
    (
        """    test('_renderMonthEventsPanel — секции отпусков и СИЗ', () => {
        const m = methodText(INDEX_SRC, '_renderMonthEventsPanel');
        assertTrue(m.indexOf('this._VACATIONS || []') !== -1,
            'защитный доступ к отпускам (харнессы без поля)');
        assertTrue(m.indexOf('this._PPE || []') !== -1,
            'защитный доступ к СИЗ');
        assertTrue(m.indexOf('vE < mStart || vS > mEnd') !== -1,
            'отпуск попадает при ПЕРЕСЕЧЕНИИ месяца (как мероприятия)');
        assertTrue(m.indexOf('pExpIso < mStart || pExpIso > mEnd') !== -1,
            'СИЗ — дата_окончания ВНУТРИ месяца');
        assertTrue(m.indexOf("pExpIso === 'До износа'") !== -1,
            '«До износа» — без даты, не показывается');
        assertTrue(m.indexOf('Отпуска · ') !== -1 && m.indexOf('СИЗ · ') !== -1,
            'заголовки секций');
        assertTrue(m.indexOf('ws-ep-dot-vac') !== -1 && m.indexOf('ws-ep-dot-ppe') !== -1,
            'точки секций');
        assertTrue(m.indexOf("'Отпуск · ' + vFio") !== -1 &&
                   m.indexOf("'СИЗ · ' + String(ppz['наименование']") !== -1,
            'тексты строк секций');
        assertTrue(m.indexOf('pExpIso !== selIso') !== -1,
            'режим выбранного дня: СИЗ — истекающие ровно в день');
        assertTrue(m.indexOf('vacList.length') !== -1 && m.indexOf('ppeList.length') !== -1,
            'счётчики секций');
    });""",
        """    test('_renderMonthEventsPanel — секция СИЗ (отпуска убраны — Task 404)', () => {
        const m = methodText(INDEX_SRC, '_renderMonthEventsPanel');
        assertFalse(m.indexOf('vacList') !== -1,
            'сборки отпусков больше НЕТ (заявка Task 404)');
        assertFalse(m.indexOf('Отпуска · ') !== -1,
            'заголовка секции «Отпуска» нет');
        assertFalse(m.indexOf('ws-ep-dot-vac') !== -1, 'точки отпусков нет');
        assertTrue(m.indexOf('this._PPE || []') !== -1,
            'защитный доступ к СИЗ');
        assertTrue(m.indexOf('pExpIso < mStart || pExpIso > mEnd') !== -1,
            'СИЗ — дата_окончания ВНУТРИ месяца');
        assertTrue(m.indexOf("pExpIso === 'До износа'") !== -1,
            '«До износа» — без даты, не показывается');
        assertTrue(m.indexOf('СИЗ · ') !== -1,
            'заголовок секции СИЗ');
        assertTrue(m.indexOf('ws-ep-dot-ppe') !== -1,
            'точка секции СИЗ');
        assertTrue(m.indexOf("'СИЗ · ' + String(ppz['наименование']") !== -1,
            'текст строки секции');
        assertTrue(m.indexOf('pExpIso !== selIso') !== -1,
            'режим выбранного дня: СИЗ — истекающие ровно в день');
        assertTrue(m.indexOf('ppeList.length') !== -1,
            'счётчик секции');
    });""",
    ),

    # 3) DOM-порядок панели страницы
    (
        """        // порядок блоков в DOM: профиль → отпуска → мероприятия → СИЗ
        const i1 = body.indexOf('Галкин Д. Н.');
        const i2 = body.indexOf('Отпуска · 2026');
        const i3 = body.indexOf('Мероприятия · 2026');
        const i4 = body.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(i1 < i2 && i2 < i3 && i3 < i4,
            'DOM-порядок = раскладка сетки: профиль|отпуска / мероприятия|СИЗ');""",
        """        // порядок блоков в DOM: профиль → отпуска → СИЗ → мероприятия
        // (Task 404: СИЗ — ВТОРАЯ колонка, слева от мероприятий)
        const i1 = body.indexOf('Галкин Д. Н.');
        const i2 = body.indexOf('Отпуска · 2026');
        const i3 = body.indexOf('Мероприятия · 2026');
        const i4 = body.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(i1 < i2 && i2 < i4 && i4 < i3,
            'DOM-порядок = раскладка: профиль|отпуска / СИЗ / мероприятия');""",
    ),

    # 4) VM-блок «ОТПУСКА» — отпуска больше НЕ показываются
    (
        """describe('Task 394 — VM: окно мероприятий — ОТПУСКА', () => {

    // отпуск ЧАСТИЧНО на два месяца: 29.09–02.10
    const VAC2M = [
        { id: 21, 'таб_номер': '0871', 'часть': 1,
          'дата_начала': '2026-09-29', 'дата_окончания': '2026-10-02',
          'комментарий': '' },
    ];

    test('отпуск через границу — в окне СЕНТЯБРЯ', () => {
        const el = panelHost({ month: 9, vacations: VAC2M });
        assertTrue(el.innerHTML.indexOf('Отпуска · сентябрь 2026 · 1') !== -1,
            'секция «Отпуска» с месяцем и счётчиком');
        assertTrue(el.innerHTML.indexOf('29.09–02.10') !== -1,
            'диапазон через границу месяцев');
        assertTrue(el.innerHTML.indexOf('Отпуск · Иванов Иван Иванович') !== -1,
            'текст строки: Отпуск · ФИО');
        assertTrue(el.innerHTML.indexOf('ws-ep-dot-vac') !== -1,
            'точка отпуска');
    });

    test('тот же отпуск — в окне ОКТЯБРЯ (заявка: обоих месяцев)', () => {
        const el = panelHost({ month: 10, vacations: VAC2M });
        assertTrue(el.innerHTML.indexOf('Отпуска · октябрь 2026 · 1') !== -1,
            'секция «Отпуска» есть и в следующем месяце');
        assertTrue(el.innerHTML.indexOf('29.09–02.10') !== -1,
            'тот же период виден в октябре');
    });

    test('месяц БЕЗ отпусков — секции «Отпуска» нет (скрыта)', () => {
        const el = panelHost({ month: 11, vacations: VAC2M });
        assertFalse(el.innerHTML.indexOf('Отпуска · ') !== -1,
            'ноябрь — отпуск не показывается');
        assertFalse(el.innerHTML.indexOf('· 0') !== -1,
            'нулевого счётчика нет');
    });

    test('без данных об отпусках — секции нет (харнесс без _VACATIONS)', () => {
        const el = panelHost({ month: 9, vacations: [] });
        assertFalse(el.innerHTML.indexOf('Отпуска · ') !== -1,
            'пустой список — секция скрыта');
    });

    test('выбранный день — только НАКРЫВАЮЩИЙ отпуск', () => {
        const vac = [
            { id: 22, 'таб_номер': '0871', 'часть': 1,
              'дата_начала': '2026-09-02', 'дата_окончания': '2026-09-05',
              'комментарий': '' },
        ];
        const el3 = panelHost({ month: 9, selDay: 3, vacations: vac });
        assertTrue(el3.innerHTML.indexOf('Отпуска · 03.09 · 1') !== -1,
            'день 3 накрыт отпуском 02–05.09');
        const el10 = panelHost({ month: 9, selDay: 10, vacations: vac });
        assertFalse(el10.innerHTML.indexOf('Отпуска · ') !== -1,
            'день 10 не накрыт — секция скрыта');
    });
});""",
        """describe('Task 394 → 404 — VM: окно мероприятий — отпуска НЕ показываются', () => {

    // отпуск ЧАСТИЧНО на два месяца: 29.09–02.10
    const VAC2M = [
        { id: 21, 'таб_номер': '0871', 'часть': 1,
          'дата_начала': '2026-09-29', 'дата_окончания': '2026-10-02',
          'комментарий': '' },
    ];

    test('отпуск в месяце — секции «Отпуска» НЕТ (заявка Task 404)', () => {
        const el = panelHost({ month: 9, vacations: VAC2M });
        assertFalse(el.innerHTML.indexOf('Отпуска · ') !== -1,
            'секция «Отпуска» удалена из окна мероприятий');
        assertFalse(el.innerHTML.indexOf('Отпуск · Иванов Иван Иванович') !== -1,
            'строк отпусков нет');
        assertFalse(el.innerHTML.indexOf('ws-ep-dot-vac') !== -1,
            'точек отпусков нет');
        assertFalse(el.innerHTML.indexOf('29.09–02.10') !== -1,
            'диапазонов отпусков нет');
    });

    test('октябрь — тоже без отпусков; выбранный день, накрытый отпуском — тоже', () => {
        const el10 = panelHost({ month: 10, vacations: VAC2M });
        assertFalse(el10.innerHTML.indexOf('Отпуска · ') !== -1,
            'секции «Отпуска» нет и в следующем месяце');
        const vac = [
            { id: 22, 'таб_номер': '0871', 'часть': 1,
              'дата_начала': '2026-09-02', 'дата_окончания': '2026-09-05',
              'комментарий': '' },
        ];
        const el3 = panelHost({ month: 9, selDay: 3, vacations: vac });
        assertFalse(el3.innerHTML.indexOf('Отпуска · ') !== -1,
            'день 3 накрыт отпуском 02–05.09 — но секции нет (Task 404)');
    });
});""",
    ),

    # 5) прошедшие — только строки СИЗ
    (
        """        const el = panelHost({ year: Y, month: M, vacations: vac, ppe: ppe });
        // «1-е число» — прошедшее iff 1-е < сегодня (в этом же месяце)
        const expPast = iso(Y, M, 1) < iso(Y, M, NOW.getDate());
        // строк отпуска — 2, СИЗ — 2; прошедшие из них: оба «1-го числа»
        // (отпуск + СИЗ) iff 1-е < сегодня
        const nPast = (el.innerHTML.match(/ws-ep-past/g) || []).length;
        assertEqual(nPast, expPast ? 2 : 0,
            'классов ws-ep-past столько, сколько строк с прошедшей датой');
        assertEqual((el.innerHTML.match(/<span class="ws-ep-item/g) || []).length, 4,
            'строки: 2 отпуска + 2 СИЗ');""",
        """        const el = panelHost({ year: Y, month: M, vacations: vac, ppe: ppe });
        // «1-е число» — прошедшее iff 1-е < сегодня (в этом же месяце)
        const expPast = iso(Y, M, 1) < iso(Y, M, NOW.getDate());
        // Task 404: отпуска НЕ показываются — в окне только 2 строки
        // СИЗ; прошедшая из них — «1-го числа» iff 1-е < сегодня
        const nPast = (el.innerHTML.match(/ws-ep-past/g) || []).length;
        assertEqual(nPast, expPast ? 1 : 0,
            'классов ws-ep-past столько, сколько СИЗ с прошедшей датой');
        assertEqual((el.innerHTML.match(/<span class="ws-ep-item/g) || []).length, 2,
            'строки: 2 СИЗ (отпуска не показываются — Task 404)');""",
    ),

    # 6) порядок секций: Мероприятия → СИЗ
    (
        """    test('порядок: Мероприятия → Отпуска → СИЗ', () => {
        const el = panelHost({
            month: 9,
            trainings: [{ 'таб_номер': '0871', 'тип': 'инструктаж',
                          'тема': 'Повторный', 'дата_начала': '2026-09-05',
                          'дата_окончания': '2026-09-05' }],
            vacations: [{ 'таб_номер': '0871', 'дата_начала': '2026-09-10',
                          'дата_окончания': '2026-09-20' }],
            ppe: [{ 'таб_номер': '0871', 'наименование': 'Каска защитная',
                    'дата_окончания': '2026-09-25' }],
        });
        const iEv = el.innerHTML.indexOf('Мероприятия · сентябрь 2026');
        const iVac = el.innerHTML.indexOf('Отпуска · сентябрь 2026');
        const iPpe = el.innerHTML.indexOf('СИЗ · сентябрь 2026');
        assertTrue(iEv !== -1 && iVac !== -1 && iPpe !== -1, 'все три секции');
        assertTrue(iEv < iVac && iVac < iPpe, 'порядок: мероприятия → отпуска → СИЗ');
    });""",
        """    test('порядок: Мероприятия → СИЗ (отпуска убраны — Task 404)', () => {
        const el = panelHost({
            month: 9,
            trainings: [{ 'таб_номер': '0871', 'тип': 'инструктаж',
                          'тема': 'Повторный', 'дата_начала': '2026-09-05',
                          'дата_окончания': '2026-09-05' }],
            vacations: [{ 'таб_номер': '0871', 'дата_начала': '2026-09-10',
                          'дата_окончания': '2026-09-20' }],
            ppe: [{ 'таб_номер': '0871', 'наименование': 'Каска защитная',
                    'дата_окончания': '2026-09-25' }],
        });
        const iEv = el.innerHTML.indexOf('Мероприятия · сентябрь 2026');
        const iPpe = el.innerHTML.indexOf('СИЗ · сентябрь 2026');
        assertTrue(iEv !== -1 && iPpe !== -1, 'обе секции');
        assertTrue(iEv < iPpe, 'порядок: мероприятия → СИЗ');
        assertFalse(el.innerHTML.indexOf('Отпуска · сентябрь 2026') !== -1,
            'секции «Отпуска» нет (Task 404)');
    });""",
    ),
])

# ============================================================
# test-task399.js — фильтр мастеров: две секции
# ============================================================
patch('tests/test-task399.js', [

    (
        """    test('фильтр во ВСЕХ трёх секциях — мероприятия/отпуска/СИЗ', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderMonthEventsPanel'));
        assertTrue(fn.indexOf("masterTabs[t['таб_номер']]") !== -1,
            'секция «Мероприятия» — записи мастеров пропускаются');
        assertTrue(fn.indexOf("masterTabs[vRec['таб_номер']]") !== -1,
            'секция «Отпуска» — отпуска мастеров пропускаются');
        assertTrue(fn.indexOf("masterTabs[pRec['таб_номер']]") !== -1,
            'секция «СИЗ» — СИЗ мастеров пропускаются');
    });""",
        """    test('фильтр в ОБОИХ секциях — мероприятия/СИЗ (отпуска убраны, Task 404)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderMonthEventsPanel'));
        assertTrue(fn.indexOf("masterTabs[t['таб_номер']]") !== -1,
            'секция «Мероприятия» — записи мастеров пропускаются');
        assertFalse(fn.indexOf("masterTabs[vRec['таб_номер']]") !== -1,
            'секции «Отпуска» больше нет (Task 404) — фильтр удалён вместе с ней');
        assertTrue(fn.indexOf("masterTabs[pRec['таб_номер']]") !== -1,
            'секция «СИЗ» — СИЗ мастеров пропускаются');
    });""",
    ),

    (
        """        assertTrue(html.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'мероприятий — 1 (мастерское не в счёте)');
        assertTrue(html.indexOf('Отпуска · сентябрь 2026 · 1') !== -1,
            'отпусков — 1');
        assertTrue(html.indexOf('СИЗ · сентябрь 2026 · 1') !== -1,
            'СИЗ — 1');""",
        """        assertTrue(html.indexOf('Мероприятия · сентябрь 2026 · 1') !== -1,
            'мероприятий — 1 (мастерское не в счёте)');
        assertFalse(html.indexOf('Отпуска · сентябрь 2026 · 1') !== -1,
            'секции отпусков нет (Task 404)');
        assertTrue(html.indexOf('СИЗ · сентябрь 2026 · 1') !== -1,
            'СИЗ — 1');""",
    ),

    (
        """        assertTrue(html.indexOf('Мероприятия · сентябрь 2026 · 2') !== -1 &&
                   html.indexOf('Отпуска · сентябрь 2026 · 2') !== -1 &&
                   html.indexOf('СИЗ · сентябрь 2026 · 2') !== -1,
            'счётчики полные (по 2)');""",
        """        assertTrue(html.indexOf('Мероприятия · сентябрь 2026 · 2') !== -1 &&
                   html.indexOf('СИЗ · сентябрь 2026 · 2') !== -1,
            'счётчики полные (по 2)');
        assertFalse(html.indexOf('Отпуска · сентябрь 2026 · 2') !== -1,
            'секции отпусков нет (Task 404)');""",
    ),
])

# ============================================================
# test-task393.js — порядок панелей: СИЗ — 2-я колонка
# ============================================================
patch('tests/test-task393.js', [

    (
        """        const i1 = html.indexOf('Галкин Д. Н.');
        const i2 = html.indexOf('Отпуска · 2026');
        const i3 = html.indexOf('Мероприятия · 2026');
        const i4 = html.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(i1 !== -1 && i2 !== -1 && i3 !== -1 && i4 !== -1, 'блоки на месте');
        assertTrue(i1 < i2 && i2 < i3 && i3 < i4, 'порядок панелей — как в заявке');""",
        """        const i1 = html.indexOf('Галкин Д. Н.');
        const i2 = html.indexOf('Отпуска · 2026');
        const i3 = html.indexOf('Мероприятия · 2026');
        const i4 = html.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(i1 !== -1 && i2 !== -1 && i3 !== -1 && i4 !== -1, 'блоки на месте');
        // Task 404: СИЗ — ВТОРАЯ колонка (слева от мероприятий):
        // DOM-порядок: профиль → отпуска → СИЗ → мероприятия
        assertTrue(i1 < i2 && i2 < i4 && i4 < i3,
            'порядок панелей: профиль → отпуска → СИЗ → мероприятия');""",
    ),
])

# ============================================================
# test-task395.js — ТРИ колонки
# ============================================================
patch('tests/test-task395.js', [

    (
        """    test('_renderWorkerCardPanels — левая (профиль/отпуска) + правая (мероприятия/СИЗ)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        // Task 403: мероприятия — в верх ПРАВОЙ колонки (между
        // профилем и СИЗ); было bi < 3 (все три слева)
        assertTrue(fn.indexOf("if (bi < 2) left += panel; else right += panel;") !== -1,
            'блоки 1–2 (профиль/отпуска) — в ЛЕВУЮ, 3–4 (мероприятия/СИЗ) — в ПРАВУЮ');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol\\">' + left + '</div>'") !== -1,
            'левая колонка-обёртка .ws-wcol');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol ws-wcol-ppe\\">' + right + '</div>'") !== -1,
            'правая колонка .ws-wcol-ppe (СИЗ)');
        assertFalse(fn.indexOf("'ws-wgrid2'") !== -1,
            'обёртку сетки задаёт _renderWorkersPage (не панели)');
    });""",
        """    test('_renderWorkerCardPanels — ТРИ колонки: main / СИЗ / мероприятия', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        // Task 404: СИЗ — ВТОРАЯ колонка (слева от мероприятий),
        // мероприятия — ТРЕТЬЯ (.ws-wcol-tr)
        assertTrue(fn.indexOf('if (bi < 2) colMain += panel;') !== -1,
            'блоки 1–2 (профиль/отпуска) — в колонку main');
        assertTrue(fn.indexOf('else if (bi === 3) colPpe += panel;') !== -1,
            'блок 4 (СИЗ) — во ВТОРУЮ колонку .ws-wcol-ppe');
        assertTrue(fn.indexOf('else colTr += panel;') !== -1,
            'блок 3 (мероприятия) — в ТРЕТЬЮ колонку .ws-wcol-tr');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol ws-wcol-tr\\">' + colTr + '</div>'") !== -1,
            'третья колонка .ws-wcol-tr (мероприятия — СПРАВА от СИЗ)');
        assertFalse(fn.indexOf("'ws-wgrid2'") !== -1,
            'обёртку сетки задаёт _renderWorkersPage (не панели)');
    });""",
    ),

    (
        """    test('десктоп ≥1024px — ДВЕ равные колонки, правая НЕ тянется', () => {
        const m = INDEX_SRC.match(/@media \\(min-width: 1024px\\) \\{\\s*\\.ws-wgrid2 \\{[^}]*?\\}\\s*\\.ws-wgrid2 \\.ws-wcol \\{[^}]*?\\}\\s*\\}/);
        assertTrue(m !== null, 'блок медиаправил жив');
        assertTrue(m[0].indexOf('display: flex;') !== -1 &&
                   m[0].indexOf('gap: 12px;') !== -1,
            'flex-раскладка с зазором 12px');
        assertTrue(m[0].indexOf('align-items: flex-start;') !== -1,
            'правая колонка (СИЗ) — ВЕРХ правой части, не тянется вниз');
        assertTrue(m[0].indexOf('flex: 1 1 0;') !== -1,
            'колонки РАВНЫЕ (1 1 0 — на всю ширину окна вкладок)');
    });""",
        """    test('десктоп ≥1024px — ТРИ равные колонки (в одну линию, Task 404)', () => {
        const m = INDEX_SRC.match(/@media \\(min-width: 1024px\\) \\{\\s*\\.ws-wgrid2 \\{[^}]*?\\}\\s*\\.ws-wgrid2 \\.ws-wcol \\{[^}]*?\\}\\s*\\}/);
        assertTrue(m !== null, 'блок медиаправил жив');
        assertTrue(m[0].indexOf('display: flex;') !== -1 &&
                   m[0].indexOf('gap: 12px;') !== -1,
            'flex-раскладка с зазором 12px');
        assertTrue(m[0].indexOf('align-items: flex-start;') !== -1,
            'колонки НЕ тянутся по высоте друг друга');
        assertTrue(m[0].indexOf('flex: 1 1 0;') !== -1,
            'колонки РАВНЫЕ (1 1 0 — три блока в одну линию на всю ширину)');
    });""",
    ),

    (
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
        // мероприятия — МЕЖДУ блоками профиля и СИЗ: профиль — в ЛЕВОЙ
        // (раньше по DOM), мероприятия — в ПРАВОЙ над СИЗ; порядок
        // DOM: профиль → мероприятия → СИЗ (координаты iL/iR общие)
        assertTrue(iL + leftPart.indexOf('Галкин Д. Н.') < iR + iTr &&
                   iR + iTr < iR + iPz,
            'визуальный порядок: профиль → мероприятия → СИЗ');
    });

    test('страница — панели в обёртке .ws-wgrid2 (вкладка работника)', () => {
        const t = pageHost({ canEdit: true });
        t.host._renderWorkersPage();
        t.host.selectWorkersTab('2706');
        const body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('<div class="ws-wgrid2">') !== -1,
            'обёртка .ws-wgrid2 жива (Task 394)');
        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-ppe">') !== -1,
            'правая колонка (мероприятия + СИЗ) — на странице');
        assertEqual((body.match(/class="ws-wcard"/g) || []).length, 4,
            'всего четыре блока-окна');
    });""",
        """    test('колонки: 1 — профиль+отпуска; 2 — СИЗ; 3 — мероприятия (Task 404)', () => {
        const t = pageHost({ canEdit: true });
        const html = t.host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iP = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        const iT = html.indexOf('<div class="ws-wcol ws-wcol-tr">');
        assertTrue(iL !== -1 && iP !== -1 && iT !== -1 && iL < iP && iP < iT,
            'ТРИ колонки: main → СИЗ → мероприятия');
        const mainPart = html.slice(iL, iP);
        const ppePart = html.slice(iP, iT);
        const trPart = html.slice(iT);
        assertEqual((mainPart.match(/class="ws-wcard"/g) || []).length, 2,
            'колонка 1 — 2 окна (профиль + отпуска)');
        assertEqual((ppePart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 2 — 1 окно (СИЗ)');
        assertEqual((trPart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 3 — 1 окно (мероприятия)');
        assertTrue(ppePart.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'СИЗ — во 2-й колонке (СЛЕВА от мероприятий)');
        assertTrue(ppePart.indexOf('Каска защитная') !== -1,
            'запись СИЗ — во 2-й колонке');
        assertTrue(trPart.indexOf('Мероприятия · 2026') !== -1,
            'мероприятия — в 3-й колонке (СПРАВА от СИЗ)');
        const i1 = mainPart.indexOf('Галкин Д. Н.');
        const i2 = mainPart.indexOf('Отпуска · 2026');
        assertTrue(i1 !== -1 && i2 !== -1 && i1 < i2,
            'порядок колонки 1: профиль → отпуска');
        assertTrue(mainPart.indexOf('СИЗ · средства') === -1 &&
                   mainPart.indexOf('Мероприятия · 2026') === -1,
            'в колонке 1 — только профиль и отпуска');
    });

    test('страница — панели в обёртке .ws-wgrid2 (вкладка работника)', () => {
        const t = pageHost({ canEdit: true });
        t.host._renderWorkersPage();
        t.host.selectWorkersTab('2706');
        const body = t.els.wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('<div class="ws-wgrid2">') !== -1,
            'обёртка .ws-wgrid2 жива (Task 394)');
        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-ppe">') !== -1,
            'вторая колонка (СИЗ) — на странице');
        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-tr">') !== -1,
            'третья колонка (мероприятия) — на странице (Task 404)');
        assertEqual((body.match(/class="ws-wcard"/g) || []).length, 4,
            'всего четыре блока-окна');
    });""",
    ),
])

# ============================================================
# test-task403.js — панели: три колонки (СИЗ слева от мероприятий)
# ============================================================
patch('tests/test-task403.js', [

    (
        """    test('_renderWorkerCardPanels: 1–2 слева, 3–4 справа', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf('if (bi < 2) left += panel; else right += panel;') !== -1,
            'ЛЕВАЯ — профиль + отпуска; ПРАВАЯ — мероприятия + СИЗ (мероприятия ВВЕРХУ)');
    });""",
        """    test('_renderWorkerCardPanels: ТРИ колонки — СИЗ СЛЕВА от мероприятий (Task 404)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf('else if (bi === 3) colPpe += panel;') !== -1,
            'СИЗ (блок 4) — ВТОРАЯ колонка (слева от мероприятий)');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol ws-wcol-tr\\">' + colTr + '</div>'") !== -1,
            'ТРЕТЬЯ колонка .ws-wcol-tr — мероприятия (справа от СИЗ)');
    });""",
    ),
])

# ============================================================
# run-all.js — подключение test-task404.js
# ============================================================
patch('tests/run-all.js', [

    (
        """// Task 403 — «разряд» → «р.» и БЕЗ группы допуска в столбце ФИО; попап
// без СИЗ; GAS-фикс бага комментария (столбцы по заголовкам); ярлыки
// «Работников» по самому длинному тексту; мероприятия над СИЗ
require('./test-task403.js');
require('./test-deploy-url.js');""",
        """// Task 403 — «разряд» → «р.» и БЕЗ группы допуска в столбце ФИО; попап
// без СИЗ; GAS-фикс бага комментария (столбцы по заголовкам); ярлыки
// «Работников» по самому длинному тексту; мероприятия над СИЗ
require('./test-task403.js');
// Task 404 — карточка: ТРИ колонки (профиль+отпуска | СИЗ | мероприятия),
// кнопки ✎/✕ рядом (контент строк растянут); окно мероприятий без отпусков
require('./test-task404.js');
require('./test-deploy-url.js');""",
    ),
])

print('OK: тест-файлы адаптированы')
