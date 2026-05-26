const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  launchGame: (data) => ipcRenderer.invoke("launch-game", data),
  getVersions: () => ipcRenderer.invoke("get-versions"),
  checkInstalled: (version) => ipcRenderer.invoke("check-installed", version),
  onProgress: (callback) =>
    ipcRenderer.on("progress-update", (event, data) => callback(data)),
  onLog: (callback) =>
    ipcRenderer.on("game-log", (event, data) => callback(data)),
});
