#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 409 — заявка: эталон раздела инструктажей/проверки знаний.

1) WorkSchedule.gs — instrListInit теперь ЗАМЕЩАЕТ строки листа
   «Список_И_и_ПЗ» эталонной номенклатурой заявки 409 — РОВНО 5
   пунктов (2 повторных инструктажа + 3 периодические проверки
   знаний; п.5 основание = «инструкция № 53-ОТ», периодичность 12).
2) index.html — НОВЫЙ _fmtPeriodRu: 12 мес → «раз в год», 24 →
   «раз в 2 года», 3/6 → «раз в 3 месяца/6 месяцев»; шапка группы
   блока и подсказка формы переведены на него.
3) Тесты 407/408 адаптированы (хосты + ассерты), run-all +409.
"""
import io

ROOT = '/home/z/my-project/kip8test'
IDX = ROOT + '/index.html'
GS = ROOT + '/scripts/WorkSchedule.gs'
T407 = ROOT + '/tests/test-task407.js'
T408 = ROOT + '/tests/test-task408.js'
RUNALL = ROOT + '/tests/run-all.js'


def patch(path, repl):
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    total = 0
    for old, new, cnt in repl:
        found = s.count(old)
        if found == 0 and new in s:
            print('  SKIP (уже применено): %r' % old[:50])
            continue
        assert found == cnt, ('FAIL %s: найдено %d, ожидалось %d: %r'
                               % (path, found, cnt, old[:80]))
        s = s.replace(old, new)
        total += found
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: %d правок' % (path.split('/')[-1], total))


# ============================================================
# 1. WorkSchedule.gs
# ============================================================
GS_OLD_PREAMBLE = """  // Task 407: разовая инициализация листа «Список_И_и_ПЗ» — создать
  // лист с заголовками (название/вид/периодичность/основание) и
  // типовым наполнением (пользователь редактирует под свою
  // номенклатуру: «название» = «тема» записей «Инструктажей»,
  // «периодичность» — число месяцев, пусто = разовый). Лист уже
  // есть — только отчёт (идемпотентно). Через API приложения НЕ
  // доступен — запуск в редакторе Apps Script (instrListInit, как
  // trainingsSplitInit)"""

GS_NEW_PREAMBLE = """  // Task 407/409: инициализация листа «Список_И_и_ПЗ» — создать
  // лист с заголовками (название/вид/периодичность/основание) и
  // заполнить ЭТАЛОННОЙ номенклатурой заявки 409 — ровно 5
  // пунктов (2 повторных инструктажа + 3 периодические проверки
  // знаний; «название» = «тема» записей «Инструктажей»,
  // «периодичность» — число месяцев, пусто = разовый). Лист уже
  // есть — строки ЗАМЕЩАЮТСЯ эталоном (Task 409). Через API
  // приложения НЕ доступен — запуск в редакторе Apps Script
  // (instrListInit, как trainingsSplitInit)"""

GS_OLD_BODY = """  instrListInit: function() {
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
  }"""

GS_NEW_BODY = """  instrListInit: function() {
    // Task 409: эталонная номенклатура заявки — РОВНО 5 пунктов;
    // повторный запуск ЗАМЕЩАЕТ строки листа эталоном
    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);
    var sheet = ss.getSheetByName(this.INSTR_LIST_SHEET);
    var created = !sheet;
    if (!sheet) {
      sheet = ss.insertSheet(this.INSTR_LIST_SHEET);
    }
    var headers = ['название', 'вид', 'периодичность', 'основание'];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length)
      .setFontWeight('bold').setBackground('#1F4E5F').setFontColor('#FFFFFF');
    sheet.setFrozenRows(1);
    var items = [
      ['Повторный инструктаж по рабочим инструкциям ОТ',
       'инструктаж', 6, ''],
      ['Повторный инструктаж по инструкции № 9-ОГЭ',
       'инструктаж', 3, ''],
      ['Периодическая проверка знаний на допуск к самостоятельной работе',
       'проверка_знаний', 12, ''],
      ['Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В',
       'проверка_знаний', 12, ''],
      ['Периодическая проверка знаний по охране труда при выполнении работ на высоте',
       'проверка_знаний', 12, 'инструкция № 53-ОТ']
    ];
    var lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      sheet.getRange(2, 1, lastRow - 1, headers.length).clearContent();
    }
    sheet.getRange(2, 1, items.length, headers.length).setValues(items);
    try {
      Utils.audit('', created ? 'WORKSCHEDULE_INSTR_LIST_SHEET_CREATED'
                              : 'WORKSCHEDULE_INSTR_LIST_SHEET_RESET', '', '',
        created
          ? 'Создан лист «Список_И_и_ПЗ» (Task 407 — шаблонный список инструктажей и проверок знаний; Task 409 — эталон заявки)'
          : 'Лист «Список_И_и_ПЗ» приведён к эталону заявки 409 (5 пунктов)');
    } catch (e) { /* ignore */ }
    return { ok: true, created: created, reset: !created,
             rows: items.length };
  }"""

GS_OLD_TOPDOC = """// ============================================================
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
// После создания функцию больше запускать не нужно."""

GS_NEW_TOPDOC = """// ============================================================
// Task 407/409: инициализация листа «Список_И_и_ПЗ»
// ============================================================
// ЗАПУСК (проект Apps Script табель_КИП_ИОС — тот же, где
// WorkSchedule.gs): в выпадающем списке функций редактора выбрать
// instrListInit → ▶ Run. Что делает:
//   1) создаёт лист «Список_И_и_ПЗ» с заголовками
//      (название / вид / периодичность / основание), если его нет;
//   2) заполняет ЭТАЛОННОЙ номенклатурой заявки 409 — РОВНО 5
//      пунктов (повторные инструктажи по рабочим инструкциям ОТ и
//      № 9-ОГЭ; периодические проверки знаний: допуск к
//      самостоятельной работе, электроустановки до 1000 В, работы
//      на высоте); правьте прямо в листе: строки добавляются/
//      удаляются; «название» должно совпадать с «темой» записей
//      таблицы «Инструктажи» (регистр/пробелы/«ё» не важны);
//      «вид» — инструктаж или проверка_знаний; «периодичность» —
//      число месяцев (пусто = разовый);
//   3) лист уже есть — ЗАМЕЩАЕТ строки эталоном 5 пунктов
//      (Task 409: прежние образцы/правки будут заменены — не
//      запускайте после ручного заполнения списка)."""

# ============================================================
# 2. index.html
# ============================================================
IDX_OLD_PLURAL = """        // Русская форма множественного: 1 часть / 2 части / 5 частей
        _plural: function(n, forms) {
            var a = Math.abs(n) % 100;
            var b = a % 10;
            if (a > 10 && a < 20) return forms[2];
            if (b > 1 && b < 5) return forms[1];
            if (b === 1) return forms[0];
            return forms[2];
        },"""

IDX_NEW_PLURAL = """        // Русская форма множественного: 1 часть / 2 части / 5 частей
        _plural: function(n, forms) {
            var a = Math.abs(n) % 100;
            var b = a % 10;
            if (a > 10 && a < 20) return forms[2];
            if (b > 1 && b < 5) return forms[1];
            if (b === 1) return forms[0];
            return forms[2];
        },

        // Task 409: периодичность по-русски: 12 мес → «раз в год»,
        // 24 → «раз в 2 года», 36 → «раз в 3 года», 6 → «раз в
        // 6 месяцев», 3 → «раз в 3 месяца», 1 → «раз в месяц»;
        // 0/пусто → '' (разовый — не показывается)
        _fmtPeriodRu: function(n) {
            n = parseFloat(n) || 0;
            if (n <= 0) return '';
            var forms = function(k, f) {
                var a = Math.abs(k) % 100, b = a % 10;
                if (a > 10 && a < 20) return f[2];
                if (b > 1 && b < 5) return f[1];
                if (b === 1) return f[0];
                return f[2];
            };
            if (n % 12 === 0) {
                var y = Math.round(n / 12);
                return 'раз в ' + (y === 1 ? '' : y + ' ') +
                       forms(y, ['год', 'года', 'лет']);
            }
            return 'раз в ' + (n === 1 ? '' : String(n).replace('.', ',') + ' ') +
                   forms(n, ['месяц', 'месяца', 'месяцев']);
        },"""

IDX_OLD_HEAD = """                        (gItem.периодичность
                            ? '<span class="ws-il-per">раз в ' + gItem.периодичность + ' ' +
                              this._plural(gItem.периодичность,
                                           ['месяц', 'месяца', 'месяцев']) + '</span>'
                            : '') +"""

IDX_NEW_HEAD = """                        (gItem.периодичность
                            ? '<span class="ws-il-per">' +
                              this._fmtPeriodRu(gItem.периодичность) + '</span>'
                            : '') +"""

IDX_OLD_HINT = """                    if (per > 0) {
                        txt = 'раз в ' + per + ' ' +
                              this._plural(per, ['месяц', 'месяца', 'месяцев']);
                    }"""

IDX_NEW_HINT = """                    if (per > 0) {
                        // Task 409: «раз в год» для 12 мес
                        txt = this._fmtPeriodRu(per);
                    }"""

# ============================================================
# 3. tests/test-task407.js
# ============================================================
T407_OLD_HDR = """//    по всем годам); instrListInit — разовое создание листа с
//    типовым наполнением (идемпотентно)."""

T407_NEW_HDR = """//    по всем годам); instrListInit — создание листа с эталоном
//    заявки 409 (5 пунктов; повторный запуск замещает строки)."""

T407_OLD_INIT_TEST = """    test('instrListInit: создание листа + идемпотентность', () => {
        const fn = stripComments(methodText(WS_SRC, 'instrListInit'));
        assertTrue(fn.indexOf('exists: true') !== -1,
            'лист уже есть — только отчёт (идемпотентно)');
        assertTrue(fn.indexOf("ss.insertSheet(this.INSTR_LIST_SHEET)") !== -1,
            'создание листа');
        assertTrue(fn.indexOf("'название', 'вид', 'периодичность', 'основание'") !== -1,
            'заголовки столбцов');
        assertTrue(fn.indexOf("'Охрана труда'") !== -1 &&
                   fn.indexOf("'Электробезопасность'") !== -1,
            'типовое наполнение (4 пункта)');
        assertTrue(WS_SRC.indexOf('Task 407: РАЗОВАЯ инициализация листа «Список_И_и_ПЗ»') !== -1,
            'инструкция запуска в редакторе (как trainingsSplitInit)');
    });"""

T407_NEW_INIT_TEST = """    test('instrListInit: создание листа + замещение эталоном (Task 409)', () => {
        const fn = stripComments(methodText(WS_SRC, 'instrListInit'));
        assertTrue(fn.indexOf('reset: !created') !== -1,
            'лист уже есть — замещение строк (reset)');
        assertTrue(fn.indexOf("ss.insertSheet(this.INSTR_LIST_SHEET)") !== -1,
            'создание листа');
        assertTrue(fn.indexOf("'название', 'вид', 'периодичность', 'основание'") !== -1,
            'заголовки столбцов');
        assertTrue(fn.indexOf("'Повторный инструктаж по рабочим инструкциям ОТ'") !== -1 &&
                   fn.indexOf("'Периодическая проверка знаний на допуск к самостоятельной работе'") !== -1,
            'эталонная номенклатура заявки 409');
        assertTrue(fn.indexOf('clearContent') !== -1,
            'перед записью — очистка прежних строк');
        assertTrue(WS_SRC.indexOf('Task 407/409: инициализация листа «Список_И_и_ПЗ»') !== -1,
            'инструкция запуска в редакторе (как trainingsSplitInit)');
    });"""

T407_OLD_PER = """        assertTrue(fn.indexOf('ws-il-per') !== -1 &&
                   fn.indexOf("['месяц', 'месяца', 'месяцев']") !== -1,
            'подпись «раз в N месяцев»');"""

T407_NEW_PER = """        assertTrue(fn.indexOf('ws-il-per') !== -1 &&
                   fn.indexOf('this._fmtPeriodRu(gItem.периодичность)') !== -1,
            'подпись периодичности — _fmtPeriodRu (Task 409: «раз в год»)');"""

T407_OLD_HOST = """            methodText(INDEX_SRC, '_addMonthsIso') + ',\\n' +
            methodText(INDEX_SRC, '_isoDate') + ',\\n' +"""

T407_NEW_HOST = """            methodText(INDEX_SRC, '_addMonthsIso') + ',\\n' +
            methodText(INDEX_SRC, '_isoDate') + ',\\n' +
            methodText(INDEX_SRC, '_fmtPeriodRu') + ',\\n' +"""

# ============================================================
# 4. tests/test-task408.js
# ============================================================
T408_OLD_HOST1 = """            methodText(INDEX_SRC, '_normInstrKey') + ',\\n' +
            '_esc: function(s) { return String(s); },' +"""

T408_NEW_HOST1 = """            methodText(INDEX_SRC, '_normInstrKey') + ',\\n' +
            methodText(INDEX_SRC, '_fmtPeriodRu') + ',\\n' +
            '_esc: function(s) { return String(s); },' +"""

T408_OLD_HOST2 = """            methodText(INDEX_SRC, '_addMonthsIso') + ',\\n' +
            methodText(INDEX_SRC, '_isoDate') + ',\\n' +"""

T408_NEW_HOST2 = """            methodText(INDEX_SRC, '_addMonthsIso') + ',\\n' +
            methodText(INDEX_SRC, '_isoDate') + ',\\n' +
            methodText(INDEX_SRC, '_fmtPeriodRu') + ',\\n' +"""

# ============================================================
# 5. tests/run-all.js
# ============================================================
RA_OLD = """require('./test-task408.js');
require('./test-deploy-url.js');"""

RA_NEW = """require('./test-task408.js');
// Task 409 — эталон «Список_И_и_ПЗ» (5 пунктов заявки; instrListInit —
// замещение); периодичность «раз в год» (_fmtPeriodRu)
require('./test-task409.js');
require('./test-deploy-url.js');"""


def main():
    patch(GS, [
        (GS_OLD_PREAMBLE, GS_NEW_PREAMBLE, 1),
        (GS_OLD_BODY, GS_NEW_BODY, 1),
        (GS_OLD_TOPDOC, GS_NEW_TOPDOC, 1),
    ])
    patch(IDX, [
        (IDX_OLD_PLURAL, IDX_NEW_PLURAL, 1),
        (IDX_OLD_HEAD, IDX_NEW_HEAD, 1),
        (IDX_OLD_HINT, IDX_NEW_HINT, 1),
    ])
    patch(T407, [
        (T407_OLD_HDR, T407_NEW_HDR, 1),
        (T407_OLD_INIT_TEST, T407_NEW_INIT_TEST, 1),
        (T407_OLD_PER, T407_NEW_PER, 1),
        (T407_OLD_HOST, T407_NEW_HOST, 2),  # sectionHost + cardHost
    ])
    patch(T408, [
        (T408_OLD_HOST1, T408_NEW_HOST1, 1),
        (T408_OLD_HOST2, T408_NEW_HOST2, 1),
    ])
    patch(RUNALL, [
        (RA_OLD, RA_NEW, 1),
    ])
    print('OK — Task 409 патч применён')


if __name__ == '__main__':
    main()
