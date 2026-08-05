const { app, BrowserWindow, Menu, shell, dialog, protocol } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow = null;

// Корневая директория приложения (где index.html, data/, images/)
const APP_ROOT = path.join(__dirname, '..');

// ⚠️ ВАЖНО: регистрируем схему как привилегированную ДО app.whenReady()
// Это позволяет fetch(), Service Worker, CSS и JS работать через app://
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app',
    privileges: {
      standard: true,       // работает как http/https
      secure: true,         // TLS-подобная схема
      bypassCSP: true,      // обходит CSP
      allowServiceWorkers: true,
      supportFetchAPI: true,
      corsEnabled: true,
      stream: true
    }
  }
]);

// Обработчик протокола app:// — обслуживает файлы из APP_ROOT
function registerProtocolHandler() {
  protocol.handle('app', (request) => {
    const url = new URL(request.url);
    let filePath = path.normalize(path.join(APP_ROOT, url.pathname));

    // Безопасность: path traversal protection
    if (!filePath.startsWith(APP_ROOT)) {
      return new Response('Forbidden', { status: 403 });
    }

    // MIME-типы
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
      '.html':  'text/html; charset=utf-8',
      '.js':    'application/javascript; charset=utf-8',
      '.css':   'text/css; charset=utf-8',
      '.json':  'application/json; charset=utf-8',
      '.png':   'image/png',
      '.jpg':   'image/jpeg',
      '.jpeg':  'image/jpeg',
      '.svg':   'image/svg+xml',
      '.ico':   'image/x-icon',
      '.woff':  'font/woff',
      '.woff2': 'font/woff2',
      '.ttf':   'font/ttf',
      '.webp':  'image/webp',
      '.webmanifest': 'application/manifest+json'
    };
    const mimeType = mimeTypes[ext] || 'application/octet-stream';

    try {
      const data = fs.readFileSync(filePath);
      return new Response(data, {
        status: 200,
        headers: {
          'content-type': mimeType,
          'cache-control': 'no-cache'
        }
      });
    } catch (err) {
      return new Response('Not Found: ' + url.pathname, { status: 404 });
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    icon: path.join(APP_ROOT, 'images', 'icon-512.png'),
    title: 'КИПиА — справочник инженера',
    backgroundColor: '#1a2233', // цвет фона при загрузке (как в PWA)
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,   // нужен для кастомного протокола
      devTools: false   // установите true для отладки
    },
    autoHideMenuBar: true,
    show: false
  });

  // Загружаем через кастомный протокол
  mainWindow.loadURL('app://localhost/index.html');

  // Показываем окно когда контент загружен
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Внешние ссылки → системный браузер
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Навигация только по нашему протоколу
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('app://localhost')) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Отключаем стандартное контекстное меню
  mainWindow.webContents.on('context-menu', (e) => {
    e.preventDefault();
  });
}

// Меню приложения
function createMenu() {
  const template = [
    {
      label: 'Файл',
      submenu: [
        {
          label: 'О приложении',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'КИПиА',
              message: 'КИПиА — справочник инженера',
              detail: `Версия: ${app.getVersion()}\n\nСправочник и калькулятор контрольно-измерительных приборов и автоматики.\n\nПриборы, блокировки, клапаны, регуляторы, кабельный журнал, проекты, калькуляторы, конвертер единиц, экзаменационные билеты.`,
              buttons: ['OK']
            });
          }
        },
        { type: 'separator' },
        { label: 'Выход', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }
      ]
    },
    {
      label: 'Вид',
      submenu: [
        { label: 'Обновить', accelerator: 'CmdOrCtrl+R', click: () => mainWindow.reload() },
        { label: 'Полный экран', accelerator: 'F11', click: () => mainWindow.setFullScreen(!mainWindow.isFullScreen()) }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Запуск приложения
app.whenReady().then(() => {
  registerProtocolHandler();
  createMenu();
  createWindow();

  // macOS: пересоздать окно при клике на док-иконку
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Закрыть приложение когда все окна закрыты
app.on('window-all-closed', () => {
  app.quit();
});

// Блокируем создание дополнительных окон
app.on('web-contents-created', (event, contents) => {
  contents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
});
