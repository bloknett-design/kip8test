/**
 * @module core/custom-select
 * @description Custom select dropdown system — replaces native <select> with styled dropdowns.
 * Extracted from the monolithic src/index.html (lines 14420–14869).
 */

// Container for all dropdown panels (appended to body to avoid z-index stacking issues)
var dropdownContainer = document.createElement('div');
dropdownContainer.id = 'cs-dropdown-container';
dropdownContainer.style.cssText = 'position:fixed;top:0;left:0;width:0;height:0;z-index:99999;pointer-events:none;';
document.body.appendChild(dropdownContainer);

// Global click handler to close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.cs-wrapper') && !e.target.closest('.cs-dropdown')) {
        closeAllDropdowns();
    }
});
// Close on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeAllDropdowns();
});

function closeAllDropdowns() {
    document.querySelectorAll('.cs-dropdown.cs-show').forEach(function(dd) {
        dd.classList.remove('cs-show');
        dd.classList.remove('cs-drop-up');
        dd.style.pointerEvents = 'none';
        dd.style.minWidth = '';
        dd.style.maxWidth = '';
        dd.style.width = '';
        var trigger = dd._csTrigger;
        if (trigger) trigger.classList.remove('cs-open');
    });
}

// Map: select element → current optgroup hint for its options
// Used for temp_rtd_type where optgroup data is shown inline
function getOptgroupHints(select) {
    var hints = {};
    var currentGroup = '';
    var options = select.querySelectorAll('option, optgroup');
    options.forEach(function(opt) {
        if (opt.tagName === 'OPTGROUP') {
            currentGroup = opt.getAttribute('label') || '';
        } else if (opt.tagName === 'OPTION') {
            hints[opt.value] = currentGroup;
        }
    });
    return hints;
}

function buildDropdown(select) {
    // Skip already-converted selects
    if (select.closest('.cs-wrapper')) return;

    var wrapper = document.createElement('div');
    wrapper.className = 'cs-wrapper';

    // Transfer layout-related inline styles from select to wrapper
    var inlineStyle = select.getAttribute('style') || '';
    var layoutProps = ['flex', 'width', 'min-width', 'max-width', 'margin-bottom'];
    var wrapperStyle = '';
    layoutProps.forEach(function(prop) {
        var re = new RegExp(prop + '\\s*:\\s*([^;]+)', 'i');
        var m = inlineStyle.match(re);
        if (m) wrapperStyle += prop + ':' + m[1] + ';';
    });
    if (wrapperStyle) wrapper.setAttribute('style', wrapperStyle);

    // Mark wrapper as being inside kit-dev-form context (for CSS descendant selectors)
    // Do NOT add 'kit-dev-form' class directly — it carries unwanted margin/padding

    // Build trigger
    var trigger = document.createElement('div');
    trigger.className = 'cs-trigger';
    trigger.setAttribute('tabindex', '0');
    trigger.setAttribute('role', 'combobox');
    trigger.setAttribute('aria-expanded', 'false');
    var selectedOpt = select.options[select.selectedIndex];
    var triggerText = document.createElement('span');
    triggerText.className = 'cs-trigger-text';
    triggerText.textContent = selectedOpt ? selectedOpt.textContent : '';
    trigger.appendChild(triggerText);

    // Build dropdown panel (appended to body container for z-index fix)
    var dropdown = document.createElement('div');
    dropdown.className = 'cs-dropdown';
    dropdown._csTrigger = trigger;

    // Get optgroup hints if this select uses optgroups with meaningful data
    var hints = getOptgroupHints(select);

    buildDropdownOptions(select, dropdown, hints);

    dropdownContainer.appendChild(dropdown);

    // Toggle dropdown on trigger click
    trigger.addEventListener('click', function(ev) {
        ev.stopPropagation();
        var isOpen = dropdown.classList.contains('cs-show');
        closeAllDropdowns();
        if (!isOpen) {
            // Position dropdown relative to trigger using fixed positioning
            var triggerRect = trigger.getBoundingClientRect();
            var spaceBelow = window.innerHeight - triggerRect.bottom;
            var spaceAbove = triggerRect.top;
            // Measure dropdown: auto-size width to fit content, min = trigger width
            var vpWidth = window.innerWidth;
            dropdown.style.visibility = 'hidden';
            dropdown.style.display = 'block';
            dropdown.style.minWidth = triggerRect.width + 'px';
            dropdown.style.maxWidth = (vpWidth - 16) + 'px';
            dropdown.style.width = 'auto';
            var dropHeight = Math.min(dropdown.scrollHeight, 220);
            var dropWidth = dropdown.offsetWidth;
            dropdown.style.display = '';
            dropdown.style.visibility = '';

            // Calculate left position: align to trigger, but keep within viewport
            var dropLeft = triggerRect.left;
            if (dropLeft + dropWidth > vpWidth - 8) {
                dropLeft = Math.max(8, vpWidth - dropWidth - 8);
            }

            if (spaceBelow < dropHeight && spaceAbove > spaceBelow) {
                dropdown.style.top = 'auto';
                dropdown.style.bottom = (window.innerHeight - triggerRect.top + 4) + 'px';
                dropdown.style.left = dropLeft + 'px';
                dropdown.classList.add('cs-drop-up');
            } else {
                dropdown.style.top = (triggerRect.bottom + 4) + 'px';
                dropdown.style.bottom = 'auto';
                dropdown.style.left = dropLeft + 'px';
                dropdown.classList.remove('cs-drop-up');
            }
            dropdown.classList.add('cs-show');
            dropdown.style.pointerEvents = 'auto';
            trigger.classList.add('cs-open');
            trigger.setAttribute('aria-expanded', 'true');
            scrollToSelected(dropdown);
        } else {
            trigger.setAttribute('aria-expanded', 'false');
        }
    });
    // Keyboard support
    trigger.addEventListener('keydown', function(ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); trigger.click(); }
        else if (ev.key === 'Escape') closeAllDropdowns();
    });

    // Hide the native select visually but keep in DOM for JS compatibility
    select.style.position = 'absolute';
    select.style.width = '0';
    select.style.height = '0';
    select.style.opacity = '0';
    select.style.pointerEvents = 'none';
    select.style.overflow = 'hidden';
    select.style.margin = '0';
    select.style.padding = '0';
    select.style.border = 'none';

    // Insert wrapper
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(trigger);
    wrapper.appendChild(select);

    // Store references
    select._csWrapper = wrapper;
    select._csTrigger = trigger;
    select._csTriggerText = triggerText;
    select._csDropdown = dropdown;
    select._csHints = hints;
}

function buildDropdownOptions(select, dropdown, hints) {
    dropdown.innerHTML = '';
    var options = select.querySelectorAll('option, optgroup');
    options.forEach(function(opt) {
        if (opt.tagName === 'OPTGROUP') {
            // Skip optgroup labels — they are shown as hints inline
            return;
        } else if (opt.tagName === 'OPTION') {
            var optDiv = document.createElement('div');
            optDiv.className = 'cs-option';
            if (opt.selected) optDiv.classList.add('cs-selected');
            if (opt.disabled) optDiv.classList.add('cs-disabled');
            optDiv.setAttribute('data-value', opt.value);

            var mainText = document.createElement('span');
            mainText.textContent = opt.textContent;
            optDiv.appendChild(mainText);

            // If there's an optgroup hint or data-hint attribute for this option, show it inline on the right
            var hintText = hints[opt.value] || opt.getAttribute('data-hint') || '';
            if (hintText) {
                var hintSpan = document.createElement('span');
                hintSpan.className = 'cs-option-hint';
                hintSpan.textContent = hintText;
                optDiv.appendChild(hintSpan);
            }

            optDiv.addEventListener('click', function(ev) {
                ev.stopPropagation();
                if (optDiv.classList.contains('cs-disabled')) return;
                selectOption(select, optDiv);
            });
            dropdown.appendChild(optDiv);
        }
    });
}

function selectOption(select, optDiv) {
    var trigger = select._csTrigger;
    var dropdown = select._csDropdown;
    var value = optDiv.getAttribute('data-value');
    // Set value (triggers syncFromNative via overridden setter)
    select.value = value;

    // Update selected visual
    dropdown.querySelectorAll('.cs-option.cs-selected').forEach(function(o) { o.classList.remove('cs-selected'); });
    optDiv.classList.add('cs-selected');

    // Close dropdown
    dropdown.classList.remove('cs-show');
    dropdown.classList.remove('cs-drop-up');
    dropdown.style.pointerEvents = 'none';
    dropdown.style.minWidth = '';
    dropdown.style.maxWidth = '';
    dropdown.style.width = '';
    trigger.classList.remove('cs-open');
    trigger.setAttribute('aria-expanded', 'false');

    // Fire native change event
    var event = new Event('change', { bubbles: true });
    select.dispatchEvent(event);

    // Haptic feedback
    if (navigator.vibrate) navigator.vibrate(10);
}

function scrollToSelected(dropdown) {
    var selected = dropdown.querySelector('.cs-option.cs-selected');
    if (selected) {
        setTimeout(function() {
            selected.scrollIntoView({ block: 'nearest', inline: 'nearest' });
        }, 10);
    }
}

// Sync custom dropdown when native select value changes programmatically
function syncFromNative(select) {
    var trigger = select._csTrigger;
    var triggerText = select._csTriggerText;
    var dropdown = select._csDropdown;
    if (!trigger || !triggerText || !dropdown) return;

    var selectedOpt = select.options[select.selectedIndex];
    triggerText.textContent = selectedOpt ? selectedOpt.textContent : '';

    dropdown.querySelectorAll('.cs-option').forEach(function(o) {
        if (o.getAttribute('data-value') === select.value) {
            o.classList.add('cs-selected');
        } else {
            o.classList.remove('cs-selected');
        }
    });
}

// Override value setter on HTMLSelectElement
var origValueDesc = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
var origValueGetter = origValueDesc.get;
var origValueSetter = origValueDesc.set;
Object.defineProperty(HTMLSelectElement.prototype, 'value', {
    set: function(val) {
        origValueSetter.call(this, val);
        if (this._csWrapper) syncFromNative(this);
    },
    get: function() { return origValueGetter.call(this); }
});

// Override selected setter on HTMLOptionElement
var origOptionSelectedDesc = Object.getOwnPropertyDescriptor(HTMLOptionElement.prototype, 'selected');
var origOptionSelectedGetter = origOptionSelectedDesc.get;
var origOptionSelectedSetter = origOptionSelectedDesc.set;
Object.defineProperty(HTMLOptionElement.prototype, 'selected', {
    set: function(val) {
        origOptionSelectedSetter.call(this, val);
        var select = this.closest('select');
        if (select && select._csWrapper) syncFromNative(select);
    },
    get: function() { return origOptionSelectedGetter.call(this); }
});

// Override disabled setter on HTMLOptionElement
var origOptionDisabledDesc = Object.getOwnPropertyDescriptor(HTMLOptionElement.prototype, 'disabled');
var origOptionDisabledGetter = origOptionDisabledDesc.get;
var origOptionDisabledSetter = origOptionDisabledDesc.set;
Object.defineProperty(HTMLOptionElement.prototype, 'disabled', {
    set: function(val) {
        origOptionDisabledSetter.call(this, val);
        var select = this.closest('select');
        if (select && select._csDropdown) {
            var val_ = this.value;
            var optEl = select._csDropdown.querySelector('.cs-option[data-value="' + CSS.escape(val_) + '"]');
            if (optEl) {
                if (val) optEl.classList.add('cs-disabled');
                else optEl.classList.remove('cs-disabled');
            }
        }
    },
    get: function() { return origOptionDisabledGetter.call(this); }
});

// Override innerHTML setter for <select> to auto-rebuild custom dropdown
var origInnerHTMLDesc = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
Object.defineProperty(HTMLSelectElement.prototype, 'innerHTML', {
    set: function(html) {
        origInnerHTMLDesc.set.call(this, html);
        if (this._csWrapper && typeof window.rebuildCustomSelect === 'function') {
            window.rebuildCustomSelect(this);
        }
    },
    get: function() { return origInnerHTMLDesc.get.call(this); }
});

// Initialize all existing selects
function initCustomSelects(root) {
    root = root || document;
    var selects = root.querySelectorAll('select.scale-field, select.form-field');
    selects.forEach(function(sel) { buildDropdown(sel); });
}

// Refresh custom selects for dynamically added content
function refreshCustomSelects(container) {
    container = container || document;
    var selects = container.querySelectorAll('select.scale-field, select.form-field');
    selects.forEach(function(sel) {
        if (!sel._csWrapper) buildDropdown(sel);
    });
}

// Rebuild a specific select's custom dropdown (when options change)
function rebuildCustomSelect(selectEl) {
    if (!selectEl || !selectEl._csWrapper) return;
    var dropdown = selectEl._csDropdown;
    var hints = getOptgroupHints(selectEl);
    selectEl._csHints = hints;
    buildDropdownOptions(selectEl, dropdown, hints);
    syncFromNative(selectEl);
}

// Backward compat with inline HTML handlers
window.refreshCustomSelects = refreshCustomSelects;
window.rebuildCustomSelect = rebuildCustomSelect;

// Initialize on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { initCustomSelects(); });
} else {
    initCustomSelects();
}

// MutationObserver for dynamically added selects
var csObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(m) {
        m.addedNodes.forEach(function(node) {
            if (node.nodeType !== 1) return;
            if (node.tagName === 'SELECT' && (node.classList.contains('scale-field') || node.classList.contains('form-field'))) {
                if (!node._csWrapper) buildDropdown(node);
            }
            var selects = node.querySelectorAll ? node.querySelectorAll('select.scale-field, select.form-field') : [];
            selects.forEach(function(sel) {
                if (!sel._csWrapper) buildDropdown(sel);
            });
        });
    });
});
csObserver.observe(document.body, { childList: true, subtree: true });

// Reposition open dropdown on scroll/resize
window.addEventListener('scroll', function() {
    document.querySelectorAll('.cs-dropdown.cs-show').forEach(function(dd) {
        var trigger = dd._csTrigger;
        if (!trigger) return;
        var rect = trigger.getBoundingClientRect();
        var vpW = window.innerWidth;
        dd.style.minWidth = rect.width + 'px';
        dd.style.maxWidth = (vpW - 16) + 'px';
        dd.style.width = 'auto';
        var dw = dd.offsetWidth;
        var dl = rect.left;
        if (dl + dw > vpW - 8) dl = Math.max(8, vpW - dw - 8);
        dd.style.left = dl + 'px';
        if (dd.classList.contains('cs-drop-up')) {
            dd.style.bottom = (window.innerHeight - rect.top + 4) + 'px';
            dd.style.top = 'auto';
        } else {
            dd.style.top = (rect.bottom + 4) + 'px';
            dd.style.bottom = 'auto';
        }
    });
}, true);
window.addEventListener('resize', function() {
    document.querySelectorAll('.cs-dropdown.cs-show').forEach(function(dd) {
        var trigger = dd._csTrigger;
        if (!trigger) return;
        var rect = trigger.getBoundingClientRect();
        var vpW = window.innerWidth;
        dd.style.minWidth = rect.width + 'px';
        dd.style.maxWidth = (vpW - 16) + 'px';
        dd.style.width = 'auto';
        var dw = dd.offsetWidth;
        var dl = rect.left;
        if (dl + dw > vpW - 8) dl = Math.max(8, vpW - dw - 8);
        dd.style.left = dl + 'px';
    });
});

export { refreshCustomSelects, rebuildCustomSelect };
