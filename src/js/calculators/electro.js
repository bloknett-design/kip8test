/**
 * @module calculators/electro
 * Temperature sensor calculators — RTD resistance and thermocouple voltage (NIST ITS-90 polynomials)
 */
const showToast = window.showToast;
const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const roundNumber = window.roundNumber;
const copyCalcTable = window.copyCalcTable;

function updateTempSensorOptions(){
    let type=document.getElementById('temp_sensor_type').value;
    document.getElementById('rtd_options').style.display=type==='rtd'?'block':'none';
    document.getElementById('tc_options').style.display=type==='tc'?'block':'none';
}
function calcTempSensor(){
    let type=document.getElementById('temp_sensor_type').value;
    let tMin=parseLocaleNumber(document.getElementById('temp_sensor_min').value);
    let tMax=parseLocaleNumber(document.getElementById('temp_sensor_max').value);
    let step=parseLocaleNumber(document.getElementById('temp_sensor_step').value)||10;
    let resDiv=document.getElementById('tempSensorResults');
    if(isNaN(tMin)||isNaN(tMax)){showToast('Введите диапазон измерения');return;}
    if(tMin>=tMax){showToast('Минимум должен быть меньше максимума');return;}
    if(step<=0){step=10;}
    if(type==='rtd'){
        let rtdType=document.getElementById('temp_rtd_type').value;
        let sensorData={
            cu50_1428:{r0:50,alpha:0.00428,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
            cu100_1428:{r0:100,alpha:0.00428,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00428·t)'},
            cu50_1426:{r0:50,alpha:0.00426,name:'50М (Cu50)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00426·t)'},
            cu100_1426:{r0:100,alpha:0.00426,name:'100М (Cu100)',nsc:'cu',formula:'R(t) = R₀(1 + 0,00426·t)'},
            pt50_1391:{r0:50,name:'50П (Pt50)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},
            pt100_1391:{r0:100,name:'100П (Pt100)',nsc:'pt1391',formula:'R(t) = R₀[1 + At + Bt²], A=3,96847·10⁻³, B=−5,84·10⁻⁷'},
            pt100_1385:{r0:100,name:'Pt100 (IEC)',nsc:'pt1385',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³], IEC 60751 / ГОСТ 6651-2009'},
            pt1000_1385:{r0:1000,name:'Pt1000 (IEC)',nsc:'pt1385',formula:'R(t) = R₀[1 + At + Bt² + C(t−100)t³], IEC 60751 / ГОСТ 6651-2009'}
        };
        let sd=sensorData[rtdType];
        if(!sd){showToast('Неизвестный тип ТС');return;}
        let isCu=sd.nsc==='cu';
        let html=`<div class="converter-result-label-title">Результаты расчёта (ГОСТ 6651-2009)</div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">Тип ТС</span><span class="converter-result-value">${sd.name}</span></div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">Диапазон</span><span class="converter-result-value">${formatNumber(tMin)} … ${formatNumber(tMax)} °C</span></div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">R₀ (при 0°C)</span><span class="converter-result-value">${sd.r0} Ом</span></div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">${sd.formula}</span></div>`;
        html+=`<div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; margin-bottom:0;"><div class="converter-result-label-title">Таблица значений (шаг ${formatNumber(step)}°C)</div><button type="button" class="query-btn" onclick="copyCalcTable('tempTableContainer')" style="width:auto; padding:5px 10px; font-size:11px;"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>Копировать</button></div>`;
        html+=`<div id="tempTableContainer" style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.05);"><table style="min-width:100%;width:100%;border-collapse:collapse;"><thead><tr style="background:rgba(22,27,34,0.7);"><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">t, °C</th><th style="padding:10px 12px;font-size:13px;color:#4ac771;text-align:left;">R(t), Ом</th></tr></thead><tbody>`;
        let start=Math.ceil(tMin/step)*step;
        let end=Math.floor(tMax/step)*step;
        if(start>tMax||end<tMin){start=tMin;end=tMax;}
        let row=0;
        for(let tc=start;tc<=end;tc+=step){
            let rv=isCu?calcCuResistance(tc,sd.r0,sd.alpha):calcRtdResistance(tc,sd.r0,sd.nsc);
            let bg=row%2?'rgba(22,27,34,0.4)':'rgba(13,17,23,0.4)';
            html+=`<tr style="background:${bg};"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">${formatNumber(tc)}</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">${formatNumber(rv)}</td></tr>`;
            row++;
        }
        if(row===0){
            let rv=isCu?calcCuResistance(tMin,sd.r0,sd.alpha):calcRtdResistance(tMin,sd.r0,sd.nsc);
            html+=`<tr style="background:rgba(13,17,23,0.4);"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">${formatNumber(tMin)}</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">${formatNumber(rv)}</td></tr>`;
        }
        html+=`</tbody></table></div>`;
        resDiv.innerHTML=html;
    } else {
        let tcType=document.getElementById('temp_tc_type').value;
        let names={K:'ТХА (K)',J:'ТЖК (J)',T:'ТМК (T)',N:'ТНН (N)',E:'ТХКн (E)',R:'ТПП (R)',S:'ТПП (S)',B:'ТПР (B)'};
        let html=`<div class="converter-result-label-title">Результаты расчёта (ГОСТ Р 8.585-2001)</div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">Тип термопары</span><span class="converter-result-value">${names[tcType]}</span></div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">Диапазон</span><span class="converter-result-value">${formatNumber(tMin)} … ${formatNumber(tMax)} °C</span></div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">E(0°C)</span><span class="converter-result-value">0,000 мВ</span></div>`;
        html+=`<div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">E = Σ cᵢ·tⁱ (полином НИСТ)</span></div>`;
        html+=`<div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; margin-bottom:0;"><div class="converter-result-label-title">Таблица значений (шаг ${formatNumber(step)}°C)</div><button type="button" class="query-btn" onclick="copyCalcTable('tempTableContainer')" style="width:auto; padding:5px 10px; font-size:11px;"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>Копировать</button></div>`;
        html+=`<div id="tempTableContainer" style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.05);"><table style="min-width:100%;width:100%;border-collapse:collapse;"><thead><tr style="background:rgba(22,27,34,0.7);"><th style="padding:10px 12px;font-size:13px;color:#4a8fc7;text-align:left;">t, °C</th><th style="padding:10px 12px;font-size:13px;color:#4ac771;text-align:left;">E(t), мВ</th></tr></thead><tbody>`;
        let start=Math.ceil(tMin/step)*step;
        let end=Math.floor(tMax/step)*step;
        if(start>tMax||end<tMin){start=tMin;end=tMax;}
        let row=0;
        for(let tc=start;tc<=end;tc+=step){
            let ev=calcTcVoltage(tc,tcType);
            let bg=row%2?'rgba(22,27,34,0.4)':'rgba(13,17,23,0.4)';
            html+=`<tr style="background:${bg};"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">${formatNumber(tc)}</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">${formatNumber(ev)}</td></tr>`;
            row++;
        }
        if(row===0){
            let ev=calcTcVoltage(tMin,tcType);
            html+=`<tr style="background:rgba(13,17,23,0.4);"><td style="padding:8px 12px;font-size:14px;color:rgba(255,255,255,0.4);">${formatNumber(tMin)}</td><td style="padding:8px 12px;font-size:14px;color:#4ac771;">${formatNumber(ev)}</td></tr>`;
        }
        html+=`</tbody></table></div>`;
        resDiv.innerHTML=html;
    }
    resDiv.style.display='block';
    setTimeout(()=>resDiv.scrollIntoView({behavior:'smooth',block:'start'}),100);
}
function calcRtdResistance(t,r0,nsc){
    if(nsc==='pt1385'){
        let A=3.9083e-3, B=-5.775e-7, C=-4.183e-12;
        if(t>=0){ return r0*(1+A*t+B*t*t); }
        else { return r0*(1+A*t+B*t*t+C*(t-100)*t*t*t); }
    } else if(nsc==='pt1391'){
        let A=3.96847e-3, B=-5.84e-7;
        if(t>=0){ return r0*(1+A*t+B*t*t); }
        else { return r0*(1+A*t+B*t*t); }
    }
    return r0;
}
function calcCuResistance(t,r0,alpha){
    return r0*(1+alpha*t);
}
function calcTcVoltage(t,type){
    // Все коэффициенты — NIST ITS-90 (SRD 60), в мВ.
    // Полином: E(t) = c0 + c1·t + c2·t² + ... + cn·t^n
    // Коэффициенты записаны от низших степеней к высшим (c0, c1, c2, ...).
    // Источник: NIST Standard Reference Database 60, версия 2.0
    let mv=0;
    if(type==='K'){
        if(t<0){
            let c=[0,3.9450128025e-2,2.3622373598e-5,-3.2858906784e-7,-4.9904828777e-9,-6.7509059173e-11,-5.7410327428e-13,-3.1088872894e-15,-1.0451609365e-17,-1.9889266878e-20,-1.6322697487e-23];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else {
            let c=[-1.7600413686e-2,3.8921204975e-2,1.8558770032e-5,-9.9457592874e-8,3.1840945719e-10,-5.6072844889e-13,5.6075059059e-16,-3.2020720003e-19,9.7151147152e-23,-1.2104721275e-26];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
            mv+=1.185976e-1*Math.exp(-1.183432e-4*Math.pow(t-1.269686e2,2));
        }
    } else if(type==='J'){
        if(t>=0){
            let c=[0,5.0381187815e-2,3.0475836930e-5,-8.5681066720e-8,1.3228195295e-10,-1.7052958337e-13,2.0948090697e-16,-1.2538395336e-19,1.5631725697e-23];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else {
            let c=[0,5.0381187815e-2,3.0475836930e-5,-8.5681066720e-8,1.3228195295e-10,-1.7052958337e-13,2.0948090697e-16,-1.2538395336e-19,1.5631725697e-23];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        }
    } else if(type==='T'){
        // T (медь-константан): диапазоны -270..0°C и 0..400°C
        if(t>=0){
            // NIST ITS-90, диапазон 0..400°C (9 коэффициентов, степени 0..8)
            let c=[0, 3.8748106364e-2, 3.3292227880e-5, 2.0618243404e-7, -2.1882256846e-9, 1.0996880928e-11, -3.0815758772e-14, 4.5479135290e-17, -2.7512901673e-20];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else {
            // NIST ITS-90, диапазон -270..0°C (15 коэффициентов, степени 0..14)
            let c=[0, 3.8748106364e-2, 4.4194434347e-5, 1.1844323105e-7, 2.0032973554e-8, 9.0138019559e-10, 2.2651156593e-11, 3.6071154205e-13, 3.8493939883e-15, 2.8213521925e-17, 1.4251594779e-19, 4.8768662286e-22, 1.0795539270e-24, 1.3945027062e-27, 7.9795153927e-31];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        }
    } else if(type==='N'){
        // N (никросил-нисил): диапазоны -270..0°C и 0..1300°C
        if(t>=0){
            // NIST ITS-90, диапазон 0..1300°C (11 коэффициентов, степени 0..10)
            let c=[0, 2.5929394601e-2, 1.5710141880e-5, 4.3825627237e-8, -2.5261169794e-10, 6.4311819339e-13, -1.0063471519e-15, 9.9745338992e-19, -6.0863245607e-22, 2.0849229339e-25, -3.0682196151e-29];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else {
            // NIST ITS-90, диапазон -270..0°C (9 коэффициентов, степени 0..8)
            let c=[0, 2.6159105962e-2, 1.0957484228e-5, -9.3841111554e-8, -4.6412039759e-11, -2.6303357716e-12, -2.2653438003e-14, -7.6089300791e-17, -9.3419667835e-20];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        }
    } else if(type==='E'){
        // E (хромель-константан): диапазоны -270..0°C и 0..1000°C
        if(t>=0){
            // NIST ITS-90, диапазон 0..1000°C (11 коэффициентов, степени 0..10)
            let c=[0, 5.8665508710e-2, 4.5032275582e-5, 2.8908407212e-8, -3.3056896652e-10, 6.5024403270e-13, -1.9197495504e-16, -1.2536600497e-18, 2.1489217569e-21, -1.4388041782e-24, 3.5960899481e-28];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else {
            // NIST ITS-90, диапазон -270..0°C (14 коэффициентов)
            let c=[0, 5.8665508708e-2, 4.5410977124e-5, -7.7998048686e-7, -2.5800160843e-8, -5.9452583057e-10, -9.3214058667e-12, -1.0287605534e-13, -8.0370123621e-16, -4.3979497391e-18, -1.6414776355e-20, -3.9673619516e-23, -5.5827328721e-26, -3.4657842013e-29];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        }
    } else if(type==='R'){
        // R (платинородий-платина 13%): 3 диапазона
        if(t>=1064.18){
            // NIST ITS-90, диапазон 1064.18..1664.5°C
            let c=[2.9515792532e0, -2.5206125133e-3, 1.5956450187e-5, -7.6408594758e-9, 2.0530529102e-12, -2.9335966817e-16];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else if(t>=-50){
            // NIST ITS-90, диапазон -50..1064.18°C (10 коэффициентов)
            let c=[0, 5.2896172977e-3, 1.3916658978e-5, -2.3885569302e-8, 3.5691600106e-11, -4.6234766630e-14, 5.0077744103e-17, -3.7310588619e-20, 1.5771648237e-23, -2.8103862525e-27];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        }
    } else if(type==='S'){
        // S (платинородий-платина 10%): 3 диапазона
        if(t>=1064.18){
            // NIST ITS-90, диапазон 1064.18..1664.5°C (5 коэффициентов)
            let c=[1.3290044409e0, 3.3450931134e-3, 6.5480519282e-6, -1.6485625921e-9, 1.2998960517e-14];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else if(t>=-50){
            // NIST ITS-90, диапазон -50..1064.18°C (9 коэффициентов)
            // ВАЖНО: ранее здесь был баг — c1=5.4e-6 вместо 5.4e-3
            let c=[0, 5.4031330863e-3, 1.2593428974e-5, -2.3247796869e-8, 3.2202882304e-11, -3.3146519639e-14, 2.5574425179e-17, -1.2506887139e-20, 2.7144317615e-24];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        }
    } else if(type==='B'){
        // B (платинородий-платинородий 30%/6%): 2 диапазона, начинается с 0°C
        if(t>=630.615){
            // NIST ITS-90, диапазон 630.615..1820°C (9 коэффициентов)
            let c=[-3.8938168621e0, 2.8571747470e-2, -8.4885104785e-5, 1.5785280164e-7, -1.6835344864e-10, 1.1109794013e-13, -4.4515431033e-17, 9.8975640821e-21, -9.3791330289e-25];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        } else {
            // NIST ITS-90, диапазон 0..630.615°C (7 коэффициентов)
            let c=[0, -2.4650818346e-4, 5.9040421171e-6, -1.3257931636e-9, 1.5668291901e-12, -1.6944529240e-15, 6.2990347094e-19];
            let p=1; for(let i=0;i<c.length;i++){ mv+=c[i]*p; p*=t; }
        }
    }
    return mv;
}

export {
    calcTempSensor,
    updateTempSensorOptions,
    calcRtdResistance,
    calcCuResistance,
    calcTcVoltage
};
