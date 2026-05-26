import eel
import os
import minecraft_launcher_lib as mll
import subprocess
import threading
import json
import uuid
import platform 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MINECRAFT_PATH = os.path.join(BASE_DIR, 'minecraft_data')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

if not os.path.exists(MINECRAFT_PATH):
    os.makedirs(MINECRAFT_PATH)

eel.init('frontend')

@eel.expose
def save_username(username):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'username': username}, f)
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
def load_username():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f).get('username', '')
    return ''

@eel.expose
def get_versions():
    versions = mll.utils.get_version_list()
    return [v['id'] for v in versions if v['type'] == 'release']

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
def launch_game(data):
    mc_ver = data['version']
    loader = data['loader']
    
    try:
        if loader == "forge":
            forge_ver = data['forge_version']
            
            versions_path = os.path.join(MINECRAFT_PATH, 'versions')
            version_to_launch = None
            for folder in os.listdir(versions_path):
                if mc_ver in folder and forge_ver.split('.')[-1] in folder:
                    version_to_launch = folder
                    break
            
            if not version_to_launch:
                eel.progress_update({'task': "Встановлення Forge..."})
                mll.forge.install_forge_version(forge_ver, MINECRAFT_PATH)
                for folder in os.listdir(versions_path):
                    if mc_ver in folder and forge_ver.split('.')[-1] in folder:
                        version_to_launch = folder
                        break
            else:
                eel.progress_update({'task': "Запуск гри..."})
        else:
            if not os.path.exists(os.path.join(MINECRAFT_PATH, 'versions', mc_ver)):
                eel.progress_update({'task': "Завантаження гри..."})
                mll.install.install_minecraft_version(mc_ver, MINECRAFT_PATH)
            version_to_launch = mc_ver
        
        if not version_to_launch:
            raise Exception("Не вдалося знайти встановлену версію Forge")

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

eel.start('index.html', size=(900, 600))
