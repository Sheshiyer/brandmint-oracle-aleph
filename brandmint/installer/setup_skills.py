"""
Brandmint -- Installation and setup utilities.

Handles skill symlinks, FAL_KEY verification, and brand directory scaffolding.
Consumed by `bm install skills` and `bm install check` CLI commands.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.table import Table

# Package root (brandmint repo directory, three levels up from this file)
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
BRAND_SKILLS_DIR = PACKAGE_ROOT / "skills"
CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"
BRANDMINT_SKILL_DIR = CLAUDE_SKILLS_DIR / "brandmint"
CLAUDE_ENV_PATH = Path.home() / ".claude" / ".env"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def install_skills(console: Optional[Console] = None) -> bool:
    """Install brandmint skill symlink to ~/.claude/skills/brandmint/.

    Steps:
    1. Ensure ~/.claude/skills/ directory exists
    2. Check if brandmint symlink already exists
       - If it points to correct target, skip
       - If it points elsewhere, remove and recreate
    3. Create symlink: ~/.claude/skills/brandmint/ -> PACKAGE_ROOT
    4. Verify SKILL.md is accessible through the symlink

    Returns True if installation succeeded.
    """
    _log(console, "Installing brandmint skills...")
    skill_md = PACKAGE_ROOT / "SKILL.md"
    if not skill_md.exists():
        _log(console, f"[red]SKILL.md not found at {skill_md}[/red]")
        return False

    try:
        CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        _log(console, f"[red]Permission denied creating {CLAUDE_SKILLS_DIR}[/red]")
        return False

    # If symlink already exists, check target
    if BRANDMINT_SKILL_DIR.is_symlink():
        current_target = BRANDMINT_SKILL_DIR.resolve()
        if current_target == PACKAGE_ROOT.resolve():
            _log(console, f"[green]Symlink already correct:[/green] {BRANDMINT_SKILL_DIR} -> {PACKAGE_ROOT}")
            return True
        _log(console, f"Removing stale symlink (pointed to {current_target})")
        BRANDMINT_SKILL_DIR.unlink()
    elif BRANDMINT_SKILL_DIR.exists():
        _log(console, f"[yellow]Removing existing directory at {BRANDMINT_SKILL_DIR}[/yellow]")
        shutil.rmtree(BRANDMINT_SKILL_DIR)

    try:
        BRANDMINT_SKILL_DIR.symlink_to(PACKAGE_ROOT)
    except PermissionError:
        _log(console, f"[red]Permission denied creating symlink at {BRANDMINT_SKILL_DIR}[/red]")
        return False
    except OSError as exc:
        _log(console, f"[red]Failed to create symlink: {exc}[/red]")
        return False

    # Verify SKILL.md is reachable through the symlink
    linked_skill = BRANDMINT_SKILL_DIR / "SKILL.md"
    if linked_skill.exists():
        _log(console, f"[green]Installed:[/green] {BRANDMINT_SKILL_DIR} -> {PACKAGE_ROOT}")
        _log(console, f"[green]SKILL.md verified accessible[/green]")
    else:
        _log(console, "[red]Symlink created but SKILL.md not accessible through it[/red]")
        return False

    # Also install brand-domain skills from skills/ directory
    if BRAND_SKILLS_DIR.exists():
        _log(console, "Installing brand-domain skills...")
        install_brand_skills(console)

    return True


def install_brand_skills(console: Optional[Console] = None) -> Dict[str, str]:
    """Install symlinks for all brand-domain skills in brandmint/skills/.

    Scans BRAND_SKILLS_DIR recursively for directories containing SKILL.md.
    For each skill, creates a symlink in ~/.claude/skills/{skill_name}
    pointing to the skill directory in the brandmint repo.

    Returns dict of {skill_name: status} where status is one of:
        "installed" - new symlink created
        "ok"        - symlink already correct
        "skipped"   - non-symlink directory exists (won't clobber)
        "updated"   - stale symlink replaced
        "error"     - failed to create symlink
    """
    if not BRAND_SKILLS_DIR.exists():
        _log(console, "[yellow]No skills/ directory found in brandmint repo[/yellow]")
        return {}

    results: Dict[str, str] = {}

    # Find all skill directories (contain SKILL.md) under skills/
    for skill_md in BRAND_SKILLS_DIR.rglob("SKILL.md"):
        skill_dir = skill_md.parent
        skill_name = skill_dir.name
        target_link = CLAUDE_SKILLS_DIR / skill_name

        if target_link.is_symlink():
            current_target = target_link.resolve()
            if current_target == skill_dir.resolve():
                results[skill_name] = "ok"
                continue
            # Stale symlink -- update it
            _log(console, f"  Updating stale symlink: {skill_name}")
            target_link.unlink()
            try:
                target_link.symlink_to(skill_dir)
                results[skill_name] = "updated"
            except OSError as exc:
                _log(console, f"  [red]Failed to update {skill_name}: {exc}[/red]")
                results[skill_name] = "error"
        elif target_link.exists():
            # Regular directory exists -- don't clobber user customizations
            _log(console, f"  [yellow]Skipping {skill_name} (non-symlink dir exists)[/yellow]")
            results[skill_name] = "skipped"
        else:
            try:
                target_link.symlink_to(skill_dir)
                results[skill_name] = "installed"
            except OSError as exc:
                _log(console, f"  [red]Failed to install {skill_name}: {exc}[/red]")
                results[skill_name] = "error"

    # Report summary
    installed = sum(1 for s in results.values() if s == "installed")
    ok = sum(1 for s in results.values() if s == "ok")
    updated = sum(1 for s in results.values() if s == "updated")
    skipped = sum(1 for s in results.values() if s == "skipped")
    errors = sum(1 for s in results.values() if s == "error")

    _log(console, f"[green]Brand skills: {installed} installed, {ok} already ok, "
         f"{updated} updated, {skipped} skipped, {errors} errors[/green]")

    return results


def check_installation(console: Optional[Console] = None) -> Dict[str, bool]:
    """Run full installation verification.

    Checks:
    1. brandmint package importable
    2. bm command available in PATH
    3. ~/.claude/skills/brandmint/ exists and has SKILL.md
    4. FAL_KEY is set in environment
    5. Python version >= 3.10
    6. fal-client package importable

    Returns dict of {check_name: pass/fail}.
    Prints a Rich table with status per check if console is provided.
    """
    results: Dict[str, bool] = {}

    # 1. brandmint importable
    try:
        import brandmint  # noqa: F401
        results["brandmint importable"] = True
    except ImportError:
        results["brandmint importable"] = False

    # 2. bm command in PATH
    results["bm in PATH"] = shutil.which("bm") is not None

    # 3. Skills symlink with SKILL.md
    skill_md = BRANDMINT_SKILL_DIR / "SKILL.md"
    results["skills symlink"] = skill_md.exists()

    # 3b. Brand skills symlinked
    if BRAND_SKILLS_DIR.exists():
        expected = sum(1 for _ in BRAND_SKILLS_DIR.rglob("SKILL.md"))
        linked = sum(
            1 for sm in BRAND_SKILLS_DIR.rglob("SKILL.md")
            if (CLAUDE_SKILLS_DIR / sm.parent.name).is_symlink()
        )
        results[f"brand skills ({linked}/{expected})"] = linked == expected

    # 4. FAL_KEY set
    results["FAL_KEY set"] = check_fal_key()

    # 5. Python >= 3.10
    results["Python >= 3.10"] = sys.version_info >= (3, 10)

    # 6. fal-client importable
    try:
        import fal_client  # noqa: F401
        results["fal-client installed"] = True
    except ImportError:
        results["fal-client installed"] = False

    if console is not None:
        _render_check_table(console, results)

    return results


def check_fal_key() -> bool:
    """Check if FAL_KEY is set.

    Tries in order:
    1. os.environ.get("FAL_KEY")
    2. Load from ~/.claude/.env via dotenv
    3. Load from PACKAGE_ROOT/.env

    Returns True if FAL_KEY is found and non-empty.
    """
    if os.environ.get("FAL_KEY"):
        return True

    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    for env_path in (CLAUDE_ENV_PATH, PACKAGE_ROOT / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)
            if os.environ.get("FAL_KEY"):
                return True

    return False


def setup_brand_directory(
    brand_name: str,
    base_dir: Optional[Path] = None,
    console: Optional[Console] = None,
) -> Path:
    """Create a new brand directory with scaffolded structure.

    Creates:
      {base_dir}/brands/{slugified-brand-name}/
        +-- brand-config.yaml   (from template)
        +-- .brandmint/
            +-- prompts/        (for scaffolded skill prompts)
            +-- outputs/        (for skill output JSONs)
            +-- state.json      (execution state, initially empty {})

    Args:
        brand_name: Human-readable brand name (gets slugified for directory).
        base_dir: Override base directory. Defaults to PACKAGE_ROOT.
        console: Optional Rich console for output.

    Returns: Path to the created brand directory.

    Raises:
        FileExistsError: If brand directory already exists.
    """
    root = base_dir or PACKAGE_ROOT
    slug = _slugify(brand_name)
    brand_dir = root / "brands" / slug

    if brand_dir.exists():
        raise FileExistsError(f"Brand directory already exists: {brand_dir}")

    _log(console, f"Creating brand directory: {brand_dir}")

    try:
        brand_dir.mkdir(parents=True)
        (brand_dir / ".brandmint" / "prompts").mkdir(parents=True)
        (brand_dir / ".brandmint" / "outputs").mkdir(parents=True)
        (brand_dir / ".brandmint" / "state.json").write_text("{}\n")
        (brand_dir / "brand-config.yaml").write_text(
            _get_brand_config_template(brand_name, slug)
        )
    except PermissionError:
        _log(console, f"[red]Permission denied creating {brand_dir}[/red]")
        raise

    _log(console, f"[green]Brand scaffolded:[/green] {brand_dir}")
    return brand_dir


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _slugify(name: str) -> str:
    """Convert brand name to directory-safe slug.

    "Tirak Dream Journeys" -> "tirak-dream-journeys"
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)  # strip special chars
    slug = re.sub(r"[\s_]+", "-", slug)   # spaces/underscores to hyphens
    slug = re.sub(r"-+", "-", slug)       # collapse repeated hyphens
    return slug.strip("-")


def _get_brand_config_template(brand_name: str, slug: str) -> str:
    """Return a minimal brand-config.yaml template as a string."""
    return f"""\
# {brand_name} -- Brandmint Config
# Generated by `bm install` scaffolding.

# --- EXECUTION CONTEXT (set by ARC orchestrator) ---
execution_context:
  budget_tier: "lean"          # lean | standard | premium
  launch_channel: "dtc"        # dtc | retail | b2b | marketplace
  maturity_stage: "pre-launch" # pre-launch | launch | growth | mature
  depth_level: "focused"       # focused | comprehensive | exhaustive
  tone: "conversion-focused"   # brand-building | conversion-focused | awareness
  quality_bar: "standard"      # standard | premium

# --- BRAND IDENTITY ---
brand:
  name: "{brand_name}"
  tagline: ""                  # Short memorable phrase
  archetype: ""                # e.g. "The Explorer", "The Creator"
  voice: ""                    # Tone description
  domain: ""                   # Industry / category
  domain_tags: []              # e.g. ["app", "marketplace", "lifestyle"]

# --- VISUAL THEME ---
theme:
  name: ""
  description: ""
  metaphor: ""                 # Sensory metaphor for AI prompts
  mood_keywords: []            # 5-10 evocative keywords

# --- COLOR PALETTE ---
palette:
  primary:
    name: ""
    hex: "#000000"
    role: "60% backgrounds"
  secondary:
    name: ""
    hex: "#FFFFFF"
    role: "30% text and surfaces"
  accent:
    name: ""
    hex: "#FF0000"
    role: "10% CTAs and highlights"

# --- TYPOGRAPHY ---
typography:
  header:
    font: "Inter"
    weights: ["Regular", "Bold"]
  body:
    font: "Inter"
    weights: ["Regular"]

# --- GENERATION ---
generation:
  output_dir: "generated"
  seeds: [42, 137]
  resolution: "2K"
  output_format: "png"
  env_file: "~/.claude/.env"
"""


def _render_check_table(console: Console, results: Dict[str, bool]) -> None:
    """Render installation check results as a Rich table."""
    from .. import __version__

    console.print()
    table = Table(title=f"Brandmint v{__version__} Installation Check", show_lines=False)
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")

    for name, passed in results.items():
        icon = "[green]pass[/green]" if passed else "[red]FAIL[/red]"
        table.add_row(name, icon)

    console.print(table)
    console.print()


def _log(console: Optional[Console], message: str) -> None:
    """Print message if console is provided, otherwise no-op."""
    if console is not None:
        console.print(f"  {message}")
