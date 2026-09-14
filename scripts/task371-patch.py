#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 371: заявка пользователя — «На странице Главная / Инженерные
#   калькуляторы / КИП и А / Датчики температуры, под блоком Таблица
#   значений добавь блок Расчёт произвольных значений, по примеру
#   как в разделе Шкала-сигнал.»
#
# Что делает патч (index.html):
#   1. Рефакторинг: локальная карта типов ТС из calcTempSensor()
#      вынесена в getRtdSensorMap() — переиспользуется блоком
#      «Расчёт произвольных значений» (карта в файле ровно одна).
#   2. Новые функции после calcTcVoltage():
#      - tempCustomCalcHtml(valLabel, valPlaceholder) — HTML блока
#        (единый для ТС и ТП, по разметке scaleCustomCalcPanel);
#      - getTempSensorRange() — диапазоны НСХ по типу датчика;
#      - tempCalcForwardValue(t) — R(t)/E(t) по текущей форме;
#      - tempCalcInvertValue(v) — обращение монотонной НСХ бисекцией;
#      - tempQueryFromTemp() — живой расчёт «температура → значение»;
#      - tempQueryFromValue() — живой расчёт «значение → температура».
#   3. В ОБЕИХ ветках calcTempSensor() (ТС и ТП) под таблицей значений
#      дописывается блок «Расчёт произвольных значений».
# Сервер (Apps Script) не менялся. Запуск из корня репо kip8test.

import io

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
orig_len = len(src)

def replace_once(anchor, replacement, what):
    global src
    n = src.count(anchor)
    assert n == 1, '%s: якорь должен встречаться 1 раз, найдено %d' % (what, n)
    src = src.replace(anchor, replacement)

# ---------------------------------------------------------------
# 1. Рефакторинг: карта типов ТС → getRtdSensorMap()
# ---------------------------------------------------------------
SENSOR_MAP_OLD = """            let sensorData={
                cu50_1428:{r0:50,alpha:0.00428,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
                cu100_1428:{r0:100,alpha:0.00428,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
                cu50_1426:{r0:50,alpha:0.00426,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00426·t)'},
                cu100_1426:{r0:100,alpha:0.00426,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00426·t)'},
                pt50_1391:{r0:50,name:'50П (Pt50)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},
                pt100_1391:{r0:100,name:'100П (Pt100)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},
                pt100_1385:{r0:100,name:'Pt100 (IEC)',nsc:'pt1385',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³], IEC 60751 / ГОСТ 6651-2009'},
                pt1000_1385:{r0:1000,name:'Pt1000 (IEC)',nsc:'pt1385',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³], IEC 60751 / ГОСТ 6651-2009'}
            };"""
SENSOR_MAP_NEW = """            // Task 371: карта типов ТС — общая с блоком
            // «Расчёт произвольных значений» (см. getRtdSensorMap)
            let sensorData=getRtdSensorMap();"""
replace_once(SENSOR_MAP_OLD, SENSOR_MAP_NEW, 'карта типов ТС в calcTempSensor')

# ---------------------------------------------------------------
# 2. Новые функции после calcTcVoltage (перед «// DOMContentLoaded»)
# ---------------------------------------------------------------
FUNCS_ANCHOR = """        return mv;
    }

    // DOMContentLoaded"""

FUNCS_NEW = """        return mv;
    }

    // Task 371: блок «Расчёт произвольных значений» на странице
    // «Датчики температуры» — под таблицей значений, по примеру
    // раздела «Шкала-сигнал»: живой двусторонний расчёт
    // t ↔ R(t) (ТС) / t ↔ E(t) (ТП) при вводе в любое поле.
    // Карта типов ТС вынесена из calcTempSensor() для переиспользования.
    function getRtdSensorMap(){
        return {
            cu50_1428:{r0:50,alpha:0.00428,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
            cu100_1428:{r0:100,alpha:0.00428,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
            cu50_1426:{r0:50,alpha:0.00426,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00426·t)'},
            cu100_1426:{r0:100,alpha:0.00426,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00426·t)'},
            pt50_1391:{r0:50,name:'50П (Pt50)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},
            pt100_1391:{r0:100,name:'100П (Pt100)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},
            pt100_1385:{r0:100,name:'Pt100 (IEC)',nsc:'pt1385',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³], IEC 60751 / ГОСТ 6651-2009'},
            pt1000_1385:{r0:1000,name:'Pt1000 (IEC)',nsc:'pt1385',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³], IEC 60751 / ГОСТ 6651-2009'}
        };
    }
    // Task 371: HTML блока «Расчёт произвольных значений» — единый для
    // веток ТС и ТП (отличаются подпись второго поля и пример в нём);
    // разметка повторяет scaleCustomCalcPanel раздела «Шкала-сигнал»
    function tempCustomCalcHtml(valLabel,valPlaceholder){
        return `<div id="tempCustomCalcPanel"><div class="converter-result-label-title" style="margin-top:16px;">Расчёт произвольных значений</div><div class="scale-form" style="margin-top:8px;"><div style="color:rgba(255,255,255,0.25); font-size:11px; margin-bottom:10px; line-height:1.4;">Введите значение в любое поле — другое рассчитается автоматически</div><div class="scale-form-label">Температура (°C)</div><input type="text" inputmode="numeric" id="tempQueryTemp" class="scale-field" placeholder="Например: 55" oninput="tempQueryFromTemp()" autocomplete="off" enterkeyhint="done"><div class="scale-form-label">${valLabel}</div><input type="text" inputmode="numeric" id="tempQueryVal" class="scale-field" placeholder="${valPlaceholder}" oninput="tempQueryFromValue()" autocomplete="off" enterkeyhint="done"></div></div>`;
    }
    // Task 371: диапазоны НСХ по типу датчика — границы применимости
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
    }
    // Task 371: прямое значение по температуре из ТЕКУЩЕЙ формы
    // (R(t) для ТС, E(t) для ТП) — как queryFromScaleLive читает поля живьём
    function tempCalcForwardValue(t){
        let type=document.getElementById('temp_sensor_type').value;
        if(type==='rtd'){
            let sd=getRtdSensorMap()[document.getElementById('temp_rtd_type').value];
            if(!sd){return null;}
            return sd.nsc==='cu'?calcCuResistance(t,sd.r0,sd.alpha):calcRtdResistance(t,sd.r0,sd.nsc);
        }
        return calcTcVoltage(t,document.getElementById('temp_tc_type').value);
    }
    // Task 371: температура по значению R/E — обращение монотонной
    // характеристики НСХ бисекцией (аналитически не обращается:
    // у Pt ниже 0°C член C, у ТП — полиномы высоких степеней)
    function tempCalcInvertValue(v){
        let rng=getTempSensorRange();
        let f=function(t){return tempCalcForwardValue(t);};
        let vmin=f(rng.min),vmax=f(rng.max);
        if(v===null||isNaN(v)||v<vmin-1e-9||v>vmax+1e-9){return null;}
        let lo=rng.min,hi=rng.max;
        for(let i=0;i<80;i++){
            let mid=(lo+hi)/2;
            if(f(mid)<v){lo=mid;}else{hi=mid;}
        }
        return (lo+hi)/2;
    }
    // Task 371: живой расчёт «температура → R/E» (ввод в поле температуры)
    function tempQueryFromTemp(){
        let tEl=document.getElementById('tempQueryTemp');
        let vEl=document.getElementById('tempQueryVal');
        if(!tEl||!vEl){return;}
        let t=parseLocaleNumber(tEl.value);
        if(isNaN(t)){vEl.value='';return;}
        let rng=getTempSensorRange();
        if(t<rng.min||t>rng.max){
            vEl.value='';
            showToast('Температура вне диапазона НСХ ('+formatNumber(rng.min)+' … '+formatNumber(rng.max)+' °C)');
            return;
        }
        let val=tempCalcForwardValue(t);
        if(val===null){vEl.value='';return;}
        vEl.value=formatNumber(val);
    }
    // Task 371: живой расчёт «R/E → температура» (ввод в поле значения)
    function tempQueryFromValue(){
        let tEl=document.getElementById('tempQueryTemp');
        let vEl=document.getElementById('tempQueryVal');
        if(!tEl||!vEl){return;}
        let v=parseLocaleNumber(vEl.value);
        if(isNaN(v)){tEl.value='';return;}
        let type=document.getElementById('temp_sensor_type').value;
        let unit=type==='rtd'?'Ом':'мВ';
        let rng=getTempSensorRange();
        let f=function(t){return tempCalcForwardValue(t);};
        let vmin=f(rng.min),vmax=f(rng.max);
        if(v<vmin-1e-9||v>vmax+1e-9){
            tEl.value='';
            showToast('Значение вне диапазона НСХ ('+formatNumber(vmin)+' … '+formatNumber(vmax)+' '+unit+')');
            return;
        }
        let t=tempCalcInvertValue(v);
        if(t===null){tEl.value='';return;}
        tEl.value=formatNumber(t);
    }

    // DOMContentLoaded"""
replace_once(FUNCS_ANCHOR, FUNCS_NEW, 'блок новых функций после calcTcVoltage')

# ---------------------------------------------------------------
# 3. Панель в ветке ТС (после таблицы, до resDiv.innerHTML)
# ---------------------------------------------------------------
RTD_ANCHOR = """            html+=`</tbody></table></div>`;
            resDiv.innerHTML=html;
        } else {"""
RTD_NEW = """            html+=`</tbody></table></div>`;
            // Task 371: под таблицей — блок «Расчёт произвольных значений»
            // (по примеру раздела «Шкала-сигнал», живой двусторонний расчёт)
            html+=tempCustomCalcHtml('Сопротивление R(t), Ом','Например: 61,8');
            resDiv.innerHTML=html;
        } else {"""
replace_once(RTD_ANCHOR, RTD_NEW, 'панель в ветке ТС')

# ---------------------------------------------------------------
# 4. Панель в ветке ТП
# ---------------------------------------------------------------
TC_ANCHOR = """            html+=`</tbody></table></div>`;
            resDiv.innerHTML=html;
        }
        resDiv.style.display='block';"""
TC_NEW = """            html+=`</tbody></table></div>`;
            // Task 371: под таблицей — блок «Расчёт произвольных значений»
            html+=tempCustomCalcHtml('Термо-ЭДС E(t), мВ','Например: 2,2');
            resDiv.innerHTML=html;
        }
        resDiv.style.display='block';"""
replace_once(TC_ANCHOR, TC_NEW, 'панель в ветке ТП')

io.open(PATH, 'w', encoding='utf-8').write(src)

# Контрольные проверки результата
assert src.count('cu50_1428:{r0:50,alpha:0.00428') == 1, 'карта ТС должна быть ровно в одном месте'
assert src.count('function tempQueryFromTemp') == 1
assert src.count('function tempQueryFromValue') == 1
assert src.count('function getRtdSensorMap') == 1
assert src.count('function getTempSensorRange') == 1
assert src.count('id="tempCustomCalcPanel"') == 1, 'панель только в генерируемом HTML (шаблон)'
assert src.count("tempCustomCalcHtml('Сопротивление R(t), Ом','Например: 61,8')") == 1
assert src.count("tempCustomCalcHtml('Термо-ЭДС E(t), мВ','Например: 2,2')") == 1
assert src.index('tempTableContainer') < src.index('tempCustomCalcHtml'), 'панель после таблицы'
print('OK: index.html пропатчен (%d → %d символов)' % (orig_len, len(src)))
