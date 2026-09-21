#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 388 — адаптация затронутых тестов под новую функциональность:
#   1) миниатюры мероприятий ВСЕГДА сплошные с цветом кода (ws-ev-pending/
#      wsp-ev-plan удалены) — test-work-events, test-task314/319/341/343/
#      356/361;
#   2) канон _STATUS_CODES_CANON получил short — test-work-schedule,
#      test-task312 (литерал «Выходного»);
#   3) итоги учёта доступны во ВСЕХ видах (гейт только уровня «min») —
#      test-task338/340;
#   4) значок .ws-bar-exp — правый ВЕРХНИЙ угол — test-task378/381;
#   5) страница «Работники» — вкладки-ярлыки (Общая + по фамильно) —
#      test-task385;
#   6) ширина краткого вида «Обозначений» 190 → 230px — test-task385/
#      386/387.
# Каждая замена — с проверкой точного числа вхождений.

import sys


def patch(path, repls):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    for item in repls:
        if len(item) == 4:
            name, old, new, cnt = item
        else:
            name, old, new = item
            cnt = 1
        found = s.count(old)
        if found == 0 and cnt == 1 and s.count(new) >= 1:
            continue    # уже применено (идемпотентность при повторном запуске)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: применено правок: %d' % (path, len(repls)))


# ============================================================
# test-work-schedule.js — канон с short (литерал «Выходного»)
# ============================================================
patch('tests/test-work-schedule.js', [
    ('canon-vyh-short',
     "{code:'',     name:'Выходной, плановый выходной день', color:'#EEF0F2'}",
     "{code:'',     short:'выходной', name:'Выходной, плановый выходной день', color:'#EEF0F2'}",
     1),
])

# ============================================================
# test-task312.js — тот же литерал канона
# ============================================================
patch('tests/test-task312.js', [
    ('canon-vyh-short',
     "{code:'',     name:'Выходной, плановый выходной день', color:'#EEF0F2'}",
     "{code:'',     short:'выходной', name:'Выходной, плановый выходной день', color:'#EEF0F2'}",
     1),
])

# ============================================================
# test-work-events.js — пунктирных бейджей больше нет
# ============================================================
patch('tests/test-work-events.js', [
    ('solid-badges-assert',
     """        assertTrue(INDEX_SRC.indexOf('var solidBadges = !!status;') !== -1,
            'сплошные бейджи при любом статусе (вкл. дни отсутствия — Task 314)');
""",
     """        // Task 388 (заявка: «цвет фона миниатюр всегда должен
        // соответствовать установленному»): пунктирные удалены
        assertTrue(INDEX_SRC.indexOf('ws-ev-pending') === -1,
            'пунктирных бейджей больше нет (Task 388: фон всегда цвет кода)');
"""),
    ('pending-test-rewrite',
     """    test('JS: пунктирный бейдж на пустой ячейке (ws-ev-pending)', () => {
        assertTrue(INDEX_SRC.indexOf('ws-ev-pending') !== -1,
            'пунктирный бейдж-подсказка (аналог ws-vac-plan)');
""",
     """    test('JS: бейдж на пустой ячейке — СПЛОШНОЙ с цветом кода (Task 388)', () => {
        assertFalse(INDEX_SRC.indexOf('ws-ev-pending') !== -1,
            'пунктирного бейджа-подсказки больше нет (Task 388)');
"""),
    ('pending-css-assert',
     """        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ws-grid tbody td.ws-cell .ws-ev-badge.ws-ev-pending') !== -1,
            'светлая тема пунктирного бейджа');
""",
     """        // Task 388: правила ws-ev-pending удалены (пунктирных бейджей нет)
        assertFalse(INDEX_SRC.indexOf('.ws-ev-badge.ws-ev-pending') !== -1,
            'правил пунктирного бейджа больше нет (Task 388)');
"""),
])

# ============================================================
# test-task314.js — VM: пустая/план ячейка → сплошной бейдж
# ============================================================
patch('tests/test-task314.js', [
    ('vm-empty-solid',
     """    test('пустая ячейка + мероприятие — пунктирный бейдж-подсказка', () => {
        const ctx = mkRenderCtx({ '2026-09-01': [{ code: 'И', training: { id: 4 } }] }, null);
        const html = cellHtml(ctx, null);
        assertTrue(html.indexOf('ws-ev-pending') !== -1, 'пунктирный бейдж');
        assertFalse(/style="background:/.test(html.match(/<span class="ws-ev-badge[^>]*>/)[0]),
            'пунктирный бейдж без заливки');
    });
""",
     """    test('пустая ячейка + мероприятие — СПЛОШНОЙ бейдж с цветом кода (Task 388)', () => {
        const ctx = mkRenderCtx({ '2026-09-01': [{ code: 'И', training: { id: 4 } }] }, null);
        const html = cellHtml(ctx, null);
        assertFalse(html.indexOf('ws-ev-pending') !== -1,
            'пунктирного бейджа нет (Task 388: фон всегда цвет кода)');
        assertTrue(/style="background:/.test(html.match(/<span class="ws-ev-badge[^>]*>/)[0]),
            'заливка цветом кода — и на пустой ячейке');
    });
"""),
    ('vm-vacplan-solid',
     """    test('план отпуска + мероприятие — пунктирный бейдж рядом с «ОТ»', () => {
        const ctx = mkRenderCtx({ '2026-09-01': [{ code: 'И', training: { id: 5 } }] },
                                { '2026-09-01': { 'таб_номер': '017' } });
        const html = cellHtml(ctx, null);
        assertTrue(html.indexOf('>ОТ') !== -1, 'код плана «ОТ»');
        assertTrue(html.indexOf('ws-ev-pending') !== -1, 'пунктирный бейдж события');
    });
""",
     """    test('план отпуска + мероприятие — СПЛОШНОЙ бейдж рядом с «ОТ» (Task 388)', () => {
        const ctx = mkRenderCtx({ '2026-09-01': [{ code: 'И', training: { id: 5 } }] },
                                { '2026-09-01': { 'таб_номер': '017' } });
        const html = cellHtml(ctx, null);
        assertTrue(html.indexOf('>ОТ') !== -1, 'код плана «ОТ»');
        assertFalse(html.indexOf('ws-ev-pending') !== -1,
            'пунктирного бейджа нет (Task 388)');
        assertTrue(/style="background:/.test(html.match(/<span class="ws-ev-badge[^>]*>/)[0]),
            'заливка цветом кода — и на плане отпуска');
    });
"""),
])

# ============================================================
# test-task319.js — тёмная тема: правило пунктирного бейджа удалено
# ============================================================
patch('tests/test-task319.js', [
    ('dark-pending-rule',
     """        assertTrue(cssRule(/\\[data-theme="dark"\\] \\.ws-grid tbody td\\.ws-cell \\.ws-ev-badge\\.ws-ev-pending \\{[^}]*color:\\s*#141413;[^}]*\\}/s),
            'пунктирный бейдж — тёмный текст');
""",
     """        // Task 388: правило тёмной темы пунктирного бейджа удалено
        assertFalse(INDEX_SRC.indexOf('[data-theme="dark"] .ws-grid tbody td.ws-cell .ws-ev-badge.ws-ev-pending') !== -1,
            'пунктирных бейджей больше нет (Task 388)');
"""),
])

# ============================================================
# test-task338.js — итоги доступны в любом виде (гейт только min)
# ============================================================
patch('tests/test-task338.js', [
    ('applyview-btn',
     """        assertTrue(fn.indexOf("totalsBtn.hidden = !full || minNoTotals;") !== -1,
            '«Итоги учёта» скрыты вне полного вида И у уровня min (Task 340)');
""",
     """        // Task 388 (заявка): итоги доступны во ВСЕХ видах — скрыты
        // только уровню «min» (Task 340)
        assertTrue(fn.indexOf("totalsBtn.hidden = minNoTotals;") !== -1,
            '«Итоги учёта» скрыты только уровню min (Task 388)');
        assertFalse(fn.indexOf('!full || minNoTotals') !== -1,
            'гейта вида больше нет (Task 388)');
"""),
    ('toggle-gate',
     """        assertTrue(fn.indexOf("(vGate !== 'full' || this._viewLevel === 'min')") !== -1,
            'десктоп: открытие шторки гейчится видом и уровнем (Task 340)');
        assertTrue(fn.indexOf("if (vGate !== 'full' || this._viewLevel === 'min') return;") !== -1,
            'мобильная страница итогов — гейт вида и уровня');
""",
     """        // Task 388 (заявка): итоги в любом виде; гейт — только min
        assertTrue(fn.indexOf("if (this._viewLevel === 'min' &&") !== -1,
            'десктоп: гейт только уровнем min (Task 388/340)');
        assertTrue(fn.indexOf("if (this._viewLevel === 'min') return;") !== -1,
            'мобильная страница итогов — гейт уровня');
        assertFalse(fn.indexOf("vGate !== 'full'") !== -1,
            'гейта вида больше нет (Task 388)');
"""),
    ('vm-page-shift-open',
     """    test('VM: onTotalsPageOpen — зритель (вид shift) уходит на табель', () => {
        let navPage = null;
        const host = new Function('navigateTo', 'return ({' +
            methodText(WS_CLIENT, 'onTotalsPageOpen') + '\\n' +
            "_view: 'shift', _viewLevel: 'view'," +
            '});')(function(page) { navPage = page; });
        host.onTotalsPageOpen();
        assertEqual(navPage, 'work-schedule', 'редирект на страницу табеля');
        assertFalse(host._ttPage === true, 'флаг страницы итогов не ставится');
    });
""",
     """    test('VM: onTotalsPageOpen — вид shift ОТКРЫВАЕТ страницу (Task 388)', () => {
        // Task 388 (заявка: итоги в видах сменный/дневной): гейт вида
        // снят — страница итогов открывается и в сменном виде
        const els = {
            wsTtPageTabMonth: { classList: { toggle: function() {} } },
            wsTtPageTabYear: { classList: { toggle: function() {} } }
        };
        let navPage = null;
        const host = new Function('document', 'navigateTo', 'return ({' +
            methodText(WS_CLIENT, 'onTotalsPageOpen') + '\\n' +
            "_view: 'shift', _viewLevel: 'view'," +
            "_totalsTab: 'month'," +
            '_renderTotals: function() { this.rendered = true; },' +
            '_reapplyEmpNarrow: function() {}' +
            '});')(els, function(page) { navPage = page; });
        host.onTotalsPageOpen();
        assertEqual(navPage, null, 'редиректа нет — итоги доступны в сменном виде');
        assertEqual(host._ttPage, true, 'флаг страницы итогов ставится');
        assertEqual(host.rendered, true, 'таблицы отрисованы');
    });
"""),
])

# ============================================================
# test-task340.js — гейт только min (вид — любой)
# ============================================================
patch('tests/test-task340.js', [
    ('applyview-btn',
     """        assertTrue(fn.indexOf('totalsBtn.hidden = !full || minNoTotals;') !== -1,
            'кнопка «Итоги учёта» скрыта и в полном виде у min');
        assertTrue(fn.indexOf('(!full || minNoTotals) && this._totalsOpen') !== -1,
            'открытая шторка закрывается при min (смена уровня)');
""",
     """        assertTrue(fn.indexOf('totalsBtn.hidden = minNoTotals;') !== -1,
            'кнопка «Итоги учёта» скрыта только у min (Task 388: вид — любой)');
        assertTrue(fn.indexOf('minNoTotals && this._totalsOpen') !== -1,
            'открытая шторка закрывается при min (смена уровня)');
"""),
    ('toggle-gate',
     """        assertTrue(fn.indexOf(
            "(vGate !== 'full' || this._viewLevel === 'min')") !== -1,
            'десктоп: открытие шторки гейчится видом и уровнем');
""",
     """        assertTrue(fn.indexOf(
            "if (this._viewLevel === 'min' &&") !== -1,
            'десктоп: гейт только уровнем min (Task 388: вид — любой)');
"""),
    ('vm-page-min-gate',
     """    test('VM: onTotalsPageOpen — уровень view, вид shift: гейт вида жив', () => {
        let navPage = null;
        const host = new Function('navigateTo', 'return ({' +
            methodText(WS_CLIENT, 'onTotalsPageOpen') + '\\n' +
            "_view: 'shift', _viewLevel: 'view'," +
            '});')(function(page) { navPage = page; });
        host.onTotalsPageOpen();
        assertEqual(navPage, 'work-schedule', 'сменный вид — без итогов (гейт вида)');
    });
""",
     """    test('VM: onTotalsPageOpen — уровень min, вид shift: гейт уровня жив (Task 388)', () => {
        // Task 388: гейт ВИДА снят (итоги в любом виде); гейт УРОВНЯ
        // min жив — редирект на табель
        let navPage = null;
        const host = new Function('navigateTo', 'return ({' +
            methodText(WS_CLIENT, 'onTotalsPageOpen') + '\\n' +
            "_view: 'shift', _viewLevel: 'min'," +
            '});')(function(page) { navPage = page; });
        host.onTotalsPageOpen();
        assertEqual(navPage, 'work-schedule', 'уровень min — без итогов (гейт уровня)');
        assertFalse(host._ttPage === true, 'флаг страницы не ставится');
    });
"""),
])

# ============================================================
# test-task341.js — печать: бейдж всегда сплошной
# ============================================================
patch('tests/test-task341.js', [
    ('vm-empty-print-solid',
     """        assertTrue(td.indexOf('wsp-ev-plan') !== -1,
            'пунктирный бейдж у несформированного дня');
        assertTrue(td.indexOf('background:') === -1,
            'у плана нет заливки (появится при «Сформировать»)');
""",
     """        assertFalse(td.indexOf('wsp-ev-plan') !== -1,
            'пунктирного бейджа нет (Task 388)');
        assertTrue(td.indexOf('background:') !== -1,
            'заливка цветом кода — и у несформированного дня (Task 388)');
"""),
])

# ============================================================
# test-task343.js — печать: пунктирных бейджей нет
# ============================================================
patch('tests/test-task343.js', [
    ('src-printcell-plan',
     """        assertTrue(c.indexOf('wsp-ev-plan') !== -1, 'пунктирные бейджи-план');
""",
     """        assertFalse(c.indexOf('wsp-ev-plan') !== -1,
            'пунктирных бейджей-план больше нет (Task 388: заливка всегда)');
"""),
    ('src-css-plan',
     """        assertTrue(block.indexOf('wsp-ev-plan') !== -1,
            'правило .wsp-ev-plan есть');
""",
     """        assertFalse(block.indexOf('wsp-ev-plan') !== -1,
            'правила .wsp-ev-plan нет (Task 388: пунктирные удалены)');
"""),
    ('vm-plan',
     """        assertTrue(td.indexOf('wsp-ev') !== -1, 'бейджи есть');
        assertTrue(td.indexOf('wsp-ev-plan') !== -1, 'пунктирные (день не сформирован)');
        assertTrue(td.indexOf('>ОБ<') !== -1 && td.indexOf('>ПР<') !== -1,
            'коды мероприятий в бейджах');
        assertTrue(td.indexOf('background:') === -1,
            'без заливки (появится при «Сформировать»)');
""",
     """        assertTrue(td.indexOf('wsp-ev') !== -1, 'бейджи есть');
        assertFalse(td.indexOf('wsp-ev-plan') !== -1,
            'пунктирных нет (Task 388: заливка всегда)');
        assertTrue(td.indexOf('>ОБ<') !== -1 && td.indexOf('>ПР<') !== -1,
            'коды мероприятий в бейджах');
        assertTrue(td.indexOf('background:') !== -1,
            'с заливкой цветом кода (Task 388)');
"""),
])

# ============================================================
# test-task356.js — пунктирного бейджа нет
# ============================================================
patch('tests/test-task356.js', [
    ('vm-pending',
     """        assertTrue(html.indexOf('ws-ev-pending') !== -1, 'пунктирный бейдж-подсказка жив');
""",
     """        assertFalse(html.indexOf('ws-ev-pending') !== -1,
            'пунктирного бейджа нет (Task 388: сплошной с цветом кода)');
"""),
])

# ============================================================
# test-task361.js — печать: сплошные бейджи всегда
# ============================================================
patch('tests/test-task361.js', [
    ('src-css-plan',
     """        assertTrue(block.indexOf('.wsp-ev.wsp-ev-plan { border-style: dashed; }') !== -1,
            'пунктирный бейдж-план');
""",
     """        assertFalse(block.indexOf('wsp-ev-plan') !== -1,
            'пунктирного бейджа-план нет (Task 388: заливка всегда)');
"""),
    ('src-printcell-solid',
     """        assertTrue(c.indexOf("wsp-ev' + (solid ? '' : ' wsp-ev-plan')") !== -1,
            'сплошной/пунктирный по признаку сформированности дня');
""",
     """        // Task 388: бейдж печати ВСЕГДА сплошной с цветом кода
        assertFalse(c.indexOf('wsp-ev-plan') !== -1,
            'пунктирных бейджей нет (Task 388)');
"""),
    ('src-footnote',
     """        assertTrue(b.indexOf('пунктирный') !== -1,
            'пунктирный значок = день ещё не сформирован');
""",
     """        assertFalse(b.indexOf('день ещё не сформирован') !== -1,
            'пояснение «день ещё не сформирован» удалено (Task 388)');
"""),
    ('vm-two-solid',
     """    test('VM: пустая ячейка + 2 события — два пунктирных бейджа без заливки', () => {
        var td = cellHost({ events: [{ code: 'И', training: 1 },
                                      { code: 'ПР', training: 2 }] })
            ._printCell(6, '2026-09-06', EMP, null);
        var n = (td.match(/class="wsp-ev wsp-ev-plan"/g) || []).length;
        assertEqual(n, 2, 'два пунктирных бейджа');
        assertTrue(td.indexOf('background:') === -1, 'без заливки');
    });
""",
     """    test('VM: пустая ячейка + 2 события — два СПЛОШНЫХ бейджа с заливкой (Task 388)', () => {
        var td = cellHost({ events: [{ code: 'И', training: 1 },
                                      { code: 'ПР', training: 2 }] })
            ._printCell(6, '2026-09-06', EMP, null);
        var n = (td.match(/class="wsp-ev"/g) || []).length;
        assertEqual(n, 2, 'два сплошных бейджа');
        assertTrue(td.indexOf('background:') !== -1,
            'с заливкой цветом кода (Task 388)');
    });
"""),
])

# ============================================================
# test-task378.js — значок в правом ВЕРХНЕМ углу
# ============================================================
patch('tests/test-task378.js', [
    ('bar-exp-top',
     """    test('значок .ws-bar-exp: правый нижний угол, контраст по активности', () => {
        const b = ruleBlock('.ws-bar-exp {');
        assertTrue(b !== null && /position:\\s*absolute/.test(b), 'absolute');
        assertTrue(b !== null && /right:\\s*5px/.test(b) && /bottom:\\s*5px/.test(b),
            'правый нижний угол окна');
""",
     """    test('значок .ws-bar-exp: правый ВЕРХНИЙ угол, контраст по активности (Task 388)', () => {
        const b = ruleBlock('.ws-bar-exp {');
        assertTrue(b !== null && /position:\\s*absolute/.test(b), 'absolute');
        assertTrue(b !== null && /right:\\s*5px/.test(b) && /top:\\s*5px/.test(b),
            'правый ВЕРХНИЙ угол окна (Task 388: прежде нижний — уезжал при раскрытии)');
"""),
])

# ============================================================
# test-task381.js — значок absolute в правом верхнем углу
# ============================================================
patch('tests/test-task381.js', [
    ('bar-exp-top',
     """    test('значок остаётся absolute (CSS не менялся)', () => {
        const b = ruleBlock('.ws-bar-exp {');
        assertTrue(b !== null && /position:\\s*absolute/.test(b) &&
                   /right:\\s*5px/.test(b) && /bottom:\\s*5px/.test(b),
            'правый нижний угол, absolute — как в Task 378');
    });
""",
     """    test('значок остаётся absolute в правом ВЕРХНЕМ углу (Task 388)', () => {
        const b = ruleBlock('.ws-bar-exp {');
        assertTrue(b !== null && /position:\\s*absolute/.test(b) &&
                   /right:\\s*5px/.test(b) && /top:\\s*5px/.test(b),
            'правый ВЕРХНИЙ угол, absolute (Task 388: верх при раскрытии не двигается)');
    });
"""),
])

# ============================================================
# test-task385.js — подсказка «Вид», страница «Работники» (вкладки),
#                   ширина краткого вида легенды 230px
# ============================================================
patch('tests/test-task385.js', [
    ('host-methods-add',
     """        '_renderEmpPopup', '_renderWorkerCard', '_renderWorkersPage',
""",
     """        '_renderEmpPopup', '_renderWorkerCard', '_renderWorkersPage',
        '_renderWorkersGeneral', 'selectWorkersTab', '_escAttr',
"""),
    ('view-tip-text',
     """        assertTrue(INDEX_SRC.indexOf('полный — все работники, доступна шторка «Итоги учёта»') !== -1,
            'подсказка «Вид»');
""",
     """        assertTrue(INDEX_SRC.indexOf('Итоги учёта доступны в любом виде') !== -1,
            'подсказка «Вид» (Task 388: итоги в любом виде)');
"""),
    ('src-workers-page-tabs',
     """    test('_renderWorkersPage — сортировка сетки + счётчик + карточки', () => {
        const fn = methodText(INDEX_SRC, '_renderWorkersPage');
        assertTrue(fn.indexOf('this._sortEmployees(this._EMPLOYEES)') !== -1,
            'порядок карточек — как строки шахматки (Task 259)');
        assertTrue(fn.indexOf('ws-workers-count') !== -1, 'счётчик работников');
        assertTrue(fn.indexOf('ws-wcard') !== -1, 'обёртка карточки .ws-wcard');
        assertTrue(fn.indexOf('_renderWorkerCard(tabNo, withEdit)') !== -1,
            'карточки — общий рендер с withEdit');
        assertTrue(fn.indexOf('Нет активных работников.') !== -1,
            'пустое состояние страницы');
        assertTrue(fn.indexOf("['работник', 'работника', 'работников']") !== -1,
            'склонение счётчика');
    });
""",
     """    test('_renderWorkersPage — вкладки: Общая + по фамильно (Task 388)', () => {
        const fn = methodText(INDEX_SRC, '_renderWorkersPage');
        assertTrue(fn.indexOf('localeCompare') !== -1 &&
                   fn.indexOf("'ru'") !== -1,
            'сортировка по ФИО (фамильно по алфавиту; Task 388)');
        assertTrue(fn.indexOf('ws-workers-layout') !== -1, 'раскладка вкладки+тело');
        assertTrue(fn.indexOf('ws-wtabs') !== -1, 'колонка ярлыков-вкладок');
        assertTrue(fn.indexOf('ws-wtab-general') !== -1, 'ярлык «Общая» первый');
        assertTrue(fn.indexOf('selectWorkersTab') !== -1, 'клики по ярлыкам');
        assertTrue(fn.indexOf('ws-wcard') !== -1, 'обёртка карточки .ws-wcard');
        assertTrue(fn.indexOf('_renderWorkerCard(empTabNo, withEdit)') !== -1,
            'карточка — общий рендер с withEdit');
        assertTrue(fn.indexOf('_renderWorkersGeneral(list)') !== -1,
            '«Общая» вкладка — сводная таблица');
        assertTrue(fn.indexOf('Нет активных работников.') !== -1,
            'пустое состояние страницы');
        const gen = methodText(INDEX_SRC, '_renderWorkersGeneral');
        assertTrue(gen.indexOf("['работник', 'работника', 'работников']") !== -1,
            'склонение счётчика (в «Общей»)');
    });
"""),
    ('vm-workers-page-tabs',
     """    test('VM: _renderWorkersPage — счётчик + карточки в порядке сетки', () => {
        const h = makeHost();
        h.WSM._renderWorkersPage();
        const body = h.els().wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('ws-workers-count') !== -1, 'счётчик');
        assertTrue(body.indexOf('2 ') === 0 || body.indexOf('>2 ') !== -1, 'двое работников');
        assertEqual((body.match(/ws-wcard/g) || []).length, 2, 'две карточки');
        // порядок _sortEmployees: сменный Иванов (смена 2) ПЕРВЫМ,
        // дневной Петров — вторым
        assertTrue(body.indexOf('Иванов И. И.') < body.indexOf('Петров П. П.'),
            'сменные выше дневных (Task 259)');
        // карточка с кнопками правки (редактор)
        assertTrue(body.indexOf('ws-emp-editdata') !== -1,
            'кнопки правки в карточках (withEdit=true у редактора)');
    });
""",
     """    test('VM: _renderWorkersPage — вкладки: Общая + фамильный алфавит (Task 388)', () => {
        const h = makeHost();
        h.WSM._renderWorkersPage();
        const body = h.els().wsWorkersBody.innerHTML;
        // вкладки-ярлыки: «Общая» + работники ПО ФАМИЛЬНО ПО АЛФАВИТУ
        assertTrue(body.indexOf('ws-workers-layout') !== -1, 'раскладка вкладок');
        assertEqual((body.match(/role="tab"/g) || []).length, 3,
            'три ярлыка: «Общая» + двое работников');
        assertTrue(body.indexOf('ws-wtab-general active') !== -1,
            '«Общая» активна по умолчанию');
        // ПО ФАМИЛЬНО ПО АЛФАВИТУ: Иванов выше Петрова (не по сменам!)
        assertTrue(body.indexOf('Иванов И. И.') < body.indexOf('Петров П. П.'),
            'фамильный алфавит (Task 388)');
        // «Общая» вкладка — сводная таблица + счётчик
        assertTrue(body.indexOf('ws-wgen-table') !== -1, 'сводная таблица');
        assertTrue(body.indexOf('ws-workers-count') !== -1, 'счётчик работников');
        // клик по ярлыку — карточка с кнопками правки (редактор)
        h.WSM.selectWorkersTab('0871');
        const body2 = h.els().wsWorkersBody.innerHTML;
        assertEqual((body2.match(/ws-wcard/g) || []).length, 1, 'карточка выбранного');
        assertTrue(body2.indexOf('ws-emp-editdata') !== -1,
            'кнопки правки в карточке (withEdit=true у редактора)');
        // выбор живёт между перерисовками
        h.WSM._renderWorkersPage();
        assertTrue(h.els().wsWorkersBody.innerHTML.indexOf('ws-wcard') !== -1,
            'вкладка сохраняется при перерисовке');
    });
"""),
    ('vm-workers-viewer',
     """    test('VM: _renderWorkersPage — зритель без кнопок', () => {
        const h = makeHost();
        h.WSM._canEdit = false;
        h.WSM._renderWorkersPage();
        const body = h.els().wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('ws-wcard') !== -1, 'карточки есть');
        assertTrue(body.indexOf('ws-emp-editdata') === -1 &&
                   body.indexOf('ws-emp-addvac') === -1,
            'без права записи — карточки без кнопок');
    });
""",
     """    test('VM: _renderWorkersPage — зритель без кнопок (Task 388)', () => {
        const h = makeHost();
        h.WSM._canEdit = false;
        h.WSM.selectWorkersTab('0871');
        const body = h.els().wsWorkersBody.innerHTML;
        assertTrue(body.indexOf('ws-wcard') !== -1, 'карточка есть');
        assertTrue(body.indexOf('ws-emp-editdata') === -1 &&
                   body.indexOf('ws-emp-addvac') === -1,
            'без права записи — карточка без кнопок');
    });
"""),
    ('vm-open-workers-page',
     """        assertTrue(h.els().wsWorkersBody.innerHTML.indexOf('ws-wcard') !== -1,
            'карточки отрендерены');
""",
     """        assertTrue(h.els().wsWorkersBody.innerHTML.indexOf('ws-workers-layout') !== -1,
            'страница отрендерена (вкладки, Task 388)');
        assertTrue(h.els().wsWorkersBody.innerHTML.indexOf('ws-wgen-table') !== -1,
            '«Общая» вкладка — сводка по всем работникам');
"""),
    ('vm-legend-230',
     """        assertEqual(drawer.style.width, '190px', 'слот — узкий вид (190px)');
""",
     """        assertEqual(drawer.style.width, '230px', 'слот — краткий вид (230px, Task 388)');
"""),
    ('vm-legend-230-close',
     """        assertEqual(drawer.style.marginRight, '-190px', 'уехала за край (−ширина вида)');
""",
     """        assertEqual(drawer.style.marginRight, '-230px', 'уехала за край (−ширина вида)');
"""),
])

# ============================================================
# test-task386.js — ширина краткого вида 230px
# ============================================================
patch('tests/test-task386.js', [
    ('css-inner-230',
     """    test('CSS: inner — flex:none + 190px (латентный баг Task 385 закрыт)', () => {
        const iCss = INDEX_SRC.indexOf('.ws-legend-inner {');
        assertTrue(iCss !== -1, 'правило .ws-legend-inner есть');
        const chunk = INDEX_SRC.slice(iCss, iCss + 400);
        assertTrue(chunk.indexOf('flex: none') !== -1,
            'flex: none — inner НЕ сжимается flex-сжатием');
        assertTrue(chunk.indexOf('width: 190px') !== -1,
            'узкий вид — 190px (сокращённые обозначения)');
""",
     """    test('CSS: inner — flex:none + 230px (Task 388: краткие обозначения)', () => {
        const iCss = INDEX_SRC.indexOf('.ws-legend-inner {');
        assertTrue(iCss !== -1, 'правило .ws-legend-inner есть');
        const chunk = INDEX_SRC.slice(iCss, iCss + 400);
        assertTrue(chunk.indexOf('flex: none') !== -1,
            'flex: none — inner НЕ сжимается flex-сжатием');
        assertTrue(chunk.indexOf('width: 230px') !== -1,
            'краткий вид — 230px (Task 388: коды + краткие обозначения)');
"""),
    ('widthpx-230',
     """        assertTrue(fn.indexOf('190') !== -1, 'узкий вид — 190px');
""",
     """        assertTrue(fn.indexOf('230') !== -1, 'краткий вид — 230px (Task 388)');
"""),
    ('max-230',
     """        assertTrue(fn.indexOf('Math.max(190') !== -1,
            'широкий не уже 190px');
""",
     """        assertTrue(fn.indexOf('Math.max(230') !== -1,
            'широкий не уже 230px (Task 388)');
"""),
    ('vm-open-230',
     """    test('VM: _setLegend — открытие узким видом (190px)', () => {
        const h = makeHost(true);
        h.WSM._setLegend(true);
        const drawer = h.els().wsLegendDrawer;
        assertEqual(drawer.style.width, '190px', 'слот — узкий вид');
        assertEqual(drawer.style.marginRight, '0px', 'выехала (маржа 0)');
        assertEqual(h.els().wsLgChv.hidden, false, 'шеврон показан');
        h.WSM._setLegend(false);
        assertEqual(drawer.style.marginRight, '-190px',
            'закрытие — за край на ширину вида');
        assertEqual(h.els().wsLgChv.hidden, true, 'шеврон скрыт');
    });
""",
     """    test('VM: _setLegend — открытие кратким видом (230px, Task 388)', () => {
        const h = makeHost(true);
        h.WSM._setLegend(true);
        const drawer = h.els().wsLegendDrawer;
        assertEqual(drawer.style.width, '230px', 'слот — краткий вид');
        assertEqual(drawer.style.marginRight, '0px', 'выехала (маржа 0)');
        assertEqual(h.els().wsLgChv.hidden, false, 'шеврон показан');
        h.WSM._setLegend(false);
        assertEqual(drawer.style.marginRight, '-230px',
            'закрытие — за край на ширину вида');
        assertEqual(h.els().wsLgChv.hidden, true, 'шеврон скрыт');
    });
"""),
    ('vm-wide-collapse-230',
     """        assertEqual(h.els().wsLegendDrawer.style.width, '190px', 'слот — 190px');
""",
     """        assertEqual(h.els().wsLegendDrawer.style.width, '230px', 'слот — 230px (Task 388)');
"""),
    ('vm-caps-230',
     """    test('VM: _legendWidthPx — капы (190 / 500 / 45vw)', () => {
        const h = makeHost(true);            // vw не задан → 1280 fallback
        assertEqual(h.WSM._legendWidthPx(), 190, 'узкий — 190px');
""",
     """    test('VM: _legendWidthPx — капы (230 / 500 / 45vw; Task 388)', () => {
        const h = makeHost(true);            // vw не задан → 1280 fallback
        assertEqual(h.WSM._legendWidthPx(), 230, 'краткий — 230px (Task 388)');
"""),
])

# ============================================================
# test-task387.js — ширина краткого вида 230px
# ============================================================
patch('tests/test-task387.js', [
    ('widthpx-230',
     """        assertEqual(h.WSM._legendWidthPx(), 190, 'узкий — 190px');
""",
     """        assertEqual(h.WSM._legendWidthPx(), 230, 'краткий вид — 230px (Task 388)');
"""),
])

print('Task 388: адаптация тестов завершена')
