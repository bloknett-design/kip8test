#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 435 + 436 (заявка пользователя):
#
# Task 435 — «В картах работников, при переключении года в блоке
# инструктажей, автоматически переключается год в блоке мероприятий,
# и наоборот то же самое. Эти блоки не должны влиять друг на друга»:
# годы блоков «Мероприятия» (fam 0, хранилище _wtabYear) и «Повторные
# инструктажи и периодическая проверка знаний» (fam 1, хранилище
# _wtabYearInstr) — РАЗДЕЛЬНЫЕ: стрелки ‹год› каждого блока меняют
# только свой год, записи каждого блока — своя выборка года, нижняя
# граница навигации — по записям СВОЕГО раздела. Сигнатуры клика
# блока мероприятий НЕ менялись (без третьего аргумента) — попапы и
# прежние тесты совместимы.
#
# Task 436 — «В разделе расходомеров хозрасчётных, в полных карточках
# расходомеров, график должен строится по логике - все значения
# относительно между собой до 100%, но если есть значения, которые
# больше в два раза и выше чем среднее значение остальных, то все
# меньше него значения отображаются относительно до 80% ... а большие
# значения отображаются от 80 до 100%»: _buildArchiveChart — шкала
# ДВУХ ГРУПП: значение «большое», если ≥ 2 × среднего ОСТАЛЬНЫХ
# показанных (среднее остальных > 0); малые — полоса 0–80% (пол 5%,
# Task 226), большие — 80–100%; равные/единственные в группе —
# середина своей полосы (40% / 90%); без «больших» — прежняя
# нормализация 0–100% (Task 224/226) без изменений.
#
# Сервер WorkSchedule.gs НЕ тронут (srvVer 427). Запуск из корня kip8test.
import io, sys

PATH = 'index.html'
s = io.open(PATH, encoding='utf-8').read()
orig = s
edits = []

def edit(name, old, new, count=1):
    global s
    found = s.count(old)
    assert found == count, '%s: найдено %d вхождений (ожидалось %d)' % (name, found, count)
    s = s.replace(old, new, count)
    edits.append(name)

# ============================================================
# Task 435 — РАЗДЕЛЬНЫЕ ГОДЫ БЛОКОВ КАРТОЧКИ
# ============================================================

# E1: _renderWorkerCard — два года + две выборки записей
edit('E1 wYearEv/wYearIn',
"""            var wYear = asBlocks ? this._wtabYearOf(tabNo) : this._year;
            var wRecs = this._wtabYearRecords(tabNo, wYear);
            var evs = wRecs.evs, ins = wRecs.ins;""",
"""            // Task 435 (заявка: «эти блоки не должны влиять друг
            // на друга»): годы блоков «Мероприятия» и «Повторные
            // инструктажи…» — РАЗДЕЛЬНЫЕ (fam 0 → хранилище
            // _wtabYear, fam 1 → _wtabYearInstr): стрелки ‹год›
            // каждого блока меняют ТОЛЬКО свой год, записи — своя
            // выборка года; попап ячейки (не asBlocks) — год
            // шахматки, как прежде
            var wYearEv = asBlocks ? this._wtabYearOf(tabNo, 0) : this._year;
            var wYearIn = asBlocks ? this._wtabYearOf(tabNo, 1) : this._year;
            var wRecsEv = this._wtabYearRecords(tabNo, wYearEv);
            var wRecsIn = this._wtabYearRecords(tabNo, wYearIn);
            var evs = wRecsEv.evs, ins = wRecsIn.ins;""")

# E2: шапка блока «Мероприятия» — fam 0
edit('E2 шапка b3 fam 0',
"""                ? '<div class="ws-whead"><div class="ws-whead-t">Мероприятия · ' +
                  wYear + this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +""",
"""                ? '<div class="ws-whead"><div class="ws-whead-t">Мероприятия · ' +
                  wYearEv + this._wtabYearNav(tabNo, wYearEv, 0) + '</div><div class="ws-whead-a">' +""")

# E3: шапка блока «Повторные инструктажи…» — fam 1
edit('E3 шапка b5 fam 1',
"""                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-wrap">Повторные инструктажи и периодическая проверка знаний · ' +
                  wYear + this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +""",
"""                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-wrap">Повторные инструктажи и периодическая проверка знаний · ' +
                  wYearIn + this._wtabYearNav(tabNo, wYearIn, 1) + '</div><div class="ws-whead-a">' +""")

# E4: _renderInstrSection — год инструктажного блока
edit('E4 renderInstrSection wYearIn',
"""                b5 += this._renderInstrSection(ins, tabNo, withEdit,
                                                asBlocks, this._INSTR_LIST, wYear);""",
"""                b5 += this._renderInstrSection(ins, tabNo, withEdit,
                                                asBlocks, this._INSTR_LIST, wYearIn);""")

# E5: _wtabYearOf — fam-хранилище
edit('E5 _wtabYearOf fam',
"""        _wtabYearOf: function(tabNo) {
            var y = this._wtabYear && this._wtabYear[String(tabNo)];
            y = parseInt(y, 10);
            if (y && y >= 1900 && y <= 2999) return y;
            return this._year || new Date().getFullYear();
        },""",
"""        // Task 435: fam 1 — год блока «Повторные инструктажи…»
        // (хранилище _wtabYearInstr), fam 0/не задан — год блока
        // «Мероприятия» (хранилище _wtabYear, прежнее поведение)
        _wtabYearOf: function(tabNo, fam) {
            var store = (fam === 1) ? this._wtabYearInstr : this._wtabYear;
            var y = store && store[String(tabNo)];
            y = parseInt(y, 10);
            if (y && y >= 1900 && y <= 2999) return y;
            return this._year || new Date().getFullYear();
        },""")

# E6: _wtabYearMin — fam-фильтр записей по разделу
edit('E6 _wtabYearMin fam',
"""        // нижняя граница навигации — самый ранний год записи
        // работника (instrAll/eventsAll/срез года табеля); записей
        // нет — год шахматки
        _wtabYearMin: function(tabNo) {
            tabNo = String(tabNo);
            var min = null;
            var pools = [this._INSTR_ALL, this._EVENTS_ALL, this._TRAININGS];
            for (var p = 0; p < pools.length; p++) {
                var arr = pools[p] || [];
                for (var i = 0; i < arr.length; i++) {
                    if (String(arr[i]['таб_номер']) !== tabNo) continue;
                    var s = String(arr[i].дата_начала || '');""",
"""        // нижняя граница навигации — самый ранний год записи
        // работника (instrAll/eventsAll/срез года табеля); записей
        // нет — год шахматки. Task 435: fam 1 — граница ТОЛЬКО по
        // записям инструктажей, fam 0 — только по мероприятиям
        // (стрелки блока не зависят от записей чужого раздела);
        // fam не задан — по всем записям (попап, прежнее поведение)
        _wtabYearMin: function(tabNo, fam) {
            tabNo = String(tabNo);
            var famFilter = (fam === 0 || fam === 1);
            var wantInstr = (fam === 1);
            var min = null;
            var pools = [this._INSTR_ALL, this._EVENTS_ALL, this._TRAININGS];
            for (var p = 0; p < pools.length; p++) {
                var arr = pools[p] || [];
                for (var i = 0; i < arr.length; i++) {
                    if (String(arr[i]['таб_номер']) !== tabNo) continue;
                    if (famFilter &&
                        (this._isInstrType(arr[i].тип) !== wantInstr)) continue;
                    var s = String(arr[i].дата_начала || '');""")

# E7: _wtabYearShift — fam-хранилище
edit('E7 _wtabYearShift fam',
"""        _wtabYearShift: function(tabNo, delta) {
            tabNo = String(tabNo);
            var now = new Date().getFullYear();
            var y = this._wtabYearOf(tabNo) + (delta || 0);
            var min = this._wtabYearMin(tabNo);
            var max = Math.max(now, this._year || now);
            if (y < min) y = min;
            if (y > max) y = max;
            if (!this._wtabYear) this._wtabYear = {};
            if (y === (this._year || now)) delete this._wtabYear[tabNo];
            else this._wtabYear[tabNo] = y;
            this._renderWorkersPage();
        },""",
"""        // Task 435: fam 1 — меняется год ТОЛЬКО блока инструктажей
        // (хранилище _wtabYearInstr), fam 0/не задан — только
        // блока мероприятий (_wtabYear): второй блок сохраняет
        // свой год
        _wtabYearShift: function(tabNo, delta, fam) {
            tabNo = String(tabNo);
            var now = new Date().getFullYear();
            var y = this._wtabYearOf(tabNo, fam) + (delta || 0);
            var min = this._wtabYearMin(tabNo, fam);
            var max = Math.max(now, this._year || now);
            if (y < min) y = min;
            if (y > max) y = max;
            var store = (fam === 1) ? '_wtabYearInstr' : '_wtabYear';
            if (!this[store]) this[store] = {};
            if (y === (this._year || now)) delete this[store][tabNo];
            else this[store][tabNo] = y;
            this._renderWorkersPage();
        },""")

# E8: _wtabYearNav — fam-минимум + третий аргумент клика fam 1
edit('E8 _wtabYearNav fam',
"""        _wtabYearNav: function(tabNo, year) {
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
        },""",
"""        // Task 435: fam 1 — навигатор блока инструктажей (клик
        // передаёт третий аргумент 1), fam 0/не задан — блока
        // мероприятий (прежняя сигнатура клика, без третьего
        // аргумента); минимум — по записям СВОЕГО раздела
        _wtabYearNav: function(tabNo, year, fam) {
            var min = this._wtabYearMin(tabNo, fam);
            var now = new Date().getFullYear();
            var max = Math.max(now, this._year || now);
            var famArg = (fam === 1) ? ', 1' : '';
            var left = (year > min)
                ? '<span class="ws-ynav-btn" role="button" title="Предыдущий год"' +
                  ' onclick="event.stopPropagation(); WorkSchedule._wtabYearShift(\\'' +
                  this._esc(String(tabNo)) + '\\', -1' + famArg + ')">‹</span>'
                : '<span class="ws-ynav-btn ws-ynav-off">‹</span>';
            var right = (year < max)
                ? '<span class="ws-ynav-btn" role="button" title="Следующий год"' +
                  ' onclick="event.stopPropagation(); WorkSchedule._wtabYearShift(\\'' +
                  this._esc(String(tabNo)) + '\\', 1' + famArg + ')">›</span>'
                : '<span class="ws-ynav-btn ws-ynav-off">›</span>';
            return '<span class="ws-ynav">' + left + right + '</span>';
        },""")

# E9: состояние — второе хранилище
edit('E9 состояние _wtabYearInstr',
"""        // Task 408: выбранный ГОД блоков карточки по работникам
        // (стрелки ‹год›; не выбран — год шахматки)
        _wtabYear: {},""",
"""        // Task 408: выбранный ГОД блоков карточки по работникам
        // (стрелки ‹год›; не выбран — год шахматки). Task 435: годы
        // блоков РАЗДЕЛЬНЫЕ — «Мероприятия» (_wtabYear, fam 0) и
        // «Повторные инструктажи…» (_wtabYearInstr, fam 1) не
        // влияют друг на друга
        _wtabYear: {},
        _wtabYearInstr: {},""")

# ============================================================
# Task 436 — ГРАФИК РАСХОДОМЕРА: ШКАЛА ДВУХ ГРУПП
# ============================================================

# E10: расчёт групп после среза 31 записи
edit('E10 группы twoScale',
"""            // Записи от старых к новым (по X слева направо)
            var chartRecords = records.slice(0, 31).reverse();""",
"""            // Записи от старых к новым (по X слева направо)
            var chartRecords = records.slice(0, 31).reverse();

            // Task 436 (заявка: «все значения относительно между
            // собой до 100%, но если есть значения, которые больше
            // в два раза и выше чем среднее значение остальных…»):
            // шкала ДВУХ ГРУПП для сильно различающихся значений.
            // Значение показанной записи — «большое», если оно
            // ≥ 2 × среднего ОСТАЛЬНЫХ показанных значений (среднее
            // остальных > 0 — при нулевых остальных «вдвое больше
            // нуля» не считается). Есть большие → малые
            // масштабируются «относительно друг друга» в полосе
            // 0–80% высоты графика, большие — в полосе 80–100%
            // (равные/единственные в группе — середина своей
            // полосы): резко выделяющееся значение не снижает все
            // остальные к нулю. Границы групп — по ПОКАЗАННЫМ
            // записям (последние 31 суточных): значения вне окна
            // графика на него не влияют. Больших нет — прежняя
            // нормализация 0–100% (Task 224/226) без изменений
            var vals = [];
            for (var cv = 0; cv < chartRecords.length; cv++) {
                vals.push(pickValue(chartRecords[cv]));
            }
            var vSum = 0;
            for (var sv = 0; sv < vals.length; sv++) vSum += vals[sv];
            var isBig = [], bigCount = 0;
            for (var bv = 0; bv < vals.length; bv++) {
                var avgOthers = (vals.length > 1)
                    ? ((vSum - vals[bv]) / (vals.length - 1)) : 0;
                var big = (avgOthers > 0 && vals[bv] >= 2 * avgOthers);
                isBig.push(big);
                if (big) bigCount++;
            }
            var twoScale = (bigCount > 0 && bigCount < vals.length);
            var minS = Infinity, maxS = -Infinity;
            var minB = Infinity, maxB = -Infinity;
            if (twoScale) {
                for (var gv = 0; gv < vals.length; gv++) {
                    if (isBig[gv]) {
                        if (vals[gv] < minB) minB = vals[gv];
                        if (vals[gv] > maxB) maxB = vals[gv];
                    } else {
                        if (vals[gv] < minS) minS = vals[gv];
                        if (vals[gv] > maxS) maxS = vals[gv];
                    }
                }
            }""")

# E11: высота бара — своя полоса для своей группы
edit('E11 barPct twoScale',
"""                // Task 224: нормализация по диапазону (val − min) / (max − min) × 100.
                // Task 226: минимальная высота бара 5%.
                var barPct;
                if (flat) {
                    barPct = 60; // все значения одинаковы — плоская линия
                } else {
                    barPct = Math.max(5, ((val - minVal) / range) * 100);
                }""",
"""                // Task 224: нормализация по диапазону (val − min) / (max − min) × 100.
                // Task 226: минимальная высота бара 5%.
                // Task 436: есть «большие» (≥ 2 × среднего
                // остальных) — высота по СВОЕЙ группе: малые — в
                // полосе 0–80% (пол 5% — Task 226), большие — в
                // полосе 80–100% (равные/единственные — середина
                // полосы: 40% у малых, 90% у больших)
                var barPct;
                if (twoScale && isBig[j]) {
                    barPct = (minB === maxB)
                        ? 90
                        : (80 + ((val - minB) / (maxB - minB)) * 20);
                } else if (twoScale) {
                    barPct = (minS === maxS)
                        ? 40
                        : Math.max(5, ((val - minS) / (maxS - minS)) * 80);
                } else if (flat) {
                    barPct = 60; // все значения одинаковы — плоская линия
                } else {
                    barPct = Math.max(5, ((val - minVal) / range) * 100);
                }""")

io.open(PATH, 'w', encoding='utf-8').write(s)
print('index.html: применено правок %d' % len(edits))
for name in edits:
    print('  OK %s' % name)
print('изменение размера: %+d байт' % (len(s) - len(orig)))
