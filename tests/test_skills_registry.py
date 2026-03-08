"""Tests for brandmint.core.skills_registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from brandmint.core.skills_registry import SkillsRegistry


def _write_skill(path: Path, name: str, description: str = "Test skill") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        "# Steps\n\n"
        "1. Do thing\n"
    )
    path.write_text(content, encoding="utf-8")


def test_alias_resolution_for_folder_name_mismatch(tmp_path: Path) -> None:
    orchestrator = tmp_path / "orchestrator"
    brand_skills = tmp_path / "brand_skills"
    claude_skills = tmp_path / "claude_skills"

    _write_skill(
        brand_skills / "text-strategy" / "buyer-persona" / "SKILL.md",
        name="buyer-persona-generator",
        description="Buyer persona generator",
    )

    registry = SkillsRegistry(
        skills_dir=orchestrator,
        brand_skills_dir=brand_skills,
        claude_skills_dir=claude_skills,
        conflict_policy="warn_skip",
    )

    resolved = registry.get_skill("buyer-persona")
    assert resolved is not None
    assert resolved.id == "buyer-persona-generator"


def test_conflict_is_recorded_and_skipped_by_default(tmp_path: Path) -> None:
    orchestrator = tmp_path / "orchestrator"
    brand_skills = tmp_path / "brand_skills"
    claude_skills = tmp_path / "claude_skills"

    brand_path = brand_skills / "group" / "alpha" / "SKILL.md"
    claude_path = claude_skills / "alpha" / "SKILL.md"

    _write_skill(brand_path, name="alpha", description="Brand alpha")
    _write_skill(claude_path, name="alpha", description="Claude alpha")

    registry = SkillsRegistry(
        skills_dir=orchestrator,
        brand_skills_dir=brand_skills,
        claude_skills_dir=claude_skills,
        conflict_policy="warn_skip",
    )

    assert len(registry.get_conflicts()) == 1

    chosen = registry.get_skill("alpha")
    assert chosen is not None
    assert chosen.skill_md_path is not None
    assert Path(chosen.skill_md_path).resolve() == brand_path.resolve()


def test_conflict_policy_error_raises(tmp_path: Path) -> None:
    orchestrator = tmp_path / "orchestrator"
    brand_skills = tmp_path / "brand_skills"
    claude_skills = tmp_path / "claude_skills"

    _write_skill(brand_skills / "group" / "alpha" / "SKILL.md", name="alpha")
    _write_skill(claude_skills / "alpha" / "SKILL.md", name="alpha")

    with pytest.raises(ValueError):
        SkillsRegistry(
            skills_dir=orchestrator,
            brand_skills_dir=brand_skills,
            claude_skills_dir=claude_skills,
            conflict_policy="error",
        )


def test_recursive_claude_discovery(tmp_path: Path) -> None:
    orchestrator = tmp_path / "orchestrator"
    brand_skills = tmp_path / "brand_skills"
    claude_skills = tmp_path / "claude_skills"

    _write_skill(
        claude_skills / "pack" / "nested-skill" / "SKILL.md",
        name="nested-skill",
        description="Nested skill",
    )

    registry = SkillsRegistry(
        skills_dir=orchestrator,
        brand_skills_dir=brand_skills,
        claude_skills_dir=claude_skills,
        conflict_policy="warn_skip",
    )

    assert registry.get_skill("nested-skill") is not None


def test_instructions_without_frontmatter_is_ignored(tmp_path: Path) -> None:
    orchestrator = tmp_path / "orchestrator"
    brand_skills = tmp_path / "brand_skills"
    claude_skills = tmp_path / "claude_skills"

    instructions = claude_skills / "misc" / "instructions.md"
    instructions.parent.mkdir(parents=True, exist_ok=True)
    instructions.write_text("# Notes\n\nJust notes, not a skill.\n", encoding="utf-8")

    registry = SkillsRegistry(
        skills_dir=orchestrator,
        brand_skills_dir=brand_skills,
        claude_skills_dir=claude_skills,
        conflict_policy="warn_skip",
    )

    assert registry.get_skill("misc") is None


def test_claude_variant_folder_duplicates_are_mergeable(tmp_path: Path) -> None:
    orchestrator = tmp_path / "orchestrator"
    brand_skills = tmp_path / "brand_skills"
    claude_skills = tmp_path / "claude_skills"

    _write_skill(claude_skills / "Council" / "SKILL.md", name="Council")
    _write_skill(claude_skills / "Thinking" / "Council" / "SKILL.md", name="Council")

    _write_skill(claude_skills / "CreateCLI" / "SKILL.md", name="CreateCLI")
    _write_skill(claude_skills / "Utilities" / "CreateCLI" / "SKILL.md", name="CreateCLI")

    _write_skill(claude_skills / "Documents" / "Docx" / "SKILL.md", name="Docx")
    _write_skill(claude_skills / "document-skills" / "docx" / "SKILL.md", name="docx")

    registry = SkillsRegistry(
        skills_dir=orchestrator,
        brand_skills_dir=brand_skills,
        claude_skills_dir=claude_skills,
        conflict_policy="error",
    )

    assert registry.get_conflicts() == []
    assert registry.get_skill("council") is not None
    assert registry.get_skill("createcli") is not None
    assert registry.get_skill("docx") is not None


def test_non_variant_claude_duplicate_still_conflicts(tmp_path: Path) -> None:
    orchestrator = tmp_path / "orchestrator"
    brand_skills = tmp_path / "brand_skills"
    claude_skills = tmp_path / "claude_skills"

    _write_skill(claude_skills / "alpha" / "SKILL.md", name="alpha")
    _write_skill(claude_skills / "other-pack" / "alpha" / "SKILL.md", name="alpha")

    registry = SkillsRegistry(
        skills_dir=orchestrator,
        brand_skills_dir=brand_skills,
        claude_skills_dir=claude_skills,
        conflict_policy="warn_skip",
    )

    conflicts = registry.get_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0]["skill_id"] == "alpha"
