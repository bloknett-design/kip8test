#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 376 — заявка пользователя: «при вводе новых данных расходов, в
# последнем расходомере №12 введённые новые данные записались на сервер
# в hozraschet_meters, а в архиве на hozraschet_archive не записались,
# в чём может быть причина, проверь».
#
# ДИАГНОЗ (подтверждён кодом):
#   Flowmeter.gs updateReading пишет meters-строку БЕЗ замка (~10
#   setValue), и ТОЛЬКО ПОТОМ вызывает appendToArchive — а тот обёрнут
#   в catch, глотающий ЛЮБУЮ ошибку как «non-critical», и возвращает
#   ok:true. appendToArchive пишет под Utils.withLock → tryLock(10 c):
#   при вводе всех 12 расходомеров подряд / параллельных beacon-
#   доставках при закрытии приложения очередь на ЕДИНСТВЕННЫЙ замок
#   скрипта длинная, и ПОСЛЕДНИЙ расходомер №12 упирался в таймаут →
#   server_busy → глотается → строка архива терялась при записанном
#   meters. Клиент получал ok:true, удалял запись из outbox — повтора
#   не было. Усилитель: дедуп _flushOutbox сверялся ТОЛЬКО с meters
#   (flowmeter.list) — раз meters совпал, запись из outbox удалялась
#   без проверки архива.
#
# ФИКС:
#   СЕРВЕР (FlowmeterArchive.gs): appendToArchive — 3 попытки записи
#   (10 c + 4 c + 4 c замок, пауза 1 с): транзиент очереди/квоты
#   поглощается; после последней неудачи — ПЕРЕБРОС вызывающему.
#   СЕРВЕР (Flowmeter.gs): updateReading при неудаче архива честно
#   возвращает ok:false 'archive_write_failed' (meters УЖЕ записан —
#   повторная доставка идемпотентна, серверный дедуп Task 366/375 не
#   даст дубль строки); _writePeriodEntry — стабильный код той же
#   ошибки (архив для периодических записей — единственное хранилище).
#   КЛИЕНТ (index.html): (1) archive_write_failed — НЕ «окончательный
#   отказ» (ретрай); (2) _sendUpdateReading/_submitPeriodEntry — запись
#   остаётся в outbox, тост честный, ретрай-таймер; (3) дедуп флаша
#   'day' подтверждает доставку по АРХИВУ (entryType+dateCurr+curr), а
#   не только по meters; (4) флаш, закончившийся с остатком, сам
#   планирует ретрай с бэкоффом.

import io, sys

def patch(path, repls):
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    for old, new, tag in repls:
        if src.count(old) != 1:
            print('FAIL [%s] anchor count=%d (ожидался 1): %r' % (tag, src.count(old), old[:80]))
            sys.exit(1)
        src = src.replace(old, new)
        print('OK  [%s] +%d/-%d строк' % (tag, new.count('\n'), old.count('\n')))
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(src)

# ============================================================
# 1. FlowmeterArchive.gs — appendToArchive: ретраи + переброс
# ============================================================
ARCHIVE = [
    (
        """    // Task 366: запись под замком (Utils.withLock, Task 348) — атомарная
    // пара «проверил хвост на дубль → дописал». Без замка две доставки
    // одного показания (ретрай outbox / beacon рядом с fetch / два окна
    // приложения) успевали прочитать хвост ДО чужой записи — и обе
    // дописывали строку. Замок НЕ реентерабельный: внутри только
    // операции листа (никаких withLock-функций). Дубль по ключу
    // meterId+prev+curr+dateCurr+entryType — НЕ дописываем: meters-
    // строка уже актуальна, история не обрастает копиями.
    var self = this;
    var appended = Utils.withLock(function() {
      if (self._isDuplicateArchiveRow(sheet, meterId, prev, curr, dateCurr, entryType)) {
        Logger.log('Archive (Task 366): дубль пропущен — meterId=' + meterId +
                   ', prev=' + prev + ', curr=' + curr + ', dateCurr=' + dateCurr +
                   (entryType ? (', entryType=' + entryType) : ''));
        return false;
      }""",
        """    // Task 366: запись под замком (Utils.withLock, Task 348) — атомарная
    // пара «проверил хвост на дубль → дописал». Без замка две доставки
    // одного показания (ретрай outbox / beacon рядом с fetch / два окна
    // приложения) успевали прочитать хвост ДО чужой записи — и обе
    // дописывали строку. Замок НЕ реентерабельный: внутри только
    // операции листа (никаких withLock-функций). Дубль по ключу
    // meterId+prev+curr+dateCurr+entryType — НЕ дописываем: meters-
    // строка уже актуальна, история не обрастает копиями.
    //
    // Task 376: РЕТРАИ записи — замок скрипта ОДИН на все выполнения
    // (соседние appendToArchive, сессии, крон). При вводе всех 12
    // расходомеров подряд или параллельных beacon-доставках при
    // закрытии приложения очередь на замок длинная, и ПОСЛЕДНИЙ в
    // очереди (№12) упирался в tryLock-таймаут → server_busy →
    // ошибка глоталась вызывающим как «non-critical» → строка архива
    // ТЕРЯЛАСЬ при записанном meters. Теперь: 3 попытки (10 c + 4 c +
    // 4 c, пауза 1 c) — транзиент очереди/квоты рассасывается за
    // секунды; после последней неудачи ПЕРЕБРАСЫВАЕМ исключение
    // вызывающему (updateReading/_writePeriodEntry вернут клиенту
    // archive_write_failed, запись останется в outbox и уйдёт позже;
    // повторная запись meters идемпотентна, дедуп Task 366/375 не
    // даст дубль строки). «Дубль» (false) ошибкой НЕ считается:
    // строка уже в архиве — миссия выполнена.
    var self = this;
    var attempts = [10000, 4000, 4000];
    var appended = null;
    var lastErr = null;
    for (var ai = 0; ai < attempts.length; ai++) {
      try {
        appended = Utils.withLock(function() {
      if (self._isDuplicateArchiveRow(sheet, meterId, prev, curr, dateCurr, entryType)) {
        Logger.log('Archive (Task 366): дубль пропущен — meterId=' + meterId +
                   ', prev=' + prev + ', curr=' + curr + ', dateCurr=' + dateCurr +
                   (entryType ? (', entryType=' + entryType) : ''));
        return false;
      }""",
        'archive: открытие цикла ретраев',
    ),
    (
        """      return true;
    });

    if (appended) {""",
        """      return true;
        }, attempts[ai]);
        lastErr = null;
        break;
      } catch (writeErr) {
        lastErr = writeErr;
        Logger.log('Archive write attempt ' + (ai + 1) + '/' + attempts.length +
                   ' failed: ' + writeErr.message);
        if (ai < attempts.length - 1) {
          Utilities.sleep(1000);
        }
      }
    }
    if (lastErr) {
      // Task 376: все попытки не удались — НЕ глотаем (так строка архива
      // терялась навсегда при записанном meters): вызывающий честно
      // вернёт archive_write_failed, клиент доставит запись повторно.
      throw lastErr;
    }

    if (appended) {""",
        'archive: закрытие цикла ретраев + переброс',
    ),
]

# ============================================================
# 2. Flowmeter.gs — честный ответ при неудаче архива
# ============================================================
FLOWMETER = [
    (
        """    // Ошибка архива не блокирует основной ответ (тихо логируется).
    try {""",
        """    // Task 376: ошибка архива больше НЕ «тихо логируется». Так терялась
    // строка архива при записанном meters: клиент получал ok:true, удалял
    // запись из outbox — повторной доставки не было (дедуп флаша к тому
    // же сверялся только с meters). Теперь при неудаче всех ретраев
    // appendToArchive — честный ответ archive_write_failed: meters уже
    // записан, запись ОСТАЁТСЯ в outbox клиента и будет доставлена
    // автоматически (повторная запись meters идемпотентна, серверный
    // дедуп Task 366/375 не даст дубль строки архива). «Дубль»
    // (appendToArchive вернул false — строка уже есть) ошибкой НЕ
    // считается.
    try {""",
        'flowmeter: комментарий-диагноз updateReading',
    ),
    (
        """    } catch (archiveErr) {
      Logger.log('Archive write failed (non-critical): ' + archiveErr.message);
    }

    return { ok: true, data: { id: id } };
  },""",
        """    } catch (archiveErr) {
      Logger.log('Archive write failed: ' + archiveErr.message);
      // Task 376: meters записан, архив — нет: честный отказ, клиент
      // оставит запись в outbox и доставит её повторно автоматически.
      return { ok: false, error: 'archive_write_failed',
               message: 'Показания сохранены, но запись в архив временно ' +
                        'не удалась — она будет отправлена повторно автоматически' };
    }

    return { ok: true, data: { id: id } };
  },""",
        'flowmeter: archive_write_failed в updateReading',
    ),
    (
        """    } catch (archiveErr) {
      Logger.log('Archive write failed (period entry): ' + archiveErr.message);
      return { ok: false, error: 'Ошибка записи в архив: ' + archiveErr.message };
    }""",
        """    } catch (archiveErr) {
      Logger.log('Archive write failed (period entry): ' + archiveErr.message);
      // Task 376: стабильный код ошибки (раньше текст в error не позволял
      // клиенту отличить «окончательный отказ» от «доставим позже»):
      // запись остаётся в outbox и уйдёт повторно.
      return { ok: false, error: 'archive_write_failed',
               message: 'Запись в архив не удалась — она будет отправлена ' +
                        'повторно автоматически (' + archiveErr.message + ')' };
    }""",
        'flowmeter: archive_write_failed в _writePeriodEntry',
    ),
]

# ============================================================
# 3. index.html — клиент: 5 правок
# ============================================================
INDEX = [
    # --- 3.1 _outboxIsPermanentError: archive_write_failed — ретрай ---
    (
        """            if (/server_busy/i.test(msg)) return false;             // Task 366: замок архива занят — ретрай позже
            return true;  // edit_window_expired / not_your_input / sign_neg / ...""",
        """            if (/server_busy/i.test(msg)) return false;             // Task 366: замок архива занят — ретрай позже
            if (/archive_write_failed/i.test(msg)) return false;    // Task 376: meters записан, архив нет — ретрай позже
            return true;  // edit_window_expired / not_your_input / sign_neg / ...""",
        'клиент: archive_write_failed не окончательный',
    ),
    # --- 3.2 _sendUpdateReading: ветка archive_write_failed ---
    (
        """            }).catch(function(err) {
                console.error('flowmeter.updateReading:', err);
                if (outboxCid && self._outboxIsPermanentError(err)) {""",
        """            }).catch(function(err) {
                console.error('flowmeter.updateReading:', err);
                // Task 376: meters на сервере уже записан, но строка архива
                // не доставлена (замок/квота при всех ретраях) — запись
                // ОСТАЁТСЯ в outbox и уйдёт повторно автоматически:
                // повторная запись meters идемпотентна, серверный дедуп
                // Task 366/375 не даст дубль строки архива.
                if (outboxCid && err &&
                        /archive_write_failed/i.test(String((err && err.message) || err))) {
                    self._outboxUpdate(outboxCid, {
                        state: 'retry',
                        lastErr: String(err.message || err)
                    });
                    self._scheduleOutboxRetry();
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Показания сохранены, но запись в архив не удалась — отправим повторно автоматически');
                    }
                    setTimeout(function() { self.load(); }, 200);
                    return;
                }
                if (outboxCid && self._outboxIsPermanentError(err)) {""",
        'клиент: ветка archive_write_failed в _sendUpdateReading',
    ),
    # --- 3.3 _submitPeriodEntry: ветка archive_write_failed ---
    (
        """                } else if (err && err._kind === 'SERVER') {
                    // Бизнес-ошибка (date_inconsistent и т.п.) — показываем
                    // человекочитаемое serverMessage, если сервер его приложил.
                    // Task 358: окончательный отказ — из outbox убираем
                    self._outboxRemove(outboxCid);""",
        """                } else if (err && err._kind === 'SERVER' &&
                           /archive_write_failed/i.test(msg)) {
                    // Task 376: архив не записан (архив — единственное
                    // хранилище периодической записи!) — запись ОСТАЁТСЯ в
                    // outbox и уйдёт повторно автоматически.
                    self._outboxUpdate(outboxCid, { state: 'retry', lastErr: msg });
                    self._scheduleOutboxRetry();
                    if (typeof KipToast !== 'undefined' && KipToast.show) {
                        KipToast.show('Запись в архив не удалась — отправим повторно автоматически');
                    }
                } else if (err && err._kind === 'SERVER') {
                    // Бизнес-ошибка (date_inconsistent и т.п.) — показываем
                    // человекочитаемое serverMessage, если сервер его приложил.
                    // Task 358: окончательный отказ — из outbox убираем
                    self._outboxRemove(outboxCid);""",
        'клиент: ветка archive_write_failed в _submitPeriodEntry',
    ),
    # --- 3.4 _flushOutbox: дедуп 'day' подтверждает по АРХИВУ ---
    (
        """            // Дедуп 'day': один flowmeter.list на все записи
            var p = Promise.resolve();
            if (dayEntries.length > 0) {
                p = p.then(function() {
                    return self._api('flowmeter.list', {}).then(function(data) {
                        var meters = (data && Array.isArray(data.meters)) ? data.meters : [];
                        dayEntries.forEach(function(e) {
                            var meter = null;
                            for (var i = 0; i < meters.length; i++) {
                                if (String(meters[i].id) === String((e.payload || {}).id)) {
                                    meter = meters[i]; break;
                                }
                            }
                            if (meter &&
                                String(meter.dateCurr || '') === String((e.payload || {}).dateCurr || '') &&
                                String(parseFloat(meter.curr)) === String(parseFloat((e.payload || {}).curr))) {
                                // уже на сервере (beacon дошёл в прошлый раз)
                                self._outboxRemove(e.cid);
                                e._delivered = true;
                            }
                        });
                    }).catch(function() { /* сеть — отправим ниже как есть */ });
                });
            }""",
        """            // Дедуп 'day': один flowmeter.list на все записи.
            // Task 376: сверки с meters МАЛО — meters-строка пишется
            // РАНЬШЕ архива и могла остаться ЕДИНСТВЕННОЙ записью
            // (архивная строка терялась при таймауте замка/квоте, ответ
            // был ok:true, запись из outbox удалялась — №12). Теперь
            // запись считается доставленной ТОЛЬКО когда в архиве есть
            // её строка (entryType + dateCurr + curr): meters-совпадение
            // без строки архива → запись ОСТАЁТСЯ и уйдёт повторно
            // (повторная запись meters идемпотентна, серверный дедуп
            // Task 366/375 не даст дубль строки архива).
            var p = Promise.resolve();
            if (dayEntries.length > 0) {
                p = p.then(function() {
                    return self._api('flowmeter.list', {}).then(function(data) {
                        var meters = (data && Array.isArray(data.meters)) ? data.meters : [];
                        var candidates = [];
                        dayEntries.forEach(function(e) {
                            var meter = null;
                            for (var i = 0; i < meters.length; i++) {
                                if (String(meters[i].id) === String((e.payload || {}).id)) {
                                    meter = meters[i]; break;
                                }
                            }
                            if (meter &&
                                String(meter.dateCurr || '') === String((e.payload || {}).dateCurr || '') &&
                                String(parseFloat(meter.curr)) === String(parseFloat((e.payload || {}).curr))) {
                                // meters совпал — кандидат на «уже доставлено»
                                // (beacon дошёл в прошлый раз); финальное слово
                                // за архивом
                                candidates.push({ e: e, id: (e.payload || {}).id });
                            }
                        });
                        // Task 376: подтверждение по архиву — один запрос на
                        // расходомер (обычно кандидатов 0–1: записи с ответом
                        // сервера из outbox уже удалены)
                        var ids = [];
                        candidates.forEach(function(c) {
                            if (ids.indexOf(String(c.id)) === -1) ids.push(String(c.id));
                        });
                        var vp = Promise.resolve();
                        ids.forEach(function(mid) {
                            vp = vp.then(function() {
                                return self._api('flowmeter.archive', { id: mid, limit: 30 })
                                    .then(function(adata) {
                                        var recs = (adata && Array.isArray(adata.records))
                                                   ? adata.records : [];
                                        candidates.forEach(function(c) {
                                            if (String(c.id) !== mid) return;
                                            var pl = (c.e.payload || {});
                                            var etNeedle = String(pl.entryType || 'сутки').trim().toLowerCase();
                                            if (etNeedle !== 'сутки') return;   // day-записи — только 'сутки'
                                            for (var r = 0; r < recs.length; r++) {
                                                var rec = recs[r];
                                                if (String(rec.entryType || 'сутки').toLowerCase() === etNeedle &&
                                                    String(rec.dateCurr || '') === String(pl.dateCurr || '') &&
                                                    String(parseFloat(rec.curr)) === String(parseFloat(pl.curr))) {
                                                    // строка архива на месте — теперь точно доставлено
                                                    self._outboxRemove(c.e.cid);
                                                    c.e._delivered = true;
                                                    break;
                                                }
                                            }
                                        });
                                    })
                                    .catch(function() { /* сеть — отправим ниже как есть */ });
                            });
                        });
                        return vp;
                    }).catch(function() { /* сеть — отправим ниже как есть */ });
                });
            }""",
        'клиент: дедуп day подтверждает по архиву',
    ),
    # --- 3.5 _flushOutbox finish: ретрай-таймер при остатке ---
    (
        """                if (sent > 0) {
                    self._outboxRetryTries = 0;
                    try {
                        if (typeof KipToast !== 'undefined' && KipToast.show) {
                            KipToast.show('Показания, ожидавшие связи, отправлены: ' + sent);
                        }
                    } catch (e) { /* ignore */ }
                }
                return sent;
            };""",
        """                if (sent > 0) {
                    self._outboxRetryTries = 0;
                    try {
                        if (typeof KipToast !== 'undefined' && KipToast.show) {
                            KipToast.show('Показания, ожидавшие связи, отправлены: ' + sent);
                        }
                    } catch (e) { /* ignore */ }
                }
                // Task 376: что-то осталось (сеть/сессия/server_busy/
                // archive_write_failed — флаш остановился на 'stop') —
                // планируем ретрай с бэкоффом сами: раньше запись ждала
                // только online/visibility/следующий заход в раздел.
                try {
                    if (self._outboxLoad().length > 0) {
                        self._scheduleOutboxRetry();
                    }
                } catch (e) { /* ignore */ }
                return sent;
            };""",
        'клиент: finish планирует ретрай при остатке',
    ),
]

patch('scripts/FlowmeterArchive.gs', ARCHIVE)
patch('scripts/Flowmeter.gs', FLOWMETER)
patch('index.html', INDEX)
print('\nTask 376: все правки применены.')
