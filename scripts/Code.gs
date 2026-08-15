// ============================================================
// Code.gs — Главный файл маршрутизации Apps Script (КИПиА)
// ============================================================
// Развёртывается в Apps Script проекте вместе с:
//   Utils.gs, CableJournal.gs, Flowmeter.gs
//
// doPost(e) — единая точка входа для всех API-вызовов.
// Клиент отправляет POST с query-параметром ?action=<action>
// и JSON-телом { token, ...params }.
// ============================================================

// ============================================================
// doGet — редирект (не используется для API)
// ============================================================
function doGet(e) {
  return HtmlService.createHtmlOutput('КИПиА API — используйте POST');
}

// ============================================================
// doPost — основной обработчик
// ============================================================
function doPost(e) {
  try {
    // Определяем action из query-параметра
    var action = e.parameter.action || '';
    // Парсим payload из тела запроса (JSON в text/plain)
    var payload = {};
    if (e.postData && e.postData.contents) {
      try {
        payload = JSON.parse(e.postData.contents);
      } catch (parseErr) {
        return jsonResponse({ ok: false, error: 'invalid_json' });
      }
    }

    // ============================================================
    // Маршрутизация по action
    // ============================================================

    // --- Авторизация / сессии ---
    if (action === 'sendOTP') {
      return jsonResponse(Utils.sendOTP(payload));
    }
    else if (action === 'verifyOTP') {
      return jsonResponse(Utils.verifyOTP(payload));
    }
    else if (action === 'getCurrentUser') {
      return jsonResponse(Utils.getCurrentUser(payload));
    }
    else if (action === 'heartbeat') {
      return jsonResponse(Utils.heartbeat(payload));
    }
    else if (action === 'logout') {
      return jsonResponse(Utils.logout(payload));
    }

    // --- Кабельный журнал ---
    else if (action === 'cableJournal.list') {
      return jsonResponse(CableJournal.list(payload));
    }
    else if (action === 'cableJournal.getColumns') {
      return jsonResponse(CableJournal.getColumns(payload));
    }
    else if (action === 'cableJournal.getFilters') {
      return jsonResponse(CableJournal.getFilters(payload));
    }
    else if (action === 'cableJournal.appendRow') {
      return jsonResponse(CableJournal.appendRow(payload));
    }
    else if (action === 'cableJournal.updateRow') {
      return jsonResponse(CableJournal.updateRow(payload));
    }
    else if (action === 'cableJournal.deleteRow') {
      return jsonResponse(CableJournal.deleteRow(payload));
    }

    // --- Расходомеры хозрасчётные (Flowmeter) ---
    else if (action === 'flowmeter.list') {
      return jsonResponse(Flowmeter.list(payload));
    }
    else if (action === 'flowmeter.updateReading') {
      return jsonResponse(Flowmeter.updateReading(payload));
    }

    // --- Админ-панель ---
    else if (action === 'adminListUsers') {
      return jsonResponse(Utils.adminListUsers(payload));
    }
    else if (action === 'adminListSessions') {
      return jsonResponse(Utils.adminListSessions(payload));
    }
    else if (action === 'adminListLogs') {
      return jsonResponse(Utils.adminListLogs(payload));
    }
    else if (action === 'adminUpdateRole') {
      return jsonResponse(Utils.adminUpdateRole(payload));
    }
    else if (action === 'adminResetLogin') {
      return jsonResponse(Utils.adminResetLogin(payload));
    }
    else if (action === 'adminCreateUser') {
      return jsonResponse(Utils.adminCreateUser(payload));
    }

    // --- Неизвестный action ---
    else {
      return jsonResponse({ ok: false, error: 'unknown_action', action: action });
    }

  } catch (err) {
    // Глобальный обработчик ошибок
    return jsonResponse({
      ok: false,
      error: 'server_error',
      message: err.toString()
    });
  }
}

// ============================================================
// Вспомогательная: обёртка для JSON-ответа
// ============================================================
function jsonResponse(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
