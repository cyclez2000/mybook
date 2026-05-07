"""Centralized configuration — no API keys needed.

MyBook is powered by your AI agent, not external LLM APIs.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    project_dir: Path = Path(os.getenv("MYBOOK_PROJECT_DIR", "./my_novel"))
    language: str = os.getenv("MYBOOK_LANGUAGE", "zh")

    @property
    def bible_dir(self) -> Path:
        return self.project_dir / "bible"

    @classmethod
    def validate(cls) -> list[str]:
        """Always valid — no API keys required."""
        return []


config = Config()
