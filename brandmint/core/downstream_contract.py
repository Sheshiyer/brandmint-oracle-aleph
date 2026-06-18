"""Build Cambium downstream variable contracts from Brandmint state."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


def _compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _compact(v) for k, v in value.items() if _compact(v) not in (None, "", [], {})}
    if isinstance(value, list):
        return [_compact(v) for v in value if _compact(v) not in (None, "", [], {})]
    return value


def _first(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _as_list(value: Any) -> List[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def _visual_assets_from_wave_plan(wave_plan: Optional[Iterable[Any]]) -> List[str]:
    assets: List[str] = []
    for wave in wave_plan or []:
        if isinstance(wave, dict):
            assets.extend(str(v) for v in wave.get("visual_assets", []) if v)
            continue
        values = getattr(wave, "visual_assets", [])
        assets.extend(str(v) for v in values if v)
    return list(dict.fromkeys(assets))


def build_downstream_variable_contract(
    config: Dict[str, Any],
    skill_outputs: Optional[Dict[str, Dict[str, Any]]] = None,
    *,
    wave_plan: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:
    """Return the structured seed pack Cambium's next organs consume.

    The contract is intentionally derived from existing Brandmint config and
    skill outputs, so genesis can hand downstream organs brand, copy, visual,
    asset, and section intent without flattening everything into prose.
    """
    skill_outputs = skill_outputs or {}
    brand = config.get("brand", {}) if isinstance(config.get("brand"), dict) else {}
    theme = config.get("theme", {}) if isinstance(config.get("theme"), dict) else {}
    positioning = config.get("positioning", {}) if isinstance(config.get("positioning"), dict) else {}
    palette = config.get("palette", {}) if isinstance(config.get("palette"), dict) else {}
    typography = config.get("typography", {}) if isinstance(config.get("typography"), dict) else {}
    aesthetic = config.get("aesthetic", {}) if isinstance(config.get("aesthetic"), dict) else {}
    products = config.get("products", {}) if isinstance(config.get("products"), dict) else {}
    audience = config.get("audience", {}) if isinstance(config.get("audience"), dict) else {}

    campaign = skill_outputs.get("campaign-page-copy", {}).get("handoff", {})
    visual = skill_outputs.get("visual-identity-core", {})
    voice = skill_outputs.get("voice-and-tone", {})
    detailed = skill_outputs.get("detailed-product-description", {})

    brand_system = {
        "name": brand.get("name"),
        "brand_archetype": _first(brand.get("archetype"), theme.get("name"), brand.get("domain")),
        "positioning": _first(positioning.get("statement"), skill_outputs.get("product-positioning-summary", {}).get("positioning_statement")),
        "audience": _first(audience.get("persona_name"), skill_outputs.get("buyer-persona", {}).get("persona", {}).get("name")),
        "voice": _first(brand.get("voice"), voice.get("voice_persona")),
        "tone": _first(brand.get("tone"), voice.get("tone_calibration")),
    }
    copy_system = {
        "hero_headline": positioning.get("hero_headline"),
        "tagline": positioning.get("tagline"),
        "pillars": positioning.get("pillars"),
        "cta_primary": _first(*(campaign.get("cta_language", []) if isinstance(campaign.get("cta_language"), list) else [])),
        "faq": campaign.get("faq"),
    }
    visual_primitives = {
        "palette": palette or visual.get("color_palette"),
        "typography": typography or visual.get("typography"),
        "motion_style": _first(aesthetic.get("motion_style"), visual.get("motion_style")),
        "surface_treatment": _first(aesthetic.get("hero_surface"), visual.get("imagery", {}).get("hero_surface")),
        "hero_object_type": _first(aesthetic.get("hero_object_type"), visual.get("imagery", {}).get("hero_object_type")),
        "logo_treatment": _first(aesthetic.get("logo_treatment"), visual.get("logo_usage", {}).get("treatment")),
    }
    asset_requirements = {
        "required": list(dict.fromkeys([
            "logo",
            "hero_media",
            *(_visual_assets_from_wave_plan(wave_plan)),
            *(["product_shot"] if products.get("hero") or detailed.get("hero_product") else []),
        ])),
        "hero_product": _first(products.get("hero"), detailed.get("hero_product")),
        "avoid_visual_patterns": config.get("competitive_context", {}).get("avoid_visual_patterns") if isinstance(config.get("competitive_context"), dict) else None,
    }
    section_defaults = {
        "ordered_sections": ["hero", "problem", "solution", "proof", "pricing", "cta"],
        "hero": {
            "copy_slot": "hero_headline",
            "asset_requirements": ["hero_media", "logo"],
        },
        "proof": {
            "copy_slot": "proof_points",
            "asset_requirements": ["product_shot"],
        },
        "cta": {
            "copy_slot": "cta_primary",
        },
    }
    contract = {
        "brand_system": brand_system,
        "copy_system": copy_system,
        "visual_primitives": visual_primitives,
        "visual_system": visual_primitives,
        "asset_requirements": asset_requirements,
        "asset_plan": asset_requirements,
        "section_defaults": section_defaults,
        "section_plan": section_defaults["ordered_sections"],
    }
    return _compact(contract)
