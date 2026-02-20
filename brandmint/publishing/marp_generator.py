"""
Marp Slide Deck Generator — converts brand data into branded PDF slide decks.

Uses Marp CLI to render Markdown → PDF with brand CSS theme.
Produces 3 decks by default:
- Brand Overview (investor/partner, 10 slides)
- Product Showcase (customer-facing, 8-10 slides)
- Strategy & Insights (internal team, 12 slides)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console

from .theme_exporter import BrandThemeExporter, _extract_brand_info
from .source_builder import SOURCE_GROUPS


# ---------------------------------------------------------------------------
# Deck definitions
# ---------------------------------------------------------------------------

DECK_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "brand-overview",
        "title": "Brand Overview Deck",
        "template": "brand-overview.md.j2",
        "output_filename": "brand-overview-deck.pdf",
        "slides": 10,
        "description": "Investor/partner brand overview",
        "data_sources": ["niche-validator", "buyer-persona", "competitor-analysis",
                         "product-positioning-summary", "mds-messaging-direction-summary",
                         "voice-and-tone", "visual-identity-core", "detailed-product-description"],
    },
    {
        "id": "product-showcase",
        "title": "Product Showcase Deck",
        "template": "product-showcase.md.j2",
        "output_filename": "product-showcase-deck.pdf",
        "slides": 8,
        "description": "Customer-facing product showcase",
        "data_sources": ["detailed-product-description", "product-positioning-summary",
                         "buyer-persona", "competitor-analysis"],
    },
    {
        "id": "strategy-insights",
        "title": "Strategy & Insights Deck",
        "template": "strategy-insights.md.j2",
        "output_filename": "strategy-insights-deck.pdf",
        "slides": 12,
        "description": "Internal team strategy briefing",
        "data_sources": ["niche-validator", "buyer-persona", "competitor-analysis",
                         "product-positioning-summary", "mds-messaging-direction-summary",
                         "voice-and-tone", "social-content-engine", "campaign-page-copy"],
    },
]


# ---------------------------------------------------------------------------
# Data extraction from pipeline outputs
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


def _extract_deck_data(
    deck_id: str,
    config: dict,
    skill_outputs: Dict[str, dict],
) -> Dict[str, Any]:
    """Extract template variables from brand config and skill outputs.

    Maps pipeline output data into the flat variable namespace expected
    by Jinja2 deck templates.
    """
    brand = config.get("brand", {})
    positioning = config.get("positioning", {})
    products = config.get("products", {})
    palette = config.get("palette", {})

    data: Dict[str, Any] = {
        "brand_name": brand.get("name", "Brand"),
        "tagline": brand.get("tagline", ""),
        "archetype": brand.get("archetype", ""),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Voice & tone
    voice = brand.get("voice", "")
    tone = brand.get("tone", "")
    data["voice_tone"] = f"{voice}, {tone}" if voice and tone else voice or tone or ""

    # Positioning
    data["positioning_statement"] = positioning.get("statement", "")
    data["hero_headline"] = positioning.get("hero_headline", "")

    # Palette summary
    palette_parts = []
    for role in ("primary", "secondary", "accent"):
        entry = palette.get(role, {})
        if isinstance(entry, dict) and entry.get("name"):
            palette_parts.append(f"{entry['name']} ({entry.get('hex', '')})")
    data["palette_summary"] = ", ".join(palette_parts) if palette_parts else ""

    # Hero product
    hero = products.get("hero", "")
    if isinstance(hero, dict):
        data["hero_product"] = hero.get("name", "")
    elif isinstance(hero, str):
        data["hero_product"] = hero
    else:
        data["hero_product"] = ""

    # Extract from skill outputs
    _inject_niche_data(data, skill_outputs.get("niche-validator", {}))
    _inject_persona_data(data, skill_outputs.get("buyer-persona", {}))
    _inject_competitor_data(data, skill_outputs.get("competitor-analysis", {}))
    _inject_product_data(data, skill_outputs.get("detailed-product-description", {}))
    _inject_positioning_data(data, skill_outputs.get("product-positioning-summary", {}))
    _inject_voice_data(data, skill_outputs.get("voice-and-tone", {}))
    _inject_messaging_data(data, skill_outputs.get("mds-messaging-direction-summary", {}))
    _inject_campaign_data(data, skill_outputs.get("campaign-page-copy", {}))
    _inject_social_data(data, skill_outputs.get("social-content-engine", {}))

    # Custom overrides from deliverables config
    deliverables = config.get("deliverables", {})
    deck_overrides = {}
    for deck_def in deliverables.get("slide_decks", []):
        if deck_def.get("id") == deck_id:
            deck_overrides = deck_def
            break
    if deck_overrides.get("content"):
        data["custom_content"] = deck_overrides["content"]
    if deck_overrides.get("style"):
        data["custom_style"] = deck_overrides["style"]

    return data


def _safe_get(data: dict, *keys: str, default: Any = "") -> Any:
    """Safely traverse nested dict keys."""
    current = data
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, {})
        else:
            return default
    return current if current and current != {} else default


def _inject_niche_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    data.setdefault("market_problem", _safe_get(handoff, "market_gap"))
    data.setdefault("market_opportunity", _safe_get(handoff, "opportunity_summary"))
    data.setdefault("market_analysis", _safe_get(handoff, "market_analysis"))
    risks = _safe_get(handoff, "risks", default=[])
    if isinstance(risks, list):
        data.setdefault("market_risks", risks)


def _inject_persona_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    data.setdefault("persona_name", _safe_get(handoff, "persona_name"))
    data.setdefault("persona_summary", _safe_get(handoff, "summary"))
    motivations = _safe_get(handoff, "motivations", default=[])
    if isinstance(motivations, list):
        data.setdefault("persona_motivations", motivations)
    pain_points = _safe_get(handoff, "pain_points", default=[])
    if isinstance(pain_points, list):
        data.setdefault("pain_points", pain_points)
    # Structured persona for strategy deck
    data.setdefault("persona", {
        "name": _safe_get(handoff, "persona_name"),
        "demographics": _safe_get(handoff, "demographics"),
        "psychographics": _safe_get(handoff, "psychographics"),
        "pain_points": ", ".join(pain_points) if isinstance(pain_points, list) else str(pain_points),
        "triggers": _safe_get(handoff, "buying_triggers"),
    })


def _inject_competitor_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    competitors = _safe_get(handoff, "competitors", default=[])
    if isinstance(competitors, list):
        data.setdefault("competitors", competitors)
        data.setdefault("competitor_matrix", competitors)


def _inject_product_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    data.setdefault("product_description", _safe_get(handoff, "description"))
    data.setdefault("product_overview", _safe_get(handoff, "overview"))
    features = _safe_get(handoff, "features", default=[])
    if isinstance(features, list):
        data.setdefault("features", features)
    data.setdefault("pricing", _safe_get(handoff, "pricing"))
    data.setdefault("differentiation", _safe_get(handoff, "differentiation"))


def _inject_positioning_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    data.setdefault("value_proposition", _safe_get(handoff, "value_proposition"))
    data.setdefault("positioning_statement", _safe_get(handoff, "positioning_statement"))
    pillars = _safe_get(handoff, "identity_pillars", default=[])
    if isinstance(pillars, list):
        data.setdefault("positioning_pillars", pillars)
        data.setdefault("identity_pillars", pillars)
    data.setdefault("competitive_moat", _safe_get(handoff, "competitive_moat"))


def _inject_voice_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    voice_desc = _safe_get(handoff, "voice_description")
    if voice_desc:
        data.setdefault("voice_description", voice_desc)
    attributes = _safe_get(handoff, "voice_attributes", default=[])
    if isinstance(attributes, list):
        data.setdefault("voice_attributes", attributes)


def _inject_messaging_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    pillars = _safe_get(handoff, "messaging_pillars", default=[])
    if isinstance(pillars, list):
        data.setdefault("messaging_pillars", pillars)
    data.setdefault("executive_summary", _safe_get(handoff, "executive_summary"))


def _inject_campaign_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    data.setdefault("cta", _safe_get(handoff, "cta"))
    data.setdefault("business_model", _safe_get(handoff, "business_model"))


def _inject_social_data(data: dict, output: dict) -> None:
    handoff = output.get("handoff", output)
    channels = _safe_get(handoff, "channels", default=[])
    if isinstance(channels, list):
        data.setdefault("channels", channels)
    themes = _safe_get(handoff, "content_themes", default=[])
    if isinstance(themes, list):
        data.setdefault("content_themes", themes)


# ---------------------------------------------------------------------------
# State persistence (follows notebooklm_publisher pattern)
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

class MarpDeckGenerator:
    """Generate branded PDF slide decks using Marp CLI."""

    def __init__(
        self,
        brand_dir: Path,
        config: dict,
        config_path: Path,
        console: Optional[Console] = None,
        deck_filter: Optional[Set[str]] = None,
        force: bool = False,
    ):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.config_path = Path(config_path)
        self.console = console or Console()
        self.deck_filter = deck_filter
        self.force = force

        self.outputs_dir = self.brand_dir / ".brandmint" / "outputs"
        self.deliverables_dir = self.brand_dir / "deliverables" / "decks"
        self.theme_dir = self.brand_dir / "deliverables" / ".themes"
        self.state_path = self.brand_dir / ".brandmint" / "decks-state.json"

        self.state: dict = {} if force else _load_state(self.state_path)
        self.brand_name = config.get("brand", {}).get("name", "Brand")

        # Template directory
        self.templates_dir = Path(__file__).parent / "deck_templates"

    def generate(self) -> bool:
        """Generate all configured slide decks. Returns True on success."""
        started = time.time()

        # Preflight
        if not self._check_marp():
            return False

        # Export theme
        exporter = BrandThemeExporter(self.config, self.theme_dir)
        css_path = exporter.export_marp_css()
        self.console.print(f"  [green]\u2713[/green] Brand CSS theme exported")

        # Load skill outputs
        skill_outputs = _load_skill_outputs(self.outputs_dir)
        self.console.print(
            f"  [green]\u2713[/green] Loaded {len(skill_outputs)} skill outputs"
        )

        # Generate decks
        defs = self._filtered_defs()
        self.deliverables_dir.mkdir(parents=True, exist_ok=True)
        all_ok = True

        for deck_def in defs:
            ok = self._generate_deck(deck_def, skill_outputs, css_path)
            if not ok:
                all_ok = False

        # Save state
        elapsed = time.time() - started
        self.state["updated_at"] = datetime.now().isoformat()
        self.state["elapsed_seconds"] = round(elapsed, 1)
        _save_state(self.state, self.state_path)

        self.console.print(
            f"\n  Decks generated in {elapsed:.1f}s → {self.deliverables_dir}"
        )
        return all_ok

    def _check_marp(self) -> bool:
        """Check if marp CLI is installed."""
        if shutil.which("marp"):
            return True
        self.console.print(
            "[red]Marp CLI not found.[/red]\n"
            "Install with: [bold]npm install -g @marp-team/marp-cli[/bold]"
        )
        return False

    def _generate_deck(
        self,
        deck_def: dict,
        skill_outputs: Dict[str, dict],
        css_path: Path,
    ) -> bool:
        """Generate a single slide deck."""
        deck_id = deck_def["id"]

        # Check idempotency
        existing = self.state.get(deck_id, {})
        if existing.get("status") == "completed" and not self.force:
            self.console.print(f"  [dim]\u23ed {deck_id} \u2014 already generated[/dim]")
            return True

        self.console.print(f"  \u23f3 Generating {deck_def['title']}...")

        # Load and render Jinja2 template
        template_path = self.templates_dir / deck_def["template"]
        if not template_path.is_file():
            self.console.print(f"  [red]Template not found: {template_path}[/red]")
            return False

        try:
            from jinja2 import Environment, FileSystemLoader
        except ImportError:
            self.console.print(
                "[red]Jinja2 not installed.[/red]\n"
                "Install with: [bold]pip install jinja2[/bold]"
            )
            return False

        env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            undefined=__import__("jinja2").Undefined,
        )
        template = env.get_template(deck_def["template"])

        # Extract data
        data = _extract_deck_data(deck_id, self.config, skill_outputs)
        rendered_md = template.render(**data)

        # Write markdown
        md_path = self.deliverables_dir / f"{deck_id}.md"
        md_path.write_text(rendered_md)

        # Run Marp CLI
        output_pdf = self.deliverables_dir / deck_def["output_filename"]
        cmd = [
            "marp",
            "--theme", str(css_path),
            "--pdf",
            "--allow-local-files",
            str(md_path),
            "-o", str(output_pdf),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and output_pdf.exists():
                size_kb = output_pdf.stat().st_size / 1024
                self.state[deck_id] = {
                    "status": "completed",
                    "path": str(output_pdf),
                    "size_kb": round(size_kb, 1),
                    "generated_at": datetime.now().isoformat(),
                }
                _save_state(self.state, self.state_path)
                self.console.print(
                    f"  [green]\u2713[/green] {deck_def['output_filename']} ({size_kb:.1f} KB)"
                )
                return True
            else:
                error = (result.stderr or result.stdout or "")[:300]
                self.state[deck_id] = {"status": "failed", "error": error}
                _save_state(self.state, self.state_path)
                self.console.print(f"  [red]\u2717 {deck_id} failed: {error}[/red]")
                return False
        except subprocess.TimeoutExpired:
            self.state[deck_id] = {"status": "failed", "error": "Timeout"}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {deck_id} timed out[/red]")
            return False
        except Exception as e:
            self.state[deck_id] = {"status": "failed", "error": str(e)[:300]}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {deck_id} error: {e}[/red]")
            return False

    def _filtered_defs(self) -> List[dict]:
        if self.deck_filter:
            return [d for d in DECK_DEFINITIONS if d["id"] in self.deck_filter]
        return list(DECK_DEFINITIONS)
