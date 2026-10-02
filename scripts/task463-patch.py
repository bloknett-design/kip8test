#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 463: патч index.html + sw.js — ИНТЕРАКТИВНЫЕ отметки выполнения
# в разделе «Плановые мероприятия» + архив в новом файле
# Мероприятия_КИП_ИОС.
#
# ЗАЯВКА: «Суть раздела в том, чтобы ежемесячно отмечать выполнение
# перечисленных в таблице мероприятий, с функцией архива в новом файле
# https://docs.google.com/spreadsheets/d/1uX8... Отметки делает
# пользователь в таблице плана мероприятий путём нажатия на ячейку
# напротив мероприятия за выбранный месяц, при этом, после
# подтверждения данного действия, в ячейке вместо тусклого крестика
# появляется значок галочки зелёного цвета, и эта информация, с
# указанием наименования мероприятия и даты его выполнения,
# сохраняется в архив файла Мероприятия_КИП_ИОС.»
#
# ИЗМЕНЕНИЯ (index.html):
#   1. Шапка страницы: кнопка «Обновить» (перезагрузка отметок);
#   2. Карточка: строка-подсказка «нажмите на ячейку…»;
#   3. Таблице — id="peTable" (делегированный клик);
#   4. CSS: тусклый крест / зелёная галочка / hover / busy /
#      подсказка / кнопка обновления / input даты в диалоге;
#   5. НОВЫЙ модуль PlanEventsData (перед WorkSchedule): init при
#      открытии страницы, loadMarks (planEvents.list), клик по ячейке
#      → диалог подтверждения с датой (по умолчанию сегодня) →
#      planEvents.mark → ЗЕЛЁНАЯ галочка вместо крестика;
#   6. navigateTo: хук plan-events → PlanEventsData.init();
#   7. sw.js: kipia-test-v686 → kipia-test-v687 + комментарий.
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
SW = os.path.join(ROOT, 'sw.js')

with io.open(INDEX, encoding='utf-8') as f:
    src = f.read()
with io.open(SW, encoding='utf-8') as f:
    sw = f.read()

REPL = []

# --- 1. Шапка страницы: кнопка «Обновить» ---
REPL.append((
"""                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Плановые мероприятия</div>
            </div>""",
"""                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Плановые мероприятия</div>
                <!-- Task 463: перезагрузка отметок выполнения с сервера -->
                <button type="button" id="peRefreshBtn" class="pe-refresh-btn" onclick="PlanEventsData.refresh()" aria-label="Обновить отметки"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.65 6.35A7.95 7.95 0 0 0 12 4a8 8 0 1 0 7.73 10h-2.08A6 6 0 1 1 12 6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="currentColor"/></svg></button>
            </div>"""))

# --- 2. Подсказка над таблицей + id таблице ---
REPL.append((
"""                <div class="pe-card">
                    <div class="pe-grid-wrap">
                        <table class="pe-table">""",
"""                <div class="pe-card">
                    <!-- Task 463: подсказка интерактивности ячеек -->
                    <div class="pe-hint" id="peHint">Нажмите на ячейку месяца, чтобы отметить выполнение мероприятия — отметка с датой сохраняется в архив файла Мероприятия_КИП_ИОС</div>
                    <div class="pe-grid-wrap">
                        <table class="pe-table" id="peTable">"""))

# --- 3. CSS: отметки выполнения (якорь — .pe-m из Task 460) ---
REPL.append((
"""    /* Пустая ячейка месяца (разметка периодичности в образец
       не входит) — высота как у строки с текстом */
    .pe-m { height: 36px; }""",
"""    /* Пустая ячейка месяца (разметка периодичности в образец
       не входит) — высота как у строки с текстом */
    .pe-m { height: 36px; }
    /* ====== Task 463: отметки выполнения ======
       Клик по ячейке месяца → диалог с датой выполнения →
       ЗЕЛЁНАЯ галочка в ячейке (вместо тусклого крестика) +
       запись в архив файла Мероприятия_КИП_ИОС (лист «Архив»,
       сервер PlanEvents.gs — Apps Script). Знаки — inline SVG,
       рендерит PlanEventsData._setCell (index.html, модуль). */
    td.pe-m {
        cursor: pointer;
        text-align: center;
        -webkit-user-select: none; user-select: none;
        -webkit-tap-highlight-color: transparent;
        transition: background 0.12s;
    }
    /* Специфичность выше зебры чётных строк — hover виден
       и на подсвеченных строках */
    .pe-table td.pe-m:hover { background: rgba(74, 143, 199, 0.16); }
    td.pe-m.pe-m-busy { pointer-events: none; opacity: 0.55; }
    .pe-ic {
        width: 15px; height: 15px;
        fill: none;
        stroke-width: 2.4;
        stroke-linecap: round; stroke-linejoin: round;
        vertical-align: middle;
        display: inline-block;
    }
    /* Тусклый крестик — «ещё не выполнено» */
    .pe-ic-cross {
        stroke: var(--text-secondary, rgba(255, 255, 255, 0.45));
        opacity: 0.42;
    }
    /* Зелёная галочка — «выполнено» (дата в title ячейки) */
    .pe-m-done .pe-ic-check { stroke: #43a047; }
    [data-theme="light"] .pe-ic-cross { stroke: rgba(55, 65, 81, 0.55); }
    [data-theme="light"] .pe-m-done .pe-ic-check { stroke: #2e7d32; }
    /* Подсказка над таблицей */
    .pe-hint {
        padding: 10px 12px 0;
        font-size: 12px;
        line-height: 1.45;
        color: var(--text-secondary, rgba(255, 255, 255, 0.55));
    }
    /* Кнопка «Обновить» в шапке страницы (паттерн #flowFavBtn) */
    .pe-refresh-btn {
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        width: 36px; height: 36px;
        border: none;
        background: transparent;
        color: var(--text-secondary, rgba(255, 255, 255, 0.55));
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
        display: flex; align-items: center; justify-content: center;
        border-radius: 50%;
        transition: transform 0.12s, color 0.15s;
    }
    .pe-refresh-btn:active { transform: translateY(-50%) scale(0.88); }
    .pe-refresh-btn svg { width: 18px; height: 18px; display: block; }
    .pe-refresh-btn.pe-refreshing svg { animation: peRefreshSpin 0.9s linear infinite; }
    @keyframes peRefreshSpin { to { transform: rotate(360deg); } }
    [data-theme="light"] .pe-refresh-btn { color: #5a6a7d; }
    /* Диалог отметки: подпись и поле даты (на базе .kip-dialog) */
    .pe-dialog { max-width: 320px; }
    .pe-dialog-label {
        display: block;
        margin: 10px 0 4px;
        font-size: 12px;
        color: var(--text-secondary, rgba(255, 255, 255, 0.55));
        text-align: left;
    }
    .pe-dialog-date { width: 100%; box-sizing: border-box; }"""))

# --- 4. navigateTo: хук инициализации страницы ---
REPL.append((
"""        if (page === 'flowmeter-data') {
            setTimeout(() => { if (typeof FlowmeterData !== 'undefined') FlowmeterData.init(); }, 30);
            // Task 130: крошки и .active класс уже установлены выше (перед сменой active страницы)
        }""",
"""        // Task 463: «Плановые мероприятия» — построение знаков
        // (тусклые крестики) + загрузка отметок года с сервера
        if (page === 'plan-events') {
            setTimeout(() => { if (typeof PlanEventsData !== 'undefined') PlanEventsData.init(); }, 30);
        }
        if (page === 'flowmeter-data') {
            setTimeout(() => { if (typeof FlowmeterData !== 'undefined') FlowmeterData.init(); }, 30);
            // Task 130: крошки и .active класс уже установлены выше (перед сменой active страницы)
        }"""))

# --- 5. НОВЫЙ модуль PlanEventsData (перед WorkSchedule) ---
MODULE = """    // ============================================================
    // PlanEventsData — модуль «Плановые мероприятия»: отметки
    // выполнения (Task 463)
    // ============================================================
    // Раздел «Плановые мероприятия» (таблица-образец Task 460)
    // становится ИНТЕРАКТИВНЫМ: клик по ячейке месяца → диалог
    // подтверждения с датой выполнения (по умолчанию сегодня) →
    // в ячейке вместо тусклого крестика появляется ЗЕЛЁНАЯ галочка,
    // отметка (наименование мероприятия + дата выполнения) попадает
    // в АРХИВ файла Мероприятия_КИП_ИОС (Google Sheets, лист
    // «Архив»; создаётся одноразовым scripts/PlanEventsInit.gs).
    //
    // Сервер: scripts/PlanEvents.gs (Apps Script, ОДИН развёрнутый
    // проект на kip8 и kip8test):
    //   planEvents.list — отметки года {token, year}
    //   planEvents.mark — отметить {token, year, month, event, date}
    // Доступ — право plan.events матрицы KIP8_Access (Task 462):
    // и просмотр, и отметка — одним правом.
    //
    // Год плана фиксирован заголовком таблицы «2026 год» (Task 460);
    // наименования мероприятий читаются из DOM (один источник
    // истины — разметка таблицы), совпадение с архивом — по точной
    // строке наименования.
    // ============================================================
    var PlanEventsData = {

        // Год плана (шапка таблицы «2026 год»)
        YEAR: 2026,

        // Полные названия месяцев — для диалога подтверждения
        MONTHS: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],

        // Отметки года (planEvents.list): [{id, дата_выполнения,
        // мероприятие, год, месяц}]; null — ещё не грузились
        _marks: null,
        _byKey: {},
        _initialized: false,

        // Ключ отметки: год|месяц|наименование
        _key: function(year, month, event) {
            return year + '|' + month + '|' + event;
        },

        // Локальная дата в ISO (yyyy-mm-dd) без UTC-сдвига
        _todayIso: function() {
            var d = new Date();
            var m = d.getMonth() + 1;
            var day = d.getDate();
            return d.getFullYear() + '-' +
                   (m < 10 ? '0' : '') + m + '-' +
                   (day < 10 ? '0' : '') + day;
        },

        // 'yyyy-mm-dd' → 'dd.mm.yyyy' (русская нотация в title/тостах)
        _ruDate: function(iso) {
            var m = /^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(String(iso || ''));
            return m ? (m[3] + '.' + m[2] + '.' + m[1]) : String(iso || '');
        },

        // Индекс отметок по ключу (последняя запись главнее — при
        // дублях в листе руками)
        _rebuildIndex: function() {
            var self = this;
            this._byKey = {};
            (this._marks || []).forEach(function(mk) {
                if (!mk || !mk['мероприятие']) return;
                self._byKey[self._key(mk['год'], mk['месяц'], mk['мероприятие'])] = mk;
            });
        },

        // Открытие страницы: построение знаков + загрузка отметок.
        // Повторные вызовы (возврат на страницу) — только обновление
        // данных с сервера
        init: function() {
            var table = document.getElementById('peTable');
            if (!table) return;
            if (!this._initialized) {
                this._buildCells(table);
                var self = this;
                // Делегированный клик: один обработчик на таблицу
                table.addEventListener('click', function(e) {
                    var td = e.target && e.target.closest ?
                             e.target.closest('td.pe-m') : null;
                    if (!td) return;
                    self._cellClick(td);
                });
                this._initialized = true;
            }
            this.loadMarks(true);
        },

        // Начальный вид ячеек: тусклый крестик в каждой
        _buildCells: function(table) {
            var rows = table.querySelectorAll('tbody tr.pe-row');
            for (var i = 0; i < rows.length; i++) {
                var tds = rows[i].querySelectorAll('td.pe-m');
                for (var j = 0; j < tds.length; j++) {
                    this._setCell(tds[j], null);
                }
            }
        },

        // Ячейка: mark=null → тусклый крест; mark → зелёная галочка
        // + title с датой выполнения
        _setCell: function(td, mark) {
            if (mark) {
                td.classList.add('pe-m-done');
                td.setAttribute('title',
                    'Выполнено ' + this._ruDate(mark['дата_выполнения']));
                td.innerHTML = '<svg class="pe-ic pe-ic-check" viewBox="0 0 24 24" aria-hidden="true"><polyline points="4 12.5 10 18.5 20 6.5"/></svg>';
            } else {
                td.classList.remove('pe-m-done');
                td.removeAttribute('title');
                td.innerHTML = '<svg class="pe-ic pe-ic-cross" viewBox="0 0 24 24" aria-hidden="true"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>';
            }
        },

        // Контекст кликнутой ячейки: {месяц, мероприятие, отметка}
        _cellInfo: function(td) {
            var tr = td.closest('tr');
            if (!tr) return null;
            var name = tr.querySelector('td.pe-name');
            var tds = tr.querySelectorAll('td.pe-m');
            var month = Array.prototype.indexOf.call(tds, td) + 1;
            var event = (name && name.textContent || '').trim();
            return {
                month: month,
                event: event,
                mark: this._byKey[this._key(this.YEAR, month, event)] || null
            };
        },

        // Клик по ячейке: отмеченная → подсказка с датой; пустая →
        // диалог подтверждения → сохранение отметки на сервере
        _cellClick: function(td) {
            var info = this._cellInfo(td);
            if (!info || !info.event) return;
            if (info.mark) {
                showToast('Уже отмечено: выполнено ' +
                          this._ruDate(info.mark['дата_выполнения']));
                return;
            }
            var self = this;
            this._confirmDialog(info.event, info.month).then(function(res) {
                if (!res) return; // отмена
                self._markCell(td, info, res.date);
            });
        },

        // Диалог подтверждения отметки: наименование + месяц + дата
        // выполнения (input type=date, по умолчанию сегодня).
        // Промис: null (отмена) | {date: 'yyyy-mm-dd'}
        _confirmDialog: function(eventName, month) {
            var self = this;
            return new Promise(function(resolve) {
                var ov = _kipDialogOverlay();
                var m = self.MONTHS[month - 1] || ('Месяц ' + month);
                ov.innerHTML =
                    '<div class="kip-dialog pe-dialog">' +
                        '<div class="kip-dialog-title">Отметка выполнения</div>' +
                        '<div class="kip-dialog-msg">' +
                            eventName.replace(/</g, '&lt;') +
                            ' — ' + m + ' ' + self.YEAR + '</div>' +
                        '<label class="pe-dialog-label" for="peDialogDate">Дата выполнения</label>' +
                        '<input type="date" id="peDialogDate" class="kip-dialog-input pe-dialog-date" value="' + self._todayIso() + '">' +
                        '<div class="kip-dialog-btns">' +
                            '<button type="button" class="kip-dialog-btn kip-dialog-cancel">Отмена</button>' +
                            '<button type="button" class="kip-dialog-btn kip-dialog-ok">Отметить</button>' +
                        '</div></div>';
                var settled = false;
                var done = function(v) {
                    if (settled) return;
                    settled = true;
                    ov.classList.remove('active');
                    setTimeout(function() { ov.innerHTML = ''; }, 250);
                    resolve(v);
                };
                ov.querySelector('.kip-dialog-cancel').onclick = function() { done(null); };
                ov.querySelector('.kip-dialog-ok').onclick = function() {
                    var d = ov.querySelector('#peDialogDate').value;
                    if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(d)) {
                        showToast('Укажите дату выполнения');
                        return;
                    }
                    done({ date: d });
                };
                requestAnimationFrame(function() { ov.classList.add('active'); });
            });
        },

        // Сохранение отметки: сервер → зелёная галочка в ячейке.
        // Сетевая/серверная ошибка → тост, ячейка остаётся крестиком
        _markCell: function(td, info, date) {
            var self = this;
            var token = (typeof KipAuth !== 'undefined') ? KipAuth.getToken() : '';
            if (!token) { showToast('Нужен вход в приложение'); return; }
            td.classList.add('pe-m-busy');
            KipAuth.api('planEvents.mark', {
                token: token,
                year: this.YEAR,
                month: info.month,
                event: info.event,
                date: date
            }).then(function(data) {
                td.classList.remove('pe-m-busy');
                var mk = data && data.mark ? data.mark : null;
                if (!mk) { showToast('Сервер не вернул отметку'); return; }
                // Заменяем возможный дубль ключа (идемпотентность)
                self._marks = (self._marks || []).filter(function(x) {
                    return self._key(x['год'], x['месяц'], x['мероприятие']) !==
                           self._key(mk['год'], mk['месяц'], mk['мероприятие']);
                });
                self._marks.push(mk);
                self._rebuildIndex();
                self._setCell(td, mk);
                showToast(data && data.already ?
                          'Отметка уже была сохранена' :
                          'Выполнение отмечено');
            }).catch(function(err) {
                td.classList.remove('pe-m-busy');
                showToast('Не удалось отметить: ' +
                          (err && err.serverMessage ? err.serverMessage :
                           (err && err.message ? err.message : 'ошибка сети')));
            });
        },

        // Загрузка отметок года. silent=true (автозагрузка при
        // открытии страницы) — без тостов; кнопка «Обновить» —
        // с тостом результата
        loadMarks: function(silent) {
            var self = this;
            var token = (typeof KipAuth !== 'undefined') ? KipAuth.getToken() : '';
            if (!token) {
                this._marks = [];
                this._rebuildIndex();
                this._renderMarks();
                return;
            }
            KipAuth.api('planEvents.list', {
                token: token,
                year: this.YEAR
            }).then(function(data) {
                self._marks = (data && data.marks) ? data.marks : [];
                self._rebuildIndex();
                self._renderMarks();
                if (!silent) showToast('Отметки обновлены');
            }).catch(function(err) {
                // Старый сервер без planEvents.* (Unknown action) —
                // молча: крестики остаются, отметки просто недоступны
                // до обновления Apps Script (см. DEPLOY Task 463)
                console.warn('planEvents.list:', err && err.message);
                if (!silent) {
                    showToast('Не удалось загрузить отметки: ' +
                              (err && err.message ? err.message : 'ошибка сети'));
                }
            });
        },

        // Перерисовка всех ячеек по _byKey (галочки/крестики)
        _renderMarks: function() {
            var table = document.getElementById('peTable');
            if (!table) return;
            var rows = table.querySelectorAll('tbody tr.pe-row');
            for (var i = 0; i < rows.length; i++) {
                var name = rows[i].querySelector('td.pe-name');
                var ev = (name && name.textContent || '').trim();
                var tds = rows[i].querySelectorAll('td.pe-m');
                for (var j = 0; j < tds.length; j++) {
                    this._setCell(tds[j],
                        this._byKey[this._key(this.YEAR, j + 1, ev)] || null);
                }
            }
        },

        // Кнопка «Обновить» в шапке страницы
        refresh: function() {
            var btn = document.getElementById('peRefreshBtn');
            if (btn) btn.classList.add('pe-refreshing');
            var self = this;
            var token = (typeof KipAuth !== 'undefined') ? KipAuth.getToken() : '';
            var fin = function() {
                if (btn) btn.classList.remove('pe-refreshing');
            };
            if (!token) {
                this._marks = [];
                this._rebuildIndex();
                this._renderMarks();
                showToast('Нужен вход в приложение');
                fin();
                return;
            }
            KipAuth.api('planEvents.list', {
                token: token,
                year: this.YEAR
            }).then(function(data) {
                self._marks = (data && data.marks) ? data.marks : [];
                self._rebuildIndex();
                self._renderMarks();
                showToast('Отметки обновлены');
                fin();
            }).catch(function(err) {
                showToast('Не удалось загрузить отметки: ' +
                          (err && err.message ? err.message : 'ошибка сети'));
                fin();
            });
        }
    };

"""

REPL.append((
"""    // ============================================================
    // WorkSchedule — модуль «График работы» (Task 201)
    // ============================================================""",
MODULE + """    // ============================================================
    // WorkSchedule — модуль «График работы» (Task 201)
    // ============================================================"""))

# ============ ПРОВЕРКИ ДО ЗАПИСИ ============
errors = []
for i, (old, new) in enumerate(REPL, 1):
    n = src.count(old)
    if n != 1:
        errors.append('якорь %d найден %d раз (ожидался 1): %s...' %
                      (i, n, old.strip()[:90].replace('\n', ' | ')))
if errors:
    print('ОШИБКИ ЯКОРЕЙ:')
    for e in errors:
        print('  X ' + e)
    sys.exit(1)

for old, new in REPL:
    src = src.replace(old, new)

# ============ ПРОВЕРКИ ПОСЛЕ ПАТЧА ============
POST_MUST = [
    ('id="peRefreshBtn"', 'кнопка обновления в шапке'),
    ('onclick="PlanEventsData.refresh()"', 'onclick кнопки'),
    ('class="pe-hint" id="peHint"', 'подсказка над таблицей'),
    ('<table class="pe-table" id="peTable">', 'id таблицы'),
    ('td.pe-m.pe-m-busy { pointer-events: none;', 'CSS busy'),
    ('.pe-table td.pe-m:hover', 'CSS hover выше специфичностью'),
    ('.pe-ic-cross {', 'CSS крестика'),
    ('.pe-m-done .pe-ic-check { stroke: #43a047; }', 'CSS зелёной галочки'),
    ("'</div></div>';", 'закрывающие div диалога одним литералом'),
    ('@keyframes peRefreshSpin', 'анимация обновления'),
    ("var PlanEventsData = {", 'модуль PlanEventsData'),
    ("YEAR: 2026,", 'константа года'),
    ("planEvents.mark', {", 'вызов mark'),
    ("planEvents.list', {", 'вызов list'),
    ("_kipDialogOverlay()", 'диалог на базе kip-dialog'),
    ('type="date" id="peDialogDate"', 'поле даты в диалоге'),
    ("pe-ic-check\" viewBox=\"0 0 24 24\"", 'SVG галочки'),
    ("pe-ic-cross\" viewBox=\"0 0 24 24\"", 'SVG крестика'),
    ("if (page === 'plan-events') {", 'хук navigateTo'),
    ("Уже отмечено: выполнено ", 'тост по отмеченной ячейке'),
]
POST_ABSENT = [
    ("// Task 460: «Плановые мероприятия» —\n                         // статичная страница-таблица",
     'старый комментарий «статичная страница»'),
]

post_errors = []
for marker, why in POST_MUST:
    if marker not in src:
        post_errors.append('НЕТ маркера (%s): %s' % (why, marker[:80]))
for marker, why in POST_ABSENT:
    if marker in src:
        post_errors.append('ОСТАЛСЯ старый код (%s): %s' % (why, marker[:80].replace('\n', ' | ')))
# Хук plan-events должен идти ПЕРЕД flowmeter-data (обе строки есть)
if src.index("if (page === 'plan-events') {") > src.index("if (page === 'flowmeter-data') {"):
    post_errors.append('хук plan-events не перед flowmeter-data')
# Модуль — перед WorkSchedule
if src.index('var PlanEventsData = {') > src.index('var WorkSchedule = {'):
    post_errors.append('модуль PlanEventsData не перед WorkSchedule')
# Диалог НЕ должен содержать паттерн «'</div>' +\n{20sp}'</div>';» —
# им тест Task 269 ищет конец блока .ws-cp-cols в WorkSchedule
if "'</div>' +\n                    '</div>';" in MODULE:
    post_errors.append('диалог содержит закрывающий паттерн Task 269 (ws-cp-cols)')
# 96 ячеек месяцев (8 мероприятий × 12) остаются в разметке
n_cells = src.count('<td class="pe-m"></td>')
if n_cells != 96:
    post_errors.append('ячеек месяцев в разметке %d (ожидалось 96 — не трогать разметку строк)' % n_cells)
if post_errors:
    print('ОШИБКИ ПОСЛЕ ПАТЧА:')
    for e in post_errors:
        print('  X ' + e)
    sys.exit(1)

with io.open(INDEX, 'w', encoding='utf-8') as f:
    f.write(src)
print('index.html: %d блоков заменено, проверки пройдены' % len(REPL))

# ============ sw.js ============
SW_OLD_COMMENT = """// Task 462: «Плановые мероприятия» — ОТДЕЛЬНОЕ право plan.events
// в матрице KIP8_Access (колонку добавляет RoleMatrixTask462Init.gs);
// до появления колонки — прежнее поведение (за «Документацией ИОС»)."""
SW_NEW_COMMENT = SW_OLD_COMMENT + """
// Task 463: «Плановые мероприятия» — ИНТЕРАКТИВНЫЕ отметки
// выполнения: клик по ячейке месяца → диалог с датой → зелёная
// галочка вместо тусклого крестика; архив — лист «Архив» файла
// Мероприятия_КИП_ИОС (PlanEvents.gs + PlanEventsInit.gs)."""
assert sw.count(SW_OLD_COMMENT) == 1, 'якорь комментария Task 462 в sw.js не найден'
sw = sw.replace(SW_OLD_COMMENT, SW_NEW_COMMENT)
assert sw.count("const CACHE_VERSION = 'kipia-test-v686';") == 1, 'нет v686 в sw.js'
sw = sw.replace("const CACHE_VERSION = 'kipia-test-v686';",
                "const CACHE_VERSION = 'kipia-test-v687';")
assert sw.count("const CACHE_VERSION = 'kipia-test-v687';") == 1
assert 'kipia-test-v686' not in sw, 'v686 осталась в sw.js'
assert 'Task 463' in sw and 'Мероприятия_КИП_ИОС' in sw

with io.open(SW, 'w', encoding='utf-8') as f:
    f.write(sw)
print('sw.js: kipia-test-v686 -> kipia-test-v687 + комментарий Task 463')
