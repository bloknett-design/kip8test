// ============================================================
// VacationsInit.gs — Одноразовая инициализация листа «Отпуска»
// в Google Таблице табель_КИП_ИОС (Task 274/275 — автоматическая
// расстановка отпусков в шахматке)
// ============================================================
// ИСПОЛЬЗОВАНИЕ:
//   1. Скопировать этот файл в проект Apps Script табели
//      (тот же проект, где Code.gs, Utils.gs, WorkSchedule.gs)
//   2. В редакторе Apps Script выбрать функцию vacationsInitSheet
//      в выпадающем списке функций
//   3. Нажать ▶ Run (первый запуск попросит авторизацию — разрешить)
//   4. Проверить лог выполнения (Ctrl+Enter / «Выполнение»)
//   5. После инициализации этот файл можно удалить из проекта
//
// ФУНКЦИИ:
//   vacationsInitSheet([force]) — создать/починить лист «Отпуска»:
//     • листа нет            → создать: шапка A1–F1, форматирование,
//                              валидации, подсветка пересечений;
//     • лист есть, БЕЗ force → БЕЗОПАСНЫЙ режим: данные НЕ трогаются;
//                              чинится только шапка (если строки 1
//                              не было — данные сдвигаются вниз);
//     • force = true         → полная перестройка (ДАННЫЕ УДАЛЯЮТСЯ!).
//   vacationsSeedDemo([force]) — демо-периоды из DEPLOY-инструкции
//     (017 — 3 части 28 дн., 023 — 1 часть). Добавляются только на
//     пустой лист (или force=true). Удобно для проверки сразу
//     после деплоя серверной части Task 274.
//
// СТРУКТУРА ЛИСТА (строка 1 — шапка, данные со строки 2; читает
// WorkSchedule.gs → VACATIONS_SHEET):
//   A: id             — число; присваивает приложение (max id + 1)
//   B: таб_номер      — текст, FK на лист «Сотрудники» (столбец A)
//   C: часть          — число 1–3 (отпуск делится на 2–3 части в год)
//   D: дата_начала    — дата
//   E: дата_окончания — дата
//   F: комментарий    — текст (до 500 символов)
//
// ВАЖНО: даты обязаны быть реальными датами Google Таблиц —
// WorkSchedule.gs проверяет `instanceof Date` и ИГНОРИРУЕТ строки.
// vacationsSeedDemo пишет даты как new Date(y, m, d); при ручном
// заполнении вводите даты в ячейки с форматом даты (не текстом).
//
// Идемпотентность: повторный запуск vacationsInitSheet() безопасен —
// данные сохраняются, переустанавливаются только шапка/форматирование/
// валидации/подсветка. С другими листами таблицы скрипт НЕ работает.
// ============================================================

/**
 * Инициализация листа «Отпуска» в табель_КИП_ИОС.
 * Запускается вручную из редактора Apps Script (один раз).
 *
 * @param {boolean} [force] — true: очистить лист и перестроить
 *                            (ДАННЫЕ УДАЛЯЮТСЯ). По умолчанию false.
 * @return {Object} { sheet, rows, created, force }
 */
function vacationsInitSheet(force) {
  // Тот же ID, что и WorkSchedule.gs (табель_КИП_ИОС)
  var SPREADSHEET_ID = '1MQtW-CWCmjlu-SAeVBllKDP6NRkiOkmW-7xgOjHskWY';
  var SHEET_NAME = 'Отпуска';
  var HEADERS = ['id', 'таб_номер', 'часть', 'дата_начала', 'дата_окончания', 'комментарий'];
  var VALIDATION_ROWS = 1000;  // валидации/подсветка до строки 1000

  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME);

  // --- Создать лист, если не существует ---
  var created = false;
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    created = true;
    Logger.log('Лист «' + SHEET_NAME + '» создан.');
  }

  var lastRow = sheet.getLastRow();
  var hasData = lastRow >= 2;

  // --- force: полная перестройка (данные удаляются!) ---
  if (force) {
    if (hasData) {
      Logger.log('⚠ FORCE: лист очищается — ' + (lastRow - 1) +
                 ' строк данных будет удалено.');
    }
    sheet.clear();
    hasData = false;
  }

  // --- Шапка (строка 1) ---
  // Приложение читает данные СТРОГО со строки 2: всё, что стоит в
  // строке 1, воспринимается как шапка и в данные НЕ попадает.
  //   • строка 1 пуста            → пишем шапку в неё (данные со
  //                                 строки 2 остаются на месте);
  //   • A1 = 'id'                 → шапка на месте, канонизируем все
  //                                 6 ячеек (починка опечаток);
  //   • A1 заполнен чем-то иным   → в строке 1 ДАННЫЕ (приложение их
  //                                 не видело!) — вставляем строку
  //                                 сверху, данные сдвигаются вниз
  //                                 и становятся видимыми.
  var a1 = String(sheet.getRange(1, 1).getValue()).trim();
  if (a1 !== '' && a1 !== HEADERS[0]) {
    sheet.insertRowBefore(1);
    Logger.log('⚠ Строка 1 содержала данные («' + a1 + '») — вставлена ' +
               'строка шапки, данные сдвинуты вниз (ранее приложение ' +
               'их не видело: чтение идёт со строки 2).');
  }
  sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);

  // --- Форматирование ---
  // Стиль как у остальных инициализируемых листов (FlowmeterInit.gs):
  // жирная шапка, синий фон, белый текст, закрепление строки 1.
  var headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
  headerRange.setFontWeight('bold')
             .setBackground('#4a86e8')
             .setFontColor('#ffffff');

  sheet.setFrozenRows(1);

  // Ширины столбцов (autoResizeColumn не подходит: у пустого столбца
  // без данных он сужается до минимума)
  sheet.setColumnWidth(1, 60);    // id
  sheet.setColumnWidth(2, 110);   // таб_номер
  sheet.setColumnWidth(3, 70);    // часть
  sheet.setColumnWidth(4, 120);   // дата_начала
  sheet.setColumnWidth(5, 130);   // дата_окончания
  sheet.setColumnWidth(6, 320);   // комментарий

  // Форматы на весь столбец (открытые диапазоны A2:A — новые строки
  // наследуют формат):
  sheet.getRange('A2:A').setNumberFormat('0');           // id — целое
  sheet.getRange('C2:C').setNumberFormat('0');           // часть — целое
  sheet.getRange('D2:E').setNumberFormat('dd.mm.yyyy');  // даты
  sheet.getRange('A2:A').setHorizontalAlignment('center');
  sheet.getRange('C2:E').setHorizontalAlignment('center');

  // --- Валидация: часть = целое 1..3 (ст. 125 ТК РФ) ---
  // addVacation отклонит неверную часть на сервере; валидация
  // помогает при ручном редактировании листа.
  // ВАЖНО: у DataValidationBuilder НЕТ метода setHelpTitle — только
  // setHelpText (иначе TypeError, Task 276). Не добавлять.
  var partRule = SpreadsheetApp.newDataValidation()
    .requireNumberBetween(1, 3)
    .setAllowInvalid(false)
    .setHelpText('Часть отпуска: введите 1, 2 или 3 (ст. 125 ТК РФ — отпуск делится на 1–3 части в год).')
    .build();
  sheet.getRange(2, 3, VALIDATION_ROWS - 1, 1).setDataValidation(partRule);

  // --- Валидация: таб_номер — выпадающий список из «Сотрудники» ---
  var empSheet = ss.getSheetByName('Сотрудники');
  if (empSheet && empSheet.getLastRow() >= 2) {
    var empRange = empSheet.getRange(2, 1, empSheet.getLastRow() - 1, 1);
    var empRule = SpreadsheetApp.newDataValidation()
      .requireValueInRange(empRange, true)  // true — показывать список
      .setAllowInvalid(false)
      .setHelpText('Табельный номер: выберите сотрудника из листа «Сотрудники».')
      .build();
    sheet.getRange(2, 2, VALIDATION_ROWS - 1, 1).setDataValidation(empRule);
    Logger.log('Выпадающий список таб_номер: ' + (empSheet.getLastRow() - 1) +
               ' сотрудников из листа «Сотрудники».');
  } else {
    Logger.log('⚠ Лист «Сотрудники» пуст или не найден — выпадающий список ' +
               'таб_номер не настроен (не критично, можно заполнить вручную).');
  }

  // --- Подсветка пересечений периодов одного сотрудника (D2:E) ---
  // Сервер addVacation отклоняет пересечения; при РУЧНОМ заполнении
  // пересекающиеся периоды подсвечиваются красным. Периоды
  // [s1..e1] и [s2..e2] пересекаются, если s1 <= e2 и e1 >= s2.
  // «<>» (непустые) в COUNTIFS и guards $D2/$E2 — черновики без
  // дат (заполнен только таб_номер) не дают ложных пересечений.
  var overlapRange = sheet.getRange(2, 4, VALIDATION_ROWS - 1, 2);  // D2:E1000
  var overlapFormula = 'AND($B2<>"", $D2<>"", $E2<>"", ' +
    'COUNTIFS($B$2:$B,$B2, $D$2:$D,"<>", $E$2:$E,"<>", ' +
    '$D$2:$D,"<="&$E2, $E$2:$E,">="&$D2) > 1)';
  var overlapRule = SpreadsheetApp.newConditionalFormatRule()
    .whenFormulaSatisfied(overlapFormula)
    .setBackground('#f4c7c3')
    .build();
  // Правила листа заменяются целиком (идемпотентность повторных
  // запусков; свои правила на листе «Отпуска» завести заново).
  sheet.setConditionalFormatRules([overlapRule]);
  Logger.log('Подсветка пересечений периодов: D2:E' + (VALIDATION_ROWS - 0) +
             ' (красный фон).');

  // --- Итог ---
  var dataRows = Math.max(0, sheet.getLastRow() - 1);
  Logger.log('==========================================');
  Logger.log('Лист «' + SHEET_NAME + '» готов' +
             (created ? ' (создан)' : ' (существовал)') + '.');
  Logger.log('Столбцы: ' + HEADERS.join(', '));
  Logger.log('Строк данных: ' + dataRows + ' — ' +
             (force ? 'очищено (force)' : 'сохранены'));
  Logger.log('Следующий шаг: деплой WorkSchedule.gs + Code.gs — см. ' +
             'scripts/DEPLOY-Task274-vacations.md.');
  if (dataRows === 0) {
    Logger.log('Совет: для быстрой проверки запустите vacationsSeedDemo() — ' +
               'демо-периоды 017 (3 части) и 023 (1 часть).');
  }
  return { sheet: SHEET_NAME, rows: dataRows, created: created, force: !!force };
}

// ============================================================
// vacationsSeedDemo — демо-периоды из DEPLOY-инструкции
// ============================================================
// Заполняет лист «Отпуска» примером из DEPLOY-Task274-vacations.md:
//   017 — 3 части (14 + 10 + 4 = 28 дн.), 023 — 1 часть (14 дн.).
// Добавляет ТОЛЬКО на пустой лист (или с force=true — тогда поверх
// существующих, id продолжается от max id).
//
// Даты — Date objects (месяц в JavaScript 0-indexed: 5 = июнь).
// После деплоя серверной части: «Сформировать» за 2026 год проставит
// «О» в июне/августе/октябре у 017 и в июне у 023.
//
// @param {boolean} [force] — true: добавить поверх существующих данных.
// ============================================================
function vacationsSeedDemo(force) {
  var SPREADSHEET_ID = '1MQtW-CWCmjlu-SAeVBllKDP6NRkiOkmW-7xgOjHskWY';
  var SHEET_NAME = 'Отпуска';

  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    Logger.log('⚠ Лист «Отпуска» не найден — сначала запустите ' +
               'vacationsInitSheet().');
    return;
  }

  var lastRow = sheet.getLastRow();
  if (lastRow >= 2 && !force) {
    Logger.log('Лист уже содержит данные (' + (lastRow - 1) +
               ' строк) — демо не добавлено.');
    Logger.log('Для добавления демо поверх существующих: ' +
               'vacationsSeedDemo(true).');
    return;
  }

  // Демо-периоды (пример из DEPLOY-Task274-vacations.md)
  var DEMO = [
    { tab: '017', part: 1, start: new Date(2026, 5, 1),  end: new Date(2026, 5, 14),  comment: 'основная часть' },
    { tab: '017', part: 2, start: new Date(2026, 7, 3),  end: new Date(2026, 7, 12),  comment: '' },
    { tab: '017', part: 3, start: new Date(2026, 9, 19), end: new Date(2026, 9, 22),  comment: '' },
    { tab: '023', part: 1, start: new Date(2026, 5, 15), end: new Date(2026, 5, 28),  comment: '' }
  ];

  // Предупреждение: страница «Отпуска» строится по списку «Сотрудники»
  // (join по таб_номер) — периоды несуществующих номеров не отобразятся.
  var empSheet = ss.getSheetByName('Сотрудники');
  if (empSheet && empSheet.getLastRow() >= 2) {
    var empVals = empSheet.getRange(2, 1, empSheet.getLastRow() - 1, 1).getValues();
    var tabs = {};
    for (var i = 0; i < empVals.length; i++) {
      tabs[String(empVals[i][0]).trim()] = true;
    }
    var warned = {};
    for (var j = 0; j < DEMO.length; j++) {
      var t = DEMO[j].tab;
      if (!warned[t]) {
        warned[t] = true;
        if (!tabs[t]) {
          Logger.log('⚠ таб_номер ' + t + ' отсутствует в «Сотрудники» — ' +
                     'его периоды не отобразятся на странице «Отпуска» ' +
                     '(замените таб в скрипте на реальный номер).');
        }
      }
    }
  }

  // max id в столбце A (та же логика, что в addVacation)
  var maxId = 0;
  if (lastRow >= 2) {
    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var k = 0; k < ids.length; k++) {
      var v = parseInt(ids[k][0], 10);
      if (!isNaN(v) && v > maxId) maxId = v;
    }
  }

  // Добавление (appendRow, как в addVacation: [id, таб, часть, start, end, комментарий])
  for (var d = 0; d < DEMO.length; d++) {
    var row = DEMO[d];
    maxId++;
    sheet.appendRow([maxId, row.tab, row.part, row.start, row.end, row.comment]);
  }

  Logger.log('Добавлено демо-периодов: ' + DEMO.length +
             ' (id ' + (maxId - DEMO.length + 1) + '…' + maxId + ').');
  Logger.log('017: 3 части (14 + 10 + 4 = 28 дн.), 023: 1 часть (14 дн.).');
  Logger.log('Даты записаны как Date objects. «Сформировать» (2026) ' +
             'проставит «О»: июнь/август/октябрь — 017, июнь — 023.');
}
