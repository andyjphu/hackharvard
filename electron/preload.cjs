// preload.cjs
const { contextBridge, ipcRenderer } = require('electron');

const validSend = new Set([
  'minimize-window',
  'close-window',
  'stt/transcribe',
  'tts/speak'
  // (drop 'user-input' to avoid confusion with the new agent flow)
]);

const validInvoke = new Set([
  'agent/run',          // run Python agent with a goal
  'debug/selftest',     // optional: Windows debugger ops
  'debug/ping',
  'debug/echo',
  'tts/speak',
  'capture-screenshot', // you already use this
  'stt/transcribe'   // speech-to-text
]);

const validOn = new Set([
  'agent-event',        // stream step-by-step events from Python
  // if you still use these elsewhere, keep them; otherwise remove:
  // 'assistant-response',
  // 'assistant-error',
]);

contextBridge.exposeInMainWorld('ipcrenderer', {
  invoke: (channel, ...args) => {
    if (!validInvoke.has(channel)) {
      throw new Error(`Blocked invoke channel: ${channel}`);
    }
    return ipcRenderer.invoke(channel, ...args);
  },

  send: (channel, ...args) => {
    if (!validSend.has(channel)) {
      throw new Error(`Blocked send channel: ${channel}`);
    }
    ipcRenderer.send(channel, ...args);
  },

  on: (channel, listener) => {
    if (!validOn.has(channel)) {
      throw new Error(`Blocked on channel: ${channel}`);
    }
    ipcRenderer.on(channel, listener);
  },

  off: (channel, listener) => {
    ipcRenderer.removeListener(channel, listener);
  },

  // Optional: convenience "once" helper
  once: (channel, listener) => {
    if (!validOn.has(channel)) {
      throw new Error(`Blocked once channel: ${channel}`);
    }
    ipcRenderer.once(channel, listener);
  },
});
