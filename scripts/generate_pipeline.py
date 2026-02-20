#!/usr/bin/env python3
"""
generate_pipeline.py — Brandmint pipeline engine.
Reads brand-config.yaml → generates Python scripts + prompt cookbook.

Usage:
  python3 generate_pipeline.py ./my-brand/brand-config.yaml
  python3 generate_pipeline.py ./my-brand/brand-config.yaml --output-dir ./my-brand
"""
import argparse
import os
import sys
import textwrap
import re

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: uv pip install pyyaml")
    sys.exit(1)

try:
    import json
except ImportError:
    pass


# =====================================================================
# REFERENCE MAP LOADING
# =====================================================================

# Hardcoded fallback when reference-map.json is not available
_DEFAULT_REF_IMAGES = {
    "2A": "ref-2A-bento-grid.jpg",
    "2B": "ref-2B-brand-seal.jpg",
    "2C": "ref-2C-logo-emboss.jpg",
    "3A": "ref-3A-capsule-collection.jpg",
    "3B": "ref-3B-hero-product.jpg",
    "3C": "ref-3C-essence-vial.jpg",
    "4A": "ref-4A-catalog-layout.jpg",
    "4B": "ref-4B-flatlay.jpg",
    "5A": "ref-5A-heritage-engraving.jpg",
    "5B": "ref-5B-campaign-grid.jpg",
    "5D": "ref-5D-engine-icons.jpg",
    "7A": "ref-7A-contact-sheet.jpg",
    "8A": "ref-8A-seeker-poster.jpg",
    "9A": "ref-9A-engine-poster.jpg",
    "10A": "ref-7A-contact-sheet.jpg",
}


def load_ref_map(ref_map_path):
    """Load reference-map.json and return a REF_IMAGES dict.

    Returns dict mapping prompt_id -> filename.
    Falls back to _DEFAULT_REF_IMAGES if file not found.
    """
    if not os.path.exists(ref_map_path):
        return dict(_DEFAULT_REF_IMAGES)

    with open(ref_map_path) as f:
        data = json.load(f)

    result = {}
    for pid, entry in data.get("primary", {}).items():
        result[pid] = entry["file"]
    for pid, entry in data.get("reuses", {}).items():
        result[pid] = entry["file"]
    return result


def build_ref_images_block(ref_images_dict):
    """Build the REF_IMAGES block for embedding in generated scripts.

    Returns a template-escaped string ({{ for literal braces) suitable
    for inclusion in SCRIPT_HEADER before .format_map() rendering.
    """
    lines = ["REF_IMAGES = {{"]
    for pid in sorted(ref_images_dict.keys(), key=_sort_pid):
        lines.append(f'    "{pid}": "{ref_images_dict[pid]}",')
    lines.append("}}")
    return "\n".join(lines)


def _sort_pid(pid):
    """Sort prompt IDs numerically: 2A, 2B, ..., 10A, 10B, 10C."""
    m = re.match(r"(\d+)([A-Z]?)", pid)
    if m:
        return (int(m.group(1)), m.group(2))
    return (50, pid)


# =====================================================================
# CONFIG LOADING
# =====================================================================

def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_execution_context(config_path, cfg):
    """Load execution context from config or sidecar JSON.

    Priority: sidecar execution-context.json > config execution_context section > defaults.
    """
    defaults = {
        "budget_tier": "standard",
        "launch_channel": "dtc",
        "maturity_stage": "pre-launch",
        "depth_level": "focused",
        "tone": "",
        "quality_bar": "standard",
    }
    # Try sidecar JSON first (orchv2 writes this directly)
    sidecar = os.path.join(os.path.dirname(config_path), "execution-context.json")
    if os.path.exists(sidecar):
        with open(sidecar) as f:
            ctx = json.load(f)
        for k in defaults:
            defaults[k] = ctx.get(k, defaults[k])
    # Config section overrides sidecar for explicit values
    ec = cfg.get("execution_context", {})
    for k in defaults:
        if ec.get(k):
            defaults[k] = ec[k]
    return defaults


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# =====================================================================
# DEPTH / CHANNEL / TONE CONFIGURATION
# =====================================================================

DEPTH_CONFIG = {
    "surface":       {"seeds_count": 1, "skip_ids": {"5C", "8A", "10A", "10B", "10C"}, "quality": "4K", "detail_suffix": ""},
    "focused":       {"seeds_count": 2, "skip_ids": set(),                              "quality": "8K", "detail_suffix": ""},
    "comprehensive": {"seeds_count": 2, "skip_ids": set(),                              "quality": "8K", "detail_suffix": " Extreme attention to micro-detail: material grain, light caustics, sub-surface scattering, fiber textures."},
    "exhaustive":    {"seeds_count": 3, "skip_ids": set(),                              "quality": "8K ultra-detailed", "detail_suffix": " Extreme attention to micro-detail: material grain, light caustics, sub-surface scattering, fiber textures. Every surface tells a story of craft and intention."},
}

CHANNEL_PROFILES = {
    "kickstarter": {
        "hero_aspect": "16:9",
        "priority_assets": {"2A", "2B", "3A", "3B", "5B", "8A"},
        "platform_note": "Optimized for Kickstarter: bold hero imagery, clear product shots, campaign grid.",
    },
    "dtc": {
        "hero_aspect": "1:1",
        "priority_assets": {"2A", "2B", "3A", "3B", "3C", "4A", "4B", "5A", "7A"},
        "platform_note": "Optimized for DTC e-commerce: product-first imagery, flatlay grids, lifestyle context.",
    },
    "saas": {
        "hero_aspect": "16:9",
        "priority_assets": {"2A", "2B", "2C", "5A", "5B", "5D"},
        "platform_note": "Optimized for SaaS: brand system, iconography, and campaign visuals.",
    },
    "b2b": {
        "hero_aspect": "16:9",
        "priority_assets": {"2A", "2B", "2C", "5A", "5B", "8A"},
        "platform_note": "Optimized for B2B: professional brand system, presentation-ready assets.",
    },
}

TONE_PREAMBLES = {
    "conversion-focused": "Act as a conversion-focused Brand Designer. Every visual must stop scrolling and communicate value in 2 seconds. Create",
    "comprehensive": "Act as Lead Brand Designer creating a comprehensive, museum-quality",
    "minimal": "Act as a minimalist Brand Designer. Strip to essentials. Create",
    "premium": "Act as a luxury Brand Director with uncompromising attention to craft. Create",
    "": "Act as Lead Brand Designer creating a comprehensive",  # default
}

CHANNEL_REF_OVERRIDES = {
    "kickstarter": {},
    "dtc": {"3A": "ref-alt-leather-duffles.jpg"},
    "saas": {"2B": "ref-alt-chrome-logos.jpg"},
    "b2b": {"2B": "ref-alt-chrome-logos.jpg"},
}


def _resolve_logo_path(path_str, config_dir):
    """Resolve a logo path relative to the config directory. Returns abs path or ''."""
    if not path_str:
        return ""
    if os.path.isabs(path_str):
        return path_str if os.path.exists(path_str) else ""
    # Resolve relative to config file's directory
    if config_dir:
        resolved = os.path.join(os.path.dirname(config_dir), path_str)
    else:
        resolved = path_str
    return os.path.abspath(resolved) if os.path.exists(resolved) else ""


def build_vars(cfg, exec_ctx=None, config_path=None):
    """Flatten config into a dict of template variables."""
    b = cfg["brand"]
    t = cfg["theme"]
    p = cfg["palette"]
    ty = cfg["typography"]
    ec = exec_ctx or {}

    # Competitive context — append avoid patterns to negative prompt
    cc = cfg.get("competitive_context", {})
    neg = cfg.get("negative_prompt", "")
    avoid_patterns = cc.get("avoid_visual_patterns", "")
    if avoid_patterns:
        neg = neg.rstrip().rstrip(",") + ",\n  " + avoid_patterns

    # Audience
    aud = cfg.get("audience", {})

    # Positioning
    pos = cfg.get("positioning", {})
    pillars = pos.get("identity_pillars", [])

    # Tone preamble
    tone = ec.get("tone", "")
    tone_preamble = TONE_PREAMBLES.get(tone, TONE_PREAMBLES[""])

    # Typography extended fields
    header_display_weight = ty["header"].get("display_weight", "Light")
    header_emphasis_weight = ty["header"].get("emphasis_weight", "SemiBold")
    header_case = ty["header"].get("case", "all caps")

    # Color role directive
    color_directive = (
        f"{p['primary']['name']} 60% backgrounds. "
        f"{p['secondary']['name']} 30% text/surfaces. "
        f"{p['accent']['name']} 10% highlights ONLY."
    )

    # Channel
    channel = ec.get("launch_channel", "dtc")
    channel_profile = CHANNEL_PROFILES.get(channel, CHANNEL_PROFILES["dtc"])
    platform_note = channel_profile.get("platform_note", "")

    # Depth
    depth = ec.get("depth_level", "focused")
    depth_cfg = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["focused"])
    detail_suffix = depth_cfg.get("detail_suffix", "")

    v = {
        "brand_name": b["name"],
        "brand_tagline": b.get("tagline", ""),
        "archetype": b.get("archetype", "creator"),
        "voice": b.get("voice", "precise"),
        "domain": b.get("domain", "technology"),
        "theme_name": t["name"],
        "theme_description": t["description"],
        "theme_metaphor": t.get("metaphor", ""),
        "mood_keywords": ", ".join(t.get("mood_keywords", [])),
        # Colors
        "primary_name": p["primary"]["name"],
        "primary_hex": p["primary"]["hex"],
        "primary_role": p["primary"].get("role", ""),
        "secondary_name": p["secondary"]["name"],
        "secondary_hex": p["secondary"]["hex"],
        "secondary_role": p["secondary"].get("role", ""),
        "accent_name": p["accent"]["name"],
        "accent_hex": p["accent"]["hex"],
        "accent_role": p["accent"].get("role", ""),
        "support_name": p["support"]["name"],
        "support_hex": p["support"]["hex"],
        "support_role": p["support"].get("role", ""),
        "signal_name": p["signal"]["name"],
        "signal_hex": p["signal"]["hex"],
        "signal_role": p["signal"].get("role", ""),
        "color_directive": color_directive,
        # Typography
        "header_font": ty["header"]["font"],
        "body_font": ty["body"]["font"],
        "data_font": ty["data"]["font"],
        "header_display_weight": header_display_weight,
        "header_emphasis_weight": header_emphasis_weight,
        "header_case": header_case,
        # Materials
        "materials_list": ", ".join(cfg.get("materials", [])),
        # Photography
        "photo_style": cfg.get("photography", {}).get("style", ""),
        "photo_environment": cfg.get("photography", {}).get("environment", ""),
        "photo_constraint": cfg.get("photography", {}).get("constraint", ""),
        "photo_camera": cfg.get("photography", {}).get("camera", ""),
        # Illustration
        "illus_style": cfg.get("illustration", {}).get("style", ""),
        "illus_references": cfg.get("illustration", {}).get("references", ""),
        # Negative prompt (with competitive avoidance appended)
        "negative_prompt": neg,
        # Sigil
        "sigil_description": cfg.get("sigil", {}).get("description", ""),
        "sigil_components": ", ".join(cfg.get("sigil", {}).get("components", [])),
        # Execution context
        "budget_tier": ec.get("budget_tier", "standard"),
        "launch_channel": channel,
        "maturity_stage": ec.get("maturity_stage", "pre-launch"),
        "depth_level": depth,
        "tone": tone,
        "quality_bar": ec.get("quality_bar", "standard"),
        "tone_preamble": tone_preamble,
        "quality": depth_cfg.get("quality", "8K"),
        "detail_suffix": detail_suffix,
        "platform_note": platform_note,
        # Audience
        "persona_name": aud.get("persona_name", ""),
        "audience_aesthetic": aud.get("aesthetic_affinity", ""),
        "audience_aspiration": aud.get("aspirational_brands", ""),
        "emotional_register": aud.get("emotional_register", ""),
        # Competitive context
        "occupy_territory": cc.get("occupy_territory", ""),
        "differentiate_from": cc.get("differentiate_from", ""),
        # Positioning
        "positioning_statement": pos.get("statement", ""),
        "hero_headline": pos.get("hero_headline", ""),
        "identity_pillars": ", ".join(pillars) if pillars else "",
    }

    # ── Products (with safe fallbacks to original defaults) ──
    prods = cfg.get("products", {})
    hero = prods.get("hero", {})
    v["product_hero_name"] = hero.get("name", "guidebook")
    v["product_hero_description"] = hero.get("description", "comprehensive practice manual")
    v["product_hero_physical"] = hero.get("physical_form",
        f"hardcover codex with custom spine in {v['accent_name']} ({v['accent_hex']}) material, "
        f"pages made of fine craft paper, geometric diagrams visible on open pages in {v['data_font']}")

    capsule = prods.get("capsule_lineup", [])
    if len(capsule) >= 3:
        v["product_capsule_1"] = capsule[0].get("description", "primary product")
        v["product_capsule_2"] = capsule[1].get("description", "companion piece")
        v["product_capsule_3"] = capsule[2].get("description", "symbolic artifact")
    elif len(capsule) >= 1:
        descs = [c.get("description", "brand product") for c in capsule]
        while len(descs) < 3:
            descs.append("brand artifact")
        v["product_capsule_1"], v["product_capsule_2"], v["product_capsule_3"] = descs
    else:
        v["product_capsule_1"] = "bio-digital notebook with custom spine"
        v["product_capsule_2"] = "small glass vessel"
        v["product_capsule_3"] = "symbolic craft object"

    essence = prods.get("essence", {})
    v["product_essence_name"] = essence.get("name", "essence")
    v["product_essence_container"] = essence.get("container",
        "Small borosilicate glass bottle with oxidized metal dropper cap")
    v["product_essence_size"] = essence.get("size", "30ml")

    flatlay = prods.get("flatlay_objects", {})
    v["product_flatlay_count"] = str(flatlay.get("count", 5))
    flatlay_items = flatlay.get("items", [])
    v["product_flatlay_description"] = ", ".join(flatlay_items) if flatlay_items else "brand objects"

    v["product_category"] = prods.get("category", "lifestyle product")

    # ── Aesthetic language overrides (backward-compatible defaults) ──
    aes = cfg.get("aesthetic", {})
    v["hero_object_type"] = aes.get("hero_object_type", "bio-digital object")
    v["hero_surface"] = aes.get("hero_surface", "polished surface")
    v["seal_material"] = aes.get("seal_material", "Oxidized copper")
    v["seal_geometry"] = aes.get("seal_geometry", "Art Deco geometric precision")
    v["logo_treatment"] = aes.get("logo_treatment", "stained-glass")
    v["logo_substrate"] = aes.get("logo_substrate", "stained-glass window panel")
    v["panel_structure"] = aes.get("panel_structure",
        "Bio-digital structure elements with fiber-optic filaments")
    v["icon_line_style"] = aes.get("icon_line_style",
        "Flowing organic curves with circuit-trace precision")
    v["poster_artifact"] = aes.get("poster_artifact", "bio-digital artifact")
    v["poster_filament"] = aes.get("poster_filament", "fiber-optic filaments")
    v["poster_border"] = aes.get("poster_border", "Art Deco geometric border frame")
    v["quality_reference"] = aes.get("quality_reference", "Behance Trend / Awwwards Winner")
    v["engraving_style"] = aes.get("engraving_style", "heritage engraving")
    v["seeker_inner_detail"] = aes.get("seeker_inner_detail",
        "circuit-trace diagrams, fiber-optic filaments")
    v["sequence_type"] = aes.get("sequence_type", "sequential practice narrative")
    v["sequence_constraint"] = aes.get("sequence_constraint", "hands-only")

    # ── Logo file paths (Phase 2) ──
    logo_cfg = cfg.get("logo_files", {})
    config_dir = config_path if config_path else ""
    v["logo_primary_path"] = _resolve_logo_path(logo_cfg.get("primary", ""), config_dir)
    v["logo_icon_path"] = _resolve_logo_path(logo_cfg.get("icon", ""), config_dir)
    v["has_logo_files"] = "true" if v["logo_primary_path"] else ""

    # ── Product reference images (Phase 4 — actual product photos for model accuracy) ──
    prod_refs = cfg.get("generation", {}).get("product_reference_images", [])
    resolved_refs = []
    for ref_path in prod_refs[:3]:  # Cap at 3 images
        if os.path.isabs(ref_path):
            resolved = ref_path
        elif config_path:
            resolved = os.path.join(os.path.dirname(config_path), ref_path)
        else:
            resolved = ref_path
        if os.path.exists(resolved):
            resolved_refs.append(resolved)
        else:
            print(f"  WARNING: Product ref not found: {ref_path}")
    v["product_reference_images"] = resolved_refs

    # ── Domain tags (Phase 3) ──
    v["domain_tags"] = cfg.get("brand", {}).get("domain_tags", [])

    # ── Extended prompts (Phase 3 — domain-specific assets) ──
    v["extended_prompts"] = cfg.get("prompts", {}).get("extended", {})

    # ── Provider configuration ──
    gen = cfg.get("generation", {})
    v["provider"] = gen.get("provider", os.environ.get("IMAGE_PROVIDER", "fal"))

    return v


def render(template, v):
    """Safe .format() — missing keys become {key_name}."""
    class SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"
    return template.format_map(SafeDict(v))


# =====================================================================
# SCRIPT HEADER / FUNCTION TEMPLATES
# =====================================================================

SCRIPT_HEADER = '''#!/usr/bin/env python3
"""
{brand_name} — {script_desc}
Generated by Brandmint pipeline engine.

Provider: {provider}
"""
import os, sys, subprocess, requests
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.claude/.env"))

BRAND_NAME = "{brand_name}"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "{output_subdir}")
os.makedirs(OUT_DIR, exist_ok=True)

# Skill reference images directory (composition references for Nano Banana Pro)
SKILL_REF_DIR = os.path.expanduser("~/.claude/skills/brandmint/references/images")

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================
# Supports: fal (default), openrouter, openai, replicate
# Set IMAGE_PROVIDER env var or use --provider CLI flag

PROVIDER = os.environ.get("IMAGE_PROVIDER", "{provider}").lower()

# Provider-specific imports and setup
if PROVIDER == "fal":
    try:
        import fal_client
        if not os.environ.get("FAL_KEY"):
            print("ERROR: Set FAL_KEY in ~/.claude/.env")
            sys.exit(1)
    except ImportError:
        print("ERROR: fal_client required for FAL provider. Install: pip install fal-client")
        sys.exit(1)
elif PROVIDER == "openrouter":
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("ERROR: Set OPENROUTER_API_KEY in ~/.claude/.env")
        sys.exit(1)
elif PROVIDER == "openai":
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY in ~/.claude/.env")
        sys.exit(1)
elif PROVIDER == "replicate":
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("ERROR: Set REPLICATE_API_TOKEN in ~/.claude/.env")
        sys.exit(1)
else:
    # Default to FAL for backward compatibility
    PROVIDER = "fal"
    try:
        import fal_client
        if not os.environ.get("FAL_KEY"):
            print("ERROR: Set FAL_KEY in ~/.claude/.env")
            sys.exit(1)
    except ImportError:
        print("ERROR: fal_client required. Install: pip install fal-client")
        sys.exit(1)

print(f"Using image provider: {{PROVIDER.upper()}}")

NEGATIVE = """{negative_prompt}"""

# Brand logo file (for visual reference injection — empty if no logo configured)
LOGO_PATH = "{logo_primary_path}"

_logo_url_cache = None
def get_logo_url():
    """Upload brand logo once and cache the URL for reuse."""
    global _logo_url_cache
    if _logo_url_cache:
        return _logo_url_cache
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        print(f"  Uploading brand logo: {{os.path.basename(LOGO_PATH)}}")
        if PROVIDER == "fal":
            _logo_url_cache = fal_client.upload_file(LOGO_PATH)
        else:
            # For non-FAL providers, return local path (they may not support image refs)
            _logo_url_cache = LOGO_PATH
        return _logo_url_cache
    return None


# Product reference images (actual product photos for Nano Banana Pro accuracy)
PRODUCT_REF_PATHS = {product_ref_paths_literal}

_product_ref_url_cache = None
def get_product_ref_urls():
    """Upload product reference images once and cache URLs for reuse."""
    global _product_ref_url_cache
    if _product_ref_url_cache is not None:
        return _product_ref_url_cache
    _product_ref_url_cache = []
    for p in PRODUCT_REF_PATHS:
        if os.path.exists(p):
            print(f"  Uploading product ref: {{os.path.basename(p)}}")
            if PROVIDER == "fal":
                _product_ref_url_cache.append(fal_client.upload_file(p))
            else:
                _product_ref_url_cache.append(p)
    return _product_ref_url_cache


# Reference image mapping: prompt ID -> composition reference filename
{ref_images_block}

# Config-driven reference image overrides
REF_OVERRIDES = {ref_overrides_literal}
REF_IMAGES.update(REF_OVERRIDES)


def get_ref_image(pid):
    """Get composition reference image path for a prompt ID."""
    fname = REF_IMAGES.get(pid, "")
    if fname:
        path = os.path.join(SKILL_REF_DIR, fname)
        if os.path.exists(path):
            return path
    return None


def download_image(url, filepath):
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(resp.content)
    # Auto-convert JPEG-as-PNG: Flux 2 Pro returns JPEG but pipeline names files .png
    if filepath.endswith(".png"):
        with open(filepath, "rb") as f:
            header = f.read(4)
        if header[:2] == b"\\xff\\xd8":  # JPEG magic bytes
            import subprocess
            subprocess.run(["sips", "-s", "format", "png", filepath, "--out", filepath],
                         capture_output=True, check=True)
            print(f"  Converted JPEG -> PNG: {{os.path.getsize(filepath) // 1024}} KB")
    size_kb = os.path.getsize(filepath) / 1024
    print(f"  Saved: {{os.path.basename(filepath)}} ({{size_kb:.0f}} KB)")


# =============================================================================
# PROVIDER-AWARE GENERATION FUNCTIONS
# =============================================================================

def gen_with_openrouter(prompt, model, output_path, width=1024, height=1024, **kwargs):
    """Generate image using OpenRouter API."""
    import json
    import urllib.request
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_map = {{
        "nano-banana": "black-forest-labs/flux-1.1-pro",
        "flux-2-pro": "black-forest-labs/flux-1.1-pro",
        "recraft": "stabilityai/stable-diffusion-xl-base-1.0",
    }}
    model_id = model_map.get(model, "black-forest-labs/flux-1.1-pro")
    
    payload = {{"model": model_id, "prompt": prompt, "n": 1, "size": f"{{width}}x{{height}}"}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/images/generations",
        data=data,
        headers={{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "data" in result and result["data"]:
        download_image(result["data"][0]["url"], output_path)
        return True
    return False


def gen_with_openai(prompt, model, output_path, width=1024, height=1024, **kwargs):
    """Generate image using OpenAI DALL-E API."""
    import json
    import urllib.request
    
    api_key = os.environ.get("OPENAI_API_KEY")
    # DALL-E 3 has fixed sizes
    if width > height:
        size = "1792x1024"
    elif height > width:
        size = "1024x1792"
    else:
        size = "1024x1024"
    
    payload = {{"model": "dall-e-3", "prompt": prompt, "n": 1, "size": size, "quality": "hd"}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=data,
        headers={{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if "data" in result and result["data"]:
        download_image(result["data"][0]["url"], output_path)
        return True
    return False


def gen_with_replicate(prompt, model, output_path, width=1024, height=1024, **kwargs):
    """Generate image using Replicate API."""
    import json
    import time
    import urllib.request
    
    api_key = os.environ.get("REPLICATE_API_TOKEN")
    model_map = {{
        "nano-banana": "black-forest-labs/flux-1.1-pro",
        "flux-2-pro": "black-forest-labs/flux-1.1-pro",
        "recraft": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    }}
    model_id = model_map.get(model, "black-forest-labs/flux-1.1-pro")
    
    # Create prediction
    payload = {{"input": {{"prompt": prompt, "width": width, "height": height}}}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.replicate.com/v1/models/{{model_id}}/predictions",
        data=data,
        headers={{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        pred = json.loads(resp.read().decode("utf-8"))
    
    # Poll for completion
    pred_id = pred.get("id")
    for _ in range(60):
        time.sleep(5)
        req = urllib.request.Request(
            f"https://api.replicate.com/v1/predictions/{{pred_id}}",
            headers={{"Authorization": f"Bearer {{api_key}}"}},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("status") == "succeeded":
            output = result.get("output")
            url = output[0] if isinstance(output, list) else output
            download_image(url, output_path)
            return True
        if result.get("status") in ("failed", "canceled"):
            return False
    return False

'''

FUNC_NANO_BANANA = '''
def gen_nano_banana(pid, slug, prompt, aspect, image_urls, seeds=({seed_a}, {seed_b})):
    """Generate with Nano Banana Pro + style anchor (or equivalent on other providers)."""
    full_prompt = f"{{prompt}}\\n\\nAvoid: {{NEGATIVE}}"
    
    # Parse aspect ratio to get dimensions
    aspect_dims = {{"16:9": (1792, 1024), "9:16": (1024, 1792), "1:1": (1024, 1024), 
                   "3:4": (896, 1152), "4:3": (1152, 896)}}
    w, h = aspect_dims.get(aspect, (1024, 1024))
    
    for seed in seeds:
        variant = "v1" if seed == {seed_a} else f"v{{seed}}"
        out_path = os.path.join(OUT_DIR, f"{{pid}}-{{slug}}-nanobananapro-{{variant}}.png")
        print(f"\\n  [{{pid}}] Nano Banana Pro seed={{seed}} (provider: {{PROVIDER}})...")
        
        if PROVIDER == "fal":
            result = fal_client.subscribe(
                "fal-ai/nano-banana-pro",
                arguments={{
                    "prompt": full_prompt,
                    "image_urls": image_urls,
                    "aspect_ratio": aspect,
                    "resolution": "2K",
                    "output_format": "png",
                    "seed": seed,
                    "num_images": 1,
                }},
            )
            download_image(result["images"][0]["url"], out_path)
        elif PROVIDER == "openrouter":
            gen_with_openrouter(full_prompt, "nano-banana", out_path, w, h)
        elif PROVIDER == "openai":
            gen_with_openai(full_prompt, "nano-banana", out_path, w, h)
        elif PROVIDER == "replicate":
            gen_with_replicate(full_prompt, "nano-banana", out_path, w, h)

'''

FUNC_FLUX_PRO = '''
def gen_flux_pro(pid, slug, prompt, aspect, seeds=({seed_a}, {seed_b})):
    """Generate with Flux 2 Pro (or equivalent on other providers)."""
    full_prompt = f"{{prompt}}\\n\\nAvoid: {{NEGATIVE}}"
    
    # Parse aspect to dimensions
    aspect_dims = {{"landscape_16_9": (1792, 1024), "portrait_9_16": (1024, 1792), 
                   "square": (1024, 1024), "portrait_3_4": (896, 1152), "landscape_4_3": (1152, 896)}}
    w, h = aspect_dims.get(aspect, (1024, 1024))
    
    for seed in seeds:
        variant = "v1" if seed == {seed_a} else f"v{{seed}}"
        out_path = os.path.join(OUT_DIR, f"{{pid}}-{{slug}}-flux2pro-{{variant}}.png")
        print(f"\\n  [{{pid}}] Flux 2 Pro seed={{seed}} (provider: {{PROVIDER}})...")
        
        if PROVIDER == "fal":
            result = fal_client.subscribe(
                "fal-ai/flux-2-pro",
                arguments={{
                    "prompt": full_prompt,
                    "image_size": aspect,
                    "num_images": 1,
                    "seed": seed,
                }},
            )
            download_image(result["images"][0]["url"], out_path)
        elif PROVIDER == "openrouter":
            gen_with_openrouter(full_prompt, "flux-2-pro", out_path, w, h)
        elif PROVIDER == "openai":
            gen_with_openai(full_prompt, "flux-2-pro", out_path, w, h)
        elif PROVIDER == "replicate":
            gen_with_replicate(full_prompt, "flux-2-pro", out_path, w, h)

'''

FUNC_RECRAFT = '''
def gen_recraft(pid, slug, prompt, style, colors, size, seeds=({seed_a}, {seed_b})):
    """Generate with Recraft V3 (or SDXL equivalent on other providers)."""
    # Parse size to dimensions for non-FAL providers
    size_dims = {{"square": (1024, 1024), "landscape_16_9": (1792, 1024), 
                 "portrait_9_16": (1024, 1792), "1024x1024": (1024, 1024)}}
    w, h = size_dims.get(size, (1024, 1024))
    
    for seed in seeds:
        variant = "v1" if seed == {seed_a} else f"v{{seed}}"
        base_name = f"{{pid}}-{{slug}}-recraft-{{variant}}"
        print(f"\\n  [{{pid}}] Recraft V3 ({{style}}) seed={{seed}} (provider: {{PROVIDER}})...")
        
        if PROVIDER == "fal":
            print(f"  Prompt length: {{len(prompt)}} chars")
            args = {{
                "prompt": prompt,
                "image_size": size,
                "style": style,
                "seed": seed,
            }}
            if colors:
                args["colors"] = [{{"rgb": c}} for c in colors]
            result = fal_client.subscribe(
                "fal-ai/recraft/v3/text-to-image",
                arguments=args,
            )
            img_url = result["images"][0]["url"]
            is_svg = img_url.endswith(".svg") or "vector" in style
            if is_svg:
                native_path = os.path.join(OUT_DIR, f"{{base_name}}.svg")
                download_image(img_url, native_path)
                png_path = os.path.join(OUT_DIR, f"{{base_name}}.png")
                try:
                    subprocess.run(
                        ["rsvg-convert", "-w", "2048", "-h", "2048",
                         "--keep-aspect-ratio", native_path, "-o", png_path],
                        check=True, capture_output=True,
                    )
                    sz = os.path.getsize(png_path) / 1024
                    print(f"  Converted SVG -> PNG: {{sz:.0f}} KB")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"  WARNING: SVG->PNG failed: {{e}}")
            else:
                native_path = os.path.join(OUT_DIR, f"{{base_name}}.webp")
                download_image(img_url, native_path)
                png_path = os.path.join(OUT_DIR, f"{{base_name}}.png")
                try:
                    subprocess.run(
                        ["sips", "-s", "format", "png", native_path, "--out", png_path],
                        check=True, capture_output=True,
                    )
                    sz = os.path.getsize(png_path) / 1024
                    print(f"  Converted WebP -> PNG: {{sz:.0f}} KB")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"  WARNING: WebP->PNG failed: {{e}}")
        else:
            # Non-FAL providers: use SDXL or equivalent (no SVG support)
            out_path = os.path.join(OUT_DIR, f"{{base_name}}.png")
            enhanced_prompt = f"{{prompt}}. Style: {{style}}. Fine line art, detailed illustration."
            if PROVIDER == "openrouter":
                gen_with_openrouter(enhanced_prompt, "recraft", out_path, w, h)
            elif PROVIDER == "openai":
                gen_with_openai(enhanced_prompt, "recraft", out_path, w, h)
            elif PROVIDER == "replicate":
                gen_with_replicate(enhanced_prompt, "recraft", out_path, w, h)

'''


# =====================================================================
# PROMPT TEMPLATES (parameterized with {variables})
# =====================================================================

PROMPT_2A_BENTO = """{brand_name} ({domain}).
{tone_preamble} "Brand Identity System" presentation (Bento-Grid Layout).
Core metaphor: {theme_metaphor}. Mood: {mood_keywords}.

Generate a single high-resolution bento-grid board containing 6 distinct modules:

PHASE 1: VISUAL STRATEGY
1. Analyze the Brand: Archetype = "{archetype}" -- {voice}.
   Visual vibe = {theme_name}, {theme_description}.
   Visual territory: {occupy_territory}.
2. Define the Palette: {color_directive}
   {primary_name} {primary_hex}, {secondary_name} {secondary_hex},
   {accent_name} {accent_hex}, {support_name} {support_hex}.
3. Select Typography: {header_font} (headers, {header_display_weight}/{header_emphasis_weight}, {header_case}). {body_font} (body).

PHASE 2: THE LAYOUT (6-MODULE GRID)
Block 1 (The Hero): High-contrast photograph of a {product_hero_physical} resting on
{hero_surface} inside {photo_environment}. Warm {accent_name} light.
Materials: {materials_list}. Overlay "{brand_name}" wordmark in
{secondary_name} ({secondary_hex}), {header_font} {header_display_weight}, {header_case}.
Block 2 (Social Media): Instagram Post mockup -- {primary_name} ({primary_hex})
background with subtle pattern overlay at 5% opacity, centered text in {header_font}:
"{hero_headline}" {accent_name} accent line below.
Block 3 (The Palette): 5 Vertical Color Swatches -- {primary_hex}, {secondary_hex},
{accent_hex}, {support_hex}, {signal_hex}. Simulated HEX codes.
Block 4 (Typography Spec): "{header_font}" displayed prominently. Tiny "Primary
Typeface" subtext in {body_font}.
Block 5 (The Sigil): {sigil_description}. {sigil_components}.
Block 6 (Brand DNA): Manifesto Card -- ARCHETYPE: "{archetype}."
VOICE: "{voice}." POSITIONING: "{positioning_statement}."
PILLARS: {identity_pillars}. VISUALS: "{theme_description}."

PHASE 3: AESTHETIC & FINISH
Style: {quality_reference}. Quality: {quality}. {detail_suffix}
Soft studio lighting with {accent_name} rim accent. Sharp edges, 1px {support_name}
borders. Generous white space. {platform_note}"""

PROMPT_2B_SEAL = """{brand_name} brand seal emblem. {seal_material} circular seal
with {seal_geometry}. Central sigil: {sigil_description}.
Typography: "{brand_name}" around perimeter in {header_font} {header_display_weight}, {header_case}.
Below sigil: "{brand_tagline}" in {body_font}. Material: {seal_material} with
{accent_name} ({accent_hex}) patina highlights. Background: solid {primary_name}
({primary_hex}). {color_directive} Clean, architectural, precision-engineered. {quality} detail.{detail_suffix}"""

PROMPT_2C_LOGO = """{brand_name} {logo_treatment} logo emboss. The brand sigil
({sigil_description}) rendered as a {logo_substrate} with
{accent_name} ({accent_hex}) leading between colored glass segments.
Colors: {primary_hex}, {accent_hex}, {signal_hex}. Backlit with warm diffused
light creating colored shadows on {secondary_name} ({secondary_hex}) surface below.
"{brand_name}" wordmark in {header_font} SemiBold below. 8K detail."""

PROMPT_3A_CAPSULE = """{brand_name} capsule collection product lineup.
Three products in a row on {hero_surface}: {product_capsule_1},
{product_capsule_2}, and {product_capsule_3}.
Materials: {materials_list}. Environment: {photo_environment}.
{photo_style}. {photo_constraint}. Camera: {photo_camera}. {quality} detail.
Color palette: {color_directive} {primary_hex} deep shadows, {secondary_hex} highlights,
{accent_hex} reflections, {signal_hex} living accents.
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}.{detail_suffix}"""

PROMPT_3B_BOOK = """{brand_name} hero product shot. {product_hero_physical}.
Sitting on {hero_surface}. {photo_style}. Environment: {photo_environment}.
{photo_constraint}. Camera: {photo_camera}. Materials: {materials_list}. 8K."""

PROMPT_3C_VIAL = """{brand_name} {product_essence_name} product shot. {product_essence_container}
({product_essence_size}). Etched label directly into surface in {data_font}.
Brand name "{brand_name}" etched dominant. Minimal sigil below. Pure solid
{primary_name} ({primary_hex}) background. Sharp high-contrast lighting from above.
{accent_name} highlight, {secondary_name} edge-glow.
{photo_constraint}. 8K."""

PROMPT_4A_CATALOG = """{brand_name} product design catalog page. Top section:
{product_category} image inside {photo_environment}. {accent_name} ({accent_hex})
light filtering through. Bottom section: technical specification panel with
architectural line drawings in {accent_name} on {primary_name} background.
Fine hairline technical lines with measurement callouts in {data_font}.
Material swatches panel: {materials_list}. {photo_style}. {color_directive}
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}. {quality}.{detail_suffix}"""

PROMPT_4B_FLATLAY = """{brand_name} product collection flat-lay. {product_flatlay_count} objects
arranged on {hero_surface} in precise architectural spacing: {product_flatlay_description}. Materials:
{materials_list}. Overhead composition. Each object casting a single sharp shadow.
Lighting: directional from upper left with warm {accent_name} ({accent_hex})
temperature. Cool {secondary_name} ({secondary_hex}) fill from below.
{photo_constraint}. {photo_style}. {color_directive}
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}. {quality} quality.{detail_suffix}"""

PROMPT_5A_HERITAGE = """{brand_name} {engraving_style} logomark. {illus_style}.
Thin delicate hairlines in organic curves. Airy, precise, no heavy borders.
Central sigil: {sigil_description}. {sigil_components}. Rendered as
botanical-scientific diagram. "{brand_name}" in geometric serif ({header_font}
style), wide spacing. Below: "EST. MMXXVI" lighter weight. {secondary_name}
({secondary_hex}) paper. {primary_name} ({primary_hex}) lines. {accent_name}
({accent_hex}) accent on borders."""

PROMPT_5B_CAMPAIGN = """{brand_name} Campaign Visual Identity Grid. 2-column
asymmetrical layout. Full bleed, zero spacing between tiles.
Core metaphor: {theme_metaphor}. Visual territory: {occupy_territory}.
TYPE A: Solid {primary_name} ({primary_hex}) background with pattern at 5% opacity,
centered sigil in {secondary_name} ({secondary_hex}).
TYPE B: {accent_name} ({accent_hex}) background, "{brand_tagline}" in {header_font}
{header_emphasis_weight}, {secondary_name} text.
TYPE C: High-contrast duotone photographs using {primary_hex} + {accent_hex}.
Materials: {materials_list}. {photo_constraint}. Typography: {header_font} ONLY.
{color_directive} Every photo unique. {illus_style}.{detail_suffix}"""

PROMPT_5C_PANEL = """{brand_name} conceptual panel illustration. {illus_style}.
{illus_references}. Core metaphor: {theme_metaphor}. Mood: {mood_keywords}.
Flowing organic lines, flat color planes in {primary_name}
({primary_hex}), {accent_name} ({accent_hex}), and {signal_name} ({signal_hex}).
{color_directive} Decorative border of flowing curves and organic tendrils. Grounded figure on
{hero_surface}. {panel_structure}
glowing {secondary_name}. No mystical imagery. Paper texture: warm, fibrous."""

PROMPT_5D_ICONS = """{count} minimalist styled flat vector icons for {brand_name}
"{group_name}" in {layout} layout. {icon_line_style}. Only {primary_name} ({primary_hex}) and {secondary_name} ({secondary_hex}).
No shading, no gradients. Icons: {icon_list}. {secondary_name} background.
Square frames with decorative corner accents. {data_font} labels."""

PROMPT_5D_ICONS_FLUX = """{count} clean, modern feature icons for {brand_name} "{group_name}".
Arranged in a {layout} grid on clean {secondary_name} ({secondary_hex}) background.
Style: {icon_line_style}. Professional iconography, no cartoon elements.
Each icon is a distinct, recognizable pictogram with consistent stroke weight.
Primary: {primary_name} ({primary_hex}). Accent: {accent_name} ({accent_hex}).
No text labels. No newspaper or stamp aesthetic. Clean minimalist precision.
Icons: {icon_list}. {quality}."""

PROMPT_7A_CONTACT = """{brand_name} editorial contact sheet. 3x3 grid, 9 panels,
hands-only lifestyle photography inside {photo_environment}. No face -- only hands
and forearms. Same hands all panels. 9 panels showing different moments of a
practice ritual with brand objects. Materials: {materials_list}.
Camera: {photo_camera}. {photo_environment} light. {accent_name} ({accent_hex})
highlights. 2px {support_name} ({support_hex}) borders. {quality} detail.
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}.{detail_suffix}"""

PROMPT_8A_SEEKER = """{brand_name} "The Seeker" conceptual portrait poster.
Core metaphor: {theme_metaphor}.
A solitary figure seen from behind -- standing still, contemplative posture.
No face visible. Full body, centered in frame.
SPLIT COMPOSITION: LEFT HALF shows material reality -- ultra-photorealistic detail:
hand texture, fabric weave, polished floor, {photo_environment} visible behind.
RIGHT HALF shows inner architecture -- translucent technical blueprint revealing:
{seeker_inner_detail} glowing {secondary_name} ({secondary_hex}),
engineering nodes at key body points, network patterns from feet.
The split line glows {accent_name} ({accent_hex}).
COLOR: {color_directive} {primary_name} dominant, {accent_name} highlights, {secondary_name} inner glow,
{signal_name} ({signal_hex}) for living elements. Film grain.
Typography: "THE SEEKER" in {header_font} {header_display_weight}, {support_name} ({support_hex}).
Audience aesthetic: {audience_aesthetic}. Emotional register: {emotional_register}.{detail_suffix}"""

PROMPT_9A_ENGINE = """{brand_name} campaign poster. Single {{object}} centered on
{{bg_color}} ({{bg_hex}}) background. The object rendered as physical {poster_artifact}
artifact -- part {{material_a}}, part {{material_b}}, with {poster_filament}
glowing {secondary_name} ({secondary_hex}). {poster_border} in
{accent_name} ({accent_hex}). Typography bottom third: "{{engine_name}}" in
{header_font} Bold, all caps, {secondary_name} ({secondary_hex}).
Below: "{{tagline}}" in {header_font} Light, {support_name} ({support_hex}).
Bottom: "{brand_name}" in {body_font} Regular. Dramatic top-down spotlight. 8K."""

PROMPT_10_SEQUENCE = """{brand_name} "{{sequence_title}}" {sequence_type}.
3x3 grid of 9 panels showing {sequence_constraint} progression.
No face -- only hands and forearms. Same hands across all 9 panels.
Environment: {photo_environment}. Materials: {materials_list}.
9 PANELS: {{panel_descriptions}}
Camera: {photo_camera}. {accent_name} ({accent_hex}) highlights,
{primary_name} ({primary_hex}) deep shadows. 2px {support_name} borders. 8K."""


# =====================================================================
# PHASE 3: DEFAULT PROMPT TEMPLATES FOR DOMAIN-SPECIFIC ASSETS
# (Used when brand config doesn't provide custom prompts.extended)
# =====================================================================

DEFAULT_EXTENDED_PROMPTS = {
    "app_icon": """{brand_name} app icon. Minimalist design on solid {primary_name} ({primary_hex}) background.
Central mark: simplified version of brand sigil ({sigil_description}).
{icon_line_style}. Rounded corners, clean modern design, no text.
{accent_name} ({accent_hex}) highlight accents. {quality} quality.""",

    "og_image": """{brand_name} Open Graph social sharing preview. 1200x630 composition.
PRODUCT: {product_hero_name} -- {product_hero_physical}.
The product must match the reference photos exactly. Do NOT substitute with any other device.
"{brand_tagline}" headline in {header_font} {header_emphasis_weight},
{secondary_name} ({secondary_hex}) text on {primary_name} ({primary_hex}) overlay.
Brand mark bottom-right: {sigil_description}.
{color_directive} Cinematic, shareable, attention-grabbing. {quality}.""",

    "ig_story": """{brand_name} Instagram Story template. Vertical 9:16 composition.
{primary_name} ({primary_hex}) background with subtle material texture.
{accent_name} ({accent_hex}) border frame. {poster_border}. Content area
centered with space for text overlay. Bottom watermark: {sigil_description}.
{header_font} typography. {mood_keywords}. Premium social media design. {quality}.""",

    "app_screenshot": """{brand_name} App Store screenshot. Mobile phone frame showing
brand-themed UI with {primary_name} ({primary_hex}) background,
{accent_name} ({accent_hex}) CTA buttons, {secondary_name} ({secondary_hex}) text.
{header_font} typography. Clean modern mobile interface design.
Product context: {product_hero_name}. {icon_line_style}. {quality}.""",

    "pitch_hero": """{brand_name} pitch deck hero slide. 16:9 landscape composition.
PRODUCT: {product_hero_name} -- {product_hero_physical}.
The product must match the reference photos exactly. Do NOT substitute with any other device.
"{hero_headline}" in {header_font} {header_display_weight}, {header_case},
{secondary_name} ({secondary_hex}) text. {primary_name} ({primary_hex}) background.
{color_directive} Presentation-quality, cinematic. {quality}.""",

    "twitter_header": """{brand_name} Twitter/X header banner. 1500x500 panoramic.
PRODUCT: {product_hero_name} -- {product_hero_physical}.
The product must match the reference photos exactly. Do NOT substitute with any other device.
"{brand_tagline}" in {header_font} {header_emphasis_weight}.
Brand mark right-aligned: {sigil_description}.
{color_directive} {primary_name} overlay gradient. Cinematic. {quality}.""",

    "email_hero": """{brand_name} email header hero image. 600px wide landscape composition.
PRODUCT: {product_hero_name} -- {product_hero_physical}.
The product must match the reference photos exactly. Do NOT substitute with any other device.
Warm {accent_name} ({accent_hex}) lighting. {primary_name} ({primary_hex}) tonal background.
Brand mark: {sigil_description}. Materials: {materials_list}. Clean, inviting. {quality}.""",
}


# =====================================================================
# SCRIPT GENERATORS
# =====================================================================

def write_script(path, content):
    with open(path, "w") as f:
        f.write(content)
    print(f"  Generated: {os.path.basename(path)}")


def _get_asset_ids(asset_groups, generator_name, legacy_ids):
    """Get asset IDs for a generator. Returns legacy_ids if not in registry mode."""
    if asset_groups is None:
        return legacy_ids
    group = asset_groups.get(generator_name, [])
    return {aid for aid, _ in group}


def _flux_to_nb_aspect(aspect):
    """Convert Flux 2 Pro aspect names to Nano Banana Pro ratio format."""
    mapping = {
        "landscape_16_9": "16:9",
        "landscape_4_3": "4:3",
        "portrait_hd": "9:16",
        "portrait_4_3": "3:4",
        "square": "1:1",
        "square_hd": "1:1",
    }
    return mapping.get(aspect, aspect)  # Pass through if already ratio format


def _get_new_assets(asset_groups, generator_name):
    """Get Phase 3 domain-specific assets for a generator (IDs that don't start with a digit)."""
    if asset_groups is None:
        return []
    group = asset_groups.get(generator_name, [])
    return [(aid, adef) for aid, adef in group if not aid[0].isdigit()]


def gen_anchor_script(scripts_dir, v, cfg, asset_groups=None):
    """Generate generate-anchor.py (2A bento grid — MUST run first)."""
    seeds = cfg["generation"].get("seeds", [42, 137])
    prompt = render(PROMPT_2A_BENTO, v)
    out_sub = cfg["generation"].get("output_dir", "generated")

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": "Style Anchor Bento Grid (2A)",
        "output_subdir": out_sub,
    })
    func = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})

    main_body = f'''
PROMPT_2A = """{prompt}"""


def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Style Anchor Bento Grid (2A)")
    print("Model: Nano Banana Pro | MUST RUN FIRST")
    print("=" * 60)

    # Upload composition reference image if available
    image_urls = []
    ref_path = get_ref_image("2A")
    if ref_path:
        print(f"\\nUploading composition reference: {{os.path.basename(ref_path)}}")
        ref_url = fal_client.upload_file(ref_path)
        image_urls.append(ref_url)
    else:
        print("\\nNo composition reference found for 2A (optional).")

    # Add brand logo as visual reference if available
    logo_url = get_logo_url()
    if logo_url:
        image_urls.append(logo_url)

    print("\\n--- 2A: Brand Kit Bento Grid ---")
    gen_nano_banana("2A", "brand-kit-bento", PROMPT_2A, "16:9", image_urls)

    print("\\n" + "=" * 60)
    print("  ANCHOR GENERATION COMPLETE (2A)")
    print("  This file is the STYLE ANCHOR for all subsequent generation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''
    write_script(os.path.join(scripts_dir, "generate-anchor.py"), header + func + main_body)


def gen_identity_script(scripts_dir, v, cfg, asset_groups=None):
    """Generate generate-identity.py (2B seal + 2C logo + domain-specific identity assets)."""
    asset_ids = _get_asset_ids(asset_groups, "identity", {"2B", "2C"})
    if not asset_ids:
        return  # No identity assets selected

    seeds = cfg["generation"].get("seeds", [42, 137])
    prompt_2b = render(PROMPT_2B_SEAL, v)
    prompt_2c = render(PROMPT_2C_LOGO, v)
    out_sub = cfg["generation"].get("output_dir", "generated")

    # Build new asset prompts
    new_assets = _get_new_assets(asset_groups, "identity")
    new_asset_code = ""
    new_prompt_defs = ""
    extended = v.get("extended_prompts", {})
    for aid, adef in new_assets:
        pkey = adef.get("prompt_key", aid.lower().replace("-", "_"))
        # Use brand config prompt if available, else default template
        if pkey in extended:
            prompt_text = render(extended[pkey], v)
        elif pkey in DEFAULT_EXTENDED_PROMPTS:
            prompt_text = render(DEFAULT_EXTENDED_PROMPTS[pkey], v)
        else:
            continue
        aspect = adef.get("aspect", "square_hd")
        slug = aid.lower().replace("-", "_")
        safe_prompt = prompt_text.replace('"""', '\\"\\"\\"')
        new_prompt_defs += f'\nPROMPT_{slug.upper()} = """{safe_prompt}"""\n'
        new_asset_code += f'''
    print("\\n--- {aid}: {adef.get('name', aid)} ---")
    gen_flux_pro("{aid}", "{slug}", PROMPT_{slug.upper()} + logo_directive, "{aspect}")
'''

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": "Brand Identity (2B Seal + 2C Logo)",
        "output_subdir": out_sub,
    })
    func = render(FUNC_FLUX_PRO, {"seed_a": seeds[0], "seed_b": seeds[1]})

    # Build conditional blocks for legacy assets
    gen_2b = ""
    if "2B" in asset_ids:
        gen_2b = '''
    print("\\n--- 2B: Brand Seal ---")
    gen_flux_pro("2B", "brand-seal", PROMPT_2B + logo_directive, "square_hd")
'''
    gen_2c = ""
    if "2C" in asset_ids:
        gen_2c = '''
    print("\\n--- 2C: Logo Emboss ---")
    gen_flux_pro("2C", "logo-emboss", PROMPT_2C + logo_directive, "landscape_16_9")
'''

    main_body = f'''
PROMPT_2B = """{prompt_2b}"""

PROMPT_2C = """{prompt_2c}"""
{new_prompt_defs}

def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Brand Identity")
    print("Model: Flux 2 Pro")
    print("=" * 60)

    # If brand logo exists, append directive to reproduce it faithfully
    logo_directive = ""
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        print(f"  Logo file found: {{os.path.basename(LOGO_PATH)}}")
        logo_directive = "\\nCRITICAL: The brand's logo mark (described in the sigil section) must be reproduced faithfully as the established brand identity."
{gen_2b}{gen_2c}{new_asset_code}
    print("\\n" + "=" * 60)
    print("  IDENTITY COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''
    write_script(os.path.join(scripts_dir, "generate-identity.py"), header + func + main_body)


def gen_products_script(scripts_dir, v, cfg, asset_groups=None):
    """Generate generate-products.py (3A capsule + 3B book + 3C vial + domain-specific)."""
    asset_ids = _get_asset_ids(asset_groups, "products", {"3A", "3B", "3C"})
    if not asset_ids:
        return

    seeds = cfg["generation"].get("seeds", [42, 137])
    prompt_3a = render(PROMPT_3A_CAPSULE, v)
    prompt_3b = render(PROMPT_3B_BOOK, v)
    prompt_3c = render(PROMPT_3C_VIAL, v)
    out_sub = cfg["generation"].get("output_dir", "generated")

    # Build new asset code (Nano Banana Pro for domain-specific product assets)
    new_assets = _get_new_assets(asset_groups, "products")
    new_prompt_defs = ""
    new_asset_code = ""
    extended = v.get("extended_prompts", {})
    for aid, adef in new_assets:
        pkey = adef.get("prompt_key", aid.lower().replace("-", "_"))
        if pkey in extended:
            prompt_text = render(extended[pkey], v)
        elif pkey in DEFAULT_EXTENDED_PROMPTS:
            prompt_text = render(DEFAULT_EXTENDED_PROMPTS[pkey], v)
        else:
            continue
        aspect = adef.get("aspect", "portrait_hd")
        slug = aid.lower().replace("-", "_")
        model = adef.get("model", "nano-banana-pro")
        safe_prompt = prompt_text.replace('"""', '\\"\\"\\"')
        new_prompt_defs += f'\nPROMPT_{slug.upper()} = """{safe_prompt}"""\n'
        if model == "nano-banana-pro":
            nb_aspect = _flux_to_nb_aspect(aspect)
            new_asset_code += f'''
    print("\\n--- {aid}: {adef.get('name', aid)} (Nano Banana Pro) ---")
    gen_nano_banana("{aid}", "{slug}", PROMPT_{slug.upper()}, "{nb_aspect}", image_urls)
'''
        else:
            new_asset_code += f'''
    print("\\n--- {aid}: {adef.get('name', aid)} (Flux 2 Pro) ---")
    gen_flux_pro("{aid}", "{slug}", PROMPT_{slug.upper()}, "{aspect}")
'''

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": "Product Concepts",
        "output_subdir": out_sub,
    })
    func_flux = render(FUNC_FLUX_PRO, {"seed_a": seeds[0], "seed_b": seeds[1]})

    # Add Nano Banana if we have new assets needing it
    func_nb = ""
    nb_setup = ""
    if any(adef.get("model") == "nano-banana-pro" for _, adef in new_assets):
        func_nb = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})
        nb_setup = '''
    # Style anchor for Nano Banana Pro assets
    image_urls = []
    anchor_path = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")
    if os.path.exists(anchor_path):
        image_urls.append(fal_client.upload_file(anchor_path))
    logo_url = get_logo_url()
    if logo_url:
        image_urls.append(logo_url)
    # Product reference images for model accuracy
    for purl in get_product_ref_urls():
        image_urls.append(purl)
'''

    gen_3a = f'''
    print("\\n--- 3A: Capsule Collection ---")
    gen_flux_pro("3A", "capsule-collection", PROMPT_3A, "landscape_4_3")
''' if "3A" in asset_ids else ""
    gen_3b = f'''
    print("\\n--- 3B: Hero Book ---")
    gen_flux_pro("3B", "hero-book", PROMPT_3B, "square_hd")
''' if "3B" in asset_ids else ""
    gen_3c = f'''
    print("\\n--- 3C: Essence Vial ---")
    gen_flux_pro("3C", "essence-vial", PROMPT_3C, "square_hd")
''' if "3C" in asset_ids else ""

    main_body = f'''
PROMPT_3A = """{prompt_3a}"""

PROMPT_3B = """{prompt_3b}"""

PROMPT_3C = """{prompt_3c}"""
{new_prompt_defs}

def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Product Concepts")
    print("Model: Flux 2 Pro / Nano Banana Pro")
    print("=" * 60)
{nb_setup}{gen_3a}{gen_3b}{gen_3c}{new_asset_code}
    print("\\n" + "=" * 60)
    print("  PRODUCTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''
    write_script(os.path.join(scripts_dir, "generate-products.py"), header + func_flux + func_nb + main_body)


def gen_photography_script(scripts_dir, v, cfg, asset_groups=None):
    """Generate generate-photography.py (4A catalog + 4B flatlay + domain-specific)."""
    seeds = cfg["generation"].get("seeds", [42, 137])
    prompt_4a = render(PROMPT_4A_CATALOG, v)
    prompt_4b = render(PROMPT_4B_FLATLAY, v)
    out_sub = cfg["generation"].get("output_dir", "generated")

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": "Product Photography (4A + 4B)",
        "output_subdir": out_sub,
    })
    func_nb = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})
    func_flux = render(FUNC_FLUX_PRO, {"seed_a": seeds[0], "seed_b": seeds[1]})

    asset_ids = _get_asset_ids(asset_groups, "photography", {"4A", "4B"})
    if not asset_ids:
        return

    # Build new asset code
    new_assets = _get_new_assets(asset_groups, "photography")
    new_prompt_defs = ""
    new_asset_code = ""
    extended = v.get("extended_prompts", {})
    for aid, adef in new_assets:
        pkey = adef.get("prompt_key", aid.lower().replace("-", "_"))
        if pkey in extended:
            prompt_text = render(extended[pkey], v)
        elif pkey in DEFAULT_EXTENDED_PROMPTS:
            prompt_text = render(DEFAULT_EXTENDED_PROMPTS[pkey], v)
        else:
            continue
        aspect = _flux_to_nb_aspect(adef.get("aspect", "landscape_16_9"))
        slug = aid.lower().replace("-", "_")
        safe_prompt = prompt_text.replace('"""', '\\"\\"\\"')
        new_prompt_defs += f'\nPROMPT_{slug.upper()} = """{safe_prompt}"""\n'
        new_asset_code += f'''
    print("\\n--- {aid}: {adef.get('name', aid)} (Nano Banana Pro) ---")
    gen_nano_banana("{aid}", "{slug}", PROMPT_{slug.upper()}, "{aspect}", anchor_urls)
'''

    gen_4a = '''
    # 4A with composition reference
    print("\\n--- 4A: Catalog Layout (Nano Banana Pro) ---")
    urls_4a = list(anchor_urls)
    ref_4a = get_ref_image("4A")
    if ref_4a:
        print(f"  Adding composition ref: {os.path.basename(ref_4a)}")
        urls_4a.append(fal_client.upload_file(ref_4a))
    gen_nano_banana("4A", "catalog-layout", PROMPT_4A, "3:4", urls_4a)
''' if "4A" in asset_ids else ""

    gen_4b = '''
    print("\\n--- 4B: Flatlay (Flux 2 Pro) ---")
    gen_flux_pro("4B", "flatlay", PROMPT_4B, "square_hd")
''' if "4B" in asset_ids else ""

    main_body = f'''
PROMPT_4A = """{prompt_4a}"""

PROMPT_4B = """{prompt_4b}"""
{new_prompt_defs}
STYLE_ANCHOR = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")


def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Product Photography")
    print("=" * 60)

    anchor_urls = []
    if os.path.exists(STYLE_ANCHOR):
        print("Uploading style anchor...")
        anchor_url = fal_client.upload_file(STYLE_ANCHOR)
        anchor_urls = [anchor_url]
    else:
        print("WARNING: Style anchor not found. Run generate-anchor.py first.")

    # Add brand logo reference if available
    logo_url = get_logo_url()
    if logo_url:
        anchor_urls.append(logo_url)
    # Product reference images for model accuracy
    for purl in get_product_ref_urls():
        anchor_urls.append(purl)
{gen_4a}{gen_4b}{new_asset_code}
    print("\\n" + "=" * 60)
    print("  PHOTOGRAPHY COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''
    write_script(os.path.join(scripts_dir, "generate-photography.py"),
                 header + func_nb + func_flux + main_body)


def gen_illustrations_script(scripts_dir, v, cfg, asset_groups=None):
    """Generate generate-illustrations.py (5A-5D)."""
    seeds = cfg["generation"].get("seeds", [42, 137])
    # Condense for Recraft 1000-char limit
    prompt_5a = render(PROMPT_5A_HERITAGE, v)[:990]
    prompt_5b = render(PROMPT_5B_CAMPAIGN, v)
    prompt_5c = render(PROMPT_5C_PANEL, v)[:990]
    out_sub = cfg["generation"].get("output_dir", "generated")

    # Build icon prompts from config
    illus_cfg = cfg.get("prompts", {}).get("illustration", {})
    if isinstance(illus_cfg, dict):
        icon_groups = illus_cfg.get("icon_groups", [])
        icon_gen_model = illus_cfg.get("icon_generation_model", "flux")  # Default: flux (PNG), opt-in: recraft_vector (SVG)
    else:
        icon_groups = []
        icon_gen_model = "flux"

    # Build 5D icon generation code (depth-gated at generation time)
    icon_code = ""
    if icon_groups:
        depth = v.get("depth_level", "focused")
        if depth == "surface":
            active_groups = []
        elif depth == "focused":
            active_groups = icon_groups[:2]
        else:
            active_groups = icon_groups

        for gi, group in enumerate(active_groups):
            gname = group.get("name", f"Group {gi+1}")
            icons = group.get("icons", [])
            icon_names = [ic.get("name", "") if isinstance(ic, dict) else str(ic) for ic in icons]
            icon_list_str = ", ".join(icon_names)
            count = len(icons)
            layout = "2x2" if count <= 4 else "3x2" if count <= 6 else "4x2"

            batch_id = f"5D-{gi+1}"
            slug = slugify(gname)

            # Choose prompt template and generation code based on icon model
            if icon_gen_model == "recraft_vector":
                icon_prompt = render(PROMPT_5D_ICONS, {
                    **v, "count": str(count), "group_name": gname,
                    "layout": layout, "icon_list": icon_list_str,
                })[:990]  # Recraft 1000-char limit
                safe_prompt = icon_prompt.replace('"""', '\\"\\"\\"')
                icon_code += f'''
    # {batch_id}: {gname} Icons (Recraft V3 vector — SVG opt-in)
    print("\\n--- {batch_id}: {gname} Icons (Recraft V3 vector) ---")
    gen_recraft("{batch_id}", "{slug}-icons",
                """{safe_prompt}""",
                "vector_illustration",
                ["{v['primary_hex']}", "{v['secondary_hex']}"],
                "square_hd")
'''
            elif icon_gen_model == "recraft_digital":
                icon_prompt = render(PROMPT_5D_ICONS, {
                    **v, "count": str(count), "group_name": gname,
                    "layout": layout, "icon_list": icon_list_str,
                })[:990]
                safe_prompt = icon_prompt.replace('"""', '\\"\\"\\"')
                icon_code += f'''
    # {batch_id}: {gname} Icons (Recraft V3 digital illustration)
    print("\\n--- {batch_id}: {gname} Icons (Recraft V3 digital) ---")
    gen_recraft("{batch_id}", "{slug}-icons",
                """{safe_prompt}""",
                "digital_illustration",
                ["{v['primary_hex']}", "{v['secondary_hex']}"],
                "square_hd")
'''
            elif icon_gen_model == "flux":
                icon_prompt = render(PROMPT_5D_ICONS_FLUX, {
                    **v, "count": str(count), "group_name": gname,
                    "layout": layout, "icon_list": icon_list_str,
                })
                safe_prompt = icon_prompt.replace('"""', '\\"\\"\\"')
                icon_code += f'''
    # {batch_id}: {gname} Icons (Flux 2 Pro — default, PNG only)
    print("\\n--- {batch_id}: {gname} Icons (Flux 2 Pro) ---")
    gen_flux_pro("{batch_id}", "{slug}-icons",
                 """{safe_prompt}""",
                 "square_hd")
'''
            elif icon_gen_model == "nano_banana":
                icon_prompt = render(PROMPT_5D_ICONS_FLUX, {
                    **v, "count": str(count), "group_name": gname,
                    "layout": layout, "icon_list": icon_list_str,
                })
                safe_prompt = icon_prompt.replace('"""', '\\"\\"\\"')
                icon_code += f'''
    # {batch_id}: {gname} Icons (Nano Banana Pro with style anchor)
    print("\\n--- {batch_id}: {gname} Icons (Nano Banana Pro) ---")
    gen_nano_banana("{batch_id}", "{slug}-icons",
                    """{safe_prompt}""",
                    "1:1", image_urls)
'''

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": "Illustrations + Icons (5A-5D)",
        "output_subdir": out_sub,
    })
    func_rc = render(FUNC_RECRAFT, {"seed_a": seeds[0], "seed_b": seeds[1]})
    func_nb = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})
    func_flux = ""
    if icon_gen_model == "flux":
        func_flux = render(FUNC_FLUX_PRO, {"seed_a": seeds[0], "seed_b": seeds[1]})

    main_body = f'''
PROMPT_5A = """{prompt_5a}"""

PROMPT_5B = """{prompt_5b}"""

PROMPT_5C = """{prompt_5c}"""

STYLE_ANCHOR = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")


def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Illustrations + Icons (5A-5D)")
    print("=" * 60)

    # Verify Recraft prompt lengths
    for pid, p in {{"5A": PROMPT_5A, "5C": PROMPT_5C}}.items():
        count = len(p)
        status = "OK" if count < 1000 else "OVER LIMIT"
        print(f"  {{pid}}: {{count}} chars [{{status}}]")
        if count >= 1000:
            print("ERROR: Prompt exceeds 1000 char Recraft V3 limit. Condense it.")
            sys.exit(1)

    # 5A: Heritage Engraving (Recraft digital_illustration)
    print("\\n--- 5A: Heritage Engraving (Recraft V3 digital) ---")
    gen_recraft("5A", "heritage-engraving", PROMPT_5A,
                "digital_illustration",
                ["{v['primary_hex']}", "{v['secondary_hex']}", "{v['accent_hex']}"],
                "square_hd")

    # 5B: Campaign Grid (Nano Banana Pro + anchor + comp ref)
    print("\\n--- 5B: Campaign Grid (Nano Banana Pro) ---")
    anchor_urls = []
    if os.path.exists(STYLE_ANCHOR):
        anchor_url = fal_client.upload_file(STYLE_ANCHOR)
        anchor_urls = [anchor_url]
    logo_url = get_logo_url()
    if logo_url:
        anchor_urls.append(logo_url)
    ref_5b = get_ref_image("5B")
    if ref_5b:
        print(f"  Adding composition ref: {{os.path.basename(ref_5b)}}")
        anchor_urls.append(fal_client.upload_file(ref_5b))
    gen_nano_banana("5B", "campaign-grid", PROMPT_5B, "3:4", anchor_urls)

    # 5C: Art Panel (Recraft digital_illustration)
    print("\\n--- 5C: Art Panel (Recraft V3 digital) ---")
    gen_recraft("5C", "art-panel", PROMPT_5C,
                "digital_illustration",
                ["{v['primary_hex']}", "{v['accent_hex']}", "{v['signal_hex']}"],
                "portrait_4_3")
{icon_code}
    print("\\n" + "=" * 60)
    print("  ILLUSTRATIONS COMPLETE (5A-5D)")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''
    write_script(os.path.join(scripts_dir, "generate-illustrations.py"),
                 header + func_rc + func_nb + func_flux + main_body)


def gen_narrative_script(scripts_dir, v, cfg, asset_groups=None):
    """Generate generate-narrative.py (7A contact sheets + domain-specific)."""
    asset_ids = _get_asset_ids(asset_groups, "narrative", {"7A"})
    if not asset_ids:
        return

    seeds = cfg["generation"].get("seeds", [42, 137])
    prompt_7a = render(PROMPT_7A_CONTACT, v)
    out_sub = cfg["generation"].get("output_dir", "generated")

    # Build new asset code
    new_assets = _get_new_assets(asset_groups, "narrative")
    new_prompt_defs = ""
    new_asset_code = ""
    extended = v.get("extended_prompts", {})
    for aid, adef in new_assets:
        pkey = adef.get("prompt_key", aid.lower().replace("-", "_"))
        if pkey in extended:
            prompt_text = render(extended[pkey], v)
        elif pkey in DEFAULT_EXTENDED_PROMPTS:
            prompt_text = render(DEFAULT_EXTENDED_PROMPTS[pkey], v)
        else:
            continue
        aspect = _flux_to_nb_aspect(adef.get("aspect", "landscape_16_9"))
        slug = aid.lower().replace("-", "_")
        safe_prompt = prompt_text.replace('"""', '\\"\\"\\"')
        new_prompt_defs += f'\nPROMPT_{slug.upper()} = """{safe_prompt}"""\n'
        new_asset_code += f'''
    print("\\n--- {aid}: {adef.get('name', aid)} ---")
    gen_nano_banana("{aid}", "{slug}", PROMPT_{slug.upper()}, "{aspect}", image_urls)
'''

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": "Narrative Assets",
        "output_subdir": out_sub,
    })
    func = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})

    gen_7a = '''
    ref_7a = get_ref_image("7A")
    if ref_7a:
        print(f"  Adding composition ref: {os.path.basename(ref_7a)}")
        comp_url = fal_client.upload_file(ref_7a)
        image_urls.append(comp_url)

    gen_nano_banana("7A", "contact-sheet", PROMPT_7A, "1:1", image_urls)
''' if "7A" in asset_ids else ""

    main_body = f'''
PROMPT_7A = """{prompt_7a}"""
{new_prompt_defs}
STYLE_ANCHOR = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")


def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Narrative Assets")
    print("Model: Nano Banana Pro")
    print("=" * 60)

    image_urls = []
    if os.path.exists(STYLE_ANCHOR):
        print("Uploading style anchor...")
        anchor_url = fal_client.upload_file(STYLE_ANCHOR)
        image_urls.append(anchor_url)
    else:
        print("WARNING: Style anchor not found. Run generate-anchor.py first.")

    logo_url = get_logo_url()
    if logo_url:
        image_urls.append(logo_url)
    # Product reference images for model accuracy
    for purl in get_product_ref_urls():
        image_urls.append(purl)
{gen_7a}{new_asset_code}
    print("\\n" + "=" * 60)
    print("  NARRATIVE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''
    write_script(os.path.join(scripts_dir, "generate-narrative.py"), header + func + main_body)


def gen_posters_script(scripts_dir, v, cfg, asset_groups=None):
    """Generate generate-posters.py (8A seeker + 9A engines + 10A-C sequences + domain-specific)."""
    asset_ids = _get_asset_ids(asset_groups, "posters", {"8A"})
    # Posters always generate (9A/10A come from config, not registry)

    seeds = cfg["generation"].get("seeds", [42, 137])
    # Check for brand-specific prompt overrides (Phase 4 — detemplatization)
    extended = v.get("extended_prompts", {})
    prompt_8a = render(extended["prompt_8a"], v) if "prompt_8a" in extended else render(PROMPT_8A_SEEKER, v)
    prompt_9a = render(extended["prompt_9a"], v) if "prompt_9a" in extended else render(PROMPT_9A_ENGINE, v)
    prompt_10 = render(extended["prompt_10"], v) if "prompt_10" in extended else render(PROMPT_10_SEQUENCE, v)
    out_sub = cfg["generation"].get("output_dir", "generated")

    # Load engine definitions from config
    engines = cfg.get("prompts", {}).get("posters", {})
    if isinstance(engines, dict):
        engines_list = engines.get("engines", [])
        sequences_list = engines.get("sequences", [])
    else:
        engines_list = []
        sequences_list = []

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": "Campaign Posters (8A + 9A + 10A-C)",
        "output_subdir": out_sub,
    })
    func = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})

    # Build engine dict literal
    engine_dict = "ENGINES = {\n"
    for eng in engines_list:
        eid = eng.get("id", "9A-01")
        engine_dict += f'    "{eid}": {{\n'
        for k in ["name", "engine_name", "tagline", "object",
                   "material_a", "material_b", "bg_color", "bg_hex"]:
            val = eng.get(k, "")
            engine_dict += f'        "{k}": """{val}""",\n'
        engine_dict += "    },\n"
    engine_dict += "}\n"

    # Build sequence dict literal
    seq_dict = "SEQUENCES = {\n"
    for seq in sequences_list:
        sid = seq.get("id", "10A")
        key = seq.get("key", sid.lower())
        title = seq.get("title", "Practice Sequence")
        panels = seq.get("panels", "")
        seq_dict += f'    "{key}": {{\n'
        seq_dict += f'        "id": "{sid}",\n'
        seq_dict += f'        "title": """{title}""",\n'
        seq_dict += f'        "panels": """{panels}""",\n'
        seq_dict += "    },\n"
    seq_dict += "}\n"

    # Build new asset code for posters
    new_assets = _get_new_assets(asset_groups, "posters")
    new_prompt_defs = ""
    new_asset_code = ""
    extended = v.get("extended_prompts", {})
    for aid, adef in new_assets:
        pkey = adef.get("prompt_key", aid.lower().replace("-", "_"))
        if pkey in extended:
            prompt_text = render(extended[pkey], v)
        elif pkey in DEFAULT_EXTENDED_PROMPTS:
            prompt_text = render(DEFAULT_EXTENDED_PROMPTS[pkey], v)
        else:
            continue
        aspect = _flux_to_nb_aspect(adef.get("aspect", "portrait_hd"))
        slug = aid.lower().replace("-", "_")
        safe_prompt = prompt_text.replace('"""', '\\"\\"\\"')
        new_prompt_defs += f'\nPROMPT_{slug.upper()} = """{safe_prompt}"""\n'
        new_asset_code += f'''
    print("\\n--- {aid}: {adef.get('name', aid)} ---")
    gen_nano_banana("{aid}", "{slug}", PROMPT_{slug.upper()}, "{aspect}", image_urls)
'''

    gen_8a = f'''
    # 8A: Seeker poster (with composition reference)
    print("\\n--- 8A: Seeker Poster ---")
    urls_8a = list(image_urls)
    ref_8a = get_ref_image("8A")
    if ref_8a:
        print(f"  Adding composition ref: {{os.path.basename(ref_8a)}}")
        urls_8a.append(fal_client.upload_file(ref_8a))
    gen_nano_banana("8A", "seeker-poster", PROMPT_8A, "3:4", urls_8a,
                    seeds=({seeds[0]}, {seeds[1]}, 256))
''' if "8A" in asset_ids else ""

    main_body = f'''
PROMPT_8A = """{prompt_8a}"""

PROMPT_9A_BASE = """{prompt_9a}"""

PROMPT_10_BASE = """{prompt_10}"""
{new_prompt_defs}
{engine_dict}
{seq_dict}
STYLE_ANCHOR = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")


def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Campaign Posters")
    print("Model: Nano Banana Pro")
    print("=" * 60)

    image_urls = []
    if os.path.exists(STYLE_ANCHOR):
        print("Uploading style anchor...")
        anchor_url = fal_client.upload_file(STYLE_ANCHOR)
        image_urls = [anchor_url]
    else:
        print("WARNING: Style anchor not found.")

    logo_url = get_logo_url()
    if logo_url:
        image_urls.append(logo_url)
    # Product reference images for model accuracy
    for purl in get_product_ref_urls():
        image_urls.append(purl)
{gen_8a}
    # 9A: Individual engine posters (with composition reference)
    if ENGINES:
        print("\\n--- 9A: Engine Posters ---")
        urls_9a = list(image_urls)
        ref_9a = get_ref_image("9A")
        if ref_9a:
            print(f"  Adding composition ref: {{os.path.basename(ref_9a)}}")
            urls_9a.append(fal_client.upload_file(ref_9a))
        for eid, edata in ENGINES.items():
            prompt = PROMPT_9A_BASE.format(**edata)
            slug = edata["name"].lower().replace(" ", "-").replace("&", "and")
            print(f"\\n  [{{eid}}] {{edata['name']}}...")
            gen_nano_banana(eid, f"{{slug}}-poster", prompt, "3:4", urls_9a,
                            seeds=({seeds[0]},))

    # 10A-C: Ritual sequences (with grid composition reference)
    if SEQUENCES:
        print("\\n--- 10A-C: Practice Sequences ---")
        urls_10 = list(image_urls)
        ref_10 = get_ref_image("10A")
        if ref_10:
            print(f"  Adding grid composition ref: {{os.path.basename(ref_10)}}")
            urls_10.append(fal_client.upload_file(ref_10))
        for skey, sdata in SEQUENCES.items():
            sid = sdata["id"]
            prompt = PROMPT_10_BASE.format(
                sequence_title=sdata["title"],
                panel_descriptions=sdata["panels"],
            )
            slug = sdata["title"].lower().replace(" ", "-")
            print(f"\\n  [{{sid}}] {{sdata['title']}}...")
            gen_nano_banana(sid, slug, prompt, "1:1", urls_10)

{new_asset_code}
    print("\\n" + "=" * 60)
    print("  POSTERS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''
    write_script(os.path.join(scripts_dir, "generate-posters.py"), header + func + main_body)


# =====================================================================
# COOKBOOK GENERATOR
# =====================================================================

def gen_cookbook(out_dir, v, cfg):
    """Generate prompt-cookbook.md with all prompts documented."""
    brand = v["brand_name"]
    lines = [
        f"# {brand} -- Visual Identity Prompt Cookbook",
        "",
        "Generated by Brandmint pipeline engine.",
        "",
        "## Brand Context",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Brand | {brand} |",
        f"| Tagline | {v['brand_tagline']} |",
        f"| Archetype | {v['archetype']} |",
        f"| Voice | {v['voice']} |",
        f"| Domain | {v['domain']} |",
        f"| Theme | {v['theme_name']} |",
        f"| Primary | {v['primary_name']} {v['primary_hex']} |",
        f"| Secondary | {v['secondary_name']} {v['secondary_hex']} |",
        f"| Accent | {v['accent_name']} {v['accent_hex']} |",
        f"| Header Font | {v['header_font']} |",
        f"| Body Font | {v['body_font']} |",
        f"| Materials | {v['materials_list']} |",
        "",
        "---",
        "",
        "## Prompts",
        "",
    ]

    prompt_entries = [
        ("2A", "Brand Kit Bento Grid", "fal-ai/nano-banana-pro", "16:9", PROMPT_2A_BENTO),
        ("2B", "Brand Seal", "fal-ai/flux-2-pro", "1:1", PROMPT_2B_SEAL),
        ("2C", "Logo Emboss", "fal-ai/flux-2-pro", "16:9", PROMPT_2C_LOGO),
        ("3A", "Capsule Collection", "fal-ai/flux-2-pro", "4:3", PROMPT_3A_CAPSULE),
        ("3B", "Hero Book", "fal-ai/flux-2-pro", "1:1", PROMPT_3B_BOOK),
        ("3C", "Essence Vial", "fal-ai/flux-2-pro", "1:1", PROMPT_3C_VIAL),
        ("4A", "Catalog Layout", "fal-ai/nano-banana-pro", "3:4", PROMPT_4A_CATALOG),
        ("4B", "Flatlay", "fal-ai/flux-2-pro", "1:1", PROMPT_4B_FLATLAY),
        ("5A", "Heritage Engraving", "fal-ai/recraft/v3", "1:1", PROMPT_5A_HERITAGE),
        ("5B", "Campaign Grid", "fal-ai/nano-banana-pro", "3:4", PROMPT_5B_CAMPAIGN),
        ("5C", "Art Panel", "fal-ai/recraft/v3", "3:4", PROMPT_5C_PANEL),
        ("7A", "Contact Sheet", "fal-ai/nano-banana-pro", "1:1", PROMPT_7A_CONTACT),
        ("8A", "Seeker Poster", "fal-ai/nano-banana-pro", "3:4", PROMPT_8A_SEEKER),
    ]

    for pid, name, model, aspect, template in prompt_entries:
        rendered = render(template, v)
        lines.extend([
            f"### {pid}: {name}",
            "",
            f"- **Model**: `{model}`",
            f"- **Aspect Ratio**: {aspect}",
            f"- **Prompt Length**: {len(rendered)} chars",
            "",
            "```",
            rendered,
            "```",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## Negative Prompt (Applied to All)",
        "",
        "```",
        v["negative_prompt"],
        "```",
        "",
    ])

    cookbook_path = os.path.join(out_dir, "prompt-cookbook.md")
    with open(cookbook_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Generated: prompt-cookbook.md")


# =====================================================================
# MANIFEST GENERATOR
# =====================================================================

def gen_manifest(out_dir, v, cfg, exec_ctx, asset_groups=None):
    """Generate generation-manifest.json for orchv2 budget validation."""
    depth = exec_ctx.get("depth_level", "focused")
    depth_cfg = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["focused"])
    skip_ids = depth_cfg["skip_ids"]
    seeds_count = depth_cfg["seeds_count"]

    # Cost per call by model
    costs = {"nano-banana-pro": 0.08, "flux-2-pro": 0.05, "recraft-v3": 0.04}

    assets = []

    # If we have domain-aware asset_groups, use those for the base asset list
    if asset_groups is not None:
        for gen_name, group in asset_groups.items():
            for aid, adef in group:
                model = adef.get("model", "nano-banana-pro")
                cost_key = model if model in costs else "nano-banana-pro"
                sc = seeds_count
                if aid == "8A" and depth != "surface":
                    sc = seeds_count + 1  # Seeker gets extra seed
                assets.append({
                    "id": aid,
                    "name": adef.get("name", aid),
                    "model": model,
                    "seeds": sc,
                    "calls": sc,
                    "est_cost": round(sc * costs.get(cost_key, 0.08), 2),
                })
    else:
        # Legacy mode: hardcoded 19 assets
        # 2A: Nano Banana
        assets.append({"id": "2A", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 2B, 2C: Flux 2 Pro
        for pid in ["2B", "2C"]:
            if pid not in skip_ids:
                assets.append({"id": pid, "model": "flux-2-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["flux-2-pro"]})
        # 3A, 3B, 3C: Flux 2 Pro
        for pid in ["3A", "3B", "3C"]:
            if pid not in skip_ids:
                assets.append({"id": pid, "model": "flux-2-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["flux-2-pro"]})
        # 4A: Nano Banana, 4B: Flux 2
        if "4A" not in skip_ids:
            assets.append({"id": "4A", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        if "4B" not in skip_ids:
            assets.append({"id": "4B", "model": "flux-2-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["flux-2-pro"]})
        # 5A, 5C: Recraft
        for pid in ["5A", "5C"]:
            if pid not in skip_ids:
                assets.append({"id": pid, "model": "recraft-v3", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["recraft-v3"]})
        # 5B: Nano Banana
        if "5B" not in skip_ids:
            assets.append({"id": "5B", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 5D: Recraft (icon groups)
        illus_cfg = cfg.get("prompts", {}).get("illustration", {})
        icon_groups = illus_cfg.get("icon_groups", []) if isinstance(illus_cfg, dict) else []
        if depth != "surface":
            active = icon_groups[:2] if depth == "focused" else icon_groups
            for gi, g in enumerate(active):
                assets.append({"id": f"5D-{gi+1}", "model": "recraft-v3", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["recraft-v3"]})
        # 7A: Nano Banana
        if "7A" not in skip_ids:
            assets.append({"id": "7A", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 8A: Nano Banana (extra seed for seeker at non-surface depths)
        if "8A" not in skip_ids:
            seeker_seeds = seeds_count + 1 if depth != "surface" else seeds_count
            assets.append({"id": "8A", "model": "nano-banana-pro", "seeds": seeker_seeds, "calls": seeker_seeds, "est_cost": seeker_seeds * costs["nano-banana-pro"]})

    # Config-driven assets (always added regardless of mode — 9A engines, 10A-C sequences)
    engines = cfg.get("prompts", {}).get("posters", {})
    engines_list = engines.get("engines", []) if isinstance(engines, dict) else []
    for eng in engines_list:
        eid = eng.get("id", "9A")
        if eid not in skip_ids:
            assets.append({"id": eid, "model": "nano-banana-pro", "seeds": 1, "calls": 1, "est_cost": costs["nano-banana-pro"]})
    sequences_list = engines.get("sequences", []) if isinstance(engines, dict) else []
    for seq in sequences_list:
        sid = seq.get("id", "10A")
        if sid not in skip_ids:
            assets.append({"id": sid, "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})

    # 5D icon groups (always config-driven)
    if asset_groups is not None:
        illus_cfg = cfg.get("prompts", {}).get("illustration", {})
        icon_groups = illus_cfg.get("icon_groups", []) if isinstance(illus_cfg, dict) else []
        if depth != "surface":
            active = icon_groups[:2] if depth == "focused" else icon_groups
            for gi, g in enumerate(active):
                assets.append({"id": f"5D-{gi+1}", "model": "recraft-v3", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["recraft-v3"]})

    total_calls = sum(a["calls"] for a in assets)
    total_cost = sum(a["est_cost"] for a in assets)

    domain_tags = v.get("domain_tags", [])
    manifest = {
        "brand": v["brand_name"],
        "depth_level": depth,
        "budget_tier": exec_ctx.get("budget_tier", "standard"),
        "launch_channel": exec_ctx.get("launch_channel", "dtc"),
        "mode": "domain-aware" if domain_tags else "legacy",
        "domain_tags": domain_tags,
        "total_assets": len(assets),
        "total_api_calls": total_calls,
        "estimated_cost_usd": round(total_cost, 2),
        "assets": assets,
    }

    manifest_path = os.path.join(out_dir, "generation-manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Generated: generation-manifest.json ({len(assets)} assets, ${total_cost:.2f} est.)")


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Brandmint -- Generate pipeline scripts from brand config"
    )
    parser.add_argument("config", help="Path to brand-config.yaml")
    parser.add_argument("--output-dir", help="Output directory (default: derived from brand name)")
    parser.add_argument("--refresh-refs", action="store_true",
                        help="Re-scan references/images/ and regenerate reference-map.json before generating pipeline")
    args = parser.parse_args()

    print("=" * 60)
    print("BRANDMINT -- Pipeline Engine")
    print("=" * 60)

    config_path = os.path.abspath(args.config)
    print(f"\n  Config: {config_path}")

    cfg = load_config(config_path)
    exec_ctx = load_execution_context(config_path, cfg)
    v = build_vars(cfg, exec_ctx, config_path=config_path)

    # ── Reference map: load from JSON or use hardcoded fallback ──
    ref_map_path = os.path.join(os.path.dirname(config_path), "..", "references", "reference-map.json")
    if not os.path.exists(ref_map_path):
        # Try relative to script location (brandmint repo root)
        ref_map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "reference-map.json")

    if args.refresh_refs:
        images_dir = os.path.join(os.path.dirname(ref_map_path), "images")
        if os.path.isdir(images_dir):
            import subprocess
            mapper_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_references.py")
            if os.path.exists(mapper_script):
                print("\n  Refreshing reference map...")
                subprocess.run([sys.executable, mapper_script, images_dir, "--json-only"], check=True)
                print("  Reference map refreshed.")
            else:
                print(f"  WARNING: map_references.py not found at {mapper_script}")
        else:
            print(f"  WARNING: references/images/ not found at {images_dir}")

    ref_images = load_ref_map(ref_map_path)
    if os.path.exists(ref_map_path):
        print(f"  Refs: Loaded {len(ref_images)} mappings from reference-map.json")
    else:
        print(f"  Refs: Using {len(ref_images)} hardcoded defaults (no reference-map.json found)")
    v["ref_images_block"] = build_ref_images_block(ref_images)

    # Build ref overrides literal for generated scripts
    ref_dict = cfg.get("generation", {}).get("reference_overrides", {})
    channel = exec_ctx.get("launch_channel", "dtc")
    for k, val in CHANNEL_REF_OVERRIDES.get(channel, {}).items():
        if k not in ref_dict:
            ref_dict[k] = val
    ref_literal = ("{\n" + "".join(f'    "{k}": "{val}",\n' for k, val in ref_dict.items()) + "}") if ref_dict else "{}"
    v["ref_overrides_literal"] = ref_literal

    # Build product reference paths literal for generated scripts
    prod_refs = v.get("product_reference_images", [])
    v["product_ref_paths_literal"] = repr(prod_refs) if prod_refs else "[]"

    if args.output_dir:
        out_dir = os.path.abspath(args.output_dir)
    else:
        out_dir = os.path.join(os.path.dirname(config_path), slugify(v["brand_name"]))

    scripts_dir = os.path.join(out_dir, "scripts")
    output_subdir = cfg["generation"].get("output_dir", "generated")
    assets_dir = os.path.join(out_dir, output_subdir)

    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # ── Phase 3: Asset Registry Selection ──
    domain_tags = v.get("domain_tags", [])
    depth = exec_ctx.get("depth_level", "focused")

    asset_groups = None  # None = legacy mode
    if domain_tags:
        try:
            from asset_registry import select_assets, get_assets_by_generator, print_selection_summary
            selected = select_assets(domain_tags, depth, channel)
            asset_groups = get_assets_by_generator(selected)
            print_selection_summary(selected, domain_tags, depth, channel)
        except ImportError:
            print("  WARNING: asset_registry.py not found, using legacy mode")

    print(f"  Output: {out_dir}")
    print(f"  Scripts: {scripts_dir}")
    print(f"  Brand: {v['brand_name']}")
    print(f"  Theme: {v['theme_name']}")
    print(f"  Depth: {depth}")
    print(f"  Channel: {channel}")
    print(f"  Tone: {exec_ctx.get('tone', 'default') or 'default'}")
    if not domain_tags:
        print(f"  Mode: Legacy (all 19 assets — no domain_tags)")
    print()

    print("Generating pipeline scripts...")
    gen_anchor_script(scripts_dir, v, cfg, asset_groups)
    gen_identity_script(scripts_dir, v, cfg, asset_groups)
    gen_products_script(scripts_dir, v, cfg, asset_groups)
    gen_photography_script(scripts_dir, v, cfg, asset_groups)
    gen_illustrations_script(scripts_dir, v, cfg, asset_groups)
    gen_narrative_script(scripts_dir, v, cfg, asset_groups)
    gen_posters_script(scripts_dir, v, cfg, asset_groups)

    print("\nGenerating prompt cookbook...")
    gen_cookbook(out_dir, v, cfg)

    print("\nGenerating manifest...")
    gen_manifest(out_dir, v, cfg, exec_ctx, asset_groups)

    print(f"\n{'=' * 60}")
    print("  PIPELINE GENERATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"\n  Scripts: {scripts_dir}/")
    print(f"  Cookbook: {os.path.join(out_dir, 'prompt-cookbook.md')}")
    print(f"  Manifest: {os.path.join(out_dir, 'generation-manifest.json')}")
    print(f"\n  Execution order:")
    print(f"    1. python3 {scripts_dir}/generate-anchor.py     # MUST RUN FIRST")
    print(f"    2-7. Remaining scripts can run in parallel after anchor.")
    print(f"\n  Total estimated assets: See generation-manifest.json for details")


if __name__ == "__main__":
    main()
