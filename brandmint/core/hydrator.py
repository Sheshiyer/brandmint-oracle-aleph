"""
Brandmint -- Auto-hydration bridge.

Maps text skill outputs into brand-config.yaml fields so visual prompts
use the strategy data from earlier waves.

After Wave 2 text skills complete (buyer-persona, product-positioning,
MDS, voice-and-tone), their JSON outputs feed into the brand-config.yaml.
This is the interweave between text and visual workflows.

Usage:
    from brandmint.core.hydrator import hydrate_brand_config, save_hydrated_config

    config = yaml.safe_load(Path("brand-config.yaml").read_text())
    outputs = {
        "voice-and-tone": json.loads(Path(".brandmint/outputs/voice-and-tone.json").read_text()),
        "buyer-persona": json.loads(Path(".brandmint/outputs/buyer-persona.json").read_text()),
    }
    hydrate_brand_config(config, outputs)
    save_hydrated_config(config, Path("brand-config.yaml"))
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict

import yaml


# ---------------------------------------------------------------------------
# Hydration mapping: skill_id -> { config_dot_path: output_dot_path }
# ---------------------------------------------------------------------------

HYDRATION_MAP: Dict[str, Dict[str, str]] = {
    "buyer-persona": {
        "audience.persona_name": "persona.name",
        "audience.aspiration": "persona.aspirations",
        "audience.pain_points": "persona.pain_points",
    },
    "product-positioning-summary": {
        "positioning.statement": "positioning_statement",
        "positioning.pillars": "key_pillars",
    },
    "mds-messaging-direction-summary": {
        "positioning.hero_headline": "hero_headline",
        "positioning.tagline": "tagline",
    },
    "voice-and-tone": {
        "brand.voice": "voice_persona",
        "brand.tone": "tone_calibration",
    },
    "competitor-analysis": {
        "competitive_context.differentiate_from": "key_differentiators",
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_nested(data: dict, dot_path: str) -> Any:
    """Traverse dict using dot-separated path.

    Walks each segment of *dot_path* through nested dicts. Returns ``None``
    when any intermediate key is missing or the current node is not a dict.

    Examples::

        _get_nested({"a": {"b": 1}}, "a.b")   -> 1
        _get_nested({"a": 1}, "a.b.c")         -> None
        _get_nested({}, "x")                    -> None

    Args:
        data: The dict to traverse.
        dot_path: Dot-separated key path (e.g. ``"persona.name"``).

    Returns:
        The value at the path, or ``None`` if not found.
    """
    current: Any = data
    for key in dot_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _set_nested(data: dict, dot_path: str, value: Any) -> None:
    """Set value in dict using dot-separated path.

    Creates intermediate dicts when they do not exist. Overwrites the
    leaf value if one already exists.

    Examples::

        d = {}
        _set_nested(d, "a.b.c", 1)
        # d == {"a": {"b": {"c": 1}}}

    Args:
        data: The dict to mutate.
        dot_path: Dot-separated key path (e.g. ``"audience.persona_name"``).
        value: The value to set at the leaf.
    """
    keys = dot_path.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hydrate_brand_config(config: dict, skill_outputs: Dict[str, dict]) -> dict:
    """Inject text skill outputs into brand config dict.

    For each completed skill in *skill_outputs* that has a
    :data:`HYDRATION_MAP` entry, extract value from the skill output
    using the output dot-path and set it in *config* using the config
    dot-path.

    Missing output fields are silently skipped -- the config field
    retains its original value (no crash on incomplete skill data).

    Args:
        config: Brand config dict (from ``yaml.safe_load``).
                **Modified in place.**
        skill_outputs: ``{skill_id: output_json_dict}`` for completed skills.

    Returns:
        The mutated *config* dict (same reference as input).
    """
    for skill_id, output_data in skill_outputs.items():
        mappings = HYDRATION_MAP.get(skill_id)
        if mappings is None:
            continue

        for config_path, output_path in mappings.items():
            value = _get_nested(output_data, output_path)
            if value is not None:
                _set_nested(config, config_path, value)

    return config


def save_hydrated_config(config: dict, path: Path) -> None:
    """Write hydrated config back to YAML file.

    Creates a backup at ``path.with_suffix('.yaml.bak')`` first if the
    original file exists. Uses ``yaml.dump`` with readable block-style
    formatting.

    Args:
        config: The hydrated config dict to write.
        path: Destination YAML file path.
    """
    path = Path(path)

    # Back up existing file before overwriting
    if path.exists():
        backup_path = path.with_suffix(".yaml.bak")
        shutil.copy2(path, backup_path)

    path.write_text(
        yaml.dump(
            config,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
    )


def get_hydration_status(skill_outputs: Dict[str, dict]) -> Dict[str, bool]:
    """Check which hydration mappings can be applied.

    Returns a dict keyed by every skill ID in :data:`HYDRATION_MAP`,
    with ``True`` if the skill has output data available in
    *skill_outputs*, ``False`` otherwise.

    Args:
        skill_outputs: ``{skill_id: output_json_dict}`` for available skills.

    Returns:
        ``{skill_id: bool}`` for each skill in ``HYDRATION_MAP``.
    """
    return {
        skill_id: skill_id in skill_outputs and bool(skill_outputs[skill_id])
        for skill_id in HYDRATION_MAP
    }
