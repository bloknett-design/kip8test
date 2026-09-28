#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 439: адаптация исторических тестов под новую печатную
# форму (колонка «ФИО + Тип», коды справа от мероприятий) и
# дедупликацию легаси-«.» в попапе + зачистка stale-комментариев
# index.html (упоминания _posLabel как живого метода).
import io

def patch(path, pairs):
    src = io.open(path, encoding='utf-8').read()
    applied = 0
    for old, new in pairs:
        cnt = src.count(old)
        if cnt == 0:
            # уже применено ранее (идемпотентность повторного запуска)
            assert src.count(new) >= 1, \
                '%s: не найден фрагмент (и замена отсутствует):\n---\n%s\n---' % (path, old[:120])
            print('  SKIP (уже применено): %s' % old.strip().splitlines()[0][:70])
            continue
        src = src.replace(old, new)
        applied += 1
    io.open(path, 'w', encoding='utf-8').write(src)
    print('OK: %s (%d замен)' % (path, applied))

# ============================================================
# index.html — stale-комментарии про _posLabel (метод удалён)
# ============================================================
patch('index.html', [
    ("""                // (см. _empPosLine/_empTipLine; прежний склеенный формат
                // «Слесарь КИПиА смена №1» остаётся в печатной форме —
                // _posLabel, Task 361). Пустая строка — блок не
                // рендерится вовсе (без пустых строк в колонке).""",
     """                // (см. _empPosLine/_empTipLine; Task 439: печатная
                // форма тоже показывает только Тип — _empTipLine).
                // Пустая строка — блок не
                // рендерится вовсе (без пустых строк в колонке)."""),
    ("""        // Группа допуска из столбца ФИО УБРАНА по заявке (данные
        // остаются в карточке, сводной «Общая» и шторке правки).
        // Карточка/сводная/печать — полная должность без сокращения
        // (_posLabel печатной формы прежний, Task 361).""",
     """        // Группа допуска из столбца ФИО УБРАНА по заявке (данные
        // остаются в карточке, сводной «Общая» и шторке правки).
        // Карточка/сводная — полная должность без сокращения
        // (печать с Task 439 должность не показывает — только Тип)."""),
])

# ============================================================
# test-work-schedule.js — _posLabel удалён, печать на _empTipLine
# ============================================================
patch('tests/test-work-schedule.js', [
    ("""        test('JS: _posLabel — должность + тип (столбец C) + смена №N (столбец D)', () => {
            // Данные таблицы «Сотрудники» файла табель_КИП_ИОС: столбец C —
            // тип (сменный/дневной), столбец D — номер смены. Формирование:
            // «Слесарь КИПиА смена №1» / «Слесарь КИПиА дневной».
            const re = /_posLabel: function\\(emp\\) \\{[\\s\\S]*?if \\(tip === 'сменный'\\) \\{[\\s\\S]*?' смена №' \\+ smena[\\s\\S]*?\\} else if \\(tip === 'дневной'\\) \\{[\\s\\S]*?' дневной';[\\s\\S]*?\\}/;
            assertTrue(re.test(html),
                'Хелпер _posLabel формирует «… смена №N» / «… дневной»');
            const reRange = /smena >= 1 && smena <= 5/;
            assertTrue(reRange.test(html),
                'Смена выводится только при корректном номере 1..5');
        });""",
     """        test('JS: _empTipLine — Тип (смена №N/сменный/дневной); _posLabel удалён (Task 439)', () => {
            // Task 439: печатная форма показывает под ФИО только Тип
            // (_empTipLine); склеенная подпись «должность + тип»
            // (_posLabel) удалена — потребителей не осталось.
            const re = /_empTipLine: function\\(emp\\) \\{[\\s\\S]*?if \\(tip === 'сменный'\\) \\{[\\s\\S]*?\\? 'смена №' \\+ smena : 'сменный';[\\s\\S]*?if \\(tip === 'дневной'\\) return 'дневной';[\\s\\S]*?return '';/;
            assertTrue(re.test(html),
                'Хелпер _empTipLine формирует «смена №N» / «сменный» / «дневной»');
            const reRange = /smena >= 1 && smena <= 5/;
            assertTrue(reRange.test(html),
                'Смена выводится только при корректном номере 1..5');
            assertFalse(html.indexOf('_posLabel: function') !== -1,
                'склеенная подпись _posLabel удалена (Task 439 — печать: только ФИО и Тип)');
        });"""),
])

# ============================================================
# test-task341.js — хост-мок + ассерты строки работника
# ============================================================
patch('tests/test-task341.js', [
    ("""            '_posLabel: function() { return "Слесарь КИПиА, смена 1"; },' +""",
     """            '_empTipLine: function() { return "смена №1"; },' +"""),
    ("""        assertTrue(html.indexOf('Иванов Иван Иванович') !== -1, 'ФИО сотрудника');
        assertTrue(html.indexOf('Слесарь КИПиА, смена 1') !== -1, 'должность под ФИО');""",
     """        assertTrue(html.indexOf('Иванов Иван Иванович') !== -1, 'ФИО сотрудника');
        assertTrue(html.indexOf('смена №1') !== -1,
            'Тип под ФИО (Task 439: только ФИО и Тип)');
        assertTrue(html.indexOf('Слесарь КИПиА') === -1,
            'должности в колонке больше нет (Task 439)');"""),
])

# ============================================================
# test-task342.js — хост-мок
# ============================================================
patch('tests/test-task342.js', [
    ("""            '_posLabel: function() { return "Слесарь КИПиА, смена 1"; },' +""",
     """            '_empTipLine: function() { return "смена №1"; },' +"""),
])

# ============================================================
# test-task343.js — хост-мок
# ============================================================
patch('tests/test-task343.js', [
    ("""            '_posLabel: function() { return "Слесарь КИПиА, смена 1"; },' +""",
     """            '_empTipLine: function() { return "смена №1"; },' +"""),
])

# ============================================================
# test-task360.js — хост-моки ×3+1 (replace-all) + окно printCss
# ============================================================
patch('tests/test-task360.js', [
    ("""        return stripComments(INDEX_SRC.slice(i, i + 13000));""",
     """        // Task 439 удлинил блок (flex-ряд + комментарии) — окно 16000
        return stripComments(INDEX_SRC.slice(i, i + 16000));"""),
    # три одинаковых мока «Слесарь КИПиА» (хосты L281/L447/L578)
    ("""            '_posLabel: function() { return "Слесарь КИПиА"; },' +""",
     """            '_empTipLine: function() { return "смена №1"; },' +"""),
    ("""            '_posLabel: function() { return ""; },' +""",
     """            '_empTipLine: function() { return ""; },' +"""),
])

# ============================================================
# test-task361.js — SRC-ассерты (кламп/Тип) + VM-хосты и ширины
# ============================================================
patch('tests/test-task361.js', [
    ("""        assertTrue(b.indexOf('empWmm < 24') !== -1 && b.indexOf('empWmm > 48') !== -1,
            'кламп 24–48mm');""",
     """        assertTrue(b.indexOf('empWmm < 12') !== -1 && b.indexOf('empWmm > 48') !== -1,
            'кламп 12–48mm (Task 439: мин снижен — колонка уже');"""),
    ("""        assertTrue(b.indexOf('_posLabel(viewEmps[wi])') !== -1,
            'должность сотрудника');""",
     """        assertTrue(b.indexOf('_empTipLine(viewEmps[wi])') !== -1,
            'Тип сотрудника (Task 439: должность из колонки убрана)');"""),
    ("""    test('SRC: измеряются ФИО и должность печатаемых строк', () => {""",
     """    test('SRC: измеряются ФИО и Тип печатаемых строк (Task 439)', () => {"""),
    ("""            '_posLabel: function() { return "Слесарь КИПиА"; },' +
            '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
            '_STATUS_CODES: ' + JSON.stringify(opts.codes || [""",
     """            '_empTipLine: function() { return "смена №1"; },' +
            '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
            '_STATUS_CODES: ' + JSON.stringify(opts.codes || ["""),
    ("""    test('VM: inline ширина на th .wsp-emp в клампе 24–48 (фолбэк-оценка)', () => {""",
     """    test('VM: inline ширина на th .wsp-emp в клампе 12–48 (Task 439)', () => {"""),
    ("""        assertTrue(w >= 24 && w <= 48, 'в клампе 24–48mm: ' + w);""",
     """        assertTrue(w >= 12 && w <= 48, 'в клампе 12–48mm: ' + w);"""),
    ("""    test('VM: короткие ФИО — минимум 24mm', () => {
        var html = sheetHost()._buildPrintHtml(
            [{ 'ФИО': 'А', 'таб_номер': '001' }], { byTab: {}, grand: null });
        assertEqual(empWidth(html), 24, 'кламп-минимум 24mm');
    });""",
     """    test('VM: короткие ФИО — ширина по заголовку «Работник» (Task 439)', () => {
        var html = sheetHost()._buildPrintHtml(
            [{ 'ФИО': 'А', 'таб_номер': '001' }], { byTab: {}, grand: null });
        // «Работник» 8 симв × 11 × 0.62 = 54.6px = 14.4mm + 3.5 =
        // 17.95 → шаг 0.5mm вверх = 18mm; Тип «смена №1» короче
        assertEqual(empWidth(html), 18, 'по заголовку «Работник» — 18mm');
    });"""),
    ("""    test('VM: самая длинная строка побеждает (ФИО против должности)', () => {
        var html = sheetHost()._buildPrintHtml(
            [{ 'ФИО': 'А', 'таб_номер': '001' }], { byTab: {}, grand: null });
        // должность-мок «Слесарь КИПиА» (13 симв × 8.5 × 0.62 =
        // 68.5px = 18.1mm + 3.5 = 21.6) — меньше минимума 24
        assertEqual(empWidth(html), 24, 'ФИО «А» + короткая должность → 24mm');
    });""",
     """    test('VM: самая длинная строка побеждает (заголовок против Типа)', () => {
        var html = sheetHost()._buildPrintHtml(
            [{ 'ФИО': 'А', 'таб_номер': '001' }], { byTab: {}, grand: null });
        // Тип-мок «смена №1» (8 симв × 8.5 × 0.62 = 42.2px =
        // 11.2mm) — короче заголовка «Работник» (14.4mm)
        assertEqual(empWidth(html), 18, 'ФИО «А» + короткий Тип → 18mm');
    });"""),
    ("""            '_posLabel: function() { return "Слесарь КИПиА"; },' +
            '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
            '_STATUS_CODES: [{ code: "Д", name: "День (12-час)", color: "#FFE082" }],'""",
     """            '_empTipLine: function() { return "смена №1"; },' +
            '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
            '_STATUS_CODES: [{ code: "Д", name: "День (12-час)", color: "#FFE082" }],'"""),
])

# ============================================================
# test-task362.js — хост-мок
# ============================================================
patch('tests/test-task362.js', [
    ("""        '_posLabel: function() { return "Слесарь КИПиА"; },' +""",
     """        '_empTipLine: function() { return "смена №1"; },' +"""),
])

# ============================================================
# test-task364.js — SRC-ассерты (ряд вместо вертикали) + мок
# ============================================================
patch('tests/test-task364.js', [
    ("""    test('SRC: CSS .wsp-bottom — обёртка вертикальной секции (Task 433)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-bottom');
        assertTrue(r !== '', 'правило обёртки есть');
        // Task 433 (заявка: «расположение кодов в печати верни
        // обратно…»): флоат Task 432 и flex-ряд Task 364–431
        // СНЯТЫ — нижняя секция ВЕРТИКАЛЬНАЯ: список мероприятий
        // на всю ширину, коды — строкой-абзацем ПОД ним
        assertTrue(r.indexOf('display: flex') === -1,
            'flex-ряда нет (Task 433: вертикальная секция)');
        assertTrue(r.indexOf('flow-root') === -1,
            'флоат-обёртки Task 432 больше нет');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы перенесён на обёртку');
    });""",
     """    test('SRC: CSS .wsp-bottom — РЯД: мероприятия слева, коды справа (Task 439)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-bottom');
        assertTrue(r !== '', 'правило обёртки есть');
        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): нижняя секция — ГИБКИЙ РЯД (флоат Task 432
        // не вернулся): список мероприятий слева, коды справа
        assertTrue(r.indexOf('display: flex') !== -1,
            'обёртка — flex-ряд (Task 439)');
        assertTrue(r.indexOf('align-items: flex-start') !== -1,
            'блоки выровнены по верхней линии');
        assertTrue(r.indexOf('gap: 6mm') !== -1, 'зазор между блоками');
        assertTrue(r.indexOf('flow-root') === -1,
            'флоат-обёртки Task 432 не вернулась');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы на обёртке жив');
    });"""),
    ("""    test('SRC: CSS .wsp-mev — строки на всю ширину листа (Task 432)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        // Task 432: flex снят — блок мероприятий на всю ширину, строки
        // ТЕКУТ вокруг плавающих кодов (рядом — до кромки кодов минус
        // 10px, ниже — до конца листа), переносятся ТОЛЬКО когда
        // места не хватает (прежде 0 1 auto Task 431 сжимал колонку
        // по тексту — правая часть листа пустовала)
        assertTrue(r.indexOf('flex:') === -1,
            'мероприятия НЕ в flex-колонке (Task 432: обтекание)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'личный отступ сверху снят (отступ — на обёртке)');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });""",
     """    test('SRC: CSS .wsp-mev — ЛЕВАЯ часть ряда (растягивается, Task 439)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-mev');
        // Task 439: мероприятия — левая часть flex-ряда обёртки,
        // растягиваются на остаток ширины (коды — справа)
        assertTrue(r.indexOf('flex: 1 1 auto') !== -1,
            'блок мероприятий растягивается (левая часть ряда)');
        assertTrue(r.indexOf('min-width: 0') !== -1,
            'усадка для переносов текста');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'личный отступ сверху снят (отступ — на обёртке)');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });"""),
    ("""    test('SRC: CSS .wsp-legend — строка-абзац ПОД списком (Task 433)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        // Task 433 (заявка: «расположение кодов в печати верни
        // обратно»): ВЕРНУЛИ исходную форму «в одну строку» —
        // флоат и max-width сняты, блок — обычный абзац ПОД
        // списком мероприятий, растянутый до конца листа
        assertTrue(r.indexOf('float:') === -1,
            'флоат Task 432 снят (коды — не плавающий столбик)');
        assertTrue(r.indexOf('max-width') === -1,
            'кап ширины Task 364 снят');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от списка мероприятий сверху');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });""",
     """    test('SRC: CSS .wsp-legend — ПРАВЫЙ блок ряда (Task 439)', () => {
        const r = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        // Task 439: коды — ПРАВАЯ часть flex-ряда (справа от
        // мероприятий), фиксированная ширина блока
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'блок кодов — фикс. ширина 92mm справа (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'верхняя линия общая с мероприятиями');
        assertTrue(r.indexOf('float:') === -1,
            'флоат Task 432 не вернулся');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) сохранён');
    });"""),
    ("""        '_posLabel: function() { return "Слесарь КИПиА"; },' +""",
     """        '_empTipLine: function() { return "смена №1"; },' +"""),
])

# ============================================================
# test-task375.js — отступ легенды (теперь правый блок)
# ============================================================
patch('tests/test-task375.js', [
    ("""        const leg = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        assertTrue(leg.indexOf('float:') === -1,
            'коды — не плавающий столбик (Task 433: строка под списком)');
        assertTrue(leg.indexOf('margin-top: 2.5mm') !== -1,
            'отступ строки кодов от списка мероприятий');""",
     """        const leg = cssRule(INDEX_SRC, '#wsPrintSheet .wsp-legend');
        assertTrue(leg.indexOf('float:') === -1,
            'коды — не плавающий столбик (Task 439: правый блок ряда)');
        assertTrue(leg.indexOf('margin-top: 0') !== -1,
            'отступ строки кодов снят (Task 439: общая верхняя линия с мероприятиями)');"""),
])

# ============================================================
# test-task402.js — печать перешла на _empTipLine
# ============================================================
patch('tests/test-task402.js', [
    ("""    test('печать НЕ меняется: _posLabel остаётся у _buildPrintHtml', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        assertTrue(fn.indexOf('this._posLabel(') !== -1,
            'печатная форма — прежний склеенный формат (Task 361)');
        const grid = stripComments(methodText(INDEX_SRC, '_renderGrid'));
        assertTrue(grid.indexOf('this._posLabel(') === -1,
            'сетка _posLabel больше не использует (только _empPosLine/_empTipLine)');
    });""",
     """    test('печать использует Тип (Task 439): _empTipLine, _posLabel удалён', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        assertTrue(fn.indexOf('this._empTipLine(') !== -1,
            'печатная форма — Тип под ФИО (Task 439: «только ФИО и Тип»)');
        const grid = stripComments(methodText(INDEX_SRC, '_renderGrid'));
        assertTrue(grid.indexOf('this._posLabel(') === -1,
            'сетка _posLabel не использует (только _empPosLine/_empTipLine)');
        assertFalse(INDEX_SRC.indexOf('_posLabel: function') !== -1,
            'метод _posLabel удалён (Task 439 — потребителей не осталось)');
    });"""),
])

# ============================================================
# test-task403.js — _posLabel удалён, _shortGrade жив у _empPosLine
# ============================================================
patch('tests/test-task403.js', [
    ("""    test('печать НЕ меняется: _posLabel — полный текст должности', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_posLabel'));
        assertTrue(fn.indexOf('_shortGrade') === -1,
            'печатная форма — без сокращения «разряд»');
    });""",
     """    test('печать НЕ показывает должность (Task 439); «разряд» — только в сетке', () => {
        // Task 439: _posLabel удалён — печать показывает только
        // ФИО и Тип; сокращение «разряд» (_shortGrade) живёт
        // только в _empPosLine ячейки сетки
        assertFalse(INDEX_SRC.indexOf('_posLabel: function') !== -1,
            'метод _posLabel удалён (Task 439)');
        const fn = stripComments(methodText(INDEX_SRC, '_empPosLine'));
        assertTrue(fn.indexOf('_shortGrade') !== -1,
            'строка должности сетки — с сокращением «разряд»');
        const b = stripComments(methodText(INDEX_SRC, '_buildPrintHtml'));
        assertTrue(b.indexOf('_shortGrade') === -1 && b.indexOf('должность') === -1,
            'печать должность не читает (только _empTipLine)');
    });"""),
])

# ============================================================
# test-task431.js — .wsp-mev/.wsp-legend в ряду (Task 439)
# ============================================================
patch('tests/test-task431.js', [
    ("""    test('.wsp-mev: без flex — строки на всю ширину листа', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-mev {');
        assertTrue(i !== -1, 'правило .wsp-mev есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        // Task 432 (заявка: «строки столбика мероприятий должны
        // растягиваться вправо до конца листа»): flex снят ВЕСЬ — блок
        // на всю ширину, строки ТЕКУТ вокруг плавающих кодов и ниже
        // их растягиваются до конца листа (прежде 0 1 auto сжимал
        // колонку по тексту — правая часть листа пустовала)
        assertTrue(r.indexOf('flex:') === -1,
            'flex снят — обтекание кодов (Task 432)');
        assertFalse(r.indexOf('flex: 1 1 auto') !== -1,
            'прежний flex 1 1 auto (растяжение, коды у правого края) снят');
    });""",
     """    test('.wsp-mev: ЛЕВАЯ часть ряда — flex 1 1 auto (Task 439)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-mev {');
        assertTrue(i !== -1, 'правило .wsp-mev есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): мероприятия — растягиваемая ЛЕВАЯ часть
        // flex-ряда (правая — блок кодов 92mm); возвращённый
        // flex 1 1 auto (как в Task 364–431) снова уместен
        assertTrue(r.indexOf('flex: 1 1 auto') !== -1,
            'растяжение мероприятий на остаток ширины (Task 439)');
    });"""),
    ("""    test('.wsp-legend: коды — строка-абзац ПОД списком (Task 433)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-legend {');
        assertTrue(i !== -1, 'правило кодов есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        // Task 433 (заявка: «расположение кодов в печати верни
        // обратно»): флоат Task 432 и зазор 10px Task 431/375 СНЯТЫ —
        // коды вернулись исходной строкой-абзацем ПОД списком
        assertTrue(r.indexOf('float:') === -1,
            'флоат снят (коды — не плавающий столбик)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,""",
     """    test('.wsp-legend: коды — ПРАВЫЙ блок ряда (Task 439)', () => {
        const i = INDEX_SRC.indexOf('#wsPrintSheet .wsp-legend {');
        assertTrue(i !== -1, 'правило кодов есть');
        const r = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): коды — ПРАВАЯ часть flex-ряда фикс. ширины
        assertTrue(r.indexOf('float:') === -1,
            'флоат не вернулся (коды — не плавающий столбик)');
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'фиксированная ширина блока кодов (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,"""),
])

# ============================================================
# test-task432.js — ряд Task 439 вместо блочного потока
# ============================================================
patch('tests/test-task432.js', [
    ("""    test('.wsp-bottom — обычный блочный поток (Task 433)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r !== '', 'правило обёртки есть');
        // Task 433 (заявка: «расположение кодов в печати верни
        // обратно…»): флоат Task 432 СНЯТ — секция вертикальная
        assertTrue(r.indexOf('display: flow-root') === -1,
            'флоат-обёртка Task 432 снята');
        assertFalse(r.indexOf('display: flex') !== -1,
            'flex-ряда Task 364–431 нет');
        assertFalse(r.indexOf('gap:') !== -1,
            'gap снят (столбиков рядом больше нет)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,""",
     """    test('.wsp-bottom — flex-ряд: коды справа от мероприятий (Task 439)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r !== '', 'правило обёртки есть');
        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): секция — ГИБКИЙ РЯД (флоат Task 432 не
        // вернулся): мероприятия слева, коды справа, зазор 6mm
        assertTrue(r.indexOf('display: flow-root') === -1,
            'флоат-обёртка Task 432 не вернулась');
        assertTrue(r.indexOf('display: flex') !== -1,
            'обёртка — flex-ряд (Task 439)');
        assertTrue(r.indexOf('gap: 6mm') !== -1,
            'зазор между блоками ряда (Task 439)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,"""),
    ("""    test('.wsp-mev — БЕЗ flex-колонки: записи на всю ширину листа', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-mev {');
        assertTrue(r !== '', 'правило мероприятий есть');
        assertFalse(r.indexOf('flex:') !== -1,
            'flex-колонка снята (Task 432), секция — на всю ширину листа');
        assertFalse(r.indexOf('min-width: 0') !== -1,
            'min-width снят (был нужен flex-усадке Task 431)');
    });""",
     """    test('.wsp-mev — ЛЕВАЯ часть ряда (flex 1 1 auto, Task 439)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-mev {');
        assertTrue(r !== '', 'правило мероприятий есть');
        assertTrue(r.indexOf('flex: 1 1 auto') !== -1,
            'мероприятия растягиваются на остаток ряда (Task 439)');
        assertTrue(r.indexOf('min-width: 0') !== -1,
            'min-width — усадка для переносов текста (Task 439)');
    });"""),
])

# ============================================================
# test-task433.js — блочный поток → ряд (Task 439)
# ============================================================
patch('tests/test-task433.js', [
    ("""    test('.wsp-bottom — блочный поток: флоат и flex сняты', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r !== '', 'правило обёртки есть');
        assertTrue(r.indexOf('display:') === -1,
            'обёртка — обычный блочный поток (Task 433)');
        assertTrue(r.indexOf('flow-root') === -1,
            'флоат-обёртка Task 432 снята');
        assertTrue(r.indexOf('flex') === -1,
            'flex-ряда Task 364–431 нет');
        assertTrue(r.indexOf('gap') === -1,
            'gap снят — столбиков рядом больше нет');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы (Task 364) жив');
    });""",
     """    test('.wsp-bottom — РЯД: мероприятия слева, коды справа (Task 439)', () => {
        const r = ruleBlock('#wsPrintSheet .wsp-bottom {');
        assertTrue(r !== '', 'правило обёртки есть');
        // Task 439 (заявка: «блок с кодами размести справа от
        // мероприятий»): вертикальная секция Task 433 снова стала
        // РЯДОМ (flex; флоат Task 432 не вернулся)
        assertTrue(r.indexOf('display: flex') !== -1,
            'обёртка — flex-ряд (Task 439)');
        assertTrue(r.indexOf('flow-root') === -1,
            'флоат-обёртка Task 432 не вернулась');
        assertTrue(r.indexOf('gap: 6mm') !== -1,
            'зазор между мероприятиями и кодами (Task 439)');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от таблицы (Task 364) жив');
    });"""),
])

# ============================================================
# test-task434.js — легенда: правый блок ряда (Task 439)
# ============================================================
patch('tests/test-task434.js', [
    ("""        assertTrue(r.indexOf('float') === -1,
            'флоат Task 432 не вернулся');
        assertTrue(r.indexOf('max-width') === -1,
            'кап ширины Task 364 не вернулся');
        assertTrue(r.indexOf('margin-top: 2.5mm') !== -1,
            'отступ от списка мероприятий (Task 433) жив');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) жив');""",
     """        assertTrue(r.indexOf('float') === -1,
            'флоат Task 432 не вернулся');
        assertTrue(r.indexOf('max-width') === -1,
            'кап ширины Task 364 не вернулся');
        // Task 439: коды — ПРАВЫЙ блок ряда (справа от
        // мероприятий), верхняя линия общая — отступа сверху нет
        assertTrue(r.indexOf('flex: 0 0 92mm') !== -1,
            'фиксированная ширина блока кодов (Task 439)');
        assertTrue(r.indexOf('margin-top: 0') !== -1,
            'верхняя линия общая с мероприятиями (Task 439)');
        assertTrue(r.indexOf('font-size: 11px') !== -1,
            'шрифт Task 361 (11px) жив');"""),
])

# ============================================================
# test-task438.js — хост-моки на _empTipLine + поля модели
# ============================================================
patch('tests/test-task438.js', [
    ("""            '_posLabel: function() { return "Слесарь КИПиА, смена 1"; },' +
            '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
            '_STATUS_CODES: ' + JSON.stringify(opts.codes || [
                { code: 'Д', short: 'день 12ч', name: 'День, плановая 12-часовая смена', color: '#FFE082' },""",
     """            '_empTipLine: function() { return "смена №1"; },' +
            '_fmtTotalsNum: function(v) { return String(Math.round((v || 0) * 10) / 10).replace(".", ","); },' +
            '_STATUS_CODES: ' + JSON.stringify(opts.codes || [
                { code: 'Д', short: 'день 12ч', name: 'День, плановая 12-часовая смена', color: '#FFE082' },"""),
    ("""            '_posLabel: function() { return "Слесарь КИПиА, смена 1"; },' +""",
     """            '_empTipLine: function() { return "смена №1"; },' +"""),
    ("""            rows.push({ fio: 'Работник №' + (r + 1), pos: '', tab: String(r),
                        cells: [], inAgg: true, work: 21, overDays: 0 });""",
     """            rows.push({ fio: 'Работник №' + (r + 1), tip: '', tab: String(r),
                        cells: [], inAgg: true, work: 21, overDays: 0 });"""),
    ("""            '             rows: [{ fio: "Иванов И. И.", pos: "", tab: "017",' +""",
     """            '             rows: [{ fio: "Иванов И. И.", tip: "", tab: "017",' +"""),
])

print('\nВсе адаптации применены')
