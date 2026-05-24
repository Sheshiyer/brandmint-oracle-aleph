"""
GPT Image 2 Provider — generates images via local Codex CLI using ChatGPT subscription.

Uses the gpt-image-2 skill's gen.sh script to generate images through the user's
existing ChatGPT Plus or Pro subscription. No FAL_KEY, no per-image billing.

Prerequisites:
- codex CLI installed and logged in with ChatGPT Plus/Pro
- gpt-image-2 skill installed at ~/.agents/skills/gpt-image-2/
- python3 on PATH
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ImageProvider, GenerationResult, ProviderName


# Default path to gpt-image-2 skill scripts
GPT_IMAGE2_SKILL_PATH = Path(os.path.expanduser("~/.agents/skills/gpt-image-2"))
GPT_IMAGE2_GEN_SCRIPT = GPT_IMAGE2_SKILL_PATH / "scripts" / "gen.sh"


class GptImage2Provider(ImageProvider):
    """Image provider that uses GPT Image 2 via local Codex CLI."""

    name = ProviderName.GPT_IMAGE2

    def __init__(self, skill_path: Optional[str] = None):
        """Initialize GPT Image 2 provider.

        Args:
            skill_path: Optional path to gpt-image-2 skill directory.
                       Defaults to ~/.agents/skills/gpt-image-2/
        """
        if skill_path:
            self._skill_path = Path(skill_path)
        else:
            self._skill_path = GPT_IMAGE2_SKILL_PATH
        self._gen_script = self._skill_path / "scripts" / "gen.sh"

    def is_available(self) -> bool:
        """Check if GPT Image 2 is available."""
        # Check codex CLI
        if not shutil.which("codex"):
            return False
        # Check python3
        if not shutil.which("python3"):
            return False
        # Check gen.sh script exists
        if not self._gen_script.is_file():
            return False
        # Check script is executable
        if not os.access(self._gen_script, os.X_OK):
            return False
        return True

    def generate(
        self,
        prompt: str,
        model: str,
        output_path: str,
        image_urls: Optional[List[str]] = None,
        aspect_ratio: str = "1:1",
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate an image using GPT Image 2.

        Args:
            prompt: Image generation prompt
            model: Logical model name (ignored, always uses GPT Image 2)
            output_path: Where to save the generated image
            image_urls: Optional reference image URLs for image-to-image
            aspect_ratio: Aspect ratio (ignored, GPT Image 2 handles sizing)
            **kwargs: Additional arguments (ignored)

        Returns:
            GenerationResult with success status and output path
        """
        if not self.is_available():
            return GenerationResult(
                success=False,
                error="GPT Image 2 not available. Check codex CLI, python3, and gen.sh script.",
                model_used="gpt-image-2",
                provider="gpt-image2",
            )

        # Build command
        cmd = [
            str(self._gen_script),
            "--prompt", prompt,
            "--out", str(output_path),
        ]

        # Add local reference images if provided. gen.sh expects repeated --ref paths.
        reference_inputs = list(image_urls or []) + list(kwargs.get("reference_paths") or [])
        reference_paths: List[str] = []
        for ref in reference_inputs:
            ref_value = str(ref).strip()
            if not ref_value or ref_value.startswith(("http://", "https://")):
                continue
            ref_path = Path(ref_value).expanduser()
            if ref_path.exists():
                resolved_ref = str(ref_path)
                cmd.extend(["--ref", resolved_ref])
                reference_paths.append(resolved_ref)

        # Set timeout from kwargs or default to 300
        timeout = kwargs.get("timeout_sec", 300)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                error_msg = self._decode_error(result.returncode, result.stderr)
                return GenerationResult(
                    success=False,
                    error=error_msg,
                    model_used="gpt-image-2",
                    provider="gpt-image2",
                )

            # Verify output file was created
            output_file = Path(output_path)
            if not output_file.exists():
                return GenerationResult(
                    success=False,
                    error="GPT Image 2 completed but no output file was created",
                    model_used="gpt-image-2",
                    provider="gpt-image2",
                )

            return GenerationResult(
                success=True,
                local_path=str(output_file),
                model_used="gpt-image-2",
                provider="gpt-image2",
                metadata={
                    "prompt": prompt,
                    "skill_path": str(self._skill_path),
                    "reference_paths": reference_paths,
                },
            )

        except subprocess.TimeoutExpired:
            return GenerationResult(
                success=False,
                error=f"GPT Image 2 timed out after {timeout} seconds",
                model_used="gpt-image-2",
                provider="gpt-image2",
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                error=f"GPT Image 2 execution failed: {str(e)}",
                model_used="gpt-image-2",
                provider="gpt-image2",
            )

    def _decode_error(self, exit_code: int, stderr: str) -> str:
        """Decode gen.sh exit code to human-readable error."""
        error_messages = {
            2: "Bad arguments to gen.sh",
            3: "codex or python3 CLI missing",
            4: "Reference file does not exist",
            5: "codex exec failed (auth, network, or model error)",
            6: "No new session file detected",
            7: "Image generation did not produce an image payload",
        }
        base_msg = error_messages.get(exit_code, f"Unknown error (exit code {exit_code})")
        if stderr.strip():
            return f"{base_msg}: {stderr.strip()[:200]}"
        return base_msg

    def estimate_cost(self, model: str, **kwargs: Any) -> float:
        """Estimate cost for GPT Image 2 generation.

        GPT Image 2 uses ChatGPT subscription, so cost is $0 per image
        (covered by existing subscription).

        Args:
            model: Model name (ignored)
            **kwargs: Additional arguments (ignored)

        Returns:
            0.0 (covered by subscription)
        """
        return 0.0

    def supports_model(self, model: str) -> bool:
        """Check if GPT Image 2 supports the given model.

        GPT Image 2 is its own model, but we accept any model name
        and use GPT Image 2 regardless.

        Args:
            model: Model name to check

        Returns:
            True (always supported)
        """
        return True

    def get_capabilities(self) -> Dict[str, Any]:
        """Get GPT Image 2 capabilities."""
        return {
            "supports_image_reference": True,  # Via --ref flag
            "supports_negative_prompt": False,
            "max_prompt_length": 2000,
            "supported_aspects": ["1:1", "16:9", "9:16", "3:4", "4:3"],
            "resolution_options": ["1K", "2K"],
            "output_formats": ["png", "jpeg", "webp"],
        }

    @property
    def display_name(self) -> str:
        """Human-readable provider name."""
        return "GPT Image 2 (ChatGPT Subscription)"

    def get_model_id(self, logical_model: str) -> str:
        """Map logical model to GPT Image 2 (always returns gpt-image-2)."""
        return "gpt-image-2"

    def supports_image_reference(self) -> bool:
        """GPT Image 2 supports image references via --ref flag."""
        return True
