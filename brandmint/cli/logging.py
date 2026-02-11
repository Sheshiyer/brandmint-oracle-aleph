"""
Brandmint CLI — Structured logging with Rich integration.

Provides consistent logging across all brandmint modules with
Rich formatting, log levels, and optional file output.

Usage:
    from brandmint.cli.logging import setup_logging, get_logger

    # In CLI entry point
    setup_logging(verbose=args.verbose)
    
    # In any module
    logger = get_logger(__name__)
    logger.info("Processing brand config")
    logger.debug("Detailed debug info")
    logger.warning("Something might be wrong")
    logger.error("Operation failed", exc_info=True)
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.logging import RichHandler
from rich.console import Console
from rich.text import Text


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_configured = False
_log_file: Optional[Path] = None


# ---------------------------------------------------------------------------
# Custom formatter for file output
# ---------------------------------------------------------------------------

class BrandmintFormatter(logging.Formatter):
    """Custom formatter with timestamp, level, and module info."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add custom fields
        record.module_path = f"{record.name}.{record.funcName}"
        return super().format(record)


# ---------------------------------------------------------------------------
# Setup functions
# ---------------------------------------------------------------------------

def setup_logging(
    verbose: bool = False,
    debug: bool = False,
    quiet: bool = False,
    log_file: Optional[str] = None,
    console: Optional[Console] = None,
) -> logging.Logger:
    """Configure logging for the brandmint CLI.
    
    Args:
        verbose: Enable verbose output (INFO level with details)
        debug: Enable debug output (DEBUG level, very detailed)
        quiet: Suppress most output (WARNING level only)
        log_file: Optional path to write logs to file
        console: Optional Rich console instance
        
    Returns:
        Root brandmint logger
        
    Example:
        # In CLI entry point
        @app.callback()
        def main(verbose: bool = False, debug: bool = False):
            setup_logging(verbose=verbose, debug=debug)
    """
    global _configured, _log_file
    
    # Determine log level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    
    # Get root brandmint logger
    root_logger = logging.getLogger("brandmint")
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Rich console handler
    console = console or Console(stderr=True)
    rich_handler = RichHandler(
        console=console,
        show_time=debug,
        show_path=debug,
        rich_tracebacks=True,
        tracebacks_show_locals=debug,
        markup=True,
    )
    rich_handler.setLevel(level)
    
    # Format for Rich handler (minimal, Rich adds its own formatting)
    rich_format = "%(message)s"
    rich_handler.setFormatter(logging.Formatter(rich_format))
    root_logger.addHandler(rich_handler)
    
    # File handler (if requested)
    if log_file:
        _log_file = Path(log_file)
        _log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(_log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always capture everything to file
        
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        file_handler.setFormatter(BrandmintFormatter(file_format))
        root_logger.addHandler(file_handler)
        
        root_logger.debug(f"Logging to file: {_log_file}")
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    _configured = True
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Starting operation")
    """
    # Ensure brandmint prefix for proper hierarchy
    if not name.startswith("brandmint"):
        name = f"brandmint.{name}"
    
    return logging.getLogger(name)


def get_log_file() -> Optional[Path]:
    """Get the current log file path, if any."""
    return _log_file


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def log_section(title: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a section header for visual separation.
    
    Args:
        title: Section title
        logger: Optional logger (uses root brandmint logger if not provided)
    """
    logger = logger or get_logger("brandmint")
    logger.info("")
    logger.info(f"[bold cyan]{'─' * 3} {title} {'─' * (50 - len(title))}[/bold cyan]")


def log_key_value(
    key: str,
    value: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
) -> None:
    """Log a key-value pair with consistent formatting.
    
    Args:
        key: Label/key
        value: Value to display
        logger: Optional logger
        level: Log level
    """
    logger = logger or get_logger("brandmint")
    logger.log(level, f"  [cyan]{key}:[/cyan] {value}")


def log_progress(
    current: int,
    total: int,
    message: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log progress with count.
    
    Args:
        current: Current item number
        total: Total items
        message: Progress message
        logger: Optional logger
    """
    logger = logger or get_logger("brandmint")
    logger.info(f"  [{current}/{total}] {message}")


def log_success(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a success message with green checkmark."""
    logger = logger or get_logger("brandmint")
    logger.info(f"[green]✓[/green] {message}")


def log_failure(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a failure message with red X."""
    logger = logger or get_logger("brandmint")
    logger.error(f"[red]✗[/red] {message}")


def log_warning(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a warning message with yellow icon."""
    logger = logger or get_logger("brandmint")
    logger.warning(f"[yellow]⚠[/yellow] {message}")


# ---------------------------------------------------------------------------
# Context manager for operation logging
# ---------------------------------------------------------------------------

class LoggedOperation:
    """Context manager for logging operation start/end with timing.
    
    Usage:
        with LoggedOperation("Generating assets", logger):
            generate_assets()
        # Logs: "Generating assets... done (2.3s)"
    """
    
    def __init__(
        self,
        operation: str,
        logger: Optional[logging.Logger] = None,
        level: int = logging.INFO,
    ):
        self.operation = operation
        self.logger = logger or get_logger("brandmint")
        self.level = level
        self.start_time: Optional[datetime] = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log(self.level, f"{self.operation}...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.log(
                self.level,
                f"{self.operation}... [green]done[/green] ({duration:.1f}s)"
            )
        else:
            self.logger.error(
                f"{self.operation}... [red]failed[/red] ({duration:.1f}s): {exc_val}"
            )
        
        return False  # Don't suppress exceptions
