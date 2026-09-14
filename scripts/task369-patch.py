#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# task369-patch.py — kip8test Task 369: заявка пользователя:
#   «В разделе КИП ИОС, сделай при свайпе кнопки "Проекты" (по такому же
#    принципу как на кнопках "Приборы" и "Клапана") открывался список
#    проектов сгруппированный по столбцу Статус проекта.»
# Изменения index.html (11 правок):
#   1. CSS: .project-swipe-cell / .project-swipe-bg (янтарно-коричневая
#      палитра кнопки #b08048, тёмная + светлая) + обнуление базового
#      отступа .dev-swipe-cell в отдельно стоящей строке «Проекты».
#   2. HTML: projectsEntryBtn обёрнут в свайп-ячейку #projectSwipeCell с
#      ДВУМЯ подложками «По статусу» (свайп в любую сторону — одна цель).
#   3. HTML: новая страница #page-projects-status («Проекты по статусу»):
#      поиск projectStatusSearchInput, инфо-бар, список projectStatusList.
#   4. JS: PROJECT_STATUS_ORDER + projectStatusGroupKey +
#      projectStatusSortKey (фиксированный порядок статусов, «(без
#      статуса)» в конце).
#   5. JS: projectInitSorted — ids для режима 'status' (ошибка загрузки).
#   6. JS: projectsRenderSorted — ids.status; isStatusMode: сортировка
#      по приоритету статуса → дата → наименование; группировка по
#      «Статусу проекта»; групп-сортировка по минимальной дате — только
#      для 'prod' (в 'status' порядок уже задан сортом элементов).
#   7. JS: projectsRenderGroup — фильтр по группе статуса (mode='status').
#   8. JS: projectsInitEntryButton — pointerdown-свайп (копия паттерна
#      «Клапана»), tap → projects-prod, свайп ←/→ → projects-status.
#   9. JS: navigateTo-хук для 'projects-status'.
#  10. JS: DESKTOP_MASTER_PAGES + PAGE_PARENTS + PAGE_LABELS.
#  11. JS: _KIP_IOS_PAGES + список активной вкладки «Документация».
# Тап по группе — прежняя страница project-group (год-подгруппы).
import io
import sys

PATH = 'index.html'
html = io.open(PATH, encoding='utf-8').read()
orig = html

def rep(old, new, n_expected, tag):
    global html
    n = html.count(old)
    if n != n_expected:
        print('ОШИБКА [%s]: фрагмент найден %d раз (ожидалось %d):' % (tag, n, n_expected))
        print('---')
        print(old[:200])
        sys.exit(1)
    html = html.replace(old, new)
    print('[ok] %s (%d зам.)' % (tag, n))

# ============ 1. CSS: свайп-ячейка и подложка «Проекты» ============
rep(
    """    /* Подложка для карточки «Клапана» — сине-зелёная (морская) палитра */
    .valve-swipe-bg {
        background: linear-gradient(135deg, rgba(31, 78, 80, 0.95), rgba(74, 138, 140, 0.85));
    }
    [data-theme="light"] .valve-swipe-bg {
        background: linear-gradient(135deg, rgba(40, 95, 97, 0.9), rgba(74, 138, 140, 0.8));
    }
""",
    """    /* Подложка для карточки «Клапана» — сине-зелёная (морская) палитра */
    .valve-swipe-bg {
        background: linear-gradient(135deg, rgba(31, 78, 80, 0.95), rgba(74, 138, 140, 0.85));
    }
    [data-theme="light"] .valve-swipe-bg {
        background: linear-gradient(135deg, rgba(40, 95, 97, 0.9), rgba(74, 138, 140, 0.8));
    }
    /* Task 369: карточка «Проекты» — свайп-ячейка + янтарно-коричневая
       подложка в цвет кнопки (#b08048). Свайп в любую сторону открывает
       «Проекты по статусу», тап — «По отделениям» (как раньше). */
    .project-swipe-cell > #projectsEntryBtn {
        position: relative;
        z-index: 1;
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        margin: 0;
        touch-action: pan-y;
    }
    .project-swipe-cell > #projectsEntryBtn.swipe-active {
        transition: none;
    }
    .project-swipe-bg {
        background: linear-gradient(135deg, rgba(146, 98, 44, 0.95), rgba(176, 128, 72, 0.85));
    }
    [data-theme="light"] .project-swipe-bg {
        background: linear-gradient(135deg, rgba(156, 108, 52, 0.9), rgba(176, 128, 72, 0.8));
    }
    /* Отдельно стоящая строка «Проекты»: базовый отступ .dev-swipe-cell
       (4px снизу) не нужен — зазор между строками задаёт margin-top
       соседних .menu-btn-row (6px), как было до обёртки в ячейку. */
    #page-kip-ios > .menu-btn-row .dev-swipe-cell {
        margin-bottom: 0;
    }
""",
    1, '1-CSS подложка Проекты')

# ============ 2. HTML: обернуть кнопку в свайп-ячейку ============
rep(
    """            <div class="menu-btn-row">
                <div class="menu-btn" id="projectsEntryBtn" style="border-color:rgba(176,128,72,0.35);"><div class="menu-btn-text"><div class="menu-btn-label" style="color:#b08048;">Проекты</div><div class="menu-btn-sublabel">По отделениям</div></div><button type="button" class="menu-btn-overflow" aria-label="Действия" onclick="event.stopPropagation(); openPinSheet('projects')"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg></button><i class="menu-btn-arrow" style="color:rgba(176,128,72,0.4);">›</i></div>
            </div>
""",
    """            <div class="menu-btn-row">
                <!-- Task 369: свайп-ячейка — как у «Приборы»/«Клапана»:
                     тап → по отделениям, свайп в любую сторону → по статусу. -->
                <div class="dev-swipe-cell project-swipe-cell" id="projectSwipeCell">
                    <div class="dev-swipe-bg dev-swipe-bg-left project-swipe-bg"><span>По статусу</span></div>
                    <div class="dev-swipe-bg dev-swipe-bg-right project-swipe-bg"><span>По статусу</span></div>
                    <div class="menu-btn" id="projectsEntryBtn" style="border-color:rgba(176,128,72,0.35);"><div class="menu-btn-text"><div class="menu-btn-label" style="color:#b08048;">Проекты</div><div class="menu-btn-sublabel">По отделениям</div></div><button type="button" class="menu-btn-overflow" aria-label="Действия" onclick="event.stopPropagation(); openPinSheet('projects')"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg></button><i class="menu-btn-arrow" style="color:rgba(176,128,72,0.4);">›</i></div>
                </div>
            </div>
""",
    1, '2-HTML свайп-ячейка кнопки')

# ============ 3. HTML: страница «Проекты по статусу» ============
rep(
    """            <div id="projectProdList"></div>
        </div>

        <!-- ======================== КАРТОЧКА ПРОЕКТА ======================== -->
""",
    """            <div id="projectProdList"></div>
        </div>

        <!-- ======================== ПРОЕКТЫ — ПО СТАТУСУ (Task 369) ========================
             Открывается свайпом кнопки «Проекты» на странице КИП ИОС (в любую
             сторону). Группы — по столбцу «Статус проекта» листа «Проекты»:
             «Новый» → «Выполнен» → «Остановлен» → «Отменен/Отменён» →
             неизвестные статусы по алфавиту → «(без статуса)». Тап по группе
             открывает страницу группы (project-group) с подгруппами по годам. -->
        <div id="page-projects-status" class="page-content">
            <div class="page-inline-header"><div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div><div class="page-inline-header-title">Проекты по статусу</div><input type="search" id="projectStatusSearchInput" class="dev-header-search" placeholder="Поиск…" autocomplete="off" enterkeyhint="search" oninput="projectsRenderSorted('status')" hidden><button type="button" id="projectStatusSearchInputToggleBtn" class="dev-search-toggle-btn" aria-label="Поиск" data-search-input="projectStatusSearchInput"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></button></div>
            <div id="projectStatusInfo" class="pb-info-bar" style="padding:6px 14px;font-size:11px;color:var(--text-secondary);border-bottom:1px solid var(--border-color);">Загрузка…</div>
            <div id="projectStatusList"></div>
        </div>

        <!-- ======================== КАРТОЧКА ПРОЕКТА ======================== -->
""",
    1, '3-HTML страница projects-status')

# ============ 4. JS: хелперы статусов ============
rep(
    """    function projectStatusClass(status) {
        const s = String(status || '').toLowerCase().trim();
        if (s === 'выполнен')   return 'project-card-status-done';
        if (s === 'новый')      return 'project-card-status-new';
        if (s === 'остановлен') return 'project-card-status-stopped';
        if (s === 'отменен' || s === 'отменён') return 'project-card-status-cancel';
        return '';
    }
""",
    """    function projectStatusClass(status) {
        const s = String(status || '').toLowerCase().trim();
        if (s === 'выполнен')   return 'project-card-status-done';
        if (s === 'новый')      return 'project-card-status-new';
        if (s === 'остановлен') return 'project-card-status-stopped';
        if (s === 'отменен' || s === 'отменён') return 'project-card-status-cancel';
        return '';
    }
    // Task 369: группировка проектов по столбцу «Статус проекта» (свайп
    // кнопки «Проекты» на странице КИП ИОС). Порядок известных статусов
    // фиксирован: активные («Новый») первыми, затем «Выполнен»,
    // «Остановлен», «Отменен/Отменён»; незнакомые статусы — по алфавиту
    // после известных; проекты с пустым статусом — в самом конце.
    const PROJECT_STATUS_ORDER = ['Новый', 'Выполнен', 'Остановлен', 'Отменен', 'Отменён'];
    function projectStatusGroupKey(status) {
        const s = String(status || '').trim();
        return s || '(без статуса)';
    }
    // Ключ сортировки группы статуса: '<приоритет>:<имя>'. Даёт
    // детерминированный порядок групп и при одинаковых приоритетах
    // (неизвестные статусы) — по алфавиту имён.
    function projectStatusSortKey(status) {
        const s = String(status || '').trim();
        if (!s) return '9:(без статуса)';
        const i = PROJECT_STATUS_ORDER.indexOf(s);
        return (i === -1 ? '5:' : '0' + i + ':') + s;
    }
""",
    1, '4-JS хелперы статусов')

# ============ 5. JS: projectInitSorted — ids режима status ============
rep(
    """                const ids = { prod: 'projectProdList' };
""",
    """                const ids = { prod: 'projectProdList', status: 'projectStatusList' }; // Task 369
""",
    1, '5-JS projectInitSorted ids')

# ============ 6а. JS: projectsRenderSorted — ids.status ============
rep(
    """    function projectsRenderSorted(mode) {
        const ids = {
            prod: { list: 'projectProdList', info: 'projectProdInfo', search: 'projectProdSearchInput', page: 'page-projects-prod' },
        };
""",
    """    function projectsRenderSorted(mode) {
        const ids = {
            prod: { list: 'projectProdList', info: 'projectProdInfo', search: 'projectProdSearchInput', page: 'page-projects-prod' },
            // Task 369: список проектов по статусам (свайп кнопки «Проекты»)
            status: { list: 'projectStatusList', info: 'projectStatusInfo', search: 'projectStatusSearchInput', page: 'page-projects-status' },
        };
""",
    1, '6а-JS ids.status')

# ============ 6б. JS: сортировка элементов — режим status ============
rep(
    """        // Сортировка: по «Отделению», внутри отделения — по «Дате утв.» (старые → новые).
        const sortKey = 'Отделение';
        filtered.sort((a, b) => {
            const va = (a[sortKey] || '').toString().toLowerCase();
            const vb = (b[sortKey] || '').toString().toLowerCase();
            if (va < vb) return -1;
            if (va > vb) return 1;
            // Внутри отделения — по дате утверждения (от старых к новым).
            const da = projectDateSortValue(a['Дата утв.']);
""",
    """        // Сортировка: по «Отделению», внутри отделения — по «Дате утв.» (старые → новые).
        // Task 369: режим 'status' — сначала по приоритету статуса
        // (PROJECT_STATUS_ORDER / projectStatusSortKey), внутри статуса —
        // та же «Дата утв.» от старых к новым.
        const isStatusMode = (mode === 'status');
        const sortKey = isStatusMode ? 'Статус проекта' : 'Отделение';
        filtered.sort((a, b) => {
            if (isStatusMode) {
                const ka = projectStatusSortKey(a['Статус проекта']);
                const kb = projectStatusSortKey(b['Статус проекта']);
                if (ka < kb) return -1;
                if (ka > kb) return 1;
            } else {
                const va = (a[sortKey] || '').toString().toLowerCase();
                const vb = (b[sortKey] || '').toString().toLowerCase();
                if (va < vb) return -1;
                if (va > vb) return 1;
            }
            // Внутри группы — по дате утверждения (от старых к новым).
            const da = projectDateSortValue(a['Дата утв.']);
""",
    1, '6б-JS сортировка элементов')

# ============ 6в. JS: накопление групп — статус ============
rep(
    """        // Группировка верхнего уровня — по «Отделению».
        const groups = {};
        const groupOrder = [];
        for (const d of filtered) {
            const g = d[sortKey] || '(без отделения)';
            if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
            groups[g].push(d);
        }
""",
    """        // Группировка верхнего уровня — по «Отделению».
        // Task 369: режим 'status' — по столбцу «Статус проекта»
        // (пустой статус → «(без статуса)»).
        const groups = {};
        const groupOrder = [];
        for (const d of filtered) {
            const g = isStatusMode ? projectStatusGroupKey(d['Статус проекта'])
                                   : (d[sortKey] || '(без отделения)');
            if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
            groups[g].push(d);
        }
""",
    1, '6в-JS накопление групп')

# ============ 6г. JS: групп-сортировка — только prod ============
rep(
    """        // Сортировка самих подгрупп (отделений) по «Дате утв.» —
        // подгруппа с самым старым проектом идёт первой; подгруппы, где все даты
        // пустые/невалидные ('00.00.00'), уходят в конец. При совпадении «минимальной»
        // даты добиваем по алфавиту (имя отделения).
        groupOrder.sort((a, b) => {
""",
    """        // Сортировка самих подгрупп (отделений) по «Дате утв.» —
        // подгруппа с самым старым проектом идёт первой; подгруппы, где все даты
        // пустые/невалидные ('00.00.00'), уходят в конец. При совпадении «минимальной»
        // даты добиваем по алфавиту (имя отделения).
        // Task 369: в режиме 'status' порядок групп уже задан сортировкой
        // элементов выше (приоритет статуса) — повторно не сортируем.
        if (!isStatusMode) {
        groupOrder.sort((a, b) => {
""",
    1, '6г-JS групп-сортировка (открытие)')

rep(
    """            if (minA < minB) return -1;
            if (minA > minB) return 1;
            const va = a.toString().toLowerCase();
            const vb = b.toString().toLowerCase();
            if (va < vb) return -1;
            if (va > vb) return 1;
            return 0;
        });
""",
    """            if (minA < minB) return -1;
            if (minA > minB) return 1;
            const va = a.toString().toLowerCase();
            const vb = b.toString().toLowerCase();
            if (va < vb) return -1;
            if (va > vb) return 1;
            return 0;
        });
        } // Task 369: конец if (!isStatusMode)
""",
    1, '6г-JS групп-сортировка (закрытие)')

# ============ 7. JS: projectsRenderGroup — фильтр по статусу ============
rep(
    """        // Фильтр по отделению (как было раньше).
        const sortKey = 'Отделение';
        let items = (projectData.projects || []).filter(d => {
            const g = d[sortKey] || '(без отделения)';
            return g === group;
        });
""",
    """        // Фильтр по отделению (как было раньше).
        // Task 369: режим 'status' — фильтр по группе статуса.
        const sortKey = 'Отделение';
        let items = (projectData.projects || []).filter(d => {
            if (mode === 'status') return projectStatusGroupKey(d['Статус проекта']) === group;
            const g = d[sortKey] || '(без отделения)';
            return g === group;
        });
""",
    1, '7-JS projectsRenderGroup фильтр')

# ============ 8. JS: свайп кнопки «Проекты» ============
rep(
    """    // ===== Кнопка Проекты на странице КИП И ОС =====
    function projectsInitEntryButton() {
        const btn = document.getElementById('projectsEntryBtn');
        if (!btn || btn.dataset.initialized) return;
        btn.dataset.initialized = '1';
        btn.addEventListener('click', function() {
            if (navigator.vibrate) navigator.vibrate(15);
            navigateTo('projects-prod');
        });
        // Обновить sublabel количеством проектов
        projectsUpdateEntrySublabel();
    }
""",
    """    // ===== Кнопка Проекты на странице КИП И ОС =====
    // Task 369: как у «Приборы»/«Клапана» — свайп-ячейка с подложками.
    // Отличие: альтернативная группировка одна («По статусу»), поэтому
    // свайп В ЛЮБУЮ сторону (влево или вправо) открывает её:
    //   tap → по отделениям (projects-prod, как раньше)
    //   swipe ← / swipe → → по статусам (projects-status, Task 369)
    const PROJECT_SWIPE_THRESHOLD = 12;    // px до определения направления
    const PROJECT_SWIPE_NAV_RATIO = 0.3;   // доля ширины для перехода
    let projectSwipeState = null;
    let projectSwipeMoved = false;

    function projectsInitEntryButton() {
        const btn = document.getElementById('projectsEntryBtn');
        if (!btn || btn.dataset.initialized) return;
        btn.dataset.initialized = '1';
        btn.addEventListener('pointerdown', onProjectSwipePointerDown);
        btn.addEventListener('click', function() {
            if (projectSwipeMoved) return;
            if (navigator.vibrate) navigator.vibrate(15);
            navigateTo('projects-prod');
        });
        // Обновить sublabel количеством проектов
        projectsUpdateEntrySublabel();
    }

    function onProjectSwipePointerDown(e) {
        if (e.button !== undefined && e.button !== 0) return;
        const el = e.currentTarget;
        const cell = document.getElementById('projectSwipeCell');
        if (!el || !cell) return;
        const rect = el.getBoundingClientRect();
        projectSwipeState = {
            el: el,
            cell: cell,
            startX: e.clientX,
            startY: e.clientY,
            width: rect.width,
            currentDx: 0,
            active: false,
            moved: false
        };
        window.addEventListener('pointermove', onProjectSwipePointerMove);
        window.addEventListener('pointerup', onProjectSwipePointerUp);
        window.addEventListener('pointercancel', onProjectSwipePointerUp);
    }

    function onProjectSwipePointerMove(e) {
        if (!projectSwipeState) return;
        const st = projectSwipeState;
        const dx = e.clientX - st.startX;
        const dy = e.clientY - st.startY;
        if (!st.active) {
            if (Math.abs(dx) > PROJECT_SWIPE_THRESHOLD || Math.abs(dy) > PROJECT_SWIPE_THRESHOLD) {
                if (Math.abs(dx) > Math.abs(dy) * 1.5) {
                    st.active = true;
                    st.el.classList.add('swipe-active');
                    st.el.style.pointerEvents = 'none';
                    if (navigator.vibrate) navigator.vibrate(10);
                } else {
                    // Вертикальное — скролл, отменяем
                    cleanupProjectSwipe();
                    return;
                }
            } else {
                return;
            }
        }
        e.preventDefault();
        let effectiveDx = dx;
        if (Math.abs(dx) > st.width) {
            const overshoot = Math.abs(dx) - st.width;
            effectiveDx = Math.sign(dx) * (st.width + overshoot * 0.3);
        }
        st.currentDx = effectiveDx;
        st.el.style.transform = 'translateX(' + effectiveDx + 'px)';
        st.cell.classList.toggle('swiping-left',  effectiveDx < 0);
        st.cell.classList.toggle('swiping-right', effectiveDx > 0);
    }

    function onProjectSwipePointerUp(e) {
        if (!projectSwipeState) return;
        const st = projectSwipeState;
        const threshold = st.width * PROJECT_SWIPE_NAV_RATIO;
        const shouldNav = st.active && Math.abs(st.currentDx) > threshold;

        if (shouldNav) {
            if (navigator.vibrate) navigator.vibrate(20);
            st.el.classList.remove('swipe-active');
            st.el.style.transition = 'transform 0.2s ease-out, opacity 0.2s ease-out';
            // Оба направления — одна цель: «По статусу» (единственная
            // альтернативная группировка проектов, Task 369).
            st.el.style.transform = 'translateX(' + (st.currentDx < 0 ? '-100%' : '100%') + ')';
            st.el.style.opacity = '0';
            const targetPage = 'projects-status';
            setTimeout(function() {
                navigateTo(targetPage);
                setTimeout(function() {
                    st.el.style.transition = '';
                    st.el.style.opacity = '';
                    st.el.style.transform = '';
                    st.el.style.pointerEvents = '';
                    st.cell.classList.remove('swiping-left', 'swiping-right');
                }, 100);
            }, 200);
            projectSwipeState = null;
            window.removeEventListener('pointermove', onProjectSwipePointerMove);
            window.removeEventListener('pointerup', onProjectSwipePointerUp);
            window.removeEventListener('pointercancel', onProjectSwipePointerUp);
        } else {
            // Возвращаем карточку на место (с анимацией)
            st.el.classList.remove('swipe-active');
            st.el.style.transform = '';
            st.el.style.pointerEvents = '';
            st.cell.classList.remove('swiping-left', 'swiping-right');
            st.moved = st.active;
            cleanupProjectSwipe();
        }
    }

    function cleanupProjectSwipe() {
        if (!projectSwipeState) return;
        const st = projectSwipeState;
        st.el.classList.remove('swipe-active');
        st.el.style.pointerEvents = '';
        st.el.style.transform = '';
        if (st.cell) {
            st.cell.classList.remove('swiping-left', 'swiping-right');
        }
        // Если был активный свайп — блокируем следующий click
        if (st.active) {
            projectSwipeMoved = true;
            setTimeout(function() { projectSwipeMoved = false; }, 300);
        }
        projectSwipeState = null;
        window.removeEventListener('pointermove', onProjectSwipePointerMove);
        window.removeEventListener('pointerup', onProjectSwipePointerUp);
        window.removeEventListener('pointercancel', onProjectSwipePointerUp);
    }
""",
    1, '8-JS свайп кнопки Проекты')

# ============ 9. JS: navigateTo-хук ============
rep(
    """        if (page === 'projects-prod') { setTimeout(() => { if (typeof projectInitSorted === 'function') projectInitSorted('prod'); }, 30); }
""",
    """        if (page === 'projects-prod') { setTimeout(() => { if (typeof projectInitSorted === 'function') projectInitSorted('prod'); }, 30); }
        if (page === 'projects-status') { setTimeout(() => { if (typeof projectInitSorted === 'function') projectInitSorted('status'); }, 30); } // Task 369
""",
    1, '9-JS navigateTo-хук')

# ============ 10а. JS: DESKTOP_MASTER_PAGES ============
rep(
    """        'regulators-prod', 'regulator-group',
        'projects-prod', 'project-group',
        'cable-journal-edit',
        'tickets-1000v', 'tickets-4', 'tickets-5', 'tickets-6',
""",
    """        'regulators-prod', 'regulator-group',
        'projects-prod', 'projects-status', 'project-group', // Task 369
        'cable-journal-edit',
        'tickets-1000v', 'tickets-4', 'tickets-5', 'tickets-6',
""",
    1, '10а-JS DESKTOP_MASTER_PAGES')

# ============ 10б. JS: PAGE_PARENTS ============
rep(
    """        'projects-prod':    'kip-ios',
        'project-detail':   'projects-prod',
""",
    """        'projects-prod':    'kip-ios',
        'projects-status':  'kip-ios',   // Task 369: свайп кнопки «Проекты»
        'project-detail':   'projects-prod',
""",
    1, '10б-JS PAGE_PARENTS')

# ============ 10в. JS: PAGE_LABELS ============
rep(
    """        'projects-prod':    'Проекты',
        'project-detail':   'Проект',
""",
    """        'projects-prod':    'Проекты',
        'projects-status':  'Проекты по статусу',   // Task 369
        'project-detail':   'Проект',
""",
    1, '10в-JS PAGE_LABELS')

# ============ 11а. JS: _KIP_IOS_PAGES ============
rep(
    """                         'projects-prod', 'project-detail', 'project-group',
""",
    """                         'projects-prod', 'projects-status', 'project-detail', 'project-group', // Task 369
""",
    1, '11а-JS _KIP_IOS_PAGES')

# ============ 11б. JS: активная вкладка «Документация» ============
rep(
    """                    'regulators-prod', 'regulator-detail', 'regulator-group',
                    'projects-prod', 'project-detail', 'project-group',
                    'cable-journal-edit', 'cable-journal-add', 'cable-journal-view',
""",
    """                    'regulators-prod', 'regulator-detail', 'regulator-group',
                    'projects-prod', 'projects-status', 'project-detail', 'project-group', // Task 369
                    'cable-journal-edit', 'cable-journal-add', 'cable-journal-view',
""",
    1, '11б-JS вкладка Документация')

# ============ Контроль ============
assert html != orig, 'изменений нет'
assert html.count('projectStatusSortKey') >= 3, 'projectStatusSortKey должен встречаться (определение + сортировка + тесты не в HTML)'
assert "id=\"page-projects-status\"" in html
assert "id=\"projectSwipeCell\"" in html
io.open(PATH, 'w', encoding='utf-8').write(html)
print('OK — Task 369 применён (%d символов добавлено)' % (len(html) - len(orig)))
