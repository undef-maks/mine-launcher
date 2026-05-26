import eel
import os
import minecraft_launcher_lib as mll
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MINECRAFT_PATH = os.path.join(BASE_DIR, 'minecraft_data')

if not os.path.exists(MINECRAFT_PATH):
    os.makedirs(MINECRAFT_PATH)

eel.init('frontend')

def send_log(message):
    print(f"[LOG]: {message}")
    eel.log_update({'payload': message})

@eel.expose
def get_versions():
    versions = mll.utils.get_version_list()
    return [v['id'] for v in versions if v['type'] == 'release']

@eel.expose
def check_installed(version):
    versions_path = os.path.join(MINECRAFT_PATH, 'versions', version)
    return os.path.exists(versions_path) and os.path.exists(os.path.join(versions_path, f"{version}.json"))

@eel.expose
def launch_game(data):
    version = data['version']
    
    def progress_callback(progress):
        eel.progress_update({'percent': progress, 'task': f"Завантаження: {progress}%"})

    try:
        if not check_installed(version):
            send_log(f"Початок встановлення версії {version}...")
            mll.install.install_minecraft_version(
                version, 
                MINECRAFT_PATH, 
                callback={
                    'setProgress': progress_callback,
                    'setStatus': lambda msg: send_log(f"Статус: {msg}")
                }
            )
            send_log("Встановлення завершено успішно.")
        
        send_log(f"Запуск гри для користувача {data['username']}...")
        options = {'username': data['username'], 'uuid': '0', 'token': '0'}
        
        env = os.environ.copy()
        command = mll.command.get_minecraft_command(version, MINECRAFT_PATH, options)
        subprocess.Popen(command, env=env)
        send_log("Гра успішно запущена.")
        
        return {"success": True}
    except Exception as e:
        send_log(f"ПОМИЛКА: {str(e)}")
        return {"success": False, "error": str(e)}

eel.start('index.html', size=(900, 600))
