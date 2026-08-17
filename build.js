#!/usr/bin/env node
// ============================================================
// Build-скрипт для kip8test — два режима:
//   node build.js mobile   → PWA-бандл (base.css + mobile.css)
//   node build.js desktop  → Electron-бандл (base.css + desktop.css)
//
// Стратегия: CSS-файлы собираются в один <style> блок,
// инлайнятся в index.html. Изображения и данные копируются как есть.
// Результат — автономный index.html для offline.
// ============================================================

import { readFileSync, writeFileSync, copyFileSync, mkdirSync, readdirSync, existsSync, rmSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { minify } from 'terser';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const mode = process.argv[2] || 'mobile';
const isDesktop = mode === 'desktop';

if (!['mobile', 'desktop'].includes(mode)) {
    console.error('Usage: node build.js [mobile|desktop]');
    process.exit(1);
}

const outDir = resolve(__dirname, isDesktop ? 'dist-desktop' : 'dist-mobile');
const srcDir = resolve(__dirname, 'src');

console.log(`\n🔧 Building ${mode.toUpperCase()} bundle...\n`);

// --- 1. Очистить выходную директорию ---
if (existsSync(outDir)) rmSync(outDir, { recursive: true });
mkdirSync(outDir, { recursive: true });

// --- 2. Собрать CSS ---
const cssFiles = ['base.css', `${mode}.css`];
let combinedCss = '';
for (const file of cssFiles) {
    const filePath = resolve(srcDir, 'css', file);
    if (existsSync(filePath)) {
        const content = readFileSync(filePath, 'utf-8');
        combinedCss += `/* === ${file} === */\n${content}\n`;
        console.log(`  ✓ CSS: ${file} (${content.split('\n').length} lines)`);
    } else {
        console.warn(`  ⚠ CSS not found: ${file}`);
    }
}
console.log(`  → Total CSS: ${combinedCss.split('\n').length} lines (${(combinedCss.length / 1024).toFixed(1)} KB)`);

// --- 3. Прочитать HTML-шаблон ---
const htmlPath = resolve(srcDir, 'index.html');
let html = readFileSync(htmlPath, 'utf-8');
console.log(`  ✓ HTML template: ${(html.length / 1024).toFixed(1)} KB`);

// --- 4. Заменить <link> на инлайн <style> ---
// Убираем все <link> на CSS-файлы
html = html.replace(/<link[^>]*href=["']\.\/css\/(?:base|mobile|desktop)\.css["'][^>]*>\n?/g, '');
// Вставляем инлайн <style> после <title>
html = html.replace(
    /(<title>КИПиА<\/title>)/,
    `$1\n<style>\n${combinedCss}</style>`
);
console.log(`  ✓ CSS inlined into HTML`);

// --- 5. Установить константу __IS_DESKTOP_BUILD__ в JS ---
// Заменяем все вхождения __IS_DESKTOP_BUILD__ на true/false
// (для future use когда JS будет модульным)
html = html.replace(/__IS_DESKTOP_BUILD__/g, String(isDesktop));

// --- 6. Минификация HTML (опционально) ---
// Пока оставляем как есть — для отладки

// --- 7. Записать index.html ---
writeFileSync(resolve(outDir, 'index.html'), html, 'utf-8');
const htmlSize = Buffer.byteLength(html, 'utf-8');
console.log(`  ✓ Written index.html: ${(htmlSize / 1024).toFixed(1)} KB`);

// --- 8. Скопировать статические файлы ---
function copyDirRecursive(src, dest) {
    if (!existsSync(src)) return;
    mkdirSync(dest, { recursive: true });
    for (const entry of readdirSync(src, { withFileTypes: true })) {
        const srcPath = join(src, entry.name);
        const destPath = join(dest, entry.name);
        if (entry.isDirectory()) {
            copyDirRecursive(srcPath, destPath);
        } else {
            copyFileSync(srcPath, destPath);
        }
    }
}

// images/
copyDirRecursive(resolve(srcDir, 'images'), resolve(outDir, 'images'));
console.log(`  ✓ Copied images/`);

// data/
copyDirRecursive(resolve(srcDir, 'data'), resolve(outDir, 'data'));
console.log(`  ✓ Copied data/`);

// manifest.json
const manifestSrc = resolve(srcDir, 'manifest.json');
if (existsSync(manifestSrc)) {
    copyFileSync(manifestSrc, resolve(outDir, 'manifest.json'));
    console.log(`  ✓ Copied manifest.json`);
}

// sw.js — из корня проекта
const swSrc = resolve(__dirname, 'sw.js');
if (existsSync(swSrc)) {
    copyFileSync(swSrc, resolve(outDir, 'sw.js'));
    console.log(`  ✓ Copied sw.js`);
}

// electron/ — только для desktop
if (isDesktop) {
    copyDirRecursive(resolve(__dirname, 'electron'), resolve(outDir, 'electron'));
    console.log(`  ✓ Copied electron/`);
}

// --- 9. Итого ---
console.log(`\n✅ ${mode.toUpperCase()} build complete → ${outDir}`);
console.log(`   index.html: ${(htmlSize / 1024).toFixed(1)} KB`);
console.log(`   CSS: base.css + ${mode}.css (inlined)`);
if (isDesktop) {
    console.log(`   ❌ Excluded: mobile.css (${readFileSync(resolve(srcDir, 'css/mobile.css'), 'utf-8').split('\n').length} lines)`);
} else {
    console.log(`   ❌ Excluded: desktop.css (${readFileSync(resolve(srcDir, 'css/desktop.css'), 'utf-8').split('\n').length} lines)`);
}
