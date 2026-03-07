"""
Vision describer — generates textual descriptions of brand visual assets using LLM vision.

Transforms raw images into rich text source documents for NotebookLM by:
1. Sending images to a multimodal LLM (OpenRouter vision models)
2. Getting structured descriptions (composition, colors, typography, mood, brand elements)
3. Formatting as prose source documents that NotebookLM can use to generate
   on-brand PDFs, infographics, and reports.

Uses OpenRouter chat/completions API with image_url content blocks (zero pip deps).
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_VISION_MODEL = "anthropic/claude-3.5-haiku"
DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit per image
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

ASSET_DESCRIPTION_SYSTEM = """You are a brand design analyst. Given a visual asset from a brand kit, write a detailed description covering:

1. COMPOSITION: Layout structure, visual hierarchy, use of space
2. COLOR PALETTE: Dominant colors, accents, gradients, color relationships
3. TYPOGRAPHY: Any visible text, font styles, typographic treatment
4. BRAND ELEMENTS: Logos, icons, patterns, motifs, signatures
5. MOOD & TONE: Emotional quality, visual energy, brand personality expressed
6. TECHNICAL: Aspect ratio, style (photo/illustration/3D/flat), rendering quality

Write as analytical prose, not bullet lists. Be specific about colors (use descriptive names), spatial relationships, and design decisions. This description will be used by an AI to generate on-brand documents, so precision matters."""

LOGO_DESCRIPTION_SYSTEM = """You are a brand identity expert analyzing a logo. Write a comprehensive description covering:

1. FORM: Shape language, geometry, symmetry/asymmetry, negative space
2. COLOR: Exact colors used, relationships between them, how they create hierarchy
3. TYPOGRAPHY: Letterforms, font characteristics (serif/sans/display), weight, spacing
4. SYMBOLISM: What the logo communicates, visual metaphors, cultural references
5. CONSTRUCTION: How elements relate spatially, alignment, proportions
6. VERSATILITY: How well it would work at small sizes, on dark/light backgrounds, in monochrome
7. BRAND SIGNAL: What personality, values, and market position the logo communicates

Write as analytical prose. Be extremely specific — this description will be used to ensure the logo's essence is preserved across all brand touchpoints."""

STYLE_GUIDE_SYSTEM = """You are a brand strategist writing a style guide narrative. Transform the provided brand configuration data into a cohesive style guide document that covers:

1. COLOR SYSTEM: Primary, secondary, accent colors with their roles and relationships
2. TYPOGRAPHY: Font families, weights, sizes, and their hierarchy
3. VISUAL LANGUAGE: Aesthetic direction, materials, textures, patterns
4. BRAND PERSONALITY: How visual elements express the brand's character
5. APPLICATION RULES: How to use these elements consistently

Write as authoritative prose — this is the definitive guide for maintaining brand consistency."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AssetDescription:
    """Description of a single visual asset."""

    asset_id: str
    file_path: str
    description: str
    asset_type: str = "visual"  # visual, logo, product, pattern
    label: str = ""
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""
    cached: bool = False


# ---------------------------------------------------------------------------
# VisionDescriber
# ---------------------------------------------------------------------------

class VisionDescriber:
    """Generate text descriptions of brand images via LLM vision API."""

    def __init__(
        self,
        model: str = DEFAULT_VISION_MODEL,
        cache_dir: Optional[Path] = None,
        console: Optional[Console] = None,
    ):
        self.model = model
        self.cache_dir = cache_dir
        self.console = console or Console()
        self._api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self._print_lock = threading.Lock()
        self._total_tokens = 0
        self._total_cost = 0.0
        self._telemetry_lock = threading.Lock()

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def describe_asset(
        self,
        image_path: str,
        asset_id: str = "",
        asset_type: str = "visual",
        brand_context: str = "",
    ) -> AssetDescription:
        """Describe a single image asset."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if path.suffix.lower() not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {path.suffix}")

        if path.stat().st_size > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"Image too large: {path.stat().st_size} bytes")

        # Check cache
        if self.cache_dir:
            cached = self._read_cache(asset_id or path.stem)
            if cached:
                return AssetDescription(
                    asset_id=asset_id or path.stem,
                    file_path=str(path),
                    description=cached,
                    asset_type=asset_type,
                    cached=True,
                )

        # Select system prompt based on asset type
        if asset_type == "logo":
            system_prompt = LOGO_DESCRIPTION_SYSTEM
        else:
            system_prompt = ASSET_DESCRIPTION_SYSTEM

        user_prompt = "Describe this brand visual asset."
        if brand_context:
            user_prompt += f"\n\nBrand context: {brand_context}"

        # Call vision API
        description, usage = self._call_vision(system_prompt, user_prompt, path)

        if not description:
            return AssetDescription(
                asset_id=asset_id or path.stem,
                file_path=str(path),
                description="",
                asset_type=asset_type,
            )

        # Cache result
        if self.cache_dir:
            self._write_cache(asset_id or path.stem, description)

        tokens = usage.get("total_tokens", 0) if usage else 0
        cost = usage.get("total_cost", 0.0) if usage else 0.0

        with self._telemetry_lock:
            self._total_tokens += tokens
            self._total_cost += cost

        return AssetDescription(
            asset_id=asset_id or path.stem,
            file_path=str(path),
            description=description,
            asset_type=asset_type,
            tokens_used=tokens,
            cost_usd=cost,
            model=self.model,
        )

    def describe_batch(
        self,
        assets: List[Dict[str, str]],
        brand_context: str = "",
        max_workers: int = 3,
    ) -> List[AssetDescription]:
        """Describe multiple assets in parallel.

        Args:
            assets: List of dicts with keys: path, asset_id, asset_type (optional)
            brand_context: Brand info to include in prompts
            max_workers: Parallel workers (be gentle with API rate limits)
        """
        results: List[AssetDescription] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for asset in assets:
                future = executor.submit(
                    self.describe_asset,
                    image_path=asset["path"],
                    asset_id=asset.get("asset_id", ""),
                    asset_type=asset.get("asset_type", "visual"),
                    brand_context=brand_context,
                )
                futures[future] = asset

            for future in as_completed(futures):
                asset = futures[future]
                try:
                    desc = future.result()
                    results.append(desc)
                    status = "[dim]cached[/dim]" if desc.cached else f"{desc.tokens_used} tokens"
                    with self._print_lock:
                        self.console.print(
                            f"    [green]✓[/green] {desc.asset_id}: {status}"
                        )
                except Exception as e:
                    with self._print_lock:
                        self.console.print(
                            f"    [red]✗[/red] {asset.get('asset_id', '?')}: {e}"
                        )

        return results

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "total_tokens": self._total_tokens,
            "total_cost_usd": self._total_cost,
            "model": self.model,
        }

    # -- Vision API ---------------------------------------------------------

    def _call_vision(
        self,
        system_prompt: str,
        user_prompt: str,
        image_path: Path,
    ) -> Tuple[str, Optional[dict]]:
        """Call OpenRouter vision API with image."""
        if not self._api_key:
            return "", None

        image_data = self._encode_image(image_path)
        mime = mimetypes.guess_type(str(image_path))[0] or "image/png"

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{image_data}",
                            },
                        },
                    ],
                },
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            DEFAULT_ENDPOINT,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://brandmint.dev",
                "X-Title": "Brandmint Vision Describer",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return text.strip(), usage
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            with self._print_lock:
                self.console.print(f"    [red]Vision API error: {e.code} — {body[:200]}[/red]")
            return "", None
        except Exception as e:
            with self._print_lock:
                self.console.print(f"    [red]Vision API error: {e}[/red]")
            return "", None

    @staticmethod
    def _encode_image(path: Path) -> str:
        """Base64-encode an image file."""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

    # -- Cache --------------------------------------------------------------

    def _read_cache(self, key: str) -> Optional[str]:
        if not self.cache_dir:
            return None
        cache_file = self.cache_dir / f"{key}.md"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
        return None

    def _write_cache(self, key: str, content: str) -> None:
        if not self.cache_dir:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"{key}.md"
        cache_file.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# NB-04: Brand Style Guide Source Builder
# ---------------------------------------------------------------------------


class BrandStyleGuideBuilder:
    """Build a narrative style guide document from brand config data."""

    def __init__(
        self,
        model: str = DEFAULT_VISION_MODEL,
        console: Optional[Console] = None,
    ):
        self.model = model
        self.console = console or Console()
        self._api_key = os.environ.get("OPENROUTER_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def build_style_guide(self, config: dict) -> str:
        """Transform brand config into a narrative style guide source document."""
        sections = []

        # Color system
        palette = config.get("palette", {})
        if palette:
            sections.append(self._format_color_system(palette))

        # Typography
        typography = config.get("typography", {})
        if typography:
            sections.append(self._format_typography(typography))

        # Aesthetic
        aesthetic = config.get("aesthetic", {})
        if aesthetic:
            sections.append(self._format_aesthetic(aesthetic))

        # Theme
        theme = config.get("theme", {})
        if theme:
            sections.append(self._format_theme(theme))

        # Brand identity
        brand = config.get("brand", {})
        if brand:
            sections.append(self._format_brand_identity(brand))

        if not sections:
            return ""

        # If API available, synthesize into prose; otherwise return structured
        raw_content = "\n\n".join(sections)

        if self.available:
            return self._synthesize_guide(raw_content, config) or raw_content

        return f"# Brand Style Guide\n\n{raw_content}"

    def _format_color_system(self, palette: dict) -> str:
        lines = ["## Color System\n"]
        for role, value in palette.items():
            if isinstance(value, str):
                lines.append(f"- **{role.replace('_', ' ').title()}**: `{value}`")
            elif isinstance(value, dict):
                name = value.get("name", role)
                hex_val = value.get("hex", value.get("value", ""))
                usage = value.get("usage", "")
                lines.append(f"- **{name}**: `{hex_val}`{f' — {usage}' if usage else ''}")
        return "\n".join(lines)

    def _format_typography(self, typography: dict) -> str:
        lines = ["## Typography\n"]
        for role, spec in typography.items():
            if isinstance(spec, str):
                lines.append(f"- **{role.replace('_', ' ').title()}**: {spec}")
            elif isinstance(spec, dict):
                family = spec.get("family", spec.get("name", role))
                weight = spec.get("weight", "")
                style = spec.get("style", "")
                lines.append(f"- **{role.replace('_', ' ').title()}**: {family}"
                             f"{f' ({weight})' if weight else ''}"
                             f"{f' — {style}' if style else ''}")
        return "\n".join(lines)

    def _format_aesthetic(self, aesthetic: dict) -> str:
        lines = ["## Aesthetic Direction\n"]
        for key, value in aesthetic.items():
            if isinstance(value, list):
                lines.append(f"- **{key.replace('_', ' ').title()}**: {', '.join(str(v) for v in value)}")
            elif isinstance(value, str):
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        return "\n".join(lines)

    def _format_theme(self, theme: dict) -> str:
        lines = ["## Theme\n"]
        for key, value in theme.items():
            if isinstance(value, str):
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        return "\n".join(lines)

    def _format_brand_identity(self, brand: dict) -> str:
        lines = ["## Brand Identity\n"]
        name = brand.get("name", "")
        tagline = brand.get("tagline", "")
        mission = brand.get("mission", "")
        voice = brand.get("voice", "")
        tone = brand.get("tone", "")

        if name:
            lines.append(f"**Brand Name**: {name}")
        if tagline:
            lines.append(f"**Tagline**: {tagline}")
        if mission:
            lines.append(f"**Mission**: {mission}")
        if voice:
            lines.append(f"**Voice**: {voice}")
        if tone:
            lines.append(f"**Tone**: {tone}")
        return "\n".join(lines)

    def _synthesize_guide(self, raw_content: str, config: dict) -> Optional[str]:
        """Use LLM to transform structured data into narrative prose."""
        brand_name = config.get("brand", {}).get("name", "Brand")

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": STYLE_GUIDE_SYSTEM},
                {
                    "role": "user",
                    "content": f"Write a brand style guide for {brand_name} "
                    f"based on these specifications:\n\n{raw_content}",
                },
            ],
            "max_tokens": 3000,
            "temperature": 0.3,
        }

        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            DEFAULT_ENDPOINT,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://brandmint.dev",
                "X-Title": "Brandmint Style Guide Builder",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            self.console.print(f"  [yellow]Style guide synthesis failed: {e}[/yellow]")
            return None
