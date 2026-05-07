param(
    [Parameter(Mandatory=$true)]
    [string]$Workspace,

    [switch]$BuildFirst
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

# ---- Find UV4.exe ----
$uv4Path = Get-ConfigValue $configFile "uv4_path"
if (!$uv4Path) {
    $uv4Path = (Get-Command "UV4.exe" -ErrorAction SilentlyContinue).Source
}
if (!$uv4Path) {
    $regPath = (Get-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\Keil\Products\MDK" -Name "Path" -ErrorAction SilentlyContinue).Path
    if (!$regPath) { $regPath = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Keil\Products\MDK" -Name "Path" -ErrorAction SilentlyContinue).Path }
    if ($regPath) {
        # Try standard layout: <regPath>\UV4\UV4.exe
        $candidate = Join-Path $regPath "UV4\UV4.exe"
        if (Test-Path $candidate) { $uv4Path = $candidate }
        if (!$uv4Path) {
            # Try alternative layout: UV4 is sibling of the regPath directory
            $parent = Split-Path $regPath -Parent
            if ($parent) {
                $candidate = Join-Path $parent "UV4\UV4.exe"
                if (Test-Path $candidate) { $uv4Path = $candidate }
            }
        }
        if (!$uv4Path) {
            # Fallback: search under the Keil install root
            $keilRoot = Split-Path $regPath -Parent
            if (!$keilRoot) { $keilRoot = $regPath }
            $candidate = Get-ChildItem -Path $keilRoot -Filter "UV4.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($candidate) { $uv4Path = $candidate.FullName }
        }
    }
}
if (!$uv4Path -or !(Test-Path $uv4Path)) {
    Write-Error "UV4.exe not found. Check Keil MDK installation."
    exit 99
}

# ---- Find project ----
$projectPath = Get-ConfigValue $configFile "project_path"
if (!$projectPath) {
    $proj = Get-ChildItem -Recurse -Filter "*.uvprojx" -File | Select-Object -First 1
    if (!$proj) { $proj = Get-ChildItem -Recurse -Filter "*.uvproj" -File | Select-Object -First 1 }
    if ($proj) { $projectPath = $proj.FullName }
}
if (!$projectPath) {
    Write-Error "Keil project file (.uvprojx or .uvproj) not found in workspace."
    exit 98
}

# ---- Save config ----
@"
[keil]
uv4_path = $uv4Path
project_path = $projectPath
"@ | Out-File -FilePath $configFile -Encoding utf8 -Force

# ---- Optional: Build first ----
if ($BuildFirst) {
    Write-Output "Step 1/2: Building..."
    $buildLog = Join-Path $Workspace "build_log.txt"
    $proc = Start-Process -FilePath $uv4Path `
        -ArgumentList @('-b', $projectPath, '-o', $buildLog) `
        -Wait -PassThru -WindowStyle Hidden

    $buildExit = $proc.ExitCode
    $buildErrors = 0
    if (Test-Path $buildLog) {
        $log = Get-Content $buildLog -Raw
        if ($log -match '(\d+)\s+Error\(s\)') { $buildErrors = [int]$matches[1] }
    }

    Write-Output "Build ExitCode: $buildExit, Errors: $buildErrors"

    if ($buildExit -ge 2) {
        Write-Error "Build failed with $buildErrors error(s). Aborting burn."
        if (Test-Path $buildLog) {
            Get-Content $buildLog | Select-Object -Last 40
        }
        exit $buildExit
    }
    Write-Output "Build OK, proceeding to burn..."
    Write-Output ""
}

# ---- Burn ----
$logFile = Join-Path $Workspace "burn_log.txt"
Write-Output "Burning..."
Write-Output "  UV4   : $uv4Path"
Write-Output "  Project: $projectPath"

$proc = Start-Process -FilePath $uv4Path `
    -ArgumentList @('-f', $projectPath, '-o', $logFile) `
    -Wait -PassThru -WindowStyle Hidden

$exitCode = $proc.ExitCode

# ---- Check result ----
$success = $false
if (Test-Path $logFile) {
    $logContent = Get-Content $logFile -Raw
    if ($logContent -match 'Verify\s+OK' -or $logContent -match 'Download\s+Complete' -or $logContent -match 'Flash Load finished') {
        $success = $true
    }
    if ($logContent -match 'Error:\s*Flash Download failed' -or $logContent -match 'No Algorithm found' -or $logContent -match 'Cannot Load Flash Programming Algorithm') {
        $success = $false
    }
}

# ---- Summary ----
Write-Output ""
Write-Output "=== Burn Result ==="
Write-Output "ExitCode: $exitCode"
Write-Output "Success : $(if ($success) { 'YES' } else { 'UNKNOWN/FAILED' })"
Write-Output "Log     : $logFile"
Write-Output "==================="

# ---- Output log tail ----
if (Test-Path $logFile) {
    Write-Output ""
    Write-Output "=== Burn Log (last 40 lines) ==="
    Get-Content $logFile | Select-Object -Last 40
}

if (!$success -and $exitCode -ne 0) {
    exit $exitCode
}
exit 0
