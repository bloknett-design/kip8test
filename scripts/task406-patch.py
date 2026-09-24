#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 406 (kip8test): заявка «В картах работников, блок мероприятия
перемести под блок отпуска, а блоки СИЗ и инструктажей поменяй местами».

Раскладка карточки «Работники» (десктоп ≥1024px, ТРИ равные колонки):
  ДО (Task 404/405): 1-я — профиль + отпуска | 2-я — СИЗ | 3-я —
  мероприятия + под ним инструктажи
  ПОСЛЕ (Task 406):  1-я — профиль + отпуска + МЕРОПРИЯТИЯ (под
  отпусками) | 2-я — ИНСТРУКТАЖИ (.ws-wcol-instr) | 3-я — СИЗ
  (.ws-wcol-ppe). Мобайл ≤1023px — стек колонок в том же порядке
  (профиль → отпуска → мероприятия → инструктажи → СИЗ).

Попап шахматки (b1+b2+b3+b5 — вертикальный стек: профиль → отпуска →
мероприятия → инструктажи) уже соответствует заявке и НЕ меняется.
СЕРВЕР (WorkSchedule.gs) не трогается — меняется только раскладка.
"""
import io
import sys

PATH = '/home/z/my-project/kip8test/index.html'
src = io.open(PATH, encoding='utf-8').read()
orig = src

REPL = []


def rep(old, new, tag):
    REPL.append((old, new, tag))


# --- 1. Комментарий + код _renderWorkerCardPanels: раскладка колонок ---
OLD_FN = """        // Task 395 \u2192 403 \u2192 404 (заявка): ТРИ колонки-обёртки .ws-wcol
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
        // (Task 393) + межколоночный (CSS)
        _renderWorkerCardPanels: function(tabNo, withEdit) {
            var blocks = this._renderWorkerCard(tabNo, withEdit, true);
            var colMain = '', colPpe = '', colTr = '';
            for (var bi = 0; bi < blocks.length; bi++) {
                var panel = '<div class="ws-wcard">' + blocks[bi] + '</div>';
                if (bi < 2) colMain += panel;
                else if (bi === 3) colPpe += panel;
                else colTr += panel;
            }
            return '<div class="ws-wcol">' + colMain + '</div>' +
                   '<div class="ws-wcol ws-wcol-ppe">' + colPpe + '</div>' +
                   '<div class="ws-wcol ws-wcol-tr">' + colTr + '</div>';
        },"""

NEW_FN = """        // Task 395 → 403 → 404 → 406 (заявки): ТРИ колонки-обёртки
        // .ws-wcol (раскладка — CSS @media ≥1024px). Task 406
        // (заявка: «блок мероприятия перемести под блок отпуска,
        // блоки СИЗ и инструктажей поменяй местами»): колонка 1 —
        // ПРОФИЛЬ + ОТПУСКА + МЕРОПРИЯТИЯ (вертикальный стек),
        // колонка 2 (.ws-wcol-instr) — «Повторные инструктажи и
        // периодическая проверка знаний», колонка 3 (.ws-wcol-ppe)
        // — СИЗ. Мобайл ≤1023px — вертикальный СТЕК колонок
        // (профиль → отпуска → мероприятия → инструктажи → СИЗ);
        // зазоры — margin-bottom панелей (Task 393) +
        // межколоночный (CSS)
        _renderWorkerCardPanels: function(tabNo, withEdit) {
            var blocks = this._renderWorkerCard(tabNo, withEdit, true);
            var colMain = '', colInstr = '', colPpe = '';
            for (var bi = 0; bi < blocks.length; bi++) {
                var panel = '<div class="ws-wcard">' + blocks[bi] + '</div>';
                if (bi < 3) colMain += panel;
                else if (bi === 4) colInstr += panel;
                else colPpe += panel;
            }
            return '<div class="ws-wcol">' + colMain + '</div>' +
                   '<div class="ws-wcol ws-wcol-instr">' + colInstr + '</div>' +
                   '<div class="ws-wcol ws-wcol-ppe">' + colPpe + '</div>';
        },"""

rep(OLD_FN, NEW_FN, 'renderWorkerCardPanels')

# --- 2. Комментарий у _renderWorkersPage (обёртка .ws-wgrid2) ---
OLD_WRAP = """                // Task 394 (заявка): четыре блока-окна — в обёртке
                // .ws-wgrid2: десктоп ≥1024px — ДВЕ колонки на всю
                // ширину (Task 403: слева профиль и отпуска, справа
                // мероприятия НАД СИЗ — между блоками профиля и СИЗ);
                // мобайл — прежний вертикальный стек (обёртка без
                // правил сетки)"""

NEW_WRAP = """                // Task 394 (заявка): блоки-окна — в обёртке
                // .ws-wgrid2: десктоп ≥1024px — ТРИ колонки на всю
                // ширину (Task 406: 1-я — профиль + отпуска +
                // мероприятия, 2-я — инструктажи, 3-я — СИЗ);
                // мобайл — вертикальный стек (обёртка без
                // правил сетки)"""

rep(OLD_WRAP, NEW_WRAP, 'renderWorkersPage-comment')

# --- 3. CSS: комментарий блока-окон (ЧЕТЫРЕ → ПЯТЬ) ---
OLD_CNT = """    /* Task 393: в теле вкладки карточка — ЧЕТЫРЕ блока-окна: зазор
       между ними — margin-bottom, у последнего — 0 (стек ВНУТРИ
       колонок Task 395 — и мобайл, и десктоп) */"""

NEW_CNT = """    /* Task 393: в теле вкладки карточка — ПЯТЬ блоков-окон (Task
       405): зазор между ними — margin-bottom, у последнего — 0 (стек
       ВНУТРИ колонок Task 395 — и мобайл, и десктоп) */"""

rep(OLD_CNT, NEW_CNT, 'css-wcard-count')

# --- 4. CSS: комментарий колонок .ws-wcol ---
OLD_COLS = """    /* Task 395 (заявка): КОЛОНКИ-обёртки .ws-wcol (сборка —
       _renderWorkerCardPanels; Task 404 — ТРИ колонки: 1-я —
       профиль + отпуска, 2-я .ws-wcol-ppe — СИЗ, 3-я .ws-wcol-tr —
       мероприятия; блок СИЗ — СЛЕВА от блока мероприятий, три
       верхних блока в одну линию).
       Мобайл ≤1023px —
       колонки БЕЗ правил раскладки = блоки друг под другом; зазор
       между колонками — margin-bottom, у последней — 0 (внутри
       колонок панелям — базовые правила Task 393 выше) */"""

NEW_COLS = """    /* Task 395 (заявка): КОЛОНКИ-обёртки .ws-wcol (сборка —
       _renderWorkerCardPanels; Task 406 — ТРИ колонки: 1-я —
       профиль + отпуска + мероприятия (мероприятия — ПОД
       отпусками), 2-я .ws-wcol-instr — инструктажи, 3-я
       .ws-wcol-ppe — СИЗ; блоки СИЗ и инструктажей поменяны
       местами).
       Мобайл ≤1023px —
       колонки БЕЗ правил раскладки = блоки друг под другом; зазор
       между колонками — margin-bottom, у последней — 0 (внутри
       колонок панелям — базовые правила Task 393 выше) */"""

rep(OLD_COLS, NEW_COLS, 'css-wcol-comment')

# --- 5. CSS: комментарий @media (три равные колонки) ---
OLD_MEDIA = """    /* Task 394 → 395 → 403 → 404 (заявка): ДЕСКТОП (≥1024px) —
       ТРИ РАВНЫЕ колонки НА ВСЮ ШИРИНУ окна вкладок (flex, обёртка
       .ws-wgrid2 — _renderWorkersPage, только вкладка работника;
       «Общая» — без колонок): 1-я — ПРОФИЛЬ, ПОД ним ОТПУСКА
       (вертикальный стек окон); 2-я — СИЗ; 3-я — МЕРОПРИЯТИЯ
       (Task 404: блок СИЗ — СЛЕВА от блока мероприятий, три верхних
       блока — профиль/СИЗ/мероприятия — в ОДНУ ЛИНИЮ; равные доли
       flex: 1 1 0 — блоки гарантированно помещаются; align-items:
       flex-start — колонки НЕ тянутся по высоте друг друга). Зазоры:
       между колонками — gap 12px; между окнами 1-й колонки —
       margin-bottom панелей (базовые правила Task 393) */"""

NEW_MEDIA = """    /* Task 394 → 395 → 403 → 404 → 406 (заявки): ДЕСКТОП (≥1024px) —
       ТРИ РАВНЫЕ колонки НА ВСЮ ШИРИНУ окна вкладок (flex, обёртка
       .ws-wgrid2 — _renderWorkersPage, только вкладка работника;
       «Общая» — без колонок): 1-я — ПРОФИЛЬ, ПОД ним ОТПУСКА, ПОД
       ними МЕРОПРИЯТИЯ (Task 406); 2-я — ИНСТРУКТАЖИ; 3-я — СИЗ
       (Task 406: блоки СИЗ и инструктажей поменяны местами; равные
       доли flex: 1 1 0 — блоки гарантированно помещаются;
       align-items: flex-start — колонки НЕ тянутся по высоте друг
       друга). Зазоры: между колонками — gap 12px; между окнами
       колонок — margin-bottom панелей (базовые правила Task 393) */"""

rep(OLD_MEDIA, NEW_MEDIA, 'css-media-comment')

fail = 0
for old, new, tag in REPL:
    n = src.count(old)
    if n != 1:
        print('FAIL [%s]: вхождений %d (ожидалось 1)' % (tag, n))
        fail += 1
        continue
    src = src.replace(old, new)
    print('OK [%s]' % tag)

if fail:
    print('ПАТЧ НЕ ПРИМЕНЁН: %d ошибок' % fail)
    sys.exit(1)

if src == orig:
    print('НЕТ ИЗМЕНЕНИЙ — патч пуст')
    sys.exit(1)

io.open(PATH, 'w', encoding='utf-8').write(src)
print('index.html: %d правок записано' % len(REPL))

# пост-проверки
chk = io.open(PATH, encoding='utf-8').read()
assert chk.count('ws-wcol-instr') == 3, 'маркер .ws-wcol-instr ×3 (комментарий + код + CSS)'
assert chk.count("'<div class=\"ws-wcol ws-wcol-tr\">'") == 0, 'легаси .ws-wcol-tr удалён из кода'
assert chk.count('if (bi < 3) colMain += panel;') == 1, 'bi<3 → colMain'
assert chk.count('else if (bi === 4) colInstr += panel;') == 1, 'bi===4 → colInstr'
assert chk.count('else colPpe += panel;') == 1, 'else → colPpe (СИЗ)'
print('Пост-проверки пройдены')
