# -*- coding: utf-8 -*-
# Task 303: browser-check «График работы» — слой мероприятий в ячейке.
# Playwright + мок fetch (перехват POST к Apps Script по action).
# Проверяет: бейдж И/ПЗ на сменных ячейках (Д/Д8), пунктирный бейдж
# на пустой ячейке, тултипы с темой, секцию «Мероприятия в этот день»
# в попапе, быстрое добавление «+ Мероприятие…» с префиллом.
import json, sys, time
from playwright.sync_api import sync_playwright

WS_URL = 'https://script.google.com/macros/s/AKfycbyt2sjbJ8xT5UPKDlYj4q-CV-5pH_Yrv5COrg0PIpp92snpQULUNtJC__pMnQ0h6feNlA/exec'

CODES = [
  {'code':'Д','name':'День, плановая дневная 12-часовая смена (7:30–19:30)','color':'#FFE082'},
  {'code':'Д8','name':'День, плановая дневная 8-часовая смена (7:30–16:30)','color':'#FFF9C4'},
  {'code':'Д7,2','name':'День, плановая дневная 7,2-часовая смена (пятница/предпраздничный)','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь, плановая ночная 12-часовая смена (19:30–7:30)','color':'#B0BEC5'},
  {'code':'д','name':'День, работа в выходные и праздничные дни','color':'#FFD54F'},
  {'code':'н','name':'Ночь, работа в выходные и праздничные дни','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск, ежегодный основной оплачиваемый','color':'#ECEFF1'},
  {'code':'У','name':'Учебный отпуск','color':'#80CBC4'},
  {'code':'ОВ','name':'Отгул (оплачиваемый)','color':'#C5E1A5'},
  {'code':'Б','name':'Больничный','color':'#F8BBD0'},
  {'code':'ПР','name':'Прогул','color':'#EF5350'},
  {'code':'И','name':'Инструктаж, повторные по охране труда и промбезопасности','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение, по охране труда и промышленной безопасности','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний, до 1000В, на допуск к самостоятельной работе','color':'#FFCDD2'},
  {'code':'*','name':'Примечание (с комментарием)','color':'#FFAB91'},
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
  # 01.09 — смена «Д» + инструктаж (бейдж «И»)
  {'дата':'2026-09-01','таб_номер':'017','статус':'Д','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':1,'комментарий':''},
  # 02.09 — смена «Н», БЕЗ мероприятий (контроль: бейджей нет)
  {'дата':'2026-09-02','таб_номер':'017','статус':'Н','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  # 03.09 — «Д8» + проверка знаний (бейдж «ПЗ»)
  {'дата':'2026-09-03','таб_номер':'023','статус':'Д8','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':2,'комментарий':''},
  # 09.09 — день-мероприятие БЕЗ смены: код «И» — основной (бейджа нет)
  {'дата':'2026-09-09','таб_номер':'017','статус':'И','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':5,'комментарий':''},
  # 12.09 — отпуск на дне с мероприятием: бейдж скрыт (ОТ)
  {'дата':'2026-09-12','таб_номер':'023','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  # 10.09 — «.» ручной, мероприятий нет
  {'дата':'2026-09-10','таб_номер':'023','статус':'.','переработка':0,'праздник':0,'источник':'руч','дата_обновления':'2026-09-10T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''}
]
TRAININGS = [
  {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по ОТ и ПБ','дата_начала':'2026-09-01','дата_окончания':'2026-09-01','длительность_дней':1,'комментарий':''},
  {'id':2,'таб_номер':'023','тип':'проверка_знаний','тема':'Проверка знаний до 1000В','дата_начала':'2026-09-03','дата_окончания':'2026-09-03','длительность_дней':1,'комментарий':''},
  {'id':3,'таб_номер':'017','тип':'обучение','тема':'Курс по охране труда','дата_начала':'2026-09-05','дата_окончания':'2026-09-05','длительность_дней':1,'комментарий':''},
  {'id':5,'таб_номер':'017','тип':'инструктаж','тема':'Инструктаж на рабочем месте','дата_начала':'2026-09-09','дата_окончания':'2026-09-09','длительность_дней':1,'комментарий':''},
  {'id':6,'таб_номер':'023','тип':'обучение','тема':'Обучение по ПБ (в отпуске)','дата_начала':'2026-09-12','дата_окончания':'2026-09-12','длительность_дней':1,'комментарий':''}
]
VACATIONS = []

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
        return {'ok':True,'data':{'trainings':TRAININGS}}
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
    ctx.route('**script.google.com/**', handle)

    page.goto('http://localhost:8925/index.html')
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t303')")
    page.reload()
    page.wait_for_timeout(2500)

    # 1. Страница загрузилась
    check('A: страница загрузилась, дашборд активен',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # 2. Переход на График работы
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    check('B: шахматка отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # 3. Бейдж на сменной ячейке «Д» (01.09, 017) — «два значения»
    d_cell = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var wrap = tds[i].querySelector('.ws-ev-wrap');
            if (tds[i].textContent.trim()==='ДИ' && wrap) {
                var b = tds[i].querySelector('.ws-ev-badge');
                return {text: tds[i].textContent.trim(), badge: b? b.textContent : '',
                        bg: b? b.style.background : '', cls: tds[i].className};
            }
        }
        return null;
    })()""")
    check('C: ячейка «Д» + бейдж «И» (два значения)', d_cell and d_cell['badge']=='И', str(d_cell))
    check('D: цвет бейджа «И» из справочника (rgb(179,229,252)=#B3E5FC)',
          d_cell and d_cell['bg'].replace(' ','')=='rgb(179,229,252)', str(d_cell and d_cell['bg']))

    # 4. Бейдж «ПЗ» на «Д8» (03.09, 023)
    pz = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            if (tds[i].textContent.trim()==='Д8ПЗ') {
                var b = tds[i].querySelector('.ws-ev-badge');
                return {text: tds[i].textContent.trim(), badge: b? b.textContent : '',
                        bg: b? b.style.background : ''};
            }
        }
        return null;
    })()""")
    check('E: ячейка «Д8» + бейдж «ПЗ»', pz and pz['badge']=='ПЗ' and pz['text']=='Д8ПЗ', str(pz))
    check('F: цвет бейджа «ПЗ» (rgb(255,205,210)=#FFCDD2)',
          pz and pz['bg'].replace(' ','')=='rgb(255,205,210)', str(pz and pz['bg']))

    # 5. Смена «Н» без мероприятий — бейджа нет
    no_badge = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            if (tds[i].textContent.trim()==='Н') return !tds[i].querySelector('.ws-ev-badge');
        }
        return false;
    })()""")
    check('G: «Н» без мероприятий — бейджа нет', no_badge)

    # 6. День-мероприятие без смены (09.09, «И») — код основной, бейджа нет
    ev_day = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            if (tds[i].textContent.trim()==='И') return {badge: !!tds[i].querySelector('.ws-ev-badge')};
        }
        return null;
    })()""")
    check('H: «И» без смены — код в ячейке, бейджа нет (не дублируем)', ev_day and ev_day['badge']==False, str(ev_day))

    # 7. Отпуск (ОТ) с мероприятием — бейдж скрыт
    ot_badge = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            if (tds[i].textContent.trim()==='ОТ') return !!tds[i].querySelector('.ws-ev-badge');
        }
        return null;
    })()""")
    check('I: «ОТ» с мероприятием — бейдж скрыт (событие в тултипе)', ot_badge==False, str(ot_badge))

    # 8. Пустая ячейка с мероприятием (05.09, обучение) — пунктирный бейдж
    pending = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var b = tds[i].querySelector('.ws-ev-badge.ws-ev-pending');
            if (b) return {cell: tds[i].textContent.trim(), badge: b.textContent,
                           tip: tds[i].getAttribute('title')};
        }
        return null;
    })()""")
    check('J: пустая ячейка + пунктирный бейдж «ОБ»', pending and pending['badge']=='ОБ' and pending['cell']=='·ОБ', str(pending))
    # Task 311: тултипы с ячеек убраны — подсказку заменяет пунктирный бейдж
    check('K: Task 311 — тултип подсказки убран (title пуст), пунктирный бейдж жив',
          pending and pending['badge'] == 'ОБ' and not (pending['tip'] or ''), str(pending and (pending['tip'] or '')[:120]))

    # 9. (Task 311) Тултип ячейки «Д» убран — тема мероприятия в попапе
    #    клика (проверка M ниже) и в карточке сотрудника
    tip_d = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            if (tds[i].textContent.trim()==='ДИ') return tds[i].getAttribute('title') || '';
        }
        return '';
    })()""")
    check('L: Task 311 — тултип «Д»+И убран (title пуст)',
          tip_d == '', str(tip_d[:160]))

    # 10. Попап ячейки с мероприятием (01.09, 017): Task 313 — окно
    #     мероприятий НАД окном кодов (секция переехала из попапа)
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){ if (tds[i].textContent.trim()==='ДИ') { tds[i].click(); return; } }
    })()""")
    page.wait_for_timeout(600)
    pop_m = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var ev = document.getElementById('wsEventsPopup');
        return { codesOpen: cp ? cp.classList.contains('active') : false,
                 evOpen: ev ? ev.classList.contains('active') : false,
                 codesHtml: cp ? cp.innerHTML : '',
                 evHtml: ev ? ev.innerHTML : '' };
    })()""")
    rows = page.evaluate("document.querySelectorAll('#wsCellPopup .ws-popup-row').length")
    check('M: Task 313 — окно «Мероприятия в этот день» над окном кодов (секция переехала)',
          pop_m['codesOpen'] and pop_m['evOpen'] and
          ('Мероприятия в этот день' in pop_m['evHtml']) and
          ('Мероприятия в этот день' not in pop_m['codesHtml']))
    check('N: строка события с темой (справочная, некликабельная)',
          'Повторный инструктаж по ОТ и ПБ' in pop_m['evHtml'] and 'ws-popup-event' in pop_m['evHtml'])
    check('O: «+ Мероприятие…» в попапе (быстрое добавление)', '+ Мероприятие…' in pop_m['codesHtml'])
    check('P: строк в окне кодов 13 (11 статусов + «+Мероприятие» + «Дополнительно»; Task 312/313)',
          rows == 13, rows)

    # 11. Попап ячейки БЕЗ мероприятий: 19 строк (без секции)
    page.evaluate("WorkSchedule.closeCellPopup()")
    page.wait_for_timeout(200)
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){ if (tds[i].textContent.trim()==='Н') { tds[i].click(); return; } }
    })()""")
    page.wait_for_timeout(600)
    popup2 = page.evaluate("document.getElementById('wsCellPopup')? document.getElementById('wsCellPopup').innerHTML : ''")
    rows2 = page.evaluate("document.querySelectorAll('#wsCellPopup .ws-popup-row').length")
    check('Q: попап без событий: 13 строк, секции нет (Task 312: без «— выходной —» и мероприятий)', rows2 == 13 and 'Мероприятия в этот день' not in popup2, rows2)

    # 12. «+ Мероприятие…» — форма с префиллом (сотрудник + дата ячейки)
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){ if (tds[i].textContent.trim()==='ДИ') { tds[i].click(); return; } }
    })()""")
    page.wait_for_timeout(500)
    page.evaluate("WorkSchedule.onPopupAddEvent()")
    page.wait_for_timeout(600)
    form = page.evaluate("""(function(){
        var sheet = document.getElementById('wsTrSheet');
        return {open: sheet? sheet.classList.contains('active') : false,
                tab: (document.getElementById('wsTrTabNo')||{}).value,
                start: (document.getElementById('wsTrStart')||{}).value,
                end: (document.getElementById('wsTrEnd')||{}).value};
    })()""")
    check('R: форма мероприятия открыта, сотрудник 017, дата 2026-09-01',
          form and form['open'] and form['tab']=='017' and form['start']=='2026-09-01' and form['end']=='2026-09-01', str(form))
    page.evaluate("WorkSchedule.closeTrainingForm()")

    # 13. JS-ошибок нет
    check('S: 0 JS-ошибок', len(js_errors)==0, '; '.join(js_errors[:3]))

    # 14. Бейджи не вылезают за ячейку (DOM-измерение)
    fit = page.evaluate("""(function(){
        var out = [];
        document.querySelectorAll('#wsGridWrap td.ws-cell').forEach(function(td){
            var wrap = td.querySelector('.ws-ev-wrap');
            if (!wrap) return;
            var w = wrap.getBoundingClientRect();
            var c = td.getBoundingClientRect();
            if (w.right > c.right + 1) out.push('badge-right:' + Math.round(w.right) + '>' + Math.round(c.right));
            if (w.left < c.left - 1) out.push('badge-left');
            if (w.bottom > c.bottom + 1) out.push('badge-bottom');
        });
        return out;
    })()""")
    check('T: бейджи в пределах ячеек', len(fit)==0, str(fit[:6]))

    # Скриншоты: сетка с бейджами (мобильный) + зум к ячейке «Д8+ПЗ»
    page.wait_for_timeout(400)
    page.screenshot(path='/home/z/my-project/kip8test/scripts/task303-proof-grid.png')
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){ if (tds[i].textContent.trim()==='Д8ПЗ') { tds[i].scrollIntoView({block:'nearest', inline:'center'}); return; } }
    })()""")
    page.wait_for_timeout(300)
    page.screenshot(path='/home/z/my-project/kip8test/scripts/task303-proof-badge.png')
    browser.close()

fails = [r for r in results if not r[1]]
print()
print('ИТОГО: %d/%d PASS' % (len(results)-len(fails), len(results)))
sys.exit(1 if fails else 0)
