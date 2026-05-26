const { Client } = require("minecraft-launcher-core");
const fs = require("fs");
const path = require("path");

class MinecraftManager {
  constructor(rootPath) {
    this.launcher = new Client();
    this.root = path.resolve(rootPath);
    if (!fs.existsSync(this.root)) {
      fs.mkdirSync(this.root, { recursive: true });
    }
  }

  async getVersionList() {
    const response = await fetch(
      "https://launchermeta.mojang.com/mc/game/version_manifest.json",
    );
    const data = await response.json();
    return data.versions;
  }
  async launch(versionName, progressCallback) {
    const versions = await this.getVersionList();
    const version = versions.find((v) => v.id === versionName);
    if (!version) throw new Error("Версія не знайдена");

    this.launcher.on("progress", (e) => {
      const percent = Math.round((e.downloaded / e.total) * 100) || 0;
      progressCallback({ percent, task: `Завантаження: ${percent}%` });
    });

    this.launcher.on("debug", (e) => {
      progressCallback({ type: "debug", payload: e });
    });

    this.launcher.launch({
      root: this.root,
      version: { number: version.id, type: version.type },
      authorization: {
        access_token: "offline",
        client_token: "offline",
        uuid: "550e8400-e29b-41d4-a716-446655440000",
        name: "Player",
      },
    });
  }
}

module.exports = MinecraftManager;
