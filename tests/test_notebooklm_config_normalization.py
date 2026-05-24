from __future__ import annotations

from brandmint.publishing.config_normalization import (
    notebooklm_config_warnings,
    resolve_notebooklm_config,
    resolve_synthesis_settings,
)


def test_resolve_notebooklm_config_legacy_only() -> None:
    cfg = {
        "notebooklm": {
            "max_parallel_workers": 2,
            "reuse_policy": "reuse-existing",
        }
    }
    resolved = resolve_notebooklm_config(cfg)
    assert resolved["max_parallel_workers"] == 2
    assert resolved["reuse_policy"] == "reuse-existing"


def test_resolve_notebooklm_config_canonical_only() -> None:
    cfg = {
        "publishing": {
            "notebooklm": {
                "max_parallel_workers": 7,
                "reuse_policy": "fresh-per-spec",
            }
        }
    }
    resolved = resolve_notebooklm_config(cfg)
    assert resolved["max_parallel_workers"] == 7
    assert resolved["reuse_policy"] == "fresh-per-spec"


def test_resolve_notebooklm_config_canonical_overrides_legacy() -> None:
    cfg = {
        "notebooklm": {"max_parallel_workers": 1},
        "publishing": {"notebooklm": {"max_parallel_workers": 9}},
    }
    resolved = resolve_notebooklm_config(cfg)
    assert resolved["max_parallel_workers"] == 9


def test_resolve_synthesis_settings_nested_overrides_legacy_path() -> None:
    cfg = {
        "publishing": {
            "synthesize": False,
            "synthesis_model": "legacy/model",
            "notebooklm": {
                "synthesize": True,
                "synthesis_model": "canonical/model",
            },
        }
    }
    synthesize, model = resolve_synthesis_settings(cfg)
    assert synthesize is True
    assert model == "canonical/model"


def test_resolve_synthesis_settings_fallback_to_legacy_path() -> None:
    cfg = {
        "publishing": {
            "synthesize": False,
            "synthesis_model": "legacy/model",
        }
    }
    synthesize, model = resolve_synthesis_settings(cfg)
    assert synthesize is False
    assert model == "legacy/model"


def test_notebooklm_config_warnings_detect_mixed_and_legacy_keys() -> None:
    cfg = {
        "notebooklm": {"max_parallel_workers": 2},
        "publishing": {
            "synthesize": True,
            "synthesis_model": "legacy/model",
            "notebooklm": {"max_parallel_workers": 3},
        },
    }
    warnings = notebooklm_config_warnings(cfg)
    assert any("both `notebooklm`" in warning for warning in warnings)
    assert any("publishing.{synthesize,synthesis_model}" in warning for warning in warnings)
