---
name: keil_project_compile
description: 编译当前Keil工程。当用户要求编译、build、make或验证代码时使用此skill。
---

# Keil 工程编译

直接调用编译脚本，脚本内部自动完成 UV4.exe 查找、工程文件查找、config.ini 读写、编译执行、结果检查。

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\WLPC\.kimi-code\skills\keil_project_compile\keil_compile.ps1" -Workspace "<工作目录>"
```

timeout 设置为 600000（10 分钟）。脚本退出码即为 UV4.exe 退出码：
- 0：编译成功，无警告
- 1：编译成功，有警告
- 2+：编译失败，有错误

脚本会输出摘要（ExitCode / Errors / Warnings）和日志尾部，agent 据此向用户报告结果即可。
