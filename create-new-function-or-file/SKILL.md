---
name: create-new-function-or-file
description: 新建源文件或函数时，统一署名规范为 lichunjiang。非沃莱科技项目的代码不写 Copyright 公司行。当用户要求创建新文件、新函数、新增模块或生成代码框架时，确保文件头部署名和函数注释符合此规范。
---

# 代码署名规范

## 署名规则

所有新建的文件和函数，署名统一使用 **lichunjiang**。

### 文件头部注释模板

```c
/******************************************************************************
 * @file    filename.c
 * @author  lichunjiang
 * @version V1.0.0
 * @date    YYYY-MM-DD
 * @brief   一句话描述文件功能
 ******************************************************************************/
```

### 函数注释模板

```c
/**
 * @brief  函数功能简述
 * @param  param1 参数1说明
 * @param  param2 参数2说明
 * @retval 返回值说明
 * @note   注意事项（可选）
 */
```

## Copyright 规则

- **沃莱科技（Woleitech）项目**：文件头部保留 Copyright 公司行
  ```c
  * @copyright Copyright (c) 20XX 沃莱科技
  ```
- **非沃莱科技项目**：不写 Copyright 公司行，只保留 @author lichunjiang

## 适用范围

- 新建 C/C++ 源文件（.c / .h / .cpp / .hpp）
- 新建 Python 脚本（.py）—— 使用对应格式的文件头
- 新建汇编文件（.s / .asm）
- 任何用户要求"新建文件"、"创建函数"、"生成代码框架"的场景
