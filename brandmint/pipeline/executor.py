"""
Brandmint Pipeline -- Wave Execution Engine.

Orchestrates text skill prompt generation and visual asset subprocess
execution across dependency-ordered waves with persistent state for
resume capability.

Architecture
------------
The executor sits between the CLI (launch.py) and core services:

    CLI  ->  WaveExecutor  ->  AgentScaffolder   (text prompts)
                           ->  subprocess         (visual assets)
                           ->  hydrator           (config enrichment)

Text skills follow a *prompt-file handoff* model:
    1. Generate scaffolded prompt -> write to .brandmint/prompts/{id}.md
    2. Wait for user/agent to execute and save output to .brandmint/outputs/{id}.json
    3. Read output -> store as upstream data for downstream skills

Visual assets auto-execute via subprocess to scripts/run_pipeline.py.

Between Wave 2 and Wave 3, auto-hydration injects completed text
outputs into brand-config.yaml so visual prompts use strategy data.
"""

from __future__ import annotations

import json
import logging
import re
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.prompt import Confirm

from ..models.wave import Wave, WaveStatus, ExecutionState
from ..models.scenario import ExecutionContext
from ..models.skill import UnifiedSkill, SkillSource
from ..core.skills_registry import SkillsRegistry
from ..core.agent_scaffolder import AgentScaffolder
from ..core.hydrator import hydrate_brand_config, save_hydrated_config
from ..core.kickstarter_blueprint import build_kickstarter_readiness
from ..cli.ui import (
    render_wave_progress,
    render_skill_prompt,
    render_execution_summary,
)
from ..cli.icons import Icons
from ..cli.spinners import create_wave_progress, create_skill_progress
from ..cli.notifications import notify_completion, notify_error
from ..cli.report import (
    ExecutionReport, 
    SkillExecution, 
    AssetExecution,
    save_report,
)
from .visual_backend import create_visual_backend
from ..core.cache import get_prompt_cache
from ..models.state_validator import load_state_safe, save_state_safe

logger = logging.getLogger(__name__)

# Estimated costs per provider (USD per image)
PROVIDER_COSTS = {
    "fal": 0.08,
    "openrouter": 0.05,
    "openai": 0.08,
    "replicate": 0.06,
}

# Root of the brandmint package (three levels up from this file).
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


class WaveExecutor:
    """Orchestrates wave-by-wave execution of text skills and visual assets.

    Each wave is processed in dependency order.  Text skills produce
    scaffolded prompts written to disk; visual assets are dispatched to a
    subprocess pipeline.  Persistent state allows execution to be
    interrupted and resumed across sessions.
    """

    # Asset ID -> batch name mapping for the visual pipeline.
    ASSET_BATCH_MAP: Dict[str, str] = {
        "2A": "anchor",
        "2B": "identity",
        "2C": "identity",
        "APP-ICON": "identity",
        "3A": "products",
        "3B": "products",
        "3C": "products",
        "APP-SCREENSHOT": "products",
        "4A": "photography",
        "4B": "photography",
        "5A": "illustration",
        "5B": "illustration",
        "5C": "illustration",
        "7A": "narrative",
        "8A": "posters",
        "IG-STORY": "posters",
        "PITCH-HERO": "posters",
        "OG-IMAGE": "photography",
        "TWITTER-HEADER": "photography",
        "EMAIL-HERO": "narrative",
    }

    def __init__(
        self,
        config: dict,
        config_path: Path,
        waves: List[Wave],
        execution_context: ExecutionContext,
        brand_dir: Path,
        console: Console,
        scenario_id: Optional[str] = None,
    ) -> None:
        self.config = config
        self.config_path = config_path
        self.waves = waves
        self.context = execution_context
        self.brand_dir = brand_dir
        self.console = console
        self.scenario_id = scenario_id

        # Working directories
        self.prompts_dir = brand_dir / ".brandmint" / "prompts"
        self.outputs_dir = brand_dir / ".brandmint" / "outputs"
        self.state_path = brand_dir / ".brandmint-state.json"

        # Ensure directories exist
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        # Core services
        self.registry = SkillsRegistry(
            claude_skills_dir=Path.home() / ".claude" / "skills",
        )
        self.scaffolder = AgentScaffolder()

        # Runtime state
        self.state = self._load_or_create_state()
        if self.scenario_id:
            self.state.scenario = self.scenario_id
        elif self.state.scenario:
            self.scenario_id = self.state.scenario

        self.upstream_data: Dict[str, Any] = {}
        self._interrupted = False
        
        # Cost tracking
        self._actual_costs: Dict[str, float] = {}  # asset_id -> cost
        self._provider = self.config.get("generation", {}).get("provider", "fal")
        self._visual_backend = create_visual_backend(
            config=self.config,
            brand_dir=self.brand_dir,
            console=self.console,
        )
        self._visual_bundle_prepared = False
        
        # Execution report
        self._report = ExecutionReport(
            brand_name=self.config.get("brand", {}).get("name", "Unknown"),
            scenario=self.scenario_id or "custom",
            started_at=datetime.now().isoformat(),
        )

        # Setup graceful interrupt handling
        self._setup_signal_handlers()

        # Hydrate upstream_data from any pre-existing outputs on disk.
        self._load_existing_outputs()
        self._refresh_kickstarter_readiness()

    def _setup_signal_handlers(self) -> None:
        """Install signal handlers for graceful shutdown.
        
        Catches SIGINT (Ctrl+C) and SIGTERM to save state before exit.
        """
        def handler(signum, frame):
            if self._interrupted:
                # Second interrupt - force exit
                self.console.print("\n[red]Force quit.[/red]")
                sys.exit(130)
            
            self._interrupted = True
            self.console.print(f"\n[yellow]{Icons.WARNING} Interrupted. Saving state...[/yellow]")
            self._save_state()
            self._finalize_report(success=False)
            self.console.print(f"  [dim]State saved to: {self.state_path}[/dim]")
            self.console.print(f"  [dim]Resume with: bm launch --config {self.config_path}[/dim]")
            sys.exit(130)
        
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        wave_range: Optional[range] = None,
        interactive: bool = True,
    ) -> ExecutionState:
        """Run waves in dependency order and return final execution state.

        Args:
            wave_range: Optional range of wave numbers to execute.
                        When ``None`` all waves are executed.
            interactive: If ``True``, pause for user input when waiting
                         for text skill outputs.

        Returns:
            The updated :class:`ExecutionState` after all targeted waves
            have been processed.
        """
        self.state.started_at = self.state.started_at or datetime.now().isoformat()
        self.state.updated_at = datetime.now().isoformat()
        self._save_state()

        target_waves = self._resolve_waves(wave_range)

        for wave in target_waves:
            # Dependency gate: all prerequisite waves must be complete.
            if not self._dependencies_met(wave):
                self.console.print(
                    f"[yellow]Skipping Wave {wave.number} -- "
                    f"dependencies {wave.depends_on} not yet complete.[/yellow]"
                )
                continue

            self.console.print(
                f"\n[bold cyan]--- Wave {wave.number}: {wave.name} ---[/bold cyan]"
            )

            # Auto-hydration checkpoint: enrich config before Wave 3.
            if wave.number == 3 and self._is_wave_complete(2):
                self._run_hydration()

            # Initialize wave state bucket if needed.
            wkey = str(wave.number)
            if wkey not in self.state.waves:
                self.state.waves[wkey] = {
                    "status": WaveStatus.IN_PROGRESS.value,
                    "text_skills": {},
                    "visual_assets": {},
                    "estimated_cost": wave.estimated_cost,
                    "kickstarter_sections": list(wave.kickstarter_sections),
                    "kickstarter_artifacts": list(wave.kickstarter_artifacts),
                }

            self.state.waves[wkey]["status"] = WaveStatus.IN_PROGRESS.value
            self.state.waves[wkey]["kickstarter_sections"] = list(wave.kickstarter_sections)
            self.state.waves[wkey]["kickstarter_artifacts"] = list(wave.kickstarter_artifacts)
            self._save_state()

            # Post-hook waves delegate to a custom publisher.
            if wave.post_hook:
                hook_ok = self._execute_post_hook(wave.post_hook, wave.number)
                self.state.waves[wkey]["status"] = (
                    WaveStatus.COMPLETED.value if hook_ok
                    else WaveStatus.FAILED.value
                )
                self.state.updated_at = datetime.now().isoformat()
                self._save_state()
                render_wave_progress(wave, self.state.waves[wkey], self.console)
                continue

            # Execute text skills sequentially (prompt-file handoff).
            all_text_ok = True
            for skill_id in wave.text_skills:
                ok = self._execute_text_skill(skill_id, wave.number, interactive)
                if not ok:
                    all_text_ok = False

            # Execute visual assets via subprocess batches.
            all_visual_ok = True
            if wave.visual_assets:
                all_visual_ok = self._execute_visual_assets(
                    wave.visual_assets, wave.number
                )

            # Mark wave status.
            if all_text_ok and all_visual_ok:
                self.state.waves[wkey]["status"] = WaveStatus.COMPLETED.value
            else:
                self.state.waves[wkey]["status"] = WaveStatus.FAILED.value

            self.state.updated_at = datetime.now().isoformat()
            self._save_state()

            # Display progress.
            render_wave_progress(wave, self.state.waves[wkey], self.console)

        # Final summary.
        render_execution_summary(
            {"waves": self.state.waves, "state_file": str(self.state_path)},
            self.console,
        )

        # Compute success status
        all_success = all(
            w.get("status") == "completed" for w in self.state.waves.values()
        )
        total_assets = sum(
            len([a for a in w.get("visual_assets", {}).values() if a.get("status") == "completed"])
            for w in self.state.waves.values()
        )

        # Finalize and save report
        self._finalize_report(success=all_success)
        brand_name = self.config.get("brand", {}).get("name", "Brand")
        
        if self.state.started_at:
            from datetime import datetime as dt
            start = dt.fromisoformat(self.state.started_at)
            duration = (dt.now() - start).total_seconds()
        else:
            duration = None
        
        notify_completion(
            brand_name,
            success=all_success,
            assets_generated=total_assets,
            duration_seconds=duration,
        )

        return self.state

    # ------------------------------------------------------------------
    # Post-hook execution (Wave 7+)
    # ------------------------------------------------------------------

    def _execute_post_hook(self, hook_name: str, wave_number: int) -> bool:
        """Execute a wave post-hook (e.g. publishing pipeline).

        Returns True on success.
        """
        if hook_name in ("notebooklm", "publishing"):
            return self._hook_publishing_pipeline(wave_number)
        if hook_name in ("brand_docs", "astro_wiki"):
            return self._hook_brand_docs_pipeline(wave_number)
        else:
            self.console.print(
                f"[red]Unknown post hook: {hook_name}[/red]"
            )
            return False

    def _hook_publishing_pipeline(self, wave_number: int) -> bool:
        """Run Wave 7 publishing — NotebookLM only.

        Creates a notebook, uploads brand sources, and generates all
        artifacts (mind-map, slide decks, report, audio overview).
        Reads synthesis config from brand-config.yaml ``publishing:`` section.
        """
        self.console.print("\n  [bold cyan]Wave 7: NotebookLM Publishing[/bold cyan]")
        try:
            from ..publishing.notebooklm_publisher import NotebookLMPublisher

            # Read synthesis config from brand-config.yaml publishing section
            pub_config = self.config.get("publishing", {})
            synthesize = pub_config.get("synthesize", True)
            synthesis_model = pub_config.get("synthesis_model", "")

            publisher = NotebookLMPublisher(
                brand_dir=self.brand_dir,
                config=self.config,
                config_path=self.config_path,
                console=self.console,
                synthesize=synthesize,
                synthesis_model=synthesis_model,
            )
            if not publisher.publish():
                self.console.print(
                    "  [yellow]NotebookLM publishing did not complete[/yellow]"
                )
                return False
            return True
        except ImportError:
            self.console.print(
                "  [red]NotebookLM publishing requires notebooklm-py.[/red]\n"
                "  Install with: [bold]pip install notebooklm-py[/bold]"
            )
            return False
        except Exception as e:
            self.console.print(f"  [red]NotebookLM error: {e}[/red]")
            return False

    def _hook_brand_docs_pipeline(self, wave_number: int) -> bool:
        """Run Wave 8 publishing — brand docs markdown + Astro wiki build."""
        self.console.print("\n  [bold cyan]Wave 8: Brand Docs + Astro Wiki[/bold cyan]")
        try:
            from ..publishing.brand_docs_publisher import BrandDocsPublisher

            publisher = BrandDocsPublisher(
                brand_dir=self.brand_dir,
                config=self.config,
                config_path=self.config_path,
                console=self.console,
            )
            if not publisher.publish():
                self.console.print(
                    "  [yellow]Brand docs publishing did not complete[/yellow]"
                )
                return False
            return True
        except Exception as e:
            self.console.print(f"  [red]Brand docs error: {e}[/red]")
            return False

    # ------------------------------------------------------------------
    # Text skill execution
    # ------------------------------------------------------------------

    def _execute_text_skill(
        self,
        skill_id: str,
        wave_num: int,
        interactive: bool = True,
    ) -> bool:
        """Generate prompt, write to disk, wait for output, store upstream.

        Returns ``True`` when output was successfully captured, ``False``
        when skipped or timed out.
        """
        # Skip if already completed.
        if self._is_skill_complete(skill_id):
            self.console.print(f"  [dim]Skipping {skill_id} (already completed)[/dim]")
            return True

        # Resolve skill from registry (or create a stub).
        skill = self.registry.get_skill(skill_id)
        if skill is None:
            skill = self._create_stub_skill(skill_id)

        # Generate the scaffolded prompt (with caching).
        start_ts = time.monotonic()
        cache = get_prompt_cache()
        cache_key = f"{skill_id}:{self.state.scenario or 'execution'}"
        cached = cache.get(cache_key, provider="scaffolder", model=skill_id)
        if cached and isinstance(cached, str):
            prompt = cached
            self.console.print(f"  [dim]Using cached prompt for {skill_id}[/dim]")
        else:
            prompt = self.scaffolder.generate_context_prompt(
                skill=skill,
                context=self.context,
                upstream_data=self.upstream_data,
                scenario_name=self.state.scenario or "execution",
            )
            cache.set(cache_key, prompt, provider="scaffolder", model=skill_id)

        # Write prompt to disk.
        prompt_path = self.prompts_dir / f"{skill_id}.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        output_path = self.outputs_dir / f"{skill_id}.json"

        # Display prompt panel.
        render_skill_prompt(skill_id, prompt, str(output_path), self.console)

        # Mark in-progress.
        self._update_state(wave_num, skill_id, "text_skills", "in_progress")

        # Wait for output (prompt-file handoff).
        output_data = self._wait_for_output(skill_id, interactive)
        duration = time.monotonic() - start_ts

        if output_data is not None:
            self.upstream_data[skill_id] = output_data
            self._refresh_kickstarter_readiness()
            self._update_state(
                wave_num,
                skill_id,
                "text_skills",
                "completed",
                duration_seconds=round(duration, 1),
            )
            # Track in report
            self._report.skills.append(SkillExecution(
                skill_id=skill_id,
                wave=wave_num,
                status="success",
                duration_seconds=round(duration, 1),
            ))
            self.console.print(f"  [green]Captured output for {skill_id}[/green]")
            return True

        # Output not produced -- mark skipped.
        self._update_state(
            wave_num,
            skill_id,
            "text_skills",
            "skipped",
            duration_seconds=round(duration, 1),
        )
        # Track in report
        self._report.skills.append(SkillExecution(
            skill_id=skill_id,
            wave=wave_num,
            status="skipped",
            duration_seconds=round(duration, 1),
        ))
        self.console.print(f"  [yellow]Skipped {skill_id} (no output found)[/yellow]")
        return False

    # ------------------------------------------------------------------
    # Visual asset execution
    # ------------------------------------------------------------------

    def _execute_visual_assets(
        self,
        asset_ids: List[str],
        wave_num: int,
        parallel: bool = True,
    ) -> bool:
        """Group assets into batches and dispatch to the visual pipeline.

        Args:
            asset_ids: List of asset IDs to generate.
            wave_num: Wave number for state tracking.
            parallel: If True, run independent batches in parallel.

        Returns ``True`` when every batch succeeds.
        """
        script_path = PACKAGE_ROOT / "scripts" / "run_pipeline.py"
        if self._visual_backend.requires_script_path and not script_path.exists():
            self.console.print(
                f"[yellow]Visual pipeline script not found at "
                f"{script_path} -- skipping visual assets.[/yellow]"
            )
            for aid in asset_ids:
                self._update_state(wave_num, aid, "visual_assets", "skipped")
            return False

        if self._visual_backend.requires_script_path and not self._ensure_visual_bundle_ready(
            script_path
        ):
            for aid in asset_ids:
                self._update_state(
                    wave_num,
                    aid,
                    "visual_assets",
                    "failed",
                    error="Visual bundle preparation failed",
                )
            return False

        # Group by batch.
        batches: Dict[str, List[str]] = {}
        for aid in asset_ids:
            batch = self.ASSET_BATCH_MAP.get(aid, "misc")
            batches.setdefault(batch, []).append(aid)

        # Anchor batch must run first (style reference)
        anchor_batch = batches.pop("anchor", None)
        if anchor_batch:
            ok = self._run_single_batch("anchor", anchor_batch, wave_num, script_path)
            if not ok:
                return False
        
        # Run remaining batches (can be parallelized)
        if not batches:
            return True
        
        if parallel and len(batches) > 1:
            return self._run_batches_parallel(batches, wave_num, script_path)
        else:
            return self._run_batches_sequential(batches, wave_num, script_path)
    
    def _run_batches_parallel(
        self,
        batches: Dict[str, List[str]],
        wave_num: int,
        script_path: Path,
    ) -> bool:
        """Execute batches in parallel using ThreadPoolExecutor."""
        all_ok = True
        max_workers = min(len(batches), 8)  # Cap at 8 parallel batches (I/O-bound FAL API calls)
        
        self.console.print(
            f"  [cyan]Running {len(batches)} batches in parallel "
            f"(max {max_workers} workers)...[/cyan]"
        )
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._run_single_batch, batch_name, batch_asset_ids, wave_num, script_path
                ): batch_name
                for batch_name, batch_asset_ids in batches.items()
            }
            
            for future in as_completed(futures):
                batch_name = futures[future]
                try:
                    ok = future.result()
                    if not ok:
                        all_ok = False
                except Exception as exc:
                    all_ok = False
                    self.console.print(
                        f"  [red]Batch '{batch_name}' exception: {exc}[/red]"
                    )
        
        return all_ok
    
    def _run_batches_sequential(
        self,
        batches: Dict[str, List[str]],
        wave_num: int,
        script_path: Path,
    ) -> bool:
        """Execute batches sequentially."""
        all_ok = True
        for batch_name, batch_asset_ids in batches.items():
            ok = self._run_single_batch(batch_name, batch_asset_ids, wave_num, script_path)
            if not ok:
                all_ok = False
        return all_ok
    
    def _run_single_batch(
        self,
        batch_name: str,
        batch_asset_ids: List[str], 
        wave_num: int,
        script_path: Path,
    ) -> bool:
        """Run a single batch of visual assets."""
        # Mark all assets in the batch as in-progress.
        for aid in batch_asset_ids:
            self._update_state(wave_num, aid, "visual_assets", "in_progress")

        self.console.print(
            f"  [cyan]Running visual batch '{batch_name}' "
            f"({len(batch_asset_ids)} assets, backend={self._visual_backend.name})...[/cyan]"
        )

        start_ts = time.monotonic()

        timeout_seconds = int(
            self.config.get("generation", {}).get("batch_timeout_seconds", 1200)
        )
        timeout_seconds = max(60, timeout_seconds)

        try:
            result = self._visual_backend.run_batch(
                script_path=script_path,
                config_path=self.config_path,
                batch_name=batch_name,
                asset_ids=batch_asset_ids,
                timeout_seconds=timeout_seconds,
            )
            duration = round(time.monotonic() - start_ts, 1)
            self._record_batch_routing_decisions(batch_name=batch_name, wave_num=wave_num)
            error_msg = (result.stderr or result.stdout or "").strip()[:300]
            succeeded_asset_ids, failed_asset_ids = self._reconcile_batch_asset_results(
                batch_name=batch_name,
                batch_asset_ids=batch_asset_ids,
                wave_num=wave_num,
                duration=duration,
                error_msg=error_msg,
            )

            if not failed_asset_ids:
                batch_cost = len(succeeded_asset_ids) * PROVIDER_COSTS.get(self._provider, 0.08)
                self.console.print(
                    f"  [green]Batch '{batch_name}' completed "
                    f"({duration}s, ${batch_cost:.2f})[/green]"
                )
                return True

            if succeeded_asset_ids:
                self.console.print(
                    f"  [yellow]Batch '{batch_name}' partially completed "
                    f"({len(succeeded_asset_ids)}/{len(batch_asset_ids)} assets). "
                    f"Completed: {', '.join(succeeded_asset_ids)} | "
                    f"Missing: {', '.join(failed_asset_ids)}[/yellow]"
                )
            else:
                self.console.print(
                    f"  [red]Batch '{batch_name}' failed "
                    f"(exit {result.returncode})[/red]"
                )
            if error_msg:
                self.console.print(f"  [dim]{error_msg}[/dim]")
            return False

        except subprocess.TimeoutExpired:
            for aid in batch_asset_ids:
                self._update_state(
                    wave_num,
                    aid,
                    "visual_assets",
                    "failed",
                    error=f"Subprocess timed out after {timeout_seconds}s",
                )
                self._report.assets.append(AssetExecution(
                    asset_id=aid,
                    batch=batch_name,
                    status="failed",
                    error=f"Timeout after {timeout_seconds}s",
                ))
            self.console.print(
                f"  [red]Batch '{batch_name}' timed out.[/red]"
            )
            return False
        except Exception as exc:
            for aid in batch_asset_ids:
                self._update_state(
                    wave_num,
                    aid,
                    "visual_assets",
                    "failed",
                    error=str(exc)[:300],
                )
                self._report.assets.append(AssetExecution(
                    asset_id=aid,
                    batch=batch_name,
                    status="failed",
                    error=str(exc)[:100],
                ))
            self.console.print(
                f"  [red]Batch '{batch_name}' error: {exc}[/red]"
            )
            return False

    def _reconcile_batch_asset_results(
        self,
        *,
        batch_name: str,
        batch_asset_ids: List[str],
        wave_num: int,
        duration: float,
        error_msg: str,
    ) -> Tuple[List[str], List[str]]:
        """Reconcile batch results against actual generated files.

        Some provider-backed batches can partially succeed even when the batch
        wrapper exits non-zero. We treat generated files as the source of truth
        per asset so later waves can resume from the real artifact state.
        """
        asset_cost = PROVIDER_COSTS.get(self._provider, 0.08)
        succeeded_asset_ids: List[str] = []
        failed_asset_ids: List[str] = []

        for aid in batch_asset_ids:
            outputs = self._generated_visual_outputs(aid)
            if outputs:
                succeeded_asset_ids.append(aid)
                self._actual_costs[aid] = asset_cost
                self._update_state(
                    wave_num,
                    aid,
                    "visual_assets",
                    "completed",
                    duration_seconds=duration,
                    cost_usd=asset_cost,
                )
                self._report.assets.append(
                    AssetExecution(
                        asset_id=aid,
                        batch=batch_name,
                        status="success",
                        provider=self._provider,
                        cost_usd=asset_cost,
                        duration_seconds=duration / max(len(batch_asset_ids), 1),
                        file_path=str(outputs[0]),
                    )
                )
                continue

            failed_asset_ids.append(aid)
            self._update_state(
                wave_num,
                aid,
                "visual_assets",
                "failed",
                error=error_msg or "Batch did not produce expected output files",
            )
            self._report.assets.append(
                AssetExecution(
                    asset_id=aid,
                    batch=batch_name,
                    status="failed",
                    provider=self._provider,
                    error=(error_msg or "missing generated output")[:100],
                )
            )

        return succeeded_asset_ids, failed_asset_ids

    def _generated_visual_outputs(self, asset_id: str) -> List[Path]:
        """Return generated files whose basename starts with the asset prefix."""
        output_dir = self._resolve_visual_output_dir()
        matches: List[Path] = []
        for pattern in ("*.png", "*.svg", "*.webp"):
            matches.extend(
                path for path in output_dir.glob(pattern) if path.name.startswith(f"{asset_id}-")
            )
        return sorted(matches)

    def _resolve_visual_output_dir(self) -> Path:
        """Resolve the generated asset directory for the current brand config."""
        output_subdir = (
            str(self.config.get("generation", {}).get("output_dir", "generated")).strip()
            or "generated"
        )
        brand_name = str(self.config.get("brand", {}).get("name", "")).strip()
        brand_slug = re.sub(r"[^a-z0-9]+", "-", brand_name.lower()).strip("-")

        candidates: List[Path] = []
        if brand_slug:
            candidates.append(self.brand_dir / brand_slug / output_subdir)
        candidates.append(self.brand_dir / output_subdir)
        if brand_name:
            candidates.append(self.brand_dir / brand_name / output_subdir)

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0] if candidates else (self.brand_dir / output_subdir)

    def _ensure_visual_bundle_ready(self, script_path: Path) -> bool:
        """Generate the per-brand visual script bundle once per execution run.

        Fresh launches and resumed runs should not depend on a manually prepared
        ``brand_slug/scripts`` folder. Regenerate the bundle from the approved
        config before the first visual batch so Wave 3+ can run end-to-end.
        """
        if self._visual_bundle_prepared:
            return True

        python_executable = getattr(self._visual_backend, "python_executable", sys.executable)
        timeout_seconds = int(
            self.config.get("generation", {}).get("bundle_prepare_timeout_seconds", 300)
        )
        timeout_seconds = max(60, timeout_seconds)

        self.console.print(
            "  [cyan]Preparing visual bundle from approved config...[/cyan]"
        )

        try:
            result = subprocess.run(
                [
                    python_executable,
                    str(script_path),
                    "generate",
                    "--config",
                    str(self.config_path),
                ],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            self.console.print(
                "  [red]Visual bundle preparation timed out.[/red]"
            )
            return False
        except Exception as exc:
            self.console.print(
                f"  [red]Visual bundle preparation error: {exc}[/red]"
            )
            return False

        if result.returncode != 0:
            error_msg = (result.stderr or result.stdout or "").strip()[:500]
            self.console.print(
                "  [red]Visual bundle preparation failed.[/red]"
            )
            if error_msg:
                self.console.print(f"  [dim]{error_msg}[/dim]")
            return False

        self._visual_bundle_prepared = True
        self.console.print(
            "  [green]Visual bundle ready.[/green]"
        )
        return True

    # ------------------------------------------------------------------
    # Auto-hydration
    # ------------------------------------------------------------------

    def _record_batch_routing_decisions(self, *, batch_name: str, wave_num: int) -> None:
        """Append backend routing summaries to execution report when available."""
        getter = getattr(self._visual_backend, "get_batch_routing_summary", None)
        if not callable(getter):
            return
        try:
            rows = getter(batch_name)
        except Exception:
            return
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            entry = dict(row)
            entry.setdefault("batch", batch_name)
            entry.setdefault("wave", wave_num)
            self._report.routing_decisions.append(entry)

    def _run_hydration(self) -> None:
        """Inject completed text skill outputs into the brand config.

        Called automatically when transitioning from Wave 2 to Wave 3.
        Writes a .yaml.bak backup before mutating the config file.
        """
        if not self.upstream_data:
            self.console.print(
                "  [dim]No upstream data for hydration -- skipping.[/dim]"
            )
            return

        try:
            hydrate_brand_config(self.config, self.upstream_data)
            save_hydrated_config(self.config, self.config_path)
            count = len(self.upstream_data)
            self.console.print(
                f"  [green]Auto-hydrated brand config with "
                f"{count} skill output(s).[/green]"
            )
        except Exception as exc:
            self.console.print(
                f"  [red]Hydration failed: {exc}[/red]"
            )

    def _refresh_kickstarter_readiness(self) -> None:
        """Refresh the report snapshot for mandatory Kickstarter artifact coverage."""
        self._report.kickstarter_readiness = build_kickstarter_readiness(self.upstream_data)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _finalize_report(self, success: bool = True) -> None:
        """Finalize and save the execution report."""
        self._refresh_kickstarter_readiness()
        self._report.completed_at = datetime.now().isoformat()
        self._report.status = "completed" if success else "failed"
        
        # Calculate totals
        if self._report.started_at:
            start = datetime.fromisoformat(self._report.started_at)
            self._report.total_duration_seconds = (datetime.now() - start).total_seconds()
        
        # Costs
        self._report.actual_cost_usd = sum(self._actual_costs.values())
        self._report.estimated_cost_usd = sum(
            w.get("estimated_cost", 0) for w in self.state.waves.values()
        )
        
        # Count summaries
        self._report.skills_succeeded = sum(
            1 for s in self._report.skills if s.status == "success"
        )
        self._report.skills_failed = sum(
            1 for s in self._report.skills if s.status == "failed"
        )
        self._report.skills_skipped = sum(
            1 for s in self._report.skills if s.status == "skipped"
        )
        self._report.assets_generated = sum(
            1 for a in self._report.assets if a.status == "success"
        )
        self._report.assets_failed = sum(
            1 for a in self._report.assets if a.status == "failed"
        )
        
        # Save report
        save_report(self.config_path, self._report)
        
        # Display cost summary
        if self._actual_costs:
            variance = self._report.actual_cost_usd - self._report.estimated_cost_usd
            color = "green" if variance <= 0 else "yellow"
            self.console.print(
                f"\n[bold]Cost Summary:[/bold] "
                f"Estimated ${self._report.estimated_cost_usd:.2f} | "
                f"Actual [{color}]${self._report.actual_cost_usd:.2f}[/] | "
                f"Variance [{color}]${variance:+.2f}[/]"
            )

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _load_or_create_state(self) -> ExecutionState:
        """Resume from persisted state or create a fresh one."""
        if self.state_path.exists():
            try:
                state_data, was_repaired = load_state_safe(
                    self.state_path,
                    state_type="execution",
                )
                if was_repaired:
                    self.console.print(
                        "[yellow]Execution state was repaired and a corrupted backup was created.[/yellow]"
                    )
                return ExecutionState.model_validate(state_data)
            except Exception as exc:
                logger.warning("Failed to load execution state from %s: %s", self.state_path, exc)
                self.console.print(
                    f"[yellow]Could not load state ({exc}), "
                    f"starting fresh.[/yellow]"
                )

        brand_name = self.config.get("brand", {}).get("name", "unknown")
        return ExecutionState(
            brand=brand_name,
            started_at=datetime.now().isoformat(),
        )

    def _load_existing_outputs(self) -> None:
        """Pre-populate upstream_data from outputs already on disk."""
        if not self.outputs_dir.exists():
            return
        for output_file in self.outputs_dir.glob("*.json"):
            skill_id = output_file.stem
            if skill_id in self.upstream_data:
                continue
            try:
                data = json.loads(output_file.read_text(encoding="utf-8"))
                self.upstream_data[skill_id] = data
            except (json.JSONDecodeError, OSError):
                pass

    def _save_state(self) -> None:
        """Persist current execution state to disk."""
        self.state.updated_at = datetime.now().isoformat()
        saved = save_state_safe(
            self.state.model_dump(),
            self.state_path,
            state_type="execution",
        )
        if not saved:
            logger.error("Failed to save execution state to %s", self.state_path)
            self.console.print(
                "[yellow]Could not safely persist execution state; continuing with in-memory state.[/yellow]"
            )

    def _is_wave_complete(self, wave_num: int) -> bool:
        """Return True when the given wave is marked completed in state."""
        wave_data = self.state.waves.get(str(wave_num), {})
        return wave_data.get("status") == WaveStatus.COMPLETED.value

    def _is_skill_complete(self, skill_id: str) -> bool:
        """Check if a skill is marked completed in any wave."""
        for wave_data in self.state.waves.values():
            skills = wave_data.get("text_skills", {})
            if skills.get(skill_id, {}).get("status") == "completed":
                return True
            assets = wave_data.get("visual_assets", {})
            if assets.get(skill_id, {}).get("status") == "completed":
                return True
        return False

    def _dependencies_met(self, wave: Wave) -> bool:
        """Return True when every dependency wave is completed."""
        return all(self._is_wave_complete(dep) for dep in wave.depends_on)

    def _update_state(
        self,
        wave_num: int,
        item_id: str,
        item_type: str,
        status: str,
        **kwargs: Any,
    ) -> None:
        """Atomically update a single item in wave state and persist.

        Args:
            wave_num: The wave number owning the item.
            item_id: Skill or asset identifier.
            item_type: Either ``"text_skills"`` or ``"visual_assets"``.
            status: New status string.
            **kwargs: Additional fields (``duration_seconds``, ``error``).
        """
        wkey = str(wave_num)
        if wkey not in self.state.waves:
            self.state.waves[wkey] = {
                "status": WaveStatus.IN_PROGRESS.value,
                "text_skills": {},
                "visual_assets": {},
            }

        bucket = self.state.waves[wkey].setdefault(item_type, {})
        bucket[item_id] = {"status": status, **kwargs}
        self._save_state()

    # ------------------------------------------------------------------
    # Output polling
    # ------------------------------------------------------------------

    def _wait_for_output(
        self,
        skill_id: str,
        interactive: bool = True,
    ) -> Optional[dict]:
        """Wait for a skill output file to appear on disk.

        In interactive mode the user is prompted to press Enter once
        they have executed the prompt and saved the output.  In
        non-interactive mode the method polls for up to 300 seconds.

        Returns:
            Parsed JSON dict if the output file was found, else ``None``.
        """
        output_path = self.outputs_dir / f"{skill_id}.json"

        # Fast path: output already exists (e.g. prior run).
        data = self._try_load_output(output_path)
        if data is not None:
            return data

        if interactive:
            self.console.print(
                f"\n  [bold]Execute the prompt above and save output to:[/bold]"
                f"\n  [cyan]{output_path}[/cyan]\n"
            )

            try:
                proceed = Confirm.ask(
                    "  Press [bold]y[/bold] when output is ready "
                    "(or [bold]n[/bold] to skip)",
                    default=True,
                    console=self.console,
                )
            except (EOFError, KeyboardInterrupt):
                proceed = False

            if proceed:
                data = self._try_load_output(output_path)
                if data is not None:
                    return data

                # Brief polling window after user confirms.
                self.console.print(
                    "  [dim]Checking for output file...[/dim]"
                )
                for _ in range(15):
                    time.sleep(2)
                    data = self._try_load_output(output_path)
                    if data is not None:
                        return data

            return None

        # Non-interactive: poll with timeout.
        max_wait = 600
        interval = 2
        elapsed = 0

        self.console.print(
            f"  [dim]Waiting up to {max_wait}s for {output_path.name}...[/dim]"
        )

        while elapsed < max_wait:
            time.sleep(interval)
            elapsed += interval
            data = self._try_load_output(output_path)
            if data is not None:
                return data
            # Progress indicator every 30 seconds
            if elapsed % 30 == 0:
                self.console.print(
                    f"  [dim]Still waiting... {elapsed}s / {max_wait}s for {output_path.name}[/dim]"
                )

        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _try_load_output(path: Path) -> Optional[dict]:
        """Attempt to load and parse a JSON output file.

        Returns ``None`` when the file does not exist or is not valid JSON.
        """
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            return None
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _create_stub_skill(skill_id: str) -> UnifiedSkill:
        """Create a minimal UnifiedSkill for an unregistered skill ID."""
        return UnifiedSkill(
            id=skill_id,
            name=skill_id.replace("-", " ").title(),
            source=SkillSource.ORCHESTRATOR,
            description=f"Auto-generated stub for {skill_id}",
        )

    def _resolve_waves(self, wave_range: Optional[range]) -> List[Wave]:
        """Filter waves to those within the requested range."""
        if wave_range is None:
            return list(self.waves)
        return [w for w in self.waves if w.number in wave_range]
