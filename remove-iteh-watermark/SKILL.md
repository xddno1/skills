---
name: remove-iteh-watermark
description: 去除 iTeh Standards 发布的 ISO 预览版 PDF 中的水印叠加层。iTeh 水印以 Form XObject 方式通过额外的 content stream 叠加到每页，与正文内容流完全分离。当用户要求去除 iTeh 水印、清理 ISO 预览版 PDF 水印、移除标准预览水印时使用此 skill。TRIGGER：任何涉及 iTeh watermark / iTeh 预览 PDF / 去除水印 / 去水印 ISO / clean iTeh PDF / remove watermark from ISO preview 的请求。
---

# Remove iTeh Watermark

去除 iTeh Standards 发布的 ISO 预览版 PDF 水印叠加层。

## 原理

iTeh Standards 在其分发的 ISO 预览版 PDF 中，为每页附加一个独立的 content stream（约 65–80 字节），该 stream 通过 `/Xxx Do` 操作调用一个 Form XObject（水印图层），叠加在正文内容之上。

关键点：**水印与正文分别位于独立的 content stream 中**。直接清空水印 stream 即可完全移除水印，正文内容流不受任何影响。

不同 ISO PDF 使用的 Form XObject 名称不同（例如 `/Fm0`、`/FXX1`），因此通过 stream 大小 + 内容特征（XObject `Do` 调用 + 不含 `BT` 文字绘制）自动识别水印 stream。

## 依赖

- `pymupdf` (`pip install pymupdf`)

## 用法

```powershell
python "C:\Users\WLPC\.claude\skills\remove-iteh-watermark\remove_iteh_watermark.py" "<input.pdf>" "<output.pdf>"
```

## 工作流程

1. 用户指定需要处理的 PDF 路径
2. 运行脚本，输出 `-clean.pdf`
3. 验证正文内容完整性（对比原文与处理后文本）
4. 报告处理结果（水印 stream 数量、文件大小变化）
