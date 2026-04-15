from pathlib import Path
import json

import yaml

from brandmint.pipeline.visual_backend import (
    InferenceScaffoldExecutionBackend,
    SubprocessVisualExecutionBackend,
    create_visual_backend,
)


def _write_allowlist(path: Path, skills: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "version: 1\nskills:\n" + "".join(f"  - {sid}\n" for sid in skills),
        encoding="utf-8",
    )


def test_backend_factory_defaults_to_scripts(tmp_path: Path) -> None:
    backend = create_visual_backend(config={}, brand_dir=tmp_path)
    assert isinstance(backend, SubprocessVisualExecutionBackend)
    assert backend.name == "scripts"


def test_backend_factory_falls_back_to_scripts_when_inference_auth_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("INFERENCE_API_KEY", raising=False)
    backend = create_visual_backend(
        config={"generation": {"visual_backend": "inference"}},
        brand_dir=tmp_path,
    )
    assert isinstance(backend, SubprocessVisualExecutionBackend)
    assert backend.name == "scripts"


def test_backend_factory_can_remain_in_scaffold_mode_without_auth(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("INFERENCE_API_KEY", raising=False)
    backend = create_visual_backend(
        config={
            "generation": {
                "visual_backend": "inference",
                "inference_missing_auth_fallback": "scaffold",
            }
        },
        brand_dir=tmp_path,
    )
    assert isinstance(backend, InferenceScaffoldExecutionBackend)
    assert backend.name == "inference_scaffold"



def test_backend_factory_selects_inference_scaffold_when_auth_present(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("INFERENCE_API_KEY", "test-token")
    backend = create_visual_backend(
        config={"generation": {"visual_backend": "inference"}},
        brand_dir=tmp_path,
    )
    assert isinstance(backend, InferenceScaffoldExecutionBackend)
    assert backend.name == "inference_scaffold"



def test_inference_scaffold_backend_writes_asset_scaffolds(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "brand": {
            "name": "Test Brand",
            "tagline": "Build with confidence",
            "domain": "SaaS",
        },
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)
    result = backend.run_batch(
        script_path=tmp_path / "unused-script.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["APP-SCREENSHOT", "3A"],
        timeout_seconds=60,
    )

    assert result.returncode == 0

    out_dir = brand_dir / ".brandmint" / "inference-agent-scaffolds" / "products"
    app_screenshot_payload = json.loads((out_dir / "APP-SCREENSHOT.json").read_text())
    three_a_payload = json.loads((out_dir / "3A.json").read_text())
    runbook = json.loads((out_dir / "runbook.json").read_text())

    assert app_screenshot_payload["schema_version"] == "v1"
    assert app_screenshot_payload["status"] == "validated"
    assert isinstance(app_screenshot_payload["validation_errors"], list)
    assert app_screenshot_payload["routing"]["reason"] in {
        "asset_id_in_browser_assets",
        "keyword_match",
    }
    assert "confidence" in app_screenshot_payload["routing"]
    assert app_screenshot_payload["skills"]["media_skill_id"] == "infsh-agentic-browser"
    assert three_a_payload["skills"]["media_skill_id"] == "infsh-ai-image-generation"
    assert three_a_payload["media_input"]["app_id_hint"] == "falai/flux-2-klein-lora"
    assert len(three_a_payload["run_id"]) == 12
    assert len(three_a_payload["asset_run_id"]) == 12
    assert runbook["asset_count"] == 2
    assert runbook["summary"]["validated"] == 2
    assert runbook["summary"]["failed_validation"] == 0


def test_inference_scaffold_backend_merges_configured_asset_registry_paths(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    custom_registry = tmp_path / "custom-assets.yaml"
    custom_registry.write_text(
        yaml.safe_dump(
            {
                "assets": {
                    "CUSTOM-APP": {
                        "tags": ["app"],
                        "priority": 9,
                        "generator": "products",
                        "prompt_key": "custom_app",
                    }
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    config = {
        "brand": {"name": "Test Brand"},
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
            "asset_registry_paths": [str(custom_registry)],
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)

    assert "APP-SCREENSHOT" in backend._asset_registry
    assert "CUSTOM-APP" in backend._asset_registry


def test_inference_skill_policy_applies_asset_override_when_allowlisted(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    allowlist_path = tmp_path / "allowlist.yaml"
    _write_allowlist(
        allowlist_path,
        ["infsh-llm-models", "infsh-ai-image-generation", "infsh-agentic-browser"],
    )

    config = {
        "brand": {"name": "Test Brand"},
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
            "inference_skill_policy": {
                "allowlist_file": str(allowlist_path),
                "asset_overrides": {
                    "3A": {"media_skill_id": "infsh-agentic-browser"},
                },
            },
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)
    backend.run_batch(
        script_path=tmp_path / "unused-script.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["3A"],
        timeout_seconds=60,
    )
    out_dir = brand_dir / ".brandmint" / "inference-agent-scaffolds" / "products"
    payload = json.loads((out_dir / "3A.json").read_text())
    assert payload["skills"]["media_skill_id"] == "infsh-agentic-browser"


def test_inference_skill_policy_rejects_non_image_media_override(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    allowlist_path = tmp_path / "allowlist.yaml"
    _write_allowlist(
        allowlist_path,
        [
            "infsh-llm-models",
            "infsh-ai-image-generation",
            "infsh-agentic-browser",
            "infsh-web-search",
        ],
    )

    config = {
        "brand": {"name": "Test Brand"},
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
            "inference_skill_policy": {
                "allowlist_file": str(allowlist_path),
                "asset_overrides": {
                    "3A": {"media_skill_id": "infsh-web-search"},
                },
            },
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)
    backend.run_batch(
        script_path=tmp_path / "unused-script.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["3A"],
        timeout_seconds=60,
    )
    out_dir = brand_dir / ".brandmint" / "inference-agent-scaffolds" / "products"
    payload = json.loads((out_dir / "3A.json").read_text())
    assert payload["skills"]["media_skill_id"] == "infsh-ai-image-generation"


def test_semantic_routing_can_be_disabled(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    allowlist_path = tmp_path / "allowlist.yaml"
    _write_allowlist(
        allowlist_path,
        ["infsh-llm-models", "infsh-ai-image-generation", "infsh-agentic-browser"],
    )

    config = {
        "brand": {"name": "Test Brand"},
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
            "inference_skill_policy": {
                "allowlist_file": str(allowlist_path),
                "semantic_routing": {"enabled": False},
            },
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)
    backend.run_batch(
        script_path=tmp_path / "unused-script.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["APP-SCREENSHOT"],
        timeout_seconds=60,
    )
    out_dir = brand_dir / ".brandmint" / "inference-agent-scaffolds" / "products"
    payload = json.loads((out_dir / "APP-SCREENSHOT.json").read_text())
    assert payload["skills"]["media_skill_id"] == "infsh-ai-image-generation"


def test_semantic_routing_keyword_can_switch_asset_to_browser(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    allowlist_path = tmp_path / "allowlist.yaml"
    _write_allowlist(
        allowlist_path,
        ["infsh-llm-models", "infsh-ai-image-generation", "infsh-agentic-browser"],
    )

    config = {
        "brand": {"name": "Test Brand"},
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
            "inference_skill_policy": {
                "allowlist_file": str(allowlist_path),
                "semantic_routing": {
                    "enabled": True,
                    "browser_assets": [],
                    "browser_keywords": ["capsule"],
                },
            },
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)
    backend.run_batch(
        script_path=tmp_path / "unused-script.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["3A"],
        timeout_seconds=60,
    )
    out_dir = brand_dir / ".brandmint" / "inference-agent-scaffolds" / "products"
    payload = json.loads((out_dir / "3A.json").read_text())
    assert payload["skills"]["media_skill_id"] == "infsh-agentic-browser"


def test_style_anchor_check_warns_when_anchor_missing(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    allowlist_path = tmp_path / "allowlist.yaml"
    _write_allowlist(
        allowlist_path,
        ["infsh-llm-models", "infsh-ai-image-generation", "infsh-agentic-browser"],
    )

    config = {
        "brand": {"name": "Test Brand"},
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
            "inference_skill_policy": {
                "allowlist_file": str(allowlist_path),
            },
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)
    backend.run_batch(
        script_path=tmp_path / "unused-script.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["3A"],
        timeout_seconds=60,
    )
    out_dir = brand_dir / ".brandmint" / "inference-agent-scaffolds" / "products"
    payload = json.loads((out_dir / "3A.json").read_text())
    runbook = json.loads((out_dir / "runbook.json").read_text())
    assert payload["execution_plan"]["requires_anchor"] is True
    assert runbook["style_anchor_check"]["ok"] is False
    assert runbook["summary"]["warnings"] >= 1


def test_semantic_routing_domain_pack_file_can_adjust_routes(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    allowlist_path = tmp_path / "allowlist.yaml"
    rules_path = tmp_path / "semantic.yaml"
    _write_allowlist(
        allowlist_path,
        ["infsh-llm-models", "infsh-ai-image-generation", "infsh-agentic-browser"],
    )
    rules_path.write_text(
        "\n".join(
            [
                "version: v1",
                "default:",
                "  browser_assets: []",
                "  browser_keywords: []",
                "domain_packs:",
                "  app:",
                "    browser_assets: []",
                "    browser_keywords: [capsule]",
            ]
        ),
        encoding="utf-8",
    )

    config = {
        "brand": {"name": "Test Brand", "domain_tags": ["app"]},
        "generation": {
            "output_dir": "generated",
            "visual_backend": "inference",
            "inference_skill_policy": {
                "allowlist_file": str(allowlist_path),
                "semantic_routing": {
                    "enabled": True,
                    "rules_file": str(rules_path),
                },
            },
        },
    }

    backend = InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir)
    backend.run_batch(
        script_path=tmp_path / "unused-script.py",
        config_path=tmp_path / "brand-config.yaml",
        batch_name="products",
        asset_ids=["3A"],
        timeout_seconds=60,
    )
    out_dir = brand_dir / ".brandmint" / "inference-agent-scaffolds" / "products"
    payload = json.loads((out_dir / "3A.json").read_text())
    assert payload["skills"]["media_skill_id"] == "infsh-agentic-browser"
