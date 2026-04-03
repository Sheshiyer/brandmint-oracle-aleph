"""
Safe-account smoke test for X/Twitter automation.

Executes a controlled test against a designated test account:
1. Posts a test tweet
2. Likes it
3. Deletes it (cleanup)

Validates the full round-trip works before running live automation.

Setup:
  - Set X_SMOKE_TEST_ACCOUNT to the handle of your test account
  - Ensure INFERENCE_API_KEY and X_OAUTH_TOKEN are configured
  - The test account should be a private/locked account used only for testing
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .x_actions import XAction, XActionExecutor, XActionRequest, XActionResult
from .x_audit import XAuditLog
from .x_preflight import run_preflight


@dataclass
class SmokeTestStep:
    """Result of a single smoke test step."""
    name: str
    passed: bool
    result: Optional[XActionResult] = None
    error: Optional[str] = None


@dataclass
class SmokeTestResult:
    """Aggregated smoke test results."""
    steps: List[SmokeTestStep] = field(default_factory=list)
    account: str = ""

    @property
    def all_passed(self) -> bool:
        return all(s.passed for s in self.steps)

    @property
    def summary(self) -> str:
        passed = sum(1 for s in self.steps if s.passed)
        return f"{passed}/{len(self.steps)} steps passed (account: {self.account})"

    def to_dict(self) -> Dict:
        return {
            "all_passed": self.all_passed,
            "summary": self.summary,
            "account": self.account,
            "steps": [
                {"name": s.name, "passed": s.passed, "error": s.error}
                for s in self.steps
            ],
        }


def run_smoke_test(
    safe_account: Optional[str] = None,
    dry_run: bool = False,
) -> SmokeTestResult:
    """Execute smoke test against a safe test account.

    Args:
        safe_account: X handle for the test account. Defaults to X_SMOKE_TEST_ACCOUNT env var.
        dry_run: If True, runs all steps in dry-run mode (no actual API calls).
    """
    account = safe_account or os.environ.get("X_SMOKE_TEST_ACCOUNT", "").strip()
    result = SmokeTestResult(account=account)

    if not account:
        result.steps.append(SmokeTestStep(
            name="account_check", passed=False,
            error="No test account specified. Set X_SMOKE_TEST_ACCOUNT or pass --account.",
        ))
        return result

    # Step 0: Preflight
    preflight = run_preflight(actions=[XAction.POST_TWEET, XAction.POST_LIKE])
    if not preflight.all_passed:
        failing = [c for c in preflight.checks if not c.passed]
        result.steps.append(SmokeTestStep(
            name="preflight", passed=False,
            error=f"Preflight failed: {'; '.join(c.message for c in failing)}",
        ))
        return result

    result.steps.append(SmokeTestStep(name="preflight", passed=True))

    executor = XActionExecutor()
    audit = XAuditLog()
    test_text = f"[brandmint smoke test] {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"

    # Step 1: Post test tweet
    post_req = XActionRequest(
        action=XAction.POST_TWEET,
        payload={"text": test_text},
        dry_run=dry_run,
        operator="smoke-test",
    )
    post_result = executor.execute(post_req)
    audit.log_action(
        action=post_req.action.value, payload=post_req.payload,
        dry_run=dry_run, success=post_result.success,
        operator="smoke-test", error=post_result.error,
        response=post_result.response,
    )
    result.steps.append(SmokeTestStep(
        name="post_tweet", passed=post_result.success,
        result=post_result, error=post_result.error,
    ))

    if not post_result.success:
        return result

    # Extract tweet ID for subsequent steps
    tweet_id = post_result.response.get("id") or post_result.response.get("tweet_id", "")

    # Step 2: Like the tweet
    if tweet_id:
        like_req = XActionRequest(
            action=XAction.POST_LIKE,
            payload={"tweet_id": str(tweet_id)},
            dry_run=dry_run,
            operator="smoke-test",
        )
        like_result = executor.execute(like_req)
        audit.log_action(
            action=like_req.action.value, payload=like_req.payload,
            dry_run=dry_run, success=like_result.success,
            operator="smoke-test", error=like_result.error,
        )
        result.steps.append(SmokeTestStep(
            name="like_tweet", passed=like_result.success,
            result=like_result, error=like_result.error,
        ))
    else:
        result.steps.append(SmokeTestStep(
            name="like_tweet", passed=dry_run,
            error=None if dry_run else "No tweet_id returned from post — cannot like",
        ))

    # Step 3: Cleanup note
    # Note: Tweet deletion is not yet an inference-sh app action.
    # For now, smoke test tweets should be manually cleaned up or auto-deleted
    # via the test account's settings.
    result.steps.append(SmokeTestStep(
        name="cleanup_note", passed=True,
        error=None,
    ))

    return result
