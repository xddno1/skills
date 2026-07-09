---
name: html-mermaid-flowchart
description: Guide agents to generate friendly Mermaid program flowcharts inside HTML pages, reports, or artifacts. Use when creating or editing HTML and the content needs a process flow, program logic flow, call path, state/business workflow, conditional branch diagram, or troubleshooting sequence; prefer Mermaid-rendered diagrams over ASCII art, static screenshots, or hand-written SVG unless the user explicitly asks otherwise.
---

# Html Mermaid Flowchart

## Overview

When an HTML output needs a flowchart, embed a Mermaid diagram that renders in the page and is easy to scan. Keep the chart faithful to the source logic, visually calm, and useful for readers who need to understand program behavior quickly.

## Workflow

1. Identify the flow to show from code, logs, docs, or the user's description.
2. Choose the smallest diagram type that fits:
   - Use `flowchart TD` for normal program or business flow.
   - Use `sequenceDiagram` only when call order between actors/components is the main point.
   - Use `stateDiagram-v2` only when states and transitions are the main point.
3. Embed the Mermaid source in the HTML with `<pre class="mermaid">...</pre>` or `<div class="mermaid">...</div>`.
4. Initialize Mermaid once after the library is loaded.
5. Verify that the browser renders a diagram, not raw Mermaid text.

## HTML Pattern

For a standalone static HTML file, use the existing project dependency if one exists. Otherwise, include a pinned Mermaid browser bundle and initialize it explicitly:

```html
<section class="flow-section">
  <h2>程序流程</h2>
  <pre class="mermaid">
flowchart TD
  start([开始])
  input[/接收输入/]
  validate{参数有效?}
  process[执行核心逻辑]
  save[(保存结果)]
  error[记录错误并返回]
  done([结束])

  start --> input --> validate
  validate -- 是 --> process --> save --> done
  validate -- 否 --> error --> done
  </pre>
</section>

<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({
    startOnLoad: true,
    theme: "base",
    securityLevel: "strict",
    flowchart: { curve: "basis", htmlLabels: false }
  });
</script>
```

Use CSS to make the diagram readable and responsive:

```css
.flow-section {
  width: 100%;
  overflow-x: auto;
}

.mermaid {
  min-width: 640px;
  padding: 16px;
  border: 1px solid #d7dde5;
  border-radius: 8px;
  background: #ffffff;
}
```

## Diagram Rules

- Use ASCII node IDs and concise human labels: `validate{参数有效?}` is good; long code expressions in labels are not.
- Keep Mermaid delimiters balanced on every node definition. Common valid forms are `node["label"]`, `node{"label"}`, `node(["label"])`, `node[/"label"/]`, and `node[("label")]`.
- Close quoted decision labels before the closing brace. For example, write `CHRG_CHECK{"IO_CHRG == 0 ?<br/>(充电 IC 正在充电?)"}`, not `CHRG_CHECK{"IO_CHRG == 0 ?<br/>(充电 IC 正在充电?)}`.
- Do not place raw double quotes inside a quoted node label. Use single quotes, remove the quote marks, or escape them as `&quot;`.
- Include clear start and end nodes for program flows.
- Put each meaningful operation in one node; avoid one node per source line.
- Use decision diamonds for branches and label branch edges with `是` / `否`, `成功` / `失败`, or concrete conditions.
- Show error, timeout, retry, and fallback paths when they affect behavior.
- Use `subgraph` to group modules, layers, tasks, or phases when the flow crosses boundaries.
- Prefer `TD` for procedural flow and `LR` for pipeline or module-to-module flow.
- Split diagrams that exceed roughly 20 nodes or become visually dense.
- Do not invent business semantics. If the source material does not prove a branch, label it as inferred or ask the user to confirm before baking it into the diagram.

## Styling Guidance

Use subtle styles only when they improve scanning:

```mermaid
flowchart TD
  start([开始]):::terminal
  check{是否满足条件?}:::decision
  ok[继续处理]:::action
  fail[失败处理]:::error
  done([结束]):::terminal

  start --> check
  check -- 是 --> ok --> done
  check -- 否 --> fail --> done

  classDef terminal fill:#e8f3ff,stroke:#2563eb,color:#172033;
  classDef decision fill:#fff7d6,stroke:#b7791f,color:#172033;
  classDef action fill:#edf7ed,stroke:#2f855a,color:#172033;
  classDef error fill:#fde8e8,stroke:#c53030,color:#172033;
```

Avoid decorative gradients, oversized headings, nested cards, and color-heavy themes in program-analysis HTML reports. The diagram should support the explanation, not dominate it.

## Validation Checklist

- Open the HTML in a browser or run the app page when practical.
- Confirm Mermaid renders an SVG diagram instead of showing raw Mermaid syntax.
- Inspect the Mermaid source before rendering: every line containing `["`, `{"`, or `(["` must have a matching closing quote and bracket/brace on the same logical node definition.
- When extracting Mermaid blocks for validation, select elements with the exact `mermaid` class token. Do not treat wrapper classes such as `mermaid-wrap` as diagram source.
- Check desktop and mobile widths for horizontal overflow, clipped labels, and unreadable nodes.
- Confirm the diagram matches the actual code or documented flow.
- If the HTML is meant to be shared offline, note that the CDN dependency requires network access or replace it with a local Mermaid bundle.
