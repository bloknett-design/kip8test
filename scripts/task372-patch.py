#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 372: переделка раздела «Датчики температуры» (заявка пользователя):
#   1) страница Главная / Инженерные калькуляторы / КИП и А / Датчики
#      температуры — список КАРТОЧЕК всех датчиков из бывших выпадающих
#      списков (8 ТС + 8 ТП);
#   2) выбор карточки → переход на страницу датчика: диапазон измерения,
#      шаг таблицы, «Рассчитать» → таблица значений + блок «Расчёт
#      произвольных значений» (Task 371: t ↔ R(t) для ТС, t ↔ E(t) для ТП);
#   3) справочная информация — в КАЖДОМ датчике, но в термометрах НЕТ
#      информации о термопарах, в термопарах — о термометрах.
#
# Правки index.html:
#   CSS: блок .ts-* (карточки, группы, бейджи, чип) + светлая тема + мобайл;
#   HTML: #page-temp-sensors → страница карточек; новая #page-temp-sensor-view
#         (conv-3col-page: форма + результаты + справка);
#   JS: состояние tempSensorKey, getTcSensorMap, getTempSensorCatalog,
#       tempSensorFindByKey, renderTempSensorCards, openTempSensor,
#       tempSensorInfoHtml; calcTempSensor/getTempSensorRange/
#       tempCalcForwardValue читают состояние вместо selects;
#       updateTempSensorOptions удалён;
#   Реестры: PAGE_PARENTS, PAGE_LABELS, топ-бар, KipAuth._CALC_PAGES,
#            navigateTo-хуки; саблейблы меню и SUBSECTIONS.
# Запуск из корня репо kip8test: python3 scripts/task372-patch.py
import sys

PATH = 'index.html'
src = open(PATH, encoding='utf-8').read()
orig_len = len(src)
edits_done = []

def rep(old, new, tag, count=1):
    global src
    n = src.count(old)
    assert n == count, 'ЯКОРЬ %s: найдено %d (ожидалось %d)' % (tag, n, count)
    src = src.replace(old, new, count)
    edits_done.append(tag)

# ============================================================
# 1. CSS — стили карточек/групп/чипа (после .formula-inline, перед .method-indicator)
# ============================================================
CSS = '''
    /* ===== Task 372: «Датчики температуры» — страница карточек ===== */
    .ts-page { padding: 4px 0 12px; position: relative; z-index: 2; }
    .ts-group-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 16px 0 10px; font-size: 16px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.2px; }
    .ts-group-title .ts-group-sub { font-size: 12px; font-weight: 500; color: var(--conv-info-text); }
    .ts-group-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 34px; height: 22px; padding: 0 7px; border-radius: 7px; font-size: 12px; font-weight: 800; letter-spacing: 0.5px; flex-shrink: 0; }
    .ts-group-badge-rtd { background: rgba(74, 199, 113, 0.14); color: #4ac771; border: 1px solid rgba(74, 199, 113, 0.35); }
    .ts-group-badge-tc { background: rgba(199, 150, 74, 0.14); color: #c7964a; border: 1px solid rgba(199, 150, 74, 0.35); }
    .ts-cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }
    .ts-card { position: relative; display: flex; flex-direction: column; gap: 6px; padding: 12px 14px; background: var(--card-bg); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid var(--card-border); border-radius: 14px; cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; -webkit-user-select: none; user-select: none; touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
    .ts-card:hover, .ts-card:active { transform: scale(0.97); background: var(--active-bg); border-color: rgba(74, 143, 199, 0.35); }
    .ts-card-top { display: flex; align-items: center; gap: 8px; }
    .ts-card-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 32px; height: 20px; padding: 0 6px; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; flex-shrink: 0; }
    .ts-card-badge-rtd { background: rgba(74, 199, 113, 0.14); color: #4ac771; border: 1px solid rgba(74, 199, 113, 0.3); }
    .ts-card-badge-tc { background: rgba(199, 150, 74, 0.14); color: #c7964a; border: 1px solid rgba(199, 150, 74, 0.3); }
    .ts-card-name { font-size: 17px; font-weight: 600; color: var(--text-primary); line-height: 1.25; overflow-wrap: break-word; word-break: break-word; }
    .ts-card-meta { font-size: 12px; color: var(--conv-info-text); line-height: 1.45; }
    .ts-card-range { font-size: 11px; color: rgba(255, 255, 255, 0.3); line-height: 1.4; }
    .ts-card-arrow { margin-left: auto; color: rgba(255, 255, 255, 0.12); font-size: 18px; font-style: normal; font-weight: 700; flex-shrink: 0; }
    .ts-card:hover .ts-card-arrow, .ts-card:active .ts-card-arrow { color: rgba(74, 143, 199, 0.4); }
    /* Task 372: чип выбранного датчика на странице датчика */
    .ts-view-chip { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; min-height: 44px; padding: 9px 12px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; }
    .ts-view-chip-name { font-size: 15px; font-weight: 700; color: var(--text-primary); }
    .ts-view-chip-meta { font-size: 11px; color: var(--conv-info-text); line-height: 1.35; }
    [data-theme="light"] .ts-card-range { color: rgba(20, 20, 19, 0.35); }
    [data-theme="light"] .ts-card-arrow { color: rgba(20, 20, 19, 0.15); }
    [data-theme="light"] .ts-card-badge-rtd, [data-theme="light"] .ts-group-badge-rtd { background: rgba(43, 138, 74, 0.1); color: #2b8a4a; border-color: rgba(43, 138, 74, 0.3); }
    [data-theme="light"] .ts-card-badge-tc, [data-theme="light"] .ts-group-badge-tc { background: rgba(156, 108, 52, 0.1); color: #8a5c26; border-color: rgba(156, 108, 52, 0.3); }
    @media (max-width: 1023px) { .ts-cards-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); } }
    @media (max-width: 400px) { .ts-card { padding: 10px 12px; } .ts-card-name { font-size: 15px; } .ts-card-meta { font-size: 11px; } }

    .method-indicator {'''
rep('\n    .method-indicator {', CSS, 'CSS .ts-* перед .method-indicator')

# ============================================================
# 2. HTML — #page-temp-sensors (карточки) + #page-temp-sensor-view (расчёт)
# ============================================================
start = src.index('        <div id="page-temp-sensors"')
end = src.index('        <!-- ======================== ЧТО НОВОГО / СПРАВКА ======================== -->')
assert start != -1 and end != -1 and start < end, 'блок page-temp-sensors не найден'

NEW_PAGES = '''        <div id="page-temp-sensors" class="page-content">
            <div class="page-inline-header"><div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div><div class="page-inline-header-title">Датчики температуры</div></div>

            <!-- Task 372: страница выбора датчика — карточки вместо выпадающих
                 списков (типы жили в select temp_sensor_type / temp_rtd_type /
                 temp_tc_type). Карточки рендеряет renderTempSensorCards(). -->
            <div class="ts-page">
                <div class="ts-group-title"><span class="ts-group-badge ts-group-badge-rtd">ТС</span><span>Термометры сопротивления</span><span class="ts-group-sub">ГОСТ 6651-2009</span></div>
                <div id="tsRtdCards" class="ts-cards-grid"></div>
                <div class="ts-group-title ts-group-title-tc"><span class="ts-group-badge ts-group-badge-tc">ТП</span><span>Термопары</span><span class="ts-group-sub">ГОСТ Р 8.585-2001</span></div>
                <div id="tsTcCards" class="ts-cards-grid"></div>
            </div>
        </div>

        <!-- Task 372: страница выбранного датчика температуры — диапазон
             измерения, шаг таблицы, таблица значений, «Расчёт произвольных
             значений» (Task 371) и справочная информация по типу датчика -->
        <div id="page-temp-sensor-view" class="page-content conv-3col-page">
            <div class="page-inline-header"><div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div><div class="page-inline-header-title" id="tempSensorViewTitle">Датчик температуры</div></div>
            <div class="conv-columns">
                <div class="conv-col conv-col-input">
                    <div class="scale-form">
                <div class="scale-form-label">Тип датчика</div>
                <div id="tempSensorViewChip" class="ts-view-chip"></div>
                <div class="scale-form-label" style="margin-top:12px;">Диапазон измерения (°C)</div>
                <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: stretch;"><input type="text" inputmode="numeric" id="temp_sensor_min" class="scale-field" style="flex: 1; margin-bottom: 0;" value="0" placeholder="min °C" autocomplete="off" enterkeyhint="next"><input type="text" inputmode="numeric" id="temp_sensor_max" class="scale-field" style="flex: 1; margin-bottom: 0;" value="100" placeholder="max °C" autocomplete="off" enterkeyhint="next"></div>
                <div class="scale-form-label">Шаг таблицы (°C)</div>
                <input type="text" inputmode="numeric" id="temp_sensor_step" class="scale-field" value="10" placeholder="10" autocomplete="off" enterkeyhint="done"><div style="color:rgba(255,255,255,0.25); font-size:10px; margin-top:-6px; margin-bottom:8px; padding-left:4px;">Шаг расчёта таблицы в градусах Цельсия</div>
                            </div>
            <button type="button" class="converter-convert-btn" onclick="calcTempSensor()"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 16 16 12 12 8"/><line x1="8" y1="12" x2="16" y2="12"/></svg>Рассчитать</button>
                </div>
                <div class="conv-col conv-col-table">
                    <div class="conv-table-placeholder"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg><div class="ctp-title">Результаты расчёта</div><div class="ctp-text">Заполните параметры и нажмите «Рассчитать». Здесь появится таблица с расчётными значениями.</div></div>
            <div id="tempSensorResults" class="converter-result-group" style="display:none;"></div>
                </div>
                <div class="conv-col conv-col-info">
                    <!-- Task 372: справка заполняется под тип датчика
                         (tempSensorInfoHtml): в термометрах НЕТ информации о
                         термопарах, в термопарах — о термометрах. -->
            <div id="tempSensorInfo" class="conv-info-block" style="margin:14px 0 10px;padding:14px 16px;background:var(--card-bg);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border:1px solid var(--card-border);border-radius:14px;position:relative;z-index:2;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:var(--accent-blue);fill:none;stroke-width:2;stroke-linecap:round;flex-shrink:0;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span style="font-size:14px;font-weight:700;color:var(--text-primary);letter-spacing:-0.2px;">Справочная информация</span></div>
                <div id="tempSensorInfoBody" style="font-size:12px;color:var(--conv-info-text);line-height:1.6;"></div>
            </div>
                </div>
            </div>
        </div>

'''
src = src[:start] + NEW_PAGES + src[end:]
edits_done.append('HTML: #page-temp-sensors (карточки) + #page-temp-sensor-view')

# ============================================================
# 3. JS — состояние + каталог + карточки + открытие + справка
#    (на месте updateTempSensorOptions) + новый head calcTempSensor
# ============================================================
OLD = '''    function updateTempSensorOptions(){
        let type=document.getElementById('temp_sensor_type').value;
        document.getElementById('rtd_options').style.display=type==='rtd'?'block':'none';
        document.getElementById('tc_options').style.display=type==='tc'?'block':'none';
    }
    function calcTempSensor(){
        let type=document.getElementById('temp_sensor_type').value;'''

NEW = '''    // ============================================================
    // Task 372: «Датчики температуры» — страница карточек и страница
    // датчика. Раньше тип датчика выбирался выпадающими списками
    // (temp_sensor_type / temp_rtd_type / temp_tc_type) прямо в форме
    // расчёта; теперь список датчиков — карточки на #page-temp-sensors,
    // а расчёт живёт на отдельной странице #page-temp-sensor-view.
    // ============================================================
    // Состояние: ключ выбранного датчика (см. getTempSensorCatalog).
    var tempSensorKey=null;
    // Карта типов термопар (имена как в бывшем select temp_tc_type)
    function getTcSensorMap(){
        return {K:'ТХА (K)',J:'ТЖК (J)',T:'ТМК (T)',N:'ТНН (N)',E:'ТХКн (E)',R:'ТПП (R)',S:'ТПП (S)',B:'ТПР (B)'};
    }
    // Каталог всех датчиков температуры — источник карточек страницы
    // выбора, диапазонов НСХ и справочной информации. Порядок как в
    // бывших выпадающих списках: ТС (Cu → Pt), затем ТП (K…B).
    function getTempSensorCatalog(){
        let rtd=getRtdSensorMap();
        let alphaTxt={pt1391:'α = 0,00391 (ГОСТ)',pt1385:'α = 0,00385 (IEC)'};
        let fmtR=function(v){return String(v).replace('-','−');};
        let list=[];
        ['cu50_1428','cu100_1428','cu50_1426','cu100_1426','pt50_1391','pt100_1391','pt100_1385','pt1000_1385'].forEach(function(k){
            let sd=rtd[k];
            if(!sd){return;}
            let isCu=sd.nsc==='cu';
            let alpha=isCu?('α = '+String(sd.alpha).replace('.',',')+' °C⁻¹'):alphaTxt[sd.nsc];
            list.push({key:k,kind:'rtd',name:sd.name,meta:'R₀ = '+sd.r0+' Ом · '+alpha,range:isCu?{min:-50,max:200}:{min:-200,max:850}});
        });
        let tcm={K:{mat:'хромель-алюмель',r:[-270,1372]},J:{mat:'железо-константан',r:[-210,1200]},T:{mat:'медь-константан',r:[-270,400]},N:{mat:'никросил-нисил',r:[-270,1300]},E:{mat:'хромель-константан',r:[-270,1000]},R:{mat:'платинородий-платина',r:[-50,1768]},S:{mat:'платинородий-платина',r:[-50,1768]},B:{mat:'платинородий-платинородий',r:[0,1820]}};
        ['K','J','T','N','E','R','S','B'].forEach(function(k){
            let m=tcm[k];
            list.push({key:'tc_'+k,kind:'tc',tc:k,name:getTcSensorMap()[k],meta:m.mat,range:{min:m.r[0],max:m.r[1]}});
        });
        return list;
    }
    // Поиск датчика в каталоге по ключу
    function tempSensorFindByKey(key){
        let found=null;
        getTempSensorCatalog().forEach(function(s){ if(s.key===key){found=s;} });
        return found;
    }
    // Рендер карточек на странице выбора (идемпотентный)
    function renderTempSensorCards(){
        let rtdBox=document.getElementById('tsRtdCards');
        let tcBox=document.getElementById('tsTcCards');
        if(!rtdBox||!tcBox){return;}
        if(rtdBox.children.length&&tcBox.children.length){return;}
        let fmtR=function(v){return String(v).replace('-','−');};
        let rtdHtml='',tcHtml='';
        getTempSensorCatalog().forEach(function(s){
            let cls=s.kind==='rtd'?'ts-card-badge-rtd':'ts-card-badge-tc';
            let card='<div class="ts-card'+(s.kind==='tc'?' ts-card-tc':'')+'" onclick="openTempSensor(\\''+s.key+'\\')" role="button" tabindex="0" aria-label="'+s.name+'">'
                +'<div class="ts-card-top"><span class="ts-card-badge '+cls+'">'+(s.kind==='rtd'?'ТС':'ТП')+'</span><span class="ts-card-name">'+s.name+'</span><i class="ts-card-arrow">›</i></div>'
                +'<div class="ts-card-meta">'+s.meta+'</div>'
                +'<div class="ts-card-range">НСХ: '+fmtR(s.range.min)+'…'+fmtR(s.range.max)+' °C</div>'
                +'</div>';
            if(s.kind==='rtd'){rtdHtml+=card;}else{tcHtml+=card;}
        });
        rtdBox.innerHTML=rtdHtml;
        tcBox.innerHTML=tcHtml;
    }
    // Открытие страницы датчика: карточка → #page-temp-sensor-view
    function openTempSensor(key){
        let sel=tempSensorFindByKey(key);
        if(!sel){showToast('Датчик не найден');return;}
        tempSensorKey=key;
        let title=document.getElementById('tempSensorViewTitle');
        if(title){title.textContent=sel.name+(sel.kind==='rtd'?' — термометр сопротивления':' — термопара');}
        let chip=document.getElementById('tempSensorViewChip');
        if(chip){chip.innerHTML='<span class="ts-card-badge '+(sel.kind==='rtd'?'ts-card-badge-rtd':'ts-card-badge-tc')+'">'+(sel.kind==='rtd'?'ТС':'ТП')+'</span><span class="ts-view-chip-name">'+sel.name+'</span><span class="ts-view-chip-meta">'+sel.meta+'</span>';}
        let mn=document.getElementById('temp_sensor_min'),mx=document.getElementById('temp_sensor_max'),st=document.getElementById('temp_sensor_step');
        if(mn){mn.value='0';}
        if(mx){mx.value='100';}
        if(st){st.value='10';}
        let res=document.getElementById('tempSensorResults');
        if(res){res.innerHTML='';res.style.display='none';}
        let body=document.getElementById('tempSensorInfoBody');
        if(body){body.innerHTML=tempSensorInfoHtml(sel);}
        if(typeof navigator!=='undefined'&&navigator.vibrate){navigator.vibrate(10);}
        navigateTo('temp-sensor-view');
    }
    // Справочная информация на странице датчика (заявка Task 372):
    // блок остаётся в КАЖДОМ датчике, но в термометрах НЕТ информации
    // о термопарах, а в термопарах — о термометрах.
    function tempSensorInfoHtml(sel){
        let b='color:var(--conv-info-bold);';
        if(sel.kind==='rtd'){
            let sd=getRtdSensorMap()[sel.key]||{};
            return '<div style="margin-bottom:8px;"><b style="'+b+'">Тип:</b> Термопреобразователь сопротивления (ТС) — измеряет температуру по изменению электрического сопротивления чувствительного элемента.</div>'
                +'<div style="margin-bottom:8px;"><b style="'+b+'">Этот датчик:</b> '+(sd.name||sel.name)+'; R₀ = '+(sd.r0||'—')+' Ом; формула: '+(sd.formula||'—')+'; диапазон НСХ: '+sel.range.min+'…'+sel.range.max+' °C.</div>'
                +'<div style="margin-bottom:8px;"><b style="'+b+'">Формулы ТС:</b> медные: R(t) = R₀·(1 + α·t); платиновые: R(t) = R₀·[1 + A·t + B·t² + C·(t−100)·t³] — член C добавляется ниже 0 °C.</div>'
                +'<div style="margin-bottom:8px;"><b style="'+b+'">Температурные коэффициенты:</b> Cu: α = 0,00428 °C⁻¹ (50М, 100М) или 0,00426 °C⁻¹; Pt: α = 0,00391 °C⁻¹ (50П, 100П, ГОСТ 6651-2009) или 0,00385 °C⁻¹ (IEC 60751).</div>'
                +'<div><b style="'+b+'">Нормативные документы:</b> ГОСТ 6651-2009 (ТС), IEC 60751 (Pt).</div>';
        }
        return '<div style="margin-bottom:8px;"><b style="'+b+'">Тип:</b> Термопара (ТП) — измеряет температуру по термо-ЭДС, возникающей в спае двух разнородных проводников (эффект Зеебека).</div>'
            +'<div style="margin-bottom:8px;"><b style="'+b+'">Этот датчик:</b> '+sel.name+'; электроды: '+sel.meta+'; диапазон НСХ: '+sel.range.min+'…'+sel.range.max+' °C; E(0 °C) = 0 мВ (опорный спай 0 °C).</div>'
            +'<div style="margin-bottom:8px;"><b style="'+b+'">НСХ термопар:</b> стандартизированы ГОСТ Р 8.585-2001; расчёт — полиномы НИСТ ITS-90 (SRD 60): E(t) = Σ cᵢ·tⁱ.</div>'
            +'<div style="margin-bottom:8px;"><b style="'+b+'">Наиболее распространённые типы:</b> ТХА (K), ТЖК (J), ТМК (T), ТНН (N), ТХКн (E), ТПП (R), ТПП (S), ТПР (B).</div>'
            +'<div><b style="'+b+'">Нормативные документы:</b> ГОСТ Р 8.585-2001 (ТП).</div>';
    }
    function calcTempSensor(){
        // Task 372: датчик — из состояния страницы карточек (раньше —
        // выпадающие списки temp_sensor_type / temp_rtd_type / temp_tc_type)
        let sel=tempSensorFindByKey(tempSensorKey);
        if(!sel){showToast('Выберите датчик температуры');return;}
        let type=sel.kind;'''

rep(OLD, NEW, 'JS: каталог/карточки/openTempSensor/справка + head calcTempSensor')

# 3b. ветка ТС: rtdType из состояния (якорь с комментарием — паттерн
#     «if(type==='rtd'){let rtdType=…}» есть и в getTempSensorRange,
#     но там нет комментария Task 371)
rep('''        if(type==='rtd'){
            let rtdType=document.getElementById('temp_rtd_type').value;
            // Task 371: карта типов ТС — общая с блоком''',
    '''        if(type==='rtd'){
            let rtdType=sel.key;
            // Task 371: карта типов ТС — общая с блоком''',
    'JS: ветка ТС rtdType=sel.key')

# 3c. ветка ТП: tcType из состояния, имена из карты
rep('''        } else {
            let tcType=document.getElementById('temp_tc_type').value;
            let names={K:'ТХА (K)',J:'ТЖК (J)',T:'ТМК (T)',N:'ТНН (N)',E:'ТХКн (E)',R:'ТПП (R)',S:'ТПП (S)',B:'ТПР (B)'};''',
    '''        } else {
            let tcType=sel.tc;
            let names=getTcSensorMap();''',
    'JS: ветка ТП tcType=sel.tc + getTcSensorMap()')

# 3d. getTempSensorRange — из каталога (единый источник диапазонов)
rep('''    // Task 371: диапазоны НСХ по типу датчика — границы применимости
    // формул (и проверка введённых произвольных значений)
    function getTempSensorRange(){
        let type=document.getElementById('temp_sensor_type').value;
        if(type==='rtd'){
            let rtdType=document.getElementById('temp_rtd_type').value;
            if(rtdType.indexOf('cu')===0){ return {min:-50,max:200}; }
            return {min:-200,max:850};
        }
        let tcType=document.getElementById('temp_tc_type').value;
        let r={K:[-270,1372],J:[-210,1200],T:[-270,400],N:[-270,1300],E:[-270,1000],R:[-50,1768],S:[-50,1768],B:[0,1820]}[tcType];
        return r?{min:r[0],max:r[1]}:{min:-50,max:1768};
    }''',
    '''    // Task 371/372: диапазоны НСХ по типу датчика — границы применимости
    // формул (и проверка введённых произвольных значений). Task 372:
    // единый источник диапазонов — каталог getTempSensorCatalog();
    // датчик берётся из состояния страницы карточек.
    function getTempSensorRange(){
        let sel=tempSensorFindByKey(tempSensorKey);
        if(sel){ return {min:sel.range.min,max:sel.range.max}; }
        return {min:-50,max:200};
    }''',
    'JS: getTempSensorRange из каталога')

# 3e. tempCalcForwardValue — из состояния
rep('''    // Task 371: прямое значение по температуре из ТЕКУЩЕЙ формы
    // (R(t) для ТС, E(t) для ТП) — как queryFromScaleLive читает поля живьём
    function tempCalcForwardValue(t){
        let type=document.getElementById('temp_sensor_type').value;
        if(type==='rtd'){
            let sd=getRtdSensorMap()[document.getElementById('temp_rtd_type').value];
            if(!sd){return null;}
            return sd.nsc==='cu'?calcCuResistance(t,sd.r0,sd.alpha):calcRtdResistance(t,sd.r0,sd.nsc);
        }
        return calcTcVoltage(t,document.getElementById('temp_tc_type').value);
    }''',
    '''    // Task 371/372: прямое значение по температуре ВЫБРАННОГО датчика
    // (R(t) для ТС, E(t) для ТП) — как queryFromScaleLive читает поля живьём
    function tempCalcForwardValue(t){
        let sel=tempSensorFindByKey(tempSensorKey);
        if(!sel){return null;}
        if(sel.kind==='rtd'){
            let sd=getRtdSensorMap()[sel.key];
            if(!sd){return null;}
            return sd.nsc==='cu'?calcCuResistance(t,sd.r0,sd.alpha):calcRtdResistance(t,sd.r0,sd.nsc);
        }
        return calcTcVoltage(t,sel.tc);
    }''',
    'JS: tempCalcForwardValue из состояния')

# 3f. tempQueryFromValue: единица Ом/мВ — по выбранному датчику
rep('''        let type=document.getElementById('temp_sensor_type').value;
        let unit=type==='rtd'?'Ом':'мВ';''',
    '''        // Task 372: единица — по выбранному датчику (карточка), а не select
        let selQ=tempSensorFindByKey(tempSensorKey);
        let unit=(selQ&&selQ.kind==='rtd')?'Ом':'мВ';''',
    'JS: tempQueryFromValue единица из состояния')

# 3g. устаревший комментарий у getOptgroupHints (temp_rtd_type удалён)
rep('''        // Map: select element → current optgroup hint for its options
        // Used for temp_rtd_type where optgroup data is shown inline''',
    '''        // Map: select element → current optgroup hint for its options
        // Used for selects with optgroups (e.g. buoy_signal_type) where
        // optgroup data is shown inline (Task 372: temp_rtd_type удалён)''',
    'JS: комментарий getOptgroupHints')

# ============================================================
# 4. navigateTo — хуки страницы карточек и страницы датчика
# ============================================================
rep('''        if (page === 'project-group') { setTimeout(() => { if (typeof projectsRenderGroup === 'function') projectsRenderGroup(); }, 30); }''',
    '''        if (page === 'project-group') { setTimeout(() => { if (typeof projectsRenderGroup === 'function') projectsRenderGroup(); }, 30); }
        // Task 372: «Датчики температуры» — карточки списка рендерятся при
        // открытии страницы; детальная страница без выбранного датчика
        // (прямой переход по hash после перезагрузки) уходит на список.
        if (page === 'temp-sensor-view' && !tempSensorKey) { page = 'temp-sensors'; }
        if (page === 'temp-sensors') { if (typeof renderTempSensorCards === 'function') renderTempSensorCards(); }''',
    'navigateTo: хуки temp-sensor-view/temp-sensors')

# ============================================================
# 5. Реестры страниц
# ============================================================
rep("        'temp-sensors':     'calc-kipa',",
    """        'temp-sensors':     'calc-kipa',
        'temp-sensor-view': 'temp-sensors',   // Task 372: страница датчика""",
    'PAGE_PARENTS: temp-sensor-view')

rep("        'temp-sensors':     'Датчики температуры',",
    """        'temp-sensors':     'Датчики температуры',
        'temp-sensor-view': 'Датчик температуры',   // Task 372""",
    'PAGE_LABELS: temp-sensor-view')

rep("                    'temp-sensors', 'orifice-select', 'circuit-breaker',",
    "                    'temp-sensors', 'temp-sensor-view', 'orifice-select', 'circuit-breaker',",
    'Топ-бар: temp-sensor-view в calculators')

rep("                      'buoy-select', 'buoy-calc', 'temp-sensors',",
    "                      'buoy-select', 'buoy-calc', 'temp-sensors', 'temp-sensor-view',",
    'KipAuth._CALC_PAGES: temp-sensor-view')

# ============================================================
# 6. Саблейблы: меню КИП и А + SUBSECTIONS (реестр закреплений)
# ============================================================
rep('<div class="menu-btn-sublabel">Расчёт R и мВ по температуре (°C)</div>',
    '<div class="menu-btn-sublabel">Термометры сопротивления и термопары</div>',
    'Меню calc-kipa: саблейбл temp-sensors')

rep("sublabel: 'Расчёт R и мВ по температуре (°C)',",
    "sublabel: 'Термометры сопротивления и термопары',",
    'SUBSECTIONS: саблейбл temp-sensors')

# ============================================================
# Контроль и запись
# ============================================================
# Функциональных ссылок на старые select-ы больше нет (в комментариях
# имена могут упоминаться как история — это допустимо)
for gone in [
    "getElementById('temp_sensor_type'", "getElementById('temp_rtd_type'",
    "getElementById('temp_tc_type'", 'id="temp_sensor_type"', 'id="temp_rtd_type"',
    'id="temp_tc_type"', 'id="rtd_options"', 'id="tc_options"',
    'function updateTempSensorOptions', 'updateTempSensorOptions()',
]:
    assert gone not in src, 'осталась функциональная ссылка: ' + gone
assert src.count('id="page-temp-sensor-view"') == 1
assert src.count('id="page-temp-sensors"') == 1
assert 'class="page-content conv-3col-page">' in src[src.index('id="page-temp-sensor-view"'):src.index('id="page-temp-sensor-view"') + 100]
# шаблон onclick в карточках (JS-конкатенация с экранированными кавычками)
assert "openTempSensor(\\''+s.key+'\\')" in src, 'нет шаблона onclick карточек'
assert src.count('Task 372') >= 14, 'мало маркеров Task 372: %d' % src.count('Task 372')

open(PATH, 'w', encoding='utf-8').write(src)
print('OK: %d правок применено' % len(edits_done))
for t in edits_done:
    print('  -', t)
print('Размер: %d → %d байт (+%d)' % (orig_len, len(src), len(src) - orig_len))
