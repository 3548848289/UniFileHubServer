@echo off
echo 正在停止所有 SmartDeskServer 服务...

:: 按窗口标题关闭
taskkill /F /FI "WINDOWTITLE eq UserInfo"
taskkill /F /FI "WINDOWTITLE eq SharedFile"
taskkill /F /FI "WINDOWTITLE eq FIleHistory"
taskkill /F /FI "WINDOWTITLE eq PersonalDrive"
taskkill /F /FI "WINDOWTITLE eq BoostAsioServer"

echo 所有服务已停止
pause
