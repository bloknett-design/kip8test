#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 440 — патч №2: коды следуют ЗА ТЕКСТОМ мероприятий (не прижаты
к правому краю листа) — дословная семантика заявок Task 431 («список
кодов расположи справа от списка мероприятий на расстоянии 10px,
СЕЙЧАС МЕЖДУ НИМИ ОЧЕНЬ БОЛЬШОЕ РАССТОЯНИЕ») и Task 440 («коды
справа от мероприятий на расстоянии друг от друга 10px»):
- HTML: .wsp-mev flex 1 1 auto → 0 1 auto (НЕ растягивается) — блок
  кодов встаёт в 10px от правого края текста мероприятий; длинные
  тексты по-прежнему переночатся (flex-shrink + min-width: 0 — зона
  ограничена: лист − 92мм кодов − 10px);
- PDF: _printPdfPaintPage — codeX по ФАКТИЧЕСКОМУ правому краю строк
  мероприятий (evRightMax + colGap), не x0+CW−codeW; страницы без
  мероприятий — коды от левого края (+colGap); ограничение зоны
  мероприятий (evZoneW) и пагинация _printPdfLayout НЕ меняются.
"""
import io

PATH = '/home/z/my-project/kip8test/index.html'
src = io.open(PATH, encoding='utf-8').read()
n = [0]

def rep(old, new, what):
    global src
    cnt = src.count(old)
    assert cnt == 1, 'FAIL [%s]: найдено %d (ожидалось 1)' % (what, cnt)
    src = src.replace(old, new)
    n[0] += 1
    print('OK  %02d) %s' % (n[0], what))

# ----------------------------------------------------------------------
# 1. HTML: .wsp-mev НЕ растягивается (Task 431 → 440)
# ----------------------------------------------------------------------
rep("""        #wsPrintSheet .wsp-mev {
            margin-top: 0;
            font-size: 11px;
            line-height: 1.6;
            /* Task 439: мероприятия — ЛЕВАЯ часть ряда */
            flex: 1 1 auto;
            min-width: 0;
        }""",
    """        #wsPrintSheet .wsp-mev {
            margin-top: 0;
            font-size: 11px;
            line-height: 1.6;
            /* Task 431 → Task 440 (заявка: «коды справа от
               мероприятий на расстоянии друг от друга 10px»; ранее
               в 431 — «сейчас между ними очень большое расстояние»):
               столбик мероприятий НЕ растягивается (flex-grow снят,
               было 1 1 auto Task 439) — блок кодов встаёт в 10px от
               ПРАВОГО КРАЯ ТЕКСТА мероприятий (самой широкой строки),
               а не прижатым к правому краю листа; длинные тексты —
               по-прежнему переносятся (зона усечена flex-shrink +
               min-width: 0: лист − 92мм кодов − 10px зазор) */
            flex: 0 1 auto;
            min-width: 0;
        }""",
    'CSS: .wsp-mev flex 0 1 auto (коды за текстом)')

# ----------------------------------------------------------------------
# 2. PDF: codeX по фактическому краю текста мероприятий
# ----------------------------------------------------------------------
rep("""            var codeW = lay.codeW || 235;
            // Task 440: зазор мероприятий↔коды — 7.5pt (= 10px)
            var colGap = lay.colGap || 7.5;
            var evZoneW = CW - codeW - colGap;
            var codeX = x0 + CW - codeW;
            var botY = y;""",
    """            var codeW = lay.codeW || 235;
            // Task 440: зазор мероприятий↔коды — 7.5pt (= 10px)
            var colGap = lay.colGap || 7.5;
            var evZoneW = CW - codeW - colGap;
            // Task 440 (как в HTML flex 0 1 auto): блок кодов — за
            // ФАКТИЧЕСКИМ правым краем строк мероприятий (+colGap),
            // не прижат к правому краю листа; страницы без
            // мероприятий — коды от левого края (+colGap);
            // кодыX вычисляется ПОСЛЕ отрисовки мероприятий
            // (evRightMax), ограничение — правый край листа
            var codeX = x0 + colGap;
            var evRightMax = 0;
            var botY = y;""",
    'PDF paint: заготовка codeX/evRightMax')

# заголовок «Мероприятия · …» — учитывается в крае
rep("""            if (page.events) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Мероприятия · ' +
                             monthsNom[model.month - 1] + ' ' + model.year +
                             (model.events.length
                                 ? ' · ' + model.events.length : ''),
                             x0, y + 8);""",
    """            if (page.events) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                var evHead = 'Мероприятия · ' +
                             monthsNom[model.month - 1] + ' ' + model.year +
                             (model.events.length
                                 ? ' · ' + model.events.length : '');
                ctx.fillText(evHead, x0, y + 8);
                evRightMax = Math.max(evRightMax,
                    x0 + ctx.measureText(evHead).width);""",
    'PDF paint: заголовок мероприятий в evRightMax')

# строки мероприятий: каждая уложенная строка — в крае
rep("""                    var evMaxW = x0 + evZoneW - ex;
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
                    if (evLine) ctx.fillText(evLine, ex, evLy);""",
    """                    var evMaxW = x0 + evZoneW - ex;
                    for (var ewi = 0; ewi < evWords.length; ewi++) {
                        var evCand = evLine
                            ? evLine + ' ' + evWords[ewi] : evWords[ewi];
                        if (ctx.measureText(evCand).width <= evMaxW ||
                            !evLine) {
                            evLine = evCand;
                        } else {
                            ctx.fillText(evLine, ex, evLy);
                            evRightMax = Math.max(evRightMax,
                                ex + ctx.measureText(evLine).width);
                            evLy += lay.evRowH;
                            evLine = evWords[ewi];
                        }
                    }
                    if (evLine) {
                        ctx.fillText(evLine, ex, evLy);
                        evRightMax = Math.max(evRightMax,
                            ex + ctx.measureText(evLine).width);
                    }""",
    'PDF paint: строки мероприятий в evRightMax')

# коды: codeX по краю текста (не правый край листа)
rep("""            if (page.codes) {
                y = botY;
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Коды:', codeX, y + 8);""",
    """            if (page.codes) {
                y = botY;
                // Task 440: коды — за фактическим краем мероприятий
                // (в пределах листа); лист пуст от мероприятий — от
                // левого края (+colGap)
                if (page.events && evRightMax > 0) {
                    codeX = Math.min(evRightMax + colGap,
                                     x0 + CW - codeW);
                }
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Коды:', codeX, y + 8);""",
    'PDF paint: коды за краем текста мероприятий')

io.open(PATH, 'w', encoding='utf-8').write(src)
print('\nГОТОВО: %d замен' % n[0])
