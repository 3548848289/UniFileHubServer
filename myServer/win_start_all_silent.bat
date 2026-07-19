@echo off


net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)


setlocal

set "ROOT_DIR=E:\UniFileHub\UniFileHub-Server"

echo Starting MySQL...
net start mysql8

echo Starting Python services...

start "" pythonw "%ROOT_DIR%\UserInfo\app.py"
start "" pythonw "%ROOT_DIR%\SharedFile\app.py"
start "" pythonw "%ROOT_DIR%\FIleHistory\app.py"
start "" pythonw "%ROOT_DIR%\PersonalDrive\run.py"
start "" pythonw "%ROOT_DIR%\ClipboardSync\app.py"

echo.
echo All available services have been started.