from __future__ import annotations

from pathlib import Path

from brandmint.pipeline.inference_runbook import (
    collect_failed_assets,
    diff_runbooks,
    prompt_fingerprint,
    validate_asset_contract,
)


def _asset(
    asset_id: str,
    *,
    media_skill: str = "infsh-ai-image-generation",
    reason: str = "default_image_generation",
    confidence: float = 0.7,
    prompt: str = "Render asset",
    status: str = "validated",
) -> dict:
    return {
        "asset_id": asset_id,
        "batch_type": "products",
        "status": status,
        "skills": {"media_skill_id": media_skill},
        "routing": {"reason": reason, "confidence": confidence},
        "media_input": {"prompt": prompt},
        "agent_prompt": "Agent prompt",
        "prompt_lineage": {"final_skills": {"media_skill_id": media_skill}},
        "expected_outputs": {"output_dir": "generated", "file_glob": f"{asset_id}-*.png"},
        "validation_errors": [],
    }


def test_prompt_fingerprint_changes_on_prompt_update() -> None:
    a = _asset("3A", prompt="Render A")
    b = _asset("3A", prompt="Render B")
    assert prompt_fingerprint(a) != prompt_fingerprint(b)


def test_diff_runbooks_detects_skill_and_routing_changes() -> None:
    left = {"assets": [_asset("3A")]}
    right = {
        "assets": [
            _asset(
                "3A",
                media_skill="infsh-agentic-browser",
                reason="keyword_match",
                confidence=0.9,
            )
        ]
    }
    diffs = diff_runbooks(left, right)
    assert len(diffs) == 1
    assert diffs[0]["asset_id"] == "3A"
    assert diffs[0]["left_media_skill_id"] == "infsh-ai-image-generation"
    assert diffs[0]["right_media_skill_id"] == "infsh-agentic-browser"


def test_validate_asset_contract_reports_missing_and_present(tmp_path: Path) -> None:
    runbook_path = tmp_path / "runbook.json"
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    (generated_dir / "3A-v1.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    runbook = {
        "assets": [
            {
                **_asset("3A"),
                "expected_outputs": {"output_dir": str(generated_dir), "file_glob": "3A-*.png"},
            },
            {
                **_asset("3B"),
                "expected_outputs": {"output_dir": str(generated_dir), "file_glob": "3B-*.png"},
            },
        ]
    }

    rows = validate_asset_contract(runbook, runbook_path=runbook_path)
    by_asset = {row["asset_id"]: row for row in rows}
    assert by_asset["3A"]["status"] == "ok"
    assert by_asset["3B"]["status"] == "failed"


def test_collect_failed_assets_groups_by_batch() -> None:
    runbook = {
        "assets": [
            _asset("3A", status="validated"),
            _asset("3B", status="failed_validation"),
            {**_asset("4A", status="validated"), "batch_type": "photography", "validation_errors": ["x"]},
        ]
    }
    grouped, total = collect_failed_assets(runbook)
    assert total == 2
    assert grouped["products"] == ["3B"]
    assert grouped["photography"] == ["4A"]
