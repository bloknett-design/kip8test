#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 364 — 2 правки по заявке пользователя:
# (1) КРАСНАЯ РАМКА-ГРУППА выходных (экранная сетка, Task 363):
#     3px #e53935 → 2px #e57373 — «сделай 2px и по меньше яркости».
#     Кнопка .ws-dismiss-submit (#e53935) НЕ трогается — это увольнение.
# (2) ПЕЧАТЬ: коды — СТОЛБИКОМ СПРАВА от столбика мероприятий
#     («коды под графиком на печати размести в столбик справа от
#     столбика мероприятий»): обёртка .wsp-bottom (flex-ряд),
#     мероприятия слева (flex: 1), коды справа (max-width 44%),
#     сноска wsp-foot — ниже обёртки на всю ширину.
import io

path = 'index.html'
src = io.open(path, encoding='utf-8').read()
edits = []

def rep(old, new, tag):
    global src
    assert old in src, 'НЕ НАЙДЕНО: ' + tag
    n = src.count(old)
    assert n == 1, 'НЕ УНИКАЛЬНО (%d): %s' % (n, tag)
    src = src.replace(old, new)
    edits.append(tag)

# ── (1) РАМКА-ГРУППА: комментарий + 6 правил 3px #e53935 → 2px #e57373 ──
rep('#e53935, толщина 3px — заметно при 1px-линиях сетки. */',
    '#e57373, толщина 2px — спокойнее яркого #e53935 (Task 364:\n'
    '       заявка «сделай 2px и по меньше яркости»: та же рамка,\n'
    '       тоньше и бледнее). */',
    'комментарий рамки')

rep('''    .ws-grid thead th.ws-day-col.ws-wgrp {
        box-shadow: inset 0 3px 0 0 #e53935;
    }
    .ws-grid thead th.ws-day-col.ws-wgrp-first { border-left: 3px solid #e53935; }
    .ws-grid thead th.ws-day-col.ws-wgrp-last { border-right: 3px solid #e53935; }
    .ws-grid tbody td.ws-cell.ws-wgrp-first { border-left: 3px solid #e53935; }
    .ws-grid tbody td.ws-cell.ws-wgrp-last { border-right: 3px solid #e53935; }
    .ws-grid tbody tr:last-child td.ws-cell.ws-wgrp {
        border-bottom: 3px solid #e53935;
    }''',
    '''    .ws-grid thead th.ws-day-col.ws-wgrp {
        box-shadow: inset 0 2px 0 0 #e57373;
    }
    .ws-grid thead th.ws-day-col.ws-wgrp-first { border-left: 2px solid #e57373; }
    .ws-grid thead th.ws-day-col.ws-wgrp-last { border-right: 2px solid #e57373; }
    .ws-grid tbody td.ws-cell.ws-wgrp-first { border-left: 2px solid #e57373; }
    .ws-grid tbody td.ws-cell.ws-wgrp-last { border-right: 2px solid #e57373; }
    .ws-grid tbody tr:last-child td.ws-cell.ws-wgrp {
        border-bottom: 2px solid #e57373;
    }''',
    '6 правил рамки 2px #e57373')

# ── (2a) ПЕЧАТЬ, CSS: комментарий блока + .wsp-bottom + .wsp-mev ──
rep('''           «размер шрифта всех строк над и под таблицей сделай
           больше») */
        #wsPrintSheet .wsp-mev {
            margin-top: 2.5mm;
            font-size: 11px;
            line-height: 1.6;
        }''',
    '''           «размер шрифта всех строк над и под таблицей сделай
           больше»).
           Task 364 (заявка: «коды под графиком на печати размести
           в столбик справа от столбика мероприятий»): мероприятия
           и коды — ДВЕ КОЛОНКИ одного ряда под таблицей (обёртка
           wsp-bottom, flex-ряд: мероприятия слева, коды справа),
           каждая запись/код — по-прежнему отдельной строкой своего
           столбика; отступ сверху 2.5mm перенесён на обёртку */
        #wsPrintSheet .wsp-bottom {
            display: flex;
            flex-direction: row;
            align-items: flex-start;
            gap: 5mm;
            margin-top: 2.5mm;
        }
        #wsPrintSheet .wsp-mev {
            flex: 1 1 auto;
            min-width: 0;
            margin-top: 0;
            font-size: 11px;
            line-height: 1.6;
        }''',
    'CSS: wsp-bottom + wsp-mev')

# ── (2b) ПЕЧАТЬ, CSS: .wsp-legend — правая колонка ряда ──
rep('''        /* легенда кодов и пояснения (Task 360: только коды
           этого месяца, одна строка — один код; Task 361:
           шрифт 8→11px, точка 7→9px) */
        #wsPrintSheet .wsp-legend {
            margin-top: 2.5mm;
            font-size: 11px;
            line-height: 1.6;
        }''',
    '''        /* легенда кодов и пояснения (Task 360: только коды
           этого месяца, одна строка — один код; Task 361:
           шрифт 8→11px, точка 7→9px; Task 364: правая колонка
           ряда wsp-bottom — «в столбик справа от столбика
           мероприятий», без растяжения на всю ширину) */
        #wsPrintSheet .wsp-legend {
            flex: 0 0 auto;
            max-width: 44%;
            margin-top: 0;
            font-size: 11px;
            line-height: 1.6;
        }''',
    'CSS: wsp-legend правая колонка')

# ── (2c) JS: открытие обёртки перед секцией мероприятий ──
rep('''            html += '<div class="wsp-mev"><span class="wsp-mev-t">' +''',
    '''            // Task 364 (заявка: «коды под графиком на печати
            // размести в столбик справа от столбика мероприятий»):
            // обёртка wsp-bottom — мероприятия и коды в ОДНОМ РЯДУ
            // (мероприятия слева, коды справа; CSS @media print),
            // сноска wsp-foot — ниже обёртки на всю ширину листа
            html += '<div class="wsp-bottom">';
            html += '<div class="wsp-mev"><span class="wsp-mev-t">' +''',
    'JS: открытие wsp-bottom')

# ── (2d) JS: закрытие обёртки после перечня кодов ──
rep('''            html += '</div>';
            html += '<div class="wsp-foot">* — сокращённый предпраздничный рабочий день; ''' + "'",
    '''            html += '</div></div>';
            html += '<div class="wsp-foot">* — сокращённый предпраздничный рабочий день; ''' + "'",
    'JS: закрытие wsp-bottom')

# ── (2e) JS: комментарий перечня кодов — позиция правой колонки ──
rep('''            // легаси-код, удалённый из справочника, попадает в
            // конец без цвета и имени (только код)''',
    '''            // легаси-код, удалённый из справочника, попадает в
            // конец без цвета и имени (только код). Task 364:
            // столбик кодов — ПРАВАЯ колонка ряда wsp-bottom
            // (слева — мероприятия), а не секция под списком''',
    'JS: комментарий кодов')

io.open(path, 'w', encoding='utf-8').write(src)
print('OK, правок: %d' % len(edits))
for e in edits:
    print('  ✓', e)

# самоконтроль: в правилах wgrp не осталось 3px/#e53935
i = src.indexOf if False else src.find('.ws-grid thead th.ws-day-col.ws-wgrp')
j = src.find('/* === Task 260')
blk = src[i:j]
assert '3px' not in blk and '#e53935' not in blk, 'в блоке wgrp остался старый цвет/толщина'
# кнопка увольнения НЕ задета
assert '.ws-dismiss-submit {\n        background: #e53935;' in src, 'ws-dismiss-submit не задет'
# обёртка в печати
assert src.count('wsp-bottom') == 4, 'wsp-bottom должен встретиться 4 раза (CSS x2 + JS x2)'
print('Самоконтроль пройден.')
