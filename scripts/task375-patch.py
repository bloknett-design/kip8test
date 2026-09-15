# -*- coding: utf-8 -*-
# Task 375 — две заявки пользователя:
#   1) Печать табеля: «столбец со списком кодов расположить справа от
#      столбца списка мероприятий на расстоянии 10px» — зазор ряда
#      wsp-bottom 5mm → 10px (расположение справа уже сделано Task 364,
#      меняется ТОЛЬКО расстояние).
#   2) Хозрасчётные расходомеры: «при внесении новых данных иногда они
#      автоматически дублируются, нужно сделать больше упор в сторону
#      исключения случайных автоматических дублирований новых записей
#      по разным причинам (в момент ввода данных и в первый час после
#      ввода данных, когда доступно редактирование)».
#
# Анти-дубль (клиент, index.html):
#   №1 кулдаун повторного срабатывания «Сохранить» (2.5 c) — двойной
#      тап в анимацию закрытия sheet / Enter + клик; openInput сбрасывает;
#   №2 проверка «эти показания уже введены за эту дату» (состояние
#      meters в памяти) — блокирует и повторный вызов, и ручной повторный
#      ввод того же значения (раньше шёл второй строкой с расходом 0);
#   №3 та же проверка по outbox (запись ждёт доставки/подтверждения) —
#      второе окно приложения, двойной клик до ответа сервера;
#   №4 свёртка копий одного показания внутри outbox при флаше
#      (_outboxCollapseDuplicates: ключ id+dateCurr+curr+entryType,
#      prev намеренно НЕ в ключе — «двойной сдвиг» prev и есть мусор).
# Анти-дубль (сервер, справочная копия scripts/FlowmeterArchive.gs):
#   правило «окно 1 часа»: тот же meterId+curr+dateCurr+entryType,
#      записанный не более часа назад (O-таймштамп строки), — дубль
#      НЕЗАВИСИМО от prev (ловит «двойной сдвиг» от старых клиентов
#      и любых гонок; точный ключ Task 366 — правило 1 — сохранён).

import io, sys

def patch(path, repls):
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    for old, new, tag in repls:
        if src.count(old) != 1:
            print('FAIL [%s] anchor count=%d (ожидался 1): %r' % (tag, src.count(old), old[:80]))
            sys.exit(1)
        if old in new and new.count(old) != 1:
            # защита от самоподмены
            print('FAIL [%s] new contains old' % tag); sys.exit(1)
        src = src.replace(old, new)
        print('OK  [%s] +%d/-%d' % (tag, new.count('\n'), old.count('\n')))
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(src)

# ============================================================
# index.html — 9 правок
# ============================================================
INDEX = [
    # --- 1. CSS: зазор wsp-bottom 5mm → 10px ---
    ("""        #wsPrintSheet .wsp-bottom {
            display: flex;
            flex-direction: row;
            align-items: flex-start;
            gap: 5mm;
            margin-top: 2.5mm;
        }""",
     """        #wsPrintSheet .wsp-bottom {
            display: flex;
            flex-direction: row;
            align-items: flex-start;
            /* Task 375 (заявка: «на расстоянии 10px»): зазор между
               столбиком мероприятий и столбиком кодов — 10px */
            gap: 10px;
            margin-top: 2.5mm;
        }""",
     'css-gap-10px'),

    # --- 2. CSS-комментарий Task 364 → дополнение Task 375 ---
    ("""           Task 364 (заявка: «коды под графиком на печати размести
           в столбик справа от столбика мероприятий»): мероприятия
           и коды — ДВЕ КОЛОНКИ одного ряда под таблицей (обёртка
           wsp-bottom, flex-ряд: мероприятия слева, коды справа),
           каждая запись/код — по-прежнему отдельной строкой своего
           столбика; отступ сверху 2.5mm перенесён на обёртку */""",
     """           Task 364 (заявка: «коды под графиком на печати размести
           в столбик справа от столбика мероприятий»): мероприятия
           и коды — ДВЕ КОЛОНКИ одного ряда под таблицей (обёртка
           wsp-bottom, flex-ряд: мероприятия слева, коды справа),
           каждая запись/код — по-прежнему отдельной строкой своего
           столбика; отступ сверху 2.5mm перенесён на обёртку.
           Task 375: расстояние между столбиками — ровно 10px */""",
     'css-comment-375'),

    # --- 3. submitInput: кулдаун повторного срабатывания ---
    ("""            var val = field.value.replace(/\\s/g, '').replace(',', '.');
            var num = parseFloat(val);
            if (isNaN(num)) {
                field.style.borderColor = '#e55';
                setTimeout(function() { field.style.borderColor = ''; }, 1500);
                return;
            }""",
     """            var val = field.value.replace(/\\s/g, '').replace(',', '.');
            var num = parseFloat(val);
            if (isNaN(num)) {
                field.style.borderColor = '#e55';
                setTimeout(function() { field.style.borderColor = ''; }, 1500);
                return;
            }

            // Task 375 (анти-дубль №1): защита от ПОВТОРНОГО срабатывания
            // «Сохранить» — двойной тап в момент анимации закрытия sheet
            // (0.3 c), Enter + клик, дрожь тача. Второй вызов успевал
            // сдвинуть prev→curr ЕЩЁ раз: второй payload с другим prev
            // проходил серверный дедуп Task 366 и дописывал строку-дубль
            // в архив. Кулдаун 2.5 c после ПРИНЯТОГО ввода (флаг ставится
            // ниже, перед оптимистичным обновлением); openInput() снимает.
            if (this._inputAcceptedAt &&
                (Date.now() - this._inputAcceptedAt) < 2500) {
                return;
            }""",
     'submit-cooldown'),

    # --- 4. submitInput: дубль-проверка + установка флага ---
    ("""            var id = window._flowDetailId;
            var self = this;

            // Оптимистичное обновление UI: сразу обновляем в памяти""",
     """            var id = window._flowDetailId;
            var self = this;

            // Task 375 (анти-дубль №2/№3): эти показания уже введены за
            // эту дату (в памяти — первый вызов уже обновил meter.curr)
            // или уже ждут доставки в outbox (второе окно, двойной клик
            // до ответа сервера). Повторный ввод ТОГО ЖЕ значения за ту
            // же дату раньше сдвигал prev→curr и дописывал мусорную
            // строку с расходом 0; правка значения — кнопкой «Изменить
            // показания» (окно 1 ч).
            if (this._isDuplicateReadingInput(id, num, dateStr, isEdit)) {
                this.closeInput();
                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('Эти показания уже введены за эту дату — для правки используйте «Изменить показания» (окно 1 час)');
                }
                return;
            }
            // Task 375 (анти-дубль №1): ввод принят — кулдаун активен
            this._inputAcceptedAt = Date.now();

            // Оптимистичное обновление UI: сразу обновляем в памяти""",
     'submit-dup-check'),

    # --- 5. новый метод _isDuplicateReadingInput (после closeInput) ---
    ("""            document.getElementById('flowInputOverlay').classList.remove('active');
            document.getElementById('flowInputSheet').classList.remove('active');
        },

        // Сохранить введённые показания""",
     """            document.getElementById('flowInputOverlay').classList.remove('active');
            document.getElementById('flowInputSheet').classList.remove('active');
        },

        // Task 375: проверка «эти показания уже введены/уже в очереди».
        // true — отправку заблокировать (дубль), false — новый ввод.
        // Ключ сравнения: id + curr + dateCurr (prev НАМЕРЕННО не входит:
        // повторный вызов «Сохранить» сдвигал prev, и именно такие
        // «двойные сдвиги» должны ловиться). Покрывает:
        //   • состояние в памяти (первый вызов уже обновил meter.curr,
        //     ответ сервера ещё не пришёл);
        //   • outbox (запись ждёт доставки/подтверждения аномалии —
        //     второй «Сохранить», второе окно приложения);
        //   • данные сервера после load() (пользователь вводит то же
        //     значение повторно, не заметив, что уже сохранил).
        // isEdit (правка в окне 1 ч) не блокируется: сервер обновляет
        // запись на месте (Task 359), дубля не создаёт.
        _isDuplicateReadingInput: function(id, num, dateStr, isEdit) {
            if (isEdit) return false;
            var meters = this._METERS || [];
            for (var i = 0; i < meters.length; i++) {
                if (String(meters[i].id) !== String(id)) continue;
                if (String(parseFloat(meters[i].curr || 0)) === String(num) &&
                    String(meters[i].dateCurr || '') === String(dateStr)) {
                    return true;
                }
            }
            var pending = this._outboxLoad();
            for (var p = 0; p < pending.length; p++) {
                var pl = (pending[p] && pending[p].payload) || {};
                if (String(pl.id) !== String(id)) continue;
                if (String(parseFloat(pl.curr || 0)) === String(num) &&
                    String(pl.dateCurr || '') === String(dateStr)) {
                    return true;
                }
            }
            return false;
        },

        // Сохранить введённые показания""",
     'method-is-dup-reading'),

    # --- 6. openInput: сброс кулдауна ---
    ("""        openInput: function(isEdit) {
            var id = window._flowDetailId;
            var m = null;""",
     """        openInput: function(isEdit) {
            // Task 375 (анти-дубль №1): осознанное новое открытие формы —
            // кулдаун повторного «Сохранить» снимается (быстрая смена
            // решения не блокируется; дубль по значению ловят №2/№3)
            this._inputAcceptedAt = 0;
            var id = window._flowDetailId;
            var m = null;""",
     'openinput-reset'),

    # --- 7. _submitPeriodEntry: флаг после проверок дат ---
    ("""            var self = this;
            this.closeInput();

            // Task 358: write-ahead — «расход за месяц» тоже фиксируем""",
     """            var self = this;
            // Task 375 (анти-дубль №1): ввод принят (даты прошли hard-
            // проверки) — кулдаун активен и для ветки «расход за месяц»
            this._inputAcceptedAt = Date.now();
            this.closeInput();

            // Task 358: write-ahead — «расход за месяц» тоже фиксируем""",
     'period-flag'),

    # --- 8. _flushOutbox: свёртка дублей до серверных дедупов ---
    ("""            var dayEntries = [], periodEntries = [];
            entries.forEach(function(e) {
                (e.kind === 'period' ? periodEntries : dayEntries).push(e);
            });""",
     """            var dayEntries = [], periodEntries = [];
            entries.forEach(function(e) {
                (e.kind === 'period' ? periodEntries : dayEntries).push(e);
            });

            // Task 375 (анти-дубль №4): свёртка копий одного показания
            // ВНУТРИ outbox — до серверных дедуп-запросов. Одно показание
            // (id + dateCurr + curr + entryType) должно уйти на сервер
            // ОДИН раз, каким бы ни был prev: повторный «Сохранить»
            // (двойной сдвиг prev), задвоение из второго окна, копии,
            // накопленные до клиентских защит Task 375. Оставляем
            // СТАРЕЙШУЮ запись (первая в очереди = реальные показания);
            // поздние копии (в т.ч. со сдвинутым prev) — мусор, убираем.
            entries = this._outboxCollapseDuplicates(entries);
            if (entries.length === 0) return Promise.resolve(0);""",
     'flush-collapse'),

    # --- 9. новый метод _outboxCollapseDuplicates (после _outboxCount) ---
    ("""        _outboxCount: function() {
            return this._outboxLoad().length;
        },""",
     """        _outboxCount: function() {
            return this._outboxLoad().length;
        },

        // Task 375: убрать копии одного показания из списка записей
        // outbox. Ключ: id + dateCurr + curr + entryType (prev НЕ входит
        // — «двойной сдвиг» prev и есть мусорная копия). Порядок
        // сохраняется (старейшие первыми); копии удаляются из журнала
        // на месте (_outboxRemove). Вызывается из _flushOutbox ДО
        // серверных дедуп-запросов — экономит и round-trip'ы.
        _outboxCollapseDuplicates: function(entries) {
            var seen = {};
            var kept = [];
            var arr = entries || [];
            for (var i = 0; i < arr.length; i++) {
                var e = arr[i] || {};
                var pl = e.payload || {};
                var key = String(pl.id) + '|' + String(pl.dateCurr || '') +
                          '|' + String(parseFloat(pl.curr || 0)) + '|' +
                          String(pl.entryType || '');
                if (Object.prototype.hasOwnProperty.call(seen, key)) {
                    if (e.cid) this._outboxRemove(e.cid);
                    continue;
                }
                seen[key] = true;
                kept.push(e);
            }
            return kept;
        },""",
     'method-collapse'),
]

# ============================================================
# scripts/FlowmeterArchive.gs — правило «окно 1 часа» (Task 375)
# ============================================================
ARCHIVE = [
    # --- 10. комментарий блока дедупа ---
    ("""  // Повторы приходят с ИДЕНТИЧНЫМ payload (outbox ретраит запись
  // после потерянного ответа; sendBeacon «последнего шанса» летит
  // рядом с живым fetch'ем при закрытии; два окна приложения флашат
  // один localStorage) — ключ записи meterId (A) + prev (C) + curr (D)
  // + dateCurr (G) + entryType (R) у повтора совпадает полностью.
  // Разные показания расходятся хотя бы одним полем ключа (новое
  // значение → curr; новая дата → dateCurr; правка в окне 1 ч идёт
  // через updateLatestReading — на месте, без appendToArchive).""",
     """  // Повторы приходят с ИДЕНТИЧНЫМ payload (outbox ретраит запись
  // после потерянного ответа; sendBeacon «последнего шанса» летит
  // рядом с живым fetch'ем при закрытии; два окна приложения флашат
  // один localStorage) — ключ записи meterId (A) + prev (C) + curr (D)
  // + dateCurr (G) + entryType (R) у повтора совпадает полностью.
  // Разные показания расходятся хотя бы одним полем ключа (новое
  // значение → curr; новая дата → dateCurr; правка в окне 1 ч идёт
  // через updateLatestReading — на месте, без appendToArchive).
  //
  // Task 375 («окно 1 часа»): ДВА правила дубля —
  //   1) точный ключ A+C+D+G+R (повтор доставки одного payload);
  //   2) «свежий повтор значения»: тот же meterId + curr + dateCurr +
  //      entryType записан НЕ БОЛЕЕ ЧАСА НАЗАД (O-таймштамп строки),
  //      независимо от prev. Ловит «двойной сдвиг» prev при повторном
  //      срабатывании «Сохранить» (второй payload = prev сдвинут,
  //      точный ключ не совпадает) и прочие задвоения в окне правки —
  //      ровно тот период, когда повторная запись той же даты/значения
  //      всегда избыточна. Позже часа правило не действует (не мешает
  //      редким осознанным повторным вводам).""",
     'arch-comment-375'),

    # --- 11. _isDuplicateArchiveRow: правило 2 ---
    ("""      for (var i = values.length - 1; i >= 0; i--) {
        var row = values[i] || [];
        if (String(parseInt(row[0], 10)) !== idNeedle) continue;      // A: meterId
        if (String(parseFloat(row[2])) !== prevNeedle) continue;      // C: prev
        if (String(parseFloat(row[3])) !== currNeedle) continue;      // D: curr
        if (this._normEntryType(row[17]) !== etNeedle) continue;       // R: entryType
        var g = row[6];                                                // G: dateCurr (Date)
        if (g instanceof Date &&
            g.getFullYear() * 10000 + (g.getMonth() + 1) * 100 + g.getDate() === needleDay) {
          return true;
        }
      }
      return false;""",
     """      for (var i = values.length - 1; i >= 0; i--) {
        var row = values[i] || [];
        if (String(parseInt(row[0], 10)) !== idNeedle) continue;      // A: meterId
        if (String(parseFloat(row[3])) !== currNeedle) continue;      // D: curr
        if (this._normEntryType(row[17]) !== etNeedle) continue;       // R: entryType
        var g = row[6];                                                // G: dateCurr (Date)
        if (!(g instanceof Date) ||
            g.getFullYear() * 10000 + (g.getMonth() + 1) * 100 + g.getDate() !== needleDay) {
          continue;
        }
        // Правило 1 (Task 366): точный ключ — совпадает и prev
        if (String(parseFloat(row[2])) === prevNeedle) return true;   // C: prev
        // Правило 2 (Task 375): «свежий повтор значения» — та же запись
        // того же значения за ту же дату моложе 1 часа (O: timestamp),
        // независимо от prev («двойной сдвиг» при повторном «Сохранить»)
        var o = row[14];                                               // O: timestamp
        if (o instanceof Date && (new Date() - o) <= 60 * 60 * 1000) {
          return true;
        }
      }
      return false;""",
     'arch-rule-1h'),
]

if __name__ == '__main__':
    patch('index.html', INDEX)
    patch('scripts/FlowmeterArchive.gs', ARCHIVE)
    print('\nTask 375: все правки применены')
