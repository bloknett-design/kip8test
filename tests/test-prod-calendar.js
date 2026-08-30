// tests/test-prod-calendar.js
// Task 260: тесты модуля ProdCalendar (производственный календарь РФ)
//
// Что проверяется:
//   1. Парсинг isDayOff (GitHub-зеркало) — реальные данные 2024/2026:
//      праздники, перенесённые выходные, сокращённые дни, РАБОЧИЕ
//      субботы (2024: 27.04, 28.12, 02.11).
//   2. Парсинг production-calendar.ru/v2 — типы дней 1..6, названия,
//      региональные праздники, гостевое ограничение (days строкой).
//   3. dayInfo — единая логика «нерабочий/праздник/сокращённый/рабочая
//      суббота + название»; фолбэк без данных (Сб/Вс + ст. 112 ТК РФ).
//   4. monthStats — нормы времени 40/36/24-час. недель по месяцам и
//      году (сверено с официальным календарём 2026: 247 дн., 1972 ч).
//   5. Кэш localStorage (ключ = год + регион), TTL, офлайн-устаревание.
//   6. Настройки: регион по умолчанию 42 (Кемеровская область — Кузбасс).
//   7. Интеграция в index.html: чип в тулбаре, шторка, вызовы в
//      WorkSchedule, CSS, SW-версия.
//
// Запуск: через tests/run-all.js (require './test-prod-calendar.js').

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { test, describe, assertEqual, assertTrue, assertFalse, assertApprox } = require('./test-helpers.js');

const indexPath = path.resolve(__dirname, '..', 'index.html');
const html = fs.readFileSync(indexPath, 'utf8');

// ============================================================
// Извлечение модуля ProdCalendar из index.html (vm-песочница с моком
// localStorage; сетевые методы подменяются в конкретных тестах).
// ============================================================

function extractProdCalendarSrc(src) {
    const marker = 'var ProdCalendar = {';
    const start = src.indexOf(marker);
    if (start === -1) return null;
    const braceStart = src.indexOf('{', start);
    let depth = 0;
    for (let i = braceStart; i < src.length; i++) {
        if (src[i] === '{') depth++;
        else if (src[i] === '}') {
            depth--;
            if (depth === 0) return src.slice(start, i + 1) + ';';
        }
    }
    return null;
}

const PC_SRC = extractProdCalendarSrc(html);

// Фабрика: свежий экземпляр ProdCalendar в vm-контексте с моком localStorage
function makePC(storageData) {
    const storage = {
        _d: storageData || {},
        getItem: function(k) { return (k in this._d) ? this._d[k] : null; },
        setItem: function(k, v) { this._d[String(k)] = String(v); },
        removeItem: function(k) { delete this._d[k]; }
    };
    const ctx = {
        localStorage: storage,
        console: console,
        Math: Math, Date: Date, JSON: JSON, RegExp: RegExp,
        parseInt: parseInt, parseFloat: parseFloat,
        isNaN: isNaN, isFinite: isFinite,
        String: String, Number: Number, Boolean: Boolean,
        Array: Array, Object: Object, Promise: Promise,
        setTimeout: function() { return 0; },
        clearTimeout: function() {},
        document: { getElementById: function() { return null; } }
    };
    vm.createContext(ctx);
    vm.runInContext(PC_SRC, ctx, { filename: 'index.html-ProdCalendar' });
    return { PC: ctx.ProdCalendar, storage: storage };
}

// ============================================================
// Фикстуры — РЕАЛЬНЫЕ данные источников (изъяты живыми запросами)
// ============================================================

// isDayOff 2026 (raw.githubusercontent.com/isdayoff/calendars):
// 18 нерабочих сверх Сб/Вс, 4 сокращённых, 0 рабочих суббот, 14 праздников
const IDO_2026 = {
    year: 2026, countrycode: 'ru',
    dayoff: ['0101','0102','0103','0104','0105','0106','0107','0108',
             '0109','0110','0111','0223','0309','0501','0511','0612',
             '1104','1231'],
    predayoff: ['0430','0508','0611','1103'],
    workday: [],
    holiday: ['0101','0102','0103','0104','0105','0106','0107','0108',
              '0223','0308','0501','0509','0612','1104'],
    covidday: []
};

// isDayOff 2024 — год с РАБОЧИМИ субботами (0427, 1228, 1102)
const IDO_2024 = {
    year: 2024, countrycode: 'ru',
    dayoff: ['0101','0102','0103','0104','0105','0106','0107','0108',
             '0223','0308','0429','0430','0501','0509','0510','0612',
             '1104','1230','1231'],
    predayoff: ['0222','0307','0508','0611','1102'],
    workday: ['0427','1228','1102'],
    holiday: ['0101','0102','0103','0104','0105','0106','0107','0108',
              '0223','0308','0501','0509','0612','1104'],
    covidday: []
};

// production-calendar.ru/v2 (compact): все 6 типов дней + региональный
// праздник (Радоница в Ставропольском крае — тип 4) и перенос (тип 6)
const PCAL_DAYS = [
    { date: '2026-01-01', type: { id: 3, name: 'Государственный праздник', is_working: 0 },
      title: 'Новогодние каникулы', working_hours: 0, is_project: false, is_wsch: false },
    { date: '2026-01-07', type: { id: 3, name: 'Государственный праздник', is_working: 0 },
      title: 'Рождество Христово', working_hours: 0, is_project: false, is_wsch: false },
    { date: '2026-01-09', type: { id: 6, name: 'Дополнительный / перенесенный выходной день', is_working: 0 },
      title: 'Перенос с субботы 3 января', working_hours: 0, is_project: false, is_wsch: false },
    { date: '2026-04-21', type: { id: 4, name: 'Региональный праздник', is_working: 0 },
      title: 'День поминовения усопших (Радоница)', working_hours: 0, is_project: false, is_wsch: false },
    { date: '2026-04-30', type: { id: 5, name: 'Предпраздничный сокращенный рабочий день', is_working: 1 },
      title: null, working_hours: 7, is_project: false, is_wsch: false },
    { date: '2026-10-31', type: { id: 1, name: 'Рабочий день', is_working: 1 },
      title: 'Перенос рабочего дня', working_hours: 8, is_project: true, is_wsch: false }
];

const PCAL_OK = {
    status: 'ok', period: 'месяц',
    dt_start: '2026-01-01', dt_end: '2026-01-31',
    country: { code: 'ru', name: 'Российская Федерация',
               region: { id: 42, name: 'Кемеровская область - Кузбасс' } },
    work_week: { id: 5, name: '5-дневная рабочая неделя' },
    statistics: { calendar_days: 31, work_days: 15, working_hours: 120 },
    days: PCAL_DAYS
};

// Гостевое ограничение production-calendar.ru: days = СТРОКА
const PCAL_GUEST_RESTRICTED = {
    status: 'ok', period: 'месяц',
    country: { code: 'ru', name: 'Российская Федерация', region: null },
    days: 'Данные за выбранный период недоступны для гостевого токена.'
};

// Загрузить в модуль данные isDayOff конкретного года (минуя сеть)
function loadIsDayOff(PC, json, year) {
    const parsed = PC._parseIsDayOff(json);
    PC._MEM[year] = {
        source: parsed.source,
        fetchedAtMs: Date.now(),
        region: 42,
        regionName: 'Кемеровская область - Кузбасс',
        days: parsed.days
    };
    return parsed;
}

// ============================================================
// Тесты
// ============================================================

describe('ProdCalendar: модуль определён', () => {
    test('JS: var ProdCalendar определён в index.html', () => {
        assertTrue(PC_SRC !== null && PC_SRC.indexOf('_REGIONS_RAW') !== -1,
            'Модуль ProdCalendar извлекается из index.html');
    });
    test('JS: источники данных — isDayOff GitHub и production-calendar.ru', () => {
        assertTrue(html.indexOf('raw.githubusercontent.com/isdayoff/calendars') !== -1,
            'URL isDayOff GitHub-зеркала прописан');
        assertTrue(html.indexOf('production-calendar.ru/v2/ru/') !== -1,
            'URL production-calendar.ru прописан');
    });
});

describe('ProdCalendar: парсинг isDayOff', () => {
    test('2026: 18 нерабочих сверх Сб/Вс, 4 сокращённых', () => {
        const { PC } = makePC();
        const parsed = PC._parseIsDayOff(IDO_2026);
        let offs = 0, shorts = 0, holidays = 0;
        for (const k in parsed.days) {
            if (parsed.days[k].off) offs++;
            if (parsed.days[k].short) shorts++;
            if (parsed.days[k].holiday) holidays++;
        }
        assertEqual(offs, 18, 'dayoff[] → 18 записей off');
        assertEqual(shorts, 4, 'predayoff[] → 4 записи short');
        assertEqual(holidays, 14, 'holiday[] → 14 записей holiday');
        assertEqual(parsed.source, 'isdayoff', 'источник помечен');
    });
    test('2026: 9 января — перенесённый выходной (off без holiday)', () => {
        const { PC } = makePC();
        const parsed = PC._parseIsDayOff(IDO_2026);
        assertTrue(parsed.days['0109'].off === 1 && !parsed.days['0109'].holiday,
            '0109 = off, не праздник (перенос с субботы 3 января)');
    });
    test('2024: рабочие субботы 0427/1228/1102 → work, без off', () => {
        const { PC } = makePC();
        const parsed = PC._parseIsDayOff(IDO_2024);
        assertTrue(parsed.days['0427'].work === 1 && !parsed.days['0427'].off,
            '27 апреля 2024 — рабочая суббота');
        assertTrue(parsed.days['1102'].work === 1 && parsed.days['1102'].short === 1,
            '2 ноября 2024 — рабочая И сокращённая суббота');
    });
    test('некорректный формат → null', () => {
        const { PC } = makePC();
        assertEqual(PC._parseIsDayOff(null), null);
        assertEqual(PC._parseIsDayOff({ predayoff: ['0101'] }), null,
            'нет dayoff[] → null');
        assertEqual(PC._parseIsDayOff({ dayoff: '0101' }), null,
            'dayoff не массив → null');
    });
});

describe('ProdCalendar: парсинг production-calendar.ru', () => {
    test('типы дней 1-6 → off/holiday/regional/short/work', () => {
        const { PC } = makePC();
        const parsed = PC._parseProdCal(PCAL_OK);
        assertEqual(parsed.source, 'prodcalendar');
        assertEqual(parsed.days['0101'].off, 1, 'тип 3 — нерабочий');
        assertEqual(parsed.days['0101'].holiday, 1, 'тип 3 — праздник');
        assertEqual(parsed.days['0101'].title, 'Новогодние каникулы',
            'официальное название из API');
        assertEqual(parsed.days['0109'].off, 1, 'тип 6 — нерабочий');
        assertFalse(parsed.days['0109'].holiday, 'тип 6 — не праздник');
        assertEqual(parsed.days['0109'].title, 'Перенос с субботы 3 января');
        assertEqual(parsed.days['0421'].regional, 1, 'тип 4 — региональный');
        assertEqual(parsed.days['0421'].holiday, 1, 'тип 4 — праздник');
        assertEqual(parsed.days['0430'].short, 1, 'тип 5 — сокращённый');
        assertTrue(!parsed.days['0430'].off, 'тип 5 — рабочий день');
        assertEqual(parsed.days['1031'].work, 1, 'тип 1 — рабочий перенос');
        assertEqual(parsed.days['1031'].project, 1, 'is_project сохранён');
    });
    test('гостевое ограничение (days строкой) → null', () => {
        const { PC } = makePC();
        assertEqual(PC._parseProdCal(PCAL_GUEST_RESTRICTED), null,
            'days-строка с сообщением об ограничении → источник пропускается');
    });
    test('status не ok → null', () => {
        const { PC } = makePC();
        assertEqual(PC._parseProdCal({ status: 'error', days: [] }), null);
        assertEqual(PC._parseProdCal(null), null);
    });
});

describe('ProdCalendar: dayInfo — производственный календарь 2026', () => {
    test('9 января (пт) — перенесённый выходной', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const info = PC.dayInfo(2026, 1, 9);
        assertTrue(info.off, 'нерабочий');
        assertFalse(info.holiday, 'не праздник');
        assertEqual(info.title, 'Выходной (перенесённый)');
        assertTrue(info.hasData, 'данные есть');
    });
    test('1 мая (пт) — праздник с названием из ТК РФ', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const info = PC.dayInfo(2026, 5, 1);
        assertTrue(info.off && info.holiday);
        assertEqual(info.title, 'Праздник Весны и Труда');
    });
    test('9 мая (сб) — праздник на выходном', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const info = PC.dayInfo(2026, 5, 9);
        assertTrue(info.off, 'нерабочий (суббота + праздник)');
        assertTrue(info.holiday);
        assertEqual(info.title, 'День Победы');
    });
    test('30 апреля (чт) — сокращённый рабочий день', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const info = PC.dayInfo(2026, 4, 30);
        assertFalse(info.off, 'рабочий');
        assertTrue(info.short, 'сокращённый');
        assertEqual(info.title, 'Сокращённый рабочий день');
    });
    test('23 февраля (пн) и 8 марта (вс) — праздники', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const feb = PC.dayInfo(2026, 2, 23);
        assertTrue(feb.off && feb.holiday);
        assertEqual(feb.title, 'День защитника Отечества');
        const mar = PC.dayInfo(2026, 3, 8);
        assertTrue(mar.off && mar.holiday, 'воскресенье + праздник');
        assertEqual(mar.title, 'Международный женский день');
    });
    test('31 декабря (чт) — перенесённый выходной', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const info = PC.dayInfo(2026, 12, 31);
        assertTrue(info.off && !info.holiday);
        assertEqual(info.title, 'Выходной (перенесённый)');
    });
    test('обычная среда — рабочий день без названия', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const info = PC.dayInfo(2026, 8, 12);
        assertFalse(info.off);
        assertEqual(info.title, null);
        assertTrue(info.hasData);
    });
});

describe('ProdCalendar: dayInfo — рабочие субботы 2024', () => {
    test('27 апреля (сб) — РАБОЧАЯ суббота', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2024, 2024);
        const info = PC.dayInfo(2024, 4, 27);
        assertFalse(info.off, 'выходной отменён переносом');
        assertTrue(info.work, 'рабочий перенос');
        assertEqual(info.title, 'Рабочий день (перенос)');
    });
    test('28 апреля (вс) — обычный выходной', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2024, 2024);
        const info = PC.dayInfo(2024, 4, 28);
        assertTrue(info.off && !info.work);
    });
    test('2 ноября (сб) — рабочая И сокращённая', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2024, 2024);
        const info = PC.dayInfo(2024, 11, 2);
        assertFalse(info.off);
        assertTrue(info.work && info.short);
    });
});

describe('ProdCalendar: dayInfo — фолбэк без данных', () => {
    test('Сб/Вс — нерабочие, hasData=false, source=fallback', () => {
        const { PC } = makePC();
        const sat = PC.dayInfo(2027, 8, 14);
        assertTrue(sat.off);
        assertFalse(sat.hasData);
        assertEqual(sat.source, 'fallback');
        const mon = PC.dayInfo(2027, 8, 16);
        assertFalse(mon.off);
    });
    test('праздники ст. 112 ТК РФ видны и без данных', () => {
        const { PC } = makePC();
        const may = PC.dayInfo(2027, 5, 1);
        assertTrue(may.off && may.holiday);
        assertEqual(may.title, 'Праздник Весны и Труда');
        const jan = PC.dayInfo(2027, 1, 7);
        assertEqual(jan.title, 'Рождество Христово');
    });
    test('переносы без данных НЕ известны (обычный рабочий день)', () => {
        const { PC } = makePC();
        const d = PC.dayInfo(2027, 5, 11);
        assertFalse(d.off, 'вторник 11 мая без данных — рабочий');
    });
});

describe('ProdCalendar: monthStats — нормы времени', () => {
    test('январь 2026: 15 рабочих, 120 ч (40-час)', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const st = PC.monthStats(2026, 1);
        assertEqual(st.workDays, 15);
        assertEqual(st.offDays, 16);
        assertEqual(st.shortened, 0);
        assertEqual(st.hours40, 120);
        assertEqual(st.specialDays.length, 9,
            '8 праздников (1-8 января) + 1 перенос (9 января)');
    });
    test('май 2026: 19 рабочих, 1 сокращённый, 151 ч', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const st = PC.monthStats(2026, 5);
        assertEqual(st.workDays, 19);
        assertEqual(st.offDays, 12);
        assertEqual(st.shortened, 1);
        assertEqual(st.hours40, 151);
        assertApprox(st.hours36, 135.8, 0.05, '19×7,2 − 1 = 135,8');
        assertApprox(st.hours24, 90.2, 0.05, '19×4,8 − 1 = 90,2');
        // особые дни: 1 мая (праздник), 8 (сокращённый), 9 (праздник), 11 (перенос)
        assertEqual(st.specialDays.length, 4);
        assertEqual(st.specialDays[0].kind, 'праздник');
        assertEqual(st.specialDays[1].kind, 'сокращённый');
        assertEqual(st.specialDays[3].kind, 'перенос');
    });
    test('апрель 2026: 22 рабочих, 175 ч', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const st = PC.monthStats(2026, 4);
        assertEqual(st.workDays, 22);
        assertEqual(st.hours40, 175, '22×8 − 1 = 175');
    });
    test('2026 год целиком: 247 раб. дн., 1972 / 1774,4 / 1181,6 ч', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        let workDays = 0, shortened = 0;
        for (let m = 1; m <= 12; m++) {
            const st = PC.monthStats(2026, m);
            workDays += st.workDays;
            shortened += st.shortened;
        }
        assertEqual(workDays, 247, 'официальная норма 2026 года');
        assertEqual(shortened, 4);
        assertEqual(workDays * 8 - shortened, 1972, 'норма 40-час. недели');
        assertApprox(workDays * 7.2 - shortened, 1774.4, 0.05, '36-час.');
        assertApprox(workDays * 4.8 - shortened, 1181.6, 0.05, '24-час.');
    });
    test('апрель 2024 (рабочая суббота): 21 рабочий, 168 ч', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2024, 2024);
        const st = PC.monthStats(2024, 4);
        assertEqual(st.workDays, 21, '27.04 — рабочая суббота, 29-30 — выходные');
        assertEqual(st.hours40, 168);
        assertEqual(st.specialDays.length, 3,
            '27 — рабочий перенос, 29 и 30 — перенесённые выходные');
        const kinds = st.specialDays.map(function(sd) { return sd.kind; }).join(',');
        assertEqual(kinds, 'рабочий перенос,перенос,перенос');
    });
});

describe('ProdCalendar: регионы и настройки', () => {
    test('регион по умолчанию — 42 (Кемеровская область - Кузбасс)', () => {
        const { PC } = makePC();
        const s = PC.getSettings();
        assertEqual(s.region, 42);
        assertEqual(s.token, '');
    });
    test('справочник: 89 регионов, у 42 НЕТ региональных праздников', () => {
        const { PC } = makePC();
        const regs = PC.regions();
        assertEqual(regs.length, 89);
        assertEqual(PC.regionName(42), 'Кемеровская область - Кузбасс');
        assertFalse(PC.regionHasRegional(42), 'Кузбасс — федеральный календарь');
        assertTrue(PC.regionHasRegional(16), 'Татарстан — есть региональные');
    });
    test('настройки сохраняются в localStorage', () => {
        const { PC, storage } = makePC();
        PC.setSettings({ region: 54, token: 'abc123' });
        const s = PC.getSettings();
        assertEqual(s.region, 54);
        assertEqual(s.token, 'abc123');
        assertTrue(storage._d['ws_pcal_settings_v1'] !== undefined);
    });
    test('битые настройки → значения по умолчанию', () => {
        const { PC } = makePC({ 'ws_pcal_settings_v1': '{битый json' });
        const s = PC.getSettings();
        assertEqual(s.region, 42);
        assertEqual(s.token, '');
    });
});

describe('ProdCalendar: кэш и ensureYear', () => {
    test('ключ кэша включает год и регион', () => {
        const { PC } = makePC();
        PC.setSettings({ region: 54, token: '' });
        assertEqual(PC._cacheKey(2026), 'ws_pcal_year_2026_54');
    });
    test('свежий кэш → сеть НЕ дёргается, resolve(false)', () => {
        const fresh = {
            source: 'isdayoff', fetchedAtMs: Date.now(),
            region: 42, regionName: 'Кемеровская область - Кузбасс',
            days: { '0509': { holiday: 1 } }
        };
        const { PC } = makePC({
            'ws_pcal_year_2026_42': JSON.stringify(fresh)
        });
        PC._fetchYear = function() { throw new Error('сеть не должна вызываться'); };
        let resolved = null;
        PC.ensureYear(2026, false).then(function(v) { resolved = v; });
        // синхронная проверка: _fetchYear бросил бы исключение до промиса
        assertEqual(PC._MEM[2026].days['0509'].holiday, 1, 'кэш загружен в память');
    });
    test('force=true → сеть вызывается, данные в памяти и кэше', async () => {
        const { PC, storage } = makePC();
        const parsed = PC._parseIsDayOff(IDO_2026);
        parsed.fetchedAtMs = Date.now();
        parsed.region = 42;
        parsed.regionName = 'Кемеровская область - Кузбасс';
        PC._fetchYear = function() { return Promise.resolve(parsed); };
        const changed = await PC.ensureYear(2026, true);
        assertEqual(changed, true, 'пришли новые данные');
        assertTrue(PC._MEM[2026] && PC._MEM[2026].days['0109'].off === 1, 'в памяти');
        const cached = JSON.parse(storage._d['ws_pcal_year_2026_42']);
        assertEqual(cached.source, 'isdayoff', 'в localStorage');
        assertTrue(cached.days['0501'].off === 1);
    });
    test('сбой сети → устаревший кэш продолжает работать (офлайн)', async () => {
        const stale = {
            source: 'isdayoff', fetchedAtMs: Date.now() - 10 * 24 * 3600 * 1000,
            region: 42, regionName: 'Кемеровская область - Кузбасс',
            days: { '0509': { holiday: 1 } }
        };
        const { PC } = makePC({
            'ws_pcal_year_2026_42': JSON.stringify(stale)
        });
        PC._fetchYear = function() { return Promise.reject(new Error('нет сети')); };
        const changed = await PC.ensureYear(2026, true);
        assertEqual(changed, false, 'новых данных нет');
        assertTrue(PC._MEM[2026] && PC._MEM[2026].days['0509'],
            'устаревший кэш загружен в память (офлайн-режим)');
        const info = PC.dayInfo(2026, 5, 9);
        assertTrue(info.off && info.holiday, 'День Победы работает офлайн');
    });
    test('полный отказ (нет сети, нет кэша) → фолбэк Сб/Вс', async () => {
        const { PC } = makePC();
        PC._fetchYear = function() { return Promise.resolve(null); };
        const changed = await PC.ensureYear(2030, true);
        assertEqual(changed, false);
        const info = PC.dayInfo(2030, 5, 9);
        assertFalse(info.hasData);
        assertEqual(info.source, 'fallback');
    });
    test('некорректный год → resolve(false) без сети', async () => {
        const { PC } = makePC();
        PC._fetchYear = function() { throw new Error('сеть не должна вызываться'); };
        assertEqual(await PC.ensureYear(1899, true), false);
        assertEqual(await PC.ensureYear(2101, true), false);
        assertEqual(await PC.ensureYear('abc', true), false);
    });
});

describe('ProdCalendar: утилиты', () => {
    test('_fmtHours: целые без дроби, дробные с запятой', () => {
        const { PC } = makePC();
        assertEqual(PC._fmtHours(151), '151');
        assertEqual(PC._fmtHours(135.8), '135,8');
        assertEqual(PC._fmtHours(1774.4), '1774,4');
        assertEqual(PC._fmtHours(120), '120');
    });
    test('_esc экранирует HTML', () => {
        const { PC } = makePC();
        assertEqual(PC._esc('<b>"x"&\'</b>'), '&lt;b&gt;&quot;x&quot;&amp;&#39;&lt;/b&gt;');
    });
});

describe('Task 260: интеграция в index.html', () => {
    test('HTML: чип календаря в тулбаре шахматки', () => {
        assertTrue(html.indexOf('id="wsCalChip"') !== -1 &&
                   html.indexOf('wsCalChipText') !== -1,
            'кнопка-чип wsCalChip с текстовым элементом');
        assertTrue(html.indexOf('onclick="ProdCalendar.openSheet()"') !== -1,
            'клик по чипу открывает шторку ProdCalendar.openSheet()');
        assertTrue(/id="wsCalChip"[\s\S]{0,600}?class="ws-cal-chip"/.test(html) ||
                   /class="ws-cal-chip"[\s\S]{0,600}?id="wsCalChip"/.test(html),
            'чип в тулбаре (рядом с селектами месяца/года)');
    });
    test('HTML: шторка производственного календаря', () => {
        assertTrue(html.indexOf('id="wsCalOverlay"') !== -1 &&
                   html.indexOf('id="wsCalSheet"') !== -1 &&
                   html.indexOf('id="wsCalSheetBody"') !== -1,
            'оверлей + шторка + тело шторки');
        assertTrue(html.indexOf('ProdCalendar.closeSheet()') !== -1,
            'закрытие по клику на оверлей');
    });
    test('JS: WorkSchedule запускает загрузку календаря', () => {
        assertTrue(html.indexOf('_ensureCal: function') !== -1,
            'метод _ensureCal определён');
        const initCalls = (html.match(/this\._ensureCal\(\);/g) || []).length;
        assertTrue(initCalls >= 2,
            '_ensureCal вызывается в init() и onMonthChange()');
        assertTrue(html.indexOf('self._updateCalChip();') !== -1,
            'чип норм обновляется после загрузки сетки (loadGrid)');
    });
    test('JS: ячейки шахматки используют календарь (_calDayOff)', () => {
        assertTrue(html.indexOf('_calDayOff: function') !== -1,
            'метод _calDayOff определён');
        assertTrue(html.indexOf("var dayOff = this._calDayOff(day);") !== -1,
            '_renderCell определяет нерабочий день по календарю');
        assertTrue(html.indexOf("if (dayOff) classes.push('ws-weekend');") !== -1,
            'класс ws-weekend — по календарю (Сб/Вс + праздники + переносы)');
    });
    test('JS: шапка шахматки — ws-holiday/ws-feast + тултип с названием', () => {
        assertTrue(html.indexOf("var isFeast = dInfo ? !!dInfo.holiday : false;") !== -1,
            'праздник определяется по ProdCalendar.dayInfo');
        assertTrue(html.indexOf("' ws-feast'") !== -1,
            'класс ws-feast для праздников');
        assertTrue(html.indexOf('thTitle = d + \' \' + dow + \' — \' + dInfo.title') !== -1,
            'тултип заголовка с названием праздника');
    });
    test('CSS: стили чипа, праздника и шторки', () => {
        assertTrue(html.indexOf('.ws-cal-chip {') !== -1, 'стили чипа');
        assertTrue(html.indexOf('.ws-grid thead th.ws-day-col.ws-feast {') !== -1,
            'стили праздника в шапке');
        assertTrue(html.indexOf('.ws-cal-day-kind') !== -1, 'стили списка праздников');
        assertTrue(html.indexOf('.ws-cal-norms-grid') !== -1, 'стили блока норм');
    });
    test('SW: версия кэша kipia-test-v518', () => {
        const sw = fs.readFileSync(path.resolve(__dirname, '..', 'sw.js'), 'utf8');
        assertTrue(sw.indexOf("CACHE_VERSION = 'kipia-test-v518'") !== -1,
            'CACHE_VERSION в sw.js = kipia-test-v518');
    });
    test('Тултип ячейки содержит название праздника', () => {
        assertTrue(html.indexOf('titleParts.splice(1, 0, cellInfo.title);') !== -1,
            'название вставляется в тултип ячейки');
        assertTrue(html.indexOf('popupDate += \' · \' + pdInfo.title;') !== -1,
            'название — в заголовке попапа выбора статуса');
    });
});
