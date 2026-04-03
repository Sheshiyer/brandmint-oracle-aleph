"""
Source builder — transforms brandmint JSON outputs into NotebookLM-optimised
markdown source documents.

NotebookLM generates dramatically better artifacts from readable prose than
from raw JSON. This module supports two rendering modes:

1. **Synthesized** (default) — LLM-powered prose synthesis via OpenRouter that
   transforms raw skill JSON into narrative brand prose written *as* the brand.
2. **Mechanical** (fallback) — Direct JSON-to-markdown conversion used when
   no OPENROUTER_API_KEY is set or ``--no-synthesize`` is passed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console

from ..core.kickstarter_blueprint import (
    KICKSTARTER_READINESS_DOC_STEM,
    MANDATORY_KICKSTARTER_ARTIFACTS,
    MANDATORY_KICKSTARTER_SECTIONS,
    artifact_doc_stem,
    build_kickstarter_readiness,
    iter_section_artifacts,
    section_doc_stem,
)


# ---------------------------------------------------------------------------
# Source group definitions
# ---------------------------------------------------------------------------

CORE_SOURCE_GROUPS: Dict[str, Dict[str, Any]] = {
    "brand-foundation": {
        "title": "Brand Foundation",
        "description": "Market validation, target audience, competitive landscape, and core brand definition.",
        "skills": ["niche-validator", "buyer-persona", "competitor-analysis"],
        "include_config_sections": [
            "brand", "theme", "palette", "typography", "materials",
        ],
    },
    "brand-strategy": {
        "title": "Brand Strategy",
        "description": "Product positioning, messaging, voice and tone, visual identity system.",
        "skills": [
            "product-positioning-summary",
            "mds-messaging-direction-summary",
            "voice-and-tone",
            "detailed-product-description",
            "visual-identity-core",
        ],
        "include_config_sections": [],
    },
    "campaign-content": {
        "title": "Campaign Content",
        "description": "Campaign copy, video scripts, advertising creative.",
        "skills": [
            "campaign-page-copy",
            "campaign-video-script",
            "pre-launch-ads",
            "live-campaign-ads",
            "press-release-copy",
        ],
        "include_config_sections": [],
    },
    "communications-social": {
        "title": "Communications & Social Strategy",
        "description": "Email sequences, social media calendar, influencer outreach, community management.",
        "skills": [
            "welcome-email-sequence",
            "pre-launch-email-sequence",
            "launch-email-sequence",
            "social-content-engine",
            "short-form-hook-generator",
            "influencer-outreach-pro",
            "review-response-strategist",
        ],
        "include_config_sections": [],
    },
    "visual-asset-catalog": {
        "title": "Visual Asset Catalog",
        "description": "Inventory of all generated visual assets with descriptions and usage context.",
        "skills": [],
        "include_config_sections": ["prompts", "photography", "illustration"],
        "scan_visual_assets": True,
    },
}

# Backwards-compatible export used by the prose synthesizer.
SOURCE_GROUPS: Dict[str, Dict[str, Any]] = dict(CORE_SOURCE_GROUPS)

SOURCE_DOCUMENT_MODES = {"hybrid", "legacy-only", "kickstarter-only"}


def resolve_source_document_mode(config: dict) -> str:
    """Resolve which source document families should be generated."""
    mode = (
        config.get("publishing", {})
        .get("notebooklm", {})
        .get("source_document_mode", "hybrid")
    )
    mode = str(mode).strip().lower() if mode is not None else "hybrid"
    if mode not in SOURCE_DOCUMENT_MODES:
        return "hybrid"
    return mode


# ---------------------------------------------------------------------------
# Skill-specific formatters
# ---------------------------------------------------------------------------


def _format_handoff(skill_id: str, data: dict, heading_level: int = 2) -> str:
    """Convert a skill's handoff dict into markdown sections."""
    handoff = data.get("handoff", data)
    meta = data.get("meta", {})

    parts: List[str] = []
    skill_name = meta.get("skill", skill_id).replace("-", " ").title()
    prefix = "#" * heading_level
    sub_prefix = "#" * min(heading_level + 1, 6)
    parts.append(f"{prefix} {skill_name}\n")

    # Narrative summary if available
    narrative = data.get("narrative") or handoff.get("narrative")
    if narrative:
        parts.append(f"{narrative}\n")

    # Walk the handoff keys
    for key, value in handoff.items():
        if key in ("narrative",):
            continue
        heading = key.replace("_", " ").title()
        parts.append(f"{sub_prefix} {heading}\n")
        parts.append(_render_value(value, depth=0))

    return "\n".join(parts)



def _render_value(value: Any, depth: int = 0) -> str:
    """Recursively render a value as markdown."""
    if isinstance(value, str):
        return f"{value}\n"
    elif isinstance(value, (int, float, bool)):
        return f"{value}\n"
    elif isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                summary = _dict_summary(item)
                lines.append(f"{'  ' * depth}- {summary}")
            else:
                lines.append(f"{'  ' * depth}- {item}")
        return "\n".join(lines) + "\n"
    elif isinstance(value, dict):
        lines = []
        for k, v in value.items():
            label = k.replace("_", " ").title()
            if isinstance(v, (str, int, float, bool)):
                lines.append(f"- **{label}:** {v}")
            elif isinstance(v, list):
                lines.append(f"- **{label}:**")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(f"  - {_dict_summary(item)}")
                    else:
                        lines.append(f"  - {item}")
            elif isinstance(v, dict):
                lines.append(f"\n#### {label}\n")
                lines.append(_render_value(v, depth + 1))
        return "\n".join(lines) + "\n"
    return str(value) + "\n"



def _dict_summary(d: dict) -> str:
    """Produce a compact one-line summary of a dict."""
    parts = []
    for k, v in d.items():
        if isinstance(v, (str, int, float)):
            label = k.replace("_", " ").title()
            text = str(v)
            if len(text) > 120:
                text = text[:117] + "..."
            parts.append(f"**{label}:** {text}")
    return " | ".join(parts[:4])


# ---------------------------------------------------------------------------
# Config section renderer
# ---------------------------------------------------------------------------


def _render_config_section(config: dict, section_key: str) -> str:
    """Render a brand-config.yaml section as markdown."""
    section = config.get(section_key, {})
    if not section:
        return ""

    heading = section_key.replace("_", " ").title()
    parts = [f"### {heading} (from brand config)\n"]
    parts.append(_render_value(section, depth=0))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Visual asset scanner
# ---------------------------------------------------------------------------


def _scan_visual_assets(brand_dir: Path, config: dict) -> str:
    """Build a descriptive catalog of generated visual assets."""
    brand_name = config.get("brand", {}).get("name", "brand")
    slug = brand_name.lower().replace(" ", "-").replace("'", "")

    gen_dir = None
    for candidate in [
        brand_dir / slug / "generated",
        brand_dir / "generated",
        brand_dir / brand_name / "generated",
    ]:
        if candidate.is_dir():
            gen_dir = candidate
            break

    if gen_dir is None:
        return "### Generated Visual Assets\n\nNo generated assets directory found.\n"

    parts = ["### Generated Visual Assets\n"]
    image_files = sorted(gen_dir.glob("*.png")) + sorted(gen_dir.glob("*.webp"))

    if not image_files:
        parts.append("No visual asset files found in the generated directory.\n")
        return "\n".join(parts)

    parts.append(f"Total: {len(image_files)} visual assets\n")

    groups: Dict[str, List[Path]] = {}
    for f in image_files:
        stem = f.stem
        prefix = stem.split("-")[0] if "-" in stem else stem
        groups.setdefault(prefix, []).append(f)

    for prefix, files in sorted(groups.items()):
        size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
        parts.append(
            f"- **{prefix}**: {len(files)} file(s), {size_mb:.1f} MB total"
        )
        for f in files[:3]:
            parts.append(f"  - `{f.name}`")

    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Manifest reader
# ---------------------------------------------------------------------------


def _read_generation_manifest(brand_dir: Path, config: dict) -> str:
    """Read generation-manifest.json if it exists."""
    brand_name = config.get("brand", {}).get("name", "brand")
    slug = brand_name.lower().replace(" ", "-").replace("'", "")

    for candidate in [
        brand_dir / slug / "generated" / "generation-manifest.json",
        brand_dir / "generated" / "generation-manifest.json",
    ]:
        if candidate.is_file():
            try:
                manifest = json.loads(candidate.read_text())
                parts = ["### Generation Manifest\n"]
                parts.append(f"- **Total assets:** {manifest.get('total_assets', 'N/A')}")
                parts.append(f"- **Total API calls:** {manifest.get('total_api_calls', 'N/A')}")
                parts.append(f"- **Estimated cost:** ${manifest.get('estimated_cost_usd', 0):.2f}")
                parts.append(f"- **Mode:** {manifest.get('mode', 'N/A')}")
                assets = manifest.get("assets", [])
                if assets:
                    parts.append("\n#### Asset Details\n")
                    for a in assets:
                        parts.append(
                            f"- **{a.get('id', '?')}** ({a.get('name', '')}): "
                            f"{a.get('model', 'unknown')} model, "
                            f"{a.get('seeds', 0)} seeds, "
                            f"~${a.get('est_cost', 0):.2f}"
                        )
                return "\n".join(parts) + "\n"
            except (json.JSONDecodeError, OSError):
                pass
    return ""


# ---------------------------------------------------------------------------
# Kickstarter prototype renderers
# ---------------------------------------------------------------------------


def _render_kickstarter_section_doc(section_id: str, skill_outputs: Dict[str, dict], config: dict) -> str:
    """Render a section-oriented Kickstarter source document."""
    section = MANDATORY_KICKSTARTER_SECTIONS[section_id]
    readiness = build_kickstarter_readiness(skill_outputs)
    row = readiness["section_status"][section_id]
    brand_name = config.get("brand", {}).get("name", "Brand")

    parts = [
        f"# {section.title}\n",
        f"> {section.description}\n",
        f"**Brand:** {brand_name}\n",
        f"**Readiness:** {'Ready' if row['ready'] else 'In progress'} ({row['completed']}/{row['total']} artifacts available)\n",
    ]

    if row["missing_artifact_ids"]:
        parts.append("## Missing Mandatory Artifacts\n")
        for artifact_id in row["missing_artifact_ids"]:
            artifact = MANDATORY_KICKSTARTER_ARTIFACTS[artifact_id]
            parts.append(f"- **{artifact.title}:** waiting on `{artifact.source_skill_id}` output")
        parts.append("")

    for artifact in iter_section_artifacts(section_id):
        parts.append(f"## {artifact.title}\n")
        parts.append(f"> Source skill: `{artifact.source_skill_id}` — {artifact.description}\n")
        payload = skill_outputs.get(artifact.source_skill_id)
        if payload:
            parts.append(_format_handoff(artifact.source_skill_id, payload, heading_level=3))
        else:
            parts.append("_This mandatory artifact has not been generated yet._\n")

    return "\n".join(parts).strip() + "\n"



def _render_kickstarter_artifact_doc(artifact_id: str, skill_outputs: Dict[str, dict], config: dict) -> Optional[str]:
    """Render an artifact-focused Kickstarter source document if data exists."""
    artifact = MANDATORY_KICKSTARTER_ARTIFACTS[artifact_id]
    payload = skill_outputs.get(artifact.source_skill_id)
    if not payload:
        return None

    brand_name = config.get("brand", {}).get("name", "Brand")
    section = MANDATORY_KICKSTARTER_SECTIONS[artifact.section_id]
    parts = [
        f"# {artifact.title}\n",
        f"> {artifact.description}\n",
        f"**Brand:** {brand_name}\n",
        f"**Kickstarter Section:** {section.title}\n",
        f"**Source Skill:** `{artifact.source_skill_id}`\n",
        _format_handoff(artifact.source_skill_id, payload, heading_level=2),
    ]
    return "\n".join(parts).strip() + "\n"



def _render_kickstarter_readiness_doc(skill_outputs: Dict[str, dict], config: dict) -> str:
    """Render the mandatory Kickstarter readiness summary."""
    readiness = build_kickstarter_readiness(skill_outputs)
    brand_name = config.get("brand", {}).get("name", "Brand")

    parts = [
        "# Kickstarter Prototype Readiness\n",
        "> Mandatory section and artifact coverage for Kickstarter-capable products.\n",
        f"**Brand:** {brand_name}\n",
        f"**Overall Readiness:** {'Ready' if readiness['all_ready'] else 'Incomplete'}\n",
        "## Section Status\n",
    ]

    for section_id, section in MANDATORY_KICKSTARTER_SECTIONS.items():
        row = readiness["section_status"][section_id]
        parts.append(
            f"- **{section.title}:** {'Ready' if row['ready'] else 'In progress'} "
            f"({row['completed']}/{row['total']})"
        )
        if row["missing_artifact_ids"]:
            missing = ", ".join(
                MANDATORY_KICKSTARTER_ARTIFACTS[artifact_id].title
                for artifact_id in row["missing_artifact_ids"]
            )
            parts.append(f"  - Missing: {missing}")

    parts.append("\n## Artifact Status\n")
    for artifact_id, artifact in MANDATORY_KICKSTARTER_ARTIFACTS.items():
        status = readiness["artifact_status"][artifact_id]
        parts.append(
            f"- **{artifact.title}:** {'Available' if status else 'Missing'} "
            f"(source: `{artifact.source_skill_id}`)"
        )

    return "\n".join(parts).strip() + "\n"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_source_group_definitions(document_mode: str = "hybrid") -> Dict[str, Dict[str, Any]]:
    """Return metadata for all generated source documents."""
    mode = document_mode if document_mode in SOURCE_DOCUMENT_MODES else "hybrid"
    groups: Dict[str, Dict[str, Any]] = {}

    if mode in {"hybrid", "legacy-only"}:
        groups.update(CORE_SOURCE_GROUPS)

    if mode in {"hybrid", "kickstarter-only"}:
        for section_id, section in MANDATORY_KICKSTARTER_SECTIONS.items():
            groups[section_doc_stem(section_id)] = {
                "title": section.title,
                "description": section.description,
                "skills": [artifact.source_skill_id for artifact in iter_section_artifacts(section_id)],
                "category": "kickstarter-section",
            }

        for artifact_id, artifact in MANDATORY_KICKSTARTER_ARTIFACTS.items():
            groups[artifact_doc_stem(artifact_id)] = {
                "title": artifact.title,
                "description": artifact.description,
                "skills": [artifact.source_skill_id],
                "category": "kickstarter-artifact",
            }

        groups[KICKSTARTER_READINESS_DOC_STEM] = {
            "title": "Kickstarter Prototype Readiness",
            "description": "Mandatory Kickstarter-capable product section coverage and missing artifact summary.",
            "skills": [],
            "category": "kickstarter-readiness",
        }
    return groups


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_source_documents(
    outputs_dir: Path,
    config: dict,
    config_path: Path,
    brand_dir: Path,
    output_dir: Path,
    *,
    synthesize: bool = True,
    model: str = "",
    console: Optional[Console] = None,
) -> Dict[str, Path]:
    """Build all source markdown documents and write to output_dir."""
    _console = console or Console()
    output_dir.mkdir(parents=True, exist_ok=True)

    skill_outputs: Dict[str, dict] = {}
    if outputs_dir.is_dir():
        for f in outputs_dir.glob("*.json"):
            skill_id = f.stem
            try:
                skill_outputs[skill_id] = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                pass

    document_mode = resolve_source_document_mode(config)
    synthesized: Dict[str, str] = {}
    if synthesize and document_mode in {"hybrid", "legacy-only"}:
        from .prose_synthesizer import ProseSynthesizer, DEFAULT_MODEL

        voice_config = skill_outputs.get("voice-and-tone", {})
        synth = ProseSynthesizer(
            voice_config=voice_config,
            brand_config=config,
            model=model or DEFAULT_MODEL,
            cache_dir=brand_dir / ".brandmint" / "prose-cache",
            console=_console,
        )

        if synth.available:
            synthesized = synth.synthesize_all(
                groups=SOURCE_GROUPS,
                skill_outputs=skill_outputs,
                config=config,
            )
        else:
            _console.print(
                "  [yellow]OPENROUTER_API_KEY not set — falling back to mechanical rendering[/yellow]"
            )

    result: Dict[str, Path] = {}
    brand_name = config.get("brand", {}).get("name", "Brand")

    if document_mode in {"hybrid", "legacy-only"}:
        for group_id, group_def in CORE_SOURCE_GROUPS.items():
            if group_id in synthesized:
                doc_path = output_dir / f"{group_id}.md"
                doc_path.write_text(synthesized[group_id])
                result[group_id] = doc_path
                continue

            parts: List[str] = []
            parts.append(f"# {group_def['title']}\n")
            parts.append(f"> {group_def['description']}\n")
            parts.append(f"**Brand:** {brand_name}\n")

            for section_key in group_def.get("include_config_sections", []):
                rendered = _render_config_section(config, section_key)
                if rendered:
                    parts.append(rendered)

            for skill_id in group_def.get("skills", []):
                if skill_id in skill_outputs:
                    parts.append(_format_handoff(skill_id, skill_outputs[skill_id]))

            if group_def.get("scan_visual_assets"):
                parts.append(_scan_visual_assets(brand_dir, config))
                parts.append(_read_generation_manifest(brand_dir, config))

            doc_path = output_dir / f"{group_id}.md"
            doc_path.write_text("\n".join(parts))
            result[group_id] = doc_path

    if document_mode in {"hybrid", "kickstarter-only"}:
        # Section-oriented Kickstarter docs
        for section_id in MANDATORY_KICKSTARTER_SECTIONS:
            group_id = section_doc_stem(section_id)
            doc_path = output_dir / f"{group_id}.md"
            doc_path.write_text(_render_kickstarter_section_doc(section_id, skill_outputs, config))
            result[group_id] = doc_path

        # Per-artifact Kickstarter docs (only when backing skill output exists)
        for artifact_id in MANDATORY_KICKSTARTER_ARTIFACTS:
            rendered = _render_kickstarter_artifact_doc(artifact_id, skill_outputs, config)
            if rendered is None:
                continue
            group_id = artifact_doc_stem(artifact_id)
            doc_path = output_dir / f"{group_id}.md"
            doc_path.write_text(rendered)
            result[group_id] = doc_path

        readiness_path = output_dir / f"{KICKSTARTER_READINESS_DOC_STEM}.md"
        readiness_path.write_text(_render_kickstarter_readiness_doc(skill_outputs, config))
        result[KICKSTARTER_READINESS_DOC_STEM] = readiness_path

    known_paths: Set[Path] = {
        output_dir / f"{group_id}.md"
        for group_id in get_source_group_definitions("hybrid")
    }
    generated_paths = set(result.values())
    for known_path in known_paths:
        if known_path not in generated_paths and known_path.exists():
            known_path.unlink()

    return result
