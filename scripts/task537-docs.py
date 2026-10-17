#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task537-docs.py — обновление системного промта kip8test (Task 537).

Заменяет:
  1) версионную строку (шапка) — post-Task 536 → post-Task 537;
  2) строку «Телефонный справочник» в таблице источников данных —
     добавляет архив пользовательских данных;
  3) сводку Apps Script — PhonebookArchive.gs + эндпоинты phonebook.*;
  4) гейты прав — secret.view.

Идемпотентно: повторный запуск не дублирует (искомые якоря post-537
уже не находятся → exit без изменений).
"""

import io
import sys

PROMPT = 'Системный_промт_для_приложения_КИПиА.md'

NEW_VERSION = (
    '> **Версия документа:** 2026-10-17 (post-Task 537 — ТЕЛЕФОННЫЙ СПРАВОЧНИК: '
    'АРХИВ ПОЛЬЗОВАТЕЛЬСКИХ ДАННЫХ (заявка: «Необходимо проработать телефонный '
    'справочник. создать файл с google таблицей для телефонного справочника, '
    'придумай для него название, в этом файле я планирую организовать сохранять '
    'данные внесённые пользователями в разделах телефонного справочника '
    'избранное и добавленные примечания, доступные только тем пользователям '
    'которые их внесли для себя, то есть таблицы с архивами данных общие, но '
    'данные индивидуальные привязанные к email. и в дальнейшем по необходимости '
    'расширение архива данных для телефонного справочника.»): СЕРВЕР-ONLY задача '
    'создания ХРАНИЛИЩА (клиентская интеграция — следующая задача): (1) НОВЫЙ '
    'scripts/PhonebookArchive.gs — файл Google Таблиц «Телефонный справочник — '
    'Архив пользователей» СОЗДАЁТСЯ САМИМ СКРИПТОМ (SpreadsheetApp.create; '
    'разовый запуск phonebookArchiveInit() из редактора ИЛИ лениво при первом '
    'обращении к API; ID — в Script Properties PHONEBOOK_ARCHIVE_SPREADSHEET_ID, '
    'открытие по ID — файл можно переименовывать/перемещать по Drive; диагностика '
    'phonebookArchiveStatus); листы «Избранное» (id/дата_добавления/email/'
    'контакт_id/фио/должность/телефон/организация/контакт_json/статус/'
    'дата_удаления), «Примечания» (id/даты/email/контакт_id/снимки/контакт_json/'
    'примечание ≤500/статус), «Служебное» (версия структуры, назначение, порядок '
    'расширения архива); (2) ПРИНЦИП ЗАЯВКИ: таблицы общие, данные '
    'индивидуальны — каждая строка привязана к email, чтение фильтруется по '
    'email, запись/удаление только своих строк, чужие записи ни при каком '
    'запросе не возвращаются и не меняются; контакт_id = pbMakeId клиента '
    '(header|group|subgroup|position|name|phone), снимки полей + контакт_json — '
    'резерв на смену phonebook.json; (3) мягкое удаление (статус «активна»/'
    '«удалена» + дата_удаления — история сохраняется, повторное добавление = '
    'новая строка; ≤1 активная на email+контакт_id, при ручных дублях активная '
    'последняя); (4) гейт secret.view (как у страницы справочника _SECRET_PAGES, '
    'fail-closed без RoleMatrixGate.gs), LockService на записи, Utils.audit '
    '(PHONEBOOK_FAV_ADD/REMOVE, PHONEBOOK_NOTE_ADD/UPDATE/REMOVE, '
    'PHONEBOOK_ARCHIVE_CREATED), формат «@» (Task 304) + экранирование =+-@ '
    'апострофом (защита примечаний от формул), email регистронезависим; '
    '(5) Code.gs: роутинг phonebook.getMyData/setFavorite/setNote (+ шапка-индекс '
    'модулей) — контракт в шапке PhonebookArchive.gs (getMyData → {srvVer:537, '
    'favorites:{id:true}, notes:{id:текст}} — форма карт как в localStorage '
    'клиента, интеграция сведётся к слиянию); (6) тесты — НОВЫЙ test-task537.js '
    '×51 (SRC: модуль/название файла/листы/статусы/гейт/локи/аудит/«@»+'
    'экранирование/init+status/лимиты; SRC Code.gs: 3 роута + не в GATE_ACTIONS; '
    'VM: init/идемпотентность/порядок листов/Служебное/ленивое автосоздание/'
    'авто-ремонт листа; избранное: строка+снимки/already/изоляция чужих/мягкое '
    'удаление/идемпотентность/повторное добавление/регистр email/аудит; '
    'примечания: created/updated-та же строка/изоляция/пустой текст=удаление/'
    'invalid_note/invalid_id/аудит; доступ: no_session/access_denied/гейт с '
    'secret.view/fail-closed; формулы: апостроф/обычный текст/два пользователя '
    'в одном файле) — 7028/0 → 7079/0 (+51); (7) клиент НЕ менялся — SW '
    'kipia-test-v749 БЕЗ изменений (index.html не тронут; kip8test-desktop НЕ '
    'синкается — триггер синка только index.html, норма как docs-пуши); '
    'DEPLOY-Task537-phonebook-archive-storage.md (СЕРВЕР: + PhonebookArchive.gs '
    '→ заменить Code.gs → phonebookArchiveInit() ▶ Run → New version; файл '
    'появится на Drive владельца, переименование/перемещение безопасны; откат '
    'прост — клиент не зависит; kipia-test-v749, Task 537))'
)

OLD_PB_ROW = (
    '| Телефонный справочник | статический коммит (без sync-скрипта) | — |'
)
NEW_PB_ROWS = (
    '| Телефонный справочник (справочник) | статический коммит data/phonebook.json (без sync-скрипта) | — |\n'
    '| Телефонный справочник: АРХИВ ПОЛЬЗОВАТЕЛЬСКИХ ДАННЫХ (Task 537) | через Apps Script (`PhonebookArchive.gs`): листы «Избранное»/«Примечания»/«Служебное», email-привязка строк, мягкое удаление | файл «Телефонный справочник — Архив пользователей» создаёт сам скрипт (`phonebookArchiveInit()` / лениво), ID — в Script Properties |'
)

OLD_GS_LIST = (
    'Flowmeter, FlowmeterArchive/Init, Sessions, SessionsDevicePolicy, Utils, ValidationRules,\n'
    'WorkSchedule, Vacations*, RoleMatrix*, PlanEvents*, PPEInit, StatusCodesInit, TabNumbersFix);'
)
NEW_GS_LIST = (
    'Flowmeter, FlowmeterArchive/Init, Sessions, SessionsDevicePolicy, Utils, ValidationRules,\n'
    'WorkSchedule, Vacations*, RoleMatrix*, PlanEvents*, PPEInit, StatusCodesInit, TabNumbersFix,\n'
    'PhonebookArchive (Task 537 — архив пользовательских данных телефонного справочника));'
)

OLD_ENDPOINTS = (
    'отпуска/СИЗ), `planEvents.*`, `admin*`. Гейты прав: `workschedule.view`/`.min`/`.edit`,\n'
    '`admin.panel`; READ_ROLES/INPUT_ROLES в Flowmeter.gs.'
)
NEW_ENDPOINTS = (
    'отпуска/СИЗ), `planEvents.*`, `phonebook.*` (Task 537: getMyData/setFavorite/setNote —\n'
    'архив пользовательских данных справочника, email-bound), `admin*`. Гейты прав:\n'
    '`workschedule.view`/`.min`/`.edit`, `admin.panel`, `secret.view` (телефонный справочник);\n'
    'READ_ROLES/INPUT_ROLES в Flowmeter.gs.'
)


def main():
    with io.open(PROMPT, encoding='utf-8') as f:
        lines = f.read().split('\n')

    changed = []

    # 1) Версионная строка (строка с индексом 2)
    if lines[2].startswith('> **Версия документа:** 2026-10-16 (post-Task 536'):
        lines[2] = NEW_VERSION
        changed.append('версионная строка → post-Task 537')
    elif 'post-Task 537' in lines[2]:
        print('версионная строка уже post-Task 537 — пропуск')
    else:
        print('ВНИМАНИЕ: версионная строка не распознана — смотрите вручную')
        sys.exit(1)

    text = '\n'.join(lines)

    # 2) Строка телефонного справочника в источниках данных
    if OLD_PB_ROW in text:
        text = text.replace(OLD_PB_ROW, NEW_PB_ROWS)
        changed.append('источники данных: архив справочника')
    elif 'АРХИВ ПОЛЬЗОВАТЕЛЬСКИХ ДАННЫХ (Task 537)' in text:
        print('строка источников уже обновлена — пропуск')
    else:
        print('ВНИМАНИЕ: строка телефонного справочника не найдена')
        sys.exit(1)

    # 3) Список .gs-файлов в сводке Apps Script
    if OLD_GS_LIST in text:
        text = text.replace(OLD_GS_LIST, NEW_GS_LIST)
        changed.append('сводка Apps Script: PhonebookArchive')
    elif 'PhonebookArchive (Task 537' in text:
        print('список .gs уже обновлён — пропуск')

    # 4) Эндпоинты и гейты
    if OLD_ENDPOINTS in text:
        text = text.replace(OLD_ENDPOINTS, NEW_ENDPOINTS)
        changed.append('эндпоинты: phonebook.* + гейт secret.view')
    elif 'phonebook.*` (Task 537' in text:
        print('эндпоинты уже обновлены — пропуск')

    with io.open(PROMPT, 'w', encoding='utf-8') as f:
        f.write(text)

    for c in changed:
        print('OK: ' + c)
    print('Готово: {} изменений'.format(len(changed)))


if __name__ == '__main__':
    main()
