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
// Структура Google Таблицы «hozraschet_meters»:
//   Столбцы (строка 1 — заголовки):
//     A: id         — номер позиции (1–12)
//     B: hoz        — название (Хозрасчёт №1)
//     C: param      — параметр (Расход пара в корпус 114)
//     D: datePrev   — предыдущая дата (M/D/YYYY)
//     E: dateCurr   — текущая дата (M/D/YYYY)
//     F: prev       — предыдущие показания (число)
//     G: curr       — текущие показания (число)
//     H: unit       — единица измерения (т, м³)
//     I: temp       — температура среды (число или пусто)
//     J: period     — периодичность (Ежедневно/Еженедельно/Ежемесячно)
//
//   Строка 2 — первая запись (id=1), строка 13 — последняя (id=12).
//   Данные начинаются со строки 2 (строка 1 — заголовки).
// ============================================================

var Flowmeter = {

  // ID Google Таблицы «hozraschet_meters»
  SPREADSHEET_ID: '1enZSq7K8pwJVzaAI_tbXZtvATqARTxH0lSU4c-wc1eY',

  // Имя листа в таблице
  SHEET_NAME: 'hozraschet_meters',

  // ============================================================
  // flowmeter.list — прочитать все позиции расходомеров
  // ============================================================
  // payload: { token }
  // Возвращает: { ok: true, data: { meters: [...] } }
  list: function(payload) {
    // Авторизация: любой аутентифицированный пользователь может читать
    var user = Utils.verifyToken(payload.token);
    if (!user) return { ok: false, error: 'no_session' };

    // Проверка роли: нужны права на просмотр расходомеров
    // (роли с доступом: КИП ИОС дежурный, ИТР8, ИТР8 pro, ИТР ИОС, КИП ИОС pro, Админ)
    var FLOWMETER_ROLES = ['КИП ИОС дежурный', 'ИТР8', 'ИТР8 pro', 'ИТР ИОС',
                           'КИП ИОС pro', 'Админ'];
    if (FLOWMETER_ROLES.indexOf(user.role) === -1) {
      return { ok: false, error: 'access_denied' };
    }

    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    var sheet = ss.getSheetByName(this.SHEET_NAME);
    if (!sheet) {
      return { ok: false, error: 'Лист «' + this.SHEET_NAME + '» не найден' };
    }

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) {
      return { ok: true, data: { meters: [] } };
    }

    // Читаем все данные (строка 2 до lastRow, столбцы A–J)
    var range = sheet.getRange(2, 1, lastRow - 1, 10);
    var values = range.getValues();

    var meters = [];
    for (var i = 0; i < values.length; i++) {
      var row = values[i];
      // Пропускаем пустые строки
      if (!row[0] && !row[1]) continue;

      var meter = {
        id:     parseInt(row[0], 10) || (i + 1),
        hoz:    String(row[1] || ''),
        param:  String(row[2] || ''),
        datePrev: this._formatDate(row[3]),
        dateCurr: this._formatDate(row[4]),
        prev:   parseFloat(row[5]) || 0,
        curr:   parseFloat(row[6]) || 0,
        unit:   String(row[7] || ''),
        temp:   (row[8] !== '' && row[8] !== null && row[8] !== undefined) ? parseFloat(row[8]) : null,
        period: String(row[9] || '')
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
  // Записывает в строку (id + 1) столбцы D, E, F, G, I:
  //   D → datePrev, E → dateCurr, F → prev, G → curr, I → temp
  updateReading: function(payload) {
    // Авторизация
    var user = Utils.verifyToken(payload.token);
    if (!user) return { ok: false, error: 'no_session' };

    // Только роли с правом ввода показаний могут писать
    var INPUT_ROLES = ['КИП ИОС дежурный', 'Админ'];
    if (INPUT_ROLES.indexOf(user.role) === -1) {
      return { ok: false, error: 'access_denied' };
    }

    var id = parseInt(payload.id, 10);
    if (!id || id < 1) {
      return { ok: false, error: 'Некорректный id позиции' };
    }

    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    var sheet = ss.getSheetByName(this.SHEET_NAME);
    if (!sheet) {
      return { ok: false, error: 'Лист «' + this.SHEET_NAME + '» не найден' };
    }

    // Строка в таблице: id + 1 (строка 1 — заголовки, строка 2 — id=1)
    var rowNum = id + 1;
    var lastRow = sheet.getLastRow();
    if (rowNum > lastRow) {
      return { ok: false, error: 'Позиция id=' + id + ' не найдена' };
    }

    // Обновляем ячейки: D(datePrev), E(dateCurr), F(prev), G(curr), I(temp)
    // Столбцы: D=4, E=5, F=6, G=7, I=9
    sheet.getRange(rowNum, 4).setValue(payload.datePrev || '');  // D: datePrev
    sheet.getRange(rowNum, 5).setValue(payload.dateCurr || '');  // E: dateCurr
    sheet.getRange(rowNum, 6).setValue(parseFloat(payload.prev) || 0);  // F: prev
    sheet.getRange(rowNum, 7).setValue(parseFloat(payload.curr) || 0);  // G: curr

    // Температура: если null/undefined — очищаем ячейку
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
  // Вспомогательная: форматирование даты для клиента
  // Google Sheets хранит даты как Date objects или строки
  // Клиент ожидает формат M/D/YYYY
  // ============================================================
  _formatDate: function(val) {
    if (!val) return '';
    if (val instanceof Date) {
      return (val.getMonth() + 1) + '/' + val.getDate() + '/' + val.getFullYear();
    }
    return String(val);
  }
};
