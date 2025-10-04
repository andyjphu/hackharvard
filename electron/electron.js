// main.mjs (or main.js)
import { app, BrowserWindow, ipcMain } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { PythonAgent } from "./pythonagent.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let win;
let py;

function createWindow() {
  win = new BrowserWindow({
    width: 400,
    height: 500,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
    },
  });

  win.loadURL(process.env.VITE_DEV_SERVER_URL || "http://localhost:5173");

  // ---- Start Python bridge
  py = new PythonAgent({
    bridgePath: path.join(__dirname, "../py_files/agent_bridge.py"), // adjust to your path
    env: {
      GEMINI_API_KEY: process.env.GEMINI_API_KEY || "", // forward your key
      PYTHONPATH: path.join(__dirname, "../py_files"),   // so imports find agent_core, etc.
    },
  });
  py.start();

  // Forward streaming events to the renderer (for step-by-step UI)
  py.on("event", (msg) => {
    if (win && !win.isDestroyed()) win.webContents.send("agent-event", msg);
  });
  py.on("stderr", (line) => console.error("[PY STDERR]", line));
}

// IPC: run the agent with a goal
ipcMain.handle("agent/run", async (_evt, { goal, target_app, max_iterations }) => {
  if (!py) throw new Error("Python bridge not running");
  const result = await py.runGoal({ goal, target_app, max_iterations });
  return result; // goes back to renderer invoke()
});

// Optional: clean shutdown
app.on("before-quit", () => {
  try { py?.stop(); } catch {}
});

app.whenReady().then(createWindow);
