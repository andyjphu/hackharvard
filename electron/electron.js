import { app, BrowserWindow, ipcMain } from 'electron' ;
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import screenshot from 'screenshot-desktop';
// ESM doesn't provide __dirname by default. Create equivalents using import.meta.url
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
console.log("Dirname:", __dirname);


function createWindow() {
  const win = new BrowserWindow({
    width: 400,
    height: 500,
    x: 1150, // adjust based on screen size
    y: 20,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: false,
    minimizable: true,
    title: "Axon",
    titleBarOverlay: {
        color: '#2f3241',
        symbolColor: '#74b1be',
        height: 10
    },
    webPreferences: {
        preload: path.join(__dirname, 'preload.cjs'),
        contextIsolation: true, // Enable context isolation
    },
  });

    //win.webContents.openDevTools()
    ipcMain.handle('capture-screenshot', async () => {
        try {
            const img = await screenshot({ format: 'png' });
            console.log("Captured screenshot bytes:", img.length); // DEBUG
            return `data:image/png;base64,${img.toString('base64')}`;
        } catch (err) {
            console.error("Screenshot failed:", err);
            return null;
        }
    });

    ipcMain.on('minimize-window', () => {
        win.minimize();
    });

    ipcMain.on('close-window', () => {
        win.close();
    });

    ipcMain.handle('user-input', async (_event, payload) => {
    const { text = '', files = [], hasAudio = false } = payload || {};
    const fileCount = Array.isArray(files) ? files.length : 0;

    const parts = [];
        if (text.trim()) parts.push(text.trim());
        if (fileCount) parts.push(`📎 Received ${fileCount} file${fileCount>1?'s':''}.`);
        if (hasAudio) parts.push('🎙️ Received audio clip.');

        // return { text: parts.join('\n') || "I didn't receive any content." };

        return {text: "yoyoyo this is a test"}
    });

//   if (process.env.VITE_DEV_SERVER_URL) {
//     // Development: load Vite dev server
    console.log("Loading dev server:", process.env.VITE_DEV_SERVER_URL);
    win.loadURL(process.env.VITE_DEV_SERVER_URL ? process.env.VITE_DEV_SERVER_URL : "http://localhost:5173");
//   } else {
//     // Production: load built files
//     const indexPath = path.join(__dirname, '../index.html');
//     console.log("Loading built app:", indexPath);
//     win.loadFile(indexPath);
//   }
}

app.whenReady().then(createWindow);