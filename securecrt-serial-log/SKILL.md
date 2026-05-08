---
name: securecrt-serial-log
description: 打开SecureCRT连接串口、查找日志文件位置。当用户需要打开串口工具看log或询问log存在哪里时使用。
---

# SecureCRT 串口连接与日志定位

直接调用脚本，脚本内部自动完成 SecureCRT.exe 查找、串口打开、日志目录定位、config.ini 读写。

## 1. 打开串口

```powershell
powershell -ExecutionPolicy Bypass -File "c:\Users\WLPC\.claude\skills\securecrt-serial-log\securecrt.ps1" -Workspace "<工作目录>" -Action open -Com "<COMx>" -Baud "<波特率>"
```

参数说明：
- `-Workspace`：工程根目录（必填）
- `-Action open`：打开串口连接
- `-Com`：串口号，如 `COM9`。可省略，省略时从 `.ai-output/config.ini` 的 `com` 字段读取。
- `-Baud`：波特率，默认 `115200`。常用 `115200` / `9600`。

脚本会按 config.ini → 注册表 → 常见安装路径（包括 `D:\software\CRT\SecureCRT.exe`）的顺序查找 SecureCRT.exe，并把结果回写到 config.ini。

## 2. 查看最新日志

```powershell
powershell -ExecutionPolicy Bypass -File "c:\Users\WLPC\.claude\skills\securecrt-serial-log\securecrt.ps1" -Workspace "<工作目录>" -Action logs -LogCount 5
```

参数说明：
- `-Action logs`：列出日志目录中最近修改的日志
- `-LogCount`：返回条数，默认 5

脚本会按 config.ini → SecureCRT 会话配置 (`Log Filename V2`) → 默认 `D:\log\` 的顺序查找日志目录，输出最近 N 个文件的时间、大小、文件名，并打印最新文件的完整路径。

## 3. 退出码

- `0`：成功
- `97`：找不到日志目录
- `98`：未指定 COM 口
- `99`：找不到 SecureCRT.exe
