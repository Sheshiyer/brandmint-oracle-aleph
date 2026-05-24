"""Config normalization helpers for NotebookLM publishing.

Canonical config path is ``publishing.notebooklm``.
Legacy paths remain supported with deterministic precedence and warnings.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def resolve_notebooklm_config(config: dict) -> Dict[str, Any]:
    """Return merged NotebookLM config with canonical precedence.

    Merge order:
    1) legacy top-level ``notebooklm``
    2) canonical ``publishing.notebooklm`` (overrides legacy)
    """
    resolved: Dict[str, Any] = {}

    legacy = config.get("notebooklm", {})
    if isinstance(legacy, dict):
        resolved.update(legacy)

    publishing = config.get("publishing", {})
    nested = publishing.get("notebooklm", {}) if isinstance(publishing, dict) else {}
    if isinstance(nested, dict):
        resolved.update(nested)

    return resolved


def notebooklm_config_warnings(config: dict) -> List[str]:
    """Return migration/deprecation warnings for NotebookLM config usage."""
    warnings: List[str] = []

    has_legacy = isinstance(config.get("notebooklm"), dict) and bool(config.get("notebooklm"))
    publishing = config.get("publishing", {})
    has_nested = (
        isinstance(publishing, dict)
        and isinstance(publishing.get("notebooklm"), dict)
        and bool(publishing.get("notebooklm"))
    )

    if has_legacy and has_nested:
        warnings.append(
            "NotebookLM config found in both `notebooklm` (legacy) and "
            "`publishing.notebooklm` (canonical). Canonical values are used."
        )
    elif has_legacy:
        warnings.append(
            "Top-level `notebooklm` config is deprecated. Move keys under "
            "`publishing.notebooklm`."
        )

    if isinstance(publishing, dict):
        legacy_pub_keys = []
        for key in ("synthesize", "synthesis_model"):
            if key in publishing:
                legacy_pub_keys.append(key)
        if legacy_pub_keys:
            warnings.append(
                "Publishing synthesis keys at `publishing.{synthesize,synthesis_model}` "
                "are legacy. Prefer `publishing.notebooklm.{synthesize,synthesis_model}`."
            )

    return warnings


def resolve_synthesis_settings(config: dict) -> Tuple[bool, str]:
    """Resolve synthesis settings with nested canonical precedence.

    Canonical path:
      - publishing.notebooklm.synthesize
      - publishing.notebooklm.synthesis_model

    Legacy fallback path:
      - publishing.synthesize
      - publishing.synthesis_model
    """
    publishing = config.get("publishing", {})
    if not isinstance(publishing, dict):
        return True, ""

    nested = publishing.get("notebooklm", {})
    if not isinstance(nested, dict):
        nested = {}

    synthesize = nested.get("synthesize", publishing.get("synthesize", True))
    synthesis_model = nested.get("synthesis_model", publishing.get("synthesis_model", ""))

    return bool(synthesize), str(synthesis_model or "")
