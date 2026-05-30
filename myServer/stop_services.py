import psutil
import os
import signal

services = [
    ("UserInfo", "app.py"),
    ("SharedFile", "app.py"),
    ("FIleHistory", "app.py")
]

def stop_service(folder, entry):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and "python" in cmdline[0] and entry in " ".join(cmdline):
                print(f"Stopping {folder}/{entry} (PID {proc.pid})")
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

if __name__ == "__main__":
    for folder, entry in services:
        stop_service(folder, entry)
