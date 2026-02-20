"""
NotebookLM Publisher — orchestrates notebook creation, source upload,
artifact generation, and download.

This is the main entry point called by the Wave 7 post_hook in executor.py
or by ``bm publish notebooklm`` standalone CLI command.
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

from .instruction_templates import ARTIFACT_DEFINITIONS
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
    ):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.config_path = Path(config_path)
        self.console = console or Console()
        self.artifact_filter = artifact_filter
        self.force = force
        self.max_sources = max_sources

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
        self.console.print(
            Panel(
                f"[bold]NotebookLM Publisher[/bold]\n"
                f"Brand: {self.brand_name}\n"
                f"Outputs: {self.outputs_dir}\n"
                f"Deliverables: {self.deliverables_dir}",
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

        # Step 6: Generate artifacts
        self._generate_artifacts(notebook_id)

        # Step 7: Wait for artifacts
        self._wait_for_artifacts(notebook_id)

        # Step 8: Download artifacts
        self._download_artifacts(notebook_id)

        # Step 9: Save report
        elapsed = time.time() - started
        self._save_report(elapsed)
        self.state["updated_at"] = datetime.now().isoformat()
        _save_state(self.state, self.state_path)

        # Summary
        self._print_summary(elapsed)
        return True

    def dry_run(self) -> None:
        """Show what would be done without executing."""
        self.console.print(
            Panel(
                f"[bold]NotebookLM Publisher — Dry Run[/bold]\n"
                f"Brand: {self.brand_name}\n"
                f"Source budget: {self.max_sources}",
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

        # Artifacts
        defs = self._filtered_artifact_defs()
        self.console.print(f"\n[bold]Artifacts to generate:[/bold] {len(defs)}")
        for adef in defs:
            self.console.print(
                f"  - {adef['id']}: {adef['type']} → {adef['output_filename']} "
                f"(~{adef['estimated_minutes']} min)"
            )

        total_min = sum(d["estimated_minutes"] for d in defs if d["phase"] != "instant")
        # Parallel cuts it roughly in half
        parallel_min = max(
            sum(d["estimated_minutes"] for d in defs if d["phase"] == "parallel") / 3,
            max((d["estimated_minutes"] for d in defs if d["phase"] == "sequential"), default=0),
        )
        self.console.print(
            f"\n[bold]Estimated time:[/bold] ~{int(parallel_min + 5)} min "
            f"(parallel execution) / ~{total_min} min (sequential)"
        )

    # -- Internal steps ----------------------------------------------------

    def _preflight(self) -> bool:
        """Check CLI is installed and authenticated."""
        if not self.client.check_installed():
            self.console.print(
                "[red]notebooklm CLI not found.[/red]\n"
                "Install with: [bold]pip install notebooklm-py[/bold]\n"
                "Then run: [bold]notebooklm login[/bold]"
            )
            return False

        if not self.client.check_authenticated():
            self.console.print(
                "[red]NotebookLM authentication failed.[/red]\n"
                "Run: [bold]notebooklm login[/bold]"
            )
            return False

        self.console.print("  [green]✓[/green] NotebookLM CLI ready")
        return True

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
        """Build prose docs, then curate optimal source set.

        Returns a list of :class:`SourceCandidate` objects ordered by score.
        """
        # Step 1: Build the 5 prose source documents (existing pipeline)
        self.console.print("\n[bold]Building prose source documents...[/bold]")
        prose_paths = build_source_documents(
            outputs_dir=self.outputs_dir,
            config=self.config,
            config_path=self.config_path,
            brand_dir=self.brand_dir,
            output_dir=self.sources_dir,
        )
        for gid, path in prose_paths.items():
            size_kb = path.stat().st_size / 1024
            self.console.print(f"  [green]✓[/green] {gid}.md ({size_kb:.1f} KB)")

        # Step 2: Curate from all available sources
        self.console.print("\n[bold]Curating sources...[/bold]")
        curator = SourceCurator(
            brand_dir=self.brand_dir,
            config=self.config,
            max_sources=self.max_sources,
            sources_dir=self.sources_dir,
        )
        selected = curator.curate()

        # Print curator summary
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
            # Use filename as unique key
            key = candidate.path.name

            # Skip if already uploaded
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

    def _generate_artifacts(self, notebook_id: str) -> None:
        """Generate all configured artifacts."""
        self.console.print("\n[bold]Generating artifacts...[/bold]")
        artifacts_state: dict = self.state.setdefault("artifacts", {})
        defs = self._filtered_artifact_defs()

        # Phase 1: Instant artifacts (mind map)
        for adef in defs:
            if adef["phase"] != "instant":
                continue
            self._generate_single(adef, notebook_id, artifacts_state)

        # Phase 2: Parallel artifacts (decks + report)
        parallel = [a for a in defs if a["phase"] == "parallel"]
        if parallel:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(
                        self._generate_single, adef, notebook_id, artifacts_state,
                    ): adef["id"]
                    for adef in parallel
                }
                for future in as_completed(futures):
                    aid = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        self.console.print(
                            f"  [red]✗ {aid} generation failed: {e}[/red]"
                        )

        # Phase 3: Sequential artifacts (audio)
        for adef in defs:
            if adef["phase"] != "sequential":
                continue
            self._generate_single(adef, notebook_id, artifacts_state)

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

        self.console.print(
            f"  ⏳ Generating {aid} ({adef['type']})..."
        )
        try:
            artifact_id = self.client.generate_artifact(
                artifact_type=adef["type"],
                notebook_id=notebook_id,
                instructions=instructions,
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
        """Wait for all pending artifacts to complete."""
        artifacts_state: dict = self.state.get("artifacts", {})
        pending = {
            aid: info["artifact_id"]
            for aid, info in artifacts_state.items()
            if info.get("status") == "pending" and info.get("artifact_id")
        }

        if not pending:
            return

        self.console.print(
            f"\n[bold]Waiting for {len(pending)} artifacts to complete...[/bold]"
        )

        def _wait_one(aid: str, artifact_id: str) -> tuple:
            ok = self.client.wait_for_artifact(artifact_id, notebook_id)
            return aid, ok

        with ThreadPoolExecutor(max_workers=len(pending)) as executor:
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

    def _download_artifacts(self, notebook_id: str) -> None:
        """Download all completed artifacts."""
        self.console.print("\n[bold]Downloading artifacts...[/bold]")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifacts_state: dict = self.state.get("artifacts", {})
        defs = self._filtered_artifact_defs()

        for adef in defs:
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

    def _save_report(self, elapsed: float) -> None:
        """Write the publish execution report."""
        self.deliverables_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "brand": self.brand_name,
            "notebook_id": self.state.get("notebook_id"),
            "sources": self.state.get("sources", {}),
            "artifacts": self.state.get("artifacts", {}),
            "elapsed_seconds": round(elapsed, 1),
            "completed_at": datetime.now().isoformat(),
        }
        self.report_path.write_text(json.dumps(report, indent=2))

    def _print_summary(self, elapsed: float) -> None:
        """Print a final summary table."""
        table = Table(
            title="NotebookLM Publishing Summary",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Artifact")
        table.add_column("Status")
        table.add_column("File")

        artifacts_state = self.state.get("artifacts", {})
        for adef in self._filtered_artifact_defs():
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
            table.add_row(aid, style, fpath)

        self.console.print()
        self.console.print(table)
        self.console.print(f"\n  Total time: {elapsed:.0f}s")
        self.console.print(
            f"  Deliverables: {self.deliverables_dir}"
        )

    def _filtered_artifact_defs(self) -> List[dict]:
        """Return artifact definitions, optionally filtered."""
        if self.artifact_filter:
            return [
                d for d in ARTIFACT_DEFINITIONS
                if d["id"] in self.artifact_filter
            ]
        return list(ARTIFACT_DEFINITIONS)
