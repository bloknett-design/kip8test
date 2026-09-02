#!/usr/bin/env node
/**
 * task293-mock-test.js — проверка RoleMatrixInit.gs v3 на моках Apps Script.
 *
 * Воспроизводит ошибку пользователя v2:
 *   «Exception: Невозможно закрепить столбцы, в которых содержится
 *    только часть объединенных ячеек. Разделите ячейки или закрепите
 *    все столбцы, содержащие объединенные ячейки.»
 * (setFrozenColumns при существующем merge, пересекающем границу).
 *
 * Два режима:
 *  permissive — merge через границу закрепления РАЗРЕШЁН (ожидаемое
 *    поведение реального Apps Script), НО setFrozenRows/setFrozenColumns
 *    при пересекающем merge бросают исключение (как у пользователя);
 *  strict     — merge через границу ТОЖЕ бросает (если Google запретит
 *    и объединение) — проверяется запасное разбиение _mergeRow().
 *
 * Запуск: node scripts/task293-mock-test.js
 */
'use strict';

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const GS_CODE = fs.readFileSync(path.join(__dirname, 'RoleMatrixInit.gs'), 'utf8');

const USER_ERR_COLS =
  'Exception: Невозможно закрепить столбцы, в которых содержится только часть ' +
  'объединенных ячеек. Разделите ячейки или закрепите все столбцы, содержащие ' +
  'объединенные ячейки.';
const USER_ERR_ROWS =
  'Exception: Невозможно закрепить строки, в которых содержится только часть ' +
  'объединенных ячеек.';

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

// Мок-мир: таблица + листы + диапазоны + глобальные сервисы Apps Script.
function makeWorld(strict) {
  const world = { strict, order: [], logs: [], errInInit: null };

  class MockRange {
    constructor(sheet, row, col, numRows, numCols) {
      this.sh = sheet;
      this.row = row;
      this.col = col;
      this.numRows = numRows;
      this.numCols = numCols;
    }
    _key(dr, dc) {
      return (this.row + (dr || 0)) + ':' + (this.col + (dc || 0));
    }
    crossesColsBoundary(frozen) {
      return frozen > 0 && this.col <= frozen && (this.col + this.numCols - 1) > frozen;
    }
    setValue(v) {
      for (let r = 0; r < this.numRows; r++) {
        for (let c = 0; c < this.numCols; c++) { this.sh.cells[this._key(r, c)] = v; }
      }
      return this;
    }
    setValues(vs) {
      for (let r = 0; r < this.numRows; r++) {
        for (let c = 0; c < this.numCols; c++) { this.sh.cells[this._key(r, c)] = vs[r][c]; }
      }
      return this;
    }
    merge() {
      if (this.numRows !== 1 && this.numCols !== 1) {
        // Apps Script merge() объединяет только однострочные/одноколоночные
        // диапазоны; для прочих нужно mergeAcross/mergeVertically. В скрипте
        // используются только однострочные — контролируем контракт.
        throw new Error('mock: merge() вызван на диапазоне ' + this.numRows + 'x' + this.numCols + ' — Apps Script требует mergeAcross()');
      }
      if (world.strict && this.crossesColsBoundary(this.sh.frozenCols)) {
        throw new Error('Exception: Объединение ячеек через границу закрепления запрещено (strict-мок).');
      }
      this.sh.merges.push({ row: this.row, col: this.col, numRows: this.numRows, numCols: this.numCols });
      world.order.push(this.sh.name + ':merge r' + this.row + ' c' + this.col + ' ' + this.numCols + 'w');
      return this;
    }
    setDataValidation(rule) {
      this.sh.validations.push({ row: this.row, col: this.col, numRows: this.numRows, numCols: this.numCols, rule: rule });
      return this;
    }
    protect() {
      return {
        setDescription() { return this; },
        canSetWarningOnly() { return true; },
        setWarningOnly() { return this; }
      };
    }
    // Остальные сеттеры — цепные заглушки.
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
      this.colWidths = {};
      this.rowHeights = {};
      this.tabColor = null;
    }
    getRange(a, b, c, d) {
      let r;
      if (typeof a === 'string') {
        r = parseA1(a);
      } else if (c === undefined) {
        r = { row: a, col: b, numRows: 1, numCols: 1 };
      } else {
        r = { row: a, col: b, numRows: c, numCols: d };
      }
      return new MockRange(this, r.row, r.col, r.numRows, r.numCols);
    }
    setFrozenRows(n) {
      for (let i = 0; i < this.merges.length; i++) {
        const m = this.merges[i];
        if (m.row <= n && (m.row + m.numRows - 1) > n) { throw new Error(USER_ERR_ROWS); }
      }
      this.frozenRows = n;
      world.order.push(this.name + ':freezeRows=' + n);
      return this;
    }
    setFrozenColumns(n) {
      for (let i = 0; i < this.merges.length; i++) {
        const m = this.merges[i];
        if (m.col <= n && (m.col + m.numCols - 1) > n) { throw new Error(USER_ERR_COLS); }
      }
      this.frozenCols = n;
      world.order.push(this.name + ':freezeCols=' + n);
      return this;
    }
    getFrozenColumns() { return this.frozenCols; }
    getFrozenRows() { return this.frozenRows; }
    setColumnWidth(c, w) { this.colWidths[c] = w; return this; }
    setRowHeight(r, h) { this.rowHeights[r] = h; return this; }
    setTabColor(c) { this.tabColor = c; return this; }
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
    deleteSheet(s) { delete this.sheets[s.name]; }
  };

  const sandbox = {
    SpreadsheetApp: {
      getActive() { return ss; },
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
  sandbox.__ss = ss;
  sandbox.__world = world;
  vm.createContext(sandbox);
  vm.runInContext(GS_CODE, sandbox, { filename: 'RoleMatrixInit.gs' });
  return { sandbox, ss, world };
}

function checkNoMergeCrossesBoundary(sheet, frozen, label) {
  const crossing = sheet.merges.filter(function (m) {
    return frozen > 0 && m.col <= frozen && (m.col + m.numCols - 1) > frozen;
  });
  ok(crossing.length === 0, label + ': ни один merge не пересекает границу закрепления (найдено ' + crossing.length + ')');
}

function checkRowMergedAcross(sheet, row, lastCol, label) {
  const rowMerges = sheet.merges.filter(function (m) { return m.row === row; });
  let covered = 0;
  for (let i = 0; i < rowMerges.length; i++) { covered += rowMerges[i].numCols; }
  ok(rowMerges.length >= 1 && covered >= lastCol,
    label + ': строка ' + row + ' объединена по всей ширине (' + covered + '/' + lastCol + ' колонок, блоков: ' + rowMerges.length + ')');
}

function runMode(modeName, strict) {
  console.log('\n=== Режим ' + modeName + ' ===');
  const t = makeWorld(strict);
  const { sandbox, ss, world } = t;

  // --- 1. Полный прогон roleMatrixInit без исключений ---
  let result = null;
  let initErr = null;
  try {
    result = sandbox.roleMatrixInit();
  } catch (e) {
    initErr = e;
  }
  ok(initErr === null, modeName + ': roleMatrixInit() выполнен без исключений' + (initErr ? ' — получено: ' + initErr.message : ''));
  if (initErr) { return; }
  ok(/Готово\. Созданы листы: matrix, permissions, roles\. Прав: 13, ролей: 12\./.test(String(result)),
    modeName + ': итоговое сообщение корректно («Готово…Прав: 13, ролей: 12»)');

  const matrix = ss.sheets.matrix;
  const permissions = ss.sheets.permissions;
  const roles = ss.sheets.roles;
  ok(!!matrix && !!permissions && !!roles, modeName + ': созданы все 3 листа');

  // --- 2. Закрепление ---
  ok(matrix.frozenRows === 5 && matrix.frozenCols === 2, modeName + ': matrix закреплена 5 строк × 2 колонки');
  ok(permissions.frozenRows === 4 && permissions.frozenCols === 2, modeName + ': permissions закреплена 4×2');
  ok(roles.frozenRows === 4 && roles.frozenCols === 2, modeName + ': roles закреплена 4×2');

  // --- 3. Порядок операций: закрепление ДО первого merge на каждом листе ---
  ['matrix', 'permissions', 'roles'].forEach(function (name) {
    const freezeIdx = world.order.findIndex(function (ev) { return ev.indexOf(name + ':freezeCols=') === 0; });
    const mergeIdx = world.order.findIndex(function (ev) { return ev.indexOf(name + ':merge ') === 0; });
    ok(freezeIdx !== -1 && mergeIdx !== -1 && freezeIdx < mergeIdx,
      modeName + ': ' + name + ' — закрепление (шаг ' + freezeIdx + ') раньше первого объединения (шаг ' + mergeIdx + ')');
  });

  // --- 4. Объединения строк 1-2 ---
  // В permissive-режиме (реальный Apps Script) объединение на всю ширину
  // ЗАКОННО пересекает границу закрепления (критично лишь ПОРЯДОК:
  // закрепление до объединения — проверено выше); в strict-режиме
  // контракт: ни один merge не пересекает границу.
  if (strict) {
    checkNoMergeCrossesBoundary(matrix, 2, modeName + ' matrix');
    checkNoMergeCrossesBoundary(permissions, 2, modeName + ' permissions');
    checkNoMergeCrossesBoundary(roles, 2, modeName + ' roles');
  }
  // И в строгом, и в разрешающем режимах строка заголовка/инструкции покрыта
  checkRowMergedAcross(matrix, 1, 15, modeName + ' matrix');
  checkRowMergedAcross(matrix, 2, 15, modeName + ' matrix');
  checkRowMergedAcross(permissions, 1, 8, modeName + ' permissions');
  checkRowMergedAcross(permissions, 2, 8, modeName + ' permissions');
  checkRowMergedAcross(roles, 1, 5, modeName + ' roles');
  checkRowMergedAcross(roles, 2, 5, modeName + ' roles');

  // --- 5. Данные matrix: совпадение с INIT_* ---
  const INIT_ROLES = sandbox.INIT_ROLES;
  const INIT_PERMISSIONS = sandbox.INIT_PERMISSIONS;
  const INIT_MATRIX = sandbox.INIT_MATRIX;
  let dataOk = true;
  for (let r = 0; r < INIT_ROLES.length; r++) {
    const row = 6 + r;
    const rid = INIT_ROLES[r][0];
    if (matrix.cells[row + ':1'] !== rid) { dataOk = false; }
    if (matrix.cells[row + ':2'] !== INIT_ROLES[r][1]) { dataOk = false; }
    for (let c = 0; c < INIT_PERMISSIONS.length; c++) {
      const expect = INIT_MATRIX[rid][INIT_PERMISSIONS[c][0]] === true;
      if (matrix.cells[row + ':' + (3 + c)] !== expect) { dataOk = false; }
    }
  }
  ok(dataOk, modeName + ': matrix — все 12×15 значений совпадают с INIT_MATRIX');

  // --- 6. Чекбоксы ---
  const dv = matrix.validations.filter(function (v) {
    return v.row === 6 && v.col === 3 && v.numRows === 12 && v.numCols === 13 && v.rule && v.rule.checkbox;
  });
  ok(dv.length === 1, modeName + ': matrix — чекбокс-валидация на C6:O17');

  // --- 7. Данные permissions/roles ---
  let permOk = true;
  for (let i = 0; i < INIT_PERMISSIONS.length; i++) {
    for (let c = 0; c < 8; c++) {
      if (permissions.cells[(5 + i) + ':' + (1 + c)] !== INIT_PERMISSIONS[i][c]) { permOk = false; }
    }
  }
  ok(permOk, modeName + ': permissions — все 13×8 значений совпадают с INIT_PERMISSIONS');
  let rolesOk = true;
  for (let i = 0; i < INIT_ROLES.length; i++) {
    for (let c = 0; c < 5; c++) {
      if (roles.cells[(5 + i) + ':' + (1 + c)] !== INIT_ROLES[i][c]) { rolesOk = false; }
    }
  }
  ok(rolesOk, modeName + ': roles — все 12×5 значений совпадают с INIT_ROLES');

  // --- 8. Идемпотентность ---
  let result2 = sandbox.roleMatrixInit();
  ok(/уже существует/.test(String(result2)) && Object.keys(ss.sheets).length === 3,
    modeName + ': повторный запуск — выход без изменений (листов по-прежнему 3)');

  // --- 9. Частичная инициализация → подсказка cleanup ---
  const t2 = makeWorld(strict);
  t2.ss.insertSheet('matrix');
  let partialErr = null;
  try { t2.sandbox.roleMatrixInit(); } catch (e) { partialErr = e; }
  ok(partialErr !== null && /roleMatrixCleanup/.test(String(partialErr && partialErr.message)),
    modeName + ': частичная инициализация распознана, подсказка про roleMatrixCleanup');
  const cleanMsg = t2.sandbox.roleMatrixCleanup();
  ok(/Удалены листы: matrix/.test(String(cleanMsg)), modeName + ': cleanup удаляет недосозданный лист');
  const res3 = t2.sandbox.roleMatrixInit();
  ok(/Готово/.test(String(res3)), modeName + ': после cleanup init проходит до конца');
}

runMode('permissive (реальный Apps Script: merge через границу разрешён)', false);
runMode('strict (гипотеза: merge через границу тоже запрещён)', true);

console.log('\n==========================================');
console.log('Итог: ' + passed + ' passed / ' + failed + ' failed');
if (failed > 0) {
  console.log('Проваленные проверки:');
  failures.forEach(function (f) { console.log('  - ' + f); });
  process.exit(1);
}
console.log('OK');
