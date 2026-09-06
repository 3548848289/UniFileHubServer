param(
    [switch]$SkipMysql,
    [switch]$Quiet
)

$ErrorActionPreference = "Continue"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$MysqlService = if ($env:UNIFILEHUB_MYSQL_SERVICE) { $env:UNIFILEHUB_MYSQL_SERVICE } else { "mysql8" }
$Ports = @(5000, 5001, 5002, 5005, 5006)
$UdpPorts = @(15000)
$ServiceScripts = @(
    Join-Path $RootDir "UserInfo\app.py"
    Join-Path $RootDir "SharedFile\app.py"
    Join-Path $RootDir "FIleHistory\app.py"
    Join-Path $RootDir "PersonalDrive\run.py"
    Join-Path $RootDir "ClipboardSync\app.py"
    Join-Path $RootDir "Discovery\app.py"
)

function Write-Status($Message) {
    if (-not $Quiet) {
        Write-Host $Message
    }
}

function Stop-Pid($ProcessId, $Reason) {
    if (-not $ProcessId -or $ProcessId -eq $PID) {
        return
    }

    try {
        $process = Get-Process -Id $ProcessId -ErrorAction Stop
        Write-Status ("Stopping PID {0} ({1}) - {2}" -f $ProcessId, $process.ProcessName, $Reason)
        & taskkill.exe /PID $ProcessId /T /F *>$null
    } catch {
        Write-Status ("PID {0} already stopped or cannot be stopped: {1}" -f $ProcessId, $_.Exception.Message)
    }
}

function Get-ProcessInfo($ProcessId) {
    if (-not $ProcessId) {
        return $null
    }

    Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $ProcessId) -ErrorAction SilentlyContinue
}

function Stop-PortOwner($Port) {
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $owner = Get-ProcessInfo $connection.OwningProcess
        if (-not $owner) {
            Stop-Pid $connection.OwningProcess ("listening on port {0}" -f $Port)
            continue
        }

        $parent = Get-ProcessInfo $owner.ParentProcessId
        $parentName = if ($parent) { [System.IO.Path]::GetFileNameWithoutExtension($parent.Name) } else { "" }
        if ($parent -and $parentName -in @("python", "pythonw", "py")) {
            Stop-Pid $parent.ProcessId ("parent of process listening on port {0}" -f $Port)
        } else {
            Stop-Pid $owner.ProcessId ("listening on port {0}" -f $Port)
        }
    }
}

function Stop-MatchedServiceScripts {
    foreach ($scriptPath in $ServiceScripts) {
        $scriptName = Split-Path $scriptPath -Leaf
        $scriptPathPattern = "*" + $scriptPath + "*"

        $matches = Get-CimInstance Win32_Process |
            Where-Object {
                $_.CommandLine -and
                (
                    $_.CommandLine -like $scriptPathPattern -or
                    $_.CommandLine -like ("*UniFileHub-Server*" + $scriptName + "*")
                )
            }

        foreach ($match in $matches) {
            Stop-Pid $match.ProcessId ("matched command line for {0}" -f $scriptPath)
        }
    }
}

Write-Status "Stopping UniFileHub Python services..."

for ($round = 1; $round -le 5; $round++) {
    Stop-MatchedServiceScripts

    foreach ($port in $Ports) {
        try {
            Stop-PortOwner $port
        } catch {
            Write-Status ("Unable to inspect port {0}: {1}" -f $port, $_.Exception.Message)
        }
    }

    foreach ($port in $UdpPorts) {
        try {
            $udpConnections = Get-NetUDPEndpoint -LocalPort $port -ErrorAction SilentlyContinue
            foreach ($udpConnection in $udpConnections) {
                Stop-Pid $udpConnection.OwningProcess ("listening on UDP port {0}" -f $port)
            }
        } catch {
            Write-Status ("Unable to inspect UDP port {0}: {1}" -f $port, $_.Exception.Message)
        }
    }

    Start-Sleep -Milliseconds 600
}

Start-Sleep -Milliseconds 800

$stillListening = @()
foreach ($port in $Ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        $stillListening += $port
    }
}

if ($stillListening.Count -gt 0) {
    Write-Status ("Warning: ports still listening after stop: {0}" -f ($stillListening -join ", "))
}

if (-not $SkipMysql -and $env:UNIFILEHUB_STOP_MYSQL -eq "1") {
    $service = Get-Service -Name $MysqlService -ErrorAction SilentlyContinue
    if ($service -and $service.Status -ne "Stopped") {
        Write-Status ("Stopping MySQL service {0}..." -f $MysqlService)
        try {
            Stop-Service -Name $MysqlService -ErrorAction Stop
            $service.WaitForStatus("Stopped", [TimeSpan]::FromSeconds(45))
            Write-Status "MySQL stopped."
        } catch {
            Write-Status ("Warning: failed to stop MySQL service {0}: {1}" -f $MysqlService, $_.Exception.Message)
        }
    }
} elseif (-not $SkipMysql) {
    Write-Status "Keeping MySQL running. Set UNIFILEHUB_STOP_MYSQL=1 if you want the stop script to stop it."
}

Write-Status "UniFileHub services stopped."
