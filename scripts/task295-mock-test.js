#!/usr/bin/env node
/**
 * task295-mock-test.js — мок-тест Этапа 3 (Task 295): серверный шлюз
 * прав RoleMatrixGate.gs + интеграция в Code.gs / Flowmeter.gs /
 * WorkSchedule.gs.
 *
 * МЕТОД: Apps Script моделируется в Node.js (vm.createContext).
 * ДАННЫЕ РЕАЛЬНЫЕ: матрица — снята скачиванием KIP8_Access после v4
 * (12 ролей, 13 прав, фактические галочки + «стилевой холст» A1:Z1000);
 * пользователи — 20 штук из журнала roleMatrixDebug у пользователя
 * (02.09.2026); сессии — условные токены.
 *
 * КОНТЕКСТЫ:
 *   A  Code.gs + RoleMatrix.gs + RoleMatrixGate.gs + заглушки модулей
 *      → маршрутизация doPost: гейт админ-действий и записей
 *      кабельного журнала, getMyAccess, публичные/сессионные
 *      действия не гейтятся.
 *   B  RoleMatrix.gs + RoleMatrixGate.gs + РЕАЛЬНЫЕ Flowmeter.gs и
 *      WorkSchedule.gs → внутренние проверки _requireRead/_requireEdit/
 *      _requireWrite по матрице (включая изменения поведения).
 *   B2 как B, но лист matrix отсутствует → fail-closed для ВСЕХ.
 *   C  Code.gs + реальные Flowmeter/WorkSchedule БЕЗ RoleMatrix/Gate
 *      → legacy-режим (старые списки ролей + предупреждение в консоль).
 */

'use strict';

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const DIR = __dirname;

// ==========================================================================
// РЕАЛЬНЫЕ ДАННЫЕ (KIP8_Access, 02.09.2026)
// ==========================================================================

const REAL_PERMS = [
  'calc.view', 'library.view', 'kipios.view', 'kipios.restricted',
  'cablejournal.edit', 'admin.panel', 'secret.view', 'whatsnew.view',
  'charts.view', 'flowmeter.view', 'flowmeter.input',
  'workschedule.view', 'workschedule.edit'
];

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

// 20 реальных пользователей (журнал roleMatrixDebug 02.09.2026)
const REAL_USERS = [
  { id: 1,  email: 'bloknett@gmail.com',         role: 'Админ' },
  { id: 3,  email: 'bloknet@bk.ru',              role: 'Админ' },
  { id: 4,  email: 'blooknet@yandex.ru',         role: 'Админ' },
  { id: 2,  email: 'bloknetm@gmail.com',         role: 'Админ' },
  { id: 13, email: 'shaman00986@gmail.com',      role: 'ИТР ИОС' },
  { id: 18, email: 'kotir325094@yandex.ru',      role: 'ИТР8 pro' },
  { id: 21, email: 'vg.lyahovsky@gmail.com',     role: 'ИТР8' },
  { id: 22, email: 'mrnikolaika@gmail.com',      role: 'ИТР8 pro' },
  { id: 23, email: 'sperwow42ru@gmail.com',      role: 'КИП ИОС' },
  { id: 24, email: 'mrartimon@gmail.com',        role: 'КИП ИОС' },
  { id: 25, email: 'roma.now260207@gmail.com',   role: 'КИП ИОС' },
  { id: 26, email: 'zwerowoi@gmail.com',         role: 'КИП ИОС' },
  { id: 27, email: 'hadandreas91@gmail.com',     role: 'КИП ИОС дежурный' },
  { id: 28, email: 'evgenysachkin@yandex.ru',    role: 'КИП ИОС дежурный' },
  { id: 29, email: 'yurachikrizov@gmail.com',    role: 'КИП ИОС дежурный' },
  { id: 30, email: 'jurij090263@yandex.ru',      role: 'КИП ИОС дежурный' },
  { id: 31, email: 'krivezhenkobogdan@gmail.com', role: 'КИП ИОС дежурный' },
  { id: 32, email: 'fedos9247@gmail.com',        role: 'КИП ИОС pro' },
  { id: 33, email: 'erogatov@mail.ru',           role: 'КИП8 pro' },
  { id: 34, email: 'tigor196314@gmail.com',      role: 'КИП8' },
  { id: 99, email: 'banned@example.com',         role: 'Запрет' } // тестовая
];

const SESSIONS = [
  { token: 'tok-admin1',   user_id: 1 },   // bloknett@gmail.com, Админ
  { token: 'tok-admin2',   user_id: 3 },   // bloknet@bk.ru, Админ
  { token: 'tok-itr-ios',  user_id: 13 },  // shaman00986, ИТР ИОС
  { token: 'tok-itr8',     user_id: 21 },  // vg.lyahovsky, ИТР8
  { token: 'tok-itr8-pro', user_id: 18 },  // kotir325094, ИТР8 pro
  { token: 'tok-duty',     user_id: 27 },  // hadandreas91, дежурный
  { token: 'tok-kipios',   user_id: 23 },  // sperwow42ru, КИП ИОС
  { token: 'tok-kip8',     user_id: 34 },  // tigor196314, КИП8
  { token: 'tok-kip8-pro', user_id: 33 },  // erogatov, КИП8 pro
  { token: 'tok-zapret',   user_id: 99 }   // banned@example.com, Запрет
];

// ==========================================================================
// МОКИ
// ==========================================================================

/** 2D-модель листа matrix (холст 1000×26 + реальные данные). */
function buildMatrixGrid() {
  const ROWS = 1000, COLS = 26;
  const grid = Array.from({ length: ROWS }, () => new Array(COLS).fill(''));
  grid[0][0] = 'ЛИСТ: matrix — МАТРИЦА ДОСТУПА «роль × право»';
  grid[1][0] = 'ИНСТРУКЦИЯ: источник истины для сервера.';
  grid[2][0] = 'Сгенерировано: 02.09.2026 RoleMatrixInit v4';
  grid[3][0] = 'role_id'; grid[3][1] = 'role_name';
  REAL_PERMS.forEach((p, i) => { grid[3][2 + i] = p; });
  grid[4][1] = 'Роль';
  REAL_PERMS.forEach((p, i) => { grid[4][2 + i] = 'Название ' + p; });
  REAL_ROLES.forEach((r, i) => {
    for (let c = 0; c < Math.min(r.length, COLS - 2); c++) { grid[5 + i][c] = r[c]; }
  });
  return grid;
}

/** Мок листа (getRange/getValues + getLast*). */
function makeSheet(name, grid, lastRow, lastCol) {
  return {
    _name: name,
    getLastRow: () => lastRow,
    getLastColumn: () => lastCol,
    getRange: (row, col, numRows, numCols) => {
      numRows = numRows || 1; numCols = numCols || 1;
      return {
        getValues: () => {
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

/** Мок Utils (контракт как в WorkSchedule.gs/Flowmeter.gs). */
function makeUtils(state) {
  const sessMap = {};
  SESSIONS.forEach(s => { sessMap[s.token] = s; });
  const userMap = {};
  REAL_USERS.forEach(u => { userMap[u.id] = u; });
  return {
    findSessionByToken: (t) => (t && sessMap[t]) ? Object.assign({}, sessMap[t]) : null,
    findUserById: (id) => (userMap[id] !== undefined) ? Object.assign({}, userMap[id]) : null,
    audit: (email, code, a, b, details) => {
      state.audits.push({ email: email, code: code, details: details });
    }
  };
}

/** Заглушки модулей для Code.gs (записывают вызовы). */
function makeModuleStubs(state) {
  const rec = (name) => function () {
    state.moduleCalls.push({ module: name, args: Array.prototype.slice.call(arguments) });
    return { ok: true, stub: true, module: name };
  };
  return {
    Auth: { sendOTP: rec('Auth.sendOTP'), verifyOTP: rec('Auth.verifyOTP') },
    Sessions: {
      getCurrentUser: rec('Sessions.getCurrentUser'),
      heartbeat: rec('Sessions.heartbeat'),
      logout: rec('Sessions.logout')
    },
    Admin: {
      listUsers: rec('Admin.listUsers'), updateRole: rec('Admin.updateRole'),
      resetLogin: rec('Admin.resetLogin'), createUser: rec('Admin.createUser'),
      listSessions: rec('Admin.listSessions'), listLogs: rec('Admin.listLogs')
    },
    CableJournal: {
      list: rec('CableJournal.list'), getColumns: rec('CableJournal.getColumns'),
      getFilters: rec('CableJournal.getFilters'), appendRow: rec('CableJournal.appendRow'),
      updateRow: rec('CableJournal.updateRow'), deleteRow: rec('CableJournal.deleteRow')
    },
    Flowmeter: {
      list: rec('Flowmeter.list'), updateReading: rec('Flowmeter.updateReading'),
      setComment: rec('Flowmeter.setComment')
    },
    FlowmeterArchive: {
      listArchive: rec('FlowmeterArchive.listArchive'),
      listRecentAllMeters: rec('FlowmeterArchive.listRecentAllMeters')
    },
    ValidationRules: {
      listRules: rec('ValidationRules.listRules'), listHelp: rec('ValidationRules.listHelp')
    },
    WorkSchedule: {
      getStatusCodes: rec('WorkSchedule.getStatusCodes'),
      getPatterns: rec('WorkSchedule.getPatterns'),
      listEmployees: rec('WorkSchedule.listEmployees'),
      listEntries: rec('WorkSchedule.listEntries'),
      listTrainings: rec('WorkSchedule.listTrainings'),
      generateMonth: rec('WorkSchedule.generateMonth'),
      setManualEntry: rec('WorkSchedule.setManualEntry'),
      deleteEntry: rec('WorkSchedule.deleteEntry'),
      addEmployee: rec('WorkSchedule.addEmployee'),
      addTraining: rec('WorkSchedule.addTraining'),
      deleteTraining: rec('WorkSchedule.deleteTraining'),
      listVacations: rec('WorkSchedule.listVacations'),
      addVacation: rec('WorkSchedule.addVacation'),
      deleteVacation: rec('WorkSchedule.deleteVacation')
    }
  };
}

/**
 * Создаёт контекст vm.
 * opts.files — какие .gs грузить; opts.modules — 'stub' | 'real';
 * opts.matrix — true/false (есть ли лист matrix).
 */
function createContext(opts) {
  const state = { moduleCalls: [], audits: [], consoleErrs: [], logs: [] };

  const matrixSheet = opts.matrix === false ? null : makeSheet('matrix', buildMatrixGrid(), 1000, 26);
  const usersSheet = makeSheet('users', [['header']], 1, 6);
  const ss = {
    getName: () => 'KIP8_Access',
    getSheetByName: (n) => (n === 'matrix' ? matrixSheet : (n === 'users' ? usersSheet : null))
  };

  const sandbox = {
    SpreadsheetApp: {
      openById: (id) => {
        if (id !== '1TmmNZLUArWH38F6NX0gMGar8LMNMQomm_FaGZv9osyk') {
          throw new Error('Таблица не найдена: ' + id);
        }
        return ss;
      }
    },
    CacheService: {
      getScriptCache: () => ({
        get: () => null,
        put: () => {},
        remove: () => {}
      })
    },
    ContentService: {
      MimeType: { JSON: 'JSON' },
      createTextOutput: (txt) => ({
        _txt: txt,
        setMimeType: function () { return this; }
      })
    },
    ScriptApp: { getProjectTriggers: () => [] },
    Utils: makeUtils(state),
    Logger: { log: (m) => { state.logs.push(String(m)); } },
    console: {
      log: () => {},
      error: (...a) => { state.consoleErrs.push(a.join(' ')); }
    }
  };

  if (opts.modules === 'stub') {
    Object.assign(sandbox, makeModuleStubs(state));
  }

  const ctx = vm.createContext(sandbox);
  for (const f of opts.files) {
    const code = fs.readFileSync(path.join(DIR, f), 'utf8');
    vm.runInContext(code, ctx, { filename: f });
  }
  return { ctx, state };
}

/** doPost(action, payload) → распарсенный JSON. */
function callDoPost(ctx, action, payload) {
  const e = {
    parameter: { action: action },
    postData: { contents: JSON.stringify(payload || {}) }
  };
  const out = vm.runInContext('doPost(' + JSON.stringify(e) + ')', ctx);
  return JSON.parse(out._txt);
}

function readCode(f) {
  return fs.readFileSync(path.join(DIR, f), 'utf8');
}

// ==========================================================================
// МИНИ-ФРЕЙМВОРК
// ==========================================================================

let passed = 0, failed = 0;
const fails = [];
function ok(cond, name) {
  if (cond) { passed++; process.stdout.write('  \u2713 ' + name + '\n'); }
  else { failed++; fails.push(name); process.stdout.write('  \u2717 ' + name + '\n'); }
}
function section(t) { process.stdout.write('\n== ' + t + ' ==\n'); }
function hasAudit(state, code) {
  return state.audits.some(a => a.code === code);
}

// ==========================================================================
// КОНТЕКСТ A: маршрутизация Code.gs с гейтом
// ==========================================================================

section('A1. Гейт админ-действий (admin.panel)');
{
  const { ctx, state } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'Code.gs'],
    modules: 'stub', matrix: true
  });

  let r = callDoPost(ctx, 'adminListUsers', { token: 'tok-admin1' });
  ok(r.ok === true, 'админ: adminListUsers → ok');
  ok(state.moduleCalls.some(c => c.module === 'Admin.listUsers'), 'Admin.listUsers вызван');

  const st0 = state.moduleCalls.length;
  r = callDoPost(ctx, 'adminListUsers', { token: 'tok-itr8' });
  ok(r.ok === false && r.error === 'access_denied', 'ИТР8: adminListUsers → access_denied');
  ok(state.moduleCalls.length === st0, 'Admin.listUsers НЕ вызван (гейт раньше модуля)');
  ok(hasAudit(state, 'RM_ACCESS_DENIED'), 'отказ записан в audit (RM_ACCESS_DENIED)');
  const a0 = state.audits.find(a => a.code === 'RM_ACCESS_DENIED');
  ok(/admin\.panel/.test(a0.details) && /adminListUsers/.test(a0.details),
    'в аудите право + действие');

  r = callDoPost(ctx, 'adminUpdateRole', { token: 'tok-duty' });
  ok(r.ok === false && r.error === 'access_denied', 'дежурный: adminUpdateRole → denied');
  r = callDoPost(ctx, 'adminListLogs', { token: 'tok-kipios' });
  ok(r.ok === false && r.error === 'access_denied', 'КИП ИОС: adminListLogs → denied');
  r = callDoPost(ctx, 'adminListSessions', { token: 'tok-itr-ios' });
  ok(r.ok === false && r.error === 'access_denied', 'ИТР ИОС: adminListSessions → denied');
  r = callDoPost(ctx, 'adminListUsers', { token: 'tok-zapret' });
  ok(r.ok === false && r.error === 'access_denied', 'Запрет: adminListUsers → denied');
  r = callDoPost(ctx, 'adminListUsers', { token: '' });
  ok(r.ok === false && r.error === 'no_session', 'без токена → no_session');
  r = callDoPost(ctx, 'adminListUsers', { token: 'BAD' });
  ok(r.ok === false && r.error === 'no_session', 'мусорный токен → no_session');
  r = callDoPost(ctx, 'adminListUsers', { token: 'tok-admin2' });
  ok(r.ok === true, 'второй админ (bloknet@bk.ru) проходит');
}

section('A2. Гейт записей каб. журнала (cablejournal.edit)');
{
  const { ctx, state } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'Code.gs'],
    modules: 'stub', matrix: true
  });

  let r = callDoPost(ctx, 'cableJournal.appendRow', { token: 'tok-itr-ios', data: {} });
  ok(r.ok === true, 'ИТР ИОС (cablejournal.edit ✓): appendRow → ok');
  ok(state.moduleCalls.some(c => c.module === 'CableJournal.appendRow'), 'CableJournal.appendRow вызван');

  const st0 = state.moduleCalls.length;
  r = callDoPost(ctx, 'cableJournal.appendRow', { token: 'tok-kipios' });
  ok(r.ok === false && r.error === 'access_denied', 'КИП ИОС (права нет): appendRow → denied');
  r = callDoPost(ctx, 'cableJournal.updateRow', { token: 'tok-duty' });
  ok(r.ok === false && r.error === 'access_denied', 'дежурный: updateRow → denied');
  r = callDoPost(ctx, 'cableJournal.deleteRow', { token: 'tok-kip8-pro' });
  ok(r.ok === false && r.error === 'access_denied', 'КИП8 pro: deleteRow → denied');
  ok(state.moduleCalls.length === st0, 'модуль ни разу не вызван при отказах');

  r = callDoPost(ctx, 'cableJournal.list', { token: 'tok-kip8' });
  ok(r.ok === true && state.moduleCalls.some(c => c.module === 'CableJournal.list'),
    'cableJournal.list НЕ гейтится роутером (чтение)');
  r = callDoPost(ctx, 'flowmeter.list', { token: 'tok-itr8' });
  ok(r.ok === true && state.moduleCalls.some(c => c.module === 'Flowmeter.list'),
    'flowmeter.list идёт в модуль (его проверяет сам Flowmeter.gs)');
}

section('A3. getMyAccess (карта прав для клиента)');
{
  const { ctx } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'Code.gs'],
    modules: 'stub', matrix: true
  });

  let r = callDoPost(ctx, 'getMyAccess', { token: 'tok-duty' });
  ok(r.ok === true, 'ok');
  const d = r.data;
  ok(d.email === 'hadandreas91@gmail.com', 'email');
  ok(d.role === 'КИП ИОС дежурный' && d.roleId === 'kip_ios_duty', 'role/roleId');
  ok(d.userId === 27, 'userId');
  ok(d.isAdmin === false, 'isAdmin=false');
  ok(d.permissions['flowmeter.input'] === true, 'flowmeter.input=true');
  ok(d.permissions['admin.panel'] === false, 'admin.panel=false');
  ok(d.granted.indexOf('flowmeter.input') !== -1, 'granted содержит flowmeter.input');
  ok(d.found === true, 'found=true');

  r = callDoPost(ctx, 'getMyAccess', { token: 'tok-admin1' });
  ok(r.ok === true && r.data.isAdmin === true, 'админ: isAdmin=true');
  ok(r.data.permissions['admin.panel'] === true, 'админ: admin.panel=true');
  ok(r.data.granted.length === 12, 'админ: 12 прав (без kipios.restricted)');
  ok(r.data.permissions['kipios.restricted'] === false, 'админ: kipios.restricted по чекбоксу');

  r = callDoPost(ctx, 'getMyAccess', { token: 'tok-zapret' });
  ok(r.ok === true && r.data.granted.length === 0, 'Запрет: granted пуст');
  ok(r.data.permissions['calc.view'] === false, 'Запрет: calc.view=false');

  r = callDoPost(ctx, 'getMyAccess', { token: 'BAD' });
  ok(r.ok === false && r.error === 'no_session', 'мусорный токен → no_session');
  r = callDoPost(ctx, 'getMyAccess', {});
  ok(r.ok === false && r.error === 'no_session', 'без токена → no_session');
}

section('A4. Публичные/сессионные действия НЕ гейтятся');
{
  const { ctx, state } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'Code.gs'],
    modules: 'stub', matrix: true
  });

  let r = callDoPost(ctx, 'sendOTP', { email: 'x@example.com' });
  ok(r.ok === true && state.moduleCalls.some(c => c.module === 'Auth.sendOTP'),
    'sendOTP без токена работает (вход не гейтится)');
  r = callDoPost(ctx, 'getCurrentUser', { token: 'tok-zapret' });
  ok(r.ok === true && state.moduleCalls.some(c => c.module === 'Sessions.getCurrentUser'),
    'getCurrentUser работает даже для Запрета (сессия ≠ права)');
  r = callDoPost(ctx, 'heartbeat', { token: 'tok-itr8' });
  ok(r.ok === true, 'heartbeat работает');
  r = callDoPost(ctx, 'unknownAction', {});
  ok(r.ok === false && /Unknown action/.test(r.error), 'неизвестное действие → Unknown action');
}

// ==========================================================================
// КОНТЕКСТ B: реальные Flowmeter.gs / WorkSchedule.gs + матрица
// ==========================================================================

section('B1. Flowmeter: права из матрицы');
{
  const { ctx } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'Flowmeter.gs'],
    modules: 'real', matrix: true
  });

  let res = vm.runInContext('Flowmeter._requireRead("tok-kip8-pro")', ctx);
  ok(!!res.user, 'КИП8 pro: чтение расходомеров ✓ (flowmeter.view)');
  res = vm.runInContext('Flowmeter._requireRead("tok-itr8")', ctx);
  ok(!!res.user, 'ИТР8: чтение ✓');
  res = vm.runInContext('Flowmeter._requireRead("tok-kipios")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'КИП ИОС: чтение ✗ (нет flowmeter.view)');
  res = vm.runInContext('Flowmeter._requireRead("")', ctx);
  ok(res.error && res.error.error === 'no_session', 'без токена → no_session');
  res = vm.runInContext('Flowmeter._requireRead("BAD")', ctx);
  ok(res.error && res.error.error === 'no_session', 'мусорный токен → no_session');

  res = vm.runInContext('Flowmeter._requireEdit("tok-duty")', ctx);
  ok(!!res.user, 'дежурный: ввод показаний ✓ (flowmeter.input)');
  res = vm.runInContext('Flowmeter._requireEdit("tok-itr-ios")', ctx);
  ok(!!res.user, 'ИТР ИОС: ввод ✓ — ИЗМЕНЕНИЕ ПОВЕДЕНИЯ (осознанное, матрица)');
  res = vm.runInContext('Flowmeter._requireEdit("tok-itr8")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'ИТР8: ввод ✗ (только просмотр)');
  res = vm.runInContext('Flowmeter._requireEdit("tok-kipios")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'КИП ИОС: ввод ✗');
}

section('B2. WorkSchedule: права из матрицы');
{
  const { ctx, state } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'WorkSchedule.gs'],
    modules: 'real', matrix: true
  });

  let res = vm.runInContext('WorkSchedule._requireRead("tok-itr8-pro")', ctx);
  ok(!!res.user, 'ИТР8 pro: чтение ✓ — ИЗМЕНЕНИЕ ПОВЕДЕНИЯ (осознанное, матрица)');
  res = vm.runInContext('WorkSchedule._requireRead("tok-itr8")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'ИТР8: чтение ✗ (нет workschedule.view)');
  res = vm.runInContext('WorkSchedule._requireRead("tok-admin1")', ctx);
  ok(!!res.user, 'Админ: чтение ✓');
  res = vm.runInContext('WorkSchedule._requireWrite("tok-admin1")', ctx);
  ok(!!res.user, 'Админ: запись ✓ (workschedule.edit)');
  res = vm.runInContext('WorkSchedule._requireWrite("tok-itr8-pro")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'ИТР8 pro: запись ✗ (edit только у Админа)');
  res = vm.runInContext('WorkSchedule._requireWrite("tok-duty")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'дежурный: запись ✗');
  res = vm.runInContext('WorkSchedule._requireWrite("")', ctx);
  ok(res.error && res.error.error === 'no_session', 'без токена → no_session');
  ok(hasAudit(state, 'RM_ACCESS_DENIED'), 'отказы в audit_log');
}

section('B3. rmGateStatus (диагностика шлюза)');
{
  const { ctx } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'WorkSchedule.gs'],
    modules: 'real', matrix: true
  });
  const out = vm.runInContext('rmGateStatus()', ctx);
  ok(/RoleMatrixGate: статус/.test(out), 'заголовок есть');
  ok(/RoleMatrix: OK/.test(out), 'RoleMatrix: OK');
  ok(/Админ/.test(out) && /ИТР8 pro/.test(out), 'таблица ролей выведена');
}

// ==========================================================================
// КОНТЕКСТ B2: лист matrix отсутствует → fail-closed
// ==========================================================================

section('B4. Матрица недоступна → fail-closed для ВСЕХ');
{
  const { ctx, state } = createContext({
    files: ['RoleMatrix.gs', 'RoleMatrixGate.gs', 'Flowmeter.gs', 'WorkSchedule.gs'],
    modules: 'real', matrix: false
  });

  let res = vm.runInContext('Flowmeter._requireRead("tok-admin1")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'Админ: чтение расходомеров ✗ (fail-closed)');
  res = vm.runInContext('Flowmeter._requireEdit("tok-duty")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'дежурный: ввод ✗');
  res = vm.runInContext('WorkSchedule._requireWrite("tok-admin1")', ctx);
  ok(res.error && res.error.error === 'access_denied', 'Админ: запись графика ✗');
  ok(state.consoleErrs.length >= 1, 'проблема залогирована в консоль');
}

// ==========================================================================
// КОНТЕКСТ C: legacy-режим (RoleMatrix/RoleMatrixGate НЕ задеплоены)
// ==========================================================================

section('C1. Code.gs без RoleMatrixGate: гейт пропускается + предупреждение');
{
  const { ctx, state } = createContext({
    files: ['Code.gs', 'Flowmeter.gs', 'WorkSchedule.gs'],
    modules: 'stub', matrix: true
  });

  const r = callDoPost(ctx, 'adminListUsers', { token: 'tok-itr8' });
  ok(r.ok === true, 'ИТР8: adminListUsers → ok (legacy, как до Этапа 3)');
  ok(state.moduleCalls.some(c => c.module === 'Admin.listUsers'), 'Admin.listUsers вызван');
  ok(state.consoleErrs.some(e => /RoleMatrixGate\.gs не задеплоен/.test(e)),
    'в консоль написано предупреждение');
  const r2 = callDoPost(ctx, 'getMyAccess', { token: 'tok-admin1' });
  ok(r2.ok === false && /не задеплоен/.test(r2.error), 'getMyAccess → понятная ошибка');
}

section('C2. Flowmeter/WorkSchedule без матрицы: прежние списки');
{
  const { ctx } = createContext({
    files: ['Flowmeter.gs', 'WorkSchedule.gs'],
    modules: 'real', matrix: true
  });

  let res = vm.runInContext('Flowmeter._requireEdit("tok-itr-ios")', ctx);
  ok(res.error && res.error.error === 'access_denied',
    'ИТР ИОС: ввод ✗ (legacy INPUT_ROLES — как до Этапа 3)');
  res = vm.runInContext('Flowmeter._requireRead("tok-itr8")', ctx);
  ok(!!res.user, 'ИТР8: чтение ✓ (legacy READ_ROLES)');
  res = vm.runInContext('Flowmeter._requireRead("tok-kip8-pro")', ctx);
  ok(!!res.user, 'КИП8 pro: чтение ✓ (legacy)');
  res = vm.runInContext('WorkSchedule._requireRead("tok-itr8-pro")', ctx);
  ok(res.error && res.error.error === 'access_denied',
    'ИТР8 pro: график ✗ (legacy READ_ROLES=Админ — Task 204)');
  res = vm.runInContext('WorkSchedule._requireWrite("tok-admin1")', ctx);
  ok(!!res.user, 'Админ: запись ✓ (legacy)');
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
