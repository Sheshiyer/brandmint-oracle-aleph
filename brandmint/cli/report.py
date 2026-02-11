"""
Execution report generator for brandmint.

Generates summaries of pipeline runs including:
- Skills executed (success/failure)
- Costs incurred (estimated vs actual)
- Time taken per wave
- Assets generated
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import yaml

console = Console()


@dataclass
class SkillExecution:
    """Record of a single skill execution."""
    skill_id: str
    wave: int
    status: str  # success, failed, skipped
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None


@dataclass
class AssetExecution:
    """Record of an asset generation."""
    asset_id: str
    batch: str  # anchor, identity, products, photography
    status: str  # success, failed, skipped
    provider: str = ""
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    file_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExecutionReport:
    """Complete execution report."""
    brand_name: str
    scenario: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "in_progress"  # in_progress, completed, failed
    
    # Timing
    total_duration_seconds: float = 0.0
    
    # Costs
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    
    # Executions
    skills: list[SkillExecution] = field(default_factory=list)
    assets: list[AssetExecution] = field(default_factory=list)
    
    # Summaries
    skills_succeeded: int = 0
    skills_failed: int = 0
    skills_skipped: int = 0
    assets_generated: int = 0
    assets_failed: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionReport":
        """Create from dictionary."""
        skills = [SkillExecution(**s) for s in data.pop("skills", [])]
        assets = [AssetExecution(**a) for a in data.pop("assets", [])]
        return cls(**data, skills=skills, assets=assets)


def get_state_file(config_path: Path) -> Path:
    """Get state file path for a config."""
    return config_path.parent / ".brandmint-state.yaml"


def load_report(config_path: Path) -> Optional[ExecutionReport]:
    """Load execution report from state file."""
    state_file = get_state_file(config_path)
    if not state_file.exists():
        return None
    
    with open(state_file) as f:
        data = yaml.safe_load(f)
    
    if not data or "report" not in data:
        return None
    
    return ExecutionReport.from_dict(data["report"])


def save_report(config_path: Path, report: ExecutionReport):
    """Save execution report to state file."""
    state_file = get_state_file(config_path)
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file) as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    state["report"] = report.to_dict()
    state["last_updated"] = datetime.now().isoformat()
    
    with open(state_file, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False)


def format_markdown(report: ExecutionReport) -> str:
    """Format report as Markdown."""
    lines = [
        f"# Brandmint Execution Report",
        f"",
        f"**Brand:** {report.brand_name}",
        f"**Scenario:** {report.scenario}",
        f"**Status:** {report.status}",
        f"",
        f"## Timing",
        f"",
        f"- Started: {report.started_at}",
        f"- Completed: {report.completed_at or 'In progress'}",
        f"- Duration: {report.total_duration_seconds:.1f}s",
        f"",
        f"## Costs",
        f"",
        f"| Item | Amount |",
        f"|------|--------|",
        f"| Estimated | ${report.estimated_cost_usd:.2f} |",
        f"| Actual | ${report.actual_cost_usd:.2f} |",
        f"| Variance | ${report.actual_cost_usd - report.estimated_cost_usd:+.2f} |",
        f"",
        f"## Skills Summary",
        f"",
        f"- Succeeded: {report.skills_succeeded}",
        f"- Failed: {report.skills_failed}",
        f"- Skipped: {report.skills_skipped}",
        f"",
    ]
    
    if report.skills:
        lines.extend([
            f"### Skill Details",
            f"",
            f"| Skill | Wave | Status | Duration |",
            f"|-------|------|--------|----------|",
        ])
        for skill in report.skills:
            lines.append(f"| {skill.skill_id} | {skill.wave} | {skill.status} | {skill.duration_seconds:.1f}s |")
        lines.append("")
    
    if report.assets:
        lines.extend([
            f"## Assets Summary",
            f"",
            f"- Generated: {report.assets_generated}",
            f"- Failed: {report.assets_failed}",
            f"",
            f"### Asset Details",
            f"",
            f"| Asset | Batch | Status | Cost | Provider |",
            f"|-------|-------|--------|------|----------|",
        ])
        for asset in report.assets:
            lines.append(f"| {asset.asset_id} | {asset.batch} | {asset.status} | ${asset.cost_usd:.3f} | {asset.provider} |")
        lines.append("")
    
    lines.extend([
        f"---",
        f"*Generated by Brandmint at {datetime.now().isoformat()}*",
    ])
    
    return "\n".join(lines)


def format_json(report: ExecutionReport) -> str:
    """Format report as JSON."""
    return json.dumps(report.to_dict(), indent=2)


def format_html(report: ExecutionReport) -> str:
    """Format report as HTML."""
    # Simple HTML template
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Brandmint Report - {report.brand_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #6366f1; padding-bottom: 10px; }}
        h2 {{ color: #4f46e5; margin-top: 30px; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: 600; }}
        .status-completed {{ background: #dcfce7; color: #166534; }}
        .status-failed {{ background: #fee2e2; color: #991b1b; }}
        .status-in_progress {{ background: #fef3c7; color: #92400e; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; }}
        .cost-box {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .cost-card {{ background: #f3f4f6; padding: 20px; border-radius: 8px; text-align: center; }}
        .cost-card .value {{ font-size: 24px; font-weight: 700; color: #4f46e5; }}
        .cost-card .label {{ font-size: 14px; color: #6b7280; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>🎨 Brandmint Execution Report</h1>
    
    <p><strong>Brand:</strong> {report.brand_name}</p>
    <p><strong>Scenario:</strong> {report.scenario}</p>
    <p><strong>Status:</strong> <span class="status status-{report.status}">{report.status}</span></p>
    
    <h2>💰 Costs</h2>
    <div class="cost-box">
        <div class="cost-card">
            <div class="value">${report.estimated_cost_usd:.2f}</div>
            <div class="label">Estimated</div>
        </div>
        <div class="cost-card">
            <div class="value">${report.actual_cost_usd:.2f}</div>
            <div class="label">Actual</div>
        </div>
        <div class="cost-card">
            <div class="value">${report.actual_cost_usd - report.estimated_cost_usd:+.2f}</div>
            <div class="label">Variance</div>
        </div>
    </div>
    
    <h2>⏱️ Timing</h2>
    <table>
        <tr><th>Started</th><td>{report.started_at}</td></tr>
        <tr><th>Completed</th><td>{report.completed_at or 'In progress'}</td></tr>
        <tr><th>Duration</th><td>{report.total_duration_seconds:.1f} seconds</td></tr>
    </table>
    
    <h2>📋 Skills Summary</h2>
    <p>Succeeded: {report.skills_succeeded} | Failed: {report.skills_failed} | Skipped: {report.skills_skipped}</p>
    
    {"<table><tr><th>Skill</th><th>Wave</th><th>Status</th><th>Duration</th></tr>" + "".join(f"<tr><td>{s.skill_id}</td><td>{s.wave}</td><td>{s.status}</td><td>{s.duration_seconds:.1f}s</td></tr>" for s in report.skills) + "</table>" if report.skills else ""}
    
    <h2>🖼️ Assets Summary</h2>
    <p>Generated: {report.assets_generated} | Failed: {report.assets_failed}</p>
    
    {"<table><tr><th>Asset</th><th>Batch</th><th>Status</th><th>Cost</th><th>Provider</th></tr>" + "".join(f"<tr><td>{a.asset_id}</td><td>{a.batch}</td><td>{a.status}</td><td>${a.cost_usd:.3f}</td><td>{a.provider}</td></tr>" for a in report.assets) + "</table>" if report.assets else ""}
    
    <hr>
    <p><em>Generated by Brandmint at {datetime.now().isoformat()}</em></p>
</body>
</html>
"""
    return html


def render_report_table(report: ExecutionReport):
    """Render report to console as Rich table."""
    # Header panel
    console.print(Panel(
        f"[bold]{report.brand_name}[/bold] — {report.scenario}\n"
        f"Status: [{'green' if report.status == 'completed' else 'yellow'}]{report.status}[/]",
        title="📊 Execution Report"
    ))
    
    # Costs table
    cost_table = Table(title="💰 Costs", show_header=True, header_style="bold cyan")
    cost_table.add_column("Item")
    cost_table.add_column("Amount", justify="right")
    cost_table.add_row("Estimated", f"${report.estimated_cost_usd:.2f}")
    cost_table.add_row("Actual", f"${report.actual_cost_usd:.2f}")
    variance = report.actual_cost_usd - report.estimated_cost_usd
    color = "green" if variance <= 0 else "red"
    cost_table.add_row("Variance", f"[{color}]${variance:+.2f}[/]")
    console.print(cost_table)
    
    # Skills summary
    console.print(f"\n[bold]📋 Skills:[/] ✓ {report.skills_succeeded}  ✗ {report.skills_failed}  ○ {report.skills_skipped}")
    
    # Assets summary  
    console.print(f"[bold]🖼️ Assets:[/] ✓ {report.assets_generated}  ✗ {report.assets_failed}")
    
    # Timing
    console.print(f"\n[dim]Duration: {report.total_duration_seconds:.1f}s[/]")


def run_report(config_path: Path, format: str = "markdown", output: Optional[Path] = None):
    """Main entry point for report command."""
    if not config_path.exists():
        console.print(f"[red]Config not found:[/] {config_path}")
        raise typer.Exit(1)
    
    report = load_report(config_path)
    
    if report is None:
        console.print("[yellow]No execution data found.[/] Run `bm launch` first.")
        raise typer.Exit(1)
    
    # Format output
    if format == "markdown":
        content = format_markdown(report)
    elif format == "json":
        content = format_json(report)
    elif format == "html":
        content = format_html(report)
    else:
        console.print(f"[red]Unknown format:[/] {format}")
        raise typer.Exit(1)
    
    # Write output
    if output:
        output.write_text(content)
        console.print(f"[green]Report saved to:[/] {output}")
    else:
        # For non-JSON, render rich table to console
        if format != "json":
            render_report_table(report)
        else:
            console.print(content)


# Export for use by executor
__all__ = [
    "ExecutionReport",
    "SkillExecution", 
    "AssetExecution",
    "load_report",
    "save_report",
    "run_report",
]
