import json
import time
from io import StringIO
from pathlib import Path

from rich.console import Console

from brandmint.models.wave import ExecutionState
from brandmint.pipeline.executor import WaveExecutor
from brandmint.publishing import notebooklm_publisher as notebooklm_module
from brandmint.publishing.notebooklm_publisher import NotebookLMPublisher


def _test_console() -> tuple[Console, StringIO]:
    buffer = StringIO()
    console = Console(
        file=buffer,
        force_terminal=False,
        color_system=None,
        width=120,
    )
    return console, buffer


def _build_executor_for_state_tests(state_path: Path, config: dict, console: Console) -> WaveExecutor:
    executor = WaveExecutor.__new__(WaveExecutor)
    executor.state_path = state_path
    executor.config = config
    executor.console = console
    return executor


def _build_publisher(tmp_path: Path, console: Console) -> NotebookLMPublisher:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    config_path = brand_dir / "brand-config.yaml"
    config_path.write_text("brand:\n  name: Test Brand\n", encoding="utf-8")
    return NotebookLMPublisher(
        brand_dir=brand_dir,
        config={"brand": {"name": "Test Brand"}},
        config_path=config_path,
        console=console,
    )


def test_executor_load_healthy_state_preserves_existing_data(tmp_path: Path) -> None:
    state_path = tmp_path / ".brandmint-state.json"
    state_path.write_text(
        json.dumps(
            {
                "brand": "Test Brand",
                "scenario": "custom-hybrid",
                "started_at": "2026-04-01T10:00:00",
                "updated_at": "2026-04-01T10:05:00",
                "waves": {
                    "1": {
                        "status": "completed",
                        "text_skills": {"1A": {"status": "completed"}},
                        "visual_assets": {},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    console, buffer = _test_console()
    executor = _build_executor_for_state_tests(
        state_path=state_path,
        config={"brand": {"name": "Test Brand"}},
        console=console,
    )

    state = executor._load_or_create_state()

    assert state.brand == "Test Brand"
    assert state.waves["1"]["status"] == "completed"
    assert not list(tmp_path.glob(".brandmint-state.corrupted-*.json"))
    assert "repaired" not in buffer.getvalue().lower()


def test_executor_load_repair_creates_backup_and_surfaces_notice(tmp_path: Path) -> None:
    state_path = tmp_path / ".brandmint-state.json"
    state_path.write_text(
        json.dumps(
            {
                "brand": "Test Brand",
                "scenario": "custom-hybrid",
                "waves": [],  # Invalid shape: must be object
            }
        ),
        encoding="utf-8",
    )

    console, buffer = _test_console()
    executor = _build_executor_for_state_tests(
        state_path=state_path,
        config={"brand": {"name": "Test Brand"}},
        console=console,
    )

    state = executor._load_or_create_state()

    assert isinstance(state, ExecutionState)
    assert state.brand == "Test Brand"
    assert state.waves == {}
    assert list(tmp_path.glob(".brandmint-state.corrupted-*.json"))
    assert "repaired" in buffer.getvalue().lower()


def test_executor_save_state_uses_safe_save(monkeypatch, tmp_path: Path) -> None:
    state_path = tmp_path / ".brandmint-state.json"
    console, _ = _test_console()
    executor = _build_executor_for_state_tests(
        state_path=state_path,
        config={"brand": {"name": "Test Brand"}},
        console=console,
    )
    executor.state = ExecutionState(brand="Test Brand")

    calls: dict = {}

    def fake_save_state_safe(state: dict, path: Path, state_type: str = "execution") -> bool:
        calls["state"] = state
        calls["path"] = path
        calls["state_type"] = state_type
        return True

    monkeypatch.setattr("brandmint.pipeline.executor.save_state_safe", fake_save_state_safe)

    executor._save_state()

    assert calls["state_type"] == "execution"
    assert calls["path"] == state_path
    assert calls["state"]["brand"] == "Test Brand"
    assert "updated_at" in calls["state"]


def test_notebooklm_load_repair_creates_backup_and_surfaces_notice(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    state_dir = brand_dir / ".brandmint"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "notebooklm-state.json"
    state_path.write_text(
        json.dumps(
            {
                "notebook_id": 123,  # Invalid type
                "sources_uploaded": "not-a-list",
                "artifacts_generated": "not-an-object",
            }
        ),
        encoding="utf-8",
    )

    console, buffer = _test_console()
    publisher = _build_publisher(tmp_path, console)

    assert publisher.state["notebook_id"] is None
    assert publisher.state["sources_uploaded"] == []
    assert publisher.state["artifacts_generated"] == {}
    assert list(state_dir.glob("notebooklm-state.corrupted-*.json"))
    assert "repaired" in buffer.getvalue().lower()


def test_notebooklm_persist_progress_uses_safe_save(monkeypatch, tmp_path: Path) -> None:
    console, _ = _test_console()
    publisher = _build_publisher(tmp_path, console)

    calls: dict = {}

    def fake_save_state_safe(state: dict, path: Path, state_type: str = "execution") -> bool:
        calls["state"] = state
        calls["path"] = path
        calls["state_type"] = state_type
        return True

    monkeypatch.setattr(notebooklm_module, "save_state_safe", fake_save_state_safe)
    monkeypatch.setattr(publisher, "_save_report", lambda elapsed, artifact_defs: None)

    started = time.time() - 1
    publisher._persist_progress(started=started, artifact_defs=[])

    assert calls["state_type"] == "notebooklm"
    assert calls["path"] == publisher.state_path
    assert "updated_at" in calls["state"]
