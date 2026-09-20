#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 384 — заявка пользователя: «В Табеле учёта рабочего времени,
# в карточках сотрудников добавь функционал редактирования данных
# сотрудника, отпусков и мероприятий по отдельности, с возможностью
# добавления и удаления информации, по которой будет строиться
# шахматка табеля на месяц и на год».
#
# ЧТО ДЕЛАЕТ ПАТЧ:
#   КЛИЕНТ (index.html):
#     1) карточка сотрудника — ЦЕНТР ПРАВКИ:
#        - профиль: строка «Правка данных…» (редакторам) → шторка
#          #wsEmpSheet в режиме ПРАВКИ (таб. № — readonly, PK);
#        - отпуска: кнопки ✎/✕ у каждого периода (редакторам,
#          записи с id): ✎ → шторка #wsVacSheet в режиме ПРАВКИ,
#          ✕ → deleteVacation (диалог подтверждения);
#        - мероприятия: строка «+ Мероприятие…» (префилл сотрудника)
#          — правка/удаление (✎/✕) уже были (Task 309);
#     2) шторка сотрудника: id заголовка/кнопки (Task 309-паттерн),
#        режимы «Новый сотрудник»/«Правка сотрудника»; submitEmployee-
#        Form — ветка updateEmployee;
#     3) шторка отпуска: id заголовка/кнопки, режимы «Новый отпуск»/
#        «Правка отпуска»; openVacationForm(tabNo, editVacation);
#        submitVacationForm — ветка updateVacation; подбор «части»,
#        пересечения и лимит года НЕ считают саму строку;
#     4) deleteVacation закрывает попапы до диалога (как deleteTraining).
#   СЕРВЕР (справочные копии scripts/*.gs — ручной деплой Apps Script):
#     5) WorkSchedule.gs: НОВЫЕ эндпоинты updateEmployee (B..G, J..K;
#        A/H/I не трогаются) и updateVacation (B..F по id; проверки
#        пересечения/дубля части исключают саму строку; B — текст
#        Task 304);
#     6) Code.gs: диспетчеризация workSchedule.updateEmployee /
#        workSchedule.updateVacation.
#
# SW-бамп делается отдельно: scripts/task384-bump-sw.py (v611 → v612).

import sys

INDEX = 'index.html'
WS_GS = 'scripts/WorkSchedule.gs'
CODE_GS = 'scripts/Code.gs'


def patch(path, repls):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: применено правок: %d' % (path, len(repls)))


# ============================================================
# index.html
# ============================================================
index_repls = []

# --- 1. HTML: комментарий карточки (Task 384 — центр правки) ---
index_repls.append((
    'карточка-комментарий',
    '''     («Инструктажи» — события месяца с кнопками правки/удаления).
     Карточка прикреплена к клику: закрытие — фоновый кловер
     и Esc. -->''',
    '''     («Инструктажи» — события месяца с кнопками правки/удаления).
     Карточка прикреплена к клику: закрытие — фоновый кловер
     и Esc. Task 384: карточка — ЦЕНТР ПРАВКИ по отдельности:
     «Правка данных…» (профиль → updateEmployee), ✎/✕ у периодов
     отпусков (updateVacation/deleteVacation), «+ Мероприятие…»
     (openTrainingForm с префиллом) — редакторам; шахматка на
     месяц и год строится из этих данных («Сформировать»). -->''',
    1))

# --- 2. HTML: шторка сотрудника — id заголовка и кнопки ---
index_repls.append((
    'wsEmpSheetTitle',
    '<div class="flow-input-sheet-title">Новый сотрудник</div>',
    '<div class="flow-input-sheet-title" id="wsEmpSheetTitle">Новый сотрудник</div>',
    1))
index_repls.append((
    'wsEmpSubmitBtn',
    '<button type="button" class="flow-input-submit" onclick="WorkSchedule.submitEmployeeForm()">Добавить</button>',
    '<button type="button" class="flow-input-submit" id="wsEmpSubmitBtn" onclick="WorkSchedule.submitEmployeeForm()">Добавить</button>',
    1))

# --- 3. HTML: шторка отпуска — id заголовка и кнопки ---
index_repls.append((
    'wsVacSheetTitle',
    '<div class="flow-input-sheet-title">Новый отпуск</div>',
    '<div class="flow-input-sheet-title" id="wsVacSheetTitle">Новый отпуск</div>',
    1))
index_repls.append((
    'wsVacSubmitBtn',
    '<button type="button" class="flow-input-submit" onclick="WorkSchedule.submitVacationForm()">Добавить</button>',
    '<button type="button" class="flow-input-submit" id="wsVacSubmitBtn" onclick="WorkSchedule.submitVacationForm()">Добавить</button>',
    1))

# --- 4. JS: докблок модуля — новые эндпоинты ---
index_repls.append((
    'докблок-эндпоинты',
    '''    //   workSchedule.addEmployee         — добавить сотрудника
    //   workSchedule.addTraining         — добавить мероприятие''',
    '''    //   workSchedule.addEmployee         — добавить сотрудника
    //   workSchedule.updateEmployee      — правка данных сотрудника
    //                                     (Task 384: таб_№ — PK,
    //                                     не меняется; B..G, J..K)
    //   workSchedule.addTraining         — добавить мероприятие''',
    1))
index_repls.append((
    'докблок-эндпоинты-отпуска',
    '''    //   workSchedule.addVacation         — добавить период (часть 1..3)
    //   workSchedule.deleteVacation      — удалить период''',
    '''    //   workSchedule.addVacation         — добавить период (часть 1..3)
    //   workSchedule.updateVacation      — правка периода отпуска
    //                                     (Task 384: по id, проверки
    //                                     исключают саму строку)
    //   workSchedule.deleteVacation      — удалить период''',
    1))

# --- 5. JS: состояние — режимы правки шторок ---
index_repls.append((
    'state-переменные',
    '''        // Task 318: таб. № сотрудника шторки увольнения (null — закрыта).
        // Ставится openDismissForm из карточки, сбрасывается
        // closeDismissForm; submitDismissForm отправляет пару
        // {таб_номер, дата_увольнения} → dismissEmployee
        _dismissTabNo: null,''',
    '''        // Task 318: таб. № сотрудника шторки увольнения (null — закрыта).
        // Ставится openDismissForm из карточки, сбрасывается
        // closeDismissForm; submitDismissForm отправляет пару
        // {таб_номер, дата_увольнения} → dismissEmployee
        _dismissTabNo: null,

        // Task 384: режим ПРАВКИ шторки сотрудника — таб. №
        // редактируемого (null — создание). Поле таб. № в правке
        // readOnly (PK: на него ссылаются «Записи_графика»/
        // «Инструктажи»/«Отпуска» — смена таб. № через правку
        // запрещена); submitEmployeeForm уходит в
        // workSchedule.updateEmployee
        _empEditTab: null,

        // Task 384: режим ПРАВКИ шторки отпуска — id редактируемого
        // периода (null — создание). Подбор «части», пересечения и
        // лимит года НЕ считают саму строку (период заменяется
        // целиком); submitVacationForm уходит в
        // workSchedule.updateVacation
        _vacEditId: null,''',
    1))

# --- 6. JS: карточка — «Правка данных…» перед «Уволить…» ---
index_repls.append((
    'карточка-правка-данных',
    '''            // Task 318: «Уволить…» — форма увольнения (дата → таблица''',
    '''            // Task 384: «Правка данных…» — шторка сотрудника в режиме
            // ПРАВКИ (профиль: ФИО/тип/смена/шаблон/старт/приём/
            // должность/комментарий; таб. № — readonly, PK). Сервер:
            // workSchedule.updateEmployee. Только редакторам — как
            // «Уволить…» (двойная защита в openEmpEditForm)
            if (this._canEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-editdata"' +
                        ' title="Правка данных сотрудника: ФИО, режим, должность…"' +
                        ' onclick="WorkSchedule.openEmpEditForm(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">Правка данных…</div>';
            }

            // Task 318: «Уволить…» — форма увольнения (дата → таблица''',
    1))

# --- 7. JS: карточка — ✎/✕ у периодов отпусков ---
index_repls.append((
    'карточка-отпуска-кнопки',
    '''                for (var vk = 0; vk < vacs.length; vk++) {
                    var vv = vacs[vk];
                    var vNet = this._vacNetDaysInYear(vv, this._year);
                    var vCal = this._vacDaysInYear(vv, this._year);
                    var pNo = parseInt(vv.часть, 10);
                    html += '<div class="ws-emp-field"><span class="ws-emp-k">Часть ' +
                            (pNo ? pNo : '—') + '</span><span class="ws-emp-v">' +
                            this._fmtDateRu(vv.дата_начала) + ' — ' +
                            this._fmtDateRu(vv.дата_окончания) + ' · ' +
                            vNet + ' ' + this._plural(vNet, ['день', 'дня', 'дней']) +
                            (vCal > vNet ? ' (−' + (vCal - vNet) + ' праздн.)' : '') +
                            (String(vv.комментарий || '').trim()
                                ? ' · «' + this._esc(vv.комментарий) + '»' : '') +
                            '</span></div>';
                }''',
    '''                for (var vk = 0; vk < vacs.length; vk++) {
                    var vv = vacs[vk];
                    var vNet = this._vacNetDaysInYear(vv, this._year);
                    var vCal = this._vacDaysInYear(vv, this._year);
                    var pNo = parseInt(vv.часть, 10);
                    // Task 384: ✎ — правка периода (шторка «Правка
                    // отпуска», сервер updateVacation), ✕ — удаление
                    // (deleteVacation с подтверждением). Редакторам и
                    // только записям с id (строки листа без id —
                    // ручное заполнение — не правятся, как «Удалить»
                    // из Task 279)
                    var vActs = '';
                    var vId = parseInt(vv.id, 10);
                    if (this._canEdit && vId) {
                        vActs = '<span class="ws-popup-act" title="Редактировать период"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.editVacation(' + vId + ')">✎</span>' +
                                '<span class="ws-popup-act ws-popup-act-del" title="Удалить период"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.deleteVacation(' + vId + ')">✕</span>';
                    }
                    html += '<div class="ws-emp-field"><span class="ws-emp-k">Часть ' +
                            (pNo ? pNo : '—') + '</span><span class="ws-emp-v">' +
                            this._fmtDateRu(vv.дата_начала) + ' — ' +
                            this._fmtDateRu(vv.дата_окончания) + ' · ' +
                            vNet + ' ' + this._plural(vNet, ['день', 'дня', 'дней']) +
                            (vCal > vNet ? ' (−' + (vCal - vNet) + ' праздн.)' : '') +
                            (String(vv.комментарий || '').trim()
                                ? ' · «' + this._esc(vv.комментарий) + '»' : '') +
                            '</span>' + vActs + '</div>';
                }''',
    1))

# --- 8. JS: карточка — «+ Мероприятие…» в конце блока мероприятий ---
index_repls.append((
    'карточка-плюс-мероприятие',
    '''                    html += '<div class="ws-popup-row ws-popup-event">' +
                            '<span class="ws-popup-swatch" style="background:' +
                            (meta.color || '#3a3a3a') + ';"></span>' +
                            '<span class="ws-popup-code">' + this._esc(code || '—') + '</span>' +
                            '<span class="ws-popup-name">' +
                            this._esc(t.тема || meta.name || t.тип) +
                            ' · ' + period + '</span>' + acts + '</div>';
                }
            }
            return html;
        },''',
    '''                    html += '<div class="ws-popup-row ws-popup-event">' +
                            '<span class="ws-popup-swatch" style="background:' +
                            (meta.color || '#3a3a3a') + ';"></span>' +
                            '<span class="ws-popup-code">' + this._esc(code || '—') + '</span>' +
                            '<span class="ws-popup-name">' +
                            this._esc(t.тема || meta.name || t.тип) +
                            ' · ' + period + '</span>' + acts + '</div>';
                }
            }
            // Task 384: «+ Мероприятие…» — шторка «Новое мероприятие»
            // с УЖЕ ВЫБРАННЫМ сотрудником карточки (как «+ Отпуск…»,
            // Task 312). Только редакторам (двойная защита —
            // onEmpAddTraining → openTrainingForm)
            if (this._canEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addtr"' +
                        ' title="Добавить мероприятие этому сотруднику"' +
                        ' onclick="WorkSchedule.onEmpAddTraining(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Мероприятие…</div>';
            }
            return html;
        },''',
    1))

# --- 9. JS: openEmployeeForm — сброс режима правки при создании ---
index_repls.append((
    'openEmployeeForm-сброс',
    '''        openEmployeeForm: function() {
            if (!this._canEdit) return;
            var patSel = document.getElementById('wsEmpPattern');''',
    '''        openEmployeeForm: function() {
            if (!this._canEdit) return;
            // Task 384: сброс режима правки — шторка открывается на
            // СОЗДАНИЕ (заголовок/кнопка/таб. № вводится; режим правки
            // ставит openEmpEditForm поверх этих значений)
            this._empEditTab = null;
            var sheetTitle = document.getElementById('wsEmpSheetTitle');
            var submitBtn = document.getElementById('wsEmpSubmitBtn');
            if (sheetTitle) sheetTitle.textContent = 'Новый сотрудник';
            if (submitBtn) submitBtn.textContent = 'Добавить';
            var tabInput = document.getElementById('wsEmpTabNo');
            if (tabInput) tabInput.readOnly = false;
            var patSel = document.getElementById('wsEmpPattern');''',
    1))

# --- 10. JS: closeEmployeeForm — сброс режима правки ---
index_repls.append((
    'closeEmployeeForm-сброс',
    '''        closeEmployeeForm: function() {
            document.getElementById('wsEmpOverlay').classList.remove('active');
            document.getElementById('wsEmpSheet').classList.remove('active');
        },''',
    '''        closeEmployeeForm: function() {
            document.getElementById('wsEmpOverlay').classList.remove('active');
            document.getElementById('wsEmpSheet').classList.remove('active');
            // Task 384: сброс режима правки (таб. № снова вводится)
            this._empEditTab = null;
            var tabInput = document.getElementById('wsEmpTabNo');
            if (tabInput) tabInput.readOnly = false;
        },

        // Task 384: правка данных сотрудника из карточки (строка
        // «Правка данных…») — шторка #wsEmpSheet в режиме ПРАВКИ:
        // поля заполняются значениями сотрудника, заголовок/кнопка
        // меняются («Правка сотрудника»/«Сохранить»), таб. № —
        // READONLY (PK: смена таб. № сломала бы ссылки листов
        // «Записи_графика»/«Инструктажи»/«Отпуска»). Карточка
        // закрывается ДО шторки (z-уровень попапа 9401 выше шторки
        // 201 — как openDismissForm/onEmpAddVacation)
        openEmpEditForm: function(tabNo) {
            if (!this._canEdit) return;
            var emp = null;
            for (var i = 0; i < (this._EMPLOYEES || []).length; i++) {
                if (this._EMPLOYEES[i]['таб_номер'] === tabNo) {
                    emp = this._EMPLOYEES[i];
                    break;
                }
            }
            if (!emp) {
                if (typeof KipToast !== 'undefined') KipToast.show('Сотрудник не найден');
                return;
            }
            this._empEditTab = String(emp['таб_номер']);

            // Шаблоны ротации — как при создании (префилл значения)
            var patSel = document.getElementById('wsEmpPattern');
            if (patSel) {
                var patHtml = '<option value="">— выберите —</option>';
                for (var pi = 0; pi < this._PATTERNS.length; pi++) {
                    patHtml += '<option value="' + this._PATTERNS[pi].id + '">' +
                               this._esc(this._PATTERNS[pi].name) + ' (цикл ' +
                               this._PATTERNS[pi].cycle + ' дн)</option>';
                }
                patSel.innerHTML = patHtml;
                var empPat = parseInt(emp['шаблон_ротации'], 10);
                if (empPat) patSel.value = String(empPat);
            }

            // Поля профиля из записи сотрудника (старт цикла обязателен
            // на клиенте: пустой в записи → сегодня)
            document.getElementById('wsEmpTabNo').value = String(emp['таб_номер'] || '');
            document.getElementById('wsEmpTabNo').readOnly = true;
            document.getElementById('wsEmpFio').value = String(emp['ФИО'] || '');
            var tip = String(emp['тип'] || '').trim();
            document.getElementById('wsEmpType').value =
                (tip === 'сменный' || tip === 'дневной') ? tip : 'сменный';
            var smena = parseInt(emp['смена'], 10);
            document.getElementById('wsEmpShift').value =
                (smena >= 1 && smena <= 5) ? String(smena) : '';
            document.getElementById('wsEmpStart').value =
                String(emp['старт_цикла'] || '') || this._isoDate(new Date());
            document.getElementById('wsEmpHire').value = String(emp['дата_приёма'] || '');
            // Должность: временная опция текущего значения — асинхронный
            // _fillPositionSelect сохранит выбор (keep = sel.value,
            // Task 318), полный список подгрузится поверх
            var posSel = document.getElementById('wsEmpPosition');
            var posVal = String(emp['должность'] || '').trim();
            if (posSel && posVal) {
                posSel.innerHTML = '<option value="' + this._escAttr(posVal) + '">' +
                                   this._esc(posVal) + '</option>';
                posSel.value = posVal;
            } else if (posSel) {
                posSel.innerHTML = '<option value="">— выберите —</option>';
            }
            this._fillPositionSelect();
            document.getElementById('wsEmpComment').value = String(emp['комментарий'] || '');
            this.onEmpTypeChange();

            // Режим правки: заголовок и кнопка
            var sheetTitle = document.getElementById('wsEmpSheetTitle');
            var submitBtn = document.getElementById('wsEmpSubmitBtn');
            if (sheetTitle) sheetTitle.textContent = 'Правка сотрудника';
            if (submitBtn) submitBtn.textContent = 'Сохранить';

            this.closeEmpPopup();
            document.getElementById('wsEmpOverlay').classList.add('active');
            document.getElementById('wsEmpSheet').classList.add('active');
            setTimeout(function() {
                var f = document.getElementById('wsEmpFio');
                if (f) f.focus();
            }, 350);
        },''',
    1))

# --- 11. JS: submitEmployeeForm — ветка РЕЖИМА ПРАВКИ ---
index_repls.append((
    'submitEmployeeForm-правка',
    '''            if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Введите таб. №'); return; }
            if (!fio)   { if (typeof KipToast !== 'undefined') KipToast.show('Введите ФИО'); return; }
            if (!startCycle) { if (typeof KipToast !== 'undefined') KipToast.show('Укажите дату старта цикла'); return; }

            this._api('workSchedule.addEmployee', {''',
    '''            if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Введите таб. №'); return; }
            if (!fio)   { if (typeof KipToast !== 'undefined') KipToast.show('Введите ФИО'); return; }
            if (!startCycle) { if (typeof KipToast !== 'undefined') KipToast.show('Укажите дату старта цикла'); return; }

            // Task 384: РЕЖИМ ПРАВКИ — данные существующего сотрудника
            // обновляются (workSchedule.updateEmployee; таб. № — из
            // _empEditTab, поле в форме readonly/PK). Шторка закрывается
            // только при успехе — при ошибке поля сохранены для повтора
            if (this._empEditTab) {
                var editTab = this._empEditTab;
                this._api('workSchedule.updateEmployee', {
                    'таб_номер': editTab, 'ФИО': fio, тип: type,
                    смена: shift || null,
                    шаблон_ротации: patId ? parseInt(patId, 10) : null,
                    старт_цикла: startCycle,
                    дата_приёма: hireDate || null,
                    должность: position,
                    комментарий: comment
                }).then(function() {
                    self._empEditTab = null;
                    self.closeEmployeeForm();
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Данные сотрудника обновлены');
                    }
                    // как при добавлении: перезагружаем шахматку — строка
                    // сотрудника перечитается из справочника
                    self.loadGrid(true);
                }).catch(function(err) {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Ошибка: ' + self._apiErrText(err));
                    }
                });
                return;
            }

            this._api('workSchedule.addEmployee', {''',
    1))

# --- 12. JS: onEmpAddTraining — после onEmpAddVacation ---
index_repls.append((
    'onEmpAddTraining',
    '''        onEmpAddVacation: function(tabNo) {
            this.closeEmpPopup();
            this.openVacationForm(tabNo);
        },''',
    '''        onEmpAddVacation: function(tabNo) {
            this.closeEmpPopup();
            this.openVacationForm(tabNo);
        },

        // Task 384: «+ Мероприятие…» из карточки сотрудника — шторка
        // «Новое мероприятие» с префиллом сотрудника (как «+ Отпуск…»,
        // Task 312): карточка закрывается (z-уровень попапа выше
        // шторки), openTrainingForm(tabNo) выбирает сотрудника в
        // селекте ДО дефолтов даты
        onEmpAddTraining: function(tabNo) {
            this.closeEmpPopup();
            this.openTrainingForm(tabNo);
        },''',
    1))

# --- 13. JS: editVacation — новый метод перед openVacationForm ---
index_repls.append((
    'editVacation',
    '''        // Task 312: tabNo (необяз.) — префилл сотрудника из карточки
        // (строка «+ Отпуск…» в блоке отпусков): выбирается в списке
        // ДО вызова onVacEmployeeChange, поэтому «часть» (первый
        // свободный номер) и строка лимита года сразу считаются для
        // НУЖНОГО сотрудника. Без аргумента (прочие вызовы) — как
        // раньше: «— выберите —»
        openVacationForm: function(tabNo) {
            if (!this._canEdit) return;
            var empSel = document.getElementById('wsVacTabNo');
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
            // даты по умолчанию: сегодня + 14 дней (минимальная «большая»
            // часть по ст. 125 ТК РФ), число дней пересчитается
            var today = this._isoDate(new Date());
            var startInput = document.getElementById('wsVacStart');
            var endInput = document.getElementById('wsVacEnd');
            if (startInput) startInput.value = today;
            if (endInput) {
                var dft = new Date();
                dft.setDate(dft.getDate() + 13);
                endInput.value = this._isoDate(dft);
            }
            document.getElementById('wsVacPart').value = '1';
            document.getElementById('wsVacComment').value = '';
            this.onVacEmployeeChange();
            this.onVacDatesChange();

            document.getElementById('wsVacOverlay').classList.add('active');
            document.getElementById('wsVacSheet').classList.add('active');
            setTimeout(function() {
                var f = document.getElementById('wsVacTabNo');
                if (f) f.focus();
            }, 350);
        },''',
    '''        // Task 384: правка периода отпуска из карточки сотрудника
        // (кнопка ✎ у периода) — находит запись в _VACATIONS по id
        // и открывает шторку в режиме ПРАВКИ (openVacationForm с
        // 2-м аргументом — как openTrainingForm с editTraining).
        // Попапы закрываются: шторка с оверлеем ниже попапа по
        // z-index (как editTraining/onEmpAddVacation)
        editVacation: function(id) {
            if (!this._canEdit) return;
            var vid = parseInt(id, 10);
            var rec = null;
            for (var i = 0; i < (this._VACATIONS || []).length; i++) {
                if (parseInt(this._VACATIONS[i].id, 10) === vid) {
                    rec = this._VACATIONS[i];
                    break;
                }
            }
            if (!rec) {
                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('Период отпуска не найден — обновите график');
                }
                return;
            }
            this.closeCellPopup();
            this.closeEmpPopup();
            this.openVacationForm(rec['таб_номер'], rec);
        },

        // Task 312: tabNo (необяз.) — префилл сотрудника из карточки
        // (строка «+ Отпуск…» в блоке отпусков): выбирается в списке
        // ДО вызова onVacEmployeeChange, поэтому «часть» (первый
        // свободный номер) и строка лимита года сразу считаются для
        // НУЖНОГО сотрудника. Без аргумента (прочие вызовы) — как
        // раньше: «— выберите —»
        // Task 384: 2-й аргумент editVacation — запись из _VACATIONS
        // (кнопка ✎ в карточке): режим ПРАВКИ — поля заполняются
        // значениями периода, id хранится в _vacEditId, submit
        // уходит в updateVacation, проверки части/пересечения/лимита
        // НЕ считают саму строку
        openVacationForm: function(tabNo, editVacation) {
            if (!this._canEdit) return;
            var sheetTitle = document.getElementById('wsVacSheetTitle');
            var submitBtn = document.getElementById('wsVacSubmitBtn');
            var empSel = document.getElementById('wsVacTabNo');
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
            // Task 384: два режима — создание (по умолчанию) и ПРАВКА
            // существующего периода (editVacation: запись найдена в
            // _VACATIONS по id — editVacation())
            this._vacEditId = null;
            if (editVacation && editVacation.id) {
                this._vacEditId = parseInt(editVacation.id, 10);
                if (empSel) empSel.value = String(editVacation['таб_номер'] || '');
                var recPart = parseInt(editVacation.часть, 10);
                document.getElementById('wsVacPart').value =
                    (recPart >= 1 && recPart <= 3) ? String(recPart) : '1';
                document.getElementById('wsVacStart').value =
                    String(editVacation.дата_начала || '');
                document.getElementById('wsVacEnd').value =
                    String(editVacation.дата_окончания ||
                           editVacation.дата_начала || '');
                document.getElementById('wsVacComment').value =
                    String(editVacation.комментарий || '');
                if (sheetTitle) sheetTitle.textContent = 'Правка отпуска';
                if (submitBtn) submitBtn.textContent = 'Сохранить';
            } else {
                // даты по умолчанию: сегодня + 14 дней (минимальная «большая»
                // часть по ст. 125 ТК РФ), число дней пересчитается
                var today = this._isoDate(new Date());
                var startInput = document.getElementById('wsVacStart');
                var endInput = document.getElementById('wsVacEnd');
                if (startInput) startInput.value = today;
                if (endInput) {
                    var dft = new Date();
                    dft.setDate(dft.getDate() + 13);
                    endInput.value = this._isoDate(dft);
                }
                document.getElementById('wsVacPart').value = '1';
                document.getElementById('wsVacComment').value = '';
                if (sheetTitle) sheetTitle.textContent = 'Новый отпуск';
                if (submitBtn) submitBtn.textContent = 'Добавить';
            }
            this.onVacEmployeeChange();
            this.onVacDatesChange();

            document.getElementById('wsVacOverlay').classList.add('active');
            document.getElementById('wsVacSheet').classList.add('active');
            setTimeout(function() {
                var f = document.getElementById('wsVacTabNo');
                if (f) f.focus();
            }, 350);
        },''',
    1))

# --- 14. JS: closeVacationForm — сброс режима правки ---
index_repls.append((
    'closeVacationForm-сброс',
    '''        closeVacationForm: function() {
            document.getElementById('wsVacOverlay').classList.remove('active');
            document.getElementById('wsVacSheet').classList.remove('active');
        },''',
    '''        closeVacationForm: function() {
            document.getElementById('wsVacOverlay').classList.remove('active');
            document.getElementById('wsVacSheet').classList.remove('active');
            // Task 384: сброс режима правки (следующее открытие — создание)
            this._vacEditId = null;
        },''',
    1))

# --- 15. JS: onVacEmployeeChange — исключение себя + сохранение части ---
index_repls.append((
    'onVacEmployeeChange-исключение',
    '''        // Выбор сотрудника → «часть» подставляется первым свободным
        // номером (1..3) этого сотрудника в выбранном году
        onVacEmployeeChange: function() {
            var empSel = document.getElementById('wsVacTabNo');
            var partSel = document.getElementById('wsVacPart');
            if (!empSel || !partSel) return;
            var tabNo = empSel.value;
            var used = {};
            for (var i = 0; i < (this._VAC_PAGE || []).length; i++) {
                var v = this._VAC_PAGE[i];
                if (v['таб_номер'] === tabNo &&
                    String(v.дата_начала).slice(0, 4) === String(this._vacYear)) {
                    used[parseInt(v.часть, 10)] = true;
                }
            }
            var free = 1;
            while (free <= 3 && used[free]) free++;
            if (free <= 3) partSel.value = String(free);
            // все 3 части заняты — оставляем выбор пользователю,
            // сервер отклонит дубль (duplicate_часть) с пояснением
            // Task 310: смена сотрудника пересчитывает строку лимита
            this._vacUpdateYearInfo();
        },''',
    '''        // Выбор сотрудника → «часть» подставляется первым свободным
        // номером (1..3) этого сотрудника в выбранном году.
        // Task 384: в режиме ПРАВКИ своя строка не занимает «часть»
        // (период заменяется целиком); выбранная часть СОХРАНЯЕТСЯ,
        // если свободна у других периодов — правим часть 2, не
        // перетаскивая на 1; занята — первый свободный, как при
        // создании
        onVacEmployeeChange: function() {
            var empSel = document.getElementById('wsVacTabNo');
            var partSel = document.getElementById('wsVacPart');
            if (!empSel || !partSel) return;
            var tabNo = empSel.value;
            var used = {};
            for (var i = 0; i < (this._VAC_PAGE || []).length; i++) {
                var v = this._VAC_PAGE[i];
                // Task 384: правка — своя строка не считается
                if (this._vacEditId && parseInt(v.id, 10) === this._vacEditId) continue;
                if (v['таб_номер'] === tabNo &&
                    String(v.дата_начала).slice(0, 4) === String(this._vacYear)) {
                    used[parseInt(v.часть, 10)] = true;
                }
            }
            var cur = parseInt(partSel.value, 10);
            if (this._vacEditId && cur >= 1 && cur <= 3 && !used[cur]) {
                // выбранная часть свободна — сохраняем (режим правки)
            } else {
                var free = 1;
                while (free <= 3 && used[free]) free++;
                if (free <= 3) partSel.value = String(free);
            }
            // все 3 части заняты — оставляем выбор пользователю,
            // сервер отклонит дубль (duplicate_часть) с пояснением
            // Task 310: смена сотрудника пересчитывает строку лимита
            this._vacUpdateYearInfo();
        },''',
    1))

# --- 16. JS: _vacUpdateYearInfo — исключение себя из «запланировано» ---
index_repls.append((
    '_vacUpdateYearInfo-исключение',
    '''            var used = 0;
            for (var i = 0; i < (this._VAC_PAGE || []).length; i++) {
                var v = this._VAC_PAGE[i];
                if (v['таб_номер'] !== tabNo) continue;
                used += this._vacNetDaysInYear(v, year);
            }''',
    '''            var used = 0;
            for (var i = 0; i < (this._VAC_PAGE || []).length; i++) {
                var v = this._VAC_PAGE[i];
                if (v['таб_номер'] !== tabNo) continue;
                // Task 384: правка — своя строка не в счёт «запланиро-
                // вано» (период заменяется новым значением формы)
                if (this._vacEditId && parseInt(v.id, 10) === this._vacEditId) continue;
                used += this._vacNetDaysInYear(v, year);
            }''',
    1))

# --- 17. JS: submitVacationForm — пересечение без себя ---
index_repls.append((
    'submitVacationForm-пересечение',
    '''            for (var i = 0; i < (this._VAC_PAGE || []).length; i++) {
                var v = this._VAC_PAGE[i];
                if (v['таб_номер'] !== tabNo) continue;
                if (startDate <= v.дата_окончания && endDate >= v.дата_начала) {''',
    '''            for (var i = 0; i < (this._VAC_PAGE || []).length; i++) {
                var v = this._VAC_PAGE[i];
                if (v['таб_номер'] !== tabNo) continue;
                // Task 384: правка — пересечение с САМОЙ СОБОЙ не
                // считается (период заменяется целиком)
                if (this._vacEditId && parseInt(v.id, 10) === this._vacEditId) continue;
                if (startDate <= v.дата_окончания && endDate >= v.дата_начала) {''',
    1))

# --- 18. JS: submitVacationForm — лимит без себя ---
index_repls.append((
    'submitVacationForm-лимит',
    '''            for (var li = 0; li < (this._VAC_PAGE || []).length; li++) {
                var lv = this._VAC_PAGE[li];
                if (lv['таб_номер'] !== tabNo) continue;
                usedNet += this._vacNetDaysInYear(lv, vacYear);
            }''',
    '''            for (var li = 0; li < (this._VAC_PAGE || []).length; li++) {
                var lv = this._VAC_PAGE[li];
                if (lv['таб_номер'] !== tabNo) continue;
                // Task 384: правка — своя строка не в счёт лимита
                if (this._vacEditId && parseInt(lv.id, 10) === this._vacEditId) continue;
                usedNet += this._vacNetDaysInYear(lv, vacYear);
            }''',
    1))

# --- 19. JS: submitVacationForm — ветка РЕЖИМА ПРАВКИ ---
index_repls.append((
    'submitVacationForm-правка',
    '''            this._api('workSchedule.addVacation', {
                'таб_номер': tabNo, часть: part,
                дата_начала: startDate, дата_окончания: endDate,
                комментарий: comment
            }).then(function() {''',
    '''            // Task 384: РЕЖИМ ПРАВКИ — период обновляется НА МЕСТЕ
            // (workSchedule.updateVacation, id из _vacEditId; проверки
            // выше уже исключили саму строку из пересечений/лимита).
            // Шторка закрывается только при успехе — при ошибке поля
            // сохранены для повтора
            if (this._vacEditId) {
                var editVacId = this._vacEditId;
                this._api('workSchedule.updateVacation', {
                    id: editVacId,
                    'таб_номер': tabNo, часть: part,
                    дата_начала: startDate, дата_окончания: endDate,
                    комментарий: comment
                }).then(function() {
                    self._vacEditId = null;
                    self.closeVacationForm();
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Период отпуска обновлён. Нажмите «Сформировать» в шахматке — дни отметятся кодом «О»');
                    }
                    self.loadGrid(true);
                }).catch(function(err) {
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Ошибка: ' + self._apiErrText(err));
                    }
                });
                return;
            }

            this._api('workSchedule.addVacation', {
                'таб_номер': tabNo, часть: part,
                дата_начала: startDate, дата_окончания: endDate,
                комментарий: comment
            }).then(function() {''',
    1))

# --- 20. JS: deleteVacation — закрыть попапы до диалога ---
index_repls.append((
    'deleteVacation-попапы',
    '''        deleteVacation: function(id) {
            if (!this._canEdit) return;
            var self = this;''',
    '''        deleteVacation: function(id) {
            if (!this._canEdit) return;
            // Task 384: кнопки ✕ теперь и в карточке сотрудника —
            // закрываем попапы ДО диалога подтверждения (как
            // deleteTraining: карточка по z-уровню выше шторок)
            this.closeCellPopup();
            this.closeEmpPopup();
            var self = this;''',
    1))

# ============================================================
# scripts/WorkSchedule.gs — справочная копия серверного кода
# ============================================================
ws_repls = []

# --- Заголовок: список эндпоинтов ---
ws_repls.append((
    'шапка-эндпоинты',
    '''//   workSchedule.addEmployee      — добавить нового сотрудника
//   workSchedule.dismissEmployee   — уволить: дата_увольнения (H) + в_архиве=1 (I)''',
    '''//   workSchedule.addEmployee      — добавить нового сотрудника
//   workSchedule.updateEmployee   — правка данных сотрудника (Task 384:
//                                   B..G, J..K; таб_№ — PK, не меняется)
//   workSchedule.dismissEmployee   — уволить: дата_увольнения (H) + в_архиве=1 (I)''',
    1))
ws_repls.append((
    'шапка-эндпоинты-отпуска',
    '''//   workSchedule.addVacation      — добавить период отпуска (часть 1..3)
//   workSchedule.deleteVacation   — удалить период отпуска''',
    '''//   workSchedule.addVacation      — добавить период отпуска (часть 1..3)
//   workSchedule.updateVacation   — правка периода отпуска (Task 384:
//                                   B..F по id; проверки не считают
//                                   саму строку)
//   workSchedule.deleteVacation   — удалить период отпуска''',
    1))

# --- updateEmployee: после dismissEmployee, перед CRUD инструктажей ---
ws_repls.append((
    'updateEmployee',
    '''  // ============================================================
  // CRUD инструктажей
  // ============================================================''', 
    '''  // workSchedule.updateEmployee (Task 384)
  // payload: { token, таб_номер, ФИО, тип, смена, шаблон_ротации,
  //            старт_цикла(ISO), дата_приёма(ISO), должность, комментарий }
  // Правка данных сотрудника из карточки (шторка «Правка сотрудника»).
  // Обновляет B..G (ФИО/тип/смена/шаблон/старт_цикла/дата_приёма) и
  // J..K (должность/комментарий); A (таб_номер) — НЕИЗМЕНЕН: PK, на
  // него ссылаются «Записи_графика»/«Инструктажи»/«Отпуска»; H/I
  // (дата_увольнения/в_архиве) не трогаются — увольнение отдельным
  // dismissEmployee.
  updateEmployee: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };
    var fio = String(payload.ФИО || '').trim();
    if (!fio) return { ok: false, error: 'invalid_ФИО' };
    var tip = String(payload.тип || '').trim();
    if (tip !== 'сменный' && tip !== 'дневной') {
      return { ok: false, error: 'invalid_тип' };
    }

    var sheet = this._getSheet(this.EMPLOYEES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.EMPLOYEES_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) {
      return { ok: false, error: 'not_found_таб_номер',
               message: 'Сотрудник с таб. № ' + tabNo + ' не найден' };
    }

    var smena     = payload.смена ? parseInt(payload.смена, 10) : '';
    var patId     = payload.шаблон_ротации ? parseInt(payload.шаблон_ротации, 10) : '';
    var startCycle = this._parseIsoDate(payload.старт_цикла);
    var hireDate  = this._parseIsoDate(payload.дата_приёма);
    var position  = String(payload.должность || '').trim();
    var comment   = String(payload.комментарий || '').slice(0, 500);

    // Поиск строки по таб. № (A — текст, Task 304: ведущие нули)
    var tabs = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < tabs.length; i++) {
      if (String(tabs[i][0]).trim() !== tabNo) continue;
      var row = i + 2;
      // B..G: ФИО, тип, смена, шаблон_ротации, старт_цикла, дата_приёма
      sheet.getRange(row, 2, 1, 6).setValues([[
        fio, tip, smena || null, patId || null, startCycle, hireDate
      ]]);
      // J..K: должность, комментарий (A/H/I не трогаются)
      sheet.getRange(row, 10, 1, 2).setValues([[ position, comment ]]);
      try {
        Utils.audit(user.email, 'WORKSCHEDULE_UPDATE_EMPLOYEE', '', '',
          'Обновлены данные сотрудника таб_номер=' + tabNo + ' ФИО=' + fio);
      } catch (e) { /* ignore */ }
      return { ok: true, data: { таб_номер: tabNo } };
    }
    return { ok: false, error: 'not_found_таб_номер',
             message: 'Сотрудник с таб. № ' + tabNo + ' не найден' };
  },

  // ============================================================
  // CRUD инструктажей
  // ============================================================''', 
    1))

# --- updateVacation: после addVacation, перед deleteVacation ---
ws_repls.append((
    'updateVacation',
    '''  // workSchedule.deleteVacation
  // payload: { token, id }
  deleteVacation: function(payload) {''',
    '''  // workSchedule.updateVacation (Task 384)
  // payload: { token, id, таб_номер, часть(1..3), дата_начала(ISO),
  //            дата_окончания(ISO), комментарий }
  // Правка периода отпуска из карточки сотрудника (шторка «Правка
  // отпуска»). Обновляет B..F строки листа «Отпуска» по id (A — не
  // меняется); валидация — как addVacation, но пересечение/дубль
  // части НЕ считают саму редактируемую строку (иначе правка своих
  // дат/части блокировалась бы собой). Task 304: B (таб_номер) —
  // текстовый формат, ведущие нули не теряются.
  updateVacation: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var id = parseInt(payload.id, 10);
    if (isNaN(id)) return { ok: false, error: 'invalid_id' };
    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };
    var part = parseInt(payload.часть, 10);
    if (isNaN(part) || part < 1 || part > 3) {
      return { ok: false, error: 'invalid_часть',
               message: 'Часть отпуска — 1, 2 или 3' };
    }
    var startDate = this._parseIsoDate(payload.дата_начала);
    if (!startDate) return { ok: false, error: 'invalid_дата_начала' };
    var endDate = payload.дата_окончания ? this._parseIsoDate(payload.дата_окончания) : startDate;
    if (!endDate) endDate = startDate;
    if (endDate.getTime() < startDate.getTime()) {
      return { ok: false, error: 'end_before_start',
               message: 'Дата окончания раньше даты начала' };
    }
    var days = Math.round((endDate.getTime() - startDate.getTime()) /
                          (24 * 60 * 60 * 1000)) + 1;
    var comment = String(payload.комментарий || '').slice(0, 500);

    var sheet = this._getSheet(this.VACATIONS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.VACATIONS_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'not_found' };

    // Строка по id (A)
    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    var rowIndex = -1;
    for (var fi = 0; fi < ids.length; fi++) {
      if (parseInt(ids[fi][0], 10) === id) { rowIndex = fi + 2; break; }
    }
    if (rowIndex === -1) return { ok: false, error: 'not_found' };

    // Проверки по существующим периодам сотрудника — КРОМЕ самой
    // строки (Task 384: правка не пересекается сама с собой и не
    // занимает «свою» часть)
    var values = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
    for (var vi = 0; vi < values.length; vi++) {
      if ((vi + 2) === rowIndex) continue;
      var r = values[vi];
      if ((r[0] === '' || r[0] === null) && !String(r[1] || '').trim() &&
          !this._parseSheetDate(r[3])) continue;
      if (String(r[1] || '').trim() !== tabNo) continue;
      var exStart = this._parseSheetDate(r[3]);
      var exEnd   = this._parseSheetDate(r[4]) || exStart;
      if (!exStart) continue;
      if (endDate.getTime() >= exStart.getTime() &&
          startDate.getTime() <= exEnd.getTime()) {
        return { ok: false, error: 'overlap',
                 message: 'Период пересекается с уже заданным отпуском ' +
                          'этого сотрудника (' + this._toIsoDate(exStart) + ' — ' +
                          this._toIsoDate(exEnd) + ')' };
      }
      var exPart = parseInt(r[2], 10);
      if (exPart === part && exStart.getFullYear() === startDate.getFullYear()) {
        return { ok: false, error: 'duplicate_часть',
                 message: 'Часть ' + part + ' у этого сотрудника уже задана на ' +
                          startDate.getFullYear() + ' год' };
      }
    }

    // Запись B..F (id в A не меняется); Task 304: B — текст
    sheet.getRange(rowIndex, 2).setNumberFormat('@');
    sheet.getRange(rowIndex, 2, 1, 5).setValues(
      [[tabNo, part, startDate, endDate, comment]]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_UPDATE_VACATION', '', '',
        'Обновлён отпуск id=' + id + ' часть=' + part +
        ' таб_номер=' + tabNo + ' ' + this._toIsoDate(startDate) + '…' +
        this._toIsoDate(endDate) + ' (' + days + ' дн.)');
    } catch (e) { /* ignore */ }

    return { ok: true, data: { id: id, дней: days } };
  },

  // workSchedule.deleteVacation
  // payload: { token, id }
  deleteVacation: function(payload) {''',
    1))

# ============================================================
# scripts/Code.gs — диспетчеризация новых эндпоинтов
# ============================================================
code_repls = []
code_repls.append((
    'диспетчер',
    '''      case 'workSchedule.deleteVacation':
        return _json(WorkSchedule.deleteVacation(payload));

      default:''',
    '''      case 'workSchedule.deleteVacation':
        return _json(WorkSchedule.deleteVacation(payload));

      // Task 384: правка данных сотрудника (B..G, J..K; таб_№ — PK,
      // не меняется) — шторка «Правка сотрудника» из карточки
      case 'workSchedule.updateEmployee':
        return _json(WorkSchedule.updateEmployee(payload));

      // Task 384: правка периода отпуска (B..F по id; проверки
      // пересечения/дубля части не считают саму строку)
      case 'workSchedule.updateVacation':
        return _json(WorkSchedule.updateVacation(payload));

      default:''',
    1))

if __name__ == '__main__':
    patch(INDEX, index_repls)
    patch(WS_GS, ws_repls)
    patch(CODE_GS, code_repls)
    print('Task 384: патч применён полностью')
