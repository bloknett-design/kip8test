/**
 * Utils.gs — Вспомогательные функции
 * ============================================================
 * Чтение/запись листов, валидация, генерация токенов,
 * нормализация email, rate limiting, cleanup.
 *
 * Task 347 (2026-09-08): добавлена Utils.cleanupStaleSessions() —
 * чистка «заброшенных» строк листа sessions (last_heartbeat старше
 * N дней; config STALE_SESSION_DAYS, по умолчанию 30). Вызывается
 * из hourlyCleanup (Code.gs, одна строка). Диагноз: за месяцы
 * тестов в листе sessions накопились десятки строк-сирот (старый
 * logout их не удалял, входы без выхода, а сессии по заявке
 * бессрочные), из-за них фикс Task 346 не сбрасывал login_status
 * последней сессии («another session stays active»). Справочник
 * соответствует живому Utils.gs (прислан 2026-09-08, включая
 * встроенные Admin.gs и setupTriggers) + новая функция.
 */

const Utils = {

  /** Кэш листов (один getActiveSheet за вызов). */
  _sheetCache: {},

  /** Получить лист по имени (с кэшем). */
  getSheet: function(name) {
    if (!this._sheetCache[name]) {
      this._sheetCache[name] = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
    }
    return this._sheetCache[name];
  },

  /** Получить все строки листа как массив объектов (ключи — из строки 4 заголовков). */
  getRows: function(name) {
    const sheet = this.getSheet(name);
    if (!sheet || sheet.getLastRow() < 4) return [];
    const range = sheet.getRange(4, 1, sheet.getLastRow() - 3, sheet.getLastColumn());
    const values = range.getValues();
    const headers = values[0];
    const rows = [];
    for (let i = 1; i < values.length; i++) {
      const obj = { row: i + 4 }; // номер строки в таблице
      for (let j = 0; j < headers.length; j++) {
        obj[headers[j]] = values[i][j];
      }
      rows.push(obj);
    }
    return rows;
  },

  /** Добавить строку в лист. */
  appendRow: function(name, values) {
    const sheet = this.getSheet(name);
    sheet.appendRow(values);
  },

  /** Удалить строку по номеру. */
  deleteRow: function(name, rowNum) {
    const sheet = this.getSheet(name);
    sheet.deleteRow(rowNum);
  },

  /** Обновить ячейку. */
  setCell: function(name, rowNum, colNum, value) {
    const sheet = this.getSheet(name);
    sheet.getRange(rowNum, colNum).setValue(value);
  },

  // ========================================================================
  // CONFIG
  // ========================================================================

  /** Получить значение настройки из листа config. */
  getConfig: function(key, defaultValue) {
    const rows = this.getRows('config');
    for (let i = 0; i < rows.length; i++) {
      if (rows[i].key === key) {
        const v = rows[i].value;
        // Если значение числовое — вернуть число
        if (typeof v === 'number') return v;
        if (typeof v === 'string' && /^\d+$/.test(v)) return parseInt(v, 10);
        return v;
      }
    }
    return defaultValue;
  },

  // ========================================================================
  // USERS
  // ========================================================================

  /** Найти пользователя по email. Возвращает {id, email, role, login_status, last_login, row} или null. */
  findUserByEmail: function(email) {
    const rows = this.getRows('users');
    for (let i = 0; i < rows.length; i++) {
      if (String(rows[i].email || '').toLowerCase() === email.toLowerCase()) {
        return rows[i];
      }
    }
    return null;
  },

  /** Найти пользователя по ID. */
  findUserById: function(id) {
    const rows = this.getRows('users');
    for (let i = 0; i < rows.length; i++) {
      if (Number(rows[i].ID) === Number(id)) {
        return rows[i];
      }
    }
    return null;
  },

  /** Обновить login_status и last_login в строке users. */
  updateUserStatus: function(rowNum, status, lastLogin) {
    const sheet = this.getSheet('users');
    sheet.getRange(rowNum, 4).setValue(status);   // login_status = D
    if (lastLogin !== undefined) {
      sheet.getRange(rowNum, 5).setValue(lastLogin); // last_login = E
    }
  },

  // ========================================================================
  // SESSIONS
  // ========================================================================

  /** Найти сессию по token. */
  findSessionByToken: function(token) {
    const rows = this.getRows('sessions');
    for (let i = 0; i < rows.length; i++) {
      if (rows[i].session_token === token) return rows[i];
    }
    return null;
  },

  /**
   * Проверить, есть ли у пользователя активная сессия.
   * Возвращает true, если есть хотя бы одна запись в sessions для этого пользователя.
   *
   * ВАЖНО: сессии НЕ истекают по времени. Активной считается любая запись
   * в таблице sessions для этого пользователя.
   *
   * Используется в Auth.sendOTP для проверки "уже выполнен вход":
   * если login_status = 'вход выполнен', но записей в sessions нет — значит
   * login_status устарел, и его нужно сбросить, а не блокировать вход.
   */
  userHasActiveSession: function(userId) {
    const rows = this.getRows('sessions');
    for (let i = 0; i < rows.length; i++) {
      if (Number(rows[i].user_id) === Number(userId)) {
        return true;
      }
    }
    return false;
  },

  // ========================================================================
  // OTP
  // ========================================================================

  /** Получить последний активный (не used) OTP для email. */
  getActiveOtpForEmail: function(email) {
    const rows = this.getRows('otp_codes');
    let latest = null;
    for (let i = 0; i < rows.length; i++) {
      if (String(rows[i].email || '').toLowerCase() === email.toLowerCase() &&
          rows[i].used !== true && String(rows[i].used).toUpperCase() !== 'TRUE') {
        if (!latest || rows[i].created_at.getTime() > latest.created_at.getTime()) {
          latest = rows[i];
        }
      }
    }
    return latest;
  },

  /** Получить последний OTP для email (любой, включая used). */
  getLastOtpForEmail: function(email) {
    const rows = this.getRows('otp_codes');
    let latest = null;
    for (let i = 0; i < rows.length; i++) {
      if (String(rows[i].email || '').toLowerCase() === email.toLowerCase()) {
        if (!latest || rows[i].created_at.getTime() > latest.created_at.getTime()) {
          latest = rows[i];
        }
      }
    }
    return latest;
  },

  /** Пометить OTP как использованный. */
  markOtpUsed: function(rowNum) {
    const sheet = this.getSheet('otp_codes');
    sheet.getRange(rowNum, 5).setValue('TRUE'); // used = E
  },

  /** Увеличить счётчик попыток для OTP. */
  incrementOtpAttempts: function(rowNum) {
    const sheet = this.getSheet('otp_codes');
    const cell = sheet.getRange(rowNum, 6); // attempts = F
    const cur = parseInt(cell.getValue() || '0', 10);
    cell.setValue(cur + 1);
  },

  /** Подсчитать неудачные попытки OTP для email за последние N минут. */
  countRecentOtpFails: function(email, minutes) {
    const since = new Date(Date.now() - minutes * 60 * 1000);
    const rows = this.getRows('audit_log');
    let count = 0;
    for (let i = 0; i < rows.length; i++) {
      if (rows[i].email === email &&
          rows[i].action === 'OTP_FAILED' &&
          rows[i].timestamp instanceof Date &&
          rows[i].timestamp.getTime() > since.getTime()) {
        count++;
      }
    }
    return count;
  },

  // ========================================================================
  // AUDIT LOG
  // ========================================================================

  /** Записать событие в audit_log. */
  audit: function(email, action, ip, userAgent, details) {
    this.appendRow('audit_log', [
      new Date(),
      email || '',
      action || '',
      ip || '',
      userAgent || '',
      details || ''
    ]);
  },

  /** Подсчитать события action за последние N минут (глобально). */
  countRecentAuditLogs: function(action, minutes) {
    const since = new Date(Date.now() - minutes * 60 * 1000);
    const rows = this.getRows('audit_log');
    let count = 0;
    for (let i = 0; i < rows.length; i++) {
      if (rows[i].action === action &&
          rows[i].timestamp instanceof Date &&
          rows[i].timestamp.getTime() > since.getTime()) {
        count++;
      }
    }
    return count;
  },

  /** Подсчитать события action с конкретного IP за последние N минут. */
  countRecentAuditLogsByIp: function(action, ip, minutes) {
    if (!ip) return 0;
    const since = new Date(Date.now() - minutes * 60 * 1000);
    const rows = this.getRows('audit_log');
    let count = 0;
    for (let i = 0; i < rows.length; i++) {
      if (rows[i].action === action &&
          rows[i].ip === ip &&
          rows[i].timestamp instanceof Date &&
          rows[i].timestamp.getTime() > since.getTime()) {
        count++;
      }
    }
    return count;
  },

  // ========================================================================
  // VALIDATION & GENERATORS
  // ========================================================================

  /** Нормализовать email: lowercase, trim, базовая валидация. */
  normalizeEmail: function(raw) {
    if (!raw) return '';
    const s = String(raw).toLowerCase().trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s)) return '';
    return s;
  },

  /** Сгенерировать случайный токен заданной длины. */
  generateToken: function(length) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let out = '';
    for (let i = 0; i < length; i++) {
      out += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return out;
  },

  /** Сгенерировать числовой код заданной длины (например, 6 = 100000..999999). */
  generateNumericCode: function(length) {
    const min = Math.pow(10, length - 1);
    const max = Math.pow(10, length) - 1;
    return String(Math.floor(min + Math.random() * (max - min + 1)));
  },

  /** Получить IP клиента (из заголовков Apps Script). */
  getClientIp: function() {
    // Apps Script не предоставляет прямого доступа к IP,
    // но в некоторых сценариях его можно вытащить из заголовков.
    // Для простоты — пустая строка (при необходимости можно расширить).
    return '';
  },

  /** Получить User-Agent клиента. */
  getClientUserAgent: function() {
    return '';
  },

  // ========================================================================
  // ROLES (источник истины — Карта ролей, см. kip8-desktop/tests/test-role-access.js)
  // ========================================================================

  /**
   * Полный список допустимых ролей.
   * ============================================================
   * Порядок соответствует карте ролей (tests/test-role-access.js):
   *   1. Запрет
   *   2. Общий доступ
   *   3. ИТР ТОКЕМ                 — калькуляторы + ограниченный КИП ИОС + «Что нового» (фильтры 1, 4, 8)
   *   4. КИП8                       — калькуляторы + билеты + секретные + «Что нового»
   *   5. КИП8 pro                   — КИП8 + расходомеры
   *   6. КИП ИОС                    — КИП8 + КИП ИОС
   *   7. КИП ИОС pro                — КИП ИОС + «Проекты» и «Каб.журнал» (фильтр 5)
   *   8. КИП ИОС дежурный           — КИП ИОС pro + расходомеры + canInputReadings
   *   9. ИТР8                       — КИП ИОС + расходомеры
   *  10. ИТР8 pro                   — ИТР8
   *  11. ИТР ИОС                    — ИТР8 + «Проекты»/«Каб.журнал»
   *  12. Админ                      — полный доступ (фильтры 1-11)
   *
   * ВАЖНО: любые изменения этого списка синхронизировать с:
   *   - kip8-desktop/tests/test-role-access.js (const ROLES)
   *   - kip8-desktop/index.html (ROLE_ACCESS + LVL_* константы в _applyRoleToUI)
   * ============================================================
   */
  getAllowedRoles: function() {
    return [
      'Запрет',
      'Общий доступ',
      'ИТР ТОКЕМ',
      'КИП8',
      'КИП8 pro',
      'КИП ИОС',
      'КИП ИОС pro',
      'КИП ИОС дежурный',
      'ИТР8',
      'ИТР8 pro',
      'ИТР ИОС',
      'Админ'
    ];
  },

  // ========================================================================
  // CLEANUP (вызывается из hourlyCleanup через trigger)
  // ========================================================================

  /**
   * Очистка сессий (вызывается из hourlyCleanup через trigger).
   * ============================================================
   * ВАЖНО: сессии НЕ истекают по времени. Эта функция только удаляет
   * «осиротевшие» сессии — те, у которых пользователь удалён из users.
   * Логика getCurrentUser уже делает это лениво, но cron нужен для
   * сессий, к которым никто не обращается.
   * ============================================================
   */
  cleanupExpiredSessions: function() {
    const rows = this.getRows('sessions');
    // Идём с конца, чтобы не сбивать нумерацию строк при удалении
    for (let i = rows.length - 1; i >= 0; i--) {
      const s = rows[i];
      const user = this.findUserById(s.user_id);
      if (!user) {
        this.deleteRow('sessions', s.row);
        this.audit(s.email, 'SESSION_CLEANUP_ORPHAN', '', '',
          'User deleted from users table, session removed');
      }
    }
  },

  /** Удалить истёкшие OTP-коды (старше 1 часа). */
  cleanupExpiredOtpCodes: function() {
    const cutoff = new Date(Date.now() - 60 * 60 * 1000);
    const rows = this.getRows('otp_codes');
    for (let i = rows.length - 1; i >= 0; i--) {
      const o = rows[i];
      if (o.expires_at instanceof Date && o.expires_at.getTime() < cutoff.getTime()) {
        this.deleteRow('otp_codes', o.row);
      }
    }
  },

  /** Удалить старые записи audit_log (старше N дней). */
  cleanupOldAuditLogs: function() {
    const days = this.getConfig('AUDIT_LOG_RETENTION_DAYS', 90);
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const rows = this.getRows('audit_log');
    for (let i = rows.length - 1; i >= 0; i--) {
      const r = rows[i];
      if (r.timestamp instanceof Date && r.timestamp.getTime() < cutoff.getTime()) {
        this.deleteRow('audit_log', r.row);
      }
    }
  },

  /**
   * Task 347: удалить «заброшенные» сессии — строки листа sessions,
   * у которых last_heartbeat старше N дней (config: STALE_SESSION_DAYS,
   * по умолчанию 30). Вызывается из hourlyCleanup (Code.gs).
   *
   * Почему это НЕ «истечение по времени» (заявка: сессии бессрочные):
   * живое устройство бьёт heartbeat каждые 5 минут, поэтому last_heartbeat
   * активной сессии всегда свежий. Строка, молчавшая месяц, — это удалённое
   * приложение/очищенный браузер, а не живая сессия. Именно такие строки
   * копились месяцами (старый logout их не удалял) и не давали фиксу
   * Task 346 сбрасывать login_status последней сессии.
   *
   * Дополнительно: если у пользователя после чистки не осталось ни одной
   * строки — сбросить login_status в «вход не выполнен» (событие
   * LOGIN_STATUS_AUTO_RESET, как в самосинхронизации Auth.sendOTP).
   * Строки с пустым user_id (легаси Task 37) удаляются, но статус их
   * пользователя не трогаем — рассинхрон починит самосинхронизация при
   * следующем входе.
   *
   * Возвращает число удалённых строк (для логирования/отладки).
   */
  cleanupStaleSessions: function() {
    const days = this.getConfig('STALE_SESSION_DAYS', 30);
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    const rows = this.getRows('sessions');
    const affected = {}; // user_id -> true (у кого могли исчезнуть все сессии)
    let removed = 0;

    // Проход 1: удалить устаревшие строки (с конца — нумерация не сбивается)
    for (let i = rows.length - 1; i >= 0; i--) {
      const s = rows[i];
      const hb = (s.last_heartbeat instanceof Date) ? s.last_heartbeat.getTime() : 0;
      if (hb < cutoff) {
        this.deleteRow('sessions', s.row);
        if (s.user_id !== '' && s.user_id !== undefined && s.user_id !== null) {
          affected[s.user_id] = true;
        }
        this.audit(s.email, 'SESSION_CLEANUP_STALE', '', '',
          'last_heartbeat older than ' + days + ' days — session removed');
        removed++;
      }
    }

    // Проход 2: сбросить login_status тем, у кого сессий не осталось
    for (const uid in affected) {
      if (!this.userHasActiveSession(uid)) {
        const user = this.findUserById(uid);
        if (user && user.login_status === 'вход выполнен') {
          this.updateUserStatus(user.row, 'вход не выполнен', user.last_login);
          this.audit(user.email, 'LOGIN_STATUS_AUTO_RESET', '', '',
            'No sessions left after stale cleanup');
        }
      }
    }
    return removed;
  }
};

/**
 * Admin.gs — Админ-функции (требуют роль "Админ")
 * Встроен в Utils.gs для удобства (отдельный файл не обязателен).
 */
const Admin = {

  _requireAdmin: function(token) {
    if (!token) throw new Error('Unauthorized');
    const session = Utils.findSessionByToken(token);
    if (!session) throw new Error('Unauthorized');
    const user = Utils.findUserById(session.user_id);
    if (!user || user.role !== 'Админ') {
      Utils.audit(session.email, 'ADMIN_ACCESS_DENIED', '', '', 'Non-admin tried admin endpoint');
      throw new Error('Forbidden: admin role required');
    }
    return user;
  },

  listUsers: function(token) {
    this._requireAdmin(token);
    return Utils.getRows('users').map(u => ({
      id: u.ID, email: u.email, role: u.role,
      login_status: u.login_status, last_login: u.last_login
    }));
  },

  updateRole: function(token, userId, newRole) {
    const admin = this._requireAdmin(token);
    const user = Utils.findUserById(userId);
    if (!user) throw new Error('User not found');
    // Список ролей по карте ролей (Task 38, "Карта ролей.xlsx").
    // Источник истины — Utils.getAllowedRoles() — чтобы список был в одном месте.
    const allowed = Utils.getAllowedRoles();
    if (allowed.indexOf(newRole) === -1) throw new Error('Invalid role: ' + newRole);

    const sheet = Utils.getSheet('users');
    sheet.getRange(user.row, 3).setValue(newRole); // role = C
    Utils.audit(admin.email, 'ADMIN_UPDATE_ROLE', '', '',
      'User ' + user.email + ' role: ' + user.role + ' → ' + newRole);
    return { ok: true };
  },

  resetLogin: function(token, userId) {
    const admin = this._requireAdmin(token);
    const user = Utils.findUserById(userId);
    if (!user) throw new Error('User not found');

    Utils.updateUserStatus(user.row, 'вход не выполнен', user.last_login);

    // Удалить все активные сессии этого пользователя
    const sessions = Utils.getRows('sessions');
    for (let i = sessions.length - 1; i >= 0; i--) {
      if (Number(sessions[i].user_id) === Number(userId)) {
        Utils.deleteRow('sessions', sessions[i].row);
      }
    }

    Utils.audit(admin.email, 'ADMIN_RESET_LOGIN', '', '',
      'Reset login for ' + user.email);
    return { ok: true };
  },

  /**
   * Создать нового пользователя.
   * Логика:
   *   1. Валидация email (normalizeEmail)
   *   2. Проверка, что email уникальный (findUserByEmail)
   *   3. Проверка роли (allowed список)
   *   4. Сгенерировать новый ID = max(existing IDs) + 1
   *   5. Добавить строку: [ID, email, role, 'вход не выполнен', '']
   *   6. audit_log
   * Возвращает { ok: true, id: <newId>, email, role }.
   */
  createUser: function(token, rawEmail, newRole) {
    const admin = this._requireAdmin(token);

    const email = Utils.normalizeEmail(rawEmail);
    if (!email) throw new Error('Некорректный email');

    // Список ролей — единый источник истины Utils.getAllowedRoles().
    const allowed = Utils.getAllowedRoles();
    if (allowed.indexOf(newRole) === -1) {
      throw new Error('Недопустимая роль: ' + newRole);
    }

    // Проверка уникальности email.
    const existing = Utils.findUserByEmail(email);
    if (existing) {
      throw new Error('Пользователь с email ' + email + ' уже существует');
    }

    // Сгенерировать новый ID = max(existing IDs) + 1.
    const rows = Utils.getRows('users');
    let maxId = 0;
    for (let i = 0; i < rows.length; i++) {
      const id = Number(rows[i].ID);
      if (!isNaN(id) && id > maxId) maxId = id;
    }
    const newId = maxId + 1;

    // Добавить строку: ID | email | role | login_status | last_login
    // Структура листа users: A=ID, B=email, C=role, D=login_status, E=last_login.
    Utils.appendRow('users', [newId, email, newRole, 'вход не выполнен', '']);

    Utils.audit(admin.email, 'ADMIN_CREATE_USER', '', '',
      'Created user: ' + email + ' (role: ' + newRole + ', id: ' + newId + ')');

    return { ok: true, id: newId, email: email, role: newRole };
  },

  listSessions: function(token) {
    this._requireAdmin(token);
    return Utils.getRows('sessions').map(s => ({
      token: s.session_token ? s.session_token.substring(0, 8) + '…' : '', // не возвращаем полный токен
      user_id: s.user_id,
      email: s.email,
      role: s.role,
      created_at: s.created_at,
      last_heartbeat: s.last_heartbeat
    }));
  },

  listLogs: function(token, limit) {
    this._requireAdmin(token);
    limit = Math.min(limit || 100, 500);
    const rows = Utils.getRows('audit_log');
    // Сортировка по убыванию timestamp
    rows.sort((a, b) => {
      const ta = a.timestamp instanceof Date ? a.timestamp.getTime() : 0;
      const tb = b.timestamp instanceof Date ? b.timestamp.getTime() : 0;
      return tb - ta;
    });
    return rows.slice(0, limit).map(r => ({
      timestamp: r.timestamp,
      email: r.email,
      action: r.action,
      ip: r.ip,
      details: r.details
    }));
  }
};

/**
 * Настройка триггеров — ОДНОРАЗОВО вызвать вручную из редактора Apps Script.
 * Запустите функцию setupTriggers() один раз (Run → setupTriggers).
 * Она создаст hourly-триггер для cleanup.
 */
function setupTriggers() {
  // Удалить старые триггеры
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }
  // Создать hourly-триггер для cleanup
  ScriptApp.newTrigger('hourlyCleanup')
    .timeBased()
    .everyHours(1)
    .create();
  console.log('Triggers set up: hourlyCleanup every 1 hour');
}
