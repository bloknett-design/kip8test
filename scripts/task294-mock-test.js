#!/usr/bin/env node
/**
 * task294-mock-test.js — мок-тест RoleMatrix.gs (Этап 2, Task 294).
 *
 * МЕТОД: Apps Script не запускается вне Google, поэтому его окружение
 * моделируется в Node.js (vm.createContext). Моки повторяют ДОКАЗАННОЕ
 * поведение API, а ДАННЫЕ — сняты с реальной таблицы KIP8_Access
 * скачиванием 02.09.2026 (экспорт xlsx после успешного запуска
 * RoleMatrixInit v4 у пользователя), включая «стилевой холст»
 * A1:Z1000 (пустые ячейки со стилями) — из-за него getLastRow()
 * возвращает 1000, getLastColumn() — 26, хотя данных только 17×15.
 *
 * Проверки:
 *   T1  чтение всех 12 реальных ролей → сверка granted с таблицей;
 *   T2  «Админ» всегда все права (кроме kipios.restricted) + admin.panel;
 *   T3  «Админ» с полностью снятой матрицей → всё равно все права;
 *   T4  hasPermission: точечные true/false/неизвестное право;
 *   T5  динамичность: добавили роль «Монтажник» + право reports.view;
 *   T6  неизвестная роль → fail-closed;
 *   T7  лист matrix отсутствует → fail-closed + подсказка Task 293;
 *   T8  email → роль (users) → права; регистр/пробелы email; неизвестный;
 *   T9  кэш: повторное чтение из кэша; инвалидация; битый JSON в кэше;
 *   T10 регистр/пробелы названия роли; поиск по role_id;
 *   T11 ловушка getLast* (холст 1000×26): нет лишних ролей/прав;
 *   T12 мусор в чекбоксах: 'TRUE'→true, 'yes'/''/0→false;
 *   T13 users: колонки email/role найдены при сдвинутой шапке;
 *   T14 реальные пользователи: bloknet@bk.ru → Админ → все права;
 *       shaman00986@gm… → ИТР ИОС → фактический набор из таблицы.
 */

'use strict';

const fs = require('fs');
const vm = require('vm');
const path = require('path');

// ==========================================================================
// РЕАЛЬНЫЕ ДАННЫЕ (сняты с KIP8_Access 02.09.2026, экспорт xlsx)
// ==========================================================================

const REAL_PERMS = [
  'calc.view', 'library.view', 'kipios.view', 'kipios.restricted',
  'cablejournal.edit', 'admin.panel', 'secret.view', 'whatsnew.view',
  'charts.view', 'flowmeter.view', 'flowmeter.input',
  'workschedule.view', 'workschedule.edit'
];

// matrix r6..r17: [role_id, Название, ...13 чекбоксов]
const REAL_ROLES = [
  ['zapret',       'Запрет',           0,0,0,0,0,0,0,0,0,0,0,0,0],
  ['common',       'Общий доступ',     1,0,0,0,0,0,0,0,0,0,0,0],
  ['itr_tokem',    'ИТР ТОКЕМ',        1,0,0,1,0,0,0,1,0,0,0,0,0],
  ['kip8',         'КИП8',             1,1,0,0,0,0,1,1,0,0,0,0,0],
  ['kip8_pro',     'КИП8 pro',         1,1,0,0,0,0,1,1,0,1,0,0,0],
  ['kip_ios',      'КИП ИОС',          1,1,1,0,0,0,1,1,0,0,0,0,0],
  ['kip_ios_pro',  'КИП ИОС pro',      1,1,1,0,1,0,1,1,0,0,0,0,0],
  ['kip_ios_duty', 'КИП ИОС дежурный', 1,1,1,0,0,0,1,1,0,1,1,0,0],
  ['itr8',         'ИТР8',             1,1,1,0,0,0,1,1,0,1,0,0,0],
  ['itr8_pro',     'ИТР8 pro',         1,1,1,0,0,0,1,1,0,1,0,1,0],
  ['itr_ios',      'ИТР ИОС',          1,1,1,0,1,0,1,1,0,1,1,0,0],
  ['admin',        'Админ',            1,1,1,0,1,1,1,1,1,1,1,1,1]
];

// Ожидаемые наборы прав (грант = индексы TRUE), для сверок T1.
const EXPECT_GRANTS = {
  'Запрет': [],
  'Общий доступ': ['calc.view'],
  'ИТР ТОКЕМ': ['calc.view', 'kipios.restricted', 'whatsnew.view'],
  'КИП8': ['calc.view', 'library.view', 'secret.view', 'whatsnew.view'],
  'КИП8 pro': ['calc.view', 'library.view', 'secret.view', 'whatsnew.view', 'flowmeter.view'],
  'КИП ИОС': ['calc.view', 'library.view', 'kipios.view', 'secret.view', 'whatsnew.view'],
  'КИП ИОС pro': ['calc.view', 'library.view', 'kipios.view', 'cablejournal.edit', 'secret.view', 'whatsnew.view'],
  'КИП ИОС дежурный': ['calc.view', 'library.view', 'kipios.view', 'secret.view', 'whatsnew.view', 'flowmeter.view', 'flowmeter.input'],
  'ИТР8': ['calc.view', 'library.view', 'kipios.view', 'secret.view', 'whatsnew.view', 'flowmeter.view'],
  'ИТР8 pro': ['calc.view', 'library.view', 'kipios.view', 'secret.view', 'whatsnew.view', 'flowmeter.view', 'workschedule.view'],
  'ИТР ИОС': ['calc.view', 'library.view', 'kipios.view', 'cablejournal.edit', 'secret.view', 'whatsnew.view', 'flowmeter.view', 'flowmeter.input'],
  // «Админ»: по правилу «всегда все права, кроме kipios.restricted»:
  'Админ': ['calc.view', 'library.view', 'kipios.view', 'cablejournal.edit', 'admin.panel', 'secret.view', 'whatsnew.view', 'charts.view', 'flowmeter.view', 'flowmeter.input', 'workschedule.view', 'workschedule.edit']
};

// users: r4 = [ID, email, role, login_status, last_login, name]; r5+ реальные
const REAL_USERS_ROWS = [
  ['ID', 'email', 'role', 'login_status', 'last_login', 'name'],
  [1,  'bloknett@gmail.com',   'Админ',    'вход выполнен', '2026-08-29 20:xx', 'Галкин'],
  [3,  'bloknet@bk.ru',        'Админ',    'вход выполнен', '2026-08-29 08:xx', 'desktop_home_t'],
  [4,  'blooknet@yandex.ru',   'Админ',    'вход выполнен', '2026-08-29 08:xx', 'desktop_work_t'],
  [2,  'bloknetm@gmail.com',   'Админ',    'вход выполнен', '2026-08-29 19:xx', 'mobile_test'],
  [13, 'shaman00986@gmail.com','ИТР ИОС',  'вход выполнен', '2026-08-31 15:xx', 'Шабашов'],
  [18, 'kotir325094@yandex.ru','ИТР8 pro', 'вход выполнен', '2026-08-26 08:xx', 'Котельникова']
];

// ==========================================================================
// МОК GOOGLE APPS SCRIPT
// ==========================================================================

/** Сборка 2D-модели листа matrix (холст 1000×26 + реальные данные). */
function buildMatrixModel(opts) {
  opts = opts || {};
  const ROWS = 1000, COLS = 26;
  const grid = Array.from({ length: ROWS }, () => new Array(COLS).fill(''));
  // r1–r3: шапка листа (текст в A, остальное пусто — как в таблице)
  grid[0][0] = 'ЛИСТ: matrix — МАТРИЦА ДОСТУПА «роль × право»';
  grid[1][0] = 'ИНСТРУКЦИЯ: источник истины для сервера. Строка 4 — perm_id, строка 5 — названия, строки 6+ — роли.';
  grid[2][0] = 'Сгенерировано: 02.09.2026 RoleMatrixInit v4';
  // r4: тех. ID
  grid[3][0] = 'role_id'; grid[3][1] = 'role_name';
  REAL_PERMS.forEach((p, i) => { grid[3][2 + i] = p; });
  // r5: названия (сокращённо)
  grid[4][1] = 'Роль';
  REAL_PERMS.forEach((p, i) => { grid[4][2 + i] = 'Название ' + p; });
  // r6+: роли
  const roles = opts.roles || REAL_ROLES;
  roles.forEach((r, i) => {
    for (let c = 0; c < Math.min(r.length, COLS - 2); c++) {
      grid[5 + i][c] = r[c];
    }
  });
  if (opts.extraHeader) { // динамическое право (T5)
    grid[3][2 + REAL_PERMS.length] = 'reports.view';
    grid[4][2 + REAL_PERMS.length] = 'Отчёты';
  }
  return grid;
}

/** Сборка 2D-модели users. opts.shiftCols — сдвиг шапки (T13). */
function buildUsersModel(opts) {
  opts = opts || {};
  const ROWS = opts.rows || 40, COLS = 26;
  const grid = Array.from({ length: ROWS }, () => new Array(COLS).fill(''));
  grid[0][0] = 'ЛИСТ: users — список пользователей';
  grid[1][0] = 'Вручную добавляйте пользователей снизу. Роль — точное название из matrix!B.';
  if (opts.shiftCols) {
    // шапка на r4, но email/role сдвинуты: A=№, B=name, C=role, D=id, E=email
    grid[3] = ['№', 'name', 'role', 'id', 'email', 'login_status', '', '', ''].concat(new Array(17).fill(''));
    REAL_USERS_ROWS.slice(1).forEach((u, i) => {
      grid[4 + i][1] = u[5]; grid[4 + i][2] = u[2]; grid[4 + i][3] = u[0]; grid[4 + i][4] = u[1];
    });
  } else {
    grid[3] = REAL_USERS_ROWS[0].concat(new Array(20).fill(''));
    REAL_USERS_ROWS.slice(1).forEach((u, i) => {
      for (let c = 0; c < u.length; c++) { grid[4 + i][c] = u[c]; }
    });
  }
  return grid;
}

/** Создаёт мок-мир (SpreadsheetApp/CacheService/Logger/console). */
function createWorld(opts) {
  opts = opts || {};
  const state = {
    openCount: 0,
    matrixReads: 0,
    usersReads: 0,
    cacheStore: {},
    cacheOps: 0,
    logs: [],
    consoleErrs: []
  };

  function sheetFromGrid(name, grid, lastRow, lastCol) {
    return {
      _name: name,
      getLastRow: () => lastRow,
      getLastColumn: () => lastCol,
      getRange: (row, col, numRows, numCols) => {
        if (typeof row !== 'number' || typeof col !== 'number') {
          throw new Error('мок: getRange ожидает (row, col, …), получено: ' + JSON.stringify([row, col]));
        }
        numRows = numRows || 1; numCols = numCols || 1;
        if (row < 1 || col < 1 || numRows < 1 || numCols < 1) {
          throw new Error('мок: некорректный диапазон ' + [row, col, numRows, numCols].join(','));
        }
        return {
          getValues: () => {
            if (name === 'matrix') { state.matrixReads++; }
            if (name === 'users') { state.usersReads++; }
            const out = [];
            for (let r = row - 1; r < row - 1 + numRows && r < grid.length; r++) {
              const src = grid[r] || [];
              const line = [];
              for (let c = col - 1; c < col - 1 + numCols; c++) {
                line.push(c < src.length ? src[c] : '');
              }
              out.push(line);
            }
            while (out.length < numRows) { out.push(new Array(numCols).fill('')); }
            return out;
          }
        };
      }
    };
  }

  const matrixGrid = opts.matrixGrid !== undefined ? opts.matrixGrid : buildMatrixModel();
  const usersGrid = opts.usersGrid !== undefined ? opts.usersGrid : buildUsersModel();
  const matrixSheet = opts.noMatrix ? null : sheetFromGrid('matrix', matrixGrid, 1000, 26);
  const usersSheet = opts.noUsers ? null : sheetFromGrid('users', usersGrid, 33, 26);

  const ss = {
    getName: () => 'KIP8_Access',
    getUrl: () => 'https://docs.google.com/spreadsheets/d/1TmmNZLUArWH38F6NX0gMGar8LMNMQomm_FaGZv9osyk/edit',
    getSheetByName: (name) => (name === 'matrix' ? matrixSheet : (name === 'users' ? usersSheet : null))
  };

  const sandbox = {
    SpreadsheetApp: {
      openById: (id) => {
        if (id !== '1TmmNZLUArWH38F6NX0gMGar8LMNMQomm_FaGZv9osyk') {
          throw new Error('Таблица ' + id + ' не найдена или нет доступа');
        }
        state.openCount++;
        return ss;
      }
    },
    CacheService: {
      getScriptCache: () => ({
        get: (k) => {
          state.cacheOps++;
          return Object.prototype.hasOwnProperty.call(state.cacheStore, k) ? state.cacheStore[k] : null;
        },
        put: (k, v, ttl) => {
          state.cacheOps++;
          if (opts.cachePutThrows) { throw new Error('Cache quota exceeded'); }
          state.cacheStore[k] = String(v);
        },
        remove: (k) => { state.cacheOps++; delete state.cacheStore[k]; }
      })
    },
    Logger: { log: (...a) => { state.logs.push(a.join(' ')); } },
    console: {
      log: () => {},
      error: (...a) => { state.consoleErrs.push(a.join(' ')); }
    },
    JSON, Math, String, Number, Object, Array, Error, RegExp
  };

  return { sandbox, state };
}

/** Загружает RoleMatrix.gs в мок-мир. */
function loadRoleMatrix(sandbox) {
  const code = fs.readFileSync(path.join(__dirname, 'RoleMatrix.gs'), 'utf8');
  const ctx = vm.createContext(sandbox);
  vm.runInContext(code, ctx, { filename: 'RoleMatrix.gs' });
  return {
    getAccess: (n) => vm.runInContext('roleMatrixGetAccess(' + JSON.stringify(n) + ')', ctx),
    hasPermission: (n, p) => vm.runInContext('roleMatrixHasPermission(' + JSON.stringify(n) + ',' + JSON.stringify(p) + ')', ctx),
    getAccessForEmail: (e) => vm.runInContext('roleMatrixGetAccessForEmail(' + JSON.stringify(e) + ')', ctx),
    invalidateCache: (e) => vm.runInContext('roleMatrixInvalidateCache(' + (e === undefined ? '' : JSON.stringify(e)) + ')', ctx),
    debug: () => vm.runInContext('roleMatrixDebug()', ctx),
    _getMatrix: () => vm.runInContext('_rmGetMatrix()', ctx),
    world: ctx
  };
}

// ==========================================================================
// МИНИ-ФРЕЙМВОРК ПРОВЕРОК
// ==========================================================================

let passed = 0, failed = 0;
const fails = [];
function ok(cond, name) {
  if (cond) { passed++; process.stdout.write('  \u2713 ' + name + '\n'); }
  else { failed++; fails.push(name); process.stdout.write('  \u2717 ' + name + '\n'); }
}
function eqArr(a, b, name) {
  const sa = JSON.stringify((a || []).slice().sort());
  const sb = JSON.stringify((b || []).slice().sort());
  ok(sa === sb, name + (sa === sb ? '' : ' (получено ' + sa + ', ожидалось ' + sb + ')'));
}
function section(title) { process.stdout.write('\n== ' + title + ' ==\n'); }

function sortGranted(res) { return (res.granted || []).slice().sort(); }

// ==========================================================================
// ТЕСТЫ
// ==========================================================================

// --- T1: все 12 реальных ролей, сверка granted с фактической таблицей ---
section('T1. Чтение реальной матрицы: 12 ролей, сверка granted');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  const names = REAL_ROLES.map(r => r[1]);
  for (const nm of names) {
    const res = rm.getAccess(nm);
    ok(res.found === true, nm + ': found');
    eqArr(sortGranted(res), EXPECT_GRANTS[nm], nm + ': granted совпадает с таблицей');
    if (nm === 'Админ') { ok(res.isAdmin === true, 'Админ: isAdmin'); }
    else { ok(res.isAdmin === false, nm + ': не админ'); }
    ok(res.warnings.length === 0, nm + ': без предупреждений');
  }
  const zapret = rm.getAccess('Запрет');
  eqArr(zapret.granted, [], 'Запрет: прав нет (полный запрет)');
  ok(zapret.permissions['admin.panel'] === false, 'Запрет: admin.panel=false');
}

// --- T2: «Админ всегда все права» ---
section('T2. Админ: все права + admin.panel неотключаем');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  const adm = rm.getAccess('Админ');
  const all = REAL_PERMS.filter(p => p !== 'kipios.restricted');
  eqArr(sortGranted(adm), all, 'Админ: все права кроме kipios.restricted');
  ok(adm.permissions['admin.panel'] === true, 'Админ: admin.panel=true');
  ok(adm.permissions['kipios.restricted'] === false, 'Админ: kipios.restricted по чекбоксу (false)');
  ok(adm.roleId === 'admin', 'Админ: roleId=admin');
  // по role_id тоже
  const adm2 = rm.getAccess('admin');
  ok(adm2.found && adm2.isAdmin && adm2.role === 'Админ', 'поиск по role_id «admin» тоже работает');
}

// --- T3: админ с полностью снятой матрицей → всё равно все права ---
section('T3. Защита от сброса галочек админа');
{
  const roles = REAL_ROLES.map(r => r.slice());
  const admIdx = roles.findIndex(r => r[0] === 'admin');
  roles[admIdx] = ['admin', 'Админ', 0,0,0,0,0,0,0,0,0,0,0,0,0]; // всё снято!
  const { sandbox } = createWorld({ matrixGrid: buildMatrixModel({ roles }) });
  const rm = loadRoleMatrix(sandbox);
  const adm = rm.getAccess('Админ');
  ok(adm.found && adm.isAdmin, 'Админ найден');
  ok(adm.granted.length === 12, 'все 12 прав возвращены несмотря на снятые галочки');
  ok(adm.permissions['admin.panel'] === true, 'admin.panel гарантирован');
  // режимное право НЕ выдано автоматически (по чекбоксу):
  ok(adm.permissions['kipios.restricted'] === false, 'kipios.restricted не навязан');
}

// --- T3b: админ САМ включил режимное право → уважается ---
section('T3b. Админ осознанно включил kipios.restricted');
{
  const roles = REAL_ROLES.map(r => r.slice());
  const admIdx = roles.findIndex(r => r[0] === 'admin');
  roles[admIdx][5] = 1; // kipios.restricted = true (индекс 5: 2+3)
  const { sandbox } = createWorld({ matrixGrid: buildMatrixModel({ roles }) });
  const rm = loadRoleMatrix(sandbox);
  const adm = rm.getAccess('Админ');
  ok(adm.permissions['kipios.restricted'] === true, 'осознанная галочка уважается');
  ok(adm.granted.length === 13, 'все 13 прав');
}

// --- T4: hasPermission ---
section('T4. hasPermission');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  ok(rm.hasPermission('ИТР ИОС', 'cablejournal.edit') === true, 'ИТР ИОС: cablejournal.edit=true');
  ok(rm.hasPermission('ИТР ИОС', 'workschedule.view') === false, 'ИТР ИОС: workschedule.view=false');
  ok(rm.hasPermission('Админ', 'admin.panel') === true, 'Админ: admin.panel=true');
  ok(rm.hasPermission('Запрет', 'calc.view') === false, 'Запрет: calc.view=false');
  ok(rm.hasPermission('ИТР ИОС', 'no.such.perm') === false, 'неизвестное право → false');
  ok(rm.hasPermission('Нет такой роли', 'calc.view') === false, 'неизвестная роль → false');
  ok(rm.hasPermission('ИТР ИОС', '') === false, 'пустое право → false');
}

// --- T5: динамичность (новая роль + новое право) ---
section('T5. Динамика: добавлены «Монтажник» и reports.view');
{
  const roles = REAL_ROLES.concat([['montazh', 'Монтажник', 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]]);
  const grid = buildMatrixModel({ roles, extraHeader: true });
  // колонка reports.view — 16-я (индекс 15); у «Монтажника» значение 1
  // запишем в r17 (Монтажник — 13-я роль, строка 6+12=18 → индекс 17):
  grid[17][15] = 1;
  const { sandbox } = createWorld({ matrixGrid: grid });
  const rm = loadRoleMatrix(sandbox);
  const m = rm.getAccess('Монтажник');
  ok(m.found === true, 'Монтажник найден (13-я роль)');
  ok(m.roleId === 'montazh', 'Монтажник: roleId');
  ok(m.permissions['reports.view'] === true, 'новое право reports.view прочитано');
  ok(rm.hasPermission('Монтажник', 'reports.view') === true, 'hasPermission по новому праву');
  const kip8 = rm.getAccess('КИП8');
  ok(kip8.permissions['reports.view'] === false, 'старой роли новое право не выдано (пусто = false)');
  const adm = rm.getAccess('Админ');
  ok(adm.permissions['reports.view'] === true, 'новое право автоматически у Админа');
  eqArr(sortGranted(adm), REAL_PERMS.concat(['reports.view']).filter(p => p !== 'kipios.restricted'),
    'Админ: 13 прав с reports.view');
}

// --- T6: неизвестная роль → fail-closed ---
section('T6. Неизвестная роль → fail-closed');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  const res = rm.getAccess('Супервайзер');
  ok(res.found === false, 'found=false');
  eqArr(res.granted, [], 'granted пуст');
  ok(res.permissions && Object.keys(res.permissions).length === 0, 'permissions пуст');
  ok(/не найдена/.test(res.warnings.join(' ')), 'есть предупреждение');
}

// --- T7: лист matrix отсутствует ---
section('T7. Лист matrix отсутствует → fail-closed + подсказка');
{
  const { sandbox, state } = createWorld({ noMatrix: true });
  const rm = loadRoleMatrix(sandbox);
  const res = rm.getAccess('Админ');
  ok(res.found === false, 'found=false');
  eqArr(res.granted, [], 'granted пуст');
  ok(/RoleMatrixInit/.test(res.warnings.join(' ')), 'подсказка про Task 293');
  ok(state.consoleErrs.length >= 1, 'console.error вызван');
  const res2 = rm.getAccessForEmail('bloknet@bk.ru');
  eqArr(res2.granted, [], 'email-путь тоже закрыт');
}

// --- T8: email → роль → права ---
section('T8. getAccessForEmail');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  const a = rm.getAccessForEmail('shaman00986@gmail.com');
  ok(a.userFound === true, 'пользователь найден');
  ok(a.role === 'ИТР ИОС', 'роль подхвачена: ИТР ИОС');
  eqArr(sortGranted(a), EXPECT_GRANTS['ИТР ИОС'], 'права ИТР ИОС из реальной матрицы');
  const b = rm.getAccessForEmail('  BLOKNET@BK.RU ');
  ok(b.userFound === true && b.isAdmin === true, 'email без регистра/с пробелами найден');
  ok(b.role === 'Админ', 'роль Админ');
  const c = rm.getAccessForEmail('ghost@example.com');
  ok(c.userFound === false, 'неизвестный email: userFound=false');
  eqArr(c.granted, [], 'неизвестный email: доступ закрыт');
  ok(/не найден/.test(c.warnings.join(' ')), 'предупреждение о незнакомом email');
  const d = rm.getAccessForEmail('');
  eqArr(d.granted, [], 'пустой email → закрыт');
}

// --- T9: кэш ---
section('T9. Кэш CacheService');
{
  const { sandbox, state } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  rm.getAccess('ИТР8');
  const reads1 = state.matrixReads;
  rm.getAccess('ИТР8 pro');      // другой вызов — матрица уже в кэше
  rm.hasPermission('Админ', 'charts.view');
  ok(state.matrixReads === reads1, 'повторные чтения идут из кэша (обращений к листу нет)');
  rm.invalidateCache();
  rm.getAccess('ИТР8');
  ok(state.matrixReads > reads1, 'после invalidateCache — перечитывание');

  // битый JSON в кэше → игнор и перечитывание
  const { sandbox: sb2, state: st2 } = createWorld();
  const rm2 = loadRoleMatrix(sb2);
  st2.cacheStore['RoleMatrix.matrix.v1'] = '{битый json';
  const res = rm2.getAccess('Админ');
  ok(res.found === true && res.isAdmin === true, 'битый кэш проигнорирован, матрица перечитана');
  eqArr(sortGranted(res), EXPECT_GRANTS['Админ'], 'данные корректны после битого кэша');

  // put бросает (переполнение) → не падаем
  const { sandbox: sb3 } = createWorld({ cachePutThrows: true });
  const rm3 = loadRoleMatrix(sb3);
  const res3 = rm3.getAccess('ИТР8');
  ok(res3.found === true, 'кэш-переполнение не ломает чтение');
  eqArr(sortGranted(res3), EXPECT_GRANTS['ИТР8'], 'данные корректны без кэша');
}

// --- T10: нормализация названий ---
section('T10. Регистр/пробелы/role_id');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  ok(rm.getAccess('итр8 pro').found === true, 'нижний регистр');
  ok(rm.getAccess('  ИТР8 PRO  ').found === true, 'пробелы по краям');
  ok(rm.getAccess('kip_ios_duty').found === true, 'поиск по role_id');
  ok(rm.getAccess('kip_ios_duty').role === 'КИП ИОС дежурный', 'role_id → человекочитаемое название');
  const empty = rm.getAccess('   ');
  ok(empty.found === false && empty.granted.length === 0, 'пустое имя → закрыт');
}

// --- T11: ловушка getLast* (холст 1000×26) ---
section('T11. Стилевой холст A1:Z1000 не мешает');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  const m = rm._getMatrix();
  ok(m.permIds.length === 13, 'прав ровно 13 (не 24 колонки холста)');
  ok(m.roles.length === 12, 'ролей ровно 12 (не 994 строки холста)');
  eqArr(m.permIds.slice().sort(), REAL_PERMS.slice().sort(), 'состав прав точен');
  // Эффективность: одна загрузка матрицы = 2 обращения getValues
  // (шапка r4 + данные r6+), не построчно:
  const { sandbox: sbEff, state: stEff } = createWorld();
  const rmEff = loadRoleMatrix(sbEff);
  rmEff._getMatrix();
  ok(stEff.matrixReads === 2, 'чтение матрицы = 2 запроса getValues (шапка + данные)');
}

// --- T12: мусор в значениях чекбоксов ---
section('T12. Значения-не-чекбоксы');
{
  const roles = REAL_ROLES.map(r => r.slice());
  roles[2] = ['itr_tokem', 'ИТР ТОКЕМ', 'TRUE', 'yes', 0, 1, 0, 0, 'true', '', null, 0, 0, 0, 0];
  //         calc='TRUE'(→T), library='yes'(→F), kipios.view=0(F), restricted=1(T)
  const { sandbox } = createWorld({ matrixGrid: buildMatrixModel({ roles }) });
  const rm = loadRoleMatrix(sandbox);
  const t = rm.getAccess('ИТР ТОКЕМ');
  ok(t.permissions['calc.view'] === true, 'строка "TRUE" → true');
  ok(t.permissions['kipios.restricted'] === true, 'число 1 → true');
  ok(t.permissions['secret.view'] === true, 'строка "true" (низкий регистр) → true');
  ok(t.permissions['library.view'] === false, 'строка "yes" → false');
  ok(t.permissions['whatsnew.view'] === false, 'пусто → false');
  ok(t.permissions['kipios.view'] === false, '0 → false');
}

// --- T13: users со сдвинутой шапкой ---
section('T13. users: колонки email/role найдены динамически');
{
  const { sandbox } = createWorld({ usersGrid: buildUsersModel({ shiftCols: true }) });
  const rm = loadRoleMatrix(sandbox);
  const a = rm.getAccessForEmail('kotir325094@yandex.ru');
  ok(a.userFound === true, 'email в колонке E найден');
  ok(a.role === 'ИТР8 pro', 'role из колонки C');
  eqArr(sortGranted(a), EXPECT_GRANTS['ИТР8 pro'], 'права верные');
}

// --- T14: реальные пользователи ---
section('T14. Реальные пользователи из users');
{
  const { sandbox } = createWorld();
  const rm = loadRoleMatrix(sandbox);
  const cases = [
    ['bloknet@bk.ru', 'Админ'],
    ['bloknett@gmail.com', 'Админ'],
    ['blooknet@yandex.ru', 'Админ'],
    ['bloknetm@gmail.com', 'Админ'],
    ['shaman00986@gmail.com', 'ИТР ИОС'],
    ['kotir325094@yandex.ru', 'ИТР8 pro']
  ];
  for (const [em, role] of cases) {
    const r = rm.getAccessForEmail(em);
    ok(r.userFound && r.role === role, em + ' → «' + role + '»');
    eqArr(sortGranted(r), EXPECT_GRANTS[role], em + ': права «' + role + '» верны');
  }
  // roleMatrixDebug не падает и отчитывается:
  const { sandbox: sdbg } = createWorld();
  const rmdbg = loadRoleMatrix(sdbg);
  const out = rmdbg.debug();
  ok(/Права \(matrix r4, C\+\): 13/.test(out), 'debug: 13 прав');
  ok(/Роли \(matrix r6\+\): 12/.test(out), 'debug: 12 ролей');
  ok(/роль есть в matrix/.test(out), 'debug: связки users↔matrix проверены');
  ok(/Предупреждений нет/.test(out), 'debug: предупреждений нет');
}

// ==========================================================================
process.stdout.write('\n════════════════════════════════════════\n');
process.stdout.write('ИТОГ: ' + passed + ' passed / ' + failed + ' failed\n');
if (failed) {
  process.stdout.write('ПРОВАЛЫ:\n');
  fails.forEach(f => process.stdout.write('  - ' + f + '\n'));
  process.exit(1);
}
process.stdout.write('ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ\n');
