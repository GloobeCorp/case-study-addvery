from __future__ import annotations

from pathlib import Path

from .config import PROJECT_ROOT


PROMPTS_DIR = PROJECT_ROOT / "app" / "prompts"
SKILL_PATH = PROJECT_ROOT / "skills" / "source_quality" / "SKILL.md"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def load_source_quality_skill() -> str:
    if not SKILL_PATH.exists():
        raise FileNotFoundError(f"Skill not found: {SKILL_PATH}")
    return SKILL_PATH.read_text(encoding="utf-8").strip()

