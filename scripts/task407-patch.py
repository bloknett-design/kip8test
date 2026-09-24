# -*- coding: utf-8 -*-
# Task 407: блок «Повторные инструктажи и периодическая проверка знаний»
# по ШАБЛОНУ «Список_И_и_ПЗ» (новый лист табель_КИП_ИОС) + связка с
# таблицей «Инструктажи» по столбцу «название» (= «тема» записи).
# GAS: чтение листа по заголовкам (позиция столбцов любая) + поля
#      instrList/instrAll в ответе listTrainings + разовый instrListInit.
# Фронт: _INSTR_LIST/_INSTR_ALL (+кэш Task 314), групповой рендер блока
#      (пункты шаблона, записи года, «след. срок»/«просрочено», «вне
#      списка»), datalist подсказок «Темы» в шторке.
import io, sys

ROOT = '/home/z/my-project/kip8test'
GS = ROOT + '/scripts/WorkSchedule.gs'
IDX = ROOT + '/index.html'

def patch(path, edits):
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    for (old, new, label) in edits:
        if src.count(old) != 1:
            print('FAIL [%s] count=%d: %s' % (path.split('/')[-1], src.count(old), label))
            sys.exit(1)
        src = src.replace(old, new, 1)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print('OK %s: %d edits' % (path.split('/')[-1], len(edits)))

# ============================================================
# WorkSchedule.gs
# ============================================================
GS_EDITS = []

# G1: константа листа
GS_EDITS.append((
"""  EVENTS_SHEET:       'Мероприятия',
""",
"""  EVENTS_SHEET:       'Мероприятия',
  // Task 407: лист «Список_И_и_ПЗ» — шаблонный список инструктажей
  // и проверок знаний (каркас блока «Повторные инструктажи и
  // периодическая проверка знаний»; связка с записями «Инструктажей»
  // по «название» = «тема» записи). Лист может отсутствовать (до
  // разового запуска instrListInit) — приложение работает, блок
  // показывает плоский список записей года
  INSTR_LIST_SHEET:   'Список_И_и_ПЗ',
""", 'G1 константа INSTR_LIST_SHEET'))

# G2: док-блок структуры листа
GS_EDITS.append((
"""//   формат столбцов как у «Инструктажей»; listTrainings читает ОБА
//   листа одним списком, addTraining пишет в лист по типу,
//   deleteTraining ищет id в обоих листах
""",
"""//   формат столбцов как у «Инструктажей»; listTrainings читает ОБА
//   листа одним списком, addTraining пишет в лист по типу,
//   deleteTraining ищет id в обоих листах
//
// Структура листа «Список_И_и_ПЗ» (Task 407 — шаблонный список
//   инструктажей и проверок знаний): столбцы — ПО ЗАГОЛОВКАМ строки 1
//   (позиция любая, приём Task 402/403 «группа_допуска»):
//   название — ключ соответствия: текст = «тема» записи таблицы
//     «Инструктажи» (сравнение нормализованное: регистр/лишние
//     пробелы/«ё» не важны — считает клиент);
//   вид — инструктаж/проверка_знаний (толерантно к написанию);
//   периодичность — число месяцев (пусто/0 = разовый — «следующий
//     срок» не считается);
//   основание — приказ/правила (справочно).
//   Создание — разовый запуск instrListInit в редакторе Apps Script.
""", 'G2 док-блок структуры'))

# G3: listTrainings — instrList + instrAll в ответе
GS_EDITS.append((
"""    var trainings = this._readTrainingsSheet(sheet, payload);
    var evSheet = this._getSheet(this.EVENTS_SHEET);
    if (evSheet) {
      trainings = trainings.concat(this._readTrainingsSheet(evSheet, payload));
    }
    return { ok: true, data: { trainings: trainings } };
  },
""",
"""    var trainings = this._readTrainingsSheet(sheet, payload);
    var evSheet = this._getSheet(this.EVENTS_SHEET);
    if (evSheet) {
      trainings = trainings.concat(this._readTrainingsSheet(evSheet, payload));
    }
    // Task 407: каркас блока «Повторные инструктажи…» — шаблонный
    // список «Список_И_и_ПЗ» (нет листа — пустой массив, блок живёт
    // плоским списком записей года) и ВСЕ записи «Инструктажей» БЕЗ
    // фильтра года (клиент ищет ПОСЛЕДНИЙ инструктаж по всем годам —
    // контроль годовых/трёхлетних циклов; trainings остаётся годовым
    // срезом — бейджи/окно месяца/печать/сводная не меняются)
    return { ok: true, data: {
      trainings: trainings,
      instrList: this._readInstrListSheet(),
      instrAll:  this._readTrainingsSheet(sheet, {})
    } };
  },
""", 'G3 listTrainings instrList/instrAll'))

# G4: _readInstrListSheet — после _readTrainingsSheet
GS_EDITS.append((
"""    return out;
  },

  // workSchedule.listVacations (Task 274)
""",
"""    return out;
  },

  // Task 407: чтение листа «Список_И_и_ПЗ» — шаблонного списка
  // инструктажей и проверок знаний. Столбцы — ПО ЗАГОЛОВКАМ строки 1
  // (_headerColIndex, позиция любая): название (ключ соответствия с
  // «темой» записей «Инструктажей»), вид (инструктаж/
  // проверка_знаний), периодичность (число месяцев; пусто = разовый),
  // основание. Нет листа или ключевого столбца «название» — пустой
  // список (клиент показывает плоский список записей года)
  _readInstrListSheet: function() {
    var sheet = this._getSheet(this.INSTR_LIST_SHEET);
    if (!sheet) return [];
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return [];
    var lastCol = 1;
    try { lastCol = sheet.getLastColumn() || 1; } catch (e) { lastCol = 8; }
    var nameCol = this._headerColIndex(sheet, ['название']);
    if (nameCol === null) return [];
    var kindCol = this._headerColIndex(sheet, ['вид']);
    var perCol  = this._headerColIndex(sheet, [
      'периодичность', 'периодичность, мес', 'периодичность мес']);
    var baseCol = this._headerColIndex(sheet, ['основание']);
    var values = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
    var out = [];
    for (var i = 0; i < values.length; i++) {
      var r = values[i];
      var name = String(r[nameCol] || '').trim();
      if (!name) continue;
      var per = 0;
      if (perCol !== null) {
        per = parseFloat(String(r[perCol] || '').replace(',', '.')) || 0;
      }
      out.push({
        название:      name,
        вид:           kindCol !== null ? String(r[kindCol] || '').trim() : '',
        периодичность: per,
        основание:     baseCol !== null ? String(r[baseCol] || '').trim() : ''
      });
    }
    return out;
  },

  // workSchedule.listVacations (Task 274)
""", 'G4 _readInstrListSheet'))

# G5: instrListInit — метод (перед закрывающим }; объекта)
GS_EDITS.append((
"""    return { ok: false, error: 'not_found' };
  }

};
""",
"""    return { ok: false, error: 'not_found' };
  },

  // Task 407: разовая инициализация листа «Список_И_и_ПЗ» — создать
  // лист с заголовками (название/вид/периодичность/основание) и
  // типовым наполнением (пользователь редактирует под свою
  // номенклатуру: «название» = «тема» записей «Инструктажей»,
  // «периодичность» — число месяцев, пусто = разовый). Лист уже
  // есть — только отчёт (идемпотентно). Через API приложения НЕ
  // доступен — запуск в редакторе Apps Script (instrListInit, как
  // trainingsSplitInit)
  instrListInit: function() {
    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    var sheet = ss.getSheetByName(this.INSTR_LIST_SHEET);
    if (sheet) {
      return { ok: true, exists: true,
               rows: Math.max(0, sheet.getLastRow() - 1) };
    }
    sheet = ss.insertSheet(this.INSTR_LIST_SHEET);
    var headers = ['название', 'вид', 'периодичность', 'основание'];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length)
      .setFontWeight('bold').setBackground('#1F4E5F').setFontColor('#FFFFFF');
    sheet.setFrozenRows(1);
    var sample = [
      ['Охрана труда', 'инструктаж', 6,
       'не реже 1 раза в 6 месяцев'],
      ['Пожарная безопасность', 'инструктаж', 6,
       'не реже 1 раза в 6 месяцев'],
      ['Электробезопасность', 'проверка_знаний', 12,
       'ежегодно'],
      ['Проверка знаний по специальности', 'проверка_знаний', 12,
       'не реже 1 раза в год']
    ];
    sheet.getRange(2, 1, sample.length, 4).setValues(sample);
    try {
      Utils.audit('', 'WORKSCHEDULE_INSTR_LIST_SHEET_CREATED', '', '',
        'Создан лист «Список_И_и_ПЗ» (Task 407 — шаблонный список инструктажей и проверок знаний)');
    } catch (e) { /* ignore */ }
    return { ok: true, created: true, rows: sample.length };
  }

};
""", 'G5 instrListInit метод'))

# G6: топ-левел функция instrListInit (после trainingsSplitInit)
GS_EDITS.append((
"""function trainingsSplitInit() {
  var r = WorkSchedule.splitTrainingsSheet();
  Logger.log('trainingsSplitInit: ' + JSON.stringify(r));
}
""",
"""function trainingsSplitInit() {
  var r = WorkSchedule.splitTrainingsSheet();
  Logger.log('trainingsSplitInit: ' + JSON.stringify(r));
}

// ============================================================
// Task 407: РАЗОВАЯ инициализация листа «Список_И_и_ПЗ»
// ============================================================
// ЗАПУСК (проект Apps Script табель_КИП_ИОС — тот же, где
// WorkSchedule.gs): в выпадающем списке функций редактора выбрать
// instrListInit → ▶ Run. Что делает:
//   1) создаёт лист «Список_И_и_ПЗ» с заголовками
//      (название / вид / периодичность / основание);
//   2) заполняет ТИПОВЫМ списком (охрана труда, пожарная
//      безопасность, электробезопасность, проверка знаний) —
//      ОТРЕДАКТИРУЙТЕ под свою номенклатуру: строки добавляются/
//      удаляются прямо в листе; «название» должно совпадать с
//      «темой» записей таблицы «Инструктажи» (регистр/пробелы/«ё»
//      не важны); «вид» — инструктаж или проверка_знаний;
//      «периодичность» — число месяцев (пусто = разовый);
//   3) лист уже есть — ничего не делает (идемпотентно).
// После создания функцию больше запускать не нужно.
function instrListInit() {
  var r = WorkSchedule.instrListInit();
  Logger.log('instrListInit: ' + JSON.stringify(r));
}
""", 'G6 топ-левел instrListInit'))

patch(GS, GS_EDITS)

# ============================================================
# index.html
# ============================================================
IDX_EDITS = []

# I1: форма — datalist подсказок «Темы»
IDX_EDITS.append((
"""            <label class="flow-input-label" for="wsTrTitle">Тема</label>
            <input type="text" id="wsTrTitle" class="flow-input-field-small" placeholder="Повторный инструктаж по ОТ (Q3 2026)" autocomplete="off">
""",
"""            <label class="flow-input-label" for="wsTrTitle">Тема</label>
            <!-- Task 407: подсказки названий из шаблона «Список_И_и_ПЗ»
                 (datalist #wsTrTitleList) — при типе инструктаж/проверка
                 знаний, по «виду» пункта; свободный ввод остаётся
                 (внеплановые темы) -->
            <input type="text" id="wsTrTitle" class="flow-input-field-small" placeholder="Повторный инструктаж по ОТ (Q3 2026)" autocomplete="off" list="wsTrTitleList">
            <datalist id="wsTrTitleList"></datalist>
""", 'I1 datalist формы'))

# I2: состояние — _INSTR_LIST/_INSTR_ALL
IDX_EDITS.append((
"""        _EMPLOYEES: [],
        _ENTRIES: [],
        _TRAININGS: [],
""",
"""        _EMPLOYEES: [],
        _ENTRIES: [],
        _TRAININGS: [],
        // Task 407: каркас блока «Повторные инструктажи и периодическая
        // проверка знаний» — шаблон «Список_И_и_ПЗ» (название/вид/
        // периодичность/основание) и ВСЕ записи «Инструктажей» (без
        // фильтра года — «последний» инструктаж ищется по всем годам).
        // Пустой шаблон (листа нет/сервер старый/кэш прежней версии) —
        // блок живёт плоским списком записей года (как до Task 407)
        _INSTR_LIST: [],
        _INSTR_ALL: [],
""", 'I2 состояние'))

# I3: _loadTrainings — разбор новых полей
IDX_EDITS.append((
"""            return this._api('workSchedule.listTrainings', { year: this._year })
                .then(function(data) {
                    self._TRAININGS = data.trainings || [];
                });
""",
"""            return this._api('workSchedule.listTrainings', { year: this._year })
                .then(function(data) {
                    self._TRAININGS = data.trainings || [];
                    // Task 407: шаблон «Список_И_и_ПЗ» + все записи
                    // «Инструктажей» (старый сервер полей не отдаёт —
                    // пустые массивы, блок без шаблона/без межгодовых
                    // сроков)
                    self._INSTR_LIST = data.instrList || [];
                    self._INSTR_ALL = data.instrAll || [];
                });
""", 'I3 _loadTrainings'))

# I4: _restoreCachedView — восстановление новых полей
IDX_EDITS.append((
"""            this._PPE = Array.isArray(c.ppe) ? c.ppe : [];
""",
"""            this._PPE = Array.isArray(c.ppe) ? c.ppe : [];
            // Task 407: шаблон инструктажей + все записи «Инструктажей»
            // (кэш прежних версий полей не содержит — пустые, блок без
            // шаблона до первого «Обновить»)
            this._INSTR_LIST = Array.isArray(c.instrList) ? c.instrList : [];
            this._INSTR_ALL = Array.isArray(c.instrAll) ? c.instrAll : [];
""", 'I4 кэш-рестор'))

# I5: _cacheWrite — сохранение новых полей
IDX_EDITS.append((
"""                // Task 392: СИЗ — единый список (не по годам)
                c.ppe = this._PPE;
""",
"""                // Task 392: СИЗ — единый список (не по годам)
                c.ppe = this._PPE;
                // Task 407: шаблон инструктажей + все записи
                // «Инструктажей» (не по годам)
                c.instrList = this._INSTR_LIST;
                c.instrAll = this._INSTR_ALL;
""", 'I5 кэш-райт'))

# I6: хелперы — после _isInstrType
IDX_EDITS.append((
"""        _isInstrType: function(тип) {
            var t = String(тип || '').trim().toLowerCase()
                       .replace(/\\s+/g, '_');
            return t === 'инструктаж' || t === 'проверка_знаний';
        },
""",
"""        _isInstrType: function(тип) {
            var t = String(тип || '').trim().toLowerCase()
                       .replace(/\\s+/g, '_');
            return t === 'инструктаж' || t === 'проверка_знаний';
        },

        // Task 407: нормализованный ключ соответствия «тема» записи
        // «Инструктажей» ↔ «название» пункта шаблона «Список_И_и_ПЗ»:
        // регистр/лишние пробелы/«ё» не важны (ручное заполнение)
        _normInstrKey: function(s) {
            return String(s || '').trim().toLowerCase()
                       .replace(/ё/g, 'е')
                       .replace(/\\s+/g, ' ');
        },

        // Task 407: «вид» пункта шаблона / тип записи → инструктаж |
        // проверка_знаний (толерантно, как _isInstrType; пустое
        // значение — инструктаж)
        _normInstrKind: function(вид) {
            var v = String(вид || '').trim().toLowerCase()
                        .replace(/\\s+/g, '_');
            return v === 'проверка_знаний' ? 'проверка_знаний'
                                            : 'инструктаж';
        },

        // Task 407: ISO-дата + N месяцев (день клампится к концу
        // месяца: 31.01 + 1 мес → 28.02) — «следующий срок»
        // периодичного инструктажа от последней записи
        _addMonthsIso: function(iso, months) {
            var p = String(iso || '').split('-');
            if (p.length < 3 || !months) return '';
            var y = parseInt(p[0], 10);
            var m = parseInt(p[1], 10);
            var d = parseInt(p[2], 10);
            if (!y || !m || !d) return '';
            var t = new Date(y, m - 1 + months, 1);
            var dim = new Date(t.getFullYear(), t.getMonth() + 1, 0).getDate();
            t.setDate(Math.min(d, dim));
            return this._isoDate(t);
        },
""", 'I6 хелперы'))

# I7: b5 — ветка шаблона (плоский путь сохранён)
IDX_EDITS.append((
"""            if (!ins.length) {
                b5 += '<div class="ws-emp-empty">нет инструктажей и проверок знаний за год</div>';
            } else {
                for (var ik = 0; ik < ins.length; ik++) {
""",
"""            // Task 407: шаблон «Список_И_и_ПЗ» загружен — ГРУППОВОЙ
            // вид (пункты шаблона + записи года + «следующий срок» +
            // секция «вне списка»); шаблона нет (лист не создан /
            // сервер старый / кэш прежней версии) — прежний ПЛОСКИЙ
            // список записей года
            if (this._INSTR_LIST && this._INSTR_LIST.length) {
                b5 += this._renderInstrSection(ins, tabNo, withEdit,
                                                asBlocks, this._INSTR_LIST);
            } else if (!ins.length) {
                b5 += '<div class="ws-emp-empty">нет инструктажей и проверок знаний за год</div>';
            } else {
                for (var ik = 0; ik < ins.length; ik++) {
""", 'I7 ветка шаблона b5'))

# I8a: CSS — базовые правила (после .ws-ppe-meta светлой темы)
IDX_EDITS.append((
"""    [data-theme="light"] .ws-ppe-name { color: #222; }
    [data-theme="light"] .ws-ppe-meta { color: #777; }
""",
"""    [data-theme="light"] .ws-ppe-name { color: #222; }
    [data-theme="light"] .ws-ppe-meta { color: #777; }
    /* Task 407: блок «Повторные инструктажи и периодическая проверка
       знаний» по ШАБЛОНУ «Список_И_и_ПЗ» — ГРУППЫ: шапка пункта
       (свотч / код И|ПЗ / название / «раз в N мес.»), строки-записи
       года (код + дата + ✎/✕ — .ws-popup-row.ws-il-row), строка
       следующего срока (✓ актуально / ⚠ просрочено — «последний»
       инструктаж ищется по записям ВСЕХ лет), разделитель
       «вне списка» (записи без соответствия шаблону) */
    .ws-il-head {
        display: flex;
        align-items: baseline;
        gap: 6px;
        padding: 5px 10px 2px 8px;
        font-size: 12px;
        line-height: 1.3;
    }
    .ws-il-name {
        color: var(--text-primary, #e0e0e0);
        font-weight: 600;
        overflow-wrap: break-word;
        min-width: 0;
    }
    .ws-il-per {
        color: var(--text-secondary, rgba(255,255,255,0.55));
        font-size: 10.5px;
        white-space: nowrap;
        margin-left: auto;
    }
    .ws-il-row { /* маркер строки-записи года в группе (стили — .ws-popup-row) */ }
    .ws-il-due {
        padding: 1px 10px 5px 8px;
        font-size: 11px;
        color: var(--text-secondary, rgba(255,255,255,0.55));
    }
    .ws-il-due-ok { color: #81c784; }
    .ws-il-due-bad { color: #ef5350; font-weight: 600; }
    [data-theme="light"] .ws-il-name { color: #222; }
    [data-theme="light"] .ws-il-per { color: #777; }
    [data-theme="light"] .ws-il-due { color: #777; }
    [data-theme="light"] .ws-il-due-ok { color: #2e7d32; }
    [data-theme="light"] .ws-il-due-bad { color: #c62828; }
    .ws-il-off {
        padding: 7px 10px 2px 8px;
        font-size: 10.5px;
        letter-spacing: 0.4px;
        color: var(--text-secondary, rgba(255,255,255,0.45));
        font-style: italic;
        border-top: 1px dashed var(--card-border, rgba(255,255,255,0.08));
        margin-top: 4px;
    }
    [data-theme="light"] .ws-il-off { color: #999; }
""", 'I8a CSS база'))

# I8b: CSS — размеры страницы «Работники» (.ws-wcard)
IDX_EDITS.append((
"""    .ws-wcard .ws-ppe-item {
        font-size: 14px;
        /* Task 396: боковой паддинг — полосы-«пилюли» ЗЕБРЫ строк */
        padding: 6px 10px;
    }
    .ws-wcard .ws-ppe-name { font-size: 14px; }
    .ws-wcard .ws-ppe-meta { font-size: 12.5px; }
""",
"""    .ws-wcard .ws-ppe-item {
        font-size: 14px;
        /* Task 396: боковой паддинг — полосы-«пилюли» ЗЕБРЫ строк */
        padding: 6px 10px;
    }
    .ws-wcard .ws-ppe-name { font-size: 14px; }
    .ws-wcard .ws-ppe-meta { font-size: 12.5px; }
    /* Task 407: группы шаблона «Список_И_и_ПЗ» в окне карточки —
       крупнее (как строки СИЗ/мероприятий); строки-записи года —
       компактнее «пилюль» (группы и так делят блок) */
    .ws-wcard .ws-il-head { font-size: 14px; padding: 6px 10px 2px; }
    .ws-wcard .ws-il-name { font-size: 14px; }
    .ws-wcard .ws-il-per { font-size: 12px; }
    .ws-wcard .ws-il-row { font-size: 14px; padding: 4px 10px; }
    .ws-wcard .ws-il-due { font-size: 12.5px; padding: 1px 10px 6px; }
""", 'I8b CSS wcard'))

# I9: _renderInstrSection — метод после _renderWorkerCardPanels
IDX_EDITS.append((
"""            return '<div class="ws-wcol">' + colMain + '</div>' +
                   '<div class="ws-wcol ws-wcol-instr">' + colInstr + '</div>' +
                   '<div class="ws-wcol ws-wcol-ppe">' + colPpe + '</div>';
        },
""",
"""            return '<div class="ws-wcol">' + colMain + '</div>' +
                   '<div class="ws-wcol ws-wcol-instr">' + colInstr + '</div>' +
                   '<div class="ws-wcol ws-wcol-ppe">' + colPpe + '</div>';
        },

        // Task 407: ТЕЛО блока «Повторные инструктажи и периодическая
        // проверка знаний» по ШАБЛОНУ «Список_И_и_ПЗ» (вызывается из
        // _renderWorkerCard, когда шаблон загружен):
        //   • ГРУППА на каждый пункт шаблона (порядок = порядок строк
        //     листа): шапка (свотч/код И|ПЗ по «виду» пункта/название/
        //     «раз в N мес.»), записи ГОДА с ✎/✕ (связка — по
        //     нормализованному названию «тема» ↔ «название»; код
        //     строки — факт записи), строка следующего срока от
        //     ПОСЛЕДНЕЙ записи ЛЮБОГО года («след. срок: … ✓» /
        //     «⚠ просрочено с …»; периодичность 0 = разовый — срок не
        //     считается). Карточка (asBlocks) дополнительно показывает
        //     «— не проводился» / «— в этом году не проводился»; попап
        //     — компактно, без этих строк и без пустых пунктов;
        //   • записи года без соответствия шаблону — секция
        //     «вне списка» (плоские строки, как до Task 407).
        // Дубли названий шаблона — первый пункт (map). Вид записи ≠
        // вид пункта — показываем факт записи, периодичность из шаблона
        _renderInstrSection: function(ins, tabNo, withEdit, asBlocks, iList) {
            var html = '';
            var today = this._isoDate(new Date());
            var map = {}, order = [];
            for (var ii = 0; ii < iList.length; ii++) {
                var key = this._normInstrKey(iList[ii].название);
                if (!key || map[key]) continue;
                map[key] = iList[ii];
                order.push(key);
            }
            // записи работника по ВСЕМ годам («последний» инструктаж):
            // _INSTR_ALL (все «Инструктажи») + срез года ins (запись
            // могла попасть в лист «Мероприятия» вручную) — dedupe
            // по id, только инструктажные типы и записи с датой
            var all = [], seen = {};
            var pool = (this._INSTR_ALL || []).concat(ins || []);
            for (var ai = 0; ai < pool.length; ai++) {
                var ar = pool[ai];
                if (ar['таб_номер'] !== tabNo) continue;
                if (!this._isInstrType(ar.тип)) continue;
                if (!ar.дата_начала) continue;
                var ak = parseInt(ar.id, 10);
                var dedup = ak ? ('i' + ak)
                    : ('t' + ar.дата_начала + '|' + String(ar.тема || ''));
                if (seen[dedup]) continue;
                seen[dedup] = true;
                all.push(ar);
            }
            all.sort(function(a, b) {
                return String(a.дата_начала).localeCompare(String(b.дата_начала));
            });
            // записи года по группам; без соответствия — «вне списка»
            var byKey = {}, offlist = [];
            for (var yi = 0; yi < (ins || []).length; yi++) {
                var yk = this._normInstrKey(ins[yi].тема);
                if (yk && map[yk]) {
                    if (!byKey[yk]) byKey[yk] = [];
                    byKey[yk].push(ins[yi]);
                } else {
                    offlist.push(ins[yi]);
                }
            }
            for (var gi = 0; gi < order.length; gi++) {
                var gKey = order[gi];
                var gItem = map[gKey];
                var gRows = byKey[gKey] || [];
                var last = null;
                for (var li = 0; li < all.length; li++) {
                    if (this._normInstrKey(all[li].тема) === gKey) {
                        last = all[li];
                    }
                }
                // попап: пункты без записей вообще — не показываем
                if (!asBlocks && !gRows.length && !last) continue;
                var gKind = this._normInstrKind(gItem.вид);
                var gCode = gKind === 'проверка_знаний' ? 'ПЗ' : 'И';
                var gMeta = this._statusMeta(gCode) || {};
                html += '<div class="ws-il-head">' +
                        '<span class="ws-popup-swatch" style="background:' +
                        (gMeta.color || '#3a3a3a') + ';"></span>' +
                        '<span class="ws-popup-code">' + this._esc(gCode) + '</span>' +
                        '<span class="ws-il-name">' +
                        this._esc(String(gItem.название || '')) + '</span>' +
                        (gItem.периодичность
                            ? '<span class="ws-il-per">раз в ' + gItem.периодичность + ' ' +
                              this._plural(gItem.периодичность,
                                           ['месяц', 'месяца', 'месяцев']) + '</span>'
                            : '') +
                        '</div>';
                for (var ri = 0; ri < gRows.length; ri++) {
                    var gr = gRows[ri];
                    var rId = parseInt(gr.id, 10);
                    var rActs = '';
                    if (withEdit && rId) {
                        rActs = '<span class="ws-popup-act" title="Редактировать"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.editTraining(' + rId + ')">✎</span>' +
                                '<span class="ws-popup-act ws-popup-act-del" title="Удалить"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.deleteTraining(' + rId + ')">✕</span>';
                    }
                    var rPeriod = (gr.дата_начала === gr.дата_окончания)
                        ? this._fmtDateRu(gr.дата_начала)
                        : (this._fmtDateRu(gr.дата_начала) + ' — ' +
                           this._fmtDateRu(gr.дата_окончания));
                    html += '<div class="ws-popup-row ws-popup-event ws-il-row">' +
                            '<span class="ws-popup-code">' +
                            this._esc(this._trainingCodeOf(gr.тип) || gCode) + '</span>' +
                            '<span class="ws-popup-name">' + rPeriod + '</span>' +
                            rActs + '</div>';
                }
                if (asBlocks && !gRows.length) {
                    html += last
                        ? '<div class="ws-emp-empty">— в этом году не проводился</div>'
                        : '<div class="ws-emp-empty">— не проводился</div>';
                }
                var perN = parseFloat(gItem.периодичность) || 0;
                var dueIso = (last && perN > 0)
                    ? this._addMonthsIso(last.дата_начала, perN) : '';
                if (dueIso) {
                    html += (dueIso < today)
                        ? '<div class="ws-il-due ws-il-due-bad">⚠ просрочено с ' +
                          this._fmtDateRu(dueIso) + '</div>'
                        : '<div class="ws-il-due ws-il-due-ok">след. срок: ' +
                          this._fmtDateRu(dueIso) + ' ✓</div>';
                }
            }
            if (offlist.length) {
                html += '<div class="ws-il-off">вне списка:</div>';
                for (var oi = 0; oi < offlist.length; oi++) {
                    var ot = offlist[oi];
                    var oCode = this._trainingCodeOf(ot.тип);
                    var oMeta = this._statusMeta(oCode) || {};
                    var oId = parseInt(ot.id, 10);
                    var oActs = '';
                    if (withEdit && oId) {
                        oActs = '<span class="ws-popup-act" title="Редактировать"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.editTraining(' + oId + ')">✎</span>' +
                                '<span class="ws-popup-act ws-popup-act-del" title="Удалить"' +
                                ' onclick="event.stopPropagation(); WorkSchedule.deleteTraining(' + oId + ')">✕</span>';
                    }
                    var oPeriod = (ot.дата_начала === ot.дата_окончания)
                        ? this._fmtDateRu(ot.дата_начала)
                        : (this._fmtDateRu(ot.дата_начала) + ' — ' +
                           this._fmtDateRu(ot.дата_окончания));
                    html += '<div class="ws-popup-row ws-popup-event' +
                          ((asBlocks && oi % 2 === 1) ? ' ws-row-alt' : '') + '">' +
                          '<span class="ws-popup-swatch" style="background:' +
                          (oMeta.color || '#3a3a3a') + ';"></span>' +
                          '<span class="ws-popup-code">' + this._esc(oCode || '—') + '</span>' +
                          '<span class="ws-popup-name">' +
                          this._esc(ot.тема || oMeta.name || ot.тип) +
                          ' · ' + oPeriod + '</span>' + oActs + '</div>';
                }
            }
            return html;
        },
""", 'I9 _renderInstrSection'))

# I10: openTrainingForm — datalist подсказок
IDX_EDITS.append((
"""                if (prefillTab) empSel.value = String(prefillTab);
            }
""",
"""                if (prefillTab) empSel.value = String(prefillTab);
            }
            // Task 407: подсказки названий «Темы» из шаблона
            // «Список_И_и_ПЗ» (datalist #wsTrTitleList): тип
            // инструктаж/проверка знаний — названия соответствующего
            // вида; пересбор при смене типа (onchange); свободный
            // ввод остаётся (внеплановые темы)
            var typeSel = document.getElementById('wsTrType');
            if (typeSel) {
                typeSel.onchange = function() {
                    WorkSchedule._fillTrTitleOptions();
                };
            }
            this._fillTrTitleOptions();
""", 'I10 openTrainingForm datalist'))

# I11: _fillTrTitleOptions — метод перед openTrainingForm
IDX_EDITS.append((
"""        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {
""",
"""        // Task 407: пересобрать подсказки поля «Тема» шторки «Новое
        // мероприятие» (datalist #wsTrTitleList) по шаблону
        // «Список_И_и_ПЗ»: тип инструктаж — названия вида «инструктаж»,
        // проверка знаний — «проверка_знаний» (толерантно); прочие
        // типы (обучение/прогул/примечание) — без подсказок (темы
        // свободные). Шаблона нет (лист не создан/сервер старый) —
        // пустой список, ввод свободный
        _fillTrTitleOptions: function() {
            var dl = document.getElementById('wsTrTitleList');
            if (!dl) return;
            var tipEl = document.getElementById('wsTrType');
            var tip = tipEl ? tipEl.value : '';
            var html = '';
            if (this._isInstrType(tip)) {
                var want = this._normInstrKind(tip);
                for (var i = 0; i < (this._INSTR_LIST || []).length; i++) {
                    if (this._normInstrKind(this._INSTR_LIST[i].вид) !== want) {
                        continue;
                    }
                    html += '<option value="' +
                            this._esc(this._INSTR_LIST[i].название) + '"></option>';
                }
            }
            dl.innerHTML = html;
        },

        openTrainingForm: function(prefillTab, prefillDate, editTraining, prefillType) {
""", 'I11 _fillTrTitleOptions'))

patch(IDX, IDX_EDITS)
print('Task 407 patch: DONE')
