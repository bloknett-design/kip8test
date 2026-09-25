#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 412 — адаптация тестов 407/408 под _normalizeInstrList.

1) test-task407.js: SRC-ассерт «_loadTrainings разбирает instrList» —
   старый текст `self._INSTR_LIST = data.instrList || [];` заменён на
   `self._normalizeInstrList(data.instrList);`.
2) test-task407.js + test-task408.js: VM-хосты _restoreCachedView
   (по 2 в каждом файле) получают заглушку
   `_normalizeInstrList: function(l) { return l; }` (какexisting
   `_normalizeStatusCodes`) — тесты 407/408 проверяют СВОЮ логику
   (кэш-раундтрип instrList/instrAll/eventsAll), канон-фолбэк
   покрыт отдельными тестами Task 412 (реальный метод).
"""
import io
import sys

ROOT = '/home/z/my-project/kip8test'


def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def replace_counted(s, old, new, expected, label):
    n = s.count(old)
    if n != expected:
        print('FAIL [%s]: найдено %d, ожидалось %d' % (label, n, expected))
        sys.exit(1)
    return s.replace(old, new)


def main():
    # --- 1) 407: SRC-ассерт ---
    p407 = ROOT + '/tests/test-task407.js'
    s = read(p407)
    s = replace_counted(
        s,
        "        assertTrue(fn.indexOf('self._INSTR_LIST = data.instrList || [];') !== -1,\n"
        "            'шаблон из ответа (старый сервер — пустой)');",
        "        assertTrue(fn.indexOf('self._INSTR_LIST = self._normalizeInstrList(data.instrList);') !== -1,\n"
        "            'шаблон из ответа (Task 412: пустой сервер — встроенный эталон 409)');",
        1, '407 SRC-ассерт _loadTrainings')

    # --- 2) 407: VM-хосты (2 шт.) ---
    s = replace_counted(
        s,
        "            '_normalizeStatusCodes: function(c) { return c; },' +\n",
        "            '_normalizeStatusCodes: function(c) { return c; },' +\n"
        "            '_normalizeInstrList: function(l) { return l; },' +\n",
        2, '407 VM-хосты _restoreCachedView')
    write(p407, s)
    print('OK — test-task407.js (1 SRC + 2 VM-хоста)')

    # --- 3) 408: VM-хосты (2 шт.) ---
    p408 = ROOT + '/tests/test-task408.js'
    s = read(p408)
    s = replace_counted(
        s,
        "            '_normalizeStatusCodes: function(c) { return c; },' +\n",
        "            '_normalizeStatusCodes: function(c) { return c; },' +\n"
        "            '_normalizeInstrList: function(l) { return l; },' +\n",
        2, '408 VM-хосты _restoreCachedView')
    write(p408, s)
    print('OK — test-task408.js (2 VM-хоста)')


if __name__ == '__main__':
    main()
