"""
Instruction templates — brand-themed prompts for NotebookLM artifact generation.

Each function returns a string that is passed to ``notebooklm generate <type>``
as the instruction argument. Templates inject brand-specific data (colours,
typography, voice, positioning) so NotebookLM generates artifacts that reflect
the brand's identity.
"""
from __future__ import annotations

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(config: dict, *keys: str, default: str = "") -> str:
    """Safely traverse nested config keys."""
    current: Any = config
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, {})
        else:
            return default
    return str(current) if current and current != {} else default


def _palette_block(config: dict) -> str:
    """Render colour palette as instruction-friendly text."""
    palette = config.get("palette", {})
    lines = []
    for role in ("primary", "secondary", "accent", "support", "signal"):
        entry = palette.get(role, {})
        if isinstance(entry, dict) and entry.get("hex"):
            name = entry.get("name", role.title())
            lines.append(f"  - {role.title()}: {name} ({entry['hex']})")
    return "\n".join(lines) if lines else "  (no palette defined)"


def _typography_block(config: dict) -> str:
    """Render typography as instruction-friendly text."""
    typo = config.get("typography", {})
    lines = []
    for role in ("header", "body", "data"):
        entry = typo.get(role, {})
        if isinstance(entry, dict) and entry.get("font"):
            lines.append(f"  - {role.title()}: {entry['font']}")
    return "\n".join(lines) if lines else "  (no typography defined)"


def _voice_excerpt(config: dict) -> str:
    """Extract a short voice/tone description."""
    brand = config.get("brand", {})
    voice = brand.get("voice", "")
    tone = brand.get("tone", "")
    if voice and tone:
        return f"{voice}, {tone}"
    return voice or tone or "authentic and engaging"


# ---------------------------------------------------------------------------
# Brand Overview Deck
# ---------------------------------------------------------------------------

def brand_overview_deck(config: dict) -> str:
    """Generate instructions for a comprehensive brand overview slide deck."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    archetype = _get(config, "brand", "archetype")
    hero = _get(config, "positioning", "hero_headline")
    statement = _get(config, "positioning", "statement")

    return f"""Create a comprehensive Brand Overview slide deck for {brand_name}.

BRAND IDENTITY:
- Brand: {brand_name}
- Tagline: {tagline}
- Archetype: {archetype}
- Voice: {_voice_excerpt(config)}

VISUAL IDENTITY (reference these in slide design recommendations):
Colour Palette:
{_palette_block(config)}
Typography:
{_typography_block(config)}

POSITIONING:
- Hero Headline: {hero}
- Statement: {statement}

SLIDE STRUCTURE (10 slides):
1. Title — Brand name, tagline, one-line positioning
2. The Problem — Market gap and pain points from buyer persona
3. The Solution — Product/service value proposition
4. Target Audience — Primary persona profile and motivations
5. Product Details — Key features, differentiators, pricing logic
6. Market Opportunity — TAM context and competitive positioning
7. Business Model — Revenue mechanics and growth strategy
8. Traction & Roadmap — Milestones achieved and next phases
9. Brand Identity — Visual system, voice, and tone summary
10. Call to Action — Next steps and contact

TONE: Use the brand's {_voice_excerpt(config)} voice throughout.
Write with conviction and specificity. Avoid generic business jargon.
Reference specific data, quotes, and findings from the source materials."""


# ---------------------------------------------------------------------------
# Product Showcase Deck
# ---------------------------------------------------------------------------

def product_showcase_deck(config: dict) -> str:
    """Generate instructions for a product/service showcase slide deck."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")

    # Try to get product info
    products = config.get("products", {})
    hero_product = ""
    if isinstance(products, dict):
        hero = products.get("hero", "")
        if isinstance(hero, dict):
            hero_product = hero.get("name", "")
        elif isinstance(hero, str):
            hero_product = hero

    return f"""Create a Product/Service Showcase slide deck for {brand_name}.

BRAND: {brand_name} — {tagline}
HERO PRODUCT: {hero_product}

VISUAL IDENTITY:
Colour Palette:
{_palette_block(config)}
Typography:
{_typography_block(config)}

SLIDE STRUCTURE (8-10 slides):
1. Product Hero — Hero product name and one-line value claim
2. The Problem It Solves — Customer pain points and current alternatives
3. Product Overview — What it is, how it works, key features
4. Feature Deep-Dive — 3-4 standout features with benefits
5. Use Cases — Real scenarios showing the product in context
6. Differentiation — What makes this different from competitors
7. Pricing & Value — Pricing logic, value justification
8. Social Proof — Testimonials, traction metrics, press mentions
9. Product Lineup — Additional products or upcoming releases
10. Get Started — CTA, availability, next steps

Focus on the PRODUCT, not the company. Lead with features and benefits.
Use specific details, measurements, and material descriptions from the sources.
Voice: {_voice_excerpt(config)}"""


# ---------------------------------------------------------------------------
# Audio Overview
# ---------------------------------------------------------------------------

def audio_overview(config: dict) -> str:
    """Generate instructions for a brand audio overview (podcast)."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")

    return f"""Create a deep-dive audio overview of {brand_name}.

BRAND: {brand_name} — {tagline}

PODCAST STRUCTURE:
- Open with the brand's origin story and why it exists
- Explain the market problem and who the target customer is
- Walk through the product/service and what makes it unique
- Cover the brand's visual identity and design philosophy
- Discuss the competitive landscape and positioning strategy
- Share the content and marketing strategy
- Close with the brand's vision and next steps

VOICE AND PERSONALITY:
Use a {_voice_excerpt(config)} tone throughout. The podcast should feel
like a conversation with someone who deeply understands {brand_name} —
knowledgeable but approachable, passionate but not salesy.

Colour references for descriptive language:
{_palette_block(config)}

Reference specific data points, persona insights, and competitive
findings from the source materials. Name actual features, products,
and strategies rather than speaking in generalities.

Make this feel like an exclusive insider briefing on {brand_name}'s
brand DNA — not a generic company overview."""


# ---------------------------------------------------------------------------
# Brand Report
# ---------------------------------------------------------------------------

def brand_report(config: dict) -> str:
    """Generate instructions for a comprehensive brand report."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a comprehensive Brand Intelligence Report for {brand_name}.

FORMAT: Structured briefing document with clear sections and data.

SECTIONS:
1. Executive Summary — One-page overview of the brand
2. Market Analysis — Niche validation, market opportunity, competitive landscape
3. Target Audience — Persona profile, motivations, pain points, buying behaviour
4. Brand Strategy — Positioning statement, identity pillars, competitive moat
5. Product Overview — Features, benefits, pricing, differentiation
6. Visual Identity — Colour system, typography, design principles, materials
7. Voice & Tone — Brand personality, communication style, cultural references
8. Content Strategy — Social media plan, content calendar, channel strategy
9. Campaign Assets — Email sequences, ad copy, video scripts
10. Recommendations — Strategic next steps and priority actions

STYLE: Professional, data-driven, actionable. Use bullet points for
scanability. Include specific numbers, quotes, and findings from the sources.
Voice: {_voice_excerpt(config)}"""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ARTIFACT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "mind-map",
        "type": "mind-map",
        "instructions_fn": None,  # No instructions for mind map
        "output_filename": "brand-mind-map.json",
        "download_type": "mind-map",
        "estimated_minutes": 1,
        "phase": "instant",
    },
    {
        "id": "brand-overview-deck",
        "type": "slide-deck",
        "instructions_fn": brand_overview_deck,
        "output_filename": "brand-overview-deck.pdf",
        "download_type": "slide-deck",
        "estimated_minutes": 15,
        "phase": "parallel",
    },
    {
        "id": "product-showcase-deck",
        "type": "slide-deck",
        "instructions_fn": product_showcase_deck,
        "output_filename": "product-showcase-deck.pdf",
        "download_type": "slide-deck",
        "estimated_minutes": 15,
        "phase": "parallel",
    },
    {
        "id": "brand-report",
        "type": "report",
        "instructions_fn": brand_report,
        "output_filename": "brand-report.md",
        "download_type": "report",
        "estimated_minutes": 15,
        "phase": "parallel",
    },
    {
        "id": "audio-overview",
        "type": "audio",
        "instructions_fn": audio_overview,
        "output_filename": "brand-audio-overview.mp3",
        "download_type": "audio",
        "estimated_minutes": 20,
        "phase": "sequential",
    },
]
