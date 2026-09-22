#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 392 (2 части):
#   (1) строка «Общей» вкладки «Работники»: ведущее число ТЕКУЩЕГО
#       момента — БЕЗ СКОБОК: «Работников на текущий момент 12 (2
#       мастера, 5 дневных, 5 сменных).» (заявка: «"(12) (2 мастера…)"
#       — 12 без скобок»);
#   (2) НОВЫЙ РАЗДЕЛ «СИЗ» — средства индивидуальной защиты (лист
#       «СИЗ» файла табель_КИП_ИОС, образец — «Таблица СИЗ работникам
#       КИП ИОС.xlsx», перечень — Приказ Минтруда России от
#       29.10.2021 N767н): карточка работника — секция СИЗ с
#       правкой (✎)/удалением (✕)/добавлением («+ СИЗ…»), дата
#       окончания срока годности считается АВТОМАТИЧЕСКИ (дата
#       выдачи + срок годности). Клиент + сервер (WorkSchedule.gs:
#       listPpe/addPpe/updatePpe/deletePpe; Code.gs: 4 case) +
#       PPEInit.gs (создание листа и предзаполнение перечня).
#
# Все якоря проверяются на единственность (count==1) — при несовпа-
# дении скрипт падает с пояснением, файлы не портит (запись только
# после успешного прогона всех REPL).
import io, sys

def apply(path, repls):
    src = io.open(path, encoding='utf-8').read()
    for i, (old, new, note) in enumerate(repls):
        n = src.count(old)
        if n != 1:
            print('FAIL %s: якорь #%d (%s) найден %d раз' % (path, i + 1, note, n))
            sys.exit(1)
    for (old, new, note) in repls:
        src = src.replace(old, new)
        print('  OK %s: %s' % (path, note))
    io.open(path, 'w', encoding='utf-8').write(src)

# ============================================================
# index.html
# ============================================================
INDEX = 'index.html'

index_repls = []

# --- (1) строка текущего момента: ведущее число БЕЗ СКОБОК ---
index_repls.append((
r'''            // Task 391: ведущее число в скобках — СУММА категорий
            // (сходится с разбивкой в скобках той же строки)
            var totalN = masterN + dayN + shiftN;''',
r'''            // Task 391: ведущее число — СУММА категорий (сходится
            // с разбивкой в скобках той же строки). Task 392: БЕЗ
            // СКОБОК — «Работников на текущий момент 12 (2 мастера,
            // 5 дневных, 5 сменных).» (заявка: «12 без скобок»)
            var totalN = masterN + dayN + shiftN;''',
'комментарий ведущего числа (Task 392: без скобок)'))

index_repls.append((
r'''                       '<span class="ws-workers-count">Работников на текущий момент ' +
                       '(' + totalN + ') (' +''',
r'''                       '<span class="ws-workers-count">Работников на текущий момент ' +
                       totalN + ' (' +''',
'строка текущего момента: totalN БЕЗ СКОБОК'))

# --- (2) CSS: записи СИЗ в карточке + строка авто-даты в шторке ---
index_repls.append((
r'''    [data-theme="light"] .ws-emp-field .ws-emp-k { color: #777; }
    [data-theme="light"] .ws-emp-field .ws-emp-v { color: #222; }
    [data-theme="light"] .ws-emp-empty { color: #999; }
''',
r'''    [data-theme="light"] .ws-emp-field .ws-emp-k { color: #777; }
    [data-theme="light"] .ws-emp-field .ws-emp-v { color: #222; }
    [data-theme="light"] .ws-emp-empty { color: #999; }
    /* Task 392: СИЗ — записи средств индивидуальной защиты в
       карточке работника (лист «СИЗ» табель_КИП_ИОС). Наименование
       бывает длинным («Костюм для защиты от растворов кислот и
       щелочей») — двухстрочная компоновка: имя (переносится),
       под ним мета-строка (выдано / срок / до / примечание);
       кнопки ✎/✕ у редакторов — как у отпусков и мероприятий */
    .ws-ppe-item {
        display: flex;
        align-items: flex-start;
        gap: 6px;
        padding: 4px 10px 4px 8px;
        font-size: 12px;
        line-height: 1.35;
    }
    .ws-ppe-item .ws-ppe-body {
        min-width: 0;
        flex: 1;
    }
    .ws-ppe-name {
        color: var(--text-primary, #e0e0e0);
        font-weight: 600;
        overflow-wrap: break-word;
    }
    .ws-ppe-meta {
        font-size: 10.5px;
        color: var(--text-secondary, rgba(255,255,255,0.55));
        margin-top: 1px;
    }
    [data-theme="light"] .ws-ppe-name { color: #222; }
    [data-theme="light"] .ws-ppe-meta { color: #777; }
    /* Task 392: строка АВТО-даты окончания срока годности в шторке
       СИЗ (дата выдачи + срок; стиль — как .ws-vac-form-info) */
    .ws-ppe-form-info {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary, #e0e0e0);
        padding: 2px 2px 8px;
    }
    [data-theme="light"] .ws-ppe-form-info { color: #333; }
''',
'CSS: .ws-ppe-item/.ws-ppe-name/.ws-ppe-meta/.ws-ppe-form-info'))

# --- (3) HTML: шторка «Новое СИЗ» (после шторки отпуска) ---
index_repls.append((
r'''    <button type="button" class="flow-input-submit" id="wsVacSubmitBtn" onclick="WorkSchedule.submitVacationForm()">Добавить</button>
    <button type="button" class="flow-input-cancel" onclick="WorkSchedule.closeVacationForm()">Отмена</button>
</div>

<script>''',
r'''    <button type="button" class="flow-input-submit" id="wsVacSubmitBtn" onclick="WorkSchedule.submitVacationForm()">Добавить</button>
    <button type="button" class="flow-input-cancel" onclick="WorkSchedule.closeVacationForm()">Отмена</button>
</div>

<!-- ===== Task 392: Bottom sheet — СИЗ работника (workSchedule) =====
     Средства индивидуальной защиты (лист «СИЗ» табель_КИП_ИОС;
     перечень — на основании Приказа Минтруда России от 29.10.2021
     N767н, образец — файл «Таблица СИЗ работникам КИП ИОС.xlsx»).
     «Дата окончания срока годности» НЕ вводится — считается
     автоматически (дата выдачи + срок годности) и показывается
     строкой под полями (wsPpeExpiryInfo). Наименование — ввод со
     списком стандартных позиций (datalist) или свободный текст. -->
<div id="wsPpeOverlay" class="pin-sheet-overlay" onclick="WorkSchedule.closePpeForm()"></div>
<div id="wsPpeSheet" class="flow-input-sheet" style="max-height: 90vh; overflow-y: auto;">
    <div class="flow-input-sheet-handle"></div>
    <!-- режимы: создание («Новое СИЗ» / «Добавить») и правка
         (editPpe → «Правка СИЗ» / «Сохранить») -->
    <div class="flow-input-sheet-title" id="wsPpeSheetTitle">Новое СИЗ</div>
    <div class="flow-input-row">
        <div class="flow-input-group" style="flex:0 0 35%;">
            <label class="flow-input-label" for="wsPpeTabNo">Таб. №</label>
            <select id="wsPpeTabNo" class="flow-input-field-small"></select>
        </div>
        <div class="flow-input-group" style="flex:1 1 65%;">
            <label class="flow-input-label" for="wsPpeName">Наименование СИЗ</label>
            <input type="text" id="wsPpeName" class="flow-input-field-small" list="wsPpeNameList" placeholder="Костюм для защиты от растворов кислот и щелочей" maxlength="300" autocomplete="off">
            <!-- стандартный перечень (образец файла): подсказки
                 ввода, свободный текст не запрещён -->
            <datalist id="wsPpeNameList">
                <option value="Костюм для защиты от растворов кислот и щелочей"></option>
                <option value="Ботинки"></option>
                <option value="Белье нательное"></option>
                <option value="Куртка утеплённая"></option>
                <option value="Каска защитная"></option>
                <option value="Подшлемник"></option>
                <option value="Противогаз"></option>
                <option value="Очки закрытые"></option>
            </datalist>
        </div>
    </div>
    <div class="flow-input-row">
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsPpeIssued">Дата выдачи</label>
            <input type="date" id="wsPpeIssued" class="flow-input-field-small" onchange="WorkSchedule.onPpeFormInput()">
        </div>
        <div class="flow-input-group">
            <label class="flow-input-label" for="wsPpeTerm">Срок годности</label>
            <select id="wsPpeTerm" class="flow-input-field-small" onchange="WorkSchedule.onPpeFormInput()">
                <option value="">— не указан —</option>
                <option value="6 мес.">6 мес.</option>
                <option value="1 год">1 год</option>
                <option value="1,5 года">1,5 года</option>
                <option value="2 года">2 года</option>
                <option value="3 года">3 года</option>
                <option value="До износа">До износа</option>
            </select>
        </div>
    </div>
    <!-- авто-дата окончания: «заполняется автоматически в
         зависимости от даты выдачи плюс срок годности» (образец) -->
    <div class="ws-ppe-form-info" id="wsPpeExpiryInfo">Дата окончания срока годности: —</div>
    <div class="ws-vac-form-hint">Дата окончания срока годности заполняется автоматически: дата выдачи плюс срок годности («До износа» — без даты). Перечень СИЗ — на основании Приказа Минтруда России от 29.10.2021 N767н.</div>
    <textarea id="wsPpeComment" class="flow-comment-field" rows="2" maxlength="200" placeholder="Примечание (необязательно)" autocomplete="off"></textarea>
    <button type="button" class="flow-input-submit" id="wsPpeSubmitBtn" onclick="WorkSchedule.submitPpeForm()">Добавить</button>
    <button type="button" class="flow-input-cancel" onclick="WorkSchedule.closePpeForm()">Отмена</button>
</div>

<script>''',
'HTML: шторка #wsPpeSheet (СИЗ)'))

# --- (4) состояние: _PPE ---
index_repls.append((
r'''        _VACATIONS: [],
        _VAC_PAGE: [],
        _vacYear: null,
''',
r'''        _VACATIONS: [],
        _VAC_PAGE: [],
        _vacYear: null,
        // Task 392: СИЗ — средства индивидуальной защиты работников
        // (лист «СИЗ» табель_КИП_ИОС: наименование, дата выдачи,
        // срок годности, АВТО-дата окончания = выдача + срок,
        // примечание). Грузится в loadGrid вместе со справочниками;
        // карточка работника показывает его записи с правкой (✎),
        // удалением (✕) и добавлением («+ СИЗ…», шторка #wsPpeSheet)
        _PPE: [],
''',
'состояние: _PPE []'))

# --- (5) загрузчик _loadPpe (после _loadVacations) ---
index_repls.append((
r'''                .catch(function() {
                    self._VACATIONS = [];
                    self._VAC_PAGE = [];
                });
        },
''',
r'''                .catch(function() {
                    self._VACATIONS = [];
                    self._VAC_PAGE = [];
                });
        },

        // Task 392: СИЗ работников (лист «СИЗ» табель_КИП_ИОС) —
        // единый список (не по годам/месяцам: карточка показывает
        // всё выданное). Ошибка (лист/эндпоинт ещё нет — до
        // серверного деплоя) НЕ ломает шахматку: пустой список
        _loadPpe: function() {
            var self = this;
            return this._api('workSchedule.listPpe', {})
                .then(function(data) {
                    self._PPE = data.ppe || [];
                })
                .catch(function() {
                    self._PPE = [];
                });
        },
''',
'загрузчик _loadPpe (с catch)'))

# --- (6) loadGrid: _loadPpe в Promise.all ---
index_repls.append((
r'''                // Task 274: план отпусков — с собственным catch, сбой
                // не блокирует рендер сетки
                this._loadVacations()
            ]).then(function() {''',
r'''                // Task 274: план отпусков — с собственным catch, сбой
                // не блокирует рендер сетки
                this._loadVacations(),
                // Task 392: СИЗ — с собственным catch, сбой не
                // блокирует рендер сетки
                this._loadPpe()
            ]).then(function() {''',
'loadGrid: _loadPpe() в Promise.all'))

# --- (7) кэш: восстановление _PPE ---
index_repls.append((
r'''            this._VACATIONS = vacs;
            this._VAC_PAGE = vacs;
            this._vacYear = this._year;''',
r'''            this._VACATIONS = vacs;
            this._VAC_PAGE = vacs;
            this._vacYear = this._year;
            // Task 392: СИЗ — в кэше прошлых версий поля ppe могло
            // не быть (до Task 392) — пустой список, до серверного
            // деплоя он и будет пустым
            this._PPE = Array.isArray(c.ppe) ? c.ppe : [];''',
'кэш: восстановление _PPE (c.ppe)'))

# --- (8) кэш: запись c.ppe ---
index_repls.append((
r'''                if (!c.vacations || typeof c.vacations !== 'object') c.vacations = {};
                c.vacations[String(this._year)] = this._VACATIONS;''',
r'''                if (!c.vacations || typeof c.vacations !== 'object') c.vacations = {};
                c.vacations[String(this._year)] = this._VACATIONS;
                // Task 392: СИЗ — единый список (не по годам)
                c.ppe = this._PPE;''',
'кэш: запись c.ppe'))

# --- (9) карточка работника: секция СИЗ (после «+ Мероприятие…») ---
index_repls.append((
r'''            if (withEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addtr"' +
                        ' title="Добавить мероприятие этому работнику"' +
                        ' onclick="WorkSchedule.onEmpAddTraining(\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\')">+ Мероприятие…</div>';
            }
            return html;
        },''',
r'''            if (withEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addtr"' +
                        ' title="Добавить мероприятие этому работнику"' +
                        ' onclick="WorkSchedule.onEmpAddTraining(\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\')">+ Мероприятие…</div>';
            }

            // --- Секция 4: СИЗ — средства индивидуальной защиты
            //     работника (Task 392, лист «СИЗ» табель_КИП_ИОС).
            //     Каждая запись: наименование, дата выдачи, срок
            //     годности, дата окончания (АВТО: выдача + срок,
            //     «До износа» — без даты), примечание. ✎/✕ —
            //     редакторам и записям с id (строки ручного
            //     заполнения листа без id не правятся — как у
            //     отпусков, Tasks 279/384) ---
            var ppes = [];
            for (var ppi = 0; ppi < (this._PPE || []).length; ppi++) {
                if (this._PPE[ppi]['таб_номер'] === tabNo) ppes.push(this._PPE[ppi]);
            }
            html += '<div class="ws-popup-sec">СИЗ · средства индивидуальной защиты</div>';
            if (!ppes.length) {
                html += '<div class="ws-emp-empty">нет выданных СИЗ</div>';
            } else {
                for (var pk = 0; pk < ppes.length; pk++) {
                    var pz = ppes[pk];
                    var pId = parseInt(pz.id, 10);
                    var pActs = '';
                    if (withEdit && pId) {
                        pActs = '<span class="ws-popup-act" title="Редактировать запись СИЗ"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.editPpe(' + pId + ')">✎</span>' +
                                '<span class="ws-popup-act ws-popup-act-del" title="Удалить запись СИЗ"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.deletePpe(' + pId + ')">✕</span>';
                    }
                    var pMeta = [];
                    pMeta.push(pz.дата_выдачи
                        ? ('выдано ' + this._fmtDateRu(pz.дата_выдачи))
                        : 'не выдано');
                    var pTerm = String(pz.срок_годности || '').trim();
                    if (pTerm) pMeta.push('срок ' + pTerm);
                    var pExp = String(pz.дата_окончания || '').trim();
                    if (pExp && pExp !== 'До износа') {
                        pMeta.push('до ' + this._fmtDateRu(pExp));
                    }
                    if (String(pz.примечание || '').trim()) {
                        pMeta.push('«' + this._esc(String(pz.примечание).trim()) + '»');
                    }
                    html += '<div class="ws-ppe-item">' +
                            '<div class="ws-ppe-body">' +
                            '<div class="ws-ppe-name">' +
                            this._esc(String(pz.наименование || '')) + '</div>' +
                            '<div class="ws-ppe-meta">' + pMeta.join(' · ') + '</div>' +
                            '</div>' + pActs + '</div>';
                }
            }
            // «+ СИЗ…» — шторка «Новое СИЗ» с УЖЕ ВЫБРАННЫМ
            // работником карточки (как «+ Отпуск…»/«+ Мероприятие…»,
            // Tasks 312/384). Двойная защита — в openPpeForm
            if (withEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addppe"' +
                        ' title="Добавить СИЗ этому работнику"' +
                        ' onclick="WorkSchedule.onEmpAddPpe(\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\')">+ СИЗ…</div>';
            }
            return html;
        },''',
'карточка: секция СИЗ + «+ СИЗ…»'))

# --- (10) JS-функции СИЗ (после _doDeleteVacation) ---
index_repls.append((
r'''        _doDeleteVacation: function(id) {
            var self = this;
            this._api('workSchedule.deleteVacation', { id: id })
                .then(function() {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Период отпуска удалён. Пересформируйте шахматку, чтобы снять «О»');
                    }
                    // Task 309: регресс-фикс Task 308 — удалённый
                    // loadVacations() (страница «Отпуска») заменили на
                    // loadGrid(): перезагружаются и план «ОТ», и сетка
                    self.loadGrid(true);
                })
                .catch(function(err) {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Ошибка: ' + self._apiErrText(err));
                    }
                });
        },
''',
r'''        _doDeleteVacation: function(id) {
            var self = this;
            this._api('workSchedule.deleteVacation', { id: id })
                .then(function() {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Период отпуска удалён. Пересформируйте шахматку, чтобы снять «О»');
                    }
                    // Task 309: регресс-фикс Task 308 — удалённый
                    // loadVacations() (страница «Отпуска») заменили на
                    // loadGrid(): перезагружаются и план «ОТ», и сетка
                    self.loadGrid(true);
                })
                .catch(function(err) {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Ошибка: ' + self._apiErrText(err));
                    }
                });
        },

        // ============================================================
        // Task 392: СИЗ — средства индивидуальной защиты работника
        // (лист «СИЗ» табель_КИП_ИОС). Карточка работника: секция с
        // записями, ✎/✕, «+ СИЗ…»; шторка #wsPpeSheet; сервер —
        // workSchedule.listPpe/addPpe/updatePpe/deletePpe
        // ============================================================

        // «+ СИЗ…» из карточки работника — шторка с ПРЕФИЛЛОМ
        // сотрудника (как «+ Отпуск…»/«+ Мероприятие…»): карточка
        // закрывается (z-уровень попапа выше шторки)
        onEmpAddPpe: function(tabNo) {
            this.closeEmpPopup();
            this.openPpeForm(tabNo);
        },

        // правка записи СИЗ из карточки (кнопка ✎): запись ищется в
        // _PPE по id, шторка открывается в режиме ПРАВКИ (2-й
        // аргумент openPpeForm — как editVacation/editTraining)
        editPpe: function(id) {
            if (!this._canEdit) return;
            var pid = parseInt(id, 10);
            var rec = null;
            for (var i = 0; i < (this._PPE || []).length; i++) {
                if (parseInt(this._PPE[i].id, 10) === pid) {
                    rec = this._PPE[i];
                    break;
                }
            }
            if (!rec) {
                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('Запись СИЗ не найдена — обновите график');
                }
                return;
            }
            this.closeCellPopup();
            this.closeEmpPopup();
            this.openPpeForm(rec['таб_номер'], rec);
        },

        // шторка «Новое СИЗ» / «Правка СИЗ». tabNo (необяз.) —
        // префилл работника из карточки; editPpe (необяз.) — запись
        // из _PPE: режим ПРАВКИ (id в _ppeEditId, submit уходит в
        // updatePpe). Дата окончания НЕ вводится — считается
        // автоматически (дата выдачи + срок годности) и показывается
        // строкой под полями (onPpeFormInput → wsPpeExpiryInfo)
        openPpeForm: function(tabNo, editPpe) {
            if (!this._canEdit) return;
            var sheetTitle = document.getElementById('wsPpeSheetTitle');
            var submitBtn = document.getElementById('wsPpeSubmitBtn');
            var empSel = document.getElementById('wsPpeTabNo');
            if (empSel) {
                var html = '<option value="">— выберите —</option>';
                for (var i = 0; i < this._EMPLOYEES.length; i++) {
                    html += '<option value="' + this._esc(this._EMPLOYEES[i]['таб_номер']) + '">' +
                            this._esc(this._EMPLOYEES[i]['таб_номер']) + ' — ' +
                            this._esc(this._EMPLOYEES[i]['ФИО']) + '</option>';
                }
                empSel.innerHTML = html;
                if (tabNo !== undefined && tabNo !== null && String(tabNo) !== '') {
                    empSel.value = String(tabNo);
                }
            }
            // список сроков: стандартный набор; в режиме ПРАВКИ
            // незнакомый срок записи (ручная строка листа) добавляется
            // опцией — значение не теряется при открытии шторки
            var termSel = document.getElementById('wsPpeTerm');
            if (termSel) {
                var terms = ['', '6 мес.', '1 год', '1,5 года', '2 года', '3 года', 'До износа'];
                var curTerm = editPpe ? String(editPpe.срок_годности || '').trim() : '';
                if (curTerm && terms.indexOf(curTerm) === -1) terms.push(curTerm);
                var tHtml = '';
                for (var ti2 = 0; ti2 < terms.length; ti2++) {
                    tHtml += '<option value="' + this._escAttr(terms[ti2]) + '">' +
                             (terms[ti2] === '' ? '— не указан —' : this._esc(terms[ti2])) +
                             '</option>';
                }
                termSel.innerHTML = tHtml;
                termSel.value = curTerm;
            }
            this._ppeEditId = null;
            if (editPpe && editPpe.id) {
                this._ppeEditId = parseInt(editPpe.id, 10);
                if (empSel) empSel.value = String(editPpe['таб_номер'] || '');
                document.getElementById('wsPpeName').value =
                    String(editPpe.наименование || '');
                document.getElementById('wsPpeIssued').value =
                    String(editPpe.дата_выдачи || '');
                document.getElementById('wsPpeComment').value =
                    String(editPpe.примечание || '');
                if (sheetTitle) sheetTitle.textContent = 'Правка СИЗ';
                if (submitBtn) submitBtn.textContent = 'Сохранить';
            } else {
                document.getElementById('wsPpeName').value = '';
                document.getElementById('wsPpeIssued').value = '';
                document.getElementById('wsPpeComment').value = '';
                if (sheetTitle) sheetTitle.textContent = 'Новое СИЗ';
                if (submitBtn) submitBtn.textContent = 'Добавить';
            }
            this.onPpeFormInput();

            document.getElementById('wsPpeOverlay').classList.add('active');
            document.getElementById('wsPpeSheet').classList.add('active');
            setTimeout(function() {
                var f = document.getElementById('wsPpeName');
                if (f && f.focus) f.focus();
            }, 350);
        },

        closePpeForm: function() {
            document.getElementById('wsPpeOverlay').classList.remove('active');
            document.getElementById('wsPpeSheet').classList.remove('active');
            // сброс режима правки (следующее открытие — создание)
            this._ppeEditId = null;
        },

        // срок годности текстом → месяцы (образец «Таблица СИЗ»):
        // «1 год» → 12, «1,5 года» → 18, «2 года» → 24, «3 года» →
        // 36, «6 мес.» → 6; «До износа» → маркер -1; незнакомый
        // или пустой → null (дата окончания не считается)
        _ppeTermMonths: function(term) {
            var s = String(term || '').trim().toLowerCase()
                .replace(',', '.').replace(/\u00a0/g, ' ');
            if (!s) return null;
            if (s.indexOf('до износа') !== -1) return -1;
            var m = s.match(/^(\d+(?:\.\d+)?)\s*(мес|год|л)/);
            if (!m) return null;
            var n = parseFloat(m[1]);
            if (isNaN(n) || n <= 0) return null;
            if (m[2] === 'мес') {
                var mo = Math.round(n);
                return (mo >= 1 && mo <= 120) ? mo : null;
            }
            var mm = Math.round(n * 12);
            return (mm >= 1 && mm <= 600) ? mm : null;
        },

        // дата окончания срока годности = дата выдачи + срок
        // (кламп дня к длине целевого месяца: 31.08 + 6 мес →
        // 28/29.02, не «3 марта»); «До износа» → строка «До
        // износа»; без даты/срока (или срок не распознан) → null
        _ppeExpiry: function(isoIssued, term) {
            var months = this._ppeTermMonths(term);
            if (months === -1) return 'До износа';
            if (!months) return null;
            var d = this._parseIsoLocal(String(isoIssued || ''));
            if (!d) return null;
            var y = d.getFullYear();
            var mo = d.getMonth() + months;
            var day = d.getDate();
            var last = new Date(y, mo + 1, 0).getDate();
            if (day > last) day = last;
            return this._isoDate(new Date(y, mo, day));
        },

        // подсказка авто-даты окончания в шторке СИЗ — на каждое
        // изменение даты выдачи/срока (onchange/oninput полей)
        onPpeFormInput: function() {
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
        },

        submitPpeForm: function() {
            var tabNo = document.getElementById('wsPpeTabNo').value.trim();
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
            };

            // режим ПРАВКИ — запись обновляется на месте
            // (updatePpe по id); шторка закрывается только при
            // успехе — при ошибке поля сохранены для повтора
            if (this._ppeEditId) {
                var editPpeId = this._ppeEditId;
                payload.id = editPpeId;
                this._api('workSchedule.updatePpe', payload).then(function() {
                    self._ppeEditId = null;
                    self.closePpeForm();
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Запись СИЗ обновлена');
                    }
                    self.loadGrid(true);
                }).catch(function(err) {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Ошибка: ' + self._apiErrText(err));
                    }
                });
                return;
            }

            this._api('workSchedule.addPpe', payload).then(function() {
                self.closePpeForm();
                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('СИЗ добавлено работнику');
                }
                // карточка перерисуется вместе с сеткой
                // (_renderWorkersIfOpen) — новая запись видна сразу
                self.loadGrid(true);
            }).catch(function(err) {
                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('Ошибка: ' + self._apiErrText(err));
                }
            });
        },

        deletePpe: function(id) {
            if (!this._canEdit) return;
            // карточка по z-уровню выше шторок — закрываем попапы ДО
            // диалога подтверждения (как deleteVacation/deleteTraining)
            this.closeCellPopup();
            this.closeEmpPopup();
            var self = this;
            if (typeof kipConfirm === 'function') {
                kipConfirm('Удалить запись СИЗ id=' + id + '?', { danger: true })
                    .then(function(ok) { if (ok) self._doDeletePpe(id); });
            } else {
                if (confirm('Удалить запись СИЗ id=' + id + '?')) self._doDeletePpe(id);
            }
        },

        _doDeletePpe: function(id) {
            var self = this;
            this._api('workSchedule.deletePpe', { id: id })
                .then(function() {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Запись СИЗ удалена');
                    }
                    self.loadGrid(true);
                })
                .catch(function(err) {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Ошибка: ' + self._apiErrText(err));
                    }
                });
        },
''',
'JS: функции СИЗ (шторка/правка/удаление/сроки)'))

# ============================================================
# scripts/WorkSchedule.gs
# ============================================================
WS = 'scripts/WorkSchedule.gs'

ws_repls = []

ws_repls.append((
r'''//   workSchedule.deleteVacation   — удалить период отпуска
//''',
r'''//   workSchedule.deleteVacation   — удалить период отпуска
//   workSchedule.listPpe          — СИЗ работников (Task 392, лист «СИЗ»)
//   workSchedule.addPpe           — выдать СИЗ работнику (дата окончания
//                                   считается автоматически: выдача + срок)
//   workSchedule.updatePpe        — правка записи СИЗ (B..I по id)
//   workSchedule.deletePpe        — удалить запись СИЗ
//''',
'шапка: эндпоинты СИЗ'))

ws_repls.append((
r'''// Листы (9):
//   README, Сотрудники, Коды_статусов, Шаблоны_ротации,
//   Дни_цикла, Инструктажи, Записи_графика, Сводка_по_месяцам,
//   Отпуска (Task 274)''',
r'''// Листы (10):
//   README, Сотрудники, Коды_статусов, Шаблоны_ротации,
//   Дни_цикла, Инструктажи, Записи_графика, Сводка_по_месяцам,
//   Отпуска (Task 274), СИЗ (Task 392)''',
'шапка: листы (10) + СИЗ'))

ws_repls.append((
r'''//   приоритет статуса дня — ручная правка > отпуск > плановая смена >
//   мероприятие (И/ОБ/ПЗ — только на день БЕЗ плановой смены).
//   Task 303: мероприятие больше НЕ затирает плановую смену — на
//   сменных днях смена остаётся кодом ячейки, а мероприятие (И/ОБ/ПЗ)
//   показывается бейджем на клиенте (данные — лист «Инструктажи»,
//   связка — колонка I «инструкция»).
// ============================================================''',
r'''//   приоритет статуса дня — ручная правка > отпуск > плановая смена >
//   мероприятие (И/ОБ/ПЗ — только на день БЕЗ плановой смены).
//   Task 303: мероприятие больше НЕ затирает плановую смену — на
//   сменных днях смена остаётся кодом ячейки, а мероприятие (И/ОБ/ПЗ)
//   показывается бейджем на клиенте (данные — лист «Инструктажи»,
//   связка — колонка I «инструкция»).
//
// Структура листа «СИЗ» (Task 392 — средства индивидуальной защиты;
//   перечень — Приказ Минтруда России от 29.10.2021 N767н, образец —
//   файл «Таблица СИЗ работникам КИП ИОС.xlsx»; создаёт PPEInit.gs):
//   A: id (auto-increment)
//   B: таб_номер (FK на Сотрудники; ТЕКСТ — Task 304)
//   C: работник (ФИО — копия для читаемости листа; заполняется
//      приложением из справочника «Сотрудники»)
//   D: должность (копия для читаемости листа; автоматически)
//   E: наименование_СИЗ
//   F: дата_выдачи (Date; может быть пусто — не выдано)
//   G: срок_годности («1 год» / «1,5 года» / «2 года» / «3 года» /
//      «6 мес.» / «До износа» / пусто)
//   H: дата_окончания (заполняется АВТОМАТИЧЕСКИ: дата выдачи +
//      срок годности; «До износа» для соответствующего срока; без
//      даты выдачи — пусто)
//   I: примечание
// ============================================================''',
'шапка: структура листа «СИЗ»'))

ws_repls.append((
r'''  VACATIONS_SHEET:    'Отпуска',
''',
r'''  VACATIONS_SHEET:    'Отпуска',
  // Task 392: лист «СИЗ» — средства индивидуальной защиты работников
  // (наименование/дата выдачи/срок/авто-дата окончания/примечание)
  PPE_SHEET:          'СИЗ',
''',
'константа PPE_SHEET'))

ws_repls.append((
r'''    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) {
      if (parseInt(ids[i][0], 10) === id) {
        sheet.deleteRow(i + 2);
        try {
          Utils.audit(user.email, 'WORKSCHEDULE_DELETE_VACATION', '', '',
            'Удалён отпуск id=' + id);
        } catch (e) { /* ignore */ }
        return { ok: true, data: { id: id } };
      }
    }
    return { ok: false, error: 'not_found' };
  }

};''',
r'''    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) {
      if (parseInt(ids[i][0], 10) === id) {
        sheet.deleteRow(i + 2);
        try {
          Utils.audit(user.email, 'WORKSCHEDULE_DELETE_VACATION', '', '',
            'Удалён отпуск id=' + id);
        } catch (e) { /* ignore */ }
        return { ok: true, data: { id: id } };
      }
    }
    return { ok: false, error: 'not_found' };
  },

  // ============================================================
  // CRUD СИЗ (Task 392 — лист «СИЗ»)
  // ============================================================

  // workSchedule.listPpe
  // payload: { token }
  // returns: { ok:true, data: { ppe: [...] } }
  // Все записи СИЗ (клиент фильтрует по таб_номеру для карточки
  // работника). Строка без таб_номера И наименования — пустая
  // (стилевой холст getLastRow, урок Task 294) — пропускается.
  // Даты могут лежать текстом — парсим _parseSheetDate (урок
  // Task 279); дата_окончания «До износа» остаётся СТРОКОЙ.
  listPpe: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { ppe: [] } };

    // Читаем id (A), таб_номер (B), работник (C), должность (D),
    // наименование (E), дата_выдачи (F), срок (G), дата_окончания
    // (H), примечание (I)
    var values = sheet.getRange(2, 1, lastRow - 1, 9).getValues();
    var ppe = [];
    for (var i = 0; i < values.length; i++) {
      var r = values[i];
      var tabNo = String(r[1] || '').trim();
      var name = String(r[4] || '').trim();
      if (!tabNo && !name) continue;
      var vId = parseInt(r[0], 10);
      var issued = this._parseSheetDate(r[5]);
      var expRaw = r[7];
      var expiry = '';
      if (expRaw instanceof Date) {
        expiry = this._toIsoDate(expRaw);
      } else if (String(expRaw || '').trim()) {
        var expDate = this._parseSheetDate(expRaw);
        expiry = expDate ? this._toIsoDate(expDate) : String(expRaw).trim();
      }
      ppe.push({
        id:              isNaN(vId) ? null : vId,
        'таб_номер':     tabNo,
        работник:        String(r[2] || '').trim(),
        должность:       String(r[3] || '').trim(),
        наименование:    name,
        дата_выдачи:     issued ? this._toIsoDate(issued) : '',
        срок_годности:   String(r[6] || '').trim(),
        дата_окончания:  expiry,
        примечание:      String(r[8] || '').trim()
      });
    }
    return { ok: true, data: { ppe: ppe } };
  },

  // Task 392: работник по таб. № в листе «Сотрудники» — для колонок-
  // копий C/D листа «СИЗ» (работник/должность для читаемости листа).
  // null — таб. № в справочнике не найден
  _ppeLookupEmployee: function(empSheet, tabNo) {
    var lastRow = empSheet.getLastRow();
    if (lastRow < 2) return null;
    var tabs = empSheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < tabs.length; i++) {
      if (String(tabs[i][0]).trim() !== tabNo) continue;
      var vals = empSheet.getRange(i + 2, 1, 1, 11).getValues();
      return {
        fio:      String(vals[0][1] || '').trim(),
        position: String(vals[0][9] || '').trim()
      };
    }
    return null;
  },

  // Task 392: срок годности текстом → месяцы («1 год» → 12,
  // «1,5 года» → 18, «2 года» → 24, «3 года» → 36, «6 мес.» → 6);
  // «До износа» → маркер -1; незнакомый/пустой → null
  _ppeTermMonths: function(term) {
    var s = String(term || '').trim().toLowerCase()
      .replace(',', '.').replace(/\u00a0/g, ' ');
    if (!s) return null;
    if (s.indexOf('до износа') !== -1) return -1;
    var m = s.match(/^(\d+(?:\.\d+)?)\s*(мес|год|л)/);
    if (!m) return null;
    var n = parseFloat(m[1]);
    if (isNaN(n) || n <= 0) return null;
    if (m[2] === 'мес') {
      var mo = Math.round(n);
      return (mo >= 1 && mo <= 120) ? mo : null;
    }
    var mm = Math.round(n * 12);
    return (mm >= 1 && mm <= 600) ? mm : null;
  },

  // Task 392: дата окончания срока годности = дата выдачи + срок
  // (кламп дня к длине целевого месяца: 31.08 + 6 мес → 28/29.02).
  // «До износа» → строка «До износа»; без даты/срока → null
  _ppeExpiry: function(issueDate, term) {
    var months = this._ppeTermMonths(term);
    if (months === -1) return 'До износа';
    if (!months || !issueDate) return null;
    var y = issueDate.getFullYear();
    var mo = issueDate.getMonth() + months;
    var day = issueDate.getDate();
    var last = new Date(y, mo + 1, 0).getDate();
    if (day > last) day = last;
    return new Date(y, mo, day);
  },

  // workSchedule.addPpe
  // payload: { token, таб_номер, наименование, дата_выдачи(ISO|''),
  //            срок_годности, примечание }
  // Добавляет запись СИЗ работнику. Работник/должность (C/D) — копия
  // из справочника «Сотрудники» (для читаемости листа). Дата
  // окончания (H) считается АВТОМАТИЧЕСКИ: дата выдачи + срок
  // годности; «До износа» → текст «До износа»; без даты выдачи —
  // пусто (образец файла «Таблица СИЗ работникам КИП ИОС»).
  addPpe: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };
    var name = String(payload.наименование || '').trim().slice(0, 300);
    if (!name) return { ok: false, error: 'invalid_наименование' };

    var empSheet = this._getSheet(this.EMPLOYEES_SHEET);
    if (!empSheet) return { ok: false, error: 'sheet_not_found: ' + this.EMPLOYEES_SHEET };
    var emp = this._ppeLookupEmployee(empSheet, tabNo);
    if (!emp) {
      return { ok: false, error: 'not_found_таб_номер',
               message: 'Работник с таб. № ' + tabNo + ' не найден' };
    }

    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };

    var issued = payload.дата_выдачи ? this._parseIsoDate(payload.дата_выдачи) : null;
    var term = String(payload.срок_годности || '').trim().slice(0, 50);
    var comment = String(payload.примечание || '').slice(0, 200);
    var expiry = this._ppeExpiry(issued, term);  // Date|'До износа'|null

    // max id в столбце A
    var lastRow = sheet.getLastRow();
    var maxId = 0;
    if (lastRow >= 2) {
      var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) {
        var v = parseInt(ids[i][0], 10);
        if (!isNaN(v) && v > maxId) maxId = v;
      }
    }
    var newId = maxId + 1;

    // Task 304: B (таб_№) — текст, ведущие нули не теряются
    this._appendRowKeepText(sheet,
      [newId, tabNo, emp.fio, emp.position, name, issued, term, expiry, comment],
      [2]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_ADD_PPE', '', '',
        'Добавлено СИЗ id=' + newId + ' таб_номер=' + tabNo +
        ' «' + name + '»' +
        (issued ? ' выдано ' + this._toIsoDate(issued) : ''));
    } catch (e) { /* ignore */ }

    return { ok: true, data: { id: newId } };
  },

  // workSchedule.updatePpe
  // payload: { token, id, таб_номер, наименование, дата_выдачи(ISO|''),
  //            срок_годности, примечание }
  // Правка записи СИЗ из карточки работника (шторка «Правка СИЗ»).
  // Обновляет B..I строки по id (A не меняется); работник/должность
  // (C/D) освежаются из справочника «Сотрудники»; дата окончания
  // (H) пересчитывается. Task 304: B (таб_номер) — текстовый формат.
  updatePpe: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var id = parseInt(payload.id, 10);
    if (isNaN(id)) return { ok: false, error: 'invalid_id' };
    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };
    var name = String(payload.наименование || '').trim().slice(0, 300);
    if (!name) return { ok: false, error: 'invalid_наименование' };

    var empSheet = this._getSheet(this.EMPLOYEES_SHEET);
    if (!empSheet) return { ok: false, error: 'sheet_not_found: ' + this.EMPLOYEES_SHEET };
    var emp = this._ppeLookupEmployee(empSheet, tabNo);
    if (!emp) {
      return { ok: false, error: 'not_found_таб_номер',
               message: 'Работник с таб. № ' + tabNo + ' не найден' };
    }

    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'not_found' };

    // Строка по id (A)
    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    var rowIndex = -1;
    for (var fi = 0; fi < ids.length; fi++) {
      if (parseInt(ids[fi][0], 10) === id) { rowIndex = fi + 2; break; }
    }
    if (rowIndex === -1) return { ok: false, error: 'not_found' };

    var issued = payload.дата_выдачи ? this._parseIsoDate(payload.дата_выдачи) : null;
    var term = String(payload.срок_годности || '').trim().slice(0, 50);
    var comment = String(payload.примечание || '').slice(0, 200);
    var expiry = this._ppeExpiry(issued, term);

    // Запись B..I (id в A не меняется); Task 304: B — текст
    sheet.getRange(rowIndex, 2).setNumberFormat('@');
    sheet.getRange(rowIndex, 2, 1, 8).setValues(
      [[tabNo, emp.fio, emp.position, name, issued, term, expiry, comment]]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_UPDATE_PPE', '', '',
        'Обновлено СИЗ id=' + id + ' таб_номер=' + tabNo + ' «' + name + '»');
    } catch (e) { /* ignore */ }

    return { ok: true, data: { id: id } };
  },

  // workSchedule.deletePpe
  // payload: { token, id }
  deletePpe: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var id = parseInt(payload.id, 10);
    if (isNaN(id)) return { ok: false, error: 'invalid_id' };

    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'not_found' };

    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) {
      if (parseInt(ids[i][0], 10) === id) {
        sheet.deleteRow(i + 2);
        try {
          Utils.audit(user.email, 'WORKSCHEDULE_DELETE_PPE', '', '',
            'Удалено СИЗ id=' + id);
        } catch (e) { /* ignore */ }
        return { ok: true, data: { id: id } };
      }
    }
    return { ok: false, error: 'not_found' };
  }

};''',
'методы СИЗ: listPpe/addPpe/updatePpe/deletePpe + хелперы'))

# ============================================================
# scripts/Code.gs
# ============================================================
CODE = 'scripts/Code.gs'

code_repls = []

code_repls.append((
r'''      // Task 384: правка периода отпуска (B..F по id; проверки
      // пересечения/дубля части не считают саму строку)
      case 'workSchedule.updateVacation':
        return _json(WorkSchedule.updateVacation(payload));

      default:''',
r'''      // Task 384: правка периода отпуска (B..F по id; проверки
      // пересечения/дубля части не считают саму строку)
      case 'workSchedule.updateVacation':
        return _json(WorkSchedule.updateVacation(payload));

      // Task 392: СИЗ — средства индивидуальной защиты работников
      // (лист «СИЗ» таблицы табель_КИП_ИОС); карточка работника:
      // секция СИЗ с правкой/добавлением/удалением записей
      case 'workSchedule.listPpe':
        return _json(WorkSchedule.listPpe(payload));

      case 'workSchedule.addPpe':
        return _json(WorkSchedule.addPpe(payload));

      case 'workSchedule.updatePpe':
        return _json(WorkSchedule.updatePpe(payload));

      case 'workSchedule.deletePpe':
        return _json(WorkSchedule.deletePpe(payload));

      default:''',
'Code.gs: 4 case СИЗ'))

# ============================================================
# PPEInit.gs — новый файл (создание листа «СИЗ» + предзаполнение)
# ============================================================
PPE_INIT = r'''// ============================================================
// PPEInit.gs — создание листа «СИЗ» в таблице «График работы»
// (файл табель_КИП_ИОС) и предзаполнение перечня СИЗ (Task 392)
// ============================================================
// НАЗНАЧЕНИЕ:
//   Разовый инструмент деплоя Task 392 (см. scripts/DEPLOY-Task392):
//   создаёт лист «СИЗ» со структурой, которую читает/пишет
//   WorkSchedule.gs (listPpe/addPpe/updatePpe/deletePpe — секция
//   СИЗ в карточке работника), и по желанию заполняет СТАНДАРТНЫЙ
//   перечень СИЗ для каждого активного работника справочника
//   «Сотрудники» (образец — файл «Таблица СИЗ работникам КИП
//   ИОС.xlsx»; перечень — на основании Приказа Минтруда России от
//   29.10.2021 N767н).
//
// ИСПОЛЬЗОВАНИЕ:
//   1. Открыть редактор Apps Script (проект развёртывания
//      AKfycbyt… — тот же, где Code.gs и WorkSchedule.gs)
//   2. + → Создать файл «PPEInit.gs», вставить содержимое ЦЕЛИКОМ
//   3. В выпадающем списке функций выбрать нужную и нажать ▶ Run
//      (первый запуск попросит авторизацию — разрешить)
//   4. Результат смотреть в журнале (Ctrl+Enter / «Выполнения»)
//   5. После завершения деплоя файл можно удалить из проекта
//      (код приложения его НЕ использует — это разовый инструмент)
//
// ФУНКЦИИ (каждая запускается отдельно):
//   ppeDeployAll()       — рекомендованный порядок: создать лист +
//                          предзаполнить стандартный перечень всем
//                          активным работникам. Запустить ОДИН раз.
//   ppeCreateSheet()     — ШАГ 1: создать лист «СИЗ» с заголовками
//                          (существующий лист НЕ трогается).
//   ppePrefillStandard() — ШАГ 2: каждому АКТИВНОМУ работнику
//                          («Сотрудники», в_архиве=0), у которого
//                          ещё нет строк СИЗ, добавить стандартный
//                          перечень из 8 позиций (даты выдачи
//                          пустые — заполняются приложением при
//                          выдаче; «Очки закрытые» — «До износа»).
//   ppeStatus()          — диагностика: наличие листа, заголовки,
//                          число строк, последний id, покрытие
//                          работников. Ничего не меняет.
//
// БЕЗОПАСНОСТЬ:
//   - Существующий лист «СИЗ» НИКОГДА не перезаписывается
//     (ppeCreateSheet пропускает шаг, если лист уже есть).
//   - ppePrefillStandard НЕ дублирует: работник, у которого уже
//     есть строки СИЗ, пропускается (повторный запуск безопасен).
//   - Остальные листы не пишутся; читается только «Сотрудники»
//     (и «СИЗ» — для диагностики/проверки дублей).
//   - Приложение работает и БЕЗ листа (до его создания): секция
//     СИЗ в карточках показывает «нет выданных СИЗ», кнопки
//     добавления вернут понятную ошибку sheet_not_found в тосте.
// ============================================================

// Целевая таблица — «График работы» (тот же ID, что в
// WorkSchedule.gs; скрипт открывает её по ID явно, чтобы
// исключить запись «не в ту таблицу»).
var PPE_SPREADSHEET_ID = '1MQtW-CWCmjlu-SAeVBllKDP6NRkiOkmW-7xgOjHskWY';

var PPE_SHEET_NAME = 'СИЗ';
var PPE_HEADERS    = ['id', 'таб_номер', 'работник', 'должность',
                      'наименование_СИЗ', 'дата_выдачи', 'срок_годности',
                      'дата_окончания', 'примечание'];
var PPE_EMPLOYEES_SHEET = 'Сотрудники';

// Цвет шапки — как у листа «Коды_статусов» (StatusCodesInit.gs):
// тёмный, белый текст — единый вид таблицы
var PPE_HEADER_BG = '#1F4E5F';

// Стандартный перечень СИЗ цеха №8 (образец файла «Таблица СИЗ
// работникам КИП ИОС.xlsx»; Приказ Минтруда России от 29.10.2021
// N767н). срок_годности/примечание — как в образце; дата_выдачи
// пустая (заполнится приложением при фактической выдаче).
// «Очки закрытые»: срок «До износа» → дата_окончания «До износа».
var PPE_STANDARD = [
  { name: 'Костюм для защиты от растворов кислот и щелочей',
    term: '1 год',   note: '' },
  { name: 'Ботинки',                                term: '1,5 года', note: '' },
  { name: 'Белье нательное',                        term: '',         note: '' },
  { name: 'Куртка утеплённая',                      term: '2 года',   note: 'До износа' },
  { name: 'Каска защитная',                         term: '2 года',   note: 'До износа' },
  { name: 'Подшлемник',                             term: '',         note: '' },
  { name: 'Противогаз',                             term: '',         note: '' },
  { name: 'Очки закрытые',                          term: 'До износа', note: '' }
];

function ppeDeployAll() {
  var created = ppeCreateSheet();
  var pre = ppePrefillStandard();
  Logger.log('PPEInit: лист=%s, предзаполнено работников=%s, строк добавлено=%s',
    created ? 'создан' : 'уже был', pre.workers, pre.rows);
}

// ШАГ 1: создать лист «СИЗ» с заголовками. Лист уже есть —
// ничего не меняет (возвращает false). Заголовок — строка 1.
function ppeCreateSheet() {
  var ss = SpreadsheetApp.openById(PPE_SPREADSHEET_ID);
  var sheet = ss.getSheetByName(PPE_SHEET_NAME);
  if (sheet) {
    Logger.log('PPEInit: лист «%s» уже существует — не трогаю', PPE_SHEET_NAME);
    return false;
  }
  sheet = ss.insertSheet(PPE_SHEET_NAME);
  var head = sheet.getRange(1, 1, 1, PPE_HEADERS.length);
  head.setValues([PPE_HEADERS]);
  head.setBackground(PPE_HEADER_BG)
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
  // таб_номер (B) — текстовый формат на всю колонку (Task 304)
  sheet.getRange('B2:B').setNumberFormat('@');
  sheet.setFrozenRows(1);
  Logger.log('PPEInit: лист «%s» создан, заголовки: %s',
    PPE_SHEET_NAME, PPE_HEADERS.join(' | '));
  return true;
}

// ШАГ 2: стандартный перечень каждому активному работнику без
// строк СИЗ. Возвращает {workers, rows} — сколько работников
// обработано и сколько строк добавлено.
function ppePrefillStandard() {
  var ss = SpreadsheetApp.openById(PPE_SPREADSHEET_ID);
  var ppeSheet = ss.getSheetByName(PPE_SHEET_NAME);
  if (!ppeSheet) {
    Logger.log('PPEInit: листа «%s» нет — сначала ppeCreateSheet()', PPE_SHEET_NAME);
    return { workers: 0, rows: 0 };
  }
  var empSheet = ss.getSheetByName(PPE_EMPLOYEES_SHEET);
  if (!empSheet) {
    Logger.log('PPEInit: листа «%s» нет — стоп', PPE_EMPLOYEES_SHEET);
    return { workers: 0, rows: 0 };
  }

  // Активные работники (в_архиве=0): A таб_№, B ФИО, J должность
  var empLast = empSheet.getLastRow();
  var workers = [];
  if (empLast >= 2) {
    var vals = empSheet.getRange(2, 1, empLast - 1, 11).getValues();
    for (var i = 0; i < vals.length; i++) {
      var tabNo = String(vals[i][0] || '').trim();
      if (!tabNo) continue;
      if (parseInt(vals[i][8], 10) === 1) continue;  // в_архиве
      workers.push({
        tabNo: tabNo,
        fio:   String(vals[i][1] || '').trim(),
        pos:   String(vals[i][9] || '').trim()
      });
    }
  }

  // Уже покрытые таб_№ (есть хоть одна строка СИЗ)
  var covered = {};
  var ppeLast = ppeSheet.getLastRow();
  if (ppeLast >= 2) {
    var pVals = ppeSheet.getRange(2, 1, ppeLast - 1, 9).getValues();
    for (var p = 0; p < pVals.length; p++) {
      var t = String(pVals[p][1] || '').trim();
      if (t) covered[t] = true;
    }
  }

  // max id
  var maxId = 0;
  if (ppeLast >= 2) {
    var ids = ppeSheet.getRange(2, 1, ppeLast - 1, 1).getValues();
    for (var q = 0; q < ids.length; q++) {
      var v = parseInt(ids[q][0], 10);
      if (!isNaN(v) && v > maxId) maxId = v;
    }
  }

  var added = 0, touched = 0;
  for (var w = 0; w < workers.length; w++) {
    var wk = workers[w];
    if (covered[wk.tabNo]) {
      Logger.log('PPEInit: %s (таб %s) — строки уже есть, пропуск', wk.fio, wk.tabNo);
      continue;
    }
    for (var s = 0; s < PPE_STANDARD.length; s++) {
      var item = PPE_STANDARD[s];
      maxId++;
      var newRow = ppeSheet.getLastRow() + 1;
      // Task 304: B (таб_№) — текст, ведущие нули не теряются
      ppeSheet.getRange(newRow, 2).setNumberFormat('@');
      ppeSheet.getRange(newRow, 1, 1, 9).setValues([[
        maxId, wk.tabNo, wk.fio, wk.pos, item.name,
        '',                                 // дата_выдачи — не выдано
        item.term,
        item.term === 'До износа' ? 'До износа' : '',  // дата_окончания
        item.note
      ]]);
      added++;
    }
    touched++;
    Logger.log('PPEInit: %s (таб %s) — добавлен стандартный перечень (%s позиций)',
      wk.fio, wk.tabNo, PPE_STANDARD.length);
  }
  Logger.log('PPEInit: предзаполнение — работников %s, строк %s', touched, added);
  return { workers: touched, rows: added };
}

// Диагностика: состояние листа «СИЗ» (ничего не меняет)
function ppeStatus() {
  var ss = SpreadsheetApp.openById(PPE_SPREADSHEET_ID);
  var sheet = ss.getSheetByName(PPE_SHEET_NAME);
  if (!sheet) {
    Logger.log('PPEInit: листа «%s» НЕТ — запусти ppeDeployAll()', PPE_SHEET_NAME);
    return;
  }
  var lastRow = sheet.getLastRow();
  Logger.log('PPEInit: лист «%s», строк данных: %s', PPE_SHEET_NAME,
    Math.max(0, lastRow - 1));
  var head = sheet.getRange(1, 1, 1, PPE_HEADERS.length).getValues()[0];
  var headDiff = [];
  for (var h = 0; h < PPE_HEADERS.length; h++) {
    if (String(head[h] || '').trim() !== PPE_HEADERS[h]) {
      headDiff.push(PPE_HEADERS[h] + ' ≠ ' + String(head[h] || ''));
    }
  }
  Logger.log('PPEInit: заголовки %s', headDiff.length
    ? 'ОТЛИЧАЮТСЯ: ' + headDiff.join('; ') : 'совпадают');
  if (lastRow < 2) return;
  var vals = sheet.getRange(2, 1, lastRow - 1, 9).getValues();
  var maxId = 0, byTab = {}, noTab = 0, noName = 0;
  for (var i = 0; i < vals.length; i++) {
    var id = parseInt(vals[i][0], 10);
    if (!isNaN(id) && id > maxId) maxId = id;
    var t = String(vals[i][1] || '').trim();
    if (!t) { noTab++; continue; }
    byTab[t] = (byTab[t] || 0) + 1;
    if (!String(vals[i][4] || '').trim()) noName++;
  }
  Logger.log('PPEInit: последний id=%s; работников со строками: %s; строк без таб_№: %s; строк без наименования: %s',
    maxId, Object.keys(byTab).length, noTab, noName);
  var keys = Object.keys(byTab);
  for (var k = 0; k < keys.length; k++) {
    Logger.log('PPEInit:   таб %s — %s строк', keys[k], byTab[keys[k]]);
  }
}
'''

if __name__ == '__main__':
    print('== Task 392: kip8test ==')
    apply(INDEX, index_repls)
    apply(WS, ws_repls)
    apply(CODE, code_repls)
    io.open('scripts/PPEInit.gs', 'w', encoding='utf-8').write(PPE_INIT)
    print('  OK scripts/PPEInit.gs: создан (%d строк)' % PPE_INIT.count('\n'))
    print('== Готово ==')
