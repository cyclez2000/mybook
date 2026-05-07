# mybook

**AI 驱动的无限流小说写作工具** —— 由 Sisyphus 代理执行，无需任何 API Key。

## 核心理念

不是"AI 替人写小说"，而是 **"AI 作为工具链中的代理"**：

```
你给意图 → mybook 出任务 → Sisyphus 执行 → 文件落地 → 你审阅 → 下一轮
```

Sisyphus 是你的专属 AI Agent，直接操作文件系统。mybook 负责提供结构化的任务上下文——世界观设计、大纲规划、场景写作、伏笔追踪、审校修订——每一步都有明确的**阶段、约束、预期产出**。

## 特性

- **零配置**：不需要 API Key，不需要模型配置。Sisyphus 就是你的 AI
- **故事圣经**：文件系统的 bible 目录维护世界观、角色卡、大纲、场景、伏笔、时间线的完整一致
- **五阶段流水线**：世界观构建 → 大纲规划 → 逐场景写作 → 全文审校 → 修订
- **副本卡池**（无限流专属）：`mybook card draw` 随机抽取副本卡，支持恐怖/科幻/悬疑/历史等多类型
- **伏笔追踪**：11 个伏笔全部自动追踪埋在哪个场景、计划在哪个场景回收、是否已回收
- **人工审核断点**：大纲完成后暂停确认，避免方向偏差

## 快速开始

```bash
# 安装
pip install -e .
# 或者
uv pip install -e .

# 初始化项目
mybook init my_novel

# 生成当前阶段任务 → 把 .mybook/task.md 给 Sisyphus
mybook task

# 查看进度
mybook status

# 编译手稿
mybook compile
```

### 无限流模式

```bash
# 初始化卡池（预置5张经典副本：恐怖病院、赛博废墟、镜中公寓、明朝诏狱、深海平台）
mybook card pool-init

# 随机抽取一张未用过的副本卡
mybook card draw

# 查看卡池
mybook card list

# 手动添加自定义副本卡
mybook card add-instance -n "副本名" -t "horror" -l 5 -p "一句话描述"
```

## 项目结构

```
mybook/
├── mybook/
│   ├── main.py              # CLI 入口（click）
│   ├── config.py            # 配置
│   ├── task_generator.py    # 任务生成器（状态机 + 上下文组装）
│   ├── bible/
│   │   ├── schemas.py       # Pydantic 数据模型
│   │   └── manager.py       # 圣经 CRUD 引擎
│   ├── tools/
│   │   ├── definitions.py   # 24 个工具的 JSON Schema
│   │   └── handlers.py      # 工具执行器
│   └── prompts/
│       └── system_prompts.py # 6 个阶段的 System Prompt
├── pyproject.toml
└── requirements.txt
```

## 已完成的示例作品

### 《往生章》（道崩纪元 · 修仙题材）

- 36 场景，~48,000 字
- 三幕结构：废墟猎章人 → 幽墟真相 → 新天道重建
- 11 个伏笔全部回收
- 已编译到 `my_novel/manuscript.md`

### 《无限监狱》（无限流 · 悬疑题材）

- 世界观：无限副本是一座监狱，主角是能看见底层代码的"狱警"
- 钩子：最深层的牢房封印上刻着主角自己的名字
- 副本1：恐怖病院（已通关，4/4 场景）
- 卡池：5 张副本卡，3 张待抽取

## 工作流设计

整个工具围绕一个核心问题设计：**AI 在写长篇小说时最需要什么？**

答案是**上下文管理**。长篇小说最大的敌人不是"写不出来"，而是"写到后面忘了前面"。

mybook 的解决方案：

| 问题 | 方案 |
|---|---|
| 写到第 20 个场景，忘了第 3 个场景的伏笔 | `foreshadowing.json` 自动追踪 |
| 角色行为前后矛盾 | `character.current_state` 增量更新 |
| AI 一次性拿太多上下文导致质量下降 | `get_writing_context` 精准打包 |
| 写完场景忘了总结 → 衔接断裂 | 写作和总结分两次独立调用 |
| 大纲偏离方向 | 大纲完成后人工审核断点 |

## 为什么不用 API Key

传统 AI 写作工具的模式：你的代码 → 调 OpenAI/Anthropic API → 文本回来。

mybook 的模式：你的代码 → 出任务 → 你把任务给我 → 我直接操作文件。

优势：
- 不花 API 费用
- 不用管 token 限制
- 可以随时中断、修改、继续
- 所有中间产物（世界观、大纲、场景）都留在你的文件系统里

## License

MIT
