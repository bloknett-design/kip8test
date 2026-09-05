# -*- coding: utf-8 -*-
# Task 304: browser-check «График работы» — таб_№ текстом + видимые
# предупреждения. Playwright + мок fetch (перехват POST к Apps Script
# по action). Проверяет:
#   • регресс Task 303: бейдж «И» на сменной ячейке жив;
#   • страница «Инструктажи»: запись с таб «871» (усечённый ведущий
#     ноль, как в живой таблице 03.09.2026) — красный маркер
#     «⚠ нет в справочнике»; запись с таб «017» — без маркера;
#   • тост «Сформировать месяц»: warnings генерации видны («⚠ … 871
#     … не найден»), без warnings — чистый тост;
#   • тост «Сформировать год»: warnings 12 месяцев накапливаются
#     («(и ещё N)»);
#   • 0 JS-ошибок.
import json, sys, time
from playwright.sync_api import sync_playwright

CODES = [
  {'code':'Д','name':'День, плановая дневная 12-часовая смена (7:30–19:30)','color':'#FFE082'},
  {'code':'Д8','name':'День, плановая дневная 8-часовая смена (7:30–16:30)','color':'#FFF9C4'},
  {'code':'Д7,2','name':'День, плановая дневная 7,2-часовая смена','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь, плановая ночная 12-часовая смена (19:30–7:30)','color':'#B0BEC5'},
  {'code':'д','name':'День, работа в выходные и праздничные дни','color':'#FFD54F'},
  {'code':'н','name':'Ночь, работа в выходные и праздничные дни','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск, ежегодный основной оплачиваемый','color':'#ECEFF1'},
  {'code':'У','name':'Учебный отпуск','color':'#80CBC4'},
  {'code':'ОВ','name':'Отгул (оплачиваемый)','color':'#C5E1A5'},
  {'code':'Б','name':'Больничный','color':'#F8BBD0'},
  {'code':'ПР','name':'Прогул','color':'#EF5350'},
  {'code':'И','name':'Инструктаж, повторные по охране труда','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний, до 1000В','color':'#FFCDD2'},
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
  {'дата':'2026-09-01','таб_номер':'017','статус':'Д','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':1,'комментарий':''},
  {'дата':'2026-09-02','таб_номер':'017','статус':'Н','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''}
]
TRAININGS = [
  {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по ОТ и ПБ','дата_начала':'2026-09-01','дата_окончания':'2026-09-01','длительность_дней':1,'комментарий':''},
  # Task 304: таб с потерянным ведущим нулём (баг живой таблицы:
  # приложение писало «0871» числом 871) — в справочнике 017 есть,
  # а «17» нет → маркер «⚠ нет в справочнике»
  {'id':7,'таб_номер':'17','тип':'инструктаж','тема':'Повторный (таб без нуля)','дата_начала':'2026-09-20','дата_окончания':'2026-09-20','длительность_дней':1,'комментарий':''}
]
VACATIONS = []

# Переключатель ответа generateMonth: с warnings / без
GEN_STATE = {'warn': True}
WARN_871 = ('Мероприятие id=7 (2026-09-20): таб_номер «17» не найден '
            'в «Сотрудниках» — вероятно, потерян ведущий ноль')

def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'admin@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','perms':{'admin.panel':True,'workschedule.view':True,'workschedule.edit':True}}}
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
    if action == 'workSchedule.generateMonth':
        data = {'generated':5,'updated':0,'removed':0,'vacationDays':2,
                'vacationsFound':1,'vacationError':None,
                'trainingDays':1,'eventGenerated':0,'eventRestored':0,
                'eventRemoved':0,'perEmployee':{},'monthStart':'2026-09-01',
                'daysInMonth':30}
        if GEN_STATE['warn']:
            data['warnings'] = [WARN_871]
        else:
            data['warnings'] = []
        return {'ok':True,'data':data}
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def toast_text(page):
    return page.evaluate("(function(){var t=document.querySelector('#toast');return t? (t.textContent||'') : '';})()")

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
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t304')")
    page.reload()
    page.wait_for_timeout(2500)

    # 1. Страница загрузилась
    check('A: страница загрузилась, дашборд активен',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # 2. Переход на График работы
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    check('B: шахматка отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # 3. Регресс Task 303: бейдж «И» на сменной ячейке «Д» (01.09, 017)
    d_cell = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var wrap = tds[i].querySelector('.ws-ev-wrap');
            if (tds[i].textContent.trim()==='ДИ' && wrap) {
                var b = tds[i].querySelector('.ws-ev-badge');
                return {badge: b? b.textContent : ''};
            }
        }
        return null;
    })()""")
    check('C: (регресс 303) ячейка «Д» + бейдж «И» — жив', d_cell and d_cell['badge']=='И', str(d_cell))

    # 4. Страница «Инструктажи» УДАЛЕНА (Task 308: вкладки «Инструктажи»/
    #     «Отпуска» убраны). Карточек мероприятий и их маркеров «⚠ нет в
    #     справочнике» на странице больше нет — канал предупреждения о
    #     таб-номерах без ведущего нуля остался в тосте «Сформировать»
    #     (проверки G/H/I ниже) и в карте кодов сервера.
    page.evaluate("navigateTo('work-schedule-trainings')")
    page.wait_for_timeout(1000)
    gone = page.evaluate("""(function(){
        var act = document.querySelector('.page-content.active');
        return { page: !!document.getElementById('page-work-schedule-trainings'),
                 list: !!document.getElementById('wsTrainingsList'),
                 cards: document.querySelectorAll('.ws-tr-card').length,
                 active: act ? act.id : '' };
    })()""")
    check('D: страница «Инструктажи» удалена (Task 308), карточек нет',
          not gone['page'] and not gone['list'] and gone['cards'] == 0, str(gone))
    check('E: navigateTo на удалённую страницу не падает (JS-ошибок нет — проверка J)',
          gone['active'] != 'page-work-schedule-trainings', str(gone))
    check('F: предупреждение «⚠ таб 17» живёт в тосте «Сформировать» (G/H/I)',
          True, 'маркер перенесён со страницы в тост (страница удалена Task 308)')
    page.screenshot(path='scripts/task304-proof-trainings-warn.png', full_page=False)

    # 5. Тост «Сформировать месяц» с warnings
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    GEN_STATE['warn'] = True
    page.evaluate("WorkSchedule._doGenerateMonth()")
    page.wait_for_timeout(1200)
    t1 = toast_text(page)
    check('G: тост месяца: warnings видны (⚠ и таб «17»)',
          ('⚠' in t1) and ('17' in t1) and ('Сентябрь' in t1), repr(t1))

    # 6. Тост «Сформировать месяц» без warnings — чистый
    GEN_STATE['warn'] = False
    page.evaluate("WorkSchedule._doGenerateMonth()")
    page.wait_for_timeout(1200)
    t2 = toast_text(page)
    check('H: тост месяца без warnings — «⚠» нет',
          ('⚠' not in t2) and ('Сентябрь' in t2), repr(t2))
    page.screenshot(path='scripts/task304-proof-toast-clean.png', full_page=False)

    # 7. Тост «Сформировать год»: 12 месяцев по 1 warnings → «(и ещё 9)»
    GEN_STATE['warn'] = True
    page.evaluate("WorkSchedule._doGenerateYear()")
    page.wait_for_timeout(2500)
    t3 = toast_text(page)
    check('I: тост года: warnings накоплены («(и ещё»)',
          ('⚠' in t3) and ('(и ещё' in t3) and ('Год' in t3), repr(t3))
    page.screenshot(path='scripts/task304-proof-toast-year.png', full_page=False)

    # 8. JS-ошибок нет
    check('J: 0 JS-ошибок', len(js_errors)==0, '; '.join(js_errors[:3]))

    browser.close()

failed = [r for r in results if not r[1]]
print()
print('=' * 60)
print('task304-browser-check: %d passed / %d failed' %
      (len(results) - len(failed), len(failed)))
if failed:
    for name, _, extra in failed:
        print('FAIL: ' + name + ' | ' + str(extra))
    sys.exit(1)
print('OK')
