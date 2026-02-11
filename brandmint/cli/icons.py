"""
Brandmint CLI — Standardized status icons and symbols.

Provides consistent visual indicators across all CLI output.
Supports both Unicode symbols and emoji modes.

Usage:
    from brandmint.cli.icons import Icons, get_status_icon

    print(f"{Icons.COMPLETED} Task done")
    print(get_status_icon("in_progress"))
"""

from enum import Enum
from typing import Optional


class StatusType(str, Enum):
    """Standard status types used across brandmint."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"
    CACHED = "cached"


class Icons:
    """Standard icon set for CLI output.
    
    Unicode symbols that render correctly in most terminals.
    Use these for consistent visual language across all commands.
    """
    
    # Status indicators
    PENDING = "○"
    IN_PROGRESS = "◐"
    COMPLETED = "●"
    FAILED = "✗"
    SKIPPED = "◌"
    WAITING = "◔"
    CACHED = "◉"
    
    # Progress indicators
    ARROW_RIGHT = "→"
    ARROW_DOWN = "↓"
    ARROW_UP = "↑"
    CHEVRON = "›"
    BULLET = "•"
    DASH = "─"
    
    # Result indicators
    CHECK = "✓"
    CROSS = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    QUESTION = "?"
    
    # Category indicators
    WAVE = "〜"
    SKILL = "◆"
    ASSET = "◇"
    BATCH = "▣"
    CONFIG = "⚙"
    
    # Box drawing
    BOX_TL = "╭"
    BOX_TR = "╮"
    BOX_BL = "╰"
    BOX_BR = "╯"
    BOX_H = "─"
    BOX_V = "│"
    
    # Decorative
    SPARKLE = "✦"
    STAR = "★"
    DIAMOND = "◆"
    BRAND = "❖"


class EmojiIcons:
    """Emoji icon set for enhanced visual output.
    
    Use when terminal supports emoji rendering.
    """
    
    # Status indicators
    PENDING = "⏳"
    IN_PROGRESS = "🔄"
    COMPLETED = "✅"
    FAILED = "❌"
    SKIPPED = "⏭️"
    WAITING = "⏸️"
    CACHED = "💾"
    
    # Result indicators
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    
    # Category indicators
    WAVE = "🌊"
    SKILL = "🎯"
    ASSET = "🖼️"
    BATCH = "📦"
    CONFIG = "⚙️"
    
    # Decorative
    SPARKLE = "✨"
    STAR = "⭐"
    BRAND = "🎨"
    ROCKET = "🚀"
    MONEY = "💰"
    TIME = "⏱️"
    FILE = "📄"
    FOLDER = "📁"


# ---------------------------------------------------------------------------
# Status icon mapping
# ---------------------------------------------------------------------------

_STATUS_ICON_MAP = {
    StatusType.PENDING: Icons.PENDING,
    StatusType.IN_PROGRESS: Icons.IN_PROGRESS,
    StatusType.COMPLETED: Icons.COMPLETED,
    StatusType.FAILED: Icons.FAILED,
    StatusType.SKIPPED: Icons.SKIPPED,
    StatusType.WAITING: Icons.WAITING,
    StatusType.CACHED: Icons.CACHED,
}

_STATUS_EMOJI_MAP = {
    StatusType.PENDING: EmojiIcons.PENDING,
    StatusType.IN_PROGRESS: EmojiIcons.IN_PROGRESS,
    StatusType.COMPLETED: EmojiIcons.COMPLETED,
    StatusType.FAILED: EmojiIcons.FAILED,
    StatusType.SKIPPED: EmojiIcons.SKIPPED,
    StatusType.WAITING: EmojiIcons.WAITING,
    StatusType.CACHED: EmojiIcons.CACHED,
}

_STATUS_STYLE_MAP = {
    StatusType.PENDING: "dim",
    StatusType.IN_PROGRESS: "yellow",
    StatusType.COMPLETED: "green",
    StatusType.FAILED: "red",
    StatusType.SKIPPED: "dim",
    StatusType.WAITING: "cyan",
    StatusType.CACHED: "blue",
}


def get_status_icon(status: str, emoji: bool = False) -> str:
    """Get the appropriate icon for a status string.
    
    Args:
        status: Status string (e.g., "completed", "in_progress")
        emoji: If True, use emoji icons instead of Unicode symbols
        
    Returns:
        Icon character/emoji for the status
    """
    try:
        status_type = StatusType(status.lower().replace("-", "_"))
    except ValueError:
        return Icons.QUESTION
    
    icon_map = _STATUS_EMOJI_MAP if emoji else _STATUS_ICON_MAP
    return icon_map.get(status_type, Icons.QUESTION)


def get_status_style(status: str) -> str:
    """Get the Rich style for a status string.
    
    Args:
        status: Status string (e.g., "completed", "failed")
        
    Returns:
        Rich style string (e.g., "green", "red")
    """
    try:
        status_type = StatusType(status.lower().replace("-", "_"))
    except ValueError:
        return "white"
    
    return _STATUS_STYLE_MAP.get(status_type, "white")


def format_status(status: str, emoji: bool = False) -> str:
    """Format a status with icon and Rich markup.
    
    Args:
        status: Status string
        emoji: Use emoji icons
        
    Returns:
        Formatted string like "[green]● completed[/green]"
    """
    icon = get_status_icon(status, emoji)
    style = get_status_style(status)
    label = status.replace("_", " ")
    return f"[{style}]{icon} {label}[/{style}]"


def format_status_line(
    item_id: str,
    status: str,
    duration: Optional[float] = None,
    error: Optional[str] = None,
    emoji: bool = False,
) -> str:
    """Format a complete status line for an item.
    
    Args:
        item_id: Identifier for the item
        status: Status string
        duration: Optional duration in seconds
        error: Optional error message
        emoji: Use emoji icons
        
    Returns:
        Formatted status line like "  ● buyer-persona (2.3s)"
    """
    icon = get_status_icon(status, emoji)
    style = get_status_style(status)
    
    parts = [f"  [{style}]{icon}[/{style}] {item_id}"]
    
    if duration is not None:
        parts.append(f" ({duration:.1f}s)")
    
    if error:
        parts.append(f" [red]- {error}[/red]")
    
    return "".join(parts)


# ---------------------------------------------------------------------------
# Progress indicators for inline use
# ---------------------------------------------------------------------------

PROGRESS_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
PROGRESS_BLOCKS = "░▒▓█"
PROGRESS_BAR = "▏▎▍▌▋▊▉█"


def make_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Create a simple text progress bar.
    
    Args:
        current: Current progress value
        total: Total value
        width: Bar width in characters
        
    Returns:
        Progress bar string like "[████████░░░░░░░░░░░░]"
    """
    if total == 0:
        return f"[{'░' * width}]"
    
    filled = int(width * current / total)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}]"
