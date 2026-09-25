#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 413 — заявка: «При добавлении инструктажа или проверки знаний в
форме ввода в приложении, они не добавляются, ещё я удалил таблицу
Инструктажи в файле табель_КИП_ИОС... Где должны сохраняться вновь
создаваемые записи в этом разделе? Что нужно сделать чтобы был их
архив?».

ДИААГНОЗ: записи раздела пишутся в лист «Инструктажи» файла
табель_КИП_ИОС; лист удалён пользователем → addTraining возвращал
'sheet_not_found: Инструктажи' (для «Мероприятий» автосоздание было,
Task 405, для «Инструктажей» — нет); listTrainings при отсутствии
листа падал ошибкой → вся загрузка сетки с тостом ошибки.

ПРАВКИ:
  WorkSchedule.gs:
    1) _ensureTrainingsSheet — автосоздание листа «Инструктажи» с
       каноническими заголовками (зеркально _ensureEventsSheet 405);
    2) addTraining — при отсутствии ЛЮБОГО листа вызывает
       соответствующий ensure (архив восстанавливается первым же
       добавлением записи);
    3) listTrainings — мягкая деградация без листа: trainings/instrAll
       пустые, «Мероприятия»/«Список_И_и_ПЗ» читаются независимо;
    4) док-блоки (шапка + структура листа).
  index.html:
    5) _apiErrText — понятный русский текст для 'sheet_not_found: X'
       (пока у пользователя старый WorkSchedule.gs в Apps Script);
    6) submitTrainingForm/_doDeleteTraining/loadGrid — тосты/экран
       ошибки через _apiErrText (раньше сырой err.message).
"""
import io

ROOT = '/home/z/my-project/kip8test'


def patch(path, pairs):
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    for i, (old, new) in enumerate(pairs, 1):
        if s.count(old) != 1:
            raise SystemExit('правка %d: старый текст встречается %d раз (ожидался 1):\n%s'
                             % (i, s.count(old), old[:200]))
        if old == new:
            raise SystemExit('правка %d: old == new' % i)
        s = s.replace(old, new)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: %d правок OK' % (path, len(pairs)))


# ============================================================
# WorkSchedule.gs
# ============================================================
GS = ROOT + '/scripts/WorkSchedule.gs'

gs_pairs = [
    # 1) шапка — перечень эндпоинтов
    (
        "//   workSchedule.addTraining      — добавить плановое мероприятие\n"
        "//   workSchedule.deleteTraining   — удалить мероприятие\n",
        "//   workSchedule.addTraining      — добавить плановое мероприятие\n"
        "//                                   (Task 413: лист «Инструктажи»/\n"
        "//                                   «Мероприятия» удалён — создаётся\n"
        "//                                   автоматически с заголовками)\n"
        "//   workSchedule.deleteTraining   — удалить мероприятие\n",
    ),
    # 2) док-блок структуры листа «Инструктажи»
    (
        "//   G: длительность_дней (int)\n"
        "//   H: комментарий\n"
        "//\n"
        "// Структура листа «Мероприятия» (Task 405 — вторая половина\n",
        "//   G: длительность_дней (int)\n"
        "//   H: комментарий\n"
        "//   Task 413: лист может быть удалён вручную — addTraining\n"
        "//   создаёт его автоматически (заголовки/стили,\n"
        "//   _ensureTrainingsSheet), listTrainings без листа — пустые\n"
        "//   списки, не ошибка: архив записей восстанавливается\n"
        "//   первым же добавлением\n"
        "//\n"
        "// Структура листа «Мероприятия» (Task 405 — вторая половина\n",
    ),
    # 3) новый метод _ensureTrainingsSheet — после _ensureEventsSheet
    (
        "    try {\n"
        "      Utils.audit('', 'WORKSCHEDULE_EVENTS_SHEET_CREATED', '', '',\n"
        "        'Создан лист «Мероприятия» (Task 405 — разделение таблицы инструктажей)');\n"
        "    } catch (e) { /* ignore */ }\n"
        "    return sheet;\n"
        "  },\n"
        "\n"
        "  _requireRead: function(token) {\n",
        "    try {\n"
        "      Utils.audit('', 'WORKSCHEDULE_EVENTS_SHEET_CREATED', '', '',\n"
        "        'Создан лист «Мероприятия» (Task 405 — разделение таблицы инструктажей)');\n"
        "    } catch (e) { /* ignore */ }\n"
        "    return sheet;\n"
        "  },\n"
        "\n"
        "  // Task 413: создать лист «Инструктажи» с каноническими\n"
        "  // заголовками (зеркально _ensureEventsSheet Task 405).\n"
        "  // Причина: лист был удалён из файла вручную — добавление\n"
        "  // записей падало ошибкой sheet_not_found, а listTrainings не\n"
        "  // отдавал данные. Вызывается addTraining при отсутствии\n"
        "  // листа: архив записей восстанавливается первым же\n"
        "  // добавлением (заголовки + строка); лист уже есть —\n"
        "  // возвращается как есть\n"
        "  _ensureTrainingsSheet: function() {\n"
        "    var ss = SpreadsheetApp.openById(this.SPREADSHEET_ID);\n"
        "    var sheet = ss.getSheetByName(this.TRAININGS_SHEET);\n"
        "    if (sheet) return sheet;\n"
        "    try {\n"
        "      sheet = ss.insertSheet(this.TRAININGS_SHEET);\n"
        "    } catch (e) {\n"
        "      // гонка одновременных добавлений: лист создал другой вызов\n"
        "      sheet = ss.getSheetByName(this.TRAININGS_SHEET);\n"
        "      if (!sheet) return null;\n"
        "    }\n"
        "    var headers = ['id', 'таб_номер', 'тип', 'тема', 'дата_начала',\n"
        "                   'дата_окончания', 'длительность_дней', 'комментарий'];\n"
        "    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);\n"
        "    sheet.getRange(1, 1, 1, headers.length)\n"
        "      .setFontWeight('bold').setBackground('#1F4E5F').setFontColor('#FFFFFF');\n"
        "    sheet.setFrozenRows(1);\n"
        "    try {\n"
        "      Utils.audit('', 'WORKSCHEDULE_TRAININGS_SHEET_CREATED', '', '',\n"
        "        'Создан лист «Инструктажи» (Task 413 — автосоздание при добавлении записи; лист был удалён)');\n"
        "    } catch (e) { /* ignore */ }\n"
        "    return sheet;\n"
        "  },\n"
        "\n"
        "  _requireRead: function(token) {\n",
    ),
    # 4) addTraining — автосоздание ОБЕИХ листов
    (
        "    // Task 405: лист записи — по ТИПУ мероприятия (инструктаж/\n"
        "    // проверка_знаний → «Инструктажи»; обучение/прогул/примечание →\n"
        "    // «Мероприятия», лист создаётся при первой записи, если нет)\n"
        "    var sheetName = this._trainingsSheetForType(tip);\n"
        "    var sheet = this._getSheet(sheetName);\n"
        "    if (!sheet && sheetName === this.EVENTS_SHEET) {\n"
        "      sheet = this._ensureEventsSheet();\n"
        "    }\n"
        "    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + sheetName };",
        "    // Task 405: лист записи — по ТИПУ мероприятия (инструктаж/\n"
        "    // проверка_знаний → «Инструктажи»; обучение/прогул/примечание →\n"
        "    // «Мероприятия», лист создаётся при первой записи, если нет).\n"
        "    // Task 413: ОБА листа создаются автоматически (лист\n"
        "    // «Инструктажи» был удалён вручную — добавление падало\n"
        "    // sheet_not_found; архив записей восстанавливается первым\n"
        "    // же добавлением)\n"
        "    var sheetName = this._trainingsSheetForType(tip);\n"
        "    var sheet = this._getSheet(sheetName);\n"
        "    if (!sheet) {\n"
        "      sheet = (sheetName === this.EVENTS_SHEET)\n"
        "        ? this._ensureEventsSheet()\n"
        "        : this._ensureTrainingsSheet();\n"
        "    }\n"
        "    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + sheetName };",
    ),
    # 5) listTrainings — мягкая деградация без листа «Инструктажи»
    (
        "    var sheet = this._getSheet(this.TRAININGS_SHEET);\n"
        "    if (!sheet) return { ok: false, error: 'sheet_not_found: ' + this.TRAININGS_SHEET };\n"
        "\n"
        "    // Task 405: мероприятие может лежать в ОДНОМ ИЗ ДВУХ листов —\n"
        "    // «Инструктажи» (инструктаж/проверка_знаний) или «Мероприятия»\n"
        "    // (обучение/прогул/примечание; формат A..H тот же). Ответ —\n"
        "    // ОБЪЕДИНЁННЫЙ список обоих листов (бейджи/окна/печать/генерация\n"
        "    // видят все мероприятия вместе, нумерация id сквозная). Листа\n"
        "    // «Мероприятия» может не быть (до разделения данных) — тогда\n"
        "    // отдаются только «Инструктажи»\n"
        "    var trainings = this._readTrainingsSheet(sheet, payload);\n"
        "    var evSheet = this._getSheet(this.EVENTS_SHEET);",
        "    // Task 413: лист «Инструктажи» может отсутствовать (удалён\n"
        "    // вручную) — чтение НЕ падает: trainings/instrAll — пустые\n"
        "    // срезы, «Мероприятия» и «Список_И_и_ПЗ» читаются независимо.\n"
        "    // Лист создастся автоматически при первом добавлении записи\n"
        "    // (addTraining → _ensureTrainingsSheet)\n"
        "    var sheet = this._getSheet(this.TRAININGS_SHEET);\n"
        "    var trainings = sheet ? this._readTrainingsSheet(sheet, payload) : [];\n"
        "\n"
        "    // Task 405: мероприятие может лежать в ОДНОМ ИЗ ДВУХ листов —\n"
        "    // «Инструктажи» (инструктаж/проверка_знаний) или «Мероприятия»\n"
        "    // (обучение/прогул/примечание; формат A..H тот же). Ответ —\n"
        "    // ОБЪЕДИНЁННЫЙ список обоих листов (бейджи/окна/печать/генерация\n"
        "    // видят все мероприятия вместе, нумерация id сквозная). Любого\n"
        "    // листа может не быть — отдаются имеющиеся (Task 413)\n"
        "    var evSheet = this._getSheet(this.EVENTS_SHEET);",
    ),
    # 6) listTrainings — instrAll только при живом листе
    (
        "      instrAll:  this._readTrainingsSheet(sheet, {}),\n",
        "      instrAll:  sheet ? this._readTrainingsSheet(sheet, {}) : [],\n",
    ),
]

# ============================================================
# index.html
# ============================================================
IDX = ROOT + '/index.html'

idx_pairs = [
    # 7) _apiErrText — понятный текст для sheet_not_found
    (
        "        _apiErrText: function(err) {\n"
        "            if (err && err.serverMessage) return err.serverMessage;\n"
        "            if (err && err.message) return err.message;\n"
        "            return String(err || 'ошибка');\n"
        "        },\n",
        "        _apiErrText: function(err) {\n"
        "            if (err && err.serverMessage) return err.serverMessage;\n"
        "            if (err && err.message) {\n"
        "                // Task 413: таблица удалена из файла вручную —\n"
        "                // сервер отдаёт 'sheet_not_found: <имя листа>'.\n"
        "                // Обновлённый WorkSchedule.gs создаёт лист\n"
        "                // автоматически при первом добавлении записи; до\n"
        "                // обновления — понятный текст вместо кода ошибки\n"
        "                var sm = /^sheet_not_found:\\s*(.+?)\\s*$/.exec(err.message);\n"
        "                if (sm) {\n"
        "                    return 'таблица «' + sm[1] + '» отсутствует в ' +\n"
        "                           'файле табель_КИП_ИОС — обновите ' +\n"
        "                           'WorkSchedule.gs в Apps Script: она будет ' +\n"
        "                           'создана автоматически при первом ' +\n"
        "                           'добавлении записи';\n"
        "                }\n"
        "                return err.message;\n"
        "            }\n"
        "            return String(err || 'ошибка');\n"
        "        },\n",
    ),
    # 8) submitTrainingForm (новая запись) — тост через _apiErrText
    (
        "            }).catch(function(err) {\n"
        "                if (typeof KipToast !== 'undefined' && KipToast.show) {\n"
        "                    KipToast.show('Ошибка: ' + (err.message || err));\n"
        "                }\n"
        "            });\n"
        "        },\n"
        "\n"
        "        deleteTraining: function(id) {\n",
        "            }).catch(function(err) {\n"
        "                if (typeof KipToast !== 'undefined' && KipToast.show) {\n"
        "                    // Task 413: понятный текст ошибок сервера\n"
        "                    // (sheet_not_found → «таблица отсутствует…»)\n"
        "                    KipToast.show('Ошибка: ' + self._apiErrText(err));\n"
        "                }\n"
        "            });\n"
        "        },\n"
        "\n"
        "        deleteTraining: function(id) {\n",
    ),
    # 9) _doDeleteTraining — тост через _apiErrText
    (
        "                .catch(function(err) {\n"
        "                    if (typeof KipToast !== 'undefined' && KipToast.show) {\n"
        "                        KipToast.show('Ошибка: ' + (err.message || err));\n"
        "                    }\n"
        "                });\n"
        "        },\n"
        "\n"
        "        // ============================================================\n"
        "        // Task 308: страница «Отпуска» удалена — initVacationsPage/\n",
        "                .catch(function(err) {\n"
        "                    if (typeof KipToast !== 'undefined' && KipToast.show) {\n"
        "                        // Task 413: понятный текст ошибок сервера\n"
        "                        KipToast.show('Ошибка: ' + self._apiErrText(err));\n"
        "                    }\n"
        "                });\n"
        "        },\n"
        "\n"
        "        // ============================================================\n"
        "        // Task 308: страница «Отпуска» удалена — initVacationsPage/\n",
    ),
    # 10) loadGrid catch — экран ошибки и тост через _apiErrText
    (
        "                if (!keepGrid && wrapEl) {\n"
        "                    wrapEl.innerHTML = '<div class=\"admin-empty\">Ошибка загрузки: ' + (err.message || err) + '</div>';\n"
        "                }\n"
        "                // Task 264: окошко календаря рисуем и при ошибке загрузки\n"
        "                // сетки — календарь не зависит от бэкенда шахматки\n"
        "                self._updateCalChip();\n"
        "                if (typeof KipToast !== 'undefined' && KipToast.show) {\n"
        "                    KipToast.show('Ошибка загрузки графика: ' + (err.message || err));\n"
        "                }\n",
        "                if (!keepGrid && wrapEl) {\n"
        "                    // Task 413: понятный текст ошибок сервера\n"
        "                    wrapEl.innerHTML = '<div class=\"admin-empty\">Ошибка загрузки: ' + self._apiErrText(err) + '</div>';\n"
        "                }\n"
        "                // Task 264: окошко календаря рисуем и при ошибке загрузки\n"
        "                // сетки — календарь не зависит от бэкенда шахматки\n"
        "                self._updateCalChip();\n"
        "                if (typeof KipToast !== 'undefined' && KipToast.show) {\n"
        "                    // Task 413: понятный текст ошибок сервера\n"
        "                    KipToast.show('Ошибка загрузки графика: ' + self._apiErrText(err));\n"
        "                }\n",
    ),
]

patch(GS, gs_pairs)
patch(IDX, idx_pairs)
print('Task 413: патч применён')
