#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408 — ЧАСТЬ 3 (уточнения после прогона):
#  1) заголовки блоков: год ОБЫЧНЫМ текстом (обратная совместимость
#     ассертов «Мероприятия · 2026»), навигатор — СТРЕЛКИ после года
#     («Мероприятия · 2026 ‹ ›»);
#  2) _wtabYearNav: только ‹ › (без года внутри);
#  3) _wtabYearRecords: _TRAININGS в пуле ВСЕГДА (дедуп по id
#     разруливает; убрана зависимость от this._year — VM-хосты без
#     _year получают записи года).
import io

def apply(path, edits):
    src = io.open(path, encoding='utf-8').read()
    for old, new in edits:
        if src.count(old) != 1:
            raise SystemExit('FAIL %s: фрагмент встречается %d раз:\n%r'
                             % (path, src.count(old), old[:120]))
        src = src.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('%s: %d правок' % (path, len(edits)))

IDX = 'index.html'
apply(IDX, [
    # b3: год текстом + навигатор после
    (
"""            var b3 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Мероприятия · ' +
                  this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +
""",
"""            var b3 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Мероприятия · ' +
                  wYear + this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +
"""),
    # b5: год текстом + навигатор после
    (
"""            var b5 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-wrap">Повторные инструктажи и периодическая проверка знаний · ' +
                  this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +
""",
"""            var b5 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-wrap">Повторные инструктажи и периодическая проверка знаний · ' +
                  wYear + this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +
"""),
    # _wtabYearNav: только стрелки (год уже в заголовке текстом)
    (
"""        // навигатор «‹ 2026 ›» для заголовка блока карточки (только
        // asBlocks — страница «Работники»); на границах —
        // приглушённые стрелки без клика
        _wtabYearNav: function(tabNo, year) {
            var min = this._wtabYearMin(tabNo);
            var now = new Date().getFullYear();
            var max = Math.max(now, this._year || now);
            var left = (year > min)
                ? '<span class="ws-ynav-btn" role="button" title="Предыдущий год"' +
                  ' onclick="event.stopPropagation(); WorkSchedule._wtabYearShift(\\'' +
                  this._esc(String(tabNo)) + '\\', -1)">‹</span>'
                : '<span class="ws-ynav-btn ws-ynav-off">‹</span>';
            var right = (year < max)
                ? '<span class="ws-ynav-btn" role="button" title="Следующий год"' +
                  ' onclick="event.stopPropagation(); WorkSchedule._wtabYearShift(\\'' +
                  this._esc(String(tabNo)) + '\\', 1)">›</span>'
                : '<span class="ws-ynav-btn ws-ynav-off">›</span>';
            return '<span class="ws-ynav">' + left +
                   '<span class="ws-ynav-y">' + year + '</span>' +
                   right + '</span>';
        },
""",
"""        // навигатор «‹ ›» для заголовка блока карточки (год стоит
        // перед ним текстом; только asBlocks — страница «Работники»);
        // на границах — приглушённые стрелки без клика
        _wtabYearNav: function(tabNo, year) {
            var min = this._wtabYearMin(tabNo);
            var now = new Date().getFullYear();
            var max = Math.max(now, this._year || now);
            var left = (year > min)
                ? '<span class="ws-ynav-btn" role="button" title="Предыдущий год"' +
                  ' onclick="event.stopPropagation(); WorkSchedule._wtabYearShift(\\'' +
                  this._esc(String(tabNo)) + '\\', -1)">‹</span>'
                : '<span class="ws-ynav-btn ws-ynav-off">‹</span>';
            var right = (year < max)
                ? '<span class="ws-ynav-btn" role="button" title="Следующий год"' +
                  ' onclick="event.stopPropagation(); WorkSchedule._wtabYearShift(\\'' +
                  this._esc(String(tabNo)) + '\\', 1)">›</span>'
                : '<span class="ws-ynav-btn ws-ynav-off">›</span>';
            return '<span class="ws-ynav">' + left + right + '</span>';
        },
"""),
    # _wtabYearRecords: _TRAININGS в пуле всегда (дедуп разрулит)
    (
"""        // записи работника за выбранный год блока — единый пул:
        // instrAll (все «Инструктажи») + eventsAll (все «Мероприятия»)
        // + годовой срез _TRAININGS (старый сервер/кэш без eventsAll);
        // дедуп по id (без id — дата+тема); возврат { ins, evs }
        // выбранного года (пересечение с годом)
        _wtabYearRecords: function(tabNo, year) {
            tabNo = String(tabNo);
            var yS = year + '-01-01', yE = year + '-12-31';
            var pool = [].concat(this._INSTR_ALL || [],
                                 this._EVENTS_ALL || [],
                                 (year === this._year)
                                     ? (this._TRAININGS || []) : []);
""",
"""        // записи работника за выбранный год блока — единый пул:
        // instrAll (все «Инструктажи») + eventsAll (все «Мероприятия»)
        // + годовой срез _TRAININGS (старый сервер/кэш без eventsAll;
        // для архивных лет срез года табеля отфильтруется датами, а
        // дубли снимет дедуп по id); возврат { ins, evs } выбранного
        // года (пересечение с годом)
        _wtabYearRecords: function(tabNo, year) {
            tabNo = String(tabNo);
            var yS = year + '-01-01', yE = year + '-12-31';
            var pool = [].concat(this._INSTR_ALL || [],
                                 this._EVENTS_ALL || [],
                                 this._TRAININGS || []);
"""),
])

print('ЧАСТЬ 3 применена')
