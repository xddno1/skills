---
name: keil_project_burn
description: 烧录（下载）当前Keil工程到目标芯片。当用户要求烧录、download、flash、下载程序到芯片时使用此skill。
---

# Keil 工程烧录（Download）

直接调用烧录脚本，脚本内部自动完成 UV4.exe 查找、工程文件查找、config.ini 读写、烧录执行、结果检查。

## 仅烧录（默认）

```powershell
powershell -ExecutionPolicy Bypass -File "c:\Users\WLPC\.agents\skills\keil_project_burn\keil_burn.ps1" -Workspace "<工作目录>"
```

## 编译并烧录

用户要求"编译并烧录"时，加 `-BuildFirst` 开关。脚本会先编译，确认 0 Error 后再烧录；若编译失败则自动中止。

```powershell
powershell -ExecutionPolicy Bypass -File "c:\Users\WLPC\.agents\skills\keil_project_burn\keil_burn.ps1" -Workspace "<工作目录>" -BuildFirst
```

## 参数说明

- `-Workspace`：工程根目录（必填）
- `-BuildFirst`：先编译再烧录（编译失败则跳过烧录）

timeout 设置为 600000（10 分钟）。脚本退出码 0 表示烧录成功，非 0 表示失败。

脚本会输出摘要（ExitCode / Success / Log）和日志尾部。如果日志中出现 "Error: Flash Download failed" / "No Algorithm found" / "Cannot Load Flash Programming Algorithm"，需停下来排查（接线、目标芯片型号、调试器配置），不要重试覆盖芯片。
