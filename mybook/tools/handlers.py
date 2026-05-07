"""Tool handler functions.

Each handler receives the tool name and input arguments,
calls the appropriate BibleManager method, and returns
the result. This is the bridge between AI tool calls and
the file system.
"""

from __future__ import annotations

from typing import Any

from ..bible.manager import BibleManager


def handle_tool_call(
    bible: BibleManager,
    tool_name: str,
    tool_input: dict[str, Any],
) -> str:
    """Route a tool call to the appropriate handler and return JSON result."""

    handler = _HANDLERS.get(tool_name)
    if handler is None:
        return _error(f"未知工具: {tool_name}")

    try:
        result = handler(bible, tool_input)
        return _success(result)
    except Exception as e:
        return _error(f"工具 {tool_name} 执行失败: {str(e)}")


def _success(data: Any) -> str:
    """Format successful result as JSON string."""
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)


def _error(message: str) -> str:
    """Format error result as JSON string."""
    import json

    return json.dumps({"error": message}, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# Handler implementations
# ═══════════════════════════════════════════════════════════════


def _read_world(bible: BibleManager, inp: dict) -> str:
    return bible.read_world()


def _read_outline(bible: BibleManager, inp: dict) -> dict:
    level = inp.get("level", "scene")
    return bible.read_outline(level=level)


def _read_character(bible: BibleManager, inp: dict) -> dict | None:
    name = inp["name"]
    result = bible.read_character(name)
    if result is None:
        return {"error": f"角色 '{name}' 不存在"}
    return result


def _list_characters(bible: BibleManager, inp: dict) -> list[str]:
    return bible.list_characters()


def _read_scene(bible: BibleManager, inp: dict) -> str:
    scene_id = inp["scene_id"]
    text = bible.read_scene(scene_id)
    if not text:
        return {"error": f"场景 {scene_id} 不存在或为空"}
    return text


def _read_scene_summary(bible: BibleManager, inp: dict) -> dict | None:
    scene_id = inp["scene_id"]
    result = bible.read_scene_summary(scene_id)
    if result is None:
        return {"error": f"场景 {scene_id} 的摘要不存在"}
    return result


def _list_recent_summaries(bible: BibleManager, inp: dict) -> list[dict]:
    n = inp.get("n", 5)
    return bible.list_recent_summaries(n=n)


def _read_foreshadowing(bible: BibleManager, inp: dict) -> list[dict]:
    status = inp.get("status", "all")
    return bible.read_foreshadowing(status=status)


def _write_world(bible: BibleManager, inp: dict) -> dict:
    content = inp["content"]
    bible.write_world(content)
    return {"status": "ok", "message": "世界观已保存"}


def _create_character(bible: BibleManager, inp: dict) -> dict:
    bible.create_character(
        name=inp["name"],
        role=inp["role"],
        appearance=inp.get("appearance", ""),
        personality=inp.get("personality", ""),
        background=inp.get("background", ""),
        arc_notes=inp.get("arc_notes", ""),
    )
    return {"status": "ok", "message": f"角色 '{inp['name']}' 已创建"}


def _write_outline(bible: BibleManager, inp: dict) -> dict:
    outline = inp["outline"]
    bible.write_outline(outline)
    return {"status": "ok", "message": "大纲已保存"}


def _revise_scene_plan(bible: BibleManager, inp: dict) -> dict:
    scene_id = inp["scene_id"]
    fields = {k: v for k, v in inp.items() if k != "scene_id"}
    result = bible.revise_scene_plan(scene_id, **fields)
    if result is None:
        return {"error": f"场景 {scene_id} 不存在"}
    return {"status": "ok", "scene": result}


def _get_writing_context(bible: BibleManager, inp: dict) -> dict:
    scene_id = inp["scene_id"]
    return bible.get_writing_context(scene_id)


def _write_scene(bible: BibleManager, inp: dict) -> dict:
    scene_id = inp["scene_id"]
    content = inp["content"]
    result = bible.write_scene(scene_id, content)
    return result


def _summarize_scene(bible: BibleManager, inp: dict) -> dict:
    return bible.summarize_scene(
        scene_id=inp["scene_id"],
        summary=inp["summary"],
        key_events=inp.get("key_events"),
        ends_with=inp.get("ends_with", ""),
    )


def _update_character_state(bible: BibleManager, inp: dict) -> dict:
    result = bible.update_character_state(
        name=inp["name"],
        location=inp.get("location"),
        abilities_added=inp.get("abilities_added"),
        abilities_removed=inp.get("abilities_removed"),
        relationships_changed=inp.get("relationships_changed"),
        notes=inp.get("notes"),
    )
    if result is None:
        return {"error": f"角色 '{inp['name']}' 不存在"}
    return {"status": "ok", "character": result}


def _plant_foreshadowing(bible: BibleManager, inp: dict) -> dict:
    return bible.plant_foreshadowing(
        description=inp["description"],
        intended_payoff_scene=inp.get("intended_payoff_scene", ""),
    )


def _pay_off_foreshadowing(bible: BibleManager, inp: dict) -> dict:
    result = bible.pay_off_foreshadowing(
        foreshadowing_id=inp["foreshadowing_id"],
        scene_id=inp["scene_id"],
    )
    if result is None:
        return {"error": f"伏笔 {inp['foreshadowing_id']} 不存在"}
    return {"status": "ok", "foreshadowing": result}


def _add_timeline_event(bible: BibleManager, inp: dict) -> dict:
    return bible.add_timeline_event(
        scene_id=inp["scene_id"],
        event=inp["event"],
        in_story_time=inp.get("in_story_time", ""),
    )


def _list_all_scenes(bible: BibleManager, inp: dict) -> list[str]:
    return bible.list_all_scenes()


def _check_foreshadowing_unpaid(bible: BibleManager, inp: dict) -> list[dict]:
    return bible.check_foreshadowing_unpaid()


def _check_character_consistency(bible: BibleManager, inp: dict) -> dict:
    result = bible.check_character_consistency(inp["name"])
    if result is None:
        return {"error": f"角色 '{inp['name']}' 不存在"}
    return result


def _flag_issue(bible: BibleManager, inp: dict) -> dict:
    return bible.flag_issue(
        scene_id=inp["scene_id"],
        issue_type=inp["issue_type"],
        description=inp["description"],
    )


def _apply_revision(bible: BibleManager, inp: dict) -> dict:
    return bible.apply_revision(
        scene_id=inp["scene_id"],
        new_content=inp["new_content"],
        reason=inp["reason"],
    )


# ── Handler registry ─────────────────────

_HANDLERS: dict[str, Any] = {
    "read_world": _read_world,
    "read_outline": _read_outline,
    "read_character": _read_character,
    "list_characters": _list_characters,
    "read_scene": _read_scene,
    "read_scene_summary": _read_scene_summary,
    "list_recent_summaries": _list_recent_summaries,
    "read_foreshadowing": _read_foreshadowing,
    "write_world": _write_world,
    "create_character": _create_character,
    "write_outline": _write_outline,
    "revise_scene_plan": _revise_scene_plan,
    "get_writing_context": _get_writing_context,
    "write_scene": _write_scene,
    "summarize_scene": _summarize_scene,
    "update_character_state": _update_character_state,
    "plant_foreshadowing": _plant_foreshadowing,
    "pay_off_foreshadowing": _pay_off_foreshadowing,
    "add_timeline_event": _add_timeline_event,
    "list_all_scenes": _list_all_scenes,
    "check_foreshadowing_unpaid": _check_foreshadowing_unpaid,
    "check_character_consistency": _check_character_consistency,
    "flag_issue": _flag_issue,
    "apply_revision": _apply_revision,
}
