#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 413 — адаптация тестов 407/408 под осознанное изменение
listTrainings (мягкая деградация без листа «Инструктажи», Task 413):
строка ответа instrAll теперь `sheet ? this._readTrainingsSheet(sheet, {}) : []`.
"""
import io

ROOT = '/home/z/my-project/kip8test'


def patch(path, pairs):
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    for i, (old, new) in enumerate(pairs, 1):
        if s.count(old) != 1:
            raise SystemExit('%s: правка %d встречается %d раз (ожидался 1)'
                             % (path, i, s.count(old)))
        s = s.replace(old, new)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: %d правок OK' % (path, len(pairs)))


# test-task407.js — instrAll в ответе listTrainings
patch(ROOT + '/tests/test-task407.js', [(
    "        assertTrue(fn.indexOf('instrAll:  this._readTrainingsSheet(sheet, {})') !== -1,\n"
    "            'поле instrAll — ВСЕ записи «Инструктажей» без фильтра года');\n",
    "        assertTrue(\n"
    "            fn.indexOf('instrAll:  sheet ? this._readTrainingsSheet(sheet, {}) : []') !== -1,\n"
    "            'поле instrAll — ВСЕ записи «Инструктажей» (Task 413: без '\n"
    "            'листа — пустой срез, чтение не падает)');\n",
)])

# test-task408.js — instrAll не тронут (событийный срез жив)
patch(ROOT + '/tests/test-task408.js', [(
    "        assertTrue(fn.indexOf('instrAll:  this._readTrainingsSheet(sheet, {})') !== -1,\n"
    "            'instrAll (Task 407) не тронут');\n",
    "        assertTrue(\n"
    "            fn.indexOf('instrAll:  sheet ? this._readTrainingsSheet(sheet, {}) : []') !== -1,\n"
    "            'instrAll (Task 407) жив; Task 413 — пустой срез без листа');\n",
)])
