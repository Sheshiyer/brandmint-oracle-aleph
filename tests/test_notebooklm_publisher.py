from pathlib import Path

from brandmint.publishing.instruction_templates import DEFAULT_ARTIFACT_DEFINITIONS, ext_for_type
from brandmint.publishing.notebooklm_publisher import NotebookLMPublisher


class FakeClient:
    def __init__(self) -> None:
        self.generate_calls = []
        self.wait_calls = []
        self.download_calls = []
        self.create_notebook_calls = []

    def check_installed(self) -> bool:
        return True

    def check_authenticated(self) -> bool:
        return True

    def create_notebook(self, title: str) -> str:
        self.create_notebook_calls.append(title)
        return f"nb-created-{len(self.create_notebook_calls)}"

    def generate_artifact(self, artifact_type: str, notebook_id: str, instructions: str = "", extra_args=None) -> str:
        self.generate_calls.append((artifact_type, notebook_id))
        return f"{artifact_type}-artifact-id"

    def wait_for_artifact(self, artifact_id: str, notebook_id: str, timeout: int = 0) -> bool:
        self.wait_calls.append((artifact_id, notebook_id))
        return True

    def download_artifact(self, artifact_type: str, output_path: str, artifact_id: str, notebook_id: str):
        self.download_calls.append((artifact_type, output_path, artifact_id, notebook_id))
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"downloaded:{artifact_id}", encoding="utf-8")
        return True, ""


MINIMAL_ARTIFACT_DEF = {
    "id": "report-briefing",
    "type": "report",
    "instructions_fn": None,
    "output_filename": "report-briefing.md",
    "download_type": "report",
    "estimated_minutes": 1,
    "phase": "parallel-1",
    "extra_args": [],
    "group": "report",
    "description": "briefing",
}


def _make_publisher(tmp_path: Path) -> NotebookLMPublisher:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    config_path = brand_dir / "brand-config.yaml"
    config_path.write_text("brand:\n  name: Test Brand\n", encoding="utf-8")
    publisher = NotebookLMPublisher(
        brand_dir=brand_dir,
        config={"brand": {"name": "Test Brand"}},
        config_path=config_path,
    )
    publisher.client = FakeClient()
    publisher.state["notebook_id"] = "nb-123"
    publisher.state["notebook_fingerprint"] = publisher.notebook_fingerprint
    publisher.state.setdefault("artifacts", {})
    return publisher


def test_fingerprint_change_creates_fresh_notebook(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.state.update({
        "notebook_id": "nb-old",
        "notebook_fingerprint": "outdated123",
        "sources": {"legacy.png": {"status": "indexed"}},
        "artifacts": {"report-briefing": {"status": "completed"}},
    })

    notebook_id = publisher._ensure_notebook()

    assert notebook_id == "nb-created-1"
    assert publisher.client.create_notebook_calls
    assert publisher.state["previous_notebook_id"] == "nb-old"
    assert publisher.state["notebook_fingerprint"] == publisher.notebook_fingerprint
    assert publisher.state["sources"] == {}
    assert publisher.state["artifacts"] == {}



def test_reuse_existing_policy_keeps_current_notebook(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.notebook_reuse_policy = "reuse-existing"
    publisher.state.update({
        "notebook_id": "nb-old",
        "notebook_fingerprint": "outdated123",
    })

    notebook_id = publisher._ensure_notebook()

    assert notebook_id == "nb-old"
    assert publisher.client.create_notebook_calls == []



def test_generate_artifacts_does_not_resubmit_pending_on_resume(tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.state["artifacts"]["report-briefing"] = {
        "artifact_id": "existing-artifact",
        "status": "pending",
        "type": "report",
        "started_at": "2026-03-10T10:00:00",
    }

    publisher._generate_artifacts("nb-123", [MINIMAL_ARTIFACT_DEF])

    assert publisher.client.generate_calls == []



def test_publish_downloads_completed_undownloaded_before_generating(monkeypatch, tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.state["artifacts"]["report-briefing"] = {
        "artifact_id": "existing-artifact",
        "status": "completed",
        "type": "report",
        "started_at": "2026-03-10T10:00:00",
    }

    monkeypatch.setattr(publisher, "_build_artifact_defs", lambda: [MINIMAL_ARTIFACT_DEF])
    monkeypatch.setattr(publisher, "_build_sources", lambda: [object()])
    monkeypatch.setattr(publisher, "_upload_sources", lambda curated, notebook_id: None)
    monkeypatch.setattr(publisher, "_wait_for_indexing", lambda notebook_id: None)
    monkeypatch.setattr(publisher, "_print_summary", lambda elapsed, defs: None)

    ok = publisher.publish()

    assert ok is True
    assert publisher.client.generate_calls == []
    assert len(publisher.client.download_calls) == 1
    assert publisher.state["artifacts"]["report-briefing"]["downloaded"] is True
    assert publisher.report_path.exists()



def test_publish_writes_partial_report_on_failure(monkeypatch, tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)

    monkeypatch.setattr(publisher, "_build_artifact_defs", lambda: [MINIMAL_ARTIFACT_DEF])
    monkeypatch.setattr(publisher, "_build_sources", lambda: [object()])
    monkeypatch.setattr(publisher, "_upload_sources", lambda curated, notebook_id: None)
    monkeypatch.setattr(publisher, "_wait_for_indexing", lambda notebook_id: None)
    monkeypatch.setattr(publisher, "_generate_artifacts", lambda notebook_id, defs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(publisher, "_print_summary", lambda elapsed, defs: None)

    ok = publisher.publish()

    assert ok is False
    assert publisher.report_path.exists()
    report = publisher.report_path.read_text(encoding="utf-8")
    assert '"artifact_summary"' in report
    assert '"notebook_id": "nb-123"' in report


def test_targeted_retry_reuses_indexed_sources_without_rebuilding(monkeypatch, tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)

    publisher.artifact_filter = {"report-briefing"}
    publisher.state["sources"] = {
        "brand-foundation.md": {
            "source_id": "src-indexed",
            "status": "indexed",
            "source_type": "prose",
            "score": 94.0,
        },
        "primary-persona.md": {
            "status": "failed",
            "error": "Failed to add source",
        },
    }
    publisher.state["source_selection"] = {
        "count": 2,
        "files": ["brand-foundation.md", "primary-persona.md"],
        "image_source_policy": "manifest-only",
    }

    monkeypatch.setattr(publisher, "_build_artifact_defs", lambda: [MINIMAL_ARTIFACT_DEF])
    monkeypatch.setattr(
        publisher,
        "_build_sources",
        lambda: (_ for _ in ()).throw(AssertionError("_build_sources should not run")),
    )
    monkeypatch.setattr(
        publisher,
        "_upload_sources",
        lambda curated, notebook_id: (_ for _ in ()).throw(AssertionError("_upload_sources should not run")),
    )
    monkeypatch.setattr(
        publisher,
        "_wait_for_indexing",
        lambda notebook_id: (_ for _ in ()).throw(AssertionError("_wait_for_indexing should not run")),
    )
    monkeypatch.setattr(publisher, "_print_summary", lambda elapsed, defs: None)

    ok = publisher.publish()

    assert ok is True
    assert publisher.client.generate_calls == [("report", "nb-123")]
    assert list(publisher.state["sources"]) == ["brand-foundation.md"]
    assert publisher.state["source_selection"]["count"] == 1
    assert publisher.state["source_selection"]["files"] == ["brand-foundation.md"]



def test_download_failure_persists_error(monkeypatch, tmp_path: Path) -> None:
    publisher = _make_publisher(tmp_path)
    publisher.state["artifacts"]["report-briefing"] = {
        "artifact_id": "existing-artifact",
        "status": "completed",
        "type": "report",
        "started_at": "2026-03-10T10:00:00",
    }

    def failing_download(*, artifact_type, output_path, artifact_id, notebook_id):
        return False, "Authentication expired or invalid"

    monkeypatch.setattr(publisher.client, "download_artifact", failing_download)

    publisher._download_artifacts("nb-123", [MINIMAL_ARTIFACT_DEF])

    assert publisher.state["artifacts"]["report-briefing"]["download_error"] == "Authentication expired or invalid"
    assert publisher.state["artifacts"]["report-briefing"].get("downloaded") is not True



def test_data_table_artifacts_use_csv_output() -> None:
    assert ext_for_type("data-table") == "csv"
    filenames = {
        artifact["id"]: artifact["output_filename"]
        for artifact in DEFAULT_ARTIFACT_DEFINITIONS
        if artifact["type"] == "data-table"
    }
    assert filenames["table-competitive"].endswith(".csv")
    assert filenames["table-product"].endswith(".csv")
    assert filenames["table-persona"].endswith(".csv")
