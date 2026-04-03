from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_generate_pipeline():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "scripts" / "generate_pipeline.py"
    spec = spec_from_file_location("brandmint_generate_pipeline", path)
    module = module_from_spec(spec)
    assert spec and spec.loader
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
