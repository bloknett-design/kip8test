#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408 — ЧАСТЬ 2: карточка (год-стрелки, _wtabYearRecords),
# _renderInstrSection (year + снимок сроков), форма (select+hint+
# submit). Запускать ПОСЛЕ task408-patch.py.
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
    # --- 3a. _renderWorkerCard: записи года блока + год-стрелки ---
    (
"""            var trs = [];
            var trYStart = this._year + '-01-01', trYEnd = this._year + '-12-31';
            for (var ti = 0; ti < (this._TRAININGS || []).length; ti++) {
                var tRec = this._TRAININGS[ti];
                if (tRec['таб_номер'] !== tabNo) continue;
                var tS = String(tRec['дата_начала'] || '');
                if (!tS) continue;
                var tE = String(tRec['дата_окончания'] || tS);
                if (tE < trYStart || tS > trYEnd) continue;
                trs.push(tRec);
            }
            trs.sort(function(a, b) {
                return String(a.дата_начала).localeCompare(String(b.дата_начала));
            });
            // Task 405: деление годовых записей по типу — блок
            // «Мероприятия» (evs: обучение/примечание/прогул) и блок
            // «Повторные инструктажи…» (ins: инструктаж/проверка_знаний)
            var evs = [], ins = [];
            for (var si = 0; si < trs.length; si++) {
                if (this._isInstrType(trs[si].тип)) ins.push(trs[si]);
                else evs.push(trs[si]);
            }
""",
"""            // Task 408 (заявка: годовые архивы): на странице
            // «Работники» (asBlocks) блоки листают годы СТРЕЛКАМИ
            // «‹ год ›» — записи любого года из instrAll/eventsAll
            // (выбранный год хранится по работнику); попап ячейки
            // остаётся за ГОД ШАХМАТКИ
            var wYear = asBlocks ? this._wtabYearOf(tabNo) : this._year;
            var wRecs = this._wtabYearRecords(tabNo, wYear);
            var evs = wRecs.evs, ins = wRecs.ins;
"""),
    # --- 3b. Шапка b3 «Мероприятия»: год + навигатор ---
    (
"""            var b3 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Мероприятия · ' +
                  this._year + '</div><div class="ws-whead-a">' +
""",
"""            var b3 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Мероприятия · ' +
                  this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +
"""),
    # --- 3c. Шапка b5 «Повторные инструктажи…»: год + навигатор ---
    (
"""            var b5 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-wrap">Повторные инструктажи и периодическая проверка знаний · ' +
                  this._year + '</div><div class="ws-whead-a">' +
""",
"""            var b5 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-wrap">Повторные инструктажи и периодическая проверка знаний · ' +
                  this._wtabYearNav(tabNo, wYear) + '</div><div class="ws-whead-a">' +
"""),
    # --- 3d. Вызов _renderInstrSection с годом блока ---
    (
"""            if (this._INSTR_LIST && this._INSTR_LIST.length) {
                b5 += this._renderInstrSection(ins, tabNo, withEdit,
                                                asBlocks, this._INSTR_LIST);
""",
"""            if (this._INSTR_LIST && this._INSTR_LIST.length) {
                b5 += this._renderInstrSection(ins, tabNo, withEdit,
                                                asBlocks, this._INSTR_LIST, wYear);
"""),
    # --- 3e. _renderInstrSection: год + новые методы года ---
    (
"""        _renderInstrSection: function(ins, tabNo, withEdit, asBlocks, iList) {
            var html = '';
            var today = this._isoDate(new Date());
""",
"""        // Task 408: год просмотра блока «Повторные инструктажи…»
        // (стрелки ‹год› карточки). Не выбран/попап — год шахматки.
        // Снимок: «последний» и «след. срок» считаются по записям
        // ДО КОНЦА выбранного года; архивный год — нейтральная
        // строка срока, без красного «просрочено»
        _wtabYearOf: function(tabNo) {
            var y = this._wtabYear && this._wtabYear[String(tabNo)];
            y = parseInt(y, 10);
            if (y && y >= 1900 && y <= 2999) return y;
            return this._year || new Date().getFullYear();
        },

        // нижняя граница навигации — самый ранний год записи
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
                    var s = String(arr[i].дата_начала || '');
                    if (s.length >= 4) {
                        var y = parseInt(s.slice(0, 4), 10);
                        if (y && (min === null || y < min)) min = y;
                    }
                }
            }
            return min || (this._year || new Date().getFullYear());
        },

        // стрелка ‹/› — смена года работника и перерисовка страницы
        // «Работники»; границы клампятся (раньше записей нельзя,
        // выше максимума(текущий; год табеля) нельзя); возврат к
        // году табеля снимает персональный выбор
        _wtabYearShift: function(tabNo, delta) {
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
        },

        // навигатор «‹ 2026 ›» для заголовка блока карточки (только
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

        // записи работника за выбранный год блока — единый пул:
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
            var seen = {}, ins = [], evs = [];
            for (var i = 0; i < pool.length; i++) {
                var r = pool[i];
                if (String(r['таб_номер']) !== tabNo) continue;
                var s = String(r['дата_начала'] || '');
                if (!s) continue;
                var e = String(r['дата_окончания'] || s);
                if (e < yS || s > yE) continue;
                var id = parseInt(r.id, 10);
                var k = id ? ('i' + id)
                    : ('t' + s + '|' + String(r.тема || ''));
                if (seen[k]) continue;
                seen[k] = true;
                if (this._isInstrType(r.тип)) ins.push(r);
                else evs.push(r);
            }
            var byDate = function(a, b) {
                return String(a.дата_начала).localeCompare(String(b.дата_начала));
            };
            ins.sort(byDate);
            evs.sort(byDate);
            return { ins: ins, evs: evs };
        },

        _renderInstrSection: function(ins, tabNo, withEdit, asBlocks, iList, year) {
            var html = '';
            var today = this._isoDate(new Date());
            // Task 408: год блока (не задан — год шахматки); снимок
            // «последнего» ограничен концом выбранного года
            year = year || this._year || new Date().getFullYear();
            var nowY = new Date().getFullYear();
"""),
    # --- 3f. «последний» ≤ конец выбранного года ---
    (
"""                var last = null;
                for (var li = 0; li < all.length; li++) {
                    if (this._normInstrKey(all[li].тема) === gKey) {
                        last = all[li];
                    }
                }
""",
"""                var last = null;
                var lastCut = year + '-12-31';
                for (var li = 0; li < all.length; li++) {
                    if (String(all[li].дата_начала) > lastCut) continue;
                    if (this._normInstrKey(all[li].тема) === gKey) {
                        last = all[li];
                    }
                }
"""),
    # --- 3g. Пустое состояние: год в тексте ---
    (
"""                if (asBlocks && !gRows.length) {
                    html += last
                        ? '<div class="ws-emp-empty">— в этом году не проводился</div>'
                        : '<div class="ws-emp-empty">— не проводился</div>';
                }
""",
"""                if (asBlocks && !gRows.length) {
                    // Task 408: wording с номером года (архивы)
                    html += last
                        ? '<div class="ws-emp-empty">— за ' + year + ' год не проводился</div>'
                        : '<div class="ws-emp-empty">— не проводился</div>';
                }
"""),
    # --- 3h. Снимок срока в архивном году ---
    (
"""                var perN = parseFloat(gItem.периодичность) || 0;
                var dueIso = (last && perN > 0)
                    ? this._addMonthsIso(last.дата_начала, perN) : '';
                if (dueIso) {
                    html += (dueIso < today)
                        ? '<div class="ws-il-due ws-il-due-bad">⚠ просрочено с ' +
                          this._fmtDateRu(dueIso) + '</div>'
                        : '<div class="ws-il-due ws-il-due-ok">след. срок: ' +
                          this._fmtDateRu(dueIso) + ' ✓</div>';
                }
""",
"""                var perN = parseFloat(gItem.периодичность) || 0;
                var dueIso = (last && perN > 0)
                    ? this._addMonthsIso(last.дата_начала, perN) : '';
                if (dueIso) {
                    if (year < nowY) {
                        // Task 408: архивный год — нейтральный снимок
                        // срока (состояние на конец того года)
                        html += '<div class="ws-il-due">след. срок (на конец ' +
                                year + '): ' + this._fmtDateRu(dueIso) + '</div>';
                    } else {
                        html += (dueIso < today)
                            ? '<div class="ws-il-due ws-il-due-bad">⚠ просрочено с ' +
                              this._fmtDateRu(dueIso) + '</div>'
                            : '<div class="ws-il-due ws-il-due-ok">след. срок: ' +
                              this._fmtDateRu(dueIso) + ' ✓</div>';
                    }
                }
"""),
    # --- 3i. Форма: новые методы (select + подсказка) ---
    (
"""            dl.innerHTML = html;
        },

        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {
""",
"""            dl.innerHTML = html;
        },

        // Task 408: СТРОГИЙ выбор пункта шаблона в шторке «Новое
        // мероприятие» — тип инструктаж/проверка знаний показывает
        // SELECT пунктов «Список_И_и_ПЗ» этого вида (свободный ввод
        // скрыт; внеплановые темы — сначала добавить в список);
        // прочие типы и ОТСУТСТВИЕ шаблона — прежний текстовый ввод
        // (#wsTrTitle + datalist). selValue — тема правки: совпала с
        // пунктом — выбрать его; нет — отдельный пункт «(вне
        // списка)» (значение сохранится, можно перевыбрать)
        _syncTrTitleField: function(selValue) {
            var typeEl = document.getElementById('wsTrType');
            var sel = document.getElementById('wsTrTitleSel');
            var inp = document.getElementById('wsTrTitle');
            var hint = document.getElementById('wsTrItemHint');
            if (!sel || !inp) return;
            var tip = typeEl ? typeEl.value : '';
            var useSel = this._isInstrType(tip) &&
                         (this._INSTR_LIST || []).length > 0;
            sel.hidden = !useSel;
            inp.hidden = !!useSel;
            if (useSel) {
                var want = this._normInstrKind(tip);
                var opts = ['<option value="">— выберите из списка —</option>'];
                var matchName = '';
                for (var i = 0; i < this._INSTR_LIST.length; i++) {
                    var nm = String(this._INSTR_LIST[i].название || '');
                    if (this._normInstrKind(this._INSTR_LIST[i].вид) !== want) continue;
                    if (selValue && this._normInstrKey(selValue) ===
                        this._normInstrKey(nm)) {
                        matchName = nm;
                    }
                    opts.push('<option value="' + this._esc(nm) + '">' +
                              this._esc(nm) + '</option>');
                }
                if (selValue && !matchName) {
                    opts.push('<option value="' + this._esc(selValue) + '">' +
                              this._esc(selValue) + ' (вне списка)</option>');
                }
                sel.innerHTML = opts.join('');
                sel.value = matchName || String(selValue || '');
                this._updateTrItemHint();
            } else {
                if (hint) { hint.hidden = true; hint.textContent = ''; }
                this._fillTrTitleOptions();
            }
        },

        // Task 408: подсказка выбранного пункта — периодичность и
        // основание из шаблона (заявка: «вся необходимая информация
        // подтягивается»); разовый/без данных — строка скрыта
        _updateTrItemHint: function() {
            var sel = document.getElementById('wsTrTitleSel');
            var hint = document.getElementById('wsTrItemHint');
            if (!hint) return;
            var txt = '';
            if (sel && !sel.hidden) {
                var key = this._normInstrKey(sel.value);
                for (var i = 0; i < (this._INSTR_LIST || []).length; i++) {
                    if (this._normInstrKey(this._INSTR_LIST[i].название) !== key) continue;
                    var per = parseFloat(this._INSTR_LIST[i].периодичность) || 0;
                    var osn = String(this._INSTR_LIST[i].основание || '').trim();
                    if (per > 0) {
                        txt = 'раз в ' + per + ' ' +
                              this._plural(per, ['месяц', 'месяца', 'месяцев']);
                    }
                    if (osn) {
                        txt += (txt ? ' · ' : '') + 'Основание: ' + osn;
                    }
                    break;
                }
            }
            hint.textContent = txt;
            hint.hidden = !txt;
        },

        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {
"""),
    # --- 3j. Форма: wiring select/тип ---
    (
"""            var typeSel = document.getElementById('wsTrType');
            if (typeSel) {
                typeSel.onchange = function() {
                    WorkSchedule._fillTrTitleOptions();
                };
            }
            this._fillTrTitleOptions();
""",
"""            var typeSel = document.getElementById('wsTrType');
            if (typeSel) {
                typeSel.onchange = function() {
                    WorkSchedule._syncTrTitleField();
                };
            }
            var trSelEl = document.getElementById('wsTrTitleSel');
            if (trSelEl) {
                trSelEl.onchange = function() {
                    WorkSchedule._updateTrItemHint();
                };
            }
"""),
    # --- 3k. Форма: правка — тема в select ---
    (
"""                document.getElementById('wsTrComment').value =
                    String(editTraining.комментарий || '');
                if (sheetTitle) sheetTitle.textContent = 'Правка мероприятия';
""",
"""                document.getElementById('wsTrComment').value =
                    String(editTraining.комментарий || '');
                // Task 408: тема правки — в строгий select (совпала с
                // пунктом — выбрана; «вне списка» — отдельный пункт)
                this._syncTrTitleField(String(editTraining.тема || ''));
                if (sheetTitle) sheetTitle.textContent = 'Правка мероприятия';
"""),
    # --- 3l. Форма: новый — пустой select ---
    (
"""                document.getElementById('wsTrTitle').value = '';
                document.getElementById('wsTrComment').value = '';
                if (sheetTitle) sheetTitle.textContent = 'Новое мероприятие';
""",
"""                document.getElementById('wsTrTitle').value = '';
                document.getElementById('wsTrComment').value = '';
                // Task 408: новый инструктаж/ПЗ — select «— выберите
                // из списка —»
                this._syncTrTitleField();
                if (sheetTitle) sheetTitle.textContent = 'Новое мероприятие';
"""),
    # --- 3m. Submit: тема из select для инструктажа/ПЗ ---
    (
"""            var tabNo = document.getElementById('wsTrTabNo').value.trim();
            var tip = document.getElementById('wsTrType').value;
            var tema = document.getElementById('wsTrTitle').value.trim();
""",
"""            var tabNo = document.getElementById('wsTrTabNo').value.trim();
            var tip = document.getElementById('wsTrType').value;
            // Task 408: инструктаж/ПЗ со шаблоном — тема ТОЛЬКО из
            // строгого select (свободный ввод скрыт); прочие типы —
            // прежний текстовый ввод
            var trSel = document.getElementById('wsTrTitleSel');
            var trInp = document.getElementById('wsTrTitle');
            var tema = (this._isInstrType(tip) && trSel && !trSel.hidden)
                ? String(trSel.value || '').trim()
                : String((trInp && trInp.value) || '').trim();
"""),
    (
"""            if (!tema) { if (typeof KipToast !== 'undefined') KipToast.show('Введите тему мероприятия'); return; }
""",
"""            if (!tema) {
                if (typeof KipToast !== 'undefined') {
                    KipToast.show(this._isInstrType(tip) && trSel && !trSel.hidden
                        ? 'Выберите пункт из списка'
                        : 'Введите тему мероприятия');
                }
                return;
            }
"""),
])

print('ЧАСТЬ 2 применена')
