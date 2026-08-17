/**
 * @module calculators/rtd-tc
 * RTD and Thermocouple error calculators, scale and weighing instrument error calculators
 */
const showToast = window.showToast;
const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const roundNumber = window.roundNumber;
const validateField = window.validateField;
const clearFieldError = window.clearFieldError;

const rtdData = {
    'pt10': { name:'10П (Pt10)', group:'Pt', r0:10, nsc:'10П', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-100,450]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-196,600]}, classC:{formula:{const:0.60,coeff:0.0100},range:[-196,600]} },
    'pt50': { name:'50П (Pt50)', group:'Pt', r0:50, nsc:'50П', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-100,450]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-196,600]}, classC:{formula:{const:0.60,coeff:0.0100},range:[-196,600]} },
    'pt100': { name:'100П (Pt100)', group:'Pt', r0:100, nsc:'100П', classAA:{formula:{const:0.10,coeff:0.0017},range:[-50,250]}, classA:{formula:{const:0.15,coeff:0.0020},range:[-100,450]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-196,600]}, classC:{formula:{const:0.60,coeff:0.0100},range:[-196,600]} },
    'pt500': { name:'500П (Pt500)', group:'Pt', r0:500, nsc:'500П', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-200,600]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-200,600]}, classC:{formula:{const:0.60,coeff:0.0100},range:[-200,600]} },
    'pt1000': { name:'1000П (Pt1000)', group:'Pt', r0:1000, nsc:'1000П', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-200,600]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-200,600]}, classC:{formula:{const:0.60,coeff:0.0100},range:[-200,600]} },
    'cu10': { name:'10М (Cu10)', group:'Cu', r0:10, nsc:'10М', classAA:null, classA:null, classB:{formula:{const:0.30,coeff:0.0050},range:[-50,180]}, classC:null },
    'cu50': { name:'50М (Cu50)', group:'Cu', r0:50, nsc:'50М', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-50,180]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-50,180]}, classC:null },
    'cu100': { name:'100М (Cu100)', group:'Cu', r0:100, nsc:'100М', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-50,180]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-50,180]}, classC:null },
    'ni50': { name:'50Н (Ni50)', group:'Ni', r0:50, nsc:'50Н', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-60,180]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-60,180]}, classC:null },
    'ni100': { name:'100Н (Ni100)', group:'Ni', r0:100, nsc:'100Н', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-60,180]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-60,180]}, classC:null },
    'ni120': { name:'120Н (Ni120)', group:'Ni', r0:120, nsc:'120Н', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-60,180]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-60,180]}, classC:null },
    'ni500': { name:'500Н (Ni500)', group:'Ni', r0:500, nsc:'500Н', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-60,180]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-60,180]}, classC:null },
    'ni1000': { name:'1000Н (Ni1000)', group:'Ni', r0:1000, nsc:'1000Н', classAA:null, classA:{formula:{const:0.15,coeff:0.0020},range:[-60,180]}, classB:{formula:{const:0.30,coeff:0.0050},range:[-60,180]}, classC:null }
};
function updateRtdTypeOptions(){ let g=document.getElementById('rtd_group').value; let typeSel=document.getElementById('rtd_type'); let classSel=document.getElementById('rtd_class'); let opts=''; if(g==='Pt'){ opts='<option value="pt10">10П (Pt10)</option><option value="pt50">50П (Pt50)</option><option value="pt100" selected>100П (Pt100)</option><option value="pt500">500П (Pt500)</option><option value="pt1000">1000П (Pt1000)</option>'; classSel.innerHTML='<option value="AA" data-hint="высокоточный">AA</option><option value="A" selected data-hint="точный">A</option><option value="B" data-hint="стандартный">B</option><option value="C" data-hint="грубый">C</option>'; } else if(g==='Cu'){ opts='<option value="cu10">10М (Cu10)</option><option value="cu50" selected>50М (Cu50)</option><option value="cu100">100М (Cu100)</option>'; classSel.innerHTML='<option value="A" data-hint="точный">A</option><option value="B" selected data-hint="стандартный">B</option><option value="C" data-hint="грубый">C</option>'; } else if(g==='Ni'){ opts='<option value="ni50">50Н (Ni50)</option><option value="ni100">100Н (Ni100)</option><option value="ni120">120Н (Ni120)</option><option value="ni500">500Н (Ni500)</option><option value="ni1000" selected>1000Н (Ni1000)</option>'; classSel.innerHTML='<option value="A" data-hint="точный">A</option><option value="B" selected data-hint="стандартный">B</option><option value="C" data-hint="грубый">C</option>'; } typeSel.innerHTML=opts; updateRtdClassOptions(); }
function updateRtdClassOptions(){ let type=document.getElementById('rtd_type').value; let d=rtdData[type]; let classSel=document.getElementById('rtd_class'); if(!d)return; for(let i=0;i<classSel.options.length;i++){ let opt=classSel.options[i]; let key='class'+opt.value.toUpperCase(); let avail=!!d[key]; opt.disabled=!avail; if(!avail&&opt.selected){ for(let j=0;j<classSel.options.length;j++){ if(!classSel.options[j].disabled){ classSel.options[j].selected=true; break; } } } } }
function calcRtdError(){ let type=document.getElementById('rtd_type').value; let cls=document.getElementById('rtd_class').value.toLowerCase(); let t=parseLocaleNumber(document.getElementById('rtd_temperature').value); let warn=document.getElementById('rtd_range_warning'); if(isNaN(t)){showToast('Введите температуру');return;} let d=rtdData[type]; if(!d){showToast('Некорректный тип ТС');return;} let data=d['class'+cls.toUpperCase()]; if(!data){showToast(`Класс ${cls.toUpperCase()} не определён`);return;} let absT=Math.abs(t); let err=data.formula.const+data.formula.coeff*absT; let rng=data.range; if(t<rng[0]||t>rng[1]){ warn.style.display='block'; warn.innerHTML=` Температура ${formatNumber(t)}°C вне диапазона [${formatNumber(rng[0])}…${formatNumber(rng[1])}]°C`; }else warn.style.display='none'; let groupNames={Pt:'Платиновый (Pt)',Cu:'Медный (Cu)',Ni:'Никелевый (Ni)'}; let html=`<div class="converter-result-label-title">Результаты (ГОСТ 6651-2009)</div><div class="converter-result-item"><span class="converter-result-label">Тип ТС</span><span class="converter-result-value">${d.name}</span></div><div class="converter-result-item"><span class="converter-result-label">Материал</span><span class="converter-result-value">${groupNames[d.group]}</span></div><div class="converter-result-item"><span class="converter-result-label">R₀ (0°C)</span><span class="converter-result-value">${d.r0} Ом</span></div><div class="converter-result-item"><span class="converter-result-label">Класс допуска</span><span class="converter-result-value">${cls.toUpperCase()}</span></div><div class="converter-result-item"><span class="converter-result-label">Предел погрешности</span><span class="converter-result-value" style="color:#4ac771;">± ${formatNumber(err)} °C</span></div><div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">Δ = ±(${formatNumber(data.formula.const)} + ${formatNumber(data.formula.coeff)}·|t|) °C</span></div><div class="converter-result-item"><span class="converter-result-label">Диапазон</span><span class="converter-result-value">${formatNumber(rng[0])} … ${formatNumber(rng[1])} °C</span></div>`; document.getElementById('rtdResults').innerHTML=html; document.getElementById('rtdResults').style.display='block'; setTimeout(()=>document.getElementById('rtdResults').scrollIntoView({behavior:'smooth',block:'start'}),100); }

const tcData={
    'K':{name:'ТХА (K)',ranges:{class1:[[-40,375,'const',1.5],[375,1000,'linear',0.004]],class2:[[-40,333,'const',2.5],[333,1300,'linear',0.0075]],class3:[[-250,-167,'linear',0.015],[-167,40,'const',2.5]]}},
    'J':{name:'ТЖК (J)',ranges:{class1:[[-40,375,'const',1.5],[375,750,'linear',0.004]],class2:[[0,333,'const',2.5],[333,900,'linear',0.0075]],class3:null}},
    'T':{name:'ТМК (T)',ranges:{class1:[[-40,125,'const',0.5],[125,350,'linear',0.004]],class2:[[-40,135,'const',1.0],[135,350,'linear',0.0075]],class3:[[-200,-66,'linear',0.015],[-66,40,'const',1.0]]}},
    'N':{name:'ТНН (N)',ranges:{class1:[[-40,375,'const',1.5],[375,1000,'linear',0.004]],class2:[[-40,333,'const',2.5],[333,1300,'linear',0.0075]],class3:[[-250,-167,'linear',0.015],[-167,40,'const',2.5]]}},
    'E':{name:'ТХКн (E)',ranges:{class1:[[-40,375,'const',1.5],[375,800,'linear',0.004]],class2:[[-40,333,'const',2.5],[333,900,'linear',0.0075]],class3:[[-200,-167,'linear',0.015],[-167,40,'const',2.5]]}},
    'R':{name:'R (ТПП 13% Rh)',ranges:{class1:[[0,1100,'const',1.0],[1100,1600,'linear2',[1.0,0.003]]],class2:[[0,600,'const',1.5],[600,1600,'linear',0.0025]],class3:null}},
    'S':{name:'S (ТПП 10% Rh)',ranges:{class1:[[0,1100,'const',1.0],[1100,1600,'linear2',[1.0,0.003]]],class2:[[0,600,'const',1.5],[600,1600,'linear',0.0025]],class3:null}},
    'B':{name:'B (ТПР 30/6%)',ranges:{class1:null,class2:[[600,1700,'linear',0.005]],class3:[[600,800,'const',4.0],[800,1700,'linear',0.005]]}}
};
function updateTcRanges(){ let type=document.getElementById('tc_type').value; let cls=document.getElementById('tc_class').value; let warn=document.getElementById('tc_range_warning'); if(tcData[type] && tcData[type].ranges['class'+cls]) warn.style.display='none'; }
function calcTcError(){ let type=document.getElementById('tc_type').value; let cls=document.getElementById('tc_class').value; let t=parseLocaleNumber(document.getElementById('tc_temperature').value); let warn=document.getElementById('tc_range_warning'); if(isNaN(t)){showToast('Введите температуру');return;} let data=tcData[type]; if(!data){showToast('Некорректный тип термопары');return;} let classData=data.ranges['class'+cls]; if(!classData){showToast(`Класс ${cls} не определён`);return;} let absT=Math.abs(t); let err=null, formula='', valid=''; for(let i=0;i<classData.length;i++){ let r=classData[i]; if(t>=r[0]&&t<=r[1]){ if(r[2]==='const'){ err=r[3]; formula=`Δ = ±${String(r[3]).replace('.',',')} °C`; } else if(r[2]==='linear'){ err=r[3]*absT; formula=`Δ = ±(${String(r[3]).replace('.',',')}·|t|) °C`; } else if(r[2]==='linear2'){ let p=r[3]; err=p[0]+p[1]*(t-1100); formula=`Δ = ±[${String(p[0]).replace('.',',')} + ${String(p[1]).replace('.',',')}·(t−1100)] °C`; } valid=`${formatNumber(r[0])} … ${formatNumber(r[1])} °C`; break; } } if(err===null||isNaN(err)){ warn.style.display='block'; warn.innerHTML=` Температура ${formatNumber(t)}°C вне допустимого диапазона для данного класса`; return; } else warn.style.display='none'; let html=`<div class="converter-result-label-title">Результаты (ГОСТ Р 8.585-2001)</div><div class="converter-result-item"><span class="converter-result-label">Тип термопары</span><span class="converter-result-value">${data.name}</span></div><div class="converter-result-item"><span class="converter-result-label">Класс точности (<span class="greek-gamma">&gamma;</span>)</span><span class="converter-result-value">${cls}</span></div><div class="converter-result-item"><span class="converter-result-label">Предел погрешности</span><span class="converter-result-value" style="color:#4ac771;">± ${formatNumber(err)} °C</span></div><div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">${formula}</span></div><div class="converter-result-item"><span class="converter-result-label">Диапазон</span><span class="converter-result-value">${valid}</span></div>`; document.getElementById('tcResults').innerHTML=html; document.getElementById('tcResults').style.display='block'; setTimeout(()=>document.getElementById('tcResults').scrollIntoView({behavior:'smooth',block:'start'}),100); }

// Весы — расчёт погрешности
function toggleScaleTypeFields() {
    let type = document.getElementById('ws_type').value;
    document.getElementById('ws_mech_group').style.display = type === 'mechanical' ? 'block' : 'none';
    document.getElementById('ws_elc_group').style.display = type === 'electronic_lc' ? 'block' : 'none';
    document.getElementById('ws_els_group').style.display = type === 'electronic_simple' ? 'block' : 'none';
    document.getElementById('ws_ref_mech').style.display = type === 'mechanical' ? 'block' : 'none';
    document.getElementById('ws_ref_elc').style.display = type === 'electronic_lc' ? 'block' : 'none';
    document.getElementById('ws_ref_els').style.display = type === 'electronic_simple' ? 'block' : 'none';
}

function wsUnitFactor(unit) {
    let factors = {'mg':0.001, 'g':1, 'kg':1000, 't':1000000};
    return factors[unit] || 1;
}
function wsUnitLabel(unit) {
    let labels = {'mg':'мг', 'g':'г', 'kg':'кг', 't':'т'};
    return labels[unit] || unit;
}

function calcScaleError() {
    let type = document.getElementById('ws_type').value;
    if (type === 'mechanical') {
        calcMechScaleError();
    } else if (type === 'electronic_lc') {
        calcElcScaleError();
    } else {
        calcElsScaleError();
    }
}

// Пределы погрешности по ГОСТ OIML R 76-1-2011 (таблица 3)
// mpe = ±e при 0 < m ≤ 500e; ±2e при 500e < m ≤ 2000e; ±3e при 2000e < m ≤ Max
// Для класса I: mpe = ±e при 0 < m ≤ 50000e; ±2e при 50000e < m ≤ 200000e; ±3e при 200000e < m
function getOimlMpe(oimlClass, loadInE) {
    // loadInE = нагрузка, выраженная в числе поверочных делений e
    if (loadInE <= 0) return 0;
    if (oimlClass === 'I') {
        if (loadInE <= 50000) return 1;
        if (loadInE <= 200000) return 2;
        return 3;
    } else if (oimlClass === 'II') {
        if (loadInE <= 5000) return 1;
        if (loadInE <= 20000) return 2;
        return 3;
    } else if (oimlClass === 'III') {
        if (loadInE <= 500) return 1;
        if (loadInE <= 2000) return 2;
        return 3;
    } else { // IIII
        if (loadInE <= 50) return 1;
        if (loadInE <= 200) return 2;
        return 3;
    }
}

function calcMechScaleError() {
    let oimlClass = document.getElementById('ws_mech_oiml_class').value;
    let n = parseLocaleNumber(document.getElementById('ws_mech_n').value);
    let e = parseLocaleNumber(document.getElementById('ws_mech_e').value);
    let eUnit = document.getElementById('ws_mech_e_unit').value;
    let maxVal = parseLocaleNumber(document.getElementById('ws_mech_max').value);
    let maxUnit = document.getElementById('ws_mech_max_unit').value;

    if (isNaN(n) || n <= 0) { showToast('Введите число поверочных делений'); return; }
    if (isNaN(e) || e <= 0) { showToast('Введите цену поверочного деления'); return; }
    if (isNaN(maxVal) || maxVal <= 0) { showToast('Введите НПВ'); return; }

    let eInGrams = e * wsUnitFactor(eUnit);
    let maxInGrams = maxVal * wsUnitFactor(maxUnit);
    let unitLabel = wsUnitLabel(eUnit);

    let html = '<div class="converter-result-label-title">Результаты расчёта (механические весы)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value">' + oimlClass + ' (ГОСТ OIML R 76-1-2011)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">НПВ (Max)</span><span class="converter-result-value">' + formatNumber(maxVal) + ' ' + wsUnitLabel(maxUnit) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Число поверочных делений (n)</span><span class="converter-result-value">' + formatNumber(n) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Цена поверочного деления (e)</span><span class="converter-result-value">' + formatNumber(e) + ' ' + unitLabel + '</span></div>';

    // Таблица пределов погрешности по диапазонам
    let tableHtml = '<table style="min-width:100%;width:100%;border-collapse:collapse;">';
    tableHtml += '<thead><tr style="background:rgba(22,27,34,0.7);"><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">Диапазон нагрузки</th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">МПЕ (±)</th></tr></thead><tbody>';

    let ranges = [];
    if (oimlClass === 'I') {
        ranges = [[0, 50000, 1], [50000, 200000, 2], [200000, n, 3]];
    } else if (oimlClass === 'II') {
        ranges = [[0, 5000, 1], [5000, 20000, 2], [20000, n, 3]];
    } else if (oimlClass === 'III') {
        ranges = [[0, 500, 1], [500, 2000, 2], [2000, n, 3]];
    } else {
        ranges = [[0, 50, 1], [50, 200, 2], [200, n, 3]];
    }

    for (let i = 0; i < ranges.length; i++) {
        let r = ranges[i];
        let upperE = Math.min(r[1], n);
        if (r[0] >= n) continue;
        let lowerMass = r[0] * e;
        let upperMass = upperE * e;
        let mpe = r[2] * e;
        let bg = i % 2 ? 'rgba(22,27,34,0.4)' : 'rgba(13,17,23,0.4)';
        tableHtml += '<tr style="background:' + bg + ';"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.6);">от ' + formatNumber(lowerMass) + ' до ' + formatNumber(upperMass) + ' ' + unitLabel + '</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">± ' + formatNumber(mpe) + ' ' + unitLabel + ' (' + r[2] + 'e)</td></tr>';
    }
    tableHtml += '</tbody></table>';

    html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; margin-bottom:0;"><div class="converter-result-label-title">Пределы погрешности по диапазонам</div><button type="button" class="query-btn" onclick="copyCalcTable(\'wsTableContainer\')" style="width:auto; padding:5px 10px; font-size:11px;"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>Копировать</button></div>';
    html += '<div id="wsTableContainer" style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.05);">' + tableHtml + '</div>';

    document.getElementById('ws_results').innerHTML = html;
    document.getElementById('ws_results').style.display = 'block';
    setTimeout(() => document.getElementById('ws_results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

function calcElcScaleError() {
    let lcClass = document.getElementById('ws_lc_class').value;
    let lcN = parseLocaleNumber(document.getElementById('ws_lc_n').value);
    let lcE = parseLocaleNumber(document.getElementById('ws_lc_e').value);
    let lcCount = parseInt(document.getElementById('ws_lc_count').value);
    let jboxErr = parseLocaleNumber(document.getElementById('ws_jbox_err').value);
    let jboxErrUnit = document.getElementById('ws_jbox_err_unit').value;
    let jboxSigMax = parseLocaleNumber(document.getElementById('ws_jbox_sig_max').value);
    let moduleClass = parseLocaleNumber(document.getElementById('ws_module_class').value);
    let moduleSigMin = parseLocaleNumber(document.getElementById('ws_module_sig_min').value);
    let moduleSigMax = parseLocaleNumber(document.getElementById('ws_module_sig_max').value);
    let maxVal = parseLocaleNumber(document.getElementById('ws_elc_max').value);
    let maxUnit = document.getElementById('ws_elc_max_unit').value;

    if (isNaN(lcN) || lcN <= 0) { showToast('Введите число поверочных делений тензодатчика'); return; }
    if (isNaN(lcE) || lcE <= 0) { showToast('Введите цену поверочного деления тензодатчика'); return; }
    if (isNaN(jboxErr) || jboxErr < 0) { showToast('Введите погрешность БК'); return; }
    if (isNaN(jboxSigMax) || jboxSigMax <= 0) { showToast('Введите выходной сигнал БК при Max'); return; }
    if (isNaN(moduleClass) || moduleClass <= 0) { showToast('Введите класс точности модуля ввода'); return; }
    if (isNaN(moduleSigMin) || isNaN(moduleSigMax) || moduleSigMin >= moduleSigMax) { showToast('Введите корректный диапазон входного сигнала модуля'); return; }
    if (isNaN(maxVal) || maxVal <= 0) { showToast('Введите НПВ'); return; }

    let unitLabel = wsUnitLabel(maxUnit);

    // 1. Погрешность тензодатчика(ов) по OIML R 60 (при Max)
    let lcMpeMultiplier = getOimlMpeR60(lcClass, lcN);
    let lcMpePerUnit = lcMpeMultiplier * lcE;
    let lcMpeInMV = (lcMpePerUnit / maxVal) * jboxSigMax;
    if (lcCount > 1) {
        lcMpeInMV = lcMpeInMV * Math.sqrt(lcCount);
    }

    // 2. Погрешность БК (при Max)
    let jboxAbsMV;
    if (jboxErrUnit === 'pct') {
        jboxAbsMV = (jboxErr / 100) * jboxSigMax;
    } else {
        jboxAbsMV = jboxErr;
    }

    // 3. Погрешность модуля ввода АСУТП
    let moduleRange = moduleSigMax - moduleSigMin;
    let moduleAbsMV = (moduleClass / 100) * moduleRange;

    // Функция расчёта суммарной погрешности при нагрузке m (в мВ)
    function calcTotalMVAtLoad(loadMass) {
        let frac = loadMass / maxVal;
        let lcMV = lcMpeInMV * frac;                           // пропорционально нагрузке
        let jboxMV = jboxErrUnit === 'pct' ? jboxAbsMV * frac : jboxAbsMV;  // %: пропорц., мВ: const
        let modMV = moduleAbsMV;                                // const (приведённая)
        return 1.1 * Math.sqrt(lcMV * lcMV + jboxMV * jboxMV + modMV * modMV);
    }

    // Пересчёт мВ → единицы массы
    function mvToMass(mv) {
        return (mv / jboxSigMax) * maxVal;
    }

    // Суммарная погрешность при Max
    let totalAbsMV = calcTotalMVAtLoad(maxVal);
    let totalAbsMass = mvToMass(totalAbsMV);

    // === Автоматическое определение класса точности и e ===
    // МПЕ при Max = ±3e (по OIML R 76-1-2011) → e_min = Δ_Σ(Max) / 3
    let eMin = totalAbsMass / 3;
    let eSys = roundUpToStandardE(eMin);
    let nSys = Math.floor(maxVal / eSys);
    let sysClass = getClassFromN(nSys);
    let classWarning = '';

    // Итеративная проверка: расчётная Δ_Σ не должна превышать МПЕ во всех диапазонах
    for (let iter = 0; iter < 10; iter++) {
        if (!sysClass) break;
        let ranges = getClassRanges(sysClass);
        let passAll = true;

        for (let i = 0; i < ranges.length; i++) {
            let upperE = (i < ranges.length - 1) ? ranges[i + 1] : nSys;
            if (ranges[i] >= nSys) continue;
            upperE = Math.min(upperE, nSys);
            let testLoad = upperE * eSys;
            let actualMass = mvToMass(calcTotalMVAtLoad(testLoad));
            let mpe = (i + 1) * eSys;
            if (actualMass > mpe * 1.005) { // допуск 0.5% на округление
                passAll = false;
                break;
            }
        }

        if (passAll) break;

        // Увеличить e до следующего стандартного значения
        let nextE = getNextStandardE(eSys);
        if (nextE === eSys) break; // не удалось увеличить
        eSys = nextE;
        nSys = Math.floor(maxVal / eSys);
        let newClass = getClassFromN(nSys);
        if (newClass !== sysClass) {
            classWarning = 'Класс понижен: система не проходит поверку по классу ' + getClassName(sysClass) + ' при e = ' + formatNumber(eSys) + ' ' + unitLabel;
        }
        sysClass = newClass;
    }

    // === Генерация результатов ===
    let html = '<div class="converter-result-label-title">Результаты расчёта (ТВЭУ)</div>';

    // Параметры компонентов
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс тензодатчика (OIML R 60)</span><span class="converter-result-value">' + lcClass + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">n<sub>LC</sub> (число поверочных делений)</span><span class="converter-result-value">' + formatNumber(lcN) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Количество тензодатчиков</span><span class="converter-result-value">' + lcCount + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">НПВ (Max)</span><span class="converter-result-value">' + formatNumber(maxVal) + ' ' + unitLabel + '</span></div>';

    // Составляющие погрешности при Max (в мВ)
    html += '<div style="margin-top:8px;padding:6px 0;font-size:12px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.5px;">Составляющие погрешности при Max (в <span style="text-transform:none;">мВ</span>)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Погрешность тензодатчика</span><span class="converter-result-value" style="color:#4a8fc7;">\u00B1 ' + formatNumber(lcMpeInMV) + ' <span style="text-transform:none;">мВ</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Погрешность балансировочной коробки</span><span class="converter-result-value" style="color:#4a8fc7;">\u00B1 ' + formatNumber(jboxAbsMV) + ' <span style="text-transform:none;">мВ</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Погрешность модуля ввода АСУТП</span><span class="converter-result-value" style="color:#4a8fc7;">\u00B1 ' + formatNumber(moduleAbsMV) + ' <span style="text-transform:none;">мВ</span></span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Суммарная абс. погрешность</span><span class="converter-result-value" style="color:#4a8fc7;">\u00B1 ' + formatNumber(totalAbsMV) + ' <span style="text-transform:none;">мВ</span> (' + formatNumber(totalAbsMass) + ' ' + unitLabel + ')</span></div>';

    // Автоматически определённые параметры весов
    html += '<div style="margin-top:12px;padding:6px 0;font-size:12px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.5px;">Параметры весов (определены автоматически)</div>';

    if (sysClass) {
        html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value" style="color:#4ac771;">' + getClassName(sysClass) + ' (ГОСТ OIML R 76-1-2011)</span></div>';
        html += '<div class="converter-result-item"><span class="converter-result-label">Поверочное деление <span style="text-transform:none;font-style:italic;">e</span></span><span class="converter-result-value">' + formatNumber(eSys) + ' ' + unitLabel + '</span></div>';
        html += '<div class="converter-result-item"><span class="converter-result-label">Число поверочных делений <span style="text-transform:none;font-style:italic;">n</span> = Max/<span style="text-transform:none;font-style:italic;">e</span></span><span class="converter-result-value">' + formatNumber(nSys) + '</span></div>';

        if (classWarning) {
            html += '<div class="converter-result-item" style="background:rgba(231,76,60,0.08);border:1px solid rgba(231,76,60,0.2);border-radius:8px;padding:8px 12px;"><span class="converter-result-label" style="color:#e74c3c;">Внимание</span><span class="converter-result-value" style="color:#e74c3c;font-size:12px;">' + classWarning + '</span></div>';
        }
    } else {
        html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value" style="color:#e74c3c;">Не классифицируется (n < 100)</span></div>';
        html += '<div class="converter-result-item" style="background:rgba(231,76,60,0.08);border:1px solid rgba(231,76,60,0.2);border-radius:8px;padding:8px 12px;"><span class="converter-result-label" style="color:#e74c3c;">Причина</span><span class="converter-result-value" style="color:#e74c3c;font-size:12px;">Суммарная погрешность системы слишком велика. Уменьшите погрешность компонентов или НПВ.</span></div>';
    }

    // Таблица погрешности по диапазонам нагрузки
    if (sysClass) {
        let ranges = getClassRanges(sysClass);
        let tableHtml = '<table style="min-width:100%;width:100%;border-collapse:collapse;">';
        tableHtml += '<thead><tr style="background:rgba(22,27,34,0.7);"><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">Диапазон нагрузки</th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">МПЕ OIML R 76</th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">Расчётная \u0394<sub>\u03A3</sub></th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:center;">Запас</th></tr></thead><tbody>';

        for (let i = 0; i < ranges.length; i++) {
            let lowerE = ranges[i];
            let upperE = (i < ranges.length - 1) ? ranges[i + 1] : nSys;
            if (lowerE >= nSys) continue;
            upperE = Math.min(upperE, nSys);
            if (lowerE >= upperE) continue;

            let lowerMass = lowerE * eSys;
            let upperMass = upperE * eSys;
            let mpeMultiplier = i + 1;
            let mpe = mpeMultiplier * eSys;

            // Расчётная погрешность на верхней границе диапазона
            let actualMV = calcTotalMVAtLoad(upperMass);
            let actualMass = mvToMass(actualMV);
            let pass = actualMass <= mpe * 1.005;
            let margin = ((mpe - actualMass) / mpe * 100);

            let bg = i % 2 ? 'rgba(22,27,34,0.4)' : 'rgba(13,17,23,0.4)';
            tableHtml += '<tr style="background:' + bg + ';">';
            tableHtml += '<td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.6);">от ' + formatNumber(lowerMass) + ' до ' + formatNumber(upperMass) + ' ' + unitLabel + '</td>';
            tableHtml += '<td style="padding:8px 12px;font-size:14px;color:#4ac771;">\u00B1 ' + formatNumber(mpe) + ' ' + unitLabel + ' (' + mpeMultiplier + '<span style="text-transform:none;font-style:italic;">e</span>)</td>';
            tableHtml += '<td style="padding:8px 12px;font-size:14px;' + (pass ? 'color:rgba(255,255,255,0.6);' : 'color:#e74c3c;') + '">\u00B1 ' + formatNumber(actualMass) + ' ' + unitLabel + '</td>';
            tableHtml += '<td style="padding:8px 12px;font-size:14px;text-align:center;' + (pass ? 'color:#4ac771;' : 'color:#e74c3c;') + '">' + (pass ? (margin > 0 ? formatNumber(margin) + '%' : '<1%') : 'превышение') + '</td>';
            tableHtml += '</tr>';
        }

        tableHtml += '</tbody></table>';
        html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; margin-bottom:0;"><div class="converter-result-label-title">Погрешность по диапазонам нагрузки</div><button type="button" class="query-btn" onclick="copyCalcTable(\'wsTableContainer\')" style="width:auto; padding:5px 10px; font-size:11px;"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>Копировать</button></div>';
        html += '<div id="wsTableContainer" style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.05);">' + tableHtml + '</div>';
    }

    // Формула расчёта
    html += '<div style="margin-top:10px;padding:6px 0;font-size:12px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.5px;">Формулы расчёта</div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Суммарная погрешность</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">\u0394<sub>\u03A3</sub>(m) = K\u00B7\u221A(\u0394<sub>LC</sub>(m)\u00B2 + \u0394<sub>\u0411\u041A</sub>(m)\u00B2 + \u0394<sub>\u043C\u043E\u0434</sub>\u00B2), K=1,1, P=0,95<br>\u0394<sub>LC</sub>(m) \u221d m/Max (пропорц. нагрузке); \u0394<sub>\u0411\u041A</sub> = const (мВ) или \u221d m/Max (%); \u0394<sub>\u043C\u043E\u0434</sub> = const<br>\u0394<sub>\u043C\u0430\u0441\u0441\u0430</sub> = (\u0394<sub>\u03A3</sub>(<span style="text-transform:none;">мВ</span>) / U<sub>max</sub>) \u00B7 Max</span></div>';

    if (sysClass) {
        html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Определение <span style="text-transform:none;font-style:italic;">e</span> и класса</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;"><span style="text-transform:none;font-style:italic;">e</span><sub>min</sub> = \u0394<sub>\u03A3</sub>(Max) / 3 = ' + formatNumber(totalAbsMass) + ' / 3 = ' + formatNumber(eMin) + ' ' + unitLabel + '<br><span style="text-transform:none;font-style:italic;">e</span> = ' + formatNumber(eSys) + ' ' + unitLabel + ' (округлено до стандартного ряда 1, 2, 5 \u00D7 10<sup>k</sup>)<br><span style="text-transform:none;font-style:italic;">n</span> = Max/<span style="text-transform:none;font-style:italic;">e</span> = ' + formatNumber(maxVal) + '/' + formatNumber(eSys) + ' = ' + formatNumber(nSys) + ' \u2192 класс ' + getClassName(sysClass) + '</span></div>';
    }

    document.getElementById('ws_results').innerHTML = html;
    document.getElementById('ws_results').style.display = 'block';
    setTimeout(() => document.getElementById('ws_results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

// Пределы погрешности по OIML R 60 для тензодатчиков
function getOimlMpeR60(lcClass, nLC) {
    // Возвращает множитель MPE относительно e
    // Упрощённая модель: для класса B при nLC=3000 → MPE ≈ 1e при Max
    // Точнее: по OIML R 60, предел погрешности зависит от нагрузки
    // Для упрощения берём максимальный предел (при Max)
    if (lcClass === 'A') {
        if (nLC <= 50000) return 0.7;
        if (nLC <= 100000) return 1.0;
        return 1.5;
    } else if (lcClass === 'B') {
        if (nLC <= 5000) return 0.7;
        if (nLC <= 10000) return 1.0;
        return 1.5;
    } else if (lcClass === 'C') {
        if (nLC <= 2500) return 0.7;
        if (nLC <= 5000) return 1.0;
        return 1.5;
    } else { // D
        if (nLC <= 1000) return 0.7;
        if (nLC <= 2000) return 1.0;
        return 1.5;
    }
}

// Вспомогательные функции для автоматического определения класса точности ТВЭУ
function roundUpToStandardE(val) {
    if (val <= 0) return 1;
    let exp = Math.floor(Math.log10(val));
    let base = Math.pow(10, exp);
    let mantissa = val / base;
    if (mantissa <= 1) return base;
    if (mantissa <= 2) return 2 * base;
    if (mantissa <= 5) return 5 * base;
    return 10 * base;
}
function getNextStandardE(currentE) {
    let exp = Math.floor(Math.log10(currentE + 1e-15));
    let base = Math.pow(10, exp);
    let mantissa = currentE / base;
    if (mantissa < 1.5) return 2 * base;
    if (mantissa < 3.5) return 5 * base;
    if (mantissa < 7) return 10 * base;
    return 20 * base;
}
function getClassFromN(n) {
    if (n >= 50000) return 'I';
    if (n > 10000) return 'II';
    if (n > 1000) return 'III';
    if (n >= 100) return 'IIII';
    return null;
}
function getClassRanges(oimlClass) {
    if (oimlClass === 'I') return [0, 50000, 200000];
    if (oimlClass === 'II') return [0, 5000, 20000];
    if (oimlClass === 'III') return [0, 500, 2000];
    if (oimlClass === 'IIII') return [0, 50, 200];
    return [0, 500, 2000];
}
function getClassName(oimlClass) {
    let names = {'I': 'I (специальный)', 'II': 'II (высокий)', 'III': 'III (средний)', 'IIII': 'IIII (обычный)'};
    return names[oimlClass] || oimlClass;
}

function calcElsScaleError() {
    let oimlClass = document.getElementById('ws_els_oiml_class').value;
    let n = parseLocaleNumber(document.getElementById('ws_els_n').value);
    let e = parseLocaleNumber(document.getElementById('ws_els_e').value);
    let eUnit = document.getElementById('ws_els_e_unit').value;
    let maxVal = parseLocaleNumber(document.getElementById('ws_els_max').value);
    let maxUnit = document.getElementById('ws_els_max_unit').value;

    if (isNaN(n) || n <= 0) { showToast('Введите число поверочных делений'); return; }
    if (isNaN(e) || e <= 0) { showToast('Введите цену поверочного деления'); return; }
    if (isNaN(maxVal) || maxVal <= 0) { showToast('Введите НПВ'); return; }

    let eInGrams = e * wsUnitFactor(eUnit);
    let maxInGrams = maxVal * wsUnitFactor(maxUnit);
    let unitLabel = wsUnitLabel(eUnit);

    let html = '<div class="converter-result-label-title">Результаты расчёта (электронные весы автономные)</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Класс точности</span><span class="converter-result-value">' + oimlClass + ' (ГОСТ OIML R 76-1-2011)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">НПВ (Max)</span><span class="converter-result-value">' + formatNumber(maxVal) + ' ' + wsUnitLabel(maxUnit) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Число поверочных делений (n)</span><span class="converter-result-value">' + formatNumber(n) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Цена поверочного деления (e)</span><span class="converter-result-value">' + formatNumber(e) + ' ' + unitLabel + '</span></div>';

    // Таблица пределов погрешности
    let tableHtml = '<table style="min-width:100%;width:100%;border-collapse:collapse;">';
    tableHtml += '<thead><tr style="background:rgba(22,27,34,0.7);"><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">Диапазон нагрузки</th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">МПЕ (±)</th></tr></thead><tbody>';

    let ranges = [];
    if (oimlClass === 'I') {
        ranges = [[0, 50000, 1], [50000, 200000, 2], [200000, n, 3]];
    } else if (oimlClass === 'II') {
        ranges = [[0, 5000, 1], [5000, 20000, 2], [20000, n, 3]];
    } else if (oimlClass === 'III') {
        ranges = [[0, 500, 1], [500, 2000, 2], [2000, n, 3]];
    } else {
        ranges = [[0, 50, 1], [50, 200, 2], [200, n, 3]];
    }

    for (let i = 0; i < ranges.length; i++) {
        let r = ranges[i];
        let upperE = Math.min(r[1], n);
        if (r[0] >= n) continue;
        let lowerMass = r[0] * e;
        let upperMass = upperE * e;
        let mpe = r[2] * e;
        let bg = i % 2 ? 'rgba(22,27,34,0.4)' : 'rgba(13,17,23,0.4)';
        tableHtml += '<tr style="background:' + bg + ';"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.6);">от ' + formatNumber(lowerMass) + ' до ' + formatNumber(upperMass) + ' ' + unitLabel + '</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">± ' + formatNumber(mpe) + ' ' + unitLabel + ' (' + r[2] + 'e)</td></tr>';
    }
    tableHtml += '</tbody></table>';

    html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; margin-bottom:0;"><div class="converter-result-label-title">Пределы погрешности по диапазонам</div><button type="button" class="query-btn" onclick="copyCalcTable(\'wsTableContainer\')" style="width:auto; padding:5px 10px; font-size:11px;"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>Копировать</button></div>';
    html += '<div id="wsTableContainer" style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.05);">' + tableHtml + '</div>';

    document.getElementById('ws_results').innerHTML = html;
    document.getElementById('ws_results').style.display = 'block';
    setTimeout(() => document.getElementById('ws_results').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}


export {
    rtdData,
    tcData,
    calcRtdError,
    calcTcError,
    updateRtdTypeOptions,
    updateRtdClassOptions,
    updateTcRanges,
    toggleScaleTypeFields,
    calcScaleError,
    getOimlMpe,
    calcMechScaleError,
    calcElcScaleError,
    getOimlMpeR60,
    getNextStandardE,
    getClassFromN,
    getClassRanges,
    getClassName,
    calcElsScaleError
};
