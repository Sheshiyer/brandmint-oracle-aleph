#!/usr/bin/env python3
"""Import and normalize skills from inference-sh/skills into Brandmint.

This script does not modify runtime behavior by itself. It prepares a
vendor snapshot and a normalized skill pack under:

- skills/external/inference-sh/upstream/<commit>/
- skills/external/inference-sh/normalized/
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPO_URL = "https://github.com/inference-sh/skills.git"

KNOWN_REF_REWRITES = {
    "@inference-sh": "@agent-tools",
    "@markdown-ui": "@chat-ui",
    "@seo": "@seo-content-brief",
    "infsh/agent-browser": "agent-browser",
}


def discover_skill_dirs(repo_dir: Path) -> List[Path]:
    """Discover skill directories across old and new upstream layouts."""
    legacy_root = repo_dir / "skills"
    if legacy_root.exists():
        return sorted([p for p in legacy_root.iterdir() if p.is_dir()], key=lambda p: str(p))

    skill_dirs: List[Path] = []
    for skill_md in sorted(repo_dir.rglob("SKILL.md"), key=lambda p: str(p)):
        if ".git" in skill_md.parts:
            continue
        skill_dirs.append(skill_md.parent)
    return skill_dirs


def run(cmd: List[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def normalize_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str, bool, bool]:
    """Return (frontmatter, body, had_frontmatter, parse_ok)."""
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


def coerce_allowed_tools(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return ["Bash(infsh *)"]


def rewrite_body(body: str) -> str:
    updated = body
    for src, dst in KNOWN_REF_REWRITES.items():
        updated = re.sub(rf"\b{re.escape(src)}\b", dst, updated)
    return updated


def infer_description(frontmatter: Dict[str, Any], body: str, slug: str) -> str:
    desc = str(frontmatter.get("description") or "").strip()
    if desc:
        return desc

    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if len(line) > 180:
            line = line[:177].rstrip() + "..."
        return line

    return f"Imported skill from inference-sh ({slug})"


def copy_upstream_snapshot(repo_tmp: Path, vendor_dest: Path) -> None:
    if vendor_dest.exists():
        shutil.rmtree(vendor_dest)

    shutil.copytree(
        repo_tmp,
        vendor_dest,
        ignore=shutil.ignore_patterns(".git"),
    )


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import inference-sh skills into Brandmint")
    parser.add_argument("--repo", default=DEFAULT_REPO_URL, help="Source git repo URL")
    parser.add_argument("--commit", default="", help="Pinned commit SHA/tag/branch")
    parser.add_argument(
        "--allowlist",
        default="",
        help="Comma-separated skill folder allowlist (default: import all)",
    )
    parser.add_argument(
        "--output-root",
        default=str(REPO_ROOT / "skills" / "external" / "inference-sh"),
        help="Output root for upstream/normalized packs",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files")
    args = parser.parse_args()

    allowlist = {
        normalize_slug(item)
        for item in args.allowlist.split(",")
        if normalize_slug(item)
    }

    out_root = Path(args.output_root).resolve()
    upstream_root = out_root / "upstream"
    normalized_root = out_root / "normalized"

    with tempfile.TemporaryDirectory(prefix="inference-skills-") as td:
        tmp = Path(td)
        repo_dir = tmp / "repo"

        run(["git", "clone", "--depth", "1", args.repo, str(repo_dir)])

        if args.commit:
            run(["git", "fetch", "--depth", "1", "origin", args.commit], cwd=repo_dir)
            run(["git", "checkout", args.commit], cwd=repo_dir)

        commit = run(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        short_commit = commit[:12]

        vendor_dest = upstream_root / short_commit

        skill_dirs = discover_skill_dirs(repo_dir)

        manifest: Dict[str, Any] = {
            "source_repo": args.repo,
            "source_commit": commit,
            "imported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "allowlist": sorted(allowlist),
            "skills": [],
            "stats": {
                "candidate_dirs": len(skill_dirs),
                "imported": 0,
                "skipped": 0,
                "frontmatter_fixed": 0,
                "reference_rewrites": 0,
            },
        }

        if args.dry_run:
            print(f"[dry-run] source commit: {commit}")
            print(f"[dry-run] upstream snapshot -> {vendor_dest}")
            print(f"[dry-run] normalized output -> {normalized_root}")
        else:
            vendor_dest.parent.mkdir(parents=True, exist_ok=True)
            copy_upstream_snapshot(repo_dir, vendor_dest)
            ensure_clean_dir(normalized_root)

        used_slugs: set[str] = set()
        for skill_dir in skill_dirs:
            basename_slug = normalize_slug(skill_dir.name)
            rel_slug = normalize_slug(str(skill_dir.relative_to(repo_dir)).replace("/", "-"))
            slug = basename_slug
            if slug in used_slugs:
                slug = rel_slug
            used_slugs.add(slug)

            if allowlist and not ({slug, basename_slug, rel_slug} & allowlist):
                manifest["stats"]["skipped"] += 1
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                manifest["stats"]["skipped"] += 1
                continue

            content = skill_md.read_text(encoding="utf-8", errors="ignore")
            frontmatter, body, had_frontmatter, parse_ok = parse_frontmatter(content)
            normalized_id = f"infsh-{slug}"
            description = infer_description(frontmatter, body, slug)
            allowed_tools = coerce_allowed_tools(frontmatter.get("allowed-tools"))

            rewritten_body = rewrite_body(body)
            rewrite_count = 0
            for src in KNOWN_REF_REWRITES:
                rewrite_count += body.count(src)

            if (not had_frontmatter) or (not parse_ok) or not frontmatter.get("name"):
                manifest["stats"]["frontmatter_fixed"] += 1
            if rewrite_count:
                manifest["stats"]["reference_rewrites"] += rewrite_count

            generated_frontmatter = {
                "name": normalized_id,
                "description": description,
                "allowed-tools": allowed_tools,
                "source_repo": args.repo,
                "source_commit": commit,
                "source_skill": slug,
            }

            new_skill = (
                "---\n"
                + yaml.safe_dump(generated_frontmatter, sort_keys=False).strip()
                + "\n---\n\n"
                + rewritten_body.lstrip("\n")
            )

            target_dir = normalized_root / normalized_id

            if not args.dry_run:
                shutil.copytree(skill_dir, target_dir, dirs_exist_ok=True)
                (target_dir / "SKILL.md").write_text(new_skill, encoding="utf-8")

            manifest["skills"].append(
                {
                    "source_slug": slug,
                    "source_basename_slug": basename_slug,
                    "source_path": str(skill_dir.relative_to(repo_dir)),
                    "normalized_id": normalized_id,
                    "target_path": str((normalized_root / normalized_id).relative_to(out_root)),
                    "had_frontmatter": had_frontmatter,
                    "frontmatter_parse_ok": parse_ok,
                    "rewrites_applied": rewrite_count,
                }
            )
            manifest["stats"]["imported"] += 1

        if args.dry_run:
            print(json.dumps(manifest["stats"], indent=2))
            return 0

        manifest_path = normalized_root / "import-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        allowlist_ids = sorted(
            {
                str(row.get("normalized_id", "")).strip()
                for row in manifest.get("skills", [])
                if str(row.get("normalized_id", "")).strip()
            }
        )
        allowlist_payload = {
            "version": 1,
            "skills": allowlist_ids,
        }
        allowlist_path = normalized_root / "allowlist.yaml"
        allowlist_path.write_text(
            yaml.safe_dump(allowlist_payload, sort_keys=False),
            encoding="utf-8",
        )

        print(f"Imported inference-sh skills @ {short_commit}")
        print(f"Upstream snapshot: {vendor_dest}")
        print(f"Normalized pack: {normalized_root}")
        print(f"Manifest: {manifest_path}")
        print(f"Allowlist: {allowlist_path}")
        print(json.dumps(manifest["stats"], indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
