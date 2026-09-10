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
require('./test-task322.js');
require('./test-task323.js');
require('./test-task324.js');
require('./test-task325.js');
require('./test-task326.js');
require('./test-task327.js');
require('./test-task328.js');
require('./test-task329.js');
require('./test-task330.js');
require('./test-task331.js');
require('./test-task333.js');
require('./test-task334.js');
require('./test-task335.js');
require('./test-task336.js');
require('./test-task337.js');
require('./test-task338.js');
require('./test-task340.js');
require('./test-task341.js');
require('./test-task342.js');
require('./test-task343.js');
// Task 346 — политика сессий «1 моб + 1 десктоп» (device в verifyOTP,
// тост evicted, бейдж устройства в админ-панели, справочник сервера)
require('./test-task346.js');
// Task 347 — автосчистка «заброшенных» строк sessions (Utils.cleanupStaleSessions,
// справочник Utils.gs теперь в репо; вызов из hourlyCleanup в Code.gs)
require('./test-task347.js');
// Task 348 — Utilities.getUuid() вместо Math.random (токены + OTP) и
// Utils.withLock (LockService) от гонок; гард node --check всех .gs
require('./test-task348.js');
// Task 349 — удалён мёртвый IP-код (per-IP лимит + getClientIp/UA),
// SESSION_ORPHAN_REMOVED → SESSION_CLEANUP_ORPHAN, updateRole: замок +
// синхрон sessions!D + мгновенная выгонка при «Запрет»
require('./test-task349.js');
// Task 350 — замки на последние мутации (крон-чистки, verifyOTP с пере-чтением
// OTP, sendOTP кулдаун+appendRow под замком) + батч-удаления deleteRows(5, N)
require('./test-task350.js');
// Task 351 — Admin.deleteUser (гарды себя/последнего админа, сессии+OTP),
// кэш чтений на выполнение (beginExecution/инвалидация), listLogs-хвост
// (getLastRows), устойчивый getConfig с числовым дефолтом
require('./test-task351.js');
// Task 352 — анти-DoS: email-блок sendOTP удалён (countRecentOtpFails мёртв),
// верный код работает после лимита неудач, дешёвый отказ без инкремента/аудита
require('./test-task352.js');
// Task 353 — UI удаления пользователя в админ-панели: кнопка «Удалить»
// (свой аккаунт disabled), модалка подтверждения, ошибка — в модалке,
// текстовая XSS-безопасность email (textContent), фильтр журнала
require('./test-task353.js');
// Task 354 — легаси-сборка для Windows 7/8.1: Electron 22.3.27, флаг
// kipiaWin7Legacy, двойной путь protocol.handle/registerBufferProtocol,
// isRemoteAvailable через net, PE-верификация в CI (полные ассерты —
// только в kip8-desktop, в прочих репо — синк-заглушка)
require('./test-task354.js');
// Task 355 — шахматка табеля: «·» убрана из нерабочих выходных/праздничных
// ячеек; линии ячеек и шапки (дни месяца) тонкие 1px, но ярче (30% чёрного
// в светлой / стале-голубой 55% в тёмной); розовый выходных пастельнее
// #f7d9e3 → #f8e2e9 (обе темы)
require('./test-task355.js');
// Task 356 — шахматка табеля: «·» убрана и из ПУСТЫХ ячеек рабочих дней
// (пустая/«.»/статус-мероприятие — чистый центр, как выходные после
// Task 355; бейджи, коды и планы «ОТ» — прежние)
require('./test-task356.js');
require('./test-task357.js');
require('./test-task358.js');
require('./test-deploy-url.js');

// Запускаем
runAll().then(exitCode => {
    process.exit(exitCode);
}).catch(err => {
    console.error('Критическая ошибка при выполнении тестов:', err);
    process.exit(1);
});
