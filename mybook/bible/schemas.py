"""Data schemas for the story bible — all Pydantic models.

These models define the complete data structure of the story bible,
as outlined in the design document. They serve as the single source
of truth for type validation and serialization.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Character
# ──────────────────────────────────────────────

class CharacterState(BaseModel):
    """Current state of a character — updated after each scene."""
    location: str = ""
    abilities: list[str] = Field(default_factory=list)
    relationships: dict[str, str] = Field(default_factory=dict)
    last_updated_scene: str = ""


class Character(BaseModel):
    """Full character card."""
    name: str
    role: str  # 主角, 配角, 反派, etc.
    appearance: str = ""
    personality: str = ""
    background: str = ""
    current_state: CharacterState = Field(default_factory=CharacterState)
    arc_notes: str = ""


# ──────────────────────────────────────────────
# Outline
# ──────────────────────────────────────────────

class SceneStatus(str, Enum):
    pending = "pending"
    writing = "writing"
    done = "done"
    revised = "revised"


class ScenePlan(BaseModel):
    """A single scene in the outline."""
    id: str  # e.g., "scene_001"
    template: str = ""  # e.g., "开局奇遇"
    pov: str = ""  # POV character
    location: str = ""
    characters: list[str] = Field(default_factory=list)
    purpose: str = ""
    conflict: str = ""
    hook: str = ""
    target_words: int = 800
    status: SceneStatus = SceneStatus.pending
    revision_history: list[str] = Field(default_factory=list)


class Chapter(BaseModel):
    """A chapter containing multiple scenes."""
    id: str  # e.g., "ch_01"
    title: str = ""
    purpose: str = ""
    scenes: list[ScenePlan] = Field(default_factory=list)


class Act(BaseModel):
    """An act containing multiple chapters."""
    act: int
    purpose: str = ""
    chapters: list[Chapter] = Field(default_factory=list)


class Outline(BaseModel):
    """Complete story outline."""
    premise: str = ""  # One-sentence story
    theme: str = ""
    style_sample: str = ""  # Sample paragraph showing desired writing style
    acts: list[Act] = Field(default_factory=list)

    # Convenience: iterate all scenes in order
    def iter_scenes(self):
        for act in self.acts:
            for chapter in act.chapters:
                yield from chapter.scenes

    def get_scene(self, scene_id: str) -> Optional[ScenePlan]:
        for scene in self.iter_scenes():
            if scene.id == scene_id:
                return scene
        return None

    def total_scenes(self) -> int:
        return sum(1 for _ in self.iter_scenes())


# ──────────────────────────────────────────────
# Scene Summary
# ──────────────────────────────────────────────

class SceneSummary(BaseModel):
    """Summary recorded after a scene is written."""
    scene_id: str
    summary: str  # ≤50 words
    key_events: list[str] = Field(default_factory=list)
    word_count: int = 0
    ends_with: str = ""  # The emotional/cliffhanger ending
    written_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SceneSummaries(BaseModel):
    """Collection of all scene summaries."""
    summaries: dict[str, SceneSummary] = Field(default_factory=dict)

    def recent(self, n: int = 5) -> list[SceneSummary]:
        """Return the most recent n summaries by writing order."""
        sorted_items = sorted(
            self.summaries.values(),
            key=lambda s: s.written_at,
            reverse=True,
        )
        return sorted_items[:n]


# ──────────────────────────────────────────────
# Foreshadowing
# ──────────────────────────────────────────────

class ForeshadowingStatus(str, Enum):
    planted = "planted"
    paid_off = "paid_off"


class Foreshadowing(BaseModel):
    """A single foreshadowing entry."""
    id: str  # e.g., "fs_001"
    planted_in: str  # scene_id
    description: str
    intended_payoff: str = ""  # scene_id
    actual_payoff: str = ""  # scene_id where it was paid off
    status: ForeshadowingStatus = ForeshadowingStatus.planted


class ForeshadowingTable(BaseModel):
    """Collection of all foreshadowing entries."""
    entries: list[Foreshadowing] = Field(default_factory=list)

    def unpaid(self) -> list[Foreshadowing]:
        return [e for e in self.entries if e.status == ForeshadowingStatus.planted]


# ──────────────────────────────────────────────
# Timeline
# ──────────────────────────────────────────────

class TimelineEvent(BaseModel):
    """A single event on the story timeline."""
    scene_id: str
    event: str
    in_story_time: str = ""  # e.g., "第三天傍晚"


class Timeline(BaseModel):
    """Chronological story timeline."""
    events: list[TimelineEvent] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Issues (Review Phase)
# ──────────────────────────────────────────────

class IssueType(str, Enum):
    foreshadowing_unpaid = "foreshadowing_unpaid"
    character_inconsistency = "character_inconsistency"
    timeline_conflict = "timeline_conflict"
    pacing = "pacing"
    other = "other"


class Issue(BaseModel):
    """An issue flagged during review."""
    id: str  # e.g., "issue_001"
    scene_id: str
    issue_type: IssueType
    description: str
    resolved: bool = False


class Issues(BaseModel):
    """Collection of flagged issues."""
    issues: list[Issue] = Field(default_factory=list)

    def unresolved(self) -> list[Issue]:
        return [i for i in self.issues if not i.resolved]


# ──────────────────────────────────────────────
# Writing Context (packaged for AI)
# ──────────────────────────────────────────────

class WritingContext(BaseModel):
    """The context bundle passed to the AI before writing a scene.
    
    This is the output of get_writing_context — it encapsulates
    all the information the AI needs to write the current scene,
    carefully filtered to avoid context explosion.
    """
    world_brief: str = ""  # Compressed world setting (~500 chars)
    current_scene_plan: Optional[ScenePlan] = None
    previous_scene_full: str = ""  # Full text of the previous scene
    earlier_summaries: list[str] = Field(default_factory=list)
    active_characters: list[Character] = Field(default_factory=list)
    open_foreshadowing: list[str] = Field(default_factory=list)
    style_sample: str = ""
