"""
Brand Theme Exporter — generates tool-specific theme configs from brand-config.yaml.

Reads the brand's palette, typography, and voice sections and emits:
- Marp CSS theme (slide decks)
- Typst brand template (PDF reports)
- Markmap options JSON (mind maps)
- Mermaid config JSON (diagrams)

This is the force multiplier: one module unlocks brand consistency
across all rendering tools.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .instruction_templates import _get, _palette_block, _typography_block, _voice_excerpt


# ---------------------------------------------------------------------------
# Palette / typography extraction helpers
# ---------------------------------------------------------------------------

def _extract_colors(config: dict) -> Dict[str, str]:
    """Extract hex colors from brand-config palette section.

    Returns a dict like ``{"primary": "#1A1A2E", "secondary": "#16213E", ...}``.
    """
    palette = config.get("palette", {})
    colors: Dict[str, str] = {}
    for role in ("primary", "secondary", "accent", "support", "signal"):
        entry = palette.get(role, {})
        if isinstance(entry, dict) and entry.get("hex"):
            colors[role] = entry["hex"]
    # Fallbacks
    colors.setdefault("primary", "#1A1A2E")
    colors.setdefault("secondary", "#16213E")
    colors.setdefault("accent", "#E94560")
    return colors


def _extract_fonts(config: dict) -> Dict[str, str]:
    """Extract font family names from brand-config typography section."""
    typo = config.get("typography", {})
    fonts: Dict[str, str] = {}
    for role in ("header", "body", "data"):
        entry = typo.get(role, {})
        if isinstance(entry, dict) and entry.get("font"):
            fonts[role] = entry["font"]
    fonts.setdefault("header", "Inter")
    fonts.setdefault("body", "Inter")
    return fonts


def _extract_brand_info(config: dict) -> Dict[str, str]:
    """Extract brand name, tagline, and voice."""
    return {
        "name": _get(config, "brand", "name", default="Brand"),
        "tagline": _get(config, "brand", "tagline", default=""),
        "voice": _voice_excerpt(config),
    }


# ---------------------------------------------------------------------------
# Marp CSS theme
# ---------------------------------------------------------------------------

def generate_marp_theme(config: dict) -> str:
    """Generate a Marp CSS theme from brand-config.yaml.

    The CSS uses custom properties so slides inherit brand colours
    automatically. Includes Google Fonts import for header/body fonts.
    """
    colors = _extract_colors(config)
    fonts = _extract_fonts(config)

    header_font = fonts.get("header", "Inter")
    body_font = fonts.get("body", "Inter")

    # Google Fonts import (best-effort — works for most web fonts)
    font_families = {header_font, body_font}
    imports = "\n".join(
        f"@import url('https://fonts.googleapis.com/css2?family={f.replace(' ', '+')}:wght@300;400;500;600;700&display=swap');"
        for f in sorted(font_families)
    )

    return f"""\
/* Brandmint auto-generated Marp theme */
/* Brand: {_get(config, "brand", "name", default="Brand")} */

{imports}

:root {{
  --brand-primary: {colors.get("primary", "#1A1A2E")};
  --brand-secondary: {colors.get("secondary", "#16213E")};
  --brand-accent: {colors.get("accent", "#E94560")};
  --brand-support: {colors.get("support", "#7B8794")};
  --brand-signal: {colors.get("signal", "#22C55E")};
  --brand-bg: #ffffff;
  --brand-text: #1a1a2e;
  --font-header: '{header_font}', system-ui, sans-serif;
  --font-body: '{body_font}', system-ui, sans-serif;
}}

/* @theme brand */

section {{
  font-family: var(--font-body);
  color: var(--brand-text);
  background: var(--brand-bg);
  padding: 40px 60px;
}}

section.lead {{
  background: var(--brand-primary);
  color: #ffffff;
  text-align: center;
}}

section.lead h1 {{
  color: #ffffff;
  font-size: 2.4em;
}}

section.lead p {{
  color: rgba(255, 255, 255, 0.85);
}}

h1 {{
  font-family: var(--font-header);
  color: var(--brand-primary);
  font-weight: 700;
  font-size: 2em;
  border-bottom: 3px solid var(--brand-accent);
  padding-bottom: 0.2em;
}}

h2 {{
  font-family: var(--font-header);
  color: var(--brand-secondary);
  font-weight: 600;
  font-size: 1.5em;
}}

h3 {{
  font-family: var(--font-header);
  color: var(--brand-accent);
  font-weight: 600;
}}

strong {{
  color: var(--brand-primary);
}}

a {{
  color: var(--brand-accent);
  text-decoration: none;
}}

blockquote {{
  border-left: 4px solid var(--brand-accent);
  padding-left: 1em;
  color: var(--brand-secondary);
  font-style: italic;
}}

table {{
  width: 100%;
  border-collapse: collapse;
}}

th {{
  background: var(--brand-primary);
  color: #ffffff;
  padding: 8px 12px;
  text-align: left;
}}

td {{
  border-bottom: 1px solid #e5e7eb;
  padding: 8px 12px;
}}

code {{
  background: #f3f4f6;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.9em;
}}

/* Utility classes */
section.accent {{
  background: var(--brand-accent);
  color: #ffffff;
}}

section.dark {{
  background: var(--brand-primary);
  color: #ffffff;
}}

footer {{
  font-size: 0.7em;
  color: var(--brand-support);
}}
"""


# ---------------------------------------------------------------------------
# Typst brand template
# ---------------------------------------------------------------------------

def generate_typst_template(config: dict) -> str:
    """Generate a Typst brand template with colour definitions and typography."""
    colors = _extract_colors(config)
    fonts = _extract_fonts(config)
    brand = _extract_brand_info(config)

    return f"""\
// Brandmint auto-generated Typst brand template
// Brand: {brand["name"]}

// --- Colour definitions ---
#let brand-primary = rgb("{colors.get('primary', '#1A1A2E')}")
#let brand-secondary = rgb("{colors.get('secondary', '#16213E')}")
#let brand-accent = rgb("{colors.get('accent', '#E94560')}")
#let brand-support = rgb("{colors.get('support', '#7B8794')}")
#let brand-signal = rgb("{colors.get('signal', '#22C55E')}")
#let brand-bg = rgb("#ffffff")

// --- Brand metadata ---
#let brand-name = "{brand['name']}"
#let brand-tagline = "{brand['tagline']}"

// --- Page setup ---
#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  header: align(right, text(size: 8pt, fill: brand-support)[{brand['name']}]),
  footer: align(center, text(size: 8pt, fill: brand-support)[
    #counter(page).display("1 / 1", both: true)
  ]),
)

// --- Typography ---
#set text(
  font: "{fonts.get('body', 'Inter')}",
  size: 10pt,
  fill: brand-primary,
)

#show heading.where(level: 1): it => {{
  set text(font: "{fonts.get('header', 'Inter')}", size: 18pt, weight: "bold", fill: brand-primary)
  block(below: 0.8em)[
    #it.body
    #line(length: 100%, stroke: 2pt + brand-accent)
  ]
}}

#show heading.where(level: 2): it => {{
  set text(font: "{fonts.get('header', 'Inter')}", size: 14pt, weight: "semibold", fill: brand-secondary)
  block(above: 1.2em, below: 0.6em, it.body)
}}

#show heading.where(level: 3): it => {{
  set text(font: "{fonts.get('header', 'Inter')}", size: 12pt, weight: "semibold", fill: brand-accent)
  block(above: 1em, below: 0.4em, it.body)
}}

// --- Table styling ---
#set table(
  stroke: 0.5pt + brand-support,
  inset: 8pt,
)

// --- Blockquote styling ---
#show quote: it => {{
  block(
    width: 100%,
    inset: (left: 1em, y: 0.5em),
    stroke: (left: 3pt + brand-accent),
  )[
    #set text(style: "italic", fill: brand-secondary)
    #it.body
  ]
}}
"""


# ---------------------------------------------------------------------------
# Markmap options JSON
# ---------------------------------------------------------------------------

def generate_markmap_options(config: dict) -> dict:
    """Generate Markmap options JSON with brand colours for nodes."""
    colors = _extract_colors(config)
    color_list = [
        colors.get("primary", "#1A1A2E"),
        colors.get("secondary", "#16213E"),
        colors.get("accent", "#E94560"),
        colors.get("support", "#7B8794"),
        colors.get("signal", "#22C55E"),
    ]

    return {
        "colorFreezeLevel": 2,
        "color": color_list,
        "maxWidth": 300,
        "initialExpandLevel": 3,
        "zoom": True,
        "pan": True,
    }


# ---------------------------------------------------------------------------
# Mermaid config JSON
# ---------------------------------------------------------------------------

def generate_remotion_constants(config: dict) -> str:
    """Generate TypeScript constants for a Remotion video project.

    Returns a complete ``constants.ts`` source string with brand COLORS,
    FONTS, VIDEO config, and scene-frame mapping utilities.
    """
    colors = _extract_colors(config)
    fonts = _extract_fonts(config)
    brand = _extract_brand_info(config)

    return f"""\
// Brandmint auto-generated Remotion constants
// Brand: {brand["name"]}

export const COLORS = {{
  primary: '{colors.get("primary", "#1A1A2E")}',
  secondary: '{colors.get("secondary", "#16213E")}',
  accent: '{colors.get("accent", "#E94560")}',
  support: '{colors.get("support", "#7B8794")}',
  signal: '{colors.get("signal", "#22C55E")}',
  bg: '#0a0a0a',
  text: '#ffffff',
  textMuted: 'rgba(255, 255, 255, 0.7)',
}};

export const FONTS = {{
  header: '"{fonts.get("header", "Inter")}", system-ui, sans-serif',
  body: '"{fonts.get("body", "Inter")}", system-ui, sans-serif',
}};

export const VIDEO = {{
  fps: 30,
  width: 1920,
  height: 1080,
}};

export const BRAND = {{
  name: '{brand["name"]}',
  tagline: '{brand["tagline"]}',
}};

export type SceneDef = {{ id: string; seconds: number }};

export const sceneToFrames = (seconds: number) => seconds * VIDEO.fps;

export const buildFrameMap = (scenes: SceneDef[]) =>
  scenes.reduce(
    (acc, scene) => {{
      const duration = sceneToFrames(scene.seconds);
      const start = acc.total;
      acc.total += duration;
      acc.map[scene.id] = {{ start, duration }};
      return acc;
    }},
    {{ total: 0, map: {{}} as Record<string, {{ start: number; duration: number }}> }},
  );
"""


def generate_mermaid_config(config: dict) -> dict:
    """Generate Mermaid theme config JSON with brand palette."""
    colors = _extract_colors(config)

    return {
        "theme": "base",
        "themeVariables": {
            "primaryColor": colors.get("primary", "#1A1A2E"),
            "primaryTextColor": "#ffffff",
            "primaryBorderColor": colors.get("secondary", "#16213E"),
            "lineColor": colors.get("support", "#7B8794"),
            "secondaryColor": colors.get("secondary", "#16213E"),
            "tertiaryColor": colors.get("accent", "#E94560"),
            "fontFamily": _extract_fonts(config).get("body", "Inter"),
            "fontSize": "14px",
            "nodeBorder": colors.get("secondary", "#16213E"),
            "mainBkg": colors.get("primary", "#1A1A2E"),
            "clusterBkg": "#f8f9fa",
            "clusterBorder": colors.get("support", "#7B8794"),
            "titleColor": colors.get("primary", "#1A1A2E"),
            "edgeLabelBackground": "#ffffff",
            "quadrant1Fill": colors.get("primary", "#1A1A2E"),
            "quadrant2Fill": colors.get("secondary", "#16213E"),
            "quadrant3Fill": colors.get("support", "#7B8794"),
            "quadrant4Fill": colors.get("accent", "#E94560"),
            "quadrantPointFill": colors.get("signal", "#22C55E"),
            "quadrantPointTextFill": "#ffffff",
        },
    }


# ---------------------------------------------------------------------------
# Public API — write all theme files to a directory
# ---------------------------------------------------------------------------

class BrandThemeExporter:
    """Reads brand-config.yaml and writes theme configs for all tools.

    Usage::

        exporter = BrandThemeExporter(config, output_dir)
        paths = exporter.export_all()
    """

    def __init__(self, config: dict, output_dir: Path) -> None:
        self.config = config
        self.output_dir = Path(output_dir)

    def export_all(self) -> Dict[str, Path]:
        """Generate and write all theme files. Returns dict of name → path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths: Dict[str, Path] = {}

        # Marp CSS
        css_path = self.output_dir / "brand-theme.css"
        css_path.write_text(generate_marp_theme(self.config))
        paths["marp_css"] = css_path

        # Typst template
        typ_path = self.output_dir / "brand-template.typ"
        typ_path.write_text(generate_typst_template(self.config))
        paths["typst_template"] = typ_path

        # Markmap options
        mm_path = self.output_dir / "markmap-options.json"
        mm_path.write_text(json.dumps(generate_markmap_options(self.config), indent=2))
        paths["markmap_options"] = mm_path

        # Mermaid config
        mmd_path = self.output_dir / "mermaid-config.json"
        mmd_path.write_text(json.dumps(generate_mermaid_config(self.config), indent=2))
        paths["mermaid_config"] = mmd_path

        # Remotion constants
        rem_path = self.output_dir / "remotion-constants.ts"
        rem_path.write_text(generate_remotion_constants(self.config))
        paths["remotion_constants"] = rem_path

        return paths

    def export_marp_css(self) -> Path:
        """Export only the Marp CSS theme."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "brand-theme.css"
        path.write_text(generate_marp_theme(self.config))
        return path

    def export_remotion_constants(self) -> Path:
        """Export Remotion TypeScript constants."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "remotion-constants.ts"
        path.write_text(generate_remotion_constants(self.config))
        return path

    def export_typst_template(self) -> Path:
        """Export only the Typst brand template."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "brand-template.typ"
        path.write_text(generate_typst_template(self.config))
        return path
