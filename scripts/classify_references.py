#!/usr/bin/env python3
"""
classify_references.py — Brandmint reference image auto-classifier.

Reads prompt text from .prompt.md files and filenames, scores each reference
image on the same 5-axis aesthetic system used by aesthetic_engine.py, and
generates references/reference-catalog.yaml.

Usage:
  python3 scripts/classify_references.py                    # Build catalog
  python3 scripts/classify_references.py --dry-run          # Preview without writing
  python3 scripts/classify_references.py --merge            # Preserve manual edits
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: uv pip install pyyaml")
    sys.exit(1)


# =====================================================================
# REFERENCE CLASSIFIER
# =====================================================================

class ReferenceClassifier:
    """Score reference images on 5 aesthetic axes from prompt text.

    Uses keyword-matching against prompt text and filenames.
    Same axis system as AestheticProfile in aesthetic_engine.py:
      composition_density:      0=sparse/zen → 1=dense/ornate
      temporal_register:        0=futuristic → 1=heritage/ancestral
      material_richness:        0=synthetic  → 1=natural/craft
      visual_boldness:          0=subtle     → 1=bold/architectural
      editorial_vs_commercial:  0=editorial  → 1=commercial/conversion
    """

    # Keyword → axis delta mappings
    COMPOSITION_KEYWORDS = {
        "grid": {"density": 0.15},
        "bento": {"density": 0.15},
        "modular": {"density": 0.10},
        "panel": {"density": 0.10},
        "minimal": {"density": -0.20, "boldness": -0.15},
        "minimalist": {"density": -0.25, "boldness": -0.15},
        "sparse": {"density": -0.25},
        "ornate": {"density": 0.25},
        "poster": {"boldness": 0.15},
        "editorial": {"commercial": -0.20},
        "commercial": {"commercial": 0.20},
        "luxury": {"material": 0.15, "boldness": -0.10},
        "retro": {"temporal": 0.25},
        "futuristic": {"temporal": -0.30},
        "vintage": {"temporal": 0.30},
        "craft": {"material": 0.25},
        "natural": {"material": 0.20},
        "synthetic": {"material": -0.20},
        "portrait": {"density": -0.10, "boldness": 0.10},
        "collage": {"density": 0.20, "boldness": 0.15},
        "diorama": {"density": 0.20, "material": 0.15},
        "isometric": {"density": 0.15, "temporal": -0.10},
        "infographic": {"density": 0.15, "commercial": 0.10},
        "product": {"commercial": 0.15},
        "fashion": {"boldness": 0.10, "commercial": -0.10},
        "illustration": {"temporal": 0.10, "material": -0.10},
        "photography": {"material": 0.10},
        "cinematic": {"boldness": 0.20, "commercial": -0.15},
        "motion": {"boldness": 0.15, "temporal": -0.10},
        "scrapbook": {"density": 0.15, "temporal": 0.15, "material": 0.10},
        "anime": {"temporal": 0.15, "boldness": 0.15},
        "3d": {"temporal": -0.15, "boldness": 0.15},
        "render": {"temporal": -0.15, "boldness": 0.10},
        "mosaic": {"density": 0.20, "temporal": 0.15},
        "synthwave": {"temporal": -0.20, "boldness": 0.25},
        "neon": {"temporal": -0.20, "boldness": 0.25},
        "ceramic": {"material": 0.20, "temporal": 0.15},
        "glass": {"material": -0.10, "temporal": -0.10},
        "stone": {"material": 0.25, "temporal": 0.20},
        "linen": {"material": 0.20, "temporal": 0.15},
        "wood": {"material": 0.20, "temporal": 0.15},
        "emboss": {"material": 0.10, "boldness": 0.10},
        "seal": {"temporal": 0.20, "material": 0.15},
        "engraving": {"temporal": 0.25, "density": 0.10},
        "botanical": {"material": 0.20, "temporal": 0.15},
        "caricature": {"boldness": 0.20, "density": -0.10},
        "avatar": {"density": -0.10, "temporal": -0.10},
        "flatlay": {"density": 0.10, "commercial": 0.10},
        "catalog": {"density": 0.15, "commercial": 0.15},
        "hero": {"boldness": 0.10},
        "campaign": {"commercial": 0.15, "boldness": 0.10},
        "icon": {"density": -0.15, "boldness": -0.10},
        "sticker": {"boldness": 0.10, "temporal": -0.05},
        "chrome": {"material": -0.15, "temporal": -0.15, "boldness": 0.15},
        "leather": {"material": 0.25, "temporal": 0.15},
        "fragrance": {"material": 0.15, "commercial": -0.10},
        "packaging": {"commercial": 0.15, "density": 0.10},
        "lifestyle": {"commercial": -0.10, "material": 0.10},
        "calligraphic": {"temporal": 0.25, "material": 0.10},
        "typography": {"boldness": 0.10},
        "photoshoot": {"commercial": 0.05, "boldness": 0.10},
        "recipe": {"density": 0.10, "material": 0.10},
        "diagram": {"density": 0.10, "commercial": 0.10},
        "evolution": {"density": 0.15, "temporal": 0.10},
        "timeline": {"density": 0.15},
        "superhero": {"boldness": 0.25},
        "car": {"boldness": 0.20, "temporal": -0.10},
        "dominance": {"boldness": 0.25},
    }

    # Composition structure patterns → tags
    STRUCTURE_PATTERNS = {
        r"\bgrid\b": "grid",
        r"\bbento\b": "grid",
        r"\b2[x×]2\b": "grid",
        r"\b3[x×]3\b": "grid",
        r"\bmodular\b": "grid",
        r"\bpanel\b": "grid",
        r"\bposter\b": "poster",
        r"\bplacard\b": "poster",
        r"\bbillboard\b": "poster",
        r"\bproduct\b": "product-shot",
        r"\bbottle\b": "product-shot",
        r"\bpackaging\b": "product-shot",
        r"\bhero shot\b": "product-shot",
        r"\bflatlay\b": "product-shot",
        r"\bportrait\b": "portrait",
        r"\bface\b": "portrait",
        r"\bcharacter\b": "portrait",
        r"\bperson\b": "portrait",
        r"\beditorial\b": "editorial",
        r"\bmagazine\b": "editorial",
        r"\bspread\b": "editorial",
        r"\b3d\b": "3d-render",
        r"\bdiorama\b": "3d-render",
        r"\bisometric\b": "3d-render",
        r"\brender\b": "3d-render",
        r"\billustration\b": "illustration",
        r"\bcollage\b": "collage",
        r"\bscrapbook\b": "collage",
        r"\binfographic\b": "infographic",
        r"\btimeline\b": "infographic",
        r"\bcinematic\b": "cinematic",
        r"\bmotion\b": "cinematic",
        r"\bicon\b": "icon-set",
        r"\blogo\b": "logo",
        r"\bseal\b": "logo",
        r"\bemblem\b": "logo",
        r"\btypography\b": "typography",
        r"\blettering\b": "typography",
        r"\bcalligraph": "typography",
        r"\blifestyle\b": "lifestyle",
        r"\bsynthwave\b": "synthwave",
        r"\bmosaic\b": "mosaic",
        r"\banime\b": "anime",
        r"\bcaticature\b": "caricature",
        r"\bcartoon\b": "caricature",
        r"\bavatar\b": "avatar",
    }

    # Asset compatibility mapping: composition tag sets → prompt IDs
    COMPAT_RULES = [
        ({"grid", "editorial"}, ["2A", "5B", "7A", "10A"]),
        ({"grid"}, ["2A", "7A", "10A"]),
        ({"product-shot"}, ["3A", "3B", "3C", "4A", "4B"]),
        ({"product-shot", "editorial"}, ["3A", "3B", "3C", "4A"]),
        ({"poster"}, ["8A", "9A"]),
        ({"poster", "portrait"}, ["8A"]),
        ({"portrait"}, ["8A"]),
        ({"editorial"}, ["2A", "5B"]),
        ({"logo"}, ["2B", "2C"]),
        ({"icon-set"}, ["5D"]),
        ({"illustration"}, ["5A"]),
        ({"3d-render"}, ["9A"]),
        ({"infographic"}, ["9A"]),
        ({"cinematic"}, ["8A", "5B"]),
        ({"lifestyle"}, ["3A", "3B", "4A"]),
        ({"collage"}, ["5B", "7A"]),
        ({"typography"}, ["2B", "8A"]),
        ({"caricature"}, ["8A"]),
        ({"avatar"}, ["8A"]),
    ]

    # Model affinity patterns
    MODEL_PATTERNS = {
        "nano-banana": "nano-banana-pro",
        "nano banana": "nano-banana-pro",
        "gemini": "nano-banana-pro",
        "flux": "flux-2-pro",
        "recraft": "recraft-v3",
        "midjourney": "midjourney",
        "gpt-image": "gpt-image-1",
        "chatgpt": "gpt-image-1",
        "dall-e": "gpt-image-1",
    }

    def classify(self, prompt_text, filename, existing_tags=None):
        """Return aesthetic profile + composition_tags + asset_compatibility.

        Args:
            prompt_text: Full prompt text from .prompt.md file
            filename: Image filename (used for keyword extraction)
            existing_tags: Optional list of tags from manifest

        Returns:
            dict with aesthetic, composition_tags, model_affinity, asset_compatibility
        """
        axes = {
            "density": 0.5, "temporal": 0.5, "material": 0.5,
            "boldness": 0.5, "commercial": 0.5,
        }

        combined_text = (prompt_text + " " + filename).lower()
        words = set(re.findall(r'[a-z]{3,}', combined_text))

        # Score keywords
        matched_keywords = []
        for keyword, deltas in self.COMPOSITION_KEYWORDS.items():
            if keyword in words or any(keyword in w for w in words):
                for axis, delta in deltas.items():
                    axes[axis] = max(0.0, min(1.0, axes[axis] + delta))
                matched_keywords.append(keyword)

        # Detect composition structure
        composition_tags = self._detect_composition(combined_text, matched_keywords)

        # Add existing manifest tags if provided
        if existing_tags:
            for tag in existing_tags:
                tag_lower = tag.lower().replace(" ", "-")
                if tag_lower not in composition_tags:
                    composition_tags.append(tag_lower)

        # Infer asset compatibility
        asset_compat = self._infer_asset_compatibility(composition_tags)

        # Detect model affinity
        model_affinity = self._detect_model_affinity(combined_text)

        return {
            "aesthetic": {
                "composition_density": round(axes["density"], 2),
                "temporal_register": round(axes["temporal"], 2),
                "material_richness": round(axes["material"], 2),
                "visual_boldness": round(axes["boldness"], 2),
                "editorial_vs_commercial": round(axes["commercial"], 2),
            },
            "composition_tags": sorted(set(composition_tags)),
            "model_affinity": sorted(set(model_affinity)),
            "asset_compatibility": sorted(set(asset_compat)),
        }

    def _detect_composition(self, text, matched_keywords):
        """Detect composition structure tags from text patterns."""
        tags = []
        for pattern, tag in self.STRUCTURE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                if tag not in tags:
                    tags.append(tag)
        return tags

    def _infer_asset_compatibility(self, composition_tags):
        """Map composition tags to compatible prompt IDs."""
        tag_set = set(composition_tags)
        compat = set()

        for required_tags, pids in self.COMPAT_RULES:
            if required_tags.issubset(tag_set):
                compat.update(pids)

        return sorted(compat)

    def _detect_model_affinity(self, text):
        """Detect which AI models this reference style works best with."""
        models = []
        for pattern, model in self.MODEL_PATTERNS.items():
            if pattern in text:
                if model not in models:
                    models.append(model)
        return models if models else ["nano-banana-pro"]


# =====================================================================
# CATALOG BUILDER
# =====================================================================

def build_catalog(ref_map_path, images_dir, twitter_dir=None, merge_path=None):
    """Build the reference catalog from reference-map.json and prompt files.

    Args:
        ref_map_path: Path to reference-map.json
        images_dir: Path to references/images/ directory
        twitter_dir: Path to twitter-sync/assets/ directory (auto-discovered if None)
        merge_path: If set, merge with existing catalog at this path

    Returns:
        dict: The catalog data structure ready for YAML serialization
    """
    classifier = ReferenceClassifier()

    # Load reference-map.json
    with open(ref_map_path) as f:
        ref_map = json.load(f)

    # Auto-discover twitter dir if not given
    if twitter_dir is None:
        candidate = os.path.join(os.path.dirname(images_dir), "twitter-sync", "assets")
        if os.path.isdir(candidate):
            twitter_dir = candidate

    # Load existing catalog for merge
    existing_entries = {}
    if merge_path and os.path.exists(merge_path):
        with open(merge_path) as f:
            existing = yaml.safe_load(f) or {}
        existing_entries = existing.get("entries", {})

    entries = {}

    # ── PRIMARY REFS ──
    for pid, entry in ref_map.get("primary", {}).items():
        filename = entry["file"]
        entry_id = os.path.splitext(filename)[0]
        description = entry.get("description", "")

        result = classifier.classify(description, filename)

        catalog_entry = {
            "file": filename,
            "type": "primary",
            "prompt_id": pid,
            "name": entry.get("name", ""),
            "aesthetic": result["aesthetic"],
            "composition_tags": result["composition_tags"],
            "model_affinity": [entry.get("model", "unknown")],
            "asset_compatibility": [pid],
            "description": description,
        }

        # Merge: preserve manual edits
        if entry_id in existing_entries:
            _merge_entry(catalog_entry, existing_entries[entry_id])

        entries[entry_id] = catalog_entry

    # ── REUSE REFS ──
    # Reuses share the same file as the source primary ref, so no separate catalog entry needed.

    # ── ALTERNATIVE REFS ──
    for pid, alts in ref_map.get("alternatives", {}).items():
        for alt in alts:
            filename = alt["file"]
            entry_id = os.path.splitext(filename)[0]
            description = alt.get("description", "")

            result = classifier.classify(description, filename)
            result["asset_compatibility"] = sorted(set(result["asset_compatibility"] + [pid]))

            catalog_entry = {
                "file": filename,
                "type": "alternative",
                "related_pid": pid,
                "aesthetic": result["aesthetic"],
                "composition_tags": result["composition_tags"],
                "model_affinity": result["model_affinity"],
                "asset_compatibility": result["asset_compatibility"],
                "description": description,
            }

            if entry_id in existing_entries:
                _merge_entry(catalog_entry, existing_entries[entry_id])

            entries[entry_id] = catalog_entry

    # ── STYLE REFS ──
    for style in ref_map.get("styles", []):
        filename = style["file"]
        entry_id = os.path.splitext(filename)[0]
        description = style.get("description", "")

        result = classifier.classify(description, filename)

        catalog_entry = {
            "file": filename,
            "type": "style",
            "aesthetic": result["aesthetic"],
            "composition_tags": result["composition_tags"],
            "model_affinity": result["model_affinity"],
            "asset_compatibility": result["asset_compatibility"],
            "description": description,
        }

        if entry_id in existing_entries:
            _merge_entry(catalog_entry, existing_entries[entry_id])

        entries[entry_id] = catalog_entry

    # ── DEMO REFS ──
    for demo in ref_map.get("demos", []):
        filename = demo["file"]
        entry_id = os.path.splitext(filename)[0]
        description = demo.get("description", "")

        result = classifier.classify(description, filename)

        catalog_entry = {
            "file": filename,
            "type": "demo",
            "aesthetic": result["aesthetic"],
            "composition_tags": result["composition_tags"],
            "model_affinity": result["model_affinity"],
            "asset_compatibility": result["asset_compatibility"],
            "description": description,
        }

        if entry_id in existing_entries:
            _merge_entry(catalog_entry, existing_entries[entry_id])

        entries[entry_id] = catalog_entry

    # ── TWITTER / COMMUNITY REFS ──
    for tw in ref_map.get("twitter", []):
        seq = tw.get("seq", 0)
        author = tw.get("author", "unknown")
        tweet_id = tw.get("tweet_id", "")
        likes = tw.get("likes", 0)
        tags = tw.get("tags", [])
        images = tw.get("images", [])

        # Read prompt text from .prompt.md file
        prompt_text = tw.get("prompt_text", "")
        if not prompt_text and twitter_dir:
            prompt_file = tw.get("prompt_file", "")
            if prompt_file:
                prompt_path = os.path.join(twitter_dir, prompt_file)
                if os.path.exists(prompt_path):
                    prompt_text = _read_prompt_text(prompt_path)

        # Create entry for each image
        for img in images:
            filename = img.get("file", "")
            if not filename:
                continue

            entry_id = os.path.splitext(filename)[0]
            result = classifier.classify(prompt_text, filename, existing_tags=tags)

            catalog_entry = {
                "file": filename,
                "type": "community",
                "source": {
                    "author": f"@{author}",
                    "tweet_id": tweet_id,
                    "likes": likes,
                },
                "aesthetic": result["aesthetic"],
                "composition_tags": result["composition_tags"],
                "model_affinity": result["model_affinity"],
                "asset_compatibility": result["asset_compatibility"],
                "description": _truncate(prompt_text, 120) if prompt_text else filename.replace("-", " "),
            }

            if entry_id in existing_entries:
                _merge_entry(catalog_entry, existing_entries[entry_id])

            entries[entry_id] = catalog_entry

    catalog = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_entries": len(entries),
        "entries": entries,
    }

    return catalog


def _read_prompt_text(prompt_path):
    """Extract prompt text from a .prompt.md file."""
    with open(prompt_path) as f:
        content = f.read()

    # Extract text between "## Prompt" and next "##" or end
    m = re.search(r"## Prompt\n\n(.+?)(?:\n## |\Z)", content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def _truncate(text, max_len):
    """Truncate text to max_len, adding ellipsis if needed."""
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 3].rstrip() + "..."


def _merge_entry(new_entry, existing_entry):
    """Merge: existing manual aesthetic scores override auto-generated ones."""
    if "aesthetic" in existing_entry:
        # Check if the existing entry has manually edited scores
        # (We preserve the existing aesthetic if it differs from auto)
        new_entry["aesthetic"] = existing_entry["aesthetic"]
    if "composition_tags" in existing_entry:
        # Merge tags: keep both auto and manual
        combined = set(new_entry.get("composition_tags", []))
        combined.update(existing_entry.get("composition_tags", []))
        new_entry["composition_tags"] = sorted(combined)
    if "asset_compatibility" in existing_entry:
        combined = set(new_entry.get("asset_compatibility", []))
        combined.update(existing_entry.get("asset_compatibility", []))
        new_entry["asset_compatibility"] = sorted(combined)


def write_catalog(catalog, output_path):
    """Write catalog to YAML file."""
    # Custom YAML representer for clean output
    class CatalogDumper(yaml.SafeDumper):
        pass

    def _represent_str(dumper, data):
        if "\n" in data:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    CatalogDumper.add_representer(str, _represent_str)

    header = (
        "# references/reference-catalog.yaml\n"
        "# Brandmint Reference Catalog — Aesthetic Taxonomy\n"
        f"# Auto-generated by: python3 scripts/classify_references.py\n"
        "# Manual edits preserved on re-run (--merge flag)\n"
        "#\n"
        "# Aesthetic axes (0.0-1.0):\n"
        "#   composition_density:     0=sparse/zen → 1=dense/ornate\n"
        "#   temporal_register:       0=futuristic → 1=heritage/ancestral\n"
        "#   material_richness:       0=synthetic  → 1=natural/craft\n"
        "#   visual_boldness:         0=subtle     → 1=bold/architectural\n"
        "#   editorial_vs_commercial: 0=editorial  → 1=commercial/conversion\n"
        "\n"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(header)
        yaml.dump(catalog, f, Dumper=CatalogDumper, default_flow_style=False,
                  sort_keys=False, allow_unicode=True, width=120)

    print(f"  Written: {output_path} ({catalog['total_entries']} entries)")


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Brandmint — Reference Image Auto-Classifier"
    )
    parser.add_argument(
        "--ref-map", "-r",
        default=None,
        help="Path to reference-map.json (default: references/reference-map.json)",
    )
    parser.add_argument(
        "--images-dir", "-i",
        default=None,
        help="Path to references/images/ (default: references/images/)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output path for catalog YAML (default: references/reference-catalog.yaml)",
    )
    parser.add_argument(
        "--twitter-dir",
        default=None,
        help="Path to twitter-sync/assets/ (default: auto-discover)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview catalog without writing to disk",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Preserve manual edits in existing catalog",
    )

    args = parser.parse_args()

    # Resolve paths relative to repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ref_map_path = args.ref_map or os.path.join(repo_root, "references", "reference-map.json")
    images_dir = args.images_dir or os.path.join(repo_root, "references", "images")
    output_path = args.output or os.path.join(repo_root, "references", "reference-catalog.yaml")
    twitter_dir = args.twitter_dir

    if not os.path.exists(ref_map_path):
        print(f"ERROR: reference-map.json not found at {ref_map_path}", file=sys.stderr)
        print("  Run: python3 scripts/map_references.py references/images/", file=sys.stderr)
        sys.exit(1)

    merge_path = output_path if args.merge else None

    print()
    print("BRANDMINT — Reference Classifier")
    print("=" * 50)

    catalog = build_catalog(ref_map_path, images_dir, twitter_dir=twitter_dir, merge_path=merge_path)

    # Print summary
    type_counts = {}
    for entry in catalog["entries"].values():
        t = entry.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"  Classified: {catalog['total_entries']} references")
    for t, count in sorted(type_counts.items()):
        print(f"    {t}: {count}")

    if args.dry_run:
        print()
        print("  DRY RUN — showing first 5 entries:")
        print("  " + "-" * 40)
        for i, (entry_id, entry) in enumerate(catalog["entries"].items()):
            if i >= 5:
                print(f"  ... and {catalog['total_entries'] - 5} more")
                break
            a = entry["aesthetic"]
            tags = ", ".join(entry.get("composition_tags", [])[:4])
            print(f"  {entry_id}")
            print(f"    density={a['composition_density']} temporal={a['temporal_register']} "
                  f"material={a['material_richness']} bold={a['visual_boldness']} "
                  f"commercial={a['editorial_vs_commercial']}")
            print(f"    tags: [{tags}]")
            print(f"    compat: {entry.get('asset_compatibility', [])}")
        return 0

    write_catalog(catalog, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
