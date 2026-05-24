from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from brandmint.core.design_memory import search_design_memory


class _Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_search_design_memory_posts_query_and_returns_existing_paths(monkeypatch, tmp_path: Path) -> None:
    ref = tmp_path / "reference.png"
    ref.write_bytes(b"png")
    calls = []

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        calls.append((request, timeout))
        payload = {
            "results": [
                {"asset": {"path": str(ref)}},
                {"asset": {"path": str(tmp_path / "missing.png")}},
            ]
        }
        return _Response(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("brandmint.core.design_memory.urllib.request.urlopen", fake_urlopen)

    paths = search_design_memory(
        "https://worker.example",
        query="premium oracle identity",
        aspect="1:1",
        limit=3,
        timeout_sec=2,
    )

    assert paths == [str(ref)]
    request, timeout = calls[0]
    assert request.full_url == "https://worker.example/search"
    assert timeout == 2
    assert json.loads(request.data.decode("utf-8"))["query"] == "premium oracle identity"


def test_search_design_memory_returns_empty_without_url() -> None:
    assert search_design_memory("", query="anything") == []
