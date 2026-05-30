
@echo off
:: 在 UserInfo 文件夹运行 app.py，窗口标题设为 [UserInfo]
start "UserInfo" cmd /k "cd /d %~dp0UserInfo && python app.py"

:: 在 SharedFile 文件夹运行 app.py，窗口标题设为 [SharedFile]
start "SharedFile" cmd /k "cd /d %~dp0SharedFile && python app.py"

:: 在 FIleHistory 文件夹运行 app.py，窗口标题设为 [FIleHistory]
start "FIleHistory" cmd /k "cd /d %~dp0FIleHistory && python app.py"

:: 在 PersonalDrive 文件夹运行 app.py，窗口标题设为 [PersonalDrive]
start "PersonalDrive" cmd /k "cd /d %~dp0PersonalDrive && python run.py"

:: 在 SharedCSV/build/Debug 文件夹运行 exe，窗口标题设为 [BoostAsioServer]
start "BoostAsioServer" cmd /k "cd /d %~dp0SharedCSV\build\Release && BoostAsioServer.exe"

echo 所有服务已启动...
pause
