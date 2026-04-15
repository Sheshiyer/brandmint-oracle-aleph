from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from brandmint.core.asset_registry import select_assets
from brandmint.core.wave_planner import compute_wave_plan


def _load_generate_pipeline():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "scripts" / "generate_pipeline.py"
    spec = spec_from_file_location("brandmint_generate_pipeline_ref_policy", path)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_heyzack_config():
    repo_root = Path(__file__).resolve().parents[1]
    gp = _load_generate_pipeline()
    config_path = repo_root / "brandmint-run" / "heyzack-ai" / "brand-config.yaml"
    cfg = gp.load_config(str(config_path))
    return gp, cfg, config_path


def test_heyzack_strict_supplementary_ref_policy_returns_no_generic_examples():
    gp, cfg, _ = _load_heyzack_config()
    repo_root = Path(__file__).resolve().parents[1]

    policy = gp._derive_supp_ref_policy(cfg)
    supp_refs = gp.select_supp_refs(
        [],
        [],
        catalog_yaml_path=str(repo_root / "references" / "reference-catalog.yaml"),
        brand_domain_tags=cfg["brand"]["domain_tags"],
        selection_policy=policy,
    )

    assert supp_refs == {}


def test_heyzack_asset_exclusions_are_applied_in_registry_and_wave_plan():
    _, cfg, _ = _load_heyzack_config()
    excluded = set(cfg["generation"]["excluded_assets"])

    selected = select_assets(
        cfg["brand"]["domain_tags"],
        depth=cfg["execution_context"]["depth_level"],
        channel=cfg["execution_context"]["launch_channel"],
        excluded_assets=cfg["generation"]["excluded_assets"],
    )
    selected_ids = {asset_id for asset_id, _ in selected}
    assert excluded.isdisjoint(selected_ids)
    assert "5B" in selected_ids

    waves = compute_wave_plan(cfg, depth=cfg["execution_context"]["depth_level"])
    planned_ids = {asset_id for wave in waves for asset_id in wave.visual_assets}
    assert excluded.isdisjoint(planned_ids)
    assert "5B" in planned_ids


def test_illustration_script_omits_excluded_recraft_assets(tmp_path):
    gp, cfg, config_path = _load_heyzack_config()
    exec_ctx = gp.load_execution_context(str(config_path), cfg)
    v = gp.build_vars(cfg, exec_ctx, config_path=str(config_path))

    asset_groups = {"illustrations": [("5B", {"generator": "illustrations"})]}
    gp.gen_illustrations_script(str(tmp_path), v, cfg, asset_groups=asset_groups)

    script = (tmp_path / "generate-illustrations.py").read_text()

    assert "heritage-engraving" not in script
    assert "art-panel" not in script
    assert "PROMPT_5A" not in script
    assert "PROMPT_5C" not in script
    assert "campaign-grid" in script
