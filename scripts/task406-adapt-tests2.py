#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 406 (kip8test): адаптация тестов — ЧАСТЬ 2 (VM-секции 394/395,
найдены прогоном run-all после первой адаптации)."""
import io
import sys

BASE = '/home/z/my-project/kip8test/tests/'
fail = 0


def patch(fname, repl):
    global fail
    path = BASE + fname
    src = io.open(path, encoding='utf-8').read()
    orig = src
    for old, new, tag in repl:
        n = src.count(old)
        if n != 1:
            print('FAIL %s [%s]: вхождений %d' % (fname, tag, n))
            fail += 1
            continue
        src = src.replace(old, new)
        print('OK %s [%s]' % (fname, tag))
    if src != orig and not fail:
        io.open(path, 'w', encoding='utf-8').write(src)


# ---------- test-task394.js: DOM-порядок на странице ----------
patch('test-task394.js', [
    ("""        // порядок блоков в DOM: профиль → отпуска → СИЗ → мероприятия
        // → повторные инструктажи (Task 404 + Task 405)
        const i1 = body.indexOf('Галкин Д. Н.');
        const i2 = body.indexOf('Отпуска · 2026');
        const i3 = body.indexOf('Мероприятия · 2026');
        const i4 = body.indexOf('СИЗ · средства индивидуальной защиты');
        const i5 = body.indexOf(
            'Повторные инструктажи и периодическая проверка знаний · 2026');
        assertTrue(i1 < i2 && i2 < i4 && i4 < i3 && i3 < i5,
            'DOM-порядок = раскладка: профиль|отпуска / СИЗ / '
            + 'мероприятия+инструктажи');""",
     """        // порядок блоков в DOM: профиль → отпуска → мероприятия →
        // инструктажи → СИЗ (Task 406)
        const i1 = body.indexOf('Галкин Д. Н.');
        const i2 = body.indexOf('Отпуска · 2026');
        const i3 = body.indexOf('Мероприятия · 2026');
        const i4 = body.indexOf('СИЗ · средства индивидуальной защиты');
        const i5 = body.indexOf(
            'Повторные инструктажи и периодическая проверка знаний · 2026');
        assertTrue(i1 !== -1 && i2 !== -1 && i3 !== -1 && i4 !== -1 &&
                   i5 !== -1 && i1 < i2 && i2 < i3 && i3 < i5 && i5 < i4,
            'DOM-порядок = раскладка (Task 406): профиль|отпуска|'
            + 'мероприятия / инструктажи / СИЗ');""",
     'dom-порядок'),
])

# ---------- test-task395.js: VM-колонки + страница ----------
patch('test-task395.js', [
    ("""    test('колонки: 1 — профиль+отпуска; 2 — СИЗ; 3 — мероприятия (Task 404)', () => {
        const t = pageHost({ canEdit: true });
        const html = t.host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iP = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        const iT = html.indexOf('<div class="ws-wcol ws-wcol-tr">');
        assertTrue(iL !== -1 && iP !== -1 && iT !== -1 && iL < iP && iP < iT,
            'ТРИ колонки: main → СИЗ → мероприятия');
        const mainPart = html.slice(iL, iP);
        const ppePart = html.slice(iP, iT);
        const trPart = html.slice(iT);
        assertEqual((mainPart.match(/class="ws-wcard"/g) || []).length, 2,
            'колонка 1 — 2 окна (профиль + отпуска)');
        assertEqual((ppePart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 2 — 1 окно (СИЗ)');
        assertEqual((trPart.match(/class="ws-wcard"/g) || []).length, 2,
            'колонка 3 — 2 окна (мероприятия + повторные инструктажи, Task 405)');
        assertTrue(ppePart.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'СИЗ — во 2-й колонке (СЛЕВА от мероприятий)');
        assertTrue(ppePart.indexOf('Каска защитная') !== -1,
            'запись СИЗ — во 2-й колонке');
        assertTrue(trPart.indexOf('Мероприятия · 2026') !== -1,
            'мероприятия — в 3-й колонке (СПРАВА от СИЗ)');
        assertTrue(
            trPart.indexOf('Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,
            'Task 405: повторные инструктажи — под мероприятиями (colTr)');
        const i1 = mainPart.indexOf('Галкин Д. Н.');
        const i2 = mainPart.indexOf('Отпуска · 2026');
        assertTrue(i1 !== -1 && i2 !== -1 && i1 < i2,
            'порядок колонки 1: профиль → отпуска');
        assertTrue(mainPart.indexOf('СИЗ · средства') === -1 &&
                   mainPart.indexOf('Мероприятия · 2026') === -1,
            'в колонке 1 — только профиль и отпуска');
    });""",
     """    test('колонки: 1 — профиль+отпуска+мероприятия; 2 — инструктажи; 3 — СИЗ (Task 406)', () => {
        const t = pageHost({ canEdit: true });
        const html = t.host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iI = html.indexOf('<div class="ws-wcol ws-wcol-instr">');
        const iP = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        assertTrue(iL !== -1 && iI !== -1 && iP !== -1 && iL < iI && iI < iP,
            'ТРИ колонки: main → инструктажи → СИЗ (Task 406)');
        const mainPart = html.slice(iL, iI);
        const insPart = html.slice(iI, iP);
        const ppePart = html.slice(iP);
        assertEqual((mainPart.match(/class="ws-wcard"/g) || []).length, 3,
            'колонка 1 — 3 окна (профиль + отпуска + мероприятия, Task 406)');
        assertEqual((insPart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 2 — 1 окно (повторные инструктажи)');
        assertEqual((ppePart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 3 — 1 окно (СИЗ)');
        assertTrue(insPart.indexOf(
            'Повторные инструктажи и периодическая проверка знаний · 2026') !== -1,
            'Task 406: инструктажи — ВТОРАЯ колонка');
        assertTrue(ppePart.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            'СИЗ — в 3-й колонке (СПРАВА от инструктажей)');
        assertTrue(ppePart.indexOf('Каска защитная') !== -1,
            'запись СИЗ — в 3-й колонке');
        const i1 = mainPart.indexOf('Галкин Д. Н.');
        const i2 = mainPart.indexOf('Отпуска · 2026');
        const i3 = mainPart.indexOf('Мероприятия · 2026');
        assertTrue(i1 !== -1 && i2 !== -1 && i3 !== -1 &&
                   i1 < i2 && i2 < i3,
            'порядок колонки 1: профиль → отпуска → мероприятия');
        assertTrue(mainPart.indexOf('СИЗ · средства') === -1 &&
                   mainPart.indexOf('Повторные инструктажи') === -1,
            'в колонке 1 — без СИЗ и инструктажей');
    });""",
     'vm-колонки'),

    ("""        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-ppe">') !== -1,
            'вторая колонка (СИЗ) — на странице');
        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-tr">') !== -1,
            'третья колонка (мероприятия) — на странице (Task 404)');""",
     """        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-instr">') !== -1,
            'вторая колонка (инструктажи) — на странице (Task 406)');
        assertTrue(body.indexOf('<div class="ws-wcol ws-wcol-ppe">') !== -1,
            'третья колонка (СИЗ) — на странице (Task 406)');""",
     'страница-колонки'),
])

if fail:
    print('АДАПТАЦИЯ-2 НЕ ЗАВЕРШЕНА: %d ошибок' % fail)
    sys.exit(1)
print('Адаптация-2 тестов Task 406 завершена')
