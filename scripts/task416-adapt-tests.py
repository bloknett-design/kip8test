#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 416 — адаптация тестов, ЧАСТЬ 2 (идемпотентная): конкатенации
хостов печати и карточки + 385 HOST_METHODS + SRC-ассерты 313/408.
(Часть 1 — массивы имён 315/316/380/394/404/399/319 — уже применена.)
"""
import io

ROOT = '/home/z/my-project/kip8test/tests/'


def patch(fname, old, new, count=None):
    p = ROOT + fname
    with io.open(p, encoding='utf-8') as f:
        s = f.read()
    n = s.count(old)
    if n == 0:
        if new in s:
            print('  skip (уже применено): %s' % fname)
            return
        raise SystemExit('НЕ НАЙДЕНО в %s: %r' % (fname, old[:90]))
    if count is not None and n != count:
        raise SystemExit('%s: ожидалось %d, найдено %d' % (fname, count, n))
    s = s.replace(old, new)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(s)
    print('  patched %s ×%d' % (fname, n))


# --- Печать (WS_CLIENT-семейство, join '\n') ---
PRINT_OLD = "methodText(WS_CLIENT, '_buildPrintHtml') + '\\n' +"
PRINT_NEW = ("methodText(WS_CLIENT, '_instrShortOf') + '\\n' +\n"
             "            methodText(WS_CLIENT, '_normInstrKey') + '\\n' +\n"
             "            methodText(WS_CLIENT, '_buildPrintHtml') + '\\n' +")
patch('test-task360.js', PRINT_OLD, PRINT_NEW, count=4)
patch('test-task362.js', PRINT_OLD, PRINT_NEW, count=1)
patch('test-task364.js', PRINT_OLD, PRINT_NEW, count=1)


def concat_pair(m, ind):
    old = ind + "methodText(INDEX_SRC, '%s') + ',\\n' +" % m
    new = (ind + "methodText(INDEX_SRC, '_instrShortOf') + ',\\n' +\n" +
           ind + "methodText(INDEX_SRC, '_normInstrKey') + ',\\n' +\n" +
           ind + "methodText(INDEX_SRC, '%s') + ',\\n' +" % m)
    return old, new


I8 = ' ' * 8
I12 = ' ' * 12

# 394 (8sp ×2), 396 (8sp ×2)
o, n = concat_pair('_renderWorkerCard', I8)
patch('test-task394.js', o, n, count=2)
patch('test-task396.js', o, n, count=2)

# 403 (12sp ×2), 404 (12sp ×2), 405 (12sp ×1), 406 (12sp ×1)
o, n = concat_pair('_renderWorkerCard', I12)
patch('test-task403.js', o, n, count=2)
patch('test-task404.js', o, n, count=2)
patch('test-task405.js', o, n, count=1)
patch('test-task406.js', o, n, count=1)

# 407: card ×1 + section ×2 (12sp); 408: section ×1; 409: section ×1;
# 414: card ×1 + section ×1
o, n = concat_pair('_renderWorkerCard', I12)
patch('test-task407.js', o, n, count=1)
patch('test-task414.js', o, n, count=1)
o, n = concat_pair('_renderInstrSection', I12)
patch('test-task407.js', o, n, count=2)
patch('test-task408.js', o, n, count=1)
patch('test-task409.js', o, n, count=1)
patch('test-task414.js', o, n, count=1)

# --- 385: HOST_METHODS (Node vm) ---
patch('test-task385.js',
      "        '_trainingCodeOf', '_statusMeta',",
      "        '_trainingCodeOf', '_statusMeta',\n"
      "        '_instrShortOf', '_normInstrKey',",
      count=1)

# --- SRC-ассерты ---
patch('test-task313.js',
      "assertTrue(ep.indexOf(\"deT.тема || deMeta.name || ''\") !== -1,",
      "assertTrue(ep.indexOf(\"this._instrShortOf(deT.тема) || deMeta.name || ''\") !== -1,",
      count=1)

patch('test-task408.js',
      "        assertTrue(fn.indexOf('events[evj].code + \\' — \\' + String(evTr.тема).trim()') !== -1,\n"
      "            'формат «код — тема»');",
      "        assertTrue(fn.indexOf('events[evj].code + \\' — \\' +') !== -1 &&\n"
      "                   fn.indexOf('this._instrShortOf(String(evTr.тема).trim())') !== -1,\n"
      "            'формат «код — тема» (Task 416: короткое название при наличии сокращения)');",
      count=1)

print()
print('OK — адаптация тестов Task 416 (часть 2) завершена')
