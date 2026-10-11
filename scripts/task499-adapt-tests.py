#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 499 (kip8test): адаптация существующих тестов под изменения.

Изменения заявки:
  (1) подсказки диапазонов НСХ — ПЛЕЙСХОЛДЕРЫ полей ППР (бледный
      текст) вместо предложений «Например: 55» / «Например: 61,8» /
      «Например: 2,2»; div-подсказки ts-calc-range (Task 498) убраны;
  (2) диапазон Cu α = 0,00428 (50М/100М) расширен до −180…+200
      (таблица А.3 / формула 5.2.3 ГОСТ 6651-2009);
  (3) calcCuResistance ниже 0 °C для α = 0,00428 — по ГОСТ 5.2.3
      (R(−50) Cu50 = 39,2275, а не линейные 39,3).

Адаптируемые файлы (до бампа версий — по актуальному коду):
  test-rtd.js        — R(−50) Cu 0,00428: 39,3 → 39,2275 (ГОСТ 5.2.3).
  test-task371.js    — SRC «Например:» → плейсхолдеры 499; диапазоны
                       каталога (−180…200); VM R(−50) → 39,2275;
                       HTML панели без «Например:».
  test-task372.js    — карточки: добавлен диапазон −180…200 (α 0,00428).
  test-task373.js    — SRC и VM «Например:» → плейсхолдеры 499.
  test-task494.js    — панель и openTempSensor: «Например:» →
                       плейсхолдеры 499.
  test-task498.js    — каталог (rng499), подсказки → плейсхолдеры,
                       CSS (ts-calc-range удалён), VM-значения.
"""
import io

T = '/home/z/my-project/kip8test/tests/'


def apply(path, edits):
    s = io.open(path, encoding='utf-8').read()
    for name, old, new in edits:
        n = s.count(old)
        assert n == 1, 'ЯКОРЬ %s (%s): вхождений %d (ожидалось 1)' % (name, path, n)
        s = s.replace(old, new)
        print('  OK %s' % name)
    io.open(path, 'w', encoding='utf-8').write(s)


# ------------------------------------------------------- test-rtd.js --
apply(T + 'test-rtd.js', [
    ('rtd: describe-заголовок',
     "describe('calcCuResistance — медные ТС (линейная характеристика)', () => {\n\n    // Формула: R(t) = R₀·(1 + α·t)",
     "describe('calcCuResistance — медные ТС (ГОСТ 6651-2009)', () => {\n\n    // Формула: R(t) = R₀·(1 + α·t) при t ≥ 0; ниже 0 °C для α = 0,00428 —\n    // формула 5.2.3 ГОСТ 6651-2009: R(t) = R₀·[1 + At + Bt(t+6,7) + Ct³]\n    // (Task 499: R(−50) = 39,2275 для Cu50 — раньше линейно 39,3)"),
    ('rtd: R(-50) по ГОСТ 5.2.3',
     """    test('Cu50 (α=0.00428): R(-50°C) = 39.3 Ом', () => {
        // 50·(1 + 0.00428·(-50)) = 50·0.786 = 39.3
        const r = fns.calcCuResistance(-50, 50, 0.00428);
        assertApprox(r, 39.3, 0.01);
    });""",
     """    test('Cu50 (α=0.00428): R(-50°C) = 39.2275 Ом (ГОСТ 5.2.3, Task 499)', () => {
        // Task 499: ниже 0 °C — формула 5.2.3 ГОСТ 6651-2009
        // 50·(1 + 4.28e-3·(-50) - 6.2032e-7·(-50)·(-43.3) + 8.5154e-10·(-50)³)
        // = 50·0.784550… = 39.2275 (таблица А.3: 78.46 на 100 Ом)
        const r = fns.calcCuResistance(-50, 50, 0.00428);
        assertApprox(r, 39.2275, 0.001);
    });"""),
])

# --------------------------------------------------- test-task371.js --
apply(T + 'test-task371.js', [
    ('371: SRC плейсхолдеры 499',
     """        assertTrue(op.indexOf("vInp.placeholder='Например: 61,8'") !== -1,
            'openTempSensor: пример ТС');
        assertTrue(op.indexOf("vInp.placeholder='Например: 2,2'") !== -1,
            'openTempSensor: пример ТП');""",
     """        // Task 499: подсказки диапазонов — плейсхолдеры полей
        assertTrue(op.indexOf('tInp.placeholder=fmtI499(rng499.min)') !== -1,
            'openTempSensor: плейсхолдер температуры (Task 499)');
        assertTrue(op.indexOf('vInp.placeholder=fmtM499(vmin499)') !== -1,
            'openTempSensor: плейсхолдер значения (Task 499)');"""),
    ('371: диапазоны каталога (−180…200)',
     """    test('Диапазоны НСХ: Cu −50…200, Pt −200…850, ТП по типам', () => {
        // Task 372: единый источник диапазонов — каталог карточек
        const fn = grabFn('getTempSensorCatalog');
        assertTrue(fn.indexOf('{min:-50,max:200}') !== -1, 'Cu: −50…200');""",
     """    test('Диапазоны НСХ: Cu 0,00428 −180…200 (Task 499), Pt −200…850, ТП по типам', () => {
        // Task 372: единый источник диапазонов — каталог карточек;
        // Task 499: Cu α = 0,00428 — −180…+200 (ГОСТ 6651-2009, А.3/5.2.3)
        const fn = grabFn('getTempSensorCatalog');
        assertTrue(fn.indexOf('{min:-180,max:200}') !== -1, 'Cu 0,00428: −180…200 (Task 499)');
        assertTrue(fn.indexOf('{min:-50,max:200}') !== -1, 'Cu 0,00426: −50…200');"""),
    ('371: VM границы НСХ по ГОСТ',
     """    test('Cu50: границы НСХ −50…200 → 39,3 / 92,8 Ом', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '-50';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '39,3', 'R(−50)');
        vmw.els['tempQueryTemp'].value = '200';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '92,8', 'R(200)');
    });""",
     """    test('Cu50: границы НСХ −180…200 → 10,2642 / 92,8 Ом (ГОСТ 5.2.3, Task 499)', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '-50';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '39,2275', 'R(−50) по ГОСТ 5.2.3');
        vmw.els['tempQueryTemp'].value = '-180';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '10,2642', 'R(−180) — нижняя граница А.3');
        vmw.els['tempQueryTemp'].value = '200';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '92,8', 'R(200)');
    });"""),
    ('371: HTML панели без «Например:»',
     """        const panel = INDEX_SRC.slice(iPanel, iRange);
        assertTrue(panel.indexOf('placeholder="Например: 55"') !== -1, 'пример температуры общий');
        assertTrue(panel.indexOf('placeholder="Например: 61,8"') !== -1, 'пример ТС (дефолт)');
        assertTrue(panel.indexOf('Сопротивление R(t), Ом') !== -1, 'подпись ТС (дефолт)');
        const op = grabFn('openTempSensor');
        assertTrue(op.indexOf("Термо-ЭДС E(t), мВ") !== -1, 'подпись ТП подставляется');
        assertTrue(op.indexOf("Например: 2,2") !== -1, 'пример ТП подставляется');""",
     """        const panel = INDEX_SRC.slice(iPanel, iRange);
        // Task 499: «Например: …» в полях заменены диапазонами НСХ
        // (плейсхолдеры, бледный текст)
        assertTrue(panel.indexOf('Например:') === -1, 'Task 499: предложений «Например:» нет');
        assertTrue(panel.indexOf('Task 499 (заявка: «подсказки диапазонов') !== -1,
            'комментарий Task 499 в панели');
        assertTrue(panel.indexOf('Сопротивление R(t), Ом') !== -1, 'подпись ТС (дефолт)');
        const op = grabFn('openTempSensor');
        assertTrue(op.indexOf("Термо-ЭДС E(t), мВ") !== -1, 'подпись ТП подставляется');
        assertTrue(op.indexOf('vInp.placeholder=fmtM499(vmin499)') !== -1,
            'Task 499: диапазон подставляется прямо в поле');"""),
])

# --------------------------------------------------- test-task372.js --
apply(T + 'test-task372.js', [
    ('372: карточки Cu −180…200',
     """        assertTrue(rtd.indexOf('НСХ: −50…200 °C') !== -1, 'диапазон на карточке Cu (минус U+2212)');""",
     """        assertTrue(rtd.indexOf('НСХ: −50…200 °C') !== -1, 'диапазон Cu α = 0,00426 (минус U+2212)');
        assertTrue(rtd.indexOf('НСХ: −180…200 °C') !== -1,
            'Task 499: Cu α = 0,00428 — −180…200 (ГОСТ 6651-2009, А.3)');"""),
])

# --------------------------------------------------- test-task373.js --
apply(T + 'test-task373.js', [
    ('373: SRC подсказки 499',
     """        assertTrue(fn.indexOf('Сопротивление R(t), Ом') !== -1, 'подпись ТС');
        assertTrue(fn.indexOf('Термо-ЭДС E(t), мВ') !== -1, 'подпись ТП');
        assertTrue(fn.indexOf('Например: 61,8') !== -1, 'пример ТС');
        assertTrue(fn.indexOf('Например: 2,2') !== -1, 'пример ТП');""",
     """        assertTrue(fn.indexOf('Сопротивление R(t), Ом') !== -1, 'подпись ТС');
        assertTrue(fn.indexOf('Термо-ЭДС E(t), мВ') !== -1, 'подпись ТП');
        // Task 499: подсказки диапазонов — плейсхолдеры полей
        assertTrue(fn.indexOf('tInp.placeholder=fmtI499(rng499.min)') !== -1,
            'плейсхолдер температуры (Task 499)');
        assertTrue(fn.indexOf('vInp.placeholder=fmtM499(vmin499)') !== -1,
            'плейсхолдер значения (Task 499)');"""),
    ('373: VM плейсхолдер ТП',
     """        assertEqual(vmw.els['tempQueryVal'].placeholder, 'Например: 2,2', 'пример ТП');""",
     """        assertEqual(vmw.els['tempQueryVal'].placeholder, '−9,4881…66,4659 мВ',
            'Task 499: диапазон НСХ L в поле (бледный плейсхолдер)');"""),
    ('373: VM плейсхолдер ТС',
     """        assertEqual(vmw.els['tempQueryVal'].placeholder, 'Например: 61,8', 'пример ТС');""",
     """        assertEqual(vmw.els['tempQueryVal'].placeholder, '10,2642…92,8 Ом',
            'Task 499: диапазон НСХ Cu50 в поле (−180…+200, ГОСТ 5.2.3)');"""),
])

# --------------------------------------------------- test-task494.js --
apply(T + 'test-task494.js', [
    ('494: панель без «Например:»',
     """            'Температура (°C)',
            'Сопротивление R(t), Ом',
            'placeholder="Например: 55"',
            'placeholder="Например: 61,8"'
        ]) {""",
     """            'Температура (°C)',
            'Сопротивление R(t), Ом',
            'Task 499 (заявка: «подсказки диапазонов',
            'бледным текстом'
        ]) {"""),
    ('494: openTempSensor плейсхолдеры 499',
     """        assertTrue(fn.indexOf("vInp.placeholder='Например: 61,8'") !== -1,
            'пример ТС подставляется');
        assertTrue(fn.indexOf("vInp.placeholder='Например: 2,2'") !== -1,
            'пример ТП подставляется');""",
     """        // Task 499: подсказки диапазонов — прямо в поля (плейсхолдеры)
        assertTrue(fn.indexOf('tInp.placeholder=fmtI499(rng499.min)') !== -1,
            'плейсхолдер температуры (Task 499)');
        assertTrue(fn.indexOf('vInp.placeholder=fmtM499(vmin499)') !== -1,
            'плейсхолдер значения (Task 499)');"""),
])

# --------------------------------------------------- test-task498.js --
apply(T + 'test-task498.js', [
    ('498: каталог rng499',
     """    test('Каталог: пределы НСХ НЕ менялись (сверка подтвердила)', () => {
        const fn = grabFn('getTempSensorCatalog');
        assertTrue(fn !== null, 'функция есть');
        assertTrue(fn.indexOf('range:isCu?{min:-50,max:200}:{min:-200,max:850}') !== -1,
            'Cu −50…+200 (ГОСТ 6651-2009, приложение Б), Pt −200…+850 (А.1/А.2)');
        assertTrue(fn.indexOf('K:{mat:\\'хромель-алюмель\\',r:[-270,1372]}') !== -1, 'K: −270…1372');
        assertTrue(fn.indexOf('L:{mat:\\'хромель-копель\\',r:[-200,800]}') !== -1, 'L: −200…800');
        assertTrue(fn.indexOf('B:{mat:\\'платинородий-платинородий\\',r:[0,1820]}') !== -1, 'B: 0…1820');
        // комментарий сверки — НАД функцией (в INDEX_SRC, вне grabFn)
        const iCat = INDEX_SRC.indexOf('function getTempSensorCatalog(');
        assertTrue(INDEX_SRC.slice(Math.max(0, iCat - 1200), iCat).indexOf('пределы НСХ каталога СВЕРЕНЫ') !== -1,
            'комментарий сверки Task 498 перед каталогом');
    });""",
     """    test('Каталог: пределы НСХ (Task 499: Cu 0,00428 — −180…+200)', () => {
        const fn = grabFn('getTempSensorCatalog');
        assertTrue(fn !== null, 'функция есть');
        // Task 499: Cu α = 0,00428 расширен до −180…+200 (таблица А.3 /
        // формула 5.2.3 ГОСТ 6651-2009); 0,00426 — прежние −50…+200;
        // Pt/ТП — без изменений
        assertTrue(fn.indexOf('rng499=isCu?((Math.abs(sd.alpha-0.00428)<1e-9)?{min:-180,max:200}:{min:-50,max:200}):{min:-200,max:850}') !== -1,
            'Cu 0,00428: −180…+200; Cu 0,00426: −50…+200; Pt: −200…+850');
        assertTrue(fn.indexOf('K:{mat:\\'хромель-алюмель\\',r:[-270,1372]}') !== -1, 'K: −270…1372');
        assertTrue(fn.indexOf('L:{mat:\\'хромель-копель\\',r:[-200,800]}') !== -1, 'L: −200…800');
        assertTrue(fn.indexOf('B:{mat:\\'платинородий-платинородий\\',r:[0,1820]}') !== -1, 'B: 0…1820');
        // комментарии сверки 498 + 499 — НАД функцией (окно расширено:
        // перед каталогом теперь 3 комментария — 491/498/499)
        const iCat = INDEX_SRC.indexOf('function getTempSensorCatalog(');
        assertTrue(INDEX_SRC.slice(Math.max(0, iCat - 2600), iCat).indexOf('пределы НСХ каталога СВЕРЕНЫ') !== -1,
            'комментарий сверки Task 498 перед каталогом');
        assertTrue(INDEX_SRC.slice(Math.max(0, iCat - 2600), iCat).indexOf('Task 499 (заявка: «проверь у 50М') !== -1,
            'комментарий Task 499 перед каталогом');
    });"""),
    ('498: подсказки в полях (плейсхолдеры)',
     """    test('openTempSensor: заполняет подсказки пределов обоих полей', () => {
        const fn = grabFn('openTempSensor');
        assertTrue(fn.indexOf("tempQueryTempRange") !== -1, 'элемент пределов °C');
        assertTrue(fn.indexOf("tempQueryValRange") !== -1, 'элемент пределов Ом/мВ');
        assertTrue(fn.indexOf('tempCalcForwardValue(rng498.min)') !== -1,
            'значения на границах — через НСХ (единый источник)');
        assertTrue(fn.indexOf('getTempSensorRange()') !== -1, 'границы — из каталога');
        assertTrue(fn.indexOf("'Ом':'мВ'") !== -1, 'единица по типу датчика');
    });""",
     """    test('openTempSensor: подсказки пределов — ПЛЕЙСХОЛДЕРЫ полей (Task 499)', () => {
        const fn = grabFn('openTempSensor');
        // Task 499: подсказки диапазонов вписаны непосредственно в поля
        // ввода (бледный текст), div-подсказки 498 удалены
        assertTrue(fn.indexOf('tempQueryTempRange') === -1, 'div-подсказка 498 удалена (°C)');
        assertTrue(fn.indexOf('tempQueryValRange') === -1, 'div-подсказка 498 удалена (Ом/мВ)');
        assertTrue(fn.indexOf('Например:') === -1, 'предложения «Например:» убраны');
        assertTrue(fn.indexOf('tInp.placeholder=fmtI499(rng499.min)') !== -1,
            'плейсхолдер температуры — из каталога');
        assertTrue(fn.indexOf('tempCalcForwardValue(rng499.min)') !== -1,
            'значения на границах — через НСХ (единый источник)');
        assertTrue(fn.indexOf('getTempSensorRange()') !== -1, 'границы — из каталога');
        assertTrue(fn.indexOf("'Ом':'мВ'") !== -1, 'единица по типу датчика');
    });"""),
    ('498: HTML панели без div-подсказок',
     """    test('HTML: подсказки под обоими полями ППР (порядок)', () => {
        const p = panelChunk();
        assertTrue(p !== null, 'панель ППР найдена');
        assertEqual(p.split('class="ts-calc-range"').length - 1, 2,
            'ровно ДВА div-подсказки (без учёта комментария)');
        const iT = p.indexOf('id="tempQueryTemp"');
        const iTR = p.indexOf('id="tempQueryTempRange"');
        const iL = p.indexOf('id="tempQueryValLabel"');
        const iV = p.indexOf('id="tempQueryVal"');
        const iVR = p.indexOf('id="tempQueryValRange"');
        assertTrue(iT !== -1 && iTR !== -1 && iL !== -1 && iV !== -1 && iVR !== -1,
            'все элементы панели на месте');
        assertTrue(iT < iTR && iTR < iL, 'подсказка °C — ПОД полем температуры');
        assertTrue(iV < iVR, 'подсказка Ом/мВ — ПОД полем значения');
        // инварианты Task 494/496 не задеты
        assertEqual(p.split('class="scale-field ts-calc-field"').length - 1, 2,
            'оба поля остались ts-calc-field (Task 494)');
        assertEqual(p.split('onkeydown="tempQueryEnterBlur(event,this)"').length - 1, 2,
            'Enter-закрытие клавиатуры живо (Task 496)');
    });""",
     """    test('HTML: подсказки в полях, div-подсказок нет (Task 499)', () => {
        const p = panelChunk();
        assertTrue(p !== null, 'панель ППР найдена');
        // Task 499: подсказки — плейсхолдеры полей (заполняет
        // openTempSensor), div-подсказки под полями удалены
        assertEqual(p.split('ts-calc-range').length - 1, 0,
            'div-подсказок ts-calc-range нет (комментарий — без класса)');
        assertEqual(p.split('id="tempQueryTempRange"').length - 1, 0, 'id tempQueryTempRange удалён');
        assertEqual(p.split('id="tempQueryValRange"').length - 1, 0, 'id tempQueryValRange удалён');
        assertTrue(p.indexOf('placeholder="Например:') === -1,
            'Task 499: статических «Например:» в полях нет');
        assertTrue(p.indexOf('Task 499 (заявка: «подсказки диапазонов') !== -1,
            'комментарий Task 499 в панели');
        const iT = p.indexOf('id="tempQueryTemp"');
        const iL = p.indexOf('id="tempQueryValLabel"');
        const iV = p.indexOf('id="tempQueryVal"');
        assertTrue(iT !== -1 && iL !== -1 && iV !== -1, 'все элементы панели на месте');
        assertTrue(iT < iL && iL < iV, 'порядок: температура → подпись → значение');
        // инварианты Task 494/496 не задеты
        assertEqual(p.split('class="scale-field ts-calc-field"').length - 1, 2,
            'оба поля остались ts-calc-field (Task 494)');
        assertEqual(p.split('onkeydown="tempQueryEnterBlur(event,this)"').length - 1, 2,
            'Enter-закрытие клавиатуры живо (Task 496)');
    });"""),
    ('498: CSS — ts-calc-range удалён',
     """    test('CSS: .ts-calc-range — стиль подсказок (тёмная + светлая)', () => {
        assertTrue(INDEX_SRC.indexOf('.ts-calc-range { font-size: 11px;') !== -1,
            'базовое правило .ts-calc-range');
        assertTrue(INDEX_SRC.indexOf('.ts-calc-panel .ts-calc-range:last-child { margin-bottom: 0; }') !== -1,
            'нижний отступ последней подсказки убран');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ts-calc-range') !== -1,
            'светлая тема');
    });""",
     """    test('CSS: .ts-calc-range удалён — подсказки в полях (Task 499)', () => {
        // Task 499: правила .ts-calc-range убраны, бледный цвет
        // подсказок — прежний ::placeholder полей (Task 494)
        assertTrue(INDEX_SRC.indexOf('.ts-calc-range {') === -1,
            'правило .ts-calc-range удалено');
        assertTrue(INDEX_SRC.indexOf('ts-calc-range') === -1,
            'упоминаний ts-calc-range в CSS нет (ts-card-range не задет)');
        assertTrue(INDEX_SRC.indexOf('.ts-calc-field::placeholder { color: rgba(255, 255, 255, 0.4); font-weight: 500; }') !== -1,
            'бледный плейсхолдер полей ППР (Task 494, жив)');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ts-calc-field::placeholder { color: rgba(20, 20, 19, 0.45); }') !== -1,
            'бледный плейсхолдер в светлой теме (жив)');
    });"""),
    ('498: VM Cu50 placeholders',
     """    test('Cu50 (0,00428): «−50…200 °C» + «39,3…92,8 Ом»', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '−50…200 °C',
            'пределы температуры в °C (минус — типографский)');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '39,3…92,8 Ом',
            'пределы сопротивления в Ом');
    });""",
     """    test('Cu50 (0,00428): плейсхолдеры «−180…200 °C» + «10,2642…92,8 Ом»', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.els['tempQueryTemp'].placeholder, '−180…200 °C',
            'Task 499: пределы температуры в °C в поле (минус — типографский)');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '10,2642…92,8 Ом',
            'Task 499: пределы сопротивления в Ом в поле (−180 по ГОСТ 5.2.3)');
    });"""),
    ('498: VM 1426/Cu100 placeholders',
     """    test('Cu50 (0,00426) и Cu100: значения от α и R₀', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1426');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '39,35…92,6 Ом',
            'Cu50 α = 0,00426');
        vmw.api.openTempSensor('cu100_1428');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '78,6…185,6 Ом',
            'Cu100 α = 0,00428 (R₀ = 100)');
    });""",
     """    test('Cu50 (0,00426) и Cu100: значения от α и R₀ (плейсхолдеры)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1426');
        assertEqual(vmw.els['tempQueryTemp'].placeholder, '−50…200 °C',
            'Cu50 α = 0,00426: диапазон прежний (плейсхолдер)');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '39,35…92,6 Ом',
            'Cu50 α = 0,00426 (линейная НСХ)');
        vmw.api.openTempSensor('cu100_1428');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '20,5284…185,6 Ом',
            'Cu100 α = 0,00428 (R₀ = 100; −180 → 20,5284 по ГОСТ 5.2.3)');
    });"""),
    ('498: VM 100П placeholders',
     """    test('100П: «−200…850 °C» + «17,2444…395,16 Ом» (новая формула!)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1391');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '−200…850 °C',
            'пределы Pt');
        // 17,2444 (а не 18,29 — старая формула без члена C) — А.2 ГОСТ
        assertEqual(vmw.els['tempQueryValRange'].textContent, '17,2444…395,16 Ом',
            'пределы 100П по НСХ с C-членом');
    });""",
     """    test('100П: плейсхолдеры «−200…850 °C» + «17,2444…395,16 Ом»', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1391');
        assertEqual(vmw.els['tempQueryTemp'].placeholder, '−200…850 °C',
            'пределы Pt (плейсхолдер)');
        // 17,2444 (а не 18,29 — старая формула без члена C) — А.2 ГОСТ
        assertEqual(vmw.els['tempQueryVal'].placeholder, '17,2444…395,16 Ом',
            'пределы 100П по НСХ с C-членом (плейсхолдер)');
    });"""),
    ('498: VM Pt100 placeholders',
     """    test('Pt100 (IEC): «18,5201…390,48 Ом» (ветка не менялась)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1385');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '18,5201…390,48 Ом',
            'пределы Pt100 (IEC)');
    });""",
     """    test('Pt100 (IEC): «18,5201…390,48 Ом» (ветка не менялась)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1385');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '18,5201…390,48 Ом',
            'пределы Pt100 (IEC) — плейсхолдер');
    });"""),
    ('498: VM K placeholders',
     """    test('ТХА (K): °C + мВ; минус — типографский', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('tc_K');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '−270…1372 °C',
            'пределы K в °C');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '−6,4577…54,8864 мВ',
            'пределы термо-ЭДС в мВ');
    });""",
     """    test('ТХА (K): °C + мВ в полях; минус — типографский', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('tc_K');
        assertEqual(vmw.els['tempQueryTemp'].placeholder, '−270…1372 °C',
            'пределы K в °C — плейсхолдер');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '−6,4577…54,8864 мВ',
            'пределы термо-ЭДС в мВ — плейсхолдер');
    });"""),
    ('498: VM B placeholders',
     """    test('ТПР (B): нижний предел 0 → «0…13,8203 мВ»', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('tc_B');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '0…1820 °C',
            'пределы B в °C');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '0…13,8203 мВ',
            'пределы B в мВ (E(0) = 0)');
    });""",
     """    test('ТПР (B): нижний предел 0 → «0…13,8203 мВ» в поле', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('tc_B');
        assertEqual(vmw.els['tempQueryTemp'].placeholder, '0…1820 °C',
            'пределы B в °C — плейсхолдер');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '0…13,8203 мВ',
            'пределы B в мВ (E(0) = 0) — плейсхолдер');
    });"""),
    ('498: VM смена датчика placeholders',
     """    test('Смена датчика обновляет подсказки', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '39,3…92,8 Ом', 'до смены');
        vmw.api.openTempSensor('pt100_1391');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '17,2444…395,16 Ом', 'после смены');""",
     """    test('Смена датчика обновляет подсказки-плейсхолдеры', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '10,2642…92,8 Ом', 'до смены');
        vmw.api.openTempSensor('pt100_1391');
        assertEqual(vmw.els['tempQueryVal'].placeholder, '17,2444…395,16 Ом', 'после смены');"""),
    ('498: заголовок describe-блока VM',
     """describe('Task 498 — VM: пределы в полях ввода произвольного расчёта', () => {""",
     """describe('Task 498/499 — VM: пределы в полях ППР (плейсхолдеры, Task 499)', () => {"""),
])

print('Task 499: тесты адаптированы.')
