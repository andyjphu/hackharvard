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

const ELEVEN_API_KEY = process.env.ELEVENLABS_API_KEY || process.env.ELEVEN_API_KEY || '';
// Rachel’s public voice id from the docs. Replace with your own if you like.
const DEFAULT_VOICE_ID = process.env.ELEVEN_VOICE_ID || 'EXAVITQu4vr4xnSDxMaL';
const DEFAULT_MODEL_ID = 'eleven_multilingual_v2'; // good default

async function ttsElevenLabs({ text, voiceId = DEFAULT_VOICE_ID, modelId = DEFAULT_MODEL_ID }) {
  if (!ELEVEN_API_KEY) throw new Error('Missing ELEVENLABS_API_KEY');

  // Keep messages short-ish (service limit ~5k chars)
  const safeText = String(text || '').slice(0, 4500);

  const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?optimize_streaming_latency=0&output_format=mp3_44100_64`;

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'xi-api-key': ELEVEN_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        text: safeText,
        model_id: modelId,
        voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75
        }
        })
    });

    if (!res.ok) {
        const errText = await res.text().catch(() => '');
        throw new Error(`ElevenLabs TTS failed (${res.status}): ${errText}`);
    }

    const ab = await res.arrayBuffer();
    const base64 = Buffer.from(ab).toString('base64');
    return { audioBase64: base64, mime: 'audio/mpeg' };
}

function createWindow() {
  win = new BrowserWindow({
    width: 500,
    height: 500,
    x: 1050,
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
  py.on('event', (msg) => {
    console.log('[PY EVENT]', msg);
    if (!win?.isDestroyed()) win.webContents.send('agent-event', msg);
  });
  py.on('stdout', (line) => {
    console.log('[PY STDOUT]', line);
    if (!win?.isDestroyed()) win.webContents.send('agent-stdout', line);
  });
  py.on('stderr', (line) => {
    console.error('[PY STDERR]', line);
    if (!win?.isDestroyed()) win.webContents.send('agent-stderr', line);
  });
  py.on('exit', ({ code, signal }) => {
    console.log('[PY EXIT]', { code, signal });
    if (!win?.isDestroyed()) win.webContents.send('agent-exit', { code, signal });
  });

  // ========== 🧠 Run agent with a user goal (NEW) ==========
  ipcMain.handle('agent/run', async (_evt, { goal, target_app = null, max_iterations = 3 }) => {
    try {
      console.log(`🚀 Starting agent with goal: "${goal}", target_app: "${target_app}"`);
      const result = await py.runGoal({ goal, target_app, max_iterations });
      console.log('✅ Agent completed:', result);
      return result; // renderer await window.ipcrenderer.invoke('agent/run', ...)
    } catch (error) {
      console.error('❌ Agent error:', error);
      throw error;
    }
  });

  // ========== Optional debugger helpers (NEW) ==========
  ipcMain.handle('debug/selftest', async () => py.selftest());
  ipcMain.handle('debug/ping', async () => ({ id: py.ping() }));
  ipcMain.handle('debug/echo', async (_e, data) => ({ id: py.echo(data), data }));

    ipcMain.handle('tts/speak', async (_evt, { text, voiceId, modelId } = {}) => {
        return ttsElevenLabs({ text, voiceId, modelId });
    });

  // ✅ REMOVE the old user-input handler to avoid confusion/duplicates
  // ipcMain.handle('user-input', ...)  ← delete this block
}

app.whenReady().then(createWindow);
app.on('before-quit', () => { try { py?.stop(); } catch { } });
