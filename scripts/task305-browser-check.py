# -*- coding: utf-8 -*-
# Task 305: browser-check «График работы» — бейдж плановой смены на
# днях отпуска (формат мероприятия, правый нижний угол).
# Task 306: бейдж — ТОЛЬКО у «сменных» (заявка пользователя):
# дневной 023 в отпуске бейдж НЕ показывает.
# Playwright + мок fetch (перехват POST к Apps Script по action).
#
# СТЕHД: 017 «сменный» (шаблон 1: Д/Н/вых×3, старт 31.08.2026 —
# 01.09=Н, 02–04=вых, 05=Д, 06=Н, 07–09=вых, 10=Д, 11=Н, 12–14=вых,
# 15=Д, 16=Н, 17–19=вых, 20=Д, 25=Д…); отпуск 05–16.09 (12 «ОТ»).
# 023 «дневной» (шаблон 2: Д8×5/вых×2, старт 07.09.2026);
# отпуск 21–25.09 БЕЗ записей (план «ОТ» до «Сформировать»).
# Ожидание (Task 305 + 306): дни отпуска 017 на сменных по циклу
# днях показывают «ОТ» + бейдж Д/Н; цикловые выходные в отпуске —
# без бейджа; 023 «дневной» в отпуске — план «ОТ» БЕЗ бейджа
# (фильтр empIsShift); сменные, больничные и пустые дни — без
# бейджа; слой мероприятий (Task 303) не пострадал.
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
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  # 017: смена до отпуска (контроль: бейджа нет на сменном дне)
  {'дата':'2026-09-01','таб_номер':'017','статус':'Н','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  # 017: отпуск 05–16.09 (сгенерирован): смена по циклу «под» отпуском
  {'дата':'2026-09-05','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-06','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-07','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-08','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-09','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-10','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-11','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-12','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-13','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-14','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-15','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-16','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  # 017: смена после отпуска + мероприятие (регресс Task 303: бейдж «И»)
  {'дата':'2026-09-20','таб_номер':'017','статус':'Д','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':1,'комментарий':''},
  # 017: больничный на сменном по циклу дне (контроль: НЕ отпуск — бейджа нет)
  {'дата':'2026-09-25','таб_номер':'017','статус':'Б','переработка':0,'праздник':0,'источник':'руч','дата_обновления':'2026-09-25T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  # 023: обычные смены (контроль)
  {'дата':'2026-09-14','таб_номер':'023','статус':'Д8','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-28','таб_номер':'023','статус':'Д8','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''}
]
TRAININGS = [
  {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по ОТ и ПБ','дата_начала':'2026-09-20','дата_окончания':'2026-09-20','длительность_дней':1,'комментарий':''}
]
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':2,'дата_начала':'2026-09-05','дата_окончания':'2026-09-16','комментарий':''},
  {'id':2,'таб_номер':'023','часть':1,'дата_начала':'2026-09-21','дата_окончания':'2026-09-25','комментарий':''}
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
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t305')")
    page.reload()
    page.wait_for_timeout(2500)

    # A. Страница загрузилась
    check('A: страница загрузилась, дашборд активен',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # B. Переход на График работы + явный выбор сентября 2026
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    page.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '9';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page.wait_for_timeout(2500)
    check('B: шахматка отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # C. 05.09 (017): «ОТ» + бейдж плановой смены «Д» (формат мероприятия)
    info = page.evaluate(r"""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[5]){
                var td = tds[5];
                var b = td.querySelector('.ws-ev-badge.ws-ev-shift');
                return { text: td.textContent.replace(/\s+/g,' ').trim(),
                         badge: b ? b.textContent : null,
                         bg: b ? getComputedStyle(b).backgroundColor : null,
                         wrap: !!td.querySelector('.ws-ev-wrap') };
            }
        }
        return null;
    })()""")
    check('C: 05.09 — «ОТ» (отпуск в приоритете)', info and info['text'].startswith('ОТ'), info)
    check('C2: бейдж плановой смены «Д» (формат мероприятия)',
          info and info['badge'] == 'Д' and info['wrap'], info)
    check('C3: цвет бейджа — цвет кода «Д» из справочника (#FFE082)',
          info and info['bg'] == 'rgb(255, 224, 130)', info)

    # D. 06.09: бейдж «Н» (#B0BEC5)
    info6 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[6]){
                var td = tds[6];
                var b = td.querySelector('.ws-ev-badge.ws-ev-shift');
                return { text: td.textContent.trim(), badge: b ? b.textContent : null,
                         bg: b ? getComputedStyle(b).backgroundColor : null };
            }
        }
        return null;
    })()""")
    check('D: 06.09 — «ОТ» + бейдж «Н» (#B0BEC5)',
          info6 and info6['text'].startswith('ОТ') and info6['badge'] == 'Н' and
          info6['bg'] == 'rgb(176, 190, 197)', info6)

    # E. 07.09: цикловой выходной в отпуске — бейджа нет
    info7 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[7]){
                var td = tds[7];
                return { text: td.textContent.trim(),
                         badges: td.querySelectorAll('.ws-ev-badge').length };
            }
        }
        return null;
    })()""")
    check('E: 07.09 — «ОТ» без бейджа (выходной по циклу)',
          info7 and info7['text'].startswith('ОТ') and info7['badges'] == 0, info7)

    # F. Полная серия бейджей строки 017: 05=Д 06=Н 10=Д 11=Н 15=Д 16=Н
    series = page.evaluate("""(function(){
        var days = [5,6,10,11,15,16];
        var want = ['Д','Н','Д','Н','Д','Н'];
        var out = [];
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1){
                for (var i=0;i<days.length;i++){
                    var b = tds[days[i]].querySelector('.ws-ev-badge.ws-ev-shift');
                    out.push(b ? b.textContent : null);
                }
            }
        }
        return { out: out, total: document.querySelectorAll('.ws-ev-badge.ws-ev-shift').length };
    })()""")
    check('F: серия смен под отпуском 017 = Д,Н,Д,Н,Д,Н',
          series and series['out'] == ['Д','Н','Д','Н','Д','Н'], series)
    # 017: 6 бейджей; Task 306: 023 «дневной» бейджей НЕ показывает
    check('F2: всего бейджей смен в сетке = 6 (только у 017 — дневной 023 без бейджа)',
          series and series['total'] == 6, series)

    # G. 01.09 — сменный день «Н» без бейджа (код уже основной)
    info1 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[1]){
                var td = tds[1];
                var b = td.querySelector('.ws-ev-badge.ws-ev-shift');
                return { text: td.textContent.trim(), shiftBadge: !!b };
            }
        }
        return null;
    })()""")
    check('G: 01.09 — смена «Н», бейджа плановой смены нет',
          info1 and info1['text'].startswith('Н') and not info1['shiftBadge'], info1)

    # H. 20.09: смена «Д» + бейдж мероприятия «И» (регресс Task 303)
    info20 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[20]){
                var td = tds[20];
                var ev = td.querySelector('.ws-ev-badge:not(.ws-ev-shift)');
                var sh = td.querySelector('.ws-ev-badge.ws-ev-shift');
                return { text: td.textContent.trim(), evBadge: ev ? ev.textContent : null,
                         shiftBadge: !!sh };
            }
        }
        return null;
    })()""")
    check('H: 20.09 — «Д» + бейдж мероприятия «И» (Task 303 жив)',
          info20 and info20['text'].startswith('Д') and info20['evBadge'] == 'И' and
          not info20['shiftBadge'], info20)

    # I. 25.09: больничный на сменном по циклу дне — бейджа нет
    info25 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[25]){
                var td = tds[25];
                return { text: td.textContent.trim(),
                         badges: td.querySelectorAll('.ws-ev-badge').length };
            }
        }
        return null;
    })()""")
    check('I: 25.09 — «Б» без бейджа (не семейство отпусков)',
          info25 and info25['text'].startswith('Б') and info25['badges'] == 0, info25)

    # J. 023, 21.09: ПЛАН отпуска (пустая ячейка), БЕЗ бейджа (Task 306:
    # бейдж плановой смены — только у «сменных»; дневной его не показывает)
    infop = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Петров') !== -1 && tds[21]){
                var td = tds[21];
                var b = td.querySelector('.ws-ev-badge.ws-ev-shift');
                return { text: td.textContent.trim(), plan: td.classList.contains('ws-vac-plan'),
                         badge: b ? b.textContent : null,
                         bg: b ? getComputedStyle(b).backgroundColor : null,
                         dashed: b ? b.classList.contains('ws-ev-pending') : null,
                         title: td.getAttribute('title') || '' };
            }
        }
        return null;
    })()""")
    check('J: 21.09 (023) — план «ОТ» (ws-vac-plan)', infop and infop['plan'] and infop['text'].startswith('ОТ'), infop)
    check('J2: Task 306 — бейджа плановой смены у дневного НЕТ',
          infop and infop['badge'] is None and infop['dashed'] is None, infop)

    # K. 023, 14.09: обычная смена «Д8» — бейджа нет
    info14 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Петров') !== -1 && tds[14]){
                var td = tds[14];
                return { text: td.textContent.trim(),
                         badges: td.querySelectorAll('.ws-ev-badge').length };
            }
        }
        return null;
    })()""")
    check('K: 14.09 (023) — смена «Д8» без бейджа',
          info14 and info14['text'].startswith('Д8') and info14['badges'] == 0, info14)

    # L. Тултип 05.09: плановая смена по циклу с полным названием
    info_l = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[5]){
                return { title: tds[5].getAttribute('title') || '' };
            }
        }
        return null;
    })()""")
    tip = info_l['title'] if info_l else ''
    check('L: тултип 05.09 — «по циклу (Дни_цикла): День…»',
          'по циклу (Дни_цикла): День' in tip, tip[:200])

    # M. Тултип плана 21.09: план отпуска БЕЗ плановой смены (Task 306)
    tipp = infop['title'] if infop and 'title' in infop else ''
    check('M: тултип 21.09 — план «заполнится кодом «ОТ»», БЕЗ «по циклу»',
          ('заполнится кодом' in tipp) and ('по циклу' not in tipp), tipp[:250])

    # N. Геометрия: бейджи в пределах своих ячеек (мобильная вёрстка)
    geom = page.evaluate("""(function(){
        var bad = 0, total = 0;
        document.querySelectorAll('#wsGridWrap td.ws-cell .ws-ev-badge').forEach(function(b){
            total++;
            var tb = b.getBoundingClientRect();
            var td = b.closest('td').getBoundingClientRect();
            if (tb.left < td.left - 0.5 || tb.right > td.right + 0.5 ||
                tb.top < td.top - 0.5 || tb.bottom > td.bottom + 0.5) bad++;
        });
        return { total: total, bad: bad };
    })()""")
    check('N: все бейджи в пределах ячеек (мобильная, 375px)',
          geom and geom['bad'] == 0 and geom['total'] >= 6, geom)

    # Скриншот мобильной вёрстки (строки с отпусками)
    page.screenshot(path='scripts/task305-proof-mobile.png', full_page=False)

    # O. Десктоп: бейджи в пределах ячеек
    page.set_viewport_size({'width':1280,'height':800})
    page.wait_for_timeout(800)
    geom2 = page.evaluate("""(function(){
        var bad = 0, total = 0;
        document.querySelectorAll('#wsGridWrap td.ws-cell .ws-ev-badge').forEach(function(b){
            total++;
            var tb = b.getBoundingClientRect();
            var td = b.closest('td').getBoundingClientRect();
            if (tb.left < td.left - 0.5 || tb.right > td.right + 0.5 ||
                tb.top < td.top - 0.5 || tb.bottom > td.bottom + 0.5) bad++;
        });
        return { total: total, bad: bad };
    })()""")
    check('O: бейджи в пределах ячеек (десктоп, 1280px)',
          geom2 and geom2['bad'] == 0 and geom2['total'] >= 6, geom2)
    page.screenshot(path='scripts/task305-proof-desktop.png', full_page=False)

    # P. JS-ошибок нет
    check('P: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])

    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task305-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
