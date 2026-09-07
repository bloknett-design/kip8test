# -*- coding: utf-8 -*-
# Минимальный репро: кто из page.evaluate зовёт window.print?
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('about:blank')

    r1 = page.evaluate("window.__c = 0; window.print = function(){ window.__c++; };")
    print('1) после установки стаба:', page.evaluate("window.__c"), '| возврат install:', str(r1)[:60])

    r2 = page.evaluate("window.__c")
    print('2) чтение __c после обычного чтения:', r2)

    # гипотеза: evaluate, возвращающий функцию, может её вызвать
    r3 = page.evaluate("(function(){ return 42; })")
    print('3) evaluate функции-выражения:', str(r3)[:60], '| __c:', page.evaluate("window.__c"))

    r4 = page.evaluate("window.__arr = []; window.__arr")
    print('4) массив:', r4, '| __c:', page.evaluate("window.__c"))
    browser.close()
