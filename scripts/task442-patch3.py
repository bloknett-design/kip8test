#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442 (kip8test), патч 3 из 3: Excel — _wsTabelStyleMap (новый),
# _wsTabelStylesXml (medium-контуры, жирные числа выходных, без
# indent-стилей кодов), _wsTabelRows (без столбца кодов, контуры),
# _buildTabelWorkbook (цвета из ячеек, counts без codes); чистка:
# codeRowH/dyy в PDF-раскладке/художнике.
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


# ============================================================
# 0. Чистка PDF: codeRowH (раскладка) и dyy (художник) — сняты
# ============================================================
rep(
    "            var secH = opts.secH || 18;\n"
    "            var evRowH = opts.evRowH || 13;\n"
    "            var codeRowH = opts.codeRowH || 14;\n"
    "            var gapH = opts.gapH || 8;\n",
    "            var secH = opts.secH || 18;\n"
    "            var evRowH = opts.evRowH || 13;\n"
    "            var gapH = opts.gapH || 8;\n",
    'clean-codeRowH-var', 2)
rep(
    "                             evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,\n",
    "                             evRowH: evRowH, gapH: gapH,\n",
    'clean-codeRowH-ret', 1)
rep(
    "                     evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,\n",
    "                     evRowH: evRowH, gapH: gapH,\n",
    'clean-codeRowH-ret2', 1)
rep(
    '        // повторяется на каждой странице с таблицей); мероприятия\n'
    '        // — на последней странице под таблицей, если влезают,\n'
    '        // иначе отдельными страницами (события режутся по высоте).\n'
    '        // Task 442: зоны кодов справа больше нет (столбец кодов\n'
    '        // удалён по заявке) — мероприятия занимают всю ширину\n'
    '        // листа; codeRowH сохранён в раскладке для совместимости\n'
    '        // callers, в отрисовке не используется\n',
    '        // повторяется на каждой странице с таблицей); мероприятия\n'
    '        // — на последней странице под таблицей, если влезают,\n'
    '        // иначе отдельными страницами (события режутся по высоте).\n'
    '        // Task 442: зоны кодов справа больше нет (столбец кодов\n'
    '        // удалён по заявке) — мероприятия занимают всю ширину\n'
    '        // листа\n',
    'clean-codeRowH-doc')
rep(
    '                        var cell = row.cells[cc];\n'
    '                        var dx = x0 + empW + cc * dayW;\n'
    '                        var dyy = model.days[cc];\n'
    '                        // Task 442: серой заливки нерабочих дней\n'
    '                        // больше нет (только цвет статуса);\n'
    '                        // бейджи мероприятий удалены (ниже)\n'
    '                        if (cell.status && cell.color) {\n',
    '                        var cell = row.cells[cc];\n'
    '                        var dx = x0 + empW + cc * dayW;\n'
    '                        // Task 442: серой заливки нерабочих дней и\n'
    '                        // бейджей мероприятий больше нет — только\n'
    '                        // цвет статуса, пунктир плана отпуска,\n'
    '                        // код и точка переработки\n'
    '                        if (cell.status && cell.color) {\n',
    'clean-dyy')

# ============================================================
# 1. _wsTabelStyleMap — НОВЫЙ метод (единая карта стилей)
# ============================================================
rep(
    '        _wsTabelStylesXml: function(colors) {\n'
    '            colors = colors || [];\n'
    "            var f = '', fl = '', xf = '';\n",
    '        // Task 442: карта индексов стилей листа «Табель» — ЕДИНАЯ\n'
    '        // для _wsTabelStylesXml (порядок cellXfs) и _wsTabelRows\n'
    '        // (s-индексы ячеек). База 0–6 прежняя (0 default, 1 шапка\n'
    '        // bold/белая-по-синему, 2 заголовок листа, 3 подзаголовок,\n'
    '        // 4 ячейка сетки, 5 работник wrap, 6 день недели); далее\n'
    '        // ДИНАМИКА: цветные ячейки кодов (border thin, база 7),\n'
    '        // контуры полос выходных (medium-границы: шапка T/TL/TR/\n'
    '        // TLR — bold-число, дни недели L/R/LR, тело L/R/LR/B/BL/\n'
    '        // BR/BLR — обычные и ЦВЕТНЫЕ варианты), последняя — обычные\n'
    '        // (НЕ жирные) числа дат не-выходных\n'
    '        _wsTabelStyleMap: function(nColors) {\n'
    '            var coloredBase = 7;\n'
    '            var headC = coloredBase + nColors;\n'
    '            var dowsC = headC + 4;\n'
    '            var bodyC = dowsC + 3;\n'
    '            var colC = bodyC + 7;\n'
    '            var regDate = colC + 7 * nColors;\n'
    '            return { coloredBase: coloredBase, headC: headC,\n'
    '                     dowsC: dowsC, bodyC: bodyC, colC: colC,\n'
    '                     regDate: regDate };\n'
    '        },\n'
    '\n'
    '        _wsTabelStylesXml: function(colors) {\n'
    '            colors = colors || [];\n'
    '            var st = this._wsTabelStyleMap(colors.length);\n'
    "            var f = '', fl = '', xf = '', bd = '';\n",
    'stylemap-new')

# ============================================================
# 2. _wsTabelStylesXml: шрифт 6 (НЕ жирные белые числа дат)
# ============================================================
rep(
    "            f += '<font><b/><sz val=\"11\"/><color rgb=\"FF1B1F24\"/><name val=\"Arial\"/></font>';\n"
    '            fl += \'<fill><patternFill patternType="none"/></fill>\';\n',
    "            f += '<font><b/><sz val=\"11\"/><color rgb=\"FF1B1F24\"/><name val=\"Arial\"/></font>';\n"
    '            // Task 442: числа дат НЕ-выходных дней — НЕ жирные\n'
    '            // (выходные остаются bold — «даты выходных жирнее»)\n'
    "            f += '<font><sz val=\"11\"/><color rgb=\"FFFFFFFF\"/><name val=\"Arial\"/></font>';\n"
    '            fl += \'<fill><patternFill patternType="none"/></fill>\';\n',
    'styles-font6')

# ============================================================
# 3. _wsTabelStylesXml: границы — medium-комбинации контура
# ============================================================
rep(
    "            xf += '<xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/>';\n",
    '            // Task 442: границы — thin (сетка, как прежде) +\n'
    '            // MEDIUM-комбинации ВНЕШНЕГО КОНТУРА полос выходных\n'
    '            // (цвет 8F99A3 — как в HTML-печати). Порядок границ\n'
    '            // 2–12: T, TL, TR, TLR, L, R, LR, B, BL, BR, BLR —\n'
    '            // соответствует карте _wsTabelStyleMap (шапка —\n'
    '            // верх полосы, тело — бока и низ последней строки)\n'
    '            var TH = function(side) {\n'
    '                return \'<\' + side + \' style="thin">\' +\n'
    '                       \'<color rgb="FFB9C2CC"/></\' + side + \'>\';\n'
    '            };\n'
    '            var MED = function(side) {\n'
    '                return \'<\' + side + \' style="medium">\' +\n'
    '                       \'<color rgb="FF8F99A3"/></\' + side + \'>\';\n'
    '            };\n'
    '            var sideLine = function(sides, side) {\n'
    '                return sides.indexOf(side) !== -1\n'
    '                    ? MED(side) : TH(side);\n'
    '            };\n'
    '            var borderOf = function(sides) {\n'
    '                var out = \'<border>\';\n'
    "                out += sideLine(sides, 'left');\n"
    "                out += sideLine(sides, 'right');\n"
    "                out += sideLine(sides, 'top');\n"
    "                out += sideLine(sides, 'bottom');\n"
    '                return out + \'<diagonal/></border>\';\n'
    '            };\n'
    "            bd += '<border><left/><right/><top/><bottom/><diagonal/></border>';\n"
    "            bd += '<border>' +\n"
    "                  '<left style=\"thin\"><color rgb=\"FFB9C2CC\"/></left>' +\n"
    "                  '<right style=\"thin\"><color rgb=\"FFB9C2CC\"/></right>' +\n"
    "                  '<top style=\"thin\"><color rgb=\"FFB9C2CC\"/></top>' +\n"
    "                  '<bottom style=\"thin\"><color rgb=\"FFB9C2CC\"/></bottom>' +\n"
    "                  '<diagonal/></border>';\n"
    '            var CONTOURS = [\n'
    "                ['top'], ['top', 'left'], ['top', 'right'],\n"
    "                ['top', 'left', 'right'],\n"
    "                ['left'], ['right'], ['left', 'right'],\n"
    "                ['bottom'], ['bottom', 'left'], ['bottom', 'right'],\n"
    "                ['bottom', 'left', 'right']\n"
    '            ];\n'
    '            for (var bc = 0; bc < CONTOURS.length; bc++) {\n'
    '                bd += borderOf(CONTOURS[bc]);\n'
    '            }\n'
    "            xf += '<xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/>';\n",
    'styles-borders')

# ============================================================
# 4. _wsTabelStylesXml: стили — база, цветные, контуры, regDate
# ============================================================
OLD_STYLES = '''            xf += '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>';
            xf += '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>';
            xf += '<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>';
            xf += '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>';
            xf += '<xf numFmtId="0" fontId="5" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment wrapText="1" vertical="top"/></xf>';
            xf += '<xf numFmtId="0" fontId="4" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment horizontal="center"/></xf>';
            // Task 440 (заявка: «коды справа от мероприятий на
            // расстоянии друг от друга 10px»): Excel-эквивалент
            // зазора — ОТСТУП indent="1" (~7px = ширина символа
            // Arial 11) у ячеек КОДОВ в колонке D: текст мероприятий
            // (A/B) переполнением через пустую C обрезается у левой
            // кромки D, а текст кодов начинается на ~7px ПРАВЕЕ
            // кромки — видимый зазор между блоками (10px точно
            // недостижимы: колонка-разделитель C общая с сеткой дней
            // табеля, сузить её нельзя). Стиль 7 — строка кода,
            // стиль 8 — заголовок «Коды:» (шапка как s=1 + отступ)
            xf += '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">' +
                  '<alignment horizontal="left" indent="1"/></xf>';
            xf += '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1">' +
                  '<alignment horizontal="left" indent="1"/></xf>';
            for (var k = 0; k < colors.length; k++) {
                xf += '<xf numFmtId="0" fontId="0" fillId="' + (3 + k) +
                      '" borderId="1" xfId="0" applyFill="1" ' +
                      'applyBorder="1" applyAlignment="1">' +
                      '<alignment horizontal="center"/></xf>';
            }
            return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
                '<fonts count="' + 6 + '">' + f + '</fonts>' +
                '<fills count="' + (3 + colors.length) + '">' + fl + '</fills>' +
                '<borders count="2">' +
                '<border><left/><right/><top/><bottom/><diagonal/></border>' +
                '<border>' +
                '<left style="thin"><color rgb="FFB9C2CC"/></left>' +
                '<right style="thin"><color rgb="FFB9C2CC"/></right>' +
                '<top style="thin"><color rgb="FFB9C2CC"/></top>' +
                '<bottom style="thin"><color rgb="FFB9C2CC"/></bottom>' +
                '<diagonal/></border></borders>' +
                '<cellStyleXfs count="1">' +
                '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>' +
                '</cellStyleXfs>' +
                '<cellXfs count="' + (9 + colors.length) + '">' + xf +
                '</cellXfs>' +
                '<cellStyles count="1">' +
                '<cellStyle name="Normal" xfId="0" builtinId="0"/>' +
                '</cellStyles></styleSheet>';
        },
'''

NEW_STYLES = '''            xf += '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>';
            xf += '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>';
            xf += '<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>';
            xf += '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>';
            xf += '<xf numFmtId="0" fontId="5" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment wrapText="1" vertical="top"/></xf>';
            xf += '<xf numFmtId="0" fontId="4" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment horizontal="center"/></xf>';
            // Task 442: indent-стили кодов (7/8 из Task 440)
            // УДАЛЕНЫ вместе со столбцом кодов; база цветных — 7
            for (var k = 0; k < colors.length; k++) {
                xf += '<xf numFmtId="0" fontId="0" fillId="' + (3 + k) +
                      '" borderId="1" xfId="0" applyFill="1" ' +
                      'applyBorder="1" applyAlignment="1">' +
                      '<alignment horizontal="center"/></xf>';
            }
            // Task 442: контуры полос выходных — ШАПКА (bold-число
            // на синей заливке, medium-верх + края): T, TL, TR, TLR
            for (var hc = 0; hc < 4; hc++) {
                xf += '<xf numFmtId="0" fontId="1" fillId="2" borderId="' +
                      (2 + hc) + '" xfId="0" applyFont="1" applyFill="1" ' +
                      'applyBorder="1" applyAlignment="1">' +
                      '<alignment horizontal="center"/></xf>';
            }
            // Task 442: контуры полос выходных — ДНИ НЕДЕЛИ (серый
            // мелкий, medium-края): L, R, LR
            for (var dc = 0; dc < 3; dc++) {
                xf += '<xf numFmtId="0" fontId="4" fillId="0" borderId="' +
                      (6 + dc) + '" xfId="0" applyFont="1" ' +
                      'applyBorder="1" applyAlignment="1">' +
                      '<alignment horizontal="center"/></xf>';
            }
            // Task 442: контуры полос выходных — ТЕЛО, обычные
            // ячейки (центр, без заливки): L, R, LR, B, BL, BR, BLR
            for (var bcf = 0; bcf < 7; bcf++) {
                xf += '<xf numFmtId="0" fontId="0" fillId="0" borderId="' +
                      (6 + bcf) + '" xfId="0" applyBorder="1" ' +
                      'applyAlignment="1">' +
                      '<alignment horizontal="center"/></xf>';
            }
            // Task 442: контуры полос выходных — ТЕЛО, ЦВЕТНЫЕ
            // ячейки статусов (заливка цвета кода + medium-бока):
            // 7 вариантов на каждый цвет
            for (var k2 = 0; k2 < colors.length; k2++) {
                for (var bcc = 0; bcc < 7; bcc++) {
                    xf += '<xf numFmtId="0" fontId="0" fillId="' +
                          (3 + k2) + '" borderId="' + (6 + bcc) +
                          '" xfId="0" applyFill="1" applyBorder="1" ' +
                          'applyAlignment="1">' +
                          '<alignment horizontal="center"/></xf>';
                }
            }
            // Task 442: обычные (НЕ выходные) числа дат — НЕ
            // жирные (fontId 6), та же синяя шапка и thin-рамка
            xf += '<xf numFmtId="0" fontId="6" fillId="2" borderId="1" ' +
                  'xfId="0" applyFont="1" applyFill="1" applyBorder="1" ' +
                  'applyAlignment="1"><alignment horizontal="center"/></xf>';
            return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
                '<fonts count="' + 7 + '">' + f + '</fonts>' +
                '<fills count="' + (3 + colors.length) + '">' + fl + '</fills>' +
                '<borders count="13">' + bd + '</borders>' +
                '<cellStyleXfs count="1">' +
                '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>' +
                '</cellStyleXfs>' +
                '<cellXfs count="' + (st.regDate + 1) + '">' + xf +
                '</cellXfs>' +
                '<cellStyles count="1">' +
                '<cellStyle name="Normal" xfId="0" builtinId="0"/>' +
                '</cellStyles></styleSheet>';
        },
'''
rep(OLD_STYLES, NEW_STYLES, 'styles-body')

# ============================================================
# 5. _wsTabelRows: докстринг
# ============================================================
rep(
    '        // Task 438: строки листа «Табель» для Excel (чистая, для\n'
    '        // VM-тестов): шапка из двух строк (Task 438), сетка\n'
    '        // Работник/дни/Дни/Перераб. (без «Часов», переработка —\n'
    '        // только дни), цветные ячейки кодов; Task 439: работник —\n'
    '        // ФИО + Тип (второй строкой), мероприятия и коды — РЯДОМ\n'
    '        // (даты/текст в A/B, коды — в колонке D справа)\n',
    '        // Task 438: строки листа «Табель» для Excel (чистая, для\n'
    '        // VM-тестов): шапка из двух строк (Task 438), сетка\n'
    '        // Работник/дни/Дни/Перераб. (без «Часов», переработка —\n'
    '        // только дни), цветные ячейки кодов; Task 439: работник —\n'
    '        // ФИО + Тип (второй строкой). Task 442: столбец кодов\n'
    '        // УДАЛЁН — под сеткой только мероприятия (дата в A, текст\n'
    '        // в B); числа выходных — ЖИРНЫЕ (обычные дни — НЕ жирные,\n'
    '        // новый стиль), полосы выходных — MEDIUM-внешний контур\n'
    '        // (верх — строка чисел, бока — края полосы, низ —\n'
    '        // последняя строка сетки; края полосы — по соседям,\n'
    '        // Сб+Вс подряд — один контур)\n',
    'tabelrows-doc')

# ============================================================
# 6. _wsTabelRows: шапка дней — жирные выходные + контуры
# ============================================================
rep(
    '            var rows = [];\n'
    "            rows.push([{ v: 'График работы', s: 2 }]);\n"
    "            rows.push([{ v: monthsNom[model.month - 1] + ' ' + model.year +\n"
    "                         ' г. · вид табеля: ' +\n"
    "                         (viewLabels[model.view] || 'полный'), s: 3 }]);\n"
    '            rows.push([]);\n'
    "            var head = [{ v: 'Работник', s: 1 }];\n"
    "            var dows = [{ v: '', s: 6 }];\n"
    '            for (var d = 0; d < model.days.length; d++) {\n'
    "                head.push({ v: String(model.days[d].d) +\n"
    "                            (model.days[d].short ? '*' : ''), s: 1 });\n"
    "                dows.push({ v: model.days[d].dow, s: 6 });\n"
    '            }\n'
    "            head.push({ v: 'Дни', s: 1 });\n"
    "            head.push({ v: 'Перераб.', s: 1 });\n"
    "            dows.push({ v: '', s: 6 });\n"
    "            dows.push({ v: '', s: 6 });\n"
    '            rows.push(head);\n'
    '            rows.push(dows);\n',
    '            var rows = [];\n'
    '            // Task 442: карта стилей (индексы контуров/regDate)\n'
    '            var nCol = 0;\n'
    '            for (var ck in colorIdx) {\n'
    '                if (Object.prototype.hasOwnProperty.call(colorIdx, ck)) {\n'
    '                    nCol++;\n'
    '                }\n'
    '            }\n'
    '            var stMap = this._wsTabelStyleMap(nCol);\n'
    "            rows.push([{ v: 'График работы', s: 2 }]);\n"
    "            rows.push([{ v: monthsNom[model.month - 1] + ' ' + model.year +\n"
    "                         ' г. · вид табеля: ' +\n"
    "                         (viewLabels[model.view] || 'полный'), s: 3 }]);\n"
    '            rows.push([]);\n'
    "            var head = [{ v: 'Работник', s: 1 }];\n"
    "            var dows = [{ v: '', s: 6 }];\n"
    '            var nDays = model.days.length;\n'
    '            // Task 442: флаги нерабочих дней + края полос — по\n'
    '            // соседям (непрерывная Сб+Вс полоса — один контур)\n'
    '            var offArr = [];\n'
    '            for (var d0 = 0; d0 < nDays; d0++) {\n'
    '                offArr[d0] = !!model.days[d0].off;\n'
    '            }\n'
    '            for (var d = 0; d < nDays; d++) {\n'
    '                var off = offArr[d];\n'
    '                var edge = off\n'
    '                    ? ((d === 0 || !offArr[d - 1]) ? 1 : 0) +\n'
    '                      ((d === nDays - 1 || !offArr[d + 1]) ? 2 : 0)\n'
    '                    : 0;\n'
    '                // Task 442: число ВЫХОДНОГО дня — ЖИРНОЕ (s=1,\n'
    '                // как прежде у всех) + medium-верх контура\n'
    '                // (headC: T/TL/TR/TLR); обычный день — НЕ жирное\n'
    '                // число (новый стиль regDate)\n'
    "                head.push({ v: String(model.days[d].d) +\n"
    "                            (model.days[d].short ? '*' : ''),\n"
    '                            s: off ? stMap.headC + edge\n'
    '                                   : stMap.regDate });\n'
    '                // день недели в полосе выходного — medium-бока\n'
    '                // (dowsC: L/R/LR; прочие — прежний s=6)\n'
    "                dows.push({ v: model.days[d].dow,\n"
    '                            s: off && edge\n'
    '                                ? stMap.dowsC + edge - 1 : 6 });\n'
    '            }\n'
    "            head.push({ v: 'Дни', s: 1 });\n"
    "            head.push({ v: 'Перераб.', s: 1 });\n"
    "            dows.push({ v: '', s: 6 });\n"
    "            dows.push({ v: '', s: 6 });\n"
    '            rows.push(head);\n'
    '            rows.push(dows);\n',
    'tabelrows-head')

# ============================================================
# 7. _wsTabelRows: тело — контуры полос выходных
# ============================================================
rep(
    '            for (var r = 0; r < model.rows.length; r++) {\n'
    '                var row = model.rows[r];\n'
    '                // Task 439: работник — ФИО + Тип (перенос строки в\n'
    '                // ячейке, стиль 5 с wrapText)\n'
    '                var line = [{ v: row.fio +\n'
    "                              (row.tip ? '\\n' + row.tip : ''), s: 5 }];\n"
    '                for (var c = 0; c < row.cells.length; c++) {\n'
    '                    var cell = row.cells[c];\n'
    '                    var st = 4;\n'
    '                    if (cell.status && cell.color) {\n'
    "                        var col = String(cell.color).replace('#', '')\n"
    '                                    .toUpperCase();\n'
    '                        // Task 440: база цветных стилей 9 (7/8 —\n'
    '                        // коды с indent)\n'
    '                        if (colorIdx[col] !== undefined) {\n'
    '                            st = 9 + colorIdx[col];\n'
    '                        }\n'
    '                    }\n'
    "                    line.push({ v: cell.status || '', s: st });\n"
    '                }\n',
    '            for (var r = 0; r < model.rows.length; r++) {\n'
    '                var row = model.rows[r];\n'
    '                // Task 442: последняя строка сетки — низ контура\n'
    '                var isLast = (r === model.rows.length - 1);\n'
    '                // Task 439: работник — ФИО + Тип (перенос строки в\n'
    '                // ячейке, стиль 5 с wrapText)\n'
    '                var line = [{ v: row.fio +\n'
    "                              (row.tip ? '\\n' + row.tip : ''), s: 5 }];\n"
    '                for (var c = 0; c < row.cells.length; c++) {\n'
    '                    var cell = row.cells[c];\n'
    '                    var st = 4;\n'
    '                    var col = cell.color\n'
    "                        ? String(cell.color).replace('#', '').toUpperCase()\n"
    "                        : '';\n"
    '                    if (cell.status && col && colorIdx[col] !== undefined) {\n'
    '                        // Task 442: база цветных стилей — 7\n'
    '                        // (indent-стили кодов 7/8 из Task 440\n'
    '                        // удалены вместе со столбцом кодов)\n'
    '                        st = stMap.coloredBase + colorIdx[col];\n'
    '                    }\n'
    '                    // Task 442: ячейка в полосе выходного —\n'
    '                    // MEDIUM-контур (бока/низ): combo 1=L, 2=R,\n'
    '                    // 3=LR, 4=B, 5=BL, 6=BR, 7=BLR (0 — внутри\n'
    '                    // полосы, thin); у цветной ячейки — цветной\n'
    '                    // вариант контура (colC), у пустой — bodyC\n'
    '                    if (c < nDays && offArr[c]) {\n'
    '                        var cEdge = ((c === 0 || !offArr[c - 1]) ? 1 : 0) +\n'
    '                                    ((c === nDays - 1 || !offArr[c + 1])\n'
    '                                        ? 2 : 0);\n'
    '                        var combo = cEdge + (isLast ? 4 : 0);\n'
    '                        if (combo) {\n'
    '                            st = (cell.status && col &&\n'
    '                                  colorIdx[col] !== undefined)\n'
    '                                ? stMap.colC + colorIdx[col] * 7 + (combo - 1)\n'
    '                                : stMap.bodyC + (combo - 1);\n'
    '                        }\n'
    '                    }\n'
    "                    line.push({ v: cell.status || '', s: st });\n"
    '                }\n',
    'tabelrows-body')

# ============================================================
# 8. _wsTabelRows: нижняя секция — только мероприятия
# ============================================================
rep(
    '            // Task 439 (заявка: «блок с кодами размести справа от\n'
    '            // мероприятий»): секции — РЯДОМ: мероприятия в колонках\n'
    '            // A (дата) + B (текст), коды — в колонке D (C — зазор),\n'
    '            // заголовки «Мероприятия · …» и «Коды:» на одной строке;\n'
    '            // пустой месяц — заглушка в A (как в печати).\n'
    '            // Task 441 (заявка: «коды сделай в один столбец»):\n'
    '            // коды — ОДИН столбец D (строка на код; двух\n'
    '            // колонок в Excel и не было — семантика сохранена)\n'
    '            rows.push([]);\n'
    '            var evRowsOut = [];\n'
    '            if (model.events.length) {\n'
    '                for (var e2 = 0; e2 < model.events.length; e2++) {\n'
    '                    evRowsOut.push({ a: model.events[e2].range,\n'
    '                                     b: model.events[e2].text, as: 5, bs: 0 });\n'
    '                }\n'
    '            } else {\n'
    "                evRowsOut.push({ a: 'нет мероприятий в этом месяце',\n"
    '                                 b: \'\', as: 0, bs: 0 });\n'
    '            }\n'
    '            var codeLines = [];\n'
    '            for (var k = 0; k < model.codes.length; k++) {\n'
    '                var cd = model.codes[k];\n'
    '                codeLines.push(cd.code\n'
    "                    ? (cd.label ? cd.code + ' — ' + cd.label : cd.code)\n"
    "                    : (cd.label || ''));\n"
    '            }\n'
    '            var botRows = Math.max(evRowsOut.length, codeLines.length, 1);\n'
    "            rows.push([{ v: 'Мероприятия · ' +\n"
    "                         monthsNom[model.month - 1] + ' ' + model.year +\n"
    "                         (model.events.length\n"
    "                             ? ' · ' + model.events.length : ''), s: 1 },\n"
    "                       null, null, { v: 'Коды:', s: 8 }]);\n"
    '            for (var b = 0; b < botRows; b++) {\n'
    '                var bev = evRowsOut[b];\n'
    '                rows.push([bev ? { v: bev.a || \'\', s: bev.as } : null,\n'
    '                           bev && bev.b ? { v: bev.b, s: bev.bs } : null,\n'
    '                           null,\n'
    '                           codeLines[b] !== undefined\n'
    '                               ? { v: codeLines[b], s: 7 } : null]);\n'
    '            }\n'
    '            return rows;\n'
    '        },\n',
    '            // Task 442: столбец кодов D и заголовок «Коды:»\n'
    '            // УДАЛЕНЫ (заявка) — под сеткой только список\n'
    '            // мероприятий: дата в A, текст в B (Task 439);\n'
    '            // пустой месяц — заглушка в A (как в печати)\n'
    '            rows.push([]);\n'
    "            rows.push([{ v: 'Мероприятия · ' +\n"
    "                         monthsNom[model.month - 1] + ' ' + model.year +\n"
    "                         (model.events.length\n"
    "                             ? ' · ' + model.events.length : ''), s: 1 }]);\n"
    '            if (model.events.length) {\n'
    '                for (var e2 = 0; e2 < model.events.length; e2++) {\n'
    "                    rows.push([{ v: model.events[e2].range, s: 5 },\n"
    "                               { v: model.events[e2].text, s: 0 }]);\n"
    '                }\n'
    '            } else {\n'
    "                rows.push([{ v: 'нет мероприятий в этом месяце', s: 0 }]);\n"
    '            }\n'
    '            return rows;\n'
    '        },\n',
    'tabelrows-bottom')

# ============================================================
# 9. _buildTabelWorkbook: цвета — только из ячеек; counts без codes
# ============================================================
rep(
    '        // Task 438: КНИГА .xlsx «Табель» (чистая — те же помощники\n'
    '        // Task 430: _wsXlsZip/_wsXlsBytes; имя — «График_работы_\n'
    '        // ‹Месяц›_‹год›.xlsx»); цвета кодов → динамические стили\n'
    '        _buildTabelWorkbook: function(viewEmps, agg) {\n'
    '            var model = this._printModel(viewEmps, agg);\n'
    '            var colors = [];\n'
    '            var colorIdx = {};\n'
    '            for (var c = 0; c < model.codes.length; c++) {\n'
    '                var col = String(model.codes[c].color || \'\')\n'
    "                    .replace('#', '').toUpperCase();\n"
    '                if (!col || colorIdx[col] !== undefined) continue;\n'
    '                colorIdx[col] = colors.length;\n'
    '                colors.push(col);\n'
    '            }\n'
    '            // ячейки сетки могут нести цвет кода, которого нет в\n'
    '            // легенде (легаси без цвета — пустой, не бывает), но на\n'
    '            // всякий случай индексируем и их\n'
    '            for (var r = 0; r < model.rows.length; r++) {\n'
    '                var cells = model.rows[r].cells;\n'
    '                for (var k = 0; k < cells.length; k++) {\n'
    '                    var cc = String(cells[k].color || \'\')\n'
    "                        .replace('#', '').toUpperCase();\n"
    '                    if (!cc || colorIdx[cc] !== undefined) continue;\n'
    '                    colorIdx[cc] = colors.length;\n'
    '                    colors.push(cc);\n'
    '                }\n'
    '            }\n',
    '        // Task 438: КНИГА .xlsx «Табель» (чистая — те же помощники\n'
    '        // Task 430: _wsXlsZip/_wsXlsBytes; имя — «График_работы_\n'
    '        // ‹Месяц›_‹год›.xlsx»); цвета кодов → динамические стили.\n'
    '        // Task 442: перечень кодов из модели удалён — цвета\n'
    '        // собираются ТОЛЬКО из ячеек сетки (цвета статусов месяца)\n'
    '        _buildTabelWorkbook: function(viewEmps, agg) {\n'
    '            var model = this._printModel(viewEmps, agg);\n'
    '            var colors = [];\n'
    '            var colorIdx = {};\n'
    '            for (var r = 0; r < model.rows.length; r++) {\n'
    '                var cells = model.rows[r].cells;\n'
    '                for (var k = 0; k < cells.length; k++) {\n'
    '                    var cc = String(cells[k].color || \'\')\n'
    "                        .replace('#', '').toUpperCase();\n"
    '                    if (!cc || colorIdx[cc] !== undefined) continue;\n'
    '                    colorIdx[cc] = colors.length;\n'
    '                    colors.push(cc);\n'
    '                }\n'
    '            }\n',
    'workbook-colors')

rep(
    '                counts: {\n'
    '                    rows: model.rows.length,\n'
    '                    events: model.events.length,\n'
    '                    codes: model.codes.length,\n'
    '                    colors: colors.length\n'
    '                }\n',
    '                // Task 442: counts.codes удалён вместе со столбцом\n'
    '                counts: {\n'
    '                    rows: model.rows.length,\n'
    '                    events: model.events.length,\n'
    '                    colors: colors.length\n'
    '                }\n',
    'workbook-counts')

# ============================================================
io.open(P, 'w', encoding='utf-8').write(s)
print()
print('=== ИТОГ (патч 3: Excel + чистка) ===')
if fail:
    print('ПРОВАЛЕНО %d:' % len(fail))
    for m in fail:
        print('  - %s' % m)
    raise SystemExit(1)
print('ВСЕ ЗАМЕНЫ ПРИМЕНИЛИСЬ. Δдлина: %+d символов' % (len(s) - orig_len))
