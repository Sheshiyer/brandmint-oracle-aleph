#!/usr/bin/env python3
"""
init_brand.py - Interactive CLI to create a brand-config.yaml file.

Usage:
  Interactive:     python3 init_brand.py --output ./brand-config.yaml
  Non-interactive: python3 init_brand.py --preset bioluminescent-architecture --brand-name "My Brand"
"""

import argparse
import os
import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: uv pip install pyyaml")
    sys.exit(1)


# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Theme presets
# ---------------------------------------------------------------------------
THEME_PRESETS = {
    "bioluminescent-architecture": {
        "theme": {
            "name": "Bioluminescent Architecture",
            "description": "Tech-Solarpunk-Art-Nouveau-Art-Deco fusion. Living systems rendered in architectural glass and bronze.",
            "metaphor": "A living building that breathes light through its veins",
            "mood_keywords": [
                "bioluminescent", "architectural", "solarpunk", "art-nouveau",
                "art-deco", "living-systems", "phosphorescent", "organic-geometry",
            ],
        },
        "palette": {
            "primary":   {"name": "Void Teal",       "hex": "#0A1628", "role": "background, anchoring surfaces"},
            "secondary": {"name": "Phosphor Cream",   "hex": "#F0EDE3", "role": "text, light surfaces, contrast"},
            "accent":    {"name": "Solar Bronze",      "hex": "#C4873B", "role": "highlights, CTAs, sigils"},
            "support":   {"name": "Titanium",          "hex": "#8A9BA8", "role": "metadata, secondary text, borders"},
            "signal":    {"name": "Chlorophyll",       "hex": "#4A7C59", "role": "growth indicators, success states"},
        },
        "typography": {
            "header": {"font": "Exo 2",         "weights": ["600", "700", "800"]},
            "body":   {"font": "Space Grotesk",  "weights": ["300", "400", "500"]},
            "data":   {"font": "Fira Code",      "weights": ["400", "500"]},
        },
        "materials": [
            "brushed titanium", "phosphorescent glass", "living moss on concrete",
            "hammered bronze", "translucent mycelium panels", "oxidized copper",
            "volcanic basalt", "luminescent resin", "carbon-fiber mesh",
            "hand-pressed botanical paper", "smoked crystal",
        ],
        "photography": {
            "style": "studio product photography with bioluminescent accents",
            "environment": "dark void background with edge-lit surfaces and volumetric glow",
            "constraint": "No humans. No faces. No text overlays. No stock photo aesthetics.",
            "camera": "Phase One IQ4 150MP, 120mm macro, f/5.6, focus-stacked",
        },
        "illustration": {
            "style": "technical-botanical hybrid illustration with architectural linework",
            "references": "Ernst Haeckel meets Zaha Hadid; Art Nouveau biological forms rendered with engineering precision",
        },
        "negative_prompt": "cartoon, anime, clipart, watermark, text overlay, blurry, low resolution, stock photo, generic, plastic, cheap, oversaturated, neon, grainy, noisy, distorted, ugly, deformed, bad anatomy, extra limbs, poorly drawn, signature, username, error, jpeg artifacts",
    },

    "brutalist-minimalism": {
        "theme": {
            "name": "Brutalist Minimalism",
            "description": "Raw concrete, stark typography, monochrome power. Stripped to structural truth.",
            "metaphor": "A concrete monolith that speaks through silence and shadow",
            "mood_keywords": [
                "brutalist", "minimalist", "monochrome", "raw",
                "stark", "industrial", "structural", "austere",
            ],
        },
        "palette": {
            "primary":   {"name": "Concrete Dark",    "hex": "#1A1A1A", "role": "background, primary surfaces"},
            "secondary": {"name": "Raw White",         "hex": "#F5F5F0", "role": "text, contrast, negative space"},
            "accent":    {"name": "Signal Red",         "hex": "#CC2936", "role": "alerts, CTAs, focal points"},
            "support":   {"name": "Aggregate Grey",     "hex": "#8B8B8B", "role": "secondary text, dividers, metadata"},
            "signal":    {"name": "Rebar Orange",       "hex": "#D4730E", "role": "warnings, highlights, structure"},
        },
        "typography": {
            "header": {"font": "Space Mono",      "weights": ["400", "700"]},
            "body":   {"font": "Inter",            "weights": ["300", "400", "500"]},
            "data":   {"font": "JetBrains Mono",   "weights": ["400", "500"]},
        },
        "materials": [
            "poured concrete", "exposed aggregate", "rusted rebar",
            "raw plywood", "galvanized steel", "matte black rubber",
            "unfinished plaster", "corrugated metal", "industrial glass",
        ],
        "photography": {
            "style": "high-contrast monochrome architectural photography",
            "environment": "raw concrete environments with dramatic directional lighting",
            "constraint": "No humans. No colour unless accent. No decorative elements.",
            "camera": "Hasselblad X2D 100C, 45mm, f/8, natural directional light",
        },
        "illustration": {
            "style": "geometric linework, isometric technical drawings, blueprint aesthetic",
            "references": "Tadao Ando architectural sketches meets Swiss International Style grid systems",
        },
        "negative_prompt": "cartoon, anime, colourful, gradient, glossy, decorative, ornamental, curvy, organic, floral, watermark, text overlay, blurry, low resolution, stock photo, generic, cheap",
    },

    "botanical-victorian": {
        "theme": {
            "name": "Botanical Victorian",
            "description": "Pressed flowers, aged paper, serif elegance. Scientific illustration meets parlour romanticism.",
            "metaphor": "A pressed-flower herbarium bound in gilt-edged leather",
            "mood_keywords": [
                "botanical", "victorian", "aged", "pressed-flower",
                "herbarium", "gilt", "romantic", "scientific-illustration",
            ],
        },
        "palette": {
            "primary":   {"name": "Aged Parchment",   "hex": "#F4E8D1", "role": "background, paper surfaces"},
            "secondary": {"name": "Ink Dark",          "hex": "#2C1810", "role": "text, borders, botanical linework"},
            "accent":    {"name": "Gilt Gold",          "hex": "#B8860B", "role": "highlights, frames, decorative elements"},
            "support":   {"name": "Pressed Sage",       "hex": "#7A8B6E", "role": "botanical fills, secondary elements"},
            "signal":    {"name": "Rose Madder",        "hex": "#9B2335", "role": "accents, chapter markers, focal blooms"},
        },
        "typography": {
            "header": {"font": "Playfair Display", "weights": ["400", "600", "700", "900"]},
            "body":   {"font": "Crimson Pro",       "weights": ["300", "400", "500"]},
            "data":   {"font": "IBM Plex Mono",     "weights": ["400", "500"]},
        },
        "materials": [
            "aged linen paper", "pressed botanical specimens", "gilt-edged pages",
            "wax-sealed envelopes", "embossed leather", "botanical ink",
            "hand-blown glass", "oxidized brass", "dried flower petals",
            "cotton rag paper", "calligraphy nibs",
        ],
        "photography": {
            "style": "flat-lay still life with aged paper textures and botanical specimens",
            "environment": "natural window light on wooden surfaces, aged textile backgrounds",
            "constraint": "No humans. No modern objects. No plastic. Must feel pre-1900.",
            "camera": "Canon R5, 85mm macro, f/4, natural diffused window light",
        },
        "illustration": {
            "style": "detailed scientific botanical illustration with hand-drawn linework and watercolour fills",
            "references": "Pierre-Joseph Redoute meets Maria Sibylla Merian; Kew Gardens archive precision",
        },
        "negative_prompt": "modern, digital, neon, glowing, plastic, cartoon, anime, 3D render, CGI, futuristic, tech, chrome, watermark, text overlay, blurry, low resolution, stock photo",
    },

    "neo-bauhaus-digital": {
        "theme": {
            "name": "Neo-Bauhaus Digital",
            "description": "Primary colours, grid systems, geometric forms. Functional beauty through universal design.",
            "metaphor": "A pixel-perfect grid where every element earns its place through function",
            "mood_keywords": [
                "bauhaus", "geometric", "primary-colors", "grid",
                "functional", "modernist", "constructivist", "systematic",
            ],
        },
        "palette": {
            "primary":   {"name": "Bauhaus Black",    "hex": "#121212", "role": "background, grids, structural elements"},
            "secondary": {"name": "Canvas White",      "hex": "#FAFAFA", "role": "text, negative space, contrast"},
            "accent":    {"name": "Primary Blue",       "hex": "#1A4CFF", "role": "CTAs, interactive elements, links"},
            "support":   {"name": "Primary Yellow",     "hex": "#FFD600", "role": "highlights, alerts, focal points"},
            "signal":    {"name": "Primary Red",        "hex": "#E53935", "role": "errors, urgency, energy accents"},
        },
        "typography": {
            "header": {"font": "DM Sans",       "weights": ["500", "700", "900"]},
            "body":   {"font": "Work Sans",      "weights": ["300", "400", "500"]},
            "data":   {"font": "Source Code Pro", "weights": ["400", "600"]},
        },
        "materials": [
            "matte-painted steel", "tempered glass", "powder-coated aluminium",
            "injection-moulded ABS", "screen-printed canvas", "bent plywood",
            "tubular chrome", "woven textile", "laser-cut acrylic",
        ],
        "photography": {
            "style": "geometric product photography with bold primary-colour backgrounds",
            "environment": "solid-colour seamless backgrounds with hard directional shadows",
            "constraint": "No humans. No gradients. No texture. Pure form and colour.",
            "camera": "Sony A7R V, 90mm macro, f/8, controlled studio strobes",
        },
        "illustration": {
            "style": "flat geometric vector illustration with primary-colour palette and grid alignment",
            "references": "Herbert Bayer meets Josef Mueller-Brockmann; Kandinsky geometric compositions",
        },
        "negative_prompt": "organic, floral, handwritten, watercolour, sketch, vintage, retro, grunge, textured, noisy, photorealistic, 3D, cartoon, anime, watermark, text overlay, blurry, low resolution, stock photo",
    },
}

# Quick-access keys
PRESET_KEYS = list(THEME_PRESETS.keys())

# Default prompt categories (mapping to typical script names)
DEFAULT_PROMPT_CATEGORIES = {
    "brand_identity": [
        "bento-grid-brand-kit",
        "glass-sigil-logo",
        "brand-seal-emblem",
    ],
    "products": [
        "ritual-kit-box",
        "somatic-book",
        "product-lineup",
    ],
    "photography": [
        "hero-product-shot",
        "detail-macro",
        "environment-context",
    ],
    "illustration": [
        "technical-botanical",
        "icon-set",
        "pattern-tile",
    ],
    "narrative": [
        "contact-sheet-sequence",
        "brand-story-panels",
    ],
    "posters": [
        "campaign-poster-a",
        "campaign-poster-b",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def banner(text: str) -> None:
    width = max(len(text) + 6, 50)
    print(f"\n{C.CYAN}{'=' * width}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}   {text}{C.RESET}")
    print(f"{C.CYAN}{'=' * width}{C.RESET}\n")


def section(text: str) -> None:
    print(f"\n{C.BOLD}{C.MAGENTA}--- {text} ---{C.RESET}\n")


def prompt_input(label: str, default: str = "") -> str:
    suffix = f" {C.DIM}[{default}]{C.RESET}" if default else ""
    raw = input(f"  {C.GREEN}>{C.RESET} {label}{suffix}: ").strip()
    return raw if raw else default


def prompt_choice(label: str, options: list, default: int = 0) -> str:
    print(f"  {C.YELLOW}{label}{C.RESET}")
    for i, opt in enumerate(options):
        marker = f"{C.GREEN}*{C.RESET}" if i == default else " "
        print(f"    {marker} [{i + 1}] {opt}")
    raw = input(f"  {C.GREEN}>{C.RESET} Choice [1-{len(options)}]: ").strip()
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except (ValueError, IndexError):
        pass
    return options[default]


def validate_hex(h: str) -> bool:
    return bool(re.match(r"^#[0-9A-Fa-f]{6}$", h))


def prompt_hex(label: str, default: str = "#000000") -> str:
    while True:
        val = prompt_input(label, default)
        if validate_hex(val):
            return val
        print(f"    {C.RED}Invalid hex colour. Use format #RRGGBB{C.RESET}")


def prompt_list(label: str, default: list = None) -> list:
    default = default or []
    default_str = ", ".join(default) if default else ""
    raw = prompt_input(f"{label} (comma-separated)", default_str)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Interactive flow
# ---------------------------------------------------------------------------
def interactive_brand() -> dict:
    banner("Brandmint -- Brand Config Builder")

    # -- Brand identity -------------------------------------------------------
    section("1/9  Brand Identity")
    brand_name = prompt_input("Brand name", "My Brand")
    tagline = prompt_input("Tagline", "")
    archetype = prompt_input("Archetype (e.g. sage, creator, explorer)", "creator")
    voice = prompt_input("Voice (e.g. precise, warm, authoritative)", "precise and warm")
    domain = prompt_input("Domain / industry", "technology")

    # -- Theme ----------------------------------------------------------------
    section("2/9  Theme Selection")
    theme_labels = [
        "Bioluminescent Architecture (Tech-Solarpunk-Art-Nouveau-Art-Deco)",
        "Brutalist Minimalism (Raw concrete, stark typography, monochrome)",
        "Botanical Victorian (Pressed flowers, aged paper, serif elegance)",
        "Neo-Bauhaus Digital (Primary colours, grid systems, geometric forms)",
        "Custom theme (define your own)",
    ]
    chosen_label = prompt_choice("Choose a theme preset:", theme_labels, default=0)
    custom_theme = chosen_label.startswith("Custom")

    if custom_theme:
        preset_key = None
        theme_block = {
            "name": prompt_input("Theme name"),
            "description": prompt_input("Theme description"),
            "metaphor": prompt_input("Theme metaphor (one sentence)"),
            "mood_keywords": prompt_list("Mood keywords"),
        }
    else:
        # Map label back to key
        label_to_key = dict(zip(theme_labels[:4], PRESET_KEYS))
        preset_key = label_to_key[chosen_label]
        preset = THEME_PRESETS[preset_key]
        theme_block = dict(preset["theme"])
        print(f"\n  {C.DIM}Loaded preset: {theme_block['name']}{C.RESET}")

    # -- Palette --------------------------------------------------------------
    section("3/9  Colour Palette")
    if preset_key:
        preset = THEME_PRESETS[preset_key]
        print(f"  {C.DIM}Preset palette loaded. Edit or press Enter to keep defaults.{C.RESET}")
        palette_block = {}
        for role in ("primary", "secondary", "accent", "support", "signal"):
            p = preset["palette"][role]
            print(f"\n  {C.YELLOW}{role.upper()}{C.RESET}  {p['name']}  {p['hex']}  -- {p['role']}")
            edit = prompt_input("Edit this colour? (y/N)", "n").lower()
            if edit == "y":
                palette_block[role] = {
                    "name": prompt_input("  Name", p["name"]),
                    "hex": prompt_hex("  Hex", p["hex"]),
                    "role": prompt_input("  Role", p["role"]),
                }
            else:
                palette_block[role] = dict(p)
    else:
        palette_block = {}
        for role in ("primary", "secondary", "accent", "support", "signal"):
            print(f"\n  {C.YELLOW}{role.upper()} colour{C.RESET}")
            palette_block[role] = {
                "name": prompt_input("  Name"),
                "hex": prompt_hex("  Hex"),
                "role": prompt_input("  Role"),
            }

    # -- Typography -----------------------------------------------------------
    section("4/9  Typography")
    if preset_key:
        typo = THEME_PRESETS[preset_key]["typography"]
        print(f"  {C.DIM}Preset typography loaded.{C.RESET}")
        print(f"    Header: {typo['header']['font']} ({', '.join(typo['header']['weights'])})")
        print(f"    Body:   {typo['body']['font']} ({', '.join(typo['body']['weights'])})")
        print(f"    Data:   {typo['data']['font']} ({', '.join(typo['data']['weights'])})")
        edit = prompt_input("Edit typography? (y/N)", "n").lower()
        if edit == "y":
            typography_block = _ask_typography()
        else:
            typography_block = {k: dict(v) for k, v in typo.items()}
    else:
        typography_block = _ask_typography()

    # -- Materials ------------------------------------------------------------
    section("5/9  Materials Vocabulary")
    if preset_key:
        mats = THEME_PRESETS[preset_key]["materials"]
        print(f"  {C.DIM}Preset materials: {', '.join(mats[:5])} ...{C.RESET}")
        edit = prompt_input("Edit materials list? (y/N)", "n").lower()
        if edit == "y":
            materials_block = prompt_list("Materials", mats)
        else:
            materials_block = list(mats)
    else:
        materials_block = prompt_list("Materials (8-15 descriptors)")

    # -- Photography / Illustration -------------------------------------------
    section("6/9  Photography Direction")
    if preset_key:
        photo = THEME_PRESETS[preset_key]["photography"]
        print(f"  {C.DIM}Preset: {photo['style'][:60]}...{C.RESET}")
        edit = prompt_input("Edit photography? (y/N)", "n").lower()
        if edit == "y":
            photo_block = _ask_photography()
        else:
            photo_block = dict(photo)
    else:
        photo_block = _ask_photography()

    section("7/9  Illustration Direction")
    if preset_key:
        illus = THEME_PRESETS[preset_key]["illustration"]
        print(f"  {C.DIM}Preset: {illus['style'][:60]}...{C.RESET}")
        edit = prompt_input("Edit illustration? (y/N)", "n").lower()
        if edit == "y":
            illus_block = _ask_illustration()
        else:
            illus_block = dict(illus)
    else:
        illus_block = _ask_illustration()

    # -- Negative prompt ------------------------------------------------------
    section("8/9  Negative Prompt")
    if preset_key:
        neg = THEME_PRESETS[preset_key]["negative_prompt"]
        print(f"  {C.DIM}Preset negative prompt loaded ({len(neg)} chars).{C.RESET}")
        edit = prompt_input("Edit negative prompt? (y/N)", "n").lower()
        if edit == "y":
            neg_block = prompt_input("Negative prompt")
        else:
            neg_block = neg
    else:
        neg_block = prompt_input(
            "Negative prompt (things to avoid in generation)",
            "cartoon, anime, clipart, watermark, text overlay, blurry, low resolution, stock photo",
        )

    # -- Generation settings --------------------------------------------------
    section("9/9  Generation Settings")
    output_dir = prompt_input("Output directory", f"./{brand_name.lower().replace(' ', '-')}-assets/generated/")
    seed_str = prompt_input("Seeds (comma-separated integers)", "42, 137")
    seeds = [int(s.strip()) for s in seed_str.split(",") if s.strip().isdigit()]
    resolution = prompt_input("Resolution", "1024x1024")
    output_format = prompt_input("Output format", "png")
    env_file = prompt_input("Env file path", "~/.claude/.env")

    # -- Prompt categories ----------------------------------------------------
    print(f"\n  {C.YELLOW}Prompt categories to enable:{C.RESET}")
    prompts_block = {}
    for cat, items in DEFAULT_PROMPT_CATEGORIES.items():
        print(f"    {cat}: {', '.join(items)}")
    enable_all = prompt_input("Enable all categories? (Y/n)", "y").lower()
    if enable_all != "n":
        prompts_block = {k: list(v) for k, v in DEFAULT_PROMPT_CATEGORIES.items()}
    else:
        for cat, items in DEFAULT_PROMPT_CATEGORIES.items():
            enable = prompt_input(f"Enable {cat}? (Y/n)", "y").lower()
            if enable != "n":
                prompts_block[cat] = list(items)

    # -- Sigil ----------------------------------------------------------------
    sigil_block = {
        "description": f"Abstract geometric mark representing {brand_name}",
        "components": ["geometric-core", "organic-border", "brand-initial"],
    }

    # -- Assemble config ------------------------------------------------------
    config = {
        "brand": {
            "name": brand_name,
            "tagline": tagline,
            "archetype": archetype,
            "voice": voice,
            "domain": domain,
        },
        "theme": theme_block,
        "palette": palette_block,
        "typography": typography_block,
        "materials": materials_block,
        "photography": photo_block,
        "illustration": illus_block,
        "sigil": sigil_block,
        "negative_prompt": neg_block,
        "generation": {
            "output_dir": output_dir,
            "seeds": seeds,
            "resolution": resolution,
            "output_format": output_format,
            "env_file": env_file,
        },
        "prompts": prompts_block,
    }
    return config


def _ask_typography() -> dict:
    result = {}
    for role in ("header", "body", "data"):
        print(f"\n  {C.YELLOW}{role.upper()} font{C.RESET}")
        font = prompt_input("  Font name")
        weights_str = prompt_input("  Weights (comma-separated)", "400, 700")
        weights = [w.strip() for w in weights_str.split(",") if w.strip()]
        result[role] = {"font": font, "weights": weights}
    return result


def _ask_photography() -> dict:
    return {
        "style": prompt_input("Photography style"),
        "environment": prompt_input("Environment / setting"),
        "constraint": prompt_input("Constraints (what to avoid)", "No humans. No faces. No text overlays."),
        "camera": prompt_input("Camera spec (optional)", ""),
    }


def _ask_illustration() -> dict:
    return {
        "style": prompt_input("Illustration style"),
        "references": prompt_input("Artist/style references"),
    }


# ---------------------------------------------------------------------------
# Non-interactive (preset) mode
# ---------------------------------------------------------------------------
def preset_brand(preset_key: str, brand_name: str, tagline: str = "",
                 output_dir: str = "", env_file: str = "~/.claude/.env") -> dict:
    if preset_key not in THEME_PRESETS:
        print(f"{C.RED}ERROR: Unknown preset '{preset_key}'.{C.RESET}")
        print(f"Available: {', '.join(PRESET_KEYS)}")
        sys.exit(1)

    preset = THEME_PRESETS[preset_key]
    slug = brand_name.lower().replace(" ", "-")
    final_output_dir = output_dir if output_dir else f"./{slug}-assets/generated/"

    config = {
        "brand": {
            "name": brand_name,
            "tagline": tagline or f"{brand_name} -- crafted with intention",
            "archetype": "creator",
            "voice": "precise and warm",
            "domain": "technology",
        },
        "theme": dict(preset["theme"]),
        "palette": {k: dict(v) for k, v in preset["palette"].items()},
        "typography": {k: dict(v) for k, v in preset["typography"].items()},
        "materials": list(preset["materials"]),
        "photography": dict(preset["photography"]),
        "illustration": dict(preset["illustration"]),
        "sigil": {
            "description": f"Abstract geometric mark representing {brand_name}",
            "components": ["geometric-core", "organic-border", "brand-initial"],
        },
        "negative_prompt": preset["negative_prompt"],
        "generation": {
            "output_dir": final_output_dir,
            "seeds": [42, 137],
            "resolution": "1024x1024",
            "output_format": "png",
            "env_file": env_file,
        },
        "prompts": {k: list(v) for k, v in DEFAULT_PROMPT_CATEGORIES.items()},
    }
    return config


# ---------------------------------------------------------------------------
# Write YAML
# ---------------------------------------------------------------------------
def write_config(config: dict, output_path: str) -> None:
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"\n{C.GREEN}Brand config written to: {out}{C.RESET}")
    print(f"{C.DIM}  Sections: {', '.join(config.keys())}{C.RESET}")
    palette = config.get("palette", {})
    for role, col in palette.items():
        print(f"  {role:>10}: {col.get('hex', '???')}  {col.get('name', '')}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="init_brand",
        description="Create a brand-config.yaml for the Brandmint pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive:
    python3 init_brand.py --output ./my-brand/brand-config.yaml

  Non-interactive (preset):
    python3 init_brand.py --preset bioluminescent-architecture --brand-name "Tryambakam Noesis"

  Quick with custom output dir:
    python3 init_brand.py --preset brutalist-minimalism --brand-name "Stark Co" \\
      --output ./stark/brand-config.yaml

Available presets:
  bioluminescent-architecture   Tech-Solarpunk-Art-Nouveau-Art-Deco
  brutalist-minimalism          Raw concrete, stark typography, monochrome
  botanical-victorian           Pressed flowers, aged paper, serif elegance
  neo-bauhaus-digital           Primary colours, grid systems, geometric forms
""",
    )
    parser.add_argument(
        "--output", "-o",
        default="./brand-config.yaml",
        help="Output path for brand-config.yaml (default: ./brand-config.yaml)",
    )
    parser.add_argument(
        "--preset", "-p",
        choices=PRESET_KEYS,
        default=None,
        help="Use a theme preset (skips interactive mode)",
    )
    parser.add_argument(
        "--brand-name", "-n",
        default=None,
        help="Brand name (required with --preset)",
    )
    parser.add_argument(
        "--tagline", "-t",
        default="",
        help="Brand tagline (optional with --preset)",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Override output directory for generated assets",
    )
    parser.add_argument(
        "--env-file",
        default="~/.claude/.env",
        help="Path to .env file with API keys (default: ~/.claude/.env)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.preset:
        # Non-interactive mode
        if not args.brand_name:
            parser.error("--brand-name is required when using --preset")
        config = preset_brand(
            preset_key=args.preset,
            brand_name=args.brand_name,
            tagline=args.tagline,
            output_dir=args.output_dir,
            env_file=args.env_file,
        )
    else:
        # Interactive mode
        config = interactive_brand()

    write_config(config, args.output)


if __name__ == "__main__":
    main()
