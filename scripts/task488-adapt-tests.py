#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 488: адаптация ТЕСТОВ под «простой редактируемый xlsx».
# Новые вызовы строителей: _buildTabelWorkbook/_buildEventsWorkbook/
# _buildArchiveWorkbook зовут this._wsXlsDocProps() — VM-хосты тестов
# 430/438/439/441/445/446/459/465 не знают метода → добавляем
# methodText(..., '_wsXlsDocProps') во все хосты этих файлов.
# Плюс: zip архива теперь 12 частей (docProps×2, CT первым) —
# тесты Task 430 (count=10, список имён) обновлены.
import re

# ---------- 1. Хосты: добавляем _wsXlsDocProps ----------
ESC_NL = "methodText(INDEX_SRC, '_wsXlsEsc') + ',\\n' +"
DP_NL = "methodText(INDEX_SRC, '_wsXlsDocProps') + ',\\n' +"
ESC_WS = "methodText(WS_CLIENT, '_wsXlsEsc') + ',' +"
DP_WS = "methodText(WS_CLIENT, '_wsXlsDocProps') + ',' +"

for f in ['tests/test-task430.js', 'tests/test-task445.js',
          'tests/test-task446.js', 'tests/test-task459.js']:
    s = open(f, encoding='utf-8').read()
    n = s.count(ESC_NL)
    s = s.replace(ESC_NL, ESC_NL + '\n' + '            ' + DP_NL)
    open(f, 'w', encoding='utf-8').write(s)
    print('%s: %d хостов +_wsXlsDocProps' % (f, n))

for f in ['tests/test-task438.js', 'tests/test-task439.js',
          'tests/test-task441.js']:
    s = open(f, encoding='utf-8').read()
    n = s.count(ESC_WS)
    s = s.replace(ESC_WS, ESC_WS + '\n            ' + DP_WS)
    open(f, 'w', encoding='utf-8').write(s)
    print('%s: %d хостов +_wsXlsDocProps' % (f, n))

# test-task465: имена в массиве
f = 'tests/test-task465.js'
s = open(f, encoding='utf-8').read()
old = "'_wsXlsColName', '_wsXlsEsc', '_wsXlsBytes', '_wsXlsZip', '_wsXlsCrc32'"
new = "'_wsXlsColName', '_wsXlsEsc', '_wsXlsBytes', '_wsXlsZip', '_wsXlsCrc32',\n                      '_wsXlsDocProps'"
assert old in s, '465: массив имён не найден'
s = s.replace(old, new)
open(f, 'w', encoding='utf-8').write(s)
print('test-task465.js: names +_wsXlsDocProps')

# ---------- 2. test-task430: zip 12 частей + docProps + CT первым ----------
f = 'tests/test-task430.js'
s = open(f, encoding='utf-8').read()

old = """    test('zip: 10 частей, stored, EOCD/каталог консистентны', () => {
        const wb = wbHost()._buildArchiveWorkbook();
        const z = parseZip(wb.bytes);
        assertEqual(z.files.length, 10,
            'все части книги в контейнере (5 листов + 5 служебных; Task 445)');"""
new = """    test('zip: 12 частей, stored, EOCD/каталог консистентны', () => {
        const wb = wbHost()._buildArchiveWorkbook();
        const z = parseZip(wb.bytes);
        assertEqual(z.files.length, 12,
            'все части книги в контейнере (5 листов + 7 служебных: CT, .rels, docProps core/app, workbook, workbook-rels, styles; Task 488)');
        assertEqual(z.files[0].name, '[Content_Types].xml',
            'CT — ПЕРВАЯ часть zip (канонический порядок, Task 488)');"""
assert old in s, '430: zip-тест не найден'
s = s.replace(old, new)

old = """        const names = z.files.map(f => f.name);
        for (const need of ['[Content_Types].xml', '_rels/.rels',
                            'xl/workbook.xml', 'xl/_rels/workbook.xml.rels',
                            'xl/styles.xml', 'xl/worksheets/sheet1.xml',"""
new = """        const names = z.files.map(f => f.name);
        for (const need of ['[Content_Types].xml', '_rels/.rels',
                            'docProps/core.xml', 'docProps/app.xml',
                            'xl/workbook.xml', 'xl/_rels/workbook.xml.rels',
                            'xl/styles.xml', 'xl/worksheets/sheet1.xml',"""
assert old in s, '430: список имён не найден'
s = s.replace(old, new)

# заголовок в комментарии шапки файла
s = s.replace('//   8) _wsXlsZip: парсинг — 9 файлов PK, EOCD, имена, CRC',
              '//   8) _wsXlsZip: парсинг — 12 файлов PK (docProps×2, Task 488), EOCD, имена, CRC')
open(f, 'w', encoding='utf-8').write(s)
print('test-task430.js: zip-тест 12 частей + docProps + CT первым')

# ---------- 3. Контроль: больше ничего не трогаем ----------
print('OK — хосты и zip-ассерты обновлены')
