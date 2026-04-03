"""Brandmint CLI — Inference utilities."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import yaml
from rich.console import Console
from rich.table import Table

from ..pipeline.inference_runbook import collect_failed_assets, load_runbook
from ..pipeline.visual_backend import (
    InferenceScaffoldExecutionBackend,
    SubprocessVisualExecutionBackend,
)

console = Console()
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALLOWLIST_PATH = REPO_ROOT / "skills" / "external" / "inference-sh" / "normalized" / "allowlist.yaml"
DEFAULT_SEMANTIC_RULES_PATH = REPO_ROOT / "config" / "inference-semantic-routing.v1.yaml"
DEFAULT_PACK_ROOT = REPO_ROOT / "skills" / "external" / "inference-sh" / "normalized"
SUPPORTED_ROLLOUT_MODES = {"ring0", "ring1", "ring2"}


def _load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config YAML must be a mapping")
    return data


def _resolve_brand_dir(config_path: Path) -> Path:
    parent = config_path.resolve().parent
    if parent.parent.name == "brands":
        return parent
    return parent


def _resolve_path(raw: str, *, base: Path, fallback: Path) -> Path:
    if not raw:
        return fallback
    p = Path(raw).expanduser()
    if p.is_absolute():
        return p
    from_base = (base / p).resolve()
    if from_base.exists():
        return from_base
    return (REPO_ROOT / p).resolve()


def _status_rank(value: str) -> int:
    return {"pass": 0, "warn": 1, "fail": 2}.get(value, 2)


def _run_pack_validator() -> tuple[str, str]:
    validator = REPO_ROOT / "scripts" / "validate_skill_pack.py"
    cmd = [sys.executable, str(validator), "--pack-root", str(DEFAULT_PACK_ROOT)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    status = "pass" if proc.returncode == 0 else "fail"
    detail = (proc.stdout or proc.stderr or "").strip().splitlines()
    brief = detail[-1] if detail else ""
    return status, brief


def run_doctor(config: Path, strict: bool = False, json_output: bool = False) -> int:
    checks: List[Dict[str, str]] = []

    try:
        cfg = _load_config(config)
    except Exception as exc:
        checks.append({"name": "config", "status": "fail", "value": str(config), "detail": str(exc)})
        if json_output:
            console.print_json(json.dumps({"checks": checks}))
        else:
            table = Table(title="Inference Doctor")
            table.add_column("Check")
            table.add_column("Status")
            table.add_column("Detail")
            for row in checks:
                table.add_row(row["name"], row["status"], row["detail"])
            console.print(table)
        return 1

    generation = cfg.get("generation", {}) if isinstance(cfg, dict) else {}
    policy = generation.get("inference_skill_policy", {})
    if not isinstance(policy, Mapping):
        policy = {}
    semantic = policy.get("semantic_routing", {})
    if not isinstance(semantic, Mapping):
        semantic = {}

    checks.append(
        {
            "name": "visual_backend",
            "status": "pass" if str(generation.get("visual_backend", "scripts")).strip().lower() == "inference" else "warn",
            "value": str(generation.get("visual_backend", "scripts")),
            "detail": "set generation.visual_backend=inference to use scaffold backend",
        }
    )

    endpoint = str(generation.get("inference_endpoint", "")).strip() or "https://api.inference.sh"
    checks.append(
        {
            "name": "inference_endpoint",
            "status": "pass" if endpoint else "fail",
            "value": endpoint or "-",
            "detail": "",
        }
    )

    api_key = (
        str(generation.get("inference_api_key", "")).strip()
        or str(generation.get("inferenceApiKey", "")).strip()
        or str(os.environ.get("INFERENCE_API_KEY", "")).strip()
    )
    checks.append(
        {
            "name": "inference_api_key",
            "status": "pass" if api_key else "warn",
            "value": "configured" if api_key else "missing",
            "detail": "set INFERENCE_API_KEY for authenticated execution",
        }
    )

    rollout_mode = str(generation.get("inference_rollout_mode", "ring0")).strip().lower() or "ring0"
    checks.append(
        {
            "name": "rollout_mode",
            "status": "pass" if rollout_mode in SUPPORTED_ROLLOUT_MODES else "fail",
            "value": rollout_mode,
            "detail": "supported: ring0|ring1|ring2",
        }
    )

    allowlist_path = _resolve_path(
        str(policy.get("allowlist_file", "")).strip(),
        base=config.resolve().parent,
        fallback=DEFAULT_ALLOWLIST_PATH,
    )
    checks.append(
        {
            "name": "allowlist_file",
            "status": "pass" if allowlist_path.exists() else "fail",
            "value": str(allowlist_path),
            "detail": "",
        }
    )

    rules_path = _resolve_path(
        str(semantic.get("rules_file", "")).strip(),
        base=config.resolve().parent,
        fallback=DEFAULT_SEMANTIC_RULES_PATH,
    )
    checks.append(
        {
            "name": "semantic_rules_file",
            "status": "pass" if rules_path.exists() else "fail",
            "value": str(rules_path),
            "detail": "",
        }
    )

    pack_ok = DEFAULT_PACK_ROOT.exists()
    checks.append(
        {
            "name": "normalized_pack_root",
            "status": "pass" if pack_ok else "fail",
            "value": str(DEFAULT_PACK_ROOT),
            "detail": "",
        }
    )

    if pack_ok:
        validator_status, validator_detail = _run_pack_validator()
    else:
        validator_status, validator_detail = "fail", "normalized pack root missing"
    checks.append(
        {
            "name": "normalized_pack_validation",
            "status": validator_status,
            "value": validator_detail or "-",
            "detail": "",
        }
    )

    # Route sanity checks
    cfg_for_preview = json.loads(json.dumps(cfg))
    cfg_for_preview.setdefault("generation", {})
    cfg_for_preview["generation"]["visual_backend"] = "inference"
    backend = InferenceScaffoldExecutionBackend(config=cfg_for_preview, brand_dir=_resolve_brand_dir(config))
    route_samples = [
        backend.preview_asset_route(asset_id="APP-SCREENSHOT", batch_name="products"),
        backend.preview_asset_route(asset_id="3A", batch_name="products"),
    ]
    screenshot_route = route_samples[0].get("media_skill_id")
    checks.append(
        {
            "name": "route_sanity_app_screenshot",
            "status": "pass" if screenshot_route == "infsh-agentic-browser" else "warn",
            "value": str(screenshot_route),
            "detail": "expected infsh-agentic-browser for APP-SCREENSHOT",
        }
    )

    highest = max((_status_rank(row["status"]) for row in checks), default=0)
    has_warn = any(row["status"] == "warn" for row in checks)

    if json_output:
        console.print_json(
            json.dumps(
                {
                    "config": str(config),
                    "strict": strict,
                    "checks": checks,
                    "route_samples": route_samples,
                }
            )
        )
    else:
        table = Table(title="Inference Doctor", show_header=True, header_style="bold cyan")
        table.add_column("Check")
        table.add_column("Status")
        table.add_column("Value", style="dim")
        table.add_column("Detail")
        for row in checks:
            color = {"pass": "green", "warn": "yellow", "fail": "red"}.get(row["status"], "white")
            table.add_row(row["name"], f"[{color}]{row['status']}[/{color}]", row["value"], row["detail"])
        console.print(table)

    if highest >= 2:
        return 1
    if strict and has_warn:
        return 1
    return 0


def run_route_test(config: Path, batch: str, assets: str, json_output: bool = False) -> int:
    cfg = _load_config(config)
    cfg_for_preview = json.loads(json.dumps(cfg))
    cfg_for_preview.setdefault("generation", {})
    cfg_for_preview["generation"]["visual_backend"] = "inference"

    backend = InferenceScaffoldExecutionBackend(config=cfg_for_preview, brand_dir=_resolve_brand_dir(config))
    asset_ids = [item.strip() for item in assets.split(",") if item.strip()]
    rows = [backend.preview_asset_route(asset_id=aid, batch_name=batch) for aid in asset_ids]

    if json_output:
        console.print_json(json.dumps({"batch": batch, "assets": rows}))
        return 0

    table = Table(title=f"Semantic Route Test ({batch})", show_header=True, header_style="bold cyan")
    table.add_column("Asset", style="cyan")
    table.add_column("Media Skill")
    table.add_column("Reason")
    table.add_column("Confidence")
    for row in rows:
        routing = row.get("routing", {})
        table.add_row(
            str(row.get("asset_id", "")),
            str(row.get("media_skill_id", "")),
            str(routing.get("reason", "")),
            str(routing.get("confidence", "")),
        )
    console.print(table)
    return 0


def _batch_backend_for_rerun(
    *,
    cfg: Dict[str, Any],
    brand_dir: Path,
    recommendation: str,
    override: Optional[str],
):
    backend_name = (override or recommendation or "scripts").strip().lower()
    if backend_name in {"inference", "inference_scaffold", "inference-scaffold"}:
        cfg_copy = json.loads(json.dumps(cfg))
        cfg_copy.setdefault("generation", {})
        cfg_copy["generation"]["visual_backend"] = "inference"
        return "inference", InferenceScaffoldExecutionBackend(config=cfg_copy, brand_dir=brand_dir)
    return "scripts", SubprocessVisualExecutionBackend()


def run_rerun_failed(config: Path, runbook: Path, backend_override: Optional[str] = None) -> int:
    cfg = _load_config(config)
    data = load_runbook(runbook)
    failed_by_batch, failed_count = collect_failed_assets(data)
    if failed_count == 0:
        console.print("[green]No failed assets found in runbook.[/green]")
        return 0

    # Determine per-batch recommendation from first failed asset.
    recommendations: Dict[str, str] = {}
    for asset in data.get("assets", []):
        if not isinstance(asset, Mapping):
            continue
        status = str(asset.get("status", "")).strip().lower()
        errors = asset.get("validation_errors", [])
        if status not in {"failed", "failed_validation", "validation_failed"} and not errors:
            continue
        batch = str(asset.get("batch_type", "misc"))
        rec = str((asset.get("execution_plan") or {}).get("recommended_backend", "scripts")).strip().lower()
        recommendations.setdefault(batch, rec or "scripts")

    script_path = REPO_ROOT / "scripts" / "run_pipeline.py"
    timeout_seconds = max(60, int(cfg.get("generation", {}).get("batch_timeout_seconds", 1200)))
    brand_dir = _resolve_brand_dir(config)
    had_failures = False

    table = Table(title="Rerun Failed Assets", show_header=True, header_style="bold cyan")
    table.add_column("Batch", style="cyan")
    table.add_column("Assets")
    table.add_column("Backend")
    table.add_column("Result")

    for batch, asset_ids in sorted(failed_by_batch.items()):
        rec = recommendations.get(batch, "scripts")
        backend_name, backend = _batch_backend_for_rerun(
            cfg=cfg,
            brand_dir=brand_dir,
            recommendation=rec,
            override=backend_override,
        )
        result = backend.run_batch(
            script_path=script_path,
            config_path=config.resolve(),
            batch_name=batch,
            asset_ids=asset_ids,
            timeout_seconds=timeout_seconds,
        )
        ok = result.returncode == 0
        had_failures = had_failures or not ok
        table.add_row(
            batch,
            ",".join(asset_ids),
            backend_name,
            "[green]ok[/green]" if ok else f"[red]failed ({result.returncode})[/red]",
        )

    console.print(table)
    return 1 if had_failures else 0
