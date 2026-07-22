# kip8test — тестовый репозиторий PWA «КИПиА»

Проверочный репозиторий для тестирования изменений PWA «КИПиА» перед деплоем в основной репозиторий [kip8](https://github.com/bloknett-design/kip8).

- **Репозиторий:** https://github.com/bloknett-design/kip8test
- **Живая страница:** https://bloknett-design.github.io/kip8test/
- **Исходные файлы:** https://drive.google.com/drive/folders/1chBGGftT-EGU9EAvmheHhPt52wKJxZke

---

## ⚠️ Отличия от основного репозитория kip8

Этот репозиторий **готов к запуску** — все необходимые правки для изоляции от основного репозитория уже применены.

### 1. `manifest.json`

Все пути изменены с `/kip8/` на `/kip8test/`:

| Поле | Значение |
|------|----------|
| `id` | `/kip8test/?source=pwa` |
| `start_url` | `/kip8test/?source=pwa` |
| `scope` | `/kip8test/` |
| 7 shortcuts | Все URL начинаются с `/kip8test/?source=pwa#...` |

**Почему это важно:** без этих правок браузер посчитает `kip8` и `kip8test` одним PWA (по `id`) — установится только одно приложение.

### 2. `sw.js` — имена кэшей

| Переменная | В kip8 | В kip8test (этот репо) |
|------------|--------|------------------------|
| `CACHE_VERSION` | `kipia-v15` | `kipia-test-v124` |
| `IMAGE_CACHE_VERSION` | `kipia-images-v1` | `kipia-images-test-v1` |

**Почему это важно:** Cache Storage общий на весь origin `bloknett-design.github.io`. Одинаковые имена кэшей привели бы к взаимному удалению данных и поломке офлайн-режима в обоих репозиториях.

При обновлении файлов в этом репо **инкрементируйте** `CACHE_VERSION`:
- `kipia-test-v1` → `kipia-test-v2` → … → `kipia-test-v124` (текущая)

### 3. `index.html` — изоляция localStorage

В начале JS-блока добавлена обёртка, которая добавляет префикс `kip8test:` ко всем ключам `localStorage`:

```javascript
(function isolateLocalStorage() {
    const PREFIX = 'kip8test:';
    const origGetItem = localStorage.getItem.bind(localStorage);
    const origSetItem = localStorage.setItem.bind(localStorage);
    const origRemoveItem = localStorage.removeItem.bind(localStorage);
    localStorage.getItem = function(key) { return origGetItem(PREFIX + key); };
    localStorage.setItem = function(key, value) { return origSetItem(PREFIX + key, value); };
    localStorage.removeItem = function(key) { return origRemoveItem(PREFIX + key); };
})();
```

**Почему это важно:** `localStorage` общий на origin. Без префикса переключение темы в `kip8test` изменило бы тему в `kip8` (и наоборот).

### 4. `.github/workflows/update-exam-tickets.yml` — отключён cron

Автоматическое ежедневное обновление билетов **отключено** (закомментирован блок `schedule:`). Запуск только вручную через GitHub Actions UI (`workflow_dispatch`).

**Источник данных:** публичная ссылка Яндекс Диска
`https://disk.yandex.ru/i/oAuOyVb4OkmNtA`
(файл «Экзаминационные билеты_app.xlsx»). Скрипт `scripts/convert-exam-tickets.py`
тянет файл через Yandex Disk Public API — так же, как и приборы
(`scripts/sync-devices.py`). Зависимости от OneDrive и от основного репо kip8 нет.

**Почему cron отключён:** иначе оба репо будут каждый день дёргать Яндекс Диск — дублирование работы и риск rate-limit.

### 5. `.github/workflows/ci.yml` — без изменений

Тесты запускаются при push/PR в `main`/`master`, как и в основном репо.

---

## 🚀 Установка

### Вариант A: создать новый репозиторий с этими файлами

```bash
# 1. Клонировать пустой репозиторий kip8test с GitHub
git clone https://github.com/bloknett-design/kip8test.git
cd kip8test

# 2. Распаковать архив kip8test.zip в эту папку
unzip /path/to/kip8test.zip -d .

# 3. Закоммитить и запушить
git add .
git commit -m "Инициализация тестового репозитория kip8test"
git push origin main
```

### Вариант B: репозиторий уже создан и содержит файлы

```bash
# 1. Клонировать существующий репозиторий
git clone https://github.com/bloknett-design/kip8test.git
cd kip8test

# 2. Распаковать архив поверх
unzip /path/to/kip8test.zip -d .

# 3. Проверить diff
git diff

# 4. Закоммитить
git add .
git commit -m "Изоляция от основного репо: manifest, sw, localStorage"
git push origin main
```

После push GitHub Pages автоматически опубликует сайт на `https://bloknett-design.github.io/kip8test/`.

### Вариант C: использовать файлы с Google Drive

Если у вас есть обновлённые файлы на Google Drive (ссылка вверху), скачайте их и поместите в корень репозитория, затем примените правки вручную согласно разделам 1-4 выше. Альтернативно — просто используйте файлы из этого архива.

---

## ✅ Чек-лист проверки после деплоя

Открыть https://bloknett-design.github.io/kip8test/ в Chrome DevTools:

### 1. Manifest
- [ ] DevTools → Application → Manifest
- [ ] `Id:` должен быть `/kip8test/?source=pwa`
- [ ] `Start URL:` должен быть `/kip8test/?source=pwa`
- [ ] `Scope:` должен быть `/kip8test/`

### 2. Service Worker
- [ ] DevTools → Application → Service Workers
- [ ] SW зарегистрирован и активирован (статус: *Activated and is running*)
- [ ] Source: `sw.js`

### 3. Cache Storage
- [ ] DevTools → Application → Cache Storage
- [ ] Должен быть кэш `kipia-test-v124` (НЕ `kipia-v15`!)
- [ ] В кэше должны быть: `index.html`, `manifest.json`, `data/exam-tickets.json`, `data/devices.json`, `data/lockouts.json`, `data/valves.json`, `data/regulators.json`, иконки
- [ ] Опционально: кэш `kipia-images-test-v1` для картинок Google Drive

### 4. localStorage
- [ ] DevTools → Application → Local Storage → `https://bloknett-design.github.io`
- [ ] После переключения темы должен появиться ключ `kip8test:app-theme`
- [ ] **НЕ должен** появиться ключ `app-theme` (без префикса) — это означало бы конфликт с kip8

### 5. Офлайн-режим
- [ ] DevTools → Network → Offline
- [ ] Перезагрузить страницу — приложение должно открыться из кэша
- [ ] Перейти в раздел «Экзаменационные билеты» → открыть билет с картинкой
- [ ] Картинка должна отобразиться из `kipia-images-test-v1` кэша

### 6. Проверка изоляции от kip8
- [ ] Открыть параллельно https://bloknett-design.github.io/kip8/
- [ ] Переключить тему в kip8test (тёмная ↔ светлая)
- [ ] Тема в kip8 **НЕ должна измениться**
- [ ] Проверить Cache Storage в kip8 — кэш `kipia-v15` должен быть на месте, `kipia-test-v124` не должен появиться

### 7. Картинки приборов
- [ ] Открыть раздел «Приборы»
- [ ] В карточках приборов с заполненным полем «Изображение» (share-ссылка из Excel → base64 в `devices.json`) должна отображаться картинка
- [ ] Если для прибора в Excel ещё не указана share-ссылка `https://disk.yandex.ru/i/...` — показывается SVG-заставка с надписью «КИП»

---

## 🔄 Процесс переноса изменений в основной репозиторий

### Сценарий: вы внесли правки в `index.html` в kip8test и хотите перенести их в kip8

```
1. В kip8test:
   - Внести правки в index.html
   - Инкрементировать CACHE_VERSION в sw.js: kipia-test-v124 → kipia-test-v125
   - Запустить тесты: node tests/run-all.js (ожидается 207 passed)
   - Запушить в kip8test
   - Проверить на https://bloknett-design.github.io/kip8test/

2. Если всё OK — перенос в kip8:
   - Скопировать ИЗМЕНЁННЫЕ файлы из kip8test в kip8:
     • index.html — скопировать полностью
     • tests/ — скопировать, если менялись тесты
     • data/ — скопировать, если менялись данные
     • images/ — скопировать, если менялись картинки
     • scripts/ — скопировать, если менялись скрипты
   - НЕ КОПИРОВАТЬ:
     • manifest.json — в kip8 останутся пути /kip8/
     • sw.js — нужно скопировать код, но вернуть имена кэшей kipia-vN
     • .github/workflows/update-exam-tickets.yml — в kip8 cron должен работать
   - В sw.js репозитория kip8:
     • CACHE_VERSION: kipia-v15 → kipia-v16 (инкремент!)
     • IMAGE_CACHE_VERSION: оставить kipia-images-v1
   - Удалить из index.html блок isolateLocalStorage() (если копировали полностью)
   - Запустить тесты: node tests/run-all.js (ожидается 207 passed)
   - Запушить в kip8
   - Проверить на https://bloknett-design.github.io/kip8/
```

### Что инкрементировать при переносе в kip8

| Файл | Действие |
|------|----------|
| `sw.js` | `CACHE_VERSION`: `kipia-v15` → `kipia-v16` (или следующее число) |
| `sw.js` | `IMAGE_CACHE_VERSION`: оставить `kipia-images-v1` (картинки те же) |
| `manifest.json` | **Не трогать** — пути `/kip8/` должны остаться |
| `index.html` | Удалить блок `isolateLocalStorage()` (если копировали полностью) |

---

## 📋 Сводная таблица файлов

| Файл | Изменён для kip8test | Действие при переносе в kip8 |
|------|---------------------|------------------------------|
| `index.html` | ✅ Добавлен `isolateLocalStorage()`, `devGetImageUrl()` для preview-картинок (base64 + прямые URL) | Скопировать, **удалить** блок `isolateLocalStorage()` |
| `manifest.json` | ✅ Все `/kip8/` → `/kip8test/` | **Не копировать** — в kip8 свои пути |
| `sw.js` | ✅ `kipia-test-*` имена кэшей | Скопировать код, **вернуть** имена `kipia-v*`, инкрементировать версию |
| `.github/workflows/update-exam-tickets.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/ci.yml` | ❌ Без изменений | Можно копировать |
| `.github/workflows/sync-devices.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/sync-lockouts.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/sync-valves.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/sync-regulators.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `tests/` | ❌ Без изменений | Можно копировать |
| `scripts/convert-exam-tickets.py` | ✅ Переведён с OneDrive на Яндекс Диск (Public API) | Можно копировать |
| `scripts/sync-devices.py` | ✅ Обновлена ссылка Яндекс Диска | Можно копировать |
| `scripts/sync-lockouts.py` | ✅ Добавлен скрипт | Можно копировать |
| `scripts/sync-valves.py` | ✅ Адаптирован под лист «Клапана_app» | Можно копировать |
| `scripts/sync-regulators.py` | ✅ Адаптирован под лист «Регуляторы_app» | Можно копировать |
| `images/` | ❌ Без изменений | Можно копировать |
| `data/exam-tickets.json` | ❌ Без изменений | Можно копировать |
| `data/devices.json` | ❌ Без изменений (включая base64-картинки, разрешённые из share-ссылок) | Можно копировать |
| `data/lockouts.json` | ❌ Без изменений | Можно копировать |
| `data/valves.json` | ❌ Без изменений | Можно копировать |
| `data/regulators.json` | ❌ Без изменений | Можно копировать |
| `data/phonebook.json` | ❌ Без изменений (обновляется **вручную**) | Можно копировать |

---

## 🛠 Полезные команды

```bash
# Запуск тестов
cd kip8test && node tests/run-all.js

# Локальный сервер для разработки
cd kip8test && python3 -m http.server 8000
# Открыть http://localhost:8000

# Проверка, что manifest.json валиден
python3 -c "import json; json.load(open('manifest.json')); print('OK')"

# Проверка имён кэшей в sw.js
grep 'CACHE_VERSION\|IMAGE_CACHE_VERSION' sw.js

# Проверка префикса localStorage в index.html
grep 'PREFIX' index.html

# Ручной запуск sync-devices.py (приборы + разрешение share-ссылок → base64)
python3 scripts/sync-devices.py
```

---

## ⚠️ Что НЕ делать в этом репозитории

1. **НЕ собирать APK через Bubblewrap.** TWA-манифест в основном репозитории настроен на `kip8`, а не на `kip8test`. Сборка APK здесь приведёт к конфликтам `packageId` и `assetlinks.json`.

2. **НЕ включать cron в `update-exam-tickets.yml` без необходимости.** Это создаст параллельные ежедневные запросы к Яндекс Диску вместе с основным репо. Если нужно протестировать обновление — используйте ручной запуск `workflow_dispatch`.

3. **НЕ копировать `manifest.json` из kip8test в kip8 как есть.** Пути `/kip8test/` сломают установку PWA в основном репозитории.

4. **НЕ копировать `sw.js` из kip8test в kip8 как есть.** Имена кэшей `kipia-test-*` будут конфликтовать с кэшем `kipia-v*` основного репо.

5. **НЕ коммитить `signing.keystore` и пароли.** Как и в основном репозитории — критично.

6. **НЕ удалять `data/phonebook.json`** — файл используется PWA (телефонный справочник, обновляется вручную).

---

## 📞 Ссылки

- Основной репозиторий: https://github.com/bloknett-design/kip8
- Тестовый репозиторий: https://github.com/bloknett-design/kip8test
- Живая страница kip8: https://bloknett-design.github.io/kip8/
- Живая страница kip8test: https://bloknett-design.github.io/kip8test/
- Исходные файлы на Google Drive: https://drive.google.com/drive/folders/1chBGGftT-EGU9EAvmheHhPt52wKJxZke

---

## 📞 Телефонный справочник (ручное обновление)

PWA включает раздел «Телефонный справочник» (в Документации) с контактами ООО ПО «ТОКЕМ» и дочерних организаций.

### Архитектура

```
data/phonebook.json (закоммичен в репо)
    ↓ (PWA забирает через fetch)
Пользователь видит список организаций → карточки контактов
```

**Обновление данных — вручную.** Автоматической синхронизации с Яндекс Диском нет: файл `data/phonebook.json` редактируется и коммитится в репозиторий вручную при изменении контактных данных. Ранее в репозитории присутствовали `scripts/sync-phonebook.py` и `.github/workflows/sync-phonebook.yml`, но они были удалены как неиспользуемые; если автоматическая синхронизация потребуется — скрипт и workflow нужно восстановить из основного репозитория `kip8` (там они активны).

### Файлы

| Файл | Назначение |
|------|------------|
| `data/phonebook.json` | Данные телефонного справочника (закоммичен в репо, обновляется вручную) |

### Структура `phonebook.json`

Файл содержит иерархию: организации → отделы/цеха → лаборатории/секторы → карточки контактов. Каждая карточка содержит ФИО, должность, телефон и email (поля могут быть пустыми).

---

## 🖼 Картинки приборов (preview в карточках)

В карточках приборов (раздел «Приборы») отображаются preview-изображения, если для прибора в Excel-таблице «Перечень КИП ИОС рабочий.xlsx» (лист «Приборы_app», колонка «Изображение») указана индивидуальная публичная ссылка Яндекс Диска вида `https://disk.yandex.ru/i/...`.

### Архитектура

```
Excel-таблица «Перечень КИП ИОС рабочий.xlsx», лист «Приборы_app», колонка «Изображение»
    → содержит индивидуальные публичные share-ссылки https://disk.yandex.ru/i/<ID>
    ↓ (GitHub Actions: workflow_dispatch «Update Devices (TEST)»)
scripts/sync-devices.py → resolve_share_link_images()
    ↓ (Yandex Disk Public API: share-ссылка → file URL → бинарные данные → base64 data URI)
data/devices.json (поле «Изображение» содержит base64 data URI)
    ↓ (PWA: fetch devices.json → devGetImageUrl())
Карточка прибора: <img src="data:image/jpeg;base64,...">
```

**Ключевое:** доступ к общей папке `/СИ_Images` на Яндекс Диске **не нужен**. Каждая картинка загружается по своей индивидуальной публичной ссылке, прописанной в Excel-таблице. Это означает, что:
- добавление/удаление картинки = правка одной ячейки в Excel + повторный запуск `sync-devices.py`;
- нет отдельного скрипта `sync-devices-images.py` и файла `data/devices-images.json` — эта инфраструктура удалена как избыточная;
- base64 встраивается прямо в `devices.json`, поэтому картинки доступны офлайн (кэшируются вместе с `devices.json` в Service Worker).

### Логика `devGetImageUrl(dev)`

Приоритет выбора URL для картинки в карточке прибора:

1. **base64 data URI** в поле `Изображение` (`data:image/...`) — возвращается как есть. Это основной путь: `sync-devices.py` заранее разрешает все share-ссылки и встраивает base64 в `devices.json`.
2. **Прямая ссылка** `http(s)://...` в поле `Изображение` — возвращается как есть. Если по какой-то причине `sync-devices.py` не смог разрешить share-ссылку, она остаётся в поле как URL и PWA попробует загрузить её напрямую.
3. **Иначе** — SVG-заставка с надписью «КИП». Это касается приборов, у которых в Excel колонка «Изображение» пуста или содержит устаревший путь вида `кип_app\СИ_Images\...` (такие пути не обрабатываются и должны быть заменены на share-ссылки).

### Если картинка не отображается

1. Проверить, что в Excel в колонке «Изображение» для нужного прибора стоит именно `https://disk.yandex.ru/i/...` (а не путь вида `кип_app\СИ_Images\...`).
2. Запустить workflow «Update Devices (TEST)» в GitHub Actions (или локально `python3 scripts/sync-devices.py`) — скрипт скачает Excel, разрешит share-ссылки и пересоберёт `data/devices.json`.
3. Инкрементировать `CACHE_VERSION` в `sw.js`, закоммитить обновлённые `data/devices.json` и `sw.js`, запушить.
4. В PWA (после обновления Service Worker) карточка прибора покажет картинку.

### Ограничения

- `sync-devices.py` использует библиотеку **Pillow** для уменьшения картинок до 150×150 px. Если Pillow не установлен в окружении запуска — share-ссылки не разрешаются и в `devices.json` остаются как текст (картинки не отобразятся). В GitHub Actions Pillow устанавливается по умолчанию.
- Дублирующиеся share-ссылки (одно и то же изображение у нескольких приборов) скачиваются один раз и переиспользуются — это оптимизация в `resolve_share_link_images()`.

---

## 🔄 Синхронизация данных (приборы, блокировки, клапаны, регуляторы, билеты)

Все 5 sync-скриптов используют один и тот же подход: Yandex Disk Public API + публичная ссылка на файл `https://disk.yandex.ru/i/B8-c9XnMZlgTkw` (файл «Перечень КИП ИОС рабочий.xlsx»). Секреты НЕ требуются.

| Скрипт | Лист Excel | Выходной JSON | Записей |
|--------|------------|---------------|---------|
| `scripts/sync-devices.py` | `Приборы_app` | `data/devices.json` | 1312 |
| `scripts/sync-lockouts.py` | `Блокировки_app` | `data/lockouts.json` | 526 |
| `scripts/sync-valves.py` | `Клапана_app` | `data/valves.json` | 320 |
| `scripts/sync-regulators.py` | `Регуляторы_app` | `data/regulators.json` | 268 |
| `scripts/convert-exam-tickets.py` | `4 разряд`, `5 разряд`, `6 разряд`, `До 1000 В` (отдельный файл) | `data/exam-tickets.json` | — |

Все соответствующие workflow (`.github/workflows/sync-*.yml`) имеют **отключённый cron** — только ручной запуск через `workflow_dispatch`. Это сделано для изоляции от основного репозитория kip8, чтобы не дублировать ежедневные запросы к Яндекс Диску.

### Ручной запуск любого sync-workflow

В GitHub: Actions → выбрать нужный workflow ("Update Devices (TEST)", "Update Lockouts (TEST)", "Update Valves (TEST)", "Update Regulators (TEST)", "Update Exam Tickets (TEST)") → Run workflow.

---

## 🆕 История обновлений

### 2026-07-22 — удаление избыточной инфраструктуры `devices-images.json`

**Контекст:** предыдущая архитектура preview-картинок приборов опиралась на отдельный скрипт `sync-devices-images.py`, который перебирал общую папку Яндекс Диска `https://disk.yandex.ru/d/cCyJzs4tThjxYA` (подпапка `/СИ_Images`) и собирал словарь «путь → URL» в `data/devices-images.json`. На практике этот подход не работал (папка отдаёт 404, в JSON попадало 0 картинок), да и не нужен: каждая картинка прибора имеет индивидуальную публичную ссылку `https://disk.yandex.ru/i/...`, прописанную прямо в Excel-таблице в колонке «Изображение».

**Что изменилось:**

1. Удалены файлы:
   - `data/devices-images.json` (всегда был пуст: `total_images: 0`);
   - `scripts/sync-devices-images.py` (перебор общей папки больше не нужен);
   - `.github/workflows/sync-devices-images.yml` (workflow для удалённого скрипта).

2. `index.html`: из `devLoad()` убрана параллельная загрузка `devices-images.json`, удалён словарь `devImages`, удалена функция `devNormalizeImagePath()`, упрощена `devGetImageUrl()` — теперь только 3 ветки: base64 / прямой URL / SVG-заставка.

3. `sw.js`: `CACHE_VERSION` v123 → v124; из массива `ASSETS` удалён `./data/devices-images.json`.

4. `README.md`: переписан раздел «🖼 Картинки приборов» — теперь описывает реальную архитектуру (share-ссылки в Excel → `sync-devices.py` → base64 в `devices.json` → `devGetImageUrl()`); обновлены чек-листы и сводная таблица файлов.

**Результат:** preview-картинки приборов работают через существующий механизм `sync-devices.py` (функция `resolve_share_link_images()` уже умеет скачивать share-ссылки и встраивать их как base64). Чтобы картинка появилась в карточке, нужно прописать её share-ссылку в Excel-таблице и перезапустить workflow «Update Devices (TEST)».

### 2026-07-22 — обновление sync-скриптов и UI клапанов/регуляторов

**Что изменилось:**

1. Во всех 4 sync-скриптах (devices, lockouts, valves, regulators) заменена `DEFAULT_PUBLIC_KEY`:
   - Старая: `https://disk.yandex.ru/i/KNVTQ7Q6II7zbA` (404 Not Found)
   - Новая: `https://disk.yandex.ru/i/B8-c9XnMZlgTkw` (рабочая)

2. Переписаны `VALVE_FIELDS` (24 поля, группы 1–6) и `REGULATOR_FIELDS` (12 полей, группы 1–5) под реальные колонки листов «Клапана_app» и «Регуляторы_app».

3. Адаптирована логика sync-скриптов для клапанов и регуляторов: `№ п/п` копируется в `record['ID']`, проверка на пустоту по полям «Марка» и «Параметр» соответственно.

4. Адаптирована JS-логика отображения карточек: заголовок карточки клапана = Марка, регулятора = Параметр; сортировка/группировка в обоих подразделах по полю «Производство».

5. Service Worker: `CACHE_VERSION` v121 → v122 → v123; в `ASSETS` добавлены `data/lockouts.json`, `data/regulators.json`.

6. Тесты: все 207 тестов проходят (0 failed).
