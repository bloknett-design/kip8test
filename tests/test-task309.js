// tests/test-task309.js
// Task 309 — карточка сотрудника у колонки ФИО + правка/удаление
// мероприятий + рамка ручных д/н. Заявка пользователя:
//   «при наведении указателя мыши или при нажатии на поле с
//    сотрудником (слева от шахматки), должно появляться окно с
//    данными сотрудника, которые раньше были в убранных вкладках
//    (сотрудники, отпуска, инструктажи). Так же сделай возможность
//    редактирования и удаления добавляемых мероприятий в ячейки.
//    Коды "д" и "н", добавляемые в шахматку пользователем вручную,
//    должны отображаться с обрамлением по краям, по примеру как
//    в их миниатюрах.»
//
// ЧТО ПРОВЕРЯЕТСЯ (статические инварианты клиента):
//   Карточка сотрудника:
//     — элементы #wsEmpPopup/#wsEmpPopupCloser в HTML;
//     — td.ws-emp-col получает data-tab + onclick onEmpCellClick;
//     — hover-делегирование (mouseover/mouseout на wsGridWrap,
//       (hover: hover), задержки 350/400 мс, вход в попап отменяет
//       закрытие — кнопки кликабельны);
//     — клик — прикреплённый режим (кловер active);
//     — _renderEmpPopup: три секции (профиль «Сотрудники», отпуска
//       года с фильтром _vacDaysInYear и итогом, мероприятия месяца
//       с кнопками ✎/✕ только редакторам);
//     — Esc и взаимная блокировка с попапом ячейки.
//   Правка/удаление мероприятий:
//     — кнопки ✎/✕ в попапе ячейки («Мероприятия в этот день»)
//       и в карточке; stopPropagation;
//     — editTraining: поиск записи по id в _TRAININGS, закрытие
//       попапов, openTrainingForm в режиме правки (заголовок
//       «Правка мероприятия», кнопка «Сохранить»);
//     — submitTrainingForm в правке: addTraining(новые значения)
//       → deleteTraining(старый id) (серверного updateTraining нет,
//       Apps Script не трогаем), тост «Мероприятие обновлено»;
//     — deleteTraining закрывает оба попапа до подтверждения.
//   Рамка ручных д/н:
//     — _renderCell: класс ws-manual-dn при источник «руч» и статусе
//       д/н (виден и до сохранения — pending даёт «руч»);
//     — CSS: box-shadow inset 2px, тёмная и светлая темы.
//   Регресс-фиксы Task 308 (заявка «добавляю мероприятие — тост
//   "Ошибка: self.loadTrainings is not a function"»):
//     — вызовы удалённых страниц loadTrainings()/loadVacations()
//       больше не встречаются; вместо них loadGrid().
//   SW: kipia-test-v548.
//
// Запуск: через tests/run-all.js (require './test-task309.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse } = require('./test-helpers.js');

const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');

// Вырезка тела функции: от сигнатуры до следующего «имя: function»
// на том же уровне отступов (8 пробелов — методы WorkSchedule)
function fnBody(src, signature) {
    const i = src.indexOf(signature);
    if (i === -1) return '';
    const rest = src.slice(i + signature.length);
    const m = rest.match(/^[\s\S]*?\n        [a-zA-Z_]+: function/);
    return m ? m[0] : rest;
}

describe('Task 309 — карточка сотрудника у колонки ФИО', () => {

    test('HTML: элементы попапа #wsEmpPopup и кловера #wsEmpPopupCloser', () => {
        assertTrue(INDEX_SRC.indexOf('id="wsEmpPopupCloser"') !== -1,
            'кловер для прикреплённого режима');
        assertTrue(INDEX_SRC.indexOf('id="wsEmpPopup"') !== -1,
            'контейнер карточки');
        assertTrue(INDEX_SRC.indexOf('onclick="WorkSchedule.closeEmpPopup()"') !== -1,
            'клик по кловеру закрывает карточку');
        // класс-основа ws-cell-popup (позиционирование/фон/рамка)
        // + модификатор ws-emp-popup
        assertTrue(INDEX_SRC.indexOf('class="ws-cell-popup ws-emp-popup"') !== -1,
            'попап наследует стили статусного попапа');
    });

    test('Рендер: td.ws-emp-col получает data-tab и onclick onEmpCellClick', () => {
        const gridPart = INDEX_SRC.slice(
            INDEX_SRC.indexOf('_renderGrid: function'),
            INDEX_SRC.indexOf('_fitGrid: function'));
        assertTrue(gridPart.indexOf("td.getAttribute('data-tab')") === -1,
            'рендер не читает атрибуты (читает только hover-делегат)');
        assertTrue(gridPart.indexOf('data-tab=') !== -1,
            'колонка ФИО несёт data-tab для hover-делегата');
        assertTrue(gridPart.indexOf('WorkSchedule.onEmpCellClick(event,') !== -1,
            'клик по колонке ФИО открывает карточку');
        assertTrue(gridPart.indexOf('Карточка сотрудника: профиль, отпуска, мероприятия') !== -1,
            'title-подсказка на колонке');
    });

    test('JS: hover-делегирование в init — mouseover/mouseout, (hover: hover), таймеры', () => {
        const initPart = INDEX_SRC.slice(
            INDEX_SRC.indexOf('init: function'),
            INDEX_SRC.indexOf('_refreshFromUrlState: function'));
        assertTrue(initPart.indexOf('_attachEmpPopupHover();') !== -1,
            'init навешивает hover-делегирование');
        const hoverPart = fnBody(INDEX_SRC, '_attachEmpPopupHover: function');
        assertTrue(hoverPart.indexOf("addEventListener('mouseover'") !== -1,
            'делегат mouseover на контейнере сетки');
        assertTrue(hoverPart.indexOf("addEventListener('mouseout'") !== -1,
            'делегат mouseout на контейнере сетки');
        assertTrue(hoverPart.indexOf("(hover: hover)") !== -1,
            'тач-устройства без hover игнорируются (карточка — по клику)');
        assertTrue(hoverPart.indexOf('}, 350);') !== -1,
            'открытие по наведению — с задержкой 350 мс');
        assertTrue(hoverPart.indexOf("td.getAttribute('data-tab')") !== -1,
            'таб-номер берётся из data-tab ячейки');
        // вход в попап отменяет закрытие (кнопки кликабельны)
        assertTrue(hoverPart.indexOf("popup.addEventListener('mouseenter'") !== -1,
            'mouseenter попапа отменяет закрытие');
        assertTrue(hoverPart.indexOf("popup.addEventListener('mouseleave'") !== -1,
            'mouseleave попапа планирует закрытие');
        // защита от повторного навешивания
        assertTrue(hoverPart.indexOf('_empHoverAttached') !== -1,
            'слушатели навешиваются один раз');
    });

    test('JS: клик — прикреплённый режим (кловер active, Esc закрывает)', () => {
        const clickPart = fnBody(INDEX_SRC, 'onEmpCellClick: function');
        assertTrue(clickPart.indexOf('_openEmpPopup(td, tabNo, true)') !== -1,
            'клик открывает карточку в прикреплённом режиме');
        assertTrue(clickPart.indexOf('this.closeCellPopup();') !== -1,
            'взаимная блокировка: статусный попап закрывается');
        const openPart = fnBody(INDEX_SRC, '_openEmpPopup: function');
        assertTrue(openPart.indexOf("closer.classList.toggle('active', !!pinned)") !== -1,
            'кловер активен только в прикреплённом режиме');
        // Esc: обработчик init закрывает ОБА попапа
        const escIdx = INDEX_SRC.indexOf("if (ev.key === 'Escape')");
        assertTrue(escIdx !== -1 &&
            INDEX_SRC.indexOf('selfOnce.closeEmpPopup();', escIdx) !== -1,
            'Esc закрывает и карточку сотрудника');
        // обратная блокировка: открытие статусного попапа закрывает карточку
        const cellClickPart = fnBody(INDEX_SRC, 'onCellClick: function');
        assertTrue(cellClickPart.indexOf('this.closeEmpPopup();') !== -1,
            'onCellClick закрывает карточку сотрудника');
    });

    test('JS: _renderEmpPopup — три секции данных из убранных вкладок', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');
        assertTrue(rp.indexOf('<div class="ws-popup-sec">Сотрудник</div>') !== -1,
            'секция профиля (бывшая вкладка «Сотрудники»)');
        assertTrue(rp.indexOf('<div class="ws-popup-sec">Отпуска · ') !== -1,
            'секция отпусков (бывшая вкладка «Отпуска»)');
        assertTrue(rp.indexOf('<div class="ws-popup-sec">Мероприятия · ') !== -1,
            'секция мероприятий (бывшая вкладка «Инструктажи»)');
        // профиль: поля карточки
        ['Тип', 'Должность', 'Шаблон ротации', 'Старт цикла', 'Дата приёма', 'Комментарий']
            .forEach(f => assertTrue(rp.indexOf("['" + f + "',") !== -1,
                'поле профиля «' + f + '»'));
        // шаблон ротации — имя из _PATTERNS
        assertTrue(rp.indexOf('this._PATTERNS[pi].name') !== -1,
            'имя шаблона берётся из загруженных шаблонов');
    });

    test('JS: отпуска в карточке — фильтр по году (_vacDaysInYear) и итог дней', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');
        assertTrue(rp.indexOf('this._vacDaysInYear(v, this._year)') !== -1,
            'периоды фильтруются по году шахматки');
        assertTrue(rp.indexOf('Итого в году: ') !== -1,
            'итог дней года');
        assertTrue(rp.indexOf("this._plural(vacTotal, ['день', 'дня', 'дней'])") !== -1,
            'русское окончание для итога');
        assertTrue(rp.indexOf('нет запланированных периодов') !== -1,
            'пустое состояние секции отпусков');
    });

    test('JS: мероприятия в карточке — сортировка по дате, кнопки только редакторам', () => {
        const rp = fnBody(INDEX_SRC, '_renderEmpPopup: function');
        assertTrue(rp.indexOf('WorkSchedule.editTraining(') !== -1,
            'кнопка правки ✎ в карточке');
        assertTrue(rp.indexOf('WorkSchedule.deleteTraining(') !== -1,
            'кнопка удаления ✕ в карточке');
        assertTrue(rp.indexOf('if (this._canEdit && trId)') !== -1,
            'кнопки — только ролям с правом записи');
        assertTrue(rp.indexOf('нет мероприятий в месяце') !== -1,
            'пустое состояние секции мероприятий');
        assertTrue(rp.indexOf('a.дата_начала).localeCompare') !== -1,
            'мероприятия отсортированы по дате начала');
    });

    test('JS: closeEmpPopup сбрасывает состояние и очищает DOM', () => {
        const cp = fnBody(INDEX_SRC, 'closeEmpPopup: function');
        assertTrue(cp.indexOf("popup.classList.remove('active')") !== -1,
            'попап деактивируется');
        assertTrue(cp.indexOf("closer.classList.remove('active')") !== -1,
            'кловер деактивируется');
        assertTrue(cp.indexOf('this._empPinned = false;') !== -1,
            'флаг прикрепления сброшен');
        assertTrue(cp.indexOf('_cancelEmpPopupOpen') !== -1 &&
            cp.indexOf('_cancelEmpPopupClose') !== -1,
            'отложенные таймеры отменяются');
    });
});

describe('Task 309 — правка и удаление мероприятий', () => {

    test('JS: кнопки ✎/✕ в попапе ячейки (секция «Мероприятия в этот день»)', () => {
        const popupPart = INDEX_SRC.slice(
            INDEX_SRC.indexOf('_renderCellPopup: function'),
            INDEX_SRC.indexOf('_openCellPopup: function'));
        assertTrue(popupPart.indexOf('if (this._canEdit && deId)') !== -1,
            'кнопки — только редакторам');
        assertTrue(popupPart.indexOf('event.stopPropagation(); WorkSchedule.editTraining(') !== -1,
            '✎ с stopPropagation');
        assertTrue(popupPart.indexOf('event.stopPropagation(); WorkSchedule.deleteTraining(') !== -1,
            '✕ с stopPropagation');
    });

    test('JS: editTraining находит запись по id и открывает форму в режиме правки', () => {
        const et = fnBody(INDEX_SRC, 'editTraining: function');
        assertTrue(et.indexOf('parseInt(this._TRAININGS[i].id, 10) === tid') !== -1,
            'поиск записи в _TRAININGS по id');
        assertTrue(et.indexOf('this.closeCellPopup();') !== -1 &&
            et.indexOf('this.closeEmpPopup();') !== -1,
            'попапы закрываются до открытия формы');
        assertTrue(et.indexOf('this.openTrainingForm(null, null, rec);') !== -1,
            'форма открывается с записью для правки');
        assertTrue(et.indexOf('Мероприятие не найдено — обновите график') !== -1,
            'тост при ненайденной записи');
    });

    test('JS: форма мероприятия — режимы «Новое мероприятие»/«Правка мероприятия»', () => {
        // ids для переключения заголовка/кнопки
        assertTrue(INDEX_SRC.indexOf('id="wsTrSheetTitle"') !== -1,
            'заголовок шторки имеет id');
        assertTrue(INDEX_SRC.indexOf('id="wsTrSubmitBtn"') !== -1,
            'кнопка отправки имеет id');
        const otf = fnBody(INDEX_SRC, 'openTrainingForm: function');
        assertTrue(otf.indexOf("sheetTitle.textContent = 'Правка мероприятия'") !== -1,
            'заголовок в режиме правки');
        assertTrue(otf.indexOf("submitBtn.textContent = 'Сохранить'") !== -1,
            'кнопка в режиме правки');
        assertTrue(otf.indexOf("sheetTitle.textContent = 'Новое мероприятие'") !== -1,
            'заголовок в режиме создания');
        assertTrue(otf.indexOf('this._editTrainingId = parseInt(editTraining.id, 10);') !== -1,
            'id правимой записи сохраняется в _editTrainingId');
        // префилл значений записи
        assertTrue(otf.indexOf("String(editTraining.дата_начала || '')") !== -1,
            'даты записи вписываются в форму');
    });

    test('JS: submitTrainingForm в правке — add новых значений, затем delete старой записи', () => {
        const stf = fnBody(INDEX_SRC, 'submitTrainingForm: function');
        const editIdx = stf.indexOf('if (this._editTrainingId)');
        assertTrue(editIdx !== -1, 'ветка режима правки есть');
        const editBranch = stf.slice(editIdx);
        // порядок: add → delete (сбой add не трогает старую запись)
        const addIdx = editBranch.indexOf("this._api('workSchedule.addTraining', payload)");
        const delIdx = editBranch.indexOf("deleteTraining', { id: oldId })");
        assertTrue(addIdx !== -1 && delIdx !== -1 && addIdx < delIdx,
            'addTraining выполняется ДО deleteTraining старой записи');
        assertTrue(editBranch.indexOf("'Мероприятие обновлено'") !== -1,
            'тост об обновлении');
        // сбой частичного шага — сетка перезагружается и ошибка видна
        assertTrue(editBranch.indexOf('self.loadGrid();') !== -1,
            'сетка перезагружается после правки (и при сбое)');
        // сервер не менялся: updateTraining НЕ добавлялся
        assertFalse(INDEX_SRC.indexOf('workSchedule.updateTraining') !== -1,
            'клиент не зовёт несуществующий updateTraining (Apps Script не трогаем)');
    });

    test('JS: deleteTraining закрывает попапы до диалога подтверждения', () => {
        const dt = fnBody(INDEX_SRC, 'deleteTraining: function');
        assertTrue(dt.indexOf('this.closeCellPopup();') !== -1 &&
            dt.indexOf('this.closeEmpPopup();') !== -1,
            'оба попапа закрываются (кнопки ✕ есть в обоих)');
        assertTrue(dt.indexOf('kipConfirm') !== -1,
            'подтверждение удаления сохранено');
    });
});

describe('Task 309 — рамка ручных д/н', () => {

    test('JS: _renderCell ставит ws-manual-dn только ручным д/н', () => {
        const rc = INDEX_SRC.slice(
            INDEX_SRC.indexOf('_renderCell: function'),
            INDEX_SRC.indexOf('generateYear: function'));
        const idx = rc.indexOf("if (isManual && (status === 'д' || status === 'н'))");
        assertTrue(idx !== -1, 'условие: источник «руч» + статус д/н');
        // класс ставится после ws-source-manual (общий маркер жив)
        assertTrue(rc.indexOf("if (isManual) classes.push('ws-source-manual');") !== -1,
            'общий маркер ручных записей не тронут');
        // планированные Д/Н и ручные другие коды — БЕЗ яркой рамки:
        // условие объединяет оба требования через &&
        const cond = rc.slice(idx, rc.indexOf('}', idx));
        assertTrue(cond.indexOf('isManual') !== -1 && cond.indexOf("status === 'д'") !== -1,
            'рамка не вешается на авто-коды');
    });

    test('CSS: ws-manual-dn — inset 2px рамка, тёмная и светлая темы', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-grid tbody td.ws-cell.ws-manual-dn {') !== -1,
            'базовое правило');
        assertTrue(INDEX_SRC.indexOf('box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.85);') !== -1,
            'тёмная тема: светлая рамка 2px по краям (как у миниатюры)');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ws-grid tbody td.ws-cell.ws-manual-dn {') !== -1,
            'светлая тема: правило есть');
        assertTrue(INDEX_SRC.indexOf('box-shadow: inset 0 0 0 2px rgba(38, 50, 56, 0.75);') !== -1,
            'светлая тема: тёмная рамка 2px');
    });

    test('CSS: колонка ФИО интерактивна (cursor + сплошная подсветка hover)', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-grid tbody td.ws-emp-col {') !== -1 &&
            INDEX_SRC.indexOf('.ws-grid tbody td.ws-emp-col:hover {') !== -1,
            'hover-подсветка колонки');
        // сплошной фон (sticky-колонка: полупрозрачный просвечивал бы)
        const hoverRule = INDEX_SRC.slice(
            INDEX_SRC.indexOf('.ws-grid tbody td.ws-emp-col:hover {'),
            INDEX_SRC.indexOf('}', INDEX_SRC.indexOf('.ws-grid tbody td.ws-emp-col:hover {')));
        assertTrue(hoverRule.indexOf('#15202f') !== -1,
            'тёмная тема: сплошной цвет подсветки');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ws-grid tbody td.ws-emp-col:hover') !== -1,
            'светлая тема подсветки');
    });
});

describe('Task 309 — регресс-фиксы Task 308 (loadTrainings/loadVacations)', () => {

    test('JS: вызовы удалённых страниц loadTrainings()/loadVacations() исчезли', () => {
        // Task 308 удалил страницы «Инструктажи»/«Отпуска» вместе с их
        // загрузчиками, но вызовы self.loadTrainings() остались — после
        // добавления/удаления мероприятия тостил ложную «Ошибка» и сетка
        // не перезагружалась. Task 309 заменил вызовы на loadGrid().
        assertFalse(/self\.loadTrainings\(\)/.test(INDEX_SRC),
            'self.loadTrainings() больше не зовётся (метода нет)');
        assertFalse(/self\.loadVacations\(\)/.test(INDEX_SRC),
            'self.loadVacations() больше не зовётся (метода нет)');
        assertFalse(/this\.loadTrainings\(\)/.test(INDEX_SRC),
            'this.loadTrainings() тоже не встречается');
        assertFalse(/this\.loadVacations\(\)/.test(INDEX_SRC),
            'this.loadVacations() тоже не встречается');
    });

    test('JS: добавление/удаление мероприятия и удаление отпуска перезагружают сетку', () => {
        const stf = fnBody(INDEX_SRC, 'submitTrainingForm: function');
        assertTrue(stf.indexOf('self.loadGrid();') !== -1,
            'submitTrainingForm (создание) → loadGrid');
        const ddt = fnBody(INDEX_SRC, '_doDeleteTraining: function');
        assertTrue(ddt.indexOf('self.loadGrid();') !== -1,
            '_doDeleteTraining → loadGrid');
        const ddv = fnBody(INDEX_SRC, '_doDeleteVacation: function');
        assertTrue(ddv.indexOf('self.loadGrid();') !== -1,
            '_doDeleteVacation → loadGrid (план «ОТ» обновляется)');
    });
});

describe('Task 309 — Service Worker', () => {

    test('SW: версия кэша kipia-test-v548', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v548'") !== -1,
            'CACHE_VERSION в sw.js = kipia-test-v548');
        assertFalse(SW_SRC.indexOf('kipia-test-v547') !== -1,
            'старой версии v547 нет');
    });
});
