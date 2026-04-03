"""Kickstarter prototype blueprint.

Defines the mandatory section structure for Kickstarter-capable products and
provides shared helpers for source generation, readiness reporting, and later
prototype orchestration work.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class KickstarterArtifact:
    """A mandatory prototype artifact for Kickstarter-capable products."""

    artifact_id: str
    title: str
    source_skill_id: str
    section_id: str
    description: str


@dataclass(frozen=True)
class KickstarterSection:
    """A logical section in the Kickstarter prototype program."""

    section_id: str
    title: str
    description: str
    artifact_ids: Tuple[str, ...]


MANDATORY_KICKSTARTER_ARTIFACTS: Dict[str, KickstarterArtifact] = {
    "market-buyer-persona": KickstarterArtifact(
        artifact_id="market-buyer-persona",
        title="Market Buyer Persona",
        source_skill_id="buyer-persona",
        section_id="market-understanding",
        description="Target audience profile, pains, motivations, and buying triggers.",
    ),
    "competitor-summary": KickstarterArtifact(
        artifact_id="competitor-summary",
        title="Competitor Summary",
        source_skill_id="competitor-analysis",
        section_id="market-understanding",
        description="Competitive landscape, standout gaps, and differentiation context.",
    ),
    "detailed-product-description": KickstarterArtifact(
        artifact_id="detailed-product-description",
        title="Detailed Product Description",
        source_skill_id="detailed-product-description",
        section_id="product-detailing",
        description="Detailed feature, benefit, material, and proof narrative for the product.",
    ),
    "product-positioning-summary": KickstarterArtifact(
        artifact_id="product-positioning-summary",
        title="Product Positioning Summary",
        source_skill_id="product-positioning-summary",
        section_id="product-detailing",
        description="Unique value proposition and strategic positioning in the market.",
    ),
    "mds": KickstarterArtifact(
        artifact_id="mds",
        title="Messaging & Direction Summary",
        source_skill_id="mds-messaging-direction-summary",
        section_id="product-detailing",
        description="Message hierarchy, promises, proof points, and strategic language direction.",
    ),
    "voice-and-tone": KickstarterArtifact(
        artifact_id="voice-and-tone",
        title="Voice and Tone",
        source_skill_id="voice-and-tone",
        section_id="product-detailing",
        description="Brand writing persona, tonal bounds, and stylistic rules.",
    ),
    "landing-page-copy": KickstarterArtifact(
        artifact_id="landing-page-copy",
        title="Landing Page Copy",
        source_skill_id="campaign-page-copy",
        section_id="crafting-compelling-copy",
        description="Conversion-oriented page copy used as the prototype landing-page layer.",
    ),
    "pre-launch-ads-copy": KickstarterArtifact(
        artifact_id="pre-launch-ads-copy",
        title="Pre-Launch Ads Copy",
        source_skill_id="pre-launch-ads",
        section_id="crafting-compelling-copy",
        description="Audience-targeted pre-launch ad concepts, hooks, and CTA angles.",
    ),
    "welcome-email-sequence": KickstarterArtifact(
        artifact_id="welcome-email-sequence",
        title="Welcome Email Sequence",
        source_skill_id="welcome-email-sequence",
        section_id="email-strategy",
        description="Lead nurturing welcome email flow.",
    ),
    "pre-launch-email-sequence": KickstarterArtifact(
        artifact_id="pre-launch-email-sequence",
        title="Pre-Launch Email Sequence",
        source_skill_id="pre-launch-email-sequence",
        section_id="email-strategy",
        description="Momentum-building email flow before launch.",
    ),
    "launch-email-sequence": KickstarterArtifact(
        artifact_id="launch-email-sequence",
        title="Launch Email Sequence",
        source_skill_id="launch-email-sequence",
        section_id="email-strategy",
        description="Launch-day and launch-window email conversion flow.",
    ),
    "campaign-page-copy": KickstarterArtifact(
        artifact_id="campaign-page-copy",
        title="Campaign Page Copy",
        source_skill_id="campaign-page-copy",
        section_id="campaign-messaging",
        description="Primary campaign page messaging and conversion narrative.",
    ),
    "campaign-video-script": KickstarterArtifact(
        artifact_id="campaign-video-script",
        title="Campaign Video Script",
        source_skill_id="campaign-video-script",
        section_id="campaign-messaging",
        description="Narrative, beats, and CTA framing for the campaign video.",
    ),
    "live-campaign-ads-copy": KickstarterArtifact(
        artifact_id="live-campaign-ads-copy",
        title="Live Campaign Ads Copy",
        source_skill_id="live-campaign-ads",
        section_id="driving-continual-interest",
        description="Live-campaign ad variants used to sustain momentum during the campaign.",
    ),
    "press-release-copy": KickstarterArtifact(
        artifact_id="press-release-copy",
        title="Press Release Copy",
        source_skill_id="press-release-copy",
        section_id="driving-continual-interest",
        description="Launch announcement and media-ready press release narrative.",
    ),
}


MANDATORY_KICKSTARTER_SECTIONS: Dict[str, KickstarterSection] = {
    "market-understanding": KickstarterSection(
        section_id="market-understanding",
        title="Part 1 — Understanding the Market",
        description="Learn the target audience, map buying motivations, and understand competitors well enough to stand out.",
        artifact_ids=("market-buyer-persona", "competitor-summary"),
    ),
    "product-detailing": KickstarterSection(
        section_id="product-detailing",
        title="Part 2 — Product Detailing",
        description="Define the product in detail, articulate positioning, and create the canonical messaging and voice substrate.",
        artifact_ids=(
            "detailed-product-description",
            "product-positioning-summary",
            "mds",
            "voice-and-tone",
        ),
    ),
    "crafting-compelling-copy": KickstarterSection(
        section_id="crafting-compelling-copy",
        title="Part 3 — Crafting Compelling Copy",
        description="Create the conversion-oriented copy that attracts and warms up prospective backers.",
        artifact_ids=("landing-page-copy", "pre-launch-ads-copy"),
    ),
    "email-strategy": KickstarterSection(
        section_id="email-strategy",
        title="Part 4 — Developing a Robust Email Strategy",
        description="Design the lifecycle email flows that nurture prospects into backers.",
        artifact_ids=(
            "welcome-email-sequence",
            "pre-launch-email-sequence",
            "launch-email-sequence",
        ),
    ),
    "campaign-messaging": KickstarterSection(
        section_id="campaign-messaging",
        title="Part 5 — Perfecting the Campaign Messaging",
        description="Create the campaign page and campaign video narrative that inspire confidence and conversions.",
        artifact_ids=("campaign-page-copy", "campaign-video-script"),
    ),
    "driving-continual-interest": KickstarterSection(
        section_id="driving-continual-interest",
        title="Part 6 — Driving Continual Interest",
        description="Maintain campaign momentum through live ads and a launch-ready press release.",
        artifact_ids=("live-campaign-ads-copy", "press-release-copy"),
    ),
}


def iter_section_artifacts(section_id: str) -> Iterable[KickstarterArtifact]:
    """Yield artifact definitions for a section in display order."""
    section = MANDATORY_KICKSTARTER_SECTIONS[section_id]
    for artifact_id in section.artifact_ids:
        yield MANDATORY_KICKSTARTER_ARTIFACTS[artifact_id]



def artifact_ids_for_source_skill(skill_id: str) -> List[str]:
    """Return mandatory Kickstarter artifact IDs backed by a source skill ID."""
    return [
        artifact.artifact_id
        for artifact in MANDATORY_KICKSTARTER_ARTIFACTS.values()
        if artifact.source_skill_id == skill_id
    ]



def section_ids_for_source_skills(skill_ids: Iterable[str]) -> List[str]:
    """Return the ordered mandatory Kickstarter section IDs touched by skill IDs."""
    section_ids: List[str] = []
    seen = set()
    for section_id, section in MANDATORY_KICKSTARTER_SECTIONS.items():
        source_skill_ids = {
            MANDATORY_KICKSTARTER_ARTIFACTS[artifact_id].source_skill_id
            for artifact_id in section.artifact_ids
        }
        if source_skill_ids.intersection(skill_ids) and section_id not in seen:
            seen.add(section_id)
            section_ids.append(section_id)
    return section_ids



def mandatory_source_skill_ids() -> List[str]:
    """Return the unique skill IDs backing mandatory Kickstarter artifacts."""
    seen = []
    for artifact in MANDATORY_KICKSTARTER_ARTIFACTS.values():
        if artifact.source_skill_id not in seen:
            seen.append(artifact.source_skill_id)
    return seen


def build_kickstarter_readiness(skill_outputs: Dict[str, dict]) -> dict:
    """Compute artifact- and section-level readiness from available outputs."""
    artifact_status = {}
    for artifact_id, artifact in MANDATORY_KICKSTARTER_ARTIFACTS.items():
        payload = skill_outputs.get(artifact.source_skill_id)
        artifact_status[artifact_id] = bool(payload)

    section_status = {}
    for section_id, section in MANDATORY_KICKSTARTER_SECTIONS.items():
        statuses = [artifact_status[artifact_id] for artifact_id in section.artifact_ids]
        ready = all(statuses)
        completed = sum(1 for status in statuses if status)
        section_status[section_id] = {
            "ready": ready,
            "completed": completed,
            "total": len(statuses),
            "missing_artifact_ids": [
                artifact_id
                for artifact_id in section.artifact_ids
                if not artifact_status[artifact_id]
            ],
        }

    all_ready = all(row["ready"] for row in section_status.values()) if section_status else False
    return {
        "all_ready": all_ready,
        "artifact_status": artifact_status,
        "section_status": section_status,
    }



def load_mandatory_skill_outputs(outputs_dir: Path) -> Dict[str, dict]:
    """Load the saved outputs backing mandatory Kickstarter artifacts."""
    loaded: Dict[str, dict] = {}
    if not outputs_dir.is_dir():
        return loaded

    for skill_id in mandatory_source_skill_ids():
        output_path = outputs_dir / f"{skill_id}.json"
        if not output_path.is_file():
            continue
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, dict):
            loaded[skill_id] = payload
    return loaded



def build_kickstarter_readiness_from_outputs(outputs_dir: Path) -> dict:
    """Compute Kickstarter readiness directly from a brand's outputs directory."""
    return build_kickstarter_readiness(load_mandatory_skill_outputs(outputs_dir))


def section_doc_stem(section_id: str) -> str:
    """Return the source document stem for a section doc."""
    return f"kickstarter-{section_id}"


def artifact_doc_stem(artifact_id: str) -> str:
    """Return the source document stem for a mandatory artifact doc."""
    return f"artifact-{artifact_id}"


KICKSTARTER_READINESS_DOC_STEM = "kickstarter-readiness"
