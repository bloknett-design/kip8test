#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 527 — docs-коммиты (КИПИА-конвейер, по образцу Task 526):
  1) версионная строка промта: post-Task 527 ПРЕДШЕСТВУЕТ, post-Task
     526 демонирован в хвост (оба репо);
  2) ARCHITECTURE.md §2 — счётчики тестов (6728/6729) + зеркала
     (6713/6744) + число тест-файлов;
  3) worklog.md — записи финализации ×2.
Файлы Правятся, коммиты делает обёртка (bash).
"""
import io

T527 = ('post-Task 527 — ГЕОМЕТРИЯ: ПЕРЕСЕЧЕНИЯ ЛИНИЙ/ЦИФР ИСПРАВЛЕНЫ + '
        'РАСЧЁТНЫЕ ДАННЫЕ ВНУТРИ КАРТИНКИ ПОД ФИГУРОЙ + БЛОК УВЕЛИЧЕН '
        '(заявка: «В разделе Главная / Инженерные калькуляторы / Геометрия, '
        'на некоторых геометрических фигурах линии и цифры пересекаются и '
        'накладываются друг на друга, поправь, и расчётные данные должны '
        'отображаться на картинке под геометрической фигурой, поэтому блок '
        'с фигурой сделай немного больше.»): ДИАГНОСТИКА (VLM-аудит '
        'скриншотов Task 526 + геометрический разбор координат): сфера — '
        'подпись D пересекала штриховой меридиан; конус — L пересекала '
        'размерную линию H, D впритык к линии (0–2 px); гориз. цилиндр — '
        'вертикальная подпись h (span 45 < длины ~61) перекрывала выносную '
        'линию зеркала жидкости; кольцо — подписи D/d в отверстии '
        'ломались при малом d (стрелки d/D на одной оси); ИСПРАВЛЕНИЯ: '
        'gfDimH labelPos \'below\' (подпись ПОД размерной линией — для '
        'размеров под фигурой), gfDimV — отступ повернутой подписи 5→9 '
        '(глифы касались линии) + ВЫНОС подписи за выносные линии при '
        'коротком размере (вниз, иначе вверх), круг/сфера/кольцо — D '
        'размер ПОД фигурой (линия + выносные + стрелки у нижнего края, '
        'подпись под линией), кольцо — d сквозной через отверстие с '
        'подписью НАД фигурой (стрелки наружу при тонком кольце), конус — '
        'L у ЛЕВОГО ребра (text-anchor end), D — под линией; РАСЧЁТНЫЕ '
        'ДАННЫЕ — ВНУТРИ КАРТИНКИ ПОД ФИГУРОЙ: HTML-блок #xxFigRes и CSS '
        '.geo-fig-res* УБРАНЫ со всех 6 страниц — новая gfDataZone рисует '
        'живой расчёт В САМОМ SVG (разделитель .gf-sep на y=194 + строки '
        '«формула — значение» .gf-tx/.gf-val с y=212 шагом 17, значения '
        'цветом результата, анимация .gf-resg каскадом 1.35s; гварды '
        ':not(.geo-static) и prefers-reduced-motion сохранены; математика '
        'и formatNumber — те же, что calcGeo*, числа совпадают с панелью '
        '«Результат»); БЛОК С ФИГУРОЙ НЕМНОГО БОЛЬШЕ: рамка .geo-fig-frame '
        '320→350px, viewBox 240×190→240×240 (гориз. цилиндр 240×257 — три '
        'строки расчёта); DEPLOY-Task527 (ТОЛЬКО КЛИЕНТ: .gs, листы Google '
        'Sheets и деплой веб-приложения НЕ менялись); тесты test-task527 '
        '×33 НОВЫЙ (SRC HTML: нет #xxFigRes, viewBox 240×240/240×257, '
        'комментарии Task 527; SRC CSS: 350px, .gf-sep/.gf-val, '
        '.geo-fig-res* удалены, анимация/reduced-motion .gf-resg; SRC JS: '
        'gfDataZone/labelPos/вынос подписи/подписи вне фигур; VM: данные '
        'в картинке = calcGeo*, позиции подписей вне фигур (D y=168/170/'
        '172, d y=17, L x=96 anchor end, h вне выносных), юнит-тесты '
        'gfDimH/gfDimV; SW) + адаптация test-task526 (viewBox, отсутствие '
        '#xxFigRes, 350px, гвард .gf-resg); бамп SW v739→v740 / v536→v537 '
        '(870/873 замены); браузерная проверка 208/208 (десктоп тёмная/'
        'светлая — все 6 страниц: подписи размеров ВНЕ фигур, данные '
        'расчёта В КАРТИНКЕ под разделителем, анимации gf-draw/gf-resg '
        'играют и завершаются, жидкость; взаимодействие: ввод 150 → '
        'мгновенно D=150 и 176,71 см² В КАРТИНКЕ, «Рассчитать» → анимация '
        'перезапущена; мобайл 390×844 обе темы — не обрезано; 0 JS-ошибок) '
        '+ VLM 15/15 («дефектов пересечения НЕТ» на всех чертежах, '
        'дословные цитаты данных в картинке ОБЯЗАТЕЛЬНО со значениями; '
        'скриншоты download/kip8test-task527/); УРОК ПАЙПЛАЙНА: '
        'transfer-скрипт тестов kip8 резал файлы по ПЕРВОМУ разделителю '
        '«// ===» (index() вместо rindex() до маркера «5. SW») — итог '
        '6674 с обрезанными файлами; пересборка fix-скриптом, полный набор '
        'стал 6729/0 (+32 к 6697); SW kipia-test-v740 / kipia-v537; все 4 '
        'репо ЗЕЛЁНЫЕ: kip8test 6728/0 → kip8test-desktop 6713/0 (+33), '
        'kip8 6729/0 → kip8-desktop 6744/0 (+32; обе сборки success)')


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def bump_prompt(path):
    s = read(path)
    old = '> **Версия документа:** 2026-10-14 (post-Task 526 — '
    assert s.count(old) == 1, 'версионная строка не найдена: ' + path
    s = s.replace(old, '> **Версия документа:** 2026-10-15 ('
                   + T527 + '. Post-Task 526 — ')
    write(path, s)
    print('[ok] промт: ' + path)


def bump_arch(path, old_tests, new_tests, old_files, new_files, old_mirror, new_mirror):
    s = read(path)
    old = ('`tests/`, %s тестов, %s тест-файлов, `node tests/run-all.js`; '
           'зеркало CI: %s' % (old_tests, old_files, old_mirror))
    # строка содержит «kip8test-desktop 6680 — гварды…» — зеркало с суффиксом
    i = s.index(old)
    seg = s[i:i + 400]
    seg = seg.replace(old_tests, new_tests, 1).replace(old_files, new_files, 1)
    seg = seg.replace(old_mirror, new_mirror, 1)
    s = s[:i] + seg + s[i + 400:]
    assert new_tests in s and new_mirror in s, 'ARCHITECTURE не обновлён: ' + path
    write(path, s)
    print('[ok] ARCHITECTURE: %s → %s тестов, зеркало %s → %s' %
          (path, new_tests, old_mirror, new_mirror))


# kip8test
bump_prompt('/home/z/my-project/kip8test/Системный_промт_для_приложения_КИПиА.md')
bump_arch('/home/z/my-project/kip8test/ARCHITECTURE.md',
          '6695', '6728', '223', '224', 'kip8test-desktop 6680', 'kip8test-desktop 6713')

# kip8
bump_prompt('/home/z/my-project/kip8/Системный_промт_для_приложения_КИПиА.md')
bump_arch('/home/z/my-project/kip8/ARCHITECTURE.md',
          '6697', '6729', '224', '225', 'kip8-desktop 6712', 'kip8-desktop 6744')

# worklog-записи финализации
for repo, counts in [('kip8test', 'kip8test 6728/0 → kip8test-desktop 6713/0 (+33)'),
                     ('kip8', 'kip8 6729/0 → kip8-desktop 6744/0 (+32)')]:
    p = '/home/z/my-project/%s/worklog.md' % repo
    entry = ('\n---\nTask ID: 527 (финализация)\nAgent: main (Super Z)\n'
             'Task: Пуш/CI/синк/docs Task 527.\n\nWork Log:\n')
    if repo == 'kip8test':
        entry += ('- Пуш 178afab6 → CI Tests 6728/0 + Pages + синк (bot '
                  '91117c8f) → kip8test-desktop 6713/0 + Build success.\n')
    else:
        entry += ('- Пуш b8080e5 → CI Tests 6729/0 + Pages + Build + синк '
                  '(bot d366d6ae) → kip8-desktop 6744/0 + Build success '
                  '(перенос prepare-kip8-transfer.py, дифф 244 строки).\n')
    entry += ('- Docs: версионная строка промта post-Task 527 (демоция '
              'post-Task 526), ARCHITECTURE.md §2, эта запись.\n\n'
              'Stage Summary:\n- Task 527 ПОЛНОСТЬЮ ЗАКРЫТ: %s; обе '
              'сборки success. Правка ТОЛЬКО КЛИЕНТ — Apps Script, листы '
              'Google Sheets и деплой НЕ менялись: клиенты получат '
              'исправленные схемы по обычному циклу SW (kipia-test-v740 / '
              'kipia-v537). Открытых хвостов НЕТ.\n' % counts)
    with io.open(p, 'a', encoding='utf-8') as f:
        f.write(entry)
    print('[ok] worklog: ' + p)

print('OK — docs готовы к коммитам.')
