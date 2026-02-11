"""
Unified skill models bridging orchestrator and Claude skills
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SkillSource(str, Enum):
    """Where the skill comes from"""
    ORCHESTRATOR = "orchestrator"  # /skills directory
    CLAUDE = "claude"              # .claude/skills directory
    BOTH = "both"                  # Exists in both


class QualityTier(str, Enum):
    """Output quality level"""
    LEAN = "lean"           # Abbreviated, MVP-quality
    STANDARD = "standard"   # Production-ready
    PREMIUM = "premium"     # Agency-grade
    ENTERPRISE = "enterprise"  # Legal/compliance-ready


class SkillMetadata(BaseModel):
    """Metadata about skill capabilities and costs"""
    estimated_tokens: int = Field(default=5000, description="Rough token cost")
    quality_tier: QualityTier = Field(default=QualityTier.STANDARD)
    execution_time_minutes: int = Field(default=5, description="Typical execution time")
    complexity: str = Field(default="medium", description="low|medium|high|very_high")
    can_run_parallel: bool = Field(default=True)
    requires_human_input: bool = Field(default=False)
    
    # Cost scaling factors
    lean_mode_multiplier: float = Field(default=0.6, description="Token reduction in lean mode")
    premium_mode_multiplier: float = Field(default=1.5, description="Token increase in premium")


class UnifiedSkill(BaseModel):
    """
    Unified skill schema combining orchestrator and Claude skills
    """
    id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Human-readable name")
    source: SkillSource = Field(..., description="Where this skill comes from")
    
    # Paths
    skill_md_path: Optional[str] = Field(default=None, description="Path to skill.md")
    template_path: Optional[str] = Field(default=None, description="Path to output template")
    
    # Behavior
    description: str = Field(default="", description="What this skill does")
    inputs: List[str] = Field(default_factory=list, description="Required upstream data")
    outputs: List[str] = Field(default_factory=list, description="Generated artifacts")
    
    # Dependencies
    required_keys: List[str] = Field(default_factory=list, description="JSON keys for validation")
    upstream_dependencies: List[str] = Field(default_factory=list, description="Skill IDs that must run first")
    
    # Metadata
    metadata: SkillMetadata = Field(default_factory=SkillMetadata)
    
    # Scenario support
    supported_scenarios: List[str] = Field(default_factory=list, description="Which scenarios use this")
    
    # Protocol (if available)
    protocol_steps: List[str] = Field(default_factory=list, description="Step-by-step instructions")
    
    def estimate_cost(self, depth_level: str = "standard", output_format: str = "standard") -> int:
        """
        Estimate token cost based on depth and format
        
        Args:
            depth_level: surface|focused|comprehensive|exhaustive
            output_format: minimal|standard|maximum
        """
        base_tokens = self.metadata.estimated_tokens
        
        # Depth multipliers
        depth_multipliers = {
            "surface": 0.5,
            "focused": 1.0,
            "comprehensive": 1.5,
            "exhaustive": 2.5,
        }
        
        # Format overhead
        format_overhead = {
            "minimal": 500,
            "standard": 1500,
            "maximum": 3000,
        }
        
        depth_mult = depth_multipliers.get(depth_level, 1.0)
        format_add = format_overhead.get(output_format, 1500)
        
        return int(base_tokens * depth_mult + format_add)
    
    def get_lean_variant(self) -> "UnifiedSkill":
        """Create a budget-optimized variant"""
        lean_skill = self.model_copy(deep=True)
        lean_skill.id = f"{self.id}-lean"
        lean_skill.name = f"{self.name} (Lean)"
        lean_skill.metadata.estimated_tokens = int(
            self.metadata.estimated_tokens * self.metadata.lean_mode_multiplier
        )
        lean_skill.metadata.quality_tier = QualityTier.LEAN
        return lean_skill
    
    def get_premium_variant(self) -> "UnifiedSkill":
        """Create a premium quality variant"""
        premium_skill = self.model_copy(deep=True)
        premium_skill.id = f"{self.id}-premium"
        premium_skill.name = f"{self.name} (Premium)"
        premium_skill.metadata.estimated_tokens = int(
            self.metadata.estimated_tokens * self.metadata.premium_mode_multiplier
        )
        premium_skill.metadata.quality_tier = QualityTier.PREMIUM
        return premium_skill
