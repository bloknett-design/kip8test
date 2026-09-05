# -*- coding: utf-8 -*-
# BUG REPORT (заявка пользователя): «не открываются некоторые разделы
# и полные карточки расходомеров».
# Репродукция: мок Apps Script + реальный fallback data/flowmeters.json,
# прогон по ВСЕМ разделам приложения + клик по КАЖДОЙ карточке
# расходомера (десктоп: detail-панель; мобайл: полная страница).
# Собираем JS-ошибки, ошибки консоли и результаты открытия.
import json
import sys
from playwright.sync_api import sync_playwright

PORT = 8945
BASE = 'http://127.0.0.1:%d/index.html' % PORT

FALLBACK = json.load(open('/home/z/my-project/kip8test/data/flowmeters.json', encoding='utf-8'))
METERS = FALLBACK['meters']

RESULTS = []
JS_ERRORS = []
CONSOLE_ERRORS = []

PERMS = {
    'calc.view': True, 'library.view': True, 'kipios.view': True,
    'kipios.restricted': True, 'secret.view': True, 'whatsnew.view': True,
    'charts.view': True, 'flowmeter.view': True, 'flowmeter.input': True,
    'workschedule.view': True,
}

ARCHIVE_RECORDS = [
    {'id': 101, 'prev': 90.11, 'curr': 91.11, 'unit': 'т', 'gcal': 60.46,
     'date': '8/20/2026', 'modRole': 'Админ', 'modName': 'mobile_test',
     'timestamp': '2026-08-20T09:00:00.000Z', 'type': 'сутки', 'comment': ''},
    {'id': 100, 'prev': 89.5, 'curr': 90.11, 'unit': 'т', 'gcal': 60.1,
     'date': '8/19/2026', 'modRole': 'Админ', 'modName': 'mobile_test',
     'timestamp': '2026-08-19T09:00:00.000Z', 'type': 'сутки', 'comment': ''},
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'role': 'Админ', 'email': 'qa@local.test', 'userId': 1}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'found': True, 'role': 'Админ', 'permissions': PERMS}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': METERS}}
    if action == 'flowmeter.archive':
        return {'ok': True, 'data': {'records': ARCHIVE_RECORDS, 'anomalyHelp': {}}}
    if action == 'flowmeter.getValidationRules':
        return {'ok': True, 'data': {'rules': []}}
    if action == 'flowmeter.getValidationHelp':
        return {'ok': True, 'data': {'anomalyHelp': {}}}
    # workSchedule (чтобы init не падал)
    if action == 'workSchedule.getCodes':
        return {'ok': True, 'data': {'codes': [
            {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
            {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
            {'code': '.', 'name': 'Плановый выходной', 'color': '#EEF0F2'},
        ]}}
    if action == 'workSchedule.getEmployees':
        return {'ok': True, 'data': {'employees': []}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    return {'ok': False, 'error': 'unknown action ' + str(action)}

def setup_routes(ctx):
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            from urllib.parse import unquote
            action = unquote(action)
        resp = mock_response(action, None)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

def log(name, ok, detail=''):
    RESULTS.append((name, ok, detail))
    print(('  OK  ' if ok else ' FAIL ') + name + ((' — ' + detail) if detail else ''))

def check_sections(page, label):
    print('== Разделы (%s) ==' % label)
    # (page-id, проверка активности страницы)
    sections = ['docs', 'kip-ios', 'docs-ios', 'devices-prod', 'lockouts-prod',
                'valves-prod', 'regulators-prod', 'projects-prod',
                'cable-journal-edit', 'flowmeter-data', 'work-schedule',
                'exam-tickets', 'whats-new', 'library', 'calculators']
    for sec in sections:
        try:
            page.evaluate("navigateTo('%s')" % sec)
            page.wait_for_timeout(450)
            active = page.evaluate('''(() => {
                const el = document.getElementById('page-%s');
                return el ? el.classList.contains('active') : null;
            })()''' % sec)
            log('%s → page-%s.active' % (label, sec), bool(active),
                'active=%s' % active)
        except Exception as e:
            log('%s → page-%s' % (label, sec), False, 'EXC: %s' % e)

def check_flowmeter_cards(page, label, desktop):
    print('== Карточки расходомеров (%s) ==' % label)
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1200)
    n = page.evaluate("document.querySelectorAll('#flowList .flow-card').length")
    log('%s: карточек в списке' % label, n == len(METERS), 'найдено %d (ожидалось %d)' % (n, len(METERS)))
    for m in METERS:
        mid = m['id']
        try:
            clicked = page.evaluate('''(() => {
                const card = document.querySelector('#flowList .flow-card[data-flow-id="%s"]');
                if (!card) return 'no-card';
                card.querySelector('.flow-card-header').click();
                return 'ok';
            })()''' % mid)
            page.wait_for_timeout(350)
            if desktop:
                state = page.evaluate('''(() => {
                    const panel = document.getElementById('detailPanel');
                    const body = document.getElementById('detailPanelBody');
                    const title = document.getElementById('detailPanelTitle');
                    return {
                        active: panel ? panel.classList.contains('active') : false,
                        len: body ? body.innerHTML.length : 0,
                        title: title ? title.textContent : '',
                        visible: panel ? (panel.offsetWidth > 0 && panel.offsetHeight > 0) : false,
                    };
                })()''')
                okk = state['active'] and state['len'] > 100 and state['visible']
                log('%s: карточка id=%s (%s)' % (label, mid, m['hoz'][:30]), okk,
                    'active=%s len=%s title="%s" clicked=%s' % (state['active'], state['len'], state['title'][:40], clicked))
            else:
                state = page.evaluate('''(() => {
                    const pg = document.getElementById('page-flowmeter-detail');
                    const body = document.getElementById('flowDetailBody');
                    return {
                        active: pg ? pg.classList.contains('active') : false,
                        len: body ? body.innerHTML.length : 0,
                        visible: pg ? (pg.offsetWidth > 0 && pg.offsetHeight > 0) : false,
                    };
                })()''')
                okk = state['active'] and state['len'] > 100 and state['visible']
                log('%s: карточка id=%s (%s)' % (label, mid, m['hoz'][:30]), okk,
                    'active=%s len=%s clicked=%s' % (state['active'], state['len'], clicked))
            # вернуться к списку
            if desktop:
                page.evaluate("closeDetailPanel && closeDetailPanel()")
            else:
                page.evaluate("navigateTo('flowmeter-data')")
            page.wait_for_timeout(250)
        except Exception as e:
            log('%s: карточка id=%s' % (label, mid), False, 'EXC: %s' % e)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------- DESKTOP ----------
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        setup_routes(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: JS_ERRORS.append(('desktop', str(e))))
        page.on('console', lambda m: CONSOLE_ERRORS.append(('desktop', m.text)) if m.type == 'error' else None)
        page.goto(BASE)
        page.evaluate("localStorage.setItem('kip8_session_token','bug326-token')")
        page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
        page.evaluate("localStorage.setItem('kip8_cached_email','qa@local.test')")
        page.reload()
        page.wait_for_timeout(3000)
        check_sections(page, 'desktop')
        check_flowmeter_cards(page, 'desktop', True)
        ctx.close()

        # ---------- MOBILE ----------
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 812},
                                   is_mobile=True, has_touch=True,
                                   user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Mobile Safari/537.36')
        setup_routes(ctx2)
        page2 = ctx2.new_page()
        page2.on('pageerror', lambda e: JS_ERRORS.append(('mobile', str(e))))
        page2.on('console', lambda m: CONSOLE_ERRORS.append(('mobile', m.text)) if m.type == 'error' else None)
        page2.goto(BASE)
        page2.evaluate("localStorage.setItem('kip8_session_token','bug326-token')")
        page2.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
        page2.evaluate("localStorage.setItem('kip8_cached_email','qa@local.test')")
        page2.reload()
        page2.wait_for_timeout(3000)
        check_flowmeter_cards(page2, 'mobile', False)
        ctx2.close()
        browser.close()

    print('\n===== ИТОГИ =====')
    fails = [r for r in RESULTS if not r[1]]
    print('Всего проверок: %d, FAIL: %d' % (len(RESULTS), len(fails)))
    for f in fails:
        print('  FAIL: %s — %s' % (f[0], f[2]))
    print('\n===== JS ERRORS (%d) =====' % len(JS_ERRORS))
    for e in JS_ERRORS[:20]:
        print('  [%s] %s' % (e[0], e[1][:300]))
    print('\n===== CONSOLE ERRERS (%d) =====' % len(CONSOLE_ERRORS))
    for e in CONSOLE_ERRORS[:30]:
        print('  [%s] %s' % (e[0], e[1][:300]))
    return 1 if fails or JS_ERRORS else 0

if __name__ == '__main__':
    sys.exit(run())
