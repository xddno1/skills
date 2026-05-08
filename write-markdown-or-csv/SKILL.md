---
name: write-markdown-or-csv
description: 输出 markdown 或 csv 文件时，统一保存到工程的 .ai-output 目录下。当用户要求生成报告、统计数据、导出表格或整理分析结果时使用此 skill。
---

# Markdown / CSV 输出规范

## 文件保存位置

所有 markdown 和 csv 文件统一放在工程的 `.ai-output/` 文件夹下。

- Markdown 文件：`.ai-output/*.md`
- CSV 文件：`.ai-output/*.csv`

## 勘误与验证

所有文件在**写入前**必须：

1. **回到项目代码中再次验证**分析结果
2. 检查每一项数据是否有代码依据
3. 如有不正确的内容，必须修正
4. **验证需要仔细、有依据，不能靠猜**

## CSV 编码

CSV 文件使用 UTF-8 with BOM 编码，确保 Excel 打开时中文不乱码。

## Markdown 格式

- 使用标准 Markdown 语法
- 表格对齐，表头与内容分隔清晰
- 代码块标注语言类型
