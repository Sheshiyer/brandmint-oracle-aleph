"""Tests for X/Twitter automation modules."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from brandmint.automation.x_actions import (
    XAction, XActionExecutor, XActionRequest, XActionResult, ACTION_APP_MAP,
)
from brandmint.automation.x_preflight import (
    check_api_key, check_x_oauth_token, check_scopes_for_action,
    run_preflight, ACTION_SCOPES, PreflightResult,
)
from brandmint.automation.x_audit import XAuditLog, AuditEntry


# ━━━ XAction Tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestXActionEnum:
    def test_all_actions_have_app_mapping(self):
        for action in XAction:
            assert action in ACTION_APP_MAP, f"Missing app mapping for {action.value}"

    def test_app_ids_are_prefixed(self):
        for action, app_id in ACTION_APP_MAP.items():
            assert app_id.startswith("infsh-x-"), f"App ID {app_id} should start with infsh-x-"


# ━━━ Dry-Run Tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestDryRun:
    def test_dry_run_returns_preview(self):
        executor = XActionExecutor()
        request = XActionRequest(
            action=XAction.POST_TWEET,
            payload={"text": "Hello from brandmint"},
            dry_run=True,
        )
        result = executor.execute(request)

        assert result.success is True
        assert result.dry_run is True
        assert result.response["would_execute"] is True
        assert result.response["app"] == "infsh-x-post-tweet"
        assert result.response["reason"] == "dry-run"

    def test_dry_run_no_network_calls(self):
        """Dry-run must not make any HTTP requests."""
        executor = XActionExecutor()
        request = XActionRequest(
            action=XAction.DM_SEND,
            payload={"user": "testuser", "text": "hi"},
            dry_run=True,
        )

        with patch("urllib.request.urlopen") as mock_urlopen:
            result = executor.execute(request)
            mock_urlopen.assert_not_called()

        assert result.success is True
        assert result.dry_run is True

    def test_dry_run_works_without_api_key(self):
        """Dry-run should succeed even without INFERENCE_API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            executor = XActionExecutor(api_key="")
            request = XActionRequest(
                action=XAction.POST_TWEET,
                payload={"text": "test"},
                dry_run=True,
            )
            result = executor.execute(request)
            assert result.success is True
            assert result.dry_run is True


# ━━━ Live Execution Tests (mocked) ━━━━━━━━━━━━━━━━━━━━━━━━


class TestLiveExecution:
    def test_missing_api_key_fails(self):
        executor = XActionExecutor(api_key="")
        request = XActionRequest(
            action=XAction.POST_TWEET,
            payload={"text": "test"},
            dry_run=False,
        )
        result = executor.execute(request)
        assert result.success is False
        assert "INFERENCE_API_KEY" in (result.error or "")

    def test_unknown_action_fails(self):
        """Test that an invalid action returns an error."""
        executor = XActionExecutor(api_key="test-key")
        # Manually construct a request with an unmapped action
        request = XActionRequest(
            action=XAction.POST_TWEET,
            payload={"text": "test"},
            dry_run=False,
        )
        # Temporarily remove the mapping
        original = ACTION_APP_MAP.pop(XAction.POST_TWEET)
        try:
            result = executor.execute(request)
            assert result.success is False
            assert "Unknown action" in (result.error or "")
        finally:
            ACTION_APP_MAP[XAction.POST_TWEET] = original

    def test_result_serialization(self):
        result = XActionResult(
            success=True, action="post-tweet", dry_run=False,
            payload={"text": "hello"}, response={"id": "123"},
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["action"] == "post-tweet"
        assert d["payload"]["text"] == "hello"


# ━━━ Preflight Tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestPreflight:
    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            check = check_api_key()
            assert check.passed is False
            assert "not set" in check.message

    def test_present_api_key(self):
        with patch.dict(os.environ, {"INFERENCE_API_KEY": "sk-test-1234567890"}):
            check = check_api_key()
            assert check.passed is True
            assert "sk-t" in check.message  # masked prefix

    def test_missing_oauth_token(self):
        with patch.dict(os.environ, {}, clear=True):
            check = check_x_oauth_token()
            assert check.passed is False

    def test_present_oauth_token(self):
        with patch.dict(os.environ, {"X_OAUTH_TOKEN": "oauth-token-123"}):
            check = check_x_oauth_token()
            assert check.passed is True

    def test_scope_check_with_all_scopes(self):
        required = ACTION_SCOPES[XAction.POST_TWEET]
        check = check_scopes_for_action(XAction.POST_TWEET, available_scopes=required)
        assert check.passed is True

    def test_scope_check_missing_scope(self):
        check = check_scopes_for_action(XAction.POST_TWEET, available_scopes={"users.read"})
        assert check.passed is False
        assert "tweet.write" in check.message

    def test_run_preflight_all_checks(self):
        with patch.dict(os.environ, {"INFERENCE_API_KEY": "sk-test", "X_OAUTH_TOKEN": "tok", "X_OAUTH_SCOPES": "tweet.write,users.read"}):
            result = run_preflight(actions=[XAction.POST_TWEET])
            assert len(result.checks) == 3  # api_key + oauth + scopes
            assert result.all_passed is True


# ━━━ Audit Log Tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestAuditLog:
    def test_log_and_query(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        audit = XAuditLog(log_path=str(log_path))

        # Log an action
        entry = audit.log_action(
            action="post-tweet",
            payload={"text": "hello world"},
            dry_run=True,
            success=True,
            operator="test",
        )
        assert entry.action == "post-tweet"
        assert entry.dry_run is True

        # File should exist with one line
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1

        # Query should return it
        results = audit.query()
        assert len(results) == 1
        assert results[0].action == "post-tweet"

    def test_query_filters(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        audit = XAuditLog(log_path=str(log_path))

        audit.log_action(action="post-tweet", payload={"text": "a"}, dry_run=True, success=True)
        audit.log_action(action="post-like", payload={"tweet_id": "1"}, dry_run=False, success=True)
        audit.log_action(action="post-tweet", payload={"text": "b"}, dry_run=False, success=False, error="timeout")

        # Filter by action
        results = audit.query(action="post-tweet")
        assert len(results) == 2

        # Filter by dry_run
        results = audit.query(dry_run_only=True)
        assert len(results) == 1
        assert results[0].dry_run is True

    def test_payload_hash_deterministic(self):
        h1 = XAuditLog._hash_payload({"a": 1, "b": 2})
        h2 = XAuditLog._hash_payload({"b": 2, "a": 1})
        assert h1 == h2  # sorted keys

    def test_empty_log_returns_empty(self, tmp_path):
        log_path = tmp_path / "nonexistent.jsonl"
        audit = XAuditLog(log_path=str(log_path))
        assert audit.query() == []
