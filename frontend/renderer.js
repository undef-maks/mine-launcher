const btn = document.getElementById("play-btn");
const status = document.getElementById("status");
const versionSelect = document.getElementById("version-select");
const forgeSelect = document.getElementById("forge-select");
const forgeLabel = document.getElementById("forge-label");
const progressBar = document.getElementById("progress-bar");
const usernameInput = document.getElementById("username");
const logContainer = document.getElementById("log-container");

async function init() {
  usernameInput.value = await eel.load_username()();
  const versions = await eel.get_versions()();
  versionSelect.innerHTML =
    '<option value="" disabled selected>Оберіть версію</option>';

  for (const ver of versions) {
    const isInstalled = await eel.check_installed(ver)();
    const opt = document.createElement("option");
    opt.value = ver;
    opt.textContent = isInstalled ? `✓ ${ver}` : ver;
    versionSelect.appendChild(opt);
  }
}
init();

usernameInput.addEventListener("input", () =>
  eel.save_username(usernameInput.value),
);
document.getElementById("open-folder-btn").addEventListener("click", () => {
  eel.open_minecraft_folder();
});
async function updateForgeList() {
  const isForge =
    document.querySelector('input[name="loader"]:checked').value === "forge";
  if (isForge && versionSelect.value) {
    status.innerText = "Завантаження списку Forge...";
    const fVers = await eel.get_forge_versions(versionSelect.value)();

    forgeSelect.innerHTML =
      '<option value="" disabled selected>Оберіть Forge</option>';
    if (fVers.length === 0) {
      status.innerText = "Для цієї версії Forge не знайдено.";
      forgeSelect.style.display = "none";
      forgeLabel.style.display = "none";
    } else {
      status.innerText = "Оберіть версію Forge";
      for (const v of fVers) {
        const isInstalled = await eel.check_forge_installed(
          versionSelect.value,
          v,
        )();
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = isInstalled ? `✓ ${v}` : v;
        forgeSelect.appendChild(opt);
      }
      forgeSelect.style.display = "block";
      forgeLabel.style.display = "block";
    }
  } else {
    forgeSelect.style.display = "none";
    forgeLabel.style.display = "none";
  }
}

versionSelect.addEventListener("change", updateForgeList);

document.getElementsByName("loader").forEach((radio) => {
  radio.addEventListener("change", updateForgeList);
});

btn.addEventListener("click", async () => {
  if (!versionSelect.value) return (status.innerText = "Оберіть версію!");
  const loader = document.querySelector('input[name="loader"]:checked').value;
  if (loader === "forge" && !forgeSelect.value)
    return (status.innerText = "Оберіть версію Forge!");

  const data = {
    version: versionSelect.value,
    username: usernameInput.value,
    loader: loader,
    forge_version: forgeSelect.value,
  };

  btn.disabled = true;
  const result = await eel.launch_game(data)();

  if (!result.success) {
    status.innerText = "Помилка: " + result.error;
    btn.disabled = false;
  } else {
    status.innerText = "Гра запущена!";
    btn.innerText = "Гра запущена";
  }
});

eel.expose(progress_update);
function progress_update(data) {
  status.innerText = data.task;
  const currentWidth = parseInt(progressBar.style.width) || 0;
  const randomWidth = Math.min(currentWidth + Math.random() * 10, 90);
  progressBar.style.width = randomWidth + "%";
}

eel.expose(game_closed);
function game_closed() {
  status.innerText = "Гра закрита";
  btn.innerText = "ГРАТИ";
  btn.disabled = false;
  progressBar.style.width = "0%";
}

eel.expose(log_update);
function log_update(data) {
  const logItem = document.createElement("div");
  logItem.className = "log-item";
  logItem.textContent = `> ${data.payload}`;
  logItem.onclick = () => logItem.classList.toggle("expanded");
  logContainer.prepend(logItem);
}
