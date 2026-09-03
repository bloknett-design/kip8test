# -*- coding: utf-8 -*-
# Task 298: browser-check «График работы» — новые коды статусов.
# Playwright + мок fetch (перехват POST к Apps Script по action).
import json, sys, time
from playwright.sync_api import sync_playwright

BASE = 'https://localhost.invalid/exec'  # не используется — мок по URL-паттерну
WS_URL = 'https://script.google.com/macros/s/AKfycbyt2sjbJ8xT5UPKDlYj4q-CV-5pH_Yrv5COrg0PIpp92snpQULUNtJC__pMnQ0h6feNlA/exec'

CODES = [
  {'code':'Д','name':'День, плановая дневная 12-часовая смена (7:30–19:30)','color':'#FFE082'},
  {'code':'Д8','name':'День, плановая дневная 8-часовая смена (7:30–16:30)','color':'#FFF9C4'},
  {'code':'Д7,2','name':'День, плановая дневная 7,2-часовая смена (пятница/предпраздничный)','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь, плановая ночная 12-часовая смена (19:30–7:30)','color':'#B0BEC5'},
  {'code':'д','name':'День, работа в выходные и нерабочие праздничные дни','color':'#FFD54F'},
  {'code':'н','name':'Ночь, работа в выходные и нерабочие праздничные дни','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск, ежегодный основной оплачиваемый','color':'#ECEFF1'},
  {'code':'У','name':'Учебный отпуск, с сохранением среднего заработка','color':'#80CBC4'},
  {'code':'ОВ','name':'Отгул, дополнительные выходные дни (оплачиваемые)','color':'#C5E1A5'},
  {'code':'Б','name':'Больничный, временная нетрудоспособность с назначением пособия','color':'#F8BBD0'},
  {'code':'ПР','name':'Прогул (отсутствие без уважительных причин)','color':'#EF5350'},
  {'code':'И','name':'Инструктаж, повторные по охране труда и промбезопасности','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение, по охране труда и промышленной безопасности','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний, по охране труда и промбезопасности, до 1000В, на допуск к самостоятельной работе','color':'#FFCDD2'},
  {'code':'*','name':'Примечание, не плановые случаи (аварийные работы, принят, уволен), с обязательным комментированием','color':'#FFAB91'},
  {'code':'.','name':'Плановый выходной день','color':'#CFD8DC'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов И. И.','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА смена №1','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров П. П.','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА дневной','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный 5-дневный','cycle':5,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''},{'day':5,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Д'},{'day':3,'status':'Д'},{'day':4,'status':'Д'},{'day':5,'status':'Д'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'дата':'2026-09-01','таб_номер':'017','статус':'Д','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-02','таб_номер':'017','статус':'Н','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-03','таб_номер':'023','статус':'Д8','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-06','таб_номер':'017','статус':'д','переработка':1,'праздник':0,'источник':'руч','дата_обновления':'2026-09-06T10:00:00Z','замещает':None,'инструкция':None,'комментарий':'12 ч'},
  {'дата':'2026-09-10','таб_номер':'023','статус':'.','переработка':0,'праздник':0,'источник':'руч','дата_обновления':'2026-09-10T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''}
]
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':2,'дата_начала':'2026-09-14','дата_окончания':'2026-09-20','комментарий':''}
]

def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'admin@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','perms':{'admin.panel':True,'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True,'flowmeter.input':True}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':[]}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width':375,'height':720})  # мобильный
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
        try:
            from urllib.parse import unquote
            action = unquote(action)
        except Exception:
            pass
        body = json.dumps(mock_response(action), ensure_ascii=False)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=body.encode('utf-8') if isinstance(body, str) else body)
    ctx.route('**/exec?**', handle)
    # также все прочие запросы к script.google.com
    ctx.route('**script.google.com/**', handle)

    page.goto('http://localhost:8925/index.html')
    # сессионный токен (без префикса kip8test: — общий ключ)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t298')")
    page.reload()
    page.wait_for_timeout(2500)

    # 1. Страница загрузилась без ошибок
    check('A: страница загрузилась, дашборд активен', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # 2. Переход на График работы
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    grid = page.evaluate("document.querySelector('#wsGridWrap table')")
    check('B: шахматка отрисована', grid is not None)

    # 3. Ячейки с новыми кодами: Д8 и «.» и «д»
    cells_text = page.evaluate("Array.from(document.querySelectorAll('#wsGridWrap td.ws-cell')).map(td=>td.textContent.trim())")
    check('C: ячейка «Д8» отрисована (запись дневного)', 'Д8' in cells_text)
    check('D: ячейка «.» (плановый выходной) отрисована', '.' in cells_text)
    check('E: ячейка «д» (работа в выходной, строчная) отрисована', 'д' in cells_text)
    check('F: маркер переработки у «д» (ws-overtime)', page.evaluate("!!document.querySelector('#wsGridWrap td.ws-cell.ws-overtime')"))

    # 4. План отпуска в пустых ячейках: буква «ОТ»
    vac_cells = page.evaluate("Array.from(document.querySelectorAll('#wsGridWrap td.ws-cell.ws-vac-plan')).map(td=>td.textContent.trim())")
    check('G: пустые ячейки плана отпуска показывают «ОТ»', len(vac_cells) > 0 and all(t == 'ОТ' for t in vac_cells), str(vac_cells[:5]))
    check('H: 7 дней плана (14–20.09)', len([t for t in vac_cells if t == 'ОТ']) == 7, len(vac_cells))

    # 5. Тултип ячейки плана — «заполнится кодом «ОТ»»
    tip = page.evaluate("var el=document.querySelector('#wsGridWrap td.ws-cell.ws-vac-plan'); el? el.getAttribute('title') : ''")
    check('I: тултип плана: «заполнится кодом «ОТ»»', 'заполнится кодом «ОТ»' in tip, tip[:100])

    # 6. Цвет фона статусной ячейки «Д8» = из справочника
    bg = page.evaluate("""(function(){var tds=document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){ if(tds[i].textContent.trim()==='Д8') return tds[i].style.background; } return '';})()""")
    check('J: фон ячейки «Д8» из справочника (rgb(255,249,196) = #FFF9C4)', bg.replace(' ','') == 'rgb(255,249,196)', bg)

    # 7. Попап: клик по пустой ячейке → строки 16 кодов + «— выходной»
    page.evaluate("document.querySelector('#wsGridWrap td.ws-cell.ws-status-empty') ? document.querySelector('#wsGridWrap td.ws-cell.ws-status-empty').click() : null")
    page.wait_for_timeout(600)
    popup_html = page.evaluate("document.getElementById('wsCellPopup') ? document.getElementById('wsCellPopup').innerHTML : ''")
    rows = page.evaluate("document.querySelectorAll('#wsCellPopup .ws-popup-row').length")
    check('K: попап открыт', popup_html != '', popup_html[:80])
    # Task 303: + строка «+ Мероприятие…» (быстрое добавление события)
    check('L: в попапе 19 строк (16 кодов + «— выходной» + «+ Мероприятие…» + «Дополнительно…»)', rows == 19, rows)
    for code in ['Д8','Д7,2','д','н','ОТ','У','ОВ','ПР','*','.']:
        check('M: попап содержит код «%s»' % code, ('>' + code + '<') in popup_html.replace('\n',''))
    check('N: старых кодов «О» (отпуск) и «П» (прогул) в попапе НЕТ', ('>О<' not in popup_html) and ('>П<' not in popup_html))

    # 8. Выбор «.» в попапе — ячейка локально перекрашивается, «Сохранить (1)»
    page.evaluate("WorkSchedule && WorkSchedule._popupCell ? WorkSchedule.onPopupStatus('.') : 'no-popup'")
    page.wait_for_timeout(400)
    save_btn = page.evaluate("var b=document.getElementById('wsSaveBtn'); b? {hidden:b.hidden, text:b.textContent} : null")
    check('O: выбор «.» — кнопка «Сохранить (1)»', save_btn and not save_btn['hidden'] and '1' in save_btn['text'], str(save_btn))

    # 9. Расширенная правка: select заполнен 16 кодами + «— выходной»
    page.evaluate("document.querySelector('#wsGridWrap td.ws-cell').click()")
    page.wait_for_timeout(500)
    page.evaluate("WorkSchedule.onPopupMore()")
    page.wait_for_timeout(500)
    opts = page.evaluate("Array.from(document.querySelectorAll('#wsCellStatus option')).map(o=>o.value)")
    check('P: select расширенной правки: 17 опций (16 кодов + «—»)', len(opts) == 17, str(opts))
    check('Q: select содержит «Д7,2» и «.»', 'Д7,2' in opts and '.' in opts)
    opt_texts = page.evaluate("Array.from(document.querySelectorAll('#wsCellStatus option')).map(o=>o.textContent)")
    check('R: опция «Д7,2» с названием', any('Д7,2' in t for t in opt_texts), str(opt_texts[:4]))
    page.evaluate("WorkSchedule.closeCellForm ? WorkSchedule.closeCellForm() : null")

    # 10. Отмена локальной правки (не сохраняем) — удалим _PENDING
    page.evaluate("WorkSchedule._PENDING = {}; WorkSchedule._renderGrid(); WorkSchedule._updateSaveBtn()")

    # 11. JS-ошибок нет
    check('S: 0 JS-ошибок', len(js_errors) == 0, '; '.join(js_errors[:3]))

    # DOM-измерение: коды помещаются в ячейки (anti-VLM-галлюцинация)
    fit = page.evaluate("""(function(){
        var out = [];
        document.querySelectorAll('#wsGridWrap td.ws-cell').forEach(function(td){
            var txt = td.textContent.trim();
            if (!txt || txt === '·' || txt === 'ОТ') return;
            var range = document.createRange();
            range.selectNodeContents(td);
            var w = range.getBoundingClientRect().width;
            var cw = td.getBoundingClientRect().width;
            if (w > cw - 1) out.push(txt + ':' + Math.round(w) + 'px>' + Math.round(cw) + 'px');
        });
        return out;
    })()""")
    check('T: все коды помещаются в ячейки (без обрезания)', len(fit) == 0, str(fit[:6]))

    # Скриншот 1: чистая сетка (форма закрыта, правки отменены)
    page.wait_for_timeout(400)
    page.screenshot(path='/home/z/my-project/kip8test/scripts/task298-proof-grid.png')
    # Скриншот 1b: прокрутка к плану отпуска (день 14+, «ОТ» в кадре)
    page.evaluate("var td=Array.from(document.querySelectorAll('#wsGridWrap td.ws-cell.ws-vac-plan'))[0]; td ? td.scrollIntoView({block:'nearest', inline:'center'}) : null;")
    page.wait_for_timeout(300)
    page.screenshot(path='/home/z/my-project/kip8test/scripts/task298-proof-vacplan.png')
    # Скриншот 2: попап выбора статуса (Task 251) со свотчами
    page.evaluate("document.querySelector('#wsGridWrap td.ws-cell').click()")
    page.wait_for_timeout(500)
    page.screenshot(path='/home/z/my-project/kip8test/scripts/task298-proof-popup.png')
    # Десктоп
    page2 = ctx.new_page()
    page2.set_viewport_size({'width':1280,'height':800})
    browser.close()

fails = [r for r in results if not r[1]]
print()
print('ИТОГО: %d/%d PASS' % (len(results)-len(fails), len(results)))
sys.exit(1 if fails else 0)
