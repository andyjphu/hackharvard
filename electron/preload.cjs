const { contextBridge, ipcRenderer } = require ('electron');
console.log("START");
// Expose a secure API to the renderer process
contextBridge.exposeInMainWorld('ipcrenderer', {
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
  send: (channel, ...args) => {
    const validChannels = ['minimize-window', 'close-window', 'user-input']; // Whitelist channels
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, ...args);
    }
  },
  on: (channel, listener) => ipcRenderer.on(channel, listener),
  off: (channel, listener) => ipcRenderer.removeListener(channel, listener),
});