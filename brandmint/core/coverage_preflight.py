"""Scenario/depth coverage preflight for publish-quality runs."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .kickstarter_blueprint import mandatory_source_skill_ids
from .wave_planner import compute_wave_plan


def build_coverage_preflight(
    config: dict,
    scenario_id: Optional[str] = None,
    depth: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a coverage report from scenario + depth wave planning.

    Returns a machine-readable summary used to detect likely Wave 7 quality risks.
    """
    resolved_depth = depth or config.get("execution_context", {}).get("depth_level", "focused")
    waves = compute_wave_plan(config, scenario_id=scenario_id, depth=resolved_depth)

    wave_rows: List[Dict[str, Any]] = []
    planned_text_skills: List[str] = []
    planned_visual_assets: List[str] = []

    for wave in waves:
        planned_text_skills.extend(wave.text_skills)
        planned_visual_assets.extend(wave.visual_assets)
        wave_rows.append(
            {
                "number": wave.number,
                "name": wave.name,
                "text_skill_count": len(wave.text_skills),
                "visual_asset_count": len(wave.visual_assets),
                "post_hook": wave.post_hook,
                "is_empty_execution_wave": (
                    len(wave.text_skills) == 0
                    and len(wave.visual_assets) == 0
                    and not wave.post_hook
                ),
            }
        )

    planned_text_set = sorted(set(planned_text_skills))
    planned_visual_set = sorted(set(planned_visual_assets))

    required_skills = mandatory_source_skill_ids()
    missing_mandatory_skills = [skill_id for skill_id in required_skills if skill_id not in planned_text_set]

    empty_execution_waves = [row["number"] for row in wave_rows if row["is_empty_execution_wave"]]

    warnings: List[str] = []
    if missing_mandatory_skills:
        warnings.append(
            "Mandatory source skills missing from wave plan; source docs may degrade to placeholders."
        )
    if any(w in empty_execution_waves for w in (4, 5, 6)):
        warnings.append(
            "One or more core content waves (4-6) are empty; expect weak Wave 7 source quality."
        )
    if not planned_visual_set:
        warnings.append(
            "No visual assets are planned; visual storytelling artifacts will be low fidelity."
        )

    return {
        "scenario_id": scenario_id,
        "depth": resolved_depth,
        "wave_count": len(waves),
        "waves": wave_rows,
        "planned_text_skills": planned_text_set,
        "planned_visual_assets": planned_visual_set,
        "missing_mandatory_source_skills": missing_mandatory_skills,
        "empty_execution_waves": empty_execution_waves,
        "warnings": warnings,
    }
