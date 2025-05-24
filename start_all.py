import subprocess

services = [
    ("UserInfo", "app.py"),
    ("SharedFile", "app.py"),
    ("FIleHistory", "app.py")
]

processes = []

for folder, entry in services:
    p = subprocess.Popen(["python3", entry], cwd=f"./{folder}")
    processes.append(p)

# 可选：阻塞主线程直到用户退出
try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("Stopping all services...")
    for p in processes:
        p.terminate()
