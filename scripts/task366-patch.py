#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 366 — расходомеры, 2 замечания пользователя:
#   (1) баннер недоставленных показаний: «замени на более информативное
#       и просто читаемое сообщение и без иконки» — текст с НОМЕРАМИ
#       расходомеров (№2, №4; у одного несколько записей — «№2 ×2»),
#       нормальная грамматика ед/мн числа, иконка ⟳ убрана;
#   (2) дубль задания client-хардening: server_busy (замок архива
#       Task 366 на сервере) — ПОВТОРЯЕМАЯ ошибка, запись outbox
#       не должна удаляться (иначе период-запись терялась бы при
#       таймауте замка).
# Правки index.html (5 зон). Серверная часть — FlowmeterArchive.gs
# (дедуп + замок) отдельными правками в этом же скрипте.
import sys

P = '/home/z/my-project/kip8test/index.html'
html = open(P, encoding='utf-8').read()
orig = html

def rep(old, new, n=1, tag=''):
    global html
    cnt = html.count(old)
    if cnt != n:
        print('ОШИБКА [%s]: найдено %d, ожидалось %d' % (tag, cnt, n))
        sys.exit(1)
    html = html.replace(old, new)
    print('[ok] %s (%d зам.)' % (tag, cnt))

# --- 1. CSS: комментарий + удаление правила иконки ---
rep(
"""    /* Task 358: баннер «ждут отправки» — показания введены, но ещё
       не доставлены на сервер (нет связи); уйдут автоматически */
    .flow-outbox-banner {
        display: flex; align-items: center; gap: 8px;
        margin: 8px 14px 4px; padding: 10px 12px;
        border-radius: 8px;
        background: rgba(230,150,20,0.10);
        border: 1px solid rgba(230,150,20,0.32);
        font-size: 13px; line-height: 1.35;
        color: var(--text-primary);
    }
    .flow-outbox-ico {
        font-size: 16px; line-height: 1;
        color: #e69614; flex: 0 0 auto;
    }
""",
"""    /* Task 358: баннер «ждут отправки» — показания введены, но ещё
       не доставлены на сервер (нет связи); уйдут автоматически.
       Task 366: без иконки (заявка), текст с номерами расходомеров. */
    .flow-outbox-banner {
        display: flex; align-items: center; gap: 8px;
        margin: 8px 14px 4px; padding: 10px 12px;
        border-radius: 8px;
        background: rgba(230,150,20,0.10);
        border: 1px solid rgba(230,150,20,0.32);
        font-size: 13px; line-height: 1.35;
        color: var(--text-primary);
    }
""", 1, 'CSS: правило иконки удалено')

# --- 2. renderList: баннер через _outboxBannerText, без иконки ---
rep(
"""            var html = '';
            // Task 358: честный индикатор — N показаний ещё НЕ на
            // сервере (нет связи в прошлой сессии); уйдут автоматически.
            // Пользователь должен ЗНАТЬ, что введённое не доставлено.
            var outboxN = 0;
            try { outboxN = this._outboxCount(); } catch (e) { outboxN = 0; }
            if (outboxN > 0) {
                html += '<div class="flow-outbox-banner">' +
                    '<span class="flow-outbox-ico">⟳</span>' +
                    '<span>Показаний ждут отправки: ' + outboxN +
                    ' — уйдут на сервер автоматически при восстановлении связи</span>' +
                    '</div>';
            }
""",
"""            var html = '';
            // Task 358: честный индикатор — показания ещё НЕ на сервере
            // (нет связи в прошлой сессии); уйдут автоматически.
            // Пользователь должен ЗНАТЬ, что введённое не доставлено.
            // Task 366: текст с НОМЕРАМИ расходомеров, без иконки
            // (заявка: «более информативное и просто читаемое»).
            var outboxEntries = [];
            try { outboxEntries = this._outboxLoad(); } catch (e) { outboxEntries = []; }
            var outboxBanner = (outboxEntries.length > 0)
                ? this._outboxBannerText(outboxEntries) : null;
            if (outboxBanner) {
                html += '<div class="flow-outbox-banner">' +
                    '<span>' + this._esc(outboxBanner) + '</span>' +
                    '</div>';
            }
""", 1, 'renderList: баннер по хелперу')

# --- 3. helper _outboxBannerText после _outboxCount ---
rep(
"""        _outboxCount: function() {
            return this._outboxLoad().length;
        },
""",
"""        _outboxCount: function() {
            return this._outboxLoad().length;
        },

        // Task 366: текст баннера недоставленных показаний (заявка:
        // «замени на более информативное и просто читаемое сообщение
        // и без иконки»). Было: «⟳ Показаний ждут отправки: N — уйдут
        // на сервер при восстановлении связи» — видно количество, но
        // не видно, ЧЬИ показания не ушли. Теперь: номера расходомеров
        // (у одного может быть несколько записей — «№2 ×2»), обычная
        // грамматика ед./мн. числа, иконки нет. null — записей нет,
        // баннер не показывается.
        _outboxBannerText: function(entries) {
            if (!Array.isArray(entries) || entries.length === 0) return null;
            var order = [], counts = {};
            for (var i = 0; i < entries.length; i++) {
                var pid = ((entries[i] || {}).payload || {}).id;
                var key = (pid === undefined || pid === null || pid === '') ? '' : String(pid);
                if (key === '') continue;
                if (!counts[key]) { counts[key] = 0; order.push(key); }
                counts[key]++;
            }
            if (order.length === 0) {
                // страховка: номера не извлеклись (не должно случаться) —
                // текст по счётчику, чтобы пользователь всё равно ЗНАЛ,
                // что введённое не доставлено (суть Task 358)
                return (entries.length === 1)
                    ? 'Показание не отправлено — отправится на сервер автоматически при восстановлении связи'
                    : 'Показания (' + entries.length + ') не отправлены — отправятся на сервер автоматически при восстановлении связи';
            }
            var parts = [];
            for (var j = 0; j < order.length; j++) {
                var part = '№' + order[j];
                if (counts[order[j]] > 1) part += ' ×' + counts[order[j]];
                parts.push(part);
            }
            var list = parts.join(', ');
            if (entries.length === 1) {
                return 'Показание ' + list + ' не отправлено — отправится на сервер автоматически при восстановлении связи';
            }
            return 'Показания ' + list + ' не отправлены — отправятся на сервер автоматически при восстановлении связи';
        },
""", 1, 'helper _outboxBannerText')

# --- 4. server_busy — повторяемая ошибка (замок архива Task 366) ---
rep(
"""        _outboxIsPermanentError: function(err) {
            if (!err) return false;
            if (err._kind !== 'SERVER') return false;
            var msg = String(err.message || err.error || err);
            if (/session|токен|token/i.test(msg)) return false;      // лечится входом
            if (/unknown action/i.test(msg)) return false;           // лечится апгрейдом сервера
            return true;  // edit_window_expired / not_your_input / sign_neg / ...
        },
""",
"""        _outboxIsPermanentError: function(err) {
            if (!err) return false;
            if (err._kind !== 'SERVER') return false;
            var msg = String(err.message || err.error || err);
            if (/session|токен|token/i.test(msg)) return false;      // лечится входом
            if (/unknown action/i.test(msg)) return false;           // лечится апгрейдом сервера
            if (/server_busy/i.test(msg)) return false;             // Task 366: замок архива занят — ретрай позже
            return true;  // edit_window_expired / not_your_input / sign_neg / ...
        },
""", 1, 'server_busy повторяем')

# --- 5. комментарий секции outbox: дедуп на сервере тоже (Task 366) ---
rep(
"""        // Дедуп обязателен: сервер пишет архив appendRow'ом без проверки
        // дублей — бездумный повтор создал бы дубликат в архиве. Перед
        // повтором сверяемся с фактом: 'day' — meters-строка
        // (flowmeter.list), 'period' — архив (flowmeter.archive).
""",
"""        // Дедуп обязателен: повтор может создать дубликат в архиве.
        // Перед повтором сверяемся с фактом: 'day' — meters-строка
        // (flowmeter.list), 'period' — архив (flowmeter.archive).
        // Task 366: СЕРВЕР тоже дедупит (FlowmeterArchive.gs — ключ
        // meterId+prev+curr+dateCurr+entryType под Utils.withLock):
        // ретрай, beacon «последнего шанса» рядом с живым fetch'ем и
        // два окна приложения больше не создают дубль строки архива.
""", 1, 'комментарий секции outbox')

open(P, 'w', encoding='utf-8').write(html)
print('index.html: %d правок, +%d/-%d строк' % (5, html.count(chr(10)) - orig.count(chr(10)), 0))

# Контроль: старых следов нет, новые на месте
assert 'flow-outbox-ico' not in html, 'иконка ещё в рендере/CSS'
assert '⟳' not in html[html.index('.flow-outbox-banner'):html.index('.flow-outbox-banner') + 1200], '⟳ в зоне баннера'
assert "'Показаний ждут отправки" not in html, 'рендерный старый текст жив (цитата в комментарии хелпера — намеренно)'
assert html.count('_outboxBannerText') == 2, 'helper: определение + вызов'
print('Контроль пройден: иконки/старого текста нет, helper на месте')
