#!/usr/bin/env node
/**
 * task293-mock-test.js — проверка RoleMatrixInit.gs v4 на моках Apps Script.
 *
 * Моделирует ДОКАЗАННОЕ поведение реального Google Apps Script
 * (по журналам пользователя v2/v3 и скачиванию таблицы после v3):
 *
 *  (1) merge() диапазона, пересекающего границу закрепления СТОЛБЦОВ,
 *      ПРОХОДИТ без исключения, но лист становится НЕОТОБРАЖАЕМЫМ:
 *      UI и экспорт xlsx показывают его ПУСТЫМ — симптом пользователя
 *      после v3 («листы без содержимого и заголовков»; подтверждено
 *      скачиванием: листы есть, закрепления 5×2/4×2 есть, ячеек — 0);
 *  (2) setFrozenRows/setFrozenColumns при ЧАСТИЧНО пересекающих
 *      объединениях — исключение (ошибка v2);
 *  (3) protect() диапазона через границу закрепления столбцов —
 *      исключение «Нельзя объединять закрепленные и незакрепленные
 *      столбцы» (3 предупреждения в журнале v3);
 *  (4) чтение: getValue/getValues/getLastRow/getLastColumn/
 *      getMergedRanges/getFrozenRows/getFrozenColumns.
 *
 * Запуск: node scripts/task293-mock-test.js
 */
'use strict';

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const GS_CODE = fs.readFileSync(path.join(__dirname, 'RoleMatrixInit.gs'), 'utf8');

const USER_ERR_FREEZE_COLS =
  'Exception: Невозможно закрепить столбцы, в которых содержится только часть ' +
  'объединенных ячеек. Разделите ячейки или закрепите все столбцы, содержащие ' +
  'объединенные ячейки.';
const USER_ERR_FREEZE_ROWS =
  'Exception: Невозможно закрепить строки, в которых содержится только часть ' +
  'объединенных ячеек.';
const USER_ERR_PROTECT =
  'Exception: Нельзя объединять закрепленные и незакрепленные столбцы.';

let passed = 0;
let failed = 0;
const failures = [];
function ok(cond, name) {
  if (cond) { passed++; } else { failed++; failures.push(name); console.error('  FAIL: ' + name); }
}

function colToNum(letters) {
  let n = 0;
  for (let i = 0; i < letters.length; i++) { n = n * 26 + (letters.charCodeAt(i) - 64); }
  return n;
}
function parseA1(a1) {
  const m = /^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$/.exec(a1);
  if (!m) { throw new Error('mock: bad A1 notation "' + a1 + '"'); }
  const c1 = colToNum(m[1]);
  const r1 = parseInt(m[2], 10);
  const c2 = m[3] ? colToNum(m[3]) : c1;
  const r2 = m[4] ? parseInt(m[4], 10) : r1;
  return { row: r1, col: c1, numRows: r2 - r1 + 1, numCols: c2 - c1 + 1 };
}

function makeWorld(opts) {
  opts = opts || {};
  const world = { logs: [], order: [] };

  class MockMergedRange {
    constructor(row, col, numRows, numCols) {
      this._r = row; this._c = col; this._nr = numRows; this._nc = numCols;
    }
    getRow() { return this._r; }
    getColumn() { return this._c; }
    getNumRows() { return this._nr; }
    getNumColumns() { return this._nc; }
  }

  class MockRange {
    constructor(sheet, row, col, numRows, numCols) {
      this.sh = sheet;
      this.row = row; this.col = col;
      this.numRows = numRows; this.numCols = numCols;
    }
    _key(dr, dc) { return (this.row + (dr || 0)) + ':' + (this.col + (dc || 0)); }
    crossesColsBoundary(frozen) {
      return frozen > 0 && this.col <= frozen && (this.col + this.numCols - 1) > frozen;
    }
    setValue(v) {
      if (opts.dropValues) { return this; }
      for (let r = 0; r < this.numRows; r++) {
        for (let c = 0; c < this.numCols; c++) { this.sh.cells[this._key(r, c)] = v; }
      }
      return this;
    }
    setValues(vs) {
      if (opts.dropValues) { return this; }
      for (let r = 0; r < this.numRows; r++) {
        for (let c = 0; c < this.numCols; c++) { this.sh.cells[this._key(r, c)] = vs[r][c]; }
      }
      return this;
    }
    getValue() {
      const v = this.sh.cells[this._key(0, 0)];
      return v === undefined ? '' : v;
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
    merge() {
      if (this.numRows !== 1) {
        throw new Error('mock: merge() только для однострочных диапазонов');
      }
      // Реальность v3: объединение через границу закрепления столбцов
      // ПРОХОДИТ молча, но лист становится неотображаемым.
      const crossing = this.crossesColsBoundary(this.sh.frozenCols);
      this.sh.merges.push({ row: this.row, col: this.col, numRows: this.numRows, numCols: this.numCols });
      if (crossing) { this.sh.poisoned = true; }
      world.order.push(this.sh.name + ':merge r' + this.row + ' c' + this.col + ' ' + this.numCols + 'w');
      return this;
    }
    getMergedRanges() {
      const res = [];
      for (const m of this.sh.merges) {
        const intersects = m.row <= this.row + this.numRows - 1 && (m.row + m.numRows - 1) >= this.row &&
          m.col <= this.col + this.numCols - 1 && (m.col + m.numCols - 1) >= this.col;
        if (intersects) { res.push(new MockMergedRange(m.row, m.col, m.numRows, m.numCols)); }
      }
      return res;
    }
    setDataValidation(rule) {
      this.sh.validations.push({ row: this.row, col: this.col, numRows: this.numRows, numCols: this.numCols, rule: rule });
      return this;
    }
    protect() {
      // Реальность v3: protect() диапазона через границу закрепления
      // столбцов бросает исключение.
      if (this.crossesColsBoundary(this.sh.frozenCols)) {
        throw new Error(USER_ERR_PROTECT);
      }
      return {
        setDescription() { return this; },
        canSetWarningOnly() { return true; },
        setWarningOnly() { return this; }
      };
    }
    setBackground() { return this; }
    setFontWeight() { return this; }
    setFontSize() { return this; }
    setFontColor() { return this; }
    setFontStyle() { return this; }
    setFontFamily() { return this; }
    setVerticalAlignment() { return this; }
    setHorizontalAlignment() { return this; }
    setWrap() { return this; }
    setBorder() { return this; }
  }

  class MockSheet {
    constructor(name) {
      this.name = name;
      this.frozenRows = 0;
      this.frozenCols = 0;
      this.merges = [];
      this.cells = {};
      this.validations = [];
      this.poisoned = false;
    }
    getRange(a, b, c, d) {
      let r;
      if (typeof a === 'string') { r = parseA1(a); }
      else if (c === undefined) { r = { row: a, col: b, numRows: 1, numCols: 1 }; }
      else { r = { row: a, col: b, numRows: c, numCols: d }; }
      return new MockRange(this, r.row, r.col, r.numRows, r.numCols);
    }
    setFrozenRows(n) {
      for (const m of this.merges) {
        if (m.row <= n && (m.row + m.numRows - 1) > n) { throw new Error(USER_ERR_FREEZE_ROWS); }
      }
      this.frozenRows = n;
      world.order.push(this.name + ':freezeRows=' + n);
      return this;
    }
    setFrozenColumns(n) {
      for (const m of this.merges) {
        if (m.col <= n && (m.col + m.numCols - 1) > n) { throw new Error(USER_ERR_FREEZE_COLS); }
      }
      this.frozenCols = n;
      world.order.push(this.name + ':freezeCols=' + n);
      return this;
    }
    getFrozenRows() { return this.frozenRows; }
    getFrozenColumns() { return this.frozenCols; }
    getLastRow() {
      let m = 0;
      for (const k in this.cells) { m = Math.max(m, parseInt(k.split(':')[0], 10)); }
      return m;
    }
    getLastColumn() {
      let m = 0;
      for (const k in this.cells) { m = Math.max(m, parseInt(k.split(':')[1], 10)); }
      return m;
    }
    setColumnWidth() { return this; }
    setRowHeight() { return this; }
    setTabColor() { return this; }
  }

  const ss = {
    sheets: {},
    getSheetByName(n) { return this.sheets[n] || null; },
    insertSheet(n) {
      const s = new MockSheet(n);
      this.sheets[n] = s;
      world.order.push(n + ':insert');
      return s;
    },
    deleteSheet(s) { delete this.sheets[s.name]; },
    getName() { return 'KIP8_Access (мок)'; },
    getUrl() { return 'https://docs.google.com/spreadsheets/d/mock-access/edit'; }
  };

  const sandbox = {
    SpreadsheetApp: {
      getActive() { return null; },
      openById() { return ss; },
      newDataValidation() {
        return {
          requireCheckbox() { return this; },
          setAllowInvalid() { return this; },
          build() { return { checkbox: true }; }
        };
      },
      BorderStyle: { SOLID: 'SOLID', SOLID_MEDIUM: 'SOLID_MEDIUM' }
    },
    Session: { getScriptTimeZone() { return 'Asia/Novosibirsk'; } },
    Utilities: { formatDate() { return '02.09.2026'; } },
    Logger: { log(m) { world.logs.push(String(m)); } },
    console: { log() {}, error() {} }
  };
  vm.createContext(sandbox);
  vm.runInContext(GS_CODE, sandbox, { filename: 'RoleMatrixInit.gs' });
  return { sandbox, ss, world };
}

// Хелперы-инварианты
function anyMergeCrossesBoundary(sheet) {
  const f = sheet.frozenCols;
  if (f <= 0) { return false; }
  return sheet.merges.some(m => m.col <= f && (m.col + m.numCols - 1) > f);
}
function uiCells(sheet) { return sheet.poisoned ? {} : sheet.cells; }
function rowMergeBlocks(sheet, row) {
  return sheet.merges.filter(m => m.row === row);
}

// ==========================================================================
// T1: чистый прогон v4
// ==========================================================================
console.log('=== T1: init v4 — чистый прогон ===');
const t1 = makeWorld();
let res1 = null, err1 = null;
try { res1 = t1.sandbox.roleMatrixInit(); } catch (e) { err1 = e; }
ok(err1 === null, 'T1: init() без исключений' + (err1 ? ' — ' + err1.message : ''));
if (err1 === null) {
  ok(/^Готово\. Созданы листы: matrix, permissions, roles\. Прав: 13, ролей: 12\./.test(String(res1)),
    'T1: сообщение «Готово…Прав: 13, ролей: 12»');
  ok(/Самопроверка чтения: matrix 17×15 \(A6='zapret'\)/.test(String(res1)),
    'T1: самопроверка в сообщении: matrix 17×15 (A6=\'zapret\')');
  ok(/permissions 17×8, roles 16×5 — ОК\./.test(String(res1)),
    'T1: самопроверка permissions 17×8, roles 16×5 — ОК');
}
ok(t1.world.logs.some(l => /Целевая таблица: «KIP8_Access \(мок\)»/.test(l)),
  'T1: в журнале адрес целевой таблицы');
ok(!t1.world.logs.some(l => /Защита диапазона не установлена/.test(l)),
  'T1: НЕТ предупреждений защиты (симптом v3 устранён)');
ok(!t1.world.logs.some(l => /Полное объединение/.test(l)),
  'T1: НЕТ сообщений о разбиении объединений');

const M = t1.ss.sheets.matrix, P = t1.ss.sheets.permissions, R = t1.ss.sheets.roles;
ok(!!M && !!P && !!R, 'T1: созданы все 3 листа');
ok(!M.poisoned && !P.poisoned && !R.poisoned, 'T1: листы ОТОБРАЖАЕМЫЕ (не «повреждены»)');
ok(M.frozenCols === 0 && P.frozenCols === 0 && R.frozenCols === 0,
  'T1: закрепление столбцов НЕ используется (как в users/sessions)');
ok(M.frozenRows === 5 && P.frozenRows === 4 && R.frozenRows === 4,
  'T1: закрепление строк 5/4/4');
ok(!anyMergeCrossesBoundary(M) && !anyMergeCrossesBoundary(P) && !anyMergeCrossesBoundary(R),
  'T1: ни одно объединение не пересекает границу закрепления');

// строки 1–2 объединены на всю ширину одним блоком (домашний стиль users)
ok(rowMergeBlocks(M, 1).length === 1 && M.merges.find(m => m.row === 1).numCols === 15 &&
   rowMergeBlocks(M, 2).length === 1 && M.merges.find(m => m.row === 2).numCols === 15,
  'T1: matrix — строки 1–2 объединены на всю ширину (A1:O1, A2:O2)');
ok(rowMergeBlocks(P, 1).length === 1 && P.merges.find(m => m.row === 1).numCols === 8,
  'T1: permissions — строка 1 объединена A1:H1');
ok(rowMergeBlocks(R, 1).length === 1 && R.merges.find(m => m.row === 1).numCols === 5,
  'T1: roles — строка 1 объединена A1:E1');

// данные
const INIT_ROLES = t1.sandbox.INIT_ROLES;
const INIT_PERMISSIONS = t1.sandbox.INIT_PERMISSIONS;
const INIT_MATRIX = t1.sandbox.INIT_MATRIX;
let dataOk = true;
for (let r = 0; r < INIT_ROLES.length; r++) {
  const row = 6 + r;
  const rid = INIT_ROLES[r][0];
  if (M.cells[row + ':1'] !== rid) { dataOk = false; }
  if (M.cells[row + ':2'] !== INIT_ROLES[r][1]) { dataOk = false; }
  for (let c = 0; c < INIT_PERMISSIONS.length; c++) {
    if (M.cells[row + ':' + (3 + c)] !== (INIT_MATRIX[rid][INIT_PERMISSIONS[c][0]] === true)) { dataOk = false; }
  }
}
ok(dataOk, 'T1: matrix — все 12×15 значений совпадают с INIT_MATRIX');
let headOk = true;
for (let c = 0; c < INIT_PERMISSIONS.length; c++) {
  if (M.cells['4:' + (3 + c)] !== INIT_PERMISSIONS[c][0]) { headOk = false; }
  if (M.cells['5:' + (3 + c)] !== INIT_PERMISSIONS[c][1]) { headOk = false; }
}
ok(headOk, 'T1: matrix — строки 4–5 (ID и названия прав)');
let permOk = true;
for (let i = 0; i < INIT_PERMISSIONS.length; i++) {
  for (let c = 0; c < 8; c++) {
    if (P.cells[(5 + i) + ':' + (1 + c)] !== INIT_PERMISSIONS[i][c]) { permOk = false; }
  }
}
ok(permOk, 'T1: permissions — все 13×8 значений');
let rolesOk = true;
for (let i = 0; i < INIT_ROLES.length; i++) {
  for (let c = 0; c < 5; c++) {
    if (R.cells[(5 + i) + ':' + (1 + c)] !== INIT_ROLES[i][c]) { rolesOk = false; }
  }
}
ok(rolesOk, 'T1: roles — все 12×5 значений');

ok(M.validations.some(v => v.row === 6 && v.col === 3 && v.numRows === 12 && v.numCols === 13 && v.rule && v.rule.checkbox),
  'T1: matrix — чекбоксы C6:O17');
ok(M.getLastRow() === 17 && P.getLastRow() === 17 && R.getLastRow() === 16,
  'T1: getLastRow 17/17/16');
ok(Object.keys(uiCells(M)).length >= 200,
  'T1: в UI-представлении matrix есть все данные (лист не пустой)');

// ==========================================================================
// T2: идемпотентность
// ==========================================================================
console.log('=== T2: идемпотентность ===');
const cellsBefore = Object.keys(M.cells).length;
const res2 = t1.sandbox.roleMatrixInit();
ok(/уже существует/.test(String(res2)) && Object.keys(t1.ss.sheets).length === 3,
  'T2: повторный запуск — выход без изменений');
ok(Object.keys(M.cells).length === cellsBefore, 'T2: данные не тронуты');

// ==========================================================================
// T3: частичная инициализация → подсказка cleanup
// ==========================================================================
console.log('=== T3: частичная инициализация ===');
const t3 = makeWorld();
t3.ss.insertSheet('matrix');
let perr = null;
try { t3.sandbox.roleMatrixInit(); } catch (e) { perr = e; }
ok(perr !== null && /roleMatrixCleanup/.test(String(perr && perr.message)),
  'T3: частичная инициализация распознана');
ok(/Удалены листы: matrix/.test(String(t3.sandbox.roleMatrixCleanup())),
  'T3: cleanup удаляет недосозданный лист');
ok(/Готово/.test(String(t3.sandbox.roleMatrixInit())), 'T3: после cleanup init проходит до конца');

// ==========================================================================
// T4: текущее состояние пользователя (повреждённые листы v3):
//     status бьёт тревогу, cleanup лечит, init пересоздаёт здоровые
// ==========================================================================
console.log('=== T4: повреждённые листы v3 → диагностика и лечение ===');
const t4 = makeWorld();
const widths = { matrix: 15, permissions: 8, roles: 5 };
Object.keys(widths).forEach(function (n) {
  const sh = t4.ss.insertSheet(n);
  sh.setFrozenRows(n === 'matrix' ? 5 : 4);   // v3: закрепление прошло
  sh.setFrozenColumns(2);                      // (объединений ещё нет)
  sh.getRange(1, 1, 1, widths[n]).merge();     // v3: merge «прошёл» молча…
  sh.getRange(4, 1, 1, widths[n]).setValues([new Array(widths[n]).fill('x')]); // данные «записаны»
});
ok(t4.ss.sheets.matrix.poisoned === true, 'T4: модель воспроизводит повреждение v3 (merge через границу)');
const st4 = String(t4.sandbox.roleMatrixStatus());
ok((st4.match(/ПОВРЕЖДЁН/g) || []).length === 3, 'T4: status помечает все 3 листа как ПОВРЕЖДЁННЫЕ');
const cl4 = String(t4.sandbox.roleMatrixCleanup());
ok(/Удалены листы: matrix, permissions, roles/.test(cl4), 'T4: cleanup удаляет повреждённые листы');
const res4 = String(t4.sandbox.roleMatrixInit());
ok(/Готово/.test(res4) && t4.ss.sheets.matrix.poisoned === false,
  'T4: после cleanup+init — здоровые отображаемые листы');
ok(/— ОК\./.test(res4), 'T4: самопроверка успешна');

// ==========================================================================
// T4b: лист с лишним закреплением столбцов (без повреждения) → подсказка
// ==========================================================================
console.log('=== T4b: лишнее закрепление столбцов ===');
const t4b = makeWorld();
const shb = t4b.ss.insertSheet('matrix');
shb.setFrozenRows(5);
shb.setFrozenColumns(2);
shb.getRange(4, 1, 1, 15).setValues([['role_id', 'role_name'].concat(new Array(13).fill('p'))]);
const stb = String(t4b.sandbox.roleMatrixStatus());
ok(/закрепление столбцов \(2\) в v4 не используется/.test(stb),
  'T4b: status подсказывает про закрепление столбцов вне v4');
t4b.sandbox.roleMatrixCleanup();
ok(/Готово/.test(String(t4b.sandbox.roleMatrixInit())), 'T4b: cleanup+init исправляет');

// ==========================================================================
// T5: status на здоровом состоянии (после T1)
// ==========================================================================
console.log('=== T5: status на здоровом состоянии ===');
const st5 = String(t1.sandbox.roleMatrixStatus());
ok(/Таблица: «KIP8_Access \(мок\)»/.test(st5), 'T5: заголовок с адресом таблицы');
ok(/matrix: 17×15, закрепление 5 стр\. × 0 кол\. — ОК/.test(st5), 'T5: matrix — ОК с размерами');
ok(/permissions: 17×8, закрепление 4 стр\. × 0 кол\. — ОК/.test(st5), 'T5: permissions — ОК');
ok(/roles: 16×5, закрепление 4 стр\. × 0 кол\. — ОК/.test(st5), 'T5: roles — ОК');
ok(!/ПОВРЕЖДЁН|ПУСТОЙ|ОТСУТСТВУЕТ/.test(st5), 'T5: без тревог');

// ==========================================================================
// T6: «тихая» потеря данных → самопроверка ловит
// ==========================================================================
console.log('=== T6: тихая потеря данных ===');
const t6 = makeWorld({ dropValues: true });
let verr = null;
try { t6.sandbox.roleMatrixInit(); } catch (e) { verr = e; }
ok(verr !== null && /Самопроверка после создания НЕ ПРОШЛА/.test(String(verr && verr.message)),
  'T6: тихая потеря данных ловится самопроверкой');

// ==========================================================================
// T7: регрессионная модель v3 — «успешный» merge через границу
//     делает лист пустым в UI/экспорте
// ==========================================================================
console.log('=== T7: регрессия — модель провала v3 ===');
const t7 = makeWorld();
const sh7 = t7.ss.insertSheet('x');
sh7.setFrozenRows(5);
sh7.setFrozenColumns(2);
sh7.getRange(1, 1, 1, 15).merge();
sh7.getRange('A6').setValue('zapret');
ok(sh7.poisoned === true, 'T7: merge через границу «проходит», но помечает лист повреждённым');
ok(Object.keys(uiCells(sh7)).length === 0,
  'T7: UI/экспорт такого листа — ПУСТОЙ (симптом пользователя после v3)');

console.log('\n==========================================');
console.log('Итог: ' + passed + ' passed / ' + failed + ' failed');
if (failed > 0) {
  console.log('Проваленные проверки:');
  failures.forEach(f => console.log('  - ' + f));
  process.exit(1);
}
console.log('OK');
