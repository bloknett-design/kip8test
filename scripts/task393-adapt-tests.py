#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 393: адаптация тестов — карточка работника на странице
# «Работники» теперь ЧЕТЫРЕ блока-окна .ws-wcard (заявка: «разбить
# карты работников на четыре блока» + шрифт крупнее):
#   1) HOST_METHODS (385) и моки workersHost (388/389/390/391/392) —
#      добавлен метод _renderWorkerCardPanels (страница зовёт его,
#      а не прямой _renderWorkerCard);
#   2) ассерты вызова «_renderWorkerCard(empTabNo, withEdit)» →
#      «_renderWorkerCardPanels(empTabNo, withEdit)» (385/388) и
#      обёртка «ws-wcard» → «_renderWorkerCardPanels» (385);
#   3) счётчик окон .ws-wcard в теле вкладки: 1 → 4 (385).
# Мок панели возвращает ту же CARD-строку в ОДНОЙ обёртке .ws-wcard
# (инвариант «CARD:№:edit» и счётчик 388 «одна карточка» сохранены).
import io
import sys

MOCK_LINE_1_8 = "        '_renderWorkerCard: function(tabNo, withEdit) {' +\n"
MOCK_LINE_2_8 = "        '  return \"CARD:\" + tabNo + \":\" + (withEdit ? \"edit\" : \"view\"); },' +\n"
PANEL_LINE_1_8 = "        '_renderWorkerCardPanels: function(tabNo, withEdit) {' +\n"
PANEL_LINE_2_8 = ("        '  return \\'<div class=\"ws-wcard\">CARD:\\' + tabNo + "
                  "\\':\\' + (withEdit ? \"edit\" : \"view\") + \\'</div>\\'; },' +\n")

MOCK_8 = MOCK_LINE_1_8 + MOCK_LINE_2_8
MOCK_8_NEW = (MOCK_LINE_1_8 + MOCK_LINE_2_8 +
              "        // Task 393: страница «Работники» рендерит ПАНЕЛИ блоков карточки\n" +
              PANEL_LINE_1_8 + PANEL_LINE_2_8)

MOCK_LINE_1_12 = "            '_renderWorkerCard: function(tabNo, withEdit) {' +\n"
MOCK_LINE_2_12 = "            '  return \"CARD:\" + tabNo + \":\" + (withEdit ? \"edit\" : \"view\"); },' +\n"
PANEL_LINE_1_12 = "            '_renderWorkerCardPanels: function(tabNo, withEdit) {' +\n"
PANEL_LINE_2_12 = ("            '  return \\'<div class=\"ws-wcard\">CARD:\\' + tabNo + "
                   "\\':\\' + (withEdit ? \"edit\" : \"view\") + \\'</div>\\'; },' +\n")

MOCK_12 = MOCK_LINE_1_12 + MOCK_LINE_2_12
MOCK_12_NEW = (MOCK_LINE_1_12 + MOCK_LINE_2_12 +
               "            // Task 393: страница «Работники» рендерит ПАНЕЛИ блоков карточки\n" +
               PANEL_LINE_1_12 + PANEL_LINE_2_12)


def patch(path, repl):
    s = io.open(path, encoding='utf-8').read()
    ok = True
    for old, new, cnt in repl:
        n = s.count(old)
        if n != cnt:
            print('  !! %s: якорь x%d (ожидалось x%d): %r' % (path, n, cnt, old[:70]))
            ok = False
            continue
        s = s.replace(old, new)
    if not ok:
        sys.exit(1)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('  ok %s (%d правок)' % (path, len(repl)))


print('Task 393 — адаптация тестов под 4 блока карточки:')

# test-task385.js — HOST_METHODS + вызов + обёртка + счётчик окон
patch('tests/test-task385.js', [
    ("""    const HOST_METHODS = [
        '_renderEmpPopup', '_renderWorkerCard', '_renderWorkersPage',""",
     """    const HOST_METHODS = [
        '_renderEmpPopup', '_renderWorkerCard', '_renderWorkerCardPanels',
        '_renderWorkersPage',""", 1),
    ("""        assertTrue(fn.indexOf('ws-wcard') !== -1, 'обёртка карточки .ws-wcard');""",
     """        assertTrue(fn.indexOf('_renderWorkerCardPanels') !== -1,
            'обёртка карточки — панели .ws-wcard (Task 393)');""", 1),
    ("""        assertTrue(fn.indexOf('_renderWorkerCard(empTabNo, withEdit)') !== -1,
            'карточка — общий рендер с withEdit');""",
     """        assertTrue(fn.indexOf('_renderWorkerCardPanels(empTabNo, withEdit)') !== -1,
            'карточка — панели блоков с withEdit (Task 393)');""", 1),
    ("""assertEqual((body2.match(/ws-wcard/g) || []).length, 1, 'карточка выбранного');""",
     """assertEqual((body2.match(/ws-wcard/g) || []).length, 4,
            'карточка выбранного — ЧЕТЫРЕ блока-окна (Task 393)');""", 1),
])

# test-task388.js — вызов + мок-панель (12 пробелов)
patch('tests/test-task388.js', [
    ("""        assertTrue(fn.indexOf('_renderWorkerCard(empTabNo, withEdit)') !== -1,
            'тело вкладки работника — полная карточка');""",
     """        assertTrue(fn.indexOf('_renderWorkerCardPanels(empTabNo, withEdit)') !== -1,
            'тело вкладки работника — четыре блока-панели (Task 393)');""", 1),
    (MOCK_12, MOCK_12_NEW, 1),
])

# test-task389/390/391/392.js — мок-панель (8 пробелов)
for f in ['tests/test-task389.js', 'tests/test-task390.js',
          'tests/test-task391.js', 'tests/test-task392.js']:
    patch(f, [(MOCK_8, MOCK_8_NEW, 1)])

print('Готово: 6 файлов адаптировано.')
