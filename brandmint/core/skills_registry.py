"""
Skills Registry - Unified catalog bridging orchestrator and Claude skills
Phase 2 implementation
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models.skill import UnifiedSkill, SkillSource, SkillMetadata, QualityTier


class SkillsRegistry:
    """
    Discovers, merges, and manages skills from multiple sources
    """

    # Package root for local brand skills discovery
    _PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent

    def __init__(
        self,
        skills_dir: Optional[Path] = None,
        claude_skills_dir: Optional[Path] = None,
        brand_skills_dir: Optional[Path] = None,
    ):
        self.skills_dir = skills_dir or (self._PACKAGE_ROOT / "skills")
        self.claude_skills_dir = claude_skills_dir or (Path.home() / ".claude" / "skills")
        self.brand_skills_dir = brand_skills_dir or (self._PACKAGE_ROOT / "skills")

        self.skills: Dict[str, UnifiedSkill] = {}
        self._load_all_skills()
    
    def _load_all_skills(self):
        """Load skills from all sources.

        Load order (later sources take precedence on conflict):
        1. Orchestrator manifest (skills/manifest.yaml)
        2. Local brand skills (brandmint/skills/**/SKILL.md)
        3. Claude skills (~/.claude/skills/*/SKILL.md)
        """
        # Load from orchestrator manifest
        orchestrator_skills = self._load_orchestrator_skills()

        # Load from local brand skills (new — lives in brandmint repo)
        local_brand_skills = self._load_local_brand_skills()

        # Load from Claude skills
        claude_skills = self._load_claude_skills()

        # Merge: orchestrator first, then local brand, then Claude (highest priority)
        for skill in orchestrator_skills:
            self.skills[skill.id] = skill

        for skill in local_brand_skills:
            if skill.id in self.skills:
                self.skills[skill.id].source = SkillSource.BOTH
                self.skills[skill.id].skill_md_path = skill.skill_md_path
                if skill.description:
                    self.skills[skill.id].description = skill.description
            else:
                self.skills[skill.id] = skill

        for skill in claude_skills:
            if skill.id in self.skills:
                self.skills[skill.id].source = SkillSource.BOTH
                self.skills[skill.id].skill_md_path = skill.skill_md_path
                if skill.description:
                    self.skills[skill.id].description = skill.description
            else:
                self.skills[skill.id] = skill
    
    def _load_orchestrator_skills(self) -> List[UnifiedSkill]:
        """Load skills from skills/manifest.yaml"""
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
        """Discover skills from brandmint repo skills/**/SKILL.md"""
        if not self.brand_skills_dir.exists():
            return []

        skills = []

        for skill_md in self.brand_skills_dir.rglob("SKILL.md"):
            skill = self._parse_claude_skill(skill_md)
            if skill:
                skills.append(skill)

        return skills

    def _load_claude_skills(self) -> List[UnifiedSkill]:
        """Discover skills from .claude/skills/*/SKILL.md"""
        if not self.claude_skills_dir.exists():
            return []

        skills = []

        for skill_dir in self.claude_skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            # Check both SKILL.md (canonical) and skill.md (legacy)
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                skill_md = skill_dir / "skill.md"
            if not skill_md.exists():
                continue

            skill = self._parse_claude_skill(skill_md)
            if skill:
                skills.append(skill)

        return skills
    
    def _parse_claude_skill(self, skill_md: Path) -> Optional[UnifiedSkill]:
        """Parse a Claude skill.md file"""
        try:
            content = skill_md.read_text()
            
            # Extract frontmatter
            frontmatter = self._extract_frontmatter(content)
            name = frontmatter.get("name", skill_md.parent.name)
            description = frontmatter.get("description", "")
            
            # Extract protocol steps
            protocol_steps = self._extract_protocol_steps(content)
            
            # Estimate token cost based on content length
            estimated_tokens = max(3000, len(content) // 3)
            
            # Normalize ID
            skill_id = name.lower().replace(" ", "-")
            
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
            print(f"Warning: Failed to parse {skill_md}: {e}")
            return None
    
    def _extract_frontmatter(self, content: str) -> Dict[str, str]:
        """Extract YAML frontmatter from skill.md"""
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except:
                return {}
        return {}
    
    def _extract_protocol_steps(self, content: str) -> List[str]:
        """Extract numbered protocol steps"""
        steps = []
        # Look for numbered lists (1., 2., etc.)
        pattern = r'^\d+\.\s+(.+)$'
        for line in content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                steps.append(match.group(1))
        return steps
    
    def _estimate_complexity(self, num_steps: int) -> str:
        """Estimate complexity from protocol length"""
        if num_steps < 5:
            return "low"
        elif num_steps < 15:
            return "medium"
        elif num_steps < 30:
            return "high"
        else:
            return "very_high"
    
    def _estimate_metadata(self, skill_data: Dict[str, Any]) -> SkillMetadata:
        """Estimate metadata for orchestrator skills"""
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
        """Get a skill by ID"""
        return self.skills.get(skill_id)
    
    def get_all_skills(self) -> List[UnifiedSkill]:
        """Get all skills"""
        return list(self.skills.values())
    
    def get_skills_by_source(self, source: SkillSource) -> List[UnifiedSkill]:
        """Get skills from a specific source"""
        return [s for s in self.skills.values() if s.source == source]
    
    def get_skills_for_scenario(self, skill_ids: List[str]) -> List[UnifiedSkill]:
        """Get skill objects for a list of IDs"""
        return [self.skills[sid] for sid in skill_ids if sid in self.skills]
    
    def estimate_total_cost(
        self,
        skill_ids: List[str],
        depth_level: str = "focused",
        output_format: str = "standard",
    ) -> Dict[str, Any]:
        """
        Estimate total cost for a set of skills
        
        Returns dict with:
        - total_tokens
        - total_usd (rough estimate)
        - per_skill_breakdown
        """
        breakdown = []
        total_tokens = 0
        
        for skill_id in skill_ids:
            skill = self.get_skill(skill_id)
            if skill:
                tokens = skill.estimate_cost(depth_level, output_format)
                total_tokens += tokens
                breakdown.append({
                    "skill_id": skill_id,
                    "skill_name": skill.name,
                    "tokens": tokens,
                    "usd": tokens * 0.25,  # Rough $0.25 per 1K tokens
                })
        
        return {
            "total_tokens": total_tokens,
            "total_usd": int(total_tokens * 0.25),
            "per_skill_breakdown": breakdown,
        }
    
    def find_skills_by_tag(self, tag: str) -> List[UnifiedSkill]:
        """Find skills by tag (if supported in future)"""
        # TODO: Add tagging system
        return []
    
    def sync_to_file(self, output_path: Path):
        """Export unified registry to JSON"""
        import json
        data = {
            "skills": [s.model_dump() for s in self.skills.values()],
            "total_count": len(self.skills),
            "by_source": {
                "orchestrator": len(self.get_skills_by_source(SkillSource.ORCHESTRATOR)),
                "claude": len(self.get_skills_by_source(SkillSource.CLAUDE)),
                "both": len(self.get_skills_by_source(SkillSource.BOTH)),
            }
        }
        
        output_path.write_text(json.dumps(data, indent=2))
        print(f"✓ Synced {len(self.skills)} skills to {output_path}")
