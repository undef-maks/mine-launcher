import eel
import os
import minecraft_launcher_lib as mll
import subprocess
import threading
import json
import uuid
import platform 
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MINECRAFT_PATH = os.path.join(BASE_DIR, 'minecraft_data')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

if not os.path.exists(MINECRAFT_PATH):
    os.makedirs(MINECRAFT_PATH)

eel.init('frontend')

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {"username": "", "profiles": {}, "selected_profile": ""}

def save_config(config_data):
    current = get_config()
    current.update(config_data)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(current, f)

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
            with open(local_file_path, 'wb') as f:
                for chunk in mod_res.iter_content(chunk_size=1048576):
                    if chunk:
                        f.write(chunk)
            eel.log_update({'payload': f"Успішно скачано: {file_name}"})
    except Exception as e:
        eel.log_update({'payload': f"Помилка завантаження {file_name}: {str(e)}"})

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
    versions = mll.utils.get_version_list()
    return [v['id'] for v in versions if v['type'] == 'release']

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
            return True
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
def launch_game(data):
    mc_ver = data['version']
    loader = data['loader']
    try:
        config = get_config()
        selected_profile = config.get('selected_profile', '')
        profiles = config.get('profiles', {})
        
        if selected_profile in profiles:
            profile_data = profiles[selected_profile]
            if profile_data.get('type') == 'github':
                repo_url = profile_data.get('repo_url')
                
                raw_url = repo_url.replace("github.com", "raw.githubusercontent.com").strip('/')
                if not raw_url.endswith("/main") and not raw_url.endswith("/master"):
                    raw_url += "/main"
                settings_url = f"{raw_url}/settings.json"
                
                try:
                    res = requests.get(settings_url, timeout=5)
                    if res.status_code == 200:
                        remote_data = res.json()
                        remote_version = remote_data.get('version', '1.0.0')
                        if remote_version != profile_data.get('version'):
                            eel.log_update({'payload': f"Знайдено нову версію збірки: {remote_version}. Оновлення..."})
                            profiles[selected_profile]['version'] = remote_version
                            profiles[selected_profile]['minecraft_version'] = remote_data.get('minecraft_version', mc_ver)
                            profiles[selected_profile]['downloader'] = remote_data.get('downloader', loader)
                            save_config({'profiles': profiles})
                            mc_ver = remote_data.get('minecraft_version', mc_ver)
                            loader = remote_data.get('downloader', loader)
                except:
                    pass

                sync_mods_from_github(repo_url)

        versions_path = os.path.join(MINECRAFT_PATH, 'versions')
        version_to_launch = None
        callbacks = launcher_callback()

        if loader == "forge":
            forge_ver = data.get('forge_version') or mll.forge.list_forge_versions()[0]
            for folder in os.listdir(versions_path):
                if mc_ver in folder and forge_ver.split('.')[-1] in folder:
                    version_to_launch = folder
                    break
            if not version_to_launch:
                eel.progress_update({'task': "Встановлення Forge..."})
                mll.forge.install_forge_version(forge_ver, MINECRAFT_PATH, callback=callbacks)
                for folder in os.listdir(versions_path):
                    if mc_ver in folder and forge_ver.split('.')[-1] in folder:
                        version_to_launch = folder
                        break
            else:
                eel.progress_update({'task': "Запуск гри..."})

        elif loader == "neoforge":
            if not os.path.exists(versions_path):
                os.makedirs(versions_path)
            for folder in os.listdir(versions_path):
                if "neoforge" in folder.lower() and mc_ver in folder:
                    version_to_launch = folder
                    break
            if not version_to_launch:
                eel.progress_update({'task': f"Встановлення NeoForge для {mc_ver}..."})
                if not os.path.exists(os.path.join(MINECRAFT_PATH, 'versions', mc_ver)):
                    mll.install.install_minecraft_version(mc_ver, MINECRAFT_PATH, callback=callbacks)
                neoforge_manager = mll.mod_loader.get_mod_loader("neoforge")
                version_to_launch = neoforge_manager.install(mc_ver, MINECRAFT_PATH, callback=callbacks)
            else:
                eel.progress_update({'task': "Запуск гри..."})

        else:
            if not os.path.exists(os.path.join(MINECRAFT_PATH, 'versions', mc_ver)):
                eel.progress_update({'task': "Завантаження гри..."})
                mll.install.install_minecraft_version(mc_ver, MINECRAFT_PATH, callback=callbacks)
            version_to_launch = mc_ver
        
        if not version_to_launch:
            raise Exception(f"Не вдалося знайти або встановити версію для {loader}")

        player_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, data['username']))
        options = {'username': data['username'], 'uuid': player_uuid, 'token': '0'}
        command = mll.command.get_minecraft_command(version_to_launch, MINECRAFT_PATH, options)
        command.insert(1, "-Dsun.awt.X11.ignore_bad_visuals=1")
        command.insert(2, "-Dglfw.platform=x11")
        
        process = subprocess.Popen(command, env=os.environ.copy())
        threading.Thread(target=lambda: (process.wait(), eel.game_closed()), daemon=True).start()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@eel.expose
def get_forge_versions(minecraft_version):
    try:
        all_forge = mll.forge.list_forge_versions()
        return [v for v in all_forge if v.startswith(minecraft_version)]
    except Exception as e:
        return []

@eel.expose
def get_neoforge_versions(minecraft_version):
    try:
        neoforge_manager = mll.mod_loader.get_mod_loader("neoforge")
        supported_mc_versions = neoforge_manager.get_minecraft_versions(True)
        if minecraft_version in supported_mc_versions:
            return [minecraft_version]
        return []
    except Exception as e:
        return []

eel.start('index.html', size=(900, 600))
