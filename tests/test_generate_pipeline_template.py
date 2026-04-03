from pathlib import Path


def _template_source() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / "scripts" / "generate_pipeline.py").read_text()


def test_template_uses_core_provider_adapters_only() -> None:
    src = _template_source()

    assert "from brandmint.core.providers import get_provider as _bm_get_provider" in src
    assert "CORE_PROVIDER = _bm_get_provider(PROVIDER)" in src
    assert "def gen_with_provider(" in src

    # Legacy inline HTTP implementations are removed from generated templates.
    assert "def gen_with_openrouter(" not in src
    assert "def gen_with_openai(" not in src
    assert "def gen_with_replicate(" not in src
    assert "def gen_with_non_fal(" not in src
    assert "fal_client.upload_file(" not in src
    assert "download_image(" not in src


def test_template_supports_inference_provider_env_bridge() -> None:
    src = _template_source()

    assert "SUPPORTED_PROVIDERS =" in src
    assert '"inference"' in src
    assert 'os.environ.setdefault("INFERENCE_BASE_URL", INFERENCE_ENDPOINT)' in src
    assert 'os.environ.setdefault("INFERENCE_IMAGE_APP", INFERENCE_APP)' in src


def test_generated_batches_route_references_through_upload_helper() -> None:
    src = _template_source()
    expected = [
        "ref_url = upload_reference(ref_path)",
        "anchor_url = upload_reference(STYLE_ANCHOR)",
        "ref_url = upload_reference(ref_8a)",
        "ref_url = upload_reference(ref_9a)",
        "ref_url = upload_reference(ref_10)",
    ]
    for marker in expected:
        assert marker in src



def test_template_enforces_reference_payload_for_nano_banana() -> None:
    src = _template_source()

    assert 'REFERENCE_POLICY = os.environ.get("BRANDMINT_REFERENCE_POLICY", "error")' in src
    assert "def enforce_reference_payload(pid, image_urls):" in src
    assert "enforce_reference_payload(pid, image_urls)" in src
    assert "degrade to text-only generation" in src



def test_template_includes_product_spec_lock() -> None:
    src = _template_source()

    assert "def build_product_spec_lock(" in src
    assert "SPEC LOCK: Depict only" in src
    assert "{product_spec_lock}" in src
    assert 'get_ref_image("3C")' not in src
    assert 'get_supp_ref_images("3C")' not in src



def test_model_callsites_use_unified_gen_with_provider() -> None:
    src = _template_source()

    assert '"nano-banana-pro"' in src
    assert '"flux-2-pro"' in src
    assert '"recraft-v3"' in src
    assert "gen_with_provider(" in src
