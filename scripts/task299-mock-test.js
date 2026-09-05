#!/usr/bin/env node
/**
 * task299-mock-test.js — проверка StatusCodesInit.gs на моках Apps Script.
 *
 * Моделирует ПОВЕДЕНИЕ Google Apps Script, нужное скрипту:
 *   - openById / getSheets / getSheetByName / insertSheet(name, index
 *     — 0-based, как в GAS) / deleteSheet (нельзя последний);
 *   - getIndex() — 1-based (асимметрия с insertSheet — как в GAS);
 *   - getLastRow() — максимум СТРОКИ с непустым значением (стили
 *     не влияют — Lesson Task 294 про стилевой холст);
 *   - getRange(row, col, numRows, numCols) + setValues/setValue/
 *     getValues/getValue, setNumberFormat('@'), setBackground(s),
 *     setFont.../setWrap... (и множественные формы) — «пишут» в мок-ячейки;
 *   - copyTo(ss) — глубокая копия листа (в т.ч. Date-значения).
 *
 * Сценарии:
 *   A. Данные: 16 строк, уникальные коды, цвета #RRGGBB; состав
 *      и цвета СОВПАДАЮТ с fallback-набором index.html (Task 298);
 *   B. Замена старого листа (10 кодов): резерв + новый лист 16
 *      кодов на прежней позиции + форматы/оформление;
 *   C. Идемпотентность: повторный запуск — skip, без резерва;
 *   D. Замена листа в состоянии «как у пользователя» (15 строк,
 *      склеенный «Д8, Д7,2», «?» в цветах) — 16 эталонных;
 *   E. Листа нет — создаётся на 3-й позиции;
 *   F. Дубль кода в данных — замена отклонена ДО изменений;
 *   G. dropValues (запись потерялась) — самопроверка ловит;
 *   H. Миграция «О»→«ОТ»: только точное «О»; «ОТ»/«ОБ»/«д»/
 *      латинская «O» не тронуты; резерв; повтор — 0;
 *   I. Дни_цикла шаблон 2: Д1-4→Д8, Д5→Д7,2; «д»/пусто/шаблон 1
 *      не тронуты; резерв; повтор — 0;
 *   J. Диагностика: missing/extra/vacationLegacy/cycleLegacy;
 *   K. Очистка резервов: только резервные семейства;
 *   L. statusCodesDeployAll: оба шага.
 *
 * Запуск: node scripts/task299-mock-test.js
 */
'use strict';

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const GS_CODE = fs.readFileSync(path.join(__dirname, 'StatusCodesInit.gs'), 'utf8');
const INDEX_HTML = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

let passed = 0;
let failed = 0;
const failures = [];
function ok(cond, name) {
  if (cond) { passed++; } else { failed++; failures.push(name); console.error('  FAIL: ' + name); }
}

// ------------------------------------------------------------
// Мок Google Apps Script
// ------------------------------------------------------------
class MockRange {
  constructor(sheet, row, col, numRows, numCols) {
    this.sh = sheet;
    this.row = row; this.col = col;
    this.numRows = numRows; this.numCols = numCols;
  }
  _key(dr, dc) { return (this.row + (dr || 0)) + ':' + (this.col + (dc || 0)); }
  setNumberFormat(f) {
    for (let r = 0; r < this.numRows; r++)
      for (let c = 0; c < this.numCols; c++) this.sh.formats[this._key(r, c)] = f;
    return this;
  }
  setValues(vs) {
    if (this.sh.ss.world.dropValues) return this;
    for (let r = 0; r < this.numRows; r++)
      for (let c = 0; c < this.numCols; c++) this.sh.cells[this._key(r, c)] = vs[r][c];
    return this;
  }
  setValue(v) {
    if (this.sh.ss.world.dropValues) return this;
    for (let r = 0; r < this.numRows; r++)
      for (let c = 0; c < this.numCols; c++) this.sh.cells[this._key(r, c)] = v;
    return this;
  }
  getValues() {
    const out = [];
    for (let r = 0; r < this.numRows; r++) {
      const row = [];
      for (let c = 0; c < this.numCols; c++) {
        const v = this.sh.cells[this._key(r, c)];
        row.push(v === undefined ? '' : v);
      }
      out.push(row);
    }
    return out;
  }
  getValue() { return this.getValues()[0][0]; }
  setBackground(clr) {
    for (let r = 0; r < this.numRows; r++)
      for (let c = 0; c < this.numCols; c++) this.sh.bg[this._key(r, c)] = clr;
    return this;
  }
  setBackgrounds(m) {
    for (let r = 0; r < this.numRows; r++)
      for (let c = 0; c < this.numCols; c++) this.sh.bg[this._key(r, c)] = m[r][c];
    return this;
  }
  setFontColor(v) { this.sh.styleCalls.push(['setFontColor', v]); return this; }
  setFontWeight(v) { this.sh.styleCalls.push(['setFontWeight', v]); return this; }
  setFontWeights(m) { this.sh.styleCalls.push(['setFontWeights', m]); return this; }
  setHorizontalAlignment(v) { this.sh.styleCalls.push(['setHorizontalAlignment', v]); return this; }
  setHorizontalAlignments(m) { this.sh.styleCalls.push(['setHorizontalAlignments', m]); return this; }
  setVerticalAlignment(v) { this.sh.styleCalls.push(['setVerticalAlignment', v]); return this; }
  setVerticalAlignments(m) { this.sh.styleCalls.push(['setVerticalAlignments', m]); return this; }
  setWrap(v) { this.sh.styleCalls.push(['setWrap', v]); return this; }
  setWraps(m) { this.sh.styleCalls.push(['setWraps', m]); return this; }
}

class MockSheet {
  constructor(ss, name) {
    this.ss = ss; this.name = name;
    this.cells = {}; this.formats = {}; this.bg = {};
    this.frozenRows = 0; this.colWidths = {}; this.styleCalls = [];
  }
  getName() { return this.name; }
  setName(n) { this.name = n; return this; }
  getIndex() { return this.ss.sheets.indexOf(this) + 1; }         // 1-based (как в GAS)
  getLastRow() {
    let max = 0;
    for (const k in this.cells) {
      const v = this.cells[k];
      if (v === '' || v === null || v === undefined) continue;
      const r = parseInt(k.split(':')[0], 10);
      if (r > max) max = r;
    }
    return max;
  }
  getRange(row, col, numRows, numCols) {
    return new MockRange(this, row, col,
      numRows === undefined ? 1 : numRows, numCols === undefined ? 1 : numCols);
  }
  setFrozenRows(n) { this.frozenRows = n; }
  setColumnWidth(c, w) { this.colWidths[c] = w; }
  copyTo(ss) {
    const clone = new MockSheet(ss, 'Copy of ' + this.name);
    for (const k in this.cells) {
      const v = this.cells[k];
      clone.cells[k] = (v instanceof Date) ? new Date(v.getTime()) : v;
    }
    for (const k in this.formats) clone.formats[k] = this.formats[k];
    for (const k in this.bg) clone.bg[k] = this.bg[k];
    ss.sheets.push(clone);
    return clone;
  }
}

class MockSS {
  constructor(world, name, sheets) {
    this.world = world; this.name = name; this.sheets = sheets;
  }
  getName() { return this.name; }
  getUrl() { return 'https://docs.google.com/spreadsheets/d/mock-' + this.name + '/edit'; }
  getSheets() { return this.sheets.slice(); }
  getSheetByName(n) {
    for (let i = 0; i < this.sheets.length; i++) {
      if (this.sheets[i].name === n) return this.sheets[i];
    }
    return null;
  }
  insertSheet(name, index) {
    const s = new MockSheet(this, name);
    if (index === undefined || index === null) { this.sheets.push(s); }
    else { this.sheets.splice(Math.min(index, this.sheets.length), 0, s); }
    return s;
  }
  deleteSheet(sh) {
    if (this.sheets.length <= 1) throw new Error('mock: нельзя удалить последний лист');
    const i = this.sheets.indexOf(sh);
    if (i < 0) throw new Error('mock: лист не найден');
    this.sheets.splice(i, 1);
  }
}

function fillSheet(sheet, header, rows) {
  if (header) {
    for (let c = 0; c < header.length; c++) sheet.cells['1:' + (c + 1)] = header[c];
  }
  for (let r = 0; r < rows.length; r++) {
    for (let c = 0; c < rows[r].length; c++) {
      sheet.cells[(r + 2) + ':' + (c + 1)] = rows[r][c];
    }
  }
}

// Старые 10 кодов (лист до Task 298)
const OLD_10 = [
  ['Д',  'День',                        '#FFE082'],
  ['Н',  'Ночь',                        '#B0BEC5'],
  ['О',  'Отпуск',                      '#ECEFF1'],
  ['Б',  'Больничный',                  '#F8BBD0'],
  ['ОТ', 'Отгул',                       '#CFD8DC'],
  ['П',  'Прогул',                      '#EF5350'],
  ['*',  'Праздник',                    '#FFAB91'],
  ['И',  'Инструктаж',                  '#B3E5FC'],
  ['ОБ', 'Обучение',                    '#D1C4E9'],
  ['ПЗ', 'Проверка знаний',             '#FFCDD2']
];

// Состояние «как у пользователя» (xlsx от 03.09.2026: 15 строк,
// склеенный «Д8, Д7,2», «?» в цветах)
const USER_LIKE = [
  ['Д',        'День, плановая дневная 12-часовая смена (с 7:30 до 19:30)', '#FFE082'],
  ['Н',        'Ночь, плановая ночная 12-часовая смена (с 19:30 до 7:30)', '#B0BEC5'],
  ['Д8, Д7,2', 'День, плановая дневная 8-часовая (7,2-часовая) смена',     '?'],
  ['д',        'День, плановая продолжительность работы в выходные',        '?'],
  ['н',        'Ночь, плановая продолжительность работы в выходные',        '?'],
  ['ОТ',       'Отпуск, ежегодный основной оплачиваемый отпуск',           '#ECEFF1'],
  ['У',        'Учебный отпуск',                                          '?'],
  ['ОВ',       'Отгул, дополнительные выходные дни (оплачиваемые)',        '#C5E1A5'],
  ['Б',        'Больничный, временная нетрудоспособность',                 '#F8BBD0'],
  ['ПР',       'Прогул (отсутствие без уважительных причин)',              '#EF5350'],
  ['И',        'Инструктаж',                                              '?'],
  ['ОБ',       'Обучение',                                                '#D1C4E9'],
  ['ПЗ',       'Проверка знаний',                                         '#FFCDD2'],
  ['*',        'Примечание',                                              '?'],
  ['.',        'Выходной, плановый выходной день',                         '?']
];

function makeCtx(world) {
  const ctx = {
    Logger: { log: function (m) { world.logs.push(String(m)); } },
    SpreadsheetApp: { openById: function (id) { return world.ss; } }
  };
  vm.createContext(ctx);
  vm.runInContext(GS_CODE, ctx);
  return ctx;
}

// Таблица «как живая»: 9 листов, «Коды_статусов» в 3-й позиции
function makeTable(statusRows) {
  const world = { logs: [], dropValues: false };
  const ss = new MockSS(world, 'График работы', []);
  world.ss = ss;
  const sheets = [
    new MockSheet(ss, 'README'),
    new MockSheet(ss, 'Сотрудники'),
    new MockSheet(ss, 'Коды_статусов'),
    new MockSheet(ss, 'Шаблоны_ротации'),
    new MockSheet(ss, 'Дни_цикла'),
    new MockSheet(ss, 'Инструктажи'),
    new MockSheet(ss, 'Записи_графика'),
    new MockSheet(ss, 'Сводка_по_месяцам'),
    new MockSheet(ss, 'Отпуска')
  ];
  ss.sheets.push(...sheets);

  fillSheet(ss.getSheetByName('Коды_статусов'), ['код', 'название', 'цвет_заливки'],
    statusRows || OLD_10);
  fillSheet(ss.getSheetByName('Шаблоны_ротации'),
    ['id_шаблона', 'название', 'цикл_дней', 'описание'], [
      [1, 'Сменный 5-дневный', 5, 'Д→Н→3 вых.'],
      [2, 'Дневной 5/2', 7, 'Д×5/2 вых.']
    ]);
  fillSheet(ss.getSheetByName('Дни_цикла'),
    ['id_шаблона', 'день_цикла', 'статус'], [
      [1, 1, 'Д'], [1, 2, 'Н'], [1, 3, ''], [1, 4, ''], [1, 5, ''],
      [2, 1, 'Д'], [2, 2, 'Д'], [2, 3, 'Д'], [2, 4, 'Д'], [2, 5, 'Д'],
      [2, 6, ''], [2, 7, ''], [2, 8, 'д']
    ]);
  fillSheet(ss.getSheetByName('Записи_графика'),
    ['дата', 'таб_номер', 'статус', 'переработка', 'праздник', 'источник',
     'дата_обновления', 'замещает', 'инструкция', 'комментарий'], [
      [new Date(2026, 7, 10), '017', 'Д',  0, 0, 'авто', new Date(2026, 7, 10), '', '', ''],
      [new Date(2026, 7, 11), '017', 'О',  0, 0, 'авто', new Date(2026, 7, 11), '', '', ''],
      [new Date(2026, 7, 12), '023', 'О',  0, 0, 'авто', new Date(2026, 7, 12), '', '', ''],
      [new Date(2026, 7, 13), '017', 'ОТ', 0, 0, 'авто', new Date(2026, 7, 13), '', '', ''],
      [new Date(2026, 7, 14), '023', 'ОБ', 0, 0, 'авто', new Date(2026, 7, 14), '', '', ''],
      [new Date(2026, 7, 15), '017', 'д',  0, 0, 'руч',  new Date(2026, 7, 15), '', '', ''],
      [new Date(2026, 7, 16), '023', 'O',  0, 0, 'руч',  new Date(2026, 7, 16), '', '', ''] // латинская!
    ]);
  return { world, ctx: null, ss };
}

function sheetRows(ss, name) {
  const sh = ss.getSheetByName(name);
  if (!sh) return null;
  const lastRow = sh.getLastRow();
  if (lastRow < 2) return [];
  const vals = sh.getRange(2, 1, lastRow - 1, 3).getValues();
  return vals.filter(function (r) { return r[0] !== '' && r[0] !== null; })
             .map(function (r) { return [String(r[0]).trim(), String(r[1] || '').trim(), String(r[2] || '').trim()]; });
}

function backupCount(ss) {
  return ss.getSheets().filter(function (s) {
    const n = s.getName();
    return n.indexOf('Коды_статусов_резерв_') === 0 ||
           n.indexOf('Записи_графика_резерв_') === 0 ||
           n.indexOf('Дни_цикла_резерв_') === 0;
  }).length;
}

// ------------------------------------------------------------
console.log('A. Эталонные данные и сверка с index.html (fallback)');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  const codes = ctx.SC_STATUS_CODES.map(function (r) { return r[0]; });
  ok(ctx.SC_STATUS_CODES.length === 16, 'A1: ровно 16 кодов');
  ok(new Set(codes).size === 16, 'A2: коды уникальны (PK)');
  ok(ctx.SC_STATUS_CODES.every(function (r) { return /^#[0-9A-Fa-f]{6}$/.test(r[2]); }),
     'A3: все цвета вида #RRGGBB');
  ok(ctx.SC_STATUS_CODES.every(function (r) { return String(r[1]).length > 0; }),
     'A4: названия непустые');

  // Состав и цвета обязаны совпадать с fallback index.html (Task 298)
  const m = /self\._STATUS_CODES = \[([\s\S]*?)\];\s*\n/.exec(INDEX_HTML);
  ok(!!m, 'A5: fallback-блок найден в index.html');
  if (m) {
    const fb = {};
    const re = /\{code:'([^']+)',\s*name:'([^']*)',\s*color:'(#[0-9A-Fa-f]{6})'\}/g;
    let mm;
    while ((mm = re.exec(m[1]))) { fb[mm[1]] = mm[3]; }
    ok(Object.keys(fb).length === 16, 'A6: fallback = 16 кодов');
    const setOk = ctx.SC_STATUS_CODES.every(function (r) { return fb[r[0]] === r[2]; });
    ok(setOk, 'A7: каждый код и цвет совпадают с fallback index.html');
    const extra = Object.keys(fb).filter(function (k) { return codes.indexOf(k) < 0; });
    ok(extra.length === 0, 'A8: в fallback нет кодов вне эталона');
  }

  // Скрипт не должен конфликтовать с глобалами других .gs
  const globals = GS_CODE.match(/^(?:function ([A-Za-z_]\w*)|var ([A-Za-z_]\w*))/gm) || [];
  const taken = ['doGet', 'doPost', 'hourlyCleanup', 'setupTriggers', '_json',
    '_gateLegacyWarn', 'vacationsInitSheet', 'vacationsSeedDemo', 'vacParseDate',
    'vacSafeDate', 'vacationsDiagnose', 'diagParseDate', 'diagSafeDate', 'diagIso',
    'diagShow', 'diagTypeName', 'flowmeterInitSheet', 'flowmeterFixDates',
    'rmResolveUserByToken', 'rmRequirePerm', 'rmGetMyAccess', 'rmGateStatus',
    'roleMatrixInit', 'roleMatrixCleanup', 'roleMatrixStatus', 'flowmeterInitArchive',
    'flowmeterInitRules', 'flowmeterInitRulesFromArchive', 'FALLBACK_SPREADSHEET_ID',
    'INIT_ROLES', 'INIT_PERMISSIONS', 'INIT_MATRIX', 'RMG_AUDIT_CODE',
    'ROLE_MATRIX_SPREADSHEET_ID', 'WorkSchedule', 'FlowmeterArchive', 'ValidationRules'];
  const declared = globals.map(function (g) {
    return g.replace(/^function /, '').replace(/^var /, '');
  });
  const clash = declared.filter(function (d) { return taken.indexOf(d) >= 0; });
  ok(clash.length === 0, 'A9: нет конфликтов имён с другими .gs (объявлены: ' +
     declared.length + ')');
}

// ------------------------------------------------------------
console.log('B. Замена старого листа (10 кодов)');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  const oldSheet = t.ss.getSheetByName('Коды_статусов');
  const res = ctx.statusCodesReplace();

  ok(res.ok === true, 'B1: ok=true');
  ok(typeof res.backup === 'string' && res.backup.indexOf('Коды_статусов_резерв_') === 0,
     'B2: имя резерва');
  const rows = sheetRows(t.ss, 'Коды_статусов');
  ok(rows.length === 16, 'B3: 16 строк данных');
  ok(JSON.stringify(rows) === JSON.stringify(ctx.SC_STATUS_CODES),
     'B4: содержимое = эталон (посимвольно, включая «Д7,2», «*», «.»)');

  // Резерв: старый лист с прежними данными, на позиции после нового
  const backupSheet = t.ss.getSheetByName(res.backup);
  ok(!!backupSheet && backupSheet === oldSheet, 'B5: резерв = переименованный старый лист');
  ok(JSON.stringify(sheetRows(t.ss, res.backup)) === JSON.stringify(OLD_10),
     'B6: данные резерва не тронуты (10 старых кодов)');
  ok(t.ss.sheets[2].getName() === 'Коды_статусов' && t.ss.sheets[2] !== oldSheet,
     'B7: новый лист на прежней позиции (3-я, 0-based 2)');
  ok(t.ss.sheets[3].getName() === res.backup, 'B8: резерв сразу после нового листа');
  ok(backupCount(t.ss) === 1, 'B9: ровно один резерв');

  // Форматы и оформление
  const ns = t.ss.getSheetByName('Коды_статусов');
  ok(ns.frozenRows === 1, 'B10: закреплена строка 1');
  ok(ns.formats['1:1'] === '@' && ns.formats['17:3'] === '@' && ns.formats['2:1'] === '@',
     'B11: формат «@» (текст) на всём блоке A1:C17');
  ok(ns.bg['1:1'] === '#1F4E5F' && ns.bg['1:3'] === '#1F4E5F', 'B12: шапка тёмная');
  ok(ns.bg['2:1'] === '#FFE082' && ns.bg['2:3'] === '#FFE082', 'B13: строка «Д» залита #FFE082');
  ok(ns.bg['17:1'] === '#CFD8DC' && ns.bg['17:3'] === '#CFD8DC', 'B14: строка «.» залита #CFD8DC');
  ok(ns.colWidths[1] === 90 && ns.colWidths[2] === 560 && ns.colWidths[3] === 110,
     'B15: ширины колонок 90/560/110');
  ok(ns.getLastRow() === 17, 'B16: getLastRow=17 (стили не раздули диапазон — урок 294)');

  // header значения
  const hdr = ns.getRange(1, 1, 1, 3).getValues()[0];
  ok(hdr[0] === 'код' && hdr[1] === 'название' && hdr[2] === 'цвет_заливки',
     'B17: шапка код/название/цвет_заливки');
}

// ------------------------------------------------------------
console.log('C. Идемпотентность');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  ctx.statusCodesReplace();
  const sheetsBefore = t.ss.sheets.length;
  const res2 = ctx.statusCodesReplace();
  ok(res2.ok === true && res2.skipped === true, 'C1: второй запуск = skip');
  ok(t.ss.sheets.length === sheetsBefore && backupCount(t.ss) === 1,
     'C2: новых листов/резервов не создано');
  const res3 = ctx.statusCodesReplace(true); // force — починка оформления
  ok(res3.ok === true && !res3.skipped, 'C3: force=true перестраивает лист');
  ok(backupCount(t.ss) === 2, 'C4: force создаёт ещё один резерв');
}

// ------------------------------------------------------------
console.log('D. Замена состояния «как у пользователя» (xlsx 03.09.2026)');
// ------------------------------------------------------------
{
  const t = makeTable(USER_LIKE);
  const ctx = makeCtx(t.world);
  const res = ctx.statusCodesReplace();
  ok(res.ok === true, 'D1: ok=true');
  const rows = sheetRows(t.ss, 'Коды_статусов');
  ok(rows.length === 16 && JSON.stringify(rows) === JSON.stringify(ctx.SC_STATUS_CODES),
     'D2: 16 эталонных строк (склейка «Д8, Д7,2» разведена, «?» заменены цветами)');
  ok(JSON.stringify(sheetRows(t.ss, res.backup)) === JSON.stringify(USER_LIKE),
     'D3: прежние 15 строк пользователя — в резерве');
}

// ------------------------------------------------------------
console.log('E. Листа нет — создание');
// ------------------------------------------------------------
{
  const t = makeTable();
  t.ss.deleteSheet(t.ss.getSheetByName('Коды_статусов'));
  const ctx = makeCtx(t.world);
  const res = ctx.statusCodesReplace();
  ok(res.ok === true && res.backup === null, 'E1: создан с нуля, без резерва');
  ok(t.ss.sheets[2].getName() === 'Коды_статусов',
     'E2: позиция 3 (после README и Сотрудников)');
  ok(sheetRows(t.ss, 'Коды_статусов').length === 16, 'E3: 16 строк');
}

// ------------------------------------------------------------
console.log('F. Дубль кода — отклонение ДО изменений');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  const before = JSON.stringify(sheetRows(t.ss, 'Коды_статусов'));
  ctx.SC_STATUS_CODES.push(['Д', 'Дубль', '#000000']);
  const res = ctx.statusCodesReplace();
  ok(res.ok === false && /дубль кода/.test(res.error), 'F1: ошибка про дубль');
  ok(JSON.stringify(sheetRows(t.ss, 'Коды_статусов')) === before,
     'F2: лист НЕ тронут (валидация до записи)');
  ok(backupCount(t.ss) === 0, 'F3: резервов нет');
}

// ------------------------------------------------------------
console.log('G. Потеря записи — самопроверка ловит');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  t.world.dropValues = true;
  const res = ctx.statusCodesReplace();
  ok(res.ok === false && res.errors && res.errors.length > 0,
     'G1: ok=false, расхождения перечислены');
  t.world.dropValues = false;
  ok(backupCount(t.ss) === 1, 'G2: резерв старых данных создан (откат возможен)');
}

// ------------------------------------------------------------
console.log('H. Миграция «О» → «ОТ»');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  const res = ctx.migrateVacationStatus();
  ok(res.ok === true && res.migrated === 2, 'H1: мигрировано ровно 2 записи');
  const entries = t.ss.getSheetByName('Записи_графика');
  const colC = entries.getRange(2, 3, 7, 1).getValues().map(function (r) { return r[0]; });
  ok(colC[0] === 'Д' && colC[3] === 'ОТ' && colC[4] === 'ОБ' && colC[5] === 'д' && colC[6] === 'O',
     'H2: Д/ОТ(старый)/ОБ/д/лат.O не тронуты');
  ok(colC[1] === 'ОТ' && colC[2] === 'ОТ', 'H3: обе «О» → «ОТ»');
  ok(colC[3] === 'ОТ', 'H4: прежняя «ОТ» не задвоена');
  ok(!!res.backup && res.backup.indexOf('Записи_графика_резерв_') === 0,
     'H5: создан резерв-копия листа');
  // в резерве — состояние ДО миграции (обе «О» на месте)
  ok(sheetRows(t.ss, res.backup).filter(function (r) { return r[2] === 'О'; }).length === 2,
     'H6: резерв хранит обе записи «О» (колонка C, до миграции)');
  const res2 = ctx.migrateVacationStatus();
  ok(res2.ok === true && res2.migrated === 0, 'H7: повтор — 0 изменений');
  ok(backupCount(t.ss) === 1, 'H8: повтор не плодит резервы');
}

// ------------------------------------------------------------
console.log('I. Дни_цикла, шаблон 2');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  const res = ctx.updateCycleDaysTemplate2();
  ok(res.ok === true && res.changed === 5, 'I1: 5 замен (дни 1–5)');
  const days = t.ss.getSheetByName('Дни_цикла');
  const vals = days.getRange(2, 1, 13, 3).getValues();
  // порядок строк: t1: 1-5 → индексы 0-4; t2: 6-12 → индексы 5-11; t2 день 8 → 12
  ok(vals[5][2] === 'Д8' && vals[6][2] === 'Д8' && vals[7][2] === 'Д8' && vals[8][2] === 'Д8',
     'I2: дни 1–4 шаблона 2 → Д8');
  ok(vals[9][2] === 'Д7,2', 'I3: день 5 → Д7,2');
  ok(vals[10][2] === '' && vals[11][2] === '' && vals[12][2] === 'д',
     'I4: выходные (пусто) и строчная «д» (день 8) не тронуты');
  ok(vals[0][2] === 'Д' && vals[1][2] === 'Н', 'I5: шаблон 1 не тронут');
  ok(!!res.backup && res.backup.indexOf('Дни_цикла_резерв_') === 0, 'I6: резерв создан');
  const res2 = ctx.updateCycleDaysTemplate2();
  ok(res2.ok === true && res2.changed === 0, 'I7: повтор — 0 изменений');
}

// ------------------------------------------------------------
console.log('J. Диагностика (только чтение)');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  const st = ctx.statusCodesStatus();
  ok(st.ok === true, 'J1: ok=true');
  ok(st.missing.length === 8, 'J2: missing = 8 (Д8,Д7,2,д,н,У,ОВ,ПР,.)');
  ok(JSON.stringify(st.extra) === JSON.stringify(['О', 'П']), 'J3: extra = О, П');
  ok(st.vacationLegacy === 2, 'J4: vacationLegacy = 2');
  ok(st.cycleTemplate2Legacy === 5, 'J5: cycleTemplate2Legacy = 5');
  ok(st.backups.length === 0, 'J6: резервов нет');
  // ничего не изменилось
  ok(sheetRows(t.ss, 'Коды_статусов').length === 10, 'J7: лист не тронут');
  ok(backupCount(t.ss) === 0, 'J8: листов не прибавилось');
}

// ------------------------------------------------------------
console.log('K. Очистка резервов');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  ctx.statusCodesReplace();
  ctx.migrateVacationStatus();
  ctx.updateCycleDaysTemplate2();
  ok(backupCount(t.ss) === 3, 'K1: три резерва после полного деплоя');
  const res = ctx.statusCodesCleanupBackups();
  ok(res.ok === true && res.removed.length === 3, 'K2: удалены все 3');
  ok(backupCount(t.ss) === 0, 'K3: резервов не осталось');
  ok(t.ss.getSheetByName('Коды_статусов') && t.ss.getSheetByName('Записи_графика') &&
     t.ss.getSheetByName('Дни_цикла') && t.ss.getSheetByName('README'),
     'K4: рабочие листы целы');
  ok(t.ss.sheets.length === 9, 'K5: в таблице снова 9 листов');
  const res2 = ctx.statusCodesCleanupBackups();
  ok(res2.removed.length === 0, 'K6: повтор — нечего удалять');
}

// ------------------------------------------------------------
console.log('L. statusCodesDeployAll — оба шага сразу');
// ------------------------------------------------------------
{
  const t = makeTable();
  const ctx = makeCtx(t.world);
  const res = ctx.statusCodesDeployAll();
  ok(res.ok === true && res.steps.length === 2, 'L1: два шага, ok=true');
  ok(sheetRows(t.ss, 'Коды_статусов').length === 16, 'L2: лист заменён');
  const colC = t.ss.getSheetByName('Записи_графика').getRange(2, 3, 7, 1).getValues();
  ok(colC[1][0] === 'ОТ' && colC[2][0] === 'ОТ' && colC[0][0] === 'Д',
     'L3: миграция выполнена, прочее цело');
  ok(backupCount(t.ss) === 2, 'L4: два резерва (лист + записи)');
  // повтор — всё идемпотентно
  const res2 = ctx.statusCodesDeployAll();
  ok(res2.ok === true && res2.steps[0].skipped === true && res2.steps[1].migrated === 0,
     'L5: повтор — оба шага no-op');
  ok(backupCount(t.ss) === 2, 'L6: резервов не прибавилось');
}

// ------------------------------------------------------------
console.log('');
console.log('==========================================');
console.log('task299-mock-test: ' + passed + ' passed / ' + failed + ' failed');
if (failed) {
  console.log('FAILURES:');
  failures.forEach(function (f) { console.log('  - ' + f); });
  process.exit(1);
}
console.log('OK');
