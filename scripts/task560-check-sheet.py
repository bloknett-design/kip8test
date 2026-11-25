#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 560: проверка структуры НОВОЙ Google-таблицы «Перечень КИП ИОС
рабочий.xlsx» (ID 14l0ac4zGwOblvuH8kRkwwdOymAVXD5op) — по образцу
scripts/task480-check-sheet.py (прецедент Task 480).

Сверяем: валидный xlsx-экспорт, все 4 листа _app, заголовки
(24/13/24/12 колонок, ключевые поля ППР-индикации), количество строк
данных против текущих data/*.json обоих репозиториев (kip8/kip8test).
"""
import json
import urllib.request

import openpyxl

NEW_ID = '14l0ac4zGwOblvuH8kRkwwdOymAVXD5op'
OLD_ID = '1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee'
URL = 'https://docs.google.com/spreadsheets/d/%s/export?format=xlsx' % NEW_ID
PATH = '/home/z/my-project/tmp/task560-new-sheet.xlsx'

print('Скачиваю: %s' % URL)
req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=60) as r, open(PATH, 'wb') as f:
    f.write(r.read())
print('Сохранено: %s' % PATH)

with open(PATH, 'rb') as f:
    head = f.read(4)
print('Первые байты: %r -> %s' % (head, 'OK (xlsx)' if head == b'PK\x03\x04' else 'FAIL (не xlsx!)'))

wb = openpyxl.load_workbook(PATH, read_only=True, data_only=True)
names = wb.sheetnames
print('Листы (%d): %s' % (len(names), names))

REQUIRED = ['Приборы_app', 'Блокировки_app', 'Клапана_app', 'Регуляторы_app']
for req in REQUIRED:
    print('  Лист "%s": %s' % (req, 'OK' if req in names else 'ОТСУТСТВУЕТ!'))

# Текущие totals обоих репозиторей
CUR = {}
for repo in ('kip8', 'kip8test'):
    for name, key in (('devices', 'total_devices'), ('lockouts', 'total_lockouts'),
                      ('valves', 'total_valves'), ('regulators', 'total_regulators')):
        d = json.load(open('/home/z/my-project/%s/data/%s.json' % (repo, name), encoding='utf-8'))
        CUR[(repo, name)] = d[key]
print('\nТекущие totals: kip8    devices/lockouts/valves/regulators = %s' %
      [CUR[('kip8', n)] for n in ('devices', 'lockouts', 'valves', 'regulators')])
print('Текущие totals: kip8test devices/lockouts/valves/regulators = %s' %
      [CUR[('kip8test', n)] for n in ('devices', 'lockouts', 'valves', 'regulators')])

SHEET_TO_DATA = [('Приборы_app', 'devices'), ('Блокировки_app', 'lockouts'),
                 ('Клапана_app', 'valves'), ('Регуляторы_app', 'regulators')]
print('\nСверка НОВОЙ таблицы с текущими данными:')
for sheet, dname in SHEET_TO_DATA:
    if sheet not in names:
        continue
    ws = wb[sheet]
    headers = [str(c.value).strip() if c.value is not None else '' for c in next(ws.iter_rows(max_row=1))]
    cnt = sum(1 for row in ws.iter_rows(min_row=2, max_col=1) if row[0].value is not None)
    cur_kip8 = CUR[('kip8', dname)]
    cur_test = CUR[('kip8test', dname)]
    match = 'СОВПАДАЕТ' if cnt == cur_kip8 == cur_test else 'ОТЛИЧАЕТСЯ!'
    print('  %s: %d колонок, %d строк данных (kip8=%d, kip8test=%d) -> %s' %
          (sheet, len(headers), cnt, cur_kip8, cur_test, match))
    print('    Заголовки (%d): %s' % (len(headers), headers[:8]), '...' if len(headers) > 8 else '')

# Ключевые колонки ППР-индикации (Task 478/479) на листе Приборы_app
if 'Приборы_app' in names:
    ws = wb['Приборы_app']
    headers = [str(c.value).strip() if c.value is not None else '' for c in next(ws.iter_rows(max_row=1))]
    print('\nКлючевые колонки Приборы_app (Task 478/479):')
    for key in ['ID', 'Наименование', 'Дата', 'В гр. ППР', 'Вид ремонта', 'Период ремонта', 'Изображение']:
        print('  Колонка "%s": %s' % (key, 'OK' if key in headers else 'ОТСУТСТВУЕТ!'))
wb.close()
