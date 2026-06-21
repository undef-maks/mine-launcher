const btn = document.getElementById("play-btn");
const status = document.getElementById("status");
const logContainer = document.getElementById("log-container");
const progressBar = document.getElementById("progress-bar");
const usernameInput = document.getElementById("username");

const profileSelect = document.getElementById("profile-select");
const activeProfileInfo = document.getElementById("active-profile-info");
const infoMcVersion = document.getElementById("info-mc-version");
const infoLoader = document.getElementById("info-loader");
const infoRepoContainer = document.getElementById("info-repo-container");
const infoRepoStatus = document.getElementById("info-repo-status");
const loaderVersionWrapper = document.getElementById("loader-version-wrapper");
const loaderVersionSelect = document.getElementById("loader-version-select");

const modalOverlay = document.getElementById("modal-overlay");
const openCreateModalBtn = document.getElementById("open-create-modal-btn");
const cancelBtn = document.getElementById("cancel-btn");
const saveBtn = document.getElementById("save-btn");
const modalProfileName = document.getElementById("modal-profile-name");
const modalVersionSelect = document.getElementById("modal-version-select");
const modalLoaderSelect = document.getElementById("modal-loader-select");
const modalRepoUrl = document.getElementById("modal-repo-url");
const manualFields = document.getElementById("manual-creation-fields");
const githubFields = document.getElementById("github-creation-fields");

const settingsModalOverlay = document.getElementById("settings-modal-overlay");
const openSettingsBtn = document.getElementById("open-settings-btn");
const settingsCloseBtn = document.getElementById("settings-close-btn");
const ramSelect = document.getElementById("ram-select");
const gpuSelect = document.getElementById("gpu-select");

let currentProfiles = {};

async function init() {
  usernameInput.value = await eel.load_username()();

  const config = await eel.get_config()();
  if (config) {
    if (config.ram) {
      ramSelect.value = config.ram;
    }
    if (config.selected_gpu) {
      gpuSelect.value = config.selected_gpu;
    }
  }

  const gpus = await eel.get_available_gpus()();
  gpuSelect.innerHTML =
    '<option value="auto">Автоматично (За замовчуванням)</option>';
  for (const gpu of gpus) {
    const opt = document.createElement("option");
    opt.value = gpu.id;
    opt.textContent = gpu.name;
    gpuSelect.appendChild(opt);
  }

  if (config && config.selected_gpu) {
    gpuSelect.value = config.selected_gpu;
  }

  const versions = await eel.get_versions()();
  modalVersionSelect.innerHTML =
    '<option value="" disabled selected>Оберіть версію</option>';
  for (const ver of versions) {
    const opt = document.createElement("option");
    opt.value = ver;
    opt.textContent = ver;
    modalVersionSelect.appendChild(opt);
  }

  await loadProfiles();
}
init();

async function loadProfiles() {
  currentProfiles = await eel.get_profiles()();
  const selected = await eel.get_selected_profile()();

  profileSelect.innerHTML =
    '<option value="" disabled selected>Оберіть або створіть збірку</option>';

  for (const name in currentProfiles) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    if (name === selected) opt.selected = true;
    profileSelect.appendChild(opt);
  }

  if (selected && currentProfiles[selected]) {
    handleProfileChange(selected);
  } else {
    activeProfileInfo.style.display = "none";
  }
}

async function handleProfileChange(profileName) {
  const p = currentProfiles[profileName];
  if (!p) return;

  await eel.set_selected_profile(profileName)();

  infoMcVersion.textContent = p.minecraft_version;
  infoLoader.textContent = p.downloader.toUpperCase();

  if (p.type === "github") {
    infoRepoContainer.style.display = "block";
    infoRepoStatus.textContent = p.version || "Синхронізовано";
  } else {
    infoRepoContainer.style.display = "none";
  }

  activeProfileInfo.style.display = "block";

  const downloader = p.downloader ? p.downloader.toLowerCase() : "";

  if (downloader === "forge" || downloader === "neoforge" || downloader === "fabric") {
    status.innerText = "Завантаження списку версій завантажувача...";
    loaderVersionWrapper.style.display = "block"; 
    loaderVersionSelect.innerHTML = '<option value="" disabled selected>Завантаження...</option>';
    
    let subVersions = [];
    try {
      if (downloader === "forge") {
        subVersions = await eel.get_forge_versions(p.minecraft_version)();
      } else if (downloader === "neoforge") {
        subVersions = await eel.get_neoforge_versions(p.minecraft_version)();
      } else if (downloader === "fabric") {
        subVersions = await eel.get_fabric_versions()(); // Fabric версії зазвичай загальні
      }
    } catch (err) {
      console.error("Помилка отримання версій:", err);
    }

    loaderVersionSelect.innerHTML = '<option value="" disabled selected>Оберіть версію</option>';
    
    if (subVersions && subVersions.length > 0) {
      for (const v of subVersions) {
        let isInstalled = false;
        try {
          if (downloader === "forge") {
            isInstalled = await eel.check_forge_installed(p.minecraft_version, v)();
          } else if (downloader === "neoforge") {
            isInstalled = await eel.check_neoforge_installed(p.minecraft_version, v)();
          } else if (downloader === "fabric") {
            isInstalled = await eel.check_fabric_installed(p.minecraft_version, v)();
          }
        } catch (e) {}

        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = isInstalled ? `✓ ${v}` : v;
        loaderVersionSelect.appendChild(opt);
      }
      status.innerText = "Конфігурацію завантажено.";
    } else {
      loaderVersionSelect.innerHTML = '<option value="" disabled>Версій не знайдено</option>';
      status.innerText = "Лоадери для цієї версії не знайдені.";
    }
  } else {
    loaderVersionWrapper.style.display = "none";
    status.innerText = "";
  }
}

profileSelect.addEventListener("change", (e) => {
  handleProfileChange(e.target.value);
});

openCreateModalBtn.addEventListener("click", () => {
  modalProfileName.value = "";
  modalRepoUrl.value = "";
  modalOverlay.classList.remove("modal-hidden");
});

cancelBtn.addEventListener("click", () => {
  modalOverlay.classList.add("modal-hidden");
});

openSettingsBtn.addEventListener("click", () => {
  settingsModalOverlay.classList.remove("modal-hidden");
});

settingsCloseBtn.addEventListener("click", () => {
  settingsModalOverlay.classList.add("modal-hidden");
});

ramSelect.addEventListener("change", () => {
  eel.save_config({ ram: ramSelect.value });
});

gpuSelect.addEventListener("change", () => {
  eel.save_config({ selected_gpu: gpuSelect.value });
});

document.getElementsByName("creation-type").forEach((radio) => {
  radio.addEventListener("change", (e) => {
    if (e.target.value === "manual") {
      manualFields.style.display = "block";
      githubFields.style.display = "none";
    } else {
      manualFields.style.display = "none";
      githubFields.style.display = "block";
    }
  });
});

saveBtn.addEventListener("click", async () => {
  const name = modalProfileName.value.trim();
  if (!name) return alert("Вкажіть назву збірки!");

  const type = document.querySelector(
    'input[name="creation-type"]:checked',
  ).value;
  let result;

  if (type === "manual") {
    const ver = modalVersionSelect.value;
    const ldr = modalLoaderSelect.value;
    if (!ver) return alert("Оберіть версію гри!");
    result = await eel.create_profile_manual(name, ver, ldr)();
  } else {
    const url = modalRepoUrl.value.trim();
    if (!url) return alert("Вкажіть лінк на репозиторій!");
    status.innerText = "Парсинг settings.json з GitHub...";
    result = await eel.create_profile_github(name, url)();
  }

  if (result && result.success) {
    modalOverlay.classList.add("modal-hidden");
    await loadProfiles();
    status.innerText = `Збірку "${name}" успішно створено!`;
  } else {
    alert("Помилка: " + (result?.error || "Невідома помилка"));
    status.innerText = "Помилка створення профілю.";
  }
});

usernameInput.addEventListener("input", () =>
  eel.save_username(usernameInput.value),
);

document
  .getElementById("open-folder-btn")
  .addEventListener("click", () => eel.open_minecraft_folder());

btn.addEventListener("click", async () => {
  const selected = profileSelect.value;
  if (!selected || !currentProfiles[selected])
    return (status.innerText = "Оберіть збірку!");

  const p = currentProfiles[selected];

  if (
    (p.downloader === "forge" || p.downloader === "neoforge" || p.downloader === "fabric") &&
    !loaderVersionSelect.value
  ) {
    return (status.innerText = "Оберіть версію завантажувача!");
  }

  const data = {
    version: p.minecraft_version,
    username: usernameInput.value,
    loader: p.downloader,
    ram: ramSelect.value,
    gpu: gpuSelect.value,
    // Просто передаємо вибране значення для будь-якого модлоадера
    loader_version: loaderVersionSelect.value 
  };

  btn.disabled = true;
  const result = await eel.launch_game(data)();

  if (!result.success) {
    status.innerText = "Помилка: " + result.error;
    btn.disabled = false;
  } else {
    status.innerText = "Гра запущена!";
    btn.innerText = "В ГРІ";
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

const deleteBtn = document.getElementById("delete-profile-btn");
if (deleteBtn) {
  deleteBtn.addEventListener("click", async () => {
    const profileSelect = document.getElementById("profile-select");
    const selectedProfile = profileSelect.value;

    if (!selectedProfile || selectedProfile === "") {
      alert("Будь ласка, спочатку оберіть збірку, яку бажаєте видалити.");
      return;
    }

    const confirmed = confirm(`Ви дійсно хочете видалити збірку "${selectedProfile}"?`);
    
    if (confirmed) {
      try {
        const result = await eel.delete_profile(selectedProfile)();
        if (result && result.success) {
          window.location.reload();
        } else {
          alert("Помилка при видаленні: " + (result ? result.error : "Невідома помилка"));
        }
      } catch (err) {
        alert("Помилка виконання команди видалення: " + err);
      }
    }
  });
}