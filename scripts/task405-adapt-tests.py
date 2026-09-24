#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 405 — адаптация тестов под разделение таблицы инструктажей.

Сессия оборвалась после применения task405-patch.py и бампа SW (v632),
тесты адаптированы ЧАСТИЧНО — 45 падений. Этот скрипт доводит адаптацию:

  test-work-events.js  — сигнатура openTrainingForm (+prefillType)
  test-tab-numbers.js  — _appendRowKeepText: 5 → 6 вызовов (+splitTrainingsSheet)
  test-task306.js      — G: «прогул»/«примечание» → лист «Мероприятия»
                         (мок insertSheet + стилизация + setFrozenRows)
  test-task384.js      — onEmpAddTraining → openTrainingForm(tabNo, null, null, 'обучение')
  test-task385.js      — HOST_METHODS +_isInstrType; ws-wcard 4 → 5
  test-task388.js      — workersHost +_isInstrType; сводная: две колонки
                         (мероприятия/инструктажи), мок +2 обучения
  test-task393.js      — return [b1..b5] / (b1+b2+b3+b5); хосты +_isInstrType;
                         блоки/окна 4 → 5; новый тест блока 5
  test-task394.js      — хосты +_isInstrType; блок 3 = только НЕ-инструктажи,
                         блок 5 = инструктажи; сводная 2 колонки; 5 панелей
  test-task395.js      — pageHost +_isInstrType; колонка 3 — 2 окна; 5 окон
  test-task396.js      — 6 легаси-строк; хосты +_isInstrType; 5 блоков/
                         6 кнопок; зебра b5; попап с секцией инструктажей
  test-task403.js      — SRC return-строки; 5 блоков; колонка 3 — 2 окна
  test-task404.js      — хосты +_isInstrType; 5 блоков; колонка 3 — 2 окна;
                         ✎/✕ в блоках 3 (обучение) и 5 (инструктаж)
  test-task405.js      — сводка: хост +_isMasterKipia
"""

import io
import sys

BASE = '/home/z/my-project/kip8test'
FAILED = []


def patch(path, repls, label):
    """repls: список (old, new, count) — count=None значит «все вхождения»."""
    full = BASE + '/' + path
    with io.open(full, 'r', encoding='utf-8') as f:
        src = f.read()
    for old, new, cnt in repls:
        n = src.count(old)
        if n == 0:
            FAILED.append('%s: НЕ НАЙДЕНО: %s' % (label, old[:72]))
            continue
        if cnt is not None and n != cnt:
            FAILED.append('%s: ждали %d вхождений, нашли %d: %s'
                          % (label, cnt, n, old[:72]))
            continue
        src = src.replace(old, new)
    with io.open(full, 'w', encoding='utf-8') as f:
        f.write(src)
    print('  ok %s' % path)


ISIN = "methodText(INDEX_SRC, '_isInstrType') + ',\\n' + "


# ------------------------------------------------------------
# 1. test-work-events.js — сигнатура openTrainingForm
# ------------------------------------------------------------
patch('tests/test-work-events.js', [
    (
        "assertTrue(INDEX_SRC.indexOf('openTrainingForm: "
        "function(prefillTab, prefillDate, editTraining)') !== -1,\n"
        "            'сигнатура с параметрами префилла + правки');",
        "assertTrue(INDEX_SRC.indexOf('openTrainingForm: "
        "function(prefillTab, prefillDate, editTraining, prefillType)') !== -1,\n"
        "            'сигнатура с параметрами префилла + правки "
        "(Task 405: +prefillType — тип по умолчанию из кнопки входа)');",
        1),
], 'work-events')

# ------------------------------------------------------------
# 2. test-tab-numbers.js — _appendRowKeepText: 6 вызовов
# ------------------------------------------------------------
patch('tests/test-tab-numbers.js', [
    (
        "assertEqual(uses, 5, 'addEmployee + addTraining + addVacation "
        "+ setManualEntry + addPpe (Task 392)');",
        "assertEqual(uses, 6, 'addEmployee + addTraining + addVacation "
        "+ setManualEntry + addPpe (Task 392) + splitTrainingsSheet "
        '(Task 405: перенос строк в лист «Мероприятия»)\');',
        1),
], 'tab-numbers')

# ------------------------------------------------------------
# 3. test-task306.js — мок insertSheet; G: маршрутизация по типу
# ------------------------------------------------------------
patch('tests/test-task306.js', [
    # мок листа: стилизация/заморозка строки 1 (нужны _ensureEventsSheet)
    (
        "            setNumberFormat(fmt) {\n"
        "                self.fmtCalls.push({ row: row, col: col,\n"
        "                                     numRows: numRows, numCols: numCols, fmt: fmt });\n"
        "            }\n"
        "        };\n"
        "    }\n"
        "    deleteRow(r) { this.rows.splice(r - 1, 1); }\n"
        "    appendRow(arr) { this.rows.push(arr.slice()); }\n"
        "}",
        "            setNumberFormat(fmt) {\n"
        "                self.fmtCalls.push({ row: row, col: col,\n"
        "                                     numRows: numRows, numCols: numCols, fmt: fmt });\n"
        "            },\n"
        "            // Task 405: стилизация заголовка нового листа\n"
        "            // «Мероприятия» (_ensureEventsSheet) — ноу-опы\n"
        "            setFontWeight() { return this; },\n"
        "            setBackground() { return this; },\n"
        "            setFontColor() { return this; }\n"
        "        };\n"
        "    }\n"
        "    deleteRow(r) { this.rows.splice(r - 1, 1); }\n"
        "    appendRow(arr) { this.rows.push(arr.slice()); }\n"
        "    setFrozenRows() {}  // Task 405: _ensureEventsSheet\n"
        "}",
        1),
    # мок ss: insertSheet — автосоздание листа «Мероприятия»
    (
        "function loadWS(sheets) {\n"
        "    const ss = { getSheetByName: (n) => sheets[n] || null };\n"
        "    const SpreadsheetApp = { openById: () => ss };",
        "function loadWS(sheets) {\n"
        "    // Task 405: insertSheet — автосоздание листа «Мероприятия»\n"
        "    // при первой записи «мероприятийного» типа (addTraining)\n"
        "    const ss = {\n"
        "        getSheetByName: (n) => sheets[n] || null,\n"
        "        insertSheet: (name) => {\n"
        "            const s = new MockSheet([]);\n"
        "            sheets[name] = s;\n"
        "            return s;\n"
        "        }\n"
        "    };\n"
        "    const SpreadsheetApp = { openById: () => ss };",
        1),
    # сам тест G: «прогул»/«примечание» → лист «Мероприятия»
    (
        "        const r1 = WS.addTraining({ token: 't', 'таб_номер': '017', тип: 'прогул',\n"
        "                                    тема: 'Не явился', дата_начала: '2026-08-20',\n"
        "                                    дата_окончания: '2026-08-20', длительность_дней: 1,\n"
        "                                    комментарий: '' });\n"
        "        assertTrue(r1.ok, 'addTraining: тип «прогул» принят');\n"
        "        const last = sheets['Инструктажи'].rows[sheets['Инструктажи'].rows.length - 1];\n"
        "        assertEqual(last[2], 'прогул', 'тип записан в лист «Инструктажи»');\n"
        "\n"
        "        const r2 = WS.addTraining({ token: 't', 'таб_номер': '017', тип: 'примечание',\n"
        "                                    тема: 'Перенос по приказу', дата_начала: '2026-08-21' });\n"
        "        assertTrue(r2.ok, 'addTraining: тип «примечание» принят');",
        "        const r1 = WS.addTraining({ token: 't', 'таб_номер': '017', тип: 'прогул',\n"
        "                                    тема: 'Не явился', дата_начала: '2026-08-20',\n"
        "                                    дата_окончания: '2026-08-20', длительность_дней: 1,\n"
        "                                    комментарий: '' });\n"
        "        assertTrue(r1.ok, 'addTraining: тип «прогул» принят');\n"
        "        // Task 405: прогул — «мероприятийный» тип → лист\n"
        "        // «Мероприятия» (создаётся автоматически), НЕ «Инструктажи»\n"
        "        const evSheet = sheets['Мероприятия'];\n"
        "        assertTrue(!!evSheet, 'лист «Мероприятия» создан автоматически');\n"
        "        const last = evSheet.rows[evSheet.rows.length - 1];\n"
        "        assertEqual(last[2], 'прогул', 'тип записан в лист «Мероприятия»');\n"
        "        assertEqual(sheets['Инструктажи'].rows.length, 1,\n"
        "            '«Инструктажи» не тронут (только строка заголовка)');\n"
        "\n"
        "        const r2 = WS.addTraining({ token: 't', 'таб_номер': '017', тип: 'примечание',\n"
        "                                    тема: 'Перенос по приказу', дата_начала: '2026-08-21' });\n"
        "        assertTrue(r2.ok, 'addTraining: тип «примечание» принят');\n"
        "        const last2 = evSheet.rows[evSheet.rows.length - 1];\n"
        "        assertEqual(last2[2], 'примечание',\n"
        "            'примечание — тоже в листе «Мероприятия» (Task 405)');",
        1),
], 'task306')

# ------------------------------------------------------------
# 4. test-task384.js — onEmpAddTraining зовёт с типом «обучение»
# ------------------------------------------------------------
patch('tests/test-task384.js', [
    (
        "        assertTrue(fn.indexOf('this.openTrainingForm(tabNo);') !== -1, 'форма с сотрудником');",
        "        assertTrue(\n"
        "            fn.indexOf(\"this.openTrainingForm(tabNo, null, null, 'обучение');\") !== -1,\n"
        "            'форма с сотрудником и типом «обучение» (Task 405: кнопка блока'\n"
        "            + ' «Мероприятия» — дефолт типа из новой таблицы)');",
        1),
], 'task384')

# ------------------------------------------------------------
# 5. test-task385.js — HOST_METHODS +_isInstrType; ws-wcard 5
# ------------------------------------------------------------
patch('tests/test-task385.js', [
    (
        "        '_trainingCodeOf', '_statusMeta',\n",
        "        '_trainingCodeOf', '_statusMeta',\n"
        "        // Task 405: деление записей по типу (мероприятия/инструктажи)\n"
        "        '_isInstrType',\n",
        1),
    (
        "        assertEqual((body2.match(/ws-wcard/g) || []).length, 4,\n"
        "            'карточка выбранного — ЧЕТЫРЕ блока-окна (Task 393)');",
        "        assertEqual((body2.match(/ws-wcard/g) || []).length, 5,\n"
        "            'карточка выбранного — ПЯТЬ блоков-окон (Task 393 + Task 405)');",
        1),
], 'task385')

# ------------------------------------------------------------
# 6. test-task388.js — workersHost +_isInstrType; сводная 2 колонки
# ------------------------------------------------------------
patch('tests/test-task388.js', [
    (
        "            // Task 390: шапка «Общей» вкладки считает мастеров\n"
        "            methodText(INDEX_SRC, '_isMasterKipia') + ',\\n' +\n"
        "            '_workersTab: \"general\",'",
        "            // Task 390: шапка «Общей» вкладки считает мастеров\n"
        "            methodText(INDEX_SRC, '_isMasterKipia') + ',\\n' +\n"
        "            // Task 405: сводка делит записи по типу\n"
        "            methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "            '_workersTab: \"general\",'",
        1),
    # мок _TRAININGS: + 2 обучения (колонки различимы числом)
    (
        "            '_TRAININGS: [' +\n"
        "            \"  { id: 31, 'таб_номер': '0871', 'тип': 'инструктаж',\" +\n"
        "            \"    'тема': 'ОТ', 'дата_начала': '2026-06-05', 'дата_окончания': '2026-06-05' }\" +\n"
        "            '],' +",
        "            '_TRAININGS: [' +\n"
        "            \"  { id: 31, 'таб_номер': '0871', 'тип': 'инструктаж',\" +\n"
        "            \"    'тема': 'ОТ', 'дата_начала': '2026-06-05', 'дата_окончания': '2026-06-05' },\" +\n"
        "            \"  { id: 32, 'таб_номер': '0871', 'тип': 'обучение',\" +\n"
        "            \"    'тема': 'КУ', 'дата_начала': '2026-07-01', 'дата_окончания': '2026-07-03' },\" +\n"
        "            \"  { id: 33, 'таб_номер': '0871', 'тип': 'обучение',\" +\n"
        "            \"    'тема': 'ПТ', 'дата_начала': '2026-08-11', 'дата_окончания': '2026-08-11' }\" +\n"
        "            '],' +",
        1),
    # сводная: две колонки — мероприятия и инструктажи
    (
        "        assertTrue(ivanovRow.indexOf('>1<') !== -1, 'мероприятие Иванова — 1');",
        "        // Task 405: колонки разделены — мероприятия 2 (обучения),\n"
        "        // инструктажи 1; проверяем пару ячеек целиком\n"
        "        assertTrue(ivanovRow.indexOf('<td>2</td><td>1</td></tr>') !== -1,\n"
        "            'Иванов: мероприятия 2, инструктажи 1 (Task 405)');",
        1),
], 'task388')

# ------------------------------------------------------------
# 7. test-task393.js — return-строка; хосты; 5 блоков; тест b5
# ------------------------------------------------------------
patch('tests/test-task393.js', [
    (
        "        assertTrue(fn.indexOf('return asBlocks ? [b1, b2, b3, b4] : (b1 + b2 + b3);') !== -1,\n"
        "            'массив 4 блоков / склеенная строка (Task 403: попап БЕЗ СИЗ)');",
        "        assertTrue(\n"
        "            fn.indexOf('return asBlocks ? [b1, b2, b3, b4, b5] : (b1 + b2 + b3 + b5);') !== -1,\n"
        "            'массив 5 блоков / склеенная строка (Task 403: попап БЕЗ СИЗ;\n"
        "            'Task 405: +b5 «Повторные инструктажи»)');",
        1),
    # хосты: cardHost + pageHost — оба имеют пару карточка+панели
    (
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        '_canEdit: ' + JSON.stringify(!!withEdit) + ','",
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "        '_canEdit: ' + JSON.stringify(!!withEdit) + ','",
        1),
    (
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        1),
    # asBlocks — 5 блоков
    (
        "        assertEqual(blocks.length, 4, 'ровно 4 блока');",
        "        assertEqual(blocks.length, 5,\n"
        "            'ровно 5 блоков (Task 405: + повторные инструктажи)');",
        1),
    # новый тест блока 5 — после «блок 4 — СИЗ…»
    (
        "    test('зритель — блоки без элементов правки', () => {\n"
        "        const host = cardHost(false, PPE);\n"
        "        const blocks = host._renderWorkerCard('2706', false, true);\n"
        "        assertEqual(blocks.length, 4, '4 блока и у зрителя');",
        "    test('блок 5 — повторные инструктажи года (Task 405)', () => {\n"
        "        const host = cardHost(true, PPE);\n"
        "        const b = host._renderWorkerCard('2706', true, true)[4];\n"
        "        assertTrue(\n"
        "            b.indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,\n"
        "            'заголовок нового блока');\n"
        "        assertTrue(b.indexOf('нет инструктажей и проверок знаний за год') !== -1,\n"
        "            'пустое состояние');\n"
        "        assertTrue(b.indexOf('+ Инструктаж…') !== -1, '«+ Инструктаж…» в блоке 5');\n"
        "        assertTrue(b.indexOf(\"WorkSchedule.onEmpAddInstruction('2706')\") !== -1,\n"
        "            'контракт onclick кнопки');\n"
        "    });\n"
        "\n"
        "    test('зритель — блоки без элементов правки', () => {\n"
        "        const host = cardHost(false, PPE);\n"
        "        const blocks = host._renderWorkerCard('2706', false, true);\n"
        "        assertEqual(blocks.length, 5, '5 блоков и у зрителя');",
        1),
    # зритель: + «+ Инструктаж…» отсутствует
    (
        "                   all.indexOf('+ Мероприятие…') === -1 &&\n"
        "                   all.indexOf('+ СИЗ…') === -1,\n"
        "            'без права записи — блоки без действий');",
        "                   all.indexOf('+ Мероприятие…') === -1 &&\n"
        "                   all.indexOf('+ СИЗ…') === -1 &&\n"
        "                   all.indexOf('+ Инструктаж…') === -1,\n"
        "            'без права записи — блоки без действий');",
        1),
    # панели: 5 обёрток, порядок с b5
    (
        "        assertEqual((html.match(/class=\"ws-wcard\"/g) || []).length, 4,\n"
        "            'ровно четыре окна-панели');\n"
        "        const i1 = html.indexOf('Галкин Д. Н.');\n"
        "        const i2 = html.indexOf('Отпуска · 2026');\n"
        "        const i3 = html.indexOf('Мероприятия · 2026');\n"
        "        const i4 = html.indexOf('СИЗ · средства индивидуальной защиты');\n"
        "        assertTrue(i1 !== -1 && i2 !== -1 && i3 !== -1 && i4 !== -1, 'блоки на месте');\n"
        "        // Task 404: СИЗ — ВТОРАЯ колонка (слева от мероприятий):\n"
        "        // DOM-порядок: профиль → отпуска → СИЗ → мероприятия\n"
        "        assertTrue(i1 < i2 && i2 < i4 && i4 < i3,\n"
        "            'порядок панелей: профиль → отпуска → СИЗ → мероприятия');",
        "        assertEqual((html.match(/class=\"ws-wcard\"/g) || []).length, 5,\n"
        "            'ровно пять окон-панелей');\n"
        "        const i1 = html.indexOf('Галкин Д. Н.');\n"
        "        const i2 = html.indexOf('Отпуска · 2026');\n"
        "        const i3 = html.indexOf('Мероприятия · 2026');\n"
        "        const i4 = html.indexOf('СИЗ · средства индивидуальной защиты');\n"
        "        const i5 = html.indexOf(\n"
        "            'Повторные инструктажи и периодическая проверка знаний · 2026');\n"
        "        assertTrue(i1 !== -1 && i2 !== -1 && i3 !== -1 && i4 !== -1 &&\n"
        "                   i5 !== -1, 'блоки на месте');\n"
        "        // Task 404: СИЗ — ВТОРАЯ колонка (слева от мероприятий);\n"
        "        // Task 405: за мероприятиями — блок повторных инструктажей\n"
        "        // (обе правые колонки — общий стек colTr)\n"
        "        assertTrue(i1 < i2 && i2 < i4 && i4 < i3 && i3 < i5,\n"
        "            'порядок: профиль → отпуска → СИЗ → мероприятия → инструктажи');",
        1),
    # вкладка работника: 5 окон
    (
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 4,\n"
        "            'тело вкладки — четыре блока-окна');",
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 5,\n"
        "            'тело вкладки — пять блоков-окон (Task 405)');",
        1),
    # зритель: 5 окон
    (
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 4,\n"
        "            'четыре окна и у зрителя');",
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 5,\n"
        "            'пять окон и у зрителя');",
        1),
], 'task393')

# ------------------------------------------------------------
# 8. test-task394.js — хосты; блок 3/5 разделение; сводная; панели
# ------------------------------------------------------------
patch('tests/test-task394.js', [
    # cardHost: пара карточка+панели → +_isInstrType (единственное
    # вхождение с '_canEdit: true,' после)
    (
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        '_canEdit: true,'",
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "        '_canEdit: true,'",
        1),
    # pageHost: пара карточка+панели → +_isInstrType
    (
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        1),
    # блок 3: только НЕ-инструктажи; новый блок 5
    (
        "    test('блок 3 — «Мероприятия · 2026»: записи ВСЕХ месяцев года', () => {\n"
        "        const host = cardHost(TRS);\n"
        "        const b = host._renderWorkerCard('2706', true, true)[2];\n"
        "        assertTrue(b.indexOf('Мероприятия · 2026') !== -1,\n"
        "            'заголовок — год (не месяц)');\n"
        "        ['Февральский', 'Июньское', 'Сентябрьское', 'Через Новый год']\n"
        "            .forEach(t => assertTrue(b.indexOf(t) !== -1,\n"
        "                'мероприятие года показано: ' + t));\n"
        "        assertFalse(b.indexOf('Прошлый год') !== -1,\n"
        "            'запись вне года не показывается');\n"
        "        assertFalse(b.indexOf('Чужое') !== -1,\n"
        "            'чужой работник не показывается');\n"
        "        assertFalse(b.indexOf('нет мероприятий за год') !== -1,\n"
        "            'пустого состояния нет');\n"
        "    });",
        "    test('блок 3 — «Мероприятия · 2026»: только НЕ-инструктажи (Task 405)', () => {\n"
        "        const host = cardHost(TRS);\n"
        "        const b = host._renderWorkerCard('2706', true, true)[2];\n"
        "        assertTrue(b.indexOf('Мероприятия · 2026') !== -1,\n"
        "            'заголовок — год (не месяц)');\n"
        "        // Task 405: в блоке мероприятий — только обучение/примечание/\n"
        "        // прогул (новая таблица «Мероприятия»)\n"
        "        assertTrue(b.indexOf('Июньское') !== -1,\n"
        "            'обучение года показано в мероприятиях');\n"
        "        ['Февральский', 'Сентябрьское', 'Через Новый год']\n"
        "            .forEach(t => assertFalse(b.indexOf(t) !== -1,\n"
        "                'инструктаж НЕ в мероприятиях: ' + t));\n"
        "        assertFalse(b.indexOf('Прошлый год') !== -1,\n"
        "            'запись вне года не показывается');\n"
        "        assertFalse(b.indexOf('Чужое') !== -1,\n"
        "            'чужой работник не показывается');\n"
        "        assertFalse(b.indexOf('нет мероприятий за год') !== -1,\n"
        "            'пустого состояния нет');\n"
        "    });\n"
        "\n"
        "    test('блок 5 — повторные инструктажи года (Task 405)', () => {\n"
        "        const host = cardHost(TRS);\n"
        "        const b = host._renderWorkerCard('2706', true, true)[4];\n"
        "        assertTrue(\n"
        "            b.indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,\n"
        "            'заголовок нового блока (таблица «Инструктажи»)');\n"
        "        ['Февральский', 'Сентябрьское', 'Через Новый год']\n"
        "            .forEach(t => assertTrue(b.indexOf(t) !== -1,\n"
        "                'инструктаж года показан: ' + t));\n"
        "        assertFalse(b.indexOf('Июньское') !== -1,\n"
        "            'обучение НЕ в инструктажах');\n"
        "        assertFalse(b.indexOf('Прошлый год') !== -1,\n"
        "            'вне года — не показывается');\n"
        "        assertFalse(b.indexOf('Чужое') !== -1,\n"
        "            'чужой работник — не показывается');\n"
        "    });",
        1),
    # порядок записей — теперь хронология в блоке 5
    (
        "    test('порядок записей года — по дате начала', () => {\n"
        "        const host = cardHost(TRS);\n"
        "        const b = host._renderWorkerCard('2706', true, true)[2];\n"
        "        const i1 = b.indexOf('Через Новый год');\n"
        "        const i2 = b.indexOf('Февральский');\n"
        "        const i3 = b.indexOf('Июньское');\n"
        "        const i4 = b.indexOf('Сентябрьское');\n"
        "        assertTrue(i1 < i2 && i2 < i3 && i3 < i4,\n"
        "            'хронология года: декабрь→февраль→июнь→сентябрь');\n"
        "    });",
        "    test('порядок записей года — по дате начала', () => {\n"
        "        const host = cardHost(TRS);\n"
        "        // Task 405: три инструктажа года — в блоке 5\n"
        "        const b = host._renderWorkerCard('2706', true, true)[4];\n"
        "        const i1 = b.indexOf('Через Новый год');\n"
        "        const i2 = b.indexOf('Февральский');\n"
        "        const i3 = b.indexOf('Сентябрьское');\n"
        "        assertTrue(i1 < i2 && i2 < i3,\n"
        "            'хронология инструктажей года: декабрь→февраль→сентябрь');\n"
        "    });",
        1),
    # попап: + секция повторных инструктажей
    (
        "        assertTrue(html.indexOf('Мероприятия · 2026') !== -1,\n"
        "            'секция года и в попапе');\n"
        "        assertTrue(html.indexOf('Февральский') !== -1 &&\n"
        "                   html.indexOf('Сентябрьское') !== -1,\n"
        "            'записи разных месяцев года в попапе');",
        "        assertTrue(html.indexOf('Мероприятия · 2026') !== -1,\n"
        "            'секция года и в попапе');\n"
        "        assertTrue(html.indexOf('Июньское') !== -1,\n"
        "            'записи месяцев года в попапе (обучение — в мероприятиях)');\n"
        "        // Task 405: инструктажи — своя секция в попапе\n"
        "        assertTrue(\n"
        "            html.indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,\n"
        "            'секция инструктажей и в попапе');\n"
        "        assertTrue(html.indexOf('Февральский') !== -1 &&\n"
        "                   html.indexOf('Сентябрьское') !== -1,\n"
        "            'инструктажи разных месяцев года в попапе');",
        1),
    # вкладка работника: 5 панелей + порядок
    (
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 4,\n"
        "            'в обёртке — ровно четыре блока-окна');\n"
        "        // порядок блоков в DOM: профиль → отпуска → СИЗ → мероприятия\n"
        "        // (Task 404: СИЗ — ВТОРАЯ колонка, слева от мероприятий)\n"
        "        const i1 = body.indexOf('Галкин Д. Н.');\n"
        "        const i2 = body.indexOf('Отпуска · 2026');\n"
        "        const i3 = body.indexOf('Мероприятия · 2026');\n"
        "        const i4 = body.indexOf('СИЗ · средства индивидуальной защиты');\n"
        "        assertTrue(i1 < i2 && i2 < i4 && i4 < i3,\n"
        "            'DOM-порядок = раскладка: профиль|отпуска / СИЗ / мероприятия');",
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 5,\n"
        "            'в обёртке — ровно пять блоков-окон (Task 405)');\n"
        "        // порядок блоков в DOM: профиль → отпуска → СИЗ → мероприятия\n"
        "        // → повторные инструктажи (Task 404 + Task 405)\n"
        "        const i1 = body.indexOf('Галкин Д. Н.');\n"
        "        const i2 = body.indexOf('Отпуска · 2026');\n"
        "        const i3 = body.indexOf('Мероприятия · 2026');\n"
        "        const i4 = body.indexOf('СИЗ · средства индивидуальной защиты');\n"
        "        const i5 = body.indexOf(\n"
        "            'Повторные инструктажи и периодическая проверка знаний · 2026');\n"
        "        assertTrue(i1 < i2 && i2 < i4 && i4 < i3 && i3 < i5,\n"
        "            'DOM-порядок = раскладка: профиль|отпуска / СИЗ /\n"
        "            'мероприятия+инструктажи');",
        1),
    # сводная: две колонки
    (
        "        assertTrue(body.indexOf('<th>Мероприятия · 2026</th>') !== -1,\n"
        "            'колонка сводки — «Мероприятия · 2026» (год)');\n"
        "        // счётчик в ячейке — годовой: у 2706 три записи года\n"
        "        const re = /<tr><td>2706<\\/td>[\\s\\S]*?<td>3<\\/td><\\/tr>/;\n"
        "        assertTrue(re.test(body), 'ячейка Галкина — 3 мероприятия года');",
        "        assertTrue(body.indexOf('<th>Мероприятия · 2026</th>') !== -1,\n"
        "            'колонка сводки — «Мероприятия · 2026» (год)');\n"
        "        // Task 405: инструктажи — СВОЯ колонка сводки\n"
        "        assertTrue(body.indexOf('<th>Инструктажи · 2026</th>') !== -1,\n"
        "            'колонка сводки — «Инструктажи · 2026» (Task 405)');\n"
        "        // счётчики в ячейках: у 2706 — 1 мероприятие (обучение Б)\n"
        "        // и 2 инструктажа (А, В); год, типы разделены\n"
        "        const re = /<tr><td>2706<\\/td>[\\s\\S]*?<td>1<\\/td><td>2<\\/td><\\/tr>/;\n"
        "        assertTrue(re.test(body),\n"
        "            'ячейка Галкина — 1 мероприятие и 2 инструктажа (Task 405)');",
        1),
], 'task394')

# ------------------------------------------------------------
# 9. test-task395.js — pageHost +_isInstrType; колонка 3 — 2 окна
# ------------------------------------------------------------
patch('tests/test-task395.js', [
    (
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        1),
    (
        "        assertEqual((trPart.match(/class=\"ws-wcard\"/g) || []).length, 1,\n"
        "            'колонка 3 — 1 окно (мероприятия)');",
        "        assertEqual((trPart.match(/class=\"ws-wcard\"/g) || []).length, 2,\n"
        "            'колонка 3 — 2 окна (мероприятия + повторные инструктажи, Task 405)');",
        1),
    (
        "        assertTrue(trPart.indexOf('Мероприятия · 2026') !== -1,\n"
        "            'мероприятия — в 3-й колонке (СПРАВА от СИЗ)');",
        "        assertTrue(trPart.indexOf('Мероприятия · 2026') !== -1,\n"
        "            'мероприятия — в 3-й колонке (СПРАВА от СИЗ)');\n"
        "        assertTrue(\n"
        "            trPart.indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,\n"
        "            'Task 405: повторные инструктажи — под мероприятиями (colTr)');",
        1),
    (
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 4,\n"
        "            'всего четыре блока-окна');",
        "        assertEqual((body.match(/class=\"ws-wcard\"/g) || []).length, 5,\n"
        "            'всего пять блоков-окон (Task 405)');",
        1),
], 'task395')

# ------------------------------------------------------------
# 10. test-task396.js — 6 легаси-строк; хосты; 5 блоков/6 кнопок
# ------------------------------------------------------------
patch('tests/test-task396.js', [
    # SRC: легаси-строк теперь 6 (+ «+ Инструктаж…»)
    (
        "        assertEqual(fn.split('if (withEdit && !asBlocks) {').length - 1, 5,\n"
        "            'пять легаси-строк (Правка/Уволить/+Отпуск/+Мероприятие/+СИЗ) — только БЕЗ asBlocks');",
        "        assertEqual(fn.split('if (withEdit && !asBlocks) {').length - 1, 6,\n"
        "            'шесть легаси-строк (Правка/Уволить/+Отпуск/+Мероприятие/\n"
        "            '+Инструктаж/+СИЗ) — только БЕЗ asBlocks (Task 405)');",
        1),
    # cardHost: карточка + _canEdit → +_isInstrType
    (
        "        methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "        '_canEdit: ' + JSON.stringify(!!withEdit) + ','",
        "        methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "        '_canEdit: ' + JSON.stringify(!!withEdit) + ','",
        1),
    # pageHost: карточка + панели → +_isInstrType
    (
        "        methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        "        methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "        '_workersTab: \"general\",'",
        1),
    # четыре блока → пять (+ шапка b5)
    (
        "        const blocks = h._renderWorkerCard('2706', true, true);\n"
        "        assertEqual(blocks.length, 4, 'массив 4 блоков (Task 393)');\n"
        "        blocks.forEach(function(b, i) {\n"
        "            assertTrue(b.indexOf('<div class=\"ws-whead\">') === 0,\n"
        "                'блок ' + (i + 1) + ' НАЧИНАЕТСЯ с шапки-полосы .ws-whead');\n"
        "        });",
        "        const blocks = h._renderWorkerCard('2706', true, true);\n"
        "        assertEqual(blocks.length, 5, 'массив 5 блоков (Task 393 + 405)');\n"
        "        blocks.forEach(function(b, i) {\n"
        "            assertTrue(b.indexOf('<div class=\"ws-whead\">') === 0,\n"
        "                'блок ' + (i + 1) + ' НАЧИНАЕТСЯ с шапки-полосы .ws-whead');\n"
        "        });",
        1),
    (
        "        assertTrue(blocks[3].indexOf('СИЗ · средства индивидуальной защиты') !== -1, 'шапка СИЗ');",
        "        assertTrue(blocks[3].indexOf('СИЗ · средства индивидуальной защиты') !== -1, 'шапка СИЗ');\n"
        "        assertTrue(\n"
        "            blocks[4].indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,\n"
        "            'Task 405: шапка блока повторных инструктажей');\n"
        "        assertTrue(blocks[4].indexOf('ws-whead-wrap') !== -1,\n"
        "            'Task 405: длинный заголовок — с классом переноса');",
        1),
    # кнопки: 6 (+ «+ Инструктаж…»)
    (
        "        assertTrue(blocks[3].indexOf('class=\"ws-wbtn ws-emp-addppe\"') !== -1 &&\n"
        "                   blocks[3].indexOf('WorkSchedule.onEmpAddPpe(\\'2706\\')') !== -1,\n"
        "            '«+ СИЗ…» — в шапке блока СИЗ');\n"
        "        assertEqual((blocks.join('').match(/class=\"ws-wbtn/g) || []).length, 5,\n"
        "            'всего 5 компактных кнопок (2+1+1+1)');",
        "        assertTrue(blocks[3].indexOf('class=\"ws-wbtn ws-emp-addppe\"') !== -1 &&\n"
        "                   blocks[3].indexOf('WorkSchedule.onEmpAddPpe(\\'2706\\')') !== -1,\n"
        "            '«+ СИЗ…» — в шапке блока СИЗ');\n"
        "        assertTrue(blocks[4].indexOf('class=\"ws-wbtn ws-emp-addins\"') !== -1 &&\n"
        "                   blocks[4].indexOf(\"WorkSchedule.onEmpAddInstruction('2706')\") !== -1,\n"
        "            'Task 405: «+ Инструктаж…» — в шапке блока инструктажей');\n"
        "        assertEqual((blocks.join('').match(/class=\"ws-wbtn/g) || []).length, 6,\n"
        "            'всего 6 компактных кнопок (2+1+1+1+1)');",
        1),
    # зебра: b3 — 1 обучение (0 alt), b5 — 3 инструктажа (1 alt)
    (
        "        // b3: 4 мероприятия → 2 alt (2-я и 4-я)\n"
        "        assertEqual((blocks[2].match(/ws-popup-event ws-row-alt/g) || []).length, 2,\n"
        "            'мероприятия: вторая И четвёртая строки — alt');\n"
        "        // b4: 3 СИЗ → 1 alt",
        "        // Task 405: b3 — только обучение (1 запись) → 0 alt\n"
        "        assertEqual((blocks[2].match(/ws-popup-event ws-row-alt/g) || []).length, 0,\n"
        "            'мероприятия: одна запись — без зебры');\n"
        "        assertTrue(blocks[2].indexOf('Пожарная безопасность') !== -1,\n"
        "            'b3: обучение — в мероприятиях (Task 405)');\n"
        "        // Task 405: b5 — 3 инструктажа → 1 alt (вторая строка)\n"
        "        assertEqual((blocks[4].match(/ws-popup-event ws-row-alt/g) || []).length, 1,\n"
        "            'инструктажи: вторая строка — alt');\n"
        "        assertTrue(blocks[4].indexOf('Охрана труда') !== -1 &&\n"
        "                   blocks[4].indexOf('Первая помощь') !== -1 &&\n"
        "                   blocks[4].indexOf('Экзамен') !== -1,\n"
        "            'b5: инструктажи и проверка знаний (с пробелом!) — в блоке 5');\n"
        "        // b4: 3 СИЗ → 1 alt",
        1),
    # зритель: 5 блоков, зебра в b5
    (
        "        assertEqual(blocks.length, 4, 'блоки рендерятся');\n"
        "        blocks.forEach(function(b) {\n"
        "            assertTrue(b.indexOf('ws-wbtn') === -1, 'кнопок действий НЕТ у зрителя');\n"
        "        });\n"
        "        assertTrue(blocks[0].indexOf('ws-whead') !== -1 &&\n"
        "                   blocks[2].indexOf('ws-popup-event ws-row-alt') !== -1,\n"
        "            'шапки-оглавления и ЗЕБРА — видны всем (не правка)');",
        "        assertEqual(blocks.length, 5, 'блоки рендерятся (Task 405: 5)');\n"
        "        blocks.forEach(function(b) {\n"
        "            assertTrue(b.indexOf('ws-wbtn') === -1, 'кнопок действий НЕТ у зрителя');\n"
        "        });\n"
        "        assertTrue(blocks[0].indexOf('ws-whead') !== -1 &&\n"
        "                   blocks[4].indexOf('ws-popup-event ws-row-alt') !== -1,\n"
        "            'шапки-оглавления и ЗЕБРА — видны всем (зебра теперь в b5)');",
        1),
    # легаси-попап: 5 строк-действий (+ Инструктаж)
    (
        "        assertTrue(html.indexOf('ws-popup-row ws-popup-more ws-emp-editdata') !== -1 &&\n"
        "                   html.indexOf('ws-popup-row ws-popup-more ws-emp-dismiss') !== -1 &&\n"
        "                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addvac') !== -1 &&\n"
        "                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addtr') !== -1,\n"
        "            'четыре строки-действия — прежний вид (попап-совместимость)');",
        "        assertTrue(html.indexOf('ws-popup-row ws-popup-more ws-emp-editdata') !== -1 &&\n"
        "                   html.indexOf('ws-popup-row ws-popup-more ws-emp-dismiss') !== -1 &&\n"
        "                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addvac') !== -1 &&\n"
        "                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addtr') !== -1 &&\n"
        "                   html.indexOf('ws-popup-row ws-popup-more ws-emp-addins') !== -1,\n"
        "            'пять строк-действий — прежний вид (+ «+ Инструктаж…», Task 405)');",
        1),
    # попап шахматки: секция инструктажей
    (
        "        assertTrue(html.indexOf('<div class=\"ws-popup-sec\">Отпуска · 2026') !== -1,\n"
        "            'секции отпусков/мероприятий — прежние .ws-popup-sec');",
        "        assertTrue(html.indexOf('<div class=\"ws-popup-sec\">Отпуска · 2026') !== -1,\n"
        "            'секции отпусков/мероприятий — прежние .ws-popup-sec');\n"
        "        assertTrue(\n"
        "            html.indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,\n"
        "            'Task 405: секция инструктажей — в попапе (после мероприятий)');",
        1),
    # страница: 5 шапок + 6 кнопок
    (
        "        assertEqual((body.match(/<div class=\"ws-whead\">/g) || []).length, 4,\n"
        "            'четыре блока-окна — каждый с шапкой-полосой');\n"
        "        assertEqual((body.match(/class=\"ws-wbtn/g) || []).length, 5,\n"
        "            '5 компактных кнопок (2 в профиле + 3 «+ …»)');",
        "        assertEqual((body.match(/<div class=\"ws-whead\">/g) || []).length, 5,\n"
        "            'пять блоков-окон — каждый с шапкой-полосой (Task 405)');\n"
        "        assertEqual((body.match(/class=\"ws-wbtn/g) || []).length, 6,\n"
        "            '6 компактных кнопок (2 в профиле + 4 «+ …»)');",
        1),
], 'task396')

# ------------------------------------------------------------
# 11. test-task403.js — return-строки; 5 блоков; колонка 3 — 2 окна
# ------------------------------------------------------------
patch('tests/test-task403.js', [
    (
        "        assertTrue(fn.indexOf('return asBlocks ? [b1, b2, b3, b4] : (b1 + b2 + b3);') !== -1,\n"
        "            'попап (без asBlocks) — только профиль + отпуска + мероприятия');",
        "        assertTrue(\n"
        "            fn.indexOf('return asBlocks ? [b1, b2, b3, b4, b5] : (b1 + b2 + b3 + b5);') !== -1,\n"
        "            'попап (без asBlocks) — профиль + отпуска + мероприятия\n"
        "            '+ инструктажи (Task 405), БЕЗ СИЗ');",
        1),
    (
        "        assertTrue(fn.indexOf('[b1, b2, b3, b4]') !== -1,\n"
        "            'asBlocks — по-прежнему 4 блока (страница «Работники»)');",
        "        assertTrue(fn.indexOf('[b1, b2, b3, b4, b5]') !== -1,\n"
        "            'asBlocks — 5 блоков (Task 405: + повторные инструктажи)');",
        1),
    # cardHost: +_isInstrType
    (
        "        return new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            '_canEdit: ' + JSON.stringify(!!withEdit) + ','",
        "        return new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "            '_canEdit: ' + JSON.stringify(!!withEdit) + ','",
        1),
    # asBlocks: 5 блоков
    (
        "        const blocks = host._renderWorkerCard('2706', true, true);\n"
        "        assertEqual(blocks.length, 4, 'четыре блока');\n"
        "        assertTrue(blocks[0].indexOf('Галкин Д. Н.') !== -1, 'блок 1 — профиль');\n"
        "        assertTrue(blocks[1].indexOf('Отпуска · 2026') !== -1, 'блок 2 — отпуска');\n"
        "        assertTrue(blocks[2].indexOf('Мероприятия · 2026') !== -1, 'блок 3 — мероприятия');\n"
        "        assertTrue(blocks[3].indexOf('СИЗ · средства индивидуальной защиты') !== -1,\n"
        "            'блок 4 — СИЗ (страница «Работники»)');\n",
        "        const blocks = host._renderWorkerCard('2706', true, true);\n"
        "        assertEqual(blocks.length, 5, 'пять блоков (Task 405)');\n"
        "        assertTrue(blocks[0].indexOf('Галкин Д. Н.') !== -1, 'блок 1 — профиль');\n"
        "        assertTrue(blocks[1].indexOf('Отпуска · 2026') !== -1, 'блок 2 — отпуска');\n"
        "        assertTrue(blocks[2].indexOf('Мероприятия · 2026') !== -1, 'блок 3 — мероприятия');\n"
        "        assertTrue(blocks[3].indexOf('СИЗ · средства индивидуальной защиты') !== -1,\n"
        "            'блок 4 — СИЗ (страница «Работники»)');\n"
        "        assertTrue(\n"
        "            blocks[4].indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,\n"
        "            'Task 405: блок 5 — повторные инструктажи (пустое состояние)');\n",
        1),
    # 403→404 панели-хост: +_isInstrType; колонка 3 — 2 окна
    (
        "        const host = new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "            '_canEdit: true, _year: 2026, _month: 8,'",
        "        const host = new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "            '_canEdit: true, _year: 2026, _month: 8,'",
        1),
    (
        "        assertEqual((trPart.match(/class=\"ws-wcard\"/g) || []).length, 1,\n"
        "            'колонка 3 — 1 окно (мероприятия)');",
        "        assertEqual((trPart.match(/class=\"ws-wcard\"/g) || []).length, 2,\n"
        "            'колонка 3 — 2 окна (мероприятия + инструктажи, Task 405)');",
        1),
    (
        "        const iPz = ppePart.indexOf('СИЗ · средства индивидуальной защиты');\n"
        "        const iTr = trPart.indexOf('Мероприятия · 2026');\n"
        "        assertTrue(iPz !== -1 && iTr !== -1, 'СИЗ и мероприятия на месте');",
        "        const iPz = ppePart.indexOf('СИЗ · средства индивидуальной защиты');\n"
        "        const iTr = trPart.indexOf('Мероприятия · 2026');\n"
        "        assertTrue(iPz !== -1 && iTr !== -1, 'СИЗ и мероприятия на месте');\n"
        "        // Task 405: «Инструктаж» с заглавной — тоже b5 (толерантность)\n"
        "        assertTrue(trPart.indexOf('Повторные инструктажи') !== -1 &&\n"
        "                   trPart.indexOf('ОТ') !== -1,\n"
        "            'инструктаж — в колонке 3, в блоке повторных инструктажей');",
        1),
], 'task403')

# ------------------------------------------------------------
# 12. test-task404.js — хосты; 5 блоков; колонка 3 — 2 окна; ✎/✕
# ------------------------------------------------------------
patch('tests/test-task404.js', [
    # cardHost: +_isInstrType и мок + обучение id 6
    (
        "        return new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "            '_canEdit: true, _year: 2026, _month: 8,'",
        "        return new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "            '_canEdit: true, _year: 2026, _month: 8,'",
        1),
    (
        "            '_TRAININGS: ' + JSON.stringify([{\n"
        "                id: 5, 'таб_номер': '2706', 'тип': 'Инструктаж', 'тема': 'ОТ',\n"
        "                'дата_начала': '2026-02-10', 'дата_окончания': '2026-02-10' }]) + ',' +\n"
        "            '_PPE: ' + JSON.stringify([{\n"
        "                id: 3, 'таб_номер': '2706', наименование: 'Каска защитная',",
        "            '_TRAININGS: ' + JSON.stringify([{\n"
        "                id: 5, 'таб_номер': '2706', 'тип': 'Инструктаж', 'тема': 'ОТ',\n"
        "                'дата_начала': '2026-02-10', 'дата_окончания': '2026-02-10' },\n"
        "              { id: 6, 'таб_номер': '2706', 'тип': 'обучение', 'тема': 'КУ',\n"
        "                'дата_начала': '2026-03-02', 'дата_окончания': '2026-03-02' }]) + ',' +\n"
        "            '_PPE: ' + JSON.stringify([{\n"
        "                id: 3, 'таб_номер': '2706', наименование: 'Каска защитная',",
        1),
    # три колонки: колонка 3 — 2 окна
    (
        "        assertEqual((trPart.match(/class=\"ws-wcard\"/g) || []).length, 1,\n"
        "            'колонка 3 — мероприятия');",
        "        assertEqual((trPart.match(/class=\"ws-wcard\"/g) || []).length, 2,\n"
        "            'колонка 3 — мероприятия + инструктажи (Task 405)');",
        1),
    (
        "        assertTrue(iL + iProf < iP + iPz && iP + iPz < iT + iTr,\n"
        "            'визуальный порядок: профиль → СИЗ → мероприятия');",
        "        assertTrue(iL + iProf < iP + iPz && iP + iPz < iT + iTr,\n"
        "            'визуальный порядок: профиль → СИЗ → мероприятия');\n"
        "        // Task 405: за мероприятиями — блок повторных инструктажей\n"
        "        const iIns = trPart.indexOf('Повторные инструктажи');\n"
        "        assertTrue(iIns > iTr, 'инструктажи — ПОД мероприятиями (colTr)');",
        1),
    # ✎/✕: 5 блоков, обучение — b3, инструктаж — b5
    (
        "        const blocks = host._renderWorkerCard('2706', true, true);\n"
        "        assertEqual(blocks.length, 4, 'четыре блока');",
        "        const blocks = host._renderWorkerCard('2706', true, true);\n"
        "        assertEqual(blocks.length, 5, 'пять блоков (Task 405)');",
        1),
    (
        "        // мероприятия\n"
        "        const iEt = blocks[2].indexOf('WorkSchedule.editTraining(5)');\n"
        "        const iDt = blocks[2].indexOf('WorkSchedule.deleteTraining(5)');\n"
        "        assertTrue(iEt !== -1 && iDt !== -1 && iEt < iDt,\n"
        "            'мероприятие: ✎ и ✕ — оба, ✎ первым');",
        "        // мероприятия (Task 405: в b3 — обучение id 6)\n"
        "        const iEt = blocks[2].indexOf('WorkSchedule.editTraining(6)');\n"
        "        const iDt = blocks[2].indexOf('WorkSchedule.deleteTraining(6)');\n"
        "        assertTrue(iEt !== -1 && iDt !== -1 && iEt < iDt,\n"
        "            'мероприятие (обучение): ✎ и ✕ — оба, ✎ первым');\n"
        "        // инструктаж (Task 405: в b5 — «Инструктаж» id 5)\n"
        "        const iEi = blocks[4].indexOf('WorkSchedule.editTraining(5)');\n"
        "        const iDi = blocks[4].indexOf('WorkSchedule.deleteTraining(5)');\n"
        "        assertTrue(iEi !== -1 && iDi !== -1 && iEi < iDi,\n"
        "            'инструктаж: ✎ и ✕ — в блоке 5, ✎ первым');",
        1),
    # зритель-хост: +_isInstrType
    (
        "        const host = new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            '_canEdit: false, _year: 2026, _month: 8,'",
        "        const host = new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "            '_canEdit: false, _year: 2026, _month: 8,'",
        1),
], 'task404')

# ------------------------------------------------------------
# 13. test-task405.js — сводка: хост +_isMasterKipia
# ------------------------------------------------------------
patch('tests/test-task405.js', [
    (
        "        const host = new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "            '_year: 2026,'",
        "        const host = new Function('document', 'return ({' +\n"
        "            methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_isInstrType') + ',\\n' +\n"
        "            methodText(INDEX_SRC, '_isMasterKipia') + ',\\n' +\n"
        "            '_year: 2026,'",
        1),
], 'task405')

print()
if FAILED:
    print('ОШИБКИ АДАПТАЦИИ (%d):' % len(FAILED))
    for m in FAILED:
        print('  ✗ ' + m)
    sys.exit(1)
print('Все адаптации применены успешно.')
