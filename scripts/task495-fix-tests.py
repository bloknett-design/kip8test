#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 495 — kip8test: точечные фиксы после первого прогона.

1. index.html: из HTML-комментария над новой панелью убран литерал
   «ts-calc-field» (test-task494 считает поля панели по этому
   литералу; урок Task 488: комментарии не должны содержать
   считаемые литералы).
2. test-task495.js: (а) tablePanelChunk начинается с '<div' перед
   id-якорем — класс-атрибут стоит ДО id в теге; (б) проверка
   «кнопка вне панели» — по порядку последнего '</div>' и '<button';
   (в) calcTempSensor показывает результаты через display='block'.
"""
import io
import sys

ROOT = '/home/z/my-project/kip8test'
OK = True


def rep(path, old, new, cnt=1):
    global OK
    src = io.open(path, encoding='utf-8').read()
    n = src.count(old)
    if n != cnt:
        print('FAIL %s: найдено %d (ожидалось %d):\n%s' %
              (path.split('/')[-1], n, cnt, old[:80]))
        OK = False
        return
    src = src.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('OK   %s' % path.split('/')[-1])


# 1. Комментарий в index.html — без литерала ts-calc-field
rep(ROOT + '/index.html',
    '                         блок оформлен как панель\n'
    '                         произвольного расчёта (Task 494: контейнер\n'
    '                         ts-calc-panel, поля ts-calc-field), но с эффектом\n'
    '                         УГЛУБЛЕНИЯ, а не выступа — модификатор\n',
    '                         блок оформлен как панель\n'
    '                         произвольного расчёта (Task 494: тот же контейнер\n'
    '                         и те же поля), но с эффектом\n'
    '                         УГЛУБЛЕНИЯ, а не выступа — модификатор\n')

# 2а. tablePanelChunk — от начала тега '<div' (класс до id)
rep(ROOT + '/tests/test-task495.js',
    "// Чанк новой панели таблицы: от id=\"tempTableFormPanel\" до кнопки\n"
    "// «Рассчитать» (onclick=\"calcTempSensor()\") — панель закрывается ДО\n"
    "// кнопки (кнопка вне панели)\n"
    "function tablePanelChunk() {\n"
    "    const iPanel = INDEX_SRC.indexOf('id=\"tempTableFormPanel\"');\n"
    "    const iBtn = INDEX_SRC.indexOf('onclick=\"calcTempSensor()\"');\n"
    "    if (iPanel === -1 || iBtn === -1 || iBtn < iPanel) return null;\n"
    "    return INDEX_SRC.slice(iPanel, iBtn);\n"
    "}\n",
    "// Чанк новой панели таблицы: от начала тега '<div' (класс-атрибут\n"
    "// стоит ДО id в теге) до кнопки «Рассчитать» — панель закрывается\n"
    "// ДО кнопки (кнопка вне панели)\n"
    "function tablePanelChunk() {\n"
    "    const iId = INDEX_SRC.indexOf('id=\"tempTableFormPanel\"');\n"
    "    const iPanel = iId === -1 ? -1 : INDEX_SRC.lastIndexOf('<div', iId);\n"
    "    const iBtn = INDEX_SRC.indexOf('onclick=\"calcTempSensor()\"');\n"
    "    if (iPanel === -1 || iBtn === -1 || iBtn < iPanel) return null;\n"
    "    return INDEX_SRC.slice(iPanel, iBtn);\n"
    "}\n")

# 2б. Кнопка — вне панели: порядок последнего </div> и <button>
rep(ROOT + '/tests/test-task495.js',
    "        const c = tablePanelChunk();\n"
    "        // до кнопки «Рассчитать» панель закрыта: 2 подписи + flex-строка\n"
    "        // + закрытие самой панели = 4 </div>, кнопка НЕ внутри панели\n"
    "        assertEqual(c.split('</div>').length - 1, 4,\n"
    "            'панель закрыта ДО кнопки (4 закрытия: 2 подписи + flex + сама панель)');\n"
    "        assertFalse(c.indexOf('<button') !== -1, 'кнопки внутри панели НЕТ');\n"
    "        assertTrue(c.indexOf('calcTempSensor()') === -1,\n"
    "            'onclick-обработчик не внутри панели');\n",
    "        const c = tablePanelChunk();\n"
    "        // до кнопки «Рассчитать» панель закрыта: 2 подписи + flex-строка\n"
    "        // + закрытие самой панели = 4 </div>; последняя </div> — ДО <button\n"
    "        assertEqual(c.split('</div>').length - 1, 4,\n"
    "            'панель закрыта ДО кнопки (4 закрытия: 2 подписи + flex + сама панель)');\n"
    "        assertTrue(c.lastIndexOf('</div>') < c.indexOf('<button'),\n"
    "            'кнопка «Рассчитать» начинается ПОСЛЕ закрытия панели');\n")

# 2в. calcTempSensor показывает результаты: display = 'block'
rep(ROOT + '/tests/test-task495.js',
    "        assertEqual(res.style.display, '', 'результаты показаны (display снят не был)');\n",
    "        assertEqual(res.style.display, 'block',\n"
    "            'результаты показаны (calcTempSensor ставит block)');\n")

print('RESULT: %s' % ('OK' if OK else 'FAIL'))
sys.exit(0 if OK else 1)
