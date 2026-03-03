"""
NotebookLM Publisher — orchestrates notebook creation, source upload,
artifact generation, and download.

This is the main entry point called by the Wave 7 post_hook in executor.py
or by ``bm publish notebooklm`` standalone CLI command.

Generates all 9 NotebookLM artifact types with multiple variations (~25
artifacts per project) using a 5-phase execution strategy:
  instant → slow-start → parallel-1 → parallel-2 → slow-poll
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .instruction_templates import (
    DEFAULT_ARTIFACT_DEFINITIONS,
    LEGACY_ID_MAP,
    ext_for_type,
    estimate_for_type,
    phase_for_type,
    resolve_video_style,
)
from .notebooklm_client import NotebookLMClient
from .source_builder import build_source_documents
from .source_curator import SourceCurator, SourceCandidate


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def _load_state(path: Path) -> dict:
    """Load publisher state from disk, or return empty state."""
    if path.is_file():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state: dict, path: Path) -> None:
    """Persist publisher state to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

class NotebookLMPublisher:
    """Orchestrate NotebookLM notebook creation and artifact generation."""

    def __init__(
        self,
        brand_dir: Path,
        config: dict,
        config_path: Path,
        console: Optional[Console] = None,
        artifact_filter: Optional[Set[str]] = None,
        force: bool = False,
        max_sources: int = 50,
        synthesize: bool = True,
        synthesis_model: str = "",
        max_parallel: int = 3,
    ):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.config_path = Path(config_path)
        self.console = console or Console()
        self.artifact_filter = artifact_filter
        self.force = force
        self.max_sources = max_sources
        self.synthesize = synthesize
        self.synthesis_model = synthesis_model

        # NotebookLM config overrides from brand-config.yaml
        nb_config = config.get("notebooklm", {})
        artifacts_config = nb_config.get("artifacts", {})
        self.max_parallel = nb_config.get("max_parallel_workers", max_parallel)
        self.inter_artifact_delay = nb_config.get("inter_artifact_delay", 2.0)
        self.video_style_override = artifacts_config.get("video_style")
        self.disabled_artifacts: Set[str] = set(artifacts_config.get("disabled", []))
        self.custom_artifacts: List[dict] = artifacts_config.get("custom", [])

        # Derived paths
        self.outputs_dir = self.brand_dir / ".brandmint" / "outputs"
        self.deliverables_dir = self.brand_dir / "deliverables" / "notebooklm"
        self.sources_dir = self.deliverables_dir / "sources"
        self.artifacts_dir = self.deliverables_dir / "artifacts"
        self.state_path = self.brand_dir / ".brandmint" / "notebooklm-state.json"
        self.report_path = self.deliverables_dir / "publish-report.json"

        # State
        self.state: dict = {} if force else _load_state(self.state_path)
        self.client = NotebookLMClient(console=self.console)

        # Brand info
        self.brand_name = config.get("brand", {}).get("name", "Brand")

    def publish(self) -> bool:
        """Run the full publish pipeline. Returns True on success."""
        started = time.time()
        artifact_defs = self._build_artifact_defs()

        self.console.print(
            Panel(
                f"[bold]NotebookLM Publisher[/bold]\n"
                f"Brand: {self.brand_name}\n"
                f"Outputs: {self.outputs_dir}\n"
                f"Deliverables: {self.deliverables_dir}\n"
                f"Artifacts: {len(artifact_defs)} configured",
                title="[cyan]Wave 7: Publishing[/cyan]",
                border_style="cyan",
            )
        )

        # Step 1: Preflight
        if not self._preflight():
            return False

        # Step 2: Create or reuse notebook
        notebook_id = self._ensure_notebook()
        if not notebook_id:
            return False

        # Step 3: Build and curate source documents
        curated = self._build_sources()
        if not curated:
            self.console.print("[red]No source documents generated.[/red]")
            return False

        # Step 4: Upload curated sources
        self._upload_sources(curated, notebook_id)

        # Step 5: Wait for source indexing
        self._wait_for_indexing(notebook_id)

        # Step 6-8: Generate, wait, download artifacts
        self._generate_artifacts(notebook_id, artifact_defs)
        self._wait_for_artifacts(notebook_id)
        self._download_artifacts(notebook_id, artifact_defs)

        # Step 9: Save report
        elapsed = time.time() - started
        self._save_report(elapsed, artifact_defs)
        self.state["updated_at"] = datetime.now().isoformat()
        _save_state(self.state, self.state_path)

        # Summary
        self._print_summary(elapsed, artifact_defs)
        return True

    def dry_run(self) -> None:
        """Show what would be done without executing."""
        artifact_defs = self._build_artifact_defs()
        self.console.print(
            Panel(
                f"[bold]NotebookLM Publisher — Dry Run[/bold]\n"
                f"Brand: {self.brand_name}\n"
                f"Source budget: {self.max_sources}\n"
                f"Artifacts: {len(artifact_defs)} configured",
                title="[yellow]Dry Run[/yellow]",
                border_style="yellow",
            )
        )

        # Check outputs
        outputs = list(self.outputs_dir.glob("*.json")) if self.outputs_dir.is_dir() else []
        self.console.print(f"\n[bold]Available outputs:[/bold] {len(outputs)} JSON files")
        for f in sorted(outputs):
            self.console.print(f"  - {f.stem}")

        # Build prose docs (non-destructive) so curator can scan them
        self.console.print(f"\n[bold]Building prose source documents...[/bold]")
        prose_paths = build_source_documents(
            outputs_dir=self.outputs_dir,
            config=self.config,
            config_path=self.config_path,
            brand_dir=self.brand_dir,
            output_dir=self.sources_dir,
            synthesize=self.synthesize,
            model=self.synthesis_model,
            console=self.console,
        )
        for gid, path in prose_paths.items():
            size_kb = path.stat().st_size / 1024
            self.console.print(f"  [green]✓[/green] {gid}.md ({size_kb:.1f} KB)")

        # Run curator in analysis mode
        curator = SourceCurator(
            brand_dir=self.brand_dir,
            config=self.config,
            max_sources=self.max_sources,
            sources_dir=self.sources_dir,
        )
        curator.curate()
        self.console.print(f"\n{curator.report()}")

        # Artifacts by phase
        self.console.print(f"\n[bold]Artifacts to generate:[/bold] {len(artifact_defs)}")
        phase_order = ["instant", "slow", "parallel-1", "parallel-2"]
        for phase in phase_order:
            phase_defs = [d for d in artifact_defs if d["phase"] == phase]
            if not phase_defs:
                continue
            self.console.print(f"\n  [bold]{phase}[/bold] ({len(phase_defs)} artifacts):")
            for adef in phase_defs:
                extra = " ".join(adef.get("extra_args", []))
                desc = adef.get("description", "")
                self.console.print(
                    f"    - {adef['id']}: {adef['type']} → {adef['output_filename']} "
                    f"(~{adef['estimated_minutes']} min)"
                    f"{f'  [{extra}]' if extra else ''}"
                )

        # Time estimation
        slow_max = max(
            (d["estimated_minutes"] for d in artifact_defs if d["phase"] == "slow"),
            default=0,
        )
        p1_total = sum(d["estimated_minutes"] for d in artifact_defs if d["phase"] == "parallel-1")
        p2_total = sum(d["estimated_minutes"] for d in artifact_defs if d["phase"] == "parallel-2")
        parallel_est = (p1_total / self.max_parallel) + (p2_total / self.max_parallel)
        # Slow artifacts run concurrently with parallel phases
        wall_clock = max(slow_max, parallel_est) + 5  # +5 for instant + overhead
        sequential_total = sum(d["estimated_minutes"] for d in artifact_defs)
        self.console.print(
            f"\n[bold]Estimated time:[/bold] ~{int(wall_clock)} min "
            f"(5-phase execution, {self.max_parallel} workers) / "
            f"~{sequential_total} min (sequential)"
        )

    # -- Artifact definition builder ----------------------------------------

    def _build_artifact_defs(self) -> List[dict]:
        """Build artifact definitions from defaults + config overrides.

        1. Start with DEFAULT_ARTIFACT_DEFINITIONS
        2. Remove disabled artifacts
        3. Add custom artifacts from brand-config.yaml
        4. Resolve video style from brand archetype or config override
        5. Apply artifact filter (--artifacts CLI flag)
        """
        defs = list(DEFAULT_ARTIFACT_DEFINITIONS)

        # Remove disabled
        if self.disabled_artifacts:
            defs = [d for d in defs if d["id"] not in self.disabled_artifacts]

        # Add custom artifacts
        for custom in self.custom_artifacts:
            ctype = custom.get("type", "")
            defs.append({
                "id": custom["id"],
                "type": ctype,
                "instructions_fn": None,  # custom uses description as instructions
                "output_filename": f"{custom['id']}.{ext_for_type(ctype)}",
                "download_type": ctype,
                "estimated_minutes": estimate_for_type(ctype),
                "phase": phase_for_type(ctype),
                "extra_args": custom.get("extra_args", []),
                "group": ctype,
                "description": custom.get("description", ""),
            })

        # Resolve video style
        video_style = self.video_style_override or resolve_video_style(self.config)
        if video_style and video_style != "auto":
            for d in defs:
                if d["type"] == "video":
                    args = list(d.get("extra_args", []))
                    if "--style" in args:
                        idx = args.index("--style")
                        args[idx + 1] = video_style
                    else:
                        args.extend(["--style", video_style])
                    d["extra_args"] = args

        # Apply artifact filter
        return self._apply_filter(defs)

    def _apply_filter(self, defs: List[dict]) -> List[dict]:
        """Filter artifact definitions by --artifacts CLI flag.

        Supports:
        - Exact ID match: ``deck-detailed-full``
        - Type match: ``slide-deck`` (all slide-deck variations)
        - Group match: ``slide-deck`` (via group field)
        - Legacy alias: ``brand-overview-deck`` → ``deck-detailed-full``
        """
        if not self.artifact_filter:
            return defs

        # Resolve legacy aliases
        resolved_filter: Set[str] = set()
        for f in self.artifact_filter:
            resolved_filter.add(LEGACY_ID_MAP.get(f, f))

        return [
            d for d in defs
            if d["id"] in resolved_filter
            or d["type"] in resolved_filter
            or d.get("group") in resolved_filter
        ]

    # -- Internal steps ----------------------------------------------------

    def _preflight(self) -> bool:
        """Check CLI is installed (auto-install if missing) and authenticated."""
        if not self.client.check_installed():
            self.console.print(
                "  [yellow]notebooklm CLI not found — installing notebooklm-py...[/yellow]"
            )
            if not self._auto_install_notebooklm():
                self.console.print(
                    "[red]Auto-install failed.[/red]\n"
                    "Install manually: [bold]pip install notebooklm-py[/bold]\n"
                    "Then run: [bold]notebooklm login[/bold]"
                )
                return False

            if not self.client.check_installed():
                self.console.print(
                    "[red]notebooklm CLI still not found after install.[/red]\n"
                    "Install manually: [bold]pip install notebooklm-py[/bold]"
                )
                return False
            self.console.print("  [green]✓[/green] notebooklm-py installed successfully")

        if not self.client.check_authenticated():
            self.console.print(
                "[red]NotebookLM authentication required.[/red]\n"
                "Run: [bold]notebooklm login[/bold]"
            )
            return False

        self.console.print("  [green]✓[/green] NotebookLM CLI ready")
        return True

    @staticmethod
    def _auto_install_notebooklm() -> bool:
        """Attempt to pip-install notebooklm-py into the current environment."""
        import subprocess as _sp
        import sys

        try:
            proc = _sp.run(
                [sys.executable, "-m", "pip", "install", "notebooklm-py"],
                capture_output=True, text=True, timeout=120,
            )
            return proc.returncode == 0
        except (FileNotFoundError, _sp.TimeoutExpired):
            return False

    def _ensure_notebook(self) -> Optional[str]:
        """Create or reuse a notebook. Returns notebook_id or None."""
        existing_id = self.state.get("notebook_id")
        if existing_id and not self.force:
            self.console.print(
                f"  [green]✓[/green] Reusing notebook: {existing_id[:12]}..."
            )
            return existing_id

        title = f"{self.brand_name} — Brand Intelligence"
        self.console.print(f"  Creating notebook: [bold]{title}[/bold]")
        try:
            notebook_id = self.client.create_notebook(title)
            self.state["notebook_id"] = notebook_id
            self.state["notebook_title"] = title
            self.state["created_at"] = datetime.now().isoformat()
            self.state.setdefault("sources", {})
            self.state.setdefault("artifacts", {})
            _save_state(self.state, self.state_path)
            self.console.print(
                f"  [green]✓[/green] Notebook created: {notebook_id[:12]}..."
            )
            return notebook_id
        except RuntimeError as e:
            self.console.print(f"  [red]Failed to create notebook: {e}[/red]")
            return None

    def _build_sources(self) -> List[SourceCandidate]:
        """Build prose docs, then curate optimal source set."""
        self.console.print("\n[bold]Building prose source documents...[/bold]")
        prose_paths = build_source_documents(
            outputs_dir=self.outputs_dir,
            config=self.config,
            config_path=self.config_path,
            brand_dir=self.brand_dir,
            output_dir=self.sources_dir,
            synthesize=self.synthesize,
            model=self.synthesis_model,
            console=self.console,
        )
        for gid, path in prose_paths.items():
            size_kb = path.stat().st_size / 1024
            self.console.print(f"  [green]✓[/green] {gid}.md ({size_kb:.1f} KB)")

        self.console.print("\n[bold]Curating sources...[/bold]")
        curator = SourceCurator(
            brand_dir=self.brand_dir,
            config=self.config,
            max_sources=self.max_sources,
            sources_dir=self.sources_dir,
        )
        selected = curator.curate()

        self.console.print(
            f"  [green]✓[/green] Selected {len(selected)} sources "
            f"(budget: {self.max_sources})"
        )
        type_counts: Dict[str, int] = {}
        for c in selected:
            type_counts[c.source_type] = type_counts.get(c.source_type, 0) + 1
        for stype, count in sorted(type_counts.items()):
            self.console.print(f"    {stype}: {count}")

        return selected

    def _upload_sources(
        self, curated: List[SourceCandidate], notebook_id: str,
    ) -> None:
        """Upload curated source candidates to the notebook."""
        self.console.print(
            f"\n[bold]Uploading {len(curated)} sources...[/bold]"
        )
        sources_state: dict = self.state.setdefault("sources", {})

        for candidate in curated:
            key = candidate.path.name
            existing = sources_state.get(key, {})
            if existing.get("status") == "indexed" and not self.force:
                self.console.print(
                    f"  [dim]⏭ {key} — already indexed[/dim]"
                )
                continue

            try:
                source_id = self.client.add_source(
                    str(candidate.path), notebook_id,
                )
                sources_state[key] = {
                    "source_id": source_id,
                    "source_type": candidate.source_type,
                    "score": round(candidate.score, 1),
                    "status": "processing",
                    "uploaded_at": datetime.now().isoformat(),
                }
                _save_state(self.state, self.state_path)
                self.console.print(
                    f"  [green]✓[/green] {key} uploaded "
                    f"({source_id[:12]}...) [{candidate.source_type}]"
                )
            except RuntimeError as e:
                self.console.print(f"  [red]✗ {key} failed: {e}[/red]")
                sources_state[key] = {"status": "failed", "error": str(e)}

    def _wait_for_indexing(self, notebook_id: str) -> None:
        """Wait for all sources to be indexed."""
        sources_state: dict = self.state.get("sources", {})
        pending = {
            gid: info["source_id"]
            for gid, info in sources_state.items()
            if info.get("status") == "processing" and info.get("source_id")
        }

        if not pending:
            self.console.print("  [dim]No sources pending indexing.[/dim]")
            return

        self.console.print(
            f"\n[bold]Waiting for {len(pending)} sources to index...[/bold]"
        )

        def _wait_one(gid: str, source_id: str) -> tuple:
            ok = self.client.wait_for_source(source_id, notebook_id)
            return gid, ok

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(_wait_one, gid, sid): gid
                for gid, sid in pending.items()
            }
            for future in as_completed(futures):
                gid = futures[future]
                try:
                    _, ok = future.result()
                    new_status = "indexed" if ok else "failed"
                    sources_state[gid]["status"] = new_status
                    icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
                    self.console.print(f"  {icon} {gid} — {new_status}")
                except Exception as e:
                    sources_state[gid]["status"] = "failed"
                    self.console.print(f"  [red]✗ {gid} — error: {e}[/red]")

        _save_state(self.state, self.state_path)

    # -- Artifact generation (5-phase) ------------------------------------

    def _generate_artifacts(
        self, notebook_id: str, artifact_defs: List[dict],
    ) -> None:
        """Generate all configured artifacts using 5-phase execution.

        Phase 1 (instant):    Mind map — synchronous, inline
        Phase 2 (slow-start): Video + audio — kicked off early, polled later
        Phase 3 (parallel-1): Decks + reports — parallel batch
        Phase 4 (parallel-2): Quiz, flashcards, infographic, data-table — parallel batch
        Phase 5 (slow-poll):  Handled by ``_wait_for_artifacts()``
        """
        self.console.print(
            f"\n[bold]Generating {len(artifact_defs)} artifacts "
            f"({self.max_parallel} workers)...[/bold]"
        )
        artifacts_state: dict = self.state.setdefault("artifacts", {})

        # Phase 1: instant (mind-map)
        for adef in artifact_defs:
            if adef["phase"] == "instant":
                self._generate_single(adef, notebook_id, artifacts_state)

        # Phase 2: kick off slow artifacts (video + audio) — fire and continue
        slow = [a for a in artifact_defs if a["phase"] == "slow"]
        if slow:
            self.console.print(
                f"\n  [bold]Phase 2:[/bold] Starting {len(slow)} slow artifacts "
                f"(video + audio)..."
            )
            for i, adef in enumerate(slow):
                self._generate_single(adef, notebook_id, artifacts_state)
                if i < len(slow) - 1:
                    time.sleep(5)  # Stagger to avoid burst rate limit

        # Phase 3: parallel batch 1 (decks + reports)
        parallel_1 = [a for a in artifact_defs if a["phase"] == "parallel-1"]
        if parallel_1:
            self.console.print(
                f"\n  [bold]Phase 3:[/bold] Generating {len(parallel_1)} decks + reports..."
            )
            self._run_parallel_batch(parallel_1, notebook_id, artifacts_state)

        # Cooldown between batches
        if parallel_1 and any(a["phase"] == "parallel-2" for a in artifact_defs):
            time.sleep(10)

        # Phase 4: parallel batch 2 (quiz, flashcards, infographic, data-table)
        parallel_2 = [a for a in artifact_defs if a["phase"] == "parallel-2"]
        if parallel_2:
            self.console.print(
                f"\n  [bold]Phase 4:[/bold] Generating {len(parallel_2)} "
                f"quiz + flashcards + infographic + tables..."
            )
            self._run_parallel_batch(parallel_2, notebook_id, artifacts_state)

        _save_state(self.state, self.state_path)

    def _run_parallel_batch(
        self,
        defs: List[dict],
        notebook_id: str,
        artifacts_state: dict,
    ) -> None:
        """Run a batch of artifacts with controlled parallelism."""
        if not defs:
            return
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            futures = {}
            for i, adef in enumerate(defs):
                if i > 0:
                    time.sleep(self.inter_artifact_delay)
                future = executor.submit(
                    self._generate_single, adef, notebook_id, artifacts_state,
                )
                futures[future] = adef["id"]
            for future in as_completed(futures):
                aid = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.console.print(
                        f"  [red]✗ {aid} generation failed: {e}[/red]"
                    )

    def _generate_single(
        self,
        adef: dict,
        notebook_id: str,
        artifacts_state: dict,
    ) -> None:
        """Generate a single artifact."""
        aid = adef["id"]

        # Skip if already generated
        existing = artifacts_state.get(aid, {})
        if existing.get("status") == "completed" and not self.force:
            self.console.print(f"  [dim]⏭ {aid} — already completed[/dim]")
            return

        # Build instructions
        instructions = ""
        if adef["instructions_fn"]:
            instructions = adef["instructions_fn"](self.config)
        elif adef.get("description"):
            # Custom artifacts use description as instructions
            instructions = adef["description"]

        # Resolve extra_args
        extra_args = adef.get("extra_args", [])
        if callable(extra_args):
            extra_args = extra_args(self.config)

        # Mind-map is returned inline by notebooklm CLI (not as async artifact)
        if adef["type"] == "mind-map":
            self.console.print(f"  ⏳ Generating {aid} ({adef['type']})...")
            try:
                payload = self.client.generate_mind_map(notebook_id)
                self.artifacts_dir.mkdir(parents=True, exist_ok=True)
                out_path = self.artifacts_dir / adef["output_filename"]
                out_path.write_text(json.dumps(payload, indent=2))
                artifacts_state[aid] = {
                    "artifact_id": payload.get("note_id", ""),
                    "status": "completed",
                    "type": adef["type"],
                    "started_at": datetime.now().isoformat(),
                    "downloaded": True,
                    "path": str(out_path),
                }
                _save_state(self.state, self.state_path)
                size_kb = out_path.stat().st_size / 1024
                self.console.print(
                    f"  [green]✓[/green] {aid} generated ({size_kb:.1f} KB)"
                )
            except RuntimeError as e:
                artifacts_state[aid] = {"status": "failed", "error": str(e)}
                self.console.print(f"  [red]✗ {aid} failed: {e}[/red]")
            return

        self.console.print(
            f"  ⏳ Generating {aid} ({adef['type']}"
            f"{' ' + ' '.join(extra_args) if extra_args else ''})..."
        )
        try:
            artifact_id = self.client.generate_artifact(
                artifact_type=adef["type"],
                notebook_id=notebook_id,
                instructions=instructions,
                extra_args=extra_args or None,
            )
            artifacts_state[aid] = {
                "artifact_id": artifact_id,
                "status": "pending",
                "type": adef["type"],
                "started_at": datetime.now().isoformat(),
            }
            _save_state(self.state, self.state_path)
            self.console.print(
                f"  [green]✓[/green] {aid} generation started ({artifact_id[:12]}...)"
            )
        except RuntimeError as e:
            artifacts_state[aid] = {"status": "failed", "error": str(e)}
            self.console.print(f"  [red]✗ {aid} failed: {e}[/red]")

    def _wait_for_artifacts(self, notebook_id: str) -> None:
        """Wait for all pending artifacts to complete (Phase 5: slow-poll)."""
        artifacts_state: dict = self.state.get("artifacts", {})
        pending = {
            aid: info["artifact_id"]
            for aid, info in artifacts_state.items()
            if info.get("status") == "pending" and info.get("artifact_id")
        }

        if not pending:
            return

        self.console.print(
            f"\n[bold]Phase 5:[/bold] Waiting for {len(pending)} artifacts "
            f"to complete..."
        )

        def _wait_one(aid: str, artifact_id: str) -> tuple:
            ok = self.client.wait_for_artifact(artifact_id, notebook_id)
            return aid, ok

        # Cap workers at max_parallel to avoid overwhelming the API
        workers = min(len(pending), self.max_parallel)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_wait_one, aid, art_id): aid
                for aid, art_id in pending.items()
            }
            for future in as_completed(futures):
                aid = futures[future]
                try:
                    _, ok = future.result()
                    new_status = "completed" if ok else "failed"
                    artifacts_state[aid]["status"] = new_status
                    icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
                    self.console.print(f"  {icon} {aid} — {new_status}")
                except Exception as e:
                    artifacts_state[aid]["status"] = "failed"
                    self.console.print(f"  [red]✗ {aid} — error: {e}[/red]")

        _save_state(self.state, self.state_path)

    def _download_artifacts(
        self, notebook_id: str, artifact_defs: List[dict],
    ) -> None:
        """Download all completed artifacts."""
        self.console.print("\n[bold]Downloading artifacts...[/bold]")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifacts_state: dict = self.state.get("artifacts", {})

        for adef in artifact_defs:
            aid = adef["id"]
            info = artifacts_state.get(aid, {})
            if info.get("status") != "completed":
                continue
            if info.get("downloaded") and not self.force:
                self.console.print(
                    f"  [dim]⏭ {aid} — already downloaded[/dim]"
                )
                continue

            artifact_id = info.get("artifact_id", "")
            output_path = self.artifacts_dir / adef["output_filename"]

            ok = self.client.download_artifact(
                artifact_type=adef["download_type"],
                output_path=str(output_path),
                artifact_id=artifact_id,
                notebook_id=notebook_id,
            )
            if ok:
                info["downloaded"] = True
                info["path"] = str(output_path)
                size_kb = output_path.stat().st_size / 1024
                self.console.print(
                    f"  [green]✓[/green] {adef['output_filename']} ({size_kb:.1f} KB)"
                )
            else:
                self.console.print(
                    f"  [red]✗ {adef['output_filename']} download failed[/red]"
                )

        _save_state(self.state, self.state_path)

    def _save_report(self, elapsed: float, artifact_defs: List[dict]) -> None:
        """Write the publish execution report."""
        self.deliverables_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "brand": self.brand_name,
            "notebook_id": self.state.get("notebook_id"),
            "sources": self.state.get("sources", {}),
            "artifacts": self.state.get("artifacts", {}),
            "artifact_count": len(artifact_defs),
            "elapsed_seconds": round(elapsed, 1),
            "completed_at": datetime.now().isoformat(),
        }
        self.report_path.write_text(json.dumps(report, indent=2))

    def _print_summary(self, elapsed: float, artifact_defs: List[dict]) -> None:
        """Print a final summary table."""
        table = Table(
            title="NotebookLM Publishing Summary",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Artifact")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("File")

        artifacts_state = self.state.get("artifacts", {})
        for adef in artifact_defs:
            aid = adef["id"]
            info = artifacts_state.get(aid, {})
            status = info.get("status", "skipped")
            style = {
                "completed": "[green]completed[/green]",
                "failed": "[red]failed[/red]",
                "pending": "[yellow]pending[/yellow]",
            }.get(status, f"[dim]{status}[/dim]")
            fpath = info.get("path", "—")
            if fpath != "—":
                fpath = Path(fpath).name
            table.add_row(aid, adef["type"], style, fpath)

        self.console.print()
        self.console.print(table)
        self.console.print(f"\n  Total time: {elapsed:.0f}s")
        self.console.print(
            f"  Deliverables: {self.deliverables_dir}"
        )
