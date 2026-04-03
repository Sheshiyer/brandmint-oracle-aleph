#!/usr/bin/env python3
"""
map_references.py — Brandmint reference image scanner & mapper.

Scans references/images/, classifies each image by naming convention,
maps to prompt template IDs and models, detects unmapped new references,
and outputs a structured reference-map.json catalog.

Usage:
  python3 scripts/map_references.py /Volumes/madara/2026/brandmint/references/images/
  python3 scripts/map_references.py /Volumes/madara/2026/brandmint/references/images/ --check-new
  python3 scripts/map_references.py /Volumes/madara/2026/brandmint/references/images/ --output /custom/path/reference-map.json
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


# =====================================================================
# KNOWN MAPPING REGISTRY
# =====================================================================
# Sourced from prompt-templates.md — the single source of truth.

PRIMARY_REFS = {
    "2A": {
        "file": "ref-2A-bento-grid.jpg",
        "name": "Bento Grid",
        "model": "nano-banana-pro",
        "supports_image_urls": True,
        "aspect": "16:9",
        "description": "6-module bento grid layout structure (style anchor)",
    },
    "2B": {
        "file": "ref-2B-brand-seal.jpg",
        "name": "Brand Seal",
        "model": "flux-2-pro",
        "supports_image_urls": False,
        "aspect": "1:1",
        "description": "Wax seal / emblem composition",
    },
    "2C": {
        "file": "ref-2C-logo-emboss.jpg",
        "name": "Logo Emboss",
        "model": "flux-2-pro",
        "supports_image_urls": False,
        "aspect": "16:9",
        "description": "Frosted glass logo emboss style",
    },
    "3A": {
        "file": "ref-3A-capsule-collection.jpg",
        "name": "Capsule Collection",
        "model": "flux-2-pro",
        "supports_image_urls": False,
        "aspect": "4:3",
        "description": "Product lineup / flatlay composition",
    },
    "3B": {
        "file": "ref-3B-hero-product.jpg",
        "name": "Hero Product",
        "model": "flux-2-pro",
        "supports_image_urls": False,
        "aspect": "1:1",
        "description": "Individual branded product shots",
    },
    "3C": {
        "file": "ref-3C-essence-vial.jpg",
        "name": "Product Detail",
        "model": "nano-banana-pro",
        "supports_image_urls": True,
        "aspect": "1:1",
        "description": "Branded vessel / vial product shots",
    },
    "4A": {
        "file": "ref-4A-catalog-layout.jpg",
        "name": "Catalog Layout",
        "model": "nano-banana-pro",
        "supports_image_urls": True,
        "aspect": "3:4",
        "description": "Product catalog with spec callouts",
    },
    "4B": {
        "file": "ref-4B-flatlay.jpg",
        "name": "Flatlay",
        "model": "flux-2-pro",
        "supports_image_urls": False,
        "aspect": "1:1",
        "description": "Minimal white product photography",
    },
    "5A": {
        "file": "ref-5A-heritage-engraving.jpg",
        "name": "Heritage Engraving",
        "model": "recraft-v3",
        "supports_image_urls": False,
        "aspect": "1:1",
        "style": "digital_illustration",
        "description": "Fine-line botanical heritage engraving",
    },
    "5B": {
        "file": "ref-5B-campaign-grid.jpg",
        "name": "Campaign Grid",
        "model": "nano-banana-pro",
        "supports_image_urls": True,
        "aspect": "3:4",
        "description": "2-column asymmetric campaign grid",
    },
    "5D": {
        "file": "ref-5D-engine-icons.jpg",
        "name": "Engine Icons",
        "model": "recraft-v3",
        "supports_image_urls": False,
        "aspect": "1:1",
        "style": "vector_illustration/line_circuit",
        "description": "Minimal icon set on solid background",
    },
    "7A": {
        "file": "ref-7A-contact-sheet.jpg",
        "name": "Contact Sheet",
        "model": "nano-banana-pro",
        "supports_image_urls": True,
        "aspect": "1:1",
        "description": "3x3 grid-tiled photo composition",
    },
    "8A": {
        "file": "ref-8A-seeker-poster.jpg",
        "name": "Seeker Poster",
        "model": "nano-banana-pro",
        "supports_image_urls": True,
        "aspect": "3:4",
        "description": "Brand presentation poster layout",
    },
    "9A": {
        "file": "ref-9A-engine-poster.jpg",
        "name": "Engine Poster",
        "model": "nano-banana-pro",
        "supports_image_urls": True,
        "aspect": "3:4",
        "description": "Detailed single-object poster with labels",
    },
}

# 10A-C reuse 7A's grid layout
REUSE_REFS = {
    "10A": "7A",
    "10B": "7A",
    "10C": "7A",
}

# Alt refs: filename -> {relevant_template, description}
ALT_REF_REGISTRY = {
    "ref-alt-glass-editorial.jpg": {
        "relevant_template": "2C",
        "description": "Frosted glass editorial layouts",
    },
    "ref-alt-emboss-monochrome.jpg": {
        "relevant_template": "2C",
        "description": "Monochrome glossy emboss on colored surfaces",
    },
    "ref-alt-chrome-logos.jpg": {
        "relevant_template": "2B",
        "description": "Polished 3D chrome logo renders",
    },
    "ref-alt-3d-sticker-logos.jpg": {
        "relevant_template": "2B",
        "description": "3D tactile logo artifacts",
    },
    "ref-alt-minimal-logos.jpg": {
        "relevant_template": "2B",
        "description": "Clean metallic minimal logo reimaginings",
    },
    "ref-alt-foil-stickers.jpg": {
        "relevant_template": "misc",
        "description": "Crinkled foil / balloon textured brand stickers",
    },
    "ref-alt-leather-duffles.jpg": {
        "relevant_template": "3A",
        "description": "Branded luxury duffle bag lineup",
    },
    "ref-alt-passport-covers.jpg": {
        "relevant_template": "3B",
        "description": "Branded accessory product shots",
    },
    "ref-alt-leather-bags.jpg": {
        "relevant_template": "3A",
        "description": "Branded leather bag product shots",
    },
    "ref-alt-beverage-bottles.jpg": {
        "relevant_template": "3C",
        "description": "Branded bottles on colored backgrounds",
    },
    "ref-alt-branded-shoes.jpg": {
        "relevant_template": "3A",
        "description": "Cross-brand product design collabs",
    },
    "ref-alt-varsity-jackets.jpg": {
        "relevant_template": "3A",
        "description": "Branded apparel in environmental setting",
    },
    "ref-alt-embossed-tshirts.jpg": {
        "relevant_template": "3A",
        "description": "Material texture detail in branded apparel",
    },
    "ref-alt-boxing-gloves.jpg": {
        "relevant_template": "3B",
        "description": "Luxury branded product concept",
    },
    "ref-alt-organic-logo.jpg": {
        "relevant_template": "misc",
        "description": "Logo-as-organic-material concept",
    },
    "ref-alt-calligraphic-initials.jpg": {
        "relevant_template": "5A",
        "description": "Ornate typography / letterform style",
    },
    "ref-alt-dieline-to-3d.jpg": {
        "relevant_template": "misc",
        "description": "Packaging design dieline-to-3D workflow",
    },
    "ref-alt-product-branding-workflow.jpg": {
        "relevant_template": "misc",
        "description": "Product branding workflow diagram",
    },
    "ref-alt-sneaker-collabs.jpg": {
        "relevant_template": "misc",
        "description": "Cross-brand sneaker collab product design",
    },
}

# Style refs: filename -> description
STYLE_REF_REGISTRY = {
    "ref-style-fashion-tutorial.jpg": "Fashion prompt tutorial (3 person photos)",
    "ref-style-bold-portrait-grid.jpg": "Celebrity portraits with bold color blocks",
    "ref-style-collage-portraits.jpg": "Collage/glitch torn-paper portrait effect",
    "ref-style-duotone-faces.jpg": "Minimalist duotone flat vector face illustrations",
    "ref-style-line-portraits.jpg": "B&W minimal line-art portrait icons",
    "ref-style-retro-typography.jpg": "Retro baseball-style brand typography",
    "ref-style-line-sketches.jpg": "Line-art character sketches",
    "ref-style-cartoon-caricatures.jpg": "Colored cartoon caricatures",
    "ref-style-graffiti-overlay.jpg": "Graffiti/crackle face overlays with doodles",
    "ref-style-halftone-portraits.jpg": "Halftone dot comic-style portraits",
    "ref-style-fashion-prompt.jpg": "Fashion prompt with outfit changes",
}

# Demo refs: filename -> description
DEMO_REF_REGISTRY = {
    "ref-demo-aerial-logo.jpg": "Logo made of aerial people (creative concept)",
    "ref-demo-superhero-composite.jpg": "Superhero characters composite",
    "ref-demo-product-design-tutorial.jpg": "Creative product design tutorial slide",
    "ref-demo-metal-grillz.jpg": "Metal grillz/jewelry with brand names",
    "ref-demo-box-christmas-trees.jpg": "Christmas trees made of brand boxes",
}


# =====================================================================
# FILENAME PARSER
# =====================================================================

# Regex patterns for each naming convention
RE_PRIMARY = re.compile(r"^ref-(\d+[A-Z])-(.+)\.(jpg|jpeg|png|webp)$")
RE_ALT = re.compile(r"^ref-alt-(.+)\.(jpg|jpeg|png|webp)$")
RE_STYLE = re.compile(r"^ref-style-(.+)\.(jpg|jpeg|png|webp)$")
RE_DEMO = re.compile(r"^ref-demo-(.+)\.(jpg|jpeg|png|webp)$")
RE_TWITTER = re.compile(r"^ref-tw-(\d+)-([^.]+)\.(jpg|jpeg|png|webp)$")


def parse_filename(filename):
    """Parse a reference image filename into structured metadata.

    Returns dict with: type, prompt_id (if primary), slug, filename
    """
    m = RE_PRIMARY.match(filename)
    if m:
        return {
            "type": "primary",
            "prompt_id": m.group(1),
            "slug": m.group(2),
            "filename": filename,
        }

    m = RE_ALT.match(filename)
    if m:
        return {
            "type": "alt",
            "slug": m.group(1),
            "filename": filename,
        }

    m = RE_STYLE.match(filename)
    if m:
        return {
            "type": "style",
            "slug": m.group(1),
            "filename": filename,
        }

    m = RE_DEMO.match(filename)
    if m:
        return {
            "type": "demo",
            "slug": m.group(1),
            "filename": filename,
        }

    m = RE_TWITTER.match(filename)
    if m:
        return {
            "type": "twitter",
            "seq": int(m.group(1)),
            "slug": m.group(2),
            "filename": filename,
        }

    return {
        "type": "unknown",
        "slug": os.path.splitext(filename)[0],
        "filename": filename,
    }


# =====================================================================
# SCANNER
# =====================================================================

def scan_images(images_dir):
    """Scan directory and return list of parsed reference metadata."""
    if not os.path.isdir(images_dir):
        print(f"ERROR: Directory not found: {images_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(f for f in os.listdir(images_dir)
                   if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))

    results = []
    for f in files:
        parsed = parse_filename(f)
        parsed["exists"] = True
        parsed["path"] = os.path.join(images_dir, f)
        results.append(parsed)

    return results


# =====================================================================
# MAPPER
# =====================================================================

def load_twitter_manifest(twitter_dir):
    """Load Twitter sync manifest.json and return enriched entries.

    Returns list of dicts with: file, seq, author, slug, prompt_text, tags, likes,
    relevance_score, source_url, images[].
    """
    manifest_path = os.path.join(twitter_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return []

    with open(manifest_path) as f:
        manifest = json.load(f)

    entries = []
    for entry in manifest.get("entries", []):
        # Read the paired .prompt.md for full tweet text
        prompt_file = entry.get("prompt_file", "")
        prompt_text = ""
        if prompt_file:
            prompt_path = os.path.join(twitter_dir, prompt_file)
            if os.path.exists(prompt_path):
                with open(prompt_path) as pf:
                    content = pf.read()
                # Extract text between "## Prompt" and next "##" or end
                import re as _re
                m = _re.search(r"## Prompt\n\n(.+?)(?:\n## |\Z)", content, _re.DOTALL)
                if m:
                    prompt_text = m.group(1).strip()

        entries.append({
            "seq": entry.get("seq", 0),
            "author": entry.get("author", "unknown"),
            "slug": entry.get("slug", ""),
            "tweet_id": entry.get("tweet_id", ""),
            "prompt_text": prompt_text,
            "prompt_file": prompt_file,
            "tags": entry.get("tags", []),
            "likes": entry.get("likes", 0),
            "relevance_score": entry.get("relevance_score", 0),
            "images": entry.get("images", []),
        })

    return entries


def build_reference_map(parsed_refs, twitter_dir=None):
    """Build the structured reference map from parsed filenames."""
    primary = {}
    alternatives = {}  # template_id -> list of alt refs
    styles = []
    demos = []
    unmapped = []

    for ref in parsed_refs:
        fname = ref["filename"]

        if ref["type"] == "primary":
            pid = ref["prompt_id"]
            if pid in PRIMARY_REFS:
                entry = dict(PRIMARY_REFS[pid])
                entry["prompt_id"] = pid
                primary[pid] = entry
            else:
                # New primary ref not in known registry
                primary[pid] = {
                    "file": fname,
                    "prompt_id": pid,
                    "name": ref["slug"].replace("-", " ").title(),
                    "model": "unknown",
                    "supports_image_urls": False,
                    "aspect": "unknown",
                    "description": f"NEW — unmapped primary reference for {pid}",
                    "_new": True,
                }

        elif ref["type"] == "alt":
            if fname in ALT_REF_REGISTRY:
                info = ALT_REF_REGISTRY[fname]
                template_id = info["relevant_template"]
                if template_id not in alternatives:
                    alternatives[template_id] = []
                alternatives[template_id].append({
                    "file": fname,
                    "description": info["description"],
                })
            else:
                unmapped.append({
                    "file": fname,
                    "type": "alt",
                    "reason": "Not in known alt registry",
                })

        elif ref["type"] == "style":
            if fname in STYLE_REF_REGISTRY:
                styles.append({
                    "file": fname,
                    "description": STYLE_REF_REGISTRY[fname],
                })
            else:
                unmapped.append({
                    "file": fname,
                    "type": "style",
                    "reason": "Not in known style registry",
                })

        elif ref["type"] == "demo":
            if fname in DEMO_REF_REGISTRY:
                demos.append({
                    "file": fname,
                    "description": DEMO_REF_REGISTRY[fname],
                })
            else:
                unmapped.append({
                    "file": fname,
                    "type": "demo",
                    "reason": "Not in known demo registry",
                })

        elif ref["type"] == "twitter":
            pass  # Counted by scan; enriched from manifest below

        else:
            unmapped.append({
                "file": fname,
                "type": "unknown",
                "reason": "Filename does not match any known pattern",
            })

    # Add reuse entries
    reuses = {}
    for pid, source_pid in REUSE_REFS.items():
        if source_pid in primary:
            reuses[pid] = {
                "file": primary[source_pid]["file"],
                "reuses": source_pid,
                "prompt_id": pid,
                "name": f"Reuses {source_pid}",
                "model": primary[source_pid]["model"],
                "supports_image_urls": primary[source_pid]["supports_image_urls"],
                "aspect": primary[source_pid]["aspect"],
                "description": f"Reuses {source_pid} ({primary[source_pid]['name']}) grid layout",
            }

    # Load Twitter community refs from manifest (enriches with prompt text, tags, etc.)
    # Auto-discover twitter-sync/assets/ relative to images_dir if twitter_dir not given
    twitter = []
    if twitter_dir:
        twitter = load_twitter_manifest(twitter_dir)
    elif parsed_refs:
        # Auto-discover: images_dir/../twitter-sync/assets/
        first_path = parsed_refs[0].get("path", "")
        if first_path:
            images_parent = os.path.dirname(os.path.dirname(first_path))
            candidate = os.path.join(images_parent, "twitter-sync", "assets")
            if os.path.isdir(candidate):
                twitter = load_twitter_manifest(candidate)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_refs": sum(1 for r in parsed_refs if r["type"] != "unknown"),
        "primary": primary,
        "reuses": reuses,
        "alternatives": alternatives,
        "styles": styles,
        "demos": demos,
        "twitter": twitter,
        "unmapped": unmapped,
    }


# =====================================================================
# PYTHON DICT GENERATOR
# =====================================================================

def generate_ref_images_dict(ref_map):
    """Generate REF_IMAGES Python dict literal from the reference map."""
    lines = ["REF_IMAGES = {"]
    for pid in sorted(ref_map["primary"].keys(), key=_sort_prompt_id):
        entry = ref_map["primary"][pid]
        lines.append(f'    "{pid}": "{entry["file"]}",')

    # Add reuses
    for pid in sorted(ref_map["reuses"].keys(), key=_sort_prompt_id):
        entry = ref_map["reuses"][pid]
        lines.append(f'    "{pid}": "{entry["file"]}",  # reuses {entry["reuses"]}')

    lines.append("}")
    return "\n".join(lines)


def generate_alt_refs_dict(ref_map):
    """Generate ALT_REFS Python dict literal from the reference map."""
    lines = ["ALT_REFS = {"]
    for tid in sorted(ref_map["alternatives"].keys(), key=_sort_prompt_id):
        alts = ref_map["alternatives"][tid]
        alt_files = [a["file"] for a in alts]
        lines.append(f'    "{tid}": {alt_files},')
    lines.append("}")
    return "\n".join(lines)


def _sort_prompt_id(pid):
    """Sort prompt IDs: 2A, 2B, 2C, 3A, ... 10A, 10B, 10C, misc."""
    if pid == "misc":
        return (99, "misc")
    m = re.match(r"(\d+)([A-Z]?)", pid)
    if m:
        return (int(m.group(1)), m.group(2))
    return (50, pid)


# =====================================================================
# CONSOLE OUTPUT
# =====================================================================

def print_summary(ref_map, check_new_only=False):
    """Print a human-readable summary to stdout."""
    print()
    print("BRANDMINT — Reference Image Mapper")
    print("=" * 60)

    total = ref_map["total_refs"]
    n_primary = len(ref_map["primary"])
    n_alt = sum(len(v) for v in ref_map["alternatives"].values())
    n_style = len(ref_map["styles"])
    n_demo = len(ref_map["demos"])
    n_twitter = len(ref_map.get("twitter", []))
    n_unmapped = len(ref_map["unmapped"])
    n_reuse = len(ref_map["reuses"])

    print(f"  Found: {total} reference images" + (f" + {n_twitter} community (Twitter)" if n_twitter else ""))
    print(f"  Primary: {n_primary} | Reuses: {n_reuse} | Alt: {n_alt} | Style: {n_style} | Demo: {n_demo}" +
          (f" | Twitter: {n_twitter}" if n_twitter else ""))
    if n_unmapped:
        print(f"  UNMAPPED: {n_unmapped}")
    print()

    if check_new_only:
        if n_unmapped == 0:
            new_primary = [p for p in ref_map["primary"].values() if p.get("_new")]
            if not new_primary:
                print("  All references are mapped. No new refs detected.")
                return
        # Show only new/unmapped
        new_primary = [p for p in ref_map["primary"].values() if p.get("_new")]
        if new_primary:
            print("NEW PRIMARY REFS:")
            for p in new_primary:
                print(f"  {p['prompt_id']:4s}  {p['file']:<40s}  → UNMAPPED")
            print()

        if n_unmapped:
            print(f"UNMAPPED ({n_unmapped}):")
            for u in ref_map["unmapped"]:
                print(f"  {u['file']:<45s}  ({u['type']}: {u['reason']})")
        return

    # Full summary
    print(f"PRIMARY ({n_primary}):")
    for pid in sorted(ref_map["primary"].keys(), key=_sort_prompt_id):
        entry = ref_map["primary"][pid]
        model_short = entry["model"].replace("-", " ").title()
        new_tag = " [NEW]" if entry.get("_new") else ""
        print(f"  {pid:4s}  {entry['file']:<40s}  → {model_short} ({entry['aspect']}){new_tag}")
    print()

    if n_reuse:
        print(f"REUSES ({n_reuse}):")
        for pid in sorted(ref_map["reuses"].keys(), key=_sort_prompt_id):
            entry = ref_map["reuses"][pid]
            print(f"  {pid:4s}  {entry['file']:<40s}  → reuses {entry['reuses']}")
        print()

    if n_alt:
        print(f"ALTERNATIVES ({n_alt}):")
        for tid in sorted(ref_map["alternatives"].keys(), key=_sort_prompt_id):
            for alt in ref_map["alternatives"][tid]:
                print(f"  {tid:4s} alt  {alt['file']:<40s}  → \"{alt['description']}\"")
        print()

    if n_style:
        print(f"STYLES ({n_style}):")
        for s in ref_map["styles"]:
            print(f"  {s['file']:<45s}  → \"{s['description']}\"")
        print()

    if n_demo:
        print(f"DEMOS ({n_demo}):")
        for d in ref_map["demos"]:
            print(f"  {d['file']:<45s}  → \"{d['description']}\"")
        print()

    if n_twitter:
        print(f"TWITTER / COMMUNITY ({n_twitter}):")
        for t in ref_map["twitter"][:10]:  # Show first 10
            img_count = len(t.get("images", []))
            tags_str = ", ".join(t.get("tags", [])[:3]) or "untagged"
            print(f"  [{t['seq']:03d}] @{t['author']:<20s}  {img_count} img  {t['likes']:>5d} likes  [{tags_str}]")
        if n_twitter > 10:
            print(f"  ... and {n_twitter - 10} more")
        print()

    if n_unmapped:
        print(f"UNMAPPED ({n_unmapped}):")
        for u in ref_map["unmapped"]:
            print(f"  {u['file']:<45s}  ({u['type']}: {u['reason']})")
        print()
    else:
        print("NEW/UNMAPPED (0):")
        print("  (none)")
        print()


# =====================================================================
# JSON OUTPUT
# =====================================================================

def write_json(ref_map, output_path):
    """Write reference-map.json."""
    # Strip internal _new flags from output
    clean = json.loads(json.dumps(ref_map))
    for entry in clean.get("primary", {}).values():
        entry.pop("_new", None)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(clean, f, indent=2)
    print(f"  Written: {output_path}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Brandmint — Reference Image Scanner & Mapper"
    )
    parser.add_argument(
        "images_dir",
        help="Path to references/images/ directory",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for reference-map.json (default: ../reference-map.json relative to images_dir)",
    )
    parser.add_argument(
        "--check-new",
        action="store_true",
        help="Only report new/unmapped references",
    )
    parser.add_argument(
        "--print-dict",
        action="store_true",
        help="Print REF_IMAGES and ALT_REFS Python dicts to stdout",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only write JSON, skip console summary",
    )
    parser.add_argument(
        "--twitter-dir",
        help="Path to twitter-sync assets dir (default: auto-discover from images_dir/../twitter-sync/assets/)",
    )
    parser.add_argument(
        "--rebuild-catalog",
        action="store_true",
        help="After building reference-map.json, regenerate reference-catalog.yaml via classify_references.py",
    )
    args = parser.parse_args()

    images_dir = os.path.abspath(args.images_dir)

    # Auto-discover twitter assets dir
    twitter_dir = None
    if args.twitter_dir:
        twitter_dir = os.path.abspath(args.twitter_dir)
    else:
        # Try to find it relative to images_dir (references/images/ -> references/twitter-sync/assets/)
        candidate = os.path.join(os.path.dirname(images_dir), "twitter-sync", "assets")
        if os.path.isdir(candidate):
            twitter_dir = candidate

    # Scan
    parsed = scan_images(images_dir)

    # Map
    ref_map = build_reference_map(parsed, twitter_dir=twitter_dir)

    # Console output
    if not args.json_only:
        print_summary(ref_map, check_new_only=args.check_new)

    # JSON output
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        output_path = os.path.join(os.path.dirname(images_dir), "reference-map.json")

    write_json(ref_map, output_path)

    # Rebuild aesthetic catalog
    if args.rebuild_catalog:
        try:
            from classify_references import build_catalog, write_catalog
        except ImportError:
            # Try relative import from same directory
            scripts_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, scripts_dir)
            from classify_references import build_catalog, write_catalog

        catalog_path = os.path.join(os.path.dirname(images_dir), "reference-catalog.yaml")
        print()
        print("  Rebuilding reference-catalog.yaml...")
        catalog = build_catalog(
            output_path, images_dir,
            twitter_dir=twitter_dir,
            merge_path=catalog_path if os.path.exists(catalog_path) else None,
        )
        write_catalog(catalog, catalog_path)

    # Python dict output
    if args.print_dict:
        print()
        print("# ── Generated REF_IMAGES dict ──")
        print(generate_ref_images_dict(ref_map))
        print()
        print("# ── Generated ALT_REFS dict ──")
        print(generate_alt_refs_dict(ref_map))
        print()

    return 0 if not ref_map["unmapped"] else 1


if __name__ == "__main__":
    sys.exit(main())
