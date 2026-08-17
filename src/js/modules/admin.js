/**
 * @module admin
 * KipAdmin — админ-панель (users/sessions/logs/stats)
 * Extracted from src/index.html (lines 20178–20744)
 */

// ===== External dependency bridges =====
var KipAuth   = window.KipAuth;
var showToast = window.showToast;

// ============================================================
// KipAdmin — Админ-панель (старый код ниже)
// ============================================================
const KipAdmin = {

    // Кэш загруженных данных.
    _users: null,
    _sessions: null,
    _logs: null,

    // Список ролей для <select> (тот же, что в Utils.gs Admin.updateRole).
    ROLES: [
        'Запрет', 'Общий доступ',
        'КИП8', 'КИП8 pro',
        'КИП ИОС', 'КИП ИОС pro',
        'ИТР8', 'ИТР8 pro',
        'ИТР ИОС',
        'Админ'
    ],

    // ============================================================
    // Универсальный вызов админ-эндпоинта.
    // ============================================================
    _api: function(action, payload) {
        const token = KipAuth.getToken();
        if (!token) {
            return Promise.reject(new Error('Нет токена — войдите как Админ'));
        }
        return KipAuth.api(action, Object.assign({ token: token }, payload || {}));
    },

    // ============================================================
    // Загрузка данных.
    // ============================================================
    loadUsers: function() {
        const el = document.getElementById('adminUsersList');
        if (el) el.innerHTML = '<div class="admin-empty">Загрузка…</div>';
        const self = this;
        this._api('adminListUsers').then(function(users) {
            self._users = users || [];
            self.renderUsers();
        }).catch(function(err) {
            if (el) el.innerHTML = '<div class="admin-empty">Ошибка: ' + (err.message || err) + '</div>';
        });
    },

    loadSessions: function() {
        const el = document.getElementById('adminSessionsList');
        if (el) el.innerHTML = '<div class="admin-empty">Загрузка…</div>';
        const self = this;
        this._api('adminListSessions').then(function(sessions) {
            self._sessions = sessions || [];
            self.renderSessions();
        }).catch(function(err) {
            if (el) el.innerHTML = '<div class="admin-empty">Ошибка: ' + (err.message || err) + '</div>';
        });
    },

    loadLogs: function() {
        const el = document.getElementById('adminLogsList');
        if (el) el.innerHTML = '<div class="admin-empty">Загрузка…</div>';
        const self = this;
        this._api('adminListLogs', { limit: 200 }).then(function(logs) {
            self._logs = logs || [];
            self.renderLogs();
        }).catch(function(err) {
            if (el) el.innerHTML = '<div class="admin-empty">Ошибка: ' + (err.message || err) + '</div>';
        });
    },

    loadStats: function() {
        const el = document.getElementById('adminStatsContainer');
        if (el) el.innerHTML = '<div class="admin-empty">Загрузка…</div>';
        const self = this;
        // Параллельно грузим users и sessions.
        Promise.all([
            this._api('adminListUsers'),
            this._api('adminListSessions')
        ]).then(function(results) {
            self._users = results[0] || [];
            self._sessions = results[1] || [];
            self.renderStats();
        }).catch(function(err) {
            if (el) el.innerHTML = '<div class="admin-empty">Ошибка: ' + (err.message || err) + '</div>';
        });
    },

    refreshAll: function() {
        this._users = null;
        this._sessions = null;
        this._logs = null;
        this.loadUsers();
        this.loadSessions();
        this.loadLogs();
        if (typeof showToast === 'function') showToast('Данные обновляются…');
    },

    // ============================================================
    // Рендер: Пользователи.
    // ============================================================
    renderUsers: function() {
        const el = document.getElementById('adminUsersList');
        if (!el) return;
        if (!this._users) { el.innerHTML = '<div class="admin-empty">Загрузка…</div>'; return; }

        const search = (document.getElementById('adminUserSearch').value || '').toLowerCase().trim();
        let users = this._users.slice();
        if (search) {
            users = users.filter(function(u) {
                return (u.email || '').toLowerCase().indexOf(search) !== -1
                    || (u.role || '').toLowerCase().indexOf(search) !== -1;
            });
        }
        // Сортировка: сначала Админ, потом по email.
        users.sort(function(a, b) {
            if (a.role === 'Админ' && b.role !== 'Админ') return -1;
            if (b.role === 'Админ' && a.role !== 'Админ') return 1;
            return (a.email || '').localeCompare(b.email || '');
        });

        if (users.length === 0) {
            el.innerHTML = '<div class="admin-empty">Пользователи не найдены</div>';
            return;
        }

        const self = this;
        el.innerHTML = users.map(function(u) {
            const online = u.login_status === 'вход выполнен';
            const statusBadge = online
                ? '<span class="admin-badge admin-badge-online">Вход выполнен</span>'
                : '<span class="admin-badge admin-badge-offline">Вход не выполнен</span>';
            const last = u.last_login
                ? self._formatDate(u.last_login)
                : '—';
            // Select смены роли.
            const options = self.ROLES.map(function(r) {
                return '<option value="' + r + '"' + (r === u.role ? ' selected' : '') + '>' + r + '</option>';
            }).join('');
            const roleSelect = '<select class="admin-role-select" onchange="KipAdmin.changeRole(' + u.id + ', this.value)">' + options + '</select>';
            // Кнопка "Сбросить вход" — только для залогиненных.
            const resetBtn = online
                ? '<button type="button" class="admin-action-btn" onclick="KipAdmin.resetLogin(' + u.id + ', \'' + self._esc(u.email) + '\')">Сбросить вход</button>'
                : '';

            return '' +
                '<div class="admin-item">' +
                    '<div class="admin-item-row">' +
                        '<div class="admin-item-email">' + self._esc(u.email) + '</div>' +
                        statusBadge +
                    '</div>' +
                    '<div class="admin-item-meta">' +
                        'ID: ' + u.id + ' · Последний вход: ' + last +
                    '</div>' +
                    '<div class="admin-item-actions">' +
                        roleSelect +
                        resetBtn +
                    '</div>' +
                '</div>';
        }).join('');
    },

    // ============================================================
    // Рендер: Сессии.
    // ============================================================
    renderSessions: function() {
        const el = document.getElementById('adminSessionsList');
        if (!el) return;
        if (!this._sessions) { el.innerHTML = '<div class="admin-empty">Загрузка…</div>'; return; }

        const search = (document.getElementById('adminSessionSearch').value || '').toLowerCase().trim();
        let sessions = this._sessions.slice();
        if (search) {
            sessions = sessions.filter(function(s) {
                return (s.email || '').toLowerCase().indexOf(search) !== -1
                    || (s.role || '').toLowerCase().indexOf(search) !== -1;
            });
        }
        // Сортировка: по убыванию last_heartbeat.
        sessions.sort(function(a, b) {
            const ta = a.last_heartbeat ? new Date(a.last_heartbeat).getTime() : 0;
            const tb = b.last_heartbeat ? new Date(b.last_heartbeat).getTime() : 0;
            return tb - ta;
        });

        if (sessions.length === 0) {
            el.innerHTML = '<div class="admin-empty">Активных сессий нет</div>';
            return;
        }

        const self = this;
        el.innerHTML = sessions.map(function(s) {
            const created = s.created_at ? self._formatDate(s.created_at) : '—';
            const last = s.last_heartbeat ? self._formatDate(s.last_heartbeat) : '—';
            return '' +
                '<div class="admin-item">' +
                    '<div class="admin-item-row">' +
                        '<div class="admin-item-email">' + self._esc(s.email) + '</div>' +
                        '<span class="admin-badge admin-badge-role">' + self._esc(s.role || '—') + '</span>' +
                    '</div>' +
                    '<div class="admin-item-meta">' +
                        'Создана: ' + created + '<br>' +
                        'Активность: ' + last + '<br>' +
                        'Токен: ' + self._esc(s.token || '—') +
                    '</div>' +
                '</div>';
        }).join('');
    },

    // ============================================================
    // Рендер: Журнал.
    // ============================================================
    renderLogs: function() {
        const el = document.getElementById('adminLogsList');
        if (!el) return;
        if (!this._logs) { el.innerHTML = '<div class="admin-empty">Загрузка…</div>'; return; }

        const search = (document.getElementById('adminLogSearch').value || '').toLowerCase().trim();
        const filter = (document.getElementById('adminLogFilter') || {}).value || '';
        let logs = this._logs.slice();
        if (search) {
            logs = logs.filter(function(l) {
                return (l.email || '').toLowerCase().indexOf(search) !== -1
                    || (l.action || '').toLowerCase().indexOf(search) !== -1
                    || (l.details || '').toLowerCase().indexOf(search) !== -1;
            });
        }
        if (filter) {
            logs = logs.filter(function(l) { return l.action === filter; });
        }

        if (logs.length === 0) {
            el.innerHTML = '<div class="admin-empty">Записей не найдено</div>';
            return;
        }

        const self = this;
        el.innerHTML = logs.map(function(l) {
            const ts = l.timestamp ? self._formatDate(l.timestamp) : '—';
            const actionClass = self._actionBadgeClass(l.action);
            return '' +
                '<div class="admin-item">' +
                    '<div class="admin-item-row">' +
                        '<div class="admin-item-email">' + self._esc(l.email || '—') + '</div>' +
                        '<span class="admin-badge ' + actionClass + '">' + self._esc(l.action || '—') + '</span>' +
                    '</div>' +
                    '<div class="admin-item-meta">' +
                        ts + (l.ip ? ' · IP: ' + self._esc(l.ip) : '') +
                        (l.details ? '<br>' + self._esc(l.details) : '') +
                    '</div>' +
                '</div>';
        }).join('');
    },

    // ============================================================
    // Рендер: Статистика.
    // ============================================================
    renderStats: function() {
        const el = document.getElementById('adminStatsContainer');
        if (!el) return;
        if (!this._users || !this._sessions) {
            el.innerHTML = '<div class="admin-empty">Загрузка…</div>';
            return;
        }

        const users = this._users;
        const sessions = this._sessions;
        const total = users.length;
        const online = users.filter(function(u) { return u.login_status === 'вход выполнен'; }).length;
        const activeSessions = sessions.length;
        const admins = users.filter(function(u) { return u.role === 'Админ'; }).length;

        // Входы за сегодня.
        const today = new Date(); today.setHours(0, 0, 0, 0);
        const todayLogins = users.filter(function(u) {
            if (!u.last_login) return false;
            return new Date(u.last_login) >= today;
        }).length;

        // Распределение по ролям.
        const byRole = {};
        users.forEach(function(u) {
            const r = u.role || '—';
            byRole[r] = (byRole[r] || 0) + 1;
        });
        const roleBreakdown = Object.keys(byRole)
            .sort(function(a, b) { return byRole[b] - byRole[a]; })
            .map(function(r) {
                return '<div><span>' + this._esc(r) + '</span><span>' + byRole[r] + '</span></div>';
            }.bind(this))
            .join('');

        el.innerHTML = '' +
            '<div class="admin-stat-card">' +
                '<div class="admin-stat-value">' + total + '</div>' +
                '<div class="admin-stat-label">Всего пользователей</div>' +
            '</div>' +
            '<div class="admin-stat-card">' +
                '<div class="admin-stat-value">' + online + '</div>' +
                '<div class="admin-stat-label">С входом выполнен</div>' +
            '</div>' +
            '<div class="admin-stat-card">' +
                '<div class="admin-stat-value">' + activeSessions + '</div>' +
                '<div class="admin-stat-label">Активных сессий</div>' +
            '</div>' +
            '<div class="admin-stat-card">' +
                '<div class="admin-stat-value">' + todayLogins + '</div>' +
                '<div class="admin-stat-label">Входов сегодня</div>' +
            '</div>' +
            '<div class="admin-stat-card full-width">' +
                '<div class="admin-stat-label">Распределение по ролям</div>' +
                '<div class="admin-stat-breakdown">' + roleBreakdown + '</div>' +
            '</div>' +
            '<div class="admin-stat-card full-width">' +
                '<div class="admin-stat-label">Админов в системе</div>' +
                '<div class="admin-stat-value" style="font-size:22px;margin-top:6px;">' + admins + '</div>' +
            '</div>';
    },

    // ============================================================
    // Действия.
    // ============================================================

    // Сменить роль пользователя.
    // Согласно выбранной логике: сразу + reset сессий.
    // Поэтому после updateRole вызываем resetLogin (если был вход выполнен).
    changeRole: function(userId, newRole) {
        const self = this;
        const user = (this._users || []).find(function(u) { return Number(u.id) === Number(userId); });
        const oldRole = user ? user.role : '?';
        const email = user ? user.email : '';

        // Найти текущий select, чтобы вернуть значение, если операция провалится.
        const selects = document.querySelectorAll('.admin-role-select');
        let targetSelect = null;
        for (let i = 0; i < selects.length; i++) {
            if (Number(selects[i].value) === Number(userId) || selects[i].value === newRole) {
                // Грубый поиск: по onchange мы знаем, что select только что изменился.
            }
        }

        this._api('adminUpdateRole', { userId: userId, newRole: newRole }).then(function() {
            // Если у пользователя был выполнен вход — сбрасываем его сессии,
            // чтобы при следующем входе он получил новую роль.
            if (user && user.login_status === 'вход выполнен') {
                return self._api('adminResetLogin', { userId: userId }).then(function() {
                    if (typeof showToast === 'function') {
                        showToast('Роль изменена: ' + oldRole + ' → ' + newRole + '. Сессии сброшены.');
                    }
                });
            }
            if (typeof showToast === 'function') {
                showToast('Роль изменена: ' + oldRole + ' → ' + newRole);
            }
        }).then(function() {
            // Перезагрузить списки пользователей и сессий.
            self.loadUsers();
            self.loadSessions();
        }).catch(function(err) {
            if (typeof showToast === 'function') {
                showToast('Ошибка: ' + (err.message || err));
            }
            // Вернуть select на старое значение.
            if (user) {
                document.querySelectorAll('.admin-role-select').forEach(function(sel) {
                    // Найти нужный select по id пользователя — но у нас нет data-attr.
                    // Простой fallback: перерендерить весь список.
                });
            }
            self.renderUsers();
        });
    },

    // Сбросить вход пользователя (force logout).
    resetLogin: function(userId, email) {
        const self = this;
        this._api('adminResetLogin', { userId: userId }).then(function() {
            if (typeof showToast === 'function') {
                showToast('Вход сброшен: ' + (email || ''));
            }
            self.loadUsers();
            self.loadSessions();
        }).catch(function(err) {
            if (typeof showToast === 'function') {
                showToast('Ошибка: ' + (err.message || err));
            }
        });
    },

    // ============================================================
    // Создание нового пользователя.
    // ============================================================

    // Открыть модалку создания пользователя.
    // Заполняет <select> ролями и ставит «Общий доступ» по умолчанию.
    openCreateUser: function() {
        const overlay = document.getElementById('createUserOverlay');
        if (!overlay) return;

        // Заполнить select ролями.
        const sel = document.getElementById('createUserRole');
        if (sel) {
            sel.innerHTML = this.ROLES.map(function(r) {
                return '<option value="' + r + '">' + r + '</option>';
            }).join('');
            // По умолчанию — «Общий доступ» (минимальные права).
            sel.value = 'Общий доступ';
        }
        // Очистить поля.
        const emailInput = document.getElementById('createUserEmail');
        if (emailInput) emailInput.value = '';
        const errEl = document.getElementById('createUserError');
        if (errEl) errEl.textContent = '';
        const btn = document.getElementById('createUserBtn');
        if (btn) { btn.disabled = false; btn.textContent = 'Создать пользователя'; }

        overlay.classList.add('active');
        // Фокус на поле email после анимации.
        setTimeout(function() { if (emailInput) emailInput.focus(); }, 150);
    },

    // Закрыть модалку создания пользователя.
    closeCreateUser: function() {
        const overlay = document.getElementById('createUserOverlay');
        if (overlay) overlay.classList.remove('active');
    },

    // Отправить запрос на создание пользователя.
    createUser: function() {
        const emailInput = document.getElementById('createUserEmail');
        const roleSel = document.getElementById('createUserRole');
        const errEl = document.getElementById('createUserError');
        const btn = document.getElementById('createUserBtn');
        if (!emailInput || !roleSel) return;

        const email = (emailInput.value || '').trim().toLowerCase();
        const role = roleSel.value;

        // Клиентская валидация email (двойная: сервер тоже проверит).
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            if (errEl) errEl.textContent = 'Введите корректный email';
            return;
        }

        if (errEl) errEl.textContent = '';
        if (btn) { btn.disabled = true; btn.textContent = 'Создание…'; }

        const self = this;
        this._api('adminCreateUser', { email: email, role: role }).then(function() {
            if (typeof showToast === 'function') {
                showToast('Пользователь создан: ' + email + ' (' + role + ')');
            }
            self.closeCreateUser();
            // Перезагрузить список, чтобы новый пользователь появился.
            self.loadUsers();
        }).catch(function(err) {
            if (errEl) errEl.textContent = err.message || String(err);
            if (btn) { btn.disabled = false; btn.textContent = 'Создать пользователя'; }
        });
    },

    // ============================================================
    // Утилиты.
    // ============================================================

    // Экранирование HTML — защита от XSS при вставке email/details.
    _esc: function(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    // Форматирование даты.
    _formatDate: function(d) {
        if (!d) return '—';
        try {
            const date = (d instanceof Date) ? d : new Date(d);
            if (isNaN(date.getTime())) return '—';
            const pad = function(n) { return (n < 10 ? '0' : '') + n; };
            return pad(date.getDate()) + '.' + pad(date.getMonth() + 1) + '.' + date.getFullYear() +
                ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes());
        } catch (e) {
            return '—';
        }
    },

    // Класс бейджа для типа действия в журнале.
    _actionBadgeClass: function(action) {
        if (!action) return 'admin-badge admin-badge-offline';
        if (action.indexOf('ADMIN_') === 0) return 'admin-badge admin-badge-action';
        if (action === 'LOGIN_SUCCESS' || action === 'OTP_VERIFIED') return 'admin-badge admin-badge-online';
        if (action === 'LOGIN_FAILED' || action === 'ADMIN_ACCESS_DENIED') return 'admin-badge admin-badge-danger';
        if (action === 'LOGOUT') return 'admin-badge admin-badge-offline';
        return 'admin-badge admin-badge-role';
    }
};

// ============================================================
// Обработка OTP input: автопереход между полями + paste.
// ============================================================
(function setupOtpInputs() {
    function setup() {
        ['otp1','otp2','otp3','otp4','otp5','otp6'].forEach(function(id, i) {
            const input = document.getElementById(id);
            if (!input) return;
            input.addEventListener('input', function(e) {
                const v = e.target.value.replace(/\D/g, '');
                e.target.value = v;
                if (v) {
                    e.target.classList.add('filled');
                    if (i < 5) document.getElementById('otp' + (i+2)).focus();
                    else {
                        // Последнее поле — автопроверка через 200 мс.
                        setTimeout(function() { KipAuth.verifyOTP(); }, 200);
                    }
                } else {
                    e.target.classList.remove('filled');
                }
            });
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && !e.target.value && i > 0) {
                    document.getElementById('otp' + i).focus();
                }
                if (e.key === 'Enter') {
                    KipAuth.verifyOTP();
                }
            });
            input.addEventListener('paste', function(e) {
                e.preventDefault();
                const text = (e.clipboardData || window.clipboardData).getData('text');
                const digits = text.replace(/\D/g, '').substring(0, 6);
                for (let j = 0; j < 6; j++) {
                    const el = document.getElementById('otp' + (j+1));
                    if (el) {
                        el.value = digits[j] || '';
                        if (digits[j]) el.classList.add('filled');
                        else el.classList.remove('filled');
                    }
                }
                if (digits.length === 6) {
                    setTimeout(function() { KipAuth.verifyOTP(); }, 200);
                }
            });
        });

        // Enter в поле email — отправить OTP.
        const emailInput = document.getElementById('authEmail');
        if (emailInput) {
            emailInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') KipAuth.sendOTP();
            });
        }

        // Enter в поле email модалки создания пользователя — создать.
        const createUserEmail = document.getElementById('createUserEmail');
        if (createUserEmail) {
            createUserEmail.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') KipAdmin.createUser();
            });
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();

// ===== Window bridge (for inline HTML event handlers) =====
window.KipAdmin = KipAdmin;

export { KipAdmin };
export default KipAdmin;
