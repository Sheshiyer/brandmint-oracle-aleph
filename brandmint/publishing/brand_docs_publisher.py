from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from rich.console import Console

from .brand_docs_localization import localized_page_metadata, localized_page_paths, render_localized_page_body


PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_SKILL_DIR = PACKAGE_ROOT / "skills" / "publishing" / "wiki-doc-generator"
ASTRO_SKILL_DIR = PACKAGE_ROOT / "skills" / "publishing" / "markdown-to-astro-wiki"


@dataclass(frozen=True)
class PageSpec:
    path: str
    title: str
    description: str
    category: str
    tags: List[str]
    source_ids: List[str]
    order: int
    icon: str


PAGE_SPECS: List[PageSpec] = [
    PageSpec(
        "index.md",
        "Launch Dossier Index",
        "High-level index of the latest launch documentation, key outputs, and research deliverables.",
        "general",
        ["overview", "launch", "docs"],
        [],
        1,
        "🏠",
    ),
    PageSpec(
        "getting-started/quickstart.md",
        "Quickstart",
        "Fast navigation guide for the latest docs, visuals, NotebookLM artifacts, and published outputs.",
        "general",
        ["quickstart", "launch", "runbook"],
        [],
        2,
        "🚀",
    ),
    PageSpec(
        "product/overview.md",
        "Product Overview",
        "Core product story, positioning, and hero-product definition for the current launch build.",
        "product",
        ["product", "overview", "hero"],
        ["detailed-product-description", "product-positioning-summary", "mds-messaging-direction-summary"],
        1,
        "📦",
    ),
    PageSpec(
        "product/features.md",
        "Product Features",
        "Feature-level framing, use-case context, and supporting campaign details for the current product line.",
        "product",
        ["product", "features", "detail"],
        ["detailed-product-description", "campaign-page-copy"],
        2,
        "✨",
    ),
    PageSpec(
        "product/specifications.md",
        "Product Specifications",
        "Canonical spec, material references, and product-detail context for the current product configuration.",
        "product",
        ["product", "specifications", "materials"],
        ["detailed-product-description"],
        3,
        "🧵",
    ),
    PageSpec(
        "brand/voice-tone.md",
        "Voice & Tone",
        "Voice system, writing guardrails, and narrative guidance across launch touchpoints and channels.",
        "brand",
        ["brand", "voice", "tone"],
        ["voice-and-tone"],
        1,
        "🗣️",
    ),
    PageSpec(
        "brand/visual-guidelines.md",
        "Visual Guidelines",
        "Visual identity, palette, typography, and art-direction guidance that anchor the current brand expression.",
        "brand",
        ["brand", "visual", "guidelines"],
        ["visual-identity-core"],
        2,
        "🎨",
    ),
    PageSpec(
        "brand/visual-assets.md",
        "Visual Assets Library",
        "Curated library of generated visuals and surfaced NotebookLM infographics for the latest launch run.",
        "brand",
        ["brand", "assets", "gallery"],
        [],
        3,
        "🖼️",
    ),
    PageSpec(
        "audience/primary-persona.md",
        "Primary Persona",
        "Primary buyer persona insights, motivations, and trust triggers for the current launch audience.",
        "audience",
        ["audience", "persona", "buyer"],
        ["buyer-persona"],
        1,
        "👪",
    ),
    PageSpec(
        "audience/secondary-personas.md",
        "Secondary Personas",
        "Supporting audience segments, adjacent needs, and persona comparisons derived from the campaign outputs.",
        "audience",
        ["audience", "personas", "segments"],
        ["buyer-persona", "competitor-analysis"],
        2,
        "🧭",
    ),
    PageSpec(
        "market/competitive-landscape.md",
        "Competitive Landscape",
        "Market context, competitor framing, and differentiation logic supporting the current launch strategy.",
        "audience",
        ["market", "competition", "landscape"],
        ["competitor-analysis"],
        3,
        "🥊",
    ),
    PageSpec(
        "marketing/campaign-copy.md",
        "Campaign Copy",
        "Campaign-level launch messaging, narrative framing, and conversion-oriented copy assets for the launch push.",
        "marketing",
        ["marketing", "campaign", "copy"],
        ["campaign-page-copy", "campaign-video-script", "press-release-copy"],
        1,
        "📝",
    ),
    PageSpec(
        "marketing/email-templates.md",
        "Email Templates",
        "Welcome, pre-launch, and launch email assets organized for direct review and publishing use.",
        "marketing",
        ["marketing", "email", "templates"],
        ["welcome-email-sequence", "pre-launch-email-sequence", "launch-email-sequence"],
        2,
        "✉️",
    ),
    PageSpec(
        "marketing/social-content.md",
        "Social Content",
        "Social publishing plans, creator support material, and always-on content direction for the launch window.",
        "marketing",
        ["marketing", "social", "content"],
        ["social-content-engine", "influencer-outreach-pro"],
        3,
        "📣",
    ),
    PageSpec(
        "marketing/video-scripts.md",
        "Video Scripts",
        "Video and motion storytelling scripts that support campaign presentation and launch storytelling.",
        "marketing",
        ["marketing", "video", "script"],
        ["campaign-video-script"],
        4,
        "🎬",
    ),
    PageSpec(
        "marketing/ad-creative.md",
        "Ad Creative",
        "Pre-launch and live-campaign advertising concepts, copy, and creative direction for paid acquisition.",
        "marketing",
        ["marketing", "ads", "creative"],
        ["pre-launch-ads", "live-campaign-ads"],
        5,
        "🎯",
    ),
    PageSpec(
        "research/notebooklm-artifacts.md",
        "NotebookLM Artifacts",
        "Research hub for NotebookLM-generated reports, decks, audio, infographics, tables, and structured study outputs.",
        "general",
        ["research", "notebooklm", "artifacts"],
        [],
        1,
        "🧠",
    ),
]


NAVIGATION = [
    {"title": "Getting Started", "items": ["index.md", "getting-started/quickstart.md"]},
    {"title": "product", "items": ["product/overview.md", "product/features.md", "product/specifications.md"]},
    {"title": "brand", "items": ["brand/voice-tone.md", "brand/visual-guidelines.md", "brand/visual-assets.md"]},
    {"title": "audience", "items": ["audience/primary-persona.md", "audience/secondary-personas.md", "market/competitive-landscape.md"]},
    {"title": "marketing", "items": ["marketing/campaign-copy.md", "marketing/email-templates.md", "marketing/social-content.md", "marketing/video-scripts.md", "marketing/ad-creative.md"]},
    {"title": "general", "items": ["research/notebooklm-artifacts.md"]},
]


class BrandDocsPublisher:
    """Generate brand docs markdown and an Astro wiki site for the latest run."""

    def __init__(self, brand_dir: Path, config: dict, config_path: Path, console: Optional[Console] = None):
        self.brand_dir = Path(brand_dir)
        self.config = config
        self.config_path = Path(config_path)
        self.console = console or Console()
        self.outputs_dir = self.brand_dir / ".brandmint" / "outputs"
        self.wiki_output_dir = self.brand_dir / "wiki-output"
        self.wiki_output_fr_dir = self.brand_dir / "wiki-output-fr"
        self.wiki_site_dir = self.brand_dir / "wiki-site"
        self.deliverables_dir = self.brand_dir / "deliverables" / "brand-docs"
        self.report_path = self.deliverables_dir / "publish-report.json"
        self.latest_symlink = self.brand_dir / "published-site"
        self.generated_dir = self._resolve_generated_dir()
        self.notebooklm_artifacts_dir = self.brand_dir / "deliverables" / "notebooklm" / "artifacts"
        self.generated_at = datetime.now()

    def publish(self) -> bool:
        if not self.outputs_dir.is_dir():
            self.console.print(f"[red]Outputs directory not found: {self.outputs_dir}[/red]")
            return False

        self._prepare_output_dirs()
        outputs = self._load_outputs()
        inventory = self._run_inventory()
        asset_map = self._run_asset_map()
        notebooklm = self._scan_notebooklm_artifacts()

        self._write_wiki_docs(outputs, inventory, asset_map, notebooklm)
        self._write_localized_wiki_docs(outputs, inventory, asset_map, notebooklm)
        self._validate_wiki()
        self._build_astro_site(outputs, asset_map, notebooklm)
        self._write_report(outputs, inventory, asset_map, notebooklm)
        self.console.print(f"[green]✓[/green] Wave 8 docs published: {self.wiki_site_dir / 'dist'}")
        return True

    def _resolve_generated_dir(self) -> Optional[Path]:
        brand_name = self.config.get("brand", {}).get("name", "brand")
        slug = slugify(brand_name)
        for candidate in [self.brand_dir / slug / "generated", self.brand_dir / "generated"]:
            if candidate.is_dir():
                return candidate
        return None

    def _prepare_output_dirs(self) -> None:
        for path in [self.wiki_output_dir, self.wiki_output_fr_dir, self.wiki_site_dir, self.deliverables_dir]:
            if not path.exists():
                continue
            self._remove_path(path)
        self.wiki_output_dir.mkdir(parents=True, exist_ok=True)
        self.deliverables_dir.mkdir(parents=True, exist_ok=True)

    def _remove_path(self, path: Path) -> None:
        if path.is_symlink() or path.is_file():
            path.unlink()
            return
        try:
            shutil.rmtree(path)
        except OSError:
            subprocess.run(["rm", "-rf", str(path)], check=True)
            if path.exists():
                raise

    def _load_outputs(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for path in sorted(self.outputs_dir.glob("*.json")):
            try:
                results[path.stem] = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
        return results

    def _run_inventory(self) -> Dict[str, Any]:
        script = WIKI_SKILL_DIR / "scripts" / "inventory-sources.py"
        proc = subprocess.run(
            ["python3", str(script), str(self.outputs_dir), "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        inventory = json.loads(proc.stdout)
        (self.wiki_output_dir / "wiki-inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
        return inventory

    def _run_asset_map(self) -> Dict[str, Any]:
        if not self.generated_dir or not self.generated_dir.is_dir():
            return {}
        script = WIKI_SKILL_DIR / "scripts" / "map-assets-to-wiki.py"
        output_path = self.wiki_output_dir / "wiki-asset-map.json"
        subprocess.run(
            ["python3", str(script), str(self.generated_dir), "--output", str(output_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(output_path.read_text())

    def _scan_notebooklm_artifacts(self) -> Dict[str, Any]:
        categories = {
            "reports": [],
            "decks": [],
            "audio": [],
            "infographics": [],
            "tables": [],
            "flashcards": [],
            "quizzes": [],
            "mind_maps": [],
            "other": [],
        }
        all_items: List[Dict[str, Any]] = []

        if not self.notebooklm_artifacts_dir.is_dir():
            return {**categories, "all": [], "counts": {key: 0 for key in categories}}

        for path in sorted(self.notebooklm_artifacts_dir.iterdir()):
            if not path.is_file():
                continue
            item = self._classify_notebooklm_artifact(path)
            all_items.append(item)
            categories[item["bucket"]].append(item)

        counts = {bucket: len(items) for bucket, items in categories.items()}
        return {**categories, "all": all_items, "counts": counts}

    def _classify_notebooklm_artifact(self, path: Path) -> Dict[str, Any]:
        name = path.name
        route = f"/notebooklm/{name}"
        stem = path.stem
        entry: Dict[str, Any] = {
            "file": name,
            "path": str(path),
            "route": route,
            "slug": stem,
            "size_bytes": path.stat().st_size,
        }

        if name.startswith("report-") and path.suffix == ".md":
            title, excerpt, body = parse_markdown_artifact(path)
            entry.update(
                {
                    "bucket": "reports",
                    "kind": "Report",
                    "title": title,
                    "summary": excerpt,
                    "doc_path": f"research/{stem}.md",
                    "doc_href": f"/docs/research/{stem}",
                    "body": body,
                }
            )
            return entry

        if name.startswith("deck-") and path.suffix == ".pdf":
            entry.update(
                {
                    "bucket": "decks",
                    "kind": "Deck",
                    "title": humanize_artifact_name(name),
                    "summary": "Presentation-ready NotebookLM export in PDF format.",
                }
            )
            return entry

        if name.startswith("audio-") and path.suffix == ".mp3":
            entry.update(
                {
                    "bucket": "audio",
                    "kind": "Audio",
                    "title": humanize_artifact_name(name),
                    "summary": "NotebookLM-generated audio briefing for listening review.",
                }
            )
            return entry

        if name.startswith("infographic-") and path.suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            entry.update(
                {
                    "bucket": "infographics",
                    "kind": "Infographic",
                    "title": humanize_artifact_name(name),
                    "summary": "NotebookLM visual summary artifact surfaced in the media library.",
                    "image_route": route,
                }
            )
            return entry

        if name.startswith("table-") and path.suffix == ".csv":
            columns, rows = inspect_csv(path)
            entry.update(
                {
                    "bucket": "tables",
                    "kind": "Data Table",
                    "title": humanize_artifact_name(name),
                    "summary": f"CSV export with {rows} rows and {len(columns)} columns.",
                    "columns": columns,
                    "row_count": rows,
                }
            )
            return entry

        if name.startswith("flashcards-") and path.suffix == ".json":
            count = inspect_json_count(path, ["cards"])
            entry.update(
                {
                    "bucket": "flashcards",
                    "kind": "Flashcards",
                    "title": humanize_artifact_name(name),
                    "summary": f"NotebookLM flashcard deck with {count} cards." if count is not None else "NotebookLM flashcard export.",
                    "item_count": count,
                }
            )
            return entry

        if name.startswith("quiz-") and path.suffix == ".json":
            count = inspect_json_count(path, ["questions"])
            entry.update(
                {
                    "bucket": "quizzes",
                    "kind": "Quiz",
                    "title": humanize_artifact_name(name),
                    "summary": f"NotebookLM quiz set with {count} questions." if count is not None else "NotebookLM quiz export.",
                    "item_count": count,
                }
            )
            return entry

        if name == "mind-map.json":
            count = inspect_json_count(path, ["mind_map", "nodes"])
            entry.update(
                {
                    "bucket": "mind_maps",
                    "kind": "Mind Map",
                    "title": "Mind Map",
                    "summary": f"NotebookLM mind-map export with {count} mapped nodes." if count is not None else "NotebookLM mind-map export.",
                    "item_count": count,
                }
            )
            return entry

        entry.update(
            {
                "bucket": "other",
                "kind": "Artifact",
                "title": humanize_artifact_name(name),
                "summary": "NotebookLM-generated artifact included for provenance and download.",
            }
        )
        return entry

    def _write_wiki_docs(
        self,
        outputs: Dict[str, Any],
        inventory: Dict[str, Any],
        asset_map: Dict[str, Any],
        notebooklm: Dict[str, Any],
    ) -> None:
        navigation = [{"title": group["title"], "items": list(group["items"])} for group in NAVIGATION]

        for spec in PAGE_SPECS:
            page_path = self.wiki_output_dir / spec.path
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(self._render_page(spec, outputs, inventory, asset_map, notebooklm), encoding="utf-8")

        for index, artifact in enumerate(notebooklm.get("reports", []), start=10):
            page_path = self.wiki_output_dir / artifact["doc_path"]
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(self._render_notebooklm_report_page(artifact, index), encoding="utf-8")
            navigation[-1]["items"].append(artifact["doc_path"])

        navigation_path = self.wiki_output_dir / "navigation.yaml"
        navigation_path.write_text(yaml.safe_dump(navigation, sort_keys=False, allow_unicode=True), encoding="utf-8")

    def _write_localized_wiki_docs(
        self,
        outputs: Dict[str, Any],
        inventory: Dict[str, Any],
        asset_map: Dict[str, Any],
        notebooklm: Dict[str, Any],
    ) -> None:
        for locale in ["fr"]:
            localized_paths = set(localized_page_paths(locale, self.config))
            for spec in PAGE_SPECS:
                if spec.path not in localized_paths:
                    continue
                metadata = localized_page_metadata(locale, spec.path, self.config)
                if not metadata:
                    continue
                body = render_localized_page_body(
                    locale,
                    spec.path,
                    outputs=outputs,
                    config=self.config,
                    config_path=self.config_path,
                    brand_dir=self.brand_dir,
                    notebooklm=notebooklm,
                )
                if not body:
                    continue
                frontmatter = {
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "category": spec.category,
                    "tags": spec.tags,
                    "sources": [f"{source_id}.json" for source_id in spec.source_ids],
                    "lastUpdated": self.generated_at.date().isoformat(),
                    "order": spec.order,
                    "icon": spec.icon,
                }
                target_dir = self.wiki_output_fr_dir if locale == "fr" else self.wiki_output_dir
                page_path = target_dir / spec.path
                page_path.parent.mkdir(parents=True, exist_ok=True)
                content = "\n".join([
                    "---",
                    yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
                    "---",
                    "",
                    body.rstrip(),
                    "",
                ])
                page_path.write_text(content, encoding="utf-8")

    def _render_page(
        self,
        spec: PageSpec,
        outputs: Dict[str, Any],
        inventory: Dict[str, Any],
        asset_map: Dict[str, Any],
        notebooklm: Dict[str, Any],
    ) -> str:
        frontmatter = {
            "title": spec.title,
            "description": spec.description,
            "category": spec.category,
            "tags": spec.tags,
            "sources": [f"{source_id}.json" for source_id in spec.source_ids],
            "lastUpdated": self.generated_at.date().isoformat(),
            "order": spec.order,
            "icon": spec.icon,
        }
        parts = ["---", yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip(), "---", "", f"# {spec.title}", ""]

        if spec.path != "research/notebooklm-artifacts.md":
            parts.extend(self._render_page_images(spec.path, asset_map))

        if spec.path == "index.md":
            parts.extend(self._render_index(inventory, notebooklm))
        elif spec.path == "getting-started/quickstart.md":
            parts.extend(self._render_quickstart(notebooklm))
        elif spec.path == "brand/visual-assets.md":
            parts.extend(self._render_visual_assets_library(asset_map, notebooklm))
        elif spec.path == "brand/visual-guidelines.md":
            parts.extend(self._render_brand_visual_guidelines(outputs))
            parts.extend(self._render_sources(outputs, spec.source_ids))
        elif spec.path == "product/specifications.md":
            parts.extend(self._render_product_specifications(outputs))
            parts.extend(self._render_sources(outputs, spec.source_ids))
        elif spec.path == "research/notebooklm-artifacts.md":
            parts.extend(self._render_notebooklm_artifacts_page(notebooklm))
        else:
            parts.extend(self._render_sources(outputs, spec.source_ids))

        return "\n".join(parts).rstrip() + "\n"

    def _render_index(self, inventory: Dict[str, Any], notebooklm: Dict[str, Any]) -> List[str]:
        docs_count = len(list(self.outputs_dir.glob("*.json")))
        lines = [
            "This dossier index summarizes the latest launch documentation build.",
            "",
            "## Launch Snapshot",
            "",
            f"- **Brand:** {self.config.get('brand', {}).get('name', 'Brand')}",
            f"- **Tagline:** {self.config.get('brand', {}).get('tagline', '')}",
            f"- **Run root:** `{self.brand_dir}`",
            f"- **Source outputs:** `{self.outputs_dir}`",
            f"- **NotebookLM artifacts:** `{self.notebooklm_artifacts_dir}`",
            f"- **Published site:** `{self.wiki_site_dir / 'dist'}`",
            f"- **Structured outputs available:** {docs_count}",
            f"- **NotebookLM artifacts surfaced:** {len(notebooklm.get('all', []))}",
            "",
            "## Primary Sections",
            "",
        ]
        for group in NAVIGATION:
            lines.append(f"### {group['title']}")
            for item in group["items"]:
                label = Path(item).stem.replace("-", " ").title()
                lines.append(f"- [{label}]({item})")
            lines.append("")
        lines.extend(
            [
                "## Inventory Snapshot",
                "",
                f"- **Source directory:** `{inventory.get('source_directory', self.outputs_dir)}`",
                f"- **Documents classified:** {len(inventory.get('documents', []))}",
                f"- **Agent groups available:** {', '.join(sorted(inventory.get('agent_dispatch', {}).keys())) or 'none'}",
                "",
            ]
        )
        return lines

    def _render_quickstart(self, notebooklm: Dict[str, Any]) -> List[str]:
        lines = [
            "Use this page to find the latest launch outputs quickly.",
            "",
            "## Key Paths",
            "",
            f"- **Config:** `{self.config_path}`",
            f"- **JSON outputs:** `{self.outputs_dir}`",
            f"- **Generated images:** `{self.generated_dir}`" if self.generated_dir else "- **Generated images:** not available",
            f"- **NotebookLM artifacts:** `{self.notebooklm_artifacts_dir}`",
            f"- **Wiki markdown:** `{self.wiki_output_dir}`",
            f"- **Astro project:** `{self.wiki_site_dir}`",
            f"- **Published site build:** `{self.wiki_site_dir / 'dist'}`",
            "",
            "## Product Reference Policy",
            "",
            "- NotebookLM image sources in this run were restricted to the configured product reference images only.",
            "- Visual generation references come from the product images declared in `brand-config.yaml`.",
            "- NotebookLM generated deliverables are now ingested into the Wave 8 wiki system as first-class research and media artifacts.",
            "",
            "## NotebookLM Coverage",
            "",
            f"- **Reports:** {len(notebooklm.get('reports', []))}",
            f"- **Infographics:** {len(notebooklm.get('infographics', []))}",
            f"- **Decks:** {len(notebooklm.get('decks', []))}",
            f"- **Audio briefings:** {len(notebooklm.get('audio', []))}",
            f"- **Structured study assets:** {len(notebooklm.get('tables', [])) + len(notebooklm.get('flashcards', [])) + len(notebooklm.get('quizzes', [])) + len(notebooklm.get('mind_maps', []))}",
            "",
        ]
        return lines

    def _render_brand_visual_guidelines(self, outputs: Dict[str, Any]) -> List[str]:
        lines = [
            "## Palette & Typography",
            "",
            f"- **Primary:** {self.config.get('palette', {}).get('primary', {}).get('name', '')} {self.config.get('palette', {}).get('primary', {}).get('hex', '')}",
            f"- **Secondary:** {self.config.get('palette', {}).get('secondary', {}).get('name', '')} {self.config.get('palette', {}).get('secondary', {}).get('hex', '')}",
            f"- **Accent:** {self.config.get('palette', {}).get('accent', {}).get('name', '')} {self.config.get('palette', {}).get('accent', {}).get('hex', '')}",
            f"- **Header font:** {self.config.get('typography', {}).get('header', {}).get('font', '')}",
            f"- **Body font:** {self.config.get('typography', {}).get('body', {}).get('font', '')}",
            "",
            "## Visual Identity Summary",
            "",
        ]
        lines.extend(self._render_json_block(outputs.get("visual-identity-core", {}), level=3))
        return lines

    def _render_product_specifications(self, outputs: Dict[str, Any]) -> List[str]:
        hero = self.config.get("products", {}).get("hero", {})
        lines = [
            "## Canonical Product Spec",
            "",
            f"- **Name:** {hero.get('name', '')}",
            f"- **Description:** {hero.get('description', '')}",
            f"- **Physical form:** {hero.get('physical_form', '')}",
            "",
            "## Materials",
            "",
        ]
        for item in self.config.get("materials", []):
            lines.append(f"- {item}")
        lines.extend(["", "## Detailed Product Source", ""])
        lines.extend(self._render_json_block(outputs.get("detailed-product-description", {}), level=3))
        return lines

    def _render_visual_assets_library(self, asset_map: Dict[str, Any], notebooklm: Dict[str, Any]) -> List[str]:
        gallery = asset_map.get("brand/visual-assets.md", {})
        generated_assets = gallery.get("all_assets", [])
        infographics = notebooklm.get("infographics", [])
        lines = [
            "Curated visual library for the latest launch run.",
            "",
            "## Brandmint Generated Visuals",
            "",
        ]
        for asset in generated_assets:
            file_name = asset.get("file")
            if not file_name:
                continue
            lines.append(f"### {asset.get('asset_id', '?')} — {asset.get('alt', 'Asset')}")
            lines.append("")
            lines.append(f"![{asset.get('alt', 'Asset')}](/images/{file_name})")
            lines.append("")
            lines.append(f"- **Section:** {asset.get('section', 'Unknown')}")
            lines.append(f"- **Variants:** {asset.get('variant_count', 1)}")
            lines.append("")
        if not generated_assets:
            lines.append("_No generated visual assets were mapped for this run._")
            lines.append("")

        lines.extend(["## NotebookLM Infographics", ""])
        for artifact in infographics:
            lines.append(f"### {artifact['title']}")
            lines.append("")
            lines.append(f"![{artifact['title']}]({artifact['route']})")
            lines.append("")
            lines.append(f"- **Type:** {artifact['kind']}")
            lines.append(f"- **Download:** [{artifact['file']}]({artifact['route']})")
            lines.append("")
        if not infographics:
            lines.append("_No NotebookLM infographic artifacts were available for this run._")
            lines.append("")
        return lines

    def _render_notebooklm_artifacts_page(self, notebooklm: Dict[str, Any]) -> List[str]:
        counts = notebooklm.get("counts", {})
        lines = [
            "NotebookLM outputs are treated as first-class publish artifacts in this Wave 8 build.",
            "",
            "## Coverage",
            "",
            f"- **Reports:** {counts.get('reports', 0)}",
            f"- **Decks:** {counts.get('decks', 0)}",
            f"- **Audio:** {counts.get('audio', 0)}",
            f"- **Infographics:** {counts.get('infographics', 0)}",
            f"- **Tables:** {counts.get('tables', 0)}",
            f"- **Flashcards:** {counts.get('flashcards', 0)}",
            f"- **Quizzes:** {counts.get('quizzes', 0)}",
            f"- **Mind Maps:** {counts.get('mind_maps', 0)}",
            "",
        ]

        lines.extend(["## Reports", ""])
        for artifact in notebooklm.get("reports", []):
            lines.append(f"### [{artifact['title']}]({artifact['doc_href']})")
            lines.append("")
            if artifact.get("summary"):
                lines.append(artifact["summary"])
                lines.append("")
            lines.append(f"- **Docs page:** [{artifact['doc_href']}]({artifact['doc_href']})")
            lines.append(f"- **Raw artifact path:** `{artifact['route']}`")
            lines.append("")
        if not notebooklm.get("reports"):
            lines.append("_No NotebookLM report markdown artifacts were found._")
            lines.append("")

        lines.extend(["## Infographics", ""])
        for artifact in notebooklm.get("infographics", []):
            lines.append(f"### {artifact['title']}")
            lines.append("")
            lines.append(f"![{artifact['title']}]({artifact['route']})")
            lines.append("")
            lines.append(f"- **Download:** [{artifact['file']}]({artifact['route']})")
            lines.append("")
        if not notebooklm.get("infographics"):
            lines.append("_No NotebookLM infographics were found._")
            lines.append("")

        lines.extend(self._render_artifact_group("Decks", notebooklm.get("decks", [])))
        lines.extend(self._render_artifact_group("Audio Briefings", notebooklm.get("audio", [])))
        lines.extend(self._render_artifact_group("Data Tables", notebooklm.get("tables", []), show_shape=True))
        lines.extend(self._render_artifact_group("Flashcards", notebooklm.get("flashcards", []), show_shape=True))
        lines.extend(self._render_artifact_group("Quizzes", notebooklm.get("quizzes", []), show_shape=True))
        lines.extend(self._render_artifact_group("Mind Maps", notebooklm.get("mind_maps", []), show_shape=True))
        return lines

    def _render_artifact_group(self, heading: str, artifacts: List[Dict[str, Any]], show_shape: bool = False) -> List[str]:
        lines = [f"## {heading}", ""]
        if not artifacts:
            lines.append(f"_No {heading.lower()} were available for this run._")
            lines.append("")
            return lines

        for artifact in artifacts:
            lines.append(f"### {artifact['title']}")
            lines.append("")
            lines.append(artifact.get("summary", artifact["kind"]))
            lines.append("")
            if show_shape:
                if artifact.get("row_count") is not None:
                    lines.append(f"- **Rows:** {artifact['row_count']}")
                if artifact.get("columns"):
                    lines.append(f"- **Columns:** {', '.join(artifact['columns'])}")
                if artifact.get("item_count") is not None:
                    lines.append(f"- **Items:** {artifact['item_count']}")
            lines.append(f"- **Download:** [{artifact['file']}]({artifact['route']})")
            lines.append("")
        return lines

    def _render_sources(self, outputs: Dict[str, Any], source_ids: List[str]) -> List[str]:
        lines: List[str] = []
        for source_id in source_ids:
            payload = outputs.get(source_id)
            if payload is None:
                continue
            title = source_id.replace("-", " ").title()
            lines.extend([f"## {title}", ""])
            lines.extend(self._render_json_block(payload, level=3))
            lines.append("")
        return lines or ["_No source outputs were available for this page._", ""]

    def _render_page_images(self, page_path: str, asset_map: Dict[str, Any]) -> List[str]:
        mapping = asset_map.get(page_path, {}) if asset_map else {}
        lines: List[str] = []
        hero = mapping.get("hero")
        if hero and hero.get("file"):
            lines.extend([f"![{hero.get('alt', 'Hero image')}](/images/{hero['file']})", ""])
        for img in mapping.get("images", []):
            if img.get("file"):
                lines.extend([f"![{img.get('alt', 'Image')}](/images/{img['file']})", ""])
        for img in mapping.get("gallery", []):
            if img.get("file"):
                lines.extend([f"![{img.get('alt', 'Image')}](/images/{img['file']})", ""])
        return lines

    def _render_json_block(self, value: Any, level: int = 2) -> List[str]:
        heading = "#" * level
        lines: List[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                title = str(key).replace("_", " ").replace("-", " ").title()
                if isinstance(item, (dict, list)):
                    lines.extend([f"{heading} {title}", ""])
                    lines.extend(self._render_json_block(item, level=level + 1))
                else:
                    lines.append(f"- **{title}:** {item}")
            if not value:
                lines.append("_No structured content available._")
        elif isinstance(value, list):
            if not value:
                lines.append("_No items available._")
            elif all(not isinstance(item, (dict, list)) for item in value):
                for item in value:
                    lines.append(f"- {item}")
            else:
                for index, item in enumerate(value, start=1):
                    lines.extend([f"{heading} Item {index}", ""])
                    lines.extend(self._render_json_block(item, level=level + 1))
        elif value is None:
            lines.append("_No structured content available._")
        else:
            lines.append(str(value))
        return lines

    def _render_notebooklm_report_page(self, artifact: Dict[str, Any], order: int) -> str:
        frontmatter = {
            "title": artifact["title"],
            "description": artifact.get("summary") or "NotebookLM report imported into the launch research library.",
            "category": "general",
            "tags": ["research", "notebooklm", "report"],
            "sources": [artifact["file"]],
            "lastUpdated": self.generated_at.date().isoformat(),
            "order": order,
            "icon": "📚",
        }
        parts = ["---", yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip(), "---", "", f"# {artifact['title']}", ""]
        parts.extend(
            [
                trim_excerpt(artifact.get("summary") or "NotebookLM research report surfaced into the Wave 8 docs layer."),
                "",
                f"- **Raw artifact path:** `{artifact['route']}`",
                "",
            ]
        )
        body = artifact.get("body") or ""
        if body:
            parts.append("## Imported Report")
            parts.append("")
            parts.append(body.strip())
            parts.append("")
        return "\n".join(parts).rstrip() + "\n"

    def _validate_wiki(self) -> None:
        script = WIKI_SKILL_DIR / "scripts" / "validate-wiki.py"
        subprocess.run(["python3", str(script), str(self.wiki_output_dir)], check=True)
        if any(self.wiki_output_fr_dir.rglob("*.md")):
            subprocess.run(["python3", str(script), str(self.wiki_output_fr_dir)], check=True)

    def _build_astro_site(self, outputs: Dict[str, Any], asset_map: Dict[str, Any], notebooklm: Dict[str, Any]) -> None:
        init_script = ASTRO_SKILL_DIR / "scripts" / "init-astro-wiki.sh"
        process_script = ASTRO_SKILL_DIR / "scripts" / "process-markdown.sh"
        subprocess.run(["bash", str(init_script), self.wiki_site_dir.name], cwd=self.brand_dir, check=True)

        cmd = [
            "bash",
            str(process_script),
            str(self.wiki_output_dir),
            str(self.wiki_site_dir / "src" / "content" / "docs"),
        ]
        if self.generated_dir and self.generated_dir.is_dir():
            cmd.extend(["--images", str(self.generated_dir)])
        subprocess.run(cmd, check=True)

        if any(self.wiki_output_fr_dir.rglob("*.md")):
            subprocess.run(
                [
                    "bash",
                    str(process_script),
                    str(self.wiki_output_fr_dir),
                    str(self.wiki_site_dir / "src" / "content" / "frDocs"),
                ],
                check=True,
            )

        self._copy_notebooklm_public_assets()
        self._write_site_data(outputs, asset_map, notebooklm)

        subprocess.run(["bun", "install"], cwd=self.wiki_site_dir, check=True)
        subprocess.run(["bun", "run", "build"], cwd=self.wiki_site_dir, check=True)

        if self.latest_symlink.exists() or self.latest_symlink.is_symlink():
            self.latest_symlink.unlink()
        elif self.latest_symlink.is_dir():
            shutil.rmtree(self.latest_symlink)
        self.latest_symlink.symlink_to(self.wiki_site_dir / "dist")

    def _copy_notebooklm_public_assets(self) -> None:
        if not self.notebooklm_artifacts_dir.is_dir():
            return
        target = self.wiki_site_dir / "public" / "notebooklm"
        target.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.notebooklm_artifacts_dir.iterdir()):
            if path.is_file():
                shutil.copy2(path, target / path.name)

    def _write_site_data(self, outputs: Dict[str, Any], asset_map: Dict[str, Any], notebooklm: Dict[str, Any]) -> None:
        hero_image = self._hero_image(asset_map)
        brand_name = self.config.get("brand", {}).get("name", "brand")
        tagline = self.config.get("brand", {}).get("tagline", "Launch Portal")
        theme = self.config.get("theme", {})
        theme_description = theme.get("description", "")
        hero_description = (
            f"{brand_name} brings together product narrative, visual direction, and launch-ready research in one review portal."
        )
        site_data = {
            "brandName": brand_name,
            "tagline": tagline,
            "themeName": theme.get("name", "Brand Theme"),
            "launchChannel": self.config.get("execution_context", {}).get("launch_channel", "launch"),
            "heroTitle": self.config.get("positioning", {}).get("hero_headline", brand_name),
            "heroSubtitle": theme_description or tagline,
            "heroDescription": hero_description,
            "heroPrimaryHref": "/docs/product/overview",
            "heroSecondaryHref": "/docs/research/notebooklm-artifacts",
            "docsHomeHref": "/docs/index",
            "heroImage": hero_image[0],
            "heroImageAlt": hero_image[1],
            "metrics": [
                {"label": "Brandmint outputs", "value": str(len(outputs))},
                {"label": "Visual assets", "value": str(len(asset_map.get('brand/visual-assets.md', {}).get('all_assets', [])))},
                {"label": "NotebookLM artifacts", "value": str(len(notebooklm.get('all', [])))},
                {"label": "Reports surfaced", "value": str(len(notebooklm.get('reports', [])))},
            ],
            "launchFacts": [
                {"label": "Launch channel", "value": self.config.get('execution_context', {}).get('launch_channel', 'launch')},
                {"label": "Quality bar", "value": self.config.get('execution_context', {}).get('quality_bar', 'standard')},
                {"label": "Notebook policy", "value": self.config.get('publishing', {}).get('notebooklm', {}).get('reuse_policy', 'fresh-per-spec')},
                {"label": "Image policy", "value": self.config.get('publishing', {}).get('notebooklm', {}).get('image_source_policy', 'product-reference-only')},
            ],
            "storyPillars": self.config.get("positioning", {}).get("identity_pillars", [])[:5],
            "featuredDocs": self._featured_docs(),
            "visualHighlights": self._visual_highlights(asset_map, notebooklm),
            "notebooklmHighlights": self._notebooklm_highlights(notebooklm),
            "publishedAtHuman": self.generated_at.strftime("%B %d, %Y at %I:%M %p"),
            "runLabel": f"Latest {self.brand_dir.name} launch build",
            "palette": self.config.get("palette", {}),
            "typography": self.config.get("typography", {}),
        }
        site_data_path = self.wiki_site_dir / "src" / "data" / "site-data.json"
        site_data_path.parent.mkdir(parents=True, exist_ok=True)
        site_data_path.write_text(json.dumps(site_data, indent=2), encoding="utf-8")
        (self.wiki_output_dir / "site-data.json").write_text(json.dumps(site_data, indent=2), encoding="utf-8")

    def _hero_image(self, asset_map: Dict[str, Any]) -> Tuple[str, str]:
        hero = asset_map.get("product/overview.md", {}).get("hero")
        if hero and hero.get("file"):
            return (f"/images/{hero['file']}", hero.get("alt", "Hero image"))
        gallery = asset_map.get("brand/visual-assets.md", {}).get("all_assets", [])
        if gallery:
            first = gallery[0]
            if first.get("file"):
                return (f"/images/{first['file']}", first.get("alt", "Hero image"))
        return ("", "")

    def _featured_docs(self) -> List[Dict[str, str]]:
        return [
            {
                "title": "Product Overview",
                "description": "Hero product definition, positioning, and messaging stack for the current launch build.",
                "href": "/docs/product/overview",
                "icon": "📦",
                "eyebrow": "Product",
            },
            {
                "title": "Visual Guidelines",
                "description": "Palette, typography, art direction, and brand-system guardrails for the current run.",
                "href": "/docs/brand/visual-guidelines",
                "icon": "🎨",
                "eyebrow": "Brand System",
            },
            {
                "title": "Campaign Copy",
                "description": "Campaign narratives, key copy assets, and launch-ready messaging organized for review.",
                "href": "/docs/marketing/campaign-copy",
                "icon": "📝",
                "eyebrow": "Campaign",
            },
            {
                "title": "NotebookLM Artifacts",
                "description": "Surfaced reports, infographics, decks, audio, and research tables produced during Wave 7.",
                "href": "/docs/research/notebooklm-artifacts",
                "icon": "🧠",
                "eyebrow": "Research",
            },
        ]

    def _visual_highlights(self, asset_map: Dict[str, Any], notebooklm: Dict[str, Any]) -> List[Dict[str, str]]:
        highlights: List[Dict[str, str]] = []
        for page, eyebrow in [
            ("product/overview.md", "Hero Product"),
            ("brand/visual-guidelines.md", "Brand Identity"),
            ("product/specifications.md", "Product Detail"),
        ]:
            hero = asset_map.get(page, {}).get("hero")
            if hero and hero.get("file"):
                highlights.append(
                    {
                        "title": hero.get("alt", "Visual asset"),
                        "description": f"Primary visual surfaced from {page.replace('.md', '')}.",
                        "href": f"/docs/{page.replace('.md', '')}",
                        "image": f"/images/{hero['file']}",
                        "eyebrow": eyebrow,
                    }
                )
        if notebooklm.get("infographics"):
            infographic = notebooklm["infographics"][0]
            highlights.append(
                {
                    "title": infographic["title"],
                    "description": "NotebookLM infographic surfaced directly into the media library.",
                    "href": "/docs/research/notebooklm-artifacts",
                    "image": infographic["route"],
                    "eyebrow": "NotebookLM",
                }
            )
        return highlights[:4]

    def _notebooklm_highlights(self, notebooklm: Dict[str, Any]) -> List[Dict[str, str]]:
        highlights: List[Dict[str, str]] = []
        for bucket in ["reports", "infographics", "decks", "audio"]:
            if not notebooklm.get(bucket):
                continue
            artifact = notebooklm[bucket][0]
            highlights.append(
                {
                    "title": artifact["title"],
                    "description": artifact.get("summary", artifact.get("kind", "Artifact")),
                    "href": artifact.get("doc_href", "/docs/research/notebooklm-artifacts"),
                    "downloadHref": artifact["route"],
                    "kind": artifact.get("kind", "Artifact"),
                    "image": artifact.get("image_route", ""),
                }
            )
        return highlights[:4]

    def _write_report(
        self,
        outputs: Dict[str, Any],
        inventory: Dict[str, Any],
        asset_map: Dict[str, Any],
        notebooklm: Dict[str, Any],
    ) -> None:
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "brand": self.config.get("brand", {}).get("name", "brand"),
            "run_root": str(self.brand_dir),
            "outputs_dir": str(self.outputs_dir),
            "generated_dir": str(self.generated_dir) if self.generated_dir else None,
            "notebooklm_artifacts_dir": str(self.notebooklm_artifacts_dir),
            "wiki_output_dir": str(self.wiki_output_dir),
            "wiki_output_fr_dir": str(self.wiki_output_fr_dir),
            "wiki_site_dir": str(self.wiki_site_dir),
            "published_site_dir": str(self.wiki_site_dir / "dist"),
            "latest_symlink": str(self.latest_symlink),
            "generated_docs": sorted(str(path.relative_to(self.wiki_output_dir)) for path in self.wiki_output_dir.rglob("*.md")),
            "localized_docs": {
                "fr": sorted(str(path.relative_to(self.wiki_output_fr_dir)) for path in self.wiki_output_fr_dir.rglob("*.md")),
            },
            "output_count": len(outputs),
            "inventory_documents": len(inventory.get("documents", [])),
            "asset_map_pages": sorted(asset_map.keys()),
            "notebooklm_counts": notebooklm.get("counts", {}),
            "notebooklm_report_pages": [artifact.get("doc_path") for artifact in notebooklm.get("reports", [])],
            "published_at": self.generated_at.isoformat(),
        }
        self.report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def humanize_artifact_name(name: str) -> str:
    stem = Path(name).stem
    replacements = {
        "report-blog": "Blog Report",
        "report-briefing": "Briefing Report",
        "report-study-guide": "Study Guide Report",
        "deck-detailed-full": "Detailed Deck — Full",
        "deck-detailed-short": "Detailed Deck — Short",
        "deck-presenter-full": "Presenter Deck — Full",
        "deck-presenter-short": "Presenter Deck — Short",
        "audio-brief-short": "Audio Brief — Short",
        "audio-debate": "Audio Debate",
        "audio-deep-dive-long": "Audio Deep Dive — Long",
        "table-competitive": "Competitive Table",
        "table-persona": "Persona Table",
        "table-product": "Product Table",
        "flashcards-standard": "Flashcards — Standard",
        "flashcards-detailed": "Flashcards — Detailed",
        "quiz-medium": "Quiz — Medium",
        "quiz-hard": "Quiz — Hard",
        "mind-map": "Mind Map",
        "infographic-landscape": "Infographic — Landscape",
        "infographic-portrait": "Infographic — Portrait",
        "infographic-square": "Infographic — Square",
    }
    return replacements.get(stem, stem.replace("-", " ").replace("_", " ").title())


def parse_markdown_artifact(path: Path) -> Tuple[str, str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    title = humanize_artifact_name(path.name)
    body_lines = lines[:]
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            body_lines = lines[index + 1 :]
            break
    excerpt = ""
    paragraph_lines: List[str] = []
    for line in body_lines:
        stripped = line.strip()
        if not stripped:
            if paragraph_lines:
                break
            continue
        if stripped.startswith("#"):
            continue
        paragraph_lines.append(stripped)
    if paragraph_lines:
        excerpt = trim_excerpt(" ".join(paragraph_lines), limit=150)
    body = "\n".join(body_lines).strip()
    return title, excerpt, body


def inspect_csv(path: Path) -> Tuple[List[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    if not rows:
        return ([], 0)
    return (rows[0], max(0, len(rows) - 1))


def inspect_json_count(path: Path, key_path: List[str]) -> Optional[int]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    current: Any = data
    for key in key_path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            current = None
            break
    if isinstance(current, list):
        return len(current)
    if isinstance(current, dict):
        return len(current)
    return None


def trim_excerpt(value: str, limit: int = 160) -> str:
    clean = re.sub(r"\s+", " ", value).strip()
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 1)].rstrip() + "…"
