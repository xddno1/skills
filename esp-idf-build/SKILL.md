---
name: esp-idf-build
description: Auto-detect ESP-IDF environment, handle platform differences (Windows PowerShell execution policy), execute idf.py build/flash/monitor commands, and parse compilation output to provide fix suggestions
---

## 触发条件

当用户提到以下任一关键词时激活：
- "build", "编译", "构建"
- "flash", "烧录", "下载"
- "monitor", "监控", "串口"
- "idf.py"
- "esp-idf"

## 执行流程

### 1. 环境检测

#### 1.1 检测操作系统
```
检查 $PSVersionTable.Platform 或 uname
├── Windows (PowerShell)
│   └── 需要处理 ExecutionPolicy
├── Linux
└── macOS
```

#### 1.2 查找 ESP-IDF 安装
搜索路径（按优先级）：
1. 环境变量 `$env:IDF_PATH`
2. 常见安装路径：
   - Windows: `C:\esp\v*\esp-idf` (支持多版本)
   - Linux: `~/esp/esp-idf`, `/opt/esp/esp-idf`
   - macOS: `~/esp/esp-idf`

如果找到多个版本：
1. **优先匹配项目已有版本**：检查 `build/project_description.json` 中的 `IDF_VER`，或 `build/config/sdkconfig.h` 中的版本标记。如果找到，使用与项目匹配的已安装版本。
2. **回退到最新版本**：如果项目未构建过或无法确定版本，列出可用版本供用户选择，**不要**自动选择最新版本（避免版本不兼容问题）。

#### 1.3 验证环境完整性
检查以下文件是否存在：
- `tools/idf.py`
- `export.ps1` (Windows) 或 `export.sh` (Linux/Mac)
- `tools/python_env` 或虚拟环境

### 2. 环境激活

#### Windows (PowerShell)
```powershell
# 临时绕过执行策略
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# 激活环境
& "C:\esp\vX.X\esp-idf\export.ps1"
```

#### Linux/macOS
```bash
source ~/esp/esp-idf/export.sh
```

### 2.5 变更分析（自动判断是否需要编译）

在执行编译前，自动分析当前 git 工作区的变更内容，判断修改类型：

1. **获取变更内容**：
   ```powershell
   $diffs = git diff HEAD --unified=0 2>$null
   $allChanges = $diffs + "`n" + (git diff --cached --unified=0 2>$null)
   ```
   如果 `git diff HEAD` 无输出且无暂存变更，跳过变更分析；如果项目不是 git 仓库，也跳过分析，直接执行编译。

2. **逐行分析变更内容**：
   从 diff 中提取所有以 `+` 或 `-` 开头的行（排除 `---`、`+++`、`@@` 元信息行），逐行匹配以下规则：

   | 普通修改（跳过编译） | 需要编译的修改 |
   |--------------------|--------------|
   | 包含日志函数调用：`ESP_LOGI(`、`ESP_LOGE(`、`ESP_LOGW(`、`ESP_LOGD(`、`ESP_LOGV(`、`printf(`、`ets_printf(` | 修改函数逻辑/控制流（`if`、`for`、`while`、`switch`、`case` 等关键字） |
   | 纯注释行：以 `//`、`/*`、`*/`、`*` 开头 | 修改结构体/联合体/枚举定义（`struct`、`union`、`enum`、`typedef`） |
   | 仅空白/缩进/空行调整 | 修改宏定义（`#define`、`#if`、`#ifdef`、`#ifndef`、`#undef`） |
   | 变量名重命名（行中无类型关键字变化） | 修改函数签名/参数/返回值类型 |
   | 删除未使用的变量声明（仅 `int/char/void xxx;` 整行删除） | 修改 `sdkconfig`、`CMakeLists.txt`、`partitions.csv`、`Kconfig` |
   | 修饰符调整（`static`、`const`、`inline` 等关键字的增删） | 修改外设/管脚/GPIO/时钟配置 |
   | | 新增或删除源文件（`.c`、`.h`、`.cpp`） |
   | | 修改 `.h` 头文件中的声明/接口/宏 |
   | | 所有不符合左侧条件的变更 |

3. **判定规则**：
   - 遍历所有变更行，如果**所有行**均匹配左侧"普通修改"规则 → **跳过编译验证**，提示用户"检测到仅含日志/注释/格式变更，无需编译验证"
   - 如果**存在任意一行**匹配右侧"需要编译"规则 → **执行完整编译验证**，继续后续步骤
   - 如果同时存在两类修改，或无法明确判断 → **保守执行编译验证**

   > **判断示例**：
   > - ✅ 跳过：`+    ESP_LOGI("TAG", "enter func");`
   > - ✅ 跳过：`+// TODO: fix later`
   > - ✅ 跳过：`-int unused_var;`（仅删除未使用的变量）
   > - ❌ 编译：`+    gpio_set_level(GPIO_NUM_4, 1);`
   > - ❌ 编译：`+#define NEW_MACRO 1`
   > - ❌ 编译：`-    if (condition) {`
   > - ❌ 编译：任何对 `.h` 文件的修改

### 3. 命令执行

#### build
```bash
idf.py build
```
- 超时：300秒（大型项目可延长）
- 捕获 stdout 和 stderr

#### flash
```bash
# 自动检测端口（Windows COM*, Linux /dev/ttyUSB* /dev/ttyACM*）
# 或从 sdkconfig 读取 CONFIG_ESPTOOLPY_PORT
idf.py -p PORT flash
```

#### monitor
```bash
idf.py -p PORT monitor
```

#### 组合命令
```bash
idf.py -p PORT flash monitor
```

### 4. 输出解析与错误处理

#### 4.1 成功标志
- `[X/Y] Building C object ...`
- `Project build complete`
- `Successfully created esp32s3 image`

#### 4.2 常见错误分类

| 错误类型 | 识别模式 | 修复建议 |
|---------|---------|---------|
| **宏不存在** | `implicit declaration of function 'XXX'` | 检查 ESP-IDF 版本兼容性，替换为新版本宏 |
| **缺少头文件** | `No such file or directory` | 添加缺失的 `#include` 或 `REQUIRES` |
| **类型不匹配** | `expects argument of type 'X' but argument has type 'Y'` | 添加类型转换或修改格式字符串 |
| **链接错误** | `undefined reference to 'xxx'` | 添加缺失的源文件到 CMakeLists.txt 或添加 `REQUIRES` |
| **执行策略** | `PSSecurityException` | 运行 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| **Python 依赖缺失** | `No module named 'xxx'` | 运行 `python -m pip install xxx` 或重新运行 install.sh |
| **JTAG 引脚冲突** | 涉及 GPIO12-15 (ESP32) 或 GPIO41-42 (ESP32-S3) | 提示用户检查 JTAG 是否启用 |

#### 4.3 自动修复尝试
对于已知错误模式，自动提供修复代码：
1. 替换不存在的宏
2. 添加缺失的头文件包含
3. 修复类型转换

## 示例交互

**用户**: 帮我构建这个 ESP-IDF 项目

**Assistant**:
1. 检测到项目目录包含 `CMakeLists.txt` 和 `sdkconfig`
2. 发现 ESP-IDF v5.4.3 安装在 `C:\esp\v5.4.3\esp-idf`
3. 激活环境并运行 `idf.py build`
4. 如果编译成功：报告二进制大小和分区占用
5. 如果编译失败：分析错误，提供修复建议或自动修复

**用户**: 烧录到开发板

**Assistant**:
1. 检查可用串口（Windows: COM3, COM4...）
2. 询问用户或自动选择（如果有 sdkconfig 中的配置）
3. 运行 `idf.py -p COM3 flash`

**用户**: 打开串口监控

**Assistant**:
1. 运行 `idf.py -p COM3 monitor`
2. 解释快捷键：Ctrl+] 退出，Ctrl+T Ctrl+R 复位

## 注意事项

1. **Windows 执行策略**：首次使用 PowerShell 时必须绕过执行策略
2. **多版本选择**：优先使用项目已有构建记录的匹配版本；若项目未构建过，列出可用版本供用户选择，不自动选择最新版
3. **虚拟环境**：确保使用 ESP-IDF 的 Python 虚拟环境而非系统 Python
4. **端口检测**：Windows 自动检测 COM 端口，Linux 检测 /dev/ttyUSB* 和 /dev/ttyACM*
5. **项目配置**：读取 `sdkconfig.defaults` 了解项目配置（目标芯片、分区表等）
