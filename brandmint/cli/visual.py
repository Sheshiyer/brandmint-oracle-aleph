"""
Brandmint CLI — Visual subcommands.
Delegates to existing scripts/run_pipeline.py and scripts/generate_pipeline.py.
"""
import os
import json
import sys
import subprocess
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table

from ..pipeline.inference_runbook import (
    diff_runbooks,
    load_runbook,
    validate_asset_contract,
)

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


def run_diff(left: Path, right: Path, json_output: bool = False, strict: bool = False) -> int:
    """Diff two runbooks and return process-like status code."""
    left_book = load_runbook(left)
    right_book = load_runbook(right)
    diffs = diff_runbooks(left_book, right_book)

    if json_output:
        console.print_json(
            json.dumps(
                {
                    "left": str(left),
                    "right": str(right),
                    "difference_count": len(diffs),
                    "differences": diffs,
                }
            )
        )
    else:
        table = Table(title="Runbook Diff", show_header=True, header_style="bold cyan")
        table.add_column("Asset", style="cyan")
        table.add_column("Change")
        table.add_column("Media Skill (L -> R)")
        table.add_column("Routing (L -> R)")

        for row in diffs:
            if row.get("change") == "missing":
                table.add_row(
                    str(row.get("asset_id", "")),
                    "missing",
                    "-",
                    f"L={row.get('left_present')} R={row.get('right_present')}",
                )
                continue
            table.add_row(
                str(row.get("asset_id", "")),
                str(row.get("change", "")),
                f"{row.get('left_media_skill_id')} -> {row.get('right_media_skill_id')}",
                f"{row.get('left_reason')} ({row.get('left_confidence')})"
                f" -> {row.get('right_reason')} ({row.get('right_confidence')})",
            )
        console.print(table)
        console.print(f"\nDifferences: [bold]{len(diffs)}[/bold]")

    if strict and diffs:
        return 1
    return 0


def run_contract_verify(runbook: Path, strict: bool = False, json_output: bool = False) -> int:
    """Validate output contracts from a runbook."""
    book = load_runbook(runbook)
    rows = validate_asset_contract(book, runbook_path=runbook)
    failed = [r for r in rows if r.get("status") != "ok"]

    if json_output:
        console.print_json(
            json.dumps(
                {
                    "runbook": str(runbook),
                    "asset_count": len(rows),
                    "failed_count": len(failed),
                    "results": rows,
                }
            )
        )
    else:
        table = Table(title="Asset Contract Verification", show_header=True, header_style="bold cyan")
        table.add_column("Asset", style="cyan")
        table.add_column("Batch")
        table.add_column("Status")
        table.add_column("Details")
        for row in rows:
            status = str(row.get("status", "failed"))
            color = "green" if status == "ok" else "red"
            details = (
                f"{len(row.get('matched_files', []))} file(s)"
                if status == "ok"
                else str(row.get("reason", "missing_output"))
            )
            table.add_row(
                str(row.get("asset_id", "")),
                str(row.get("batch", "")),
                f"[{color}]{status}[/{color}]",
                details,
            )
        console.print(table)
        console.print(f"\nFailed: [bold]{len(failed)}[/bold] / {len(rows)}")

    if strict and failed:
        return 1
    return 0
