#!/usr/bin/env python3
"""
Конвертирует xlsx-файл в JSON для PWA «КИПиА».

Логика:
  1. Если xlsx-файл есть в репозитории (data/exam-tickets.xlsx) — берём его.
  2. Если нет — пробуем скачать с OneDrive по ссылке общего доступа.
  3. Конвертируем все листы в JSON и сохраняем.

Запускается через GitHub Actions (workflow_dispatch или schedule).

Единый принцип работы с картинками (поле Image):
  - Значение из ячейки столбца Image копируется в JSON КАК ЕСТЬ.
  - В Excel-таблице должны быть указаны ТОЛЬКО HTTP/HTTPS-ссылки
    на изображения (например, Google Drive share-ссылка с доступом
    «Anyone with the link», либо прямая ссылка на PNG/JPG).
  - Любые другие значения (локальные Windows-пути, относительные пути
    вида images/tickets/...) НЕ КОНВЕРТИРУЮТСЯ и НЕ ОТОБРАЖАЮТСЯ в PWA —
    они просто сохраняются в JSON как строка, но фронтенд через
    isWorkingUrl() их отклонит.
  - Это гарантирует, что картинки грузятся по единому принципу —
    только по URL из ячейки Image.
"""

import json
import os
import re
import sys

import openpyxl

# Попробуем импортировать requests (может не быть при оффлайн-конвертации)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ============================================================
# Конфигурация
# ============================================================
ONEDRIVE_SHARE_URL = os.environ.get(
    "ONEDRIVE_SHARE_URL",
    "https://1drv.ms/x/c/c9414adb26fe5b28/IQDqsaT9uFR_T6HBWRyYhhEtAXDVcDPDoT3-O_um4E6V7O0?e=IKtgRl",
)

LOCAL_XLSX = os.environ.get("LOCAL_XLSX", "data/exam-tickets.xlsx")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "data/exam-tickets.json")

SHEETS_CONFIG = {
    "4 разряд": {"id": "tickets-4", "title": "Билеты на 4 разряд"},
    "5 разряд": {"id": "tickets-5", "title": "Билеты на 5 разряд"},
    "6 разряд": {"id": "tickets-6", "title": "Билеты на 6 разряд"},
    "До 1000 В": {"id": "tickets-1000v", "title": "Билеты до 1000 В"},
}


# ============================================================
# Стандартизация имён полей
# ============================================================
# Excel-таблица содержит русские заголовки с пробелами и спецсимволами
# (№ билета, № вопроса, Название литературы и т.д.).
# Для JSON используем латинские snake_case имена — это упрощает
# работу в JavaScript, устраняет проблемы с кодировками в escape-
# последовательностях (\u2116 для № и т.д.) и делает код читаемее.
#
# Фронтенд PWA (index.html) читает новые имена, но также поддерживает
# старые русские имена как fallback — это обеспечивает плавную
# миграцию, если где-то остался старый JSON.
FIELD_NAME_MAP = {
    "ID": "id",
    "№ билета": "ticket_number",
    "№билета": "ticket_number",        # вариант без пробела (для надёжности)
    "№ вопроса": "question_number",
    "№вопроса": "question_number",     # вариант без пробела
    "Вопрос": "question",
    "Ответ": "answer",
    "Image": "image_url",
    "Название литературы": "literature_name",
    "Файл": "file_url",
}

# Обратное отображение (для fallback в JS) — не используется в конвертере,
# но задокументировано здесь для согласованности с фронтендом.
FIELD_NAME_REVERSE_MAP = {v: k for k, v in FIELD_NAME_MAP.items()}


def _normalize_field_name(raw_name: str) -> str:
    """Конвертирует русское имя поля из Excel в стандартное латинское.

    Если поле не входит в FIELD_NAME_MAP — возвращает оригинальное имя
    (это позволяет добавлять новые столбцы в Excel без изменения кода).
    """
    if not raw_name:
        return ""
    name = raw_name.strip()
    return FIELD_NAME_MAP.get(name, name)


def _is_http_url(s: str) -> bool:
    """Возвращает True, если строка начинается с http:// или https://.

    Это ЕДИНСТВЕННЫЙ допустимый формат значения для поля Image.
    Любые другие значения (локальные пути, относительные пути) будут
    проигнорированы фронтендом PWA через функцию isWorkingUrl().
    """
    return s.strip().lower().startswith(("http://", "https://"))


def _normalize_image_field(raw_value: str) -> str:
    """Нормализует значение поля Image из Excel.

    Единый принцип: только HTTP/HTTPS-ссылки.
    - Если значение — URL (http/https) → пропускаем как есть.
    - Если значение — что-то другое (локальный путь Windows,
      относительный путь, имя файла) → возвращаем пустую строку,
      чтобы в JSON не попал неработающий путь.
    """
    if not raw_value or not raw_value.strip():
        return ""
    if _is_http_url(raw_value):
        return raw_value.strip()
    # Любое нерабочее значение игнорируем — оно не должно отображаться.
    # В логе конвертера это будет видно как предупреждение.
    print(f"  [ВНИМАНИЕ] Поле Image содержит не-URL значение, "
          f"оно будет проигнорировано в PWA: {raw_value[:80]}",
          file=sys.stderr)
    return ""


def _normalize_file_field(raw_value: str) -> str:
    """Нормализует значение поля Файл (ссылка на файл литературы).

    Аналогично полю Image: принимаются только HTTP/HTTPS-ссылки.
    """
    if not raw_value or not raw_value.strip():
        return ""
    if _is_http_url(raw_value):
        return raw_value.strip()
    # Нерабочие пути — игнорируем (но не выводим предупреждение,
    # т.к. поле Файл может быть пустым, если литература без ссылки)
    return ""


def _unescape_url(url: str) -> str:
    """Расшифровывает экранированные символы в URL."""
    return url.replace("\\u0026", "&").replace("&amp;", "&")


def _try_download(dl_url: str, dest: str, headers: dict) -> bool:
    """Пытается скачать файл по URL и проверяет, что это xlsx (ZIP)."""
    try:
        r = requests.get(dl_url, headers=headers, allow_redirects=True, timeout=30)
        if r.status_code == 200 and len(r.content) > 100 and r.content[:2] == b"PK":
            with open(dest, "wb") as f:
                f.write(r.content)
            print(f"Скачано: {len(r.content)} байт")
            return True
        print(f"Скачивание: статус {r.status_code}, размер {len(r.content)}, первые байты: {r.content[:4]}")
    except Exception as e:
        print(f"Ошибка скачивания: {e}")
    return False


def download_xlsx(share_url: str, dest: str) -> bool:
    """Скачивает xlsx по ссылке OneDrive (несколько способов)."""
    if not HAS_REQUESTS:
        print("Библиотека requests недоступна, скачивание невозможно", file=sys.stderr)
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # ================================================================
    # Способ 1: Извлечение FileGetUrl из HTML-страницы (САМЫЙ НАДЁЖНЫЙ)
    # ================================================================
    try:
        print(f"Открываем ссылку: {share_url}")
        r = requests.get(share_url, headers=headers, allow_redirects=True, timeout=20)
        page_text = r.text
        print(f"Страница загружена: {len(page_text)} символов, URL: {r.url[:80]}...")

        # 1a. Ищем FileGetUrl (содержит tempauth-токен для скачивания)
        file_get_match = re.search(
            r'"FileGetUrl"\s*:\s*"(https://[^"]+)"',
            page_text,
        )
        if file_get_match:
            dl_url = _unescape_url(file_get_match.group(1))
            print(f"Найден FileGetUrl (длина {len(dl_url)})")
            if _try_download(dl_url, dest, headers):
                return True
            print("FileGetUrl не дал валидный xlsx, пробуем другие способы...")

        # 1b. Ищем @content.downloadUrl
        content_dl_match = re.search(
            r'"@content\.downloadUrl"\s*:\s*"(https://[^"]+)"',
            page_text,
        )
        if content_dl_match:
            dl_url = _unescape_url(content_dl_match.group(1))
            print(f"Найден @content.downloadUrl (длина {len(dl_url)})")
            if _try_download(dl_url, dest, headers):
                return True
            print("@content.downloadUrl не дал валидный xlsx, пробуем другие способы...")

        # 1c. Ищем любой URL с tempauth на my.microsoftpersonalcontent.com
        tempauth_match = re.search(
            r'(https://my\.microsoftpersonalcontent\.com/[^"\s]+tempauth=[^"\s]+)',
            page_text,
        )
        if tempauth_match:
            dl_url = _unescape_url(tempauth_match.group(1))
            print(f"Найден tempauth URL на my.microsoftpersonalcontent.com (длина {len(dl_url)})")
            if _try_download(dl_url, dest, headers):
                return True

        # 1d. Ищем любой URL с tempauth на onedrive.live.com
        tempauth_match2 = re.search(
            r'(https://onedrive\.live\.com/[^"\s]+download\.aspx[^"\s]*tempauth=[^"\s]+)',
            page_text,
        )
        if tempauth_match2:
            dl_url = _unescape_url(tempauth_match2.group(1))
            print(f"Найден tempauth URL на onedrive.live.com (длина {len(dl_url)})")
            if _try_download(dl_url, dest, headers):
                return True

    except Exception as e:
        print(f"Ошибка при разборе страницы: {e}")

    # ================================================================
    # Способ 2: Graph API shares (может потребовать токен)
    # ================================================================
    try:
        import base64
        encoded = base64.urlsafe_b64encode(share_url.encode()).decode().rstrip("=")
        api_url = f"https://graph.microsoft.com/v1.0/shares/u!{encoded}/root/content"
        print(f"Пробуем Graph API: {api_url[:80]}...")
        r = requests.get(api_url, headers=headers, allow_redirects=True, timeout=30)
        if r.status_code == 200 and len(r.content) > 100 and r.content[:2] == b"PK":
            with open(dest, "wb") as f:
                f.write(r.content)
            print(f"Скачано через Graph API: {len(r.content)} байт")
            return True
        print(f"Graph API: статус {r.status_code}")
    except Exception as e:
        print(f"Graph API: ошибка — {e}")

    print("Не удалось скачать файл с OneDrive", file=sys.stderr)
    return False


def convert_xlsx_to_json(xlsx_path: str, json_path: str) -> bool:
    """Конвертирует xlsx в JSON."""
    wb = openpyxl.load_workbook(xlsx_path)
    all_data = {}

    for sheet_name, config in SHEETS_CONFIG.items():
        if sheet_name not in wb.sheetnames:
            print(f"Лист «{sheet_name}» не найден, пропускаю", file=sys.stderr)
            continue

        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue

        headers = [str(h) if h else "" for h in rows[0]]
        # Стандартизируем имена полей: русские → латинские snake_case
        normalized_headers = [_normalize_field_name(h) for h in headers]
        data_rows = []

        for row in rows[1:]:
            obj = {}
            for i, val in enumerate(row):
                if i < len(normalized_headers):
                    field_name = normalized_headers[i]
                    cell_val = str(val) if val is not None else ""
                    # Единый принцип: только HTTP/HTTPS-ссылки.
                    # Локальные/относительные пути игнорируются —
                    # фронтенд PWA отображает только URL.
                    if field_name == "image_url":
                        cell_val = _normalize_image_field(cell_val)
                    elif field_name == "file_url":
                        cell_val = _normalize_file_field(cell_val)
                    obj[field_name] = cell_val
            data_rows.append(obj)

        all_data[config["id"]] = {
            "title": config["title"],
            "sheet": sheet_name,
            "headers": normalized_headers,
            "rows": data_rows,
            "total": len(data_rows),
        }
        print(f"  {sheet_name}: {len(data_rows)} строк")

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    size = os.path.getsize(json_path)
    print(f"JSON сохранён: {json_path} ({size / 1024:.1f} КБ)")
    return True


def main():
    xlsx_path = LOCAL_XLSX

    # 1. Проверяем локальный xlsx в репозитории
    if os.path.isfile(xlsx_path):
        print(f"Найден локальный файл: {xlsx_path}")
    else:
        # 2. Пробуем скачать с OneDrive
        print("Локальный xlsx не найден, скачиваем с OneDrive...")
        xlsx_path = "/tmp/exam_tickets.xlsx"
        if not download_xlsx(ONEDRIVE_SHARE_URL, xlsx_path):
            print("ОШИБКА: не удалось получить xlsx файл", file=sys.stderr)
            sys.exit(1)

    # Проверяем что файл валидный
    try:
        with open(xlsx_path, "rb") as f:
            header = f.read(4)
        if header[:2] != b"PK":
            print(f"ОШИБКА: файл {xlsx_path} не является xlsx (не ZIP)", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"ОШИБКА: не удалось прочитать файл — {e}", file=sys.stderr)
        sys.exit(1)

    print("Конвертация xlsx → JSON...")
    if not convert_xlsx_to_json(xlsx_path, OUTPUT_PATH):
        sys.exit(1)

    print("Готово!")


if __name__ == "__main__":
    main()
