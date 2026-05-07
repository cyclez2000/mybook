"""Task generator — produces Markdown task files for Sisyphus to execute.

Replaces the LLM-calling scheduler. At each phase, this module:
1. Checks the current bible state
2. Determines what needs to be done
3. Assembles context (system prompt, bible excerpts, expected outputs)
4. Outputs a structured Markdown task file

Sisyphus reads the task file, executes the required operations
using his own file tools, and reports completion.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .bible.manager import BibleManager
from .bible.schemas import SceneStatus
from .prompts.system_prompts import MODE_PROMPTS


class TaskGenerator:
    """Generates structured task descriptions for the current phase."""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.bible = BibleManager(root=self.project_dir / "bible")
        self.bible.ensure_dirs()

    # ═══════════════════════════════════════════════
    # Main: determine current phase and generate task
    # ═══════════════════════════════════════════════

    def detect_phase(self) -> str:
        """Determine which phase we should be in based on bible state."""
        if not self.bible.has_world():
            return "worldbuilding"
        if not self.bible.has_outline():
            return "outlining"
        # Check if there are pending scenes
        if self.bible.has_outline():
            outline = self.bible._load_outline()
            pending = [s for s in outline.iter_scenes() if s.status in (SceneStatus.pending, SceneStatus.writing)]
            if pending:
                return "writing"
        # Check for unreviewed issues
        issues = self.bible._load_issues()
        unresolved = issues.unresolved()
        if unresolved:
            return "revising"
        # Default: review
        outline = self.bible._load_outline()
        done = sum(1 for s in outline.iter_scenes() if s.status in (SceneStatus.done, SceneStatus.revised))
        total = outline.total_scenes()
        if total > 0 and done >= total:
            return "reviewing"
        return "writing"

    def generate_task(self, phase: str | None = None) -> str:
        """Generate a Markdown task file for the given phase.

        If phase is None, auto-detects from bible state.
        Returns the task content as a Markdown string.
        """
        if phase is None:
            phase = self.detect_phase()

        generators = {
            "worldbuilding": self._task_worldbuilding,
            "outlining": self._task_outlining,
            "writing": self._task_writing,
            "summarizing": self._task_summarizing,
            "reviewing": self._task_reviewing,
            "revising": self._task_revising,
        }

        gen = generators.get(phase)
        if gen is None:
            return f"# Error\nUnknown phase: {phase}\n\nValid phases: {', '.join(generators.keys())}"

        return gen()

    def write_task_file(self, phase: str | None = None) -> Path:
        """Generate task and write to .mybook/task.md. Returns the path."""
        content = self.generate_task(phase)
        task_dir = self.project_dir / ".mybook"
        task_dir.mkdir(exist_ok=True)
        task_file = task_dir / "task.md"
        task_file.write_text(content, encoding="utf-8")
        return task_file

    # ═══════════════════════════════════════════════
    # Phase task generators
    # ═══════════════════════════════════════════════

    def _task_worldbuilding(self) -> str:
        """Generate worldbuilding task."""
        return self._build_task(
            phase="worldbuilding",
            title="世界观构建",
            system_prompt=MODE_PROMPTS["worldbuilding"],
            bible_state=self._bible_state_summary(),
            instructions=[
                "设计小说的核心世界观设定（3-5条，简洁聚焦）",
                "确定故事主题（1-2句话）",
                "写一段约200字的文风样本，展示整部小说的文字风格",
                "创建主角和1-2个重要配角的角色卡",
            ],
            expected_outputs=[
                {
                    "file": "bible/world.md",
                    "format": "Markdown，包含：核心设定、主题、文风样本（用 ## 文风样本 标记）",
                },
                {
                    "file": "bible/characters/{name}.json",
                    "format": "JSON，格式参考 bible/characters/ 目录下的示例。必填字段：name, role。可选：appearance, personality, background, arc_notes",
                },
            ],
            notes=[
                "用中文写作所有内容",
                "文风样本很重要——它会指导后续所有场景的写作风格",
                "角色数量控制在3-5个以内（2-3万字小说）",
            ],
        )

    def _task_outlining(self) -> str:
        """Generate outlining task."""
        world_preview = self._preview_world()
        chars = self.bible.list_characters()
        char_details = []
        for name in chars:
            c = self.bible.read_character(name)
            if c:
                char_details.append(f"- **{name}** ({c.get('role', '')}): {c.get('personality', '')}")

        return self._build_task(
            phase="outlining",
            title="故事大纲规划",
            system_prompt=MODE_PROMPTS["outlining"],
            bible_state=self._bible_state_summary(),
            context_blocks=[
                ("世界观摘要", world_preview[:800] if world_preview else "（无）"),
                ("已创建角色", "\n".join(char_details) if char_details else "（无）"),
            ],
            instructions=[
                "阅读世界观和角色信息（见上下文）",
                "规划三幕结构，共30-50个场景",
                "每个场景必须包含：id, template, pov, location, characters, purpose, conflict, hook, target_words",
                "注意节奏：每5-7个场景一个小高潮，幕末重大转折",
            ],
            expected_outputs=[
                {
                    "file": "bible/outline.json",
                    "format": """JSON 格式：
{
  "premise": "一句话故事",
  "theme": "主题",
  "acts": [
    {
      "act": 1, "purpose": "建立世界与主角动机",
      "chapters": [
        {
          "id": "ch_01", "title": "章节标题", "purpose": "本章目的",
          "scenes": [
            {
              "id": "scene_001", "template": "开局奇遇",
              "pov": "主角名", "location": "地点",
              "characters": ["角色1"], "purpose": "场景目的",
              "conflict": "冲突", "hook": "钩子",
              "target_words": 800, "status": "pending"
            }
          ]
        }
      ]
    }
  ]
}""",
                },
            ],
            notes=[
                "大纲是放大器——这里写好了，后面30个场景质量才有保障",
                "每个场景都要有明确的'为什么存在'",
                "target_words 建议 600-1200，全书约2-3万字",
            ],
        )

    def _task_writing(self) -> str:
        """Generate writing task for the next pending scene."""
        outline = self.bible._load_outline()
        pending = [s for s in outline.iter_scenes() if s.status == SceneStatus.pending]

        if not pending:
            return self._build_task(
                phase="writing",
                title="写作 — 全部完成",
                system_prompt="",
                bible_state=self._bible_state_summary(),
                instructions=["所有场景已写完！请运行 mybook task 进入审校阶段。"],
                expected_outputs=[],
            )

        scene = pending[0]
        # Build rich context
        scene_plan_text = json.dumps({
            "id": scene.id,
            "template": scene.template,
            "pov": scene.pov,
            "location": scene.location,
            "characters": scene.characters,
            "purpose": scene.purpose,
            "conflict": scene.conflict,
            "hook": scene.hook,
            "target_words": scene.target_words,
        }, ensure_ascii=False, indent=2)

        # Get previous scene
        all_scenes = list(outline.iter_scenes())
        current_idx = next((i for i, s in enumerate(all_scenes) if s.id == scene.id), -1)
        prev_scene_text = ""
        if current_idx > 0:
            prev = all_scenes[current_idx - 1]
            prev_text = self.bible.read_scene(prev.id)
            prev_summary = self.bible.read_scene_summary(prev.id)
            prev_scene_text = f"**上一个场景** ({prev.id}):\n"
            if prev_summary:
                prev_scene_text += f"摘要: {prev_summary.get('summary', '')}\n"
                prev_scene_text += f"结尾: {prev_summary.get('ends_with', '')}\n\n"
            prev_scene_text += f"全文:\n{prev_text[:1500]}"

        # Active characters
        char_blocks = []
        for name in scene.characters:
            c = self.bible.read_character(name)
            if c:
                char_blocks.append(f"### {name}\n```json\n{json.dumps(c, ensure_ascii=False, indent=2)}\n```")

        # Open foreshadowing
        fs_table = self.bible._load_foreshadowing()
        unpaid = fs_table.unpaid()
        fs_text = "\n".join(f"- {e.id}: {e.description}（计划在 {e.intended_payoff} 回收）" for e in unpaid) if unpaid else "（无待回收伏笔）"

        # Style sample
        world = self.bible.read_world()
        style = ""
        if "## 文风样本" in world:
            parts = world.split("## 文风样本", 1)
            if len(parts) > 1:
                style = parts[1].strip()[:400]

        # Progress
        done = sum(1 for s in all_scenes if s.status in (SceneStatus.done, SceneStatus.revised))
        total = len(all_scenes)

        return self._build_task(
            phase="writing",
            title=f"写场景: {scene.id}（进度 {done}/{total}）",
            system_prompt=MODE_PROMPTS["writing"],
            bible_state=self._bible_state_summary(),
            context_blocks=[
                ("当前场景计划", f"```json\n{scene_plan_text}\n```"),
                ("上一场景", prev_scene_text if prev_scene_text else "（这是第一个场景）"),
                ("出场角色", "\n\n".join(char_blocks) if char_blocks else "（无角色信息）"),
                ("待回收伏笔", fs_text),
                ("文风样本", style if style else "（未设置）"),
            ],
            instructions=[
                f"写场景 {scene.id}：{scene.purpose}",
                f"视角：{scene.pov}，地点：{scene.location}",
                f"目标字数：{scene.target_words} ± 20%",
                "严格遵守场景计划，不要推进计划之外的剧情",
                "结尾要有钩子（除非是收束场景）",
                "文风与文风样本保持一致",
                "角色行为与角色卡设定一致",
            ],
            expected_outputs=[
                {
                    "file": f"bible/scenes/{scene.id}.md",
                    "format": f"Markdown 格式的场景正文。目标 {scene.target_words} 字。",
                },
            ],
            notes=[
                f"写完场景后，请继续运行 mybook task 进入总结阶段",
                "或者直接一次性完成：写好场景正文后，也写好总结",
            ],
        )

    def _task_summarizing(self) -> str:
        """Generate summarization task for the most recently written scene."""
        outline = self.bible._load_outline()
        all_scenes = list(outline.iter_scenes())
        done_scenes = [s for s in all_scenes if s.status == SceneStatus.done]

        if not done_scenes:
            return self._build_task(
                phase="summarizing",
                title="总结 — 无待总结场景",
                system_prompt="",
                bible_state=self._bible_state_summary(),
                instructions=["没有刚写完待总结的场景。"],
                expected_outputs=[],
            )

        # Find the last done scene that doesn't have a summary
        last_scene = done_scenes[-1]
        has_summary = self.bible.read_scene_summary(last_scene.id) is not None

        if has_summary:
            return self._build_task(
                phase="summarizing",
                title="总结 — 无需操作",
                system_prompt="",
                bible_state=self._bible_state_summary(),
                instructions=[f"场景 {last_scene.id} 已有摘要，无需重复总结。"],
                expected_outputs=[],
            )

        scene_text = self.bible.read_scene(last_scene.id)

        return self._build_task(
            phase="summarizing",
            title=f"总结场景: {last_scene.id}",
            system_prompt=MODE_PROMPTS["summarizing"],
            bible_state=self._bible_state_summary(),
            context_blocks=[
                ("场景全文", scene_text[:3000] if scene_text else "（无内容）"),
            ],
            instructions=[
                f"阅读场景 {last_scene.id} 的全文",
                "写摘要（≤50字）",
                "列出关键事件",
                "描述结尾的氛围/悬念（ends_with 字段很重要）",
                "更新出场角色的状态（location, abilities, relationships）",
                "如有新伏笔，登记到 foreshadowing.json",
                "如有伏笔回收，标记为 paid_off",
                "追加时间线事件",
            ],
            expected_outputs=[
                {
                    "file": "bible/scene_summaries.json",
                    "format": f"在 summaries 中添加 {last_scene.id} 的条目：summary, key_events, word_count, ends_with",
                },
                {
                    "file": "bible/characters/*.json",
                    "format": "更新出场角色的 current_state",
                },
                {
                    "file": "bible/foreshadowing.json",
                    "format": "新增伏笔条目或标记回收入口",
                },
                {
                    "file": "bible/timeline.json",
                    "format": "追加时间线事件",
                },
            ],
            notes=["只记录实际发生的，不要编造", "ends_with 对下个场景的衔接至关重要"],
        )

    def _task_reviewing(self) -> str:
        """Generate review task."""
        scenes = self.bible.list_all_scenes()
        unpaid = self.bible.check_foreshadowing_unpaid()

        scene_list = "\n".join(f"- {sid}" for sid in scenes) if scenes else "（无场景）"
        unpaid_list = "\n".join(
            f"- {e['id']}: {e['description']}（计划回收: {e.get('intended_payoff', '未指定')}）"
            for e in unpaid
        ) if unpaid else "（无未回收伏笔）"

        return self._build_task(
            phase="reviewing",
            title="全文审校",
            system_prompt=MODE_PROMPTS["reviewing"],
            bible_state=self._bible_state_summary(),
            context_blocks=[
                ("所有场景", scene_list),
                ("未回收伏笔", unpaid_list),
            ],
            instructions=[
                "通读全文，逐项检查：",
                "1. 伏笔回收：所有 planted 的伏笔是否都有对应回收？",
                "2. 角色一致性：行为是否符合性格？能力前后矛盾？关系变化自然？",
                "3. 时间线：场景时间衔接合理？",
                "4. 节奏：高潮/缓冲分布合理？幕转折有力？",
                "5. 文风：前后一致？",
                "发现问题用 flag_issue（即写入 issues.json）",
            ],
            expected_outputs=[
                {
                    "file": "bible/issues.json",
                    "format": "JSON 数组，每个条目：{id, scene_id, issue_type, description, resolved: false}",
                },
            ],
            notes=[
                "只登记问题，不直接修改场景",
                "issue_type 可选：foreshadowing_unpaid, character_inconsistency, timeline_conflict, pacing, other",
            ],
        )

    def _task_revising(self) -> str:
        """Generate revision task for the next unresolved issue."""
        issues = self.bible._load_issues()
        unresolved = issues.unresolved()

        if not unresolved:
            return self._build_task(
                phase="revising",
                title="修订 — 无需操作",
                system_prompt="",
                bible_state=self._bible_state_summary(),
                instructions=["所有问题已解决！小说写作完成。"],
                expected_outputs=[],
            )

        issue = unresolved[0]
        scene_text = self.bible.read_scene(issue.scene_id)

        return self._build_task(
            phase="revising",
            title=f"修订: {issue.scene_id}",
            system_prompt=MODE_PROMPTS["revising"],
            bible_state=self._bible_state_summary(),
            context_blocks=[
                ("问题描述", f"**类型**: {issue.issue_type.value}\n**描述**: {issue.description}"),
                ("当前场景内容", scene_text[:2000] if scene_text else "（无内容）"),
            ],
            instructions=[
                f"修订场景 {issue.scene_id}",
                f"问题：{issue.description}",
                "最小改动原则——只改必要的部分",
                "保持与前后场景的自然衔接",
                "不引入新问题",
            ],
            expected_outputs=[
                {
                    "file": f"bible/scenes/{issue.scene_id}.md",
                    "format": "修订后的完整场景正文",
                },
                {
                    "file": "bible/issues.json",
                    "format": f"将 {issue.id} 的 resolved 设为 true",
                },
            ],
            notes=[f"还有 {len(unresolved) - 1} 个问题待修订"],
        )

    # ═══════════════════════════════════════════════
    # Task builder helpers
    # ═══════════════════════════════════════════════

    def _build_task(
        self,
        phase: str,
        title: str,
        system_prompt: str,
        bible_state: str,
        instructions: list[str],
        expected_outputs: list[dict],
        context_blocks: list[tuple[str, str]] | None = None,
        notes: list[str] | None = None,
    ) -> str:
        """Build a complete task Markdown document."""
        lines = []
        lines.append(f"# Phase: {phase}")
        lines.append(f"## {title}")
        lines.append(f"")
        lines.append(f"> 生成时间: {datetime.now().isoformat()}")
        lines.append(f"> 项目: {self.project_dir}")
        lines.append(f"")

        # System prompt
        if system_prompt:
            lines.append(f"## System Prompt")
            lines.append(f"")
            lines.append(system_prompt)
            lines.append(f"")

        # Bible state
        lines.append(f"## Bible 当前状态")
        lines.append(f"")
        lines.append(bible_state)
        lines.append(f"")

        # Context blocks
        if context_blocks:
            for block_title, block_content in context_blocks:
                lines.append(f"## {block_title}")
                lines.append(f"")
                lines.append(block_content)
                lines.append(f"")

        # Instructions
        lines.append(f"## 任务指令")
        lines.append(f"")
        for i, instr in enumerate(instructions, 1):
            lines.append(f"{i}. {instr}")
        lines.append(f"")

        # Expected outputs
        lines.append(f"## 预期产出")
        lines.append(f"")
        for output in expected_outputs:
            lines.append(f"### {output['file']}")
            lines.append(f"")
            lines.append(f"```")
            lines.append(output.get("format", ""))
            lines.append(f"```")
            lines.append(f"")

        # Notes
        if notes:
            lines.append(f"## 注意事项")
            lines.append(f"")
            for note in notes:
                lines.append(f"- {note}")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"*此任务由 mybook task-generator 自动生成*")
        lines.append(f"")

        return "\n".join(lines)

    def _bible_state_summary(self) -> str:
        """Summarize current bible state."""
        lines = []
        lines.append(f"- 世界观: {'已创建' if self.bible.has_world() else '未创建'}")
        chars = self.bible.list_characters()
        lines.append(f"- 角色: {len(chars)} 个 ({', '.join(chars) if chars else '无'})")

        if self.bible.has_outline():
            outline = self.bible._load_outline()
            total = outline.total_scenes()
            done = sum(1 for s in outline.iter_scenes() if s.status.value == "done")
            revised = sum(1 for s in outline.iter_scenes() if s.status.value == "revised")
            pending = sum(1 for s in outline.iter_scenes() if s.status.value == "pending")
            lines.append(f"- 大纲: {total} 场景 ({done} 已完成, {revised} 已修订, {pending} 待写)")
            lines.append(f"- 前提: {outline.premise}")

        fs = self.bible._load_foreshadowing()
        unpaid = fs.unpaid()
        lines.append(f"- 伏笔: {len(fs.entries)} 个 ({len(unpaid)} 未回收)")

        issues = self.bible._load_issues()
        unresolved = issues.unresolved()
        lines.append(f"- 问题: {len(unresolved)} 个未解决")

        return "\n".join(lines)

    def _preview_world(self) -> str:
        """Get a preview of world.md."""
        text = self.bible.read_world()
        if not text:
            return ""
        return text[:1000]
