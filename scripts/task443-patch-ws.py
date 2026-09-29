#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 443 — часть 1: WorkSchedule.gs — лист «СИЗ»: НОВЫЙ столбец
# G «дата_изготовления» справа от F «дата_выдачи»; прежние G/H/I
# (срок_годности/дата_окончания/примечание) сместились в H/I/J.
# Логика даты окончания: ПРИОРИТЕТ у даты изготовления (если
# указана — окончание = изготовление + срок; дата выдачи — только
# информация), иначе — дата выдачи + срок (как прежде).
# Защита от багов сдвига: listPpe читает ОБЕ структуры по шапке
# листа, addPpe/updatePpe требуют новую структуру (guard
# ppe_not_migrated — без записи в чужие столбцы).
import io

P = 'scripts/WorkSchedule.gs'
s = io.open(P, encoding='utf-8').read()
n0 = s

def rep(old, new, tag):
    global s
    assert old in s, 'НЕ НАЙДЕНО (%s): %r' % (tag, old[:90])
    assert s.count(old) == 1, 'НЕ УНИКАЛЬНО (%s): %d вхождений' % (tag, s.count(old))
    s = s.replace(old, new)
    print('OK  %s' % tag)

# --- 1. Шапка файла: описание эндпоинтов -------------------------------
rep(
"""//   workSchedule.listPpe          — СИЗ работников (Task 392, лист «СИЗ»)
//   workSchedule.addPpe           — выдать СИЗ работнику (дата окончания
//                                   считается автоматически: выдача + срок)
//   workSchedule.updatePpe        — правка записи СИЗ (B..I по id)
//   workSchedule.deletePpe        — удалить запись СИЗ""",
"""//   workSchedule.listPpe          — СИЗ работников (Task 392, лист «СИЗ»;
//                                   Task 443 — читает и дату изготовления,
//                                   понимает ОБЕ структуры листа по шапке)
//   workSchedule.addPpe           — выдать СИЗ работнику (дата окончания
//                                   считается автоматически: дата
//                                   изготовления в приоритете, иначе дата
//                                   выдачи, + срок — Task 443)
//   workSchedule.updatePpe        — правка записи СИЗ (B..J по id — Task 443)
//   workSchedule.deletePpe        — удалить запись СИЗ""",
'1. шапка файла — эндпоинты')

# --- 2. Комментарий структуры листа «СИЗ» ------------------------------
rep(
"""// Структура листа «СИЗ» (Task 392 — средства индивидуальной защиты;
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
//   I: примечание""",
"""// Структура листа «СИЗ» (Task 392 — средства индивидуальной защиты;
//   перечень — Приказ Минтруда России от 29.10.2021 N767н, образец —
//   файл «Таблица СИЗ работникам КИП ИОС.xlsx»; создаёт PPEInit.gs;
//   Task 443 — столбец G «дата_изготовления» вставлен после F, прежние
//   G/H/I сместились в H/I/J, миграция ppeMigrateManufacture в PPEInit.gs):
//   A: id (auto-increment)
//   B: таб_номер (FK на Сотрудники; ТЕКСТ — Task 304)
//   C: работник (ФИО — копия для читаемости листа; заполняется
//      приложением из справочника «Сотрудники»)
//   D: должность (копия для читаемости листа; автоматически)
//   E: наименование_СИЗ
//   F: дата_выдачи (Date; может быть пусто — не выдано)
//   G: дата_изготовления (Date; может быть пусто — Task 443; при
//      наличии — ПРИОРИТЕТ расчёта даты окончания: изготовление +
//      срок годности, дата выдачи (F) носит информационный
//      характер; пример — фильтрующие коробки противогазов, у
//      которых срок исчисляется с даты производства)
//   H: срок_годности («1 год» / «1,5 года» / «2 года» / «3 года» /
//      «6 мес.» / «До износа» / пусто)
//   I: дата_окончания (заполняется АВТОМАТИЧЕСКИ: приоритетная дата
//      (изготовление G, иначе выдача F) + срок годности; «До
//      износа» для соответствующего срока; без даты — пусто)
//   J: примечание""",
'2. структура листа СИЗ')

# --- 3. listPpe: dual-read по шапке + поле дата_изготовления -----------
rep(
"""  // Все записи СИЗ (клиент фильтрует по таб_номеру для карточки
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
  },""",
"""  // Все записи СИЗ (клиент фильтрует по таб_номеру для карточки
  // работника). Строка без таб_номера И наименования — пустая
  // (стилевой холст getLastRow, урок Task 294) — пропускается.
  // Даты могут лежать текстом — парсим _parseSheetDate (урок
  // Task 279); дата_окончания «До износа» остаётся СТРОКОЙ.
  // Task 443: столбец G «дата_изготовления» вставлен после F
  // «дата_выдачи» — срок/окончание/примечание сместились G→H,
  // H→I, I→J. ЧТЕНИЕ понимает ОБЕ структуры листа (по шапке
  // строки 1): новая (G «дата_изготовления») и легаси (G
  // «срок_годности» — лист до миграции ppeMigrateManufacture:
  // записи читаются как прежде, дата_изготовления пустая; запись
  // addPpe/updatePpe при этом возвращает ppe_not_migrated).
  listPpe: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { ppe: [] } };

    // Карта служебных столбцов по шапке (Task 443): mfg: 0 —
    // легаси-лист без столбца изготовления (поле = '')
    var head = sheet.getRange(1, 1, 1, 10).getValues()[0];
    var gHead = String(head[6] || '').trim();
    var cols = null;
    if (gHead === 'дата_изготовления') {
      cols = { issued: 6, mfg: 7, term: 8, expiry: 9, note: 10 };
    } else if (gHead === 'срок_годности') {
      cols = { issued: 6, mfg: 0, term: 7, expiry: 8, note: 9 };
    }
    if (!cols) {
      return { ok: false, error: 'ppe_columns_unknown',
               message: 'Лист «СИЗ»: столбец G — не «дата_изготовления» и не «срок_годности», структура не распознана' };
    }

    // Читаем id (A), таб_номер (B), работник (C), должность (D),
    // наименование (E) и служебные столбцы по карте cols
    var values = sheet.getRange(2, 1, lastRow - 1, 10).getValues();
    var ppe = [];
    for (var i = 0; i < values.length; i++) {
      var r = values[i];
      var tabNo = String(r[1] || '').trim();
      var name = String(r[4] || '').trim();
      if (!tabNo && !name) continue;
      var vId = parseInt(r[0], 10);
      var issued = this._parseSheetDate(r[cols.issued - 1]);
      var mfg = cols.mfg ? this._parseSheetDate(r[cols.mfg - 1]) : null;
      var expRaw = r[cols.expiry - 1];
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
        дата_изготовления: mfg ? this._toIsoDate(mfg) : '',
        срок_годности:   String(r[cols.term - 1] || '').trim(),
        дата_окончания:  expiry,
        примечание:      String(r[cols.note - 1] || '').trim()
      });
    }
    return { ok: true, data: { ppe: ppe } };
  },

  // Task 443: у листа «СИЗ» есть столбец G «дата_изготовления»?
  // (шапка строки 1). Запись addPpe/updatePpe требует НОВУЮ
  // структуру: после сдвига G→H→I→J запись в старый лист положила
  // бы срок/окончание/примечание не в свои столбцы — вместо этого
  // понятная ошибка ppe_not_migrated (как legacy_columns в
  // setTrainingDone, урок Task 418)
  _ppeHasManufactureCol: function(sheet) {
    var head = sheet.getRange(1, 7, 1, 1).getValues()[0];
    return String(head[0] || '').trim() === 'дата_изготовления';
  },""",
'3. listPpe dual-read + _ppeHasManufactureCol')

# --- 4. _ppeExpiry: базовая дата (приоритет изготовления) --------------
rep(
"""  // Task 392: дата окончания срока годности = дата выдачи + срок
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
  },""",
"""  // Task 392: дата окончания срока годности = базовая дата + срок
  // (кламп дня к длине целевого месяца: 31.08 + 6 мес → 28/29.02).
  // Task 443: базовая дата = дата ИЗГОТОВЛЕНИЯ (ПРИОРИТЕТ, если
  // указана — срок годности фильтрующих коробок противогазов и
  // т.п. исчисляется с даты производства), иначе дата выдачи;
  // выбор делает вызывающий код (base = manufactured || issued).
  // «До износа» → строка «До износа»; без даты/срока → null
  _ppeExpiry: function(baseDate, term) {
    var months = this._ppeTermMonths(term);
    if (months === -1) return 'До износа';
    if (!months || !baseDate) return null;
    var y = baseDate.getFullYear();
    var mo = baseDate.getMonth() + months;
    var day = baseDate.getDate();
    var last = new Date(y, mo + 1, 0).getDate();
    if (day > last) day = last;
    return new Date(y, mo, day);
  },""",
'4. _ppeExpiry — базовая дата')

# --- 5. addPpe: приоритет изготовления + 10 значений + guard -----------
rep(
"""  // workSchedule.addPpe
  // payload: { token, таб_номер, наименование, дата_выдачи(ISO|''),
  //            срок_годности, примечание }
  // Добавляет запись СИЗ работнику. Работник/должность (C/D) — копия
  // из справочника «Сотрудники» (для читаемости листа). Дата
  // окончания (H) считается АВТОМАТИЧЕСКИ: дата выдачи + срок
  // годности; «До износа» → текст «До износа»; без даты выдачи —
  // пусто (образец файла «Таблица СИЗ работникам КИП ИОС»).
  addPpe: function(payload) {""",
"""  // workSchedule.addPpe
  // payload: { token, таб_номер, наименование, дата_выдачи(ISO|''),
  //            дата_изготовления(ISO|'' — Task 443), срок_годности,
  //            примечание }
  // Добавляет запись СИЗ работнику. Работник/должность (C/D) — копия
  // из справочника «Сотрудники» (для читаемости листа). Дата
  // окончания (I) считается АВТОМАТИЧЕСКИ: ПРИОРИТЕТ у даты
  // изготовления (G): если указана — окончание = изготовление +
  // срок, дата выдачи (F) носит информационный характер; без даты
  // изготовления — дата выдачи + срок (Task 392); «До износа» →
  // текст «До износа»; без дат — пусто. Требует НОВУЮ структуру
  // листа (Task 443) — легаси-шапка → ppe_not_migrated.
  addPpe: function(payload) {""",
'5a. addPpe — докстринг')

rep(
"""    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };

    var issued = payload.дата_выдачи ? this._parseIsoDate(payload.дата_выдачи) : null;
    var term = String(payload.срок_годности || '').trim().slice(0, 50);
    var comment = String(payload.примечание || '').slice(0, 200);
    var expiry = this._ppeExpiry(issued, term);  // Date|'До износа'|null

    // max id в столбце A""",
"""    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };
    if (!this._ppeHasManufactureCol(sheet)) {
      return { ok: false, error: 'ppe_not_migrated',
               message: 'Лист «СИЗ»: нет столбца G «дата_изготовления» — запустите ppeMigrateManufacture() в редакторе Apps Script (Task 443)' };
    }

    var issued = payload.дата_выдачи ? this._parseIsoDate(payload.дата_выдачи) : null;
    var manufactured = payload.дата_изготовления ? this._parseIsoDate(payload.дата_изготовления) : null;
    var term = String(payload.срок_годности || '').trim().slice(0, 50);
    var comment = String(payload.примечание || '').slice(0, 200);
    // Task 443: приоритет даты изготовления (фильтрующие коробки
    // противогазов — срок с даты производства); иначе — дата выдачи
    var base = manufactured || issued;
    var expiry = this._ppeExpiry(base, term);  // Date|'До износа'|null

    // max id в столбце A""",
'5b. addPpe — guard + парсинг изготовления')

rep(
"""    // Task 304: B (таб_№) — текст, ведущие нули не теряются
    this._appendRowKeepText(sheet,
      [newId, tabNo, emp.fio, emp.position, name, issued, term, expiry, comment],
      [2]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_ADD_PPE', '', '',
        'Добавлено СИЗ id=' + newId + ' таб_номер=' + tabNo +
        ' «' + name + '»' +
        (issued ? ' выдано ' + this._toIsoDate(issued) : ''));""",
"""    // Task 304: B (таб_№) — текст, ведущие нули не теряются.
    // Task 443: строка — ДЕСЯТЬ значений (F выдача, G изготовление,
    // H срок, I окончание, J примечание)
    this._appendRowKeepText(sheet,
      [newId, tabNo, emp.fio, emp.position, name, issued, manufactured, term, expiry, comment],
      [2]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_ADD_PPE', '', '',
        'Добавлено СИЗ id=' + newId + ' таб_номер=' + tabNo +
        ' «' + name + '»' +
        (issued ? ' выдано ' + this._toIsoDate(issued) : '') +
        (manufactured ? ' изгот. ' + this._toIsoDate(manufactured) : ''));""",
'5c. addPpe — запись 10 значений + аудит')

# --- 6. updatePpe: приоритет + B..J + guard ----------------------------
rep(
"""  // workSchedule.updatePpe
  // payload: { token, id, таб_номер, наименование, дата_выдачи(ISO|''),
  //            срок_годности, примечание }
  // Правка записи СИЗ из карточки работника (шторка «Правка СИЗ»).
  // Обновляет B..I строки по id (A не меняется); работник/должность
  // (C/D) освежаются из справочника «Сотрудники»; дата окончания
  // (H) пересчитывается. Task 304: B (таб_номер) — текстовый формат.
  updatePpe: function(payload) {""",
"""  // workSchedule.updatePpe
  // payload: { token, id, таб_номер, наименование, дата_выдачи(ISO|''),
  //            дата_изготовления(ISO|'' — Task 443), срок_годности,
  //            примечание }
  // Правка записи СИЗ из карточки работника (шторка «Правка СИЗ»).
  // Обновляет B..J строки по id (A не меняется; Task 443 — 9
  // значений: срок H, окончание I, примечание J); работник/
  // должность (C/D) освежаются из справочника «Сотрудники»; дата
  // окончания (I) пересчитывается с ПРИОРИТЕТОМ даты изготовления
  // (G). Task 304: B (таб_номер) — текстовый формат. Требует новую
  // структуру листа — легаси-шапка → ppe_not_migrated.
  updatePpe: function(payload) {""",
'6a. updatePpe — докстринг')

rep(
"""    var sheet = this._getSheet(this.PPE_SHEET);
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
      [[tabNo, emp.fio, emp.position, name, issued, term, expiry, comment]]);""",
"""    var sheet = this._getSheet(this.PPE_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.PPE_SHEET };
    if (!this._ppeHasManufactureCol(sheet)) {
      return { ok: false, error: 'ppe_not_migrated',
               message: 'Лист «СИЗ»: нет столбца G «дата_изготовления» — запустите ppeMigrateManufacture() в редакторе Apps Script (Task 443)' };
    }

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
    var manufactured = payload.дата_изготовления ? this._parseIsoDate(payload.дата_изготовления) : null;
    var term = String(payload.срок_годности || '').trim().slice(0, 50);
    var comment = String(payload.примечание || '').slice(0, 200);
    // Task 443: приоритет даты изготовления, иначе — дата выдачи
    var base = manufactured || issued;
    var expiry = this._ppeExpiry(base, term);

    // Запись B..J (id в A не меняется; Task 443 — 9 значений:
    // F выдача, G изготовление, H срок, I окончание, J примечание);
    // Task 304: B — текст
    sheet.getRange(rowIndex, 2).setNumberFormat('@');
    sheet.getRange(rowIndex, 2, 1, 9).setValues(
      [[tabNo, emp.fio, emp.position, name, issued, manufactured, term, expiry, comment]]);""",
'6b. updatePpe — guard + B..J')

io.open(P, 'w', encoding='utf-8').write(s)
print('\nWorkSchedule.gs: %d замен, файл записан (%d -> %d байт)'
      % (6 if s != n0 else 0, len(n0), len(s)))
