"""
wave_planner.py -- Wave computation engine for brandmint.

Transforms brand configuration + scenario + depth into an ordered
List[Wave] execution plan with cost estimates and dependency chains.

Usage:
    from brandmint.core.wave_planner import compute_wave_plan

    waves = compute_wave_plan(cfg, scenario_id="crowdfunding-lean", depth="focused")
    for w in waves:
        print(f"Wave {w.number}: {w.name} -- ${w.estimated_cost:.2f}")

Architecture:
    1. WAVE_DEFINITIONS -- static structure (what goes in each wave)
    2. Asset registry -- loaded from assets/asset-registry.yaml
    3. Domain filtering -- prunes visual assets by brand's domain_tags
    4. Scenario filtering -- prunes text skills to scenario's skill_ids
    5. Depth pruning -- limits how many waves are returned
    6. Cost estimation -- text skills + visual asset seeds
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..models.wave import Wave, WaveStatus


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_COST_ESTIMATE: float = 600.0
"""Rough cost estimate per text-based skill execution (USD)."""

DEFAULT_SEEDS: int = 2
"""Default number of seed generations per visual asset."""

DEPTH_WAVE_LIMITS: Dict[str, int] = {
    "surface": 2,
    "focused": 5,
    "comprehensive": 7,
    "exhaustive": 999,
}
"""Maximum wave number included at each depth level."""


# ---------------------------------------------------------------------------
# Visual asset cost reference (cost per single seed)
# ---------------------------------------------------------------------------

VISUAL_ASSET_COSTS: Dict[str, float] = {
    # Wave 3 -- Visual Identity
    "2A": 0.08,
    "2B": 0.05,
    "2C": 0.05,
    # Wave 4 -- Products & Content
    "3A": 0.05,
    "3B": 0.05,
    "3C": 0.05,
    "4A": 0.08,
    "4B": 0.05,
    # Wave 5 -- Campaign Assets
    "5A": 0.04,
    "5B": 0.08,
    "5C": 0.04,
    "7A": 0.08,
    "8A": 0.08,
    # Domain-specific assets
    "APP-ICON": 0.05,
    "OG-IMAGE": 0.08,
    "IG-STORY": 0.08,
    "APP-SCREENSHOT": 0.08,
    "PITCH-HERO": 0.08,
    "TWITTER-HEADER": 0.08,
    "EMAIL-HERO": 0.08,
}
"""Per-seed cost for each visual asset ID (USD)."""


# ---------------------------------------------------------------------------
# Wave definitions (static structure)
# ---------------------------------------------------------------------------

WAVE_DEFINITIONS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Foundation",
        "description": "Market understanding + brand identity setup",
        "text_skills": ["niche-validator", "buyer-persona", "competitor-analysis"],
        "visual_assets": [],
        "depends_on": [],
    },
    2: {
        "name": "Strategy",
        "description": "Product positioning + messaging direction",
        "text_skills": [
            "detailed-product-description",
            "product-positioning-summary",
            "mds-messaging-direction-summary",
            "voice-and-tone",
        ],
        "visual_assets": [],
        "depends_on": [1],
    },
    3: {
        "name": "Visual Identity",
        "description": "Brand visual system -- anchor, seal, logo",
        "text_skills": ["visual-identity-core"],
        "visual_assets": ["2A", "2B", "2C", "APP-ICON"],
        "depends_on": [2],
    },
    4: {
        "name": "Products & Content",
        "description": "Product visuals + campaign copy",
        "text_skills": [
            "campaign-page-copy",
            "campaign-video-script",
            "pre-launch-ads",
        ],
        "visual_assets": ["3A", "3B", "3C", "4A", "4B", "APP-SCREENSHOT"],
        "depends_on": [3],
    },
    5: {
        "name": "Campaign Assets",
        "description": "Campaign visuals + email sequences",
        "text_skills": [
            "welcome-email-sequence",
            "pre-launch-email-sequence",
            "launch-email-sequence",
        ],
        "visual_assets": [
            "5A", "5B", "5C",
            "7A", "8A",
            "OG-IMAGE", "TWITTER-HEADER", "IG-STORY",
        ],
        "depends_on": [4],
    },
    6: {
        "name": "Distribution",
        "description": "Launch amplification -- ads, press, social",
        "text_skills": [
            "live-campaign-ads",
            "press-release-copy",
            "social-content-engine",
            "short-form-hook-generator",
            "influencer-outreach-pro",
            "review-response-strategist",
        ],
        "visual_assets": ["PITCH-HERO", "EMAIL-HERO"],
        "depends_on": [5],
    },
    7: {
        "name": "Publishing & Deliverables",
        "description": "Brand theme export, NotebookLM, slide decks, reports, diagrams",
        "text_skills": [],
        "visual_assets": [],
        "depends_on": [6],
        "post_hook": "publishing",
        "sub_steps": [
            {"id": "7A", "name": "Brand Theme Export", "hook": "theme_export"},
            {"id": "7B", "name": "NotebookLM Publishing", "hook": "notebooklm"},
            {"id": "7C", "name": "Slide Decks (Marp)", "hook": "marp_decks"},
            {"id": "7D", "name": "Reports (Typst)", "hook": "typst_reports"},
            {"id": "7E", "name": "Mind Maps & Diagrams", "hook": "diagrams"},
            {"id": "7F", "name": "Video Overviews (Remotion)", "hook": "remotion"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Asset registry loader
# ---------------------------------------------------------------------------

PACKAGE_ROOT: Path = Path(__file__).resolve().parent.parent.parent
"""Root of the brandmint repository (two levels up from core/)."""

ASSET_REGISTRY_PATH: Path = PACKAGE_ROOT / "assets" / "asset-registry.yaml"
"""Default path to the asset-registry.yaml file."""


def load_asset_registry(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and return the asset registry YAML as a dict.

    Args:
        config_path: Override path to asset-registry.yaml.
                     Defaults to ``<repo>/assets/asset-registry.yaml``.

    Returns:
        Dict mapping asset IDs to their definitions.

    Raises:
        FileNotFoundError: If the registry file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    path = Path(config_path) if config_path else ASSET_REGISTRY_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Asset registry not found at {path}. "
            f"Expected location: {ASSET_REGISTRY_PATH}"
        )
    with open(path) as fh:
        data = yaml.safe_load(fh)
    return data.get("assets", {})


# ---------------------------------------------------------------------------
# Domain-based asset filtering
# ---------------------------------------------------------------------------

def filter_assets_by_domain(
    asset_registry: Dict[str, Any],
    domain_tags: List[str],
) -> List[str]:
    """Return asset IDs whose tags overlap with *domain_tags*.

    An asset is included when:
    - It carries the ``"*"`` tag (universal asset), **or**
    - Any of its tags intersect with the supplied *domain_tags*.

    Args:
        asset_registry: Full asset registry dict (asset_id -> definition).
        domain_tags: Brand-level domain tags (e.g. ``["dtc", "crowdfunding"]``).

    Returns:
        Sorted list of matching asset IDs.
    """
    if not domain_tags:
        # With no domain tags, only universal assets qualify.
        return sorted(
            aid for aid, adef in asset_registry.items()
            if "*" in adef.get("tags", [])
        )

    domain_set = set(domain_tags)
    matched: List[str] = []

    for asset_id, asset_def in asset_registry.items():
        tags = set(asset_def.get("tags", []))
        if "*" in tags or tags & domain_set:
            matched.append(asset_id)

    return sorted(matched)


# ---------------------------------------------------------------------------
# Cost calculation helpers
# ---------------------------------------------------------------------------

def _text_skill_cost(skill_count: int) -> float:
    """Estimate USD cost for *skill_count* text skills."""
    return skill_count * SKILL_COST_ESTIMATE


def _visual_asset_cost(
    asset_ids: List[str],
    seeds: int = DEFAULT_SEEDS,
) -> float:
    """Estimate USD cost for generating *asset_ids* with *seeds* per asset.

    Falls back to the median cost ($0.08) for unknown asset IDs so the
    planner never silently drops cost.
    """
    fallback = 0.08
    total = 0.0
    for aid in asset_ids:
        per_seed = VISUAL_ASSET_COSTS.get(aid, fallback)
        total += per_seed * seeds
    return total


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_wave_plan(
    config: Any,
    scenario_id: Optional[str] = None,
    depth: str = "focused",
) -> List[Wave]:
    """Compute the ordered wave execution plan for a brand launch.

    This is the main entry point called by ``launch.py``.

    Algorithm:
        1. Load the asset registry from disk.
        2. Read ``domain_tags`` from the brand config.
        3. Determine which visual assets match the brand's domain.
        4. Optionally filter text skills to the scenario's ``skill_ids``.
        5. Prune waves by *depth* (surface/focused/comprehensive/exhaustive).
        6. Calculate estimated cost per wave (text + visual).
        7. Return ``List[Wave]``.

    Args:
        config: Brand configuration object. Must expose:
                - ``config.domain_tags`` (``List[str]``) -- brand domain tags
                - ``config.asset_registry_path`` (optional ``str``) -- override
                  path to asset-registry.yaml
        scenario_id: If provided, fetch the scenario from
                     ``ScenarioRecommender`` and restrict each wave's
                     text_skills to the scenario's ``skill_ids``.
        depth: Execution depth. One of:
               ``"surface"`` (waves 1-2),
               ``"focused"`` (waves 1-5),
               ``"comprehensive"`` (waves 1-6),
               ``"exhaustive"`` (all waves).

    Returns:
        Ordered list of ``Wave`` objects ready for execution.

    Raises:
        ValueError: If *depth* is not a recognized level.
        FileNotFoundError: If the asset registry cannot be located.
    """
    # -- Validate depth ---------------------------------------------------
    if depth not in DEPTH_WAVE_LIMITS:
        raise ValueError(
            f"Unknown depth '{depth}'. "
            f"Valid options: {list(DEPTH_WAVE_LIMITS.keys())}"
        )
    max_wave = DEPTH_WAVE_LIMITS[depth]

    # -- Load asset registry ---------------------------------------------
    if isinstance(config, dict):
        registry_path = config.get("asset_registry_path")
        domain_tags_raw = config.get("brand", {}).get("domain_tags", [])
    else:
        registry_path = getattr(config, "asset_registry_path", None)
        domain_tags_raw = getattr(config, "domain_tags", [])
    asset_registry = load_asset_registry(registry_path)

    # -- Read domain tags from config ------------------------------------
    domain_tags: List[str] = domain_tags_raw if domain_tags_raw else []
    eligible_assets = set(filter_assets_by_domain(asset_registry, domain_tags))

    # -- Optionally fetch scenario skill filter --------------------------
    scenario_skill_ids: Optional[set] = None
    if scenario_id is not None:
        from .scenario_recommender import ScenarioRecommender

        recommender = ScenarioRecommender()
        scenario = recommender.get_scenario(scenario_id)
        scenario_skill_ids = set(scenario.skill_ids)

    # -- Build waves ------------------------------------------------------
    waves: List[Wave] = []

    for wave_number in sorted(WAVE_DEFINITIONS.keys()):
        if wave_number > max_wave:
            break

        defn = WAVE_DEFINITIONS[wave_number]

        # Filter text skills by scenario (if applicable)
        text_skills = list(defn["text_skills"])
        if scenario_skill_ids is not None:
            text_skills = [s for s in text_skills if s in scenario_skill_ids]

        # Filter visual assets by domain eligibility
        visual_assets = [
            aid for aid in defn["visual_assets"]
            if aid in eligible_assets
        ]

        # Cost estimation
        text_cost = _text_skill_cost(len(text_skills))
        visual_cost = _visual_asset_cost(visual_assets)
        estimated_cost = text_cost + visual_cost

        wave = Wave(
            number=wave_number,
            name=defn["name"],
            description=defn["description"],
            text_skills=text_skills,
            visual_assets=visual_assets,
            depends_on=list(defn["depends_on"]),
            status=WaveStatus.PENDING,
            estimated_cost=round(estimated_cost, 2),
            post_hook=defn.get("post_hook"),
        )
        waves.append(wave)

    return waves
