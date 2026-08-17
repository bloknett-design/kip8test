/**
 * @module calculators/circuit-breaker
 * Circuit breaker calculator adapted for KIP and ASU TP (low power, 12-36 V)
 */
const showToast = window.showToast;
const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const validateField = window.validateField;

// Автоматический выключатель — адаптирован для КИП, АСУ ТП, малой мощности, 12-36 В
const cbCableDataKip = {
    cu: {
        0.5: { Ik: 11, Imax: 6, desc: 'сигнальные цепи, датчики' },
        0.75: { Ik: 15, Imax: 10, desc: '4-20 мА, термопары, ТС' },
        1.0: { Ik: 17, Imax: 10, desc: 'питание 24 В DC, клапана' },
        1.5: { Ik: 23, Imax: 16, desc: 'группа приборов 220 В' },
        2.5: { Ik: 30, Imax: 25, desc: 'силовая линия, щит' },
        4: { Ik: 41, Imax: 32, desc: 'щит питания АСУ ТП' },
        6: { Ik: 50, Imax: 40, desc: 'главный ввод' }
    },
    al: {
        0.5: { Ik: 8, Imax: 4, desc: 'не рекомендуется для КИП' },
        0.75: { Ik: 11, Imax: 6, desc: 'не рекомендуется для КИП' },
        1.0: { Ik: 13, Imax: 10, desc: 'временные линии' },
        1.5: { Ik: 17, Imax: 10, desc: 'освещение' },
        2.5: { Ik: 23, Imax: 16, desc: 'силовая линия' },
        4: { Ik: 30, Imax: 25, desc: 'щит' },
        6: { Ik: 38, Imax: 32, desc: 'главный ввод' }
    }
};
const cbStandardSeriesKip = [0.5, 1, 2, 3, 4, 6, 8, 10, 13, 16, 20, 25, 32, 40, 50, 63];
const cbConsumerProfiles = {
    kip_resistive: { cosphi: 1.0, inrush: 1.0, desc: 'активная нагрузка' },
    kip_inductive: { cosphi: 0.7, inrush: 3.0, desc: 'клапана, реле, соленоиды' },
    asutp_controller: { cosphi: 0.95, inrush: 1.2, desc: 'контроллер + модули' },
    asutp_actuator: { cosphi: 0.75, inrush: 5.0, desc: 'исполнительные механизмы' },
    mixed: { cosphi: 0.85, inrush: 2.0, desc: 'смешанная нагрузка' },
    custom: { cosphi: null, inrush: null, desc: 'пользовательские параметры' }
};
const cbSupplyProfiles = {
    ac220: { U: 220, type: 'AC', desc: '~220 В' },
    dc24: { U: 24, type: 'DC', desc: '=24 В' },
    dc12: { U: 12, type: 'DC', desc: '=12 В' },
    dc36: { U: 36, type: 'DC', desc: '=36 В' },
    ac24: { U: 24, type: 'AC', desc: '~24 В' },
    ac36: { U: 36, type: 'AC', desc: '~36 В' },
    custom: { U: null, type: null, desc: 'своё' }
};
function getCbCableDataKip(lineType, customSection, customMaterial) {
    let preset = {
        signal_0_75: { mat: 'cu', sec: 0.75 },
        power_1_0: { mat: 'cu', sec: 1.0 },
        power_1_5: { mat: 'cu', sec: 1.5 },
        power_2_5: { mat: 'cu', sec: 2.5 }
    };
    let mat = lineType === 'custom' ? customMaterial : preset[lineType].mat;
    let sec = lineType === 'custom' ? parseLocaleNumber(customSection) : preset[lineType].sec;
    return { material: mat, section: sec, data: cbCableDataKip[mat][sec] };
}
function nearestCbStandardKip(val) {
    for (let i = 0; i < cbStandardSeriesKip.length; i++) {
        if (cbStandardSeriesKip[i] >= val) return cbStandardSeriesKip[i];
    }
    return cbStandardSeriesKip[cbStandardSeriesKip.length - 1];
}
function updateCbForm() {
    let loadType = document.getElementById('cb_load_type').value;
    document.getElementById('cb_power_block').style.display = loadType === 'power' ? 'block' : 'none';
    document.getElementById('cb_current_block').style.display = loadType === 'current' ? 'block' : 'none';
    let supply = document.getElementById('cb_supply_type').value;
    document.getElementById('cb_custom_voltage_block').style.display = supply === 'custom' ? 'block' : 'none';
}
function updateCbCosPhi() {
    let consumer = document.getElementById('cb_consumer_type').value;
    document.getElementById('cb_custom_cosphi_block').style.display = consumer === 'custom' ? 'block' : 'none';
}
function updateCbCableTable() {
    let lineType = document.getElementById('cb_line_type').value;
    document.getElementById('cb_custom_cable').style.display = lineType === 'custom' ? 'block' : 'none';
}
function calcCircuitBreaker() {
    let supplyType = document.getElementById('cb_supply_type').value;
    let loadType = document.getElementById('cb_load_type').value;
    let consumerType = document.getElementById('cb_consumer_type').value;
    let lineType = document.getElementById('cb_line_type').value;
    let curve = document.getElementById('cb_curve').value;
    let deviceCount = parseInt(document.getElementById('cb_device_count').value) || 1;
    let customSection = document.getElementById('cb_cable_section') ? document.getElementById('cb_cable_section').value : '0.75';
    let customMaterial = document.getElementById('cb_cable_material') ? document.getElementById('cb_cable_material').value : 'cu';

    // Supply profile
    let supply = cbSupplyProfiles[supplyType];
    let U;
    if (supplyType === 'custom') {
        U = parseLocaleNumber(document.getElementById('cb_custom_voltage').value);
        if (isNaN(U) || U <= 0) { showToast('Введите напряжение питания'); return; }
    } else {
        U = supply.U;
    }

    // Consumer profile
    let consumer = cbConsumerProfiles[consumerType];
    let cosphi, inrush;
    if (consumerType === 'custom') {
        cosphi = parseLocaleNumber(document.getElementById('cb_custom_cosphi').value);
        inrush = parseLocaleNumber(document.getElementById('cb_inrush_factor').value);
        if (isNaN(cosphi) || cosphi <= 0 || cosphi > 1) { showToast('cos φ должен быть 0,1…1,0'); return; }
        if (isNaN(inrush) || inrush < 1) { showToast('Кпуск ≥ 1,0'); return; }
    } else {
        cosphi = consumer.cosphi;
        inrush = consumer.inrush;
    }

    // Calculate current
    let Icalc;
    if (loadType === 'power') {
        let P = parseLocaleNumber(document.getElementById('cb_power').value);
        let unitMult = parseLocaleNumber(document.getElementById('cb_power_unit').value);
        if (isNaN(P) || P <= 0) { showToast('Введите мощность'); return; }
        P = P * unitMult * deviceCount;
        Icalc = P / (U * cosphi);
    } else {
        Icalc = parseLocaleNumber(document.getElementById('cb_current').value);
        if (isNaN(Icalc) || Icalc <= 0) { showToast('Введите ток'); return; }
        Icalc = Icalc * deviceCount;
    }

    // Cable data
    let cable = getCbCableDataKip(lineType, customSection, customMaterial);
    let In_min = Icalc * 1.25; // Запас 25% для КИП
    let Ina = nearestCbStandardKip(In_min);
    let Ina_inrush = nearestCbStandardKip(Icalc * inrush / (curve === 'B' ? 3 : curve === 'C' ? 5 : curve === 'D' ? 10 : 2));
    if (Ina_inrush > Ina) Ina = Ina_inrush;

    let warning = '';
    if (Ina > cable.data.Imax) {
        warning = `Выбранный автомат ${formatNumber(Ina)} А превышает допустимый ток для кабеля ${formatNumber(cable.section)} мм² (${formatNumber(cable.data.Imax)} А). Увеличьте сечение кабеля.`;
    }
    if (Ina < 0.5) {
        warning += (warning ? '<br>' : '') + `Расчётный ток ${formatNumber(Icalc)} А очень мал. Рекомендуется применять предохранители или защиту в составе БП.`;
    }

    let Pmax = Ina * U * cosphi;
    let I_inrush = Icalc * inrush;

    let html = '<div class="converter-result-label-title">Результаты расчёта (КИП и А / АСУ ТП)</div>';
    html += `<div class="converter-result-item"><span class="converter-result-label">Напряжение питания</span><span class="converter-result-value">${supplyType === 'custom' ? (document.getElementById('cb_custom_voltage_type').value === 'dc' ? '=' : '~') + formatNumber(U) + ' В' : supply.desc}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Тип нагрузки</span><span class="converter-result-value">${consumer.desc}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">cos φ / Кпуск</span><span class="converter-result-value">${formatNumber(cosphi)} / ${formatNumber(inrush)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Расчётный ток Iр</span><span class="converter-result-value">${formatNumber(Icalc)} А</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Пусковой ток Iпуск</span><span class="converter-result-value">${formatNumber(I_inrush)} А</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Кабель</span><span class="converter-result-value">${cable.material === 'cu' ? 'медь' : 'алюминий'} ${formatNumber(cable.section)} мм² · ${formatNumber(cable.data.Imax)} А · ${cable.data.desc}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Макс. автомат для кабеля</span><span class="converter-result-value">${formatNumber(cable.data.Imax)} А</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Рекомендуемый автомат</span><span class="converter-result-value" style="color:#4ac771; font-size:14px;">${curve}${formatNumber(Ina)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Макс. мощность</span><span class="converter-result-value">${formatNumber(Pmax)} Вт (${formatNumber(Pmax/1000)} кВт)</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Количество приборов</span><span class="converter-result-value">${deviceCount} шт.</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">I = P/(U·cos φ) · Кзапаса 1,25</span></div>`;

    if (warning) {
        html += `<div class="warning-banner" style="margin:10px 0 0;"><div class="warning-icon"><svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div><div class="warning-banner-content"><div class="warning-banner-title">Рекомендации</div><div class="warning-banner-desc">${warning}</div></div></div>`;
    }

    document.getElementById('cbResults').innerHTML = html;
    document.getElementById('cbResults').style.display = 'block';
    setTimeout(() => document.getElementById('cbResults').scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// ===== СУЖАЮЩЕЕ УСТРОЙСТВО (ДИАФРАГМА) — вспомогательные функции =====

export {
    calcCircuitBreaker,
    cbCableDataKip,
    cbStandardSeriesKip,
    cbConsumerProfiles,
    cbSupplyProfiles,
    getCbCableDataKip,
    nearestCbStandardKip,
    updateCbForm,
    updateCbCosPhi,
    updateCbCableTable
};
