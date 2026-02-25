#!/usr/bin/env python3
"""
list_references.py — Brandmint reference catalog query tool.

Query, filter, and display the reference catalog with aesthetic profiles.

Usage:
  python3 scripts/list_references.py                              # List all
  python3 scripts/list_references.py --tag grid                   # Filter by tag
  python3 scripts/list_references.py --tag product-shot --tag editorial
  python3 scripts/list_references.py --density 0.5:1.0            # Axis range
  python3 scripts/list_references.py --boldness 0.0:0.4
  python3 scripts/list_references.py --for 2A                     # Asset compat
  python3 scripts/list_references.py --similar-to ref-2A-bento-grid
  python3 scripts/list_references.py --json                       # JSON output
"""
import argparse
import json
import math
import os
import sys

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: uv pip install pyyaml")
    sys.exit(1)


# =====================================================================
# AESTHETIC DISTANCE
# =====================================================================

AXES = [
    "composition_density", "temporal_register",
    "material_richness", "visual_boldness",
    "editorial_vs_commercial",
]


def aesthetic_distance(profile_a, profile_b):
    """Euclidean distance between two 5-axis aesthetic profiles."""
    return math.sqrt(sum(
        (profile_a.get(ax, 0.5) - profile_b.get(ax, 0.5)) ** 2
        for ax in AXES
    ))


# =====================================================================
# FILTERS
# =====================================================================

def parse_range(range_str):
    """Parse 'lo:hi' range string into (lo, hi) floats."""
    parts = range_str.split(":")
    if len(parts) != 2:
        print(f"ERROR: Invalid range '{range_str}'. Expected format: 0.0:1.0", file=sys.stderr)
        sys.exit(1)
    return float(parts[0]), float(parts[1])


def filter_entries(entries, args):
    """Apply all filters and return matching entries."""
    results = list(entries.items())

    # Filter by type
    if args.type:
        results = [(eid, e) for eid, e in results if e.get("type") == args.type]

    # Filter by tag (all specified tags must be present)
    if args.tag:
        tag_set = set(t.lower() for t in args.tag)
        results = [
            (eid, e) for eid, e in results
            if tag_set.issubset(set(t.lower() for t in e.get("composition_tags", [])))
        ]

    # Filter by asset compatibility
    if getattr(args, "for_pid", None):
        pid_set = set(args.for_pid)
        results = [
            (eid, e) for eid, e in results
            if pid_set.intersection(set(e.get("asset_compatibility", [])))
        ]

    # Filter by axis ranges
    for axis_name, axis_key in [
        ("density", "composition_density"),
        ("temporal", "temporal_register"),
        ("material", "material_richness"),
        ("boldness", "visual_boldness"),
        ("commercial", "editorial_vs_commercial"),
    ]:
        range_str = getattr(args, axis_name, None)
        if range_str:
            lo, hi = parse_range(range_str)
            results = [
                (eid, e) for eid, e in results
                if lo <= e.get("aesthetic", {}).get(axis_key, 0.5) <= hi
            ]

    return results


# =====================================================================
# DISPLAY
# =====================================================================

def print_catalog(entries, catalog_data, args):
    """Print catalog in human-readable format."""
    total = catalog_data.get("total_entries", len(entries))

    if args.similar_to:
        # Similarity mode: sort by distance to target
        target_entry = catalog_data.get("entries", {}).get(args.similar_to)
        if not target_entry:
            print(f"ERROR: Reference '{args.similar_to}' not found in catalog", file=sys.stderr)
            sys.exit(1)

        target_profile = target_entry.get("aesthetic", {})
        scored = []
        for eid, entry in entries:
            if eid == args.similar_to:
                continue
            dist = aesthetic_distance(target_profile, entry.get("aesthetic", {}))
            similarity = round(1.0 / (1.0 + dist), 3)
            scored.append((eid, entry, similarity))

        scored.sort(key=lambda x: -x[2])
        limit = args.limit or 20

        print()
        print(f"SIMILAR TO: {args.similar_to}")
        a = target_profile
        print(f"  Profile: density={a.get('composition_density', 0.5):.2f} "
              f"temporal={a.get('temporal_register', 0.5):.2f} "
              f"material={a.get('material_richness', 0.5):.2f} "
              f"bold={a.get('visual_boldness', 0.5):.2f} "
              f"commercial={a.get('editorial_vs_commercial', 0.5):.2f}")
        print(f"  Tags: {', '.join(target_entry.get('composition_tags', []))}")
        print()
        print(f"TOP {min(limit, len(scored))} MATCHES:")
        print("-" * 90)

        for i, (eid, entry, sim) in enumerate(scored[:limit]):
            a = entry.get("aesthetic", {})
            tags = ", ".join(entry.get("composition_tags", [])[:4])
            compat = ", ".join(entry.get("asset_compatibility", [])[:5])
            print(f"  {sim:.3f}  {eid[:55]:<55s}  [{tags}]")
            if compat:
                print(f"         → compatible: {compat}")

        return

    # Group by type
    groups = {}
    for eid, entry in entries:
        t = entry.get("type", "unknown")
        if t not in groups:
            groups[t] = []
        groups[t].append((eid, entry))

    # Print header
    print()
    filtered = len(entries) < total
    if filtered:
        print(f"BRANDMINT REFERENCE CATALOG — {len(entries)}/{total} refs (filtered)")
    else:
        print(f"BRANDMINT REFERENCE CATALOG — {total} refs")
    print("=" * 70)

    type_order = ["primary", "alternative", "style", "demo", "community"]
    for t in type_order:
        if t not in groups:
            continue

        group_entries = groups[t]
        label = t.upper()
        extra = ""
        if t == "community":
            n_images = len(group_entries)
            extra = f" ({n_images} images)"

        print()
        print(f"{label} ({len(group_entries)}{extra})")
        print("-" * 70)

        for eid, entry in group_entries:
            a = entry.get("aesthetic", {})
            tags = ", ".join(entry.get("composition_tags", [])[:4])
            compat = entry.get("asset_compatibility", [])

            # Format axis summary
            axis_str = (
                f"d={a.get('composition_density', 0.5):.2f} "
                f"t={a.get('temporal_register', 0.5):.2f} "
                f"m={a.get('material_richness', 0.5):.2f} "
                f"b={a.get('visual_boldness', 0.5):.2f} "
                f"c={a.get('editorial_vs_commercial', 0.5):.2f}"
            )

            # Primary refs show prompt_id
            if t == "primary":
                pid = entry.get("prompt_id", "")
                print(f"  {pid:4s}  {entry['file']:<42s}  {axis_str}")
                if tags:
                    print(f"        [{tags}]")
            else:
                truncated_id = eid[:52]
                print(f"  {truncated_id:<54s}  {axis_str}")
                if tags:
                    print(f"        [{tags}]")
                if compat:
                    print(f"        → compatible: {', '.join(compat[:8])}")


def print_json(entries):
    """Print entries as JSON for piping."""
    output = {}
    for eid, entry in entries:
        output[eid] = entry
    print(json.dumps(output, indent=2))


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Brandmint — Reference Catalog Query Tool"
    )
    parser.add_argument(
        "--catalog", "-c",
        default=None,
        help="Path to reference-catalog.yaml (default: references/reference-catalog.yaml)",
    )
    parser.add_argument(
        "--tag", "-t",
        action="append",
        help="Filter by composition tag (can specify multiple)",
    )
    parser.add_argument(
        "--for", dest="for_pid",
        action="append",
        help="Filter by asset compatibility (prompt ID, e.g. 2A)",
    )
    parser.add_argument(
        "--type",
        choices=["primary", "alternative", "style", "demo", "community"],
        help="Filter by reference type",
    )
    parser.add_argument(
        "--density",
        help="Filter by composition_density range (e.g. 0.5:1.0)",
    )
    parser.add_argument(
        "--temporal",
        help="Filter by temporal_register range",
    )
    parser.add_argument(
        "--material",
        help="Filter by material_richness range",
    )
    parser.add_argument(
        "--boldness",
        help="Filter by visual_boldness range",
    )
    parser.add_argument(
        "--commercial",
        help="Filter by editorial_vs_commercial range",
    )
    parser.add_argument(
        "--similar-to",
        help="Find most similar to a specific reference ID",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        help="Limit number of results (for --similar-to)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON for piping",
    )

    args = parser.parse_args()

    # Resolve catalog path
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    catalog_path = args.catalog or os.path.join(repo_root, "references", "reference-catalog.yaml")

    if not os.path.exists(catalog_path):
        print(f"ERROR: Catalog not found at {catalog_path}", file=sys.stderr)
        print("  Run: python3 scripts/classify_references.py", file=sys.stderr)
        sys.exit(1)

    with open(catalog_path) as f:
        catalog_data = yaml.safe_load(f)

    entries = catalog_data.get("entries", {})

    # Apply filters
    filtered = filter_entries(entries, args)

    # Output
    if args.json:
        print_json(filtered)
    else:
        print_catalog(filtered, catalog_data, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
