#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442 (kip8test), патч 1 из 3: CSS печатного листа + _buildPrintHtml
# + _printCell.
# Заявка: «На распечатываемом графике работы убери мини значки
# мероприятий в шахматке и столбец с кодами, и внешний контур линий
# выходных календарных дней в шахматке сделай толще, а выделять их
# фоном не нужно, и даты выходных жирнее».
import io

P = 'index.html'
s = io.open(P, encoding='utf-8').read()
orig_len = len(s)
fail = []


def rep(old, new, tag, cnt=1):
    global s
    n = s.count(old)
    if n != cnt:
        fail.append('[%s] вхождений %d, ожидалось %d' % (tag, n, cnt))
        print('FAIL [%s]: вхождений %d, ожидалось %d' % (tag, n, cnt))
        return
    s = s.replace(old, new)
    print('OK [%s]' % tag)


Z = 'На распечатываемом графике работы убери мини значки мероприятий в шахматке и столбец с кодами'

# ============================================================
# 1. CSS: шапка дней — выходные без заливки, число ЖИРНОЕ,
#    верх полосы выходных — толстая линия + края
# ============================================================
rep(
    '        /* выходные/праздники в шапке — заливка/цвет как в шахматке */\n'
    '        #wsPrintSheet .wsp-day.wsp-off { background: #dfe5e9; }\n'
    '        #wsPrintSheet .wsp-day.wsp-feast,\n'
    '        #wsPrintSheet .wsp-day.wsp-feast span { color: #b02a2a; }',
    '        /* Task 442 (заявка: «…внешний контур линий выходных\n'
    '           календарных дней в шахматке сделай толще, а выделять\n'
    '           их фоном не нужно, и даты выходных жирнее»): выходные\n'
    '           в шапке — БЕЗ заливки: число ЖИРНОЕ (день недели под\n'
    '           ним — прежний обычный), сверху колонки выходного —\n'
    '           ТОЛСТАЯ линия контура, wsp-off-edge-l/r — бока полосы\n'
    '           (Сб+Вс подряд — один контур). Праздники — прежний\n'
    '           красный цвет чисел */\n'
    '        #wsPrintSheet .wsp-day.wsp-off {\n'
    '            font-weight: 700;\n'
    '            border-top: 2px solid #8f99a3;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-day.wsp-off span { font-weight: 400; }\n'
    '        #wsPrintSheet .wsp-day.wsp-off-edge-l {\n'
    '            border-left: 2px solid #8f99a3;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-day.wsp-off-edge-r {\n'
    '            border-right: 2px solid #8f99a3;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-day.wsp-feast,\n'
    '        #wsPrintSheet .wsp-day.wsp-feast span { color: #b02a2a; }',
    'css-day-off')

# ============================================================
# 2. CSS: ячейки — серая заливка выходных снята, вместо неё
#    толстые линии контура полосы (edge-l/r/b)
# ============================================================
rep(
    '        /* пустые ячейки нерабочих дней — серая заливка (как\n'
    '           розовая в шахматке, но в печатной гамме); статусные\n'
    '           ячейки сохраняют свой inline-фон */\n'
    '        #wsPrintSheet .wsp-cell.wsp-cell-off { background: #e2e8ec !important; }\n',
    '        /* Task 442 (заявка: «…выделять их фоном не нужно»):\n'
    '           серая заливка пустых ячеек нерабочих дней УДАЛЕНА —\n'
    '           класс wsp-cell-off теперь МАРКЕР колонки выходного\n'
    '           дня: у ВСЕХ ячеек полосы выходных (пустых, статусных,\n'
    '           плана отпуска) толстые линии ВНЕШНЕГО КОНТУРА:\n'
    '           wsp-off-edge-l/r — бока полосы, wsp-off-edge-b — низ\n'
    '           последней строки; !important — выше пунктирной рамки\n'
    '           плана отпуска на боках полосы. Статусные ячейки\n'
    '           сохраняют свой inline-фон кода */\n'
    '        #wsPrintSheet .wsp-cell.wsp-cell-off.wsp-off-edge-l {\n'
    '            border-left: 2px solid #8f99a3 !important;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-cell.wsp-cell-off.wsp-off-edge-r {\n'
    '            border-right: 2px solid #8f99a3 !important;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-cell.wsp-cell-off.wsp-off-edge-b {\n'
    '            border-bottom: 2px solid #8f99a3 !important;\n'
    '        }\n',
    'css-cell-off')

# ============================================================
# 3. CSS: бейджи мероприятий .wsp-ev* — правила УДАЛЕНЫ
# ============================================================
rep(
    '        /* Task 361 (заявка: «сделай отображение на печати значков\n'
    '           мероприятий в ячейках шахматки»): бейджи мероприятий в\n'
    '           печати ВЕРНУТЫ (Task 343 их убирал; заявка 361 вернула).\n'
    '           Формат — как в экранной сетке (Task 314/388): бейдж\n'
    '           ВСЕГДА сплошной с inline-цветом кода (Task 388: пунктирные\n'
    '           wsp-ev-plan у пустой ячейки удалены — как в сетке).\n'
    '           Правый НИЖНИЙ угол (точка переработки — правый\n'
    '           верхний, конфликтов нет); цвет печатается принудительно */\n'
    '        #wsPrintSheet .wsp-ev-wrap {\n'
    '            position: absolute;\n'
    '            right: 0.5mm;\n'
    '            bottom: 0.4mm;\n'
    '            line-height: 1;\n'
    '            white-space: nowrap;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-ev {\n'
    '            display: inline-block;\n'
    '            border: 1px solid #4c5660;\n'
    '            border-radius: 0.5mm;\n'
    '            font-size: 7.5px;\n'
    '            font-weight: 700;\n'
    '            line-height: 1;\n'
    '            padding: 0.4mm 0.5mm 0.3mm;\n'
    '            margin-left: 0.5mm;\n'
    '            color: #263238;\n'
    '            -webkit-print-color-adjust: exact;\n'
    '            print-color-adjust: exact;\n'
    '        }\n'
    '        /* Task 388: пунктирный бейдж-план печати удалён — бейдж\n'
    '           мероприятия всегда сплошной с цветом кода (как в сетке) */\n',
    '        /* Task 442 (заявка: «убери мини значки мероприятий в\n'
    '           шахматке»): бейджи мероприятий в печати УДАЛЕНЫ —\n'
    '           правила .wsp-ev-wrap/.wsp-ev и разметка в _printCell\n'
    '           сняты (Task 361 их возвращал, Task 343 убирал);\n'
    '           мероприятия месяца печатаются только списком под\n'
    '           таблицей, экранная сетка приложения не тронута */\n',
    'css-ev-remove')

# ============================================================
# 4. CSS: wsp-bottom/wsp-mev — ряд снят, легенда удаляется,
#    мероприятия — на всю ширину листа
# ============================================================
rep(
    '        #wsPrintSheet .wsp-bottom {\n'
    '            margin-top: 2.5mm;\n'
    '            /* Task 439 (заявка: «блок с кодами размести справа от\n'
    '               мероприятий»): нижняя секция — ГИБКИЙ РЯД: список\n'
    '               мероприятий слева (растягивается на остаток), блок\n'
    '               кодов — справа фиксированной ширины. Task 440 (заявка:\n'
    '               «коды справа от мероприятий на расстоянии друг от\n'
    '               друга 10px»): зазор между блоками — РОВНО 10px (прежде\n'
    '               6mm ≈ 23px) */\n'
    '            display: flex;\n'
    '            align-items: flex-start;\n'
    '            gap: 10px;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-mev {\n'
    '            margin-top: 0;\n'
    '            font-size: 11px;\n'
    '            line-height: 1.6;\n'
    '            /* Task 431 → Task 440 (заявка: «коды справа от\n'
    '               мероприятий на расстоянии друг от друга 10px»; ранее\n'
    '               в 431 — «сейчас между ними очень большое расстояние»):\n'
    '               столбик мероприятий НЕ растягивается (flex-grow снят,\n'
    '               было 1 1 auto Task 439) — блок кодов встаёт в 10px от\n'
    '               ПРАВОГО КРАЯ ТЕКСТА мероприятий (самой широкой строки),\n'
    '               а не прижатым к правому краю листа; длинные тексты —\n'
    '               по-прежнему переносятся (зона усечена flex-shrink +\n'
    '               min-width: 0: лист − 92мм кодов − 10px зазор) */\n'
    '            flex: 0 1 auto;\n'
    '            min-width: 0;\n'
    '        }\n',
    '        #wsPrintSheet .wsp-bottom {\n'
    '            /* Task 442 (заявка: «убери … столбец с кодами»): блок\n'
    '               кодов УДАЛЕН — нижняя секция снова ОДНА колонка на\n'
    '               всю ширину листа: только список мероприятий (flex-ряд\n'
    '               и зазор 10px из Tasks 439/440 сняты вместе с блоком) */\n'
    '            margin-top: 2.5mm;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-mev {\n'
    '            margin-top: 0;\n'
    '            font-size: 11px;\n'
    '            line-height: 1.6;\n'
    '            /* Task 442: столбца кодов справа больше нет — список\n'
    '               мероприятий на ВСЮ ширину листа (flex-ограничения\n'
    '               зоны из Tasks 439/440 сняты) */\n'
    '        }\n',
    'css-bottom-mev')

# ============================================================
# 5. CSS: легенда кодов .wsp-legend* — правила УДАЛЕНЫ
# ============================================================
rep(
    '        /* легенда кодов и пояснения (Task 360: только коды\n'
    '           этого месяца; Task 361: шрифт 8→11px, точка 7→9px;\n'
    '           Task 364: правая колонка ряда wsp-bottom; Task 432:\n'
    '           флоат у правого верхнего угла; Task 433: единая\n'
    '           строка-абзац «Коды: …» под списком мероприятий).\n'
    '           Task 434 (заявка: «коды на печати сделать в ДВЕ\n'
    '           КОЛОНКИ под названием "Коды:"»): заголовок «Коды:» —\n'
    '           ОТДЕЛЬНОЙ строкой СВЕРХУ, под ним сетка .wsp-legend-cols;\n'
    '           Task 441 (заявка: «коды сделай в один столбец»):\n'
    '           ОДНА колонка (grid 1fr; прежде ДВЕ равные, Task 434)\n'
    '           на всю ширину блока кодов ДО КОНЦА; каждая запись-код\n'
    '           — своя строка (длинное наименование переносится\n'
    '           ВНУТРИ колонки, запись не рвётся между страницами) */\n'
    '        #wsPrintSheet .wsp-legend {\n'
    '            margin-top: 0;\n'
    '            font-size: 11px;\n'
    '            line-height: 1.6;\n'
    '            /* Task 439: коды — ПРАВАЯ часть ряда (СПРАВА от\n'
    '               мероприятий), фиксированная ширина блока */\n'
    '            flex: 0 0 92mm;\n'
    '            min-width: 0;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-legend-t {\n'
    '            display: block;\n'
    '            font-weight: 700;\n'
    '            margin-bottom: 1mm;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-legend-cols {\n'
    '            display: grid;\n'
    '            /* Task 441 (заявка: «коды сделай в один столбец»):\n'
    '               ОДНА колонка — прежде ДВЕ равные (Task 434);\n'
    '               межколоночный зазор снят — колонок больше нет */\n'
    '            grid-template-columns: 1fr;\n'
    '            row-gap: 0.8mm;\n'
    '            align-items: start;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-lg {\n'
    '            display: block;\n'
    '            min-width: 0;\n'
    '            white-space: normal;\n'
    '            break-inside: avoid;\n'
    '            page-break-inside: avoid;\n'
    '        }\n'
    '        #wsPrintSheet .wsp-lg i {\n'
    '            display: inline-block;\n'
    '            width: 9px;\n'
    '            height: 9px;\n'
    '            border: 1px solid #7a838c;\n'
    '            margin-right: 1mm;\n'
    '            -webkit-print-color-adjust: exact;\n'
    '            print-color-adjust: exact;\n'
    '        }\n',
    '        /* Task 442 (заявка: «убери … столбец с кодами»): ЛЕГЕНДА\n'
    '           КОДОВ УДАЛЕНА — правила .wsp-legend/.wsp-legend-t/\n'
    '           .wsp-legend-cols/.wsp-lg/.wsp-lg i сняты вместе с\n'
    '           разметкой в _buildPrintHtml; лист заканчивается списком\n'
    '           мероприятий (точка-цвет строки мероприятия жива —\n'
    '           правило .wsp-mev-item i выше) */\n',
    'css-legend-remove')

# ============================================================
# 6. JS _buildPrintHtml: докстринг
# ============================================================
rep(
    '        // Task 341: HTML печатного листа (светлая «бумажная» вёрстка,\n'
    '        // классы wsp-* из @media print-блока CSS). Повторяет логику\n'
    '        // раскладки _renderGrid: шапка дней с днём недели/выходными/\n'
    '        // праздниками/«*» сокращённых, строки сотрудников вида, в\n'
    '        // ячейках — ЭФФЕКТИВНЫЕ записи (запись + локальная правка,\n'
    '        // __delete — ячейка пустая), план отпуска пунктиром;\n'
    '        // Task 361: бейджи мероприятий в ячейках печати ВЕРНУТЫ\n'
    '        // (см. _printCell). В конце каждой строки — «Дни»/\n'
    '        // «Перераб.» (Task 438: только дни), внизу — Task 360:\n'
    '        // список мероприятий\n'
    '        // текущего месяца (один столбик) и перечень кодов ТОЛЬКО\n'
    '        // этого месяца (Task 343: итоговая строка agg.grand убрана)\n',
    '        // Task 341: HTML печатного листа (светлая «бумажная» вёрстка,\n'
    '        // классы wsp-* из @media print-блока CSS). Повторяет логику\n'
    '        // раскладки _renderGrid: шапка дней с днём недели/выходными/\n'
    '        // праздниками/«*» сокращённых, строки сотрудников вида, в\n'
    '        // ячейках — ЭФФЕКТИВНЫЕ записи (запись + локальная правка,\n'
    '        // __delete — ячейка пустая), план отпуска пунктиром.\n'
    '        // Task 442 (заявка: «' + Z + '…»): бейджи мероприятий\n'
    '        // в ячейках печати УДАЛЕНЫ (Task 361 их возвращал), столбец\n'
    '        // кодов под таблицей УДАЛЕН (Tasks 360–441), полосы выходных\n'
    '        // — ТОЛСТЫЙ внешний контур без заливки, числа выходных —\n'
    '        // ЖИРНЫЕ. В конце каждой строки — «Дни»/«Перераб.»\n'
    '        // (Task 438: только дни), внизу — список мероприятий текущего\n'
    '        // месяца (Task 343: итоговая строка agg.grand убрана)\n',
    'doc-buildprint')

# ============================================================
# 7. JS _buildPrintHtml: шапка дней — сбор offArr + края полосы
# ============================================================
rep(
    "            html += '<table class=\"wsp-grid\"><thead><tr>';\n"
    "            html += '<th class=\"wsp-emp\" style=\"width:' + empWmm + 'mm\">Работник</th>';\n"
    '            for (var d = 1; d <= daysInMonth; d++) {\n'
    '                var dt = new Date(this._year, this._month - 1, d);\n'
    '                var dInfo = (typeof ProdCalendar !== \'undefined\' && ProdCalendar.dayInfo)\n'
    '                    ? ProdCalendar.dayInfo(this._year, this._month, d) : null;\n'
    '                var isOff = dInfo ? dInfo.off\n'
    '                          : (dt.getDay() === 0 || dt.getDay() === 6);\n'
    '                var isFeast = dInfo ? !!dInfo.holiday : false;\n'
    '                var isShort = dInfo ? !!dInfo.short : false;\n'
    "                html += '<th class=\"wsp-day' + (isOff ? ' wsp-off' : '') +\n"
    "                        (isFeast ? ' wsp-feast' : '') + '\">' + d +\n"
    "                        (isShort ? '*' : '') + '<span>' + dows[dt.getDay()] +\n"
    "                        '</span></th>';\n"
    '            }\n',
    "            html += '<table class=\"wsp-grid\"><thead><tr>';\n"
    "            html += '<th class=\"wsp-emp\" style=\"width:' + empWmm + 'mm\">Работник</th>';\n"
    '            // Task 442: флаги нерабочих дней собираются ЗАРАНЕЕ —\n'
    '            // краям полосы выходных (wsp-off-edge-l/r в шапке и\n'
    '            // wsp-cell-off/wsp-off-edge-* в теле) нужен взгляд на\n'
    '            // СОСЕДЕЙ: непрерывная полоса Сб+Вс — ОДИН контур\n'
    '            var offArr = [], feastArr = [], shortArr = [], dowArr = [];\n'
    '            for (var d = 1; d <= daysInMonth; d++) {\n'
    '                var dt = new Date(this._year, this._month - 1, d);\n'
    '                var dInfo = (typeof ProdCalendar !== \'undefined\' && ProdCalendar.dayInfo)\n'
    '                    ? ProdCalendar.dayInfo(this._year, this._month, d) : null;\n'
    '                offArr[d] = dInfo ? !!dInfo.off\n'
    '                          : (dt.getDay() === 0 || dt.getDay() === 6);\n'
    '                feastArr[d] = dInfo ? !!dInfo.holiday : false;\n'
    '                shortArr[d] = dInfo ? !!dInfo.short : false;\n'
    '                dowArr[d] = dows[dt.getDay()];\n'
    '            }\n'
    '            for (var d = 1; d <= daysInMonth; d++) {\n'
    '                var isOff = offArr[d];\n'
    "                html += '<th class=\"wsp-day' + (isOff ? ' wsp-off' : '') +\n"
    "                        (isOff && (d === 1 || !offArr[d - 1])\n"
    "                            ? ' wsp-off-edge-l' : '') +\n"
    "                        (isOff && (d === daysInMonth || !offArr[d + 1])\n"
    "                            ? ' wsp-off-edge-r' : '') +\n"
    "                        (feastArr[d] ? ' wsp-feast' : '') + '\">' + d +\n"
    "                        (shortArr[d] ? '*' : '') + '<span>' + dowArr[d] +\n"
    "                        '</span></th>';\n"
    '            }\n',
    'head-off-edges')

# ============================================================
# 8. JS _buildPrintHtml: убрать usedCodes (комментарий + сбор)
# ============================================================
rep(
    '            var entryIdx = this._buildEntryIndex();\n'
    '            var pend = this._PENDING || {};\n'
    '            // Task 360: статусы, ПРИСУТСТВУЮЩИЕ в этом месяце (по\n'
    '            // ЭФФЕКТИВНЫМ записям ПЕЧАТАЕМЫХ строк — как в сетке:\n'
    '            // локальные правки учитываются, __delete исключается),\n'
    '            // для перечня кодов под списком мероприятий: печатаются\n'
    '            // только коды этого месяца, а не весь справочник.\n'
    '            // «.» и коды мероприятий (И/ОБ/ПЗ/ПР/*) — тоже коды\n'
    '            // месяца: «.» виден в ячейках, коды мероприятий —\n'
    '            // раскрываются в списке мероприятий выше. Task 362\n'
    '            // (заявка: «не отобразилось наименование кода проверки\n'
    '            // знаний ПЗ, хотя он есть в мероприятиях у дневного\n'
    '            // сотрудника»): коды мероприятий добавляются в\n'
    '            // usedCodes и из СПИСКА МЕРОПРИЯТИЙ месяца (см. цикл\n'
    '            // evList ниже) — у дневного персонала мероприятие живёт\n'
    '            // только в «Инструктажах», записи сетки нет, а бейдж в\n'
    '            // ячейке печати ставится — перечень обязан объяснять\n'
    '            // и его\n'
    '            var usedCodes = {};\n',
    '            var entryIdx = this._buildEntryIndex();\n'
    '            var pend = this._PENDING || {};\n'
    '            // Task 442: сбор usedCodes для перечня кодов УДАЛЕН —\n'
    '            // столбца кодов под таблицей больше нет (заявка);\n'
    '            // коды статусов остаются В ЯЧЕЙКАХ шахматки с цветами\n'
    '            // справочника\n',
    'rows-usedcodes-comment')

rep(
    '                    html += this._printCell(day, isoDate, emp, effEntry);\n'
    '                    // Task 360: помечаем код месяца (эффективный\n'
    '                    // статус ячейки)\n'
    '                    if (effEntry && effEntry[\'статус\']) {\n'
    '                        usedCodes[effEntry[\'статус\']] = true;\n'
    '                    }\n',
    '                    // Task 442: isLastRow — низ толстого контура\n'
    '                    // полосы выходных (последняя строка таблицы)\n'
    '                    html += this._printCell(day, isoDate, emp, effEntry,\n'
    '                                            ei === viewEmps.length - 1);\n',
    'rows-call-printcell')

# ============================================================
# 9. JS _buildPrintHtml: убрать пометку кодов мероприятий
# ============================================================
rep(
    '            // Task 362 (заявка: «не отобразилось наименование кода\n'
    '            // проверки знаний ПЗ, хотя он есть в мероприятиях у\n'
    '            // дневного сотрудника»): коды мероприятий отфильтрован-\n'
    '            // ного списка тоже помечаются в usedCodes — бейджи в\n'
    '            // ячейках печати строятся по «Инструктажам» БЕЗ записей\n'
    '            // сетки, сноска листа ссылается на перечень выше; коды\n'
    '            // событий сетки (статус-мероприятия) уже учтены в цикле\n'
    '            // строк шахматки\n'
    '            for (var eci = 0; eci < evList.length; eci++) {\n'
    '                var evCd = (typeof this._trainingCodeOf === \'function\')\n'
    '                    ? this._trainingCodeOf(evList[eci][\'тип\']) : \'\';\n'
    '                if (evCd) usedCodes[evCd] = true;\n'
    '            }\n',
    '            // Task 442: пометка кодов мероприятий для перечня кодов\n'
    '            // УДАЛЕНА — столбца кодов под таблицей больше нет\n',
    'evlist-usedcodes')

# ============================================================
# 10. JS _buildPrintHtml: комментарий секции + легенда УДАЛЕНА
# ============================================================
rep(
    '            // Task 364: обёртка wsp-bottom — мероприятия и коды\n'
    '            // под таблицей. Task 439: внутри обёртки — РЯД:\n'
    '            // мероприятия слева, коды СПРАВА от них (CSS flex).\n'
    '            // Task 433 (заявка: «расположение кодов в печати верни\n'
    '            // обратно, я имел в виду, что бы правая часть блока\n'
    '            // растянулась вправо до конца листа, и если текст не\n'
    '            // будет вмещаться в одну строку, тогда переносить его на\n'
    '            // следующую строку»): нижняя секция снова ВЕРТИКАЛЬНАЯ\n'
    '            // (флоат Task 432 и flex-ряд Task 364–431 сняты):\n'
    '            // ПЕРВЫМ в DOM — список мероприятий (записи-блоки\n'
    '            // [точка][дата][текст], текст растянут до конца листа,\n'
    '            // перенос — только когда не вмещается в одну строку),\n'
    '            // ВТОРЫМ — коды ЕДИНОЙ СТРОКОЙ-АБЗАЦЕМ «Коды: …»\n'
    '            // (исходное расположение до Task 360), сноска — ниже\n',
    '            // Task 364: обёртка wsp-bottom под таблицей.\n'
    '            // Task 442 (заявка: «убери … столбец с кодами»):\n'
    '            // ЛЕГЕНДА КОДОВ УДАЛЕНА — в нижней секции остался\n'
    '            // ТОЛЬКО список мероприятий (Task 433: записи-блоки\n'
    '            // [точка][дата][текст], текст растянут до конца листа,\n'
    '            // перенос — только когда не вмещается в одну строку)\n',
    'bottom-comment')

rep(
    "            html += '</div>';\n"
    '            // Task 360 (заявка: «а под списком, в один столбик\n'
    '            // перечень кодов с их наименованием только которые есть\n'
    '            // в этом месяце»): в печать идут ТОЛЬКО коды,\n'
    '            // ПРИСУТСТВУЮЩИЕ в этом месяце (usedCodes — эффективные\n'
    '            // записи печатаемых строк, см. выше). Порядок —\n'
    '            // справочник _STATUS_CODES (единственный источник имён);\n'
    '            // легаси-код, удалённый из справочника, попадает в\n'
    '            // конец без цвета и имени (только код).\n'
    '            // Task 433 (заявка: «расположение кодов в печати верни\n'
    '            // обратно»): ВЕРНУЛИ ИСХОДНУЮ ФОРМУ «в одну строку"\n'
    '            // (как до Task 360; столбик Task 360–431 и флоат Task 432\n'
    '            // сняты). Task 434 (заявка: «коды на печати сделать в\n'
    '            // две колонки под названием "Коды:""): заголовок —\n'
    '            // ОТДЕЛЬНОЙ строкой, под ним колонка кодов; Task 441 (заявка:\n'
    '            // «коды сделай в один столбец»): ОДНА колонка\n'
    '            // (.wsp-legend-cols, grid 1fr) на всю ширину блока:\n'
    '            // каждый код — своя строка, длинное название\n'
    '            // переносится ВНУТРИ колонки (запись не рвётся)\n'
    '            var codes = this._STATUS_CODES || [];\n'
    "            html += '<div class=\"wsp-legend\"><span class=\"wsp-legend-t\">Коды:</span>' +\n"
    "                    '<div class=\"wsp-legend-cols\">';\n"
    '            for (var ci = 0; ci < codes.length; ci++) {\n'
    '                // Task 387: «.» в данных = выходной — раскрывается\n'
    '                // строкой «Выходного» (пустой код) БЕЗ кода-символа\n'
    '                if (!usedCodes[codes[ci].code] &&\n'
    "                    !(codes[ci].code === '' && usedCodes['.'])) continue;\n"
    "                if (codes[ci].code === '') {\n"
    "                    html += '<span class=\"wsp-lg\"><i style=\"background:' +\n"
    "                            (codes[ci].color || '#ffffff') + ';\"></i>' +\n"
    "                            this._esc(codes[ci].name || 'Выходной') +\n"
    "                            '</span>';\n"
    '                    continue;\n'
    '                }\n'
    '                // Task 438 (заявка: «список кодов — в сокращённом\n'
    '                // виде»): после кода — КОРОТКОЕ обозначение\n'
    '                // (short из справочника, Task 388), у самодельных\n'
    '                // кодов вне канона short нет — фолбэк на name\n'
    "                var lgShort = codes[ci].short || codes[ci].name || '';\n"
    "                html += '<span class=\"wsp-lg\"><i style=\"background:' +\n"
    "                        (codes[ci].color || '#ffffff') + ';\"></i>' +\n"
    "                        this._esc(codes[ci].code) +\n"
    "                        (lgShort ? ' — ' + this._esc(lgShort) : '') +\n"
    "                        '</span>';\n"
    '            }\n'
    '            // легаси-коды месяца, которых нет в справочнике.\n'
    '            // Task 438: «.» пропускается — точка уже раскрыта слотом\n'
    '            // «Выходной» (пустой код) выше, дублирующая голая «.»\n'
    '            // в перечне не нужна\n'
    '            var legacy = [];\n'
    '            for (var lk in usedCodes) {\n'
    '                if (!Object.prototype.hasOwnProperty.call(usedCodes, lk)) continue;\n'
    "                if (lk === '.') continue;\n"
    '                var known = false;\n'
    '                for (var cj = 0; cj < codes.length; cj++) {\n'
    "                    if (codes[cj].code === lk) { known = true; break; }\n"
    '                }\n'
    '                if (!known) legacy.push(lk);\n'
    '            }\n'
    '            legacy.sort();\n'
    '            for (var li = 0; li < legacy.length; li++) {\n'
    "                html += '<span class=\"wsp-lg\">' + this._esc(legacy[li]) + '</span>';\n"
    '            }\n'
    '            // Task 434: закрытие ДВУХ уровней — сетка-колонки\n'
    '            // .wsp-legend-cols и сама легенда .wsp-legend\n'
    "            html += '</div>';\n"
    "            html += '</div>';\n",
    "            html += '</div>';\n"
    '            // Task 442: легенда кодов (wsp-legend/wsp-lg, Tasks\n'
    '            // 360–441) УДАЛЕНА по заявке — закрывается только\n'
    '            // обёртка wsp-bottom; перечень кодов месяца больше\n'
    '            // не печатается\n',
    'legend-remove')

rep(
    '            // Task 438 (заявка): пояснительная сноска wsp-foot\n'
    '            // («* — сокращённый предпраздничный…») УДАЛЕНА — лист\n'
    '            // заканчивается перечнем кодов\n',
    '            // Task 438 (заявка): пояснительная сноска wsp_foot\n'
    '            // («* — сокращённый предпраздничный…») УДАЛЕНА; Task\n'
    '            // 442: лист заканчивается списком мероприятий\n',
    'foot-comment')

# ============================================================
# 11. JS _printCell: полная замена (бейджи удалены, контур)
# ============================================================
rep(
    '        // Task 341: ячейка печатной шахматки — упрощённый _renderCell\n'
    '        // без экранных фич (клики/подсветки/сегодня), цвета — inline\n'
    '        // из справочника (печать фонов — print-color-adjust: exact):\n'
    '        // основной код фоном; «.» — пустая; план отпуска — пунктир;\n'
    '        // переработка — красная точка; пустые нерабочие — серая\n'
    '        // заливка (wsp-cell-off, как розовая в сетке — только ПУСТЫЕ\n'
    '        // ячейки, статусные сохраняют свой цвет). Task 361 (заявка:\n'
    '        // «сделай отображение на печати значков мероприятий в\n'
    '        // ячейках шахматки»): бейджи мероприятий ВЕРНУТЫ в печать\n'
    '        // (Task 343 их убирал) — статус-мероприятие печатается\n'
    '        // ПУСТОЙ ячейкой + бейдж в углу, события дня — бейджами\n'
    '        // (как в экранной сетке, Task 314)\n'
    '        _printCell: function(day, isoDate, emp, entry) {\n'
    "            var status = entry ? entry.статус : '';\n"
    '            var isOvertime = !!(entry && entry.переработка === 1);\n'
    "            var isDotCode = (status === '.');\n"
    '            var isEventStatus = !!status &&\n'
    '                this._EVENT_CODES.indexOf(status) !== -1;\n'
    '            var showMainCode = !!status && !isDotCode && !isEventStatus;\n'
    '\n'
    "            var classes = ['wsp-cell'];\n"
    "            var style = '';\n"
    '            if (showMainCode) {\n'
    '                var meta = this._statusMeta(status) || {};\n'
    "                if (meta.color) style += 'background:' + meta.color + ';';\n"
    '            }\n'
    '            // нерабочие дни (производственный календарь): заливка —\n'
    '            // только ПУСТЫМ ячейкам без плана (статусные — свой цвет)\n'
    '            var dayOff = this._calDayOff(day);\n'
    '            // план отпуска в пустой ячейке — пунктирная рамка\n'
    '            var vacPlan = null;\n'
    '            if (!status) {\n'
    "                vacPlan = this._vacationAt(isoDate, emp['таб_номер']);\n"
    "                if (vacPlan) classes.push('wsp-vac');\n"
    '            }\n'
    "            if (dayOff && !showMainCode && !vacPlan) classes.push('wsp-cell-off');\n"
    '\n'
    "            var content = showMainCode ? this._esc(status) : '';\n"
    "            if (isOvertime) content += '<i class=\"wsp-over\"></i>';\n"
    '\n'
    '            // Task 361 (заявка: «сделай отображение на печати\n'
    '            // значков мероприятий в ячейках шахматки»): бейджи\n'
    '            // мероприятий в печати ВЕРНУТЫ (Task 343 их убирал).\n'
    '            // Формат — как в экранной сетке (Task 314/388): события\n'
    '            // дня из листа «Инструктажи» (_eventsAt) — ВСЕГДА сплошные\n'
    '            // бейджи с inline-цветом кода (Task 388: пунктирные\n'
    '            // wsp-ev-plan у пустой ячейки/плана отпуска удалены);\n'
    '            // статус-мероприятие (И/ОБ/ПЗ/ПР/*) без строки в\n'
    '            // «Инструктажах» — виртуальный бейдж, чтобы день не\n'
    '            // «потерял» мероприятие. Точка переработки — правый\n'
    '            // ВЕРХНИЙ угол, бейджи — правый нижний (без конфликтов)\n'
    '            var events = (typeof this._eventsAt === \'function\')\n'
    '                ? (this._eventsAt(isoDate, emp[\'таб_номер\']) || []) : [];\n'
    '            if (isEventStatus) {\n'
    '                var covered = false;\n'
    '                for (var ci = 0; ci < events.length; ci++) {\n'
    '                    if (events[ci].code === status) { covered = true; break; }\n'
    '                }\n'
    '                if (!covered) {\n'
    '                    events = events.concat([{ code: status, training: null }]);\n'
    '                }\n'
    '            }\n'
    "            var evHtml = '';\n"
    '            if (events.length) {\n'
    '                // Task 388: бейдж печати ВСЕГДА сплошной с цветом\n'
    '                // кода (как экранная сетка; прежде пустая/план\n'
    '                // ячейка давала пунктирный wsp-ev-plan без заливки)\n'
    "                var chips = '';\n"
    '                for (var evj = 0; evj < events.length; evj++) {\n'
    '                    var evMeta = this._statusMeta(events[evj].code) || {};\n'
    "                    chips += '<span class=\"wsp-ev\"' +\n"
    "                             (evMeta.color ? ' style=\"background:' + evMeta.color + ';\"' : '') +\n"
    "                             '>' + this._esc(events[evj].code) + '</span>';\n"
    '                }\n'
    "                evHtml = '<span class=\"wsp-ev-wrap\">' + chips + '</span>';\n"
    '            }\n'
    '            return \'<td class="\' + classes.join(\' \') + \'"\' +\n'
    '                   (style ? \' style="\' + style + \'"\' : \'\') + \'>\' +\n'
    '                   content + evHtml + \'</td>\';\n'
    '        },\n',
    '        // Task 341: ячейка печатной шахматки — упрощённый _renderCell\n'
    '        // без экранных фич (клики/подсветки/сегодня), цвета — inline\n'
    '        // из справочника (печать фонов — print-color-adjust: exact):\n'
    '        // основной код фоном; «.» — пустая; план отпуска — пунктир;\n'
    '        // переработка — красная точка. Task 442 (заявка: «' + Z + ',\n'
    '        // и внешний контур линий выходных календарных дней в шахматке\n'
    '        // сделай толще, а выделять их фоном не нужно»): бейджи\n'
    '        // мероприятий в печати УДАЛЕНЫ (Task 361 их возвращал) —\n'
    '        // статус-мероприятия (И/ОБ/ПЗ/ПР/*) печатаются ПУСТЫМИ\n'
    '        // ячейками (события месяца — списком под таблицей);\n'
    '        // серая заливка нерабочих дней снята — вместо неё ТОЛСТЫЙ\n'
    '        // ВНЕШНИЙ КОНТУР полосы выходных (wsp-cell-off — маркер\n'
    '        // колонки выходного дня, wsp-off-edge-l/r — края полосы\n'
    '        // по соседям, wsp-off-edge-b — низ последней строки)\n'
    '        _printCell: function(day, isoDate, emp, entry, isLastRow) {\n'
    "            var status = entry ? entry.статус : '';\n"
    '            var isOvertime = !!(entry && entry.переработка === 1);\n'
    "            var isDotCode = (status === '.');\n"
    '            var isEventStatus = !!status &&\n'
    '                this._EVENT_CODES.indexOf(status) !== -1;\n'
    '            var showMainCode = !!status && !isDotCode && !isEventStatus;\n'
    '\n'
    "            var classes = ['wsp-cell'];\n"
    "            var style = '';\n"
    '            if (showMainCode) {\n'
    '                var meta = this._statusMeta(status) || {};\n'
    "                if (meta.color) style += 'background:' + meta.color + ';';\n"
    '            }\n'
    '            // план отпуска в пустой ячейке — пунктирная рамка\n'
    '            if (!status && this._vacationAt(isoDate, emp[\'таб_номер\'])) {\n'
    "                classes.push('wsp-vac');\n"
    '            }\n'
    '            // Task 442: нерабочий день (производственный календарь)\n'
    '            // — БЕЗ заливки: ВСЕ ячейки колонки получают маркер\n'
    '            // wsp-cell-off (толстый внешний контур полосы выходных);\n'
    '            // края полосы — по соседям (Сб+Вс подряд — один\n'
    '            // контур), низ — у последней строки таблицы\n'
    '            if (this._calDayOff(day)) {\n'
    "                classes.push('wsp-cell-off');\n"
    '                var dim = new Date(this._year, this._month, 0).getDate();\n'
    '                var prevOff = day > 1 && this._calDayOff(day - 1);\n'
    '                var nextOff = day < dim && this._calDayOff(day + 1);\n'
    "                if (!prevOff) classes.push('wsp-off-edge-l');\n"
    "                if (!nextOff) classes.push('wsp-off-edge-r');\n"
    "                if (isLastRow) classes.push('wsp-off-edge-b');\n"
    '            }\n'
    '\n'
    "            var content = showMainCode ? this._esc(status) : '';\n"
    "            if (isOvertime) content += '<i class=\"wsp-over\"></i>';\n"
    '            return \'<td class="\' + classes.join(\' \') + \'"\' +\n'
    '                   (style ? \' style="\' + style + \'"\' : \'\') + \'>\' +\n'
    '                   content + \'</td>\';\n'
    '        },\n',
    'printcell')

# ============================================================
io.open(P, 'w', encoding='utf-8').write(s)
print()
print('=== ИТОГ (патч 1: CSS + _buildPrintHtml + _printCell) ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ВСЕ ЗАМЕНЫ ПРИМЕНИЛИСЬ. Δдлина: %+d символов' % (len(s) - orig_len))
