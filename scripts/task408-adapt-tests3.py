#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408 — адаптация (часть 3):
#  1) ВСЕ вхождения хост-паттерна (не только первое) — 393/394/396/404
#     имеют по 2 хоста;
#  2) test-task385: HOST_METHODS-массив — добавить методы года;
#  3) test-task405: SRC «деление по типу» — фильтр в _wtabYearRecords;
#  4) test-task407: SRC datalist — пересбор через _syncTrTitleField.
import glob
import re
import io

host_re = re.compile(
    r"^([ \t]*)methodText\(INDEX_SRC, '_renderWorkerCard'\) \+ ',\\n' \+[ \t]*\n",
    re.M)

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = io.open(f, encoding='utf-8').read()
    if '_wtabYearRecords' in s and host_re.search(s) and \
            s.count("methodText(INDEX_SRC, '_wtabYearRecords')") >= \
            len(host_re.findall(s)):
        continue  # уже полный комплект
    n_before = s.count("methodText(INDEX_SRC, '_wtabYearRecords')")

    def add_methods(mm):
        indent = mm.group(1)
        return (mm.group(0) +
                indent + "methodText(INDEX_SRC, '_wtabYearOf') + ',\\n' +\n" +
                indent + "methodText(INDEX_SRC, '_wtabYearMin') + ',\\n' +\n" +
                indent + "methodText(INDEX_SRC, '_wtabYearNav') + ',\\n' +\n" +
                indent + "methodText(INDEX_SRC, '_wtabYearRecords') + ',\\n' +\n")

    s2 = host_re.sub(add_methods, s)
    if s2 != s and s2.count("methodText(INDEX_SRC, '_wtabYearRecords')") > n_before:
        io.open(f, 'w', encoding='utf-8').write(s2)
        changed.append(f)
print('хосты (все вхождения): %d файлов' % len(changed))
for f in changed:
    print('  ' + f)

def patch(path, edits):
    s = io.open(path, encoding='utf-8').read()
    for old, new in edits:
        if s.count(old) != 1:
            raise SystemExit('FAIL %s: %r встречается %d раз'
                             % (path, old[:80], s.count(old)))
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: %d правок' % (path, len(edits)))

# 385: HOST_METHODS-массив
patch('tests/test-task385.js', [(
"""        // Task 405: деление записей по типу (мероприятия/инструктажи)
        '_isInstrType',
""",
"""        // Task 405: деление записей по типу (мероприятия/инструктажи)
        '_isInstrType',
        // Task 408: год блоков карточки (стрелки ‹год›)
        '_wtabYearOf', '_wtabYearMin', '_wtabYearNav',
        '_wtabYearRecords',
""")])

# 405: SRC деление по типу — фильтр в _wtabYearRecords
patch('tests/test-task405.js', [(
"""    test('карточка: деление записей по типу (evs/ins)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCard'));
        assertTrue(fn.indexOf('var evs = [], ins = [];') !== -1,
            'два списка: evs (мероприятия) и ins (инструктажи)');
        assertTrue(fn.indexOf('this._isInstrType(trs[si].тип)') !== -1,
            'фильтр по типу');
        assertTrue(fn.indexOf('for (var tk = 0; tk < evs.length; tk++)') !== -1,
            'блок «Мероприятия» строится по evs');
    });
""",
"""    test('карточка: деление записей по типу (evs/ins)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkerCard'));
        const wr = stripComments(methodText(INDEX_SRC, '_wtabYearRecords'));
        assertTrue(wr.indexOf('if (this._isInstrType(r.тип)) ins.push(r);') !== -1 &&
                   wr.indexOf('else evs.push(r);') !== -1,
            'два списка: evs (мероприятия) и ins (инструктажи)');
        assertTrue(fn.indexOf('var evs = wRecs.evs, ins = wRecs.ins;') !== -1,
            'карточка берёт записи года из _wtabYearRecords (Task 408)');
        assertTrue(fn.indexOf('for (var tk = 0; tk < evs.length; tk++)') !== -1,
            'блок «Мероприятия» строится по evs');
    });
""")])

# 407: SRC datalist — пересбор через _syncTrTitleField
patch('tests/test-task407.js', [(
"""        const of = stripComments(methodText(INDEX_SRC, 'openTrainingForm'));
        assertTrue(of.indexOf('typeSel.onchange') !== -1 &&
                   of.indexOf('this._fillTrTitleOptions();') !== -1,
            'пересбор подсказок при открытии и смене типа');
""",
"""        const of = stripComments(methodText(INDEX_SRC, 'openTrainingForm'));
        assertTrue(of.indexOf('typeSel.onchange') !== -1 &&
                   of.indexOf('this._syncTrTitleField(') !== -1,
            'пересбор поля при открытии и смене типа (Task 408: select)');
""")])

print('АДАПТАЦИЯ-3 ЗАВЕРШЕНА')
