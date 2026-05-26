const btn = document.getElementById("play-btn");
const status = document.getElementById("status");
const versionSelect = document.getElementById("version-select");
const progressBar = document.getElementById("progress-bar");
const usernameInput = document.getElementById("username");
const customRepoDiv = document.getElementById("custom-repo");
const modal = document.getElementById("modal-overlay");
const repoInput = document.getElementById("modal-repo-url");
const logContainer = document.getElementById("log-container");

usernameInput.value = localStorage.getItem("username") || "";
usernameInput.addEventListener("input", () =>
  localStorage.setItem("username", usernameInput.value),
);

async function updateUI(version) {
  const isInstalled = await eel.check_installed(version)();
  btn.innerText = isInstalled ? "ГРАТИ" : "ВСТАНОВИТИ";
}

eel.expose(log_update);
function log_update(data) {
  const logContainer = document.getElementById("log-container");
  const logItem = document.createElement("div");
  logItem.className = "log-item";
  logItem.textContent = `> ${data.payload}`;
  logItem.onclick = () => logItem.classList.toggle("expanded");
  logContainer.prepend(logItem);
}
versionSelect.addEventListener("change", async () => {
  updateUI(versionSelect.value);
  customRepoDiv.style.display =
    versionSelect.value === "custom" ? "block" : "none";
  if (versionSelect.value === "custom") modal.classList.remove("modal-hidden");
});

async function loadVersions() {
  try {
    const versions = await eel.get_versions()();
    versionSelect.innerHTML =
      '<option value="" disabled selected>Оберіть версію</option><option value="custom">GitHub збірка...</option>';
    for (const ver of versions) {
      const isInstalled = await eel.check_installed(ver)();
      const option = document.createElement("option");
      option.value = ver;
      option.textContent = isInstalled ? `✓ ${ver}` : ver;
      versionSelect.appendChild(option);
    }
  } catch (e) {
    status.innerText = "Помилка завантаження версій";
  }
}

btn.addEventListener("click", async () => {
  if (!versionSelect.value) return (status.innerText = "Оберіть версію!");
  btn.disabled = true;
  const data = {
    version: versionSelect.value,
    username: usernameInput.value,
  };
  const result = await eel.launch_game(data)();
  if (!result.success) status.innerText = "Помилка: " + result.error;
  else status.innerText = "Гра запущена!";
});

// Функції для зв'язку з Python
eel.expose(progress_update);
function progress_update(data) {
  progressBar.style.width = data.percent + "%";
  status.innerText = data.task;
  if (data.percent >= 100) btn.disabled = false;
}

eel.expose(log_update);
function log_update(data) {
  const logItem = document.createElement("div");
  logItem.className = "log-item";
  logItem.textContent = `> ${data.payload}`;
  logItem.onclick = () => logItem.classList.toggle("expanded");
  logContainer.prepend(logItem);
}

document.getElementById("save-btn").addEventListener("click", () => {
  if (repoInput.value) {
    document.getElementById("repo-url").value = repoInput.value;
    modal.classList.add("modal-hidden");
  }
});

document.getElementById("cancel-btn").addEventListener("click", () => {
  modal.classList.add("modal-hidden");
  versionSelect.value = "";
});

loadVersions();
