import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import screenshot from 'screenshot-desktop';
import { PythonAgent } from './pythonagent.js'; // ← NEW
import * as dotenv from 'dotenv';
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let win;
let py;

function createWindow() {
  win = new BrowserWindow({
    width: 400,
    height: 500,
    x: 1150,
    y: 20,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: false,
    minimizable: true,
    title: "Axon",
    titleBarOverlay: { color: '#2f3241', symbolColor: '#74b1be', height: 10 },
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
    },
  });

  console.log("Loading dev server:", process.env.VITE_DEV_SERVER_URL);
  win.loadURL(process.env.VITE_DEV_SERVER_URL || "http://localhost:5173");

  ipcMain.handle('stt/transcribe', async (_evt, { bytes, mime }) => {
    if (!process.env.ELEVENLABS_API_KEY) {
        throw new Error('ELEVENLABS_API_KEY missing');
    }

    // Recreate a Blob from bytes coming from the renderer
    const uint8 = new Uint8Array(bytes);
    const blob = new Blob([uint8], { type: mime || 'audio/webm' });

    const form = new FormData();
    form.append('model_id', 'scribe_v1');        // ElevenLabs STT model
    form.append('diarize', 'false');             // turn on if you want speaker labels
    form.append('language_code', 'eng');        // or "eng" etc.
    form.append('tag_audio_events', 'false');    // laughter/applause tagging
    form.append('file', blob, 'input.webm');

    const res = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {
        method: 'POST',
        headers: { 'xi-api-key': process.env.ELEVENLABS_API_KEY },
        body: form
    });

    if (!res.ok) {
        const txt = await res.text().catch(() => '');
        throw new Error(`STT failed: ${res.status} ${res.statusText} ${txt}`);
    }
    const json = await res.json();
    // API returns a structured object; "text" holds the transcript
    // (fields depend on options like diarization/timestamps)
    return json.text ?? json.transcript ?? JSON.stringify(json);
  });

  // ========== Screenshot handler (unchanged) ==========

  // ========== Window controls (unchanged) ==========
  ipcMain.on('minimize-window', () => win.minimize());
  ipcMain.on('close-window', () => win.close());

  // ========== 🔌 Start Python bridge (NEW) ==========
  py = new PythonAgent({
    bridgePath: path.join(__dirname, '../py_files/agent_bridge.py'), // ← adjust to your path
    env: {
      GEMINI_API_KEY: process.env.GEMINI_API_KEY || "",
      PYTHONPATH: path.join(__dirname, '../py_files'),              // ← folder containing agent_core.py, etc.
    },
  });
  py.start();

  // Stream all Python events to renderer so you can show steps
  py.on('event', (msg) => { if (!win?.isDestroyed()) win.webContents.send('agent-event', msg); });
  py.on('stderr', (line) => console.error('[PY STDERR]', line));
  py.on('exit',   ({code, signal}) => console.log('[PY EXIT]', code, signal));

  // ========== 🧠 Run agent with a user goal (NEW) ==========
  ipcMain.handle('agent/run', async (_evt, { goal, target_app = null, max_iterations = 3 }) => {
    const result = await py.runGoal({ goal, target_app, max_iterations });
    return result; // renderer await window.ipcrenderer.invoke('agent/run', ...)
  });

  // ========== Optional debugger helpers (NEW) ==========
  ipcMain.handle('debug/selftest', async () => py.selftest());
  ipcMain.handle('debug/ping',     async () => ({ id: py.ping() }));
  ipcMain.handle('debug/echo',     async (_e, data) => ({ id: py.echo(data), data }));

  // ✅ REMOVE the old user-input handler to avoid confusion/duplicates
  // ipcMain.handle('user-input', ...)  ← delete this block
}

app.whenReady().then(createWindow);
app.on('before-quit', () => { try { py?.stop(); } catch {} });
