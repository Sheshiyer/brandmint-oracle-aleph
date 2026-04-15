# Lessons

- When the user explicitly excludes providers or asset classes (for example, "no Recraft" or "no icons"), remove those lanes from the active plan/config before rerunning anything; do not treat an ambiguous provider mention as permission to keep the legacy assets in scope.
- When a brand run starts reusing old scripted example imagery, treat supplementary references as untrusted until they prove brand relevance: require explicit brand/product term matches or leave `SUPP_REFS` empty instead of falling back to generic community/style examples.
- When the user reframes scope (for example, from "integrate skills" to "replace core provider architecture"), update `tasks/todo.md` immediately with a dedicated migration track and explicit rollback gates.
- For platform replacement decisions, substantiate with official runtime/API docs first, then map capability parity against current code assumptions before recommending cutover.
- When the user explicitly de-scopes an axis (e.g., cost optimization), freeze related implementation/issues as deferred and continue execution on the newly prioritized track without mixing concerns.
- When the user says integration should target image-generation specifically, constrain imported-skill adoption to visual pipeline paths only; avoid broad text-skill substitution unless explicitly requested.
- For Wave 8 publishing work, do not stop at raw `.brandmint/outputs` + generated-image ingestion: explicitly decide whether NotebookLM artifacts must be part of the wiki/library, and default the homepage toward a branded launch experience rather than a generic text-heavy wiki index.
- When the user says the UI still feels generic or under-branded, treat that as a product-design failure, not a cosmetic note: push the portal shell, layout, color system, typography, interaction language, and page composition much closer to the actual brand theme/vibe instead of settling for a mildly customized docs template.
- When overhauling the portal UI, preserve actual wiki affordances (navigation hierarchy, document browsing, internal linking, research pages, readable long-form content) instead of drifting into a marketing-only microsite.
- For repeated Wave 8 rebuilds, treat generated `wiki-site/` cleanup as a real reliability concern — harden deletion logic instead of assuming `shutil.rmtree` will always succeed on the fixture filesystem.
- For bilingual wiki work, verify the main article body in-browser, not just the sidebar or route title — mixed-language fragments can survive even when localized metadata looks correct.
- When a repo review request says to omit a backlog stream (for example `vision-upgrade`), filter that stream out before scoring readiness, risk, and next-wave priorities.
- When the user asks for `autoresearch` loops, explicitly run and document a minimum three-pass keep/discard cycle (detect -> remediate -> verify), not a single-pass patch.
- Keep brand-specific localization packs behind explicit config guards; never let one brand's localized narrative auto-generate for every brand.
- Tests that depend on local fixture repos/paths should skip cleanly when the fixture is absent, rather than failing the whole suite.
