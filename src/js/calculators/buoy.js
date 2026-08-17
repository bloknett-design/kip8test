/**
 * @module calculators/buoy
 * Buoyancy level meter calibration calculator
 */
const showToast = window.showToast;
const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const roundNumber = window.roundNumber;
const validateField = window.validateField;
const navigateTo = window.navigateTo;

// Буйковый уровнемер
const G = 9.80665;
function setLiquidDensity(){ let p=document.getElementById('liquid_preset').value; if(p!=='custom') document.getElementById('liquid_density').value=p; }
function getSignalRangeAndUnit(st){ let r={ '4_20':{min:4,max:20,unit:'мА',label:'4-20 мА'}, '0_20':{min:0,max:20,unit:'мА',label:'0-20 мА'}, '0_5mA':{min:0,max:5,unit:'мА',label:'0-5 мА'}, '0_10V':{min:0,max:10,unit:'В',label:'0-10 В'}, '1_5V':{min:1,max:5,unit:'В',label:'1-5 В'}, '0_5V':{min:0,max:5,unit:'В',label:'0-5 В'}, 'bipolar_10':{min:-10,max:10,unit:'В',label:'-10...+10 В'}, '20_100_kPa':{min:20,max:100,unit:'кПа',label:'20-100 кПа'}, '0_2_1_0_bar':{min:0.2,max:1.0,unit:'бар',label:'0,2-1,0 бар'}, '3_15_psi':{min:3,max:15,unit:'psi',label:'3-15 psi'}, '0_2_1_0_kgf_cm2':{min:0.2,max:1.0,unit:'кгс/см²',label:'0,2-1,0 кгс/см²'}, '0_100_pct':{min:0,max:100,unit:'%',label:'0-100 %'} }; if(st==='custom'){ let cmin=parseLocaleNumber(document.getElementById('sigMin').value); let cmax=parseLocaleNumber(document.getElementById('sigMax').value); let cunit=document.getElementById('sigUnitCustom').value; return { min:cmin, max:cmax, unit:cunit, label:(isNaN(cmin)?'?':formatNumber(cmin))+'-'+(isNaN(cmax)?'?':formatNumber(cmax))+' '+cunit, isCustom:true }; } return r[st]||r['4_20']; }
function getBuoySignalRangeAndUnit(st){ let r={ '4_20':{min:4,max:20,unit:'мА',label:'4-20 мА'}, '0_20':{min:0,max:20,unit:'мА',label:'0-20 мА'}, '0_5mA':{min:0,max:5,unit:'мА',label:'0-5 мА'}, '0_10V':{min:0,max:10,unit:'В',label:'0-10 В'}, '1_5V':{min:1,max:5,unit:'В',label:'1-5 В'}, '0_5V':{min:0,max:5,unit:'В',label:'0-5 В'}, 'bipolar_10':{min:-10,max:10,unit:'В',label:'-10...+10 В'}, '20_100_kPa':{min:20,max:100,unit:'кПа',label:'20-100 кПа'}, '0_2_1_0_bar':{min:0.2,max:1.0,unit:'бар',label:'0,2-1,0 бар'}, '3_15_psi':{min:3,max:15,unit:'psi',label:'3-15 psi'}, '0_2_1_0_kgf_cm2':{min:0.2,max:1.0,unit:'кгс/см²',label:'0,2-1,0 кгс/см²'} }; if(st==='custom'){ let cmin=parseLocaleNumber(document.getElementById('signal_min_custom').value); let cmax=parseLocaleNumber(document.getElementById('signal_max_custom').value); let cunit=document.getElementById('signal_unit_custom').value||'ед.'; return { min:cmin, max:cmax, unit:cunit, label:(isNaN(cmin)?'?':formatNumber(cmin))+'-'+(isNaN(cmax)?'?':formatNumber(cmax))+' '+cunit, isCustom:true }; } return r[st]||r['4_20']; }
function calculateBuoySignalValue(pct,st){ let r=getBuoySignalRangeAndUnit(st); if(r.isCustom && (isNaN(r.min)||isNaN(r.max))) return {value:0,unit:r.unit,isValid:false}; if(r.min===r.max) return {value:r.min,unit:r.unit,isValid:true}; return {value:r.min+(pct/100)*(r.max-r.min),unit:r.unit,isValid:true}; }
function updateBuoySignalUnit(){ let st=document.getElementById('buoy_signal_type').value; let cd=document.getElementById('customSignalRange'); let ud=document.getElementById('signalUnitDisplay'); if(st==='custom'){ cd.style.display='block'; let cmin=parseLocaleNumber(document.getElementById('signal_min_custom').value); let cmax=parseLocaleNumber(document.getElementById('signal_max_custom').value); let cunit=document.getElementById('signal_unit_custom').value||'мА'; ud.innerHTML=' Сигнал: '+(isNaN(cmin)?'?':formatNumber(cmin))+'–'+(isNaN(cmax)?'?':formatNumber(cmax))+' '+cunit; ud.style.color='#4ac771'; }else{ cd.style.display='none'; ud.innerHTML=' Сигнал: '+getBuoySignalRangeAndUnit(st).label; ud.style.color='rgba(255,255,255,0.25)'; } }
function calculateSignalValue(pct,st){ let r=getSignalRangeAndUnit(st); if(r.isCustom && (isNaN(r.min)||isNaN(r.max))) return {value:0,unit:r.unit,isValid:false}; if(r.min===r.max) return {value:r.min,unit:r.unit,isValid:true}; return {value:r.min+(pct/100)*(r.max-r.min),unit:r.unit,isValid:true}; }
function calcBuoyVolume(d,l){ let r=(d/1000)/2, l_m=l/1000; return Math.PI*r*r*l_m; }
function calcBuoyancyMass(pct,d,l,rho){ let l_m=l/1000, sub=(pct/100)*l_m; if(sub<=0)return 0; if(sub>l_m)sub=l_m; let r=(d/1000)/2; return Math.PI*r*r*sub*rho; }
function formatBuoyNumber(n){
    if(n===0)return '0';
    if(Math.abs(n)<0.0001)return n.toExponential(4).replace('.',',');
    let d=Math.abs(n)>=100?2:Math.abs(n)>=1?3:4;
    let s = parseFloat(n.toFixed(d)).toString().replace('.',',');
    // Разделяем разряды целой части неразрывным пробелом
    const parts = s.split(',');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '\u00A0');
    return parts.join(',');
}
let lastBuoyParams = null;

function clearBuoyCustomFields(exceptId) {
    if (exceptId !== 'buoyCustomLevel') document.getElementById('buoyCustomLevel').value = '';
    if (exceptId !== 'buoyCustomMass') document.getElementById('buoyCustomMass').value = '';
    if (exceptId !== 'buoyCustomSignal') document.getElementById('buoyCustomSignal').value = '';
}

function calcBuoyFromLevel() {
    if (!lastBuoyParams) return;
    let p = lastBuoyParams;
    let pctVal = parseLocaleNumber(document.getElementById('buoyCustomLevel').value);
    if (isNaN(pctVal)) { clearBuoyCustomFields('buoyCustomLevel'); return; }
    let clampedPct = Math.max(0, Math.min(100, pctVal));
    let m_buoy = calcBuoyancyMass(clampedPct, p.d, p.l, p.rho);
    let mass_kg = p.method === 'without_buoy' ? p.w - m_buoy + p.m_s : m_buoy + p.m_s;
    let sig = calculateBuoySignalValue(clampedPct, p.st);
    document.getElementById('buoyCustomMass').value = formatBuoyNumber(mass_kg * 1000);
    document.getElementById('buoyCustomSignal').value = formatBuoyNumber(sig.value);
}

function calcBuoyFromMass() {
    if (!lastBuoyParams) return;
    let p = lastBuoyParams;
    let massVal = parseLocaleNumber(document.getElementById('buoyCustomMass').value);
    if (isNaN(massVal)) { clearBuoyCustomFields('buoyCustomMass'); return; }
    let mass_kg = massVal / 1000;
    let m_buoy;
    if (p.method === 'without_buoy') {
        m_buoy = p.w + p.m_s - mass_kg;
    } else {
        m_buoy = mass_kg - p.m_s;
    }
    let r_m = (p.d / 1000) / 2;
    let l_m = p.l / 1000;
    let denom = Math.PI * r_m * r_m * l_m * p.rho;
    if (denom === 0) return;
    let pct = (m_buoy / denom) * 100;
    pct = Math.max(0, Math.min(100, pct));
    let sig = calculateBuoySignalValue(pct, p.st);
    document.getElementById('buoyCustomLevel').value = formatBuoyNumber(pct);
    document.getElementById('buoyCustomSignal').value = formatBuoyNumber(sig.value);
}

function calcBuoyFromSignal() {
    if (!lastBuoyParams) return;
    let p = lastBuoyParams;
    let sigVal = parseLocaleNumber(document.getElementById('buoyCustomSignal').value);
    if (isNaN(sigVal)) { clearBuoyCustomFields('buoyCustomSignal'); return; }
    let sigRange = getBuoySignalRangeAndUnit(p.st);
    let rangeDiff = sigRange.max - sigRange.min;
    if (rangeDiff === 0) return;
    let pct = ((sigVal - sigRange.min) / rangeDiff) * 100;
    pct = Math.max(0, Math.min(100, pct));
    let m_buoy = calcBuoyancyMass(pct, p.d, p.l, p.rho);
    let mass_kg = p.method === 'without_buoy' ? p.w - m_buoy + p.m_s : m_buoy + p.m_s;
    document.getElementById('buoyCustomLevel').value = formatBuoyNumber(pct);
    document.getElementById('buoyCustomMass').value = formatBuoyNumber(mass_kg * 1000);
}

function copyBuoyTable(){ copyCalcTable('buoyTableContainer'); }
function copyScaleTable(){ copyCalcTable('scaleTableContainer'); }
// Универсальная функция копирования таблицы из контейнера
function copyCalcTable(containerId){ let t=document.getElementById(containerId); if(!t){showToast('Нет данных');return;} let tbl=t.querySelector('table'); if(!tbl){showToast('Нет данных');return;} let rows=tbl.querySelectorAll('tr'), data=[]; for(let i=0;i<rows.length;i++){ let cells=rows[i].querySelectorAll('th,td'), row=[]; for(let j=0;j<cells.length;j++) row.push(cells[j].innerText.trim()); data.push(row.join('\t')); } navigator.clipboard.writeText(data.join('\n')).then(()=>showToast('Таблица скопирована')).catch(()=>showToast('Ошибка копирования')); }
function calculateBuoyCalibration(){ let d=parseLocaleNumber(document.getElementById('buoy_diam').value); let l=parseLocaleNumber(document.getElementById('buoy_length').value); let w=parseLocaleNumber(document.getElementById('buoy_weight_kg').value); let rho=parseLocaleNumber(document.getElementById('liquid_density').value); let m_s=parseLocaleNumber(document.getElementById('suspension_mass').value) / 1000; let st=document.getElementById('buoy_signal_type').value; let method=getSelectedCalibMethod(); if(isNaN(d)||d<=0){showToast('Введите диаметр');return;} if(isNaN(l)||l<=0){showToast('Введите длину');return;} if(method==='without_buoy'&&(isNaN(w)||w<=0)){showToast('Введите вес буйка');return;} if(isNaN(rho)||rho<=0){showToast('Введите плотность жидкости');return;} if(isNaN(m_s)||m_s<0){showToast('Введите массу подвеса');return;} let sigRange=getBuoySignalRangeAndUnit(st); if(st==='custom'&&(isNaN(sigRange.min)||isNaN(sigRange.max))){showToast('Введите диапазон сигнала');return;} let vol=calcBuoyVolume(d,l); let results=[]; for(let p=0;p<=100;p+=10){ let m_buoy=calcBuoyancyMass(p,d,l,rho); let mass_kg=method==='without_buoy'? w - m_buoy + m_s : m_buoy + m_s; let sig=calculateBuoySignalValue(p,st); results.push({pct:p, mass_kg:mass_kg, signal:sig.value, sigUnit:sig.unit}); } let html='<table style="min-width:100%;width:100%;border-collapse:collapse;"><thead><tr style="background:rgba(22,27,34,0.7);"><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;">Уровень (%)</th><th style="padding:10px 12px;font-size:13px;color:#4ac771;">Масса гирь (г)</th><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;">Сигнал ('+results[0].sigUnit+')</th></tr></thead><tbody>'; for(let i=0;i<results.length;i++){ let r=results[i]; let bg=i%2?'rgba(22,27,34,0.4)':'rgba(13,17,23,0.4)'; html+=`<tr style="background:${bg};"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">${r.pct}</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">${formatBuoyNumber(r.mass_kg*1000)}</td><td style="padding:8px 12px;font-size:14px;color:#5b9bd5;">${formatBuoyNumber(r.signal)}</td></tr>`; } html+='</tbody></table>'; let methodName=method==='without_buoy'?'Без буйка':'С буйком'; let formulaText=method==='without_buoy'?'m_гири = m_буйка − m_выт + m_подвеса':'m_гири = m_выт + m_подвеса'; let infoHtml=`<strong>${methodName}</strong><br> ${formulaText}<br>`; if(method==='without_buoy') infoHtml+=` Вес буйка: ${formatBuoyNumber(w)} кг<br>`; infoHtml+=` Плотность: ${formatBuoyNumber(rho)} кг/м³<br> Объём: ${formatBuoyNumber(vol*1e6)} см³<br> Масса гирь: ${formatBuoyNumber(results[results.length-1].mass_kg*1000)} г (100%)<br> Сигнал: ${sigRange.label}`; document.getElementById('buoyTableContainer').innerHTML=html; document.getElementById('buoyInfo').innerHTML=infoHtml; lastBuoyParams={d:d,l:l,w:w,rho:rho,m_s:m_s,st:st,method:method}; let sigUnitEl=document.getElementById('buoyCustomSigUnit'); if(sigUnitEl) sigUnitEl.innerText=results[0].sigUnit; document.getElementById('buoyCustomLevel').value=''; document.getElementById('buoyCustomMass').value=''; document.getElementById('buoyCustomSignal').value=''; document.getElementById('buoyCustomCalcPanel').style.display='block'; document.getElementById('buoyResults').style.display='block'; setTimeout(()=>document.getElementById('buoyResults').scrollIntoView({behavior:'smooth',block:'start'}),100); }
function selectCalibMethod(m){ localStorage.setItem('buoy_calib_method',m); navigateTo('buoy-calc'); }
function getSelectedCalibMethod(){ let m=localStorage.getItem('buoy_calib_method'); return (m==='with_buoy'||m==='without_buoy')?m:'with_buoy'; }
function setCalibMethodOnForm(){ let m=getSelectedCalibMethod(); let ind=document.getElementById('selectedMethodText'); if(ind) ind.innerText=m==='with_buoy'?'С буйком':'Без буйка'; updateBuoyCalcTitle(); let wCont=document.getElementById('buoyWeightContainer'); if(wCont) wCont.style.display=m==='with_buoy'?'none':'block'; }
function updateBuoyCalcTitle(){ let m=getSelectedCalibMethod(); let t=document.getElementById('buoyCalcTitle'); if(t) t.innerText=m==='with_buoy'?'Калибровка: с буйком':'Калибровка: без буйка'; }


export {
    G,
    lastBuoyParams,
    calculateBuoyCalibration,
    calcBuoyancyMass,
    calcBuoyVolume,
    formatBuoyNumber,
    getSignalRangeAndUnit,
    getBuoySignalRangeAndUnit,
    calculateBuoySignalValue,
    calculateSignalValue,
    setLiquidDensity,
    updateBuoySignalUnit,
    clearBuoyCustomFields,
    calcBuoyFromLevel,
    calcBuoyFromMass,
    calcBuoyFromSignal,
    copyBuoyTable,
    copyScaleTable,
    copyCalcTable,
    selectCalibMethod,
    getSelectedCalibMethod,
    setCalibMethodOnForm,
    updateBuoyCalcTitle
};
