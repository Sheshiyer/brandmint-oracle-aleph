import json

from brandmint.core.providers import DEFAULT_FALLBACK_CHAIN, get_provider
from brandmint.core.providers.inference_provider import InferenceProvider


class _Response:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_inference_provider_missing_key(monkeypatch, tmp_path):
    monkeypatch.delenv("INFERENCE_API_KEY", raising=False)
    provider = InferenceProvider()

    result = provider.generate(
        prompt="test",
        model="nano-banana-pro",
        output_path=str(tmp_path / "out.png"),
    )

    assert result.success is False
    assert "INFERENCE_API_KEY" in (result.error or "")


def test_inference_provider_generate_success(monkeypatch, tmp_path):
    monkeypatch.setenv("INFERENCE_API_KEY", "inf_test_key")
    monkeypatch.setenv("INFERENCE_BASE_URL", "https://api.inference.sh")
    monkeypatch.setattr("brandmint.core.providers.inference_provider.time.sleep", lambda _: None)

    task_calls = {"count": 0}

    def fake_urlopen(req, timeout=0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        method = req.get_method() if hasattr(req, "get_method") else "GET"

        if url.endswith("/api/v1/apps/run") and method == "POST":
            return _Response(json.dumps({"task_id": "task-123"}).encode("utf-8"))

        if url.endswith("/api/v1/tasks/task-123") and method == "GET":
            task_calls["count"] += 1
            if task_calls["count"] == 1:
                return _Response(json.dumps({"status": "running"}).encode("utf-8"))
            return _Response(
                json.dumps(
                    {
                        "status": "completed",
                        "result": {"images": [{"url": "https://cdn.example/generated.png"}]},
                    }
                ).encode("utf-8")
            )

        if url == "https://cdn.example/generated.png":
            return _Response(b"\x89PNG\r\n\x1a\nfakepng")

        raise AssertionError(f"Unexpected request: {method} {url}")

    monkeypatch.setattr("brandmint.core.providers.inference_provider.urllib.request.urlopen", fake_urlopen)

    output = tmp_path / "generated.png"
    provider = InferenceProvider()
    result = provider.generate(
        prompt="brand hero visual",
        model="nano-banana-pro",
        output_path=str(output),
        image_urls=["/tmp/ref1.png", "/tmp/ref2.png"],
    )

    assert result.success is True
    assert result.provider == "Inference"
    assert result.model_used == "infsh-ai-image-generation"
    assert result.image_url == "https://cdn.example/generated.png"
    assert output.exists()
    assert task_calls["count"] >= 2


def test_provider_factory_registers_inference(monkeypatch):
    monkeypatch.setenv("INFERENCE_API_KEY", "inf_test_key")
    provider = get_provider("inference")

    assert isinstance(provider, InferenceProvider)
    assert DEFAULT_FALLBACK_CHAIN[-1] == "inference"
