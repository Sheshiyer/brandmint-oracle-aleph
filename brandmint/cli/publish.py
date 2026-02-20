"""
Brandmint CLI — Publish subcommands.

Post-pipeline publishing to external platforms and deliverable generation.
Supports NotebookLM, Marp slide decks, Typst reports, diagrams, and videos.
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
) -> None:
    """Publish brand intelligence to NotebookLM."""
    config, cfg, brand_dir = _load_config(config)

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
    )

    if dry_run:
        publisher.dry_run()
        return

    success = publisher.publish()
    if not success:
        raise SystemExit(1)


def run_decks_publish(
    config: Path,
    decks: Optional[str] = None,
    force: bool = False,
) -> None:
    """Generate branded PDF slide decks using Marp CLI.

    Args:
        config: Path to brand-config.yaml.
        decks: Comma-separated deck IDs to generate (default: all).
        force: If True, regenerate all decks.
    """
    config, cfg, brand_dir = _load_config(config)

    deck_filter: Optional[Set[str]] = None
    if decks:
        deck_filter = {d.strip() for d in decks.split(",")}

    from ..publishing.marp_generator import MarpDeckGenerator

    generator = MarpDeckGenerator(
        brand_dir=brand_dir,
        config=cfg,
        config_path=config,
        console=console,
        deck_filter=deck_filter,
        force=force,
    )

    success = generator.generate()
    if not success:
        raise SystemExit(1)


def run_reports_publish(
    config: Path,
    reports: Optional[str] = None,
    force: bool = False,
) -> None:
    """Generate branded PDF reports using Typst.

    Args:
        config: Path to brand-config.yaml.
        reports: Comma-separated report IDs to generate (default: all).
        force: If True, regenerate all reports.
    """
    config, cfg, brand_dir = _load_config(config)

    report_filter: Optional[Set[str]] = None
    if reports:
        report_filter = {r.strip() for r in reports.split(",")}

    from ..publishing.report_generator import TypstReportGenerator

    generator = TypstReportGenerator(
        brand_dir=brand_dir,
        config=cfg,
        config_path=config,
        console=console,
        report_filter=report_filter,
        force=force,
    )

    success = generator.generate()
    if not success:
        raise SystemExit(1)


def run_diagrams_publish(
    config: Path,
    diagrams: Optional[str] = None,
    force: bool = False,
) -> None:
    """Generate mind maps and diagrams using Markmap and Mermaid CLI.

    Args:
        config: Path to brand-config.yaml.
        diagrams: Comma-separated diagram IDs to generate (default: all).
        force: If True, regenerate all diagrams.
    """
    config, cfg, brand_dir = _load_config(config)

    diagram_filter: Optional[Set[str]] = None
    if diagrams:
        diagram_filter = {d.strip() for d in diagrams.split(",")}

    from ..publishing.diagram_generator import DiagramGenerator

    generator = DiagramGenerator(
        brand_dir=brand_dir,
        config=cfg,
        config_path=config,
        console=console,
        diagram_filter=diagram_filter,
        force=force,
    )

    success = generator.generate()
    if not success:
        raise SystemExit(1)


def run_video_publish(
    config: Path,
    videos: Optional[str] = None,
    force: bool = False,
) -> None:
    """Generate branded MP4 videos using Remotion.

    Args:
        config: Path to brand-config.yaml.
        videos: Comma-separated video IDs to generate (default: all).
        force: If True, regenerate all videos.
    """
    config, cfg, brand_dir = _load_config(config)

    video_filter: Optional[Set[str]] = None
    if videos:
        video_filter = {v.strip() for v in videos.split(",")}

    from ..publishing.remotion_generator import RemotionVideoGenerator

    generator = RemotionVideoGenerator(
        brand_dir=brand_dir,
        config=cfg,
        config_path=config,
        console=console,
        video_filter=video_filter,
        force=force,
    )

    success = generator.generate()
    if not success:
        raise SystemExit(1)
