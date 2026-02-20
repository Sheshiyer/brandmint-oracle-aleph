"""
Remotion Video Generator — scaffolds a Remotion project and renders branded MP4 videos.

Produces up to 3 video compositions per brand:
- Brand Sizzle Reel (60-90s, 6 scenes: hook → problem → solution → proof → offer → CTA)
- Product Showcase (30-60s, 4 scenes: hero → features → differentiation → CTA)
- Audio + Slides (dynamic duration, synced to NotebookLM MP3)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console

from .theme_exporter import _extract_colors, _extract_fonts, _extract_brand_info


# ---------------------------------------------------------------------------
# Video definitions
# ---------------------------------------------------------------------------

VIDEO_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "brand-sizzle",
        "title": "Brand Sizzle Reel",
        "composition_id": "brand-sizzle",
        "output_filename": "brand-sizzle-reel.mp4",
        "description": "60-90s brand sizzle reel with 6 scenes",
        "data_sources": [
            "niche-validator", "buyer-persona", "competitor-analysis",
            "product-positioning-summary", "voice-and-tone", "visual-identity-core",
        ],
    },
    {
        "id": "product-showcase",
        "title": "Product Showcase",
        "composition_id": "product-showcase",
        "output_filename": "product-showcase.mp4",
        "description": "30-60s product showcase with 4 scenes",
        "data_sources": [
            "detailed-product-description", "product-positioning-summary",
            "buyer-persona", "competitor-analysis",
        ],
    },
    {
        "id": "audio-slides",
        "title": "Audio + Slides Overview",
        "composition_id": "audio-slides",
        "output_filename": "audio-slides-overview.mp4",
        "description": "Audio-synced slide show (matches NotebookLM MP3 duration)",
        "requires_audio": True,
        "data_sources": [],
    },
]


# ---------------------------------------------------------------------------
# Data extraction (reuses marp_generator helpers)
# ---------------------------------------------------------------------------

def _load_skill_outputs(outputs_dir: Path) -> Dict[str, dict]:
    """Load all JSON skill outputs from the outputs directory."""
    outputs: Dict[str, dict] = {}
    if not outputs_dir.is_dir():
        return outputs
    for f in outputs_dir.glob("*.json"):
        try:
            outputs[f.stem] = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return outputs


def _safe_get(data: dict, *keys: str, default: Any = "") -> Any:
    """Safely traverse nested dict keys."""
    current = data
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, {})
        else:
            return default
    return current if current and current != {} else default


def _extract_video_data(config: dict, skill_outputs: Dict[str, dict]) -> Dict[str, Any]:
    """Extract template variables for video compositions from brand config and skill outputs."""
    brand = config.get("brand", {})
    positioning = config.get("positioning", {})

    data: Dict[str, Any] = {
        "brand_name": brand.get("name", "Brand"),
        "tagline": brand.get("tagline", ""),
        "hero_headline": positioning.get("hero_headline", ""),
        "positioning_statement": positioning.get("statement", ""),
    }

    # From skill outputs
    for skill_id, output in skill_outputs.items():
        handoff = output.get("handoff", output)

        if skill_id == "niche-validator":
            data.setdefault("market_problem", _safe_get(handoff, "market_gap"))
        elif skill_id == "buyer-persona":
            data.setdefault("persona_name", _safe_get(handoff, "persona_name"))
            data.setdefault("persona_summary", _safe_get(handoff, "summary"))
            pain_points = _safe_get(handoff, "pain_points", default=[])
            if isinstance(pain_points, list):
                data.setdefault("pain_points", pain_points)
        elif skill_id == "product-positioning-summary":
            data.setdefault("value_proposition", _safe_get(handoff, "value_proposition"))
            data.setdefault("competitive_moat", _safe_get(handoff, "competitive_moat"))
            pillars = _safe_get(handoff, "identity_pillars", default=[])
            if isinstance(pillars, list):
                data.setdefault("identity_pillars", pillars)
        elif skill_id == "detailed-product-description":
            features = _safe_get(handoff, "features", default=[])
            if isinstance(features, list):
                data.setdefault("features", features)
            data.setdefault("differentiation", _safe_get(handoff, "differentiation"))
        elif skill_id == "voice-and-tone":
            data.setdefault("voice_description", _safe_get(handoff, "voice_description"))
        elif skill_id == "campaign-page-copy":
            data.setdefault("cta", _safe_get(handoff, "cta"))

    # Ensure list fields default to empty lists
    for key in ("features", "pain_points", "identity_pillars"):
        data.setdefault(key, [])

    # Ensure string fields default to empty strings
    for key in ("market_problem", "persona_name", "persona_summary",
                "value_proposition", "competitive_moat", "voice_description",
                "cta", "differentiation"):
        data.setdefault(key, "")

    return data


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def _load_state(path: Path) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class RemotionVideoGenerator:
    """Generate branded MP4 videos using Remotion (React-based programmatic video)."""

    def __init__(
        self,
        brand_dir: Path,
        config: dict,
        config_path: Path,
        console: Optional[Console] = None,
        video_filter: Optional[Set[str]] = None,
        force: bool = False,
    ):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.config_path = Path(config_path)
        self.console = console or Console()
        self.video_filter = video_filter
        self.force = force

        self.workspace = self.brand_dir / "deliverables" / ".remotion-workspace"
        self.videos_dir = self.brand_dir / "deliverables" / "videos"
        self.state_path = self.brand_dir / ".brandmint" / "videos-state.json"
        self.outputs_dir = self.brand_dir / ".brandmint" / "outputs"

        slug = config.get("brand", {}).get("slug", "brand")
        self.generated_dir = self.brand_dir / slug / "generated"
        self.audio_path = (
            self.brand_dir / "deliverables" / "notebooklm" / "artifacts"
            / "brand-audio-overview.mp3"
        )

        self.state: dict = {} if force else _load_state(self.state_path)
        self.brand_name = config.get("brand", {}).get("name", "Brand")

        # Template directory (alongside this module)
        self.templates_dir = Path(__file__).parent / "remotion_templates"

    def generate(self) -> bool:
        """Main entry: scaffold, install, render, save. Returns True on full success."""
        started = time.time()

        # Preflight
        if not self._check_node():
            return False

        # Load skill outputs
        skill_outputs = _load_skill_outputs(self.outputs_dir)
        self.console.print(
            f"  [green]\u2713[/green] Loaded {len(skill_outputs)} skill outputs"
        )

        # Scaffold workspace
        self._scaffold_workspace(skill_outputs)
        self.console.print("  [green]\u2713[/green] Remotion workspace scaffolded")

        # Install dependencies
        self._install_deps()

        # Render videos
        defs = self._filtered_defs()
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        all_ok = True

        for video_def in defs:
            ok = self._render_video(video_def)
            if not ok:
                all_ok = False

        # Save state
        elapsed = time.time() - started
        self.state["updated_at"] = datetime.now().isoformat()
        self.state["elapsed_seconds"] = round(elapsed, 1)
        _save_state(self.state, self.state_path)

        self.console.print(
            f"\n  Videos generated in {elapsed:.1f}s \u2192 {self.videos_dir}"
        )
        return all_ok

    # ------------------------------------------------------------------
    # Preflight
    # ------------------------------------------------------------------

    def _check_node(self) -> bool:
        """Verify node and npx are available."""
        if not shutil.which("node"):
            self.console.print(
                "[red]Node.js not found.[/red]\n"
                "Install with: [bold]brew install node[/bold] or visit https://nodejs.org\n"
                "Required: Node.js >= 18"
            )
            return False
        if not shutil.which("npx"):
            self.console.print(
                "[red]npx not found.[/red]\n"
                "It should come with Node.js. Try reinstalling Node.js."
            )
            return False

        # Check version
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=10,
            )
            version_str = result.stdout.strip().lstrip("v")
            major = int(version_str.split(".")[0])
            if major < 18:
                self.console.print(
                    f"[red]Node.js {version_str} is too old.[/red]\n"
                    "Remotion requires Node.js >= 18. Please upgrade."
                )
                return False
        except Exception:
            pass  # Best-effort version check

        return True

    # ------------------------------------------------------------------
    # Scaffold
    # ------------------------------------------------------------------

    def _scaffold_workspace(self, skill_outputs: Dict[str, dict]) -> None:
        """Write Remotion project from Jinja2 templates."""
        try:
            from jinja2 import Environment, FileSystemLoader
        except ImportError:
            self.console.print(
                "[red]Jinja2 not installed.[/red]\n"
                "Install with: [bold]pip install jinja2[/bold]"
            )
            raise

        env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            undefined=__import__("jinja2").Undefined,
        )

        # Prepare template data
        colors = _extract_colors(self.config)
        fonts = _extract_fonts(self.config)
        brand_info = _extract_brand_info(self.config)
        video_data = _extract_video_data(self.config, skill_outputs)
        slug = self.config.get("brand", {}).get("slug", "brand")

        # Detect audio
        has_audio = self.audio_path.is_file()
        audio_duration = 0.0
        if has_audio:
            audio_duration = self._get_audio_duration()

        # Collect visual assets
        visual_assets: List[str] = []
        slide_captions: List[str] = []
        if self.generated_dir.is_dir():
            for img in sorted(self.generated_dir.glob("*.png")):
                visual_assets.append(img.name)
                # Use filename as caption (strip extension, replace hyphens)
                caption = img.stem.replace("-", " ").replace("_", " ").title()
                slide_captions.append(caption)

        # Ensure at least a few slides for audio-slides
        if has_audio and not visual_assets:
            # Generate placeholder slide names
            for i in range(5):
                slide_captions.append(f"{brand_info['name']} - Slide {i + 1}")

        # Create workspace structure
        src_dir = self.workspace / "src"
        scenes_dir = src_dir / "scenes"
        components_dir = src_dir / "components"
        public_dir = self.workspace / "public"

        for d in (src_dir, scenes_dir, components_dir, public_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Template context
        ctx = {
            "brand_slug": slug,
            "brand_name": brand_info["name"],
            "tagline": brand_info["tagline"],
            "colors": colors,
            "fonts": fonts,
            "has_audio": has_audio,
            "audio_duration_seconds": audio_duration if has_audio else 60,
            "visual_assets": visual_assets,
            "slide_captions": slide_captions,
            **video_data,
        }

        # Render Jinja2 templates
        templates_to_render = [
            ("package.json.j2", self.workspace / "package.json"),
            ("index.tsx.j2", src_dir / "index.tsx"),
            ("root.tsx.j2", src_dir / "root.tsx"),
            ("constants.ts.j2", src_dir / "constants.ts"),
            ("brand-data.ts.j2", src_dir / "brand-data.ts"),
            ("scenes/brand-sizzle.tsx.j2", scenes_dir / "brand-sizzle.tsx"),
            ("scenes/product-showcase.tsx.j2", scenes_dir / "product-showcase.tsx"),
        ]

        if has_audio:
            templates_to_render.append(
                ("scenes/audio-slides.tsx.j2", scenes_dir / "audio-slides.tsx"),
            )

        for template_name, output_path in templates_to_render:
            tmpl = env.get_template(template_name)
            output_path.write_text(tmpl.render(**ctx))

        # Copy static files (tsconfig, components)
        static_tsconfig = self.templates_dir / "tsconfig.json"
        if static_tsconfig.is_file():
            shutil.copy2(static_tsconfig, self.workspace / "tsconfig.json")

        for comp_file in (self.templates_dir / "components").glob("*.tsx"):
            shutil.copy2(comp_file, components_dir / comp_file.name)

        # Symlink/copy visual assets to public/
        if self.generated_dir.is_dir():
            for img in self.generated_dir.glob("*.png"):
                dest = public_dir / img.name
                if not dest.exists():
                    try:
                        dest.symlink_to(img.resolve())
                    except OSError:
                        shutil.copy2(img, dest)

        # Copy audio to public/ if available
        if has_audio:
            audio_dest = public_dir / "audio-overview.mp3"
            if not audio_dest.exists():
                try:
                    audio_dest.symlink_to(self.audio_path.resolve())
                except OSError:
                    shutil.copy2(self.audio_path, audio_dest)

    def _get_audio_duration(self) -> float:
        """Get audio duration in seconds using ffprobe or fallback."""
        if not self.audio_path.is_file():
            return 60.0

        # Try ffprobe first
        if shutil.which("ffprobe"):
            try:
                result = subprocess.run(
                    [
                        "ffprobe", "-v", "quiet", "-show_entries",
                        "format=duration", "-of", "csv=p=0",
                        str(self.audio_path),
                    ],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())
            except Exception:
                pass

        # Fallback: estimate from file size (~128kbps)
        try:
            size_bytes = self.audio_path.stat().st_size
            return size_bytes / (128 * 1024 / 8)  # 128kbps
        except Exception:
            return 120.0  # 2 minute fallback

    # ------------------------------------------------------------------
    # Install dependencies
    # ------------------------------------------------------------------

    def _install_deps(self) -> None:
        """Run npm install in workspace (skip if node_modules is fresh)."""
        node_modules = self.workspace / "node_modules"
        pkg_json = self.workspace / "package.json"

        # Skip if node_modules exists and is newer than package.json
        if (
            node_modules.is_dir()
            and node_modules.stat().st_mtime > pkg_json.stat().st_mtime
            and not self.force
        ):
            self.console.print("  [dim]\u23ed npm install skipped (cached)[/dim]")
            return

        self.console.print("  \u23f3 Running npm install...")
        try:
            result = subprocess.run(
                ["npm", "install", "--prefer-offline"],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                self.console.print("  [green]\u2713[/green] Dependencies installed")
            else:
                error = (result.stderr or result.stdout or "")[:300]
                self.console.print(f"  [yellow]npm install warning: {error}[/yellow]")
        except subprocess.TimeoutExpired:
            self.console.print("  [yellow]npm install timed out (120s)[/yellow]")
        except Exception as e:
            self.console.print(f"  [yellow]npm install error: {e}[/yellow]")

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _render_video(self, video_def: dict) -> bool:
        """Render a single video composition to MP4."""
        video_id = video_def["id"]

        # Check idempotency
        existing = self.state.get(video_id, {})
        if existing.get("status") == "completed" and not self.force:
            self.console.print(f"  [dim]\u23ed {video_id} \u2014 already rendered[/dim]")
            return True

        # Check audio requirement
        if video_def.get("requires_audio") and not self.audio_path.is_file():
            self.console.print(
                f"  [dim]\u23ed {video_id} \u2014 skipped (no NotebookLM audio found)[/dim]"
            )
            self.state[video_id] = {
                "status": "skipped",
                "reason": "No audio file available",
            }
            _save_state(self.state, self.state_path)
            return True  # Not a failure, just skipped

        self.console.print(f"  \u23f3 Rendering {video_def['title']}...")

        # Output path
        output_mp4 = self.videos_dir / video_def["output_filename"]

        # Run remotion render
        cmd = [
            "npx", "remotion", "render",
            "src/index.tsx",
            video_def["composition_id"],
            str(output_mp4),
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, "NODE_OPTIONS": "--max-old-space-size=4096"},
            )
            if result.returncode == 0 and output_mp4.exists():
                size_mb = output_mp4.stat().st_size / (1024 * 1024)
                self.state[video_id] = {
                    "status": "completed",
                    "path": str(output_mp4),
                    "size_mb": round(size_mb, 2),
                    "generated_at": datetime.now().isoformat(),
                }
                _save_state(self.state, self.state_path)
                self.console.print(
                    f"  [green]\u2713[/green] {video_def['output_filename']} ({size_mb:.1f} MB)"
                )
                return True
            else:
                error = (result.stderr or result.stdout or "")[:500]
                self.state[video_id] = {"status": "failed", "error": error}
                _save_state(self.state, self.state_path)
                self.console.print(f"  [red]\u2717 {video_id} failed: {error[:200]}[/red]")
                return False
        except subprocess.TimeoutExpired:
            self.state[video_id] = {"status": "failed", "error": "Timeout (300s)"}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {video_id} timed out (300s)[/red]")
            return False
        except Exception as e:
            self.state[video_id] = {"status": "failed", "error": str(e)[:300]}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {video_id} error: {e}[/red]")
            return False

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _filtered_defs(self) -> List[dict]:
        """Return video definitions, optionally filtered by video_filter."""
        if self.video_filter:
            return [d for d in VIDEO_DEFINITIONS if d["id"] in self.video_filter]
        return list(VIDEO_DEFINITIONS)
