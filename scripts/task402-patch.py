#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 402 (kip8test): заявка «В разделе Табель учёта рабочего времени,
# в столбце работники, в ячейках с фамилиями работников, данные типа
# работника размести в третьей строчке снизу, не меняя при этом шрифта
# и высоты ячеек. В файле табель_КИП_ИОС я добавил новый столбец
# "группа_допуска", необходимо сделать чтобы данные из него также
# редактировались из приложения и отображались в приложении после
# данных "должность"».
#
# ДВЕ части (index.html + scripts/WorkSchedule.gs):
#   ЧАСТЬ 1 — ЯЧЕЙКА СЕТКИ (столбец работников):
#     данные ТИПА работника («смена №1» / «сменный» / «дневной») —
#     ТРЕТЬЕЙ строкой ячейки, под ФИО и должностью (прежде — суффикс
#     строки должности: «Слесарь КИПиА смена №1»). Шрифт и стили —
#     те же, что у строки должности (10px/400, line-height 12px,
#     эллипсис; заявка: «не меняя шрифта и высоты ячеек»). Высота
#     ячеек на десктопе НЕ меняется: строки задаёт растяжка _fitGrid
#     по высоте области (реальные ~12 работников → ~70px ≥ природных
#     52px трёх строк); ярусы compact/tight подстраиваются сами
#     (замер природной высоты). Пустой тип — строка не рендерится.
#     Сужение (мобайл, ws-narrow) скрывает строку типа вместе с
#     должностью и таб.№. Печатная форма НЕ меняется (_posLabel:
#     «должность смена №1» — Task 361).
#     Строка должности теперь: «должность · группа» (данные
#     «группа_допуска» — ПОСЛЕ должности, «Слесарь КИПиА · IV»).
#   ЧАСТЬ 2 — «ГРУППА ДОПУСКА» (столбец «группа_допуска» листа
#     «Сотрудники» файла табель_КИП_ИОС, добавлен пользователем):
#     • карточка работника (профиль): строка «Группа допуска» —
#       сразу ПОСЛЕ «Должности»;
#     • сводная таблица вкладки «Общая» (страница «Работники»):
#       колонка «Группа допуска» — сразу ПОСЛЕ «Должности»;
#     • шторка создания/правки работника: селект «Группа допуска»
#       рядом с «Должностью» (уникальные значения листа + стандарт
#       II/III/IV/V, «— не указана —»); submit шлёт поле
#       группа_допуска в addEmployee/updateEmployee;
#     • WorkSchedule.gs: столбец находится по ЗАГОЛОВКУ строки 1
#       («группа_допуска», позиция любая — обычно L) — listEmployees
#       отдаёт поле, updateEmployee/addEmployee пишут в столбец
#       (нет столбца — мягкая деградация: поле пустое, запись
#       пропускается). СТАРЫЙ фронтенд (кэш SW) без поля в payload
#       НЕ затирает значение в листе (guard по наличию поля).
#       ⚠ СЕРВЕРНЫЙ ШАГ (у пользователя): задеплоить обновлённый
#       WorkSchedule.gs в Apps Script проекта табель_КИП_ИОС.

import sys

IDX = 'index.html'
GS = 'scripts/WorkSchedule.gs'


def apply(path, repls):
    src = open(path, encoding='utf-8').read()
    for i, (old, new, what) in enumerate(repls, 1):
        if old not in src:
            print('FAIL [%s #%d]: якорь не найден — %s' % (path, i, what))
            sys.exit(1)
        if src.count(old) != 1:
            print('FAIL [%s #%d]: якорь не уникален (%d) — %s'
                  % (path, i, src.count(old), what))
            sys.exit(1)
        src = src.replace(old, new)
        print('  [%s #%d] OK — %s' % (path, i, what))
    open(path, 'w', encoding='utf-8').write(src)


# ============================================================
# index.html
# ============================================================
IDX_REPLS = [

# ---------- 1. CSS: строка типа .ws-emp-tip — базовые стили ----------
(
"""    /* Task 254: должность сотрудника — второй строкой под ФИО
       (например, «Слесарь КИПиА дневной» / «Слесарь КИПиА смена №1»).
       Пустая должность — строка не рендерится (JS). */
    .ws-grid tbody td.ws-emp-col .ws-emp-pos {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 10px;
        font-weight: 400;
        color: var(--text-secondary, rgba(255,255,255,0.55));
        margin-top: 1px;
        /* Task 256: целый интервал — в сумме с ФИО ровно 39px (см. выше) */
        line-height: 12px;
    }
""",
"""    /* Task 254: должность сотрудника — второй строкой под ФИО
       (например, «Слесарь КИПиА дневной» / «Слесарь КИПиА смена №1»).
       Пустая должность — строка не рендерится (JS). */
    .ws-grid tbody td.ws-emp-col .ws-emp-pos {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 10px;
        font-weight: 400;
        color: var(--text-secondary, rgba(255,255,255,0.55));
        margin-top: 1px;
        /* Task 256: целый интервал — в сумме с ФИО ровно 39px (см. выше) */
        line-height: 12px;
    }
    /* Task 402 (заявка): данные ТИПА работника — ТРЕТЬЕЙ строкой
       ячейки, под ФИО и должностью («смена №1» / «сменный» /
       «дневной»). Шрифт и стили — ТЕ ЖЕ, что у строки должности
       (заявка: «не меняя при этом шрифта и высоты ячеек»: на десктопе
       высоту строк задаёт растяжка _fitGrid — третья строка
       помещается в ту же ячейку; природная высота блока растёт
       39 → 52px, ярусы compact/tight пересчитываются сами по замеру).
       Пустой тип — строка не рендерится (JS, как у должности). */
    .ws-grid tbody td.ws-emp-col .ws-emp-tip {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 10px;
        font-weight: 400;
        color: var(--text-secondary, rgba(255,255,255,0.55));
        margin-top: 1px;
        line-height: 12px;
    }
""",
'CSS: базовый блок .ws-emp-tip (шрифт должности, третья строка)'),

# ---------- 2. CSS: сужение (мобайл) скрывает и строку типа ----------
(
"""        .ws-grid.ws-narrow td.ws-emp-col .ws-tab-no,
        .ws-grid.ws-narrow td.ws-emp-col .ws-emp-pos { display: none; }
""",
"""        .ws-grid.ws-narrow td.ws-emp-col .ws-tab-no,
        .ws-grid.ws-narrow td.ws-emp-col .ws-emp-pos,
        .ws-grid.ws-narrow td.ws-emp-col .ws-emp-tip { display: none; }
""",
'CSS: ws-narrow скрывает .ws-emp-tip вместе с должностью/таб.№'),

# ---------- 3. CSS: светлая тема — цвет как у должности ----------
(
"""    /* Task 254: светлая тема — должность под ФИО потемнее */
    [data-theme="light"] .ws-grid tbody td.ws-emp-col .ws-emp-pos {
        color: #666;
    }
""",
"""    /* Task 254: светлая тема — должность под ФИО потемнее */
    [data-theme="light"] .ws-grid tbody td.ws-emp-col .ws-emp-pos {
        color: #666;
    }
    /* Task 402: строка типа работника — тот же цвет, что должность */
    [data-theme="light"] .ws-grid tbody td.ws-emp-col .ws-emp-tip {
        color: #666;
    }
""",
'CSS: светлая тема .ws-emp-tip #666'),

# ---------- 4. CSS: компактный ярус — без отступа ----------
(
"""        .ws-grid-wrap.ws-compact .ws-grid tbody td.ws-emp-col .ws-emp-pos {
            margin-top: 0;
        }
""",
"""        .ws-grid-wrap.ws-compact .ws-grid tbody td.ws-emp-col .ws-emp-pos {
            margin-top: 0;
        }
        /* Task 402: строка типа — без отступа, как должность */
        .ws-grid-wrap.ws-compact .ws-grid tbody td.ws-emp-col .ws-emp-tip {
            margin-top: 0;
        }
""",
'CSS: compact .ws-emp-tip margin-top 0'),

# ---------- 5. CSS: сжатый ярус — 9px/10px как должность ----------
(
"""        .ws-grid-wrap.ws-tight .ws-grid tbody td.ws-emp-col .ws-emp-pos {
            font-size: 9px;
            line-height: 10px;
            margin-top: 0;
        }
""",
"""        .ws-grid-wrap.ws-tight .ws-grid tbody td.ws-emp-col .ws-emp-pos {
            font-size: 9px;
            line-height: 10px;
            margin-top: 0;
        }
        /* Task 402: строка типа — как должность в сжатом ярусе */
        .ws-grid-wrap.ws-tight .ws-grid tbody td.ws-emp-col .ws-emp-tip {
            font-size: 9px;
            line-height: 10px;
            margin-top: 0;
        }
""",
'CSS: tight .ws-emp-tip 9px/10px'),

# ---------- 6. Рендер ячейки: должность·группа + третья строка типа ----------
(
"""                // Task 254 + Task 255: под ФИО — строка с должностью и
                // режимом занятости из справочника сотрудников (таблица
                // «Сотрудники» файла табель_КИП_ИОС: столбец C — тип,
                // столбец D — номер смены): «Слесарь КИПиА смена №1»,
                // «Слесарь КИПиА дневной» (см. _posLabel). Пустая
                // подпись — строка не рендерится вовсе (без пустых
                // строк в колонке). ФИО и подпись — отдельные блоки с
                // собственным эллипсисом (десктоп: колонка — по
                // самому широкому тексту, Task 325, --ws-emp-w).
                var empPosLabel = this._posLabel(emp);
                var empPos = empPosLabel
                    ? '<div class="ws-emp-pos">' + this._esc(empPosLabel) + '</div>'
                    : '';
""",
"""                // Task 254 + Task 255 + Task 402: под ФИО — строка с
                // должностью и группой допуска (столбец «группа_допуска»
                // листа «Сотрудники», данные ПОСЛЕ должности: «Слесарь
                // КИПиА · IV»), ТРЕТЬЕЙ строкой — данные типа работника
                // (таблица «Сотрудники» файла табель_КИП_ИОС: столбец C
                // — тип, столбец D — номер смены): «смена №1», «дневной»
                // (см. _empPosLine/_empTipLine; прежний склеенный формат
                // «Слесарь КИПиА смена №1» остаётся в печатной форме —
                // _posLabel, Task 361). Пустая строка — блок не
                // рендерится вовсе (без пустых строк в колонке).
                // ФИО/должность/тип — отдельные блоки с собственным
                // эллипсисом (десктоп: колонка — по самому широкому
                // тексту, Task 325, --ws-emp-w).
                var empPosLabel = this._empPosLine(emp);
                var empPos = empPosLabel
                    ? '<div class="ws-emp-pos">' + this._esc(empPosLabel) + '</div>'
                    : '';
                var empTipLabel = this._empTipLine(emp);
                var empTip = empTipLabel
                    ? '<div class="ws-emp-tip">' + this._esc(empTipLabel) + '</div>'
                    : '';
""",
'Рендер ячейки: _empPosLine (должность·группа) + _empTipLine (тип)'),

# ---------- 7. Рендер ячейки: td получает строку типа ----------
(
"""'</span></div>' + empPos + '</td>';""",
"""'</span></div>' + empPos + empTip + '</td>';""",
'Рендер ячейки: empTip в td (третья строка)'),

# ---------- 8. Замер колонки: учитывать и строку типа ----------
(
"""                var w = measure(cells[i].querySelector('.ws-emp-name'));
                var pos = cells[i].querySelector('.ws-emp-pos');
                var pw = measure(pos);
                if (pw > w) w = pw;
                if (w > max) max = w;
""",
"""                var w = measure(cells[i].querySelector('.ws-emp-name'));
                var pos = cells[i].querySelector('.ws-emp-pos');
                var pw = measure(pos);
                if (pw > w) w = pw;
                // Task 402: строка типа — тоже в замере (колонка по
                // самому широкому тексту из ТРЁХ строк)
                var tip = cells[i].querySelector('.ws-emp-tip');
                var tw = measure(tip);
                if (tw > w) w = tw;
                if (w > max) max = w;
""",
'_measureEmpCol: замер .ws-emp-tip'),

# ---------- 9. Хелперы _empPosLine/_empTipLine (перед _posLabel) ----------
(
"""        // Task 255: подпись должности с режимом занятости — данные из
        // таблицы «Сотрудники» файла табель_КИП_ИОС (тот же справочник
        // в Google-таблице, метод listEmployees): столбец C — тип
        // (сменный/дневной), столбец D — номер смены (1..5, только у
        // сменного). Примеры формирования: «Слесарь КИПиА смена №1»
        // (сменный, смена 1), «Слесарь КИПиА дневной» (дневной).
        // Сменный без номера смены — «… сменный»; без типа — только
        // должность; пусто и там и там — '' (строка не рендерится).
        _posLabel: function(emp) {
""",
"""        // Task 402 (заявка): строка ДОЛЖНОСТИ ячейки сетки — должность
        // + группа допуска через «·» (столбец «группа_допуска» листа
        // «Сотрудники»: «Слесарь КИПиА · IV»). Без группы — только
        // должность; без должности — только группа; пусто — ''
        // (строка не рендерится). Тип работника сюда БОЛЬШЕ не входит
        // — он переехал на собственную ТРЕТЬЮ строку ячейки
        // (_empTipLine); склеенный формат «должность + тип» остаётся
        // в печатной форме (_posLabel, Task 361).
        _empPosLine: function(emp) {
            var pos = String(emp['должность'] || '').trim();
            var grp = String(emp['группа_допуска'] || '').trim();
            if (!pos) return grp;
            if (!grp) return pos;
            return pos + ' · ' + grp;
        },

        // Task 402 (заявка): данные типа работника — ТРЕТЬЯ строка
        // ячейки сетки, под ФИО и должностью. Данные таблицы
        // «Сотрудники» файла табель_КИП_ИОС: столбец C — тип
        // (сменный/дневной), столбец D — номер смены (1..5, только у
        // сменного): «смена №1», «сменный» (сменный без номера),
        // «дневной». Без типа — '' (строка не рендерится).
        _empTipLine: function(emp) {
            var tip = String(emp['тип'] || '').trim();
            if (tip === 'сменный') {
                var smena = parseInt(emp['смена'], 10);
                return (smena >= 1 && smena <= 5) ? 'смена №' + smena : 'сменный';
            }
            if (tip === 'дневной') return 'дневной';
            return '';
        },

        // Task 255: подпись должности с режимом занятости — данные из
        // таблицы «Сотрудники» файла табель_КИП_ИОС (тот же справочник
        // в Google-таблице, метод listEmployees): столбец C — тип
        // (сменный/дневной), столбец D — номер смены (1..5, только у
        // сменного). Примеры формирования: «Слесарь КИПиА смена №1»
        // (сменный, смена 1), «Слесарь КИПиА дневной» (дневной).
        // Сменный без номера смены — «… сменный»; без типа — только
        // должность; пусто и там и там — '' (строка не рендерится).
        // Task 402: используется ПЕЧАТНОЙ формой (_buildPrintHtml,
        // Task 361) — шахматка перешла на _empPosLine/_empTipLine.
        _posLabel: function(emp) {
""",
'Хелперы _empPosLine/_empTipLine (сетка) перед _posLabel (печать)'),

# ---------- 10. Карточка: «Группа допуска» после «Должности» ----------
(
"""            var fields = [
                ['Режим работы', tipVal],
                ['Должность', String(emp['должность'] || '').trim() || '—'],
                ['Дата приёма', emp['дата_приёма'] ? this._fmtDateRu(emp['дата_приёма']) : '—'],
                ['Комментарий', String(emp['комментарий'] || '').trim()]
            ];
""",
"""            var fields = [
                ['Режим работы', tipVal],
                ['Должность', String(emp['должность'] || '').trim() || '—'],
                // Task 402 (заявка): «группа_допуска» — строкой ПОСЛЕ
                // «Должности» (столбец листа «Сотрудники»; пусто — «—»,
                // редактируется в шторке «Правка данных…»)
                ['Группа допуска', String(emp['группа_допуска'] || '').trim() || '—'],
                ['Дата приёма', emp['дата_приёма'] ? this._fmtDateRu(emp['дата_приёма']) : '—'],
                ['Комментарий', String(emp['комментарий'] || '').trim()]
            ];
""",
'Карточка: строка «Группа допуска» после «Должности»'),

# ---------- 11. Сводная «Общая»: колонка после «Должности» (шапка) ----------
(
"""            html += '<table class="ws-wgen-table"><thead><tr>' +
                    '<th>Таб. №</th><th>ФИО</th><th>Режим работы</th>' +
                    '<th>Должность</th><th>Дата приёма</th>' +
                    '<th>Отпуск · ' + this._year + '</th>' +
                    '<th>Мероприятия · ' + this._year + '</th>' +
                    '</tr></thead><tbody>';
""",
"""            html += '<table class="ws-wgen-table"><thead><tr>' +
                    '<th>Таб. №</th><th>ФИО</th><th>Режим работы</th>' +
                    '<th>Должность</th><th>Группа допуска</th>' +
                    '<th>Дата приёма</th>' +
                    '<th>Отпуск · ' + this._year + '</th>' +
                    '<th>Мероприятия · ' + this._year + '</th>' +
                    '</tr></thead><tbody>';
""",
'Сводная «Общая»: th «Группа допуска» после «Должности»'),

# ---------- 12. Сводная «Общая»: ячейки строк ----------
(
"""                html += '<tr><td>' + this._esc(emp['таб_номер']) + '</td>' +
                        '<td class="ws-wgen-fio">' + this._esc(emp['ФИО']) + '</td>' +
                        '<td>' + this._esc(tipVal) + '</td>' +
                        '<td>' + this._esc(String(emp['должность'] || '').trim() || '—') + '</td>' +
                        '<td>' + (emp['дата_приёма'] ? this._fmtDateRu(emp['дата_приёма']) : '—') + '</td>' +
""",
"""                html += '<tr><td>' + this._esc(emp['таб_номер']) + '</td>' +
                        '<td class="ws-wgen-fio">' + this._esc(emp['ФИО']) + '</td>' +
                        '<td>' + this._esc(tipVal) + '</td>' +
                        '<td>' + this._esc(String(emp['должность'] || '').trim() || '—') + '</td>' +
                        '<td>' + this._esc(String(emp['группа_допуска'] || '').trim() || '—') + '</td>' +
                        '<td>' + (emp['дата_приёма'] ? this._fmtDateRu(emp['дата_приёма']) : '—') + '</td>' +
""",
'Сводная «Общая»: td «группа_допуска» после «Должности»'),

# ---------- 13. Шторка работника: селект «Группа допуска» ----------
(
"""    <div class="flow-input-row">
        <div class="flow-input-group" style="flex:0 0 60%;">
            <!-- Task 318: «Должность» — ВЫПАДАЮЩИЙ список вариантов из
                 таблицы «Сотрудники» (файл табель_КИП_ИОС): уникальные
                 должности строк листа (активные + архив), по алфавиту.
                 Наполняется при открытии шторки — _fillPositionSelect
                 (listEmployees includeArchived, офлайн/сбой — активные
                 из _EMPLOYEES); лист — единственный источник истины -->
            <label class="flow-input-label" for="wsEmpPosition">Должность</label>
            <select id="wsEmpPosition" class="flow-input-field-small"></select>
        </div>
    </div>
""",
"""    <div class="flow-input-row">
        <div class="flow-input-group" style="flex:0 0 60%;">
            <!-- Task 318: «Должность» — ВЫПАДАЮЩИЙ список вариантов из
                 таблицы «Сотрудники» (файл табель_КИП_ИОС): уникальные
                 должности строк листа (активные + архив), по алфавиту.
                 Наполняется при открытии шторки — _fillPositionSelect
                 (listEmployees includeArchived, офлайн/сбой — активные
                 из _EMPLOYEES); лист — единственный источник истины -->
            <label class="flow-input-label" for="wsEmpPosition">Должность</label>
            <select id="wsEmpPosition" class="flow-input-field-small"></select>
        </div>
        <div class="flow-input-group" style="flex:0 0 40%;">
            <!-- Task 402: «Группа допуска» — столбец «группа_допуска»
                 листа «Сотрудники» (табель_КИП_ИОС), ПОСЛЕ «Должности».
                 ВЫПАДАЮЩИЙ список: уникальные значения листа +
                 стандарт II/III/IV/V + «— не указана —»; наполняется
                 при открытии шторки — _fillGroupSelect (как «Должность»
                 Task 318; текущее значение сохраняется поверх) -->
            <label class="flow-input-label" for="wsEmpAccessGroup">Группа допуска</label>
            <select id="wsEmpAccessGroup" class="flow-input-field-small"></select>
        </div>
    </div>
""",
'Шторка работника: селект wsEmpAccessGroup рядом с «Должностью»'),

# ---------- 14. Создание работника: сброс «Группы допуска» ----------
(
"""            this._fillPositionSelect();
            document.getElementById('wsEmpComment').value = '';
""",
"""            this._fillPositionSelect();
            // Task 402: сброс «Группы допуска» при создании
            this._fillGroupSelect('');
            document.getElementById('wsEmpComment').value = '';
""",
'openEmployeeForm: сброс «Группы допуска» (создание)'),

# ---------- 15. Правка работника: префилл «Группы допуска» ----------
(
"""            this._fillPositionSelect();
            document.getElementById('wsEmpComment').value = String(emp['комментарий'] || '');
            this.onEmpTypeChange();
""",
"""            this._fillPositionSelect();
            // Task 402: префилл «Группы допуска» правкой (временная
            // опция значения — асинхронный _fillGroupSelect сохранит
            // выбор, как у «Должности» Task 318)
            this._fillGroupSelect(String(emp['группа_допуска'] || '').trim());
            document.getElementById('wsEmpComment').value = String(emp['комментарий'] || '');
            this.onEmpTypeChange();
""",
'openEmpEditForm: префилл «Группы допуска» (правка)'),

# ---------- 16. Наполнение селекта: _fillGroupSelect/_fillGroupOptions ----------
(
"""            var keep = sel.value;
            sel.innerHTML = html;
            if (keep) sel.value = keep;
        },
""",
"""            var keep = sel.value;
            sel.innerHTML = html;
            if (keep) sel.value = keep;
        },

        // Task 402: «Группа допуска» — наполнение селекта шторки
        // работника: уникальные значения столбца «группа_допуска»
        // листа «Сотрудники» (listEmployees includeArchived) +
        // стандартные группы II/III/IV/V (всегда в списке — новые
        // значения выбираются и без существующих строк листа) +
        // «— не указана —» (пусто). keep — текущее значение шторки:
        // временная опция до подгрузки, как у «Должности» (Task 318).
        _fillGroupSelect: function(keep) {
            var self = this;
            var sel = document.getElementById('wsEmpAccessGroup');
            if (!sel) return;
            this._api('workSchedule.listEmployees', { includeArchived: true })
                .then(function(data) {
                    self._fillGroupOptions(sel, data.employees || [], keep);
                })
                .catch(function() {
                    self._fillGroupOptions(sel, self._EMPLOYEES || [], keep);
                });
        },

        _fillGroupOptions: function(sel, employees, keep) {
            var seen = {};
            var list = [];
            // стандартные группы — всегда в списке (электробезопасность)
            var std = ['II', 'III', 'IV', 'V'];
            for (var s = 0; s < std.length; s++) {
                if (!seen[std[s]]) { seen[std[s]] = true; list.push(std[s]); }
            }
            for (var i = 0; i < (employees || []).length; i++) {
                var g = String(employees[i]['группа_допуска'] || '').trim();
                if (g && !seen[g]) { seen[g] = true; list.push(g); }
            }
            // значение шторки (правка) — даже если его нет в листе
            if (keep && !seen[keep]) { seen[keep] = true; list.push(keep); }
            list.sort(function(a, b) { return a.localeCompare(b, 'ru'); });
            var html = '<option value="">— не указана —</option>';
            for (var j = 0; j < list.length; j++) {
                html += '<option value="' + this._escAttr(list[j]) + '">' +
                        this._esc(list[j]) + '</option>';
            }
            sel.innerHTML = html;
            if (keep) sel.value = keep;
        },
""",
'_fillGroupSelect/_fillGroupOptions (уникальные + II–V + keep)'),

# ---------- 17. submit: чтение поля + payload updateEmployee ----------
(
"""            var position = document.getElementById('wsEmpPosition').value.trim();
            var comment = document.getElementById('wsEmpComment').value.slice(0, 500);
""",
"""            var position = document.getElementById('wsEmpPosition').value.trim();
            // Task 402: группа допуска — селект шторки (пусто =
            // «не указана», в лист пишется пустая строка); селекта
            // нет (старые VM-моки) — пусто
            var grpSel = document.getElementById('wsEmpAccessGroup');
            var accessGroup = grpSel ? String(grpSel.value || '').trim() : '';
            var comment = document.getElementById('wsEmpComment').value.slice(0, 500);
""",
'submitEmployeeForm: чтение accessGroup'),

# ---------- 18. payload updateEmployee: поле группа_допуска ----------
(
"""                this._api('workSchedule.updateEmployee', {
                    'таб_номер': editTab, 'ФИО': fio, тип: type,
                    смена: shift || null,
                    шаблон_ротации: patId ? parseInt(patId, 10) : null,
                    старт_цикла: startCycle,
                    дата_приёма: hireDate || null,
                    должность: position,
                    комментарий: comment
                }).then(function() {
""",
"""                this._api('workSchedule.updateEmployee', {
                    'таб_номер': editTab, 'ФИО': fio, тип: type,
                    смена: shift || null,
                    шаблон_ротации: patId ? parseInt(patId, 10) : null,
                    старт_цикла: startCycle,
                    дата_приёма: hireDate || null,
                    должность: position,
                    'группа_допуска': accessGroup,
                    комментарий: comment
                }).then(function() {
""",
'payload updateEmployee: группа_допуска'),

# ---------- 19. payload addEmployee: поле группа_допуска ----------
(
"""            this._api('workSchedule.addEmployee', {
                'таб_номер': tabNo, 'ФИО': fio, тип: type,
                смена: shift || null,
                шаблон_ротации: patId ? parseInt(patId, 10) : null,
                старт_цикла: startCycle,
                дата_приёма: hireDate || null,
                должность: position,
                комментарий: comment
""",
"""            this._api('workSchedule.addEmployee', {
                'таб_номер': tabNo, 'ФИО': fio, тип: type,
                смена: shift || null,
                шаблон_ротации: patId ? parseInt(patId, 10) : null,
                старт_цикла: startCycle,
                дата_приёма: hireDate || null,
                должность: position,
                'группа_допуска': accessGroup,
                комментарий: comment
""",
'payload addEmployee: группа_допуска'),
]

# ============================================================
# scripts/WorkSchedule.gs
# ============================================================
GS_REPLS = [

# ---------- G1. Докблок структуры листа: новый столбец ----------
(
"""//   I: в_архиве           — 0/1
//   J: должность
//   K: комментарий
//
""",
"""//   I: в_архиве           — 0/1
//   J: должность
//   K: комментарий
//   группа_допуска (Task 402) — ПОЗИЦИЯ ЛЮБАЯ: столбец добавлен
//     пользователем в файл табель_КИП_ИОС (обычно L, за «комментарием»);
//     находится по ЗАГОЛОВКУ строки 1 («группа_допуска» / «группа
//     допуска», без учёта регистра — _accessGroupColIndex). Нет
//     столбца — listEmployees отдаёт пустое поле, запись в
//     updateEmployee/addEmployee пропускается (обратная совместимость)
//
""",
'GS докблок: столбец группа_допуска (позиция любая)'),

# ---------- G2. Хелпер _accessGroupColIndex ----------
(
"""  // workSchedule.listEmployees
  // payload: { token, includeArchived }
  // returns: { ok:true, data: { employees: [...] } }
  listEmployees: function(payload) {
""",
"""  // Task 402: индекс столбца «группа_допуска» листа «Сотрудники» —
  // по ЗАГОЛОВКУ строки 1 (столбец добавлен пользователем в файл
  // табель_КИП_ИОС; позиция может быть любой — обычно L). Сравнение
  // толерантно к регистру, пробелам вокруг и пробелу/подчёркиванию
  // внутри: «группа_допуска» / «группа допуска» / «Группа допуска».
  // Столбца нет (меньше 12 колонок или заголовок не найден) — null:
  // мягкая деградация до канона A..K.
  _accessGroupColIndex: function(sheet) {
    try {
      var lastCol = sheet.getLastColumn();
      if (!lastCol || lastCol < 12) return null;
      var heads = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
      for (var c = 0; c < heads.length; c++) {
        var h = String(heads[c] || '').trim().toLowerCase()
                  .replace(/\\s+/g, ' ');
        if (h === 'группа_допуска' || h === 'группа допуска') return c;
      }
    } catch (e) { /* ignore */ }
    return null;
  },

  // workSchedule.listEmployees
  // payload: { token, includeArchived }
  // returns: { ok:true, data: { employees: [...] } }
  listEmployees: function(payload) {
""",
'GS хелпер _accessGroupColIndex (поиск по заголовку)'),

# ---------- G3. listEmployees: расширенное чтение ----------
(
"""    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { employees: [] } };

    var values = sheet.getRange(2, 1, lastRow - 1, 11).getValues();
    var includeArchived = !!payload.includeArchived;
""",
"""    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: { employees: [] } };

    // Task 402: столбец «группа_допуска» — по заголовку строки 1
    // (позиция любая); чтение расширено до найденного столбца
    var groupCol = this._accessGroupColIndex(sheet);
    var values = sheet.getRange(2, 1, lastRow - 1,
        (groupCol !== null && groupCol + 1 > 11) ? groupCol + 1 : 11)
        .getValues();
    var includeArchived = !!payload.includeArchived;
""",
'GS listEmployees: чтение до столбца группа_допуска'),

# ---------- G4. listEmployees: поле в объекте ----------
(
"""        должность:       String(r[9] || '').trim(),
        комментарий:     String(r[10] || '').trim()
      });
""",
"""        должность:       String(r[9] || '').trim(),
        // Task 402: группа допуска — из столбца по заголовку
        // «группа_допуска» (нет столбца — пусто)
        группа_допуска:  (groupCol !== null)
                           ? String(r[groupCol] || '').trim() : '',
        комментарий:     String(r[10] || '').trim()
      });
""",
'GS listEmployees: поле группа_допуска в ответе'),

# ---------- G5. addEmployee: докблок payload ----------
(
"""  // workSchedule.addEmployee
  // payload: { token, таб_номер, ФИО, тип, смена, шаблон_ротации,
  //            старт_цикла(ISO), дата_приёма(ISO), должность, комментарий }
""",
"""  // workSchedule.addEmployee
  // payload: { token, таб_номер, ФИО, тип, смена, шаблон_ротации,
  //            старт_цикла(ISO), дата_приёма(ISO), должность,
  //            группа_допуска, комментарий }
""",
'GS addEmployee: докблок payload + группа_допуска'),

# ---------- G6. addEmployee: группа в новой строке ----------
(
"""    // Task 304: A (таб_номер) — текст: «0871» не должен стать числом 871
    this._appendRowKeepText(sheet, [
      tabNo, fio, tip, smena || null, patId || null,
      startCycle, hireDate, null,  // H=дата_увольнения — пусто
      0,  // в_архиве=0
      position, comment
    ], [1]);
""",
"""    // Task 304: A (таб_номер) — текст: «0871» не должен стать числом 871
    // Task 402: группа допуска — в столбец по заголовку строки 1
    // («группа_допуска», позиция любая; нет столбца — A..K как прежде)
    var groupCol = this._accessGroupColIndex(sheet);
    var rowVals = [
      tabNo, fio, tip, smena || null, patId || null,
      startCycle, hireDate, null,  // H=дата_увольнения — пусто
      0,  // в_архиве=0
      position, comment
    ];
    if (groupCol !== null) {
      var accessGroup = (payload.группа_допуска !== undefined
                         && payload.группа_допуска !== null)
        ? String(payload.группа_допуска).trim().slice(0, 50) : '';
      while (rowVals.length <= groupCol) rowVals.push('');
      rowVals[groupCol] = accessGroup;
    }
    this._appendRowKeepText(sheet, rowVals, [1]);
""",
'GS addEmployee: группа в новой строке листа'),

# ---------- G7. updateEmployee: докблок payload ----------
(
"""  // workSchedule.updateEmployee (Task 384)
  // payload: { token, таб_номер, ФИО, тип, смена, шаблон_ротации,
  //            старт_цикла(ISO), дата_приёма(ISO), должность, комментарий }
""",
"""  // workSchedule.updateEmployee (Task 384)
  // payload: { token, таб_номер, ФИО, тип, смена, шаблон_ротации,
  //            старт_цикла(ISO), дата_приёма(ISO), должность,
  //            группа_допуска, комментарий }
""",
'GS updateEmployee: докблок payload + группа_допуска'),

# ---------- G8. updateEmployee: запись группы ----------
(
"""      // J..K: должность, комментарий (A/H/I не трогаются)
      sheet.getRange(row, 10, 1, 2).setValues([[ position, comment ]]);
""",
"""      // J..K: должность, комментарий (A/H/I не трогаются)
      sheet.getRange(row, 10, 1, 2).setValues([[ position, comment ]]);
      // Task 402: группа допуска — в столбец по заголовку строки 1
      // («группа_допуска», позиция любая; нет столбца — пропуск).
      // Пишем ТОЛЬКО когда поле пришло в payload: старый фронтенд
      // (кэш SW) без поля НЕ затирает существующее значение листа
      var groupCol = this._accessGroupColIndex(sheet);
      if (groupCol !== null && payload.группа_допуска !== undefined
              && payload.группа_допуска !== null) {
        var accessGroup = String(payload.группа_допуска).trim().slice(0, 50);
        sheet.getRange(row, groupCol + 1).setValue(accessGroup);
      }
""",
'GS updateEmployee: запись группы (guard по payload)'),
]

apply(IDX, IDX_REPLS)
apply(GS, GS_REPLS)
print('OK: index.html %d правок, WorkSchedule.gs %d правок'
      % (len(IDX_REPLS), len(GS_REPLS)))
