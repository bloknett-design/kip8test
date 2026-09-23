#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 399 (kip8test): заявка «Установи ещё одно условие, если у
# пользователя нет доступа к просмотру информации мастеров в
# табеле учёта, то и в окне мероприятий не должно быть информации
# мастеров (мероприятия, отпуска, СИЗ)».
#
# КОНТЕКСТ:
#   · «Нет доступа к просмотру информации мастеров» = уровень
#     «min» (право workschedule.view.min, ограниченный просмотр
#     табеля): с Task 340 в шахматке у этого уровня скрыты
#     работники с должностью «Мастер КИПиА» (фильтр _viewEmployees
#     по признаку _isMasterKipia — «мастер кипиа» в начале
#     должности, толерантное сравнение).
#   · НО окно мероприятий месяца (#wsEventsPanel, Task 315→394)
#     показывало записи ВСЕХ работников — включая мастеров:
#     мероприятия/отпуска/СИЗ мастеров ПРОТЕКАЛИ уровню min,
#     который в сетке их не видит.
#
# ФИКС: _renderMonthEventsPanel — единственная точка рендера окна
# (десктоп-окно тулбара, мобайл-чип «Мероприятия», режим
# выбранного дня — один и тот же innerHTML). У уровня «min» записи
# мастеров исключаются из ВСЕХ трёх секций (мероприятия/отпуска/
# СИЗ) тем же признаком _isMasterKipia, что и фильтр сетки:
#   · индекс таб. номеров мастеров — по ПОЛНОМУ списку _EMPLOYEES
#     (мастера есть в данных: фильтр сетки — про отображение
#     строк, не про данные) и строится ДО первого цикла записей
#     (мероприятия фильтруются раньше, чем индекс понадобился бы);
#   · записи с таб. номером БЕЗ сотрудника в справочнике мастером
#     не считаются — показываются (как и прежде);
#   · счётчики секций и пустые состояния пересчитываются сами
#     (list.length / vacList.length / ppeList.length после фильтра);
#   · рендер симметричен смене уровня: _onRoleUpdate →
#     _applyView({rerender:true}) → _renderGrid → окно.
# Только index.html (серверных шагов НЕТ: права — из уже
# работающей матрицы, данные те же).

REPLS = [

# ---------- 1. Индекс мастеров — ДО цикла мероприятий ----------
(
"""            // Мероприятия, пересекающие открытый месяц
            var list = [];
            var trs = this._TRAININGS || [];
""",
"""            // Task 399 (заявка): уровню «min» (ограниченный просмотр,
            // workschedule.view.min) работники «Мастер КИПиА» в
            // шахматке СКРЫТЫ (_viewEmployees, Task 340) — «нет
            // доступа к информации мастеров» значит и в ОКНЕ
            // МЕРОПРИЯТИЙ их записей НЕ должно быть: мероприятия/
            // отпуска/СИЗ мастеров исключаются из ВСЕХ трёх секций
            // тем же признаком _isMasterKipia, что и фильтр сетки.
            // Индекс таб. номеров — по ПОЛНОМУ списку _EMPLOYEES
            // (мастера есть в данных: фильтр сетки — про отображение
            // строк, не про данные; здесь emps общий и с fioIdx ниже);
            // записи с таб. номером БЕЗ сотрудника в справочнике
            // мастером не считаются — показываются (как прежде).
            // Уровни edit/view видят мастеров в сетке — окно полное;
            // null — раздел целиком недоступен, окно не рендерится.
            // Блок — ДО первого цикла записей: фильтр мероприятий
            // читает индекс сразу
            var hideMasters = (this._viewLevel === 'min');
            var emps = this._EMPLOYEES || [];
            var masterTabs = {};
            if (hideMasters) {
                for (var mI = 0; mI < emps.length; mI++) {
                    if (this._isMasterKipia(emps[mI])) {
                        masterTabs[emps[mI]['таб_номер']] = true;
                    }
                }
            }
            // Мероприятия, пересекающие открытый месяц
            var list = [];
            var trs = this._TRAININGS || [];
"""
),

# ---------- 2. fioIdx — emps уже объявлен выше ----------
(
"""            // ФИО по таб. номеру
            var fioIdx = {};
            var emps = this._EMPLOYEES || [];
            for (var ei = 0; ei < emps.length; ei++) {
                fioIdx[emps[ei]['таб_номер']] = emps[ei]['ФИО'];
            }
""",
"""            // ФИО по таб. номеру (emps — объявлен выше, у индекса
            // мастеров Task 399)
            var fioIdx = {};
            for (var ei = 0; ei < emps.length; ei++) {
                fioIdx[emps[ei]['таб_номер']] = emps[ei]['ФИО'];
            }
"""
),

# ---------- 3. Секция «Мероприятия» — фильтр мастеров ----------
(
"""            for (var i = 0; i < trs.length; i++) {
                var t = trs[i];
                var s = t['дата_начала'];
""",
"""            for (var i = 0; i < trs.length; i++) {
                var t = trs[i];
                // Task 399: min — мероприятия мастеров не показываются
                if (hideMasters && masterTabs[t['таб_номер']]) continue;
                var s = t['дата_начала'];
"""
),

# ---------- 4. Секция «Отпуска» — фильтр мастеров ----------
(
"""            var vacList = [];
            var vacsAll = this._VACATIONS || [];
            for (var vI = 0; vI < vacsAll.length; vI++) {
                var vRec = vacsAll[vI];
                var vS = vRec['дата_начала'];
""",
"""            var vacList = [];
            var vacsAll = this._VACATIONS || [];
            for (var vI = 0; vI < vacsAll.length; vI++) {
                var vRec = vacsAll[vI];
                // Task 399: min — отпуска мастеров не показываются
                if (hideMasters && masterTabs[vRec['таб_номер']]) continue;
                var vS = vRec['дата_начала'];
"""
),

# ---------- 5. Секция «СИЗ» — фильтр мастеров ----------
(
"""            var ppeList = [];
            var ppeAll = this._PPE || [];
            for (var pzI = 0; pzI < ppeAll.length; pzI++) {
                var pRec = ppeAll[pzI];
                var pExpIso = String(pRec['дата_окончания'] || '').trim();
""",
"""            var ppeList = [];
            var ppeAll = this._PPE || [];
            for (var pzI = 0; pzI < ppeAll.length; pzI++) {
                var pRec = ppeAll[pzI];
                // Task 399: min — СИЗ мастеров не показываются
                if (hideMasters && masterTabs[pRec['таб_номер']]) continue;
                var pExpIso = String(pRec['дата_окончания'] || '').trim();
"""
),
]

if __name__ == '__main__':
    path = 'index.html'
    s = open(path, encoding='utf-8').read()
    for i, (old, new) in enumerate(REPLS, 1):
        n = s.count(old)
        assert n == 1, 'REPL %d: найдено %d вхождений (ожидалось 1)' % (i, n)
        s = s.replace(old, new)
        print('REPL %2d: OK (%d симв.)' % (i, len(new)))
    open(path, 'w', encoding='utf-8').write(s)
    print('task399-patch: применено %d правок к index.html' % len(REPLS))
