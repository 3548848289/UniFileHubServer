@echo off
setlocal

set "ROOT_DIR=%~dp0.."

echo Starting Python services from %ROOT_DIR%

start "UserInfo" cmd /k "cd /d ""%ROOT_DIR%\UserInfo"" && python app.py"
start "SharedFile" cmd /k "cd /d ""%ROOT_DIR%\SharedFile"" && python app.py"
start "FIleHistory" cmd /k "cd /d ""%ROOT_DIR%\FIleHistory"" && python app.py"
start "PersonalDrive" cmd /k "cd /d ""%ROOT_DIR%\PersonalDrive"" && python run.py"
start "ClipboardSync" cmd /k "cd /d ""%ROOT_DIR%\ClipboardSync"" && python app.py"

if exist "%ROOT_DIR%\SharedCSV\build\Release\BoostAsioServer.exe" (
    start "BoostAsioServer" cmd /k "cd /d ""%ROOT_DIR%\SharedCSV\build\Release"" && BoostAsioServer.exe"
) else (
    echo SharedCSV executable not found, skipping BoostAsioServer.
)

echo.
echo All available services have been started.
pause
