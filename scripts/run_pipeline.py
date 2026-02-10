#!/usr/bin/env python3
"""
run_pipeline.py — Brandmint CLI orchestrator.
Executes generated pipeline scripts in dependency order.

Agent Compatibility:
  When invoked by an AI agent (Claude Code, Claude Desktop):
  - Use `preview --json` to get budget/recommendations as JSON
  - Use `generate --assets 2A,3A,8A` for selective generation
  - NEVER use `studio` command (requires TTY input)
  - The agent should present recommendations to user via its own UI,
    then call generate with the user's selections.

Usage:
  python3 run_pipeline.py generate --config ./brand-config.yaml [--assets 2A,3A]
  python3 run_pipeline.py execute  --config ./brand-config.yaml --batch anchor
  python3 run_pipeline.py execute  --config ./brand-config.yaml --batch all
  python3 run_pipeline.py status   --config ./brand-config.yaml
  python3 run_pipeline.py verify   --config ./brand-config.yaml
  python3 run_pipeline.py studio   --config ./brand-config.yaml
  python3 run_pipeline.py preview  --config ./brand-config.yaml [--assets 2A,3A] [--json]
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: uv pip install pyyaml")
    sys.exit(1)


# =====================================================================
# GLOBAL CONFIG
# =====================================================================

# Detect if we're in interactive mode (TTY) or headless (piped/agent)
INTERACTIVE = sys.stdin.isatty()


# =====================================================================
# ANSI COLOR CODES (Brand Palette + UI Colors)
# =====================================================================

class C:
    """ANSI color codes mapped to brand palette."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Brand palette
    TEAL = "\033[38;2;10;22;40m"        # Void Teal #0A1628
    CREAM = "\033[38;2;240;237;227m"    # Phosphor Cream #F0EDE3
    BRONZE = "\033[38;2;196;135;59m"    # Solar Bronze #C4873B
    TITANIUM = "\033[38;2;138;155;168m" # Titanium #8A9BA8
    GREEN = "\033[38;2;74;124;89m"      # Chlorophyll #4A7C59

    # Standard UI colors
    WHITE = "\033[97m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BG_DARK = "\033[48;2;10;22;40m"


# =====================================================================
# ASSET CATALOG
# =====================================================================

ASSET_CATALOG = {
    "2A": {
        "name": "Brand Identity Bento Grid",
        "category": "brand_identity",
        "model": "nano-banana-pro",
        "cost_per_seed": 0.08,
        "priority": 1,
        "description": "6-module visual system board. THE style anchor — all subsequent assets reference this.",
        "when": "Always generate first. Required foundation.",
        "tags": ["foundation", "required", "hero"],
        "aspect": "16:9",
    },
    "2B": {
        "name": "Brand Seal Emblem",
        "category": "brand_identity",
        "model": "flux-2-pro",
        "cost_per_seed": 0.05,
        "priority": 2,
        "description": "Oxidized copper circular seal with Art Deco geometry. Logo mark.",
        "when": "Core brand identity piece. Essential for any launch.",
        "tags": ["foundation", "logo", "identity"],
        "aspect": "1:1",
    },
    "2C": {
        "name": "Glass Logo Emboss",
        "category": "brand_identity",
        "model": "flux-2-pro",
        "cost_per_seed": 0.05,
        "priority": 3,
        "description": "Stained-glass logo panel with backlit colored shadows.",
        "when": "Premium brand identity. Great for hero sections.",
        "tags": ["identity", "premium"],
        "aspect": "16:9",
    },
    "3A": {
        "name": "Capsule Collection",
        "category": "products",
        "model": "flux-2-pro",
        "cost_per_seed": 0.05,
        "priority": 2,
        "description": "Three-product lineup on polished surface. The hero product shot.",
        "when": "Any brand with physical or conceptual products.",
        "tags": ["product", "hero", "e-commerce"],
        "aspect": "16:9",
    },
    "3B": {
        "name": "Hero Book / Codex",
        "category": "products",
        "model": "flux-2-pro",
        "cost_per_seed": 0.05,
        "priority": 3,
        "description": "Hardcover codex with custom spine and visible diagrams.",
        "when": "Brands with knowledge/education products.",
        "tags": ["product", "knowledge"],
        "aspect": "3:4",
    },
    "3C": {
        "name": "Essence Vial",
        "category": "products",
        "model": "flux-2-pro",
        "cost_per_seed": 0.05,
        "priority": 4,
        "description": "Borosilicate glass vessel with branded elements.",
        "when": "Wellness, beauty, or ceremonial product brands.",
        "tags": ["product", "niche"],
        "aspect": "3:4",
    },
    "4A": {
        "name": "Product Catalog Page",
        "category": "photography",
        "model": "nano-banana-pro",
        "cost_per_seed": 0.08,
        "priority": 3,
        "description": "Split layout: lifestyle shot + technical spec panel with line drawings.",
        "when": "DTC and e-commerce launches. Product-focused brands.",
        "tags": ["photography", "e-commerce", "catalog"],
        "aspect": "3:4",
    },
    "4B": {
        "name": "Product Flatlay",
        "category": "photography",
        "model": "flux-2-pro",
        "cost_per_seed": 0.05,
        "priority": 3,
        "description": "Overhead arrangement of 5 brand objects with architectural spacing.",
        "when": "Instagram, Pinterest, social media hero images.",
        "tags": ["photography", "social", "flatlay"],
        "aspect": "1:1",
    },
    "5A": {
        "name": "Heritage Engraving",
        "category": "illustration",
        "model": "recraft-v3",
        "cost_per_seed": 0.04,
        "priority": 3,
        "description": "Fine-line botanical heritage engraving of brand sigil.",
        "when": "Brands wanting heritage, craft, or artisanal feel.",
        "tags": ["illustration", "heritage", "engraving"],
        "aspect": "1:1",
    },
    "5B": {
        "name": "Campaign Visual Grid",
        "category": "illustration",
        "model": "nano-banana-pro",
        "cost_per_seed": 0.08,
        "priority": 2,
        "description": "2-column asymmetric campaign layout with duotone photos.",
        "when": "Kickstarter and campaign launches. Social media kits.",
        "tags": ["campaign", "social", "grid"],
        "aspect": "3:4",
    },
    "5C": {
        "name": "Art Panel",
        "category": "illustration",
        "model": "recraft-v3",
        "cost_per_seed": 0.04,
        "priority": 4,
        "description": "Conceptual panel illustration with flowing organic curves.",
        "when": "Art-forward brands. Wall art or merch potential.",
        "tags": ["illustration", "art", "decorative"],
        "aspect": "3:4",
    },
    "5D": {
        "name": "Engine Icon Sets",
        "category": "illustration",
        "model": "recraft-v3",
        "cost_per_seed": 0.04,
        "priority": 3,
        "description": "Minimalist vector icon sets grouped by system (from config).",
        "when": "Brands with categorized features, tools, or frameworks.",
        "tags": ["icons", "vector", "system"],
        "aspect": "1:1",
    },
    "7A": {
        "name": "Editorial Contact Sheet",
        "category": "narrative",
        "model": "nano-banana-pro",
        "cost_per_seed": 0.08,
        "priority": 3,
        "description": "3x3 grid of hands-only lifestyle photography showing ritual practice.",
        "when": "Brands with physical practices, rituals, or experiences.",
        "tags": ["photography", "narrative", "lifestyle"],
        "aspect": "1:1",
    },
    "8A": {
        "name": "The Seeker Poster",
        "category": "posters",
        "model": "nano-banana-pro",
        "cost_per_seed": 0.08,
        "priority": 2,
        "description": "Conceptual portrait poster with split reality/inner-architecture composition.",
        "when": "Campaign hero. Kickstarter headers. Brand manifesto visual.",
        "tags": ["poster", "hero", "campaign", "conceptual"],
        "aspect": "3:4",
    },
    "9A": {
        "name": "Engine Campaign Posters",
        "category": "posters",
        "model": "nano-banana-pro",
        "cost_per_seed": 0.08,
        "priority": 3,
        "description": "Individual posters per engine/system with bio-digital artifact objects.",
        "when": "Brands with multiple tools/engines/frameworks to showcase.",
        "tags": ["poster", "campaign", "series"],
        "aspect": "3:4",
    },
    "10A-C": {
        "name": "Ritual Sequence Panels",
        "category": "posters",
        "model": "nano-banana-pro",
        "cost_per_seed": 0.08,
        "priority": 4,
        "description": "9-panel sequential photography showing practice rituals (morning/evening/initiation).",
        "when": "Brands with step-by-step experiences or unboxing journeys.",
        "tags": ["narrative", "sequence", "premium"],
        "aspect": "1:1",
    },
}


# =====================================================================
# PACKS
# =====================================================================

PACKS = {
    "essential": {
        "name": "Essential Pack",
        "description": "Core brand identity. Logo, seal, hero product shot.",
        "assets": ["2A", "2B", "3A"],
        "est_images": 6,
    },
    "launch": {
        "name": "Launch Pack",
        "description": "Everything you need for a Kickstarter or product launch.",
        "assets": ["2A", "2B", "2C", "3A", "3B", "5B", "8A"],
        "est_images": 14,
    },
    "full": {
        "name": "Full Suite",
        "description": "Complete visual identity system — all asset types.",
        "assets": list(ASSET_CATALOG.keys()),
        "est_images": 30,
    },
    "social": {
        "name": "Social Media Kit",
        "description": "Assets optimized for social media presence.",
        "assets": ["2A", "2B", "4B", "5B", "7A"],
        "est_images": 10,
    },
    "premium": {
        "name": "Premium Collection",
        "description": "Full suite plus sequence panels and all icon groups.",
        "assets": list(ASSET_CATALOG.keys()),
        "est_images": 50,
    },
}


# =====================================================================
# BATCH DEFINITIONS
# =====================================================================

BATCHES = {
    "anchor":       ["generate-anchor.py"],
    "identity":     ["generate-identity.py"],
    "products":     ["generate-products.py"],
    "photography":  ["generate-photography.py"],
    "illustration": ["generate-illustrations.py"],
    "narrative":    ["generate-narrative.py"],
    "posters":      ["generate-posters.py"],
}

# Execution order: anchor MUST be first
BATCH_ORDER = ["anchor", "identity", "products", "photography",
               "illustration", "narrative", "posters"]


# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def get_brand_dir(config_path, cfg):
    brand_name = cfg["brand"]["name"]
    return os.path.join(os.path.dirname(os.path.abspath(config_path)),
                        slugify(brand_name))


def get_exec_context(config_path, cfg):
    """Extract execution context from config for recommendation engine."""
    brand = cfg.get("brand", {})
    ec = cfg.get("execution_context", {})
    prompts = cfg.get("prompts", {})
    illus_cfg = prompts.get("illustration", {})
    posters_cfg = prompts.get("posters", {})
    icon_groups = illus_cfg.get("icon_groups", []) if isinstance(illus_cfg, dict) else []
    engines_list = posters_cfg.get("engines", []) if isinstance(posters_cfg, dict) else []
    sequences_list = posters_cfg.get("sequences", []) if isinstance(posters_cfg, dict) else []

    # Depth determines seeds count
    depth_level = ec.get("depth_level", "focused")
    seeds_map = {"surface": 1, "focused": 2, "comprehensive": 2, "exhaustive": 3}
    seeds_count = seeds_map.get(depth_level, 2)

    return {
        "domain": brand.get("domain", "general"),
        "archetype": brand.get("archetype", "general"),
        "launch_channel": ec.get("launch_channel", "dtc"),
        "maturity_stage": ec.get("maturity_stage", "pre-launch"),
        "depth_level": depth_level,
        "seeds_count": seeds_count,
        "has_sigil": bool(cfg.get("sigil", {}).get("description")),
        "has_icon_groups": len(icon_groups) > 0,
        "icon_groups_count": len(icon_groups),
        "has_engines": len(engines_list) > 0,
        "engines_count": len(engines_list),
        "has_sequences": len(sequences_list) > 0,
        "sequences_count": len(sequences_list),
    }


# =====================================================================
# TERMINAL UI HELPERS
# =====================================================================

def box(title, content, width=60):
    """Draw a bordered box with title."""
    lines = content.split("\n")
    top = f"{C.TEAL}╔{'═' * (width-2)}╗{C.RESET}"
    title_line = f"{C.TEAL}║{C.RESET} {C.BOLD}{C.BRONZE}{title}{C.RESET}{' ' * (width-4-len(title))}{C.TEAL}║{C.RESET}"
    sep = f"{C.TEAL}╠{'═' * (width-2)}╣{C.RESET}"
    bottom = f"{C.TEAL}╚{'═' * (width-2)}╝{C.RESET}"

    result = [top, title_line, sep]
    for line in lines:
        padded = line + " " * (width - 4 - len(line))
        result.append(f"{C.TEAL}║{C.RESET} {padded} {C.TEAL}║{C.RESET}")
    result.append(bottom)
    return "\n".join(result)


def table(headers, rows, col_widths=None):
    """Draw a formatted table."""
    if not col_widths:
        col_widths = [max(len(str(row[i])) for row in [headers] + rows) + 2
                      for i in range(len(headers))]

    lines = []
    # Header
    header_line = "  " + "  ".join(f"{C.BOLD}{h:<{col_widths[i]}}{C.RESET}"
                                    for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("  " + "  ".join("-" * w for w in col_widths))

    # Rows
    for row in rows:
        row_line = "  " + "  ".join(f"{str(r):<{col_widths[i]}}"
                                     for i, r in enumerate(row))
        lines.append(row_line)

    return "\n".join(lines)


def progress_bar(current, total, width=40):
    """ASCII progress bar."""
    pct = current / total if total > 0 else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"{C.GREEN}[{bar}]{C.RESET} {current}/{total} ({pct*100:.0f}%)"


def section_header(text):
    """Print a section header with horizontal rule."""
    print()
    print(f"{C.BOLD}{C.BRONZE}{text}{C.RESET}")
    print(f"{C.TITANIUM}{'─' * 60}{C.RESET}")


def brand_banner(cfg):
    """Print the brand identity banner with palette swatches."""
    brand = cfg.get("brand", {})
    palette = cfg.get("visual_identity", {}).get("palette", {})

    name = brand.get("name", "UNKNOWN")
    theme = cfg.get("visual_identity", {}).get("theme", "")
    archetype = brand.get("archetype", "")
    domain = brand.get("domain", "")

    print()
    print(f"{C.BG_DARK}{C.CREAM}{C.BOLD}{'═' * 60}{C.RESET}")
    print(f"{C.BG_DARK}{C.CREAM}{C.BOLD}  {name.upper()}{C.RESET}")
    print(f"{C.BG_DARK}{C.TITANIUM}  {theme}{C.RESET}")
    print(f"{C.BG_DARK}{C.CREAM}{C.BOLD}{'═' * 60}{C.RESET}")
    print()
    print(f"  {C.BOLD}Domain:{C.RESET} {domain}  |  {C.BOLD}Archetype:{C.RESET} {archetype}")

    # Palette swatches
    if palette:
        print(f"\n  {C.BOLD}Palette:{C.RESET}")
        for color_name, hex_val in list(palette.items())[:5]:
            # Simple colored block
            rgb = tuple(int(hex_val.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
            color_code = f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
            print(f"    {color_code}██{C.RESET} {color_name.replace('_', ' ').title():<20} {hex_val}")
    print()


# =====================================================================
# RECOMMENDATION ENGINE
# =====================================================================

def recommend_assets(cfg, exec_ctx):
    """
    Smart recommendation engine that scores assets based on brand profile.
    Returns list of dicts: [{"id": "2A", "name": "...", "reason": "...", "score": 95}, ...]
    """
    recommendations = []

    for asset_id, asset in ASSET_CATALOG.items():
        score = 50  # Base score
        reasons = []

        # Priority boost (higher priority = higher score)
        priority_boost = (5 - asset["priority"]) * 10
        score += priority_boost

        # Foundation assets always recommended
        if "foundation" in asset["tags"]:
            score += 30
            reasons.append("Foundation asset")

        if "required" in asset["tags"]:
            score += 20
            reasons.append("Required for all brands")

        # Launch channel matching
        channel = exec_ctx.get("launch_channel", "dtc")
        if channel == "kickstarter":
            if "campaign" in asset["tags"] or "hero" in asset["tags"]:
                score += 25
                reasons.append("Perfect for Kickstarter launch")
        elif channel == "dtc":
            if "e-commerce" in asset["tags"] or "product" in asset["tags"]:
                score += 20
                reasons.append("Essential for DTC e-commerce")
        elif channel == "saas":
            if "identity" in asset["tags"] or "system" in asset["tags"]:
                score += 20
                reasons.append("Strong for SaaS branding")
        elif channel == "b2b":
            if "identity" in asset["tags"] or "poster" in asset["tags"]:
                score += 15
                reasons.append("Professional B2B presence")

        # Maturity stage
        stage = exec_ctx.get("maturity_stage", "pre-launch")
        if stage == "pre-launch":
            if "hero" in asset["tags"] or "foundation" in asset["tags"]:
                score += 15
                reasons.append("Critical for launch")

        # Depth level filter
        depth = exec_ctx.get("depth_level", "standard")
        if depth == "surface":
            if asset["priority"] > 2:
                score -= 30  # Significantly reduce non-essentials
        elif depth == "exhaustive":
            score += 10  # Boost everything

        # Config-specific boosts
        if exec_ctx.get("has_sigil") and "illustration" in asset["category"]:
            score += 10
            reasons.append("Leverage your sigil design")

        if exec_ctx.get("has_icon_groups") and asset_id == "5D":
            score += 25
            reasons.append("Icon groups configured")

        if exec_ctx.get("has_engines") and asset_id == "9A":
            score += 25
            reasons.append(f"{exec_ctx['engines_count']} engines configured")

        if exec_ctx.get("has_sequences") and asset_id == "10A-C":
            score += 20
            reasons.append(f"{exec_ctx['sequences_count']} sequences configured")

        # Social media optimization
        if "social" in asset["tags"]:
            score += 10
            reasons.append("Social media ready")

        # Build recommendation
        recommendations.append({
            "id": asset_id,
            "name": asset["name"],
            "description": asset["description"],
            "score": min(score, 100),  # Cap at 100
            "reason": ", ".join(reasons) if reasons else asset["when"],
            "category": asset["category"],
            "priority": asset["priority"],
        })

    # Sort by score descending
    recommendations.sort(key=lambda x: (-x["score"], x["priority"]))

    return recommendations


# =====================================================================
# BUDGET CALCULATOR
# =====================================================================

def calculate_budget(asset_ids, cfg, exec_ctx):
    """
    Calculate budget for selected assets.
    Returns dict with breakdown by asset and totals.
    """
    seeds_count = exec_ctx.get("seeds_count", 2)
    breakdown = []
    total_calls = 0
    total_cost = 0.0

    for asset_id in asset_ids:
        if asset_id not in ASSET_CATALOG:
            continue

        asset = ASSET_CATALOG[asset_id]

        # Calculate call count (varies by asset type)
        if asset_id == "9A" and exec_ctx.get("has_engines"):
            calls = exec_ctx["engines_count"]
        elif asset_id == "5D" and exec_ctx.get("has_icon_groups"):
            calls = exec_ctx.get("icon_groups_count", 0)
        elif asset_id == "10A-C" and exec_ctx.get("has_sequences"):
            calls = exec_ctx["sequences_count"]
        else:
            calls = seeds_count

        cost = calls * asset["cost_per_seed"]
        total_calls += calls
        total_cost += cost

        breakdown.append({
            "id": asset_id,
            "name": asset["name"],
            "model": asset["model"],
            "calls": calls,
            "cost": cost,
        })

    # Time estimate (rough: 30s per call)
    time_seconds = total_calls * 30
    time_minutes = time_seconds / 60

    return {
        "breakdown": breakdown,
        "total_calls": total_calls,
        "total_cost": total_cost,
        "time_estimate_minutes": time_minutes,
    }


# =====================================================================
# COMMANDS
# =====================================================================

def cmd_generate(args):
    """Run generate_pipeline.py to create scripts from config."""
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    gen_script = os.path.join(skill_dir, "generate_pipeline.py")

    cmd = [sys.executable, gen_script, args.config]
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    if args.assets:
        cmd.extend(["--assets", args.assets])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def cmd_execute(args):
    """Execute generated pipeline scripts in dependency order."""
    cfg = load_config(args.config)
    brand_dir = args.output_dir or get_brand_dir(args.config, cfg)
    scripts_dir = os.path.join(brand_dir, "scripts")

    if not os.path.isdir(scripts_dir):
        print(f"ERROR: Scripts directory not found: {scripts_dir}")
        print("Run 'run_pipeline.py generate' first.")
        sys.exit(1)

    batch = args.batch or "all"

    if batch == "all":
        batches_to_run = BATCH_ORDER
    elif batch in BATCHES:
        batches_to_run = [batch]
    else:
        print(f"ERROR: Unknown batch '{batch}'")
        print(f"Available: {', '.join(BATCH_ORDER)} or 'all'")
        sys.exit(1)

    # Check anchor dependency
    if batch != "anchor" and batch != "all":
        anchor_output = os.path.join(brand_dir,
                                      cfg["generation"].get("output_dir", "generated"),
                                      "2A-brand-kit-bento-nanobananapro-v1.png")
        if not os.path.exists(anchor_output):
            print("WARNING: Style anchor (2A) not found.")
            print("Run with --batch anchor first for best results.")
            if INTERACTIVE:
                resp = input("Continue anyway? (y/N): ").strip().lower()
                if resp != "y":
                    sys.exit(0)

    print("=" * 60)
    print("BRANDMINT -- Pipeline Execution")
    print("=" * 60)
    print(f"  Brand dir: {brand_dir}")
    print(f"  Batches:   {', '.join(batches_to_run)}")
    print()

    for batch_name in batches_to_run:
        scripts = BATCHES[batch_name]
        for script_name in scripts:
            script_path = os.path.join(scripts_dir, script_name)
            if not os.path.exists(script_path):
                print(f"  SKIP: {script_name} (not found)")
                continue

            print(f"\n{'=' * 60}")
            print(f"  EXECUTING: {script_name}")
            print(f"{'=' * 60}")

            result = subprocess.run(
                [sys.executable, script_path],
                cwd=scripts_dir,
            )
            if result.returncode != 0:
                print(f"\n  ERROR: {script_name} failed (exit code {result.returncode})")
                if batch_name == "anchor":
                    print("  CRITICAL: Anchor failed. Cannot continue.")
                    sys.exit(1)
                else:
                    print("  Continuing with next batch...")

    print(f"\n{'=' * 60}")
    print("  PIPELINE EXECUTION COMPLETE")
    print(f"{'=' * 60}")


def cmd_status(args):
    """Show which assets exist and which are missing."""
    cfg = load_config(args.config)
    brand_dir = args.output_dir or get_brand_dir(args.config, cfg)
    output_subdir = cfg["generation"].get("output_dir", "generated")
    assets_dir = os.path.join(brand_dir, output_subdir)

    print("=" * 60)
    print("BRANDMINT -- Asset Status")
    print("=" * 60)
    print(f"  Assets dir: {assets_dir}")
    print()

    if not os.path.isdir(assets_dir):
        print("  No assets directory found. Run the pipeline first.")
        return

    # Count files by type
    pngs = glob.glob(os.path.join(assets_dir, "*.png"))
    svgs = glob.glob(os.path.join(assets_dir, "*.svg"))
    webps = glob.glob(os.path.join(assets_dir, "*.webp"))

    print(f"  PNG files:  {len(pngs)}")
    print(f"  SVG files:  {len(svgs)}")
    print(f"  WebP files: {len(webps)}")
    print(f"  Total:      {len(pngs) + len(svgs) + len(webps)}")

    # Check expected files by ID prefix
    expected_prefixes = [
        ("2A", "Style Anchor Bento"),
        ("2B", "Brand Seal"),
        ("2C", "Logo Emboss"),
        ("3A", "Capsule Collection"),
        ("3B", "Hero Book"),
        ("3C", "Essence Vial"),
        ("4A", "Catalog Layout"),
        ("4B", "Flatlay"),
        ("5A", "Heritage Engraving"),
        ("5B", "Campaign Grid"),
        ("5C", "Art Panel"),
        ("7A", "Contact Sheet"),
        ("8A", "Seeker Poster"),
    ]

    print(f"\n  {'ID':<6} {'Name':<25} {'Status':<10} {'Files'}")
    print(f"  {'-'*6} {'-'*25} {'-'*10} {'-'*20}")

    all_files = pngs + svgs + webps
    for prefix, name in expected_prefixes:
        matching = [f for f in all_files if os.path.basename(f).startswith(prefix)]
        status = "OK" if matching else "MISSING"
        files_str = ", ".join(os.path.basename(f) for f in matching[:3])
        if len(matching) > 3:
            files_str += f" (+{len(matching)-3} more)"
        print(f"  {prefix:<6} {name:<25} {status:<10} {files_str}")


def cmd_verify(args):
    """Verify all generated files are valid."""
    cfg = load_config(args.config)
    brand_dir = args.output_dir or get_brand_dir(args.config, cfg)
    output_subdir = cfg["generation"].get("output_dir", "generated")
    assets_dir = os.path.join(brand_dir, output_subdir)

    print("=" * 60)
    print("BRANDMINT -- Asset Verification")
    print("=" * 60)
    print(f"  Assets dir: {assets_dir}")
    print()

    if not os.path.isdir(assets_dir):
        print("  ERROR: Assets directory not found.")
        sys.exit(1)

    pngs = glob.glob(os.path.join(assets_dir, "*.png"))
    svgs = glob.glob(os.path.join(assets_dir, "*.svg"))
    webps = glob.glob(os.path.join(assets_dir, "*.webp"))

    errors = 0
    warnings = 0

    # Check PNG magic bytes
    print("Checking PNG files...")
    for png in sorted(pngs):
        fname = os.path.basename(png)
        size_kb = os.path.getsize(png) / 1024

        with open(png, "rb") as f:
            magic = f.read(4)

        if magic != b'\x89PNG':
            print(f"  ERROR: {fname} — invalid PNG header (got {magic.hex()})")
            errors += 1
        elif size_kb < 100:
            print(f"  WARN:  {fname} — suspiciously small ({size_kb:.0f} KB)")
            warnings += 1
        else:
            print(f"  OK:    {fname} ({size_kb:.0f} KB)")

    # Check SVG files
    if svgs:
        print("\nChecking SVG files...")
        for svg in sorted(svgs):
            fname = os.path.basename(svg)
            size_kb = os.path.getsize(svg) / 1024
            with open(svg, "r", errors="ignore") as f:
                head = f.read(100)
            if "<svg" in head or "<?xml" in head:
                print(f"  OK:    {fname} ({size_kb:.0f} KB)")
            else:
                print(f"  ERROR: {fname} — not valid SVG")
                errors += 1

    # Check WebP files
    if webps:
        print("\nChecking WebP files...")
        for webp in sorted(webps):
            fname = os.path.basename(webp)
            size_kb = os.path.getsize(webp) / 1024
            with open(webp, "rb") as f:
                magic = f.read(4)
            if magic == b'RIFF':
                print(f"  OK:    {fname} ({size_kb:.0f} KB)")
            else:
                print(f"  ERROR: {fname} — invalid WebP header")
                errors += 1

    # Summary
    total = len(pngs) + len(svgs) + len(webps)
    print(f"\n{'=' * 60}")
    print(f"  VERIFICATION COMPLETE")
    print(f"  Total files: {total} ({len(pngs)} PNG + {len(svgs)} SVG + {len(webps)} WebP)")
    print(f"  Errors:   {errors}")
    print(f"  Warnings: {warnings}")
    if errors == 0:
        print(f"  Status:   ALL VALID")
    else:
        print(f"  Status:   {errors} ERRORS FOUND")
    print(f"{'=' * 60}")

    sys.exit(1 if errors > 0 else 0)


def cmd_preview(args):
    """Preview budget and recommendations (headless mode for agents)."""
    cfg = load_config(args.config)
    exec_ctx = get_exec_context(args.config, cfg)

    # Get asset list
    if args.assets:
        asset_ids = [a.strip() for a in args.assets.split(",")]
        recommendations = None
    else:
        recommendations = recommend_assets(cfg, exec_ctx)
        asset_ids = [r["id"] for r in recommendations[:10]]  # Top 10

    # Calculate budget
    budget = calculate_budget(asset_ids, cfg, exec_ctx)

    # JSON output for agents
    if args.json:
        output = {
            "brand": cfg["brand"]["name"],
            "context": exec_ctx,
            "recommendations": recommendations[:15] if recommendations else None,
            "selected_assets": asset_ids,
            "budget": budget,
        }
        print(json.dumps(output, indent=2))
        return

    # Terminal output for humans
    brand_banner(cfg)

    if recommendations:
        section_header("Smart Recommendations")
        print(f"  Based on your brand profile ({exec_ctx['launch_channel']} / {exec_ctx['depth_level']})\n")

        for i, rec in enumerate(recommendations[:10], 1):
            score_color = C.GREEN if rec["score"] >= 70 else C.YELLOW if rec["score"] >= 50 else C.GRAY
            print(f"  {score_color}{rec['score']:>3}{C.RESET}  {C.BOLD}{rec['id']:<8}{C.RESET} {rec['name']}")
            print(f"       {C.DIM}{rec['reason']}{C.RESET}")

    section_header("Budget Preview")

    # Budget table
    headers = ["ID", "Name", "Model", "Calls", "Cost"]
    rows = [[b["id"], b["name"][:30], b["model"][:15], str(b["calls"]), f"${b['cost']:.2f}"]
            for b in budget["breakdown"]]
    print(table(headers, rows))

    print()
    print(f"  {C.BOLD}Total API Calls:{C.RESET}  {budget['total_calls']}")
    print(f"  {C.BOLD}Estimated Cost:{C.RESET}   {C.GREEN}${budget['total_cost']:.2f}{C.RESET}")
    print(f"  {C.BOLD}Time Estimate:{C.RESET}   ~{budget['time_estimate_minutes']:.0f} minutes")
    print()


def cmd_studio(args):
    """Interactive studio mode for asset selection and generation."""
    if not INTERACTIVE:
        print("ERROR: Studio mode requires interactive terminal (TTY).")
        print("Use 'preview --json' for headless operation.")
        sys.exit(1)

    cfg = load_config(args.config)
    exec_ctx = get_exec_context(args.config, cfg)

    # 1. Brand Banner
    brand_banner(cfg)

    # 2. Smart Recommendations
    section_header("Smart Recommendations")
    recommendations = recommend_assets(cfg, exec_ctx)

    print(f"  Based on your brand profile:\n")
    for i, rec in enumerate(recommendations[:10], 1):
        score_color = C.GREEN if rec["score"] >= 70 else C.YELLOW if rec["score"] >= 50 else C.GRAY
        print(f"  {i:>2}. {score_color}[{rec['score']:>3}]{C.RESET} {C.BOLD}{rec['id']:<6}{C.RESET} {rec['name']}")
        print(f"      {C.DIM}{rec['reason']}{C.RESET}")

    # 3. Pack Selection
    section_header("Pack Selection")

    pack_options = []
    for i, (pack_id, pack) in enumerate(PACKS.items(), 1):
        budget = calculate_budget(pack["assets"], cfg, exec_ctx)
        pack_options.append((pack_id, pack, budget))
        print(f"  [{i}] {C.BOLD}{pack['name']}{C.RESET} — {len(pack['assets'])} assets, ~${budget['total_cost']:.2f}")
        print(f"      {C.DIM}{pack['description']}{C.RESET}")

    print(f"  [{len(pack_options)+1}] {C.BOLD}Custom{C.RESET} — Pick individual assets")
    print()

    choice = input(f"  Enter choice (1-{len(pack_options)+1}): ").strip()

    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(pack_options):
            # Pack selected
            _, selected_pack, _ = pack_options[choice_num - 1]
            selected_assets = selected_pack["assets"]
            print(f"\n  ✓ Selected: {selected_pack['name']}")
        elif choice_num == len(pack_options) + 1:
            # Custom selection
            section_header("Custom Asset Selection")
            print(f"  Enter asset IDs separated by commas (e.g., 2A,3A,8A)")
            print(f"  Available: {', '.join(ASSET_CATALOG.keys())}")
            print()
            custom_input = input("  Assets: ").strip()
            selected_assets = [a.strip() for a in custom_input.split(",")]

            # Validate
            invalid = [a for a in selected_assets if a not in ASSET_CATALOG]
            if invalid:
                print(f"\n  ERROR: Invalid asset IDs: {', '.join(invalid)}")
                sys.exit(1)
        else:
            print(f"\n  ERROR: Invalid choice.")
            sys.exit(1)
    except ValueError:
        print(f"\n  ERROR: Invalid input.")
        sys.exit(1)

    # 4. Budget Preview
    section_header("Budget Preview")
    budget = calculate_budget(selected_assets, cfg, exec_ctx)

    headers = ["ID", "Name", "Calls", "Cost"]
    rows = [[b["id"], b["name"][:35], str(b["calls"]), f"${b['cost']:.2f}"]
            for b in budget["breakdown"]]
    print(table(headers, rows))

    print()
    print(f"  {C.BOLD}Total API Calls:{C.RESET}  {budget['total_calls']}")
    print(f"  {C.BOLD}Estimated Cost:{C.RESET}   {C.GREEN}${budget['total_cost']:.2f}{C.RESET}")
    print(f"  {C.BOLD}Time Estimate:{C.RESET}   ~{budget['time_estimate_minutes']:.0f} minutes")

    # 5. Confirmation
    print()
    confirm = input(f"  {C.BOLD}Generate these assets? (y/N):{C.RESET} ").strip().lower()

    if confirm != "y":
        print("\n  Cancelled.")
        sys.exit(0)

    # 6. Execute
    section_header("Generating Pipeline")

    # Call generate with asset filter
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    gen_script = os.path.join(skill_dir, "generate_pipeline.py")

    cmd = [sys.executable, gen_script, args.config, "--assets", ",".join(selected_assets)]
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n  ERROR: Pipeline generation failed.")
        sys.exit(1)

    # Now execute
    print(f"\n  Pipeline generated. Executing batches...")

    # Determine which batches to run based on selected assets
    batches_needed = set()
    if "2A" in selected_assets:
        batches_needed.add("anchor")
    if any(a in selected_assets for a in ["2B", "2C"]):
        batches_needed.add("identity")
    if any(a in selected_assets for a in ["3A", "3B", "3C"]):
        batches_needed.add("products")
    if any(a in selected_assets for a in ["4A", "4B"]):
        batches_needed.add("photography")
    if any(a in selected_assets for a in ["5A", "5B", "5C", "5D"]):
        batches_needed.add("illustration")
    if "7A" in selected_assets:
        batches_needed.add("narrative")
    if any(a in selected_assets for a in ["8A", "9A", "10A-C"]):
        batches_needed.add("posters")

    # Execute in order
    brand_dir = get_brand_dir(args.config, cfg)
    scripts_dir = os.path.join(brand_dir, "scripts")

    for batch_name in BATCH_ORDER:
        if batch_name not in batches_needed:
            continue

        scripts = BATCHES[batch_name]
        for script_name in scripts:
            script_path = os.path.join(scripts_dir, script_name)
            if not os.path.exists(script_path):
                continue

            print(f"\n  Executing: {script_name}")
            result = subprocess.run([sys.executable, script_path], cwd=scripts_dir)

            if result.returncode != 0:
                print(f"  WARNING: {script_name} failed")

    section_header("Complete")
    print(f"  Your assets are in: {os.path.join(brand_dir, cfg['generation'].get('output_dir', 'generated'))}")
    print()


# =====================================================================
# CLI
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        prog="run_pipeline",
        description="Brandmint -- Pipeline orchestrator",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # generate
    gen_p = subparsers.add_parser("generate", help="Generate pipeline scripts from config")
    gen_p.add_argument("--config", required=True, help="Path to brand-config.yaml")
    gen_p.add_argument("--output-dir", help="Override output directory")
    gen_p.add_argument("--assets", help="Comma-separated asset IDs to generate (e.g., 2A,3A,8A)")

    # execute
    exe_p = subparsers.add_parser("execute", help="Execute pipeline scripts")
    exe_p.add_argument("--config", required=True, help="Path to brand-config.yaml")
    exe_p.add_argument("--batch", default="all",
                       help=f"Batch to run: {', '.join(BATCH_ORDER)} or 'all'")
    exe_p.add_argument("--output-dir", help="Override output directory")

    # status
    st_p = subparsers.add_parser("status", help="Show asset status")
    st_p.add_argument("--config", required=True, help="Path to brand-config.yaml")
    st_p.add_argument("--output-dir", help="Override output directory")

    # verify
    vr_p = subparsers.add_parser("verify", help="Verify generated assets")
    vr_p.add_argument("--config", required=True, help="Path to brand-config.yaml")
    vr_p.add_argument("--output-dir", help="Override output directory")

    # studio (new)
    stu_p = subparsers.add_parser("studio", help="Interactive studio mode")
    stu_p.add_argument("--config", required=True, help="Path to brand-config.yaml")

    # preview (new)
    prv_p = subparsers.add_parser("preview", help="Preview budget and recommendations")
    prv_p.add_argument("--config", required=True, help="Path to brand-config.yaml")
    prv_p.add_argument("--assets", help="Comma-separated asset IDs to preview (e.g., 2A,3A,8A)")
    prv_p.add_argument("--json", action="store_true", help="Output as JSON (for agents)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "execute":
        cmd_execute(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "studio":
        cmd_studio(args)
    elif args.command == "preview":
        cmd_preview(args)


if __name__ == "__main__":
    main()
