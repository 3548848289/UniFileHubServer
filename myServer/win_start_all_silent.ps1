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

function Test-TcpPort($HostName, $Port, $TimeoutMs) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        if ($async.AsyncWaitHandle.WaitOne($TimeoutMs)) {
            $client.EndConnect($async)
            return $true
        }

        return $false
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Get-MysqlService {
    $service = Get-Service -Name $MysqlService -ErrorAction SilentlyContinue
    if (-not $service) {
        throw "MySQL service '$MysqlService' was not found. Set UNIFILEHUB_MYSQL_SERVICE if your service name is different."
    }

    $startType = $null
    try { $startType = $service.StartType } catch { }
    if ($startType -eq "Disabled") {
        throw "MySQL service '$MysqlService' is disabled. Run: Set-Service '$MysqlService' -StartupType Manual"
    }

    return $service
}

function Wait-ServiceStopped($Service, $TimeoutSeconds) {
    try {
        $Service.WaitForStatus("Stopped", [TimeSpan]::FromSeconds($TimeoutSeconds))
        return $true
    } catch {
        return $false
    }
}

# Issues the start request without blocking, so the cleanup pass below overlaps with MySQL booting.
function Start-MysqlKickoff($Service) {
    if ($Service.Status -in @("Running", "StartPending")) {
        return $Service
    }

    if ($Service.Status -eq "StopPending") {
        Write-Host "MySQL service is still stopping; waiting up to 60 seconds for it to settle..."
        if (-not (Wait-ServiceStopped $Service 60)) {
            Write-Host "MySQL is stuck stopping, sending a stop request..."
            try {
                $Service.Stop()
            } catch {
                Write-Host ("MySQL stop request failed: {0}" -f $_.Exception.Message)
            }

            if (-not (Wait-ServiceStopped $Service 15)) {
                Write-Host "Warning: MySQL did not stop cleanly, force-killing mysqld.exe..."
                & taskkill.exe /IM mysqld.exe /T /F *>$null
                Start-Sleep -Seconds 3
            }
        }

        $Service.Refresh()
    }

    Write-Host ("Requesting start of MySQL service {0}..." -f $MysqlService)
    try {
        $Service.Start()
    } catch {
        Write-Host ("MySQL start request failed (will be retried): {0}" -f $_.Exception.Message)
    }

    return $Service
}

function Wait-MysqlReady($Service) {
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        if ($attempt -gt 1) {
            Write-Host ("Retrying MySQL start (attempt {0} of 2)..." -f $attempt)
            try {
                $Service.Start()
            } catch {
                Write-Host ("MySQL start request failed: {0}" -f $_.Exception.Message)
            }
        }

        if ($Service.Status -ne "Running") {
            try {
                $Service.WaitForStatus("Running", [TimeSpan]::FromSeconds(60))
            } catch {
                $Service.Refresh()
                Write-Host ("MySQL did not reach Running within 60 seconds (status: {0})." -f $Service.Status)
                continue
            }
        }

        # Wait for TCP readiness, watching for mysqld crashing back to Stopped.
        $crashed = $false
        $deadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $deadline) {
            $Service.Refresh()
            if ($Service.Status -eq "Stopped") {
                Write-Host "MySQL exited while starting (mysqld crashed?)."
                $crashed = $true
                break
            }

            if (Test-TcpPort $MysqlHost $MysqlPort 400) {
                Write-Host "MySQL is ready."
                return
            }

            Start-Sleep -Milliseconds 500
        }

        # Service is running but the port never opened; retrying will not help.
        if (-not $crashed) {
            break
        }
    }

    $Service.Refresh()
    $portHint = ""
    $listener = Get-NetTCPConnection -LocalPort $MysqlPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        $owner = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        if ($owner) {
            $portHint = (" Port {0} is currently held by PID {1} ({2})." -f $MysqlPort, $owner.Id, $owner.ProcessName)
        }
    }

    throw ("MySQL on {0}:{1} did not become ready (service status: {2}).{3} Check the MySQL error log and Windows Event Viewer." -f $MysqlHost, $MysqlPort, $Service.Status, $portHint)
}

function Resolve-PythonExe {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        throw "python.exe was not found in PATH."
    }

    return $python.Source
}

# Launches every service first, then polls all ports together, so one slow
# service no longer delays the startup of the others.
function Start-PythonServices($PythonExe) {
    $launched = @()
    foreach ($service in $Services) {
        $workDir = Join-Path $RootDir $service.Dir
        $scriptPath = Join-Path $workDir $service.Script
        if (-not (Test-Path $scriptPath)) {
            Write-Host ("Skipping {0}: script not found: {1}" -f $service.Name, $scriptPath)
            continue
        }

        $stdout = Join-Path $LogDir ($service.Name + ".out.log")
        $stderr = Join-Path $LogDir ($service.Name + ".err.log")
        $protocol = if ($service.Protocol) { $service.Protocol } else { "TCP" }

        Write-Host ("Starting {0} on {1} port {2}..." -f $service.Name, $protocol, $service.Port)
        try {
            $process = Start-Process `
                -FilePath $PythonExe `
                -ArgumentList @($scriptPath) `
                -WorkingDirectory $workDir `
                -WindowStyle Hidden `
                -RedirectStandardOutput $stdout `
                -RedirectStandardError $stderr `
                -PassThru
        } catch {
            Write-Host ("Failed to launch {0}: {1}" -f $service.Name, $_.Exception.Message)
            continue
        }

        $launched += [pscustomobject]@{
            Name = $service.Name
            Protocol = $protocol
            Port = $service.Port
            ProcessId = $process.Id
            Stdout = $stdout
            Stderr = $stderr
        }
    }

    $pending = @($launched)
    $deadline = (Get-Date).AddSeconds(30)
    while ($pending.Count -gt 0 -and (Get-Date) -lt $deadline) {
        $remaining = @()
        foreach ($item in $pending) {
            if ($item.Protocol -eq "UDP") {
                $isListening = [bool](Get-NetUDPEndpoint -LocalPort $item.Port -ErrorAction SilentlyContinue |
                    Select-Object -First 1)
            } else {
                $isListening = Test-TcpPort "127.0.0.1" $item.Port 400
            }

            if ($isListening) {
                Write-Host ("{0} is listening on {1} port {2}. PID: {3}" -f $item.Name, $item.Protocol, $item.Port, $item.ProcessId)
                continue
            }

            if (-not (Get-Process -Id $item.ProcessId -ErrorAction SilentlyContinue)) {
                Write-Host ("Warning: {0} (PID {1}) exited without opening port {2}. Check {3} and {4}." -f $item.Name, $item.ProcessId, $item.Port, $item.Stdout, $item.Stderr)
                continue
            }

            $remaining += $item
        }

        $pending = $remaining
        if ($pending.Count -gt 0) {
            Start-Sleep -Milliseconds 400
        }
    }

    foreach ($item in $pending) {
        Write-Host ("Warning: {0} did not open {1} port {2} within 30 seconds. Check {3} and {4}." -f $item.Name, $item.Protocol, $item.Port, $item.Stdout, $item.Stderr)
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
    $clientName = [System.IO.Path]::GetFileName($clientFullPath)

    $existing = Get-CimInstance Win32_Process -Filter ("Name='{0}'" -f $clientName.Replace("'", "''")) -ErrorAction SilentlyContinue |
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

$mysqlService = Get-MysqlService
$mysqlService = Start-MysqlKickoff $mysqlService

Write-Host "Cleaning stale UniFileHub services..."
& (Join-Path $PSScriptRoot "win_stop_all_silent.ps1") -SkipMysql -Quiet

Wait-MysqlReady $mysqlService

$pythonExe = Resolve-PythonExe

Write-Host "Starting Python services..."
Start-PythonServices $pythonExe

Start-UniFileHubClient

Write-Host ""
Write-Host ("All available services have been started. Logs: {0}" -f $LogDir)
