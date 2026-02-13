#!/usr/bin/env python3
"""
Map generated visual assets to wiki documentation pages.
Scans a generated/ directory, parses asset IDs from filenames,
and outputs a JSON mapping of which images belong on which wiki pages.
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict

# Asset ID → wiki page mapping
# Based on brandmint asset-registry.yaml categories
ASSET_WIKI_MAP = {
    # Identity → brand/visual-guidelines.md
    "2A": {"page": "brand/visual-guidelines.md", "section": "Brand Kit", "role": "hero", "alt": "Brand Kit Bento Grid"},
    "2B": {"page": "brand/visual-guidelines.md", "section": "Logo & Seal", "role": "inline", "alt": "Brand Seal"},
    "2C": {"page": "brand/visual-guidelines.md", "section": "Logo & Seal", "role": "inline", "alt": "Logo Emboss"},

    # Products → product pages
    "3A": {"page": "product/features.md", "section": "Product Line", "role": "inline", "alt": "Capsule Collection"},
    "3B": {"page": "product/overview.md", "section": "Hero Product", "role": "hero", "alt": "Hero Product"},
    "3C": {"page": "product/features.md", "section": "Product Line", "role": "inline", "alt": "Essence Vial"},

    # Photography → product/specifications.md
    "4A": {"page": "product/specifications.md", "section": "Catalog", "role": "hero", "alt": "Catalog Layout"},
    "4B": {"page": "product/specifications.md", "section": "Product Photography", "role": "inline", "alt": "Flatlay"},

    # Illustrations → brand + marketing
    "5A": {"page": "brand/visual-guidelines.md", "section": "Illustration Style", "role": "inline", "alt": "Heritage Engraving"},
    "5B": {"page": "marketing/campaign-copy.md", "section": "Campaign Visuals", "role": "inline", "alt": "Campaign Grid"},
    "5C": {"page": "brand/visual-guidelines.md", "section": "Art Direction", "role": "inline", "alt": "Art Panel"},
    "5D-1": {"page": "brand/visual-guidelines.md", "section": "Icon System", "role": "inline", "alt": "Regional Traditions Icons"},
    "5D-2": {"page": "brand/visual-guidelines.md", "section": "Icon System", "role": "inline", "alt": "Life Ceremonies Icons"},
    "5D-3": {"page": "brand/visual-guidelines.md", "section": "Icon System", "role": "inline", "alt": "Epic Narratives Icons"},

    # Narrative → marketing
    "7A": {"page": "marketing/video-scripts.md", "section": "Visual Reference", "role": "hero", "alt": "Contact Sheet"},

    # Posters → marketing/campaign-copy.md
    "8A": {"page": "marketing/campaign-copy.md", "section": "Poster Assets", "role": "inline", "alt": "Seeker Poster"},
    "9A": {"page": "marketing/campaign-copy.md", "section": "Campaign Posters", "role": "gallery", "alt": "Campaign Poster"},
    "10A": {"page": "marketing/campaign-copy.md", "section": "Narrative Sequences", "role": "gallery", "alt": "Narrative Sequence"},
    "10B": {"page": "marketing/campaign-copy.md", "section": "Narrative Sequences", "role": "gallery", "alt": "Narrative Sequence"},
    "10C": {"page": "marketing/campaign-copy.md", "section": "Narrative Sequences", "role": "gallery", "alt": "Narrative Sequence"},

    # Social → marketing + index
    "EMAIL-HERO": {"page": "marketing/email-templates.md", "section": "Email Hero Banner", "role": "hero", "alt": "Email Header Hero"},
    "IG-STORY": {"page": "marketing/social-content.md", "section": "Instagram Assets", "role": "inline", "alt": "Instagram Story Template"},
    "OG-IMAGE": {"page": "index.md", "section": "Social Preview", "role": "meta", "alt": "Open Graph Image"},
    "TWITTER-HEADER": {"page": "marketing/social-content.md", "section": "Twitter Assets", "role": "inline", "alt": "Twitter Header Banner"},
}


def parse_asset_id(filename: str) -> str | None:
    """Extract asset ID from a generated filename.

    Examples:
        2A-brand-kit-bento-nanobananapro-v1.png → 2A
        5D-1-regional-traditions-icons-flux2pro-v137.png → 5D-1
        EMAIL-HERO-email_hero-nanobananapro-v1.png → EMAIL-HERO
        9A-01-sampradaya-protocols-poster-nanobananapro-v1.png → 9A
        10A-the-artisan's-craft-nanobananapro-v1.png → 10A
    """
    stem = Path(filename).stem

    # Try specific patterns in order (most specific first)
    patterns = [
        r'^(EMAIL-HERO|IG-STORY|OG-IMAGE|TWITTER-HEADER)',  # Domain-specific with hyphens
        r'^(5D-[123])',                                       # Icon subgroups
        r'^(9A)-\d+',                                         # Engine posters (9A-01, 9A-02, etc.)
        r'^(10[ABC])',                                         # Narrative sequences
        r'^([2-8][A-C])',                                      # Standard asset IDs
    ]

    for pattern in patterns:
        match = re.match(pattern, stem)
        if match:
            return match.group(1)

    return None


def is_primary_variant(filename: str) -> bool:
    """Check if this is the v1 (primary) variant."""
    return '-v1.' in filename or '-v1-' in filename


def scan_assets(generated_dir: str) -> dict:
    """Scan generated directory and build asset inventory."""
    gen_path = Path(generated_dir)

    if not gen_path.exists():
        print(f"Error: Directory not found: {generated_dir}", file=sys.stderr)
        sys.exit(1)

    # Collect all image files grouped by asset ID
    assets_by_id = defaultdict(lambda: {"primary": None, "variants": [], "all_files": []})

    image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}

    for filepath in sorted(gen_path.iterdir()):
        if filepath.suffix.lower() not in image_extensions:
            continue

        asset_id = parse_asset_id(filepath.name)
        if asset_id is None:
            print(f"  Warning: Could not parse asset ID from: {filepath.name}", file=sys.stderr)
            continue

        assets_by_id[asset_id]["all_files"].append(filepath.name)

        # Only use PNG for primary/variants (skip WebP duplicates)
        if filepath.suffix.lower() == '.png':
            if is_primary_variant(filepath.name):
                assets_by_id[asset_id]["primary"] = filepath.name
            else:
                assets_by_id[asset_id]["variants"].append(filepath.name)

    return dict(assets_by_id)


def build_page_map(assets_by_id: dict) -> dict:
    """Build per-page asset mapping from inventory."""
    page_map = defaultdict(lambda: {"hero": None, "images": [], "gallery": [], "meta": []})

    for asset_id, asset_info in sorted(assets_by_id.items()):
        mapping = ASSET_WIKI_MAP.get(asset_id)
        if mapping is None:
            print(f"  Warning: No wiki mapping for asset ID: {asset_id}", file=sys.stderr)
            continue

        page = mapping["page"]
        role = mapping["role"]
        alt = mapping["alt"]
        primary = asset_info["primary"]

        if primary is None:
            # Use first variant if no v1
            primary = asset_info["all_files"][0] if asset_info["all_files"] else None

        if primary is None:
            continue

        entry = {
            "asset_id": asset_id,
            "file": primary,
            "alt": alt,
            "section": mapping["section"],
            "variants": asset_info["variants"],
        }

        if role == "hero" and page_map[page]["hero"] is None:
            page_map[page]["hero"] = entry
        elif role == "gallery":
            page_map[page]["gallery"].append(entry)
        elif role == "meta":
            page_map[page]["meta"].append(entry)
        else:
            page_map[page]["images"].append(entry)

    # Also build the visual-assets gallery page
    gallery_page = {"hero": None, "images": [], "gallery": [], "meta": [], "all_assets": []}
    for asset_id, asset_info in sorted(assets_by_id.items()):
        mapping = ASSET_WIKI_MAP.get(asset_id, {"alt": asset_id, "section": "Unknown"})
        gallery_page["all_assets"].append({
            "asset_id": asset_id,
            "file": asset_info["primary"] or (asset_info["all_files"][0] if asset_info["all_files"] else None),
            "alt": mapping.get("alt", asset_id),
            "section": mapping.get("section", "Unknown"),
            "variants": asset_info["all_files"],
            "variant_count": len(asset_info["all_files"]),
        })
    page_map["brand/visual-assets.md"] = gallery_page

    return dict(page_map)


def main():
    if len(sys.argv) < 2:
        print("Usage: map-assets-to-wiki.py <generated-dir> [--output FILE]")
        print("\nScans generated visual assets and maps them to wiki documentation pages.")
        sys.exit(1)

    generated_dir = sys.argv[1]

    # Parse --output flag
    output_file = None
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    # Scan assets
    print(f"\nScanning: {generated_dir}")
    assets_by_id = scan_assets(generated_dir)
    print(f"Found {len(assets_by_id)} unique asset IDs")

    # Build page map
    page_map = build_page_map(assets_by_id)

    # Print summary
    print(f"\n{'='*60}")
    print("ASSET → WIKI PAGE MAPPING")
    print(f"{'='*60}")

    for page, assets in sorted(page_map.items()):
        if page == "brand/visual-assets.md":
            continue  # Skip gallery summary
        hero = assets.get("hero")
        images = assets.get("images", [])
        gallery = assets.get("gallery", [])
        meta = assets.get("meta", [])
        total = (1 if hero else 0) + len(images) + len(gallery) + len(meta)

        print(f"\n  {page} ({total} assets)")
        if hero:
            print(f"    hero:    {hero['asset_id']} → {hero['file']}")
        for img in images:
            print(f"    inline:  {img['asset_id']} → {img['file']}")
        for img in gallery:
            print(f"    gallery: {img['asset_id']} → {img['file']}")
        for img in meta:
            print(f"    meta:    {img['asset_id']} → {img['file']}")

    gallery = page_map.get("brand/visual-assets.md", {})
    all_assets = gallery.get("all_assets", [])
    print(f"\n  brand/visual-assets.md (gallery: {len(all_assets)} assets)")

    print(f"\n{'='*60}")

    # Output JSON
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(page_map, f, indent=2)
        print(f"\nSaved: {output_file}")
    else:
        # Default: save next to generated dir
        default_output = Path(generated_dir).parent / "wiki-asset-map.json"
        with open(default_output, 'w') as f:
            json.dump(page_map, f, indent=2)
        print(f"\nSaved: {default_output}")


if __name__ == '__main__':
    main()
