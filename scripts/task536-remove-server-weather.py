#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 536 — удаление НЕРАБОЧЕЙ серверной погоды из WorkSchedule.gs.
Заявка: «Через сервер погода не загружается, работает только через
wttr.in (напрямую из браузера), поэтому убери из кода WorkSchedule.gs
не рабочие строки кода связанные с погодой».

Удаляет:
  1) строку эндпоинта workSchedule.getWeather из шапки-индекса;
  2) блок getWeather (Task 530 → 532 → 534) + парсеры
     _parseMeteoinfo + _parseOpenMeteo (~230 строк);
  3) топ-уровневую authorizeWeather() с инструкцией (Task 534/535).

НЕ трогает: _getProdCal (legalic.ru — производственный календарь,
там свой UrlFetchApp с фолбэком — это НЕ погода).
Идемпотентен: повторный запуск — «уже сделано».
"""
import io
import sys

PATH = '/home/z/my-project/kip8test/scripts/WorkSchedule.gs'
src = io.open(PATH, encoding='utf-8').read()
orig_len = src.count('\n') + 1
changed = []

# ---------- 1. шапка: строка эндпоинта ----------
HDR = ('//   workSchedule.getWeather      — погода Кемерово: meteoinfo.ru +\n'
       '//                                   резерв open-meteo.com (Task 532);\n'
       '//                                   Task 534: топ-уровневая функция\n'
       '//                                   authorizeWeather() — разовая\n'
       '//                                   авторизация внешних запросов\n')
if HDR in src:
    src = src.replace(HDR, '', 1)
    changed.append('шапка: 5 строк эндпоинта getWeather')

# ---------- 2. блок getWeather + парсеры ----------
A2 = '  // workSchedule.getWeather (Task 530'
B2 = '  // workSchedule.getPatterns'
i2 = src.find(A2)
if i2 != -1:
    j2 = src.find(B2, i2)
    assert j2 != -1, 'якорь getPatterns не найден'
    NOTE2 = (
        '  // Task 536 — СЕРВЕРНАЯ ПОГОДА УДАЛЕНА (getWeather,\n'
        '  // _parseMeteoinfo, _parseOpenMeteo). Причина (заявка):\n'
        '  // серверные запросы UrlFetchApp (meteoinfo.ru,\n'
        '  // open-meteo.com) падали — развёртыванию не хватало области\n'
        '  // script.external_request, авторизацию пользователь так и не\n'
        '  // выдал. Погода идёт НАПРЯМУЮ из браузера: open-meteo.com →\n'
        '  // wttr.in (Task 533/534 — клиентский код WsLcdClock в\n'
        '  // index.html), от сервера больше НЕ зависит. Роутинг в\n'
        '  // Code.gs тоже убран.\n'
        '\n')
    src = src[:i2] + NOTE2 + src[j2:]
    changed.append('блок getWeather + парсеры (%d строк)'
                   % (src[i2:j2].count('\n') - NOTE2.count('\n')))

# ---------- 3. authorizeWeather (конец файла) ----------
A3 = ('// ============================================================\n'
      '// Task 534 — РАЗОВАЯ АВТОРИЗАЦИЯ ВНЕШНИХ ЗАПРОСОВ (погода)')
i3 = src.find(A3)
if i3 != -1:
    # блок тянется до конца файла (функция — последняя); хвостовой \n
    tail = src[i3:]
    assert 'function authorizeWeather()' in tail
    assert tail.count('function ') == 1, 'после маркера чужие функции!'
    NOTE3 = (
        '// ============================================================\n'
        '// Task 536 — СЕРВЕРНАЯ ПОГОДА УДАЛЕНА (authorizeWeather,\n'
        '// getWeather, _parseMeteoinfo, _parseOpenMeteo)\n'
        '// ============================================================\n'
        '// Заявка: «Через сервер погода не загружается, работает только\n'
        '// через wttr.in (напрямую из браузера), поэтому убери из кода\n'
        '// WorkSchedule.gs не рабочие строки кода связанные с погодой».\n'
        '// Серверные запросы UrlFetchApp (meteoinfo.ru, open-meteo.com)\n'
        '// падали из-за отсутствия области script.external_request в\n'
        '// токене развёртывания. Погода в клиенте идёт напрямую из\n'
        '// браузера (open-meteo.com → wttr.in, Task 533/534) и от\n'
        '// сервера больше НЕ зависит. Функция authorizeWeather()\n'
        '// (Task 534/535 — разовая авторизация внешних запросов) больше\n'
        '// не нужна и удалена вместе с эндпоинтом workSchedule.getWeather\n'
        '// (роутинг в Code.gs убран).\n')
    src = src[:i3] + NOTE3
    changed.append('authorizeWeather + инструкция (%d строк)'
                   % (tail.count('\n') + 1))

# ---------- контроль (кодовые формы — заметки Task 536 упоминают
# имена удалённых функций текстом, это НЕ код) ----------
GONE = ['getWeather: function(payload)', '_parseMeteoinfo: function',
        '_parseOpenMeteo: function', 'function authorizeWeather() {',
        'ws_weather_kemerovo_v1',
        'meteoinfo.ru/pogoda/russia/kemerovo-area/kemerovo',
        'api.open-meteo.com/v1/forecast']
for g in GONE:
    assert g not in src, 'осталось: ' + g
KEPT = ['_getProdCal', '_LEGALIC_URL', 'getPatterns: function',
        'getStatusCodes: function', 'Task 536']
for k in KEPT:
    assert k in src, 'пропало (не должно было): ' + k

io.open(PATH, 'w', encoding='utf-8').write(src)
new_len = src.count('\n') + 1
print('WorkSchedule.gs: %d → %d строк (−%d)' % (orig_len, new_len, orig_len - new_len))
for c in changed:
    print('  − ' + c)
if not changed:
    print('  (уже выполнено — идемпотентный перезапуск)')
print('OK')
