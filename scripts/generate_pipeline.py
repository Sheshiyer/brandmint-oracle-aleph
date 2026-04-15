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
    "3C": "ref-3C-product-detail.jpg",
    "4A": "ref-4A-catalog-layout.jpg",
    "4B": "ref-4B-flatlay.jpg",
    "5A": "ref-5A-heritage-engraving.jpg",
    "5B": "ref-5B-campaign-grid.jpg",
    "7A": "ref-7A-contact-sheet.jpg",
    "8A": "ref-8A-seeker-poster.jpg",
    "9A": "ref-9A-engine-poster.jpg",
    "10A": "ref-7A-contact-sheet.jpg",
}


def load_ref_map(ref_map_path):
    """Load reference-map.json and return (ref_images, full_catalog).

    Returns:
        ref_images: dict mapping prompt_id -> filename (primary + reuses only)
        full_catalog: list of {"file": str, "tags": list, "description": str, "type": str}
    """
    if not os.path.exists(ref_map_path):
        return dict(_DEFAULT_REF_IMAGES), []

    with open(ref_map_path) as f:
        data = json.load(f)

    # Primary + reuses → REF_IMAGES (unchanged behavior)
    result = {}
    for pid, entry in data.get("primary", {}).items():
        result[pid] = entry["file"]
    for pid, entry in data.get("reuses", {}).items():
        result[pid] = entry["file"]

    # Full catalog: alternatives, styles, demos, twitter
    catalog = []
    for pid, alts in data.get("alternatives", {}).items():
        for alt in alts:
            catalog.append({
                "file": alt["file"],
                "description": alt.get("description", ""),
                "tags": _extract_tags_from_filename(alt["file"]),
                "type": "alternative",
                "related_pid": pid,
            })
    for style in data.get("styles", []):
        catalog.append({
            "file": style["file"],
            "description": style.get("description", ""),
            "tags": _extract_tags_from_filename(style["file"]),
            "type": "style",
        })
    for demo in data.get("demos", []):
        catalog.append({
            "file": demo["file"],
            "description": demo.get("description", ""),
            "tags": _extract_tags_from_filename(demo["file"]),
            "type": "demo",
        })
    for tw in data.get("twitter", []):
        catalog.append({
            "file": tw["images"][0]["file"] if tw.get("images") else "",
            "description": tw.get("prompt_text", "")[:200],
            "tags": tw.get("tags", []),
            "type": "twitter",
        })

    return result, catalog


def _extract_tags_from_filename(filename):
    """Extract tags from reference filename by splitting on hyphens."""
    base = os.path.splitext(filename)[0]
    # Strip prefix patterns: ref-alt-, ref-style-, ref-demo-, ref-tw-NNN-author-
    base = re.sub(r"^ref-(alt|style|demo|tw-\d+-[^-]+)-", "", base)
    return [t for t in base.split("-") if len(t) > 2]


_SUPP_REF_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "your", "their",
    "our", "use", "using", "show", "shown", "across", "over", "under", "through",
    "feel", "like", "looks", "look", "only", "plus", "without", "brand", "image",
    "design", "style", "visual", "lighting", "premium", "modern", "clean", "high",
    "real", "world", "hyper", "ultra", "professional", "commercial", "photo",
    "photography", "video", "poster", "layout", "grid", "product", "products",
}

_SUPP_REF_LOW_SIGNAL_TERMS = {
    "blue", "pink", "white", "black", "gold", "silver", "premium", "modern",
    "clean", "visual", "design", "image", "commercial", "photo", "photography",
    "product", "products", "lighting", "video", "poster", "layout", "grid",
    "nano", "banana", "gemini", "prompt", "prompts", "google", "openai", "gpt",
}

_SUPP_REF_DEVICE_BRAND_CONFLICT_TERMS = {
    "portrait", "portraits", "face", "faces", "fashion", "beauty", "skincare",
    "makeup", "cosmetic", "cosmetics", "celebrity", "caricature", "female", "male",
    "woman", "women", "man", "men", "person", "people", "model", "models",
    "outfit", "outfits", "fragrance", "perfume", "lip", "lips", "food", "drink",
    "beverage", "coffee", "cocktail",
}

_SUPP_REF_DEVICE_BRAND_TERMS = {
    "automation", "app", "dashboard", "device", "devices", "hardware", "building",
    "buildings", "home", "homes", "security", "control", "controls", "camera",
    "cameras", "door", "doorbell", "lock", "energy", "climate", "access",
    "architectural", "panel", "system", "systems",
}


def _normalize_ref_token(token):
    token = (token or "").strip().lower()
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        return token[:-1]
    return token


def _extract_ref_terms(*values):
    terms = []
    for value in values:
        if not value:
            continue
        if isinstance(value, (list, tuple, set)):
            for item in value:
                terms.extend(_extract_ref_terms(item))
            continue
        for raw in re.findall(r"[a-z0-9]+", str(value).lower()):
            token = _normalize_ref_token(raw)
            if len(token) < 3 or token in _SUPP_REF_STOPWORDS:
                continue
            terms.append(token)
    return terms


def _derive_supp_ref_policy(cfg):
    supp_cfg = cfg.get("generation", {}).get("supplementary_refs", {})
    sources = [
        cfg.get("brand", {}).get("domain", ""),
        cfg.get("brand", {}).get("tagline", ""),
        cfg.get("theme", {}).get("description", ""),
        cfg.get("positioning", {}).get("statement", ""),
        cfg.get("products", {}).get("hero", {}).get("name", ""),
        cfg.get("products", {}).get("hero", {}).get("description", ""),
        cfg.get("products", {}).get("hero", {}).get("physical_form", ""),
        cfg.get("products", {}).get("detail", {}).get("focus", ""),
        cfg.get("products", {}).get("category", ""),
        cfg.get("photography", {}).get("style", ""),
        cfg.get("photography", {}).get("environment", ""),
        cfg.get("brand", {}).get("domain_tags", []),
        cfg.get("theme", {}).get("mood_keywords", []),
        cfg.get("products", {}).get("flatlay_objects", {}).get("items", []),
    ]
    context_terms = {
        term for term in _extract_ref_terms(*sources)
        if term not in _SUPP_REF_LOW_SIGNAL_TERMS
    }

    required_terms = {
        term for term in _extract_ref_terms(supp_cfg.get("required_terms", []))
        if term not in _SUPP_REF_LOW_SIGNAL_TERMS
    }
    if not required_terms:
        required_terms = set(context_terms)

    blocked_terms = set(_extract_ref_terms(supp_cfg.get("blocked_terms", [])))
    if context_terms.intersection({_normalize_ref_token(t) for t in _SUPP_REF_DEVICE_BRAND_TERMS}):
        blocked_terms.update(
            _normalize_ref_token(term) for term in _SUPP_REF_DEVICE_BRAND_CONFLICT_TERMS
        )

    return {
        "enabled": supp_cfg.get("enabled", True),
        "required_terms": required_terms,
        "context_terms": context_terms,
        "blocked_terms": blocked_terms,
        "minimum_required_matches": max(1, int(supp_cfg.get("minimum_required_matches", 1))),
    }


def _entry_ref_terms(entry_id, entry):
    return set(_extract_ref_terms(
        entry_id,
        entry.get("file", ""),
        entry.get("description", ""),
        entry.get("composition_tags", []),
        entry.get("model_affinity", []),
        entry.get("tags", []),
    ))


# Prompt IDs that use Nano Banana Pro (support image_url references)
_NANO_BANANA_PIDS = ["2A", "3A", "3B", "3C", "4A", "4B", "5B", "7A", "8A", "9A", "10A"]

# Subject type per PID — what the asset conceptually depicts
_PID_SUBJECT_TYPES = {
    "2A": "layout",          # bento grid → compositional layout
    "2B": "logo",            # brand seal
    "2C": "logo",            # logo emboss
    "3A": "multi-product",   # capsule collection
    "3B": "single-product",  # hero product
    "3C": "single-product",  # product detail
    "4A": "catalog-layout",  # catalog with spec callouts
    "4B": "flatlay",         # product flatlay
    "5A": "illustration",    # heritage engraving
    "5B": "campaign-layout", # campaign grid
    "5C": "illustration",    # art panel
    "7A": "photo-grid",      # contact sheet
    "8A": "poster",          # seeker poster
    "9A": "poster",          # engine poster
    "10A": "photo-grid",     # social proof contact sheet
}

# Layout PIDs get relaxed subject_type filtering (compositional refs are broadly useful)
_LAYOUT_PIDS = {"2A", "4A", "5B", "7A", "8A", "9A", "10A"}

# Fallback keyword context (used when reference-catalog.yaml is unavailable)
_PID_CONTEXT = {
    "2A": ["bento", "grid", "layout", "brand-kit", "composition", "modular"],
    "3A": ["capsule", "collection", "lineup", "product", "multi", "range"],
    "3B": ["hero", "product", "single", "flagship", "main", "feature"],
    "3C": ["detail", "product", "close-up", "texture", "material", "craft"],
    "4A": ["catalog", "layout", "product", "spec", "detail", "grid"],
    "4B": ["flatlay", "product", "minimal", "white", "arrangement", "overhead"],
    "5B": ["campaign", "grid", "poster", "marketing", "ad", "promotion"],
    "7A": ["contact", "sheet", "proof", "collection", "overview"],
    "8A": ["seeker", "poster", "persona", "portrait", "character"],
    "9A": ["engine", "poster", "system", "process", "mechanism"],
    "10A": ["contact", "sheet", "proof", "collection", "social"],
}


def _aesthetic_distance(profile_a, profile_b):
    """Euclidean distance between two 5-axis aesthetic profiles."""
    axes = [
        "composition_density", "temporal_register",
        "material_richness", "visual_boldness",
        "editorial_vs_commercial",
    ]
    return sum(
        (profile_a.get(ax, 0.5) - profile_b.get(ax, 0.5)) ** 2
        for ax in axes
    ) ** 0.5


def select_supp_refs(catalog, brand_tags, max_per_pid=3, catalog_yaml_path=None,
                     brand_domain_tags=None, selection_policy=None):
    """Select supplementary refs using semantic + aesthetic scoring.

    Gated pipeline (when catalog YAML is available):
      1. Relevance filter: candidate metadata must match brand/product terms
      2. Conflict filter: reject candidates with blocked subject/style terms
      3. Domain filter: candidate domain_suitability must intersect brand domains
      4. Subject filter: candidate subject_type must match PID (layout PIDs exempt)
      5. Diversity slots: for multi-domain brands, spread refs across domains
      6. Aesthetic tiebreaker: within filtered set, score by aesthetic distance

    Falls back to keyword-overlap scoring if catalog YAML is not available.

    Args:
        catalog: list of catalog entries from load_ref_map() (fallback)
        brand_tags: list of brand-relevant keywords (fallback)
        max_per_pid: max supplementary refs per prompt ID
        catalog_yaml_path: path to reference-catalog.yaml (preferred)
        brand_domain_tags: list of brand domain tags (e.g. ["marketplace", "fashion"])
        selection_policy: dict with required/context/blocked term sets

    Returns:
        dict mapping pid -> [{"file": str, "score": float}, ...]
    """
    if brand_domain_tags is None:
        brand_domain_tags = []
    if selection_policy is None:
        selection_policy = {"enabled": True, "required_terms": set(), "context_terms": set(), "blocked_terms": set(), "minimum_required_matches": 1}
    if not selection_policy.get("enabled", True):
        return {}

    # Try semantic + aesthetic scoring from YAML catalog
    if catalog_yaml_path and os.path.exists(catalog_yaml_path):
        try:
            with open(catalog_yaml_path) as f:
                yaml_catalog = yaml.safe_load(f)
            return _select_supp_refs_semantic(
                yaml_catalog, max_per_pid, brand_domain_tags,
                selection_policy=selection_policy,
            )
        except Exception:
            pass  # Fall through to keyword-based scoring

    # Fallback: keyword-overlap scoring (original behavior)
    return _select_supp_refs_keyword(catalog, brand_tags, max_per_pid, selection_policy=selection_policy)


def _select_supp_refs_semantic(yaml_catalog, max_per_pid, brand_domain_tags, selection_policy=None):
    """Select supplementary refs using semantic gates + aesthetic tiebreaker."""
    entries = yaml_catalog.get("entries", {})
    brand_domains = set(brand_domain_tags)
    selection_policy = selection_policy or {}
    required_terms = set(selection_policy.get("required_terms", set()))
    context_terms = set(selection_policy.get("context_terms", set()))
    blocked_terms = set(selection_policy.get("blocked_terms", set()))
    min_required_matches = selection_policy.get("minimum_required_matches", 1)

    # Build primary ref profiles for aesthetic comparison
    primary_profiles = {}
    for entry_id, entry in entries.items():
        if entry.get("type") == "primary" and entry.get("prompt_id"):
            primary_profiles[entry["prompt_id"]] = entry.get("aesthetic", {})

    result = {}
    for pid in _NANO_BANANA_PIDS:
        target_profile = primary_profiles.get(pid)
        if not target_profile:
            continue

        pid_subject = _PID_SUBJECT_TYPES.get(pid, "")
        is_layout = pid in _LAYOUT_PIDS

        candidates = []
        for entry_id, entry in entries.items():
            if entry.get("type") == "primary":
                continue
            if pid not in entry.get("asset_compatibility", []):
                continue

            entry_terms = _entry_ref_terms(entry_id, entry)
            blocked_matches = blocked_terms.intersection(entry_terms)
            if blocked_matches:
                continue

            required_matches = required_terms.intersection(entry_terms)
            if required_terms and len(required_matches) < min_required_matches:
                continue

            # Gate 1: Domain filter
            entry_domains = set(entry.get("domain_suitability", []))
            if entry_domains and brand_domains:
                if not entry_domains.intersection(brand_domains):
                    continue  # No domain overlap → skip

            # Gate 2: Subject type filter (layout PIDs exempt)
            if not is_layout and pid_subject:
                entry_subject = entry.get("subject_type", "")
                if entry_subject and entry_subject != pid_subject:
                    # Allow close matches: multi-product ↔ single-product
                    product_types = {"multi-product", "single-product", "flatlay"}
                    if not ({entry_subject, pid_subject} <= product_types):
                        continue

            # Score by aesthetic distance
            entry_profile = entry.get("aesthetic", {})
            dist = _aesthetic_distance(target_profile, entry_profile)
            similarity = round(1.0 / (1.0 + dist), 3)
            context_matches = context_terms.intersection(entry_terms)
            relevance = (len(required_matches) * 10) + len(context_matches)
            candidates.append({
                "file": entry.get("file", ""),
                "score": similarity,
                "relevance": relevance,
                "_domains": list(entry_domains),
            })

        # Diversity slot assignment for multi-domain brands
        if brand_domains and len(brand_domains) >= 3 and candidates:
            result[pid] = _fill_domain_diverse_slots(
                candidates, brand_domains, max_per_pid,
            )
        else:
            candidates.sort(key=lambda x: (-x["relevance"], -x["score"], x["file"]))
            if candidates:
                result[pid] = [
                    {"file": c["file"], "score": c["score"]}
                    for c in candidates[:max_per_pid]
                ]

    return result


def _fill_domain_diverse_slots(candidates, brand_domains, max_slots):
    """Fill slots ensuring domain diversity, then backfill with best aesthetic.

    For multi-domain brands (3+ tags), try to pick one ref per domain tag
    to showcase breadth. Remaining slots filled by best aesthetic score.
    """
    used_files = set()
    selected = []

    # Pass 1: one per domain (best aesthetic within each domain)
    for domain in sorted(brand_domains):
        domain_cands = [
            c for c in candidates
            if domain in c.get("_domains", []) and c["file"] not in used_files
        ]
        if domain_cands:
            best = max(domain_cands, key=lambda x: (x.get("relevance", 0), x["score"]))
            selected.append({"file": best["file"], "score": best["score"]})
            used_files.add(best["file"])
            if len(selected) >= max_slots:
                break

    # Pass 2: backfill remaining slots with best overall aesthetic
    if len(selected) < max_slots:
        remaining = sorted(
            [c for c in candidates if c["file"] not in used_files],
            key=lambda x: (-x.get("relevance", 0), -x["score"], x["file"]),
        )
        for c in remaining:
            selected.append({"file": c["file"], "score": c["score"]})
            if len(selected) >= max_slots:
                break

    return selected


def _select_supp_refs_keyword(catalog, brand_tags, max_per_pid=3, selection_policy=None):
    """Fallback: score catalog entries via keyword overlap."""
    selection_policy = selection_policy or {}
    required_terms = set(selection_policy.get("required_terms", set()))
    context_terms = set(selection_policy.get("context_terms", set()))
    blocked_terms = set(selection_policy.get("blocked_terms", set()))
    min_required_matches = selection_policy.get("minimum_required_matches", 1)
    result = {}
    for pid, context_tags in _PID_CONTEXT.items():
        scored = []
        search_terms = set(t.lower() for t in context_tags + brand_tags if t)
        for entry in catalog:
            if not entry.get("file"):
                continue
            entry_terms = set(_extract_ref_terms(
                entry.get("file", ""),
                entry.get("description", ""),
                entry.get("tags", []),
            ))
            if blocked_terms.intersection(entry_terms):
                continue
            required_matches = required_terms.intersection(entry_terms)
            if required_terms and len(required_matches) < min_required_matches:
                continue
            score = 0.0
            entry_text = " ".join(entry.get("tags", []) + [entry.get("description", ""), entry["file"]]).lower()
            for term in search_terms:
                if term in entry_text:
                    score += 1.0
            score += len(required_matches) * 10
            score += len(context_terms.intersection(entry_terms))
            if entry.get("related_pid") == pid:
                score += 2.0
            if entry.get("type") == "style":
                score += 0.5
            if score > 0:
                scored.append({"file": entry["file"], "score": score})
        scored.sort(key=lambda x: -x["score"])
        if scored:
            result[pid] = scored[:max_per_pid]
    return result


def build_ref_images_block(ref_images_dict):
    """Build the REF_IMAGES block for embedding in generated scripts.

    Returns a plain Python dict literal string.  Replacement values
    injected via .format_map() are NOT re-processed, so we use single
    braces here (NOT escaped doubles).
    """
    lines = ["REF_IMAGES = {"]
    for pid in sorted(ref_images_dict.keys(), key=_sort_pid):
        lines.append(f'    "{pid}": "{ref_images_dict[pid]}",')
    lines.append("}")
    return "\n".join(lines)


def build_supp_refs_block(supp_refs_dict):
    """Build the SUPP_REFS block for embedding in generated scripts.

    Returns a plain Python dict literal string (single braces).
    """
    lines = ["SUPP_REFS = {"]
    for pid in sorted(supp_refs_dict.keys(), key=_sort_pid):
        files = [e["file"] for e in supp_refs_dict[pid]]
        lines.append(f'    "{pid}": {files!r},')
    lines.append("}")
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
        "priority_assets": {"2A", "2B", "2C", "5A", "5B"},
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


# =====================================================================
# DOMAIN-AWARE VISUAL CONCEPT DEFAULTS
# =====================================================================
# Maps brand domain_tags to appropriate visual defaults.
# Replaces the previous Tryambakam Noesis-specific hardcoded fallbacks.

DOMAIN_CONCEPTS = {
    "saas": {
        "hero_object_type": "digital product interface",
        "hero_surface": "clean matte desk surface",
        "seal_material": "Brushed aluminum",
        "seal_geometry": "Clean geometric precision",
        "logo_treatment": "embossed",
        "logo_substrate": "matte metallic surface",
        "panel_structure": "Clean interface elements with subtle grid patterns",
        "icon_line_style": "Minimal geometric linework with consistent stroke weight",
        "poster_artifact": "digital product artifact",
        "poster_filament": "subtle gradient light trails",
        "poster_border": "Clean minimal border frame",
        "engraving_style": "modern line engraving",
        "seeker_inner_detail": "data flow patterns, interface wireframe elements",
        "sequence_type": "sequential product usage narrative",
        "sequence_constraint": "screen-focused",
        "product_hero_name": "product",
        "product_hero_description": "flagship digital product",
        "product_hero_physical": "laptop screen displaying product dashboard with clean UI",
        "product_capsule_1": "product interface on laptop screen",
        "product_capsule_2": "mobile app companion view",
        "product_capsule_3": "branded merchandise item",
        "product_essence_name": "product",
        "product_essence_container": "Sleek device showing product interface with branded elements",
        "product_essence_size": "standard",
    },
    "marketplace": {
        "hero_object_type": "curated marketplace scene",
        "hero_surface": "warm textured surface",
        "seal_material": "Brushed brass",
        "seal_geometry": "Modern geometric precision",
        "logo_treatment": "embossed",
        "logo_substrate": "premium textured card stock",
        "panel_structure": "Warm architectural elements with ambient lighting",
        "icon_line_style": "Warm minimal linework with rounded accents",
        "poster_artifact": "handcrafted marketplace artifact",
        "poster_filament": "warm ambient light trails",
        "poster_border": "Warm modern border frame",
        "engraving_style": "artisan line engraving",
        "seeker_inner_detail": "connection pathways, discovery network patterns",
        "sequence_type": "sequential discovery narrative",
        "sequence_constraint": "lifestyle-focused",
        "product_hero_name": "experience",
        "product_hero_description": "curated marketplace experience",
        "product_hero_physical": "smartphone showing marketplace app with curated selections",
        "product_capsule_1": "marketplace app interface on phone",
        "product_capsule_2": "curated selection showcase",
        "product_capsule_3": "branded companion card",
        "product_essence_name": "discovery",
        "product_essence_container": "Curated selection box with branded tissue and card",
        "product_essence_size": "standard",
    },
    "dtc": {
        "hero_object_type": "premium retail product",
        "hero_surface": "clean studio surface",
        "seal_material": "Metallic foil",
        "seal_geometry": "Refined geometric precision",
        "logo_treatment": "foil-stamped",
        "logo_substrate": "premium packaging surface",
        "panel_structure": "Clean product display elements with studio lighting",
        "icon_line_style": "Clean refined linework with brand-consistent weight",
        "poster_artifact": "premium product artifact",
        "poster_filament": "product highlight accents",
        "poster_border": "Elegant minimal border frame",
        "engraving_style": "refined line engraving",
        "seeker_inner_detail": "product craftsmanship details, material textures",
        "sequence_type": "sequential unboxing narrative",
        "sequence_constraint": "product-focused",
        "product_hero_name": "product",
        "product_hero_description": "flagship retail product",
        "product_hero_physical": "premium packaged product with branded box and tissue",
        "product_capsule_1": "primary product with packaging",
        "product_capsule_2": "companion accessory item",
        "product_capsule_3": "branded gift item",
        "product_essence_name": "product",
        "product_essence_container": "Premium branded container with clean label design",
        "product_essence_size": "standard",
    },
    "food": {
        "hero_object_type": "artisan food product",
        "hero_surface": "natural wood or stone surface",
        "seal_material": "Wax seal",
        "seal_geometry": "Organic rounded precision",
        "logo_treatment": "letterpress",
        "logo_substrate": "kraft or textured paper",
        "panel_structure": "Natural organic elements with warm ambient lighting",
        "icon_line_style": "Hand-drawn organic linework with natural curves",
        "poster_artifact": "artisan food artifact",
        "poster_filament": "warm steam and aroma trails",
        "poster_border": "Natural rustic border frame",
        "engraving_style": "woodcut-style engraving",
        "seeker_inner_detail": "ingredient textures, preparation process details",
        "sequence_type": "sequential preparation narrative",
        "sequence_constraint": "hands-only cooking",
        "product_hero_name": "product",
        "product_hero_description": "artisan food product",
        "product_hero_physical": "artisan food product in branded packaging on natural surface",
        "product_capsule_1": "primary food product with packaging",
        "product_capsule_2": "companion flavor or variety",
        "product_capsule_3": "branded serving accessory",
        "product_essence_name": "essence",
        "product_essence_container": "Small artisan jar with branded label and natural lid",
        "product_essence_size": "standard",
    },
    "wellness": {
        "hero_object_type": "wellness product",
        "hero_surface": "natural stone or wood surface",
        "seal_material": "Matte ceramic",
        "seal_geometry": "Soft organic precision",
        "logo_treatment": "debossed",
        "logo_substrate": "natural matte surface",
        "panel_structure": "Serene organic elements with soft natural lighting",
        "icon_line_style": "Flowing organic linework with gentle curves",
        "poster_artifact": "wellness ritual artifact",
        "poster_filament": "soft ambient glow trails",
        "poster_border": "Soft organic border frame",
        "engraving_style": "botanical line engraving",
        "seeker_inner_detail": "energy flow patterns, botanical elements",
        "sequence_type": "sequential wellness ritual narrative",
        "sequence_constraint": "hands-only",
        "product_hero_name": "product",
        "product_hero_description": "premium wellness product",
        "product_hero_physical": "wellness product in minimal branded packaging with natural elements",
        "product_capsule_1": "primary wellness product",
        "product_capsule_2": "companion wellness item",
        "product_capsule_3": "branded wellness accessory",
        "product_essence_name": "essence",
        "product_essence_container": "Frosted glass bottle with minimal branded dropper cap",
        "product_essence_size": "30ml",
    },
    "fashion": {
        "hero_object_type": "fashion product",
        "hero_surface": "polished studio surface",
        "seal_material": "Embossed leather",
        "seal_geometry": "Sharp angular precision",
        "logo_treatment": "foil-embossed",
        "logo_substrate": "leather or satin surface",
        "panel_structure": "Editorial fashion elements with dramatic lighting",
        "icon_line_style": "Sharp angular linework with fashion-forward precision",
        "poster_artifact": "fashion editorial artifact",
        "poster_filament": "dramatic light streaks",
        "poster_border": "Editorial fashion border frame",
        "engraving_style": "fashion illustration engraving",
        "seeker_inner_detail": "textile patterns, construction detail elements",
        "sequence_type": "sequential editorial styling narrative",
        "sequence_constraint": "styling-focused",
        "product_hero_name": "piece",
        "product_hero_description": "signature fashion piece",
        "product_hero_physical": "fashion item draped on premium surface with editorial styling",
        "product_capsule_1": "signature garment or accessory",
        "product_capsule_2": "companion fashion piece",
        "product_capsule_3": "branded fashion accessory",
        "product_essence_name": "fragrance",
        "product_essence_container": "Sculptural glass bottle with branded cap and embossed label",
        "product_essence_size": "50ml",
    },
    "education": {
        "hero_object_type": "educational product",
        "hero_surface": "clean desk surface",
        "seal_material": "Matte metal",
        "seal_geometry": "Clean structured precision",
        "logo_treatment": "embossed",
        "logo_substrate": "premium paper surface",
        "panel_structure": "Structured learning elements with clear visual hierarchy",
        "icon_line_style": "Clean structured linework with educational clarity",
        "poster_artifact": "knowledge artifact",
        "poster_filament": "connecting knowledge pathways",
        "poster_border": "Structured academic border frame",
        "engraving_style": "academic line engraving",
        "seeker_inner_detail": "knowledge maps, learning pathway diagrams",
        "sequence_type": "sequential learning progression narrative",
        "sequence_constraint": "study-focused",
        "product_hero_name": "course",
        "product_hero_description": "flagship educational product",
        "product_hero_physical": "branded course materials with workbook and digital access card",
        "product_capsule_1": "primary course workbook",
        "product_capsule_2": "companion reference guide",
        "product_capsule_3": "branded notebook or tool",
        "product_essence_name": "toolkit",
        "product_essence_container": "Compact branded toolkit box with embossed label",
        "product_essence_size": "standard",
    },
}

# Truly generic fallback — no domain-specific assumptions
_GENERIC_DEFAULTS = {
    "hero_object_type": "brand product",
    "hero_surface": "clean surface",
    "seal_material": "Metallic",
    "seal_geometry": "Clean geometric precision",
    "logo_treatment": "embossed",
    "logo_substrate": "textured premium surface",
    "panel_structure": "Clean design elements with balanced lighting",
    "icon_line_style": "Clean minimal linework with consistent stroke weight",
    "poster_artifact": "brand artifact",
    "poster_filament": "subtle accent light trails",
    "poster_border": "Clean minimal border frame",
    "engraving_style": "refined line engraving",
    "seeker_inner_detail": "brand pattern details, structural elements",
    "sequence_type": "sequential brand narrative",
    "sequence_constraint": "lifestyle-focused",
    "product_hero_name": "product",
    "product_hero_description": "flagship brand product",
    "product_hero_physical": "premium branded product on clean surface with studio lighting",
    "product_capsule_1": "primary brand product",
    "product_capsule_2": "companion product item",
    "product_capsule_3": "branded accessory",
    "product_essence_name": "product",
    "product_essence_container": "Compact branded container with clean label design",
    "product_essence_size": "standard",
}


def resolve_domain_defaults(cfg):
    """Derive visual concept defaults from brand domain_tags and archetype.

    Priority: first matching domain_tag in DOMAIN_CONCEPTS, else generic.
    """
    domain_tags = cfg.get("brand", {}).get("domain_tags", [])
    channel = cfg.get("execution_context", {}).get("launch_channel", "")

    # Check domain_tags first (most specific)
    for tag in domain_tags:
        tag_lower = tag.lower()
        if tag_lower in DOMAIN_CONCEPTS:
            return DOMAIN_CONCEPTS[tag_lower]

    # Fall back to launch channel (less specific)
    if channel in DOMAIN_CONCEPTS:
        return DOMAIN_CONCEPTS[channel]

    return dict(_GENERIC_DEFAULTS)


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


LEGACY_PRODUCT_PROMPT_IDS = {
    "hero_book": "hero_product",
    "essence_vial": "product_detail",
}


def normalize_product_prompt_ids(cfg):
    """Normalize legacy product prompt ids in config in-place."""
    products = cfg.get("prompts", {}).get("products", [])
    if not isinstance(products, list):
        return []
    replacements = []
    normalized = []
    for item in products:
        mapped = LEGACY_PRODUCT_PROMPT_IDS.get(item, item)
        if mapped != item:
            replacements.append((item, mapped))
        if mapped not in normalized:
            normalized.append(mapped)
    cfg.setdefault("prompts", {})["products"] = normalized
    return replacements



def validate_product_spec_consistency(cfg):
    """Return high-signal product-spec contradictions that should stop generation."""
    errors = []
    products = cfg.get("products", {})
    hero = products.get("hero", {})
    hero_blob = " ".join(
        str(v) for v in [hero.get("name", ""), hero.get("description", ""), hero.get("physical_form", "")]
    ).lower()
    flatlay_items = products.get("flatlay_objects", {}).get("items", [])
    flatlay_blob = " ".join(str(item) for item in flatlay_items).lower()
    materials_blob = " ".join(str(item) for item in cfg.get("materials", [])).lower()
    negative_blob = str(cfg.get("negative_prompt", "")).lower()
    photo_constraint = str(cfg.get("photography", {}).get("constraint", "")).lower()
    prompt_products = [str(p).lower() for p in cfg.get("prompts", {}).get("products", [])]

    screen_banned = any(term in negative_blob or term in photo_constraint for term in ["no screens", "screen", "phone", "tablet", "laptop", "monitor", "tv"])
    screen_instructions = any(term in flatlay_blob for term in ["phone", "screen", "tablet", "laptop", "monitor", "tv"])
    if screen_banned and screen_instructions:
        errors.append(
            "Conflicting screen instructions: the config bans visible screens, but products.flatlay_objects.items still includes a phone/screen device."
        )

    mentions_usb_c = any("usb-c" in blob for blob in [hero_blob, flatlay_blob, materials_blob])
    mentions_dock = any(term in blob for blob in [hero_blob, flatlay_blob, materials_blob] for term in ["charging dock", "charging pad", "charging station"])
    if mentions_usb_c and mentions_dock:
        errors.append(
            "Conflicting charging instructions: the product is described with USB-C charging, but other fields still describe a charging dock/pad/station."
        )

    plush_like = any(term in hero_blob for term in ["plush", "stuffed", "soft toy", "toy", "cat-like ears", "creature"])
    legacy_prompt_ids = {legacy for legacy in LEGACY_PRODUCT_PROMPT_IDS if legacy in prompt_products}
    if plush_like and legacy_prompt_ids:
        errors.append(
            "Legacy product prompt ids remain in prompts.products for a plush/toy product: "
            + ", ".join(sorted(legacy_prompt_ids))
        )

    return errors



def build_product_spec_lock(cfg, *, primary_name, primary_hex, negative_prompt):
    """Build a canonical product-spec lock string injected into product-facing prompts."""
    products = cfg.get("products", {})
    hero = products.get("hero", {})
    detail = products.get("detail") or products.get("essence") or {}
    if not isinstance(detail, dict):
        detail = {"description": str(detail)}
    materials = cfg.get("materials", [])
    flatlay_items = products.get("flatlay_objects", {}).get("items", [])

    hero_name = hero.get("name", "the product")
    hero_physical = hero.get("physical_form") or hero.get("description") or ""
    detail_focus = (
        detail.get("focus")
        or detail.get("description")
        or hero.get("description")
        or hero_physical
    )

    accessories = []
    for item in flatlay_items:
        item_text = str(item).strip()
        if not item_text:
            continue
        if any(token in item_text.lower() for token in ["phone", "screen", "tablet", "laptop", "monitor", "tv"]):
            continue
        accessories.append(item_text)
    accessories_text = ", ".join(accessories[:5]) if accessories else "only the accessories shown in the approved product references"

    neg_lower = str(negative_prompt).lower()
    bans = []
    if "teddy bear" in neg_lower or "bear shape" in neg_lower:
        bans.append("teddy bear / bear silhouette")
    if any(term in neg_lower for term in ["screen", "phone", "tablet", "laptop", "monitor", "tv"]):
        bans.append("screens or phone/tablet devices")
    if "charging dock" in neg_lower or "charging pad" in neg_lower or "charging station" in neg_lower:
        bans.append("charging dock / charging pad")
    elif "usb-c" in hero_physical.lower():
        bans.append("charging dock / charging pad")
    if "robot" in neg_lower or "metallic" in neg_lower:
        bans.append("robotic hard-surface body")
    if "cat-like ears" in hero_physical.lower():
        bans.append("missing cat-like ears")

    bans_text = ", ".join(dict.fromkeys(bans)) if bans else "no substitutions or accessory inventions"
    return (
        f"SPEC LOCK: Depict only {hero_name}. Exact physical form: {hero_physical}. "
        f"Signature color anchor: {primary_name} ({primary_hex}). "
        f"Detail focus: {detail_focus}. "
        f"Allowed accessories only: {accessories_text}. "
        f"Hard bans: {bans_text}. "
        "Match the uploaded product reference photos exactly in silhouette, face details, materials, ports, and included accessories."
    )



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

    # ── Domain-aware defaults (replaces hardcoded Noesis fallbacks) ──
    dd = resolve_domain_defaults(cfg)

    # ── Products (domain-aware fallbacks) ──
    prods = cfg.get("products", {})
    hero = prods.get("hero", {})
    v["product_hero_name"] = hero.get("name", dd["product_hero_name"])
    v["product_hero_description"] = hero.get("description", dd["product_hero_description"])
    v["product_hero_physical"] = hero.get("physical_form", dd["product_hero_physical"])

    capsule = prods.get("capsule_lineup", [])
    if len(capsule) >= 3:
        v["product_capsule_1"] = capsule[0].get("description", "primary product")
        v["product_capsule_2"] = capsule[1].get("description", "companion piece")
        v["product_capsule_3"] = capsule[2].get("description", "brand accessory")
    elif len(capsule) >= 1:
        descs = [c.get("description", "brand product") for c in capsule]
        while len(descs) < 3:
            descs.append("brand product")
        v["product_capsule_1"], v["product_capsule_2"], v["product_capsule_3"] = descs
    else:
        v["product_capsule_1"] = dd["product_capsule_1"]
        v["product_capsule_2"] = dd["product_capsule_2"]
        v["product_capsule_3"] = dd["product_capsule_3"]

    detail = prods.get("detail") or prods.get("essence") or {}
    if not isinstance(detail, dict):
        detail = {"description": str(detail)}
    v["product_detail_name"] = detail.get("name", hero.get("name", dd["product_hero_name"]))
    v["product_detail_focus"] = (
        detail.get("focus")
        or detail.get("description")
        or hero.get("description", dd["product_hero_description"])
    )

    flatlay = prods.get("flatlay_objects", {})
    v["product_flatlay_count"] = str(flatlay.get("count", 5))
    flatlay_items = flatlay.get("items", [])
    v["product_flatlay_description"] = ", ".join(flatlay_items) if flatlay_items else "brand objects"

    v["product_category"] = prods.get("category", "lifestyle product")
    v["product_spec_lock"] = build_product_spec_lock(
        cfg,
        primary_name=v["primary_name"],
        primary_hex=v["primary_hex"],
        negative_prompt=neg,
    )

    # ── Aesthetic language overrides (domain-aware defaults) ──
    aes = cfg.get("aesthetic", {})
    v["hero_object_type"] = aes.get("hero_object_type", dd["hero_object_type"])
    v["hero_surface"] = aes.get("hero_surface", dd["hero_surface"])
    v["seal_material"] = aes.get("seal_material", dd["seal_material"])
    v["seal_geometry"] = aes.get("seal_geometry", dd["seal_geometry"])
    v["logo_treatment"] = aes.get("logo_treatment", dd["logo_treatment"])
    v["logo_substrate"] = aes.get("logo_substrate", dd["logo_substrate"])
    v["panel_structure"] = aes.get("panel_structure", dd["panel_structure"])
    v["icon_line_style"] = aes.get("icon_line_style", dd["icon_line_style"])
    v["poster_artifact"] = aes.get("poster_artifact", dd["poster_artifact"])
    v["poster_filament"] = aes.get("poster_filament", dd["poster_filament"])
    v["poster_border"] = aes.get("poster_border", dd["poster_border"])
    v["quality_reference"] = aes.get("quality_reference", "Behance Trend / Awwwards Winner")
    v["engraving_style"] = aes.get("engraving_style", dd["engraving_style"])
    v["seeker_inner_detail"] = aes.get("seeker_inner_detail", dd["seeker_inner_detail"])
    v["sequence_type"] = aes.get("sequence_type", dd["sequence_type"])
    v["sequence_constraint"] = aes.get("sequence_constraint", dd["sequence_constraint"])
    v["8a_title_text"] = aes.get("poster_title_text", "THE SEEKER")
    v["8a_subject_directive"] = aes.get(
        "poster_subject_directive",
        "A solitary figure seen from behind -- standing still, contemplative posture.\nNo face visible. Full body, centered in frame.",
    )
    v["8a_left_half_detail"] = aes.get(
        "poster_left_half_detail",
        f"hand texture, fabric weave, polished floor, {v['photo_environment']} visible behind.",
    )
    v["8a_right_half_detail"] = aes.get(
        "poster_right_half_detail",
        "engineering nodes at key body points, network patterns from feet.",
    )

    # ── Aesthetic variant structural holes (Phase D) ──
    # All default to "" — overridden by aesthetic engine with variant-specific text.
    # Purely additive: empty string = current prompt unchanged = zero regression.
    for _k in [
        "2b_composition_style", "2b_finish_approach", "2b_atmosphere",
        "2c_render_approach", "2c_atmosphere",
        "3a_composition_approach", "3a_lighting_note", "3a_atmosphere",
        "3b_composition_style", "3b_lighting_note", "3b_atmosphere",
        "3c_composition_style", "3c_lighting_approach", "3c_atmosphere",
        "4a_layout_approach", "4a_panel_note", "4a_atmosphere",
        "4b_arrangement_style", "4b_lighting_approach", "4b_atmosphere",
        "5a_illustration_approach", "5a_rendering_style", "5a_atmosphere",
        "5b_grid_approach", "5b_type_c_style", "5b_atmosphere",
        "5c_composition_approach", "5c_color_treatment", "5c_atmosphere",
        "7a_grid_approach", "7a_moment_style", "7a_atmosphere",
        "8a_composition_approach", "8a_split_style", "8a_atmosphere",
    ]:
        v[_k] = ""

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
    v["inference_endpoint"] = str(gen.get("inference_endpoint", "https://api.inference.sh")).strip()
    v["inference_app"] = str(gen.get("inference_app", "")).strip()
    v["brandmint_repo_root"] = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

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
import os, sys, subprocess
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.claude/.env"))

BRAND_NAME = "{brand_name}"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "{output_subdir}")
os.makedirs(OUT_DIR, exist_ok=True)

# Ensure generated scripts can import local brandmint package adapters.
BRANDMINT_REPO_ROOT = "{brandmint_repo_root}"
if BRANDMINT_REPO_ROOT and os.path.isdir(BRANDMINT_REPO_ROOT) and BRANDMINT_REPO_ROOT not in sys.path:
    sys.path.insert(0, BRANDMINT_REPO_ROOT)

# Skill reference images directory (composition references for Nano Banana Pro)
SKILL_REF_DIR = os.path.expanduser("~/.claude/skills/brandmint/references/images")

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================
# Supports: fal, openrouter, openai, replicate, inference
# All generation goes through core provider adapters.

PROVIDER = os.environ.get("IMAGE_PROVIDER", "{provider}").lower()
SUPPORTED_PROVIDERS = {{"fal", "openrouter", "openai", "replicate", "inference"}}
if PROVIDER not in SUPPORTED_PROVIDERS:
    print(f"WARNING: Unknown provider '{{PROVIDER}}', defaulting to FAL.")
    PROVIDER = "fal"

INFERENCE_ENDPOINT = "{inference_endpoint}".strip()
if INFERENCE_ENDPOINT:
    os.environ.setdefault("INFERENCE_BASE_URL", INFERENCE_ENDPOINT)
INFERENCE_APP = "{inference_app}".strip()
if INFERENCE_APP:
    os.environ.setdefault("INFERENCE_IMAGE_APP", INFERENCE_APP)

try:
    from brandmint.core.providers import get_provider as _bm_get_provider
except Exception as e:
    print(f"ERROR: Failed to import core provider adapters: {{e}}")
    sys.exit(1)

try:
    CORE_PROVIDER = _bm_get_provider(PROVIDER)
except Exception as e:
    print(f"ERROR: Provider '{{PROVIDER}}' is not available: {{e}}")
    sys.exit(1)

print(f"Using image provider: {{PROVIDER.upper()}}")

NEGATIVE = """{negative_prompt}"""

# Brand logo file (for visual reference injection — empty if no logo configured)
LOGO_PATH = "{logo_primary_path}"

def upload_reference(path):
    """Resolve a local reference path; provider adapters handle upload semantics."""
    if not path or not os.path.exists(path):
        return None
    return os.path.abspath(path)

_logo_url_cache = None
def get_logo_url():
    """Upload brand logo once and cache the URL for reuse."""
    global _logo_url_cache
    if _logo_url_cache:
        return _logo_url_cache
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        print(f"  Uploading brand logo: {{os.path.basename(LOGO_PATH)}}")
        _logo_url_cache = upload_reference(LOGO_PATH)
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
            uploaded = upload_reference(p)
            if uploaded:
                _product_ref_url_cache.append(uploaded)
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


# Supplementary composition references (dynamically selected from full catalog)
{supp_refs_block}

_supp_ref_url_cache = {{}}
def get_supp_ref_images(pid, limit=3):
    """Get supplementary composition reference URLs for a prompt ID.

    Uploads images on first call, caches for reuse.
    Returns list of uploaded URLs (may be empty).
    """
    if pid in _supp_ref_url_cache:
        return _supp_ref_url_cache[pid]
    urls = []
    for fname in SUPP_REFS.get(pid, [])[:limit]:
        path = os.path.join(SKILL_REF_DIR, fname)
        if os.path.exists(path):
            print(f"  Uploading supp ref: {{os.path.basename(path)}}")
            uploaded = upload_reference(path)
            if uploaded:
                urls.append(uploaded)
    _supp_ref_url_cache[pid] = urls
    return urls


REFERENCE_POLICY = os.environ.get("BRANDMINT_REFERENCE_POLICY", "error").strip().lower()
if REFERENCE_POLICY not in {"error", "warn", "off"}:
    print(f"WARNING: Unknown BRANDMINT_REFERENCE_POLICY '{{REFERENCE_POLICY}}', defaulting to error.")
    REFERENCE_POLICY = "error"


def _existing_reference_paths(pid):
    """Return local reference files that should anchor a Nano Banana generation."""
    expected = []
    if pid != "2A":
        style_anchor = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")
        if os.path.exists(style_anchor):
            expected.append(style_anchor)
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        expected.append(LOGO_PATH)
    expected.extend([p for p in PRODUCT_REF_PATHS if os.path.exists(p)])
    ref_path = get_ref_image(pid)
    if ref_path:
        expected.append(ref_path)
    for fname in SUPP_REFS.get(pid, [])[:3]:
        path = os.path.join(SKILL_REF_DIR, fname)
        if os.path.exists(path):
            expected.append(path)

    deduped = []
    seen = set()
    for path in expected:
        apath = os.path.abspath(path)
        if apath in seen:
            continue
        seen.add(apath)
        deduped.append(apath)
    return deduped



def enforce_reference_payload(pid, image_urls):
    """Prevent ref-capable Nano Banana steps from silently degrading to text-only."""
    if REFERENCE_POLICY == "off":
        return
    expected = _existing_reference_paths(pid)
    provided = [url for url in (image_urls or []) if url]
    if not expected or provided:
        return

    names = ", ".join(os.path.basename(path) for path in expected[:5])
    message = (
        f"[{{pid}}] Reference payload missing despite available refs: {{names}}. "
        "This Nano Banana step would degrade to text-only generation."
    )
    if REFERENCE_POLICY == "warn":
        print(f"WARNING: {{message}}")
        return
    raise RuntimeError(message)


def _normalize_png_if_needed(filepath):
    """Convert JPEG/WebP/SVG payloads into PNG when output path expects PNG."""
    if not filepath.endswith(".png") or not os.path.exists(filepath):
        return
    with open(filepath, "rb") as f:
        header = f.read(64)
    if header.startswith(b"\\x89PNG"):
        return

    try:
        if header[:2] == b"\\xff\\xd8" or header[:4] == b"RIFF":
            subprocess.run(
                ["sips", "-s", "format", "png", filepath, "--out", filepath],
                check=True,
                capture_output=True,
            )
            return

        head_text = header.decode("utf-8", errors="ignore").lstrip().lower()
        if head_text.startswith("<?xml") or "<svg" in head_text:
            tmp_svg = filepath + ".svg.tmp"
            os.replace(filepath, tmp_svg)
            try:
                subprocess.run(
                    ["rsvg-convert", "-w", "2048", "-h", "2048", "--keep-aspect-ratio", tmp_svg, "-o", filepath],
                    check=True,
                    capture_output=True,
                )
            finally:
                if os.path.exists(tmp_svg):
                    os.remove(tmp_svg)
            return
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  WARNING: failed to normalize image payload at {{filepath}}: {{e}}")


def gen_with_provider(
    prompt,
    model,
    output_path,
    width=1024,
    height=1024,
    image_url=None,
    image_urls=None,
    negative_prompt="",
    **kwargs,
):
    """Generate with core provider adapters only."""
    if CORE_PROVIDER is None:
        return False

    primary_ref = image_url
    if primary_ref is None and isinstance(image_urls, list) and image_urls:
        primary_ref = image_urls[0]

    result = CORE_PROVIDER.generate(
        prompt=prompt,
        model=model,
        output_path=output_path,
        width=width,
        height=height,
        image_url=primary_ref,
        negative_prompt=negative_prompt,
        image_urls=image_urls,
        **kwargs,
    )
    if not (result and result.success):
        err = result.error if result else "unknown adapter error"
        print(f"  ERROR: generation failed for {{model}} via {{PROVIDER}}: {{err}}")
        return False

    _normalize_png_if_needed(output_path)
    if os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024
        print(f"  Saved: {{os.path.basename(output_path)}} ({{size_kb:.0f}} KB)")
    return True

'''

FUNC_NANO_BANANA = '''
def gen_nano_banana(pid, slug, prompt, aspect, image_urls, seeds=({seed_a}, {seed_b})):
    """Generate with Nano Banana Pro via unified core provider adapter path."""
    full_prompt = f"{{prompt}}\\n\\nAvoid: {{NEGATIVE}}"
    enforce_reference_payload(pid, image_urls)
    
    # Parse aspect ratio to get dimensions
    aspect_dims = {{"16:9": (1792, 1024), "9:16": (1024, 1792), "1:1": (1024, 1024), 
                   "3:4": (896, 1152), "4:3": (1152, 896)}}
    w, h = aspect_dims.get(aspect, (1024, 1024))
    
    for seed in seeds:
        variant = "v1" if seed == {seed_a} else f"v{{seed}}"
        out_path = os.path.join(OUT_DIR, f"{{pid}}-{{slug}}-nanobananapro-{{variant}}.png")
        print(f"\\n  [{{pid}}] Nano Banana Pro seed={{seed}} (provider: {{PROVIDER}})...")
        gen_with_provider(
            full_prompt,
            "nano-banana-pro",
            out_path,
            w,
            h,
            image_urls=image_urls,
            negative_prompt="",
            seed=seed,
            aspect_ratio=aspect,
            resolution="2K",
            output_format="png",
            num_images=1,
        )

'''

FUNC_FLUX_PRO = '''
def gen_flux_pro(pid, slug, prompt, aspect, seeds=({seed_a}, {seed_b})):
    """Generate with Flux 2 Pro via unified core provider adapter path."""
    full_prompt = f"{{prompt}}\\n\\nAvoid: {{NEGATIVE}}"
    
    # Parse aspect to dimensions
    aspect_dims = {{"landscape_16_9": (1792, 1024), "portrait_9_16": (1024, 1792), 
                   "square": (1024, 1024), "portrait_3_4": (896, 1152), "landscape_4_3": (1152, 896)}}
    w, h = aspect_dims.get(aspect, (1024, 1024))
    
    for seed in seeds:
        variant = "v1" if seed == {seed_a} else f"v{{seed}}"
        out_path = os.path.join(OUT_DIR, f"{{pid}}-{{slug}}-flux2pro-{{variant}}.png")
        print(f"\\n  [{{pid}}] Flux 2 Pro seed={{seed}} (provider: {{PROVIDER}})...")
        gen_with_provider(
            full_prompt,
            "flux-2-pro",
            out_path,
            w,
            h,
            negative_prompt="",
            seed=seed,
            image_size=aspect,
            num_images=1,
        )

'''

FUNC_RECRAFT = '''
def gen_recraft(pid, slug, prompt, style, colors, size, seeds=({seed_a}, {seed_b})):
    """Generate with Recraft V3 via unified core provider adapter path."""
    size_dims = {{"square": (1024, 1024), "landscape_16_9": (1792, 1024), 
                 "portrait_9_16": (1024, 1792), "1024x1024": (1024, 1024)}}
    w, h = size_dims.get(size, (1024, 1024))
    
    for seed in seeds:
        variant = "v1" if seed == {seed_a} else f"v{{seed}}"
        out_path = os.path.join(OUT_DIR, f"{{pid}}-{{slug}}-recraft-{{variant}}.png")
        print(f"\\n  [{{pid}}] Recraft V3 ({{style}}) seed={{seed}} (provider: {{PROVIDER}})...")
        gen_with_provider(
            prompt,
            "recraft-v3",
            out_path,
            w,
            h,
            negative_prompt="",
            seed=seed,
            image_size=size,
            style=style,
            colors=colors,
        )

'''


# =====================================================================
# PROMPT TEMPLATES (parameterized with {variables})
# =====================================================================

PROMPT_2A_BENTO = """{brand_name} ({domain}).
{tone_preamble} "Brand Identity System" presentation ({2a_layout_format}).
Core metaphor: {theme_metaphor}. Mood: {mood_keywords}.

Generate a single high-resolution {2a_layout_format} board containing {2a_module_count}:

PHASE 1: VISUAL STRATEGY
1. Analyze the Brand: Archetype = "{archetype}" -- {voice}.
   Visual vibe = {theme_name}, {theme_description}.
   Visual territory: {occupy_territory}.
2. Define the Palette: {color_directive}
   {primary_name} {primary_hex}, {secondary_name} {secondary_hex},
   {accent_name} {accent_hex}, {support_name} {support_hex}.
3. Select Typography: {2a_typography_treatment}

PHASE 2: THE LAYOUT
{2a_layout_blocks}

PHASE 3: AESTHETIC & FINISH
{2a_lighting}. {2a_shadow_quality}. Quality: {quality}. {detail_suffix}
{2a_spatial_instruction} {platform_note}
Atmosphere: {2a_atmosphere}."""

PROMPT_2B_SEAL = """{brand_name} brand seal emblem. {2b_composition_style}{seal_material} circular seal
with {seal_geometry}. Central sigil: {sigil_description}.
Typography: "{brand_name}" around perimeter in {header_font} {header_display_weight}, {header_case}.
Below sigil: "{brand_tagline}" in {body_font}. Material: {seal_material} with
{accent_name} ({accent_hex}) patina highlights. Background: solid {primary_name}
({primary_hex}). {color_directive} {2b_finish_approach}Clean, architectural, precision-engineered. {quality} detail.
{2b_atmosphere}{detail_suffix}"""

PROMPT_2C_LOGO = """{brand_name} {logo_treatment} logo emboss. {2c_render_approach}The brand sigil
({sigil_description}) rendered as a {logo_substrate} with
{accent_name} ({accent_hex}) leading between colored glass segments.
Colors: {primary_hex}, {accent_hex}, {signal_hex}. Backlit with warm diffused
light creating colored shadows on {secondary_name} ({secondary_hex}) surface below.
"{brand_name}" wordmark in {header_font} SemiBold below. {2c_atmosphere}8K detail."""

PROMPT_3A_CAPSULE = """{brand_name} capsule collection product lineup.
{product_spec_lock}
Three products in a row on {hero_surface}: {product_capsule_1},
{product_capsule_2}, and {product_capsule_3}.
{3a_composition_approach}
Materials: {materials_list}. Environment: {photo_environment}.
{photo_style}. {3a_lighting_note}{photo_constraint}. Camera: {photo_camera}. {quality} detail.
Color palette: {color_directive} {primary_hex} deep shadows, {secondary_hex} highlights,
{accent_hex} reflections, {signal_hex} living accents.
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}.
{3a_atmosphere}{detail_suffix}"""

PROMPT_3B_HERO = """{brand_name} hero product shot. {product_hero_physical}.
{product_spec_lock}
{3b_composition_style}Sitting on {hero_surface}. {photo_style}. Environment: {photo_environment}.
{3b_lighting_note}{photo_constraint}. Camera: {photo_camera}. Materials: {materials_list}.
{3b_atmosphere}8K."""

PROMPT_3C_DETAIL = """{brand_name} product detail close-up.
{product_spec_lock}
Focus on {product_detail_name}: {product_detail_focus}. {3c_composition_style}Tight framing on the approved product only.
No substitute objects, no invented accessories, no alternate device class. Pure solid
{primary_name} ({primary_hex}) background. {3c_lighting_approach}Sharp high-contrast lighting from above.
{accent_name} highlight, {secondary_name} edge-glow.
{3c_atmosphere}{photo_constraint}. 8K."""

PROMPT_4A_CATALOG = """{brand_name} product design catalog page. {4a_layout_approach}Top section:
{product_spec_lock}
{product_category} image inside {photo_environment}. {accent_name} ({accent_hex})
light filtering through. Bottom section: {4a_panel_note}technical specification panel with
architectural line drawings in {accent_name} on {primary_name} background.
Fine hairline technical lines with measurement callouts in {data_font}.
Material swatches panel: {materials_list}. {photo_style}. {color_directive}
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}.
{4a_atmosphere}{quality}.{detail_suffix}"""

PROMPT_4B_FLATLAY = """{brand_name} product collection flat-lay. {product_flatlay_count} objects
{product_spec_lock}
{4b_arrangement_style}arranged on {hero_surface} in precise architectural spacing: {product_flatlay_description}. Materials:
{materials_list}. Overhead composition. Each object casting a single sharp shadow.
{4b_lighting_approach}Lighting: directional from upper left with warm {accent_name} ({accent_hex})
temperature. Cool {secondary_name} ({secondary_hex}) fill from below.
{photo_constraint}. {photo_style}. {color_directive}
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}.
{4b_atmosphere}{quality} quality.{detail_suffix}"""

PROMPT_5A_HERITAGE = """{brand_name} {engraving_style} logomark. {illus_style}.
{5a_illustration_approach}Thin delicate hairlines in organic curves. Airy, precise, no heavy borders.
Central sigil: {sigil_description}. {sigil_components}. {5a_rendering_style}Rendered as
botanical-scientific diagram. "{brand_name}" in geometric serif ({header_font}
style), wide spacing. Below: "EST. MMXXVI" lighter weight. {secondary_name}
({secondary_hex}) paper. {primary_name} ({primary_hex}) lines. {accent_name}
({accent_hex}) accent on borders. {5a_atmosphere}"""

PROMPT_5B_CAMPAIGN = """{brand_name} Campaign Visual Identity Grid. {5b_grid_approach}2-column
asymmetrical layout. Full bleed, zero spacing between tiles.
Core metaphor: {theme_metaphor}. Visual territory: {occupy_territory}.
TYPE A: Solid {primary_name} ({primary_hex}) background with pattern at 5% opacity,
centered sigil in {secondary_name} ({secondary_hex}).
TYPE B: {accent_name} ({accent_hex}) background, "{brand_tagline}" in {header_font}
{header_emphasis_weight}, {secondary_name} text.
{5b_type_c_style}TYPE C: High-contrast duotone photographs using {primary_hex} + {accent_hex}.
Materials: {materials_list}. {photo_constraint}. Typography: {header_font} ONLY.
{color_directive} Every photo unique. {illus_style}.
{5b_atmosphere}{detail_suffix}"""

PROMPT_5C_PANEL = """{brand_name} conceptual panel illustration. {illus_style}.
{5c_composition_approach}{illus_references}. Core metaphor: {theme_metaphor}. Mood: {mood_keywords}.
{5c_color_treatment}Flowing organic lines, flat color planes in {primary_name}
({primary_hex}), {accent_name} ({accent_hex}), and {signal_name} ({signal_hex}).
{color_directive} Decorative border of flowing curves and organic tendrils. Grounded figure on
{hero_surface}. {panel_structure}
glowing {secondary_name}. No mystical imagery. Paper texture: warm, fibrous.
{5c_atmosphere}"""

PROMPT_7A_CONTACT = """{brand_name} editorial contact sheet. {7a_grid_approach}3x3 grid, 9 panels,
{product_spec_lock}
{sequence_constraint} lifestyle photography inside {photo_environment}. No face -- only hands
and forearms. Same hands all panels. {7a_moment_style}9 panels showing different moments of
{sequence_type} with brand products. Materials: {materials_list}.
Camera: {photo_camera}. {photo_environment} light. {accent_name} ({accent_hex})
highlights. 2px {support_name} ({support_hex}) borders. {quality} detail.
Audience aesthetic: {audience_aesthetic}. Must feel like it belongs in the world of {audience_aspiration}.
{7a_atmosphere}{detail_suffix}"""

PROMPT_8A_SEEKER = """{brand_name} "{8a_title_text}" brand presence poster.
Core metaphor: {theme_metaphor}.
{8a_composition_approach}{8a_subject_directive}
{8a_split_style}SPLIT COMPOSITION: LEFT HALF shows material reality -- ultra-photorealistic detail:
{8a_left_half_detail}
RIGHT HALF shows inner architecture -- translucent technical blueprint revealing:
{seeker_inner_detail} glowing {secondary_name} ({secondary_hex}),
{8a_right_half_detail}
The split line glows {accent_name} ({accent_hex}).
COLOR: {color_directive} {primary_name} dominant, {accent_name} highlights, {secondary_name} inner glow,
{signal_name} ({signal_hex}) for living elements. Film grain.
Typography: "{8a_title_text}" in {header_font} {header_display_weight}, {support_name} ({support_hex}).
Audience aesthetic: {audience_aesthetic}. Emotional register: {emotional_register}.
{8a_atmosphere}{detail_suffix}"""

PROMPT_9A_ENGINE = """{brand_name} campaign poster. Single {{object}} centered on
{{bg_color}} ({{bg_hex}}) background. {product_spec_lock}
The object rendered as physical {poster_artifact}
artifact -- part {{material_a}}, part {{material_b}}, with {poster_filament}
glowing {secondary_name} ({secondary_hex}). {poster_border} in
{accent_name} ({accent_hex}). Typography bottom third: "{{engine_name}}" in
{header_font} Bold, all caps, {secondary_name} ({secondary_hex}).
Below: "{{tagline}}" in {header_font} Light, {support_name} ({support_hex}).
Bottom: "{brand_name}" in {body_font} Regular. Dramatic top-down spotlight. 8K."""

PROMPT_10_SEQUENCE = """{brand_name} "{{sequence_title}}" {sequence_type}.
{product_spec_lock}
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
{product_spec_lock}
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
{product_spec_lock}
"{hero_headline}" in {header_font} {header_display_weight}, {header_case},
{secondary_name} ({secondary_hex}) text. {primary_name} ({primary_hex}) background.
{color_directive} Presentation-quality, cinematic. {quality}.""",

    "twitter_header": """{brand_name} Twitter/X header banner. 1500x500 panoramic.
PRODUCT: {product_hero_name} -- {product_hero_physical}.
The product must match the reference photos exactly. Do NOT substitute with any other device.
{product_spec_lock}
"{brand_tagline}" in {header_font} {header_emphasis_weight}.
Brand mark right-aligned: {sigil_description}.
{color_directive} {primary_name} overlay gradient. Cinematic. {quality}.""",

    "email_hero": """{brand_name} email header hero image. 600px wide landscape composition.
PRODUCT: {product_hero_name} -- {product_hero_physical}.
The product must match the reference photos exactly. Do NOT substitute with any other device.
{product_spec_lock}
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
        ref_url = upload_reference(ref_path)
        if ref_url:
            image_urls.append(ref_url)
    else:
        print("\\nNo composition reference found for 2A (optional).")

    # Add brand logo as visual reference if available
    logo_url = get_logo_url()
    if logo_url:
        image_urls.append(logo_url)

    # Product reference images help the anchor stay faithful to the hero object.
    for purl in get_product_ref_urls():
        image_urls.append(purl)

    # Add supplementary composition references
    image_urls.extend(get_supp_ref_images("2A"))

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
    """Generate generate-products.py (3A capsule + 3B hero + 3C product detail + domain-specific)."""
    asset_ids = _get_asset_ids(asset_groups, "products", {"3A", "3B", "3C"})
    if not asset_ids:
        return

    seeds = cfg["generation"].get("seeds", [42, 137])
    prompt_3a = render(PROMPT_3A_CAPSULE, v)
    prompt_3b = render(PROMPT_3B_HERO, v)
    prompt_3c = render(PROMPT_3C_DETAIL, v)
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
    func_nb = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})
    func_flux = render(FUNC_FLUX_PRO, {"seed_a": seeds[0], "seed_b": seeds[1]})

    # Always set up style anchor (3A/3B/3C all use Nano Banana Pro now)
    nb_setup = '''
    # Style anchor for Nano Banana Pro assets
    image_urls = []
    anchor_path = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")
    if os.path.exists(anchor_path):
        anchor_url = upload_reference(anchor_path)
        if anchor_url:
            image_urls.append(anchor_url)
    logo_url = get_logo_url()
    if logo_url:
        image_urls.append(logo_url)
    # Product reference images for model accuracy
    for purl in get_product_ref_urls():
        image_urls.append(purl)
'''

    gen_3a = '''
    # 3A with composition reference
    print("\\n--- 3A: Capsule Collection (Nano Banana Pro) ---")
    urls_3a = list(image_urls)
    ref_3a = get_ref_image("3A")
    if ref_3a:
        print(f"  Adding composition ref: {os.path.basename(ref_3a)}")
        ref_url = upload_reference(ref_3a)
        if ref_url:
            urls_3a.append(ref_url)
    urls_3a.extend(get_supp_ref_images("3A"))
    gen_nano_banana("3A", "capsule-collection", PROMPT_3A, "4:3", urls_3a)
''' if "3A" in asset_ids else ""
    gen_3b = '''
    # 3B with composition reference
    print("\\n--- 3B: Hero Product (Nano Banana Pro) ---")
    urls_3b = list(image_urls)
    ref_3b = get_ref_image("3B")
    if ref_3b:
        print(f"  Adding composition ref: {os.path.basename(ref_3b)}")
        ref_url = upload_reference(ref_3b)
        if ref_url:
            urls_3b.append(ref_url)
    urls_3b.extend(get_supp_ref_images("3B"))
    gen_nano_banana("3B", "hero-product", PROMPT_3B, "1:1", urls_3b)
''' if "3B" in asset_ids else ""
    gen_3c = '''
    # 3C uses the style anchor + actual product reference photos only.
    print("\\n--- 3C: Product Detail (Nano Banana Pro) ---")
    urls_3c = list(image_urls)
    gen_nano_banana("3C", "product-detail", PROMPT_3C, "1:1", urls_3c)
''' if "3C" in asset_ids else ""

    main_body = f'''
PROMPT_3A = """{prompt_3a}"""

PROMPT_3B = """{prompt_3b}"""

PROMPT_3C = """{prompt_3c}"""
{new_prompt_defs}

def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Product Concepts")
    print("Model: Nano Banana Pro")
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
        ref_url = upload_reference(ref_4a)
        if ref_url:
            urls_4a.append(ref_url)
    urls_4a.extend(get_supp_ref_images("4A"))
    gen_nano_banana("4A", "catalog-layout", PROMPT_4A, "3:4", urls_4a)
''' if "4A" in asset_ids else ""

    gen_4b = '''
    # 4B with composition reference
    print("\\n--- 4B: Flatlay (Nano Banana Pro) ---")
    urls_4b = list(anchor_urls)
    ref_4b = get_ref_image("4B")
    if ref_4b:
        print(f"  Adding composition ref: {os.path.basename(ref_4b)}")
        ref_url = upload_reference(ref_4b)
        if ref_url:
            urls_4b.append(ref_url)
    urls_4b.extend(get_supp_ref_images("4B"))
    gen_nano_banana("4B", "flatlay", PROMPT_4B, "1:1", urls_4b)
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
        anchor_url = upload_reference(STYLE_ANCHOR)
        if anchor_url:
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
    """Generate generate-illustrations.py (5A-5C)."""
    asset_ids = _get_asset_ids(asset_groups, "illustrations", {"5A", "5B", "5C"})
    if not asset_ids:
        return

    seeds = cfg["generation"].get("seeds", [42, 137])
    # Condense for Recraft 1000-char limit
    prompt_5a = render(PROMPT_5A_HERITAGE, v)[:990]
    prompt_5b = render(PROMPT_5B_CAMPAIGN, v)
    prompt_5c = render(PROMPT_5C_PANEL, v)[:990]
    out_sub = cfg["generation"].get("output_dir", "generated")
    script_desc = "Illustrations"

    header = render(SCRIPT_HEADER, {
        **v, "script_desc": script_desc,
        "output_subdir": out_sub,
    })
    func_rc = render(FUNC_RECRAFT, {"seed_a": seeds[0], "seed_b": seeds[1]})
    func_nb = render(FUNC_NANO_BANANA, {"seed_a": seeds[0], "seed_b": seeds[1]})
    func_flux = ""

    prompt_defs = []
    if "5A" in asset_ids:
        prompt_defs.append(f'PROMPT_5A = """{prompt_5a}"""')
    if "5B" in asset_ids:
        prompt_defs.append(f'PROMPT_5B = """{prompt_5b}"""')
    if "5C" in asset_ids:
        prompt_defs.append(f'PROMPT_5C = """{prompt_5c}"""')
    prompt_defs_block = "\n\n".join(prompt_defs)
    recraft_prompt_items = []
    if "5A" in asset_ids:
        recraft_prompt_items.append('"5A": PROMPT_5A')
    if "5C" in asset_ids:
        recraft_prompt_items.append('"5C": PROMPT_5C')
    recraft_prompt_map = "{%s}" % ", ".join(recraft_prompt_items) if recraft_prompt_items else "{}"

    main_body = f'''
{prompt_defs_block}

STYLE_ANCHOR = os.path.join(OUT_DIR, "2A-brand-kit-bento-nanobananapro-v1.png")


def main():
    print("=" * 60)
    print(f"{{BRAND_NAME}} -- Illustrations")
    print("=" * 60)

    # Verify Recraft prompt lengths
    for pid, p in {recraft_prompt_map}.items():
        if pid not in {sorted(asset_ids)!r}:
            continue
        count = len(p)
        status = "OK" if count < 1000 else "OVER LIMIT"
        print(f"  {{pid}}: {{count}} chars [{{status}}]")
        if count >= 1000:
            print("ERROR: Prompt exceeds 1000 char Recraft V3 limit before submission.")
            sys.exit(1)

'''
    if "5A" in asset_ids:
        main_body += f'''
    # 5A: Heritage Engraving (Recraft digital_illustration)
    print("\\n--- 5A: Heritage Engraving (Recraft V3 digital) ---")
    gen_recraft("5A", "heritage-engraving", PROMPT_5A,
                "digital_illustration",
                ["{v['primary_hex']}", "{v['secondary_hex']}", "{v['accent_hex']}"],
                "square_hd")
'''

    if "5B" in asset_ids:
        main_body += '''
    # 5B: Campaign Grid (Nano Banana Pro + anchor + comp ref)
    print("\\n--- 5B: Campaign Grid (Nano Banana Pro) ---")
    anchor_urls = []
    if os.path.exists(STYLE_ANCHOR):
        anchor_url = upload_reference(STYLE_ANCHOR)
        if anchor_url:
            anchor_urls = [anchor_url]
    logo_url = get_logo_url()
    if logo_url:
        anchor_urls.append(logo_url)
    ref_5b = get_ref_image("5B")
    if ref_5b:
        print(f"  Adding composition ref: {os.path.basename(ref_5b)}")
        ref_url = upload_reference(ref_5b)
        if ref_url:
            anchor_urls.append(ref_url)
    anchor_urls.extend(get_supp_ref_images("5B"))
    gen_nano_banana("5B", "campaign-grid", PROMPT_5B, "3:4", anchor_urls)
'''

    if "5C" in asset_ids:
        main_body += f'''
    # 5C: Art Panel (Recraft digital_illustration)
    print("\\n--- 5C: Art Panel (Recraft V3 digital) ---")
    gen_recraft("5C", "art-panel", PROMPT_5C,
                "digital_illustration",
                ["{v['primary_hex']}", "{v['accent_hex']}", "{v['signal_hex']}"],
                "portrait_4_3")
'''

    main_body += '''
    print("\\n" + "=" * 60)
    print("  ILLUSTRATIONS COMPLETE")
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
        comp_url = upload_reference(ref_7a)
        if comp_url:
            image_urls.append(comp_url)
    image_urls.extend(get_supp_ref_images("7A"))

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
        anchor_url = upload_reference(STYLE_ANCHOR)
        if anchor_url:
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
    excluded_assets = set(cfg.get("generation", {}).get("excluded_assets", []) or [])

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
        engines_list = [
            eng for eng in engines.get("engines", [])
            if eng.get("id", "9A") not in excluded_assets
        ]
        sequences_list = [
            seq for seq in engines.get("sequences", [])
            if seq.get("id", "10A") not in excluded_assets
        ]
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
    # 8A: Brand presence poster (with composition reference)
    print("\\n--- 8A: Brand Presence Poster ---")
    urls_8a = list(image_urls)
    ref_8a = get_ref_image("8A")
    if ref_8a:
        print(f"  Adding composition ref: {{os.path.basename(ref_8a)}}")
        ref_url = upload_reference(ref_8a)
        if ref_url:
            urls_8a.append(ref_url)
    urls_8a.extend(get_supp_ref_images("8A"))
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
        anchor_url = upload_reference(STYLE_ANCHOR)
        if anchor_url:
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
            ref_url = upload_reference(ref_9a)
            if ref_url:
                urls_9a.append(ref_url)
        urls_9a.extend(get_supp_ref_images("9A"))
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
            ref_url = upload_reference(ref_10)
            if ref_url:
                urls_10.append(ref_url)
        urls_10.extend(get_supp_ref_images("10A"))
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
    ]

    # ── Aesthetic Intelligence section (only when engine ran) ──────────────
    aes = v.get("aesthetic_profile_summary")
    if aes:
        # Score bar helper: 0.0-1.0 → visual bar of 10 chars
        def _bar(score):
            filled = round(score * 10)
            return "█" * filled + "░" * (10 - filled)

        # Map of asset_prefix → display name for rationale table
        asset_display = {
            "2a": "2A Brand Kit Bento Grid", "2b": "2B Brand Seal",
            "2c": "2C Logo Emboss",          "3a": "3A Capsule Collection",
            "3b": "3B Hero Product",          "3c": "3C Product Detail",
            "4a": "4A Catalog Layout",        "4b": "4B Flatlay",
            "5a": "5A Heritage Engraving",    "5b": "5B Campaign Grid",
            "5c": "5C Art Panel",             "7a": "7A Contact Sheet",
            "8a": "8A Brand Presence Poster",
        }

        # Register → human-readable description
        register_desc = {
            "heritage-craft":      "Dense craft detail, material textures, ancestral temporal register",
            "minimal-zen":         "Sparse negative space, restrained palette, refined visual boldness",
            "futuristic-editorial":"Cold precision, technical overlays, speculative temporal register",
            "bold-commercial":     "High contrast, strong calls-to-action, conversion-optimised framing",
            "natural-editorial":   "Organic materials, editorial pacing, natural-contemporary register",
            "ornate-traditional":  "Rich ornamentation, high density, heritage-adjacent visual grammar",
            "minimal-futuristic":  "Clean lines, low density, forward-looking minimal aesthetic",
            "rich-editorial":      "Dense editorial layering, high material richness, contemporary depth",
            "balanced-contemporary":"Moderate across all axes — versatile contemporary aesthetic",
        }
        reg = aes["register"]
        reg_note = register_desc.get(reg, "Balanced multi-axis profile")
        conf_pct = int(aes["confidence"] * 100)

        lines.extend([
            "---",
            "",
            "## Aesthetic Intelligence",
            "",
            f"> **Register:** `{reg}` ({conf_pct}% confidence) — {reg_note}",
            "",
            "### Axis Scores",
            "",
            "| Axis | Score | Visualisation |",
            "|------|------:|--------------|",
            f"| Composition Density     | {aes['density']:.2f} | `{_bar(aes['density'])}` |",
            f"| Temporal Register       | {aes['temporal']:.2f} | `{_bar(aes['temporal'])}` |",
            f"| Material Richness       | {aes['material']:.2f} | `{_bar(aes['material'])}` |",
            f"| Visual Boldness         | {aes['boldness']:.2f} | `{_bar(aes['boldness'])}` |",
            f"| Editorial vs Commercial | {aes['commercial']:.2f} | `{_bar(aes['commercial'])}` |",
            "",
        ])

        if aes.get("signals"):
            lines.extend([
                "### Classification Signals",
                "",
                "| Source | Signal |",
                "|--------|--------|",
            ])
            for sig in aes["signals"]:
                # signals are "source:value" strings (e.g. "archetype:cultural guardian")
                if isinstance(sig, dict):
                    src = sig.get("source", "—"); val = sig.get("value", "—")
                elif ":" in str(sig):
                    src, _, val = str(sig).partition(":")
                else:
                    src = "signal"; val = str(sig)
                lines.append(f"| `{src}` | {val} |")
            lines.append("")

        # Per-asset variant selection rationale
        lines.extend([
            "### Template Variant Selection",
            "",
            "| Asset | Variant | Rationale |",
            "|-------|---------|-----------|",
        ])
        for prefix, display in asset_display.items():
            variant_id  = v.get(f"variant_selection_{prefix}", "—")
            description = v.get(f"variant_description_{prefix}", "")
            if variant_id != "—":
                lines.append(f"| {display} | `{variant_id}` | {description} |")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Prompts",
        "",
    ])

    prompt_entries = [
        ("2A", "Brand Kit Bento Grid", "fal-ai/nano-banana-pro", "16:9", PROMPT_2A_BENTO),
        ("2B", "Brand Seal", "fal-ai/flux-2-pro", "1:1", PROMPT_2B_SEAL),
        ("2C", "Logo Emboss", "fal-ai/flux-2-pro", "16:9", PROMPT_2C_LOGO),
        ("3A", "Capsule Collection", "fal-ai/nano-banana-pro", "4:3", PROMPT_3A_CAPSULE),
        ("3B", "Hero Product", "fal-ai/nano-banana-pro", "1:1", PROMPT_3B_HERO),
        ("3C", "Product Detail", "fal-ai/nano-banana-pro", "1:1", PROMPT_3C_DETAIL),
        ("4A", "Catalog Layout", "fal-ai/nano-banana-pro", "3:4", PROMPT_4A_CATALOG),
        ("4B", "Flatlay", "fal-ai/nano-banana-pro", "1:1", PROMPT_4B_FLATLAY),
        ("5A", "Heritage Engraving", "fal-ai/recraft/v3", "1:1", PROMPT_5A_HERITAGE),
        ("5B", "Campaign Grid", "fal-ai/nano-banana-pro", "3:4", PROMPT_5B_CAMPAIGN),
        ("5C", "Art Panel", "fal-ai/recraft/v3", "3:4", PROMPT_5C_PANEL),
        ("7A", "Contact Sheet", "fal-ai/nano-banana-pro", "1:1", PROMPT_7A_CONTACT),
        ("8A", "Brand Presence Poster", "fal-ai/nano-banana-pro", "3:4", PROMPT_8A_SEEKER),
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

    # ── Supplementary Composition References section ──
    supp_refs = v.get("_supp_refs_summary", {})
    if supp_refs:
        lines.extend([
            "---", "",
            "## Supplementary Composition References", "",
            "> Dynamically selected from the full reference catalog based on brand context.", "",
        ])
        for pid in sorted(supp_refs.keys(), key=_sort_pid):
            refs = supp_refs[pid]
            lines.append(f"### {pid}")
            for ref in refs:
                lines.append(f"- `{ref['file']}` (score: {ref['score']:.1f})")
            lines.append("")

    # ── Community Prompts section (from Twitter sync) ──
    twitter_refs = v.get("_twitter_refs", [])
    if twitter_refs:
        lines.extend([
            "---",
            "",
            "## Community Prompts (Twitter Sync)",
            "",
            f"> {len(twitter_refs)} prompts sourced from high-signal tweets.",
            "",
        ])
        for tw in twitter_refs:
            tags_str = ", ".join(tw.get("tags", [])) or "untagged"
            img_count = len(tw.get("images", []))
            lines.extend([
                f"### @{tw['author']} — {tw['slug']}",
                "",
                f"- **Likes**: {tw.get('likes', 0)} | **Score**: {tw.get('relevance_score', 0):.2f}",
                f"- **Tags**: {tags_str}",
                f"- **Images**: {img_count}",
                "",
            ])
            prompt_text = tw.get("prompt_text", "")
            if prompt_text:
                lines.extend([
                    "```",
                    prompt_text[:2000],  # Cap at 2000 chars
                    "```",
                    "",
                ])
        lines.append("")

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
    excluded_assets = set(cfg.get("generation", {}).get("excluded_assets", []) or [])

    # Cost per call by model
    costs = {"nano-banana-pro": 0.08, "flux-2-pro": 0.05, "recraft-v3": 0.04}

    assets = []

    # If we have domain-aware asset_groups, use those for the base asset list
    if asset_groups is not None:
        for gen_name, group in asset_groups.items():
            for aid, adef in group:
                if aid in excluded_assets:
                    continue
                model = adef.get("model", "nano-banana-pro")
                cost_key = model if model in costs else "nano-banana-pro"
                sc = seeds_count
                if aid == "8A" and depth != "surface":
                    sc = seeds_count + 1  # Brand poster gets extra seed
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
        if "2A" not in excluded_assets:
            assets.append({"id": "2A", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 2B, 2C: Flux 2 Pro
        for pid in ["2B", "2C"]:
            if pid not in skip_ids and pid not in excluded_assets:
                assets.append({"id": pid, "model": "flux-2-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["flux-2-pro"]})
        # 3A, 3B, 3C: Nano Banana Pro
        for pid in ["3A", "3B", "3C"]:
            if pid not in skip_ids and pid not in excluded_assets:
                assets.append({"id": pid, "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 4A, 4B: Nano Banana Pro
        if "4A" not in skip_ids and "4A" not in excluded_assets:
            assets.append({"id": "4A", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        if "4B" not in skip_ids and "4B" not in excluded_assets:
            assets.append({"id": "4B", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 5A, 5C: Recraft
        for pid in ["5A", "5C"]:
            if pid not in skip_ids and pid not in excluded_assets:
                assets.append({"id": pid, "model": "recraft-v3", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["recraft-v3"]})
        # 5B: Nano Banana
        if "5B" not in skip_ids and "5B" not in excluded_assets:
            assets.append({"id": "5B", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 7A: Nano Banana
        if "7A" not in skip_ids and "7A" not in excluded_assets:
            assets.append({"id": "7A", "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})
        # 8A: Nano Banana (extra seed for seeker at non-surface depths)
        if "8A" not in skip_ids and "8A" not in excluded_assets:
            seeker_seeds = seeds_count + 1 if depth != "surface" else seeds_count
            assets.append({"id": "8A", "model": "nano-banana-pro", "seeds": seeker_seeds, "calls": seeker_seeds, "est_cost": seeker_seeds * costs["nano-banana-pro"]})

    # Config-driven assets (always added regardless of mode — 9A engines, 10A-C sequences)
    engines = cfg.get("prompts", {}).get("posters", {})
    engines_list = engines.get("engines", []) if isinstance(engines, dict) else []
    for eng in engines_list:
        eid = eng.get("id", "9A")
        if eid not in skip_ids and eid not in excluded_assets:
            assets.append({"id": eid, "model": "nano-banana-pro", "seeds": 1, "calls": 1, "est_cost": costs["nano-banana-pro"]})
    sequences_list = engines.get("sequences", []) if isinstance(engines, dict) else []
    for seq in sequences_list:
        sid = seq.get("id", "10A")
        if sid not in skip_ids and sid not in excluded_assets:
            assets.append({"id": sid, "model": "nano-banana-pro", "seeds": seeds_count, "calls": seeds_count, "est_cost": seeds_count * costs["nano-banana-pro"]})

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
    normalized_prompt_ids = normalize_product_prompt_ids(cfg)
    if normalized_prompt_ids:
        print("  Normalized legacy product prompt ids: " + ", ".join(f"{old}->{new}" for old, new in normalized_prompt_ids))

    validation_errors = validate_product_spec_consistency(cfg)
    if validation_errors:
        print("\n  ERROR: Product-spec validation failed:")
        for err in validation_errors:
            print(f"    - {err}")
        sys.exit(1)

    exec_ctx = load_execution_context(config_path, cfg)
    v = build_vars(cfg, exec_ctx, config_path=config_path)

    # ── Aesthetic Engine: dynamic template variant selection ──────────────
    # Maps brand archetype/mood/materials → AestheticProfile → variant per asset.
    # Runs in try/except: pipeline falls back to legacy behavior on any error.
    try:
        _ae_dir = os.path.dirname(os.path.abspath(__file__))
        import sys as _sys
        if _ae_dir not in _sys.path:
            _sys.path.insert(0, _ae_dir)
        from aesthetic_engine import (
            AestheticClassifier, TemplateMatcher, inject_variant_vars,
            load_template_variants, load_upstream_data, write_aesthetic_sidecar,
        )
        _variants_path = os.path.join(_ae_dir, "..", "assets", "template-variants.yaml")
        _registry = load_template_variants(os.path.abspath(_variants_path))
        if _registry:
            _upstream = load_upstream_data(config_path)
            _classifier = AestheticClassifier()
            _matcher = TemplateMatcher()
            _profile = _classifier.classify(v, _upstream)
            _aesthetic_overrides = cfg.get("aesthetic", {})
            _selections = _matcher.select_variants(_profile, _registry, _aesthetic_overrides)
            v = inject_variant_vars(v, _selections, _registry, _profile)
            write_aesthetic_sidecar(config_path, _profile, _selections)
            print(f"  Aesthetic: {_profile.dominant_register} "
                  f"(density={_profile.composition_density:.2f}, "
                  f"temporal={_profile.temporal_register:.2f}, "
                  f"confidence={_profile.confidence:.2f})")
            print(f"  Variants:  " + ", ".join(f"{k}={s}" for k, s in sorted(_selections.items())))
        else:
            print("  Aesthetic: template-variants.yaml not found — using legacy prompts")
    except Exception as _ae_err:
        print(f"  Aesthetic: engine error ({_ae_err}) — using legacy prompts")

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
                cmd = [sys.executable, mapper_script, images_dir, "--json-only"]
                # Auto-pass twitter assets dir if it exists
                twitter_dir = os.path.join(os.path.dirname(ref_map_path), "twitter-sync", "assets")
                if os.path.isdir(twitter_dir):
                    cmd.extend(["--twitter-dir", twitter_dir])
                subprocess.run(cmd, check=True)
                print("  Reference map refreshed.")
            else:
                print(f"  WARNING: map_references.py not found at {mapper_script}")
        else:
            print(f"  WARNING: references/images/ not found at {images_dir}")

    ref_images, full_catalog = load_ref_map(ref_map_path)
    if os.path.exists(ref_map_path):
        print(f"  Refs: Loaded {len(ref_images)} mappings from reference-map.json")
        if full_catalog:
            print(f"  Catalog: {len(full_catalog)} supplementary refs available")
        # Load twitter community refs for cookbook
        try:
            with open(ref_map_path) as _rmf:
                _ref_data = json.load(_rmf)
            twitter_refs = _ref_data.get("twitter", [])
            if twitter_refs:
                v["_twitter_refs"] = twitter_refs
                print(f"  Twitter: {len(twitter_refs)} community prompts available for cookbook")
        except (json.JSONDecodeError, OSError):
            pass
    else:
        print(f"  Refs: Using {len(ref_images)} hardcoded defaults (no reference-map.json found)")
    v["ref_images_block"] = build_ref_images_block(ref_images)

    # Select supplementary refs based on brand context
    brand_tags = [
        v.get("domain", ""),
        v.get("archetype", ""),
        *[t.strip() for t in v.get("mood_keywords", "").split(",") if t.strip()],
    ]
    catalog_yaml_path = os.path.join(os.path.dirname(ref_map_path), "reference-catalog.yaml")
    brand_domain_tags = v.get("domain_tags", [])
    if isinstance(brand_domain_tags, str):
        brand_domain_tags = [t.strip() for t in brand_domain_tags.split(",") if t.strip()]
    supp_ref_policy = _derive_supp_ref_policy(cfg)
    supp_refs = select_supp_refs(
        full_catalog, brand_tags,
        catalog_yaml_path=catalog_yaml_path,
        brand_domain_tags=brand_domain_tags,
        selection_policy=supp_ref_policy,
    ) if full_catalog or os.path.exists(catalog_yaml_path) else {}
    if supp_refs:
        total_supp = sum(len(refs) for refs in supp_refs.values())
        print(f"  Supp refs: {total_supp} supplementary refs selected across {len(supp_refs)} prompts")
    else:
        print("  Supp refs: no brand-relevant supplementary refs selected")
    v["supp_refs_block"] = build_supp_refs_block(supp_refs)
    v["_supp_refs_summary"] = supp_refs

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
    excluded_assets = cfg.get("generation", {}).get("excluded_assets", []) or []

    asset_groups = None  # None = legacy mode
    if domain_tags:
        try:
            from asset_registry import select_assets, get_assets_by_generator, print_selection_summary
            selected = select_assets(domain_tags, depth, channel, excluded_assets=excluded_assets)
            asset_groups = get_assets_by_generator(selected)
            print_selection_summary(selected, domain_tags, depth, channel)
            if excluded_assets:
                print(f"  Excluded assets: {sorted(excluded_assets)}")
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
