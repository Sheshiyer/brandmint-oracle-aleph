# Prompt Scaffolding Starter (v2)

## Priority Order (Docs + Prompt-First)
1. **Product MD extraction prompt** — parse product narrative, audience, offer, differentiators.
2. **Brand-config synthesis prompt** — map extraction into valid `brand-config.yaml` fields.
3. **Aesthetic direction prompt** — derive visual direction from X-reference tags and selected style anchors.
4. **Wizard microcopy prompt** — rewrite technical language into plain, friendly coaching text.
5. **Error clarity + recovery prompt** — convert failures into actionable user guidance.

## Prompt QA Harness
- Build 20 golden Product MD examples (simple → complex).
- Score each prompt run on: correctness, completeness, clarity, tone, and hallucination risk.
- Promote only prompts with >= 90% pass rate over golden set.
- Keep changelog with: version, reason, before/after, observed regression risk.

## Dispatch Pattern
- Run extraction + synthesis + microcopy prompts in parallel lanes after shared schema contract is frozen.
- Run prompt QA lane independently from UI implementation lane.
- If one prompt regresses, rollback that prompt only; keep other lanes active.

## Immediate Deliverables
- `prompt-registry.json`
- `prompt-golden-set.json`
- `prompt-eval-report.md`
- `prompt-changelog.md`
