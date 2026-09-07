# -*- coding: utf-8 -*-
# Task 335 probe: измерить зазор между верхним баром и блоком
# картинка+№+Место в мобильной карточке прибора (до правок).
import json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8937
Y, M = datetime.date.today().year, datetime.date.today().month

DEVICES = [
  {'ID':'100','Наименование':'Термометр сопротивления ТСП-100П','Тип':'КИПиА','№ прибора':'ТСП-001','Место установки':'Цех №1, трубопровод пара','Раздел':'Тепло','Заводской №':'Z-100','Дата поверки':'2026-05-01','Замечания':'','Ед. изм.':'°C','Диапазон':'0…150','Класс точности':'B','Год выпуска':'2023','Изготовитель':'Элемер','Схема':'','Примечание':''},
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'kip.view':True,'kip.edit':True,'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'getDevices':
        return {'ok':True,'data':{'devices':DEVICES}}
    return {'ok':True,'data':{'ok':True}}

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width':375,'height':720})
    page = ctx.new_page()
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, body), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','probe-t335')")
    page.reload()
    page.wait_for_timeout(2500)

    # перейти в КИПиА (список приборов) и открыть карточку
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(1500)
    info = page.evaluate("""(function(){
        var act = document.querySelector('.page-content.active');
        return {page: act ? act.id : null,
                cards: document.querySelectorAll('.dev-card, [class*="card"]').length};
    })()""")
    print('page:', info)
    # клик по первой карточке прибора
    page.evaluate("devOpenDetail('100')")
    page.wait_for_timeout(1200)
    m = page.evaluate("""(function(){
        var page = document.getElementById('page-device-detail');
        var head = page ? page.querySelector('.page-inline-header') : null;
        var top = page ? page.querySelector('.dev-detail-top') : null;
        var card = page ? page.querySelector('.dev-detail-card') : null;
        var content = document.getElementById('deviceDetailContent');
        if (!head || !top) return {err:'no elements'};
        var hb = head.getBoundingClientRect();
        var tb = top.getBoundingClientRect();
        var cb = card ? card.getBoundingClientRect() : null;
        var ctb = content ? content.getBoundingClientRect() : null;
        var st = getComputedStyle(top);
        return {
            headerBottom: hb.bottom, topBlockTop: tb.top,
            gap: tb.top - hb.bottom,
            cardTop: cb ? cb.top : null, cardGap: cb ? (cb.top - hb.bottom) : null,
            contentGap: ctb ? (ctb.top - hb.bottom) : null,
            contentPadTop: content ? getComputedStyle(content).paddingTop : null,
            contentMarginTop: content ? getComputedStyle(content).marginTop : null,
            cardMargin: card ? getComputedStyle(card).marginTop : null,
            topSticky: st.position, topTop: st.top,
            active: page.classList.contains('active'),
            bodyScrollY: window.scrollY
        };
    })()""")
    print(json.dumps(m, ensure_ascii=False, indent=1))
    page.screenshot(path='t335-probe-card-top.png')
    browser.close()
