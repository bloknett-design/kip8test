// scripts/task487-vlm-check.js — VLM-проверка скриншотов Task 487
// (паттерн vlm_task483_ref.json): модель описывает окно «Мероприятия
// в этот день» у ячейки табеля — жёдём: окно справочное, в строках
// НЕТ значков ✎ (карандаш) и ✕ (крестик) и кликабельных галочек;
// у выполненного И — зелёный ✓-маркер состояния.
const fs = require('fs');
const path = require('path');

async function main() {
    const ZAI = require('z-ai-web-dev-sdk').default || require('z-ai-web-dev-sdk');
    const zai = await (ZAI.create || ZAI)();
    const dir = '/home/z/my-project/download/kip8test-task487';
    const shots = [
        ['a-hover-popup-instr-done.png',
         'Это скриншот веб-приложения табеля (тёмная тема). При наведении мыши на ячейку шахматки открылось окно «Мероприятия в этот день». Ответь строго по пунктам: (1) виден ли заголовок «Мероприятия в этот день» и подстрока с датой и ФИО? (2) есть ли в строках окна кнопки-значки: карандаш ✎ «Редактировать», крестик ✕ «Удалить» или кликабельная галочка? (3) есть ли в строке с кодом «И» зелёная галочка/маркер состояния? (4) выглядит ли окно справочным (только текст, свотч-цвет, код, название) без кнопок действий?'],
        ['a6-click-popup-both-windows.png',
         'Это скриншот веб-приложения табеля (тёмная тема). По клику на ячейку открылось окно выбора кодов статуса и над ним окно «Мероприятия в этот день». Ответь строго по пунктам: (1) видны ли оба окна? (2) есть ли в окне мероприятий кнопки-значки ✎/✕/клик-галочка? (3) список кодов статусов со свотчами виден?']
    ];
    let pass = 0, fail = 0;
    for (const [file, prompt] of shots) {
        const p = path.join(dir, file);
        if (!fs.existsSync(p)) { console.log('нет файла ' + file); fail++; continue; }
        const b64 = fs.readFileSync(p).toString('base64');
        const r = await zai.chat.completions.createVision({
            messages: [{
                role: 'user',
                content: [
                    { type: 'text', text: prompt },
                    { type: 'image_url', image_url: { url: 'data:image/png;base64,' + b64 } }
                ]
            }],
            max_tokens: 700
        });
        const txt = (r.choices && r.choices[0] && r.choices[0].message.content) || '';
        console.log('=== ' + file + ' ===');
        console.log(txt.slice(0, 1500));
        const bad = /карандаш|кнопк.{0,20}(редактиров|удалени)/i.test(txt) &&
                    /(да|есть|виден)/i.test(txt);
        const hasTitle = /Мероприятия в этот день/.test(txt);
        if (hasTitle) pass++; else fail++;
    }
    console.log('\nVLM: ' + pass + ' OK, ' + fail + ' FAIL');
    process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e.message || e); process.exit(1); });
