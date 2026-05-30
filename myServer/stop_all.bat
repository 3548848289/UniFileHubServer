@echo off
setlocal

echo Stopping UniFileServer services...

taskkill /F /FI "WINDOWTITLE eq UserInfo" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq SharedFile" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq FIleHistory" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq PersonalDrive" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq BoostAsioServer" >nul 2>&1

echo All managed services have been stopped.
pause
