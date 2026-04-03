"""
Brandmint CLI — Publish subcommands.

Post-pipeline publishing to NotebookLM.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Set

import yaml
from rich.console import Console

console = Console()


def _load_config(config: Path):
    """Load and validate brand-config.yaml. Returns (config_path, cfg, brand_dir)."""
    config = config.resolve()
    if not config.is_file():
        console.print(f"[red]Config not found: {config}[/red]")
        raise SystemExit(1)

    with open(config) as f:
        cfg = yaml.safe_load(f)

    brand_dir = config.parent
    return config, cfg, brand_dir


def run_notebooklm_publish(
    config: Path,
    artifacts: Optional[str] = None,
    force: bool = False,
    dry_run: bool = False,
    max_sources: int = 50,
    no_synthesize: bool = False,
    synthesis_model: str = "",
    clear_prose_cache: bool = False,
    max_parallel: int = 3,
) -> None:
    """Publish brand intelligence to NotebookLM."""
    config, cfg, brand_dir = _load_config(config)

    # Clear prose synthesis cache if requested
    if clear_prose_cache:
        cache_dir = brand_dir / ".brandmint" / "prose-cache"
        from ..publishing.prose_synthesizer import ProseSynthesizer
        count = ProseSynthesizer.clear_cache(cache_dir)
        console.print(
            f"  [green]\u2713[/green] Cleared {count} cached prose file(s)"
            if count > 0
            else "  [dim]Prose cache already empty[/dim]"
        )

    artifact_filter: Optional[Set[str]] = None
    if artifacts:
        artifact_filter = {a.strip() for a in artifacts.split(",")}

    try:
        from ..publishing.notebooklm_publisher import NotebookLMPublisher
    except ImportError:
        console.print(
            "[red]NotebookLM publishing requires notebooklm-py.[/red]\n"
            "Install with: [bold]pip install 'brandmint[publishing]'[/bold]\n"
            "Or: [bold]pip install notebooklm-py[/bold]"
        )
        raise SystemExit(1)

    publisher = NotebookLMPublisher(
        brand_dir=brand_dir,
        config=cfg,
        config_path=config,
        console=console,
        artifact_filter=artifact_filter,
        force=force,
        max_sources=max_sources,
        synthesize=not no_synthesize,
        synthesis_model=synthesis_model,
        max_parallel=max_parallel,
    )

    if dry_run:
        publisher.dry_run()
        return

    success = publisher.publish()
    if not success:
        raise SystemExit(1)
