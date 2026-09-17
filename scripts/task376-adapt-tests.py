#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 376 — адаптации СУЩЕСТВУЮЩИХ тестов под намеренно изменённое
# поведение (прецедент Task 375: «адаптации test-task364/366/358»):
#
#   1. test-task366.js — archiveVM: мок Utilities.sleep (ретраи Task 376
#      паузят между попытками; в VM-контексте нет Apps Script глобалей);
#      тест «server_busy пробрасывается» — теперь замок берётся 3 раза
#      (10 c + 4 c + 4 c) и только затем исключение уходит вызывающему.
#   2. test-task375.js — archiveVM: тот же мок Utilities (харнессы
#      идентичны; future-proof).
#   3. test-flow-period-input.js — _writePeriodEntry при сбое архива
#      возвращает СТАБИЛЬНЫЙ код 'archive_write_failed' (Task 376:
#      клиент отличает «доставим позже» от «окончательный отказ»),
#      а не человекочитаемый текст в error.
#   4. test-task358.js — дедуб 'day' во флеше теперь подтверждается по
#      АРХИВУ (meters-совпадения мало: meters пишется раньше архива):
#      в маршрут добавлен flowmeter.archive со строкой показания.

import io, sys

def patch(path, repls):
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    for old, new, tag in repls:
        if src.count(old) != 1:
            print('FAIL [%s] anchor count=%d (ожидался 1): %r' % (tag, src.count(old), old[:80]))
            sys.exit(1)
        src = src.replace(old, new)
        print('OK  [%s]' % tag)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(src)

# --- 1. test-task366.js ---
patch('tests/test-task366.js', [
    (
        """    const ctx = {
        Date: Date, Math: Math,
        parseInt: parseInt, parseFloat: parseFloat, String: String,
        Logger: { log: function (m) { (ctx.__logs = ctx.__logs || []).push(String(m)); } },
        Flowmeter: {
            _clientToDateObj: function (val) {
                if (!val) return null;
                const m = String(val).trim().match(/^(\\d{1,2})\\/(\\d{1,2})\\/(\\d{4})$/);
                return m ? new Date(+m[3], +m[1] - 1, +m[2]) : null;
            }
        },
        Utils: {
            withLock: function (fn) {
                mock.calls.withLock++;
                if (lockBehavior === 'busy') throw new Error('server_busy: попробуйте ещё раз через несколько секунд');
                return fn();
            }
        }
    };""",
        """    const ctx = {
        Date: Date, Math: Math,
        parseInt: parseInt, parseFloat: parseFloat, String: String,
        Logger: { log: function (m) { (ctx.__logs = ctx.__logs || []).push(String(m)); } },
        Utilities: { sleep: function () { /* Task 376: пауза между ретраями */ } },
        Flowmeter: {
            _clientToDateObj: function (val) {
                if (!val) return null;
                const m = String(val).trim().match(/^(\\d{1,2})\\/(\\d{1,2})\\/(\\d{4})$/);
                return m ? new Date(+m[3], +m[1] - 1, +m[2]) : null;
            }
        },
        Utils: {
            withLock: function (fn) {
                mock.calls.withLock++;
                if (lockBehavior === 'busy') throw new Error('server_busy: попробуйте ещё раз через несколько секунд');
                return fn();
            }
        }
    };""",
        '366: Utilities.sleep в archiveVM',
    ),
    (
        """    test('server_busy из withLock пробрасывается вызывающему', () => {
        const rows = [];
        const a = archiveVM(rows, { lockBehavior: 'busy' });
        let msg = '';
        try {
            a.obj.appendToArchive(2, 'Х', 1, 2, '9/8/2026', '9/9/2026', null, null, 'м³', 'Ежедневно', 'Админ', 'И', '', '', 'сутки');
        } catch (e) { msg = String(e.message); }
        assertTrue(msg.indexOf('server_busy') !== -1,
            'клиентская сторона классифицирует как повторяемую (тест выше)');
        assertEqual(rows.length, 0, 'при таймауте замка строка не потеряна молча');
    });""",
        """    test('server_busy из withLock пробрасывается вызывающему', () => {
        const rows = [];
        const a = archiveVM(rows, { lockBehavior: 'busy' });
        let msg = '';
        try {
            a.obj.appendToArchive(2, 'Х', 1, 2, '9/8/2026', '9/9/2026', null, null, 'м³', 'Ежедневно', 'Админ', 'И', '', '', 'сутки');
        } catch (e) { msg = String(e.message); }
        assertTrue(msg.indexOf('server_busy') !== -1,
            'клиентская сторона классифицирует как повторяемую (тест выше)');
        assertEqual(rows.length, 0, 'при таймауте замка строка не потеряна молча');
        // Task 376: ретраи — замок берётся 3 раза (10 c + 4 c + 4 c),
        // только после последней неудачи исключение уходит вызывающему
        assertEqual(a.mock.calls.withLock, 3,
            'три попытки перед перебросом (транзиент очереди поглощается)');
    });""",
        '366: ретраи задокументированы в тесте busy',
    ),
])

# --- 2. test-task375.js ---
patch('tests/test-task375.js', [
    (
        """    const ctx = {
        Date: Date, Math: Math,
        parseInt: parseInt, parseFloat: parseFloat, String: String,
        Logger: { log: function (m) { (ctx.__logs = ctx.__logs || []).push(String(m)); } },
        Flowmeter: {""",
        """    const ctx = {
        Date: Date, Math: Math,
        parseInt: parseInt, parseFloat: parseFloat, String: String,
        Logger: { log: function (m) { (ctx.__logs = ctx.__logs || []).push(String(m)); } },
        Utilities: { sleep: function () { /* Task 376: пауза между ретраями */ } },
        Flowmeter: {""",
        '375: Utilities.sleep в archiveVM',
    ),
])

# --- 3. test-flow-period-input.js ---
patch('tests/test-flow-period-input.js', [
    (
        """    test('Ошибка записи в архив — неуспех (архив — единственное хранилище)', () => {
        const start = FLOWMETER_GS.indexOf('_writePeriodEntry: function');
        const end = FLOWMETER_GS.indexOf('setComment: function');
        const body = FLOWMETER_GS.slice(start, end);
        assertTrue(body.indexOf("return { ok: false, error: 'Ошибка записи в архив: '") !== -1,
            'ok:false при сбое архива');
    });""",
        """    test('Ошибка записи в архив — неуспех (архив — единственное хранилище)', () => {
        const start = FLOWMETER_GS.indexOf('_writePeriodEntry: function');
        const end = FLOWMETER_GS.indexOf('setComment: function');
        const body = FLOWMETER_GS.slice(start, end);
        // Task 376: стабильный код archive_write_failed (клиент отличает
        // «доставим позже» от «окончательный отказ»), человекочитаемый
        // текст — в message
        assertTrue(body.indexOf("return { ok: false, error: 'archive_write_failed'") !== -1,
            'ok:false при сбое архива');
        assertTrue(body.indexOf('повторно автоматически') !== -1,
            'message объясняет автоматический повтор');
    });""",
        'period-input: стабильный код ошибки архива',
    ),
])

# --- 4. test-task358.js ---
patch('tests/test-task358.js', [
    (
        """    test('дедуб day: beacon дошёл в прошлый раз → повтор НЕ отправляется', async () => {
        // сервер уже содержит показание (curr=95, dateCurr 9/9/2026)
        const M = flushMixin({
            'flowmeter.list': () => Promise.resolve({
                meters: [{ id: 2, dateCurr: '9/9/2026', curr: 95 }]
            })
        });""",
        """    test('дедуб day: beacon дошёл в прошлый раз → повтор НЕ отправляется', async () => {
        // сервер уже содержит показание (curr=95, dateCurr 9/9/2026);
        // Task 376: подтверждение доставки — meters И строка архива
        // (meters-совпадения мало: meters пишется раньше архива)
        const M = flushMixin({
            'flowmeter.list': () => Promise.resolve({
                meters: [{ id: 2, dateCurr: '9/9/2026', curr: 95 }]
            }),
            'flowmeter.archive': () => Promise.resolve({
                records: [{ entryType: 'сутки', dateCurr: '9/9/2026', curr: 95 }]
            })
        });""",
        '358: дедуб day подтверждён архивом',
    ),
])

print('\nTask 376: адаптации применены.')
