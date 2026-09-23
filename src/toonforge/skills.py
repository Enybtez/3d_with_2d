from pathlib import Path

from .config import PROJECT_ROOT


def load_skill(name: str) -> str:
    if name not in {"image-analysis", "toon-review"}:
        raise ValueError("未知 Skill")
    content = (PROJECT_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError("Skill 缺少 frontmatter")
    return content.split("---\n", 2)[2].strip()
