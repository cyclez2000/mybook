"""Anthropic-compatible tool JSON schema definitions.

Each tool is defined with name, description, and input_schema.
Tools are grouped by phase — the scheduler only exposes the
relevant subset to the AI at each stage.
"""

from __future__ import annotations

from typing import Any


# ──────────────────────────────────────────────
# Helper: build a tool definition
# ──────────────────────────────────────────────

def _tool(
    name: str,
    description: str,
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties or {},
            "required": required or [],
        },
    }


# ═══════════════════════════════════════════════════════════════
# General read tools (available in most phases)
# ═══════════════════════════════════════════════════════════════

READ_TOOLS: list[dict[str, Any]] = [
    _tool(
        "read_world",
        "返回 world.md 全文，包含世界观设定、主题、文风样本。",
    ),
    _tool(
        "read_outline",
        "按指定粒度返回大纲。level='scene'（默认）返回完整大纲，'chapter' 返回章节级，'act' 返回幕级。",
        properties={
            "level": {
                "type": "string",
                "enum": ["scene", "chapter", "act"],
                "description": "大纲粒度：scene(完整), chapter(章节级), act(幕级)",
            }
        },
    ),
    _tool(
        "read_character",
        "读取单个角色卡，包含外貌、性格、背景、当前状态等信息。",
        properties={
            "name": {
                "type": "string",
                "description": "角色名称",
            }
        },
        required=["name"],
    ),
    _tool(
        "list_characters",
        "列出所有已创建的角色名称。",
    ),
    _tool(
        "read_scene",
        "读取某个场景的全文。",
        properties={
            "scene_id": {
                "type": "string",
                "description": "场景ID，如 scene_001",
            }
        },
        required=["scene_id"],
    ),
    _tool(
        "read_scene_summary",
        "读取某个场景的摘要（含关键事件、字数、结尾氛围）。",
        properties={
            "scene_id": {
                "type": "string",
                "description": "场景ID",
            }
        },
        required=["scene_id"],
    ),
    _tool(
        "list_recent_summaries",
        "返回最近 n 个场景的摘要（按写作顺序），n 默认为 5。",
        properties={
            "n": {
                "type": "integer",
                "description": "返回最近几个场景的摘要，默认 5",
            }
        },
    ),
    _tool(
        "read_foreshadowing",
        "读取伏笔表。status 可选 'planted'（未回收）、'paid_off'（已回收）、'all'（全部）。",
        properties={
            "status": {
                "type": "string",
                "enum": ["planted", "paid_off", "all"],
                "description": "筛选伏笔状态",
            }
        },
    ),
]


# ═══════════════════════════════════════════════════════════════
# Phase 1: Worldbuilding
# ═══════════════════════════════════════════════════════════════

WORLDBUILDING_TOOLS: list[dict[str, Any]] = [
    _tool(
        "write_world",
        "写入/覆盖世界观文档 world.md。应包含：核心设定（3-5条）、主题、文风样本（一段200字示范文字）。Markdown 格式。",
        properties={
            "content": {
                "type": "string",
                "description": "world.md 的完整内容（Markdown）",
            }
        },
        required=["content"],
    ),
    _tool(
        "create_character",
        "创建新角色卡。JSON 文件将保存到 characters/{name}.json。",
        properties={
            "name": {"type": "string", "description": "角色姓名"},
            "role": {"type": "string", "description": "角色定位：主角、配角、反派等"},
            "appearance": {"type": "string", "description": "外貌描述"},
            "personality": {"type": "string", "description": "性格特征"},
            "background": {"type": "string", "description": "背景故事"},
            "arc_notes": {"type": "string", "description": "角色弧光/成长轨迹"},
        },
        required=["name", "role"],
    ),
]


# ═══════════════════════════════════════════════════════════════
# Phase 2: Outlining
# ═══════════════════════════════════════════════════════════════

OUTLINING_TOOLS: list[dict[str, Any]] = [
    _tool("read_world", "读取世界观文档"),
    _tool("list_characters", "列出所有角色"),
    *[t for t in READ_TOOLS if t["name"] == "read_character"],
    _tool(
        "write_outline",
        "写入完整大纲。格式为 JSON，包含 premise、theme、acts 数组。每个 act 包含 chapters，每个 chapter 包含 scenes。",
        properties={
            "outline": {
                "type": "object",
                "description": "完整的大纲 JSON 对象",
            }
        },
        required=["outline"],
    ),
]


# ═══════════════════════════════════════════════════════════════
# Phase 3: Writing
# ═══════════════════════════════════════════════════════════════

WRITING_TOOLS: list[dict[str, Any]] = [
    _tool(
        "get_writing_context",
        "【最重要】获取当前场景所需的全部上下文，包括：压缩版世界观(500字)、当前场景计划、上一个场景全文、更早场景摘要、相关角色卡、待回收伏笔、文风样本。写场景前必须先调用此工具。",
        properties={
            "scene_id": {
                "type": "string",
                "description": "当前要写的场景ID",
            }
        },
        required=["scene_id"],
    ),
    *[t for t in READ_TOOLS if t["name"] in ("read_character", "read_scene")],
    _tool(
        "write_scene",
        "写入场景正文。内置字数校验：偏离目标超过30%时会返回警告。使用 Markdown 格式。",
        properties={
            "scene_id": {
                "type": "string",
                "description": "场景ID",
            },
            "content": {
                "type": "string",
                "description": "场景正文（Markdown）",
            },
        },
        required=["scene_id", "content"],
    ),
]


# ═══════════════════════════════════════════════════════════════
# Phase 3b: Summarization (runs right after writing)
# ═══════════════════════════════════════════════════════════════

SUMMARIZATION_TOOLS: list[dict[str, Any]] = [
    _tool(
        "read_scene",
        "读取刚写完的场景全文，以便准确总结。",
        properties={
            "scene_id": {"type": "string", "description": "场景ID"},
        },
        required=["scene_id"],
    ),
    _tool(
        "summarize_scene",
        "记录场景摘要。summary 控制在 50 字以内，key_events 列出本场景发生的关键事件，ends_with 描述结尾的情绪/悬念。只记录实际发生的，不要编造。",
        properties={
            "scene_id": {"type": "string", "description": "场景ID"},
            "summary": {"type": "string", "description": "场景摘要，≤50字"},
            "key_events": {
                "type": "array",
                "items": {"type": "string"},
                "description": "本场景的关键事件列表",
            },
            "ends_with": {"type": "string", "description": "场景结尾的氛围/悬念描述"},
        },
        required=["scene_id", "summary"],
    ),
    _tool(
        "update_character_state",
        "增量更新角色当前状态：位置、能力变化、关系变化。只传有变化的字段。",
        properties={
            "name": {"type": "string", "description": "角色名称"},
            "location": {"type": "string", "description": "新位置（如有变化）"},
            "abilities_added": {
                "type": "array",
                "items": {"type": "string"},
                "description": "新增的能力/技能",
            },
            "abilities_removed": {
                "type": "array",
                "items": {"type": "string"},
                "description": "失去的能力/技能",
            },
            "relationships_changed": {
                "type": "object",
                "description": "关系变化，如 {\"张三\": \"从陌生变为盟友\"}",
            },
            "notes": {"type": "string", "description": "角色发展备注"},
        },
        required=["name"],
    ),
    _tool(
        "plant_foreshadowing",
        "登记新伏笔。当场景中埋下对后续剧情有暗示作用的细节时调用。",
        properties={
            "description": {"type": "string", "description": "伏笔内容描述"},
            "intended_payoff_scene": {
                "type": "string",
                "description": "计划在哪个场景回收（可选）",
            },
        },
        required=["description"],
    ),
    _tool(
        "pay_off_foreshadowing",
        "标记伏笔已回收。当场景中回应了之前埋下的伏笔时调用。",
        properties={
            "foreshadowing_id": {"type": "string", "description": "伏笔ID，如 fs_001"},
            "scene_id": {"type": "string", "description": "当前场景ID"},
        },
        required=["foreshadowing_id", "scene_id"],
    ),
    _tool(
        "add_timeline_event",
        "追加时间线事件。记录故事中发生的重要时间节点。",
        properties={
            "scene_id": {"type": "string", "description": "场景ID"},
            "event": {"type": "string", "description": "事件描述"},
            "in_story_time": {"type": "string", "description": "故事内时间，如'第三天傍晚'"},
        },
        required=["scene_id", "event"],
    ),
]


# ═══════════════════════════════════════════════════════════════
# Phase 4: Review
# ═══════════════════════════════════════════════════════════════

REVIEW_TOOLS: list[dict[str, Any]] = [
    _tool(
        "list_all_scenes",
        "列出所有场景ID（按写作顺序）。",
    ),
    *[t for t in READ_TOOLS if t["name"] in ("read_scene", "read_scene_summary")],
    _tool(
        "check_foreshadowing_unpaid",
        "返回所有尚未回收的伏笔。",
    ),
    _tool(
        "check_character_consistency",
        "检查某角色的出场历史和状态变化，用于发现行为/能力前后矛盾。",
        properties={
            "name": {"type": "string", "description": "角色名称"},
        },
        required=["name"],
    ),
    _tool(
        "flag_issue",
        "登记发现的问题。issue_type 可选：foreshadowing_unpaid, character_inconsistency, timeline_conflict, pacing, other。只记录问题，不直接修改。",
        properties={
            "scene_id": {"type": "string", "description": "问题所在的场景ID"},
            "issue_type": {
                "type": "string",
                "enum": ["foreshadowing_unpaid", "character_inconsistency", "timeline_conflict", "pacing", "other"],
                "description": "问题类型",
            },
            "description": {"type": "string", "description": "问题描述"},
        },
        required=["scene_id", "issue_type", "description"],
    ),
]


# ═══════════════════════════════════════════════════════════════
# Phase 5: Revision
# ═══════════════════════════════════════════════════════════════

REVISION_TOOLS: list[dict[str, Any]] = [
    *[t for t in READ_TOOLS if t["name"] in ("read_scene",)],
    *[t for t in WRITING_TOOLS if t["name"] == "get_writing_context"],
    _tool(
        "apply_revision",
        "修订场景内容。传入新内容和修改原因。会覆盖原场景文件。",
        properties={
            "scene_id": {"type": "string", "description": "要修订的场景ID"},
            "new_content": {"type": "string", "description": "修订后的完整正文"},
            "reason": {"type": "string", "description": "修订原因"},
        },
        required=["scene_id", "new_content", "reason"],
    ),
]


# ═══════════════════════════════════════════════════════════════
# Phase tools mapping
# ═══════════════════════════════════════════════════════════════

PHASE_TOOLS: dict[str, list[dict[str, Any]]] = {
    "worldbuilding": WORLDBUILDING_TOOLS,
    "outlining": OUTLINING_TOOLS,
    "writing": WRITING_TOOLS,
    "summarizing": SUMMARIZATION_TOOLS,
    "reviewing": REVIEW_TOOLS,
    "revising": REVISION_TOOLS,
}
