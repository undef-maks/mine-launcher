import time, os, shutil, subprocess, sys

def apply():
    time.sleep(2)
    src_base = "temp_update"
    try:
        folders = [f for f in os.listdir(src_base) if os.path.isdir(os.path.join(src_base, f))]
        src = os.path.join(src_base, folders[0]) if folders else src_base
        
        for item in os.listdir(src):
            if item not in ["minecraft_data", "config.json", "updater.py"]:
                target = item
                if os.path.exists(target):
                    if os.path.isdir(target): shutil.rmtree(target)
                    else: os.remove(target)
                shutil.move(os.path.join(src, item), target)
        shutil.rmtree(src_base)
        subprocess.Popen([sys.executable, "main.py"])
    except Exception as e:
        print(f"Помилка оновлення: {e}")
    sys.exit()

if __name__ == "__main__":
    apply()
