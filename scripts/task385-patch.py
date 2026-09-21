#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 385 — заявка пользователя (3 части):
#   1) «В баре с кнопками добавь кнопку, при нажатии на которую
#      справа будет выезжать окно с подробным описанием всех
#      сокращений в шахматке табеля, по такому же принципу, как это
#      реализовано с окном итогов учёта» → кнопка «Легенда» (ряд 2),
#      шторка #wsLegendDrawer (десктоп — margin-right-анимация как у
#      итогов; мобайл — fixed-оверлей), контент — коды дней Т-12/Т-13
#      из справочника «Коды_статусов» с живыми цветами, коды
#      мероприятий, обозначения вёрстки; взаимоисключающая с итогами;
#   2) «В разделе Табель учёта рабочего времени, переименуй все
#      упоминания слова сотрудник на слово работник (в том числе в
#      разных склонениях)» — видимые строки UI (шапки сетки/итогов,
#      шторки, тосты, подтверждения, печать, подсказки вида);
#      идентификаторы (ws-emp-*) и серверные контракты (лист
#      «Сотрудники», payload) НЕ тронуты;
#   3) «У пользователей, у которых есть доступ к редактированию
#      данных в табеле, при открытии информации о сотруднике, в окне
#      с информацией убери все кнопки связанные с редактированием и
#      внесением данных, а вместо них, в баре с кнопками, добавь
#      кнопку для перехода на страницу с полными карточками
#      работников, где будет возможность внесения и редактирования
#      данных по каждому работнику, и в том числе добавление
#      мероприятий» → карточка шахматки read-only для ВСЕХ уровней;
#      кнопка «Работники» в ряду 1 (редакторам) + заголовок «Работник +»
#      шапки сетки → новая страница #page-ws-workers с полными
#      карточками (профиль/отпуска/мероприятия: правка, ✎/✕, +,
#      «Уволить…»); «+ Работник» в шапке страницы (шторка создания).
#
# SW-бамп отдельным скриптом: task385-bump-sw.py (v612 → v613).

import sys

INDEX = 'index.html'


def patch(path, repls):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: применено правок: %d' % (path, len(repls)))


repls = []
R = repls.append

# ============================================================
# 1. CSS: шторка «Легенда» + страница «Работники» (вставка между
#    мобильным блоком .ws-tt-drawer и Task 334-блоком)
# ============================================================
R(('CSS: легенда + страница работников', '''        #page-work-schedule.ws-tt-open .ws-tt-drawer { transform: none; }
    }

    /* ============================================================
       Task 334 (заявка: МОБИЛЬНАЯ ВЕРСИЯ ТАБЕЛЬНОГО УЧЁТА):
''', '''        #page-work-schedule.ws-tt-open .ws-tt-drawer { transform: none; }
    }

    /* ============================================================
       Task 385 (заявка, часть 1): ШТОРКА «ЛЕГЕНДА» — окно с
       подробным описанием всех сокращений шахматки табеля, по
       принципу окна итогов учёта: кнопка-переключатель «Легенда»
       в ряду 2 тулбара; ДЕСКТОП — панель выезжает СПРАВА
       (margin-right 0.28s, сетка сжимается, дни прокручиваются
       под ней), МОБАЙЛ — fixed-оверлей ~86vw со скруглением и
       тенью (как итоги, Task 334). Контент — коды дней Т-12/Т-13
       и коды мероприятий из справочника «Коды_статусов» (живые
       цвета ячеек) + обозначения вёрстки. Взаимоисключающая с
       «Итогами учёта» (открытие закрывает другую шторку) */
    .ws-legend-drawer {
        flex: none;
        position: relative;
        width: 0;             /* до первого открытия (панель скрыта) */
        max-width: 45%;
        overflow: hidden;
        display: flex;
        transition: margin-right 0.28s ease;
    }
    .ws-legend-inner {
        width: min(400px, 45vw);  /* фикс-ширина: маржу мерит JS */
        display: flex;
        flex-direction: column;
        min-height: 0;
        background: var(--bg-tertiary, #0e1621);
    }
    [data-theme="light"] .ws-legend-inner {
        background: var(--bg-tertiary, #e9e7de);
    }
    /* левый бортик — стальной bevel, как .ws-tt-edge итогов */
    .ws-lg-edge {
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 2px;
        background: linear-gradient(180deg, #5c718c, #2c3a4c);
        z-index: 2;
    }
    [data-theme="light"] .ws-lg-edge {
        background: linear-gradient(180deg, #b7c3d1, #8fa0b4);
    }
    .ws-lg-head {
        padding: 12px 14px 10px 18px;
        font-size: 13px;
        font-weight: 700;
        flex: none;
    }
    .ws-lg-body {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
        overscroll-behavior: contain;
        scrollbar-width: none;
        -ms-overflow-style: none;
        padding: 0 12px 16px 16px;
    }
    .ws-lg-body::-webkit-scrollbar { width: 0; height: 0; display: none; }
    .ws-lg-sec {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        opacity: 0.72;
        margin: 16px 2px 6px;
    }
    .ws-lg-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 6px;
        border-radius: 6px;
    }
    .ws-lg-item:nth-child(even) { background: rgba(255,255,255,0.05); }
    [data-theme="light"] .ws-lg-item:nth-child(even) { background: rgba(0,0,0,0.05); }
    .ws-lg-swatch {
        width: 15px; height: 15px;
        border-radius: 4px;
        border: 1px solid rgba(0,0,0,0.3);
        flex: none;
    }
    .ws-lg-code { font-weight: 700; min-width: 36px; flex: none; }
    .ws-lg-name { font-size: 12.5px; line-height: 1.35; }
    .ws-lg-note {
        font-size: 12px;
        line-height: 1.5;
        padding: 5px 6px;
        opacity: 0.92;
    }
    @media (max-width: 1023px) {
        .ws-legend-drawer {
            position: fixed;
            top: 10vh;
            height: 74vh;
            width: min(86vw, 560px);
            right: 0;
            z-index: 75;
            display: flex;
            transform: translateX(100%);
            transition: transform 0.28s ease;
            border-radius: 10px 0 0 10px;
            box-shadow: -10px 0 26px rgba(0, 0, 0, 0.38);
            overflow: hidden;
        }
        .ws-legend-inner {
            width: 100%;
            border-radius: 10px 0 0 10px;
        }
        #page-work-schedule.ws-legend-open .ws-legend-drawer { transform: none; }
    }

    /* ============================================================
       Task 385 (заявка, часть 3): СТРАНИЦА «РАБОТНИКИ» — полные
       карточки (внесение/редактирование профиля, отпусков,
       мероприятий; добавление работника). Переход — кнопка
       «Работники» ряда 1 тулбара и заголовок «Работник +» шапки
       сетки (только редакторам). Карточка .ws-wcard — панель с
       внутренностями попапа шахматки (ws-popup-title/поля/секции
       тех же классов); счётчик сверху; кнопка «+» в шапке
       страницы — шторка создания #wsEmpSheet (openEmployeeForm) */
    .ws-workers-body {
        padding: 10px 12px 24px;
        max-width: 760px;
        margin: 0 auto;
    }
    .ws-workers-count {
        font-size: 12px;
        opacity: 0.75;
        margin: 2px 2px 10px;
    }
    .ws-wcard {
        background: var(--bg-tertiary, #0e1621);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 12px 14px 8px;
        margin-bottom: 12px;
    }
    [data-theme="light"] .ws-wcard {
        background: var(--bg-tertiary, #e9e7de);
        border-color: rgba(0,0,0,0.1);
    }
    .ws-workers-add {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.06);
        color: inherit;
        font-size: 20px;
        line-height: 1;
        font-weight: 700;
        cursor: pointer;
        flex: none;
    }
    .ws-workers-add:hover { background: rgba(255,255,255,0.12); }
    [data-theme="light"] .ws-workers-add {
        border-color: rgba(0,0,0,0.18);
        background: rgba(0,0,0,0.05);
    }
    [data-theme="light"] .ws-workers-add:hover { background: rgba(0,0,0,0.1); }

    /* ============================================================
       Task 334 (заявка: МОБИЛЬНАЯ ВЕРСИЯ ТАБЕЛЬНОГО УЧЁТА):
''', 1))

# ============================================================
# 2. HTML: кнопка «Работники» в ряду 1 (после «Печать»)
# ============================================================
R(('HTML: кнопка «Работники» ряда 1', '''<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V6z" fill="currentColor"/></svg>Печать</button>
                    </div>
''', '''<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V6z" fill="currentColor"/></svg>Печать</button>
                    <!-- Task 385: кнопка «Работники» — переход на
                         страницу полных карточек #page-ws-workers
                         (внесение/редактирование данных профиля,
                         отпусков и мероприятий, добавление
                         работника). Только редакторам (право
                         workschedule.edit: видимость —
                         _onRoleUpdate, двойная защита —
                         openWorkersPage). До Task 385 кнопки правки
                         жили в карточке шахматки (Task 384) — попап
                         стал чисто информационным -->
                    <button type="button" id="wsWorkersBtn" class="ws-refresh-btn ws-workers-btn" onclick="WorkSchedule.openWorkersPage()" hidden><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" fill="currentColor"/></svg>Работники</button>
                    </div>
''', 1))

# ============================================================
# 3. HTML: кнопка «Легенда» в ряду 2 (после вкладки «Год»)
# ============================================================
R(('HTML: кнопка «Легенда» ряда 2', '''                        <button type="button" id="wsTtTabYear" class="ws-tt-tab" onclick="WorkSchedule.setTotalsTab('year')" hidden>Год</button>
                    </div>
''', '''                        <button type="button" id="wsTtTabYear" class="ws-tt-tab" onclick="WorkSchedule.setTotalsTab('year')" hidden>Год</button>
                        <!-- Task 385: кнопка-переключатель «Легенда» —
                             окно расшифровки всех сокращений шахматки
                             (справа, по принципу шторки итогов).
                             Видна всем ролям (просмотр); открытие
                             закрывает открытые итоги — окна бара
                             взаимоисключающие -->
                        <button type="button" id="wsLegendBtn" class="ws-totals-btn ws-legend-btn" onclick="WorkSchedule.toggleLegend()" aria-pressed="false">Легенда</button>
                    </div>
''', 1))

# ============================================================
# 4. HTML: подсказка «Обновить» — сотрудники → работники
# ============================================================
R(('HTML: wsRefreshTip desc', '''<div class="ws-rt-desc">Обновить данные графика с сервера: сотрудники, записи, мероприятия, планы отпусков, коды. Локальная копия открывается мгновенно — эта кнопка подгружает свежие данные.</div>''',
   '''<div class="ws-rt-desc">Обновить данные графика с сервера: работники, записи, мероприятия, планы отпусков, коды. Локальная копия открывается мгновенно — эта кнопка подгружает свежие данные.</div>''', 1))

# ============================================================
# 5. HTML: подсказка «Вид» — сотрудники → работники (×3)
# ============================================================
R(('HTML: wsViewTipDesc', '''<div class="ws-rt-desc" id="wsViewTipDesc">Переключение вида табеля: полный — все сотрудники, доступна шторка «Итоги учёта»; сменный — только сменные сотрудники; дневной — только дневные. Клик по кнопке переключает вид по кругу.</div>''',
   '''<div class="ws-rt-desc" id="wsViewTipDesc">Переключение вида табеля: полный — все работники, доступна шторка «Итоги учёта»; сменный — только сменные работники; дневной — только дневные. Клик по кнопке переключает вид по кругу.</div>''', 1))

# ============================================================
# 6. HTML: шторка «Легенда» (после закрытия wsTotalsDrawer,
#    внутри #wsWsBody)
# ============================================================
R(('HTML: #wsLegendDrawer', '''                    <div class="ws-tt-hbar" id="wsTtHbar" aria-hidden="true"><div class="ws-hbar-thumb"></div></div>
                </div>
            </div>
            </div>
        </div>
''', '''                    <div class="ws-tt-hbar" id="wsTtHbar" aria-hidden="true"><div class="ws-hbar-thumb"></div></div>
                </div>
            </div>
            <!-- Task 385: ШТОРКА «ЛЕГЕНДА» — окно расшифровки всех
                 сокращений шахматки (кнопка «Легенда» в ряду 2
                 тулбара; принцип — как у шторки итогов: десктоп —
                 выезжает справа, сжимая сетку; мобайл — fixed-оверлей
                 ~86vw). Контент — _renderLegendSheet: коды дней Т-12/Т-13
                 из справочника «Коды_статусов» (живые цвета), коды
                 мероприятий, обозначения вёрстки. Взаимоисключающая
                 с «Итогами учёта» -->
            <div id="wsLegendDrawer" class="ws-legend-drawer">
                <div class="ws-lg-edge" aria-hidden="true"></div>
                <div class="ws-legend-inner">
                    <div class="ws-lg-head">Сокращения в шахматке</div>
                    <div class="ws-lg-body" id="wsLegendBody"></div>
                </div>
            </div>
            </div>
        </div>
''', 1))

# ============================================================
# 7. HTML: страница «Работники» (после мобильной страницы итогов)
# ============================================================
R(('HTML: #page-ws-workers', '''                <div id="wsTtPageBody" class="ws-tt-body ws-tt-page-body"></div>
            </div>
        </div>
''', '''                <div id="wsTtPageBody" class="ws-tt-body ws-tt-page-body"></div>
            </div>
        </div>

        <!-- ============ Task 385: СТРАНИЦА «РАБОТНИКИ» — полные
             карточки (переход — кнопка «Работники» в ряду 1 тулбара
             табеля и заголовок «Работник +» шапки сетки; только
             редакторам). Карточка каждого работника: профиль,
             отпуска года (✎/✕/«+ Отпуск…»), мероприятия месяца
             (✎/✕/«+ Мероприятие…»), «Правка данных…» (шторка
             #wsEmpSheet, таб. № — readonly PK) и «Уволить…» — всё,
             что до Task 385 жило в карточке шахматки (попап стал
             чисто информационным). Рендер — _renderWorkersPage
             (порядок — как строки шахматки); данные обновляются
             вместе с сеткой (loadGrid(true) → _renderGrid →
             _renderWorkersIfOpen); «+» в шапке — шторка создания
             (openEmployeeForm) -->
        <div id="page-ws-workers" class="page-content">
            <div class="page-inline-header">
                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Работники</div>
                <button type="button" id="wsWorkersAddBtn" class="ws-workers-add" onclick="WorkSchedule.openEmployeeForm()" aria-label="Добавить работника">+</button>
            </div>
            <div id="wsWorkersBody" class="ws-workers-body"></div>
        </div>
''', 1))

# ============================================================
# 8. HTML: aria-label карточки шахматки
# ============================================================
R(('HTML: aria-label карточки', '''<div id="wsEmpPopup" class="ws-cell-popup ws-emp-popup" role="dialog" aria-label="Карточка сотрудника"></div>''',
   '''<div id="wsEmpPopup" class="ws-cell-popup ws-emp-popup" role="dialog" aria-label="Карточка работника"></div>''', 1))

# ============================================================
# 9. HTML: шторка создания — «Новый работник»
# ============================================================
R(('HTML: заголовок шторки создания', '''<div class="flow-input-sheet-title" id="wsEmpSheetTitle">Новый сотрудник</div>''',
   '''<div class="flow-input-sheet-title" id="wsEmpSheetTitle">Новый работник</div>''', 1))

# ============================================================
# 10. HTML: шторка увольнения — «работник» (заголовок/лейбл/info)
# ============================================================
R(('HTML: шторка увольнения', '''    <div class="flow-input-sheet-title">Увольнение сотрудника</div>''',
   '''    <div class="flow-input-sheet-title">Увольнение работника</div>''', 1))
R(('HTML: лейбл шторки увольнения', '''            <label class="flow-input-label">Сотрудник</label>
            <div id="wsDismissEmp" class="ws-dismiss-emp">—</div>''',
   '''            <label class="flow-input-label">Работник</label>
            <div id="wsDismissEmp" class="ws-dismiss-emp">—</div>''', 1))
R(('HTML: info шторки увольнения', '''<div class="ws-dismiss-info">Сотрудник уйдёт из графика — строка останется в архиве справочника «Сотрудники»</div>''',
   '''<div class="ws-dismiss-info">Работник уйдёт из графика — строка останется в архиве справочника</div>''', 1))

# ============================================================
# 11. JS: Esc закрывает и шторку легенды
# ============================================================
R(('JS: Esc — легенда', '''            document.addEventListener('keydown', function(ev) {
                if (ev.key === 'Escape') {
                    selfOnce.closeCellPopup();
                    selfOnce.closeEmpPopup();
''', '''            document.addEventListener('keydown', function(ev) {
                if (ev.key === 'Escape') {
                    selfOnce.closeCellPopup();
                    selfOnce.closeEmpPopup();
                    // Task 385: Esc закрывает и шторку «Легенда»
                    if (selfOnce._legendOpen && typeof selfOnce._setLegend === 'function') {
                        selfOnce._setLegend(false);
                    }
''', 1))

# ============================================================
# 12. JS: _onRoleUpdate — видимость кнопки «Работники»
# ============================================================
R(('JS: _onRoleUpdate — wsWorkersBtn', '''            var genBtn = document.getElementById('wsGenerateBtn');
            if (genBtn) genBtn.hidden = !newCanEdit;
''', '''            var genBtn = document.getElementById('wsGenerateBtn');
            if (genBtn) genBtn.hidden = !newCanEdit;
            // Task 385: «Работники» (ряд 1) — страница полных
            // карточек; видна только редакторам (workschedule.edit)
            var workersBtn = document.getElementById('wsWorkersBtn');
            if (workersBtn) workersBtn.hidden = !newCanEdit;
''', 1))

# ============================================================
# 13. JS: тосты вида — работники (×4)
# ============================================================
R(('JS: тосты вида', '''            var titles = {
                full: 'Полный вид — все сотрудники, итоги учёта доступны',
                shift: 'Сменный вид — только сменные сотрудники',
                day: 'Дневной вид — только дневные сотрудники'
            };
            if (this._viewLevel === 'min') {
                // Task 340: у «min» итогов нет — тост без обещания
                titles.full = 'Полный вид — все сотрудники (кроме «Мастер КИПиА»)';
            }
''', '''            var titles = {
                full: 'Полный вид — все работники, итоги учёта доступны',
                shift: 'Сменный вид — только сменные работники',
                day: 'Дневной вид — только дневные работники'
            };
            if (this._viewLevel === 'min') {
                // Task 340: у «min» итогов нет — тост без обещания
                titles.full = 'Полный вид — все работники (кроме «Мастер КИПиА»)';
            }
''', 1))

# ============================================================
# 14. JS: описание подсказки вида — работники (×5)
# ============================================================
R(('JS: подсказка вида', '''                if (this._viewLocked) {
                    descEl.textContent = 'Роли «КИП ИОС дежурный» доступен ' +
                        'только сменный вид: шахматка сменных сотрудников, ' +
                        'шторка итогов и шахматка дневных недоступны.';
                } else {
                    descEl.textContent = 'Переключение вида табеля: полный — ' +
                        'все сотрудники и шторка «Итоги учёта»; сменный — ' +
                        'только сменные сотрудники; дневной — только дневные. ' +
                        'Клик по кнопке переключает вид по кругу.';
                }
''', '''                if (this._viewLocked) {
                    descEl.textContent = 'Роли «КИП ИОС дежурный» доступен ' +
                        'только сменный вид: шахматка сменных работников, ' +
                        'шторка итогов и шахматка дневных недоступны.';
                } else {
                    descEl.textContent = 'Переключение вида табеля: полный — ' +
                        'все работники и шторка «Итоги учёта»; сменный — ' +
                        'только сменные работники; дневной — только дневные. ' +
                        'Клик по кнопке переключает вид по кругу.';
                }
''', 1))

# ============================================================
# 15. JS: печать — «Работник» в шапке таблицы
# ============================================================
R(('JS: печать — Работник', '''html += '<th class="wsp-emp" style="width:' + empWmm + 'mm">Сотрудник</th>';''',
   '''html += '<th class="wsp-emp" style="width:' + empWmm + 'mm">Работник</th>';''', 1))

# ============================================================
# 16. JS: пустое состояние сетки — работники + страница
# ============================================================
R(('JS: admin-empty сетки', '''wrap.innerHTML = '<div class="admin-empty">Нет активных сотрудников. Добавьте их на странице «Сотрудники».</div>';''',
   '''wrap.innerHTML = '<div class="admin-empty">Нет активных работников. Добавьте их на странице «Работники».</div>';''', 1))
R(('JS: admin-empty вида', '''wrap.innerHTML = '<div class="admin-empty">Сотрудники вида «' +''',
   '''wrap.innerHTML = '<div class="admin-empty">Работники вида «' +''', 1))

# ============================================================
# 17. JS: шапка сетки — «Работник» + переход на страницу
# ============================================================
R(('JS: шапка сетки — Работник +', '''            // Task 311: заголовок «Сотрудник» — КНОПКА добавления
            // (кнопка «+ Сотрудник» из тулбара удалена): редакторам —
            // плюсик-индикатор, курсор-палец и подсветка наведения
            // (класс ws-emp-head-add), клик открывает шторку
            // #wsEmpSheet (openEmployeeForm); зрителям — обычный
            // заголовок без клика. Двойная защита: класс/onclick
            // вешаются по _canEdit, а сам openEmployeeForm внутри
            // ещё раз проверяет право записи.
            var empHeadAdd = this._canEdit ? ' ws-emp-head-add' : '';
            // Task 335 (заявка): «Сотрудник +» в суженном виде —
            // «Сотр»: текст в span с data-full/data-s4 — тот же
            // span-обмен, что у ФИО (_narrowApply); плюсик-индикатор
            // скрывается CSS (.ws-grid.ws-narrow .ws-emp-head-plus)
            html += '<th class="ws-emp-col' + empHeadAdd + '"' +
                    (this._canEdit
                        ? ' onclick="WorkSchedule.openEmployeeForm()"'
                        : '') +
                    '><span class="ws-emp-head-txt" data-full="Сотрудник" data-s4="Сотр">Сотрудник</span>' +
                    (this._canEdit ? '<i class="ws-emp-head-plus">+</i>' : '') +
                    '</th>';
''', '''            // Task 311 → 385: заголовок «Работник» — КНОПКА ПЕРЕХОДА
            // на страницу полных карточек «Работники» (Task 385:
            // внесение/правка данных переехали туда — карточка
            // шахматки стала чисто информационной): редакторам —
            // плюсик-индикатор, курсор-палец и подсветка наведения
            // (класс ws-emp-head-add), клик открывает страницу
            // (openWorkersPage); зрителям — обычный заголовок без
            // клика. Двойная защита: класс/onclick вешаются по
            // _canEdit, а сам openWorkersPage ещё раз проверяет право
            // записи. До Task 385 здесь открывалась шторка создания
            // #wsEmpSheet (Task 311) — теперь шторка открывается
            // кнопкой «+» на странице «Работники»
            var empHeadAdd = this._canEdit ? ' ws-emp-head-add' : '';
            // Task 335 (заявка): «Работник +» в суженном виде —
            // «Рабо»: текст в span с data-full/data-s4 — тот же
            // span-обмен, что у ФИО (_narrowApply); плюсик-индикатор
            // скрывается CSS (.ws-grid.ws-narrow .ws-emp-head-plus)
            html += '<th class="ws-emp-col' + empHeadAdd + '"' +
                    (this._canEdit
                        ? ' onclick="WorkSchedule.openWorkersPage()"'
                        : '') +
                    '><span class="ws-emp-head-txt" data-full="Работник" data-s4="Рабо">Работник</span>' +
                    (this._canEdit ? '<i class="ws-emp-head-plus">+</i>' : '') +
                    '</th>';
''', 1))

# ============================================================
# 18. JS: хвост _renderGrid — обновление страницы «Работники»
# ============================================================
R(('JS: _renderGrid хвост — workers', '''            this._renderTotalsIfOpen();
            // Task 334: сужение ФИО — восстановить, если контейнер
''', '''            this._renderTotalsIfOpen();
            // Task 385: страница «Работники» — если открыта, карточки
            // обновляются вместе с сеткой (правки/перезагрузка данных
            // перерисовывают и полные карточки работников)
            if (typeof this._renderWorkersIfOpen === 'function') this._renderWorkersIfOpen();
            // Task 334: сужение ФИО — восстановить, если контейнер
''', 1))

# ============================================================
# 19. JS: _renderEmpPopup → обёртка (только чтение)
#     + новый _renderWorkerCard(tabNo, withEdit)
# ============================================================
R(('JS: _renderEmpPopup → обёртка + _renderWorkerCard', '''        _renderEmpPopup: function(tabNo) {
            var emp = null;
            for (var j = 0; j < this._EMPLOYEES.length; j++) {
                if (this._EMPLOYEES[j]['таб_номер'] === tabNo) {
                    emp = this._EMPLOYEES[j];
                    break;
                }
            }
''', '''        _renderEmpPopup: function(tabNo) {
            // Task 385: карточка в шахматке — ТОЛЬКО ЧТЕНИЕ для всех
            // уровней (заявка: все кнопки правки убраны из окна
            // информации; внесение/редактирование — на странице
            // «Работники»). Общий рендер — _renderWorkerCard
            return this._renderWorkerCard(tabNo, false);
        },

        // Task 385: ПОЛНАЯ КАРТОЧКА РАБОТНИКА — общий рендер: попап
        // шахматки (withEdit=false — чистая информация) и страница
        // «Работники» (withEdit=true — «Правка данных…», «Уволить…»,
        // ✎/✕ отпусков, «+ Отпуск…», ✎/✕ мероприятий,
        // «+ Мероприятие…»; страница открывается только редакторам —
        // кнопка тулбара/заголовок сетки гейтятся _canEdit, двойная
        // защита — openWorkersPage и _renderWorkersPage)
        _renderWorkerCard: function(tabNo, withEdit) {
            var emp = null;
            for (var j = 0; j < this._EMPLOYEES.length; j++) {
                if (this._EMPLOYEES[j]['таб_номер'] === tabNo) {
                    emp = this._EMPLOYEES[j];
                    break;
                }
            }
''', 1))

# --- гейты withEdit + «работника» в title ---
R(('JS: карточка — «Правка данных…» withEdit', '''            // Task 384: «Правка данных…» — шторка сотрудника в режиме
            // ПРАВКИ (профиль: ФИО/тип/смена/шаблон/старт/приём/
            // должность/комментарий; таб. № — readonly, PK). Сервер:
            // workSchedule.updateEmployee. Только редакторам — как
            // «Уволить…» (двойная защита в openEmpEditForm)
            if (this._canEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-editdata"' +
                        ' title="Правка данных сотрудника: ФИО, режим, должность…"' +
                        ' onclick="WorkSchedule.openEmpEditForm(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">Правка данных…</div>';
            }
''', '''            // Task 384 → 385: «Правка данных…» — шторка работника в
            // режиме ПРАВКИ (профиль: ФИО/тип/смена/шаблон/старт/
            // приём/должность/комментарий; таб. № — readonly, PK).
            // Сервер: workSchedule.updateEmployee. Со страницы
            // «Работники» (withEdit; до Task 385 — из карточки
            // шахматки; двойная защита в openEmpEditForm)
            if (withEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-editdata"' +
                        ' title="Правка данных работника: ФИО, режим, должность…"' +
                        ' onclick="WorkSchedule.openEmpEditForm(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">Правка данных…</div>';
            }
''', 1))

R(('JS: карточка — «Уволить…» withEdit', '''            // Task 318: «Уволить…» — форма увольнения (дата → таблица
            // «Сотрудники», строка сотрудника уходит из шахматки,
            // остаётся в архиве справочника). Только ролям с правом
            // записи — как «+ Отпуск…» (двойная защита в
            // openDismissForm); красная строка — опасное действие
            if (this._canEdit) {
''', '''            // Task 318 → 385: «Уволить…» — форма увольнения (дата →
            // таблица «Сотрудники», строка работника уходит из
            // шахматки, остаётся в архиве справочника). Со страницы
            // «Работники» (withEdit; двойная защита в
            // openDismissForm); красная строка — опасное действие
            if (withEdit) {
''', 1))

R(('JS: карточка — ✎/✕ отпусков withEdit', '''                    var vActs = '';
                    var vId = parseInt(vv.id, 10);
                    if (this._canEdit && vId) {
''', '''                    var vActs = '';
                    var vId = parseInt(vv.id, 10);
                    if (withEdit && vId) {
''', 1))

R(('JS: карточка — «+ Отпуск…» withEdit', '''            // Task 312: «+ Отпуск…» — функционал убранной из тулбара
            // кнопки «+ Отпуск» (Task 308): открывает шторку «Новый
            // отпуск» с УЖЕ ВЫБРАННЫМ сотрудником карточки (префилл
            // таб. № — free-часть и лимит года посчитаются сразу).
            // Только ролям с правом записи — как «+ Мероприятие…» в
            // попапе ячейки (двойная защита — в openVacationForm).
            // Дни каждого периода — «чистые» (минус праздники ст. 112
            // ТК РФ, ст. 120) с пометкой о вычтенных (Task 310);
            // итог года с лимитом — в шторке, не в карточке (Task 311)
            if (this._canEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addvac"' +
                        ' title="Добавить период отпуска этому сотруднику"' +
                        ' onclick="WorkSchedule.onEmpAddVacation(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Отпуск…</div>';
            }
''', '''            // Task 312 → 385: «+ Отпуск…» — открывает шторку «Новый
            // отпуск» с УЖЕ ВЫБРАННЫМ работником карточки (префилл
            // таб. № — free-часть и лимит года посчитаются сразу).
            // Со страницы «Работники» (withEdit; двойная защита — в
            // openVacationForm). Дни каждого периода — «чистые» (минус
            // праздники ст. 112 ТК РФ, ст. 120) с пометкой о
            // вычтенных (Task 310); итог года с лимитом — в шторке
            // (Task 311)
            if (withEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addvac"' +
                        ' title="Добавить период отпуска этому работнику"' +
                        ' onclick="WorkSchedule.onEmpAddVacation(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Отпуск…</div>';
            }
''', 1))

R(('JS: карточка — ✎/✕ мероприятий withEdit', '''                    var acts = '';
                    if (this._canEdit && trId) {
''', '''                    var acts = '';
                    if (withEdit && trId) {
''', 1))

R(('JS: карточка — «+ Мероприятие…» withEdit', '''            // Task 384: «+ Мероприятие…» — шторка «Новое мероприятие»
            // с УЖЕ ВЫБРАННЫМ сотрудником карточки (как «+ Отпуск…»,
            // Task 312). Только редакторам (двойная защита —
            // onEmpAddTraining → openTrainingForm)
            if (this._canEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addtr"' +
                        ' title="Добавить мероприятие этому сотруднику"' +
                        ' onclick="WorkSchedule.onEmpAddTraining(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Мероприятие…</div>';
            }
''', '''            // Task 384 → 385: «+ Мероприятие…» — шторка «Новое
            // мероприятие» с УЖЕ ВЫБРАННЫМ работником карточки (как
            // «+ Отпуск…», Task 312). Со страницы «Работники»
            // (withEdit; двойная защита — onEmpAddTraining →
            // openTrainingForm)
            if (withEdit) {
                html += '<div class="ws-popup-row ws-popup-more ws-emp-addtr"' +
                        ' title="Добавить мероприятие этому работнику"' +
                        ' onclick="WorkSchedule.onEmpAddTraining(\\'' +
                        this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Мероприятие…</div>';
            }
''', 1))

# ============================================================
# 20. JS: новые методы страницы «Работники» (после _renderWorkerCard)
# ============================================================
R(('JS: методы страницы «Работники»', '''            return html;
        },

        // Серверная запись по ключу (без pending-наложения)
''', '''            return html;
        },

        // Task 385: СТРАНИЦА «РАБОТНИКИ» — переход (кнопка тулбара
        // «Работники» в ряду 1 / заголовок «Работник +» шапки сетки).
        // Гейт _canEdit — двойная защита (кнопки видны только
        // редакторам); страница — полные карточки всех активных
        // работников с внесением/редактированием данных
        openWorkersPage: function() {
            if (!this._canEdit) return;
            if (typeof navigateTo === 'function') navigateTo('ws-workers');
            this._renderWorkersPage();
        },

        // хук navigateTo('ws-workers') (прямой заход по URL/#hash,
        // возврат на страницу): рендер карточек после активации —
        // паттерн onTotalsPageOpen (Task 334)
        onWorkersPageOpen: function() {
            this._renderWorkersPage();
        },

        _renderWorkersIfOpen: function() {
            var pg = document.getElementById('page-ws-workers');
            if (pg && pg.classList && pg.classList.contains('active')) {
                this._renderWorkersPage();
            }
        },

        // полные карточки: порядок — как строки шахматки
        // (_sortEmployees, Task 259: сменные по сменам 1..5, затем
        // дневные, внутри — по алфавиту); с правом записи — кнопки
        // правки в каждой карточке (_renderWorkerCard withEdit)
        _renderWorkersPage: function() {
            var body = document.getElementById('wsWorkersBody');
            if (!body) return;
            if (!this._EMPLOYEES || !this._EMPLOYEES.length) {
                body.innerHTML = '<div class="ws-tt-empty">Нет активных работников. ' +
                                 'Добавьте их кнопкой «+» в шапке страницы.</div>';
                return;
            }
            var withEdit = !!this._canEdit;
            var list = this._sortEmployees(this._EMPLOYEES);
            var html = '<div class="ws-workers-count">' + list.length + ' ' +
                       this._plural(list.length, ['работник', 'работника', 'работников']) +
                       '</div>';
            for (var i = 0; i < list.length; i++) {
                var tabNo = list[i]['таб_номер'];
                html += '<div class="ws-wcard">' +
                        this._renderWorkerCard(tabNo, withEdit) + '</div>';
            }
            body.innerHTML = html;
        },

        // Серверная запись по ключу (без pending-наложения)
''', 1))

# ============================================================
# 21. JS: toggleTotals — взаимоисключение (закрыть легенду)
# ============================================================
R(('JS: toggleTotals — закрыть легенду', '''        toggleTotals: function() {
            // толерантный гейт: моки/старые состояния без _view = полный
''', '''        toggleTotals: function() {
            // Task 385: взаимоисключающие окна бара — открытая
            // легенда закрывается НАПРЯМУЮ (_setLegend, без вызова
            // toggleLegend — иначе взаимная рекурсия)
            if (this._legendOpen && typeof this._setLegend === 'function') {
                this._setLegend(false);
            }
            // толерантный гейт: моки/старые состояния без _view = полный
''', 1))

# ============================================================
# 22. JS: _setLegend / toggleLegend / _renderLegendSheet (после
#     toggleTotals)
# ============================================================
R(('JS: _setLegend/toggleLegend/_renderLegendSheet', '''                var self = this;
                this._ttWideTimer = setTimeout(function() {
                    self._ttWideTimer = null;
                    self._ttCloseCleanup();
                }, 320);
                this._fitGrid();
            }
        },
''', '''                var self = this;
                this._ttWideTimer = setTimeout(function() {
                    self._ttWideTimer = null;
                    self._ttCloseCleanup();
                }, 320);
                this._fitGrid();
            }
        },

        // Task 385: ШТОРКА «ЛЕГЕНДА» — открытие/закрытие. Десктоп:
        // панель #wsLegendDrawer едет справа margin-right'ом (как
        // итоги: замер фикс-ширины inner → старт за краем → 0);
        // мобайл: transform-оверлей (класс ws-legend-open на
        // странице). Открытие закрывает итоги (взаимоисключающие
        // окна бара); закрытие — повторный клик/Esc
        _setLegend: function(open) {
            this._legendOpen = !!open;
            var btn = document.getElementById('wsLegendBtn');
            if (btn && btn.setAttribute) {
                btn.setAttribute('aria-pressed', open ? 'true' : 'false');
            }
            var page = document.getElementById('page-work-schedule');
            if (page && page.classList) {
                if (open) page.classList.add('ws-legend-open');
                else page.classList.remove('ws-legend-open');
            }
            if (open) this._renderLegendSheet();
            var drawer = document.getElementById('wsLegendDrawer');
            if (!drawer) return;
            var desktop = (typeof window !== 'undefined' && window.matchMedia
                && window.matchMedia('(min-width: 1024px)').matches);
            if (desktop) {
                // ширина = фикс-ширина inner (не зависит от нулевой
                // ширины свёрнутого drawer); открытие: старт за
                // правым краем, синхронный reflow, анимация к 0
                var inner = drawer.querySelector
                    ? drawer.querySelector('.ws-legend-inner') : null;
                var w = (inner && inner.getBoundingClientRect)
                    ? Math.ceil(inner.getBoundingClientRect().width) : 0;
                if (open) {
                    drawer.style.width = w + 'px';
                    drawer.style.marginRight = (-w) + 'px';
                    void drawer.offsetWidth;
                    drawer.style.marginRight = '0px';
                } else {
                    // уезжает за край анимацией (ширина остаётся —
                    // контент под overflow:hidden, flex-слот = 0)
                    drawer.style.marginRight = (-w) + 'px';
                }
                this._fitGrid();
            } else {
                drawer.style.width = '';
                drawer.style.marginRight = '';
            }
        },

        toggleLegend: function() {
            // взаимоисключающие окна бара: открытые итоги
            // закрываются ПОЛНЫМ путём toggleTotals (он снимет и
            // классы, и маржу; сам toggleTotals легенду не зовёт —
            // рекурсии нет)
            if (this._totalsOpen) this.toggleTotals();
            this._setLegend(!this._legendOpen);
        },

        // Task 385: контент шторки «Легенда» — все сокращения
        // шахматки: коды дней Т-12/Т-13 и коды мероприятий из
        // справочника «Коды_статусов» (живые цвета ячеек — свотчи),
        // затем — обозначения вёрстки (бейдж плановой смены,
        // «сегодня», рамки выходных, праздники в отпусках)
        _renderLegendSheet: function() {
            var body = document.getElementById('wsLegendBody');
            if (!body) return;
            var html = '';
            var codes = this._STATUS_CODES || [];
            var evSet = {};
            for (var k = 0; k < (this._EVENT_CODES || []).length; k++) {
                evSet[this._EVENT_CODES[k]] = true;
            }
            var dayHtml = '', evHtml = '';
            for (var i = 0; i < codes.length; i++) {
                var c = codes[i];
                var row = '<div class="ws-lg-item"><span class="ws-lg-swatch" style="background:' +
                          this._esc(String(c.color || '#3a3a3a')) + '"></span><span class="ws-lg-code">' +
                          this._esc(String(c.code || '')) + '</span><span class="ws-lg-name">' +
                          this._esc(String(c.name || '')) + '</span></div>';
                if (evSet[String(c.code)]) evHtml += row;
                else dayHtml += row;
            }
            html += '<div class="ws-lg-sec">Коды дней (Т-12/Т-13)</div>';
            html += dayHtml ||
                '<div class="ws-lg-note">Справочник кодов ещё не загружен — нажмите «Обновить».</div>';
            html += '<div class="ws-lg-sec">Коды мероприятий</div>';
            html += evHtml ||
                '<div class="ws-lg-note">Справочник кодов ещё не загружен — нажмите «Обновить».</div>';
            html += '<div class="ws-lg-note">Код мероприятия ставится в угол ячейки ПОВЕРХ плановой смены (Д/Н); ручная правка дня сильнее.</div>';
            html += '<div class="ws-lg-sec">Обозначения в шахматке</div>';
            html += '<div class="ws-lg-note">Бейдж «Д»/«Н» в правом нижнем углу ячейки отпуска — плановая смена по циклу (только у сменных работников).</div>';
            html += '<div class="ws-lg-note">Подсветка числа и столбца — сегодняшняя дата.</div>';
            html += '<div class="ws-lg-note">Рамка 2px вокруг группы ячеек — выходные и праздники; «*» у числа (24*) — сокращённый предпраздничный день.</div>';
            html += '<div class="ws-lg-note">В отпусках: «12 дней (−2 праздн.)» — вычтены праздники (ст. 120 ТК РФ); годовой лимит — 42 дня (ст. 125 ТК РФ, до 3 частей).</div>';
            html += '<div class="ws-lg-note">Зебра строк — чередование фона по работникам; перекрестье — подсветка строки и столбца при наведении (кнопка в ряду 3).</div>';
            body.innerHTML = html;
        },
''', 1))

# ============================================================
# 23. JS: итоги — «Работник» в шапках (×3) и пустые состояния
# ============================================================
R(('JS: итоги — шапки «Работник» ×3', '''data-full="Сотрудник" data-s4="Сотр">Сотрудник</span></th>';''',
   '''data-full="Работник" data-s4="Рабо">Работник</span></th>';''', 3))
R(('JS: итоги месяц — пусто', '''body.innerHTML = '<div class="ws-tt-empty">Нет активных сотрудников.</div>';''',
   '''body.innerHTML = '<div class="ws-tt-empty">Нет активных работников.</div>';''', 1))
R(('JS: итоги год — пусто', '''body.innerHTML = '<div class="ws-tt-empty">Нет сотрудников.</div>';''',
   '''body.innerHTML = '<div class="ws-tt-empty">Нет работников.</div>';''', 1))

# ============================================================
# 24. JS: шторка создания — заголовки «работник»
# ============================================================
R(('JS: «Новый работник»', '''            if (sheetTitle) sheetTitle.textContent = 'Новый сотрудник';''',
   '''            if (sheetTitle) sheetTitle.textContent = 'Новый работник';''', 1))
R(('JS: «Правка работника»', '''            if (sheetTitle) sheetTitle.textContent = 'Правка сотрудника';''',
   '''            if (sheetTitle) sheetTitle.textContent = 'Правка работника';''', 1))

# ============================================================
# 25. JS: «Работник не найден» (×2 — правка/увольнение)
# ============================================================
R(('JS: «Работник не найден» — правка', '''                if (typeof KipToast !== 'undefined') KipToast.show('Сотрудник не найден');
                return;
            }
            this._empEditTab = String(emp['таб_номер']);
''', '''                if (typeof KipToast !== 'undefined') KipToast.show('Работник не найден');
                return;
            }
            this._empEditTab = String(emp['таб_номер']);
''', 1))
R(('JS: «Работник не найден» — увольнение', '''                if (typeof KipToast !== 'undefined') KipToast.show('Сотрудник не найден');
                return;
            }
            this._dismissTabNo = String(emp['таб_номер']);
''', '''                if (typeof KipToast !== 'undefined') KipToast.show('Работник не найден');
                return;
            }
            this._dismissTabNo = String(emp['таб_номер']);
''', 1))

# ============================================================
# 26. JS: подтверждение увольнения — «Работник…»
# ============================================================
R(('JS: kipConfirm увольнения', '''                kipConfirm('Уволить ' + fio + '? Дата увольнения ' +
                           this._fmtDateRu(date) + '. Сотрудник уйдёт из ' +
                           'графика, строка останется в архиве справочника ' +
                           '«Сотрудники».', { danger: true })
''', '''                kipConfirm('Уволить ' + fio + '? Дата увольнения ' +
                           this._fmtDateRu(date) + '. Работник уйдёт из ' +
                           'графика, строка останется в архиве ' +
                           'справочника.', { danger: true })
''', 1))

# ============================================================
# 27. JS: тосты мутаций — «работник»
# ============================================================
R(('JS: тост «Работник уволен…»', '''                    KipToast.show('Сотрудник уволен и убран из графика');''',
   '''                    KipToast.show('Работник уволен и убран из графика');''', 1))
R(('JS: тост «Данные работника обновлены»', '''                        KipToast.show('Данные сотрудника обновлены');''',
   '''                        KipToast.show('Данные работника обновлены');''', 1))
R(('JS: тост «Работник добавлен»', '''                    KipToast.show('Сотрудник добавлен');''',
   '''                    KipToast.show('Работник добавлен');''', 1))

# ============================================================
# 28. JS: «Выберите работника» (×2 — валидации шторок)
# ============================================================
R(('JS: «Выберите работника» ×2', '''if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Выберите сотрудника'); return; }''',
   '''if (!tabNo) { if (typeof KipToast !== 'undefined') KipToast.show('Выберите работника'); return; }''', 2))

# ============================================================
# 29. KipAuth: _WORK_SCHEDULE_PAGES + ws-workers
# ============================================================
R(('JS: _WORK_SCHEDULE_PAGES', '''        // Task 334: + мобильная страница итогов учёта (те же права,
        // что у табеля — доступ наследуют все роли с workschedule.view)
        _WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals'],
''', '''        // Task 334: + мобильная страница итогов учёта (те же права,
        // что у табеля — доступ наследуют все роли с workschedule.view)
        // Task 385: + страница «Работники» (полные карточки; кнопки
        // правки внутри — только редакторам workschedule.edit)
        _WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers'],
''', 1))

# ============================================================
# 30. navigateTo: хук страницы «Работники»
# ============================================================
R(('JS: navigateTo — хук ws-workers', '''        if (page === 'ws-totals') {
            setTimeout(() => { if (typeof WorkSchedule !== 'undefined' && WorkSchedule.onTotalsPageOpen) WorkSchedule.onTotalsPageOpen(); }, 30);
        } else if (typeof WorkSchedule !== 'undefined' && WorkSchedule._ttPage) {
            WorkSchedule.onTotalsPageClose();
        }
''', '''        if (page === 'ws-totals') {
            setTimeout(() => { if (typeof WorkSchedule !== 'undefined' && WorkSchedule.onTotalsPageOpen) WorkSchedule.onTotalsPageOpen(); }, 30);
        } else if (typeof WorkSchedule !== 'undefined' && WorkSchedule._ttPage) {
            WorkSchedule.onTotalsPageClose();
        }
        // Task 385: страница «Работники» — рендер полных карточек
        // после активации (прямой заход по URL/возврат на страницу)
        if (page === 'ws-workers') {
            setTimeout(() => { if (typeof WorkSchedule !== 'undefined' && WorkSchedule.onWorkersPageOpen) WorkSchedule.onWorkersPageOpen(); }, 30);
        }
''', 1))

# ============================================================
# 31. Карта «страница → раздел» (фильтр «№ проекта»)
# ============================================================
R(('JS: карта разделов — ws-workers', '''        // Task 334: мобильная страница «Итоги учёта» — дочь табеля
        // (крошки: … / Табель учёта рабочего времени / Итоги учёта)
        'ws-totals':                'work-schedule',
''', '''        // Task 334: мобильная страница «Итоги учёта» — дочь табеля
        // (крошки: … / Табель учёта рабочего времени / Итоги учёта)
        'ws-totals':                'work-schedule',
        // Task 385: страница «Работники» — дочь табеля (полные
        // карточки; крошки: … / Табель учёта рабочего времени /
        // Работники)
        'ws-workers':               'work-schedule',
''', 1))

# ============================================================
# 32. Карта названий страниц (крошки)
# ============================================================
R(('JS: карта названий — ws-workers', '''        // Task 334: мобильная страница итогов учёта
        'ws-totals':                'Итоги учёта',
''', '''        // Task 334: мобильная страница итогов учёта
        'ws-totals':                'Итоги учёта',
        // Task 385: страница полных карточек работников
        'ws-workers':               'Работники',
''', 1))

# ============================================================
# 33. JS: комментарий openEmpEditForm — актуализация (работник,
#     страница «Работники»)
# ============================================================
R(('JS: комментарий openEmpEditForm', '''        // «Правка данных…») — шторка #wsEmpSheet в режиме ПРАВКИ:
        // поля заполняются значениями сотрудника, заголовок/кнопка
        // меняются («Правка сотрудника»/«Сохранить»), таб. № —
''', '''        // «Правка данных…» со страницы «Работники») — шторка
        // #wsEmpSheet в режиме ПРАВКИ: поля заполняются значениями
        // работника, заголовок/кнопка меняются («Правка
        // работника»/«Сохранить»), таб. № —
''', 1))

# ============================================================
# 34. HTML: комментарий попапа — Task 385 (read-only, правки на
#     странице «Работники»; тест-384-маркер обновляется)
# ============================================================
R(('HTML: комментарий попапа (read-only)', '''<!-- Task 309: карточка сотрудника — попап у колонки ФИО шахматки
     (КЛИК; Task 311: наведение больше не открывает — пояснительные
     окна при наведении убраны по заявке). Показывает данные,
     которые были в удалённых вкладках (Task 307/308): профиль
     («Сотрудники» — тип/смена/должность), план отпусков
     («Отпуска» — периоды года шахматки по частям) и мероприятия
     («Инструктажи» — события месяца с кнопками правки/удаления).
     Карточка прикреплена к клику: закрытие — фоновый кловер
     и Esc. Task 384: карточка — ЦЕНТР ПРАВКИ по отдельности:
     «Правка данных…» (профиль → updateEmployee), ✎/✕ у периодов
     отпусков (updateVacation/deleteVacation), «+ Мероприятие…»
     (openTrainingForm с префиллом) — редакторам; шахматка на
     месяц и год строится из этих данных («Сформировать»). -->''', '''<!-- Task 309: карточка работника — попап у колонки ФИО шахматки
     (КЛИК; Task 311: наведение больше не открывает — пояснительные
     окна при наведении убраны по заявке). Показывает данные,
     которые были в удалённых вкладках (Task 307/308): профиль
     («Сотрудники» — тип/смена/должность), план отпусков
     («Отпуска» — периоды года шахматки по частям) и мероприятия
     («Инструктажи» — события месяца). Карточка прикреплена к
     клику: закрытие — фоновый кловер и Esc. Task 384 приносил
     сюда центр правки («Правка данных…»/updateEmployee, ✎/✕
     отпусков updateVacation/deleteVacation, «+ Мероприятие…»);
     Task 385: карточка — ТОЛЬКО ЧТЕНИЕ для всех уровней —
     внесение/редактирование переехало на страницу «Работники»
     (кнопка тулбара / заголовок «Работник +»); шахматка на месяц
     и год строится из этих данных («Сформировать»). -->''', 1))

# ============================================================
# 35. JS: kipConfirm увольнения — неразрывное «архиве справочника»
# ============================================================
R(('JS: kipConfirm — неразрывный текст', '''                kipConfirm('Уволить ' + fio + '? Дата увольнения ' +
                           this._fmtDateRu(date) + '. Работник уйдёт из ' +
                           'графика, строка останется в архиве ' +
                           'справочника.', { danger: true })''', '''                kipConfirm('Уволить ' + fio + '? Дата увольнения ' +
                           this._fmtDateRu(date) + '. Работник уйдёт из ' +
                           'графика, строка останется в архиве справочника.',
                           { danger: true })''', 1))

# ============================================================
# 36. JS: init() — показать «Работники» по _canEdit (как genBtn;
#     _onRoleUpdate — вторая линия при поздней роли)
# ============================================================
R(('JS: init — wsWorkersBtn', '''            var genBtn = document.getElementById('wsGenerateBtn');
            if (genBtn) genBtn.hidden = !this._canEdit;
            // Task 337→340: кнопка ВИДА ТАБЕЛЯ #wsViewBtn — инструмент''', '''            var genBtn = document.getElementById('wsGenerateBtn');
            if (genBtn) genBtn.hidden = !this._canEdit;
            // Task 385: «Работники» (ряд 1) — страница полных карточек;
            // видна только редакторам (как «Сформировать»; повтор —
            // и в _onRoleUpdate: роль может прийти позже init)
            var workersBtnInit = document.getElementById('wsWorkersBtn');
            if (workersBtnInit) workersBtnInit.hidden = !this._canEdit;
            // Task 337→340: кнопка ВИДА ТАБЕЛЯ #wsViewBtn — инструмент''', 1))

if __name__ == '__main__':
    patch(INDEX, repls)
    print('Task 385: патч применён полностью')
