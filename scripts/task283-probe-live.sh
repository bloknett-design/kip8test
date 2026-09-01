#!/bin/bash
# Task 283: проб-запрос к живому Apps Script деплою (read-only, фейковый токен)
# Определяет, какая версия кода работает: старая (без роутинга отпусков)
# отвечает "Unknown action: workSchedule.listVacations", новая — "no_session".
URL=$(grep -o "https://script\.google\.com/macros/s/[A-Za-z0-9_-]\+/exec" \
  $(dirname "$0")/../index.html | head -1)

probe() {
  local action="$1"
  local body="$2"
  # POST -> ловим Location редиректа
  local loc=$(curl -s -m 60 -D - -o /dev/null -X POST \
    "${URL}?action=${action}" \
    -H "Content-Type: application/json" \
    -d "${body}" | grep -i '^location:' | tr -d '\r' | sed 's/^[Ll]ocation: //')
  if [ -z "$loc" ]; then echo "NO_REDIRECT (ошибка сети?)"; return; fi
  # GET по Location — тело ответа POST
  curl -s -m 60 "$loc"
}

echo "=== 1. Базлайн: zzz.probe.task283 (ожидаем Unknown action) ==="
probe "zzz.probe.task283" '{}'
echo ""
echo "=== 2. ФЛАГ: workSchedule.listVacations + фейковый токен ==="
echo "    старая версия -> Unknown action | новая -> no_session"
probe "workSchedule.listVacations" '{"token":"probe-fake-task283"}'
echo ""
echo "=== 3. Контроль: workSchedule.addTraining + фейковый токен ==="
echo "    (инструктажи работают у пользователя -> ожидаем no_session даже на старой)"
probe "workSchedule.addTraining" '{"token":"probe-fake-task283"}'
echo ""
echo "=== 4. ФЛАГ-2: workSchedule.getStatusCodes (было до Task 274) ==="
probe "workSchedule.getStatusCodes" '{"token":"probe-fake-task283"}'
echo ""
