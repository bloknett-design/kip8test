#!/usr/bin/env python3
"""
Синхронизация блокировок с Яндекс Диска (публичная ссылка).
Аналог sync-devices.py для раздела Блокировки.
"""
import os
import sys
import json
import requests

# Публичная ссылка на Excel-файл с блокировками (лист "Блокировки_app")
# ЗАМЕНИТЕ на вашу реальную ссылку Яндекс Диска
YANDEX_PUBLIC_URL = os.environ.get('YANDEX_LOCKOUTS_URL', 'https://disk.yandex.ru/i/ВАША_ССЫЛКА')

def download_xlsx():
    """Скачивает XLSX через Yandex Disk Public API."""
    # Извлекаем public_key из ссылки
    public_key = YANDEX_PUBLIC_URL.strip()

    # Получаем прямую ссылку на скачивание
    api_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'
    params = {'public_key': public_key}

    resp = requests.get(api_url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"Ошибка получения ссылки: {resp.status_code} {resp.text}")
        sys.exit(1)

    download_url = resp.json().get('href')
    if not download_url:
        print("Не удалось получить ссылку на скачивание")
        sys.exit(1)

    # Скачиваем файл
    file_resp = requests.get(download_url, timeout=60)
    if file_resp.status_code != 200:
        print(f"Ошибка скачивания: {file_resp.status_code}")
        sys.exit(1)

    with open('lockouts.xlsx', 'wb') as f:
        f.write(file_resp.content)
    print("✓ XLSX скачан")

def parse_xlsx():
    """Парсит XLSX и возвращает JSON."""
    try:
        import openpyxl
    except ImportError:
        print("Установите openpyxl: pip install openpyxl")
        sys.exit(1)

    wb = openpyxl.load_workbook('lockouts.xlsx', data_only=True)
    ws = wb['Блокировки_app']

    # Читаем заголовки из первой строки
    headers = [cell.value for cell in ws[1]]

    lockouts = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        item = {}
        for i, header in enumerate(headers):
            if header:
                item[header] = row[i] if i < len(row) else None
        lockouts.append(item)

    return {"lockouts": lockouts}

def main():
    print("=== Синхронизация блокировок ===")
    download_xlsx()
    data = parse_xlsx()

    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lockouts.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ Сохранено {len(data['lockouts'])} записей в data/lockouts.json")

    # Cleanup
    if os.path.exists('lockouts.xlsx'):
        os.remove('lockouts.xlsx')

if __name__ == '__main__':
    main()
