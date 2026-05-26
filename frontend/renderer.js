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
  const isInstalled = await window.electronAPI.checkInstalled(version);
  btn.innerText = isInstalled ? "ГРАТИ" : "ВСТАНОВИТИ";
}

versionSelect.addEventListener("change", () => updateUI(versionSelect.value));

window.electronAPI.onProgress((data) => {
  progressBar.style.width = data.percent + "%";
  status.innerText = data.task;
  if (data.percent >= 100) {
    status.innerText = "Гра запущена!";
    btn.disabled = false;
    updateUI(versionSelect.value);
  }
});

versionSelect.addEventListener("change", async () => {
  const isInstalled = await window.electronAPI.checkInstalled(
    versionSelect.value,
  );
  btn.innerText = isInstalled ? "ГРАТИ" : "ВСТАНОВИТИ";
  customRepoDiv.style.display =
    versionSelect.value === "custom" ? "block" : "none";
  if (versionSelect.value === "custom") modal.classList.remove("modal-hidden");
});

async function loadVersions() {
  try {
    const versions = await window.electronAPI.getVersions();
    versionSelect.innerHTML =
      '<option value="" disabled selected>Оберіть версію</option><option value="custom">GitHub збірка...</option>';
    for (const ver of versions) {
      const isInstalled = await window.electronAPI.checkInstalled(ver);
      const option = document.createElement("option");
      option.value = ver;
      option.textContent = isInstalled ? `✓ ${ver}` : ver;
      versionSelect.appendChild(option);
    }
  } catch (e) {
    status.innerText = "Помилка";
  }
}

btn.addEventListener("click", async () => {
  if (!versionSelect.value) return (status.innerText = "Оберіть версію!");
  btn.disabled = true;
  const data = {
    version: versionSelect.value,
    username: usernameInput.value,
    loader: document.querySelector('input[name="loader"]:checked').value,
    repoUrl: document.getElementById("repo-url").value,
  };
  await window.electronAPI.launchGame(data);
});

window.electronAPI.onProgress((data) => {
  progressBar.style.width = data.percent + "%";
  status.innerText = data.task || "Завантаження...";
});

window.electronAPI.onLog((data) => {
  const logItem = document.createElement("div");
  logItem.className = "log-item";
  const payload = data.payload;
  let text =
    typeof payload === "object" ? JSON.stringify(payload, null, 2) : payload;
  logItem.textContent = `> ${text}`;
  logItem.addEventListener("click", () => logItem.classList.toggle("expanded"));
  logContainer.prepend(logItem);
});

window.electronAPI.onProgress((data) => {
  const bar = document.getElementById("progress-bar");
  const status = document.getElementById("status");

  bar.style.width = data.percent + "%";
  status.innerText = data.task;

  if (data.percent >= 100) {
    status.innerText = "Готово!";
    document.getElementById("play-btn").disabled = false;
  }
});

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
