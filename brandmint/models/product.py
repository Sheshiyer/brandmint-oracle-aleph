"""
Product data models with enhanced launch context
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LaunchChannel(str, Enum):
    """Launch channel types"""
    KICKSTARTER = "kickstarter"
    INDIEGOGO = "indiegogo"
    DTC = "direct-to-consumer"
    ENTERPRISE = "enterprise"
    SAAS = "saas"
    ORGANIC = "organic"
    UNKNOWN = "unknown"


class BudgetTier(str, Enum):
    """Budget categories"""
    BOOTSTRAPPED = "bootstrapped"  # <$5K
    LEAN = "lean"                   # $5-20K
    STANDARD = "standard"           # $20-100K
    PREMIUM = "premium"             # >$100K


class MaturityStage(str, Enum):
    """Brand/product maturity"""
    PRE_LAUNCH = "pre-launch"
    LAUNCH_READY = "launch-ready"
    GROWTH = "growth"
    ESTABLISHED = "established"


class TimelineUrgency(str, Enum):
    """Timeline pressure"""
    RUSHED = "rushed"        # <2 weeks
    STANDARD = "standard"    # 2-8 weeks
    THOROUGH = "thorough"    # >8 weeks


class TeamSize(str, Enum):
    """Team capacity"""
    SOLO = "solo"           # 1 person
    SMALL = "small"         # 2-5 people
    AGENCY = "agency"       # >5 people


class LaunchContext(BaseModel):
    """Extended context beyond product specs"""
    channel: LaunchChannel = Field(default=LaunchChannel.UNKNOWN)
    budget_tier: BudgetTier = Field(default=BudgetTier.STANDARD)
    budget_amount: Optional[int] = Field(default=None, description="Budget in USD")
    maturity_stage: MaturityStage = Field(default=MaturityStage.LAUNCH_READY)
    timeline_urgency: TimelineUrgency = Field(default=TimelineUrgency.STANDARD)
    timeline_weeks: Optional[int] = Field(default=None)
    team_size: TeamSize = Field(default=TeamSize.SMALL)
    team_count: Optional[int] = Field(default=None)
    
    # Preferences
    content_depth: str = Field(default="standard", description="minimal|standard|maximum")
    quality_bar: str = Field(default="standard", description="mvp|standard|premium|enterprise")
    tone_preference: str = Field(default="balanced", description="scrappy|balanced|corporate")
    
    # Constraints
    has_existing_brand: bool = Field(default=False)
    has_existing_content: bool = Field(default=False)
    skip_video: bool = Field(default=False)
    skip_packaging: bool = Field(default=False)


class ProductBrand(BaseModel):
    """Brand information"""
    name: str = Field(..., description="Brand/product name")
    hero_product: Optional[str] = Field(default=None)
    category: str = Field(..., description="Product category")
    primary_promise: str = Field(..., description="Primary brand promise")
    pillars: List[str] = Field(default_factory=list)


class ProductSpecs(BaseModel):
    """Technical specifications"""
    dimensions: Optional[str] = Field(default=None)
    materials: Optional[str] = Field(default=None)
    weight: Optional[str] = Field(default=None)
    features: Dict[str, Any] = Field(default_factory=dict)
    colorways: List[str] = Field(default_factory=list)


class AudienceSegment(BaseModel):
    """Audience segment"""
    name: str
    who: str
    why_fits: str = Field(default="")
    top_messages: List[str] = Field(default_factory=list)
    offer_angle: str = Field(default="")


class ProductData(BaseModel):
    """Complete product data with launch context"""
    brand: ProductBrand
    launch_context: LaunchContext = Field(default_factory=LaunchContext)
    positioning_statement: str = Field(default="")
    specs: ProductSpecs = Field(default_factory=ProductSpecs)
    segments: List[AudienceSegment] = Field(default_factory=list)
    messaging: Dict[str, Any] = Field(default_factory=dict)
    commercial_offer: Dict[str, Any] = Field(default_factory=dict)
    target_regions: List[str] = Field(default_factory=list)
    
    # Pricing (for budget tier detection)
    price: Optional[int] = Field(default=None, description="Product price in USD")
