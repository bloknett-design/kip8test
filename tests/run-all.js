// ============================================================
// Главный раннер тестов КИПиА
// ============================================================
// Запуск: node tests/run-all.js
// Возвращает код 0 при успехе, 1 при наличии ошибок.
// Используется в CI (GitHub Actions) для блокировки деплоя
// при падении тестов.
// ============================================================

const { runAll } = require('./test-helpers.js');

// Проверяем, что index.html существует
const fs = require('fs');
const path = require('path');
const indexPath = path.resolve(__dirname, '..', 'index.html');
if (!fs.existsSync(indexPath)) {
    console.error('ОШИБКА: index.html не найден по пути ' + indexPath);
    process.exit(1);
}

// Подключаем все тестовые файлы — они при require регистрируют тесты
require('./test-format.js');
require('./test-signal.js');
require('./test-buoy.js');
require('./test-rtd.js');
require('./test-thermocouple.js');
require('./test-orifice.js');
require('./test-utils.js');
require('./test-role-access.js');
require('./test-minesweeper.js');
require('./test-flowmeter-comment.js');
require('./test-flowmeter-validation.js');
require('./test-work-schedule.js');
require('./test-prod-calendar.js');
require('./test-vacations-init.js');
require('./test-vacations-generate.js');
require('./test-vacations-diagnose.js');

// Запускаем
runAll().then(exitCode => {
    process.exit(exitCode);
}).catch(err => {
    console.error('Критическая ошибка при выполнении тестов:', err);
    process.exit(1);
});
