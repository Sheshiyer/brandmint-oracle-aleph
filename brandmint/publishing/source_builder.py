"""
Source builder — transforms brandmint JSON outputs into NotebookLM-optimised
markdown source documents.

NotebookLM generates dramatically better artifacts from readable prose than
from raw JSON. This module converts each skill's structured output into
natural language sections grouped into 5 thematic documents.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Source group definitions
# ---------------------------------------------------------------------------

SOURCE_GROUPS: Dict[str, Dict[str, Any]] = {
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


# ---------------------------------------------------------------------------
# Skill-specific formatters
# ---------------------------------------------------------------------------

def _format_handoff(skill_id: str, data: dict) -> str:
    """Convert a skill's handoff dict into markdown sections."""
    handoff = data.get("handoff", data)
    meta = data.get("meta", {})

    parts: List[str] = []
    skill_name = meta.get("skill", skill_id).replace("-", " ").title()
    parts.append(f"## {skill_name}\n")

    # Narrative summary if available
    narrative = data.get("narrative") or handoff.get("narrative")
    if narrative:
        parts.append(f"{narrative}\n")

    # Walk the handoff keys
    for key, value in handoff.items():
        if key in ("narrative",):
            continue
        heading = key.replace("_", " ").title()
        parts.append(f"### {heading}\n")
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
                # Inline dict as a bullet with sub-fields
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

    # Try common generated directories
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

    # Scan for images
    parts = ["### Generated Visual Assets\n"]
    image_files = sorted(gen_dir.glob("*.png")) + sorted(gen_dir.glob("*.webp"))

    if not image_files:
        parts.append("No visual asset files found in the generated directory.\n")
        return "\n".join(parts)

    parts.append(f"Total: {len(image_files)} visual assets\n")

    # Group by asset ID prefix
    groups: Dict[str, List[Path]] = {}
    for f in image_files:
        # Extract asset ID from filename (e.g., "2A-brand-kit-bento-grid-seed1.png")
        stem = f.stem
        prefix = stem.split("-")[0] if "-" in stem else stem
        groups.setdefault(prefix, []).append(f)

    for prefix, files in sorted(groups.items()):
        size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
        parts.append(
            f"- **{prefix}**: {len(files)} file(s), {size_mb:.1f} MB total"
        )
        for f in files[:3]:  # Show up to 3 filenames
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
# Public API
# ---------------------------------------------------------------------------

def build_source_documents(
    outputs_dir: Path,
    config: dict,
    config_path: Path,
    brand_dir: Path,
    output_dir: Path,
) -> Dict[str, Path]:
    """Build all source markdown documents and write to output_dir.

    Args:
        outputs_dir: Path to ``.brandmint/outputs/`` directory.
        config: Parsed brand-config.yaml dict.
        config_path: Path to brand-config.yaml file.
        brand_dir: Root brand directory (parent of .brandmint/).
        output_dir: Where to write the markdown source documents.

    Returns:
        Dict mapping group_id to the written file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load all available skill outputs
    skill_outputs: Dict[str, dict] = {}
    if outputs_dir.is_dir():
        for f in outputs_dir.glob("*.json"):
            skill_id = f.stem
            try:
                skill_outputs[skill_id] = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                pass

    result: Dict[str, Path] = {}

    for group_id, group_def in SOURCE_GROUPS.items():
        parts: List[str] = []

        # Header
        parts.append(f"# {group_def['title']}\n")
        parts.append(f"> {group_def['description']}\n")
        brand_name = config.get("brand", {}).get("name", "Brand")
        parts.append(f"**Brand:** {brand_name}\n")

        # Config sections
        for section_key in group_def.get("include_config_sections", []):
            rendered = _render_config_section(config, section_key)
            if rendered:
                parts.append(rendered)

        # Skill outputs
        for skill_id in group_def.get("skills", []):
            if skill_id in skill_outputs:
                parts.append(_format_handoff(skill_id, skill_outputs[skill_id]))
            # Silently skip missing skills — not all brands run all skills

        # Visual asset catalog (special case)
        if group_def.get("scan_visual_assets"):
            parts.append(_scan_visual_assets(brand_dir, config))
            parts.append(_read_generation_manifest(brand_dir, config))

        # Write document
        doc_path = output_dir / f"{group_id}.md"
        doc_path.write_text("\n".join(parts))
        result[group_id] = doc_path

    return result
