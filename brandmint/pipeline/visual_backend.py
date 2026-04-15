"""
Visual execution backends for Brandmint pipeline.

This module separates *how* a visual batch is executed from WaveExecutor's
state/report orchestration logic.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol

import yaml
from rich.console import Console

from ..core.providers import ProviderFallbackChain


_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASSET_REGISTRY_PATH = _REPO_ROOT / "assets" / "asset-registry.yaml"
_INFSH_SKILLS_ROOT = _REPO_ROOT / "skills" / "external" / "inference-sh" / "normalized"
_INFSH_ALLOWLIST_PATH = _INFSH_SKILLS_ROOT / "allowlist.yaml"
_SEMANTIC_RULES_PATH = _REPO_ROOT / "config" / "inference-semantic-routing.v1.yaml"
_SUPPORTED_SCAFFOLD_SKILL_IDS = {"infsh-llm-models"}
_SUPPORTED_MEDIA_SKILL_IDS = {
    "infsh-ai-image-generation",
    "infsh-agentic-browser",
}
_SUPPORTED_FALLBACK_PROVIDERS = {
    "fal",
    "replicate",
    "openrouter",
    "openai",
    "inference",
}
_SUPPORTED_ROLLOUT_MODES = {"ring0", "ring1", "ring2"}
_SCAFFOLD_SCHEMA_REQUIRED_KEYS = {
    "schema_version",
    "asset_id",
    "asset_name",
    "batch_type",
    "prompt_key",
    "skills",
    "agent_prompt",
    "media_input",
    "expected_outputs",
    "routing",
    "execution_plan",
    "prompt_lineage",
}


def _normalize_skill_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class VisualExecutionBackend(Protocol):
    """Backend interface used by WaveExecutor for visual batch execution."""

    name: str
    requires_script_path: bool

    def run_batch(
        self,
        *,
        script_path: Path,
        config_path: Path,
        batch_name: str,
        asset_ids: List[str],
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a visual batch."""


class SubprocessVisualExecutionBackend:
    """Current default backend: call scripts/run_pipeline.py execute."""

    name = "scripts"
    requires_script_path = True

    def __init__(
        self,
        python_executable: Optional[str] = None,
        *,
        config: Optional[Dict[str, Any]] = None,
        console: Optional[Console] = None,
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.config = config or {}
        self.console = console
        self._last_batch_metadata: Dict[str, Dict[str, Any]] = {}
        generation = self.config.get("generation", {}) if isinstance(self.config, dict) else {}
        configured_order = _validate_fallback_order(generation.get("fallback_order"))
        self._fallback_chain = ProviderFallbackChain(
            self.config,
            fallback_order=configured_order or None,
        )
        self._configured_fallback_order = (
            configured_order
            or [provider.value for provider in self._fallback_chain.fallback_order]
        )

    def run_batch(
        self,
        *,
        script_path: Path,
        config_path: Path,
        batch_name: str,
        asset_ids: List[str],
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        cmd = [
            self.python_executable,
            str(script_path),
            "execute",
            "--config",
            str(config_path),
            "--batch",
            batch_name,
        ]
        provider_order = self._resolve_provider_attempt_order()
        attempts: List[Dict[str, Any]] = []
        final_result: Optional[subprocess.CompletedProcess[str]] = None

        for provider_id in provider_order:
            env = os.environ.copy()
            env["IMAGE_PROVIDER"] = provider_id

            started = time.monotonic()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
            )
            attempt_duration = round(time.monotonic() - started, 3)
            attempts.append(
                {
                    "provider": provider_id,
                    "returncode": result.returncode,
                    "duration_seconds": attempt_duration,
                }
            )
            final_result = result
            if result.returncode == 0:
                break

        if final_result is None:
            final_result = subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")

        successful_provider = next(
            (entry["provider"] for entry in attempts if entry["returncode"] == 0),
            None,
        )
        providers_tried = [entry["provider"] for entry in attempts]
        summary = {
            "batch_name": batch_name,
            "asset_ids": list(asset_ids),
            "configured_fallback_order": list(self._configured_fallback_order),
            "providers_tried": providers_tried,
            "successful_provider": successful_provider,
            "attempt_count": len(attempts),
            "fallback_used": len(attempts) > 1,
            "attempts": attempts,
        }
        self._last_batch_metadata[batch_name] = summary

        if self.console and len(attempts) > 1:
            self.console.print(
                f"  [yellow]Provider fallback used for batch '{batch_name}': "
                f"{' -> '.join(providers_tried)} "
                f"(selected: {successful_provider or 'none'})[/yellow]"
            )

        stdout = final_result.stdout or ""
        fallback_summary = (
            f"provider_fallback attempts={summary['attempt_count']} "
            f"providers={','.join(providers_tried)} "
            f"selected={successful_provider or 'none'}"
        )
        stdout = (stdout.rstrip() + ("\n" if stdout else "") + fallback_summary).strip()

        return subprocess.CompletedProcess(
            args=final_result.args,
            returncode=final_result.returncode,
            stdout=stdout,
            stderr=final_result.stderr,
        )

    def _resolve_provider_attempt_order(self) -> List[str]:
        providers = self._fallback_chain._get_available_providers(require_image_reference=False)
        ordered: List[str] = []
        for provider in providers:
            provider_name = getattr(getattr(provider, "name", None), "value", "")
            provider_name = str(provider_name).strip().lower()
            if provider_name and provider_name not in ordered:
                ordered.append(provider_name)

        if ordered:
            return ordered

        generation = self.config.get("generation", {}) if isinstance(self.config, dict) else {}
        primary = str(generation.get("provider", "fal")).strip().lower() or "fal"
        fallback = list(self._configured_fallback_order)
        if primary not in fallback:
            fallback.insert(0, primary)
        return fallback or ["fal"]

    def get_batch_routing_summary(self, batch_name: str) -> List[Dict[str, Any]]:
        """Expose provider fallback metadata to execution reports."""
        meta = self._last_batch_metadata.get(batch_name, {})
        if not meta:
            return []
        provider_used = meta.get("successful_provider") or ""
        providers_tried = meta.get("providers_tried", [])
        fallback_order = meta.get("configured_fallback_order", [])
        fallback_summary = {
            "attempt_count": meta.get("attempt_count", 0),
            "providers_tried": providers_tried,
            "successful_provider": provider_used or None,
            "fallback_used": bool(meta.get("fallback_used")),
        }
        rows: List[Dict[str, Any]] = []
        for asset_id in meta.get("asset_ids", []):
            rows.append(
                {
                    "asset_id": asset_id,
                    "batch": batch_name,
                    "media_skill_id": "",
                    "reason": "provider_fallback_chain",
                    "confidence": "",
                    "provider_used": provider_used,
                    "fallback_attempts": meta.get("attempt_count", 0),
                    "fallback_providers_tried": ", ".join(providers_tried),
                    "fallback_order": ", ".join(fallback_order),
                    "fallback_attempt_summary": json.dumps(
                        fallback_summary,
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                }
            )
        return rows


@dataclass
class _SkillRef:
    skill_id: str
    description: str


class InferenceScaffoldExecutionBackend:
    """Inference-oriented backend that scaffolds asset-level agent runbooks.

    This backend does not invoke image generation directly yet. It writes
    per-asset scaffold files and a batch runbook so teams can execute
    Inference-powered media workflows with explicit, auditable prompts.
    """

    name = "inference_scaffold"
    requires_script_path = False

    _DEFAULT_BATCH_SKILLS: Dict[str, Dict[str, str]] = {
        "anchor": {
            "scaffold_skill_id": "infsh-llm-models",
            "media_skill_id": "infsh-ai-image-generation",
        },
        "identity": {
            "scaffold_skill_id": "infsh-llm-models",
            "media_skill_id": "infsh-ai-image-generation",
        },
        "products": {
            "scaffold_skill_id": "infsh-llm-models",
            "media_skill_id": "infsh-ai-image-generation",
        },
        "photography": {
            "scaffold_skill_id": "infsh-llm-models",
            "media_skill_id": "infsh-ai-image-generation",
        },
        "illustration": {
            "scaffold_skill_id": "infsh-llm-models",
            "media_skill_id": "infsh-ai-image-generation",
        },
        "narrative": {
            "scaffold_skill_id": "infsh-llm-models",
            "media_skill_id": "infsh-ai-image-generation",
        },
        "posters": {
            "scaffold_skill_id": "infsh-llm-models",
            "media_skill_id": "infsh-ai-image-generation",
        },
    }

    _MODEL_APP_HINTS = {
        "nano-banana-pro": "falai/flux-dev-lora",
        "flux-2-pro": "falai/flux-2-klein-lora",
        "recraft-v3": "falai/reve",
    }

    def __init__(self, config: Dict[str, Any], brand_dir: Path, console: Optional[Console] = None) -> None:
        self.config = config
        self.brand_dir = brand_dir
        self.console = console
        self.scaffold_root = brand_dir / ".brandmint" / "inference-agent-scaffolds"
        self.scaffold_root.mkdir(parents=True, exist_ok=True)
        generation = config.get("generation", {}) if isinstance(config, dict) else {}
        self.inference_endpoint = str(generation.get("inference_endpoint", "https://api.inference.sh")).strip()
        self.inference_api_key = (
            str(generation.get("inference_api_key", "")).strip()
            or str(generation.get("inferenceApiKey", "")).strip()
            or str(os.environ.get("INFERENCE_API_KEY", "")).strip()
        )
        mode = str(generation.get("inference_rollout_mode", "ring0")).strip().lower() or "ring0"
        self.rollout_mode = mode if mode in _SUPPORTED_ROLLOUT_MODES else "ring0"

        self._asset_registry = self._load_asset_registry()
        self._skill_refs = self._load_inference_skill_refs()
        self._image_skill_policy = self._load_image_skill_policy(generation)
        self._semantic_routing = self._load_semantic_routing(generation)
        self._allowlisted_image_skills = self._load_allowlisted_image_skills(
            self._image_skill_policy
        )
        self._last_batch_metadata: Dict[str, Dict[str, Any]] = {}

    def run_batch(
        self,
        *,
        script_path: Path,
        config_path: Path,
        batch_name: str,
        asset_ids: List[str],
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        batch_dir = self.scaffold_root / batch_name
        batch_dir.mkdir(parents=True, exist_ok=True)
        run_id = self._build_run_id(config_path=config_path, batch_name=batch_name, asset_ids=asset_ids)
        style_anchor_check = self._check_style_anchor_presence(batch_name)

        runbook_items: List[Dict[str, Any]] = []
        batch_meta: Dict[str, Dict[str, Any]] = {}
        generated = 0
        failures = 0
        warnings = 0

        for index, asset_id in enumerate(asset_ids):
            payload = self._build_asset_payload(asset_id=asset_id, batch_name=batch_name)
            if payload is None:
                failures += 1
                continue

            payload["run_id"] = run_id
            payload["asset_run_id"] = self._build_asset_run_id(run_id=run_id, asset_id=asset_id, index=index)
            payload["status"] = "planned"
            payload["validation_errors"] = []

            validation_errors = self._validate_scaffold_payload(payload)
            if validation_errors:
                failures += 1
                payload["status"] = "failed_validation"
                payload["validation_errors"] = validation_errors
                payload.setdefault("execution_plan", {})
                payload["execution_plan"]["recommended_backend"] = "scripts"
                payload["execution_plan"]["fallback_reason"] = "schema_validation_failed"
            else:
                payload["status"] = "validated"

            if not style_anchor_check.get("ok", True):
                warnings += 1
                payload.setdefault("execution_plan", {})
                payload["execution_plan"]["requires_anchor"] = True
                payload["execution_plan"]["anchor_check"] = style_anchor_check

            generated += 1
            runbook_items.append(payload)
            batch_meta[asset_id] = payload
            (batch_dir / f"{asset_id}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False)
            )
            (batch_dir / f"{asset_id}.md").write_text(self._render_asset_prompt_markdown(payload))

        self._last_batch_metadata[batch_name] = batch_meta

        runbook = {
            "schema_version": "v1",
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "backend": self.name,
            "run_id": run_id,
            "rollout_mode": self.rollout_mode,
            "batch_name": batch_name,
            "asset_count": generated,
            "summary": {
                "validated": sum(1 for item in runbook_items if item.get("status") == "validated"),
                "failed_validation": sum(
                    1 for item in runbook_items if item.get("status") == "failed_validation"
                ),
                "warnings": warnings,
            },
            "inference": {
                "endpoint": self.inference_endpoint,
                "api_key_configured": bool(self.inference_api_key),
            },
            "style_anchor_check": style_anchor_check,
            "assets": runbook_items,
        }
        (batch_dir / "runbook.json").write_text(json.dumps(runbook, indent=2, ensure_ascii=False))

        if self.console:
            self.console.print(
                f"  [cyan]Inference scaffold backend wrote {generated} asset scaffold(s) "
                f"to {batch_dir}[/cyan]"
            )
            if not self.inference_api_key:
                self.console.print(
                    "  [yellow]INFERENCE_API_KEY is not set. "
                    "Scaffolds were generated, but live Inference execution is not authenticated.[/yellow]"
                )

        return subprocess.CompletedProcess(
            args=["inference_scaffold", batch_name],
            returncode=0 if failures == 0 else 2,
            stdout=(
                f"Generated {generated} inference scaffold(s) in {batch_dir}"
                + (f" with {failures} validation failure(s)" if failures else "")
            ),
            stderr="",
        )

    def _load_asset_registry(self) -> Dict[str, Dict[str, Any]]:
        generation = self.config.get("generation", {}) if isinstance(self.config, dict) else {}
        raw_paths = [_ASSET_REGISTRY_PATH]
        configured = generation.get("asset_registry_paths", []) or []
        if isinstance(configured, list):
            raw_paths.extend(configured)
        elif configured:
            raw_paths.append(configured)
        single_path = generation.get("asset_registry_path") or self.config.get("asset_registry_path")
        if single_path:
            raw_paths.append(single_path)

        resolved_paths: List[Path] = []
        seen: set[str] = set()
        for raw in raw_paths:
            path = Path(str(raw)).expanduser()
            if not path.is_absolute():
                path = (self.brand_dir / path).resolve()
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            resolved_paths.append(path)

        merged: Dict[str, Dict[str, Any]] = {}
        for path in resolved_paths:
            if not path.exists():
                continue
            try:
                data = yaml.safe_load(path.read_text()) or {}
            except Exception:
                continue
            assets = data.get("assets", {})
            if not isinstance(assets, dict):
                continue
            merged.update(assets)
        return merged

    def _load_inference_skill_refs(self) -> Dict[str, _SkillRef]:
        refs: Dict[str, _SkillRef] = {}
        if not _INFSH_SKILLS_ROOT.exists():
            return refs

        for skill_md in sorted(_INFSH_SKILLS_ROOT.rglob("SKILL.md")):
            frontmatter = _parse_frontmatter(skill_md.read_text())
            if not frontmatter:
                continue
            sid = str(frontmatter.get("name", "")).strip()
            if not sid:
                continue
            refs[sid] = _SkillRef(
                skill_id=sid,
                description=str(frontmatter.get("description", "")).strip(),
            )
        return refs

    def _load_image_skill_policy(self, generation: Dict[str, Any]) -> Dict[str, Any]:
        """Load image-skill policy from config.

        Preferred key: generation.inference_skill_policy
        Backward-compat key: generation.imported_skill_policy
        """
        policy = generation.get("inference_skill_policy")
        if not isinstance(policy, Mapping):
            legacy = generation.get("imported_skill_policy")
            policy = legacy if isinstance(legacy, Mapping) else {}
        return dict(policy)

    def _load_semantic_routing(self, generation: Dict[str, Any]) -> Dict[str, Any]:
        policy = self._load_image_skill_policy(generation)
        routing = policy.get("semantic_routing", {})
        if not isinstance(routing, Mapping):
            routing = {}

        rules_file = _resolve_rules_path(routing.get("rules_file"), brand_dir=self.brand_dir)
        rules = _load_semantic_rules(rules_file)

        enabled = routing.get("enabled")
        if enabled is None:
            enabled = True

        browser_assets = rules.get("default", {}).get("browser_assets", ["APP-SCREENSHOT"])
        domain_pack = str(routing.get("domain_pack") or "").strip().lower()
        if not domain_pack:
            domain_pack = _infer_domain_pack(self.config.get("brand", {}), rules.get("domain_packs", {}))
        if domain_pack and domain_pack in rules.get("domain_packs", {}):
            pack = rules["domain_packs"][domain_pack]
            if isinstance(pack, Mapping):
                browser_assets = list(browser_assets) + list(pack.get("browser_assets", []))

        browser_assets = routing.get("browser_assets", browser_assets)
        if not isinstance(browser_assets, list):
            browser_assets = ["APP-SCREENSHOT"]
        browser_assets_norm = {str(x).strip().upper() for x in browser_assets if str(x).strip()}

        browser_keywords = rules.get("default", {}).get(
            "browser_keywords",
            ["screenshot", "screen", "ui", "interface", "dashboard", "webpage", "app store"],
        )
        if domain_pack and domain_pack in rules.get("domain_packs", {}):
            pack = rules["domain_packs"][domain_pack]
            if isinstance(pack, Mapping):
                browser_keywords = list(browser_keywords) + list(pack.get("browser_keywords", []))

        browser_keywords = routing.get("browser_keywords", browser_keywords)
        if not isinstance(browser_keywords, list):
            browser_keywords = []
        browser_keywords_norm = [str(x).strip().lower() for x in browser_keywords if str(x).strip()]

        return {
            "enabled": bool(enabled),
            "rules_file": str(rules_file),
            "domain_pack": domain_pack,
            "browser_assets": browser_assets_norm,
            "browser_keywords": browser_keywords_norm,
        }

    def _load_allowlisted_image_skills(self, policy: Mapping[str, Any]) -> set[str]:
        path = _resolve_allowlist_path(policy.get("allowlist_file"), brand_dir=self.brand_dir)
        parsed = _load_skill_allowlist(path)

        inline = policy.get("allowlist", [])
        if isinstance(inline, list):
            for item in inline:
                sid = _normalize_skill_id(str(item))
                if sid:
                    parsed.add(sid)

        # Keep runtime usable even if allowlist file is missing.
        if not parsed:
            parsed = {
                "infsh-llm-models",
                "infsh-ai-image-generation",
                "infsh-agentic-browser",
            }
        return parsed

    @staticmethod
    def _build_run_id(*, config_path: Path, batch_name: str, asset_ids: List[str]) -> str:
        seed = f"{str(config_path.resolve())}|{batch_name}|{','.join(sorted(asset_ids))}"
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _build_asset_run_id(*, run_id: str, asset_id: str, index: int) -> str:
        seed = f"{run_id}|{asset_id}|{index}"
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]

    def get_batch_metadata(self, batch_name: str) -> Dict[str, Dict[str, Any]]:
        """Return last generated per-asset metadata for a batch."""
        return dict(self._last_batch_metadata.get(batch_name, {}))

    def get_batch_routing_summary(self, batch_name: str) -> List[Dict[str, Any]]:
        """Return concise routing metadata for execution reporting."""
        out: List[Dict[str, Any]] = []
        for asset_id, payload in self.get_batch_metadata(batch_name).items():
            routing = payload.get("routing", {})
            skills = payload.get("skills", {})
            out.append(
                {
                    "asset_id": asset_id,
                    "batch": batch_name,
                    "media_skill_id": skills.get("media_skill_id"),
                    "reason": routing.get("reason"),
                    "confidence": routing.get("confidence"),
                    "signals": routing.get("signals", []),
                    "status": payload.get("status"),
                    "run_id": payload.get("run_id"),
                    "asset_run_id": payload.get("asset_run_id"),
                }
            )
        return out

    def preview_asset_route(self, *, asset_id: str, batch_name: str) -> Dict[str, Any]:
        """Preview inferred route for an asset without writing files."""
        payload = self._build_asset_payload(asset_id=asset_id, batch_name=batch_name)
        if payload is None:
            return {"asset_id": asset_id, "batch_name": batch_name, "status": "not_found"}
        return {
            "asset_id": asset_id,
            "batch_name": batch_name,
            "media_skill_id": payload.get("skills", {}).get("media_skill_id"),
            "scaffold_skill_id": payload.get("skills", {}).get("scaffold_skill_id"),
            "routing": payload.get("routing", {}),
            "prompt_lineage": payload.get("prompt_lineage", {}),
        }

    def _check_style_anchor_presence(self, batch_name: str) -> Dict[str, Any]:
        if batch_name == "anchor":
            return {"ok": True, "required": False, "reason": "anchor batch"}

        output_dir = self.brand_dir / self.config.get("generation", {}).get("output_dir", "generated")
        exists = any(output_dir.glob("2A-*"))
        return {
            "ok": bool(exists),
            "required": True,
            "anchor_glob": str(output_dir / "2A-*"),
            "reason": "style_anchor_found" if exists else "style_anchor_missing",
        }

    def _validate_scaffold_payload(self, payload: Dict[str, Any]) -> List[str]:
        errors: List[str] = []

        missing = sorted(_SCAFFOLD_SCHEMA_REQUIRED_KEYS - set(payload.keys()))
        if missing:
            errors.append(f"missing top-level keys: {', '.join(missing)}")

        skills = payload.get("skills", {})
        if not isinstance(skills, Mapping):
            errors.append("skills must be an object")
        else:
            if not skills.get("scaffold_skill_id"):
                errors.append("skills.scaffold_skill_id is required")
            if not skills.get("media_skill_id"):
                errors.append("skills.media_skill_id is required")

        media_input = payload.get("media_input", {})
        if not isinstance(media_input, Mapping):
            errors.append("media_input must be an object")
        else:
            if not media_input.get("prompt"):
                errors.append("media_input.prompt is required")
            if not media_input.get("aspect_ratio"):
                errors.append("media_input.aspect_ratio is required")

        execution_plan = payload.get("execution_plan", {})
        if not isinstance(execution_plan, Mapping):
            errors.append("execution_plan must be an object")

        routing = payload.get("routing", {})
        if not isinstance(routing, Mapping):
            errors.append("routing must be an object")
        else:
            if "confidence" not in routing:
                errors.append("routing.confidence is required")
            if "reason" not in routing:
                errors.append("routing.reason is required")

        return errors

    def _apply_image_skill_policy(
        self,
        *,
        asset_id: str,
        batch_name: str,
        base_skills: Dict[str, str],
    ) -> tuple[Dict[str, str], List[str]]:
        skills = dict(base_skills)
        policy = self._image_skill_policy
        lineage: List[str] = []

        default_override = _normalize_override_spec(policy.get("default"))
        if default_override:
            skills.update(default_override)
            lineage.append("policy.default")

        batch_overrides = policy.get("batch_overrides", {})
        if isinstance(batch_overrides, Mapping):
            batch_override = _normalize_override_spec(batch_overrides.get(batch_name))
            if batch_override:
                skills.update(batch_override)
                lineage.append(f"policy.batch_overrides.{batch_name}")

        asset_overrides = policy.get("asset_overrides", {})
        if isinstance(asset_overrides, Mapping):
            asset_override = _normalize_override_spec(asset_overrides.get(asset_id))
            if asset_override:
                skills.update(asset_override)
                lineage.append(f"policy.asset_overrides.{asset_id}")

        skills["scaffold_skill_id"] = self._enforce_allowlist_for_image_skill(
            candidate=skills.get("scaffold_skill_id", ""),
            fallback=base_skills.get("scaffold_skill_id", "infsh-llm-models"),
            context=f"{asset_id}/scaffold",
            role="scaffold",
        )
        skills["media_skill_id"] = self._enforce_allowlist_for_image_skill(
            candidate=skills.get("media_skill_id", ""),
            fallback=base_skills.get("media_skill_id", "infsh-ai-image-generation"),
            context=f"{asset_id}/media",
            role="media",
        )
        return skills, lineage

    def _apply_semantic_image_routing(
        self,
        *,
        asset_id: str,
        batch_name: str,
        meta: Mapping[str, Any],
        base_skills: Dict[str, str],
    ) -> tuple[Dict[str, str], Dict[str, Any]]:
        """Meta-semantic media skill selection for image flows.

        Defaults to image-generation and upgrades to browser automation when
        asset semantics indicate screenshot/UI capture.
        """
        skills = dict(base_skills)
        if not self._semantic_routing.get("enabled", True):
            return skills, {
                "enabled": False,
                "reason": "semantic_routing_disabled",
                "confidence": 0.5,
                "signals": [],
            }

        routing = self._infer_semantic_media_skill(
            asset_id=asset_id,
            batch_name=batch_name,
            meta=meta,
            current_media_skill=skills.get("media_skill_id", "infsh-ai-image-generation"),
        )
        media_skill = str(routing.get("media_skill_id") or "").strip()
        if media_skill:
            skills["media_skill_id"] = media_skill
        return skills, routing

    def _infer_semantic_media_skill(
        self,
        *,
        asset_id: str,
        batch_name: str,
        meta: Mapping[str, Any],
        current_media_skill: str,
    ) -> Dict[str, Any]:
        browser_assets = self._semantic_routing.get("browser_assets", set())
        if asset_id.upper() in browser_assets:
            return {
                "media_skill_id": "infsh-agentic-browser",
                "reason": "asset_id_in_browser_assets",
                "confidence": 0.99,
                "signals": [asset_id.upper()],
            }

        name = str(meta.get("name", "")).strip().lower()
        prompt_key = str(meta.get("prompt_key", "")).strip().lower()
        tags = meta.get("tags", [])
        tag_text = " ".join(str(t).strip().lower() for t in tags) if isinstance(tags, list) else ""
        semantic_blob = " ".join([asset_id.lower(), batch_name.lower(), name, prompt_key, tag_text])

        browser_keywords = self._semantic_routing.get("browser_keywords", [])
        for kw in browser_keywords:
            if kw and kw in semantic_blob:
                return {
                    "media_skill_id": "infsh-agentic-browser",
                    "reason": "keyword_match",
                    "confidence": 0.85,
                    "signals": [kw],
                }

        return {
            "media_skill_id": current_media_skill,
            "reason": "default_image_generation",
            "confidence": 0.7,
            "signals": [],
        }

    def _enforce_allowlist_for_image_skill(
        self,
        *,
        candidate: str,
        fallback: str,
        context: str,
        role: str,
    ) -> str:
        candidate_id = _normalize_skill_id(candidate)
        fallback_id = _normalize_skill_id(fallback)

        if not candidate_id:
            return fallback_id or candidate_id

        allowed_role_set = (
            _SUPPORTED_SCAFFOLD_SKILL_IDS if role == "scaffold" else _SUPPORTED_MEDIA_SKILL_IDS
        )
        if candidate_id not in allowed_role_set:
            self._warn(
                f"Image skill '{candidate_id}' is not supported for role={role} ({context}); "
                f"using '{fallback_id}'."
            )
            candidate_id = fallback_id

        if candidate_id not in self._allowlisted_image_skills:
            self._warn(
                f"Image skill override '{candidate_id}' is not allowlisted for {context}; "
                f"using '{fallback_id}'."
            )
            candidate_id = fallback_id

        if candidate_id and self._skill_refs and candidate_id not in self._skill_refs:
            self._warn(
                f"Image skill '{candidate_id}' is not installed in normalized inference pack; "
                f"using '{fallback_id}'."
            )
            candidate_id = fallback_id

        return candidate_id

    def _warn(self, message: str) -> None:
        if not self.console:
            return
        self.console.print(f"  [yellow]{message}[/yellow]")

    def _build_asset_payload(self, asset_id: str, batch_name: str) -> Optional[Dict[str, Any]]:
        meta = self._asset_registry.get(asset_id, {})
        name = str(meta.get("name", asset_id)).strip()
        prompt_key = str(meta.get("prompt_key", asset_id.lower().replace("-", "_"))).strip()
        model = str(meta.get("model", "nano-banana-pro")).strip()
        aspect = str(meta.get("aspect", "landscape_16_9")).strip()
        batch_norm = self._normalize_batch_name(batch_name)

        skills = dict(self._DEFAULT_BATCH_SKILLS.get(batch_norm, {}))
        if not skills:
            skills = {
                "scaffold_skill_id": "infsh-llm-models",
                "media_skill_id": "infsh-ai-image-generation",
            }
        skills_before_semantic = dict(skills)
        skills, routing = self._apply_semantic_image_routing(
            asset_id=asset_id,
            batch_name=batch_norm,
            meta=meta,
            base_skills=skills,
        )
        skills, policy_lineage = self._apply_image_skill_policy(
            asset_id=asset_id,
            batch_name=batch_norm,
            base_skills=skills,
        )

        scaffold_skill = skills["scaffold_skill_id"]
        media_skill = skills["media_skill_id"]
        app_id_hint = self._MODEL_APP_HINTS.get(model, "falai/flux-dev-lora")

        brand = self.config.get("brand", {}) if isinstance(self.config, dict) else {}
        brand_name = brand.get("name", "Unknown Brand")
        brand_tagline = brand.get("tagline", "")
        brand_domain = brand.get("domain", "")

        agent_prompt = (
            f"You are the media asset agent for {asset_id} ({name}) in batch '{batch_name}'. "
            f"Brand: {brand_name}. "
            f"Tagline: {brand_tagline}. "
            f"Domain: {brand_domain}. "
            f"Use {media_skill} to produce the asset output with strong brand consistency. "
            "Generate one final production-ready output and one concise reasoning note "
            "describing composition, typography, and style choices."
        )

        file_glob = f"{asset_id}-*.png"
        if media_skill == "infsh-agentic-browser":
            file_glob = f"{asset_id}-*.png"

        fallback_enabled = bool(self._image_skill_policy.get("fallback_to_scripts", True))
        execution_plan = {
            "primary_backend": "inference",
            "recommended_backend": "inference",
            "fallback_backend": "scripts" if fallback_enabled else None,
            "fallback_enabled": fallback_enabled,
            "fallback_reason": None,
            "rollout_mode": self.rollout_mode,
        }
        if media_skill not in _SUPPORTED_MEDIA_SKILL_IDS:
            execution_plan["recommended_backend"] = "scripts"
            execution_plan["fallback_reason"] = "unsupported_media_skill"
        if self.rollout_mode == "ring0":
            execution_plan["recommended_backend"] = "scripts"
            execution_plan["fallback_reason"] = "rollout_ring0"

        return {
            "schema_version": "v1",
            "asset_id": asset_id,
            "asset_name": name,
            "batch_type": batch_name,
            "prompt_key": prompt_key,
            "skills": {
                "scaffold_skill_id": scaffold_skill,
                "media_skill_id": media_skill,
                "scaffold_skill_description": self._skill_description(scaffold_skill),
                "media_skill_description": self._skill_description(media_skill),
            },
            "routing": {
                "enabled": bool(self._semantic_routing.get("enabled", True)),
                "reason": routing.get("reason", "unknown"),
                "confidence": routing.get("confidence", 0.5),
                "signals": routing.get("signals", []),
            },
            "execution_plan": execution_plan,
            "agent_prompt": agent_prompt,
            "prompt_lineage": {
                "base_batch_skills": skills_before_semantic,
                "semantic_routing_applied": routing,
                "policy_overrides_applied": policy_lineage,
                "final_skills": skills,
            },
            "media_input": {
                "app_id_hint": app_id_hint,
                "model_hint": model,
                "prompt": f"Render asset {asset_id} ({name}) for brand {brand_name}.",
                "aspect_ratio": _normalize_aspect(aspect),
                "image_urls": [],
            },
            "expected_outputs": {
                "file_glob": file_glob,
                "output_dir": str((self.brand_dir / self.config.get("generation", {}).get("output_dir", "generated"))),
            },
        }

    def _skill_description(self, skill_id: str) -> str:
        ref = self._skill_refs.get(skill_id)
        if not ref:
            return ""
        return ref.description

    @staticmethod
    def _normalize_batch_name(batch_name: str) -> str:
        if batch_name == "illustration":
            return "illustration"
        if batch_name == "illustrations":
            return "illustration"
        return batch_name

    def _render_asset_prompt_markdown(self, payload: Dict[str, Any]) -> str:
        skills = payload.get("skills", {})
        media_input = payload.get("media_input", {})
        routing = payload.get("routing", {})
        lineage = payload.get("prompt_lineage", {})
        execution_plan = payload.get("execution_plan", {})
        return (
            f"# Asset Agent Scaffold: {payload.get('asset_id')}\n\n"
            f"## Target\n"
            f"- Asset: {payload.get('asset_name')}\n"
            f"- Batch: {payload.get('batch_type')}\n"
            f"- Run ID: {payload.get('run_id', '-')}\n"
            f"- Asset Run ID: {payload.get('asset_run_id', '-')}\n"
            f"- Prompt key: {payload.get('prompt_key')}\n\n"
            f"## Skills\n"
            f"- Scaffold skill: `{skills.get('scaffold_skill_id')}`\n"
            f"- Media skill: `{skills.get('media_skill_id')}`\n\n"
            f"## Routing\n"
            f"- Reason: `{routing.get('reason')}`\n"
            f"- Confidence: `{routing.get('confidence')}`\n"
            f"- Signals: `{', '.join(routing.get('signals', [])) if isinstance(routing.get('signals'), list) else ''}`\n\n"
            f"## Execution Plan\n"
            f"- Primary backend: `{execution_plan.get('primary_backend')}`\n"
            f"- Recommended backend: `{execution_plan.get('recommended_backend')}`\n"
            f"- Fallback backend: `{execution_plan.get('fallback_backend')}`\n"
            f"- Fallback enabled: `{execution_plan.get('fallback_enabled')}`\n\n"
            f"## Prompt Lineage\n"
            f"- Policy overrides: `{', '.join(lineage.get('policy_overrides_applied', [])) if isinstance(lineage.get('policy_overrides_applied'), list) else ''}`\n"
            f"- Final skills: `{lineage.get('final_skills')}`\n\n"
            f"## Agent Prompt\n"
            f"{payload.get('agent_prompt')}\n\n"
            f"## Inference Hints\n"
            f"- App ID hint: `{media_input.get('app_id_hint')}`\n"
            f"- Model hint: `{media_input.get('model_hint')}`\n"
            f"- Aspect ratio: `{media_input.get('aspect_ratio')}`\n"
        )


def create_visual_backend(
    *,
    config: Dict[str, Any],
    brand_dir: Path,
    console: Optional[Console] = None,
) -> VisualExecutionBackend:
    generation = config.get("generation", {}) if isinstance(config, dict) else {}
    mode = str(generation.get("visual_backend", "scripts")).strip().lower()

    if mode in {"inference_scaffold", "inference-scaffold"}:
        return InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir, console=console)

    if mode == "inference":
        inference_api_key = (
            str(generation.get("inference_api_key", "")).strip()
            or str(generation.get("inferenceApiKey", "")).strip()
            or str(os.environ.get("INFERENCE_API_KEY", "")).strip()
        )
        fallback = str(generation.get("inference_missing_auth_fallback", "scripts")).strip().lower() or "scripts"
        if inference_api_key:
            return InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir, console=console)
        if fallback in {"scaffold", "inference_scaffold", "inference-scaffold"}:
            if console:
                console.print("[yellow]Inference auth missing — remaining in scaffold mode by configuration.[/yellow]")
            return InferenceScaffoldExecutionBackend(config=config, brand_dir=brand_dir, console=console)
        if console:
            console.print("[yellow]Inference auth missing — falling back to scripts backend.[/yellow]")
        return SubprocessVisualExecutionBackend(config=config, console=console)

    return SubprocessVisualExecutionBackend(config=config, console=console)


def _resolve_allowlist_path(path_value: Any, *, brand_dir: Path) -> Path:
    if not path_value:
        return _INFSH_ALLOWLIST_PATH

    raw = Path(str(path_value)).expanduser()
    if raw.is_absolute():
        return raw

    candidate_brand = (brand_dir / raw).resolve()
    if candidate_brand.exists():
        return candidate_brand

    candidate_repo = (_REPO_ROOT / raw).resolve()
    if candidate_repo.exists():
        return candidate_repo

    return candidate_repo


def _resolve_rules_path(path_value: Any, *, brand_dir: Path) -> Path:
    if not path_value:
        return _SEMANTIC_RULES_PATH

    raw = Path(str(path_value)).expanduser()
    if raw.is_absolute():
        return raw

    candidate_brand = (brand_dir / raw).resolve()
    if candidate_brand.exists():
        return candidate_brand

    candidate_repo = (_REPO_ROOT / raw).resolve()
    if candidate_repo.exists():
        return candidate_repo

    return candidate_repo


def _load_semantic_rules(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": "v1", "default": {}, "domain_packs": {}}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"version": "v1", "default": {}, "domain_packs": {}}
    if not isinstance(data, Mapping):
        return {"version": "v1", "default": {}, "domain_packs": {}}
    return {
        "version": str(data.get("version", "v1")),
        "default": dict(data.get("default", {})) if isinstance(data.get("default"), Mapping) else {},
        "domain_packs": dict(data.get("domain_packs", {}))
        if isinstance(data.get("domain_packs"), Mapping)
        else {},
    }


def _infer_domain_pack(brand: Any, domain_packs: Mapping[str, Any]) -> str:
    if not isinstance(brand, Mapping):
        return ""
    tags = brand.get("domain_tags", [])
    candidates: List[str] = []
    if isinstance(tags, list):
        candidates.extend(str(t).strip().lower() for t in tags if str(t).strip())
    domain = str(brand.get("domain", "")).strip().lower()
    if domain:
        candidates.append(domain)
    for candidate in candidates:
        if candidate in domain_packs:
            return candidate
    return ""


def _load_skill_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()

    if isinstance(data, list):
        values = data
    elif isinstance(data, Mapping):
        values = data.get("skills", [])
    else:
        values = []

    out: set[str] = set()
    if isinstance(values, list):
        for item in values:
            sid = _normalize_skill_id(str(item))
            if sid:
                out.add(sid)
    return out


def _normalize_override_spec(value: Any) -> Dict[str, str]:
    """Normalize override spec to {'scaffold_skill_id','media_skill_id'}."""
    if isinstance(value, str):
        sid = _normalize_skill_id(value)
        return {"media_skill_id": sid} if sid else {}

    if not isinstance(value, Mapping):
        return {}

    out: Dict[str, str] = {}
    scaffold = value.get("scaffold_skill_id")
    media = value.get("media_skill_id")
    if scaffold:
        sid = _normalize_skill_id(str(scaffold))
        if sid:
            out["scaffold_skill_id"] = sid
    if media:
        sid = _normalize_skill_id(str(media))
        if sid:
            out["media_skill_id"] = sid
    return out


def _validate_fallback_order(value: Any) -> List[str]:
    """Validate generation.fallback_order and return normalized providers."""
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValueError("generation.fallback_order must be a list of provider names")

    normalized: List[str] = []
    invalid: List[str] = []
    for raw_provider in value:
        provider = str(raw_provider).strip().lower()
        if not provider:
            continue
        if provider not in _SUPPORTED_FALLBACK_PROVIDERS:
            invalid.append(provider)
            continue
        if provider not in normalized:
            normalized.append(provider)

    if invalid:
        valid_values = ", ".join(sorted(_SUPPORTED_FALLBACK_PROVIDERS))
        raise ValueError(
            "generation.fallback_order contains unknown provider(s): "
            + ", ".join(invalid)
            + f". Valid options: {valid_values}"
        )
    return normalized


def _parse_frontmatter(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    if not stripped.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    block = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(block)
    except Exception:
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _normalize_aspect(aspect: str) -> str:
    mapping = {
        "landscape_16_9": "16:9",
        "landscape_4_3": "4:3",
        "portrait_hd": "9:16",
        "portrait_3_4": "3:4",
        "portrait_4_3": "4:3",
        "square": "1:1",
        "square_hd": "1:1",
    }
    return mapping.get(aspect, aspect)
