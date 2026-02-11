"""
Brandmint CLI — Rich progress indicators and spinners.

Provides visual feedback during long-running operations like API calls,
batch execution, and pipeline stages.

Usage:
    from brandmint.cli.spinners import (
        create_asset_progress,
        create_wave_progress,
        create_api_spinner,
    )

    with create_api_spinner("Generating 2A Bento Grid...") as spinner:
        result = provider.generate(...)
        spinner.update("✓ Generated 2A")
"""

from contextlib import contextmanager
from typing import Optional

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


# ---------------------------------------------------------------------------
# Brand color palette for consistent styling
# ---------------------------------------------------------------------------

BRAND_COLORS = {
    "primary": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "muted": "dim",
    "accent": "#C4873B",  # Solar Bronze
}


# ---------------------------------------------------------------------------
# Progress bar configurations
# ---------------------------------------------------------------------------

def create_asset_progress(console: Optional[Console] = None) -> Progress:
    """Create a progress tracker for visual asset generation.
    
    Shows: spinner, description, progress bar, count, elapsed time.
    
    Example:
        with create_asset_progress() as progress:
            task = progress.add_task("Generating assets...", total=19)
            for asset in assets:
                generate(asset)
                progress.advance(task)
    """
    return Progress(
        SpinnerColumn("dots12", style="cyan"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(bar_width=30, complete_style="green", finished_style="bold green"),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


def create_wave_progress(console: Optional[Console] = None) -> Progress:
    """Create a progress tracker for wave execution.
    
    Shows: wave indicator, description, bar, percentage, time remaining.
    """
    return Progress(
        TextColumn("[bold blue]Wave {task.fields[wave_num]}[/bold blue]"),
        SpinnerColumn("dots", style="blue"),
        TextColumn("{task.description}"),
        BarColumn(bar_width=25, complete_style="cyan"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


def create_batch_progress(console: Optional[Console] = None) -> Progress:
    """Create a progress tracker for batch operations.
    
    Shows: spinner, batch name, bar, count.
    """
    return Progress(
        SpinnerColumn("arc", style="yellow"),
        TextColumn("[yellow]{task.description}[/yellow]"),
        BarColumn(bar_width=20, complete_style="yellow", finished_style="bold green"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def create_skill_progress(console: Optional[Console] = None) -> Progress:
    """Create a progress tracker for text skill execution.
    
    Simpler display for prompt generation / output waiting.
    """
    return Progress(
        SpinnerColumn("dots2", style="magenta"),
        TextColumn("[magenta]{task.description}[/magenta]"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


# ---------------------------------------------------------------------------
# Spinner context managers
# ---------------------------------------------------------------------------

@contextmanager
def create_api_spinner(description: str, console: Optional[Console] = None):
    """Context manager for single API call with spinner feedback.
    
    Usage:
        with create_api_spinner("Calling FAL API...") as status:
            result = api.call()
            status.update("✓ Response received")
    
    Yields a status object with .update(text) method.
    """
    console = console or Console()
    
    class SpinnerStatus:
        def __init__(self, progress: Progress, task_id):
            self._progress = progress
            self._task_id = task_id
        
        def update(self, text: str):
            self._progress.update(self._task_id, description=text)
    
    with Progress(
        SpinnerColumn("dots12", style="cyan"),
        TextColumn("{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(description)
        yield SpinnerStatus(progress, task)


@contextmanager  
def create_pipeline_spinner(stage: str, console: Optional[Console] = None):
    """Context manager for pipeline stage transitions.
    
    Shows a pulsing indicator during stage initialization.
    """
    console = console or Console()
    
    with Progress(
        SpinnerColumn("point", style="bold cyan"),
        TextColumn(f"[bold]{stage}[/bold]"),
        TextColumn("[dim]initializing...[/dim]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("")
        yield progress


# ---------------------------------------------------------------------------
# Live status display
# ---------------------------------------------------------------------------

class LiveStatus:
    """Persistent status display that updates in place.
    
    Usage:
        status = LiveStatus(console)
        status.start("Processing...")
        status.update("Step 1 complete")
        status.update("Step 2 complete")
        status.stop("✓ All done")
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._live: Optional[Live] = None
        self._text = Text()
    
    def start(self, message: str):
        self._text = Text(f"◐ {message}", style="cyan")
        self._live = Live(self._text, console=self.console, refresh_per_second=10)
        self._live.start()
    
    def update(self, message: str):
        if self._live:
            self._text = Text(f"◐ {message}", style="cyan")
            self._live.update(self._text)
    
    def stop(self, message: str, success: bool = True):
        if self._live:
            style = "green" if success else "red"
            icon = "●" if success else "✗"
            self._live.update(Text(f"{icon} {message}", style=style))
            self._live.stop()
            self._live = None


# ---------------------------------------------------------------------------
# Composite progress displays
# ---------------------------------------------------------------------------

def create_multi_progress(console: Optional[Console] = None) -> Progress:
    """Create a multi-task progress display.
    
    Supports tracking multiple concurrent operations.
    """
    return Progress(
        SpinnerColumn("dots", style="cyan"),
        TextColumn("[bold]{task.fields[name]}[/bold]"),
        BarColumn(bar_width=15),
        TaskProgressColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
    )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def format_cost(amount: float) -> str:
    """Format cost with appropriate precision."""
    if amount < 0.01:
        return f"${amount:.4f}"
    elif amount < 1:
        return f"${amount:.3f}"
    else:
        return f"${amount:.2f}"
