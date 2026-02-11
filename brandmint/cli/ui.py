"""
Brandmint CLI -- Rich TUI display components.
Reusable rendering functions for the launch wizard and wave executor.
"""
from typing import List, Optional, Dict, Any
from time import sleep

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.live import Live

from ..models.wave import Wave, WaveStatus
from .icons import Icons, get_status_icon, get_status_style, format_status_line


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEXT_COST_PER_SKILL = 600


# ---------------------------------------------------------------------------
# Brand banner
# ---------------------------------------------------------------------------

def render_brand_banner(config: dict, console: Console, animated: bool = True) -> None:
    """Display brand header panel with name, domain tags, execution context, and palette.
    
    Args:
        config: Brand configuration dict
        console: Rich console instance
        animated: If True, show typing animation for brand name
    """
    brand = config.get("brand", {})
    ec = config.get("execution_context", {})
    palette = config.get("theme", {}).get("palette", {})

    name = brand.get("name", "Unknown Brand")
    tags = brand.get("domain_tags", [])
    channel = ec.get("launch_channel", "dtc")
    depth = ec.get("depth_level", "focused")

    # Build palette swatch line using Rich ANSI color markup
    swatches = ""
    if palette:
        parts: list[str] = []
        for label, hex_val in list(palette.items())[:6]:
            h = hex_val.lstrip("#")
            display = label.replace("_", " ").title()
            parts.append(f"[on #{h}]  [/on #{h}] {display}")
        swatches = "\n[bold]Palette:[/bold] " + "  ".join(parts)

    # Animated brand name reveal
    if animated:
        console.print()
        with Live(console=console, refresh_per_second=30, transient=True) as live:
            for i in range(len(name) + 1):
                text = Text()
                text.append(f"  {Icons.BRAND} ", style="cyan")
                text.append(name[:i].upper(), style="bold cyan")
                text.append("▌" if i < len(name) else "", style="cyan dim")
                live.update(text)
                sleep(0.04)

    body = (
        f"[bold]{name.upper()}[/bold]\n\n"
        f"[cyan]{Icons.CHEVRON} Domain:[/cyan] {', '.join(tags) if tags else 'general'}\n"
        f"[cyan]{Icons.CHEVRON} Channel:[/cyan] {channel}  {Icons.BULLET}  "
        f"[cyan]Depth:[/cyan] {depth}"
        f"{swatches}"
    )

    console.print(Panel(body, title=f"{Icons.BRAND} BRANDMINT {Icons.DASH} Launch Wizard", border_style="cyan"))


# ---------------------------------------------------------------------------
# Scenario cards
# ---------------------------------------------------------------------------

def render_scenario_cards(matches: list, scenarios: list, console: Console) -> None:
    """Display ranked scenario recommendation panels."""
    scenario_map: Dict[str, Any] = {}
    for s in scenarios:
        key = s.id if hasattr(s, "id") else s.get("id", "")
        key = key.value if hasattr(key, "value") else str(key)
        scenario_map[key] = s

    for idx, match in enumerate(matches):
        sid = match.scenario_id if hasattr(match, "scenario_id") else match.get("scenario_id", "")
        sid_str = sid.value if hasattr(sid, "value") else str(sid)
        score = match.match_score if hasattr(match, "match_score") else match.get("match_score", 0)
        reasoning = match.reasoning if hasattr(match, "reasoning") else match.get("reasoning", "")
        pros = match.pros if hasattr(match, "pros") else match.get("pros", [])
        cons = match.cons if hasattr(match, "cons") else match.get("cons", [])

        scenario = scenario_map.get(sid_str)
        if scenario is None:
            continue

        s_name = scenario.name if hasattr(scenario, "name") else scenario.get("name", sid_str)
        s_emoji = scenario.emoji if hasattr(scenario, "emoji") else scenario.get("emoji", "")
        s_skills = scenario.skill_ids if hasattr(scenario, "skill_ids") else scenario.get("skill_ids", [])
        s_cost = scenario.estimated_cost_usd if hasattr(scenario, "estimated_cost_usd") else scenario.get("estimated_cost_usd", 0)
        s_timeline = scenario.estimated_timeline_days if hasattr(scenario, "estimated_timeline_days") else scenario.get("estimated_timeline_days", "")

        label = "  [bold green]<- RECOMMENDED[/bold green]" if idx == 0 else ""
        pct = int(score * 100)

        lines = [
            f"[bold]Match:[/bold] {pct}%{label}",
            f"[bold]Skills:[/bold] {len(s_skills)}  |  "
            f"[bold]Cost:[/bold] [green]${s_cost}[/green]  |  "
            f"[bold]Timeline:[/bold] {s_timeline}",
            f"\n{reasoning}",
        ]

        if pros:
            lines.append("")
            for p in pros:
                lines.append(f"  [green]+ {p}[/green]")
        if cons:
            for c in cons:
                lines.append(f"  [red]x {c}[/red]")

        title = f"#{idx + 1} - {s_emoji} {s_name}"
        console.print(Panel("\n".join(lines), title=title, border_style="cyan" if idx == 0 else "dim"))


# ---------------------------------------------------------------------------
# Wave table
# ---------------------------------------------------------------------------

def render_wave_table(waves: List[Wave], console: Console) -> None:
    """Display wave plan overview table with totals."""
    table = Table(show_header=True, title="Wave Plan")
    table.add_column("Wave", style="cyan", justify="right")
    table.add_column("Name")
    table.add_column("Text Skills", justify="right")
    table.add_column("Visual Assets", justify="right")
    table.add_column("Est. Cost", justify="right", style="green")

    total_text = 0
    total_visual = 0
    total_cost = 0.0

    for w in waves:
        n_text = len(w.text_skills)
        n_visual = len(w.visual_assets)
        total_text += n_text
        total_visual += n_visual
        total_cost += w.estimated_cost

        table.add_row(
            str(w.number),
            w.name,
            str(n_text) if n_text else "--",
            str(n_visual) if n_visual else "--",
            f"${w.estimated_cost:.2f}",
        )

    table.add_section()
    table.add_row(
        "",
        "[bold]TOTAL[/bold]",
        f"[bold]{total_text}[/bold]",
        f"[bold]{total_visual}[/bold]",
        f"[bold green]${total_cost:.2f}[/bold green]",
    )

    console.print()
    console.print(table)


# ---------------------------------------------------------------------------
# Wave progress
# ---------------------------------------------------------------------------

def render_wave_progress(wave: Wave, state: dict, console: Console) -> None:
    """Display execution progress for a single wave."""
    items: list[str] = []

    skills_state = state.get("text_skills", {})
    assets_state = state.get("visual_assets", {})

    if wave.text_skills:
        items.append("[bold]Text Skills[/bold]")
        for skill_id in wave.text_skills:
            s = skills_state.get(skill_id, {})
            items.append(_format_status_line(skill_id, s))

    if wave.visual_assets:
        items.append("")
        items.append("[bold]Visual Assets[/bold]")
        for asset_id in wave.visual_assets:
            a = assets_state.get(asset_id, {})
            items.append(_format_status_line(asset_id, a))

    title = f"Wave {wave.number} - {wave.name}"
    console.print(Panel("\n".join(items), title=title, border_style="cyan"))


def _format_status_line(item_id: str, info: dict) -> str:
    """Format a single skill/asset status line using standardized icons."""
    status = info.get("status", "pending")
    duration = info.get("duration_seconds")
    error = info.get("error")
    
    return format_status_line(item_id, status, duration, error)


# ---------------------------------------------------------------------------
# Skill prompt
# ---------------------------------------------------------------------------

def render_skill_prompt(skill_id: str, prompt: str, output_path: str, console: Console) -> None:
    """Display a scaffolded prompt for agent / user execution."""
    console.print(Panel(prompt, title=f"[bold]{skill_id}[/bold]", border_style="dim"))
    console.print(f"  [dim]Save output to:[/dim] {output_path}\n")


# ---------------------------------------------------------------------------
# Cost summary
# ---------------------------------------------------------------------------

def render_cost_summary(waves: List[Wave], console: Console) -> None:
    """Display budget breakdown table."""
    table = Table(show_header=True, title="Budget Breakdown")
    table.add_column("Wave", style="cyan", justify="right")
    table.add_column("Text Cost", justify="right", style="green")
    table.add_column("Visual Cost", justify="right", style="green")
    table.add_column("Total", justify="right", style="bold green")

    sum_text = 0.0
    sum_visual = 0.0

    for w in waves:
        text_cost = len(w.text_skills) * _TEXT_COST_PER_SKILL
        visual_cost = max(w.estimated_cost - text_cost, 0.0)
        sum_text += text_cost
        sum_visual += visual_cost

        table.add_row(
            f"W{w.number}",
            f"${text_cost:.2f}",
            f"${visual_cost:.2f}",
            f"${w.estimated_cost:.2f}",
        )

    table.add_section()
    table.add_row(
        "",
        f"[bold]${sum_text:.2f}[/bold]",
        f"[bold]${sum_visual:.2f}[/bold]",
        f"[bold green]${sum_text + sum_visual:.2f}[/bold green]",
    )

    console.print()
    console.print(table)


# ---------------------------------------------------------------------------
# Dry-run cost preview (detailed per-asset breakdown)
# ---------------------------------------------------------------------------

# Asset cost per seed (mirrors VISUAL_ASSET_COSTS in wave_planner.py)
_ASSET_COSTS = {
    "2A": 0.08, "2B": 0.05, "2C": 0.05,
    "3A": 0.05, "3B": 0.05, "3C": 0.05,
    "4A": 0.08, "4B": 0.05,
    "5A": 0.04, "5B": 0.08, "5C": 0.04,
    "7A": 0.08, "8A": 0.08,
    "APP-ICON": 0.05, "OG-IMAGE": 0.08, "IG-STORY": 0.08,
    "APP-SCREENSHOT": 0.08, "PITCH-HERO": 0.08,
    "TWITTER-HEADER": 0.08, "EMAIL-HERO": 0.08,
}

_ASSET_MODELS = {
    "2A": "nano-banana-pro", "2B": "flux-2-pro", "2C": "flux-2-pro",
    "3A": "flux-2-pro", "3B": "flux-2-pro", "3C": "flux-2-pro",
    "4A": "nano-banana-pro", "4B": "flux-2-pro",
    "5A": "recraft-v3", "5B": "nano-banana-pro", "5C": "recraft-v3",
    "7A": "nano-banana-pro", "8A": "nano-banana-pro",
    "APP-ICON": "flux-2-pro", "OG-IMAGE": "nano-banana-pro",
    "IG-STORY": "nano-banana-pro", "APP-SCREENSHOT": "nano-banana-pro",
    "PITCH-HERO": "nano-banana-pro", "TWITTER-HEADER": "flux-2-pro",
    "EMAIL-HERO": "nano-banana-pro",
}


def render_cost_preview(
    waves: List[Wave],
    seeds: int,
    console: Console,
    show_assets: bool = True,
) -> None:
    """Display detailed dry-run cost preview with per-asset breakdown.
    
    Args:
        waves: List of Wave objects to preview
        seeds: Number of seeds per asset
        console: Rich console instance
        show_assets: If True, show individual asset costs
    """
    console.print()
    console.print(f"[bold cyan]{Icons.SPARKLE} Cost Preview[/bold cyan] (dry-run)")
    console.print(f"[dim]Seeds per asset: {seeds}[/dim]\n")

    if show_assets:
        # Detailed asset table
        asset_table = Table(show_header=True, title="Visual Asset Costs")
        asset_table.add_column("Asset", style="cyan")
        asset_table.add_column("Model", style="dim")
        asset_table.add_column("× Seeds", justify="right")
        asset_table.add_column("Cost", justify="right", style="green")

        total_asset_cost = 0.0
        all_assets = []
        for w in waves:
            all_assets.extend(w.visual_assets)

        for asset_id in sorted(set(all_assets)):
            model = _ASSET_MODELS.get(asset_id, "unknown")
            cost_per = _ASSET_COSTS.get(asset_id, 0.08)
            cost = cost_per * seeds
            total_asset_cost += cost
            asset_table.add_row(
                asset_id,
                model,
                str(seeds),
                f"${cost:.2f}",
            )

        asset_table.add_section()
        asset_table.add_row(
            f"[bold]{len(all_assets)} assets[/bold]",
            "",
            "",
            f"[bold green]${total_asset_cost:.2f}[/bold green]",
        )
        console.print(asset_table)
        console.print()

    # Summary table
    summary_table = Table(show_header=True, title="Cost Summary")
    summary_table.add_column("Category")
    summary_table.add_column("Items", justify="right")
    summary_table.add_column("Cost", justify="right", style="green")

    total_text = sum(len(w.text_skills) for w in waves)
    total_visual = sum(len(w.visual_assets) for w in waves)
    text_cost = total_text * (_TEXT_COST_PER_SKILL / 1000)  # Convert to dollars
    visual_cost = sum(
        _ASSET_COSTS.get(a, 0.08) * seeds
        for w in waves
        for a in w.visual_assets
    )

    summary_table.add_row(
        f"{Icons.SKILL} Text Skills",
        str(total_text),
        f"${text_cost:.2f}",
    )
    summary_table.add_row(
        f"{Icons.ASSET} Visual Assets",
        str(total_visual),
        f"${visual_cost:.2f}",
    )
    summary_table.add_section()
    summary_table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{total_text + total_visual}[/bold]",
        f"[bold green]${text_cost + visual_cost:.2f}[/bold green]",
    )

    console.print(summary_table)
    console.print()
    console.print(f"[dim]{Icons.INFO} Actual costs may vary slightly based on provider and model.[/dim]")


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def prompt_scenario_selection(matches: list, console: Console) -> str:
    """Interactive scenario picker. Returns selected scenario_id string."""
    console.print("\n[bold]Select a scenario:[/bold]\n")

    for idx, match in enumerate(matches):
        sid = match.scenario_id if hasattr(match, "scenario_id") else match.get("scenario_id", "")
        sid_str = sid.value if hasattr(sid, "value") else str(sid)
        score = match.match_score if hasattr(match, "match_score") else match.get("match_score", 0)
        label = " [green](recommended)[/green]" if idx == 0 else ""
        console.print(f"  [{idx + 1}] {sid_str} ({int(score * 100)}%){label}")

    choice = IntPrompt.ask(
        "\nEnter number",
        default=1,
        console=console,
    )
    choice = max(1, min(choice, len(matches)))
    selected = matches[choice - 1]
    sid = selected.scenario_id if hasattr(selected, "scenario_id") else selected.get("scenario_id", "")
    return sid.value if hasattr(sid, "value") else str(sid)


def prompt_wave_selection(console: Console) -> Optional[str]:
    """Ask user which waves to run. Returns wave range string or None for all."""
    console.print("\n[bold]Wave execution:[/bold]\n")
    console.print("  [1] Execute all waves")
    console.print("  [2] Select wave range (e.g., 1-3)")
    console.print("  [3] Exit")

    choice = IntPrompt.ask("\nEnter choice", default=1, console=console)

    if choice == 1:
        return None
    elif choice == 2:
        return Prompt.ask("Wave range (e.g. 1-3)", console=console)
    else:
        return "exit"


# ---------------------------------------------------------------------------
# Execution summary
# ---------------------------------------------------------------------------

def render_execution_summary(state_data: dict, console: Console) -> None:
    """Final summary after execution completes."""
    waves = state_data.get("waves", {})
    total_waves = len(waves)
    completed_waves = sum(
        1 for w in waves.values()
        if w.get("status") == "completed"
    )

    total_skills = 0
    total_assets = 0
    total_cost = 0.0

    for w in waves.values():
        ts = w.get("text_skills", {})
        va = w.get("visual_assets", {})
        total_skills += sum(1 for s in ts.values() if s.get("status") == "completed")
        total_assets += sum(1 for a in va.values() if a.get("status") == "completed")
        total_cost += w.get("estimated_cost", 0.0)

    state_path = state_data.get("state_file", "execution-state.json")

    lines = [
        f"[bold]Waves completed:[/bold] {completed_waves}/{total_waves}",
        f"[bold]Text skills run:[/bold] {total_skills}",
        f"[bold]Visual assets generated:[/bold] {total_assets}",
        f"[bold]Estimated cost:[/bold] [green]${total_cost:.2f}[/green]",
        f"\n[dim]State file: {state_path}[/dim]",
    ]

    console.print()
    console.print(Panel(
        "\n".join(lines),
        title="Execution Summary",
        border_style="green",
    ))
