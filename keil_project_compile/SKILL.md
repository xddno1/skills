---
name: keil_project_compile
description: 编译当前Keil工程。当用户要求编译、build、make或验证代码时使用此skill。
---

# Keil 工程编译

## 1. 获取 UV4.exe 路径

**优先从工程配置读取**：

先检查 `.ai-output/config.ini` 中的 `keil.uv4_path` 字段：

```bash
cat ".ai-output/config.ini"
```

如果工程配置存在，直接用里面的路径；否则按以下方式查找。

用以下命令搜索：

```powershell
where UV4.exe
```

或在注册表中查安装目录：

```powershell
reg query "HKLM\SOFTWARE\WOW6432Node\Keil\Products\MDK" /v "Path" 2>nul || reg query "HKLM\SOFTWARE\Keil\Products\MDK" /v "Path"
```

找到后写入 `.ai-output/config.ini`：

```bash
mkdir -p .ai-output
cat <<EOF >> .ai-output/config.ini
[keil]
uv4_path = <搜索到的路径>
EOF
```

## 2. 获取工程文件路径

**优先从工程配置读取**：

先检查 `.ai-output/config.ini` 中的 `keil.project_path` 字段：

```bash
cat ".ai-output/config.ini"
```

如果工程配置存在，直接用里面的路径；否则在当前工作目录搜索：

```bash
find . -name "*.uvprojx" -o -name "*.uvproj"
```

或：

```powershell
Get-ChildItem -Recurse -Filter "*.uvprojx" | Select-Object -First 1 FullName
```

找到后写入 `.ai-output/config.ini`：

```bash
cat <<EOF >> .ai-output/config.ini
project_path = <搜索到的路径>
EOF
```

## 3. 编译命令

⚠️ **重要**：UV4.exe 是 GUI 程序，直接 `& UV4.exe ...` 会立即返回 shell 但编译还在后台运行。**必须使用 `Start-Process -Wait` 同步等待编译完成**，否则会读到不完整的日志。

使用解析得到的路径执行（PowerShell 工具调用时务必把 `timeout` 参数提到 600000，给编译留 10 分钟上限）：

```powershell
$proc = Start-Process -FilePath "<uv4_path>" `
    -ArgumentList @('-b', '<project_path>', '-o', 'build_log.txt') `
    -Wait -PassThru -WindowStyle Hidden
"ExitCode=$($proc.ExitCode)"
```

参数说明：
- `-b`：build 模式（只编译不启动 IDE）
- `-o`：输出编译日志到指定文件
- `Start-Process -Wait`：阻塞直到 UV4.exe 真正退出（编译完成）
- `-PassThru`：返回进程对象，便于读取 `ExitCode`
- `-WindowStyle Hidden`：不弹出 Keil 窗口

UV4.exe `-b` 模式退出码：
- `0`：无警告无错误
- `1`：有警告
- `2`：有错误
- `3`：致命错误（无法启动）
- `11/12`：编译成功（含警告）
- `15`：错误，未生成可执行文件

如果编译时间预计较长（大型工程），可以在 PowerShell 工具调用时设置 `run_in_background: true`，工具会在编译结束后通知；后续再读 `build_log.txt`。

## 4. 检查结果

UV4.exe 退出后再读取日志（此时日志已写完整）：

```powershell
Get-Content "build_log.txt"
```

目标：**0 Error(s)**。如果 `ExitCode >= 2`，结合日志末尾的 `X Error(s), Y Warning(s)` 行定位问题。

## 5. 输出文件

编译成功后的 hex 文件，从工程配置 `keil.hex_path` 读取；若未配置，则在工程目录的 Objects 或 OBJ 子目录中搜索 `.hex` 文件。
