#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 368: фикс тестов после первого прогона —
#   1) test-task368.js: хронология — indexOf('}', ri) находил «}» из самого
#      «} else if» (искать от ri+1); legacy-фикстура «точка 9/6» сама
#      внутри закрытой недели [31.08–06.09] — точка должна быть ДО неё;
#   2) test-task357.js: та же ошибка фикстуры «точка 9/6» → 8/24;
#   3) test-flowmeter-validation.js (Task 247): дата теперь вычисляется
#      в переменной lastDateInline/lastDateInline368 — ассерты переписаны
#      под новую структуру С СОХРАНЕНИЕМ СМЫСЛА (пробел вне nowrap-span,
#      «за» в начале блока даты).
import io

def rep(path, old, new, label, count=1):
    s = io.open(path, encoding='utf-8').read()
    n = s.count(old)
    assert n == count, '%s: якорь найден %d раз (ожидалось %d)' % (label, n, count)
    io.open(path, 'w', encoding='utf-8').write(s.replace(old, new))
    print('  OK %s' % label)

# ================================================================
# 1. tests/test-task368.js
# ================================================================
rep('tests/test-task368.js',
"""        const ri = m.indexOf('} else if (isMeterPeriodRow && _flowParseDate(r.datePrev) &&');
        assertTrue(ri !== -1, 'ветка диапазона записей');
        const chunk = m.slice(ri, m.indexOf('}', ri) + 1);
""",
"""        const ri = m.indexOf('} else if (isMeterPeriodRow && _flowParseDate(r.datePrev) &&');
        assertTrue(ri !== -1, 'ветка диапазона записей');
        // indexOf от ri+1: ri указывает на «}» самого «} else if»
        const chunk = m.slice(ri, m.indexOf('}', ri + 1) + 1);
""",
'1a: 368 — хронология chunk')

rep('tests/test-task368.js',
"""    test('Legacy без datePrev — точечный период; инвертированный datePrev зажат', () => {
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/6/2026', datePrev: null }, new Date(2026, 8, 10, 12, 0)),
            'нет datePrev — точка 9/6 не накрывает 31.08–06.09');
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/6/2026', datePrev: '9/8/2026' }, new Date(2026, 8, 10, 12, 0)),
            'битый datePrev (позже dateCurr) зажат в точку 9/6 — внутри закрытой недели');
    });
""",
"""    test('Legacy без datePrev — точечный период [d…d]; инвертированный datePrev зажат', () => {
        // точка ДО закрытой недели 31.08–06.09 — красный
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '8/30/2026', datePrev: null }, new Date(2026, 8, 10, 12, 0)),
            'нет datePrev — точка 8/30 не накрывает 31.08–06.09');
        // точка ВНУТРИ закрытой недели (вс 06.09) — зелёный
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/6/2026', datePrev: null }, new Date(2026, 8, 10, 12, 0)),
            'точечное показание внутри закрытой недели — тоже её данные');
        // битый datePrev (позже dateCurr) зажат в точку 9/6 — зелёный
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/6/2026', datePrev: '9/8/2026' }, new Date(2026, 8, 10, 12, 0)),
            'инвертированный datePrev зажат в точку внутри закрытой недели');
    });
""",
'1b: 368 — legacy-фикстуры')

# ================================================================
# 2. tests/test-task357.js — точка 9/6 сама внутри закрытой недели
# ================================================================
rep('tests/test-task357.js',
"""    test('Закрытая неделя без данных (точка 9/6), сейчас чт 10.09 → КРАСНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/6/2026' }, new Date(2026, 8, 10, 12, 0));
        assertTrue(r, 'календарная неделя прошла — пора вводить');
    });
""",
"""    test('Закрытая неделя без данных (точка 8/24 — двухнедельной давности), чт 10.09 → КРАСНЫЙ', () => {
        const r = Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '8/24/2026' }, new Date(2026, 8, 10, 12, 0));
        assertTrue(r, 'календарная неделя 31.08–06.09 прошла без данных');
    });
""",
'2: 357 — фикстура точки')

# ================================================================
# 3. tests/test-flowmeter-validation.js — Task 247 (структура Task 368)
# ================================================================
rep('tests/test-flowmeter-validation.js',
"""    test('HTML: блок даты начинается с «за» БЕЗ ведущего пробела внутри span', () => {
        assertTrue(html.indexOf('<span class="flow-detail-date-inline">за ') !== -1,
            'span даты должен начинаться сразу с «за» (без пробела внутри)');
        assertTrue(html.indexOf('<span class="flow-detail-date-inline"> за ') === -1,
            'Старый паттерн с пробелом внутри span не должен остаться (пробел внутри nowrap-блока запретил бы перенос между названием и датой)');
    });

    test('HTML: пробел-разделитель ВНЕ span (перенос между названием и датой)', () => {
        // В _buildDetailHtml: lastReadingLabel + ' <span class="flow-detail-date-inline">за '
        // (пробел — внутри строкового литерала, но ЗА пределами HTML-тега span)
        const re = /lastReadingLabel \\+\\s*' <span class="flow-detail-date-inline">за '/;
        assertTrue(re.test(html),
            'Пробел между «Последние показания» и span даты должен быть снаружи — единственная точка переноса строки');
    });
""",
"""    test('HTML: блок даты начинается с «за» БЕЗ ведущего пробела внутри span', () => {
        // Task 368: дата вычисляется в переменной lastDateInline (для
        // периодных — «за ДД.ММ–ДД.ММ.ГГГГ») и начинается с «за »
        assertTrue(html.indexOf("var lastDateInline = 'за ' + this._fmtDate(m.dateCurr)") !== -1,
            'блок даты начинается сразу с «за» (без пробела внутри)');
        assertTrue(html.indexOf('<span class="flow-detail-date-inline"> за ') === -1,
            'Старый паттерн с пробелом внутри span не должен остаться (пробел внутри nowrap-блока запретил бы перенос между названием и датой)');
    });

    test('HTML: пробел-разделитель ВНЕ span (перенос между названием и датой)', () => {
        // Task 368: lastReadingLabel + ' <span class="flow-detail-date-inline">' + lastDateInline
        // (пробел — внутри строкового литерала, но ЗА пределами HTML-тега span)
        const re = /lastReadingLabel \\+\\s*' <span class="flow-detail-date-inline">' \\+ lastDateInline/;
        assertTrue(re.test(html),
            'Пробел между «Последние показания» и span даты должен быть снаружи — единственная точка переноса строки');
    });
""",
'3a: 247 — детальная карточка')

rep('tests/test-flowmeter-validation.js',
"""    test('HTML: блок даты начинается с «за» БЕЗ ведущего пробела внутри span', () => {
        assertTrue(html.indexOf('<span class="flow-summary-date-inline">за ') !== -1,
            'span даты в карточке списка должен начинаться сразу с «за»');
        assertTrue(html.indexOf('<span class="flow-summary-date-inline"> за ') === -1,
            'Старый паттерн с пробелом внутри span не должен остаться в карточках списка');
    });

    test('HTML: пробел-разделитель ВНЕ span в renderList', () => {
        // В renderList: «Последние показания <span class="flow-summary-date-inline">за »
        assertTrue(html.indexOf('Последние показания <span class="flow-summary-date-inline">за ') !== -1,
            'Между «Последние показания» и span даты должен стоять пробел снаружи span');
    });
""",
"""    test('HTML: блок даты начинается с «за» БЕЗ ведущего пробела внутри span', () => {
        // Task 368: дата вычисляется в переменной lastDateInline368 (для
        // периодных — «за ДД.ММ–ДД.ММ.ГГГГ») и начинается с «за »
        assertTrue(html.indexOf("var lastDateInline368 = 'за ' + this._fmtDate(m.dateCurr)") !== -1,
            'span даты в карточке списка начинается сразу с «за»');
        assertTrue(html.indexOf('<span class="flow-summary-date-inline"> за ') === -1,
            'Старый паттерн с пробелом внутри span не должен остаться в карточках списка');
    });

    test('HTML: пробел-разделитель ВНЕ span в renderList', () => {
        // Task 368: «Последние показания <span class="flow-summary-date-inline">' + lastDateInline368
        const re = /Последние показания <span class="flow-summary-date-inline">' \\+ lastDateInline368/;
        assertTrue(re.test(html),
            'Между «Последние показания» и span даты должен стоять пробел снаружи span');
    });
""",
'3b: 247 — карточки списка')

print('Фиксы тестов Task 368 применены.')
