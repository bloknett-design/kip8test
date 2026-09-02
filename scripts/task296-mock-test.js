#!/usr/bin/env node
/**
 * task296-mock-test.js — мок-тест Этапа 4 (Task 296): клиент переключён
 * на серверную карту прав из матрицы KIP8_Access (action getMyAccess,
 * Task 295): KipAuth._serverAccess/_fetchMyAccess/_applyServerAccess
 * (оверлей ROLE_ACCESS по правам) + FlowmeterData._computeCanInputReadings
 * (flowmeter.input из матрицы).
 *
 * МЕТОД: KipAuth и FlowmeterData извлекаются из index.html пословным
 * брейс-матчингом литералов (приложение объявляет их внутри
 * DOMContentLoaded-колбэка — глобально недостижимы) и исполняются в
 * песочнице vm с моками DOM/localStorage/timers. API-вызовы заменены
 * стабами. ДАННЫЕ РЕАЛЬНЫЕ: матрица 12 ролей × 13 прав — снята с живой
 * таблицы KIP8_Access (файл fixture совпадает с task295-mock-test.js).
 *
 * КЛЮЧЕВЫЕ ПРОВЕРКИ:
 *   A. Инициализация: карта ролей, легаси-список ввода не тронут.
 *   B. Оверлей по ВСЕМ 12 ролям = легаси-карта, КРОМЕ осознанных
 *      изменений матрицы: «ИТР8 pro» + график работы. Восстановление
 *      легаси после сброса.
 *   C. canAccess точечно (включая оба осознанных изменения).
 *   D. Кнопка «Ввести показания»: матрица → «ИТР ИОС» ВИДИТ ввод
 *      (главный баг-фикс задачи); без карты — легаси; fail-closed.
 *   E. _fetchMyAccess: успешный цикл (api→кэш→оверлей→UI-флаг),
 *      ошибки (старый сервер/сеть) не ломают приложение.
 *   F. _loadCachedMyAccess: валидный/чужой/битый кэш, сброс при logout.
 *   G. Статические хуки: все точки вызова в index.html + sw.js v539.
 */
'use strict';

const fs = require('fs');
const vm = require('vm');

const INDEX = __dirname + '/../index.html';
const SW = __dirname + '/../sw.js';
const html = fs.readFileSync(INDEX, 'utf-8');
const swJs = fs.readFileSync(SW, 'utf-8');

// ==========================================================================
// РЕАЛЬНЫЕ ДАННЫЕ (KIP8_Access, снятие 02.09.2026 — как в task295)
// ==========================================================================

const REAL_PERMS = [
  'calc.view', 'library.view', 'kipios.view', 'kipios.restricted',
  'cablejournal.edit', 'admin.panel', 'secret.view', 'whatsnew.view',
  'charts.view', 'flowmeter.view', 'flowmeter.input',
  'workschedule.view', 'workschedule.edit'
];

const REAL_ROLES = [
  ['zapret',       'Запрет',           0,0,0,0,0,0,0,0,0,0,0,0,0],
  ['common',       'Общий доступ',     1,0,0,0,0,0,0,0,0,0,0,0,0],
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

/** Ответ сервера getMyAccess для роли (формат RoleMatrixGate.rmGetMyAccess). */
function accessFor(roleName) {
  const row = REAL_ROLES.filter(function (r) { return r[1] === roleName; })[0] || null;
  const perms = {};
  REAL_PERMS.forEach(function (p, i) { perms[p] = row ? row[2 + i] === 1 : false; });
  return {
    userId: 1, email: 't@example.com', role: roleName,
    roleId: row ? row[0] : '', found: !!row, isAdmin: roleName === 'Админ',
    permissions: perms,
    granted: Object.keys(perms).filter(function (k) { return perms[k]; }),
    warnings: []
  };
}

// ==========================================================================
// ЭКСТРАКЦИЯ ЛИТЕРАЛОВ ИЗ index.html (брейс-матчинг со строками/комментами)
// ==========================================================================

function extractLiteral(src, marker) {
  const start = src.indexOf(marker);
  if (start === -1) throw new Error('маркер не найден: ' + marker);
  const openIdx = src.indexOf('{', start + marker.length);
  let depth = 0, i = openIdx;
  let str = null, comment = null;
  while (i < src.length) {
    const c = src[i], n = src[i + 1];
    if (comment === 'line') { if (c === '\n') comment = null; i++; continue; }
    if (comment === 'block') { if (c === '*' && n === '/') { comment = null; i += 2; continue; } i++; continue; }
    if (str) {
      if (c === '\\') { i += 2; continue; }
      if (c === str) str = null;
      i++; continue;
    }
    if (c === '/' && n === '/') { comment = 'line'; i += 2; continue; }
    if (c === '/' && n === '*') { comment = 'block'; i += 2; continue; }
    if (c === '\'' || c === '"' || c === '`') { str = c; i++; continue; }
    if (c === '{') depth++;
    if (c === '}') {
      depth--;
      if (depth === 0) return src.slice(openIdx, i + 1);
    }
    i++;
  }
  throw new Error('непарные скобки для ' + marker);
}

// ==========================================================================
// ПЕСОЧНИЦА
// ==========================================================================

function mockElement(id) {
  const el = {
    id: id, value: '', style: {},
    classList: { add: function () {}, remove: function () {},
      contains: function () { return false; }, toggle: function () {} },
    setAttribute: function () {}, getAttribute: function () { return null; },
    addEventListener: function () {}, removeEventListener: function () {},
    querySelector: function () { return null; }, querySelectorAll: function () { return []; },
    appendChild: function () {}, removeChild: function () {},
    closest: function () { return null; },
    scrollIntoView: function () {}, focus: function () {}, click: function () {}
  };
  Object.defineProperty(el, 'textContent', {
    get: function () { return this._tc || ''; },
    set: function (v) { this._tc = String(v == null ? '' : v); },
    enumerable: true, configurable: true
  });
  Object.defineProperty(el, 'innerHTML', {
    get: function () { return this._ih || ''; },
    set: function (v) { this._ih = String(v == null ? '' : v); },
    enumerable: true, configurable: true
  });
  return el;
}

const els = {};
const storage = {};
const realSetTimeout = global.setTimeout;

function makeSandbox() {
  const sb = {
    document: {
      getElementById: function (id) { if (!els[id]) els[id] = mockElement(id); return els[id]; },
      querySelector: function () { return null; },
      querySelectorAll: function () { return []; },
      addEventListener: function () {}, createElement: function (t) { return mockElement(t); },
      documentElement: mockElement('html'), body: mockElement('body'), head: mockElement('head')
    },
    window: {
      innerWidth: 375, innerHeight: 812, scrollY: 0, pageYOffset: 0,
      matchMedia: function () { return { matches: false, addEventListener: function () {}, addListener: function () {} }; },
      addEventListener: function () {}, scrollTo: function () {}, close: function () {},
      location: { reload: function () {}, hash: '' }
    },
    navigator: { vibrate: function () {}, clipboard: { writeText: function () { return Promise.resolve(); } } },
    localStorage: {
      getItem: function (k) { return k in storage ? storage[k] : null; },
      setItem: function (k, v) { storage[String(k)] = String(v); },
      removeItem: function (k) { delete storage[k]; }
    },
    console: { log: function () {}, warn: function () {}, error: function () {}, info: function () {} },
    Math: Math, Date: Date, JSON: JSON, parseInt: parseInt, parseFloat: parseFloat,
    isNaN: isNaN, isFinite: isFinite,
    String: String, Number: Number, Boolean: Boolean, Array: Array, Object: Object,
    Promise: Promise,
    setTimeout: function (fn, ms) { const t = realSetTimeout(fn, ms); if (t.unref) t.unref(); return t; },
    clearTimeout: global.clearTimeout,
    setInterval: function () { return 0; },
    clearInterval: function () {},
    fetch: function () { return Promise.reject(new TypeError('no net')); },
    showToast: function () {}, alert: function () {}
  };
  vm.createContext(sb);
  return sb;
}

const sb = makeSandbox();
// KipAuth и FlowmeterData — как глобалы песочницы (внутри литералов
// методы ссылаются на них по имени в момент ВЫЗОВА).
vm.runInContext('var KipAuth = ' + extractLiteral(html, 'const KipAuth =') + ';', sb, { filename: 'KipAuth.literal' });
vm.runInContext('var FlowmeterData = ' + extractLiteral(html, 'var FlowmeterData =') + ';', sb, { filename: 'FlowmeterData.literal' });
const KipAuth = sb.KipAuth;
const FlowmeterData = sb.FlowmeterData;

// ==========================================================================
// СЧЁТЧИК
// ==========================================================================

let passed = 0, failed = 0;
function ok(cond, label) {
  if (cond) { passed++; }
  else { failed++; console.log('  ✗ FAIL: ' + label); }
}
function sorted(list) { return list.slice().sort(); }
function sameSet(a, b) { return JSON.stringify(sorted(a)) === JSON.stringify(sorted(b)); }

// ==========================================================================
// A. Инициализация
// ==========================================================================

console.log('A. Инициализация и извлечение');
ok(typeof KipAuth === 'object' && typeof KipAuth.init === 'function', 'KipAuth извлечён');
ok(typeof FlowmeterData === 'object' && typeof FlowmeterData._computeCanInputReadings === 'function', 'FlowmeterData извлечён');
KipAuth.init();
const legacy = {};
Object.keys(KipAuth.ROLE_ACCESS).forEach(function (r) { legacy[r] = KipAuth.ROLE_ACCESS[r].slice(); });
ok(Object.keys(KipAuth.ROLE_ACCESS).length === 12, '12 ролей в ROLE_ACCESS');
ok(KipAuth._accessBase && Object.keys(KipAuth._accessBase).length === 12, '_accessBase: снимок 12 ролей (Task 296)');
ok(JSON.stringify(KipAuth._accessBase['Админ']) === '["*"]', 'Админ — ["*"], не трогаем');
ok(JSON.stringify(FlowmeterData._INPUT_READINGS_ROLES) === '["КИП ИОС дежурный","Админ"]', 'легаси-список ввода не тронут (запас)');
ok(typeof KipAuth._fetchMyAccess === 'function' && typeof KipAuth._applyServerAccess === 'function' &&
   typeof KipAuth._serverPerm === 'function' && typeof KipAuth._loadCachedMyAccess === 'function' &&
   typeof KipAuth._resetServerAccess === 'function', 'методы Task 296 на месте');

// ==========================================================================
// B. Оверлей по 12 ролям = легаси, кроме «ИТР8 pro» (+график работы)
// ==========================================================================

console.log('B. Оверлей матрицы: все 12 ролей');
REAL_ROLES.forEach(function (row) {
  const role = row[1];
  KipAuth._cachedRole = role;
  KipAuth._serverAccess = accessFor(role);
  KipAuth._applyServerAccess();
  let want = legacy[role].slice();
  if (role === 'ИТР8 pro') want = want.concat(KipAuth._WORK_SCHEDULE_PAGES);
  ok(sameSet(KipAuth.ROLE_ACCESS[role], want),
    role + ': страницы ' + (role === 'ИТР8 pro' ? '= легаси + график работы (осознанное изменение)' : '= легаси'));
  KipAuth._resetServerAccess();
  ok(sameSet(KipAuth.ROLE_ACCESS[role], legacy[role]), role + ': сброс восстанавливает легаси');
});
KipAuth._serverAccess = null;

// ==========================================================================
// C. canAccess точечно
// ==========================================================================

console.log('C. canAccess после применения матрицы');
function applyRole(role) {
  KipAuth._cachedRole = role;
  KipAuth._serverAccess = accessFor(role);
  KipAuth._applyServerAccess();
}
applyRole('ИТР8 pro');
ok(KipAuth.canAccess('work-schedule') === true, 'ИТР8 pro: график работы — ВИДЕН (осознанное изменение)');
ok(KipAuth.canAccess('work-schedule-employees') === true, 'ИТР8 pro: сотрудники графика — видны');
ok(KipAuth.canAccess('flowmeter-data') === true, 'ИТР8 pro: расходомеры — видны');
applyRole('ИТР8');
ok(KipAuth.canAccess('work-schedule') === false, 'ИТР8: график работы — скрыт (нет workschedule.view)');
ok(KipAuth.canAccess('flowmeter-data') === true, 'ИТР8: расходомеры — видны');
applyRole('ИТР ИОС');
ok(KipAuth.canAccess('flowmeter-data') === true, 'ИТР ИОС: расходомеры — видны');
ok(KipAuth.canAccess('work-schedule') === false, 'ИТР ИОС: график — скрыт');
ok(KipAuth.canAccess('cable-journal-edit') === true, 'ИТР ИОС: каб. журнал — виден (kipios.view)');
applyRole('КИП ИОС');
ok(KipAuth.canAccess('flowmeter-data') === false, 'КИП ИОС: расходомеры — скрыты (нет flowmeter.view)');
ok(KipAuth.canAccess('kip-ios') === true, 'КИП ИОС: КИП ИОС — виден');
applyRole('КИП8 pro');
ok(KipAuth.canAccess('flowmeter-data') === true, 'КИП8 pro: расходомеры — видны');
ok(KipAuth.canAccess('docs-ios') === true, 'КИП8 pro: «Документация ИОС» — видна (вход к расходомерам)');
ok(KipAuth.canAccess('kip-ios') === false, 'КИП8 pro: КИП ИОС — скрыт');
applyRole('ИТР ТОКЕМ');
ok(KipAuth.canAccess('docs') === true, 'ИТР ТОКЕМ: «Документация» — видна (kipios.restricted)');
ok(KipAuth.canAccess('kip-ios') === true, 'ИТР ТОКЕМ: КИП ИОС — виден (фильтр 4)');
ok(KipAuth.canAccess('library') === false, 'ИТР ТОКЕМ: библиотека — скрыта');
applyRole('Запрет');
ok(KipAuth.canAccess('dashboard') === true, 'Запрет: главная — видна');
ok(KipAuth.canAccess('calculators') === false, 'Запрет: калькуляторы — скрыты');
applyRole('Общий доступ');
ok(KipAuth.canAccess('calculators') === true, 'Общий доступ: калькуляторы — видны');
ok(KipAuth.canAccess('kip-ios') === false, 'Общий доступ: КИП ИОС — скрыт');
applyRole('Админ');
ok(KipAuth.canAccess('work-schedule') === true, 'Админ: график — виден (["*"] не тронут)');
ok(KipAuth.canAccess('admin') === true, 'Админ: админ-панель — видна');
KipAuth._resetServerAccess();

// ==========================================================================
// D. Кнопка «Ввести показания» (_computeCanInputReadings)
// ==========================================================================

console.log('D. Право ввода показаний');
function inputFor(role, access) {
  KipAuth._cachedRole = role;
  KipAuth._serverAccess = access;
  return FlowmeterData._computeCanInputReadings();
}
ok(inputFor('ИТР ИОС', accessFor('ИТР ИОС')) === true, 'ИТР ИОС + матрица → ВВОД ЕСТЬ (главный баг-фикс)');
ok(inputFor('КИП ИОС дежурный', accessFor('КИП ИОС дежурный')) === true, 'дежурный + матрица → ввод есть');
ok(inputFor('Админ', accessFor('Админ')) === true, 'Админ + матрица → ввод есть');
ok(inputFor('КИП8 pro', accessFor('КИП8 pro')) === false, 'КИП8 pro + матрица → ввода нет');
ok(inputFor('ИТР8', accessFor('ИТР8')) === false, 'ИТР8 + матрица → ввода нет');
ok(inputFor('ИТР8 pro', accessFor('ИТР8 pro')) === false, 'ИТР8 pro + матрица → ввода нет');
ok(inputFor('КИП ИОС', accessFor('КИП ИОС')) === false, 'КИП ИОС + матрица → ввода нет');
ok(inputFor('Запрет', accessFor('Запрет')) === false, 'Запрет + матрица → ввода нет');
// Без карты (старый сервер/сеть) — легаси-поведение:
ok(inputFor('ИТР ИОС', null) === false, 'ИТР ИОС без карты → легаси (кнопки нет — как сегодня)');
ok(inputFor('КИП ИОС дежурный', null) === true, 'дежурный без карты → легаси (кнопка есть)');
ok(inputFor('Админ', null) === true, 'Админ без карты → легаси (кнопка есть)');
// Роль не найдена в матрице → fail-closed:
ok(inputFor('ИТР ИОС', { found: false, permissions: {}, role: 'ИТР ИОС' }) === false, 'ИТР ИОС found=false → ввода нет (fail-closed)');
// _applyRoleToUI обновляет флаг на живом объекте:
KipAuth._cachedRole = 'ИТР ИОС';
KipAuth._serverAccess = accessFor('ИТР ИОС');
KipAuth._applyServerAccess();
FlowmeterData._canInputReadings = false;
KipAuth._applyRoleToUI();
ok(FlowmeterData._canInputReadings === true, '_applyRoleToUI пересчитал флаг ввода (ИТР ИОС → true)');

// ==========================================================================
// E. _fetchMyAccess (async)
// ==========================================================================

console.log('E. _fetchMyAccess');
(async function () {
  // E1: успешный цикл
  const calls = [];
  KipAuth.api = function (action, payload) {
    calls.push({ action: action, token: payload && payload.token });
    return Promise.resolve(accessFor('ИТР8 pro'));
  };
  KipAuth.setToken('tok-e1');
  KipAuth._cachedRole = 'ИТР8 pro';
  KipAuth._serverAccess = null;
  KipAuth._resetServerAccess();
  const r1 = await KipAuth._fetchMyAccess();
  ok(r1 && r1.role === 'ИТР8 pro', 'E1: resolve данными карты');
  ok(calls.length === 1 && calls[0].action === 'getMyAccess' && calls[0].token === 'tok-e1', 'E1: api(getMyAccess, token)');
  ok(KipAuth._serverAccess && KipAuth._serverAccess.found === true, 'E1: _serverAccess установлен');
  ok((storage['kip8_my_access'] || '').indexOf('"role":"ИТР8 pro"') !== -1, 'E1: кэш kip8_my_access записан');
  ok(KipAuth.canAccess('work-schedule') === true, 'E1: оверлей применён (график виден)');
  // E2: сервер без getMyAccess (старый деплой) — не ломает приложение
  KipAuth.api = function () {
    const e = new Error('Unknown action: getMyAccess');
    e._kind = 'SERVER';
    return Promise.reject(e);
  };
  let threw = false;
  try { await KipAuth._fetchMyAccess(); } catch (e) { threw = true; }
  ok(!threw, 'E2: отказ не бросается наружу');
  ok(KipAuth._serverAccess && KipAuth._serverAccess.role === 'ИТР8 pro', 'E2: прежняя карта сохранена');
  ok(KipAuth.canAccess('work-schedule') === true, 'E2: оверлей не сломан');
  // E3: сетевая ошибка — аналогично
  KipAuth.api = function () {
    const e = new Error('NETWORK_ERROR: Failed to fetch');
    e._kind = 'NETWORK';
    return Promise.reject(e);
  };
  threw = false;
  try { await KipAuth._fetchMyAccess(); } catch (e) { threw = true; }
  ok(!threw && KipAuth.canAccess('work-schedule') === true, 'E3: сеть — не ломает, оверлей жив');
  // E4: нет токена — запрос не выполняется
  calls.length = 0;
  KipAuth.clearToken();
  const r4 = await KipAuth._fetchMyAccess();
  ok(r4 === null && calls.length === 0, 'E4: без токена api не вызывается');
  // E5: мусорный ответ
  KipAuth.setToken('tok-e5');
  KipAuth.api = function () { return Promise.resolve('мусор'); };
  const r5 = await KipAuth._fetchMyAccess();
  ok(r5 === null, 'E5: не-объект → null, не бросается');
  // E6: полный цикл «ИТР ИОС» — флаг ввода на живом FlowmeterData
  KipAuth.api = function () { return Promise.resolve(accessFor('ИТР ИОС')); };
  KipAuth._cachedRole = 'ИТР ИОС';
  KipAuth._serverAccess = null;
  FlowmeterData._canInputReadings = false;
  await KipAuth._fetchMyAccess();
  ok(FlowmeterData._canInputReadings === true, 'E6: ИТР ИОС — кнопка «Ввести показания» после fetch');
  ok(KipAuth.canAccess('flowmeter-data') === true, 'E6: ИТР ИОС — расходомеры видны');
  KipAuth._resetServerAccess();
  KipAuth.clearToken();

  // ========================================================================
  // F. _loadCachedMyAccess + logout
  // ========================================================================

  console.log('F. Кэш карты и logout');
  // F1: валидный кэш той же роли
  KipAuth._cachedRole = 'ИТР8 pro';
  KipAuth._serverAccess = null;
  KipAuth._resetServerAccess();
  storage['kip8_my_access'] = JSON.stringify(accessFor('ИТР8 pro'));
  KipAuth._loadCachedMyAccess('ИТР8 pro');
  ok(KipAuth.canAccess('work-schedule') === true, 'F1: кэш применён (график виден до ответа сервера)');
  // F2: кэш чужой роли — игнор
  KipAuth._cachedRole = 'ИТР8';
  KipAuth._serverAccess = null;
  KipAuth._resetServerAccess();
  storage['kip8_my_access'] = JSON.stringify(accessFor('ИТР8 pro'));
  KipAuth._loadCachedMyAccess('ИТР8');
  ok(KipAuth.canAccess('work-schedule') === false, 'F2: кэш чужой роли не применяется');
  // F3: битый JSON (кэш чужой роли уже неактуален — пишем мусор)
  storage['kip8_my_access'] = '{битый';
  let threwF3 = false;
  try { KipAuth._loadCachedMyAccess('ИТР8'); } catch (e) { threwF3 = true; }
  ok(!threwF3, 'F3: битый кэш не бросается');
  // F4: logout сбрасывает всё
  storage['kip8_my_access'] = JSON.stringify(accessFor('ИТР8 pro'));
  KipAuth._cachedRole = 'ИТР8 pro';
  KipAuth._serverAccess = accessFor('ИТР8 pro');
  KipAuth._applyServerAccess();
  KipAuth.setToken('tok-f4');
  KipAuth.api = function () { return Promise.resolve({}); };
  KipAuth.logout();
  ok(!('kip8_my_access' in storage), 'F4: кэш карты удалён при logout');
  ok(KipAuth._serverAccess === null, 'F4: _serverAccess сброшен');
  ok(sameSet(KipAuth.ROLE_ACCESS['ИТР8 pro'], legacy['ИТР8 pro']), 'F4: легаси-карта роли восстановлена');
  ok(KipAuth.getToken() === '', 'F4: токен сброшен');
  ok(KipAuth._cachedRole === 'Общий доступ', 'F4: гостевой режим');

  // ========================================================================
  // G. Статические хуки (index.html + sw.js)
  // ========================================================================

  console.log('G. Точки вызова в исходнике');
  const n = function (s) { return html.split(s).length - 1; };
  ok(n('self._fetchMyAccess();') === 4, 'G: _fetchMyAccess() в 4 хуках (вход, heartbeat, bootstrap, фоновая проверка)');
  ok(n('_loadCachedMyAccess(cachedRole)') === 1, 'G: быстрый путь bootstrap применяет кэш карты');
  ok(n('this._resetServerAccess();') === 2, 'G: сброс карты в logout и handleSessionExpired');
  ok(n("api('getMyAccess'") === 1, 'G: единственный вызов getMyAccess');
  ok(n("localStorage.setItem('kip8_my_access'") === 1, 'G: запись кэша карты');
  ok(n('FlowmeterData._canInputReadings = FlowmeterData._computeCanInputReadings();') === 1, 'G: флаг ввода пересчитывается в _applyRoleToUI');
  ok(swJs.indexOf('kipia-test-v539') !== -1, 'G: sw.js — v539');
  ok(swJs.indexOf('kipia-test-v538') === -1, 'G: sw.js — старой версии нет');

  // ========================================================================
  console.log('\n════════════════════════════════════════');
  console.log('ИТОГО Task 296: ' + passed + ' passed / ' + failed + ' failed');
  console.log('════════════════════════════════════════');
  process.exit(failed > 0 ? 1 : 0);
})().catch(function (e) {
  console.error('ФАТАЛЬНАЯ ОШИБКА ТЕСТА:', e && e.stack || e);
  process.exit(2);
});
