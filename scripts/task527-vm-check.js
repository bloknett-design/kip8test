#!/usr/bin/env node
// scripts/task527-vm-check.js — быстрая VM-проверка движка после правок Task 527.
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('/home/z/my-project/kip8test/index.html', 'utf8');
const i0 = src.indexOf('// [Task 526 geo-fig engine: BEGIN]');
const i1 = src.indexOf('// [Task 526 geo-fig engine: END]');
const engine = src.slice(i0, i1);

// Настоящий formatNumber из репо (как в test-task526.js)
function fnBlock(name) {
    const i = src.indexOf('function ' + name + '(');
    let depth = 0;
    for (let k = i; k < src.length; k++) {
        if (src[k] === '{') depth++;
        else if (src[k] === '}') {
            depth--;
            if (depth === 0) return src.slice(i, k + 1);
        }
    }
    return null;
}
const fmt = fnBlock('formatNumber');
const sandbox = { Math: Math };
vm.createContext(sandbox);
vm.runInContext(fmt + '\n' + engine, sandbox);

let pass = 0, fail = 0;
function chk(name, cond, extra) {
    if (cond) { pass++; console.log('  + ' + name); }
    else { fail++; console.log('  X ' + name + (extra ? '  [' + extra + ']' : '')); }
}

// gc
const b = sandbox.geoFigBuild('gc', { D: 100 });
chk('gc: gf-resg в svg', b.svg.includes('gf-resg'));
chk('gc: gf-sep разделитель y=194', b.svg.includes('<line class="gf-sep" stroke-width="1" x1="10" y1="194" x2="230" y2="194"'));
chk('gc: формула в картинке', b.svg.includes('>S = π·D²/4<'));
chk('gc: значение в картинке', b.svg.includes('>78,5398 см²<'));
chk('gc: вторая строка y=229', b.svg.includes('x="228" y="229"'));
chk('gc: D под фигурой y=168', b.svg.includes('y="168.0">D = 100 мм<'));
chk('gc: R подпись на месте', b.svg.includes('>R = 50 мм<'));

// gs
const g = sandbox.geoFigBuild('gs', { D: 2 });
chk('gs: D под фигурой y=170', g.svg.includes('y="170.0">D = 2 м<'));
chk('gs: данные в картинке', g.svg.includes('>4,1888 м³<') && g.svg.includes('>12,5664 м²<'));

// gr
const r = sandbox.geoFigBuild('gr', { D: 100, d: 80 });
chk('gr: D под фигурой y=172', r.svg.includes('y="172.0">D = 100 мм<'));
chk('gr: d НАД фигурой y=17', r.svg.includes('y="17.0">d = 80 мм<'));
chk('gr: пропорция r=46.4 жива', r.svg.includes('r="46.4"'));
const r2 = sandbox.geoFigBuild('gr', { D: 100, d: 20 });
chk('gr d=20: d подпись всё ещё над фигурой', r2.svg.includes('y="17.0">d = 20 мм<'));

// gco
const c = sandbox.geoFigBuild('gco', { D: 2, H: 3 });
chk('gco: L слева anchor=end x=96', c.svg.includes('text-anchor="end" x="96.0"'));
chk('gco: L значение', c.svg.includes('>L = 3,1623 м<'));
chk('gco: D labelPos below (после линии y=170)', c.svg.includes('y="184.1">D = 2 м<'));

// gh
const h = sandbox.geoFigBuild('gh', { L: 5, D: 2, h: 1.5 });
const m = h.svg.match(/rotate\(-90 [\d.]+ ([\d.]+)\)">h = 1,5 м/);
chk('gh: h-подпись найдена', !!m, 'regex');
if (m) {
    const ly = parseFloat(m[1]);
    chk('gh: h-подпись ВНЕ выносных (не 81..126), y=' + m[1], ly < 81 || ly > 126);
}
chk('gh: 3 строки данных y=212/229/246', h.svg.includes('y="212"') && h.svg.includes('y="229"') && h.svg.includes('y="246"'));
chk('gh: заполнение в картинке', h.svg.includes('>80,4499 %<'));
const h3 = sandbox.geoFigBuild('gh', { L: 5, D: 2, h: 0.2 });
const m3 = h3.svg.match(/rotate\(-90 [\d.]+ ([\d.]+)\)">h = 0,2 м/);
chk('gh h=0.2: подпись вне 120..126', !m3 || parseFloat(m3[1]) < 120 || parseFloat(m3[1]) > 126, m3 && m3[1]);
const h0 = sandbox.geoFigBuild('gh', { L: 5, D: 2, h: 0 });
chk('gh h=0: без h-размера и жидкости', !h0.svg.includes('>h = ') && !h0.svg.includes('gf-liquid'));

// gcy
const cy = sandbox.geoFigBuild('gcy', { D: 2, H: 3 });
chk('gcy: без изменений — height 116', cy.svg.includes('height="116.0"'));
chk('gcy: данные в картинке', cy.svg.includes('>9,4248 м³<'));

// юнит-тесты gfDimH/gfDimV
chk('gfDimH below: y=64', sandbox.gfDimH(10, 100, 50, 't', [], 'below').includes('y="64.0"'));
chk('gfDimH above (default): y=45', sandbox.gfDimH(10, 100, 50, 't', []).includes('y="45.0"'));
const dvShort = sandbox.gfDimV(100, 110, 200, 'abcdefghij', [], 'right');
chk('gfDimV короткий: y=151.5 (вниз за выносную)', dvShort.includes('y="151.5"'));
const dvLong = sandbox.gfDimV(0, 100, 50, 'D = 2 м', [], 'left');
chk('gfDimV длинный: y=50 (середина)', dvLong.includes('y="50.0"'));

console.log('\nVM: ' + pass + '/' + (pass + fail));
process.exit(fail ? 1 : 0);
