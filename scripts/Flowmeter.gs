// ============================================================
// Flowmeter.gs — Расходомеры хозрасчётные: чтение/запись данных
// в Google Таблицу hozraschet_meters
// ============================================================
// Развернуть в том же Apps Script проекте, где находятся
//   Code.gs, Utils.gs, CableJournal.gs.
//
// Эндпоинты (вызываются через doPost):
//   flowmeter.list         — прочитать все позиции расходомеров
//   flowmeter.updateReading — обновить показания одной позиции
//   flowmeter.setComment   — Task 195: комментарий к последним показаниям
//                            (только для автора показаний)
//
// Авторизация — по тому же паттерну, что CableJournal.gs:
//   Utils.findSessionByToken(token) → session
//   Utils.findUserById(session.user_id) → user
//
// Структура листа «hozraschet_meters» в Google Таблице:
//   Строка 1 — заголовки столбцов
//   Строки 2+ — данные (12 позиций, строки 2–13)
//
//   Столбцы (A–Q; P не используется с Task 211):
//     A: id         — номер позиции (1–12)
//     B: hoz        — название (Хозрасчёт №1)
//     C: param      — параметр (Расход пара в корпус 114)
//     D: datePrev   — предыдущая дата (Date object в ячейке)
//     E: dateCurr   — текущая дата (Date object в ячейке)
//     F: prev       — предыдущие показания (число)
//     G: curr       — текущие показания (число)
//     H: unit       — единица измерения (т, м³)
//     I: temp       — температура среды (/число или пусто)
//     J: Gcal       — гигакалории пара (число или пусто; только для расходомеров пара, Task 100)
//     K: period     — периодичность (Ежедневно/Еженедельно/Ежемесячно)
//     L: modRole    — роль пользователя, внёсшего последние изменения
//     M: modName    — имя пользователя, внёсшего последние изменения
//     N: modTimestamp — timestamp последнего ввода (Task 108 — для редактирования в течение 1 часа)
//     O: comment    — активный комментарий к последним показаниям (Task 195; виден всем,
//                     редактировать может автор показаний ИЛИ админ — до тех пор,
//                     пока другой пользователь не внесёт новые данные)
//     P: (не используется с Task 211; ранее archivedComment — preview для карточки.
//                       Полная история комментариев — в hozraschet_archive.P по записям.)
//     Q: allowNegative — флаг «допустим отрицательный расход» (Task 199). Значения:
//                     'yes' (для счётчиков возврата конденсата, где curr<prev легитимно)
//                     или пусто/'no' (для остальных). Читается в list() → поле meter
//                     .allowNegative. Используется в ValidationRules.compute для
//                     пропуска правила JUMP_NEGATIVE.
//
//   Данные начинаются со строки 2 (строка 1 — заголовки).
//   Строка 2 → id=1, строка 13 → id=12.
//
//   Даты хранятся как Date objects (не строки!),
//   что позволяет Google Sheets отображать их корректно
//   независимо от локали таблицы.
//   Клиент отправляет/ожидает формат M/D/YYYY (8/3/2026).
// ============================================================

var Flowmeter = {

  // ID Google Таблицы
  SPREADSHEET_ID: '1enZSq7K8pwJVzaAI_tbXZtvATqARTxH0lSU4c-wc1eY',

  // Имя листа в таблице
  SHEET_NAME: 'hozraschet_meters',

  // Строка, с которой начинаются данные (1-based, после заголовков)
  DATA_START_ROW: 2,

  // Роли с правом чтения расходомеров
  // Task 112: убран 'КИП ИОС pro' — по карте ролей фильтр 10 = нет
  // Task 116: добавлен 'КИП8 pro' — по карте ролей фильтр 10 = да
  READ_ROLES: ['КИП ИОС дежурный', 'ИТР8', 'ИТР8 pro', 'ИТР ИОС',
               'КИП8 pro', 'Админ'],

  // Роли с правом ввода показаний (запись)
  INPUT_ROLES: ['КИП ИОС дежурный', 'Админ'],

  // ============================================================
  // Получить лист таблицы по имени, с fallback на первый лист
  // ============================================================
  _getSheet: function() {
    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    var sheet = ss.getSheetByName(this.SHEET_NAME);
    if (sheet) return sheet;
    var sheets = ss.getSheets();
    if (sheets.length > 0) return sheets[0];
    return null;
  },

  // ============================================================
  // Авторизация: чтение
  // По паттерну CableJournal._requireRead, но без throw —
  // возвращает { user } или { error: {ok:false,...} }
  // ============================================================
  _requireRead: function(token) {
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

  // ============================================================
  // Авторизация: запись (ввод показаний)
  // По паттерну CableJournal._requireEdit, но без throw —
  // возвращает { user } или { error: {ok:false,...} }
  // ============================================================
  _requireEdit: function(token) {
    if (!token) return { error: { ok: false, error: 'no_session' } };
    var session = Utils.findSessionByToken(token);
    if (!session) return { error: { ok: false, error: 'no_session' } };
    var user = Utils.findUserById(session.user_id);
    if (!user) return { error: { ok: false, error: 'no_session' } };

    if (this.INPUT_ROLES.indexOf(user.role) === -1) {
      try {
        Utils.audit(user.email, 'FLOWMETER_ACCESS_DENIED', '', '',
          'Роль "' + user.role + '" не имеет прав на ввод показаний расходомеров');
      } catch (e) { /* ignore */ }
      return { error: { ok: false, error: 'access_denied' } };
    }
    return { user: user };
  },

  // ============================================================
  // flowmeter.list — прочитать все позиции расходомеров
  // ============================================================
  // payload: { token }
  // Возвращает: { ok: true, data: { meters: [...] } }
  list: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet();
    if (!sheet) {
      return { ok: false, error: 'Лист не найден' };
    }

    var lastRow = sheet.getLastRow();
    if (lastRow < this.DATA_START_ROW) {
      return { ok: true, data: { meters: [] } };
    }

    // Читаем данные (строка DATA_START_ROW до lastRow, столбцы A–Q = 17 столбцов;
    // O=15 — comment, Task 195; P=16 — не используется с Task 211;
    // Q=17 — allowNegative, Task 199)
    var range = sheet.getRange(this.DATA_START_ROW, 1, lastRow - this.DATA_START_ROW + 1, 17);
    var values = range.getValues();

    // Task 109: Строим кэш email → name из таблицы users (KIP8_Access)
    // для отображения имени пользователя (а не email) в карточке.
    var userNameCache = this._buildUserNameCache();

    var meters = [];
    for (var i = 0; i < values.length; i++) {
      var row = values[i];
      // Пропускаем пустые строки
      if (!row[0] && !row[1]) continue;

      var modEmail = String(row[12] || '');  // M — email (для _canEdit)
      // Task 109: modDisplayName — имя пользователя из таблицы users (для отображения)
      var modDisplayName = modEmail;
      if (modEmail && userNameCache[modEmail]) {
        modDisplayName = userNameCache[modEmail];
      }

      var meter = {
        id:             parseInt(row[0], 10) || (i + 1),
        hoz:            String(row[1] || ''),
        param:          String(row[2] || ''),
        datePrev:       this._sheetToClientDate(row[3]),
        dateCurr:       this._sheetToClientDate(row[4]),
        prev:           parseFloat(row[5]) || 0,
        curr:           parseFloat(row[6]) || 0,
        unit:           String(row[7] || ''),
        temp:           this._parseTemp(row[8]),
        gcal:           this._parseGcal(row[9]),   // J=10 — гигакалории пара (Task 100)
        period:         String(row[10] || ''),
        modRole:        String(row[11] || ''),
        modName:        modEmail,                   // M — email (для _canEdit, Task 108)
        modDisplayName: modDisplayName,             // Task 109 — имя для отображения
        modTimestamp:   this._parseTimestamp(row[13]),  // N=14 (Task 108)
        comment:        String(row[14] || '').trim(),   // O=15 — Task 195
        // Task 211: P=16 (archivedComment) больше не читается из meters —
        // полная история комментариев живёт в hozraschet_archive.P
        allowNegative:  String(row[16] || '').trim().toLowerCase()  // Q=17 — Task 199
      };
      meters.push(meter);
    }

    return { ok: true, data: { meters: meters } };
  },

  // ============================================================
  // flowmeter.updateReading — обновить показания одной позиции
  // ============================================================
  // payload: { token, id, prev, curr, datePrev, dateCurr, temp, gcal }
  // Возвращает: { ok: true, data: { id: N } }
  //
  // Записывает в строку (id + 1):
  //   D → datePrev (Date), E → dateCurr (Date),
  //   F → prev, G → curr, I → temp, J → gcal (Task 100)
  updateReading: function(payload) {
    var auth = this._requireEdit(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var id = parseInt(payload.id, 10);
    if (!id || id < 1) {
      return { ok: false, error: 'Некорректный id позиции' };
    }

    // Task 205: Хозрасчёт №1 (id=1) — особый режим «расход за предыдущие сутки».
    // Данные приходят уже сформированными из Тэкон-19 (расход за сутки в т и Гкал).
    // Поэтому:
    //   • prev всегда 0 (нет накопительных показаний);
    //   • datePrev = dateCurr (нет «предыдущей даты»);
    //   • temp игнорируется (Тэкон-19 не отдаёт температуру);
    //   • gcal — необязательное поле (если Тэкон-19 отдаёт расход в Гкал,
    //     пользователь заполняет; если нет — поле остаётся пустым).
    // consumption в архиве = curr - 0 = curr — то есть равно введённому значению,
    // что и требуется для графика по введённым данным, а не по вычисленному расходу.
    if (id === 1) {
      payload.prev = 0;
      payload.datePrev = payload.dateCurr || '';
      payload.temp = null;
      // gcal — необязательное поле (Task 206: убрано требование обязательности).
    }

    var sheet = this._getSheet();
    if (!sheet) {
      return { ok: false, error: 'Лист не найден' };
    }

    // Строка в таблице: id + 1 (строка 1 — заголовки, строка 2 — id=1)
    var rowNum = id + 1;
    var lastRow = sheet.getLastRow();
    if (rowNum > lastRow) {
      return { ok: false, error: 'Позиция id=' + id + ' не найдена' };
    }

    // Конвертируем даты: M/D/YYYY (клиент) → Date object (таблица)
    var datePrevObj = this._clientToDateObj(payload.datePrev);
    var dateCurrObj = this._clientToDateObj(payload.dateCurr);
    var prevVal = parseFloat(payload.prev) || 0;
    var currVal = parseFloat(payload.curr) || 0;

    // Task 108: Если isEdit=true — проверяем, что прошёл менее 1 часа
    // и что текущий пользователь — тот, кто вводил последние показания.
    if (payload.isEdit) {
      var existingModName = String(sheet.getRange(rowNum, 13).getValue() || '');  // M=13
      var existingTs = sheet.getRange(rowNum, 14).getValue();  // N=14 — modTimestamp

      // Проверка: тот же пользователь? Сравниваем по email (Task 108)
      var currentUser = user.email || '';
      if (existingModName !== currentUser) {
        return { ok: false, error: 'not_your_input',
                 message: 'Редактировать может только тот, кто вводил показания' };
      }

      // Проверка: прошёл менее 1 часа?
      if (existingTs instanceof Date) {
        var elapsedMin = (new Date() - existingTs) / 1000 / 60;
        if (elapsedMin > 60) {
          return { ok: false, error: 'edit_window_expired',
                   message: 'Прошло более 1 часа — редактирование недоступно' };
        }
      } else {
        // modTimestamp пустой — редактирование недоступно (старые данные без timestamp)
        return { ok: false, error: 'edit_window_expired',
                 message: 'Нет данных о времени ввода — редактирование недоступно' };
      }
    }

    // Task 199: Валидация показаний перед записью. Считываем meter из строки
    // (нужен для allowNegative из Q=17), берём правила из flowmeter_validation_rules
    // и последнюю запись архива для проверки DUPLICATE.
    // Hard-block (SIGN_NEG, DATE_INCONSISTENT) — возвращаем ошибку, не пишем.
    // Soft-confirm правила — записываем показания, но в archive.Q пишем строку
    // с кодами и детализацией (пример: «JUMP_HIGH: расход 50.50 > max×3=15.00; ...»).
    var meterForValidation = {
      id: id,
      hoz: String(sheet.getRange(rowNum, 2).getValue() || ''),
      param: String(sheet.getRange(rowNum, 3).getValue() || ''),
      unit: String(sheet.getRange(rowNum, 8).getValue() || ''),
      period: String(sheet.getRange(rowNum, 11).getValue() || ''),
      modRole: String(sheet.getRange(rowNum, 12).getValue() || ''),
      modName: String(sheet.getRange(rowNum, 13).getValue() || ''),
      allowNegative: String(sheet.getRange(rowNum, 17).getValue() || '').toLowerCase().trim()  // Q=17
    };
    var rulesForMeter = null;
    var lastArchiveRecord = null;
    try {
      rulesForMeter = ValidationRules.getRulesForMeter(id);
    } catch (e) {
      Logger.log('ValidationRules.getRulesForMeter failed: ' + e.message);
    }
    try {
      var archSheet = SpreadsheetApp.openById(this.SPREADSHEET_ID)
                       .getSheetByName('hozraschet_archive');
      if (archSheet) {
        var archLast = archSheet.getLastRow();
        if (archLast >= 2) {
          // Читаем все строки, ищем последнюю для этого meterId (колонка A=1)
          var archRange = archSheet.getRange(2, 1, archLast - 1, 16);
          var archVals = archRange.getValues();
          for (var av = archVals.length - 1; av >= 0; av--) {
            if (parseInt(archVals[av][0], 10) === id) {
              lastArchiveRecord = {
                meterId: parseInt(archVals[av][0], 10),
                prev: parseFloat(archVals[av][2]) || 0,
                curr: parseFloat(archVals[av][3]) || 0,
                modName: String(archVals[av][13] || ''),
                timestamp: (archVals[av][14] instanceof Date)
                            ? archVals[av][14].toISOString() : String(archVals[av][14] || '')
              };
              break;
            }
          }
        }
      }
    } catch (e) {
      Logger.log('Reading last archive record failed (non-critical): ' + e.message);
    }

    // Task 200: последние записи ВСЕХ счётчиков за 7 дней для WRONG_METER
    var recentAllMeters = null;
    try {
      recentAllMeters = FlowmeterArchive.getRecentAllMeters(
        ValidationRules.WRONG_METER_PARAMS.LOOKBACK_DAYS
      );
    } catch (e) {
      Logger.log('getRecentAllMeters failed (non-critical): ' + e.message);
    }

    var validationResult = ValidationRules.compute(
      meterForValidation, payload, rulesForMeter, lastArchiveRecord, recentAllMeters
    );
    if (validationResult.hardBlock) {
      // Hard-block: возвращаем ошибку, ничего не пишем в таблицу
      try {
        Utils.audit(user.email, 'FLOWMETER_VALIDATION_BLOCK', '', '',
          'Расходомер id=' + id + ': ' + validationResult.hardBlock.code +
          ' — ' + validationResult.hardBlock.message);
      } catch (e) { /* audit — не критично */ }
      return { ok: false, error: validationResult.hardBlock.code.toLowerCase(),
               message: validationResult.hardBlock.message };
    }
    var anomalyDetail = validationResult.detail || '';

    // Обновляем ячейки:
    // D=4 (datePrev), E=5 (dateCurr), F=6 (prev), G=7 (curr), I=9 (temp)
    if (datePrevObj) {
      sheet.getRange(rowNum, 4).setValue(datePrevObj);
    } else {
      sheet.getRange(rowNum, 4).setValue(payload.datePrev || '');
    }
    if (dateCurrObj) {
      sheet.getRange(rowNum, 5).setValue(dateCurrObj);
    } else {
      sheet.getRange(rowNum, 5).setValue(payload.dateCurr || '');
    }
    sheet.getRange(rowNum, 6).setValue(prevVal);
    sheet.getRange(rowNum, 7).setValue(currVal);

    // Температура (I=9)
    if (payload.temp !== null && payload.temp !== undefined && payload.temp !== '') {
      sheet.getRange(rowNum, 9).setValue(parseFloat(payload.temp));
    } else {
      sheet.getRange(rowNum, 9).setValue('');
    }

    // Гигакалории пара (J=10, Task 100)
    // Записываются только для расходомеров пара (клиент отправляет gcal только для них).
    // Для остальных расходомеров поле gcal не отправляется — не трогаем ячейку J.
    if (payload.gcal !== null && payload.gcal !== undefined && payload.gcal !== '') {
      sheet.getRange(rowNum, 10).setValue(parseFloat(payload.gcal));
    } else if (payload.gcal === '' || payload.gcal === null) {
      // Явно послана пустая строка/null — очищаем ячейку
      sheet.getRange(rowNum, 10).setValue('');
    }
    // Если payload.gcal === undefined — не трогаем ячейку (старое значение остаётся)

    // Кто внёс изменения: L=12 (modRole), M=13 (modName)
    // Task 108: пишем email (не user.name) — чтобы клиент мог сравнить с KipAuth._cachedEmail
    // Task 211: при смене автора показаний (modName меняется) — старый непустой
    // комментарий O архивируется в archive.P (передаётся параметром comment в
    // appendToArchive; см. ниже). meters.P больше не используется. O очищается,
    // т.к. активный комментарий был привязан к предыдущему автору.
    // Тот же автор перезаписывает свои показания — комментарий O сохраняем,
    // в архиве делается запись с comment='' (старый комментарий не трогаем —
    // он не «архивный», а активный, ещё привязан к тем же показаниям).
    var existingModEmail = String(sheet.getRange(rowNum, 13).getValue() || '');  // M=13
    var oldCommentForArchive = String(sheet.getRange(rowNum, 15).getValue() || '').trim();  // O=15
    var authorChanged = existingModEmail.toLowerCase() !== String(user.email || '').toLowerCase();

    sheet.getRange(rowNum, 12).setValue(user.role || '');
    sheet.getRange(rowNum, 13).setValue(user.email || '');

    if (authorChanged && oldCommentForArchive !== '') {
      // Task 211: meters.P больше не пишем — preview не нужен.
      // Старый комментарий сохранится в archive.P через appendToArchive (вызов ниже).
      // Очистить активный комментарий O (старый текст уже заархивирован в archive.P)
      try {
        sheet.getRange(rowNum, 15).setValue('');  // O=15 — сброс (Task 195)
      } catch (e) { /* не критично */ }
    }

    // Task 108: Записываем timestamp текущего ввода в N=14 (modTimestamp)
    sheet.getRange(rowNum, 14).setValue(new Date());

    // Аудит (по паттерну CableJournal → Utils.audit)
    try {
      Utils.audit(user.email, 'FLOWMETER_UPDATE_READING', '', '',
        'Расходомер id=' + id + ': показания ' + payload.prev + ' → ' + payload.curr);
    } catch (e) { /* audit log — не критично */ }

    // Архив: добавить запись в лист hozraschet_archive
    // (не блокирует основной ответ — ошибка архива тихо логируется)
    // Task 197: в архивную запись копируется старый комментарий O — только
    // если сменился автор показаний. Тот же автор перезаписывает — comment='' ,
    // т.к. активный комментарий остаётся в O и не «архивный».
    try {
      var hozName = String(sheet.getRange(rowNum, 2).getValue() || '');
      var unitVal = String(sheet.getRange(rowNum, 8).getValue() || '');
      var periodVal = String(sheet.getRange(rowNum, 11).getValue() || '');
      FlowmeterArchive.appendToArchive(
        id, hozName,
        prevVal, currVal,
        payload.datePrev, payload.dateCurr,
        payload.temp, payload.gcal, unitVal, periodVal,
        user.role || '', user.name || user.email || '',  // Task 109: имя (если есть) или email
        authorChanged ? oldCommentForArchive : '',  // Task 197: comment архивной записи
        anomalyDetail  // Task 199: строка с кодами аномалий для archive.Q
      );
    } catch (archiveErr) {
      Logger.log('Archive write failed (non-critical): ' + archiveErr.message);
    }

    return { ok: true, data: { id: id } };
  },

  // ============================================================
  // flowmeter.setComment — Task 195: комментарий к последним показаниям
  // ============================================================
  // payload: { token, id, comment }
  //   comment — строка до 500 символов; пустая строка = удалить комментарий.
  // Возвращает: { ok: true, data: { id: N, comment: '...' } }
  //
  // Права: пользователь с правом ввода показаний (INPUT_ROLES), который
  // внёс ПОСЛЕДНИЕ показания (modName в M совпадает с его email).
  // АДМИН (role === 'Админ') может комментировать любые показания —
  // проверка авторства для него пропускается (Task 195 update).
  // Ограничения по времени НЕТ — пока показания за этим пользователем
  // (у админа — безусловно).
  // Комментарий виден всем читателям раздела (list возвращает поле comment).
  // При вводе новых показаний ДРУГИМ пользователем updateReading очищает O
  // и архивирует старый непустой комментарий в archive.P (hozraschet_archive).
  //
  // Task 211: meters.P (archivedComment preview) больше не используется.
  // При перезаписи непустого O новым текстом через setComment — старый
  // комментарий просто теряется (история сохраняется только при смене автора
  // показаний в updateReading — там старый O уходит в archive.P).
  // Удаление (пустой comment) — просто очищает O.
  // Совпадение старый === новый — не плодит дубли.
  // ============================================================
  setComment: function(payload) {
    var auth = this._requireEdit(payload.token);
    if (auth.error) return auth.error;
    var user = auth.user;

    var id = parseInt(payload.id, 10);
    if (!id || id < 1) {
      return { ok: false, error: 'Некорректный id позиции' };
    }

    var comment = String(payload.comment === undefined || payload.comment === null
      ? '' : payload.comment).trim();
    if (comment.length > 500) {
      return { ok: false, error: 'Комментарий длиннее 500 символов' };
    }

    var sheet = this._getSheet();
    if (!sheet) {
      return { ok: false, error: 'Лист не найден' };
    }

    var rowNum = id + 1;
    var lastRow = sheet.getLastRow();
    if (rowNum > lastRow) {
      return { ok: false, error: 'Позиция id=' + id + ' не найдена' };
    }

    // Валидация авторства: комментарий может добавить/изменить только тот,
    // кто вводил ПОСЛЕДНИЕ показания (столбец M — email).
    // АДМИН обходит эту проверку (Task 195 update).
    var isAdmin = (String(user.role || '').toLowerCase() === 'админ');
    if (!isAdmin) {
      var existingModName = String(sheet.getRange(rowNum, 13).getValue() || '').toLowerCase().trim();  // M=13
      var currentUser = String(user.email || '').toLowerCase().trim();
      if (!existingModName || existingModName !== currentUser) {
        return { ok: false, error: 'not_your_input',
                 message: 'Комментарий доступен только тому, кто вводил последние показания' };
      }
    }

    // Task 211: meters.P больше не пишем — preview не нужен.
    // Старый непустой комментарий при замене на новый просто теряется.
    // (История комментариев сохраняется только при смене автора показаний
    //  в updateReading — там старый O уходит в archive.P.)
    // Удаление (comment === '') — просто очищаем O.
    // Совпадение (старый === новый) — ничего не делаем, не плодим дубли.
    var oldComment = String(sheet.getRange(rowNum, 15).getValue() || '').trim();  // O=15

    // Записываем новый комментарий в O=15 (пустая строка = удалить)
    sheet.getRange(rowNum, 15).setValue(comment);

    // Аудит
    try {
      var actionLabel = comment ? 'FLOWMETER_SET_COMMENT' : 'FLOWMETER_DELETE_COMMENT';
      var shortText = comment.length > 60 ? comment.substring(0, 60) + '…' : comment;
      var who = isAdmin ? ' (админ)' : '';
      Utils.audit(user.email, actionLabel, '', '',
        'Расходомер id=' + id + who + ': ' + (comment ? '«' + shortText + '»' : 'комментарий удалён'));
    } catch (e) { /* audit log — не критично */ }

    return { ok: true, data: { id: id, comment: comment } };
  },

  // ============================================================
  // Вспомогательные: конвертация дат
  // ============================================================

  // Дата из таблицы → формат клиента (M/D/YYYY)
  _sheetToClientDate: function(val) {
    if (!val) return '';
    if (val instanceof Date) {
      return (val.getMonth() + 1) + '/' + val.getDate() + '/' + val.getFullYear();
    }
    var s = String(val).trim();
    if (!s) return '';
    // DD.MM.YYYY → M/D/YYYY
    var m = s.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
    if (m) {
      return (+m[2]) + '/' + (+m[1]) + '/' + m[3];
    }
    // M/D/YYYY — вернуть как есть
    if (s.indexOf('/') !== -1) return s;
    return s;
  },

  // Дата из клиента (M/D/YYYY) → Date object для записи в таблицу
  _clientToDateObj: function(val) {
    if (!val) return null;
    var s = String(val).trim();
    // M/D/YYYY → new Date(year, month-1, day)
    var m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (m) {
      var dateObj = new Date(+m[3], +m[1] - 1, +m[2]);
      if (!isNaN(dateObj.getTime())) return dateObj;
    }
    // DD.MM.YYYY → new Date(year, month-1, day)
    var d = s.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
    if (d) {
      var dateObj2 = new Date(+d[3], +d[2] - 1, +d[1]);
      if (!isNaN(dateObj2.getTime())) return dateObj2;
    }
    return null;
  },

  // Парсинг температуры (число или null)
  _parseTemp: function(val) {
    if (val === '' || val === null || val === undefined) return null;
    var n = parseFloat(val);
    return isNaN(n) ? null : n;
  },

  // Парсинг гигакалорий пара (число или null) — Task 100
  _parseGcal: function(val) {
    if (val === '' || val === null || val === undefined) return null;
    var n = parseFloat(val);
    return isNaN(n) ? null : n;
  },

  // Парсинг timestamp последнего ввода (Date → ISO-строка, Task 108)
  _parseTimestamp: function(val) {
    if (val === '' || val === null || val === undefined) return null;
    if (val instanceof Date) {
      return val.toISOString();
    }
    var s = String(val).trim();
    return s || null;
  },

  // ============================================================
  // Task 109: Построить кэш { email → name } из листа users (KIP8_Access)
  // Используется в list() для отображения имени пользователя (а не email)
  // в детальной карточке расходомера.
  //
  // Использует Utils.getRows('users') — возвращает массив объектов
  // с ключами из строки 4 заголовков листа users.
  // Если в таблице есть столбец 'name' — используем его.
  // Если нет — modDisplayName = email (fallback).
  // ============================================================
  _buildUserNameCache: function() {
    var cache = {};
    try {
      if (typeof Utils !== 'undefined' && Utils.getRows) {
        var users = Utils.getRows('users');
        if (users && users.length) {
          for (var i = 0; i < users.length; i++) {
            var u = users[i];
            var email = String(u.email || '').toLowerCase().trim();
            var name = String(u.name || '').trim();
            if (email && name) {
              cache[email] = name;
            }
          }
        }
      }
    } catch (e) {
      // Тихо игнорируем — modDisplayName = email (функциональность не ломается)
    }
    return cache;
  }
};

// ============================================================
// flowmeterCleanupCommentMetadata — Одноразовая миграция (Task 212)
// ============================================================
// Запускается один раз вручную из редактора Apps Script:
//   1. Выбрать функцию flowmeterCleanupCommentMetadata
//   2. Нажать ▶ Run
//   3. Проверить лог — сколько строк исправлено
//   4. После миграции функцию можно удалить из проекта
//
// Что делает:
//   • Проходит по столбцу P (16) листа hozraschet_meters и листа
//     hozraschet_archive.
//   • В каждой ячейке ищет шаблон «[ISO-timestamp | email]: текст»
//     (формат preview, который писался в meters.P до Task 211).
//   • Если совпало — заменяет значение на чистый «текст» без метаданных.
//   • Если не совпало — оставляет как есть (plain text уже).
//
// Цель: привести исторические данные к единому plain-text формату,
// который используется после Task 211. После миграции НОВЫЕ записи
// тоже будут plain text (см. Flowmeter.updateReading → appendToArchive
// и отсутствие записи в meters.P).
// ============================================================
function flowmeterCleanupCommentMetadata() {
  var SPREADSHEET_ID = '1enZSq7K8pwJVzaAI_tbXZtvATqARTxH0lSU4c-wc1eY';
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);

  // Шаблон: [2026-08-27T22:51:15.659Z | email@host]: текст
  //Capture group 1 = текст после «]: »
  var pattern = /^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z \| [^\]]+\]:\s*(.*)$/;
  var COL = 16; // P=16

  var result = { metersProcessed: 0, metersFixed: 0,
                 archiveProcessed: 0, archiveFixed: 0 };

  // 1) hozraschet_meters — столбец P, строки 2+ (до 12 позиций, но берём все)
  try {
    var metersSheet = ss.getSheetByName('hozraschet_meters');
    if (metersSheet) {
      var metersLastRow = metersSheet.getLastRow();
      if (metersLastRow >= 2) {
        var metersRange = metersSheet.getRange(2, COL, metersLastRow - 1, 1);
        var metersVals = metersRange.getValues();
        var metersChanged = false;
        for (var i = 0; i < metersVals.length; i++) {
          result.metersProcessed++;
          var v = String(metersVals[i][0] || '');
          var m = v.match(pattern);
          if (m) {
            metersVals[i][0] = m[1]; // только текст
            result.metersFixed++;
            metersChanged = true;
          }
        }
        if (metersChanged) {
          metersRange.setValues(metersVals);
        }
      }
    }
  } catch (e) {
    Logger.log('Cleanup meters failed: ' + e.message);
  }

  // 2) hozraschet_archive — столбец P, строки 2+
  try {
    var archiveSheet = ss.getSheetByName('hozraschet_archive');
    if (archiveSheet) {
      var archiveLastRow = archiveSheet.getLastRow();
      if (archiveLastRow >= 2) {
        var archiveRange = archiveSheet.getRange(2, COL, archiveLastRow - 1, 1);
        var archiveVals = archiveRange.getValues();
        var archiveChanged = false;
        for (var j = 0; j < archiveVals.length; j++) {
          result.archiveProcessed++;
          var av = String(archiveVals[j][0] || '');
          var am = av.match(pattern);
          if (am) {
            archiveVals[j][0] = am[1];
            result.archiveFixed++;
            archiveChanged = true;
          }
        }
        if (archiveChanged) {
          archiveRange.setValues(archiveVals);
        }
      }
    }
  } catch (e) {
    Logger.log('Cleanup archive failed: ' + e.message);
  }

  var msg = 'Cleanup done. meters: ' + result.metersFixed + '/' + result.metersProcessed +
            ' fixed, archive: ' + result.archiveFixed + '/' + result.archiveProcessed + ' fixed.';
  Logger.log(msg);
  return msg;
}
