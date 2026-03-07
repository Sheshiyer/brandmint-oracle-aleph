#!/usr/bin/env python3
"""
Generate Tryambakam Noesis visual assets using FAL AI Nano Banana Pro.

Reads prompt templates from references/twitter-sync/assets/, substitutes brand
variables, and calls the FAL API. Generates 2 seed variants per asset.

Usage:
    python scripts/generate_noesis_assets.py --priority 1
    python scripts/generate_noesis_assets.py --ids BK-01 LG-01 LG-02
    python scripts/generate_noesis_assets.py --all
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "references" / "twitter-sync" / "assets"
OUTPUT_DIR = Path("/Volumes/madara/2026/twc-vault/01-Projects/tryambakam-noesis/brand-docs-final/generated-v4-nano")
LOGO_PATH = Path("/Volumes/madara/2026/twc-vault/01-Projects/tryambakam-noesis/brand-docs-final/Brand Visual Identity/logo/1x/Asset 3.png")

# Nano Banana Pro on FAL
FAL_API_BASE = "https://queue.fal.run"
MODEL_ID = "fal-ai/nano-banana-pro"
SEEDS = [42, 7777]  # 2 variants per asset

# Brand identity
BRAND_NAME = "Tryambakam Noesis"
BRAND_VARS = {
    "palette": "Void Black #070B1D, Witness Violet #2D0050, Flow Indigo #0B50FB, Sacred Gold #C5A017, Coherence Emerald #10B5A7, Parchment #F0EDE3",
    "primary_color": "Witness Violet #2D0050",
    "accent_color": "Sacred Gold #C5A017",
    "bg_color": "Void Black #070B1D",
    "typography": "Panchang (headings) + Satoshi (body)",
    "tagline": "Self-Consciousness as Technology",
    "materials": "bronze, amber glass, obsidian, ceramic, aged leather, brass, terrazzo",
    "aesthetic": "Bioluminescent Solarpunk",
}

# Style suffix appended to every prompt for brand consistency
STYLE_SUFFIX = (
    "\n\nSTYLE OVERRIDE: Bioluminescent Solarpunk aesthetic. "
    "Dark-field photography with light emanating from within organic structures. "
    "Material palette: bronze, amber glass, obsidian, ceramic, aged leather, brass, terrazzo. "
    "Sacred geometry integrated structurally, not decoratively. "
    "Color palette: Void Black #070B1D background, Witness Violet #2D0050, Sacred Gold #C5A017, "
    "Coherence Emerald #10B5A7 accents. No faces. No generic AI look. "
    "Cinematic, material-rich rendering. 8K resolution."
)

# ---------------------------------------------------------------------------
# Asset definitions — maps asset_id → (prompt_ref, brand_overrides)
# ---------------------------------------------------------------------------

ASSETS = {
    # Priority 1 — Brand Identity
    "BK-01": {
        "ref": 284,
        "title": "Brand Kit Bento Grid",
        "vars": {"industry": "consciousness technology & self-awareness platform"},
        "aspect": "16:9",
        "use_logo_ref": True,
    },
    "LG-01": {
        "ref": 293,
        "title": "Natural Element 3D Logo",
        "vars": {"materials": "obsidian, amber, bronze, sacred geometry fractals"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "LG-02": {
        "ref": 233,
        "title": "Glass Logo",
        "vars": {"color": "Witness Violet #2D0050 with Sacred Gold #C5A017 rim light"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "LG-03": {
        "ref": 241,
        "title": "Dark Metallic Logo",
        "vars": {"material": "aged bronze with patina, deep void black background"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "LG-04": {
        "ref": 253,
        "title": "Calligraphic Monogram",
        "vars": {"letter": "TN", "bg_override": "Void Black #070B1D"},
        "aspect": "1:1",
        "use_logo_ref": False,
    },
    # Priority 1 — Icons
    "IC-01": {
        "ref": 254,
        "title": "Engine Icons Set",
        "vars": {"characters": "16 sacred geometry engine symbols: Vimshottari wheel, Nakshatra constellation, Chakra-Kosha layers, Human Design bodygraph, Gene Keys hexagram, Astrocartography globe, Enneagram, Numerology sigil, Tarot arcana, TCM meridian, Biorhythm wave, HRV pulse, Biofield aura, Raga notation, Birth Blueprint mandala, Daily Practice ritual"},
        "aspect": "16:9",
        "use_logo_ref": False,
    },
    "IC-02": {
        "ref": 256,
        "title": "Wing Navigation Icons",
        "vars": {"concepts": "13 icons: Observer eye, Integration spiral, Trinity pillars, Engine grid, Open book, Plumber wrench, Biosensor heart, Protocol terminal, Treasure compass, Apothecary vial, Rule origin, Journey door, Canticle wave"},
        "aspect": "16:9",
        "use_logo_ref": False,
    },
    # Priority 1 — Products
    "PR-01": {
        "ref": 248,
        "title": "Essential Oil Attar",
        "vars": {"product_type": "sacred essential oil attar in amber glass vessel with bronze cap, frankincense and sandalwood blend"},
        "aspect": "4:5",
        "use_logo_ref": True,
    },
    "PR-02": {
        "ref": 262,
        "title": "Mushroom Tincture",
        "vars": {"product_type": "medicinal mushroom tincture (Lion's Mane temporal mapping), matte ceramic bottle with micro-embossed sacred geometry"},
        "aspect": "4:5",
        "use_logo_ref": True,
    },
    "PR-05": {
        "ref": 295,
        "title": "Apothecary Flat Lay",
        "vars": {"items": "essential oil attars, orgone pyramid, crystal array, resonance pendant, sacred sage bundle, ritual candle, brass singing bowl, dark wood surface"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    # Priority 2 — Products
    "PR-03": {
        "ref": 239,
        "title": "Minimal Product Mockup",
        "vars": {"product": "orgone energy pyramid, matte obsidian resin with embedded sacred geometry brass coil"},
        "aspect": "1:1",
        "use_logo_ref": False,
    },
    "PR-04": {
        "ref": 246,
        "title": "Creative Product Concept",
        "vars": {"concept": "wearable biosensor pendant that maps somatic coherence, bronze and ceramic with amber LED"},
        "aspect": "4:5",
        "use_logo_ref": True,
    },
    "PR-06": {
        "ref": 250,
        "title": "Dieline Box Design",
        "vars": {"product": "Noesis Apothecary gift box, matte black with Sacred Gold foil stamp"},
        "aspect": "16:9",
        "use_logo_ref": True,
    },
    "PR-07": {
        "ref": 237,
        "title": "Creative Product Designer",
        "vars": {"concept": "consciousness calibration device: a brass and obsidian biofeedback reader shaped like an ancient astrolabe"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    # Priority 2 — Wing Heroes
    "WG-01": {
        "ref": 266,
        "title": "Grid Poster Campaign",
        "vars": {"slogan": "WITNESS YOURSELF", "theme": "sacred geometry, bioluminescent, void-to-light"},
        "aspect": "4:5",
        "use_logo_ref": True,
    },
    "WG-02": {
        "ref": 236,
        "title": "Swiss Design Poster",
        "vars": {"concept": "Tryambakam Noesis typographic poster, Panchang font, Self-Consciousness as Technology"},
        "aspect": "4:5",
        "use_logo_ref": False,
    },
    "WG-03": {
        "ref": 318,
        "title": "Three-Panel Manifesto",
        "vars": {"slogan": "WITNESS YOURSELF", "philosophy": "Self-Consciousness as Technology"},
        "aspect": "9:16",
        "use_logo_ref": True,
    },
    "WG-04": {
        "ref": 261,
        "title": "Heritage Engraving",
        "vars": {"style": "copperplate engraving of the Tryambakam sigil as 19th century botanical-scientific illustration"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "IC-03": {
        "ref": 272,
        "title": "Kha-Ba-La System Icons",
        "vars": {"characters": "10 Kha-Ba-La (Kabbalistic Tree of Life) sephiroth as minimalist icons: Kether crown, Chokmah wisdom, Binah understanding, Chesed mercy, Geburah strength, Tiphareth beauty, Netzach victory, Hod splendor, Yesod foundation, Malkuth kingdom"},
        "aspect": "16:9",
        "use_logo_ref": False,
    },
    "WG-08": {
        "ref": 284,
        "title": "Brand Guidelines Spread",
        "vars": {"industry": "holistic wellness & consciousness technology, show typography specimens, color palette swatches, sacred geometry grid system, brand voice manifesto"},
        "aspect": "16:9",
        "use_logo_ref": True,
    },
    # Priority 3 — Merch & Marketing
    "MR-01": {
        "ref": 245,
        "title": "Capsule Collection",
        "vars": {"items": "tech-wellness accessories: meditation headband, somatic wristband, resonance pendant, travel altar case, ritual journal"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "MR-02": {
        "ref": 263,
        "title": "Sticker Pack",
        "vars": {"elements": "sacred geometry sigil, third eye, lotus, chakra wheels, Tryambakam mandala, Om symbol, DNA helix, tree of life"},
        "aspect": "1:1",
        "use_logo_ref": False,
    },
    "MR-03": {
        "ref": 267,
        "title": "Crumpled Sticker",
        "vars": {"sticker_color": "Sacred Gold #C5A017 background with Void Black logo"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "MR-04": {
        "ref": 310,
        "title": "Social Media Ad",
        "vars": {"tagline": "WITNESS YOURSELF", "cta": "Begin Your Journey"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "MR-05": {
        "ref": 291,
        "title": "Social Media Collage",
        "vars": {"style": "sacred wellness lifestyle, meditation, plant medicine, sacred geometry overlays"},
        "aspect": "4:5",
        "use_logo_ref": True,
    },
    "WG-05": {
        "ref": 265,
        "title": "Brand as Wellness Club",
        "vars": {"concept": "Tryambakam Noesis as an elite consciousness training club, badge with sacred geometry crest"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
    "WG-06": {
        "ref": 305,
        "title": "Retro Storefront",
        "vars": {"toggle": "ON", "facade": "Art Nouveau apothecary with stained glass, bronze fixtures, Witness Violet awning"},
        "aspect": "1:1",
        "use_logo_ref": False,
    },
    "WG-07": {
        "ref": 260,
        "title": "Photo Grid Tribute",
        "vars": {"theme": "consciousness exploration: meditation spaces, sacred sites, botanical gardens, observatory domes, ancient libraries"},
        "aspect": "1:1",
        "use_logo_ref": True,
    },
}


# ---------------------------------------------------------------------------
# FAL API helpers
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/.claude/.env"))
    key = os.environ.get("FAL_KEY")
    if not key:
        print("ERROR: FAL_KEY not set", file=sys.stderr)
        sys.exit(1)
    return key


def upload_logo(logo_path: Path) -> str:
    """Upload local logo to FAL file storage and return URL."""
    try:
        import fal_client
    except ImportError:
        print("ERROR: fal_client not installed. Run: pip install fal-client", file=sys.stderr)
        sys.exit(1)
    print(f"Uploading logo: {logo_path}", file=sys.stderr)
    url = fal_client.upload_file(str(logo_path))
    print(f"  Logo URL: {url}", file=sys.stderr)
    return url


def submit_request(arguments: dict, api_key: str) -> dict:
    url = f"{FAL_API_BASE}/{MODEL_ID}"
    data = json.dumps(arguments).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_result(queue_resp: dict, api_key: str, max_wait: int = 300) -> dict:
    """Poll FAL queue until result is ready."""
    status_url = queue_resp.get("status_url")
    response_url = queue_resp.get("response_url")
    request_id = queue_resp.get("request_id", "")
    
    if not status_url:
        status_url = f"{FAL_API_BASE}/{MODEL_ID}/requests/{request_id}/status"
    if not response_url:
        response_url = f"{FAL_API_BASE}/{MODEL_ID}/requests/{request_id}"
    
    headers = {"Authorization": f"Key {api_key}"}
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            req = urllib.request.Request(status_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 405:
                try:
                    req2 = urllib.request.Request(response_url, headers=headers, method="GET")
                    with urllib.request.urlopen(req2, timeout=60) as resp2:
                        return json.loads(resp2.read().decode("utf-8"))
                except urllib.error.HTTPError:
                    time.sleep(5)
                    continue
            time.sleep(5)
            continue
        
        s = status.get("status", "UNKNOWN")
        if s == "COMPLETED":
            resp_url = status.get("response_url", response_url)
            req2 = urllib.request.Request(resp_url, headers=headers, method="GET")
            with urllib.request.urlopen(req2, timeout=60) as resp2:
                return json.loads(resp2.read().decode("utf-8"))
        if s in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Generation failed: {json.dumps(status)}")
        
        pos = status.get("queue_position", "?")
        print(f"    Status: {s} (pos: {pos})", file=sys.stderr)
        time.sleep(5)
    
    raise TimeoutError(f"Timed out after {max_wait}s")


def download_image(url: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as resp:
        output_path.write_bytes(resp.read())


# ---------------------------------------------------------------------------
# Prompt loading & customization
# ---------------------------------------------------------------------------

def find_prompt_file(ref_num: int) -> Optional[Path]:
    """Find the prompt.md file for a given reference number."""
    pattern = f"ref-tw-{ref_num}-"
    for f in PROMPTS_DIR.glob(f"{pattern}*.prompt.md"):
        return f
    return None


def extract_prompt_text(prompt_file: Path) -> str:
    """Extract the prompt text from a prompt.md file."""
    text = prompt_file.read_text()
    # Extract content after "## Prompt" header
    match = re.search(r"## Prompt\s*\n(.+?)(?=\n## |\Z)", text, re.DOTALL)
    if match:
        prompt = match.group(1).strip()
    else:
        # Fallback: skip frontmatter, take everything
        prompt = text.strip()
    
    # Remove tweet links and metadata
    prompt = re.sub(r"https?://t\.co/\S+", "", prompt)
    prompt = re.sub(r"\(access Nano Banana[^)]*\)", "", prompt)
    prompt = re.sub(r"\(change[^)]*\)", "", prompt)
    prompt = re.sub(r"\(get more[^)]*\)", "", prompt)
    prompt = re.sub(r"(?:Grab your prompt:|Just change \[BRAND NAME\] and enjoy.*?👉 Prompt:|👉 Prompt:|Prompt:|Nano Banana (?:smart )?prompt:?|Step 1.*?SYSTEM PROMPT:)\s*", "", prompt, flags=re.DOTALL)
    prompt = re.sub(r"_{3,}", "", prompt)
    prompt = re.sub(r"\n{3,}", "\n\n", prompt)
    return prompt.strip()


def customize_prompt(raw_prompt: str, asset_id: str, asset_def: dict) -> str:
    """Replace brand placeholders and append style suffix."""
    prompt = raw_prompt
    
    # Standard brand name replacements
    prompt = prompt.replace("[BRAND NAME]", BRAND_NAME)
    prompt = prompt.replace("[BRAND]", BRAND_NAME)
    prompt = prompt.replace("[Brand Name]", BRAND_NAME)
    prompt = prompt.replace("[brand name]", BRAND_NAME)
    
    # Asset-specific variable replacements
    asset_vars = asset_def.get("vars", {})
    
    # Industry
    if "{INDUSTRY}" in prompt and "industry" in asset_vars:
        prompt = prompt.replace("{INDUSTRY}", asset_vars["industry"])
    elif "{INDUSTRY}" in prompt:
        prompt = prompt.replace("{INDUSTRY}", "consciousness technology & self-awareness platform")
    
    # Color
    if "[COLOR]" in prompt and "color" in asset_vars:
        prompt = prompt.replace("[COLOR]", asset_vars["color"])
    elif "[COLOR]" in prompt:
        prompt = prompt.replace("[COLOR]", "Witness Violet #2D0050")
    
    # Character/concept names for icon prompts
    if "[CHARACTER NAME]" in prompt and "characters" in asset_vars:
        prompt = prompt.replace("[CHARACTER NAME]", asset_vars["characters"])
    if "[NAME]" in prompt and "characters" in asset_vars:
        prompt = prompt.replace("[NAME]", asset_vars["characters"])
    
    # Subject toggle for storefront
    if "[SUBJECT_TOGGLE]" in prompt:
        prompt = prompt.replace("[SUBJECT_TOGGLE]", asset_vars.get("toggle", "ON"))
    
    # Product type overrides
    if "product_type" in asset_vars:
        # For beverage prompts, replace the generic product description
        prompt = re.sub(
            r"launching a new functional wellness elixir.*?product photography\.",
            f"presenting its signature product: {asset_vars['product_type']}. "
            "The aesthetic is 'Sacred Premium' — organic, ritualistic, and sophisticated, "
            "like artisanal apothecary product photography.",
            prompt,
            flags=re.DOTALL,
        )
    
    # For flat lay prompts, inject specific items
    if "items" in asset_vars and "flat lay" in asset_def.get("title", "").lower():
        prompt += f"\n\nSPECIFIC OBJECTS: {asset_vars['items']}"
    
    # Append brand style suffix
    prompt += STYLE_SUFFIX
    
    return prompt


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def generate_asset(
    asset_id: str,
    asset_def: dict,
    api_key: str,
    logo_url: Optional[str] = None,
    dry_run: bool = False,
) -> list[dict]:
    """Generate 2 seed variants for a single asset."""
    prompt_file = find_prompt_file(asset_def["ref"])
    if not prompt_file:
        print(f"  SKIP {asset_id}: prompt file for ref {asset_def['ref']} not found", file=sys.stderr)
        return []
    
    raw_prompt = extract_prompt_text(prompt_file)
    if len(raw_prompt) < 20:
        print(f"  SKIP {asset_id}: prompt too short ({len(raw_prompt)} chars) — may be image-only tweet", file=sys.stderr)
        return []
    
    prompt = customize_prompt(raw_prompt, asset_id, asset_def)
    
    # Build image reference URLs
    image_urls = []
    if asset_def.get("use_logo_ref") and logo_url:
        image_urls.append(logo_url)
    
    results = []
    for i, seed in enumerate(SEEDS):
        variant = f"v{i+1}"
        filename = f"{asset_id}-{asset_def['title'].lower().replace(' ', '-')}-{variant}.png"
        output_path = OUTPUT_DIR / filename
        
        if output_path.exists():
            print(f"  EXISTS {asset_id}/{variant}: {output_path.name}", file=sys.stderr)
            results.append({"id": asset_id, "variant": variant, "path": str(output_path), "status": "exists"})
            continue
        
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  GENERATING {asset_id}/{variant}: {asset_def['title']}", file=sys.stderr)
        print(f"  Aspect: {asset_def.get('aspect', '1:1')} | Seed: {seed}", file=sys.stderr)
        print(f"  Prompt: {prompt[:120]}...", file=sys.stderr)
        
        if dry_run:
            print(f"  [DRY RUN] Would generate {filename}", file=sys.stderr)
            results.append({"id": asset_id, "variant": variant, "status": "dry_run"})
            continue
        
        arguments = {
            "prompt": prompt,
            "aspect_ratio": asset_def.get("aspect", "1:1"),
            "resolution": "2K",
            "output_format": "png",
            "num_images": 1,
            "seed": seed,
        }
        if image_urls:
            arguments["image_urls"] = image_urls
        
        try:
            queue_resp = submit_request(arguments, api_key)
            
            if "request_id" in queue_resp:
                print(f"    Queued: {queue_resp['request_id']}", file=sys.stderr)
                result = poll_result(queue_resp, api_key)
            else:
                result = queue_resp
            
            # Extract image URL
            img_url = None
            if "images" in result and result["images"]:
                img_url = result["images"][0].get("url")
            elif "image" in result:
                img_url = result["image"].get("url")
            
            if not img_url:
                print(f"    ERROR: No image URL in response", file=sys.stderr)
                results.append({"id": asset_id, "variant": variant, "status": "error", "error": "no_url"})
                continue
            
            download_image(img_url, output_path)
            print(f"    SAVED: {output_path}", file=sys.stderr)
            results.append({
                "id": asset_id, "variant": variant, "path": str(output_path),
                "status": "generated", "image_url": img_url,
            })
            
            # Brief cooldown between requests
            time.sleep(1)
            
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            results.append({"id": asset_id, "variant": variant, "status": "error", "error": str(e)})
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Tryambakam Noesis assets via FAL Nano Banana Pro")
    parser.add_argument("--priority", type=int, help="Generate only assets of this priority (1, 2, or 3)")
    parser.add_argument("--ids", nargs="+", help="Generate specific asset IDs (e.g., BK-01 LG-01)")
    parser.add_argument("--all", action="store_true", help="Generate all assets")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without calling API")
    parser.add_argument("--no-logo-ref", action="store_true", help="Skip logo upload as image reference")
    args = parser.parse_args()
    
    if not (args.priority or args.ids or args.all):
        parser.print_help()
        sys.exit(1)
    
    # Priority mapping
    priority_map = {}
    for aid, adef in ASSETS.items():
        if aid.startswith(("BK", "LG", "IC-01", "IC-02", "PR-01", "PR-02", "PR-05")):
            priority_map[aid] = 1
        elif aid.startswith(("IC-03", "PR-03", "PR-04", "PR-06", "PR-07", "WG-01", "WG-02", "WG-03", "WG-04", "WG-08")):
            priority_map[aid] = 2
        else:
            priority_map[aid] = 3
    
    # Determine which assets to generate
    if args.ids:
        target_ids = [i for i in args.ids if i in ASSETS]
    elif args.priority:
        target_ids = [aid for aid, p in priority_map.items() if p == args.priority]
    else:
        target_ids = list(ASSETS.keys())
    
    if not target_ids:
        print("No matching assets found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Tryambakam Noesis Asset Generation", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"Assets to generate: {len(target_ids)}", file=sys.stderr)
    print(f"Variants per asset: {len(SEEDS)}", file=sys.stderr)
    print(f"Total images: {len(target_ids) * len(SEEDS)}", file=sys.stderr)
    print(f"Output: {OUTPUT_DIR}", file=sys.stderr)
    print(f"Model: {MODEL_ID}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    # Setup
    api_key = get_api_key()
    
    logo_url = None
    if not args.no_logo_ref and LOGO_PATH.exists():
        any_needs_logo = any(ASSETS[aid].get("use_logo_ref") for aid in target_ids)
        if any_needs_logo and not args.dry_run:
            logo_url = upload_logo(LOGO_PATH)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate
    all_results = []
    for i, asset_id in enumerate(target_ids, 1):
        asset_def = ASSETS[asset_id]
        print(f"\n[{i}/{len(target_ids)}] {asset_id}: {asset_def['title']}", file=sys.stderr)
        results = generate_asset(asset_id, asset_def, api_key, logo_url, dry_run=args.dry_run)
        all_results.extend(results)
    
    # Summary
    generated = sum(1 for r in all_results if r["status"] == "generated")
    existed = sum(1 for r in all_results if r["status"] == "exists")
    errors = sum(1 for r in all_results if r["status"] == "error")
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"SUMMARY: {generated} generated, {existed} existed, {errors} errors", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    # Output JSON manifest
    print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
