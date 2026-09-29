#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 443 — часть 3: index.html — СИЗ: поле «Дата изготовления» в
# шторке (необязательное), приоритет даты изготовления в расчёте
# даты окончания (подсказка + payload), строка «изгот. …» в
# карточке работника. Сервер считает дату окончания от даты
# изготовления при её наличии (фильтрующие коробки противогазов),
# иначе — от даты выдачи, как прежде.
import io

P = 'index.html'
s = io.open(P, encoding='utf-8').read()
n0 = s

def rep(old, new, tag):
    global s
    assert old in s, 'НЕ НАЙДЕНО (%s): %r' % (tag, old[:90])
    assert s.count(old) == 1, 'НЕ УНИКАЛЬНО (%s): %d вхождений' % (tag, s.count(old))
    s = s.replace(old, new)
    print('OK  %s' % tag)

# --- 1. Разметка шторки: комментарий + поле «Дата изготовления» --------
rep(
"""<!-- ===== Task 392: Bottom sheet — СИЗ работника (workSchedule) =====
     Средства индивидуальной защиты (лист «СИЗ» табель_КИП_ИОС;
     перечень — на основании Приказа Минтруда России от 29.10.2021
     N767н, образец — файл «Таблица СИЗ работникам КИП ИОС.xlsx»).
     «Дата окончания срока годности» НЕ вводится — считается
     автоматически (дата выдачи + срок годности) и показывается
     строкой под полями (wsPpeExpiryInfo). Наименование — ввод со
     списком стандартных позиций (datalist) или свободный текст. -->""",
"""<!-- ===== Task 392: Bottom sheet — СИЗ работника (workSchedule) =====
     Средства индивидуальной защиты (лист «СИЗ» табель_КИП_ИОС;
     перечень — на основании Приказа Минтруда России от 29.10.2021
     N767н, образец — файл «Таблица СИЗ работникам КИП ИОС.xlsx»).
     «Дата окончания срока годности» НЕ вводится — считается
     автоматически и показывается строкой под полями
     (wsPpeExpiryInfo): Task 443 — ПРИОРИТЕТ у даты изготовления
     (если указана — окончание = изготовление + срок, дата выдачи
     носит информационный характер; фильтрующие коробки противогазов
     и т.п.), иначе дата выдачи + срок годности. Наименование — ввод
     со списком стандартных позиций (datalist) или свободный текст. -->""",
'1. комментарий шторки')

rep(
"""    <div class="flow-input-row">
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsPpeIssued">Дата выдачи</label>
            <input type="date" id="wsPpeIssued" class="flow-input-field-small" onchange="WorkSchedule.onPpeFormInput()">
        </div>
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsPpeTerm">Срок годности</label>""",
"""    <div class="flow-input-row">
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsPpeIssued">Дата выдачи</label>
            <input type="date" id="wsPpeIssued" class="flow-input-field-small" onchange="WorkSchedule.onPpeFormInput()">
        </div>
        <!-- Task 443: дата изготовления — НЕОБЯЗАТЕЛЬНО; при наличии
             срок годности считается ОТ НЕЁ (дата окончания =
             изготовление + срок), дата выдачи — только информация -->
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsPpeManufactured">Дата изготовления</label>
            <input type="date" id="wsPpeManufactured" class="flow-input-field-small" onchange="WorkSchedule.onPpeFormInput()">
        </div>
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsPpeTerm">Срок годности</label>""",
'2. поле «Дата изготовления»')

rep(
"""    <!-- авто-дата окончания: «заполняется автоматически в
         зависимости от даты выдачи плюс срок годности» (образец) -->
    <div class="ws-ppe-form-info" id="wsPpeExpiryInfo">Дата окончания срока годности: —</div>
    <div class="ws-vac-form-hint">Дата окончания срока годности заполняется автоматически: дата выдачи плюс срок годности («До износа» — без даты). Перечень СИЗ — на основании Приказа Минтруда России от 29.10.2021 N767н.</div>""",
"""    <!-- авто-дата окончания (Task 443): приоритет — дата
         изготовления (если указана: изготовление + срок, дата
         выдачи — информационная), иначе дата выдачи + срок -->
    <div class="ws-ppe-form-info" id="wsPpeExpiryInfo">Дата окончания срока годности: —</div>
    <div class="ws-vac-form-hint">Дата окончания срока годности заполняется автоматически: если указана дата изготовления — от неё (дата выдачи — только информация), иначе — от даты выдачи, плюс срок годности («До износа» — без даты). Перечень СИЗ — на основании Приказа Минтруда России от 29.10.2021 N767н.</div>""",
'3. подсказка — приоритет изготовления')

# --- 2. openPpeForm: префилл/сброс даты изготовления --------------------
rep(
"""        // шторка «Новое СИЗ» / «Правка СИЗ». tabNo (необяз.) —
        // префилл работника из карточки; editPpe (необяз.) — запись
        // из _PPE: режим ПРАВКИ (id в _ppeEditId, submit уходит в
        // updatePpe). Дата окончания НЕ вводится — считается
        // автоматически (дата выдачи + срок годности) и показывается
        // строкой под полями (onPpeFormInput → wsPpeExpiryInfo)""",
"""        // шторка «Новое СИЗ» / «Правка СИЗ». tabNo (необяз.) —
        // префилл работника из карточки; editPpe (необяз.) — запись
        // из _PPE: режим ПРАВКИ (id в _ppeEditId, submit уходит в
        // updatePpe). Дата окончания НЕ вводится — считается
        // автоматически (Task 443: приоритет даты изготовления, при
        // её отсутствии — дата выдачи, + срок годности) и
        // показывается строкой под полями (onPpeFormInput →
        // wsPpeExpiryInfo)""",
'4. докстринг openPpeForm')

rep(
"""                document.getElementById('wsPpeIssued').value =
                    String(editPpe.дата_выдачи || '');
                document.getElementById('wsPpeComment').value =
                    String(editPpe.примечание || '');""",
"""                document.getElementById('wsPpeIssued').value =
                    String(editPpe.дата_выдачи || '');
                // Task 443: дата изготовления (необязательное поле)
                document.getElementById('wsPpeManufactured').value =
                    String(editPpe.дата_изготовления || '');
                document.getElementById('wsPpeComment').value =
                    String(editPpe.примечание || '');""",
'5a. openPpeForm — префилл правки')

rep(
"""                document.getElementById('wsPpeName').value = '';
                document.getElementById('wsPpeIssued').value = '';
                document.getElementById('wsPpeComment').value = '';""",
"""                document.getElementById('wsPpeName').value = '';
                document.getElementById('wsPpeIssued').value = '';
                document.getElementById('wsPpeManufactured').value = '';
                document.getElementById('wsPpeComment').value = '';""",
'5b. openPpeForm — сброс при создании')

# --- 3. Клиентский _ppeExpiry: комментарий + isoBase --------------------
rep(
"""        // дата окончания срока годности = дата выдачи + срок
        // (кламп дня к длине целевого месяца: 31.08 + 6 мес →
        // 28/29.02, не «3 марта»); «До износа» → строка «До
        // износа»; без даты/срока (или срок не распознан) → null
        _ppeExpiry: function(isoIssued, term) {
            var months = this._ppeTermMonths(term);
            if (months === -1) return 'До износа';
            if (!months) return null;
            var d = this._parseIsoLocal(String(isoIssued || ''));""",
"""        // дата окончания срока годности = базовая дата + срок
        // (кламп дня к длине целевого месяца: 31.08 + 6 мес →
        // 28/29.02, не «3 марта»). Task 443: базовая дата = дата
        // ИЗГОТОВЛЕНИЯ (ПРИОРИТЕТ, если указана), иначе дата
        // выдачи — выбирает вызывающий код (base = mfg || issued);
        // «До износа» → строка «До износа»; без даты/срока (или
        // срок не распознан) → null
        _ppeExpiry: function(isoBase, term) {
            var months = this._ppeTermMonths(term);
            if (months === -1) return 'До износа';
            if (!months) return null;
            var d = this._parseIsoLocal(String(isoBase || ''));""",
'6. клиентский _ppeExpiry — база')

# --- 4. onPpeFormInput: приоритет изготовления --------------------------
rep(
"""        onPpeFormInput: function() {
            var info = document.getElementById('wsPpeExpiryInfo');
            if (!info) return;
            var issued = document.getElementById('wsPpeIssued') ?
                document.getElementById('wsPpeIssued').value : '';
            var term = document.getElementById('wsPpeTerm') ?
                document.getElementById('wsPpeTerm').value : '';
            var exp = this._ppeExpiry(issued, term);
            var txt;
            if (exp === 'До износа') {
                txt = 'Дата окончания срока годности: До износа';
            } else if (exp) {
                txt = 'Дата окончания срока годности: ' + this._fmtDateRu(exp) +
                      ' (заполнится автоматически)';
            } else if (issued && term && this._ppeTermMonths(term) === null) {
                txt = 'Дата окончания срока годности: срок не распознан — заполните вручную в таблице';
            } else {
                txt = 'Дата окончания срока годности: —';
            }
            info.textContent = txt;
        },""",
"""        onPpeFormInput: function() {
            var info = document.getElementById('wsPpeExpiryInfo');
            if (!info) return;
            var issued = document.getElementById('wsPpeIssued') ?
                document.getElementById('wsPpeIssued').value : '';
            var manufactured = document.getElementById('wsPpeManufactured') ?
                document.getElementById('wsPpeManufactured').value : '';
            var term = document.getElementById('wsPpeTerm') ?
                document.getElementById('wsPpeTerm').value : '';
            // Task 443: ПРИОРИТЕТ даты изготовления — срок считается
            // ОТ НЕЁ (фильтрующие коробки противогазов и т.п.); без
            // неё — от даты выдачи, как прежде (Task 392)
            var base = manufactured || issued;
            var exp = this._ppeExpiry(base, term);
            var txt;
            if (exp === 'До износа') {
                txt = 'Дата окончания срока годности: До износа';
            } else if (exp) {
                txt = 'Дата окончания срока годности: ' + this._fmtDateRu(exp) +
                      (manufactured
                          ? ' (от даты изготовления — заполнится автоматически)'
                          : ' (заполнится автоматически)');
            } else if ((issued || manufactured) && term && this._ppeTermMonths(term) === null) {
                txt = 'Дата окончания срока годности: срок не распознан — заполните вручную в таблице';
            } else {
                txt = 'Дата окончания срока годности: —';
            }
            info.textContent = txt;
        },""",
'7. onPpeFormInput — приоритет')

# --- 5. submitPpeForm: payload с датой изготовления ---------------------
rep(
"""            var tabNo = document.getElementById('wsPpeTabNo').value.trim();
            var name = document.getElementById('wsPpeName').value.trim().slice(0, 300);
            var issued = document.getElementById('wsPpeIssued').value;
            var term = document.getElementById('wsPpeTerm').value;
            var comment = document.getElementById('wsPpeComment').value.slice(0, 200);
            var self = this;

            if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Выберите работника'); return; }
            if (!name) { if (typeof KipToast !== 'undefined') KipToast.show('Укажите наименование СИЗ'); return; }

            var payload = {
                'таб_номер': tabNo,
                наименование: name,
                дата_выдачи: issued || '',
                срок_годности: term || '',
                примечание: comment
            };""",
"""            var tabNo = document.getElementById('wsPpeTabNo').value.trim();
            var name = document.getElementById('wsPpeName').value.trim().slice(0, 300);
            var issued = document.getElementById('wsPpeIssued').value;
            var manufactured = document.getElementById('wsPpeManufactured').value;
            var term = document.getElementById('wsPpeTerm').value;
            var comment = document.getElementById('wsPpeComment').value.slice(0, 200);
            var self = this;

            if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Выберите работника'); return; }
            if (!name) { if (typeof KipToast !== 'undefined') KipToast.show('Укажите наименование СИЗ'); return; }

            // Task 443: дата изготовления уходит на сервер (пустая —
            // если не указана); дата окончания считает сервер с
            // ПРИОРИТЕТОМ даты изготовления
            var payload = {
                'таб_номер': tabNo,
                наименование: name,
                дата_выдачи: issued || '',
                дата_изготовления: manufactured || '',
                срок_годности: term || '',
                примечание: comment
            };""",
'8. submitPpeForm — payload')

# --- 6. Карточка: комментарий секции + «изгот.» в мета-строке ----------
rep(
"""            // --- Секция 4: СИЗ — средства индивидуальной защиты
            //     работника (Task 392, лист «СИЗ» табель_КИП_ИОС;
            //     Task 403 — блок ТОЛЬКО страницы «Работники»
            //     (asBlocks): попап шахматки его не показывает).
            //     Каждая запись: наименование, дата выдачи, срок
            //     годности, дата окончания (АВТО: выдача + срок,
            //     «До износа» — без даты), примечание. ✎/✕ —
            //     редакторам и записям с id (строки ручного
            //     заполнения листа без id не правятся — как у
            //     отпусков, Tasks 279/384) ---""",
"""            // --- Секция 4: СИЗ — средства индивидуальной защиты
            //     работника (Task 392, лист «СИЗ» табель_КИП_ИОС;
            //     Task 403 — блок ТОЛЬКО страницы «Работники»
            //     (asBlocks): попап шахматки его не показывает).
            //     Каждая запись: наименование, дата выдачи, дата
            //     изготовления (Task 443 — необязательная; при
            //     наличии дата окончания считается ОТ НЕЁ, дата
            //     выдачи — информационная), срок годности, дата
            //     окончания (АВТО: приоритетная дата + срок, «До
            //     износа» — без даты), примечание. ✎/✕ —
            //     редакторам и записям с id (строки ручного
            //     заполнения листа без id не правятся — как у
            //     отпусков, Tasks 279/384) ---""",
'9. комментарий секции СИЗ')

rep(
"""                    var pMeta = [];
                    pMeta.push(pz.дата_выдачи
                        ? ('выдано ' + this._fmtDateRu(pz.дата_выдачи))
                        : 'не выдано');
                    var pTerm = String(pz.срок_годности || '').trim();""",
"""                    var pMeta = [];
                    pMeta.push(pz.дата_выдачи
                        ? ('выдано ' + this._fmtDateRu(pz.дата_выдачи))
                        : 'не выдано');
                    // Task 443: дата изготовления (необязательная) —
                    // дата окончания на сервере считается ОТ НЕЁ;
                    // показываем сразу после даты выдачи
                    if (pz.дата_изготовления) {
                        pMeta.push('изгот. ' + this._fmtDateRu(pz.дата_изготовления));
                    }
                    var pTerm = String(pz.срок_годности || '').trim();""",
'10. карточка — «изгот.» в мета')

io.open(P, 'w', encoding='utf-8').write(s)
print('\nindex.html: файл записан (%d -> %d байт)' % (len(n0), len(s)))
