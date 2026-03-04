"""
Inference provider adapter.

Implements the Inference REST lifecycle:
- POST /api/v1/apps/run
- GET  /api/v1/tasks/{task_id}
- GET  /api/v1/tasks/{task_id}/result (best-effort fallback)
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Mapping, Optional

from .base import GenerationResult, ImageProvider, ProviderName
from .model_mapping import get_model_id


class InferenceProvider(ImageProvider):
    """Inference.sh image generation provider."""

    DEFAULT_BASE_URL = "https://api.inference.sh"
    DEFAULT_APP_ID = "infsh-ai-image-generation"
    DEFAULT_POLL_SECONDS = 2.0
    DEFAULT_TIMEOUT_SECONDS = 180.0

    SUCCESS_STATUS_TEXT = {"completed", "succeeded", "success", "done"}
    FAILURE_STATUS_TEXT = {"failed", "error", "cancelled", "canceled"}
    SUCCESS_STATUS_INT = {9}
    FAILURE_STATUS_INT = {10, 11}

    @property
    def name(self) -> ProviderName:
        return ProviderName.INFERENCE

    @property
    def display_name(self) -> str:
        return "Inference"

    def is_available(self) -> bool:
        return bool(os.environ.get("INFERENCE_API_KEY"))

    def supports_image_reference(self) -> bool:
        return True

    def get_model_id(self, logical_model: str) -> str:
        return get_model_id("inference", logical_model)

    def _get_api_key(self) -> str:
        key = os.environ.get("INFERENCE_API_KEY", "").strip()
        if not key:
            raise EnvironmentError("INFERENCE_API_KEY environment variable not set")
        return key

    def _base_url(self) -> str:
        raw = os.environ.get("INFERENCE_BASE_URL", "").strip() or self.DEFAULT_BASE_URL
        return raw.rstrip("/")

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        api_key: str,
        payload: Optional[Mapping[str, Any]] = None,
        timeout: float = 60.0,
    ) -> Mapping[str, Any]:
        data = None
        headers = {
            "Authorization": f"Bearer {api_key}",
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
            raise RuntimeError(f"Inference API {method} {url} failed ({e.code}): {body[:240]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Inference API {method} {url} failed: {e}")

        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            raise RuntimeError(f"Inference API {method} {url} returned non-JSON response")

        if not isinstance(parsed, Mapping):
            raise RuntimeError(f"Inference API {method} {url} returned unexpected payload type")
        return parsed

    def _normalize_status(self, value: Any) -> tuple[Optional[int], str]:
        if isinstance(value, int):
            return value, str(value)
        text = str(value or "").strip().lower()
        if text.isdigit():
            return int(text), text
        return None, text

    def _is_success_status(self, value: Any) -> bool:
        code, text = self._normalize_status(value)
        if code is not None and code in self.SUCCESS_STATUS_INT:
            return True
        return text in self.SUCCESS_STATUS_TEXT

    def _is_failure_status(self, value: Any) -> bool:
        code, text = self._normalize_status(value)
        if code is not None and code in self.FAILURE_STATUS_INT:
            return True
        return text in self.FAILURE_STATUS_TEXT

    def _extract_task_id(self, payload: Mapping[str, Any]) -> Optional[str]:
        for key in ("task_id", "taskId", "id"):
            value = payload.get(key)
            if value is not None:
                sval = str(value).strip()
                if sval:
                    return sval
        for key in ("task", "data", "result"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                nested_id = self._extract_task_id(nested)
                if nested_id:
                    return nested_id
        return None

    def _extract_image_url(self, payload: Any) -> Optional[str]:
        queue: list[Any] = [payload]
        while queue:
            current = queue.pop(0)
            if isinstance(current, str):
                if current.startswith("http://") or current.startswith("https://"):
                    return current
                continue
            if isinstance(current, list):
                queue.extend(current)
                continue
            if not isinstance(current, Mapping):
                continue

            for key in ("url", "uri", "image_url", "imageUri"):
                value = current.get(key)
                if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
                    return value

            for key in ("image", "images", "output", "result", "data"):
                if key in current:
                    queue.append(current.get(key))
        return None

    def _poll_task(self, *, base_url: str, api_key: str, task_id: str) -> Mapping[str, Any]:
        max_wait = float(os.environ.get("INFERENCE_TASK_MAX_WAIT", self.DEFAULT_TIMEOUT_SECONDS))
        interval = float(os.environ.get("INFERENCE_TASK_POLL_INTERVAL", self.DEFAULT_POLL_SECONDS))
        start = time.time()

        last_payload: Optional[Mapping[str, Any]] = None
        while time.time() - start < max_wait:
            task_payload = self._request_json(
                method="GET",
                url=f"{base_url}/api/v1/tasks/{task_id}",
                api_key=api_key,
                timeout=30.0,
            )
            last_payload = task_payload
            status = task_payload.get("status")
            if self._is_failure_status(status):
                raise RuntimeError(f"Inference task {task_id} failed with status={status}: {json.dumps(task_payload)[:240]}")

            if self._is_success_status(status):
                # Prefer rich result payload when available.
                if self._extract_image_url(task_payload):
                    return task_payload
                try:
                    result_payload = self._request_json(
                        method="GET",
                        url=f"{base_url}/api/v1/tasks/{task_id}/result",
                        api_key=api_key,
                        timeout=30.0,
                    )
                    if self._extract_image_url(result_payload):
                        return result_payload
                    return result_payload or task_payload
                except Exception:
                    return task_payload

            time.sleep(interval)

        raise TimeoutError(
            f"Inference task {task_id} did not complete within {max_wait:.0f}s; "
            f"last payload={json.dumps(last_payload or {})[:200]}"
        )

    def _download_image(self, url: str, output_path: str) -> None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())

    def generate(
        self,
        prompt: str,
        model: str,
        output_path: str,
        width: int = 1024,
        height: int = 1024,
        image_url: Optional[str] = None,
        negative_prompt: str = "",
        guidance_scale: float = 7.5,
        num_steps: int = 50,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate an image via Inference app execution + task polling."""
        try:
            api_key = self._get_api_key()
        except EnvironmentError as e:
            return GenerationResult(
                success=False,
                error=str(e),
                model_used=model,
                provider=self.display_name,
            )

        base_url = self._base_url()
        app_id = str(
            kwargs.get("inference_app")
            or os.environ.get("INFERENCE_IMAGE_APP", "").strip()
            or self.get_model_id(model)
            or self.DEFAULT_APP_ID
        ).strip()

        image_urls = kwargs.get("image_urls")
        normalized_refs: list[str] = []
        if isinstance(image_urls, list):
            normalized_refs = [str(item).strip() for item in image_urls if str(item).strip()]
        if image_url and str(image_url).strip():
            normalized_refs.insert(0, str(image_url).strip())

        input_payload: dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "width": width,
            "height": height,
        }
        if negative_prompt:
            input_payload["negative_prompt"] = negative_prompt
        if guidance_scale:
            input_payload["guidance_scale"] = guidance_scale
        if num_steps:
            input_payload["num_steps"] = num_steps
        if normalized_refs:
            # Keep both single + list for app compatibility.
            input_payload["image_url"] = normalized_refs[0]
            input_payload["image_urls"] = normalized_refs

        payload: dict[str, Any] = {
            "app": app_id,
            "input": input_payload,
        }

        function = kwargs.get("function")
        if function is not None:
            payload["function"] = function
        setup = kwargs.get("setup")
        if isinstance(setup, Mapping):
            payload["setup"] = dict(setup)

        try:
            run_payload = self._request_json(
                method="POST",
                url=f"{base_url}/api/v1/apps/run",
                api_key=api_key,
                payload=payload,
                timeout=30.0,
            )
            task_id = self._extract_task_id(run_payload)
            final_payload = (
                self._poll_task(base_url=base_url, api_key=api_key, task_id=task_id)
                if task_id
                else run_payload
            )
            image_result_url = self._extract_image_url(final_payload)
            if not image_result_url:
                return GenerationResult(
                    success=False,
                    error=f"Inference response missing image URL: {json.dumps(final_payload)[:240]}",
                    model_used=app_id,
                    provider=self.display_name,
                )

            self._download_image(image_result_url, output_path)
            return GenerationResult(
                success=True,
                image_url=image_result_url,
                local_path=output_path,
                model_used=app_id,
                provider=self.display_name,
                metadata={
                    "task_id": task_id,
                    "base_url": base_url,
                    "app": app_id,
                },
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                model_used=app_id,
                provider=self.display_name,
            )
