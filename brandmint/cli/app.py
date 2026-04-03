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
inference_app = typer.Typer(help="Inference visual integration tools", no_args_is_help=True)
registry_app = typer.Typer(help="Unified skill registry management", no_args_is_help=True)
install_app = typer.Typer(help="Installation and setup utilities", no_args_is_help=True)
cache_app = typer.Typer(help="Prompt and asset cache management", no_args_is_help=True)
publish_app = typer.Typer(help="Post-pipeline publishing (NotebookLM)", no_args_is_help=True)
x_app = typer.Typer(help="X/Twitter automation with dry-run safeguards", no_args_is_help=True)

app.add_typer(plan_app, name="plan")
app.add_typer(visual_app, name="visual")
app.add_typer(inference_app, name="inference")
app.add_typer(registry_app, name="registry")
app.add_typer(install_app, name="install")
app.add_typer(cache_app, name="cache")
app.add_typer(publish_app, name="publish")
app.add_typer(x_app, name="x")


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
    inference_only_visual: bool = typer.Option(
        False,
        "--inference-only-visual",
        help="Force inference visual backend for visual batches (text flow unchanged).",
    ),
    inference_rollout_mode: Optional[str] = typer.Option(
        None,
        "--inference-rollout-mode",
        help="Override inference rollout mode: ring0|ring1|ring2",
    ),
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
        inference_only_visual=inference_only_visual,
        inference_rollout_mode=inference_rollout_mode,
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
):
    """Generate pipeline scripts from brand config."""
    from .visual import run_generate
    run_generate(config, output_dir=output_dir, assets=assets)


@visual_app.command("execute")
def visual_execute(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    batch: str = typer.Option("all", "--batch", "-b", help="Batch to run: anchor, identity, products, etc."),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o"),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass cache, regenerate all assets"),
):
    """Execute generated pipeline scripts."""
    from .visual import run_execute
    run_execute(config, batch=batch, output_dir=output_dir, force=force)


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


@visual_app.command("diff")
def visual_diff(
    left: Path = typer.Option(..., "--left", help="Left runbook JSON path"),
    right: Path = typer.Option(..., "--right", help="Right runbook JSON path"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON diff"),
    strict: bool = typer.Option(False, "--strict", help="Exit non-zero if any differences"),
):
    """Diff two inference runbooks (routing, skills, prompt fingerprint)."""
    from .visual import run_diff

    code = run_diff(left=left, right=right, json_output=json_output, strict=strict)
    if code != 0:
        raise typer.Exit(code=code)


@visual_app.command("contract-verify")
def visual_contract_verify(
    runbook: Path = typer.Option(..., "--runbook", help="Runbook JSON path"),
    strict: bool = typer.Option(False, "--strict", help="Exit non-zero if contracts fail"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Validate generated outputs against runbook expected output contract."""
    from .visual import run_contract_verify

    code = run_contract_verify(runbook=runbook, strict=strict, json_output=json_output)
    if code != 0:
        raise typer.Exit(code=code)


# ━━━ Inference subcommands ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@inference_app.command("doctor")
def inference_doctor(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    strict: bool = typer.Option(False, "--strict", help="Exit non-zero if warnings/failures are found"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Run inference backend diagnostics."""
    from .inference import run_doctor

    code = run_doctor(config=config, strict=strict, json_output=json_output)
    if code != 0:
        raise typer.Exit(code=code)


@inference_app.command("route-test")
def inference_route_test(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    batch: str = typer.Option("products", "--batch", "-b", help="Batch name for route preview"),
    assets: str = typer.Option(..., "--assets", "-a", help="Comma-separated asset IDs"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Preview semantic route decisions for specific assets."""
    from .inference import run_route_test

    code = run_route_test(config=config, batch=batch, assets=assets, json_output=json_output)
    if code != 0:
        raise typer.Exit(code=code)


@inference_app.command("rerun-failed")
def inference_rerun_failed(
    config: Path = typer.Option(..., "--config", "-c", help="Path to brand-config.yaml"),
    runbook: Path = typer.Option(..., "--runbook", help="Runbook JSON path"),
    backend: Optional[str] = typer.Option(
        None,
        "--backend",
        help="Override rerun backend: scripts|inference (default uses runbook recommendation)",
    ),
):
    """Rerun failed assets from an inference runbook."""
    from .inference import run_rerun_failed

    code = run_rerun_failed(config=config, runbook=runbook, backend_override=backend)
    if code != 0:
        raise typer.Exit(code=code)


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
def install_check():
    """Verify brandmint installation is complete."""
    from ..installer.setup_skills import check_installation
    check_installation(console=console)


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
    )


# ━━━ X/Twitter automation subcommands ━━━━━━━━━━━━━━━━━━━━━

@x_app.command("preflight")
def x_preflight(
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Run OAuth/scope checks before X automation."""
    from ..automation.x_preflight import run_preflight

    result = run_preflight()
    if json_output:
        console.print_json(data=result.to_dict())
    else:
        for check in result.checks:
            icon = "[green]✓[/green]" if check.passed else "[red]✗[/red]"
            console.print(f"  {icon} {check.name}: {check.message}")
        console.print()
        if result.all_passed:
            console.print("[green]All preflight checks passed.[/green]")
        else:
            console.print(f"[yellow]{result.summary}[/yellow]")
            raise typer.Exit(code=1)


@x_app.command("post")
def x_post(
    text: str = typer.Option(..., "--text", "-t", help="Tweet text"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without posting"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Post a tweet."""
    from ..automation.x_actions import XAction, XActionExecutor, XActionRequest
    from ..automation.x_audit import XAuditLog

    executor = XActionExecutor()
    audit = XAuditLog()
    request = XActionRequest(action=XAction.POST_TWEET, payload={"text": text}, dry_run=dry_run)
    result = executor.execute(request)
    audit.log_action(action=request.action.value, payload=request.payload, dry_run=dry_run, success=result.success, error=result.error, response=result.response)

    if json_output:
        console.print_json(data=result.to_dict())
    elif result.success:
        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] Would post tweet via {result.response.get('app', 'unknown')}")
        else:
            console.print(f"[green]Tweet posted.[/green]")
    else:
        console.print(f"[red]Failed:[/red] {result.error}")
        raise typer.Exit(code=1)


@x_app.command("like")
def x_like(
    tweet_id: str = typer.Option(..., "--tweet-id", help="Tweet ID to like"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without liking"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Like a tweet."""
    from ..automation.x_actions import XAction, XActionExecutor, XActionRequest
    from ..automation.x_audit import XAuditLog

    executor = XActionExecutor()
    audit = XAuditLog()
    request = XActionRequest(action=XAction.POST_LIKE, payload={"tweet_id": tweet_id}, dry_run=dry_run)
    result = executor.execute(request)
    audit.log_action(action=request.action.value, payload=request.payload, dry_run=dry_run, success=result.success, error=result.error)

    if json_output:
        console.print_json(data=result.to_dict())
    elif result.success:
        console.print(f"[yellow]DRY RUN:[/yellow] Would like tweet {tweet_id}" if dry_run else f"[green]Liked tweet {tweet_id}.[/green]")
    else:
        console.print(f"[red]Failed:[/red] {result.error}")
        raise typer.Exit(code=1)


@x_app.command("retweet")
def x_retweet(
    tweet_id: str = typer.Option(..., "--tweet-id", help="Tweet ID to retweet"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without retweeting"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Retweet a tweet."""
    from ..automation.x_actions import XAction, XActionExecutor, XActionRequest
    from ..automation.x_audit import XAuditLog

    executor = XActionExecutor()
    audit = XAuditLog()
    request = XActionRequest(action=XAction.POST_RETWEET, payload={"tweet_id": tweet_id}, dry_run=dry_run)
    result = executor.execute(request)
    audit.log_action(action=request.action.value, payload=request.payload, dry_run=dry_run, success=result.success, error=result.error)

    if json_output:
        console.print_json(data=result.to_dict())
    elif result.success:
        console.print(f"[yellow]DRY RUN:[/yellow] Would retweet {tweet_id}" if dry_run else f"[green]Retweeted {tweet_id}.[/green]")
    else:
        console.print(f"[red]Failed:[/red] {result.error}")
        raise typer.Exit(code=1)


@x_app.command("dm")
def x_dm(
    user: str = typer.Option(..., "--user", "-u", help="X handle to DM"),
    text: str = typer.Option(..., "--text", "-t", help="Message text"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without sending"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Send a direct message."""
    from ..automation.x_actions import XAction, XActionExecutor, XActionRequest
    from ..automation.x_audit import XAuditLog

    executor = XActionExecutor()
    audit = XAuditLog()
    request = XActionRequest(action=XAction.DM_SEND, payload={"user": user, "text": text}, dry_run=dry_run)
    result = executor.execute(request)
    audit.log_action(action=request.action.value, payload=request.payload, dry_run=dry_run, success=result.success, error=result.error)

    if json_output:
        console.print_json(data=result.to_dict())
    elif result.success:
        console.print(f"[yellow]DRY RUN:[/yellow] Would DM @{user}" if dry_run else f"[green]DM sent to @{user}.[/green]")
    else:
        console.print(f"[red]Failed:[/red] {result.error}")
        raise typer.Exit(code=1)


@x_app.command("follow")
def x_follow(
    user: str = typer.Option(..., "--user", "-u", help="X handle to follow"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without following"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Follow a user."""
    from ..automation.x_actions import XAction, XActionExecutor, XActionRequest
    from ..automation.x_audit import XAuditLog

    executor = XActionExecutor()
    audit = XAuditLog()
    request = XActionRequest(action=XAction.USER_FOLLOW, payload={"user": user}, dry_run=dry_run)
    result = executor.execute(request)
    audit.log_action(action=request.action.value, payload=request.payload, dry_run=dry_run, success=result.success, error=result.error)

    if json_output:
        console.print_json(data=result.to_dict())
    elif result.success:
        console.print(f"[yellow]DRY RUN:[/yellow] Would follow @{user}" if dry_run else f"[green]Following @{user}.[/green]")
    else:
        console.print(f"[red]Failed:[/red] {result.error}")
        raise typer.Exit(code=1)


@x_app.command("audit")
def x_audit(
    since: Optional[str] = typer.Option(None, "--since", help="ISO date filter (e.g., 2026-03-20)"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Filter by action type"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max entries to show"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Query X automation audit log."""
    from ..automation.x_audit import XAuditLog

    audit = XAuditLog()
    entries = audit.query(since=since, action=action, limit=limit)

    if json_output:
        console.print_json(data=[e.to_json() for e in entries])
    elif not entries:
        console.print("[dim]No audit entries found.[/dim]")
    else:
        from rich.table import Table
        table = Table(title="X Audit Log", show_header=True, header_style="bold cyan")
        table.add_column("Timestamp", style="dim")
        table.add_column("Action")
        table.add_column("Dry Run")
        table.add_column("Success")
        table.add_column("Operator")
        table.add_column("Error", style="red")

        for entry in entries:
            table.add_row(
                entry.timestamp[:19],
                entry.action,
                "✓" if entry.dry_run else "",
                "[green]✓[/green]" if entry.success else "[red]✗[/red]",
                entry.operator,
                (entry.error or "")[:40],
            )
        console.print(table)


@x_app.command("smoke-test")
def x_smoke_test(
    account: Optional[str] = typer.Option(None, "--account", help="Test account handle"),
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="Run in dry-run mode (default: True)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Run smoke test against a safe test account."""
    from ..automation.x_smoke_test import run_smoke_test

    result = run_smoke_test(safe_account=account, dry_run=dry_run)
    if json_output:
        console.print_json(data=result.to_dict())
    else:
        for step in result.steps:
            icon = "[green]✓[/green]" if step.passed else "[red]✗[/red]"
            msg = step.error or "OK"
            console.print(f"  {icon} {step.name}: {msg}")
        console.print()
        if result.all_passed:
            console.print(f"[green]{result.summary}[/green]")
        else:
            console.print(f"[red]{result.summary}[/red]")
            raise typer.Exit(code=1)


def main():
    """Entry point for both `brandmint` and `bm` commands."""
    app()


if __name__ == "__main__":
    main()
