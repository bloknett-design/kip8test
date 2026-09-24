#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408 — адаптация тестов:
#  1) ВСЕ VM-хосты с _renderWorkerCard: + методы года
#     (_wtabYearOf/_wtabYearMin/_wtabYearNav/_wtabYearRecords);
#  2) test-task311: title на БЕЙДЖЕ мероприятия разрешён (вид И/ПЗ —
#     заявка), ячейка — по-прежнему без title;
#  3) test-task394: границы года переехали в _wtabYearRecords,
#     заголовок блока — wYear + навигатор;
#  4) test-task407: wording «— за N год не проводился».
import glob
import re
import io

NEW_METHODS = [
    ("_wtabYearOf", "_wtabYearOf"),
    ("_wtabYearMin", "_wtabYearMin"),
    ("_wtabYearNav", "_wtabYearNav"),
    ("_wtabYearRecords", "_wtabYearRecords"),
]

# --- 1. хосты: вставка методов года после _renderWorkerCard ---
host_re = re.compile(
    r"^([ \t]*)methodText\(INDEX_SRC, '_renderWorkerCard'\) \+ ',\\\\n' \+[ \t]*\n",
    re.M)

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = io.open(f, encoding='utf-8').read()
    m = host_re.search(s)
    if not m:
        continue
    indent = m.group(1)
    add = ''.join(
        "%smethodText(INDEX_SRC, '%s') + ',\\\\n' +\n" % (indent, name)
        for _, name in NEW_METHODS)
    s2 = host_re.sub(lambda mm: mm.group(0) + add, s, count=1)
    if s2 != s:
        io.open(f, 'w', encoding='utf-8').write(s2)
        changed.append(f)
print('хосты дополнены: %d файлов' % len(changed))
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

# --- 2. test-task311: title только на бейдже ---
patch('tests/test-task311.js', [(
"""        assertFalse(rc.indexOf('title="') !== -1,
            'рендер не пишет title-атрибут в ячейку');
""",
"""        // Task 408 (заявка: вид И/ПЗ у кодов в шахматке): title
        // остаётся ТОЛЬКО на бейдже мероприятия («код — тема
        // записи»); сама ячейка — по-прежнему без title
        const tCount = rc.split('title="').length - 1;
        const bCount = rc.split("' title=\\"' +").length - 1;
        assertTrue(tCount === bCount && bCount === 1,
            'единственный title — тултип бейджа (не ячейка)');
""")])

# --- 3. test-task394: фильтр года в _wtabYearRecords ---
patch('tests/test-task394.js', [(
"""        assertTrue(fn.indexOf("Мероприятия · ' +\\n                     this._year + '</div>'") !== -1,
            'заголовок блока — год');
        assertTrue(fn.indexOf('нет мероприятий за год') !== -1,
            'пустое состояние — «нет мероприятий за год»');
        assertFalse(fn.indexOf('monthNames') !== -1,
            'monthNames карточке больше не нужен');
        // защита от смешанных данных: сверка пересечения с годом
        assertTrue(fn.indexOf("trYStart = this._year + '-01-01'") !== -1 &&
                   fn.indexOf("trYEnd = this._year + '-12-31'") !== -1,
            'границы года для фильтра записей');
        assertTrue(fn.indexOf('if (tE < trYStart || tS > trYEnd) continue;') !== -1,
            'записи вне года не показываются');
""",
"""        assertTrue(fn.indexOf("Мероприятия · ' +") !== -1 &&
                   fn.indexOf('wYear + this._wtabYearNav(tabNo, wYear)') !== -1,
            'заголовок блока — год + навигатор (Task 408)');
        assertTrue(fn.indexOf('нет мероприятий за год') !== -1,
            'пустое состояние — «нет мероприятий за год»');
        assertFalse(fn.indexOf('monthNames') !== -1,
            'monthNames карточке больше не нужен');
        // защита от смешанных данных: сверка пересечения с годом
        // (Task 408: фильтр переехал в _wtabYearRecords)
        const wr = stripComments(methodText(INDEX_SRC, '_wtabYearRecords'));
        assertTrue(wr.indexOf("yS = year + '-01-01'") !== -1 &&
                   wr.indexOf("yE = year + '-12-31'") !== -1,
            'границы года для фильтра записей');
        assertTrue(wr.indexOf('if (e < yS || s > yE) continue;') !== -1,
            'записи вне года не показываются');
""")])

# --- 4. test-task407: wording «— за N год не проводился» ---
patch('tests/test-task407.js', [
    (
"""        assertTrue(fn.indexOf('— не проводился') !== -1 &&
                   fn.indexOf('— в этом году не проводился') !== -1,
            'пустые состояния пункта (только asBlocks)');
""",
"""        assertTrue(fn.indexOf('— не проводился') !== -1 &&
                   fn.indexOf('год не проводился') !== -1,
            'пустые состояния пункта (только asBlocks; Task 408: «— за год»)');
"""),
    (
"""        assertTrue(seg.indexOf('— в этом году не проводился') !== -1,
            'в году записей нет (карточка показывает явно)');
""",
"""        assertTrue(seg.indexOf('— за ' + new Date().getFullYear() +
                                ' год не проводился') !== -1,
            'в году записей нет (карточка показывает явно)');
"""),
    (
"""        assertTrue(html.indexOf('— не проводился') === -1 &&
                   html.indexOf('— в этом году не проводился') === -1,
            'пустые состояния в попапе не показываются');
""",
"""        assertTrue(html.indexOf('— не проводился') === -1 &&
                   html.indexOf('год не проводился') === -1,
            'пустые состояния в попапе не показываются');
"""),
])

print('АДАПТАЦИЯ ЗАВЕРШЕНА')
