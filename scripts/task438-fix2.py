#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 438, фикс 2 — доадаптация тестов, найденных полным прогоном:
# 343 (значение «1/12» → «1»), 360 (хвост iLegend < iFoot), 361
# (14mm → 12mm; сноска значка → удалена), 388 (сноска значка),
# 430 (сигнатура вызова _openPrintPreview(html, ctx)), 431 (якорь
# закрытий после удаления сноски). Запуск из корня kip8test.
import io

def patch(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        found = s.count(old)
        assert found == 1, '%s: найдено %d (ожидалось 1): %s' % (path, found, old[:80])
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: %d замен' % (path, len(pairs)))

# --- test-task343.js: старый формат «1/12» ---
patch('tests/test-task343.js', [
("""        // построчные итоги при этом на месте
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">1/12</td>') !== -1,
            'колонка «Перераб.» сотрудника жива (регресс 342)');""",
"""        // построчные итоги при этом на месте
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">1</td>') !== -1,
            'колонка «Перераб.» сотрудника жива — только дни (Task 438)');
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">1/12</td>') === -1,
            'старый формат «1/12» не печатается (Task 438)');"""),
])

# --- test-task360.js: хвост iLegend < iFoot ---
patch('tests/test-task360.js', [
("""        assertTrue(iMev < iLegend, 'перечень кодов — ПОД списком мероприятий'
            + ' (Task 433: вертикальная секция, флоат снят)');
        assertTrue(iLegend < iFoot, 'сноска после перечня кодов');
    });""",
"""        assertTrue(iMev < iLegend, 'перечень кодов — ПОД списком мероприятий'
            + ' (Task 433: вертикальная секция, флоат снят)');
        // Task 438: сноски после кодов больше нет — лист заканчивается
        // перечнем кодов
    });"""),
])

# --- test-task361.js: ширина 12mm + сноска значка (SRC и VM) ---
patch('tests/test-task361.js', [
("""    test('SRC: итоговые колонки и точка переработки шире/крупнее', () => {
        assertTrue(ruleOf('#wsPrintSheet .wsp-tot {').indexOf('width: 10mm') !== -1,
            '«Дни»/«Часы» 10mm (были 9mm)');
        assertTrue(ruleOf('#wsPrintSheet .wsp-tot.wsp-tot-over {').indexOf('width: 14mm') !== -1,
            '«Перераб.» 14mm (была 12mm)');""",
"""    test('SRC: итоговые колонки и точка переработки шире/крупнее', () => {
        assertTrue(ruleOf('#wsPrintSheet .wsp-tot {').indexOf('width: 10mm') !== -1,
            '«Дни» 10mm (были 9mm)');
        assertTrue(ruleOf('#wsPrintSheet .wsp-tot.wsp-tot-over {').indexOf('width: 12mm') !== -1,
            '«Перераб.» 12mm (Task 438: только дни; было 14mm под «дни/ч»)');"""),
("""    test('SRC: сноска поясняет значок мероприятия в углу ячейки', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('значок в углу ячейки') !== -1,
            'пояснение значка мероприятия');
        assertFalse(b.indexOf('день ещё не сформирован') !== -1,
            'пояснение «день ещё не сформирован» удалено (Task 388)');
    });""",
"""    test('SRC: сноска удалена — пояснений значка больше нет (Task 438)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('значок в углу ячейки') === -1,
            'сноска с пояснением значка удалена вместе со wsp-foot (Task 438)');
        assertFalse(b.indexOf('день ещё не сформирован') !== -1,
            'пояснение «день ещё не сформирован» удалено (Task 388)');
    });"""),
("""        assertTrue(html.indexOf('значок в углу ячейки') !== -1, 'сноска с пояснением значка (Task 361)');""",
"""        assertTrue(html.indexOf('значок в углу ячейки') === -1,
            'сноски с пояснением значка нет (Task 438)');"""),
])

# --- test-task388.js: сноска значка ---
patch('tests/test-task388.js', [
("""    test('печать: сноска без «день ещё не сформирован»', () => {
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        assertFalse(b.indexOf('день ещё не сформирован') !== -1,
            'пояснение пунктирного значка удалено');
        assertTrue(b.indexOf('значок в углу ячейки') !== -1,
            'пояснение значка мероприятия живо (регресс 361)');
    });""",
"""    test('печать: сноски нет вовсе (Task 438)', () => {
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        assertFalse(b.indexOf('день ещё не сформирован') !== -1,
            'пояснение пунктирного значка удалено');
        assertTrue(b.indexOf('значок в углу ячейки') === -1,
            'сноска удалена целиком (Task 438); значки видны в ячейках, перечень кодов — выше');
    });"""),
])

# --- test-task430.js: сигнатура вызова с контекстом ---
patch('tests/test-task430.js', [
("""        const m = methodText(INDEX_SRC, 'printGrid');
        const iPrev = m.indexOf('this._openPrintPreview(html)');
        const iPrint = m.indexOf('window.print()');
        assertTrue(iPrev !== -1, 'printGrid зовёт _openPrintPreview');""",
"""        const m = methodText(INDEX_SRC, 'printGrid');
        const iPrev = m.indexOf('this._openPrintPreview(html, {');
        const iPrint = m.indexOf('window.print()');
        assertTrue(iPrev !== -1, 'printGrid зовёт _openPrintPreview (Task 438: с контекстом)');"""),
])

# --- test-task431.js: якорь закрытий (сноска удалена) ---
patch('tests/test-task431.js', [
("""    test('wsp-foot удалена; закрытие mev + обёртки — два оператора (Task 438)', () => {
        // Task 438 (заявка: «нижний текст убери»): сноска wsp-foot
        // УДАЛЕНА — но структура секций не изменилась
        const f = INDEX_SRC.indexOf("html += '<div class=\\"wsp-foot\\">");
        assertTrue(f === -1, 'сноска wsp_foot не строится (Task 438)');
        // закрытие мероприятий и обёртки — ДВА последовательных
        // оператора (прежде один '</div></div>')
        const close2 = INDEX_SRC.lastIndexOf(
            "html += '</div>';",
            INDEX_SRC.indexOf("html += '<div class=\\"wsp-legend\\">"));
        const close1 = INDEX_SRC.lastIndexOf("html += '</div>';", close2 - 1);
        assertTrue(close1 !== -1 && close2 !== -1 && close2 - close1 < 200,
            'закрытие mev + обёртки — два оператора (Task 432 жив)');
        const open = INDEX_SRC.lastIndexOf("html += '<div class=\\"wsp-bottom\\">'", close1);
        assertTrue(open !== -1 && open < close1,
            'обёртка wsp-bottom открывается раньше секций');
        // внутри обёртки — ОБА блока: мероприятия + коды
        const wrap = INDEX_SRC.slice(open, close1);
        assertTrue(wrap.indexOf('wsp-mev') !== -1 && wrap.indexOf('wsp-legend') !== -1,
            'в обёртке — список мероприятий и перечень кодов');
    });""",
"""    test('wsp-foot удалена; закрытия секций — три оператора подряд (Task 438)', () => {
        // Task 438 (заявка: «нижний текст убери»): сноска wsp-foot
        // УДАЛЕНА — но структура секций не изменилась
        const f = INDEX_SRC.indexOf("html += '<div class=\\"wsp-foot\\">");
        assertTrue(f === -1, 'сноска wsp-foot не строится (Task 438)');
        const iLegend = INDEX_SRC.indexOf("html += '<div class=\\"wsp-legend\\">");
        assertTrue(iLegend !== -1, 'легенда кодов строится');
        // Task 434 жив: закрытия сетки-колонок, легенды и обёртки —
        // ТРИ последовательных оператора (сноска шла после них)
        const close1 = INDEX_SRC.indexOf("html += '</div>';", iLegend);
        const close2 = INDEX_SRC.indexOf("html += '</div>';", close1 + 1);
        const close3 = INDEX_SRC.indexOf("html += '</div>';", close2 + 1);
        assertTrue(close1 !== -1 && close2 !== -1 && close3 !== -1 &&
                   close2 - close1 < 200 && close3 - close2 < 200,
            'закрытия сетки/легенды/обёртки — подряд (Task 434 жив)');
        const open = INDEX_SRC.lastIndexOf("html += '<div class=\\"wsp-bottom\\">'", iLegend);
        assertTrue(open !== -1 && open < iLegend,
            'обёртка wsp-bottom открывается раньше секций');
        // внутри обёртки — ОБА блока: мероприятия + коды
        const wrap = INDEX_SRC.slice(open, close3);
        assertTrue(wrap.indexOf('wsp-mev') !== -1 && wrap.indexOf('wsp-legend') !== -1,
            'в обёртке — список мероприятий и перечень кодов');
    });"""),
])

print('OK: фикс 2 применён')
