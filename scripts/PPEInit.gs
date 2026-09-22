// ============================================================
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
