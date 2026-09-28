#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 438, фикс 1: (1) вернуть определение pad2 в _buildPrintHtml
# (нужно для mStart/mEnd списка мероприятий — удалил слишком много
# вместе со штампом «Распечатано»); (2) «.» больше НЕ попадает в
# легаси-перечень печатной легенды — точка уже раскрыта слотом
# «Выходной» (пустой код) выше, дублирующая голая «.» в списке кодов
# была косметическим багом печати; (3) то же в новом _printCodesData
# для PDF/Excel. Запуск из корня kip8test.
import io

path = 'index.html'
src = io.open(path, encoding='utf-8').read()

def rep(old, new, cnt=1, label=''):
    global src
    found = src.count(old)
    assert found == cnt, 'FAIL %s: найдено %d, ожидалось %d' % (label, found, cnt)
    src = src.replace(old, new)

# 1. pad2 возвращается (mStart/mEnd событий его используют)
rep("""            // Task 438: норма месяца и штамп «Распечатано» в шапке
            // печати больше не вычисляются (заявка — шапка из двух
            // строк); норма остаётся в приложении («Итоги учёта»)

""",
"""            // Task 438: норма месяца и штамп «Распечатано» в шапке
            // печати больше не вычисляются (заявка — шапка из двух
            // строк); норма остаётся в приложении («Итоги учёта»).
            // pad2 жив: даты границ месяца нужны списку мероприятий
            var pad2 = function(v) { return (v < 10 ? '0' : '') + v; };

""", 1, 'pad2')

# 2. легаси-коды печати: «.» не дублируется (слот Выходной выше)
rep("""            // легаси-коды месяца, которых нет в справочнике
            var legacy = [];
            for (var lk in usedCodes) {
                if (!Object.prototype.hasOwnProperty.call(usedCodes, lk)) continue;
                var known = false;""",
"""            // легаси-коды месяца, которых нет в справочнике.
            // Task 438: «.» пропускается — точка уже раскрыта слотом
            // «Выходной» (пустой код) выше, дублирующая голая «.»
            // в перечне не нужна
            var legacy = [];
            for (var lk in usedCodes) {
                if (!Object.prototype.hasOwnProperty.call(usedCodes, lk)) continue;
                if (lk === '.') continue;
                var known = false;""", 1, 'легаси печати без точки')

# 3. то же в _printCodesData (PDF/Excel)
rep("""            var legacy = [];
            for (var lk in used) {
                if (!Object.prototype.hasOwnProperty.call(used, lk)) continue;
                var known = false;
                for (var cj = 0; cj < codes.length; cj++) {
                    if (codes[cj].code === lk) { known = true; break; }
                }
                if (!known) legacy.push(lk);
            }""",
"""            var legacy = [];
            for (var lk in used) {
                if (!Object.prototype.hasOwnProperty.call(used, lk)) continue;
                // «.» уже раскрыт слотом «Выходной» (пустой код)
                if (lk === '.') continue;
                var known = false;
                for (var cj = 0; cj < codes.length; cj++) {
                    if (codes[cj].code === lk) { known = true; break; }
                }
                if (!known) legacy.push(lk);
            }""", 1, 'легаси _printCodesData без точки')

io.open(path, 'w', encoding='utf-8').write(src)
print('index.html: фикс 1 применён (pad2 + «.» вне легаси)')
