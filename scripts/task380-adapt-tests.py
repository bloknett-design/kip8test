#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 380: адаптация тестов 315/316 — _renderMonthEventsPanel теперь
# зовёт this._isoDate(new Date()) (граница прошедших мероприятий);
# VM-хосты тестов собирались ДО Task 380 и _isoDate в них нет →
# TypeError. Добавляем РЕАЛЬНУЮ логику _isoDate заглушкой рядом с
# _barExpSync (тот же прецедент — Task 378 добавлял _barExpSync).
import io

STUB = ('"_isoDate: function(dt){ var m=(\\"\\"+(dt.getMonth()+1)).padStart(2,\\"0\\");'
        ' var d=(\\"\\"+dt.getDate()).padStart(2,\\"0\\");'
        ' return dt.getFullYear()+\\"-\\"+m+\\"-\\"+d; },'
        ' _barExpSync: function() {},\\""')

OLD = "'_barExpSync: function() {},'"
NEW = ("'_isoDate: function(dt){ var m=(\"\"+(dt.getMonth()+1)).padStart(2,\"0\");"
       " var d=(\"\"+dt.getDate()).padStart(2,\"0\");"
       " return dt.getFullYear()+\"-\"+m+\"-\"+d; },"
       " _barExpSync: function() {},'")

for path in ('tests/test-task315.js', 'tests/test-task316.js'):
    s = io.open(path, encoding='utf-8').read()
    n = s.count(OLD)
    assert n >= 1, path + ': якорь _barExpSync не найден'
    assert s.count('_isoDate: function') == 0, path + ': заглушка уже стоит (двойной запуск?)'
    s = s.replace(OLD, NEW)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: добавлено заглушек _isoDate: %d' % (path, n))
print('OK')
