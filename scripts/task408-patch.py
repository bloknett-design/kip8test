#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408 — заявка: «блоки инструктажи и мероприятия — РАЗНЫЕ
# информационные блоки (не объединять); в блоке Повторные инструктажи
# и периодическая проверка знаний — даты проведения + период; в
# шахматке коды И и ПЗ с указанием вида; записи "Инструктажей"
# формируются РУЧНЫМ ВЫБОРОМ из шаблонного списка; годовые архивы с
# отметкой выполнения + следующие сроки по периодичности; блок
# мероприятия (прогул/обучение/примечание) — коды в шахматке и архив».
# Ответы пользователя (5 рекомендованных): стрелки ‹год› в блоках
# карточки; тултип бейджа; select по типу; снимок срока на конец года;
# подсказка пункта в форме.
# ПРАВКИ:
#  1) GAS listTrainings + eventsAll (все «Мероприятия», без фильтра
#     года — архивы блока «Мероприятия · ‹год›»);
#  2) КЛИЕНТ: _EVENTS_ALL (кэш Task 314 запись/рестор);
#  3) ШАХМАТКА: тултип бейджа «код — тема записи» (вид И/ПЗ);
#  4) КАРТОЧКА (asBlocks): год блока = _wtabYearOf(tabNo) + стрелки
#     ‹год› (_wtabYearNav/_wtabYearShift/_wtabYearMin); записи года —
#     _wtabYearRecords (instrAll+eventsAll+_TRAININGS, дедуп по id);
#     попап ячейки — прежний год шахматки;
#  5) _renderInstrSection: параметр year; «последний» ≤ конец года;
#     архивный год — нейтральный «след. срок (на конец N)» без
#     красного «просрочено»; «— за N год не проводился»;
#  6) ФОРМА: строгий select #wsTrTitleSel по типу (инструктаж/ПЗ;
#     обучение/прогул/примечание и нет шаблона — свободный ввод),
#     подсказка #wsTrItemHint (периодичность/основание), правка
#     «вне списка» отдельным пунктом; submit — тема из select.
import io

def apply(path, edits):
    src = io.open(path, encoding='utf-8').read()
    for old, new in edits:
        if src.count(old) != 1:
            raise SystemExit('FAIL %s: фрагмент встречается %d раз:\n%r'
                             % (path, src.count(old), old[:120]))
        src = src.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('%s: %d правок' % (path, len(edits)))

# ============================================================
# 1. GAS — eventsAll
# ============================================================
GS = 'scripts/WorkSchedule.gs'
apply(GS, [
    (
"""  // workSchedule.listTrainings
  // payload: { token, year, month }  (если month не указан — все мероприятия года)
  // returns: { ok:true, data: { trainings: [...] } }
""",
"""  // workSchedule.listTrainings
  // payload: { token, year, month }  (если month не указан — все мероприятия года)
  // returns: { ok:true, data: { trainings: [...], instrList (Task 407),
  //            instrAll (Task 407), eventsAll (Task 408) } }
"""),
    (
"""    return { ok: true, data: {
      trainings: trainings,
      instrList: this._readInstrListSheet(),
      instrAll:  this._readTrainingsSheet(sheet, {})
    } };""",
"""    // Task 408 (заявка: годовые архивы мероприятий): eventsAll — ВСЕ
    // записи листа «Мероприятия» БЕЗ фильтра года (листа нет/старый
    // сервер — пустой массив; клиент мягко деградирует к годовому
    // срезу _TRAININGS года шахматки)
    return { ok: true, data: {
      trainings: trainings,
      instrList: this._readInstrListSheet(),
      instrAll:  this._readTrainingsSheet(sheet, {}),
      eventsAll: (evSheet ? this._readTrainingsSheet(evSheet, {}) : [])
    } };"""),
])

# ============================================================
# 2. index.html — состояние + кэш + шашматка + карточка + форма
# ============================================================
IDX = 'index.html'
apply(IDX, [
    # --- 2a. CSS: навигатор года + подсказка пункта формы ---
    (
"""    .ws-wcard .ws-whead-a {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-left: auto;
        flex: none;
    }
""",
"""    .ws-wcard .ws-whead-a {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-left: auto;
        flex: none;
    }
    /* Task 408: навигатор года «‹ 2026 ›» в заголовках блоков карточки
       (стрелки листают годовые архивы инструктажей/мероприятий) */
    .ws-ynav {
        display: inline-flex;
        align-items: center;
        gap: 1px;
        margin-left: 2px;
    }
    .ws-ynav-btn {
        display: inline-block;
        min-width: 17px;
        padding: 0 3px;
        cursor: pointer;
        user-select: none;
        color: var(--accent-blue, #4a8fc7);
        font-weight: 700;
        border-radius: 4px;
        line-height: 1;
    }
    .ws-ynav-btn:hover {
        background: rgba(74, 143, 199, 0.22);
    }
    .ws-ynav-btn.ws-ynav-off {
        color: #5a6b7d;
        opacity: 0.35;
        cursor: default;
    }
    .ws-ynav-btn.ws-ynav-off:hover {
        background: none;
    }
    .ws-ynav-y {
        font-weight: 700;
    }
    [data-theme="light"] .ws-ynav-btn {
        color: #2f6da3;
    }
    [data-theme="light"] .ws-ynav-btn:hover {
        background: rgba(198, 97, 63, 0.18);
    }
    [data-theme="light"] .ws-ynav-btn.ws-ynav-off {
        color: #8494a3;
    }
    /* Task 408: подсказка выбранного пункта шаблона в шторке
       «Новое мероприятие» (периодичность · основание) */
    .ws-tr-item-hint {
        margin-top: 4px;
        font-size: 12px;
        line-height: 1.35;
        color: #93a7b8;
    }
    [data-theme="light"] .ws-tr-item-hint {
        color: #6e7f90;
    }
"""),
    # --- 2b. Форма: разметка (строгий select + подсказка) ---
    (
"""            <label class="flow-input-label" for="wsTrTitle">Тема</label>
            <!-- Task 407: подсказки названий из шаблона «Список_И_и_ПЗ»
                 (datalist #wsTrTitleList) — при типе инструктаж/проверка
                 знаний, по «виду» пункта; свободный ввод остаётся
                 (внеплановые темы) -->
            <input type="text" id="wsTrTitle" class="flow-input-field-small" placeholder="Повторный инструктаж по ОТ (Q3 2026)" autocomplete="off" list="wsTrTitleList">
            <datalist id="wsTrTitleList"></datalist>
""",
"""            <label class="flow-input-label" for="wsTrTitle">Тема</label>
            <!-- Task 408 (заявка: записи «Инструктажей» формируются
                 РУЧНЫМ ВЫБОРОМ из шаблонного списка): тип
                 инструктаж/проверка знаний — СТРОГИЙ select пунктов
                 «Список_И_и_ПЗ» этого вида (свободного ввода нет;
                 внеплановые — сначала добавить в список); прочие типы
                 и ОТСУТСТВИЕ шаблона (лист не создан/сервер старый) —
                 прежний текстовый ввод #wsTrTitle (Task 407 datalist
                 остаётся как деградация) -->
            <select id="wsTrTitleSel" class="flow-input-field-small" hidden></select>
            <input type="text" id="wsTrTitle" class="flow-input-field-small" placeholder="Повторный инструктаж по ОТ (Q3 2026)" autocomplete="off" list="wsTrTitleList">
            <datalist id="wsTrTitleList"></datalist>
            <!-- Task 408: подсказка выбранного пункта — периодичность
                 и основание подтягиваются из шаблона; разовый/без
                 данных — строка скрыта -->
            <div id="wsTrItemHint" class="ws-tr-item-hint" hidden></div>
"""),
    # --- 2c. Состояние: _EVENTS_ALL + _wtabYear ---
    (
"""        _INSTR_LIST: [],
        _INSTR_ALL: [],
""",
"""        _INSTR_LIST: [],
        _INSTR_ALL: [],
        // Task 408: ВСЕ записи «Мероприятий» (listTrainings.eventsAll;
        // годовые архивы блока «Мероприятия · ‹год›»)
        _EVENTS_ALL: [],
"""),
    (
"""        _workersTab: 'general',
""",
"""        _workersTab: 'general',
        // Task 408: выбранный ГОД блоков карточки по работникам
        // (стрелки ‹год›; не выбран — год шахматки)
        _wtabYear: {},
"""),
    # --- 2d. _loadTrainings: разбор eventsAll ---
    (
"""                    self._INSTR_LIST = data.instrList || [];
                    self._INSTR_ALL = data.instrAll || [];
""",
"""                    self._INSTR_LIST = data.instrList || [];
                    self._INSTR_ALL = data.instrAll || [];
                    // Task 408: все записи «Мероприятий» (старый
                    // сервер поля не отдаёт — пустой массив)
                    self._EVENTS_ALL = data.eventsAll || [];
"""),
    # --- 2e. Кэш Task 314: рестор eventsAll ---
    (
"""            this._INSTR_LIST = Array.isArray(c.instrList) ? c.instrList : [];
            this._INSTR_ALL = Array.isArray(c.instrAll) ? c.instrAll : [];
""",
"""            this._INSTR_LIST = Array.isArray(c.instrList) ? c.instrList : [];
            this._INSTR_ALL = Array.isArray(c.instrAll) ? c.instrAll : [];
            // Task 408: все «Мероприятия» (кэш прежних версий поля не
            // содержит — пустой массив, архивная навигация деградирует
            // к году шахматки)
            this._EVENTS_ALL = Array.isArray(c.eventsAll) ? c.eventsAll : [];
"""),
    # --- 2f. Кэш Task 314: запись eventsAll ---
    (
"""                c.instrList = this._INSTR_LIST;
                c.instrAll = this._INSTR_ALL;
""",
"""                c.instrList = this._INSTR_LIST;
                c.instrAll = this._INSTR_ALL;
                // Task 408: все «Мероприятия» (не по годам)
                c.eventsAll = this._EVENTS_ALL;
"""),
    # --- 2g. Шахматка: тултип вида на бейдже ---
    (
"""                var evChips = '';
                for (var evj = 0; evj < events.length; evj++) {
                    var evMeta = this._statusMeta(events[evj].code) || {};
                    evChips += '<span class="ws-ev-badge"' +
                               (evMeta.color ? ' style="background:' + evMeta.color + ';"' : '') +
                               '>' + this._esc(events[evj].code) + '</span>';
                }
""",
"""                var evChips = '';
                for (var evj = 0; evj < events.length; evj++) {
                    var evMeta = this._statusMeta(events[evj].code) || {};
                    // Task 408 (заявка: коды И и ПЗ в шахматке — «с
                    // указанием вида инструктажа или проверки знаний»):
                    // тултип бейджа «код — тема записи» (вид); записи
                    // нет (виртуальный бейдж статуса) — полное имя
                    // кода из справочника
                    var evTr = events[evj].training;
                    var evTip = (evTr && String(evTr.тема || '').trim())
                        ? (events[evj].code + ' — ' + String(evTr.тема).trim())
                        : String((evMeta.name || '')).trim();
                    evChips += '<span class="ws-ev-badge"' +
                               (evMeta.color ? ' style="background:' + evMeta.color + ';"' : '') +
                               (evTip ? ' title="' + this._esc(evTip) + '"' : '') +
                               '>' + this._esc(events[evj].code) + '</span>';
                }
"""),
])

print('ЧАСТЬ 1 применена')
