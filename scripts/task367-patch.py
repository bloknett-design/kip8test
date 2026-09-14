#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 367 (kip8test): расходомеры — заявка пользователя:
#   1) «По баннеру недоставленных показаний, упростим ещё, убери
#      появление баннера вовсе» — баннер (Tasks 358/366) удаляется;
#   2) «сделай цвет шрифта значений в списке карточек расходомеров
#      желто-оранжевым когда возникает такая ситуация, и после
#      успешной передачи данных на сервер, снова зелёным» — класс
#      .flow-summary-val-pending (#f5a623 тёмная / #c96e00 светлая),
#      приоритет над красным «пора вводить» (ввод уже состоялся);
#      перерендер после _outboxAdd (обе ветки ввода) и в finish()
#      флаша (доставка → зелёный);
#   3) «к расходомерам еженедельным и месячным тоже примени правило
#      изменения цвета на красный, только не по суткам а по
#      календарным недели и месяцу» — поведение Task 357 уже такое
#      (пн–вс / календарный месяц), здесь оно ЗАКРЕПЛЕНО комментарием
#      и укреплено распознавание периода (регэкспы ловят сокращения
#      «Еженед.»/«Ежемес.» и «N раз в неделю/месяц» — раньше считались
#      суточными и краснели по суткам).
# Запуск из корня репо kip8test.
import io

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()

def patch(title, old, new, expect=1):
    global src
    n = src.count(old)
    assert n == expect, ('%s: найдено %d вхождений (ожидалось %d)' % (title, n, expect))
    src = src.replace(old, new)
    print('OK  %s' % title)

# ---------------------------------------------------------------
# 1. CSS: баннер удалён (комментарий-маркер Task 367 на его месте)
# ---------------------------------------------------------------
patch('CSS: удалён блок .flow-outbox-banner',
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
""",
"""    /* Task 367: баннер недоставленных показаний УБРАН (заявка:
       «упростить ещё — баннер вовсе»); недоставленные показания
       видны ЦВЕТОМ ЗНАЧЕНИЯ карточки — жёлто-оранжевый
       .flow-summary-val-pending (ниже, рядом с flow-summary-val). */
""")

# ---------------------------------------------------------------
# 2. CSS: класс жёлто-оранжевых значений + комментарий о приоритете
# ---------------------------------------------------------------
patch('CSS: комментарий Task 367 в блоке «пора вводить»',
"""       Task 365 (поправка заявки): красный — НЕ час: с 6:00 новых
       суток (следующих за сутками ввода данных) показания держатся
       красными, пока не введут новые данные; окна 6:00–7:00 нет. */
""",
"""       Task 365 (поправка заявки): красный — НЕ час: с 6:00 новых
       суток (следующих за сутками ввода данных) показания держатся
       красными, пока не введут новые данные; окна 6:00–7:00 нет.
       Task 367 (заявка): НЕдоставленные показания — жёлто-оранжевый
       цвет значения (приоритет НАД красным — ввод уже состоялся);
       после доставки сервером — снова зелёный. Недельные/месячные —
       красный по календарной неделе пн–вс / месяцу (Task 357). */
""")

patch('CSS: .flow-summary-val-pending (жёлто-оранжевый, тёмная+светлая)',
"""    [data-theme="light"] .flow-summary-val.flow-summary-val-due { color: #e8230a; font-size: 18px; font-weight: 800; }
    .flow-summary-days""",
"""    [data-theme="light"] .flow-summary-val.flow-summary-val-due { color: #e8230a; font-size: 18px; font-weight: 800; }
    /* Task 367: показания введены, но ещё НЕ доставлены на сервер
       (нет связи; запись ждёт в outbox). Только ЦВЕТ — размер/вес
       шрифта как у обычного зелёного значения. После доставки
       (флаш/online) renderList пересчитает класс — снова зелёный. */
    .flow-summary-val.flow-summary-val-pending {
        color: #f5a623;
    }
    [data-theme="light"] .flow-summary-val.flow-summary-val-pending { color: #c96e00; }
    .flow-summary-days""")

# ---------------------------------------------------------------
# 3. _isOverdue: закрепление календарной недели/месяца + регэкспы
# ---------------------------------------------------------------
patch('_isOverdue: регэкспы периодов (сокращения/«N раз в …»)',
"""            var period = String(m.period || '').toLowerCase();
            if (period.indexOf('недел') !== -1) {
                // Еженедельно: календарная неделя данных прошла (неделя пн–вс)
                return this._mondayOf(d) < this._mondayOf(n);
            }
            if (period.indexOf('месяч') !== -1) {
                // Ежемесячно: календарный месяц данных прошёл
                return (d.getFullYear() * 12 + d.getMonth()) < (n.getFullYear() * 12 + n.getMonth());
            }
""",
"""            // Task 367 (заявка): недельные — красный по КАЛЕНДАРНОЙ
            // неделе (пн–вс), месячные — по календарному месяцу
            // (поведение Task 357 подтверждено пользователем).
            // Распознавание периода укреплено: сокращения («Еженед.»,
            // «Ежемес.») и «N раз в неделю/месяц» из таблицы попадают
            // в свою ветку, а не считаются суточными.
            var period = String(m.period || '').toLowerCase();
            if (/недел|еженед/.test(period)) {
                // Еженедельно: календарная неделя данных прошла (неделя пн–вс)
                return this._mondayOf(d) < this._mondayOf(n);
            }
            if (/месяц|месяч|ежемес/.test(period)) {
                // Ежемесячно: календарный месяц данных прошёл
                return (d.getFullYear() * 12 + d.getMonth()) < (n.getFullYear() * 12 + n.getMonth());
            }
""")

# ---------------------------------------------------------------
# 4. renderList: баннер → множество pendingIds
# ---------------------------------------------------------------
patch('renderList: блок баннера заменён на pendingIds',
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
""",
"""            var html = '';
            // Task 367 (заявка: «упростить ещё — баннер убрать вовсе»):
            // недоставленные показания видны ЦВЕТОМ ЗНАЧЕНИЯ карточки —
            // жёлто-оранжевый .flow-summary-val-pending (вместо баннера
            // над списком, Tasks 358/366). Собираем номера расходомеров,
            // у которых в outbox ещё есть записи (state любой — всё,
            // что не доставлено и не отменено пользователем).
            var pendingIds = {};
            try {
                var outboxEntries = this._outboxLoad();
                for (var oi = 0; oi < outboxEntries.length; oi++) {
                    var pid = ((outboxEntries[oi] || {}).payload || {}).id;
                    if (pid !== undefined && pid !== null && pid !== '') {
                        pendingIds[String(pid)] = true;
                    }
                }
            } catch (e) { /* outbox недоступен — обычные цвета */ }
""")

# ---------------------------------------------------------------
# 5. renderList: класс значения — pending приоритетнее due
# ---------------------------------------------------------------
patch('renderList: класс значения (жёлто-оранжевый приоритетнее красного)',
"""                // Task 348: красный цвет показаний — «пора вводить новые
                // данные» (6:00 / прошедшая неделя / прошедший месяц)
                html += '<span class="flow-summary-val' + (this._isOverdue(m, null) ? ' flow-summary-val-due' : '') + '">' + this._fmtNum(m.curr) + ' ' + this._esc(m.unit) + '</span>';
""",
"""                // Task 348: красный цвет показаний — «пора вводить новые
                // данные» (6:00 / прошедшая неделя / прошедший месяц).
                // Task 367: недоставленные (outbox) — жёлто-оранжевый,
                // приоритет НАД красным: ввод уже состоялся, «пора
                // вводить» до доставки врало бы; после доставки цвет
                // пересчитается (зелёный; красный вернётся лишь для
                // действительно устаревших данных).
                var valCls = 'flow-summary-val';
                if (pendingIds[String(m.id)]) valCls += ' flow-summary-val-pending';
                else if (this._isOverdue(m, null)) valCls += ' flow-summary-val-due';
                html += '<span class="' + valCls + '">' + this._fmtNum(m.curr) + ' ' + this._esc(m.unit) + '</span>';
""")

# ---------------------------------------------------------------
# 6. Ввод суточных: перерендер после записи в outbox
# ---------------------------------------------------------------
patch('submitInput (день): renderList после _outboxAdd',
"""                this._outboxAdd({
                    cid: outboxCid,
                    kind: 'day',
                    payload: apiPayload,
                    isEdit: isEdit,
                    ts: Date.now(),
                    state: 'pending'
                });
""",
"""                this._outboxAdd({
                    cid: outboxCid,
                    kind: 'day',
                    payload: apiPayload,
                    isEdit: isEdit,
                    ts: Date.now(),
                    state: 'pending'
                });
                // Task 367: значение карточки — жёлто-оранжевое, пока
                // показание не доставлено (рендер выше успевал показать
                // зелёный ДО записи в outbox)
                this.renderList();
""")

# ---------------------------------------------------------------
# 7. Ввод за период: перерендер после записи в outbox
# ---------------------------------------------------------------
patch('_submitPeriodEntry: renderList после _outboxAdd',
"""            this._outboxAdd({
                cid: outboxCid,
                kind: 'period',
                payload: apiPayload,
                isEdit: false,
                ts: Date.now(),
                state: 'pending'
            });
""",
"""            this._outboxAdd({
                cid: outboxCid,
                kind: 'period',
                payload: apiPayload,
                isEdit: false,
                ts: Date.now(),
                state: 'pending'
            });
            // Task 367: значение карточки — жёлто-оранжевое до доставки
            this.renderList();
""")

# ---------------------------------------------------------------
# 8. Флаш: доставка → пересчитать цвета карточек
# ---------------------------------------------------------------
patch('_flushOutbox: renderList в finish()',
"""            var finish = function(sent) {
                self._outboxFlushing = false;
                if (sent > 0) {
""",
"""            var finish = function(sent) {
                self._outboxFlushing = false;
                // Task 367: записи ушли/вычищены дедупом — цвета
                // значений карточек пересчитать (жёлто-оранжевый →
                // зелёный/красный)
                try { self.renderList(); } catch (e) { /* ignore */ }
                if (sent > 0) {
""")

# ---------------------------------------------------------------
# 9. Удалён хелпер _outboxBannerText (баннера больше нет)
# ---------------------------------------------------------------
patch('удалён метод _outboxBannerText',
"""        // Task 366: текст баннера недоставленных показаний (заявка:
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
""",
"""        // Task 367: баннер недоставленных показаний убран по заявке
        // («упростить ещё — убрать баннер вовсе»); вместо него жёлто-
        // оранжевый цвет ЗНАЧЕНИЙ карточек — .flow-summary-val-pending
        // в renderList. Хелпер _outboxBannerText удалён вместе с ним.
""")

io.open(PATH, 'w', encoding='utf-8').write(src)

# Контроль: следов баннера не осталось (упоминание в комментарии
# Task 367 о самом удалении — допустимо)
assert 'flow-outbox-banner' not in src, 'остался класс flow-outbox-banner'
assert '_outboxBannerText: function' not in src, 'осталось определение _outboxBannerText'
assert 'this._outboxBannerText(' not in src, 'остался вызов _outboxBannerText'
assert 'flow-summary-val-pending' in src, 'класс pending не добавлен'
assert src.count('.flow-summary-val.flow-summary-val-pending {') == 2, 'CSS pending: тёмная+светлая темы'
print('OK  контроль: баннер удалён полностью, pending-класс добавлен')
print('Патч Task 367 применён: %s' % PATH)
