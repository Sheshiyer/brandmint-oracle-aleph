from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_generate_pipeline():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "scripts" / "generate_pipeline.py"
    spec = spec_from_file_location("brandmint_generate_pipeline", path)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_aesthetic_engine():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "scripts" / "aesthetic_engine.py"
    spec = spec_from_file_location("brandmint_aesthetic_engine", path)
    module = module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_normalize_product_prompt_ids_rewrites_legacy_keys() -> None:
    gp = _load_generate_pipeline()
    cfg = {"prompts": {"products": ["capsule_collection", "hero_book", "essence_vial", "hero_product"]}}

    replacements = gp.normalize_product_prompt_ids(cfg)

    assert replacements == [("hero_book", "hero_product"), ("essence_vial", "product_detail")]
    assert cfg["prompts"]["products"] == ["capsule_collection", "hero_product", "product_detail"]



def test_validate_product_spec_consistency_flags_screen_and_dock_conflicts() -> None:
    gp = _load_generate_pipeline()
    cfg = {
        "products": {
            "hero": {
                "name": "ZackAI Smart Plush",
                "description": "Screen-free plush companion",
                "physical_form": "Round plush creature with cat-like ears and USB-C charging",
            },
            "flatlay_objects": {
                "items": [
                    "USB-C charging cable",
                    "Companion app shown on phone screen beside plush",
                ]
            },
        },
        "materials": ["soft plush", "USB-C charging dock"],
        "negative_prompt": "screen, tablet, phone, teddy bear",
        "photography": {"constraint": "No screens visible"},
        "prompts": {"products": ["hero_book", "essence_vial"]},
    }

    errors = gp.validate_product_spec_consistency(cfg)

    assert any("screen instructions" in err for err in errors)
    assert any("charging instructions" in err for err in errors)
    assert any("Legacy product prompt ids" in err for err in errors)



def test_build_product_spec_lock_contains_exact_form_and_bans() -> None:
    gp = _load_generate_pipeline()
    cfg = {
        "products": {
            "hero": {
                "name": "ZackAI Smart Plush — Phantom Purple",
                "description": "AI-powered plush companion",
                "physical_form": "Round, ball-shaped fluffy plush creature in Muted Lilac with cat-like ears and USB-C charging",
            },
            "detail": {
                "focus": "Close-up of LED eyes, stitched smile, plush texture, and the USB-C charging port seam"
            },
            "flatlay_objects": {
                "items": [
                    "ZackAI plush toy (Phantom Purple)",
                    "USB-C charging cable",
                    "Product packaging box",
                ]
            },
        },
    }

    lock = gp.build_product_spec_lock(
        cfg,
        primary_name="Muted Lilac",
        primary_hex="#AA98D6",
        negative_prompt="teddy bear, screen, phone, tablet",
    )

    assert "ZackAI Smart Plush — Phantom Purple" in lock
    assert "Round, ball-shaped fluffy plush creature" in lock
    assert "Muted Lilac (#AA98D6)" in lock
    assert "USB-C charging cable" in lock
    assert "teddy bear / bear silhouette" in lock
    assert "screens or phone/tablet devices" in lock


def test_heyzack_system_presence_override_updates_8a_prompt() -> None:
    gp = _load_generate_pipeline()
    ae = _load_aesthetic_engine()
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "brandmint-run" / "heyzack-ai" / "brand-config.yaml"

    cfg = gp.load_config(str(config_path))
    exec_ctx = gp.load_execution_context(str(config_path), cfg)
    v = gp.build_vars(cfg, exec_ctx, config_path=str(config_path))

    registry = ae.load_template_variants(str(repo_root / "assets" / "template-variants.yaml"))
    profile = ae.AestheticClassifier().classify(v, None)
    selections = ae.TemplateMatcher().select_variants(profile, registry, cfg.get("aesthetic", {}))
    v = ae.inject_variant_vars(v, selections, registry, profile)

    prompt = gp.render(gp.PROMPT_8A_SEEKER, v)

    assert selections["8A"] == "system_presence"
    assert "SYSTEM INTELLIGENCE" in prompt
    assert "Approved hero subject only" in prompt
    assert "no human portrait" in prompt
    assert "The Seeker" not in prompt


def test_recraft_helper_does_not_append_hidden_prompt_suffix() -> None:
    gp = _load_generate_pipeline()

    rendered = gp.render(gp.FUNC_RECRAFT, {"seed_a": 42, "seed_b": 137})

    assert "enhanced_prompt" not in rendered
    assert "gen_with_provider(\n            prompt," in rendered
