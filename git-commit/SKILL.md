---
name: git-commit
description: Analyze workspace changes, create atomic commits following Conventional Commits specification with Chinese messages. Supports interactive staging, change grouping, and automatic commit message generation.
---

## 触发条件

当用户提到以下任一关键词时激活：
- "提交", "commit", "git commit"
- "保存更改", "提交代码"
- "原子化提交", "atomic commit"
- "规范提交", "conventional commit"
- "生成提交信息", "写提交信息"

## 执行流程

### 步骤 1：检查工作区状态

```bash
git status --short          # 查看修改的文件列表
git diff --stat             # 查看修改统计
git diff --cached --stat    # 查看已暂存的修改
```

### 步骤 2：分析修改内容

对每处修改进行分类：
- **新增功能** → `feat`
- **修复 bug** → `fix`
- **重构代码** → `refactor`
- **性能优化** → `perf`
- **文档更新** → `docs`
- **代码风格** → `style`
- **测试相关** → `test`
- **构建/工具** → `chore`
- **依赖更新** → `deps`

### 步骤 3：原子化分组

将相关修改分组，每组应满足：
1. **单一职责**：每组只包含一个逻辑变更
2. **独立可运行**：提交后项目仍可编译/运行
3. **完整闭环**：包含变更本身及相关测试/文档

分组示例：
```
组 1: feat(mic) - 新增麦克风驱动
  - main/mic_handler.c (新增)
  - main/include/mic_handler.h (新增)
  - main/CMakeLists.txt (添加源文件)

组 2: feat(voice) - 新增语音识别 API
  - main/voice_api.c (新增)
  - main/include/voice_api.h (新增)

组 3: refactor(button) - 按钮支持长按/短按
  - main/button_handler.c (修改)

组 4: chore(build) - 构建配置更新
  - main/CMakeLists.txt (添加依赖)
  - main/main.c (初始化调用)
```

### 步骤 4：交互式确认

向用户展示分组方案，询问：
1. 是否同意此分组？
2. 是否有遗漏或错误？
3. 是否调整某些文件的归属？

### 步骤 5：生成提交信息

根据每组内容自动生成提交信息，格式：

```
<type>[(<scope>)]: <subject>

<body>

<footer>
```

#### 类型说明

| 类型 | 说明 | 示例 |
|-----|------|------|
| **feat** | 新功能 | `feat(mic): 新增PDM麦克风驱动` |
| **fix** | 修复bug | `fix(button): 修复按钮抖动问题` |
| **refactor** | 重构代码 | `refactor(api): 重构HTTP请求逻辑` |
| **perf** | 性能优化 | `perf(camera): 优化图像捕获速度` |
| **docs** | 文档更新 | `docs(readme): 更新API使用说明` |
| **style** | 代码格式 | `style(main): 统一代码缩进` |
| **test** | 测试相关 | `test(mic): 添加麦克风单元测试` |
| **chore** | 构建/工具 | `chore(build): 更新CMakeLists.txt` |
| **deps** | 依赖更新 | `deps(camera): 升级esp32-camera组件` |

#### Subject 规范

1. **中文描述**，简洁明了（不超过50字符）
2. 使用**祈使句**（如"添加"而非"添加了"）
3. **不加句号**
4. 首字母**不大写**

#### Body 规范（可选）

- 详细描述变更原因和内容
- 每行不超过72字符
- 使用 `- ` 列出变更点

#### Footer 规范（可选）

- `BREAKING CHANGE:` 标记不兼容变更
- `Closes #123` 关联 issue
- `Co-authored-by:` 标记协作者

### 步骤 6：执行提交

```bash
# 按组暂存并提交
git add <files>
git commit -m "<type>[(<scope>)]: <subject>"

# 或带 body
git commit -m "<type>[(<scope>)]: <subject>" -m "<body>"
```

## 自动检测规则

### 文件类型映射

| 文件模式 | 推断类型 | 推断 scope |
|---------|---------|-----------|
| `*.c`, `*.cpp`, `*.h` | 看上下文 | 所在目录/模块 |
| `CMakeLists.txt` | `chore` | `build` |
| `*.md`, `*.rst` | `docs` | 相关模块 |
| `*.yml`, `*.yaml` | `chore` | `ci` 或 `config` |
| `package.json`, `*.toml` | `deps` | `deps` |
| `test/*`, `*_test.c` | `test` | 被测模块 |

### 修改内容映射

| 修改特征 | 推断类型 |
|---------|---------|
| 新增函数/接口 | `feat` |
| 修改函数实现 | `fix` 或 `refactor` |
| 删除废弃代码 | `refactor` |
| 修改变量命名 | `style` |
| 添加注释 | `docs` |
| 更新版本号 | `chore` |

## 示例交互

**用户**: 提交一下当前的修改

**Assistant**:
1. 运行 `git status --short` 查看修改
2. 分析修改内容并分组
3. 展示分组方案：
   ```
   发现 4 组修改：
   
   [组 1] feat(mic): 新增PDM麦克风驱动
   - main/mic_handler.c (新增)
   - main/include/mic_handler.h (新增)
   
   [组 2] feat(voice): 新增百度语音识别API
   - main/voice_api.c (新增)
   - main/include/voice_api.h (新增)
   
   [组 3] refactor(button): 支持长按/短按识别
   - main/button_handler.c (修改)
   
   [组 4] chore(build): 添加I2S驱动依赖
   - main/CMakeLists.txt (修改)
   - main/main.c (修改)
   
   是否按此方案提交？(y/n/edit)
   ```

**用户**: y

**Assistant**:
```bash
# 执行原子化提交
git add main/mic_handler.c main/include/mic_handler.h
git commit -m "feat(mic): 新增PDM麦克风驱动"

git add main/voice_api.c main/include/voice_api.h
git commit -m "feat(voice): 新增百度语音识别API"

git add main/button_handler.c
git commit -m "refactor(button): 支持长按/短按识别"

git add main/CMakeLists.txt main/main.c
git commit -m "chore(build): 添加I2S驱动依赖"
```

## 注意事项

1. **原子化原则**：每次提交只做一件事，便于回滚和代码审查
2. **不要提交半成品**：确保每次提交后代码可编译/运行
    - 提交第一组修改后
  - stash 剩余的工作区修改
  - 编译验证（确保只有已提交的代码能编译通过）
  - pop stash 恢复剩余修改
  - 继续提交第二组
  - 重复...
3. **敏感信息检查**：提交前检查是否包含密码、密钥等
4. **大文件警惕**：不要提交二进制文件、日志文件到 git
5. **合并提交**：如果用户明确要求，可以合并相关小提交
6. **空提交避免**：如果没有实质修改，不要创建空提交
7. **分支检查**：提交前确认当前分支是否正确