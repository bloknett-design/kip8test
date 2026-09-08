/**
 * Auth.gs — Логика OTP (генерация, отправка, верификация)
 * ============================================================
 * Task 346 (2026-09-08), патч для параллельных сессий «1 моб + 1 десктоп»:
 *   • УДАЛЕНЫ обе блокировки «С этого аккаунта уже выполнен вход…»
 *     (были в sendOTP и verifyOTP) — по заявке пользователь с одной почты
 *     может ПАРАЛЛЕЛЬНО работать в мобильном И десктопном приложениях.
 *   • Лимит «не больше двух входов, по одному на тип приложения» теперь
 *     обеспечивает SessionsDevicePolicy.gs (≤1 mobile + ≤1 desktop,
 *     вытеснение сессии ТОГО ЖЕ типа при повторном входе).
 *   • verifyOTP принимает 3-й аргумент payload (поле device от клиента)
 *     и возвращает evicted — число вытесненных сессий (для тоста).
 *   • Роутер Code.gs должен вызывать:
 *       Auth.verifyOTP(payload.email, payload.code, payload)
 *   Полный порядок активации — DEPLOY-Task346-sessions-device-policy.md.
 */

const Auth = {

  /**
   * Запросить OTP-код на email.
   * Шаги:
   *   1. Нормализовать email
   *   2. Найти пользователя в users
   *   3. Самосинхронизация login_status (Task 346: отказа «уже вошли» НЕТ)
   *   4. Проверить cooldown (не чаще 60 сек)
   *   5. Проверить rate limit (глобально и per-IP)
   *   6. Сгенерировать 6-значный код
   *   7. Записать в otp_codes
   *   8. Отправить письмо через MailApp
   *   9. Записать audit_log
   *
   * ВАЖНО: для несуществующих email возвращаем «код отправлен»,
   * но фактически не отправляем — защита от перебора email.
   */
  sendOTP: function(rawEmail) {
    const email = Utils.normalizeEmail(rawEmail);
    if (!email) {
      throw new Error('Некорректный email');
    }

    const ip = Utils.getClientIp();
    const ua = Utils.getClientUserAgent();

    // Rate limit: глобально 100 OTP/час
    const globalCount = Utils.countRecentAuditLogs('OTP_REQUESTED', 60);
    if (globalCount >= Utils.getConfig('RATE_LIMIT_OTP_PER_HOUR', 100)) {
      Utils.audit(email, 'RATE_LIMIT_HIT', ip, ua, 'Global OTP rate limit');
      throw new Error('Слишком много запросов, попробуйте позже');
    }

    // Rate limit: per-IP 20 неудач/час
    const ipFails = Utils.countRecentAuditLogsByIp('OTP_FAILED', ip, 60);
    if (ipFails >= Utils.getConfig('RATE_LIMIT_FAILED_PER_IP', 20)) {
      Utils.audit(email, 'RATE_LIMIT_HIT', ip, ua, 'Per-IP rate limit: ' + ip);
      throw new Error('Слишком много попыток с вашего IP');
    }

    // Найти пользователя
    let user = Utils.findUserByEmail(email);

    // Защита от перебора: для несуществующего email возвращаем успех,
    // но не отправляем письмо. Логируем как OTP_REQUESTED_NOT_FOUND.
    if (!user) {
      Utils.audit(email, 'OTP_REQUESTED_NOT_FOUND', ip, ua, 'Email not in users sheet');
      return { sent: true, message: 'Код отправлен на ' + email };
    }

    // Task 346: БЛОКИРОВКА «уже выполнен вход» УДАЛЕНА (заявка: с одной
    // почты — параллельная работа в мобильном И десктопном приложении;
    // запрета с формулировкой «пользователь уже вошел» быть не должно).
    // Лимит входов (не больше двух, по одному на тип приложения) применяет
    // SessionsDevicePolicy.gs в verifyOTP при создании сессии.
    //
    // Оставлена только САМОСИНХРОНИЗАЦИЯ login_status: статус может
    // рассинхронизироваться с реальным состоянием sessions:
    //   1. Hourly cleanup удалил сессию, но не сбросил login_status.
    //   2. Сессия истекла по TTL и удалена через getCurrentUser, но сброс
    //      login_status не сработал.
    //   3. Токен в браузере не находится в sessions (удалён админом или
    //      ручная правка таблицы).
    //   4. Cleanup ещё не запускался (он раз в час), а сессия уже не активна.
    // Если активных (не истёкших по TTL) сессий нет — сбросить login_status
    // и продолжить вход. Если есть — НЕ блокируем: это параллельный вход в
    // другое приложение, политику применит verifyOTP.
    if (user.login_status === 'вход выполнен'
        && !Utils.userHasActiveSession(user.ID)) {
      Utils.updateUserStatus(user.row, 'вход не выполнен', user.last_login);
      Utils.audit(email, 'LOGIN_STATUS_AUTO_RESET', ip, ua,
        'login_status was "вход выполнен" but no active session found — auto-reset');
      // Перечитать пользователя, чтобы дальше работать со свежим состоянием.
      user = Utils.findUserByEmail(email);
    }

    // Проверить блокировку OTP (после MAX_OTP_ATTEMPTS неудач)
    const recentFails = Utils.countRecentOtpFails(email, Utils.getConfig('OTP_BLOCK_MINUTES', 30));
    const maxAttempts = Utils.getConfig('MAX_OTP_ATTEMPTS', 5);
    if (recentFails >= maxAttempts) {
      Utils.audit(email, 'OTP_BLOCKED', ip, ua, 'Too many failed attempts: ' + recentFails);
      throw new Error('Слишком много неудачных попыток. Попробуйте через ' + Utils.getConfig('OTP_BLOCK_MINUTES', 30) + ' минут');
    }

    // Cooldown: не чаще 60 сек
    const cooldown = Utils.getConfig('OTP_RESEND_COOLDOWN_SECONDS', 60);
    const lastOtp = Utils.getLastOtpForEmail(email);
    if (lastOtp && (Date.now() - lastOtp.created_at.getTime()) / 1000 < cooldown) {
      const waitSec = Math.ceil(cooldown - (Date.now() - lastOtp.created_at.getTime()) / 1000);
      throw new Error('Подождите ' + waitSec + ' сек перед повторным запросом кода');
    }

    // Сгенерировать код
    const codeLength = Utils.getConfig('OTP_CODE_LENGTH', 6);
    const code = Utils.generateNumericCode(codeLength);
    const now = new Date();
    const ttlMin = Utils.getConfig('OTP_TTL_MINUTES', 10);
    const expires = new Date(now.getTime() + ttlMin * 60 * 1000);

    // Записать в otp_codes
    Utils.appendRow('otp_codes', [email, code, now, expires, 'FALSE', 0]);

    // Отправить письмо.
    // ВАЖНО: Mail.ru (bk.ru, mail.ru, inbox.ru, list.ru) и Яндекс.Почта
    // агрессивно фильтруют письма от Apps Script. Чтобы повысить
    // доставляемость:
    //   • HTML body с inline-стилями (почтовики считают легитимным)
    //   • Карточка с крупным кодом (не «голое число» — снижает spam score)
    //   • НЕ используем noReply:true (noreply-отправители понижаются)
    //   • replyTo с реальным адресом поддержки (из config или владелец скрипта)
    //   • Развёрнутый текст (контекст + время + что делать если не запрашивали)
    const subject = 'Код доступа к КИПиА: ' + code;
    const requestTime = Utilities.formatDate(now, Session.getScriptTimeZone(), 'dd.MM.yyyy HH:mm:ss z');
    const supportEmail = Utils.getConfig('SUPPORT_REPLY_TO', '') || '';

    // Plain-text fallback (для почтовиков без HTML, и для превью).
    const textBody = [
      'КИПиА — система доступа',
      '',
      'Ваш одноразовый код: ' + code,
      '',
      'Код действителен ' + ttlMin + ' минут.',
      'Запрошен: ' + requestTime + '.',
      '',
      'Если вы не запрашивали этот код — просто проигнорируйте письмо.',
      'Никому не сообщайте этот код, даже если представляются поддержкой.',
      '',
      '— Система доступа КИПиА'
    ].join('\n');

    // HTML body с карточкой.
    const htmlBody = ''
      + '<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">'
      + '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
      + '</head><body style="margin:0;padding:0;background:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,\'Helvetica Neue\',Arial,sans-serif;color:#1a2233;">'
      + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;padding:24px 12px;">'
      + '<tr><td align="center">'
      + '<table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);overflow:hidden;">'
      // Шапка
      + '<tr><td style="background:#1a2233;padding:20px 28px;">'
      + '<div style="font-size:16px;font-weight:700;color:#ffffff;letter-spacing:0.3px;">КИПиА — система доступа</div>'
      + '<div style="font-size:12px;color:rgba(255,255,255,0.6);margin-top:4px;">Одноразовый код для входа</div>'
      + '</td></tr>'
      // Тело
      + '<tr><td style="padding:28px;">'
      + '<p style="margin:0 0 16px;font-size:14px;line-height:1.5;color:#3a4a5e;">Здравствуйте! Вы запросили код для входа в приложение «КИПиА». Используйте указанный ниже код в форме ввода:</p>'
      // Карточка с кодом
      + '<div style="background:#f0f4f8;border:1px dashed #4a8fc7;border-radius:10px;padding:20px 16px;text-align:center;margin:0 0 20px;">'
      + '<div style="font-size:11px;color:#7a8a9e;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Ваш код</div>'
      + '<div style="font-size:34px;font-weight:700;color:#1a2233;letter-spacing:6px;font-family:\'Courier New\',monospace;">' + code + '</div>'
      + '<div style="font-size:12px;color:#7a8a9e;margin-top:10px;">Действителен ' + ttlMin + ' минут</div>'
      + '</div>'
      // Детали запроса
      + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:12px;color:#5a6a7e;margin-bottom:20px;">'
      + '<tr><td style="padding:3px 0;color:#9aa8b8;">Запрошен:</td><td style="padding:3px 0;text-align:right;color:#3a4a5e;font-weight:500;">' + requestTime + '</td></tr>'
      + '<tr><td style="padding:3px 0;color:#9aa8b8;">Для email:</td><td style="padding:3px 0;text-align:right;color:#3a4a5e;font-weight:500;">' + email + '</td></tr>'
      + '</table>'
      // Предупреждение
      + '<p style="margin:0 0 8px;font-size:13px;line-height:1.5;color:#5a6a7e;border-left:3px solid #c7964a;padding-left:12px;">Если вы не запрашивали этот код — просто проигнорируйте письмо. <strong style="color:#1a2233;">Никому не сообщайте этот код</strong>, даже если представляются поддержкой.</p>'
      + '</td></tr>'
      // Подвал
      + '<tr><td style="background:#fafbfc;border-top:1px solid #e8ebf0;padding:16px 28px;">'
      + '<div style="font-size:11px;color:#9aa8b8;line-height:1.5;">Это автоматическое письмо от системы доступа КИПиА. Не отвечайте на него напрямую.'
      + (supportEmail ? ' По вопросам обращайтесь: <a href="mailto:' + supportEmail + '" style="color:#4a8fc7;">' + supportEmail + '</a>.' : '')
      + '</div>'
      + '</td></tr>'
      + '</table>'
      + '</td></tr></table>'
      + '</body></html>';

    const mailOptions = {
      name: 'КИПиА — система доступа',
      htmlBody: htmlBody,
      // noReply убран намеренно: noreply-отправители понижаются в спам-фильтрах Mail.ru/Яндекса.
    };
    if (supportEmail) {
      mailOptions.replyTo = supportEmail;
    }

    try {
      MailApp.sendEmail(email, subject, textBody, mailOptions);
    } catch (e) {
      console.error('MailApp.sendEmail failed:', e);
      Utils.audit(email, 'OTP_SEND_FAILED', ip, ua, e.message);
      throw new Error('Не удалось отправить письмо. Попробуйте позже.');
    }

    Utils.audit(email, 'OTP_REQUESTED', ip, ua, 'OTP code sent');

    return { sent: true, message: 'Код отправлен на ' + email };
  },

  /**
   * Верифицировать OTP-код и создать сессию.
   * Возвращает: { token, role, userId, email, evicted }
   *
   * Task 346: 3-й аргумент payload — объект запроса (клиент шлёт поле
   * device: 'mobile' | 'desktop'; старые клиенты без поля — политика
   * пропускается). evicted > 0 — вытеснена прежняя сессия ТОГО ЖЕ типа
   * устройства (клиент показывает тост «Прежний вход в … приложении
   * завершён»). Роутер Code.gs: Auth.verifyOTP(payload.email, payload.code, payload).
   */
  verifyOTP: function(rawEmail, code, payload) {
    const email = Utils.normalizeEmail(rawEmail);
    if (!email) {
      throw new Error('Некорректный email');
    }
    if (!code || !/^\d{4,8}$/.test(String(code))) {
      throw new Error('Некорректный код');
    }

    const ip = Utils.getClientIp();
    const ua = Utils.getClientUserAgent();
    const user = Utils.findUserByEmail(email);

    if (!user) {
      Utils.audit(email, 'OTP_FAILED', ip, ua, 'User not found');
      throw new Error('Неверный код');
    }

    // Найти активный OTP для этого email
    const otp = Utils.getActiveOtpForEmail(email);
    if (!otp) {
      Utils.audit(email, 'OTP_FAILED', ip, ua, 'No active OTP');
      throw new Error('Код не найден или истёк. Запросите новый.');
    }

    // Проверить истечение
    if (otp.expires_at.getTime() < Date.now()) {
      Utils.markOtpUsed(otp.row);
      Utils.audit(email, 'OTP_FAILED', ip, ua, 'Code expired');
      throw new Error('Код истёк. Запросите новый.');
    }

    // Проверить код
    if (String(otp.code) !== String(code)) {
      Utils.incrementOtpAttempts(otp.row);
      const attempts = otp.attempts + 1;
      const max = Utils.getConfig('MAX_OTP_ATTEMPTS', 5);
      Utils.audit(email, 'OTP_FAILED', ip, ua, 'Wrong code, attempt ' + attempts + '/' + max);
      if (attempts >= max) {
        throw new Error('Неверный код. Превышен лимит попыток. Попробуйте через ' + Utils.getConfig('OTP_BLOCK_MINUTES', 30) + ' минут');
      }
      throw new Error('Неверный код. Осталось попыток: ' + (max - attempts));
    }

    // Код верный — пометить как использованный
    Utils.markOtpUsed(otp.row);

    // Ещё раз перечитать пользователя (между запросом и верификацией мог
    // войти другой). Task 346: блокировка «уже выполнен вход» УДАЛЕНА —
    // параллельный вход (моб + десктоп) разрешён; осталась только
    // самосинхронизация login_status при отсутствии активных сессий.
    let freshUser = Utils.findUserByEmail(email);
    if (freshUser.login_status === 'вход выполнен'
        && !Utils.userHasActiveSession(freshUser.ID)) {
      Utils.updateUserStatus(freshUser.row, 'вход не выполнен', freshUser.last_login);
      Utils.audit(email, 'LOGIN_STATUS_AUTO_RESET', ip, ua,
        'login_status was "вход выполнен" but no active session — auto-reset (during verify)');
      freshUser = Utils.findUserByEmail(email);
    }

    // Проверить, что роль не «Запрет»
    if (freshUser.role === 'Запрет') {
      Utils.audit(email, 'LOGIN_BLOCKED_ROLE', ip, ua, 'Role: Запрет');
      throw new Error('Доступ запрещён. Обратитесь к администратору.');
    }

    // Создать сессию
    const session = Sessions.createSession(freshUser);

    // Task 346: политика «1 моб + 1 десктоп» (SessionsDevicePolicy.gs):
    // записать device в строку новой сессии и вытеснить (удалить) все
    // ДРУГИЕ сессии этой почты с ТЕМ ЖЕ типом устройства. Инвариант:
    // ≤1 mobile + ≤1 desktop = не больше двух входов; вход в «другое»
    // приложение всегда разрешён. FAIL-OPEN: ошибки политики не блокируют
    // вход; старые клиенты без device — политика пропускается.
    const t346device = (payload && payload.device) ? String(payload.device).toLowerCase() : '';
    let t346evicted = 0;
    if (typeof sdpApplyDevicePolicy === 'function') {
      const t346policy = sdpApplyDevicePolicy(email, t346device, session.token);
      if (t346policy && t346policy.evicted) {
        t346evicted = t346policy.evicted;
      }
    } else {
      // SessionsDevicePolicy.gs ещё не добавлен в проект (Шаг 1 DEPLOY) —
      // вход работает как раньше, без лимитов.
      console.warn('Task 346: sdpApplyDevicePolicy не найдена — SessionsDevicePolicy.gs не подключён?');
    }

    // Обновить users: login_status + last_login
    Utils.updateUserStatus(freshUser.row, 'вход выполнен', new Date());

    Utils.audit(email, 'OTP_VERIFIED', ip, ua, 'Role: ' + freshUser.role);
    Utils.audit(email, 'LOGIN_SUCCESS', ip, ua,
        'Session created' + (t346device ? ', device: ' + t346device : '')
        + (t346evicted ? ', evicted: ' + t346evicted : ''));

    // ВАЖНО (Task 37): используем freshUser.ID (ЗАГЛАВНЫЕ), а НЕ freshUser.id.
    // Заголовок в листе users — "ID", поэтому Utils.getRows() возвращает obj.ID.
    // Если написать freshUser.id — будет undefined, клиент сохранит userId=''
    // в localStorage, а сессия в БД уже корректна (см. Sessions.createSession).
    return {
      token: session.token,
      role: freshUser.role,
      userId: freshUser.ID,
      email: email,
      // Task 346: >0 — прежний вход ТОГО ЖЕ типа устройства вытеснен
      // (клиент показывает тост; старым клиентам поле безвредно).
      evicted: t346evicted
    };
  }
};
