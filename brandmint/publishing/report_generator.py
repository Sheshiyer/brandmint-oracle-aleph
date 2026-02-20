"""
Typst Report Generator — converts brand data into branded PDF reports.

Uses Typst to compile markup into professional PDF documents.
Produces 3 reports by default:
- Brand Intelligence Report (comprehensive, 8-12 pages)
- Executive One-Pager (single-page summary)
- Competitive Landscape Report (visual comparison matrix)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console

from .theme_exporter import BrandThemeExporter, _extract_brand_info, _extract_colors, _extract_fonts


# ---------------------------------------------------------------------------
# Report definitions
# ---------------------------------------------------------------------------

REPORT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "brand-intelligence",
        "title": "Brand Intelligence Report",
        "template": "brand-intelligence.typ.j2",
        "output_filename": "brand-intelligence-report.pdf",
        "description": "Comprehensive brand analysis (8-12 pages)",
        "data_sources": ["niche-validator", "buyer-persona", "competitor-analysis",
                         "product-positioning-summary", "mds-messaging-direction-summary",
                         "voice-and-tone", "visual-identity-core", "detailed-product-description",
                         "social-content-engine"],
    },
    {
        "id": "executive-one-pager",
        "title": "Executive One-Pager",
        "template": "executive-one-pager.typ.j2",
        "output_filename": "executive-one-pager.pdf",
        "description": "Single-page brand summary",
        "data_sources": ["buyer-persona", "product-positioning-summary",
                         "competitor-analysis", "voice-and-tone"],
    },
    {
        "id": "competitive-landscape",
        "title": "Competitive Landscape Report",
        "template": "competitive-landscape.typ.j2",
        "output_filename": "competitive-landscape-report.pdf",
        "description": "Visual competitor comparison matrix",
        "data_sources": ["competitor-analysis", "niche-validator",
                         "product-positioning-summary"],
    },
]


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def _load_skill_outputs(outputs_dir: Path) -> Dict[str, dict]:
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
    current = data
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, {})
        else:
            return default
    return current if current and current != {} else default


def _extract_report_data(
    report_id: str,
    config: dict,
    skill_outputs: Dict[str, dict],
) -> Dict[str, Any]:
    """Extract template variables for Typst report templates."""
    brand = config.get("brand", {})
    palette = config.get("palette", {})
    typography = config.get("typography", {})

    data: Dict[str, Any] = {
        "brand_name": brand.get("name", "Brand"),
        "tagline": brand.get("tagline", ""),
        "archetype": brand.get("archetype", ""),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "palette": palette,
        "typography": typography,
    }

    # Voice & tone
    voice = brand.get("voice", "")
    tone = brand.get("tone", "")
    data["voice_tone"] = f"{voice}, {tone}" if voice and tone else voice or tone or ""

    # Positioning
    positioning = config.get("positioning", {})
    data["positioning_statement"] = positioning.get("statement", "")

    # From skill outputs
    niche = skill_outputs.get("niche-validator", {}).get("handoff", {})
    persona = skill_outputs.get("buyer-persona", {}).get("handoff", {})
    competitors_out = skill_outputs.get("competitor-analysis", {}).get("handoff", {})
    product = skill_outputs.get("detailed-product-description", {}).get("handoff", {})
    positioning_out = skill_outputs.get("product-positioning-summary", {}).get("handoff", {})
    voice_out = skill_outputs.get("voice-and-tone", {}).get("handoff", {})
    messaging = skill_outputs.get("mds-messaging-direction-summary", {}).get("handoff", {})
    social = skill_outputs.get("social-content-engine", {}).get("handoff", {})

    # Niche / Market
    data["niche_analysis"] = _safe_get(niche, "market_analysis") or _safe_get(niche, "summary")
    data["market_overview"] = _safe_get(niche, "market_overview")
    data["market_size"] = _safe_get(niche, "market_size")
    market_opps = _safe_get(niche, "opportunities", default=[])
    data["market_opportunities"] = market_opps if isinstance(market_opps, list) else []
    market_risks = _safe_get(niche, "risks", default=[])
    data["market_risks"] = market_risks if isinstance(market_risks, list) else []
    data["market_summary"] = _safe_get(niche, "opportunity_summary")

    # Persona
    data["persona_name"] = _safe_get(persona, "persona_name")
    data["persona_overview"] = _safe_get(persona, "summary")
    data["persona_summary"] = _safe_get(persona, "summary")
    motivations = _safe_get(persona, "motivations", default=[])
    data["persona_motivations"] = motivations if isinstance(motivations, list) else []
    pain_points = _safe_get(persona, "pain_points", default=[])
    data["pain_points"] = pain_points if isinstance(pain_points, list) else []

    # Competitors
    comps = _safe_get(competitors_out, "competitors", default=[])
    data["competitors"] = comps if isinstance(comps, list) else []
    data["positioning_analysis"] = _safe_get(competitors_out, "positioning_analysis")

    # Product
    data["product_description"] = _safe_get(product, "description") or _safe_get(product, "overview")
    data["product_summary"] = _safe_get(product, "overview")
    features = _safe_get(product, "features", default=[])
    data["features"] = features if isinstance(features, list) else []
    data["pricing"] = _safe_get(product, "pricing")

    # Positioning
    data["value_proposition"] = _safe_get(positioning_out, "value_proposition")
    if not data["positioning_statement"]:
        data["positioning_statement"] = _safe_get(positioning_out, "positioning_statement")
    pillars = _safe_get(positioning_out, "identity_pillars", default=[])
    data["identity_pillars"] = pillars if isinstance(pillars, list) else []
    data["competitive_moat"] = _safe_get(positioning_out, "competitive_moat")
    data["strategy_summary"] = _safe_get(positioning_out, "strategy_summary")

    # Voice
    data["voice_description"] = _safe_get(voice_out, "voice_description")
    attrs = _safe_get(voice_out, "voice_attributes", default=[])
    data["voice_attributes"] = attrs if isinstance(attrs, list) else []

    # Messaging
    data["executive_summary"] = _safe_get(messaging, "executive_summary")
    msg_pillars = _safe_get(messaging, "messaging_pillars", default=[])
    data["messaging_pillars"] = msg_pillars if isinstance(msg_pillars, list) else []

    # Social/Content
    channels = _safe_get(social, "channels", default=[])
    data["channel_strategy"] = channels if isinstance(channels, list) else []
    content_strategy = _safe_get(social, "content_strategy")
    data["content_strategy"] = content_strategy

    # Custom overrides from deliverables config
    deliverables = config.get("deliverables", {})
    for report_def in deliverables.get("reports", []):
        if report_def.get("id") == report_id:
            if report_def.get("content"):
                data["custom_content"] = report_def["content"]
            break

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

class TypstReportGenerator:
    """Generate branded PDF reports using Typst."""

    def __init__(
        self,
        brand_dir: Path,
        config: dict,
        config_path: Path,
        console: Optional[Console] = None,
        report_filter: Optional[Set[str]] = None,
        force: bool = False,
    ):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.config_path = Path(config_path)
        self.console = console or Console()
        self.report_filter = report_filter
        self.force = force

        self.outputs_dir = self.brand_dir / ".brandmint" / "outputs"
        self.deliverables_dir = self.brand_dir / "deliverables" / "reports"
        self.theme_dir = self.brand_dir / "deliverables" / ".themes"
        self.state_path = self.brand_dir / ".brandmint" / "reports-state.json"

        self.state: dict = {} if force else _load_state(self.state_path)
        self.brand_name = config.get("brand", {}).get("name", "Brand")

        self.templates_dir = Path(__file__).parent / "report_templates"

    def generate(self) -> bool:
        """Generate all configured reports. Returns True on success."""
        started = time.time()

        if not self._check_typst():
            return False

        # Export Typst brand template
        exporter = BrandThemeExporter(self.config, self.theme_dir)
        exporter.export_typst_template()
        self.console.print(f"  [green]\u2713[/green] Typst brand template exported")

        # Load skill outputs
        skill_outputs = _load_skill_outputs(self.outputs_dir)
        self.console.print(
            f"  [green]\u2713[/green] Loaded {len(skill_outputs)} skill outputs"
        )

        # Generate reports
        defs = self._filtered_defs()
        self.deliverables_dir.mkdir(parents=True, exist_ok=True)
        all_ok = True

        for report_def in defs:
            ok = self._generate_report(report_def, skill_outputs)
            if not ok:
                all_ok = False

        elapsed = time.time() - started
        self.state["updated_at"] = datetime.now().isoformat()
        self.state["elapsed_seconds"] = round(elapsed, 1)
        _save_state(self.state, self.state_path)

        self.console.print(
            f"\n  Reports generated in {elapsed:.1f}s \u2192 {self.deliverables_dir}"
        )
        return all_ok

    def _check_typst(self) -> bool:
        if shutil.which("typst"):
            return True
        self.console.print(
            "[red]Typst not found.[/red]\n"
            "Install with: [bold]brew install typst[/bold]"
        )
        return False

    def _generate_report(
        self,
        report_def: dict,
        skill_outputs: Dict[str, dict],
    ) -> bool:
        report_id = report_def["id"]

        existing = self.state.get(report_id, {})
        if existing.get("status") == "completed" and not self.force:
            self.console.print(f"  [dim]\u23ed {report_id} \u2014 already generated[/dim]")
            return True

        self.console.print(f"  \u23f3 Generating {report_def['title']}...")

        template_path = self.templates_dir / report_def["template"]
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
        template = env.get_template(report_def["template"])

        data = _extract_report_data(report_id, self.config, skill_outputs)
        rendered_typ = template.render(**data)

        # Write Typst source (alongside brand template)
        typ_path = self.deliverables_dir / f"{report_id}.typ"
        typ_path.write_text(rendered_typ)

        # Copy brand template to same dir (Typst imports are relative)
        brand_template_src = self.theme_dir / "brand-template.typ"
        brand_template_dst = self.deliverables_dir / "brand-template.typ"
        if brand_template_src.exists():
            shutil.copy2(brand_template_src, brand_template_dst)

        # Compile with Typst
        output_pdf = self.deliverables_dir / report_def["output_filename"]
        cmd = ["typst", "compile", str(typ_path), str(output_pdf)]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and output_pdf.exists():
                size_kb = output_pdf.stat().st_size / 1024
                self.state[report_id] = {
                    "status": "completed",
                    "path": str(output_pdf),
                    "size_kb": round(size_kb, 1),
                    "generated_at": datetime.now().isoformat(),
                }
                _save_state(self.state, self.state_path)
                self.console.print(
                    f"  [green]\u2713[/green] {report_def['output_filename']} ({size_kb:.1f} KB)"
                )
                return True
            else:
                error = (result.stderr or result.stdout or "")[:500]
                self.state[report_id] = {"status": "failed", "error": error}
                _save_state(self.state, self.state_path)
                self.console.print(f"  [red]\u2717 {report_id} failed: {error}[/red]")
                return False
        except subprocess.TimeoutExpired:
            self.state[report_id] = {"status": "failed", "error": "Timeout"}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {report_id} timed out[/red]")
            return False
        except Exception as e:
            self.state[report_id] = {"status": "failed", "error": str(e)[:300]}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {report_id} error: {e}[/red]")
            return False

    def _filtered_defs(self) -> List[dict]:
        if self.report_filter:
            return [d for d in REPORT_DEFINITIONS if d["id"] in self.report_filter]
        return list(REPORT_DEFINITIONS)
