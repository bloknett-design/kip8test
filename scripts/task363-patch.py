#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 363: правки index.html — шахматка табеля (экран):
#   1) фон обычных ВЫХОДНЫХ дней = фон пустых ячеек (розовый
#      убран: розовый остаётся только у ПРАЗДНИКОВ);
#   2) толстая красная (3px #e53935) рамка вокруг ГРУППЫ столбцов
#      выходных (не каждую ячейку), включая шапку с датами и низ
#      последней строки — заменила тонкие 1px-линии стыков Task 255;
#   3) праздники — розовый фон как прежде + ТА ЖЕ заливка на их
#      ячейках дат в шапке (.ws-feast background #f8e2e9).
# Каждая замена — ровно один раз (assert).
import io

path = 'index.html'
src = io.open(path, encoding='utf-8').read()
orig = src

def rep(old, new, tag):
    global src
    n = src.count(old)
    assert n == 1, 'FAIL %s: найдено %d вхождений' % (tag, n)
    src = src.replace(old, new)
    print('OK %s' % tag)

# ---- 0. комментарий .ws-dot-code (упоминание розовых выходных) ----
rep(u'''       Inline-цвет из листа
       «Коды_статусов» для «.» НЕ применяется (_renderCell не ставит
       background) — совпадение с пустой ячейкой в ЛЮБОЙ теме;
       выходной день — розовый, как пустая ячейка выходного
       (.ws-weekend.ws-status-empty выше по специфичности). Класс —''',
    u'''       Inline-цвет из листа
       «Коды_статусов» для «.» НЕ применяется (_renderCell не ставит
       background) — совпадение с пустой ячейкой в ЛЮБОЙ теме;
       праздник — розовый, как пустая ячейка праздника
       (.ws-feast.ws-status-empty выше по специфичности, Task 363);
       обычный выходной — как пустая ячейка + красная рамка-группа.
       Класс —''',
    '0: комментарий ws-dot-code')

# ---- 1. базовое правило: выходные -> праздники, #6e4250 -> #f8e2e9 ----
rep(u'''    /* Task 254: пустые ячейки выходных дней (Сб/Вс) — слабый
       пастельно-розовый фон. Только ПУСТЫЕ ячейки: статусные (Д/Н/Б…)
       сохраняют цвет справочника кодов. Фон сплошной (инвариант
       Task 250 — страница не просвечивает). */
    .ws-grid tbody td.ws-cell.ws-weekend.ws-status-empty {
        background: #6e4250;   /* тёмная тема: приглушённый пыльно-розовый */
    }''',
    u'''    /* Task 363 (заявка: «нерабочие праздничные дни оставь светлым
       розовым фоном»): розовый — теперь ТОЛЬКО праздники (нерабочие
       дни ст. 112 по производственному календарю, класс ws-feast);
       у обычных выходных (Сб/Вс + переносы) фон ПУСТОЙ ячейки —
       выходные выделяет красная рамка-группа (ws-wgrp*, правила
       ниже). Цвет — прежний пастельный Task 355 #f8e2e9, обе темы
       (тёмная несёт светлые цвета Task 319 под фильтром brightness;
       тёмный override больше не нужен). Только ПУСТЫЕ ячейки:
       статусные (Д/Н/Б/д/н…) сохраняют цвет справочника кодов.
       Фон сплошной (инвариант Task 250 — страница не просвечивает). */
    .ws-grid tbody td.ws-cell.ws-feast.ws-status-empty {
        background: #f8e2e9;   /* нерабочий праздничный день — светлый розовый */
    }''',
    '1: базовое правило выходных -> праздники')

# ---- 2. комментарий Task 319 (перечень цветов) ----
rep(u'''       фильтром brightness: пустые #eef0f2, пустые выходные #f8e2e9
       (как в светлой; Task 355 — пастельнее и бледнее), статусные —''',
    u'''       фильтром brightness: пустые #eef0f2, праздники #f8e2e9 (Task
       363: розовый — только праздники, выходные — как пустые, группа
       выходных обведена красной рамкой), статусные —''',
    '2: комментарий Task 319 (цвета)')

# ---- 3. тёмный override выходных — удалить (база теперь #f8e2e9) ----
rep(u'''    [data-theme="dark"] .ws-grid tbody td.ws-cell.ws-weekend.ws-status-empty {
        background: #f8e2e9;   /* Task 355: пастельнее (тот же цвет, что в светлой) */
    }
    [data-theme="dark"] .ws-grid tbody td.ws-cell.ws-status-empty {''',
    u'''    [data-theme="dark"] .ws-grid tbody td.ws-cell.ws-status-empty {''',
    '3: тёмный override выходных удалён')

# ---- 4. правила Task 255 -> рамка-группа Task 363 ----
rep(u'''    /* Task 255 (правка Task 254): красные линии-границы между колонками
       выходных и рабочих дней — ТОНЬШЕ (1px вместо 2px), ПРИГЛУШЁННЕЕ
       (#cc6e73 — пыльно-красный вместо яркого #e53935) и ТОЛЬКО в теле
       таблицы (из шапки thead убраны). При 1px в border-collapse цвет
       общей грани равных по толщине границ может выбрать соседняя
       серая граница, поэтому красной делается ОБЕ стороны стыка
       (классы ставит JS в _renderCell): у пятницы border-right
       (ws-boundary-after) + у субботы border-left (ws-boundary-left),
       у воскресенья border-right (ws-boundary-right) + у понедельника
       border-left (ws-boundary-before). Специфичность селекторов
       ЗАВЫШЕНА (.ws-cell): иначе в светлой теме правило
       [data-theme="light"] .ws-grid tbody td { border-color } (0,2,2,
       ниже по файлу) перекрасит красную границу в серый. */
    .ws-grid tbody td.ws-cell.ws-boundary-left,
    .ws-grid tbody td.ws-cell.ws-boundary-before { border-left: 1px solid #cc6e73; }
    .ws-grid tbody td.ws-cell.ws-boundary-right,
    .ws-grid tbody td.ws-cell.ws-boundary-after { border-right: 1px solid #cc6e73; }''',
    u'''    /* Task 363 (заявка: «на ячейках выходных дней сделай толстые
       красные разделительные линии вокруг по краям ГРУППЫ этих ячеек
       (не каждую ячейку), включая ячейки с датами»): красная рамка
       вокруг СТОЛБЦОВ группы выходных — шапка с датами + все строки +
       низ последней строки. Заменила тонкие 1px-линии стыков Task 255:
       при разной толщине границ в border-collapse ПОБЕЖДАЕТ ШИРЕ —
       3px красная всегда перекрывает 1px соседа, красить рабочий
       день по другую сторону стыка не нужно. Классы ставит JS
       (_renderGrid на th, _renderCell на td): ws-wgrp — столбец
       группы, ws-wgrp-first / ws-wgrp-last — первый/последний
       столбец группы (праздники .ws-feast в группу НЕ входят —
       остаются розовыми). Верх группы — ВНУТРЕННЯЯ ТЕНЬ на th
       (border-top в шапке запрещён Task 355: высота 37px и совпадение
       со шторкой итогов Task 331), бока — border-left/right,
       низ — border-bottom последней строки. Специфичность селекторов
       ЗАВЫШЕНА (.ws-cell): иначе в светлой теме правило
       [data-theme="light"] .ws-grid tbody td { border-color } (0,2,2,
       ниже по файлу) перекрасит красную границу в серый. Цвет
       #e53935, толщина 3px — заметно при 1px-линиях сетки. */
    .ws-grid thead th.ws-day-col.ws-wgrp {
        box-shadow: inset 0 3px 0 0 #e53935;
    }
    .ws-grid thead th.ws-day-col.ws-wgrp-first { border-left: 3px solid #e53935; }
    .ws-grid thead th.ws-day-col.ws-wgrp-last { border-right: 3px solid #e53935; }
    .ws-grid tbody td.ws-cell.ws-wgrp-first { border-left: 3px solid #e53935; }
    .ws-grid tbody td.ws-cell.ws-wgrp-last { border-right: 3px solid #e53935; }
    .ws-grid tbody tr:last-child td.ws-cell.ws-wgrp {
        border-bottom: 3px solid #e53935;
    }''',
    '4: правила Task 255 -> рамка-группа Task 363')

# ---- 5. шапка: фон праздника (та же розовая заливка на дате) ----
rep(u'''    /* Праздник в шапке (гос./региональный праздник по производственному
       календарю) — ярче и жирнее обычного выходного (ws-holiday #ff8a8a):
       день сразу читается как «красный день», у выходных/переносов цвет
       спокойнее. Название праздника — в тултипе th (title, ставит JS). */
    .ws-grid thead th.ws-day-col.ws-feast {
        color: #ff6b6b;
        font-weight: 700;
    }''',
    u'''    /* Праздник в шапке (гос./региональный праздник по производственному
       календарю) — ярче и жирнее обычного выходного (ws-holiday #ff8a8a):
       день сразу читается как «красный день», у выходных/переносов цвет
       спокойнее. Task 363 (заявка: «только добавь такой же фон и на их
       ячейки с датами»): та же светло-розовая заливка #f8e2e9, что у
       пустых ячеек праздника в теле (шапка sticky — фон обязан
       оставаться непрозрачным). Название праздника — в окошке
       производственного календаря в тулбаре. */
    .ws-grid thead th.ws-day-col.ws-feast {
        color: #ff6b6b;
        font-weight: 700;
        background: #f8e2e9;
    }''',
    '5: шапка — фон даты праздника')

# ---- 6. комментарий светлой «.»-темы ----
rep(u'''    /* Task 314: светлая тема — «.»-ячейка = пустая (#eef0f2);
       правило выше специфичности базового, чтобы не зависеть от
       порядка с Task 250. Выходные — #f8e2e9 (правило weekend ниже
       специфичнее) */''',
    u'''    /* Task 314: светлая тема — «.»-ячейка = пустая (#eef0f2);
       правило выше специфичности базового, чтобы не зависеть от
       порядка с Task 250. Праздники — #f8e2e9 (правило feast ниже
       специфичнее, Task 363) */''',
    '6: комментарий светлой точки')

# ---- 7. светлое правило: выходные -> праздники ----
rep(u'''    /* Task 254: светлая тема — слабый пастельно-розовый фон пустых
       ячеек выходных (заметно мягче «Больничного» #F8BBD0).
       Task 355 (заявка: «пастельнее и бледнее, не такой яркий»):
       #f7d9e3 → #f8e2e9 — насыщенность ниже на треть, чуть светлее;
       тёмная тема берёт тот же цвет (Task 319, см. выше) под своим
       фильтром brightness */
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-weekend.ws-status-empty {
        background: #f8e2e9;
    }''',
    u'''    /* Task 363: светлая тема — розовый ТОЛЬКО праздники: тот же
       пастельный #f8e2e9 (Tasks 254/355), что был у выходных; стоит
       ПОСЛЕ светлой «.»-темы — перекрывает и её (базовое правило
       ws-feast выше по файлу специфичностью ниже). Обычные выходные —
       фон пустой ячейки + красная рамка-группа */
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-feast.ws-status-empty {
        background: #f8e2e9;
    }''',
    '7: светлое правило выходных -> праздники')

# ---- 8. JS: хелперы _calDayFeast/_calWend после _calDayOff ----
rep(u'''        // День нерабочий по производственному календарю (Сб/Вс +
        // праздники + перенесённые выходные, без рабочих суббот).
        _calDayOff: function(day) {
            if (typeof ProdCalendar !== 'undefined' && ProdCalendar.dayInfo) {
                return !!ProdCalendar.dayInfo(this._year, this._month, day).off;
            }
            var dw = new Date(this._year, this._month - 1, day).getDay();
            return dw === 0 || dw === 6;
        },''',
    u'''        // День нерабочий по производственному календарю (Сб/Вс +
        // праздники + перенесённые выходные, без рабочих суббот).
        _calDayOff: function(day) {
            if (typeof ProdCalendar !== 'undefined' && ProdCalendar.dayInfo) {
                return !!ProdCalendar.dayInfo(this._year, this._month, day).off;
            }
            var dw = new Date(this._year, this._month - 1, day).getDay();
            return dw === 0 || dw === 6;
        },

        // Task 363: день — ПРАЗДНИЧНЫЙ нерабочий (ст. 112, поле
        // holiday производственного календаря)? Праздники — розовый
        // фон (пустые ячейки тела + ячейка даты в шапке), в красную
        // рамку-группу выходных НЕ входят. Без календаря праздников
        // нет: все нерабочие дни — обычные выходные
        _calDayFeast: function(day) {
            if (typeof ProdCalendar !== 'undefined' && ProdCalendar.dayInfo) {
                return !!ProdCalendar.dayInfo(this._year, this._month, day).holiday;
            }
            return false;
        },

        // Task 363: день — обычный ВЫХОДНОЙ (нерабочий, НЕ праздник)?
        // Сб/Вс и перенесённые выходные за вычетом праздников:
        // столбцы таких дней обводятся красной рамкой-группой
        _calWend: function(day) {
            return !!this._calDayOff(day) && !this._calDayFeast(day);
        },''',
    '8: JS-хелперы _calDayFeast/_calWend')

# ---- 9. JS: шапка — классы рамки-группы на th ----
rep(u'''                // Task 255 (правка Task 254): красные линии-границы
                // выходных/рабочих дней из ШАПКИ убраны — линии проходят
                // только по ячейкам тела таблицы (tbody, см. _renderCell).
                // Шапке остаются классы выходных (ws-holiday) и
                // праздников (ws-feast).
                var thCls = 'ws-day-col' + (isOff ? ' ws-holiday' : '') +
                            (isFeast ? ' ws-feast' : '') +''',
    u'''                // Task 363 (заявка: «на ячейках выходных дней сделай
                // толстые красные разделительные линии вокруг по краям
                // группы этих ячеек, включая ячейки с датами»): шапка
                // ВХОДИТ в рамку-группу — th обычного выходного (не
                // праздник) получает ws-wgrp (+ ws-wgrp-first/-last на
                // первом/последнем столбце группы; те же классы на td
                // ставит _renderCell). Праздники в группу не входят —
                // розовый фон даты (см. CSS ws-feast)
                var wgrpCls = '';
                if (isOff && !isFeast) {
                    wgrpCls = ' ws-wgrp';
                    var prevWgrp = (d > 1) ? this._calWend(d - 1) : false;
                    var nextWgrp = (d < daysInMonth) ? this._calWend(d + 1) : false;
                    if (!prevWgrp) wgrpCls += ' ws-wgrp-first';
                    if (!nextWgrp) wgrpCls += ' ws-wgrp-last';
                }
                var thCls = 'ws-day-col' + (isOff ? ' ws-holiday' : '') +
                            (isFeast ? ' ws-feast' : '') + wgrpCls +''',
    '9: шапка — wgrp-классы th')

# ---- 10. JS: _renderCell — блок Task 255 -> Task 363 ----
rep(u'''            // Task 260 (развитие Tasks 254/255): выходные и праздники — по
            // производственному календарю (ProdCalendar): Сб/Вс, гос.
            // праздники, перенесённые выходные; РАБОЧИЕ субботы выходными
            // не считаются. Розовый фон пустых ячеек (.ws-weekend +
            // .ws-status-empty) и приглушённые красные 1px-линии на стыках
            // нерабочих дней с рабочими — теперь по календарю, а не только
            // по Сб/Вс. При 1px в border-collapse цвет общей грани равных
            // границ браузер может взять у соседа, поэтому красной делается
            // ОБЕ стороны стыка: последний рабочий день ws-boundary-after
            // (border-right) + первый нерабочий ws-boundary-left
            // (border-left); последний нерабочий ws-boundary-right
            // (border-right) + первый рабочий ws-boundary-before
            // (border-left). Граничные случаи: нерабочий 1-го числа (слева
            // — колонка ФИО, пары нет) и нерабочий последним днём месяца
            // (справа — край таблицы, пары нет).
            var lastDay = new Date(this._year, this._month, 0).getDate();
            var dayOff = this._calDayOff(day);
            if (dayOff) classes.push('ws-weekend');
            if (dayOff && day > 1 && !this._calDayOff(day - 1)) classes.push('ws-boundary-left');
            if (dayOff && day < lastDay && !this._calDayOff(day + 1)) classes.push('ws-boundary-right');
            if (!dayOff && day < lastDay && this._calDayOff(day + 1)) classes.push('ws-boundary-after');
            if (!dayOff && day > 1 && this._calDayOff(day - 1)) classes.push('ws-boundary-before');''',
    u'''            // Task 260 (развитие Tasks 254/255): выходные и праздники — по
            // производственному календарю (ProdCalendar): Сб/Вс, гос.
            // праздники, перенесённые выходные; РАБОЧИЕ субботы выходными
            // не считаются. Task 363 (заявка: «фон выходных дней сделай
            // таким же как в пустых ячейках… толстые красные
            // разделительные линии вокруг по краям группы этих ячеек»):
            // класс ws-weekend остаётся маркером нерабочих дней, но фон
            // обычных выходных больше НЕ розовый (розовый — только
            // праздники, ws-feast); вместо тонких 1px-линий стыков —
            // красная 3px-рамка вокруг ГРУППЫ столбцов выходных (не
            // каждую ячейку): ws-wgrp на каждом столбце группы,
            // ws-wgrp-first/-last на первом/последнем (край таблицы —
            // тоже край группы: нерабочий 1-го числа получает left,
            // последнего дня — right), низ рамки — CSS tr:last-child,
            // верх — шапка th (см. _renderGrid). Праздники в группу НЕ
            // входят. Обе стороны стыка красить больше не нужно: при
            // разной толщине границ в border-collapse побеждает ШИРЕ
            // (3px перекрывает 1px соседа). Гварды typeof — старые
            // VM-хосты без новых хелперов не падают (праздников нет)
            var lastDay = new Date(this._year, this._month, 0).getDate();
            var dayOff = this._calDayOff(day);
            if (dayOff) classes.push('ws-weekend');
            var dayFeast = (typeof this._calDayFeast === 'function')
                ? !!this._calDayFeast(day) : false;
            if (dayFeast) classes.push('ws-feast');
            if (dayOff && !dayFeast) {
                classes.push('ws-wgrp');
                var prevWend = (day > 1 && typeof this._calWend === 'function')
                    ? this._calWend(day - 1) : false;
                var nextWend = (day < lastDay && typeof this._calWend === 'function')
                    ? this._calWend(day + 1) : false;
                if (!prevWend) classes.push('ws-wgrp-first');
                if (!nextWend) classes.push('ws-wgrp-last');
            }''',
    '10: _renderCell — блок групп/праздников')

assert src != orig, 'изменений нет'
io.open(path, 'w', encoding='utf-8').write(src)
print('index.html: 11 правок Task 363 применены')
