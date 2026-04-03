"""
Preflight checks for X/Twitter automation.

Validates OAuth connection and required scopes before executing actions.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .x_actions import XAction


# Required OAuth 2.0 scopes per action
ACTION_SCOPES: Dict[XAction, Set[str]] = {
    XAction.POST_TWEET: {"tweet.write", "users.read"},
    XAction.POST_CREATE: {"tweet.write", "users.read"},
    XAction.POST_LIKE: {"like.write", "tweet.read", "users.read"},
    XAction.POST_RETWEET: {"tweet.write", "tweet.read", "users.read"},
    XAction.DM_SEND: {"dm.write", "dm.read", "users.read"},
    XAction.USER_FOLLOW: {"follows.write", "users.read"},
}


@dataclass
class PreflightCheck:
    """Result of a single preflight check."""
    name: str
    passed: bool
    message: str


@dataclass
class PreflightResult:
    """Aggregated preflight results."""
    checks: List[PreflightCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def summary(self) -> str:
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        return f"{passed}/{total} checks passed"

    def to_dict(self) -> Dict:
        return {
            "all_passed": self.all_passed,
            "summary": self.summary,
            "checks": [{"name": c.name, "passed": c.passed, "message": c.message} for c in self.checks],
        }


def check_api_key() -> PreflightCheck:
    """Check that INFERENCE_API_KEY is set."""
    key = os.environ.get("INFERENCE_API_KEY", "").strip()
    if key:
        masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
        return PreflightCheck(name="api_key", passed=True, message=f"INFERENCE_API_KEY is set ({masked})")
    return PreflightCheck(name="api_key", passed=False, message="INFERENCE_API_KEY is not set")


def check_x_oauth_token() -> PreflightCheck:
    """Check that X OAuth token is available."""
    token = os.environ.get("X_OAUTH_TOKEN", "").strip()
    if token:
        return PreflightCheck(name="x_oauth_token", passed=True, message="X_OAUTH_TOKEN is set")
    return PreflightCheck(name="x_oauth_token", passed=False, message="X_OAUTH_TOKEN is not set — required for X write actions")


def check_scopes_for_action(action: XAction, available_scopes: Optional[Set[str]] = None) -> PreflightCheck:
    """Check that required scopes are available for an action."""
    required = ACTION_SCOPES.get(action, set())
    if not required:
        return PreflightCheck(name=f"scopes_{action.value}", passed=True, message=f"No scopes required for {action.value}")

    if available_scopes is None:
        raw = os.environ.get("X_OAUTH_SCOPES", "").strip()
        available_scopes = set(raw.split(",")) if raw else set()

    if not available_scopes:
        return PreflightCheck(
            name=f"scopes_{action.value}", passed=False,
            message=f"X_OAUTH_SCOPES not set — {action.value} requires: {', '.join(sorted(required))}",
        )

    missing = required - available_scopes
    if missing:
        return PreflightCheck(
            name=f"scopes_{action.value}", passed=False,
            message=f"Missing scopes for {action.value}: {', '.join(sorted(missing))}",
        )
    return PreflightCheck(name=f"scopes_{action.value}", passed=True, message=f"All scopes present for {action.value}")


def run_preflight(actions: Optional[List[XAction]] = None) -> PreflightResult:
    """Run all preflight checks.

    Args:
        actions: Specific actions to check scopes for. If None, checks all.
    """
    result = PreflightResult()
    result.checks.append(check_api_key())
    result.checks.append(check_x_oauth_token())

    target_actions = actions or list(XAction)
    for action in target_actions:
        result.checks.append(check_scopes_for_action(action))

    return result
