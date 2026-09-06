@echo off
setlocal

set "ROOT_DIR=%~dp0.."

echo Starting UniFileHub Python services from %ROOT_DIR%
echo.

start "UniFileHub-UserInfo" cmd /k "title UniFileHub-UserInfo && cd /d ""%ROOT_DIR%\UserInfo"" && python app.py"
start "UniFileHub-SharedFile" cmd /k "title UniFileHub-SharedFile && cd /d ""%ROOT_DIR%\SharedFile"" && python app.py"
start "UniFileHub-FIleHistory" cmd /k "title UniFileHub-FIleHistory && cd /d ""%ROOT_DIR%\FIleHistory"" && python app.py"
start "UniFileHub-PersonalDrive" cmd /k "title UniFileHub-PersonalDrive && cd /d ""%ROOT_DIR%\PersonalDrive"" && python run.py"
start "UniFileHub-ClipboardSync" cmd /k "title UniFileHub-ClipboardSync && cd /d ""%ROOT_DIR%\ClipboardSync"" && python app.py"
start "UniFileHub-Discovery" cmd /k "title UniFileHub-Discovery && cd /d ""%ROOT_DIR%\Discovery"" && python app.py"

echo.
echo Python services have been started in terminal windows.

