"""
Brandmint CLI — Visual subcommands.
Delegates to existing scripts/run_pipeline.py and scripts/generate_pipeline.py.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()

# Resolve the scripts directory relative to package
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")


def _resolve_scripts_dir():
    """Find the scripts directory (supports both installed and dev modes)."""
    # Dev mode: brandmint/brandmint/cli/ -> brandmint/scripts/
    dev_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
    if os.path.isdir(dev_path):
        return dev_path

    # Installed mode: check relative to package
    pkg_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts"))
    if os.path.isdir(pkg_path):
        return pkg_path

    console.print("[red]ERROR: Cannot find scripts directory[/red]")
    sys.exit(1)


def run_generate(config: Path, output_dir: Optional[str] = None, assets: Optional[str] = None):
    """Generate pipeline scripts from brand config."""
    scripts_dir = _resolve_scripts_dir()
    gen_script = os.path.join(scripts_dir, "generate_pipeline.py")

    if not os.path.exists(gen_script):
        console.print(f"[red]ERROR: generate_pipeline.py not found at {gen_script}[/red]")
        sys.exit(1)

    cmd = [sys.executable, gen_script, str(config)]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if assets:
        cmd.extend(["--assets", assets])

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def run_execute(config: Path, batch: str = "all", output_dir: Optional[str] = None, force: bool = False):
    """Execute generated pipeline scripts."""
    scripts_dir = _resolve_scripts_dir()
    run_script = os.path.join(scripts_dir, "run_pipeline.py")

    cmd = [sys.executable, run_script, "execute", "--config", str(config), "--batch", batch]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if force:
        cmd.append("--force")

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def run_preview(config: Path, assets: Optional[str] = None, json_output: bool = False):
    """Preview budget and smart recommendations."""
    scripts_dir = _resolve_scripts_dir()
    run_script = os.path.join(scripts_dir, "run_pipeline.py")

    cmd = [sys.executable, run_script, "preview", "--config", str(config)]
    if assets:
        cmd.extend(["--assets", assets])
    if json_output:
        cmd.append("--json")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def run_status(config: Path, output_dir: Optional[str] = None):
    """Show asset completion status."""
    scripts_dir = _resolve_scripts_dir()
    run_script = os.path.join(scripts_dir, "run_pipeline.py")

    cmd = [sys.executable, run_script, "status", "--config", str(config)]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def run_verify(config: Path, output_dir: Optional[str] = None):
    """Validate all generated asset files."""
    scripts_dir = _resolve_scripts_dir()
    run_script = os.path.join(scripts_dir, "run_pipeline.py")

    cmd = [sys.executable, run_script, "verify", "--config", str(config)]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)
