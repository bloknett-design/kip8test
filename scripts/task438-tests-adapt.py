#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 438: адаптация существующих тестов под новый формат
# печати (шапка 2 строки, без сноски wsp-foot, без колонки
# «Часы», «Перераб.» — только дни) и диалог с PDF/Excel вместо
# HTML. Затронуты: 341, 342, 343, 360, 361, 362, 364, 375,
# 430, 431, 432, 433, 434. Запуск из корня kip8test.
import io

def patch(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        found = s.count(old)
        assert found == 1, '%s: найдено %d (ожидалось 1): %s' % (path, found, old[:80])
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: %d замен' % (path, len(pairs)))

# ============================================================
# test-task341.js — шапка/штамп/норма/Часы/wsp-foot
# ============================================================
patch('tests/test-task341.js', [
("""    test('VM: шапка — заголовок, месяц/год, вид, штамп печати', () => {
        var html = sheetHost({ view: 'shift' })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('График работы — табель учёта рабочего времени') !== -1,
            'заголовок листа');
        assertTrue(html.indexOf('Сентябрь 2026') !== -1, 'месяц и год');
        assertTrue(html.indexOf('вид табеля: сменный') !== -1, 'вид табеля');
        assertTrue(html.indexOf('Распечатано:') !== -1, 'штамп «Распечатано»');
    });""",
"""    test('VM: шапка — заголовок, месяц/год, вид (Task 438: 2 строки)', () => {
        var html = sheetHost({ view: 'shift' })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('<div class="wsp-title">График работы</div>') !== -1,
            'заголовок листа (Task 438: «График работы»)');
        assertTrue(html.indexOf('Сентябрь 2026') !== -1, 'месяц и год');
        assertTrue(html.indexOf('вид табеля: сменный') !== -1, 'вид табеля');
        assertTrue(html.indexOf('Распечатано:') === -1,
            'штампа «Распечатано» нет (Task 438)');
    });"""),
("""    test('VM: строки сотрудников — ФИО, должность, итоги «Дни»/«Часы»', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('Иванов Иван Иванович') !== -1, 'ФИО сотрудника');
        assertTrue(html.indexOf('Слесарь КИПиА, смена 1') !== -1, 'должность под ФИО');
        assertTrue(html.indexOf('>21</td>') !== -1, 'дни явки 017');
        assertTrue(html.indexOf('>151,2</td>') !== -1, 'часы 017 с запятой');
        assertTrue(html.indexOf('<th class="wsp-tot">Дни</th>') !== -1 &&
                   html.indexOf('<th class="wsp-tot">Часы</th>') !== -1,
            'заголовки колонок итогов');
    });""",
"""    test('VM: строки сотрудников — ФИО, должность, итоги (Task 438: без «Часов»)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('Иванов Иван Иванович') !== -1, 'ФИО сотрудника');
        assertTrue(html.indexOf('Слесарь КИПиА, смена 1') !== -1, 'должность под ФИО');
        assertTrue(html.indexOf('>21</td>') !== -1, 'дни явки 017');
        assertTrue(html.indexOf('>151,2</td>') === -1,
            'часы НЕ печатаются (Task 438: колонка «Часы» удалена)');
        assertTrue(html.indexOf('<th class="wsp-tot">Дни</th>') !== -1,
            'заголовок колонки «Дни»');
        assertTrue(html.indexOf('<th class="wsp-tot">Часы</th>') === -1,
            'колонки «Часы» нет (Task 438)');
    });"""),
("""        assertTrue(html.indexOf('wsp-foot') !== -1, 'пояснения внизу');""",
"""        assertTrue(html.indexOf('wsp-foot') === -1,
            'пояснения внизу удалены (Task 438)');"""),
("""    test('VM: норма месяца — из ProdCalendar (когда доступен)', () => {
        var pcal = { monthStats: function(y, m) { return { workDays: 22, hours40: 176 }; } };
        var html = sheetHost({ pcal: pcal })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('Норма (40-час. неделя): 22 раб. дн. · 176 ч') !== -1,
            'строка нормы');
    });""",
"""    test('VM: нормы в шапке НЕТ даже при живом ProdCalendar (Task 438)', () => {
        var pcal = { monthStats: function(y, m) { return { workDays: 22, hours40: 176 }; } };
        var html = sheetHost({ pcal: pcal })._buildPrintHtml(EMPS, AGG);
        assertTrue(html.indexOf('Норма (40-час') === -1,
            'строка нормы удалена из шапки (Task 438)');
        assertTrue(html.indexOf('22 раб. дн.') === -1, 'цифр нормы нет');
    });"""),
])

# ============================================================
# test-task342.js — CSS 12mm, подпись «дни», значения без часов
# ============================================================
patch('tests/test-task342.js', [
("""    test('SRC: правило .wsp-tot-over (ширина 14mm, Task 361)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-tot.wsp-tot-over');
        assertTrue(i !== -1, 'правило ширины wsp-tot-over есть');
        const block = INDEX_SRC.slice(i, i + 200);
        assertTrue(block.indexOf('width: 14mm') !== -1,
            'ширина 14mm (Task 361: шире «Дни»/«Часы» — 10mm, шрифт 11px)');
    });""",
"""    test('SRC: правило .wsp-tot-over (ширина 12mm, Task 438)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-tot.wsp-tot-over');
        assertTrue(i !== -1, 'правило ширины wsp-tot-over есть');
        const block = INDEX_SRC.slice(i, i + 200);
        assertTrue(block.indexOf('width: 12mm') !== -1,
            'ширина 12mm (Task 438: в колонке только дни, было 14mm)');
    });"""),
("""    test('SRC: подпись заголовка «дни/ч» — мелкий блок, как дни недели', () => {""",
"""    test('SRC: подпись заголовка «дни» — мелкий блок, как дни недели', () => {"""),
("""    test('SRC: базовые колонки «Дни»/«Часы» не тронуты (10mm, Task 361)', () => {""",
"""    test('SRC: базовая колонка «Дни» не тронута (10mm, Task 361)', () => {"""),
("""    test('SRC: шапка — 3 колонки итогов, «Перераб.» с подписью', () => {
        const b = methodText(WS_CLIENT, '_buildPrintHtml');
        assertTrue(b.indexOf('<th class="wsp-tot">Дни</th>') !== -1, 'Дни');
        assertTrue(b.indexOf('<th class="wsp-tot">Часы</th>') !== -1, 'Часы');
        assertTrue(b.indexOf('wsp-tot-over">Перераб.<span>дни/ч</span></th>') !== -1,
            '«Перераб.» + подпись «дни/ч»');
    });""",
"""    test('SRC: шапка — 2 колонки итогов, «Перераб.» с подписью «дни»', () => {
        const b = methodText(WS_CLIENT, '_buildPrintHtml');
        assertTrue(b.indexOf('<th class="wsp-tot">Дни</th>') !== -1, 'Дни');
        assertTrue(b.indexOf('<th class="wsp-tot">Часы</th>') === -1,
            'Часы удалены (Task 438)');
        assertTrue(b.indexOf('wsp-tot-over">Перераб.<span>дни</span></th>') !== -1,
            '«Перераб.» + подпись «дни» (Task 438)');
    });"""),
("""    test('SRC: строка сотрудника — ячейка wsp-tot-over из agg (overDays/over)', () => {
        const b = methodText(WS_CLIENT, '_buildPrintHtml');
        const i = b.indexOf("'<td class=\\"wsp-tot wsp-tot-over\\">'");
        assertTrue(i !== -1, 'ячейка колонки в строках');
        const tail = b.slice(i, i + 400);
        assertTrue(tail.indexOf('a.overDays') !== -1 && tail.indexOf('a.over') !== -1,
            'значение из счётчиков agg (overDays/over)');
        assertTrue(tail.indexOf('_fmtTotalsNum') !== -1,
            'часы форматируются _fmtTotalsNum (запятая)');
    });""",
"""    test('SRC: строка сотрудника — ячейка wsp-tot-over из agg (только дни)', () => {
        const b = methodText(WS_CLIENT, '_buildPrintHtml');
        const i = b.indexOf("'<td class=\\"wsp-tot wsp-tot-over\\">'");
        assertTrue(i !== -1, 'ячейка колонки в строках');
        const tail = b.slice(i, i + 300);
        assertTrue(tail.indexOf('a.overDays') !== -1,
            'значение — дни переработки (overDays, Task 438)');
        assertTrue(tail.indexOf("a.overDays + '/'") === -1,
            'склейка «дни/часы» удалена (Task 438)');
        assertTrue(tail.indexOf('_fmtTotalsNum') === -1,
            'форматирование часов не используется (Task 438)');
    });"""),
("""    test('SRC: сноска поясняет колонку «Перераб.» (а не отсылает в приложение)', () => {
        const b = methodText(WS_CLIENT, '_buildPrintHtml');
        assertTrue(b.indexOf('«Перераб.» — дни/часы переработки') !== -1,
            'пояснение формата в сноске');
        assertFalse(b.indexOf('учтена в приложении («Итоги учёта»') !== -1,
            'старая отсылка удалена');
    });""",
"""    test('SRC: сноски wsp-foot больше нет (Task 438)', () => {
        const b = methodText(WS_CLIENT, '_buildPrintHtml');
        assertFalse(b.indexOf('<div class="wsp-foot">') !== -1,
            'сноска удалена целиком (Task 438)');
        assertFalse(b.indexOf('«Перераб.» — дни/часы переработки') !== -1,
            'пояснение формата вместе со сноской убрано');
        assertFalse(b.indexOf('учтена в приложении («Итоги учёта»') !== -1,
            'старая отсылка удалена');
    });"""),
("""    test('VM: переработка — «дни/часы» («3/36»)', () => {
        var agg = {
            byTab: { '017': { work: 21, hours: 151.2, over: 36, overDays: 3 },
                     '031': { work: 19, hours: 136.8, over: 0, overDays: 0 } },
            grand: { work: 40, hours: 288, over: 36, overDays: 3 }
        };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">3/36</td>') !== -1,
            'значение «3/36» (3 дня, 36 часов)');
    });""",
"""    test('VM: переработка — только дни («3»)', () => {
        var agg = {
            byTab: { '017': { work: 21, hours: 151.2, over: 36, overDays: 3 },
                     '031': { work: 19, hours: 136.8, over: 0, overDays: 0 } },
            grand: { work: 40, hours: 288, over: 36, overDays: 3 }
        };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">3</td>') !== -1,
            'значение «3» — только дни (Task 438)');
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">3/36</td>') === -1,
            'старый формат «3/36» не печатается');
    });"""),
("""    test('VM: дробные часы — с запятой («2/16,5»)', () => {
        var agg = {
            byTab: { '017': { work: 21, hours: 151.2, over: 16.5, overDays: 2 } },
            grand: { work: 21, hours: 151.2, over: 16.5, overDays: 2 }
        };
        var html = sheetHost()._buildPrintHtml([EMPS[0]], agg);
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">2/16,5</td>') !== -1,
            'дробные часы печатаются с запятой');
    });""",
"""    test('VM: переработка без часов — целые дни («2»)', () => {
        var agg = {
            byTab: { '017': { work: 21, hours: 151.2, over: 16.5, overDays: 2 } },
            grand: { work: 21, hours: 151.2, over: 16.5, overDays: 2 }
        };
        var html = sheetHost()._buildPrintHtml([EMPS[0]], agg);
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">2</td>') !== -1,
            'значение «2» — дни; часы (16,5) не печатаются (Task 438)');
    });"""),
("""    test('VM: сноска wsp-foot — новый текст про «Перераб.»', () => {
        var agg = { byTab: {}, grand: null };
        var html = sheetHost()._buildPrintHtml([EMPS[2]], agg);
        var foot = html.slice(html.indexOf('wsp-foot'));
        assertTrue(foot.indexOf('«Перераб.» — дни/часы переработки') !== -1,
            'пояснение формата');
        assertTrue(foot.indexOf('(без переработки д/н)') !== -1,
            '«Дни»/«Часы» помечены как без переработки');
    });""",
"""    test('VM: сноски wsp-foot нет (Task 438)', () => {
        var agg = { byTab: {}, grand: null };
        var html = sheetHost()._buildPrintHtml([EMPS[2]], agg);
        assertTrue(html.indexOf('wsp-foot') === -1,
            'сноска внизу листа удалена (Task 438)');
    });"""),
])

# ============================================================
# test-task343.js — колонки/сноска
# ============================================================
patch('tests/test-task343.js', [
("""        assertTrue(b.indexOf('<th class="wsp-tot">Дни</th>') !== -1, 'колонка «Дни»');
        assertTrue(b.indexOf('<th class="wsp-tot">Часы</th>') !== -1, 'колонка «Часы»');
        assertTrue(b.indexOf('wsp-tot-over">Перераб.<span>дни/ч</span></th>') !== -1,
            'колонка «Перераб.» (Task 342)');""",
"""        assertTrue(b.indexOf('<th class="wsp-tot">Дни</th>') !== -1, 'колонка «Дни»');
        assertTrue(b.indexOf('<th class="wsp-tot">Часы</th>') === -1,
            'колонка «Часы» удалена (Task 438)');
        assertTrue(b.indexOf('wsp-tot-over">Перераб.<span>дни</span></th>') !== -1,
            'колонка «Перераб.» — только дни (Task 342/438)');"""),
("""    test('SRC: сноска wsp-foot упоминает значок мероприятия (Task 361)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('значок в углу ячейки') !== -1,
            'упоминание значка мероприятия есть');
        assertTrue(b.indexOf('пунктирная рамка ячейки — плановый отпуск') !== -1,
            'пояснение плана отпуска живо (регресс 341)');
        assertTrue(b.indexOf('красная точка — переработка') !== -1,
            'пояснение переработки живо (регресс 341/342)');
    });""",
"""    test('SRC: сноска wsp-foot удалена (Task 438)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        assertTrue(b.indexOf('<div class="wsp-foot">') === -1,
            'сноска не строится (Task 438)');
        assertTrue(b.indexOf('значок в углу ячейки') === -1,
            'текст сноски про значок удалён вместе со сноской');
        assertTrue(b.indexOf('красная точка — переработка') === -1,
            'текст сноски про переработку удалён');
    });"""),
("""    test('VM: структура — шапка, строки, легенда, сноска; после строк таблица закрывается', () => {
        var agg = { byTab: {}, grand: null };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        var iClose = html.indexOf('</tbody></table>');
        assertTrue(iClose !== -1, 'таблица закрыта');
        assertTrue(html.indexOf('wsp-legend') !== -1, 'легенда после таблицы');
        assertTrue(html.indexOf('wsp-foot') !== -1, 'сноска жива');""",
"""    test('VM: структура — шапка, строки, легенда; после строк таблица закрывается', () => {
        var agg = { byTab: {}, grand: null };
        var html = sheetHost()._buildPrintHtml(EMPS, agg);
        var iClose = html.indexOf('</tbody></table>');
        assertTrue(iClose !== -1, 'таблица закрыта');
        assertTrue(html.indexOf('wsp-legend') !== -1, 'легенда после таблицы');
        assertTrue(html.indexOf('wsp-foot') === -1, 'сноски нет (Task 438)');"""),
("""    test('VM: сноска — пояснения живы + значок мероприятия упомянут (Task 361)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, { byTab: {}, grand: null });
        var foot = html.slice(html.indexOf('wsp-foot'));
        assertTrue(foot.indexOf('мероприятие') !== -1,
            'значок мероприятия в углу ячейки пояснён (Task 361)');
        assertTrue(foot.indexOf('«Перераб.» — дни/часы переработки') !== -1,
            'пояснение колонки (регресс 342)');
        assertTrue(foot.indexOf('пунктирная рамка') !== -1, 'план отпуска пояснён');
    });""",
"""    test('VM: сноски нет — лист заканчивается перечнем кодов (Task 438)', () => {
        var html = sheetHost()._buildPrintHtml(EMPS, { byTab: {}, grand: null });
        assertTrue(html.indexOf('wsp-foot') === -1, 'сноски нет (Task 438)');
        assertTrue(html.indexOf('сокращённый предпраздничный') === -1,
            'текста сноски нет');
    });"""),
])

# ============================================================
# test-task360.js — порядок секций без сноски + регресс-блок
# ============================================================
patch('tests/test-task360.js', [
("""    test('SRC: порядок секций — таблица → обёртка(мероприятия→коды) → сноска', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iTable = b.indexOf("'</tbody></table>'");
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iTable !== -1 && iMev !== -1 && iLegend !== -1 && iFoot !== -1,
            'все секции на месте');""",
"""    test('SRC: порядок секций — таблица → обёртка(мероприятия→коды)', () => {
        const b = stripComments(methodText(WS_CLIENT, '_buildPrintHtml'));
        const iTable = b.indexOf("'</tbody></table>'");
        const iMev = b.indexOf('<div class="wsp-mev">');
        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iTable !== -1 && iMev !== -1 && iLegend !== -1,
            'все секции на месте');
        assertTrue(iFoot === -1, 'сноски wsp-foot нет (Task 438)');"""),
("""        assertTrue(html.indexOf('График работы — табель учёта рабочего времени') !== -1,
            'заголовок листа (Task 341)');
        assertTrue(html.indexOf('<th class="wsp-tot wsp-tot-over">Перераб.<span>дни/ч</span></th>') !== -1,
            'колонка «Перераб.» (Task 342)');
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">1/12</td>') !== -1,
            'значение переработки (Task 342)');
        assertTrue(html.indexOf('wsp-sum') === -1, 'итоговой строки нет (Task 343)');
        var iFoot = html.indexOf('<div class="wsp-foot">');
        var foot = html.slice(iFoot);
        assertTrue(foot.indexOf('«Перераб.» — дни/часы переработки') !== -1,
            'сноска поясняет колонку (Task 342/343)');
        assertTrue(foot.indexOf('мероприятие') !== -1,
            'сноска упоминает значок мероприятия в углу ячейки (Task 361)');
    });""",
"""        assertTrue(html.indexOf('<div class="wsp-title">График работы</div>') !== -1,
            'заголовок листа (Task 341/438)');
        assertTrue(html.indexOf('<th class="wsp-tot wsp-tot-over">Перераб.<span>дни</span></th>') !== -1,
            'колонка «Перераб.» (Task 342/438: дни)');
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">1</td>') !== -1,
            'значение переработки — дни (Task 342/438)');
        assertTrue(html.indexOf('<td class="wsp-tot wsp-tot-over">1/12</td>') === -1,
            'старый формат «1/12» не печатается (Task 438)');
        assertTrue(html.indexOf('wsp-sum') === -1, 'итоговой строки нет (Task 343)');
        assertTrue(html.indexOf('wsp-foot') === -1,
            'сноска удалена (Task 438)');
    });"""),
])

# ============================================================
# test-task361.js — CSS удалённых строк
# ============================================================
patch('tests/test-task361.js', [
("""        assertTrue(ruleOf('#wsPrintSheet .wsp-meta {').indexOf('font-size: 12px') !== -1,
            'норма месяца 12px (была 10px)');
        assertTrue(ruleOf('#wsPrintSheet .wsp-printed {').indexOf('font-size: 11px') !== -1,
            'штамп «Распечатано» 11px (был 9px)');""",
"""        assertTrue(INDEX_SRC.indexOf('#wsPrintSheet .wsp-meta {') === -1,
            'строки нормы нет — правило удалено (Task 438)');
        assertTrue(INDEX_SRC.indexOf('#wsPrintSheet .wsp-printed {') === -1,
            'штампа «Распечатано» нет — правило удалено (Task 438)');"""),
("""        assertTrue(ruleOf('#wsPrintSheet .wsp-foot {').indexOf('font-size: 10px') !== -1,
            'сноска 10px (была 7.5px)');""",
"""        assertTrue(INDEX_SRC.indexOf('#wsPrintSheet .wsp-foot {') === -1,
            'сноска удалена — правило .wsp-foot убрано (Task 438)');"""),
])

# ============================================================
# test-task362.js — заголовок + сноска в регрессе
# ============================================================
patch('tests/test-task362.js', [
("""        assertTrue(html.indexOf('График работы — табель учёта рабочего времени') !== -1,
            'заголовок листа (Task 341)');""",
"""        assertTrue(html.indexOf('<div class="wsp-title">График работы</div>') !== -1,
            'заголовок листа (Task 341/438)');"""),
("""        assertTrue(html.indexOf('wsp-sum') === -1, 'итоговой строки нет (Task 343)');
        assertTrue(html.indexOf('значок в углу ячейки') !== -1,
            'сноска о значках (Task 361)');
    });""",
"""        assertTrue(html.indexOf('wsp-sum') === -1, 'итоговой строки нет (Task 343)');
        assertTrue(html.indexOf('wsp-foot') === -1,
            'сноски нет (Task 438)');
    });"""),
])

# ============================================================
# test-task364.js — обёртка/сноска в SRC и VM
# ============================================================
patch('tests/test-task364.js', [
("""        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom строится');
        assertTrue(iOpen < iMev, 'открытие обёртки до мероприятий');
        // Task 433: секция ВЕРТИКАЛЬНАЯ — список мероприятий
        // ПЕРВЫМ, коды — строкой-абзацем ПОД ним (флоат Task 432
        // строил коды первыми в DOM)
        assertTrue(iMev < iLegend, 'коды — ПОД списком мероприятий (Task 433)');
        assertTrue(iLegend < iFoot, 'сноска — после кодов');
    });""",
"""        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom строится');
        assertTrue(iOpen < iMev, 'открытие обёртки до мероприятий');
        // Task 433: секция ВЕРТИКАЛЬНАЯ — список мероприятий
        // ПЕРВЫМ, коды — строкой-абзацем ПОД ним (флоат Task 432
        // строил коды первыми в DOM)
        assertTrue(iMev < iLegend, 'коды — ПОД списком мероприятий (Task 433)');
        assertTrue(iFoot === -1, 'сноски нет (Task 438)');
    });"""),
("""        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iClose1 !== -1 && iClose2 !== -1,
            'двойное закрытие legend + обёртки');
        assertTrue(iClose1 > iLegend, 'закрытие после перечня кодов');
        assertTrue(iClose2 - iClose1 < 200,
            'операторы закрытия — подряд');
        assertTrue(iClose2 < iFoot, 'сноска строится после закрытия обёртки');
    });""",
"""        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iClose1 !== -1 && iClose2 !== -1,
            'двойное закрытие legend + обёртки');
        assertTrue(iClose1 > iLegend, 'закрытие после перечня кодов');
        assertTrue(iClose2 - iClose1 < 200,
            'операторы закрытия — подряд');
    });"""),
("""        var iClose = html.indexOf('</div></div>', iLegend);
        var iFoot = html.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom в листе');
        // Task 433: секция вертикальная — мероприятия ПЕРВЫМИ,
        // коды — ПОД списком (флоат Task 432 строил коды первыми)
        assertTrue(iOpen < iMev && iMev < iLegend,
            'мероприятия, за ними коды — внутри обёртки (Task 433)');
        assertTrue(iClose !== -1 && iClose > iLegend, 'обёртка закрыта после кодов');
        assertTrue(iFoot > iClose, 'сноска — ПОД обёрткой, на всю ширину');
    });""",
"""        var iClose = html.indexOf('</div></div>', iLegend);
        var iFoot = html.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1, 'обёртка wsp-bottom в листе');
        // Task 433: секция вертикальная — мероприятия ПЕРВЫМИ,
        // коды — ПОД списком (флоат Task 432 строил коды первыми)
        assertTrue(iOpen < iMev && iMev < iLegend,
            'мероприятия, за ними коды — внутри обёртки (Task 433)');
        assertTrue(iClose !== -1 && iClose > iLegend, 'обёртка закрыта после кодов');
        assertTrue(iFoot === -1, 'сноски нет (Task 438)');
    });"""),
])

# ============================================================
# test-task375.js — якорь среза print-CSS (wsp-foot удалён)
# ============================================================
patch('tests/test-task375.js', [
("""    test('«gap: 5mm» больше нигде в печати не встречается', () => {
        // единственное историческое упоминание 5mm — само правило,
        // оно заменено; проверяем полный источник печати
        const z = INDEX_SRC.indexOf('@media print');
        const z2 = INDEX_SRC.indexOf('}', INDEX_SRC.indexOf('#wsPrintSheet .wsp-foot'));
        const printCss = INDEX_SRC.slice(z, z2);
        assertTrue(printCss.indexOf('gap: 5mm') === -1,
            'в print-блоке не осталось зазора 5mm');
    });""",
"""    test('«gap: 5mm» больше нигде в печати не встречается', () => {
        // единственное историческое упоминание 5mm — само правило,
        // оно заменено; проверяем полный print-блок (от @media print
        // до следующей секции CSS — Task 438: якорь .wsp-foot
        // удалён вместе со сноской)
        const z = INDEX_SRC.indexOf('@media print');
        const z2 = INDEX_SRC.indexOf('/* Task 317', z);
        const printCss = INDEX_SRC.slice(z, z2 !== -1 ? z2 : z + 20000);
        assertTrue(printCss.indexOf('gap: 5mm') === -1,
            'в print-блоке не осталось зазора 5mm');
    });"""),
])

# ============================================================
# test-task430.js — кнопки диалога и _savePrintFile
# ============================================================
patch('tests/test-task430.js', [
("""    test('кнопки диалога: Печать / Сохранить в файл / Отмена', () => {
        const i = INDEX_SRC.indexOf("class=\\"wspprev-btn wspprev-print\\"");
        assertTrue(i !== -1, 'кнопка Печать');
        const seg = INDEX_SRC.slice(i, i + 900);
        assertTrue(seg.indexOf('wspprev-save') !== -1, 'кнопка Сохранить в файл');
        assertTrue(seg.indexOf('wspprev-cancel') !== -1, 'кнопка Отмена');
        assertTrue(seg.indexOf('Сохранить в файл') !== -1, 'текст кнопки файла');
    });""",
"""    test('кнопки диалога: Печать / Сохранить PDF / Сохранить Excel / Отмена', () => {
        const i = INDEX_SRC.indexOf("class=\\"wspprev-btn wspprev-print\\"");
        assertTrue(i !== -1, 'кнопка Печать');
        const seg = INDEX_SRC.slice(i, i + 1200);
        assertTrue(seg.indexOf('wspprev-pdf') !== -1, 'кнопка Сохранить PDF (Task 438)');
        assertTrue(seg.indexOf('wspprev-xlsx') !== -1, 'кнопка Сохранить Excel (Task 438)');
        assertTrue(seg.indexOf('wspprev-cancel') !== -1, 'кнопка Отмена');
        assertTrue(seg.indexOf('Сохранить PDF') !== -1, 'текст кнопки PDF');
        assertTrue(seg.indexOf('Сохранить Excel') !== -1, 'текст кнопки Excel');
        assertTrue(seg.indexOf('wspprev-save') === -1,
            'кнопки «Сохранить в файл» (HTML) больше нет (Task 438)');
    });"""),
("""    test('_savePrintFile: имя График_работы_‹Месяц›_‹год›.html', () => {
        const dl = { calls: [] };
        const toasts = [];
        const KipToast = { show: function(m) { toasts.push(m); } };
        const host = new Function('KipToast', 'return ({' +
            methodText(INDEX_SRC, '_savePrintFile') + ',\\n' +
            methodText(INDEX_SRC, '_buildPrintFileHtml') + ',\\n' +
            "_printCssText: function() { return ''; }," +
            '_esc: function(s) { return String(s); },' +
            '_month: 9, _year: 2026,' +
            '});')(KipToast);
        host._wsDownload = function(b, m, n) {
            dl.calls.push({ m: m, n: n });
            return true;
        };
        host._wsXlsBytes = function(s) { return s; };
        host._savePrintFile('SHEET');
        assertEqual(dl.calls.length, 1, 'файл отдан в загрузки');
        assertEqual(dl.calls[0].n, 'График_работы_Сентябрь_2026.html',
            'имя файла графика');
        assertEqual(dl.calls[0].m, 'text/html;charset=utf-8', 'mime html');
        assertEqual(toasts.length, 1, 'тост показан');
        assertTrue(toasts[0].indexOf('График сохранён') !== -1,
            'текст тоста');
    });""",
"""    test('_savePrintFile (HTML) удалён — вместо него PDF/Excel (Task 438)', () => {
        // Заявка Task 438: «сделай возможность сохранения в файл
        // вместо html в PDF и Excel» — HTML-выгрузка удалена
        assertTrue(INDEX_SRC.indexOf('_savePrintFile: function') === -1,
            'метод _savePrintFile удалён из клиента');
        assertTrue(INDEX_SRC.indexOf('График_работы_Сентябрь_2026.html') === -1 &&
                   INDEX_SRC.indexOf("+'_' +\\n                       this._year + '.html'") === -1,
            'HTML-имя файла больше не собирается');
        assertTrue(INDEX_SRC.indexOf('_savePrintPdf: function') !== -1,
            'метод _savePrintPdf определён (PDF)');
        assertTrue(INDEX_SRC.indexOf('_savePrintXlsx: function') !== -1,
            'метод _savePrintXlsx определён (Excel)');
        // полные VM-проверки выгрузок PDF/Excel — tests/test-task438.js
    });"""),
])

# ============================================================
# test-task431.js — сноска под столбиками → сноска удалена
# ============================================================
patch('tests/test-task431.js', [
("""    test('wsp-foot — ПОД обоими столбиками (после закрытия wsp-bottom)', () => {
        const f = INDEX_SRC.indexOf("html += '<div class=\\"wsp-foot\\">");
        assertTrue(f !== -1, 'сноска wsp-foot есть');
        // Task 432: закрытие мероприятий и обёртки — ДВА последовательных
        // оператора (прежде один '</div></div>')
        const close2 = INDEX_SRC.lastIndexOf("html += '</div>';", f);
        const close1 = INDEX_SRC.lastIndexOf("html += '</div>';", close2 - 1);
        assertTrue(close1 !== -1 && close2 !== -1 && close2 - close1 < 200,
            'перед сноской — закрытие mev + обёртки (два оператора)');
        const open = INDEX_SRC.lastIndexOf("html += '<div class=\\"wsp-bottom\\">'", close1);
        assertTrue(open !== -1 && open < close1,
            'обёртка wsp-bottom открывается раньше — сноска ПОД обоими столбиками');
        // внутри обёртки — ОБА столбика: коды (флоат, первым — Task 432) + мероприятия
        const wrap = INDEX_SRC.slice(open, close1);
        assertTrue(wrap.indexOf('wsp-mev') !== -1 && wrap.indexOf('wsp-legend') !== -1,
            'в ряду — столбик мероприятий и столбик кодов');
    });""",
"""    test('wsp-foot удалена; закрытие mev + обёртки — два оператора (Task 438)', () => {
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
    });"""),
])

# ============================================================
# test-task432.js — закрытия без сноски
# ============================================================
patch('tests/test-task432.js', [
("""    test('JS: закрытие кодов и обёртки — два оператора перед сноской', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        const iClose1 = b.indexOf("html += '</div>';", b.indexOf('<div class="wsp-legend">'));
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iFoot !== -1 && iClose1 !== -1 && iClose2 !== -1,
            'закрытия кодов и обёртки строятся');
        assertTrue(iClose2 - iClose1 < 200,
            'два последовательных оператора закрытия (legend + обёртка)');
        assertTrue(iClose2 < iFoot, 'сноска — ПОСЛЕ закрытия обёртки');
    });""",
"""    test('JS: закрытие кодов и обёртки — два оператора (сноски нет)', () => {
        const b = methodText(INDEX_SRC, '_buildPrintHtml');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        const iClose1 = b.indexOf("html += '</div>';", b.indexOf('<div class="wsp-legend">'));
        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
        assertTrue(iClose1 !== -1 && iClose2 !== -1,
            'закрытия кодов и обёртки строятся');
        assertTrue(iClose2 - iClose1 < 200,
            'два последовательных оператора закрытия (legend + обёртка)');
    });"""),
])

# ============================================================
# test-task433.js — секции без сноски
# ============================================================
patch('tests/test-task433.js', [
("""        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1 && iMev !== -1 && iLegend !== -1 && iFoot !== -1,
            'все секции строятся');""",
"""        const iLegend = b.indexOf('<div class="wsp-legend">');
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iOpen !== -1 && iMev !== -1 && iLegend !== -1,
            'все секции строятся');
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');"""),
("""        assertTrue(iClose1 !== -1 && iClose2 !== -1 && iClose3 !== -1 &&
                   iClose2 - iClose1 < 200 && iClose3 - iClose2 < 200,
            'Task 434: закрытия сетки, легенды и обёртки — три последовательных оператора');
        assertTrue(iClose3 < iFoot, 'сноска — после закрытия обёртки');
    });""",
"""        assertTrue(iClose1 !== -1 && iClose2 !== -1 && iClose3 !== -1 &&
                   iClose2 - iClose1 < 200 && iClose3 - iClose2 < 200,
            'Task 434: закрытия сетки, легенды и обёртки — три последовательных оператора');
    });"""),
])

# ============================================================
# test-task434.js — сетка кодов без сноски
# ============================================================
patch('tests/test-task434.js', [
("""        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        const iClose3 = b.indexOf("html += '</div>';", iClose2 + 1);
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iClose1 !== -1 && iClose2 !== -1 && iClose3 !== -1 &&
                   iClose2 - iClose1 < 200 && iClose3 - iClose2 < 200,
            'закрытия сетки, легенды и обёртки — три последовательных оператора');
        assertTrue(iClose3 < iFoot, 'сноска — после закрытия обёртки');
    });""",
"""        const iClose2 = b.indexOf("html += '</div>';", iClose1 + 1);
        const iClose3 = b.indexOf("html += '</div>';", iClose2 + 1);
        const iFoot = b.indexOf('<div class="wsp-foot">');
        assertTrue(iClose1 !== -1 && iClose2 !== -1 && iClose3 !== -1 &&
                   iClose2 - iClose1 < 200 && iClose3 - iClose2 < 200,
            'закрытия сетки, легенды и обёртки — три последовательных оператора');
        assertTrue(iFoot === -1, 'сноска wsp-foot удалена (Task 438)');
    });"""),
])

print('OK: все 13 файлов адаптированы')
