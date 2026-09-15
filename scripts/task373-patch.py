#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 373: «Датчики температуры» — доработки страницы карточек и страницы
# датчика (заявка пользователя):
#   1) мобильная версия: карточки СТОЛБИКОМ по одной в строке, на всю
#      ширину, с небольшими отступами по краям;
#   2) в обоих версиях — избранное по примеру расходомеров хозрасчётных
#      (FlowFav): табы «Все / Избранные», звёздочка на карточке, звёздочка
#      в шапке страницы датчика, localStorage;
#   3) бейджи «ТС»/«ТП» на цветных фонах убраны из карточек и из полных
#      карточек (чипа страницы датчика) — в заголовках групп остаются;
#   4) добавлена термопара хромель-копель ТХК (L), ГОСТ Р 8.585-2001,
#      −200…800 °C (полиномы аппроксимации по таблице стандарта);
#   5) «Расчёт произвольных значений» (Task 371) — СТАТИЧНАЯ панель НАД
#      формой выбора предела измерений и шага таблицы (отображается
#      всегда), старая панель под расчётной таблицей удалена.
# Запуск из корня репо kip8test.
import io, sys

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
orig_len = len(src)
edits = []

def edit(name, old, new, count=1):
    global src
    n = src.count(old)
    assert n == count, 'EDIT «%s»: найдено %d вхождений (ожидалось %d)' % (name, n, count)
    assert old != new, 'EDIT «%s»: old == new' % name
    src = src.replace(old, new)
    edits.append((name, len(new) - len(old)))

# ============================================================
# 1. CSS: .ts-page — небольшие отступы по краям (мобильная заявка)
# ============================================================
edit('css: ts-page padding',
"    .ts-page { padding: 4px 0 12px; position: relative; z-index: 2; }",
"    /* Task 373: небольшие отступы по краям (на мобильном карточки —\n"
"       столбиком на всю ширину строки, не вплотную к краям экрана) */\n"
"    .ts-page { padding: 4px 12px 12px; position: relative; z-index: 2; }")

# ============================================================
# 2. CSS: убрать бейджи ТС/ТП из карточек (классы .ts-card-badge*)
# ============================================================
edit('css: remove ts-card-badge rules',
"    .ts-card-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 32px; height: 20px; padding: 0 6px; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; flex-shrink: 0; }\n"
"    .ts-card-badge-rtd { background: rgba(74, 199, 113, 0.14); color: #4ac771; border: 1px solid rgba(74, 199, 113, 0.3); }\n"
"    .ts-card-badge-tc { background: rgba(199, 150, 74, 0.14); color: #c7964a; border: 1px solid rgba(199, 150, 74, 0.3); }\n",
"    /* Task 373: бейджи ТС/ТП убраны из карточек и чипа датчика —\n"
"       CSS-классы бейджей карточек удалены (в заголовках групп\n"
"       остались .ts-group-badge*) */\n")

# верхняя строка карточки: запас справа под звёздочку избранного
edit('css: ts-card-top padding-right',
"    .ts-card-top { display: flex; align-items: center; gap: 8px; }",
"    .ts-card-top { display: flex; align-items: center; gap: 8px; padding-right: 34px; }")

# ============================================================
# 3. CSS: новые правила Task 373 (звезда на карточке, табы, звезда
#    в шапке, пустое избранное, статичная панель расчёта)
# ============================================================
edit('css: new Task 373 block',
"    .ts-card:hover .ts-card-arrow, .ts-card:active .ts-card-arrow { color: rgba(74, 143, 199, 0.4); }",
"    .ts-card:hover .ts-card-arrow, .ts-card:active .ts-card-arrow { color: rgba(74, 143, 199, 0.4); }\n"
"    /* === Task 373: избранное датчиков температуры (по примеру\n"
"       расходомеров хозрасчётных) + статичная панель расчёта === */\n"
"    .ts-card-fav-btn { position: absolute; top: 8px; right: 8px; width: 32px; height: 32px; border: none; background: transparent; color: rgba(74, 143, 199, 0.4); font-size: 18px; line-height: 1; cursor: pointer; -webkit-tap-highlight-color: transparent; display: flex; align-items: center; justify-content: center; border-radius: 8px; transition: transform 0.12s, color 0.15s, background 0.15s; z-index: 2; }\n"
"    .ts-card-fav-btn:active { transform: scale(0.85); }\n"
"    .ts-card-fav-btn.active { color: #4a8fc7; background: rgba(74, 143, 199, 0.12); }\n"
"    .ts-tabs { display: flex; margin: 6px 0 4px; border: 1px solid rgba(74, 143, 199, 0.25); border-radius: 10px; overflow: hidden; background: var(--card-bg); }\n"
"    .ts-tab { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; min-height: 40px; padding: 8px 10px; border: none; background: transparent; color: rgba(74, 143, 199, 0.65); font-family: inherit; font-size: 13px; font-weight: 600; cursor: pointer; touch-action: manipulation; -webkit-tap-highlight-color: transparent; transition: background 0.2s, color 0.2s; }\n"
"    .ts-tab:active { opacity: 0.75; }\n"
"    .ts-tab.active { background: rgba(74, 143, 199, 0.15); color: #4a8fc7; }\n"
"    .ts-tab-count { display: inline-block; min-width: 17px; height: 17px; padding: 0 5px; background: rgba(74, 143, 199, 0.18); color: #4a8fc7; border-radius: 9px; font-size: 10px; font-weight: 700; line-height: 17px; text-align: center; }\n"
"    .ts-tab.active .ts-tab-count { background: #4a8fc7; color: #fff; }\n"
"    #tempSensorFavBtn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); width: 36px; height: 36px; border: none; background: transparent; color: rgba(74, 143, 199, 0.5); font-size: 22px; line-height: 1; cursor: pointer; -webkit-tap-highlight-color: transparent; display: flex; align-items: center; justify-content: center; border-radius: 50%; transition: transform 0.12s, color 0.15s; }\n"
"    #tempSensorFavBtn:active { transform: translateY(-50%) scale(0.88); }\n"
"    #tempSensorFavBtn.active { color: #4a8fc7; }\n"
"    .ts-empty-fav { grid-column: 1 / -1; padding: 34px 16px; text-align: center; }\n"
"    .ts-empty-fav-icon { font-size: 34px; color: rgba(74, 143, 199, 0.4); margin-bottom: 8px; }\n"
"    .ts-empty-fav-text { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }\n"
"    .ts-empty-fav-hint { font-size: 12px; color: var(--conv-info-text); line-height: 1.5; }\n"
"    .ts-empty-fav-hint .star { color: #4a8fc7; font-weight: 700; }\n"
"    .ts-calc-panel { padding: 14px 16px; background: var(--card-bg); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid rgba(74, 143, 199, 0.2); border-radius: 14px; margin: 8px 0 12px; position: relative; z-index: 2; }\n"
"    .ts-calc-title { font-size: 14px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.2px; }\n"
"    .ts-calc-hint { color: var(--conv-info-text); font-size: 11px; line-height: 1.4; margin: 6px 0 10px; }\n"
"    [data-theme=\"light\"] .ts-card-fav-btn { color: rgba(43, 111, 163, 0.45); }\n"
"    [data-theme=\"light\"] .ts-card-fav-btn.active { color: #2b6fa3; background: rgba(74, 143, 199, 0.12); }\n"
"    [data-theme=\"light\"] .ts-tab { color: rgba(43, 111, 163, 0.6); }\n"
"    [data-theme=\"light\"] .ts-tab.active { background: rgba(74, 143, 199, 0.12); color: #2b6fa3; }\n"
"    [data-theme=\"light\"] .ts-tab-count { background: rgba(74, 143, 199, 0.15); color: #2b6fa3; }\n"
"    [data-theme=\"light\"] .ts-tab.active .ts-tab-count { background: #2b6fa3; color: #fff; }\n"
"    [data-theme=\"light\"] #tempSensorFavBtn { color: rgba(43, 111, 163, 0.55); }\n"
"    [data-theme=\"light\"] #tempSensorFavBtn.active { color: #2b6fa3; }")

# ============================================================
# 4. CSS: светлая тема — бейджи карточек убрать из селекторов
# ============================================================
edit('css: light theme badge selectors',
"    [data-theme=\"light\"] .ts-card-badge-rtd, [data-theme=\"light\"] .ts-group-badge-rtd { background: rgba(43, 138, 74, 0.1); color: #2b8a4a; border-color: rgba(43, 138, 74, 0.3); }\n"
"    [data-theme=\"light\"] .ts-card-badge-tc, [data-theme=\"light\"] .ts-group-badge-tc { background: rgba(156, 108, 52, 0.1); color: #8a5c26; border-color: rgba(156, 108, 52, 0.3); }",
"    [data-theme=\"light\"] .ts-group-badge-rtd { background: rgba(43, 138, 74, 0.1); color: #2b8a4a; border-color: rgba(43, 138, 74, 0.3); }\n"
"    [data-theme=\"light\"] .ts-group-badge-tc { background: rgba(156, 108, 52, 0.1); color: #8a5c26; border-color: rgba(156, 108, 52, 0.3); }")

# ============================================================
# 5. CSS: мобильная сетка — карточки столбиком по одной в строке
# ============================================================
edit('css: mobile single column',
"    @media (max-width: 1023px) { .ts-cards-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); } }",
"    /* Task 373: мобильная версия — карточки столбиком, по одной в\n"
"       строке, на всю ширину (отступы по краям — padding .ts-page) */\n"
"    @media (max-width: 1023px) { .ts-cards-grid { grid-template-columns: 1fr; } }")

# ============================================================
# 6. HTML: табы «Все / Избранные» на странице выбора
# ============================================================
edit('html: tabs on temp-sensors page',
"            <div class=\"ts-page\">\n"
"                <div class=\"ts-group-title\"><span class=\"ts-group-badge ts-group-badge-rtd\">ТС</span><span>Термометры сопротивления</span><span class=\"ts-group-sub\">ГОСТ 6651-2009</span></div>\n"
"                <div id=\"tsRtdCards\" class=\"ts-cards-grid\"></div>\n"
"                <div class=\"ts-group-title ts-group-title-tc\"><span class=\"ts-group-badge ts-group-badge-tc\">ТП</span><span>Термопары</span><span class=\"ts-group-sub\">ГОСТ Р 8.585-2001</span></div>\n"
"                <div id=\"tsTcCards\" class=\"ts-cards-grid\"></div>\n"
"            </div>",
"            <div class=\"ts-page\">\n"
"                <!-- Task 373: табы «Все / Избранные» — по примеру расходомеров\n"
"                     хозрасчётных (FlowFav): звёздочка на карточке и в шапке\n"
"                     страницы датчика, счётчики, localStorage (TempFav) -->\n"
"                <div class=\"ts-tabs\" role=\"tablist\" aria-label=\"Список датчиков температуры\">\n"
"                    <button type=\"button\" class=\"ts-tab active\" data-ts-tab=\"all\" onclick=\"setTempSensorsTab('all')\" role=\"tab\" aria-selected=\"true\">Все <span class=\"ts-tab-count\" id=\"tsAllCount\">0</span></button>\n"
"                    <button type=\"button\" class=\"ts-tab\" data-ts-tab=\"fav\" onclick=\"setTempSensorsTab('fav')\" role=\"tab\" aria-selected=\"false\">Избранные <span class=\"ts-tab-count\" id=\"tsFavCount\">0</span></button>\n"
"                </div>\n"
"                <div class=\"ts-group-title\" id=\"tsRtdGroupTitle\"><span class=\"ts-group-badge ts-group-badge-rtd\">ТС</span><span>Термометры сопротивления</span><span class=\"ts-group-sub\">ГОСТ 6651-2009</span></div>\n"
"                <div id=\"tsRtdCards\" class=\"ts-cards-grid\"></div>\n"
"                <div class=\"ts-group-title ts-group-title-tc\" id=\"tsTcGroupTitle\"><span class=\"ts-group-badge ts-group-badge-tc\">ТП</span><span>Термопары</span><span class=\"ts-group-sub\">ГОСТ Р 8.585-2001</span></div>\n"
"                <div id=\"tsTcCards\" class=\"ts-cards-grid\"></div>\n"
"            </div>")

# ============================================================
# 7. HTML: звезда в шапке страницы датчика + статичная панель
#    «Расчёт произвольных значений» НАД формой выбора диапазона/шага
# ============================================================
edit('html: view header fav btn + static calc panel',
"            <div class=\"page-inline-header\"><div class=\"page-inline-header-chevron\" onclick=\"chevronTap()\" aria-label=\"Назад / Главная\"></div><div class=\"page-inline-header-title\" id=\"tempSensorViewTitle\">Датчик температуры</div></div>\n"
"            <div class=\"conv-columns\">\n"
"                <div class=\"conv-col conv-col-input\">\n"
"                    <div class=\"scale-form\">",
"            <div class=\"page-inline-header\"><div class=\"page-inline-header-chevron\" onclick=\"chevronTap()\" aria-label=\"Назад / Главная\"></div><div class=\"page-inline-header-title\" id=\"tempSensorViewTitle\">Датчик температуры</div><button type=\"button\" id=\"tempSensorFavBtn\" onclick=\"toggleTempSensorFavFromView()\" aria-label=\"В избранное\" title=\"Добавить/убрать из избранного\">☆</button></div>\n"
"            <div class=\"conv-columns\">\n"
"                <div class=\"conv-col conv-col-input\">\n"
"                    <!-- Task 373: «Расчёт произвольных значений» (Task 371) —\n"
"                         СТАТИЧНАЯ панель НАД формой выбора предела измерения и\n"
"                         шага таблицы: отображается ВСЕГДА, а не только после\n"
"                         «Рассчитать». Подпись второго поля и пример подставляет\n"
"                         openTempSensor() под тип датчика; живой двусторонний\n"
"                         расчёт — прежние tempQueryFromTemp/tempQueryFromValue. -->\n"
"                    <div class=\"ts-calc-panel\" id=\"tempCustomCalcPanel\">\n"
"                        <div class=\"ts-calc-title\">Расчёт произвольных значений</div>\n"
"                        <div class=\"ts-calc-hint\">Введите значение в любое поле — другое рассчитается автоматически</div>\n"
"                        <div class=\"scale-form-label\">Температура (°C)</div>\n"
"                        <input type=\"text\" inputmode=\"numeric\" id=\"tempQueryTemp\" class=\"scale-field\" placeholder=\"Например: 55\" oninput=\"tempQueryFromTemp()\" autocomplete=\"off\" enterkeyhint=\"next\">\n"
"                        <div class=\"scale-form-label\" id=\"tempQueryValLabel\">Сопротивление R(t), Ом</div>\n"
"                        <input type=\"text\" inputmode=\"numeric\" id=\"tempQueryVal\" class=\"scale-field\" placeholder=\"Например: 61,8\" oninput=\"tempQueryFromValue()\" autocomplete=\"off\" enterkeyhint=\"done\">\n"
"                    </div>\n"
"                    <div class=\"scale-form\">")

# ============================================================
# 8. JS: getTcSensorMap — добавить ТХК (L)
# ============================================================
edit('js: tc map + L',
"        return {K:'ТХА (K)',J:'ТЖК (J)',T:'ТМК (T)',N:'ТНН (N)',E:'ТХКн (E)',R:'ТПП (R)',S:'ТПП (S)',B:'ТПР (B)'};",
"        // Task 373: добавлена ТХК (L) — хромель-копель (ГОСТ Р 8.585-2001)\n"
"        return {K:'ТХА (K)',J:'ТЖК (J)',T:'ТМК (T)',N:'ТНН (N)',E:'ТХКн (E)',L:'ТХК (L)',R:'ТПП (R)',S:'ТПП (S)',B:'ТПР (B)'};")

# ============================================================
# 9. JS: каталог — tcm + порядок с L после E
# ============================================================
edit('js: catalog tcm + order with L',
"        let tcm={K:{mat:'хромель-алюмель',r:[-270,1372]},J:{mat:'железо-константан',r:[-210,1200]},T:{mat:'медь-константан',r:[-270,400]},N:{mat:'никросил-нисил',r:[-270,1300]},E:{mat:'хромель-константан',r:[-270,1000]},R:{mat:'платинородий-платина',r:[-50,1768]},S:{mat:'платинородий-платина',r:[-50,1768]},B:{mat:'платинородий-платинородий',r:[0,1820]}};\n"
"        ['K','J','T','N','E','R','S','B'].forEach(function(k){",
"        // Task 373: L — хромель-копель, диапазон НСХ −200…800 °C\n"
"        let tcm={K:{mat:'хромель-алюмель',r:[-270,1372]},J:{mat:'железо-константан',r:[-210,1200]},T:{mat:'медь-константан',r:[-270,400]},N:{mat:'никросил-нисил',r:[-270,1300]},E:{mat:'хромель-константан',r:[-270,1000]},L:{mat:'хромель-копель',r:[-200,800]},R:{mat:'платинородий-платина',r:[-50,1768]},S:{mat:'платинородий-платина',r:[-50,1768]},B:{mat:'платинородий-платинородий',r:[0,1820]}};\n"
"        ['K','J','T','N','E','L','R','S','B'].forEach(function(k){")

# ============================================================
# 10. JS: TempFav + переключатели (после getTcSensorMap)
# ============================================================
edit('js: TempFav module',
"    // Каталог всех датчиков температуры — источник карточек страницы\n"
"    // выбора, диапазонов НСХ и справочной информации. Порядок как в\n"
"    // бывших выпадающих списках: ТС (Cu → Pt), затем ТП (K…B).\n"
"    function getTempSensorCatalog(){",
"    // ============================================================\n"
"    // Task 373: TempFav — избранное датчиков температуры, по примеру\n"
"    // расходомеров хозрасчётных (FlowFav): отдельный localStorage-ключ,\n"
"    // звёздочка на карточке списка и в шапке страницы датчика, таб\n"
"    // «Избранные». Без drag-and-drop: порядок избранных = порядок\n"
"    // каталога (каталог фиксированный, в отличие от расходомеров).\n"
"    // ============================================================\n"
"    var TempFav={\n"
"        _STORAGE_KEY:'kip8_temp_fav_v1',\n"
"        _data:null,\n"
"        _load:function(){\n"
"            if(this._data!==null){return;}\n"
"            try{\n"
"                let raw=(typeof localStorage!=='undefined')?localStorage.getItem(this._STORAGE_KEY):null;\n"
"                this._data=raw?JSON.parse(raw):{};\n"
"            }catch(e){this._data={};}\n"
"        },\n"
"        _save:function(){\n"
"            try{localStorage.setItem(this._STORAGE_KEY,JSON.stringify(this._data||{}));}catch(e){}\n"
"        },\n"
"        has:function(key){this._load();return this._data.hasOwnProperty(String(key));},\n"
"        add:function(key){\n"
"            this._load();\n"
"            let k=String(key);\n"
"            if(this._data.hasOwnProperty(k)){return false;}\n"
"            this._data[k]=new Date().toISOString();\n"
"            this._save();\n"
"            return true;\n"
"        },\n"
"        remove:function(key){\n"
"            this._load();\n"
"            let k=String(key);\n"
"            if(!this._data.hasOwnProperty(k)){return false;}\n"
"            delete this._data[k];\n"
"            this._save();\n"
"            return true;\n"
"        },\n"
"        toggle:function(key){if(this.has(key)){this.remove(key);return false;}this.add(key);return true;},\n"
"        count:function(){this._load();return Object.keys(this._data).length;}\n"
"    };\n"
"    // Task 373: звёздочка на карточке списка (как flow-card-fav-btn)\n"
"    function toggleTempSensorFav(key){\n"
"        TempFav.toggle(key);\n"
"        if(typeof navigator!=='undefined'&&navigator.vibrate){navigator.vibrate(10);}\n"
"        renderTempSensorCards();\n"
"        updateTempSensorFavBtn();\n"
"    }\n"
"    // Task 373: звёздочка в шапке страницы датчика (как flowFavBtn)\n"
"    function toggleTempSensorFavFromView(){\n"
"        if(!tempSensorKey){return;}\n"
"        toggleTempSensorFav(tempSensorKey);\n"
"    }\n"
"    function updateTempSensorFavBtn(){\n"
"        let btn=document.getElementById('tempSensorFavBtn');\n"
"        if(!btn){return;}\n"
"        let isFav=tempSensorKey?TempFav.has(tempSensorKey):false;\n"
"        if(btn.classList){btn.classList.toggle('active',isFav);}\n"
"        btn.textContent=isFav?'★':'☆';\n"
"        btn.setAttribute('aria-label',isFav?'Убрать из избранного':'В избранное');\n"
"    }\n"
"    // Каталог всех датчиков температуры — источник карточек страницы\n"
"    // выбора, диапазонов НСХ и справочной информации. Порядок как в\n"
"    // бывших выпадающих списках: ТС (Cu → Pt), затем ТП (K…B),\n"
"    // Task 373: после ТХКн (E) — ТХК (L), хромель-копель.\n"
"    function getTempSensorCatalog(){")

# ============================================================
# 11. JS: renderTempSensorCards — перерисовка, избранное, без бейджей
# ============================================================
edit('js: renderTempSensorCards rewrite',
"    // Рендер карточек на странице выбора (идемпотентный)\n"
"    function renderTempSensorCards(){\n"
"        let rtdBox=document.getElementById('tsRtdCards');\n"
"        let tcBox=document.getElementById('tsTcCards');\n"
"        if(!rtdBox||!tcBox){return;}\n"
"        if(rtdBox.children.length&&tcBox.children.length){return;}\n"
"        let fmtR=function(v){return String(v).replace('-','−');};\n"
"        let rtdHtml='',tcHtml='';\n"
"        getTempSensorCatalog().forEach(function(s){\n"
"            let cls=s.kind==='rtd'?'ts-card-badge-rtd':'ts-card-badge-tc';\n"
"            let card='<div class=\"ts-card'+(s.kind==='tc'?' ts-card-tc':'')+'\" onclick=\"openTempSensor(\\''+s.key+'\\')\" role=\"button\" tabindex=\"0\" aria-label=\"'+s.name+'\">'\n"
"                +'<div class=\"ts-card-top\"><span class=\"ts-card-badge '+cls+'\">'+(s.kind==='rtd'?'ТС':'ТП')+'</span><span class=\"ts-card-name\">'+s.name+'</span><i class=\"ts-card-arrow\">›</i></div>'\n"
"                +'<div class=\"ts-card-meta\">'+s.meta+'</div>'\n"
"                +'<div class=\"ts-card-range\">НСХ: '+fmtR(s.range.min)+'…'+fmtR(s.range.max)+' °C</div>'\n"
"                +'</div>';\n"
"            if(s.kind==='rtd'){rtdHtml+=card;}else{tcHtml+=card;}\n"
"        });\n"
"        rtdBox.innerHTML=rtdHtml;\n"
"        tcBox.innerHTML=tcHtml;\n"
"    }",
"    // Task 373: состояние таба «Все / Избранные» страницы выбора\n"
"    var tempSensorsTab='all';\n"
"    // Рендер карточек на странице выбора. Task 373: перерисовывается при\n"
"    // КАЖДОМ вызове (звёзды избранного и активный таб меняются), в режиме\n"
"    // «Избранные» показывает только избранные датчики (заголовки пустых\n"
"    // групп скрыты), бейджи ТС/ТП убраны, звезда избранного — в правом\n"
"    // верхнем углу карточки (по примеру расходомеров хозрасчётных).\n"
"    function renderTempSensorCards(){\n"
"        let rtdBox=document.getElementById('tsRtdCards');\n"
"        let tcBox=document.getElementById('tsTcCards');\n"
"        if(!rtdBox||!tcBox){return;}\n"
"        let favMode=(tempSensorsTab==='fav');\n"
"        let fmtR=function(v){return String(v).replace('-','−');};\n"
"        let cat=getTempSensorCatalog();\n"
"        // счётчики в табах «Все / Избранные» (обновляются при каждом рендере)\n"
"        let allEl=document.getElementById('tsAllCount'),favEl=document.getElementById('tsFavCount');\n"
"        if(allEl){allEl.textContent=String(cat.length);}\n"
"        if(favEl){favEl.textContent=String(TempFav.count());}\n"
"        let rtdHtml='',tcHtml='',rtdShown=false,tcShown=false;\n"
"        cat.forEach(function(s){\n"
"            if(favMode&&!TempFav.has(s.key)){return;}\n"
"            let isFav=TempFav.has(s.key);\n"
"            let card='<div class=\"ts-card'+(s.kind==='tc'?' ts-card-tc':'')+'\" onclick=\"openTempSensor(\\''+s.key+'\\')\" role=\"button\" tabindex=\"0\" aria-label=\"'+s.name+'\">'\n"
"                +'<button type=\"button\" class=\"ts-card-fav-btn'+(isFav?' active':'')+'\" onclick=\"event.stopPropagation(); toggleTempSensorFav(\\''+s.key+'\\')\" aria-label=\"'+(isFav?'Убрать из избранного':'В избранное')+'\" title=\"'+(isFav?'Убрать из избранного':'В избранное')+'\">'+(isFav?'★':'☆')+'</button>'\n"
"                +'<div class=\"ts-card-top\"><span class=\"ts-card-name\">'+s.name+'</span><i class=\"ts-card-arrow\">›</i></div>'\n"
"                +'<div class=\"ts-card-meta\">'+s.meta+'</div>'\n"
"                +'<div class=\"ts-card-range\">НСХ: '+fmtR(s.range.min)+'…'+fmtR(s.range.max)+' °C</div>'\n"
"                +'</div>';\n"
"            if(s.kind==='rtd'){rtdHtml+=card;rtdShown=true;}else{tcHtml+=card;tcShown=true;}\n"
"        });\n"
"        if(favMode&&!rtdShown&&!tcShown){\n"
"            rtdHtml='<div class=\"ts-empty-fav\"><div class=\"ts-empty-fav-icon\">☆</div><div class=\"ts-empty-fav-text\">Нет избранных датчиков</div><div class=\"ts-empty-fav-hint\">Перейдите во вкладку «Все»<br>и нажмите <span class=\"star\">☆</span> на карточке</div></div>';\n"
"        }\n"
"        rtdBox.innerHTML=rtdHtml;\n"
"        tcBox.innerHTML=tcHtml;\n"
"        // в режиме «Избранные» скрываем заголовки пустых групп\n"
"        let rtdTitle=document.getElementById('tsRtdGroupTitle');\n"
"        let tcTitle=document.getElementById('tsTcGroupTitle');\n"
"        if(rtdTitle){rtdTitle.style.display=(!favMode||rtdShown)?'':'none';}\n"
"        if(tcTitle){tcTitle.style.display=(!favMode||tcShown)?'':'none';}\n"
"    }\n"
"    // Task 373: переключение таба «Все / Избранные» (setTab у расходомеров)\n"
"    function setTempSensorsTab(tab){\n"
"        if(tab!=='all'&&tab!=='fav'){return;}\n"
"        if(tempSensorsTab===tab){return;}\n"
"        tempSensorsTab=tab;\n"
"        if(typeof document.querySelectorAll==='function'){\n"
"            let btns=document.querySelectorAll('.ts-tab[data-ts-tab]');\n"
"            for(let i=0;i<btns.length;i++){\n"
"                let b=btns[i];\n"
"                let on=(b.getAttribute('data-ts-tab')===tab);\n"
"                b.classList.toggle('active',on);\n"
"                b.setAttribute('aria-selected',on?'true':'false');\n"
"            }\n"
"        }\n"
"        renderTempSensorCards();\n"
"    }")

# ============================================================
# 12. JS: openTempSensor — чип без бейджа, подписи панели, звезда
# ============================================================
edit('js: openTempSensor chip without badge',
"        let chip=document.getElementById('tempSensorViewChip');\n"
"        if(chip){chip.innerHTML='<span class=\"ts-card-badge '+(sel.kind==='rtd'?'ts-card-badge-rtd':'ts-card-badge-tc')+'\">'+(sel.kind==='rtd'?'ТС':'ТП')+'</span><span class=\"ts-view-chip-name\">'+sel.name+'</span><span class=\"ts-view-chip-meta\">'+sel.meta+'</span>';}",
"        let chip=document.getElementById('tempSensorViewChip');\n"
"        // Task 373: бейдж ТС/ТП убран из чипа — только имя и параметры\n"
"        if(chip){chip.innerHTML='<span class=\"ts-view-chip-name\">'+sel.name+'</span><span class=\"ts-view-chip-meta\">'+sel.meta+'</span>';}")

edit('js: openTempSensor panel labels + fav btn',
"        let res=document.getElementById('tempSensorResults');\n"
"        if(res){res.innerHTML='';res.style.display='none';}\n"
"        let body=document.getElementById('tempSensorInfoBody');\n"
"        if(body){body.innerHTML=tempSensorInfoHtml(sel);}",
"        let res=document.getElementById('tempSensorResults');\n"
"        if(res){res.innerHTML='';res.style.display='none';}\n"
"        // Task 373: панель «Расчёт произвольных значений» (статичная,\n"
"        // над формой выбора) — подпись второго поля и пример под тип\n"
"        // датчика, оба поля очищены\n"
"        let vLab=document.getElementById('tempQueryValLabel');\n"
"        let vInp=document.getElementById('tempQueryVal');\n"
"        let tInp=document.getElementById('tempQueryTemp');\n"
"        if(sel.kind==='rtd'){\n"
"            if(vLab){vLab.textContent='Сопротивление R(t), Ом';}\n"
"            if(vInp){vInp.placeholder='Например: 61,8';}\n"
"        }else{\n"
"            if(vLab){vLab.textContent='Термо-ЭДС E(t), мВ';}\n"
"            if(vInp){vInp.placeholder='Например: 2,2';}\n"
"        }\n"
"        if(tInp){tInp.value='';}\n"
"        if(vInp){vInp.value='';}\n"
"        // Task 373: звезда избранного в шапке страницы датчика\n"
"        updateTempSensorFavBtn();\n"
"        let body=document.getElementById('tempSensorInfoBody');\n"
"        if(body){body.innerHTML=tempSensorInfoHtml(sel);}")

# ============================================================
# 13. JS: tempSensorInfoHtml — НСХ-строка для L + типы с ТХК (L)
# ============================================================
edit('js: info html L-aware',
"        return '<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">Тип:</b> Термопара (ТП) — измеряет температуру по термо-ЭДС, возникающей в спае двух разнородных проводников (эффект Зеебека).</div>'\n"
"            +'<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">Этот датчик:</b> '+sel.name+'; электроды: '+sel.meta+'; диапазон НСХ: '+sel.range.min+'…'+sel.range.max+' °C; E(0 °C) = 0 мВ (опорный спай 0 °C).</div>'\n"
"            +'<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">НСХ термопар:</b> стандартизированы ГОСТ Р 8.585-2001; расчёт — полиномы НИСТ ITS-90 (SRD 60): E(t) = Σ cᵢ·tⁱ.</div>'\n"
"            +'<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">Наиболее распространённые типы:</b> ТХА (K), ТЖК (J), ТМК (T), ТНН (N), ТХКн (E), ТПП (R), ТПП (S), ТПР (B).</div>'\n"
"            +'<div><b style=\"'+b+'\">Нормативные документы:</b> ГОСТ Р 8.585-2001 (ТП).</div>';",
"        // Task 373: для ТХК (L) — отдельная строка НСХ: тип есть только в\n"
"        // ГОСТ Р 8.585-2001 (в МЭК 60584 и базе НИСТ SRD 60 его нет),\n"
"        // расчёт — аппроксимирующий полином по таблице стандарта.\n"
"        let nscLine;\n"
"        if(sel.tc==='L'){\n"
"            nscLine='<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">НСХ термопар:</b> стандартизированы ГОСТ Р 8.585-2001; тип ТХК (L) есть только в ГОСТ (в МЭК 60584 и базе НИСТ отсутствует); расчёт — аппроксимирующий полином по таблице стандарта: E(t) = Σ cᵢ·tⁱ.</div>';\n"
"        }else{\n"
"            nscLine='<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">НСХ термопар:</b> стандартизированы ГОСТ Р 8.585-2001; расчёт — полиномы НИСТ ITS-90 (SRD 60): E(t) = Σ cᵢ·tⁱ.</div>';\n"
"        }\n"
"        return '<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">Тип:</b> Термопара (ТП) — измеряет температуру по термо-ЭДС, возникающей в спае двух разнородных проводников (эффект Зеебека).</div>'\n"
"            +'<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">Этот датчик:</b> '+sel.name+'; электроды: '+sel.meta+'; диапазон НСХ: '+sel.range.min+'…'+sel.range.max+' °C; E(0 °C) = 0 мВ (опорный спай 0 °C).</div>'\n"
"            +nscLine\n"
"            +'<div style=\"margin-bottom:8px;\"><b style=\"'+b+'\">Наиболее распространённые типы:</b> ТХА (K), ТХК (L), ТЖК (J), ТМК (T), ТНН (N), ТХКн (E), ТПП (R), ТПП (S), ТПР (B).</div>'\n"
"            +'<div><b style=\"'+b+'\">Нормативные документы:</b> ГОСТ Р 8.585-2001 (ТП).</div>';")

# ============================================================
# 14. JS: calcTempSensor — убрать панель из результатов (ТС)
# ============================================================
edit('js: calcTempSensor rtd remove panel',
"            html+=`</tbody></table></div>`;\n"
"            // Task 371: под таблицей — блок «Расчёт произвольных значений»\n"
"            // (по примеру раздела «Шкала-сигнал», живой двусторонний расчёт)\n"
"            html+=tempCustomCalcHtml('Сопротивление R(t), Ом','Например: 61,8');\n"
"            resDiv.innerHTML=html;",
"            html+=`</tbody></table></div>`;\n"
"            // Task 373: блок «Расчёт произвольных значений» перенесён НАД\n"
"            // форму выбора диапазона/шага (статичная панель в колонке\n"
"            // ввода) — из результатов удалён\n"
"            resDiv.innerHTML=html;")

# ============================================================
# 15. JS: calcTempSensor — убрать панель из результатов (ТП)
# ============================================================
edit('js: calcTempSensor tc remove panel',
"            html+=`</tbody></table></div>`;\n"
"            // Task 371: под таблицей — блок «Расчёт произвольных значений»\n"
"            html+=tempCustomCalcHtml('Термо-ЭДС E(t), мВ','Например: 2,2');\n"
"            resDiv.innerHTML=html;",
"            html+=`</tbody></table></div>`;\n"
"            // Task 373: панель произвольных значений — статичная, над формой\n"
"            resDiv.innerHTML=html;")

# ============================================================
# 16. JS: calcTcVoltage — ветка L (хромель-копель, ГОСТ)
# ============================================================
edit('js: calcTcVoltage L branch',
"        } else if(type==='R'){",
"        } else if(type==='L'){\n"
"            // Task 373: ТХК (L) — хромель-копель, ГОСТ Р 8.585-2001\n"
"            // (−200…800 °C). В базе НИСТ (SRD 60) и МЭК 60584 этого типа\n"
"            // НЕТ — полиномы аппроксимации подобраны по таблице стандарта\n"
"            // (два диапазона, точность лучше 0,001 мВ). Контрольные точки:\n"
"            // E(−100)=−5,641; E(100)=6,862; E(500)=40,299; E(800)=66,466 мВ.\n"
"            if(t>=0){\n"
"                let c=[4.0535830849e-6, 6.3307953909e-2, 6.0231773449e-5, -8.0885846926e-8, 1.0111986656e-10, -4.7710783920e-14, -2.2894088054e-16, 4.1439904615e-19, -2.0259856006e-22];\n"
"                let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }\n"
"            } else {\n"
"                let c=[1.8620992536e-5, 6.3326208351e-2, 6.0355654401e-5, -8.2356261044e-8, 8.5085309858e-13, -7.0918273232e-13, -1.9410086265e-15];\n"
"                let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }\n"
"            }\n"
"        } else if(type==='R'){")

# ============================================================
# 17. JS: удалить функцию tempCustomCalcHtml (панель статичная)
# ============================================================
edit('js: remove tempCustomCalcHtml',
"    // Task 371: HTML блока «Расчёт произвольных значений» — единый для\n"
"    // веток ТС и ТП (отличаются подпись второго поля и пример в нём);\n"
"    // разметка повторяет scaleCustomCalcPanel раздела «Шкала-сигнал»\n"
"    function tempCustomCalcHtml(valLabel,valPlaceholder){\n"
"        return `<div id=\"tempCustomCalcPanel\"><div class=\"converter-result-label-title\" style=\"margin-top:16px;\">Расчёт произвольных значений</div><div class=\"scale-form\" style=\"margin-top:8px;\"><div style=\"color:rgba(255,255,255,0.25); font-size:11px; margin-bottom:10px; line-height:1.4;\">Введите значение в любое поле — другое рассчитается автоматически</div><div class=\"scale-form-label\">Температура (°C)</div><input type=\"text\" inputmode=\"numeric\" id=\"tempQueryTemp\" class=\"scale-field\" placeholder=\"Например: 55\" oninput=\"tempQueryFromTemp()\" autocomplete=\"off\" enterkeyhint=\"done\"><div class=\"scale-form-label\">${valLabel}</div><input type=\"text\" inputmode=\"numeric\" id=\"tempQueryVal\" class=\"scale-field\" placeholder=\"${valPlaceholder}\" oninput=\"tempQueryFromValue()\" autocomplete=\"off\" enterkeyhint=\"done\"></div></div>`;\n"
"    }\n",
"    // Task 373: функция tempCustomCalcHtml УДАЛЕНА — панель «Расчёт\n"
"    // произвольных значений» стала статичной разметкой страницы датчика\n"
"    // ( ts-calc-panel над формой выбора диапазона/шага ); подписи полей\n"
"    // под тип датчика задаёт openTempSensor().\n")

# ============================================================
# Запись и контроль
# ============================================================
io.open(PATH, 'w', encoding='utf-8').write(src)
print('OK: %d правок, размер %d -> %d байт (%+d)' % (len(edits), orig_len, len(src), len(src) - orig_len))
for name, delta in edits:
    print('  [+] %-42s %+d байт' % (name, delta))

# Контрольные проверки
checks = [
    ('ts-card-badge классы не используются', 'ts-card-badge-rtd' not in src and 'ts-card-badge-tc' not in src and 'class="ts-card-badge' not in src),
    ('tempCustomCalcHtml не вызывается', src.count('tempCustomCalcHtml(') == 0),
    ('function tempCustomCalcHtml удалена', 'function tempCustomCalcHtml' not in src),
    ('статичная панель в разметке', 'id="tempCustomCalcPanel"' in src),
    ('панель над формой (порядок)', src.index('id="tempCustomCalcPanel"') < src.index('id="temp_sensor_min"')),
    ('табы на месте', 'data-ts-tab="fav"' in src and 'setTempSensorsTab' in src),
    ('звезда в шапке датчика', 'id="tempSensorFavBtn"' in src),
    ('TempFav с ключом', "kip8_temp_fav_v1" in src),
    ('L в карте ТП', "L:'ТХК (L)'" in src),
    ('L в каталоге', "L:{mat:'хромель-копель',r:[-200,800]}" in src),
    ('коэффициент POS L', '6.3307953909e-2' in src),
    ('коэффициент NEG L', '6.3326208351e-2' in src),
    ('мобильная сетка 1fr', '.ts-cards-grid { grid-template-columns: 1fr; }' in src),
    ('маркеры Task 373 >= 12', len(__import__('re').findall(r'Task 373', src)) >= 12),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print('  %s %s' % ('PASS' if ok else 'FAIL', n))
assert not bad, 'Провалены проверки: %s' % bad
print('Все контрольные проверки пройдены.')
