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
//   8. Task 264: День города Кемерово (12 июня, регион 42, вместе с
//      Днём России), окошко календаря в тулбаре (нормы и праздники
//      месяца), звёздочка сокращённых предпраздничных дней.
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
        assertEqual(PC._cacheKey(2026), 'ws_pcal_year2_2026_54');
    });
    test('свежий кэш → сеть НЕ дёргается, resolve(false)', () => {
        const fresh = {
            source: 'isdayoff', fetchedAtMs: Date.now(),
            region: 42, regionName: 'Кемеровская область - Кузбасс',
            days: { '0509': { holiday: 1 } }
        };
        const { PC } = makePC({
            'ws_pcal_year2_2026_42': JSON.stringify(fresh)
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
        const cached = JSON.parse(storage._d['ws_pcal_year2_2026_42']);
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
            'ws_pcal_year2_2026_42': JSON.stringify(stale)
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
    test('CSS: стили чипа, праздника, окошка и шторки', () => {
        assertTrue(html.indexOf('.ws-cal-chip {') !== -1, 'стили чипа');
        assertTrue(html.indexOf('.ws-grid thead th.ws-day-col.ws-feast {') !== -1,
            'стили праздника в шапке');
        assertTrue(html.indexOf('.ws-cp-day.k-hol') !== -1,
            'стили чипов праздников в окошке тулбара');
        assertTrue(html.indexOf('.ws-cal-panel {') !== -1,
            'стили окошка календаря в тулбаре');
    });
    test('SW: версия кэша kipia-test-v523 (Task 267)', () => {
        const sw = fs.readFileSync(path.resolve(__dirname, '..', 'sw.js'), 'utf8');
        assertTrue(sw.indexOf("CACHE_VERSION = 'kipia-test-v523'") !== -1,
            'CACHE_VERSION в sw.js = kipia-test-v523');
    });
    test('Тултип ячейки содержит название праздника', () => {
        assertTrue(html.indexOf('titleParts.splice(1, 0, cellInfo.title);') !== -1,
            'название вставляется в тултип ячейки');
        assertTrue(html.indexOf('popupDate += \' · \' + pdInfo.title;') !== -1,
            'название — в заголовке попапа выбора статуса');
    });
});

// ============================================================
// Task 262: legalic — основной источник, официальные нормы,
// цепочки переносов, 2027 preliminary, День шахтёра (регион 42)
// ============================================================

// Фикстуры legalic. Особые дни 2026 — РЕАЛЬНЫЕ (export
// calendar.legalic.ru/api/v1/calendars/RU-FEDERAL/export?year=2026):
// 14 праздников, 4 перенесённых выходных, 4 сокращённых, 0 рабочих
// суббот. Полный год генерируется: WORKING = 480/432/288 мин,
// SHORTENED_WORKING = 420/372/228 мин (суммы минут = официальные
// нормы: 247 дн. → 1972 / 1774,4 / 1181,6 ч).
const LG2026_SPECIAL = {
    '0101': { t: 'PUBLIC_HOLIDAY', n: 'Новогодние каникулы' },
    '0102': { t: 'PUBLIC_HOLIDAY', n: 'Новогодние каникулы' },
    '0103': { t: 'PUBLIC_HOLIDAY', n: 'Новогодние каникулы' },
    '0104': { t: 'PUBLIC_HOLIDAY', n: 'Новогодние каникулы' },
    '0105': { t: 'PUBLIC_HOLIDAY', n: 'Новогодние каникулы' },
    '0106': { t: 'PUBLIC_HOLIDAY', n: 'Новогодние каникулы' },
    '0107': { t: 'PUBLIC_HOLIDAY', n: 'Рождество Христово' },
    '0108': { t: 'PUBLIC_HOLIDAY', n: 'Новогодние каникулы' },
    '0109': { t: 'TRANSFERRED_DAY_OFF', from: '2026-01-03' },
    '0223': { t: 'PUBLIC_HOLIDAY', n: 'День защитника Отечества' },
    '0308': { t: 'PUBLIC_HOLIDAY', n: 'Международный женский день', to: '2026-03-09' },
    '0309': { t: 'TRANSFERRED_DAY_OFF', from: '2026-03-08' },
    '0430': { t: 'SHORTENED_WORKING' },
    '0501': { t: 'PUBLIC_HOLIDAY', n: 'Праздник Весны и Труда' },
    '0508': { t: 'SHORTENED_WORKING' },
    '0509': { t: 'PUBLIC_HOLIDAY', n: 'День Победы' },
    '0511': { t: 'TRANSFERRED_DAY_OFF', from: '2026-05-09' },
    '0611': { t: 'SHORTENED_WORKING' },
    '0612': { t: 'PUBLIC_HOLIDAY', n: 'День России' },
    '1103': { t: 'SHORTENED_WORKING' },
    '1104': { t: 'PUBLIC_HOLIDAY', n: 'День народного единства' },
    '1231': { t: 'TRANSFERRED_DAY_OFF', from: '2026-01-04' }
};

// Генератор полного года legalic (WORKING/WEEKEND достраиваются,
// минуты соответствуют реальным суммам источника)
function buildLegalicYear(year, special, status) {
    const days = [];
    for (let m = 1; m <= 12; m++) {
        const last = new Date(year, m, 0).getDate();
        for (let d = 1; d <= last; d++) {
            const mmdd = (m < 10 ? '0' : '') + m + (d < 10 ? '0' : '') + d;
            const dow = new Date(year, m - 1, d).getDay();
            const sp = special[mmdd] || {};
            const weekend = dow === 0 || dow === 6;
            const type = sp.t || (weekend ? 'WEEKEND' : 'WORKING');
            const minutes = type === 'WORKING' ? { '40h': 480, '36h': 432, '24h': 288 }
                          : type === 'SHORTENED_WORKING' ? { '40h': 420, '36h': 372, '24h': 228 }
                          : { '40h': 0, '36h': 0, '24h': 0 };
            const day = {
                date: year + '-' + mmdd.slice(0, 2) + '-' + mmdd.slice(2),
                weekday: (dow + 6) % 7,
                type: type,
                isWorking: type === 'WORKING' || type === 'SHORTENED_WORKING' ||
                           type === 'TRANSFERRED_WORKING',
                shortened: type === 'SHORTENED_WORKING',
                minutes: minutes
            };
            if (sp.n) day.holidayName = sp.n;
            if (sp.from) day.transferredFrom = sp.from;
            if (sp.to) day.transferredTo = sp.to;
            days.push(day);
        }
    }
    return {
        version: { versionId: 'RU-FEDERAL-' + year + '-v1', year: year,
                   status: status || 'OFFICIAL' },
        contentHash: 'sha256:test',
        days: days
    };
}

// Загрузить в модуль данные legalic года (минуя сеть), регион 42
function loadLegalic(PC, json, year) {
    const parsed = PC._parseLegalic(json);
    parsed.region = 42;
    parsed.regionName = 'Кемеровская область - Кузбасс';
    parsed.fetchedAtMs = Date.now();
    PC._applyRegionalOverlay(year, parsed);
    PC._MEM[year] = parsed;
    return parsed;
}

describe('Task 262: legalic — парсинг и официальные нормы', () => {
    test('JS: источник legalic прописан в index.html (основной)', () => {
        assertTrue(html.indexOf('calendar.legalic.ru/api/v1/calendars/RU-FEDERAL/export') !== -1,
            'URL legalic export прописан');
        assertTrue(html.indexOf('_fetchLegalic: function') !== -1,
            'метод _fetchLegalic определён');
    });
    test('парсинг: типы дней → off/holiday/short/work + переносы', () => {
        const { PC } = makePC();
        const parsed = PC._parseLegalic(buildLegalicYear(2026, LG2026_SPECIAL));
        assertEqual(parsed.source, 'legalic', 'источник legalic');
        assertEqual(parsed.days['0501'].off, 1, '1 мая — нерабочий');
        assertEqual(parsed.days['0501'].holiday, 1, '1 мая — праздник');
        assertEqual(parsed.days['0501'].title, 'Праздник Весны и Труда', 'название из holidayName');
        assertEqual(parsed.days['0109'].off, 1, '9 января — перенесённый выходной');
        assertEqual(parsed.days['0109'].tFrom, '0103', 'перенос С 03.01');
        assertEqual(parsed.days['0308'].tTo, '0309', 'перенос НА 09.03');
        assertEqual(parsed.days['0430'].short, 1, '30 апреля — сокращённый');
        assertTrue(!parsed.days['0105'] || parsed.days['0105'].holiday === 1,
            'обычные дни без признаков не записываются');
        assertEqual(parsed.version.id, 'RU-FEDERAL-2026-v1', 'версия календаря');
        assertEqual(parsed.preliminary, false, '2026 — OFFICIAL');
    });
    test('парсинг: TRANSFERRED_WORKING (рабочая суббота 01.11.2025)', () => {
        const { PC } = makePC();
        const parsed = PC._parseLegalic({
            version: { versionId: 'RU-FEDERAL-2025-v1', year: 2025, status: 'OFFICIAL' },
            days: [
                { date: '2025-11-01', weekday: 5, type: 'TRANSFERRED_WORKING',
                  isWorking: true, shortened: true,
                  minutes: { '40h': 420, '36h': 372, '24h': 228 },
                  transferredTo: '2025-11-03' },
                { date: '2025-11-03', weekday: 1, type: 'TRANSFERRED_DAY_OFF',
                  isWorking: false, shortened: false,
                  minutes: { '40h': 0, '36h': 0, '24h': 0 },
                  transferredFrom: '2025-11-01' }
            ]
        });
        assertEqual(parsed.days['1101'].work, 1, 'рабочая суббота');
        assertEqual(parsed.days['1101'].short, 1, 'и сокращённая');
        assertEqual(parsed.days['1101'].tTo, '1103', 'выходной перенесён на 03.11');
        assertEqual(parsed.days['1103'].off, 1, '03.11 — нерабочий');
        assertEqual(parsed.days['1103'].tFrom, '1101', 'перенос с 01.11');
    });
    test('парсинг: некорректный формат → null', () => {
        const { PC } = makePC();
        assertEqual(PC._parseLegalic(null), null);
        assertEqual(PC._parseLegalic({ days: 'x' }), null);
        assertEqual(PC._parseLegalic({ days: [] }), null); // нет version.versionId
    });
    test('официальные нормы 2026 из минут: год и месяцы', () => {
        const { PC } = makePC();
        const parsed = PC._parseLegalic(buildLegalicYear(2026, LG2026_SPECIAL));
        assertEqual(parsed.norms.official, true);
        assertEqual(parsed.norms.year.h40, 1972, '40-час: 1972 ч');
        assertEqual(parsed.norms.year.h36, 1774.4, '36-час: 1774,4 ч');
        assertEqual(parsed.norms.year.h24, 1181.6, '24-час: 1181,6 ч');
        assertEqual(parsed.norms.months['01'].h40, 120, 'январь: 120 ч');
        assertEqual(parsed.norms.months['05'].h40, 151, 'май: 151 ч');
        assertEqual(parsed.norms.months['04'].h40, 175, 'апрель: 175 ч');
    });
    test('PRELIMINARY (2027, проект Минтруда) → флаг preliminary', () => {
        const { PC } = makePC();
        const parsed = PC._parseLegalic(buildLegalicYear(2027, {}, 'PRELIMINARY'));
        assertEqual(parsed.preliminary, true, 'год предварительный');
        assertEqual(parsed.version.status, 'PRELIMINARY');
    });
});

describe('Task 262: День шахтёра (Кузбасс, регион 42)', () => {
    test('_minersDayMmdd: последнее воскресенье августа 2024-2027', () => {
        const { PC } = makePC();
        assertEqual(PC._minersDayMmdd(2024), '0825', '2024: 25 августа');
        assertEqual(PC._minersDayMmdd(2025), '0831', '2025: 31 августа');
        assertEqual(PC._minersDayMmdd(2026), '0830', '2026: 30 августа');
        assertEqual(PC._minersDayMmdd(2027), '0829', '2027: 29 августа');
    });
    test('оверлей: для региона 42 добавляется, для 54 — нет', () => {
        const a = makePC();
        const parsedA = a.PC._parseLegalic(buildLegalicYear(2026, LG2026_SPECIAL));
        parsedA.region = 42;
        a.PC._applyRegionalOverlay(2026, parsedA);
        assertTrue(parsedA.days['0830'] && parsedA.days['0830'].regional === 1,
            '30.08.2026 — региональный праздник');
        assertEqual(parsedA.days['0830'].title, 'День шахтёра');
        assertEqual(parsedA.days['0830'].holiday, 1);
        assertEqual(parsedA.days['0830'].off, 1);

        const b = makePC();
        const parsedB = b.PC._parseLegalic(buildLegalicYear(2026, LG2026_SPECIAL));
        parsedB.region = 54;
        b.PC._applyRegionalOverlay(2026, parsedB);
        assertTrue(!parsedB.days['0830'], 'для региона 54 оверлей не применяется');
    });
    test('оверлей не перетирает уже размеченный день', () => {
        const { PC } = makePC();
        const parsed = PC._parseLegalic(buildLegalicYear(2026, {
            '0830': { t: 'TRANSFERRED_WORKING', to: '2026-09-01' }
        }));
        parsed.region = 42;
        PC._applyRegionalOverlay(2026, parsed);
        assertEqual(parsed.days['0830'].work, 1, 'рабочий перенос сохранён');
        assertTrue(!parsed.days['0830'].regional, 'региональная метка не ставится');
    });
    test('dayInfo: 30.08.2026 — День шахтёра (региональный праздник)', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const info = PC.dayInfo(2026, 8, 30);
        assertTrue(info.off, 'нерабочий');
        assertTrue(info.holiday, 'праздник');
        assertTrue(info.regional, 'региональный');
        assertEqual(info.title, 'День шахтёра');
    });
    test('фолбэк без данных: День шахтёра вычисляется для 42', () => {
        const { PC } = makePC(); // регион по умолчанию 42
        const info = PC.dayInfo(2026, 8, 30);
        assertEqual(info.source, 'fallback');
        assertTrue(info.holiday && info.regional, 'праздник региональный');
        assertEqual(info.title, 'День шахтёра');
        assertTrue(info.off, 'воскресенье — нерабочий');
    });
    test('фолбэк без данных: для региона 54 Дня шахтёра нет', () => {
        const { PC } = makePC();
        PC.setSettings({ region: 54, token: '' });
        const info = PC.dayInfo(2026, 8, 30);
        assertFalse(info.holiday, 'не праздник');
        assertFalse(info.regional, 'не региональный');
        assertEqual(info.title, null);
    });
    test('monthStats: август 2026 содержит День шахтёра в особых днях', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const st = PC.monthStats(2026, 8);
        const miners = st.specialDays.filter(function(x) { return x.title === 'День шахтёра'; });
        assertEqual(miners.length, 1, 'ровно один день');
        assertEqual(miners[0].d, 30);
        assertEqual(miners[0].kind, 'региональный праздник');
    });
    test('HTML: закон № 186-ОЗ упоминается в index.html', () => {
        assertTrue(html.indexOf('186-ОЗ') !== -1, 'ссылка на Закон Кемеровской области');
    });
});

describe('Task 262: цепочки переносов в dayInfo', () => {
    test('9 января 2026: «Выходной, перенесённый с 03.01.2026»', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const info = PC.dayInfo(2026, 1, 9);
        assertTrue(info.off && !info.holiday, 'нерабочий, не праздник');
        assertEqual(info.title, 'Выходной, перенесённый с 03.01.2026');
        assertEqual(info.transferFrom, '03.01.2026');
    });
    test('8 марта 2026: праздник + «выходной перенесён на 09.03.2026»', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const info = PC.dayInfo(2026, 3, 8);
        assertTrue(info.holiday, 'праздник (воскресенье)');
        assertEqual(info.title, 'Международный женский день (выходной перенесён на 09.03.2026)');
        assertEqual(info.transferTo, '09.03.2026');
    });
    test('31 декабря 2026: перенесённый с 04.01.2026', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const info = PC.dayInfo(2026, 12, 31);
        assertTrue(info.off, 'нерабочий');
        assertEqual(info.title, 'Выходной, перенесённый с 04.01.2026');
    });
    test('рабочая суббота 01.11.2025: «выходной перенесён на 03.11.2025»', () => {
        const { PC } = makePC();
        PC._MEM[2025] = {
            source: 'legalic', fetchedAtMs: Date.now(), region: 42,
            regionName: 'Кемеровская область - Кузбасс',
            version: { id: 'RU-FEDERAL-2025-v1', status: 'OFFICIAL' },
            norms: { official: true, months: {}, year: null },
            days: {
                '1101': { work: 1, short: 1, tTo: '1103' },
                '1103': { off: 1, tFrom: '1101' }
            }
        };
        const sat = PC.dayInfo(2025, 11, 1);
        assertFalse(sat.off, 'суббота рабочая');
        assertTrue(sat.work, 'флаг work');
        assertEqual(sat.title, 'Рабочий день (перенос): выходной перенесён на 03.11.2025');
        const mon = PC.dayInfo(2025, 11, 3);
        assertTrue(mon.off, 'понедельник нерабочий');
        assertEqual(mon.title, 'Выходной, перенесённый с 01.11.2025');
    });
    test('30 апреля 2026: сокращённый рабочий день', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const info = PC.dayInfo(2026, 4, 30);
        assertFalse(info.off, 'рабочий');
        assertTrue(info.short, 'сокращённый');
        assertEqual(info.title, 'Сокращённый рабочий день');
    });
});

describe('Task 262: официальные нормы в monthStats', () => {
    test('январь 2026: 15 раб. дн., 120/108/72 ч — официальные', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const st = PC.monthStats(2026, 1);
        assertEqual(st.source, 'legalic');
        assertEqual(st.workDays, 15);
        assertEqual(st.hours40, 120);
        assertEqual(st.hours36, 108);
        assertEqual(st.hours24, 72);
        assertEqual(st.normsOfficial, true, 'нормы официальные');
        assertEqual(st.yearHours40, 1972, 'годовая норма 40-час.');
        assertEqual(st.version.id, 'RU-FEDERAL-2026-v1');
        assertEqual(st.preliminary, false);
    });
    test('май 2026: 19 раб. дн., 151 ч; апрель: 175 ч', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const may = PC.monthStats(2026, 5);
        assertEqual(may.workDays, 19);
        assertEqual(may.hours40, 151);
        assertEqual(may.shortened, 1, '8 мая сокращённый');
        const apr = PC.monthStats(2026, 4);
        assertEqual(apr.workDays, 22);
        assertEqual(apr.hours40, 175);
    });
    test('год 2026 суммарно: 247 раб. дн. (сверка всех месяцев)', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        let wd = 0;
        for (let m = 1; m <= 12; m++) wd += PC.monthStats(2026, m).workDays;
        assertEqual(wd, 247, '247 рабочих дней в году');
    });
    test('isDayOff-данные: нормы остаются локальным расчётом', () => {
        const { PC } = makePC();
        loadIsDayOff(PC, IDO_2026, 2026);
        const st = PC.monthStats(2026, 5);
        assertEqual(st.source, 'isdayoff');
        assertEqual(st.normsOfficial, false, 'локальный расчёт');
        assertEqual(st.hours40, 151, 'совпадает с официальным');
    });
    test('PRELIMINARY-год: monthStats.preliminary = true', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2027, {}, 'PRELIMINARY'), 2027);
        const st = PC.monthStats(2027, 1);
        assertEqual(st.preliminary, true, '2027 — предварительные данные');
        assertEqual(st.version.status, 'PRELIMINARY');
    });
});

describe('Task 262: приоритет источников _fetchYear', () => {
    test('регион 42 (даже с токеном): legalic первый, оверлей применён', async () => {
        const { PC } = makePC();
        PC.setSettings({ region: 42, token: 'tok' });
        const calls = [];
        PC._fetchLegalic = function() {
            calls.push('legalic');
            return Promise.resolve({
                source: 'legalic', fetchedAtMs: Date.now(),
                region: 42, regionName: 'Кемеровская область - Кузбасс',
                days: { '0501': { off: 1, holiday: 1 } }
            });
        };
        PC._fetchIsDayOff = function() { calls.push('isdayoff'); return Promise.resolve(null); };
        PC._fetchProdCal = function() { calls.push('prodcal'); return Promise.resolve(null); };
        const data = await PC._fetchYear(2026);
        assertEqual(data.source, 'legalic', 'победил legalic');
        assertEqual(calls.join(','), 'legalic', 'другие источники не дёргались');
        assertTrue(data.days['0830'] && data.days['0830'].regional === 1,
            'День шахтёра наложен');
    });
    test('токен + регион с региональными праздниками → production-calendar.ru первый', async () => {
        const { PC } = makePC();
        PC.setSettings({ region: 26, token: 'tok' }); // Ставропольский край, type 2
        const calls = [];
        PC._fetchProdCal = function() {
            calls.push('prodcal');
            return Promise.resolve({
                source: 'prodcalendar', fetchedAtMs: Date.now(),
                region: 26, regionName: 'Ставропольский край',
                days: { '0421': { off: 1, holiday: 1, regional: 1 } }
            });
        };
        PC._fetchLegalic = function() { calls.push('legalic'); return Promise.resolve(null); };
        PC._fetchIsDayOff = function() { calls.push('isdayoff'); return Promise.resolve(null); };
        const data = await PC._fetchYear(2026);
        assertEqual(data.source, 'prodcalendar', 'победил prodcal (региональный)');
        assertEqual(calls.join(','), 'prodcal');
        assertTrue(!data.days['0830'], 'День шахтёра не для этого региона');
    });
    test('legalic недоступен → isDayOff (резерв)', async () => {
        const { PC } = makePC();
        PC.setSettings({ region: 42, token: '' });
        PC._fetchLegalic = function() { return Promise.reject(new Error('down')); };
        PC._fetchIsDayOff = function() {
            const parsed = PC._parseIsDayOff(IDO_2026);
            parsed.fetchedAtMs = Date.now();
            parsed.region = 42;
            parsed.regionName = 'Кемеровская область - Кузбасс';
            return Promise.resolve(parsed);
        };
        const data = await PC._fetchYear(2026);
        assertEqual(data.source, 'isdayoff', 'резерв сработал');
        assertTrue(data.days['0830'] && data.days['0830'].regional === 1,
            'День шахтёра наложен и на резерв');
    });
    test('все источники недоступны → null (фолбэк Сб/Вс)', async () => {
        const { PC } = makePC();
        PC.setSettings({ region: 42, token: 'tok' });
        PC._fetchLegalic = function() { return Promise.reject(new Error('down')); };
        PC._fetchIsDayOff = function() { return Promise.reject(new Error('down')); };
        PC._fetchProdCal = function() { return Promise.reject(new Error('down')); };
        const data = await PC._fetchYear(2026);
        assertEqual(data, null, 'все отказали — null');
    });
});

describe('Task 262: кэш v2 и подписи источников', () => {
    test('кэш v2 хранит version/norms и вычищает старый ключ Task 260', () => {
        const { PC, storage } = makePC({
            'ws_pcal_year_2026_42': '{"source":"isdayoff","fetchedAtMs":1,"days":{}}'
        });
        PC.setSettings({ region: 42, token: '' });
        PC._saveCache(2026, {
            source: 'legalic', fetchedAtMs: 12345,
            region: 42, regionName: 'Кемеровская область - Кузбасс',
            version: { id: 'RU-FEDERAL-2026-v1', status: 'OFFICIAL' },
            norms: { official: true, months: { '01': { h40: 120 } }, year: { h40: 1972 } },
            days: { '0101': { off: 1 } }
        });
        const cached = JSON.parse(storage._d['ws_pcal_year2_2026_42']);
        assertEqual(cached.source, 'legalic', 'legalic принимается кэшем');
        assertEqual(cached.version.id, 'RU-FEDERAL-2026-v1', 'версия в кэше');
        assertEqual(cached.norms.year.h40, 1972, 'нормы в кэше');
        assertTrue(!('ws_pcal_year_2026_42' in storage._d), 'старый ключ вычищен');
        // чтение обратно
        const loaded = PC._loadCache(2026);
        assertEqual(loaded.version.id, 'RU-FEDERAL-2026-v1');
    });
    test('_sourceLabel: legalic — основной источник', () => {
        const { PC } = makePC();
        assertTrue(PC._sourceLabel('legalic').indexOf('calendar.legalic.ru') !== -1);
        assertTrue(PC._sourceLabel('isdayoff').indexOf('isDayOff') !== -1);
        assertTrue(PC._sourceLabel('prodcalendar').indexOf('production-calendar.ru') !== -1);
    });
});

describe('Task 262: интеграция в index.html', () => {
    test('JS: цепочки переносов в тултипах (перенесён с/на)', () => {
        assertTrue(html.indexOf("title = 'Выходной, перенесённый с ' + tFrom;") !== -1,
            '«Выходной, перенесённый с …» в названии дня');
        assertTrue(html.indexOf("' (выходной перенесён на ' + tTo + ')'" ) !== -1,
            '«(выходной перенесён на …)» у праздников на Сб/Вс');
        assertTrue(html.indexOf(': выходной перенесён на ' + String.fromCharCode(39) + ' + tTo') !== -1,
            'рабочая суббота объясняет перенос');
    });
    test('CSS: бейдж «предварительные данные» (официальные нормы убраны — Task 266)', () => {
        assertTrue(html.indexOf('.ws-cal-prelim') !== -1, 'стили бейджа preliminary');
        // Task 266: бейдж «официальные нормы» убран из окошка вместе со стилями
        assertTrue(html.indexOf('.ws-cal-official') === -1,
            'стили бейджа официальных норм удалены (Task 266)');
        assertTrue(html.indexOf("На ' + y + ' год (40-час): <b>'") !== -1,
            'строка годовой нормы — в окошке тулбара');
    });
    test('JS: шторка упоминает День шахтёра и версию календаря', () => {
        assertTrue(html.indexOf('День шахтёра (последнее воскресенье августа, Закон') !== -1,
            'подсказка региона 42 в шторке');
        assertTrue(html.indexOf('Версия календаря:') !== -1, 'строка версии в шторке');
    });
    test('JS: окошко помечает официальность (тултип) и предварительность', () => {
        assertTrue(html.indexOf("st.normsOfficial ? ' — официальные данные' : ''") !== -1,
            'тултип норм окошка: официальные данные');
        assertTrue(html.indexOf('>предварительно</span>') !== -1,
            'бейдж «предварительно» в окошке');
    });
});

// ============================================================
// Task 264: День города Кемерово (12 июня, вместе с Днём России,
// регион 42), звёздочка сокращённых дней, окошко календаря в тулбаре
// ============================================================

describe('Task 264: День города Кемерово (12 июня, регион 42)', () => {
    test('dayInfo: 12.06.2026 — «День России · День города Кемерово»', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const info = PC.dayInfo(2026, 6, 12);
        assertTrue(info.off, 'нерабочий');
        assertTrue(info.holiday, 'праздник');
        assertEqual(info.title, 'День России · День города Кемерово');
    });
    test('для региона 54 День города не добавляется', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        PC.setSettings({ region: 54, token: '' });
        assertEqual(PC.dayInfo(2026, 6, 12).title, 'День России');
    });
    test('фолбэк без данных: комбинированное название и без источника', () => {
        const { PC } = makePC(); // регион по умолчанию 42
        const info = PC.dayInfo(2026, 6, 12);
        assertEqual(info.source, 'fallback');
        assertEqual(info.title, 'День России · День города Кемерово');
    });
    test('фолбэк для региона 54: только День России', () => {
        const { PC } = makePC();
        PC.setSettings({ region: 54, token: '' });
        assertEqual(PC.dayInfo(2026, 6, 12).title, 'День России');
    });
    test('monthStats: 12 июня — праздник с двойным названием', () => {
        const { PC } = makePC();
        loadLegalic(PC, buildLegalicYear(2026, LG2026_SPECIAL), 2026);
        const st = PC.monthStats(2026, 6);
        const d12 = st.specialDays.filter(function(x) { return x.d === 12; });
        assertEqual(d12.length, 1, 'ровно одна запись');
        assertEqual(d12[0].kind, 'праздник');
        assertEqual(d12[0].title, 'День России · День города Кемерово');
    });
    test('_isCityDay: только 0612 и только регион 42', () => {
        const { PC } = makePC();
        assertTrue(PC._isCityDay('0612'), 'регион 42, 12 июня');
        assertFalse(PC._isCityDay('0613'), 'другая дата');
        PC.setSettings({ region: 54, token: '' });
        assertFalse(PC._isCityDay('0612'), 'не Кузбасс');
    });
});

describe('Task 264: окошко календаря в баре кнопок графика', () => {
    test('HTML: тулбар — ряд кнопок (.ws-toolbar-main) + окошко wsCalPanel', () => {
        assertTrue(html.indexOf('id="wsCalPanel"') !== -1, 'контейнер окошка');
        assertTrue(html.indexOf('class="ws-toolbar-main"') !== -1,
            'ряд кнопок .ws-toolbar-main');
        // Task 266: мобильная база — колонка (кнопки сверху, окошко ниже);
        // на десктопе (≥1024px) тулбар — строка: окошко слева, кнопки справа
        assertTrue(/\.ws-toolbar \{[^}]*flex-direction:\s*column/.test(html),
            'мобильная база тулбара — колонка');
        assertTrue(html.indexOf('.ws-cal-panel[hidden] { display: none; }') !== -1,
            'скрытие окошка до первых данных');
    });
    test('JS: ProdCalendar.renderPanel вызывается из _updateCalChip', () => {
        assertTrue(html.indexOf('renderPanel: function') !== -1,
            'метод renderPanel определён');
        assertTrue(html.indexOf('ProdCalendar.renderPanel();') !== -1,
            'вызов из WorkSchedule._updateCalChip');
    });
    test('JS: окошко показывает нормы 40/36/24 и годовую', () => {
        assertTrue(html.indexOf('Рабочих: <b>') !== -1, 'рабочие дни в окошке');
        assertTrue(html.indexOf('40-час: <b>') !== -1, 'норма 40-час в окошке');
        assertTrue(html.indexOf('36-час: <b>') !== -1, 'норма 36-час в окошке');
        assertTrue(html.indexOf('24-час: <b>') !== -1, 'норма 24-час в окошке');
        assertTrue(html.indexOf("На ' + y + ' год (40-час): <b>'") !== -1,
            'годовая норма в окошке');
    });
    test('JS: нормы и праздники ПЕРЕМЕЩЕНЫ из шторки в окошко', () => {
        assertTrue(html.indexOf('.ws-cal-norms-grid') === -1,
            'блок норм шторки (и его CSS) удалён');
        assertTrue(html.indexOf('Нормы времени и праздники месяца — ') !== -1,
            'подсказка о переезде в шторке');
        assertTrue(html.indexOf('нет праздников и переносов') !== -1,
            'пустое состояние списка в окошке');
    });
    test('JS: звёздочка сокращённого дня в шапке + легенда', () => {
        assertTrue(html.indexOf('<i class="ws-short-star">*</i>') !== -1,
            'звёздочка у числа дня в шапке шахматки');
        assertTrue(html.indexOf('* — сокращённый предпраздничный день') !== -1,
            'легенда звёздочки в окошке');
        assertTrue(html.indexOf('(сокращённый день, −1 час)') !== -1,
            'пояснение в тултипе шапки');
    });
});

// ============================================================
// Task 266: ревизия окошка календаря в баре кнопок графика —
// столбики (нормы слева, праздники справа), окошко в левой части
// бара / кнопки в правой, статическая высота бара + скролл в
// окошке; убраны строка «источник: …» и бейдж «официальные нормы»
// ============================================================

describe('Task 266: окошко столбиками, слева в баре — кнопки справа', () => {
    test('CSS: столбики — вертикальные списки (.ws-cp-col)', () => {
        assertTrue(/\.ws-cp-col \{[^}]*flex-direction:\s*column/.test(html),
            'столбик — колонка (нормы/праздники столбиком)');
        assertTrue(/\.ws-cp-col \{[^}]*flex-shrink:\s*0/.test(html),
            'столбик не сжимается — переносится при нехватке ширины');
        assertTrue(html.indexOf('ws-cp-col ws-cp-norms') !== -1,
            'столбик норм в renderPanel');
        assertTrue(html.indexOf('ws-cp-col ws-cp-days') !== -1,
            'столбик праздников в renderPanel');
    });
    test('CSS: статическая высота окошка + скролл внутри', () => {
        assertTrue(/\.ws-cal-panel \{[^}]*height:\s*132px/.test(html),
            'фиксированная высота окошка (мобильная база)');
        assertTrue(/\.ws-cal-panel \{[^}]*overflow-y:\s*auto/.test(html),
            'полоса прокрутки, если столбики не входят');
        assertTrue(/\.ws-cal-panel \{[^}]*overscroll-behavior:\s*contain/.test(html),
            'скролл окошка не тянет страницу');
    });
    test('CSS: десктоп — окошко слева, кнопки справа (≥1024px)', () => {
        const mq = html.match(/@media \(min-width: 1024px\) \{[\s\S]*?\.ws-toolbar \{[\s\S]*?\}/);
        assertTrue(!!mq, 'media-блок десктопного тулбара');
        assertTrue(/\.ws-cal-panel \{[^}]*order:\s*0/.test(html),
            'окошко — левая часть бара (order: 0)');
        assertTrue(/\.ws-cal-panel \{[^}]*flex:\s*1 1 auto/.test(html),
            'окошко растягивается на свободную ширину слева');
        assertTrue(/\.ws-toolbar-main \{[^}]*margin-left:\s*auto/.test(html),
            'кнопки прижаты в правую часть бара');
        assertTrue(/\.ws-toolbar-main \{[^}]*flex-wrap:\s*nowrap/.test(html),
            'ряд кнопок на десктопе — в одну строку');
    });
    test('CSS: высота бара на десктопе — 160px (статическая)', () => {
        const re = /@media \(min-width: 1024px\) \{[\s\S]*?\.ws-cal-panel \{[^}]*height:\s*160px/s;
        assertTrue(re.test(html), 'десктопная высота окошка — 160px');
    });
    test('JS: убраны источник и время обновления из окошка', () => {
        // строки источника больше нет ни в JS, ни в CSS окошка
        assertTrue(html.indexOf('ws-cp-src') === -1,
            'класс строки источника удалён');
        assertTrue(html.indexOf('_sourceShort') === -1,
            'метод _sourceShort удалён (был нужен только для окошка)');
        assertTrue(html.indexOf("', обновлено ' + this._fmtDateTime") === -1,
            'время обновления не выводится в окошке');
        // источник остался в шторке настроек
        assertTrue(html.indexOf('_sourceLabel') !== -1,
            'полная подпись источника — в шторке');
    });
    test('JS: бейдж «официальные нормы» не рендерится', () => {
        assertTrue(html.indexOf('>официальные нормы</span>') === -1,
            'бейдж удалён из renderPanel');
        // официальность осталась тултипом столбика норм
        assertTrue(html.indexOf("st.normsOfficial ? ' — официальные данные' : ''") !== -1,
            'тултип столбика норм помечает официальность');
    });
    test('JS: легенда звёздочки — в конце столбика праздников', () => {
        assertTrue(html.indexOf('ws-cp-legend') !== -1,
            'класс легенды в окошке');
        assertTrue(html.indexOf('ws-cp-legend">* — сокращённый предпраздничный день') !== -1,
            'легенда — последний элемент столбика праздников');
    });
    test('JS: renderPanel — заголовки обоих столбиков', () => {
        assertTrue(html.indexOf('ws-cp-cap">Норма, ') !== -1,
            'заголовок столбика норм');
        assertTrue(html.indexOf('ws-cp-cap">Праздники и переносы</span>') !== -1,
            'заголовок столбика праздников');
    });
});
