param(
    [switch]$SkipMysql,
    [switch]$Quiet,
    [int]$MaxRounds = 5
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

# One snapshot per round, shared by script matching and port-owner lookups
# (the old version re-enumerated all processes once per script pattern).
$script:ProcessCache = @{}
$script:ListenersByPort = @{}
$script:UdpByPort = @{}

function Update-RoundSnapshot {
    $script:ProcessCache = @{}
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
        $script:ProcessCache[[int]$_.ProcessId] = $_
    }

    $script:ListenersByPort = @{}
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
        if ($Ports -contains $_.LocalPort) {
            if (-not $script:ListenersByPort.ContainsKey($_.LocalPort)) {
                $script:ListenersByPort[$_.LocalPort] = @()
            }
            $script:ListenersByPort[$_.LocalPort] += $_
        }
    }

    $script:UdpByPort = @{}
    Get-NetUDPEndpoint -ErrorAction SilentlyContinue | ForEach-Object {
        if ($UdpPorts -contains $_.LocalPort) {
            if (-not $script:UdpByPort.ContainsKey($_.LocalPort)) {
                $script:UdpByPort[$_.LocalPort] = @()
            }
            $script:UdpByPort[$_.LocalPort] += $_
        }
    }
}

function Get-CachedProcess($ProcessId) {
    if (-not $ProcessId) {
        return $null
    }

    $processId = [int]$ProcessId
    if ($script:ProcessCache.ContainsKey($processId)) {
        return $script:ProcessCache[$processId]
    }

    return Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $processId) -ErrorAction SilentlyContinue
}

function Invoke-StopRound {
    $stoppedCount = 0

    foreach ($scriptPath in $ServiceScripts) {
        $scriptName = Split-Path $scriptPath -Leaf
        $scriptPathPattern = "*" + $scriptPath + "*"
        $scriptDirPattern = "*UniFileHub-Server*" + $scriptName + "*"

        foreach ($candidate in $script:ProcessCache.Values) {
            if ($candidate.CommandLine -and
                ($candidate.CommandLine -like $scriptPathPattern -or $candidate.CommandLine -like $scriptDirPattern)) {
                Stop-Pid $candidate.ProcessId ("matched command line for {0}" -f $scriptPath)
                $stoppedCount++
            }
        }
    }

    foreach ($port in $Ports) {
        try {
            foreach ($connection in $script:ListenersByPort[$port]) {
                $owner = Get-CachedProcess $connection.OwningProcess
                if (-not $owner) {
                    Stop-Pid $connection.OwningProcess ("listening on port {0}" -f $port)
                    $stoppedCount++
                    continue
                }

                $parent = Get-CachedProcess $owner.ParentProcessId
                $parentName = if ($parent) { [System.IO.Path]::GetFileNameWithoutExtension($parent.Name) } else { "" }
                if ($parent -and $parentName -in @("python", "pythonw", "py")) {
                    Stop-Pid $parent.ProcessId ("parent of process listening on port {0}" -f $port)
                } else {
                    Stop-Pid $owner.ProcessId ("listening on port {0}" -f $port)
                }
                $stoppedCount++
            }
        } catch {
            Write-Status ("Unable to inspect port {0}: {1}" -f $port, $_.Exception.Message)
        }
    }

    foreach ($port in $UdpPorts) {
        try {
            foreach ($udpConnection in $script:UdpByPort[$port]) {
                Stop-Pid $udpConnection.OwningProcess ("listening on UDP port {0}" -f $port)
                $stoppedCount++
            }
        } catch {
            Write-Status ("Unable to inspect UDP port {0}: {1}" -f $port, $_.Exception.Message)
        }
    }

    return $stoppedCount
}

Write-Status "Stopping UniFileHub Python services..."

for ($round = 1; $round -le $MaxRounds; $round++) {
    Update-RoundSnapshot
    $stoppedCount = Invoke-StopRound

    if ($stoppedCount -eq 0) {
        break
    }

    Start-Sleep -Milliseconds 300
}

Start-Sleep -Milliseconds 500

$stillListening = @()
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    if ($Ports -contains $_.LocalPort -and $stillListening -notcontains $_.LocalPort) {
        $stillListening += $_.LocalPort
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
