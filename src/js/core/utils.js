/**
 * @module core/utils
 * @description Shared utility functions used across multiple modules.
 * Extracted from the monolithic src/index.html (lines 9223–12325).
 */

// ============================================================
// Layout detection
// ============================================================

/** Определяет, работает ли приложение в десктопном режиме */
export function isDesktop() {
    return window.matchMedia('(min-width: 1024px)').matches;
}

/** Определяет, работает ли приложение в планшетном режиме */
export function isTablet() {
    return window.matchMedia('(min-width: 768px) and (max-width: 1023px)').matches;
}

// ============================================================
// Toast notification
// ============================================================

export function showToast(msg, actionText, actionFn) {
    let t = document.getElementById('toast');
    let m = document.getElementById('toastMessage');
    let a = document.getElementById('toastAction');
    m.textContent = msg;
    if (actionText && actionFn) {
        a.textContent = actionText;
        a.style.display = 'inline';
        a.onclick = function() { t.classList.remove('show'); a.style.display = 'none'; a.onclick = null; actionFn(); };
    } else {
        a.style.display = 'none';
        a.onclick = null;
    }
    t.classList.add('show');
    if (navigator.vibrate) navigator.vibrate(50);
    clearTimeout(t._hideTimer);
    t._hideTimer = setTimeout(() => { t.classList.remove('show'); a.style.display = 'none'; a.onclick = null; }, 3000);
}

// ============================================================
// Кастомные диалоги kipConfirm / kipPrompt
// Заменяют нативные confirm()/prompt(), чтобы убрать
// «Подтвердите действие на bloknett-design.github.io»
// ============================================================

/** Получить или создать общий оверлей для кастомных диалогов. */
export function _kipDialogOverlay() {
    let ov = document.getElementById('kipDialogOverlay');
    if (ov) return ov;
    ov = document.createElement('div');
    ov.id = 'kipDialogOverlay';
    ov.className = 'kip-dialog-overlay';
    document.body.appendChild(ov);
    return ov;
}

/** Закрыть диалог и вернуть результат. */
export function _kipDialogClose(ov, resolve, value) {
    ov.classList.remove('active');
    setTimeout(function() { ov.innerHTML = ''; }, 250);
    resolve(value);
}

/**
 * Кастомный confirm-диалог.
 * @param {string} msg — текст вопроса
 * @param {object} [opts] — { danger: true } — красная кнопка OK
 * @returns {Promise<boolean>}
 */
export function kipConfirm(msg, opts) {
    opts = opts || {};
    return new Promise(function(resolve) {
        var ov = _kipDialogOverlay();
        var dangerCls = opts.danger ? ' danger' : '';
        ov.innerHTML =
            '<div class="kip-dialog">' +
                '<div class="kip-dialog-title">Подтвердите действие</div>' +
                '<div class="kip-dialog-msg">' + (msg || '').replace(/</g,'&lt;') + '</div>' +
                '<div class="kip-dialog-btns">' +
                    '<button type="button" class="kip-dialog-btn kip-dialog-cancel">Отмена</button>' +
                    '<button type="button" class="kip-dialog-btn kip-dialog-ok' + dangerCls + '">OK</button>' +
                '</div>' +
            '</div>';
        ov.querySelector('.kip-dialog-cancel').onclick = function() { _kipDialogClose(ov, resolve, false); };
        ov.querySelector('.kip-dialog-ok').onclick = function() { _kipDialogClose(ov, resolve, true); };
        requestAnimationFrame(function() { ov.classList.add('active'); });
    });
}

/**
 * Кастомный prompt-диалог.
 * @param {string} msg — подсказка
 * @param {string} [defaultVal] — значение по умолчанию
 * @returns {Promise<string|null>} — null при отмене
 */
export function kipPrompt(msg, defaultVal) {
    return new Promise(function(resolve) {
        var ov = _kipDialogOverlay();
        var val = (defaultVal != null) ? String(defaultVal).replace(/"/g,'&quot;') : '';
        ov.innerHTML =
            '<div class="kip-dialog">' +
                '<div class="kip-dialog-title">Подтвердите действие</div>' +
                '<div class="kip-dialog-msg">' + (msg || '').replace(/</g,'&lt;') + '</div>' +
                '<input type="text" class="kip-dialog-input" value="' + val + '">' +
                '<div class="kip-dialog-btns">' +
                    '<button type="button" class="kip-dialog-btn kip-dialog-cancel">Отмена</button>' +
                    '<button type="button" class="kip-dialog-btn kip-dialog-ok">OK</button>' +
                '</div>' +
            '</div>';
        var inp = ov.querySelector('.kip-dialog-input');
        ov.querySelector('.kip-dialog-cancel').onclick = function() { _kipDialogClose(ov, resolve, null); };
        ov.querySelector('.kip-dialog-ok').onclick = function() { _kipDialogClose(ov, resolve, inp.value); };
        inp.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') { _kipDialogClose(ov, resolve, inp.value); }
            if (e.key === 'Escape') { _kipDialogClose(ov, resolve, null); }
        });
        requestAnimationFrame(function() {
            ov.classList.add('active');
            inp.focus();
            inp.select();
        });
    });
}

// ============================================================
// Number parsing & formatting
// ============================================================

export function parseLocaleNumber(s){ if(typeof s!=='string')s=String(s); return parseFloat(s.replace(',','.')); }

// Форматирование числа с русской запятой и разделением разрядов
// неразрывным пробелом: 1234567.89 → "1 234 567,89"
// Соответствует ГОСТ-стилю и русской типографике.
export function formatNumber(n) {
    if (n===0) return '0';
    if (Math.abs(n)>=1e9||Math.abs(n)<0.00001&&n!==0) return n.toExponential(4).replace('.',',');
    let d=Math.abs(n)>=100?2:Math.abs(n)>=1?4:6;
    // Округляем до нужного числа знаков, затем заменяем точку на запятую
    let s = parseFloat(n.toFixed(d)).toString().replace('.',',');
    // Добавляем неразрывные пробелы между разрядами целой части
    // \u00A0 — неразрывный пробел (not \u0020), чтобы число не разрывалось
    // при переносе строки. Разделяем только целую часть (до запятой).
    const parts = s.split(',');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '\u00A0');
    return parts.join(',');
}

export function roundNumber(n) {
    if (n === 0) return '0';
    let absN = Math.abs(n);
    if (absN >= 1e9 || (absN < 0.00001 && n !== 0)) return n.toExponential(1).replace('.',',');
    // Round to 2 significant figures: keep first 2 digits, rest zeros
    let order = Math.floor(Math.log10(absN));
    let dp = 1 - order; // decimal places needed for 2 sig figs
    let s;
    if (dp < 0) {
        // Round to nearest 10^(-dp) for large numbers
        let factor = Math.pow(10, -dp);
        let result = Math.round(n / factor) * factor;
        s = result.toString().replace('.',',');
    } else {
        let result = parseFloat(n.toFixed(dp));
        s = result.toString().replace('.',',');
    }
    // Разделяем разряды целой части неразрывным пробелом
    const parts = s.split(',');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '\u00A0');
    return parts.join(',');
}

// ============================================================
// Валидация полей ввода (#12)
// ============================================================
// При невалидном значении поле подсвечивается красной рамкой
// и под ним показывается подсказка. При исправлении — рамка
// и подсказка исчезают.
//
// Использование:
//   <input oninput="validateNumericField(this)" />
//   <input oninput="validatePositiveField(this)" />
//   <input oninput="validateField(this, val => val > 0, 'Должно быть > 0')" />
// ============================================================

// Универсальная функция валидации. Принимает элемент, функцию-предикат
// (должна вернуть true, если значение валидно) и сообщение об ошибке.
export function validateField(input, isValid, errorMsg) {
    // Удаляем предыдущую подсказку, если была
    const existingMsg = input.parentElement.querySelector('.input-error-msg[data-for="' + input.id + '"]');
    if (existingMsg) existingMsg.remove();

    const raw = input.value.trim();
    if (raw === '') {
        // Пустое поле не считаем ошибкой — это будет проверено при submit
        input.classList.remove('input-error');
        return true;
    }

    const val = parseLocaleNumber(raw);
    const valid = isValid(val, raw);
    if (valid) {
        input.classList.remove('input-error');
    } else {
        input.classList.add('input-error');
        // Добавляем подсказку под полем
        const msg = document.createElement('span');
        msg.className = 'input-error-msg';
        msg.dataset.for = input.id;
        msg.textContent = errorMsg || 'Некорректное значение';
        // Вставляем после поля
        input.parentNode.insertBefore(msg, input.nextSibling);
    }
    return valid;
}

// Готовые валидаторы для типовых случаев
export function validateNumericField(input) {
    return validateField(input, (val) => !isNaN(val), 'Введите число');
}
export function validatePositiveField(input) {
    return validateField(input, (val) => !isNaN(val) && val > 0, 'Должно быть положительным числом');
}
export function validateNonNegativeField(input) {
    return validateField(input, (val) => !isNaN(val) && val >= 0, 'Должно быть неотрицательным числом');
}
export function validateRangeField(input, min, max) {
    return validateField(input, (val) => !isNaN(val) && val >= min && val <= max,
        'Должно быть в диапазоне ' + min + '–' + max);
}

// Утилита: снять ошибку с поля (вызывается при успешном расчёте)
export function clearFieldError(input) {
    if (!input) return;
    input.classList.remove('input-error');
    const msg = input.parentElement.querySelector('.input-error-msg[data-for="' + input.id + '"]');
    if (msg) msg.remove();
}

// Утилита: проверить, есть ли ошибки валидации в контейнере
// (например, в форме расчёта). Возвращает true, если есть ошибки.
export function hasValidationErrors(container) {
    if (!container) return false;
    return container.querySelectorAll('.input-error').length > 0;
}
