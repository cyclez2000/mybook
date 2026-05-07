# mybook

> [中文](README_CN.md)

**AI-powered infinite-flow novel writing tool** — executed by your AI agent (Claude, GPT, Hermes, Clawbot, etc.). Zero API keys.

## Core Idea

Not "AI writes your novel". It's **"AI as an agent in your toolchain"**:

```
you give intent → mybook generates task → AI agent executes → files on disk → you review → next round
```

Any AI agent that can read/write files can execute mybook tasks. mybook provides structured context — worldbuilding, outlining, scene writing, foreshadowing tracking, review, revision — each step with explicit **phase, constraints, and expected outputs**.

## Features

- **Zero config** — No API key, no model setup. Your AI agent is the executor.
- **Story bible** — File-system bible directory maintains world, characters, outline, scenes, foreshadowing, and timeline in consistent sync.
- **5-phase pipeline** — Worldbuilding → Outlining → Scene writing → Review → Revision.
- **Instance card pool** (infinite-flow) — `mybook card draw` randomly draws from horror/sci-fi/mystery/historical/survival cards.
- **Foreshadowing tracker** — Auto-tracks which scene planted, planned payoff, and paid-off status for every thread.
- **Human review checkpoint** — Pauses after outlining for confirmation, preventing direction drift.

## Quick Start

```bash
# Install
pip install -e .
# or
uv pip install -e .

# Create project
mybook init my_novel

# Generate task for current phase → give .mybook/task.md to your AI agent
mybook task

# Check progress
mybook status

# Compile manuscript
mybook compile
```

### Infinite-flow mode

```bash
# Init card pool (5 preset classic instances: Horror Hospital, Cyberpunk Ruins, Mirror Apartment, Ming Dynasty Prison, Deepsea Rig)
mybook card pool-init

# Randomly draw an unused card
mybook card draw

# View all cards
mybook card list

# Add custom card
mybook card add-instance -n "Instance Name" -t "horror" -l 5 -p "One-line premise"
```

## Project Structure

```
mybook/
├── mybook/
│   ├── main.py              # CLI entry (click)
│   ├── config.py            # Config
│   ├── task_generator.py    # Task generator (state machine + context assembly)
│   ├── bible/
│   │   ├── schemas.py       # Pydantic data models
│   │   └── manager.py       # Bible CRUD engine
│   ├── tools/
│   │   ├── definitions.py   # 24 tool JSON schemas
│   │   └── handlers.py      # Tool executors
│   └── prompts/
│       └── system_prompts.py # 6 phase system prompts
├── pyproject.toml
└── requirements.txt
```

## Example Works

### 《往生章》 (Dao Collapse Era · Cultivation Fantasy)

- 36 scenes, ~48,000 Chinese characters
- 3-act structure: Ruin relic-hunter → Abyss truth → New Heavenly Dao
- 11 foreshadowing threads, all paid off
- Compiled at `my_novel/manuscript.md`

### 《无限监狱》 (Infinite Prison · Horror/Mystery)

- Premise: Infinite instances are a prison. The protagonist is a "guard" who can see the underlying code — and discovers his own name on the deepest cell's seal.
- Instance 1: Horror Hospital (complete, 4/4 scenes)
- Card pool: 5 instance cards, 3 remaining

## Design Philosophy

The entire tool answers one question: **What does an AI need most when writing a long novel?**

Answer: **Context management**. The enemy of long-form fiction isn't "can't write" — it's "forgot what happened 20 scenes ago".

| Problem | Solution |
|---|---|
| Scene 20 forgets the foreshadowing from scene 3 | `foreshadowing.json` auto-tracking |
| Character behaves inconsistently | `character.current_state` incremental updates |
| Too much context degrades AI output quality | `get_writing_context` precise packaging |
| Forgetting to summarize breaks scene transitions | Writing and summarization as separate calls |
| Outline drifts off-direction | Human review checkpoint after outlining |

## Why No API Key

Traditional AI writing tools: `your code → call OpenAI/Anthropic API → text comes back`

mybook: `your code → generate task → you give task to AI agent → agent writes files directly`

Benefits:
- Zero API cost
- No token limits
- Pause, modify, resume anytime
- All intermediate artifacts (world, outline, scenes) stay on your filesystem

## License

MIT
