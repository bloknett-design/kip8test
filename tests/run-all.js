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
require('./test-flow-period-input.js');
require('./test-work-schedule.js');
require('./test-prod-calendar.js');
require('./test-vacations-init.js');
require('./test-vacations-generate.js');
require('./test-vacations-diagnose.js');
require('./test-vacations-feedback.js');
require('./test-work-events.js');
require('./test-tab-numbers.js');
require('./test-vacation-shift.js');
require('./test-task306.js');
require('./test-task309.js');
require('./test-task310.js');
require('./test-task311.js');
require('./test-task312.js');
require('./test-task313.js');
require('./test-task314.js');
require('./test-task315.js');
require('./test-task316.js');
require('./test-task317.js');
require('./test-task318.js');
require('./test-task319.js');
require('./test-task320.js');
require('./test-task321.js');
require('./test-deploy-url.js');

// Запускаем
runAll().then(exitCode => {
    process.exit(exitCode);
}).catch(err => {
    console.error('Критическая ошибка при выполнении тестов:', err);
    process.exit(1);
});
