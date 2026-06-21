import eel
import os
import minecraft_launcher_lib as mll
import subprocess
import threading
import json
import uuid
import platform 
import requests
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MINECRAFT_PATH = os.path.join(BASE_DIR, 'minecraft_data')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

if not os.path.exists(MINECRAFT_PATH):
    os.makedirs(MINECRAFT_PATH)

eel.init('frontend')

@eel.expose
def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                if "ram" not in config:
                    config["ram"] = "4G"
                if "selected_gpu" not in config:
                    config["selected_gpu"] = "auto"
                return config
            except:
                pass
    return {"username": "", "profiles": {}, "selected_profile": "", "ram": "4G", "selected_gpu": "auto"}

@eel.expose
def save_config(config_data):
    current = get_config()
    current.update(config_data)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(current, f, ensure_ascii=False, indent=4)

def launcher_callback():
    return {
        "setStatus": lambda text: (eel.progress_update({'task': text}), eel.log_update({'payload': text})),
        "setProgress": lambda progress: None,
        "setMax": lambda max_val: None
    }

def download_single_mod(download_url, local_file_path, file_name):
    try:
        eel.log_update({'payload': f"Початок завантаження: {file_name}"})
        mod_res = requests.get(download_url, stream=True, timeout=15)
        if mod_res.status_code == 200:
            expected_size = mod_res.headers.get('content-length')
            
            with open(local_file_path, 'wb') as f:
                for chunk in mod_res.iter_content(chunk_size=1048576):
                    if chunk:
                        f.write(chunk)
            
            if expected_size is not None:
                actual_size = os.path.getsize(local_file_path)
                if actual_size != int(expected_size):
                    eel.log_update({'payload': f"Помилка: {file_name} завантажився не повністю! Видалення битого файлу..."})
                    try:
                        os.remove(local_file_path)
                    except:
                        pass
                    return

            eel.log_update({'payload': f"Успішно скачано: {file_name}"})
    except Exception as e:
        eel.log_update({'payload': f"Помилка завантаження {file_name}: {str(e)}"})
        if os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except:
                pass

def sync_mods_from_github(repo_url):
    eel.progress_update({'task': "Синхронізація модифікацій..."})
    eel.log_update({'payload': "Отримання списку модів з GitHub..."})
    
    url_parts = repo_url.strip('/').split('/')
    if len(url_parts) < 2:
        return
    
    user = url_parts[-2]
    repo = url_parts[-1]
    
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents/mods"
    local_mods_dir = os.path.join(MINECRAFT_PATH, 'mods')
    
    if not os.path.exists(local_mods_dir):
        os.makedirs(local_mods_dir)
        
    try:
        headers = {"User-Agent": "Minecraft-Launcher"}
        res = requests.get(api_url, headers=headers, timeout=10)
        
        if res.status_code != 200:
            eel.log_update({'payload': f"Папку mods не знайдено (Код: {res.status_code})"})
            return
            
        remote_files = res.json()
        remote_mod_names = []
        threads = []
        
        for file_info in remote_files:
            if file_info.get('type') == 'file' and file_info.get('name', '').endswith('.jar'):
                file_name = file_info['name']
                download_url = file_info['download_url']
                remote_mod_names.append(file_name)
                
                local_file_path = os.path.join(local_mods_dir, file_name)
                if not os.path.exists(local_file_path):
                    t = threading.Thread(
                        target=download_single_mod, 
                        args=(download_url, local_file_path, file_name),
                        daemon=True
                    )
                    threads.append(t)
                    t.start()
                                        
        for t in threads:
            t.join()
                                        
        for local_file in os.listdir(local_mods_dir):
            if local_file.endswith('.jar') and local_file not in remote_mod_names:
                eel.log_update({'payload': f"Видалення застарілого моду: {local_file}"})
                try:
                    os.remove(os.path.join(local_mods_dir, local_file))
                except:
                    pass
                    
        eel.log_update({'payload': "Усі моди синхронізовано!"})
    except Exception as e:
        eel.log_update({'payload': f"Помилка синхронізації: {str(e)}"})

@eel.expose
def save_username(username):
    save_config({'username': username})

@eel.expose
def load_username():
    return get_config().get('username', '')

@eel.expose
def open_minecraft_folder():
    path = os.path.realpath(MINECRAFT_PATH)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin": 
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

@eel.expose
def get_versions():
    # Отримуємо всі доступні версії
    all_versions = mll.utils.get_version_list()
    
    # Фільтруємо: залишаємо лише ті, які мають тип 'release' 
    # і не містять дефісів (якщо ви хочете тільки чисті цифрові версії)
    stable_versions = [
        v["id"] for v in all_versions 
        if v["type"] == "release" and "-" not in v["id"]
    ]
    
    return stable_versions

@eel.expose
def get_profiles():
    return get_config().get('profiles', {})

@eel.expose
def get_selected_profile():
    return get_config().get('selected_profile', '')

@eel.expose
def set_selected_profile(name):
    save_config({'selected_profile': name})

@eel.expose
def check_installed(version):
    return os.path.exists(os.path.join(MINECRAFT_PATH, 'versions', version))

@eel.expose
def check_forge_installed(version, forge_version):
    versions_path = os.path.join(MINECRAFT_PATH, 'versions')
    if not os.path.exists(versions_path): return False
    for folder in os.listdir(versions_path):
        if version in folder and forge_version.split('.')[-1] in folder:
            return True
    return False

@eel.expose
def check_neoforge_installed(version, neoforge_version):
    versions_path = os.path.join(MINECRAFT_PATH, 'versions')
    if not os.path.exists(versions_path): return False
    for folder in os.listdir(versions_path):
        if "neoforge" in folder.lower() and version in folder:
            if neoforge_version and neoforge_version in folder:
                return True
    return False

@eel.expose
def check_fabric_installed(version, fabric_version):
    try:
        return mll.fabric.is_fabric_installed(version, MINECRAFT_PATH, fabric_version)
    except:
        return False

@eel.expose
def create_profile_manual(name, mc_version, loader):
    config = get_config()
    profiles = config.get('profiles', {})
    profiles[name] = {
        "type": "manual",
        "minecraft_version": mc_version,
        "downloader": loader
    }
    save_config({'profiles': profiles, 'selected_profile': name})
    return {"success": True}

@eel.expose
def create_profile_github(name, repo_url):
    raw_url = repo_url.replace("github.com", "raw.githubusercontent.com").strip('/')
    if not raw_url.endswith("/main") and not raw_url.endswith("/master"):
        raw_url += "/main"
    settings_url = f"{raw_url}/settings.json"
    try:
        res = requests.get(settings_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            mc_version = data.get('minecraft_version')
            downloader = data.get('downloader', 'vanilla')
            version = data.get('version', '1.0.0')
            if not mc_version:
                return {"success": False, "error": "settings.json не містить minecraft_version"}
            config = get_config()
            profiles = config.get('profiles', {})
            profiles[name] = {
                "type": "github",
                "repo_url": repo_url,
                "minecraft_version": mc_version,
                "downloader": downloader,
                "version": version
            }
            save_config({'profiles': profiles, 'selected_profile': name})
            return {"success": True}
        return {"success": False, "error": f"Файл settings.json не знайдено (Код: {res.status_code})"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@eel.expose
def get_available_gpus():
    gpus = []
    sys_platform = platform.system()
    try:
        if sys_platform == "Windows":
            cmd = "wmic path win32_VideoController get name"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            for idx, line in enumerate(lines[1:]):
                gpus.append({"id": f"win_gpu_{idx}", "name": line})
        elif sys_platform == "Linux":
            output = subprocess.check_output("lspci | grep -E 'VGA|3D'", shell=True).decode('utf-8', errors='ignore')
            for idx, line in enumerate(output.split('\n')):
                if line.strip():
                    name = line.split(':', 2)[-1].strip()
                    gpus.append({"id": f"linux_gpu_{idx}", "name": name})
        elif sys_platform == "Darwin":
            gpus.append({"id": "apple_integrated", "name": "Apple Display/Integrated GPU"})
    except:
        pass
    if not gpus:
        gpus = [
            {"id": "discrete", "name": "Дискретний адаптер (Висока продуктивність)"},
            {"id": "integrated", "name": "Інтегрований адаптер (Енергоощадження)"}
        ]
    return gpus

@eel.expose
def launch_game(data):
    try:
        mc_ver = data.get('version')
        loader = data.get('loader')
        ram_amount = data.get('ram', '4G')
        username = data.get('username')
        loader_version = data.get('loader_version') # Те, що приходить з фронтенду
        
        versions_path = os.path.join(MINECRAFT_PATH, 'versions')
        callbacks = launcher_callback()
        
        # 1. Забезпечуємо наявність базової версії
        if not os.path.exists(os.path.join(versions_path, mc_ver)):
            eel.progress_update({'task': f"Завантаження {mc_ver}..."})
            mll.install.install_minecraft_version(mc_ver, MINECRAFT_PATH, callback=callbacks)

        # 2. Визначаємо версію для запуску
        version_to_launch = mc_ver # За замовчуванням ваніла
        
        if loader == "fabric":
            # Якщо версія лоадера не вибрана, беремо останню
            lv = loader_version if loader_version else mll.fabric.get_latest_loader_version()
            expected = f"fabric-loader-{lv}-{mc_ver}"
            
            # Якщо папки немає, встановлюємо
            if not os.path.exists(os.path.join(versions_path, expected)):
                eel.progress_update({'task': "Встановлення Fabric..."})
                mll.fabric.install_fabric(mc_ver, MINECRAFT_PATH, loader_version=lv, callback=callbacks)
            version_to_launch = expected

        elif loader == "forge":
            # Для Forge логіка простіша, але перевіряємо чи є папка
            for folder in os.listdir(versions_path):
                if mc_ver in folder and "forge" in folder.lower():
                    version_to_launch = folder
                    break
        
        # 3. Формуємо команду
        options = {
            'username': username,
            'uuid': str(uuid.uuid5(uuid.NAMESPACE_DNS, username)),
            'token': '0',
            'jvmArguments': [f'-Xmx{ram_amount}', f'-Xms{ram_amount}']
        }
        
        # Генеруємо команду
        command = mll.command.get_minecraft_command(version_to_launch, MINECRAFT_PATH, options)
        
        # Запуск процесу (без зайвих insert, які можуть ламати Windows)
        process = subprocess.Popen(command)
        threading.Thread(target=lambda: (process.wait(), eel.game_closed()), daemon=True).start()
        
        return {"success": True}

    except Exception as e:
        # Виводимо помилку в консоль, щоб ви бачили, що саме сталось
        print(f"ПОМИЛКА ЗАПУСКУ: {str(e)}")
        return {"success": False, "error": str(e)}

@eel.expose
def get_forge_versions(minecraft_version):
    try:
        all_forge = mll.forge.list_forge_versions()
        return [v for v in all_forge if v.startswith(minecraft_version)]
    except:
        return []

@eel.expose
def get_fabric_versions():
    try:
        # Правильна функція бібліотеки, яка повертає список словників
        versions = mll.fabric.get_all_loader_versions()
        # Витягуємо лише номери версій (наприклад, "0.15.11")
        return [v['version'] for v in versions]
    except Exception as e:
        print(f"Помилка отримання версій Fabric: {e}")
        return []



@eel.expose
def delete_profile(name):
    config = get_config()
    profiles = config.get('profiles', {})
    if name in profiles:
        del profiles[name]
        if config.get('selected_profile') == name:
            config['selected_profile'] = ''
        save_config({'profiles': profiles, 'selected_profile': config['selected_profile']})
        return {"success": True}
    return {"success": False, "error": "Профіль не знайдено"}

@eel.expose
def get_neoforge_versions(minecraft_version):
    try:
        url = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return []
            
        root = ET.fromstring(response.content)
        all_versions = [v.text for v in root.findall(".//version")]
        
        parts = minecraft_version.split('.')
        if minecraft_version == "1.20.1":
            prefix = "47.1."
        elif len(parts) == 2:
            prefix = f"{parts[1]}.0."
        elif len(parts) >= 3:
            prefix = f"{parts[1]}.{parts[2]}."
        else:
            return []
            
        filtered_versions = [v for v in all_versions if v.startswith(prefix)]
        filtered_versions.sort(key=lambda s: [int(u) for u in s.split('.') if u.isdigit()], reverse=True)
        return filtered_versions
    except Exception as e:
        print(f"Помилка отримання версій NeoForge з Maven: {e}")
        return []

eel.start('index.html', size=(900, 600))