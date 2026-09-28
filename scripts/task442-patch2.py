#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442 (kip8test), патч 2 из 3: _printModel (бейджи/коды удалены),
# _printCodesData УДАЛЁН, _printPdfLayout (зона кодов снята),
# _printPdfPaintPage (контур выходных, жирные даты, без бейджей/кодов).
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


Z = 'убери мини значки мероприятий в шахматке и столбец с кодами'

# ============================================================
# 1. _printModel: докстринг
# ============================================================
rep(
    '        // Task 438: МОДЕЛЬ печатной формы (чистая, без DOM — для\n'
    '        // VM-тестов). Логика повторяет _buildPrintHtml/_printCell\n'
    '        // (Tasks 341/360/361/362): дни месяца с выходными/празд-\n'
    '        // никами/«*» сокращённых; строки печатаемого вида с\n'
    '        // ЭФФЕКТИВНЫМИ записями (запись + локальная правка,\n'
    '        // __delete — пустая ячейка); цвет/текст основного кода,\n'
    '        // пунктирный план отпуска, точка переработки, бейджи\n'
    '        // мероприятий; построчные итоги «Дни»/«Перераб.» (только\n'
    '        // дни — Task 438); события месяца (Task 360/362 — записи\n'
    '        // листа «Инструктажи», пересекающие месяц, в видах\n'
    '        // «сменный»/«дневной» — только печатаемые строки) и\n'
    '        // перечень используемых кодов в сокращённом виде\n',
    '        // Task 438: МОДЕЛЬ печатной формы (чистая, без DOM — для\n'
    '        // VM-тестов). Логика повторяет _buildPrintHtml/_printCell\n'
    '        // (Tasks 341/360/362): дни месяца с выходными/праздниками/\n'
    '        // «*» сокращённых (off — полосы выходных для контура и\n'
    '        // жирных чисел, Task 442); строки печатаемого вида с\n'
    '        // ЭФФЕКТИВНЫМИ записями (запись + локальная правка,\n'
    '        // __delete — пустая ячейка); цвет/текст основного кода,\n'
    '        // пунктирный план отпуска, точка переработки; построчные\n'
    '        // итоги «Дни»/«Перераб.» (только дни — Task 438); события\n'
    '        // месяца (Task 360/362 — записи листа «Инструктажи»,\n'
    '        // пересекающие месяц, в видах «сменный»/«дневной» — только\n'
    '        // печатаемые строки). Task 442: бейджи мероприятий в\n'
    '        // ячейках и перечень кодов УДАЛЕНЫ из модели (заявка:\n'
    '        // «' + Z + '»)\n',
    'doc-printmodel')

# ============================================================
# 2. _printModel: строки — var usedCodes удалён
# ============================================================
rep(
    '            var entryIdx = this._buildEntryIndex();\n'
    '            var pend = this._PENDING || {};\n'
    '            var rows = [];\n'
    '            var usedCodes = {};\n',
    '            var entryIdx = this._buildEntryIndex();\n'
    '            var pend = this._PENDING || {};\n'
    '            var rows = [];\n',
    'model-usedcodes-var')

# ============================================================
# 3. _printModel: клетки без бейджей, usedCodes-сбор удалён
# ============================================================
rep(
    '                    var status = eff ? eff.статус : \'\';\n'
    "                    var isDot = (status === '.');\n"
    '                    var isEvSt = !!status &&\n'
    '                        this._EVENT_CODES.indexOf(status) !== -1;\n'
    '                    var meta = (status && !isDot && !isEvSt)\n'
    '                        ? (this._statusMeta(status) || {}) : {};\n'
    '                    var evs = (typeof this._eventsAt === \'function\')\n'
    '                        ? (this._eventsAt(isoDate, emp[\'таб_номер\']) || [])\n'
    '                        : [];\n'
    '                    if (isEvSt) {\n'
    '                        var covered = false;\n'
    '                        for (var ei = 0; ei < evs.length; ei++) {\n'
    '                            if (evs[ei].code === status) { covered = true; break; }\n'
    '                        }\n'
    '                        if (!covered) {\n'
    '                            evs = evs.concat([{ code: status, training: null }]);\n'
    '                        }\n'
    '                    }\n'
    '                    var badges = [];\n'
    '                    for (var bi = 0; bi < evs.length; bi++) {\n'
    '                        var bMeta = this._statusMeta(evs[bi].code) || {};\n'
    '                        badges.push({ code: evs[bi].code,\n'
    '                                      color: bMeta.color || \'\' });\n'
    '                    }\n'
    '                    cells.push({\n'
    "                        status: (!isDot && !isEvSt) ? status : '',\n"
    "                        color: meta.color || '',\n"
    '                        overtime: !!(eff && eff.переработка === 1),\n'
    '                        vac: !status\n'
    "                            ? !!this._vacationAt(isoDate, emp['таб_номер'])\n"
    '                            : false,\n'
    '                        events: badges\n'
    '                    });\n'
    "                    if (eff && eff.статус) usedCodes[eff.статус] = true;\n",
    '                    var status = eff ? eff.статус : \'\';\n'
    "                    var isDot = (status === '.');\n"
    '                    var isEvSt = !!status &&\n'
    '                        this._EVENT_CODES.indexOf(status) !== -1;\n'
    '                    var meta = (status && !isDot && !isEvSt)\n'
    '                        ? (this._statusMeta(status) || {}) : {};\n'
    '                    // Task 442: бейджи мероприятий в печатной\n'
    '                    // шахматке УДАЛЕНЫ — статус-мероприятия дают\n'
    '                    // ПУСТУЮ клетку (события месяца — списком под\n'
    '                    // таблицей), поле events в модели снято\n'
    '                    cells.push({\n'
    "                        status: (!isDot && !isEvSt) ? status : '',\n"
    "                        color: meta.color || '',\n"
    '                        overtime: !!(eff && eff.переработка === 1),\n'
    '                        vac: !status\n'
    "                            ? !!this._vacationAt(isoDate, emp['таб_номер'])\n"
    '                            : false\n'
    '                    });\n',
    'model-cells')

# ============================================================
# 4. _printModel: возврат без codes
# ============================================================
rep(
    '            var events = this._printEventsData(viewEmps);\n'
    '            return {\n'
    '                year: this._year, month: this._month, view: this._view,\n'
    '                days: days, rows: rows, usedCodes: usedCodes,\n'
    '                events: events,\n'
    '                codes: this._printCodesData(usedCodes, events)\n'
    '            };\n',
    '            var events = this._printEventsData(viewEmps);\n'
    '            // Task 442: перечень кодов (codes/_printCodesData)\n'
    '            // УДАЛЕН из модели — столбца кодов в представлениях\n'
    '            // печати больше нет (заявка)\n'
    '            return {\n'
    '                year: this._year, month: this._month, view: this._view,\n'
    '                days: days, rows: rows, events: events\n'
    '            };\n',
    'model-return')

# ============================================================
# 5. _printCodesData — метод УДАЛЁН целиком
# ============================================================
rep(
    '        // Task 438: перечень кодов месяца для PDF/Excel — порядок\n'
    '        // справочника _STATUS_CODES (как в печати), «.» — слот\n'
    '        // «Выходной», обозначение — СОКРАЩЁННОЕ (short, Task 388;\n'
    '        // у кодов вне канона short нет — фолбэк name); легаси-коды\n'
    '        // месяца вне справочника — в конец без цвета (только код).\n'
    '        // Коды мероприятий (Task 362) тоже попадают в перечень\n'
    '        _printCodesData: function(usedCodes, events) {\n'
    '            var used = {};\n'
    '            for (var k in usedCodes) {\n'
    '                if (Object.prototype.hasOwnProperty.call(usedCodes, k)) {\n'
    '                    used[k] = true;\n'
    '                }\n'
    '            }\n'
    '            for (var i = 0; i < (events || []).length; i++) {\n'
    '                if (events[i].code) used[events[i].code] = true;\n'
    '            }\n'
    '            var codes = this._STATUS_CODES || [];\n'
    '            var out = [];\n'
    '            for (var ci = 0; ci < codes.length; ci++) {\n'
    '                if (!used[codes[ci].code] &&\n'
    "                    !(codes[ci].code === '' && used['.'])) continue;\n"
    '                out.push({ code: codes[ci].code,\n'
    '                           label: codes[ci].short || codes[ci].name || \'\',\n'
    "                           color: codes[ci].color || '' });\n"
    '            }\n'
    '            var legacy = [];\n'
    '            for (var lk in used) {\n'
    '                if (!Object.prototype.hasOwnProperty.call(used, lk)) continue;\n'
    '                // «.» уже раскрыт слотом «Выходной» (пустой код)\n'
    "                if (lk === '.') continue;\n"
    '                var known = false;\n'
    '                for (var cj = 0; cj < codes.length; cj++) {\n'
    "                    if (codes[cj].code === lk) { known = true; break; }\n"
    '                }\n'
    '                if (!known) legacy.push(lk);\n'
    '            }\n'
    '            legacy.sort();\n'
    '            for (var li = 0; li < legacy.length; li++) {\n'
    "                out.push({ code: legacy[li], label: '', color: '' });\n"
    '            }\n'
    '            return out;\n'
    '        },\n'
    '\n',
    '        // Task 442: метод _printCodesData (перечень кодов месяца\n'
    '        // для PDF/Excel, Tasks 438–441) УДАЛЁН по заявке\n'
    '        // («убери … столбец с кодами») — столбца кодов в\n'
    '        // представлениях печати больше нет\n',
    'printcodesdata-remove')

# ============================================================
# 6. _printPdfLayout: докстринг + тело (зона кодов снята)
# ============================================================
rep(
    '        // Task 438: РАСКЛАДКА СТРАНИЦ PDF (чистая, без DOM —\n'
    '        // VM-тесты). A4 альбомная 842×595 pt, поля 8 мм ≈ 23 pt.\n'
    '        // Страницы: [шапка (только первая) +] лента дней + строки\n'
    '        // сотрудников (граница — только по строкам, лента\n'
    '        // повторяется на каждой странице с таблицей); мероприятия\n'
    '        // и коды — РЯДОМ ДРУГ С ДРУГОМ (Task 439: события слева,\n'
    '        // коды справа, общая верхняя линия) на последней странице\n'
    '        // под таблицей, если влезают, иначе отдельными страницами\n'
    '        // (события режутся по высоте, коды — всегда одной\n'
    '        // страницей)\n'
    '        _printPdfLayout: function(model, opts) {\n'
    '            opts = opts || {};\n'
    '            var W = opts.W || 842, H = opts.H || 595, M = opts.M || 23;\n'
    '            var headH = opts.headH || 34;\n'
    '            var dayHeadH = opts.dayHeadH || 24;\n'
    '            var rowH = opts.rowH || 22;\n'
    '            var secH = opts.secH || 18;\n'
    '            var evRowH = opts.evRowH || 13;\n'
    '            var codeRowH = opts.codeRowH || 14;\n'
    '            var gapH = opts.gapH || 8;\n'
    '            // Task 439: коды — СПРАВА от мероприятий: ширина\n'
    '            // правой зоны кодов и зазор между блоками. Task 440\n'
    '            // (заявка: «на расстоянии друг от друга 10px»): зазор\n'
    '            // 12pt → 7.5pt — РОВНО 10 CSS-px (1px = 0.75pt), как в\n'
    '            // печатной HTML-форме (gap: 10px)\n'
    '            var codeW = opts.codeW || 235;\n'
    '            var colGap = opts.colGap || 7.5;\n'
    '            var contentH = H - 2 * M;\n'
    '            var evList = (model.events || []).length\n'
    '                ? model.events : [{ placeholder: true }];\n'
    '            // Task 441 (заявка: «коды сделай в один столбец»):\n'
    '            // ОДНА колонка — строк на код не делим (прежде\n'
    '            // ДВЕ колонки: ceil(n/2) строк, Task 434/439)\n'
    '            var codeRows = Math.max(1,\n'
    '                (model.codes || []).length);\n'
    '            // оценка числа строк записи мероприятия (тексты\n'
    '            // краткие — обычно 1 строка; оценка консервативная\n'
    '            // ~4.6pt/символ, реальная укладка по словам — в\n'
    '            // отрисовке _printPdfPaintPage)\n'
    '            var evW = W - 2 * M - codeW - colGap;\n',
    '        // Task 438: РАСКЛАДКА СТРАНИЦ PDF (чистая, без DOM —\n'
    '        // VM-тесты). A4 альбомная 842×595 pt, поля 8 мм ≈ 23 pt.\n'
    '        // Страницы: [шапка (только первая) +] лента дней + строки\n'
    '        // сотрудников (граница — только по строкам, лента\n'
    '        // повторяется на каждой странице с таблицей); мероприятия\n'
    '        // — на последней странице под таблицей, если влезают,\n'
    '        // иначе отдельными страницами (события режутся по высоте).\n'
    '        // Task 442: зоны кодов справа больше нет (столбец кодов\n'
    '        // удалён по заявке) — мероприятия занимают всю ширину\n'
    '        // листа; codeRowH сохранён в раскладке для совместимости\n'
    '        // callers, в отрисовке не используется\n'
    '        _printPdfLayout: function(model, opts) {\n'
    '            opts = opts || {};\n'
    '            var W = opts.W || 842, H = opts.H || 595, M = opts.M || 23;\n'
    '            var headH = opts.headH || 34;\n'
    '            var dayHeadH = opts.dayHeadH || 24;\n'
    '            var rowH = opts.rowH || 22;\n'
    '            var secH = opts.secH || 18;\n'
    '            var evRowH = opts.evRowH || 13;\n'
    '            var codeRowH = opts.codeRowH || 14;\n'
    '            var gapH = opts.gapH || 8;\n'
    '            var contentH = H - 2 * M;\n'
    '            var evList = (model.events || []).length\n'
    '                ? model.events : [{ placeholder: true }];\n'
    '            // оценка числа строк записи мероприятия (тексты\n'
    '            // краткие — обычно 1 строка; оценка консервативная\n'
    '            // ~4.6pt/символ, реальная укладка по словам — в\n'
    '            // отрисовке _printPdfPaintPage); Task 442: зона —\n'
    '            // ВСЯ ширина листа (прежде минус блок кодов)\n'
    '            var evW = W - 2 * M;\n',
    'layout-head')

rep(
    '            var evLines = 0;\n'
    '            for (var li = 0; li < evList.length; li++) {\n'
    '                evLines += evLinesOf(evList[li]);\n'
    '            }\n'
    '            // Task 439: блоки РЯДОМ — высота пары = максимум, а не\n'
    '            // сумма (коды не добавляются под мероприятиями)\n'
    '            var evH = secH + evLines * evRowH;\n'
    '            var cdH = secH + codeRows * codeRowH;\n'
    '            var botH = Math.max(evH, cdH);\n',
    '            var evLines = 0;\n'
    '            for (var li = 0; li < evList.length; li++) {\n'
    '                evLines += evLinesOf(evList[li]);\n'
    '            }\n'
    '            // Task 442: нижний блок — только мероприятия (высота\n'
    '            // пары max(evH, cdH) из Tasks 439/440 снята вместе с\n'
    '            // блоком кодов)\n'
    '            var botH = secH + evLines * evRowH;\n',
    'layout-both')

rep(
    '                if (i >= rows.length && used + botH <= contentH) {\n'
    '                    // последняя страница таблицы: мероприятия и коды\n'
    '                    // помещаются под ней\n'
    '                    pages.push({ first: first, rows: chunk,\n'
    '                                 events: model.events || [],\n'
    '                                 codes: model.codes || [] });\n'
    '                    return { pages: pages, W: W, H: H, M: M, headH: headH,\n'
    '                             dayHeadH: dayHeadH, rowH: rowH, secH: secH,\n'
    '                             evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,\n'
    '                             codeW: codeW, colGap: colGap, evW: evW };\n'
    '                }\n'
    '                pages.push({ first: first, rows: chunk,\n'
    '                             events: null, codes: null });\n'
    '            }\n'
    '            // мероприятия (+ коды, если влезут) — отдельными\n'
    '            // страницами; пустой месяц — строка-заглушка (как в\n'
    '            // печати: «нет мероприятий в этом месяце»)\n',
    '                if (i >= rows.length && used + botH <= contentH) {\n'
    '                    // последняя страница таблицы: мероприятия\n'
    '                    // помещаются под ней\n'
    '                    pages.push({ first: first, rows: chunk,\n'
    '                                 events: model.events || [] });\n'
    '                    return { pages: pages, W: W, H: H, M: M, headH: headH,\n'
    '                             dayHeadH: dayHeadH, rowH: rowH, secH: secH,\n'
    '                             evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,\n'
    '                             evW: evW };\n'
    '                }\n'
    '                pages.push({ first: first, rows: chunk, events: null });\n'
    '            }\n'
    '            // мероприятия — отдельными страницами; пустой месяц —\n'
    '            // строка-заглушка (как в печати: «нет мероприятий в\n'
    '            // этом месяце»)\n',
    'layout-lastpage')

rep(
    '                var evChunk = evList.slice(ei, ei + take);\n'
    '                ei += take;\n'
    '                var chunkLines = evCap - budget;\n'
    '                // коды — РЯДОМ с последним куском событий (влезают\n'
    '                // по ВЫСОТЕ пары — max, не сумма)\n'
    '                var withCodes = (ei >= evList.length) &&\n'
    '                                (Math.max(secH + chunkLines * evRowH,\n'
    '                                          cdH) <= contentH);\n'
    '                if (withCodes) codesPlaced = true;\n'
    '                pages.push({ first: false, rows: [], events: evChunk,\n'
    '                             codes: withCodes ? (model.codes || []) : null });\n'
    '            }\n'
    '            if (!codesPlaced) {\n'
    '                pages.push({ first: false, rows: [], events: null,\n'
    '                             codes: model.codes || [] });\n'
    '            }\n'
    '            return { pages: pages, W: W, H: H, M: M, headH: headH,\n'
    '                     dayHeadH: dayHeadH, rowH: rowH, secH: secH,\n'
    '                     evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,\n'
    '                     codeW: codeW, colGap: colGap, evW: evW };\n'
    '        },\n',
    '                var evChunk = evList.slice(ei, ei + take);\n'
    '                ei += take;\n'
    '                pages.push({ first: false, rows: [], events: evChunk });\n'
    '            }\n'
    '            return { pages: pages, W: W, H: H, M: M, headH: headH,\n'
    '                     dayHeadH: dayHeadH, rowH: rowH, secH: secH,\n'
    '                     evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,\n'
    '                     evW: evW };\n'
    '        },\n',
    'layout-evpages')

# var codesPlaced больше не нужен
rep(
    '            var ei = 0;\n'
    '            var codesPlaced = false;\n'
    '            while (ei < evList.length) {\n'
    '                // Task 439: страница событий набирается по бюджету\n'
    '                // СТРОК (длинная запись может занимать две)\n',
    '            var ei = 0;\n'
    '            while (ei < evList.length) {\n'
    '                // Task 439: страница событий набирается по бюджету\n'
    '                // СТРОК (длинная запись может занимать две)\n',
    'layout-codesplaced')

# ============================================================
# 7. _printPdfPaintPage: лента дней — без заливки выходных,
#    жирные числа выходных
# ============================================================
rep(
    '                for (var dd = 0; dd < nDays; dd++) {\n'
    '                    var day = model.days[dd];\n'
    '                    var dx = x0 + empW + dd * dayW;\n'
    '                    if (day.off) {\n'
    "                        ctx.fillStyle = '#dfe5e9';\n"
    '                        ctx.fillRect(dx, yTop, dayW, lay.dayHeadH);\n'
    '                    }\n'
    '                    ctx.textAlign = \'center\';\n'
    "                    ctx.fillStyle = day.feast ? '#b02a2a' : '#1b1f24';\n"
    "                    ctx.font = '700 7px Arial';\n"
    '                    ctx.fillText(String(day.d) + (day.short ? \'*\' : \'\'),\n'
    '                                 dx + dayW / 2, yTop + 9);\n'
    "                    ctx.fillStyle = '#54606a';\n"
    "                    ctx.font = '5.5px Arial';\n"
    '                    ctx.fillText(day.dow, dx + dayW / 2, yTop + 17);\n'
    '                    ctx.textAlign = \'left\';\n'
    '                    gridLine(dx, yTop, dayW, lay.dayHeadH);\n'
    '                }\n',
    '                for (var dd = 0; dd < nDays; dd++) {\n'
    '                    var day = model.days[dd];\n'
    '                    var dx = x0 + empW + dd * dayW;\n'
    '                    // Task 442: заливки выходных в шапке НЕТ;\n'
    '                    // число выходного дня — ЖИРНОЕ, обычные дни —\n'
    '                    // обычное начертание (как в HTML-печати)\n'
    '                    ctx.textAlign = \'center\';\n'
    "                    ctx.fillStyle = day.feast ? '#b02a2a' : '#1b1f24';\n"
    "                    ctx.font = (day.off ? '700 ' : '') + '7px Arial';\n"
    '                    ctx.fillText(String(day.d) + (day.short ? \'*\' : \'\'),\n'
    '                                 dx + dayW / 2, yTop + 9);\n'
    "                    ctx.fillStyle = '#54606a';\n"
    "                    ctx.font = '5.5px Arial';\n"
    '                    ctx.fillText(day.dow, dx + dayW / 2, yTop + 17);\n'
    '                    ctx.textAlign = \'left\';\n'
    '                    gridLine(dx, yTop, dayW, lay.dayHeadH);\n'
    '                }\n',
    'paint-dayhead')

# ============================================================
# 8. _printPdfPaintPage: строки — контур полос выходных,
#    заливка выходных и бейджи удалены
# ============================================================
rep(
    '            // строки сотрудников\n'
    '            if (page.rows.length) {\n'
    '                drawDayHead(y);\n'
    '                y += lay.dayHeadH;\n',
    '            // строки сотрудников\n'
    '            if (page.rows.length) {\n'
    '                // Task 442: gridTop — верх полос выходных\n'
    '                // (толстый контур от ленты дней до низа\n'
    '                // последней строки)\n'
    '                var gridTop = y;\n'
    '                drawDayHead(y);\n'
    '                y += lay.dayHeadH;\n',
    'paint-gridtop')

rep(
    '                        var dyy = model.days[cc];\n'
    '                        if (cell.status && cell.color) {\n'
    '                            ctx.fillStyle = cell.color;\n'
    '                            ctx.fillRect(dx, y, dayW, lay.rowH);\n'
    '                        } else if (!cell.status && !cell.vac && dyy.off) {\n'
    "                            ctx.fillStyle = '#e2e8ec';\n"
    '                            ctx.fillRect(dx, y, dayW, lay.rowH);\n'
    '                        }\n',
    '                        var dyy = model.days[cc];\n'
    '                        // Task 442: серой заливки нерабочих дней\n'
    '                        // больше нет (только цвет статуса);\n'
    '                        // бейджи мероприятий удалены (ниже)\n'
    '                        if (cell.status && cell.color) {\n'
    '                            ctx.fillStyle = cell.color;\n'
    '                            ctx.fillRect(dx, y, dayW, lay.rowH);\n'
    '                        }\n',
    'paint-cellfill')

rep(
    '                        if (cell.overtime) {\n'
    "                            ctx.fillStyle = '#d32f2f';\n"
    '                            ctx.beginPath();\n'
    '                            ctx.arc(dx + dayW - 2.5, y + 3.2, 1.4,\n'
    '                                    0, Math.PI * 2);\n'
    '                            ctx.fill();\n'
    '                        }\n'
    '                        // бейджи мероприятий — правый нижний угол\n'
    '                        for (var bb = 0; bb < cell.events.length && bb < 3; bb++) {\n'
    '                            var bw = 3.4;\n'
    '                            var bx = dx + dayW - 2 - bw -\n'
    '                                     bb * (bw + 0.8);\n'
    '                            ctx.fillStyle = cell.events[bb].color ||\n'
    '                                            \'#3a3a3a\';\n'
    '                            ctx.fillRect(bx, y + lay.rowH - 2 - bw,\n'
    '                                         bw, bw);\n'
    '                        }\n'
    '                        gridLine(dx, y, dayW, lay.rowH);\n',
    '                        if (cell.overtime) {\n'
    "                            ctx.fillStyle = '#d32f2f';\n"
    '                            ctx.beginPath();\n'
    '                            ctx.arc(dx + dayW - 2.5, y + 3.2, 1.4,\n'
    '                                    0, Math.PI * 2);\n'
    '                            ctx.fill();\n'
    '                        }\n'
    '                        gridLine(dx, y, dayW, lay.rowH);\n',
    'paint-badges-remove')

rep(
    '                    y += lay.rowH;\n'
    '                }\n'
    '                y += lay.gapH;\n'
    '            }\n'
    '\n'
    '            // Task 439: мероприятия и коды — РЯДОМ: события —\n'
    '            // ЛЕВАЯ зона листа (x0..x0+evZoneW), коды — ПРАВАЯ\n'
    '            // (codeX..правый край), заголовки блоков на одной\n'
    '            // верхней линии\n'
    '            var codeW = lay.codeW || 235;\n'
    '            // Task 440: зазор мероприятий↔коды — 7.5pt (= 10px)\n'
    '            var colGap = lay.colGap || 7.5;\n'
    '            var evZoneW = CW - codeW - colGap;\n'
    '            // Task 440 (как в HTML flex 0 1 auto): блок кодов — за\n'
    '            // ФАКТИЧЕСКИМ правым краем строк мероприятий (+colGap),\n'
    '            // не прижат к правому краю листа; страницы без\n'
    '            // мероприятий — коды от левого края (+colGap);\n'
    '            // кодыX вычисляется ПОСЛЕ отрисовки мероприятий\n'
    '            // (evRightMax), ограничение — правый край листа\n'
    '            var codeX = x0 + colGap;\n'
    '            var evRightMax = 0;\n'
    '            var botY = y;\n',
    '                    y += lay.rowH;\n'
    '                }\n'
    '                // Task 442: ТОЛСТЫЙ внешний контур полос выходных —\n'
    '                // сверху ленты дней до низа последней строки\n'
    '                // (полоса = подряд идущие нерабочие дни, Сб+Вс —\n'
    '                // ОДИН контур; фоном выходные НЕ выделяются —\n'
    '                // заявка). Цвет — как у рамок HTML-печати\n'
    "                ctx.strokeStyle = '#8f99a3';\n"
    '                ctx.lineWidth = 1.4;\n'
    '                var runStart = -1;\n'
    '                for (var so = 0; so <= nDays; so++) {\n'
    '                    var offCol = so < nDays && model.days[so].off;\n'
    '                    if (offCol && runStart < 0) runStart = so;\n'
    '                    if (!offCol && runStart >= 0) {\n'
    '                        ctx.strokeRect(x0 + empW + runStart * dayW,\n'
    '                                       gridTop, (so - runStart) * dayW,\n'
    '                                       y - gridTop);\n'
    '                        runStart = -1;\n'
    '                    }\n'
    '                }\n'
    '                y += lay.gapH;\n'
    '            }\n'
    '\n'
    '            // Task 442: мероприятия — НА ВСЮ ширину листа (зоны\n'
    '            // кодов справа больше нет — столбец кодов удалён\n'
    '            // по заявке)\n',
    'paint-contour')

# ============================================================
# 9. _printPdfPaintPage: перенос текста мероприятий — до
#    правого края листа; evRightMax-трекинг снят
# ============================================================
rep(
    '                ctx.fillText(evHead, x0, y + 8);\n'
    '                evRightMax = Math.max(evRightMax,\n'
    '                    x0 + ctx.measureText(evHead).width);\n'
    '                y += lay.secH;\n',
    '                ctx.fillText(evHead, x0, y + 8);\n'
    '                y += lay.secH;\n',
    'paint-evhead')

rep(
    '                    var evLine = \'\', evLy = y + 7;\n'
    '                    var evMaxW = x0 + evZoneW - ex;\n'
    '                    for (var ewi = 0; ewi < evWords.length; ewi++) {\n'
    '                        var evCand = evLine\n'
    '                            ? evLine + \' \' + evWords[ewi] : evWords[ewi];\n'
    '                        if (ctx.measureText(evCand).width <= evMaxW ||\n'
    '                            !evLine) {\n'
    '                            evLine = evCand;\n'
    '                        } else {\n'
    '                            ctx.fillText(evLine, ex, evLy);\n'
    '                            evRightMax = Math.max(evRightMax,\n'
    '                                ex + ctx.measureText(evLine).width);\n'
    '                            evLy += lay.evRowH;\n'
    '                            evLine = evWords[ewi];\n'
    '                        }\n'
    '                    }\n'
    '                    if (evLine) {\n'
    '                        ctx.fillText(evLine, ex, evLy);\n'
    '                        evRightMax = Math.max(evRightMax,\n'
    '                            ex + ctx.measureText(evLine).width);\n'
    '                    }\n',
    '                    var evLine = \'\', evLy = y + 7;\n'
    '                    // Task 442: перенос — до ПРАВОГО края листа\n'
    '                    var evMaxW = x0 + CW - ex;\n'
    '                    for (var ewi = 0; ewi < evWords.length; ewi++) {\n'
    '                        var evCand = evLine\n'
    '                            ? evLine + \' \' + evWords[ewi] : evWords[ewi];\n'
    '                        if (ctx.measureText(evCand).width <= evMaxW ||\n'
    '                            !evLine) {\n'
    '                            evLine = evCand;\n'
    '                        } else {\n'
    '                            ctx.fillText(evLine, ex, evLy);\n'
    '                            evLy += lay.evRowH;\n'
    '                            evLine = evWords[ewi];\n'
    '                        }\n'
    '                    }\n'
    '                    if (evLine) {\n'
    '                        ctx.fillText(evLine, ex, evLy);\n'
    '                    }\n',
    'paint-evwrap')

# ============================================================
# 10. _printPdfPaintPage: блок кодов — отрисовка УДАЛЕНА
# ============================================================
rep(
    '            // коды — ПРАВАЯ зона, ОДНА колонка (Task 441: «коды\n'
    '            // сделай в один столбец»; прежде две — Task 434);\n'
    '            // общая верхняя линия с мероприятиями\n'
    '            if (page.codes) {\n'
    '                y = botY;\n'
    '                // Task 440: коды — за фактическим краем мероприятий\n'
    '                // (в пределах листа); лист пуст от мероприятий — от\n'
    '                // левого края (+colGap)\n'
    '                if (page.events && evRightMax > 0) {\n'
    '                    codeX = Math.min(evRightMax + colGap,\n'
    '                                     x0 + CW - codeW);\n'
    '                }\n'
    "                ctx.fillStyle = '#1b1f24';\n"
    "                ctx.font = '700 9px Arial';\n"
    "                ctx.fillText('Коды:', codeX, y + 8);\n"
    '                y += lay.secH;\n'
    '                // Task 441: ОДИН столбец — все коды друг под\n'
    '                // другом от codeX (прежде: две колонки со\n'
    '                // сдвигом colW2 и разбивкой perCol)\n'
    '                for (var lc = 0; lc < page.codes.length; lc++) {\n'
    '                    var lx = codeX;\n'
    '                    var ly = y + lc * lay.codeRowH;\n'
    '                    var code = page.codes[lc];\n'
    '                    if (code.color) {\n'
    '                        ctx.fillStyle = code.color;\n'
    '                        ctx.fillRect(lx, ly + 1, 4.5, 4.5);\n'
    '                    }\n'
    "                    ctx.fillStyle = '#1b1f24';\n"
    "                    ctx.font = '8px Arial';\n"
    '                    ctx.fillText(code.code\n'
    '                        ? (code.label\n'
    "                           ? code.code + ' — ' + code.label : code.code)\n"
    "                        : (code.label || ''),\n"
    '                        lx + 7, ly + 5.5);\n'
    '                }\n'
    '            }\n'
    '\n',
    '            // Task 442: блок кодов (правая зона, Tasks 434–441)\n'
    '            // УДАЛЁН по заявке — страница заканчивается списком\n'
    '            // мероприятий на всю ширину листа\n'
    '\n',
    'paint-codes-remove')

# ============================================================
io.open(P, 'w', encoding='utf-8').write(s)
print()
print('=== ИТОГ (патч 2: модель + PDF) ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ВСЕ ЗАМЕНЫ ПРИМЕНИЛИСЬ. Δдлина: %+d символов' % (len(s) - orig_len))
