#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 395 — заявка (3 части):
#   (1) кнопка «Работники» (ряд 1 табеля) — НЕ отображается
#       пользователям БЕЗ доступа к разделу «Табель учёта рабочего
#       времени» (уровень null) и с ОГРАНИЧЕННЫМ просмотром (min)
#       по матрице доступа ролей; редакторам и зрителям (edit/view)
#       — видна (у зрителей карточки без правки);
#   (2) в картах работников: фон блоков карточек — НЕ сливается с
#       общим фоном окна; рамки блоков — ТОЛЩЕ (2px) и ЯРЧЕ, стиль
#       «выступающего вверх бордюрчика» (светлая верхняя кромка +
#       тень снизу);
#   (3) десктоп: блок ОТПУСКА — ПОД блоком профиля, блок
#       МЕРОПРИЯТИЯ — ПОД блоком отпуска (левая колонка), блок СИЗ —
#       ВЕРХНЯЯ ПРАВАЯ часть экрана (правая колонка).
# Все правки — только index.html (сервер не трогается).
import sys

path = 'index.html'
src = open(path, encoding='utf-8').read()

REPLS = []
def rep(old, new, cnt=1):
    REPLS.append((old, new, cnt))

# --- R1: JS init — видимость кнопки «Работники» по матрице ---
rep(
"""            // Task 385: «Работники» (ряд 1) — страница полных карточек;
            // видна только редакторам (как «Сформировать»; повтор —
            // и в _onRoleUpdate: роль может прийти позже init)
            var workersBtnInit = document.getElementById('wsWorkersBtn');
            if (workersBtnInit) workersBtnInit.hidden = !this._canEdit;
""",
"""            // Task 385 → 395: «Работники» (ряд 1) — страница карточек.
            // Task 395 (заявка): кнопка НЕ отображается пользователям
            // БЕЗ доступа к разделу (уровень null) и с ОГРАНИЧЕННЫМ
            // просмотром (min) — по матрице доступа ролей; редакторам
            // и зрителям (edit/view) — видна, у зрителей карточки без
            // правки (withEdit = _canEdit). Повтор — и в
            // _onRoleUpdate: роль может прийти позже init
            var workersBtnInit = document.getElementById('wsWorkersBtn');
            if (workersBtnInit) workersBtnInit.hidden =
                (this._viewLevel === null || this._viewLevel === 'min');
"""
)

# --- R2: JS _onRoleUpdate — та же логика при поздней роли ---
rep(
"""            // Task 385: «Работники» (ряд 1) — страница полных
            // карточек; видна только редакторам (workschedule.edit)
            var workersBtn = document.getElementById('wsWorkersBtn');
            if (workersBtn) workersBtn.hidden = !newCanEdit;
""",
"""            // Task 385 → 395: «Работники» (ряд 1) — страница
            // карточек. Task 395 (заявка): кнопка скрыта уровням null
            // (нет доступа к разделу) и min (ограниченный просмотр) —
            // по матрице доступа; edit/view — видна (у view карточки
            // без правки, withEdit = _canEdit)
            var workersBtn = document.getElementById('wsWorkersBtn');
            if (workersBtn) workersBtn.hidden =
                (newLevel === null || newLevel === 'min');
"""
)

# --- R3: JS openWorkersPage — гейт зеркален кнопке (edit/view) ---
rep(
"""        // Task 385 → 386: СТРАНИЦА «РАБОТНИКИ» — переход (кнопка
        // тулбара «Работники» в ряду 1 — ЕДИНСТВЕННЫЙ вход: Task 386
        // снял функцию кнопки с заголовка шапки сетки). Гейт
        // _canEdit — двойная защита (кнопка видна только
        // редакторам); страница — полные карточки всех активных
        // работников с внесением/редактированием данных
        openWorkersPage: function() {
            if (!this._canEdit) return;
""",
"""        // Task 385 → 386 → 395: СТРАНИЦА «РАБОТНИКИ» — переход
        // (кнопка тулбара «Работники» в ряду 1 — ЕДИНСТВЕННЫЙ вход:
        // Task 386 снял функцию кнопки с заголовка шапки сетки).
        // Task 395 (заявка): кнопка видна уровням edit/view (скрыта
        // для null — нет доступа к разделу — и min — ограниченный
        // просмотр); гейт перехода ЗЕРКАЛЕН кнопке — двойная защита.
        // Легаси-запас: уровень ещё не посчитан (undefined) —
        // производная от _canEdit (как до трёхуровневой схемы)
        openWorkersPage: function() {
            var lvl = (this._viewLevel === undefined)
                ? (this._canEdit ? 'edit' : 'view')
                : this._viewLevel;
            if (lvl !== 'edit' && lvl !== 'view') return;
"""
)

# --- R4: JS _renderWorkersPage — гейт edit/view (прямой URL тоже) ---
rep(
"""        _renderWorkersPage: function() {
            var body = document.getElementById('wsWorkersBody');
            if (!body) return;
            var withEdit = !!this._canEdit;
""",
"""        _renderWorkersPage: function() {
            var body = document.getElementById('wsWorkersBody');
            if (!body) return;
            // Task 395 (заявка): страница — уровням edit/view (как
            // кнопка «Работники» и карточка сетки); null (нет
            // доступа) и min (ограниченный просмотр) карточек НЕ
            // видят: прямой заход по URL — пустое тело (кнопка у них
            // скрыта — единственный вход недоступен). Легаси-запас:
            // уровень не посчитан — производная от _canEdit
            var lvl = (this._viewLevel === undefined)
                ? (this._canEdit ? 'edit' : 'view')
                : this._viewLevel;
            if (lvl !== 'edit' && lvl !== 'view') { body.innerHTML = ''; return; }
            var withEdit = !!this._canEdit;
"""
)

# --- R5: JS _renderWorkerCardPanels — колонки (лево: профиль/
#     отпуска/мероприятия; право: СИЗ) ---
rep(
"""        // Task 393 (заявка): ЧЕТЫРЕ БЛОКА карточки работника на
        // странице «Работники»: профиль с действиями / отпуска /
        // мероприятия / СИЗ — КАЖДЫЙ блок отдельным окном-панелью
        // .ws-wcard (вертикальный стек; зазор — margin-bottom, у
        // последнего — 0). Попап шахматки — прежний сплошной вид
        // (_renderWorkerCard без asBlocks)
        _renderWorkerCardPanels: function(tabNo, withEdit) {
            var blocks = this._renderWorkerCard(tabNo, withEdit, true);
            var html = '';
            for (var bi = 0; bi < blocks.length; bi++) {
                html += '<div class="ws-wcard">' + blocks[bi] + '</div>';
            }
            return html;
        },
""",
"""        // Task 393 (заявка): ЧЕТЫРЕ БЛОКА карточки работника на
        // странице «Работники»: профиль с действиями / отпуска /
        // мероприятия / СИЗ — КАЖДЫЙ блок отдельным окном-панелью
        // .ws-wcard. Попап шахматки — прежний сплошной вид
        // (_renderWorkerCard без asBlocks)
        // Task 395 (заявка, ДЕСКТОП): ОТПУСКА — ПОД блоком профиля,
        // МЕРОПРИЯТИЯ — ПОД блоком отпуска (ЛЕВАЯ колонка-обёртка
        // .ws-wcol), СИЗ — ВЕРХНЯЯ ПРАВАЯ часть экрана (ПРАВАЯ
        // колонка .ws-wcol-ppe; раскладка — CSS @media ≥1024px).
        // Мобайл ≤1023px — прежний вертикальный СТЕК: колонки без
        // правил раскладки = блоки друг под другом в прежнем
        // порядке (профиль → отпуска → мероприятия → СИЗ); зазоры —
        // margin-bottom панелей (Task 393) + межколоночный (CSS)
        _renderWorkerCardPanels: function(tabNo, withEdit) {
            var blocks = this._renderWorkerCard(tabNo, withEdit, true);
            var left = '', right = '';
            for (var bi = 0; bi < blocks.length; bi++) {
                var panel = '<div class="ws-wcard">' + blocks[bi] + '</div>';
                if (bi < 3) left += panel; else right += panel;
            }
            return '<div class="ws-wcol">' + left + '</div>' +
                   '<div class="ws-wcol ws-wcol-ppe">' + right + '</div>';
        },
"""
)

# --- R6: CSS .ws-wcard — фон не сливается + рамка толще/ярче ---
rep(
"""    .ws-wcard {
        background: var(--bg-tertiary, #0e1621);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        /* Task 393: карточка — ЧЕТЫРЕ блока-окна, текст крупнее
           (правила ниже) — паддинг чуть шире прежнего */
        padding: 14px 16px 12px;
        margin-bottom: 12px;
    }
    [data-theme="light"] .ws-wcard {
        background: var(--bg-tertiary, #e9e7de);
        border-color: rgba(0,0,0,0.1);
    }
""",
"""    .ws-wcard {
        /* Task 395 (заявка): фон блоков — НЕ сливается с общим фоном
           окна: тёмная тема — СВЕТЛЕЕ фона страницы #1a2233 (панель
           визуально «поднята» над страницей; прежний
           var(--bg-tertiary) #0e1621 был ТЕМНЕЕ фона и сливался).
           Рамка — ТОЛЩЕ (2px, было 1px) и ЯРЧЕ, стиль «выступающего
           вверх бордюрчика»: верхняя кромка — СВЕТЛАЯ (блик «света
           сверху»), бока — синее и ярче прежней, снизу — тень
           (окно приподнято над страницей) */
        background: #243349;
        border: 2px solid rgba(116, 162, 214, 0.42);
        border-top-color: rgba(152, 196, 240, 0.7);
        box-shadow: 0 3px 0 rgba(0, 0, 0, 0.24);
        border-radius: 10px;
        /* Task 393: карточка — ЧЕТЫРЕ блока-окна, текст крупнее
           (правила ниже) — паддинг чуть шире прежнего */
        padding: 14px 16px 12px;
        margin-bottom: 12px;
    }
    [data-theme="light"] .ws-wcard {
        /* Task 395: светлая — БЕЛАЯ панель поверх кремового фона
           страницы #FAF9F5 (не сливается); рамка 2px темнее + светлая
           верхняя кромка (блик) + тень снизу — тот же «приподнятый»
           стиль, что и в тёмной теме (правило выше) */
        background: #ffffff;
        border-color: rgba(20, 20, 19, 0.42);
        border-top-color: rgba(255, 255, 255, 0.95);
        box-shadow: 0 3px 0 rgba(20, 20, 19, 0.14);
    }
"""
)

# --- R7: CSS — колонки .ws-wcol + десктоп flex (замена сетки 2×2) ---
rep(
"""    /* Task 393: в теле вкладки карточка — ЧЕТЫРЕ блока-окна: зазор
       между ними — margin-bottom, у последнего — 0 (мобильный стек;
       на десктопе зазор задаёт сетка Task 394 ниже) */
    .ws-wtab-body .ws-wcard { margin-bottom: 12px; }
    .ws-wtab-body .ws-wcard:last-child { margin-bottom: 0; }
    /* Task 394 (заявка): ДЕСКТОП (≥1024px) — четыре блока карточки
       СЕТКОЙ 2×2, РАВНЫЕ колонки НА ВСЮ ШИРИНУ окна вкладок:
       профиль — слева сверху, ОТПУСКА — СПРАВА от профиля,
       МЕРОПРИЯТИЯ — под профилем, СИЗ — ПОД ОТПУСКАМИ (порядок
       блоков b1–b4 раскладывается сеткой сам). Обёртка .ws-wgrid2 —
       _renderWorkersPage (только вкладка работника; «Общая» — без
       сетки). Окна НЕ тянутся по высоте чужих строк (align-items:
       start); зазор — gap 12px, margin-bottom обнулён (базовые
       правила Task 393 остаются для мобильного стека ≤1023px) */
    @media (min-width: 1024px) {
        .ws-wgrid2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            align-items: start;
        }
        .ws-wgrid2 .ws-wcard { margin-bottom: 0; }
    }
""",
"""    /* Task 393: в теле вкладки карточка — ЧЕТЫРЕ блока-окна: зазор
       между ними — margin-bottom, у последнего — 0 (стек ВНУТРИ
       колонок Task 395 — и мобайл, и десктоп) */
    .ws-wtab-body .ws-wcard { margin-bottom: 12px; }
    .ws-wtab-body .ws-wcard:last-child { margin-bottom: 0; }
    /* Task 395 (заявка): КОЛОНКИ-обёртки .ws-wcol (сборка —
       _renderWorkerCardPanels: левая — профиль + отпуска +
       мероприятия, правая .ws-wcol-ppe — СИЗ). Мобайл ≤1023px —
       колонки БЕЗ правил раскладки = блоки друг под другом; зазор
       между колонками — margin-bottom, у последней — 0 (внутри
       колонок панелям — базовые правила Task 393 выше) */
    .ws-wgrid2 .ws-wcol { margin-bottom: 12px; }
    .ws-wgrid2 .ws-wcol:last-child { margin-bottom: 0; }
    /* Task 394 → 395 (заявка): ДЕСКТОП (≥1024px) — ДВЕ РАВНЫЕ
       колонки НА ВСЮ ШИРИНУ окна вкладок (flex, обёртка .ws-wgrid2
       — _renderWorkersPage, только вкладка работника; «Общая» — без
       колонок): ЛЕВАЯ — профиль, ПОД ним ОТПУСКА, под отпусками
       МЕРОПРИЯТИЯ (вертикальный стек окон); ПРАВАЯ — блок СИЗ в
       ВЕРХНЕЙ ПРАВОЙ части экрана (align-items: flex-start —
       правая колонка НЕ тянется по высоте левой). Зазоры: между
       колонками — gap 12px; между окнами левой колонки —
       margin-bottom панелей (базовые правила Task 393) */
    @media (min-width: 1024px) {
        .ws-wgrid2 {
            display: flex;
            flex-wrap: nowrap;
            gap: 12px;
            align-items: flex-start;
        }
        .ws-wgrid2 .ws-wcol {
            flex: 1 1 0;
            min-width: 0;
            margin-bottom: 0;
        }
    }
"""
)

# --- применяем ---
fail = 0
for old, new, cnt in REPLS:
    n = src.count(old)
    if n != cnt:
        print('ANCHOR FAIL (%d из %d):\n---\n%s\n---' % (n, cnt, old[:200]))
        fail += 1
        continue
    src = src.replace(old, new, cnt)
if fail:
    print('ПРОВАЛ: %d якорей не сошлись' % fail)
    sys.exit(1)

open(path, 'w', encoding='utf-8').write(src)
print('OK: %d правок применены' % len(REPLS))
