#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 369: browser-check — заявка пользователя:
#   «В разделе КИП ИОС, сделай при свайпе кнопки "Проекты" (по такому же
#    принципу как на кнопках "Приборы" и "Клапана") открывался список
#    проектов сгруппированный по столбцу Статус проекта.»
# Контексты:
#   1. десктоп 1280 тёмная, Админ: кнопка «Проекты» в свайп-ячейке с
#      двумя подложками «По статусу»; СВАЙП ВЛЕВО → «Проекты по статусу»
#      (порядок групп Новый → Выполнен → Остановлен → Отменен →
#      Действующий → (без статуса), счётчики); группа «Выполнен» →
#      project-group с годами; возврат, ТАП → «По отделениям»;
#      СВАЙП ВПРАВО → тоже «По статусу»; поиск сужает список.
#   2. светлая тема: подложка видна во время свайпа (opacity 1,
#      янтарный градиент), недоведённый свайп возвращает карточку.
#   3. мобайл 375: свайп работает, список читается.
# + 0 JS-ошибок; скриншот-пруфы.
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8968

# Мок data/projects.json — все известные статусы + неизвестный + пустой
def proj(pid, name, num, status, dep, date):
    return {'ID': str(pid), '№': str(pid), 'Наименование проекта': name,
            '№ проекта': num, 'Файл проекта': '', 'Дата утв.': date,
            'Отделение': dep, 'Статус проекта': status, 'Данные статуса': '',
            'Примечание': '', 'Жёлтым отмечены приоритетные проекты': ''}

MOCK_PROJECTS = {
    'projects': [
        proj(1, 'Реконструкция котельной', 'П-101', 'Выполнен', 'ТЭЦ', '2020-01-15'),
        proj(2, 'Насосная станция №2', 'П-102', 'Новый', 'ТЭЦ', '2023-05-05'),
        proj(3, 'Вентиляция корпуса 114', 'П-103', 'Выполнен', 'КО', '2019-02-02'),
        proj(4, 'Азотная станция', 'П-104', 'Остановлен', 'КО', '2021-03-03'),
        proj(5, 'Реконструкция ВОК', 'П-105', 'Новый', 'ВОК', '2022-02-02'),
        proj(6, 'Склад реагентов', 'П-106', 'Отменен', 'ВОК', '2018-04-04'),
        proj(7, 'Кислородная станция', 'П-107', 'Выполнен', 'ТЭЦ', '2024-01-01'),
        proj(8, 'Паропровод корпуса 116', 'П-108', 'Действующий', 'КО', '2024-06-06'),
        proj(9, 'Старый проект без статуса', 'П-109', '', 'КОС', '2015-07-07'),
    ]
}

STATE = {'role': 'Админ'}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': STATE['role']}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': STATE['role'], 'found': True,
                'permissions': {'kipios.view': True, 'flowmeter.view': True,
                                 'workschedule.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

ACTIVE_PAGE = "(function(){var a=document.querySelector('.page-content.active');" \
              "return a?a.id.replace('page-',''):null;})()"

def swipe(page, selector, direction):
    """Свайп карточки: direction=-1 влево, +1 вправо (50% ширины)."""
    box = page.locator(selector).bounding_box()
    cx = box['x'] + box['width'] / 2
    cy = box['y'] + box['height'] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    target = cx + direction * box['width'] * 0.5
    for i in range(1, 11):
        page.mouse.move(cx + direction * (target - cx) * i / 10.0, cy)
    page.mouse.up()

GROUP_TITLES = ("function(){return Array.from(document.querySelectorAll(" \
    "'.page-content.active .project-sorted-list .pb-section-title-text')).map(function(e){return e.textContent;});}()")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if '/data/projects.json' in url:
            route.fulfill(status=200, content_type='application/json; charset=utf-8',
                           body=json.dumps(MOCK_PROJECTS, ensure_ascii=False).encode('utf-8'))
            return
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**/data/projects.json**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t369)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t369-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    # --- КИП ИОС: кнопка в свайп-ячейке ---
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(600)
    check('B: кнопка «Проекты» внутри свайп-ячейки #projectSwipeCell',
          page.evaluate("(function(){var b=document.getElementById('projectsEntryBtn');" \
                       "return !!b && !!b.closest('#projectSwipeCell');})()"))
    check('C: две подложки «По статусу» (лево/право)',
          page.evaluate("Array.from(document.querySelectorAll(" \
              "'#projectSwipeCell .dev-swipe-bg span')).map(function(e){return e.textContent;})" \
              ".join('|')") == 'По статусу|По статусу')

    # --- СВАЙП ВЛЕВО → «Проекты по статусу» ---
    swipe(page, '#projectsEntryBtn', -1)
    page.wait_for_timeout(700)
    check('D: свайп влево → открылась страница projects-status',
          page.evaluate(ACTIVE_PAGE) == 'projects-status', page.evaluate(ACTIVE_PAGE))
    check('E: заголовок «Проекты по статусу» (хлебные крошки)',
          page.evaluate("document.querySelector('#page-projects-status " \
              ".page-inline-header-title').textContent.trim().endsWith('Проекты по статусу')"))
    page.wait_for_timeout(800)
    titles = page.evaluate(GROUP_TITLES)
    check('F: порядок групп (Новый → Выполнен → Остановлен → Отменен → Действующий → без статуса)',
          titles == ['Новый', 'Выполнен', 'Остановлен', 'Отменен', 'Действующий', '(без статуса)'],
          str(titles))
    counts = page.evaluate("Array.from(document.querySelectorAll(" \
        "'.page-content.active .project-sorted-list .pb-section-title-count')).map(function(e){return e.textContent;})")
    check('G: счётчики групп 2/3/1/1/1/1', counts == ['2', '3', '1', '1', '1', '1'], str(counts))
    page.screenshot(path='scripts/task369-proof-desktop.png')

    # --- группа «Выполнен» → project-group с годами ---
    page.evaluate("var t=Array.from(document.querySelectorAll(" \
        "'.project-sorted-list .pb-section-title')).filter(function(e){return " \
        "e.textContent.indexOf('Выполнен')===0;})[0]; t.dispatchEvent(new Event('click',{bubbles:true}))")
    page.wait_for_timeout(600)
    check('H: группа «Выполнен» → страница project-group',
          page.evaluate(ACTIVE_PAGE) == 'project-group', page.evaluate(ACTIVE_PAGE))
    check('I: заголовок группы = «Выполнен» (крошки)',
          page.evaluate("document.getElementById('projectGroupTitle').textContent.trim().endsWith('Выполнен')"))
    check('J: в группе 3 карточки Выполнен',
          page.evaluate("document.querySelectorAll('#projectGroupList .project-card').length") == 3)
    check('K: подгруппы-годы внутри статуса (2019/2020/2024)',
          sorted(page.evaluate("Array.from(document.querySelectorAll(" \
              "'#projectGroupList .pb-section-title-text'))" \
              ".map(function(e){return e.textContent;})")) == ['2019', '2020', '2024'])

    # --- возврат: ТАП → «По отделениям» (не сломано) ---
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(500)
    page.click('#projectsEntryBtn')
    page.wait_for_timeout(600)
    check('L: тап без свайпа → projects-prod (как раньше)',
          page.evaluate(ACTIVE_PAGE) == 'projects-prod', page.evaluate(ACTIVE_PAGE))
    prod_titles = page.evaluate(GROUP_TITLES)
    check('M: «По отделениям» — группы по отделениям (КО/ВОК/ТЭЦ/КОС)',
          set(prod_titles) == {'КО', 'ВОК', 'ТЭЦ', 'КОС'}, str(prod_titles))

    # --- СВАЙП ВПРАВО → тоже «По статусу» ---
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(500)
    swipe(page, '#projectsEntryBtn', +1)
    page.wait_for_timeout(700)
    check('N: свайп вправо → тоже projects-status',
          page.evaluate(ACTIVE_PAGE) == 'projects-status', page.evaluate(ACTIVE_PAGE))

    # --- поиск сужает список ---
    page.evaluate("var i=document.getElementById('projectStatusSearchInput');" \
                 "i.hidden=false; i.value='Насосная';" \
                 "i.dispatchEvent(new Event('input',{bubbles:true}))")
    page.wait_for_timeout(400)
    check('O: поиск «Насосная» — 1 карточка в группе «Новый»',
          page.evaluate("document.querySelectorAll(" \
              "'#page-projects-status .project-card').length") == 1 and
          page.evaluate("document.querySelector(" \
              "'#page-projects-status .project-card-title').textContent") == 'Насосная станция №2')
    check('P: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая — подложка во время свайпа =================
    ctx3 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    page3.on('dialog', lambda d: d.accept())
    ctx3.route('**/exec?**', handle)
    ctx3.route('**script.google.com/**', handle)
    ctx3.route('**/data/projects.json**', handle)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)
    ctx3.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t369-c');" +
        "localStorage.setItem('kip8test:app-theme','light');")
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('kip-ios')")
    page3.wait_for_timeout(600)

    box = page3.locator('#projectsEntryBtn').bounding_box()
    cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
    page3.mouse.move(cx, cy)
    page3.mouse.down()
    for i in range(1, 11):
        page3.mouse.move(cx - box['width'] * 0.35 * i / 10.0, cy)
    page3.wait_for_timeout(250)
    check('Q: светлая — ячейка в состоянии swiping-left (карточка сдвинута)',
          page3.evaluate("document.getElementById('projectSwipeCell').classList.contains('swiping-left')"))
    under = page3.evaluate("(function(){var b=document.querySelector(" \
        "'#projectSwipeCell .dev-swipe-bg-right'); var s=getComputedStyle(b);" \
        "return {opacity: s.opacity, bg: s.backgroundImage};})()")
    check('R: светлая — правая подложка ВИДИМА (opacity 1)',
          under['opacity'] == '1', str(under))
    check('S: светлая — янтарный градиент подложки (rgba(156,108,52))',
          '156, 108, 52' in under['bg'] and '176, 128, 72' in under['bg'], str(under['bg']))
    page3.screenshot(path='scripts/task369-proof-swipe-light.png')
    # Недоведённый свайп: возвращаем карточку на место
    for i in range(1, 11):
        page3.mouse.move(cx - box['width'] * 0.35 * (10 - i) / 10.0, cy)
    page3.mouse.up()
    page3.wait_for_timeout(500)
    check('T: недоведённый свайп — карточка вернулась, перехода НЕТ',
          page3.evaluate(ACTIVE_PAGE) == 'kip-ios' and
          page3.evaluate("(function(){var b=document.getElementById('projectsEntryBtn');" \
                        "return b.style.transform;})()") in ('', 'none'))
    # Отступ ячейки не ломает вёрстку строки: зазор до следующей строки = 6px
    gap = page3.evaluate("(function(){var p=document.getElementById('projectSwipeCell');" \
        "var r=p.getBoundingClientRect(); var n=document.querySelector(" \
        "'#page-kip-ios > .menu-btn-row + .menu-btn-row');" \
        "var nr=n.getBoundingClientRect(); return Math.round(nr.top - r.bottom);})()")
    check('U: зазор до следующей строки — 6px (как до Task 369)', gap == 6, gap)
    check('V: 0 JS-ошибок (светлая)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 3: мобайл 375 =================
    ctx4 = browser.new_context(viewport={'width': 375, 'height': 700})
    page4 = ctx4.new_page()
    js_errors4 = []
    page4.on('pageerror', lambda e: js_errors4.append(str(e)))
    page4.on('dialog', lambda d: d.accept())
    ctx4.route('**/exec?**', handle)
    ctx4.route('**script.google.com/**', handle)
    ctx4.route('**/data/projects.json**', handle)
    ctx4.route('**raw.githubusercontent.com/**', block_external)
    ctx4.route('**calendar.legalic.ru/**', block_external)
    ctx4.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t369-m');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page4.goto('http://localhost:%d/index.html' % PORT)
    page4.wait_for_timeout(2500)
    page4.evaluate("navigateTo('kip-ios')")
    page4.wait_for_timeout(600)
    check('W: мобайл — кнопка в ячейке, подложки на месте',
          page4.evaluate("document.querySelectorAll(" \
              "'#projectSwipeCell .dev-swipe-bg').length") == 2)
    swipe(page4, '#projectsEntryBtn', -1)
    page4.wait_for_timeout(700)
    check('X: мобайл — свайп влево → projects-status',
          page4.evaluate(ACTIVE_PAGE) == 'projects-status', page4.evaluate(ACTIVE_PAGE))
    page4.wait_for_timeout(800)
    m_titles = page4.evaluate(GROUP_TITLES)
    check('Y: мобайл — все 6 групп читаются',
          m_titles == ['Новый', 'Выполнен', 'Остановлен', 'Отменен', 'Действующий', '(без статуса)'],
          str(m_titles))
    page4.screenshot(path='scripts/task369-proof-mobile.png')
    check('Z: 0 JS-ошибок (мобайл)', len(js_errors4) == 0, js_errors4[:3])
    ctx4.close()

    browser.close()

print('\nИтог: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
