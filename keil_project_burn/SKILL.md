---
name: keil_project_burn
description: 烧录（下载）当前Keil工程到目标芯片。当用户要求烧录、download、flash、下载程序到芯片时使用此skill。
---

# Keil 工程烧录（Download）

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

## 3. 烧录命令

使用解析得到的路径执行：

```powershell
& "<uv4_path>" -f "<project_path>" -o "burn_log.txt"
```

参数说明：
- `-f`：Flash download 模式（下载到芯片，不启动 IDE）
- `-o`：输出烧录日志到指定文件

如果用户要求"编译并烧录"，先执行 `-b` 编译，再执行 `-f` 烧录。

## 4. 检查结果

烧录完成后读取日志确认结果：

```powershell
cat "burn_log.txt"
```

目标：**0 Error(s)**，或日志中包含 "Download Complete" / "Verify OK"。
