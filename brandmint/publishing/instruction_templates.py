"""
Instruction templates — brand-themed prompts for NotebookLM artifact generation.

Each function returns a string that is passed to ``notebooklm generate <type>``
as the instruction argument. Templates inject brand-specific data (colours,
typography, voice, positioning) so NotebookLM generates artifacts that reflect
the brand's identity.

Supports all 9 NotebookLM artifact types with multiple variations per type,
producing ~25 artifacts per project with the full customization matrix.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


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


def _brand_context_block(config: dict) -> str:
    """Build a compact brand context block reusable across instruction fns."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    archetype = _get(config, "brand", "archetype")
    return (
        f"BRAND: {brand_name} — {tagline}\n"
        f"ARCHETYPE: {archetype}\n"
        f"VOICE: {_voice_excerpt(config)}"
    )


# ---------------------------------------------------------------------------
# Video style auto-resolution
# ---------------------------------------------------------------------------

VIDEO_STYLE_MAP: Dict[str, str] = {
    "creator": "whiteboard",
    "sage": "classic",
    "explorer": "watercolor",
    "ruler": "heritage",
    "magician": "anime",
    "innocent": "kawaii",
    "hero": "classic",
    "outlaw": "retro-print",
    "jester": "kawaii",
    "caregiver": "paper-craft",
    "everyman": "classic",
    "lover": "watercolor",
}


def resolve_video_style(config: dict) -> str:
    """Determine NotebookLM video style from brand archetype/theme.

    Checks brand archetype first, then theme aesthetic keywords.
    Returns one of the valid ``--style`` values for ``notebooklm generate video``.
    """
    archetype = _get(config, "brand", "archetype").lower()
    theme_style = _get(config, "theme", "aesthetic").lower()

    # Check archetype keywords
    for key, style in VIDEO_STYLE_MAP.items():
        if key in archetype:
            return style

    # Check theme aesthetic keywords
    if any(kw in theme_style for kw in ("heritage", "traditional")):
        return "heritage"
    if any(kw in theme_style for kw in ("minimal", "modern", "clean")):
        return "classic"
    if any(kw in theme_style for kw in ("organic", "natural")):
        return "watercolor"
    if any(kw in theme_style for kw in ("retro", "vintage", "terminal", "futuristic")):
        return "retro-print"
    if any(kw in theme_style for kw in ("craft", "handmade", "artisan")):
        return "paper-craft"

    return "auto"


# ---------------------------------------------------------------------------
# Slide Deck instructions
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


def product_showcase_deck(config: dict) -> str:
    """Generate instructions for a product/service showcase slide deck."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")

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
# Video instructions
# ---------------------------------------------------------------------------

def video_explainer(config: dict) -> str:
    """Instructions for a full-length brand explainer video."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    statement = _get(config, "positioning", "statement")

    return f"""Create a comprehensive brand explainer video for {brand_name}.

{_brand_context_block(config)}

VIDEO STRUCTURE:
- Hook: Open with the core problem {brand_name} solves
- Origin: Tell the brand's story — why it exists and who built it
- Solution: Walk through the product/service and its key differentiators
- Audience: Describe the ideal customer persona and their world
- Visual identity: Reference the brand's design system and aesthetic
- Competitive edge: Explain how {brand_name} is positioned differently
- Strategy: Touch on the marketing and content approach
- Vision: Close with where {brand_name} is headed next

POSITIONING: {statement}

VISUAL IDENTITY:
Colour Palette:
{_palette_block(config)}
Typography:
{_typography_block(config)}

Use the brand's {_voice_excerpt(config)} voice. Make it feel like a
documentary-style deep dive — authoritative but engaging. Reference specific
data, personas, and competitive insights from the source materials.
This should feel like an exclusive behind-the-scenes look at {brand_name}."""


def video_brief(config: dict) -> str:
    """Instructions for a short social-ready brand introduction video."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    hero = _get(config, "positioning", "hero_headline")

    return f"""Create a short, punchy brand introduction video for {brand_name}.

{_brand_context_block(config)}

HERO HEADLINE: {hero}

Keep it under 3 minutes. This is a social-media-ready introduction:
- Hook in first 10 seconds: state the problem or bold claim
- Brand name + tagline reveal
- 3 key differentiators (rapid fire)
- Visual identity showcase (reference brand colours and typography)
- Strong CTA to close

Colour Palette:
{_palette_block(config)}

Make it fast-paced, visually dynamic, and memorable. Use the brand's
{_voice_excerpt(config)} voice but cranked up for social media impact.
Think trailer energy, not corporate presentation."""


# ---------------------------------------------------------------------------
# Audio instructions
# ---------------------------------------------------------------------------

def audio_deep_dive(config: dict) -> str:
    """Instructions for a deep-dive audio overview (long podcast)."""
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


def audio_brief(config: dict) -> str:
    """Instructions for a short audio brand primer."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    hero = _get(config, "positioning", "hero_headline")

    return f"""Create a concise audio introduction to {brand_name}.

BRAND: {brand_name} — {tagline}
HEADLINE: {hero}

Keep it tight and punchy — this is a quick brand primer:
- What {brand_name} is in one sentence
- The problem it solves
- Who it's for (persona snapshot)
- What makes it different (2-3 key differentiators)
- Where to learn more

Voice: {_voice_excerpt(config)} — energetic but informative.
Think elevator pitch meets podcast intro. No filler, all signal.
Reference specific details from the sources, not generalities."""


def audio_debate(config: dict) -> str:
    """Instructions for a two-host debate format audio."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    statement = _get(config, "positioning", "statement")

    return f"""Create a debate-style discussion about {brand_name}'s brand strategy.

BRAND: {brand_name} — {tagline}
POSITIONING: {statement}

DEBATE FORMAT:
Two hosts examine {brand_name}'s strategy from different angles:
- Host 1 argues FOR the brand's positioning choices and strategy
- Host 2 plays devil's advocate, raising challenges and risks
- Both cite specific data from the source materials

TOPICS TO DEBATE:
1. Is the market positioning defensible long-term?
2. Does the target persona match the product offering?
3. Are the competitive advantages real or perceived?
4. Will the content and marketing strategy reach the right audience?
5. Is the visual identity aligned with the brand archetype?

Keep it spirited but informed. Both hosts should reference actual
competitive analysis, persona data, and positioning strategy from the
sources. End with a shared summary of strengths and watch-outs.
Voice: {_voice_excerpt(config)}"""


# Backward-compatible alias
audio_overview = audio_deep_dive


# ---------------------------------------------------------------------------
# Report instructions
# ---------------------------------------------------------------------------

def brand_report(config: dict) -> str:
    """Generate instructions for a comprehensive brand report (briefing doc)."""
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


def report_blog_post(config: dict) -> str:
    """Instructions for a blog-post-style brand story."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    archetype = _get(config, "brand", "archetype")

    return f"""Write a compelling brand story blog post about {brand_name}.

{_brand_context_block(config)}

BLOG STRUCTURE:
- Opening hook — a vivid scene or bold statement that captures the brand's essence
- The problem landscape — what's broken in the market and why it matters
- The {brand_name} origin — how and why the brand was born
- The solution in action — what the product/service does differently
- The people it serves — bring the target persona to life with a narrative
- The design philosophy — visual identity and why it looks the way it does
- The road ahead — vision and upcoming milestones
- CTA — invite the reader into the brand's world

TONE: Write in the brand's {_voice_excerpt(config)} voice.
This is NOT a press release. It's a story. Use narrative techniques:
specific details, sensory language, and human moments.
Reference real data from the sources but weave it into the narrative.
The {archetype} archetype should infuse the storytelling style."""


def report_study_guide(config: dict) -> str:
    """Instructions for a brand team onboarding study guide."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a Brand Study Guide for onboarding new team members at {brand_name}.

{_brand_context_block(config)}

STUDY GUIDE STRUCTURE:
1. Brand at a Glance — One-page cheat sheet (name, tagline, archetype, voice)
2. Our Market — Industry context, target market, competitive landscape
3. Our Customer — Persona deep-dive with motivations and pain points
4. Our Strategy — Positioning, messaging pillars, competitive moat
5. Our Product — Features, benefits, pricing, key differentiators
6. Our Visual Identity — Colour system, typography, design principles
7. Our Voice — How we speak, write, and communicate
8. Our Campaigns — Active marketing initiatives and content strategy
9. Key Terms Glossary — Brand-specific terminology and definitions
10. Self-Assessment — Review questions to test understanding

FORMAT: Educational, clear, structured for learning. Use headers,
bullet points, and "Key Takeaway" callouts after each section.
Include actual data from the sources — this should teach someone
everything they need to know about {brand_name} in one sitting."""


# ---------------------------------------------------------------------------
# Quiz instructions
# ---------------------------------------------------------------------------

def quiz_brand_knowledge(config: dict) -> str:
    """Instructions for a standard brand knowledge quiz."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a brand knowledge quiz about {brand_name}.

{_brand_context_block(config)}

Focus on core brand fundamentals:
- Brand identity (name, tagline, archetype, voice)
- Target audience (persona details, motivations, demographics)
- Product/service overview (features, pricing, differentiators)
- Visual identity (colours, typography, design principles)
- Positioning strategy (statement, competitive advantages)

Mix question types: multiple choice, true/false, and fill-in-the-blank.
Questions should reference specific facts from the source materials.
Good for onboarding and team alignment checks."""


def quiz_deep_dive(config: dict) -> str:
    """Instructions for an advanced brand strategy quiz."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create an advanced brand strategy quiz about {brand_name}.

{_brand_context_block(config)}

Focus on strategic depth:
- Competitive positioning (specific competitors, differentiation points)
- Marketing strategy (channel choices, content pillars, campaign mechanics)
- Customer journey (touchpoints, conversion strategy, retention)
- Brand architecture (messaging hierarchy, voice guidelines, visual system)
- Financial/growth strategy (pricing logic, market sizing, business model)

Questions should require understanding of relationships between concepts,
not just recall. Include scenario-based questions ("If a competitor does X,
how should {brand_name} respond based on its positioning?").
Reference specific data and analysis from the sources."""


# ---------------------------------------------------------------------------
# Flashcards instructions
# ---------------------------------------------------------------------------

def flashcards_brand(config: dict) -> str:
    """Instructions for standard brand terminology flashcards."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create brand knowledge flashcards for {brand_name}.

{_brand_context_block(config)}

FLASHCARD CATEGORIES:
- Brand Identity: name, tagline, archetype, personality traits
- Visual System: colour names and hex codes, font names, design principles
- Voice & Tone: communication style, do's and don'ts, tone descriptors
- Target Audience: persona name, demographics, motivations, pain points
- Product: features, benefits, pricing tiers, key differentiators
- Positioning: statement, competitive advantages, market category

Front of card: term, concept, or question
Back of card: definition, answer, or key details with specific data

These should help someone quickly memorize {brand_name}'s core brand
elements. Use specific data from the sources — not generic definitions."""


def flashcards_detailed(config: dict) -> str:
    """Instructions for deep-cut brand data flashcards."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create detailed brand intelligence flashcards for {brand_name}.

{_brand_context_block(config)}

FLASHCARD CATEGORIES (advanced):
- Competitive Intelligence: competitor names, strengths, weaknesses
- Campaign Mechanics: email sequence details, social content pillars
- Content Strategy: channel-specific approaches, posting frameworks
- Customer Psychology: buyer motivations, objection handling, triggers
- Market Data: market size, growth trends, industry dynamics
- Product Specs: technical details, material descriptions, specifications

Front: specific question or scenario
Back: detailed answer with data points from the sources

These are deep-cut flashcards for team members who already know the
basics and need to internalize the strategic details. Include specific
numbers, competitor names, and tactical recommendations from the sources."""


# ---------------------------------------------------------------------------
# Infographic instructions
# ---------------------------------------------------------------------------

def infographic_overview(config: dict) -> str:
    """Instructions for a landscape brand overview infographic."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a comprehensive brand overview infographic for {brand_name}.

{_brand_context_block(config)}

VISUAL IDENTITY:
Colour Palette:
{_palette_block(config)}
Typography:
{_typography_block(config)}

INFOGRAPHIC SECTIONS:
1. Brand Hero — Name, tagline, and archetype visual
2. By the Numbers — Key statistics (market size, audience reach, growth)
3. Target Customer — Persona snapshot with demographics and motivations
4. Product/Service Map — Features and benefits visual breakdown
5. Competitive Position — Where {brand_name} sits in the market
6. Brand Identity System — Colour palette, typography, design principles
7. Content Strategy — Channel overview and content mix

Include specific data points and numbers from the source materials.
Use the brand's colour palette for the design recommendations.
This should work as a one-page brand summary for stakeholders."""


def infographic_product(config: dict) -> str:
    """Instructions for a portrait product showcase infographic."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a product showcase infographic for {brand_name}.

{_brand_context_block(config)}

VISUAL IDENTITY:
Colour Palette:
{_palette_block(config)}

FOCUS: Product features, benefits, and differentiation.

SECTIONS:
1. Product Hero — Name and one-line value proposition
2. Key Features — Visual breakdown of top 4-6 features
3. How It Works — Step-by-step or process flow
4. Benefits — Outcomes and value for the customer
5. vs. Alternatives — Side-by-side comparison points
6. Pricing — Tier overview or value proposition
7. CTA — Next step for the audience

Use specific product details, measurements, and specifications
from the source materials. Portrait orientation for mobile and
print-friendly layout. Reference brand colours and typography."""


def infographic_social(config: dict) -> str:
    """Instructions for a square social-media-ready brand card."""
    brand_name = _get(config, "brand", "name", default="the brand")
    tagline = _get(config, "brand", "tagline")
    hero = _get(config, "positioning", "hero_headline")

    return f"""Create a social-media-ready brand card infographic for {brand_name}.

BRAND: {brand_name} — {tagline}
HEADLINE: {hero}

Colour Palette:
{_palette_block(config)}

DESIGN: Square format optimized for social sharing (Instagram, LinkedIn).

CONTENT (concise — this is a quick-hit visual):
- Brand name and tagline prominent
- 3 key stats or differentiators
- Target customer in one line
- Visual identity colours and style reference
- CTA or website URL

Keep text minimal. Every element should be scannable in under 5 seconds.
High visual impact using the brand's colour palette.
This is the brand's social media calling card."""


# ---------------------------------------------------------------------------
# Data Table instructions
# ---------------------------------------------------------------------------

def table_competitive_analysis(config: dict) -> str:
    """Instructions for a competitive analysis comparison table."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a competitive analysis comparison table for {brand_name}.

{_brand_context_block(config)}

TABLE STRUCTURE:
- Rows: {brand_name} and its top 3-5 competitors
- Columns: Key comparison dimensions from the competitive analysis
  (e.g., pricing, target market, key features, market position,
   strengths, weaknesses, unique differentiators)

Include specific competitor names, pricing data, feature comparisons,
and market positioning from the source materials. Highlight where
{brand_name} has clear advantages. This should be a quick-reference
decision support tool for stakeholders."""


def table_product_features(config: dict) -> str:
    """Instructions for a product features vs benefits table."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a product features vs. benefits table for {brand_name}.

{_brand_context_block(config)}

TABLE STRUCTURE:
- Rows: Each product feature or capability
- Columns: Feature Name, Description, Customer Benefit, Differentiator
  (whether this feature is unique vs. competitors)

Pull specific feature names, technical details, and benefit
statements from the source materials. Include pricing-related
features if available. This should map every feature to a
concrete customer outcome."""


def table_persona_matrix(config: dict) -> str:
    """Instructions for a customer persona attributes matrix."""
    brand_name = _get(config, "brand", "name", default="the brand")

    return f"""Create a customer persona matrix for {brand_name}.

{_brand_context_block(config)}

TABLE STRUCTURE:
- Rows: Persona attributes (demographics, psychographics, behaviours)
- Columns: Attribute Category, Details, Marketing Implications, Content Approach

ATTRIBUTES TO INCLUDE:
- Age range, income level, education, location
- Motivations, frustrations, goals, fears
- Buying behaviour, decision process, triggers
- Media consumption, social platforms, content preferences
- Pain points and how {brand_name} addresses each

Use specific persona data from the source materials including
actual quotes, demographic details, and psychographic profiles.
This should be the go-to reference for anyone creating content
or campaigns targeting {brand_name}'s audience."""


# ---------------------------------------------------------------------------
# Extension & file extension helpers
# ---------------------------------------------------------------------------

_TYPE_EXT: Dict[str, str] = {
    "mind-map": "json",
    "slide-deck": "pdf",
    "video": "mp4",
    "audio": "mp3",
    "report": "md",
    "quiz": "json",
    "flashcards": "json",
    "infographic": "png",
    "data-table": "json",
}

_TYPE_MINUTES: Dict[str, int] = {
    "mind-map": 1,
    "slide-deck": 15,
    "video": 20,
    "audio": 20,
    "report": 15,
    "quiz": 5,
    "flashcards": 5,
    "infographic": 10,
    "data-table": 5,
}

_TYPE_PHASE: Dict[str, str] = {
    "mind-map": "instant",
    "slide-deck": "parallel-1",
    "video": "slow",
    "audio": "slow",
    "report": "parallel-1",
    "quiz": "parallel-2",
    "flashcards": "parallel-2",
    "infographic": "parallel-2",
    "data-table": "parallel-2",
}


def ext_for_type(artifact_type: str) -> str:
    """Return file extension for an artifact type."""
    return _TYPE_EXT.get(artifact_type, "json")


def estimate_for_type(artifact_type: str) -> int:
    """Return estimated generation minutes for an artifact type."""
    return _TYPE_MINUTES.get(artifact_type, 10)


def phase_for_type(artifact_type: str) -> str:
    """Return execution phase for an artifact type."""
    return _TYPE_PHASE.get(artifact_type, "parallel-2")


# ---------------------------------------------------------------------------
# Backward compatibility — legacy ID mapping
# ---------------------------------------------------------------------------

LEGACY_ID_MAP: Dict[str, str] = {
    "brand-overview-deck": "deck-detailed-full",
    "product-showcase-deck": "deck-detailed-short",
    "brand-report": "report-briefing",
    "audio-overview": "audio-deep-dive-long",
}


# ---------------------------------------------------------------------------
# Full artifact definitions — 25 artifacts across 9 types
# ---------------------------------------------------------------------------

DEFAULT_ARTIFACT_DEFINITIONS: List[Dict[str, Any]] = [
    # ── Mind Map (1) ──────────────────────────────────────────
    {
        "id": "mind-map",
        "type": "mind-map",
        "instructions_fn": None,
        "output_filename": "mind-map.json",
        "download_type": "mind-map",
        "estimated_minutes": 1,
        "phase": "instant",
        "extra_args": [],
        "group": "mind-map",
        "description": "Brand intelligence mind map",
    },
    # ── Slide Decks (4) ──────────────────────────────────────
    {
        "id": "deck-detailed-full",
        "type": "slide-deck",
        "instructions_fn": brand_overview_deck,
        "output_filename": "deck-detailed-full.pdf",
        "download_type": "slide-deck",
        "estimated_minutes": 15,
        "phase": "parallel-1",
        "extra_args": ["--format", "detailed"],
        "group": "slide-deck",
        "description": "Detailed brand overview deck (full length)",
    },
    {
        "id": "deck-detailed-short",
        "type": "slide-deck",
        "instructions_fn": product_showcase_deck,
        "output_filename": "deck-detailed-short.pdf",
        "download_type": "slide-deck",
        "estimated_minutes": 10,
        "phase": "parallel-1",
        "extra_args": ["--format", "detailed", "--length", "short"],
        "group": "slide-deck",
        "description": "Detailed product showcase deck (short)",
    },
    {
        "id": "deck-presenter-full",
        "type": "slide-deck",
        "instructions_fn": brand_overview_deck,
        "output_filename": "deck-presenter-full.pdf",
        "download_type": "slide-deck",
        "estimated_minutes": 15,
        "phase": "parallel-1",
        "extra_args": ["--format", "presenter"],
        "group": "slide-deck",
        "description": "Presenter slides — brand overview (full length)",
    },
    {
        "id": "deck-presenter-short",
        "type": "slide-deck",
        "instructions_fn": product_showcase_deck,
        "output_filename": "deck-presenter-short.pdf",
        "download_type": "slide-deck",
        "estimated_minutes": 10,
        "phase": "parallel-1",
        "extra_args": ["--format", "presenter", "--length", "short"],
        "group": "slide-deck",
        "description": "Presenter slides — product showcase (short)",
    },
    # ── Video (2) ─────────────────────────────────────────────
    {
        "id": "video-explainer",
        "type": "video",
        "instructions_fn": video_explainer,
        "output_filename": "video-explainer.mp4",
        "download_type": "video",
        "estimated_minutes": 20,
        "phase": "slow",
        "extra_args": ["--format", "explainer"],  # --style resolved at runtime
        "group": "video",
        "description": "Full brand explainer video (with brand-matched style)",
    },
    {
        "id": "video-brief",
        "type": "video",
        "instructions_fn": video_brief,
        "output_filename": "video-brief.mp4",
        "download_type": "video",
        "estimated_minutes": 15,
        "phase": "slow",
        "extra_args": ["--format", "brief"],  # --style resolved at runtime
        "group": "video",
        "description": "Short social-ready brand introduction video",
    },
    # ── Audio (3) ─────────────────────────────────────────────
    {
        "id": "audio-deep-dive-long",
        "type": "audio",
        "instructions_fn": audio_deep_dive,
        "output_filename": "audio-deep-dive-long.mp3",
        "download_type": "audio",
        "estimated_minutes": 20,
        "phase": "slow",
        "extra_args": ["--format", "deep-dive", "--length", "long"],
        "group": "audio",
        "description": "Deep-dive brand podcast (long format)",
    },
    {
        "id": "audio-brief-short",
        "type": "audio",
        "instructions_fn": audio_brief,
        "output_filename": "audio-brief-short.mp3",
        "download_type": "audio",
        "estimated_minutes": 10,
        "phase": "slow",
        "extra_args": ["--format", "brief", "--length", "short"],
        "group": "audio",
        "description": "Quick brand audio primer (short format)",
    },
    {
        "id": "audio-debate",
        "type": "audio",
        "instructions_fn": audio_debate,
        "output_filename": "audio-debate.mp3",
        "download_type": "audio",
        "estimated_minutes": 20,
        "phase": "slow",
        "extra_args": ["--format", "debate"],
        "group": "audio",
        "description": "Two-host debate on brand strategy",
    },
    # ── Reports (3) ───────────────────────────────────────────
    {
        "id": "report-briefing",
        "type": "report",
        "instructions_fn": brand_report,
        "output_filename": "report-briefing.md",
        "download_type": "report",
        "estimated_minutes": 15,
        "phase": "parallel-1",
        "extra_args": ["--format", "briefing-doc"],
        "group": "report",
        "description": "Brand intelligence briefing document",
    },
    {
        "id": "report-blog",
        "type": "report",
        "instructions_fn": report_blog_post,
        "output_filename": "report-blog.md",
        "download_type": "report",
        "estimated_minutes": 15,
        "phase": "parallel-1",
        "extra_args": ["--format", "blog-post"],
        "group": "report",
        "description": "Brand story blog post",
    },
    {
        "id": "report-study-guide",
        "type": "report",
        "instructions_fn": report_study_guide,
        "output_filename": "report-study-guide.md",
        "download_type": "report",
        "estimated_minutes": 15,
        "phase": "parallel-2",
        "extra_args": ["--format", "study-guide"],
        "group": "report",
        "description": "Brand onboarding study guide",
    },
    # ── Quiz (2) ──────────────────────────────────────────────
    {
        "id": "quiz-medium",
        "type": "quiz",
        "instructions_fn": quiz_brand_knowledge,
        "output_filename": "quiz-medium.json",
        "download_type": "quiz",
        "estimated_minutes": 5,
        "phase": "parallel-2",
        "extra_args": ["--difficulty", "medium", "--quantity", "standard"],
        "group": "quiz",
        "description": "Brand knowledge quiz (medium difficulty)",
    },
    {
        "id": "quiz-hard",
        "type": "quiz",
        "instructions_fn": quiz_deep_dive,
        "output_filename": "quiz-hard.json",
        "download_type": "quiz",
        "estimated_minutes": 5,
        "phase": "parallel-2",
        "extra_args": ["--difficulty", "hard", "--quantity", "more"],
        "group": "quiz",
        "description": "Advanced brand strategy quiz (hard difficulty)",
    },
    # ── Flashcards (2) ────────────────────────────────────────
    {
        "id": "flashcards-standard",
        "type": "flashcards",
        "instructions_fn": flashcards_brand,
        "output_filename": "flashcards-standard.json",
        "download_type": "flashcards",
        "estimated_minutes": 5,
        "phase": "parallel-2",
        "extra_args": ["--difficulty", "medium", "--quantity", "standard"],
        "group": "flashcards",
        "description": "Brand terminology flashcards (standard)",
    },
    {
        "id": "flashcards-detailed",
        "type": "flashcards",
        "instructions_fn": flashcards_detailed,
        "output_filename": "flashcards-detailed.json",
        "download_type": "flashcards",
        "estimated_minutes": 5,
        "phase": "parallel-2",
        "extra_args": ["--difficulty", "hard", "--quantity", "more"],
        "group": "flashcards",
        "description": "Deep-cut brand intelligence flashcards",
    },
    # ── Infographic (3) ───────────────────────────────────────
    {
        "id": "infographic-landscape",
        "type": "infographic",
        "instructions_fn": infographic_overview,
        "output_filename": "infographic-landscape.png",
        "download_type": "infographic",
        "estimated_minutes": 10,
        "phase": "parallel-2",
        "extra_args": ["--orientation", "landscape", "--detail", "detailed"],
        "group": "infographic",
        "description": "Brand overview infographic (landscape, detailed)",
    },
    {
        "id": "infographic-portrait",
        "type": "infographic",
        "instructions_fn": infographic_product,
        "output_filename": "infographic-portrait.png",
        "download_type": "infographic",
        "estimated_minutes": 10,
        "phase": "parallel-2",
        "extra_args": ["--orientation", "portrait", "--detail", "standard"],
        "group": "infographic",
        "description": "Product showcase infographic (portrait)",
    },
    {
        "id": "infographic-square",
        "type": "infographic",
        "instructions_fn": infographic_social,
        "output_filename": "infographic-square.png",
        "download_type": "infographic",
        "estimated_minutes": 10,
        "phase": "parallel-2",
        "extra_args": ["--orientation", "square", "--detail", "concise"],
        "group": "infographic",
        "description": "Social media brand card (square, concise)",
    },
    # ── Data Tables (3) ───────────────────────────────────────
    {
        "id": "table-competitive",
        "type": "data-table",
        "instructions_fn": table_competitive_analysis,
        "output_filename": "table-competitive.json",
        "download_type": "data-table",
        "estimated_minutes": 5,
        "phase": "parallel-2",
        "extra_args": [],
        "group": "data-table",
        "description": "Competitive analysis comparison table",
    },
    {
        "id": "table-product",
        "type": "data-table",
        "instructions_fn": table_product_features,
        "output_filename": "table-product.json",
        "download_type": "data-table",
        "estimated_minutes": 5,
        "phase": "parallel-2",
        "extra_args": [],
        "group": "data-table",
        "description": "Product features vs benefits table",
    },
    {
        "id": "table-persona",
        "type": "data-table",
        "instructions_fn": table_persona_matrix,
        "output_filename": "table-persona.json",
        "download_type": "data-table",
        "estimated_minutes": 5,
        "phase": "parallel-2",
        "extra_args": [],
        "group": "data-table",
        "description": "Customer persona attributes matrix",
    },
]

# Backward-compatible alias (old name → new list)
ARTIFACT_DEFINITIONS = DEFAULT_ARTIFACT_DEFINITIONS
