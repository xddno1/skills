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

### 3.1 查找 SecureCRT 配置目录

SecureCRT 的配置目录位置因安装方式不同而异，按以下优先级查找：

**方式一：从注册表读取（标准安装版）**

```powershell
reg query "HKCU\SOFTWARE\VanDyke\SecureCRT" /v "Config Path"
```

输出示例：
```
Config Path    REG_SZ    D:\WLPC\AppData\Roaming\VanDyke\Config
```

**方式二：默认路径猜测**

如果注册表读取失败，尝试以下常见路径：
- `C:\Users\<用户名>\AppData\Roaming\VanDyke\Config`
- `D:\<用户名>\AppData\Roaming\VanDyke\Config`

### 3.2 从会话配置中解析日志路径

在配置目录的 `Sessions` 子目录中，每个会话对应一个 `.ini` 文件（如 `Serial-COM9.ini`、`Default.ini`）。日志路径存储在 `Log Filename V2` 字段中。

**搜索所有会话的日志配置：**

```bash
grep -ri "Log Filename V2" "<Config目录>/Sessions/"
```

**读取特定会话的完整日志配置：**

```bash
grep -i "Log" "<Config目录>/Sessions/<会话名>.ini"
```

关键配置项说明：

| 配置项 | 含义 |
|--------|------|
| `Log Filename V2` | 日志文件保存路径及命名格式 |
| `Start Log Upon Connect` | `00000001`=连接时自动记录，`00000000`=手动开始 |
| `Log Mode` | `00000000`=追加，`00000001`=覆盖 |

**路径中的变量说明：**

日志路径支持变量替换，常见变量：
- `%S` - 会话名称
- `%Y` - 年（4位）
- `%M` - 月
- `%D` - 日
- `%h` - 时
- `%m` - 分
- `%s` - 秒

例如 `D:\log\%S-%Y%M%D_%h_%m_%s.log` 会生成 `Serial-COM9-20260508_16_11_32.log`

### 3.3 保存到工程配置

找到后写入 `.ai-output/config.ini`：

```bash
cat <<EOF >> .ai-output/config.ini
logdir = <日志目录（去掉变量部分）>
EOF
```

## 4. 快速查看最新日志

```powershell
Get-ChildItem -Path "<securecrt.logdir>" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime, Length
```
