#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 379 — kip8test, index.html. Заявки пользователя:
#   1) «переделай, фон пустых ячеек #FFFFFF — ячейки значений не в
#      шторке итогов, а в шахматке табеля» — #FFFFFF из Task 378
#      относился к шахматке, а не к таблицам итогов: СВЕТЛАЯ тема —
#      фон ПУСТЫХ ячеек значений ШАХМАТКИ (.ws-cell, «.»-ячейка,
#      свотч «.» в попапе) #eef0f2 → #FFFFFF (Task 250 → 379).
#      Тёмная тема НЕ тронута (#eef0f2 + brightness(0.88), Task 319);
#      итоги учёта Task 378 (#FFFFFF/линии/без нулей) остаются —
#      теперь шахматка и итоги совпадают по фону.
#   2) «Окна „Мероприятия“ и „Нормы“ в баре, при раскрытии должны
#      смещаться вниз по верх бара, не увеличивая его в размере» —
#      раскрытое окно = ОВЕРЛЕЙ: низ уезжает вниз ПОВЕРХ ряда 2/3
#      бара и шахматки, ГАБАРИТ БАРА НЕ РАСТЁТ — прирост высоты
#      компенсируется отрицательным margin-bottom (95 − scrollHeight,
#      ставят _barExpSync/_barExpToggle): в grid-строке/колонке бар
#      окно занимает РОВНО 95px, сетка под баром не уезжает; height и
#      margin-bottom анимируются СИНХРОННО (сумма всегда 95px —
#      раскладка не дёргается); CSS .ws-bar-open: z-index 55 (над
#      sticky-шапкой сетки z2, под шапкой приложения z60, шторкой
#      итогов z75, нижним навом z100) + тень «парения», фон окон
#      уже непрозрачный.
# Правки по якорям (уникальность проверяется), каждая с меткой.
import sys, io

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
orig = src
edits = []

def edit(old, new, label):
    global src
    i = src.find(old)
    if i == -1:
        print('FAIL not found: ' + label); sys.exit(1)
    if src.find(old, i + 1) != -1:
        print('FAIL dup: ' + label); sys.exit(1)
    src = src[:i] + new + src[i + len(old):]
    edits.append(label)

# ============================================================
# ЧАСТЬ 1. ШАХМАТКА: фон ПУСТЫХ ячеек значений — #FFFFFF (светлая)
# ============================================================

# 1.1 базовое правило пустых ячеек светлой темы (Task 250 → 379)
edit("""    /* Task 250: светлая тема — сплошной фон пустых ячеек шахматки
       (раньше transparent, просвечивал фон страницы) */
    [data-theme="light"] .ws-grid tbody td.ws-cell {
        background: #eef0f2;
    }
    /* Task 314: светлая тема — «.»-ячейка = пустая (#eef0f2);
       правило выше специфичности базового, чтобы не зависеть от
       порядка с Task 250. Праздники — #f8e2e9 (правило feast ниже
       специфичнее, Task 363) */
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-dot-code {
        background: #eef0f2;
    }""",
     """    /* Task 250 → Task 379 (заявка: «переделай, фон пустых ячеек
       #FFFFFF — ячейки значений НЕ в шторке итогов, а в шахматке
       табеля»): сплошной фон ПУСТЫХ ячеек значений шахматки —
       ЧИСТЫЙ БЕЛЫЙ #FFFFFF (было #eef0f2). Тёмная тема не тронута
       (Task 319: #eef0f2 + brightness(0.88)); статусные ячейки
       перекрывают фон inline-цветом кода, праздники — #f8e2e9
       (Task 363), выходные — фон пустой + красная рамка-группа;
       подсветки «сегодня»/перекрестья — inset-заливки ПОВЕРХ фона,
       работают как прежде */
    [data-theme="light"] .ws-grid tbody td.ws-cell {
        background: #FFFFFF;
    }
    /* Task 314 → 379: светлая тема — «.»-ячейка = пустая
       (#FFFFFF); правило выше специфичности базового, чтобы не
       зависеть от порядка с Task 250/379. Праздники — #f8e2e9
       (правило feast ниже специфичнее, Task 363) */
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-dot-code {
        background: #FFFFFF;
    }""",
     '1.1 шахматка: пустые ячейки + «.»-ячейка светлой темы → #FFFFFF')

# 1.2 свотч «.» в попапе — предпросмотр ПУСТОЙ ячейки светлой темы
edit("""    [data-theme="light"] .ws-popup-swatch.ws-swatch-dot {
        background: #eef0f2;
    }""",
     """    [data-theme="light"] .ws-popup-swatch.ws-swatch-dot {
        /* Task 379: фон ПУСТОЙ ячейки светлой темы — #FFFFFF */
        background: #FFFFFF;
    }""",
     '1.2 свотч «.» светлой темы → #FFFFFF')

# 1.3 комментарий у базового правила «.»-ячейки — актуальные цвета
edit("""    /* Task 314: код «.» (плановый выходной) — ячейка выглядит как
       ПУСТАЯ: тот же фон (var(--bg-primary), светлая тема — #eef0f2,
       см. override ниже).""",
     """    /* Task 314: код «.» (плановый выходной) — ячейка выглядит как
       ПУСТАЯ: тот же фон (var(--bg-primary), светлая тема — #FFFFFF
       (Task 379), см. override ниже).""",
     '1.3 комментарий «.»-ячейки: светлая тема #FFFFFF')
edit("""       и маркер для тестов. Светлая тема: --bg-primary страницы
       #FAF9F5 — но фон ЯЧЕЕК сетки #eef0f2 (Task 250), совпадаем
       с ячейками, а не со страницей. */""",
     """       и маркер для тестов. Светлая тема: --bg-primary страницы
       #FAF9F5 — но фон ЯЧЕЕК сетки #FFFFFF (Task 250→379),
       совпадаем с ячейками, а не со страницей. */""",
     '1.4 комментарий «.»-ячейки: фон ячеек сетки #FFFFFF')

# ============================================================
# ЧАСТЬ 2. ОКНА «МЕРОПРИЯТИЯ»/«НОРМЫ» БАРА: раскрытие = ОВЕРЛЕЙ
# (бар НЕ увеличивается в размере)
# ============================================================

# 2.1 комментарий + переход height/margin-bottom СИНХРОННО + правило
#     .ws-bar-open (z-index 55 + тень) для обоих окон
edit("""       только когда текст НЕ влезает (или окно уже раскрыто) */
    .ws-events-panel {
        position: relative;          /* якорь значка .ws-bar-exp */
        transition: height 0.18s ease;
        scrollbar-width: none;       /* Firefox: полоса скрыта */
        -ms-overflow-style: none;    /* IE/legacy Edge */
    }
    .ws-cal-panel {
        position: relative;
        transition: height 0.18s ease;
        scrollbar-width: none;
        -ms-overflow-style: none;
    }""",
     """       только когда текст НЕ влезает (или окно уже раскрыто).
       Task 379 (заявка): раскрытое окно — ОВЕРЛЕЙ: низ смещается
       вниз ПОВЕРХ ряда 2/3 бара и шахматки, ГАБАРИТ БАРА НЕ
       РАСТЁТ — прирост высоты компенсируется отрицательным
       margin-bottom (95px − высота, ставит JS _barExp*): окно
       продолжает занимать в строке бара РОВНО 95px; height и
       margin-bottom анимируются СИНХРОННО — раскладка не
       дёргается ни на миг (сумма всегда 95px) */
    .ws-events-panel {
        position: relative;          /* якорь значка .ws-bar-exp */
        transition: height 0.18s ease, margin-bottom 0.18s ease;
        scrollbar-width: none;       /* Firefox: полоса скрыта */
        -ms-overflow-style: none;    /* IE/legacy Edge */
    }
    .ws-cal-panel {
        position: relative;
        transition: height 0.18s ease, margin-bottom 0.18s ease;
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    /* Task 379 (заявка: «при раскрытии должны смещаться вниз по
       верх бара, не увеличивая его в размере»): раскрытое окно —
       ОВЕРЛЕЙ над содержимым ниже бара: z-index 55 — поверх
       sticky-шапки сетки (z 2) и рядов бара, ПОД шапкой
       приложения (z 60), шторкой итогов (z 75), нижней навигацией
       (z 100); тень «парения» отделяет окно от накрытой
       шахматки. Фон окон непрозрачный (var(--bg-tertiary)) —
       текст читается поверх сетки */
    .ws-events-panel.ws-bar-open,
    .ws-cal-panel.ws-bar-open {
        z-index: 55;
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.38);
    }
    [data-theme="light"] .ws-events-panel.ws-bar-open,
    [data-theme="light"] .ws-cal-panel.ws-bar-open {
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
    }""",
     '2.1 окна бара: transition margin-bottom + .ws-bar-open оверлей (z55, тень)')

# 2.2 комментарий-шапка над _barExpSync — поведение Task 379
edit("""        // ws-bar-open на самом окне (переживает перерисовки), высота
        // пересчитывается под НОВЫЙ объём текста
        // ============================================================""",
     """        // ws-bar-open на самом окне (переживает перерисовки), высота
        // пересчитывается под НОВЫЙ объём текста.
        // Task 379 (заявка): при раскрытии окна смещаются вниз ПОВЕРХ
        // бара, НЕ увеличивая его в размере — прирост высоты
        // компенсируется отрицательным margin-bottom (95px −
        // scrollHeight): окно занимает в строке бара РОВНО 95px
        // (grid-строка/колонка не растёт, сетка под баром НЕ
        // уезжает); раскрытое окно — оверлей (CSS .ws-bar-open:
        // z-index 55 + тень) поверх ряда 2/3 бара и шахматки; height
        // и margin-bottom анимируются СИНХРОННО — сумма всегда 95px
        // ============================================================""",
     '2.2 комментарий JS: раскрытие = оверлей, габарит бара неизменен')

# 2.3 _barExpSync: margin-bottom при раскрытии/сворачивании
edit("""            if (open && !need) {
                // текст перестал переполняться (смена месяца/дня) —
                // свернуть, значок спрятать
                el.classList.remove('ws-bar-open');
                el.style.height = '';
                open = false;
            } else if (open) {
                // остаёмся раскрытыми — низ окна следует за НОВЫМ
                // объёмом текста (замер после перерисовки)
                el.style.height = el.scrollHeight + 'px';
            }""",
     """            if (open && !need) {
                // текст перестал переполняться (смена месяца/дня) —
                // свернуть, значок спрятать
                el.classList.remove('ws-bar-open');
                el.style.height = '';
                el.style.marginBottom = '';   // Task 379: габарит бара
                open = false;
            } else if (open) {
                // остаёмся раскрытыми — низ окна следует за НОВЫМ
                // объёмом текста (замер после перерисовки);
                // Task 379: отрицательный margin-bottom компенсирует
                // прирост высоты — ГАБАРИТ БАРА НЕ МЕНЯЕТСЯ, окно
                // уходит вниз ОВЕРЛЕЕМ поверх ряда 2/3 и шахматки
                el.style.height = el.scrollHeight + 'px';
                el.style.marginBottom = (95 - el.scrollHeight) + 'px';
            }""",
     '2.3 _barExpSync: margin-bottom 95−scrollHeight / сброс')

# 2.4 _barExpToggle: margin-bottom при раскрытии/сворачивании
edit("""        // Task 378: клик по значку — раскрыть/свернуть окно бара
        _barExpToggle: function(el) {
            if (!el) return;
            var open = el.classList.contains('ws-bar-open');
            if (open) {
                el.classList.remove('ws-bar-open');
                el.style.height = '';
            } else {
                el.classList.add('ws-bar-open');
                el.style.height = el.scrollHeight + 'px';
            }
            this._barExpSync(el);
        },""",
     """        // Task 378 → 379: клик по значку — раскрыть/свернуть окно
        // бара. Раскрытие: высота = scrollHeight (весь текст),
        // margin-bottom = 95 − высота (ОТРИЦАТЕЛЬНЫЙ) — низ окна
        // смещается вниз ПОВЕРХ бара оверлеем, а строка бара
        // сохраняет габарит 95px (бар НЕ увеличивается в размере,
        // сетка под ним не уезжает)
        _barExpToggle: function(el) {
            if (!el) return;
            var open = el.classList.contains('ws-bar-open');
            if (open) {
                el.classList.remove('ws-bar-open');
                el.style.height = '';
                el.style.marginBottom = '';
            } else {
                el.classList.add('ws-bar-open');
                el.style.height = el.scrollHeight + 'px';
                el.style.marginBottom = (95 - el.scrollHeight) + 'px';
            }
            this._barExpSync(el);
        },""",
     '2.4 _barExpToggle: margin-bottom 95−scrollHeight / сброс')

# ------------------------------------------------------------
io.open(PATH, 'w', encoding='utf-8', newline='').write(src)
print('OK %d правок: %s' % (len(edits), '; '.join(edits)))
print('index.html: %d → %d байт' % (len(orig), len(src)))
