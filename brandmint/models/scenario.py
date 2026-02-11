"""
Scenario models for context-aware execution plans
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .product import BudgetTier, LaunchChannel, MaturityStage


class ScenarioType(str, Enum):
    """Scenario categories"""
    BRAND_GENESIS = "brand-genesis"
    CROWDFUNDING_LEAN = "crowdfunding-lean"
    CROWDFUNDING_FULL = "crowdfunding-full"
    BOOTSTRAPPED_DTC = "bootstrapped-dtc"
    ENTERPRISE_GTM = "enterprise-gtm"
    CUSTOM_HYBRID = "custom-hybrid"


class ExecutionContext(BaseModel):
    """Context passed to agents for prompt scaffolding"""
    budget_tier: BudgetTier
    tone: str = Field(..., description="scrappy|balanced|premium|corporate")
    output_format: str = Field(..., description="minimal|standard|maximum")
    depth_level: str = Field(..., description="surface|focused|comprehensive|exhaustive")
    quality_bar: str = Field(..., description="mvp|standard|premium|enterprise")
    token_limit_per_skill: int = Field(default=5000)
    
    # Platform-specific
    platform_constraints: List[str] = Field(default_factory=list)
    
    # Optimization flags
    prioritize: str = Field(default="balanced", description="speed|quality|cost")
    allow_parallel: bool = Field(default=True)
    enable_auto_correction: bool = Field(default=True)


class ScenarioMatch(BaseModel):
    """How well a scenario fits the product context"""
    scenario_id: ScenarioType
    match_score: float = Field(..., ge=0.0, le=1.0, description="0-1 confidence")
    reasoning: str = Field(..., description="Why this scenario matches")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)


class Scenario(BaseModel):
    """
    An execution scenario defining which skills to run with what context
    """
    id: ScenarioType
    name: str
    emoji: str = Field(default="🎯")
    description: str
    
    # Suitability
    best_for_budget: BudgetTier
    best_for_channels: List[LaunchChannel] = Field(default_factory=list)
    best_for_maturity: List[MaturityStage] = Field(default_factory=list)
    
    # Skills to execute
    skill_ids: List[str] = Field(..., description="Ordered skill IDs")
    
    # Execution context
    execution_context: ExecutionContext
    
    # Estimates
    estimated_cost_usd: int = Field(..., description="Estimated total cost")
    estimated_tokens: int = Field(..., description="Total token usage")
    estimated_timeline_days: str = Field(..., description="2-3 days, etc")
    
    # Deliverables
    deliverables: List[str] = Field(default_factory=list, description="What you'll get")
    skip_deliverables: List[str] = Field(default_factory=list, description="What's excluded")
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    
    def __repr__(self) -> str:
        return f"Scenario({self.id}): {self.name} - {len(self.skill_ids)} skills, ${self.estimated_cost_usd}"
    
    def matches_context(
        self,
        budget_tier: BudgetTier,
        channel: LaunchChannel,
        maturity: MaturityStage,
    ) -> float:
        """
        Calculate match score (0-1) based on context
        """
        score = 0.0
        factors = 0
        
        # Budget match (highest weight)
        if budget_tier == self.best_for_budget:
            score += 0.5
        elif abs(list(BudgetTier).index(budget_tier) - list(BudgetTier).index(self.best_for_budget)) == 1:
            score += 0.25  # Adjacent tier
        factors += 1
        
        # Channel match
        if channel in self.best_for_channels or not self.best_for_channels:
            score += 0.3
        factors += 1
        
        # Maturity match
        if maturity in self.best_for_maturity or not self.best_for_maturity:
            score += 0.2
        factors += 1
        
        return score
