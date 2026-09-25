#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 410 — заявка: «Не работает: в форме добавления инструктажа или
проверки знаний, в карточке работников, в блоке инструктажей и проверки
знаний, старые выпадающие списки, в том числе с обучение, прогул,
примечание, а нужно, чтобы я мог выбрать один из инструктажей или
проверки знаний из таблицы Список_И_и_ПЗ».

РЕШЕНИЕ — режимы шторки #wsTrSheet:
1) INSTR-режим (вход «+ Инструктаж…» блока инструктажей; правка записей
   инструктаж/проверка_знаний): поле «Тип» СКРЫТО, «Тема» → строгий
   select ВСЕХ пунктов «Список_И_и_ПЗ» одним списком с группами
   «Инструктажи» / «Проверка знаний»; тип записи = «вид» пункта
   (_instrTypeOfTheme); «вне списка» (правка) — тип правимой записи.
2) Мероприятие (вход «+ Мероприятие…» блока и попапа ячейки; правка
   событий): «Тип» — только обучение/прогул/примечание (инструктаж/
   проверка_знаний убраны из опций), «Тема» — свободный ввод;
   дефолт попапа ячейки — «обучение» (было «инструктаж», Task 303).
"""
import io

ROOT = '/home/z/my-project/kip8test/index.html'

edits = []


def E(old, new):
    edits.append((old, new))


def main():
    with io.open(ROOT, encoding='utf-8') as f:
        s = f.read()

    # --- 1. HTML: id групп + 3 опции типа + id ярлыка темы -----------
    E('''        <div class="flow-input-group" style="flex:0 0 35%;">
            <label class="flow-input-label" for="wsTrTabNo">Таб. №</label>
            <select id="wsTrTabNo" class="flow-input-field-small"></select>
        </div>
        <div class="flow-input-group" style="flex:1 1 65%;">
            <label class="flow-input-label" for="wsTrType">Тип</label>
            <!-- Task 306: добавлены «прогул» (ПР) и «примечание» (*) —
                 по заявке пользователя к И/ОБ/ПЗ; карта тип→код —
                 _trainingCodeOf (клиент) / TRAINING_TYPE_TO_STATUS
                 (сервер), цвета бейджа — из «Коды_статусов» -->
            <select id="wsTrType" class="flow-input-field-small">
                <option value="инструктаж">инструктаж</option>
                <option value="обучение">обучение</option>
                <option value="проверка_знаний">проверка знаний</option>
                <option value="прогул">прогул</option>
                <option value="примечание">примечание</option>
            </select>
        </div>''',
      '''        <div class="flow-input-group" style="flex:0 0 35%;" id="wsTrTabGroup">
            <label class="flow-input-label" for="wsTrTabNo">Таб. №</label>
            <select id="wsTrTabNo" class="flow-input-field-small"></select>
        </div>
        <!-- Task 410: группа «Тип» скрывается в instr-режиме — записи
             «Инструктажей» добавляются ВЫБОРОМ пункта «Список_И_и_ПЗ»
             без выбора типа (вид определяет сам пункт) -->
        <div class="flow-input-group" style="flex:1 1 65%;" id="wsTrTypeGroup">
            <label class="flow-input-label" for="wsTrType">Тип</label>
            <!-- Task 306: добавлены «прогул» (ПР) и «примечание» (*) —
                 по заявке пользователя к И/ОБ/ПЗ; карта тип→код —
                 _trainingCodeOf (клиент) / TRAINING_TYPE_TO_STATUS
                 (сервер), цвета бейджа — из «Коды_статусов».
                 Task 410: инструктаж/проверка знаний УБРАНЫ — записи
                 «Инструктажей» создаются только кнопкой «+ Инструктаж…»
                 блока инструктажей (строгий выбор пункта
                 «Список_И_и_ПЗ», тип = «вид» пункта) -->
            <select id="wsTrType" class="flow-input-field-small">
                <option value="обучение">обучение</option>
                <option value="прогул">прогул</option>
                <option value="примечание">примечание</option>
            </select>
        </div>''')

    E('''            <label class="flow-input-label" for="wsTrTitle">Тема</label>
            <!-- Task 408 (заявка: записи «Инструктажей» формируются
                 РУЧНЫМ ВЫБОРОМ из шаблонного списка): тип
                 инструктаж/проверка знаний — СТРОГИЙ select пунктов
                 «Список_И_и_ПЗ» этого вида (свободного ввода нет;
                 внеплановые — сначала добавить в список); прочие типы
                 и ОТСУТСТВИЕ шаблона (лист не создан/сервер старый) —
                 прежний текстовый ввод #wsTrTitle (Task 407 datalist
                 остаётся как деградация) -->''',
      '''            <!-- Task 410: подпись переключается по режимам (id для
                 JS): instr — «Инструктаж / проверка знаний» -->
            <label class="flow-input-label" for="wsTrTitle" id="wsTrTitleLabel">Тема</label>
            <!-- Task 408 (заявка: записи «Инструктажей» формируются
                 РУЧНЫМ ВЫБОРОМ из шаблонного списка). Task 410:
                 instr-режим — СТРОГИЙ select ВСЕХ пунктов
                 «Список_И_и_ПЗ» одним списком (группы «Инструктажи» /
                 «Проверка знаний»; тип записи = «вид» пункта;
                 свободного ввода нет); мероприятие (обучение/прогул/
                 примечание) и ОТСУТСТВИЕ шаблона (лист не создан/
                 сервер старый) — прежний текстовый ввод #wsTrTitle
                 (Task 407 datalist остаётся как деградация) -->''')

    # --- 2. Свойства режима -----------------------------------------
    E('''        _INSTR_LIST: [],
        _INSTR_ALL: [],''',
      '''        _INSTR_LIST: [],
        _INSTR_ALL: [],
        // Task 410: режим шторки «+ Инструктаж…» — выбор пункта
        // «Список_И_и_ПЗ» без поля «Тип» (вид пункта = тип записи);
        // _trEditType — тип правимой записи (фолбэк «вне списка»)
        _trInstrMode: false,
        _trEditType: '',''')

    # --- 3. _instrTypeOfTheme (после _normInstrKind) ------------------
    E('''            return v === 'проверка_знаний' ? 'проверка_знаний'
                                            : 'инструктаж';
        },
''',
      '''            return v === 'проверка_знаний' ? 'проверка_знаний'
                                            : 'инструктаж';
        },

        // Task 410: тип записи «Инструктажей» по теме — «вид» пункта
        // «Список_И_и_ПЗ» (нормализация 407: регистр/пробелы/«ё»);
        // темы нет среди пунктов («вне списка» — правка старой
        // записи) — пусто (фолбэк в submitTrainingForm)
        _instrTypeOfTheme: function(тема) {
            var key = this._normInstrKey(тема);
            if (!key) return '';
            for (var i = 0; i < (this._INSTR_LIST || []).length; i++) {
                if (this._normInstrKey(this._INSTR_LIST[i].название) === key) {
                    return this._normInstrKind(this._INSTR_LIST[i].вид);
                }
            }
            return '';
        },
''')

    # --- 4. _syncTrTitleField: все пункты с группами ------------------
    E('''        // Task 408: СТРОГИЙ выбор пункта шаблона в шторке «Новое
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
        },''',
      '''        // Task 408 → 410: СТРОГИЙ выбор пункта шаблона — instr-режим
        // («+ Инструктаж…» блока инструктажей) показывает select ВСЕХ
        // пунктов «Список_И_и_ПЗ» ОДНИМ списком с группами
        // «Инструктажи» / «Проверка знаний» (тип записи = «вид»
        // выбранного пункта; свободного ввода нет); мероприятие
        // (обучение/прогул/примечание) и ОТСУТСТВИЕ шаблона — прежний
        // текстовый ввод (#wsTrTitle + datalist). selValue — тема
        // правки: совпала с пунктом — выбрать его; нет — отдельный
        // пункт «(вне списка)» (значение сохранится, можно перевыбрать)
        _syncTrTitleField: function(selValue) {
            var sel = document.getElementById('wsTrTitleSel');
            var inp = document.getElementById('wsTrTitle');
            var hint = document.getElementById('wsTrItemHint');
            if (!sel || !inp) return;
            var useSel = !!this._trInstrMode &&
                         (this._INSTR_LIST || []).length > 0;
            sel.hidden = !useSel;
            inp.hidden = !!useSel;
            if (useSel) {
                var opts = ['<option value="">— выберите из списка —</option>'];
                var gIns = [], gPz = [];
                for (var i = 0; i < this._INSTR_LIST.length; i++) {
                    var nm = String(this._INSTR_LIST[i].название || '');
                    if (!nm) continue;
                    (this._normInstrKind(this._INSTR_LIST[i].вид) === 'проверка_знаний'
                        ? gPz : gIns).push(nm);
                }
                if (gIns.length) {
                    opts.push('<optgroup label="Инструктажи">');
                    for (var a = 0; a < gIns.length; a++) {
                        opts.push('<option value="' + this._esc(gIns[a]) + '">' +
                                  this._esc(gIns[a]) + '</option>');
                    }
                    opts.push('</optgroup>');
                }
                if (gPz.length) {
                    opts.push('<optgroup label="Проверка знаний">');
                    for (var b = 0; b < gPz.length; b++) {
                        opts.push('<option value="' + this._esc(gPz[b]) + '">' +
                                  this._esc(gPz[b]) + '</option>');
                    }
                    opts.push('</optgroup>');
                }
                var matchName = '';
                for (var j = 0; j < this._INSTR_LIST.length; j++) {
                    var nm2 = String(this._INSTR_LIST[j].название || '');
                    if (!nm2) continue;
                    if (selValue && this._normInstrKey(selValue) ===
                        this._normInstrKey(nm2)) {
                        matchName = nm2;
                        break;
                    }
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
        },''')

    # --- 5. _applyTrFormMode + openTrainingForm: режимы/заголовки ----
    E('''        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {''',
      '''        // Task 410: применить режим шторки к разметке — instr: поле
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
        },

        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {''')

    E('''            this._editTrainingId = null;
            if (editTraining && editTraining.id) {
                this._editTrainingId = parseInt(editTraining.id, 10);
                if (empSel) empSel.value = String(editTraining['таб_номер'] || '');
                document.getElementById('wsTrType').value =
                    String(editTraining.тип || 'инструктаж');
                document.getElementById('wsTrTitle').value =
                    String(editTraining.тема || '');''',
      '''            this._editTrainingId = null;
            this._trEditType = '';
            if (editTraining && editTraining.id) {
                this._editTrainingId = parseInt(editTraining.id, 10);
                // Task 410: правка инструктажа/ПЗ — instr-режим (select
                // «Список_И_и_ПЗ»); мероприятия — прежний ввод типа
                this._trEditType = String(editTraining.тип || '');
                this._trInstrMode = this._isInstrType(this._trEditType);
                if (empSel) empSel.value = String(editTraining['таб_номер'] || '');
                if (!this._trInstrMode) {
                    document.getElementById('wsTrType').value =
                        String(editTraining.тип || 'обучение');
                }
                document.getElementById('wsTrTitle').value =
                    String(editTraining.тема || '');''')

    E('''                // Task 408: тема правки — в строгий select (совпала с
                // пунктом — выбрана; «вне списка» — отдельный пункт)
                this._syncTrTitleField(String(editTraining.тема || ''));
                if (sheetTitle) sheetTitle.textContent = 'Правка мероприятия';
                if (submitBtn) submitBtn.textContent = 'Сохранить';''',
      '''                this._applyTrFormMode();
                // Task 408: тема правки — в строгий select (совпала с
                // пунктом — выбрана; «вне списка» — отдельный пункт)
                this._syncTrTitleField(String(editTraining.тема || ''));
                if (sheetTitle) {
                    sheetTitle.textContent = this._trInstrMode
                        ? 'Правка инструктажа / проверки знаний'
                        : 'Правка мероприятия';
                }
                if (submitBtn) submitBtn.textContent = 'Сохранить';''')

    E('''                // Task 405: тип по умолчанию — из кнопки входа
                // («+ Мероприятие…» блока мероприятий → обучение,
                // «+ Инструктаж…» → инструктаж); без указания —
                // прежний дефолт «инструктаж» (попап ячейки)
                var preTip = String(prefillType || '').trim();
                document.getElementById('wsTrType').value =
                    (preTip === 'инструктаж' || preTip === 'обучение' ||
                     preTip === 'проверка_знаний' || preTip === 'прогул' ||
                     preTip === 'примечание') ? preTip : 'инструктаж';
                document.getElementById('wsTrTitle').value = '';
                document.getElementById('wsTrComment').value = '';
                // Task 408: новый инструктаж/ПЗ — select «— выберите
                // из списка —»
                this._syncTrTitleField();
                if (sheetTitle) sheetTitle.textContent = 'Новое мероприятие';
                if (submitBtn) submitBtn.textContent = 'Добавить';''',
      '''                // Task 405 → 410: режим — из кнопки входа: «+ Инструктаж…»
                // блока инструктажей → instr-режим (select
                // «Список_И_и_ПЗ», поле «Тип» скрыто); «+ Мероприятие…»
                // (блок/попап ячейки) → обучение/прогул/примечание,
                // дефолт «обучение»
                var preTip = String(prefillType || '').trim();
                this._trInstrMode = this._isInstrType(preTip);
                if (!this._trInstrMode) {
                    document.getElementById('wsTrType').value =
                        (preTip === 'обучение' || preTip === 'прогул' ||
                         preTip === 'примечание') ? preTip : 'обучение';
                }
                document.getElementById('wsTrTitle').value = '';
                document.getElementById('wsTrComment').value = '';
                this._applyTrFormMode();
                // Task 408: новый инструктаж/ПЗ — select «— выберите
                // из списка —»
                this._syncTrTitleField();
                if (sheetTitle) {
                    sheetTitle.textContent = this._trInstrMode
                        ? 'Новый инструктаж / проверка знаний'
                        : 'Новое мероприятие';
                }
                if (submitBtn) submitBtn.textContent = 'Добавить';''')

    # --- 6. submitTrainingForm: тема/тип/тосты -----------------------
    E('''            var tip = document.getElementById('wsTrType').value;
            // Task 408: инструктаж/ПЗ со шаблоном — тема ТОЛЬКО из
            // строгого select (свободный ввод скрыт); прочие типы —
            // прежний текстовый ввод
            var trSel = document.getElementById('wsTrTitleSel');
            var trInp = document.getElementById('wsTrTitle');
            var tema = (this._isInstrType(tip) && trSel && !trSel.hidden)
                ? String(trSel.value || '').trim()
                : String((trInp && trInp.value) || '').trim();''',
      '''            var tip = document.getElementById('wsTrType').value;
            // Task 408 → 410: instr-режим со шаблоном — тема ТОЛЬКО из
            // строгого select (свободный ввод скрыт); мероприятие —
            // прежний текстовый ввод
            var trSel = document.getElementById('wsTrTitleSel');
            var trInp = document.getElementById('wsTrTitle');
            var tema = (this._trInstrMode && trSel && !trSel.hidden)
                ? String(trSel.value || '').trim()
                : String((trInp && trInp.value) || '').trim();
            // Task 410: тип записи «Инструктажей» — «вид» выбранного
            // пункта шаблона; «вне списка» (правка) — тип правимой
            // записи, фолбэк «инструктаж»
            if (this._trInstrMode) {
                tip = this._instrTypeOfTheme(tema) ||
                      (this._isInstrType(this._trEditType)
                          ? this._trEditType : 'инструктаж');
            }''')

    E('''                    KipToast.show(this._isInstrType(tip) && trSel && !trSel.hidden
                        ? 'Выберите пункт из списка'
                        : 'Введите тему мероприятия');''',
      '''                    KipToast.show(this._trInstrMode && trSel && !trSel.hidden
                        ? 'Выберите пункт из списка'
                        : 'Введите тему мероприятия');''')

    E('''                        if (typeof KipToast !== 'undefined' && KipToast.show) {
                            KipToast.show('Мероприятие обновлено');
                        }''',
      '''                        if (typeof KipToast !== 'undefined' && KipToast.show) {
                            KipToast.show(self._trInstrMode
                                ? 'Запись обновлена'
                                : 'Мероприятие обновлено');
                        }''')

    E('''                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('Мероприятие добавлено');
                }''',
      '''                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show(self._trInstrMode
                        ? 'Запись добавлена'
                        : 'Мероприятие добавлено');
                }''')

    # --- 7. onPopupAddEvent: дефолт «обучение» -----------------------
    E('''        onPopupAddEvent: function() {
            if (!this._popupCell) return;
            var date = this._popupCell.date;
            var tabNo = this._popupCell['таб_номер'];
            this.closeCellPopup();
            this.openTrainingForm(tabNo, date);
        },''',
      '''        onPopupAddEvent: function() {
            if (!this._popupCell) return;
            var date = this._popupCell.date;
            var tabNo = this._popupCell['таб_номер'];
            this.closeCellPopup();
            // Task 410: дефолт «обучение» — инструктажи/ПЗ добавляются
            // из блока инструктажей (строгий выбор пункта
            // «Список_И_и_ПЗ»), в «мероприятиях» их больше нет
            this.openTrainingForm(tabNo, date, null, 'обучение');
        },''')

    # --- 8. Комментарий onEmpAddInstruction --------------------------
    E('''        // Task 405: «+ Инструктаж…» из блока «Повторные инструктажи и
        // периодическая проверка знаний» — шторка «Новое мероприятие»
        // с работником карточки и типом «инструктаж» (запись уйдёт в
        // таблицу «Инструктажи»); двойная защита — в openTrainingForm
        onEmpAddInstruction: function(tabNo) {''',
      '''        // Task 405 → 410: «+ Инструктаж…» из блока «Повторные
        // инструктажи и периодическая проверка знаний» — шторка
        // «Новый инструктаж / проверка знаний»: работник карточки,
        // выбор пункта «Список_И_и_ПЗ» (тип записи = «вид» пункта,
        // запись уйдёт в таблицу «Инструктажи»); двойная защита — в
        // openTrainingForm
        onEmpAddInstruction: function(tabNo) {''')

    # --- применение ---------------------------------------------------
    ok = 0
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            raise SystemExit('ЯКОРЬ НЕ УНИКАЛЕН (n=%d):\n%r' % (n, old[:120]))
        s = s.replace(old, new)
        ok += 1
    with io.open(ROOT, 'w', encoding='utf-8') as f:
        f.write(s)
    print('Применено правок: %d' % ok)


if __name__ == '__main__':
    main()
