#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 531 — точечная проверка 02 (наезд панели на календарь)
# и 06 (полоса шторки итогов поверх календаря): пиксельный анализ
# скриншотов + elementFromPoint по МНОГИМ точкам календаря.
from PIL import Image
import os

DIR = '/home/z/my-project/download/kip8test-task531'

# --- 06: ищем вертикальную синюю линию #4a8fc7 (бортик .ws-tt-edge)
# ВНУТРИ области календаря ---
im = Image.open(os.path.join(DIR, '06-dark-totals-drawer.png')).convert('RGB')
W, H = im.size
print('06: размер', W, H)
px = im.load()

# календарь: правый нижний квадрант под баром; приблизительно:
# x от W-360 до W-10, y от ~60 до ~420 (бар 56 + панель ~330)
def is_blue(c):
    r, g, b = c
    return b > 150 and b - r > 60 and b - g > 40 and r < 140

# сканируем вертикальные линии: колонка с >=80 подряд синими пикселями
cols = {}
for x in range(W - 380, W):
    run = best = 0
    for y in range(55, 430):
        if is_blue(px[x, y]):
            run += 1
            best = max(best, run)
        else:
            run = 0
    if best >= 60:
        cols[x] = best
print('06: вертикальные синие линии (x, длина):', cols)

# --- 02: проверяем зазор между панелью настроек и календарём ---
im2 = Image.open(os.path.join(DIR, '02-dark-popup.png')).convert('RGB')
px2 = im2.load()
W2, H2 = im2.size
print('02: размер', W2, H2)
# панель справа от календаря: ищем тёмную панель (bg #0e1621 ± )
# фон страницы светлее? Возьмём горизонтальную линию y=120 (внутри обеих
# панелей) и найдём границы панелей по цвету фона панелей
y = 130
runs = []
prev = None
for x in range(0, W2):
    c = px2[x, y]
    dark = sum(c) < 200          # панельные тёмные области
    if dark != prev:
        runs.append((x, dark))
        prev = dark
print('02: границы тёмных зон на y=130:', runs[:12])
