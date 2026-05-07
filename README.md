# mybook / 我的书

**AI-powered infinite-flow novel writing tool** — executed by your AI agent (Claude, GPT, Hermes, Clawbot, etc.). Zero API keys.

**AI 驱动的无限流小说写作工具** —— 由你的 AI Agent（Claude、GPT、Hermes、Clawbot 等）代理执行。零 API Key。

---

## Core Idea / 核心理念

Not "AI writes your novel". It's **"AI as an agent in your toolchain"**:

不是"AI 替人写小说"，而是 **"AI 作为工具链中的代理"**：

```
you give intent → mybook generates task → AI agent executes → files on disk → you review → next round
你给意图 → mybook 出任务 → AI Agent 执行 → 文件落地 → 你审阅 → 下一轮
```

Any AI agent that can read/write files can execute mybook tasks. mybook provides structured context — worldbuilding, outlining, scene writing, foreshadowing tracking, review, revision — each step with explicit **phase, constraints, and expected outputs**.

任何能读写文件的 AI Agent 都可以执行 mybook 的任务。mybook 负责提供结构化上下文——世界观设计、大纲规划、场景写作、伏笔追踪、审校修订——每一步都有明确的**阶段、约束、预期产出**。

## Features / 特性

- **Zero config** — No API key, no model setup. Your AI agent is the executor. / **零配置** — 不需要 API Key，你的 AI Agent 就是执行者
- **Story bible** — File-system bible directory maintains world, characters, outline, scenes, foreshadowing, timeline in consistent sync. / **故事圣经** — 文件系统维护世界观、角色卡、大纲、场景、伏笔、时间线的完整一致
- **5-phase pipeline** — Worldbuilding → Outlining → Scene writing → Review → Revision. / **五阶段流水线** — 世界观构建 → 大纲规划 → 逐场景写作 → 全文审校 → 修订
- **Instance card pool** (infinite-flow mode) — `mybook card draw` randomly draws from horror/sci-fi/mystery/historical/survival cards. / **副本卡池**（无限流模式）—— 随机抽取恐怖/科幻/悬疑/历史/生存类副本卡
- **Foreshadowing tracker** — Auto-tracks which scene planted, planned payoff, and paid-off status for every thread. / **伏笔追踪** — 自动追踪每个伏笔的埋点、计划回收点、是否已回收
- **Human review checkpoint** — Pauses after outlining for confirmation, preventing direction drift. / **人工审核断点** — 大纲完成后暂停确认，避免方向偏差

## Quick Start / 快速开始

```bash
# Install / 安装
pip install -e .
# or / 或者
uv pip install -e .

# Create project / 初始化项目
mybook init my_novel

# Generate task for current phase → give .mybook/task.md to your AI agent
# 生成当前阶段任务 → 把 .mybook/task.md 给 AI Agent
mybook task

# Check progress / 查看进度
mybook status

# Compile manuscript / 编译手稿
mybook compile
```

### Infinite-flow mode / 无限流模式

```bash
# Init card pool (5 preset classic instances)
# 初始化卡池（预置 5 张经典副本：恐怖病院、赛博废墟、镜中公寓、明朝诏狱、深海平台）
mybook card pool-init

# Randomly draw an unused card / 随机抽取一张未用过的副本卡
mybook card draw

# View all cards / 查看卡池
mybook card list

# Add custom card / 手动添加自定义副本卡
mybook card add-instance -n "Instance Name" -t "horror" -l 5 -p "One-line premise"
```

## Project Structure / 项目结构

```
mybook/
├── mybook/
│   ├── main.py              # CLI entry (click) / CLI 入口
│   ├── config.py            # Config / 配置
│   ├── task_generator.py    # Task generator (state machine + context assembly)
│   │                         任务生成器（状态机 + 上下文组装）
│   ├── bible/
│   │   ├── schemas.py       # Pydantic data models / 数据模型
│   │   └── manager.py       # Bible CRUD engine / 圣经 CRUD 引擎
│   ├── tools/
│   │   ├── definitions.py   # 24 tool JSON schemas / 24 个工具的 JSON Schema
│   │   └── handlers.py      # Tool executors / 工具执行器
│   └── prompts/
│       └── system_prompts.py # 6 phase system prompts / 6 个阶段的 System Prompt
├── pyproject.toml
└── requirements.txt
```

## Example Works / 示例作品

### 《往生章》 (Dao Collapse Era · Cultivation Fantasy / 道崩纪元 · 修仙)

- 36 scenes, ~48,000 Chinese characters / 36 场景，~48,000 字
- 3-act structure: Ruin relic-hunter → Abyss truth → New Heavenly Dao / 三幕：废墟猎章人 → 幽墟真相 → 新天道重建
- 11 foreshadowing threads, all paid off / 11 个伏笔全部回收
- Compiled at `my_novel/manuscript.md`

### 《无限监狱》 (Infinite Prison · Horror/Mystery / 无限流 · 悬疑)

- Premise: Infinite instances are a prison. The protagonist is a "prison guard" who can see the underlying code — and discovers his own name on the deepest cell's seal. / 无限副本是一座监狱。主角是能看见底层代码的"狱警"——最深层的牢房封印上，刻着他自己的名字。
- Instance 1: Horror Hospital (complete, 4/4 scenes) / 副本1：恐怖病院（已通关）
- Card pool: 5 instance cards, 3 remaining / 卡池：5 张副本卡，3 张待抽取

## Design Philosophy / 工作流设计

The entire tool answers one question: **What does an AI need most when writing a long novel?**

整个工具围绕一个问题设计：**AI 在写长篇小说时最需要什么？**

Answer: **Context management**. The enemy of long-form fiction isn't "can't write" — it's "forgot what happened 20 scenes ago".

答案是**上下文管理**。长篇小说的敌人不是"写不出来"，而是"写到后面忘了前面"。

| Problem / 问题 | Solution / 方案 |
|---|---|
| Scene 20 forgets the foreshadowing from scene 3 | `foreshadowing.json` auto-tracking / 自动追踪 |
| Character behaves inconsistently | `character.current_state` incremental updates / 增量更新 |
| Too much context degrades AI output quality | `get_writing_context` precise packaging / 精准打包 |
| Forgetting to summarize breaks scene transitions | Writing and summarization as separate calls / 写作与总结分两次调用 |
| Outline drifts off-direction | Human review checkpoint after outlining / 大纲后人工审核 |

## Why No API Key / 为什么不用 API Key

Traditional AI writing tools: `your code → call OpenAI/Anthropic API → text comes back`

传统 AI 写作工具：`你的代码 → 调 API → 文本回来`

mybook: `your code → generate task → you give task to AI agent → agent writes files directly`

mybook：`你的代码 → 出任务 → 把任务给 AI Agent → Agent 直接写文件`

Benefits / 优势：
- Zero API cost / 不花 API 费用
- No token limits / 没有 token 限制
- Pause, modify, resume anytime / 随时中断、修改、继续
- All intermediate artifacts (world, outline, scenes) stay on your filesystem / 所有中间产物留在你的文件系统里

## License / 许可

MIT
