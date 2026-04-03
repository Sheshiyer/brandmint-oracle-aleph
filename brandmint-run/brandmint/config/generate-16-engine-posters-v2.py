#!/usr/bin/env python3
"""
Generate 16 Engine Posters v2 — Art Deco 3D Artifact Style
Based on existing 9A poster series (Vimshottari, Human Design, Tarot)
Uses Amir Mushich structured prompt format with Nano Banana 2 editing
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from brandmint.core.providers.fal_provider import FalProvider

# Paths
OUTPUT_DIR = Path("/Volumes/madara/2026/twc-vault/01-Projects/tryambakam-noesis/brand-docs-final/launch-beta-branding/9A-posters-v2")
REFERENCE_DIR = Path("/Volumes/madara/2026/twc-vault/01-Projects/brandmint/references/images")

# Reference mapping
REFS = {
    "3d-neuro": "ref-tw-024-lloydcreates-nano-banana-pro-3d-neuro.jpg",
    "glass": "ref-tw-118-lloydcreates-nano-banana-pro-glass.jpg",
    "bi-color": "ref-tw-014-Kashberg_0-google-gemini-nano-banana-pro.jpg",
    "collage": "ref-style-collage-portraits.jpg",
    "chrome": "ref-alt-chrome-logos.jpg",
    "stickers": "ref-alt-3d-sticker-logos.jpg",
}

@dataclass
class Engine:
    code: str
    name: str
    title: str
    subtitle: str
    artifact: str
    refs: list

# 16 Engines data
ENGINES = [
    Engine("9A-01", "panchanga", "PANCHANGA", 
           "The five limbs of Vedic timekeeping",
           "celestial calendar mechanism with five concentric rotating rings representing tithi, vara, nakshatra, yoga, karana. Lunar phase indicators. Sanskrit engravings",
           ["3d-neuro", "glass"]),
    
    Engine("9A-02", "vimshottari-dasha", "VIMSHOTTARI DASHA",
           "The compass of planetary time cycles", 
           "armillary sphere with nested bronze rings representing planetary orbits. Central sphere with 9 planetary markers. Gears at axis points",
           ["3d-neuro", "chrome"]),
    
    Engine("9A-03", "transits", "TRANSITS",
           "Tracking the moving sky",
           "orbital tracking astrolabe with rotating disk star map. Moving pointer arms. Epicyclic gears. Zodiac engravings. Glass lenses",
           ["3d-neuro", "glass"]),
    
    Engine("9A-04", "human-design", "HUMAN DESIGN",
           "The bodygraph as architectural blueprint",
           "circuit sculpture of 9 centers in geometric diamond formation. Channels as glowing filaments. Faceted gem nodes. Circuit board patterns",
           ["glass", "chrome"]),
    
    Engine("9A-05", "gene-keys", "GENE KEYS",
           "The spectrum of shadow to siddhi",
           "DNA double helix mechanism with 64 marker points. Color-coded rings for shadow/gift/siddhi. Base pairs as mechanical joints",
           ["3d-neuro", "chrome"]),
    
    Engine("9A-06", "biofield", "BIOFIELD",
           "The energy torus detector",
           "toroidal field detector showing donut-shaped energy visualization. Concentric torus layers. Biophoton indicators. HRV meter",
           ["glass", "3d-neuro"]),
    
    Engine("9A-07", "biorhythm", "BIORHYTHM",
           "Triple cycles of life",
           "three-wave chronometer with interlocking sine wave rings. Physical (copper), emotional (silver), intellectual (gold) waves",
           ["bi-color", "3d-neuro"]),
    
    Engine("9A-08", "vedic-clock", "VEDIC CLOCK",
           "The organ-meridian timepiece",
           "TCM organ clock with 12-sector dial. Organ symbols at each hour. Meridian lines. Rotating hands with organ icons",
           ["3d-neuro", "chrome"]),
    
    Engine("9A-09", "nadabrahman", "NADABRAHMAN",
           "Sound as divine vibration",
           "cymatic frequency resonator with concentric circular wave patterns. Central vibrating element. Harmonic overlay",
           ["glass", "3d-neuro"]),
    
    Engine("9A-10", "face-reading", "FACE READING",
           "The physiognomy lens",
           "facial mapping device with split-face mirror. Grid overlay. Zone indicators. Symmetry analysis lines",
           ["bi-color", "glass"]),
    
    Engine("9A-11", "tarot", "TAROT",
           "Symbolic mirrors for choice",
           "Art Deco frame holding three vertical cards in past-present-future arrangement. Card backs visible. Reflection mirror surface",
           ["collage", "glass"]),
    
    Engine("9A-12", "i-ching", "I CHING",
           "The binary oracle",
           "hexagram divination mechanism with six stacked horizontal bars. Binary pattern display. Changing line indicators. Trigram symbols",
           ["3d-neuro", "chrome"]),
    
    Engine("9A-13", "enneagram", "ENNEAGRAM",
           "The nine points of essence",
           "nine-pointed star structure with 9 nodal gems. Connecting lines showing paths. Integration arrows. Mathematical precision",
           ["chrome", "3d-neuro"]),
    
    Engine("9A-14", "numerology", "NUMEROLOGY",
           "The frequency of form",
           "vibrational number device with spiral number line in 3D. Number nodes. Life path indicator. Sacred geometry ratios",
           ["3d-neuro", "chrome"]),
    
    Engine("9A-15", "sacred-geometry", "SACRED GEOMETRY",
           "Divine proportion made visible",
           "Sri Yantra architectural model with 9 interlocking triangles. Upward and downward triangles. Bindu center. Golden ratio",
           ["chrome", "glass"]),
    
    Engine("9A-16", "sigil-forge", "SIGIL FORGE",
           "Where intent becomes form",
           "mechanical intent compression press with sigil die. Compressed symbol output. Retro-industrial. Worn, used appearance",
           ["stickers", "3d-neuro"]),
]

def get_ref_paths(refs: list) -> list:
    """Get full paths for references."""
    paths = []
    for r in refs:
        if r in REFS:
            p = REFERENCE_DIR / REFS[r]
            if p.exists():
                paths.append(str(p))
    return paths

def generate_poster(engine: Engine, provider: FalProvider) -> bool:
    """Generate single engine poster."""
    
    prompt = f"""{engine.title}. Act as a 3D product visualization artist and Art Deco industrial designer creating a museum-quality artifact.

THE SUBJECT & COMPOSITION:
A single, premium {engine.artifact} floats suspended in mid-air above a terrazzo pedestal, centered in frame. Angled 15-20 degrees to show depth and dimension. Realistic weight and material presence—not a stiff 3D model but a tangible, crafted artifact.

MATERIALITY & TEXTURE (CRITICAL):
- Primary: Aged copper and bronze with verdigris patina (green-blue oxidation)
- Accents: Polished gold/brass for engraved details and internal glow elements
- Surface: Mix of smooth polished areas and rough oxidized textures  
- Details: Art Deco geometric engravings, circuit-like patterns, sacred geometry motifs

ENVIRONMENT & BACKGROUND:
The artifact floats within a dramatic dark teal/navy photo studio (#1a2332). Deep gradient with subtle spotlight vignette. Art Deco gold frame borders the composition with geometric corner details.

PEDESTAL:
Rectangular terrazzo slab below the floating artifact. Realistic stone texture with embedded chips. Soft shadow cast by floating object.

LIGHTING & PHOTOGRAPHY:
Style: Hyper-realistic 3D render, museum catalog photography, Art Deco aesthetic
Lighting: Dramatic top-down spotlight with soft falloff. Internal warm gold glow from artifact's engraved lines. Subtle rim lighting defines edges.

COLOR PALETTE:
- Background: Deep navy/teal (#1a2332)
- Frame: Gold/bronze (#c9a227)  
- Artifact: Copper with verdigris (#8b4513, #5f9ea0)
- Glow: Warm gold (#ffd700)
- Typography: White (#ffffff)

TYPOGRAPHY AT BOTTOM:
Large bold white text: "{engine.title}"
Below in smaller weight: "{engine.subtitle}"
Footer in gold: "TRYAMBAKAM NOESIS — THE 16 ENGINES"

Resolution: 1792x2400px portrait format."""

    output_path = OUTPUT_DIR / f"{engine.code}-{engine.name}-poster-v2.png"
    
    # Skip if exists
    if output_path.exists():
        print(f"  ⏭️  {engine.code} already exists")
        return True
    
    ref_paths = get_ref_paths(engine.refs)
    
    print(f"  Generating {engine.code}: {engine.title}...")
    print(f"    References: {', '.join(engine.refs)}")
    
    try:
        result = provider.generate(
            prompt=prompt,
            model="google/gemini-3-1-flash-image-preview",
            output_path=str(output_path),
            width=1792,
            height=2400,
            images=ref_paths,
            seed=42
        )
        
        if result.success:
            print(f"    ✅ Saved: {output_path.name}")
            return True
        else:
            print(f"    ❌ Failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

def main():
    """Generate all 16 engine posters."""
    
    provider = FalProvider()
    
    print("=" * 70)
    print("16 ENGINE POSTERS v2 — Art Deco 3D Artifact Style")
    print("=" * 70)
    print()
    
    # Check provider
    if not provider.is_available():
        print("❌ FAL provider not available. Check FAL_KEY.")
        sys.exit(1)
    
    # Create output dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output: {OUTPUT_DIR}")
    print()
    
    # Generate all
    success = 0
    failed = 0
    
    for i, engine in enumerate(ENGINES, 1):
        print(f"[{i:2d}/16] {engine.title}")
        if generate_poster(engine, provider):
            success += 1
        else:
            failed += 1
        print()
    
    # Summary
    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {success + failed}")
    print()
    print(f"📦 Output size: {sum(f.stat().st_size for f in OUTPUT_DIR.glob('*.png')) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    main()
