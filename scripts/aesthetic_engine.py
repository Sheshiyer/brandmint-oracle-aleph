"""
Brandmint Aesthetic Engine
--------------------------
Dynamic template variant selection based on brand aesthetic profile.

Architecture:
  AestheticClassifier  — maps brand config → AestheticProfile (5 axis scores)
  TemplateMatcher      — maps AestheticProfile → {asset_id: variant_id}
  inject_variant_vars  — augments v dict with variant-specific template variables

The system is intentionally rules-based (zero ML, zero API calls, <1ms):
  - Deterministic: same config always produces same variant selection
  - Transparent: cookbook shows exact scoring reasoning
  - Editable: weight tables in YAML (future) or ARCHETYPE/MOOD/MATERIAL_WEIGHTS dicts

Integration:
  Called from generate_pipeline.py main() after build_vars().
  Runs in a try/except — pipeline falls back to legacy behavior on any error.

Phase status:
  Phase A: stub returning all defaults, zero behavioral change
  Phase B: full weight tables for all known archetypes + keywords
  Phase C: 2A gains 4 real structural variants, PROMPT_2A_BENTO updated
  Phase D (complete): all 13 assets have full variant coverage, all PROMPT templates updated
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


# ============================================================
# AESTHETIC PROFILE
# ============================================================

@dataclass
class AestheticProfile:
    """5-axis brand aesthetic classification result.

    Each axis is a float 0.0–1.0:
      0.0 = left/low pole
      0.5 = center/balanced (default for unknown brands)
      1.0 = right/high pole
    """

    # Axis 1: How densely composed are the visuals?
    composition_density: float = 0.5    # 0=sparse/zen  →  1=dense/ornate

    # Axis 2: Where on the time spectrum does the brand live?
    temporal_register: float = 0.5      # 0=speculative/futuristic  →  1=heritage/ancestral

    # Axis 3: How material/craft-intensive is the brand?
    material_richness: float = 0.5      # 0=synthetic/minimal  →  1=natural/craft-intensive

    # Axis 4: How visually bold or dramatic?
    visual_boldness: float = 0.5        # 0=subtle/refined  →  1=bold/architectural

    # Axis 5: Editorial positioning vs conversion optimization?
    editorial_vs_commercial: float = 0.5  # 0=editorial  →  1=commercial/conversion

    # Classification metadata
    dominant_register: str = "balanced-contemporary"
    confidence: float = 0.5
    signal_sources: List[str] = field(default_factory=list)
    archetype_cluster: str = ""


# ============================================================
# AESTHETIC CLASSIFIER
# ============================================================

class AestheticClassifier:
    """Maps brand config dict → AestheticProfile using keyword scoring.

    Algorithm: weighted additive scoring from center (0.5).
    Inputs processed in order of weight:
      1. brand.archetype  (weight 0.30 per match)
      2. theme.mood_keywords  (weight 0.15 per keyword)
      3. materials  (weight 0.10 per material)
      4. illustration.style  (weight 0.12, pattern-matched)
      5. brand.voice  (weight 0.08, pattern-matched)

    Phase A: returns centered profile (all axes = 0.5, register = "balanced-contemporary")
    Phase B: populates ARCHETYPE_WEIGHTS, MOOD_WEIGHTS, MATERIAL_WEIGHTS
    """

    # ── Archetype → axis deltas (applied with 0.30 multiplier) ──────────
    # Keys are lowercase substrings matched against brand.archetype.lower()
    ARCHETYPE_WEIGHTS: Dict[str, Dict[str, float]] = {
        # axis keys: density | temporal | material | boldness | commercial
        "cultural guardian": {"temporal":  0.50, "density":  0.30, "material":  0.40, "boldness":  0.10},
        "sage":              {"temporal":  0.30, "density": -0.20, "material":  0.10, "boldness": -0.20},
        "cartographer":      {"temporal":  0.15, "density":  0.15, "material":  0.05, "boldness":  0.10},
        "creator":           {"temporal":  0.05, "density":  0.15, "material":  0.20, "boldness":  0.25},
        "explorer":          {"temporal": -0.10, "density":  0.05, "material":  0.10, "boldness":  0.30},
        "rebel":             {"temporal": -0.25, "density": -0.10, "material": -0.10, "boldness":  0.50},
        "outlaw":            {"temporal": -0.25, "density": -0.10, "material": -0.10, "boldness":  0.50},
        "ruler":             {"temporal":  0.10, "density":  0.25, "material":  0.05, "boldness":  0.25},
        "hero":              {"temporal": -0.05, "density":  0.10, "material":  0.05, "boldness":  0.40},
        "magician":          {"temporal": -0.10, "density":  0.30, "material":  0.20, "boldness":  0.35},
        "lover":             {"temporal":  0.15, "density":  0.20, "material":  0.30, "boldness":  0.20},
        "jester":            {"temporal": -0.15, "density":  0.20, "material": -0.05, "boldness":  0.30, "commercial":  0.20},
        "innocent":          {"temporal":  0.10, "density": -0.15, "material":  0.10, "boldness": -0.15},
        "caregiver":         {"temporal":  0.20, "density":  0.05, "material":  0.25, "boldness": -0.10},
        "everyman":          {"temporal":  0.10, "density":  0.05, "material":  0.10, "boldness": -0.05, "commercial":  0.10},
    }

    # ── Mood keyword → axis deltas (applied with 0.15 multiplier) ────────
    MOOD_WEIGHTS: Dict[str, Dict[str, float]] = {
        # Heritage / craft
        "terracotta":        {"temporal":  0.40, "material":  0.50, "density":  0.30},
        "handcrafted":       {"temporal":  0.40, "material":  0.60, "density":  0.20},
        "handwoven":         {"temporal":  0.45, "material":  0.60, "density":  0.25},
        "ceremonial":        {"temporal":  0.50, "density":   0.40, "material":  0.40},
        "heritage":          {"temporal":  0.60, "material":  0.30, "density":   0.20},
        "ancestral":         {"temporal":  0.70, "material":  0.40, "density":   0.30},
        "folk":              {"temporal":  0.50, "material":  0.50, "density":   0.35},
        "artisanal":         {"temporal":  0.35, "material":  0.55, "density":   0.15},
        "craft":             {"temporal":  0.30, "material":  0.55, "density":   0.15},
        "wabi-sabi":         {"temporal":  0.30, "density":  -0.30, "material":  0.35},
        "patina":            {"temporal":  0.35, "material":  0.40},
        "engraved":          {"temporal":  0.30, "material":  0.35, "density":   0.15},
        # Botanical / natural
        "botanical":         {"temporal":  0.20, "material":  0.40, "density":   0.10},
        "organic":           {"temporal":  0.15, "material":  0.40},
        "earthy":            {"temporal":  0.25, "material":  0.45},
        "natural":           {"temporal":  0.15, "material":  0.45},
        "warm":              {"temporal":  0.15, "material":  0.15},
        # Minimal / zen
        "minimalist":        {"temporal":  0.00, "density":  -0.50, "boldness": -0.20},
        "minimal":           {"temporal":  0.00, "density":  -0.45, "boldness": -0.18},
        "zen":               {"temporal":  0.10, "density":  -0.55, "boldness": -0.25},
        "sparse":            {"density":  -0.45, "boldness": -0.15},
        "restrained":        {"density":  -0.30, "boldness": -0.20},
        "quiet":             {"density":  -0.20, "boldness": -0.20},
        "negative-space":    {"density":  -0.50, "boldness": -0.10},
        "stillness":         {"density":  -0.40, "boldness": -0.20},
        "minimal-zen":       {"density":  -0.60, "boldness": -0.25, "temporal":  0.05},
        # Bold / dramatic
        "bold":              {"boldness":  0.40, "density":   0.20},
        "maximalist":        {"density":   0.55, "boldness":  0.30},
        "ornate":            {"temporal":  0.20, "density":   0.55},
        "decorative":        {"temporal":  0.15, "density":   0.45},
        "jewel-toned":       {"temporal":  0.10, "density":   0.20, "boldness":  0.25},
        "dramatic":          {"boldness":  0.40, "density":   0.25},
        "architectural":     {"temporal": -0.10, "density":   0.15, "boldness":  0.30},
        # Futuristic / tech
        "futuristic":        {"temporal": -0.50, "material": -0.20, "boldness":  0.40},
        "bioluminescent":    {"temporal": -0.30, "material": -0.10, "boldness":  0.20},
        "cyberpunk":         {"temporal": -0.40, "density":   0.20, "boldness":  0.50},
        "solarpunk":         {"temporal": -0.20, "material":  0.20, "boldness":  0.20},
        "bio-digital":       {"temporal": -0.25, "material": -0.05, "boldness":  0.30},
        "speculative":       {"temporal": -0.40, "material": -0.15},
        "precision":         {"temporal": -0.15, "density":   0.10, "boldness":  0.20},
        "clinical":          {"temporal": -0.25, "density":  -0.15, "material": -0.30},
        "neon":              {"temporal": -0.30, "boldness":  0.50},
        # Editorial / commercial
        "editorial":         {"commercial": -0.40},
        "luxury":            {"temporal":   0.10, "density":   0.10, "material":  0.15, "commercial": -0.20},
        "premium":           {"temporal":   0.10, "material":  0.10, "commercial": -0.15},
        "commercial":        {"commercial":  0.35},
        "conversion":        {"commercial":  0.45},
        "campaign":          {"commercial":  0.20, "boldness":  0.15},
        # Spiritual / contemplative
        "sacred":            {"temporal":  0.30, "density":   0.20, "material":  0.25},
        "meditative":        {"density":  -0.25, "boldness":  -0.25},
        "contemplative":     {"density":  -0.20, "boldness":  -0.20},
        "mystical":          {"temporal":  0.15, "density":   0.25, "boldness":  0.15},
    }

    # ── Material vocabulary → axis deltas (applied with 0.10 multiplier) ─
    MATERIAL_WEIGHTS: Dict[str, Dict[str, float]] = {
        # Natural / earth
        "clay":              {"temporal":  0.50, "material":  0.70},
        "terracotta":        {"temporal":  0.50, "material":  0.70},
        "copper":            {"temporal":  0.40, "material":  0.50},
        "bronze":            {"temporal":  0.40, "material":  0.45},
        "iron":              {"temporal":  0.35, "material":  0.40},
        "brass":             {"temporal":  0.35, "material":  0.40},
        "stone":             {"temporal":  0.35, "material":  0.50},
        "marble":            {"temporal":  0.25, "material":  0.40, "boldness":  0.10},
        "linen":             {"temporal":  0.30, "material":  0.45},
        "cotton":            {"temporal":  0.20, "material":  0.35},
        "silk":              {"temporal":  0.30, "material":  0.40, "density":   0.10},
        "leather":           {"temporal":  0.25, "material":  0.40},
        "wood":              {"temporal":  0.30, "material":  0.45},
        "ceramic":           {"temporal":  0.35, "material":  0.50},
        "handwoven":         {"temporal":  0.45, "material":  0.60, "density":  0.25},
        "botanical":         {"temporal":  0.15, "material":  0.40},
        "wax":               {"temporal":  0.30, "material":  0.35},
        "pigment":           {"temporal":  0.20, "material":  0.40},
        "natural":           {"temporal":  0.15, "material":  0.45},
        "palm-leaf":         {"temporal":  0.55, "material":  0.60},
        "mycelium":          {"temporal":  0.05, "material":  0.45},
        # Tech / synthetic
        "titanium":          {"temporal": -0.30, "material": -0.30, "boldness":  0.20},
        "carbon-fiber":      {"temporal": -0.40, "material": -0.40, "boldness":  0.20},
        "aluminum":          {"temporal": -0.25, "material": -0.25, "boldness":  0.15},
        "glass":             {"temporal": -0.15, "material": -0.15},
        "acrylic":           {"temporal": -0.20, "material": -0.25},
        "phosphorescent":    {"temporal": -0.40, "material": -0.20, "boldness":  0.20},
        "fiber-optic":       {"temporal": -0.35, "material": -0.15, "boldness":  0.25},
        "circuit":           {"temporal": -0.35, "material": -0.20},
        "oxidized":          {"temporal":  0.30, "material":  0.30},
    }

    def classify(self, v: dict, upstream_data: Optional[dict] = None) -> AestheticProfile:
        """Classify brand config into an AestheticProfile using weighted keyword scoring."""
        scores: Dict[str, float] = {
            "density": 0.5, "temporal": 0.5, "material": 0.5,
            "boldness": 0.5, "commercial": 0.5,
        }
        sources: List[str] = []

        # Step 1: archetype (weight 0.30 per match — highest weight)
        archetype_lower = v.get("archetype", "").lower()
        for key, weights in self.ARCHETYPE_WEIGHTS.items():
            if key in archetype_lower:
                for axis, delta in weights.items():
                    scores[axis] = _clamp(scores[axis] + delta * 0.30)
                sources.append(f"archetype:{key}")
                break  # first match wins for archetype

        # Step 2: mood keywords (weight 0.15 per keyword match)
        for kw in v.get("mood_keywords", "").split(","):
            kw_norm = kw.strip().lower().replace(" ", "-")
            for key, weights in self.MOOD_WEIGHTS.items():
                if key in kw_norm:
                    for axis, delta in weights.items():
                        scores[axis] = _clamp(scores[axis] + delta * 0.15)
                    sources.append(f"mood:{key}")

        # Step 3: materials (weight 0.10 per material match)
        for mat in v.get("materials_list", "").split(","):
            mat_norm = mat.strip().lower()
            for key, weights in self.MATERIAL_WEIGHTS.items():
                if key in mat_norm:
                    for axis, delta in weights.items():
                        scores[axis] = _clamp(scores[axis] + delta * 0.10)
                    sources.append(f"material:{key}")

        # Step 4: illustration style patterns (weight 0.12)
        illus = v.get("illus_style", "").lower()
        if any(w in illus for w in ["organic", "curve", "botanical", "folk", "motif"]):
            scores["temporal"] = _clamp(scores["temporal"] + 0.12)
            scores["material"] = _clamp(scores["material"] + 0.08)
            sources.append("illus:organic-folk")
        if any(w in illus for w in ["circuit", "tech", "digital", "geometric precision"]):
            scores["temporal"] = _clamp(scores["temporal"] - 0.12)
            sources.append("illus:tech-geometric")
        if any(w in illus for w in ["art nouveau", "mucha", "warli", "madhubani", "rangoli", "patachitra"]):
            scores["temporal"] = _clamp(scores["temporal"] + 0.15)
            scores["density"] = _clamp(scores["density"] + 0.10)
            sources.append("illus:heritage-decorative")
        if any(w in illus for w in ["minimal", "clean line", "flat"]):
            scores["density"] = _clamp(scores["density"] - 0.12)
            sources.append("illus:minimal-flat")

        # Step 5: voice/tone patterns (weight 0.08)
        voice = v.get("voice", "").lower()
        if any(w in voice for w in ["bold", "fierce", "disruptive", "confrontational"]):
            scores["boldness"] = _clamp(scores["boldness"] + 0.10)
            sources.append("voice:bold")
        if any(w in voice for w in ["quiet", "restrained", "subtle", "understated", "gentle"]):
            scores["boldness"] = _clamp(scores["boldness"] - 0.10)
            sources.append("voice:restrained")
        if any(w in voice for w in ["reverent", "ceremonial", "sacred", "ancestral", "devotional"]):
            scores["temporal"] = _clamp(scores["temporal"] + 0.08)
            sources.append("voice:reverent")
        if any(w in voice for w in ["clinical", "technical", "precise", "systematic"]):
            scores["temporal"] = _clamp(scores["temporal"] - 0.08)
            sources.append("voice:technical")
        if any(w in voice for w in ["editorial", "literary", "academic", "scholarly"]):
            scores["commercial"] = _clamp(scores["commercial"] - 0.10)
            sources.append("voice:editorial")

        # Step 6: Optional upstream enrichment from Wave 1-2 outputs
        if upstream_data:
            self._enrich_from_upstream(scores, sources, upstream_data)

        dominant_register = self._label_register(scores)
        confidence = self._compute_confidence(scores)

        return AestheticProfile(
            composition_density=scores["density"],
            temporal_register=scores["temporal"],
            material_richness=scores["material"],
            visual_boldness=scores["boldness"],
            editorial_vs_commercial=scores["commercial"],
            dominant_register=dominant_register,
            confidence=confidence,
            signal_sources=sources[:15],  # extended to include upstream signals
            archetype_cluster=archetype_lower,
        )

    def _label_register(self, scores: dict) -> str:
        """Map 5-axis score vector to a named aesthetic register.

        Priority order matters: more specific conditions checked first.
        Minimal-zen checked before heritage-craft to prevent natural-material
        zen brands (wabi-sabi, linen, ceramic) from misclassifying as craft brands.
        """
        t = scores["temporal"]
        m = scores["material"]
        d = scores["density"]
        b = scores["boldness"]
        c = scores["commercial"]

        # Minimal-zen wins when density is low regardless of temporal/material
        # (Wabi-sabi brands use natural materials but NOT dense compositions)
        # Threshold relaxed to 0.30: density=0.26 brands are clearly sparse but just
        # above the old 0.25 cutoff due to floating-point accumulation in scoring.
        if d < 0.30 and b < 0.45:
            return "minimal-zen"            # Japanese minimalism, wabi-sabi, sparse
        if d < 0.35 and t < 0.40 and b < 0.45:
            return "minimal-futuristic"     # Muji-meets-tech, sparse + contemporary
        # Heritage/craft — requires both temporal AND material AND moderate density
        if t > 0.65 and m > 0.60 and d > 0.30:
            return "heritage-craft"         # Kristudios, Indian craft brands, folk art
        if t > 0.65 and d > 0.60:
            return "ornate-traditional"     # Maximal heritage, decorative, ornate
        if t < 0.35 and b > 0.60:
            return "futuristic-editorial"   # Tech-forward, dramatic, bold
        if t < 0.35 and d < 0.45:
            return "minimal-futuristic"     # Muji-meets-tech aesthetic
        if b > 0.60 and c > 0.55:
            return "bold-commercial"        # High-conversion, DTC-optimized
        if m > 0.55 and t > 0.45:
            return "natural-editorial"      # Botanical, wellness, organic
        if d > 0.55 and t > 0.45:
            return "rich-editorial"         # Dense, editorial, heritage-adjacent
        return "balanced-contemporary"      # Center fallback

    def _compute_confidence(self, scores: dict) -> float:
        """Confidence = avg distance from center (0.5). 0=totally ambiguous, 1=maximally opinionated."""
        dists = [abs(v - 0.5) for v in scores.values()]
        raw = sum(dists) / len(dists) * 2.0
        return round(min(raw, 1.0), 2)

    def _enrich_from_upstream(self, scores: dict, sources: list, upstream: dict) -> None:
        """Enrich scores from Wave 1-2 JSON outputs (buyer-persona, competitor-analysis).

        Actual JSON structure (from Wave 1-2 outputs):
          buyer-persona.json  → root["handoff"]["aspirational_brands"] (if set by brand-config)
                             or no aspirational field (skill doesn't generate it directly)
          competitor-analysis.json → root["handoff"]["aspirational_comparisons"] (dict brand→desc)
                                  → root["handoff"]["positioning_opportunities"] (list of strings)
        """
        # buyer-persona: check handoff.persona_name tone + voice for minimal/heritage signals
        persona_handoff = upstream.get("persona", {}).get("handoff", {})
        tone_source = str(persona_handoff.get("tone_source", "")).lower()
        if any(b in tone_source for b in ["muji", "acne", "minimal", "uniqlo"]):
            scores["density"] = _clamp(scores["density"] - 0.10)
            scores["boldness"] = _clamp(scores["boldness"] - 0.08)
            sources.append("upstream:minimal-aspiration")

        # competitor-analysis: aspirational_comparisons dict {BrandName: description}
        comp_handoff = upstream.get("competitive", {}).get("handoff", {})
        aspir_comps = comp_handoff.get("aspirational_comparisons", {})
        aspir_str = " ".join(
            f"{k} {v}" for k, v in (aspir_comps.items() if isinstance(aspir_comps, dict) else [])
        ).lower()
        if any(b in aspir_str for b in ["hermès", "hermes", "loewe", "bottega", "loro piana", "brunello"]):
            scores["temporal"] = _clamp(scores["temporal"] + 0.10)
            scores["material"] = _clamp(scores["material"] + 0.10)
            sources.append("upstream:heritage-aspiration")
        if any(b in aspir_str for b in ["apple", "dyson", "braun", "teenage engineering"]):
            scores["temporal"] = _clamp(scores["temporal"] - 0.10)
            scores["density"] = _clamp(scores["density"] - 0.08)
            sources.append("upstream:precision-minimal-aspiration")
        if any(b in aspir_str for b in ["fabindia", "good earth", "nalli", "tanishq"]):
            scores["temporal"] = _clamp(scores["temporal"] + 0.08)
            scores["material"] = _clamp(scores["material"] + 0.08)
            sources.append("upstream:indian-heritage-aspiration")

        # positioning_opportunities: craft/authenticity signals → push material axis
        opp_str = " ".join(str(o) for o in comp_handoff.get("positioning_opportunities", [])).lower()
        if any(w in opp_str for w in ["rawness", "authenticity", "craft", "handmade", "artisanal", "heritage"]):
            scores["material"] = _clamp(scores["material"] + 0.08)
            sources.append("upstream:craft-differentiation")


# ============================================================
# TEMPLATE MATCHER
# ============================================================

class TemplateMatcher:
    """Maps AestheticProfile → {asset_id: variant_id} for all assets in registry.

    Algorithm: score each variant's aesthetic_tags against profile axes.
    Returns the highest-scoring variant per asset.

    Phase A: returns all default variants (no scoring yet).
    Phase B: scoring is active after AestheticClassifier is calibrated.
    """

    # Tag value → (axis_attr_name, lo, hi) — range where this tag is a match
    TAG_RANGES: Dict[str, tuple] = {
        # composition_density
        "sparse":         ("composition_density", 0.0, 0.35),
        "moderate":       ("composition_density", 0.30, 0.70),
        "dense":          ("composition_density", 0.65, 0.85),
        "ornate":         ("composition_density", 0.75, 1.0),

        # temporal_register
        "speculative":    ("temporal_register", 0.0, 0.25),
        "futuristic":     ("temporal_register", 0.0, 0.35),
        "contemporary":   ("temporal_register", 0.30, 0.70),
        "heritage":       ("temporal_register", 0.60, 1.0),
        "ancestral":      ("temporal_register", 0.75, 1.0),

        # material_richness
        "synthetic":      ("material_richness", 0.0, 0.30),
        "minimal":        ("material_richness", 0.0, 0.40),
        "natural":        ("material_richness", 0.35, 0.70),
        "craft":          ("material_richness", 0.60, 1.0),

        # visual_boldness
        "subtle":         ("visual_boldness", 0.0, 0.35),
        "refined":        ("visual_boldness", 0.10, 0.45),
        "balanced":       ("visual_boldness", 0.35, 0.65),
        "bold":           ("visual_boldness", 0.60, 1.0),
        "architectural":  ("visual_boldness", 0.50, 0.85),

        # editorial_vs_commercial
        "editorial":      ("editorial_vs_commercial", 0.0, 0.45),
        "commercial":     ("editorial_vs_commercial", 0.55, 1.0),
    }

    def select_variants(
        self,
        profile: AestheticProfile,
        registry: dict,
        aesthetic_overrides: Optional[dict] = None,
    ) -> Dict[str, str]:
        """Return {asset_id: variant_id} for all assets in registry.

        Phase A: returns all default variants.
        Phase B+: scoring is active when profile.confidence > 0.3.
        """
        overrides = aesthetic_overrides or {}
        selections: Dict[str, str] = {}

        for asset_id, asset_def in registry.get("variants", {}).items():
            # Check for explicit manual override in brand-config aesthetic section
            override_key = f"template_variant_{asset_id.lower().replace('-', '_')}"
            if overrides.get(override_key):
                selections[asset_id] = overrides[override_key]
                continue

            default_variant = asset_def.get("default", "standard")
            variants = asset_def.get("variants", {})

            # Score only when multiple variants exist and profile is opinionated
            if len(variants) <= 1 or profile.confidence <= 0.20:
                # Only one option or brand signals too weak — use default
                selections[asset_id] = default_variant
                continue

            best_variant = default_variant
            best_score = -1.0
            for variant_id, variant_def in variants.items():
                tags = variant_def.get("aesthetic_tags", {})
                score = self._score_variant(profile, tags)
                if score > best_score:
                    best_score = score
                    best_variant = variant_id

            selections[asset_id] = best_variant

        return selections

    def _score_variant(self, profile: AestheticProfile, tags: dict) -> float:
        """Score compatibility between a profile and a variant's aesthetic tags."""
        total_score = 0.0
        tag_count = 0

        for _dim, tag_values in tags.items():
            for tag_value in (tag_values if isinstance(tag_values, list) else [tag_values]):
                if tag_value in self.TAG_RANGES:
                    axis_attr, lo, hi = self.TAG_RANGES[tag_value]
                    axis_score = getattr(profile, axis_attr, 0.5)
                    if lo <= axis_score <= hi:
                        total_score += 1.0
                    else:
                        dist = min(abs(axis_score - lo), abs(axis_score - hi))
                        total_score += max(0.0, 1.0 - dist * 3.0)
                    tag_count += 1

        return total_score / tag_count if tag_count > 0 else 0.5


# ============================================================
# VARIANT VARIABLE INJECTION
# ============================================================

def inject_variant_vars(
    v: dict,
    variant_selections: Dict[str, str],
    registry: dict,
    profile: AestheticProfile,
) -> dict:
    """Augment v dict with variant-specific template variables.

    Adds:
      - {asset_id_varname}: value pairs from variant's template_variables
      - variant_selection_{asset_id}: the chosen variant id (for cookbook)
      - aesthetic_profile_summary: dict for cookbook rendering

    Injected template_variables can themselves contain {brand_variable} references.
    These are pre-rendered against the current v dict so that when generate_pipeline.py
    calls render(PROMPT_*, v), the final prompt has all variables resolved in one pass.
    """
    for asset_id, variant_id in variant_selections.items():
        asset_def = registry.get("variants", {}).get(asset_id, {})
        variant_def = asset_def.get("variants", {}).get(variant_id, {})
        tvars = variant_def.get("template_variables", {})

        # Inject each template variable namespaced by asset_id
        asset_prefix = asset_id.lower().replace("-", "_")
        for var_name, var_value in tvars.items():
            # Pre-render brand variable references (e.g. {product_hero_physical})
            # so the final prompt resolves everything in one pass
            if isinstance(var_value, str) and "{" in var_value:
                var_value = _pre_render(var_value, v)
            v[f"{asset_prefix}_{var_name}"] = var_value

        # Record the selection + description for cookbook + debugging
        v[f"variant_selection_{asset_prefix}"] = variant_id
        v[f"variant_description_{asset_prefix}"] = variant_def.get("description", "")

    # Inject aesthetic profile summary for cookbook rendering
    v["aesthetic_profile_summary"] = {
        "density":    round(profile.composition_density, 2),
        "temporal":   round(profile.temporal_register, 2),
        "material":   round(profile.material_richness, 2),
        "boldness":   round(profile.visual_boldness, 2),
        "commercial": round(profile.editorial_vs_commercial, 2),
        "register":   profile.dominant_register,
        "confidence": round(profile.confidence, 2),
        "signals":    profile.signal_sources[:8],
    }

    return v


# ============================================================
# REGISTRY LOADER
# ============================================================

def load_template_variants(registry_path: str) -> dict:
    """Load template-variants.yaml from disk. Returns empty dict on error."""
    try:
        import yaml
        with open(registry_path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"  WARNING: Could not load template-variants.yaml: {e}")
        return {}


def load_upstream_data(config_path: str) -> Optional[dict]:
    """Load Wave 1-2 output JSONs for classifier enrichment.

    Looks for buyer-persona.json and competitor-analysis.json in
    the .brandmint/outputs/ directory relative to brand-config.yaml.

    Returns merged dict or None if outputs not found.
    """
    brand_dir = os.path.dirname(config_path)
    outputs_dir = os.path.join(brand_dir, ".brandmint", "outputs")
    if not os.path.isdir(outputs_dir):
        return None

    upstream: dict = {}
    for skill_id, key in [
        ("buyer-persona", "persona"),
        ("competitor-analysis", "competitive"),
    ]:
        path = os.path.join(outputs_dir, f"{skill_id}.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    upstream[key] = json.load(f)
            except Exception:
                pass

    return upstream if upstream else None


def write_aesthetic_sidecar(config_path: str, profile: AestheticProfile, selections: Dict[str, str]) -> None:
    """Write aesthetic-profile.json sidecar alongside brand-config.yaml.

    This mirrors the execution-context.json pattern: the sidecar persists
    the classification result so other tools can read it without re-running
    the full classifier.
    """
    brand_dir = os.path.dirname(config_path)
    sidecar_path = os.path.join(brand_dir, "aesthetic-profile.json")
    try:
        data = {
            "profile": asdict(profile),
            "variant_selections": selections,
        }
        with open(sidecar_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"  WARNING: Could not write aesthetic-profile.json: {e}")


# ============================================================
# HELPERS
# ============================================================

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _pre_render(template_str: str, v: dict) -> str:
    """Resolve {brand_variable} references in a variant template string.

    Uses the same SafeDict approach as generate_pipeline.render():
    missing keys remain as {key_name} rather than raising KeyError.
    This is called during inject_variant_vars() so that when the main
    PROMPT_* template is rendered later, everything resolves in one pass.
    """
    class SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"
    return template_str.format_map(SafeDict(v))
