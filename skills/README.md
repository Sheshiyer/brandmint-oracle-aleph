# Brandmint Skills Registry

44 specialized brand skills across 9 categories. Each skill contains a `SKILL.md` defining its workflow, triggers, and templates.

## Categories

### `text-strategy/` (7 skills)
Strategic brand text generation — positioning, personas, voice, competitive intelligence.

| Skill | Purpose |
|-------|---------|
| `buyer-persona` | Deep-psychology buyer persona dossier (10-step protocol) |
| `product-positioning-summary` | CBBE framework positioning summary |
| `mds-messaging-direction-summary` | Messaging direction: pitch, features, benefits, differentiators |
| `voice-and-tone` | Brand voice persona and tone calibration |
| `competitor-analysis` | Market intelligence with search-based research |
| `detailed-product-description` | Feature-by-feature product description with specs |
| `brand-name-studio` | Phonesthetics-based brand name generation |

### `visual-prompters/` (9 skills)
AI image prompt generation for various asset types.

| Skill | Purpose |
|-------|---------|
| `brand-identity-prompter` | Logo variations, brand marks, identity system prompts |
| `brand-product-prompter` | Branded product concepts, packaging mockups |
| `product-photography-prompter` | Commercial product photography prompts |
| `fashion-editorial-prompter` | High-fashion editorial, apparel lookbook prompts |
| `illustration-style-prompter` | Non-photorealistic art: posters, icons, Notion-style |
| `logo-concept-architect` | Deep visual prompts for Midjourney/DALL-E logo vectors |
| `visual-identity-core` | Complete visual language: palette, typography, logo direction |
| `packaging-experience-designer` | Box structure, copy, surprise elements design |
| `design-tool-router` | Routes to correct AI design tool for task |

### `campaign-copy/` (6 skills)
Marketing copy and campaign content.

| Skill | Purpose |
|-------|---------|
| `campaign-page-copy` | Full Kickstarter/Indiegogo page content |
| `campaign-page-builder` | Maps copy + visuals + video into campaign page |
| `campaign-video-script` | High-conversion crowdfunding video script |
| `press-release-copy` | Professional launch press release |
| `campaign-orchestrator` | Full crowdfunding workflow phase-by-phase |
| `short-form-hook-generator` | 15-second viral TikTok/Reels/Shorts hooks |

### `email-sequences/` (3 skills)
Email marketing automation.

| Skill | Purpose |
|-------|---------|
| `welcome-email-sequence` | Two-part VIP welcome sequence |
| `pre-launch-email-sequence` | Pre-launch anticipation email cadence |
| `launch-email-sequence` | Launch week email cadence (day 1-3) |

### `brand-foundation/` (3 skills)
Core brand identity and naming.

| Skill | Purpose |
|-------|---------|
| `visual-identity-core` | Visual language definition (shared with visual-prompters) |
| `brand-name-studio` | Brand name generation (shared with text-strategy) |
| `logo-concept-architect` | Logo concept generation (shared with visual-prompters) |

### `social-growth/` (5 skills)
Social media and community growth.

| Skill | Purpose |
|-------|---------|
| `social-content-engine` | 30-day warm-up content calendar |
| `community-manager-brain` | Discord/Facebook engagement scripts |
| `influencer-outreach-pro` | Personalized DM scripts and email pitches |
| `review-response-strategist` | On-brand responses to reviews |
| `update-strategy-sequencer` | Campaign update cadence for mid-campaign slump |

### `advertising/` (5 skills)
Paid advertising and market validation.

| Skill | Purpose |
|-------|---------|
| `pre-launch-ads` | 35-step programmatic ad creative protocol |
| `live-campaign-ads` | Live campaign ad headlines across urgency tiers |
| `competitive-ads-extractor` | Competitor ad library analysis |
| `niche-validator` | Reddit/forum complaint cluster scoring |
| `affiliate-program-designer` | Commission structure and swipe copy |

### `publishing/` (2 skills)
Documentation site generation pipeline.

| Skill | Purpose |
|-------|---------|
| `wiki-doc-generator` | Classifies brand outputs → structured wiki markdown |
| `markdown-to-astro-wiki` | Builds iOS26 glassmorphism Astro site from markdown |

**Pipeline:** wiki-doc-generator → markdown-to-astro-wiki

### `visual-pipeline/` (4 skills)
AI visual asset generation orchestration.

| Skill | Purpose |
|-------|---------|
| `brand-visual-pipeline` | Meta-orchestrator: chains prompt → generate → integrate |
| `visual-asset-prompt-generator` | Reads brand docs → structured fal.ai/Hunyuan3D prompts |
| `visual-asset-generator` | Executes AI generation via fal.ai (Nano Banana/Flux) |
| `visual-asset-integrator` | Places generated assets into pages with brand styling |

**Pipeline:** visual-asset-prompt-generator → visual-asset-generator → visual-asset-integrator

## Installation

Skills are auto-discovered by `setup_skills.py` via recursive `SKILL.md` scan. Run:

```bash
bm install skills
```

This creates symlinks in `~/.claude/skills/` for Claude Code discovery.

## Deferred Skills (Phase 4)

7 additional skills pending migration from `claude-skills/`:
`pitchdeck-skill`, `visual-slidedeck-generator`, `visual-video-overview-generator`, `orchv2`, `template-processor-core`, `marketing-copy-openrouter`, `huggingface-api-access`
