# Front UI Execution Plan (Taskmaster v2, docs/prompt-first)

## Sequence
1. **P0 Documentation & Narrative Foundation** (S1-S2)
2. **P1 Prompt Scaffolding First** (S3-S4)
3. **P2 Front UI Core Journey** (S5-S6)
4. **P3 Visual Design Elevation** (S7-S8)
5. **P4 Orchestration UX Upgrade** (S9-S10)
6. **P5 Backend Integration & Data Intelligence** (S11-S12)
7. **P6 QA Hardening & Launch** (S13-S14)

## Execution Gates
- Gate A: P0 sign-off (docs + user journey + success criteria)
- Gate B: P1 sign-off (prompt scaffolds + QA harness score >= 90%)
- Gate C: P2 sign-off (Product MD upload -> extraction review -> config wizard -> export works)
- Gate D: P3/P4 sign-off (premium visual polish and appealing UX validated)
- Gate E: P5/P6 sign-off (backend reliability, QA hardening, launch readiness)

## Parallel Dispatch Rules
- Use lane-level dispatch: `ux`, `prompt`, `frontend`, `integration`, `qa`, `platform`, `docs`, `security`.
- Start with up to 4 lanes in parallel per sprint.
- Respect explicit task dependencies before dispatching blocked tasks.
- Daily checkpoint: unblockers + risk review + scope trim decisions.

## Non-Negotiable User Experience Targets
- Product-MD-first flow (no terminal-first feel)
- Non-technical language by default
- Editorial + premium visual system inspired by X references
- Calm, trustworthy orchestration controls with clear retries/recovery
