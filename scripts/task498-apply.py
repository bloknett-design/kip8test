#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 498 (kip8test): «Датчики температуры» — пределы измерения.

Заявка пользователя:
  (1) посмотреть пределы измерения датчиков температуры и скорректиро-
      вать неточности;
  (2) указать пределы в °C и в единицах измерения (Ом/мВ) в полях
      ввода произвольного расчёта;
  (3) в баре с названием страницы расчёта — только тип датчика
      (например, «50М (Cu50) α = 0,00428 °C⁻¹»), шрифт крупнее.

Верификация пределов (сверка с первоисточниками):
  - Cu 50М/100М (α 0,00428/0,00426): −50…+200 °C — область обратного
    преобразования по ГОСТ 6651-2009 (приложение Б); формула линейная
    R(t)=R₀(1+αt) — официальная формула НСХ меди. БЕЗ изменений.
  - Pt (50П/100П/Pt100/Pt1000): −200…+850 °C — таблицы А.1/А.2
    ГОСТ 6651-2009 / IEC 60751. БЕЗ изменений.
  - ТП: таблицы НИСТ ITS-90 = ГОСТ Р 8.585-2001 (K −270…1372,
    J −210…1200, T −270…400, N −270…1300, E −270…1000, L −200…800,
    R/S −50…1768, B 0…1820). БЕЗ изменений.
  - НАЙДЕНА И ИСПРАВЛЕНА неточность: calcRtdResistance ветка pt1391
    не учитывала член C(t−100)t³ ниже 0 °C и использовала округлённые
    коэффициенты (A=3,96847e-3, B=−5,84e-7). По таблице А.2 ГОСТ
    6651-2009: A=3,969e-3, B=−5,841e-7, C=−4,330e-12 — сверка:
    −200→17,24; −150→38,79; −100→59,64; −50→80,00; 70→127,50;
    850→395,16 Ом (100П). Раньше при −200 °C выдавало 18,29.

Изменения:
  index.html:
    R1 calcRtdResistance: pt1391 — новые A/B + член C ниже 0 °C.
    R2 getRtdSensorMap: строки формул pt50_1391/pt100_1391.
    R3 getTempSensorCatalog: комментарий сверки (диапазоны НЕ менялись).
    R4 openTempSensor: заголовок — только тип датчика (ТС с α, ТП имя).
    R5 openTempSensor: пределы в подсказках полей ППР (ts-calc-range).
    R6 HTML панели ППР: два div.ts-calc-range (+комментарий).
    R7 CSS: .ts-calc-range + #tempSensorViewTitle (21px/17px scrolled).
  sw.js:
    R8 kipia-test-v721 → v722 + комментарий Task 498.
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

# R1: calcRtdResistance — pt1391 по таблице А.2 ГОСТ 6651-2009
idx_edits.append(('R1 calcRtdResistance pt1391',
"""        } else if(nsc==='pt1391'){
            let A=3.96847e-3, B=-5.84e-7;
            if(t>=0){ return r0*(1+A*t+B*t*t); }
            else { return r0*(1+A*t+B*t*t); }
        }
""",
"""        } else if(nsc==='pt1391'){
            // Task 498 (заявка: сверка пределов и корректировка
            // неточностей): коэффициенты выровнены по таблице А.2
            // ГОСТ 6651-2009 (платина W100 = 1,391): A = 3,969·10⁻³,
            // B = −5,841·10⁻⁷; ниже 0 °C добавлен член C·(t−100)·t³
            // с C = −4,330·10⁻¹² (аналогично pt1385). Раньше ниже 0 °C
            // член C не учитывался, а B был округлён до −5,84·10⁻⁷
            // (A = 3,96847·10⁻³) — значения 100П/50П при отрицательных
            // температурах расходились с таблицей А.2: при −200 °C на
            // ~1,05 Ом (18,29 вместо 17,24), при −100 °C на ~0,09 Ом.
            // Контроль сверки с А.2 (R₀ = 100 Ом): −200 → 17,24;
            // −150 → 38,79; −100 → 59,64; −50 → 80,00; 0 → 100,00;
            // 70 → 127,50; 100 → 139,11; 850 → 395,16.
            let A=3.969e-3, B=-5.841e-7, C=-4.330e-12;
            if(t>=0){ return r0*(1+A*t+B*t*t); }
            else { return r0*(1+A*t+B*t*t+C*(t-100)*t*t*t); }
        }
"""))

# R2: getRtdSensorMap — строки формул pt1391 (2 шт.)
idx_edits.append(('R2a формула 50П',
"pt50_1391:{r0:50,name:'50П (Pt50)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},",
"pt50_1391:{r0:50,name:'50П (Pt50)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³] при t<0; A=3,969·10⁻³, B=−5,841·10⁻⁷, C=−4,330·10⁻¹²'},"))

idx_edits.append(('R2b формула 100П',
"pt100_1391:{r0:100,name:'100П (Pt100)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},",
"pt100_1391:{r0:100,name:'100П (Pt100)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³] при t<0; A=3,969·10⁻³, B=−5,841·10⁻⁷, C=−4,330·10⁻¹²'},"))

# R3: getTempSensorCatalog — комментарий сверки пределов
idx_edits.append(('R3 комментарий каталога',
"""    function getTempSensorCatalog(){
""",
"""    // Task 498 (заявка: «посмотри пределы измерения и скорректируй
    // неточности»): пределы НСХ каталога СВЕРЕНЫ с первоисточниками и
    // подтверждены — диапазоны НЕ менялись: ТС Cu (50М/100М, α 0,00428
    // и 0,00426) — −50…+200 °C (линейная формула НСХ меди R(t)=R₀(1+αt);
    // область обратного преобразования по ГОСТ 6651-2009, приложение Б);
    // ТС Pt (50П/100П/Pt100/Pt1000) — −200…+850 °C (таблицы А.1/А.2
    // ГОСТ 6651-2009 / IEC 60751); ТП — НИСТ ITS-90 (SRD 60) =
    // ГОСТ Р 8.585-2001: K −270…1372, J −210…1200, T −270…400,
    // N −270…1300, E −270…1000, L −200…800, R и S −50…1768,
    // B 0…1820 °C. Исправлена формула pt1391 ниже 0 °C (см.
    // calcRtdResistance, Task 498) — значения 100П/50П теперь точно
    // по таблице А.2.
    function getTempSensorCatalog(){
"""))

# R4: openTempSensor — заголовок только тип датчика
idx_edits.append(('R4 заголовок страницы',
"""        let title=document.getElementById('tempSensorViewTitle');
        if(title){title.textContent=sel.name+(sel.kind==='rtd'?' — термометр сопротивления':' — термопара');}
""",
"""        let title=document.getElementById('tempSensorViewTitle');
        // Task 498 (заявка): в баре страницы — ТОЛЬКО тип датчика:
        // ТС — «градуировка (аналог) α = … °C⁻¹» (например,
        // «50М (Cu50) α = 0,00428 °C⁻¹»; α различает одинаковые
        // градуировки 50М/100М), ТП — наименование («ТХА (K)»).
        // Пояснения «— термометр сопротивления»/«— термопара» убраны;
        // шрифт заголовка крупнее (CSS #tempSensorViewTitle, 21px).
        if(title){
            let t498=sel.name;
            if(sel.kind==='rtd'){
                let sd498=getRtdSensorMap()[sel.key]||{};
                if(sd498.nsc==='cu'){
                    t498+=' α = '+String(sd498.alpha).replace('.',',')+' °C⁻¹';
                }else if(sd498.nsc==='pt1391'){
                    t498+=' α = 0,00391 °C⁻¹';
                }else if(sd498.nsc==='pt1385'){
                    t498+=' α = 0,00385 °C⁻¹';
                }
            }
            title.textContent=t498;
        }
"""))

# R5: openTempSensor — пределы в подсказках полей ППР
idx_edits.append(('R5 пределы в полях ППР',
"""        if(tInp){tInp.value='';}
        if(vInp){vInp.value='';}
        // Task 373: звезда избранного в шапке страницы датчика
""",
"""        if(tInp){tInp.value='';}
        if(vInp){vInp.value='';}
        // Task 498 (заявка): пределы НСХ датчика — в полях ввода
        // произвольного расчёта: под полем температуры — в градусах
        // Цельсия («−50…200 °C»), под полем значения — в единицах
        // измерения датчика («39,3…92,8 Ом» для ТС, мВ для ТП).
        // Границы — из каталога (единый источник диапазонов), значения
        // для Ом/мВ — через НСХ (tempCalcForwardValue) на границах.
        let tR498=document.getElementById('tempQueryTempRange');
        let vR498=document.getElementById('tempQueryValRange');
        let rng498=getTempSensorRange();
        let fmtM498=function(v){return formatNumber(v).replace('-','−');};
        if(tR498){tR498.textContent=fmtM498(rng498.min)+'…'+fmtM498(rng498.max)+' °C';}
        if(vR498){
            let vmin498=tempCalcForwardValue(rng498.min);
            let vmax498=tempCalcForwardValue(rng498.max);
            if(vmin498!==null&&vmax498!==null&&isFinite(vmin498)&&isFinite(vmax498)){
                vR498.textContent=fmtM498(vmin498)+'…'+fmtM498(vmax498)+' '+((sel.kind==='rtd')?'Ом':'мВ');
            }
        }
        // Task 373: звезда избранного в шапке страницы датчика
"""))

# R6: HTML — div.ts-calc-range под обоими полями ППР
idx_edits.append(('R6 HTML подсказки ППР',
"""                        <input type="text" inputmode="numeric" id="tempQueryTemp" class="scale-field ts-calc-field" placeholder="Например: 55" oninput="tempQueryFromTemp()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">
                        <div class="scale-form-label" id="tempQueryValLabel">Сопротивление R(t), Ом</div>
                        <input type="text" inputmode="numeric" id="tempQueryVal" class="scale-field ts-calc-field" placeholder="Например: 61,8" oninput="tempQueryFromValue()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">
                    </div>
""",
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
"""))

# R7: CSS — .ts-calc-range + #tempSensorViewTitle
idx_edits.append(('R7 CSS',
"""    [data-theme="light"] .ts-calc-panel.ts-calc-inset { background-color: rgba(21, 54, 83, 0.08); background-image: none; border-color: rgba(43, 111, 163, 0.35); box-shadow: inset 0 2px 8px rgba(21, 54, 83, 0.18), inset 0 -1px 0 rgba(255, 255, 255, 0.7); }
""",
"""    [data-theme="light"] .ts-calc-panel.ts-calc-inset { background-color: rgba(21, 54, 83, 0.08); background-image: none; border-color: rgba(43, 111, 163, 0.35); box-shadow: inset 0 2px 8px rgba(21, 54, 83, 0.18), inset 0 -1px 0 rgba(255, 255, 255, 0.7); }
    /* Task 498 (заявка): пределы НСХ под полями произвольного расчёта —
       класс ts-calc-range (id tempQueryTempRange / tempQueryValRange,
       заполняет openTempSensor): под полем температуры — в °C, под
       полем значения — в Ом (ТС) / мВ (ТП). Прижаты к «своему» полю
       (верхний отрицательный отступ компенсирует нижний отступ поля),
       у последней строки панели нижний отступ убран. */
    .ts-calc-range { font-size: 11px; font-weight: 600; color: rgba(255, 255, 255, 0.52); margin: -8px 2px 12px; line-height: 1.4; letter-spacing: -0.1px; }
    .ts-calc-panel .ts-calc-range:last-child { margin-bottom: 0; }
    [data-theme="light"] .ts-calc-range { color: rgba(20, 20, 19, 0.55); }
    /* Task 498 (заявка): в баре страницы расчёта датчика температуры —
       только тип датчика («50М (Cu50) α = 0,00428 °C⁻¹», задаёт
       openTempSensor) и шрифт крупнее: 18 → 21px, в scrolled-состоянии
       15 → 17px (ID-селектор сильнее классовых правил; при нехватке
       ширины адаптивный фиттер fitPageHeaderTitle сам уменьшит шрифт
       и/или перенесёт заголовок на несколько строк). */
    #tempSensorViewTitle { font-size: 21px; }
    .page-content.scrolled #tempSensorViewTitle { font-size: 17px; }
"""))

print('=== index.html ===')
apply(IDX, idx_edits)

# --------------------------------------------------------------- sw.js --
sw_edits = []
sw_edits.append(('R8 sw.js версия + комментарий',
"""const CACHE_VERSION = 'kipia-test-v721';
""",
"""// Task 498: «Датчики температуры» — пределы НСХ под полями
// произвольного расчёта (в °C и в Ом/мВ, ts-calc-range); в баре
// страницы датчика — только тип («50М (Cu50) α = 0,00428 °C⁻¹»)
// крупнее (21px); формула pt1391 ниже 0 °C приведена к таблице
// А.2 ГОСТ 6651-2009 (член C, коэффициенты A/B). Клиент-only.
const CACHE_VERSION = 'kipia-test-v722';
"""))

print('=== sw.js ===')
apply(SW, sw_edits)

print('Task 498: применено.')
