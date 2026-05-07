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

使用解析得到的路径执行：

```powershell
& "<uv4_path>" -b "<project_path>" -o "build_log.txt"
```

参数说明：
- `-b`：build 模式（只编译不启动 IDE）
- `-o`：输出编译日志到指定文件

## 4. 检查结果

编译完成后读取日志确认结果：

```powershell
cat "build_log.txt"
```

目标：**0 Error(s)**

## 5. 输出文件

编译成功后的 hex 文件，从工程配置 `keil.hex_path` 读取；若未配置，则在工程目录的 Objects 或 OBJ 子目录中搜索 `.hex` 文件。
