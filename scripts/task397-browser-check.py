#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 397: browser-check — заявка: «Примени общее правило к
# приложению, если у пользователя, согласно его роли, нет доступа
# к определённому разделу, то кнопка данного раздела не должна
# отображаться».
# Проверяется ОБЩЕЕ ПРАВИЛО на живом DOM в 6 контекстах (матрица
# getMyAccess — permissions):
#   1) «Запрет»-уровень (роль «КИП8», ВСЕ права сняты), десктоп:
#      нижний бар — inline display:none (JS-гейт; на десктопе бар
#      и так скрыт CSS ≥1024px, поэтому проверяется ИНЛАЙН-стиль),
#      ОБЕ кнопки скрыты; сайдбар без единого видимого пункта/группы;
#      на АКТИВНОЙ главной нет видимых кнопок-разделов; вкладки
#      десктопа скрыты; «Что нового» скрыто; 0 JS-ошибок;
#   2) только калькуляторы (calc.view), десктоп: «Инженерные
#      калькуляторы» — inline '' (доступ есть), «Документация» —
#      скрыта, бар inline '' (восстановлен); вкладка «Калькуляторы»
#      видна, «Документация» скрыта; группа сайдбара «КИП и А»
#      видна, «Библиотека» скрыта;
#   3) полный доступ (Админ), десктоп: обе кнопки бара inline '',
#      вкладки видны, секретные кнопки видны, «Табель» в сайдбаре;
#   4) ИТР ТОКЕМ (фильтр 4 — регресс универсального прохода):
#      «Документация» ВИДНА (docs через kipios.restricted),
#      «Кабельный журнал»/«Проекты» в сайдбаре СКРЫТЫ (фильтр 4 не
#      перебит проходом), «Приборы» виден;
#   5) мобайл 375 светлая, только калькуляторы: бар ВИДЕН (CSS grid
#      на мобиле), калькуляторы видна, документация скрыта; КЛИК по
#      калькуляторам — переход на страницу (НЕ «Нет доступа»);
#      «Что нового» скрыто;
#   6) мобайл 375, «Запрет»-уровень: бар СКРЫТ ЦЕЛИКОМ (computed
#      none — на мобиле CSS показал бы grid, скрывает только JS-гейт
#      общего правила).
# Порт 9006 (запуск: python3 -m http.server 9006 &).
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9006

PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag, perms, role='Админ'):
    """perms — словарь прав матрицы (getMyAccess); role — имя роли
    (для пустых/ограниченных контекстов — БЕЗ '*' в легаси-карте,
    чтобы серверная матрица пересобирала список страниц; Админа
    _applyServerAccess не трогает)."""
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if action == 'getCurrentUser':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': role}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': role, 'found': True,
                        'permissions': perms}}, ensure_ascii=False))
        if action == 'heartbeat':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t397-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t397-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# видимость элемента (display + hidden-атрибут)
def vis(page, sel):
    return page.evaluate(
        "(function(){var el=document.querySelector(%r);"
        "if(!el)return null;"
        "if(el.hidden)return false;"
        "return getComputedStyle(el).display!=='none';})()" % sel)

# inline-стиль display (что записал JS-гейт общего правила)
def inline(page, sel):
    return page.evaluate(
        "(function(){var el=document.querySelector(%r);"
        "return el?el.style.display:'(нет элемента)';})()" % sel)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: «Запрет»-уровень (все права сняты), десктоп ==========
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'zapret', {}, role='КИП8')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: страница загрузилась',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    check('A2: нижний бар — JS-гейт: inline display none',
          inline(page, '#dashboardBottomBar') == 'none',
          inline(page, '#dashboardBottomBar'))
    check('A3: «Инженерные калькуляторы» бара — inline none',
          inline(page, '.dashboard-bottom-btn:not(.dashboard-bottom-btn-docs)') == 'none')
    check('A4: «Документация» бара — inline none',
          inline(page, '.dashboard-bottom-btn-docs') == 'none')
    # раскрываем ВСЕ группы сайдбара (по умолчанию свёрнуты — items
    # скрыты CSS .sidebar-item-extra{display:none}, нужен честный замер)
    page.evaluate("document.querySelectorAll('.sidebar-group-title').forEach(function(t){t.click();})")
    page.wait_for_timeout(300)
    check('A5: в сайдбаре НЕТ видимых пунктов-разделов (группы раскрыты)',
          page.evaluate("(function(){var n=0;"
          "document.querySelectorAll('.sidebar-item[onclick*=\"navigateTo(\"]').forEach(function(it){"
          "if(getComputedStyle(it).display!=='none')n++;});return n;})()") == 0)
    check('A6: ВСЕ группы сайдбара скрыты',
          page.evaluate("(function(){var n=0;"
          "document.querySelectorAll('.sidebar-group').forEach(function(g){"
          "if(getComputedStyle(g).display!=='none')n++;});return n;})()") == 0)
    check('A7: на АКТИВНОЙ главной нет видимых кнопок-разделов',
          page.evaluate("(function(){var n=0;"
          "document.querySelectorAll('#page-dashboard .menu-btn').forEach(function(b){"
          "if(getComputedStyle(b).display!=='none')n++;});return n;})()") == 0)
    check('A8: вкладки десктопа «Калькуляторы»/«Документация» — скрыты',
          vis(page, '.desktop-top-bar-tab[data-page="calculators"]') is False and
          vis(page, '.desktop-top-bar-tab[data-page="docs"]') is False)
    check('A9: «Что нового» — скрыто',
          vis(page, '#desktopWhatsNewBtn') is False)
    check('A10: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='task397-proof-zapret.png', full_page=False)
    ctx.close()

    # ========== Контекст 2: только калькуляторы (calc.view), десктоп ==========
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'calc', {'calc.view': True}, role='КИП8')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('B1: «Инженерные калькуляторы» бара — inline пуст (доступ есть)',
          inline(page, '.dashboard-bottom-btn:not(.dashboard-bottom-btn-docs)') == '')
    check('B2: «Документация» бара — inline none (нет library/kipios)',
          inline(page, '.dashboard-bottom-btn-docs') == 'none')
    check('B3: нижний бар — inline пуст (восстановлен: одна кнопка жива)',
          inline(page, '#dashboardBottomBar') == '',
          inline(page, '#dashboardBottomBar'))
    check('B4: вкладка «Калькуляторы» — видна',
          vis(page, '.desktop-top-bar-tab[data-page="calculators"]') is True)
    check('B5: вкладка «Документация» — скрыта',
          vis(page, '.desktop-top-bar-tab[data-page="docs"]') is False)
    check('B6: сайдбар-группа «КИП и А» видна, «Библиотека» скрыта',
          vis(page, '.sidebar-group[data-group="kipa"]') is True and
          vis(page, '.sidebar-group[data-group="library"]') is False)
    check('B7: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========== Контекст 3: полный доступ (Админ), десктоп ==========
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    FULL = {'calc.view': True, 'library.view': True, 'kipios.view': True,
            'secret.view': True, 'whatsnew.view': True, 'charts.view': True,
            'flowmeter.view': True, 'workschedule.view': True,
            'workschedule.edit': True, 'admin.panel': True}
    js_errors = attach(page, ctx, 'dark', 'admin', FULL, role='Админ')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('C1: обе кнопки нижнего бара — inline пуст',
          inline(page, '.dashboard-bottom-btn:not(.dashboard-bottom-btn-docs)') == '' and
          inline(page, '.dashboard-bottom-btn-docs') == '')
    check('C2: бар — inline пуст', inline(page, '#dashboardBottomBar') == '')
    check('C3: вкладки «Калькуляторы» и «Документация» видны',
          vis(page, '.desktop-top-bar-tab[data-page="calculators"]') is True and
          vis(page, '.desktop-top-bar-tab[data-page="docs"]') is True)
    # секретные кнопки: по умолчанию display:none (CSS .menu-btn-secret),
    # открываются 2 тапами по заголовку. Десктоп: desktopBrandBtn —
    # двойной тап вызывает secretTapHandler ОДИН раз (внутренний счётчик
    # до 2), поэтому эмулируем ДВА двойных тапа (4 click-события)
    page.evaluate("(function(){var b=document.getElementById('desktopBrandBtn')||"
                  "document.querySelector('.header-title');"
                  "if(b){for(var i=0;i<4;i++)b.dispatchEvent(new Event('click'));}})()")
    page.wait_for_timeout(400)
    check('C4: секретные кнопки «Сапёр»/«Справочник» видны (после 2 тапов)',
          vis(page, '#minesweeperBtn') is True and vis(page, '#phonebookBtn') is True)
    page.evaluate("(function(){var g=document.querySelector('.sidebar-group[data-group=\\'docs-ios\\']');"
                  "if(g){var t=g.querySelector('.sidebar-group-title');if(t)t.click();}})()")
    page.wait_for_timeout(300)
    check('C5: «Табель» в сайдбаре виден (группа раскрыта)',
          vis(page, '#sidebarWorkScheduleBtn') is True)
    check('C6: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='task397-proof-admin.png', full_page=False)
    ctx.close()

    # ========== Контекст 4: ИТР ТОКЕМ (фильтр 4 — регресс прохода) ==========
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    TOKEM = {'calc.view': True, 'kipios.restricted': True, 'whatsnew.view': True}
    js_errors = attach(page, ctx, 'dark', 'tokem', TOKEM, role='ИТР ТОКЕМ')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('D1: «Документация» нижнего бара — inline пуст (docs через kipios.restricted)',
          inline(page, '.dashboard-bottom-btn-docs') == '')
    page.evaluate("(function(){var g=document.querySelector('.sidebar-group[data-group=\\'kip-ios\\']');"
                  "if(g){var t=g.querySelector('.sidebar-group-title');if(t)t.click();}})()")
    page.wait_for_timeout(300)
    check('D2: сайдбар «Кабельный журнал»/«Проекты» — СКРЫТЫ (фильтр 4 не перебит; группа раскрыта)',
          page.evaluate("(function(){var out=[];"
          "document.querySelectorAll('.sidebar-item').forEach(function(it){"
          "var oc=it.getAttribute('onclick')||'';"
          "if(oc.indexOf('cable-journal-edit')!==-1||oc.indexOf('projects-prod')!==-1){"
          "out.push(getComputedStyle(it).display!=='none');}});"
          "return out.length===2&&out[0]===false&&out[1]===false;})()"))
    check('D3: сайдбар «Приборы» — виден (КИП ИОС с ограничениями; группа раскрыта)',
          page.evaluate("(function(){var ok=false;"
          "document.querySelectorAll('.sidebar-item').forEach(function(it){"
          "if((it.getAttribute('onclick')||'').indexOf(\"navigateTo('devices-prod')\")!==-1)"
          "ok=getComputedStyle(it).display!=='none';});return ok;})()"))
    check('D4: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========== Контекст 5: мобайл 375 светлая, только калькуляторы ==========
    ctx = browser.new_context(viewport={'width': 375, 'height': 700})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mcalc', {'calc.view': True}, role='КИП8')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('E1: мобайл: нижний бар ВИДЕН (CSS grid; одна кнопка жива)',
          vis(page, '#dashboardBottomBar') is True,
          vis(page, '#dashboardBottomBar'))
    check('E2: мобайл: «Инженерные калькуляторы» — ВИДНА',
          vis(page, '.dashboard-bottom-btn:not(.dashboard-bottom-btn-docs)') is True and
          page.evaluate("(function(){var b=document.querySelector('.dashboard-bottom-btn:not(.dashboard-bottom-btn-docs)');"
                        "return b?b.getBoundingClientRect().width>0:false;})()"))
    check('E3: мобайл: «Документация» — скрыта',
          vis(page, '.dashboard-bottom-btn-docs') is False)
    check('E4: мобайл: «Что нового» (шапка) — скрыто',
          vis(page, '#mobileWhatsNewBtn') is False)
    page.screenshot(path='task397-proof-mobile.png', full_page=False)
    # клик по кнопке калькуляторов — переход РАБОТАЕТ (не «Нет доступа»)
    page.click('.dashboard-bottom-btn:not(.dashboard-bottom-btn-docs) span', timeout=10000)
    page.wait_for_timeout(600)
    check('E5: клик «Инженерные калькуляторы» — переход на страницу (не «Нет доступа»)',
          page.evaluate("document.querySelector('#page-calculators').classList.contains('active')") is True
          and page.evaluate("var s=document.getElementById('noAccessScreen');!s||getComputedStyle(s).display==='none'"))
    page.screenshot(path='task397-proof-mobile-click.png', full_page=False)
    check('E6: мобайл: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========== Контекст 6: мобайл 375, «Запрет»-уровень ==========
    ctx = browser.new_context(viewport={'width': 375, 'height': 700})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mzapret', {}, role='КИП8')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('F1: мобайл «Запрет»: нижний бар СКРЫТ ЦЕЛИКОМ (computed none)',
          vis(page, '#dashboardBottomBar') is False,
          vis(page, '#dashboardBottomBar'))
    check('F2: мобайл «Запрет»: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print('ИТОГ: %d/%d' % (PASS, PASS + FAIL))
raise SystemExit(0 if FAIL == 0 else 1)
