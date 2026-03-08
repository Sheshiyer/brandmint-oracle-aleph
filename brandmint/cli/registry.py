"""
Brandmint CLI — Registry subcommands.
Unified skill registry management (text + visual + meta skills).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.skills_registry import SkillsRegistry

console = Console()


def _load_visual_assets() -> List[Dict[str, object]]:
    """Load visual assets from asset-registry.yaml."""
    visual_skills: List[Dict[str, object]] = []
    registry_path = Path(__file__).resolve().parent.parent.parent / "assets" / "asset-registry.yaml"

    if not registry_path.exists():
        return visual_skills

    try:
        import yaml

        with open(registry_path) as f:
            registry = yaml.safe_load(f) or {}

        for asset_id, asset_def in registry.get("assets", {}).items():
            visual_skills.append(
                {
                    "id": asset_id,
                    "name": asset_def.get("name", asset_id),
                    "model": asset_def.get("model", ""),
                    "tags": asset_def.get("tags", []),
                }
            )
    except Exception as e:
        console.print(f"[yellow]Warning: failed to read visual registry: {e}[/yellow]")

    return visual_skills


def _truncate(text: str, limit: int = 72) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def run_list(source: Optional[str] = None, tags: Optional[str] = None):
    """List all registered skills."""
    console.print("\n[bold cyan]Unified Skill Registry[/bold cyan]\n")

    registry = SkillsRegistry(conflict_policy="warn_skip")
    text_skills = sorted(registry.get_all_skills(), key=lambda s: s.id)
    visual_skills = _load_visual_assets()

    # Filter by source
    show_text = source in (None, "all", "text")
    show_visual = source in (None, "all", "visual")

    # Filter by tags
    tag_filter = set(tags.split(",")) if tags else None

    if show_text:
        table = Table(title=f"Text Skills ({len(text_skills)})", show_header=True)
        table.add_column("ID", style="cyan", max_width=34)
        table.add_column("Name", max_width=32)
        table.add_column("Source", style="magenta", max_width=14)
        table.add_column("Description", style="dim", max_width=72)

        for skill in text_skills:
            table.add_row(skill.id, skill.name, skill.source.value, _truncate(skill.description))

        console.print(table)
        console.print()

    if show_visual:
        table = Table(title=f"Visual Assets ({len(visual_skills)})", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Model", style="dim")
        table.add_column("Tags", style="dim")

        displayed = 0
        for asset in visual_skills:
            tags_list = asset.get("tags", []) or []
            if tag_filter and not tag_filter.intersection(set(tags_list)):
                continue
            displayed += 1
            table.add_row(
                str(asset.get("id", "")),
                str(asset.get("name", "")),
                str(asset.get("model", "")),
                ", ".join([str(t) for t in tags_list[:4]]),
            )

        console.print(table)
        console.print()

    console.print(
        f"  Total: [bold]{len(text_skills)}[/bold] text skills + "
        f"[bold]{len(visual_skills)}[/bold] visual assets\n"
    )

    conflicts = registry.get_conflicts()
    if conflicts:
        console.print(
            f"[yellow]Detected {len(conflicts)} skill ID conflict(s). "
            f"Run `bm registry doctor` for details.[/yellow]"
        )


def run_sync(output: Optional[Path] = None):
    """Sync registry to JSON file."""
    registry = SkillsRegistry(conflict_policy="warn_skip")
    output_path = output or (Path.cwd() / ".brandmint" / "registry.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    registry.sync_to_file(output_path)


def run_info(skill_id: str):
    """Show detailed info about a skill."""
    console.print(f"\n[bold cyan]Skill: {skill_id}[/bold cyan]\n")

    registry = SkillsRegistry(conflict_policy="warn_skip")
    skill = registry.get_skill(skill_id)

    if skill is not None:
        alias_note = ""
        normalized_id = skill_id.strip().lower()
        if normalized_id != skill.id:
            alias_note = f"\n[cyan]Resolved As:[/cyan] {skill.id}"

        console.print(
            Panel(
                f"[cyan]ID:[/cyan] {skill.id}\n"
                f"[cyan]Name:[/cyan] {skill.name}\n"
                f"[cyan]Source:[/cyan] {skill.source.value}\n"
                f"[cyan]Path:[/cyan] {skill.skill_md_path or '-'}\n"
                f"[cyan]Complexity:[/cyan] {skill.metadata.complexity}\n"
                f"[cyan]Est. Tokens:[/cyan] {skill.metadata.estimated_tokens}\n"
                f"[cyan]Description:[/cyan] {skill.description or '-'}"
                f"{alias_note}",
                title=f"Text Skill: {skill.id}",
                border_style="cyan",
            )
        )
        return

    # Check visual assets
    for asset in _load_visual_assets():
        if asset.get("id") == skill_id:
            console.print(
                Panel(
                    f"[cyan]Name:[/cyan] {asset.get('name', skill_id)}\n"
                    f"[cyan]Model:[/cyan] {asset.get('model', 'unknown')}\n"
                    f"[cyan]Tags:[/cyan] {', '.join(asset.get('tags', []))}",
                    title=f"Visual Asset: {skill_id}",
                    border_style="green",
                )
            )
            return

    console.print(f"[red]Skill '{skill_id}' not found in any registry[/red]")


def run_doctor(strict: bool = False) -> int:
    """Run registry diagnostics.

    Returns process-like status code (0=ok, 1=issues found in strict mode).
    """
    registry = SkillsRegistry(conflict_policy="warn_skip")

    from ..core.wave_planner import WAVE_DEFINITIONS

    checks: List[tuple[str, str, str]] = []

    local_dir = registry.brand_skills_dir
    claude_dir = registry.claude_skills_dir

    checks.append(
        (
            "Local skills directory",
            str(local_dir),
            "pass" if local_dir.exists() else "fail",
        )
    )
    checks.append(
        (
            "Claude skills directory",
            str(claude_dir),
            "pass" if claude_dir.exists() else "warn",
        )
    )

    all_skills = registry.get_all_skills()
    checks.append(
        (
            "Discovered text skills",
            str(len(all_skills)),
            "pass" if len(all_skills) > 0 else "fail",
        )
    )

    conflicts = registry.get_conflicts()
    checks.append(
        (
            "ID conflicts",
            str(len(conflicts)),
            "pass" if len(conflicts) == 0 else "warn",
        )
    )

    aliases = registry.get_aliases()
    checks.append(("Alias mappings", str(len(aliases)), "pass" if aliases else "warn"))

    # Wave skill resolvability check.
    required_wave_skills = sorted(
        {
            skill_id
            for wave_def in WAVE_DEFINITIONS.values()
            for skill_id in wave_def.get("text_skills", [])
        }
    )
    unresolved = [skill_id for skill_id in required_wave_skills if registry.get_skill(skill_id) is None]
    checks.append(
        (
            "Wave text skill resolvability",
            f"{len(required_wave_skills) - len(unresolved)}/{len(required_wave_skills)}",
            "pass" if not unresolved else "fail",
        )
    )

    table = Table(title="Registry Doctor", show_header=True, header_style="bold cyan")
    table.add_column("Check")
    table.add_column("Value", style="dim")
    table.add_column("Status")

    for name, value, status in checks:
        color = {
            "pass": "green",
            "warn": "yellow",
            "fail": "red",
        }.get(status, "white")
        table.add_row(name, value, f"[{color}]{status}[/{color}]")

    console.print()
    console.print(table)
    console.print()

    if unresolved:
        console.print("[red]Unresolved wave skill IDs:[/red]")
        for sid in unresolved:
            console.print(f"  - {sid}")
        console.print()

    if conflicts:
        conflict_table = Table(
            title=f"Conflicts ({len(conflicts)})",
            show_header=True,
            header_style="bold yellow",
        )
        conflict_table.add_column("Skill ID", style="cyan")
        conflict_table.add_column("Existing", style="dim", max_width=48)
        conflict_table.add_column("Incoming", style="dim", max_width=48)

        for c in conflicts[:20]:
            conflict_table.add_row(
                c.get("skill_id", ""),
                c.get("existing_path") or c.get("existing_source", ""),
                c.get("incoming_path") or c.get("incoming_source", ""),
            )

        console.print(conflict_table)
        console.print()

    issues_found = bool(unresolved or conflicts or any(status == "fail" for _, _, status in checks))
    if strict and issues_found:
        console.print("[red]Registry doctor failed in strict mode.[/red]")
        return 1

    if issues_found:
        console.print("[yellow]Registry doctor found issues. Review output above.[/yellow]")
    else:
        console.print("[green]Registry doctor passed.[/green]")

    return 0
