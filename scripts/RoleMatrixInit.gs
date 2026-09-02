/**
 * RoleMatrixInit.gs — ОДНОРАЗОВЫЙ скрипт инициализации системы доступа.
 * Task 293. Запускать в Apps Script-проекте, привязанном к таблице
 * KIP8_Access (тот же проект, что деплоится как Web App AKfycbyt…).
 *
 * ЧТО ДЕЛАЕТ:
 *   Создаёт 3 листа в стиле существующих (users, sessions, …):
 *
 *   1) matrix — МАТРИЦА ДОСТУПА «роль × право» (главный лист).
 *      Строки 1–3: описание/инструкция/версия. Строка 4: технические
 *      ID (role_id в A, perm_id в C..). Строка 5: человекочитаемые
 *      названия. Строки 6+: роли, в ячейках — чекбоксы (галочки).
 *
 *   2) permissions — реестр прав (справочник, расширяемый):
 *      perm_id, Название, Описание, Группа, Конфликт с,
 *      Системное, Активно, Добавлено.
 *
 *   3) roles — реестр ролей (справочник):
 *      role_id, Название, Описание, Системная, Порядок.
 *      ВАЖНО: «Название» должно ТОЧНО совпадать со значениями
 *      role в листе users (по нему сервер сопоставляет роль
 *      пользователя со строкой матрицы).
 *
 * БЕЗОПАСНОСТЬ:
 *   - Существующие листы (users/sessions/otp_codes/audit_log/config)
 *     НЕ трогаются.
 *   - Повторный запуск при уже существующем листе matrix — выход
 *     без изменений (идемпотентность).
 *   - Технические строки/колонки защищены «мягкой» защитой
 *     (warning-only): редактирование возможно, но с предупреждением.
 *
 * РАСШИРЕНИЕ В БУДУЩЕМ (когда появятся новые разделы/функционалы):
 *   Новое право  = новая колонка в matrix (строка 4 — perm_id,
 *                  строка 5 — название) + строка в permissions.
 *   Новая роль   = новая строка в matrix (A — role_id, B — название)
 *                  + строка в roles.
 *   Код сервера (RoleMatrix.gs, следующий этап) читает matrix
 *   динамически: количество строк/колонок не фиксировано.
 */

// Если скрипт запускается в проекте, НЕ привязанном к таблице —
// укажите ID таблицы здесь (иначе оставьте как есть: используется
// активная таблица проекта). По умолчанию — ID файла KIP8_Access.
var FALLBACK_SPREADSHEET_ID = '1TmmNZLUArWH38F6NX0gMGar8LMNMQomm_FaGZv9osyk';

// ==========================================================================
// ДАННЫЕ ПО УМОЛЧАНИЮ (карта ролей пользователя, актуальная на 02.09.2026;
// 2 расхождения со старым кодом применены ПО ТАБЛИЦЕ:
//   ф.11 «Ввод показаний» добавлен роли ИТР ИОС;
//   ф.12 «График работы — просмотр» добавлен роли ИТР8 pro)
// ==========================================================================

// [role_id, Название, Описание, Системная, Порядок]
var INIT_ROLES = [
  ['zapret',       'Запрет',           'Полный запрет: доступна только главная страница (используется для блокировки пользователя)', true,  1],
  ['common',       'Общий доступ',     'Гостевой уровень: только инженерные калькуляторы, вход не требуется',                          true,  2],
  ['itr_tokem',    'ИТР ТОКЕМ',        'Калькуляторы + КИП ИОС с ограничениями (фильтр 4) + Что нового',                                false, 3],
  ['kip8',         'КИП8',             'Калькуляторы + библиотека (билеты) + секретные кнопки + Что нового',                            false, 4],
  ['kip8_pro',     'КИП8 pro',         'КИП8 + расходомеры хозрасчётные (просмотр)',                                                      false, 5],
  ['kip_ios',      'КИП ИОС',          'Полный КИП ИОС + библиотека + секретные кнопки + Что нового',                                    false, 6],
  ['kip_ios_pro',  'КИП ИОС pro',      'КИП ИОС + правка кабельного журнала',                                                             false, 7],
  ['kip_ios_duty', 'КИП ИОС дежурный', 'КИП ИОС + расходомеры с вводом показаний',                                                        false, 8],
  ['itr8',         'ИТР8',             'КИП ИОС + расходомеры хозрасчётные (просмотр)',                                                   false, 9],
  ['itr8_pro',     'ИТР8 pro',         'ИТР8 + просмотр графика работы',                                                                  false, 10],
  ['itr_ios',      'ИТР ИОС',          'ИТР8 + правка кабельного журнала + ввод показаний',                                               false, 11],
  ['admin',        'Админ',            'Полный доступ: все разделы, админ-панель, управление матрицей',                                  true,  12]
];

// [perm_id, Название, Описание, Группа, Конфликт с, Системное, Активно, Добавлено]
var INIT_PERMISSIONS = [
  ['calc.view',           'Инженерные калькуляторы',        'Отображение раздела «Инженерные калькуляторы» и всех калькуляторов/конвертеров',                     'Разделы',        '',                false, true, '2026-09-02'],
  ['library.view',        'Билеты и Библиотека КИП и А',    'Отображение разделов «Экзаменационные билеты» и «Библиотека КИП и А»',                                 'Разделы',        '',                false, true, '2026-09-02'],
  ['kipios.view',         'КИП ИОС — полный',               'Отображение всех разделов КИП ИОС: приборы, блокировки, клапаны, регуляторы, проекты, каб. журнал, план 114', 'КИП ИОС', 'kipios.restricted', false, true, '2026-09-02'],
  ['kipios.restricted',   'КИП ИОС — с ограничениями',      'КИП ИОС с фильтром: скрыты Графики, Проекты, Кабельный журнал, столбец «Замечания»; скрыты приборы без «В гр. ППР» и блокировки без «В перечне»', 'КИП ИОС', 'kipios.view', false, true, '2026-09-02'],
  ['cablejournal.edit',   'Кабельный журнал — правка',      'Добавление, правка и удаление кабелей в разделе «Кабельный журнал»',                                   'Действия',       '',                false, true, '2026-09-02'],
  ['admin.panel',         'Админ-панель',                   'Отображение раздела «Админ-панель»: пользователи, сессии, логи, матрица доступа',                      'Система',        '',                true,  true, '2026-09-02'],
  ['secret.view',         'Секретные кнопки',               'Доступны секретные кнопки «Сапёр» и «Телефонный справочник»',                                          'Сервис',         '',                false, true, '2026-09-02'],
  ['whatsnew.view',       'Что нового',                     'Отображение раздела «Что нового»',                                                                      'Разделы',        '',                false, true, '2026-09-02'],
  ['charts.view',         'Графики КИП ИОС',                'Отображение кнопки раздела «Графики» на странице КИП ИОС',                                             'Разделы',        '',                false, true, '2026-09-02'],
  ['flowmeter.view',      'Расходомеры — просмотр',         'Отображение раздела «Расходомеры хозрасчётные» (просмотр данных)',                                     'Расходомеры',    '',                false, true, '2026-09-02'],
  ['flowmeter.input',     'Расходомеры — ввод показаний',   'Ввод показаний (сутки/месяц) в разделе «Расходомеры хозрасчётные»',                                    'Расходомеры',    '',                false, true, '2026-09-02'],
  ['workschedule.view',   'График работы — просмотр',       'Просмотр раздела «График работы»: кнопки и диалоги скрыты, доступен только выбор года и месяца',        'График работы',  '',                false, true, '2026-09-02'],
  ['workschedule.edit',   'График работы — внесение',       'Внесение данных в разделе «График работы»: сотрудники, инструктажи, отпуска (подразумевает просмотр)',  'График работы',  '',                false, true, '2026-09-02']
];

// Матрица: role_id → perm_id → true/false.
var INIT_MATRIX = {
  'zapret':       {},
  'common':       { 'calc.view': true },
  'itr_tokem':    { 'calc.view': true, 'kipios.restricted': true, 'whatsnew.view': true },
  'kip8':         { 'calc.view': true, 'library.view': true, 'secret.view': true, 'whatsnew.view': true },
  'kip8_pro':     { 'calc.view': true, 'library.view': true, 'secret.view': true, 'whatsnew.view': true, 'flowmeter.view': true },
  'kip_ios':      { 'calc.view': true, 'library.view': true, 'kipios.view': true, 'secret.view': true, 'whatsnew.view': true },
  'kip_ios_pro':  { 'calc.view': true, 'library.view': true, 'kipios.view': true, 'secret.view': true, 'whatsnew.view': true, 'cablejournal.edit': true },
  'kip_ios_duty': { 'calc.view': true, 'library.view': true, 'kipios.view': true, 'secret.view': true, 'whatsnew.view': true, 'flowmeter.view': true, 'flowmeter.input': true },
  'itr8':         { 'calc.view': true, 'library.view': true, 'kipios.view': true, 'secret.view': true, 'whatsnew.view': true, 'flowmeter.view': true },
  'itr8_pro':     { 'calc.view': true, 'library.view': true, 'kipios.view': true, 'secret.view': true, 'whatsnew.view': true, 'flowmeter.view': true, 'workschedule.view': true },
  'itr_ios':      { 'calc.view': true, 'library.view': true, 'kipios.view': true, 'secret.view': true, 'whatsnew.view': true, 'flowmeter.view': true, 'cablejournal.edit': true, 'flowmeter.input': true },
  'admin':        { 'calc.view': true, 'library.view': true, 'kipios.view': true, 'secret.view': true, 'whatsnew.view': true, 'charts.view': true, 'cablejournal.edit': true, 'admin.panel': true, 'flowmeter.view': true, 'flowmeter.input': true, 'workschedule.view': true, 'workschedule.edit': true }
};

// ==========================================================================
// ГЛАВНАЯ ФУНКЦИЯ (запустить её один раз в редакторе Apps Script)
// ==========================================================================

function roleMatrixInit() {
  var ss = SpreadsheetApp.getActive();
  if (!ss) {
    if (FALLBACK_SPREADSHEET_ID.indexOf('placeholder') !== -1) {
      throw new Error('Скрипт не привязан к таблице. Откройте Apps Script из таблицы KIP8_Access (Расширения → Apps Script) или укажите FALLBACK_SPREADSHEET_ID в начале файла.');
    }
    ss = SpreadsheetApp.openById(FALLBACK_SPREADSHEET_ID);
  }

  // --- Идемпотентность: не перезаписывать существующее ---
  if (ss.getSheetByName('matrix')) {
    var msg = 'Лист «matrix» уже существует — инициализация НЕ выполнена (ничего не изменено). ' +
      'Для пересоздания удалите листы matrix / permissions / roles вручную и запустите снова.';
    Logger.log(msg);
    return msg;
  }

  // --- Самопроверка данных на консистентность ---
  var check = _validateInitData();
  if (check !== true) { throw new Error('Ошибка в данных скрипта: ' + check); }

  var created = [];
  _createMatrixSheet(ss);      created.push('matrix');
  _createPermissionsSheet(ss); created.push('permissions');
  _createRolesSheet(ss);       created.push('roles');

  var summary = 'Готово. Созданы листы: ' + created.join(', ') +
    '. Прав: ' + INIT_PERMISSIONS.length + ', ролей: ' + INIT_ROLES.length + '.' +
    ' Проверьте галочки в «matrix» и следуйте инструкции на строках 1–3 листа.';
  Logger.log(summary);
  return summary;
}

// ==========================================================================
// ВНУТРЕННИЕ ФУНКЦИИ
// ==========================================================================

function _validateInitData() {
  var permIds = {};
  for (var i = 0; i < INIT_PERMISSIONS.length; i++) { permIds[INIT_PERMISSIONS[i][0]] = true; }
  var roleIds = {};
  for (var j = 0; j < INIT_ROLES.length; j++) { roleIds[INIT_ROLES[j][0]] = true; }

  // Матрица: все perm_id и role_id известны?
  for (var rid in INIT_MATRIX) {
    if (!roleIds[rid]) return 'роль «' + rid + '» из матрицы отсутствует в INIT_ROLES';
    var perms = INIT_MATRIX[rid];
    for (var pid in perms) {
      if (!permIds[pid]) return 'право «' + pid + '» роли «' + rid + '» отсутствует в INIT_PERMISSIONS';
    }
  }
  // У каждой роли из реестра есть строка в матрице?
  for (var r2 = 0; r2 < INIT_ROLES.length; r2++) {
    if (!INIT_MATRIX.hasOwnProperty(INIT_ROLES[r2][0])) {
      return 'роль «' + INIT_ROLES[r2][0] + '» отсутствует в INIT_MATRIX';
    }
  }
  // Админ: панель администратора обязана быть включена (защита от самоблокировки)
  if (!(INIT_MATRIX['admin'] && INIT_MATRIX['admin']['admin.panel'] === true)) {
    return 'роль «admin» должна иметь право admin.panel';
  }
  return true;
}

function _headerStyle(range, bg, bold) {
  range.setBackground(bg)
       .setFontWeight(bold ? 'bold' : 'normal')
       .setFontColor('#ffffff')
       .setVerticalAlignment('middle');
}

function _softProtect(range, description) {
  try {
    var p = range.protect().setDescription(description);
    if (p.canSetWarningOnly && p.canSetWarningOnly()) { p.setWarningOnly(true); }
  } catch (e) {
    Logger.log('Защита диапазона не установлена (не критично): ' + e);
  }
}

function _createMatrixSheet(ss) {
  var sheet = ss.insertSheet('matrix');
  sheet.setTabColor('#2d7d46');

  var nRoles = INIT_ROLES.length;
  var nPerms = INIT_PERMISSIONS.length;

  // r1: заголовок
  var r1 = sheet.getRange('A1:' + _colLetter(2 + nPerms) + '1');
  r1.merge().setValue('ЛИСТ: matrix — МАТРИЦА ДОСТУПА РОЛЕЙ (роль × право; галочка = доступ разрешён)')
    .setFontWeight('bold').setFontSize(12).setVerticalAlignment('middle');
  _headerStyle(r1, '#1a3c5e', true);

  // r2: инструкция
  sheet.getRange('A2').setValue(
    'ИНСТРУКЦИЯ: источник истины для системы доступа приложения. Строка 4 — технические ID (НЕ переименовывать, не удалять), строка 5 — названия. ' +
    'Колонка A — role_id (технический, не менять), колонка B — название роли (должно ТОЧНО совпадать с role в листе users). ' +
    'НОВОЕ ПРАВО: добавить колонку (строка 4 = perm_id, строка 5 = название) и строку в лист permissions. ' +
    'НОВАЯ РОЛЬ: добавить строку ниже последней (A = role_id, B = название) и строку в лист roles. ' +
    'Роль «Админ» всегда сохраняет все права. Задвоение ID недопустимо.')
    .setWrap(true).setFontSize(9).setItalic(true).setFontColor('#333333');
  sheet.setRowHeight(2, 90);

  // r3: версия/дата
  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd.MM.yyyy');
  sheet.getRange('A3').setValue('Сгенерировано: ' + today + ' • версия матрицы: 1 • Task 293 • одноразовый скрипт RoleMatrixInit.gs')
    .setFontSize(9).setFontColor('#777777');

  // r4: технические заголовки
  var head4 = ['role_id', 'role_name'];
  for (var p = 0; p < nPerms; p++) { head4.push(INIT_PERMISSIONS[p][0]); }
  var r4 = sheet.getRange(4, 1, 1, 2 + nPerms);
  r4.setValues([head4]);
  _headerStyle(r4, '#4a4a4a', false);
  r4.setFontFamily('Consolas').setFontSize(9).setWrap(false);

  // r5: человекочитаемые названия
  var head5 = ['', 'Роль'];
  for (var p2 = 0; p2 < nPerms; p2++) { head5.push(INIT_PERMISSIONS[p2][1]); }
  var r5 = sheet.getRange(5, 1, 1, 2 + nPerms);
  r5.setValues([head5]);
  _headerStyle(r5, '#1a3c5e', true);
  r5.setWrap(true).setHorizontalAlignment('center').setVerticalAlignment('bottom');

  // r6+: роли и значения
  var values = [];
  for (var r = 0; r < nRoles; r++) {
    var rid = INIT_ROLES[r][0];
    var row = [rid, INIT_ROLES[r][1]];
    for (var c = 0; c < nPerms; c++) {
      var pid = INIT_PERMISSIONS[c][0];
      row.push(INIT_MATRIX[rid][pid] === true);
    }
    values.push(row);
  }
  var dataRange = sheet.getRange(6, 1, nRoles, 2 + nPerms);
  dataRange.setValues(values);
  dataRange.setHorizontalAlignment('center');
  sheet.getRange(6, 1, nRoles, 1).setFontFamily('Consolas').setFontSize(9).setHorizontalAlignment('left');
  sheet.getRange(6, 2, nRoles, 1).setFontWeight('bold').setHorizontalAlignment('left');

  // Чекбоксы на область значений
  sheet.getRange(6, 3, nRoles, nPerms)
    .setDataValidation(SpreadsheetApp.newDataValidation().requireCheckbox().setAllowInvalid(false).build())
    .setHorizontalAlignment('center');

  // Визуальное оформление
  sheet.setColumnWidth(1, 110);           // role_id
  sheet.setColumnWidth(2, 130);           // Роль
  for (var w = 3; w <= 2 + nPerms; w++) { sheet.setColumnWidth(w, 64); }
  sheet.setFrozenRows(5);
  sheet.setFrozenColumns(2);
  sheet.getRange(6, 1, nRoles, 1).setBackground('#f5f5f5');
  sheet.getRange(6, 2, nRoles, 1).setBackground('#eef3f8');
  // Чередование строк для читаемости
  for (var z = 0; z < nRoles; z++) {
    if (z % 2 === 1) { sheet.getRange(6 + z, 3, 1, nPerms).setBackground('#fafafa'); }
    if (INIT_ROLES[z][3] === true) { // системные роли — выделить
      sheet.getRange(6 + z, 1, 1, 2 + nPerms).setBorder(true, true, true, true, true, true, '#c9a227', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    }
  }
  sheet.getRange('B5').setBorder(true, null, null, null, null, null, '#ffffff', SpreadsheetApp.BorderStyle.SOLID);

  // Мягкая защита технических строк и колонок
  _softProtect(sheet.getRange(1, 1, 5, 2 + nPerms), 'matrix: строки 1–5 (заголовки и ID) — не редактировать');
  _softProtect(sheet.getRange(6, 1, nRoles, 2), 'matrix: колонки A–B (ID и названия ролей) — менять только осознанно');
}

function _createPermissionsSheet(ss) {
  var sheet = ss.insertSheet('permissions');
  sheet.setTabColor('#8a8a8a');

  var n = INIT_PERMISSIONS.length;
  var r1 = sheet.getRange('A1:H1');
  r1.merge().setValue('ЛИСТ: permissions — реестр прав доступа (справочник)')
    .setFontWeight('bold').setFontSize(12);
  _headerStyle(r1, '#1a3c5e', true);
  sheet.getRange('A2').setValue(
    'ИНСТРУКЦИЯ: справочник всех прав приложения, расширяется при добавлении новых разделов/функционалов. ' +
    'perm_id (A) — технический ID, латиница, НЕ переименовывать и не удалять (на него ссылается matrix строка 4). ' +
    'Название (B) — показывается в админ-панели. Конфликт с (E) — perm_id через запятую, с которыми право взаимоисключается. ' +
    'Системное (F) — право, которое нельзя отключать (admin.panel). Активно (G) — временное выключение права без удаления.')
    .setWrap(true).setFontSize(9).setItalic(true).setFontColor('#333333');
  sheet.setRowHeight(2, 70);
  sheet.getRange('A3').setValue('Сгенерировано: ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd.MM.yyyy') + ' • Task 293')
    .setFontSize(9).setFontColor('#777777');

  var headers = ['perm_id', 'Название', 'Описание', 'Группа', 'Конфликт с', 'Системное', 'Активно', 'Добавлено'];
  var r4 = sheet.getRange(4, 1, 1, headers.length);
  r4.setValues([headers]);
  _headerStyle(r4, '#4a4a4a', true);

  sheet.getRange(5, 1, n, 8).setValues(INIT_PERMISSIONS);
  sheet.getRange(5, 1, n, 1).setFontFamily('Consolas').setFontSize(9);
  sheet.getRange(5, 2, n, 1).setFontWeight('bold');
  sheet.getRange(5, 4, n, 1).setWrap(false);
  sheet.getRange(5, 3, n, 1).setWrap(true);

  sheet.setColumnWidth(1, 150); sheet.setColumnWidth(2, 160);
  sheet.setColumnWidth(3, 380); sheet.setColumnWidth(4, 110);
  sheet.setColumnWidth(5, 130); sheet.setColumnWidth(6, 90);
  sheet.setColumnWidth(7, 80);  sheet.setColumnWidth(8, 90);
  sheet.setFrozenRows(4); sheet.setFrozenColumns(2);

  _softProtect(sheet.getRange(4, 1, 1, 8), 'permissions: строка заголовков — не редактировать');
}

function _createRolesSheet(ss) {
  var sheet = ss.insertSheet('roles');
  sheet.setTabColor('#8a8a8a');

  var n = INIT_ROLES.length;
  var r1 = sheet.getRange('A1:E1');
  r1.merge().setValue('ЛИСТ: roles — реестр ролей (справочник)')
    .setFontWeight('bold').setFontSize(12);
  _headerStyle(r1, '#1a3c5e', true);
  sheet.getRange('A2').setValue(
    'ИНСТРУКЦИЯ: Название роли (B) должно ТОЧНО совпадать со значением role в листе users — по нему сервер находит роль пользователя. ' +
    'Системные роли (D): «Запрет», «Общий доступ», «Админ» — защищены от удаления. Роль «Админ» всегда имеет все права (строка в matrix не нужна «полная» — сервер гарантирует). ' +
    'Порядок (E) — сортировка в админ-панели. role_id (A) — технический, НЕ переименовывать.')
    .setWrap(true).setFontSize(9).setItalic(true).setFontColor('#333333');
  sheet.setRowHeight(2, 70);
  sheet.getRange('A3').setValue('Сгенерировано: ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd.MM.yyyy') + ' • Task 293')
    .setFontSize(9).setFontColor('#777777');

  var headers = ['role_id', 'Название', 'Описание', 'Системная', 'Порядок'];
  var r4 = sheet.getRange(4, 1, 1, headers.length);
  r4.setValues([headers]);
  _headerStyle(r4, '#4a4a4a', true);

  sheet.getRange(5, 1, n, 5).setValues(INIT_ROLES);
  sheet.getRange(5, 1, n, 1).setFontFamily('Consolas').setFontSize(9);
  sheet.getRange(5, 2, n, 1).setFontWeight('bold');
  sheet.getRange(5, 3, n, 1).setWrap(true);

  sheet.setColumnWidth(1, 120); sheet.setColumnWidth(2, 140);
  sheet.setColumnWidth(3, 420); sheet.setColumnWidth(4, 90);
  sheet.setColumnWidth(5, 70);
  sheet.setFrozenRows(4); sheet.setFrozenColumns(2);

  _softProtect(sheet.getRange(4, 1, 1, 5), 'roles: строка заголовков — не редактировать');
}

// Буква колонки по номеру (1 = A, 2 = B, …)
function _colLetter(n) {
  var s = '';
  while (n > 0) {
    var m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}
