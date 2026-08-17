/**
 * @module geometry
 * @description Geometry calculators — circle, ring, cylinder, horizontal cylinder,
 * sphere, and cone. Pure functions with DOM interaction for result display.
 * Extracted from src/index.html (lines ~10641-10792).
 *
 * External dependencies (temporary window bridges):
 *   - parseLocaleNumber  (utility, will be imported from core/utils once available)
 *   - formatNumber       (utility, will be imported from core/utils once available)
 *   - showToast          (will be imported from core/ui once available)
 */

const parseLocaleNumber = window.parseLocaleNumber;
const formatNumber = window.formatNumber;
const showToast = window.showToast;

// ============================================================
// КАЛЬКУЛЯТОРЫ ГЕОМЕТРИИ
// ============================================================

// Круг: площадь S = π·D²/4, периметр P = π·D, радиус R = D/2.
// D вводится в мм — площадь выводится в см² и м², периметр и радиус в мм.
function calcGeoCircle() {
    let Dmm = parseLocaleNumber(document.getElementById('gc_diameter').value);
    if (isNaN(Dmm) || Dmm <= 0) { showToast('Введите диаметр D'); return; }
    // Перевод в см и м для площади
    const Dcm = Dmm / 10;
    const Dm  = Dmm / 1000;
    const areaCm2 = Math.PI * Dcm * Dcm / 4;
    const areaM2  = Math.PI * Dm * Dm / 4;
    const perimeter = Math.PI * Dmm; // мм
    const radius = Dmm / 2;          // мм
    let html = '<div class="converter-result-label-title">Результат</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь S</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(areaCm2) + ' см² (' + formatNumber(areaM2) + ' м²)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Периметр P</span><span class="converter-result-value">' + formatNumber(perimeter) + ' мм (' + formatNumber(perimeter / 1000) + ' м)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Радиус R</span><span class="converter-result-value">' + formatNumber(radius) + ' мм</span></div>';
    const res = document.getElementById('gc_results');
    res.innerHTML = html;
    res.style.display = 'block';
    setTimeout(() => res.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// Кольцо: S = π·(D²−d²)/4, эквивалентный диаметр Dэкв = D − d.
// D и d в мм — площадь в см² и м², Dэкв в мм.
function calcGeoRing() {
    let Dmm = parseLocaleNumber(document.getElementById('gr_d_outer').value);
    let dmm = parseLocaleNumber(document.getElementById('gr_d_inner').value);
    if (isNaN(Dmm) || Dmm <= 0) { showToast('Введите наружный диаметр D'); return; }
    if (isNaN(dmm) || dmm <= 0) { showToast('Введите внутренний диаметр d'); return; }
    if (dmm >= Dmm) { showToast('d должен быть меньше D'); return; }
    const Dcm = Dmm / 10, dcm = dmm / 10;
    const Dm  = Dmm / 1000, dm = dmm / 1000;
    const areaCm2 = Math.PI * (Dcm * Dcm - dcm * dcm) / 4;
    const areaM2  = Math.PI * (Dm * Dm - dm * dm) / 4;
    const dEq = Dmm - dmm; // эквивалентный диаметр, мм
    let html = '<div class="converter-result-label-title">Результат</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь S</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(areaCm2) + ' см² (' + formatNumber(areaM2) + ' м²)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Эквивалентный диаметр Dэкв</span><span class="converter-result-value">' + formatNumber(dEq) + ' мм (' + formatNumber(dEq / 1000) + ' м)</span></div>';
    const res = document.getElementById('gr_results');
    res.innerHTML = html;
    res.style.display = 'block';
    setTimeout(() => res.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// Вертикальный цилиндр: V = π·D²·H/4, Sбок = π·D·H,
// Sполн = π·D·(D/2 + H), масса воды при ρ = 998 кг/м³.
// D и H в м.
function calcGeoCylinder() {
    let D = parseLocaleNumber(document.getElementById('gcy_diameter').value);
    let H = parseLocaleNumber(document.getElementById('gcy_height').value);
    if (isNaN(D) || D <= 0) { showToast('Введите диаметр D'); return; }
    if (isNaN(H) || H <= 0) { showToast('Введите высоту H'); return; }
    const volume = Math.PI * D * D * H / 4;          // м³
    const sideArea = Math.PI * D * H;                // м²
    const fullArea = Math.PI * D * (D / 2 + H);      // м²
    const waterMass = volume * 998;                  // кг (ρ = 998 кг/м³)
    let html = '<div class="converter-result-label-title">Результат</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Объём V</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(volume) + ' м³ (' + formatNumber(volume * 1000) + ' л)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь боковая Sбок</span><span class="converter-result-value">' + formatNumber(sideArea) + ' м²</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь полная Sполн</span><span class="converter-result-value">' + formatNumber(fullArea) + ' м²</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Масса воды (ρ=998)</span><span class="converter-result-value">' + formatNumber(waterMass) + ' кг</span></div>';
    const res = document.getElementById('gcy_results');
    res.innerHTML = html;
    res.style.display = 'block';
    setTimeout(() => res.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// Горизонтальный цилиндр при частичном заполнении.
// Площадь сегмента круга: S = R²·arccos((R−h)/R) − (R−h)·√(2·R·h − h²)
// V = S·L, Vполн = π·D²·L/4, % заполнения = V/Vполн·100.
// L, D, h в м. ρ воды = 998 кг/м³.
function calcGeoHorizCyl() {
    let L = parseLocaleNumber(document.getElementById('gh_length').value);
    let D = parseLocaleNumber(document.getElementById('gh_diameter').value);
    let h = parseLocaleNumber(document.getElementById('gh_level').value);
    if (isNaN(L) || L <= 0) { showToast('Введите длину L'); return; }
    if (isNaN(D) || D <= 0) { showToast('Введите диаметр D'); return; }
    if (isNaN(h) || h < 0) { showToast('Введите уровень h'); return; }
    if (h > D) { showToast('h не может быть больше D'); return; }
    const R = D / 2;
    let segmentArea;
    if (h === 0) {
        segmentArea = 0;
    } else if (h === D) {
        segmentArea = Math.PI * R * R;
    } else if (h === R) {
        segmentArea = Math.PI * R * R / 2;
    } else {
        // Общая формула площади кругового сегмента
        segmentArea = R * R * Math.acos((R - h) / R) - (R - h) * Math.sqrt(2 * R * h - h * h);
    }
    const volume = segmentArea * L;                  // м³
    const totalVolume = Math.PI * R * R * L;         // м³
    const fillPercent = totalVolume > 0 ? (volume / totalVolume) * 100 : 0;
    const waterMass = volume * 998;                  // кг
    let html = '<div class="converter-result-label-title">Результат</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Объём жидкости V</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(volume) + ' м³ (' + formatNumber(volume * 1000) + ' л)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Полный объём Vполн</span><span class="converter-result-value">' + formatNumber(totalVolume) + ' м³ (' + formatNumber(totalVolume * 1000) + ' л)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Заполнение</span><span class="converter-result-value">' + formatNumber(fillPercent) + ' %</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь сегмента S</span><span class="converter-result-value">' + formatNumber(segmentArea) + ' м²</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Масса воды (ρ=998)</span><span class="converter-result-value">' + formatNumber(waterMass) + ' кг</span></div>';
    const res = document.getElementById('gh_results');
    res.innerHTML = html;
    res.style.display = 'block';
    setTimeout(() => res.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// Сфера: V = π·D³/6, S = π·D², масса воды при ρ = 998 кг/м³.
// D в м.
function calcGeoSphere() {
    let D = parseLocaleNumber(document.getElementById('gs_diameter').value);
    if (isNaN(D) || D <= 0) { showToast('Введите диаметр D'); return; }
    const volume = Math.PI * D * D * D / 6;          // м³
    const surface = Math.PI * D * D;                 // м²
    const waterMass = volume * 998;                  // кг
    let html = '<div class="converter-result-label-title">Результат</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Объём V</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(volume) + ' м³ (' + formatNumber(volume * 1000) + ' л)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь поверхности S</span><span class="converter-result-value">' + formatNumber(surface) + ' м²</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Масса воды (ρ=998)</span><span class="converter-result-value">' + formatNumber(waterMass) + ' кг</span></div>';
    const res = document.getElementById('gs_results');
    res.innerHTML = html;
    res.style.display = 'block';
    setTimeout(() => res.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// Конус: V = π·D²·H/12, Sосн = π·D²/4,
// образующая L = √(H² + (D/2)²), Sбок = π·(D/2)·L.
// D и H в м.
function calcGeoCone() {
    let D = parseLocaleNumber(document.getElementById('gco_diameter').value);
    let H = parseLocaleNumber(document.getElementById('gco_height').value);
    if (isNaN(D) || D <= 0) { showToast('Введите диаметр D'); return; }
    if (isNaN(H) || H <= 0) { showToast('Введите высоту H'); return; }
    const R = D / 2;
    const volume = Math.PI * D * D * H / 12;         // м³
    const baseArea = Math.PI * D * D / 4;            // м²
    const slant = Math.sqrt(H * H + R * R);          // м, образующая
    const sideArea = Math.PI * R * slant;            // м²
    let html = '<div class="converter-result-label-title">Результат</div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Объём V</span><span class="converter-result-value" style="color:#4ac771;">' + formatNumber(volume) + ' м³ (' + formatNumber(volume * 1000) + ' л)</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь основания Sосн</span><span class="converter-result-value">' + formatNumber(baseArea) + ' м²</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Образующая L</span><span class="converter-result-value">' + formatNumber(slant) + ' м</span></div>';
    html += '<div class="converter-result-item"><span class="converter-result-label">Площадь боковая Sбок</span><span class="converter-result-value">' + formatNumber(sideArea) + ' м²</span></div>';
    const res = document.getElementById('gco_results');
    res.innerHTML = html;
    res.style.display = 'block';
    setTimeout(() => res.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// ========================
// Public exports
// ========================
export { calcGeoCircle, calcGeoRing, calcGeoCylinder, calcGeoHorizCyl, calcGeoSphere, calcGeoCone };
