"""
Audit logging for X/Twitter automation.

Append-only JSONL log at .brandmint/x-audit.jsonl.
Records every action (including dry-runs) for compliance and debugging.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: str
    action: str
    payload_hash: str
    dry_run: bool
    success: bool
    operator: str
    error: Optional[str] = None
    response_summary: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class XAuditLog:
    """Append-only JSONL audit log for X actions."""

    def __init__(self, log_path: Optional[str] = None):
        self._log_path = Path(log_path) if log_path else Path(".brandmint/x-audit.jsonl")

    def _ensure_dir(self) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash_payload(payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def log_action(
        self,
        action: str,
        payload: Dict[str, Any],
        dry_run: bool,
        success: bool,
        operator: str = "",
        error: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Append an audit entry to the log."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            payload_hash=self._hash_payload(payload),
            dry_run=dry_run,
            success=success,
            operator=operator or os.environ.get("USER", "unknown"),
            error=error,
            response_summary=json.dumps(response)[:200] if response else None,
        )
        self._ensure_dir()
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")
        return entry

    def query(
        self,
        since: Optional[str] = None,
        action: Optional[str] = None,
        dry_run_only: bool = False,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit log entries with optional filters.

        Args:
            since: ISO date string (e.g., '2026-03-20') — entries on or after this date.
            action: Filter by action type (e.g., 'post-tweet').
            dry_run_only: If True, only return dry-run entries.
            limit: Maximum entries to return (newest first).
        """
        if not self._log_path.exists():
            return []

        entries: List[AuditEntry] = []
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if since and data.get("timestamp", "") < since:
                    continue
                if action and data.get("action") != action:
                    continue
                if dry_run_only and not data.get("dry_run"):
                    continue

                entries.append(AuditEntry(**{
                    k: data.get(k) for k in AuditEntry.__dataclass_fields__
                }))

        # Return newest first, limited
        entries.reverse()
        return entries[:limit]
