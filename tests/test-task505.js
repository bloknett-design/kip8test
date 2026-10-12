// tests/test-task505.js
// Task 505 — заявка пользователя:
//   «В разделе "Кабельный журнал" добавь кнопку печати, компактную
//    со значком принтера, и с диалоговым окном предпросмотра и
//    сохранения в PDF или Excel, по примеру как в разделе "Табель
//    учёта рабочего времени".»
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   SRC/HTML: кнопка #cjPrintBtn (cj-print-btn-inline) в шапке
//     страницы #page-cable-journal-edit — между иконкой поиска и «+»,
//     значок-принтер (SVG-путь кнопки «Печать» табеля), onclick
//     KipCableJournal.printJournal(); БЕЗ hidden — печать доступна
//     всем, кто видит раздел (чтение — всем авторизованным).
//   CSS: .cj-print-btn-inline 32×32 (right: 88px; при скрытой «+» —
//     48px, правило :not(:has(...))), светлые/тёмные темы, hover;
//     заголовок — padding-right 128px под три кнопки; fitToTitle
//     учитывает .cj-print-btn-inline (поле поиска не наезжает).
//   SRC/JS: полный набор методов печати (модель/HTML/диалог/PDF/
//     Excel/инжект-стиль), _CJ_PRINT_CSS скоуп #wsPrintSheet.cj-sheet.
//   VM (модель из 3 строк двух отделений — данные как в cables.json):
//     группировка по «Отделение, производство» (алфавит, сквозная
//     нумерация «№ п/п», 43,5 → «43,5»), подзаголовок «записей: N
//     [из K]» (фильтр), печатный HTML (двухуровневая шапка rowspan 2 /
//     colspan 3 «По проекту»/«Проложен», строки отделений colspan 12,
//     зебра cjpr-odd/even, экранирование), standalone-документ
//     (A4 landscape, 281мм), раскладка PDF (842×595, 786pt колонок,
//     пагинация: шапка таблицы на каждой странице, подзаголовок
//     отделения не последний на странице), книга Excel (заголовок,
//     шапка с «(по проекту)»/«(проложен)», числа длин — ЧИСЛАМИ, zip
//     PK-магия, имя файла с датой).
//   VM (мок-DOM): printJournal — пустой журнал → тост без листа;
//     с данными → лист #wsPrintSheet.cj-sheet + диалог wspprev-*
//     (iframe srcdoc standalone, кнопки Печать/PDF/Excel/Отмена +
//     «A4 · альбомная»), Esc закрывает (с инжект-стилем), диалоги
//     взаимоисключающие (закрывает предпросмотры табеля), фолбэк —
//     печать сразу при закрытии диалога.
//   SW: kipia-test-v728 (двойного бампа нет — v729).
//
// Запуск: через tests/run-all.js (require './test-task505.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

// Вырезка метода: «имя: function» (отступ 8 пробелов) → следующий
// метод ТОГО ЖЕ уровня (приём test-task380.js / test-task504.js).
// ХВОСТОВЫЕ СТРОКИ КОММЕНТАРИЕЙ СЛЕДУЮЩЕГО метода СРЕЗАЮТСЯ —
// вырезка всегда оканчивается на «},» самого метода: склейка
// «A},\n B: function» без двойного разделителя и без проглатывания
// «});» комментарием (урок этой сессии).
function methodText(src, name) {
    const sig = '\n        ' + name + ': function';
    const i = src.indexOf(sig);
    if (i === -1) return '';
    const rest = src.slice(i + 1);
    const m = rest.match(/\n        [a-zA-Z_]+: function|\n    \};/);
    const end = m ? m.index : rest.length;
    return rest.slice(0, end).replace(/(\n[ \t]*\/\/[^\n]*)+[ \t]*$/, '');
}

const CJ_START = INDEX_SRC.indexOf('const KipCableJournal = {');
const CJ_END = INDEX_SRC.indexOf('FlowmeterData — Расходомеры хозрасчётные');
const CJ_SRC = INDEX_SRC.slice(CJ_START, CJ_END > CJ_START ? CJ_END : undefined);
const WS_SRC = INDEX_SRC.slice(INDEX_SRC.indexOf('var WorkSchedule = {'));

// ============================================================
// 1. SRC: кнопка печати в шапке раздела
// ============================================================
describe('Task 505 — SRC: кнопка печати (компактная, значок принтера)', () => {

    test('кнопка #cjPrintBtn в шапке page-cable-journal-edit', () => {
        const pageStart = INDEX_SRC.indexOf('id="page-cable-journal-edit"');
        const pageEnd = INDEX_SRC.indexOf('id="cjList"', pageStart);
        const header = INDEX_SRC.slice(pageStart, pageEnd);
        assertTrue(pageStart !== -1 && pageEnd > pageStart, 'страница найдена');
        assertTrue(header.indexOf('id="cjPrintBtn"') !== -1,
            'кнопка печати в шапке страницы');
        assertTrue(header.indexOf('class="cj-print-btn-inline"') !== -1,
            'класс cj-print-btn-inline');
        assertTrue(header.indexOf('KipCableJournal.printJournal()') !== -1,
            'onclick → KipCableJournal.printJournal()');
    });

    test('кнопка БЕЗ hidden — печать доступна всем уровням чтения', () => {
        const pageStart = INDEX_SRC.indexOf('id="page-cable-journal-edit"');
        const btnStart = INDEX_SRC.indexOf('id="cjPrintBtn"', pageStart);
        const btnTag = INDEX_SRC.slice(btnStart - 200, btnStart + 60);
        assertTrue(btnTag.indexOf('hidden') === -1,
            'кнопка не скрыта (в отличие от «+», который правится по canEdit)');
    });

    test('значок — принтер (SVG-путь кнопки «Печать» табеля)', () => {
        const pageStart = INDEX_SRC.indexOf('id="page-cable-journal-edit"');
        const btnStart = INDEX_SRC.indexOf('id="cjPrintBtn"', pageStart);
        const btn = INDEX_SRC.slice(btnStart, btnStart + 700);
        // тот же d, что у #wsPrintBtn табеля (Task 341)
        const wsBtn = INDEX_SRC.indexOf('id="wsPrintBtn"');
        const wsBtnTxt = INDEX_SRC.slice(wsBtn, wsBtn + 900);
        const dRe = /<path d="([^"]+)"/;
        const cjD = (btn.match(dRe) || [])[1];
        const wsD = (wsBtnTxt.match(dRe) || [])[1];
        assertTrue(!!cjD && !!wsD, 'SVG-пути найдены');
        assertEqual(cjD, wsD, 'иконка принтера — та же, что у табеля');
        assertTrue(btn.indexOf('aria-label="Печать журнала"') !== -1,
            'aria-label для доступности');
    });

    test('расположение: между иконкой поиска и «+»', () => {
        const pageStart = INDEX_SRC.indexOf('id="page-cable-journal-edit"');
        const pageEnd = INDEX_SRC.indexOf('id="cjList"', pageStart);
        const header = INDEX_SRC.slice(pageStart, pageEnd);
        const iSearch = header.indexOf('id="cjSearchToggleBtn"');
        const iPrint = header.indexOf('id="cjPrintBtn"');
        const iAdd = header.indexOf('id="cjAddBtn"');
        assertTrue(iSearch !== -1 && iPrint !== -1 && iAdd !== -1,
            'все три кнопки в шапке');
        assertTrue(iSearch < iPrint && iPrint < iAdd,
            'DOM-порядок: поиск → печать → «+»');
    });
});

// ============================================================
// 2. CSS: стиль кнопки + шапка + fitToTitle
// ============================================================
describe('Task 505 — CSS: компактная cj-print-btn-inline', () => {

    test('кнопка 32×32, right 88px (между поиском 48 и «+» 8)', () => {
        const i = INDEX_SRC.indexOf('.cj-print-btn-inline {');
        const rule = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i));
        assertTrue(i !== -1, 'правило найдено');
        assertTrue(/width:\s*32px/.test(rule) && /height:\s*32px/.test(rule),
            'компактная квадратная 32×32');
        assertTrue(/right:\s*88px/.test(rule),
            'позиция 88px — слева от поиска (48), «+» на 8');
    });

    test('«+» скрыта (роль без права записи) — печать на 48px', () => {
        const re = /#page-cable-journal-edit \.page-inline-header:not\(:has\(\.cj-add-btn-inline:not\(\[style\*="display:none"\]\)\)\) \.cj-print-btn-inline \{\s*right:\s*48px;/;
        assertTrue(re.test(INDEX_SRC),
            'печать встаёт на место поиска, поиск прижимается к краю (Task 153)');
    });

    test('светлая тема + hover + active', () => {
        assertTrue(/\[data-theme="light"\] \.cj-print-btn-inline \{/.test(INDEX_SRC),
            'светлая тема задана');
        assertTrue(/\.cj-print-btn-inline:hover \{/.test(INDEX_SRC),
            'hover есть');
        assertTrue(/\.cj-print-btn-inline:active \{/.test(INDEX_SRC) &&
                   INDEX_SRC.indexOf('scale(0.94)') !== -1,
            'active-сжатие как у остальных cj-кнопок');
    });

    test('заголовок страницы — padding под ТРИ кнопки (128px)', () => {
        const re = /#page-cable-journal-edit \.page-inline-header:has\(\.cj-print-btn-inline\) \.page-inline-header-title \{\s*padding-right:\s*128px;/;
        assertTrue(re.test(INDEX_SRC),
            'текст заголовка не залезает под значки (88..120)');
    });

    test('fitToTitle: .cj-print-btn-inline в селекторе кнопок', () => {
        const i = INDEX_SRC.indexOf(
            ".dev-search-toggle-btn, .dev-table-toggle-btn, .cj-icon-btn-inline, .cj-add-btn-inline, .cj-print-btn-inline, .fav-header-clear-btn");
        assertTrue(i !== -1,
            'поле поиска расчитывает правый край с учётом печати');
    });

    test('css печатного листа: скоуп #wsPrintSheet.cj-sheet', () => {
        assertTrue(INDEX_SRC.indexOf('_CJ_PRINT_CSS:') !== -1,
            'константа CSS определена');
        const i = INDEX_SRC.indexOf('_CJ_PRINT_CSS:');
        const css = INDEX_SRC.slice(i, INDEX_SRC.indexOf('_cjInjectPrintStyle', i));
        assertTrue(css.indexOf('#wsPrintSheet.cj-sheet') !== -1,
            'правила скоуплены под cj-sheet (не задевают печать табеля)');
        assertTrue(css.indexOf('.cjpr-table') !== -1 &&
                   css.indexOf('.cjpr-grp') !== -1,
            'табличная вёрстка журнала');
    });
});

// ============================================================
// 3. SRC: методы печати KipCableJournal
// ============================================================
describe('Task 505 — SRC: полный набор методов', () => {

    const METHODS = [
        'printJournal', '_printModel', '_cjPrintCols', '_cjCellVal',
        '_cjFmtNum', '_cjSub', '_buildCjPrintHtml', '_cjInjectPrintStyle',
        '_cjRemovePrintStyle', '_buildCjFileHtml', '_openCjPreview',
        '_cjPrevFit', '_closeCjPreview', '_saveCjPdf', '_cjPdfLayout',
        '_cjPdfPaintPage', '_saveCjXlsx', '_buildCjWorkbook',
        '_cjIsoDate', '_cjDownload'
    ];

    test('все 20 методов определены в KipCableJournal', () => {
        let all = true;
        const missing = [];
        METHODS.forEach(function(m) {
            if (CJ_SRC.indexOf('\n        ' + m + ': function') === -1) {
                all = false;
                missing.push(m);
            }
        });
        assertTrue(all, 'отсутствуют: ' + missing.join(', '));
    });

    test('printJournal: пустой журнал → тост, вызов из onclick', () => {
        const m = methodText(CJ_SRC, 'printJournal');
        assertTrue(m.indexOf('Нет записей для печати') !== -1,
            'тост про пустой журнал');
        assertTrue(m.indexOf("sheet.className = 'cj-sheet'") !== -1,
            'печатный лист получает класс cj-sheet (общий id wsPrintSheet)');
        assertTrue(m.indexOf('_openCjPreview(model)') !== -1 &&
                   m.indexOf('if (!opened) window.print()') !== -1,
            'диалог предпросмотра + фолбэк печать сразу');
    });

    test('модель печатает ТЕКУЩИЙ список this._rows (фильтр учтён)', () => {
        const m = methodText(CJ_SRC, '_printModel');
        assertTrue(m.indexOf('var srcRows = (this._rows || []).slice();') !== -1,
            'источник — текущие строки (как в списке на экране)');
        assertTrue(m.indexOf("'(без отделения)'") !== -1,
            'пустое отделение → «(без отделения)» (как _render)');
        assertTrue(m.indexOf('filtered') !== -1 &&
                   m.indexOf('totalAll') !== -1,
            'признак фильтра и полный счётчик для подзаголовка');
    });

    test('диалог: wspprev-* + взаимоисключающие предпросмотры табеля', () => {
        const m = methodText(CJ_SRC, '_openCjPreview');
        assertTrue(m.indexOf("overlay.id = 'cjPrintPrevModal'") !== -1,
            'свой id диалога (cjPrintPrevModal)');
        assertTrue(m.indexOf("'wspprev-overlay'") !== -1,
            'вёрстка классов Task 430 (как у табеля)');
        assertTrue(m.indexOf('_closePrintPreview') !== -1 &&
                   m.indexOf('_closeTalonsPreview') !== -1 &&
                   m.indexOf('_closeEventsPreview') !== -1,
            'закрывает предпросмотры табеля (график/талоны/список)');
        assertTrue(m.indexOf('A4 · альбомная') !== -1,
            'подсказка «A4 · альбомная»');
        assertTrue(m.indexOf("frame.className = 'wspprev-frame'") !== -1,
            'альбомная ширина iframe 1063px (базовая .wspprev-frame, без книжного override)');
    });

    test('Excel: делегирует помощникам табеля (Task 430/465)', () => {
        const m = methodText(CJ_SRC, '_buildCjWorkbook');
        assertTrue(m.indexOf('WorkSchedule._eventsSheetXml') !== -1 &&
                   m.indexOf('WorkSchedule._wsXlsZip') !== -1 &&
                   m.indexOf('WorkSchedule._wsXlsDocProps') !== -1,
            'писатель xlsx переиспользуется (без дублирования кода)');
        assertTrue(m.indexOf('sheet name="Кабельный журнал" sheetId') !== -1,
            'лист называется «Кабельный журнал»');
    });
});

// ============================================================
// 4. VM: модель, печатный HTML, standalone-документ
// ============================================================
describe('Task 505 — VM: модель и печатная форма', () => {

    const ROWS = [
        { _row: 2, designation: '1/7', start: 'ЩК-4, ШУ-1', end: 'ЭЩ №4',
          section: 'по коробу', mark_project: 'КВБбШЭнг-LS',
          cores_project: '14х1', length_project: 60,
          mark_actual: 'КВБбШЭнг-LS', cores_actual: '19х1',
          length_actual: 90, department: 'Водоподготовка',
          purpose: 'Контрольный' },
        { _row: 3, designation: '2/1', start: 'ЩК-4, ШУ-1',
          end: 'КС-1, отм. 0,0 м., оси 1-2/А-Б', section: 'по коробу',
          mark_project: 'КВБбШЭнг-LS', cores_project: '27х1',
          length_project: 43, mark_actual: 'КВБбШЭнг-LS',
          cores_actual: '27х1', length_actual: 43.5,
          department: 'Водоподготовка', purpose: 'Контрольный' },
        { _row: 5, designation: '5/2 & КГ', start: 'ЩСУ-2', end: 'Н-1',
          section: 'по лотку', mark_project: 'КГ', cores_project: '3х2,5',
          length_project: 12, mark_actual: 'КГ', cores_actual: '3х2,5',
          length_actual: 12, department: 'Отделение №2',
          purpose: 'Силовой <АВР>' }
    ];

    function cjHost(rows, allRows) {
        return new Function('WorkSchedule', 'KipToast', 'window', 'document',
            'return ({' +
            methodText(CJ_SRC, '_printModel') + '\n' +
            methodText(CJ_SRC, '_cjPrintCols') + '\n' +
            methodText(CJ_SRC, '_cjCellVal') + '\n' +
            methodText(CJ_SRC, '_cjFmtNum') + '\n' +
            methodText(CJ_SRC, '_cjSub') + '\n' +
            methodText(CJ_SRC, '_buildCjPrintHtml') + '\n' +
            methodText(CJ_SRC, '_buildCjFileHtml') + '\n' +
            methodText(CJ_SRC, '_plural') + '\n' +
            methodText(CJ_SRC, '_esc') + '\n' +
            '_rows: ' + JSON.stringify(rows) + ',' +
            '_allRows: ' + JSON.stringify(allRows || rows) + ',' +
            '\n});')(undefined, undefined, undefined, undefined);
    }

    test('модель: группировка по алфавиту, сквозная нумерация, 43,5', () => {
        const h = cjHost(ROWS);
        const m = h._printModel();
        assertEqual(m.groups.length, 2, 'два отделения');
        assertEqual(m.groups[0].name, 'Водоподготовка',
            'группы по алфавиту (В < О)');
        assertEqual(m.groups[1].name, 'Отделение №2', 'вторая группа');
        assertEqual(m.total, 3, 'всего записей');
        assertEqual(m.filtered, false, 'без фильтра — filtered false');
        // ячейки
        assertEqual(m.groups[0].rows[0].cells.num, '1', '№ п/п 1');
        assertEqual(m.groups[0].rows[1].cells.num, '2', '№ п/п 2');
        assertEqual(m.groups[1].rows[0].cells.num, '3', 'нумерация сквозная');
        assertEqual(m.groups[0].rows[1].cells.length_actual, '43,5',
            'число → строка с запятой');
        assertEqual(m.groups[0].rows[0].cells.length_project, '60',
            'целое без хвоста .0');
        assertEqual(m.groups[1].rows[0].cells.designation, '5/2 & КГ',
            'строки проходят как есть (экранирование — в HTML)');
    });

    test('модель: пустое отделение → «(без отделения)»', () => {
        const rows = [Object.assign({}, ROWS[0], { department: '   ' })];
        const h = cjHost(rows);
        const m = h._printModel();
        assertEqual(m.groups[0].name, '(без отделения)',
            'пробельное отделение — заглушка, как в списке');
    });

    test('модель: фильтр — «записей: 2 из 3» в подзаголовке', () => {
        const h = cjHost(ROWS.slice(0, 2), ROWS);
        const m = h._printModel();
        assertEqual(m.filtered, true, 'filtered true');
        assertEqual(m.total, 2, 'печатается отфильтрованное');
        assertEqual(h._cjSub(m), 'отделений: 1 · записей: 2 из 3',
            'подзаголовок с «из K»');
    });

    test('HTML: двухуровневая шапка + строки отделений + зебра + esc', () => {
        const h = cjHost(ROWS);
        const html = h._buildCjPrintHtml(h._printModel());
        assertTrue(html.indexOf('cjpr-title') !== -1 &&
                   html.indexOf('Кабельный журнал') !== -1, 'шапка листа');
        assertEqual((html.match(/rowspan="2"/g) || []).length, 6,
            '6 одиночных колонок rowspan 2');
        assertEqual((html.match(/colspan="3"/g) || []).length, 2,
            'пары «По проекту»/«Проложен» colspan 3');
        assertTrue(html.indexOf('По проекту') !== -1 &&
                   html.indexOf('Проложен') !== -1, 'подписи пар');
        assertEqual((html.match(/class="cjpr-grp"/g) || []).length, 2,
            'две строки-подзаголовка отделений');
        assertEqual((html.match(/colspan="12"/g) || []).length, 2,
            'строки отделений во всю ширину (12 колонок)');
        assertEqual((html.match(/class="cjpr-odd"/g) || []).length, 2,
            'зебра: нечётные строки (1 и 3)');
        assertEqual((html.match(/class="cjpr-even"/g) || []).length, 1,
            'зебра: чётная строка (2)');
        assertTrue(html.indexOf('5/2 &amp; КГ') !== -1,
            'значения экранированы (&)');
        assertTrue(html.indexOf('Силовой &lt;АВР&gt;') !== -1,
            'экранирование < >');
        assertTrue(html.indexOf('43,5') !== -1, 'число с запятой');
        assertEqual((html.match(/<col style=/g) || []).length, 12,
            'colgroup: 12 колонок фиксированной ширины');
    });

    test('HTML: пустой журнал — строка-заглушка', () => {
        const h = cjHost([]);
        const html = h._buildCjPrintHtml(h._printModel());
        assertTrue(html.indexOf('нет записей в журнале') !== -1,
            'заглушка как у печати табеля');
    });

    test('standalone-документ: A4 альбомная, 281мм, cj-sheet', () => {
        const h = cjHost(ROWS);
        const doc = h._buildCjFileHtml('X');
        assertTrue(doc.indexOf('<!DOCTYPE html>') === 0,
            'полноценный документ (для iframe)');
        assertTrue(doc.indexOf('@page { size: A4 landscape; margin: 8mm; }') !== -1,
            'альбомная ориентация');
        assertTrue(doc.indexOf('width: 281mm') !== -1,
            'лист 281мм (297 − 2×8)');
        assertTrue(doc.indexOf('id="wsPrintSheet" class="cj-sheet"') !== -1,
            'лист с классом cj-sheet');
        assertTrue(doc.indexOf('#wsPrintSheet.cj-sheet') !== -1,
            'CSS печатного листа внутри документа');
    });
});

// ============================================================
// 5. VM: раскладка PDF
// ============================================================
describe('Task 505 — VM: раскладка PDF (A4 альбомная)', () => {

    function row(i, dep) {
        return { _row: i + 2, designation: 'К' + i, start: 'ЩК-4', end: 'ЭЩ №' + i,
                 section: 'по коробу', mark_project: 'КВБбШЭнг-LS',
                 cores_project: '14х1', length_project: 60,
                 mark_actual: 'КВБбШЭнг-LS', cores_actual: '19х1',
                 length_actual: 90, department: dep, purpose: 'Контрольный' };
    }

    function layoutHost(rows) {
        return new Function('WorkSchedule', 'KipToast', 'window', 'document',
            'return ({' +
            methodText(CJ_SRC, '_printModel') + '\n' +
            methodText(CJ_SRC, '_cjPrintCols') + '\n' +
            methodText(CJ_SRC, '_cjCellVal') + '\n' +
            methodText(CJ_SRC, '_cjFmtNum') + '\n' +
            methodText(CJ_SRC, '_cjPdfLayout') + '\n' +
            '_rows: ' + JSON.stringify(rows) + ',' +
            '\n});')(undefined, undefined, undefined, undefined);
    }

    test('геометрия: 842×595, поля 28, колонки 12 суммой 786', () => {
        const rows = [row(0, 'А'), row(1, 'А')];
        const lay = layoutHost(rows)._cjPdfLayout(layoutHost(rows)._printModel());
        assertEqual(lay.W, 842, 'A4 альбомная ширина');
        assertEqual(lay.H, 595, 'высота');
        assertEqual(lay.M, 28, 'поля');
        assertEqual(lay.cols.length, 12, '12 колонок');
        let sum = 0;
        lay.cols.forEach(function(c) { sum += c.w; });
        assertEqual(sum, 842 - 2 * 28, 'ширины колонок точно раскладывают контент');
        assertEqual(lay.cols[0].x, 28, 'первая колонка от поля');
        assertEqual(lay.cols[11].x + lay.cols[11].w, 842 - 28,
            'последняя колонка доходит до правого поля');
    });

    test('малый список — одна страница, шапка на ней', () => {
        const rows = [row(0, 'А'), row(1, 'А'), row(2, 'Б')];
        const h = layoutHost(rows);
        const lay = h._cjPdfLayout(h._printModel());
        assertEqual(lay.pages.length, 1, 'одна страница');
        assertTrue(lay.pages[0].first, 'первая страница помечена');
        // элементы: 2 grp + 3 row
        const grps = lay.pages[0].items.filter(function(it) { return it.type === 'grp'; });
        const dataRows = lay.pages[0].items.filter(function(it) { return it.type === 'row'; });
        assertEqual(grps.length, 2, 'два подзаголовка отделений');
        assertEqual(dataRows.length, 3, 'три строки данных');
        assertEqual(dataRows[2].idx, 3, 'сквозной индекс зебры');
    });

    test('пагинация: длинный журнал ≥ 2 страниц, шапка на каждой', () => {
        const rows = [];
        for (let i = 0; i < 80; i++) rows.push(row(i, 'Отделение ' + (i % 4)));
        const h = layoutHost(rows);
        const lay = h._cjPdfLayout(h._printModel());
        assertTrue(lay.pages.length >= 2, 'страниц несколько (получено ' + lay.pages.length + ')');
        // каждый элемент попадает ровно на одну страницу
        let total = 0;
        lay.pages.forEach(function(p) { total += p.items.length; });
        const expect = lay.pages.reduce(function(acc, p) {
            return acc + p.items.filter(function(it) { return it.type === 'row'; }).length;
        }, 0);
        assertEqual(expect, 80, 'все 80 строк распределены');
        // подзаголовок отделения НЕ последний на странице (не висит)
        lay.pages.forEach(function(p, pi) {
            const last = p.items[p.items.length - 1];
            assertTrue(!(last && last.type === 'grp'),
                'страница ' + (pi + 1) + ': подзаголовок не висит без строк');
        });
        // высота страниц в бюджете (539pt) — проверка инварианта
        lay.pages.forEach(function(p, pi) {
            let y = p.first ? lay.headH : 0;
            y += lay.thH;
            p.items.forEach(function(it) {
                y += (it.type === 'grp') ? lay.grpH
                     : (it.lines * lay.lineH + lay.rowPad);
            });
            assertTrue(y <= lay.H - 2 * lay.M + 0.001,
                'страница ' + (pi + 1) + ' в бюджете (y=' + Math.round(y) + ')');
        });
    });

    test('перенос: длинный текст расширяет строку (lines > 1)', () => {
        const rows = [Object.assign(row(0, 'А'),
            { end: 'очень очень очень длинный конец трассы кабеля через весь корпус 114 со всеми поворотами и лотками' })];
        const h = layoutHost(rows);
        const lay = h._cjPdfLayout(h._printModel());
        const it = lay.pages[0].items.filter(function(x) { return x.type === 'row'; })[0];
        assertTrue(it.lines > 1, 'строка с длинным текстом выше одной линии');
    });
});

// ============================================================
// 6. VM: книга Excel
// ============================================================
describe('Task 505 — VM: книга Excel (кабельный журнал)', () => {

    const ROWS = [
        { _row: 2, designation: '1/7', start: 'ЩК-4, ШУ-1', end: 'ЭЩ №4',
          section: 'по коробу', mark_project: 'КВБбШЭнг-LS',
          cores_project: '14х1', length_project: 60,
          mark_actual: 'КВБбШЭнг-LS', cores_actual: '19х1',
          length_actual: 90, department: 'Водоподготовка',
          purpose: 'Контрольный' },
        { _row: 5, designation: '5/2', start: 'ЩСУ-2', end: 'Н-1',
          section: 'по лотку', mark_project: 'КГ', cores_project: '3х2,5',
          length_project: 12, mark_actual: 'КГ', cores_actual: '3х2,5',
          length_actual: 12, department: 'Отделение №2', purpose: 'Силовой' }
    ];

    // мини-WorkSchedule из РЕАЛЬНЫХ методов (писатель Task 430/465)
    function wsHost() {
        return new Function('return ({' +
            methodText(WS_SRC, '_wsXlsBytes') + '\n' +
            methodText(WS_SRC, '_wsXlsCrc32') + '\n' +
            methodText(WS_SRC, '_wsXlsZip') + '\n' +
            methodText(WS_SRC, '_wsXlsColName') + '\n' +
            methodText(WS_SRC, '_wsXlsEsc') + '\n' +
            methodText(WS_SRC, '_wsXlsDocProps') + '\n' +
            methodText(WS_SRC, '_eventsSheetXml') + '\n' +
            methodText(WS_SRC, '_eventsStylesXml') + '\n' +
            methodText(WS_SRC, '_buildPdfDocument') + '\n' +
            methodText(WS_SRC, '_wsDataUrlBytes') + '\n' +
            methodText(WS_SRC, '_wsDownload') + '\n' +
            '\n});')();
    }

    function cjBookHost(rows, ws) {
        return new Function('WorkSchedule', 'KipToast', 'window', 'document',
            'return ({' +
            methodText(CJ_SRC, '_printModel') + '\n' +
            methodText(CJ_SRC, '_cjPrintCols') + '\n' +
            methodText(CJ_SRC, '_cjCellVal') + '\n' +
            methodText(CJ_SRC, '_cjFmtNum') + '\n' +
            methodText(CJ_SRC, '_cjSub') + '\n' +
            methodText(CJ_SRC, '_buildCjWorkbook') + '\n' +
            methodText(CJ_SRC, '_cjIsoDate') + '\n' +
            methodText(CJ_SRC, '_plural') + '\n' +
            '_rows: ' + JSON.stringify(rows) + ',' +
            '_allRows: ' + JSON.stringify(rows) + ',' +
            '\n});')(ws, undefined, undefined, undefined);
    }

    test('структура строк: заголовок, шапка с «(по проекту)», числа', () => {
        const ws = wsHost();
        const h = cjBookHost(ROWS, ws);
        const wb = h._buildCjWorkbook(h._printModel());
        assertTrue(!!wb && !!wb.bytes, 'книга собрана');
        assertEqual(wb.counts.total, 2, 'счётчик записей');
        assertEqual(wb.counts.groups, 2, 'счётчик отделений');
        assertTrue(/^Кабельный_журнал_\d{4}-\d{2}-\d{2}\.xlsx$/.test(wb.name),
            'имя файла с датой: ' + wb.name);
        assertTrue(wb.bytes instanceof Uint8Array && wb.bytes.length > 500,
            'байты xlsx (архив)');
        assertEqual(wb.bytes[0], 0x50, 'PK-магия zip (P)');
        assertEqual(wb.bytes[1], 0x4B, 'PK-магия zip (K)');
        // содержимое (zip STORED — строки читаются напрямую)
        const txt = Buffer.from(wb.bytes).toString('utf8');
        assertTrue(txt.indexOf('sheet name="Кабельный журнал"') !== -1,
            'лист называется «Кабельный журнал»');
        assertTrue(txt.indexOf('Кабельный журнал') !== -1 &&
                   txt.indexOf('Водоподготовка') !== -1 &&
                   txt.indexOf('КВБбШЭнг-LS') !== -1,
            'данные журнала внутри книги');
        // числа — ЧИСЛАМИ: <v>60</v>, а не inlineStr
        assertTrue(txt.indexOf('<v>60</v>') !== -1 &&
                   txt.indexOf('<v>90</v>') !== -1 &&
                   txt.indexOf('<v>12</v>') !== -1,
            'длины записаны числами (редактируемые, Task 488)');
        assertTrue(txt.indexOf('Марка (по проекту)') !== -1 &&
                   txt.indexOf('Марка (проложен)') !== -1,
            'шапка Excel с пояснениями в скобках');
    });

    test('книга без записей — строка-заглушка', () => {
        const ws = wsHost();
        const h = cjBookHost([], ws);
        const wb = h._buildCjWorkbook(h._printModel());
        const txt = Buffer.from(wb.bytes).toString('utf8');
        assertTrue(txt.indexOf('нет записей в журнале') !== -1,
            'заглушка в книге (как в печати)');
    });
});

// ============================================================
// 7. VM (мок-DOM): printJournal + диалог предпросмотра
// ============================================================
describe('Task 505 — VM (мок-DOM): диалог предпросмотра', () => {

    function fakeDom() {
        const elements = {};
        const body = {
            children: [],
            appendChild: function(el) {
                el.parentNode = body;
                body.children.push(el);
                if (el.id) elements[el.id] = el;
            },
            removeChild: function(el) {
                body.children = body.children.filter(c => c !== el);
                if (el.id && elements[el.id] === el) delete elements[el.id];
            }
        };
        const head = {
            children: [],
            appendChild: function(el) {
                el.parentNode = head;
                head.children.push(el);
                if (el.id) elements[el.id] = el;
            },
            removeChild: function(el) {
                head.children = head.children.filter(c => c !== el);
                if (el.id && elements[el.id] === el) delete elements[el.id];
            }
        };
        function makeEl(tag) {
            const el = {
                tag: tag, id: '', className: '', innerHTML: '',
                children: [], style: {}, attrs: {}, listeners: {},
                parentNode: null, srcdoc: '', contentDocument: null,
                addEventListener: function(type, fn) {
                    (el.listeners[type] = el.listeners[type] || []).push(fn);
                },
                removeEventListener: function(type, fn) {
                    el.listeners[type] = (el.listeners[type] || [])
                        .filter(f => f !== fn);
                },
                dispatch: function(type, ev) {
                    (el.listeners[type] || []).slice()
                        .forEach(fn => fn(ev || {}));
                },
                setAttribute: function(k, v) { el.attrs[k] = v; },
                appendChild: function(c) {
                    c.parentNode = el;
                    el.children.push(c);
                    return c;
                },
                removeChild: function(c) {
                    el.children = el.children.filter(x => x !== c);
                },
                querySelector: function(sel) {
                    const cls = sel.replace(/^\./, '');
                    const find = function(root) {
                        for (let i = 0; i < root.children.length; i++) {
                            const ch = root.children[i];
                            if (String(ch.className || '')
                                    .split(/\s+/).indexOf(cls) !== -1) {
                                return ch;
                            }
                            const r = find(ch);
                            if (r) return r;
                        }
                        return null;
                    };
                    const found = find(el);
                    if (found) return found;
                    if (!el._qcache) el._qcache = {};
                    if (!el._qcache[cls]) el._qcache[cls] = makeEl('button');
                    return el._qcache[cls];
                }
            };
            return el;
        }
        const document = {
            createElement: makeEl,
            getElementById: function(id) { return elements[id] || null; },
            body: body,
            head: head
        };
        return { document: document, elements: elements };
    }

    function makeWin() {
        const win = {
            printCalls: 0,
            listeners: {},
            print: function() { win.printCalls++; },
            addEventListener: function(t, fn) {
                (win.listeners[t] = win.listeners[t] || []).push(fn);
            },
            removeEventListener: function(t, fn) {
                win.listeners[t] = (win.listeners[t] || []).filter(f => f !== fn);
            },
            key: function(k) {
                (win.listeners.keydown || []).forEach(
                    fn => fn({ key: k }));
            }
        };
        return win;
    }

    const ROWS = [
        { _row: 2, designation: '1/7', start: 'ЩК-4', end: 'ЭЩ №4',
          section: 'по коробу', mark_project: 'КВБбШЭнг-LS',
          cores_project: '14х1', length_project: 60,
          mark_actual: 'КВБбШЭнг-LS', cores_actual: '19х1',
          length_actual: 90, department: 'Водоподготовка',
          purpose: 'Контрольный' }
    ];

    function fullHost(dom, win, kipToast, rows, ws) {
        return new Function('WorkSchedule', 'KipToast', 'window', 'document',
            'return ({' +
            methodText(CJ_SRC, 'printJournal') + '\n' +
            methodText(CJ_SRC, '_printModel') + '\n' +
            methodText(CJ_SRC, '_cjPrintCols') + '\n' +
            methodText(CJ_SRC, '_cjCellVal') + '\n' +
            methodText(CJ_SRC, '_cjFmtNum') + '\n' +
            methodText(CJ_SRC, '_cjSub') + '\n' +
            methodText(CJ_SRC, '_buildCjPrintHtml') + '\n' +
            methodText(CJ_SRC, '_buildCjFileHtml') + '\n' +
            methodText(CJ_SRC, '_cjInjectPrintStyle') + '\n' +
            methodText(CJ_SRC, '_cjRemovePrintStyle') + '\n' +
            methodText(CJ_SRC, '_openCjPreview') + '\n' +
            methodText(CJ_SRC, '_cjPrevFit') + '\n' +
            methodText(CJ_SRC, '_closeCjPreview') + '\n' +
            methodText(CJ_SRC, '_plural') + '\n' +
            methodText(CJ_SRC, '_esc') + '\n' +
            '_CJ_PRINT_CSS: ' + JSON.stringify(
                '#wsPrintSheet.cj-sheet { font: 11px Arial; }') + ',' +
            '_rows: ' + JSON.stringify(rows) + ',' +
            '_allRows: ' + JSON.stringify(rows) + ',' +
            '\n});')(ws || undefined, kipToast, win, dom.document);
    }

    test('пустой журнал: тост, лист НЕ создаётся, печать НЕ зовётся', () => {
        const dom = fakeDom();
        const win = makeWin();
        const toasts = [];
        const toast = { show: function(m) { toasts.push(m); } };
        const h = fullHost(dom, win, toast, []);
        h.printJournal();
        assertEqual(toasts.length, 1, 'один тост');
        assertEqual(toasts[0], 'Нет записей для печати — журнал пуст',
            'текст тоста');
        assertEqual(win.printCalls, 0, 'печати не было');
        assertEqual(dom.elements['wsPrintSheet'], undefined,
            'печатный лист не создан');
    });

    test('с данными: лист cj-sheet + диалог wspprev-* + iframe', () => {
        const dom = fakeDom();
        const win = makeWin();
        const h = fullHost(dom, win, undefined, ROWS);
        h.printJournal();
        const sheet = dom.elements['wsPrintSheet'];
        assertTrue(!!sheet, 'печатный лист создан');
        assertEqual(sheet.className, 'cj-sheet', 'класс cj-sheet');
        assertTrue(sheet.innerHTML.indexOf('cjpr-table') !== -1,
            'таблица журнала в листе');
        const ov = dom.elements['cjPrintPrevModal'];
        assertTrue(!!ov, 'диалог предпросмотра открыт');
        assertEqual(ov.className, 'wspprev-overlay', 'вёрстка Task 430');
        const frame = ov.querySelector('.wspprev-frame');
        assertTrue(!!frame, 'iframe предпросмотра');
        assertTrue(frame.srcdoc.indexOf('<!DOCTYPE html>') === 0,
            'в iframe — standalone-документ');
        assertTrue(frame.srcdoc.indexOf('cjpr-table') !== -1,
            'контент журнала в предпросмотре');
        assertEqual(win.printCalls, 0, 'сразу НЕ печатает (сначала диалог)');
        // инжект-стиль добавлен
        const st = dom.elements['cjPrintStyle'];
        assertTrue(!!st, 'инжект-стиль печати в <head>');
        assertTrue(st.textContent.indexOf('#wsPrintSheet.cj-sheet') !== -1,
            'стиль скоуплен под cj-sheet');
    });

    test('кнопочный ряд Task 438: Печать/PDF/Excel/Отмена + подсказка', () => {
        const dom = fakeDom();
        const win = makeWin();
        const h = fullHost(dom, win, undefined, ROWS);
        h.printJournal();
        const ov = dom.elements['cjPrintPrevModal'];
        // foot — третий ребёнок диалога
        const dlg = ov.children[0];
        const foot = dlg.children[2];
        assertTrue(!!foot && foot.className === 'wspprev-foot',
            'нижний ряд диалога');
        const f = foot.innerHTML;
        assertTrue(f.indexOf('wspprev-print') !== -1 &&
                   f.indexOf('Печать</button>') !== -1, 'кнопка «Печать»');
        assertTrue(f.indexOf('wspprev-pdf') !== -1 &&
                   f.indexOf('Сохранить PDF</button>') !== -1,
            'кнопка «Сохранить PDF»');
        assertTrue(f.indexOf('wspprev-xlsx') !== -1 &&
                   f.indexOf('Сохранить Excel</button>') !== -1,
            'кнопка «Сохранить Excel»');
        assertTrue(f.indexOf('wspprev-cancel') !== -1 &&
                   f.indexOf('Отмена</button>') !== -1, 'кнопка «Отмена»');
        assertTrue(f.indexOf('A4 · альбомная') !== -1, 'подсказка формата');
    });

    test('Esc закрывает: слушатели сняты, элемент удалён, стиль снят', () => {
        const dom = fakeDom();
        const win = makeWin();
        const h = fullHost(dom, win, undefined, ROWS);
        h.printJournal();
        assertEqual((win.listeners.keydown || []).length, 1,
            'Esc-слушатель окна зарегистрирован');
        win.key('Escape');
        assertEqual(dom.elements['cjPrintPrevModal'], undefined,
            'диалог удалён из body');
        assertEqual(dom.elements['cjPrintStyle'], undefined,
            'инжект-стиль снят');
        assertEqual((win.listeners.keydown || []).length, 0,
            'слушатель снят (нет утечки)');
    });

    test('диалоги взаимоисключающие: предпросмотры табеля закрыты', () => {
        const dom = fakeDom();
        const win = makeWin();
        const closed = [];
        const ws = {
            _closePrintPreview: function() { closed.push('grid'); },
            _closeTalonsPreview: function() { closed.push('talons'); },
            _closeEventsPreview: function() { closed.push('events'); }
        };
        const h = fullHost(dom, win, undefined, ROWS, ws);
        h._openCjPreview(h._printModel());
        assertEqual(closed.length, 3,
            'все три предпросмотра табеля закрыты');
        assertTrue(closed.indexOf('grid') !== -1 &&
                   closed.indexOf('talons') !== -1 &&
                   closed.indexOf('events') !== -1, 'полный набор');
    });

    test('фолбэк: диалог не открылся — печать сразу', () => {
        const win = makeWin();
        // минимальный DOM: лист и инжект-стиль создаются, но диалог
        // «не открывается» (окружение без iframe) — printJournal
        // обязан напечатать сразу (приём Task 341/430)
        const elStub = function() {
            return { id: '', className: '', innerHTML: '', style: {},
                     appendChild: function(c) { return c; } };
        };
        const doc = {
            createElement: elStub,
            getElementById: function() { return null; },
            body: { appendChild: function() {} },
            head: { appendChild: function() {} }
        };
        const h = new Function('WorkSchedule', 'KipToast', 'window', 'document',
            'return ({' +
            methodText(CJ_SRC, 'printJournal') + '\n' +
            methodText(CJ_SRC, '_printModel') + '\n' +
            methodText(CJ_SRC, '_cjPrintCols') + '\n' +
            methodText(CJ_SRC, '_cjCellVal') + '\n' +
            methodText(CJ_SRC, '_cjFmtNum') + '\n' +
            methodText(CJ_SRC, '_cjSub') + '\n' +
            methodText(CJ_SRC, '_buildCjPrintHtml') + '\n' +
            methodText(CJ_SRC, '_plural') + '\n' +
            methodText(CJ_SRC, '_esc') + '\n' +
            methodText(CJ_SRC, '_openCjPreview') + '\n' +
            methodText(CJ_SRC, '_cjInjectPrintStyle') + '\n' +
            '_rows: ' + JSON.stringify(ROWS) + ',' +
            '\n});')(undefined, undefined, win, doc);
        h._openCjPreview = function() { return false; };
        h.printJournal();
        assertEqual(win.printCalls, 1, 'фолбэк — печать сразу');
    });

    test('_cjIsoDate: локальный ГГГГ-ММ-ДД', () => {
        const h = new Function('return ({' +
            methodText(CJ_SRC, '_cjIsoDate') + '\n});')();
        const s = h._cjIsoDate(new Date(2026, 9, 5));
        assertEqual(s, '2026-10-05', 'локальная дата с ведущими нулями');
    });
});

// ============================================================
// 8. SW: версия кэша
// ============================================================
describe('Task 505 — SW: kipia-test-v728', () => {
    test('CACHE_VERSION = kipia-test-v728', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v728'") !== -1,
            'версия кэша kipia-test-v728');
        assertFalse(SW_SRC.indexOf('kipia-test-v729') !== -1,
            'двойного бампа нет (v729 отсутствует)');
    });

    test('комментарий Task 505 в истории версий sw.js', () => {
        const i = SW_SRC.indexOf('// Task 505:');
        const v = SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v728'");
        assertTrue(i !== -1, 'запись истории на месте');
        assertTrue(i < v, 'история — выше константы версии');
        const cmt = SW_SRC.slice(i, v);
        assertTrue(cmt.indexOf('Кабельный журнал') !== -1 &&
                   cmt.toLowerCase().indexOf('предпросмотра') !== -1,
            'суть задачи в комментарии');
    });
});
