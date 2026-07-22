#!/usr/bin/env python3
"""
Синхронизация перечня приборов КИП ИОС с публичной ссылкой Яндекс Диска.

Источник: https://disk.yandex.ru/i/B8-c9XnMZlgTkw (файл "Перечень КИП ИОС рабочий.xlsx")
Лист: "Приборы_app"

Скрипт:
1. Через Yandex Disk Public API получает download_url по публичной ссылке.
2. Скачивает XLSX-файл.
3. Парсит лист "Приборы_app" — заголовки в 1-й строке, данные со 2-й.
4. Сохраняет результат в data/devices.json.

Переменные окружения:
  DEVICES_PUBLIC_KEY — публичная ссылка (по умолчанию https://disk.yandex.ru/i/B8-c9XnMZlgTkw)
  DEVICES_SHEET_NAME — имя листа (по умолчанию "Приборы_app")

Если нет интернета — использует уже существующий data/devices.json как заглушку.
"""
import os
import sys
import json
import re
import base64
import io
import time
from pathlib import Path
from datetime import datetime

import requests
import openpyxl
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


# === Настройки ===
YANDEX_PUBLIC_API = 'https://cloud-api.yandex.net/v1/disk/public/resources'
DEFAULT_PUBLIC_KEY = 'https://disk.yandex.ru/i/B8-c9XnMZlgTkw'
DEFAULT_SHEET_NAME = 'Приборы_app'
DOWNLOAD_DIR = Path('/tmp/devices_download')
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).parent.parent
JSON_OUT = PROJECT_ROOT / 'data' / 'devices.json'


def log(msg):
    print(f'[devices] {msg}', flush=True)


def get_download_url(public_key):
    """Получает download_url для публичного файла через Yandex Disk Public API."""
    log(f'Запрос метаданных публичного файла: {public_key}')
    params = {'public_key': public_key}
    resp = requests.get(YANDEX_PUBLIC_API, params=params, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f'Ошибка API: HTTP {resp.status_code} — {resp.text[:200]}')
    data = resp.json()
    download_url = data.get('file')
    if not download_url:
        raise RuntimeError(f'Не удалось получить download_url: {json.dumps(data, ensure_ascii=False)[:500]}')
    name = data.get('name', 'devices.xlsx')
    return download_url, name


def download_file(url, filename):
    """Скачивает файл по URL."""
    local_path = DOWNLOAD_DIR / filename
    log(f'Скачивание: {url[:80]}...')
    resp = requests.get(url, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f'Ошибка скачивания: HTTP {resp.status_code}')
    local_path.write_bytes(resp.content)
    file_size = local_path.stat().st_size
    log(f'Файл скачан: {local_path} ({file_size} байт)')
    return local_path


def parse_devices(xlsx_path, sheet_name):
    """
    Парсит лист sheet_name из XLSX-файла.
    Заголовки — в 1-й строке, данные — начиная со 2-й.
    Пропускает строки без ID или без Наименования.
    """
    log(f'Парсинг листа "{sheet_name}" из {xlsx_path}')
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    if sheet_name not in wb.sheetnames:
        raise RuntimeError(f'Лист "{sheet_name}" не найден. Доступные листы: {wb.sheetnames}')
    
    ws = wb[sheet_name]
    log(f'Размер листа: {ws.max_row} строк × {ws.max_column} колонок')
    
    # Читаем заголовки из 1-й строки
    headers = []
    for cell in ws[1]:
        val = str(cell.value).strip() if cell.value is not None else ''
        headers.append(val)
    log(f'Заголовки ({len(headers)}): {headers}')
    
    # Читаем данные
    devices = []
    skipped = 0
    for row_idx in range(2, ws.max_row + 1):
        row_values = []
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            val = cell.value
            # Обработка дат
            if isinstance(val, datetime):
                val = val.strftime('%Y-%m-%d')
            elif val is not None:
                val = str(val).strip()
                # Убираем мягкие переносы и нормализуем пробелы
                val = val.replace('\xad', '').replace('\u00a0', ' ')
                val = re.sub(r'\s+', ' ', val).strip()
            else:
                val = ''
            row_values.append(val)
        
        # Создаём словарь "заголовок → значение"
        record = {}
        for h, v in zip(headers, row_values):
            if h:  # пропускаем пустые заголовки
                record[h] = v
        
        # Пропускаем строки без ID или без Наименования
        id_val = record.get('ID', '').strip()
        name_val = record.get('Наименование', '').strip()
        if not id_val and not name_val:
            skipped += 1
            continue
        
        # Если ID — число, преобразуем
        if id_val and id_val.isdigit():
            record['ID'] = int(id_val)
        
        devices.append(record)
    
    log(f'Распарсено записей: {len(devices)}, пропущено: {skipped}')
    return devices, headers


def resolve_share_link_images(devices, max_size=(150, 150)):
    """
    Для записей с share-ссылками (https://disk.yandex.ru/i/...) в поле 'Изображение':
    1. Разрешает ссылку через Yandex Disk API → file URL
    2. Скачивает картинку
    3. Уменьшает до max_size
    4. Заменяет share-ссылку на base64 data URI в поле 'Изображение'
    
    Записи с локальными путями или без картинки — не трогаются.
    """
    if not HAS_PILLOW:
        log('Pillow не установлен — пропуск загрузки картинок')
        return devices
    
    # Соберём уникальные share-ссылки
    share_links = {}  # { shareLink: base64dataUri }
    for d in devices:
        img = (d.get('Изображение') or '').strip()
        if img.startswith('https://disk.yandex.ru/i/'):
            if img not in share_links:
                share_links[img] = None
    
    if not share_links:
        log('Share-ссылок не найдено — картинки не загружаются')
        return devices
    
    log(f'Найдено уникальных share-ссылок: {len(share_links)}')
    session = requests.Session()
    
    for i, link in enumerate(share_links.keys()):
        try:
            # 1. Получаем file URL через API
            log(f'  [{i+1}/{len(share_links)}] Разрешение: {link[:50]}...')
            api_resp = session.get(YANDEX_PUBLIC_API, params={
                'public_key': link,
            }, timeout=30)
            if api_resp.status_code != 200:
                log(f'    ✗ API HTTP {api_resp.status_code}')
                continue
            file_url = api_resp.json().get('file', '')
            if not file_url:
                log(f'    ✗ Нет file URL в ответе')
                continue
            
            # 2. Скачиваем картинку (в той же сессии — cookies сохраняются)
            img_resp = session.get(file_url, timeout=60)
            if img_resp.status_code != 200:
                log(f'    ✗ Download HTTP {img_resp.status_code}')
                continue
            
            # 3. Уменьшаем и конвертируем в base64
            img = Image.open(io.BytesIO(img_resp.content))
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            if img.mode in ('RGBA', 'LA', 'P'):
                img.save(buf, format='PNG')
                mime = 'image/png'
            else:
                img = img.convert('RGB')
                img.save(buf, format='JPEG', quality=85)
                mime = 'image/jpeg'
            b64 = base64.b64encode(buf.getvalue()).decode('ascii')
            data_uri = f'data:{mime};base64,{b64}'
            share_links[link] = data_uri
            log(f'    ✓ {len(b64)/1024:.1f}KB')
            
        except Exception as e:
            log(f'    ✗ Ошибка: {e}')
        time.sleep(0.3)
    
    # Заменяем share-ссылки на base64 в записях
    replaced = 0
    for d in devices:
        img = (d.get('Изображение') or '').strip()
        if img in share_links and share_links[img]:
            d['Изображение'] = share_links[img]
            replaced += 1
    
    log(f'Заменено ссылок на base64: {replaced}')
    return devices


def main():
    public_key = os.environ.get('DEVICES_PUBLIC_KEY', '').strip() or DEFAULT_PUBLIC_KEY
    sheet_name = os.environ.get('DEVICES_SHEET_NAME', '').strip() or DEFAULT_SHEET_NAME
    
    try:
        # 1. Получить download_url
        download_url, filename = get_download_url(public_key)
        
        # 2. Скачать файл
        local_file = download_file(download_url, filename)
        
        # 3. Распарсить лист
        devices, headers = parse_devices(local_file, sheet_name)
        
        # 3.5. Разрешить share-ссылки на картинки → base64
        devices = resolve_share_link_images(devices)
        
        # 4. Сохранить JSON
        out = {
            'title': 'Перечень приборов КИП ИОС',
            'source': f'Yandex Disk (public): {public_key}',
            'sheet': sheet_name,
            'total_devices': len(devices),
            'headers': headers,
            'devices': devices,
        }
        JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(JSON_OUT, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        log(f'JSON сохранён: {JSON_OUT}')
        log(f'Всего приборов: {len(devices)}')
        
        return 0
    
    except Exception as e:
        log(f'ОШИБКА: {e}')
        import traceback
        traceback.print_exc()
        # Если файл уже существует — не падать (используем как заглушку)
        if JSON_OUT.exists():
            log(f'Используется существующий файл: {JSON_OUT}')
            return 0
        return 1


if __name__ == '__main__':
    sys.exit(main())
