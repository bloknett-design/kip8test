#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 499 (kip8test): подсказки диапазонов — в поля ввода; диапазон 50М.

Заявка пользователя:
  «Подсказки диапазонов впиши непосредственно в поля ввода, бледным
   текстом, вместо предложения "Например: 55" и так далее. И проверь
   у 50М (Cu50) α = 0,00428 °C⁻¹ диапазон по моему -180...200 °C.»

Верификация диапазона 50М (диапазон ПОДТВЕРЖДЁН, расширяем):
  - ГОСТ 6651-2009, формула 5.2.3 (медь, α = 0,00428): «Для диапазона
    измерений от минус 180 °C до 0 °C: Rt = R₀[1 + At + B·t·(t+6,7 °C) +
    C·t³]», A = 4,28·10⁻³, B = −6,2032·10⁻⁷, C = 8,5154·10⁻¹⁰; для
    0…+200 °C — линейная Rt = R₀(1 + At). Источник: полный текст
    ГОСТ (проект = финальные формулы, temperatures.ru/pdf/GOST6651.pdf).
  - Таблица А.3 ГОСТ (медь, R₀ = 100, α = 0,00428) начинается с
    −180 °C (20,53 Ом) и заканчивается +200 °C (185,60 Ом) — сборник
    temperatures.ru/pdf/nshts.pdf; сверка формулы с таблицей А.3:
    −180→20,53; −170→25,10; −120→47,65; −100→56,54; −50→78,46;
    0→100,00; +200→185,60 (совпадение до 0,01 Ом).
  - НАЙДЕНА и исправлена неточность: calcCuResistance была линейной
    при ЛЮБОЙ температуре — ниже 0 °C расходилась с ГОСТ (при −50 °C
    +0,14 Ом: 78,60 вместо 78,46; при −180 °C +2,43 Ом: 22,96 вместо
    20,53).
  - Медь W100 = 1,426 (α = 0,00426): в ГОСТ 6651-2009 представлена
    только обратной функцией (прил. Б.3, −50…+200) — диапазон
    каталога НЕ менялся (−50…+200), НСХ остаётся линейной.

Изменения:
  index.html:
    R1 calcCuResistance: ниже 0 °C для α = 0,00428 — формула 5.2.3
       ГОСТ 6651-2009 (A/B/C-коэффициенты, член B·t·(t+6,7) + C·t³).
    R2 getTempSensorCatalog: Cu α = 0,00428 — диапазон НСХ −180…+200
       (таблица А.3 / формула 5.2.3); Cu α = 0,00426 — прежний
       −50…+200; комментарий 499 к каталогу.
    R3 openTempSensor: подсказки диапазонов — ПЛЕЙСХОЛДЕРЫ полей ППР
       (бледный текст, CSS .ts-calc-field::placeholder) вместо
       предложений «Например: 55» / «Например: 61,8» / «Например: 2,2»;
       блок заполнения div-подсказок Task 498 удалён.
    R4 HTML панели ППР: div.ts-calc-range ×2 и статические
       placeholder «Например: …» удалены.
    R5 CSS: правила .ts-calc-range удалены (подсказки теперь в полях;
       бледный цвет плейсхолдера — прежнее правило Task 494).
    R6 getRtdSensorMap: строки формул Cu α = 0,00428 — с веткой ниже
       0 °C по ГОСТ.
    R7 tempSensorInfoHtml: строка «Формулы ТС» — с формулой 5.2.3
       ГОСТ для меди ниже 0 °C.
  sw.js:
    R8 kipia-test-v722 → v723 + комментарий Task 499.
"""
import io
import sys

IDX = '/home/z/my-project/kip8test/index.html'
SW = '/home/z/my-project/kip8test/sw.js'


def apply(path, edits):
    s = io.open(path, encoding='utf-8').read()
    for name, old, new in edits:
        n = s.count(old)
        assert n == 1, 'ЯКОРЬ %s: вхождений %d (ожидалось 1)' % (name, n)
        s = s.replace(old, new)
        print('  OK %s' % name)
    io.open(path, 'w', encoding='utf-8').write(s)


# ---------------------------------------------------------- index.html --
idx_edits = []

# R1: calcCuResistance — формула 5.2.3 ГОСТ 6651-2009 ниже 0 °C (α 0,00428)
idx_edits.append(('R1 calcCuResistance ГОСТ 5.2.3',
"""    function calcCuResistance(t,r0,alpha){
        return r0*(1+alpha*t);
    }
""",
"""    // Task 499 (заявка: «проверь у 50М (Cu50) α = 0,00428 °C⁻¹
    // диапазон — по моему −180…200 °C»): НСХ меди W100 = 1,428 ниже
    // 0 °C НЕ линейна — формула 5.2.3 ГОСТ 6651-2009: R(t) =
    // R₀·[1 + A·t + B·t·(t+6,7 °C) + C·t³], A = 4,28·10⁻³ °C⁻¹,
    // B = −6,2032·10⁻⁷ °C⁻², C = 8,5154·10⁻¹⁰ °C⁻³ (при t ≥ 0 —
    // линейная R₀(1+At), формула 5.2.3/6). Контроль по таблице А.3
    // ГОСТ (R₀ = 100): −180 → 20,53; −170 → 25,10; −120 → 47,65;
    // −100 → 56,54; −50 → 78,46; 0 → 100,00. Раньше (линейная при
    // любой t) ниже 0 °C расходилась с ГОСТ: при −50 °C +0,14 Ом
    // (78,60 вместо 78,46), при −180 °C +2,43 Ом (22,96 вместо 20,53).
    // Медь W100 = 1,426 (α = 0,00426) в ГОСТ представлена только
    // обратной функцией (прил. Б.3, −50…+200) — для неё НСХ
    // остаётся линейной, ветка ГОСТ не применяется.
    function calcCuResistance(t,r0,alpha){
        // Task 499: ветка формулы 5.2.3 — только α = 0,00428 и t < 0
        if(t<0 && Math.abs(alpha-0.00428)<1e-9){
            let A=4.28e-3, B=-6.2032e-7, C=8.5154e-10;
            return r0*(1+A*t+B*t*(t+6.7)+C*t*t*t);
        }
        return r0*(1+alpha*t);
    }
"""))

# R2: каталог — диапазон Cu α = 0,00428 расширен до −180…+200
idx_edits.append(('R2 каталог Cu −180…+200',
"""            list.push({key:k,kind:'rtd',name:sd.name,meta:'R₀ = '+sd.r0+' Ом · '+alpha,range:isCu?{min:-50,max:200}:{min:-200,max:850}});
""",
"""            // Task 499 (заявка: сверка диапазона 50М): медь W100 = 1,428
            // (α = 0,00428) — НСХ −180…+200 (таблица А.3 / формула 5.2.3
            // ГОСТ 6651-2009, заявка подтверждена); W100 = 1,426 —
            // прежние −50…+200 (в ГОСТ — только обратная функция, Б.3).
            let rng499=isCu?((Math.abs(sd.alpha-0.00428)<1e-9)?{min:-180,max:200}:{min:-50,max:200}):{min:-200,max:850};
            list.push({key:k,kind:'rtd',name:sd.name,meta:'R₀ = '+sd.r0+' Ом · '+alpha,range:rng499});
"""))

# R2b: комментарий Task 499 над каталогом
idx_edits.append(('R2b комментарий каталога',
"""    // по таблице А.2.
    function getTempSensorCatalog(){
""",
"""    // по таблице А.2.
    // Task 499 (заявка: «проверь у 50М (Cu50) α = 0,00428 °C⁻¹
    // диапазон, по моему −180…200 °C»): УТОЧНЕНО по ГОСТ 6651-2009 —
    // НСХ меди W100 = 1,428 задана формулой 5.2.3 «от минус 180 до
    // 0 °C» + линейной «от 0 до 200 °C», таблица А.3 начинается с
    // −180 °C (R = 20,53 Ом при R₀ = 100): диапазон каталога для
    // α = 0,00428 расширен до −180…+200, НСХ ниже 0 °C нелинейна —
    // см. calcCuResistance (Task 499). Медь W100 = 1,426 (α = 0,00426)
    // в ГОСТ представлена только обратной функцией (прил. Б.3,
    // −50…+200) — диапазон прежний. Pt и ТП — без изменений.
    function getTempSensorCatalog(){
"""))

# R3: openTempSensor — подсказки диапазонов ПЛЕЙСХОЛДЕРАМИ полей
idx_edits.append(('R3 openTempSensor плейсхолдеры',
"""        // Task 373: панель «Расчёт произвольных значений» (статичная,
        // над формой выбора) — подпись второго поля и пример под тип
        // датчика, оба поля очищены
        let vLab=document.getElementById('tempQueryValLabel');
        let vInp=document.getElementById('tempQueryVal');
        let tInp=document.getElementById('tempQueryTemp');
        if(sel.kind==='rtd'){
            if(vLab){vLab.textContent='Сопротивление R(t), Ом';}
            if(vInp){vInp.placeholder='Например: 61,8';}
        }else{
            if(vLab){vLab.textContent='Термо-ЭДС E(t), мВ';}
            if(vInp){vInp.placeholder='Например: 2,2';}
        }
        if(tInp){tInp.value='';}
        if(vInp){vInp.value='';}
        // Task 498 (заявка): пределы НСХ датчика — в полях ввода
        // произвольного расчёта: под полем температуры — в градусах
        // Цельсия («−50…200 °C», целые, как на карточках каталога),
        // под полем значения — в единицах измерения датчика
        // («39,3…92,8 Ом» для ТС, мВ для ТП). Границы — из каталога
        // (единый источник диапазонов), значения для Ом/мВ — через
        // НСХ (tempCalcForwardValue) на границах.
        let tR498=document.getElementById('tempQueryTempRange');
        let vR498=document.getElementById('tempQueryValRange');
        let rng498=getTempSensorRange();
        let fmtI498=function(v){return String(v).replace('-','−');};
        let fmtM498=function(v){return formatNumber(v).replace('-','−');};
        if(tR498){tR498.textContent=fmtI498(rng498.min)+'…'+fmtI498(rng498.max)+' °C';}
        if(vR498){
            let vmin498=tempCalcForwardValue(rng498.min);
            let vmax498=tempCalcForwardValue(rng498.max);
            if(vmin498!==null&&vmax498!==null&&isFinite(vmin498)&&isFinite(vmax498)){
                vR498.textContent=fmtM498(vmin498)+'…'+fmtM498(vmax498)+' '+((sel.kind==='rtd')?'Ом':'мВ');
            }
        }
""",
"""        // Task 373: панель «Расчёт произвольных значений» (статичная,
        // над формой выбора) — подпись второго поля под тип датчика,
        // оба поля очищены
        let vLab=document.getElementById('tempQueryValLabel');
        let vInp=document.getElementById('tempQueryVal');
        let tInp=document.getElementById('tempQueryTemp');
        if(sel.kind==='rtd'){
            if(vLab){vLab.textContent='Сопротивление R(t), Ом';}
        }else{
            if(vLab){vLab.textContent='Термо-ЭДС E(t), мВ';}
        }
        if(tInp){tInp.value='';}
        if(vInp){vInp.value='';}
        // Task 499 (заявка: «подсказки диапазонов впиши непосредственно
        // в поля ввода, бледным текстом, вместо предложения "Например: 55"»):
        // пределы НСХ датчика — ПЛЕЙСХОЛДЕРЫ полей произвольного расчёта
        // (бледный текст — прежнее правило .ts-calc-field::placeholder,
        // Task 494): у температуры — в градусах Цельсия («−180…200 °C»,
        // целые, как на карточках каталога), у значения — в единицах
        // измерения датчика («10,2642…92,8 Ом» для ТС, мВ для ТП).
        // Прежние предложения «Например: 55» / «Например: 61,8» /
        // «Например: 2,2» убраны; строки-подсказки под полями
        // (div ts-calc-range, Task 498) удалены — информация теперь
        // в самих полях. Границы — из каталога (единый источник
        // диапазонов), значения для Ом/мВ — через НСХ
        // (tempCalcForwardValue) на границах.
        let rng499=getTempSensorRange();
        let fmtI499=function(v){return String(v).replace('-','−');};
        let fmtM499=function(v){return formatNumber(v).replace('-','−');};
        if(tInp){tInp.placeholder=fmtI499(rng499.min)+'…'+fmtI499(rng499.max)+' °C';}
        if(vInp){
            let vmin499=tempCalcForwardValue(rng499.min);
            let vmax499=tempCalcForwardValue(rng499.max);
            if(vmin499!==null&&vmax499!==null&&isFinite(vmin499)&&isFinite(vmax499)){
                vInp.placeholder=fmtM499(vmin499)+'…'+fmtM499(vmax499)+' '+((sel.kind==='rtd')?'Ом':'мВ');
            }else{
                vInp.placeholder='';
            }
        }
"""))

# R4: HTML — div.ts-calc-range ×2 и «Например: …» удалены
idx_edits.append(('R4 HTML панели ППР',
"""                        <input type="text" inputmode="numeric" id="tempQueryTemp" class="scale-field ts-calc-field" placeholder="Например: 55" oninput="tempQueryFromTemp()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">
                        <!-- Task 498 (заявка): под каждым полем ППР — пределы
                             НСХ выбранного датчика: у температуры — в градусах
                             Цельсия («−50…200 °C»), у значения — в единицах
                             измерения датчика («39,3…92,8 Ом» / мВ). Заполняет
                             openTempSensor() по каталогу (id tempQueryTempRange /
                             tempQueryValRange), оформление — класс ts-calc-range. -->
                        <div class="ts-calc-range" id="tempQueryTempRange"></div>
                        <div class="scale-form-label" id="tempQueryValLabel">Сопротивление R(t), Ом</div>
                        <input type="text" inputmode="numeric" id="tempQueryVal" class="scale-field ts-calc-field" placeholder="Например: 61,8" oninput="tempQueryFromValue()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">
                        <div class="ts-calc-range" id="tempQueryValRange"></div>
                    </div>
""",
"""                        <!-- Task 499 (заявка: «подсказки диапазонов впиши
                             непосредственно в поля ввода, бледным текстом,
                             вместо предложения "Например: 55" и так далее»):
                             пределы НСХ выбранного датчика — ПЛЕЙСХОЛДЕРЫ
                             полей (бледный цвет — CSS
                             .ts-calc-field::placeholder, Task 494): у
                             температуры — «−180…200 °C», у значения —
                             «10,2642…92,8 Ом» / мВ. Заполняет
                             openTempSensor() по каталогу; прежние
                             «Например: 55» / «Например: 61,8» и строки
                             под полями (div ts-calc-range, Task 498)
                             удалены. -->
                        <input type="text" inputmode="numeric" id="tempQueryTemp" class="scale-field ts-calc-field" oninput="tempQueryFromTemp()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">
                        <div class="scale-form-label" id="tempQueryValLabel">Сопротивление R(t), Ом</div>
                        <input type="text" inputmode="numeric" id="tempQueryVal" class="scale-field ts-calc-field" oninput="tempQueryFromValue()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">
                    </div>
"""))

# R5: CSS — правила .ts-calc-range удалены
idx_edits.append(('R5 CSS ts-calc-range удалён',
"""    /* Task 498 (заявка): пределы НСХ под полями произвольного расчёта —
       класс ts-calc-range (id tempQueryTempRange / tempQueryValRange,
       заполняет openTempSensor): под полем температуры — в °C, под
       полем значения — в Ом (ТС) / мВ (ТП). Прижаты к «своему» полю
       (верхний отрицательный отступ компенсирует нижний отступ поля),
       у последней строки панели нижний отступ убран. */
    .ts-calc-range { font-size: 11px; font-weight: 600; color: rgba(255, 255, 255, 0.52); margin: -8px 2px 12px; line-height: 1.4; letter-spacing: -0.1px; }
    .ts-calc-panel .ts-calc-range:last-child { margin-bottom: 0; }
    [data-theme="light"] .ts-calc-range { color: rgba(20, 20, 19, 0.55); }
""",
"""    /* Task 499 (заявка: «подсказки диапазонов впиши непосредственно
       в поля ввода, бледным текстом»): пределы НСХ в полях ППР —
       ПЛЕЙСХОЛДЕРАМИ («−180…200 °C» / «10,2642…92,8 Ом» / мВ,
       заполняет openTempSensor); бледный цвет — прежнее правило
       .ts-calc-field::placeholder (Task 494). Строки-подсказки
       .ts-calc-range (Task 498) под полями УБРАНЫ. */
"""))

# R6: getRtdSensorMap — строки формул Cu α = 0,00428
idx_edits.append(('R6 формулы 50М/100М (0,00428)',
"""            cu50_1428:{r0:50,alpha:0.00428,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
            cu100_1428:{r0:100,alpha:0.00428,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
""",
"""            cu50_1428:{r0:50,alpha:0.00428,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t) при t ≥ 0; при t < 0 по ГОСТ 6651-2009 (ф. 5.2.3): R₀[1 + At + Bt(t+6,7 °C) + Ct³]'},
            cu100_1428:{r0:100,alpha:0.00428,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t) при t ≥ 0; при t < 0 по ГОСТ 6651-2009 (ф. 5.2.3): R₀[1 + At + Bt(t+6,7 °C) + Ct³]'},
"""))

# R7: tempSensorInfoHtml — строка «Формулы ТС»
idx_edits.append(('R7 инфо «Формулы ТС»',
"""                +'<div style="margin-bottom:8px;"><b style="'+b+'">Формулы ТС:</b> медные: R(t) = R₀·(1 + α·t); платиновые: R(t) = R₀·[1 + A·t + B·t² + C·(t−100)·t³] — член C добавляется ниже 0 °C.</div>'
""",
"""                +'<div style="margin-bottom:8px;"><b style="'+b+'">Формулы ТС:</b> медные (α = 0,00428): при t ≥ 0 — R(t) = R₀·(1 + α·t); при t < 0 — R(t) = R₀·[1 + A·t + B·t·(t+6,7 °C) + C·t³], A = 4,28·10⁻³, B = −6,2032·10⁻⁷, C = 8,5154·10⁻¹⁰ (ГОСТ 6651-2009, ф. 5.2.3); платиновые: R(t) = R₀·[1 + A·t + B·t² + C·(t−100)·t³] — член C добавляется ниже 0 °C.</div>'
"""))

print('=== index.html ===')
apply(IDX, idx_edits)

# --------------------------------------------------------------- sw.js --
sw_edits = []
sw_edits.append(('R8 sw.js версия + комментарий',
"""const CACHE_VERSION = 'kipia-test-v722';
""",
"""// Task 499: подсказки диапазонов НСХ — непосредственно в поля
// ввода произвольного расчёта, бледным текстом плейсхолдера
// («−180…200 °C» / «10,2642…92,8 Ом» / мВ) вместо «Например: 55»;
// диапазон 50М/100М (Cu, α = 0,00428) расширен до −180…+200 по
// таблице А.3 / формуле 5.2.3 ГОСТ 6651-2009; НСХ меди ниже 0 °C
// нелинейна — calcCuResistance по ф. 5.2.3. Клиент-only.
const CACHE_VERSION = 'kipia-test-v723';
"""))

print('=== sw.js ===')
apply(SW, sw_edits)

print('Task 499: применено.')
