# -*- coding: utf-8 -*-
# Репро 2: какая именно evaluate-строка зовёт window.print?
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('about:blank')

    # A: однострочный install (без точки с запятой в конце)
    page.evaluate("window.print = function(){ window.__c = (window.__c || 0) + 1; }")
    cA = page.evaluate("() => window.__c || 0")
    print('A) install без ";" в конце ->', cA)

    # B: install с присваиванием счётчика ДО (два оператора)
    page.evaluate("window.__c = 0; window.print = function(){ window.__c++; };")
    cB = page.evaluate("() => window.__c")
    print('B) два оператора + ";" ->', cB)

    # C: как B, но чтение функцией (не строкой)
    print('C) чтение function-evaluate ->', page.evaluate("() => window.__c"))

    # D: стек фантомного вызова
    page.evaluate("""() => {
        window.__stacks = [];
        window.print = function(){ window.__stacks.push(new Error('ph').stack); };
        window.__c = 0;
    }""")
    cD = page.evaluate("() => window.__c")
    print('D) install через function-evaluate ->', cD)
    for s in page.evaluate("() => window.__stacks"):
        print('   phantom stack:', s.split('\n')[1:3])
    browser.close()
