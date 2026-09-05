// ============================================================
// WorkSchedule.gs — График работы персонала цеха №8 пр-ва ИОС
// ============================================================
// Развернуть в том же Apps Script проекте, где находятся
//   Code.gs, Utils.gs, Flowmeter.gs, CableJournal.gs.
//
// Эндпоинты (вызываются через doPost в Code.gs):
//   workSchedule.getStatusCodes  — легенда кодов (16 шт., Task 298)
//   workSchedule.getPatterns     — шаблоны ротации + дни цикла
//   workSchedule.listEmployees   — справочник сотрудников
//   workSchedule.listEntries     — записи графика за месяц
//   workSchedule.listTrainings   — плановые инструктажи (с фильтром по месяцу)
//   workSchedule.generateMonth   — СФОРМИРОВАТЬ шахматку на месяц
//   workSchedule.setManualEntry   — upsert ручной правки (Б/ОТ/П/замещение)
//   workSchedule.deleteEntry     — удалить ручную запись
//   workSchedule.addEmployee      — добавить нового сотрудника
//   workSchedule.dismissEmployee   — уволить: дата_увольнения (H) + в_архиве=1 (I)
//   workSchedule.addTraining      — добавить плановое мероприятие
//   workSchedule.deleteTraining   — удалить мероприятие
//   workSchedule.listVacations    — план отпусков (Task 274, лист «Отпуска»)
//   workSchedule.addVacation      — добавить период отпуска (часть 1..3)
//   workSchedule.deleteVacation   — удалить период отпуска
//
// Авторизация — по тому же паттерну, что Flowmeter.gs:
//   Utils.findSessionByToken(token) → session
//   Utils.findUserById(session.user_id) → user
//
// Google Таблица — ОТДЕЛЬНАЯ от hozraschet:
//   SPREADSHEET_ID = '1MQtW-CWCmjlu-SAeVBllKDP6NRkiOkmW-7xgOjHskWY'
//
// Листы (9):
//   README, Сотрудники, Коды_статусов, Шаблоны_ротации,
//   Дни_цикла, Инструктажи, Записи_графика, Сводка_по_месяцам,
//   Отпуска (Task 274)
//
// Task 304: таб_№ во ВСЕХ листах хранится ТЕКСТОМ. appendRow/
//   setValues пишут значения по USER_ENTERED-семантике Google
//   Sheets — числоподобная строка «0871» становится ЧИСЛОМ 871
//   (ведущий ноль теряется, таб перестаёт сопоставляться со
//   справочником «Сотрудники»: бейдж мероприятия молча пропадал).
//   Теперь перед записью таб-ячейкам ставится текстовый формат '@'
//   (см. _appendRowKeepText), а generateMonth возвращает warnings —
//   мероприятия/отпуска с таб_номер не из справочника видны в тосте
//   «Сформировать» (раньше это была тихая ошибка). Починка уже
//   испорченных ячеек — scripts/TabNumbersFix.gs (fixTabNumbers).
//
// Структура листа «Сотрудники» (заголовки в строке 1, данные со строки 2):
//   A: таб_номер              — табельный номер (строка, PK)
//   B: ФИО
//   C: тип                — 'сменный' или 'дневной'
//   D: смена              — 1..5 для сменного, пусто для дневного
//   E: шаблон_ротации     — FK на Шаблоны_ротации.id_шаблона (int)
//   F: старт_цикла        — Date
//   G: дата_приёма        — Date
//   H: дата_увольнения    — Date (может быть пусто)
//   I: в_архиве           — 0/1
//   J: должность
//   K: комментарий
//
// Структура листа «Коды_статусов» (Task 298 — состав по Т-12/Т-13):
//   A: код (Д/Д8/Д7,2/Н/д/н/ОТ/У/ОВ/Б/ПР/И/ОБ/ПЗ/*/.)
//   B: название
//   C: цвет_заливки (HEX)
//   «.» — плановый выходной день (явная запись). «Д8» — дневная
//   8-часовая, «Д7,2» — сокращённая (пятница/предпраздничный).
//   Строчные «д»/«н» — работа в выходные/праздники (коды
//   регистрозависимы!). setManualEntry валидирует код по этому
//   листу (Task 298) — см. _validateStatusCode.
//
// Структура листа «Шаблоны_ротации»:
//   A: id_шаблона (1..N)
//   B: название
//   C: цикл_дней (int)
//   D: описание
//
// Структура листа «Дни_цикла»:
//   A: id_шаблона (FK)
//   B: день_цикла (1..N)
//   C: статус (код; пусто = выходной)
//
// Структура листа «Инструктажи»:
//   A: id (auto-increment)
//   B: таб_номер (FK на Сотрудники)
//   C: тип (инструктаж/обучение/проверка_знаний/прогул/примечание —
//      Task 306: два последних отображаются кодами ПР и *)
//   D: тема
//   E: дата_начала (Date)
//   F: дата_окончания (Date)
//   G: длительность_дней (int)
//   H: комментарий
//
// Структура листа «Записи_графика» (ГЛАВНАЯ БД):
//   A: дата (Date)
//   B: таб_номер (FK на Сотрудники — кто работал)
//   C: статус (код)
//   D: переработка (0/1)
//   E: праздник (0/1)
//   F: источник (авто/руч)
//   G: дата_обновления (Date)
//   H: замещает (FK на Сотрудники — кого замещали; может быть пусто)
//   I: инструкция (FK на Инструктажи.id; может быть пусто)
//   J: комментарий
//
// Структура листа «Отпуска» (Task 274 — план периодов отпусков):
//   A: id (auto-increment)
//   B: таб_номер (FK на Сотрудники)
//   C: часть (1..3 — отпуска делятся на 2–3 части в год)
//   D: дата_начала (Date)
//   E: дата_окончания (Date)
//   F: комментарий
//   Период задаёт автоматическую расстановку «О» (Отпуск) в
//   Записи_графика при «Сформировать» (generateMonth, шаг 4.5):
//   приоритет статуса дня — ручная правка > отпуск > плановая смена >
//   мероприятие (И/ОБ/ПЗ — только на день БЕЗ плановой смены).
//   Task 303: мероприятие больше НЕ затирает плановую смену — на
//   сменных днях смена остаётся кодом ячейки, а мероприятие (И/ОБ/ПЗ)
//   показывается бейджем на клиенте (данные — лист «Инструктажи»,
//   связка — колонка I «инструкция»).
// ============================================================

var WorkSchedule = {

  // ID Google Таблицы графика работы (отдельная от hozraschet)
  SPREADSHEET_ID: '1MQtW-CWCmjlu-SAeVBllKDP6NRkiOkmW-7xgOjHskWY',

  // Имена листов
  EMPLOYEES_SHEET:    'Сотрудники',
  STATUS_CODES_SHEET: 'Коды_статусов',
  PATTERNS_SHEET:     'Шаблоны_ротации',
  PATTERN_DAYS_SHEET: 'Дни_цикла',
  TRAININGS_SHEET:    'Инструктажи',
  ENTRIES_SHEET:      'Записи_графика',
  SUMMARY_SHEET:      'Сводка_по_месяцам',
  // Task 274: лист «Отпуска» — план периодов (2–3 части на год).
  // Данные листа определяют автоматическое заполнение «О» в шахматке.
  VACATIONS_SHEET:    'Отпуска',

  // Строка, с которой начинаются данные
  DATA_START_ROW: 2,

  // Роли с правом чтения графика (LEGACY-запас, Task 295: рабочая
  // проверка — право workschedule.view из МАТРИЦЫ KIP8_Access)
  // Task 204: только Админ. Ранее было ['КИП ИОС', 'КИП ИОС pro', 'КИП ИОС дежурный',
  // 'ИТР8', 'ИТР8 pro', 'ИТР ИОС', 'Админ'] — доступ сужен по запросу заказчика.
  // ИЗМЕНЕНИЕ ПОВЕДЕНИЯ Task 295 (осознанное, матрица Task 293):
  // «ИТР8 pro» получает ПРОСМОТР графика (workschedule.view=✓ в матрице).
  READ_ROLES: ['Админ'],

  // Роли с правом записи (генерация, ручные правки, добавление сотрудников/инструктажей)
  // (LEGACY-запас, Task 295: рабочая проверка — workschedule.edit из МАТРИЦЫ;
  // в матрице право только у «Админа» — совпадает со списком)
  WRITE_ROLES: ['Админ'],

  // Task 295: флаг однократного предупреждения о legacy-режиме
  _rmgLegacyWarned: false,

  // Соответствие тип мероприятия → код статуса в Записи_графика.
  // Task 306 (заявка): к И/ОБ/ПЗ добавлены «прогул» → ПР и
  // «примечание» → * — новые типы в форме «Новое мероприятие»
  // клиента. Оба кода уже есть в листе «Коды_статусов», так что
  // цвета/названия подтягиваются без правок справочника.
  TRAINING_TYPE_TO_STATUS: {
    'инструктаж':       'И',
    'обучение':         'ОБ',
    'проверка_знаний':  'ПЗ',
    'прогул':           'ПР',
    'примечание':       '*'
  },

  // Task 303: код слоя мероприятий (И/ОБ/ПЗ, Task 306: + ПР и *).
  // Такой код записывается в Записи_графика ТОЛЬКО на дни без
  // плановой смены (мероприятие в выходной по циклу). На сменных
  // днях мероприятие не затирает смену: смена — основной код
  // ячейки, мероприятие показывается на клиенте бейджем (данные —
  // лист «Инструктажи», связка — колонка I). ПР и * — такие же
  // авто-коды: шаг 4.6 снимает их строки при удалении/переносе
  // мероприятия; РУЧНЫЕ строки с ПР/* (прогул/примечание,
  // поставленные через попап ячейки) не трогаются — как и ручные И.
  _isEventStatusCode: function(status) {
    return status === 'И' || status === 'ОБ' || status === 'ПЗ' ||
           status === 'ПР' || status === '*';
  },

  // ============================================================
  // Утилиты
  // ============================================================

  _getSheet: function(name) {
    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    var sheet = ss.getSheetByName(name);
    return sheet;
  },

  // Task 304: дописать строку в ЛИСТ с текстовым форматом таб-колонок.
  // ЗАЧЕМ: appendRow/setValues применяют USER_ENTERED-семантику
  // Google Sheets — числоподобная строка «0871» становится ЧИСЛОМ
  // 871, ведущий ноль теряется. Таб_№ хранится текстом во всех
  // листах (как в справочнике «Сотрудники»): до записи значения
  // нужным ячейкам ставится формат '@' (plain text), затем строка
  // пишется одним setValues (позиция = getLastRow()+1 — та же, куда
  // писал бы appendRow). textCols — 1-based номера текстовых колонок.
  _appendRowKeepText: function(sheet, rowValues, textCols) {
    var newRow = sheet.getLastRow() + 1;
    if (textCols && textCols.length) {
      for (var i = 0; i < textCols.length; i++) {
        sheet.getRange(newRow, textCols[i]).setNumberFormat('@');
      }
    }
    sheet.getRange(newRow, 1, 1, rowValues.length).setValues([rowValues]);
    return newRow;
  },

  _requireRead: function(token) {
    // Task 295: право workschedule.view из МАТРИЦЫ KIP8_Access
    // (лист matrix, строка 4). ИЗМЕНЕНИЕ ПОВЕДЕНИЯ (осознанное,
    // матрица Task 293): «ИТР8 pro» теперь видит график (ранее Task 204 —
    // только Админ). Legacy-список READ_ROLES — только если
    // RoleMatrixGate.gs не задеплоен.
    if (typeof rmRequirePerm === 'function') {
      var g = rmRequirePerm(token, 'workschedule.view', 'WorkSchedule');
      if (!g.ok) return { error: { ok: false, error: g.error } };
      return { user: g.user };
    }
    this._rmgLegacyWarn('WorkSchedule._requireRead');
    if (!token) return { error: { ok: false, error: 'no_session' } };
    var session = Utils.findSessionByToken(token);
    if (!session) return { error: { ok: false, error: 'no_session' } };
    var user = Utils.findUserById(session.user_id);
    if (!user) return { error: { ok: false, error: 'no_session' } };
    if (this.READ_ROLES.indexOf(user.role) === -1) {
      return { error: { ok: false, error: 'access_denied' } };
    }
    return { user: user };
  },

  _requireWrite: function(token) {
    // Task 295: право workschedule.edit из МАТРИЦЫ. В матрице право
    // только у «Админа» — поведение не меняется. Матрица недоступна →
    // отказ для всех (fail-closed, включая админа, до восстановления).
    if (typeof rmRequirePerm === 'function') {
      var g = rmRequirePerm(token, 'workschedule.edit', 'WorkSchedule');
      if (!g.ok) return { error: { ok: false, error: g.error } };
      return { user: g.user };
    }
    this._rmgLegacyWarn('WorkSchedule._requireWrite');
    if (!token) return { error: { ok: false, error: 'no_session' } };
    var session = Utils.findSessionByToken(token);
    if (!session) return { error: { ok: false, error: 'no_session' } };
    var user = Utils.findUserById(session.user_id);
    if (!user) return { error: { ok: false, error: 'no_session' } };
    if (this.WRITE_ROLES.indexOf(user.role) === -1) {
      try {
        Utils.audit(user.email, 'WORKSCHEDULE_ACCESS_DENIED', '', '',
          'Роль "' + user.role + '" не имеет прав на график работы');
      } catch (e) { /* ignore */ }
      return { error: { ok: false, error: 'access_denied' } };
    }
    return { user: user };
  },

  // Task 295: однократное предупреждение о работе без матрицы
  _rmgLegacyWarn: function(where) {
    if (this._rmgLegacyWarned) return;
    this._rmgLegacyWarned = true;
    try {
      console.error('[WorkSchedule] RoleMatrixGate.gs не задеплоен — ' + where +
        ' работает по legacy-списку READ_ROLES/WRITE_ROLES. ' +
        'Вставьте RoleMatrix.gs + RoleMatrixGate.gs в проект.');
    } catch (e) { /* ignore */ }
  },

  // Конвертация строки ISO YYYY-MM-DD → Date (без timezone-сдвига)
  _parseIsoDate: function(s) {
    if (!s) return null;
    if (s instanceof Date) return s;
    var parts = String(s).split('-');
    if (parts.length !== 3) return null;
    var y = parseInt(parts[0], 10);
    var m = parseInt(parts[1], 10);
    var d = parseInt(parts[2], 10);
    if (isNaN(y) || isNaN(m) || isNaN(d)) return null;
    return new Date(y, m - 1, d);
  },

  // Значение ячейки листа → Date (Task 279).
  // Ячейка может хранить дату как настоящий Date (формат даты Google
  // Таблиц) или как ТЕКСТ — «10.08.2026», «1.8.26», «2026-08-10»
  // (ручной ввод в локали, не распознавшей дату). Раньше текст
  // отбрасывался по instanceof Date — периоды молча терялись и
  // «Сформировать» не проставлял «О». Теперь текст парсится.
  // null — значение не похоже на дату.
  _parseSheetDate: function(v) {
    if (v instanceof Date) return v;
    if (v === null || v === undefined) return null;
    var s = String(v).trim();
    if (!s) return null;
    var m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);        // ISO
    if (m) return this._safeDate(+m[1], +m[2], +m[3]);
    m = s.match(/^(\d{1,2})[.\/](\d{1,2})[.\/](\d{4})$/);  // dd.mm.yyyy
    if (m) return this._safeDate(+m[3], +m[2], +m[1]);
    m = s.match(/^(\d{1,2})[.\/](\d{1,2})[.\/](\d{2})$/);   // dd.mm.yy
    if (m) return this._safeDate(2000 + +m[3], +m[2], +m[1]);
    return null;
  },

  // new Date с проверкой реальности даты: JS «катит» несуществующие
  // даты (32.01 → 1.02) — сверяем компоненты назад
  _safeDate: function(y, mo, d) {
    if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
    if (y < 1900 || y > 2100) return null;
    var dt = new Date(y, mo - 1, d);
    if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) {
      return null;
    }
    return dt;
  },

  // Date → ISO YYYY-MM-DD (для ключей индекса)
  _toIsoDate: function(dt) {
    if (!dt) return null;
    var y = dt.getFullYear();
    var m = ('' + (dt.getMonth() + 1)).padStart(2, '0');
    var d = ('' + dt.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + d;
  },

  // Количество дней в месяце
  _daysInMonth: function(year, month) {
    return new Date(year, month, 0).getDate();
  },

  // ============================================================
  // Чтение справочников
  // ============================================================

  // workSchedule.getStatusCodes
  // payload: { token }
  // returns: { ok:true, data: { codes: [{code, name, color}, ...] } }
  getStatusCodes: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.STATUS_CODES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.STATUS_CODES_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { codes: [] } };

    var values = sheet.getRange(2, 1, lastRow - 1, 3).getValues();
    var codes = [];
    for (var i = 0; i < values.length; i++) {
      var row = values[i];
      if (!row[0]) continue;
      codes.push({
        code:  String(row[0]).trim(),
        name:  String(row[1] || '').trim(),
        color: String(row[2] || '').trim()
      });
    }
    return { ok: true, data: { codes: codes } };
  },

  // workSchedule.getPatterns
  // payload: { token }
  // returns: { ok:true, data: { patterns: [{id, name, cycle, description, days:[{day, status}]}] } }
  getPatterns: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var pSheet = this._getSheet(this.PATTERNS_SHEET);
    var dSheet = this._getSheet(this.PATTERN_DAYS_SHEET);
    if (!pSheet || !dSheet) {
      return { ok: false, error: 'sheet_not_found' };
    }

    // Читаем шаблоны
    var pLast = pSheet.getLastRow();
    var patterns = [];
    if (pLast >= 2) {
      var pVals = pSheet.getRange(2, 1, pLast - 1, 4).getValues();
      for (var i = 0; i < pVals.length; i++) {
        var r = pVals[i];
        if (r[0] === '' || r[0] === null) continue;
        patterns.push({
          id:          parseInt(r[0], 10),
          name:        String(r[1] || '').trim(),
          cycle:       parseInt(r[2], 10),
          description: String(r[3] || '').trim(),
          days:        []
        });
      }
    }

    // Читаем дни циклов
    var dLast = dSheet.getLastRow();
    if (dLast >= 2) {
      var dVals = dSheet.getRange(2, 1, dLast - 1, 3).getValues();
      for (var j = 0; j < dVals.length; j++) {
        var dr = dVals[j];
        var pid = parseInt(dr[0], 10);
        if (isNaN(pid)) continue;
        for (var k = 0; k < patterns.length; k++) {
          if (patterns[k].id === pid) {
            patterns[k].days.push({
              day:    parseInt(dr[1], 10),
              status: dr[2] === '' || dr[2] === null ? '' : String(dr[2]).trim()
            });
            break;
          }
        }
      }
    }

    return { ok: true, data: { patterns: patterns } };
  },

  // workSchedule.listEmployees
  // payload: { token, includeArchived }
  // returns: { ok:true, data: { employees: [...] } }
  listEmployees: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.EMPLOYEES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.EMPLOYEES_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { employees: [] } };

    var values = sheet.getRange(2, 1, lastRow - 1, 11).getValues();
    var includeArchived = !!payload.includeArchived;
    var employees = [];
    for (var i = 0; i < values.length; i++) {
      var r = values[i];
      if (!r[0] && r[0] !== 0) continue;
      var archived = parseInt(r[8], 10) === 1;
      if (archived && !includeArchived) continue;
      employees.push({
        таб_номер:            String(r[0]).trim(),
        ФИО:             String(r[1] || '').trim(),
        тип:             String(r[2] || '').trim(),
        смена:           r[3] === '' || r[3] === null ? null : parseInt(r[3], 10),
        шаблон_ротации:  r[4] === '' || r[4] === null ? null : parseInt(r[4], 10),
        старт_цикла:     r[5] instanceof Date ? this._toIsoDate(r[5]) : null,
        дата_приёма:     r[6] instanceof Date ? this._toIsoDate(r[6]) : null,
        дата_увольнения: r[7] instanceof Date ? this._toIsoDate(r[7]) : null,
        в_архиве:        archived ? 1 : 0,
        должность:       String(r[9] || '').trim(),
        комментарий:     String(r[10] || '').trim()
      });
    }
    return { ok: true, data: { employees: employees } };
  },

  // workSchedule.listEntries
  // payload: { token, year, month }
  // returns: { ok:true, data: { entries: [...] } }
  listEntries: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var year  = parseInt(payload.year, 10);
    var month = parseInt(payload.month, 10);
    if (isNaN(year) || isNaN(month) || month < 1 || month > 12) {
      return { ok: false, error: 'invalid_month_year' };
    }

    var sheet = this._getSheet(this.ENTRIES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.ENTRIES_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { entries: [] } };

    // Читаем даты (A), таб_номер (B), статус (C), переработка (D), праздник (E),
    // источник (F), дата_обновления (G), замещает (H), инструкция (I), комментарий (J)
    var values = sheet.getRange(2, 1, lastRow - 1, 10).getValues();
    var monthStart = new Date(year, month - 1, 1);
    var monthEnd   = new Date(year, month, 1);  // не включительно

    var entries = [];
    for (var i = 0; i < values.length; i++) {
      var r = values[i];
      var dateCell = r[0];
      if (!(dateCell instanceof Date)) continue;
      if (dateCell < monthStart || dateCell >= monthEnd) continue;
      entries.push({
        дата:            this._toIsoDate(dateCell),
        таб_номер:           String(r[1] || '').trim(),
        статус:          String(r[2] || '').trim(),
        переработка:     parseInt(r[3], 10) === 1 ? 1 : 0,
        праздник:        parseInt(r[4], 10) === 1 ? 1 : 0,
        источник:        String(r[5] || '').trim(),
        дата_обновления: r[6] instanceof Date ? r[6].toISOString() : null,
        замещает:        r[7] === '' || r[7] === null ? null : String(r[7]).trim(),
        инструкция:      r[8] === '' || r[8] === null ? null : parseInt(r[8], 10),
        комментарий:     String(r[9] || '').trim(),
        _rowIndex:       i + 2  // 1-based номер строки в листе
      });
    }
    return { ok: true, data: { entries: entries } };
  },

  // workSchedule.listTrainings
  // payload: { token, year, month }  (если month не указан — все мероприятия года)
  // returns: { ok:true, data: { trainings: [...] } }
  listTrainings: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.TRAININGS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { trainings: [] } };

    var values = sheet.getRange(2, 1, lastRow - 1, 8).getValues();
    var year  = payload.year  ? parseInt(payload.year, 10)  : null;
    var month = payload.month ? parseInt(payload.month, 10) : null;
    var rangeStart = (year && month) ? new Date(year, month - 1, 1) : (year ? new Date(year, 0, 1) : null);
    var rangeEnd   = (year && month) ? new Date(year, month, 1) : (year ? new Date(year + 1, 0, 1) : null);

    var trainings = [];
    for (var i = 0; i < values.length; i++) {
      var r = values[i];
      if (!r[0] && r[0] !== 0) continue;
      var startDate = r[4];
      var endDate   = r[5];
      // Фильтр: мероприятие пересекается с диапазоном [rangeStart, rangeEnd)
      if (rangeStart && rangeEnd) {
        if (!(startDate instanceof Date) || !(endDate instanceof Date)) continue;
        if (endDate < rangeStart || startDate >= rangeEnd) continue;
      }
      trainings.push({
        id:                parseInt(r[0], 10),
        таб_номер:             String(r[1] || '').trim(),
        тип:               String(r[2] || '').trim(),
        тема:              String(r[3] || '').trim(),
        дата_начала:       startDate instanceof Date ? this._toIsoDate(startDate) : null,
        дата_окончания:    endDate instanceof Date ? this._toIsoDate(endDate) : null,
        длительность_дней: parseInt(r[6], 10) || 1,
        комментарий:       String(r[7] || '').trim()
      });
    }
    return { ok: true, data: { trainings: trainings } };
  },

  // workSchedule.listVacations (Task 274)
  // payload: { token, year }  (год не указан — все периоды листа)
  // Возвращает периоды, ПЕРЕСЕКАЮЩИЕСЯ с годом (границы года не
  // включаются в фильтр строго: период 29.12–11.01 попадает в оба года).
  // Task 279: id не обязателен (id: null у строк ручного заполнения),
  // даты читаются и из текстовых ячеек («10.08.2026») — см.
  // _parseSheetDate. Непарсируемые даты — строка пропускается.
  // returns: { ok:true, data: { vacations: [...] } }
  listVacations: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.VACATIONS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.VACATIONS_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { vacations: [] } };

    // Читаем id (A), таб_номер (B), часть (C), дата_начала (D),
    // дата_окончания (E), комментарий (F)
    var values = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
    var year = payload.year ? parseInt(payload.year, 10) : null;
    var yearStart = year ? new Date(year, 0, 1) : null;
    var yearEnd   = year ? new Date(year + 1, 0, 1) : null;  // не включительно

    var vacations = [];
    for (var i = 0; i < values.length; i++) {
      var r = values[i];
      // Task 279: «пустая строка» = нет ни id, ни таб_номера, ни даты
      // начала. Раньше требовался id — строки РУЧНОГО заполнения без
      // id (деплой-док Task 274 разрешал «id можно не заполнять»)
      // молча выбрасывались: план не показывался, «Сформировать» не
      // проставлял «О». Теперь id не обязателен (id: null — кнопка
      // «Удалить» на фронте скрыта; id присвоит vacationsInitSheet
      // или addVacation).
      if ((r[0] === '' || r[0] === null) && !String(r[1] || '').trim() &&
          !this._parseSheetDate(r[3])) continue;
      // Task 279: даты могут лежать текстом — парсим (см. _parseSheetDate)
      var startDate = this._parseSheetDate(r[3]);
      if (!startDate) continue;
      var endDate = this._parseSheetDate(r[4]) || startDate;
      // Период пересекается с годом?
      if (yearStart && (endDate.getTime() < yearStart.getTime() ||
                        startDate.getTime() >= yearEnd.getTime())) continue;
      var part = parseInt(r[2], 10);
      var vId = parseInt(r[0], 10);
      vacations.push({
        id:               isNaN(vId) ? null : vId,
        'таб_номер':      String(r[1] || '').trim(),
        часть:            isNaN(part) ? null : part,
        дата_начала:      this._toIsoDate(startDate),
        дата_окончания:   this._toIsoDate(endDate),
        дней:             Math.round((endDate.getTime() - startDate.getTime()) /
                                     (24 * 60 * 60 * 1000)) + 1,
        комментарий:      String(r[5] || '').trim()
      });
    }
    return { ok: true, data: { vacations: vacations } };
  },

  // ============================================================
  // ГЛАВНОЕ: generateMonth
  // ============================================================
  // payload: { token, year, month }
  // Algorithm:
  //   1. Загрузить сотрудников, шаблоны+дни, инструктажи месяца, записи месяца
  //   2. Построить индекс существующих записей: { "ISO|таб_номер": {entry, rowIndex} }
  //   3. Для каждого сотрудника с шаблоном:
  //        для каждого дня месяца → статус = pattern_day[day_of_cycle]
  //        если статус есть и в индексе НЕТ записи → вставить source=авто
  //   4. (Task 303) Прогон по инструктажам, пересекающим месяц:
  //        для каждого дня мероприятия в этом месяце:
  //          если есть ручная запись → пропустить (manual priority)
  //          если день со плановой сменой → смену НЕ затирать (Task 303:
  //            «два значения в ячейке» — смена остаётся основным кодом,
  //            мероприятие показывается бейджем на клиенте); смену
  //            ВОССТАНОВИТЬ, если генерация до Task 303 записала сюда
  //            И/ОБ/ПЗ; связка инструкция=id обновляется
  //          если день БЕЗ плановой смены и записи нет → вставить
  //            source=авто, статус=И/ОБ/ПЗ/ПР/* (Task 306),
  //            инструкция=id (как до Task 303)
  //   4.5 (Task 274) Отпуска — лист «Отпуска», ВЫСШИЙ приоритет среди
  //        авто-источников: для каждого дня периода в этом месяце:
  //          ручная запись → не трогать; авто-запись (смена/инструктаж/
  //          устаревший код) → статус='ОТ', инструкция=∅; нет записи →
  //          вставить source=авто, статус='ОТ'. Все календарные дни
  //          периода (включая Сб/Вс) отмечаются «ОТ» — отпуск в
  //          календарных днях. (Task 298: код отпуска «О» → «ОТ»
  //          по официальной семантике Т-12/Т-13.)
  //          Устаревшие авто-'ОТ' записи месяца (период изменён/удалён
  //          в листе «Отпуска») — удаляются: повторное «Сформировать»
  //          даёт актуальную расстановку (идемпотентность).
  //   4.6 (Task 303) Сверка устаревших строк мероприятий: авто-строки
  //        с кодом И/ОБ/ПЗ/ПР/* (Task 306), чей день больше не покрыт
  //        мероприятием (удалено/перенесено в листе «Инструктажи»):
  //        день со плановой сменой → восстановить смену; день без
  //        смены → удалить строку.
  //        Ручные строки не трогаются. Повторная генерация сходится к
  //        текущему состоянию листов (идемпотентность).
  //   5. Аудит, возврат {generated, updated, removed, perEmployee}
  // ============================================================
  generateMonth: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var year  = parseInt(payload.year, 10);
    var month = parseInt(payload.month, 10);
    if (isNaN(year) || isNaN(month) || month < 1 || month > 12) {
      return { ok: false, error: 'invalid_month_year' };
    }

    var entriesSheet = this._getSheet(this.ENTRIES_SHEET);
    if (!entriesSheet) return { ok: false, error: 'sheet_not_found: ' + this.ENTRIES_SHEET };

    // 1. Загрузка данных
    var employees = this.listEmployees({ token: payload.token, includeArchived: false });
    if (!employees.ok) return employees;
    var emps = employees.data.employees;

    var pats = this.getPatterns({ token: payload.token });
    if (!pats.ok) return pats;
    var patterns = pats.data.patterns;
    var patternsById = {};
    for (var pi = 0; pi < patterns.length; pi++) {
      patternsById[patterns[pi].id] = patterns[pi];
    }

    var trs = this.listTrainings({ token: payload.token, year: year, month: month });
    if (!trs.ok) return trs;
    var trainings = trs.data.trainings;

    // Существующие записи месяца (для построения индекса)
    var existing = this.listEntries({ token: payload.token, year: year, month: month });
    if (!existing.ok) return existing;
    var existingEntries = existing.data.entries;
    var entryIndex = {};  // "ISO|таб_номер": { entry, rowIndex }
    for (var ei = 0; ei < existingEntries.length; ei++) {
      var e = existingEntries[ei];
      var key = e.дата + '|' + e.таб_номер;
      entryIndex[key] = e;
    }

    var monthStart = new Date(year, month - 1, 1);
    var daysInMonth = this._daysInMonth(year, month);

    // 2. Подготовить массивы для batch-вставки и batch-обновления
    var toInsert = [];  // [[дата, таб_номер, статус, 0/1, 0/1, 'авто', дата_обновления, '', null, ''], ...]
    var toUpdate = [];  // [{ rowIndex, status, instruction_id }, ...]

    var perEmployee = {};
    for (var ei2 = 0; ei2 < emps.length; ei2++) perEmployee[emps[ei2]['таб_номер']] = { generated: 0, updated: 0, skipped: 0 };

    // Task 303: плановая смена дня по шаблону (НЕЗАВИСИМО от наличия
    // записи): "ISO|таб_номер" → код. Нужен шагам 4/4.6: мероприятие
    // не должно затирать смену, а устаревший И/ОБ/ПЗ на сменном дне
    // восстанавливается обратно в смену.
    var plannedStatus = {};

    // 3. Прогон по сотрудникам + дням месяца
    for (var i = 0; i < emps.length; i++) {
      var emp = emps[i];
      if (!emp.шаблон_ротации || !emp.старт_цикла) continue;
      var pat = patternsById[emp.шаблон_ротации];
      if (!pat) continue;
      var startDate = this._parseIsoDate(emp.старт_цикла);
      if (!startDate) continue;
      var cycle = pat.cycle;

      // Map день_цикла → статус
      var dayToStatus = {};
      for (var di = 0; di < pat.days.length; di++) {
        dayToStatus[pat.days[di].day] = pat.days[di].status;
      }

      for (var day = 1; day <= daysInMonth; day++) {
        var dt = new Date(year, month - 1, day);
        // день_цикла = ((dt - startDate).days % cycle) + 1
        var diffMs = dt.getTime() - startDate.getTime();
        var diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));
        // Внимание: JS даёт отрицательный остаток для отрицательного diffDays
        var dayOfCycle = ((diffDays % cycle) + cycle) % cycle + 1;
        var status = dayToStatus[dayOfCycle] || '';
        if (!status) continue;  // регулярный выходной → пропустить

        var iso = this._toIsoDate(dt);
        var key2 = iso + '|' + emp['таб_номер'];
        plannedStatus[key2] = status;   // Task 303: план дня (для шагов 4/4.6)
        if (entryIndex[key2]) {
          perEmployee[emp['таб_номер']].skipped++;
          continue;  // запись уже есть (manual или auto) — не трогаем
        }
        toInsert.push([dt, emp['таб_номер'], status, 0, 0, 'авто', new Date(), '', null, '']);
        entryIndex[key2] = { _rowIndex: -1, источник: 'авто', статус: status, инструкция: null };
        perEmployee[emp['таб_номер']].generated++;
      }
    }

    // 4. (Task 303) Прогон по инструктажам — «слой мероприятий».
    // Мероприятие больше НЕ затирает плановую смену: на сменном дне
    // в ячейке остаётся код смены (мероприятие показывается бейджем на
    // клиенте, данные — лист «Инструктажи», связка — колонка I). Код
    // И/ОБ/ПЗ/ПР/* (Task 306) в Записи_графика попадает только на
    // день БЕЗ смены.
    // coveredTr — дни месяца, покрытые мероприятиями (для сверки 4.6).
    var coveredTr = {};         // "ISO|таб_номер": мероприятие
    var eventGenerated = 0;     // вставлено строк мероприятий (дни без смены)
    var eventRestored = 0;      // смен восстановлено из-под мероприятий
    var eventRemoved = 0;       // удалено устаревших строк мероприятий
    // Task 304: ВИДИМЫЕ предупреждения генерации. Таб_номер
    // мероприятия/отпуска не из справочника «Сотрудники» (например,
    // «871» вместо «0871» — потерян ведущий ноль) ДО Task 304
    // работал ТИХО: бейдж не показывался, записи не сопоставлялись.
    // Возвращаются в data.warnings и видны в тосте «Сформировать».
    var warnings = [];
    for (var ti = 0; ti < trainings.length; ti++) {
      var t = trainings[ti];
      var codeFor = this.TRAINING_TYPE_TO_STATUS[t.тип];
      if (!codeFor) continue;
      var tStart = this._parseIsoDate(t.дата_начала);
      var tEnd   = this._parseIsoDate(t.дата_окончания) || tStart;
      if (!tStart) continue;

      // Task 304: таб_номер не из справочника — предупреждение
      if (!perEmployee[t['таб_номер']]) {
        warnings.push('Мероприятие id=' + t.id + ' (' + t.дата_начала + '): таб_номер «' +
                      t['таб_номер'] + '» не найден в «Сотрудниках» — вероятно, потерян ведущий ноль');
      }

      // Для каждого дня мероприятия в текущем месяце
      var cur = new Date(Math.max(tStart.getTime(), monthStart.getTime()));
      while (cur.getTime() <= tEnd.getTime()) {
        // Проверить, что cur в пределах месяца
        if (cur.getMonth() + 1 === month && cur.getFullYear() === year) {
          var iso2 = this._toIsoDate(cur);
          var key3 = iso2 + '|' + t['таб_номер'];
          coveredTr[key3] = t;
          var existingEntry = entryIndex[key3];
          var planned = plannedStatus[key3];   // плановая смена дня (Task 303)
          if (existingEntry) {
            if (existingEntry.источник === 'руч') {
              // ручные правки приоритетнее — не трогаем
              if (perEmployee[t['таб_номер']]) perEmployee[t['таб_номер']].skipped++;
            } else if (planned) {
              // (Task 303) День со плановой сменой: смена остаётся кодом
              // ячейки, мероприятие — бейджем на клиенте. Генерация до
              // Task 303 могла записать сюда И/ОБ/ПЗ — восстанавливаем
              // смену. Связку с мероприятием (колонка I) обновляем.
              var needRestore = this._isEventStatusCode(existingEntry.статус);
              if (existingEntry._rowIndex && existingEntry._rowIndex > 0) {
                if (needRestore || existingEntry.инструкция !== t.id) {
                  toUpdate.push({
                    rowIndex: existingEntry._rowIndex,
                    status: needRestore ? planned : existingEntry.статус,
                    instruction_id: t.id
                  });
                  if (perEmployee[t['таб_номер']]) perEmployee[t['таб_номер']].updated++;
                  // Обновить индекс — чтобы не обновить повторно
                  existingEntry.статус = needRestore ? planned : existingEntry.статус;
                  existingEntry.инструкция = t.id;
                  if (needRestore) eventRestored++;
                }
              } else {
                // Строка из toInsert (шаг 3) — смена уже стоит, НЕ
                // заменяем её кодом мероприятия: проставляем только
                // связку с мероприятием (колонка I).
                for (var ii = 0; ii < toInsert.length; ii++) {
                  var r = toInsert[ii];
                  if (this._toIsoDate(r[0]) === iso2 && r[1] === t['таб_номер']) {
                    r[8] = t.id;        // инструкция
                    break;
                  }
                }
              }
            } else {
              // (Task 303) День БЕЗ плановой смены (выходной по циклу):
              //   статус уже И/ОБ/ПЗ → сверяем код с типом мероприятия
              //   (тип мог измениться) и связку; в toInsert — то же;
              //   прочие статусы (напр. авто-«ОТ») не трогаем — отпуск
              //   приоритетнее (шаг 4.5).
              if (this._isEventStatusCode(existingEntry.статус)) {
                if (existingEntry.статус !== codeFor || existingEntry.инструкция !== t.id) {
                  if (existingEntry._rowIndex && existingEntry._rowIndex > 0) {
                    toUpdate.push({
                      rowIndex: existingEntry._rowIndex,
                      status: codeFor,
                      instruction_id: t.id
                    });
                    if (perEmployee[t['таб_номер']]) perEmployee[t['таб_номер']].updated++;
                    existingEntry.статус = codeFor;
                    existingEntry.инструкция = t.id;
                  } else {
                    for (var ii2 = 0; ii2 < toInsert.length; ii2++) {
                      var r2 = toInsert[ii2];
                      if (this._toIsoDate(r2[0]) === iso2 && r2[1] === t['таб_номер']) {
                        r2[2] = codeFor;     // статус
                        r2[8] = t.id;        // инструкция
                        break;
                      }
                    }
                  }
                }
              }
            }
          } else {
            // Нет записи и нет плановой смены → вставить строку
            // мероприятия (мероприятие в день отдыха — как до Task 303).
            // День со сменой сюда попасть не может: шаг 3 уже вставил
            // её в toInsert (entryIndex).
            toInsert.push([new Date(cur), t['таб_номер'], codeFor, 0, 0, 'авто', new Date(), '', t.id, '']);
            entryIndex[key3] = { _rowIndex: -1, источник: 'авто', статус: codeFor, инструкция: t.id };
            eventGenerated++;
            if (perEmployee[t['таб_номер']]) perEmployee[t['таб_номер']].generated++;
          }
        }
        cur = new Date(cur.getFullYear(), cur.getMonth(), cur.getDate() + 1);
      }
    }

    // 4.5 (Task 274) Прогон по отпускам — лист «Отпуска», высший
    // приоритет среди авто-источников (после ручных правок).
    // Отсутствие листа «Отпуска» — НЕ ошибка: генерация работает и
    // без плана отпусков (vocations=[]; до создания листа/деплоя).
    var vacs = this.listVacations({ token: payload.token, year: year });
    var vacations = (vacs.ok && vacs.data && vacs.data.vacations) ? vacs.data.vacations : [];
    var coveredVac = {};   // "ISO|таб_номер" → период (день покрыт отпуском)
    var vacationGenerated = 0;
    var vacationUpdated = 0;

    for (var vi = 0; vi < vacations.length; vi++) {
      var v = vacations[vi];
      var vStart = this._parseIsoDate(v.дата_начала);
      var vEnd   = this._parseIsoDate(v.дата_окончания) || vStart;
      if (!vStart) continue;

      // Task 304: таб_номер не из справочника — предупреждение
      if (!perEmployee[v['таб_номер']]) {
        warnings.push('Отпуск id=' + (v.id === null ? '—' : v.id) + ' (' + v.дата_начала +
                      '): таб_номер «' + v['таб_номер'] +
                      '» не найден в «Сотрудниках» — вероятно, потерян ведущий ноль');
      }

      // Для каждого календарного дня периода в текущем месяце
      // (включая Сб/Вс — отпуск в календарных днях)
      var vc = new Date(Math.max(vStart.getTime(), monthStart.getTime()));
      while (vc.getTime() <= vEnd.getTime()) {
        if (vc.getMonth() + 1 === month && vc.getFullYear() === year) {
          var isoV = this._toIsoDate(vc);
          var keyV = isoV + '|' + v['таб_номер'];
          coveredVac[keyV] = v;
          var exV = entryIndex[keyV];
          if (exV) {
            if (exV.источник === 'руч') {
              // ручные правки приоритетнее отпуска — не трогаем
              if (perEmployee[v['таб_номер']]) perEmployee[v['таб_номер']].skipped++;
            } else if (exV.статус === 'ОТ' && !exV.инструкция) {
              // уже отпуск (прошлая генерация) — не трогаем
              if (perEmployee[v['таб_номер']]) perEmployee[v['таб_номер']].skipped++;
            } else if (exV._rowIndex && exV._rowIndex > 0) {
              // авто-запись (смена/инструктаж) → перекрыть отпуском,
              // инструкция (I) очищается: сотрудник в отпуске
              // Task 298: код отпуска «О» → «ОТ» (Т-12/Т-13)
              toUpdate.push({ rowIndex: exV._rowIndex, status: 'ОТ', instruction_id: null });
              exV.статус = 'ОТ';
              exV.инструкция = null;
              vacationUpdated++;
              if (perEmployee[v['таб_номер']]) perEmployee[v['таб_номер']].updated++;
            } else {
              // строка из toInsert (шаг 3/4) — заменить статус на «ОТ»
              for (var vii = 0; vii < toInsert.length; vii++) {
                var rv = toInsert[vii];
                if (this._toIsoDate(rv[0]) === isoV && rv[1] === v['таб_номер']) {
                  rv[2] = 'ОТ';   // статус
                  rv[8] = null;   // инструкция
                  break;
                }
              }
              vacationUpdated++;
              if (perEmployee[v['таб_номер']]) perEmployee[v['таб_номер']].updated++;
            }
          } else {
            // нет записи (в т.ч. выходной по циклу) → вставить «ОТ»
            toInsert.push([new Date(vc), v['таб_номер'], 'ОТ', 0, 0, 'авто', new Date(), '', null, '']);
            entryIndex[keyV] = { _rowIndex: -1, источник: 'авто', статус: 'ОТ', инструкция: null };
            vacationGenerated++;
            if (perEmployee[v['таб_номер']]) perEmployee[v['таб_номер']].generated++;
          }
        }
        vc = new Date(vc.getFullYear(), vc.getMonth(), vc.getDate() + 1);
      }
    }

    // Устаревшие авто-«ОТ» записи месяца: сотрудник в отпуске по
    // старому плану, текущий лист «Отпуска» день не покрывает →
    // строка под удаление (идемпотентность повторной генерации).
    // «ручные» записи никогда не удаляются. Task 303: шаг 4 больше не
    // превращает «ОТ» в код мероприятия — ветка «уже отпуск» ниже
    // (статус='ОТ' && !инструкция) просто не трогает такие строки.
    // Task 298: ЛЕГАСИ-«О» (21 авто-запись до смены кода): дни, покрытые
    // актуальным отпуском, перегенерация сама обновит на «ОТ» (ветка
    // _rowIndex > 0 ниже по коду — статус в листе меняется на «ОТ»);
    // но «О»-дни с УДАЛЁННЫМ/изменённым периодом сюда не попадают →
    // останутся «зависшими». Миграцию «О»→«ОТ» (Ctrl+H, колонка C)
    // пользователь выполняет вручную — см. DEPLOY-Task298.
    var toDeleteRows = [];
    for (var sv = 0; sv < existingEntries.length; sv++) {
      var se = existingEntries[sv];
      if (se.статус === 'ОТ' && se.источник === 'авто' &&
          se._rowIndex && se._rowIndex > 0 &&
          !coveredVac[se.дата + '|' + se['таб_номер']]) {
        toDeleteRows.push(se._rowIndex);
      }
    }

    // 4.6 (Task 303) Сверка устаревших строк мероприятий (ПОСЛЕ
    // отпускного прохода 4.5: если день покрыт отпуском, И-строка уже
    // стала «ОТ» и сюда не попадает — отпуск приоритетнее). Авто-строки
    // с кодом И/ОБ/ПЗ/ПР/* (Task 306), чей день больше НЕ покрыт
    // мероприятием:
    //   • день со плановой сменой → восстановить смену (генерация до
    //     Task 303 затирала смену кодом мероприятия);
    //   • день без смены → строка под удаление (мероприятие удалено из
    //     листа «Инструктажи»; до Task 303 такая строка «висела» навсегда).
    // Ручные строки не трогаются (приоритет ручной правки).
    for (var sv3 = 0; sv3 < existingEntries.length; sv3++) {
      var se3 = existingEntries[sv3];
      if (se3.источник !== 'авто') continue;
      if (!this._isEventStatusCode(se3.статус)) continue;
      if (coveredTr[se3.дата + '|' + se3['таб_номер']]) continue;
      if (!(se3._rowIndex && se3._rowIndex > 0)) continue;
      var planned3 = plannedStatus[se3.дата + '|' + se3['таб_номер']];
      if (planned3) {
        toUpdate.push({ rowIndex: se3._rowIndex, status: planned3, instruction_id: null });
        se3.статус = planned3;
        se3.инструкция = null;
        eventRestored++;
        if (perEmployee[se3['таб_номер']]) perEmployee[se3['таб_номер']].updated++;
      } else {
        toDeleteRows.push(se3._rowIndex);
        eventRemoved++;
      }
    }

    // 5. Запись в лист
    var insertCount = toInsert.length;
    if (insertCount > 0) {
      var lastRow = entriesSheet.getLastRow();
      // Task 304: колонка B (таб_№) — текстовый формат ДО записи:
      // «0871» не должен превратиться в число 871 (USER_ENTERED)
      entriesSheet.getRange(lastRow + 1, 2, insertCount, 1).setNumberFormat('@');
      var targetRange = entriesSheet.getRange(lastRow + 1, 1, insertCount, 10);
      targetRange.setValues(toInsert);
    }

    var updateCount = toUpdate.length;
    if (updateCount > 0) {
      for (var ui = 0; ui < toUpdate.length; ui++) {
        var u = toUpdate[ui];
        entriesSheet.getRange(u.rowIndex, 3).setValue(u.status);   // C: статус
        entriesSheet.getRange(u.rowIndex, 7).setValue(new Date()); // G: дата_обновления
        entriesSheet.getRange(u.rowIndex, 9).setValue(u.instruction_id); // I: инструкция
      }
    }

    // 5.5 (Task 274) Удаление устаревших авто-«О» строк — ПОСЛЕ
    // вставок/обновлений: вставленные строки добавляются НИЖЕ
    // существующих (индексы существующих не меняются), удаление
    // СВЕРХУ ВНИЗ сохраняет корректность индексов оставшихся.
    var removeCount = toDeleteRows.length;
    if (removeCount > 0) {
      toDeleteRows.sort(function(a, b) { return b - a; });
      for (var dr = 0; dr < toDeleteRows.length; dr++) {
        entriesSheet.deleteRow(toDeleteRows[dr]);
      }
    }

    // 6. Аудит
    // Task 279: в аудит и в ответ добавлены отпускные счётчики и
    // диагностика — «отпуска не формируются» больше не тихие:
    // vacationsFound (периодов в листе на год), vacationError
    // (например, листа нет), дней «О» = generated + updated.
    var vacationDays = vacationGenerated + vacationUpdated;
    // Task 303: дни месяца, покрытые мероприятиями (бейджи на сменах +
    // строки И/ОБ/ПЗ на днях без смены)
    var trainingDays = 0;
    for (var ck in coveredTr) trainingDays++;
    var summary = 'Сформирован график на ' + String(month).padStart(2, '0') + '.' + year +
                  ': вставлено ' + insertCount + ', обновлено ' + updateCount +
                  ', удалено устаревших отпусков ' + removeCount +
                  ', периодов отпусков ' + vacations.length +
                  ', дней «О» ' + vacationDays +
                  ', дней мероприятий ' + trainingDays +
                  ' (строк И/ОБ/ПЗ/ПР/* ' + eventGenerated +
                  ', восстановлено смен ' + eventRestored +
                  ', удалено мероприятий ' + eventRemoved +
                  (warnings.length ? ', предупреждений ' + warnings.length : '') + ')';
    try {
      Utils.audit(user.email, 'WORKSCHEDULE_GENERATE_MONTH', '', '', summary);
    } catch (e) { /* ignore */ }

    return {
      ok: true,
      data: {
        generated: insertCount,
        updated: updateCount,
        removed: removeCount,
        vacationGenerated: vacationGenerated,
        vacationUpdated: vacationUpdated,
        vacationsFound:    vacations.length,
        vacationError:     (vacs && vacs.ok) ? null :
                          String((vacs && vacs.error) || 'list_vacations_failed'),
        vacationDays:      vacationDays,
        // Task 303: слой мероприятий (И/ОБ/ПЗ)
        trainingDays:      trainingDays,    // дней месяца, покрытых мероприятиями
        eventGenerated:    eventGenerated,  // вставлено строк И/ОБ/ПЗ (дни без смены)
        eventRestored:     eventRestored,   // смен восстановлено из-под мероприятий
        eventRemoved:      eventRemoved,    // удалено устаревших строк мероприятий
        // Task 304: таб_номера не из справочника (потерянные нули и пр.)
        warnings:          warnings,
        perEmployee: perEmployee,
        monthStart: this._toIsoDate(monthStart),
        daysInMonth: daysInMonth
      }
    };
  },

  // ============================================================
  // Ручные правки
  // ============================================================

  // workSchedule.setManualEntry
  // payload: { token, date(ISO), таб_номер, статус, переработка, праздник,
  //            замещает, инструкция, комментарий }
  // Если запись есть:
  //   - source='руч' → обновить
  //   - source='авто' → обновить (перевести в руч)
  // Если нет → вставить с source='руч'
  //
  // _validateStatusCode (Task 298, Q4) — проверка кода по листу
  // «Коды_статусов». Раньше setManualEntry сохранял ЛЮБОЙ код — опечатка
  // регистром («Д» вместо «д») попадала в БД незаметно и «терялась» в шахматке
  // (без цвета и названия). Теперь код обязан присутствовать в
  // справочнике; кэша нет — лист маленький (одна колонка), чтение
  // быстрое, а актуальность важнее (пользователь правит состав кодов
  // прямо в таблице). Лист отсутствует/пуст → правка отклоняется
  // (fail-closed, как у матрицы прав): лучше не пустить правку, чем
  // записать неизвестный код. ПУСТОЙ статус сюда не доходит — валиден
  // только путь удаления (deleteEntry; «— выходной» на клиенте).
  _validateStatusCode: function(status) {
    if (!status) return { ok: false, error: 'invalid_статус' };
    var sheet = this._getSheet(this.STATUS_CODES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.STATUS_CODES_SHEET };
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'empty: ' + this.STATUS_CODES_SHEET };
    // Читаем ТОЛЬКО колонку A (коды). getLastRow может быть завышен
    // стилевым холстом (урок Task 294: getLastRow()=1000 при данных
    // 17×15) — пустые строки просто пропускаются.
    var values = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < values.length; i++) {
      var c = String(values[i][0] || '').trim();
      if (c === status) return { ok: true };
    }
    return { ok: false, error: 'unknown_статус: ' + status };
  },

  setManualEntry: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var dateObj = this._parseIsoDate(payload.date);
    if (!dateObj) return { ok: false, error: 'invalid_date' };
    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };
    var status = String(payload.статус || '').trim();
    if (!status) return { ok: false, error: 'invalid_статус' };

    // Task 298: код должен быть в справочнике «Коды_статусов»
    // (регистрозависимо: «д» ≠ «Д»). Ошибка unknown_статус доедет до
    // клиента текстом тоста «Ошибка: unknown_статус: …».
    var vstat = this._validateStatusCode(status);
    if (!vstat.ok) return { ok: false, error: vstat.error };

    var sheet = this._getSheet(this.ENTRIES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.ENTRIES_SHEET };

    var lastRow = sheet.getLastRow();
    var foundRow = -1;
    if (lastRow >= 2) {
      // Читаем A (дата) и B (таб_номер) для поиска существующей записи
      var lookup = sheet.getRange(2, 1, lastRow - 1, 2).getValues();
      for (var i = 0; i < lookup.length; i++) {
        var dCell = lookup[i][0];
        if (!(dCell instanceof Date)) continue;
        if (this._toIsoDate(dCell) === payload.date && String(lookup[i][1]).trim() === tabNo) {
          foundRow = i + 2;
          break;
        }
      }
    }

    var переработка = payload.переработка === 1 || payload.переработка === '1' ? 1 : 0;
    var праздник    = payload.праздник === 1 || payload.праздник === '1' ? 1 : 0;
    var замещает    = payload.замещает ? String(payload.замещает).trim() : '';
    var инструкция  = payload.инструкция ? parseInt(payload.инструкция, 10) : null;
    var комментарий = String(payload.комментарий || '').slice(0, 500);

    if (foundRow > 0) {
      // Обновление существующей
      sheet.getRange(foundRow, 1).setValue(dateObj);
      sheet.getRange(foundRow, 2).setNumberFormat('@');  // Task 304: таб_№ текстом
      sheet.getRange(foundRow, 2).setValue(tabNo);
      sheet.getRange(foundRow, 3).setValue(status);
      sheet.getRange(foundRow, 4).setValue(переработка);
      sheet.getRange(foundRow, 5).setValue(праздник);
      sheet.getRange(foundRow, 6).setValue('руч');
      sheet.getRange(foundRow, 7).setValue(new Date());
      sheet.getRange(foundRow, 8).setValue(замещает ? замещает : null);
      sheet.getRange(foundRow, 9).setValue(инструкция);
      sheet.getRange(foundRow, 10).setValue(комментарий);
    } else {
      // Вставка новой (Task 304: B — таб_№ — текстовым форматом)
      this._appendRowKeepText(sheet, [dateObj, tabNo, status, переработка, праздник,
                       'руч', new Date(), замещает ? замещает : null, инструкция,
                       комментарий], [2]);
    }

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_SET_MANUAL', '', '',
        'Запись ' + payload.date + ' таб_номер=' + tabNo + ' → ' + status);
    } catch (e) { /* ignore */ }

    return { ok: true, data: { date: payload.date, таб_номер: tabNo, статус: status } };
  },

  // workSchedule.deleteEntry
  // Удалить запись (только source='руч'; для source='авто' — отказ, т.к. авто-записи
  // пересоздаются при следующей регенерации).
  // payload: { token, date(ISO), таб_номер }
  deleteEntry: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var dateObj = this._parseIsoDate(payload.date);
    if (!dateObj) return { ok: false, error: 'invalid_date' };
    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };

    var sheet = this._getSheet(this.ENTRIES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.ENTRIES_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'not_found' };

    var lookup = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
    for (var i = lookup.length - 1; i >= 0; i--) {
      var dCell = lookup[i][0];
      if (!(dCell instanceof Date)) continue;
      if (this._toIsoDate(dCell) === payload.date && String(lookup[i][1]).trim() === tabNo) {
        var source = String(lookup[i][5] || '').trim();
        if (source === 'авто') {
          return { ok: false, error: 'cannot_delete_auto',
                   message: 'Авто-запись нельзя удалить напрямую. Отредактируйте её как ручную.' };
        }
        sheet.deleteRow(i + 2);
        try {
          Utils.audit(user.email, 'WORKSCHEDULE_DELETE_ENTRY', '', '',
            'Удалена запись ' + payload.date + ' таб_номер=' + tabNo);
        } catch (e) { /* ignore */ }
        return { ok: true, data: { date: payload.date, таб_номер: tabNo } };
      }
    }
    return { ok: false, error: 'not_found' };
  },

  // ============================================================
  // CRUD сотрудников
  // ============================================================

  // workSchedule.addEmployee
  // payload: { token, таб_номер, ФИО, тип, смена, шаблон_ротации,
  //            старт_цикла(ISO), дата_приёма(ISO), должность, комментарий }
  addEmployee: function(payload) {
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

    // Проверка уникальности таб_номер
    var lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      var existing = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < existing.length; i++) {
        if (String(existing[i][0]).trim() === tabNo) {
          return { ok: false, error: 'duplicate_таб_номер',
                   message: 'Сотрудник с таб. № ' + tabNo + ' уже есть в справочнике' };
        }
      }
    }

    var smena     = payload.смена ? parseInt(payload.смена, 10) : '';
    var patId     = payload.шаблон_ротации ? parseInt(payload.шаблон_ротации, 10) : '';
    var startCycle = this._parseIsoDate(payload.старт_цикла);
    var hireDate  = this._parseIsoDate(payload.дата_приёма);
    var position  = String(payload.должность || '').trim();
    var comment   = String(payload.комментарий || '').slice(0, 500);

    // Task 304: A (таб_номер) — текст: «0871» не должен стать числом 871
    this._appendRowKeepText(sheet, [
      tabNo, fio, tip, smena || null, patId || null,
      startCycle, hireDate, null,  // H=дата_увольнения — пусто
      0,  // в_архиве=0
      position, comment
    ], [1]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_ADD_EMPLOYEE', '', '',
        'Добавлен сотрудник таб_номер=' + tabNo + ' ФИО=' + fio);
    } catch (e) { /* ignore */ }

    return { ok: true, data: { таб_номер: tabNo } };
  },

  // workSchedule.dismissEmployee
  // payload: { token, таб_номер, дата_увольнения(ISO) }
  // Увольнение (Task 318): в строке сотрудника таблицы «Сотрудники»
  //   записывается дата_увольнения (H) и в_архиве=1 (I). Строка НЕ
  //   удаляется — остаётся в листе как АРХИВ; listEmployees без
  //   includeArchived сотрудника больше не возвращает → строка уходит
  //   из шахматки/селектов форм. Перезапись существующей даты
  //   допустима (идемпотентно — правка даты увольнения).
  dismissEmployee: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };
    var dismissDate = this._parseIsoDate(payload.дата_увольнения);
    if (!dismissDate) return { ok: false, error: 'invalid_дата_увольнения' };

    var sheet = this._getSheet(this.EMPLOYEES_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.EMPLOYEES_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) {
      return { ok: false, error: 'not_found_таб_номер',
               message: 'Сотрудник с таб. № ' + tabNo + ' не найден' };
    }

    // Поиск строки по таб_№ (A — текст, Task 304: ведущие нули)
    var tabs = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < tabs.length; i++) {
      if (String(tabs[i][0]).trim() !== tabNo) continue;
      var row = i + 2;
      sheet.getRange(row, 8).setValue(dismissDate);  // H = дата_увольнения
      sheet.getRange(row, 9).setValue(1);            // I = в_архиве
      try {
        Utils.audit(user.email, 'WORKSCHEDULE_DISMISS_EMPLOYEE', '', '',
          'Уволен сотрудник таб_номер=' + tabNo +
          ' дата=' + String(payload.дата_увольнения || ''));
      } catch (e) { /* ignore */ }
      return { ok: true, data: { таб_номер: tabNo, в_архиве: 1 } };
    }
    return { ok: false, error: 'not_found_таб_номер',
             message: 'Сотрудник с таб. № ' + tabNo + ' не найден' };
  },

  // ============================================================
  // CRUD инструктажей
  // ============================================================

  // workSchedule.addTraining
  // payload: { token, таб_номер, тип, тема, дата_начала(ISO), дата_окончания(ISO),
  //            длительность_дней, комментарий }
  addTraining: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var tabNo = String(payload.таб_номер || '').trim();
    if (!tabNo) return { ok: false, error: 'invalid_таб_номер' };
    var tip = String(payload.тип || '').trim();
    if (!this.TRAINING_TYPE_TO_STATUS[tip]) {
      return { ok: false, error: 'invalid_тип' };
    }
    var tema = String(payload.тема || '').trim();
    if (!tema) return { ok: false, error: 'invalid_тема' };
    var startDate = this._parseIsoDate(payload.дата_начала);
    if (!startDate) return { ok: false, error: 'invalid_дата_начала' };

    var endDate = payload.дата_окончания ? this._parseIsoDate(payload.дата_окончания) : startDate;
    if (!endDate) endDate = startDate;

    var duration = parseInt(payload.длительность_дней, 10) || 1;
    var comment  = String(payload.комментарий || '').slice(0, 500);

    var sheet = this._getSheet(this.TRAININGS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };

    // Найти max id в столбце A
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
      [newId, tabNo, tip, tema, startDate, endDate, duration, comment], [2]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_ADD_TRAINING', '', '',
        'Добавлено мероприятие id=' + newId + ' тип=' + tip + ' таб_номер=' + tabNo);
    } catch (e) { /* ignore */ }

    return { ok: true, data: { id: newId } };
  },

  // workSchedule.deleteTraining
  // payload: { token, id }
  deleteTraining: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var id = parseInt(payload.id, 10);
    if (isNaN(id)) return { ok: false, error: 'invalid_id' };

    var sheet = this._getSheet(this.TRAININGS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'not_found' };

    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) {
      if (parseInt(ids[i][0], 10) === id) {
        sheet.deleteRow(i + 2);
        try {
          Utils.audit(user.email, 'WORKSCHEDULE_DELETE_TRAINING', '', '',
            'Удалено мероприятие id=' + id);
        } catch (e) { /* ignore */ }
        return { ok: true, data: { id: id } };
      }
    }
    return { ok: false, error: 'not_found' };
  },

  // ============================================================
  // CRUD отпусков (Task 274 — лист «Отпуска»)
  // ============================================================

  // workSchedule.addVacation
  // payload: { token, таб_номер, часть(1..3), дата_начала(ISO),
  //            дата_окончания(ISO), комментарий }
  // Валидация:
  //   - часть 1..3 (отпуска делятся на 2–3 части в год);
  //   - дата_окончания >= дата_начала;
  //   - период не пересекается с уже заданными периодами сотрудника;
  //   - номер части не дублируется в году начала периода.
  addVacation: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

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

    // Проверки по существующим периодам сотрудника
    var lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      var values = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
      for (var i = 0; i < values.length; i++) {
        var r = values[i];
        // Task 282: строки БЕЗ id (ручное заполнение листа) тоже
        // участвуют в проверках пересечения/дубля части. Раньше
        // строки без id пропускались — контроль дырявился: поверх
        // ручного периода можно было добавить пересекающийся.
        // «Пустая строка» — та же семантика, что в listVacations
        // (Task 279): нет ни id, ни таб_номера, ни даты начала.
        if ((r[0] === '' || r[0] === null) && !String(r[1] || '').trim() &&
            !this._parseSheetDate(r[3])) continue;
        if (String(r[1] || '').trim() !== tabNo) continue;
        // Task 279: пересечения/дубли считаются и по текстовым датам
        // (раньше такие строки игнорировались — контроль дырявился)
        var exStart = this._parseSheetDate(r[3]);
        var exEnd   = this._parseSheetDate(r[4]) || exStart;
        if (!exStart) continue;
        // Пересечение периодов одного сотрудника
        if (endDate.getTime() >= exStart.getTime() &&
            startDate.getTime() <= exEnd.getTime()) {
          return { ok: false, error: 'overlap',
                   message: 'Период пересекается с уже заданным отпуском ' +
                            'этого сотрудника (' + this._toIsoDate(exStart) + ' — ' +
                            this._toIsoDate(exEnd) + ')' };
        }
        // Дубль номера части в том же году (год даты начала периода)
        var exPart = parseInt(r[2], 10);
        if (exPart === part && exStart.getFullYear() === startDate.getFullYear()) {
          return { ok: false, error: 'duplicate_часть',
                   message: 'Часть ' + part + ' у этого сотрудника уже задана на ' +
                            startDate.getFullYear() + ' год' };
        }
      }
    }

    // max id в столбце A
    var maxId = 0;
    if (lastRow >= 2) {
      var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var j = 0; j < ids.length; j++) {
        var v = parseInt(ids[j][0], 10);
        if (!isNaN(v) && v > maxId) maxId = v;
      }
    }
    var newId = maxId + 1;

    // Task 304: B (таб_номер) — текст, ведущие нули не теряются
    this._appendRowKeepText(sheet, [newId, tabNo, part, startDate, endDate, comment], [2]);

    try {
      Utils.audit(user.email, 'WORKSCHEDULE_ADD_VACATION', '', '',
        'Добавлен отпуск id=' + newId + ' часть=' + part +
        ' таб_номер=' + tabNo + ' ' + this._toIsoDate(startDate) + '…' +
        this._toIsoDate(endDate) + ' (' + days + ' дн.)');
    } catch (e) { /* ignore */ }

    return { ok: true, data: { id: newId, дней: days } };
  },

  // workSchedule.deleteVacation
  // payload: { token, id }
  deleteVacation: function(payload) {
    var auth = this._requireWrite(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var id = parseInt(payload.id, 10);
    if (isNaN(id)) return { ok: false, error: 'invalid_id' };

    var sheet = this._getSheet(this.VACATIONS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.VACATIONS_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'not_found' };

    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
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

};
