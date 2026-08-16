# ESP-IDF Project Fast Compile
# Author: lichunjiang
# Description: Auto-detect ESP-IDF, recover environment from build cache, and run idf.py build.

param(
    [Parameter(Mandatory=$true)]
    [string]$Workspace
)

$ErrorActionPreference = "Stop"
Set-Location $Workspace

# ---- Ensure .ai-output directory ----
$configDir = Join-Path $Workspace ".ai-output"
$configFile = Join-Path $configDir "esp_compile.ini"
$logFile = Join-Path $configDir "esp_build.log"
$errFile = Join-Path $configDir "esp_build.err"
if (!(Test-Path $configDir)) { New-Item -ItemType Directory -Path $configDir -Force | Out-Null }

function Get-ConfigValue($file, $key) {
    if (!(Test-Path $file)) { return $null }
    $content = Get-Content $file -Raw -ErrorAction SilentlyContinue
    if (!$content) { return $null }
    $m = [regex]::Match($content, "(?m)^$key\s*=\s*(.+)$")
    if ($m.Success) { return $m.Groups[1].Value.Trim() }
    return $null
}

function Set-ConfigValue($file, $key, $value) {
    $content = ""
    if (Test-Path $file) { $content = Get-Content $file -Raw -ErrorAction SilentlyContinue }
    if (!$content) { $content = "[esp]`r`n" }
    $pattern = "(?m)^$key\s*=\s*.+$"
    $line = "$key = $value"
    if ($content -match $pattern) {
        $content = $content -replace $pattern, $line
    } else {
        $content = $content.TrimEnd() + "`r`n$line`r`n"
    }
    $content | Out-File -FilePath $file -Encoding utf8 -Force
}

function Get-CacheValue($file, $key) {
    if (!(Test-Path $file)) { return $null }
    foreach ($line in Get-Content $file -ErrorAction SilentlyContinue) {
        if ($line -match "^$key\s*:\s*[^=]+=\s*(.+)$") {
            return $matches[1].Trim()
        }
        if ($line -match "^$key\s*=\s*(.+)$") {
            return $matches[1].Trim()
        }
    }
    return $null
}

function Get-Directory($path) {
    if (!$path) { return $null }
    try { return Split-Path $path -Parent } catch { return $null }
}

function Test-EspIdf($path) {
    if (!$path) { return $false }
    return (Test-Path (Join-Path $path "tools\idf.py")) -and
           (Test-Path (Join-Path $path "tools\idf_tools.py")) -and
           (Test-Path (Join-Path $path "export.ps1"))
}

function Find-ToolDir($path) {
    if (!$path) { return $null }
    $dir = Get-Directory $path
    while ($dir) {
        if (Test-Path (Join-Path $dir "bin")) { return $dir }
        $parent = Get-Directory $dir
        if ($parent -eq $dir) { break }
        $dir = $parent
    }
    return $null
}

function Find-Executable($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Read-JsonIdfPath($file) {
    if (!(Test-Path $file)) { return $null }
    try {
        $json = Get-Content $file -Raw | ConvertFrom-Json -ErrorAction Stop
        if ($json.idf_path) { return $json.idf_path }
    } catch { return $null }
    return $null
}

function Find-CommonIdfPath() {
    $candidates = @()
    # C:\Espressif\frameworks\*\esp-idf
    if (Test-Path "C:\Espressif\frameworks") {
        $candidates += Get-ChildItem -Path "C:\Espressif\frameworks" -Directory | ForEach-Object {
            Join-Path $_.FullName "esp-idf"
        }
    }
    # C:\esp\v*\esp-idf
    if (Test-Path "C:\esp") {
        $candidates += Get-ChildItem -Path "C:\esp" -Directory | ForEach-Object {
            Join-Path $_.FullName "esp-idf"
        }
    }
    # User profile .espressif
    $espressif = Join-Path $env:USERPROFILE ".espressif"
    if (Test-Path $espressif) {
        $candidates += Get-ChildItem -Path $espressif -Directory -Recurse -Filter "esp-idf" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    }
    foreach ($c in $candidates) {
        if (Test-EspIdf $c) { return $c }
    }
    return $null
}

# ============================================================
# 1. Verify ESP-IDF project
# ============================================================
if (!(Test-Path "CMakeLists.txt") -or !(Test-Path "sdkconfig")) {
    Write-Error "Current workspace is not an ESP-IDF project (CMakeLists.txt or sdkconfig missing)."
    exit 98
}

# ============================================================
# 2. Find ESP-IDF path
# ============================================================
$idfPath = Get-ConfigValue $configFile "idf_path"
if (!(Test-EspIdf $idfPath)) {
    $idfPath = Read-JsonIdfPath "build\project_description.json"
}
if (!(Test-EspIdf $idfPath)) {
    $idfPath = $env:IDF_PATH
}
if (!(Test-EspIdf $idfPath)) {
    $idfPath = Find-CommonIdfPath
}
if (!(Test-EspIdf $idfPath)) {
    Write-Error "ESP-IDF not found. Please install ESP-IDF or set IDF_PATH."
    exit 99
}
$idfPath = Resolve-Path $idfPath | Select-Object -ExpandProperty Path
Set-ConfigValue $configFile "idf_path" $idfPath
Write-Output "ESP-IDF path: $idfPath"

$idfPy = Join-Path $idfPath "tools\idf.py"
$exportPs1 = Join-Path $idfPath "export.ps1"

# ============================================================
# 3. Prepare Windows environment
# ============================================================
if (-not $env:PROCESSOR_ARCHITECTURE) {
    $runtimeArch = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
    $env:PROCESSOR_ARCHITECTURE = switch ($runtimeArch) {
        'X64'   { 'AMD64' }
        'X86'   { 'x86' }
        'Arm64' { 'ARM64' }
        default { $runtimeArch }
    }
}
if (-not $env:PROCESSOR_ARCHITEW6432 -and $env:PROCESSOR_ARCHITECTURE -eq 'AMD64') {
    $env:PROCESSOR_ARCHITEW6432 = 'AMD64'
}
if (-not $env:OS) { $env:OS = 'Windows_NT' }

# Clear MSYS/Mingw markers that confuse ESP-IDF detection
@('MSYSTEM','MSYS','MINGW_CHOST','MINGW_PACKAGE_PREFIX','MINGW_PREFIX',
  'MSYSTEM_CARCH','MSYSTEM_PREFIX','MSYSTEM_CHOST') | ForEach-Object {
    Remove-Item Env:\$_ -ErrorAction SilentlyContinue
}

# Use a controlled temp directory
$tmpDir = Join-Path $configDir "tmp"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
$env:TMPDIR = $tmpDir
$env:TEMP = $tmpDir
$env:TMP = $tmpDir

# Force UTF-8 to avoid GBK/UnicodeEncodeError
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
$env:PYTHONIOENCODING = 'utf-8'

# ============================================================
# 4. Try normal export.ps1 activation
# ============================================================
$useFallback = $true
$pythonExe = $null

try {
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -ErrorAction Stop | Out-Null
    & $exportPs1 *>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $idfPyCmd = Get-Command idf.py -ErrorAction SilentlyContinue
        if ($idfPyCmd) {
            $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
            $useFallback = $false
            Write-Output "ESP-IDF activated via export.ps1"
        }
    }
} catch {
    Write-Output "export.ps1 activation failed, switching to fallback environment recovery."
}

# ============================================================
# 5. Fallback: recover environment from build cache
# ============================================================
if ($useFallback) {
    Write-Output "Using fallback environment recovery from build/CMakeCache.txt"

    $cacheFile = "build\CMakeCache.txt"
    if (!(Test-Path $cacheFile)) {
        Write-Error "No build cache found. Please run idf.py set-target or idf.py build once manually."
        exit 97
    }

    $pythonExe = Get-CacheValue $cacheFile "PYTHON"
    $cmakeExe = Get-CacheValue $cacheFile "CMAKE_COMMAND"
    $ninjaExe = Get-CacheValue $cacheFile "CMAKE_MAKE_PROGRAM"
    $gitExe = Get-CacheValue $cacheFile "GIT_EXECUTABLE"
    $compilerAr = Get-CacheValue $cacheFile "CMAKE_C_COMPILER_AR"
    $compiler = Get-CacheValue $cacheFile "CMAKE_C_COMPILER"

    $toolchainBin = $null
    if ($compilerAr) { $toolchainBin = Join-Path (Find-ToolDir $compilerAr) "bin" }
    if (!$toolchainBin -and $compiler) { $toolchainBin = Get-Directory $compiler }

    $pythonScripts = $null
    if ($pythonExe) { $pythonScripts = Join-Path (Get-Directory $pythonExe) "Scripts" }

    $cmakeDir = Get-Directory $cmakeExe
    $ninjaDir = Get-Directory $ninjaExe
    $gitDir = Get-Directory $gitExe

    $env:IDF_PATH = $idfPath
    if ($pythonExe -and (Test-Path $pythonExe)) {
        $venv = Get-Directory (Get-Directory $pythonExe)
        $env:IDF_PYTHON_ENV_PATH = $venv
    }

    $newPaths = @($pythonScripts, $pythonDir, $cmakeDir, $ninjaDir, $toolchainBin, $gitDir) | Where-Object { $_ -and (Test-Path $_) }
    $env:PATH = ($newPaths + $env:PATH) -join ';'

    if (!$pythonExe -or !(Test-Path $pythonExe)) {
        Write-Error "Python from build cache not found: $pythonExe"
        exit 96
    }
}

if (!$pythonExe) {
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (!$pythonExe -or !(Test-Path $pythonExe)) {
    Write-Error "Python interpreter not found."
    exit 95
}

Write-Output "Python: $pythonExe"

# Verify Python platform
$platformCheck = & $pythonExe -c "import platform; print(platform.system(), repr(platform.machine()))" 2>&1
Write-Output "Platform check: $platformCheck"

# ============================================================
# 6. Run idf.py build
# ============================================================
Write-Output ""
Write-Output "Starting idf.py build..."

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = "`"$idfPy`" build"
$psi.WorkingDirectory = $Workspace
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
$psi.CreateNoWindow = $true

$proc = [System.Diagnostics.Process]::Start($psi)
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
$exitCode = $proc.ExitCode

$stdout | Out-File -Encoding utf8 -FilePath $logFile -Force
$stderr | Out-File -Encoding utf8 -FilePath $errFile -Force

$combined = $stdout + "`r`n" + $stderr

# ============================================================
# 7. Analyze result
# ============================================================
$buildSuccess = ($exitCode -eq 0) -or ($combined -match "Project build complete")

$appBin = $null
$appElf = $null
$projectName = $null
$jsonFile = "build\project_description.json"
if (Test-Path $jsonFile) {
    try {
        $json = Get-Content $jsonFile -Raw | ConvertFrom-Json -ErrorAction Stop
        $projectName = $json.project_name
        if ($json.app_bin) { $appBin = Join-Path "build" $json.app_bin }
        if ($json.app_elf) { $appElf = Join-Path "build" $json.app_elf }
    } catch {}
}
if (!$appBin) {
    $bin = Get-ChildItem -Path "build" -Filter "*.bin" -File | Select-Object -First 1
    if ($bin) { $appBin = $bin.FullName }
}
if (!$appElf) {
    $elf = Get-ChildItem -Path "build" -Filter "*.elf" -File | Select-Object -First 1
    if ($elf) { $appElf = $elf.FullName }
}

$appSize = 0
$appSizeHex = "0x0"
$bootloaderSizeHex = "0x0"
$bootloaderFree = "0x0"
$appPartitionSize = "0x0"
$appPartitionFree = "0x0"

if ($buildSuccess -and $appBin -and (Test-Path $appBin)) {
    $appSize = (Get-Item $appBin).Length
    $appSizeHex = "0x" + $appSize.ToString("X")
}

if ($combined -match "Bootloader binary size\s+0x([0-9a-fA-F]+) bytes\.\s+(0x[0-9a-fA-F]+) bytes\s+\((\d+)%\) free") {
    $bootloaderSizeHex = "0x$($matches[1])"
    $bootloaderFree = $matches[2]
}
if ($combined -match "binary size\s+0x([0-9a-fA-F]+) bytes\.\s+Smallest app partition is\s+(0x[0-9a-fA-F]+) bytes\.\s+(0x[0-9a-fA-F]+) bytes\s+\((\d+)%\) free") {
    $appSizeHex = "0x$($matches[1])"
    $appPartitionSize = $matches[2]
    $appPartitionFree = $matches[3]
}

# ============================================================
# 8. Summary
# ============================================================
Write-Output ""
Write-Output "=== Build Result ==="
Write-Output "ExitCode        : $exitCode"
Write-Output "BuildStatus     : $(if ($buildSuccess) { 'SUCCESS' } else { 'FAILED' })"
if ($projectName) { Write-Output "ProjectName     : $projectName" }
if ($appBin) { Write-Output "AppBinary       : $appBin" }
if ($appSize -gt 0) { Write-Output "AppBinarySize   : $appSize bytes ($appSizeHex)" }
if ($appElf) { Write-Output "AppElf          : $appElf" }
if ($bootloaderSizeHex -ne "0x0") { Write-Output "BootloaderSize  : $bootloaderSizeHex, Free: $bootloaderFree" }
if ($appPartitionSize -ne "0x0") { Write-Output "AppPartition    : $appPartitionSize, Free: $appPartitionFree" }
Write-Output "LogFile         : $logFile"
Write-Output "ErrFile         : $errFile"
Write-Output "ConfigFile      : $configFile"
Write-Output "===================="

# Output log tail
if (Test-Path $logFile) {
    Write-Output ""
    Write-Output "=== Build Log (last 80 lines) ==="
    Get-Content $logFile | Select-Object -Last 80
}
if (Test-Path $errFile) {
    $errContent = Get-Content $errFile -Raw
    if ($errContent.Trim()) {
        Write-Output ""
        Write-Output "=== Stderr (last 20 lines) ==="
        Get-Content $errFile | Select-Object -Last 20
    }
}

if ($buildSuccess) {
    exit 0
} else {
    exit $exitCode
}
