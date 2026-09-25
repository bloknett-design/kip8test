#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 411 — форма инструктажа/ПЗ в картах работников:

1) РАБОТНИК: выпадающий список фамилий убран — работник вычисляется
   из карточки/ячейки входа; статичная строка «ФИО · таб. №» (как
   шторка увольнения, Task 318) + скрытое поле #wsTrTabNo (держатель
   значения для submit).
2) ОДНА ДАТА: instr-режим — «Дата проведения»; «Дата окончания» и
   «Длит., дн» скрыты; submit всегда пишет однодневную запись.
   Мероприятие (обучение может быть многодневным) — прежний период.
3) Выбор пункта «Список_И_и_ПЗ» (Task 410) — без изменений.

Заменяет только index.html (сервер WorkSchedule.gs не меняется).
"""
import io

PATH = '/home/z/my-project/kip8test/index.html'


def replace_once(s, old, new, tag):
    n = s.count(old)
    assert n == 1, '%s: ожидается 1 вхождение, найдено %d' % (tag, n)
    print('OK  %s' % tag)
    return s.replace(old, new, 1)


def main():
    with io.open(PATH, encoding='utf-8') as f:
        s = f.read()

    # --- 1. HTML: работник — статичная строка (отдельная строка
    #         формы), тип — в своей строке во всю ширину ---
    old1 = """    <div class="flow-input-row">
        <div class="flow-input-group" style="flex:0 0 35%;" id="wsTrTabGroup">
            <label class="flow-input-label" for="wsTrTabNo">Таб. №</label>
            <select id="wsTrTabNo" class="flow-input-field-small"></select>
        </div>
        <!-- Task 410: группа «Тип» скрывается в instr-режиме — записи
             «Инструктажей» добавляются ВЫБОРОМ пункта «Список_И_и_ПЗ»
             без выбора типа (вид определяет сам пункт) -->
        <div class="flow-input-group" style="flex:1 1 65%;" id="wsTrTypeGroup">"""
    new1 = """    <div class="flow-input-row">
        <!-- Task 411: работник вычисляется из карточки/ячейки, где
             открыта форма (кнопка блока, попап ячейки, правка записи) —
             выпадающий список фамилий убран; статичная строка
             «ФИО · таб. №» (как шторка увольнения, Task 318) +
             скрытое поле значения (#wsTrTabNo остаётся держателем
             табельного номера для submit) -->
        <div class="flow-input-group" style="flex:1 1 100%;" id="wsTrTabGroup">
            <label class="flow-input-label">Работник</label>
            <div id="wsTrEmp" class="ws-dismiss-emp">—</div>
            <input type="hidden" id="wsTrTabNo">
        </div>
    </div>
    <div class="flow-input-row">
        <!-- Task 410: группа «Тип» скрывается в instr-режиме — записи
             «Инструктажей» добавляются ВЫБОРОМ пункта «Список_И_и_ПЗ»
             без выбора типа (вид определяет сам пункт); Task 411:
             работник — отдельной строкой выше, тип во всю ширину -->
        <div class="flow-input-group" style="flex:1 1 100%;" id="wsTrTypeGroup">"""
    s = replace_once(s, old1, new1, '1. HTML: статичная строка работника')

    # --- 2. HTML: даты — id групп + подпись даты начала ---
    old2 = """    <div class="flow-input-row">
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsTrStart">Дата начала</label>
            <input type="date" id="wsTrStart" class="flow-input-field-small">
        </div>
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsTrEnd">Дата окончания</label>
            <input type="date" id="wsTrEnd" class="flow-input-field-small">
        </div>
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsTrDays">Длит., дн</label>
            <input type="number" id="wsTrDays" class="flow-input-field-small" min="1" value="1">
        </div>
    </div>"""
    new2 = """    <!-- Task 411: инструктаж/ПЗ — ОДНО поле даты «Дата проведения»
         («Дата окончания» и «Длит., дн» скрываются в instr-режиме —
         _applyTrFormMode; submit всегда пишет однодневную запись);
         мероприятие (обучение может быть многодневным) — период -->
    <div class="flow-input-row">
        <div class="flow-input-group" id="wsTrStartGroup">
            <label class="flow-input-label" for="wsTrStart" id="wsTrStartLabel">Дата начала</label>
            <input type="date" id="wsTrStart" class="flow-input-field-small">
        </div>
        <div class="flow-input-group" id="wsTrEndGroup">
            <label class="flow-input-label" for="wsTrEnd">Дата окончания</label>
            <input type="date" id="wsTrEnd" class="flow-input-field-small">
        </div>
        <div class="flow-input-group" id="wsTrDaysGroup">
            <label class="flow-input-label" for="wsTrDays">Длит., дн</label>
            <input type="number" id="wsTrDays" class="flow-input-field-small" min="1" value="1">
        </div>
    </div>"""
    s = replace_once(s, old2, new2, '2. HTML: id групп дат + подпись')

    # --- 3. JS: _applyTrFormMode — одна дата в instr-режиме ---
    old3 = """        // Task 410: применить режим шторки к разметке — instr: поле
        // «Тип» скрыто (тип записи определит выбранный пункт
        // «Список_И_и_ПЗ»), «Таб. №» во всю ширину, подпись «Инструктаж
        // / проверка знаний»; мероприятие — прежний вид формы
        _applyTrFormMode: function() {
            var typeGroup = document.getElementById('wsTrTypeGroup');
            var tabGroup = document.getElementById('wsTrTabGroup');
            var lbl = document.getElementById('wsTrTitleLabel');
            var instr = !!this._trInstrMode;
            if (typeGroup) typeGroup.style.display = instr ? 'none' : '';
            if (tabGroup) tabGroup.style.flex = instr ? '1 1 100%' : '0 0 35%';
            if (lbl) {
                lbl.textContent = instr
                    ? 'Инструктаж / проверка знаний' : 'Тема';
            }
        },"""
    new3 = """        // Task 410 → 411: применить режим шторки к разметке — instr:
        // поле «Тип» скрыто (тип записи определит выбранный пункт
        // «Список_И_и_ПЗ»), подпись «Инструктаж / проверка знаний»,
        // ОДНА дата («Дата проведения»: «Дата окончания» и «Длит., дн»
        // скрыты — инструктаж/ПЗ проводится одним днём); мероприятие —
        // прежний вид (период: обучение может быть многодневным)
        _applyTrFormMode: function() {
            var typeGroup = document.getElementById('wsTrTypeGroup');
            var lbl = document.getElementById('wsTrTitleLabel');
            var endGroup = document.getElementById('wsTrEndGroup');
            var daysGroup = document.getElementById('wsTrDaysGroup');
            var startLbl = document.getElementById('wsTrStartLabel');
            var instr = !!this._trInstrMode;
            if (typeGroup) typeGroup.style.display = instr ? 'none' : '';
            if (lbl) {
                lbl.textContent = instr
                    ? 'Инструктаж / проверка знаний' : 'Тема';
            }
            // Task 411: однодневность инструктажа/ПЗ в форме
            if (endGroup) endGroup.style.display = instr ? 'none' : '';
            if (daysGroup) daysGroup.style.display = instr ? 'none' : '';
            if (startLbl) {
                startLbl.textContent = instr
                    ? 'Дата проведения' : 'Дата начала';
            }
        },"""
    s = replace_once(s, old3, new3, '3. JS: _applyTrFormMode — одна дата')

    # --- 4. JS: openTrainingForm — работник из карточки входа ---
    old4 = """        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {
            if (!this._canEdit) return;
            var sheetTitle = document.getElementById('wsTrSheetTitle');
            var submitBtn = document.getElementById('wsTrSubmitBtn');
            var empSel = document.getElementById('wsTrTabNo');
            if (empSel) {
                var html = '<option value="">— выберите —</option>';
                for (var i = 0; i < this._EMPLOYEES.length; i++) {
                    html += '<option value="' + this._esc(this._EMPLOYEES[i]['таб_номер']) + '">' +
                            this._esc(this._EMPLOYEES[i]['таб_номер']) + ' — ' + this._esc(this._EMPLOYEES[i]['ФИО']) +
                            '</option>';
                }
                empSel.innerHTML = html;
                // Task 303: префилл из попапа ячейки — сотрудник и дата
                // (вызов с «+ Мероприятие…»: быстрая привязка события к
                // выбранному дню; Task 308: страницы «Инструктажи»
                // больше нет — попап ячейки остался единственным входом
                // к форме «Новое мероприятие»)
                if (prefillTab) empSel.value = String(prefillTab);
            }"""
    new4 = """        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {
            if (!this._canEdit) return;
            var sheetTitle = document.getElementById('wsTrSheetTitle');
            var submitBtn = document.getElementById('wsTrSubmitBtn');
            // Task 411: работник вычисляется из КАРТОЧКИ/ЯЧЕЙКИ входа
            // (кнопка блока, попап ячейки, правка записи) — выпадающий
            // список фамилий убран; статичная строка «ФИО · таб. №»
            // (как шторка увольнения, Task 318); #wsTrTabNo остаётся
            // скрытым держателем значения для submit
            var tabNo = String(prefillTab ||
                               (editTraining && editTraining['таб_номер']) ||
                               '').trim();
            var emp = null;
            for (var e = 0; e < (this._EMPLOYEES || []).length; e++) {
                if (String(this._EMPLOYEES[e]['таб_номер']) === tabNo) {
                    emp = this._EMPLOYEES[e];
                    break;
                }
            }
            if (!emp) {
                if (typeof KipToast !== 'undefined') {
                    KipToast.show('Работник не определён — откройте форму из карточки работника');
                }
                return;
            }
            var empDiv = document.getElementById('wsTrEmp');
            if (empDiv) {
                empDiv.textContent = emp['ФИО'] + ' · таб. №' + emp['таб_номер'];
            }
            var empInput = document.getElementById('wsTrTabNo');
            if (empInput) empInput.value = String(emp['таб_номер']);"""
    s = replace_once(s, old4, new4, '4. JS: openTrainingForm — работник входа')

    # --- 5. JS: правка — работник записи уже показан выше ---
    old5 = """                this._trEditType = String(editTraining.тип || '');
                this._trInstrMode = this._isInstrType(this._trEditType);
                if (empSel) empSel.value = String(editTraining['таб_номер'] || '');
                if (!this._trInstrMode) {"""
    new5 = """                this._trEditType = String(editTraining.тип || '');
                this._trInstrMode = this._isInstrType(this._trEditType);
                // Task 411: работник записи уже отображён выше
                // (строка из таб. номера правимой записи)
                if (!this._trInstrMode) {"""
    s = replace_once(s, old5, new5, '5. JS: правка — без выбора работника')

    # --- 6. JS: фокус — первый видимый контроль ---
    old6 = """            document.getElementById('wsTrOverlay').classList.add('active');
            document.getElementById('wsTrSheet').classList.add('active');
            setTimeout(function() {
                var f = document.getElementById('wsTrTabNo');
                if (f) f.focus();
            }, 350);
        },"""
    new6 = """            document.getElementById('wsTrOverlay').classList.add('active');
            document.getElementById('wsTrSheet').classList.add('active');
            setTimeout(function() {
                // Task 411: фокус — первый видимый контроль формы
                // (выпадающий список работников убран): пункт шаблона в
                // instr-режиме, тип — в режиме мероприятия
                var sel = document.getElementById('wsTrTitleSel');
                var f = (WorkSchedule._trInstrMode && sel && !sel.hidden)
                    ? sel : document.getElementById(WorkSchedule._trInstrMode
                        ? 'wsTrTitle' : 'wsTrType');
                if (f) f.focus();
            }, 350);
        },"""
    s = replace_once(s, old6, new6, '6. JS: фокус на первый видимый контроль')

    # --- 7. JS: submit — однодневная запись instr + валидации ---
    old7 = """            var startDate = document.getElementById('wsTrStart').value;
            var endDate = document.getElementById('wsTrEnd').value || startDate;
            var days = parseInt(document.getElementById('wsTrDays').value, 10) || 1;
            var comment = document.getElementById('wsTrComment').value.slice(0, 500);
            var self = this;

            if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Выберите работника'); return; }
            if (!tema) {
                if (typeof KipToast !== 'undefined') {
                    KipToast.show(this._trInstrMode && trSel && !trSel.hidden
                        ? 'Выберите пункт из списка'
                        : 'Введите тему мероприятия');
                }
                return;
            }
            if (!startDate) { if (typeof KipToast !== 'undefined') KipToast.show('Укажите дату начала'); return; }"""
    new7 = """            var startDate = document.getElementById('wsTrStart').value;
            var endDate = document.getElementById('wsTrEnd').value || startDate;
            var days = parseInt(document.getElementById('wsTrDays').value, 10) || 1;
            // Task 411: инструктаж/ПЗ — однодневное событие: дата
            // окончания = дата проведения, длительность 1 день
            // (скрытые поля могли хранить значения прошлой правки
            // многодневного мероприятия)
            if (this._trInstrMode) {
                endDate = startDate;
                days = 1;
            }
            var comment = document.getElementById('wsTrComment').value.slice(0, 500);
            var self = this;

            // Task 411: работник задан карточкой входа (скрытое поле);
            // пустое значение — защита от прямых вызовов
            if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Работник не определён'); return; }
            if (!tema) {
                if (typeof KipToast !== 'undefined') {
                    KipToast.show(this._trInstrMode && trSel && !trSel.hidden
                        ? 'Выберите пункт из списка'
                        : 'Введите тему мероприятия');
                }
                return;
            }
            if (!startDate) {
                if (typeof KipToast !== 'undefined') {
                    KipToast.show(this._trInstrMode
                        ? 'Укажите дату проведения' : 'Укажите дату начала');
                }
                return;
            }"""
    s = replace_once(s, old7, new7, '7. JS: submit — однодневность + валидации')

    with io.open(PATH, 'w', encoding='utf-8') as f:
        f.write(s)
    print('index.html обновлён')


if __name__ == '__main__':
    main()
