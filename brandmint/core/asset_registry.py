"""
asset_registry.py — Domain-aware asset selection engine (Phase 3).

Given a brand's domain_tags + depth + channel, returns the filtered
and prioritized list of assets to generate.

Usage:
    from asset_registry import select_assets, get_assets_by_generator

    selected = select_assets(
        domain_tags=["app", "marketplace", "travel"],
        depth="focused",
        channel="dtc",
    )
    groups = get_assets_by_generator(selected)
    # groups["identity"] -> [("2B", {...}), ("APP-ICON", {...}), ...]
"""

import os
import yaml


def load_registry(registry_path=None):
    """Load asset-registry.yaml and return the assets dict."""
    if not registry_path:
        registry_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'assets', 'asset-registry.yaml'
        )
    with open(registry_path) as f:
        return yaml.safe_load(f)['assets']


def select_assets(domain_tags, depth='focused', channel='dtc', registry=None):
    """
    Select and prioritize assets based on domain tags, depth, and channel.

    Returns: list of (asset_id, asset_def) tuples, sorted by priority desc.

    Selection logic:
    1. Include all assets tagged "*" (universal)
    2. Include assets where ANY asset tag matches ANY domain_tag
    3. Apply depth pruning (surface skips priority < 6 and non-required)
    4. Apply channel boost (assets matching channel get +2 priority)
    5. Sort by effective priority descending
    """
    if registry is None:
        registry = load_registry()

    selected = []
    for asset_id, asset_def in registry.items():
        tags = asset_def.get('tags', [])

        # Rule 1: Universal assets always included
        if '*' in tags:
            selected.append((asset_id, asset_def))
            continue

        # Rule 2: Tag intersection match
        if domain_tags and any(t in tags for t in domain_tags):
            selected.append((asset_id, asset_def))

    # Rule 3: Depth pruning
    if depth == 'surface':
        selected = [
            (aid, adef) for aid, adef in selected
            if adef.get('required', False) or adef.get('priority', 5) >= 6
        ]

    # Rule 4+5: Sort by effective priority
    def effective_priority(item):
        asset_id, asset_def = item
        base = asset_def.get('priority', 5)
        tags = asset_def.get('tags', [])
        if channel in tags:
            base += 2
        if asset_def.get('required', False):
            base += 5  # Required assets always sort first
        return base

    selected.sort(key=effective_priority, reverse=True)

    return selected


def get_assets_by_generator(selected_assets):
    """Group selected assets by their generator function name.

    Returns: dict mapping generator name -> list of (asset_id, asset_def) tuples.
    """
    groups = {}
    for asset_id, asset_def in selected_assets:
        gen = asset_def.get('generator', 'unknown')
        groups.setdefault(gen, []).append((asset_id, asset_def))
    return groups


def is_new_asset(asset_id):
    """Check if an asset ID is a Phase 3 domain-specific asset (not a legacy 2A-10C asset)."""
    # Legacy assets follow the pattern: digit + letter (2A, 3B, 5D, etc.)
    if not asset_id:
        return True
    if len(asset_id) >= 2 and asset_id[0].isdigit():
        return False
    return True


def print_selection_summary(selected_assets, domain_tags, depth, channel):
    """Print a human-readable summary of asset selection."""
    legacy = [(aid, adef) for aid, adef in selected_assets if not is_new_asset(aid)]
    new = [(aid, adef) for aid, adef in selected_assets if is_new_asset(aid)]

    print(f"  Domain tags: {domain_tags}")
    print(f"  Depth: {depth} | Channel: {channel}")
    print(f"  Selected: {len(selected_assets)} assets ({len(legacy)} legacy + {len(new)} domain-specific)")

    if new:
        print(f"  New assets: {', '.join(aid for aid, _ in new)}")
