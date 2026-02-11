# Campaign Orchestrator — Prompt Recipes

Use these ready-made and combo prompts to drive the full 6-part crowdfunding workflow, phase by phase, with strict validation gates and clean handoffs. Replace placeholders like `[PRODUCT_NAME]`, `[PRICE]`, `[ALLOWED_SKILLS]` with your values.

## Quick Start
- Run end-to-end with gates
  - "Run the full 6-part workflow for [PRODUCT_NAME] at [PRICE] using campaign-orchestrator. Enable skills: [ALLOWED_SKILLS]. Enforce validation gates at each phase and write outputs to each skill’s `templates/*.md`. Produce the phase status index in `campaign-orchestrator/templates/orchestrator.md`."

## Part 1: Understanding the Market
- Persona + Competitor (strict)
  - "Execute Part 1 for [PRODUCT_NAME]. Ensure the persona dossier includes ≥20 Wants and ≥20 Anti-Goals and provides casual soundbites. For competitor intelligence, include direct quotes from 1-star reviews and an FAQ anxiety matrix. Save to `Buyer Persona/templates/persona-dossier.md` and `competitor-analysis/templates/competitor-intelligence.md`."
- Re-run with constraints
  - "Re-run persona to add missing `emotional_drivers[]` and expand `voice_samples[]`. Re-run competitor to add at least three 1-star quotes, then regenerate the market gaps."

## Part 2: Product Detailing
- Product description + Positioning + MDS + Voice
  - "Generate detailed product description, positioning summary (CBBE), MDS, and the Golden Voice Prompt for [PRODUCT_NAME]. Save into:
    - `detailed-product-description/templates/detailed-product-description.md`
    - `product-positioning-summary/templates/product-positioning-summary.md`
    - `mds-messaging-direction-summary/templates/mds.md`
    - `voice-and-tone/templates/voice-and-tone.md`
    Enforce JSON keys: `product{ name, price }`, `specs{ dimensions, materials }`, `cbbe{ ... }`, `handoff{ pitch, usp, objections, emotions }`, `voice{ tones[], persona, culture, lingo, emotions[] }`."
- Tighten value logic
  - "Update Positioning Summary to refine points of difference and value logic. Keep CBBE structure intact and revalidate objections vs. credibility proof."

## Part 3: Crafting Compelling Copy
- Campaign page copy
  - "Create conversion-optimized campaign page copy using persona, MDS, positioning, and voice. Follow sections: Above-the-fold, Old World, New World, Social Proof, Risk Reversal, Final Offer. Render into `campaign-page-copy/templates/campaign-page-copy.md` and include `meta{ product, brand }`."
- Pre-launch ads dossier
  - "Generate the pre-launch ad campaign dossier with 18 headlines and 21 body variants (per defined families). Save to `pre-launch-ads/templates/ad-campaign-dossier.md`. Include rationale for the Big Idea."

## Part 4: Robust Email Strategy
- Welcome + Pre-launch + Launch
  - "Compose welcome, pre-launch, and launch email sequences using the Voice Prompt and MDS pitch. Save into:
    - `welcome-email-sequence/templates/welcome-email-sequence.md` (include `meta` and `links`)
    - `pre-launch-email-sequence/templates/pre-launch-email-sequence.md` (include `schedule`, `segments`, `links`)
    - `launch-email-sequence/templates/launch-email-sequence.md` (include `schedule` and `vars`)"
- Scheduling pass
  - "Validate and adjust all email schedules and CTAs to align with [LAUNCH_DATE_TIME] and VIP window logic. Re-render JSON schedules in each template."

## Part 5: Campaign Messaging
- Page + Video
  - "Finalize campaign page copy and draft the video script with Hook, Problem, Mechanism, Proof, Offer, CTA. Save to:
    - `campaign-page-copy/templates/campaign-page-copy.md`
    - `campaign-video-script/templates/campaign-video-script.md` (ensure `timing.total_seconds` and `cta`)"
- Proof tightening
  - "Strengthen social proof: add credible quotes, media mentions, and a user count placeholder. Keep risk reversal FAQs specific and exhaustive."

## Part 6: Continual Interest
- Live ads + PR
  - "Create live campaign ads variants (Discount, Live Now, Social Proof, Testimonial/PR, Ending Urgency) with dynamic tokens. Save to `live-campaign-ads/templates/live-campaign-ads.md` and include `tokens{ funding_percent, backers, end_date, hours_left }`."
  - "Draft the press release with headline, dateline, quotes, specs, pricing, availability, and media contact. Save to `press-release-copy/templates/press-release-copy.md`."

## Combo Prompts
- Parts 1→2 consolidation
  - "Run Parts 1 and 2 in sequence for [PRODUCT_NAME]. After persona and competitor outputs finalize, generate product description, positioning, MDS, and voice. Enforce all required JSON keys for each output."
- Voice-driven copy sprint
  - "Using `voice-and-tone` and `mds` handoffs, produce the Campaign Page Copy and Pre-Launch Ads. Stop if MDS `handoff.usp` or `pitch` is missing and request a re-run of MDS with tighter constraints."
- Email sprint from positioning
  - "From Positioning Summary and MDS, generate all three email sequences. Ensure each template contains complete JSON scheduling and segment fields."
- Resume from Part 3
  - "Resume orchestration from Part 3 using all previously saved outputs. Validate gates for MDS (`handoff.usp`), Positioning (`cbbe`), and Voice (`voice.tones`). Continue through Part 6 and produce the status report."

## Reporting & Validation
- Orchestrator status index
  - "Generate the phase-by-phase status report and outputs index into `campaign-orchestrator/templates/orchestrator.md`. Include paths for persona, competitor, product description, positioning, MDS, voice, campaign page, pre-launch ads, email sequences, video, live ads, and PR."
- Gate check only
  - "Run gate validation against all phases without regenerating content. List any missing JSON keys and indicate which upstream skills must be re-run."

## Inputs & Allowed Skills
- Minimal inputs
  - "[PRODUCT_INPUTS]: Name, price, overview"
- Allowed skills example
  - "[ALLOWED_SKILLS]: buyer-persona-generator, competitor-analysis, detailed-product-description, product-positioning-summary, mds-messaging-direction-summary, voice-and-tone, pre-launch-ads, welcome-email-sequence, pre-launch-email-sequence, launch-email-sequence, campaign-page-copy, campaign-video-script, live-campaign-ads, press-release-copy"

