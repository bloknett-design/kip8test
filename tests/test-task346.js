// tests/test-task346.js
// Task 346 — политика сессий «1 моб + 1 десктоп» на одну почту.
// Заявка (2026-09-08): «у пользователей должна быть возможность с одной
// почты заходить и параллельно работать в двух приложениях, в мобильном
// и десктопном. Чтобы при входе, допустим, в мобильное приложение, затем
// он мог с этой же почтой войти в десктопное приложение и при этом не
// было запрета с формулировкой, что пользователь уже вошел. Но не
// больше двух входов с одной почты, и только один вход в мобильное
// приложение, а другой вход с этой же почты в десктопное приложение.»
//
// Диагноз до задачи: сервер создавал сессию на КАЖДЫЙ вход без
// ограничений (снапшот KIP8_Access 2026-09-08: 41 строка sessions, у
// одного email — 12) и НЕ различал тип устройства (колонки device нет).
//
// Реализация:
//   КЛИЕНТ: KipAuth._detectDeviceType() ('mobile' — мобильный UA,
//   'desktop' — Electron/ПК); verifyOTP шлёт payload.device; при
//   ответе evicted>0 — тост «Прежний вход в … приложении … завершён»;
//   админ-панель — бейдж «моб»/«десктоп» у сессий. Старый сервер поле
//   игнорирует — обратная совместимость.
//   СЕРВЕР (Apps Script, НЕ в репо — справочник): scripts/
//   SessionsDevicePolicy.gs + DEPLOY-Task346-sessions-device-policy.md:
//   колонка device листа sessions + вытеснение прежней сессии ТОГО ЖЕ
//   типа (инвариант ≤1 mobile + ≤1 desktop; вход в «другое» приложение
//   всегда разрешён, никаких «уже вошли»).
//
// SW: kipia-test-v582.
//
// Запуск: через tests/run-all.js (require './test-task346.js').

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

// ============================================================
// Извлечение модулей (KipAuth / KipAdmin) из index.html
// ============================================================
function extractObject(name) {
    const START = INDEX_SRC.indexOf('const ' + name + ' = {');
    if (START === -1) return '';
    const END = INDEX_SRC.indexOf('\n    };', START);
    return INDEX_SRC.slice(START, END + 6) + '\n' + name + ';';
}

const KIPAUTH_SRC = extractObject('KipAuth');
const KIPADMIN_SRC = extractObject('KipAdmin');

// Мок localStorage (как test-task344)
function mockStorage() {
    const store = {};
    return {
        store: store,
        getItem: function (k) {
            return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null;
        },
        setItem: function (k, v) { store[k] = String(v); },
        removeItem: function (k) { delete store[k]; }
    };
}

// Sandbox для KipAuth: window/navigator/localStorage/showToast + счётчик тостов
function authSandbox(ua, isElectron) {
    const toasts = [];
    const storage = mockStorage();
    const sandbox = {
        localStorage: storage,
        console: { log: function () {}, warn: function () {}, error: function () {} },
        showToast: function (msg) { toasts.push(String(msg)); },
        setTimeout: function () { return 0; },
        setInterval: function () { return 0; },
        clearInterval: function () {},
        navigator: { userAgent: ua || '' },
        document: {
            getElementById: function () {
                return { value: '', classList: { add: function () {}, remove: function () {} },
                         disabled: false, innerHTML: '', focus: function () {} };
            }
        }
    };
    sandbox.window = sandbox;
    if (isElectron) sandbox.__isElectron = true;
    sandbox.__toasts = toasts;
    sandbox.__storage = storage;
    return sandbox;
}

// ============================================================
// 1. _detectDeviceType — классификация устройства
// ============================================================
describe('Task 346 — KipAuth._detectDeviceType', () => {

    test('SRC: метод _detectDeviceType определён в KipAuth', () => {
        assertTrue(KIPAUTH_SRC.indexOf('_detectDeviceType: function') !== -1,
            'метод в модуле KipAuth');
    });

    test('VM: Electron-десктоп → desktop (флаг __isElectron)', () => {
        const sb = authSandbox('Mozilla/5.0 (Linux; Android 13) Mobile', true);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);
        assertEqual(KipAuth._detectDeviceType(), 'desktop',
            '__isElectron=true даже с мобильным UA (флаг приоритетнее)');
    });

    test('VM: Android UA → mobile', () => {
        const sb = authSandbox('Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36', false);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);
        assertEqual(KipAuth._detectDeviceType(), 'mobile', 'Android PWA/браузер');
    });

    test('VM: iPhone UA → mobile', () => {
        const sb = authSandbox('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1', false);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);
        assertEqual(KipAuth._detectDeviceType(), 'mobile', 'iOS PWA/браузер');
    });

    test('VM: iPad UA → mobile', () => {
        const sb = authSandbox('Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1', false);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);
        assertEqual(KipAuth._detectDeviceType(), 'mobile', 'iPad');
    });

    test('VM: десктопный Chrome (Windows) → desktop', () => {
        const sb = authSandbox('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36', false);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);
        assertEqual(KipAuth._detectDeviceType(), 'desktop', 'браузер на ПК');
    });

    test('VM: пустой navigator.userAgent → desktop (fail-safe)', () => {
        const sb = authSandbox('', false);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);
        assertEqual(KipAuth._detectDeviceType(), 'desktop', 'нет UA — десктоп по умолчанию');
    });
});

// ============================================================
// 2. verifyOTP — device в payload + тост evicted
// ============================================================
describe('Task 346 — verifyOTP: device в payload, тост evicted', () => {

    test('SRC: payload verifyOTP содержит device: deviceType', () => {
        const i = KIPAUTH_SRC.indexOf("api('verifyOTP'");
        assertTrue(i !== -1, 'вызов api verifyOTP найден');
        const around = KIPAUTH_SRC.slice(i - 200, i + 200);
        assertTrue(around.indexOf('device: deviceType') !== -1,
            'поле device в payload');
        assertTrue(around.indexOf('this._detectDeviceType()') !== -1,
            'тип берётся из _detectDeviceType()');
    });

    test('SRC: ответ с evicted → тост о закрытии прежнего входа', () => {
        const i = KIPAUTH_SRC.indexOf('data.evicted');
        assertTrue(i !== -1, 'обработка evicted есть');
        const around = KIPAUTH_SRC.slice(i - 100, i + 500);
        assertTrue(around.indexOf('showToast') !== -1, 'тост показывается');
        assertTrue(around.indexOf('мобильном') !== -1
            && around.indexOf('десктопном') !== -1,
            'формулировка зависит от типа устройства');
        assertTrue(around.indexOf("deviceType === 'mobile'") !== -1,
            'тип вытесненной сессии — текущий deviceType');
    });

    test('VM: мобильный UA — api получает device=mobile; evicted=1 → тост; токен сохранён', () => {
        const sb = authSandbox('Mozilla/5.0 (Linux; Android 13) Mobile', false);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);

        // Мок api: запоминаем payload, возвращаем успех с evicted
        let captured = null;
        KipAuth.api = function (action, payload) {
            captured = { action: action, payload: payload };
            return Promise.resolve({ token: 't346-mob', role: 'Админ',
                userId: 3, email: 'user@test.local', evicted: 1 });
        };
        // Заглушки методов флоу входа (после успешного verify)
        let hidden = 0, beats = 0;
        KipAuth._hideLoginScreen = function () { hidden++; };
        KipAuth._startHeartbeat = function () { beats++; };
        KipAuth._updateSidebarUserInfo = function () {};
        KipAuth._applyRoleToUI = function () {};
        KipAuth._fetchMyAccess = function () {};

        KipAuth._pendingEmail = 'user@test.local';
        // OTP-поля: DOM-мок возвращает value='1' для otp1..otp6
        // (код 111111).
        sb.document.getElementById = function (id) {
            if (/^otp[1-6]$/.test(id)) {
                return { value: '1', classList: { add: function () {}, remove: function () {} },
                         disabled: false, innerHTML: '', focus: function () {} };
            }
            return { value: '', classList: { add: function () {}, remove: function () {} },
                     disabled: false, innerHTML: '', focus: function () {} };
        };

        // verifyOTP() не возвращает промис (цепочка .then внутри без
        // return — штатный код): вызываем и ждём ЦЕПЬ МИКРОТАСКОВ
        // (макротаймеры трогать нельзя — в очереди Node остаются
        // таймеры других VM-тестов с неполными DOM-моками).
        KipAuth.verifyOTP();
        var _ticks = 0;
        function _tick() {
            _ticks++;
            return _ticks < 8 ? Promise.resolve().then(_tick) : Promise.resolve();
        }
        return _tick().then(function () {
            assertEqual(captured && captured.action, 'verifyOTP', 'action');
            assertEqual(captured && captured.payload.device, 'mobile',
                'payload.device = mobile (мобильный UA)');
            assertEqual(captured.payload.email, 'user@test.local', 'email в payload');
            assertEqual(captured.payload.code, '111111', 'код из OTP-полей');
            assertEqual(sb.__storage.store['kip8_session_token'], 't346-mob',
                'токен сохранён');
            assertEqual(hidden, 1, 'экран входа скрыт');
            assertEqual(beats, 1, 'heartbeat запущен');
            assertEqual(sb.__toasts.length, 1, 'показан 1 тост (evicted=1)');
            assertTrue(sb.__toasts[0].indexOf('мобильном') !== -1,
                'тост про мобильное приложение');
            assertTrue(sb.__toasts[0].indexOf('завершён') !== -1,
                'формулировка о завершении прежнего входа');
            });
    });

    test('VM: десктопный UA — device=desktop; СТАРЫЙ сервер без evicted → тоста нет', () => {
        const sb = authSandbox('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126', false);
        const KipAuth = vm.runInNewContext(KIPAUTH_SRC, sb);

        let captured = null;
        KipAuth.api = function (action, payload) {
            captured = { action: action, payload: payload };
            // Старый сервер: поле evicted НЕ возвращает
            return Promise.resolve({ token: 't346-desk', role: 'Админ',
                userId: 3, email: 'user@test.local' });
        };
        KipAuth._hideLoginScreen = function () {};
        KipAuth._startHeartbeat = function () {};
        KipAuth._updateSidebarUserInfo = function () {};
        KipAuth._applyRoleToUI = function () {};
        KipAuth._fetchMyAccess = function () {};

        KipAuth._pendingEmail = 'user@test.local';
        sb.document.getElementById = function (id) {
            if (/^otp[1-6]$/.test(id)) {
                return { value: '2', classList: { add: function () {}, remove: function () {} },
                         disabled: false, innerHTML: '', focus: function () {} };
            }
            return { value: '', classList: { add: function () {}, remove: function () {} },
                     disabled: false, innerHTML: '', focus: function () {} };
        };

        // См. предыдущий тест: verifyOTP не возвращает промис; ждём
        // микротасками, без макротаймеров.
        KipAuth.verifyOTP();
        var _ticks2 = 0;
        function _tick2() {
            _ticks2++;
            return _ticks2 < 8 ? Promise.resolve().then(_tick2) : Promise.resolve();
        }
        return _tick2().then(function () {
            assertEqual(captured.payload.device, 'desktop',
                'payload.device = desktop (UA ПК)');
            assertEqual(sb.__toasts.length, 0,
                'тоста НЕТ — обратная совместимость со старым сервером');
            assertEqual(sb.__storage.store['kip8_session_token'], 't346-desk',
                'вход выполнен, токен сохранён');
            });
    });
});

// ============================================================
// 3. Админ-панель — бейдж устройства у сессий
// ============================================================
describe('Task 346 — админ-панель: бейдж «моб»/«десктоп»', () => {

    test('SRC: CSS-класс admin-badge-device (тёмная + светлая темы)', () => {
        assertTrue(INDEX_SRC.indexOf('.admin-badge-device {') !== -1,
            'тёмная тема');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .admin-badge-device') !== -1,
            'светлая тема');
    });

    test('SRC: renderSessions рендерит бейдж по s.device', () => {
        const i = KIPADMIN_SRC.indexOf('admin-badge-device');
        assertTrue(i !== -1, 'бейдж в renderSessions');
        const around = KIPADMIN_SRC.slice(i - 300, i + 300);
        assertTrue(around.indexOf("s.device === 'mobile'") !== -1
            && around.indexOf("s.device === 'desktop'") !== -1,
            'бейдж только для mobile/desktop');
        assertTrue(around.indexOf('моб') !== -1 && around.indexOf('десктоп') !== -1,
            'подписи бейджей');
    });

    test('VM: renderSessions — бейджи по device, у легаси-сессий нет', () => {
        const sb = authSandbox('', false);
        const KipAdmin = vm.runInNewContext(KIPADMIN_SRC, sb);

        KipAdmin._sessions = [
            { email: 'a@x.ru', role: 'Админ', token: 'tokA',
              created_at: '2026-09-08 10:00:00', last_heartbeat: '2026-09-08 11:00:00',
              device: 'mobile' },
            { email: 'b@x.ru', role: 'КИП ИОС', token: 'tokB',
              created_at: '2026-09-08 10:00:00', last_heartbeat: '2026-09-08 11:00:00',
              device: 'desktop' },
            { email: 'c@x.ru', role: 'КИП ИОС', token: 'tokC',
              created_at: '2026-09-08 10:00:00', last_heartbeat: '2026-09-08 11:00:00' },
            { email: 'd@x.ru', role: 'КИП ИОС', token: 'tokD',
              created_at: '2026-09-08 10:00:00', last_heartbeat: '2026-09-08 11:00:00',
              device: 'телефон' }
        ];
        let html = '';
        sb.document.getElementById = function (id) {
            if (id === 'adminSessionsList') {
                return { set innerHTML(v) { html = v; }, get innerHTML() { return html; } };
            }
            if (id === 'adminSessionSearch') return { value: '' };
            return { value: '' };
        };

        KipAdmin.renderSessions();

        const items = html.split('admin-item-email').length - 1;
        assertEqual(items, 4, 'все 4 сессии отрендерены');
        assertEqual(html.split('admin-badge-device').length - 1, 2,
            'ровно 2 бейджа устройства (mobile + desktop)');
        assertTrue(/>\s*моб\s*</.test(html.replace('admin-badge-device', '')),
            'бейдж «моб» у mobile-сессии');
        assertTrue(/>\s*десктоп\s*</.test(html.replace('admin-badge-device', '')),
            'бейдж «десктоп» у desktop-сессии');
        // легаси-сессии (без device / мусорное значение) — без бейджа
        const rows = html.split('<div class="admin-item">').slice(1);
        assertEqual((rows[2].indexOf('admin-badge-device') === -1), true,
            'сессия без device — без бейджа');
        assertEqual((rows[3].indexOf('admin-badge-device') === -1), true,
            'мусорный device («телефон») — без бейджа');
    });
});

// ============================================================
// 4. Серверный справочник (Apps Script, в репо — референс)
// ============================================================
describe('Task 346 — серверный справочник SessionsDevicePolicy.gs', () => {

    test('ФАЙЛ: scripts/SessionsDevicePolicy.gs существует', () => {
        assertTrue(fs.existsSync(path.join(ROOT, 'scripts', 'SessionsDevicePolicy.gs')),
            'справочник в репо');
    });

    test('ФАЙЛ: DEPLOY-инструкция существует', () => {
        assertTrue(fs.existsSync(path.join(ROOT, 'scripts', 'DEPLOY-Task346-sessions-device-policy.md')),
            'DEPLOY-Task346-sessions-device-policy.md');
    });

    test('ФАЙЛ: патченный Auth.gs существует (справочник живого сервера)', () => {
        assertTrue(fs.existsSync(path.join(ROOT, 'scripts', 'Auth.gs')),
            'scripts/Auth.gs — патч Task 346 для живого Auth.gs');
    });

    test('AUTH: блокировки «уже выполнен вход» удалены (заявка: без запретов)', () => {
        const auth = fs.readFileSync(path.join(ROOT, 'scripts', 'Auth.gs'), 'utf8');
        assertTrue(auth.indexOf('LOGIN_BLOCKED_DUPLICATE') === -1,
            'audit-событие блокировки убрано из Auth.gs');
        assertTrue(auth.indexOf("throw new Error('С этого аккаунта") === -1,
            'throw «С этого аккаунта уже выполнен вход…» убран (в комментариях упоминание допустимо)');
    });

    test('AUTH: verifyOTP принимает payload; политика с guard; evicted в ответе', () => {
        const auth = fs.readFileSync(path.join(ROOT, 'scripts', 'Auth.gs'), 'utf8');
        assertTrue(auth.indexOf('verifyOTP: function(rawEmail, code, payload)') !== -1,
            'сигнатура с 3-м аргументом payload');
        assertTrue(auth.indexOf("typeof sdpApplyDevicePolicy === 'function'") !== -1,
            'guard: без SessionsDevicePolicy.gs вход не падает');
        assertTrue(auth.indexOf('sdpApplyDevicePolicy(email, t346device, session.token)') !== -1,
            'вызов политики после создания сессии');
        assertTrue(auth.indexOf('evicted: t346evicted') !== -1,
            'evicted в ответе для тоста');
    });

    test('AUTH: самосинхронизация login_status сохранена (без throw)', () => {
        const auth = fs.readFileSync(path.join(ROOT, 'scripts', 'Auth.gs'), 'utf8');
        assertTrue(auth.indexOf('LOGIN_STATUS_AUTO_RESET') !== -1,
            'авто-сброс устаревшего login_status остался');
        assertTrue(auth.indexOf('&& !Utils.userHasActiveSession') !== -1,
            'сброс только при отсутствии активных сессий');
    });

    test('DEPLOY: правка роутера Code.gs (payload 3-м аргументом)', () => {
        const md = fs.readFileSync(path.join(ROOT, 'scripts', 'DEPLOY-Task346-sessions-device-policy.md'), 'utf8');
        assertTrue(md.indexOf('Auth.verifyOTP(payload.email, payload.code, payload)') !== -1,
            'инструкция учитывает передачу payload в роутере');
        assertTrue(md.indexOf('LOGIN_BLOCKED_DUPLICATE') !== -1,
            'инструкция описывает удаление блокировки «уже вошел»');
    });

    test('CODE.GS: справочник роутера содержит правку Task 346 (payload)', () => {
        const code = fs.readFileSync(path.join(ROOT, 'scripts', 'Code.gs'), 'utf8');
        assertTrue(code.indexOf('Auth.verifyOTP(payload.email, payload.code, payload)') !== -1,
            'справочник Code.gs передаёт payload в Auth.verifyOTP (иначе политика неактивна)');
        assertTrue(code.indexOf('Auth.verifyOTP(payload.email, payload.code);') === -1,
            'старая строка без payload не осталась');
    });

    test('ФАЙЛ: политика — fail-open, вытеснение того же device, инвариант', () => {
        const gs = fs.readFileSync(path.join(ROOT, 'scripts', 'SessionsDevicePolicy.gs'), 'utf8');
        assertTrue(gs.indexOf('function sdpApplyDevicePolicy') !== -1,
            'функция политики');
        assertTrue(gs.indexOf('FAIL-OPEN') !== -1,
            'ошибка политики не блокирует вход');
        assertTrue(gs.indexOf('rowsToEvict') !== -1, 'вытеснение старых сессий');
        assertTrue(gs.indexOf("SDP_DEVICES = { 'mobile': true, 'desktop': true }") !== -1,
            'только mobile/desktop; старые клиенты пропускаются');
        assertTrue(gs.indexOf('deleteRow') !== -1, 'удаление вытесненных строк');
        assertTrue(gs.indexOf('unsupported_device') !== -1,
            'payload без device → политика пропущена (легаси)');
    });
});

// ============================================================
// 5. SW — бамп инвалидации кэша
// ============================================================
describe('Task 346 — SW-бамп', () => {

    test("SW: CACHE_VERSION = 'kipia-test-v582'", () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v582'") !== -1,
            'v582 установлен');
        assertFalse(SW_SRC.indexOf('kipia-test-v583') !== -1,
            'v581 не остался (двойной бамп?)');
    });
});
