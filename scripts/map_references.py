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
        "name": "Essence Vial",
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

def build_reference_map(parsed_refs):
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

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_refs": sum(1 for r in parsed_refs if r["type"] != "unknown"),
        "primary": primary,
        "reuses": reuses,
        "alternatives": alternatives,
        "styles": styles,
        "demos": demos,
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
    n_unmapped = len(ref_map["unmapped"])
    n_reuse = len(ref_map["reuses"])

    print(f"  Found: {total} reference images")
    print(f"  Primary: {n_primary} | Reuses: {n_reuse} | Alt: {n_alt} | Style: {n_style} | Demo: {n_demo}")
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
    args = parser.parse_args()

    images_dir = os.path.abspath(args.images_dir)

    # Scan
    parsed = scan_images(images_dir)

    # Map
    ref_map = build_reference_map(parsed)

    # Console output
    if not args.json_only:
        print_summary(ref_map, check_new_only=args.check_new)

    # JSON output
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        output_path = os.path.join(os.path.dirname(images_dir), "reference-map.json")

    write_json(ref_map, output_path)

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
