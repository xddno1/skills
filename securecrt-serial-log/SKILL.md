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

系统已安装路径：`D:\software\CRT\SecureCRT.exe`

如果找不到，用以下命令搜索：

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

如果工程配置存在，用里面的值启动；否则用默认值。

命令行启动格式：

```powershell
& "<securecrt.path>" /SERIAL <com> /BAUD <baud>
```

常用波特率：115200、9600。

## 3. 日志存储位置

**优先从工程配置读取**：

先检查 `.ai-output/config.ini` 中的 `securecrt.logdir` 字段：

```bash
cat ".ai-output/config.ini"
```

如果工程配置存在，直接用里面指定的目录；否则按以下系统配置查找。

系统默认日志目录：`D:\log\`

文件名格式：`Serial-COM9-年月日_时_分_秒.log`

配置文件中定义了自动记录和午夜切分：
- 配置路径：`D:\WLPC\AppData\Roaming\VanDyke\Config\Sessions\Serial-COM9.ini`
- 日志路径字段：`S:"Log Filename V2"=D:\log\%S-%Y%M%D_%h_%m_%s.log`

如果以上都找不到，用以下命令搜索配置中的日志路径：

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
