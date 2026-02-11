"""
Brandmint CLI -- Launch command.

Full pipeline wizard: context analysis -> scenario recommendation ->
wave planning -> execution via WaveExecutor.

Flows
-----
Interactive (default):
    1. Load brand config
    2. Render brand banner
    3. If no scenario specified:  analyse context, recommend, prompt user
    4. Compute wave plan (filtered by scenario + depth)
    5. Render wave table + cost summary
    6. Prompt user for wave selection
    7. Build WaveExecutor and run

Dry-run (``--dry-run``):
    Steps 1-6 only -- no execution.

JSON (``--json``):
    Steps 1-4 -- print JSON, exit.

Init (``bm init``):
    Interactive questionnaire -> brand-config.yaml template.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.prompt import Prompt

console = Console()


# ---------------------------------------------------------------------------
# Public entry points (called from app.py)
# ---------------------------------------------------------------------------

def run_launch(
    config: Path,
    scenario: Optional[str] = None,
    waves: Optional[str] = None,
    dry_run: bool = False,
    json_output: bool = False,
) -> None:
    """Full pipeline wizard -- orchestrate text skills + visual assets.

    Args:
        config: Path to brand-config.yaml.
        scenario: Optional scenario ID (skip recommendation if provided).
        waves: Optional wave range string (e.g. ``"1-3"``, ``"4"``).
        dry_run: Show plan without executing.
        json_output: Agent-compatible JSON output.
    """
    from ..cli.ui import (
        render_brand_banner,
        render_scenario_cards,
        render_wave_table,
        render_cost_summary,
        prompt_scenario_selection,
        prompt_wave_selection,
    )
    from ..core.wave_planner import compute_wave_plan

    # -- 1. Load brand config -----------------------------------------------
    cfg = _load_config(config)
    ec = cfg.get("execution_context", {})
    depth = ec.get("depth_level", "focused")

    # -- 2. JSON fast-path ---------------------------------------------------
    if json_output:
        wave_plan = compute_wave_plan(cfg, scenario_id=scenario, depth=depth)
        _print_json(cfg, wave_plan, scenario, depth)
        return

    # -- 3. Brand banner -----------------------------------------------------
    render_brand_banner(cfg, console)

    # -- 4. Scenario selection -----------------------------------------------
    selected_scenario_id = scenario
    scenario_obj = None

    if selected_scenario_id is None:
        selected_scenario_id, scenario_obj = _recommend_and_select(
            cfg, render_scenario_cards, prompt_scenario_selection
        )
    else:
        # Fetch scenario object for the explicitly-provided ID.
        scenario_obj = _get_scenario_by_id(selected_scenario_id)
        if scenario_obj is None:
            console.print(
                f"[yellow]Scenario '{selected_scenario_id}' not found in "
                f"catalog -- proceeding without scenario filter.[/yellow]"
            )
            selected_scenario_id = None

    # -- 5. Wave plan --------------------------------------------------------
    wave_plan = compute_wave_plan(
        cfg, scenario_id=selected_scenario_id, depth=depth,
    )

    if not wave_plan:
        console.print("[yellow]No waves generated. Check depth and scenario.[/yellow]")
        return

    render_wave_table(wave_plan, console)
    render_cost_summary(wave_plan, console)

    # -- 6. Dry-run gate -----------------------------------------------------
    if dry_run:
        console.print(
            "\n[yellow]--dry-run: No execution. Plan displayed above.[/yellow]\n"
        )
        return

    # -- 7. Wave selection ---------------------------------------------------
    wave_range = _parse_wave_range(waves)

    if wave_range is None and waves is None:
        # Interactive: let user choose.
        wave_input = prompt_wave_selection(console)
        if wave_input == "exit":
            console.print("[dim]Exiting.[/dim]")
            return
        wave_range = _parse_wave_range(wave_input)

    # -- 8. Build execution context ------------------------------------------
    execution_context = _build_execution_context(scenario_obj, cfg)

    # -- 9. Resolve brand directory ------------------------------------------
    brand_dir = _resolve_brand_dir(config, cfg)

    # -- 10. Execute ---------------------------------------------------------
    from ..pipeline.executor import WaveExecutor

    executor = WaveExecutor(
        config=cfg,
        config_path=config.resolve(),
        waves=wave_plan,
        execution_context=execution_context,
        brand_dir=brand_dir,
        console=console,
    )

    state = executor.execute(wave_range=wave_range, interactive=True)

    # Persist scenario choice in state.
    if selected_scenario_id and state.scenario is None:
        state.scenario = selected_scenario_id

    console.print("\n[bold green]Launch complete.[/bold green]\n")


def run_init(output: Path) -> None:
    """Interactive brand config initializer."""
    console.print("\n[bold cyan]Brandmint -- Brand Config Initializer[/bold cyan]\n")

    brand_name = Prompt.ask("Brand name")
    tagline = Prompt.ask("Tagline (short memorable phrase)", default="")
    domain = Prompt.ask("Domain / industry", default="")
    domain_tags = Prompt.ask(
        "Domain tags (comma-separated, e.g. app,marketplace,lifestyle)",
        default="",
    )
    channel = Prompt.ask(
        "Launch channel",
        choices=["dtc", "kickstarter", "indiegogo", "organic", "enterprise", "saas"],
        default="dtc",
    )
    depth = Prompt.ask(
        "Execution depth",
        choices=["surface", "focused", "comprehensive", "exhaustive"],
        default="focused",
    )

    tags_list = [t.strip() for t in domain_tags.split(",") if t.strip()]

    config = {
        "execution_context": {
            "budget_tier": "lean",
            "launch_channel": channel,
            "maturity_stage": "pre-launch",
            "depth_level": depth,
            "tone": "conversion-focused",
            "quality_bar": "standard",
        },
        "brand": {
            "name": brand_name,
            "tagline": tagline,
            "archetype": "",
            "voice": "",
            "domain": domain,
            "domain_tags": tags_list,
        },
        "theme": {
            "name": "",
            "description": "",
            "metaphor": "",
            "mood_keywords": [],
        },
        "palette": {
            "primary": {"name": "", "hex": "#000000", "role": "60% backgrounds"},
            "secondary": {"name": "", "hex": "#FFFFFF", "role": "30% text and surfaces"},
            "accent": {"name": "", "hex": "#FF0000", "role": "10% CTAs and highlights"},
        },
        "typography": {
            "header": {"font": "Inter", "weights": ["Regular", "Bold"]},
            "body": {"font": "Inter", "weights": ["Regular"]},
        },
        "generation": {
            "output_dir": "generated",
            "seeds": [42, 137],
            "resolution": "2K",
            "output_format": "png",
            "env_file": "~/.claude/.env",
        },
    }

    out = Path(output)
    out.write_text(
        yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
    )
    console.print(f"\n[green]Config saved to:[/green] {out.resolve()}")
    console.print("[dim]Edit the file to fill in palette, typography, and theme.[/dim]\n")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_config(config_path: Path) -> dict:
    """Load and validate brand config YAML."""
    if not config_path.exists():
        console.print(f"[red]Config not found: {config_path}[/red]")
        sys.exit(1)
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        console.print("[red]Invalid config: expected YAML dict[/red]")
        sys.exit(1)
    return cfg


def _print_json(cfg: dict, waves: list, scenario_id: Optional[str], depth: str) -> None:
    """Output agent-compatible JSON and exit."""
    output = {
        "brand": cfg.get("brand", {}).get("name", "Unknown"),
        "domain_tags": cfg.get("brand", {}).get("domain_tags", []),
        "depth": depth,
        "scenario": scenario_id,
        "waves": [w.to_dict() for w in waves],
        "total_cost": round(sum(w.estimated_cost for w in waves), 2),
    }
    print(json.dumps(output, indent=2))


def _build_product_from_config(cfg: dict):
    """Build ProductData from brand-config.yaml.

    Maps brand config fields into the Pydantic model that
    ContextAnalyzer and ScenarioRecommender expect.
    """
    from ..models.product import (
        ProductData,
        ProductBrand,
        LaunchContext,
        LaunchChannel,
        BudgetTier,
    )

    brand = cfg.get("brand", {})
    ec = cfg.get("execution_context", {})

    channel_map = {
        "kickstarter": LaunchChannel.KICKSTARTER,
        "indiegogo": LaunchChannel.INDIEGOGO,
        "dtc": LaunchChannel.DTC,
        "saas": LaunchChannel.SAAS,
        "enterprise": LaunchChannel.ENTERPRISE,
        "organic": LaunchChannel.ORGANIC,
    }
    channel = channel_map.get(ec.get("launch_channel", "dtc"), LaunchChannel.DTC)

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


def _recommend_and_select(cfg: dict, render_cards, prompt_select) -> tuple:
    """Run context analysis + recommendation + user selection.

    Returns:
        ``(selected_scenario_id, scenario_object)`` tuple.
    """
    from ..core.context_analyzer import ContextAnalyzer
    from ..core.scenario_recommender import ScenarioRecommender

    # Build ProductData from config.
    product = _build_product_from_config(cfg)

    # Context analysis.
    analyzer = ContextAnalyzer()
    context = analyzer.analyze(product)
    product.launch_context = context

    # Recommend scenarios.
    recommender = ScenarioRecommender()
    matches = recommender.recommend(product, context, limit=3)

    # Display recommendation cards.
    all_scenarios = recommender.scenarios
    render_cards(matches, all_scenarios, console)

    # User selects.
    selected_id = prompt_select(matches, console)

    # Fetch the full scenario object.
    scenario_obj = _get_scenario_by_id(selected_id)
    return selected_id, scenario_obj


def _get_scenario_by_id(scenario_id: str):
    """Retrieve a Scenario object from the catalog.  Returns None on miss."""
    from ..core.scenario_recommender import ScenarioRecommender

    try:
        recommender = ScenarioRecommender()
        return recommender.get_scenario(scenario_id)
    except (ValueError, Exception):
        return None


def _build_execution_context(scenario_obj, cfg: dict):
    """Extract or synthesise an ExecutionContext.

    Uses the scenario's embedded context when available, otherwise
    builds a reasonable default from the brand config.
    """
    from ..models.scenario import ExecutionContext

    if scenario_obj is not None:
        return scenario_obj.execution_context

    # Fallback: build from config.
    ec = cfg.get("execution_context", {})
    return ExecutionContext(
        budget_tier=ec.get("budget_tier", "lean"),
        tone=ec.get("tone", "balanced"),
        output_format="standard",
        depth_level=ec.get("depth_level", "focused"),
        quality_bar=ec.get("quality_bar", "standard"),
        token_limit_per_skill=5000,
        prioritize="balanced",
    )


def _resolve_brand_dir(config_path: Path, cfg: dict) -> Path:
    """Determine brand working directory from config path.

    If the config lives under ``brands/{slug}/brand-config.yaml``, use
    that parent directory.  Otherwise use the config's parent.
    """
    parent = config_path.resolve().parent

    # If path looks like brands/{slug}/brand-config.yaml, use parent.
    if parent.parent.name == "brands":
        return parent

    return parent


def _parse_wave_range(waves_str: Optional[str]) -> Optional[range]:
    """Parse a wave range string into a Python range.

    Examples::

        "1-3"  -> range(1, 4)
        "3"    -> range(3, 4)
        None   -> None
        ""     -> None
    """
    if not waves_str:
        return None

    waves_str = waves_str.strip()
    if not waves_str:
        return None

    try:
        if "-" in waves_str:
            start, end = waves_str.split("-", 1)
            return range(int(start.strip()), int(end.strip()) + 1)
        else:
            n = int(waves_str)
            return range(n, n + 1)
    except ValueError:
        console.print(f"[red]Invalid wave range: '{waves_str}'[/red]")
        return None
