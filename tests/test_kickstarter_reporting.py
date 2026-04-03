import json
from pathlib import Path

from brandmint.cli.launch import _render_kickstarter_readiness_snapshot
from brandmint.cli.report import ExecutionReport, format_markdown
from brandmint.core.kickstarter_blueprint import build_kickstarter_readiness


def test_markdown_report_includes_kickstarter_readiness_section() -> None:
    readiness = build_kickstarter_readiness({
        "buyer-persona": {"persona": {"name": "Asha"}},
        "competitor-analysis": {"handoff": {"competitors": ["A"]}},
        "campaign-page-copy": {"handoff": {"headline": "Back us"}},
    })
    report = ExecutionReport(
        brand_name="Prototype Brand",
        scenario="launch-ready",
        started_at="2026-03-10T10:00:00",
        kickstarter_readiness=readiness,
    )

    rendered = format_markdown(report)

    assert "## Kickstarter Readiness" in rendered
    assert "Part 1 — Understanding the Market" in rendered
    assert "Part 2 — Product Detailing" in rendered
    assert "landing-page-copy" not in rendered  # alias is represented by section coverage, not repeated in missing list when present


def test_launch_snapshot_renders_for_kickstarter_channel(tmp_path: Path, capsys) -> None:
    outputs_dir = tmp_path / ".brandmint" / "outputs"
    outputs_dir.mkdir(parents=True)
    (outputs_dir / "buyer-persona.json").write_text(json.dumps({"persona": {"name": "Asha"}}))
    (outputs_dir / "competitor-analysis.json").write_text(json.dumps({"handoff": {"competitors": ["A"]}}))

    cfg = {"execution_context": {"launch_channel": "kickstarter"}}
    _render_kickstarter_readiness_snapshot(cfg, tmp_path)

    captured = capsys.readouterr()
    assert "Kickstarter Prototype Readiness" in captured.out
    assert "Part 1 — Understanding the Market" in captured.out
    assert "Mandatory Kickstarter sections:" in captured.out
