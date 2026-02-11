"""
Brandmint CLI — Registry subcommands.
Unified skill registry management (text + visual + meta skills).
"""
import os
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def _get_skills_dirs():
    """Get skill directory paths."""
    return {
        "claude": os.path.expanduser("~/.claude/skills"),
        "orchv2": os.path.join(os.path.dirname(__file__), "..", "..", "..",
                               "..", "claude-skills", ".claude", "skills"),
    }


def run_list(source: Optional[str] = None, tags: Optional[str] = None):
    """List all registered skills."""
    console.print("\n[bold cyan]Unified Skill Registry[/bold cyan]\n")

    # Discover text skills from ~/.claude/skills/
    skills_dir = os.path.expanduser("~/.claude/skills")
    text_skills = []
    visual_skills = []

    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, entry)
            if not os.path.isdir(skill_path):
                continue
            # Check for skill.md
            skill_md = os.path.join(skill_path, "skill.md")
            instructions_md = os.path.join(skill_path, "instructions.md")
            has_skill = os.path.exists(skill_md) or os.path.exists(instructions_md)
            if has_skill:
                # Parse name from frontmatter
                md_path = skill_md if os.path.exists(skill_md) else instructions_md
                name = entry
                desc = ""
                try:
                    with open(md_path) as f:
                        content = f.read(500)
                    if content.startswith("---"):
                        import yaml
                        fm_end = content.index("---", 3)
                        fm = yaml.safe_load(content[3:fm_end])
                        name = fm.get("name", entry)
                        desc = fm.get("description", "")[:60]
                except Exception:
                    pass
                text_skills.append({"id": entry, "name": name, "desc": desc})

    # Discover visual assets from asset-registry.yaml
    registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "asset-registry.yaml")
    if os.path.exists(registry_path):
        try:
            import yaml
            with open(registry_path) as f:
                registry = yaml.safe_load(f)
            for asset_id, asset_def in registry.get("assets", {}).items():
                visual_skills.append({
                    "id": asset_id,
                    "name": asset_def.get("name", asset_id),
                    "model": asset_def.get("model", ""),
                    "tags": asset_def.get("tags", []),
                })
        except Exception:
            pass

    # Filter by source
    show_text = source in (None, "all", "text")
    show_visual = source in (None, "all", "visual")

    # Filter by tags
    tag_filter = set(tags.split(",")) if tags else None

    # Display
    if show_text:
        table = Table(title=f"Text Skills ({len(text_skills)})", show_header=True)
        table.add_column("ID", style="cyan", max_width=30)
        table.add_column("Name", max_width=30)
        table.add_column("Description", style="dim", max_width=60)

        for skill in text_skills:
            table.add_row(skill["id"], skill["name"], skill["desc"])

        console.print(table)
        console.print()

    if show_visual:
        table = Table(title=f"Visual Assets ({len(visual_skills)})", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Model", style="dim")
        table.add_column("Tags", style="dim")

        for asset in visual_skills:
            if tag_filter and not tag_filter.intersection(set(asset["tags"])):
                continue
            table.add_row(
                asset["id"],
                asset["name"],
                asset["model"],
                ", ".join(asset["tags"][:4]),
            )

        console.print(table)
        console.print()

    console.print(f"  Total: [bold]{len(text_skills)}[/bold] text skills + [bold]{len(visual_skills)}[/bold] visual assets\n")


def run_sync():
    """Sync registry to JSON file."""
    console.print("[yellow]Registry sync: coming in Session 3[/yellow]")


def run_info(skill_id: str):
    """Show detailed info about a skill."""
    console.print(f"\n[bold cyan]Skill: {skill_id}[/bold cyan]\n")

    # Check text skills
    skill_dir = os.path.expanduser(f"~/.claude/skills/{skill_id}")
    if os.path.isdir(skill_dir):
        for md_name in ["skill.md", "instructions.md"]:
            md_path = os.path.join(skill_dir, md_name)
            if os.path.exists(md_path):
                with open(md_path) as f:
                    content = f.read(2000)
                console.print(Panel(content[:1500], title=f"Text Skill: {skill_id}", border_style="cyan"))
                return

    # Check visual assets
    registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "asset-registry.yaml")
    if os.path.exists(registry_path):
        import yaml
        with open(registry_path) as f:
            registry = yaml.safe_load(f)
        asset = registry.get("assets", {}).get(skill_id)
        if asset:
            console.print(Panel(
                f"[cyan]Name:[/cyan] {asset.get('name', skill_id)}\n"
                f"[cyan]Generator:[/cyan] {asset.get('generator', 'unknown')}\n"
                f"[cyan]Model:[/cyan] {asset.get('model', 'unknown')}\n"
                f"[cyan]Tags:[/cyan] {', '.join(asset.get('tags', []))}\n"
                f"[cyan]Priority:[/cyan] {asset.get('priority', 5)}\n"
                f"[cyan]Required:[/cyan] {asset.get('required', False)}\n"
                f"[cyan]Aspect:[/cyan] {asset.get('aspect', 'unknown')}\n"
                f"[cyan]Cost/seed:[/cyan] ${asset.get('cost_usd', 0.08):.2f}",
                title=f"Visual Asset: {skill_id}",
                border_style="green",
            ))
            return

    console.print(f"[red]Skill '{skill_id}' not found in any registry[/red]")
