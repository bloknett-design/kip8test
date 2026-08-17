/**
 * @module calculators/orifice
 * Orifice plate calculators — DP, flow, diameter, and quick estimation
 */
const showToast = window.showToast;
const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const roundNumber = window.roundNumber;
const validateField = window.validateField;
const clearFieldError = window.clearFieldError;
const hasValidationErrors = window.hasValidationErrors;


const opAlphaCoefficients = {
    orifice: { A: 0.5959, B: 0.0312, C: -0.1840, D: 0.0390 },
    nozzle: { A: 0.9965, B: 0.0105, C: -0.0420, D: 0.0085 },
    venturi: { A: 0.9840, B: 0.0050, C: -0.0150, D: 0.0030 }
};
const opThermalExpansion = {
    steel20: 11.9e-6,
    steel12x18h10t: 16.6e-6,
    steel15x5m: 11.5e-6,
    brass: 18.9e-6,
    bronze: 17.6e-6
};
function updateOpForm() {
    let type = document.getElementById('op_medium_type');
    if (type) {
        let gasParams = document.getElementById('op_gas_params');
        if (gasParams) gasParams.style.display = type.value === 'gas' ? 'block' : 'none';
    }
}
function updateOpDpForm() {
    let type = document.getElementById('op_dp_medium_type');
    if (type) {
        let gasParams = document.getElementById('op_dp_gas_params');
        if (gasParams) gasParams.style.display = type.value === 'gas' ? 'block' : 'none';
    }
}
function updateOpFlowForm() {
    let type = document.getElementById('op_flow_medium_type');
    if (type) {
        let gasParams = document.getElementById('op_flow_gas_params');
        if (gasParams) gasParams.style.display = type.value === 'gas' ? 'block' : 'none';
    }
}
function getOpAlpha(m, device) {
    let coeff = opAlphaCoefficients[device];
    return coeff.A + coeff.B * m + coeff.C * m * m + coeff.D * m * m * m;
}
function getOpEpsilon(m, dp_Pa, pressure_abs, kappa, medium) {
    if (medium !== 'gas') return 1.0;
    let tau = dp_Pa / pressure_abs;
    let eps = 1 - (0.41 + 0.35 * Math.pow(m, 1.5)) * tau / kappa;
    return eps < 0.9 ? 0.9 : eps;
}
function convertOpFlowToM3s(flow, unit, rho) {
    switch(unit) {
        case 'm3h': return flow / 3600;
        case 'm3s': return flow;
        case 'l_s': return flow / 1000;
        case 'kg_h': return flow / (3600 * rho);
        case 'kg_s': return flow / rho;
        case 't_h': return flow * 1000 / (3600 * rho);
        default: return flow / 3600;
    }
}
function convertOpDpToPa(dp, unit) {
    switch(unit) {
        case 'kPa': return dp * 1000;
        case 'Pa': return dp;
        case 'MPa': return dp * 1e6;
        case 'mmH2O': return dp * 9.80665;
        case 'mmHg': return dp * 133.322;
        case 'bar': return dp * 1e5;
        default: return dp * 1000;
    }
}

// ============================================================
// Быстрый расчёт диафрагмы (#9)
// ============================================================
// Упрощённая формула для прикидочной оценки перепада давления
// на стандартной диафрагме без полного расчёта по ГОСТ 26969-86.
//
// Формула: Δp = (ρ · Q²) / (2 · α² · β⁴ · A²)
//   где:
//     ρ — плотность среды, кг/м³
//     Q — объёмный расход, м³/с
//     α — коэффициент расхода (для стандартной диафрагмы ≈ 0.62)
//     β — относительный диаметр (d/D), безразмерный
//     A — площадь сечения трубы, м² = π·D²/4
//
// Возвращает перепад в Па. Для отображения конвертирует в кПа и мм вод.ст.
// ============================================================

// Дефолтные плотности для разных сред (при нормальных условиях)
const OQ_DEFAULT_RHO = {
    water: 1000,    // кг/м³
    air: 1.293,     // кг/м³ при 0°C, 101.325 кПа
    steam: 0.590,   // кг/м³ (насыщенный пар при 100°C)
    gas: 0.800      // кг/м³ (приблизительно для природного газа)
};

// Обновление плотности при смене типа среды
function updateOqMediumDefaults() {
    const medium = document.getElementById('oq_medium').value;
    const rhoInput = document.getElementById('oq_rho');
    if (rhoInput && OQ_DEFAULT_RHO[medium]) {
        rhoInput.value = OQ_DEFAULT_RHO[medium];
        clearFieldError(rhoInput);
    }
}

// Перевод расхода в м³/с (использует существующую convertOpFlowToM3s
// с учётом плотности для массовых единиц)
function oqFlowToM3s(flow, unit, rho) {
    // lmin → л/мин, нет в convertOpFlowToM3s — добавим обработку
    if (unit === 'lmin') {
        return flow / 60000;  // 1 л/мин = 0.001/60 м³/с
    }
    return convertOpFlowToM3s(flow, unit, rho);
}

// Главная функция быстрого расчёта
function calcOrificeQuick() {
    const flow = parseLocaleNumber(document.getElementById('oq_flow').value);
    const flowUnit = document.getElementById('oq_flow_unit').value;
    const dPipe_mm = parseLocaleNumber(document.getElementById('oq_d_pipe').value);
    const beta = parseLocaleNumber(document.getElementById('oq_beta').value);
    const rho = parseLocaleNumber(document.getElementById('oq_rho').value);

    // Валидация
    if (isNaN(flow) || flow <= 0) { showToast('Введите расход'); return; }
    if (isNaN(dPipe_mm) || dPipe_mm <= 0) { showToast('Введите диаметр трубы'); return; }
    if (isNaN(beta) || beta <= 0 || beta >= 1) { showToast('β должно быть в диапазоне 0–1'); return; }
    if (isNaN(rho) || rho <= 0) { showToast('Введите плотность среды'); return; }

    // Проверяем ошибки валидации в форме
    if (hasValidationErrors(document.getElementById('page-orifice-quick'))) {
        showToast('Исправьте ошибки в полях');
        return;
    }

    // Константы
    const ALPHA = 0.62;  // коэффициент расхода для стандартной диафрагмы
    const dPipe_m = dPipe_mm / 1000;  // мм → м
    const area = Math.PI * dPipe_m * dPipe_m / 4;  // площадь трубы, м²

    // Перевод расхода в м³/с
    const q_m3s = oqFlowToM3s(flow, flowUnit, rho);

    // Расчёт перепада давления по упрощённой формуле
    // Δp = (ρ · Q²) / (2 · α² · β⁴ · A²)
    const dp_pa = (rho * q_m3s * q_m3s) / (2 * ALPHA * ALPHA * Math.pow(beta, 4) * area * area);

    // Диаметр диафрагмы (для справки)
    const d_orifice_mm = dPipe_mm * beta;

    // Перевод в удобные единицы
    const dp_kpa = dp_pa / 1000;
    const dp_mmh2o = dp_pa / 9.80665;
    const dp_bar = dp_pa / 1e5;

    // Скорость в трубе (для справки)
    const v_pipe = q_m3s / area;  // м/с

    // Формирование результата
    const mediumNames = {
        water: 'Вода',
        air: 'Воздух',
        steam: 'Пар (насыщенный)',
        gas: 'Природный газ'
    };
    const medium = document.getElementById('oq_medium').value;

    let html = '<div class="converter-result-label-title">Результаты прикидочного расчёта</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Среда</span><span class="converter-result-value">' + mediumNames[medium] + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Расход Q</span><span class="converter-result-value">' + formatNumber(flow) + ' ' + flowUnit + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Объёмный расход (в СИ)</span><span class="converter-result-value">' + formatNumber(q_m3s) + ' м³/с</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Диаметр трубы D</span><span class="converter-result-value">' + formatNumber(dPipe_mm) + ' мм</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Относительный диаметр β</span><span class="converter-result-value">' + formatNumber(beta) + '</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Диаметр диафрагмы d = β·D</span><span class="converter-result-value">' + formatNumber(d_orifice_mm) + ' мм</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Скорость в трубе v</span><span class="converter-result-value">' + formatNumber(v_pipe) + ' м/с</span></div>';
    html += '<div class="converter-result-item" style="margin-top:10px; padding-top:10px; border-top:1px solid var(--card-border);"><span class="converter-result-label">Перепад Δp (Па)</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(dp_pa) + ' Па</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Перепад Δp (кПа)</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(dp_kpa) + ' кПа</span></div>';
    if (dp_mmh2o < 100000) {
        html += '<div class="converter-result-item"><span class="converter-result-label">Перепад Δp (мм вод.ст.)</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(dp_mmh2o) + ' мм вод.ст.</span></div>';
    }
    if (dp_bar > 0.001) {
        html += '<div class="converter-result-item"><span class="converter-result-label">Перепад Δp (бар)</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(dp_bar) + ' бар</span></div>';
    }

    // Информация о формуле
    html += '<div style="margin-top:14px; padding:14px 18px; background:rgba(13,17,23,0.5); border-radius:10px; font-size:13px; color:rgba(255,255,255,0.45); line-height:1.6;">';
    html += '<b style="color:rgba(255,255,255,0.7);">Формула:</b> Δp = (ρ · Q²) / (2 · α² · β⁴ · A²)<br>';
    html += '<b style="color:rgba(255,255,255,0.7);">Параметры:</b> α = 0.62 (коэффициент расхода), A = π·D²/4 = ' + formatNumber(area) + ' м²<br>';
    html += '<b style="color:rgba(255,255,255,0.7);">Подставлено:</b> Δp = (' + formatNumber(rho) + ' · ' + formatNumber(q_m3s) + '²) / (2 · 0.62² · ' + formatNumber(beta) + '⁴ · ' + formatNumber(area) + '²) = ' + formatNumber(dp_pa) + ' Па';
    html += '</div>';

    // Предупреждение о точности
    html += '<div style="margin-top:10px; padding:12px 14px; background:rgba(199,150,74,0.10); border:1px solid rgba(199,150,74,0.25); border-radius:10px; font-size:12px; color:#c7964a; line-height:1.5;">';
    html += '<b>⚠ Прикидочный расчёт.</b> Результат — оценка. Для точного расчёта по ГОСТ 26969-86 используйте раздел «Перепад давления». Упрощённая формула не учитывает: температурные поправки, шероховатость трубы, сжимаемость газов, поправки на вязкость.';
    html += '</div>';

    const results = document.getElementById('oq_results');
    results.innerHTML = html;
    results.style.display = 'block';
    setTimeout(() => results.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}
function getOpThermalD(d20_mm, material, temp) {
    let alpha = opThermalExpansion[material] || 11.9e-6;
    return d20_mm / 1000 * (1 + alpha * (temp - 20));
}

// Расчёт перепада давления Δp по Q и d₂₀
function calcOrificeDp() {
    let medium = document.getElementById('op_dp_medium_type').value;
    let d20_mm = parseLocaleNumber(document.getElementById('op_dp_d20').value);
    let pipeMat = document.getElementById('op_dp_pipe_material').value;
    let temp = parseLocaleNumber(document.getElementById('op_dp_temp').value);
    let flow = parseLocaleNumber(document.getElementById('op_dp_flow').value);
    let flowUnit = document.getElementById('op_dp_flow_unit').value;
    let d_plate_mm = parseLocaleNumber(document.getElementById('op_dp_d_plate').value);
    let rho = parseLocaleNumber(document.getElementById('op_dp_density').value);
    let nu_cSt = parseLocaleNumber(document.getElementById('op_dp_viscosity').value);
    let device = document.getElementById('op_dp_device_type').value;
    let plateMat = document.getElementById('op_dp_plate_material').value;
    let pressure = parseLocaleNumber(document.getElementById('op_dp_pressure').value) || 0;

    if (isNaN(d20_mm) || d20_mm <= 0) { showToast('Введите диаметр трубопровода'); return; }
    if (isNaN(flow) || flow <= 0) { showToast('Введите расход'); return; }
    if (isNaN(d_plate_mm) || d_plate_mm <= 0) { showToast('Введите диаметр диска'); return; }
    if (isNaN(rho) || rho <= 0) { showToast('Введите плотность'); return; }
    if (isNaN(nu_cSt) || nu_cSt <= 0) { showToast('Введите вязкость'); return; }
    if (d_plate_mm >= d20_mm) { showToast('Диаметр диска должен быть меньше диаметра трубы'); return; }

    let D = getOpThermalD(d20_mm, pipeMat, temp);
    let d = d_plate_mm / 1000 * (1 + (opThermalExpansion[plateMat] || 16.6e-6) * (temp - 20));
    let m = (d / D) * (d / D);
    let Q_m3s = convertOpFlowToM3s(flow, flowUnit, rho);
    let alpha = getOpAlpha(m, device);
    let kappa = medium === 'gas' ? (parseLocaleNumber(document.getElementById('op_dp_kappa').value) || 1.4) : 1.0;
    let Z = medium === 'gas' ? (parseLocaleNumber(document.getElementById('op_dp_z').value) || 1.0) : 1.0;
    let pressure_abs = pressure * 1e6 + 101325;

    let epsilon = getOpEpsilon(m, 25000, pressure_abs, kappa, medium);
    let dp_Pa;
    for (let iter = 0; iter < 20; iter++) {
        let denom = alpha * epsilon * (Math.PI * D * D / 4) * Math.sqrt(2 / rho) * m;
        dp_Pa = Math.pow(Q_m3s / denom, 2);
        let eps_new = getOpEpsilon(m, dp_Pa, pressure_abs, kappa, medium);
        if (Math.abs(eps_new - epsilon) < 0.0001) break;
        epsilon = eps_new;
    }

    let ReD = (4 * Q_m3s) / (Math.PI * D * nu_cSt * 1e-6);
    let dp_kPa = dp_Pa / 1000;
    let dp_mmH2O = dp_Pa / 9.80665;

    let warnings = [];
    if (m < 0.05) warnings.push('m < 0,05 — ниже рекомендуемого диапазона');
    if (m > 0.64) warnings.push('m > 0,64 — превышает рекомендуемый диапазон');
    if (ReD < 1e5) warnings.push('ReD < 10⁵ — возможна зависимость α от Re');
    if (dp_Pa > 0.25 * pressure_abs) warnings.push('Δp > 0,25·P — применение формулы ограничено');

    let deviceNames = { orifice: 'Диафрагма стандартная', nozzle: 'Сопло стандартное', venturi: 'Труба Вентури' };
    let html = '<div class="converter-result-label-title">Результаты расчёта Δp (РД 50-411-83)</div>';
    html += `<div class="converter-result-item"><span class="converter-result-label">Тип СУ</span><span class="converter-result-value">${deviceNames[device]}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Расход Q</span><span class="converter-result-value">${formatNumber(Q_m3s * 3600)} м³/ч</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Диаметр диска d₂₀</span><span class="converter-result-value">${formatNumber(d_plate_mm)} мм</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Относительное отверстие m</span><span class="converter-result-value">${formatNumber(m)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Коэффициент расхода α</span><span class="converter-result-value">${formatNumber(alpha)}</span></div>`;
    if (medium === 'gas') {
        html += `<div class="converter-result-item"><span class="converter-result-label">Коэффициент расширения ε</span><span class="converter-result-value">${formatNumber(epsilon)}</span></div>`;
    }
    html += `<div class="converter-result-item"><span class="converter-result-label">Число ReD</span><span class="converter-result-value">${formatNumber(ReD)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Перепад Δp</span><span class="converter-result-value" style="color:#4ac771; font-size:14px;">${formatNumber(dp_kPa)} кПа</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Перепад Δp</span><span class="converter-result-value">${formatNumber(dp_mmH2O)} мм вод.ст.</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Перепад Δp</span><span class="converter-result-value">${formatNumber(dp_Pa)} Па</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">Δp = ρ/2 · [Q/(α·ε·(πD²/4)·m)]²</span></div>`;

    if (warnings.length > 0) {
        html += `<div class="warning-banner" style="margin:10px 0 0;"><div class="warning-icon"><svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div><div class="warning-banner-content"><div class="warning-banner-title">Рекомендации</div><div class="warning-banner-desc">${warnings.join('<br>')}</div></div></div>`;
    }

    document.getElementById('opResultsDp').innerHTML = html;
    document.getElementById('opResultsDp').style.display = 'block';
    setTimeout(() => document.getElementById('opResultsDp').scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// Расчёт расхода Q по Δp и d₂₀
function calcOrificeFlow() {
    let medium = document.getElementById('op_flow_medium_type').value;
    let d20_mm = parseLocaleNumber(document.getElementById('op_flow_d20').value);
    let pipeMat = document.getElementById('op_flow_pipe_material').value;
    let temp = parseLocaleNumber(document.getElementById('op_flow_temp').value);
    let dp = parseLocaleNumber(document.getElementById('op_flow_dp').value);
    let dpUnit = document.getElementById('op_flow_dp_unit').value;
    let d_plate_mm = parseLocaleNumber(document.getElementById('op_flow_d_plate').value);
    let rho = parseLocaleNumber(document.getElementById('op_flow_density').value);
    let nu_cSt = parseLocaleNumber(document.getElementById('op_flow_viscosity').value);
    let device = document.getElementById('op_flow_device_type').value;
    let plateMat = document.getElementById('op_flow_plate_material').value;
    let pressure = parseLocaleNumber(document.getElementById('op_flow_pressure').value) || 0;

    if (isNaN(d20_mm) || d20_mm <= 0) { showToast('Введите диаметр трубопровода'); return; }
    if (isNaN(dp) || dp <= 0) { showToast('Введите перепад давления'); return; }
    if (isNaN(d_plate_mm) || d_plate_mm <= 0) { showToast('Введите диаметр диска'); return; }
    if (isNaN(rho) || rho <= 0) { showToast('Введите плотность'); return; }
    if (isNaN(nu_cSt) || nu_cSt <= 0) { showToast('Введите вязкость'); return; }
    if (d_plate_mm >= d20_mm) { showToast('Диаметр диска должен быть меньше диаметра трубы'); return; }

    let D = getOpThermalD(d20_mm, pipeMat, temp);
    let d = d_plate_mm / 1000 * (1 + (opThermalExpansion[plateMat] || 16.6e-6) * (temp - 20));
    let m = (d / D) * (d / D);
    let dp_Pa = convertOpDpToPa(dp, dpUnit);
    let alpha = getOpAlpha(m, device);
    let kappa = medium === 'gas' ? (parseLocaleNumber(document.getElementById('op_flow_kappa').value) || 1.4) : 1.0;
    let Z = medium === 'gas' ? (parseLocaleNumber(document.getElementById('op_flow_z').value) || 1.0) : 1.0;
    let pressure_abs = pressure * 1e6 + 101325;
    let epsilon = getOpEpsilon(m, dp_Pa, pressure_abs, kappa, medium);

    let Q_m3s = alpha * epsilon * (Math.PI * D * D / 4) * Math.sqrt(2 * dp_Pa / rho) * m;
    let ReD = (4 * Q_m3s) / (Math.PI * D * nu_cSt * 1e-6);

    let warnings = [];
    if (m < 0.05) warnings.push('m < 0,05 — ниже рекомендуемого диапазона');
    if (m > 0.64) warnings.push('m > 0,64 — превышает рекомендуемый диапазон');
    if (ReD < 1e5) warnings.push('ReD < 10⁵ — возможна зависимость α от Re');
    if (dp_Pa > 0.25 * pressure_abs) warnings.push('Δp > 0,25·P — применение формулы ограничено');

    let deviceNames = { orifice: 'Диафрагма стандартная', nozzle: 'Сопло стандартное', venturi: 'Труба Вентури' };
    let html = '<div class="converter-result-label-title">Результаты расчёта Q (РД 50-411-83)</div>';
    html += `<div class="converter-result-item"><span class="converter-result-label">Тип СУ</span><span class="converter-result-value">${deviceNames[device]}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Перепад Δp</span><span class="converter-result-value">${formatNumber(dp_Pa / 1000)} кПа</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Диаметр диска d₂₀</span><span class="converter-result-value">${formatNumber(d_plate_mm)} мм</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Относительное отверстие m</span><span class="converter-result-value">${formatNumber(m)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Коэффициент расхода α</span><span class="converter-result-value">${formatNumber(alpha)}</span></div>`;
    if (medium === 'gas') {
        html += `<div class="converter-result-item"><span class="converter-result-label">Коэффициент расширения ε</span><span class="converter-result-value">${formatNumber(epsilon)}</span></div>`;
    }
    html += `<div class="converter-result-item"><span class="converter-result-label">Число ReD</span><span class="converter-result-value">${formatNumber(ReD)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Расход Q</span><span class="converter-result-value" style="color:#4ac771; font-size:14px;">${formatNumber(Q_m3s * 3600)} м³/ч</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Расход Q</span><span class="converter-result-value">${formatNumber(Q_m3s)} м³/с</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Расход Q</span><span class="converter-result-value">${formatNumber(Q_m3s * 1000)} л/с</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Массовый расход</span><span class="converter-result-value">${formatNumber(Q_m3s * rho * 3600)} кг/ч</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">Q = α·ε·(πD²/4)·√(2Δp/ρ)·m</span></div>`;

    if (warnings.length > 0) {
        html += `<div class="warning-banner" style="margin:10px 0 0;"><div class="warning-icon"><svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div><div class="warning-banner-content"><div class="warning-banner-title">Рекомендации</div><div class="warning-banner-desc">${warnings.join('<br>')}</div></div></div>`;
    }

    document.getElementById('opResultsFlow').innerHTML = html;
    document.getElementById('opResultsFlow').style.display = 'block';
    setTimeout(() => document.getElementById('opResultsFlow').scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// Расчёт диаметра диска d₂₀ по Q и Δp
function calcOrificeDiameter() {
    let medium = document.getElementById('op_medium_type').value;
    let d20 = parseLocaleNumber(document.getElementById('op_d20').value);
    let dUnit = document.getElementById('op_d_unit').value;
    let pipeMat = document.getElementById('op_pipe_material').value;
    let temp = parseLocaleNumber(document.getElementById('op_temp').value);
    let flow = parseLocaleNumber(document.getElementById('op_flow').value);
    let flowUnit = document.getElementById('op_flow_unit').value;
    let flowMin = parseLocaleNumber(document.getElementById('op_flow_min').value);
    let pressure = parseLocaleNumber(document.getElementById('op_pressure').value);
    let rho = parseLocaleNumber(document.getElementById('op_density').value);
    let nu_cSt = parseLocaleNumber(document.getElementById('op_viscosity').value);
    let dp = parseLocaleNumber(document.getElementById('op_dp').value);
    let dpUnit = document.getElementById('op_dp_unit').value;
    let device = document.getElementById('op_device_type').value;
    let plateMat = document.getElementById('op_plate_material').value;

    if (isNaN(d20) || d20 <= 0) { showToast('Введите диаметр трубопровода'); return; }
    if (isNaN(flow) || flow <= 0) { showToast('Введите расход'); return; }
    if (isNaN(rho) || rho <= 0) { showToast('Введите плотность'); return; }
    if (isNaN(dp) || dp <= 0) { showToast('Введите перепад давления'); return; }
    if (isNaN(nu_cSt) || nu_cSt <= 0) { showToast('Введите вязкость'); return; }

    let D20_m = dUnit === 'mm' ? d20 / 1000 : d20;
    let Q_m3s = convertOpFlowToM3s(flow, flowUnit, rho);
    let dp_Pa = convertOpDpToPa(dp, dpUnit);
    let alpha_pipe = opThermalExpansion[pipeMat] || 11.9e-6;
    let alpha_plate = opThermalExpansion[plateMat] || 16.6e-6;
    let kt_pipe = 1 + alpha_pipe * (temp - 20);
    let kt_plate = 1 + alpha_plate * (temp - 20);
    let D = D20_m * kt_pipe;
    let coeff = opAlphaCoefficients[device];
    let kappa = medium === 'gas' ? (parseLocaleNumber(document.getElementById('op_kappa').value) || 1.4) : 1.0;
    let Z = medium === 'gas' ? (parseLocaleNumber(document.getElementById('op_z').value) || 1.0) : 1.0;
    let pressure_abs = pressure * 1e6 + 101325;

    let m = 0.25;
    let alpha, epsilon = 1.0;
    let Q_calc;
    let iter;
    for (iter = 0; iter < 50; iter++) {
        alpha = coeff.A + coeff.B * m + coeff.C * m * m + coeff.D * m * m * m;
        if (medium === 'gas') {
            let tau = dp_Pa / pressure_abs;
            epsilon = 1 - (0.41 + 0.35 * Math.pow(m, 1.5)) * tau / kappa;
            if (epsilon < 0.9) epsilon = 0.9;
        }
        Q_calc = alpha * epsilon * (Math.PI * D * D / 4) * Math.sqrt(2 * dp_Pa / rho) * m;
        let err = (Q_calc - Q_m3s) / Q_m3s;
        if (Math.abs(err) < 0.0001) break;
        m = m * (1 - err * 0.5);
        if (m < 0.02) m = 0.02;
        if (m > 0.70) m = 0.70;
    }

    let d = D * Math.sqrt(m);
    let d20_calc = d / kt_plate;
    let d_mm = d20_calc * 1000;
    let ReD = (4 * Q_m3s) / (Math.PI * D * nu_cSt * 1e-6);
    let ReD_min = ReD * (flowMin / flow);

    let warnings = [];
    if (m < 0.05) warnings.push('m < 0,05 — ниже рекомендуемого диапазона');
    if (m > 0.64) warnings.push('m > 0,64 — превышает рекомендуемый диапазон');
    if (ReD < 1e5) warnings.push('ReD < 10⁵ — возможна зависимость α от Re');
    if (d20_calc / D20_m > 0.8) warnings.push('d₂₀/D₂₀ > 0,8 — проверьте условия установки');
    if (flowMin / flow < 0.3) warnings.push('Qₘᵢₙ/Q < 0,3 — возможна недостаточная точность на малых расходах');

    let deviceNames = { orifice: 'Диафрагма стандартная', nozzle: 'Сопло стандартное', venturi: 'Труба Вентури' };
    let html = '<div class="converter-result-label-title">Результаты расчёта d₂₀ (РД 50-411-83)</div>';
    html += `<div class="converter-result-item"><span class="converter-result-label">Тип СУ</span><span class="converter-result-value">${deviceNames[device]}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Диаметр трубы D₂₀</span><span class="converter-result-value">${formatNumber(d20)} ${dUnit}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Рабочий диаметр D</span><span class="converter-result-value">${formatNumber(D * 1000)} мм</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Расход Q</span><span class="converter-result-value">${formatNumber(Q_m3s * 3600)} м³/ч</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Перепад Δp</span><span class="converter-result-value">${formatNumber(dp_Pa / 1000)} кПа</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Относительное отверстие m</span><span class="converter-result-value">${formatNumber(m)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Коэффициент расхода α</span><span class="converter-result-value">${formatNumber(alpha)}</span></div>`;
    if (medium === 'gas') {
        html += `<div class="converter-result-item"><span class="converter-result-label">Коэффициент расширения ε</span><span class="converter-result-value">${formatNumber(epsilon)}</span></div>`;
    }
    html += `<div class="converter-result-item"><span class="converter-result-label">Число ReD (ном.)</span><span class="converter-result-value">${formatNumber(ReD)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Число ReD (мин.)</span><span class="converter-result-value">${formatNumber(ReD_min)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Диаметр отверстия d₂₀</span><span class="converter-result-value" style="color:#4ac771; font-size:14px;">${formatNumber(d_mm)} мм</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Отношение d₂₀/D₂₀</span><span class="converter-result-value">${formatNumber(d20_calc / D20_m)}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Итераций</span><span class="converter-result-value">${iter}</span></div>`;
    html += `<div class="converter-result-item"><span class="converter-result-label">Формула</span><span class="converter-result-value">Q = α·ε·(πD²/4)·√(2Δp/ρ)·m</span></div>`;

    if (warnings.length > 0) {
        html += `<div class="warning-banner" style="margin:10px 0 0;"><div class="warning-icon"><svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div><div class="warning-banner-content"><div class="warning-banner-title">Рекомендации</div><div class="warning-banner-desc">${warnings.join('<br>')}</div></div></div>`;
    }

    document.getElementById('opResultsDiameter').innerHTML = html;
    document.getElementById('opResultsDiameter').style.display = 'block';
    setTimeout(() => document.getElementById('opResultsDiameter').scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}


export {
    calcOrificeDp,
    calcOrificeFlow,
    calcOrificeDiameter,
    calcOrificeQuick,
    opAlphaCoefficients,
    opThermalExpansion,
    OQ_DEFAULT_RHO,
    getOpAlpha,
    getOpEpsilon,
    convertOpFlowToM3s,
    convertOpDpToPa,
    oqFlowToM3s,
    updateOqMediumDefaults,
    getOpThermalD,
    updateOpForm,
    updateOpDpForm,
    updateOpFlowForm
};
