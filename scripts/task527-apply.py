#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 527 — применяется к kip8test/index.html.
Заявка: «В разделе Главная / Инженерные калькуляторы / Геометрия, на
некоторых геометрических фигурах линии и цифры пересекаются и
накладываются друг на друга, поправь, и расчётные данные должны
отображаться на картинке под геометрической фигурой, поэтому блок с
фигурой сделай немного больше.»

Правки:
  CSS: рамка 320→350px («немного больше»); классы .gf-sep/.gf-val;
       HTML-блок .geo-fig-res* УБРАН — данные теперь в SVG; анимация
       и prefers-reduced-motion — на .gf-resg.
  HTML: 6 рамок — viewBox 240×240 (gh 240×257, 3 строки), div
       #xxFigRes удалён; комментарии дополнены строкой Task 527.
  JS:  gfDimH — параметр labelPos ('below' — подпись под линией);
       gfDimV — отступ подписи 5→9, короткий размер: подпись вынесена
       за выносные линии; НОВАЯ gfDataZone — живой расчёт ВНУТРИ
       картинки под фигурой; geoFigBuild добавляет зону; geoFigRender
       без resEl; подписи выведены из фигур: круг/сфера/кольцо D —
       размер ПОД фигурой, кольцо d — подпись НАД фигурой, конус L —
       у ЛЕВОГО ребра.
Каждая замена проверяется на точное число вхождений.
"""
import io
import sys

PATH = '/home/z/my-project/kip8test/index.html'
src = io.open(PATH, encoding='utf-8').read()
edits = []


def rep(old, new, n=1, label=''):
    global src
    cnt = src.count(old)
    if cnt != n:
        print('ОШИБКА [%s]: найдено %d, ожидается %d' % (label, cnt, n))
        sys.exit(1)
    src = src.replace(old, new)
    edits.append(label)


# ============ 1. CSS ============

# 1.1 Рамка больше: 320 → 350
rep('        width: min(100%, 320px); box-sizing: border-box;',
    '        width: min(100%, 350px); box-sizing: border-box;',
    1, 'CSS: ширина рамки 350px')

# 1.2 Классы зоны расчёта в SVG (после .gf-dot)
rep("""    .geo-fig-svg .gf-dot   { fill: var(--gf-ink); stroke: none; }
""",
    """    .geo-fig-svg .gf-dot   { fill: var(--gf-ink); stroke: none; }
    .geo-fig-svg .gf-sep   { stroke: var(--gf-line); }   /* Task 527: разделитель зоны расчёта в картинке */
    .geo-fig-svg .gf-val   { fill: var(--gf-val); }      /* Task 527: значения живого расчёта в картинке */
""",
    1, 'CSS: классы .gf-sep/.gf-val')

# 1.3 Убираем HTML-блок .geo-fig-res* (данные — теперь в SVG)
rep("""    .geo-fig-res { width: 100%; margin-top: 9px; padding-top: 8px;
        border-top: 1px solid var(--gf-line);
        display: flex; flex-direction: column; gap: 4px; }
    .geo-fig-res-row { display: flex; justify-content: space-between;
        align-items: baseline; gap: 10px; font-size: 12.5px; line-height: 1.35; }
    .geo-fig-res-f { color: var(--gf-tx); font-weight: 500; }
    .geo-fig-res-v { color: var(--gf-val); font-weight: 600; white-space: nowrap; }
    /* --- Анимация (Task 526) --- */
""",
    """    /* Task 527: HTML-блок живого расчёта .geo-fig-res* убран —
       расчётные данные перенесены ВНУТРИ картинки (SVG-группа .gf-resg
       под фигурой: разделитель .gf-sep + строки «формула — значение»
       классами .gf-tx / .gf-val). */
    /* --- Анимация (Task 526) --- */
""",
    1, 'CSS: .geo-fig-res* удалены')

# 1.4 Гвард анимации зоны расчёта — на SVG-группу
rep("    .geo-fig-frame:not(.geo-static) .geo-fig-res { opacity: 0; animation: gf-res 0.45s ease-out forwards; }",
    "    .geo-fig-frame:not(.geo-static) .gf-resg { opacity: 0; animation: gf-res 0.45s ease-out forwards; }",
    1, 'CSS: анимация .gf-resg')

# 1.5 prefers-reduced-motion — .gf-resg вместо .geo-fig-res
rep("""        .geo-fig-frame .gf-draw, .geo-fig-frame .gf-fade, .geo-fig-frame .gf-dim,
        .geo-fig-frame .gf-rise, .geo-fig-frame .gf-sweep, .geo-fig-frame .geo-fig-res {""",
    """        .geo-fig-frame .gf-draw, .geo-fig-frame .gf-fade, .geo-fig-frame .gf-dim,
        .geo-fig-frame .gf-rise, .geo-fig-frame .gf-sweep, .geo-fig-frame .gf-resg {""",
    1, 'CSS: reduced-motion .gf-resg')

# 1.6 Комментарий CSS-блока — строка Task 527
rep("""       отключает анимацию (мгновенная перестройка при вводе в поля). */
""",
    """       отключает анимацию (мгновенная перестройка при вводе в поля).
       Task 527 (заявка: «на некоторых геометрических фигурах линии и
       цифры пересекаются… поправь, и расчётные данные должны
       отображаться на картинке под геометрической фигурой, поэтому
       блок с фигурой сделай немного больше»): подписи размеров
       выведены из фигур; расчётные данные — ВНУТРИ картинки (группа
       .gf-resg: разделитель .gf-sep + строки .gf-tx/.gf-val под
       фигурой), HTML-блок .geo-fig-res* убран; рамка 320 → 350px. */
""",
    1, 'CSS: комментарий Task 527')

# ============ 2. HTML — 6 рамок ============

FRAMES = [
    ('gc',  '240 240', 'Схема: круг'),
    ('gr',  '240 240', 'Схема: кольцо'),
    ('gcy', '240 240', 'Схема: цилиндр вертикальный'),
    ('gh',  '240 257', 'Схема: цилиндр горизонтальный с уровнем жидкости'),
    ('gs',  '240 240', 'Схема: сфера'),
    ('gco', '240 240', 'Схема: конус'),
]
for key, vb, aria in FRAMES:
    old = ('<div class="geo-fig-frame" id="' + key + 'FigFrame">'
           '<svg id="' + key + 'Fig" class="geo-fig-svg" viewBox="0 0 240 190" '
           'font-family="Inter, sans-serif" role="img" aria-label="' + aria + '">'
           '</svg><div class="geo-fig-res" id="' + key + 'FigRes"></div></div>')
    new = ('<div class="geo-fig-frame" id="' + key + 'FigFrame">'
           '<svg id="' + key + 'Fig" class="geo-fig-svg" viewBox="0 0 ' + vb + '" '
           'font-family="Inter, sans-serif" role="img" aria-label="' + aria + '">'
           '</svg></div>')
    rep(old, new, 1, 'HTML: рамка #' + key + 'FigFrame (viewBox ' + vb + ', без FigRes)')

# Комментарии над рамками — дополнить строкой Task 527 (×6)
rep('geoFigPlay/geoFigUpdate. -->',
    """geoFigPlay/geoFigUpdate. Task 527: подписи
                 размеров выведены из фигур (не пересекаются с линиями),
                 расчётные данные — в картинке ПОД фигурой (.gf-resg),
                 рамка увеличена до 350px. -->""",
    6, 'HTML: комментарии ×6 дополнены Task 527')

# ============ 3. JS — движок ============

# 3.1 Заголовок движка — блок Task 527
rep("""    //   • под схемой — «живой» расчёт: формула = результат (та же
    //     математика и то же форматирование formatNumber, что в
    //     calcGeo* — совпадает с панелью «Результат»).
""",
    """    //   • под схемой — «живой» расчёт: формула = результат (та же
    //     математика и то же форматирование formatNumber, что в
    //     calcGeo* — совпадает с панелью «Результат»).
    //
    // Task 527 (заявка): «…на некоторых геометрических фигурах линии и
    // цифры пересекаются и накладываются друг на друга, поправь, и
    // расчётные данные должны отображаться на картинке под
    // геометрической фигурой, поэтому блок с фигурой сделай немного
    // больше.» Что изменено: (1) подписи размеров выведены ИЗ фигур:
    // круг/сфера — диаметр D размером ПОД фигурой (gfDimH labelPos
    // 'below'), кольцо — D под фигурой, d сквозной с подписью НАД
    // фигурой (подписи в отверстии пересекали линии при малом d),
    // конус — подпись образующей L у ЛЕВОГО ребра (прежде пересекала
    // размерную линию H), сфера — подпись D прежде пересекал штриховой
    // меридиан; (2) gfDimV: при коротком размере повернутая подпись
    // выносится за выносные линии (низ/верх) — подпись h/D больше не
    // пересекает выносные; отступ подписи от линии 5→9; (3) расчётные
    // данные — ВНУТРИ картинки: gfDataZone под фигурой (разделитель
    // .gf-sep + строки .gf-tx/.gf-val, анимация .gf-resg), HTML-блок
    // #xxFigRes и CSS .geo-fig-res* убраны; (4) рамка 320→350px,
    // viewBox 240×240 (гориз. цилиндр — 240×257, три строки расчёта).
""",
    1, 'JS: заголовок движка Task 527')

# 3.2 gfDimH — документирующий комментарий
rep("""    // Горизонтальный размер: линия на y между x1..x2; выносные линии
    // exts = [[x, yFrom], …] — от точки фигуры (со сквозным зазором
    // 2.5) до размера и на 4 за него; стрелки внутрь (при коротком
    // размере — наружу); подпись над серединой.
""",
    """    // Горизонтальный размер: линия на y между x1..x2; выносные линии
    // exts = [[x, yFrom], …] — от точки фигуры (со сквозным зазором
    // 2.5) до размера и на 4 за него; стрелки внутрь (при коротком
    // размере — наружу); подпись над серединой. Task 527: labelPos
    // 'below' — подпись ПОД линией (для размеров под фигурой: не
    // пересекается ни с фигурой, ни с выносными линиями).
""",
    1, 'JS: комментарий gfDimH')

# 3.3 gfDimH — сигнатура
rep("    function gfDimH(x1, x2, y, label, exts) {",
    "    function gfDimH(x1, x2, y, label, exts, labelPos) {",
    1, 'JS: сигнатура gfDimH labelPos')

# 3.4 gfDimH — позиция подписи
rep("""        s += '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(mid) + '" y="' + gfN(y - 5) + '">' + label + '</text>';
""",
    """        const ty = (labelPos === 'below') ? y + 14 : y - 5;
        s += '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(mid) + '" y="' + gfN(ty) + '">' + label + '</text>';
""",
    1, 'JS: gfDimH подпись labelPos')

# 3.5 gfDimV — документирующий комментарий
rep("""    // Вертикальный размер: линия на x между y1..y2; выносные exts =
    // [[y, xFrom], …]; подпись повёрнута −90° у середины, со стороны
    // labelSide ('left' | 'right').
""",
    """    // Вертикальный размер: линия на x между y1..y2; выносные exts =
    // [[y, xFrom], …]; подпись повёрнута −90°, со стороны labelSide
    // ('left' | 'right'). Task 527: отступ подписи от размерной линии
    // 9 (было 5 — глифы касались линии); при коротком размере подпись
    // выносится за выносные линии (вниз, иначе вверх) — не пересекает
    // их (прежде подпись h/D перекрывала выносную линию).
""",
    1, 'JS: комментарий gfDimV')

# 3.6 gfDimV — тело: lx 5→9 + короткий размер
rep("""        const lx = (labelSide === 'right') ? x + 5 : x - 5;
        s += '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(lx) + '" y="' + gfN(mid) + '" transform="rotate(-90 ' + gfN(lx) + ' ' + gfN(mid) +
             ')">' + label + '</text>';
""",
    """        const lx = (labelSide === 'right') ? x + 9 : x - 9;
        const llen = label.length * 6.3 + 4;   // оценка длины повернутой подписи
        let ly = mid;
        if (Math.abs(y2 - y1) < llen + 10) {
            // Task 527: короткий размер — подпись НЕ помещается между
            // выносными линиями (пересекала бы их). Выносим за пределы:
            // вниз (под нижнюю выносную), иначе вверх (над верхней).
            const bot = Math.max(y1, y2), top = Math.min(y1, y2);
            if (bot + llen + 8 <= 186) ly = bot + llen / 2 + 8;
            else if (top - llen - 8 >= 2) ly = top - llen / 2 - 8;
        }
        s += '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(lx) + '" y="' + gfN(ly) + '" transform="rotate(-90 ' + gfN(lx) + ' ' + gfN(ly) +
             ')">' + label + '</text>';
""",
    1, 'JS: gfDimV lx=±9 + короткий размер')

# 3.7 gfDataZone — новая функция (после gfDimV, перед КРУГ)
rep("""             ')">' + label + '</text>';
        return s;
    }

    // КРУГ: окружность «прочерчивается» обегающим радиусом (останавливается
""",
    """             ')">' + label + '</text>';
        return s;
    }

    // Task 527: зона живого расчёта — ВНУТРИ картинки, ПОД геометрической
    // фигурой (заявка: «расчётные данные должны отображаться на картинке
    // под геометрической фигурой»). Фигура занимает координаты 0…190;
    // разделитель на y=194; строки «формула — значение» с y=212, шаг 17;
    // значения — той же математикой/formatNumber, что calcGeo* (совпадает
    // с панелью «Результат»). Анимация появления — класс .gf-resg.
    function gfDataZone(rows) {
        let s = '<g class="gf-resg" style="animation-delay:1.35s">' +
                '<line class="gf-sep" stroke-width="1" x1="10" y1="194" x2="230" y2="194"/>';
        rows.forEach(function (r, i) {
            const y = 212 + i * 17;
            s += '<text class="gf-tx" font-size="11.5" font-weight="500" x="12" y="' + y + '">' +
                 r[0] + '</text>';
            s += '<text class="gf-val" font-size="12" font-weight="600" text-anchor="end" x="228" y="' +
                 y + '">' + r[1] + '</text>';
        });
        return s + '</g>';
    }

    // КРУГ: окружность «прочерчивается» обегающим радиусом (останавливается
""",
    1, 'JS: gfDataZone добавлена')

# 3.8 Круг — комментарий
rep("""    // КРУГ: окружность «прочерчивается» обегающим радиусом (останавливается
    // под 45°), диаметр — сквозной размер через центр; живой расчёт S и P
    // (формулы те же, что в calcGeoCircle).
""",
    """    // КРУГ: окружность «прочерчивается» обегающим радиусом (останавливается
    // под 45°), диаметр — размер ПОД фигурой (Task 527: подпись выведена
    // из круга — не пересекается с окружностью и радиусом); живой расчёт
    // S и P (формулы те же, что в calcGeoCircle).
""",
    1, 'JS: комментарий круга')

# 3.9 Круг — D-размер под фигурой
rep("""        s += '<g class="gf-dim" style="animation-delay:.9s">' +
             '<line class="gf-dimln" stroke-width="1" x1="' + gfN(cx - R) + '" y1="' + gfN(cy) +
             '" x2="' + gfN(cx + R) + '" y2="' + gfN(cy) + '"/>' +
             '<path class="gf-dimar" d="' + gfArrow(cx - R, cy, 0) + gfArrow(cx + R, cy, Math.PI) + '"/>' +
             '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(cx) + '" y="' + gfN(cy + 17) + '">D = ' + formatNumber(Dmm) + ' мм</text></g>';
""",
    """        s += '<g class="gf-dim" style="animation-delay:.9s">' + gfDimH(cx - R, cx + R, cy + R + 14,
             'D = ' + formatNumber(Dmm) + ' мм', [[cx - R, cy], [cx + R, cy]], 'below') + '</g>';
""",
    1, 'JS: круг — D под фигурой')

# 3.10 Кольцо — комментарий
rep("""    // КОЛЬЦО: пропорция отверстия РЕАЛЬНАЯ (d/D); размеры D и d — на
    // одной горизонтальной оси (стандарт чертежа соосных окружностей);
    // живой расчёт S и Dэкв (формулы те же, что в calcGeoRing).
""",
    """    // КОЛЬЦО: пропорция отверстия РЕАЛЬНАЯ (d/D); размер D — ПОД
    // фигурой, d — сквозной через отверстие с подписью НАД фигурой
    // (Task 527: подписи выведены из отверстия — не пересекаются с
    // линиями при любом d/D); живой расчёт S и Dэкв (формулы те же,
    // что в calcGeoRing).
""",
    1, 'JS: комментарий кольца')

# 3.11 Кольцо — D под фигурой + d над фигурой
rep("""        s += '<g class="gf-dim" style="animation-delay:.9s">' +
             '<line class="gf-dimln" stroke-width="1" x1="' + gfN(cx - Ro) + '" y1="' + gfN(cy) +
             '" x2="' + gfN(cx + Ro) + '" y2="' + gfN(cy) + '"/>' +
             '<path class="gf-dimar" d="' + gfArrow(cx - Ro, cy, 0) + gfArrow(cx + Ro, cy, Math.PI) + '"/>' +
             '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(cx) + '" y="' + gfN(cy + 16) + '">D = ' + formatNumber(Dmm) + ' мм</text></g>';
        s += '<g class="gf-dim" style="animation-delay:1.05s">' +
             '<path class="gf-dimar" d="' + gfArrow(cx - Ri, cy, 0) + gfArrow(cx + Ri, cy, Math.PI) + '"/>' +
             '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(cx) + '" y="' + gfN(cy - 11) + '">d = ' + formatNumber(dmm) + ' мм</text></g>';
""",
    """        s += '<g class="gf-dim" style="animation-delay:.9s">' + gfDimH(cx - Ro, cx + Ro, cy + Ro + 14,
             'D = ' + formatNumber(Dmm) + ' мм', [[cx - Ro, cy], [cx + Ro, cy]], 'below') + '</g>';
        s += '<g class="gf-dim" style="animation-delay:1.05s">' +
             '<line class="gf-dimln" stroke-width="1" x1="' + gfN(cx - Ri) + '" y1="' + gfN(cy) +
             '" x2="' + gfN(cx + Ri) + '" y2="' + gfN(cy) + '"/>';
        s += (2 * Ri >= 22)
            ? '<path class="gf-dimar" d="' + gfArrow(cx - Ri, cy, 0) + gfArrow(cx + Ri, cy, Math.PI) + '"/>'
            : '<path class="gf-dimar" d="' + gfArrow(cx - Ri, cy, Math.PI) + gfArrow(cx + Ri, cy, 0) + '"/>';
        s += '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(cx) + '" y="' + gfN(cy - Ro - 11) + '">d = ' + formatNumber(dmm) + ' мм</text></g>';
""",
    1, 'JS: кольцо — D под, d над')

# 3.12 Сфера — комментарий
rep("""    // СФЕРА: окружность + штриховые экватор/меридиан; сквозной диаметр;
    // живой расчёт V и S (как в calcGeoSphere).
""",
    """    // СФЕРА: окружность + штриховые экватор/меридиан; диаметр — размер
    // ПОД фигурой (Task 527: подпись внутри сферы прежде пересекал
    // штриховой меридиан); живой расчёт V и S (как в calcGeoSphere).
""",
    1, 'JS: комментарий сферы')

# 3.13 Сфера — D под фигурой
rep("""        g += '<g class="gf-dim" style="animation-delay:.9s">' +
             '<line class="gf-dimln" stroke-width="1" x1="' + gfN(cx - R) + '" y1="' + gfN(cy) +
             '" x2="' + gfN(cx + R) + '" y2="' + gfN(cy) + '"/>' +
             '<path class="gf-dimar" d="' + gfArrow(cx - R, cy, 0) + gfArrow(cx + R, cy, Math.PI) + '"/>' +
             '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="middle" x="' +
             gfN(cx) + '" y="' + gfN(cy + 26) + '">D = ' + formatNumber(D) + ' м</text></g>';
""",
    """        g += '<g class="gf-dim" style="animation-delay:.9s">' + gfDimH(cx - R, cx + R, cy + R + 14,
             'D = ' + formatNumber(D) + ' м', [[cx - R, cy], [cx + R, cy]], 'below') + '</g>';
""",
    1, 'JS: сфера — D под фигурой')

# 3.14 Конус — комментарий
rep("""    // КОНУС: пропорция H/D реальная; размеры D (снизу) и H (справа),
    // образующая L — подпись у правого ребра; живой расчёт V и L
    // (как в calcGeoCone).
""",
    """    // КОНУС: пропорция H/D реальная; размеры D (снизу) и H (справа),
    // образующая L — подпись у ЛЕВОГО ребра (Task 527: прежде
    // пересекала размерную линию H); живой расчёт V и L (как в
    // calcGeoCone).
""",
    1, 'JS: комментарий конуса')

# 3.15 Конус — D-подпись под линией
rep("""        g += '<g class="gf-dim" style="animation-delay:.9s">' + gfDimH(cx - rx, cx + rx, yB + ry + 12,
             'D = ' + formatNumber(D) + ' м', [[cx - rx, yB], [cx + rx, yB]]) + '</g>';
""",
    """        g += '<g class="gf-dim" style="animation-delay:.9s">' + gfDimH(cx - rx, cx + rx, yB + ry + 12,
             'D = ' + formatNumber(D) + ' м', [[cx - rx, yB], [cx + rx, yB]], 'below') + '</g>';
""",
    1, 'JS: конус — D labelPos below')

# 3.16 Конус — L-подпись у ЛЕВОГО ребра
rep("""        const mx = cx + rx / 2, my = (yA + yB) / 2;
        g += '<g class="gf-dim" style="animation-delay:1.2s">' +
             '<text class="gf-dimtx" font-size="11.5" font-weight="600" x="' + gfN(mx + 7) + '" y="' +
             gfN(my - 4) + '">L = ' + formatNumber(slant) + ' м</text></g>';
""",
    """        const mx = cx - rx / 2, my = (yA + yB) / 2;
        g += '<g class="gf-dim" style="animation-delay:1.2s">' +
             '<text class="gf-dimtx" font-size="11.5" font-weight="600" text-anchor="end" x="' +
             gfN(mx - 7) + '" y="' + gfN(my - 4) + '">L = ' + formatNumber(slant) + ' м</text></g>';
""",
    1, 'JS: конус — L слева')

# 3.17 geoFigBuild — зона расчёта в картинке
rep("""    // Сборка схемы по ключу и значениям (чистая функция — проверяется
    // в test-task526.js без DOM).
    function geoFigBuild(key, v) {
        if (key === 'gc') return geoFigCircleSVG(v.D);
        if (key === 'gr') return geoFigRingSVG(v.D, v.d);
        if (key === 'gcy') return geoFigCylSVG(v.D, v.H);
        if (key === 'gh') return geoFigHorizSVG(v.L, v.D, v.h);
        if (key === 'gs') return geoFigSphereSVG(v.D);
        if (key === 'gco') return geoFigConeSVG(v.D, v.H);
        return { svg: '', rows: [] };
    }
""",
    """    // Сборка схемы по ключу и значениям (чистая функция — проверяется
    // в test-task526.js / test-task527.js без DOM). Task 527: к фигуре
    // добавляется зона живого расчёта ВНУТРИ картинки — под фигурой.
    function geoFigBuild(key, v) {
        let b;
        if (key === 'gc') b = geoFigCircleSVG(v.D);
        else if (key === 'gr') b = geoFigRingSVG(v.D, v.d);
        else if (key === 'gcy') b = geoFigCylSVG(v.D, v.H);
        else if (key === 'gh') b = geoFigHorizSVG(v.L, v.D, v.h);
        else if (key === 'gs') b = geoFigSphereSVG(v.D);
        else if (key === 'gco') b = geoFigConeSVG(v.D, v.H);
        else b = { svg: '', rows: [] };
        b.svg += gfDataZone(b.rows);
        return b;
    }
""",
    1, 'JS: geoFigBuild + gfDataZone')

# 3.18 geoFigRender — без resEl
rep("""    // Рендер: перерисовка SVG + блока живого расчёта. animate=true —
    // проиграть анимацию (открытие страницы / «Рассчитать»), false —
    // мгновенно (ввод в поля, класс .geo-static).
    function geoFigRender(key, animate) {
        const frame = document.getElementById(key + 'FigFrame');
        const svgEl = document.getElementById(key + 'Fig');
        const resEl = document.getElementById(key + 'FigRes');
        if (!frame || !svgEl || !resEl) return;
        const v = geoFigVals(key);
        if (v === null) return;
        const b = geoFigBuild(key, v);
        svgEl.innerHTML = b.svg;
        resEl.innerHTML = b.rows.map(function (r) {
            return '<div class="geo-fig-res-row"><span class="geo-fig-res-f">' + r[0] +
                   '</span><span class="geo-fig-res-v">' + r[1] + '</span></div>';
        }).join('');
        frame.classList.toggle('geo-static', !animate);
    }
""",
    """    // Рендер: перерисовка SVG — фигура + зона живого расчёта ВНУТРИ
    // картинки (Task 527: HTML-блок #xxFigRes убран — данные рисуются
    // в SVG под фигурой). animate=true — проиграть анимацию (открытие
    // страницы / «Рассчитать»), false — мгновенно (ввод в поля, класс
    // .geo-static).
    function geoFigRender(key, animate) {
        const frame = document.getElementById(key + 'FigFrame');
        const svgEl = document.getElementById(key + 'Fig');
        if (!frame || !svgEl) return;
        const v = geoFigVals(key);
        if (v === null) return;
        svgEl.innerHTML = geoFigBuild(key, v).svg;
        frame.classList.toggle('geo-static', !animate);
    }
""",
    1, 'JS: geoFigRender без resEl')

# ============ Запись ============
io.open(PATH, 'w', encoding='utf-8').write(src)

# Контрольные проверки
checks = [
    ('FigRes в index.html', src.count('FigRes'), 0),
    ('geo-fig-res в index.html', src.count('geo-fig-res'), 0),
    ('viewBox="0 0 240 190" (старый)', src.count('viewBox="0 0 240 190"'), 0),
    ('viewBox 240×240', src.count('viewBox="0 0 240 240"'), 5),
    ('viewBox 240×257 (gh)', src.count('viewBox="0 0 240 257"'), 1),
    ('gfDataZone определена', src.count('function gfDataZone('), 1),
    ('gf-resg в JS (группа)', src.count('class="gf-resg"'), 1),
    ('350px рамка', src.count('min(100%, 350px)'), 1),
]
bad = 0
for name, got, want in checks:
    ok = got == want
    print(('  + ' if ok else '  X ') + '%s: %d (ожид. %d)' % (name, got, want))
    if not ok:
        bad += 1

print('')
print('Правок применено: %d' % len(edits))
for e in edits:
    print('  • ' + e)
if bad:
    print('ПРОВЕРКИ ПРОВАЛЕНЫ: %d' % bad)
    sys.exit(1)
print('OK — все контрольные проверки пройдены.')
