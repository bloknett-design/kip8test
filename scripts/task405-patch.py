#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 405: заявка «в файле табель_КИП_ИОС таблицу инструктажи
# разделить на две таблицы: в текущей оставить только проведение
# инструктажей и проверки знаний, обучение и примечание перенести в
# новую таблицу "Мероприятия". В личных картах работников блок
# мероприятия остаётся (только данные новой таблицы), а данные из
# таблицы "Инструктажи" — в новом блоке "Повторные инструктажи и
# периодическая проверка знаний" на текущий год».
#
# СЕРВЕР (scripts/WorkSchedule.gs):
#   - лист «Мероприятия» (формат A..H — как «Инструктажи»)
#   - listTrainings читает ОБА листа объединённым списком (бейджи,
#     окна, печать, generateMonth — без изменений на клиенте)
#   - addTraining: маршрутизация по типу (инструктаж/проверка_знаний
#     → «Инструктажи»; обучение/прогул/примечание → «Мероприятия»,
#     лист создаётся при первой записи), id СКВОЗНОЙ по обоим листам
#   - deleteTraining: id ищется в обоих листах
#   - splitTrainingsSheet + top-level trainingsSplitInit() — разовый
#     перенос старых строк (идемпотентно, запускается в редакторе)
#
# ФРОНТ (index.html):
#   - _isInstrType; карточка: b3 «Мероприятия» = только
#     НЕ-инструктажи; НОВЫЙ b5 «Повторные инструктажи и периодическая
#     проверка знаний · год» = инструктаж/проверка_знаний (+ ✎/✕,
#     «+ Инструктаж…»); asBlocks [b1..b5], попап b1+b2+b3+b5
#   - панели: colTr = мероприятия + инструктажи (код не меняется)
#   - CSS .ws-whead-wrap — перенос длинного заголовка блока
#   - «Общая» сводка: «Мероприятия · год» = не-инструктажи + колонка
#     «Инструктажи · год»
#   - openTrainingForm 4-й аргумент prefillType («+ Мероприятие…» →
#     обучение, «+ Инструктаж…» → инструктаж)
import io


def patch(path, edits):
    src = io.open(path, encoding='utf-8').read()
    for i, (old, new) in enumerate(edits):
        n = src.count(old)
        assert n == 1, '%s PATCH %d: вхождений %d: %r' % (path, i, n, old[:90])
        src = src.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('%s: правок %d' % (path, len(edits)))


# ============================================================
# 1. scripts/WorkSchedule.gs — сервер
# ============================================================
patch('scripts/WorkSchedule.gs', [

    # 1) док-комментарий в шапке: список эндпоинтов
    (
        """//   workSchedule.listTrainings   — плановые инструктажи (с фильтром по месяцу)""",
        """//   workSchedule.listTrainings   — мероприятия: ОБЪЕДИНЁННЫЙ список
//                                   листов «Инструктажи» + «Мероприятия»
//                                   (Task 405; фильтр по месяцу/году)""",
    ),

    # 2) док-комментарий: структура листа «Инструктажи» (тип — после
    #    разделения) + блок про лист «Мероприятия»
    (
        """// Структура листа «Инструктажи»:
//   A: id (auto-increment)
//   B: таб_номер (FK на Сотрудники)
//   C: тип (инструктаж/обучение/проверка_знаний/прогул/примечание —
//      Task 306: два последних отображаются кодами ПР и *)""",
        """// Структура листа «Инструктажи» (Task 405 — таблица РАЗДЕЛЕНА):
//   A: id (auto-increment; нумерация СКВОЗНАЯ с листом
//      «Мероприятия» — связки Записи_графика.инструкция однозначны)
//   B: таб_номер (FK на Сотрудники)
//   C: тип — инструктаж/проверка_знаний (Task 306: прогул и
//      примечание тоже допустимы легаси-строками; Task 405:
//      обучение/прогул/примечание живут в листе «Мероприятия» —
//      разделение по типу, перенос старых строк — trainingsSplitInit)""",
    ),

    # 3) док-комментарий: блок листа «Мероприятия» перед «Записи_графика»
    (
        """//   G: длительность_дней (int)
//   H: комментарий
//
// Структура листа «Записи_графика» (ГЛАВНАЯ БД):""",
        """//   G: длительность_дней (int)
//   H: комментарий
//
// Структура листа «Мероприятия» (Task 405 — вторая половина
//   разделённой таблицы инструктажей: обучение/прогул/примечание):
//   A: id, B: таб_номер, C: тип, D: тема, E: дата_начала,
//   F: дата_окончания, G: длительность_дней, H: комментарий —
//   формат столбцов как у «Инструктажей»; listTrainings читает ОБА
//   листа одним списком, addTraining пишет в лист по типу,
//   deleteTraining ищет id в обоих листах
//
// Структура листа «Записи_графика» (ГЛАВНАЯ БД):""",
    ),

    # 4) док-комментарий листа «Отпуска» (бейджи мероприятий)
    (
        """//   показывается бейджем на клиенте (данные — лист «Инструктажи»,
//   связка — колонка I «инструкция»).""",
        """//   показывается бейджем на клиенте (данные — листы
//   «Инструктажи»/«Мероприятия» после разделения Task 405,
//   связка — колонка I «инструкция»).""",
    ),

    # 5) константа EVENTS_SHEET
    (
        """  TRAININGS_SHEET:    'Инструктажи',""",
        """  TRAININGS_SHEET:    'Инструктажи',
  // Task 405: лист «Мероприятия» — вторая половина разделённой
  // таблицы инструктажей (обучение/прогул/примечание; формат
  // столбцов A..H — как у «Инструктажей»). Чтение — вместе с
  // «Инструктажами» (listTrainings), записи маршрутизуются по типу
  EVENTS_SHEET:       'Мероприятия',""",
    ),

    # 6) карта маршрутизации типов + helper
    (
        """  TRAINING_TYPE_TO_STATUS: {
    'инструктаж':       'И',
    'обучение':         'ОБ',
    'проверка_знаний':  'ПЗ',
    'прогул':           'ПР',
    'примечание':       '*'
  },
""",
        """  TRAINING_TYPE_TO_STATUS: {
    'инструктаж':       'И',
    'обучение':         'ОБ',
    'проверка_знаний':  'ПЗ',
    'прогул':           'ПР',
    'примечание':       '*'
  },

  // Task 405 (заявка: разделение таблицы инструктажей): типы,
  // живущие в листе «Мероприятия» (всё, кроме инструктажа и
  // проверки знаний). Маршрутизация addTraining по типу; перенос
  // старых строк — trainingsSplitInit (разовый запуск в редакторе
  // Apps Script)
  TRAINING_EVENTSHEET_TYPES: {
    'обучение':         1,
    'прогул':           1,
    'примечание':       1
  },
""",
    ),

    # 7) комментарий слоя мероприятий (_isEventStatusCode)
    (
        """  // днях мероприятие не затирает смену: смена — основной код
  // ячейки, мероприятие показывается на клиенте бейджем (данные —
  // лист «Инструктажи», связка — колонка I). ПР и * — такие же""",
        """  // днях мероприятие не затирает смену: смена — основной код
  // ячейки, мероприятие показывается на клиенте бейджем (данные —
  // листы «Инструктажи»/«Мероприятия» Task 405, связка — колонка I).
  // ПР и * — такие же""",
    ),

    # 8) listTrainings — объединение двух листов + _readTrainingsSheet
    (
        """  listTrainings: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.TRAININGS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { trainings: [] } };

    var values = sheet.getRange(2, 1, lastRow - 1, 8).getValues();""",
        """  listTrainings: function(payload) {
    var auth = this._requireRead(payload.token);
    if (auth.error) return auth.error;

    var sheet = this._getSheet(this.TRAININGS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };

    // Task 405: мероприятие может лежать в ОДНОМ ИЗ ДВУХ листов —
    // «Инструктажи» (инструктаж/проверка_знаний) или «Мероприятия»
    // (обучение/прогул/примечание; формат A..H тот же). Ответ —
    // ОБЪЕДИНЁННЫЙ список обоих листов (бейджи/окна/печать/генерация
    // видят все мероприятия вместе, нумерация id сквозная). Листа
    // «Мероприятия» может не быть (до разделения данных) — тогда
    // отдаются только «Инструктажи»
    var trainings = this._readTrainingsSheet(sheet, payload);
    var evSheet = this._getSheet(this.EVENTS_SHEET);
    if (evSheet) {
      trainings = trainings.concat(this._readTrainingsSheet(evSheet, payload));
    }
    return { ok: true, data: { trainings: trainings } };
  },

  // Task 405: чтение ОДНОГО листа мероприятий (строки 2+, столбцы
  // A..H). payload.year/month — фильтр пересечения периода (как в
  // listTrainings до разделения); строки без id пропускаются
  _readTrainingsSheet: function(sheet, payload) {
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return [];

    var values = sheet.getRange(2, 1, lastRow - 1, 8).getValues();""",
    ),

    # 9) цикл чтения: trainings → out
    (
        """    var trainings = [];
    for (var i = 0; i < values.length; i++) {""",
        """    var out = [];
    for (var i = 0; i < values.length; i++) {""",
    ),

    # 9b) push в out (внутри цикла чтения)
    (
        """      trainings.push({""",
        """      out.push({""",
    ),

    # 10) хвост цикла: возврат списка (якорь — последнее поле записи)
    (
        """        комментарий:       String(r[7] || '').trim()
      });
    }
    return { ok: true, data: { trainings: trainings } };
  },
""",
        """        комментарий:       String(r[7] || '').trim()
      });
    }
    return out;
  },
""",
    ),

    # 11) addTraining: маршрутизация по типу + сквозной id
    (
        """    var sheet = this._getSheet(this.TRAININGS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };

    // Найти max id в столбце A
    var lastRow = sheet.getLastRow();
    var maxId = 0;
    if (lastRow >= 2) {
      var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) {
        var v = parseInt(ids[i][0], 10);
        if (!isNaN(v) && v > maxId) maxId = v;
      }
    }
    var newId = maxId + 1;""",
        """    // Task 405: лист записи — по ТИПУ мероприятия (инструктаж/
    // проверка_знаний → «Инструктажи»; обучение/прогул/примечание →
    // «Мероприятия», лист создаётся при первой записи, если нет)
    var sheetName = this._trainingsSheetForType(tip);
    var sheet = this._getSheet(sheetName);
    if (!sheet && sheetName === this.EVENTS_SHEET) {
      sheet = this._ensureEventsSheet();
    }
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + sheetName };

    // Task 405: id — ГЛОБАЛЬНЫЙ по обоим листам (сквозная
    // нумерация): связки Записи_графика.инструкция и правка по id
    // на клиенте однозначны и после разделения таблицы
    var maxId = this._maxTrainingsId(this._getSheet(this.TRAININGS_SHEET));
    var evMaxId = this._maxTrainingsId(this._getSheet(this.EVENTS_SHEET));
    if (evMaxId > maxId) maxId = evMaxId;
    var newId = maxId + 1;""",
    ),

    # 12) deleteTraining: поиск id в ОБОИХ листах
    (
        """    var sheet = this._getSheet(this.TRAININGS_SHEET);
    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: false, error: 'not_found' };

    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) {
      if (parseInt(ids[i][0], 10) === id) {
        sheet.deleteRow(i + 2);
        try {
          Utils.audit(user.email, 'WORKSCHEDULE_DELETE_TRAINING', '', '',
            'Удалено мероприятие id=' + id);
        } catch (e) { /* ignore */ }
        return { ok: true, data: { id: id } };
      }
    }
    return { ok: false, error: 'not_found' };
  },
""",
        """    // Task 405: id ищется в ОБОИХ листах — «Инструктажи» и
    // «Мероприятия» (нумерация сквозная, лист неизвестен клиенту)
    var sheetNames = [this.TRAININGS_SHEET, this.EVENTS_SHEET];
    for (var sn = 0; sn < sheetNames.length; sn++) {
      var sheet = this._getSheet(sheetNames[sn]);
      if (!sheet) continue;
      var lastRow = sheet.getLastRow();
      if (lastRow < 2) continue;
      var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) {
        if (parseInt(ids[i][0], 10) === id) {
          sheet.deleteRow(i + 2);
          try {
            Utils.audit(user.email, 'WORKSCHEDULE_DELETE_TRAINING', '', '',
              'Удалено мероприятие id=' + id + ' (лист ' + sheetNames[sn] + ')');
          } catch (e) { /* ignore */ }
          return { ok: true, data: { id: id } };
        }
      }
    }
    return { ok: false, error: 'not_found' };
  },
""",
    ),

    # 12b) док-комментарий deleteTraining
    (
        """  // workSchedule.deleteTraining
  // payload: { token, id }
  deleteTraining: function(payload) {""",
        """  // workSchedule.deleteTraining
  // payload: { token, id }
  // Task 405: id ищется в обоих листах («Инструктажи»/«Мероприятия»)
  deleteTraining: function(payload) {""",
    ),

    # 13) хелперы после _appendRowKeepText: _maxTrainingsId,
    #     _trainingsSheetForType, _ensureEventsSheet
    (
        """    sheet.getRange(newRow, 1, 1, rowValues.length).setValues([rowValues]);
    return newRow;
  },
""",
        """    sheet.getRange(newRow, 1, 1, rowValues.length).setValues([rowValues]);
    return newRow;
  },

  // Task 405: max id листа мероприятий (столбец A; null-лист — 0)
  _maxTrainingsId: function(sheet) {
    if (!sheet) return 0;
    var lastRow = sheet.getLastRow();
    var maxId = 0;
    if (lastRow >= 2) {
      var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) {
        var v = parseInt(ids[i][0], 10);
        if (!isNaN(v) && v > maxId) maxId = v;
      }
    }
    return maxId;
  },

  // Task 405: лист таблицы мероприятий для типа («Инструктажи» —
  // всё остальное: инструктаж/проверка_знаний и неизвестные типы
  // остаются в прежнем листе — перенос только явных «мероприятий»)
  _trainingsSheetForType: function(tip) {
    return this.TRAINING_EVENTSHEET_TYPES[tip]
      ? this.EVENTS_SHEET : this.TRAININGS_SHEET;
  },

  // Task 405: создать лист «Мероприятия» с заголовками (структура —
  // как у «Инструктажей»: строка 1 листа-образца копируется; нет
  // источника — канонические заголовки). Лист уже есть — вернуть
  // его. Вызывается addTraining при первой записи «мероприятийного»
  // типа и trainingsSplitInit — до ручного переноса данных
  // приложение остаётся рабочим
  _ensureEventsSheet: function() {
    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    var sheet = ss.getSheetByName(this.EVENTS_SHEET);
    if (sheet) return sheet;
    sheet = ss.insertSheet(this.EVENTS_SHEET);
    var headers = ['id', 'таб_номер', 'тип', 'тема', 'дата_начала',
                   'дата_окончания', 'длительность_дней', 'комментарий'];
    var src = this._getSheet(this.TRAININGS_SHEET);
    if (src && src.getLastRow() >= 1) {
      var srcHead = src.getRange(1, 1, 1, 8).getValues()[0];
      var filled = false;
      for (var h = 0; h < srcHead.length; h++) {
        if (String(srcHead[h] || '').trim()) { filled = true; break; }
      }
      if (filled) headers = srcHead;
    }
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length)
      .setFontWeight('bold').setBackground('#1F4E5F').setFontColor('#FFFFFF');
    sheet.setFrozenRows(1);
    try {
      Utils.audit('', 'WORKSCHEDULE_EVENTS_SHEET_CREATED', '', '',
        'Создан лист «Мероприятия» (Task 405 — разделение таблицы инструктажей)');
    } catch (e) { /* ignore */ }
    return sheet;
  },
""",
    ),
    # 14) splitTrainingsSheet — метод переноса (перед CRUD отпусков)
    (
        """  // ============================================================
  // CRUD отпусков (Task 274 — лист «Отпуска»)
  // ============================================================""",
        """  // Task 405 (заявка: разделение таблицы инструктажей): перенос
  // строк обучение/прогул/примечание из листа «Инструктажи» в лист
  // «Мероприятия». Запускается ВРУЧНУЮ из редактора Apps Script
  // (trainingsSplitInit) — через API приложения НЕ доступен.
  // Идемпотентно: повторный запуск не находит строк к переносу.
  // Тип сравнивается толерантно (регистр/пробелы); НЕИЗВЕСТНЫЕ
  // типы остаются в «Инструктажах» — переносятся только явные
  // «мероприятийные» (обучение/прогул/примечание)
  splitTrainingsSheet: function() {
    var src = this._getSheet(this.TRAININGS_SHEET);
    if (!src) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };
    var dst = this._ensureEventsSheet();
    if (!dst) return { ok: false, error: 'sheet_not_found: ' + this.EVENTS_SHEET };

    var lastRow = src.getLastRow();
    if (lastRow < 2) return { ok: true, moved: 0, sheet: this.EVENTS_SHEET };

    var values = src.getRange(2, 1, lastRow - 1, 8).getValues();
    var move = [];
    for (var i = 0; i < values.length; i++) {
      var tip = String(values[i][2] || '').trim().toLowerCase()
                  .replace(/\\s+/g, '_');
      if (this.TRAINING_EVENTSHEET_TYPES[tip]) {
        move.push({ row: i + 2, vals: values[i] });
      }
    }
    if (!move.length) return { ok: true, moved: 0, sheet: this.EVENTS_SHEET };

    // строки переносятся ЦЕЛИКОМ (id/даты — как в источнике;
    // Task 304: таб_номер — текстом, ведущие нули не теряются)
    for (var m = 0; m < move.length; m++) {
      this._appendRowKeepText(dst, move[m].vals, [2]);
    }
    // удаление перенесённых строк — снизу вверх (номера не съезжают)
    for (var d = move.length - 1; d >= 0; d--) {
      src.deleteRow(move[d].row);
    }
    try {
      Utils.audit('', 'WORKSCHEDULE_SPLIT_TRAININGS', '', '',
        'Разделение «Инструктажей»: перенесено строк — ' + move.length +
        ' (лист «' + this.EVENTS_SHEET + '»)');
    } catch (e) { /* ignore */ }
    return { ok: true, moved: move.length, sheet: this.EVENTS_SHEET };
  },

  // ============================================================
  // CRUD отпусков (Task 274 — лист «Отпуска»)
  // ============================================================""",
    ),

    # 15) top-level trainingsSplitInit — в конце файла (после `};`)
    (
        """    return { ok: false, error: 'not_found' };
  }

};""",
        """    return { ok: false, error: 'not_found' };
  }

};

// ============================================================
// Task 405: РАЗОВЫЙ перенос данных — разделение таблицы
// «Инструктажи» на «Инструктажи» + «Мероприятия»
// ============================================================
// ЗАПУСК (проект Apps Script табель_КИП_ИОС — тот же, где
// WorkSchedule.gs): в выпадающем списке функций редактора выбрать
// trainingsSplitInit → ▶ Run (первый запуск может попросить
// авторизацию — разрешить). Результат — в журнале (Ctrl+Enter).
// Что делает:
//   1) создаёт лист «Мероприятия» (заголовки — копия строки 1
//      листа «Инструктажи»; лист уже есть — не трогается);
//   2) переносит строки с типами обучение/прогул/примечание из
//      «Инструктажей» в «Мероприятия» — id и все значения строк
//      СОХРАНЯЮТСЯ (связки Записи_графика.инструкция не ломаются);
//   3) удаляет перенесённые строки из «Инструктажей».
// Повторный запуск безопасен (переносить уже нечего — moved: 0).
// После переноса функцию больше запускать не нужно.
function trainingsSplitInit() {
  var r = WorkSchedule.splitTrainingsSheet();
  Logger.log('trainingsSplitInit: ' + JSON.stringify(r));
}""",
    ),
])

print('ЧАСТЬ 1 (GAS) готова')

# ============================================================
# 2. index.html — клиент
# ============================================================
patch('index.html', [

    # 1) комментарий слоя мероприятий + хелпер _isInstrType
    (
        """        // ============================================================
        // Task 303: слой мероприятий (лист «Инструктажи»)
        // ============================================================

        // Тип мероприятия → код статуса (как TRAINING_TYPE_TO_STATUS""",
        """        // ============================================================
        // Task 303: слой мероприятий («Инструктажи» + «Мероприятия» —
        // Task 405: разделённая таблица; listTrainings отдаёт оба
        // листа одним списком, тип записи — источник истины)
        // ============================================================

        // Task 405: «инструктажный» тип — инструктаж/проверка_знаний
        // (лист «Инструктажи» после разделения таблицы; всё
        // остальное — обучение/примечание/прогул — лист
        // «Мероприятия»). Карточка работника фильтрует по ТИПУ —
        // блоки верны и до серверного переноса старых строк.
        // Толерантно к регистру/пробелам (ручное заполнение листа)
        _isInstrType: function(тип) {
            var t = String(тип || '').trim().toLowerCase()
                       .replace(/\\s+/g, '_');
            return t === 'инструктаж' || t === 'проверка_знаний';
        },

        // Тип мероприятия → код статуса (как TRAINING_TYPE_TO_STATUS""",
    ),

    # 2) карточка: сбор trs года + деление по типам
    (
        """            // --- Секция 3: мероприятия ГОДА (бывшая вкладка
            //     «Инструктажи»; Task 394 — заявка: в карточках
            //     работников мероприятия указываются НА ВЕСЬ ГОД).
            //     _TRAININGS — ГОДОВОЙ список (listTrainings без
            //     месяца); сверка пересечения с годом шахматки —
            //     защита от смешанных/устаревших данных (кэш
            //     прежних версий мог лежать месячным срезом) ---
            var trs = [];""",
        """            // --- Секция 3: мероприятия ГОДА (бывшая вкладка
            //     «Инструктажи»; Task 394 — заявка: в карточках
            //     работников мероприятия указываются НА ВЕСЬ ГОД).
            //     _TRAININGS — ГОДОВОЙ список (listTrainings без
            //     месяца); сверка пересечения с годом шахматки —
            //     защита от смешанных/устаревших данных (кэш
            //     прежних версий мог лежать месячным срезом).
            //     Task 405 (заявка: разделение таблицы): записи
            //     делятся ПО ТИПУ на два блока — «Мероприятия»
            //     (обучение/примечание/прогул) и «Повторные
            //     инструктажи и периодическая проверка знаний»
            //     (инструктаж/проверка_знаний; см. b5 ниже) ---
            var trs = [];""",
    ),

    # 3) после сортировки trs — деление evs/ins
    (
        """            trs.sort(function(a, b) {
                return String(a.дата_начала).localeCompare(String(b.дата_начала));
            });
            // Task 396: шапка блока мероприятий — полоса .ws-whead,""",
        """            trs.sort(function(a, b) {
                return String(a.дата_начала).localeCompare(String(b.дата_начала));
            });
            // Task 405: деление годовых записей по типу — блок
            // «Мероприятия» (evs: обучение/примечание/прогул) и блок
            // «Повторные инструктажи…» (ins: инструктаж/проверка_знаний)
            var evs = [], ins = [];
            for (var si = 0; si < trs.length; si++) {
                if (this._isInstrType(trs[si].тип)) ins.push(trs[si]);
                else evs.push(trs[si]);
            }
            // Task 396: шапка блока мероприятий — полоса .ws-whead,""",
    ),

    # 4) цикл блока мероприятий: trs → evs
    (
        """            if (!trs.length) {
                b3 += '<div class="ws-emp-empty">нет мероприятий за год</div>';
            } else {
                for (var tk = 0; tk < trs.length; tk++) {
                    var t = trs[tk];""",
        """            if (!evs.length) {
                b3 += '<div class="ws-emp-empty">нет мероприятий за год</div>';
            } else {
                for (var tk = 0; tk < evs.length; tk++) {
                    var t = evs[tk];""",
    ),

    # 5) НОВЫЙ блок b5 — перед секцией 4 (СИЗ)
    (
        """            // --- Секция 4: СИЗ — средства индивидуальной защиты""",
        """            // --- Секция 5 (Task 405, заявка: разделение таблицы
            //     инструктажей): ПОВТОРНЫЕ ИНСТРУКТАЖИ И ПЕРИОДИЧЕСКАЯ
            //     ПРОВЕРКА ЗНАНИЙ текущего года — данные таблицы
            //     «Инструктажи» (типы инструктаж/проверка_знаний).
            //     Строки — формат мероприятий (код И/ПЗ + тема +
            //     период, ✎/✕ редакторам по id); кнопка
            //     «+ Инструктаж…» открывает шторку с типом
            //     «инструктаж» ---
            var b5 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-wrap">Повторные инструктажи и периодическая проверка знаний · ' +
                  this._year + '</div><div class="ws-whead-a">' +
                  (withEdit ? '<button type="button" class="ws-wbtn ws-emp-addins"' +
                  ' title="Добавить инструктаж этому работнику"' +
                  ' onclick="WorkSchedule.onEmpAddInstruction(\\'' +
                  this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Инструктаж…</button>' : '') +
                  '</div></div>'
                : '<div class="ws-popup-sec">Повторные инструктажи и периодическая проверка знаний · ' +
                     this._year + '</div>';
            if (!ins.length) {
                b5 += '<div class="ws-emp-empty">нет инструктажей и проверок знаний за год</div>';
            } else {
                for (var ik = 0; ik < ins.length; ik++) {
                    var it = ins[ik];
                    var iCode = this._trainingCodeOf(it.тип);
                    var iMeta = this._statusMeta(iCode) || {};
                    var iTrId = parseInt(it.id, 10);
                    var iActs = '';
                    if (withEdit && iTrId) {
                        iActs = '<span class="ws-popup-act" title="Редактировать"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.editTraining(' + iTrId + ')">✎</span>' +
                                '<span class="ws-popup-act ws-popup-act-del" title="Удалить"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.deleteTraining(' + iTrId + ')">✕</span>';
                    }
                    var iPeriod = (it.дата_начала === it.дата_окончания)
                        ? this._fmtDateRu(it.дата_начала)
                        : (this._fmtDateRu(it.дата_начала) + ' — ' +
                           this._fmtDateRu(it.дата_окончания));
                    b5 += '<div class="ws-popup-row ws-popup-event' +
                          ((asBlocks && ik % 2 === 1) ? ' ws-row-alt' : '') + '">' +
                          '<span class="ws-popup-swatch" style="background:' +
                          (iMeta.color || '#3a3a3a') + ';"></span>' +
                          '<span class="ws-popup-code">' + this._esc(iCode || '—') + '</span>' +
                          '<span class="ws-popup-name">' +
                          this._esc(it.тема || iMeta.name || it.тип) +
                          ' · ' + iPeriod + '</span>' + iActs + '</div>';
                }
            }
            // «+ Инструктаж…» — шторка «Новое мероприятие» с работником
            // карточки и типом «инструктаж» (Task 405; вид без
            // asBlocks — строка внизу блока, как у отпусков)
            if (withEdit && !asBlocks) {
                b5 += '<div class="ws-popup-row ws-popup-more ws-emp-addins"' +
                      ' title="Добавить инструктаж этому работнику"' +
                      ' onclick="WorkSchedule.onEmpAddInstruction(\\'' +
                      this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Инструктаж…</div>';
            }

            // --- Секция 4: СИЗ — средства индивидуальной защиты""",
    ),

    # 6) возврат карточки: 5 блоков / попап с b5
    (
        """            // Task 393: asBlocks — массив 4 блоков (страница
            // «Работники», каждое — своё окно), без флага — строка.
            // Task 403 (заявка): попап шахматки — БЕЗ блока СИЗ (из
            // сплывающего окна данные СИЗ убраны; страница «Работники»
            // — по-прежнему все четыре блока)
            return asBlocks ? [b1, b2, b3, b4] : (b1 + b2 + b3);""",
        """            // Task 393: asBlocks — массив блоков (страница
            // «Работники», каждое — своё окно), без флага — строка.
            // Task 403 (заявка): попап шахматки — БЕЗ блока СИЗ (из
            // сплывающего окна данные СИЗ убраны). Task 405: ПЯТЬ
            // блоков — добавлен «Повторные инструктажи и периодическая
            // проверка знаний» (попап: профиль/отпуска/мероприятия/
            // инструктажи; страница «Работники» — все пять)
            return asBlocks ? [b1, b2, b3, b4, b5] : (b1 + b2 + b3 + b5);""",
    ),

    # 7) комментарий _renderWorkerCardPanels — 5 блоков, colTr
    (
        """        // Task 393 (заявка): ЧЕТЫРЕ БЛОКА карточки работника на
        // странице «Работники»: профиль с действиями / отпуска /
        // мероприятия / СИЗ — КАЖДЫЙ блок отдельным окном-панелью
        // .ws-wcard. Попап шахматки — сплошной вид БЕЗ блока СИЗ
        // (_renderWorkerCard без asBlocks; Task 403)
        // Task 395 → 403 → 404 (заявка): ТРИ колонки-обёртки .ws-wcol
        // (раскладка — CSS @media ≥1024px). Task 404 (заявка: «блок
        // СИЗ размести слева от блока мероприятия; в верхней части —
        // три блока слева направо: профиль (под ним отпуска), СИЗ,
        // мероприятия»): колонка 1 — ПРОФИЛЬ + ОТПУСКА (вертикальный
        // стек), колонка 2 (.ws-wcol-ppe) — СИЗ, колонка 3
        // (.ws-wcol-tr) — МЕРОПРИЯТИЯ: три верхних блока в ОДНУ
        // ЛИНИЮ. Мобайл ≤1023px — вертикальный СТЕК колонок
        // (профиль → отпуска → СИЗ → мероприятия); зазоры —
        // margin-bottom панелей (Task 393) + межколоночный (CSS)""",
        """        // Task 393 (заявка): БЛОКИ карточки работника на странице
        // «Работники»: профиль с действиями / отпуска / мероприятия
        // / СИЗ / повторные инструктажи (Task 405) — КАЖДЫЙ блок
        // отдельным окном-панелью .ws-wcard. Попап шахматки —
        // сплошной вид БЕЗ блока СИЗ (_renderWorkerCard без
        // asBlocks; Task 403)
        // Task 395 → 403 → 404 (заявка): ТРИ колонки-обёртки .ws-wcol
        // (раскладка — CSS @media ≥1024px). Task 404 (заявка: «блок
        // СИЗ размести слева от блока мероприятия; в верхней части —
        // три блока слева направо: профиль (под ним отпуска), СИЗ,
        // мероприятия»): колонка 1 — ПРОФИЛЬ + ОТПУСКА (вертикальный
        // стек), колонка 2 (.ws-wcol-ppe) — СИЗ, колонка 3
        // (.ws-wcol-tr) — МЕРОПРИЯТИЯ, под ним (Task 405) — блок
        // «Повторные инструктажи и периодическая проверка знаний»:
        // три верхних блока в ОДНУ ЛИНИЮ. Мобайл ≤1023px —
        // вертикальный СТЕК колонок (профиль → отпуска → СИЗ →
        // мероприятия → инструктажи); зазоры — margin-bottom панелей
        // (Task 393) + межколоночный (CSS)""",
    ),

    # 8) CSS: перенос длинного заголовка блока
    (
        """    .ws-wcard .ws-whead-t.ws-whead-name {
        /* ФИО · таб. № — крупнее секций, без капса */
        font-size: 16px;
        letter-spacing: 0.2px;
        text-transform: none;
    }""",
        """    .ws-wcard .ws-whead-t.ws-whead-name {
        /* ФИО · таб. № — крупнее секций, без капса */
        font-size: 16px;
        letter-spacing: 0.2px;
        text-transform: none;
    }
    .ws-wcard .ws-whead-t.ws-whead-wrap {
        /* Task 405: длинный заголовок блока инструктажей («Повторные
           инструктажи и периодическая проверка знаний · год») —
           ПЕРЕНОС строками в узкой колонке карточки, не эллипсис */
        white-space: normal;
        overflow: visible;
        text-overflow: clip;
        line-height: 1.3;
    }""",
    ),

    # 9) «Общая» сводка: колонка «Инструктажи · год»
    (
        """                    '<th>Отпуск · ' + this._year + '</th>' +
                    '<th>Мероприятия · ' + this._year + '</th>' +
                    '</tr></thead><tbody>';""",
        """                    '<th>Отпуск · ' + this._year + '</th>' +
                    '<th>Мероприятия · ' + this._year + '</th>' +
                    '<th>Инструктажи · ' + this._year + '</th>' +
                    '</tr></thead><tbody>';""",
    ),

    # 10) «Общая» сводка: счёт по типам
    (
        """                var trN = 0;
                for (var ti = 0; ti < (this._TRAININGS || []).length; ti++) {
                    if (this._TRAININGS[ti]['таб_номер'] === emp['таб_номер']) trN++;
                }""",
        """                // Task 405 (разделение таблицы): «Мероприятия» —
                // только обучение/примечание/прогул; инструктажи и
                // проверки знаний — своя колонка «Инструктажи · год»
                var trN = 0, insN = 0;
                for (var ti = 0; ti < (this._TRAININGS || []).length; ti++) {
                    if (this._TRAININGS[ti]['таб_номер'] !== emp['таб_номер']) continue;
                    if (this._isInstrType(this._TRAININGS[ti].тип)) insN++;
                    else trN++;
                }""",
    ),

    # 11) «Общая» сводка: ячейки строк
    (
        """                        '<td>' + (vacDays ? vacDays + ' ' +
                            this._plural(vacDays, ['день', 'дня', 'дней']) : '—') + '</td>' +
                        '<td>' + (trN || '—') + '</td></tr>';""",
        """                        '<td>' + (vacDays ? vacDays + ' ' +
                            this._plural(vacDays, ['день', 'дня', 'дней']) : '—') + '</td>' +
                        '<td>' + (trN || '—') + '</td>' +
                        '<td>' + (insN || '—') + '</td></tr>';""",
    ),

    # 12) openTrainingForm: 4-й аргумент prefillType
    (
        """        openTrainingForm: function(prefillTab, prefillDate, editTraining) {""",
        """        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {""",
    ),

    # 13) openTrainingForm: тип по умолчанию из кнопки входа
    (
        """                document.getElementById('wsTrStart').value = today;
                document.getElementById('wsTrEnd').value = today;
                document.getElementById('wsTrDays').value = 1;
                document.getElementById('wsTrType').value = 'инструктаж';
                document.getElementById('wsTrTitle').value = '';""",
        """                document.getElementById('wsTrStart').value = today;
                document.getElementById('wsTrEnd').value = today;
                document.getElementById('wsTrDays').value = 1;
                // Task 405: тип по умолчанию — из кнопки входа
                // («+ Мероприятие…» блока мероприятий → обучение,
                // «+ Инструктаж…» → инструктаж); без указания —
                // прежний дефолт «инструктаж» (попап ячейки)
                var preTip = String(prefillType || '').trim();
                document.getElementById('wsTrType').value =
                    (preTip === 'инструктаж' || preTip === 'обучение' ||
                     preTip === 'проверка_знаний' || preTip === 'прогул' ||
                     preTip === 'примечание') ? preTip : 'инструктаж';
                document.getElementById('wsTrTitle').value = '';""",
    ),

    # 14) onEmpAddTraining → дефолт «обучение»; + onEmpAddInstruction
    (
        """        onEmpAddTraining: function(tabNo) {
            this.closeEmpPopup();
            this.openTrainingForm(tabNo);
        },""",
        """        onEmpAddTraining: function(tabNo) {
            this.closeEmpPopup();
            // Task 405: кнопка блока «Мероприятия» — дефолт типа
            // «обучение» (запись уйдёт в таблицу «Мероприятия»)
            this.openTrainingForm(tabNo, null, null, 'обучение');
        },

        // Task 405: «+ Инструктаж…» из блока «Повторные инструктажи и
        // периодическая проверка знаний» — шторка «Новое мероприятие»
        // с работником карточки и типом «инструктаж» (запись уйдёт в
        // таблицу «Инструктажи»); двойная защита — в openTrainingForm
        onEmpAddInstruction: function(tabNo) {
            this.closeEmpPopup();
            this.openTrainingForm(tabNo, null, null, 'инструктаж');
        },""",
    ),

    # 15) док-комментарий HTML (Task 308): разделение таблицы
    (
        """             • мероприятия (инструктажи/обучения/проверки/прогул/
               примечание) — бейджи в ячейках шахматки, добавление —
               «+ Мероприятие…» в попапе ячейки (Task 303, шторка
               #wsTrSheet / openTrainingForm);""",
        """             • мероприятия (инструктажи/обучения/проверки/прогул/
               примечание) — бейджи в ячейках шахматки, добавление —
               «+ Мероприятие…» в попапе ячейки (Task 303, шторка
               #wsTrSheet / openTrainingForm); Task 405: таблица
               инструктажей РАЗДЕЛЕНА — таблица «Инструктажи»
               (инструктаж/проверка_знаний) + таблица «Мероприятия»
               (обучение/прогул/примечание), клиенту список —
               объединённый;""",
    ),

    # 16) док-комментарий API: listTrainings — оба листа
    (
        """    //   workSchedule.listTrainings      — плановые инструктажи""",
        """    //   workSchedule.listTrainings      — мероприятия года (Task 405:
    //                                      ОБЪЕДИНЁННЫЙ список таблиц
    //                                      «Инструктажи» + «Мероприятия»)""",
    ),

    # 17) комментарий кэша: _EVENT_CODES — оба листа
    (
        """        // Task 303: слой мероприятий в ячейке («два значения»):
        // _EVENT_CODES — коды мероприятий (из листа «Инструктажи»).""",
        """        // Task 303: слой мероприятий в ячейке («два значения»):
        // _EVENT_CODES — коды мероприятий (таблицы «Инструктажи» +
        // «Мероприятия» — Task 405, список объединённый).""",
    ),

    # 18) комментарий _loadTrainings — объединённый список
    (
        """        // Task 394 (заявка): мероприятия грузятся на ВЕСЬ ГОД
        // шахматки — month НЕ указан (сервер listTrainings без
        // месяца отдаёт все записи, ПЕРЕСЕКАЮЩИЕ год): карточки""",
        """        // Task 394 (заявка): мероприятия грузятся на ВЕСЬ ГОД
        // шахматки — month НЕ указан (сервер listTrainings без
        // месяца отдаёт все записи, ПЕРЕСЕКАЮЩИЕ год; Task 405 —
        // ОБЪЕДИНЁННЫЙ список таблиц «Инструктажи» + «Мероприятия»):
        // карточки""",
    ),

    # 19) комментарий страницы «Работники»: ПЯТЬ блоков
    (
        """            // тело вкладки: «Общая» — сводная таблица всех
            // работников (Task 389: ОКНО-панель .ws-wgen со сплошным
            // фоном — как карточка работника); работник — ЧЕТЫРЕ
            // блока-панели карточки (Task 393: профиль с действиями /
            // отпуска / мероприятия / СИЗ — каждое своё окно)""",
        """            // тело вкладки: «Общая» — сводная таблица всех
            // работников (Task 389: ОКНО-панель .ws-wgen со сплошным
            // фоном — как карточка работника); работник — ПЯТЬ
            // блоков-панелей карточки (Task 393: профиль с действиями
            // / отпуска / мероприятия / СИЗ; Task 405: + повторные
            // инструктажи — каждое своё окно)""",
    ),
])

print('ЧАСТЬ 2 (index.html) готова')
