@echo off
setlocal

echo Stopping UniFileHub Python services...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$titles=@('UniFileHub-UserInfo','UniFileHub-SharedFile','UniFileHub-FIleHistory','UniFileHub-PersonalDrive','UniFileHub-ClipboardSync','UniFileHub-Discovery'); Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cmd.exe' -and $_.CommandLine } | ForEach-Object { $cmd=$_.CommandLine; foreach($title in $titles){ if($cmd -like ('*title ' + $title + '*')){ & taskkill.exe /PID $_.ProcessId /T /F *> $null; break } } }"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports=@(5000,5001,5002,5005,5006); foreach($port in $ports){ Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { if($_.OwningProcess -and $_.OwningProcess -ne $PID){ & taskkill.exe /PID $_.OwningProcess /T /F *> $null } } }"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$udpports=@(15000); foreach($port in $udpports){ Get-NetUDPEndpoint -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object { if($_.OwningProcess -and $_.OwningProcess -ne $PID){ & taskkill.exe /PID $_.OwningProcess /T /F *> $null } } }"

echo.
echo UniFileHub Python services have been stopped.
