"""
Diagram Generator — produces mind maps and diagrams from brand data.

Uses:
- Markmap CLI for interactive mind map HTML + SVG
- Mermaid CLI (mmdc) for flowcharts, journey maps, quadrant charts

Produces 4 diagrams by default:
- Brand Ecosystem Mind Map (Markmap → HTML + SVG)
- Customer Journey Map (Mermaid → SVG)
- Brand Architecture Diagram (Mermaid → SVG)
- Competitive Positioning Quadrant (Mermaid → SVG)
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

from .theme_exporter import BrandThemeExporter, _extract_brand_info, _extract_colors


# ---------------------------------------------------------------------------
# Diagram definitions
# ---------------------------------------------------------------------------

DIAGRAM_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "brand-ecosystem",
        "title": "Brand Ecosystem Mind Map",
        "type": "markmap",
        "output_files": ["brand-ecosystem-mindmap.html", "brand-ecosystem-mindmap.svg"],
        "description": "Interactive mind map of the full brand ecosystem",
    },
    {
        "id": "customer-journey",
        "title": "Customer Journey Map",
        "type": "mermaid",
        "output_files": ["customer-journey.svg"],
        "description": "Awareness → purchase → retention journey",
    },
    {
        "id": "brand-architecture",
        "title": "Brand Architecture Diagram",
        "type": "mermaid",
        "output_files": ["brand-architecture.svg"],
        "description": "Brand hierarchy and product relationships",
    },
    {
        "id": "competitive-positioning",
        "title": "Competitive Positioning Quadrant",
        "type": "mermaid",
        "output_files": ["competitive-positioning.svg"],
        "description": "Market positioning map vs competitors",
    },
]


# ---------------------------------------------------------------------------
# Data-to-markup generators
# ---------------------------------------------------------------------------

def _generate_mindmap_markdown(config: dict, skill_outputs: Dict[str, dict]) -> str:
    """Generate a Markdown hierarchy for Markmap from brand data."""
    brand = config.get("brand", {})
    brand_name = brand.get("name", "Brand")
    tagline = brand.get("tagline", "")

    lines = [f"# {brand_name}"]
    if tagline:
        lines.append(f"\n> {tagline}\n")

    # Products
    products = config.get("products", {})
    if products:
        lines.append("## Products")
        hero = products.get("hero", "")
        if isinstance(hero, dict):
            lines.append(f"### {hero.get('name', 'Hero Product')}")
            if hero.get("description"):
                lines.append(f"- {hero['description']}")
        elif isinstance(hero, str) and hero:
            lines.append(f"### {hero}")
        for key, val in products.items():
            if key == "hero":
                continue
            if isinstance(val, str):
                lines.append(f"### {val}")
            elif isinstance(val, dict) and val.get("name"):
                lines.append(f"### {val['name']}")

    # Audience (from buyer-persona)
    persona = skill_outputs.get("buyer-persona", {}).get("handoff", {})
    if persona:
        lines.append("## Target Audience")
        pname = persona.get("persona_name", "Primary Persona")
        lines.append(f"### {pname}")
        for key in ("demographics", "psychographics", "motivations"):
            val = persona.get(key)
            if isinstance(val, str):
                lines.append(f"- {key.title()}: {val}")
            elif isinstance(val, list):
                for item in val[:3]:
                    lines.append(f"- {item}")

    # Channels (from social-content-engine)
    social = skill_outputs.get("social-content-engine", {}).get("handoff", {})
    channels = social.get("channels", [])
    if channels:
        lines.append("## Channels")
        for ch in channels:
            if isinstance(ch, dict):
                lines.append(f"### {ch.get('name', ch)}")
                if ch.get("strategy"):
                    lines.append(f"- {ch['strategy']}")
            elif isinstance(ch, str):
                lines.append(f"### {ch}")

    # Visual Identity
    palette = config.get("palette", {})
    if palette:
        lines.append("## Visual Identity")
        lines.append("### Colour Palette")
        for role in ("primary", "secondary", "accent"):
            entry = palette.get(role, {})
            if isinstance(entry, dict) and entry.get("name"):
                lines.append(f"- {role.title()}: {entry['name']} ({entry.get('hex', '')})")
        typo = config.get("typography", {})
        if typo:
            lines.append("### Typography")
            for role in ("header", "body"):
                entry = typo.get(role, {})
                if isinstance(entry, dict) and entry.get("font"):
                    lines.append(f"- {role.title()}: {entry['font']}")

    # Voice & Tone
    voice = brand.get("voice", "")
    tone = brand.get("tone", "")
    if voice or tone:
        lines.append("## Voice & Tone")
        if voice:
            lines.append(f"- Voice: {voice}")
        if tone:
            lines.append(f"- Tone: {tone}")

    # Positioning
    positioning = skill_outputs.get("product-positioning-summary", {}).get("handoff", {})
    if positioning:
        lines.append("## Positioning")
        vp = positioning.get("value_proposition", "")
        if vp:
            lines.append(f"- {vp}")
        pillars = positioning.get("identity_pillars", [])
        if isinstance(pillars, list):
            for p in pillars[:4]:
                if isinstance(p, dict):
                    lines.append(f"### {p.get('name', p)}")
                elif isinstance(p, str):
                    lines.append(f"### {p}")

    return "\n".join(lines)


def _generate_journey_mermaid(config: dict, skill_outputs: Dict[str, dict]) -> str:
    """Generate Mermaid journey diagram DSL."""
    brand_name = config.get("brand", {}).get("name", "Brand")
    persona = skill_outputs.get("buyer-persona", {}).get("handoff", {})
    persona_name = persona.get("persona_name", "Customer")

    lines = [f"journey"]
    lines.append(f"    title {persona_name}'s Journey with {brand_name}")
    lines.append(f"    section Awareness")
    lines.append(f"        Discovers brand: 3: {persona_name}")
    lines.append(f"        Sees content: 4: {persona_name}")
    lines.append(f"    section Consideration")
    lines.append(f"        Explores product: 4: {persona_name}")
    lines.append(f"        Reads reviews: 3: {persona_name}")
    lines.append(f"        Compares alternatives: 3: {persona_name}")
    lines.append(f"    section Purchase")
    lines.append(f"        Makes decision: 5: {persona_name}")
    lines.append(f"        Completes purchase: 5: {persona_name}")
    lines.append(f"    section Retention")
    lines.append(f"        Uses product: 5: {persona_name}")
    lines.append(f"        Shares experience: 4: {persona_name}")
    lines.append(f"    section Advocacy")
    lines.append(f"        Recommends brand: 5: {persona_name}")
    lines.append(f"        Joins community: 4: {persona_name}")

    return "\n".join(lines)


def _generate_architecture_mermaid(config: dict, skill_outputs: Dict[str, dict]) -> str:
    """Generate Mermaid graph for brand architecture."""
    brand_name = config.get("brand", {}).get("name", "Brand")
    products = config.get("products", {})

    lines = ["graph TD"]
    lines.append(f'    BRAND["{brand_name}"]')

    # Sub-brands / product lines
    hero = products.get("hero", "")
    if isinstance(hero, dict) and hero.get("name"):
        lines.append(f'    HERO["{hero["name"]}"]')
        lines.append(f"    BRAND --> HERO")
    elif isinstance(hero, str) and hero:
        lines.append(f'    HERO["{hero}"]')
        lines.append(f"    BRAND --> HERO")

    idx = 0
    for key, val in products.items():
        if key == "hero":
            continue
        if isinstance(val, dict) and val.get("name"):
            node = f"PROD{idx}"
            lines.append(f'    {node}["{val["name"]}"]')
            lines.append(f"    BRAND --> {node}")
            idx += 1
        elif isinstance(val, str) and val:
            node = f"PROD{idx}"
            lines.append(f'    {node}["{val}"]')
            lines.append(f"    BRAND --> {node}")
            idx += 1

    # Add audience and channels as connected nodes
    lines.append(f'    AUD["Target Audience"]')
    lines.append(f"    BRAND --> AUD")
    lines.append(f'    VIS["Visual Identity"]')
    lines.append(f"    BRAND --> VIS")
    lines.append(f'    VOI["Voice & Tone"]')
    lines.append(f"    BRAND --> VOI")

    # Style
    lines.append(f"    style BRAND fill:{_extract_colors(config).get('primary', '#1A1A2E')},color:#fff")

    return "\n".join(lines)


def _generate_positioning_mermaid(config: dict, skill_outputs: Dict[str, dict]) -> str:
    """Generate Mermaid quadrant chart for competitive positioning."""
    brand_name = config.get("brand", {}).get("name", "Brand")
    competitors_out = skill_outputs.get("competitor-analysis", {}).get("handoff", {})
    competitors = competitors_out.get("competitors", [])

    lines = ["quadrantChart"]
    lines.append("    title Competitive Positioning")
    lines.append('    x-axis "Low Innovation" --> "High Innovation"')
    lines.append('    y-axis "Low Brand Equity" --> "High Brand Equity"')

    # Place our brand in the top-right quadrant
    lines.append(f"    {brand_name}: [0.8, 0.8]")

    # Place competitors
    if isinstance(competitors, list):
        positions = [
            (0.3, 0.6), (0.5, 0.4), (0.6, 0.5),
            (0.4, 0.7), (0.2, 0.3), (0.7, 0.3),
        ]
        for i, comp in enumerate(competitors[:6]):
            name = comp.get("name", f"Competitor {i+1}") if isinstance(comp, dict) else str(comp)
            # Sanitize name for Mermaid
            safe_name = name.replace('"', "'").replace(":", "-")
            x, y = positions[i % len(positions)]
            lines.append(f"    {safe_name}: [{x}, {y}]")

    return "\n".join(lines)


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

class DiagramGenerator:
    """Generate mind maps and diagrams using Markmap and Mermaid CLI."""

    def __init__(
        self,
        brand_dir: Path,
        config: dict,
        config_path: Path,
        console: Optional[Console] = None,
        diagram_filter: Optional[Set[str]] = None,
        force: bool = False,
    ):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.config_path = Path(config_path)
        self.console = console or Console()
        self.diagram_filter = diagram_filter
        self.force = force

        self.outputs_dir = self.brand_dir / ".brandmint" / "outputs"
        self.deliverables_dir = self.brand_dir / "deliverables" / "diagrams"
        self.theme_dir = self.brand_dir / "deliverables" / ".themes"
        self.state_path = self.brand_dir / ".brandmint" / "diagrams-state.json"

        self.state: dict = {} if force else _load_state(self.state_path)
        self.brand_name = config.get("brand", {}).get("name", "Brand")

    def generate(self) -> bool:
        """Generate all configured diagrams. Returns True on success."""
        started = time.time()

        # Check tools
        has_markmap = shutil.which("markmap")
        has_mmdc = shutil.which("mmdc")

        if not has_markmap and not has_mmdc:
            self.console.print(
                "[red]Neither markmap nor mmdc (Mermaid CLI) found.[/red]\n"
                "Install with:\n"
                "  [bold]npm install -g markmap-cli[/bold]\n"
                "  [bold]npm install -g @mermaid-js/mermaid-cli[/bold]"
            )
            return False

        # Export theme configs
        exporter = BrandThemeExporter(self.config, self.theme_dir)
        exporter.export_all()
        self.console.print(f"  [green]\u2713[/green] Theme configs exported")

        # Load skill outputs
        skill_outputs = _load_skill_outputs(self.outputs_dir)
        self.console.print(
            f"  [green]\u2713[/green] Loaded {len(skill_outputs)} skill outputs"
        )

        self.deliverables_dir.mkdir(parents=True, exist_ok=True)
        defs = self._filtered_defs()
        all_ok = True

        for diagram_def in defs:
            dtype = diagram_def["type"]

            if dtype == "markmap" and not has_markmap:
                self.console.print(
                    f"  [yellow]\u23ed Skipping {diagram_def['id']} (markmap not installed)[/yellow]"
                )
                continue
            if dtype == "mermaid" and not has_mmdc:
                self.console.print(
                    f"  [yellow]\u23ed Skipping {diagram_def['id']} (mmdc not installed)[/yellow]"
                )
                continue

            ok = self._generate_diagram(diagram_def, skill_outputs)
            if not ok:
                all_ok = False

        elapsed = time.time() - started
        self.state["updated_at"] = datetime.now().isoformat()
        self.state["elapsed_seconds"] = round(elapsed, 1)
        _save_state(self.state, self.state_path)

        self.console.print(
            f"\n  Diagrams generated in {elapsed:.1f}s \u2192 {self.deliverables_dir}"
        )
        return all_ok

    def _generate_diagram(
        self,
        diagram_def: dict,
        skill_outputs: Dict[str, dict],
    ) -> bool:
        diag_id = diagram_def["id"]

        existing = self.state.get(diag_id, {})
        if existing.get("status") == "completed" and not self.force:
            self.console.print(f"  [dim]\u23ed {diag_id} \u2014 already generated[/dim]")
            return True

        self.console.print(f"  \u23f3 Generating {diagram_def['title']}...")

        if diagram_def["type"] == "markmap":
            return self._generate_markmap(diagram_def, skill_outputs)
        elif diagram_def["type"] == "mermaid":
            return self._generate_mermaid(diagram_def, skill_outputs)
        return False

    def _generate_markmap(
        self,
        diagram_def: dict,
        skill_outputs: Dict[str, dict],
    ) -> bool:
        diag_id = diagram_def["id"]
        md_content = _generate_mindmap_markdown(self.config, skill_outputs)

        md_path = self.deliverables_dir / f"{diag_id}.md"
        md_path.write_text(md_content)

        # Load markmap options for brand colors
        options_path = self.theme_dir / "markmap-options.json"

        # Generate HTML
        html_output = self.deliverables_dir / diagram_def["output_files"][0]
        cmd = ["markmap", str(md_path), "-o", str(html_output), "--no-open"]
        if options_path.exists():
            cmd.extend(["--options", str(options_path)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                error = (result.stderr or result.stdout or "")[:300]
                self.state[diag_id] = {"status": "failed", "error": error}
                _save_state(self.state, self.state_path)
                self.console.print(f"  [red]\u2717 {diag_id} failed: {error}[/red]")
                return False
        except (subprocess.TimeoutExpired, Exception) as e:
            self.state[diag_id] = {"status": "failed", "error": str(e)[:300]}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {diag_id} error: {e}[/red]")
            return False

        # Also try to generate SVG if markmap supports it
        if len(diagram_def["output_files"]) > 1:
            svg_output = self.deliverables_dir / diagram_def["output_files"][1]
            svg_cmd = ["markmap", str(md_path), "-o", str(svg_output), "--no-open"]
            if options_path.exists():
                svg_cmd.extend(["--options", str(options_path)])
            try:
                subprocess.run(svg_cmd, capture_output=True, text=True, timeout=30)
            except Exception:
                pass  # SVG is bonus, HTML is primary

        outputs = [f for f in diagram_def["output_files"]
                   if (self.deliverables_dir / f).exists()]
        self.state[diag_id] = {
            "status": "completed",
            "files": outputs,
            "generated_at": datetime.now().isoformat(),
        }
        _save_state(self.state, self.state_path)
        self.console.print(
            f"  [green]\u2713[/green] {', '.join(outputs)}"
        )
        return True

    def _generate_mermaid(
        self,
        diagram_def: dict,
        skill_outputs: Dict[str, dict],
    ) -> bool:
        diag_id = diagram_def["id"]

        # Generate appropriate Mermaid DSL
        generators = {
            "customer-journey": _generate_journey_mermaid,
            "brand-architecture": _generate_architecture_mermaid,
            "competitive-positioning": _generate_positioning_mermaid,
        }
        gen_fn = generators.get(diag_id)
        if not gen_fn:
            self.console.print(f"  [red]No generator for diagram: {diag_id}[/red]")
            return False

        mmd_content = gen_fn(self.config, skill_outputs)
        mmd_path = self.deliverables_dir / f"{diag_id}.mmd"
        mmd_path.write_text(mmd_content)

        # Load Mermaid config for brand theme
        config_path = self.theme_dir / "mermaid-config.json"

        svg_output = self.deliverables_dir / diagram_def["output_files"][0]
        cmd = ["mmdc", "-i", str(mmd_path), "-o", str(svg_output)]
        if config_path.exists():
            cmd.extend(["-c", str(config_path)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and svg_output.exists():
                size_kb = svg_output.stat().st_size / 1024
                self.state[diag_id] = {
                    "status": "completed",
                    "files": diagram_def["output_files"],
                    "size_kb": round(size_kb, 1),
                    "generated_at": datetime.now().isoformat(),
                }
                _save_state(self.state, self.state_path)
                self.console.print(
                    f"  [green]\u2713[/green] {diagram_def['output_files'][0]} ({size_kb:.1f} KB)"
                )
                return True
            else:
                error = (result.stderr or result.stdout or "")[:300]
                self.state[diag_id] = {"status": "failed", "error": error}
                _save_state(self.state, self.state_path)
                self.console.print(f"  [red]\u2717 {diag_id} failed: {error}[/red]")
                return False
        except subprocess.TimeoutExpired:
            self.state[diag_id] = {"status": "failed", "error": "Timeout"}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {diag_id} timed out[/red]")
            return False
        except Exception as e:
            self.state[diag_id] = {"status": "failed", "error": str(e)[:300]}
            _save_state(self.state, self.state_path)
            self.console.print(f"  [red]\u2717 {diag_id} error: {e}[/red]")
            return False

    def _filtered_defs(self) -> List[dict]:
        if self.diagram_filter:
            return [d for d in DIAGRAM_DEFINITIONS if d["id"] in self.diagram_filter]
        return list(DIAGRAM_DEFINITIONS)


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
