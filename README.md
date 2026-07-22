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
| `CACHE_VERSION` | `kipia-v15` | `kipia-test-v123` |
| `IMAGE_CACHE_VERSION` | `kipia-images-v1` | `kipia-images-test-v1` |

**Почему это важно:** Cache Storage общий на весь origin `bloknett-design.github.io`. Одинаковые имена кэшей привели бы к взаимному удалению данных и поломке офлайн-режима в обоих репозиториях.

При обновлении файлов в этом репо **инкрементируйте** `CACHE_VERSION`:
- `kipia-test-v1` → `kipia-test-v2` → … → `kipia-test-v123` (текущая)

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
- [ ] Должен быть кэш `kipia-test-v123` (НЕ `kipia-v15`!)
- [ ] В кэше должны быть: `index.html`, `manifest.json`, `data/exam-tickets.json`, `data/devices.json`, `data/devices-images.json`, `data/lockouts.json`, `data/valves.json`, `data/regulators.json`, иконки
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
- [ ] Проверить Cache Storage в kip8 — кэш `kipia-v15` должен быть на месте, `kipia-test-v123` не должен появиться

### 7. Картинки приборов
- [ ] Открыть раздел «Приборы»
- [ ] В карточках приборов с заполненным полем «Изображение» должна отображаться картинка (если в `data/devices-images.json` есть URL для соответствующего пути)
- [ ] Если URL отсутствует — показывается SVG-заставка с надписью «КИП»
- [ ] В Console должно появиться сообщение `[devices] Загружено URL картинок: N` (N = количество записей в `devices-images.json`)

---

## 🔄 Процесс переноса изменений в основной репозиторий

### Сценарий: вы внесли правки в `index.html` в kip8test и хотите перенести их в kip8

```
1. В kip8test:
   - Внести правки в index.html
   - Инкрементировать CACHE_VERSION в sw.js: kipia-test-v123 → kipia-test-v124
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
| `index.html` | ✅ Добавлен `isolateLocalStorage()`, расширен `devGetImageUrl()` для preview-картинок | Скопировать, **удалить** блок `isolateLocalStorage()` |
| `manifest.json` | ✅ Все `/kip8/` → `/kip8test/` | **Не копировать** — в kip8 свои пути |
| `sw.js` | ✅ `kipia-test-*` имена кэшей, добавлен `data/devices-images.json` в ASSETS | Скопировать код, **вернуть** имена `kipia-v*`, инкрементировать версию |
| `.github/workflows/update-exam-tickets.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/ci.yml` | ❌ Без изменений | Можно копировать |
| `.github/workflows/sync-devices.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/sync-lockouts.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/sync-valves.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/sync-regulators.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/sync-devices-images.yml` | ❌ Без изменений (только `workflow_dispatch`) | Можно копировать |
| `tests/` | ❌ Без изменений | Можно копировать |
| `scripts/convert-exam-tickets.py` | ✅ Переведён с OneDrive на Яндекс Диск (Public API) | Можно копировать |
| `scripts/sync-devices.py` | ✅ Обновлена ссылка Яндекс Диска | Можно копировать |
| `scripts/sync-lockouts.py` | ✅ Добавлен скрипт | Можно копировать |
| `scripts/sync-valves.py` | ✅ Адаптирован под лист «Клапана_app» | Можно копировать |
| `scripts/sync-regulators.py` | ✅ Адаптирован под лист «Регуляторы_app» | Можно копировать |
| `scripts/sync-devices-images.py` | ❌ Без изменений | Можно копировать |
| `images/` | ❌ Без изменений | Можно копировать |
| `data/exam-tickets.json` | ❌ Без изменений | Можно копировать |
| `data/devices.json` | ❌ Без изменений | Можно копировать |
| `data/devices-images.json` | ✅ Подключён к UI (preview-картинки в карточках приборов) | Можно копировать |
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

# Ручной запуск sync-devices-images.py (картинки приборов)
python3 scripts/sync-devices-images.py
```

---

## ⚠️ Что НЕ делать в этом репозитории

1. **НЕ собирать APK через Bubblewrap.** TWA-манифест в основном репозитории настроен на `kip8`, а не на `kip8test`. Сборка APK здесь приведёт к конфликтам `packageId` и `assetlinks.json`.

2. **НЕ включать cron в `update-exam-tickets.yml` без необходимости.** Это создаст параллельные ежедневные запросы к Яндекс Диску вместе с основным репо. Если нужно протестировать обновление — используйте ручной запуск `workflow_dispatch`.

3. **НЕ копировать `manifest.json` из kip8test в kip8 как есть.** Пути `/kip8test/` сломают установку PWA в основном репозитории.

4. **НЕ копировать `sw.js` из kip8test в kip8 как есть.** Имена кэшей `kipia-test-*` будут конфликтовать с кэшем `kipia-v*` основного репо.

5. **НЕ коммитить `signing.keystore` и пароли.** Как и в основном репозитории — критично.

6. **НЕ удалять `data/phonebook.json` и `scripts/sync-devices-images.py`/`.github/workflows/sync-devices-images.yml`/`data/devices-images.json`** — эти файлы используются PWA (телефонный справочник и картинки приборов соответственно).

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

В карточках приборов (раздел «Приборы») отображаются preview-изображения, если для прибора указано поле `Изображение`.

### Архитектура

```
Папка Яндекс Диска: кип_app/СИ_Images/{категория}/{имя_файла}.png
    ↓ (GitHub Actions, ручной запуск)
scripts/sync-devices-images.py
    ↓ (Yandex Disk Public API: список файлов → preview/file URL)
data/devices-images.json (словарь "нормализованный_путь → URL")
    ↓ (PWA: fetch + devGetImageUrl)
Карточка прибора: <img src="URL из словаря">
```

### Логика `devGetImageUrl(dev)`

Приоритет выбора URL для картинки:

1. **base64 data URI** в поле `Изображение` (`data:image/...`) — возвращается как есть.
2. **Прямая ссылка** `http(s)://...` в поле `Изображение` — возвращается как есть.
3. **Путь** вида `кип_app\СИ_Images\flow\пульсар тх.png` — нормализуется в `СИ_Images/flow/пульсар тх.png` и ищется в `devImages` (загружается из `data/devices-images.json`). Если найден — возвращается URL.
4. **Иначе** — SVG-заставка с надписью «КИП».

### Загрузка `devices-images.json` в PWA

Файл `data/devices-images.json` загружается в `index.html` параллельно с `data/devices.json` в функции `devLoad()`. Загрузка некритична: если файл недоступен (404) или пуст, `devImages` остаётся пустым объектом, и для всех путей показывается SVG-заставка. Когда файл будет обновлён (после успешного запуска `sync-devices-images.py`), картинки автоматически появятся в карточках при следующей загрузке PWA.

Файл также пред-кэшируется в Service Worker (добавлен в массив `ASSETS` в `sw.js`), поэтому доступен офлайн.

### Файлы

| Файл | Назначение |
|------|------------|
| `scripts/sync-devices-images.py` | Скрипт сбора URL картинок с Яндекс Диска |
| `.github/workflows/sync-devices-images.yml` | GitHub Actions workflow (ручной запуск) |
| `data/devices-images.json` | Словарь путь→URL (закоммичен в репо) |

### Ручной запуск обновления картинок

В GitHub: Actions → "Update Devices Images (TEST)" → Run workflow. Или локально:

```bash
python3 scripts/sync-devices-images.py
```

### Если папка Яндекс Диска недоступна

Скрипт выведет `HTTP 404 для path=/СИ_Images` и сохранит `devices-images.json` с `total_images: 0`. PWA продолжит работать с SVG-заставками. Чтобы восстановить картинки, нужно проверить публичную ссылку `https://disk.yandex.ru/d/cCyJzs4tThjxYA` и наличие в ней папки `СИ_Images`.

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

### 2026-07-22 — обновление sync-скриптов и UI клапанов/регуляторов

**Что изменилось:**

1. Во всех 4 sync-скриптах (devices, lockouts, valves, regulators) заменена `DEFAULT_PUBLIC_KEY`:
   - Старая: `https://disk.yandex.ru/i/KNVTQ7Q6II7zbA` (404 Not Found)
   - Новая: `https://disk.yandex.ru/i/B8-c9XnMZlgTkw` (рабочая)

2. Переписаны `VALVE_FIELDS` (24 поля, группы 1–6) и `REGULATOR_FIELDS` (12 полей, группы 1–5) под реальные колонки листов «Клапана_app» и «Регуляторы_app».

3. Адаптирована логика sync-скриптов для клапанов и регуляторов: `№ п/п` копируется в `record['ID']`, проверка на пустоту по полям «Марка» и «Параметр» соответственно.

4. Адаптирована JS-логика отображения карточек: заголовок карточки клапана = Марка, регулятора = Параметр; сортировка/группировка в обоих подразделах по полю «Производство».

5. Service Worker: `CACHE_VERSION` v121 → v122 → v123; в `ASSETS` добавлены `data/lockouts.json`, `data/regulators.json`, `data/devices-images.json`.

6. Подключён `data/devices-images.json` к UI: функция `devGetImageUrl()` теперь ищет URL по нормализованному пути в словаре `devImages`, который загружается параллельно с `devices.json`.

7. Тесты: все 207 тестов проходят (0 failed).
