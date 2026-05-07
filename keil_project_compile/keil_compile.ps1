param(
    [Parameter(Mandatory=$true)]
    [string]$Workspace
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

# ---- Find hex file path (from config) ----
$hexPath = Get-ConfigValue $configFile "hex_path"

# ---- Compile ----
$logFile = Join-Path $Workspace "build_log.txt"
Write-Output "Compiling..."
Write-Output "  UV4   : $uv4Path"
Write-Output "  Project: $projectPath"

$proc = Start-Process -FilePath $uv4Path `
    -ArgumentList @('-b', $projectPath, '-o', $logFile) `
    -Wait -PassThru -WindowStyle Hidden

$exitCode = $proc.ExitCode

# ---- Extract error/warning count from log ----
$errors = 0
$warnings = 0
if (Test-Path $logFile) {
    $logContent = Get-Content $logFile -Raw
    if ($logContent -match '(\d+)\s+Error\(s\)') { $errors = [int]$matches[1] }
    if ($logContent -match '(\d+)\s+Warning\(s\)') { $warnings = [int]$matches[1] }
}

# ---- Find hex file after successful build ----
if ($exitCode -lt 2 -and !$hexPath) {
    $projectDir = Split-Path $projectPath -Parent
    $hexFile = Get-ChildItem -Path $projectDir -Recurse -Filter "*.hex" -File | Select-Object -First 1
    if ($hexFile) {
        $hexPath = $hexFile.FullName
        if (Test-Path $configFile) {
            $cfg = Get-Content $configFile -Raw
            if (!$cfg) { $cfg = "" }
            $cfg += "`r`nhex_path = $hexPath"
            $cfg | Out-File -FilePath $configFile -Encoding utf8 -Force
        }
    }
}

# ---- Summary ----
Write-Output ""
Write-Output "=== Build Result ==="
Write-Output "ExitCode: $exitCode"
Write-Output "Errors  : $errors"
Write-Output "Warnings: $warnings"
if ($hexPath) { Write-Output "Hex     : $hexPath" }
Write-Output "Log     : $logFile"
Write-Output "===================="

# ---- Output log tail ----
if (Test-Path $logFile) {
    Write-Output ""
    Write-Output "=== Build Log (last 80 lines) ==="
    Get-Content $logFile | Select-Object -Last 80
}

exit $exitCode
