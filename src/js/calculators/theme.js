/**
 * @module calculators/theme
 * Theme toggle and logo/buoy image update functionality
 */
// Theme toggle functionality
function toggleTheme() {
    let currentTheme = localStorage.getItem('app-theme') || 'light';
    let newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('app-theme', newTheme);
    updateThemeLabel();
    updateBuoyImages();
    updateLogoImage();
}

function updateThemeLabel() {
    let label = document.getElementById('themeLabel');
    if (label) {
        let currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        label.textContent = currentTheme === 'dark' ? 'Светлая тема' : 'Тёмная тема';
    }
}

function updateBuoyImages() {
    var isLight = document.documentElement.getAttribute('data-theme') === 'light';
    var buoyWithImg = document.getElementById('buoy-with-img');
    var buoyWithoutImg = document.getElementById('buoy-without-img');
    if (buoyWithImg) buoyWithImg.src = isLight ? 'images/buoy_with.png' : 'images/buoy_with_black.png';
    if (buoyWithoutImg) buoyWithoutImg.src = isLight ? 'images/buoy_without.png' : 'images/buoy_without_black.png';
}

function updateLogoImage() {
    var isLight = document.documentElement.getAttribute('data-theme') === 'light';
    var logoSrc = isLight ? 'images/logo.png' : 'images/logo_black.png';
    var logo = document.getElementById('headerLogo');
    if (logo) logo.src = logoSrc;
    var logoDesktop = document.getElementById('headerLogoDesktop');
    if (logoDesktop) logoDesktop.src = logoSrc;
}

// Apply saved theme on load
(function() {
    let savedTheme = localStorage.getItem('app-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    // Перезапись UI (label, logos, buoy) выполняется в последнем
    // <script> блоке, когда все DOM-элементы уже существуют.
    // Здесь вызываем для элементов, которые уже разобраны к этому моменту.
    updateThemeLabel();
    updateBuoyImages();
    updateLogoImage();
})();

// Auto-detect system color scheme preference
(function() {
    const saved = localStorage.getItem('app-theme');
    if (!saved) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        if (typeof updateThemeLabel === 'function') updateThemeLabel();
        if (typeof updateLogoImage === 'function') updateLogoImage();
    }
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('app-theme')) {
            document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            if (typeof updateThemeLabel === 'function') updateThemeLabel();
            if (typeof updateBuoyImages === 'function') updateBuoyImages();
            if (typeof updateLogoImage === 'function') updateLogoImage();
        }
    });
})();

export {
    toggleTheme,
    updateThemeLabel,
    updateBuoyImages,
    updateLogoImage
};
