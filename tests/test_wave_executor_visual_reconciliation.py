from pathlib import Path

from brandmint.cli.report import ExecutionReport
from brandmint.models.wave import ExecutionState
from brandmint.pipeline.executor import WaveExecutor


def _build_executor(tmp_path: Path) -> WaveExecutor:
    executor = WaveExecutor.__new__(WaveExecutor)
    executor.brand_dir = tmp_path
    executor.config = {
        "brand": {"name": "HeyZack"},
        "generation": {"output_dir": "generated"},
    }
    executor._provider = "fal"
    executor._actual_costs = {}
    executor.state = ExecutionState(brand="HeyZack")
    executor.state_path = tmp_path / ".brandmint-state.json"
    executor._report = ExecutionReport(
        brand_name="HeyZack",
        scenario="custom-hybrid",
        started_at="2026-04-04T00:00:00",
    )
    return executor


def test_reconcile_batch_results_preserves_partial_visual_success(tmp_path: Path) -> None:
    generated_dir = tmp_path / "heyzack" / "generated"
    generated_dir.mkdir(parents=True)
    (generated_dir / "5B-campaign-grid-nanobananapro-v1.png").write_bytes(b"png")

    executor = _build_executor(tmp_path)

    succeeded, failed = executor._reconcile_batch_asset_results(
        batch_name="illustration",
        batch_asset_ids=["5A", "5B", "5C"],
        wave_num=5,
        duration=12.5,
        error_msg="provider batch failed",
    )

    assert succeeded == ["5B"]
    assert failed == ["5A", "5C"]

    asset_state = executor.state.waves["5"]["visual_assets"]
    assert asset_state["5B"]["status"] == "completed"
    assert asset_state["5A"]["status"] == "failed"
    assert asset_state["5C"]["status"] == "failed"

    report_by_asset = {asset.asset_id: asset for asset in executor._report.assets}
    assert report_by_asset["5B"].status == "success"
    assert report_by_asset["5B"].file_path.endswith("5B-campaign-grid-nanobananapro-v1.png")
    assert report_by_asset["5A"].status == "failed"
    assert report_by_asset["5C"].status == "failed"
