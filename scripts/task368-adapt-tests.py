#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 368: адаптация существующих тестов под новую семантику
# недельных/месячных расходомеров (красный по ЗАКРЫТЫМ календарным
# периодам, зелёный — период данных накрывает закрытую неделю/месяц).
#   - tests/extract-functions.js: flowPrevWeekRange в списке PURE_FUNCTIONS
#   - tests/test-flow-period-input.js: 2 ассерта «flowPrevWeekRange
#     удалена» перевернуты (Task 368 вернул хелпер для ПОКАЗАНИЙ
#     за период; chip «За неделю» у №1 по-прежнему нет)
#   - tests/test-task357.js: Mixin + _recordCoversPeriod; недельный и
#     месячный describe переписаны; Sheet-мок дополнен классификаторами
#   - tests/test-task365.js: Mixin; тесты §C под новую семантику
#   - tests/test-task367.js: Mixin; недельный и месячный describe переписаны
import io

def rep(path, old, new, label, count=1):
    s = io.open(path, encoding='utf-8').read()
    n = s.count(old)
    assert n == count, '%s: якорь найден %d раз (ожидалось %d)' % (label, n, count)
    io.open(path, 'w', encoding='utf-8').write(s.replace(old, new))
    print('  OK %s' % label)

# ================================================================
# 1. tests/extract-functions.js — flowPrevWeekRange в PURE_FUNCTIONS
# ================================================================
rep('tests/extract-functions.js',
"""    'flowPrevMonthRange',
    'flowWeekCounterStats',
""",
"""    'flowPrevMonthRange',
    // Task 368: показания за период — границы прошедшей календарной
    // недели (пн–вс) для недельных расходомеров (№3, №11)
    'flowPrevWeekRange',
    'flowWeekCounterStats',
""",
'1: extract-functions — flowPrevWeekRange')

# ================================================================
# 2. tests/test-flow-period-input.js — 2 ассерта про flowPrevWeekRange
# ================================================================
rep('tests/test-flow-period-input.js',
"""        assertFalse(INDEX_SRC.indexOf('flowPrevWeekRange') !== -1,
            'Task 289: flowPrevWeekRange удалена (неделя не вводится)');
""",
"""        // Task 368: хелпер возвращён — границы прошедшей недели для
        // ПОКАЗАНИЙ №3/№11 (chip «За неделю» у №1 по-прежнему нет — тест выше)
        assertTrue(INDEX_SRC.indexOf('function flowPrevWeekRange(now)') !== -1,
            'Task 368: flowPrevWeekRange есть (период показаний недельных)');
""",
'2a: flow-period-input — SRC-ассерт')

rep('tests/test-flow-period-input.js',
"""        assertFalse(EXTRACT_SRC.indexOf("'flowPrevWeekRange'") !== -1,
            'Task 289: flowPrevWeekRange не извлекается (неделя не вводится)');
""",
"""        assertTrue(EXTRACT_SRC.indexOf("'flowPrevWeekRange'") !== -1,
            'Task 368: flowPrevWeekRange извлекается (период показаний)');
""",
'2b: flow-period-input — EXTRACT-ассерт')

# ================================================================
# 3. tests/test-task357.js
# ================================================================
rep('tests/test-task357.js',
"""//        «Еженедельно» — прошла календарная неделя (пн–вс) последних
//                        данных;
//        «Ежемесячно»  — прошёл календарный месяц последних данных.
""",
"""//        «Еженедельно» / «Ежемесячно» (Task 368): показания вводятся
//                        за период двух дат; зелёный — период данных
//                        накрывает последнюю ЗАКРЫТУЮ неделю (пн–вс) /
//                        месяц; красный — закрытый период без данных.
""",
'3a: 357 — шапка')

rep('tests/test-task357.js',
"""    const parts = ['_isOverdue', '_parseMdy', '_dayKey', '_mondayOf']
        .map(n => extractMethod(INDEX_SRC, n))
        .filter(Boolean);
    if (parts.length === 4) {
""",
"""    const parts = ['_isOverdue', '_parseMdy', '_dayKey', '_mondayOf', '_recordCoversPeriod']
        .map(n => extractMethod(INDEX_SRC, n))
        .filter(Boolean);
    if (parts.length === 5) {
""",
'3b: 357 — Mixin + _recordCoversPeriod')

rep('tests/test-task357.js',
"""        vm.runInContext(
            'var Sheet = { ' + applySrc + ',' +
            ' _isDailyMode: function(m) { return !!(m && m.id === 1); },' +
            " _inputEntryType: 'сутки' };",
            ctx);
""",
"""        vm.runInContext(
            'var Sheet = { ' + applySrc + ',' +
            ' _isDailyMode: function(m) { return !!(m && m.id === 1); },' +
            // Task 368: реальные классификаторы периода — ветка показаний
            // за период в _applyEntryTypeFields (для суточных меток §C
            // возвращают false, ветка пропускается)
            " _isWeeklyMeter: function(m) { return !this._isDailyMode(m) && /недел|еженед/.test(String((m && m.period) || '').toLowerCase()); }," +
            " _isMonthlyMeter: function(m) { return !this._isDailyMode(m) && /месяц|месяч|ежемес/.test(String((m && m.period) || '').toLowerCase()); }," +
            (extractMethod(INDEX_SRC, '_parseMdy') || '_parseMdy: function(s) { return null; }') + ',' +
            " _inputEntryType: 'сутки' };",
            ctx);
""",
'3c: 357 — Sheet-мок классификаторы')

# 3d: недельный describe (между заголовками секций A)
s = io.open('tests/test-task357.js', encoding='utf-8').read()
i1 = s.index('// A. _isOverdue — «Еженедельно»')
i1 = s.rindex('// ============================================================', 0, i1)
i2 = s.index('// A. _isOverdue — «Ежемесячно»')
i2 = s.rindex('// ============================================================', 0, i2)
weekly_new = """// ============================================================
// A. _isOverdue — «Еженедельно» (Task 368: ЗАКРЫТАЯ неделя пн–вс)
// ============================================================
describe('Task 357 — _isOverdue: «Еженедельно» (закрытая неделя, Task 368)', () => {
    // Task 368: ссылка — последняя ЗАКРЫТАЯ календарная неделя:
    // «сейчас» чт 10.09.2026 → закрытая 31.08–06.09;
    // «сейчас» пн 14.09.2026 → закрытая 07.09–13.09.

    test('Период данных = закрытая неделя (8/31–9/6), сейчас чт 10.09 → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', datePrev: '8/31/2026', dateCurr: '9/6/2026' }, new Date(2026, 8, 10, 12, 0));
        assertFalse(r, 'данные за прошедшую неделю введены');
    });

    test('Закрытая неделя без данных (точка 9/6), сейчас чт 10.09 → КРАСНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/6/2026' }, new Date(2026, 8, 10, 12, 0));
        assertTrue(r, 'календарная неделя прошла — пора вводить');
    });

    test('Снова красный: данные 8/31–9/6, наступил пн 14.09 → КРАСНЫЙ (закрылась 07–13.09)', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', datePrev: '8/31/2026', dateCurr: '9/6/2026' }, new Date(2026, 8, 14, 0, 30));
        assertTrue(r, 'новая неделя прошла — ждем данные за неё');
    });

    test('Ввели за закрывшуюся неделю (9/7–9/13), пн 14.09 12:00 → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', datePrev: '9/7/2026', dateCurr: '9/13/2026' }, new Date(2026, 8, 14, 12, 0));
        assertFalse(r, 'пока следующая неделя не закрылась — зелёный');
    });

    test('Точечная запись внутри закрытой недели (9/9), пн 14.09 → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/9/2026' }, new Date(2026, 8, 14, 12, 0));
        assertFalse(r, 'показание снято в течение недели 07–13.09');
    });

    test('Ранний ввод текущей недели (точка 9/9), чт 10.09 → КРАСНЫЙ (закрытая 31.08–06.09 не накрыта)', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/9/2026' }, new Date(2026, 8, 10, 12, 0));
        assertTrue(r, 'данные нужны за ЗАКРЫТУЮ неделю');
    });

    test('Запись накрывает границу недель (8/31–9/8), чт 10.09 → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', datePrev: '8/31/2026', dateCurr: '9/8/2026' }, new Date(2026, 8, 10, 12, 0));
        assertFalse(r, 'пересечения с закрытой неделей достаточно');
    });

    test('Переход года: пн 04.01.2027, данные 28.12.2026–03.01.2027 → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', datePrev: '12/28/2026', dateCurr: '1/3/2027' }, new Date(2027, 0, 4, 10, 0));
        assertFalse(r, 'закрытая неделя накрыта через границу года');
    });

    test('Переход года: пн 04.01.2027, точка 27.12.2026 → КРАСНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '12/27/2026' }, new Date(2027, 0, 4, 10, 0));
        assertTrue(r, 'данные старше закрытой недели 28.12–03.01');
    });

    test('Нет данных → КРАСНЫЙ', () => {
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: null }, new Date(2026, 8, 10, 12, 0)),
            'нет данных — пора');
    });
});

"""
s = s[:i1] + weekly_new + s[i2:]
io.open('tests/test-task357.js', 'w', encoding='utf-8').write(s)
print('  OK 3d: 357 — недельный describe переписан')

# 3e: месячный describe
s = io.open('tests/test-task357.js', encoding='utf-8').read()
i1 = s.index('// A. _isOverdue — «Ежемесячно»')
i1 = s.rindex('// ============================================================', 0, i1)
i2 = s.index('// B. Хелперы _parseMdy / _dayKey / _mondayOf')
i2 = s.rindex('// ============================================================', 0, i2)
monthly_new = """// ============================================================
// A. _isOverdue — «Ежемесячно» (Task 368: ЗАКРЫТЫЙ месяц)
// ============================================================
describe('Task 357 — _isOverdue: «Ежемесячно» (закрытый месяц, Task 368)', () => {
    // Task 368: ссылка — последний ЗАКРЫТЫЙ календарный месяц:
    // «сейчас» сентябрь → закрытый август; «сейчас» октябрь → сентябрь.

    test('Период данных = прошлый месяц (8/1–8/31), сейчас 10.09 → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '8/1/2026', dateCurr: '8/31/2026' }, new Date(2026, 8, 10, 12, 0));
        assertFalse(r, 'данные за закрытый месяц введены');
    });

    test('Закрытый месяц без данных (точка 7/20), сейчас сентябрь → КРАСНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '7/20/2026' }, new Date(2026, 8, 10, 12, 0));
        assertTrue(r, 'календарный месяц прошёл — пора вводить');
    });

    test('Граница: 30 сент 23:59 (данные 8/1–8/31) — ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '8/1/2026', dateCurr: '8/31/2026' }, new Date(2026, 8, 30, 23, 59));
        assertFalse(r, 'сентябрь ещё не закрыт — август накрыт');
    });

    test('Граница: 1 окт 00:05 (данные 8/1–8/31) — КРАСНЫЙ (сентябрь закрылся)', () => {
        const r = Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '8/1/2026', dateCurr: '8/31/2026' }, new Date(2026, 9, 1, 0, 5));
        assertTrue(r, 'текущий месяц прошёл — ждем данные за его период');
    });

    test('Ввели за закрывшийся месяц (9/1–9/30), октябрь → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '9/1/2026', dateCurr: '9/30/2026' }, new Date(2026, 9, 15, 10, 0));
        assertFalse(r, 'пока следующий месяц не закрылся — зелёный');
    });

    test('Точечная запись внутри закрытого месяца (8/20), сентябрь → ЗЕЛЁНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '8/20/2026' }, new Date(2026, 8, 16, 10, 0));
        assertFalse(r, 'показание снято в течение августа');
    });

    test('Переход года: январь 2027, данные 12/1–12/31 → ЗЕЛЁНЫЙ; точка 11/15 → КРАСНЫЙ', () => {
        const g = Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '12/1/2026', dateCurr: '12/31/2026' }, new Date(2027, 0, 10, 10, 0));
        assertFalse(g, 'закрытый декабрь накрыт через границу года');
        const r = Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '11/15/2026' }, new Date(2027, 0, 10, 10, 0));
        assertTrue(r, 'декабрь без данных');
    });

    test('Нет данных → КРАСНЫЙ', () => {
        assertTrue(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: null }, new Date(2026, 8, 10, 12, 0)),
            'нет данных — пора');
    });
});

"""
s = s[:i1] + monthly_new + s[i2:]
io.open('tests/test-task357.js', 'w', encoding='utf-8').write(s)
print('  OK 3e: 357 — месячный describe переписан')

# ================================================================
# 4. tests/test-task365.js
# ================================================================
rep('tests/test-task365.js',
"""    const parts = ['_isOverdue', '_parseMdy', '_dayKey', '_mondayOf', '_normalizeMeters']
        .map(n => extractMethod(INDEX_SRC, n))
        .filter(Boolean);
    if (parts.length === 5) {
""",
"""    const parts = ['_isOverdue', '_parseMdy', '_dayKey', '_mondayOf', '_recordCoversPeriod', '_normalizeMeters']
        .map(n => extractMethod(INDEX_SRC, n))
        .filter(Boolean);
    if (parts.length === 6) {
""",
'4a: 365 — Mixin + _recordCoversPeriod')

rep('tests/test-task365.js',
"""    test('Без нормализации недельная логика дала бы ЗЕЛЁНЫЙ (та же неделя)', () => {
        // 11.09.2026 — пятница; данные 9/9 (среда) — та же неделя
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/9/2026' }, new Date(2026, 8, 11, 7, 0)),
            'недельный период держал бы зелёный до понедельника');
    });
""",
"""    test('Без нормализации недельная логика дала бы КРАСНЫЙ (Task 368: закрытая неделя)', () => {
        // 11.09.2026 — пятница; данные 9/9 (точка) не накрывают
        // закрытую неделю 31.08–06.09 — «пора вводить»
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/9/2026' }, new Date(2026, 8, 11, 7, 0)),
            'недельный ритм Task 368: закрытая неделя без данных');
    });
""",
'4b: 365 — тест без нормализации')

rep('tests/test-task365.js',
"""    test('№3 (настоящий недельный) НЕ нормализуется — зелёный до понедельника', () => {
        const meters = Mixin._normalizeMeters([{ id: 3, period: 'Еженедельно', dateCurr: '9/9/2026' }]);
        assertFalse(Mixin._isOverdue(meters[0], new Date(2026, 8, 11, 7, 0)),
            'недельные расходомеры сохраняют недельный ритм');
    });
""",
"""    test('№3 (настоящий недельный) НЕ нормализуется — недельный ритм жив (Task 368)', () => {
        const meters = Mixin._normalizeMeters([{ id: 3, period: 'Еженедельно', datePrev: '8/31/2026', dateCurr: '9/6/2026' }]);
        assertEqual(meters[0].period, 'Еженедельно', 'период не нормализован');
        assertFalse(Mixin._isOverdue(meters[0], new Date(2026, 8, 11, 7, 0)),
            'данные накрывают закрытую неделю 31.08–06.09 — зелёный');
    });
""",
'4c: 365 — тест №3')

# ================================================================
# 5. tests/test-task367.js
# ================================================================
rep('tests/test-task367.js',
"""//   B. VM — _isOverdue: недельные по КАЛЕНДАРНОЙ неделе пн–вс,
//      месячные по месяцу (Task 357 подтверждён + закреплён);
//      сокращения («Еженед.», «Ежемес.») и «N раз в неделю/месяц»
//      попадают в свою ветку (раньше считались суточными);
//      суточная логика (6:00, Task 365) не сломана.
""",
"""//   B. VM — _isOverdue (Task 368): недельные/месячные — зелёный,
//      пока период данных накрывает последнюю ЗАКРЫТУЮ неделю
//      (пн–вс) / месяц; красный — закрытый период без данных;
//      сокращения («Еженед.», «Ежемес.») в своей ветке;
//      суточная логика (6:00, Task 365) не сломана.
""",
'5a: 367 — шапка')

rep('tests/test-task367.js',
"""    const parts = ['_isOverdue', '_parseMdy', '_dayKey', '_mondayOf']
        .map(n => extractMethod(INDEX_SRC, n)).filter(Boolean);
    if (parts.length === 4) {
""",
"""    const parts = ['_isOverdue', '_parseMdy', '_dayKey', '_mondayOf', '_recordCoversPeriod']
        .map(n => extractMethod(INDEX_SRC, n)).filter(Boolean);
    if (parts.length === 5) {
""",
'5b: 367 — Mixin + _recordCoversPeriod')

# 5c: недельный describe
s = io.open('tests/test-task367.js', encoding='utf-8').read()
i1 = s.index("describe('Task 367 — VM: еженедельные — красный по КАЛЕНДАРНОЙ неделе', () => {")
i2 = s.index("describe('Task 367 — VM: ежемесячные — красный по КАЛЕНДАРНОМУ месяцу', () => {")
weekly_new = """describe('Task 367 — VM: еженедельные — по ЗАКРЫТОЙ неделе (Task 368)', () => {
    // «Сейчас» чт 10.09 → закрытая неделя 31.08–06.09;
    // «сейчас» пн 14.09 → закрытая неделя 07.09–13.09.

    test('Период данных 8/31–9/6, сейчас чт 10.09 — ЗЕЛЁНЫЙ (данные этой недели введены)', () => {
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', datePrev: '8/31/2026', dateCurr: '9/6/2026' }, new Date(2026, 8, 10, 12, 0)),
            'закрытая неделя накрыта');
    });

    test('Точка в текущей неделе (9/9), сейчас чт 10.09 — КРАСНЫЙ (закрытая неделя не накрыта)', () => {
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/9/2026' }, new Date(2026, 8, 10, 12, 0)),
            'нужны данные за закрытую 31.08–06.09');
    });

    test('Граница: вс 13.09 23:59 (данные 8/31–9/6) — ЗЕЛЁНЫЙ; пн 14.09 00:30 — КРАСНЫЙ', () => {
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', datePrev: '8/31/2026', dateCurr: '9/6/2026' }, new Date(2026, 8, 13, 23, 59)),
            'неделя 07–13.09 ещё не закрыта');
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', datePrev: '8/31/2026', dateCurr: '9/6/2026' }, new Date(2026, 8, 14, 0, 30)),
            'неделя закрылась — пока не введут за неё данные');
    });

    test('Точка вс 13.09, сейчас пн 14.09 — ЗЕЛЁНЫЙ (внутри закрытой недели)', () => {
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/13/2026' }, new Date(2026, 8, 14, 12, 0)),
            'показание снято в течение закрытой недели');
    });

    test('Сокращение «Еженед.» — недельная ветка (не суточная)', () => {
        assertFalse(Mixin._isOverdue({ period: 'Еженед.', datePrev: '8/31/2026', dateCurr: '9/6/2026' }, new Date(2026, 8, 10, 12, 0)),
            'закрытая неделя накрыта — зелёный');
        assertTrue(Mixin._isOverdue({ period: 'Еженед.', dateCurr: '9/9/2026' }, new Date(2026, 8, 10, 12, 0)),
            'точка в текущей неделе — красный');
    });

    test('«1 раз в неделю» — недельная ветка', () => {
        assertTrue(Mixin._isOverdue({ period: '1 раз в неделю', dateCurr: '9/9/2026' }, new Date(2026, 8, 10, 12, 0)),
            'закрытая неделя 31.08–06.09 без данных — красный');
    });

    test('Нет данных — красный (недельный)', () => {
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: null }, new Date(2026, 8, 10, 12, 0)),
            'данных нет — пора вводить');
    });
});

"""
s = s[:i1] + weekly_new + s[i2:]
io.open('tests/test-task367.js', 'w', encoding='utf-8').write(s)
print('  OK 5c: 367 — недельный describe переписан')

# 5d: месячный describe
s = io.open('tests/test-task367.js', encoding='utf-8').read()
i1 = s.index("describe('Task 367 — VM: ежемесячные — красный по КАЛЕНДАРНОМУ месяцу', () => {")
i2 = s.index("describe('Task 367 — VM: суточная логика (Task 365) не сломана', () => {")
monthly_new = """describe('Task 367 — VM: ежемесячные — по ЗАКРЫТОМУ месяцу (Task 368)', () => {

    test('Период данных = август (8/1–8/31), сейчас 16.09 — ЗЕЛЁНЫЙ', () => {
        assertFalse(Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '8/1/2026', dateCurr: '8/31/2026' }, new Date(2026, 8, 16, 10, 0)),
            'данные за этот [закрытый] месяц введены');
    });

    test('Данные старше закрытого месяца (точка 7/20), сейчас 16.09 — КРАСНЫЙ', () => {
        assertTrue(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '7/20/2026' }, new Date(2026, 8, 16, 10, 0)),
            'август без данных');
    });

    test('Граница: 30 сент 23:59 — ЗЕЛЁНЫЙ (август накрыт), 1 окт 00:30 — КРАСНЫЙ', () => {
        assertFalse(Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '8/1/2026', dateCurr: '8/31/2026' }, new Date(2026, 8, 30, 23, 59)),
            'сентябрь ещё не закрыт');
        assertTrue(Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '8/1/2026', dateCurr: '8/31/2026' }, new Date(2026, 9, 1, 0, 30)),
            'сентябрь закрылся — данные за его период не введены');
    });

    test('Точка внутри закрытого месяца (9/10), сейчас октябрь — ЗЕЛЁНЫЙ', () => {
        assertFalse(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '9/10/2026' }, new Date(2026, 9, 15, 10, 0)),
            'показание снято в течение сентября');
    });

    test('Годовой переход: янв 2027, данные 12/1–12/31 — ЗЕЛЁНЫЙ; точка 12/15 — тоже', () => {
        assertFalse(Mixin._isOverdue({ period: 'Ежемесячно', datePrev: '12/1/2026', dateCurr: '12/31/2026' }, new Date(2027, 0, 10, 10, 0)),
            'декабрь накрыт через границу года');
        assertFalse(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '12/15/2026' }, new Date(2027, 0, 10, 10, 0)),
            'точка внутри закрытого декабря');
    });

    test('Сокращения «Ежемес.» и «раз в месяц» — месячная ветка', () => {
        assertTrue(Mixin._isOverdue({ period: 'Ежемес.', dateCurr: '7/20/2026' }, new Date(2026, 8, 16, 10, 0)),
            '«Ежемес.» — закрытый август без данных — красный');
        assertTrue(Mixin._isOverdue({ period: 'раз в месяц', dateCurr: '7/20/2026' }, new Date(2026, 8, 16, 10, 0)),
            '«раз в месяц» — красный');
        assertFalse(Mixin._isOverdue({ period: 'раз в месяц', datePrev: '8/1/2026', dateCurr: '8/31/2026' }, new Date(2026, 8, 16, 10, 0)),
            '«раз в месяц» — август накрыт — зелёный');
    });
});

"""
s = s[:i1] + monthly_new + s[i2:]
io.open('tests/test-task367.js', 'w', encoding='utf-8').write(s)
print('  OK 5d: 367 — месячный describe переписан')

print('Адаптация тестов Task 368 завершена.')
