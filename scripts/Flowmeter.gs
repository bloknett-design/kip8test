// ============================================================
// Flowmeter.gs — Расходомеры хозрасчётные: чтение/запись данных
// в Google Таблицу hozraschet_meters
// ============================================================
// Развернуть в том же Apps Script проекте, где находятся
// Code.gs, Utils.gs, CableJournal.gs.
//
// Эндпоинты (вызываются через doPost):
//   flowmeter.list         — прочитать все позиции расходомеров
//   flowmeter.updateReading — обновить показания одной позиции
//
// Структура листа «hozraschet_meters» в Google Таблице:
//   Строка 1 — заголовки столбцов
//   Строки 2+ — данные (12 позиций, строки 2–13)
//
//   Столбцы (A–J):
//     A: id         — номер позиции (1–12)
//     B: hoz        — название (Хозрасчёт №1)
//     C: param      — параметр (Расход пара в корпус 114)
//     D: datePrev   — предыдущая дата (Date object в ячейке)
//     E: dateCurr   — текущая дата (Date object в ячейке)
//     F: prev       — предыдущие показания (число)
//     G: curr       — текущие показания (число)
//     H: unit       — единица измерения (т, м³)
//     I: temp       — температура среды (число или пусто)
//     J: period     — периодичность (Ежедневно/Еженедельно/Ежемесячно)
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

  // ============================================================
  // Получить лист таблицы по имени, с fallback на первый лист
  // ============================================================
  _getSheet: function() {
    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    // Сначала пробуем по имени
    var sheet = ss.getSheetByName(this.SHEET_NAME);
    if (sheet) return sheet;
    // Fallback: первый лист
    var sheets = ss.getSheets();
    if (sheets.length > 0) return sheets[0];
    return null;
  },

  // ============================================================
  // flowmeter.list — прочитать все позиции расходомеров
  // ============================================================
  // payload: { token }
  // Возвращает: { ok: true, data: { meters: [...] } }
  list: function(payload) {
    // Авторизация — через Utils.getCurrentUser (та же функция, что в Code.gs)
    var auth = Utils.getCurrentUser({ token: payload.token });
    if (!auth || !auth.ok || !auth.data) return { ok: false, error: 'no_session' };
    var user = auth.data;

    // Проверка роли
    var FLOWMETER_ROLES = ['КИП ИОС дежурный', 'ИТР8', 'ИТР8 pro', 'ИТР ИОС',
                           'КИП ИОС pro', 'Админ'];
    if (FLOWMETER_ROLES.indexOf(user.role) === -1) {
      return { ok: false, error: 'access_denied' };
    }

    var sheet = this._getSheet();
    if (!sheet) {
      return { ok: false, error: 'Лист не найден' };
    }

    var lastRow = sheet.getLastRow();
    if (lastRow < this.DATA_START_ROW) {
      return { ok: true, data: { meters: [] } };
    }

    // Читаем данные (строка DATA_START_ROW до lastRow, столбцы A–J)
    var range = sheet.getRange(this.DATA_START_ROW, 1, lastRow - this.DATA_START_ROW + 1, 10);
    var values = range.getValues();

    var meters = [];
    for (var i = 0; i < values.length; i++) {
      var row = values[i];
      // Пропускаем пустые строки
      if (!row[0] && !row[1]) continue;

      var meter = {
        id:       parseInt(row[0], 10) || (i + 1),
        hoz:      String(row[1] || ''),
        param:    String(row[2] || ''),
        datePrev: this._sheetToClientDate(row[3]),
        dateCurr: this._sheetToClientDate(row[4]),
        prev:     parseFloat(row[5]) || 0,
        curr:     parseFloat(row[6]) || 0,
        unit:     String(row[7] || ''),
        temp:     this._parseTemp(row[8]),
        period:   String(row[9] || '')
      };
      meters.push(meter);
    }

    return { ok: true, data: { meters: meters } };
  },

  // ============================================================
  // flowmeter.updateReading — обновить показания одной позиции
  // ============================================================
  // payload: { token, id, prev, curr, datePrev, dateCurr, temp }
  // Возвращает: { ok: true, data: { id: N } }
  //
  // Записывает в строку (id + 1):
  //   D → datePrev (Date), E → dateCurr (Date),
  //   F → prev, G → curr, I → temp
  updateReading: function(payload) {
    // Авторизация — через Utils.getCurrentUser (та же функция, что в Code.gs)
    var auth = Utils.getCurrentUser({ token: payload.token });
    if (!auth || !auth.ok || !auth.data) return { ok: false, error: 'no_session' };
    var user = auth.data;

    // Только роли с правом ввода показаний могут писать
    var INPUT_ROLES = ['КИП ИОС дежурный', 'Админ'];
    if (INPUT_ROLES.indexOf(user.role) === -1) {
      return { ok: false, error: 'access_denied' };
    }

    var id = parseInt(payload.id, 10);
    if (!id || id < 1) {
      return { ok: false, error: 'Некорректный id позиции' };
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
    // Записываем Date object, чтобы Google Sheets хранил дату
    // корректно и отображал по локали без двусмысленности.
    var datePrevObj = this._clientToDateObj(payload.datePrev);
    var dateCurrObj = this._clientToDateObj(payload.dateCurr);
    var prevVal = parseFloat(payload.prev) || 0;
    var currVal = parseFloat(payload.curr) || 0;

    // Обновляем ячейки:
    // D=4 (datePrev), E=5 (dateCurr), F=6 (prev), G=7 (curr), I=9 (temp)
    if (datePrevObj) {
      sheet.getRange(rowNum, 4).setValue(datePrevObj);  // D: datePrev (Date)
    } else {
      sheet.getRange(rowNum, 4).setValue(payload.datePrev || '');  // fallback: строка
    }
    if (dateCurrObj) {
      sheet.getRange(rowNum, 5).setValue(dateCurrObj);  // E: dateCurr (Date)
    } else {
      sheet.getRange(rowNum, 5).setValue(payload.dateCurr || '');  // fallback: строка
    }
    sheet.getRange(rowNum, 6).setValue(prevVal);         // F: prev
    sheet.getRange(rowNum, 7).setValue(currVal);         // G: curr

    // Температура (I=9)
    if (payload.temp !== null && payload.temp !== undefined && payload.temp !== '') {
      sheet.getRange(rowNum, 9).setValue(parseFloat(payload.temp));
    } else {
      sheet.getRange(rowNum, 9).setValue('');
    }

    // Логирование в audit_log
    try {
      Utils.logAction(user.userId, 'FLOWMETER_UPDATE_READING',
        'Расходомер id=' + id + ': показания ' + payload.prev + ' → ' + payload.curr);
    } catch (e) { /* audit log — не критично */ }

    return { ok: true, data: { id: id } };
  },

  // ============================================================
  // Вспомогательные: конвертация дат
  // ============================================================

  // Дата из таблицы → формат клиента (M/D/YYYY)
  // Google Sheets может хранить как Date object или как строку.
  // Строка может быть в формате DD.MM.YYYY (русская локаль)
  // или M/D/YYYY (если записана как текст).
  _sheetToClientDate: function(val) {
    if (!val) return '';
    // Date object — надёжный способ (Google Sheets распознал дату)
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
  // Запись Date object исключает двусмысленность при парсинге
  // Google Sheets (проблема локали D/M/YYYY vs M/D/YYYY).
  _clientToDateObj: function(val) {
    if (!val) return null;
    var s = String(val).trim();
    // M/D/YYYY → new Date(year, month-1, day)
    var m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (m) {
      var dateObj = new Date(+m[3], +m[1] - 1, +m[2]);
      // Проверка валидности
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
  }
};
