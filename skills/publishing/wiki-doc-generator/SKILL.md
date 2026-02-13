---
name: wiki-doc-generator
description: Generate structured wiki documentation from brand campaign outputs and business artifacts using parallel agent dispatch.
---

## Execution Context

> **This skill runs AFTER the brandmint pipeline completes, not as part of it.**
> It reads JSON outputs from `.brandmint/outputs/` and generates wiki markdown.
> Always use parallel agents (Task tool) for document generation — never generate pages sequentially.
> If running from `bm launch`, ensure all waves have completed first.

# Wiki Documentation Generator

Transform campaign outputs and business documents into structured, interconnected wiki documentation using parallel agent dispatch for maximum efficiency.

## Workflow Overview

```
Phase 1: Inventory        → Scan input documents, classify by type
Phase 2: Dispatch Agents  → Parallel processing of document categories
Phase 3: Cross-link       → Build navigation and internal references
Phase 4: Output           → Generate wiki-ready markdown structure
```

## Phase 1: Inventory Source Documents

Scan the input location for source documents. Classify each by type:

| Document Type | Source Skill | Wiki Section |
|--------------|--------------|--------------|
| MDS (Messaging Direction Summary) | mds-messaging-direction-summary | Product Overview, Features |
| Buyer Persona | buyer-persona | User Personas |
| Product Positioning | product-positioning-summary | Brand Positioning |
| Voice & Tone | voice-and-tone | Brand Guidelines |
| Competitor Analysis | competitor-analysis | Market Context |
| Detailed Product Description | detailed-product-description | Product Specs |
| Campaign Page Copy | campaign-page-copy | Marketing Assets |
| Email Sequences | welcome/pre-launch/launch-email-sequence | Communications |
| Proposal | thoughtseed-proposal-generator *(planned)* | Technical Architecture, Timeline |
| Contract | thoughtseed-contract-generator *(planned)* | Project Scope, Deliverables |

Run inventory script to classify:
```bash
python3 scripts/inventory-sources.py /path/to/source/documents
```

### Visual Asset Inventory

If the brand has generated visual assets (via `bm visual`), also generate the asset-to-wiki mapping:

```bash
python3 scripts/map-assets-to-wiki.py /path/to/brand/generated/
```

This produces `wiki-asset-map.json` which maps each visual asset to its target wiki page, section, and role (hero, inline, gallery, or meta). Pass this mapping to agents in Phase 2 so they embed images in the correct locations.

## Phase 2: Dispatch Parallel Agents

Each document category becomes an independent agent task. Process 3-5 categories in parallel using the dispatching-parallel-agents pattern.

### Agent Categories

**Agent 1: Foundation Docs**
- Sources: MDS, Product Positioning, Detailed Product Description
- Outputs: `product/overview.md`, `product/features.md`, `product/specifications.md`

**Agent 2: Brand Docs**
- Sources: Voice & Tone, Visual Identity (if present)
- Outputs: `brand/voice-tone.md`, `brand/visual-guidelines.md`, `brand/writing-principles.md`

**Agent 3: Persona Docs**
- Sources: Buyer Persona, Competitor Analysis
- Outputs: `audience/primary-persona.md`, `audience/secondary-personas.md`, `market/competitive-landscape.md`

**Agent 4: Marketing Assets**
- Sources: Campaign Copy, Email Sequences, Ad Copy
- Outputs: `marketing/campaign-copy.md`, `marketing/email-templates.md`, `marketing/ad-creative.md`

**Agent 5: Project Docs** (if Proposal/Contract present)
- Sources: Proposal, Contract
- Outputs: `project/architecture.md`, `project/timeline.md`, `project/team-roles.md`

**Agent 6: Visual Assets** (if `wiki-asset-map.json` exists)
- Sources: `wiki-asset-map.json`, generated image directory
- Outputs: `brand/visual-assets.md` — a gallery page listing ALL visual assets organized by category
- Schema: See `references/doc-schemas.md` → Visual Asset Library

### Agent Task Template

```markdown
## Task: Generate {Category} Wiki Documentation

**Input Sources:**
{List of source files with paths}

**Output Requirements:**
1. Extract key information following the schema in references/doc-schemas.md
2. Generate markdown files with proper frontmatter
3. Include cross-references to related documents (use relative paths)
4. Maintain heading hierarchy (H1 = page title, H2 = sections)
5. If `wiki-asset-map.json` is available, embed images for your pages using `![Alt](/images/filename.png)` syntax. Place hero images after the H1. Place inline images within their mapped sections.

**Output Location:** /home/claude/wiki-output/{category}/

**Quality Checklist:**
- [ ] Source content synthesized (no copy-paste dumps)
- [ ] Frontmatter includes: title, description, category, tags
- [ ] Internal links use relative paths
- [ ] Code/technical content in fenced blocks

Return: Summary of generated files and any content gaps found.
```

## Phase 3: Cross-Link and Structure

After agents return, build navigation and cross-references.

### Navigation Structure

Generate `navigation.yaml`:
```yaml
- title: Getting Started
  items:
    - index.md
    - quickstart.md

- title: Product
  items:
    - product/overview.md
    - product/features.md
    - product/specifications.md

- title: Brand
  items:
    - brand/voice-tone.md
    - brand/visual-guidelines.md

- title: Audience
  items:
    - audience/primary-persona.md
    - audience/secondary-personas.md

- title: Marketing
  items:
    - marketing/campaign-copy.md
    - marketing/email-templates.md

- title: Project
  items:
    - project/architecture.md
    - project/timeline.md
```

### Cross-Reference Rules

1. **Persona → Product**: Link user needs to features that address them
2. **Voice → Marketing**: Link tone guidelines to content examples
3. **Architecture → Timeline**: Link technical components to delivery phases
4. **Positioning → Competitor**: Link differentiators to competitive gaps

## Phase 4: Output Structure

```
wiki-output/
├── index.md                    # Homepage with project overview
├── navigation.yaml             # Sidebar configuration
├── getting-started/
│   └── quickstart.md
├── product/
│   ├── overview.md
│   ├── features.md
│   └── specifications.md
├── brand/
│   ├── voice-tone.md
│   ├── visual-guidelines.md
│   └── visual-assets.md          # Gallery of all visual assets (Agent 6)
├── audience/
│   ├── primary-persona.md
│   └── secondary-personas.md
├── market/
│   └── competitive-landscape.md
├── marketing/
│   ├── campaign-copy.md
│   ├── email-templates.md
│   └── ad-creative.md
└── project/
    ├── architecture.md
    ├── timeline.md
    └── scope.md
```

## Document Frontmatter Schema

Every generated markdown file includes:

```yaml
---
title: "Page Title"
description: "One-line description for SEO and navigation"
category: "product|brand|audience|marketing|project"
tags: ["relevant", "keywords"]
sources: ["mds.md", "positioning.md"]
lastUpdated: "2025-01-24"
---
```

## Scenario-Based Depth

Adapt output based on project context:

| Scenario | Pages | Sections Included |
|----------|-------|-------------------|
| Brand Genesis ($3K) | 5-8 | Foundation + Brand basics |
| Crowdfunding Lean | 12-15 | + Personas + Marketing basics |
| Crowdfunding Full | 20-25 | + Full marketing + Project |
| DTC Launch | 15-18 | All sections, moderate depth |
| Enterprise GTM | 25-30 | All sections, maximum depth |

## Integration with Astro

After generating wiki docs, build with markdown-to-astro-wiki:

```bash
# Wiki output location
/home/claude/wiki-output/

# Initialize Astro project
./scripts/init-astro-wiki.sh project-wiki

# Process markdown WITH images (if generated/ directory exists)
./scripts/process-markdown.sh /home/claude/wiki-output ./project-wiki/src/content/docs --images /path/to/brand/generated/

# Build
cd project-wiki && bun run build
```

The `--images` flag copies all visual assets (PNG, JPG, WebP) from the generated directory into `public/images/` so that `![Alt](/images/filename.png)` references in markdown resolve correctly.

## Error Handling

- **Missing sources**: Generate placeholder with TODO markers
- **Conflicting info**: Flag in output, cite both sources
- **Incomplete sources**: Extract available content, note gaps

## Resources

- `references/doc-schemas.md` - Detailed schemas for each wiki page type
- `references/frontmatter-templates.md` - Frontmatter examples by category
- `scripts/inventory-sources.py` - Scan and classify input documents (text + visual)
- `scripts/map-assets-to-wiki.py` - Map visual assets to wiki pages
- `scripts/validate-wiki.py` - Check output structure and links
