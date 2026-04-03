#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import subprocess
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from brandmint.config_approval import (
    APPROVAL_ERROR_CODE,
    build_approval_error,
    compose_config_document,
    config_launch_status,
    dump_config_document,
    read_config_document,
    semantic_payload_from_document,
    write_config_document,
)


HOST = "127.0.0.1"
PORT = 4191
FIXED_UI_PORT = 4188


def _detect_root() -> Path:
    explicit = os.environ.get("BRANDMINT_ROOT", "").strip()
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(
        [
            Path(__file__).resolve().parent.parent,
            Path.cwd(),
        ]
    )

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except FileNotFoundError:
            continue
        if (resolved / "pyproject.toml").exists() and (resolved / "brandmint").is_dir():
            return resolved

    return Path(__file__).resolve().parent.parent


ROOT = _detect_root()
ARTIFACT_PATHS = [
    ROOT / ".brandmint" / "outputs",
    ROOT / "deliverables",
    ROOT / ".brandmint",
]
REFERENCE_MAP_PATH = ROOT / "references" / "reference-map.json"
REFERENCE_IMAGE_DIRS = [
    ROOT / "references" / "images",
    ROOT / "references" / "twitter-sync" / "assets",
]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_DOC_PROMPT = (
    "Generate a concise markdown project update with completed tasks, in-progress work, "
    "risks, and next actions."
)
PUBLISH_STAGES = {"notebooklm", "decks", "reports", "diagrams", "video"}
UI_SETTINGS_PATH = ROOT / ".brandmint" / "ui-settings.json"
DEFAULT_UI_SETTINGS = {
    "openrouter": {
        "model": "openai/gpt-4o-mini",
        "routeMode": "balanced",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
    },
    "inference": {
        "endpoint": "https://api.inference.sh",
        "visualBackend": "scripts",
        "rolloutMode": "ring0",
        "fallbackToScripts": True,
        "semanticRoutingEnabled": True,
        "semanticDomainPack": "",
    },
    "nbrain": {
        "enabled": False,
        "model": "nbrain/default",
        "endpoint": "",
    },
    "defaults": {
        "preferredRunner": "bm",
    },
}
SETTINGS_LOCK = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RuntimeState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.process: subprocess.Popen[str] | None = None
        self.run_state = "idle"
        self.runner_id = "bm"
        self.run_started_at: str | None = None
        self.last_command: list[str] = []
        self.log_seq = 0
        self.logs: deque[dict] = deque(maxlen=2000)

    def append_log(self, level: str, message: str) -> None:
        with self.lock:
            self.log_seq += 1
            self.logs.append(
                {
                    "id": self.log_seq,
                    "ts": utc_now(),
                    "level": level,
                    "message": message,
                }
            )

    def snapshot(self) -> dict:
        with self.lock:
            running = bool(self.process and self.process.poll() is None)
            pid = self.process.pid if running and self.process else None
            state = self.run_state
            if not running and state in {"running", "retrying"}:
                state = "idle"
            return {
                "state": state,
                "runner": self.runner_id,
                "pid": pid,
                "running": running,
                "startedAt": self.run_started_at,
                "lastCommand": self.last_command,
                "fixedUiPort": FIXED_UI_PORT,
            }

    def read_logs(self, since: int = 0) -> list[dict]:
        with self.lock:
            return [l for l in self.logs if l["id"] > since]


runtime = RuntimeState()


def _deep_merge_dict(base: dict, incoming: dict) -> dict:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def _default_ui_settings() -> dict:
    return json.loads(json.dumps(DEFAULT_UI_SETTINGS))


def _load_ui_settings() -> dict:
    data = _default_ui_settings()
    if not UI_SETTINGS_PATH.exists():
        return data
    try:
        raw = json.loads(UI_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return data
    if isinstance(raw, dict):
        _deep_merge_dict(data, raw)
    return data


UI_SETTINGS = _load_ui_settings()


def _save_ui_settings() -> None:
    UI_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    UI_SETTINGS_PATH.write_text(json.dumps(UI_SETTINGS, indent=2), encoding="utf-8")


def _mask_secret(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]}"


def get_settings_snapshot() -> dict:
    with SETTINGS_LOCK:
        base = json.loads(json.dumps(UI_SETTINGS))
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    inference_key = os.environ.get("INFERENCE_API_KEY", "").strip()
    nbrain_key = os.environ.get("NBRAIN_API_KEY", "").strip()
    return {
        "openrouter": {
            **base.get("openrouter", {}),
            "hasApiKey": bool(openrouter_key),
            "apiKeyMasked": _mask_secret(openrouter_key),
        },
        "inference": {
            **base.get("inference", {}),
            "hasApiKey": bool(inference_key),
            "apiKeyMasked": _mask_secret(inference_key),
        },
        "nbrain": {
            **base.get("nbrain", {}),
            "hasApiKey": bool(nbrain_key),
            "apiKeyMasked": _mask_secret(nbrain_key),
        },
        "defaults": base.get("defaults", {}),
    }


def update_settings(payload: dict) -> dict:
    with SETTINGS_LOCK:
        openrouter = UI_SETTINGS.setdefault("openrouter", {})
        if "openrouterModel" in payload:
            openrouter["model"] = str(payload.get("openrouterModel") or "openai/gpt-4o-mini").strip()
        if "openrouterRouteMode" in payload:
            openrouter["routeMode"] = str(payload.get("openrouterRouteMode") or "balanced").strip()
        if "openrouterEndpoint" in payload:
            openrouter["endpoint"] = str(payload.get("openrouterEndpoint") or "").strip() or DEFAULT_UI_SETTINGS["openrouter"][
                "endpoint"
            ]

        inference = UI_SETTINGS.setdefault("inference", {})
        if "inferenceEndpoint" in payload:
            inference["endpoint"] = str(payload.get("inferenceEndpoint") or "").strip() or DEFAULT_UI_SETTINGS["inference"][
                "endpoint"
            ]
        if "inferenceVisualBackend" in payload:
            backend = str(payload.get("inferenceVisualBackend") or "scripts").strip().lower()
            inference["visualBackend"] = "inference" if backend == "inference" else "scripts"
        if "inferenceRolloutMode" in payload:
            mode = str(payload.get("inferenceRolloutMode") or "ring0").strip().lower()
            inference["rolloutMode"] = mode if mode in {"ring0", "ring1", "ring2"} else "ring0"
        if "inferenceFallbackToScripts" in payload:
            inference["fallbackToScripts"] = bool(payload.get("inferenceFallbackToScripts"))
        if "inferenceSemanticRoutingEnabled" in payload:
            inference["semanticRoutingEnabled"] = bool(payload.get("inferenceSemanticRoutingEnabled"))
        if "inferenceSemanticDomainPack" in payload:
            inference["semanticDomainPack"] = str(payload.get("inferenceSemanticDomainPack") or "").strip()

        nbrain = UI_SETTINGS.setdefault("nbrain", {})
        if "nbrainEnabled" in payload:
            nbrain["enabled"] = bool(payload.get("nbrainEnabled"))
        if "nbrainModel" in payload:
            nbrain["model"] = str(payload.get("nbrainModel") or "nbrain/default").strip()
        if "nbrainEndpoint" in payload:
            nbrain["endpoint"] = str(payload.get("nbrainEndpoint") or "").strip()

        defaults = UI_SETTINGS.setdefault("defaults", {})
        if "preferredRunner" in payload:
            defaults["preferredRunner"] = str(payload.get("preferredRunner") or "bm").strip().lower()

        _save_ui_settings()

    if "openrouterApiKey" in payload:
        key = str(payload.get("openrouterApiKey") or "").strip()
        if key:
            os.environ["OPENROUTER_API_KEY"] = key
    if payload.get("clearOpenrouterApiKey"):
        os.environ.pop("OPENROUTER_API_KEY", None)

    if "inferenceApiKey" in payload:
        key = str(payload.get("inferenceApiKey") or "").strip()
        if key:
            os.environ["INFERENCE_API_KEY"] = key
    if payload.get("clearInferenceApiKey"):
        os.environ.pop("INFERENCE_API_KEY", None)

    if "nbrainApiKey" in payload:
        key = str(payload.get("nbrainApiKey") or "").strip()
        if key:
            os.environ["NBRAIN_API_KEY"] = key
    if payload.get("clearNbrainApiKey"):
        os.environ.pop("NBRAIN_API_KEY", None)

    return get_settings_snapshot()


def discover_artifacts(limit: int = 200) -> list[dict]:
    rows: list[dict] = []
    seen: set[Path] = set()
    for base in ARTIFACT_PATHS:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p in seen:
                continue
            seen.add(p)
            try:
                stat = p.stat()
            except OSError:
                continue
            rows.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "relativePath": str(p.relative_to(ROOT)),
                    "size": stat.st_size,
                    "modifiedAt": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "extension": p.suffix.lower(),
                    "group": (
                        "outputs"
                        if ".brandmint/outputs" in str(p)
                        else ("deliverables" if "/deliverables/" in str(p) else "state")
                    ),
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [tok for tok in cleaned.split() if len(tok) > 2]


def discover_references(limit: int = 500) -> list[dict]:
    metadata_by_file: dict[str, dict] = {}

    def merge_meta(file_name: str, payload: dict) -> None:
        existing = metadata_by_file.setdefault(
            file_name,
            {
                "tags": set(),
                "sources": set(),
                "description": "",
                "priority": 0,
                "asset_ids": set(),
            },
        )
        existing["tags"].update(payload.get("tags", []))
        existing["sources"].update(payload.get("sources", []))
        if payload.get("description") and not existing["description"]:
            existing["description"] = payload["description"]
        existing["priority"] = max(existing["priority"], payload.get("priority", 0))
        existing["asset_ids"].update(payload.get("asset_ids", []))

    if REFERENCE_MAP_PATH.exists():
        try:
            ref_map = json.loads(REFERENCE_MAP_PATH.read_text(encoding="utf-8"))
        except Exception:
            ref_map = {}

        for asset_id, row in ref_map.get("primary", {}).items():
            file_name = row.get("file")
            if not file_name:
                continue
            tags = _tokenize(row.get("name", "")) + _tokenize(row.get("description", "")) + [asset_id.lower(), "core"]
            merge_meta(
                file_name,
                {
                    "tags": tags,
                    "sources": {"primary"},
                    "description": row.get("description", ""),
                    "priority": 100,
                    "asset_ids": {asset_id},
                },
            )

        for asset_id, row in ref_map.get("reuses", {}).items():
            file_name = row.get("file")
            if not file_name:
                continue
            tags = _tokenize(row.get("name", "")) + _tokenize(row.get("description", "")) + [asset_id.lower(), "reuse"]
            merge_meta(
                file_name,
                {
                    "tags": tags,
                    "sources": {"reuse"},
                    "description": row.get("description", ""),
                    "priority": 90,
                    "asset_ids": {asset_id},
                },
            )

        for asset_id, rows in ref_map.get("alternatives", {}).items():
            for row in rows:
                file_name = row.get("file")
                if not file_name:
                    continue
                tags = _tokenize(row.get("description", "")) + [asset_id.lower(), "alternative"]
                merge_meta(
                    file_name,
                    {
                        "tags": tags,
                        "sources": {"alternative"},
                        "description": row.get("description", ""),
                        "priority": 70,
                        "asset_ids": {asset_id},
                    },
                )

        for row in ref_map.get("styles", []):
            file_name = row.get("file")
            if not file_name:
                continue
            tags = _tokenize(row.get("description", "")) + ["style"]
            merge_meta(
                file_name,
                {
                    "tags": tags,
                    "sources": {"style"},
                    "description": row.get("description", ""),
                    "priority": 65,
                    "asset_ids": set(),
                },
            )

        for row in ref_map.get("demos", []):
            file_name = row.get("file")
            if not file_name:
                continue
            tags = _tokenize(row.get("description", "")) + ["demo"]
            merge_meta(
                file_name,
                {
                    "tags": tags,
                    "sources": {"demo"},
                    "description": row.get("description", ""),
                    "priority": 55,
                    "asset_ids": set(),
                },
            )

        for row in ref_map.get("twitter", []):
            slug = row.get("slug", "")
            base_tags = list(row.get("tags", [])) + _tokenize(slug) + ["twitter", "inspiration"]
            description = f"X reference by @{row.get('author', 'unknown')}"
            if not slug:
                continue
            for img_dir in REFERENCE_IMAGE_DIRS:
                if not img_dir.exists():
                    continue
                for p in img_dir.glob(f"*{slug}*"):
                    if p.suffix.lower() not in IMAGE_SUFFIXES:
                        continue
                    merge_meta(
                        p.name,
                        {
                            "tags": base_tags,
                            "sources": {"twitter"},
                            "description": description,
                            "priority": 75,
                            "asset_ids": set(),
                        },
                    )

    rows: list[dict] = []
    seen: set[Path] = set()
    for base in REFERENCE_IMAGE_DIRS:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in IMAGE_SUFFIXES or p in seen:
                continue
            seen.add(p)
            rel = p.relative_to(ROOT)
            meta = metadata_by_file.get(p.name, {})
            tags = set(meta.get("tags", set()))
            if not tags:
                tags.update(_tokenize(p.stem))
            try:
                stat = p.stat()
            except OSError:
                continue
            rows.append(
                {
                    "id": str(rel).replace("/", "__"),
                    "name": p.name,
                    "relativePath": str(rel),
                    "url": f"/api/reference-image?path={str(rel)}",
                    "description": meta.get("description", ""),
                    "tags": sorted(tags),
                    "sources": sorted(list(meta.get("sources", set()))),
                    "priority": meta.get("priority", 40),
                    "assetIds": sorted(list(meta.get("asset_ids", set()))),
                    "size": stat.st_size,
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def list_listening_pids(port: int) -> list[int]:
    try:
        out = subprocess.check_output(
            ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return []
    if not out:
        return []
    return [int(x) for x in out.splitlines() if x.strip().isdigit()]


def clear_port(port: int) -> bool:
    pids = list_listening_pids(port)
    if not pids:
        return True
    runtime.append_log("warn", f"Clearing stale listeners on port {port}: {pids}")
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(1.0)
    remaining = list_listening_pids(port)
    for pid in remaining:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    time.sleep(0.3)
    return not list_listening_pids(port)


def reader_thread(stream, level: str) -> None:
    for line in iter(stream.readline, ""):
        line = line.rstrip("\n")
        if line:
            runtime.append_log(level, line)
    stream.close()


def get_runner_catalog() -> list[dict]:
    settings = get_settings_snapshot()
    nbrain = settings.get("nbrain", {})
    nbrain_available = bool(nbrain.get("enabled") and nbrain.get("endpoint") and os.environ.get("NBRAIN_API_KEY"))
    return [
        {
            "id": "bm",
            "label": "Brandmint Pipeline",
            "kind": "pipeline",
            "available": shutil.which("bm") is not None,
            "supportsOutputPath": False,
            "requiresPrompt": False,
            "pty": False,
            "description": "Runs bm launch pipeline with waves/scenario.",
        },
        {
            "id": "claude",
            "label": "Claude Code CLI",
            "kind": "agent-cli",
            "available": shutil.which("claude") is not None,
            "supportsOutputPath": True,
            "requiresPrompt": True,
            "pty": True,
            "description": "Runs native Claude Code CLI with PTY wrapper.",
        },
        {
            "id": "codex",
            "label": "Codex CLI",
            "kind": "agent-cli",
            "available": shutil.which("codex") is not None,
            "supportsOutputPath": True,
            "requiresPrompt": True,
            "pty": True,
            "description": "Runs Codex CLI one-shot execution with PTY wrapper.",
        },
        {
            "id": "gemini",
            "label": "Gemini CLI",
            "kind": "agent-cli",
            "available": shutil.which("gemini") is not None,
            "supportsOutputPath": True,
            "requiresPrompt": True,
            "pty": False,
            "description": "Runs Gemini CLI one-shot prompt execution.",
        },
        {
            "id": "openrouter",
            "label": "OpenRouter API",
            "kind": "api",
            "available": bool(os.environ.get("OPENROUTER_API_KEY")),
            "supportsOutputPath": True,
            "requiresPrompt": True,
            "pty": False,
            "description": "Runs OpenRouter chat completion through modular wrapper script.",
        },
        {
            "id": "nbrain",
            "label": "NBrain API",
            "kind": "api",
            "available": nbrain_available,
            "supportsOutputPath": True,
            "requiresPrompt": True,
            "pty": False,
            "description": "Runs NBrain completion through modular wrapper script.",
        },
    ]


def _resolve_output_path(raw: str | None) -> Path | None:
    if not raw:
        return None
    p = Path(str(raw))
    resolved = p if p.is_absolute() else (ROOT / p)
    resolved = resolved.resolve()
    if not str(resolved).startswith(str(ROOT.resolve())):
        raise ValueError("outputPath must be inside repo root")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _resolve_user_path(raw: str | None, expect_dir: bool = False) -> Path:
    if not raw:
        raise ValueError("Path is required")
    p = Path(str(raw).strip())
    resolved = p if p.is_absolute() else (ROOT / p)
    resolved = resolved.resolve()
    if expect_dir and not resolved.is_dir():
        raise ValueError(f"Directory not found: {resolved}")
    return resolved


def _is_within_any(candidate: Path, bases: list[Path]) -> bool:
    for base in bases:
        try:
            candidate.relative_to(base.resolve())
            return True
        except ValueError:
            continue
        except FileNotFoundError:
            continue
    return False


def load_intake_from_folder(payload: dict) -> dict:
    brand_folder = str(payload.get("brandFolder") or "").strip()
    if not brand_folder:
        raise ValueError("brandFolder is required")
    folder = _resolve_user_path(brand_folder, expect_dir=True)

    product_file = str(payload.get("productMdFile") or "product.md").strip() or "product.md"
    config_file = str(payload.get("configFile") or "brand-config.yaml").strip() or "brand-config.yaml"

    product_path = (folder / product_file).resolve()
    config_path = (folder / config_file).resolve()

    warnings: list[str] = []
    product_text = ""
    if product_path.exists() and product_path.is_file():
        try:
            product_text = product_path.read_text(encoding="utf-8")
        except Exception as exc:
            warnings.append(f"Failed reading Product MD: {exc}")
    else:
        warnings.append(f"Product MD not found at {product_path}")

    if not config_path.exists():
        warnings.append(f"Config not found at {config_path}")
        config_document = None
        config_launch = None
    else:
        try:
            config_document = read_config_document(config_path)
            config_launch = config_launch_status(config_document)
        except Exception as exc:
            warnings.append(f"Failed reading config: {exc}")
            config_document = None
            config_launch = None

    runtime.append_log("info", f"Intake loaded from folder: {folder}")
    return {
        "ok": True,
        "brandFolder": str(folder),
        "productMdPath": str(product_path),
        "productMdText": product_text,
        "configPath": str(config_path),
        "configDocument": config_document,
        "semanticConfig": semantic_payload_from_document(config_document) if config_document else None,
        "configMetadata": (config_document or {}).get("_brandmint") if config_document else None,
        "configLaunchStatus": config_launch,
        "warnings": warnings,
    }


def save_config_from_payload(payload: dict) -> dict:
    raw_path = str(payload.get("configPath") or "").strip()
    if not raw_path:
        raise ValueError("configPath is required")
    config_path = _resolve_user_path(raw_path, expect_dir=False)

    semantic_config = payload.get("semanticConfig") or payload.get("configDraft")
    if not isinstance(semantic_config, dict):
        raise ValueError("semanticConfig is required")

    review = payload.get("review") or {}
    approved = bool(payload.get("approved"))
    pending_fields = review.get("pendingFields") or review.get("pending_fields") or []
    if approved and pending_fields:
        preview = ", ".join(str(item) for item in pending_fields[:3])
        raise ValueError(
            f"Config cannot be approved while fields still need review: {preview or 'pending fields remain'}"
        )

    existing_document = None
    if config_path.exists() and config_path.is_file():
        try:
            existing_document = read_config_document(config_path)
        except Exception:
            existing_document = None

    document = compose_config_document(
        semantic_config,
        review=review,
        source_text=str(payload.get("sourceText") or ""),
        source_uri=str(payload.get("sourceUri") or payload.get("productMdPath") or ""),
        source_type=str(payload.get("sourceType") or "product-md"),
        extractor_version=str(payload.get("extractorVersion") or "front-ui-v1"),
        state="approved" if approved else "draft",
        approved_by=str(payload.get("approvedBy") or ""),
        approval_note=str(payload.get("approvalNote") or ""),
        existing_document=existing_document,
    )
    write_config_document(config_path, document)
    launch_status = config_launch_status(document)
    runtime.append_log(
        "info",
        f"Config saved to {config_path} ({launch_status['state']}, pending={len(launch_status['pending_fields'])})",
    )
    return {
        "ok": True,
        "configPath": str(config_path),
        "yaml": dump_config_document(document),
        "document": document,
        "semanticConfig": semantic_payload_from_document(document),
        "configMetadata": document.get("_brandmint"),
        "configLaunchStatus": launch_status,
    }


def _build_runner_command(payload: dict, retry: bool) -> tuple[str, list[str]]:
    runner_id = str(payload.get("runner") or "bm").strip().lower()
    runner_map = {row["id"]: row for row in get_runner_catalog()}
    runner = runner_map.get(runner_id)
    settings = get_settings_snapshot()
    if not runner:
        raise ValueError(f"Unknown runner '{runner_id}'")
    if not runner.get("available"):
        raise ValueError(f"Runner '{runner_id}' is not available in this environment")

    if runner_id == "bm":
        config = payload.get("configPath") or "./brand-config.yaml"
        config_path = _resolve_user_path(str(config), expect_dir=False)
        if not config_path.exists():
            raise ValueError(f"Config file not found: {config_path}")
        config_document = read_config_document(config_path)
        launch_status = config_launch_status(config_document)
        if not launch_status["is_launchable"]:
            raise ValueError(build_approval_error(config_path, launch_status.get("pending_fields")))
        scenario = payload.get("scenario") or "focused"
        waves = payload.get("waves") or "1-3"
        inference = settings.get("inference", {})
        if retry:
            runtime.append_log("info", "Retry requested: clearing fixed UI port 4188")
            if not clear_port(FIXED_UI_PORT):
                raise RuntimeError(f"Failed to clear port {FIXED_UI_PORT}")
        cmd = [
            "bm",
            "launch",
            "--config",
            str(config_path),
            "--scenario",
            str(scenario),
            "--waves",
            str(waves),
            "--non-interactive",
        ]
        if str(inference.get("visualBackend", "scripts")).strip().lower() == "inference":
            cmd.append("--inference-only-visual")
        rollout_mode = str(inference.get("rolloutMode", "ring0")).strip().lower()
        if rollout_mode in {"ring0", "ring1", "ring2"}:
            cmd.extend(["--inference-rollout-mode", rollout_mode])
        return runner_id, cmd

    prompt = str(payload.get("taskPrompt") or DEFAULT_DOC_PROMPT).strip()
    if not prompt:
        raise ValueError("taskPrompt is required for selected runner")
    output_path = _resolve_output_path(payload.get("outputPath"))

    if runner_id == "claude":
        base_cmd = f"claude {shlex.quote(prompt)}"
    elif runner_id == "codex":
        base_cmd = f"codex exec {shlex.quote(prompt)}"
    elif runner_id == "gemini":
        base_cmd = f"gemini {shlex.quote(prompt)}"
    elif runner_id == "openrouter":
        model = str(payload.get("model") or settings.get("openrouter", {}).get("model") or "openai/gpt-4o-mini")
        endpoint = str(payload.get("endpoint") or settings.get("openrouter", {}).get("endpoint") or "").strip()
        cmd = [
            "python3",
            "scripts/openrouter_runner.py",
            "--prompt",
            prompt,
            "--model",
            model,
        ]
        if endpoint:
            cmd.extend(["--endpoint", endpoint])
        if output_path:
            cmd.extend(["--output", str(output_path)])
        return runner_id, cmd
    elif runner_id == "nbrain":
        model = str(payload.get("model") or settings.get("nbrain", {}).get("model") or "nbrain/default")
        endpoint = str(payload.get("endpoint") or settings.get("nbrain", {}).get("endpoint") or "").strip()
        if not endpoint:
            raise ValueError("NBrain endpoint is required. Configure it in Provider Settings.")
        cmd = [
            "python3",
            "scripts/nbrain_runner.py",
            "--prompt",
            prompt,
            "--model",
            model,
            "--endpoint",
            endpoint,
        ]
        if output_path:
            cmd.extend(["--output", str(output_path)])
        return runner_id, cmd
    else:
        raise ValueError(f"Unsupported runner '{runner_id}'")

    shell_cmd = base_cmd
    if output_path:
        shell_cmd = f"{shell_cmd} | tee {shlex.quote(str(output_path))}"

    if runner.get("pty"):
        return runner_id, ["script", "-q", "/dev/null", "bash", "-lc", shell_cmd]
    return runner_id, ["bash", "-lc", shell_cmd]


def _start_process_with_command(cmd: list[str], runner_id: str, retry: bool = False) -> dict:
    runtime.append_log("info", f"Runner[{runner_id}] starting: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    threading.Thread(target=reader_thread, args=(proc.stdout, "info"), daemon=True).start()
    threading.Thread(target=reader_thread, args=(proc.stderr, "error"), daemon=True).start()

    with runtime.lock:
        runtime.process = proc
        runtime.runner_id = runner_id
        runtime.run_state = "retrying" if retry else "running"
        runtime.run_started_at = utc_now()
        runtime.last_command = cmd

    return {"ok": True, "pid": proc.pid, "state": runtime.run_state, "runner": runner_id}


def start_run(payload: dict, retry: bool = False) -> dict:
    with runtime.lock:
        if runtime.process and runtime.process.poll() is None:
            return {"ok": False, "error": "Process already running"}

    try:
        runner_id, cmd = _build_runner_command(payload, retry=retry)
    except Exception as exc:
        message = str(exc)
        code = APPROVAL_ERROR_CODE if "not approved" in message.lower() else "run_start_failed"
        return {"ok": False, "error": message, "code": code}

    return _start_process_with_command(cmd, runner_id=runner_id, retry=retry)


def start_publish(payload: dict) -> dict:
    with runtime.lock:
        if runtime.process and runtime.process.poll() is None:
            return {"ok": False, "error": "Process already running"}

    stage = str(payload.get("stage") or "").strip().lower()
    if stage not in PUBLISH_STAGES:
        return {"ok": False, "error": f"Invalid publish stage '{stage}'. Use one of: {', '.join(sorted(PUBLISH_STAGES))}"}

    config = str(payload.get("configPath") or "./brand-config.yaml").strip()
    cmd = ["bm", "publish", stage, "--config", config]
    return _start_process_with_command(cmd, runner_id=f"publish:{stage}", retry=False)


def abort_run() -> dict:
    with runtime.lock:
        proc = runtime.process
    if not proc or proc.poll() is not None:
        runtime.run_state = "aborted"
        return {"ok": True, "message": "No active process"}

    runtime.append_log("warn", f"Aborting process pid={proc.pid}")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    with runtime.lock:
        runtime.run_state = "aborted"
    return {"ok": True, "message": "Process aborted"}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, data: object) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path) -> None:
        suffix = file_path.suffix.lower()
        mime = "application/octet-stream"
        if suffix in {".jpg", ".jpeg"}:
            mime = "image/jpeg"
        elif suffix == ".png":
            mime = "image/png"
        elif suffix == ".webp":
            mime = "image/webp"
        payload = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send(200, {"ok": True, "service": "ui-backend-bridge", "time": utc_now()})
            return
        if parsed.path == "/api/state":
            self._send(200, runtime.snapshot())
            return
        if parsed.path == "/api/runners":
            self._send(200, {"runners": get_runner_catalog()})
            return
        if parsed.path == "/api/settings":
            self._send(200, {"settings": get_settings_snapshot()})
            return
        if parsed.path == "/api/logs":
            qs = parse_qs(parsed.query)
            since = int(qs.get("since", ["0"])[0])
            self._send(200, {"logs": runtime.read_logs(since)})
            return
        if parsed.path == "/api/artifacts":
            qs = parse_qs(parsed.query)
            limit = int(qs.get("limit", ["200"])[0])
            self._send(200, {"artifacts": discover_artifacts(limit=min(max(limit, 1), 2000))})
            return
        if parsed.path == "/api/artifacts/read":
            qs = parse_qs(parsed.query)
            rel = unquote(qs.get("path", [""])[0]).strip()
            if not rel:
                self._send(400, {"ok": False, "error": "Missing path"})
                return
            candidate = (ROOT / rel).resolve()
            if not _is_within_any(candidate, ARTIFACT_PATHS) or not candidate.exists() or not candidate.is_file():
                self._send(404, {"ok": False, "error": "Artifact not found"})
                return
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self._send(400, {"ok": False, "error": f"Artifact is not valid JSON: {exc}"})
                return
            except Exception as exc:
                self._send(500, {"ok": False, "error": f"Failed to read artifact: {exc}"})
                return
            self._send(200, payload)
            return
        if parsed.path == "/api/references":
            qs = parse_qs(parsed.query)
            limit = int(qs.get("limit", ["500"])[0])
            self._send(200, {"references": discover_references(limit=min(max(limit, 1), 2000))})
            return
        if parsed.path == "/api/reference-image":
            qs = parse_qs(parsed.query)
            rel = unquote(qs.get("path", [""])[0]).strip()
            if not rel:
                self._send(400, {"ok": False, "error": "Missing path"})
                return
            candidate = (ROOT / rel).resolve()
            if not _is_within_any(candidate, REFERENCE_IMAGE_DIRS) or not candidate.exists() or not candidate.is_file():
                self._send(404, {"ok": False, "error": "Image not found"})
                return
            self._send_file(candidate)
            return
        self._send(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        payload = {}
        if length:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))

        if parsed.path == "/api/run/start":
            result = start_run(payload, retry=False)
            self._send(200 if result.get("ok") else 400, result)
            return
        if parsed.path == "/api/run/retry":
            result = start_run(payload, retry=True)
            self._send(200 if result.get("ok") else 400, result)
            return
        if parsed.path == "/api/run/abort":
            result = abort_run()
            self._send(200, result)
            return
        if parsed.path == "/api/publish/start":
            result = start_publish(payload)
            self._send(200 if result.get("ok") else 400, result)
            return
        if parsed.path == "/api/intake/load":
            try:
                result = load_intake_from_folder(payload)
            except Exception as exc:
                self._send(400, {"ok": False, "error": str(exc)})
                return
            self._send(200, result)
            return
        if parsed.path == "/api/settings":
            try:
                settings = update_settings(payload)
            except Exception as exc:
                self._send(400, {"ok": False, "error": str(exc)})
                return
            self._send(200, {"ok": True, "settings": settings})
            return
        if parsed.path == "/api/config/save":
            try:
                result = save_config_from_payload(payload)
            except Exception as exc:
                message = str(exc)
                code = APPROVAL_ERROR_CODE if "approve" in message.lower() or "pending" in message.lower() else "config_save_failed"
                self._send(400, {"ok": False, "error": message, "code": code})
                return
            self._send(200, result)
            return
        self._send(404, {"ok": False, "error": "Not found"})


def main() -> None:
    runtime.append_log("info", f"UI backend bridge online at http://{HOST}:{PORT}")
    runtime.append_log("info", f"Fixed UI port policy is locked to {FIXED_UI_PORT}")
    runtime.append_log("info", f"Settings path: {UI_SETTINGS_PATH}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
