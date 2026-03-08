#!/usr/bin/env python3
"""Validate a skill pack structure and frontmatter contract."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

# Match @skill-style mentions while avoiding email addresses.
RE_SKILL_REF = re.compile(r"(?<![\\w.])@([a-z0-9][a-z0-9-]{2,})\\b")


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str, bool, bool]:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", content, re.DOTALL)
    if not match:
        return {}, content, False, True

    raw = match.group(1)
    body = content[match.end() :]

    try:
        parsed = yaml.safe_load(raw) or {}
        if isinstance(parsed, dict):
            return parsed, body, True, True
        return {}, body, True, False
    except Exception:
        return {}, body, True, False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate imported skill pack")
    parser.add_argument(
        "--pack-root",
        default="skills/external/inference-sh/normalized",
        help="Path to normalized skill pack root",
    )
    parser.add_argument(
        "--expected-prefix",
        default="infsh-",
        help="Expected skill ID prefix (default: infsh-)",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    pack_root = Path(args.pack_root).resolve()
    if not pack_root.exists():
        print(f"ERROR: pack root not found: {pack_root}")
        return 1

    errors: List[str] = []
    warnings: List[str] = []

    skill_dirs = sorted([p for p in pack_root.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not skill_dirs:
        errors.append("No skill directories found")

    seen_names: Dict[str, str] = {}
    valid_skill_ids = set()
    refs_by_skill: Dict[str, List[str]] = {}

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill_dir.name}: missing SKILL.md")
            continue

        content = skill_md.read_text(encoding="utf-8", errors="ignore")
        frontmatter, body, had_frontmatter, parse_ok = parse_frontmatter(content)

        if not had_frontmatter:
            errors.append(f"{skill_dir.name}: missing frontmatter")
            continue

        if not parse_ok:
            errors.append(f"{skill_dir.name}: invalid YAML frontmatter")
            continue

        name = str(frontmatter.get("name") or "").strip()
        description = str(frontmatter.get("description") or "").strip()
        allowed_tools = frontmatter.get("allowed-tools")

        if not name:
            errors.append(f"{skill_dir.name}: frontmatter missing 'name'")
            continue

        if not description:
            errors.append(f"{skill_dir.name}: frontmatter missing 'description'")

        if not allowed_tools:
            warnings.append(f"{skill_dir.name}: frontmatter missing 'allowed-tools'")

        if args.expected_prefix and not name.startswith(args.expected_prefix):
            errors.append(
                f"{skill_dir.name}: name '{name}' does not start with '{args.expected_prefix}'"
            )

        if name in seen_names:
            errors.append(
                f"duplicate name '{name}' in {skill_dir.name} and {seen_names[name]}"
            )
        else:
            seen_names[name] = skill_dir.name

        valid_skill_ids.add(name)
        refs_by_skill[name] = RE_SKILL_REF.findall(body)

    # Cross-reference checks (warnings by default)
    for skill_name, refs in refs_by_skill.items():
        unresolved = []
        for ref in refs:
            candidate_exact = ref
            candidate_prefixed = f"{args.expected_prefix}{ref}" if args.expected_prefix else ref
            if candidate_exact in valid_skill_ids or candidate_prefixed in valid_skill_ids:
                continue
            unresolved.append(ref)

        if unresolved:
            uniq = sorted(set(unresolved))
            warnings.append(f"{skill_name}: unresolved references {', '.join(uniq)}")

    print(f"Pack root: {pack_root}")
    print(f"Skills checked: {len(valid_skill_ids)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors:
        print("\nERRORS:")
        for err in errors:
            print(f"  - {err}")

    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        return 1
    if warnings and args.strict_warnings:
        return 1

    print("\nValidation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
