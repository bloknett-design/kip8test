#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 409 — адаптация тестов: GAS-VM тесты 407 (замещение вместо
идемпотентности) + фиксы черновых багов test-task409.js."""
import io

ROOT = '/home/z/my-project/kip8test'
T407 = ROOT + '/tests/test-task407.js'
T409 = ROOT + '/tests/test-task409.js'


def patch(path, repl):
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    total = 0
    for old, new, cnt in repl:
        found = s.count(old)
        assert found == cnt, ('FAIL %s: найдено %d, ожидалось %d: %r'
                               % (path, found, cnt, old[:80]))
        s = s.replace(old, new)
        total += found
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: %d правок' % (path.split('/')[-1], total))


# ---------- test-task407.js: GAS-VM ----------

T407_OLD_CREATE = """    test('instrListInit: создаёт лист с заголовками и типовым списком', () => {
        const sheets = baseSheets();
        const WS = loadWS(sheets);
        const r = WS.instrListInit();
        assertTrue(r.ok && r.created === true, 'лист создан');
        const s = sheets['Список_И_и_ПЗ'];
        assertTrue(!!s, 'лист «Список_И_и_ПЗ» в таблице');
        assertEqual(5, s.rows.length, 'заголовок + 4 типовых пункта');
        assertEqual('название', s.rows[0][0], 'заголовок 1');
        assertEqual('вид', s.rows[0][1], 'заголовок 2');
        assertEqual('периодичность', s.rows[0][2], 'заголовок 3');
        assertEqual('основание', s.rows[0][3], 'заголовок 4');
        assertEqual('Охрана труда', s.rows[1][0], 'пункт 1');
        assertEqual(6, s.rows[1][2], 'периодичность пункта 1');
        // чтение сразу работает
        const lr = WS.listTrainings({ token: 't', year: 2026, month: 8 });
        assertEqual(4, lr.data.instrList.length, 'шаблон читается после init');
    });"""

T407_NEW_CREATE = """    test('instrListInit: создаёт лист с заголовками и эталоном (Task 409)', () => {
        const sheets = baseSheets();
        const WS = loadWS(sheets);
        const r = WS.instrListInit();
        assertTrue(r.ok && r.created === true, 'лист создан');
        const s = sheets['Список_И_и_ПЗ'];
        assertTrue(!!s, 'лист «Список_И_и_ПЗ» в таблице');
        assertEqual(6, s.rows.length, 'заголовок + 5 пунктов эталона');
        assertEqual('название', s.rows[0][0], 'заголовок 1');
        assertEqual('вид', s.rows[0][1], 'заголовок 2');
        assertEqual('периодичность', s.rows[0][2], 'заголовок 3');
        assertEqual('основание', s.rows[0][3], 'заголовок 4');
        assertEqual('Повторный инструктаж по рабочим инструкциям ОТ',
            s.rows[1][0], 'пункт 1 — эталон заявки 409');
        assertEqual(6, s.rows[1][2], 'периодичность пункта 1');
        assertEqual('инструкция № 53-ОТ', s.rows[5][3],
            'основание пункта «работы на высоте»');
        // чтение сразу работает
        const lr = WS.listTrainings({ token: 't', year: 2026, month: 8 });
        assertEqual(5, lr.data.instrList.length, 'шаблон читается после init');
    });"""

T407_OLD_IDEM = """    test('instrListInit: идемпотентно — существующий лист не трогает', () => {
        const sheets = withListSheet(baseSheets());
        const WS = loadWS(sheets);
        const before = JSON.stringify(sheets['Список_И_и_ПЗ'].rows);
        const r = WS.instrListInit();
        assertTrue(r.ok && r.exists === true, 'лист уже есть — только отчёт');
        assertEqual(4, r.rows, 'строк данных в отчёте');
        assertEqual(before, JSON.stringify(sheets['Список_И_и_ПЗ'].rows),
            'содержимое листа НЕ изменено');
    });"""

T407_NEW_IDEM = """    test('instrListInit: существующий лист — строки замещаются эталоном (Task 409)', () => {
        const sheets = withListSheet(baseSheets());
        const WS = loadWS(sheets);
        const r = WS.instrListInit();
        assertTrue(r.ok && r.reset === true, 'лист уже есть — reset (замещение)');
        assertEqual(5, r.rows, 'строк данных в отчёте');
        const s = sheets['Список_И_и_ПЗ'];
        assertEqual(6, s.rows.length, 'заголовок + 5 пунктов эталона');
        assertEqual('название', s.rows[0][0], 'заголовок приведён к эталону');
        assertEqual('Повторный инструктаж по инструкции № 9-ОГЭ',
            s.rows[2][0], 'пункт 2 эталона');
        assertTrue(s.rows.every(rr => rr[1] !== 'Проверка знаний'),
            'прежнее содержимое (столбцы в другом порядке) замещено');
        // чтение после замещения работает
        const lr = WS.listTrainings({ token: 't', year: 2026, month: 8 });
        assertEqual(5, lr.data.instrList.length, 'шаблон читается после reset');
    });"""

# ---------- test-task409.js: фиксы черновика ----------

T409_OLD_I = """        assertEqual(2, (html.match(/>И</g) || []).length, 'код И ×2');
        assertEqual(3, (html.match(/>ПЗ</g) || []).length, 'код ПЗ ×3');"""

T409_NEW_I = """        // код И ×3: две шапки групп + строка записи (тоже с кодом)
        assertEqual(3, (html.match(/>И</g) || []).length, 'код И: 2 шапки + запись');
        assertEqual(3, (html.match(/>ПЗ</g) || []).length, 'код ПЗ ×3');"""

T409_OLD_DUE = """    const INS = [
        { id: 21, 'таб_номер': TAB, 'тип': 'инструктаж',
          'тема': 'Повторный инструктаж по рабочим инструкциям ОТ',
          'дата_начала': '2026-02-10', 'дата_окончания': '2026-02-10' }
    ];"""

T409_NEW_DUE = """    // дата записи 10.04.2026 + 6 мес = 10.10.2026 — «след. срок»
    // всегда в будущем относительно даты прогона (2026-09-25+)
    const INS = [
        { id: 21, 'таб_номер': TAB, 'тип': 'инструктаж',
          'тема': 'Повторный инструктаж по рабочим инструкциям ОТ',
          'дата_начала': '2026-04-10', 'дата_окончания': '2026-04-10' }
    ];"""

T409_OLD_DUE2 = """        assertTrue(seg.indexOf('след. срок: 10.08.2026') !== -1,
            'запись 10.02.2026 + 6 мес');"""

T409_NEW_DUE2 = """        assertTrue(seg.indexOf('след. срок: 10.10.2026') !== -1,
            'запись 10.04.2026 + 6 мес');"""

T409_OLD_SUB = """        assertTrue(h.indexOf('работы на высоте') !== -1, 'высота предложена');"""

T409_NEW_SUB = """        assertTrue(h.indexOf('при выполнении работ на высоте') !== -1,
            'высота предложена');"""

T409_OLD_PER12 = """        assertEqual(3, rows[5][2], 'периодичность 12');"""

T409_NEW_PER12 = """        assertEqual(12, rows[5][2], 'периодичность 12');"""


def main():
    patch(T407, [
        (T407_OLD_CREATE, T407_NEW_CREATE, 1),
        (T407_OLD_IDEM, T407_NEW_IDEM, 1),
    ])
    patch(T409, [
        (T409_OLD_I, T409_NEW_I, 1),
        (T409_OLD_DUE, T409_NEW_DUE, 1),
        (T409_OLD_DUE2, T409_NEW_DUE2, 1),
        (T409_OLD_SUB, T409_NEW_SUB, 1),
        (T409_OLD_PER12, T409_NEW_PER12, 1),
    ])
    print('OK — адаптация завершена')


if __name__ == '__main__':
    main()
