from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_run_pipeline():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "scripts" / "run_pipeline.py"
    spec = spec_from_file_location("brandmint_run_pipeline", path)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_run_pipeline_catalog_drops_unsupported_icon_lane() -> None:
    rp = _load_run_pipeline()

    assert "5D" not in rp.ASSET_CATALOG
    assert "5D" not in rp.BATCH_EXPECTED_PREFIX_PATTERNS["illustration"]


def test_run_pipeline_catalog_aligns_product_and_flatlay_models() -> None:
    rp = _load_run_pipeline()

    assert rp.ASSET_CATALOG["3A"]["model"] == "nano-banana-pro"
    assert rp.ASSET_CATALOG["3B"]["model"] == "nano-banana-pro"
    assert rp.ASSET_CATALOG["3C"]["model"] == "nano-banana-pro"
    assert rp.ASSET_CATALOG["4B"]["model"] == "nano-banana-pro"
    assert rp.ASSET_CATALOG["3A"]["cost_per_seed"] == 0.08
    assert rp.ASSET_CATALOG["4B"]["cost_per_seed"] == 0.08


def test_wave_planner_gives_8a_an_extra_seed_off_surface() -> None:
    from brandmint.core import wave_planner

    assert wave_planner._visual_asset_cost(["8A"], seeds=2, depth="surface") == 0.16
    assert wave_planner._visual_asset_cost(["8A"], seeds=2, depth="focused") == 0.24
