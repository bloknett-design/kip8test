// ============================================================
// PlanEvents.gs — «Плановые мероприятия»: отметки выполнения
// + архив в файле Мероприятия_КИП_ИОС (Task 463)
// ============================================================
// Разворачивать в ТОМ ЖЕ Apps Script проекте, где Code.gs,
// Utils.gs, RoleMatrixGate.gs, WorkSchedule.gs (проект
// развёртывания AKfycbyt… — ОДИН бэкенд на kip8 и kip8test).
//
// В Code.gs (doPost) добавить два case (см. scripts/Code.gs —
// эталон уже обновлён):
//   case 'planEvents.list':
//     return _json(PlanEvents.list(payload));
//   case 'planEvents.mark':
//     return _json(PlanEvents.mark(payload));
//
// ЭНДПОИНТЫ (через KipAuth.api клиента — модуль PlanEventsData):
//   planEvents.list — отметки года: {token, year}
//     → {ok, data: {marks: [{id, дата_выполнения, мероприятие,
//        год, месяц}], srvVer: '463'}}
//   planEvents.mark — отметить выполнение: {token, year, month,
//     event, date('ГГГГ-ММ-ДД')}
//     → {ok, data: {mark: {…}, already: bool}}
//     ИДЕМПОТЕНТНОСТЬ: запись (год, месяц, мероприятие) уже есть →
//     новая НЕ создаётся, возвращается существующая (already: true)
//     — защита от дублей при повторных кликах/ретраях клиента.
//
// ДАННЫЕ — ОТДЕЛЬНЫЙ файл Мероприятия_КИП_ИОС (Google Sheets):
//   SPREADSHEET_ID ниже. Лист «Архив» создаётся одноразовым
//   идемпотентным scripts/PlanEventsInit.gs (функция
//   planEventsDeploy). Структура (заголовки в строке 1):
//     A: id              — автоинкремент (max + 1)
//     B: дата_выполнения — 'ГГГГ-ММ-ДД' (текст, формат '@')
//     C: мероприятие     — наименование из таблицы раздела
//     D: год             — число (2026)
//     E: месяц           — 1..12
//     F: email           — кто отметил (из сессии)
//     G: время_отметки   — ISO timestamp (текст, формат '@')
//   Ручные правки пользователем поддерживаются: строки
//   парсятся снисходительно (дата и текстом, и Date-объектом;
//   битые строки молча пропускаются — как «Отпуска» Task 279).
//
// ДОСТУП — право plan.events матрицы KIP8_Access (Task 462):
// и чтение, и отметка — одним правом (видеть раздел = отмечать
// выполнение; разделение не требуется по заявке Task 463).
// RoleMatrixGate.gs не задеплоен → отказ всем (fail-closed).
//
// Авторизация — по тому же паттерну, что WorkSchedule.gs:
//   Utils.findSessionByToken(token) → session
//   Utils.findUserById(session.user_id) → user
// ============================================================

var PlanEvents = {

  // Файл Мероприятия_КИП_ИОС (Task 463; доступ у сервисного
  // аккаунта Apps Script — тот же, что у таблицы табель_КИП_ИОС)
  SPREADSHEET_ID: '1uX8Bz6FBS9HniZfWQnHeeyccTwwjwyvpPFWyFkIclCs',
  ARCHIVE_SHEET: 'Архив',

  // Task 463: версия серверного кода (клиент отличает старый
  // Apps Script: нет action → «Unknown action» — молчаливая
  // деградация без отметок, см. DEPLOY Task 463)
  SRV_VER: '463',

  // ============================================================
  // planEvents.list — отметки года
  // ============================================================
  // payload: { token, year }  (год не указан — все записи листа)
  // returns: { ok: true, data: { marks: [...], srvVer } }
  list: function(payload) {
    var g = this._requireAccess(payload.token);
    if (g.error) return g.error;

    var sheet = this._getArchiveSheet();
    if (!sheet) {
      return { ok: false, error: 'sheet_not_found',
               message: 'Лист «Архив» в файле Мероприятия_КИП_ИОС не найден — запустите planEventsDeploy() (scripts/PlanEventsInit.gs, Task 463)' };
    }

    var year = payload.year ? parseInt(payload.year, 10) : null;
    var lastRow = sheet.getLastRow();
    var marks = [];
    if (lastRow >= 2) {
      var vals = sheet.getRange(2, 1, lastRow - 1, 7).getValues();
      for (var i = 0; i < vals.length; i++) {
        var rec = this._rowToMark(vals[i]);
        if (!rec) continue;                     // битая строка — мимо
        if (year && rec['год'] !== year) continue;
        marks.push(rec);
      }
    }
    return { ok: true, data: { marks: marks, srvVer: this.SRV_VER } };
  },

  // ============================================================
  // planEvents.mark — отметить выполнение (идемпотентно)
  // ============================================================
  // payload: { token, year, month(1..12), event, date('ГГГГ-ММ-ДД') }
  // returns: { ok: true, data: { mark: {...}, already: bool } }
  mark: function(payload) {
    var g = this._requireAccess(payload.token);
    if (g.error) return g.error;
    var user = g.user;

    var year = parseInt(payload.year, 10);
    var month = parseInt(payload.month, 10);
    var event = String(payload.event || '').trim();
    var date = this._normDate(payload.date);
    if (isNaN(year) || year < 2000 || year > 2100) {
      return { ok: false, error: 'invalid_year',
               message: 'Год отметки не распознан' };
    }
    if (isNaN(month) || month < 1 || month > 12) {
      return { ok: false, error: 'invalid_month',
               message: 'Месяц отметки должен быть 1..12' };
    }
    if (!event || event.length > 200) {
      return { ok: false, error: 'invalid_event',
               message: 'Наименование мероприятия пустое или длиннее 200 символов' };
    }
    if (!date) {
      return { ok: false, error: 'invalid_date',
               message: 'Дата выполнения не распознана (нужен формат ГГГГ-ММ-ДД)' };
    }

    var sheet = this._getArchiveSheet();
    if (!sheet) {
      return { ok: false, error: 'sheet_not_found',
               message: 'Лист «Архив» в файле Мероприятия_КИП_ИОС не найден — запустите planEventsDeploy() (scripts/PlanEventsInit.gs, Task 463)' };
    }

    // Идемпотентность: (год, месяц, мероприятие) уже отмечено →
    // существующая запись, новой НЕ создаём (дубли невозможны)
    var lastRow = sheet.getLastRow();
    var maxId = 0;
    if (lastRow >= 2) {
      var vals = sheet.getRange(2, 1, lastRow - 1, 7).getValues();
      for (var i = 0; i < vals.length; i++) {
        var rec = this._rowToMark(vals[i]);
        var rowId = parseInt(vals[i][0], 10);
        if (!isNaN(rowId) && rowId > maxId) maxId = rowId;
        if (!rec) continue;
        if (rec['год'] === year && rec['месяц'] === month &&
            rec['мероприятие'] === event) {
          try {
            Utils.audit(user.email, 'PLAN_EVENTS_MARK_IDEMPOTENT', '', '',
              'Отметка уже была: ' + event + ' ' + month + '/' + year);
          } catch (e) { /* ignore */ }
          return { ok: true, data: { mark: rec, already: true } };
        }
      }
    }

    var row = [maxId + 1, date, event, year, month,
               String(user.email || ''), this._isoNow()];
    sheet.appendRow(row);
    try {
      Utils.audit(user.email, 'PLAN_EVENTS_MARK', '', '',
        'Отмечено: ' + event + ' — ' + date + ' (' + month + '/' + year + ')');
    } catch (e) { /* ignore */ }
    return { ok: true, data: { mark: this._rowToMark(row), already: false } };
  },

  // ============================================================
  // Внутренние хелперы
  // ============================================================

  // Доступ — право plan.events (Task 462). RoleMatrixGate.gs не
  // задеплоен → отказ всем: модуль появился ПОСЛЕ Task 295, у него
  // нет «старых списков ролей» (fail-closed, как матричные группы)
  _requireAccess: function(token) {
    if (typeof rmRequirePerm !== 'function') {
      return { error: { ok: false, error: 'access_denied',
               message: 'RoleMatrixGate.gs не задеплоен — план-эвентс закрыт (fail-closed)' } };
    }
    var g = rmRequirePerm(token, 'plan.events', 'PlanEvents');
    if (!g.ok) return { error: { ok: false, error: g.error } };
    return { user: g.user };
  },

  // Лист «Архив» (null — нет файла/листа; запись невозможна до
  // запуска PlanEventsInit.gs — клиент покажет понятную ошибку)
  _getArchiveSheet: function() {
    try {
      var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
      if (!ss) return null;
      return ss.getSheetByName(this.ARCHIVE_SHEET);
    } catch (e) {
      return null;
    }
  },

  // Строка листа → отметка. Битые (нет id/наименования/месяца) —
  // null, молча пропускаются (ручные правки не ломают список)
  _rowToMark: function(r) {
    var id = parseInt(r[0], 10);
    if (isNaN(id)) return null;
    var event = String(r[2] || '').trim();
    if (!event) return null;
    var year = parseInt(r[3], 10);
    var month = parseInt(r[4], 10);
    if (isNaN(year) || isNaN(month) || month < 1 || month > 12) return null;
    return {
      id: id,
      'дата_выполнения': this._normDate(r[1]),
      'мероприятие': event,
      'год': year,
      'месяц': month
    };
  },

  // Дата листа/клиента → 'ГГГГ-ММ-ДД' ('' — не распознана).
  // Понимает: Date-объект (Google Sheets), 'ГГГГ-ММ-ДД',
  // 'ДД.ММ.ГГГГ' / 'ДД/ММ/ГГГГ' (ручное заполнение)
  _normDate: function(v) {
    if (v === null || v === undefined || v === '') return '';
    if (Object.prototype.toString.call(v) === '[object Date]') {
      if (isNaN(v.getTime())) return '';
      return Utilities.formatDate(v, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    }
    var s = String(v).trim();
    var m = /^(\d{4})-(\d{1,2})-(\d{1,2})/.exec(s);
    if (m) {
      return m[1] + '-' + (m[2].length < 2 ? '0' : '') + m[2] +
             '-' + (m[3].length < 2 ? '0' : '') + m[3];
    }
    m = /^(\d{1,2})[.\/](\d{1,2})[.\/](\d{4})$/.exec(s);
    if (m) {
      return m[3] + '-' + (m[2].length < 2 ? '0' : '') + m[2] +
             '-' + (m[1].length < 2 ? '0' : '') + m[1];
    }
    return '';
  },

  // ISO timestamp момента отметки (время_отметки, колонка G)
  _isoNow: function() {
    return Utilities.formatDate(new Date(), Session.getScriptTimeZone(),
                                "yyyy-MM-dd'T'HH:mm:ss");
  }
};
