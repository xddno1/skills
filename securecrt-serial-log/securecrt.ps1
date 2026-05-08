param(
    [Parameter(Mandatory=$true)]
    [string]$Workspace,

    [ValidateSet("open", "logs")]
    [string]$Action = "open",

    [string]$Com = "",
    [string]$Baud = "115200",
    [int]$LogCount = 5
)

$ErrorActionPreference = "Stop"
Set-Location $Workspace

# ---- Ensure .ai-output directory ----
$configDir = Join-Path $Workspace ".ai-output"
$configFile = Join-Path $configDir "config.ini"
if (!(Test-Path $configDir)) { New-Item -ItemType Directory -Path $configDir -Force | Out-Null }

function Get-ConfigValue($file, $key) {
    if (!(Test-Path $file)) { return $null }
    $content = Get-Content $file -Raw
    if (!$content) { return $null }
    $m = [regex]::Match($content, "$key\s*=\s*(.+)")
    if ($m.Success) { return $m.Groups[1].Value.Trim() }
    return $null
}

function Save-ConfigSection($file, $section, $kv) {
    $existing = ""
    if (Test-Path $file) { $existing = Get-Content $file -Raw }
    if (!$existing) { $existing = "" }

    # Remove old section if any
    $pattern = "(?ms)^\[$section\].*?(?=^\[|\Z)"
    $existing = [regex]::Replace($existing, $pattern, "")
    $existing = $existing.TrimEnd()

    $body = "[$section]`r`n"
    foreach ($k in $kv.Keys) { $body += "$k = $($kv[$k])`r`n" }

    if ($existing) { $existing = $existing + "`r`n`r`n" + $body } else { $existing = $body }
    $existing | Out-File -FilePath $file -Encoding utf8 -Force
}

# ---- Find SecureCRT.exe ----
function Find-SecureCRT {
    $p = Get-ConfigValue $configFile "securecrt_path"
    if ($p -and (Test-Path $p)) { return $p }

    $cmd = (Get-Command "SecureCRT.exe" -ErrorAction SilentlyContinue).Source
    if ($cmd) { return $cmd }

    $regDir = (Get-ItemProperty -Path "HKLM:\SOFTWARE\VanDyke\SecureCRT\Install" -Name "Main Directory" -ErrorAction SilentlyContinue)."Main Directory"
    if (!$regDir) {
        $regDir = (Get-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\VanDyke\SecureCRT\Install" -Name "Main Directory" -ErrorAction SilentlyContinue)."Main Directory"
    }
    if ($regDir) {
        $candidate = Join-Path $regDir "SecureCRT.exe"
        if (Test-Path $candidate) { return $candidate }
    }

    foreach ($p in @("D:\software\CRT\SecureCRT.exe", "C:\Program Files\VanDyke Software\SecureCRT\SecureCRT.exe", "C:\Program Files (x86)\VanDyke Software\SecureCRT\SecureCRT.exe")) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

# ---- Find log directory ----
function Find-LogDir($crtPath) {
    $d = Get-ConfigValue $configFile "logdir"
    if ($d -and (Test-Path $d)) { return $d }

    # Look in CRT session config
    $sessionRoots = @(
        "$env:APPDATA\VanDyke\Config\Sessions",
        "D:\WLPC\AppData\Roaming\VanDyke\Config\Sessions",
        "$env:USERPROFILE\AppData\Roaming\VanDyke\Config\Sessions"
    )
    foreach ($root in $sessionRoots) {
        if (!(Test-Path $root)) { continue }
        $iniFiles = Get-ChildItem -Path $root -Filter "*.ini" -Recurse -ErrorAction SilentlyContinue
        foreach ($ini in $iniFiles) {
            $content = Get-Content $ini.FullName -Raw -ErrorAction SilentlyContinue
            if (!$content) { continue }
            $m = [regex]::Match($content, 'Log Filename V2"\s*=\s*(.+)')
            if ($m.Success) {
                $logTemplate = $m.Groups[1].Value.Trim()
                # Extract directory before %S or other tokens
                $logDir = [regex]::Replace($logTemplate, '\\[^\\]*[%].*$', '')
                if ($logDir -and (Test-Path $logDir)) { return $logDir }
            }
        }
    }

    if (Test-Path "D:\log") { return "D:\log" }
    return $null
}

# ===== ACTION: open =====
if ($Action -eq "open") {
    $crtPath = Find-SecureCRT
    if (!$crtPath) {
        Write-Error "SecureCRT.exe not found. Check installation or set securecrt_path in $configFile"
        exit 99
    }

    if (!$Com) { $Com = Get-ConfigValue $configFile "com" }
    if (!$Com) {
        Write-Error "COM port not specified. Pass -Com COMx or set 'com' in $configFile"
        exit 98
    }

    $cfgBaud = Get-ConfigValue $configFile "baud"
    if ($cfgBaud) { $Baud = $cfgBaud }

    Save-ConfigSection $configFile "securecrt" @{
        "securecrt_path" = $crtPath
        "com" = $Com
        "baud" = $Baud
    }

    Write-Output "Opening SecureCRT..."
    Write-Output "  CRT  : $crtPath"
    Write-Output "  COM  : $Com"
    Write-Output "  Baud : $Baud"

    Start-Process -FilePath $crtPath -ArgumentList @('/SERIAL', $Com, '/BAUD', $Baud) | Out-Null

    Write-Output ""
    Write-Output "=== SecureCRT launched ==="
    exit 0
}

# ===== ACTION: logs =====
if ($Action -eq "logs") {
    $crtPath = Find-SecureCRT
    $logDir = Find-LogDir $crtPath
    if (!$logDir) {
        Write-Error "Log directory not found. Set 'logdir' in $configFile"
        exit 97
    }

    # Persist logdir
    if ($crtPath) {
        Save-ConfigSection $configFile "securecrt" @{
            "securecrt_path" = $crtPath
            "logdir" = $logDir
        }
    }

    Write-Output "LogDir: $logDir"
    Write-Output ""
    Write-Output "=== Latest $LogCount log files ==="
    $files = Get-ChildItem -Path $logDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First $LogCount
    if (!$files) {
        Write-Output "(no log files found)"
        exit 0
    }
    foreach ($f in $files) {
        $size = "{0,8} B" -f $f.Length
        Write-Output ("{0}  {1}  {2}" -f $f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"), $size, $f.Name)
    }
    Write-Output ""
    Write-Output "Latest: $($files[0].FullName)"
    exit 0
}
