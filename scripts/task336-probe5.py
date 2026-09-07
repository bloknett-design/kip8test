# -*- coding: utf-8 -*-
# Task 336 probe-5: решающий эксперимент — варианты выравнивания
# блока в десктоп-панели на РЕАЛЬНОМ рендере:
#   A) padding-top:0 на .detail-panel-body (:has) + margin-top:0;
#   B) padding-top:0 + margin-top:-16 (как сейчас);
#   C) текущее состояние (контроль).
import json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
DEVICES = [
  {'ID':'100','Наименование':'Термометр ТСП-100П','Тип':'КИПиА','№ прибора':'ТСП-001','Место установки':'Цех №1','Раздел':'Тепло','Заводской №':'Z-100','Дата поверки':'2026-05-01','Замечания':'','Ед. изм.':'°C','Диапазон':'0…150','Класс точности':'B','Год выпуска':'2023','Изготовитель':'Элемер','Схема':'','Примечание':''},
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'kip.view':True,'kip.edit':True,'workschedule.view':True}}}
    if action == 'getDevices':
        return {'ok':True,'data':{'devices':DEVICES}}
    return {'ok':True,'data':{'ok':True}}

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width':1440,'height':900})
    page = ctx.new_page()
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(status=404, body='x'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(status=404, body='x'))
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','probe-t336-d5')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.reload(); page.wait_for_timeout(2500)

    page.evaluate("navigateTo('kip-ios')"); page.wait_for_timeout(1500)
    page.evaluate("devOpenDetail('100')"); page.wait_for_timeout(1200)

    def measure(label):
        r = page.evaluate("""(function(){
            var body = document.getElementById('detailPanelBody');
            var bar = document.getElementById('detailBreadcrumbBar');
            var top = body.querySelector('.dev-detail-top');
            var brb = bar.getBoundingClientRect().top + bar.getBoundingClientRect().height;
            var out = { gap0: top.getBoundingClientRect().top - brb };
            body.scrollTop = 600;
            out.gapSc = top.getBoundingClientRect().top - brb;
            out.scrolled = body.scrollTop;
            body.scrollTop = 0;
            return out;
        })()""")
        print(label, json.dumps(r, ensure_ascii=False))
        return r

    measure('C (контроль):        ')
    # A: padding-top:0 + margin-top:0
    page.evaluate("""(function(){
        var body = document.getElementById('detailPanelBody');
        var top = body.querySelector('.dev-detail-top');
        body.style.paddingTop = '0px';
        top.style.marginTop = '0px';
    })()""")
    measure('A (pad0+margin0):    ')
    # B: padding-top:0 + margin-top:-16
    page.evaluate("""(function(){
        var top = document.getElementById('detailPanelBody').querySelector('.dev-detail-top');
        top.style.marginTop = '-16px';
    })()""")
    measure('B (pad0+margin-16):  ')
    page.screenshot(path='scripts/task336-probe-d-variantA.png')
    # откат
    page.evaluate("""(function(){
        var body = document.getElementById('detailPanelBody');
        var top = body.querySelector('.dev-detail-top');
        body.style.paddingTop = '';
        top.style.marginTop = '';
    })()""")
    ctx.close(); browser.close()
print('DONE')
