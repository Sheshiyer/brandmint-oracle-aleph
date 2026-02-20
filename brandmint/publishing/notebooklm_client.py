"""
NotebookLM CLI wrapper — subprocess interface with retry logic.

Wraps the ``notebooklm`` CLI (notebooklm-py >= 0.3.2) with:
- JSON output parsing (``--json`` flag)
- Parallel safety (``-n <notebook_id>`` everywhere)
- Exponential backoff on rate limits
- Timeout handling per operation type
"""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
RETRY_BASE_DELAY = 30  # seconds

TIMEOUT_SOURCE = 600    # 10 min per source
TIMEOUT_ARTIFACT = 1200 # 20 min per artifact
TIMEOUT_COMMAND = 120   # 2 min for quick commands


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class CLIResult:
    """Result from a notebooklm CLI invocation."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class NotebookLMClient:
    """Subprocess wrapper around the ``notebooklm`` CLI."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    # -- Preflight ---------------------------------------------------------

    def check_installed(self) -> bool:
        """Return True if the notebooklm CLI is available."""
        try:
            r = subprocess.run(
                ["notebooklm", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def check_authenticated(self) -> bool:
        """Return True if the CLI has valid authentication."""
        r = self._run(["notebooklm", "status"], timeout=15)
        return r.success

    # -- Notebooks ---------------------------------------------------------

    def create_notebook(self, title: str) -> str:
        """Create a notebook and return its ID."""
        r = self._run_json(["notebooklm", "create", title, "--json"])
        if not r.success:
            raise RuntimeError(f"Failed to create notebook: {r.stderr}")
        return r.data.get("id") or r.data.get("notebook_id", "")

    def list_notebooks(self) -> List[Dict[str, Any]]:
        """List all notebooks."""
        r = self._run_json(["notebooklm", "list", "--json"])
        if not r.success:
            return []
        return r.data.get("notebooks", [])

    # -- Sources -----------------------------------------------------------

    def add_source(self, file_path: str, notebook_id: str) -> str:
        """Add a source file to a notebook. Returns source_id."""
        r = self._run_json([
            "notebooklm", "source", "add", file_path,
            "--notebook", notebook_id, "--json",
        ])
        if not r.success:
            raise RuntimeError(f"Failed to add source {file_path}: {r.stderr}")
        return r.data.get("source_id", "")

    def wait_for_source(
        self, source_id: str, notebook_id: str, timeout: int = TIMEOUT_SOURCE,
    ) -> bool:
        """Wait for a source to finish indexing. Returns True on success."""
        r = self._run([
            "notebooklm", "source", "wait", source_id,
            "-n", notebook_id, "--timeout", str(timeout),
        ], timeout=timeout + 30)
        return r.success

    def list_sources(self, notebook_id: str) -> List[Dict[str, Any]]:
        """List sources in a notebook."""
        r = self._run_json([
            "notebooklm", "source", "list",
            "--notebook", notebook_id, "--json",
        ])
        if not r.success:
            return []
        return r.data.get("sources", [])

    # -- Artifacts ---------------------------------------------------------

    def generate_artifact(
        self,
        artifact_type: str,
        notebook_id: str,
        instructions: str = "",
        extra_args: Optional[List[str]] = None,
    ) -> str:
        """Start artifact generation. Returns artifact_id or task_id."""
        cmd = ["notebooklm", "generate", artifact_type]
        if instructions:
            cmd.append(instructions)
        cmd.extend(["-n", notebook_id, "--json"])
        if extra_args:
            cmd.extend(extra_args)

        r = self._run_json(cmd, retries=MAX_RETRIES)
        if not r.success:
            raise RuntimeError(
                f"Failed to generate {artifact_type}: {r.stderr}"
            )
        return (
            r.data.get("artifact_id")
            or r.data.get("task_id")
            or r.data.get("id", "")
        )

    def wait_for_artifact(
        self, artifact_id: str, notebook_id: str, timeout: int = TIMEOUT_ARTIFACT,
    ) -> bool:
        """Wait for artifact generation to complete."""
        r = self._run([
            "notebooklm", "artifact", "wait", artifact_id,
            "-n", notebook_id, "--timeout", str(timeout),
        ], timeout=timeout + 30)
        return r.success

    def list_artifacts(self, notebook_id: str) -> List[Dict[str, Any]]:
        """List artifacts in a notebook."""
        r = self._run_json([
            "notebooklm", "artifact", "list",
            "--notebook", notebook_id, "--json",
        ])
        if not r.success:
            return []
        return r.data.get("artifacts", [])

    # -- Downloads ---------------------------------------------------------

    def download_artifact(
        self,
        artifact_type: str,
        output_path: str,
        artifact_id: str,
        notebook_id: str,
    ) -> bool:
        """Download a generated artifact to disk."""
        r = self._run([
            "notebooklm", "download", artifact_type, output_path,
            "-a", artifact_id, "-n", notebook_id,
        ], timeout=TIMEOUT_COMMAND)
        if r.success:
            p = Path(output_path)
            return p.exists() and p.stat().st_size > 0
        return False

    # -- Internal ----------------------------------------------------------

    def _run(
        self,
        cmd: List[str],
        timeout: int = TIMEOUT_COMMAND,
        retries: int = 1,
    ) -> CLIResult:
        """Execute a CLI command with optional retry."""
        last_err = ""
        for attempt in range(retries):
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout,
                )
                if proc.returncode == 0:
                    return CLIResult(
                        success=True,
                        stdout=proc.stdout,
                        stderr=proc.stderr,
                        exit_code=0,
                    )
                last_err = proc.stderr.strip()

                # Rate limit — retry with backoff
                if self._is_rate_limited(last_err) and attempt < retries - 1:
                    delay = RETRY_BASE_DELAY * (attempt + 1)
                    self.console.print(
                        f"  [yellow]Rate limited, retrying in {delay}s...[/yellow]"
                    )
                    time.sleep(delay)
                    continue

                # Non-retryable error
                break

            except subprocess.TimeoutExpired:
                last_err = f"Command timed out after {timeout}s"
                break

        return CLIResult(
            success=False,
            stderr=last_err,
            exit_code=getattr(proc, "returncode", 1) if "proc" in dir() else 1,
        )

    def _run_json(
        self,
        cmd: List[str],
        timeout: int = TIMEOUT_COMMAND,
        retries: int = 1,
    ) -> CLIResult:
        """Execute a CLI command and parse JSON output."""
        result = self._run(cmd, timeout=timeout, retries=retries)
        if result.success and result.stdout.strip():
            try:
                result.data = json.loads(result.stdout)
            except json.JSONDecodeError:
                result.data = {}
        return result

    @staticmethod
    def _is_rate_limited(stderr: str) -> bool:
        """Detect rate limiting from stderr."""
        lower = stderr.lower()
        return "rate limit" in lower or "429" in lower or "quota" in lower
