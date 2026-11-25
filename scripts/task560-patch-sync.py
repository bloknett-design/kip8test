#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 560: патч нормализации 4 sync-скриптов (devices/lockouts/valves/
regulators) — защита от артефактов Excel-реимпорта новой таблицы
«Перечень КИП ИОС рабочий.xlsx» (14l0ac4zGwOblvuH8kRkwwdOymAVXD5op):

  (A) хвостовые ПУСТЫЕ заголовки срезаются — Excel-реимпорт растянул
      формат на колонки правее данных (Блокировки 13→26, Клапана
      24→26, Регуляторы 12→26; записи пустые ключи и так пропускают,
      но массив headers раздувался);
  (B) целые float приводятся к int ДО str() — Excel хранит целые как
      double (9984837.0), без приведения в JSON попадало «9984837.0»
      вместо прежнего «9984837» (и ID оставался строкой '0.0' вместо
      числа 0 — ломается int-конвертация ID по isdigit).

На старой (Google-нативной) таблице патч НИЧЕГО не меняет (целые там
int, пустых хвостовых заголовков нет) — изменение поведения только
для реимпортированных файлов.

Использование: python3 task560-patch-sync.py <корень репозитория>
"""
import io
import sys

ANCHOR_A = """    for cell in ws[1]:
        val = str(cell.value).strip() if cell.value is not None else ''
        headers.append(val)
    log(f'Заголовки ({len(headers)}): {headers}')"""

PATCH_A = """    for cell in ws[1]:
        val = str(cell.value).strip() if cell.value is not None else ''
        headers.append(val)
    # Task 560: Excel-реимпорт новой таблицы растягивает формат на
    # колонки правее данных — хвостовые ПУСТЫЕ заголовки в JSON не
    # тащим (структура листов остаётся прежней).
    while headers and headers[-1] == '':
        headers.pop()
    log(f'Заголовки ({len(headers)}): {headers}')"""

ANCHOR_B = """            elif val is not None:
                val = str(val).strip()"""

PATCH_B = """            elif val is not None:
                if isinstance(val, float) and val.is_integer():
                    # Task 560: Excel-реимпорт хранит целые как float
                    # (9984837.0) — приводим к int, чтобы в JSON было
                    # прежнее «9984837», а не «9984837.0».
                    val = int(val)
                val = str(val).strip()"""

SCRIPTS = ['scripts/sync-devices.py', 'scripts/sync-lockouts.py',
           'scripts/sync-valves.py', 'scripts/sync-regulators.py']


def main(root):
    for rel in SCRIPTS:
        path = root + '/' + rel
        src = io.open(path, encoding='utf-8').read()
        # гварды
        for anchor, label in ((ANCHOR_A, 'A'), (ANCHOR_B, 'B')):
            n = src.count(anchor)
            if n != 1:
                print('FAIL %s: якорь %s найден %d раз (ожидался 1)' % (rel, label, n))
                return 1
        if 'Task 560' in src:
            print('SKIP %s: уже пропатчен' % rel)
            continue
        src = src.replace(ANCHOR_A, PATCH_A)
        src = src.replace(ANCHOR_B, PATCH_B)
        io.open(path, 'w', encoding='utf-8').write(src)
        print('OK %s: патчи A (пустые хвостовые заголовки) + B (целые float → int)' % rel)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
