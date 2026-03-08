"""
Skills Registry - Unified catalog bridging orchestrator and Claude skills.

Adds source-aware conflict handling, alias resolution, and unified recursive
skill discovery for local + external skill packs.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..models.skill import SkillMetadata, SkillSource, UnifiedSkill

# Discovery candidates in priority order.
SKILL_FILE_CANDIDATES = ("SKILL.md", "skill.md", "instructions.md")

# Known compatibility aliases.
DEFAULT_ID_ALIASES = {
    "buyer-persona": "buyer-persona-generator",
}

# Known duplicate family roots inside ~/.claude/skills where IDs are mirrored.
CLAUDE_VARIANT_PREFIXES = {"thinking", "utilities"}
CLAUDE_DOCUMENT_SKILLS_PREFIX = "document-skills"
CLAUDE_DOCUMENTS_PREFIX = "documents"

# Conflict handling policies.
CONFLICT_POLICY_ERROR = "error"
CONFLICT_POLICY_WARN_SKIP = "warn_skip"
CONFLICT_POLICY_WARN_OVERWRITE = "warn_overwrite"
ALLOWED_CONFLICT_POLICIES = {
    CONFLICT_POLICY_ERROR,
    CONFLICT_POLICY_WARN_SKIP,
    CONFLICT_POLICY_WARN_OVERWRITE,
}


class SkillsRegistry:
    """Discovers, merges, and manages skills from multiple sources."""

    # Package root for local brand skills discovery.
    _PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent

    def __init__(
        self,
        skills_dir: Optional[Path] = None,
        claude_skills_dir: Optional[Path] = None,
        brand_skills_dir: Optional[Path] = None,
        conflict_policy: Optional[str] = None,
    ):
        self.skills_dir = skills_dir or (self._PACKAGE_ROOT / "skills")
        self.claude_skills_dir = claude_skills_dir or (Path.home() / ".claude" / "skills")
        self.brand_skills_dir = brand_skills_dir or (self._PACKAGE_ROOT / "skills")

        self.skills: Dict[str, UnifiedSkill] = {}
        self.aliases: Dict[str, str] = dict(DEFAULT_ID_ALIASES)
        self.conflicts: List[Dict[str, str]] = []
        self.warnings: List[str] = []
        self.conflict_policy = self._normalize_conflict_policy(conflict_policy)

        self._load_all_skills()

    def _normalize_conflict_policy(self, policy: Optional[str]) -> str:
        """Normalize and validate conflict policy from arg/env/default."""
        raw = (
            policy
            or os.environ.get("BRANDMINT_SKILL_CONFLICT_POLICY")
            or CONFLICT_POLICY_WARN_SKIP
        )
        normalized = raw.strip().lower().replace("+", "_")
        if normalized not in ALLOWED_CONFLICT_POLICIES:
            return CONFLICT_POLICY_WARN_SKIP
        return normalized

    def _warn(self, message: str) -> None:
        self.warnings.append(message)
        if os.environ.get("BRANDMINT_SKILL_REGISTRY_DEBUG", "").strip() == "1":
            print(f"[SkillsRegistry] {message}")

    def _load_all_skills(self) -> None:
        """Load skills from all sources.

        Load order (later sources attempt to override earlier sources):
        1. Orchestrator manifest (skills/manifest.yaml)
        2. Local brand skills (brandmint/skills/**/SKILL.md)
        3. Claude skills (~/.claude/skills/**/SKILL.md)

        Conflicts are governed by ``self.conflict_policy``.
        """
        sources: List[tuple[str, List[UnifiedSkill]]] = [
            ("orchestrator", self._load_orchestrator_skills()),
            ("local", self._load_local_brand_skills()),
            ("claude", self._load_claude_skills()),
        ]

        for source_name, source_skills in sources:
            for skill in source_skills:
                self._register_skill(skill, source_name)

    def _register_skill(self, skill: UnifiedSkill, source_name: str) -> None:
        """Register a skill with conflict policy applied."""
        existing = self.skills.get(skill.id)
        if existing is None:
            self.skills[skill.id] = skill
            return

        if self._is_mergeable_duplicate(existing, skill):
            self._merge_skills(existing, skill)
            return

        conflict = {
            "skill_id": skill.id,
            "existing_source": existing.source.value,
            "incoming_source": skill.source.value,
            "existing_path": existing.skill_md_path or existing.template_path or "",
            "incoming_path": skill.skill_md_path or skill.template_path or "",
            "detected_from": source_name,
        }
        self.conflicts.append(conflict)

        message = (
            f"Conflict for skill '{skill.id}': "
            f"existing={conflict['existing_path'] or conflict['existing_source']} "
            f"incoming={conflict['incoming_path'] or conflict['incoming_source']}"
        )

        if self.conflict_policy == CONFLICT_POLICY_ERROR:
            raise ValueError(message)

        if self.conflict_policy == CONFLICT_POLICY_WARN_OVERWRITE:
            self._warn(message + " (policy=warn_overwrite, incoming kept)")
            self.skills[skill.id] = skill
            return

        # warn_skip (default)
        self._warn(message + " (policy=warn_skip, existing kept)")

    def _is_mergeable_duplicate(self, existing: UnifiedSkill, incoming: UnifiedSkill) -> bool:
        """Return True when duplicate IDs are effectively same skill definition.

        We treat duplicates as mergeable when:
        - They point to the same underlying file path, OR
        - They are known duplicate folder variants in ~/.claude/skills, OR
        - One side only contains manifest/template metadata and the other
          provides markdown metadata.
        """
        existing_path = self._resolve_path(existing.skill_md_path)
        incoming_path = self._resolve_path(incoming.skill_md_path)

        if existing_path and incoming_path:
            if existing_path == incoming_path:
                return True
            if self._is_same_claude_variant_skill(existing_path, incoming_path):
                return True
            return False

        # Manifest/local/claude merge path: one side may have only template path.
        if not existing_path or not incoming_path:
            return True

        return False

    def _is_same_claude_variant_skill(self, existing_path: Path, incoming_path: Path) -> bool:
        """Return True if both paths represent the same known claude duplicate family."""
        existing_key = self._canonical_claude_variant_key(existing_path)
        incoming_key = self._canonical_claude_variant_key(incoming_path)
        return bool(existing_key and incoming_key and existing_key == incoming_key)

    def _canonical_claude_variant_key(self, skill_path: Path) -> Optional[str]:
        """Normalize known claude variant roots to a canonical skill key.

        Example mappings:
        - Thinking/Foo -> Foo
        - Utilities/Foo -> Foo
        - document-skills/docx -> Documents/Docx
        """
        root = self._resolve_path(str(self.claude_skills_dir))
        if root is None:
            return None

        try:
            rel_parts = list(skill_path.relative_to(root).parts)
        except Exception:
            return None

        # Drop markdown filename.
        if not rel_parts:
            return None
        parent_parts = rel_parts[:-1]
        if not parent_parts:
            return None

        first = parent_parts[0].lower()
        if first in CLAUDE_VARIANT_PREFIXES:
            parent_parts = parent_parts[1:]
        elif first == CLAUDE_DOCUMENT_SKILLS_PREFIX:
            parent_parts = [CLAUDE_DOCUMENTS_PREFIX, *parent_parts[1:]]

        if not parent_parts:
            return None

        return "/".join(self._normalize_skill_id(part) for part in parent_parts)

    def _resolve_path(self, path_str: Optional[str]) -> Optional[Path]:
        if not path_str:
            return None
        try:
            p = Path(path_str).expanduser()
            if p.exists():
                return p.resolve()
            return p.absolute()
        except Exception:
            return None

    def _merge_skills(self, existing: UnifiedSkill, incoming: UnifiedSkill) -> None:
        """Merge incoming data into existing skill record."""
        if existing.source != incoming.source:
            existing.source = SkillSource.BOTH

        # Keep the first discovered markdown path as canonical.
        if incoming.skill_md_path and not existing.skill_md_path:
            existing.skill_md_path = incoming.skill_md_path

        if incoming.template_path and not existing.template_path:
            existing.template_path = incoming.template_path

        if incoming.description and (
            not existing.description or len(incoming.description) > len(existing.description)
        ):
            existing.description = incoming.description

        if incoming.protocol_steps and not existing.protocol_steps:
            existing.protocol_steps = incoming.protocol_steps

        existing.required_keys = sorted(set(existing.required_keys + incoming.required_keys))
        existing.upstream_dependencies = sorted(
            set(existing.upstream_dependencies + incoming.upstream_dependencies)
        )

        if incoming.metadata.estimated_tokens > existing.metadata.estimated_tokens:
            existing.metadata = incoming.metadata

    def _load_orchestrator_skills(self) -> List[UnifiedSkill]:
        """Load skills from skills/manifest.yaml."""
        manifest_path = self.skills_dir / "manifest.yaml"

        if not manifest_path.exists():
            return []

        with open(manifest_path) as f:
            data = yaml.safe_load(f)

        skills = []
        for part in data.get("parts", []):
            for skill_data in part.get("skills", []):
                skill = UnifiedSkill(
                    id=skill_data["id"],
                    name=skill_data["name"],
                    source=SkillSource.ORCHESTRATOR,
                    template_path=skill_data.get("path"),
                    required_keys=skill_data.get("required_keys", []),
                    upstream_dependencies=skill_data.get("upstream", []),
                    metadata=self._estimate_metadata(skill_data),
                )
                skills.append(skill)

        return skills

    def _load_local_brand_skills(self) -> List[UnifiedSkill]:
        """Discover skills from brandmint repo skills/**/SKILL.md."""
        if not self.brand_skills_dir.exists():
            return []

        skills: List[UnifiedSkill] = []
        for skill_md in self._discover_skill_files(self.brand_skills_dir, recursive=True):
            skill = self._parse_claude_skill(skill_md)
            if skill:
                skills.append(skill)

        return skills

    def _load_claude_skills(self) -> List[UnifiedSkill]:
        """Discover skills from ~/.claude/skills/**/(SKILL.md|skill.md|instructions.md)."""
        if not self.claude_skills_dir.exists():
            return []

        skills: List[UnifiedSkill] = []
        for skill_md in self._discover_skill_files(self.claude_skills_dir, recursive=True):
            skill = self._parse_claude_skill(skill_md)
            if skill:
                skills.append(skill)

        return skills

    def _discover_skill_files(self, base_dir: Path, recursive: bool = True) -> List[Path]:
        """Discover candidate skill markdown files with deterministic precedence."""
        if not base_dir.exists():
            return []

        selected_by_parent: Dict[str, Path] = {}

        for candidate in SKILL_FILE_CANDIDATES:
            iterator = base_dir.rglob(candidate) if recursive else base_dir.glob(f"*/{candidate}")
            for file_path in iterator:
                if not file_path.is_file():
                    continue
                parts = set(file_path.parts)
                if ".git" in parts or "node_modules" in parts or "__pycache__" in parts:
                    continue
                # Vendor upstream snapshots are source archives, not active skill surfaces.
                if "external" in parts and "upstream" in parts:
                    continue

                parent_key = str(file_path.parent.absolute())
                if parent_key in selected_by_parent:
                    continue

                selected_by_parent[parent_key] = file_path

        return sorted(selected_by_parent.values(), key=lambda p: str(p))

    def _parse_claude_skill(self, skill_md: Path) -> Optional[UnifiedSkill]:
        """Parse a skill markdown file."""
        try:
            content = skill_md.read_text(encoding="utf-8", errors="ignore")

            # Extract frontmatter
            frontmatter = self._extract_frontmatter(content)

            # instructions.md is only considered when explicitly frontmatter-based.
            if skill_md.name.lower() == "instructions.md" and not frontmatter.get("name"):
                return None

            name = str(frontmatter.get("name") or skill_md.parent.name).strip()
            description = str(frontmatter.get("description") or "").strip()

            # Extract protocol steps
            protocol_steps = self._extract_protocol_steps(content)

            # Estimate token cost based on content length
            estimated_tokens = max(3000, len(content) // 3)

            # Normalize IDs and register aliases for folder-name mismatch.
            skill_id = self._normalize_skill_id(name)
            folder_id = self._normalize_skill_id(skill_md.parent.name)

            if folder_id and folder_id != skill_id:
                self.aliases.setdefault(folder_id, skill_id)

            raw_aliases = frontmatter.get("aliases")
            if isinstance(raw_aliases, str):
                raw_aliases = [raw_aliases]
            if isinstance(raw_aliases, list):
                for alias in raw_aliases:
                    alias_id = self._normalize_skill_id(str(alias))
                    if alias_id and alias_id != skill_id:
                        self.aliases.setdefault(alias_id, skill_id)

            skill = UnifiedSkill(
                id=skill_id,
                name=name,
                source=SkillSource.CLAUDE,
                skill_md_path=str(skill_md),
                description=description,
                protocol_steps=protocol_steps,
                metadata=SkillMetadata(
                    estimated_tokens=estimated_tokens,
                    complexity=self._estimate_complexity(len(protocol_steps)),
                ),
            )

            return skill

        except Exception as e:
            self._warn(f"Failed to parse {skill_md}: {e}")
            return None

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from skill markdown.

        Accepts both LF and CRLF newlines.
        """
        match = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.DOTALL)
        if not match:
            return {}

        try:
            parsed = yaml.safe_load(match.group(1)) or {}
            if isinstance(parsed, dict):
                return parsed
            return {}
        except Exception:
            return {}

    def _extract_protocol_steps(self, content: str) -> List[str]:
        """Extract numbered protocol steps."""
        steps = []
        pattern = r"^\d+\.\s+(.+)$"
        for line in content.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                steps.append(match.group(1))
        return steps

    def _normalize_skill_id(self, name: str) -> str:
        """Normalize skill names into canonical kebab-case IDs."""
        normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return normalized or name.lower().strip()

    def _estimate_complexity(self, num_steps: int) -> str:
        """Estimate complexity from protocol length."""
        if num_steps < 5:
            return "low"
        if num_steps < 15:
            return "medium"
        if num_steps < 30:
            return "high"
        return "very_high"

    def _estimate_metadata(self, skill_data: Dict[str, Any]) -> SkillMetadata:
        """Estimate metadata for orchestrator skills."""
        num_keys = len(skill_data.get("required_keys", []))
        num_deps = len(skill_data.get("upstream", []))

        # Simple heuristic
        estimated_tokens = 5000 + (num_keys * 500) + (num_deps * 300)

        complexity = "medium"
        if num_keys > 10 or num_deps > 3:
            complexity = "high"
        elif num_keys < 3 and num_deps < 2:
            complexity = "low"

        return SkillMetadata(
            estimated_tokens=estimated_tokens,
            complexity=complexity,
        )

    def get_skill(self, skill_id: str) -> Optional[UnifiedSkill]:
        """Get a skill by ID, resolving known aliases."""
        if not skill_id:
            return None

        direct = self.skills.get(skill_id)
        if direct:
            return direct

        normalized = self._normalize_skill_id(skill_id)
        normalized_direct = self.skills.get(normalized)
        if normalized_direct:
            return normalized_direct

        alias_target = self.aliases.get(skill_id) or self.aliases.get(normalized)
        if alias_target:
            return self.skills.get(alias_target)

        return None

    def get_all_skills(self) -> List[UnifiedSkill]:
        """Get all skills."""
        return list(self.skills.values())

    def get_conflicts(self) -> List[Dict[str, str]]:
        """Get detected ID conflicts during load."""
        return list(self.conflicts)

    def get_warnings(self) -> List[str]:
        """Get non-fatal registry warnings."""
        return list(self.warnings)

    def get_aliases(self) -> Dict[str, str]:
        """Get alias -> canonical ID map."""
        return dict(self.aliases)

    def get_skills_by_source(self, source: SkillSource) -> List[UnifiedSkill]:
        """Get skills from a specific source."""
        return [s for s in self.skills.values() if s.source == source]

    def get_skills_for_scenario(self, skill_ids: List[str]) -> List[UnifiedSkill]:
        """Get resolved skill objects for a list of IDs (alias-aware)."""
        resolved: List[UnifiedSkill] = []
        seen_ids = set()

        for skill_id in skill_ids:
            skill = self.get_skill(skill_id)
            if not skill:
                continue
            if skill.id in seen_ids:
                continue
            seen_ids.add(skill.id)
            resolved.append(skill)

        return resolved

    def estimate_total_cost(
        self,
        skill_ids: List[str],
        depth_level: str = "focused",
        output_format: str = "standard",
    ) -> Dict[str, Any]:
        """Estimate total cost for a set of skills."""
        breakdown = []
        total_tokens = 0

        for requested_skill_id in skill_ids:
            skill = self.get_skill(requested_skill_id)
            if skill:
                tokens = skill.estimate_cost(depth_level, output_format)
                total_tokens += tokens
                breakdown.append(
                    {
                        "requested_skill_id": requested_skill_id,
                        "resolved_skill_id": skill.id,
                        "skill_name": skill.name,
                        "tokens": tokens,
                        "usd": tokens * 0.25,  # Rough $0.25 per 1K tokens
                    }
                )

        return {
            "total_tokens": total_tokens,
            "total_usd": int(total_tokens * 0.25),
            "per_skill_breakdown": breakdown,
        }

    def find_skills_by_tag(self, tag: str) -> List[UnifiedSkill]:
        """Find skills by tag (placeholder for future tagging system)."""
        _ = tag
        return []

    def sync_to_file(self, output_path: Path) -> None:
        """Export unified registry to JSON."""
        import json

        data = {
            "skills": [s.model_dump() for s in self.skills.values()],
            "total_count": len(self.skills),
            "by_source": {
                "orchestrator": len(self.get_skills_by_source(SkillSource.ORCHESTRATOR)),
                "claude": len(self.get_skills_by_source(SkillSource.CLAUDE)),
                "both": len(self.get_skills_by_source(SkillSource.BOTH)),
            },
            "aliases": self.aliases,
            "conflicts": self.conflicts,
            "conflict_policy": self.conflict_policy,
        }

        output_path.write_text(json.dumps(data, indent=2))
        print(f"✓ Synced {len(self.skills)} skills to {output_path}")
