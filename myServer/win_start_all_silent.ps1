$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $PSScriptRoot "logs"
$MysqlService = if ($env:UNIFILEHUB_MYSQL_SERVICE) { $env:UNIFILEHUB_MYSQL_SERVICE } else { "mysql8" }
$MysqlHost = "127.0.0.1"
$MysqlPort = 3306
$ClientExe = if ($env:UNIFILEHUB_CLIENT_EXE) { $env:UNIFILEHUB_CLIENT_EXE } else { "E:\APP\UniFileHub\UniFileHub.exe" }

$Services = @(
    @{ Name = "SharedFile";    Dir = "SharedFile";    Script = "app.py"; Port = 5000;  Protocol = "TCP" }
    @{ Name = "UserInfo";      Dir = "UserInfo";      Script = "app.py"; Port = 5001;  Protocol = "TCP" }
    @{ Name = "FIleHistory";   Dir = "FIleHistory";   Script = "app.py"; Port = 5002;  Protocol = "TCP" }
    @{ Name = "PersonalDrive"; Dir = "PersonalDrive"; Script = "run.py"; Port = 5005;  Protocol = "TCP" }
    @{ Name = "ClipboardSync"; Dir = "ClipboardSync"; Script = "app.py"; Port = 5006;  Protocol = "TCP" }
    @{ Name = "Discovery";     Dir = "Discovery";     Script = "app.py"; Port = 15000; Protocol = "UDP" }
)

function Wait-TcpPort($HostName, $Port, $TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $async = $client.BeginConnect($HostName, $Port, $null, $null)
            if ($async.AsyncWaitHandle.WaitOne(1000)) {
                $client.EndConnect($async)
                return $true
            }
        } catch {
        } finally {
            $client.Close()
        }

        Start-Sleep -Seconds 1
    }

    return $false
}

function Wait-UdpPort($Port, $TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $endpoint = Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($endpoint) {
            return $true
        }

        Start-Sleep -Seconds 1
    }

    return $false
}

function Start-MysqlService {
    Write-Host ("Starting MySQL service {0}..." -f $MysqlService)
    $service = Get-Service -Name $MysqlService -ErrorAction SilentlyContinue
    if (-not $service) {
        throw "MySQL service '$MysqlService' was not found. Set UNIFILEHUB_MYSQL_SERVICE if your service name is different."
    }

    if ($service.Status -ne "Running") {
        try {
            Start-Service -Name $MysqlService
        } catch {
            Write-Host "Start-Service failed, trying net start..."
            & net start $MysqlService | Out-Host
        }
    }

    $service.WaitForStatus("Running", [TimeSpan]::FromSeconds(60))

    if (-not (Wait-TcpPort $MysqlHost $MysqlPort 60)) {
        throw "MySQL service is running, but TCP $MysqlHost`:$MysqlPort is not ready."
    }

    Write-Host "MySQL is ready."
}

function Start-PythonService($Service) {
    $workDir = Join-Path $RootDir $Service.Dir
    $scriptPath = Join-Path $workDir $Service.Script
    if (-not (Test-Path $scriptPath)) {
        Write-Host ("Skipping {0}: script not found: {1}" -f $Service.Name, $scriptPath)
        return
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        throw "python.exe was not found in PATH."
    }

    $stdout = Join-Path $LogDir ($Service.Name + ".out.log")
    $stderr = Join-Path $LogDir ($Service.Name + ".err.log")

    $protocol = if ($Service.Protocol) { $Service.Protocol } else { "TCP" }

    Write-Host ("Starting {0} on {1} port {2}..." -f $Service.Name, $protocol, $Service.Port)
    $process = Start-Process `
        -FilePath $python.Source `
        -ArgumentList @($scriptPath) `
        -WorkingDirectory $workDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru

    $isListening = if ($protocol -eq "UDP") {
        Wait-UdpPort $Service.Port 25
    } else {
        Wait-TcpPort "127.0.0.1" $Service.Port 25
    }

    if (-not $isListening) {
        Write-Host ("Warning: {0} did not open {1} port {2} within 25 seconds. Check {3} and {4}." -f $Service.Name, $protocol, $Service.Port, $stdout, $stderr)
    } else {
        Write-Host ("{0} is listening on {1} port {2}. PID: {3}" -f $Service.Name, $protocol, $Service.Port, $process.Id)
    }
}

function Start-UniFileHubClient {
    if (-not $ClientExe) {
        return
    }

    if (-not (Test-Path $ClientExe)) {
        Write-Host ("Warning: UniFileHub client executable not found: {0}" -f $ClientExe)
        return
    }

    $clientFullPath = (Resolve-Path $ClientExe).Path
    $existing = Get-CimInstance Win32_Process |
        Where-Object { $_.ExecutablePath -and $_.ExecutablePath -ieq $clientFullPath } |
        Select-Object -First 1

    if ($existing) {
        Write-Host ("UniFileHub client is already running. PID: {0}" -f $existing.ProcessId)
        return
    }

    Write-Host ("Starting UniFileHub client: {0}" -f $clientFullPath)
    Start-Process -FilePath $clientFullPath -WorkingDirectory (Split-Path $clientFullPath -Parent) | Out-Null
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "Cleaning stale UniFileHub services..."
& (Join-Path $PSScriptRoot "win_stop_all_silent.ps1") -SkipMysql -Quiet

Start-MysqlService

Write-Host "Starting Python services..."
foreach ($service in $Services) {
    Start-PythonService $service
}

Start-UniFileHubClient

Write-Host ""
Write-Host ("All available services have been started. Logs: {0}" -f $LogDir)
