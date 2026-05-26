const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("node:path");
const fs = require("fs");
const MinecraftManager = require("./MinecraftManager");

const mcManager = new MinecraftManager(
  path.join(app.getPath("userData"), "minecraft"),
);

function createWindow() {
  const win = new BrowserWindow({
    width: 900,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile(path.join(__dirname, "frontend", "index.html"));
  return win;
}

let mainWindow;
app.whenReady().then(() => {
  mainWindow = createWindow();
});

ipcMain.handle("launch-game", async (event, data) => {
  try {
    mcManager.launch(data.version, (data) => {
      if (data.type === "debug") {
        mainWindow.webContents.send("game-log", {
          type: "debug",
          payload: data.payload,
        });
      } else {
        mainWindow.webContents.send("progress-update", data);
      }
    });
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});
ipcMain.handle("get-versions", async () => {
  try {
    const versions = await mcManager.getVersionList();
    return versions.filter((v) => v.type === "release").map((v) => v.id);
  } catch (e) {
    return ["1.21.1", "1.20.1"];
  }
});

ipcMain.handle("check-installed", async (event, version) => {
  const versionsPath = path.join(mcManager.root, "versions", version);
  return fs.existsSync(versionsPath);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
