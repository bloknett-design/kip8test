/**
 * @module calculators/converters
 * Unit converters, signal/scale calculators, and instrument error calculators
 */
const showToast = window.showToast;
const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const roundNumber = window.roundNumber;
const validateField = window.validateField;
const clearFieldError = window.clearFieldError;
const hasValidationErrors = window.hasValidationErrors;
const getSignalRangeAndUnit = window.getSignalRangeAndUnit;


// ======================== КОНВЕРТЕРЫ (полные данные) ========================
const unitData = {
    pressure: { units: { 'Pa':{label:'Па',factor:1}, 'kPa':{label:'кПа',factor:1000}, 'MPa':{label:'МПа',factor:1000000}, 'bar':{label:'бар',factor:100000}, 'mbar':{label:'мбар',factor:100}, 'atm':{label:'атм',factor:101325}, 'kgf_cm2':{label:'кгс/см²',factor:98066.5}, 'kgf_m2':{label:'кгс/м²',factor:9.80665}, 'mmHg':{label:'мм рт. ст.',factor:133.322}, 'PSI':{label:'PSI',factor:6894.757}, 'mmH2O':{label:'мм вод. ст.',factor:9.80665} } },
    flow: { units: { 'm3h':{label:'м³/ч',factor:1}, 'm3s':{label:'м³/с',factor:3600}, 'l_min':{label:'л/мин',factor:0.06}, 'l_s':{label:'л/с',factor:3.6}, 't_h':{label:'т/ч',factor:1}, 'kg_s':{label:'кг/с',factor:3.6}, 'kg_h':{label:'кг/ч',factor:0.001} } },
    mass: { units: { 'kg':{label:'кг',factor:1}, 'g':{label:'г',factor:0.001}, 'mg':{label:'мг',factor:0.000001}, 't':{label:'т',factor:1000}, 'lb':{label:'фунт',factor:0.453592}, 'oz':{label:'унция',factor:0.0283495}, } },
    length: { units: { 'm':{label:'м',factor:1}, 'km':{label:'км',factor:1000}, 'cm':{label:'см',factor:0.01}, 'mm':{label:'мм',factor:0.001}, 'um':{label:'мкм',factor:0.000001}, 'mi':{label:'миля',factor:1609.344}, 'ft':{label:'фут',factor:0.3048}, 'in':{label:'дюйм',factor:0.0254}, 'yd':{label:'ярд',factor:0.9144} } },
    density: { units: { 'kg_m3':{label:'кг/м³',factor:1}, 'g_cm3':{label:'г/см³',factor:1000}, 'g_l':{label:'г/л',factor:1}, 'kg_l':{label:'кг/л',factor:1000}, } },
    time: { units: { 's':{label:'секунда',factor:1}, 'ms':{label:'мс',factor:0.001}, 'min':{label:'минута',factor:60}, 'h':{label:'час',factor:3600}, 'd':{label:'сутки',factor:86400}, 'week':{label:'неделя',factor:604800}, 'month':{label:'месяц',factor:2592000}, 'year':{label:'год',factor:31536000} } },
    volume: { units: { 'm3':{label:'м³',factor:1}, 'l':{label:'литр',factor:0.001}, 'ml':{label:'мл',factor:0.000001}, 'cm3':{label:'см³',factor:0.000001}, 'gal':{label:'галлон US',factor:0.00378541}, 'bbl':{label:'баррель',factor:0.158987}, 'ft3':{label:'куб. фут',factor:0.0283168}, 'dm3':{label:'дм³',factor:0.001} } }
};

// Готовые валидаторы для типовых случаев
function validateNumericField(input) {
    return validateField(input, (val) => !isNaN(val), 'Введите число');
}
function validatePositiveField(input) {
    return validateField(input, (val) => !isNaN(val) && val > 0, 'Должно быть положительным числом');
}
function validateNonNegativeField(input) {
    return validateField(input, (val) => !isNaN(val) && val >= 0, 'Должно быть неотрицательным числом');
}
function validateRangeField(input, min, max) {
    return validateField(input, (val) => !isNaN(val) && val >= min && val <= max,
        'Должно быть в диапазоне ' + min + '–' + max);
}

function convertUnits(cat) { if (cat==='temp') { convertTemp(); return; } let d=unitData[cat]; let val=parseLocaleNumber(document.getElementById(`conv-${cat}-input`).value); let from=document.getElementById(`conv-${cat}-unit`).value; let resDiv=document.getElementById(`conv-${cat}-results`); let tableDiv=document.getElementById(`conv-${cat}-table`); if(tableDiv) tableDiv.style.display='none'; if(isNaN(val)) { resDiv.innerHTML='<p style="text-align:center;color:#c74a4a;font-size:14px;padding:16px;">Введите значение</p>'; return; } let base=val*d.units[from].factor; let html='<div class="converter-result-label-title">Результаты</div>'; let delay=0; for(let u in d.units){ if(u===from) continue; let v=base/d.units[u].factor; html+=`<div class="converter-result-item" style="animation-delay:${delay}ms;cursor:pointer;" onclick="showConverterTable('${cat}','${from}','${u}',${base})"><span class="converter-result-label">${d.units[u].label}</span><span class="converter-result-value">${formatNumber(v)} <span style="color:rgba(255,255,255,0.25);font-weight:400;font-size:0.85em;">(${roundNumber(v)})</span></span></div>`; delay+=40; } resDiv.innerHTML=html; }
function convertTemp() { let val=parseLocaleNumber(document.getElementById('conv-temp-input').value); let from=document.getElementById('conv-temp-unit').value; let resDiv=document.getElementById('conv-temp-results'); let tableDiv=document.getElementById('conv-temp-table'); if(tableDiv) tableDiv.style.display='none'; if(isNaN(val)) { resDiv.innerHTML='<p style="text-align:center;color:#c74a4a;font-size:14px;padding:16px;">Введите значение</p>'; return; } let c=from==='C'?val:from==='F'?(val-32)*5/9:from==='K'?val-273.15:from==='R'?val*1.25:(val-491.67)*5/9; let tU={'C':{label:'°C',fn:z=>z},'F':{label:'°F',fn:z=>z*9/5+32},'K':{label:'K',fn:z=>z+273.15},'R':{label:'°R',fn:z=>z*0.8},'Ra':{label:'°Ra',fn:z=>(z+273.15)*9/5}}; let html='<div class="converter-result-label-title">Результаты</div>'; let delay=0; for(let u in tU){ if(u===from) continue; let v=tU[u].fn(c); html+=`<div class="converter-result-item" style="animation-delay:${delay}ms;cursor:pointer;" onclick="showTempTable('${from}','${u}',${c})"><span class="converter-result-label">${tU[u].label}</span><span class="converter-result-value">${formatNumber(v)} <span style="color:rgba(255,255,255,0.25);font-weight:400;font-size:0.85em;">(${roundNumber(v)})</span></span></div>`; delay+=40; } resDiv.innerHTML=html; }

// Шкала-сигнал
const sigUnitLabels={'4_20':'мА','0_20':'мА','0_5mA':'мА','0_10V':'В','1_5V':'В','0_5V':'В','bipolar_10':'В','20_100_kPa':'кПа','0_2_1_0_bar':'бар','3_15_psi':'psi','0_2_1_0_kgf_cm2':'кгс/см²','0_100_pct':'%','custom':'ед.'};

function showConverterTable(cat, fromUnit, toUnit, baseValue) {
let d = unitData[cat];
let fromLabel = d.units[fromUnit].label;
let toLabel = d.units[toUnit].label;
let toFactor = d.units[toUnit].factor;
let fromFactor = d.units[fromUnit].factor;
let tableDiv = document.getElementById('conv-' + cat + '-table');

let html = '<div class="converter-result-label-title">Таблица перевода: ' + fromLabel + ' → ' + toLabel + ' (шаг 5%)</div>';
html += '<div style="overflow-x:auto;border-radius:10px;border:1px solid rgba(74,143,199,0.1);margin-top:8px;">';
html += '<table style="min-width:100%;width:100%;border-collapse:collapse;">';
html += '<thead><tr style="background:rgba(22,27,34,0.7);">';
html += '<th style="padding:10px 12px;font-size:14px;color:#4a8fc7;text-align:left;">' + fromLabel + '</th>';
html += '<th style="padding:10px 12px;font-size:14px;color:#4ac771;text-align:left;">' + toLabel + '</th>';
html += '<th style="padding:10px 12px;font-size:14px;color:rgba(255,255,255,0.4);text-align:left;">%</th>';
html += '</tr></thead><tbody>';

for (let pct = 0; pct <= 100; pct += 5) {
    let fromVal = (baseValue * pct / 100) / fromFactor;
    let toVal = (baseValue * pct / 100) / toFactor;
    let bg = (pct / 5) % 2 ? 'rgba(22,27,34,0.4)' : 'rgba(13,17,23,0.4)';
    html += '<tr style="background:' + bg + ';">';
    html += '<td style="padding:8px 12px;font-size:15px;color:#e0e0e0;">' + formatNumber(fromVal) + '</td>';
    html += '<td style="padding:8px 12px;font-size:15px;color:#4ac771;">' + formatNumber(toVal) + '</td>';
    html += '<td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">' + pct + '%</td>';
    html += '</tr>';
}

html += '</tbody></table></div>';
html += '<div style="margin-top:8px;padding:8px 12px;background:rgba(13,17,23,0.4);border-radius:8px;font-size:12px;color:rgba(255,255,255,0.35);">';
html += 'Базовое значение: <b style="color:#4a8fc7;">' + formatNumber(baseValue / fromFactor) + ' ' + fromLabel + '</b> = <b style="color:#4ac771;">' + formatNumber(baseValue / toFactor) + ' ' + toLabel + '</b>';
html += '</div>';

tableDiv.innerHTML = html;
tableDiv.style.display = 'block';
setTimeout(() => tableDiv.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

function showTempTable(fromUnit, toUnit, baseCelsius) {
let tU = {'C':{label:'°C',fn:z=>z},'F':{label:'°F',fn:z=>z*9/5+32},'K':{label:'K',fn:z=>z+273.15},'R':{label:'°R',fn:z=>z*0.8},'Ra':{label:'°Ra',fn:z=>(z+273.15)*9/5}};
let fromLabel = tU[fromUnit].label;
let toLabel = tU[toUnit].label;
let tableDiv = document.getElementById('conv-temp-table');

let html = '<div class="converter-result-label-title">Таблица перевода: ' + fromLabel + ' → ' + toLabel + ' (шаг 5%)</div>';
html += '<div style="overflow-x:auto;border-radius:10px;border:1px solid rgba(74,143,199,0.1);margin-top:8px;">';
html += '<table style="min-width:100%;width:100%;border-collapse:collapse;">';
html += '<thead><tr style="background:rgba(22,27,34,0.7);">';
html += '<th style="padding:10px 12px;font-size:14px;color:#4a8fc7;text-align:left;">' + fromLabel + '</th>';
html += '<th style="padding:10px 12px;font-size:14px;color:#4ac771;text-align:left;">' + toLabel + '</th>';
html += '<th style="padding:10px 12px;font-size:14px;color:rgba(255,255,255,0.4);text-align:left;">%</th>';
html += '</tr></thead><tbody>';

for (let pct = 0; pct <= 100; pct += 5) {
    let cVal = baseCelsius * pct / 100;
    let fromVal = tU[fromUnit].fn(cVal);
    let toVal = tU[toUnit].fn(cVal);
    let bg = (pct / 5) % 2 ? 'rgba(22,27,34,0.4)' : 'rgba(13,17,23,0.4)';
    html += '<tr style="background:' + bg + ';">';
    html += '<td style="padding:8px 12px;font-size:15px;color:#e0e0e0;">' + formatNumber(fromVal) + '</td>';
    html += '<td style="padding:8px 12px;font-size:15px;color:#4ac771;">' + formatNumber(toVal) + '</td>';
    html += '<td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">' + pct + '%</td>';
    html += '</tr>';
}

html += '</tbody></table></div>';
html += '<div style="margin-top:8px;padding:8px 12px;background:rgba(13,17,23,0.4);border-radius:8px;font-size:12px;color:rgba(255,255,255,0.35);">';
html += 'Базовое значение: <b style="color:#4a8fc7;">' + formatNumber(tU[fromUnit].fn(baseCelsius)) + ' ' + fromLabel + '</b> = <b style="color:#4ac771;">' + formatNumber(tU[toUnit].fn(baseCelsius)) + ' ' + toLabel + '</b>';
html += '</div>';

tableDiv.innerHTML = html;
tableDiv.style.display = 'block';
setTimeout(() => tableDiv.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}
function setSignalDefaults() { let type=document.getElementById('sigType').value; let def={'4_20':[4,20],'0_20':[0,20],'0_5mA':[0,5],'0_10V':[0,10],'1_5V':[1,5],'0_5V':[0,5],'bipolar_10':[-10,10],'20_100_kPa':[20,100],'0_2_1_0_bar':['0,2','1,0'],'3_15_psi':[3,15],'0_2_1_0_kgf_cm2':['0,2','1,0'],'0_100_pct':[0,100]}; let customDiv=document.getElementById('sigCustomRange'); if(def[type]){document.getElementById('sigMin').value=def[type][0]; document.getElementById('sigMax').value=def[type][1]; customDiv.style.display='none';} else{document.getElementById('sigMin').value='0'; document.getElementById('sigMax').value='100'; document.getElementById('sigUnitCustom').value='%'; customDiv.style.display='block';} document.getElementById('sigUnitLabel').innerText=sigUnitLabels[type]; }
function setScaleDefaults() { let type=document.getElementById('scalePreset').value; let def={'0_100':[0,100,'%'],'4_20':[4,20,'мА'],'0_20':[0,20,'мА'],'0_5mA':[0,5,'мА'],'0_10V':[0,10,'В'],'1_5V':[1,5,'В'],'0_5V':[0,5,'В'],'bipolar_10':[-10,10,'В'],'20_100_kPa':[20,100,'кПа'],'0_2_1_0_bar':['0,2','1,0','бар'],'3_15_psi':[3,15,'psi'],'0_2_1_0_kgf_cm2':['0,2','1,0','кгс/см²']}; let customDiv=document.getElementById('scaleCustomRange'); if(def[type]){document.getElementById('scaleMin').value=def[type][0]; document.getElementById('scaleMax').value=def[type][1]; document.getElementById('scaleUnitName').value=def[type][2]; customDiv.style.display='none';} else{customDiv.style.display='block';} }
function calcScaleSignal() { let smin=parseLocaleNumber(document.getElementById('scaleMin').value); let smax=parseLocaleNumber(document.getElementById('scaleMax').value); let gmin=parseLocaleNumber(document.getElementById('sigMin').value); let gmax=parseLocaleNumber(document.getElementById('sigMax').value); let scaleType=document.getElementById('scaleType').value; if(isNaN(smin)||isNaN(smax)||isNaN(gmin)||isNaN(gmax)){showToast('Заполните все поля');return;} if(smin===smax||gmin===gmax){showToast('Пределы не должны совпадать');return;} document.getElementById('scaleResultsArea').style.display='block'; let unit=document.getElementById('scaleUnitName').value||'ед.'; let sigRange=getSignalRangeAndUnit(document.getElementById('sigType').value); let sigUnit=sigRange.unit; let typeLabels={linear:'Линейная',quadratic:'Квадратичная',sqrt:'Корнеизвлекающая'}; let pct=[0,5,10,15,20,25,30,40,50,60,70,75,80,90,95,100]; let html='<table style="min-width:100%;width:100%;border-collapse:collapse;"><thead><tr style="background:rgba(22,27,34,0.7);"><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">%</th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">Шкала ('+unit+')</th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">Сигнал ('+sigUnit+')</th></tr></thead><tbody>'; for(let i=0;i<pct.length;i++){ let pr=pct[i]/100; let scaleVal=smin+(smax-smin)*pr; let sigVal; if(scaleType==='quadratic'){ sigVal=gmin+(gmax-gmin)*pr*pr; } else if(scaleType==='sqrt'){ sigVal=gmin+(gmax-gmin)*Math.sqrt(pr); } else { sigVal=gmin+(gmax-gmin)*pr; } let bg=i%2?'rgba(22,27,34,0.4)':'rgba(13,17,23,0.4)'; html+=`<tr style="background:${bg};"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">${pct[i]}</td><td style="padding:8px 12px;font-size:14px;color:#e0e0e0;">${formatNumber(scaleVal)}</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">${formatNumber(sigVal)}</td></tr>`; } html+='</tbody></table>'; document.getElementById('scaleTableContainer').innerHTML=html; document.getElementById('scaleInfo').innerHTML='Тип шкалы: <b style="color:#4a8fc7;">'+typeLabels[scaleType]+'</b> · Шкала: '+formatNumber(smin)+' – '+formatNumber(smax)+' '+unit+' · Сигнал: '+sigRange.label; document.getElementById('scaleQueryUnit').textContent=unit; document.getElementById('scaleQuerySigUnit').textContent=sigUnit; document.getElementById('scaleCustomCalcPanel').style.display='block'; document.getElementById('queryScaleVal').value=''; document.getElementById('querySigVal').value=''; setTimeout(()=>document.getElementById('scaleResultsArea').scrollIntoView({behavior:'smooth',block:'start'}),100); }
function queryFromScaleLive(){ let smin=parseLocaleNumber(document.getElementById('scaleMin').value),smax=parseLocaleNumber(document.getElementById('scaleMax').value),gmin=parseLocaleNumber(document.getElementById('sigMin').value),gmax=parseLocaleNumber(document.getElementById('sigMax').value),scaleType=document.getElementById('scaleType').value,q=parseLocaleNumber(document.getElementById('queryScaleVal').value),unit=document.getElementById('scaleUnitName').value||'ед.',sigRange=getSignalRangeAndUnit(document.getElementById('sigType').value),sigUnit=sigRange.unit;if(isNaN(q)){document.getElementById('querySigVal').value='';return;} let p=(q-smin)/(smax-smin); let sig; if(scaleType==='quadratic'){sig=gmin+(gmax-gmin)*p*p;} else if(scaleType==='sqrt'){sig=gmin+(gmax-gmin)*Math.sqrt(p);} else{sig=gmin+(gmax-gmin)*p;} document.getElementById('querySigVal').value=formatNumber(sig); }
function queryFromSignalLive(){ let smin=parseLocaleNumber(document.getElementById('scaleMin').value),smax=parseLocaleNumber(document.getElementById('scaleMax').value),gmin=parseLocaleNumber(document.getElementById('sigMin').value),gmax=parseLocaleNumber(document.getElementById('sigMax').value),scaleType=document.getElementById('scaleType').value,q=parseLocaleNumber(document.getElementById('querySigVal').value),unit=document.getElementById('scaleUnitName').value||'ед.',sigRange=getSignalRangeAndUnit(document.getElementById('sigType').value),sigUnit=sigRange.unit;if(isNaN(q)){document.getElementById('queryScaleVal').value='';return;} let p=(q-gmin)/(gmax-gmin); let val_lin; if(scaleType==='quadratic'){val_lin=Math.sqrt(p);} else if(scaleType==='sqrt'){val_lin=p*p;} else{val_lin=p;} let val=smin+(smax-smin)*val_lin; document.getElementById('queryScaleVal').value=formatNumber(val); }

// Расчёт погрешности для всех типов
function toggleErrorClassFields(prefix) {
    let form = document.getElementById(prefix + 'class_form').value;
    let groups = ['group_simple', 'group_underline', 'group_circle', 'group_fraction'];
    groups.forEach(g => {
        let el = document.getElementById(prefix + g);
        if (el) el.style.display = 'none';
    });
    let showMap = {
        'number': 'group_simple',
        'underline': 'group_underline',
        'circle': 'group_circle',
        'fraction': 'group_fraction'
    };
    let showEl = document.getElementById(prefix + showMap[form]);
    if (showEl) showEl.style.display = 'block';
    let infoEl = document.getElementById(prefix + 'class_info');
    if (infoEl) {
        if (form === 'number') infoEl.innerHTML = 'Xн = ВПИ − НПИ (диапазон измерения)';
        else if (form === 'underline') infoEl.innerHTML = 'Xн = длина шкалы (в единицах измерения)';
        else if (form === 'circle') infoEl.innerHTML = 'Относительная погрешность постоянна во всём диапазоне';
        else if (form === 'fraction') infoEl.innerHTML = 'c/d — аддитивная/мультипликативная составляющие относительной погрешности';
    }
}

// Переключение видимости поля "Своё значение" для датчиков давления
function toggleEpCustomClass() {
    let sel = document.getElementById('ep_class_val');
    let wrap = document.getElementById('ep_class_val_custom_wrap');
    if (sel.value === 'custom') {
        wrap.style.display = 'block';
    } else {
        wrap.style.display = 'none';
    }
}

// Специальная функция расчёта погрешности для датчиков давления (только приведённая погрешность)
function calcPressureError() {
    let prefix = 'ep_';
    let clsVal = document.getElementById(prefix + 'class_val').value;
    let cls;
    if (clsVal === 'custom') {
        cls = parseLocaleNumber(document.getElementById(prefix + 'class_val_custom').value);
    } else {
        cls = parseFloat(clsVal);
    }
    let xmin = parseLocaleNumber(document.getElementById(prefix + 'xmin').value);
    let xmax = parseLocaleNumber(document.getElementById(prefix + 'xmax').value);
    if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
    if (isNaN(xmin) || isNaN(xmax)) { showToast('Введите диапазон измерения'); return; }
    if (xmin >= xmax) { showToast('НПИ должен быть меньше ВПИ'); return; }
    let xNorm = xmax - xmin;
    let xNormDesc = 'Xн = ВПИ − НПИ = ' + formatNumber(xmax) + ' − ' + (xmin < 0 ? '(' + formatNumber(xmin) + ')' : formatNumber(xmin)) + ' = ' + formatNumber(xNorm);
    let absErr = (cls / 100) * xNorm;
    let formulaHTML = 'Δ = ±(<span class="greek-gamma">γ</span>/100)·Xн = ±(' + formatNumber(cls) + '/100)·' + formatNumber(xNorm) + ' = ±' + formatNumber(absErr);

    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value"><span class="greek-gamma">γ</span> = ' + formatNumber(cls) + '% (приведённая)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Нормирующее значение (Xн)</span><span class="converter-result-value">' + formatNumber(xNorm) + ' <span style="font-size:11px;color:rgba(140,180,210,0.7);">(' + xNormDesc + ')</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById(prefix + 'results').innerHTML = html;
    document.getElementById(prefix + 'results').style.display = 'block';
    setTimeout(() => document.getElementById(prefix + 'results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

function toggleElCustomClass() {
    let sel = document.getElementById('el_class_val');
    let wrap = document.getElementById('el_class_val_custom_wrap');
    wrap.style.display = sel.value === 'custom' ? 'block' : 'none';
}

// Специальная функция расчёта погрешности для уровнемеров (только приведённая погрешность)
function calcLevelError() {
    let prefix = 'el_';
    let clsVal = document.getElementById(prefix + 'class_val').value;
    let cls;
    if (clsVal === 'custom') {
        cls = parseLocaleNumber(document.getElementById(prefix + 'class_val_custom').value);
    } else {
        cls = parseFloat(clsVal);
    }
    let xmin = parseLocaleNumber(document.getElementById(prefix + 'xmin').value);
    let xmax = parseLocaleNumber(document.getElementById(prefix + 'xmax').value);
    if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
    if (isNaN(xmin) || isNaN(xmax)) { showToast('Введите диапазон измерения'); return; }
    if (xmin >= xmax) { showToast('НПИ должен быть меньше ВПИ'); return; }
    let xNorm = xmax - xmin;
    let xNormDesc = 'Xн = ВПИ − НПИ = ' + formatNumber(xmax) + ' − ' + (xmin < 0 ? '(' + formatNumber(xmin) + ')' : formatNumber(xmin)) + ' = ' + formatNumber(xNorm);
    let absErr = (cls / 100) * xNorm;
    let formulaHTML = 'Δ = ±(<span class="greek-gamma">γ</span>/100)·Xн = ±(' + formatNumber(cls) + '/100)·' + formatNumber(xNorm) + ' = ±' + formatNumber(absErr);

    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value"><span class="greek-gamma">γ</span> = ' + formatNumber(cls) + '% (приведённая)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Нормирующее значение (Xн)</span><span class="converter-result-value">' + formatNumber(xNorm) + ' <span style="font-size:11px;color:rgba(140,180,210,0.7);">(' + xNormDesc + ')</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById(prefix + 'results').innerHTML = html;
    document.getElementById(prefix + 'results').style.display = 'block';
    setTimeout(() => document.getElementById(prefix + 'results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

function toggleEfCustomClass() {
    let sel = document.getElementById('ef_class_val');
    let wrap = document.getElementById('ef_class_val_custom_wrap');
    wrap.style.display = sel.value === 'custom' ? 'block' : 'none';
}

// Специальная функция расчёта погрешности для расходомеров (только относительная погрешность)
function calcFlowmeterError() {
    let prefix = 'ef_';
    let clsVal = document.getElementById(prefix + 'class_val').value;
    let cls;
    if (clsVal === 'custom') {
        cls = parseLocaleNumber(document.getElementById(prefix + 'class_val_custom').value);
    } else {
        cls = parseFloat(clsVal);
    }
    let xCurrent = parseLocaleNumber(document.getElementById(prefix + 'x_current').value);
    if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
    if (isNaN(xCurrent) || xCurrent === 0) { showToast('Введите текущее значение (X ≠ 0)'); return; }
    let absErr = (cls / 100) * Math.abs(xCurrent);
    let formulaHTML = 'Δ = ±(<span class="greek-delta">δ</span>/100)·|X| = ±(' + formatNumber(cls) + '/100)·' + formatNumber(Math.abs(xCurrent)) + ' = ±' + formatNumber(absErr);

    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value"><span class="greek-delta">δ</span> = ' + formatNumber(cls) + '% (относительная)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Текущее значение (X)</span><span class="converter-result-value">' + formatNumber(xCurrent) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById(prefix + 'results').innerHTML = html;
    document.getElementById(prefix + 'results').style.display = 'block';
    setTimeout(() => document.getElementById(prefix + 'results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

function calcErrorGOST(prefix) {
    let form = document.getElementById(prefix + 'class_form').value;
    let absErr, relErr, formulaHTML, xNorm, xNormDesc, xCurrent;
    if (form === 'number') {
        let cls = parseLocaleNumber(document.getElementById(prefix + 'class_val').value);
        let xmin = parseLocaleNumber(document.getElementById(prefix + 'xmin').value);
        let xmax = parseLocaleNumber(document.getElementById(prefix + 'xmax').value);
        xCurrent = parseLocaleNumber(document.getElementById(prefix + 'x_current').value);
        if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
        if (isNaN(xmin) || isNaN(xmax)) { showToast('Введите диапазон измерения'); return; }
        if (xmin >= xmax) { showToast('НПИ должен быть меньше ВПИ'); return; }
        xNorm = xmax - xmin;
        xNormDesc = 'Xн = ВПИ − НПИ = ' + formatNumber(xmax) + ' − ' + (xmin < 0 ? '(' + formatNumber(xmin) + ')' : formatNumber(xmin)) + ' = ' + formatNumber(xNorm);
        absErr = (cls / 100) * xNorm;
        formulaHTML = 'Δ = ±(<span class="greek-gamma">γ</span>/100)·Xн = ±(' + formatNumber(cls) + '/100)·' + formatNumber(xNorm) + ' = ±' + formatNumber(absErr);
        if (!isNaN(xCurrent) && xCurrent !== 0) {
            relErr = (absErr / Math.abs(xCurrent)) * 100;
            formulaHTML += '<br><span class="greek-delta">δ</span> = ±(Δ/|X|)·100 = ±(' + formatNumber(absErr) + '/' + formatNumber(Math.abs(xCurrent)) + ')·100 = ±' + formatNumber(relErr) + '%';
        }
    } else if (form === 'underline') {
        let cls = parseLocaleNumber(document.getElementById(prefix + 'class_val_u').value);
        xNorm = parseLocaleNumber(document.getElementById(prefix + 'xn_scale').value);
        xCurrent = parseLocaleNumber(document.getElementById(prefix + 'x_current_u').value);
        if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
        if (isNaN(xNorm) || xNorm <= 0) { showToast('Введите нормирующее значение'); return; }
        absErr = (cls / 100) * xNorm;
        formulaHTML = 'Δ = ±(<span class="greek-gamma">γ</span>/100)·Xн = ±(' + formatNumber(cls) + '/100)·' + formatNumber(xNorm) + ' = ±' + formatNumber(absErr);
        if (!isNaN(xCurrent) && xCurrent !== 0) {
            relErr = (absErr / Math.abs(xCurrent)) * 100;
            formulaHTML += '<br><span class="greek-delta">δ</span> = ±(Δ/|X|)·100 = ±' + formatNumber(relErr) + '%';
        }
    } else if (form === 'circle') {
        let cls = parseLocaleNumber(document.getElementById(prefix + 'class_val_c').value);
        xCurrent = parseLocaleNumber(document.getElementById(prefix + 'x_current_c').value);
        if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
        if (isNaN(xCurrent) || xCurrent === 0) { showToast('Введите текущее значение (X≠0)'); return; }
        relErr = cls;
        absErr = (cls / 100) * Math.abs(xCurrent);
        formulaHTML = 'Δ = ±(<span class="greek-delta">δ</span>/100)·|X| = ±(' + formatNumber(cls) + '/100)·' + formatNumber(Math.abs(xCurrent)) + ' = ±' + formatNumber(absErr);
        formulaHTML += '<br><span class="greek-delta">δ</span> = ±' + formatNumber(cls) + '% (постоянная)';
    } else if (form === 'fraction') {
        let c = parseLocaleNumber(document.getElementById(prefix + 'c_val').value);
        let d = parseLocaleNumber(document.getElementById(prefix + 'd_val').value);
        let xmax = parseLocaleNumber(document.getElementById(prefix + 'xmax_f').value);
        xCurrent = parseLocaleNumber(document.getElementById(prefix + 'x_current_f').value);
        if (isNaN(c) || isNaN(d) || c <= 0 || d <= 0) { showToast('Введите c и d'); return; }
        if (isNaN(xmax) || xmax <= 0) { showToast('Введите ВПИ'); return; }
        if (isNaN(xCurrent) || xCurrent === 0) { showToast('Введите текущее значение (X≠0)'); return; }
        relErr = c + d * (Math.abs(xmax / xCurrent) - 1);
        absErr = (relErr / 100) * Math.abs(xCurrent);
        formulaHTML = '<span class="greek-delta">δ</span> = ±[c + d·(|Xmax/X| − 1)] = ±[' + formatNumber(c) + ' + ' + formatNumber(d) + '·(|' + formatNumber(xmax) + '/' + formatNumber(Math.abs(xCurrent)) + '| − 1)] = ±' + formatNumber(relErr) + '%';
        formulaHTML += '<br>Δ = ±(<span class="greek-delta">δ</span>/100)·|X| = ±' + formatNumber(absErr);
    }
    let formNames = {'number': 'число (приведённая)', 'underline': 'число с подчёркиванием (приведённая)', 'circle': 'число в кружке (относительная)', 'fraction': 'дробь c/d (относительная)'};
    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Форма класса точности</span><span class="converter-result-value">' + formNames[form] + '</span></div>';
    if (xNorm !== undefined) html += '<div class="converter-result-item"><span class="converter-result-label">Нормирующее значение (Xн)</span><span class="converter-result-value">' + formatNumber(xNorm) + ' <span style="font-size:11px;color:rgba(140,180,210,0.7);">(' + xNormDesc + ')</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    if (relErr !== undefined) html += '<div class="converter-result-item"><span class="converter-result-label">Относительная погрешность (±<span class="greek-delta">δ</span>)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(relErr) + ' %</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById(prefix + 'results').innerHTML = html;
    document.getElementById(prefix + 'results').style.display = 'block';
    setTimeout(() => document.getElementById(prefix + 'results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

// Общий расчёт — Приведённая (число)
function toggleEgnCustomClass() {
    let sel = document.getElementById('egn_class_val');
    let wrap = document.getElementById('egn_class_val_custom_wrap');
    wrap.style.display = sel.value === 'custom' ? 'block' : 'none';
}

function calcGenericNumber() {
    let clsVal = document.getElementById('egn_class_val').value;
    let cls;
    if (clsVal === 'custom') {
        cls = parseLocaleNumber(document.getElementById('egn_class_val_custom').value);
    } else {
        cls = parseFloat(clsVal);
    }
    let xmin = parseLocaleNumber(document.getElementById('egn_xmin').value);
    let xmax = parseLocaleNumber(document.getElementById('egn_xmax').value);
    if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
    if (isNaN(xmin) || isNaN(xmax)) { showToast('Введите диапазон измерения'); return; }
    if (xmin >= xmax) { showToast('НПИ должен быть меньше ВПИ'); return; }
    let xNorm = xmax - xmin;
    let xNormDesc = 'Xн = ВПИ − НПИ = ' + formatNumber(xmax) + ' − ' + (xmin < 0 ? '(' + formatNumber(xmin) + ')' : formatNumber(xmin)) + ' = ' + formatNumber(xNorm);
    let absErr = (cls / 100) * xNorm;
    let formulaHTML = 'Δ = ±(<span class="greek-gamma">γ</span>/100)·Xн = ±(' + formatNumber(cls) + '/100)·' + formatNumber(xNorm) + ' = ±' + formatNumber(absErr);
    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value"><span class="greek-gamma">γ</span> = ' + formatNumber(cls) + '% (приведённая)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Нормирующее значение (Xн)</span><span class="converter-result-value">' + formatNumber(xNorm) + ' <span style="font-size:11px;color:rgba(140,180,210,0.7);">(' + xNormDesc + ')</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById('egn_results').innerHTML = html;
    document.getElementById('egn_results').style.display = 'block';
    setTimeout(() => document.getElementById('egn_results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

// Общий расчёт — Приведённая (подчёркивание)
function toggleEguCustomClass() {
    let sel = document.getElementById('egu_class_val');
    let wrap = document.getElementById('egu_class_val_custom_wrap');
    wrap.style.display = sel.value === 'custom' ? 'block' : 'none';
}

function calcGenericUnderline() {
    let clsVal = document.getElementById('egu_class_val').value;
    let cls;
    if (clsVal === 'custom') {
        cls = parseLocaleNumber(document.getElementById('egu_class_val_custom').value);
    } else {
        cls = parseFloat(clsVal);
    }
    let xNorm = parseLocaleNumber(document.getElementById('egu_xn_scale').value);
    if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
    if (isNaN(xNorm) || xNorm <= 0) { showToast('Введите нормирующее значение'); return; }
    let absErr = (cls / 100) * xNorm;
    let formulaHTML = 'Δ = ±(<span class="greek-gamma">γ</span>/100)·Xн = ±(' + formatNumber(cls) + '/100)·' + formatNumber(xNorm) + ' = ±' + formatNumber(absErr);
    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value"><span class="greek-gamma">γ</span> = ' + formatNumber(cls) + '% (приведённая, Xн = длина шкалы)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Нормирующее значение (Xн)</span><span class="converter-result-value">' + formatNumber(xNorm) + ' <span style="font-size:11px;color:rgba(140,180,210,0.7);">(' + xNormDesc + ')</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById('egu_results').innerHTML = html;
    document.getElementById('egu_results').style.display = 'block';
    setTimeout(() => document.getElementById('egu_results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

// Общий расчёт — Относительная (кружок)
function toggleEgcCustomClass() {
    let sel = document.getElementById('egc_class_val');
    let wrap = document.getElementById('egc_class_val_custom_wrap');
    wrap.style.display = sel.value === 'custom' ? 'block' : 'none';
}

function calcGenericCircle() {
    let clsVal = document.getElementById('egc_class_val').value;
    let cls;
    if (clsVal === 'custom') {
        cls = parseLocaleNumber(document.getElementById('egc_class_val_custom').value);
    } else {
        cls = parseFloat(clsVal);
    }
    let xCurrent = parseLocaleNumber(document.getElementById('egc_x_current').value);
    if (isNaN(cls) || cls <= 0) { showToast('Введите класс точности'); return; }
    if (isNaN(xCurrent) || xCurrent === 0) { showToast('Введите текущее значение (X ≠ 0)'); return; }
    let absErr = (cls / 100) * Math.abs(xCurrent);
    let formulaHTML = 'Δ = ±(<span class="greek-delta">δ</span>/100)·|X| = ±(' + formatNumber(cls) + '/100)·' + formatNumber(Math.abs(xCurrent)) + ' = ±' + formatNumber(absErr);
    formulaHTML += '<br><span class="greek-delta">δ</span> = ±' + formatNumber(cls) + '% (постоянная)';
    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value"><span class="greek-delta">δ</span> = ' + formatNumber(cls) + '% (относительная)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Текущее значение (X)</span><span class="converter-result-value">' + formatNumber(xCurrent) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById('egc_results').innerHTML = html;
    document.getElementById('egc_results').style.display = 'block';
    setTimeout(() => document.getElementById('egc_results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

// Общий расчёт — Относительная (дробь c/d)
function toggleEgfCustomC() {
    let sel = document.getElementById('egf_c_val');
    let wrap = document.getElementById('egf_c_val_custom_wrap');
    wrap.style.display = sel.value === 'custom_c' ? 'block' : 'none';
}
function toggleEgfCustomD() {
    let sel = document.getElementById('egf_d_val');
    let wrap = document.getElementById('egf_d_val_custom_wrap');
    wrap.style.display = sel.value === 'custom_d' ? 'block' : 'none';
}

function syncEgfXcurrent() {
    let xmaxEl = document.getElementById('egf_xmax');
    let xcurEl = document.getElementById('egf_x_current');
    if (xcurEl && !xcurEl.dataset.userEdited) {
        xcurEl.value = xmaxEl.value;
    }
}

function calcGenericFraction() {
    let cVal = document.getElementById('egf_c_val').value;
    let dVal = document.getElementById('egf_d_val').value;
    let c, d;
    if (cVal === 'custom_c') {
        c = parseLocaleNumber(document.getElementById('egf_c_val_custom').value);
    } else {
        c = parseFloat(cVal);
    }
    if (dVal === 'custom_d') {
        d = parseLocaleNumber(document.getElementById('egf_d_val_custom').value);
    } else {
        d = parseFloat(dVal);
    }
    let xmax = parseLocaleNumber(document.getElementById('egf_xmax').value);
    let xCurrent = parseLocaleNumber(document.getElementById('egf_x_current').value);
    if (isNaN(c) || isNaN(d) || c <= 0 || d <= 0) { showToast('Введите c и d'); return; }
    if (isNaN(xmax) || xmax <= 0) { showToast('Введите ВПИ'); return; }
    if (isNaN(xCurrent) || xCurrent === 0) { showToast('Введите текущее значение (X ≠ 0)'); return; }
    let relErr = c + d * (Math.abs(xmax / xCurrent) - 1);
    let absErr = (relErr / 100) * Math.abs(xCurrent);
    let formulaHTML = '<span class="greek-delta">δ</span> = ±[c + d·(|Xmax/X| − 1)] = ±[' + formatNumber(c) + ' + ' + formatNumber(d) + '·(|' + formatNumber(xmax) + '/' + formatNumber(Math.abs(xCurrent)) + '| − 1)] = ±' + formatNumber(relErr) + '%';
    formulaHTML += '<br>Δ = ±(<span class="greek-delta">δ</span>/100)·|X| = ±' + formatNumber(absErr);
    let html = '<div class="converter-result-label-title">Результаты расчёта (ГОСТ 8.401-80)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value">c/d = ' + formatNumber(c) + '/' + formatNumber(d) + ' (относительная)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Относительная погрешность (±<span class="greek-delta">δ</span>)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(relErr) + ' %</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Абсолютная погрешность (±Δ)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(absErr) + ' ед.изм.</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула расчёта</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaHTML + ' ед.изм.</span></div>';
    document.getElementById('egf_results').innerHTML = html;
    document.getElementById('egf_results').style.display = 'block';
    setTimeout(() => document.getElementById('egf_results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}


export {
    unitData,
    sigUnitLabels,
    convertUnits,
    convertTemp,
    calcScaleSignal,
    showConverterTable,
    showTempTable,
    setSignalDefaults,
    setScaleDefaults,
    toggleErrorClassFields,
    toggleEpCustomClass,
    calcPressureError,
    toggleElCustomClass,
    calcLevelError,
    toggleEfCustomClass,
    calcFlowmeterError,
    calcErrorGOST,
    toggleEgnCustomClass,
    calcGenericNumber,
    toggleEguCustomClass,
    calcGenericUnderline,
    toggleEgcCustomClass,
    calcGenericCircle,
    toggleEgfCustomC,
    toggleEgfCustomD,
    calcGenericFraction,
    validateNumericField,
    validatePositiveField,
    validateNonNegativeField,
    validateRangeField
};
