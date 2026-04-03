"""
Source curator — intelligent source selection for NotebookLM notebooks.

Scans all available brand materials (prose docs, images, wiki pages, config,
raw JSON), scores each on content value / uniqueness / category diversity /
size efficiency, and selects the optimal set within a configurable source
budget (default 50 — NotebookLM Standard plan limit).

The existing ``source_builder.py`` prose documents remain the highest-priority
sources.  The curator adds supplementary sources on top.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from .source_builder import get_source_group_definitions, resolve_source_document_mode


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_SOURCES = 50
MAX_SOURCE_SIZE_BYTES = 500 * 1024  # 500 KB per-source soft limit for text

# Image asset prefix → category mapping + base content_value
IMAGE_CATEGORY_MAP: Dict[str, tuple] = {
    # (category, content_value, human_label)
    "2A": ("brand-identity", 88, "Brand kit bento grid"),
    "2B": ("brand-identity", 86, "Brand seal"),
    "2C": ("brand-identity", 84, "Logo emboss"),
    "3A": ("product", 82, "Capsule collection"),
    "3B": ("product", 82, "Hero product"),
    "3C": ("product", 78, "Product detail"),
    "4A": ("product", 76, "Catalog layout"),
    "4B": ("product", 74, "Flatlay"),
    "5A": ("visual", 72, "Heritage engraving"),
    "5B": ("visual", 70, "Campaign grid"),
    "5C": ("visual", 70, "Art panel"),
    "5D": ("visual", 66, "Icon set"),
    "7A": ("product", 60, "Contact sheet"),
    "8A": ("campaign", 58, "Seeker poster"),
    "9A": ("campaign", 55, "Display poster"),
    "10A": ("campaign", 52, "Narrative sequence — artisan"),
    "10B": ("campaign", 52, "Narrative sequence — custodian"),
    "10C": ("campaign", 52, "Narrative sequence — festival"),
    "EMAIL-HERO": ("social", 48, "Email hero banner"),
    "IG-STORY": ("social", 46, "Instagram story template"),
    "OG-IMAGE": ("social", 44, "Open graph image"),
    "TWITTER-HEADER": ("social", 42, "Twitter header banner"),
}

# Wiki page path fragment → (category, content_value, overlap_with_prose_group)
WIKI_VALUE_MAP: Dict[str, tuple] = {
    "visual-guidelines": ("brand-identity", 72, "brand-strategy"),
    "visual-assets": ("visual", 60, "visual-asset-catalog"),
    "voice-tone": ("brand-identity", 68, "brand-strategy"),
    "writing-principles": ("brand-identity", 65, "brand-strategy"),
    "primary-persona": ("strategy", 62, "brand-foundation"),
    "competitive-landscape": ("strategy", 60, "brand-foundation"),
    "overview": ("product", 64, "brand-strategy"),
    "features": ("product", 62, "brand-strategy"),
    "specifications": ("product", 58, "brand-strategy"),
    "campaign-copy": ("campaign", 50, "campaign-content"),
    "email-templates": ("social", 48, "communications-social"),
    "press-media": ("campaign", 52, "campaign-content"),
    "social-content": ("social", 50, "communications-social"),
    "video-scripts": ("campaign", 48, "campaign-content"),
    "quickstart": ("brand-identity", 40, None),
    "index": ("brand-identity", 30, None),
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SourceCandidate:
    """A potential source for NotebookLM upload."""

    path: Path
    source_type: str  # "prose", "image", "wiki", "config"
    category: str     # "brand-identity", "product", "campaign", "social", "visual", "strategy"
    label: str        # Human-readable name
    size_bytes: int = 0

    # Scoring components (0-100 each)
    content_value: float = 0.0
    uniqueness: float = 100.0
    category_bonus: float = 0.0
    size_efficiency: float = 50.0

    # Computed
    score: float = 0.0
    selected: bool = False
    skip_reason: str = ""

    # Image-specific
    asset_id: str = ""
    seed_variant: str = ""

    def compute_score(self) -> float:
        """Weighted relevance score."""
        self.score = (
            self.content_value * 0.40
            + self.uniqueness * 0.30
            + self.category_bonus * 0.20
            + self.size_efficiency * 0.10
        )
        return self.score

    @property
    def size_kb(self) -> float:
        return self.size_bytes / 1024

    @property
    def size_display(self) -> str:
        if self.size_bytes > 1024 * 1024:
            return f"{self.size_bytes / (1024 * 1024):.1f}MB"
        return f"{self.size_kb:.1f}KB"


# ---------------------------------------------------------------------------
# Curator
# ---------------------------------------------------------------------------

class SourceCurator:
    """Intelligent source selection for NotebookLM notebooks."""

    def __init__(
        self,
        brand_dir: Path,
        config: dict,
        max_sources: int = DEFAULT_MAX_SOURCES,
        sources_dir: Optional[Path] = None,
    ):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.max_sources = max_sources
        self.sources_dir = sources_dir or (
            self.brand_dir / "deliverables" / "notebooklm" / "sources"
        )

        publishing_cfg = config.get("publishing", {}).get("notebooklm", {})
        self.image_source_policy = str(
            publishing_cfg.get("image_source_policy", "manifest-only")
        ).strip().lower() or "manifest-only"
        if self.image_source_policy not in {"manifest-only", "all-generated", "product-reference-only"}:
            self.image_source_policy = "manifest-only"

        # Derived paths
        self.outputs_dir = self.brand_dir / ".brandmint" / "outputs"
        brand_name = config.get("brand", {}).get("name", "brand")
        slug = brand_name.lower().replace(" ", "-").replace("'", "")
        self.generated_dir = self.brand_dir / slug / "generated"
        self.wiki_dir = self.brand_dir / "wiki-output"
        self.config_path = self.brand_dir / "brand-config.yaml"
        self.allowed_image_asset_ids = self._load_manifest_asset_ids()

        # State
        self._candidates: List[SourceCandidate] = []
        self._selected: List[SourceCandidate] = []

    # -- Public API --------------------------------------------------------

    def curate(self) -> List[SourceCandidate]:
        """Scan, score, select — return ordered list of sources to upload."""
        self._candidates = self._scan_all_candidates()
        self._score_all()
        self._selected = self._select_within_budget()
        return self._selected

    def report(self) -> str:
        """Human-readable selection report for dry-run / logging."""
        if not self._candidates:
            self.curate()

        lines: List[str] = []
        lines.append(f"Source Selection Plan (budget: {self.max_sources})")
        lines.append("━" * 52)

        # Group by type
        type_order = ["prose", "config", "image", "wiki"]
        type_labels = {
            "prose": "Prose Documents",
            "config": "Brand Configuration",
            "image": "Brand Images",
            "wiki": "Wiki Pages",
        }

        for stype in type_order:
            group = [c for c in self._candidates if c.source_type == stype]
            if not group:
                continue

            selected_in_group = [c for c in group if c.selected]
            skipped_in_group = [c for c in group if not c.selected]
            total_size = sum(c.size_bytes for c in selected_in_group)

            label = type_labels.get(stype, stype.title())
            size_str = _format_size(total_size)
            lines.append(
                f"\n{label} ({len(selected_in_group)} selected, "
                f"{len(skipped_in_group)} skipped, {size_str}):"
            )

            # Show selected first
            for c in sorted(selected_in_group, key=lambda x: -x.score):
                lines.append(
                    f"  ✓ {c.path.name:<45s} score: {c.score:.0f}  "
                    f"({c.size_display}) — {c.label}"
                )
            # Show top skipped (max 5)
            for c in sorted(skipped_in_group, key=lambda x: -x.score)[:5]:
                reason = c.skip_reason or "below budget cutoff"
                lines.append(
                    f"  ✗ {c.path.name:<45s} score: {c.score:.0f}  "
                    f"— Skipped: {reason}"
                )
            remaining = len(skipped_in_group) - 5
            if remaining > 0:
                lines.append(f"  ... and {remaining} more skipped")

        # Summary
        total_selected = len(self._selected)
        total_text = sum(
            c.size_bytes for c in self._selected
            if c.source_type in ("prose", "config", "wiki")
        )
        total_images = sum(
            c.size_bytes for c in self._selected
            if c.source_type == "image"
        )
        lines.append(
            f"\nSummary: {total_selected}/{self.max_sources} sources selected "
            f"({_format_size(total_text)} text + {_format_size(total_images)} images)"
        )
        total_skipped = len(self._candidates) - total_selected
        lines.append(f"Skipped: {total_skipped} candidates")

        return "\n".join(lines)

    def _load_manifest_asset_ids(self) -> Optional[Set[str]]:
        """Read current-run asset IDs from generation-manifest.json when available."""
        for candidate in [
            self.generated_dir / "generation-manifest.json",
            self.brand_dir / "generated" / "generation-manifest.json",
        ]:
            if not candidate.is_file():
                continue
            try:
                payload = json.loads(candidate.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            assets = payload.get("assets", [])
            asset_ids = {
                str(asset.get("id", "")).strip().upper()
                for asset in assets
                if isinstance(asset, dict) and str(asset.get("id", "")).strip()
            }
            return asset_ids or None
        return None

    def _scan_product_reference_images(self) -> List[SourceCandidate]:
        """Scan configured product reference images as NotebookLM image sources."""
        results: List[SourceCandidate] = []
        product_refs = self.config.get("generation", {}).get("product_reference_images", [])
        config_dir = self.config_path.parent
        for index, ref in enumerate(product_refs, start=1):
            ref_path = Path(ref)
            if not ref_path.is_absolute():
                ref_path = (config_dir / ref_path).resolve()
            if not ref_path.is_file():
                continue
            results.append(
                SourceCandidate(
                    path=ref_path,
                    source_type="image",
                    category="product",
                    label=f"Product reference {index}",
                    size_bytes=ref_path.stat().st_size,
                    content_value=95.0,
                    uniqueness=100.0,
                    asset_id=f"PRODUCT-REF-{index}",
                    seed_variant="ref",
                )
            )
        return results

    # -- Scanning ----------------------------------------------------------

    def _scan_all_candidates(self) -> List[SourceCandidate]:
        """Discover all potential source candidates."""
        candidates: List[SourceCandidate] = []
        candidates.extend(self._scan_prose_docs())
        candidates.extend(self._scan_config())
        candidates.extend(self._scan_images())
        candidates.extend(self._scan_wiki_pages())
        return candidates

    def _scan_prose_docs(self) -> List[SourceCandidate]:
        """Scan the prose source documents built by source_builder."""
        results: List[SourceCandidate] = []
        if not self.sources_dir.is_dir():
            return results

        source_groups = get_source_group_definitions()

        for md_file in sorted(self.sources_dir.glob("*.md")):
            group_id = md_file.stem
            if group_id == "brand-config-source":
                continue
            group_def = source_groups.get(group_id)
            if not group_def:
                continue

            title = group_def.get("title", group_id.replace("-", " ").title())
            content_value = _prose_content_value(group_id, group_def)
            uniqueness = 100.0
            if group_def.get("category") == "kickstarter-readiness":
                uniqueness = 75.0
            elif group_def.get("category") == "kickstarter-artifact":
                uniqueness = 68.0

            results.append(SourceCandidate(
                path=md_file,
                source_type="prose",
                category=_prose_to_category(group_id, group_def),
                label=title,
                size_bytes=md_file.stat().st_size,
                content_value=content_value,
                uniqueness=uniqueness,
            ))
        return results

    def _scan_config(self) -> List[SourceCandidate]:
        """Scan brand-config.yaml and convert to markdown source."""
        if not self.config_path.is_file():
            return []

        # Build a markdown version of the config
        config_md_path = self.sources_dir / "brand-config-source.md"
        config_md_path.parent.mkdir(parents=True, exist_ok=True)

        md_content = _config_to_markdown(self.config)
        config_md_path.write_text(md_content)

        return [SourceCandidate(
            path=config_md_path,
            source_type="config",
            category="brand-identity",
            label="Brand Configuration (source of truth)",
            size_bytes=config_md_path.stat().st_size,
            content_value=78.0,
            uniqueness=60.0,  # Partially included in prose docs
        )]

    def _scan_images(self) -> List[SourceCandidate]:
        """Scan generated visual assets, deduplicating seed variants."""
        if self.image_source_policy == "product-reference-only":
            return self._scan_product_reference_images()

        results: List[SourceCandidate] = []

        if not self.generated_dir.is_dir():
            return results

        # Collect all images
        image_files = (
            sorted(self.generated_dir.glob("*.png"))
            + sorted(self.generated_dir.glob("*.webp"))
            + sorted(self.generated_dir.glob("*.jpg"))
        )

        # Group by asset ID for dedup
        groups: Dict[str, List[Path]] = {}
        for f in image_files:
            asset_id, variant = _parse_image_filename(f.name)
            if (
                self.image_source_policy == "manifest-only"
                and self.allowed_image_asset_ids
                and asset_id not in self.allowed_image_asset_ids
            ):
                continue
            groups.setdefault(asset_id, []).append((f, variant))

        for asset_id, variants in sorted(groups.items()):
            # Get metadata from lookup table
            meta = IMAGE_CATEGORY_MAP.get(asset_id, ("visual", 40, asset_id))
            category, base_value, human_label = meta

            # Sort variants: newest file first, then highest variant number, then PNG over WebP.
            variants.sort(key=lambda x: (
                -x[0].stat().st_mtime,
                -int(re.search(r"v(\d+)", x[1]).group(1)) if re.search(r"v(\d+)", x[1]) else -1,
                0 if x[0].suffix == ".png" else 1,
            ))

            for i, (fpath, variant) in enumerate(variants):
                is_primary = (i == 0)
                cand = SourceCandidate(
                    path=fpath,
                    source_type="image",
                    category=category,
                    label=human_label,
                    size_bytes=fpath.stat().st_size,
                    content_value=float(base_value),
                    uniqueness=100.0 if is_primary else 0.0,
                    asset_id=asset_id,
                    seed_variant=variant,
                )
                if not is_primary:
                    cand.skip_reason = f"older/alternate variant of {asset_id}"
                results.append(cand)

        return results

    def _scan_wiki_pages(self) -> List[SourceCandidate]:
        """Scan wiki markdown output pages."""
        results: List[SourceCandidate] = []

        if not self.wiki_dir.is_dir():
            return results

        for md_file in sorted(self.wiki_dir.rglob("*.md")):
            stem = md_file.stem
            meta = WIKI_VALUE_MAP.get(stem, ("brand-identity", 35, None))
            category, base_value, overlaps_with = meta

            uniqueness = 100.0
            if overlaps_with:
                # Wiki page overlaps with a prose doc — penalize uniqueness
                uniqueness = 35.0

            results.append(SourceCandidate(
                path=md_file,
                source_type="wiki",
                category=category,
                label=stem.replace("-", " ").title(),
                size_bytes=md_file.stat().st_size,
                content_value=float(base_value),
                uniqueness=uniqueness,
            ))

        return results

    # -- Scoring -----------------------------------------------------------

    def _score_all(self) -> None:
        """Compute scores for all candidates with category diversity bonus."""
        # Count how many candidates per category
        category_counts: Dict[str, int] = {}
        for c in self._candidates:
            if c.uniqueness > 0:  # Don't count deduped variants
                category_counts[c.category] = category_counts.get(c.category, 0) + 1

        # Categories with fewer candidates get a diversity bonus
        max_count = max(category_counts.values()) if category_counts else 1

        for c in self._candidates:
            # Category diversity bonus: underrepresented categories score higher
            cat_count = category_counts.get(c.category, 1)
            c.category_bonus = max(0, 100.0 * (1 - cat_count / max_count))

            # Size efficiency: prefer smaller sources (more info per slot)
            if c.size_bytes > 0:
                # Normalize: 1KB = 100, 10MB = 10
                kb = c.size_bytes / 1024
                c.size_efficiency = min(100.0, max(10.0, 100.0 - kb / 10))
            else:
                c.size_efficiency = 0.0

            c.compute_score()

    def _select_within_budget(self) -> List[SourceCandidate]:
        """Select the optimal set within the source budget."""
        selected: List[SourceCandidate] = []
        budget_remaining = self.max_sources
        source_groups = get_source_group_definitions("hybrid")

        def select_group(candidates: List[SourceCandidate]) -> None:
            nonlocal budget_remaining
            for c in candidates:
                if budget_remaining <= 0:
                    c.skip_reason = "over budget"
                    continue
                if c.source_type in ("prose", "wiki") and c.size_bytes > MAX_SOURCE_SIZE_BYTES:
                    c.skip_reason = f"exceeds {MAX_SOURCE_SIZE_BYTES // 1024}KB limit"
                    continue
                c.selected = True
                selected.append(c)
                budget_remaining -= 1

        prose = [c for c in self._candidates if c.source_type == "prose"]
        prose.sort(
            key=lambda c: (
                _prose_selection_bucket(
                    c.path.stem,
                    source_groups.get(c.path.stem, {}),
                    self.config,
                ),
                -c.score,
                c.size_bytes,
            )
        )

        pinned_prose = [
            c for c in prose
            if _prose_selection_bucket(c.path.stem, source_groups.get(c.path.stem, {}), self.config) == 0
        ]
        preferred_prose = [
            c for c in prose
            if _prose_selection_bucket(c.path.stem, source_groups.get(c.path.stem, {}), self.config) == 1
        ]
        supplemental_prose = [
            c for c in prose
            if _prose_selection_bucket(c.path.stem, source_groups.get(c.path.stem, {}), self.config) >= 2
        ]

        # TIER 1: Highest-priority prose docs based on channel and document mode.
        select_group(pinned_prose)

        # TIER 1.5: Always include brand config when budget allows.
        config_sources = [c for c in self._candidates if c.source_type == "config"]
        select_group(config_sources)

        # TIER 2: Preferred prose docs (legacy grouped docs in Kickstarter mode, etc.)
        select_group(preferred_prose)

        # TIER 3+: Supplemental prose, images, and wiki pages by score.
        remaining = [
            c for c in self._candidates
            if not c.selected and c.uniqueness > 0 and not c.skip_reason
        ]
        prose_supplemental_paths = {c.path for c in supplemental_prose}
        remaining.sort(
            key=lambda c: (
                0 if c.path in prose_supplemental_paths else 1,
                -c.score,
            )
        )

        for c in remaining:
            if budget_remaining <= 0:
                c.skip_reason = "over budget"
                continue

            if c.source_type in ("wiki",) and c.size_bytes > MAX_SOURCE_SIZE_BYTES:
                c.skip_reason = f"exceeds {MAX_SOURCE_SIZE_BYTES // 1024}KB limit"
                continue

            c.selected = True
            selected.append(c)
            budget_remaining -= 1

        # Mark all non-selected, non-skipped as "below cutoff"
        for c in self._candidates:
            if not c.selected and not c.skip_reason:
                c.skip_reason = "below budget cutoff"

        return selected


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prose_selection_bucket(group_id: str, group_def: Optional[dict], config: dict) -> int:
    """Return prose selection priority bucket (lower = selected earlier)."""
    launch_channel = str(config.get("execution_context", {}).get("launch_channel", "")).strip().lower()
    document_mode = resolve_source_document_mode(config)
    category = (group_def or {}).get("category")
    is_core = category is None and group_id in {
        "brand-foundation",
        "brand-strategy",
        "campaign-content",
        "communications-social",
        "visual-asset-catalog",
    }

    if document_mode == "legacy-only":
        return 0 if is_core else 3
    if document_mode == "kickstarter-only":
        if category == "kickstarter-section":
            return 0
        if category == "kickstarter-readiness":
            return 1
        if category == "kickstarter-artifact":
            return 2
        return 3

    if launch_channel == "kickstarter":
        if category == "kickstarter-section":
            return 0
        if category == "kickstarter-readiness":
            return 1
        if is_core:
            return 2
        if category == "kickstarter-artifact":
            return 3
        return 4

    if is_core:
        return 0
    if category == "kickstarter-section":
        return 1
    if category == "kickstarter-readiness":
        return 1
    if category == "kickstarter-artifact":
        return 2
    return 3



def _prose_to_category(group_id: str, group_def: Optional[dict] = None) -> str:
    """Map source group ID to category."""
    mapping = {
        "brand-foundation": "strategy",
        "brand-strategy": "brand-identity",
        "campaign-content": "campaign",
        "communications-social": "social",
        "visual-asset-catalog": "visual",
    }
    if group_id in mapping:
        return mapping[group_id]

    category = (group_def or {}).get("category")
    if category == "kickstarter-section":
        if "market-understanding" in group_id:
            return "strategy"
        if "product-detailing" in group_id:
            return "brand-identity"
        if "email-strategy" in group_id:
            return "social"
        if "campaign-messaging" in group_id:
            return "campaign"
        if "driving-continual-interest" in group_id:
            return "campaign"
        return "campaign"
    if category == "kickstarter-artifact":
        if "buyer-persona" in group_id or "competitor-summary" in group_id:
            return "strategy"
        if any(token in group_id for token in ["product-positioning", "product-description", "voice-and-tone", "mds"]):
            return "brand-identity"
        if "email" in group_id:
            return "social"
        return "campaign"
    if category == "kickstarter-readiness":
        return "brand-identity"
    return "brand-identity"



def _prose_content_value(group_id: str, group_def: Optional[dict] = None) -> float:
    """Score prose documents by how directly they support prototype decisions."""
    category = (group_def or {}).get("category")
    if category == "kickstarter-section":
        return 93.0
    if category == "kickstarter-artifact":
        return 90.0
    if category == "kickstarter-readiness":
        return 82.0
    if group_id == "visual-asset-catalog":
        return 88.0
    return 95.0


def _parse_image_filename(filename: str) -> tuple:
    """Extract asset ID prefix and seed variant from image filename.

    Examples:
        '2A-brand-kit-bento-nanobananapro-v1.png' → ('2A', 'v1')
        '5D-1-regional-traditions-icons-flux2pro-v137.png' → ('5D', 'v137')
        'EMAIL-HERO-email_hero-nanobananapro-v1.png' → ('EMAIL-HERO', 'v1')
    """
    stem = Path(filename).stem

    # Extract variant (vN at end)
    variant_match = re.search(r"-(v\d+)$", stem)
    variant = variant_match.group(1) if variant_match else "v1"

    # Extract asset ID (prefix before the first model-name segment)
    # Known model segments to strip
    model_markers = [
        "nanobananapro", "flux2pro", "recraft",
        "nanobananapro", "flux2pro", "recraft",
    ]

    # Try to find the asset prefix
    # Strategy: split on '-', find the model marker, take everything before it
    parts = stem.split("-")
    asset_parts: List[str] = []
    for p in parts:
        lower = p.lower()
        if any(m in lower for m in model_markers):
            break
        if re.match(r"^v\d+$", p):
            break
        asset_parts.append(p)

    # Normalise known prefixes
    raw_id = "-".join(asset_parts)

    # Map prompt-prefixed IDs to their base: "3A-capsule-collection" → "3A",
    # "5D-1-regional" → "5D", "9A-01-storytelling" → "9A",
    # while keeping special social ids intact.
    for special in ["EMAIL-HERO", "IG-STORY", "OG-IMAGE", "TWITTER-HEADER"]:
        if raw_id.upper().startswith(special):
            return special, variant

    base_match = re.match(r"^(\d+[A-Z])(?:-|$)", raw_id)
    if base_match:
        base_id = base_match.group(1)
    else:
        base_id = raw_id

    return base_id, variant


def _config_to_markdown(config: dict) -> str:
    """Convert brand-config.yaml to a readable markdown source document."""
    parts: List[str] = []
    brand = config.get("brand", {})
    parts.append(f"# {brand.get('name', 'Brand')} — Brand Configuration\n")
    parts.append(f"> Source of truth for all brand decisions.\n")

    # Brand core
    parts.append("## Brand Core\n")
    for key in ("name", "tagline", "archetype", "voice", "tone", "domain"):
        val = brand.get(key)
        if val:
            parts.append(f"- **{key.title()}:** {val}")

    # Theme
    theme = config.get("theme", {})
    if theme:
        parts.append("\n## Theme\n")
        for k, v in theme.items():
            if isinstance(v, str):
                parts.append(f"- **{k.title()}:** {v}")
            elif isinstance(v, list):
                parts.append(f"- **{k.title()}:** {', '.join(str(i) for i in v)}")

    # Palette
    palette = config.get("palette", {})
    if palette:
        parts.append("\n## Colour Palette\n")
        for role, entry in palette.items():
            if isinstance(entry, dict):
                name = entry.get("name", role)
                hex_val = entry.get("hex", "")
                desc = entry.get("role", "")
                parts.append(f"- **{role.title()}:** {name} ({hex_val}) — {desc}")

    # Typography
    typo = config.get("typography", {})
    if typo:
        parts.append("\n## Typography\n")
        for role, entry in typo.items():
            if isinstance(entry, dict):
                font = entry.get("font", "")
                parts.append(f"- **{role.title()}:** {font}")

    # Materials
    materials = config.get("materials", [])
    if materials:
        parts.append("\n## Materials\n")
        if isinstance(materials, list):
            for m in materials:
                if isinstance(m, dict):
                    parts.append(f"- **{m.get('name', '')}:** {m.get('role', '')}")
                else:
                    parts.append(f"- {m}")

    # Products
    products = config.get("products", {})
    if products:
        parts.append("\n## Products\n")
        if isinstance(products, dict):
            for k, v in products.items():
                if isinstance(v, str):
                    parts.append(f"- **{k.title()}:** {v}")
                elif isinstance(v, dict):
                    parts.append(f"### {k.title()}")
                    for pk, pv in v.items():
                        parts.append(f"- **{pk.title()}:** {pv}")

    # Audience
    audience = config.get("audience", {})
    if audience:
        parts.append("\n## Target Audience\n")
        for k, v in audience.items():
            if isinstance(v, str):
                parts.append(f"- **{k.replace('_', ' ').title()}:** {v}")
            elif isinstance(v, list):
                parts.append(f"- **{k.replace('_', ' ').title()}:** {', '.join(str(i) for i in v)}")

    # Photography
    photo = config.get("photography", {})
    if photo:
        parts.append("\n## Photography Style\n")
        for k, v in photo.items():
            if isinstance(v, str):
                parts.append(f"- **{k.replace('_', ' ').title()}:** {v}")

    # Illustration
    illust = config.get("illustration", {})
    if illust:
        parts.append("\n## Illustration Style\n")
        for k, v in illust.items():
            if isinstance(v, str):
                parts.append(f"- **{k.replace('_', ' ').title()}:** {v}")
            elif isinstance(v, list):
                parts.append(f"- **{k.replace('_', ' ').title()}:** {', '.join(str(i) for i in v)}")

    return "\n".join(parts) + "\n"


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    if size_bytes > 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    return f"{size_bytes / 1024:.1f}KB"
