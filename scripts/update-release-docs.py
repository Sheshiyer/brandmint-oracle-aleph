#!/usr/bin/env python3
"""
update-release-docs.py — Scan repo changes and update documentation files.

Reads git diff/log to detect what changed since the last tagged release,
then applies surgical updates to documentation files without rewriting them.

Usage:
    # Dry run — show what would change
    python3 scripts/update-release-docs.py --dry-run

    # Apply updates with a new version
    python3 scripts/update-release-docs.py --version 4.3.0

    # Auto-detect version bump (patch/minor/major from commit messages)
    python3 scripts/update-release-docs.py --auto

    # Show change summary only (no file modifications)
    python3 scripts/update-release-docs.py --summary
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent

# ── Files to update ──────────────────────────────────────────────────────────

DOC_FILES = {
    "pyproject": ROOT / "pyproject.toml",
    "readme": ROOT / "README.md",
    "claude_md": ROOT / "CLAUDE.md",
    "skill_md": ROOT / "SKILL.md",
    "release_notes": ROOT / ".github" / "RELEASE_NOTES.md",
    "product_desc": ROOT / "docs" / "product-description.md",
    "copilot": ROOT / ".github" / "copilot-instructions.md",
    "cursorrules": ROOT / ".cursorrules",
}

# ── Git helpers ──────────────────────────────────────────────────────────────

def run_git(*args: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True, text=True, cwd=ROOT,
    )
    return result.stdout.strip()


def get_last_tag() -> Optional[str]:
    """Get the most recent git tag."""
    tag = run_git("describe", "--tags", "--abbrev=0")
    return tag if tag else None


def get_current_version() -> str:
    """Read version from pyproject.toml."""
    text = (ROOT / "pyproject.toml").read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else "0.0.0"


def bump_version(current: str, bump_type: str = "minor") -> str:
    """Bump a semver version string."""
    parts = current.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def detect_bump_type(commits: List[str]) -> str:
    """Detect version bump type from commit messages."""
    for msg in commits:
        lower = msg.lower()
        if "breaking" in lower or "major:" in lower:
            return "major"
    for msg in commits:
        lower = msg.lower()
        if lower.startswith("feat") or "feature" in lower:
            return "minor"
    return "patch"


# ── Change detection ─────────────────────────────────────────────────────────

def get_changed_files(since_ref: Optional[str] = None) -> Set[str]:
    """Get files changed since ref (or all uncommitted changes)."""
    if since_ref:
        diff = run_git("diff", "--name-only", f"{since_ref}..HEAD")
    else:
        diff = run_git("diff", "--name-only", "HEAD")
    staged = run_git("diff", "--name-only", "--cached")
    untracked = run_git("ls-files", "--others", "--exclude-standard")
    all_files = set()
    for output in [diff, staged, untracked]:
        for line in output.splitlines():
            line = line.strip()
            if line:
                all_files.add(line)
    return all_files


def get_commits_since(since_ref: Optional[str] = None) -> List[str]:
    """Get commit messages since ref."""
    if since_ref:
        log = run_git("log", f"{since_ref}..HEAD", "--oneline")
    else:
        log = run_git("log", "-20", "--oneline")
    return [line.strip() for line in log.splitlines() if line.strip()]


def categorize_changes(files: Set[str]) -> Dict[str, List[str]]:
    """Categorize changed files by area."""
    categories: Dict[str, List[str]] = {
        "cli": [],
        "core": [],
        "pipeline": [],
        "publishing": [],
        "models": [],
        "skills": [],
        "scripts": [],
        "templates": [],
        "docs": [],
        "config": [],
        "other": [],
    }
    for f in sorted(files):
        if f.startswith("brandmint/cli/"):
            categories["cli"].append(f)
        elif f.startswith("brandmint/core/"):
            categories["core"].append(f)
        elif f.startswith("brandmint/pipeline/"):
            categories["pipeline"].append(f)
        elif f.startswith("brandmint/publishing/"):
            categories["publishing"].append(f)
        elif f.startswith("brandmint/models/"):
            categories["models"].append(f)
        elif f.startswith("skills/"):
            categories["skills"].append(f)
        elif f.startswith("scripts/"):
            categories["scripts"].append(f)
        elif "template" in f.lower() or f.endswith(".j2"):
            categories["templates"].append(f)
        elif f.endswith(".md") or f.startswith("docs/"):
            categories["docs"].append(f)
        elif f in ("pyproject.toml", ".cursorrules", "CLAUDE.md", "SKILL.md"):
            categories["config"].append(f)
        else:
            categories["other"].append(f)
    return {k: v for k, v in categories.items() if v}


def detect_new_features(files: Set[str], commits: List[str]) -> List[str]:
    """Detect new features from changed files and commit messages."""
    features = []

    # New Python modules
    for f in sorted(files):
        if f.endswith(".py") and f.startswith("brandmint/"):
            path = Path(f)
            if not (ROOT / f).exists():
                continue  # deleted
            # Check if it's a new file (not in git history)
            log = run_git("log", "--oneline", "-1", "--", f)
            if not log or "feat" in log.lower():
                module_name = path.stem.replace("_", " ").title()
                features.append(f"New module: {module_name} ({f})")

    # New CLI commands from commits
    for msg in commits:
        if "bm " in msg.lower() or "command" in msg.lower():
            features.append(f"CLI: {msg}")

    # New template directories
    for f in sorted(files):
        if "templates" in f and f.endswith((".j2", ".tsx", ".ts")):
            features.append(f"Template: {Path(f).name}")

    return features


# ── Version update helpers ───────────────────────────────────────────────────

def update_version_in_file(filepath: Path, old_version: str, new_version: str,
                           dry_run: bool = False) -> bool:
    """Replace old_version with new_version in a file. Returns True if changed."""
    if not filepath.exists():
        return False
    text = filepath.read_text()
    if old_version not in text:
        return False
    new_text = text.replace(old_version, new_version)
    if new_text == text:
        return False
    if not dry_run:
        filepath.write_text(new_text)
    return True


# ── Summary generation ───────────────────────────────────────────────────────

def generate_change_summary(
    categories: Dict[str, List[str]],
    commits: List[str],
    features: List[str],
    old_version: str,
    new_version: str,
) -> str:
    """Generate a human-readable change summary."""
    lines = [
        f"# Change Summary: v{old_version} → v{new_version}",
        f"Date: {date.today().isoformat()}",
        "",
    ]

    if features:
        lines.append("## New Features")
        for f in features:
            lines.append(f"- {f}")
        lines.append("")

    lines.append("## Changed Areas")
    for cat, files in categories.items():
        lines.append(f"### {cat.title()} ({len(files)} files)")
        for f in files[:10]:  # cap at 10 per category
            lines.append(f"  - {f}")
        if len(files) > 10:
            lines.append(f"  - ... and {len(files) - 10} more")
        lines.append("")

    if commits:
        lines.append("## Recent Commits")
        for c in commits[:15]:
            lines.append(f"- {c}")
        lines.append("")

    lines.append("## Files to Update")
    for name, path in DOC_FILES.items():
        exists = "exists" if path.exists() else "MISSING"
        lines.append(f"- [{exists}] {name}: {path.relative_to(ROOT)}")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scan repo changes and update documentation files."
    )
    parser.add_argument("--version", help="New version to set (e.g. 4.3.0)")
    parser.add_argument("--auto", action="store_true",
                        help="Auto-detect version bump from commits")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without modifying files")
    parser.add_argument("--summary", action="store_true",
                        help="Print change summary only, no modifications")
    parser.add_argument("--json", action="store_true",
                        help="Output summary as JSON")
    args = parser.parse_args()

    # Gather context
    last_tag = get_last_tag()
    current_version = get_current_version()
    changed_files = get_changed_files(last_tag)
    commits = get_commits_since(last_tag)
    categories = categorize_changes(changed_files)
    features = detect_new_features(changed_files, commits)

    # Determine new version
    if args.version:
        new_version = args.version
    elif args.auto:
        bump_type = detect_bump_type(commits)
        new_version = bump_version(current_version, bump_type)
    else:
        new_version = current_version  # no bump unless requested

    if args.json:
        output = {
            "current_version": current_version,
            "new_version": new_version,
            "last_tag": last_tag,
            "changed_files": sorted(changed_files),
            "categories": categories,
            "commits": commits,
            "features": features,
            "doc_files": {k: str(v.relative_to(ROOT)) for k, v in DOC_FILES.items()},
        }
        print(json.dumps(output, indent=2))
        return

    # Generate summary
    summary = generate_change_summary(
        categories, commits, features, current_version, new_version,
    )

    if args.summary:
        print(summary)
        return

    print(summary)
    print("\n" + "=" * 60)

    if args.dry_run:
        print("\n[DRY RUN] Would update the following files:\n")

    # Apply version updates
    if new_version != current_version:
        updated = []
        for name, filepath in DOC_FILES.items():
            if update_version_in_file(filepath, current_version, new_version,
                                      dry_run=args.dry_run):
                updated.append(name)
                action = "Would update" if args.dry_run else "Updated"
                print(f"  {action} version in {filepath.relative_to(ROOT)}")

        if not args.dry_run and updated:
            print(f"\nVersion bumped: {current_version} → {new_version}")
            print(f"Updated {len(updated)} files: {', '.join(updated)}")
    else:
        print("\nNo version change requested. Use --version X.Y.Z or --auto to bump.")

    # Print what areas changed for manual review
    print("\n--- Areas requiring manual doc review ---")
    review_hints = {
        "publishing": "Update CLAUDE.md Wave 7 section, README Publishing Pipeline",
        "cli": "Update CLI Reference in README, SKILL.md, copilot-instructions.md",
        "core": "Update Architecture sections in SKILL.md, copilot-instructions.md",
        "pipeline": "Update Pipeline section in CLAUDE.md",
        "models": "Update models documentation if public API changed",
        "skills": "Update skill category counts in README, SKILL.md",
        "templates": "Note template changes in RELEASE_NOTES.md",
    }
    for cat in categories:
        if cat in review_hints:
            print(f"  [{cat}] {review_hints[cat]}")

    if not args.dry_run:
        print("\nDone. Review changes with: git diff")


if __name__ == "__main__":
    main()
