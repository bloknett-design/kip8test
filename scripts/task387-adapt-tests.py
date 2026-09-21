#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 387: адаптация существующих тестов под изменения заявки:
#   • панель «Обозначения» — развёрнутый вид до 500px (было 400px);
#   • пояснения легенды: «ст. 120 ТК РФ»-пояснение удалено (как и
#     «Рамка 2px…», «Зебра строк…», «Код мероприятия…»);
#   • справочник кодов нормализуется к канону _STATUS_CODES_CANON
#     (порядок по группам + полные наименования; «Выходной» — ПУСТОЙ
#     код: точка «·» убрана из попапа/select; фолбэк = канон);
#   • _restoreCachedView/_loadStatusCodes зовут _normalizeStatusCodes
#     (VM-харнесс кэша должен подгружать метод + канон);
#   • печать: «.»-данные раскрываются строкой «Выходного» (пустой код).
#
# Затронуты: test-task386 (500px ×4, заметка), test-task385 (заметка),
# test-task312 («·»/фолбэк/cur), test-task314 (харнесс кэша + канон),
# test-task356 («·» метки), test-task360 (фильтр печати),
# test-work-schedule (фолбэк = канон, «Выходной» пустой код).

import io


def patch(path, repls):
    s = io.open(path, encoding='utf-8').read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: применено правок: %d' % (path, len(repls)))


# ============================================================
# 1. test-task386.js — 500px + заметка «ст. 120» удалена
# ============================================================

t386 = []

t386.append(('386: CSS широкий вид 500px', '''    test('CSS: широкий вид — min(400px, 45vw) классом ws-lg-wide', () => {
        const iCss = INDEX_SRC.indexOf(
            '.ws-legend-drawer.ws-lg-wide .ws-legend-inner {');
        assertTrue(iCss !== -1, 'правило широкого вида есть');
        const chunk = INDEX_SRC.slice(iCss, iCss + 200);
        assertTrue(chunk.indexOf('width: min(400px, 45vw)') !== -1,
            'широкая панель — min(400px, 45vw)');
    });''', '''    test('CSS: широкий вид — min(500px, 45vw) классом ws-lg-wide (Task 387)', () => {
        const iCss = INDEX_SRC.indexOf(
            '.ws-legend-drawer.ws-lg-wide .ws-legend-inner {');
        assertTrue(iCss !== -1, 'правило широкого вида есть');
        const chunk = INDEX_SRC.slice(iCss, iCss + 300);
        assertTrue(chunk.indexOf('width: min(500px, 45vw)') !== -1,
            'широкая панель — до 500px (Task 387, было 400px)');
    });''', 1))

t386.append(('386: SRC _legendWidthPx 500', '''    test('_legendWidthPx — явные ширины (узкий 190 / широкий кап)', () => {
        const fn = methodText(INDEX_SRC, '_legendWidthPx');
        assertTrue(fn.indexOf('190') !== -1, 'узкий вид — 190px');
        assertTrue(fn.indexOf('Math.min(400') !== -1 && fn.indexOf('0.45') !== -1,
            'широкий — min(400px, 45vw) (согласовано с CSS)');
        assertTrue(fn.indexOf('Math.max(190') !== -1,
            'широкий не уже 190px');
    });''', '''    test('_legendWidthPx — явные ширины (узкий 190 / широкий кап)', () => {
        const fn = methodText(INDEX_SRC, '_legendWidthPx');
        assertTrue(fn.indexOf('190') !== -1, 'узкий вид — 190px');
        assertTrue(fn.indexOf('Math.min(500') !== -1 && fn.indexOf('0.45') !== -1,
            'широкий — min(500px, 45vw) (согласовано с CSS; Task 387: 500px)');
        assertTrue(fn.indexOf('Math.max(190') !== -1,
            'широкий не уже 190px');
    });''', 1))

t386.append(('386: VM капы 500', '''    test('VM: _legendWidthPx — капы (190 / 400 / 45vw)', () => {
        const h = makeHost(true);            // vw не задан → 1280 fallback
        assertEqual(h.WSM._legendWidthPx(), 190, 'узкий — 190px');
        h.WSM._legendWide = true;
        assertEqual(h.WSM._legendWidthPx(), 400, 'широкий @1280 — 400px');
        // узкий экран: 45vw < 400
        const h2 = makeHost(true, 700);
        h2.WSM._legendWide = true;
        assertEqual(h2.WSM._legendWidthPx(), 315, 'широкий @700 — 45vw = 315px');
    });''', '''    test('VM: _legendWidthPx — капы (190 / 500 / 45vw)', () => {
        const h = makeHost(true);            // vw не задан → 1280 fallback
        assertEqual(h.WSM._legendWidthPx(), 190, 'узкий — 190px');
        h.WSM._legendWide = true;
        assertEqual(h.WSM._legendWidthPx(), 500, 'широкий @1280 — 500px (Task 387)');
        // узкий экран: 45vw < 500
        const h2 = makeHost(true, 700);
        h2.WSM._legendWide = true;
        assertEqual(h2.WSM._legendWidthPx(), 315, 'широкий @700 — 45vw = 315px');
    });''', 1))

t386.append(('386: VM повторное открытие 500px', '''        h.WSM._setLegend(true);              // открыли снова
        assertEqual(h.els().wsLegendDrawer.style.width, '400px',
            'открылась сразу ШИРОКОЙ (пережитый вид)');''', '''        h.WSM._setLegend(true);              // открыли снова
        assertEqual(h.els().wsLegendDrawer.style.width, '500px',
            'открылась сразу ШИРОКОЙ (пережитый вид; Task 387: 500px)');''', 1))

t386.append(('386: VM onLegendPageOpen — заметка Task 387', '''        assertTrue(body.indexOf('Обозначения в шахматке') !== -1, 'пояснения');
        assertTrue(body.indexOf('ст. 120 ТК РФ') !== -1, 'праздники отпусков');''', '''        assertTrue(body.indexOf('Обозначения в шахматке') !== -1, 'пояснения');
        // Task 387: пояснение праздников в отпусках УДАЛЕНО; живы
        // бейдж смены/«сегодня»/«красная рамка… (пример - 24*)»
        assertTrue(body.indexOf('(пример - 24*)') !== -1, 'сокращённый предпраздничный');
        assertFalse(body.indexOf('ст. 120 ТК РФ') !== -1, 'пояснение праздников удалено (Task 387)');''', 1))

patch('tests/test-task386.js', t386)

# ============================================================
# 2. test-task385.js — заметка «ст. 120» удалена
# ============================================================

t385 = []

t385.append(('385: _legendHtml заметка Task 387', '''        assertTrue(fn.indexOf('ст. 120 ТК РФ') !== -1, 'пояснение праздников в отпусках');''', '''        // Task 387: пояснение праздников в отпусках УДАЛЕНО; живо
        // переозвученное «Красная рамка… (пример - 24*)»
        assertTrue(fn.indexOf('(пример - 24*)') !== -1, 'сокращённый предпраздничный');
        assertFalse(fn.indexOf('ст. 120 ТК РФ') !== -1, 'пояснение праздников удалено (Task 387)');''', 1))

patch('tests/test-task385.js', t385)

# ============================================================
# 3. test-task312.js — «Выходной» без «·», фолбэк = канон, cur
# ============================================================

t312 = []

t312.append(('312: _fillStatusSelect фильтр cur', '''        assertTrue(fn.indexOf('this._EVENT_CODES.indexOf(c.code) !== -1 && c.code !== current') !== -1,
            'фильтр мероприятий с исключением текущего значения');''', '''        assertTrue(fn.indexOf('this._EVENT_CODES.indexOf(c.code) !== -1 && c.code !== cur') !== -1,
            'фильтр мероприятий с исключением текущего значения (Task 387: cur)');''', 1))

t312.append(('312: фолбэк = канон («Выходной» пустой код)', '''    test('JS: fallback-цвет «.» = #EEF0F2 (фон ЯЧЕЕК сетки, светлая тема)', () => {
        // Task 314: «.»-ячейка красится CSS-классом ws-dot-code —
        // фон ПУСТОЙ ячейки в любой теме; цвет листа/фолбэка к фону
        // ячейки НЕ применяется (значение справочное для листа:
        // #EEF0F2 — фон ячеек светлой темы, Task 250; #FAF9F5 —
        // это цвет СТРАНИЦЫ, ячейки чуть темнее)
        const lc = fnBody(INDEX_SRC, '_loadStatusCodes: function');
        assertTrue(lc.indexOf("{code:'.',    name:'Плановый выходной день', color:'#EEF0F2'}") !== -1,
            'fallback «.» — #EEF0F2 (фон ячеек светлой темы)');
        assertFalse(lc.indexOf("color:'#CFD8DC'") !== -1,
            'старый серо-голубой #CFD8DC не остался');
    });''', '''    test('JS: fallback = канон Task 387 («Выходной» — пустой код, #EEF0F2)', () => {
        // Task 314: «.»-ячейка красится CSS-классом ws-dot-code —
        // фон ПУСТОЙ ячейки в любой теме; цвет листа/канона к фону
        // ячейки НЕ применяется (значение справочное; #EEF0F2 — фон
        // ячеек светлой темы, Task 250). Task 387: fallback — КАНОН
        // _STATUS_CODES_CANON (порядок по группам, полные наимено-
        // вания), «Выходной» — ПУСТОЙ код (точка «·» убрана заявкой)
        const lc = fnBody(INDEX_SRC, '_loadStatusCodes: function');
        assertTrue(lc.indexOf('self._normalizeStatusCodes(self._STATUS_CODES_CANON)') !== -1,
            'fallback — канон _STATUS_CODES_CANON (Task 387)');
        assertTrue(INDEX_SRC.indexOf("{code:'',     name:'Выходной, плановый выходной день', color:'#EEF0F2'}") !== -1,
            'канон: «Выходной» — пустой код, #EEF0F2 (фон ячеек светлой темы)');
        assertFalse(INDEX_SRC.indexOf("color:'#CFD8DC'") !== -1,
            'старый серо-голубой #CFD8DC не остался');
    });''', 1))

t312.append(('312: попап/select — «Выходной» без «·»', '''    test('JS: попап/select — символ «·», свотч ws-swatch-dot', () => {
        const rp = fnBody(INDEX_SRC, '_renderCellPopup: function');
        assertTrue(rp.indexOf("var isDot = (c.code === '.');") !== -1,
            'детектор «.» в попапе');
        assertTrue(rp.indexOf("this._esc(isDot ? '·' : c.code)") !== -1,
            'метка «·» в строке кода');
        assertTrue(rp.indexOf('ws-popup-swatch ws-swatch-dot') !== -1,
            'свотч «.» — фон пустой ячейки (тема)');
        const fs2 = fnBody(INDEX_SRC, '_fillStatusSelect: function');
        assertTrue(fs2.indexOf("var label = (c.code === '.') ? '·' : c.code;") !== -1,
            'select «Дополнительно…»: метка «·», value «.»');
    });''', '''    test('JS: попап/select — «Выходной» БЕЗ кода-символа (Task 387), свотч ws-swatch-dot', () => {
        const rp = fnBody(INDEX_SRC, '_renderCellPopup: function');
        assertTrue(rp.indexOf("var isDot = (c.code === '.' || c.code === '');") !== -1,
            'детектор «Выходного»: пустой код ИЛИ легаси-«.»');
        assertTrue(rp.indexOf("this._esc(isDot ? '' : c.code)") !== -1,
            'метка строки «Выходного» ПУСТА (точка «·» убрана, Task 387)');
        assertFalse(rp.indexOf("this._esc(isDot ? '·' : c.code)") !== -1,
            'метки «·» в попапе больше нет');
        assertTrue(rp.indexOf('ws-popup-swatch ws-swatch-dot') !== -1,
            'свотч «Выходного» — фон пустой ячейки (тема)');
        const fs2 = fnBody(INDEX_SRC, '_fillStatusSelect: function');
        assertTrue(fs2.indexOf("if (c.code === '' || c.code === '.') continue;") !== -1,
            'select: «Выходной» — опцией «— выходной —» (без дубля)');
        assertTrue(fs2.indexOf("var cur = (current === '.') ? '' : current;") !== -1,
            'select: легаси-«.» текущего значения маппится в «— выходной —»');
    });''', 1))

patch('tests/test-task312.js', t312)

# ============================================================
# 4. test-task314.js — харнесс кэша: метод + канон
# ============================================================

t314 = []

t314.append(('314: mkCtx — канон + _normalizeStatusCodes', '''    function mkCtx(store, doc) {
        const ctx = {
            _year: 2026, _month: 9,
            _wsCacheKey: 'kip8_ws_cache_v1',
            _cacheTs: 0,
            _STATUS_CODES: [], _PATTERNS: [], _EMPLOYEES: [],
            _ENTRIES: [], _TRAININGS: [],
            _VACATIONS: [], _VAC_PAGE: [], _vacYear: null,
            _fillStatusSelectCount: 0,
            _fillStatusSelect: function () { this._fillStatusSelectCount++; }
        };
        ['_ymKey', '_cacheRead', '_restoreCachedView', '_cacheWrite', '_updateCacheStamp']
            .forEach(m => { ctx[m] = loadMethod(m, store, doc); });
        return ctx;
    }''', '''    // Task 387: канон справочника — вырезается из index.html
    // (_STATUS_CODES_CANON: [ … ]) скобочным балансом
    function canonCodes() {
        const i = INDEX_SRC.indexOf('_STATUS_CODES_CANON: [');
        if (i === -1) return [];
        const open = INDEX_SRC.indexOf('[', i);
        let depth = 0;
        for (let k = open; k < INDEX_SRC.length; k++) {
            if (INDEX_SRC[k] === '[') depth++;
            else if (INDEX_SRC[k] === ']') {
                depth--;
                if (!depth) return eval(INDEX_SRC.slice(open, k + 1));
            }
        }
        return [];
    }

    function mkCtx(store, doc) {
        const ctx = {
            _year: 2026, _month: 9,
            _wsCacheKey: 'kip8_ws_cache_v1',
            _cacheTs: 0,
            _STATUS_CODES: [], _PATTERNS: [], _EMPLOYEES: [],
            _ENTRIES: [], _TRAININGS: [],
            _VACATIONS: [], _VAC_PAGE: [], _vacYear: null,
            _STATUS_CODES_CANON: canonCodes(),
            _fillStatusSelectCount: 0,
            _fillStatusSelect: function () { this._fillStatusSelectCount++; }
        };
        ['_ymKey', '_cacheRead', '_restoreCachedView', '_cacheWrite', '_updateCacheStamp',
         '_normalizeStatusCodes']
            .forEach(m => { ctx[m] = loadMethod(m, store, doc); });
        return ctx;
    }''', 1))

t314.append(('314: кэш-тест — длины 2 (Д + «Выходной» из «.»)', '''        assertTrue(ctx._restoreCachedView(), 'вид 2026-09 восстановлен');
        assertEqual(ctx._STATUS_CODES.length, 2, 'коды');''', '''        assertTrue(ctx._restoreCachedView(), 'вид 2026-09 восстановлен');
        // Task 387: кэш нормализован — «.» → слот «Выходного» (пустой
        // код, каноническое имя), Д — канонический порядок/имя
        assertEqual(ctx._STATUS_CODES.length, 2, 'коды');
        assertEqual(ctx._STATUS_CODES[0].code, 'Д', 'первый — Д (канонический порядок)');
        assertEqual(ctx._STATUS_CODES[1].code, '', 'второй — «Выходной» (пустой код)');
        assertTrue(ctx._STATUS_CODES[1].name.indexOf('Выходной') !== -1,
            'имя «Выходного» каноническое');''', 1))

patch('tests/test-task314.js', t314)

# ============================================================
# 5. test-task356.js — метки «·» в попапе/select убраны
# ============================================================

t356 = []

t356.append(('356: метки «·» убраны (Task 387)', '''    test('метка «·» в ПОПАПЕ выбора статуса и select сохранена', () => {
        // код «.» в попапе/списке по-прежнему подписан «·» — заявка
        // касается только ячеек шахматки
        assertTrue(INDEX_SRC.indexOf("this._esc(isDot ? '·' : c.code)") !== -1,
            'попап: isDot ? «·» : код');
        assertTrue(INDEX_SRC.indexOf("var label = (c.code === '.') ? '·' : c.code;") !== -1,
            'select «Дополнительно…»: метка «·»');
    });''', '''    test('Task 387: метка «·» убрана и в ПОПАПЕ/select — «Выходной» без кода', () => {
        // Task 387 (заявка: «я убрал точку — теперь просто пустая
        // ячейка белого цвета»): строка «Выходного» в попапе — БЕЗ
        // кода-символа (свотч-пустая ячейка); в select «Выходной»
        // представлен опцией «— выходной —»
        assertTrue(INDEX_SRC.indexOf("this._esc(isDot ? '' : c.code)") !== -1,
            'попап: isDot ? пусто : код (метка «·» удалена)');
        assertFalse(INDEX_SRC.indexOf("this._esc(isDot ? '·' : c.code)") !== -1,
            'метки «·» в попапе больше нет');
        assertFalse(INDEX_SRC.indexOf("var label = (c.code === '.') ? '·' : c.code;") !== -1,
            'метки «·» в select больше нет (Task 387)');
        assertTrue(INDEX_SRC.indexOf("if (c.code === '' || c.code === '.') continue;") !== -1,
            'select: «Выходной» — опцией «— выходной —»');
    });''', 1))

patch('tests/test-task356.js', t356)

# ============================================================
# 6. test-task360.js — фильтр печати (Task 387: «.»→«Выходной»)
# ============================================================

t360 = []

t360.append(('360: фильтр usedCodes + «Выходной»', '''        const iFilter = b.indexOf('if (!usedCodes[codes[ci].code]) continue;');
        const iLoop = b.indexOf('for (var ci = 0; ci < codes.length; ci++)');
        assertTrue(iFilter !== -1, 'коды вне месяца пропускаются');
        assertTrue(iLoop !== -1 && iFilter > iLoop,
            'фильтр внутри цикла справочника (порядок = справочник)');''', '''        const iFilter = b.indexOf('if (!usedCodes[codes[ci].code]');
        const iWykh = b.indexOf("!(codes[ci].code === '' && usedCodes['.'])");
        const iLoop = b.indexOf('for (var ci = 0; ci < codes.length; ci++)');
        assertTrue(iFilter !== -1, 'коды вне месяца пропускаются');
        assertTrue(iWykh !== -1, 'Task 387: легаси-«.» раскрывается строкой «Выходного»');
        assertTrue(iLoop !== -1 && iFilter > iLoop,
            'фильтр внутри цикла справочника (порядок = справочник)');''', 1))

patch('tests/test-task360.js', t360)

# ============================================================
# 7. test-work-schedule.js — фолбэк = канон (16, «Выходной» «»)
# ============================================================

tws = []

tws.append(('WS: фолбэк-канон — «Выходной» пустой код', '''    test('JS: fallback-набор _loadStatusCodes = 16 новых кодов', () => {
        // все новые коды должны быть в fallback (офлайн/старый сервер)
        const codes = ['Д8', 'Д7,2', 'д', 'н', 'ОТ', 'У', 'ОВ', 'ПР', '.'];
        codes.forEach(c => {
            assertTrue(html.indexOf("{code:'" + c + "'") !== -1,
                'fallback содержит код «' + c + '»');
        });
    });''', '''    test('JS: fallback-набор (канон Task 387) = 16 новых кодов', () => {
        // все новые коды должны быть в каноне _STATUS_CODES_CANON
        // (офлайн/старый сервер); Task 387: «Выходной» — ПУСТОЙ код
        // (точка «·» убрана заявкой: выходной = пустая ячейка)
        const codes = ['Д8', 'Д7,2', 'д', 'н', 'ОТ', 'У', 'ОВ', 'ПР'];
        codes.forEach(c => {
            assertTrue(html.indexOf("{code:'" + c + "'") !== -1,
                'канон содержит код «' + c + '»');
        });
        assertTrue(html.indexOf("{code:'',     name:'Выходной, плановый выходной день', color:'#EEF0F2'}") !== -1,
            'канон: «Выходной» — пустой код (точка убрана, Task 387)');
    });''', 1))

patch('tests/test-work-schedule.js', tws)

print('OK: Task 387 — тесты адаптированы')
