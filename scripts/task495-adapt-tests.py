#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 495 — kip8test: адаптация тестов 372/373/494 под удаление чипа
«Тип датчика» и новую панель таблицы ts-calc-inset.

- test-task372.js: (а) SRC-структура страницы — чип удалён, панель
  ts-calc-inset на месте; (б) CSS-список — .ts-view-chip снят; (в) VM —
  чип не создаётся (els без ключа).
- test-task373.js: (а) grabFn('openTempSensor') без чипа; (б) VM-чип —
  заменён на проверку отсутствия ключа в els.
- test-task494.js: panelChunk — конец чанка теперь id="tempTableFormPanel"
  (панель таблицы), чтобы счёт полей ts-calc-field в ПАНЕЛИ произвольного
  расчёта остался ровно 2 (поля min/max/шаг получили класс в Task 495).
"""
import io
import sys

T = '/home/z/my-project/kip8test/tests'
OK = True


def rep(fname, old, new):
    global OK
    p = T + '/' + fname
    src = io.open(p, encoding='utf-8').read()
    n = src.count(old)
    if n != 1:
        print('FAIL %s: фрагмент найден %d раз (ожидался 1):\n%s' %
              (fname, n, old[:100]))
        OK = False
        return
    src = src.replace(old, new)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  %-18s замена OK (%d → %d симв.)' %
          (fname, len(old), len(new)))


# --- test-task372.js --------------------------------------------------
# (а) SRC-структура: чип удалён, панель-углубление на месте
rep('test-task372.js',
    "        assertTrue(b.indexOf('id=\"tempSensorViewChip\"') !== -1, 'чип выбранного датчика');\n",
    "        assertFalse(b.indexOf('id=\"tempSensorViewChip\"') !== -1,\n"
    "            'Task 495: чип типа датчика удалён из блока ввода');\n"
    "        assertTrue(b.indexOf('ts-calc-inset') !== -1,\n"
    "            'Task 495: блок таблицы — панель с углублением');\n")

# (б) CSS-список: .ts-view-chip снят (мёртвый код)
rep('test-task372.js',
    "        for (const cls of ['.ts-cards-grid', '.ts-card {', '.ts-card-name', '.ts-card-fav-btn',\n"
    "                           '.ts-tabs', '#tempSensorFavBtn', '.ts-view-chip', '.ts-calc-panel']) {\n"
    "            assertTrue(INDEX_SRC.indexOf(cls) !== -1, 'есть правило ' + cls);\n"
    "        }\n",
    "        for (const cls of ['.ts-cards-grid', '.ts-card {', '.ts-card-name', '.ts-card-fav-btn',\n"
    "                           '.ts-tabs', '#tempSensorFavBtn', '.ts-calc-panel',\n"
    "                           '.ts-calc-panel.ts-calc-inset']) {\n"
    "            assertTrue(INDEX_SRC.indexOf(cls) !== -1, 'есть правило ' + cls);\n"
    "        }\n"
    "        // Task 495: правила чипа сняты как неиспользуемые\n"
    "        assertTrue(INDEX_SRC.indexOf('.ts-view-chip') === -1,\n"
    "            'Task 495: CSS-правила чипа удалены');\n")

# (в) VM: чип не создаётся
rep('test-task372.js',
    "        assertTrue(vmw.els['tempSensorViewChip'].innerHTML.indexOf('50М (Cu50)') !== -1, 'чип: имя');\n"
    "        assertTrue(vmw.els['tempSensorViewChip'].innerHTML.indexOf('R₀ = 50 Ом') !== -1, 'чип: meta');\n"
    "        assertTrue(vmw.els['tempSensorViewChip'].innerHTML.indexOf('ts-card-badge') === -1, 'Task 373: чип без бейджа');\n",
    "        assertFalse('tempSensorViewChip' in vmw.els,\n"
    "            'Task 495: чип удалён — openTempSensor его не трогает');\n")

# --- test-task373.js --------------------------------------------------
# (а) openTempSensor не заполняет чип
rep('test-task373.js',
    "        // чип страницы датчика — без бейджа\n"
    "        const fn = grabFn('openTempSensor');\n"
    "        assertTrue(fn.indexOf('ts-view-chip-name') !== -1, 'чип: имя');\n"
    "        assertTrue(fn.indexOf('ts-card-badge') === -1, 'чип: бейджа нет');\n",
    "        // Task 495: чип удалён — openTempSensor его не заполняет\n"
    "        const fn = grabFn('openTempSensor');\n"
    "        assertTrue(fn.indexOf('ts-view-chip-name') === -1,\n"
    "            'Task 495: заполнение чипа удалено из openTempSensor');\n"
    "        assertTrue(fn.indexOf('ts-card-badge') === -1, 'бейджей нет');\n")

# (б) VM: чип не создаётся
rep('test-task373.js',
    "        // чип: имя и электроды, без бейджа\n"
    "        const chip = vmw.els['tempSensorViewChip'].innerHTML;\n"
    "        assertTrue(chip.indexOf('ТХК (L)') !== -1, 'чип: имя');\n"
    "        assertTrue(chip.indexOf('хромель-копель') !== -1, 'чип: электроды');\n"
    "        assertTrue(chip.indexOf('ts-card-badge') === -1, 'чип: без бейджа');\n",
    "        // Task 495: чип удалён — ключа в els нет\n"
    "        assertFalse('tempSensorViewChip' in vmw.els,\n"
    "            'Task 495: чип удалён из блока ввода');\n")

# --- test-task494.js --------------------------------------------------
rep('test-task494.js',
    "// Чанк статичной панели: от id=\"tempCustomCalcPanel\" до формы выбора\n"
    "function panelChunk() {\n"
    "    const iPanel = INDEX_SRC.indexOf('id=\"tempCustomCalcPanel\"');\n"
    "    const iRange = INDEX_SRC.indexOf('id=\"temp_sensor_min\"');\n"
    "    if (iPanel === -1 || iRange === -1) return null;\n"
    "    return INDEX_SRC.slice(iPanel, iRange);\n"
    "}\n",
    "// Чанк статичной панели: от id=\"tempCustomCalcPanel\" до панели\n"
    "// таблицы Task 495 (id=\"tempTableFormPanel\") — поля таблицы\n"
    "// (min/max/шаг) получили класс ts-calc-field в Task 495, поэтому\n"
    "// конец чанка перенесён с формы выбора на новую панель.\n"
    "function panelChunk() {\n"
    "    const iPanel = INDEX_SRC.indexOf('id=\"tempCustomCalcPanel\"');\n"
    "    const iRange = INDEX_SRC.indexOf('id=\"tempTableFormPanel\"');\n"
    "    if (iPanel === -1 || iRange === -1) return null;\n"
    "    return INDEX_SRC.slice(iPanel, iRange);\n"
    "}\n")

print('RESULT: %s' % ('OK' if OK else 'FAIL'))
sys.exit(0 if OK else 1)
