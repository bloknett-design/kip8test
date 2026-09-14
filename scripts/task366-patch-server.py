#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 366 (сервер) — дубли строк hozraschet_archive при однократном
# вводе показаний. Заявка: «при однократном вводе значения расхода,
# в любом из расходомеров, добавляемая автоматически при этом строка
# в таблице hozraschet_archive иногда дублируется (иногда один раз,
# иногда несколько раз подряд)».
#
# Причина: Apps Script выполняет запросы ПАРАЛЛЕЛЬНО, а архив пишется
# appendRow'ом без проверки. Повторная доставка ОДНОГО показания —
# обычное дело: outbox ретраит запись после потерянного ответа (сеть),
# sendBeacon «последнего шанса» летит рядом с ещё живым fetch'ем при
# закрытии вкладки, два окна приложения флашат общий localStorage.
# Каждая такая доставка дописывала строку → дубли.
#
# Решение: appendToArchive под Utils.withLock (Task 348, атомарность
# «прочитал хвост → дописал») + дедуп хвоста: запись с тем же ключом
# meterId (A) + prev (C) + curr (D) + dateCurr (G) + entryType (R)
# среди последних 50 строк — НЕ дописывается. У повтора payload тот же,
# ключ совпадает полностью; разные показания расходятся хотя бы одним
# полем. Правка в окне 1 ч идёт через updateLatestReading (на месте,
# без appendToArchive) — её дедуп не касается.
import sys

P = '/home/z/my-project/kip8test/scripts/FlowmeterArchive.gs'
src = open(P, encoding='utf-8').read()

def rep(old, new, n=1, tag=''):
    global src
    cnt = src.count(old)
    if cnt != n:
        print('ОШИБКА [%s]: найдено %d, ожидалось %d' % (tag, cnt, n))
        sys.exit(1)
    src = src.replace(old, new)
    print('[ok] %s' % tag)

# --- 1. хелперы дедупа ПЕРЕД appendToArchive ---
rep(
"""  // ============================================================
  // appendToArchive — добавить запись в архив
  // Вызывается из Flowmeter.updateReading() после записи новых показаний
  // ============================================================""",
"""  // ============================================================
  // _normEntryType / _isDuplicateArchiveRow — Task 366: защита
  // архива от дублей строк при повторной доставке показания.
  // ============================================================
  // Повторы приходят с ИДЕНТИЧНЫМ payload (outbox ретраит запись
  // после потерянного ответа; sendBeacon «последнего шанса» летит
  // рядом с живым fetch'ем при закрытии; два окна приложения флашат
  // один localStorage) — ключ записи meterId (A) + prev (C) + curr (D)
  // + dateCurr (G) + entryType (R) у повтора совпадает полностью.
  // Разные показания расходятся хотя бы одним полем ключа (новое
  // значение → curr; новая дата → dateCurr; правка в окне 1 ч идёт
  // через updateLatestReading — на месте, без appendToArchive).
  // Сканируем хвост архива (последние 50 строк) — дубль всегда среди
  // свежих строк. Вызывается ТОЛЬКО из appendToArchive внутри
  // Utils.withLock (атомарность «прочитал хвост → дописал»; замок
  // НЕ реентерабельный — внутри только операции листа). Сбой
  // проверки = «не дубль»: лучше редкий дубль, чем потерянная запись.
  // ============================================================
  _normEntryType: function(v) {
    var s = String(v || '').trim().toLowerCase();
    return (s === '' || s === 'сутки') ? 'сутки' : s;   // legacy '' = сутки
  },

  _isDuplicateArchiveRow: function(sheet, meterId, prev, curr, dateCurr, entryType) {
    try {
      var lastRow = sheet.getLastRow();
      if (lastRow < this.DATA_START_ROW) return false;
      var scan = Math.min(50, lastRow - this.DATA_START_ROW + 1);
      var values = sheet.getRange(lastRow - scan + 1, 1, scan, 18).getValues();
      var idNeedle = String(parseInt(meterId, 10));
      var prevNeedle = String(parseFloat(prev || 0));
      var currNeedle = String(parseFloat(curr || 0));
      var etNeedle = this._normEntryType(entryType);
      var needleDate = Flowmeter._clientToDateObj(dateCurr);
      if (!needleDate) return false;   // дату не разобрали — дубль не подтвердить
      var needleDay = needleDate.getFullYear() * 10000 +
                      (needleDate.getMonth() + 1) * 100 + needleDate.getDate();
      for (var i = values.length - 1; i >= 0; i--) {
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
      return false;
    } catch (e) {
      Logger.log('Archive dedup check failed (append anyway): ' + e.message);
      return false;
    }
  },

  // ============================================================
  // appendToArchive — добавить запись в архив
  // Вызывается из Flowmeter.updateReading() после записи новых показаний
  // ============================================================""",
    1, 'хелперы _normEntryType/_isDuplicateArchiveRow')

# --- 2. appendRow под замком + дедуп ---
rep(
"""    // Добавляем строку в конец листа.
    // Структура (18 столбцов A–R, Task 100 добавил K=Gcal, Task 197 — P=comment,
    // Task 199 — Q=anomaly, Task 286 — R=entryType):
    //   A meterId, B hoz, C prev, D curr, E consumption,
    //   F datePrev, G dateCurr, H daysBetween, I unit, J temp,
    //   K Gcal (Task 100), L period, M modRole, N modName, O timestamp,
    //   P comment (Task 197), Q anomaly (Task 199), R entryType (Task 286)
    sheet.appendRow([
      meterId,                                                                    // A: meterId
      hoz || '',                                                                  // B: hoz
      prev || 0,                                                                  // C: prev
      curr || 0,                                                                  // D: curr
      consumption,                                                                // E: consumption
      datePrevObj || '',                                                          // F: datePrev (Date object)
      dateCurrObj || '',                                                          // G: dateCurr (Date object)
      daysBetween,                                                                // H: daysBetween
      unit || '',                                                                 // I: unit (раньше было в J, но в архиве порядок другой — см. заголовки)
      (temp !== null && temp !== undefined && temp !== '') ? parseFloat(temp) : '',  // J: temp
      (gcal !== null && gcal !== undefined && gcal !== '') ? parseFloat(gcal) : '',  // K: Gcal (Task 100)
      period || '',                                                               // L: period
      role || '',                                                                 // M: modRole
      name || '',                                                                 // N: modName
      new Date(),                                                                  // O: timestamp
      String(comment || ''),                                                       // P: comment (Task 197)
      String(anomaly || ''),                                                       // Q: anomaly (Task 199)
      String(entryType || '')                                                      // R: entryType (Task 286)
    ]);

    Logger.log('Archive: meterId=' + meterId + ', prev=' + prev + ', curr=' + curr + ', consumption=' + consumption + ', gcal=' + (gcal || '—') +
               (entryType ? (', entryType=' + entryType) : ''));
  },""",
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
      }
      // Добавляем строку в конец листа.
      // Структура (18 столбцов A–R, Task 100 добавил K=Gcal, Task 197 — P=comment,
      // Task 199 — Q=anomaly, Task 286 — R=entryType):
      //   A meterId, B hoz, C prev, D curr, E consumption,
      //   F datePrev, G dateCurr, H daysBetween, I unit, J temp,
      //   K Gcal (Task 100), L period, M modRole, N modName, O timestamp,
      //   P comment (Task 197), Q anomaly (Task 199), R entryType (Task 286)
      sheet.appendRow([
        meterId,                                                                    // A: meterId
        hoz || '',                                                                  // B: hoz
        prev || 0,                                                                  // C: prev
        curr || 0,                                                                  // D: curr
        consumption,                                                                // E: consumption
        datePrevObj || '',                                                          // F: datePrev (Date object)
        dateCurrObj || '',                                                          // G: dateCurr (Date object)
        daysBetween,                                                                // H: daysBetween
        unit || '',                                                                 // I: unit (раньше было в J, но в архиве порядок другой — см. заголовки)
        (temp !== null && temp !== undefined && temp !== '') ? parseFloat(temp) : '',  // J: temp
        (gcal !== null && gcal !== undefined && gcal !== '') ? parseFloat(gcal) : '',  // K: Gcal (Task 100)
        period || '',                                                               // L: period
        role || '',                                                                 // M: modRole
        name || '',                                                                 // N: modName
        new Date(),                                                                  // O: timestamp
        String(comment || ''),                                                       // P: comment (Task 197)
        String(anomaly || ''),                                                       // Q: anomaly (Task 199)
        String(entryType || '')                                                      // R: entryType (Task 286)
      ]);
      return true;
    });

    if (appended) {
      Logger.log('Archive: meterId=' + meterId + ', prev=' + prev + ', curr=' + curr + ', consumption=' + consumption + ', gcal=' + (gcal || '—') +
                 (entryType ? (', entryType=' + entryType) : ''));
    }
  },""",
    1, 'appendToArchive: замок + дедуп')

open(P, 'w', encoding='utf-8').write(src)

# Контроль
assert src.count('_isDuplicateArchiveRow') == 3, 'хелпер: комментарий + определение + вызов'
assert 'Utils.withLock(function() {' in src
assert 'var self = this;' in src
# _isDuplicateArchiveRow НЕ берёт замок сам (реентерабельность запрещена)
i = src.index('_isDuplicateArchiveRow: function')
j = src.index('appendToArchive: function')
assert 'withLock' not in src[i:j], 'замок внутри хелпера — ЗАПРЕЩЕНО (реентерабельность)'
print('FlowmeterArchive.gs: дедуп + Utils.withLock готовы; вложенных замков нет')
