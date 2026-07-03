from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_prompt_files_exist():
    for name in ("research.md", "analysis.md", "writer.md"):
        path = ROOT / "app" / "prompts" / name
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()


def test_skill_is_documented():
    skill = ROOT / "skills" / "source_quality" / "SKILL.md"

    assert skill.exists()
    assert "Source Quality Skill" in skill.read_text(encoding="utf-8")

