#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 397 (заявка, kip8test): «Примени общее правило к приложению,
# если у пользователя, согласно его роли, нет доступа к определённому
# разделу, то кнопка данного раздела не должна отображаться».
#
# Обобщение правила Task 395 (кнопка «Работники» по матрице) на ВСЁ
# приложение. Аудит показал: сайдбар/меню-кнопки/вкладки верхнего бара
# уже гейтятся списком allowed, но остаются ТОЧКИ-НАРУШЕНИЯ:
#   · «Инженерные калькуляторы» нижнего бара главной — «видна всегда»:
#     у роли БЕЗ calc.view («Запрет», снятая галочка в матрице) кнопка
#     вела на экран «Нет доступа»;
#   · композит docs|library|kip-ios (нижний бар + вкладка «Документация»
#     десктопа) мог ПОКАЗЫВАТЬ кнопку роли, которой page-docs недоступен
#     (гипотетический kipios без library.view) — клик → «Нет доступа»;
#   · кнопки с onclick, назначенным через addEventListener
#     (входы КИП ИОС), не покрыты общим проходом по атрибуту.
#
# РЕШЕНИЕ — универсальный проход ОБЩЕГО ПРАВИЛА в _applyRoleToUI:
# ЛЮБОЙ элемент с onclick="navigateTo('страница')" (кроме хлебных
# крошек — контекстная навигация внутри доступной страницы) виден
# ⟺ его пропустит сам navigateTo (canAccess — тот же гейт). Проход
# идёт ПЕРВЫМ и СИММЕТРИЧЕН (показ/скрытие): спец-логика ниже может
# только ДОПОЛНИТЕЛЬНО скрыть (фильтр 4, «Графики» вне Electron,
# пустые родительские страницы) — конфликтов показа нет.
import io, sys

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
n0 = src

def rep(old, new, what, count=1):
    global src
    found = src.count(old)
    assert found == count, '%s: найдено %d (ожидалось %d)' % (what, found, count)
    src = src.replace(old, new)
    print('  ✓ %s' % what)

# ============================================================
# 1. УНИВЕРСАЛЬНЫЙ ПРОХОД ОБЩЕГО ПРАВИЛА (начало _applyRoleToUI)
# ============================================================
rep(
"""            if (!this._cachedRole) return;
            const allowed = this.ROLE_ACCESS[this._cachedRole] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const self = this;

            // Sidebar items: извлечь page из onclick="navigateTo('xxx')".
""",
"""            if (!this._cachedRole) return;
            const allowed = this.ROLE_ACCESS[this._cachedRole] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const self = this;

            // ============================================================
            // Task 397 (ОБЩЕЕ ПРАВИЛО): если у пользователя, согласно
            // его роли, нет доступа к разделу — КНОПКА РАЗДЕЛА НЕ
            // ОТОБРАЖАЕТСЯ. Универсальный проход — единое правило для
            // ЛЮБОЙ навигационной кнопки приложения: элемент с onclick
            // «navigateTo('страница')» виден ТОГДА И ТОЛЬКО ТОГДА, когда
            // его пропустит сам navigateTo (canAccess — тот же гейт, что
            // в navigateTo перед показом экрана «Нет доступа»; спец-случаи
            // админ-страниц и Electron-графиков учтены внутри canAccess).
            // Проход идёт ПЕРВЫМ и СИММЕТРИЧЕН (показ/скрытие — актуально
            // при смене роли): спец-логика ниже может только ДОПОЛНИТЕЛЬНО
            // скрыть (фильтр 4 ИТР ТОКЕМ — «Кабельный журнал»/«Проекты»,
            // «Графики» вне Electron, пустые родительские страницы
            // Task 115) — конфликтов показа нет.
            // ИСКЛЮЧЕНИЕ: хлебные крошки .breadcrumb-link — контекстная
            // навигация ВНУТРИ уже доступной страницы (путь назад),
            // не вход в раздел.
            // ============================================================
            document.querySelectorAll('[onclick*="navigateTo("]').forEach(function(el) {
                if (el.classList && el.classList.contains('breadcrumb-link')) return;
                const m = String(el.getAttribute('onclick') || '')
                    .match(/navigateTo\\(['"]([^'"]+)['"]\\)/);
                if (!m) return;
                el.style.display = self.canAccess(m[1]) ? '' : 'none';
            });

            // Кнопки с onclick, назначенным через addEventListener
            // (атрибут onclick пуст — проход по атрибуту их не видит):
            // явная карта «id → целевая страница». Входы КИП ИОС живут
            // на странице раздела (доступ к ней уже проверен), карта —
            // страховочная сеть общего правила; chartsEntryBtn — раздел
            // только десктопа (canAccess учитывает IS_ELECTRON).
            var JS_NAV_TARGETS = {
                devicesEntryBtn: 'devices-prod',
                lockoutsEntryBtn: 'lockouts-prod',
                valvesEntryBtn: 'valves-prod',
                regulatorsEntryBtn: 'regulators-prod',
                projectsEntryBtn: 'projects-prod',
                cablesEntryBtn: 'cable-journal-edit',
                plan114EntryBtn: 'plan-114',
                chartsEntryBtn: 'charts'
            };
            Object.keys(JS_NAV_TARGETS).forEach(function(id) {
                var el = document.getElementById(id);
                if (!el) return;
                el.style.display = self.canAccess(JS_NAV_TARGETS[id]) ? '' : 'none';
            });

            // Sidebar items: извлечь page из onclick="navigateTo('xxx')".
""", 'универсальный проход общего правила + карта JS-кнопок')

# ============================================================
# 2. Нижний бар главной: «Документация» — композит упрощён до
#    canAccess-эквивалента; «Инженерные калькуляторы» — гейт
#    (прежде «видна всегда»); бар скрыт, если ОБЕ кнопки скрыты
# ============================================================
rep(
"""            const docsBottomBtn = document.querySelector('.dashboard-bottom-btn-docs');
            if (docsBottomBtn) {
                const hasDocsAccess = isAll
                    || allowed.indexOf('docs') !== -1
                    || allowed.indexOf('library') !== -1
                    || allowed.indexOf('kip-ios') !== -1;
                docsBottomBtn.style.display = hasDocsAccess ? '' : 'none';
            }
""",
"""            const docsBottomBtn = document.querySelector('.dashboard-bottom-btn-docs');
            if (docsBottomBtn) {
                // Task 397 (общее правило): видна ⟺ есть доступ к docs
                // (композит library/kip-ios вёл на «Нет доступа»).
                const hasDocsAccess = isAll || allowed.indexOf('docs') !== -1;
                docsBottomBtn.style.display = hasDocsAccess ? '' : 'none';
            }
            // Task 397 (общее правило): «Инженерные калькуляторы» — прежде
            // «видна всегда»: у роли БЕЗ calc.view (например «Запрет» или
            // снятая галочка в матрице) кнопка вела на «Нет доступа».
            // Теперь гейт симметричен «Документации»: нет доступа —
            // кнопка не отображается.
            const calcBottomBtn = document.querySelector(
                '.dashboard-bottom-btn:not(.dashboard-bottom-btn-docs)');
            if (calcBottomBtn) {
                calcBottomBtn.style.display =
                    (isAll || allowed.indexOf('calculators') !== -1) ? '' : 'none';
            }
            // Task 397: ОБЕ кнопки бара скрыты (роль без калькуляторов и
            // документации — «Запрет») — скрыть ВЕСЬ бар: без кнопок он
            // висел пустой плашкой над контентом главной.
            const bottomBarEl = document.getElementById('dashboardBottomBar');
            if (bottomBarEl) {
                const barBtns = bottomBarEl.querySelectorAll('.dashboard-bottom-btn');
                let anyBarBtnVisible = false;
                barBtns.forEach(function(b) {
                    if (b.style.display !== 'none') anyBarBtnVisible = true;
                });
                bottomBarEl.style.display = anyBarBtnVisible ? '' : 'none';
            }
""", 'нижний бар: калькуляторы по доступу + композит docs упрощён + бар скрыт без кнопок')

# ============================================================
# 3. Десктоп: вкладка «Документация» верхнего бара — композит
#    упрощён до canAccess-эквивалента (та же причина, что и бар)
# ============================================================
rep(
"""                // «Документация» требует доступа к docs/library/kip-ios
                let tabAllowed;
                if (page === 'docs') {
                    tabAllowed = isAll
                        || allowed.indexOf('docs') !== -1
                        || allowed.indexOf('library') !== -1
                        || allowed.indexOf('kip-ios') !== -1;
                } else {
                    tabAllowed = isAll || allowed.indexOf(page) !== -1;
                }
""",
"""                // «Документация»: Task 397 (общее правило) — вкладка видна
                // ⟺ переход возможен (canAccess('docs')). Прежний композит
                // docs|library|kip-ios мог показывать вкладку роли, которой
                // page-docs недоступен (клик → «Нет доступа»).
                let tabAllowed;
                if (page === 'docs') {
                    tabAllowed = isAll || allowed.indexOf('docs') !== -1;
                } else {
                    tabAllowed = isAll || allowed.indexOf(page) !== -1;
                }
""", 'десктоп: вкладка «Документация» — композит упрощён до docs')

# ============================================================
# Контроль: файл изменился, маркеры на месте
# ============================================================
assert src != n0, 'файл не изменился'
for marker in [
    "Task 397 (ОБЩЕЕ ПРАВИЛО)",
    "JS_NAV_TARGETS",
    "calcBottomBtn",
    "bottomBarEl",
]:
    assert marker in src, 'маркер отсутствует: ' + marker
io.open(PATH, 'w', encoding='utf-8').write(src)
print('OK: index.html пропатчен (3 правки)')
