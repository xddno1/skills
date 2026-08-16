---
name: esp_project_compile
description: 快速构建当前 ESP-IDF 工程。自动识别历史 ESP-IDF 版本、处理环境激活失败与 Windows 编码问题，适用于 Git Bash / PowerShell 混合环境。
---

# ESP-IDF 工程快速编译

直接调用编译脚本，脚本内部自动完成：

1. 工程合法性检查（`CMakeLists.txt`、`sdkconfig`）；
2. 从历史构建记录或常见路径查找匹配的 ESP-IDF；
3. 优先使用 `export.ps1` 激活环境；失败时自动从 `build/CMakeCache.txt` 回退恢复 Python/CMake/Ninja/工具链/Git 路径；
4. 自动处理 Windows GBK 编码导致的 `UnicodeEncodeError`；
5. 执行 `idf.py build` 并检查产物；
6. 输出摘要、产物大小、日志尾部。

## 调用方式

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\WLPC\.codebuddy\skills\esp_project_compile\esp_project_compile.ps1" -Workspace "<工作目录>"
```

**timeout 建议设置为 600 秒（10 分钟）**，大型工程可延长至 1200 秒。

## 退出码

- `0`：构建成功，产物已生成
- `1`：构建成功，但存在 warning（如未设置 UTF-8 时 PowerShell 把 stderr 误判）
- `2+`：构建失败，存在错误
- `98`：当前目录不是有效的 ESP-IDF 工程
- `99`：未找到可用的 ESP-IDF 安装

## 输出摘要

脚本会输出：

- `ExitCode`
- `BuildStatus`
- `AppBinary` 路径与大小
- `Bootloader` 大小与剩余空间
- `AppPartition` 最小大小与剩余空间
- 构建日志尾部（最后 80 行）

agent 直接据此向用户报告结果即可。
