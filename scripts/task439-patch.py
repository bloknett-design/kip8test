#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 439: заявка пользователя (3 части):
#   1) «В печатном графике блок с кодами размести справа от
#      мероприятий» — нижняя секция печати (HTML/PDF/Excel):
#      мероприятия слева, коды справа (общая верхняя линия);
#   2) «в колонке с работниками оставь только ФИО и Тип и сузь
#      этот столбец по размеру самого большого текста в его
#      ячейках» — печать: под ФИО — Тип (_empTipLine, «смена №1»/
#      «сменный»/«дневной»), должность убрана; ширина колонки —
#      по самому большому тексту (ФИО/Тип/заголовок «Работник»),
#      кламп 12–48mm (PDF 46–150pt, Excel — по длине текста);
#      _posLabel УДАЛЁН (потребителей не осталось);
#   3) «В мобильной версии … убери лишний код "Выходной, плановый
#      выходной день" который старый со знаком "." при выборе в
#      ячейках шахматки» — _normalizeStatusCodes не пускает
#      «точечные» легаси-коды («.», «·») в хвост списка (слот
#      «Выходной» с пустым кодом есть всегда), _renderCellPopup
#      не показывает строку «.», если есть канонический слот «».
import io, sys

path = 'index.html'
src = io.open(path, encoding='utf-8').read()
orig = src
n = [0]

def rep(old, new, what, count=1):
    global src
    found = src.count(old)
    assert found == count, '%s: найдено %d вхождений (ожидалось %d)' % (what, found, count)
    src = src.replace(old, new)
    n[0] += 1
    print('  OK: %s' % what)

# ============================================================
# 1. ПЕЧАТЬ HTML — колонка работников: ФИО + Тип, ширина по тексту
# ============================================================

# 1a. измерение ширины: Тип вместо должности + заголовок «Работник»
rep("""            var maxTxtPx = 0;
            for (var wi = 0; wi < viewEmps.length; wi++) {
                maxTxtPx = Math.max(maxTxtPx,
                    measureTxt(viewEmps[wi]['ФИО'],
                               '700 ' + fioPx + 'px Arial', fioPx),
                    measureTxt(self._posLabel(viewEmps[wi]),
                               posPx + 'px Arial', posPx));
            }
            // px→mm (96dpi) + 3.5mm паддинги/запас; шаг 0.5mm вверх
            var empWmm = Math.ceil(((maxTxtPx * 25.4 / 96) + 3.5) * 2) / 2;
            if (empWmm < 24) empWmm = 24;
            if (empWmm > 48) empWmm = 48;""",
"""            var maxTxtPx = 0;
            for (var wi = 0; wi < viewEmps.length; wi++) {
                maxTxtPx = Math.max(maxTxtPx,
                    measureTxt(viewEmps[wi]['ФИО'],
                               '700 ' + fioPx + 'px Arial', fioPx),
                    measureTxt(self._empTipLine(viewEmps[wi]),
                               posPx + 'px Arial', posPx));
            }
            // Task 439 (заявка: «в колонке с работниками оставь
            // только ФИО и Тип и сузь этот столбец по размеру
            // самого большого текста в его ячейках»): меряются
            // ФИО, Тип и заголовок «Работник»; кламп 12–48mm
            // (мин снижен с 24mm — Тип короче должности)
            maxTxtPx = Math.max(maxTxtPx,
                measureTxt('Работник', '700 11px Arial', 11));
            // px→mm (96dpi) + 3.5mm паддинги/запас; шаг 0.5mm вверх
            var empWmm = Math.ceil(((maxTxtPx * 25.4 / 96) + 3.5) * 2) / 2;
            if (empWmm < 12) empWmm = 12;
            if (empWmm > 48) empWmm = 48;""",
    '1a. _buildPrintHtml: измерение ФИО+Тип+заголовок, кламп 12–48')

# 1b. комментарий над измерением (Task 361 → дополнение Task 439)
rep("""            // Task 361 (заявка: «в печати столбец с сотрудниками
            // сделай уже, по ширине текста в нём, а в общем размер
            // таблицы увеличь»): ширина колонки «Сотрудник» — по
            // САМОМУ ДЛИННОМУ тексту печатаемых строк (ФИО 10.5px
            // bold / должность 8.5px), а НЕ фиксированные 50mm.""",
"""            // Task 361 (заявка: «в печати столбец с сотрудниками
            // сделай уже, по ширине текста в нём, а в общем размер
            // таблицы увеличь»): ширина колонки «Сотрудник» — по
            // САМОМУ ДЛИННОМУ тексту печатаемых строк (Task 439:
            // ФИО 10.5px bold / Тип 8.5px / заголовок «Работник»),
            // а НЕ фиксированные 50mm.""",
    '1b. комментарий измерения (Task 439)')

# 1c. строка работника: Тип вместо должности
rep("""                var emp = viewEmps[ei];
                var posLabel = this._posLabel(emp);
                html += '<tr><td class="wsp-emp"><span class="wsp-fio">' +
                        this._esc(emp['ФИО']) + '</span>' +
                        (posLabel ? '<span class="wsp-pos">' + this._esc(posLabel) + '</span>' : '') +
                        '</td>';""",
"""                var emp = viewEmps[ei];
                // Task 439: под ФИО — только Тип (_empTipLine:
                // «смена №1»/«сменный»/«дневной»), должность из
                // печатной колонки убрана (заявка «оставь только
                // ФИО и Тип»)
                var tipLabel = this._empTipLine(emp);
                html += '<tr><td class="wsp-emp"><span class="wsp-fio">' +
                        this._esc(emp['ФИО']) + '</span>' +
                        (tipLabel ? '<span class="wsp-pos">' + this._esc(tipLabel) + '</span>' : '') +
                        '</td>';""",
    '1c. строка работника: wsp-pos = Тип (_empTipLine)')

# ============================================================
# 2. ПЕЧАТЬ CSS — коды СПРАВА от мероприятий (flex-ряд)
# ============================================================

rep("""        #wsPrintSheet .wsp-bottom {
            margin-top: 2.5mm;
        }
        #wsPrintSheet .wsp-mev {
            margin-top: 0;
            font-size: 11px;
            line-height: 1.6;
        }""",
"""        #wsPrintSheet .wsp-bottom {
            margin-top: 2.5mm;
            /* Task 439 (заявка: «блок с кодами размести справа от
               мероприятий»): нижняя секция — ГИБКИЙ РЯД: список
               мероприятий слева (растягивается на остаток), блок
               кодов — справа фиксированной ширины, зазор 6mm */
            display: flex;
            align-items: flex-start;
            gap: 6mm;
        }
        #wsPrintSheet .wsp-mev {
            margin-top: 0;
            font-size: 11px;
            line-height: 1.6;
            /* Task 439: мероприятия — ЛЕВАЯ часть ряда */
            flex: 1 1 auto;
            min-width: 0;
        }""",
    '2a. CSS .wsp-bottom — flex-ряд, .wsp-mev — flex:1 1 auto')

rep("""        #wsPrintSheet .wsp-legend {
            margin-top: 2.5mm;
            font-size: 11px;
            line-height: 1.6;
        }""",
"""        #wsPrintSheet .wsp-legend {
            margin-top: 0;
            font-size: 11px;
            line-height: 1.6;
            /* Task 439: коды — ПРАВАЯ часть ряда (СПРАВА от
               мероприятий), фиксированная ширина блока */
            flex: 0 0 92mm;
            min-width: 0;
        }""",
    '2b. CSS .wsp-legend — flex:0 0 92mm, margin-top 0')

# 2c. CSS-комментарий .wsp-emp (кламп 24→12, ФИО/Тип)
rep("""               _buildPrintHtml (по самой длинной ФИО/должности,
               canvas measureText, кламп 24–48mm); 34mm —
               CSS-фолбэк, если JS ширину не задал. Освободившаяся
               ширина достаётся колонкам дней */""",
"""               _buildPrintHtml (Task 439: по самой длинной
               ФИО/Типу/заголовку «Работник», canvas measureText,
               кламп 12–48mm); 34mm —
               CSS-фолбэк, если JS ширину не задал. Освободившаяся
               ширина достаётся колонкам дней */""",
    '2c. CSS-комментарий .wsp-emp (Task 439)')

# 2d. CSS-комментарий .wsp-pos (должность → Тип)
rep("""        /* Task 361: ФИО 9→10.5px, должность 7.5→8.5px — крупнее;
           ширина колонки подстраивается по тексту (см. wsp-emp) */""",
"""        /* Task 361: ФИО 9→10.5px, подпись 7.5→8.5px — крупнее.
           Task 439: подпись — ТИП работника (смена №N/сменный/
           дневной, _empTipLine), должность убрана из колонки;
           ширина колонки подстраивается по тексту (см. wsp-emp) */""",
    '2d. CSS-комментарий .wsp-pos (Task 439)')

# 2e. многослойный CSS-комментарий секции (дополнение Task 439)
rep("""           Task 433 (заявка: «расположение кодов в печати верни
           обратно, я имел в виду, что бы правая часть блока
           растянулась вправо до конца листа, и если текст не
           будет вмещаться в одну строку, тогда переносить его на
           следующую строку»): флоат Task 432 и flex-ряд
           Task 364–431 СНЯТЫ — нижняя секция снова ВЕРТИКАЛЬНАЯ
           (как до Task 364): (1) СПИСОК МЕРОПРИЯТИЙ — КАЖДАЯ""",
"""           Task 433 (заявка: «расположение кодов в печати верни
           обратно…»): флоат Task 432 и flex-ряд Task 364–431
           СНЯТЫ — нижняя секция снова ВЕРТИКАЛЬНАЯ
           (как до Task 364). Task 439 (заявка: «блок с кодами
           размести справа от мероприятий»): секция СНОВА РЯД —
           мероприятия слева, коды справа (92mm): (1) СПИСОК
           МЕРОПРИЯТИЙ — КАЖДАЯ""",
    '2e. слоистый CSS-комментарий wsp-bottom (Task 439)')

# 2f. комментарий у построения wsp-bottom в _buildPrintHtml
rep("""            // Task 364: обёртка wsp-bottom — мероприятия и коды
            // под таблицей, сноска wsp-foot — ниже на всю ширину
            // листа.""",
"""            // Task 364: обёртка wsp-bottom — мероприятия и коды
            // под таблицей. Task 439: внутри обёртки — РЯД:
            // мероприятия слева, коды СПРАВА от них (CSS flex).""",
    '2f. комментарий DOM wsp-bottom (Task 439)')

# ============================================================
# 3. _printModel: строка несёт tip (Тип), не pos (должность)
# ============================================================
rep("""                rows.push({
                    fio: String(emp['ФИО'] || ''),
                    pos: String(this._posLabel(emp) || ''),
                    tab: String(emp['таб_номер'] || ''),""",
"""                rows.push({
                    fio: String(emp['ФИО'] || ''),
                    // Task 439: Тип работника (_empTipLine) —
                    // должность из печатной колонки убрана
                    tip: String(this._empTipLine(emp) || ''),
                    tab: String(emp['таб_номер'] || ''),""",
    '3. _printModel: rows[].tip = _empTipLine (pos убран)')

# ============================================================
# 4. _printPdfLayout: коды СПРАВА от мероприятий
# ============================================================
rep("""        // Страницы: [шапка (только первая) +] лента дней + строки
        // сотрудников (граница — только по строкам, лента
        // повторяется на каждой странице с таблицей); мероприятия
        // и коды — на последней странице под таблицей, если
        // влезают, иначе отдельными страницами (события режутся
        // по высоте, коды — всегда одной страницей)""",
"""        // Страницы: [шапка (только первая) +] лента дней + строки
        // сотрудников (граница — только по строкам, лента
        // повторяется на каждой странице с таблицей); мероприятия
        // и коды — РЯДОМ ДРУГ С ДРУГОМ (Task 439: события слева,
        // коды справа, общая верхняя линия) на последней странице
        // под таблицей, если влезают, иначе отдельными страницами
        // (события режутся по высоте, коды — всегда одной
        // страницей)""",
    '4a. комментарий _printPdfLayout (Task 439)')

rep("""            var gapH = opts.gapH || 8;
            var contentH = H - 2 * M;
            var evList = (model.events || []).length
                ? model.events : [{ placeholder: true }];
            var codeRows = Math.max(1,
                Math.ceil((model.codes || []).length / 2));
            var evH = secH + evList.length * evRowH + gapH;
            var cdH = secH + codeRows * codeRowH;""",
"""            var gapH = opts.gapH || 8;
            // Task 439: коды — СПРАВА от мероприятий: ширина
            // правой зоны кодов и зазор между блоками
            var codeW = opts.codeW || 235;
            var colGap = opts.colGap || 12;
            var contentH = H - 2 * M;
            var evList = (model.events || []).length
                ? model.events : [{ placeholder: true }];
            var codeRows = Math.max(1,
                Math.ceil((model.codes || []).length / 2));
            // оценка числа строк записи мероприятия (тексты
            // краткие — обычно 1 строка; оценка консервативная
            // ~4.6pt/символ, реальная укладка по словам — в
            // отрисовке _printPdfPaintPage)
            var evW = W - 2 * M - codeW - colGap;
            var evLinesOf = function(ev) {
                var est = (ev.range ? String(ev.range).length * 5.2 : 0) +
                          (ev.text ? String(ev.text).length * 4.6 : 0) + 18;
                return est > evW ? 2 : 1;
            };
            var evLines = 0;
            for (var li = 0; li < evList.length; li++) {
                evLines += evLinesOf(evList[li]);
            }
            // Task 439: блоки РЯДОМ — высота пары = максимум, а не
            // сумма (коды не добавляются под мероприятиями)
            var evH = secH + evLines * evRowH;
            var cdH = secH + codeRows * codeRowH;
            var botH = Math.max(evH, cdH);""",
    '4b. раскладка: codeW/colGap, evLines-оценка, botH = max')

rep("""                if (i >= rows.length && used + evH + cdH <= contentH) {""",
"""                if (i >= rows.length && used + botH <= contentH) {""",
    '4c. последняя страница таблицы: used + botH')

rep("""                    return { pages: pages, W: W, H: H, M: M, headH: headH,
                             dayHeadH: dayHeadH, rowH: rowH, secH: secH,
                             evRowH: evRowH, codeRowH: codeRowH, gapH: gapH };""",
"""                    return { pages: pages, W: W, H: H, M: M, headH: headH,
                             dayHeadH: dayHeadH, rowH: rowH, secH: secH,
                             evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,
                             codeW: codeW, colGap: colGap, evW: evW };""",
    '4d. return #1: + codeW/colGap/evW')

rep("""            var evCap = Math.max(1,
                Math.floor((contentH - secH) / evRowH));
            var ei = 0;
            var codesPlaced = false;
            while (ei < evList.length) {
                var take = Math.min(evCap, evList.length - ei);
                var evChunk = evList.slice(ei, ei + take);
                ei += take;
                var withCodes = (ei >= evList.length) &&
                                (secH + take * evRowH + gapH + cdH <= contentH);
                if (withCodes) codesPlaced = true;
                pages.push({ first: false, rows: [], events: evChunk,
                             codes: withCodes ? (model.codes || []) : null });
            }""",
"""            var evCap = Math.max(1,
                Math.floor((contentH - secH) / evRowH));
            var ei = 0;
            var codesPlaced = false;
            while (ei < evList.length) {
                // Task 439: страница событий набирается по бюджету
                // СТРОК (длинная запись может занимать две)
                var take = 0, budget = evCap;
                while (ei + take < evList.length) {
                    var ln = evLinesOf(evList[ei + take]);
                    if (ln > budget && take > 0) break;
                    if (ln > budget) ln = budget;
                    budget -= ln;
                    take++;
                }
                var evChunk = evList.slice(ei, ei + take);
                ei += take;
                var chunkLines = evCap - budget;
                // коды — РЯДОМ с последним куском событий (влезают
                // по ВЫСОТЕ пары — max, не сумма)
                var withCodes = (ei >= evList.length) &&
                                (Math.max(secH + chunkLines * evRowH,
                                          cdH) <= contentH);
                if (withCodes) codesPlaced = true;
                pages.push({ first: false, rows: [], events: evChunk,
                             codes: withCodes ? (model.codes || []) : null });
            }""",
    '4e. страницы событий: бюджет строк, коды рядом')

rep("""            return { pages: pages, W: W, H: H, M: M, headH: headH,
                     dayHeadH: dayHeadH, rowH: rowH, secH: secH,
                     evRowH: evRowH, codeRowH: codeRowH, gapH: gapH };""",
"""            return { pages: pages, W: W, H: H, M: M, headH: headH,
                     dayHeadH: dayHeadH, rowH: rowH, secH: secH,
                     evRowH: evRowH, codeRowH: codeRowH, gapH: gapH,
                     codeW: codeW, colGap: colGap, evW: evW };""",
    '4f. return #2: + codeW/colGap/evW')

# ============================================================
# 5. _printPdfPaintPage: Тип в строке, ширина по тексту, блоки рядом
# ============================================================
rep("""            // ширина колонки работника — по самому длинному ФИО
            var empW = 96;
            try {
                var maxW = 0;
                ctx.font = '700 9px Arial';
                for (var wi = 0; wi < model.rows.length; wi++) {
                    maxW = Math.max(maxW,
                        ctx.measureText(model.rows[wi].fio || '').width);
                }
                empW = Math.max(70, Math.min(150, maxW + 10));
            } catch (e2) { empW = 96; }""",
"""            // ширина колонки работника — по самому большому тексту
            // её ячеек (Task 439): ФИО, Тип и заголовок «Работник»
            var empW = 96;
            try {
                var maxW = 0;
                ctx.font = '700 9px Arial';
                for (var wi = 0; wi < model.rows.length; wi++) {
                    maxW = Math.max(maxW,
                        ctx.measureText(model.rows[wi].fio || '').width);
                }
                ctx.font = '6.5px Arial';
                for (var tii = 0; tii < model.rows.length; tii++) {
                    maxW = Math.max(maxW,
                        ctx.measureText(model.rows[tii].tip || '').width);
                }
                ctx.font = '700 8px Arial';
                maxW = Math.max(maxW, ctx.measureText('Работник').width);
                empW = Math.max(46, Math.min(150, maxW + 10));
            } catch (e2) { empW = 96; }""",
    '5a. PDF: empW по ФИО+Тип+заголовку, кламп 46–150')

rep("""                    if (row.pos) {
                        ctx.fillStyle = '#54606a';
                        ctx.font = '6.5px Arial';
                        ctx.fillText(row.pos, x0 + 3, y + 18);
                    }""",
"""                    if (row.tip) {
                        ctx.fillStyle = '#54606a';
                        ctx.font = '6.5px Arial';
                        ctx.fillText(row.tip, x0 + 3, y + 18);
                    }""",
    '5b. PDF: строка — row.tip (Тип)')

rep("""            // мероприятия (заголовок — как в печати: счётчик месяца)
            if (page.events) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Мероприятия · ' +
                             monthsNom[model.month - 1] + ' ' + model.year +
                             (model.events.length
                                 ? ' · ' + model.events.length : ''),
                             x0, y + 8);
                y += lay.secH;
                var evs = page.events.length ? page.events
                    : [{ range: '', color: '',
                         text: 'нет мероприятий в этом месяце' }];
                for (var ee = 0; ee < evs.length; ee++) {
                    var ex = x0;
                    if (evs[ee].color) {
                        ctx.fillStyle = evs[ee].color;
                        ctx.beginPath();
                        ctx.arc(ex + 2.4, y + 4, 2.2, 0, Math.PI * 2);
                        ctx.fill();
                    }
                    ex += 7;
                    if (evs[ee].range) {
                        ctx.fillStyle = '#1b1f24';
                        ctx.font = '700 8px Arial';
                        ctx.fillText(evs[ee].range, ex, y + 7);
                        ex += ctx.measureText(evs[ee].range).width + 6;
                    }
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '8px Arial';
                    ctx.fillText(evs[ee].text, ex, y + 7);
                    y += lay.evRowH;
                }
                y += lay.gapH;
            }

            // коды — две колонки (как в печати, Task 434)
            if (page.codes) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Коды:', x0, y + 8);
                y += lay.secH;
                var colW2 = CW / 2;
                var perCol = Math.max(1,
                    Math.ceil(page.codes.length / 2));
                for (var lc = 0; lc < page.codes.length; lc++) {
                    var lx = x0 + (lc < perCol ? 0 : colW2);
                    var ly = y + (lc % perCol) * lay.codeRowH;
                    var code = page.codes[lc];
                    if (code.color) {
                        ctx.fillStyle = code.color;
                        ctx.fillRect(lx, ly + 1, 4.5, 4.5);
                    }
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '8px Arial';
                    ctx.fillText(code.code
                        ? (code.label
                           ? code.code + ' — ' + code.label : code.code)
                        : (code.label || ''),
                        lx + 7, ly + 5.5);
                }
            }""",
"""            // Task 439: мероприятия и коды — РЯДОМ: события —
            // ЛЕВАЯ зона листа (x0..x0+evZoneW), коды — ПРАВАЯ
            // (codeX..правый край), заголовки блоков на одной
            // верхней линии
            var codeW = lay.codeW || 235;
            var colGap = lay.colGap || 12;
            var evZoneW = CW - codeW - colGap;
            var codeX = x0 + CW - codeW;
            var botY = y;
            // мероприятия (заголовок — как в печати: счётчик месяца)
            if (page.events) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Мероприятия · ' +
                             monthsNom[model.month - 1] + ' ' + model.year +
                             (model.events.length
                                 ? ' · ' + model.events.length : ''),
                             x0, y + 8);
                y += lay.secH;
                var evs = page.events.length ? page.events
                    : [{ range: '', color: '',
                         text: 'нет мероприятий в этом месяце' }];
                // слот даты — по худшему диапазону страницы
                // (короткие даты выравниваются по нему)
                var dateSlotW = 0;
                ctx.font = '700 8px Arial';
                for (var dsw = 0; dsw < evs.length; dsw++) {
                    dateSlotW = Math.max(dateSlotW,
                        ctx.measureText(evs[dsw].range || '').width);
                }
                dateSlotW = Math.min(dateSlotW + 6, 60);
                for (var ee = 0; ee < evs.length; ee++) {
                    var ex = x0;
                    if (evs[ee].color) {
                        ctx.fillStyle = evs[ee].color;
                        ctx.beginPath();
                        ctx.arc(ex + 2.4, y + 4, 2.2, 0, Math.PI * 2);
                        ctx.fill();
                    }
                    ex += 7;
                    if (evs[ee].range) {
                        ctx.fillStyle = '#1b1f24';
                        ctx.font = '700 8px Arial';
                        ctx.fillText(evs[ee].range, ex, y + 7);
                    }
                    ex += dateSlotW;
                    // текст — с переносом по словам в пределах
                    // левой зоны (не заезжает на блок кодов)
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '8px Arial';
                    var evText = String(evs[ee].text || '');
                    var evWords = evText.split(' ');
                    var evLine = '', evLy = y + 7;
                    var evMaxW = x0 + evZoneW - ex;
                    for (var ewi = 0; ewi < evWords.length; ewi++) {
                        var evCand = evLine
                            ? evLine + ' ' + evWords[ewi] : evWords[ewi];
                        if (ctx.measureText(evCand).width <= evMaxW ||
                            !evLine) {
                            evLine = evCand;
                        } else {
                            ctx.fillText(evLine, ex, evLy);
                            evLy += lay.evRowH;
                            evLine = evWords[ewi];
                        }
                    }
                    if (evLine) ctx.fillText(evLine, ex, evLy);
                    // шаг — по ФАКТИЧЕСКИ уложенным строкам
                    y += lay.evRowH *
                         (1 + Math.round((evLy - (y + 7)) / lay.evRowH));
                }
                y += lay.gapH;
            }

            // коды — ПРАВАЯ зона, две колонки (как в печати,
            // Task 434); общая верхняя линия с мероприятиями
            if (page.codes) {
                y = botY;
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Коды:', codeX, y + 8);
                y += lay.secH;
                var colW2 = codeW / 2;
                var perCol = Math.max(1,
                    Math.ceil(page.codes.length / 2));
                for (var lc = 0; lc < page.codes.length; lc++) {
                    var lx = codeX + (lc < perCol ? 0 : colW2);
                    var ly = y + (lc % perCol) * lay.codeRowH;
                    var code = page.codes[lc];
                    if (code.color) {
                        ctx.fillStyle = code.color;
                        ctx.fillRect(lx, ly + 1, 4.5, 4.5);
                    }
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '8px Arial';
                    ctx.fillText(code.code
                        ? (code.label
                           ? code.code + ' — ' + code.label : code.code)
                        : (code.label || ''),
                        lx + 7, ly + 5.5);
                }
            }""",
    '5c. PDF: мероприятия слева (перенос по словам), коды справа')

# ============================================================
# 6. Excel: работник ФИО+Тип, коды справа от мероприятий
# ============================================================
rep("""        // Task 438: строки листа «Табель» для Excel (чистая, для
        // VM-тестов): шапка из двух строк (Task 438), сетка
        // Работник/дни/Дни/Перераб. (без «Часов», переработка —
        // только дни), цветные ячейки кодов, мероприятия месяца и
        // коды в сокращённом виде (по два в ряд)""",
"""        // Task 438: строки листа «Табель» для Excel (чистая, для
        // VM-тестов): шапка из двух строк (Task 438), сетка
        // Работник/дни/Дни/Перераб. (без «Часов», переработка —
        // только дни), цветные ячейки кодов; Task 439: работник —
        // ФИО + Тип (второй строкой), мероприятия и коды — РЯДОМ
        // (даты/текст в A/B, коды — в колонке D справа)""",
    '6a. комментарий _wsTabelRows (Task 439)')

rep("""            for (var r = 0; r < model.rows.length; r++) {
                var row = model.rows[r];
                var line = [{ v: row.fio, s: 5 }];""",
"""            for (var r = 0; r < model.rows.length; r++) {
                var row = model.rows[r];
                // Task 439: работник — ФИО + Тип (перенос строки в
                // ячейке, стиль 5 с wrapText)
                var line = [{ v: row.fio +
                              (row.tip ? '\\n' + row.tip : ''), s: 5 }];""",
    '6b. Excel: ячейка A — ФИО + \\n + Тип')

rep("""            rows.push([]);
            rows.push([{ v: 'Мероприятия · ' +
                         monthsNom[model.month - 1] + ' ' + model.year +
                         (model.events.length
                             ? ' · ' + model.events.length : ''), s: 1 }]);
            if (model.events.length) {
                for (var e = 0; e < model.events.length; e++) {
                    rows.push([{ v: model.events[e].range, s: 5 },
                               { v: model.events[e].text, s: 0 }]);
                }
            } else {
                rows.push([{ v: 'нет мероприятий в этом месяце', s: 0 }]);
            }
            rows.push([]);
            rows.push([{ v: 'Коды:', s: 1 }]);
            for (var k = 0; k < model.codes.length; k += 2) {
                var pair = [];
                for (var kk = k; kk < k + 2 && kk < model.codes.length; kk++) {
                    var cd = model.codes[kk];
                    pair.push({ v: cd.code
                        ? (cd.label ? cd.code + ' — ' + cd.label : cd.code)
                        : (cd.label || ''), s: 0 });
                }
                rows.push(pair);
            }
            return rows;""",
"""            // Task 439 (заявка: «блок с кодами размести справа от
            // мероприятий»): секции — РЯДОМ: мероприятия в колонках
            // A (дата) + B (текст), коды — в колонке D (C — зазор),
            // заголовки «Мероприятия · …» и «Коды:» на одной строке
            rows.push([]);
            var evRowsOut = model.events.length
                ? model.events
                : [{ range: '', text: 'нет мероприятий в этом месяце' }];
            var codeLines = [];
            for (var k = 0; k < model.codes.length; k++) {
                var cd = model.codes[k];
                codeLines.push(cd.code
                    ? (cd.label ? cd.code + ' — ' + cd.label : cd.code)
                    : (cd.label || ''));
            }
            var botRows = Math.max(evRowsOut.length, codeLines.length, 1);
            rows.push([{ v: 'Мероприятия · ' +
                         monthsNom[model.month - 1] + ' ' + model.year +
                         (model.events.length
                             ? ' · ' + model.events.length : ''), s: 1 },
                       null, null, { v: 'Коды:', s: 1 }]);
            for (var b = 0; b < botRows; b++) {
                var bev = evRowsOut[b];
                rows.push([bev ? { v: bev.range || '', s: 5 } : null,
                           bev ? { v: bev.text || '', s: 0 } : null,
                           null,
                           codeLines[b] !== undefined
                               ? { v: codeLines[b], s: 0 } : null]);
            }
            return rows;""",
    '6c. Excel: мероприятия A/B + коды D — на тех же строках')

rep("""            var rows = this._wsTabelRows(model, colorIdx);
            var widths = [30];""",
"""            var rows = this._wsTabelRows(model, colorIdx);
            // Task 439: ширина столбца A — по самому большому тексту
            // ячейки работника (ФИО или Тип), а не фикс. 30
            var empLen = 14;
            for (var wl = 0; wl < model.rows.length; wl++) {
                empLen = Math.max(empLen,
                    String(model.rows[wl].fio || '').length,
                    String(model.rows[wl].tip || '').length);
            }
            var widths = [Math.min(34, empLen + 2)];""",
    '6d. Excel: ширина столбца A по тексту')

rep("""            xf += '<xf numFmtId="0" fontId="5" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>';""",
"""            xf += '<xf numFmtId="0" fontId="5" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment wrapText="1" vertical="top"/></xf>';""",
    '6e. Excel: стиль 5 — wrapText (ФИО + Тип двумя строками)')

rep("""        // 0 — обычный, 1 — шапка (жирный белый на синем),
        // 2 — заголовок листа (жирный 14), 3 — подстрока шапки
        // (серый), 4 — ячейка сетки (рамка), 5 — ячейка сетки
        // жирная (ФИО/итоги), 6 — день недели (серый 9, центр,
        // рамка), 7+k — заливка цвета кода k + рамка + центр""",
"""        // 0 — обычный, 1 — шапка (жирный белый на синем),
        // 2 — заголовок листа (жирный 14), 3 — подстрока шапки
        // (серый), 4 — ячейка сетки (рамка), 5 — ячейка сетки
        // жирная (ФИО+Тип [wrapText, Task 439]/итоги), 6 — день
        // недели (серый 9, центр, рамка), 7+k — заливка цвета
        // кода k + рамка + центр""",
    '6f. комментарий стилей (wrapText)')

# ============================================================
# 7. Мобильная шахматка: убрать старый код «.» («Выходной…»)
# ============================================================

rep("""                // Сервер может писать их основным кодом (generateMonth —
                // день события без смены) — такой день в попапе не
                // подсвечен строкой, событие видно в окне мероприятий
                if (this._EVENT_CODES.indexOf(c.code) !== -1) continue;""",
"""                // Сервер может писать их основным кодом (generateMonth —
                // день события без смены) — такой день в попапе не
                // подсвечен строкой, событие видно в окне мероприятий
                if (this._EVENT_CODES.indexOf(c.code) !== -1) continue;
                // Task 439 (заявка: «убери лишний код "Выходной,
                // плановый выходной день" который старый со знаком
                // "." при выборе в ячейках шахматки»): легаси-строка
                // «.» НЕ показывается отдельной строкой, если в
                // справочнике есть канонический «Выходной» (пустой
                // код — очистка ячейки); справочник только с «.»
                // (защитный путь данных) рендерит «Выходного» из
                // «.», как раньше (Task 387)
                if (c.code === '.' && hasEmptySlot) continue;""",
    '7a. попап: легаси-«.» скрыт при каноническом слоте «»')

rep("""            var html = '<div class="ws-popup-title">' + this._esc(popupDate) + ' · ' +
                       this._esc(emp ? emp['ФИО'] : 'таб. №' + tabNo) + '</div>';""",
"""            var html = '<div class="ws-popup-title">' + this._esc(popupDate) + ' · ' +
                       this._esc(emp ? emp['ФИО'] : 'таб. №' + tabNo) + '</div>';
            // Task 439: есть ли в справочнике канонический слот
            // «Выходного» (пустой код) — для дедупликации легаси-«.»
            var hasEmptySlot = false;
            for (var hs = 0; hs < this._STATUS_CODES.length; hs++) {
                if (this._STATUS_CODES[hs] &&
                    this._STATUS_CODES[hs].code === '') {
                    hasEmptySlot = true;
                    break;
                }
            }""",
    '7b. попап: предвычисление hasEmptySlot')

rep("""                var kc = String(list[k].code === undefined ? '' : list[k].code).trim();
                var kn = String(list[k].name || '').trim();
                if (!kc && !kn) continue;
                out.push({ code: kc, name: kn,
                           color: String(list[k].color || '') });""",
"""                var kc = String(list[k].code === undefined ? '' : list[k].code).trim();
                var kn = String(list[k].name || '').trim();
                if (!kc && !kn) continue;
                // Task 439: «точечные» легаси-коды («.» с пробелами,
                // «·») — старый код «Выходного»; слот «Выходной»
                // (пустой код) есть в каноне ВСЕГДА — дубль в хвост
                // списка не попадает (лишняя строка «Выходной,
                // плановый выходной день» в окне выбора кодов ячеек,
                // в т.ч. мобильная версия)
                if (kc === '.' || kc === '·') continue;
                out.push({ code: kc, name: kn,
                           color: String(list[k].color || '') });""",
    '7c. нормализация: «точечные» легаси-коды не попадают в хвост')

# ============================================================
# 8. _posLabel УДАЛЁН (потребителей после Task 439 не осталось)
# ============================================================
rep("""        // Task 255: подпись должности с режимом занятости — данные из
        // таблицы «Сотрудники» файла табель_КИП_ИОС (тот же справочник
        // в Google-таблице, метод listEmployees): столбец C — тип
        // (сменный/дневной), столбец D — номер смены (1..5, только у
        // сменного). Примеры формирования: «Слесарь КИПиА смена №1»
        // (сменный, смена 1), «Слесарь КИПиА дневной» (дневной).
        // Сменный без номера смены — «… сменный»; без типа — только
        // должность; пусто и там и там — '' (строка не рендерится).
        // Task 402: используется ПЕЧАТНОЙ формой (_buildPrintHtml,
        // Task 361) — шахматка перешла на _empPosLine/_empTipLine.
        _posLabel: function(emp) {
            var pos = String(emp['должность'] || '').trim();
            var tip = String(emp['тип'] || '').trim();
            var smena = parseInt(emp['смена'], 10);
            var suffix = '';
            if (tip === 'сменный') {
                suffix = (smena >= 1 && smena <= 5) ? ' смена №' + smena : ' сменный';
            } else if (tip === 'дневной') {
                suffix = ' дневной';
            }
            if (!pos) return suffix.trim();
            return pos + suffix;
        },

""",
"""        // Task 439: метод _posLabel (склеенная подпись «должность +
        // тип», Tasks 255/361) УДАЛЁН — печатная форма перешла на
        // «ФИО + Тип» (_empTipLine, заявка «в колонке с работниками
        // оставь только ФИО и Тип»); сетка с Task 402 использует
        // _empPosLine/_empTipLine — потребителей не осталось.

""",
    '8. _posLabel удалён')

# ============================================================
assert src != orig
io.open(path, 'w', encoding='utf-8').write(src)
print('\nГотово: %d блоков замен, index.html обновлён' % n[0])
