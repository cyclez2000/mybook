"""Bible manager — deterministic CRUD operations on the story bible.

All read/write to the file system goes through this module.
It is the single source of truth for the story bible data.
The AI agent calls tools; tools call these methods.

Directory structure:
  bible/
    world.md
    characters/{name}.json
    outline.json
    scenes/{scene_id}.md
    scene_summaries.json
    foreshadowing.json
    timeline.json
    issues.json
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schemas import (
    Character,
    CharacterState,
    Foreshadowing,
    ForeshadowingStatus,
    ForeshadowingTable,
    Issue,
    IssueType,
    Issues,
    Outline,
    ScenePlan,
    SceneStatus,
    SceneSummaries,
    SceneSummary,
    Timeline,
    TimelineEvent,
    WritingContext,
)


@dataclass
class BibleManager:
    """Manages all file I/O for the story bible."""

    root: Path  # bible/ directory

    # ── Path helpers ──────────────────────

    @property
    def world_path(self) -> Path:
        return self.root / "world.md"

    @property
    def characters_dir(self) -> Path:
        return self.root / "characters"

    @property
    def outline_path(self) -> Path:
        return self.root / "outline.json"

    @property
    def scenes_dir(self) -> Path:
        return self.root / "scenes"

    @property
    def summaries_path(self) -> Path:
        return self.root / "scene_summaries.json"

    @property
    def foreshadowing_path(self) -> Path:
        return self.root / "foreshadowing.json"

    @property
    def timeline_path(self) -> Path:
        return self.root / "timeline.json"

    @property
    def issues_path(self) -> Path:
        return self.root / "issues.json"

    # ── Init ──────────────────────────────

    def ensure_dirs(self) -> None:
        """Create all necessary directories."""
        self.root.mkdir(parents=True, exist_ok=True)
        self.characters_dir.mkdir(exist_ok=True)
        self.scenes_dir.mkdir(exist_ok=True)

    def has_world(self) -> bool:
        return self.world_path.exists() and self.world_path.read_text(encoding="utf-8").strip() != ""

    def has_outline(self) -> bool:
        return self.outline_path.exists()

    # ── Helpers ───────────────────────────

    def _load_json(self, path: Path, default: dict | list) -> dict | list:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return default

    def _save_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(data, "model_dump"):
            text = json.dumps(data.model_dump(), ensure_ascii=False, indent=2)
        else:
            text = json.dumps(data, ensure_ascii=False, indent=2)
        path.write_text(text, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════════
    # READ TOOLS
    # ═══════════════════════════════════════════════════════════════

    def read_world(self) -> str:
        """Read the full world setting document."""
        if not self.world_path.exists():
            return ""
        return self.world_path.read_text(encoding="utf-8")

    def read_outline(self, level: str = "scene") -> dict:
        """Read outline at the specified granularity.

        Args:
            level: "act", "chapter", or "scene" (default)
        """
        outline = self._load_outline()
        if level == "act":
            return {
                "premise": outline.premise,
                "theme": outline.theme,
                "acts": [{"act": a.act, "purpose": a.purpose} for a in outline.acts],
            }
        elif level == "chapter":
            result = {"premise": outline.premise, "theme": outline.theme, "acts": []}
            for act in outline.acts:
                chapters = [
                    {"id": c.id, "title": c.title, "purpose": c.purpose, "scene_count": len(c.scenes)}
                    for c in act.chapters
                ]
                result["acts"].append({"act": act.act, "purpose": act.purpose, "chapters": chapters})
            return result
        else:
            return outline.model_dump()

    def read_character(self, name: str) -> Optional[dict]:
        """Read a single character card."""
        path = self.characters_dir / f"{name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_characters(self) -> list[str]:
        """List all character names."""
        if not self.characters_dir.exists():
            return []
        names = []
        for f in self.characters_dir.iterdir():
            if f.suffix == ".json":
                names.append(f.stem)
        return sorted(names)

    def read_scene(self, scene_id: str) -> str:
        """Read the full text of a scene."""
        path = self.scenes_dir / f"{scene_id}.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def read_scene_summary(self, scene_id: str) -> Optional[dict]:
        """Read a single scene's summary."""
        summaries = self._load_summaries()
        s = summaries.summaries.get(scene_id)
        return s.model_dump() if s else None

    def list_recent_summaries(self, n: int = 5) -> list[dict]:
        """Return the n most recent scene summaries."""
        summaries = self._load_summaries()
        recent = summaries.recent(n)
        return [s.model_dump() for s in recent]

    def read_foreshadowing(self, status: str = "all") -> list[dict]:
        """Read foreshadowing entries filtered by status.

        Args:
            status: "planted", "paid_off", or "all"
        """
        table = self._load_foreshadowing()
        if status == "planted":
            entries = [e for e in table.entries if e.status == ForeshadowingStatus.planted]
        elif status == "paid_off":
            entries = [e for e in table.entries if e.status == ForeshadowingStatus.paid_off]
        else:
            entries = table.entries
        return [e.model_dump() for e in entries]

    # ═══════════════════════════════════════════════════════════════
    # PLANNING TOOLS
    # ═══════════════════════════════════════════════════════════════

    def write_world(self, content: str) -> None:
        """Write/overwrite world.md."""
        self.ensure_dirs()
        self.world_path.write_text(content, encoding="utf-8")

    def create_character(
        self,
        name: str,
        role: str,
        appearance: str = "",
        personality: str = "",
        background: str = "",
        arc_notes: str = "",
    ) -> None:
        """Create a new character card."""
        self.ensure_dirs()
        char = Character(
            name=name,
            role=role,
            appearance=appearance,
            personality=personality,
            background=background,
            arc_notes=arc_notes,
        )
        path = self.characters_dir / f"{name}.json"
        path.write_text(json.dumps(char.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    def write_outline(self, outline: dict) -> None:
        """Write the full outline."""
        self.ensure_dirs()
        validated = Outline.model_validate(outline)
        self._save_json(self.outline_path, validated)

    def revise_scene_plan(self, scene_id: str, **fields) -> Optional[dict]:
        """Adjust a scene's plan. Returns updated plan or None if not found."""
        outline = self._load_outline()
        scene = outline.get_scene(scene_id)
        if scene is None:
            return None
        for key, value in fields.items():
            if hasattr(scene, key):
                setattr(scene, key, value)
        self._save_json(self.outline_path, outline)
        return scene.model_dump()

    # ═══════════════════════════════════════════════════════════════
    # WRITING TOOLS
    # ═══════════════════════════════════════════════════════════════

    def write_scene(self, scene_id: str, content: str) -> dict:
        """Write a scene's full text. Returns validation info."""
        self.ensure_dirs()
        path = self.scenes_dir / f"{scene_id}.md"
        path.write_text(content, encoding="utf-8")

        # Mark scene as done in outline
        outline = self._load_outline()
        scene = outline.get_scene(scene_id)
        if scene:
            scene.status = SceneStatus.done
            self._save_json(self.outline_path, outline)

        # Validate word count
        word_count = len(content)
        warning = None
        if scene and scene.target_words > 0:
            deviation = abs(word_count - scene.target_words) / scene.target_words
            if deviation > 0.3:  # >30% off
                warning = (
                    f"字数偏差较大：目标{scene.target_words}字，实际{word_count}字 "
                    f"（偏差{deviation:.0%}）。请考虑调整。"
                )

        return {
            "scene_id": scene_id,
            "word_count": word_count,
            "target_words": scene.target_words if scene else 0,
            "warning": warning,
        }

    def get_writing_context(self, scene_id: str) -> dict:
        """Assemble the WritingContext for a scene.

        This is the MOST IMPORTANT tool — it packages exactly
        what the AI needs, nothing more, nothing less.
        """
        outline = self._load_outline()
        scene = outline.get_scene(scene_id)
        summaries = self._load_summaries()
        foreshadowing_table = self._load_foreshadowing()
        world_text = self.read_world()

        # World brief: first ~500 chars
        world_brief = world_text[:500] if world_text else ""

        # Previous scene: find the scene immediately before this one
        previous_scene_full = ""
        earlier_summaries: list[str] = []
        all_scenes = list(outline.iter_scenes())
        current_idx = next((i for i, s in enumerate(all_scenes) if s.id == scene_id), -1)

        if current_idx > 0:
            prev_scene = all_scenes[current_idx - 1]
            previous_scene_full = self.read_scene(prev_scene.id)

        # Earlier summaries: all summaries before current scene
        for s in all_scenes[:current_idx]:
            summary = summaries.summaries.get(s.id)
            if summary:
                earlier_summaries.append(summary.summary)

        # Active characters
        active_chars: list[dict] = []
        if scene:
            for name in scene.characters:
                char = self.read_character(name)
                if char:
                    active_chars.append(char)

        # Open foreshadowing
        open_fs = [
            f"{e.id}: {e.description}"
            for e in foreshadowing_table.unpaid()
        ]

        # Style sample - extract from world
        style_sample = ""
        if "## 文风样本" in world_text:
            parts = world_text.split("## 文风样本", 1)
            if len(parts) > 1:
                style_sample = parts[1].strip()[:300]

        context = WritingContext(
            world_brief=world_brief,
            current_scene_plan=scene,
            previous_scene_full=previous_scene_full[:2000],  # cap
            earlier_summaries=earlier_summaries[-10:],  # last 10
            active_characters=[Character.model_validate(c) for c in active_chars],
            open_foreshadowing=open_fs,
            style_sample=style_sample,
        )
        return context.model_dump()

    # ═══════════════════════════════════════════════════════════════
    # SUMMARIZATION TOOLS
    # ═══════════════════════════════════════════════════════════════

    def summarize_scene(
        self,
        scene_id: str,
        summary: str,
        key_events: list[str] | None = None,
        ends_with: str = "",
    ) -> dict:
        """Record a scene summary after writing."""
        summaries = self._load_summaries()
        scene_text = self.read_scene(scene_id)
        word_count = len(scene_text)

        s = SceneSummary(
            scene_id=scene_id,
            summary=summary,
            key_events=key_events or [],
            word_count=word_count,
            ends_with=ends_with,
        )
        summaries.summaries[scene_id] = s
        self._save_json(self.summaries_path, summaries)
        return s.model_dump()

    def update_character_state(
        self,
        name: str,
        location: str | None = None,
        abilities_added: list[str] | None = None,
        abilities_removed: list[str] | None = None,
        relationships_changed: dict[str, str] | None = None,
        notes: str | None = None,
    ) -> Optional[dict]:
        """Incrementally update a character's current state."""
        path = self.characters_dir / f"{name}.json"
        if not path.exists():
            return None

        char_data = json.loads(path.read_text(encoding="utf-8"))
        state = char_data.get("current_state", {})

        if location is not None:
            state["location"] = location
        if abilities_added:
            existing = set(state.get("abilities", []))
            existing.update(abilities_added)
            state["abilities"] = sorted(existing)
        if abilities_removed:
            existing = set(state.get("abilities", []))
            existing.difference_update(abilities_removed)
            state["abilities"] = sorted(existing)
        if relationships_changed:
            rels = state.get("relationships", {})
            rels.update(relationships_changed)
            state["relationships"] = rels
        if notes:
            existing_notes = char_data.get("arc_notes", "")
            char_data["arc_notes"] = f"{existing_notes}\n{notes}" if existing_notes else notes

        char_data["current_state"] = state
        path.write_text(json.dumps(char_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return char_data

    def plant_foreshadowing(
        self,
        description: str,
        intended_payoff_scene: str = "",
    ) -> dict:
        """Register a new foreshadowing entry."""
        table = self._load_foreshadowing()
        fs_id = f"fs_{len(table.entries) + 1:03d}"

        entry = Foreshadowing(
            id=fs_id,
            planted_in="",  # filled in by caller
            description=description,
            intended_payoff=intended_payoff_scene,
        )
        table.entries.append(entry)
        self._save_json(self.foreshadowing_path, table)
        return entry.model_dump()

    def pay_off_foreshadowing(self, foreshadowing_id: str, scene_id: str) -> Optional[dict]:
        """Mark a foreshadowing entry as paid off."""
        table = self._load_foreshadowing()
        for entry in table.entries:
            if entry.id == foreshadowing_id:
                entry.status = ForeshadowingStatus.paid_off
                entry.actual_payoff = scene_id
                self._save_json(self.foreshadowing_path, table)
                return entry.model_dump()
        return None

    def add_timeline_event(
        self,
        scene_id: str,
        event: str,
        in_story_time: str = "",
    ) -> dict:
        """Append a timeline event."""
        timeline = self._load_timeline()
        ev = TimelineEvent(
            scene_id=scene_id,
            event=event,
            in_story_time=in_story_time,
        )
        timeline.events.append(ev)
        self._save_json(self.timeline_path, timeline)
        return ev.model_dump()

    # ═══════════════════════════════════════════════════════════════
    # REVIEW TOOLS
    # ═══════════════════════════════════════════════════════════════

    def list_all_scenes(self) -> list[str]:
        """Return all scene IDs in writing order."""
        outline = self._load_outline()
        return [s.id for s in outline.iter_scenes()]

    def check_foreshadowing_unpaid(self) -> list[dict]:
        """Return all unpaid foreshadowing entries."""
        table = self._load_foreshadowing()
        return [e.model_dump() for e in table.unpaid()]

    def check_character_consistency(self, name: str) -> Optional[dict]:
        """Return character appearance history across all scenes."""
        char = self.read_character(name)
        if not char:
            return None

        outline = self._load_outline()
        appearances = []
        state_changes = []
        for scene in outline.iter_scenes():
            if name in scene.characters:
                appearances.append(scene.id)
            # Check if this scene changed character state
            summary = self.read_scene_summary(scene.id)
            if summary and name in str(summary.get("key_events", [])):
                state_changes.append({"scene": scene.id, "events": summary["key_events"]})

        return {
            "character": char,
            "appears_in": appearances,
            "state_changes_in": state_changes,
        }

    def flag_issue(
        self,
        scene_id: str,
        issue_type: str,
        description: str,
    ) -> dict:
        """Record a discovered issue."""
        issues = self._load_issues()
        issue_id = f"issue_{len(issues.issues) + 1:03d}"

        issue = Issue(
            id=issue_id,
            scene_id=scene_id,
            issue_type=IssueType(issue_type),
            description=description,
        )
        issues.issues.append(issue)
        self._save_json(self.issues_path, issues)
        return issue.model_dump()

    def apply_revision(self, scene_id: str, new_content: str, reason: str) -> dict:
        """Revise a scene with new content."""
        path = self.scenes_dir / f"{scene_id}.md"
        path.write_text(new_content, encoding="utf-8")

        # Update status
        outline = self._load_outline()
        scene = outline.get_scene(scene_id)
        if scene:
            scene.status = SceneStatus.revised
            scene.revision_history.append(reason)
            self._save_json(self.outline_path, outline)

        return {
            "scene_id": scene_id,
            "word_count": len(new_content),
            "reason": reason,
        }

    # ── Internal loaders with caching ─────

    def _load_outline(self) -> Outline:
        data = self._load_json(self.outline_path, {"acts": []})
        return Outline.model_validate(data)

    def _load_summaries(self) -> SceneSummaries:
        data = self._load_json(self.summaries_path, {"summaries": {}})
        return SceneSummaries.model_validate(data)

    def _load_foreshadowing(self) -> ForeshadowingTable:
        data = self._load_json(self.foreshadowing_path, {"entries": []})
        return ForeshadowingTable.model_validate(data)

    def _load_timeline(self) -> Timeline:
        data = self._load_json(self.timeline_path, {"events": []})
        return Timeline.model_validate(data)

    def _load_issues(self) -> Issues:
        data = self._load_json(self.issues_path, {"issues": []})
        return Issues.model_validate(data)
