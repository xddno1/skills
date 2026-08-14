---
name: esp-idf-build
description: 自动检测并使用与工程匹配的 ESP-IDF 环境，执行 build、flash、monitor，并诊断 Windows PowerShell、工具链分离安装、受限沙箱、CMake/Ninja 和链接错误。用户提到 ESP-IDF、idf.py、编译、构建、烧录、下载、串口监控或要求验证 ESP32 代码时必须使用。
---

# ESP-IDF 构建、烧录与监控

## 目标

可靠完成 ESP-IDF 工程的构建、烧录或串口监控。优先复用工程已经验证过的 ESP-IDF 版本和工具链，不因环境激活失败而误判为代码错误。

## 总体原则

1. 先确认当前目录是 ESP-IDF 工程：应存在顶层 `CMakeLists.txt`，通常还会有 `sdkconfig` 或 `sdkconfig.defaults`。
2. 构建前查看当前改动。宏、控制流、接口、配置、源文件列表等变化必须编译；只有注释、日志或纯格式变化时才可说明理由后跳过。
3. 优先使用工程历史构建记录中的 ESP-IDF 版本，不自动切换到其他版本。
4. 环境错误、沙箱权限错误和源码错误要分开报告。环境未正确激活时，不要先修改业务代码。
5. 不主动执行 `fullclean`、删除 `build` 或重新生成 `sdkconfig`。这些操作会丢失缓存或配置，只有证据明确且用户授权后才能执行。
6. 构建成功必须同时确认命令退出码为 0，并出现 `Project build complete` 或生成了最新的 `.elf`/`.bin`。

## 1. 识别工程匹配的 ESP-IDF

按以下优先级定位：

1. `build/project_description.json` 中的 `idf_path` 和版本信息。
2. 当前进程的 `IDF_PATH`。
3. 常见安装目录：
   - Windows：`C:\Espressif\frameworks\*\esp-idf`、`C:\esp\v*\esp-idf`、用户已知的 ESP-IDF 安装目录。
   - Linux/macOS：`~/esp/esp-idf`、`/opt/esp-idf`。
4. `build/CMakeCache.txt` 中已经记录的 Python、CMake、Ninja、Git 和编译器路径。

如果找到多个版本且工程历史无法确定匹配项，必须询问用户，不要擅自选择最新版。

检查选中的 IDF 目录至少包含：

- `tools/idf.py`
- `tools/idf_tools.py`
- Windows 下的 `export.ps1`，或 Linux/macOS 下的 `export.sh`

## 2. Windows 预检

### 2.1 修复平台识别变量缺失

Codex 或受限 PowerShell 进程可能缺少 `PROCESSOR_ARCHITECTURE`、`PROCESSOR_ARCHITEW6432` 和 `OS`。这会让 Python 的 `platform.machine()` 返回空字符串，使 ESP-IDF 报：

```text
Support for platform 'Windows-' hasn't been added yet.
```

仅在当前构建进程中补齐变量，不修改系统永久环境：

```powershell
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
if (-not $env:OS) {
    $env:OS = 'Windows_NT'
}
```

用 IDF Python 或当前 Python 验证：

```powershell
python -c "import platform; print(platform.system(), repr(platform.machine()))"
```

期望得到类似 `Windows 'AMD64'`，不能是 `Windows ''`。

### 2.2 检查临时目录是否可写

ESP-IDF 5.4 的激活脚本会在临时目录生成 `activate_*.ps1`。先测试当前临时目录能否创建文件。若出现：

```text
PermissionError: [Errno 13] Permission denied: ...activate_*.ps1
```

为本次任务设置一个明确可写、范围受控的临时目录。优先使用环境已经声明可写的临时目录；否则可在当前工作区创建任务专用目录，并在完成后只删除该明确目录。使用 `TMPDIR` 影响 Python `tempfile`，避免永久修改用户的 `TEMP`/`TMP`。

### 2.3 正常激活

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& '<匹配版本的 IDF_PATH>\export.ps1'
```

激活后必须检查：

```powershell
if ($LASTEXITCODE -ne 0 -or -not (Get-Command idf.py -ErrorAction SilentlyContinue)) {
    throw 'ESP-IDF activation failed'
}
idf.py --version
```

不要因为 `export.ps1` 打印了部分成功信息就认定激活成功。

## 3. Windows 分离安装回退流程

有些机器的 ESP-IDF 框架、Python、CMake、Ninja 和交叉编译器安装在不同目录。若 `export.ps1` 失败但工程已有 `build`，从工程缓存恢复准确环境。

### 3.1 从缓存读取路径

读取：

- `build/project_description.json`：`idf_path`
- `build/CMakeCache.txt`：
  - `PYTHON`
  - `CMAKE_COMMAND`
  - `CMAKE_MAKE_PROGRAM`
  - `CMAKE_C_COMPILER_AR` 或其他包含工具链 `bin` 目录的项
  - `GIT_EXECUTABLE`

`CMakeCache.txt` 的值格式为 `KEY:TYPE=value`，解析时取第一个 `=` 后的完整字符串，不要按冒号切 Windows 盘符。

### 3.2 重建当前进程环境

1. 设置 `IDF_PATH` 为 `project_description.json` 中的路径。
2. `PYTHON` 若为 `<venv>\Scripts\python.exe`，设置 `IDF_PYTHON_ENV_PATH=<venv>`。
3. 将下列目录按顺序临时加入当前进程 PATH：
   - Python 的 `Scripts`
   - CMake 所在目录
   - Ninja 所在目录
   - ESP 交叉编译器所在 `bin` 目录
   - Git 所在目录
4. 补齐第 2.1 节的 Windows 平台变量。
5. 使用匹配 Python 直接运行：

```powershell
& $idfPython "$idfPath\tools\idf.py" build
```

如果提示：

```text
"cmake" must be available on the PATH to use idf.py
```

说明 PATH 恢复不完整，继续从 `CMakeCache.txt` 添加 CMake/Ninja/编译器目录，不要切换到另一套 IDF。

如果出现 Python `asyncio`、`CreateFile` 或管道相关的 `WinError 5`，这是沙箱阻止创建子进程管道。应使用产品提供的权限升级机制，在沙箱外重跑同一条、范围明确的构建命令；不要修改工程代码绕过。

## 4. 是否需要构建

读取未暂存和已暂存差异：

```powershell
$workingDiff = git diff HEAD --unified=0 2>$null
$stagedDiff = git diff --cached --unified=0 2>$null
```

以下变化必须完整构建：

- `#define`、`#if`、`sdkconfig`、`CMakeLists.txt`、Kconfig、分区表
- 函数逻辑、控制流、结构体、枚举、函数声明或头文件接口
- GPIO、时钟、外设和硬件参数
- 新增、删除或调整源文件
- 链接关系和组件依赖

只有以下变化可跳过，并明确告诉用户原因：

- 纯注释
- 纯日志文字
- 空白和格式化
- 不影响声明或逻辑的局部变量重命名

无法判断时执行构建。

## 5. 执行命令

### 构建

```powershell
idf.py build
```

大型工程默认至少允许 300 秒。持续构建时每 60 秒向用户更新一次，不能把正常耗时误报为卡死。

### 烧录

仅在用户明确要求烧录时执行：

```powershell
idf.py -p COM_PORT flash
```

如果只检测到一个串口，可以使用该端口；存在多个候选端口时询问用户。

### 串口监控

仅在用户要求监控时执行：

```powershell
idf.py -p COM_PORT monitor
```

组合操作：

```powershell
idf.py -p COM_PORT flash monitor
```

## 6. 编译错误诊断

### 源文件整体符号缺失

如果同一 `.c` 文件中的多个公开函数全部出现 `undefined reference`，优先检查：

1. 该源文件是否仍在 `idf_component_register(SRCS ...)` 或组件源文件变量中。
2. `build/compile_commands.json` 是否包含该源文件。
3. 对应 `.obj` 是否只是旧缓存。
4. 使用工具链的 `ar t <libcomponent.a>` 检查对象是否真正进入静态库。
5. 使用 `nm -C <app.elf>` 验证最终符号。

不要因为构建目录还残留旧 `.obj` 就误认为该源文件仍参与当前构建。

### 常见错误对应关系

| 错误 | 优先检查 |
|---|---|
| `Windows-` unsupported | Windows 架构环境变量为空 |
| `activate_*.ps1 Permission denied` | Python 临时目录不可写 |
| `cmake must be available` | 激活失败或 PATH 恢复不完整 |
| `WinError 5` / asyncio pipe | 沙箱禁止子进程，申请范围明确的权限升级 |
| `No such file or directory` | include、组件依赖、IDF 版本 |
| `implicit declaration` | 头文件和版本兼容性 |
| `undefined reference` | 源文件列表、条件编译、静态库成员、链接依赖 |
| 分区超限 | `.bin` 大小与 app 分区容量 |

## 7. 成功验证与汇报

构建成功后至少确认：

1. 输出包含 `Project build complete`。
2. `.elf` 和 `.bin` 的时间戳已更新。
3. 报告应用二进制大小、最小 app 分区大小和剩余空间比例。
4. 若修复过链接错误，使用 `ar`/`nm` 确认目标对象和符号已进入最终产物。
5. 说明只完成了编译还是也完成了烧录；没有用户授权时不要自动烧录。

最终回复应先给结论，再简述根因、改动和验证结果。环境问题与源码问题分别说明。
