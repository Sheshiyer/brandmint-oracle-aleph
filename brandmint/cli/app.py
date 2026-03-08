"""
Brandmint CLI — Unified brand creation orchestrator.

Entry points:
  brandmint [command]
  bm [command]
"""
import typer
from typing import Optional
from pathlib import Path
from rich.console import Console

console = Console()

# Global state for verbose/debug flags
_verbose = False
_debug = False

# Main app
app = typer.Typer(
    name="brandmint",
    help="Brandmint — Unified brand creation orchestrator (text + visuals + campaigns)",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug output (very detailed)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress most output"),
):
    """Brandmint — Unified brand creation orchestrator."""
    global _verbose, _debug
    _verbose = verbose
    _debug = debug
    
    from .logging import setup_logging
    setup_logging(verbose=verbose, debug=debug, quiet=quiet)


# Subcommand groups
plan_app = typer.Typer(help="Scenario planning and context analysis", no_args_is_help=True)
visual_app = typer.Typer(help="Visual asset pipeline (generate, execute, preview)", no_args_is_help=True)
registry_app = typer.Typer(help="Unified skill registry management", no_args_is_help=True)
install_app = typer.Typer(help="Installation and setup utilities", no_args_is_help=True)
cache_app = typer.Typer(help="Prompt and asset cache management", no_args_is_help=True)
publish_app = typer.Typer(help="Post-pipeline publishing (NotebookLM)", no_args_is_help=True)

app.add_typer(plan_app, name="plan")
app.add_typer(visual_app, name="visual")
app.add_typer(registry_app, name="registry")
app.add_typer(install_app, name="install")
app.add_typer(cache_app, name="cache")
app.add_typer(publish_app, name="publish")


# ━━━ Top-level commands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.command()
def launch(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    scenario: Optional[str] = typer.Option(None, "--scenario", "-s", help="Scenario ID (skip recommendation)"),
    waves: Optional[str] = typer.Option(None, "--waves", "-w", help="Wave range to run (e.g., 1-3, 3, 4-6)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing"),
    json_output: bool = typer.Option(False, "--json", help="Agent-compatible JSON output"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", help="Abort if estimated cost exceeds budget (USD)"),
    resume_from: Optional[int] = typer.Option(None, "--resume-from", help="Resume from specific wave number"),
    webhook: Optional[str] = typer.Option(None, "--webhook", help="Webhook URL for completion notification"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Skip all interactive prompts (for agent/CI environments)"),
):
    """Full pipeline wizard — text skills + visual assets in orchestrated waves."""
    from .launch import run_launch
    run_launch(
        config,
        scenario=scenario,
        waves=waves,
        dry_run=dry_run,
        json_output=json_output,
        max_cost=max_cost,
        resume_from=resume_from,
        webhook=webhook,
        non_interactive=non_interactive,
    )


@app.command()
def init(
    output: Path = typer.Option("brand-config.yaml", "--output", "-o", help="Output file path"),
):
    """Initialize a new brand config file interactively."""
    from .launch import run_init
    run_init(output)


# ASCII Art Logo
LOGO = """
[cyan]╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗ ██████╗  █████╗ ███╗   ██╗██████╗ ███╗   ███╗  ║
║   ██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗████╗ ████║  ║
║   ██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║██╔████╔██║  ║
║   ██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██║  ██║██║╚██╔╝██║  ║
║   ██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝██║ ╚═╝ ██║  ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝     ╚═╝  ║
║   [bold]██╗███╗   ██╗████████╗[/bold]                                 ║
║   [bold]██║████╗  ██║╚══██╔══╝[/bold]    [white]Unified Brand Orchestrator[/white]   ║
║   [bold]██║██╔██╗ ██║   ██║[/bold]                                    ║
║   [bold]██║██║╚██╗██║   ██║[/bold]       [dim]text • visuals • campaigns[/dim]  ║
║   [bold]██║██║ ╚████║   ██║[/bold]                                    ║
║   [bold]╚═╝╚═╝  ╚═══╝   ╚═╝[/bold]                                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝[/cyan]
"""


@app.command()
def version():
    """Show version information."""
    from .. import __version__
    console.print(LOGO)
    console.print(f"  [bold]Version:[/bold] [cyan]{__version__}[/cyan]")
    console.print(f"  [bold]Python:[/bold]  [dim]{__import__('sys').version.split()[0]}[/dim]")
    console.print()


# ━━━ Plan subcommands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@plan_app.command("context")
def plan_context(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
):
    """Analyze brand context (budget, channel, maturity, timeline, team, depth)."""
    from .plan import run_context
    run_context(config)


@plan_app.command("recommend")
def plan_recommend(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    limit: int = typer.Option(3, "--limit", "-l", help="Number of scenarios to recommend"),
):
    """Recommend execution scenarios based on detected context."""
    from .plan import run_recommend
    run_recommend(config, limit=limit)


@plan_app.command("compare")
def plan_compare(
    scenarios: str = typer.Option(..., "--scenarios", "-s", help="Comma-separated scenario IDs"),
):
    """Compare multiple scenarios side-by-side."""
    from .plan import run_compare
    run_compare(scenarios)


# ━━━ Visual subcommands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@visual_app.command("generate")
def visual_generate(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Override output directory"),
    assets: Optional[str] = typer.Option(None, "--assets", "-a", help="Comma-separated asset IDs"),
    asset_mode: str = typer.Option("generate", "--asset-mode", "-m", help="Asset generation mode: generate|composite|inpaint|hybrid"),
):
    """Generate pipeline scripts from brand config."""
    from .visual import run_generate
    run_generate(config, output_dir=output_dir, assets=assets, asset_mode=asset_mode)


@visual_app.command("execute")
def visual_execute(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    batch: str = typer.Option("all", "--batch", "-b", help="Batch to run: anchor, identity, products, etc."),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o"),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass cache, regenerate all assets"),
    asset_mode: str = typer.Option("generate", "--asset-mode", "-m", help="Asset generation mode: generate|composite|inpaint|hybrid"),
):
    """Execute generated pipeline scripts."""
    from .visual import run_execute
    run_execute(config, batch=batch, output_dir=output_dir, force=force, asset_mode=asset_mode)


@visual_app.command("preview")
def visual_preview(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    assets: Optional[str] = typer.Option(None, "--assets", "-a", help="Comma-separated asset IDs"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON (for agents)"),
):
    """Preview budget and smart recommendations."""
    from .visual import run_preview
    run_preview(config, assets=assets, json_output=json_output)


@visual_app.command("status")
def visual_status(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o"),
):
    """Show which assets exist and which are missing."""
    from .visual import run_status
    run_status(config, output_dir=output_dir)


@visual_app.command("verify")
def visual_verify(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o"),
):
    """Validate all generated asset files."""
    from .visual import run_verify
    run_verify(config, output_dir=output_dir)


# ━━━ Registry subcommands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@registry_app.command("list")
def registry_list(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter: text, visual, meta, or all"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Filter by domain tags (comma-separated)"),
):
    """List all registered skills (text + visual)."""
    from .registry import run_list
    run_list(source=source, tags=tags)


@registry_app.command("sync")
def registry_sync(
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output JSON path (default: ./.brandmint/registry.json)",
    ),
):
    """Sync skill registry to JSON file."""
    from .registry import run_sync
    run_sync(output=output)


@registry_app.command("info")
def registry_info(
    skill_id: str = typer.Argument(..., help="Skill ID to show details for"),
):
    """Show detailed information about a specific skill."""
    from .registry import run_info
    run_info(skill_id)


@registry_app.command("doctor")
def registry_doctor(
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with non-zero status if issues are found",
    ),
):
    """Run registry diagnostics (conflicts, aliases, skill resolvability)."""
    from .registry import run_doctor

    code = run_doctor(strict=strict)
    if code != 0:
        raise typer.Exit(code=code)


# ━━━ Install subcommands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@install_app.command("skills")
def install_skills():
    """Create skill symlinks in ~/.claude/skills/."""
    from ..installer.setup_skills import install_skills as _install
    _install(console=console)


@install_app.command("check")
def install_check(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Provider to validate (fal, openrouter, openai, replicate, inference, auto)",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Optional brand-config.yaml to source generation.provider and fallback_chain from",
    ),
):
    """Verify brandmint installation is complete for the selected provider path."""
    from ..installer.setup_skills import check_installation
    try:
        check_installation(console=console, provider=provider, config=config)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2)


# ━━━ Report command ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.command()
def report(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, json, html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
):
    """Generate execution report from state file."""
    from .report import run_report
    run_report(config, format=format, output=output)


# ━━━ Cache subcommands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@cache_app.command("stats")
def cache_stats():
    """Show cache statistics."""
    from ..core.cache import get_prompt_cache
    from rich.table import Table
    
    cache = get_prompt_cache()
    stats = cache.stats()
    
    table = Table(title="📦 Prompt Cache Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Entries", str(stats["total_entries"]))
    table.add_row("Valid Entries", f"[green]{stats['valid_entries']}[/green]")
    table.add_row("Expired Entries", f"[yellow]{stats['expired_entries']}[/yellow]")
    table.add_row("Cache Size", f"{stats['total_size_mb']:.2f} MB")
    table.add_row("Location", f"[dim]{stats['cache_dir']}[/dim]")
    
    console.print(table)


@cache_app.command("clear")
def cache_clear(
    expired: bool = typer.Option(False, "--expired", help="Only clear expired entries"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Clear cached prompts."""
    from ..core.cache import get_prompt_cache
    from rich.prompt import Confirm
    
    cache = get_prompt_cache()
    stats = cache.stats()
    
    if expired:
        # Only clear expired
        removed = cache.clear_expired()
        console.print(f"[green]Cleared {removed} expired cache entries.[/green]")
    else:
        # Clear all
        if not force and stats["total_entries"] > 0:
            if not Confirm.ask(f"Clear all {stats['total_entries']} cache entries?"):
                console.print("[dim]Cancelled.[/dim]")
                return
        
        cache.clear_all()
        console.print(f"[green]Cache cleared. Removed {stats['total_entries']} entries.[/green]")


# ━━━ Publish subcommands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@publish_app.command("notebooklm")
def publish_notebooklm(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    artifacts: Optional[str] = typer.Option(None, "--artifacts", "-a", help="Comma-separated artifact IDs (default: all)"),
    force: bool = typer.Option(False, "--force", "-f", help="Recreate notebook from scratch"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing"),
    max_sources: int = typer.Option(50, "--max-sources", "-m", help="Max sources to upload (default: 50, NotebookLM Standard plan limit)"),
    no_synthesize: bool = typer.Option(False, "--no-synthesize", help="Skip LLM prose synthesis, use mechanical rendering"),
    synthesis_model: str = typer.Option("", "--synthesis-model", help="OpenRouter model for prose synthesis (default: claude-3.5-haiku)"),
    clear_prose_cache: bool = typer.Option(False, "--clear-prose-cache", help="Clear cached synthesized prose before building"),
    max_parallel: int = typer.Option(3, "--max-parallel", help="Max parallel artifact workers (default: 3)"),
    include_brand_materials: bool = typer.Option(False, "--include-brand-materials", help="Include logos, style guide, and visual descriptions as sources"),
    vision_descriptions: bool = typer.Option(False, "--vision-descriptions", help="Generate LLM vision descriptions for visual assets (requires OPENROUTER_API_KEY)"),
):
    """Publish brand intelligence to NotebookLM and generate artifacts."""
    from .publish import run_notebooklm_publish
    run_notebooklm_publish(
        config,
        artifacts=artifacts,
        force=force,
        dry_run=dry_run,
        max_sources=max_sources,
        no_synthesize=no_synthesize,
        synthesis_model=synthesis_model,
        clear_prose_cache=clear_prose_cache,
        max_parallel=max_parallel,
        include_brand_materials=include_brand_materials,
        vision_descriptions=vision_descriptions,
    )


def main():
    """Entry point for both `brandmint` and `bm` commands."""
    app()


if __name__ == "__main__":
    main()
