from pathlib import Path

from typer.testing import CliRunner

from brandmint.cli.app import app
from brandmint.installer import setup_skills


runner = CliRunner()


def test_resolve_install_provider_prefers_explicit_provider(tmp_path: Path, monkeypatch):
    config = tmp_path / "brand-config.yaml"
    config.write_text(
        "generation:\n"
        "  provider: openrouter\n"
        "  fallback_chain:\n"
        "    - inference\n"
        "    - fal\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("IMAGE_PROVIDER", "replicate")

    provider, fallback_chain = setup_skills.resolve_install_provider(
        config=config,
        provider="inference",
    )

    assert provider == "inference"
    assert fallback_chain == ["inference", "fal"]


def test_resolve_install_provider_uses_config_and_rejects_unknown_fallbacks(tmp_path: Path):
    config = tmp_path / "brand-config.yaml"
    config.write_text(
        "generation:\n"
        "  provider: openai\n"
        "  fallback_chain:\n"
        "    - openrouter\n"
        "    - bogus\n"
        "    - inference\n",
        encoding="utf-8",
    )

    try:
        setup_skills.resolve_install_provider(config=config)
    except ValueError as exc:
        assert "generation.fallback_chain" in str(exc)
        assert "bogus" in str(exc)
    else:
        raise AssertionError("Expected invalid config fallback provider to raise ValueError")


def test_resolve_install_provider_rejects_invalid_explicit_provider():
    try:
        setup_skills.resolve_install_provider(provider="openroutr")
    except ValueError as exc:
        assert "--provider must be one of" in str(exc)
    else:
        raise AssertionError("Expected invalid provider to raise ValueError")


def test_resolve_install_provider_rejects_missing_config_path(tmp_path: Path):
    missing = tmp_path / "missing.yaml"

    try:
        setup_skills.resolve_install_provider(config=missing)
    except FileNotFoundError as exc:
        assert str(missing) in str(exc)
    else:
        raise AssertionError("Expected missing config path to raise FileNotFoundError")


def test_resolve_install_provider_rejects_invalid_provider_in_config(tmp_path: Path):
    config = tmp_path / "brand-config.yaml"
    config.write_text(
        "generation:\n"
        "  provider: openroutr\n",
        encoding="utf-8",
    )

    try:
        setup_skills.resolve_install_provider(config=config)
    except ValueError as exc:
        assert "generation.provider" in str(exc)
        assert "openroutr" in str(exc)
    else:
        raise AssertionError("Expected invalid config provider to raise ValueError")


def test_evaluate_provider_readiness_for_inference_requires_only_api_key(monkeypatch):
    monkeypatch.setattr(
        setup_skills,
        "check_env_var",
        lambda name: name == "INFERENCE_API_KEY",
    )

    results = setup_skills.evaluate_provider_readiness("inference")

    assert results == {"INFERENCE_API_KEY set": True}


def test_evaluate_provider_readiness_for_auto_uses_fallback_candidates(monkeypatch):
    monkeypatch.setattr(
        setup_skills,
        "_provider_ready",
        lambda provider_name: provider_name == "inference",
    )
    monkeypatch.setattr(
        setup_skills,
        "_provider_import_check_name",
        lambda provider_name: "fal-client installed" if provider_name == "fal" else None,
    )
    monkeypatch.setattr(
        setup_skills,
        "_provider_import_ready",
        lambda provider_name: False,
    )

    results = setup_skills.evaluate_provider_readiness(
        "auto",
        fallback_chain=["fal", "inference"],
    )

    assert results["auto candidate fal"] is False
    assert results["fal-client installed (fal)"] is False
    assert results["auto candidate inference"] is True
    assert results["auto provider availability"] is True


def test_install_check_cli_passes_provider_and_config(monkeypatch, tmp_path: Path):
    config = tmp_path / "brand-config.yaml"
    config.write_text("generation:\n  provider: inference\n", encoding="utf-8")
    captured = {}

    def fake_check_installation(console=None, provider=None, config=None):
        captured["provider"] = provider
        captured["config"] = config
        return {}

    monkeypatch.setattr(setup_skills, "check_installation", fake_check_installation)

    result = runner.invoke(
        app,
        ["install", "check", "--provider", "inference", "--config", str(config)],
    )

    assert result.exit_code == 0
    assert captured == {"provider": "inference", "config": config}


def test_install_check_cli_fails_for_invalid_provider():
    result = runner.invoke(
        app,
        ["install", "check", "--provider", "openroutr"],
    )

    assert result.exit_code == 2
    assert "--provider must be one of" in result.stdout


def test_install_check_cli_fails_for_missing_config(tmp_path: Path):
    missing = tmp_path / "missing.yaml"

    result = runner.invoke(
        app,
        ["install", "check", "--config", str(missing)],
    )

    assert result.exit_code == 2
    assert "Config file not found:" in result.stdout
    assert str(missing).replace("/", "") in result.stdout.replace("/", "").replace("\n", "")
