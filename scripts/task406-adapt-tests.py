#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 406 (kip8test): адаптация тестов к новой раскладке карточки
«Работники» (мероприятия — под отпусками в 1-й колонке; 2-я —
инструктажи .ws-wcol-instr; 3-я — СИЗ .ws-wcol-ppe).

Файлы: test-task403.js (SRC + VM), test-task404.js (SRC + VM),
test-task405.js (SRC «панели»), test-task393.js (VM порядок),
test-task395.js (SRC колонки).
"""
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


# ---------- test-task403.js ----------
patch('test-task403.js', [
    ("""    test('_renderWorkerCardPanels: ТРИ колонки — СИЗ СЛЕВА от мероприятий (Task 404)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf('else if (bi === 3) colPpe += panel;') !== -1,
            'СИЗ (блок 4) — ВТОРАЯ колонка (слева от мероприятий)');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol ws-wcol-tr\\">' + colTr + '</div>'") !== -1,
            'ТРЕТЬЯ колонка .ws-wcol-tr — мероприятия (справа от СИЗ)');
    });""",
     """    test('_renderWorkerCardPanels: ТРИ колонки — инструктажи вторая, СИЗ третья (Task 406)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf('else if (bi === 4) colInstr += panel;') !== -1,
            'инструктажи (блок 5) — ВТОРАЯ колонка (Task 406)');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol ws-wcol-ppe\\">' + colPpe + '</div>'") !== -1,
            'ТРЕТЬЯ колонка .ws-wcol-ppe — СИЗ (Task 406)');
    });""",
     'src-колонки'),

    ("""        const html = host._renderWorkerCardPanels('2706', true);
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
            'колонка 3 — 2 окна (мероприятия + инструктажи, Task 405)');
        const iProf = mainPart.indexOf('Галкин Д. Н.');
        const iVac = mainPart.indexOf('Отпуска · 2026');
        assertTrue(iProf !== -1 && iVac !== -1 && iProf < iVac,
            'колонка 1: профиль → отпуска');
        const iPz = ppePart.indexOf('СИЗ · средства индивидуальной защиты');
        const iTr = trPart.indexOf('Мероприятия · 2026');
        assertTrue(iPz !== -1 && iTr !== -1, 'СИЗ и мероприятия на месте');
        // Task 405: «Инструктаж» с заглавной — тоже b5 (толерантность)
        assertTrue(trPart.indexOf('Повторные инструктажи') !== -1 &&
                   trPart.indexOf('ОТ') !== -1,
            'инструктаж — в колонке 3, в блоке повторных инструктажей');
        assertTrue(mainPart.indexOf('СИЗ · средства') === -1 &&
                   mainPart.indexOf('Мероприятия · 2026') === -1,
            'в колонке 1 — только профиль и отпуска');
        assertTrue(ppePart.indexOf('Мероприятия · 2026') === -1,
            'мероприятия НЕ во 2-й колонке (СИЗ — слева от них, Task 404)');""",
     """        const html = host._renderWorkerCardPanels('2706', true);
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
            'колонка 2 — 1 окно (инструктажи)');
        assertEqual((ppePart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 3 — 1 окно (СИЗ)');
        const iProf = mainPart.indexOf('Галкин Д. Н.');
        const iVac = mainPart.indexOf('Отпуска · 2026');
        const iTr = mainPart.indexOf('Мероприятия · 2026');
        assertTrue(iProf !== -1 && iVac !== -1 && iTr !== -1 &&
                   iProf < iVac && iVac < iTr,
            'колонка 1: профиль → отпуска → мероприятия (Task 406)');
        const iPz = ppePart.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(iPz !== -1, 'СИЗ на месте (3-я колонка)');
        // Task 405: «Инструктаж» с заглавной — тоже b5 (толерантность)
        assertTrue(insPart.indexOf('Повторные инструктажи') !== -1 &&
                   insPart.indexOf('ОТ') !== -1,
            'инструктаж — во 2-й колонке, в блоке повторных инструктажей');
        assertTrue(insPart.indexOf('Мероприятия · 2026') === -1,
            'мероприятия НЕ во 2-й колонке (Task 406)');
        assertTrue(ppePart.indexOf('Повторные инструктажи') === -1 &&
                   ppePart.indexOf('Мероприятия · 2026') === -1,
            'в 3-й колонке — только СИЗ');""",
     'vm-колонки'),
])

# ---------- test-task404.js ----------
patch('test-task404.js', [
    ("""    test('_renderWorkerCardPanels: СИЗ — вторая колонка, мероприятия — третья', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf('var colMain = \\'\\', colPpe = \\'\\', colTr = \\'\\';') !== -1,
            'три сборщика колонок: colMain / colPpe / colTr');
        assertTrue(fn.indexOf('if (bi < 2) colMain += panel;') !== -1,
            'блоки 1–2 (профиль + отпуска) — в ПЕРВУЮ колонку');
        assertTrue(fn.indexOf('else if (bi === 3) colPpe += panel;') !== -1,
            'блок 4 (СИЗ) — во ВТОРУЮ колонку (СЛЕВА от мероприятий)');
        assertTrue(fn.indexOf('else colTr += panel;') !== -1,
            'блок 3 (мероприятия) — в ТРЕТЬЮ колонку');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol\\">' + colMain + '</div>' +") !== -1 &&
                   fn.indexOf("'<div class=\\"ws-wcol ws-wcol-ppe\\">' + colPpe + '</div>' +") !== -1 &&
                   fn.indexOf("'<div class=\\"ws-wcol ws-wcol-tr\\">' + colTr + '</div>'") !== -1,
            'возврат: main → СИЗ (.ws-wcol-ppe) → мероприятия (.ws-wcol-tr)');
    });""",
     """    test('_renderWorkerCardPanels: мероприятия — под отпусками; инструктажи — вторая, СИЗ — третья (Task 406)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        assertTrue(fn.indexOf('var colMain = \\'\\', colInstr = \\'\\', colPpe = \\'\\';') !== -1,
            'три сборщика колонок: colMain / colInstr / colPpe');
        assertTrue(fn.indexOf('if (bi < 3) colMain += panel;') !== -1,
            'блоки 1–3 (профиль + отпуска + мероприятия) — в ПЕРВУЮ колонку');
        assertTrue(fn.indexOf('else if (bi === 4) colInstr += panel;') !== -1,
            'блок 5 (инструктажи) — во ВТОРУЮ колонку (Task 406)');
        assertTrue(fn.indexOf('else colPpe += panel;') !== -1,
            'блок 4 (СИЗ) — в ТРЕТЬЮ колонку (Task 406)');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol\\">' + colMain + '</div>' +") !== -1 &&
                   fn.indexOf("'<div class=\\"ws-wcol ws-wcol-instr\\">' + colInstr + '</div>' +") !== -1 &&
                   fn.indexOf("'<div class=\\"ws-wcol ws-wcol-ppe\\">' + colPpe + '</div>'") !== -1,
            'возврат: main → инструктажи (.ws-wcol-instr) → СИЗ (.ws-wcol-ppe)');
    });""",
     'src-колонки'),

    ("""    test('три колонки: 2 окна | 1 (СИЗ) | 1 (мероприятия); порядок DOM', () => {
        const host = cardHost();
        const html = host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iP = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        const iT = html.indexOf('<div class="ws-wcol ws-wcol-tr">');
        assertTrue(iL !== -1 && iP !== -1 && iT !== -1 && iL < iP && iP < iT,
            'ТРИ колонки: main → СИЗ → мероприятия');
        const mainPart = html.slice(iL, iP);
        const ppePart = html.slice(iP, iT);
        const trPart = html.slice(iT);
        assertEqual((mainPart.match(/class="ws-wcard"/g) || []).length, 2,
            'колонка 1 — профиль + отпуска');
        assertEqual((ppePart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 2 — СИЗ');
        assertEqual((trPart.match(/class="ws-wcard"/g) || []).length, 2,
            'колонка 3 — мероприятия + инструктажи (Task 405)');
        // порядок DOM = «слева на право» из заявки
        const iProf = mainPart.indexOf('Галкин Д. Н.');
        const iVac = mainPart.indexOf('Отпуска · 2026');
        const iPz = ppePart.indexOf('СИЗ · средства индивидуальной защиты');
        const iTr = trPart.indexOf('Мероприятия · 2026');
        assertTrue(iProf !== -1 && iVac !== -1 && iPz !== -1 && iTr !== -1,
            'все блоки на месте');
        assertTrue(iProf < iVac, 'под профилем — отпуска (внутри 1-й колонки)');
        assertTrue(iL + iProf < iP + iPz && iP + iPz < iT + iTr,
            'визуальный порядок: профиль → СИЗ → мероприятия');
        // Task 405: за мероприятиями — блок повторных инструктажей
        const iIns = trPart.indexOf('Повторные инструктажи');
        assertTrue(iIns > iTr, 'инструктажи — ПОД мероприятиями (colTr)');
    });""",
     """    test('три колонки: 3 окна | 1 (инструктажи) | 1 (СИЗ); порядок DOM (Task 406)', () => {
        const host = cardHost();
        const html = host._renderWorkerCardPanels('2706', true);
        const iL = html.indexOf('<div class="ws-wcol">');
        const iI = html.indexOf('<div class="ws-wcol ws-wcol-instr">');
        const iP = html.indexOf('<div class="ws-wcol ws-wcol-ppe">');
        assertTrue(iL !== -1 && iI !== -1 && iP !== -1 && iL < iI && iI < iP,
            'ТРИ колонки: main → инструктажи → СИЗ');
        const mainPart = html.slice(iL, iI);
        const insPart = html.slice(iI, iP);
        const ppePart = html.slice(iP);
        assertEqual((mainPart.match(/class="ws-wcard"/g) || []).length, 3,
            'колонка 1 — профиль + отпуска + мероприятия (Task 406)');
        assertEqual((insPart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 2 — инструктажи');
        assertEqual((ppePart.match(/class="ws-wcard"/g) || []).length, 1,
            'колонка 3 — СИЗ');
        // порядок DOM = «слева на право» из заявки
        const iProf = mainPart.indexOf('Галкин Д. Н.');
        const iVac = mainPart.indexOf('Отпуска · 2026');
        const iTr = mainPart.indexOf('Мероприятия · 2026');
        const iIns = insPart.indexOf('Повторные инструктажи');
        const iPz = ppePart.indexOf('СИЗ · средства индивидуальной защиты');
        assertTrue(iProf !== -1 && iVac !== -1 && iTr !== -1 &&
                   iIns !== -1 && iPz !== -1,
            'все блоки на месте');
        assertTrue(iProf < iVac && iVac < iTr,
            'под профилем — отпуска, под ним — мероприятия (1-я колонка)');
        assertTrue(iL + iProf < iI + iIns && iI + iIns < iP + iPz,
            'визуальный порядок: профиль → инструктажи → СИЗ (Task 406)');
        assertTrue(ppePart.indexOf('Повторные инструктажи') === -1,
            'инструктажи — НЕ в колонке СИЗ');
    });""",
     'vm-колонки'),
])

# ---------- test-task405.js ----------
patch('test-task405.js', [
    ("""    test('панели: колонка мероприятий — мероприятий + инструктажи', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        // bi===3 → colPpe (СИЗ), bi 2 и 4 → colTr (мероприятия,
        // инструктажи) — код раскладки НЕ меняется (else-ветка)
        assertTrue(fn.indexOf('else if (bi === 3) colPpe += panel;') !== -1 &&
                   fn.indexOf('else colTr += panel;') !== -1,
            'раскладка 5 блоков: СИЗ — 2-я колонка, третья — мероприятия+инструктажи');
    });""",
     """    test('панели: Task 406 — мероприятия в 1-ю колонку, инструктажи — 2-я, СИЗ — 3-я', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        // bi<3 → colMain (профиль+отпуска+мероприятия), bi===4 →
        // colInstr, else → colPpe (СИЗ) — Task 406
        assertTrue(fn.indexOf('if (bi < 3) colMain += panel;') !== -1 &&
                   fn.indexOf('else if (bi === 4) colInstr += panel;') !== -1,
            'раскладка 5 блоков: мероприятия — под отпусками, инструктажи — 2-я, СИЗ — 3-я');
    });""",
     'src-панели'),
])

# ---------- test-task393.js ----------
patch('test-task393.js', [
    ("""        // Task 404: СИЗ — ВТОРАЯ колонка (слева от мероприятий);
        // Task 405: за мероприятиями — блок повторных инструктажей
        // (обе правые колонки — общий стек colTr)
        assertTrue(i1 < i2 && i2 < i4 && i4 < i3 && i3 < i5,
            'порядок: профиль → отпуска → СИЗ → мероприятия → инструктажи');""",
     """        // Task 406: мероприятия — ПОД отпусками (1-я колонка),
        // инструктажи — вторая колонка, СИЗ — третья
        assertTrue(i1 < i2 && i2 < i3 && i3 < i5 && i5 < i4,
            'порядок: профиль → отпуска → мероприятия → инструктажи → СИЗ');""",
     'vm-порядок'),
])

# ---------- test-task395.js ----------
patch('test-task395.js', [
    ("""    test('_renderWorkerCardPanels — ТРИ колонки: main / СИЗ / мероприятия', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        // Task 404: СИЗ — ВТОРАЯ колонка (слева от мероприятий),
        // мероприятия — ТРЕТЬЯ (.ws-wcol-tr)
        assertTrue(fn.indexOf('if (bi < 2) colMain += panel;') !== -1,
            'блоки 1–2 (профиль/отпуска) — в колонку main');
        assertTrue(fn.indexOf('else if (bi === 3) colPpe += panel;') !== -1,
            'блок 4 (СИЗ) — во ВТОРУЮ колонку .ws-wcol-ppe');
        assertTrue(fn.indexOf('else colTr += panel;') !== -1,
            'блок 3 (мероприятия) — в ТРЕТЬЮ колонку .ws-wcol-tr');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol ws-wcol-tr\\">' + colTr + '</div>'") !== -1,
            'третья колонка .ws-wcol-tr (мероприятия — СПРАВА от СИЗ)');""",
     """    test('_renderWorkerCardPanels — ТРИ колонки: main / инструктажи / СИЗ', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCardPanels'));
        // Task 406: мероприятия — в ПЕРВУЮ колонку (под отпусками),
        // инструктажи — ВТОРАЯ (.ws-wcol-instr), СИЗ — ТРЕТЬЯ (.ws-wcol-ppe)
        assertTrue(fn.indexOf('if (bi < 3) colMain += panel;') !== -1,
            'блоки 1–3 (профиль/отпуска/мероприятия) — в колонку main');
        assertTrue(fn.indexOf('else if (bi === 4) colInstr += panel;') !== -1,
            'блок 5 (инструктажи) — во ВТОРУЮ колонку .ws-wcol-instr');
        assertTrue(fn.indexOf('else colPpe += panel;') !== -1,
            'блок 4 (СИЗ) — в ТРЕТЬЮ колонку .ws-wcol-ppe');
        assertTrue(fn.indexOf("'<div class=\\"ws-wcol ws-wcol-ppe\\">' + colPpe + '</div>'") !== -1,
            'третья колонка .ws-wcol-ppe (СИЗ — СПРАВА от инструктажей)');""",
     'src-колонки'),
])

if fail:
    print('АДАПТАЦИЯ НЕ ЗАВЕРШЕНА: %d ошибок' % fail)
    sys.exit(1)
print('Адаптация тестов Task 406 завершена')
