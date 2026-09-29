#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 443 — часть 2: PPEInit.gs — лист «СИЗ»: НОВЫЙ столбец
# G «дата_изготовления» справа от F «дата_выдачи» (PPE_HEADERS —
# 10 столбцов), предзаполнение — 10 значений, диагностика — 10
# колонок, НОВАЯ ppeMigrateManufacture() — идемпотентная миграция
# существующего листа (вставка пустого столбца G + шапка).
import io

P = 'scripts/PPEInit.gs'
s = io.open(P, encoding='utf-8').read()
n0 = s

def rep(old, new, tag):
    global s
    assert old in s, 'НЕ НАЙДЕНО (%s): %r' % (tag, old[:90])
    assert s.count(old) == 1, 'НЕ УНИКАЛЬНО (%s): %d вхождений' % (tag, s.count(old))
    s = s.replace(old, new)
    print('OK  %s' % tag)

# --- 1. Назначение файла: упоминание Task 443 ---------------------------
rep(
"""// PPEInit.gs — создание листа «СИЗ» в таблице «График работы»
// (файл табель_КИП_ИОС) и предзаполнение перечня СИЗ (Task 392)
// ============================================================
// НАЗНАЧЕНИЕ:
//   Разовый инструмент деплоя Task 392 (см. scripts/DEPLOY-Task392):""",
"""// PPEInit.gs — создание листа «СИЗ» в таблице «График работы»
// (файл табель_КИП_ИОС) и предзаполнение перечня СИЗ (Task 392)
// ============================================================
// НАЗНАЧЕНИЕ:
//   Разовый инструмент деплоя Task 392 (см. scripts/DEPLOY-Task392)
//   + миграция структуры Task 443 (столбец G «дата_изготовления»):""",
'1. назначение — Task 443')

# --- 2. Список функций: ppeMigrateManufacture ---------------------------
rep(
"""// ФУНКЦИИ (каждая запускается отдельно):
//   ppeDeployAll()       — рекомендованный порядок: создать лист +
//                          предзаполнить стандартный перечень всем
//                          активным работникам. Запустить ОДИН раз.
//   ppeCreateSheet()     — ШАГ 1: создать лист «СИЗ» с заголовками
//                          (существующий лист НЕ трогается).
//   ppePrefillStandard() — ШАГ 2: каждому АКТИВНОМУ работнику""",
"""// ФУНКЦИИ (каждая запускается отдельно):
//   ppeDeployAll()       — рекомендованный порядок: мигрировать
//                          старый лист (Task 443) + создать лист +
//                          предзаполнить стандартный перечень всем
//                          активным работникам. Запустить ОДИН раз.
//   ppeMigrateManufacture() — Task 443, ШАГ 0: вставить столбец G
//                          «дата_изготовления» в СУЩЕСТВУЮЩИЙ лист
//                          (справа от «дата_выдачи»; срок/окончание/
//                          примечание сместятся G→H, H→I, I→J;
//                          данные строк не трогаются — вставляется
//                          пустой столбец). Идемпотентно.
//   ppeCreateSheet()     — ШАГ 1: создать лист «СИЗ» с заголовками
//                          (существующий лист НЕ трогается).
//   ppePrefillStandard() — ШАГ 2: каждому АКТИВНОМУ работнику""",
'2. функции — ppeMigrateManufacture')

# --- 3. Заголовки листа: 10 столбцов ------------------------------------
rep(
"""var PPE_HEADERS    = ['id', 'таб_номер', 'работник', 'должность',
                      'наименование_СИЗ', 'дата_выдачи', 'срок_годности',
                      'дата_окончания', 'примечание'];""",
"""// Task 443: G «дата_изготовления» после F «дата_выдачи» —
// срок_годности/дата_окончания/примечание сместились в H/I/J
var PPE_HEADERS    = ['id', 'таб_номер', 'работник', 'должность',
                      'наименование_СИЗ', 'дата_выдачи', 'дата_изготовления',
                      'срок_годности', 'дата_окончания', 'примечание'];""",
'3. PPE_HEADERS — 10 столбцов')

# --- 4. ppeDeployAll: миграция первым шагом -----------------------------
rep(
"""function ppeDeployAll() {
  var created = ppeCreateSheet();
  var pre = ppePrefillStandard();
  Logger.log('PPEInit: лист=%s, предзаполнено работников=%s, строк добавлено=%s',
    created ? 'создан' : 'уже был', pre.workers, pre.rows);
}""",
"""function ppeDeployAll() {
  ppeMigrateManufacture();   // Task 443: старый лист — новая структура
  var created = ppeCreateSheet();
  var pre = ppePrefillStandard();
  Logger.log('PPEInit: лист=%s, предзаполнено работников=%s, строк добавлено=%s',
    created ? 'создан' : 'уже был', pre.workers, pre.rows);
}

// ШАГ 0 (Task 443): миграция СУЩЕСТВУЮЩЕГО листа «СИЗ» — вставить
// столбец G «дата_изготовления» справа от F «дата_выдачи»; столбцы
// срок_годности/дата_окончания/примечание сместятся G→H, H→I, I→J.
// ДАННЫЕ строк не трогаются: вставляется ПУСТОЙ столбец, прежние
// даты окончания остаются верными (без даты изготовления срок
// считается от даты выдачи — как и раньше). Дата окончания от даты
// изготовления начнёт считаться после её заполнения в приложении
// (или вручную в листе). Идемпотентно: шапка G уже
// «дата_изготовления» → ничего не делает. Листа нет → ничего не
// делает (ppeCreateSheet создаст сразу новую структуру).
function ppeMigrateManufacture() {
  var ss = SpreadsheetApp.openById(PPE_SPREADSHEET_ID);
  var sheet = ss.getSheetByName(PPE_SHEET_NAME);
  if (!sheet) {
    Logger.log('PPEInit (443): листа «%s» нет — миграция не нужна (ppeCreateSheet создаст новую структуру)',
      PPE_SHEET_NAME);
    return false;
  }
  var head = sheet.getRange(1, 1, 1, 10).getValues()[0];
  var g = String(head[6] || '').trim();
  if (g === 'дата_изготовления') {
    Logger.log('PPEInit (443): столбец G уже «дата_изготовления» — миграция не нужна');
    return false;
  }
  if (g !== 'срок_годности') {
    throw new Error('Лист «СИЗ»: шапка G = «' + g +
      '» — ожидается «срок_годности» (старая структура) или «дата_изготовления» (уже мигрировано)');
  }
  sheet.insertColumnAfter(6);  // новый ПУСТОЙ G; старые G/H/I → H/I/J
  var cell = sheet.getRange(1, 7);
  cell.setValue('дата_изготовления');
  cell.setBackground(PPE_HEADER_BG)
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
  Logger.log('PPEInit (443): вставлен столбец G «дата_изготовления» (срок_годности → H, дата_окончания → I, примечание → J); данные строк не менялись');
  return true;
}""",
'4. ppeDeployAll + ppeMigrateManufacture')

# --- 5. ppePrefillStandard: guard структуры + 10 значений ---------------
rep(
"""  var empSheet = ss.getSheetByName(PPE_EMPLOYEES_SHEET);
  if (!empSheet) {
    Logger.log('PPEInit: листа «%s» нет — стоп', PPE_EMPLOYEES_SHEET);
    return { workers: 0, rows: 0 };
  }
""",
"""  var empSheet = ss.getSheetByName(PPE_EMPLOYEES_SHEET);
  if (!empSheet) {
    Logger.log('PPEInit: листа «%s» нет — стоп', PPE_EMPLOYEES_SHEET);
    return { workers: 0, rows: 0 };
  }

  // Task 443: строка предзаполнения — ДЕСЯТЬ значений (G — дата
  // изготовления); нужен лист новой структуры — старый сначала
  // ppeMigrateManufacture() (иначе значения попали бы не в свои
  // столбцы после сдвига G→H→I→J)
  var headG = String(ppeSheet.getRange(1, 7).getValues()[0][0] || '').trim();
  if (headG !== 'дата_изготовления') {
    Logger.log('PPEInit: лист «%s» без столбца G «дата_изготовления» — сначала ppeMigrateManufacture() (Task 443)',
      PPE_SHEET_NAME);
    return { workers: 0, rows: 0 };
  }
""",
'5a. ppePrefillStandard — guard')

rep(
"""  var covered = {};
  var ppeLast = ppeSheet.getLastRow();
  if (ppeLast >= 2) {
    var pVals = ppeSheet.getRange(2, 1, ppeLast - 1, 9).getValues();
    for (var p = 0; p < pVals.length; p++) {
      var t = String(pVals[p][1] || '').trim();
      if (t) covered[t] = true;
    }
  }""",
"""  var covered = {};
  var ppeLast = ppeSheet.getLastRow();
  if (ppeLast >= 2) {
    // Task 443: 10 столбцов (G — дата изготовления)
    var pVals = ppeSheet.getRange(2, 1, ppeLast - 1, 10).getValues();
    for (var p = 0; p < pVals.length; p++) {
      var t = String(pVals[p][1] || '').trim();
      if (t) covered[t] = true;
    }
  }""",
'5b. ppePrefillStandard — чтение 10 колонок')

rep(
"""      // Task 304: B (таб_№) — текст, ведущие нули не теряются
      ppeSheet.getRange(newRow, 2).setNumberFormat('@');
      ppeSheet.getRange(newRow, 1, 1, 9).setValues([[
        maxId, wk.tabNo, wk.fio, wk.pos, item.name,
        '',                                 // дата_выдачи — не выдано
        item.term,
        item.term === 'До износа' ? 'До износа' : '',  // дата_окончания
        item.note
      ]]);""",
"""      // Task 304: B (таб_№) — текст, ведущие нули не теряются.
      // Task 443: ДЕСЯТЬ значений — G дата_изготовления (пустая:
      // заполняется приложением, если срок СИЗ исчисляется с даты
      // производства), H срок, I дата_окончания, J примечание
      ppeSheet.getRange(newRow, 2).setNumberFormat('@');
      ppeSheet.getRange(newRow, 1, 1, 10).setValues([[
        maxId, wk.tabNo, wk.fio, wk.pos, item.name,
        '',                                 // дата_выдачи — не выдано
        '',                                 // дата_изготовления (Task 443)
        item.term,
        item.term === 'До износа' ? 'До износа' : '',  // дата_окончания
        item.note
      ]]);""",
'5c. ppePrefillStandard — запись 10 значений')

# --- 6. ppeStatus: чтение 10 колонок ------------------------------------
rep(
"""  if (lastRow < 2) return;
  var vals = sheet.getRange(2, 1, lastRow - 1, 9).getValues();
  var maxId = 0, byTab = {}, noTab = 0, noName = 0;""",
"""  if (lastRow < 2) return;
  // Task 443: 10 столбцов (G — дата изготовления)
  var vals = sheet.getRange(2, 1, lastRow - 1, 10).getValues();
  var maxId = 0, byTab = {}, noTab = 0, noName = 0;""",
'6. ppeStatus — 10 колонок')

io.open(P, 'w', encoding='utf-8').write(s)
print('\nPPEInit.gs: файл записан (%d -> %d байт)' % (len(n0), len(s)))
