"""
Brandmint CLI — Plan subcommands.
Ported from orchv2 CLI (context analysis, scenario recommendation, comparison).
"""
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _load_brand_config(config_path: Path) -> dict:
    """Load brand config YAML."""
    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)


def _build_product_from_config(cfg: dict):
    """Build orchv2 ProductData from brand-config.yaml."""
    from ..models.product import ProductData, ProductBrand, LaunchContext, LaunchChannel, BudgetTier

    brand = cfg.get("brand", {})
    ec = cfg.get("execution_context", {})

    # Map channel string to enum
    channel_map = {
        "kickstarter": LaunchChannel.KICKSTARTER,
        "indiegogo": LaunchChannel.INDIEGOGO,
        "dtc": LaunchChannel.DTC,
        "saas": LaunchChannel.SAAS,
        "enterprise": LaunchChannel.ENTERPRISE,
    }
    channel = channel_map.get(ec.get("launch_channel", "dtc"), LaunchChannel.DTC)

    # Map budget tier
    budget_map = {
        "bootstrapped": BudgetTier.BOOTSTRAPPED,
        "lean": BudgetTier.LEAN,
        "standard": BudgetTier.STANDARD,
        "premium": BudgetTier.PREMIUM,
    }
    budget_tier = budget_map.get(ec.get("budget_tier", "standard"), BudgetTier.STANDARD)

    return ProductData(
        brand=ProductBrand(
            name=brand.get("name", "Unknown"),
            category=brand.get("domain", "general"),
            primary_promise=brand.get("tagline", ""),
            pillars=brand.get("identity_pillars", []),
        ),
        launch_context=LaunchContext(
            channel=channel,
            budget_tier=budget_tier,
            budget_amount=ec.get("budget_amount"),
            timeline_weeks=ec.get("timeline_weeks"),
            team_count=ec.get("team_count"),
        ),
        price=cfg.get("commercial", {}).get("price"),
    )


def run_context(config: Path):
    """Analyze brand context — detect 6 business dimensions."""
    console.print("\n[bold cyan]Analyzing Brand Context...[/bold cyan]\n")

    cfg = _load_brand_config(config)
    product = _build_product_from_config(cfg)

    from ..core.context_analyzer import ContextAnalyzer
    analyzer = ContextAnalyzer()
    context = analyzer.analyze(product)
    explanations = analyzer.explain_detection(product, context)

    # Display
    budget_str = f"${context.budget_amount:,}" if context.budget_amount else context.budget_tier.value
    timeline_str = f"{context.timeline_weeks} weeks" if context.timeline_weeks else context.timeline_urgency.value
    team_str = f"{context.team_count} people" if context.team_count else context.team_size.value

    console.print(Panel(
        f"[cyan]Channel:[/cyan] {context.channel.value}\n"
        f"[dim]{explanations.get('channel', '')}[/dim]\n\n"
        f"[cyan]Budget:[/cyan] {budget_str}\n"
        f"[dim]{explanations.get('budget_tier', '')}[/dim]\n\n"
        f"[cyan]Maturity:[/cyan] {context.maturity_stage.value}\n"
        f"[dim]{explanations.get('maturity', '')}[/dim]\n\n"
        f"[cyan]Timeline:[/cyan] {timeline_str}\n"
        f"[dim]{explanations.get('urgency', '')}[/dim]\n\n"
        f"[cyan]Team:[/cyan] {team_str}\n"
        f"[dim]{explanations.get('team_size', '')}[/dim]",
        title=f"Detected Context — {cfg.get('brand', {}).get('name', 'Unknown')}",
        border_style="green",
    ))

    console.print("\n✓ Context analysis complete\n", style="bold green")


def run_recommend(config: Path, limit: int = 3):
    """Recommend execution scenarios."""
    console.print("\n[bold cyan]Generating Scenario Recommendations...[/bold cyan]\n")

    cfg = _load_brand_config(config)
    product = _build_product_from_config(cfg)

    from ..core.context_analyzer import ContextAnalyzer
    from ..core.scenario_recommender import ScenarioRecommender

    analyzer = ContextAnalyzer()
    context = analyzer.analyze(product)
    product.launch_context = context

    recommender = ScenarioRecommender()
    matches = recommender.recommend(product, context, limit=limit)

    # Compact context
    budget_str = f"${context.budget_amount:,}" if context.budget_amount else context.budget_tier.value
    console.print(Panel(
        f"[cyan]Channel:[/cyan] {context.channel.value}  "
        f"[cyan]Budget:[/cyan] {budget_str}  "
        f"[cyan]Timeline:[/cyan] {context.timeline_urgency.value}  "
        f"[cyan]Team:[/cyan] {context.team_size.value}",
        title="Detected Context",
        border_style="dim",
    ))

    # Scenario cards
    console.print("\n[bold]Recommended Scenarios:[/bold]\n")
    for i, match in enumerate(matches, 1):
        scenario = recommender.get_scenario(match.scenario_id)
        match_pct = int(match.match_score * 100)
        pros_str = "\n".join(f"  ✓ {p}" for p in match.pros) if match.pros else "  [dim]None[/dim]"
        cons_str = "\n".join(f"  ✗ {c}" for c in match.cons) if match.cons else "  [dim]None[/dim]"

        title = f"#{i} - {scenario.emoji} {scenario.name}"
        if i == 1:
            title += " ← RECOMMENDED"

        console.print(Panel(
            f"[bold]{scenario.description}[/bold]\n\n"
            f"[cyan]Match:[/cyan] {match_pct}% — {match.reasoning}\n"
            f"[cyan]Skills:[/cyan] {len(scenario.skill_ids)}\n"
            f"[cyan]Est. Cost:[/cyan] ${scenario.estimated_cost_usd:,}\n"
            f"[cyan]Timeline:[/cyan] {scenario.estimated_timeline_days}\n\n"
            f"[green]Pros:[/green]\n{pros_str}\n\n"
            f"[yellow]Cons:[/yellow]\n{cons_str}",
            title=title,
            border_style="green" if i == 1 else "cyan",
        ))

    console.print("\n✓ Recommendations complete\n", style="bold green")


def run_compare(scenarios_str: str):
    """Compare scenarios side-by-side."""
    scenario_ids = [s.strip() for s in scenarios_str.split(",")]
    console.print("\n[bold cyan]Scenario Comparison[/bold cyan]\n")

    from ..core.scenario_recommender import ScenarioRecommender
    from ..models.scenario import ScenarioType

    recommender = ScenarioRecommender()
    table = Table(title="Scenario Comparison", show_header=True)
    table.add_column("Metric", style="cyan")

    scenario_objs = []
    for sid in scenario_ids:
        try:
            scenario = recommender.get_scenario(ScenarioType(sid))
            scenario_objs.append(scenario)
            table.add_column(f"{scenario.emoji} {scenario.name.split('(')[0].strip()}")
        except ValueError:
            console.print(f"[yellow]Warning: Unknown scenario '{sid}', skipping[/yellow]")

    if not scenario_objs:
        console.print("[red]No valid scenarios to compare[/red]")
        return

    table.add_row("Skills", *[str(len(s.skill_ids)) for s in scenario_objs])
    table.add_row("Est. Cost", *[f"${s.estimated_cost_usd:,}" for s in scenario_objs])
    table.add_row("Timeline", *[s.estimated_timeline_days for s in scenario_objs])
    table.add_row("Budget Tier", *[s.best_for_budget.value for s in scenario_objs])
    table.add_row("Quality", *[s.execution_context.quality_bar for s in scenario_objs])

    console.print(table)
    console.print()
