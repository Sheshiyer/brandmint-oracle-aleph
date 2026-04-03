"""
X/Twitter action execution with dry-run support.

Routes X actions through inference-sh app endpoints:
  post-tweet, post-like, post-retweet, dm-send, user-follow
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Optional, Mapping


class XAction(str, Enum):
    POST_TWEET = "post-tweet"
    POST_CREATE = "post-create"
    POST_LIKE = "post-like"
    POST_RETWEET = "post-retweet"
    DM_SEND = "dm-send"
    USER_FOLLOW = "user-follow"


# Map actions to inference-sh app IDs
ACTION_APP_MAP: Dict[XAction, str] = {
    XAction.POST_TWEET: "infsh-x-post-tweet",
    XAction.POST_CREATE: "infsh-x-post-create",
    XAction.POST_LIKE: "infsh-x-post-like",
    XAction.POST_RETWEET: "infsh-x-post-retweet",
    XAction.DM_SEND: "infsh-x-dm-send",
    XAction.USER_FOLLOW: "infsh-x-user-follow",
}


@dataclass
class XActionRequest:
    """Request to execute an X action."""
    action: XAction
    payload: Dict[str, Any]
    dry_run: bool = False
    operator: str = ""


@dataclass
class XActionResult:
    """Result from an X action execution."""
    success: bool
    action: str
    dry_run: bool
    payload: Dict[str, Any] = field(default_factory=dict)
    response: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class XActionExecutor:
    """Execute X actions via inference-sh apps with dry-run support."""

    DEFAULT_BASE_URL = "https://api.inference.sh"
    DEFAULT_POLL_SECONDS = 2.0
    DEFAULT_TIMEOUT_SECONDS = 120.0

    SUCCESS_STATUSES = {"completed", "succeeded", "success", "done"}
    FAILURE_STATUSES = {"failed", "error", "cancelled", "canceled"}

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self._base_url = (base_url or os.environ.get("INFERENCE_BASE_URL", "").strip() or self.DEFAULT_BASE_URL).rstrip("/")
        self._api_key = api_key or os.environ.get("INFERENCE_API_KEY", "").strip()

    def _request_json(self, *, method: str, url: str, payload: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> Dict[str, Any]:
        data = None
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"X action API {method} {url} failed ({e.code}): {body[:240]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"X action API {method} {url} failed: {e}")

        return json.loads(body) if body else {}

    def _poll_task(self, task_id: str) -> Dict[str, Any]:
        max_wait = float(os.environ.get("INFERENCE_TASK_MAX_WAIT", self.DEFAULT_TIMEOUT_SECONDS))
        interval = float(os.environ.get("INFERENCE_TASK_POLL_INTERVAL", self.DEFAULT_POLL_SECONDS))
        start = time.time()
        last_payload: Dict[str, Any] = {}

        while time.time() - start < max_wait:
            task_payload = self._request_json(
                method="GET",
                url=f"{self._base_url}/api/v1/tasks/{task_id}",
            )
            last_payload = task_payload
            status = str(task_payload.get("status", "")).strip().lower()

            if status in self.FAILURE_STATUSES:
                raise RuntimeError(f"X action task {task_id} failed: status={status}")
            if status in self.SUCCESS_STATUSES:
                return task_payload
            time.sleep(interval)

        raise TimeoutError(f"X action task {task_id} did not complete within {max_wait:.0f}s")

    def execute(self, request: XActionRequest) -> XActionResult:
        """Execute an X action or return dry-run preview."""
        app_id = ACTION_APP_MAP.get(request.action)
        if not app_id:
            return XActionResult(
                success=False, action=request.action.value,
                dry_run=request.dry_run, payload=request.payload,
                error=f"Unknown action: {request.action.value}",
            )

        if request.dry_run:
            return XActionResult(
                success=True, action=request.action.value,
                dry_run=True, payload=request.payload,
                response={"would_execute": True, "app": app_id, "reason": "dry-run"},
            )

        if not self._api_key:
            return XActionResult(
                success=False, action=request.action.value,
                dry_run=False, payload=request.payload,
                error="INFERENCE_API_KEY not set",
            )

        try:
            run_resp = self._request_json(
                method="POST",
                url=f"{self._base_url}/api/v1/apps/run",
                payload={"app": app_id, "input": request.payload},
            )
            task_id = run_resp.get("task_id") or run_resp.get("taskId") or run_resp.get("id")
            if task_id:
                result = self._poll_task(str(task_id))
            else:
                result = run_resp

            return XActionResult(
                success=True, action=request.action.value,
                dry_run=False, payload=request.payload, response=result,
            )
        except Exception as e:
            return XActionResult(
                success=False, action=request.action.value,
                dry_run=False, payload=request.payload, error=str(e),
            )
