"""Domain-aware asset selection engine with optional registry layering."""

import os

import yaml


def _default_registry_path():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "assets", "asset-registry.yaml",
    )


def _normalize_registry_inputs(registry_path=None, registry_paths=None):
    if registry_paths is not None:
        if isinstance(registry_paths, (str, os.PathLike)):
            return [str(registry_paths)]
        return [str(path) for path in registry_paths if str(path).strip()]
    if registry_path is None:
        return [_default_registry_path()]
    if isinstance(registry_path, (list, tuple, set)):
        return [str(path) for path in registry_path if str(path).strip()]
    return [str(registry_path)]


def _load_assets_from_path(registry_path):
    with open(registry_path) as f:
        payload = yaml.safe_load(f) or {}
    assets = payload.get("assets", {})
    if not isinstance(assets, dict):
        raise ValueError(f"Asset registry at {registry_path} does not contain a valid 'assets' mapping")
    return assets


def load_registry(registry_path=None, registry_paths=None):
    """Load one or more asset registries and return a merged assets dict.

    Later registry files override earlier entries when asset IDs collide.
    """
    paths = _normalize_registry_inputs(registry_path=registry_path, registry_paths=registry_paths)
    merged = {}
    for raw_path in paths:
        resolved = os.path.abspath(os.path.expanduser(str(raw_path)))
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"Asset registry not found: {resolved}")
        merged.update(_load_assets_from_path(resolved))
    return merged


def select_assets(
    domain_tags,
    depth="focused",
    channel="dtc",
    registry=None,
    excluded_assets=None,
    registry_path=None,
    registry_paths=None,
):
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
        registry = load_registry(registry_path=registry_path, registry_paths=registry_paths)
    excluded = set(excluded_assets or [])

    selected = []
    for asset_id, asset_def in registry.items():
        if asset_id in excluded:
            continue
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
