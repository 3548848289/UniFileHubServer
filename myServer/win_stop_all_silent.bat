@echo off

:: 请求管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo Stopping Python services...

wmic process where "CommandLine like '%%UserInfo\\app.py%%'" delete >nul 2>&1
wmic process where "CommandLine like '%%SharedFile\\app.py%%'" delete >nul 2>&1
wmic process where "CommandLine like '%%FIleHistory\\app.py%%'" delete >nul 2>&1
wmic process where "CommandLine like '%%PersonalDrive\\run.py%%'" delete >nul 2>&1
wmic process where "CommandLine like '%%ClipboardSync\\app.py%%'" delete >nul 2>&1

:: echo Stopping UniFileHub...

:: taskkill /F /IM UniFileHub.exe >nul 2>&1

:: echo Stopping MySQL...

:: net stop mysql8

echo.
echo All services stopped.
pause