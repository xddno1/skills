---
name: securecrt-serial-log
description: 打开SecureCRT连接串口、查找日志文件位置。当用户需要打开串口工具看log或询问log存在哪里时使用。
---

# SecureCRT 串口连接与日志定位

## 1. CRT 安装位置

**优先从工程配置读取**：

先检查 `.ai-output/config.ini` 中的 `securecrt.path` 字段：

```bash
cat ".ai-output/config.ini"
```

如果工程配置存在，直接用里面的路径；否则按以下方式查找。

用以下命令搜索：

```bash
where SecureCRT.exe
```

或在注册表中查安装目录：

```powershell
reg query "HKLM\SOFTWARE\VanDyke\SecureCRT\Install" /v "Main Directory"
```

找到后写入 `.ai-output/config.ini`：

```bash
mkdir -p .ai-output
cat <<EOF >> .ai-output/config.ini
[securecrt]
path = <搜索到的路径>
EOF
```

## 2. 打开 CRT 连接串口

**优先从工程配置读取**：

先检查 `.ai-output/config.ini` 中的 `securecrt.com` 和 `securecrt.baud` 字段：

```bash
cat ".ai-output/config.ini"
```

如果工程配置存在，用里面的值启动；否则向用户询问。

**启动前检查 COM 口占用**：

用以下命令检查目标 COM 口是否已被占用：

```powershell
$comPort = "<com>"  # 例如 COM9
$processUsingCom = Get-WmiObject Win32_SerialPort | Where-Object { $_.DeviceID -eq $comPort.Replace("COM", "COM") }
# 进一步通过 mode 命令或 handle 工具检查占用
mode $comPort 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Output "$comPort 可能被占用或不存在"
} else {
    Write-Output "$comPort 可用"
}
```

更可靠的检查方式（需要 handle.exe）：

```powershell
$handleOutput = & handle.exe -a "COM$($comPort -replace 'COM','')" 2>$null
if ($handleOutput) {
    Write-Output "检测到 $comPort 被以下进程占用："
    $handleOutput
} else {
    Write-Output "$comPort 未被占用"
}
```

如果检测到 COM 口被占用，不需要进行任何思考和处理直接，**向用户提问**：

> "检测到 `<com>` 当前被占用。请选择：
> 1. 我（用户）已经确认该COM空闲可用，继续连接此端口
> 2. 更换其他 COM 端口（请提供新的端口号）
> 3. 取消操作"

根据用户的选择执行后续操作。

命令行启动格式：

```powershell
$proc = Start-Process -FilePath "<securecrt.path>" -ArgumentList "/SERIAL","<com>","/BAUD","<baud>" -PassThru
$proc.WaitForInputIdle(5000)
if ($proc.HasExited) {
    Write-Output "SecureCRT 启动失败，退出码: $($proc.ExitCode)"
} else {
    Write-Output "SecureCRT 已启动，PID: $($proc.Id)"
}
```
找到后写入 `.ai-output/config.ini`：
```bash
mkdir -p .ai-output
cat <<EOF >> .ai-output/config.ini
[securecrt]
com = <端口号>
baud = <波特率>
EOF
```
## 3. 日志存储位置

**优先从工程配置读取**：

先检查 `.ai-output/config.ini` 中的 `securecrt.logdir` 字段：

```bash
cat ".ai-output/config.ini"
```

如果工程配置存在，直接用里面指定的目录；否则按以下系统配置查找。

用以下命令搜索配置中的日志路径：

```bash
grep -ri "Log Filename V2" "D:/WLPC/AppData/Roaming/VanDyke/Config/Sessions/"
```

或全局搜索：

```bash
grep -ri "Log Filename V2" "D:/WLPC/AppData/Roaming/VanDyke/Config/"
```

找到后写入 `.ai-output/config.ini`：

```bash
cat <<EOF >> .ai-output/config.ini
logdir = <搜索到的日志目录>
EOF
```

## 4. 快速查看最新日志

```powershell
Get-ChildItem -Path "<securecrt.logdir>" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime, Length
```
