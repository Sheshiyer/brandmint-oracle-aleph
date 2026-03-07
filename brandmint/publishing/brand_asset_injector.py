"""
Brand asset injector — extracts brand context from config for instruction templates.

NB-12: Provides ``get_brand_context_for_instructions()`` which returns a dict
of brand-specific values that instruction templates can use to inject brand
colours, typography, logo references, and aesthetic direction into
NotebookLM artifact generation prompts.
"""
from __future__ import annotations

from typing import Dict, List


def get_brand_context_for_instructions(config: dict) -> dict:
    """Extract brand context for instruction template injection.

    Args:
        config: Parsed brand-config.yaml dict.

    Returns:
        Dict with keys: palette_summary, typography_summary, logo_reference,
        brand_colors, aesthetic_direction.
    """
    return {
        "palette_summary": _build_palette_summary(config),
        "typography_summary": _build_typography_summary(config),
        "logo_reference": _build_logo_reference(config),
        "brand_colors": _build_brand_colors(config),
        "aesthetic_direction": _build_aesthetic_direction(config),
    }


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------


def _build_palette_summary(config: dict) -> str:
    """Build a human-readable palette summary."""
    palette = config.get("palette", {})
    if not palette:
        return "(no palette defined)"

    parts: List[str] = []
    for role in ("primary", "secondary", "accent", "support", "signal", "neutral"):
        entry = palette.get(role)
        if entry is None:
            continue
        if isinstance(entry, dict):
            name = entry.get("name", role.title())
            hex_val = entry.get("hex", entry.get("value", ""))
            parts.append(f"{role.title()}: {name} ({hex_val})")
        elif isinstance(entry, str):
            parts.append(f"{role.title()}: {entry}")

    return "; ".join(parts) if parts else "(no palette defined)"


def _build_typography_summary(config: dict) -> str:
    """Build a human-readable typography summary."""
    typo = config.get("typography", {})
    if not typo:
        return "(no typography defined)"

    parts: List[str] = []
    for role in ("header", "heading", "body", "data", "display"):
        entry = typo.get(role)
        if entry is None:
            continue
        if isinstance(entry, dict):
            font = entry.get("font", entry.get("family", role.title()))
            weight = entry.get("weight", "")
            parts.append(f"{role.title()}: {font}" + (f" ({weight})" if weight else ""))
        elif isinstance(entry, str):
            parts.append(f"{role.title()}: {entry}")

    return "; ".join(parts) if parts else "(no typography defined)"


def _build_logo_reference(config: dict) -> str:
    """Build a logo reference string from config."""
    brand = config.get("brand", {})
    brand_name = brand.get("name", "Brand")

    # Check for explicit logo files in config
    logo_files = config.get("logo_files", {})
    if logo_files:
        primary = logo_files.get("primary", "")
        if primary:
            return f"{brand_name} logo (source: {primary})"

    return f"{brand_name} brand logo"


def _build_brand_colors(config: dict) -> Dict[str, str]:
    """Extract hex colour values from config palette."""
    palette = config.get("palette", {})
    colors: Dict[str, str] = {}

    for role, entry in palette.items():
        if isinstance(entry, dict):
            hex_val = entry.get("hex", entry.get("value", ""))
            if hex_val:
                colors[role] = hex_val
        elif isinstance(entry, str) and entry.startswith("#"):
            colors[role] = entry

    return colors


def _build_aesthetic_direction(config: dict) -> str:
    """Build aesthetic direction summary."""
    aesthetic = config.get("aesthetic", {})
    theme = config.get("theme", {})

    parts: List[str] = []

    style = aesthetic.get("style", "")
    if style:
        parts.append(style)

    mood = aesthetic.get("mood", "")
    if mood:
        parts.append(mood)

    metaphor = theme.get("primary_metaphor", "")
    if metaphor:
        parts.append(metaphor)

    visual_lang = theme.get("visual_language", "")
    if visual_lang:
        parts.append(visual_lang)

    return "; ".join(parts) if parts else "(no aesthetic direction defined)"
