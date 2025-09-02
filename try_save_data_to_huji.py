import os
import shutil
import subprocess
# subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True) #for be sure will be permission
# subprocess.run(["sudo", "mount", "-a"], check=True)
folder_name= "exp_11_08_2025"
folder_path = os.path.join(os.getcwd(), "experiments",folder_name)
remote_folder="/mnt/labfolder/Noam/results"
try:
    src = folder_path
    dst = os.path.join(remote_folder, os.path.basename(src))
    shutil.copytree(src, dst, dirs_exist_ok=True)
    print("data updated")

except PermissionError:
    print("PermissionError")
except FileNotFoundError:
    print("FileNotFoundError")
except Exception as e:
    print(f"Exception: {e}")
