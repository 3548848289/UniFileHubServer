import subprocess

services = [
    ("UserInfo", "app.py"),
    ("SharedFile", "app.py"),
    ("FileHistory", "app.py")
]

for folder, entry in services:
    subprocess.Popen(
        ["start", "cmd", "/k", "python", entry],
        cwd=f"./{folder}",
        shell=True
    )
