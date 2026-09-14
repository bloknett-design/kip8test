#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 368: расходомеры — заявка пользователя:
#   «В хозрасчётах №3 и №11, в форме ввода показаний должен выбираться
#    период из двух дат определяющих период, и значения по умолчанию
#    в форме должны стоять даты за предыдущую календарную неделю.
#    Также с хозрасчётом №9, только период месяц. Еженедельные: красный,
#    когда календарная неделя (пн–вс) прошла; зелёный — когда данные
#    этой недели введены; снова красный, когда текущая (новая) календарная
#    неделя (пн–вс) прошла, пока не введут за неё данные. Ежемесячные:
#    красный, когда календарный месяц данных прошёл; зелёный — когда
#    данные за этот месяц введены; снова красный, когда (новый) текущий
#    календарный месяц прошел, пока не введут данные за его период.»
#
# Правки index.html (СЕРВЕР не меняется — обычный маршрут
# flowmeter.updateReading уже пишет datePrev/dateCurr в meters-строку
# D/E и архив):
#   1) flowPrevWeekRange(now) — границы ПРОШЕДШЕЙ календарной недели;
#   2) _isOverdue: недельные/месячные — зелёный, пока период последних
#      данных [datePrev…dateCurr] накрывает последнюю ЗАКРЫТУЮ неделю
#      (пн–вс) / месяц; красный — закрытый период без данных (хелпер
#      _recordCoversPeriod, пересечения достаточно);
#   3) _isWeeklyMeter/_isMonthlyMeter — классификация по периоду из
#      таблицы (№1 исключён — у него своя форма с chips);
#   4) _applyEntryTypeFields: для №3/№11/№9 — два поля дат «Период
#      с … по …», дефолт = прошедшая неделя (пн–вс) / прошлый месяц;
#      правка — предзаполнение датами записи;
#   5) submitInput: datePrev = «Период с», dateCurr = «по»
#      (пустые → дефолт формы; конец раньше начала — hard-отказ);
#   6) карточка списка + детальная: подпись «за ДД.ММ–ДД.ММ.ГГГГ»;
#   7) хронология: записи недельных/месячных — диапазон дат
#      (без бейджа «нед/мес» — это показания, не агрегат №1).
import io

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
orig = src

def rep(old, new, label, count=1):
    global src
    n = src.count(old)
    assert n == count, '%s: якорь найден %d раз (ожидалось %d)' % (label, n, count)
    src = src.replace(old, new)
    print('  OK %s' % label)

# ----------------------------------------------------------------
# 1. flowPrevWeekRange — после flowPrevMonthRange
# ----------------------------------------------------------------
rep(
"""    function flowPrevMonthRange(now) {
        var n = (now instanceof Date) ? now : new Date();
        var start = new Date(n.getFullYear(), n.getMonth() - 1, 1);
        var end = new Date(n.getFullYear(), n.getMonth(), 0);
        return { start: start, end: end };
    }
""",
"""    function flowPrevMonthRange(now) {
        var n = (now instanceof Date) ? now : new Date();
        var start = new Date(n.getFullYear(), n.getMonth() - 1, 1);
        var end = new Date(n.getFullYear(), n.getMonth(), 0);
        return { start: start, end: end };
    }

    /** Task 368: границы ПРОШЕДШЕЙ календарной недели (пн–вс) от now.
     *  Возвращает {start, end}: start = понедельник прошлой недели,
     *  end = воскресенье прошлой недели. Пример: now=чт 10.09.2026 →
     *  start=пн 31.08.2026, end=вс 06.09.2026. Ровно в понедельник
     *  «прошлая неделя» — только что закрывшаяся (вс накануне);
     *  годовые переходы корректны (Date(y, m, d-7) через декабрь). */
    function flowPrevWeekRange(now) {
        var n = (now instanceof Date) ? now : new Date();
        var mon = new Date(n.getFullYear(), n.getMonth(), n.getDate());
        mon.setDate(mon.getDate() - (mon.getDay() + 6) % 7);  // пн текущей недели
        return {
            start: new Date(mon.getFullYear(), mon.getMonth(), mon.getDate() - 7),
            end: new Date(mon.getFullYear(), mon.getMonth(), mon.getDate() - 1)
        };
    }
""",
'E1: flowPrevWeekRange')

# ----------------------------------------------------------------
# 2. Комментарий-документация _isOverdue — семантика Task 368
# ----------------------------------------------------------------
rep(
"""        //   Еженедельно — календарная неделя (пн–вс) последних
        //                 данных уже прошла; зелёный — та же неделя.
        //   Ежемесячно  — календарный месяц последних данных уже
        //                 прошёл; зелёный — тот же месяц.
""",
"""        //   Task 368 (заявка): показания недельных/месячных вводятся
        //   за ПЕРИОД двух дат; зелёный — пока период последних данных
        //   [datePrev…dateCurr] накрывает последнюю ЗАКРЫТУЮ
        //   календарную неделю (пн–вс) / месяц; красный — когда
        //   закрытая неделя/месяц осталась без данных («пора вводить»),
        //   и снова красный с закрытием следующей — пока не введут
        //   данные за её/его период. Форма ввода по умолчанию
        //   предлагает границы именно закрытой недели/месяца.
""",
'E2: комментарий _isOverdue')

# ----------------------------------------------------------------
# 3. _isOverdue — недельная ветка
# ----------------------------------------------------------------
rep(
"""            if (/недел|еженед/.test(period)) {
                // Еженедельно: календарная неделя данных прошла (неделя пн–вс)
                return this._mondayOf(d) < this._mondayOf(n);
            }
""",
"""            if (/недел|еженед/.test(period)) {
                // Task 368: зелёный — период данных накрывает последнюю
                // ЗАКРЫТУЮ календарную неделю (пн–вс); красный — закрытая
                // неделя без данных, и снова красный с закрытием следующей
                return !this._recordCoversPeriod(m, d,
                    new Date(wMon.getFullYear(), wMon.getMonth(), wMon.getDate() - 7),
                    new Date(wMon.getFullYear(), wMon.getMonth(), wMon.getDate() - 1));
            }
""",
'E3: недельная ветка')

# 3b. определение wMon ДО ветки (после period-регэкспов)
rep(
"""            var period = String(m.period || '').toLowerCase();
            if (/недел|еженед/.test(period)) {
""",
"""            var period = String(m.period || '').toLowerCase();
            // Task 368: понедельник текущей недели — база границ
            // последней ЗАКРЫТОЙ недели (пн–вс)
            var wMon = this._mondayOf(n);
            if (/недел|еженед/.test(period)) {
""",
'E3b: wMon')

# ----------------------------------------------------------------
# 4. _isOverdue — месячная ветка
# ----------------------------------------------------------------
rep(
"""            if (/месяц|месяч|ежемес/.test(period)) {
                // Ежемесячно: календарный месяц данных прошёл
                return (d.getFullYear() * 12 + d.getMonth()) < (n.getFullYear() * 12 + n.getMonth());
            }
""",
"""            if (/месяц|месяч|ежемес/.test(period)) {
                // Task 368: аналогично недельным, но по календарному месяцу —
                // последний ЗАКРЫТЫЙ месяц (1-е…последнее число)
                return !this._recordCoversPeriod(m, d,
                    new Date(n.getFullYear(), n.getMonth() - 1, 1),
                    new Date(n.getFullYear(), n.getMonth(), 0));
            }
""",
'E4: месячная ветка')

# ----------------------------------------------------------------
# 5. Хелперы после _mondayOf
# ----------------------------------------------------------------
rep(
"""        // Task 348: понедельник недели даты (локальная полночь)
        _mondayOf: function(d) {
            var r = new Date(d.getFullYear(), d.getMonth(), d.getDate());
            r.setDate(r.getDate() - (r.getDay() + 6) % 7);
            return r;
        },
""",
"""        // Task 348: понедельник недели даты (локальная полночь)
        _mondayOf: function(d) {
            var r = new Date(d.getFullYear(), d.getMonth(), d.getDate());
            r.setDate(r.getDate() - (r.getDay() + 6) % 7);
            return r;
        },

        // Task 368: недельный/месячный расходомер — по периоду из
        // таблицы (регэкспы веток _isOverdue, Task 367: «Еженед.»,
        // «Ежемес.», «N раз в неделю/месяц»). Хозрасчёт №1 исключён:
        // у него своя форма с chips «За сутки/За месяц» (расход, не
        // показания) и суточная логика «пора вводить».
        _isWeeklyMeter: function(m) {
            return !this._isDailyMode(m) &&
                /недел|еженед/.test(String((m && m.period) || '').toLowerCase());
        },
        _isMonthlyMeter: function(m) {
            return !this._isDailyMode(m) &&
                /месяц|месяч|ежемес/.test(String((m && m.period) || '').toLowerCase());
        },

        // Task 368: накрывает ли период последних данных [datePrev …
        // dateCurr] ЗАКРЫТЫЙ календарный период [refStart … refEnd]?
        // Пересечения достаточно: показание, снятое в середине
        // недели, — тоже «данные этой недели». d — разобранный
        // dateCurr; у legacy-записей без datePrev (или с битой датой)
        // период считается точечным [d … d].
        _recordCoversPeriod: function(m, d, refStart, refEnd) {
            var s = this._parseMdy(m.datePrev);
            if (!s || this._dayKey(s) > this._dayKey(d)) s = d;
            return this._dayKey(s) <= this._dayKey(refEnd) &&
                   this._dayKey(d) >= this._dayKey(refStart);
        },
""",
'E5: хелперы _isWeeklyMeter/_isMonthlyMeter/_recordCoversPeriod')

# ----------------------------------------------------------------
# 6. Комментарий формы HTML — Task 368
# ----------------------------------------------------------------
rep(
"""    <!-- Task 286/289: конец периода («по») — виден только для месяца;
             для «сутки» поле скрыто (дата одна, как раньше) -->""",
"""    <!-- Task 286/289: конец периода («по») — для №1 виден только в режиме
             «За месяц»; Task 368: также для недельных (№3, №11) и месячных
             (№9) расходомеров — показания вводятся за период двух дат -->""",
'E6: комментарий формы')

# ----------------------------------------------------------------
# 7. _applyEntryTypeFields — ветка периодных расходомеров
# ----------------------------------------------------------------
rep(
"""            // Суточный ввод (а также редактирование и не-№1 расходомеры):
""",
"""            // Task 368: недельные (№3, №11) и месячные (№9) расходомеры —
            // показания вводятся за ПЕРИОД из двух дат («Период с … по …»).
            // Новый ввод — по умолчанию границы ПРОШЕДШЕЙ календарной
            // недели (пн–вс) / прошлого календарного месяца; правка —
            // предзаполнение датами записи (datePrev — начало её периода).
            if (this._isWeeklyMeter(m) || this._isMonthlyMeter(m)) {
                var defR = this._isWeeklyMeter(m)
                    ? flowPrevWeekRange(now) : flowPrevMonthRange(now);
                var pvS = defR.start, pvE = defR.end;
                if (isEdit && m) {
                    var rs = this._parseMdy(m.datePrev);
                    var re = this._parseMdy(m.dateCurr);
                    if (rs) pvS = rs;
                    if (re) pvE = re;
                }
                if (dateLabel) dateLabel.textContent = 'Период с';
                if (dateEndLabel) dateEndLabel.textContent = 'по';
                if (dateEndGroup) dateEndGroup.style.display = '';
                if (dateField) dateField.value = flowDateToInputVal(pvS);
                if (dateEndField) dateEndField.value = flowDateToInputVal(pvE);
                return;
            }

            // Суточный ввод (а также редактирование и не-№1 расходомеры):
""",
'E7: _applyEntryTypeFields — периодная ветка')

# ----------------------------------------------------------------
# 8. submitInput — разбор двух дат периода
# ----------------------------------------------------------------
rep(
"""            var id = window._flowDetailId;
            var self = this;
""",
"""            // Task 368: недельные (№3, №11) и месячные (№9) — показания
            // за ПЕРИОД из двух дат: datePrev = «Период с», dateCurr =
            // «по» (пустые поля → границы прошедшей календарной недели
            // пн–вс / месяца — дефолт формы). Отправка — обычным
            // маршрутом flowmeter.updateReading: сервер пишет обе даты
            // в meters-строку (D/E) и в архив, расход = curr − prev за
            // выбранный период.
            var datePrevStr = null;
            var pmMeter = null;
            var pmId = window._flowDetailId;
            for (var pmi = 0; pmi < this._METERS.length; pmi++) {
                if (this._METERS[pmi].id === pmId) { pmMeter = this._METERS[pmi]; break; }
            }
            if (pmMeter && (this._isWeeklyMeter(pmMeter) || this._isMonthlyMeter(pmMeter))) {
                var pnow = new Date();
                var pDef = this._isWeeklyMeter(pmMeter)
                    ? flowPrevWeekRange(pnow) : flowPrevMonthRange(pnow);
                var pEndEl = document.getElementById('flowInputDateEnd');
                var psD = (dateField && dateField.value) ? _flowParseDate(dateField.value) : pDef.start;
                var peD = (pEndEl && pEndEl.value) ? _flowParseDate(pEndEl.value) : pDef.end;
                if (psD && peD && peD < psD) {
                    // Зеркало серверной DATE_INCONSISTENT и ветки №1
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Дата конца периода раньше даты начала — проверьте даты');
                    }
                    return;
                }
                datePrevStr = flowDateToMdy(psD || pDef.start);
                dateStr = flowDateToMdy(peD || pDef.end);
            }

            var id = window._flowDetailId;
            var self = this;
""",
'E8: submitInput — периодные даты')

# ----------------------------------------------------------------
# 9. submitInput — оптимистичное обновление meters-строки
# ----------------------------------------------------------------
rep(
"""                    meter.curr = num;
                    meter.dateCurr = dateStr;
""",
"""                    meter.curr = num;
                    meter.dateCurr = dateStr;
                    // Task 368: показания за период — дата начала из
                    // формы («Период с»); при правке — тоже (пользователь
                    // может поправить границы периода, prev/curr не сдвигаются)
                    if (datePrevStr) meter.datePrev = datePrevStr;
""",
'E9: submitInput — meter.datePrev')

# ----------------------------------------------------------------
# 10. renderList — подпись «за ДД.ММ–ДД.ММ.ГГГГ»
# ----------------------------------------------------------------
rep(
"""                html += '<span class="flow-summary-label">Последние показания <span class="flow-summary-date-inline">за ' + this._fmtDate(m.dateCurr) + ' г.</span></span>';
""",
"""                // Task 368: показания за период — подпись «за ДД.ММ–ДД.ММ.ГГГГ»
                // (границы datePrev–dateCurr; точечная legacy-запись — одна дата)
                var lastDateInline368 = 'за ' + this._fmtDate(m.dateCurr) + ' г.';
                if (this._isWeeklyMeter(m) || this._isMonthlyMeter(m)) {
                    var rpS = this._parseMdy(m.datePrev);
                    var rpE = this._parseMdy(m.dateCurr);
                    if (rpS && rpE && this._dayKey(rpS) < this._dayKey(rpE)) {
                        lastDateInline368 = 'за ' + flowWeekRangeLabel(rpS, rpE) + ' г.';
                    }
                }
                html += '<span class="flow-summary-label">Последние показания <span class="flow-summary-date-inline">' + lastDateInline368 + '</span></span>';
""",
'E10: renderList — диапазон')

# ----------------------------------------------------------------
# 11. _buildDetailHtml — подпись «за ДД.ММ–ДД.ММ.ГГГГ»
# ----------------------------------------------------------------
rep(
"""            var lastReadingLabel = 'Последние показания';
""",
"""            var lastReadingLabel = 'Последние показания';
            // Task 368: показания за период — подпись «за ДД.ММ–ДД.ММ.ГГГГ»
            var lastDateInline = 'за ' + this._fmtDate(m.dateCurr) + ' г.';
            if (this._isWeeklyMeter(m) || this._isMonthlyMeter(m)) {
                var ldS = this._parseMdy(m.datePrev);
                var ldE = this._parseMdy(m.dateCurr);
                if (ldS && ldE && this._dayKey(ldS) < this._dayKey(ldE)) {
                    lastDateInline = 'за ' + flowWeekRangeLabel(ldS, ldE) + ' г.';
                }
            }
""",
'E11a: _buildDetailHtml — переменная')

rep(
"""                        ' <span class="flow-detail-date-inline">за ' + this._fmtDate(m.dateCurr) + ' г.</span>' +
""",
"""                        ' <span class="flow-detail-date-inline">' + lastDateInline + '</span>' +
""",
'E11b: _buildDetailHtml — вставка')

# ----------------------------------------------------------------
# 12. Хронология — диапазон для записей периодных расходомеров
# ----------------------------------------------------------------
rep(
"""                var rEt = String(r.entryType || '').trim().toLowerCase();
                var isPeriodRow = (rEt === 'неделя' || rEt === 'месяц');
""",
"""                var rEt = String(r.entryType || '').trim().toLowerCase();
                var isPeriodRow = (rEt === 'неделя' || rEt === 'месяц');
                // Task 368: записи недельных/месячных расходомеров вводятся
                // за период двух дат — показываем диапазон (без бейджа
                // «нед/мес»: это показания, а не агрегат «расход за
                // неделю/месяц» Хозрасчёта №1)
                var isMeterPeriodRow = !isPeriodRow &&
                    (this._isWeeklyMeter(meter) || this._isMonthlyMeter(meter));
""",
'E12a: хронология — флаг')

rep(
"""                } else {
                    html += '<td class="flow-archive-date">' + this._fmtDate(r.dateCurr) + '</td>';
                }
""",
"""                } else if (isMeterPeriodRow && _flowParseDate(r.datePrev) &&
                           _flowParseDate(r.dateCurr) &&
                           _flowParseDate(r.datePrev).getTime() < _flowParseDate(r.dateCurr).getTime()) {
                    // Task 368: показания за период — диапазон дат записи
                    html += '<td class="flow-archive-date flow-archive-date-range">' +
                            this._fmtDateShort(r.datePrev) + '–' + this._fmtDate(r.dateCurr) + '</td>';
                } else {
                    html += '<td class="flow-archive-date">' + this._fmtDate(r.dateCurr) + '</td>';
                }
""",
'E12b: хронология — диапазон')

io.open(PATH, 'w', encoding='utf-8').write(src)
print('index.html: %d → %d строк' % (orig.count('\n'), src.count('\n')))
print('Все правки Task 368 применены.')
