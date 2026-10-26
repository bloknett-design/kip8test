// scripts/task547-repro.js — воспроизведение замечания Task 547:
// «при изменении периода отпуска сменного работника шахматка его
// рабочих дней после первого формирования остаётся пустой (дни,
// освобождённые от отпуска) и заполняется только повторным
// нажатием; ранее распределённые подменные дни другим работникам
// остаются, хотя смены отпускника вернулись».
//
// Стенд: 017/023, шаблон cycle 4 (Д/Н/—/—), старт 01.09.2026,
// месяц сентябрь 2026. Отпуск 017: 05–10 → смещается на 08–13.
// Подмены: 023 «д» 05.09 (замещает пусто — слой Task 458) и
// 023 «н» 06.09 (замещает «017» — явная связь).
//
// Запуск: node scripts/task547-repro.js

const fs = require('fs');
const path = require('path');
const WS_SRC = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'WorkSchedule.gs'), 'utf8');

class MockSheet {
    constructor(rows) { this.rows = rows || []; }
    getLastRow() { return this.rows.length; }
    getRange(row, col, numRows, numCols) {
        numRows = numRows || 1; numCols = numCols || 1;
        const self = this;
        return {
            getValues() {
                const out = [];
                for (let r = row; r < row + numRows; r++) {
                    const line = [];
                    for (let c = col; c < col + numCols; c++) {
                        const rr = self.rows[r - 1];
                        line.push(rr ? (rr[c - 1] === undefined ? '' : rr[c - 1]) : '');
                    }
                    out.push(line);
                }
                return out;
            },
            setValues(vals) {
                for (let i = 0; i < vals.length; i++) {
                    const r = row + i;
                    while (self.rows.length < r) self.rows.push([]);
                    for (let c = 0; c < vals[i].length; c++) {
                        self.rows[r - 1][col - 1 + c] = vals[i][c];
                    }
                }
            },
            setValue(v) {
                while (self.rows.length < row) self.rows.push([]);
                self.rows[row - 1][col - 1] = v;
            },
            setNumberFormat() {}
        };
    }
    deleteRow(r) { this.rows.splice(r - 1, 1); }
    appendRow(arr) { this.rows.push(arr.slice()); }
}

const MOCK_UTILS = {
    findSessionByToken: () => ({ user_id: 1 }),
    findUserById: () => ({ role: 'Админ', email: 'test@example.com' }),
    audit: () => {}
};

function loadWS(sheets) {
    const ss = { getSheetByName: (n) => sheets[n] || null };
    const SpreadsheetApp = { openById: () => ss };
    const factory = new Function('SpreadsheetApp', 'Utils', WS_SRC + '\nreturn WorkSchedule;');
    return factory(SpreadsheetApp, MOCK_UTILS);
}

function baseSheets() {
    return {
        'Сотрудники': new MockSheet([
            ['таб_номер', 'ФИО', 'тип', 'смена', 'шаблон', 'старт_цикла', 'приём', 'увольнение', 'архив', 'должность', 'комментарий'],
            ['017', 'Иванов И.И.', 'оператор', '', 1, new Date(2026, 8, 1), '', '', 0, '', ''],
            ['023', 'Петров П.П.', 'оператор', '', 1, new Date(2026, 8, 3), '', '', 0, '', '']
        ]),
        'Шаблоны_ротации': new MockSheet([
            ['id', 'name', 'cycle', 'desc'],
            [1, 'Сутки через двое', 4, '']
        ]),
        'Дни_цикла': new MockSheet([
            ['pattern_id', 'day', 'status'],
            [1, 1, 'Д'], [1, 2, 'Н'], [1, 3, ''], [1, 4, '']
        ]),
        'Инструктажи': new MockSheet([
            ['id', 'таб', 'тип', 'тема', 'начало', 'конец', 'дней', 'комментарий']
        ]),
        'Записи_графика': new MockSheet([
            ['дата', 'таб', 'статус', 'переработка', 'праздник', 'источник', 'обновлён', 'замещает', 'инструкция', 'комментарий']
        ]),
        'Отпуска': new MockSheet([
            ['id', 'таб_номер', 'часть', 'дата_начала', 'дата_окончания', 'комментарий']
        ])
    };
}

function d(y, m, dday) { return new Date(y, m - 1, dday); }
function iso(dt) {
    return dt.getFullYear() + '-' + String(dt.getMonth() + 1).padStart(2, '0') + '-' +
           String(dt.getDate()).padStart(2, '0');
}
function dump(sheets, tab) {
    const out = [];
    for (let i = 1; i < sheets['Записи_графика'].rows.length; i++) {
        const r = sheets['Записи_графика'].rows[i];
        if (String(r[1]).trim() === tab) {
            out.push(iso(r[0]) + ':' + r[2] + (r[7] ? '(зам:' + r[7] + ')' : '') +
                     '[' + r[5] + ']');
        }
    }
    return out.join(' ');
}

const sheets = baseSheets();
sheets['Отпуска'].rows.push([1, '017', 1, d(2026, 9, 5), d(2026, 9, 10), '']);
let WS = loadWS(sheets);

console.log('=== ГЕНЕРАЦИЯ #1 (отпуск 05–10) ===');
let r1 = WS.generateMonth({ token: 't', year: 2026, month: 9 });
console.log('gen:', JSON.stringify({ g: r1.data.generated, u: r1.data.updated, rm: r1.data.removed }));
console.log('017:', dump(sheets, '017'));

// Подмены (слой Task 456/458 материализован и СОХРАНЁН — записи «руч»):
// 023 «д» 05.09 — замещает ПУСТО (как пишет материализация Task 458)
// 023 «н» 06.09 — замещает «017» (явная связь, расширенная правка)
sheets['Записи_графика'].rows.push(
    [d(2026, 9, 5), '023', 'д', 0, 0, 'руч', new Date(), '', null, ''],
    [d(2026, 9, 6), '023', 'н', 0, 0, 'руч', new Date(), '017', null, '']);
console.log('023 (с подменами):', dump(sheets, '023'));

console.log('\n=== СМЕНА ПЕРИОДА ОТПУСКА: 05–10 → 08–13 ===');
const uv = WS.updateVacation({ token: 't', id: 1, 'таб_номер': '017', 'часть': 1,
                               'дата_начала': '2026-09-08', 'дата_окончания': '2026-09-13' });
console.log('updateVacation:', JSON.stringify(uv));

console.log('\n=== ГЕНЕРАЦИЯ #2 (первое нажатие после смены) ===');
let r2 = WS.generateMonth({ token: 't', year: 2026, month: 9 });
console.log('gen:', JSON.stringify({ g: r2.data.generated, u: r2.data.updated, rm: r2.data.removed }));
console.log('017:', dump(sheets, '017'));
console.log('023:', dump(sheets, '023'));

const rows017 = dump(sheets, '017');
const empty0506 = rows017.indexOf('2026-09-05:') === -1 && rows017.indexOf('2026-09-06:') === -1;
console.log('\nДИАГНОЗ: дни 05–06 у 017 ' + (empty0506 ? 'ПУСТЫЕ (баг подтверждён)' : 'заполнены'));
const sub0606 = dump(sheets, '023').indexOf('2026-09-06:н') !== -1;
console.log('Подмена 06.09 у 023 (замещает 017): ' + (sub0606 ? 'ОСТАЛАСЬ (баг подтверждён)' : 'удалена'));

console.log('\n=== ГЕНЕРАЦИЯ #3 (повторное нажатие) ===');
let r3 = WS.generateMonth({ token: 't', year: 2026, month: 9 });
console.log('gen:', JSON.stringify({ g: r3.data.generated, u: r3.data.updated, rm: r3.data.removed }));
console.log('017:', dump(sheets, '017'));
console.log('023:', dump(sheets, '023'));
