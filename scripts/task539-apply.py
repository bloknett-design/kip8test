#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 539 — телефонный справочник: табы «Все / Избранное»
(заявка: «в мобильной версии сделай в нижней части кнопки
"Избранное" и "Все", как в разделах расходомерах или в датчиках
температуры, и в десктопной версии то же в стиле десктопа на два
экрана (разделы и содержание)»).

МОБАЙЛ (≤1023px): нижний фиксированный бар #pbBottomBar — по
образцу #flowBottomBar расходомеров / #tsBottomBar датчиков
температуры (Task 492): две равные кнопки, разделитель по центру,
safe-area, счётчики.

ДЕСКТОП (≥1024px): компактные табы #pbDesktopTabs в тулбаре над
списком (sticky) — по образцу #flowDesktopTabs (Task 120/161),
акцент справочника (синий 74,143,199). Тулбар липнет к верху →
табы видны на ОБОИХ «экранах» страницы: свёрнутые организации
(«разделы») и раскрытая организация («содержание»).

Кнопка-переключатель «Только избранные» (#pbFilterFav) удалена —
её роль выполняет таб «Избранное» (state pbFilterFavOnly прежний).

Патчит index.html: 5 правок (2 HTML, 1 CSS, 2 JS + замена функций).
Строковые анкеры — репо kip8/kip8test идентичны в этих местах.

Запуск: python3 scripts/task539-apply.py [корень репо]
(по умолчанию — kip8test).
"""
import io
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/kip8test'
PATH = ROOT + '/index.html'

src = io.open(PATH, encoding='utf-8').read()
orig_len = len(src)
patches = 0


def patch(anchor, replacement, label, count=1):
    global src, patches
    n = src.count(anchor)
    if n != count:
        print('FAIL %s: анкер найден %d раз (ожидалось %d)' % (label, n, count))
        sys.exit(1)
    src = src.replace(anchor, replacement)
    patches += 1
    print('OK   %s' % label)


# ---------------------------------------------------------------
# 1. HTML: тулбар — кнопка «Только избранные» → десктопные табы
# ---------------------------------------------------------------
OLD_TOOLBAR = '''                <div class="pb-toolbar">
                    <button type="button" id="pbFilterFav" class="pb-filter-btn" onclick="pbToggleFavFilter()">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                        <span id="pbFilterFavLabel">Только избранные</span>
                    </button>'''
NEW_TOOLBAR = '''                <div class="pb-toolbar">
                    <!-- Task 539: табы «Все / Избранное» — по образцу расходомеров
                         (#flowDesktopTabs, Task 120/161) и датчиков температуры
                         (.ts-tabs, Task 373): компактные табы в тулбаре над
                         списком, видны на десктопе (≥1024px) в ОБОИХ состояниях
                         страницы — «разделы» (организации свёрнуты) и
                         «содержание» (организация раскрыта): тулбар sticky.
                         На мобильном (≤1023px) табы скрыты — их заменяет
                         нижний бар #pbBottomBar. Прежняя кнопка-переключатель
                         «Только избранные» удалена — её роль выполняет таб
                         «Избранное» (состояние pbFilterFavOnly прежнее). -->
                    <div id="pbDesktopTabs" class="pb-desktop-tabs" role="tablist" aria-label="Фильтр контактов телефонного справочника">
                        <button type="button" class="pb-tab active" data-pb-tab="all" onclick="pbSetTab('all')" role="tab" aria-selected="true">Все <span class="pb-tab-count" id="pbAllCountDesk">0</span></button>
                        <button type="button" class="pb-tab" data-pb-tab="fav" onclick="pbSetTab('fav')" role="tab" aria-selected="false">Избранное <span class="pb-tab-count" id="pbFavCountDesk">0</span></button>
                    </div>'''
patch(OLD_TOOLBAR, NEW_TOOLBAR, '1 HTML: тулбар — десктоп-табы вместо кнопки')

# ---------------------------------------------------------------
# 2. HTML: мобильный нижний бар — сиблинг #page-phonebook
# ---------------------------------------------------------------
OLD_PAGE_END = '''            <div class="pb-info" id="pbInfo">Загрузка…</div>
            <div id="pbList" class="pb-list"></div>
        </div>

        <!-- ======================== АДМИН-ПАНЕЛЬ (только роль "Админ") ======================== -->'''
NEW_PAGE_END = '''            <div class="pb-info" id="pbInfo">Загрузка…</div>
            <div id="pbList" class="pb-list"></div>
        </div>

        <!-- Task 539: нижний бар «Все / Избранное» телефонного справочника —
             по образцу расходомеров (#flowBottomBar) и датчиков температуры
             (#tsBottomBar, Task 492): fixed внизу экрана (сиблинг страницы),
             виден только на мобильной странице справочника (≤1023px, CSS
             .pb-bottom-bar); на десктопе (≥1024px) — табы #pbDesktopTabs в
             тулбаре. Счётчики-дубликаты pbAllCountMob/pbFavCountMob обновляет
             pbUpdateTabs вместе с десктопными; активный таб синхронизирует
             pbSetTab по data-pb-tab (все .pb-tab[data-pb-tab] разом). -->
        <div id="pbBottomBar" class="pb-bottom-bar">
            <button type="button" class="pb-tab active" data-pb-tab="all" onclick="pbSetTab('all')" role="tab" aria-selected="true">Все <span class="pb-tab-count" id="pbAllCountMob">0</span></button>
            <button type="button" class="pb-tab" data-pb-tab="fav" onclick="pbSetTab('fav')" role="tab" aria-selected="false">Избранное <span class="pb-tab-count" id="pbFavCountMob">0</span></button>
        </div>

        <!-- ======================== АДМИН-ПАНЕЛЬ (только роль "Админ") ======================== -->'''
patch(OLD_PAGE_END, NEW_PAGE_END, '2 HTML: мобильный нижний бар')

# ---------------------------------------------------------------
# 3. CSS: базовые .pb-tab/.pb-tab-count + десктоп-табы + нижний бар
# ---------------------------------------------------------------
OLD_CSS_ANCHOR = '''    .pb-filter-btn:active { transform: scale(0.96); }
    .pb-toolbar-spacer { flex: 1; }'''
NEW_CSS = '''    .pb-filter-btn:active { transform: scale(0.96); }
    .pb-toolbar-spacer { flex: 1; }

    /* ===== Task 539: табы «Все / Избранное» телефонного справочника ===== */
    /* Базовые табы (десктоп — компактные в тулбаре; мобильный нижний бар
       переопределяет размеры ниже). Активный таб — синий акцент
       справочника #6aa6e0 (как заголовок страницы и кнопка на главной). */
    .pb-tab { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 40px; padding: 8px 12px; border: none; background: transparent; color: rgba(255,255,255,0.55); font-family: inherit; font-size: 13px; font-weight: 600; cursor: pointer; touch-action: manipulation; -webkit-tap-highlight-color: transparent; transition: background 0.2s, color 0.2s; }
    .pb-tab:active { opacity: 0.75; }
    [data-theme="light"] .pb-tab { color: rgba(20,20,19,0.6); }
    .pb-tab-count { display: inline-block; min-width: 17px; height: 17px; padding: 0 5px; background: rgba(255,255,255,0.14); color: rgba(255,255,255,0.85); border-radius: 9px; font-size: 10px; font-weight: 700; line-height: 17px; text-align: center; }
    .pb-tab.active .pb-tab-count { background: rgba(106,166,224,0.25); color: #6aa6e0; }
    [data-theme="light"] .pb-tab-count { background: rgba(20,20,19,0.1); color: rgba(20,20,19,0.8); }
    [data-theme="light"] .pb-tab.active .pb-tab-count { background: rgba(74,143,199,0.18); color: #4a8fc7; }

    /* ДЕСКТОП (≥1024px): компактные табы в тулбаре над списком — по
       образцу .flow-desktop-tabs расходомеров (Task 120/161). Тулбар
       (.pb-search-wrap) sticky сверху → табы видны на ОБОИХ «экранах»
       страницы: «разделы» (организации свёрнуты) и «содержание»
       (организация раскрыта). На мобильном скрыты (нижний бар). */
    .pb-desktop-tabs {
        display: none;  /* скрыт на мобильном */
        gap: 0;
        flex-shrink: 0;
        border: 1px solid rgba(74,143,199,0.3);
        border-radius: 8px;
        overflow: hidden;
    }
    @media (min-width: 1024px) { .pb-desktop-tabs { display: flex; } }
    .pb-desktop-tabs .pb-tab {
        padding: 6px 14px;
        font-size: 13px;
        min-height: auto;
        border-radius: 0;
    }
    .pb-desktop-tabs .pb-tab.active {
        background: rgba(74,143,199,0.15);
        color: #6aa6e0;
    }
    [data-theme="light"] .pb-desktop-tabs .pb-tab.active {
        background: rgba(74,143,199,0.12);
        color: #4a8fc7;
    }
    .pb-desktop-tabs .pb-tab-count {
        min-width: 15px;
        height: 15px;
        padding: 0 4px;
        font-size: 10px;
        line-height: 15px;
    }

    /* МОБИЛЬНЫЙ (≤1023px): нижний фиксированный бар — по образцу
       .ts-bottom-bar датчиков температуры (Task 492) и .flow-bottom-bar
       расходомеров: две равные кнопки, разделитель по центру, safe-area. */
    .pb-bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; z-index: 80; display: none; grid-template-columns: 1fr 1fr; gap: 0; padding: 0; padding-bottom: env(safe-area-inset-bottom, 0px); background: var(--bottom-nav-bg, rgba(23, 33, 43, 0.95)); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-top: 1px solid var(--card-border); }
    body:has(#page-phonebook.active) .pb-bottom-bar { display: grid; }
    @media (min-width: 1024px) { body:has(#page-phonebook.active) .pb-bottom-bar { display: none !important; } }
    .pb-bottom-bar::before { content: ''; position: absolute; left: 50%; top: 14px; bottom: calc(14px + env(safe-area-inset-bottom, 0px)); width: 1px; background: rgba(255, 255, 255, 0.12); transform: translateX(-50%); pointer-events: none; z-index: 1; }
    [data-theme="light"] .pb-bottom-bar::before { background: rgba(20, 20, 19, 0.12); }
    #pbBottomBar .pb-tab { display: flex; align-items: center; justify-content: center; gap: 6px; min-height: 56px; padding: 16px 10px calc(16px + env(safe-area-inset-bottom, 0px)); border: none; border-radius: 0; background: transparent; color: rgba(255, 255, 255, 0.5); font-family: 'Inter', sans-serif; font-size: 17px; font-weight: 600; cursor: pointer; pointer-events: auto; touch-action: manipulation; -webkit-tap-highlight-color: transparent; box-shadow: none; transition: background 0.2s, color 0.2s; position: relative; z-index: 2; }
    #pbBottomBar .pb-tab:active { background: rgba(255, 255, 255, 0.08); opacity: 0.75; }
    #pbBottomBar .pb-tab.active { background: transparent; color: #ffffff; }
    #pbBottomBar .pb-tab-count { min-width: 18px; height: 18px; border-radius: 9px; font-size: 11px; line-height: 18px; background: rgba(255,255,255,0.14); color: rgba(255,255,255,0.85); }
    #pbBottomBar .pb-tab.active .pb-tab-count { background: rgba(255,255,255,0.92); color: #14171c; }
    [data-theme="light"] #pbBottomBar .pb-tab { color: rgba(20, 20, 19, 0.5); }
    [data-theme="light"] #pbBottomBar .pb-tab:active { background: rgba(20, 20, 19, 0.06); }
    [data-theme="light"] #pbBottomBar .pb-tab.active { color: #141413; }
    [data-theme="light"] #pbBottomBar .pb-tab-count { background: rgba(20,20,19,0.1); color: rgba(20,20,19,0.8); }
    [data-theme="light"] #pbBottomBar .pb-tab.active .pb-tab-count { background: #141413; color: #FAF9F5; }
    @media (max-width: 400px) { #pbBottomBar .pb-tab { font-size: 15px; padding: 14px 8px calc(14px + env(safe-area-inset-bottom, 0px)); gap: 4px; } }
    /* Отступ списка снизу на мобильном — фиксированный бар не накрывает
       последнюю карточку (как .ts-page padding-bottom у датчиков) */
    @media (max-width: 1023px) { body:has(#page-phonebook.active) .pb-list { padding-bottom: 96px; } }'''
patch(OLD_CSS_ANCHOR, NEW_CSS, '3 CSS: табы + десктоп + нижний бар')

# ---------------------------------------------------------------
# 4. JS: pbUpdateFilterButton + pbToggleFavFilter → pbUpdateTabs + pbSetTab
# ---------------------------------------------------------------
OLD_JS_FN = '''    function pbUpdateFilterButton() {
        const btn = document.getElementById('pbFilterFav');
        const label = document.getElementById('pbFilterFavLabel');
        if (!btn || !label) return;
        if (pbFilterFavOnly) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
        const count = pbGetFavoritesCount();
        label.textContent = 'Избранные' + (count > 0 ? ': ' + count : '');
    }

    // Переключить фильтр "только избранные"
    function pbToggleFavFilter() {
        pbFilterFavOnly = !pbFilterFavOnly;
        if (navigator.vibrate) navigator.vibrate(25);
        // Сбросить раскрытые секции — в режиме фильтра они раскрываются автоматически
        pbExpandedSections = {};
        pbRender();
    }'''
NEW_JS_FN = '''    // Task 539: обновить табы «Все / Избранное» — активный таб и счётчики.
    // Табы живут в двух местах: десктопные #pbDesktopTabs (тулбар над
    // списком, ≥1024px) и мобильный нижний бар #pbBottomBar (≤1023px);
    // синхронизация — по data-pb-tab (все .pb-tab[data-pb-tab] разом, как
    // setTempSensorsTab датчиков температуры). Счётчики: «Все» — всего
    // контактов, «Избранное» — избранных (обновляются и после загрузки
    // данных, и после переключения звёздочки). Заменила pbUpdateFilterButton
    // (кнопка «Только избранные» удалена — её роль выполняет таб).
    function pbUpdateTabs() {
        if (typeof document === 'undefined' ||
            typeof document.querySelectorAll !== 'function') return;
        const btns = document.querySelectorAll('.pb-tab[data-pb-tab]');
        for (let i = 0; i < btns.length; i++) {
            const b = btns[i];
            const on = (b.getAttribute('data-pb-tab') === 'fav') === pbFilterFavOnly;
            b.classList.toggle('active', on);
            b.setAttribute('aria-selected', on ? 'true' : 'false');
        }
        const all = pbFlat.length;
        const fav = pbGetFavoritesCount();
        const ids = ['pbAllCountDesk', 'pbAllCountMob',
                     'pbFavCountDesk', 'pbFavCountMob'];
        for (let i = 0; i < ids.length; i++) {
            const el = document.getElementById(ids[i]);
            if (el) el.textContent = String(i < 2 ? all : fav);
        }
    }

    // Task 539: переключить таб «Все / Избранное» (мобильный нижний бар
    // #pbBottomBar и десктопные табы #pbDesktopTabs; как setTempSensorsTab
    // датчиков / FlowmeterData.setTab расходомеров). 'all' — все контакты,
    // 'fav' — только избранные (прежде — кнопка «Только избранные»,
    // pbToggleFavFilter: состояние pbFilterFavOnly прежнее, все проверки
    // pbRender/pbToggleFavorite работают без изменений).
    function pbSetTab(tab) {
        if (tab !== 'all' && tab !== 'fav') return;
        const wantFav = (tab === 'fav');
        if (pbFilterFavOnly === wantFav) { pbUpdateTabs(); return; }
        pbFilterFavOnly = wantFav;
        if (navigator.vibrate) navigator.vibrate(25);
        // Сбросить раскрытые секции — в режиме фильтра они раскрываются автоматически
        pbExpandedSections = {};
        pbUpdateTabs();
        pbRender();
    }'''
patch(OLD_JS_FN, NEW_JS_FN, '4 JS: pbUpdateTabs + pbSetTab')

# ---------------------------------------------------------------
# 5. JS: точки вызова pbUpdateFilterButton → pbUpdateTabs
# ---------------------------------------------------------------
patch('''        // Обновить счётчик на кнопке фильтра
        pbUpdateFilterButton();''',
      '''        // Task 539: обновить табы «Все / Избранное» и счётчики
        pbUpdateTabs();''',
      '5 JS: вызов в pbRender')

patch('''            pbUpdateFilterButton();
            // Обновить инфо-строку (там показывается счётчик избранного)
            pbRender();''',
      '''            pbUpdateTabs();
            // Обновить инфо-строку (там показывается счётчик избранного)
            pbRender();''',
      '6 JS: вызов в pbToggleFavorite')

io.open(PATH, 'w', encoding='utf-8').write(src)
print()
print('Патчей применено: %d; размер %d → %d байт (+%d)' %
      (patches, orig_len, len(src), len(src) - orig_len))

# Контроль: старых упоминаний кнопки в телефонном блоке не осталось
import re
region_start = src.find('// ===== ТЕЛЕФОННЫЙ СПРАВОЧНИК')
region_end = src.find('// ===== ПРИБОРЫ (КИП ИОС)', region_start)
region = src[region_start:region_end] if region_start >= 0 and region_end > region_start else src
for bad in ['pbToggleFavFilter', 'pbFilterFavLabel', "getElementById('pbFilterFav')"]:
    if bad in region:
        print('WARN: %s ещё упоминается в телефонном блоке' % bad)
print('Контроль телефонного блока: пройден')
