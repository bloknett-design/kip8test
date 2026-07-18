#!/usr/bin/env python3
"""
Синхронизация картинок приборов с публичной папки Яндекс Диска.

Источник: https://disk.yandex.ru/d/cCyJzs4tThjxYA (папка "кип_app")
Структура: кип_app/СИ_Images/{категория}/{имя_файла}.png

Скрипт:
1. Получает список всех файлов из всех подпапок СИ_Images
2. Строит словарь "относительный_путь → preview_url"
3. Сохраняет в data/devices-images.json

Ключи в словаре — нормализованные пути (без "кип_app\\" в начале, с прямыми слэшами),
например: "СИ_Images/flow/пульсар тх.png"
"""
import os
import sys
import json
import time
from pathlib import Path
import requests


YANDEX_PUBLIC_API = 'https://cloud-api.yandex.net/v1/disk/public/resources'
PUBLIC_KEY = 'https://disk.yandex.ru/d/cCyJzs4tThjxYA'
SUBFOLDER = '/СИ_Images'

PROJECT_ROOT = Path(__file__).parent.parent
JSON_OUT = PROJECT_ROOT / 'data' / 'devices-images.json'


def log(msg):
    print(f'[devices-images] {msg}', flush=True)


def list_folder(public_key, path, limit=200):
    """Получает список элементов в папке публичного ресурса."""
    params = {
        'public_key': public_key,
        'path': path,
        'limit': limit,
        'preview_size': 'S',
    }
    resp = requests.get(YANDEX_PUBLIC_API, params=params, timeout=30)
    if resp.status_code != 200:
        log(f'  ОШИБКА: HTTP {resp.status_code} для path={path}')
        return []
    data = resp.json()
    return data.get('_embedded', {}).get('items', [])


def main():
    log(f'Получение списка папок в {SUBFOLDER}...')
    items = list_folder(PUBLIC_KEY, SUBFOLDER)
    
    subfolders = [item for item in items if item['type'] == 'dir']
    files_in_root = [item for item in items if item['type'] == 'file']
    
    log(f'Найдено подпапок: {len(subfolders)}, файлов в корне: {len(files_in_root)}')
    
    images = {}
    
    # Файлы в корне СИ_Images
    for f in files_in_root:
        if f['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            key = f'СИ_Images/{f["name"]}'
            # Используем 'file' URL (прямая загрузка бинарного файла) вместо 'preview'
            # 'file' URL имеет CORS: access-control-allow-origin: *
            # и cache-control: max-age=2592000 (30 дней)
            images[key] = f.get('file', '') or f.get('preview', '')
            log(f'  + {key}')
    
    # Файлы в подпапках
    for sf in subfolders:
        sf_name = sf['name']
        sf_path = f'{SUBFOLDER}/{sf_name}'
        log(f'Обработка подпапки: {sf_path}')
        
        files = list_folder(PUBLIC_KEY, sf_path)
        for f in files:
            if f['type'] == 'file' and f['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                key = f'СИ_Images/{sf_name}/{f["name"]}'
                # Используем 'file' URL (прямая загрузка бинарного файла) вместо 'preview'
                images[key] = f.get('file', '') or f.get('preview', '')
                log(f'  + {key}')
        
        # Небольшая задержка, чтобы не превышать rate limit
        time.sleep(0.3)
    
    log(f'Всего картинок: {len(images)}')
    
    # Сохраняем
    out = {
        'source': f'Yandex Disk (public): {PUBLIC_KEY}',
        'subfolder': SUBFOLDER,
        'total_images': len(images),
        'images': images,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f'JSON сохранён: {JSON_OUT}')
    
    # Проверка: сколько путей из devices.json совпадают
    devices_path = PROJECT_ROOT / 'data' / 'devices.json'
    if devices_path.exists():
        with open(devices_path, 'r', encoding='utf-8') as f:
            dev_data = json.load(f)
        matched = 0
        unmatched = set()
        for d in dev_data['devices']:
            img = d.get('Изображение', '').strip()
            if img:
                # Нормализуем путь: "кип_app\СИ_Images\flow\пульсар тх.png" → "СИ_Images/flow/пульсар тх.png"
                norm = img.replace('\\', '/').replace('кип_app/', '', 1)
                if norm in images:
                    matched += 1
                else:
                    unmatched.add(norm)
        log(f'Совпадений с devices.json: {matched}')
        if unmatched:
            log(f'НЕ найдено картинок для {len(unmatched)} путей:')
            for u in sorted(unmatched)[:10]:
                log(f'  - {u}')
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
