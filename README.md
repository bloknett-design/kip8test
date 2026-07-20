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
| `CACHE_VERSION` | `kipia-v15` | `kipia-test-v1` |
| `IMAGE_CACHE_VERSION` | `kipia-images-v1` | `kipia-images-test-v1` |

**Почему это важно:** Cache Storage общий на весь origin `bloknett-design.github.io`. Одинаковые имена кэшей привели бы к взаимному удалению данных и поломке офлайн-режима в обоих репозиториях.

При обновлении файлов в этом репо **инкрементируйте** `CACHE_VERSION`:
- `kipia-test-v1` → `kipia-test-v2` → `kipia-test-v3` → ...

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
- [ ] Должен быть кэш `kipia-test-v1` (НЕ `kipia-v15`!)
- [ ] В кэше должны быть: `index.html`, `manifest.json`, `data/exam-tickets.json`, иконки
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
- [ ] Проверить Cache Storage в kip8 — кэш `kipia-v15` должен быть на месте, `kipia-test-v1` не должен появиться

---

## 🔄 Процесс переноса изменений в основной репозиторий

### Сценарий: вы внесли правки в `index.html` в kip8test и хотите перенести их в kip8

```
1. В kip8test:
   - Внести правки в index.html
   - Инкрементировать CACHE_VERSION в sw.js: kipia-test-v1 → kipia-test-v2
   - Запустить тесты: node tests/run-all.js (ожидается 207 passed)
   - Запушить в kip8test
   - Проверить на https://bloknett-design.github.io/kip8test/

2. Если всё OK — перенос в kip8:
   - Скопировать ИЗМЕНЁННЫЕ файлы из kip8test в kip8:
     • index.html — скопировать полностью
     • tests/ — скопировать, если менялись тесты
     • data/ — скопировать, если менялись билеты
     • images/ — скопировать, если менялись картинки
     • scripts/ — скопировать, если менялся конвертер
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
| `index.html` | ✅ Добавлен `isolateLocalStorage()` | Скопировать, **удалить** блок `isolateLocalStorage()` |
| `manifest.json` | ✅ Все `/kip8/` → `/kip8test/` | **Не копировать** — в kip8 свои пути |
| `sw.js` | ✅ `kipia-test-*` имена кэшей | Скопировать код, **вернуть** имена `kipia-v*`, инкрементировать версию |
| `.github/workflows/update-exam-tickets.yml` | ✅ Cron закомментирован | **Не копировать** — в kip8 cron нужен |
| `.github/workflows/ci.yml` | ❌ Без изменений | Можно копировать |
| `tests/` | ❌ Без изменений | Можно копировать |
| `scripts/convert-exam-tickets.py` | ✅ Переведён с OneDrive на Яндекс Диск (Public API) | Можно копировать |
| `images/` | ❌ Без изменений | Можно копировать |
| `data/exam-tickets.json` | ❌ Без изменений | Можно копировать |

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
```

---

## ⚠️ Что НЕ делать в этом репозитории

1. **НЕ собирать APK через Bubblewrap.** TWA-манифест в основном репозитории настроен на `kip8`, а не на `kip8test`. Сборка APK здесь приведёт к конфликтам `packageId` и `assetlinks.json`.

2. **НЕ включать cron в `update-exam-tickets.yml` без необходимости.** Это создаст параллельные ежедневные запросы к Яндекс Диску вместе с основным репо. Если нужно протестировать обновление — используйте ручной запуск `workflow_dispatch`.

3. **НЕ копировать `manifest.json` из kip8test в kip8 как есть.** Пути `/kip8test/` сломают установку PWA в основном репозитории.

4. **НЕ копировать `sw.js` из kip8test в kip8 как есть.** Имена кэшей `kipia-test-*` будут конфликтовать с кэшем `kipia-v*` основного репо.

5. **НЕ коммитить `signing.keystore` и пароли.** Как и в основном репозитории — критично.

---

## 📞 Ссылки

- Основной репозиторий: https://github.com/bloknett-design/kip8
- Тестовый репозиторий: https://github.com/bloknett-design/kip8test
- Живая страница kip8: https://bloknett-design.github.io/kip8/
- Живая страница kip8test: https://bloknett-design.github.io/kip8test/
- Исходные файлы на Google Drive: https://drive.google.com/drive/folders/1chBGGftT-EGU9EAvmheHhPt52wKJxZke

---

## 📞 Телефонный справочник (синхронизация с Яндекс Диском)

PWA включает раздел «Телефонный справочник» (в Документации) с контактами ООО ПО «ТОКЕМ» и дочерних организаций. Данные синхронизируются с Excel-файлом на Яндекс Диске через GitHub Actions.

### Архитектура

```
Яндекс Диск (XLS/XLSX)
    ↓ (GitHub Actions, раз в день)
scripts/sync-phonebook.py
    ↓ (скачивание + парсинг по форматированию ячеек)
data/phonebook.json
    ↓ (PWA забирает через fetch)
Пользователь видит список организаций → карточки контактов
```

### Настройка синхронизации

#### 1. Получите OAuth-токен Яндекс Диска

1. Откройте ссылку:
   ```
   https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990e0da0f4fac8a1c1b8f67a228f0
   ```
2. Разрешите доступ приложению «Яндекс.Диск»
3. Скопируйте полученный токен (действителен 1 год)

#### 2. Добавьте секреты в репозиторий

В Settings → Secrets and variables → Actions добавьте:

| Имя секрета | Значение |
|-------------|----------|
| `YANDEX_DISK_TOKEN` | OAuth-токен из шага 1 |
| `YANDEX_DISK_PHONEBOOK_PATH` | Путь к файлу на Яндекс Диске, например `/Справочник/Телефоны.xls` |

#### 3. Включите расписание

В файле `.github/workflows/sync-phonebook.yml` раскомментируйте блок `schedule`:

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: '0 6 * * *'   # каждый день в 06:00 UTC (09:00 МСК)
```

#### 4. Ручной запуск

В GitHub: Actions → "Update Phonebook (TEST)" → Run workflow

### Правила парсинга Excel

Скрипт `scripts/sync-phonebook.py` анализирует форматирование ячеек:

| Тип ячейки | Признаки | Уровень |
|------------|----------|---------|
| **Шапка группы** | Аквамарин + размер шрифта 20 | 1 (организация) |
| **Название группы** | Аквамарин (без размера 20) | 2 (отдел/цех) |
| **Подгруппа** | НЕ аквамарин + жирный + без ФИО и телефона | 3 (лаборатория/сектор) |
| **Запись** | Любая другая | Карточка контакта |

«Аквамарин» = голубые/бирюзовые цвета: `FF33CCCC`, `FF99CCFF`, `FFCCFFFF`

Если ФИО или телефон у записи отсутствуют — поля сохраняются пустыми.

### Файлы

| Файл | Назначение |
|------|------------|
| `.github/workflows/sync-phonebook.yml` | GitHub Actions workflow |
| `scripts/sync-phonebook.py` | Скрипт скачивания + парсинга |
| `data/phonebook.json` | Результат (закоммичен в репо) |

### Если токен не задан

Скрипт использует уже существующий `data/phonebook.json` как заглушку — PWA продолжает работать с последними закоммиченными данными.
