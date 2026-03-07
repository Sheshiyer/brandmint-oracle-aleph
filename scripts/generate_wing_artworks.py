#!/usr/bin/env python3
"""Generate wing-specific artworks for Tryambakam Noesis infinite-canvas website.

Each image is crafted to visually represent the specific concept of its wing,
using Nano Banana Pro via FAL AI with the brand's bioluminescent solarpunk aesthetic.

Usage:
    python scripts/generate_wing_artworks.py --all
    python scripts/generate_wing_artworks.py --ids W00 W01 W02
    python scripts/generate_wing_artworks.py --wings  # Only 13 wings (no supplementary)
    python scripts/generate_wing_artworks.py --supplementary  # Only 7 supplementary
    python scripts/generate_wing_artworks.py --dry-run --all
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.claude/.env"))

FAL_KEY = os.environ.get("FAL_KEY", "")
FAL_ENDPOINT = "fal-ai/nano-banana-pro"
FAL_BASE = "https://queue.fal.run"

LOGO_PATH = "/Volumes/madara/2026/twc-vault/01-Projects/tryambakam-noesis/brand-docs-final/Brand Visual Identity/logo/1x/Asset 3.png"
OUTPUT_DIR = "/Volumes/madara/2026/twc-vault/01-Projects/tryambakam-noesis/brand-docs-final/generated-v4-wings"

# Brand style constants woven into every prompt
BRAND_STYLE = """
Aesthetic: Bioluminescent Solarpunk. Dark-field composition with light emanating from within.
Palette: Void Black #070B1D background, Witness Violet #2D0050 accents, Flow Indigo #0B50FB energy lines, Sacred Gold #C5A017 highlights, Coherence Emerald #10B5A7 bio-signals, Parchment #F0EDE3 text.
Materials: Bronze, amber glass, obsidian, ceramic, aged leather, brass instruments, terrazzo.
Typography feel: Cinzel Decorative or similar serif for headings.
Lighting: Volumetric, rim-lit, bioluminescent glow from organic elements. Dark moody atmosphere with selective illumination.
Quality: Ultra-high-resolution, editorial photography quality, no text overlays unless specified.
"""

# ─── WING PROMPTS ────────────────────────────────────────────────────────────
# Each prompt is carefully written to represent the wing's actual concept

WING_ARTWORKS = [
    {
        "id": "W00",
        "filename": "01-hero",
        "title": "Tryambakam Noesis — Self-Generating Code Well",
        "prompt": f"""A cinematic hero image for "Tryambakam Noesis" — a consciousness technology platform. 
Center composition: A sacred geometry lotus-star sigil (interlocking bronze wireframe) floating above an obsidian altar. 
From the sigil, three luminous energy streams spiral outward — gold (Spirit/Kha), indigo (Body/Ba), and emerald (Inertia/La) — forming a recursive Möbius-like pattern.
The background is deep void black (#070B1D) with faint star-field particles. Beneath the sigil, circuit-like patterns etched in bronze glow faintly, suggesting code running through organic material.
The overall feeling: ancient temple meets quantum computer. Sacred yet technological. Still yet alive.
{BRAND_STYLE}""",
    },
    {
        "id": "W01",
        "filename": "02-witness-yourself",
        "title": "Witness Yourself — The Observer Pattern",
        "prompt": f"""A meditative figure seated in lotus position, rendered in translucent obsidian glass. The figure's chest cavity reveals a luminous eye — the "witness" — radiating soft gold light.
Around the figure, fragmented mirror shards float in orbit, each reflecting a different emotion or identity fragment (joy, grief, ambition, fear) — but the central figure remains still, unmoved, observing.
Thin indigo threads connect each fragment back to the witness eye, suggesting integration without attachment.
The atmosphere is deeply contemplative — dark field, volumetric fog, with only the inner light illuminating the scene.
{BRAND_STYLE}""",
    },
    {
        "id": "W02",
        "filename": "03-self-integration",
        "title": "Self Integration — Regenerative Intelligence Field",
        "prompt": f"""A living, breathing intelligence field visualized as a toroidal energy structure. The torus is composed of thousands of tiny bioluminescent filaments — emerald and gold — pulsing in a breath-like rhythm (dense at center, expanding outward).
At the core of the torus, a human silhouette stands with arms slightly open, as if receiving and radiating simultaneously. The field wraps around the figure like a cocoon of light.
No mechanical parts — everything is organic, mycelium-like, neural. The field regenerates itself: broken strands at the edges regrow inward.
Dark void background. The only light comes from within the field itself.
{BRAND_STYLE}""",
    },
    {
        "id": "W03",
        "filename": "04-three-pillars",
        "title": "Three Pillars — The Elemental Trinity",
        "prompt": f"""Three monumental pillars standing on a dark obsidian platform, each representing a knowledge system:
PILLAR 1 (left): "Vedic Intelligence" — carved from aged sandstone with Sanskrit glyphs and Jyotisha star charts etched in gold leaf. Warm amber glow.
PILLAR 2 (center): "Western Precision" — polished chrome and glass, with Gene Keys hexagrams and Human Design bodygraph circuits visible inside. Cool blue-white light.
PILLAR 3 (right): "Biofield & Sonic" — living wood wrapped in bioluminescent moss, with sound wave patterns and HRV sine curves flowing through it. Emerald-green pulsing light.
Where the three pillars meet at their capitals, their energies merge into a single unified beam of golden light shooting upward.
{BRAND_STYLE}""",
    },
    {
        "id": "W04",
        "filename": "05-sixteen-engines",
        "title": "Sixteen Engines — The Computational Core",
        "prompt": f"""A circular mandala-like arrangement of 16 engine modules, viewed from above. Each engine is a unique bronze-and-glass mechanical-organic hybrid — part clockwork, part living organism.
The 16 engines are arranged in a 4×4 compass pattern with four quadrants labeled by faint gold text: STABILIZE (north), HEAL (east), CREATE (south), MUTATE (west).
Fine golden threads connect each engine to its neighbors, forming 256 intersection points that glow with tiny emerald sparks.
At the very center: a dark void — the "witness space" — from which all computation radiates. The overall impression is a celestial navigation instrument crossed with a biological processor.
{BRAND_STYLE}""",
    },
    {
        "id": "W05",
        "filename": "06-somatic-canticles",
        "title": "Somatic Canticles — A Story That Reads You Back",
        "prompt": f"""Three luxurious hardcover books arranged in a reverent still life on dark velvet. The books are bound in matte black leather with gold foil sacred geometry embossing on the spines.
The pages of the middle book are fanned open, and from the pages, bioluminescent gold text seems to float upward like living calligraphy — the story literally rising from the page.
Thin golden threads extend from the floating text to a faint human silhouette (the reader), suggesting the book is reading the person as much as being read.
Each book's cover has a subtle Kosha layer symbol: Physical (root/red), Energetic (sacral/orange), Mental (gold).
{BRAND_STYLE}""",
    },
    {
        "id": "W06",
        "filename": "07-financial-biosensor",
        "title": "Financial Biosensor — Clarity Over Anxiety",
        "prompt": f"""A premium dashboard interface rendered as a physical brass-and-glass instrument — like a Victorian-era scientific device crossed with a modern HUD.
The device displays: a real-time HRV waveform in emerald green, a Tattva cycle wheel with five elemental phases, and a 7-day foresight bar chart with green/amber/red windows.
At the center, a large circular gauge shows "ACT" on one side and "WAIT" on the other, with a gold needle pointing confidently to one side.
The device sits on a dark leather desk surface, surrounded by brass gears and amber glass vials — suggesting alchemy applied to financial decision-making. Warm, focused, premium lighting.
{BRAND_STYLE}""",
    },
    {
        "id": "W07",
        "filename": "08-witness-agents",
        "title": "Witness Agents — Structure & Flow",
        "prompt": f"""Two figures standing face to face in a dark ceremonial space, mirror images yet fundamentally different:
PICHET (left): A figure composed of geometric crystal lattice — sharp, structured, precise. Bronze metallic finish. Represents discipline, routine, containment. Holds a golden compass.
ALETHEOS (right): A figure composed of flowing bioluminescent tendrils — organic, emergent, fluid. Emerald and violet luminescence. Represents intuition, creativity, surrender. Holds a flowering branch.
Between them, their energies interweave — structure and flow creating a double helix of gold and green light that spirals upward into a unified field.
The space between is the temple of self-consciousness — where both agents serve the witness.
{BRAND_STYLE}""",
    },
    {
        "id": "W08",
        "filename": "09-initiation-protocols",
        "title": "Initiation Protocols — Micro-rituals, Macro-transformation",
        "prompt": f"""A sacred ritual space rendered in dark obsidian and bronze. Center: a meditation seat surrounded by a circular array of singing bowls, each bowl emitting visible sound waves in different colors (the 16 engine frequencies).
Above the seat, a holographic timer interface shows "7:21" with a breath cycle indicator — a luminous sine wave expanding and contracting.
Thin golden lines on the floor form a progressive spiral pattern — each ring represents a completed initiation cycle, with the innermost rings glowing brightest (progressive unlocking).
Seeds of light float in the air, each one a micro-ritual waiting to be activated. The atmosphere: dawn light through temple windows, ancient meets futuristic.
{BRAND_STYLE}""",
    },
    {
        "id": "W09",
        "filename": "10-infinite-treasure",
        "title": "Infinite Treasure — The Hunt Never Ends",
        "prompt": f"""A vast treasure chamber divided into four illuminated quadrants, viewed from above:
DHARMA (top-left): Ancient scrolls and star charts glowing with purpose. Gold light.
ARTHA (top-right): Brass coins, gemstones, and an alchemist's scale balanced perfectly. Amber light.
KAMA (bottom-left): A flowering lotus in full bloom, surrounded by sensory artifacts — incense, silk, rosewater. Rose-pink light.
MOKSHA (bottom-right): An empty mirror reflecting infinite depth — the treasure of liberation is the absence of seeking. Pure white-blue light.
At the center where all quadrants meet: a recursive spiral staircase descending endlessly — each answer leads to a deeper question. The hunt never ends.
{BRAND_STYLE}""",
    },
    {
        "id": "W10",
        "filename": "11-apothecary",
        "title": "The Apothecary — Alchemy You Can Touch",
        "prompt": f"""A luxurious apothecary cabinet — dark walnut wood with brass hardware — containing 12 meticulously arranged wellness products. Each product is a physical engine:
Top shelf: Essential oil bottles in amber glass with gold labels (Frankincense for Purusha Witness, Sandalwood for Temporal Mapping).
Middle shelf: Mushroom tincture vials (Lion's Mane, Reishi, Cordyceps) in dark glass with emerald caps, plus a bundle of sacred sage wrapped in gold thread.
Bottom shelf: Obsidian orgone pyramids with embedded sacred geometry, ceramic vessels with ground botanicals.
Each product has a faint bioluminescent glow matching its engine color. The cabinet is lit from within, warm and inviting. A mortar and pestle sits on the counter. The feeling: luxury herbalism meets consciousness technology.
{BRAND_STYLE}""",
    },
    {
        "id": "W11",
        "filename": "12-first-rule",
        "title": "The First Rule — Where Consciousness Begins",
        "prompt": f"""A single luminous eye — the Witness — floating in absolute void. The eye is neither human nor mechanical; it is made of recursive golden fractals that zoom infinitely inward.
Reflected in the eye's iris: three nested words arranged in a recursive loop — "CODE" → "CODER" → "RUNTIME" → back to "CODE" — forming an infinite triangle of self-reference.
From the eye, three concentric rings expand outward like ripples in dark water — each ring represents a layer of consciousness becoming aware of itself.
The composition is severe, minimal, philosophical. Maximum negative space. The void IS the canvas. The eye IS the subject. No decoration — pure concept.
{BRAND_STYLE}""",
    },
    {
        "id": "W12",
        "filename": "13-begin-journey",
        "title": "Begin Journey — The Noesis Awaits",
        "prompt": f"""A massive ornate gateway made of interlocking bronze sacred geometry patterns — the Tryambakam Noesis sigil forms the arch. Through the gateway: an infinite corridor of light, with each step forward revealing more detail, more depth, more questions.
A single figure stands at the threshold, small against the vastness, about to step through. The figure is backlit by warm golden light from within the gateway.
On the floor before the gateway, a simple inscription glows: the infinity symbol ∞.
The atmosphere: dawn breaking through an ancient temple. Anticipation. Wonder. The beginning that has no end. No prerequisites — just the willingness to witness.
{BRAND_STYLE}""",
    },
    # ─── SUPPLEMENTARY IMAGES ──────────────────────────────────────────────
    {
        "id": "S14",
        "filename": "14-plumber",
        "title": "The Plumber — System Maintenance",
        "prompt": f"""A mystical artisan-engineer figure in a workshop, maintaining the inner machinery of consciousness. The figure wears leather apron and brass goggles, surrounded by disassembled engine components — gears, crystal oscillators, golden circuit boards.
The workshop is a cave-like space with walls lined with tools: tuning forks, calibration instruments, sacred geometry templates. On the workbench: a partially disassembled consciousness engine being cleaned and recalibrated.
The feeling: the humble maintenance of sacred technology. Not the architect, not the user — the plumber who keeps everything flowing.
{BRAND_STYLE}""",
    },
    {
        "id": "S15",
        "filename": "15-noesis-dashboard",
        "title": "Noesis Dashboard — Command Center",
        "prompt": f"""A holographic command center dashboard floating in dark space. The dashboard shows:
Center: A human body outline with active engine indicators at key points (chakra-like, but technological) — each glowing its engine color.
Left panel: Real-time biorhythm graphs — HRV coherence, breath rate, Tattva cycle phase.
Right panel: Engine status grid — 16 small module indicators showing active/standby states.
Top bar: Current compass direction (STABILIZE), active protocol name, coherence score.
The UI aesthetic is premium dark with bronze accents, emerald data lines, gold highlights. Floating interface with depth-of-field blur on background elements. Feels like a spacecraft navigation system for inner exploration.
{BRAND_STYLE}""",
    },
    {
        "id": "S16",
        "filename": "16-compass",
        "title": "Compass — 256 Directions",
        "prompt": f"""A magnificent brass compass rose, viewed from directly above. The compass has 256 tiny direction markers around its circumference, with four cardinal directions prominently labeled: STABILIZE (N), HEAL (E), CREATE (S), MUTATE (W).
The compass face is made of dark obsidian with gold inlaid geometric patterns. 16 engine symbols are arranged in concentric rings between the center and the edge.
The needle is a luminous golden arrow that seems to pulse with inner light, pointing toward the viewer's current direction.
The compass floats above a star field, casting shadows that form sacred geometry on the surface below. Ancient navigation instrument reimagined for consciousness exploration.
{BRAND_STYLE}""",
    },
    {
        "id": "S17",
        "filename": "17-mentorship",
        "title": "Mentorship — Guided Witness",
        "prompt": f"""Two figures seated across from each other in a sacred space — mentor and student. The mentor is partially translucent, revealing an inner architecture of golden light networks (their consciousness map). The student is more opaque, with only a few emerging light points.
Between them, the mentor's golden threads extend toward the student's emerging light points — not imposing, but illuminating what's already there. The space between is filled with floating symbolic artifacts: books, instruments, botanical elements.
The setting: a twilight garden with bioluminescent plants, bronze lanterns, and a reflecting pool between them that shows the student's potential future state.
{BRAND_STYLE}""",
    },
    {
        "id": "S18",
        "filename": "18-soulbound-token",
        "title": "Soulbound Token — Digital Identity",
        "prompt": f"""A singular glowing token floating in void — half physical artifact, half digital construct. The left half is an ancient bronze coin with the Tryambakam Noesis sacred geometry sigil embossed. The right half dissolves into holographic blockchain data — hexagonal nodes, encrypted hash patterns, luminous data streams.
The token is soulbound — thin golden chains anchor it to a faint human silhouette below, representing identity that cannot be transferred, only earned.
Around the token: orbital rings of micro-data (timestamps, engine activations, completed protocols) forming a personal history that lives on-chain.
{BRAND_STYLE}""",
    },
    {
        "id": "S19",
        "filename": "19-constellation-field",
        "title": "Constellation Field — Network of Witnesses",
        "prompt": f"""A vast cosmic field viewed from above — hundreds of individual witness points (each a small luminous node) connected by gossamer golden threads forming constellation patterns.
Each node represents one practitioner in the Noesis network. Brighter nodes have been active longer; newly awakened nodes glow faintly emerald. The constellation patterns they form mirror the sacred geometry of the Tryambakam sigil.
At certain high-density clusters, the merged energy creates larger bioluminescent blooms — collective consciousness emerging from individual practice.
The overall view resembles both a neural network and a star field — the macro mirrors the micro.
{BRAND_STYLE}""",
    },
    {
        "id": "S20",
        "filename": "20-brand-bento",
        "title": "Brand Bento — Identity Overview",
        "prompt": f"""Tryambakam Noesis — consciousness technology and wellness brand.

Act as a Lead Brand Designer creating a comprehensive "Brand Identity System" presentation (Bento-Grid Layout).

Generate a single, high-resolution bento-grid board containing 6 distinct modules:

Block 1 (Hero): A cinematic key visual showing the sacred geometry lotus-star sigil floating above an obsidian altar with bioluminescent energy. Dark, luxurious, mystical.
Block 2 (Social): An Instagram post mockup with bold serif headline "Self-Consciousness as Technology" and a dark moody lifestyle image.
Block 3 (Palette): 6 vertical color swatches — Void Black #070B1D, Witness Violet #2D0050, Flow Indigo #0B50FB, Sacred Gold #C5A017, Coherence Emerald #10B5A7, Parchment #F0EDE3 — with HEX codes displayed.
Block 4 (Typography): The word "Panchang" displayed in an elegant decorative serif style. Subtext: "Primary Typeface".
Block 5 (Logo): The sacred geometry interlocking lotus-star pattern in bronze wireframe on black.
Block 6 (Manifesto): "You are the code. You are the coder. You are the runtime." Archetype: The Mystic. Voice: Wise, Esoteric, Direct.
{BRAND_STYLE}""",
    },
]

def upload_logo():
    """Upload logo to FAL for style reference."""
    if not os.path.exists(LOGO_PATH):
        print(f"  Logo not found: {LOGO_PATH}")
        return None
    url = "https://fal.run/fal-ai/any-llm/storage/upload"
    with open(LOGO_PATH, "rb") as f:
        data = f.read()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Key {FAL_KEY}",
            "Content-Type": "image/png",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            logo_url = result.get("url", result.get("file_url", ""))
            print(f"  Logo URL: {logo_url}")
            return logo_url
    except Exception as e:
        print(f"  Logo upload error: {e}")
        return None


def queue_generation(prompt, aspect_ratio, seed, logo_url=None):
    """Submit image generation to FAL queue."""
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": "2K",
        "output_format": "png",
        "seed": seed,
        "num_images": 1,
    }
    if logo_url:
        payload["image_urls"] = [logo_url]

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{FAL_BASE}/{FAL_ENDPOINT}",
        data=data,
        headers={
            "Authorization": f"Key {FAL_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result.get("request_id")


def poll_result(request_id, timeout=300):
    """Poll FAL queue for result."""
    url = f"{FAL_BASE}/{FAL_ENDPOINT}/requests/{request_id}/status"
    start = time.time()
    while time.time() - start < timeout:
        req = urllib.request.Request(url, headers={"Authorization": f"Key {FAL_KEY}"})
        try:
            with urllib.request.urlopen(req) as resp:
                status = json.loads(resp.read())
            state = status.get("status", "UNKNOWN")
            pos = status.get("queue_position", "?")
            print(f"    Status: {state} (pos: {pos})")
            if state == "COMPLETED":
                # Fetch result
                result_url = f"{FAL_BASE}/{FAL_ENDPOINT}/requests/{request_id}"
                req2 = urllib.request.Request(result_url, headers={"Authorization": f"Key {FAL_KEY}"})
                with urllib.request.urlopen(req2) as resp2:
                    return json.loads(resp2.read())
            elif state in ("FAILED", "CANCELLED"):
                return None
        except urllib.error.HTTPError as e:
            print(f"    Poll error: {e}")
            return None
        time.sleep(5)
    print("    TIMEOUT")
    return None


def download_image(image_url, output_path):
    """Download image from URL."""
    req = urllib.request.Request(image_url, headers={"Authorization": f"Key {FAL_KEY}"})
    with urllib.request.urlopen(req) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())


def generate_artwork(artwork, logo_url, output_dir, seeds, dry_run=False):
    """Generate one artwork with multiple seed variants."""
    results = []
    for si, seed in enumerate(seeds):
        variant = f"v{si+1}"
        out_name = f"{artwork['filename']}-{variant}.png"
        out_path = os.path.join(output_dir, out_name)

        if os.path.exists(out_path):
            print(f"  EXISTS {artwork['id']}/{variant}: {out_name}")
            results.append({"id": artwork["id"], "variant": variant, "path": out_path, "status": "exists"})
            continue

        print(f"\n{'='*60}")
        print(f"  GENERATING {artwork['id']}/{variant}: {artwork['title']}")
        print(f"  Aspect: 1:1 | Seed: {seed}")
        print(f"  Prompt: {artwork['prompt'][:100]}...")

        if dry_run:
            print(f"  [DRY RUN] Would generate {out_name}")
            results.append({"id": artwork["id"], "variant": variant, "status": "dry_run"})
            continue

        try:
            request_id = queue_generation(artwork["prompt"], "1:1", seed, logo_url)
            print(f"    Queued: {request_id}")
            result = poll_result(request_id)
            if result and result.get("images"):
                img_url = result["images"][0]["url"]
                download_image(img_url, out_path)
                print(f"    SAVED: {out_path}")
                results.append({
                    "id": artwork["id"], "variant": variant,
                    "path": out_path, "status": "generated",
                    "image_url": img_url,
                })
            else:
                print(f"    ERROR: No image in result")
                results.append({"id": artwork["id"], "variant": variant, "status": "error", "error": "No image"})
        except urllib.error.HTTPError as e:
            print(f"    ERROR: {e}")
            results.append({"id": artwork["id"], "variant": variant, "status": "error", "error": str(e)})
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"id": artwork["id"], "variant": variant, "status": "error", "error": str(e)})

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate Tryambakam Noesis wing artworks")
    parser.add_argument("--all", action="store_true", help="Generate all 20 images")
    parser.add_argument("--wings", action="store_true", help="Generate only 13 wing images")
    parser.add_argument("--supplementary", action="store_true", help="Generate only 7 supplementary images")
    parser.add_argument("--ids", nargs="+", help="Generate specific IDs (e.g., W00 W01 S14)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without generating")
    parser.add_argument("--no-logo-ref", action="store_true", help="Skip logo reference upload")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 7777], help="Seeds for variants")
    parser.add_argument("--output", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    # Select artworks
    if args.ids:
        artworks = [a for a in WING_ARTWORKS if a["id"] in args.ids]
    elif args.wings:
        artworks = [a for a in WING_ARTWORKS if a["id"].startswith("W")]
    elif args.supplementary:
        artworks = [a for a in WING_ARTWORKS if a["id"].startswith("S")]
    elif args.all:
        artworks = WING_ARTWORKS
    else:
        parser.print_help()
        sys.exit(1)

    if not artworks:
        print("No artworks matched the selection.")
        sys.exit(1)

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("Tryambakam Noesis Wing Artwork Generation")
    print("=" * 60)
    print(f"Artworks to generate: {len(artworks)}")
    print(f"Variants per artwork: {len(args.seeds)}")
    print(f"Total images: {len(artworks) * len(args.seeds)}")
    print(f"Output: {output_dir}")
    print(f"Model: {FAL_ENDPOINT}")
    print("=" * 60)

    # Upload logo
    logo_url = None
    if not args.no_logo_ref and not args.dry_run:
        print(f"\nUploading logo: {LOGO_PATH}")
        logo_url = upload_logo()

    all_results = []
    for i, artwork in enumerate(artworks):
        print(f"\n[{i+1}/{len(artworks)}] {artwork['id']}: {artwork['title']}")
        results = generate_artwork(artwork, logo_url, output_dir, args.seeds, args.dry_run)
        all_results.extend(results)

    # Summary
    generated = sum(1 for r in all_results if r["status"] == "generated")
    existed = sum(1 for r in all_results if r["status"] == "exists")
    errors = sum(1 for r in all_results if r["status"] == "error")
    print(f"\n{'='*60}")
    print(f"SUMMARY: {generated} generated, {existed} existed, {errors} errors")
    print("=" * 60)
    print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
