/**
 * @module auth
 * KipAuth — Email+OTP авторизация через Apps Script
 */

const KipAuth = {
    // URL Apps Script Web App.
    WEB_APP_URL: 'https://script.google.com/macros/s/AKfycbztmOJb_QVnjRk1GnvKe4X1TWcDgPSFVvGJiumm3y5RaGwgEiJX15PBiJVUX9mKJiWHzA/exec',

    // Ключ localStorage для session token.
    TOKEN_KEY: 'kip8_session_token',

    // Интервал heartbeat (5 минут = 300000 мс).
    HEARTBEAT_INTERVAL: 5 * 60 * 1000,

    // Кэш: роль текущего пользователя (обновляется через getCurrentUser).
    _cachedRole: null,
    _cachedEmail: null,
    _cachedUserId: null,
    _lastRoleFetch: 0,
    ROLE_CACHE_TTL: 30 * 1000, // 30 секунд

    // Состояние процесса входа.
    _pendingEmail: null,
    _resendCooldown: 0,
    _resendTimer: null,
    _heartbeatTimer: null,
    _initializing: false,

    // ============================================================
    // Карта доступа: роль → список разрешённых страниц.
    // (Подробная карта — см. ниже, после «Карта доступа на основе…».)
    // ============================================================

    // ============================================================
    // Карта доступа (на основе "Карта ролей.xlsx" от пользователя).
    // ============================================================
    // Структура (всё хранится как массивы page-id):
    //   _BASE_PAGES       — главная страница (доступна всем, включая гостей).
    //   _CALC_PAGES       — инженерные калькуляторы.
    //   _LIBRARY_PAGES    — библиотека: «Экзаменационные билеты» + «Библиотека КИП и А».
    //   _KIP_IOS_PAGES    — раздел КИП ИОС (включая кабельный журнал для просмотра).
    //   _FLOWMETER_PAGES  — расходомеры хозрасчётные (просмотр).
    //   _CHARTS_PAGES     — графики КИП ИОС (только Админ).
    //   _SECRET_PAGES     — секретные кнопки (сапёр + телефонный справочник).
    //   _WHATS_NEW_PAGES  — раздел «Что нового».
    //
    // Право ЗАПИСИ в кабельный журнал (добавление, правка, удаление кабелей)
    // определяется ОТДЕЛЬНО столбцом «Добавить, править, удалить кабели»
    // в «Карта ролей.xlsx» и управляется серверным флагом canEdit
    // (см. раздел «Кабельный журнал — canEdit» ниже).
    //
    // Право ВВОДА ПОКАЗАНИЙ в расходомеры хозрасчётные
    // определяется ОТДЕЛЬНО столбцом «Ввод показаний в расходомеры хозрасчётные»
    // в «Карта ролей.xlsx» и управляется клиентским флагом _canInputReadings
    // (роли: КИП ИОС дежурный, Админ).
    //
    // Карта ролей (из Excel, актуальная 2026-08-15):
    //   Запрет           — нет доступа (только dashboard).
    //   Общий доступ     — только калькуляторы. НЕ требует входа — гостевой режим.
    //   КИП8             — калькуляторы + библиотека + секретные кнопки + Что нового.
    //   КИП8 pro         — то же, что КИП8.
    //   КИП ИОС          — калькуляторы + библиотека + КИП ИОС + секретные + Что нового.
    //   КИП ИОС pro      — то же + canEdit (право записи в кабельный журнал).
    //   КИП ИОС дежурный — КИП ИОС + расходомеры (просмотр) + canInputReadings.
    //   ИТР8             — КИП ИОС + расходомеры (просмотр).
    //   ИТР8 pro         — то же, что ИТР8.
    //   ИТР ИОС          — ИТР8 + canEdit (право записи в кабельный журнал).
    //   Админ            — полный доступ ['*'] + админ-панель.
    // ============================================================
    _BASE_PAGES: ['dashboard'],
    _CALC_PAGES: ['calculators', 'calc-kipa', 'calc-electro', 'calc-geometry',
                  'converter', 'conv-temp', 'conv-pressure', 'conv-mass', 'conv-length',
                  'conv-volume', 'conv-flow', 'conv-density', 'conv-time',
                  'scale-signal',
                  'error-select', 'error-generic', 'error-generic-circle',
                  'error-generic-fraction', 'error-generic-number', 'error-generic-underline',
                  'error-kit', 'error-temp-rtd', 'error-temp-tc',
                  'error-flow', 'error-level', 'error-pressure', 'error-scale', 'error-temp',
                  'buoy-select', 'buoy-calc', 'temp-sensors',
                  'orifice-select', 'orifice-quick', 'orifice-dp', 'orifice-flow', 'orifice-diameter',
                  'circuit-breaker',
                  'geo-circle', 'geo-ring', 'geo-cylinder', 'geo-horiz', 'geo-sphere', 'geo-cone'],
    _LIBRARY_PAGES: ['docs', 'library', 'library-internal', 'library-electro',
                     'exam-tickets', 'tickets-4', 'tickets-5', 'tickets-6', 'tickets-1000v'],
    _KIP_IOS_PAGES: ['kip-ios',
                     'docs-ios',
                     'devices-prod', 'devices-type', 'devices-name', 'device-detail', 'dev-group',
                     'device-favorites',
                     'lockouts-prod', 'lockout-detail', 'lock-group',
                     'valves-prod', 'valves-type', 'valves-name', 'valve-detail', 'valve-group',
                     'regulators-prod', 'regulator-detail', 'regulator-group',
                     'projects-prod', 'project-detail', 'project-group',
                     'cable-journal-edit',
                     'cable-journal-add',
                     'cable-journal-view',
                     'plan-114', 'plan-114-view'],
    // Расходомеры хозрасчётные — отдельная группа доступа
    // (просмотр: ИТР8+, КИП ИОС дежурный; НЕ входит в базовый КИП ИОС)
    _FLOWMETER_PAGES: ['flowmeter-data', 'flowmeter-detail'],
    // Графики КИП ИОС — отдельная группа доступа (только Админ)
    _CHARTS_PAGES: ['charts'],
    _SECRET_PAGES: ['minesweeper', 'phonebook'],
    _WHATS_NEW_PAGES: ['whats-new'],

    ROLE_ACCESS: null,  // вычисляется в init()

    // ============================================================
    // Инициализация карты доступа (вызывается один раз).
    // ============================================================
    init: function() {
        if (this.ROLE_ACCESS) return; // уже инициализирована
        const BASE = this._BASE_PAGES;
        const CALC = this._CALC_PAGES;
        const LIB = this._LIBRARY_PAGES;
        const KIP_IOS = this._KIP_IOS_PAGES;
        const SECRET = this._SECRET_PAGES;
        const WHATS_NEW = this._WHATS_NEW_PAGES;

        // Уровни доступа (по карте ролей из Excel, актуальная 2026-08-15):
        const FLOWMETER = this._FLOWMETER_PAGES;
        const CHARTS = this._CHARTS_PAGES;

        const LVL_OBSHCHIJ = [].concat(BASE, CALC);
        const LVL_KIP8 = [].concat(BASE, CALC, LIB, SECRET, WHATS_NEW);
        const LVL_KIP_IOS = [].concat(BASE, CALC, LIB, KIP_IOS, SECRET, WHATS_NEW);
        // ИТР8+ и КИП ИОС дежурный: КИП ИОС + расходомеры (просмотр)
        const LVL_KIP_IOS_WITH_FLOW = [].concat(BASE, CALC, LIB, KIP_IOS, FLOWMETER, SECRET, WHATS_NEW);

        this.ROLE_ACCESS = {
            'Запрет': BASE,                   // только главная
            'Общий доступ': LVL_OBSHCHIJ,     // только калькуляторы (гостевой режим)
            'КИП8': LVL_KIP8,
            'КИП8 pro': LVL_KIP8,
            'КИП ИОС': LVL_KIP_IOS,
            'КИП ИОС pro': LVL_KIP_IOS,       // + canEdit (право записи в каб. журнал)
            'КИП ИОС дежурный': LVL_KIP_IOS_WITH_FLOW,  // + canInputReadings (расходомеры)
            'ИТР8': LVL_KIP_IOS_WITH_FLOW,
            'ИТР8 pro': LVL_KIP_IOS_WITH_FLOW,
            'ИТР ИОС': LVL_KIP_IOS_WITH_FLOW, // + canEdit (право записи в каб. журнал)
            'Админ': ['*']
        };
    },

    // ============================================================
    // Работа с токеном.
    // ============================================================
    getToken: function() {
        try { return localStorage.getItem(this.TOKEN_KEY) || ''; } catch (e) { return ''; }
    },
    setToken: function(token) {
        try { localStorage.setItem(this.TOKEN_KEY, token); } catch (e) {}
    },
    clearToken: function() {
        try { localStorage.removeItem(this.TOKEN_KEY); } catch (e) {}
    },

    // ============================================================
    // API: вызов Apps Script.
    // ============================================================
    api: function(action, payload) {
        const url = this.WEB_APP_URL + '?action=' + encodeURIComponent(action);
        // ВАЖНО: используем Content-Type: text/plain;charset=utf-8, а НЕ application/json.
        // Причина: application/json — это "non-simple" Content-Type, который заставляет
        // браузер отправлять CORS-preflight (OPTIONS-запрос) перед POST. Apps Script
        // НЕ определяет doOptions, возвращает 405 Method Not Allowed на preflight,
        // браузер блокирует POST → пользователь видит "Failed to fetch".
        // text/plain;charset=utf-8 — это "simple" Content-Type, preflight не отправляется,
        // POST идёт сразу. Тело запроса остаётся JSON-строкой, Apps Script парсит его
        // через e.postData.contents + JSON.parse (см. Code.gs doPost).
        const doFetch = function() {
            return fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'text/plain;charset=utf-8' },
                body: JSON.stringify(payload || {}),
                redirect: 'follow'
            }).then(function(r) {
                // Если ответ не OK — это серверная ошибка (5xx) или недоступность.
                if (!r.ok) {
                    // Классифицируем как NETWORK_ERROR — bootstrap не должен сбрасывать токен.
                    const err = new Error('NETWORK_ERROR: HTTP ' + r.status);
                    err._kind = 'NETWORK';
                    throw err;
                }
                // Получаем текст, потом парсим JSON — чтобы отличить HTML-ответ от JSON.
                return r.text().then(function(txt) {
                    let data;
                    try {
                        data = JSON.parse(txt);
                    } catch (e) {
                        // Google иногда отдаёт HTML (redirect page, error page) вместо JSON.
                        // Классифицируем как NETWORK_ERROR — это не вина сессии.
                        const err = new Error('NETWORK_ERROR: сервер вернул не JSON (возможно HTML)');
                        err._kind = 'NETWORK';
                        throw err;
                    }
                    if (!data || typeof data !== 'object') {
                        const err = new Error('NETWORK_ERROR: некорректный ответ сервера');
                        err._kind = 'NETWORK';
                        throw err;
                    }
                    if (!data.ok) {
                        // Сервер вернул корректный JSON с ошибкой.
                        // Это может быть session_expired, no_session, или бизнес-ошибка.
                        const err = new Error(data.error || 'Неизвестная ошибка сервера');
                        err._kind = 'SERVER';
                        throw err;
                    }
                    return data.data;
                });
            }).catch(function(err) {
                // TypeError: Failed to fetch — браузер не смог выполнить запрос вообще
                // (нет сети, CORS заблокирован, прерван и т.д.).
                if (err && (err.name === 'TypeError' || /Failed to fetch/i.test(err.message))) {
                    const e = new Error('NETWORK_ERROR: Failed to fetch');
                    e._kind = 'NETWORK';
                    throw e;
                }
                // Если уже классифицировали — пробрасываем как есть.
                if (err && err._kind) throw err;
                // Неизвестная ошибка — считаем сетевой (безопасный вариант).
                const e = new Error('NETWORK_ERROR: ' + (err && err.message ? err.message : 'unknown'));
                e._kind = 'NETWORK';
                throw e;
            });
        };

        // Retry для сетевых ошибок: 2 попытки с задержкой 1 сек.
        // Серверные ошибки (session_expired и т.д.) НЕ ретраим —
        // повторный запрос даст тот же результат.
        return doFetch().catch(function(err) {
            if (err && err._kind === 'NETWORK') {
                return new Promise(function(resolve) {
                    setTimeout(resolve, 1000);
                }).then(doFetch);
            }
            throw err;
        });
    },

    // ============================================================
    // Флоу входа: отправить OTP.
    // ============================================================
    sendOTP: function() {
        const emailRaw = document.getElementById('authEmail').value;
        const email = (emailRaw || '').trim().toLowerCase();
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            this._showError('Введите корректный email');
            return;
        }

        this._pendingEmail = email;
        this._showError('');
        const btn = document.getElementById('authSendBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="auth-loading"></span>Отправка…';

        const self = this;
        this.api('sendOTP', { email: email }).then(function() {
            // Перейти на шаг 2 (ввод OTP).
            document.getElementById('authEmailDisplay').textContent = email;
            self._switchStep(2);
            setTimeout(function() { document.getElementById('otp1').focus(); }, 100);
            self._startResendCooldown(60);
        }).catch(function(err) {
            self._showError(err.message);
        }).then(function() {
            btn.disabled = false;
            btn.innerHTML = 'Отправить код';
        });
    },

    // ============================================================
    // Флоу входа: повторный запрос OTP.
    // ============================================================
    resendOTP: function() {
        if (this._resendCooldown > 0) return;
        if (!this._pendingEmail) return;

        this._showError('');
        const self = this;
        this.api('sendOTP', { email: this._pendingEmail }).then(function() {
            self._showError('Новый код отправлен');
            self._startResendCooldown(60);
        }).catch(function(err) {
            self._showError(err.message);
        });
    },

    // ============================================================
    // Cooldown для повторной отправки OTP.
    // ============================================================
    _startResendCooldown: function(seconds) {
        this._resendCooldown = seconds;
        const link = document.getElementById('authResendLink');
        link.classList.add('disabled');
        this._updateResendLink();
        const self = this;
        if (this._resendTimer) clearInterval(this._resendTimer);
        this._resendTimer = setInterval(function() {
            self._resendCooldown--;
            self._updateResendLink();
            if (self._resendCooldown <= 0) {
                clearInterval(self._resendTimer);
                link.classList.remove('disabled');
                link.textContent = 'Отправить повторно';
            }
        }, 1000);
    },
    _updateResendLink: function() {
        const link = document.getElementById('authResendLink');
        if (this._resendCooldown > 0) {
            link.textContent = 'Отправить повторно через ' + this._resendCooldown + ' сек';
        } else {
            link.textContent = 'Отправить повторно';
        }
    },

    // ============================================================
    // Флоу входа: верифицировать OTP.
    // ============================================================
    verifyOTP: function() {
        if (!this._pendingEmail) {
            this._showError('Сессия истекла, начните заново');
            this._switchStep(1);
            return;
        }

        const code = ['otp1','otp2','otp3','otp4','otp5','otp6']
            .map(function(id) { return document.getElementById(id).value; })
            .join('');

        if (!/^\d{6}$/.test(code)) {
            this._showError('Введите 6-значный код');
            return;
        }

        this._showError('');
        const btn = document.getElementById('authVerifyBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="auth-loading"></span>Проверка…';

        const self = this;
        this.api('verifyOTP', { email: this._pendingEmail, code: code }).then(function(data) {
            // data = { token, role, userId, email }
            self.setToken(data.token);
            self._cachedRole = data.role;
            self._cachedEmail = data.email;
            self._cachedUserId = data.userId;
            self._lastRoleFetch = Date.now();

            // ВАЖНО (Task 33): сохранить кэш роли в localStorage.
            // Без этого при reload браузера bootstrap() не найдёт кэш,
            // пойдёт по медленному пути (синхронный запрос сервера),
            // и при любой сетевой ошибке покажет экран входа.
            try {
                localStorage.setItem('kip8_cached_role', data.role || '');
                localStorage.setItem('kip8_cached_email', data.email || '');
                localStorage.setItem('kip8_cached_user_id', String(data.userId || ''));
            } catch (e) {}

            self._hideLoginScreen();
            self._startHeartbeat();
            self._updateSidebarUserInfo();
            self._applyRoleToUI();

            // Перейти на главную страницу.
            if (typeof window.navigateTo === 'function') window.navigateTo('dashboard');
        }).catch(function(err) {
            self._showError(err.message);
            // Очистить OTP поля.
            ['otp1','otp2','otp3','otp4','otp5','otp6'].forEach(function(id) {
                const el = document.getElementById(id);
                el.value = '';
                el.classList.remove('filled');
            });
            document.getElementById('otp1').focus();
        }).then(function() {
            btn.disabled = false;
            btn.innerHTML = 'Войти';
        });
    },

    // ============================================================
    // Возврат на шаг 1 (email).
    // ============================================================
    backToStep1: function() {
        this._switchStep(1);
        this._showError('');
        ['otp1','otp2','otp3','otp4','otp5','otp6'].forEach(function(id) {
            const el = document.getElementById(id);
            el.value = '';
            el.classList.remove('filled');
        });
    },

    // ============================================================
    // Системная кнопка "← Назад" в верхнем углу экрана входа.
    // Контекстно-зависимое поведение:
    //   - Шаг 2 (OTP активен) → вернуться на Шаг 1 (backToStep1).
    //   - Шаг 1 (email) → cancelLogin (закрыть экран, гостевой режим).
    // ============================================================
    handleBackButton: function() {
        const step2 = document.getElementById('authStep2');
        const onStep2 = step2 && step2.classList.contains('active');
        if (onStep2) {
            this.backToStep1();
        } else {
            this.cancelLogin();
        }
    },

    // ============================================================
    // Отмена входа: закрыть экран входа и вернуться в гостевой
    // режим ("Общий доступ"). Токен при этом не трогается (его
    // нет у гостя), heartbeat не запускается. Пользователь
    // остаётся в приложении с доступом к калькуляторам.
    // ============================================================
    cancelLogin: function() {
        this._hideLoginScreen();
        // Гостевой режим (если ещё не установлен).
        if (!this._cachedRole) {
            this._cachedRole = 'Общий доступ';
            this._cachedEmail = null;
            this._cachedUserId = null;
        }
        this._updateSidebarUserInfo();
        this._applyRoleToUI();
        if (typeof window.navigateTo === 'function') window.navigateTo('dashboard');
        // Очистить поля формы — на случай повторного открытия.
        const emailEl = document.getElementById('authEmail');
        if (emailEl) emailEl.value = '';
        ['otp1','otp2','otp3','otp4','otp5','otp6'].forEach(function(id) {
            const el = document.getElementById(id);
            el.value = '';
            el.classList.remove('filled');
        });
        this._showError('');
    },

    // ============================================================
    // Переключение шагов.
    // ============================================================
    _switchStep: function(n) {
        document.getElementById('authStep1').classList.toggle('active', n === 1);
        document.getElementById('authStep2').classList.toggle('active', n === 2);
    },

    // ============================================================
    // Показать/скрыть экран входа.
    // ============================================================
    _showLoginScreen: function() {
        document.getElementById('loginScreen').classList.add('active');
        this._switchStep(1);
        document.getElementById('authEmail').value = '';
        ['otp1','otp2','otp3','otp4','otp5','otp6'].forEach(function(id) {
            const el = document.getElementById(id);
            el.value = '';
            el.classList.remove('filled');
        });
        this._showError('');
        setTimeout(function() { document.getElementById('authEmail').focus(); }, 100);
    },
    _hideLoginScreen: function() {
        document.getElementById('loginScreen').classList.remove('active');
    },

    // ============================================================
    // Сообщение об ошибке.
    // ============================================================
    _showError: function(msg) {
        document.getElementById('authError').textContent = msg || '';
    },

    // ============================================================
    // Получить текущего пользователя (с кэшированием 30 сек).
    // ============================================================
    getCurrentUser: function() {
        const token = this.getToken();
        if (!token) return Promise.reject(new Error('no_session'));

        if (this._cachedRole && (Date.now() - this._lastRoleFetch) < this.ROLE_CACHE_TTL) {
            return Promise.resolve({
                userId: this._cachedUserId,
                email: this._cachedEmail,
                role: this._cachedRole
            });
        }

        const self = this;
        return this.api('getCurrentUser', { token: token }).then(function(data) {
            self._cachedRole = data.role;
            self._cachedEmail = data.email;
            self._cachedUserId = data.userId;
            self._lastRoleFetch = Date.now();
            return data;
        });
    },

    // ============================================================
    // Heartbeat: каждые 5 минут продлеваем сессию.
    // ============================================================
    _startHeartbeat: function() {
        if (this._heartbeatTimer) clearInterval(this._heartbeatTimer);
        const self = this;
        this._heartbeatTimer = setInterval(function() {
            const token = self.getToken();
            if (!token) {
                self.handleSessionExpired('Нет токена');
                return;
            }
            self.api('heartbeat', { token: token }).catch(function(err) {
                self.handleSessionExpired(err.message);
            });
        }, this.HEARTBEAT_INTERVAL);
    },

    // ============================================================
    // Logout: ручной или принудительный.
    // ============================================================
    logout: function() {
        const token = this.getToken();
        if (token) {
            // Отправить logout на сервер (не дожидаемся ответа).
            this.api('logout', { token: token }).catch(function() {});
        }
        this.clearToken();
        // Очистить кэш роли.
        try {
            localStorage.removeItem('kip8_cached_role');
            localStorage.removeItem('kip8_cached_email');
            localStorage.removeItem('kip8_cached_user_id');
        } catch (e) {}
        this._cachedRole = null;
        this._cachedEmail = null;
        this._cachedUserId = null;
        if (this._heartbeatTimer) {
            clearInterval(this._heartbeatTimer);
            this._heartbeatTimer = null;
        }
        // ============================================================
        // После выхода — гостевой режим (Task 38).
        // ============================================================
        // Не показываем экран входа принудительно — пользователь
        // автоматически переходит в гостевой режим "Общий доступ"
        // и может пользоваться калькуляторами. Кнопка "Войти" в sidebar
        // позволит ему снова войти при необходимости.
        // ============================================================
        this._cachedRole = 'Общий доступ';
        this._cachedEmail = null;
        this._cachedUserId = null;
        this._updateSidebarUserInfo();
        this._applyRoleToUI();
        if (typeof window.navigateTo === 'function') window.navigateTo('dashboard');
        // Закрыть sidebar если открыт.
        const sidebar = document.getElementById('sidebar');
        if (sidebar && sidebar.classList.contains('active')) {
            if (typeof toggleSidebar === 'function') toggleSidebar();
        }
    },

    // ============================================================
    // Сессия истекла: принудительный logout.
    // ВАЖНО: вызывается из heartbeat при ошибке. Различаем:
    //   - SERVER-ошибка session_expired/no_session → реальный logout
    //   - NETWORK-ошибка → НЕ трогаем токен, оставляем пользователя в приложении
    //     (heartbeat продолжит попытки, при восстановлении сети обновится)
    // ============================================================
    handleSessionExpired: function(reason) {
        console.log('Session expired handler:', reason);
        const msg = (reason && reason.message) || String(reason || '');
        const kind = reason && reason._kind;
        const isSessionInvalid =
            (kind === 'SERVER') &&
            (msg === 'session_expired' || msg === 'no_session');

        if (!isSessionInvalid) {
            // Сетевая ошибка — не выходим из аккаунта.
            // Heartbeat продолжит работать, при восстановлении сети обновится.
            console.warn('[KipAuth] Сетевая ошибка heartbeat, токен сохранён:', msg);
            return;
        }

        // Реальный logout → переход в гостевой режим (Task 38).
        this.clearToken();
        // Очистить кэш роли.
        try {
            localStorage.removeItem('kip8_cached_role');
            localStorage.removeItem('kip8_cached_email');
            localStorage.removeItem('kip8_cached_user_id');
        } catch (e) {}
        if (this._heartbeatTimer) {
            clearInterval(this._heartbeatTimer);
            this._heartbeatTimer = null;
        }
        // Гостевой режим вместо экрана входа.
        this._cachedRole = 'Общий доступ';
        this._cachedEmail = null;
        this._cachedUserId = null;
        this._updateSidebarUserInfo();
        this._applyRoleToUI();
        if (typeof window.navigateTo === 'function') window.navigateTo('dashboard');
        // Тихое уведомление в консоль (не показываем ошибку пользователю,
        // т.к. приложение остаётся доступным в гостевом режиме).
        console.warn('[KipAuth] Сессия истекла → переход в гостевой режим');
    },

    // ============================================================
    // Проверка доступа к странице.
    // ============================================================
    canAccess: function(page) {
        if (!this._cachedRole) return false;
        // ============================================================
        // Защита admin-страниц: только роль "Админ".
        // Это двойная защита — даже если ROLE_ACCESS случайно
        // включит admin-страницу в список, доступ всё равно
        // разрешён только Админу.
        // ============================================================
        if (page === 'admin' || page === 'admin-users' ||
            page === 'admin-sessions' || page === 'admin-logs' ||
            page === 'admin-stats') {
            return this._cachedRole === 'Админ';
        }
        const allowed = this.ROLE_ACCESS[this._cachedRole];
        if (!allowed) return false;
        if (allowed.indexOf('*') !== -1) return true;
        return allowed.indexOf(page) !== -1;
    },

    // ============================================================
    // Показать экран "нет доступа".
    // ============================================================
    _showNoAccess: function(page) {
        let el = document.getElementById('noAccessScreen');
        if (!el) {
            el = document.createElement('div');
            el.id = 'noAccessScreen';
            el.style.cssText = 'position:fixed;inset:0;background:#0d1117;z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box;';
            el.innerHTML =
                '<div class="no-access-screen">' +
                '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>' +
                '<h3>Нет доступа</h3>' +
                '<p>У вашей роли «<b id="noAccessRole"></b>» нет прав на раздел <b id="noAccessPage"></b>.</p>' +
                '<button onclick="KipAuth._closeNoAccess()">На главную</button>' +
                '</div>';
            document.body.appendChild(el);
        }
        document.getElementById('noAccessRole').textContent = this._cachedRole || '—';
        document.getElementById('noAccessPage').textContent = page;
        el.style.display = 'flex';
    },
    _closeNoAccess: function() {
        const el = document.getElementById('noAccessScreen');
        if (el) el.style.display = 'none';
        if (typeof window.navigateTo === 'function') window.navigateTo('dashboard');
    },

    // ============================================================
    // Применить роль к UI: скрыть недоступные разделы в sidebar.
    // ============================================================
    _applyRoleToUI: function() {
        if (!this._cachedRole) return;
        const allowed = this.ROLE_ACCESS[this._cachedRole] || [];
        const isAll = allowed.indexOf('*') !== -1;
        const self = this;

        // Sidebar items: извлечь page из onclick="navigateTo('xxx')".
        document.querySelectorAll('.sidebar-item').forEach(function(item) {
            const onclick = item.getAttribute('onclick') || '';
            const m = onclick.match(/navigateTo\(['"]([^'"]+)['"]/);
            if (!m) return; // нет navigateTo — внешняя ссылка или сервисная кнопка
            const page = m[1];
            const allowedForPage = isAll || allowed.indexOf(page) !== -1;
            item.style.display = allowedForPage ? '' : 'none';
        });

        // Sidebar groups: скрыть целиком, если все .sidebar-item скрыты.
        // ВАЖНО: отдельная проверка по data-requires="library" / "kip-ios".
        // Если у группы есть data-requires и роль не имеет доступа к этой
        // странице — скрыть ВСЮ группу целиком, включая внешние ссылки <a>
        // (которые не имеют navigateTo и поэтому не обрабатываются выше).
        document.querySelectorAll('.sidebar-group').forEach(function(group) {
            // Сначала проверим data-requires (если есть).
            const requires = group.getAttribute('data-requires');
            if (requires) {
                const reqAllowed = isAll || allowed.indexOf(requires) !== -1;
                if (!reqAllowed) {
                    // Скрыть всю группу + все её дочерние элементы.
                    group.style.display = 'none';
                    group.querySelectorAll('.sidebar-item').forEach(function(item) {
                        item.style.display = 'none';
                    });
                    return; // дальше не идём — группа уже скрыта.
                }
            }
            // Иначе — старая логика: скрыть группу, если все её
            // sidebar-item скрыты.
            const items = group.querySelectorAll('.sidebar-item');
            if (items.length === 0) return;
            let anyVisible = false;
            items.forEach(function(item) {
                if (item.style.display !== 'none') anyVisible = true;
            });
            group.style.display = anyVisible ? '' : 'none';
        });

        // Dashboard menu buttons: извлечь page из onclick.
        document.querySelectorAll('.menu-btn').forEach(function(btn) {
            const onclick = btn.getAttribute('onclick') || '';
            const m = onclick.match(/navigateTo\(['"]([^'"]+)['"]/);
            if (!m) return; // не навигационная кнопка
            const page = m[1];
            const allowedForPage = isAll || allowed.indexOf(page) !== -1;
            btn.style.display = allowedForPage ? '' : 'none';
        });

        // ============================================================
        // Кнопка «Расходомеры хозрасчётные» в Документации ИОС:
        // скрыть для пользователей без доступа к flowmeter-data,
        // а также скрыть родительский .kip-ios-block, если внутри
        // не осталось видимых кнопок.
        // ============================================================
        const flowmeterBtn = document.getElementById('flowmeterMenuBtn');
        if (flowmeterBtn) {
            const hasFlowAccess = isAll || allowed.indexOf('flowmeter-data') !== -1;
            flowmeterBtn.style.display = hasFlowAccess ? '' : 'none';
            // Скрыть родительский .kip-ios-block целиком, если все .menu-btn скрыты
            const kipBlock = flowmeterBtn.closest('.kip-ios-block');
            if (kipBlock) {
                const visibleBtns = kipBlock.querySelectorAll('.menu-btn');
                let anyVisible = false;
                visibleBtns.forEach(function(b) {
                    if (b.style.display !== 'none') anyVisible = true;
                });
                kipBlock.style.display = anyVisible ? '' : 'none';
            }
        }

        // ============================================================
        // Кнопка «Графики» в КИП ИОС (chartsEntryBtn):
        // onclick назначается через JS (btn.onclick), поэтому
        // общий цикл .menu-btn по getAttribute('onclick') её не ловит.
        // Скрыть для пользователей без доступа к charts.
        // ============================================================
        const chartsBtn = document.getElementById('chartsEntryBtn');
        if (chartsBtn) {
            const hasChartsAccess = isAll || allowed.indexOf('charts') !== -1;
            chartsBtn.style.display = hasChartsAccess ? '' : 'none';
        }

        // Скрыть кнопки "Сапёр" и "Телефонный справочник" на главной,
        // если нет доступа.
        const minesweeperBtn = document.getElementById('minesweeperBtn');
        if (minesweeperBtn) {
            minesweeperBtn.style.display = (isAll || allowed.indexOf('minesweeper') !== -1) ? '' : 'none';
        }
        const phonebookBtn = document.getElementById('phonebookBtn');
        if (phonebookBtn) {
            phonebookBtn.style.display = (isAll || allowed.indexOf('phonebook') !== -1) ? '' : 'none';
        }

        // ============================================================
        // Нижний бар на главной (dashboardBottomBar):
        //   - Кнопка "Инженерные калькуляторы" — видна всегда.
        //   - Кнопка "Документация" — видна только ролям с доступом
        //     к библиотеке/КИП ИОС (т.е. не "Общий доступ" и не "Запрет").
        //     Для гостей оставляем только калькуляторы.
        // ============================================================
        const docsBottomBtn = document.querySelector('.dashboard-bottom-btn-docs');
        if (docsBottomBtn) {
            const hasDocsAccess = isAll
                || allowed.indexOf('docs') !== -1
                || allowed.indexOf('library') !== -1
                || allowed.indexOf('kip-ios') !== -1;
            docsBottomBtn.style.display = hasDocsAccess ? '' : 'none';
        }

        // ============================================================
        // Кнопка "Выйти" в sidebar — скрывается для гостевой роли
        // "Общий доступ" (гостю не из чего выходить, он уже не
        // залогинен). Для всех остальных ролей — видна как обычно.
        // ============================================================
        const sidebarLogoutBtn = document.getElementById('sidebarLogoutBtn');
        if (sidebarLogoutBtn) {
            const isGuest = this._cachedRole === 'Общий доступ';
            sidebarLogoutBtn.style.display = isGuest ? 'none' : '';
        }

        // ============================================================
        // Кнопка "Админ-панель" в sidebar — видна ТОЛЬКО роли "Админ".
        // ============================================================
        const sidebarAdminBtn = document.getElementById('sidebarAdminBtn');
        if (sidebarAdminBtn) {
            const isAdmin = this._cachedRole === 'Админ';
            sidebarAdminBtn.style.display = isAdmin ? '' : 'none';
        }

        // ============================================================
        // Кнопка «?» (Что нового) — видна всем ролям, кроме
        // «Запрет» и «Общий доступ» (гости не видят обновлений).
        // ============================================================
        var whatsNewAllowed = isAll || allowed.indexOf('whats-new') !== -1;
        var mobileWhatsNewBtn = document.getElementById('mobileWhatsNewBtn');
        if (mobileWhatsNewBtn) {
            mobileWhatsNewBtn.style.display = whatsNewAllowed ? '' : 'none';
        }
        var desktopWhatsNewBtn = document.getElementById('desktopWhatsNewBtn');
        if (desktopWhatsNewBtn) {
            desktopWhatsNewBtn.style.display = whatsNewAllowed ? '' : 'none';
        }

        // ============================================================
        // Десктоп: верхний бар — скрыть вкладки без доступа.
        //   - «Инженерные калькуляторы» (data-page="calculators") — видна
        //     всегда (калькуляторы доступны всем ролям).
        //   - «Документация» (data-page="docs") — видна только ролям
        //     с доступом к docs / library / kip-ios.
        //   - Разделители (.desktop-top-bar-divider) скрываются,
        //     если соседняя вкладка скрыта.
        // ============================================================
        document.querySelectorAll('.desktop-top-bar-tab').forEach(function(tab) {
            const page = tab.getAttribute('data-page');
            if (!page) return;
            // «Документация» требует доступа к docs/library/kip-ios
            let tabAllowed;
            if (page === 'docs') {
                tabAllowed = isAll
                    || allowed.indexOf('docs') !== -1
                    || allowed.indexOf('library') !== -1
                    || allowed.indexOf('kip-ios') !== -1;
            } else {
                tabAllowed = isAll || allowed.indexOf(page) !== -1;
            }
            tab.style.display = tabAllowed ? '' : 'none';
        });
        // Скрыть разделители, у которых соседняя вкладка скрыта
        document.querySelectorAll('.desktop-top-bar-divider').forEach(function(div) {
            const prev = div.previousElementSibling;
            const next = div.nextElementSibling;
            const prevHidden = prev && prev.classList.contains('desktop-top-bar-tab') && prev.style.display === 'none';
            const nextHidden = next && next.classList.contains('desktop-top-bar-tab') && next.style.display === 'none';
            // Скрыть разделитель, если обе соседние вкладки скрыты,
            // или если вкладка слева скрыта (разделитель относится к ней)
            if (prevHidden || (prevHidden && nextHidden)) {
                div.style.display = 'none';
            } else {
                div.style.display = '';
            }
        });

        // ============================================================
        // Десктоп: скрыть пустые menu-btn-row на активной странице.
        // Если после фильтрации все .menu-btn в строке скрыты —
        // скрываем всю строку, чтобы не было пустого пространства.
        // ============================================================
        document.querySelectorAll('.menu-btn-row').forEach(function(row) {
            const btns = row.querySelectorAll('.menu-btn');
            if (btns.length === 0) return;
            let anyVisible = false;
            btns.forEach(function(btn) {
                if (btn.style.display !== 'none') anyVisible = true;
            });
            row.style.display = anyVisible ? '' : 'none';
        });

        // ============================================================
        // Закреплённые элементы: скрыть .pinned-item-cell,
        // если вложенный .pinned-item (.menu-btn) скрыт.
        // ============================================================
        document.querySelectorAll('.pinned-item-cell').forEach(function(cell) {
            const btn = cell.querySelector('.pinned-item');
            if (!btn) return;
            cell.style.display = (btn.style.display === 'none') ? 'none' : '';
        });
        // Скрыть весь контейнер закреплённых, если все ячейки скрыты
        const pinnedContainer = document.getElementById('pinnedItemsContainer');
        if (pinnedContainer) {
            const visibleCells = pinnedContainer.querySelectorAll('.pinned-item-cell');
            let anyPinnedVisible = false;
            visibleCells.forEach(function(cell) {
                if (cell.style.display !== 'none') anyPinnedVisible = true;
            });
            // Если нет видимых закреплённых — показываем подсказку
            // (перерендерим через renderPinnedItems, которая учитывает
            // фильтрацию при следующем вызове _applyRoleToUI)
            if (!anyPinnedVisible && visibleCells.length > 0) {
                pinnedContainer.style.display = 'none';
            } else {
                pinnedContainer.style.display = '';
            }
        }

        // ============================================================
        // Десктоп: скрыть пустые группы (pb-section / dev-group)
        // на страницах каталогов, если все карточки скрыты.
        // Это актуально для roles с ограниченным доступом.
        // ============================================================
        document.querySelectorAll('.pb-section').forEach(function(section) {
            const body = section.querySelector('.pb-section-body');
            if (!body) return;
            const cards = body.querySelectorAll('.dev-card, .lock-card, .valve-card, .regulator-card, .project-card');
            if (cards.length === 0) return;
            let anyCardVisible = false;
            cards.forEach(function(card) {
                if (card.style.display !== 'none') anyCardVisible = true;
            });
            if (!anyCardVisible) {
                section.style.display = 'none';
            } else {
                section.style.display = '';
            }
        });

        // ============================================================
        // Примечание: раздел "Кабельный журнал" объединён с ред. версией.
        // Кнопка в sidebar одна; видимость UI редактирования (кнопка
        // "+ Добавить", поля в модалке) управляется флагом canEdit,
        // который сервер возвращает в cableJournal.list / getColumns.
        // Роли с правом записи: Админ, ИТР ИОС, КИП ИОС pro.
        // Просмотр кабельного журнала — всем ролям с доступом к КИП ИОС.
        // Право записи определяется сервером (canEdit в cableJournal.getColumns).
        // ============================================================

        // ============================================================
        // Обновить право ввода показаний в расходомеры хозрасчётные.
        // Роли с правом: КИП ИОС дежурный, Админ.
        // ============================================================
        if (typeof FlowmeterData !== 'undefined') {
            FlowmeterData._canInputReadings = FlowmeterData._computeCanInputReadings();
        }
    },

    // ============================================================
    // Обновить информацию о пользователе в sidebar.
    // ============================================================
    // Для гостей (нет токена) — показываем "Гость" + кнопку "Войти".
    // Для залогиненных — email + роль.
    _updateSidebarUserInfo: function() {
        const el = document.getElementById('sidebarUserInfo');
        if (!el) return;
        const token = this.getToken();
        if (!token) {
            // Гостевой режим.
            el.innerHTML =
                '<div class="sidebar-user-email">Гость</div>' +
                '<div class="sidebar-user-role">Общий доступ</div>' +
                '<button type="button" id="guestLoginBtn" ' +
                'style="margin-top:8px;padding:8px 12px;background:#4a8fc7;color:#fff;border:none;' +
                'border-radius:6px;cursor:pointer;font-size:13px;width:100%;">' +
                'Войти в аккаунт</button>';
            const btn = document.getElementById('guestLoginBtn');
            if (btn) {
                btn.addEventListener('click', function() {
                    KipAuth._showLoginScreen();
                });
            }
        } else {
            // Залогиненный пользователь: email + роль слева,
            // кнопка "Выйти" (иконка) справа в той же строке.
            // id="sidebarLogoutBtn" сохранён для совместимости с _applyRoleToUI().
            el.innerHTML =
                '<div class="sidebar-user-row">' +
                    '<div class="sidebar-user-text">' +
                        '<div class="sidebar-user-email">' + (this._cachedEmail || '—') + '</div>' +
                        '<div class="sidebar-user-role">' + (this._cachedRole || '—') + '</div>' +
                    '</div>' +
                    '<button type="button" id="sidebarLogoutBtn" class="sidebar-logout-icon" ' +
                        'onclick="KipAuth.logout()" aria-label="Выйти" title="Выйти">' +
                        '<svg viewBox="0 0 24 24">' +
                            '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>' +
                            '<polyline points="16 17 21 12 16 7"></polyline>' +
                            '<line x1="21" y1="12" x2="9" y2="12"></line>' +
                        '</svg>' +
                    '</button>' +
                '</div>';
        }
    },

    // ============================================================
    // Bootstrap: вызывается при загрузке страницы.
    // ============================================================
    // Стратегия (Task 33):
    //   1. Если токена нет → экран входа.
    //   2. Если токен есть И есть кэшированная роль в localStorage →
    //      НЕЗАМЕДЛИТЕЛЬНО показать приложение с кэшированной ролью.
    //      Проверку сервера (getCurrentUser) сделать В ФОНЕ. Если сервер
    //      подтвердит сессию — обновить кэш. Если скажет no_session /
    //      session_expired — сделать logout. Если сеть недоступна —
    //      оставить пользователя в приложении с кэшированной ролью.
    //      Это решает проблему "вылет при reload из-за временной ошибки сети".
    //   3. Если токен есть, но кэша нет (первый вход на этом устройстве) →
    //      ждем ответа сервера синхронно (старое поведение).
    // ============================================================
    bootstrap: function() {
        if (this._initializing) return;
        this._initializing = true;

        this.init();

        const token = this.getToken();
        if (!token) {
            // ============================================================
            // ГОСТЕВОЙ РЕЖИМ (Task 38)
            // ============================================================
            // По карте ролей: "Общий доступ" не требует входа через почту и код.
            // Любой, кто открыл приложение, получает доступ к инженерным
            // калькуляторам как гость. Для доступа к библиотеке, КИП ИОС,
            // секретным кнопкам и админ-панели нужно войти через email+OTP.
            // ============================================================
            console.log('[KipAuth.bootstrap] Гостевой режим: нет токена → роль "Общий доступ"');
            this._cachedRole = 'Общий доступ';
            this._cachedEmail = null;
            this._cachedUserId = null;
            this._lastRoleFetch = Date.now();
            // НЕ запускаем heartbeat — у гостя нет сессии.
            this._updateSidebarUserInfo();
            this._applyRoleToUI();
            this._initializing = false;
            return;
        }

        // Прочитать кэш роли из localStorage.
        let cachedRole = null, cachedEmail = null, cachedUserId = null;
        try {
            cachedRole = localStorage.getItem('kip8_cached_role') || null;
            cachedEmail = localStorage.getItem('kip8_cached_email') || null;
            cachedUserId = localStorage.getItem('kip8_cached_user_id') || null;
        } catch (e) {}

        const self = this;

        // ===== Быстрый путь: токен + кэш → показать приложение сразу =====
        // Проверка сервера пойдёт в фоне (this._verifySessionInBackground).
        // Если сервер скажет "no_session" — тогда logout. Если сеть упала —
        // пользователь останется в приложении с кэшированной ролью.
        if (cachedRole) {
            console.log('[KipAuth.bootstrap] Быстрый путь: token + cachedRole="' + cachedRole + '" → показать приложение, проверка в фоне');
            self._cachedRole = cachedRole;
            self._cachedEmail = cachedEmail;
            self._cachedUserId = cachedUserId;
            self._lastRoleFetch = Date.now();
            self._startHeartbeat();
            self._updateSidebarUserInfo();
            self._applyRoleToUI();
            self._initializing = false;
            // Асинхронная проверка сервера в фоне.
            self._verifySessionInBackground();
            return;
        }

        console.log('[KipAuth.bootstrap] Медленный путь: token есть, но кэша роли нет → синхронный запрос сервера');

        // ===== Медленный путь: токен есть, кэша нет — ждём ответа сервера =====
        this.api('getCurrentUser', { token: token }).then(function(data) {
            self._cachedRole = data.role;
            self._cachedEmail = data.email;
            self._cachedUserId = data.userId;
            self._lastRoleFetch = Date.now();
            // Сохранить роль в localStorage для восстановления при сетевом сбое.
            try {
                localStorage.setItem('kip8_cached_role', data.role || '');
                localStorage.setItem('kip8_cached_email', data.email || '');
                localStorage.setItem('kip8_cached_user_id', String(data.userId || ''));
            } catch (e) {}
            self._startHeartbeat();
            self._updateSidebarUserInfo();
            self._applyRoleToUI();
            self._initializing = false;
        }).catch(function(err) {
            self._initializing = false;
            // Классификация ошибки:
            //   - SERVER-ошибка с сообщением 'session_expired' или 'no_session':
            //     сервер точно сказал, что сессии нет. Сбрасываем токен, показываем вход.
            //   - Любая другая ошибка (NETWORK или неизвестная):
            //     не трогаем токен, показываем экран входа с пояснением.
            //     Кэша нет, поэтому показать приложение не из чего.
            const msg = (err && err.message) || '';
            const kind = err && err._kind;
            const isSessionInvalid =
                (kind === 'SERVER') &&
                (msg === 'session_expired' || msg === 'no_session');

            if (isSessionInvalid) {
                // Сервер сказал, что сессии нет → гостевой режим (Task 38).
                self.clearToken();
                try {
                    localStorage.removeItem('kip8_cached_role');
                    localStorage.removeItem('kip8_cached_email');
                    localStorage.removeItem('kip8_cached_user_id');
                } catch (e) {}
                self._cachedRole = 'Общий доступ';
                self._cachedEmail = null;
                self._cachedUserId = null;
                self._updateSidebarUserInfo();
                self._applyRoleToUI();
                if (typeof window.navigateTo === 'function') window.navigateTo('dashboard');
                console.warn('[KipAuth.bootstrap] Сессия недействительна → гостевой режим');
            } else {
                // Сетевая ошибка, но кэша нет — показать вход с пояснением.
                // Токен НЕ удаляем, чтобы пользователь мог обновить страницу.
                self._showLoginScreen();
                self._showError(
                    'Не удалось связаться с сервером. ' +
                    'Проверьте подключение к интернету и обновите страницу.'
                );
                console.warn('[KipAuth.bootstrap] Сетевая ошибка, токен сохранён:', msg);
            }
        });
    },

    // ============================================================
    // Фоновая проверка сессии после быстрого старта из кэша.
    // ============================================================
    // Вызывается из bootstrap() когда приложение уже показано с кэшированной
    // ролью. Делает запрос getCurrentUser в фоне:
    //   - Успех: обновить кэш (роль могла измениться на сервере) и пере-применить UI.
    //   - SERVER-ошибка no_session/session_expired: реальный logout.
    //   - NETWORK-ошибка: ничего не делаем, пользователь остаётся в приложении.
    // ============================================================
    _verifySessionInBackground: function() {
        const self = this;
        const token = this.getToken();
        if (!token) return;

        console.log('[KipAuth._verifySessionInBackground] Запрос getCurrentUser, token=' + token.substring(0, 8) + '...');

        this.api('getCurrentUser', { token: token }).then(function(data) {
            // Сервер подтвердил сессию. Обновить кэш.
            console.log('[KipAuth._verifySessionInBackground] УСПЕХ:', JSON.stringify(data));
            self._cachedRole = data.role;
            self._cachedEmail = data.email;
            self._cachedUserId = data.userId;
            self._lastRoleFetch = Date.now();
            try {
                localStorage.setItem('kip8_cached_role', data.role || '');
                localStorage.setItem('kip8_cached_email', data.email || '');
                localStorage.setItem('kip8_cached_user_id', String(data.userId || ''));
            } catch (e) {}
            // Пере-применить роль к UI (на случай если изменилась).
            self._updateSidebarUserInfo();
            self._applyRoleToUI();
            console.log('[KipAuth] Фоновая проверка сессии OK');
        }).catch(function(err) {
            const msg = (err && err.message) || '';
            const kind = err && err._kind;
            console.warn('[KipAuth._verifySessionInBackground] ОТВЕТ СЕРВЕРА С ОШИБКОЙ:', { kind: kind, message: msg, fullError: err });
            const isSessionInvalid =
                (kind === 'SERVER') &&
                (msg === 'session_expired' || msg === 'no_session');

            if (isSessionInvalid) {
                // Реальный logout → переход в гостевой режим (Task 38).
                console.warn('[KipAuth._verifySessionInBackground] → ГОСТЕВОЙ РЕЖИМ: сервер сказал "' + msg + '"');
                self.clearToken();
                try {
                    localStorage.removeItem('kip8_cached_role');
                    localStorage.removeItem('kip8_cached_email');
                    localStorage.removeItem('kip8_cached_user_id');
                } catch (e) {}
                if (self._heartbeatTimer) {
                    clearInterval(self._heartbeatTimer);
                    self._heartbeatTimer = null;
                }
                self._cachedRole = 'Общий доступ';
                self._cachedEmail = null;
                self._cachedUserId = null;
                self._updateSidebarUserInfo();
                self._applyRoleToUI();
                if (typeof window.navigateTo === 'function') window.navigateTo('dashboard');
            } else {
                // Сетевая ошибка — пользователь остаётся в приложении.
                console.warn('[KipAuth._verifySessionInBackground] Сетевая ошибка, токен сохранён');
            }
        });
    }
};

export default KipAuth;
export { KipAuth };
