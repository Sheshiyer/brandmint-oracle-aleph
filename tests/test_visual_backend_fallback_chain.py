from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from brandmint.cli.report import ExecutionReport, format_markdown
from brandmint.pipeline.visual_backend import (
    SubprocessVisualExecutionBackend,
    create_visual_backend,
)


class _DummyProvider:
    def __init__(self, provider_name: str) -> None:
        self.name = type("ProviderNameValue", (), {"value": provider_name})()


def test_subprocess_backend_uses_provider_fallback_chain(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    backend = SubprocessVisualExecutionBackend(
        config={
            "generation": {
                "provider": "fal",
                "fallback_order": ["fal", "replicate", "openrouter"],
            }
        }
    )
    monkeypatch.setattr(
        backend._fallback_chain,
        "_get_available_providers",
        lambda require_image_reference=False: [
            _DummyProvider("fal"),
            _DummyProvider("replicate"),
            _DummyProvider("openrouter"),
        ],
    )

    attempted_providers: list[str] = []

    def _fake_run(cmd, capture_output, text, timeout, env):  # type: ignore[no-untyped-def]
        provider = str(env.get("IMAGE_PROVIDER", ""))
        attempted_providers.append(provider)
        returncode = 0 if provider == "replicate" else 2
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=returncode,
            stdout=f"{provider}-stdout",
            stderr="" if returncode == 0 else f"{provider}-failed",
        )

    monkeypatch.setattr("brandmint.pipeline.visual_backend.subprocess.run", _fake_run)

    result = backend.run_batch(
        script_path=tmp_path / "run_pipeline.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["3A", "3B"],
        timeout_seconds=120,
    )

    assert result.returncode == 0
    assert attempted_providers == ["fal", "replicate"]
    assert "provider_fallback attempts=2 providers=fal,replicate selected=replicate" in result.stdout

    routing_rows = backend.get_batch_routing_summary("products")
    assert len(routing_rows) == 2
    assert all(row["provider_used"] == "replicate" for row in routing_rows)
    assert all(row["fallback_attempts"] == 2 for row in routing_rows)
    assert all(row["fallback_providers_tried"] == "fal, replicate" for row in routing_rows)


def test_create_visual_backend_rejects_invalid_fallback_order(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="generation\\.fallback_order"):
        create_visual_backend(
            config={"generation": {"fallback_order": ["fal", "bogus-provider"]}},
            brand_dir=tmp_path,
        )


def test_markdown_report_includes_provider_fallback_summary() -> None:
    report = ExecutionReport(
        brand_name="Fallback Test",
        scenario="custom",
        started_at="2026-04-16T00:00:00",
        status="completed",
    )
    report.routing_decisions = [
        {
            "asset_id": "3A",
            "batch": "products",
            "media_skill_id": "",
            "reason": "provider_fallback_chain",
            "confidence": "",
            "provider_used": "replicate",
            "fallback_attempts": 2,
            "fallback_providers_tried": "fal, replicate",
            "fallback_order": "fal, replicate, openrouter, openai",
        }
    ]

    rendered = format_markdown(report)
    assert "## Provider Fallback Summary" in rendered
    assert "| products | replicate | 2 | fal, replicate | fal, replicate, openrouter, openai |" in rendered
