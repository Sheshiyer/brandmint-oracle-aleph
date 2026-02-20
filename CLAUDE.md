# Brandmint — Agent Execution Guide

## The Golden Rule

**NEVER execute brandmint skills individually.** Always use the `bm launch` pipeline.

Brandmint is an orchestrated pipeline of 44 skills across 7 waves plus publishing deliverables. Each skill depends on
outputs from prior skills. Running skills individually breaks the dependency chain and
produces incomplete or inconsistent results.

## How to Run the Pipeline

### Non-interactive (agent environments)

```bash
bm launch --config <path>/brand-config.yaml \
  --scenario <scenario-id> \
  --waves 1-6 \
  --non-interactive
```

### With cost guard

```bash
bm launch --config <path>/brand-config.yaml \
  --scenario brand-genesis \
  --waves 1-6 \
  --non-interactive \
  --max-cost 5.00
```

### Resume from a specific wave

```bash
bm launch --config <path>/brand-config.yaml \
  --scenario brand-genesis \
  --resume-from 4 \
  --non-interactive
```

## How the Pipeline Works

1. `bm launch` computes a wave plan based on brand-config.yaml
2. For each skill, the executor writes a prompt to `.brandmint/prompts/{skill-id}.md`
3. The agent (you) executes the prompt and saves JSON output to `.brandmint/outputs/{skill-id}.json`
4. The executor polls for the output file and proceeds to the next skill
5. Visual asset skills (Wave 3-5) call FAL API directly — no agent intervention needed
6. Wave 7 (Publishing) runs 7A-7F: theme export, NotebookLM, slide decks, reports, diagrams, video

## Wave 7: Publishing & Deliverables

Wave 7 runs automatically at `comprehensive` depth or when `--waves 1-7` is specified.
Sub-steps can also be run standalone via `bm publish`:

| Step | Command | Deliverable |
|------|---------|-------------|
| 7A | automatic | Brand theme (CSS/Typst/JSON) |
| 7B | `bm publish notebooklm` | NotebookLM notebook + audio |
| 7C | `bm publish decks` | Slide decks (PDF via Marp) |
| 7D | `bm publish reports` | Reports (PDF via Typst) |
| 7E | `bm publish diagrams` | Mind maps & diagrams |
| 7F | `bm publish video` | Video overviews (MP4 via Remotion) |

### Video Generation (7F)

Renders 3 branded MP4 videos using Remotion (React-based programmatic video):
- **Brand Sizzle Reel** (60-90s) — Hook, problem, solution, proof, offer, CTA
- **Product Showcase** (30-60s) — Hero, features, differentiation, CTA
- **Audio + Slides** (dynamic) — NotebookLM MP3 synced with brand visuals

```bash
bm publish video --config <path>/brand-config.yaml
bm publish video --config <path>/brand-config.yaml --videos brand-sizzle --force
```

**Requires:** Node.js >= 18, `pip install 'brandmint[video]'`

## Post-Pipeline Publishing (Wiki)

After all waves complete, two publishing skills transform outputs into a documentation site:

### 1. Wiki Documentation Generation

Use the `wiki-doc-generator` skill to transform `.brandmint/outputs/*.json` into structured
markdown wiki pages. This skill uses 4-6 parallel agents via the Task tool.

### 2. Astro Wiki Site Build

Use the `markdown-to-astro-wiki` skill to convert wiki markdown into a glassmorphism Astro site.
Run `process-markdown.sh` with `--images <generated-dir>` to include visual assets.

## What NOT To Do

- Do NOT read individual SKILL.md files and execute them outside the pipeline
- Do NOT use `Confirm.ask()` or any interactive prompts when `--non-interactive` is set
- Do NOT skip skills on EOFError — use polling mode instead
- Do NOT generate visual assets manually — the pipeline handles FAL API calls

## Key Paths

- Brand config: `<brand-dir>/brand-config.yaml`
- Prompts: `<brand-dir>/.brandmint/prompts/`
- Outputs: `<brand-dir>/.brandmint/outputs/`
- Visual assets: `<brand-dir>/<brand-slug>/generated/`
- Pipeline state: `<brand-dir>/.brandmint/state.json`
- Deliverables: `<brand-dir>/deliverables/` (notebooklm, decks, reports, diagrams, videos)
- NotebookLM state: `<brand-dir>/.brandmint/notebooklm-state.json`
- Videos state: `<brand-dir>/.brandmint/videos-state.json`
