#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408 — адаптация (часть 4): точечно добить второй хост
# test-task394.js (pageHost, строка ~352) — пропущен дедуп-фильтром
# adapt3 (второе вхождение '_wtabYearRecords' оказалось SRC-ассертом).
import io

f = 'tests/test-task394.js'
s = io.open(f, encoding='utf-8').read()

old = """        methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +
        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +
        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +"""
new = """        methodText(INDEX_SRC, '_renderWorkerCard') + ',\\n' +
        methodText(INDEX_SRC, '_wtabYearOf') + ',\\n' +
        methodText(INDEX_SRC, '_wtabYearMin') + ',\\n' +
        methodText(INDEX_SRC, '_wtabYearNav') + ',\\n' +
        methodText(INDEX_SRC, '_wtabYearRecords') + ',\\n' +
        methodText(INDEX_SRC, '_renderWorkerCardPanels') + ',\\n' +
        methodText(INDEX_SRC, '_isInstrType') + ',\\n' +"""

if s.count(old) != 1:
    raise SystemExit('FAIL: якорь встречается %d раз' % s.count(old))
s = s.replace(old, new)
io.open(f, 'w', encoding='utf-8').write(s)
print('test-task394.js: pageHost дополнен')
