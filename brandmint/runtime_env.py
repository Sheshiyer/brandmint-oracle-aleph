"""Helpers for loading Brandmint runtime environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping, Optional

from dotenv import load_dotenv


def default_codex_env_file() -> Path:
    """Return the default Codex-local dotenv path."""
    codex_home = str(os.environ.get("CODEX_HOME", "")).strip()
    if codex_home:
        return Path(codex_home).expanduser() / ".env"
    return Path.home() / ".codex" / ".env"


def default_codex_env_string() -> str:
    """Return the default Codex-local dotenv path as a config-friendly string."""
    codex_home = str(os.environ.get("CODEX_HOME", "")).strip()
    if codex_home:
        return str((Path(codex_home).expanduser() / ".env").as_posix())
    return "~/.codex/.env"


def resolve_runtime_env_file(config: Optional[Mapping[str, Any]] = None) -> Path:
    """Resolve the Brandmint runtime dotenv file path.

    Priority:
    1. `generation.env_file` from the active config
    2. `BRANDMINT_ENV_FILE`
    3. `CODEX_ENV_FILE`
    4. Default Codex-local env file (`$CODEX_HOME/.env` or `~/.codex/.env`)
    """
    configured_env = ""
    if isinstance(config, Mapping):
        generation = config.get("generation", {})
        if isinstance(generation, Mapping):
            configured_env = str(generation.get("env_file", "")).strip()

    candidate = (
        configured_env
        or str(os.environ.get("BRANDMINT_ENV_FILE", "")).strip()
        or str(os.environ.get("CODEX_ENV_FILE", "")).strip()
        or default_codex_env_string()
    )
    return Path(os.path.expanduser(candidate))


def load_runtime_env(
    config: Optional[Mapping[str, Any]] = None,
    *,
    override: bool = False,
) -> Optional[Path]:
    """Load Brandmint runtime environment variables if a dotenv file exists.

    Existing process environment variables always win unless `override=True`.
    Returns the loaded path when a dotenv file exists, otherwise `None`.
    """
    env_path = resolve_runtime_env_file(config)
    if not env_path.exists():
        return None
    load_dotenv(env_path, override=override)
    return env_path
