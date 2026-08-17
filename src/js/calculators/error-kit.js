/**
 * @module calculators/error-kit
 * Error kit calculator for multi-instrument error calculation
 */
const showToast = window.showToast;
const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const roundNumber = window.roundNumber;
const validateField = window.validateField;

let kitDeviceCount = 0;

function addKitDevice(form, cls, xmin, xmax) {
    let container = document.getElementById('kit_device_list');
    let existing = container.querySelectorAll('[id^="kit_dev_"]');
    if (existing.length >= 5) {
        document.getElementById('kit_add_limit_msg').style.display = 'block';
        return;
    }
    kitDeviceCount++;
    let idx = kitDeviceCount;
    let visualNum = existing.length + 1;
    let p = 'kd_' + idx + '_';
    form = form || 'number';
    cls = cls || '0.5';
    xmin = xmin !== undefined ? xmin : '0';
    xmax = xmax !== undefined ? xmax : '';
    let div = document.createElement('div');
    div.className = 'scale-form kit-dev-form';
    div.id = 'kit_dev_' + idx;
    div.style.marginBottom = '6px';
    div.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;"><div style="font-size:13px;font-weight:600;color:rgba(74,143,199,0.9);margin:0;">Прибор ' + visualNum + '</div><button type="button" onclick="removeKitDevice(' + idx + ')" style="background:rgba(199,74,74,0.15);border:1px solid rgba(199,74,74,0.3);color:#c74a4a;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;font-family:Inter,sans-serif;min-height:28px;">Удалить</button></div>'
        + '<div style="display:flex;gap:6px;align-items:flex-end;"><div style="flex:1.2;"><div class="scale-form-label">Выбор погрешности</div><select id="' + p + 'class_form" class="scale-field" style="margin-bottom:0;" onchange="toggleKitDevFields(' + idx + ')" autocomplete="off">'
        + '<option value="absolute"' + (form === 'absolute' ? ' selected' : '') + ' data-hint="±Δ = const">Абсолютная</option>'
        + '<option value="circle"' + (form === 'circle' ? ' selected' : '') + ' data-hint="δ = Δ/|X|">Относительная</option>'
        + '<option value="number"' + (form === 'number' ? ' selected' : '') + ' data-hint="γ = Δ/Xн">Приведённая</option></select></div>'
        + '<div id="' + p + 'cls_simple_wrap" style="flex:0.8;' + (form !== 'number' ? 'display:none;' : '') + '"><div class="scale-form-label"><span class="greek-gamma">γ</span> (%)</div><select id="' + p + 'class_val" class="scale-field" style="margin-bottom:0;" onchange="toggleKitDevCustom(' + idx + ',\'number\')" autocomplete="off">'
        + '<option value="0.05"' + (cls === '0.05' ? ' selected' : '') + '>0,05</option>'
        + '<option value="0.06"' + (cls === '0.06' ? ' selected' : '') + '>0,06</option>'
        + '<option value="0.1"' + (cls === '0.1' ? ' selected' : '') + '>0,1</option>'
        + '<option value="0.15"' + (cls === '0.15' ? ' selected' : '') + '>0,15</option>'
        + '<option value="0.2"' + (cls === '0.2' ? ' selected' : '') + '>0,2</option>'
        + '<option value="0.25"' + (cls === '0.25' ? ' selected' : '') + '>0,25</option>'
        + '<option value="0.5"' + (cls === '0.5' ? ' selected' : '') + '>0,5</option>'
        + '<option value="1.0"' + (cls === '1.0' ? ' selected' : '') + '>1,0</option>'
        + '<option value="1.5"' + (cls === '1.5' ? ' selected' : '') + '>1,5</option>'
        + '<option value="2.5"' + (cls === '2.5' ? ' selected' : '') + '>2,5</option>'
        + '<option value="4.0"' + (cls === '4.0' ? ' selected' : '') + '>4,0</option>'
        + '<option value="custom" data-hint="Вручную">Своё</option></select>'
        + '<input type="text" inputmode="numeric" id="' + p + 'class_val_custom" class="scale-field kit-dev-custom-input" style="margin-bottom:0;display:none;" placeholder="γ %" autocomplete="off" enterkeyhint="next"></div>'
        + '<div id="' + p + 'cls_circle_wrap" style="flex:0.8;' + (form !== 'circle' ? 'display:none;' : '') + '"><div class="scale-form-label"><span class="greek-delta">δ</span> (%)</div><select id="' + p + 'class_val_c" class="scale-field" style="margin-bottom:0;" onchange="toggleKitDevCustom(' + idx + ',\'circle\')" autocomplete="off">'
        + '<option value="0.1"' + (cls === '0.1' ? ' selected' : '') + '>0,1</option>'
        + '<option value="0.15"' + (cls === '0.15' ? ' selected' : '') + '>0,15</option>'
        + '<option value="0.2"' + (cls === '0.2' ? ' selected' : '') + '>0,2</option>'
        + '<option value="0.25"' + (cls === '0.25' ? ' selected' : '') + '>0,25</option>'
        + '<option value="0.5"' + (cls === '0.5' ? ' selected' : '') + '>0,5</option>'
        + '<option value="1.0"' + (cls === '1.0' ? ' selected' : '') + '>1,0</option>'
        + '<option value="1.5"' + (cls === '1.5' ? ' selected' : '') + '>1,5</option>'
        + '<option value="2.0"' + (cls === '2.0' ? ' selected' : '') + '>2,0</option>'
        + '<option value="2.5"' + (cls === '2.5' ? ' selected' : '') + '>2,5</option>'
        + '<option value="4.0"' + (cls === '4.0' ? ' selected' : '') + '>4,0</option>'
        + '<option value="custom" data-hint="Вручную">Своё</option></select>'
        + '<input type="text" inputmode="numeric" id="' + p + 'class_val_c_custom" class="scale-field kit-dev-custom-input" style="margin-bottom:0;display:none;" placeholder="δ %" autocomplete="off" enterkeyhint="next"></div>'
        + '<div id="' + p + 'cls_absolute_wrap" style="flex:0.8;' + (form !== 'absolute' ? 'display:none;' : '') + '"><div class="scale-form-label" style="text-transform:none;">±Δ (ед.изм.)</div><input type="text" inputmode="numeric" id="' + p + 'abs_val" class="scale-field" style="margin-bottom:0;" value="" placeholder="±Δ" autocomplete="off" enterkeyhint="next"></div>'
        + '</div>'
        + '<div id="' + p + 'group_simple"' + (form !== 'number' ? ' style="display:none;"' : '') + '>'
        + '<div class="scale-form-label">Диапазон измерения</div><div style="display:flex;gap:8px;align-items:stretch;"><input type="text" inputmode="numeric" id="' + p + 'xmin" class="scale-field" style="flex:1;" placeholder="НПИ" value="' + xmin + '" autocomplete="off" enterkeyhint="next"><input type="text" inputmode="numeric" id="' + p + 'xmax" class="scale-field" style="flex:1;" placeholder="ВПИ" value="' + xmax + '" autocomplete="off" enterkeyhint="next"></div></div>'
        + '<div id="' + p + 'group_circle"' + (form !== 'circle' ? ' style="display:none;"' : '') + '>'
        + '<div class="scale-form-label">Текущее значение X</div><input type="text" inputmode="numeric" id="' + p + 'x_current_c" class="scale-field" placeholder="обязательно" autocomplete="off" enterkeyhint="next"></div>'
        + '<div id="' + p + 'group_absolute"' + (form !== 'absolute' ? ' style="display:none;"' : '') + '></div>'
        + '<div id="' + p + 'abs_result" style="display:none;margin-top:8px;padding:8px 12px;background:rgba(74,143,199,0.08);border:1px solid rgba(74,143,199,0.2);border-radius:8px;font-size:13px;color:#4a8fc7;"></div>';
    document.getElementById('kit_device_list').appendChild(div);
    renumberKitDevices();
    updateKitLimitMsg();
}

function removeKitDevice(idx) {
    let el = document.getElementById('kit_dev_' + idx);
    if (el) el.remove();
    renumberKitDevices();
    updateKitLimitMsg();
}

function renumberKitDevices() {
    let container = document.getElementById('kit_device_list');
    let devs = container.querySelectorAll('[id^="kit_dev_"]');
    devs.forEach((el, i) => {
        let row = el.firstElementChild;
        if (row) { let label = row.firstElementChild; if (label) label.textContent = 'Прибор ' + (i + 1); }
    });
}

function updateKitLimitMsg() {
    let container = document.getElementById('kit_device_list');
    let existing = container.querySelectorAll('[id^="kit_dev_"]');
    let msg = document.getElementById('kit_add_limit_msg');
    if (msg) msg.style.display = existing.length >= 5 ? 'block' : 'none';
}

function toggleKitDevFields(idx) {
    let p = 'kd_' + idx + '_';
    let form = document.getElementById(p + 'class_form').value;
    let groups = ['group_simple', 'group_circle', 'group_absolute'];
    groups.forEach(g => {
        let el = document.getElementById(p + g);
        if (el) el.style.display = 'none';
    });
    let clsWraps = ['cls_simple_wrap', 'cls_circle_wrap', 'cls_absolute_wrap'];
    clsWraps.forEach(w => {
        let el = document.getElementById(p + w);
        if (el) el.style.display = 'none';
    });
    let showMap = {'number': 'group_simple', 'circle': 'group_circle', 'absolute': 'group_absolute'};
    let clsMap = {'number': 'cls_simple_wrap', 'circle': 'cls_circle_wrap', 'absolute': 'cls_absolute_wrap'};
    let showEl = document.getElementById(p + showMap[form]);
    if (showEl) showEl.style.display = 'block';
    let clsEl = document.getElementById(p + clsMap[form]);
    if (clsEl) clsEl.style.display = 'block';
}

function toggleKitDevCustom(idx, type) {
    let p = 'kd_' + idx + '_';
    if (type === 'number') {
        let sel = document.getElementById(p + 'class_val');
        let inp = document.getElementById(p + 'class_val_custom');
        if (sel && inp) inp.style.display = sel.value === 'custom' ? 'block' : 'none';
    } else if (type === 'circle') {
        let sel = document.getElementById(p + 'class_val_c');
        let inp = document.getElementById(p + 'class_val_c_custom');
        if (sel && inp) inp.style.display = sel.value === 'custom' ? 'block' : 'none';
    }
}

function calcKitDeviceError(idx) {
    let p = 'kd_' + idx + '_';
    let devEl = document.getElementById('kit_dev_' + idx);
    if (!devEl) return null;
    let form = document.getElementById(p + 'class_form').value;
    let absErr, xNorm;
    try {
        if (form === 'number') {
            let clsVal = document.getElementById(p + 'class_val').value;
            let cls = clsVal === 'custom' ? parseLocaleNumber(document.getElementById(p + 'class_val_custom').value) : parseFloat(clsVal);
            let xmin = parseLocaleNumber(document.getElementById(p + 'xmin').value);
            let xmax = parseLocaleNumber(document.getElementById(p + 'xmax').value);
            if (isNaN(cls) || cls <= 0 || isNaN(xmin) || isNaN(xmax) || xmin >= xmax) return null;
            xNorm = (xmin === 0) ? Math.abs(xmax) : (xmax - xmin);
            absErr = (cls / 100) * xNorm;
        } else if (form === 'circle') {
            let clsVal = document.getElementById(p + 'class_val_c').value;
            let cls = clsVal === 'custom' ? parseLocaleNumber(document.getElementById(p + 'class_val_c_custom').value) : parseFloat(clsVal);
            let xcur = parseLocaleNumber(document.getElementById(p + 'x_current_c').value);
            if (isNaN(cls) || cls <= 0 || isNaN(xcur) || xcur === 0) return null;
            absErr = (cls / 100) * Math.abs(xcur);
        } else if (form === 'absolute') {
            let val = parseLocaleNumber(document.getElementById(p + 'abs_val').value);
            if (isNaN(val) || val <= 0) return null;
            absErr = val;
        }
    } catch(e) { return null; }
    let name = 'Прибор ' + idx;
    let resEl = document.getElementById(p + 'abs_result');
    if (resEl && absErr !== undefined) {
        resEl.innerHTML = '±Δ = ' + formatNumber(absErr);
        resEl.style.display = 'block';
    }
    return {idx: idx, name: name, absErr: absErr, form: form};
}

function calcErrorKit() {
    let devs = [];
    let container = document.getElementById('kit_device_list');
    let forms = container.querySelectorAll('[id^="kit_dev_"]');
    let allIdxs = [];
    forms.forEach((f, i) => {
        let m = f.id.match(/kit_dev_(\d+)/);
        if (m) allIdxs.push({idx: parseInt(m[1]), visualNum: i + 1});
    });
    for (let item of allIdxs) {
        let result = calcKitDeviceError(item.idx);
        if (result) { result.name = 'Прибор ' + item.visualNum; devs.push(result); }
    }
    if (devs.length === 0) { showToast('Добавьте хотя бы один прибор и заполните данные'); return; }
    let method = document.getElementById('kit_method').value;
    let totalAbs;
    let formulaText;
    if (method === 'geometric_plain') {
        let sumSq = 0;
        for (let d of devs) sumSq += d.absErr * d.absErr;
        totalAbs = Math.sqrt(sumSq);
        formulaText = 'Δ<sub>Σ</sub> = √(Δ₁² + Δ₂² + … + Δₙ²)';
    } else if (method === 'geometric') {
        let sumSq = 0;
        for (let d of devs) sumSq += d.absErr * d.absErr;
        totalAbs = 1.1 * Math.sqrt(sumSq);
        formulaText = 'Δ<sub>Σ</sub> = K·√(Δ₁² + Δ₂² + … + Δₙ²), K=1.1, P=0.95';
    } else {
        totalAbs = 0;
        for (let d of devs) totalAbs += d.absErr;
        formulaText = 'Δ<sub>Σ</sub> = Δ₁ + Δ₂ + … + Δₙ (арифметическое)';
    }
    let html = '<div class="converter-result-label-title">Результаты расчёта (комплект приборов)</div>';
    for (let d of devs) {
        html += '<div class="converter-result-item"><span class="converter-result-label">' + (d.name || 'Прибор ' + d.idx) + ': ±Δ</span><span class="converter-result-value" style="color:#4a8fc7;">± ' + formatNumber(d.absErr) + '</span></div>';
    }
    html += '<div class="converter-result-item"><span class="converter-result-label">Суммарная абс. погрешность (±Δ<sub>Σ</sub>)</span><span class="converter-result-value" style="color:#4ac771;">± ' + formatNumber(totalAbs) + '</span></div>';
    html += '<div class="converter-result-item" style="flex-direction:column;align-items:flex-start;gap:4px;"><span class="converter-result-label">Формула</span><span style="font-size:13px;color:rgba(140,180,210,0.9);line-height:1.5;">' + formulaText + '</span></div>';
    document.getElementById('errorKitResults').innerHTML = html;
    document.getElementById('errorKitResults').style.display = 'block';
    setTimeout(() => document.getElementById('errorKitResults').scrollIntoView({behavior:'smooth',block:'start'}), 100);
}

// Initialize kit page with 2 default devices
(function(){ addKitDevice('number', '0.5', '0', '1.6'); addKitDevice('number', '0.25', '4', '20'); })();

export {
    kitDeviceCount,
    calcErrorKit,
    addKitDevice,
    removeKitDevice,
    updateKitLimitMsg,
    toggleKitDevFields,
    toggleKitDevCustom,
    calcKitDeviceError
};
